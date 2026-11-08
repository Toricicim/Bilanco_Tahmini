"""Regressions from actual KAP reports and independent date/cash identities.

Run: python3 -B -m unittest discover -s tests -v
No downloads, model training or writes to canonical inputs.
"""

import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import financial_quality as quality
import parse_and_build_dataset as parser
import audit_dataset


def read_report(name):
    path = ROOT / "data/kap_raw_xls" / name
    if path.read_bytes()[:4] == b"\xd0\xcf\x11\xe0":
        return parser.extract_rows_from_biff8(path)
    return parser.extract_rows_from_html_xls(path)


class ParserRegressions(unittest.TestCase):
    def test_real_zero_is_distinct_from_missing(self):
        self.assertEqual(parser.parse_number(0), 0.0)
        self.assertEqual(parser.parse_number("0,00"), 0.0)
        self.assertIsNone(parser.parse_number("-"))
        self.assertIsNone(parser.parse_number(""))

    def test_aefes_cash_flow_totals_published_but_previously_missing(self):
        meta, rows = read_report("AEFES_2011_Q1.xls")
        _, multiplier = parser.detect_unit_multiplier(meta["original_unit"])
        audit = {}
        values = parser.parse_financial_rows(rows, multiplier, audit)
        self.assertEqual(values["T16_yatirim_nakit_akisi_ytd"], -117_029_000)
        self.assertEqual(values["T17_finansman_nakit_akisi_ytd"], 42_700_000)
        self.assertIn("ilişkin", audit["fields"]["T16_yatirim_nakit_akisi_ytd"]["source_label"])

    def test_gsdde_shipping_revenue_and_overall_gross_profit(self):
        _, rows = read_report("GSDDE_2014_Q1.xls")
        audit = {}
        values = parser.parse_financial_rows(rows, 1000, audit)
        self.assertEqual(values["T01_hasilat_ytd"], (3538 + 74 + 51) * 1000)
        self.assertEqual(values["T03_brut_kar_ytd"], 349_000)
        self.assertIn("mixed_activity_income_statement", audit["flags"])

    def test_contradictory_zero_gross_total_does_not_erase_subtotals(self):
        meta, rows = read_report("CCOLA_2013_Q2.xls")
        audit = {}
        values = parser.parse_financial_rows(rows, 1000, audit)
        self.assertEqual(values["T03_brut_kar_ytd"], 949_788_000)
        self.assertEqual(audit["financial_gross_subtotal"], 0)
        self.assertIn("gross_total_conflicts_with_complete_subtotals", audit["flags"])

    def test_csv_records_inside_biff_cells_are_recovered(self):
        meta, rows = read_report("TOASO_2013_Q1.xls")
        self.assertGreater(meta["embedded_csv_rows_recovered"], 0)
        values = parser.parse_financial_rows(rows, 1000)
        self.assertEqual(values["T15_isletme_nakit_akisi_ytd"], 623_663_000)
        self.assertEqual(values["T16_yatirim_nakit_akisi_ytd"], 14_308_000)
        self.assertEqual(values["T17_finansman_nakit_akisi_ytd"], -524_194_000)

    def test_no_last_component_fallback_for_missing_cash_total(self):
        rows = [("Nakit Akım Tablosu", None, None),
                ("Yatırım faaliyetleri", None, None),
                ("Maddi duran varlık alımı", -100, None)]
        values = parser.parse_financial_rows(rows, 1)
        self.assertIsNone(values["T16_yatirim_nakit_akisi_ytd"])

    def test_partial_borrowings_are_not_complete_debt(self):
        rows = [("Bilanço", None, None), ("Kısa Vadeli Yükümlülükler", None, None),
                ("Finansal Borçlar", 100, None), ("Uzun Vadeli Yükümlülükler", None, None),
                ("Finansal Borçlar", None, None)]
        values = parser.parse_financial_rows(rows, 1)
        self.assertEqual(values["F13_kisa_vadeli_finansal_borclar"], 100)
        self.assertIsNone(values["T12_finansal_borclar"])

    def test_parent_profit_is_not_invented_from_total_profit(self):
        values = parser.parse_financial_rows([("Gelir Tablosu", None, None), ("Dönem Karı/Zararı", 100, None)], 1)
        self.assertEqual(values["T07_donem_net_kari_ytd"], 100)
        self.assertIsNone(values["T07_ana_ortaklik_net_kari_ytd"])

    def test_cash_flow_typos_and_parentheses(self):
        rows = [("Nakit Akım Tablosu", None, None),
                ("(İşletme faaliyetlerinde kullanılan) / faaliyetlerinden sağlanan net nakit", -10, None),
                ("Finansman faliyetlerinden sağlanan/ (faaliyetlerinde kullanılan) net nakit", 20, None)]
        values = parser.parse_financial_rows(rows, 1)
        self.assertEqual(values["T15_isletme_nakit_akisi_ytd"], -10)
        self.assertEqual(values["T17_finansman_nakit_akisi_ytd"], 20)

    def test_unknowns_are_not_reported_as_company_non_disclosure(self):
        audit = {}
        parser.parse_financial_rows([("Gelir Tablosu", None, None)], 1, audit)
        self.assertEqual(audit["fields"]["T01_hasilat_ytd"]["status"], "unresolved")

    def test_original_file_beats_later_archive_revision(self):
        files = [Path("AKSEN_2018_Q1_748443.xls"), Path("AKSEN_2018_Q1_683063.xls")]
        selected = parser.select_source_files(files, {"748443": "2019-03-19 00:00:49", "683063": "2018-05-10 21:15:51"})
        self.assertEqual(selected[("AKSEN", 2018, 1)].name, "AKSEN_2018_Q1_683063.xls")

    def test_tax_is_distinct_from_pretax_profit_and_sums_children_when_parent_missing(self):
        _, rows = read_report("TUPRS_2010_Q1.xls")
        values = parser.parse_financial_rows(rows, 1000)
        self.assertEqual(values["vergi_oncesi_kar_zarar_ytd"], 125_427_000)
        self.assertEqual(values["T06_vergi_gideri_geliri_ytd"], -23_210_000)
        self.assertEqual(
            values["vergi_oncesi_kar_zarar_ytd"] + values["T06_vergi_gideri_geliri_ytd"],
            values["T07_donem_net_kari_ytd"],
        )
        synthetic = [
            ("Gelir Tablosu", None, None),
            ("SÜRDÜRÜLEN FAALİYETLER VERGİ ÖNCESİ KARI/ZARARI", 500, None),
            ("Sürdürülen Faaliyetler Vergi Gelir/Gideri", None, None),
            ("- Dönem Vergi Gelir/Gideri", -80, None),
            ("- Ertelenmiş Vergi Gelir/Gideri", -20, None),
            ("DÖNEM KARI/ZARARI", 400, None),
        ]
        syn_vals = parser.parse_financial_rows(synthetic, 1)
        self.assertEqual(syn_vals["vergi_oncesi_kar_zarar_ytd"], 500)
        self.assertEqual(syn_vals["T06_vergi_gideri_geliri_ytd"], -100)

    def test_operating_cash_flow_top_total_is_not_overwritten_by_pretax_subtotal(self):
        rows = [
            ("Nakit Akış Tablosu", None, None),
            ("A. İŞLETME FAALİYETLERİNDEN NAKİT AKIŞLARI", 250_000, None),
            ("Faaliyetlerden Elde Edilen Nakit Akışları", 310_000, None),
        ]
        values = parser.parse_financial_rows(rows, 1)
        self.assertEqual(values["T15_isletme_nakit_akisi_ytd"], 250_000)

    def test_oci_section_does_not_overwrite_net_profit(self):
        _, rows = read_report("TOASO_2014_Q1.xls")
        values = parser.parse_financial_rows(rows, 1000)
        self.assertEqual(values["T07_donem_net_kari_ytd"], 134_002_000)

    def test_tuprs_service_revenue_and_rysas_cogs_sign_and_duplicate_cf(self):
        _, tuprs_rows = read_report("TUPRS_2010_Q1.xls")
        tuprs_vals = parser.parse_financial_rows(tuprs_rows, 1000)
        self.assertEqual(
            tuprs_vals["T01_hasilat_ytd"] + tuprs_vals["T02_satislarin_maliyeti_ytd"],
            tuprs_vals["T03_brut_kar_ytd"],
        )
        _, rysas_2011_rows = read_report("RYSAS_2011_Q1.xls")
        rysas_audit = {}
        rysas_2011_vals = parser.parse_financial_rows(rysas_2011_rows, 1, rysas_audit)
        self.assertEqual(rysas_2011_vals["T02_satislarin_maliyeti_ytd"], -48_119_197)
        self.assertIn("cogs_sign_normalized_from_gross_profit", rysas_audit["flags"])
        _, rysas_2010_rows = read_report("RYSAS_2010_Q1.xls")
        rysas_2010_vals = parser.parse_financial_rows(rysas_2010_rows, 1)
        self.assertEqual(rysas_2010_vals["T17_finansman_nakit_akisi_ytd"], 12_599_566)


class TimeAndOutputRegressions(unittest.TestCase):
    def test_reported_zero_quarter_is_preserved_and_later_evidence_propagates(self):
        bases = ["T01_hasilat", "T02_satislarin_maliyeti", "T03_brut_kar", "T04_esas_faaliyet_kari", "T05_finansman_gideri", "F07_finansman_geliri", "T06_vergi_gideri_geliri", "T07_donem_net_kari", "T07_ana_ortaklik_net_kari"]
        rows = []
        for quarter in [1, 2]:
            row = {"ticker": "TEST", "year": 2012, "quarter": quarter,
                   "source_available_at": "2013-05-03 14:07:20" if quarter == 1 else "2012-08-01 12:00:00"}
            for base in bases:
                row[base + "_ytd"] = 100 if quarter == 1 else 150
                row[base + "_3m_raw"] = 0 if quarter == 2 else np.nan
            for base in ["T15_isletme_nakit_akisi", "T16_yatirim_nakit_akisi", "T17_finansman_nakit_akisi"]:
                row[base + "_ytd"] = 10 if quarter == 1 else 20
            rows.append(row)
        frame, methods = parser.derive_quarterly_flows(pd.DataFrame(rows))
        self.assertEqual(frame.loc[1, "T01_hasilat_ceyrek"], 0)
        self.assertEqual(methods[("TEST", 2012, 2)]["T01_hasilat_ceyrek"]["method"], "reported_3m")
        self.assertEqual(frame.loc[1, "available_at"], "2013-05-03 14:07:20")

    def test_selected_report_is_not_dated_to_earlier_cover(self):
        result = quality.publication_metadata("2015-01-08 17:49:07", "2014-08-06 17:46:59", "2014-08-06 17:46:59")
        self.assertEqual(result["report_available_at"], "2015-01-08 17:49:07")
        self.assertEqual(result["first_published_at"], "2015-01-08 17:49:07")
        self.assertEqual(result["publication_status"], "selected_version_later_than_earliest")

    def test_friday_fsi_is_not_available_on_monday(self):
        dates = pd.date_range("2013-09-23", "2013-09-30", freq="D")
        source = pd.DataFrame({"date": dates, "OFR_FSI": [1, 2, 3, 4, 5, np.nan, np.nan, 6]})
        values = quality.ofr_available_series(source)
        known = values[values.ofr_assumed_available_at <= pd.Timestamp("2013-09-30")]
        self.assertEqual(known.iloc[-1].ofr_observation_date, pd.Timestamp("2013-09-26"))
        friday = values[values.ofr_observation_date == pd.Timestamp("2013-09-27")].iloc[0]
        self.assertEqual(friday.ofr_assumed_available_at, pd.Timestamp("2013-10-01"))

    def test_federal_holiday_is_not_a_publication_business_day(self):
        source = pd.DataFrame({"date": pd.to_datetime(["2024-07-03"]), "OFR_FSI": [1.]})
        self.assertEqual(quality.ofr_available_series(source).iloc[0].ofr_assumed_available_at, pd.Timestamp("2024-07-08"))

    def test_fx_change_uses_calendar_days(self):
        source = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=120), "FX": np.arange(1, 121, dtype=float)})
        result = quality.calendar_fx_change(source, "FX", days=90)
        self.assertAlmostEqual(result.iloc[-1]["change"], 300.)
        self.assertTrue(pd.isna(result.iloc[0]["change"]))

    def test_fsi_average_counts_sixty_actual_observations(self):
        source = pd.DataFrame({"date": pd.bdate_range("2020-01-01", periods=60), "OFR_FSI": np.arange(60, dtype=float)})
        result = quality.ofr_available_series(source)
        self.assertEqual(result.R03_OFR_FSI_60d_mean.notna().sum(), 1)
        self.assertEqual(result.iloc[-1].R03_OFR_FSI_60d_mean, 29.5)

    def test_atomic_failure_preserves_previous_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "dataset.csv"
            path.write_text("previous")
            with patch.object(quality.os, "replace", side_effect=PermissionError("locked CSV")):
                with self.assertRaises(PermissionError):
                    quality.atomic_text(path, "new")
            self.assertEqual(path.read_text(), "previous")
            self.assertEqual(list(Path(temp).iterdir()), [path])



class FullBuildRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame, cls.quality = parser.build_dataset(return_quality=True)
        cls.rows = cls.frame.set_index(["ticker", "year", "quarter"])

    def test_karel_correction_matches_cash_bridge(self):
        row = self.rows.loc[("KAREL", 2012, 1)]
        self.assertEqual(row.T16_yatirim_nakit_akisi_ytd, -4_778_913)
        self.assertEqual(row.T17_finansman_nakit_akisi_ytd, 8_800_694)
        cash_end = 30_844_143 + row.T15_isletme_nakit_akisi_ytd + row.T16_yatirim_nakit_akisi_ytd + row.T17_finansman_nakit_akisi_ytd + 116_000
        self.assertEqual(cash_end, 46_510_193)
        q2 = self.rows.loc[("KAREL", 2012, 2)]
        self.assertEqual(q2.T16_yatirim_nakit_akisi_ceyrek, -4_925_954)

    def test_missing_debt_never_creates_minus_cash_net_debt(self):
        missing = self.frame.T12_finansal_borclar.isna()
        self.assertTrue(self.frame.loc[missing, "F13_net_borc"].isna().all())

    def test_ttrak_later_financial_date_survives(self):
        row = self.rows.loc[("TTRAK", 2014, 2)]
        self.assertEqual(row.report_available_at, "2015-01-08 17:49:07")
        self.assertIn("selected_version_later_than_earliest", row.qa_flags)

    def test_sarky_unit_correction_timestamp_and_new_features_populated(self):
        sarky = self.rows.loc[("SARKY", 2017, 2)]
        self.assertIn("manual_unit_override", sarky.qa_flags)
        self.assertEqual(sarky.source_available_at, "2017-08-21 20:29:20")
        self.assertEqual(int(self.frame["F15_maddi_duran_varliklar"].notna().sum()), 1320)
        self.assertGreaterEqual(int(self.frame["F16_genel_yonetim_giderleri_ytd"].notna().sum()), 1310)
        self.assertGreaterEqual(int(self.frame["F18_kisa_vadeli_ertelenmis_gelir_ve_avanslar"].notna().sum()), 890)
        self.assertEqual(int(self.frame["R01_GPRC_TUR"].notna().sum()), 1320)
        self.assertEqual(int(self.frame["R01_GPRD_q_mean"].notna().sum()), 1320)
        self.assertGreaterEqual(int(self.frame["T06_vergi_gideri_geliri_ytd"].notna().sum()), 1310)

    def test_all_missing_cells_have_a_reason_and_no_infinities(self):
        missing = self.frame.drop(columns=["qa_flags"]).isna() | self.frame.drop(columns=["qa_flags"]).eq("")
        self.assertEqual(int(missing.to_numpy().sum()), len(self.quality["missing_values"]))
        self.assertFalse(np.isinf(self.frame.select_dtypes("number").to_numpy()).any())

    def test_serialized_evidence_is_strict_json_and_hash_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            parser.save_dataset(self.frame, Path(temp), quality=self.quality)
            quality_dir = Path(temp) / "quality"
            manifest = json.loads((quality_dir / "manifest.json").read_text())
            self.assertEqual(quality.sha256(Path(temp) / parser.OUTPUT_CSV.name), manifest["csv_files"][0]["sha256"])
            lines = gzip.decompress((quality_dir / "missing_values.jsonl.gz").read_bytes()).decode().splitlines()
            self.assertEqual(len(lines), len(self.quality["missing_values"]))
            for line in lines:
                self.assertIn("reason", json.loads(line))
            result = audit_dataset.audit(Path(temp))
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["exit_code"], 2)  # source/vintage review is deliberately still open
            (Path(temp) / parser.OUTPUT_CSV.name).write_text("ticker,year,quarter\nBAD,2020,1\n")
            # A modified but otherwise schema-valid CSV must fail the manifest check.
            changed = self.frame.copy()
            changed.loc[0, "T01_hasilat_ceyrek"] += 1
            changed.to_csv(Path(temp) / parser.OUTPUT_CSV.name, index=False)
            self.assertIn("CSV hash does not match completed build manifest", audit_dataset.audit(Path(temp))["errors"])


if __name__ == "__main__":
    unittest.main()
