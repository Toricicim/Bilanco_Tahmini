"""
fetch_external_macro_and_risk.py
================================
Bilanco_Tahmini reposundaki (docs/model_oncesi/degiskenler.json ve DEGISKEN_LISTESI.md)
tanimlara uygun olarak KAP disindaki P0 Makro (M01-M06) ve Kuresel Risk (R01-R04)
degiskenlerini resmi kaynaklarindan / uluslararasi acik veri arsivlerinden ceker,
ham dosyalari data/external/ altina kaydeder ve aylik/gunluk zaman serilerini uretir.

Kaynaklar:
- R01 & R04 (GPR, GPRT, GPRA): Matteo Iacoviello resmi GPR arsivi (S03)
  https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls
- R02 (GEPU_ppp): Economic Policy Uncertainty resmi arsivi (S04)
  https://www.policyuncertainty.com/media/Global_Policy_Uncertainty_Data.csv
- R03 (OFR FSI): Office of Financial Research Financial Stress Index (S05)
  https://www.financialresearch.gov/financial-stress-index/data/fsi.csv
- M01 & M02 (USD/TRY, EUR/TRY): Günlük kur serisi (Yahoo Finance / TCMB karsiligi)
- M03 (Faiz / Kısa Vadeli Ticari/Piyasa Faizi): OECD MEI / TCMB (TUR.IRSTCI01.ST.M)
- M04 (TÜFE Yıllık % Değişim): TCMB Enflasyon Verileri & OECD MEI (TUR.CPALTT01.GY.M)
- M05 (Yİ-ÜFE Yıllık % Değişim): TCMB Üretici Fiyatları & OECD MEI (TUR.PIEAMP01.GY.M)
- M06 (Sanayi Üretimi Yıllık % Değişim): OECD MEI / TÜİK (TUR.PRINTO01.GYSA.M)
"""

import io
import json
import urllib.request
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

from financial_quality import ofr_available_series

ROOT_DIR = Path(__file__).resolve().parent.parent
EXT_DIR = ROOT_DIR / "data" / "external"
EXT_DIR.mkdir(parents=True, exist_ok=True)


def download_bytes(url: str, cache_name: str) -> bytes:
    cache_path = EXT_DIR / cache_name
    if cache_path.is_file() and cache_path.stat().st_size > 0:
        return cache_path.read_bytes()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BilancoTahminiResearch/1.0"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    cache_path.write_bytes(data)
    return data


def fetch_gpr() -> pd.DataFrame:
    print("[R01/R04] GPR verisi indiriliyor...")
    raw = download_bytes(
        "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls",
        "data_gpr_export.xls",
    )
    df = pd.read_excel(io.BytesIO(raw))
    df = df[["month", "GPR", "GPRT", "GPRA"]].dropna(subset=["month", "GPR"])
    df["ym"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m")
    return df[["ym", "GPR", "GPRT", "GPRA"]].drop_duplicates("ym").sort_values("ym")


def fetch_gepu() -> pd.DataFrame:
    print("[R02] GEPU verisi indiriliyor...")
    raw = download_bytes(
        "https://www.policyuncertainty.com/media/Global_Policy_Uncertainty_Data.csv",
        "Global_Policy_Uncertainty_Data.csv",
    )
    df = pd.read_csv(io.BytesIO(raw))
    # Filter valid numeric Year and Month
    df = df[pd.to_numeric(df["Year"], errors="coerce").notna()]
    df["Year"] = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)
    df["ym"] = df.apply(lambda r: f"{int(r['Year']):04d}-{int(r['Month']):02d}", axis=1)
    col = "GEPU_ppp" if "GEPU_ppp" in df.columns else df.columns[-1]
    df["GEPU_ppp"] = pd.to_numeric(df[col], errors="coerce")
    return df[["ym", "GEPU_ppp"]].dropna().drop_duplicates("ym").sort_values("ym")


def fetch_ofr_fsi() -> pd.DataFrame:
    print("[R03] OFR FSI verisi indiriliyor...")
    raw = download_bytes(
        "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv",
        "ofr_fsi.csv",
    )
    df = pd.read_csv(io.BytesIO(raw))
    df["date"] = pd.to_datetime(df["Date"]).dt.date
    df["OFR_FSI"] = pd.to_numeric(df["OFR FSI"], errors="coerce")
    return df[["date", "OFR_FSI"]].dropna().sort_values("date")


def fetch_fx_daily(symbol: str, col_name: str, cache_name: str) -> pd.DataFrame:
    print(f"[M01/M02] {col_name} gunluk kur verisi indiriliyor...")
    # 2008-01-01 (1199145600) to 2022-01-01 (1640995200)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1=1199145600&period2=1640995200&interval=1d"
    raw = download_bytes(url, cache_name)
    data = json.loads(raw)["chart"]["result"][0]
    timestamps = data["timestamp"]
    closes = data["indicators"]["quote"][0]["close"]
    rows = []
    for ts, c in zip(timestamps, closes):
        if c is not None and c > 0:
            d = datetime.utcfromtimestamp(ts).date()
            rows.append({"date": d, col_name: float(c)})
    df = pd.DataFrame(rows).drop_duplicates("date").sort_values("date")
    return df


def fetch_dbnomics_series(series_path: str, col_name: str, cache_name: str) -> pd.DataFrame:
    print(f"[Makro] {col_name} ({series_path}) indiriliyor...")
    url = f"https://api.db.nomics.world/v22/series/{series_path}?observations=1"
    raw = download_bytes(url, cache_name)
    doc = json.loads(raw)["series"]["docs"][0]
    rows = []
    for p, v in zip(doc["period"], doc["value"]):
        if v != "NA" and v is not None:
            rows.append({"ym": str(p)[:7], col_name: float(v)})
    return pd.DataFrame(rows).drop_duplicates("ym").sort_values("ym")


def fetch_tcmb_inflation() -> tuple[pd.DataFrame, pd.DataFrame]:
    """TCMB resmi web sayfasindaki TUFE ve YI-UFE tablolarini da indirip dogrular."""
    print("[M04/M05] TCMB resmi enflasyon tablolari indiriliyor...")
    raw_cpi = download_bytes(
        "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/Enflasyon+Verileri/Tuketici+Fiyatlari",
        "tcmb_tufe.html",
    )
    soup_cpi = BeautifulSoup(raw_cpi.decode("utf-8", errors="ignore"), "html.parser")
    cpi_rows = []
    for tr in soup_cpi.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) >= 2 and "-" in cells[0] and len(cells[0]) == 7:
            mm, yyyy = cells[0].split("-")
            try:
                cpi_rows.append({"ym": f"{int(yyyy):04d}-{int(mm):02d}", "tcmb_cpi_yoy": float(cells[1].replace(",", "."))})
            except ValueError:
                pass
    df_tcmb_cpi = pd.DataFrame(cpi_rows)

    raw_ppi = download_bytes(
        "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Istatistikler/Enflasyon+Verileri/Uretici+Fiyatlari",
        "tcmb_ufe.html",
    )
    soup_ppi = BeautifulSoup(raw_ppi.decode("utf-8", errors="ignore"), "html.parser")
    ppi_rows = []
    for tr in soup_ppi.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) >= 3 and "-" in cells[0] and len(cells[0]) == 7:
            mm, yyyy = cells[0].split("-")
            val_str = cells[2] if cells[2] else cells[1]
            try:
                ppi_rows.append({"ym": f"{int(yyyy):04d}-{int(mm):02d}", "tcmb_ppi_yoy": float(val_str.replace(",", "."))})
            except ValueError:
                pass
    df_tcmb_ppi = pd.DataFrame(ppi_rows)
    return df_tcmb_cpi, df_tcmb_ppi


def build_macro_and_risk_tables():
    df_gpr = fetch_gpr()
    df_gepu = fetch_gepu()
    df_ofr = fetch_ofr_fsi()
    df_usd = fetch_fx_daily("TRY=X", "USDTRY", "yahoo_usdtry.json")
    df_eur = fetch_fx_daily("EURTRY=X", "EURTRY", "yahoo_eurtry.json")

    df_cpi = fetch_dbnomics_series("OECD/MEI/TUR.CPALTT01.GY.M", "M04_TUFE_YoY", "oecd_cpi.json")
    df_ppi = fetch_dbnomics_series("OECD/MEI/TUR.PIEAMP01.GY.M", "M05_YIUFE_YoY", "oecd_ppi.json")
    df_ip = fetch_dbnomics_series("OECD/MEI/TUR.PRINTO01.GYSA.M", "M06_SanayiUretimi_YoY", "oecd_ip.json")
    df_ir = fetch_dbnomics_series("OECD/MEI/TUR.IRSTCI01.ST.M", "M03_Faiz_Orani", "oecd_ir.json")

    df_tcmb_cpi, df_tcmb_ppi = fetch_tcmb_inflation()

    # Merge monthly series
    monthly = df_gpr.merge(df_gepu, on="ym", how="outer")
    for d in [df_cpi, df_ppi, df_ip, df_ir, df_tcmb_cpi, df_tcmb_ppi]:
        if not d.empty:
            monthly = monthly.merge(d, on="ym", how="outer")
    monthly = monthly.sort_values("ym").reset_index(drop=True)

    # Prefer TCMB official inflation where available, fallback to OECD MEI (identical TURSTAT source)
    if "tcmb_cpi_yoy" in monthly.columns:
        monthly["M04_TUFE_YoY"] = monthly["tcmb_cpi_yoy"].combine_first(monthly["M04_TUFE_YoY"])
    if "tcmb_ppi_yoy" in monthly.columns:
        monthly["M05_YIUFE_YoY"] = monthly["tcmb_ppi_yoy"].combine_first(monthly["M05_YIUFE_YoY"])

    # Compute 1-quarter (3-month) interest rate change for M03
    monthly["M03_Faiz_3Aylik_Degisim"] = monthly["M03_Faiz_Orani"].diff(3)

    # Save monthly table
    monthly_out = EXT_DIR / "monthly_macro_and_risk.csv"
    monthly.to_csv(monthly_out, index=False, encoding="utf-8")
    print(f"Aylik makro ve risk tablosu kaydedildi: {monthly_out} ({len(monthly)} ay)")

    # Merge daily series (FX + OFR FSI)
    daily = df_usd.merge(df_eur, on="date", how="outer").merge(df_ofr, on="date", how="outer")
    daily = daily.sort_values("date").reset_index(drop=True)
    daily["USDTRY"] = daily["USDTRY"].ffill()
    daily["EURTRY"] = daily["EURTRY"].ffill()

    # Work on real FSI observations before merging back to the FX calendar.
    # The calendar is an explicit approximation; historical vintages are separate.
    daily["date"] = pd.to_datetime(daily["date"])
    available = ofr_available_series(daily)
    daily = pd.merge_asof(daily.sort_values("date"), available,
                          left_on="date", right_on="ofr_assumed_available_at", direction="backward")
    daily["OFR_FSI_avail"] = daily.pop("R03_OFR_FSI")
    daily_out = EXT_DIR / "daily_fx_and_fsi.csv"
    daily.to_csv(daily_out, index=False, encoding="utf-8")
    print(f"Gunluk kur ve OFR FSI tablosu kaydedildi: {daily_out} ({len(daily)} gun)")


if __name__ == "__main__":
    build_macro_and_risk_tables()
