"""Audit the canonical data/ CSV and its evidence bundle.

Exit 0: audited with no review items; 1: invalid/inconsistent build;
2: mechanically valid build with unresolved source/availability review items.
The script never downloads data, edits inputs or trains a model.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from financial_quality import sha256

ROOT = Path(__file__).resolve().parents[1]
CSV_NAME = "bist_bilanco_tahmini_2010_2020.csv"


def audit(data_dir=None):
    directory = Path(data_dir) if data_dir else ROOT / "data"
    path = directory / CSV_NAME
    errors, review = [], []
    if not path.is_file():
        return {"errors": [f"Canonical CSV missing: {path}"], "review": [], "exit_code": 1}
    frame = pd.read_csv(path)
    keys = ["ticker", "year", "quarter"]
    base_columns = keys + ["observation_period", "period_end_date", "T12_finansal_borclar", "F13_net_borc",
                           "T11_toplam_varliklar", "T13_toplam_yukumlulukler", "T14_toplam_ozkaynaklar",
                           "T01_hasilat_ytd", "T02_satislarin_maliyeti_ytd", "T03_brut_kar_ytd",
                           "T01_hasilat_ceyrek", "T07_donem_net_kari_ceyrek"]
    absent = sorted(set(base_columns) - set(frame.columns))
    if absent:
        return {"errors": [f"Missing required columns: {absent}"], "review": [], "exit_code": 1}
    if frame.duplicated(keys).any():
        errors.append("Duplicate company-quarter keys")
    if len(frame) != frame.ticker.nunique() * frame.observation_period.nunique():
        errors.append("Unbalanced company-quarter panel")
    if np.isinf(frame.select_dtypes("number").to_numpy()).any():
        errors.append("Infinite numeric values")
    required = ["source_file", "source_sha256", "available_at", "report_available_at", "publication_status"]
    for column in required:
        if column not in frame or frame[column].isna().any():
            errors.append(f"Missing required provenance: {column}")
    if "available_at" in frame and "report_available_at" in frame:
        available = pd.to_datetime(frame.available_at, errors="coerce")
        reported = pd.to_datetime(frame.report_available_at, errors="coerce")
        if (available < reported).any():
            errors.append("Value availability predates its selected source report")
    if (frame.loc[frame.T12_finansal_borclar.isna(), "F13_net_borc"].notna()).any():
        errors.append("Unknown financial debt was turned into a numeric net debt")
    residual = frame.T11_toplam_varliklar - frame.T13_toplam_yukumlulukler - frame.T14_toplam_ozkaynaklar
    if (residual.abs() > 1).any():
        errors.append("Balance sheet does not reconcile (1 TRY tolerance)")
    if "ofr_assumed_available_at" in frame:
        bad = pd.to_datetime(frame.ofr_assumed_available_at) > pd.to_datetime(frame.period_end_date)
        if bad.any():
            errors.append("OFR observation used before its assumed release date")
    if "gprd_assumed_available_at" in frame:
        bad_gprd = pd.to_datetime(frame.gprd_assumed_available_at) > pd.to_datetime(frame.period_end_date)
        if bad_gprd.any():
            errors.append("GPRD observation used before its assumed 7-day release date")
    if "vergi_oncesi_kar_zarar_ytd" in frame and "T06_vergi_gideri_geliri_ytd" in frame:
        same_as_ebt = (
            frame.T06_vergi_gideri_geliri_ytd.notna()
            & frame.vergi_oncesi_kar_zarar_ytd.notna()
            & (frame.vergi_oncesi_kar_zarar_ytd != 0)
            & (frame.T06_vergi_gideri_geliri_ytd == frame.vergi_oncesi_kar_zarar_ytd)
        )
        if same_as_ebt.any():
            errors.append("T06 tax column mistakenly equals non-zero pre-tax profit (EBT)")
    gross = frame.T01_hasilat_ytd + frame.T02_satislarin_maliyeti_ytd - frame.T03_brut_kar_ytd
    gross_count = int((gross.abs() > 1).sum())
    mixed = frame.get("qa_flags", pd.Series("", index=frame.index)).fillna("").str.contains("mixed_activity_income_statement")
    ordinary_gross_count = int(((gross.abs() > 1) & ~mixed).sum())
    mixed_gross_count = gross_count - ordinary_gross_count
    if ordinary_gross_count:
        review.append(f"{ordinary_gross_count} ordinary gross-profit source reconciliation flags (1 TRY scan, not automatic errors)")
    if mixed_gross_count:
        review.append(f"{mixed_gross_count} mixed finance/commercial scopes require a different reconciliation")
    for column in ["T01_hasilat_ceyrek", "T07_donem_net_kari_ceyrek", "T11_toplam_varliklar", "T14_toplam_ozkaynaklar"]:
        missing = int(frame[column].isna().sum())
        if missing:
            review.append(f"{column}: {missing} missing targets; mask these labels, never impute them")
    quality_dir = directory / "quality"
    manifest_path = quality_dir / "manifest.json"
    if not manifest_path.exists():
        errors.append("Missing completed build manifest")
    else:
        manifest = json.loads(manifest_path.read_text())
        hashes = {item["sha256"] for item in manifest["csv_files"]}
        if sha256(path) not in hashes:
            errors.append("CSV hash does not match completed build manifest")
        for name, expected in manifest["diagnostics_sha256"].items():
            evidence = quality_dir / name
            if not evidence.exists() or sha256(evidence) != expected:
                errors.append(f"Missing/changed diagnostics: {name}")
        if sha256(Path(__file__).with_name("parse_and_build_dataset.py")) != manifest["parser_sha256"]:
            errors.append("CSV was not built with the current parser version")
        if sha256(Path(__file__).with_name("financial_quality.py")) != manifest["quality_code_sha256"]:
            errors.append("CSV was not built with the current quality helpers")
        for name, expected in manifest["external_sha256"].items():
            if sha256(ROOT / "data/external" / name) != expected:
                errors.append(f"External input changed: {name}")
        if sha256(ROOT / "data/kap_fr_catalog_2010_2020.json") != manifest["catalog_sha256"]:
            errors.append("Publication catalog changed since the build")
    if all(column in frame for column in ["source_file", "source_sha256"]):
        for _, row in frame[["source_file", "source_sha256"]].drop_duplicates().iterrows():
            source = ROOT / str(row.source_file)
            if not source.exists() or sha256(source) != row.source_sha256:
                errors.append(f"Raw source hash mismatch: {row.source_file}")
    summary_path = quality_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        if not summary.get("fully_point_in_time_verified"):
            review.append("Historical macro vintages/release timestamps are not fully verified")
        if summary.get("flagged_reports"):
            review.append(f"{len(summary['flagged_reports'])} reports carry explicit source/scope/correction flags")
        for name in ("missing_values.jsonl.gz", "financial_sources.jsonl.gz"):
            file = quality_dir / name
            if file.exists():
                try:
                    for line in gzip.decompress(file.read_bytes()).decode().splitlines():
                        json.loads(line)
                except (ValueError, OSError, UnicodeError) as error:
                    errors.append(f"Unreadable evidence: {name}: {error}")
    else:
        errors.append("Missing quality summary")
    return {"rows": len(frame), "columns": len(frame.columns), "gross_flags": gross_count,
            "ordinary_gross_flags": ordinary_gross_count, "mixed_scope_flags": mixed_gross_count,
            "errors": errors, "review": review, "exit_code": 1 if errors else 2 if review else 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, help="Directory containing the canonical CSV and quality/ bundle")
    args = parser.parse_args()
    result = audit(args.data_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["exit_code"] == 2:
        print("URETIM KONTROLLERI GECTI; KAYNAK/ZAMAN INCELEMESI GEREKIYOR. Bu, egitime hazir onayi degildir.")
    raise SystemExit(result["exit_code"])


if __name__ == "__main__":
    main()
