"""
run_demo_models.py
==================
Ilk Demo Modeli ve Zaman Bloklu (Walk-Forward / Out-of-Time) Degerlendirme Betigi.

Kullanicinin 4 adimli demo onerisini birebir uygular:
1. Dogrulanmis kanonik veri setini (bist_bilanco_tahmini_2010_2020.csv) okur.
2. Baslangicta 4 temel hedef degiskeni tahmin eder:
   - T01: Hasilat (T01_hasilat_ceyrek) [Akis]
   - T07: Donem Net Kari (T07_donem_net_kari_ceyrek) [Akis]
   - T11: Toplam Varliklar (T11_toplam_varliklar) [Bakiye]
   - T14: Toplam Ozkaynaklar (T14_toplam_ozkaynaklar) [Bakiye]
3. Kati Girdi-Hedef ve Yayin Tarihi (Point-in-Time) Sozlesmesi:
   - Tahmin edilen hedef ceyrek q icin tahmin ani t0 = q_sonu + 70 gun (veya q-1 raporunun yayin tarihi <= t0)
     kontrolu yapilir.
   - Hedef ceyrek q'nun hicbir tutari veya orani girdide KULLANILMAZ (Sifir Veri Sizintisi / No Leakage).
   - Yalnizca t0 aninda kamuya aciklanmis (first_published_at <= t0) gecmis ceyrekler (q-1, q-4, q-5)
     kullanilir. Eger q-1 raporu t0 aninda henuz aciklanmamissa bir onceki bilinen rapor kullanilir.
   - Olcekleme: Sirketler arasi buyukluk farkini (cross-sectional scale) dengelemek icin tum tutar hedefleri
     ve gecmis tutar degiskenleri "Bilinen Son Toplam Varlik (Assets_{q-1})" ile normalize edilir;
     tahmin edilen oranlar tekrar Known_Assets_{q-1} ile carpilarak TL'ye cevrilir ve degerlendirilir.
4. Karsilastirilan Modeller ve Tarih Bloklari:
   - Baz Modeller:
     a) Son Bilinen Deger (Last Known Value: q-1)
     b) Gecen Yilin Ayni Ceyregi (Seasonal Naive: q-4)
   - Ogrenen Modeller (Tarih Bloklu Walk-Forward Test: 2017, 2018, 2019, 2020):
     c) Ridge Regression (Sadece Finansal Gecmis + Sektör)
     d) Ridge Regression (+ Makro & Zaman Eslemesi Duzeltilmis Risk Endeksleri: GPR, GEPU, OFR FSI)
     e) Random Forest (Sadece Finansal Gecmis + Sektör)
     f) Random Forest (+ Makro & Zaman Eslemesi Duzeltilmis Risk Endeksleri: GPR, GEPU, OFR FSI)
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT_DIR / "bist_bilanco_tahmini_2010_2020.csv"
REPORT_OUT = ROOT_DIR / "docs" / "model_oncesi" / "DEMO_MODEL_SONUCLARI_2026-11-07.md"


def build_point_in_time_panel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Her (ticker, year, quarter) hedef gozlemi icin yalnizca gecmiste yayinlanmis
    bilgilerden olusan sızıntısız (leakage-free) girdi tablosunu uretir.
    """
    df = df.sort_values(["ticker", "year", "quarter"]).reset_index(drop=True)
    df["pe_dt"] = pd.to_datetime(df["period_end_date"])
    df["pub_dt"] = pd.to_datetime(df["first_published_at"])

    # Tahmin anı t0: Hedef çeyrek q'nun dönem sonu tarihi (period_end_date).
    # Not: q-1 çeyreğinin finansal raporu normalde q dönem sonuna kadar (45-70 gün içinde) açıklanmış olur.
    # Yine de her satırda pub_dt(q-k) <= pe_dt(q) koşulunu açıkça doğruluyoruz!
    g = df.groupby("ticker", group_keys=False)

    # Gecikmeli yayın tarihleri
    for lag in [1, 2, 4, 5]:
        df[f"pub_dt_lag{lag}"] = g["pub_dt"].shift(lag)

    # q-1'in t0 (= pe_dt) anında yayımlanmış olup olmadığı kontrolü:
    q1_avail = df["pub_dt_lag1"] <= df["pe_dt"]

    base_vars = [
        "T01_hasilat_ceyrek",
        "T03_brut_kar_ceyrek",
        "T04_esas_faaliyet_kari_ceyrek",
        "T07_donem_net_kari_ceyrek",
        "T11_toplam_varliklar",
        "T13_toplam_yukumlulukler",
        "T14_toplam_ozkaynaklar",
        "T15_isletme_nakit_akisi_ceyrek",
        "T08_nakit_ve_nakit_benzerleri",
        "T12_finansal_borclar",
        "F03_brut_kar_marji",
        "F04_esas_faaliyet_marji",
        "F05_net_kar_marji",
        "F06_cfo_aktif_orani",
        "F09_nakit_aktif_orani",
        "F13_finansal_borc_aktif_orani",
        "F13_kisa_finansal_borc_aktif_orani",
        "F14_ozkaynak_aktif_orani",
    ]

    for col in base_vars:
        s1 = g[col].shift(1)
        s2 = g[col].shift(2)
        # Eğer q-1 henüz açıklanmadıysa q-2'yi kullan (point-in-time güvencesi)
        df[f"{col}_q1"] = np.where(q1_avail, s1, s2)
        df[f"{col}_q4"] = g[col].shift(4)
        df[f"{col}_q5"] = g[col].shift(5)

    # Bilinen son aktif büyüklüğü (ölçekleyici: F01)
    scale_assets = df["T11_toplam_varliklar_q1"].replace(0, np.nan)
    df["known_scale_assets"] = scale_assets
    df["log_known_assets"] = np.log1p(scale_assets.clip(lower=0))

    # Bilinen aktif ile ölçeklenmiş geçmiş kalemler ve değişimler (sızıntısız)
    for t_col in ["T01_hasilat_ceyrek", "T07_donem_net_kari_ceyrek", "T11_toplam_varliklar", "T14_toplam_ozkaynaklar"]:
        df[f"{t_col}_q1_scaled"] = df[f"{t_col}_q1"] / scale_assets
        df[f"{t_col}_q4_scaled"] = df[f"{t_col}_q4"] / scale_assets
        df[f"{t_col}_q5_scaled"] = df[f"{t_col}_q5"] / scale_assets
        # Yıllık değişim (q-1 vs q-5), bilinen aktif ile ölçeklenmiş:
        df[f"{t_col}_yoy_diff_scaled"] = (df[f"{t_col}_q1"] - df[f"{t_col}_q5"]) / scale_assets

    # Sızıntısız etkileşim değişkenleri (q-1 borç oranları ile t0'da bilinen makro/risk çarpımı)
    df["X02_pit"] = df["M03_Faiz_3Aylik_Degisim"] * df["F13_finansal_borc_aktif_orani_q1"]
    df["X03_pit"] = df["R03_OFR_FSI_60d_mean"] * df["F13_kisa_finansal_borc_aktif_orani_q1"]

    # Sektör ve çeyrek kukla (dummy) değişkenleri
    sector_dummies = pd.get_dummies(df["sector_group"], prefix="sec", dtype=float)
    quarter_dummies = pd.get_dummies(df["quarter"], prefix="qtr", dtype=float)
    df = pd.concat([df, sector_dummies, quarter_dummies], axis=1)

    return df


def evaluate_predictions(y_true_tl: np.ndarray, y_pred_tl: np.ndarray, scale_tl: np.ndarray) -> dict[str, float]:
    """Hem ölçeklenmiş (% Aktif) MAE/RMSE hem de Log-TL / MedAE ve R2 metriklerini hesaplar."""
    err_scaled = (y_pred_tl - y_true_tl) / scale_tl
    mae_scaled = float(np.mean(np.abs(err_scaled)) * 100.0)  # Aktifin %'si cinsinden ortalama mutlak hata
    rmse_scaled = float(np.sqrt(np.mean(err_scaled ** 2)) * 100.0)
    medae_scaled = float(np.median(np.abs(err_scaled)) * 100.0)
    r2_sc = float(r2_score(y_true_tl / scale_tl, y_pred_tl / scale_tl))
    return {
        "MAE_%Aktif": round(mae_scaled, 3),
        "MedAE_%Aktif": round(medae_scaled, 3),
        "RMSE_%Aktif": round(rmse_scaled, 3),
        "R2_Scaled": round(r2_sc, 4),
    }


def run_experiments():
    df_raw = pd.read_csv(CSV_PATH)
    df = build_point_in_time_panel(df_raw)

    # q-5 gecikmesi gerektiği için 2011Q2 ve sonrası (2011Q2 - 2020Q4) tam gözlemleri al
    panel = df[df["known_scale_assets"].notna() & df["T01_hasilat_ceyrek_q5"].notna()].copy()

    sec_cols = [c for c in panel.columns if c.startswith("sec_") or c.startswith("qtr_")]

    fin_features = [
        "log_known_assets",
        "T01_hasilat_ceyrek_q1_scaled",
        "T01_hasilat_ceyrek_q4_scaled",
        "T01_hasilat_ceyrek_yoy_diff_scaled",
        "T07_donem_net_kari_ceyrek_q1_scaled",
        "T07_donem_net_kari_ceyrek_q4_scaled",
        "T07_donem_net_kari_ceyrek_yoy_diff_scaled",
        "T11_toplam_varliklar_q1_scaled",
        "T11_toplam_varliklar_q4_scaled",
        "T11_toplam_varliklar_yoy_diff_scaled",
        "T14_toplam_ozkaynaklar_q1_scaled",
        "T14_toplam_ozkaynaklar_q4_scaled",
        "T14_toplam_ozkaynaklar_yoy_diff_scaled",
        "F03_brut_kar_marji_q1",
        "F04_esas_faaliyet_marji_q1",
        "F05_net_kar_marji_q1",
        "F06_cfo_aktif_orani_q1",
        "F09_nakit_aktif_orani_q1",
        "F13_finansal_borc_aktif_orani_q1",
        "F14_ozkaynak_aktif_orani_q1",
    ] + sec_cols

    macro_risk_features = [
        "M01_USDTRY_90g_degisim_pct",
        "M02_EURTRY_90g_degisim_pct",
        "M03_Faiz_Orani",
        "M03_Faiz_3Aylik_Degisim",
        "M04_TUFE_YoY",
        "M05_YIUFE_YoY",
        "M06_SanayiUretimi_YoY",
        "R01_GPR",
        "R02_GEPU_ppp",
        "R03_OFR_FSI",
        "R03_OFR_FSI_60d_mean",
        "X02_pit",
        "X03_pit",
    ]

    targets = [
        ("T01_hasilat_ceyrek", "T01 Hasılat (Çeyreklik)"),
        ("T07_donem_net_kari_ceyrek", "T07 Dönem Net Kârı (Çeyreklik)"),
        ("T11_toplam_varliklar", "T11 Toplam Varlıklar"),
        ("T14_toplam_ozkaynaklar", "T14 Toplam Özkaynaklar"),
    ]

    # Walk-forward yıllık test blokları: 2017, 2018, 2019, 2020 (Toplam 4 yıl x 4 çeyrek x 30 şirket = 480 test gözlemi)
    test_years = [2017, 2018, 2019, 2020]

    summary_rows = []
    block_rows = []

    for target_col, target_label in targets:
        # Her test yılı y için: Eğitim kümesi = first_published_at <= (y-1)-12-31 (veya year < y)
        preds_store = {
            "Naive_Last_q1": [],
            "Naive_Seasonal_q4": [],
            "Ridge_FinOnly": [],
            "Ridge_Fin_MacroRisk": [],
            "RF_FinOnly": [],
            "RF_Fin_MacroRisk": [],
        }
        y_true_all = []
        scale_all = []
        yr_all = []

        for ty in test_years:
            train_df = panel[panel["year"] < ty].copy()
            test_df = panel[panel["year"] == ty].copy()

            y_train_scaled = (train_df[target_col] / train_df["known_scale_assets"]).to_numpy()
            # Eğitimde aşırı uç değerleri (%1 - %99) kırp (yalnızca eğitim kümesinde öğrenilir!)
            low_q, high_q = np.nanpercentile(y_train_scaled, [0.5, 99.5])
            y_train_clipped = np.clip(y_train_scaled, low_q, high_q)

            y_test_tl = test_df[target_col].to_numpy()
            scale_test = test_df["known_scale_assets"].to_numpy()

            # 1. Baz Modeller
            p_q1 = test_df[f"{target_col}_q1"].to_numpy()
            p_q4 = test_df[f"{target_col}_q4"].to_numpy()

            # 2. Ridge (Sadece Finansal)
            ridge_fin = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=10.0, random_state=42)),
            ])
            ridge_fin.fit(train_df[fin_features], y_train_clipped)
            p_ridge_fin = ridge_fin.predict(test_df[fin_features]) * scale_test

            # 3. Ridge (Finansal + Makro + Risk)
            ridge_mr = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=10.0, random_state=42)),
            ])
            ridge_mr.fit(train_df[fin_features + macro_risk_features], y_train_clipped)
            p_ridge_mr = ridge_mr.predict(test_df[fin_features + macro_risk_features]) * scale_test

            # 4. Random Forest (Sadece Finansal)
            rf_fin = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestRegressor(n_estimators=200, max_depth=8, min_samples_leaf=5, random_state=42, n_jobs=-1)),
            ])
            rf_fin.fit(train_df[fin_features], y_train_clipped)
            p_rf_fin = rf_fin.predict(test_df[fin_features]) * scale_test

            # 5. Random Forest (Finansal + Makro + Risk)
            rf_mr = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestRegressor(n_estimators=200, max_depth=8, min_samples_leaf=5, random_state=42, n_jobs=-1)),
            ])
            rf_mr.fit(train_df[fin_features + macro_risk_features], y_train_clipped)
            p_rf_mr = rf_mr.predict(test_df[fin_features + macro_risk_features]) * scale_test

            preds_store["Naive_Last_q1"].append(p_q1)
            preds_store["Naive_Seasonal_q4"].append(p_q4)
            preds_store["Ridge_FinOnly"].append(p_ridge_fin)
            preds_store["Ridge_Fin_MacroRisk"].append(p_ridge_mr)
            preds_store["RF_FinOnly"].append(p_rf_fin)
            preds_store["RF_Fin_MacroRisk"].append(p_rf_mr)

            y_true_all.append(y_test_tl)
            scale_all.append(scale_test)
            yr_all.append(test_df["year"].to_numpy())

            # Yıllık blok bazında da MAE_%Aktif kaydet
            for m_name, p_arr in [
                ("Naive_Last_q1", p_q1),
                ("Naive_Seasonal_q4", p_q4),
                ("Ridge_FinOnly", p_ridge_fin),
                ("Ridge_Fin_MacroRisk", p_ridge_mr),
                ("RF_FinOnly", p_rf_fin),
                ("RF_Fin_MacroRisk", p_rf_mr),
            ]:
                m_eval = evaluate_predictions(y_test_tl, p_arr, scale_test)
                block_rows.append({
                    "Target": target_label,
                    "Test_Year": ty,
                    "Model": m_name,
                    **m_eval,
                })

        y_true_cat = np.concatenate(y_true_all)
        scale_cat = np.concatenate(scale_all)

        for m_name, p_list in preds_store.items():
            p_cat = np.concatenate(p_list)
            metrics = evaluate_predictions(y_true_cat, p_cat, scale_cat)
            summary_rows.append({
                "Target": target_label,
                "Model": m_name,
                **metrics,
            })

    df_sum = pd.DataFrame(summary_rows)
    df_blk = pd.DataFrame(block_rows)

    print("\n" + "=" * 80)
    print("WALK-FORWARD TEST SONUCLARI (2017Q1 - 2020Q4, N=480 Gozlem)")
    print("Not: Hata metrikleri Bilinen Son Toplam Varlik (% Aktif) cinsindendir.")
    print("=" * 80)
    for t_lbl in df_sum["Target"].unique():
        print(f"\n>>> HEDEF: {t_lbl}")
        sub = df_sum[df_sum["Target"] == t_lbl].drop(columns=["Target"])
        print(sub.to_string(index=False))

    return df_sum, df_blk


if __name__ == "__main__":
    run_experiments()
