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
import build_training_matrix as tm_builder
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

    def test_load_catalog_dates_prefers_statement_over_dipnot(self):
        cat_dates, _ = parser.load_catalog_dates()
        pub, idx = cat_dates[("AEFES", 2010, 1)]
        self.assertEqual(pub, "2010-05-11 17:54:03")
        self.assertEqual(idx, "115705")

    def test_blank_parent_subrows_recovered_and_filled_parent_never_double_counted(self):
        synthetic = [
            ("Bilanço", None, None),
            ("Dönen Varlıklar", None, None),
            ("Ticari Alacaklar", 500, None),
            ("- İlişkili taraflardan ticari alacaklar", 100, None),
            ("- Diğer ticari alacaklar", 400, None),
            ("Kısa Vadeli Yükümlülükler", None, None),
            ("Finansal Borçlar", 100, None),
            ("- Banka kredileri", 60, None),
            ("- Finansal kiralama işlemlerinden borçlar", 40, None),
        ]
        syn_vals = parser.parse_financial_rows(synthetic, 1)
        self.assertEqual(syn_vals["F10_kisa_vadeli_ticari_alacaklar"], 500)
        self.assertEqual(syn_vals["F13_kisa_vadeli_finansal_borclar"], 100)

        meta, rows = read_report("ZOREN_2010_Q3.xls")
        _, mult = parser.detect_unit_multiplier(meta["original_unit"])
        vals = parser.parse_financial_rows(rows, mult)
        self.assertEqual(vals["F13_kisa_vadeli_finansal_borclar"], (538_940 + 1_527) * 1000)
        self.assertEqual(vals["F13_uzun_vadeli_finansal_borclar"], (836_819 + 6_277) * 1000)
        self.assertEqual(vals["kisa_vadeli_ticari_borclar"], (10_826 + 61_686) * 1000)
        self.assertEqual(vals["uzun_vadeli_ticari_borclar"], (138_982 + 75_199) * 1000)

    def test_capex_amort_and_gsdde_cash_flow_recovery(self):
        aygaz_meta, aygaz_rows = read_report("AYGAZ_2010_Q1.xls")
        _, aygaz_mult = parser.detect_unit_multiplier(aygaz_meta["original_unit"])
        aygaz_vals = parser.parse_financial_rows(aygaz_rows, aygaz_mult)
        self.assertEqual(aygaz_vals["F15_capex_ytd"], (-5_879 - 469) * 1000)
        self.assertEqual(aygaz_vals["F15_amortisman_ve_itfa_ytd"], (23_760 + 511) * 1000)

        _, tavhl_rows = read_report("TAVHL_2010_Q1.xls")
        tavhl_vals = parser.parse_financial_rows(tavhl_rows, 1)
        self.assertEqual(tavhl_vals["F15_amortisman_ve_itfa_ytd"], 15_358_271 + 7_600_314 + 2_799_223)

        gsdde_meta, gsdde_rows = read_report("GSDDE_2012_Q1.xls")
        _, gsdde_mult = parser.detect_unit_multiplier(gsdde_meta["original_unit"])
        gsdde_vals = parser.parse_financial_rows(gsdde_rows, gsdde_mult)
        self.assertEqual(gsdde_vals["T15_isletme_nakit_akisi_ytd"], 4_872_000)

    def test_html_new_type_row_basic_eps_and_exclusions(self):
        _, rows = read_report("AEFES_2016_Q2_553303.xls")
        vals = parser.parse_financial_rows(rows, 1000)
        self.assertAlmostEqual(vals["kap_raporlanan_hbk_ytd"], 0.3921, places=6)


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

    def test_no_dipnot_cover_links_in_canonical_build(self):
        cat = json.loads((ROOT / "data/kap_fr_catalog_2010_2020.json").read_text(encoding="utf-8"))
        by_idx_summary = {
            str((d.get("disclosureBasic", d)).get("disclosureIndex") or ""): ((d.get("disclosureBasic", d)).get("summary") or "")
            for d in cat["disclosures"]
        }
        dipnot_rows = [
            idx for idx in self.frame["disclosure_index"].astype(str) if "dipnot" in by_idx_summary.get(idx, "").lower()
        ]
        self.assertEqual(dipnot_rows, [])

    def test_cleanup_regressions_subrows_capex_eps_and_anomalies(self):
        akenr = self.rows.loc[("AKENR", 2011, 4)]
        self.assertEqual(akenr.F13_kisa_vadeli_finansal_borclar, 207_833_040 + 265_962_296)

        tavhl_q1 = self.rows.loc[("TAVHL", 2016, 1)]
        self.assertEqual(tavhl_q1.F15_capex_ytd, -71_335_000)
        self.assertEqual(tavhl_q1.F15_amortisman_ve_itfa_ytd, 78_691_000)

        tavhl_q3 = self.rows.loc[("TAVHL", 2016, 3)]
        self.assertAlmostEqual(tavhl_q3.kap_raporlanan_hbk_ytd, 0.99, places=6)

        alctl = self.rows.loc[("ALCTL", 2018, 4)]
        self.assertTrue(pd.isna(alctl.kap_raporlanan_hbk_ytd))

        thyao = self.rows.loc[("THYAO", 2013, 4)]
        self.assertTrue(pd.isna(thyao.F16_ar_ge_giderleri_ytd))
        self.assertIn("raw_source_row_shift_ar_ge", thyao.qa_flags)

        gsdde = self.rows.loc[("GSDDE", 2010, 1)]
        self.assertIn("non_standard_financial_leasing_bs_schema", gsdde.qa_flags)

        zoren = self.rows.loc[("ZOREN", 2012, 3)]
        self.assertTrue(pd.isna(zoren.F14_borc_ozkaynak_orani))
        self.assertTrue(np.isfinite(zoren.F14_ozkaynak_aktif_orani))
        zoren_missing = [
            r for r in self.quality["missing_values"]
            if r["ticker"] == "ZOREN" and r["period"] == "2012Q3" and r["column"] == "F14_borc_ozkaynak_orani"
        ]
        self.assertEqual(len(zoren_missing), 1)
        self.assertEqual(zoren_missing[0]["reason"], "non_positive_equity")

    def test_training_matrix_pit_macro_lags_and_negative_equity_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            canon_path = Path(temp) / "canon.csv"
            self.frame.to_csv(canon_path, index=False)
            matrix = tm_builder.build_training_matrix(canonical_csv=canon_path)
        self.assertEqual(len(matrix), 5280)
        q1_60 = matrix[(matrix["observation_period"] == "2019Q1") & (matrix["horizon_days"] == 60)].iloc[0]
        self.assertEqual(q1_60["t0_date"], "2019-03-02")
        self.assertEqual(q1_60["macro_obs_month_lag1"], "2019-01")
        self.assertEqual(q1_60["ip_obs_month_lag2"], "2018-12")
        q2_30 = matrix[(matrix["observation_period"] == "2019Q2") & (matrix["horizon_days"] == 30)].iloc[0]
        self.assertEqual(q2_30["t0_date"], "2019-05-01")
        self.assertEqual(q2_30["macro_obs_month_lag1"], "2019-03")
        self.assertEqual(q2_30["ip_obs_month_lag2"], "2019-02")
        for col in (
            "R01_GPR_lag1q", "R01_GPR_lag2q", "R01_GPR_lag4q",
            "R01_GPRC_TUR_lag1q", "R01_GPRC_TUR_lag2q", "R01_GPRC_TUR_lag4q",
        ):
            self.assertEqual(int(matrix[col].isna().sum()), 0)
        de_vals = matrix["last_known_borc_ozkaynak_orani"].dropna()
        self.assertTrue((de_vals > 0).all())
        self.assertGreater(int((matrix["last_known_is_negative_equity"] == 1).sum()), 0)


if __name__ == "__main__":
    unittest.main()
