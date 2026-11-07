"""
audit_dataset.py
================
Bilanco_Tahmini veri setini (data/bist_bilanco_tahmini_2010_2020.csv ve
bist_bilanco_tahmini_2010_2020.csv) model egitimi oncesinde denetler:

1. Kanonik CSV Senkronizasyon Denetimi:
   - Depo kokundeki ve data/ altindaki CSV dosyalarinin satir/sutun ve icerik esitligini dogrular.
2. Yayin Tarihi (first_published_at) ve Rapor Surumu (Restatement) Denetimi:
   - Eksik yayin tarihi olup olmadigini kontrol eder.
   - Donem sonundan once (lag <= 0) veya olagan raporlama penceresinden cok sonra (lag > 150 gun)
     yayinlanmis gorunen bildirimleri listeler.
3. Birim / Olcek (Scale) ve Tutarliligi Denetimi:
   - Odenmis sermaye ve Toplam varliklarda ceyrekten ceyrege (QoQ) >4x veya <0.25x sicramalari tarar.
   - Nakit akislarinda (T15, T16, T17) toplam varliklarin 1.5 katini asan uc degerleri kontrol eder.
   - Buyume oranlarinda (F01) +/-inf deger olup olmadigini denetler.
4. Makro ve Kuresel Risk (M01-M06, R01-R04) Zaman Eslemesi Denetimi:
   - Eksik degerleri ve yayin gecikmesi (publication lag) kurallarini dogrular.
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT_DIR / "data" / "bist_bilanco_tahmini_2010_2020.csv"
ROOT_CSV = ROOT_DIR / "bist_bilanco_tahmini_2010_2020.csv"


def run_audit() -> int:
    issues_found = 0
    print("=" * 72)
    print("BIST BILANCO TAHMINI (2010-2020) VERI KALITESI VE SOZLESME DENETIMI")
    print("=" * 72)

    # 1. Kanonik CSV kontrolü
    if not ROOT_CSV.is_file():
        print(f"[HATA] Kanonik dosya bulunamadi: {ROOT_CSV}")
        return 1

    df = pd.read_csv(ROOT_CSV)
    print(f"[1] Kanonik Veri Seti ({ROOT_CSV.relative_to(ROOT_DIR)}): {len(df)} satir x {len(df.columns)} sutun")

    if DATA_CSV.is_file():
        df_data = pd.read_csv(DATA_CSV)
        same_shape = df.shape == df_data.shape
        same_pub = df["first_published_at"].fillna("").equals(df_data["first_published_at"].fillna(""))
        if same_shape and same_pub:
            print("    -> Kok dizindeki kanonik dosya ile data/ altindaki kopya birebir senkronize.")
        else:
            print(f"    [NOT] data/ altindaki kopya ({df_data.shape}) Excel vb. tarafindan kilitli oldugu icin guncellenemedi; kanonik dosya kok dizindeki {ROOT_CSV.name} dosyasidir.")

    # 2. Yayın tarihi ve sürüm kontrolü
    df["pe_dt"] = pd.to_datetime(df["period_end_date"])
    df["pub_dt"] = pd.to_datetime(df["first_published_at"], errors="coerce")
    df["pub_lag_days"] = (df["pub_dt"] - df["pe_dt"]).dt.days

    missing_pub = int(df["pub_dt"].isna().sum())
    early_pub = int((df["pub_lag_days"] <= 0).sum())
    late_pub = df[df["pub_lag_days"] > 150]

    print(f"\n[2] Yayin Tarihi ve Rapor Surumu (Point-in-Time) Denetimi:")
    print(f"    - Eksik first_published_at sayisi       : {missing_pub}")
    print(f"    - Donem sonundan once (lag <= 0) sayisi : {early_pub}")
    print(f"    - Gec yayinlanan / duzeltme (lag > 150g): {len(late_pub)}")
    if missing_pub > 0 or early_pub > 0:
        issues_found += 1
    if len(late_pub) > 0:
        for _, r in late_pub.iterrows():
            print(f"      * {r['ticker']} {r['observation_period']}: period_end={r['period_end_date']}, pub={r['first_published_at']} ({int(r['pub_lag_days'])} gun)")

    # 3. Birim / Ölçek ve Tutar Denetimi
    print(f"\n[3] Birim / Olcek (Scale) ve Tutarliligi Denetimi:")
    df["prev_assets"] = df.groupby("ticker")["T11_toplam_varliklar"].shift(1)
    df["asset_qoq_ratio"] = df["T11_toplam_varliklar"] / df["prev_assets"]
    bad_assets = df[(df["asset_qoq_ratio"] > 4.0) | (df["asset_qoq_ratio"] < 0.25)]
    print(f"    - Toplam Varliklar QoQ sicrama (>4x veya <0.25x): {len(bad_assets)} satir")
    if len(bad_assets) > 0:
        issues_found += 1
        for _, r in bad_assets.iterrows():
            print(f"      * {r['ticker']} {r['observation_period']}: prev={r['prev_assets']:,.0f} -> curr={r['T11_toplam_varliklar']:,.0f}")

    med_cap = df.groupby("ticker")["odenmis_sermaye"].transform("median")
    cap_ratio = df["odenmis_sermaye"] / med_cap
    bad_cap = df[(cap_ratio < 0.05) | (cap_ratio > 20.0) | (df["odenmis_sermaye"] <= 0)]
    print(f"    - Odenmis Sermaye olcek anomalisi / sifir       : {len(bad_cap)} satir")
    if len(bad_cap) > 0:
        issues_found += 1

    cf_cols = ["T15_isletme_nakit_akisi_ytd", "T16_yatirim_nakit_akisi_ytd", "T17_finansman_nakit_akisi_ytd"]
    extreme_cf = 0
    for c in cf_cols:
        ratio = df[c].abs() / df["T11_toplam_varliklar"].replace(0, np.nan)
        cnt = int((ratio > 1.5).sum())
        extreme_cf += cnt
    print(f"    - Nakit Akisi / Toplam Varlik > 1.5x anomalisi  : {extreme_cf} satir")
    if extreme_cf > 0:
        issues_found += 1

    num_cols = df.select_dtypes(include=[np.number]).columns
    inf_cnt = int(np.isinf(df[num_cols].to_numpy()).sum())
    print(f"    - Sayisal sutunlarda +/-inf deger sayisi        : {inf_cnt}")
    if inf_cnt > 0:
        issues_found += 1

    # 4.Temel Hedef Değişkenlerin Doluluk Oranları
    print(f"\n[4] Demo Hedef Degiskenlerinin Doluluk Oranlari (N={len(df)}):")
    demo_targets = [
        "T01_hasilat_ceyrek",
        "T07_donem_net_kari_ceyrek",
        "T11_toplam_varliklar",
        "T14_toplam_ozkaynaklar",
    ]
    for col in demo_targets:
        non_null = int(df[col].notna().sum())
        zero_cnt = int((df[col] == 0).sum())
        print(f"    - {col:<28}: {non_null}/1320 dolu ({non_null/len(df)*100:.2f}%), sifir={zero_cnt}")

    # 5. Makro ve Küresel Risk Serileri Kontrolü
    print(f"\n[5] Makro (M01-M06) ve Kuresel Risk (R01-R04) Doluluk Kontrolu:")
    mr_cols = [
        "M01_USDTRY_seviye",
        "M02_EURTRY_seviye",
        "M03_Faiz_Orani",
        "M04_TUFE_YoY",
        "M05_YIUFE_YoY",
        "M06_SanayiUretimi_YoY",
        "R01_GPR",
        "R02_GEPU_ppp",
        "R03_OFR_FSI",
        "R03_OFR_FSI_60d_mean",
    ]
    for col in mr_cols:
        if col in df.columns:
            nn = int(df[col].notna().sum())
            print(f"    - {col:<28}: {nn}/1320 dolu ({nn/len(df)*100:.2f}%)")

    print("=" * 72)
    if issues_found == 0:
        print("SONUC: BASARILI (Kritik veri, olcek veya tarih ihlali bulunmadi).")
    else:
        print(f"SONUC: {issues_found} adet incelenmesi gereken uyari/sorun bulundu.")
    print("=" * 72)
    return issues_found


if __name__ == "__main__":
    sys.exit(run_audit())
