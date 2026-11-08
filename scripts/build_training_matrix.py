"""
build_training_matrix.py
========================
P0-C Sızıntısız (Point-in-Time) Karma Frekanslı Nowcasting Eğitim Matrisi Üreticisi.

AGENTS.md P0-C kurallarına uygun olarak:
1. Kanonik gözlem tablosunu (data/bist_bilanco_tahmini_2010_2020.csv) değiştirmeden okur.
2. Tabloyu 90 güne kopyalamak (sözde-tekrar / pseudoreplication) yerine her şirket-çeyrek
   için belirli bilgi kesim ufukları (horizon_days in {30, 60, 90, 120}) tanımlar.
3. Her t0 kesim anında:
   - Hedef raporun zaten açıklanıp açıklanmadığını (already_published_at_t0 = report_available_at <= t0)
     işaretler (+120g ufkunda erken açıklanan 174 rapor maskelenir).
   - Yalnız available_at <= t0 koşulunu sağlayan geçmiş finansal raporlardan (last_known, lag2, lag4)
     özellik üretir; hedef dönemin toplam varlığını ölçekleme için asla kullanmaz.
   - Günlük serilerden (USDTRY, EURTRY, OFR FSI [+2 ABD iş günü], GPRD [+7 takvim günü])
     yalnız gerçek gözlem günleri (non-ffilled) ve available_at <= t0 üzerinden çeyrek içi
     dağılım/yörünge özelliklerini (_q_mean, _q_last, _q_std, _q_max, _last15d_diff) hesaplar.
   - Türkiye Jeopolitik Risk Endeksi (R01_GPRC_TUR), küresel GPR/GPRT/GPRA (cari ve q-1, q-2, q-4
     gecikmeleri) ile alt sektör (SAVUNMA, ULAŞTIRMA, BİLİŞİM vb.) ve F18 (alınan avanslar /
     ertelenmiş gelirler) çarpımsal etkileşim terimlerini (X04) sabit yön kodlamadan üretir.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from financial_quality import atomic_text, compute_in_quarter_trajectories
from parse_and_build_dataset import EXTERNAL_DIR, OUTPUT_CSV, QUARTER_END_DATES, QUARTER_START_DATES, ROOT_DIR

DEFAULT_MATRIX_CSV = ROOT_DIR / "data" / "training_matrix_pit_2010_2020.csv"
HORIZONS = (30, 60, 90, 120)


def _compute_t0_date(year: int, quarter: int, horizon_days: int) -> pd.Timestamp:
    q_start = pd.Timestamp(f"{year}-{QUARTER_START_DATES[quarter]}")
    p_end = pd.Timestamp(f"{year}-{QUARTER_END_DATES[quarter]}")
    if horizon_days == 30:
        return q_start + pd.Timedelta(days=30)
    if horizon_days == 60:
        return q_start + pd.Timedelta(days=60)
    if horizon_days == 90:
        return p_end
    if horizon_days == 120:
        return p_end + pd.Timedelta(days=30)
    return q_start + pd.Timedelta(days=horizon_days)


def build_training_matrix(
    canonical_csv: Path = OUTPUT_CSV,
    external_dir: Path = EXTERNAL_DIR,
    horizons: tuple[int, ...] = HORIZONS,
) -> pd.DataFrame:
    df = pd.read_csv(canonical_csv)
    df.sort_values(["ticker", "year", "quarter"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    df["available_at_dt"] = pd.to_datetime(df["available_at"], errors="coerce")
    df["report_available_at_dt"] = pd.to_datetime(df["report_available_at"], errors="coerce")

    monthly_path = external_dir / "monthly_macro_and_risk.csv"
    daily_path = external_dir / "daily_fx_and_fsi.csv"

    m_df = pd.read_csv(monthly_path).drop_duplicates(subset=["ym"]).sort_values("ym").reset_index(drop=True)
    d_df = pd.read_csv(daily_path)
    d_df["date"] = pd.to_datetime(d_df["date"])
    d_df.sort_values("date", inplace=True)

    # Pre-index monthly macro by ym
    m_by_ym = m_df.set_index("ym").to_dict(orient="index")

    # Precompute daily trajectories and monthly macro for each unique (year, quarter, horizon_days)
    unique_periods = df[["year", "quarter"]].drop_duplicates().sort_values(["year", "quarter"]).to_records(index=False)
    period_q_list = [(int(y), int(q)) for y, q in unique_periods]

    # Map each (year, quarter) to quarter-end macro/risk for quarter lags (q-1, q-2, q-4)
    q_end_risk: dict[tuple[int, int], dict[str, float | None]] = {}
    for yr, q_num in period_q_list:
        p_end = pd.Timestamp(f"{yr}-{QUARTER_END_DATES[q_num]}")
        ym_lag1 = (pd.Period(p_end.strftime("%Y-%m"), freq="M") - 1).strftime("%Y-%m")
        m_row = m_by_ym.get(ym_lag1, {})
        q_end_risk[(yr, q_num)] = {
            "GPR": m_row.get("GPR"),
            "GPRC_TUR": m_row.get("GPRC_TUR"),
            "GPRT": m_row.get("GPRT"),
            "GPRA": m_row.get("GPRA"),
        }

    macro_traj_cache: dict[tuple[int, int, int], dict[str, Any]] = {}
    for idx_p, (yr, q_num) in enumerate(period_q_list):
        q_start = pd.Timestamp(f"{yr}-{QUARTER_START_DATES[q_num]}")
        p_end = pd.Timestamp(f"{yr}-{QUARTER_END_DATES[q_num]}")
        lag1_key = period_q_list[idx_p - 1] if idx_p >= 1 else None
        lag2_key = period_q_list[idx_p - 2] if idx_p >= 2 else None
        lag4_key = period_q_list[idx_p - 4] if idx_p >= 4 else None

        for h in horizons:
            t0_dt = _compute_t0_date(yr, q_num, h)
            t0_ym = t0_dt.strftime("%Y-%m")
            ym_m1 = (pd.Period(t0_ym, freq="M") - 1).strftime("%Y-%m")
            ym_m2 = (pd.Period(t0_ym, freq="M") - 2).strftime("%Y-%m")
            m1_vals = m_by_ym.get(ym_m1, {})
            m2_vals = m_by_ym.get(ym_m2, {})

            traj = compute_in_quarter_trajectories(d_df, q_start, p_end, t0_dt)
            macro_traj_cache[(yr, q_num, h)] = {
                "quarter_start_date": q_start.strftime("%Y-%m-%d"),
                "t0_date": t0_dt.strftime("%Y-%m-%d"),
                "days_since_quarter_start": int((t0_dt - q_start).days),
                "macro_obs_month_lag1": ym_m1,
                "ip_obs_month_lag2": ym_m2,
                "M03_Faiz_Orani": m1_vals.get("M03_Faiz_Orani"),
                "M03_Faiz_3Aylik_Degisim": m1_vals.get("M03_Faiz_3Aylik_Degisim"),
                "M04_TUFE_YoY": m1_vals.get("M04_TUFE_YoY"),
                "M05_YIUFE_YoY": m1_vals.get("M05_YIUFE_YoY"),
                "M06_SanayiUretimi_YoY": m2_vals.get("M06_SanayiUretimi_YoY"),
                "R01_GPR": m1_vals.get("GPR"),
                "R01_GPRC_TUR": m1_vals.get("GPRC_TUR"),
                "R04_GPRT": m1_vals.get("GPRT"),
                "R04_GPRA": m1_vals.get("GPRA"),
                "R02_GEPU_ppp": m1_vals.get("GEPU_ppp"),
                "R01_GPR_lag1q": q_end_risk.get(lag1_key, {}).get("GPR") if lag1_key else None,
                "R01_GPR_lag2q": q_end_risk.get(lag2_key, {}).get("GPR") if lag2_key else None,
                "R01_GPR_lag4q": q_end_risk.get(lag4_key, {}).get("GPR") if lag4_key else None,
                "R01_GPRC_TUR_lag1q": q_end_risk.get(lag1_key, {}).get("GPRC_TUR") if lag1_key else None,
                "R01_GPRC_TUR_lag2q": q_end_risk.get(lag2_key, {}).get("GPRC_TUR") if lag2_key else None,
                "R01_GPRC_TUR_lag4q": q_end_risk.get(lag4_key, {}).get("GPRC_TUR") if lag4_key else None,
                "R04_GPRT_lag1q": q_end_risk.get(lag1_key, {}).get("GPRT") if lag1_key else None,
                "R04_GPRA_lag1q": q_end_risk.get(lag1_key, {}).get("GPRA") if lag1_key else None,
                **traj,
            }

    last_known_cols = [
        ("hasilat_ceyrek", "T01_hasilat_ceyrek"),
        ("donem_net_kari_ceyrek", "T07_donem_net_kari_ceyrek"),
        ("toplam_varliklar", "T11_toplam_varliklar"),
        ("toplam_ozkaynaklar", "T14_toplam_ozkaynaklar"),
        ("esas_faaliyet_kari_ceyrek", "T04_esas_faaliyet_kari_ceyrek"),
        ("isletme_nakit_akisi_ceyrek", "T15_isletme_nakit_akisi_ceyrek"),
        ("brut_kar_marji", "F03_brut_kar_marji"),
        ("esas_faaliyet_marji", "F04_esas_faaliyet_marji"),
        ("net_kar_marji", "F05_net_kar_marji"),
        ("cfo_aktif_orani", "F06_cfo_aktif_orani"),
        ("tahakkuk_aktif_orani", "F06_tahakkuk_aktif_orani"),
        ("nakit_aktif_orani", "F09_nakit_aktif_orani"),
        ("finansal_borc_aktif_orani", "F13_finansal_borc_aktif_orani"),
        ("kisa_finansal_borc_aktif_orani", "F13_kisa_finansal_borc_aktif_orani"),
        ("ozkaynak_aktif_orani", "F14_ozkaynak_aktif_orani"),
        ("borc_ozkaynak_orani", "F14_borc_ozkaynak_orani"),
        ("maddi_duran_varlik_aktif_orani", "F15_maddi_duran_varlik_aktif_orani"),
        ("capex_hasilat_orani", "F15_capex_hasilat_orani"),
        ("pazarlama_hasilat_orani", "F16_pazarlama_hasilat_orani"),
        ("genel_yonetim_hasilat_orani", "F16_genel_yonetim_hasilat_orani"),
        ("ertelenmis_gelir_kisa_aktif_orani", "F18_ertelenmis_gelir_kisa_aktif_orani"),
    ]

    out_records: list[dict[str, Any]] = []

    for ticker, group in df.groupby("ticker", sort=False):
        g_rows = group.sort_values(["year", "quarter"]).to_dict(orient="records")
        for i, row in enumerate(g_rows):
            yr, q_num = int(row["year"]), int(row["quarter"])
            sub_sec = str(row.get("C01_kap_sub_sector") or "")
            sec_grp = str(row.get("sector_group") or "")
            is_savunma = int("SAVUNMA" in sub_sec.upper())
            is_bilisim = int("BİLİŞİM" in sub_sec.upper() or "BILISIM" in sub_sec.upper())
            is_ulastirma = int("ULAŞTIRMA" in sub_sec.upper() or "ULASTIRMA" in sub_sec.upper())
            is_otomotiv = int("OTOMOTİV" in sec_grp.upper() or "OTOMOTIV" in sec_grp.upper())
            is_enerji = int("ENERJİ" in sec_grp.upper() or "ENERJI" in sec_grp.upper())
            is_gida = int("GIDA" in sec_grp.upper())

            for h in horizons:
                mt = macro_traj_cache[(yr, q_num, h)]
                t0_ts = pd.Timestamp(f"{mt['t0_date']} 23:59:59")
                rep_dt = row["report_available_at_dt"]
                already_pub = bool(pd.notna(rep_dt) and rep_dt <= t0_ts)

                # Search historical reports k in {1, 2, 3, 4} strictly available at t0_ts
                last_row = None
                last_lag = None
                for k in (1, 2, 3, 4):
                    if i - k >= 0:
                        cand = g_rows[i - k]
                        cand_avail = cand["available_at_dt"]
                        if pd.notna(cand_avail) and cand_avail <= t0_ts:
                            last_row = cand
                            last_lag = k
                            break

                lag2_row = None
                if i - 2 >= 0 and pd.notna(g_rows[i - 2]["available_at_dt"]) and g_rows[i - 2]["available_at_dt"] <= t0_ts:
                    lag2_row = g_rows[i - 2]

                lag4_row = None
                if i - 4 >= 0 and pd.notna(g_rows[i - 4]["available_at_dt"]) and g_rows[i - 4]["available_at_dt"] <= t0_ts:
                    lag4_row = g_rows[i - 4]

                rec: dict[str, Any] = {
                    "ticker": ticker,
                    "sector_group": sec_grp,
                    "C01_kap_main_sector": row["C01_kap_main_sector"],
                    "C01_kap_sub_sector": sub_sec,
                    "year": yr,
                    "quarter": q_num,
                    "observation_period": row["observation_period"],
                    "quarter_start_date": mt["quarter_start_date"],
                    "period_end_date": row["period_end_date"],
                    "horizon_days": h,
                    "t0_date": mt["t0_date"],
                    "days_since_quarter_start": mt["days_since_quarter_start"],
                    "report_available_at": row["report_available_at"],
                    "target_available_at": row["available_at"],
                    "already_published_at_t0": already_pub,
                    "eligible_for_nowcast": not already_pub,
                    "qa_flags": row.get("qa_flags", ""),
                    "last_known_period": last_row["observation_period"] if last_row else "",
                    "last_known_lag_quarters": last_lag,
                    "is_q_minus_1_available": int(last_lag == 1) if last_lag is not None else 0,
                }

                for short_name, src_col in last_known_cols:
                    rec[f"last_known_{short_name}"] = last_row.get(src_col) if last_row else None

                for short_name, src_col in (
                    ("hasilat_ceyrek", "T01_hasilat_ceyrek"),
                    ("donem_net_kari_ceyrek", "T07_donem_net_kari_ceyrek"),
                    ("toplam_varliklar", "T11_toplam_varliklar"),
                    ("toplam_ozkaynaklar", "T14_toplam_ozkaynaklar"),
                ):
                    rec[f"lag2_{short_name}"] = lag2_row.get(src_col) if lag2_row else None

                for short_name, src_col in (
                    ("hasilat_ceyrek", "T01_hasilat_ceyrek"),
                    ("donem_net_kari_ceyrek", "T07_donem_net_kari_ceyrek"),
                    ("toplam_varliklar", "T11_toplam_varliklar"),
                    ("toplam_ozkaynaklar", "T14_toplam_ozkaynaklar"),
                    ("esas_faaliyet_kari_ceyrek", "T04_esas_faaliyet_kari_ceyrek"),
                    ("isletme_nakit_akisi_ceyrek", "T15_isletme_nakit_akisi_ceyrek"),
                ):
                    rec[f"lag4_{short_name}"] = lag4_row.get(src_col) if lag4_row else None

                # Add macro and daily trajectory features for (yr, q_num, h)
                for k_mt, v_mt in mt.items():
                    if k_mt not in rec:
                        rec[k_mt] = v_mt

                # Sub-sector flags & X04 heterogeneous risk interactions (learned from data, no fixed sign)
                rec["is_savunma"] = is_savunma
                rec["is_bilisim"] = is_bilisim
                rec["is_ulastirma"] = is_ulastirma
                rec["is_otomotiv"] = is_otomotiv
                rec["is_enerji"] = is_enerji
                rec["is_gida"] = is_gida

                gpr = mt.get("R01_GPR")
                gprc_tur = mt.get("R01_GPRC_TUR")
                gprt = mt.get("R04_GPRT")
                gpra = mt.get("R04_GPRA")
                gprc_tur_lag1 = mt.get("R01_GPRC_TUR_lag1q")
                f18_ratio = rec.get("last_known_ertelenmis_gelir_kisa_aktif_orani")
                fin_debt_ratio = rec.get("last_known_finansal_borc_aktif_orani")
                short_debt_ratio = rec.get("last_known_kisa_finansal_borc_aktif_orani")
                ir_diff = mt.get("M03_Faiz_3Aylik_Degisim")
                ofr_q_mean = mt.get("R03_OFR_FSI_q_mean")

                rec["X04_savunma_x_gpr"] = (is_savunma * gpr) if gpr is not None else None
                rec["X04_savunma_x_gprc_tur"] = (is_savunma * gprc_tur) if gprc_tur is not None else None
                rec["X04_savunma_x_gprt"] = (is_savunma * gprt) if gprt is not None else None
                rec["X04_savunma_x_gpra"] = (is_savunma * gpra) if gpra is not None else None
                rec["X04_savunma_x_gprc_tur_lag1q"] = (is_savunma * gprc_tur_lag1) if gprc_tur_lag1 is not None else None
                rec["X04_ulastirma_x_gpr"] = (is_ulastirma * gpr) if gpr is not None else None
                rec["X04_ulastirma_x_gprc_tur"] = (is_ulastirma * gprc_tur) if gprc_tur is not None else None
                rec["X04_bilisim_x_gprc_tur"] = (is_bilisim * gprc_tur) if gprc_tur is not None else None
                rec["X04_ertelenmis_gelir_x_gpr"] = (
                    (f18_ratio * gpr) if (f18_ratio is not None and pd.notna(f18_ratio) and gpr is not None) else None
                )
                rec["X04_ertelenmis_gelir_x_gprc_tur"] = (
                    (f18_ratio * gprc_tur)
                    if (f18_ratio is not None and pd.notna(f18_ratio) and gprc_tur is not None)
                    else None
                )
                rec["X02_faiz_degisimi_x_last_finansal_borc_aktif"] = (
                    (ir_diff * fin_debt_ratio)
                    if (ir_diff is not None and pd.notna(ir_diff) and fin_debt_ratio is not None and pd.notna(fin_debt_ratio))
                    else None
                )
                rec["X03_ofr_fsi_x_last_kisa_borc_aktif"] = (
                    (ofr_q_mean * short_debt_ratio)
                    if (ofr_q_mean is not None and pd.notna(ofr_q_mean) and short_debt_ratio is not None and pd.notna(short_debt_ratio))
                    else None
                )

                # Primary 4 targets (never used as inputs for the same period)
                rec["target_T01_hasilat_ceyrek"] = row["T01_hasilat_ceyrek"]
                rec["target_T07_donem_net_kari_ceyrek"] = row["T07_donem_net_kari_ceyrek"]
                rec["target_T11_toplam_varliklar"] = row["T11_toplam_varliklar"]
                rec["target_T14_toplam_ozkaynaklar"] = row["T14_toplam_ozkaynaklar"]

                out_records.append(rec)

    matrix = pd.DataFrame(out_records)
    matrix.replace([np.inf, -np.inf], np.nan, inplace=True)
    return matrix


def main() -> None:
    ap = argparse.ArgumentParser(description="Build point-in-time multi-horizon nowcasting training matrix.")
    ap.add_argument("--output", type=Path, default=DEFAULT_MATRIX_CSV, help="Output CSV path.")
    args = ap.parse_args()
    print("P0-C point-in-time nowcasting egitim matrisi olusturuluyor...", flush=True)
    matrix = build_training_matrix()
    atomic_text(args.output, "\ufeff" + matrix.to_csv(index=False))
    pub_120 = int(matrix.loc[matrix["horizon_days"] == 120, "already_published_at_t0"].sum())
    print(
        f"Kaydedildi: {args.output} ({len(matrix)} satir, {len(matrix.columns)} sutun). "
        f"+120g ufkunda zaten aciklanmis (maskelenen) rapor sayisi: {pub_120}"
    )


if __name__ == "__main__":
    main()
