"""Source diagnostics for the financial parser. Missing never means zero."""

from __future__ import annotations

import hashlib
import gzip
import json
import math
import os
import re
import tempfile
from pathlib import Path

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay


class FinancialValues(dict):
    """Keep the existing parser mapping API and record where assignments came from."""

    def __init__(self, values):
        super().__init__(values)
        self.source = None
        self.fields = {}

    def reading(self, label, ytd, quarter):
        self.source = (label, ytd, quarter)

    def deriving(self):
        self.source = None

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.source is None:
            self.fields[key] = {"status": "derived", "value": value}
        else:
            label, ytd, quarter = self.source
            self.fields[key] = {
                "status": "reported" if value is not None else "source_value_unavailable",
                "source_label": label,
                "raw_value": quarter if key.endswith("_3m_raw") else ytd,
                "value": value,
            }

    def diagnostics(self, raw_rows):
        result = dict(self.fields)
        for key, value in self.items():
            if key not in result:
                result[key] = {"status": "unresolved", "value": value}
            if result[key]["status"] == "derived" and key in DEPENDENCIES:
                result[key]["dependencies"] = DEPENDENCIES[key]
        # Unknown mappings are deliberately not labelled "company did not disclose".
        return {"fields": result, "raw_row_count": len(raw_rows)}


def cash_flow_total(label):
    """Recognize activity totals across old KAP templates; ignore component rows.

    label is already normalized to ASCII/lowercase. A section heading without a
    number can be recognized, but callers only assign a value if a number exists.
    """
    label = re.sub(r"^[abc](?:\s*[.\-:)]+\s*|\s+)", "", label).strip()
    label = re.sub(r"\s+", " ", label.replace("(", " ").replace(")", " ")).strip(" -")
    label = label.replace("faliyet", "faaliyet")  # observed spelling in old CLEBI filings
    if "duzeltme" in label or "net nakit akislarina neden" in label:
        return None
    for prefix, field in (
        ("isletme faaliyet", "T15_isletme_nakit_akisi_ytd"),
        ("esas faaliyet", "T15_isletme_nakit_akisi_ytd"),
        ("faaliyetlerden", "T15_isletme_nakit_akisi_ytd"),
        ("faaliyetlerde", "T15_isletme_nakit_akisi_ytd"),
        ("yatirim faaliyet", "T16_yatirim_nakit_akisi_ytd"),
        ("finansman faaliyet", "T17_finansman_nakit_akisi_ytd"),
        ("finansal faaliyet", "T17_finansman_nakit_akisi_ytd"),
    ):
        if label.startswith(prefix) and "nakit" in label:
            # Explicit net totals beat pre-tax/interest operating subtotals.
            priority = 3 if "net nakit" in label else 2 if ("akis" in label or "akim" in label) else 1
            return field, priority
    return None


def finite_sum(values):
    """A total is unknown if any required component is unknown."""
    return sum(values) if all(v is not None for v in values) else None


def publication_metadata(selected_date, catalog_date, header_date):
    """Date the selected content conservatively; do not move it to an early cover."""
    selected = selected_date or header_date or catalog_date or ""
    known_first = min(p for p in (catalog_date, header_date, selected_date) if p) if any((catalog_date, header_date, selected_date)) else ""
    return {
        # Legacy name retained for consumers: this dates the selected report version.
        "first_published_at": selected,
        "report_available_at": selected,
        "earliest_known_publication_at": known_first,
        "publication_status": "selected_version_later_than_earliest" if selected and known_first < selected else "selected_version_dated" if selected else "unknown",
    }


def ofr_available_series(daily):
    """Shift actual FSI observations by 2 US federal business days, not merged rows.

    A declared calendar approximation, not a reconstruction of historical releases
    or data vintages. Explicit available_at timestamps can replace it later.
    """
    observations = daily.loc[daily["OFR_FSI"].notna(), ["date", "OFR_FSI"]].copy()
    observations["date"] = pd.to_datetime(observations["date"])
    observations = observations.sort_values("date").drop_duplicates("date")
    offset = CustomBusinessDay(n=2, calendar=USFederalHolidayCalendar())
    observations["ofr_assumed_available_at"] = [stamp + offset for stamp in observations["date"]]
    observations["R03_OFR_FSI_60d_mean"] = observations["OFR_FSI"].rolling(60, min_periods=60).mean()
    return observations.rename(columns={"date": "ofr_observation_date", "OFR_FSI": "R03_OFR_FSI"}).sort_values("ofr_assumed_available_at")


def calendar_fx_change(daily, column, days=90):
    current = daily[["date", column]].dropna().sort_values("date").drop_duplicates("date")
    anchors = current[["date"]].copy()
    anchors["anchor_date"] = anchors["date"] - pd.Timedelta(days=days)
    history = current.rename(columns={"date": "history_date", column: "history_value"})
    joined = pd.merge_asof(anchors, history, left_on="anchor_date", right_on="history_date", direction="backward")
    joined[column] = current[column].to_numpy()
    joined["change"] = (joined[column] / joined["history_value"].replace(0, float("nan")) - 1) * 100
    return joined[["date", "change"]]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        return json_safe(value.item())
    return value


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save_json(path, value):
    atomic_text(path, json.dumps(json_safe(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n")


DEPENDENCIES = {
    "T09_ticari_alacaklar": ["F10_kisa_vadeli_ticari_alacaklar", "F10_uzun_vadeli_ticari_alacaklar"],
    "T12_finansal_borclar": ["F13_kisa_vadeli_finansal_borclar", "F13_uzun_vadeli_finansal_borclar"],
    "F12_ticari_borclar": ["kisa_vadeli_ticari_borclar", "uzun_vadeli_ticari_borclar"],
    "F07_net_finansman_ytd": ["F07_finansman_geliri_ytd", "T05_finansman_gideri_ytd"],
    "F07_net_finansman_ceyrek": ["F07_finansman_geliri_ceyrek", "T05_finansman_gideri_ceyrek"],
    "F13_net_borc": ["T12_finansal_borclar", "T08_nakit_ve_nakit_benzerleri"],
    "F03_brut_kar_marji": ["T03_brut_kar_ceyrek", "T01_hasilat_ceyrek"],
    "F04_esas_faaliyet_marji": ["T04_esas_faaliyet_kari_ceyrek", "T01_hasilat_ceyrek"],
    "F05_net_kar_marji": ["T07_donem_net_kari_ceyrek", "T01_hasilat_ceyrek"],
    "F06_cfo_aktif_orani": ["T15_isletme_nakit_akisi_ceyrek", "T11_toplam_varliklar"],
    "F06_tahakkuk_aktif_orani": ["T07_donem_net_kari_ceyrek", "T15_isletme_nakit_akisi_ceyrek", "T11_toplam_varliklar"],
    "F09_nakit_aktif_orani": ["T08_nakit_ve_nakit_benzerleri", "T11_toplam_varliklar"],
    "F10_alacak_satis_orani": ["T09_ticari_alacaklar", "T01_hasilat_ceyrek"],
    "F11_stok_maliyet_orani": ["T10_stoklar", "T02_satislarin_maliyeti_ceyrek"],
    "F12_ticari_borc_maliyet_orani": ["F12_ticari_borclar", "T02_satislarin_maliyeti_ceyrek"],
    "F13_finansal_borc_aktif_orani": ["T12_finansal_borclar", "T11_toplam_varliklar"],
    "F13_kisa_finansal_borc_aktif_orani": ["F13_kisa_vadeli_finansal_borclar", "T11_toplam_varliklar"],
    "F14_ozkaynak_aktif_orani": ["T14_toplam_ozkaynaklar", "T11_toplam_varliklar"],
    "F14_borc_ozkaynak_orani": ["T13_toplam_yukumlulukler", "T14_toplam_ozkaynaklar"],
    "hisse_basina_kar_ytd": ["T07_ana_ortaklik_net_kari_ytd", "odenmis_sermaye"],
    "hisse_basina_kar_ceyrek": ["T07_ana_ortaklik_net_kari_ceyrek", "odenmis_sermaye"],
    "X02_faiz_degisimi_x_finansal_borc_aktif": ["M03_Faiz_3Aylik_Degisim", "F13_finansal_borc_aktif_orani"],
    "X03_ofr_fsi_x_kisa_borc_aktif": ["R03_OFR_FSI_60d_mean", "F13_kisa_finansal_borc_aktif_orani"],
}


def missing_details(frame, report_audits, quarter_methods):
    """Explain unknowns conservatively; never infer non-disclosure or a zero."""
    records = []
    for _, row in frame.iterrows():
        identity = (row["ticker"], int(row["year"]), int(row["quarter"]))
        source = report_audits.get(identity, {})
        methods = quarter_methods.get(identity, {})
        for column in frame.columns:
            if column == "qa_flags":  # an empty flag set is a valid state
                continue
            if not pd.isna(row[column]) and row[column] != "":
                continue
            reason, detail = "unresolved", {}
            field = source.get("fields", {}).get(column)
            if column == "F03_brut_kar_marji" and "mixed_activity_income_statement" in row.get("qa_flags", ""):
                reason = "income_statement_scope_mismatch"
            elif column in DEPENDENCIES:
                missing = [name for name in DEPENDENCIES[column] if pd.isna(row[name])]
                reason = "missing_component" if missing else "zero_denominator_or_unavailable"
                detail = {"dependencies": DEPENDENCIES[column], "missing_dependencies": missing}
            elif column in methods:
                reason = "missing_quarter_component"
                detail = methods[column]
            elif column.startswith("F01_hasilat_"):
                reason = "insufficient_history" if (column.endswith("qoq_buyume") and row["observation_period"] == "2010Q1") or (column.endswith("yoy_buyume") and row["year"] == 2010) else "missing_history_or_zero_base"
            elif column.startswith(("M", "R")):
                reason = "external_observation_unavailable"
            elif field:
                reason = "source_value_unavailable" if field["status"] == "source_value_unavailable" else "missing_component" if field["status"] == "derived" else "unresolved_source_or_mapping"
                detail = {k: v for k, v in field.items() if k != "value"}
            records.append({"ticker": identity[0], "period": row["observation_period"], "column": column,
                            "reason": reason, "source_file": row.get("source_file", ""), **detail})
    return records


def save_jsonl_gzip(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = "".join(json.dumps(json_safe(row), ensure_ascii=False, allow_nan=False) + "\n" for row in records).encode()
    # Fixed gzip timestamp makes repeated builds comparable.
    fd, temp = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(gzip.compress(data, mtime=0))
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
