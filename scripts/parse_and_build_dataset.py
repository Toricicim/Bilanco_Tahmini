"""
parse_and_build_dataset.py
==========================
Bilanco_Tahmini reposundaki (docs/model_oncesi/degiskenler.json ve DEGISKEN_LISTESI.md)
veri sozlesmesine uygun olarak:
1. data/kap_raw_xls/ altindaki KAP finansal rapor dosyalarini (2010-2015 BIFF8 .xls ve
   2016-2020 HTML .xls formatlarini) ayristirir.
2. Her sirket-ceyrek icin birim (TL / 1.000 TL / Bin TL / Milyon TL) normalizasyonu yaparak tum
   parasal kalemleri tam TL (TRY) cinsine cevirir.
3. Yillik kumulatif (YTD) gelir ve nakit akisi kalemlerinden tek ceyreklik (3 aylik)
   akislari (Q1 = YTD_Q1, Q2 = 3Aylik veya YTD_Q2 - YTD_Q1, Q3 = 3Aylik veya YTD_Q3 - YTD_Q2,
   Q4 = YTD_Q4 - YTD_Q3) turetir.
4. P0 cekirdek finansal oranlari (F01-F14), Turkiye makroekonomik serilerini (M01-M06),
   kuresel jeopolitik/ekonomik/finansal risk serilerini (R01-R04) ve rejim etkilesim
   degiskenlerini (X02-X03) acik gecikme/takvim varsayimlariyla esler; tarihsel
   yayin ve vintage dogrulugunu otomatik olarak garanti etmez.
5. Sonuc veri setini Wide Format .csv olarak kaydeder.
"""

from __future__ import annotations

import html
import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fetch_kap_financials_2010_2020 import SELECTED_COMPANIES
from financial_quality import (
    FinancialValues, atomic_text, calendar_fx_change, cash_flow_total,
    finite_sum, missing_details, ofr_available_series, publication_metadata,
    save_json, save_jsonl_gzip, sha256,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
KAP_RAW_DIR = ROOT_DIR / "data" / "kap_raw_xls"
EXTERNAL_DIR = ROOT_DIR / "data" / "external"
OUTPUT_CSV = ROOT_DIR / "data" / "bist_bilanco_tahmini_2010_2020.csv"

QUARTER_END_DATES = {
    1: "03-31",
    2: "06-30",
    3: "09-30",
    4: "12-31",
}


def normalize_tr(text: Any) -> str:
    """Türkçe metinleri karşılaştırma için küçük harfe ve standart ASCII karakterlere indirger."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    s = str(text).strip()
    s = s.replace("İ", "i").replace("I", "ı")
    s = s.lower()
    tr_map = str.maketrans("çğıöşüâîû", "cgiosuaiu")
    s = s.translate(tr_map)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_number(val: Any) -> float | None:
    """KAP tablolarındaki sayısal hücreleri float'a çevirir. Boş hücreler None döner (0 değil)."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    s = str(val).strip()
    if not s or s in ("-", "--", "nan", "None", "null"):
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    elif "." in s:
        parts = s.split(".")
        if (
            len(parts) == 2
            and len(parts[1]) == 3
            and len(parts[0]) >= 1
            and parts[0].lstrip("-").isdigit()
            and parts[1].isdigit()
        ):
            s = s.replace(".", "")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s == "-" or s == ".":
        return None
    try:
        res = float(s)
        return -abs(res) if neg else res
    except ValueError:
        return None


def detect_unit_multiplier(unit_str: str) -> tuple[str, float]:
    """Raporlama birimini (TL, 1.000 TL, Bin TL, Milyon TL) tespit eder ve TL çarpanını döndürür."""
    u_raw = (unit_str or "").strip()
    u = normalize_tr(u_raw)
    if not u:
        return "TL", 1.0
    if "milyon" in u or "1.000.000" in u or "1000000" in u:
        return u_raw, 1_000_000.0
    if "1.000" in u or "1000" in u or "bin" in u or "1,000" in u:
        return u_raw, 1_000.0
    return u_raw, 1.0


def extract_rows_from_biff8(file_path: Path) -> tuple[dict[str, str], list[tuple[str, float | None, float | None]]]:
    """2010-2015 BIFF8 (.xls) dosyasından üstbilgileri ve (etiket, cari_donem, cari_3aylik) satırlarını çıkarır."""
    df = pd.read_excel(file_path, header=None, engine="xlrd")
    meta = {
        "consolidation": "",
        "original_unit": "TL",
        "published_at_header": "",
        "financial_report_published_at": "",
        "embedded_csv_rows_recovered": 0,
    }
    rows: list[tuple[str, float | None, float | None]] = []

    col_ytd = 2
    col_3m: int | None = 4

    for _, r in df.iterrows():
        c0 = str(r[0]).strip() if pd.notna(r[0]) else ""
        # Some legacy KAP BIFF files contain a whole CSV record in column A.
        # Decode the record before interpreting the numeric columns; the number
        # was published but is otherwise invisible to the Excel column reader.
        if c0.startswith('"') and '","' in c0:
            try:
                decoded = next(csv.reader([c0], skipinitialspace=True))
            except csv.Error:
                decoded = []
            if len(decoded) >= 3:
                r = pd.Series(decoded, dtype=object)
                c0 = str(r[0]).strip()
                meta["embedded_csv_rows_recovered"] += 1
        c0_norm = normalize_tr(c0)

        # Dinamik sütun başlığı kontrolü ('Cari Dönem' ve 'Cari Dönem 3 Aylık' hangi sütunda?)
        row_norms = [normalize_tr(r[j]) if j < len(r) and pd.notna(r[j]) else "" for j in range(min(8, len(r)))]
        if any(rn == "cari donem" or rn.startswith("cari donem ") for rn in row_norms[1:]):
            found_ytd = None
            found_3m = None
            for j in range(1, len(row_norms)):
                rn = row_norms[j]
                if rn == "cari donem" and found_ytd is None:
                    found_ytd = j
                elif ("3 aylik" in rn or "uc aylik" in rn) and "cari" in rn and found_3m is None:
                    found_3m = j
            if found_ytd is not None:
                col_ytd = found_ytd
                col_3m = found_3m
            continue

        if not c0:
            continue

        # Üstbilgi satırı: "ASELSAN ... / ASELS , 2010/9 Aylık [] 12.11.2010 11:35:43"
        # veya "KAMUYU AYDINLATMA PLATFORMU [TTRAK] 06.08.2014 17:46:59"
        if ("[]" in c0 or "[" in c0):
            m = re.search(r"\]\s*(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})", c0)
            if m:
                d_str = m.group(1)
                pts = d_str.split()
                d_parts = pts[0].split(".")
                cand_iso = f"{d_parts[2]}-{d_parts[1]}-{d_parts[0]} {pts[1]}"
                if not meta["published_at_header"] or cand_iso < meta["published_at_header"]:
                    meta["published_at_header"] = cand_iso
                if "[]" in c0:
                    # Cover announcements can precede a later financial version.
                    meta["financial_report_published_at"] = max(meta["financial_report_published_at"], cand_iso)

        if c0_norm == "finansal tablo turu":
            for j in range(1, min(6, len(r))):
                if pd.notna(r[j]) and str(r[j]).strip():
                    if not meta["consolidation"]:
                        meta["consolidation"] = str(r[j]).strip()
                    break
            continue
        if c0_norm == "raporlama birimi":
            for j in range(1, min(6, len(r))):
                if pd.notna(r[j]) and str(r[j]).strip():
                    u_cand = str(r[j]).strip()
                    if meta["original_unit"] == "TL" and u_cand:
                        meta["original_unit"] = u_cand
                    break
            continue

        c_ytd_raw = r[col_ytd] if col_ytd < len(r) else None
        c_3m_raw = r[col_3m] if (col_3m is not None and col_3m < len(r)) else None

        val_ytd = parse_number(c_ytd_raw)
        val_3m = parse_number(c_3m_raw)

        # Bazı 2010-2011 tablolarında Cari Dönem sütunu 4. sütuna kaymış olabilir:
        if val_ytd is None and col_ytd == 2 and len(r) > 4:
            alt_ytd = parse_number(r[4])
            if alt_ytd is not None and parse_number(r[2]) is None and parse_number(r[3]) is None:
                val_ytd = alt_ytd
                val_3m = parse_number(r[6]) if len(r) > 6 else None

        rows.append((c0, val_ytd, val_3m))

    return meta, rows


# Hızlı derlenmiş regex kalıpları (2016-2020 HTML .xls dosyaları için)
RE_UNIT = re.compile(r"Sunum Para Birimi\s*</td>\s*<td[^>]*>\s*([^<]+)", re.I | re.S)
RE_CONS = re.compile(r"Finansal Tablo Niteli[^\s<]*\s*</td>\s*<td[^>]*>\s*([^<]+)", re.I | re.S)
RE_LABEL_TR = re.compile(r'content-tr"[^>]*>\s*([^<]+)', re.I | re.S)
RE_CTX_CELL = re.compile(r'<td\s+class="taxonomy-context-value[^"]*"[^>]*>(.*?)</td>', re.I | re.S)
RE_TITLE_VAL = re.compile(r'title="([^"]+)"', re.I | re.S)
RE_INNER_TEXT = re.compile(r"<[^>]+>")


def extract_rows_from_html_xls(file_path: Path) -> tuple[dict[str, str], list[tuple[str, float | None, float | None]]]:
    """2016-2020 HTML tabanlı (.xls) dosyasından üstbilgileri ve (etiket, cari_donem, cari_3aylik) satırlarını hızla çıkarır."""
    html_text = file_path.read_bytes().decode("utf-8", errors="ignore")

    meta = {
        "consolidation": "",
        "original_unit": "TL",
        "published_at_header": "",
    }
    # Tam KAP bildirim sayfası indirildiyse <table class="financial-table öncesindeki başlığa da bak
    fin_tbl_pos = html_text.find("financial-header-title")
    search_slice = html_text[max(0, fin_tbl_pos - 500) : fin_tbl_pos + 15000] if fin_tbl_pos != -1 else html_text[:30000]
    search_slice_unesc = (
        search_slice.replace("\\u003c", "<")
        .replace("\\u003e", ">")
        .replace('\\"', '"')
        .replace("\\r\\n", " ")
        .replace("\\n", " ")
    )
    m_unit = RE_UNIT.search(search_slice_unesc)
    if m_unit:
        meta["original_unit"] = html.unescape(m_unit.group(1)).strip()
    m_cons = RE_CONS.search(search_slice_unesc)
    if m_cons:
        meta["consolidation"] = html.unescape(m_cons.group(1)).strip()

    rows: list[tuple[str, float | None, float | None]] = []
    chunks = html_text.split('<tr class="')
    last_role = ""

    for ch in chunks[1:]:
        head_part = ch[:140]
        if "presentation-disabled" in head_part:
            continue
        if "presentation-enabled" not in head_part:
            continue

        # Tablo rol kodunu kontrol et (general_role_210... = BS, 310... = IS, 510.../520... = CF, 610... = EQ)
        m_role = re.search(r"general_role_(\d{3})", head_part)
        if m_role:
            role_prefix = m_role.group(1)
            if role_prefix != last_role:
                last_role = role_prefix
                if role_prefix.startswith("21"):
                    rows.append(("Finansal Durum Tablosu", None, None))
                elif role_prefix.startswith("31") or role_prefix.startswith("32"):
                    rows.append(("Gelir Tablosu", None, None))
                elif role_prefix.startswith("51") or role_prefix.startswith("52"):
                    rows.append(("Nakit Akış Tablosu", None, None))
                elif role_prefix.startswith("61"):
                    rows.append(("Özkaynak Değişim Tablosu", None, None))

        m_lbl = RE_LABEL_TR.search(ch)
        if not m_lbl:
            continue
        label = html.unescape(m_lbl.group(1)).strip()
        if not label:
            continue

        ctx_cells = RE_CTX_CELL.findall(ch)
        parsed_vals: list[float | None] = []
        for cell_html in ctx_cells:
            m_t = RE_TITLE_VAL.search(cell_html)
            if m_t:
                parsed_vals.append(parse_number(m_t.group(1)))
            else:
                txt_val = html.unescape(RE_INNER_TEXT.sub(" ", cell_html)).strip()
                parsed_vals.append(parse_number(txt_val))

        val_ytd = parsed_vals[0] if len(parsed_vals) >= 1 else None
        val_3m = parsed_vals[2] if len(parsed_vals) >= 3 else None

        rows.append((label, val_ytd, val_3m))

    return meta, rows


def parse_financial_rows(rows: list[tuple[str, float | None, float | None]], mult: float, audit: dict | None = None) -> dict[str, float | None]:
    """
    (etiket, cari_ytd, cari_3m) satır listesini Bilanço, Gelir Tablosu ve Nakit Akış
    bölümlerine ayırarak T01-T17 ve F01-F14 kalemlerini tam TL cinsinden döndürür.
    """
    out = FinancialValues({
        "T01_hasilat_ytd": None,
        "T01_hasilat_3m_raw": None,
        "T02_satislarin_maliyeti_ytd": None,
        "T02_satislarin_maliyeti_3m_raw": None,
        "T03_brut_kar_ytd": None,
        "T03_brut_kar_3m_raw": None,
        "T04_esas_faaliyet_kari_ytd": None,
        "T04_esas_faaliyet_kari_3m_raw": None,
        "T05_finansman_gideri_ytd": None,
        "T05_finansman_gideri_3m_raw": None,
        "F07_finansman_geliri_ytd": None,
        "F07_finansman_geliri_3m_raw": None,
        "T06_vergi_gideri_geliri_ytd": None,
        "T06_vergi_gideri_geliri_3m_raw": None,
        "T07_donem_net_kari_ytd": None,
        "T07_donem_net_kari_3m_raw": None,
        "T07_ana_ortaklik_net_kari_ytd": None,
        "T07_ana_ortaklik_net_kari_3m_raw": None,
        "T08_nakit_ve_nakit_benzerleri": None,
        "F10_kisa_vadeli_ticari_alacaklar": None,
        "F10_uzun_vadeli_ticari_alacaklar": None,
        "T09_ticari_alacaklar": None,
        "T10_stoklar": None,
        "donen_varliklar": None,
        "duran_varliklar": None,
        "T11_toplam_varliklar": None,
        "F13_kisa_vadeli_finansal_borclar": None,
        "F13_uzun_vadeli_finansal_borclar": None,
        "T12_finansal_borclar": None,
        "kisa_vadeli_ticari_borclar": None,
        "uzun_vadeli_ticari_borclar": None,
        "F12_ticari_borclar": None,
        "kisa_vadeli_yukumlulukler": None,
        "uzun_vadeli_yukumlulukler": None,
        "T13_toplam_yukumlulukler": None,
        "T14_toplam_ozkaynaklar": None,
        "T14_ana_ortakliga_ait_ozkaynaklar": None,
        "odenmis_sermaye": None,
        "kap_raporlanan_hbk_ytd": None,
        "T15_isletme_nakit_akisi_ytd": None,
        "T16_yatirim_nakit_akisi_ytd": None,
        "T17_finansman_nakit_akisi_ytd": None,
    })

    def optional_round(value, digits):
        return round(value, digits) if value is not None else None

    def scale(v: float | None) -> float | None:
        return round(v * mult, 2) if v is not None else None

    statement = "BS"
    bs_section = "DONEN"
    cf_section = ""

    kisa_borc_parts: list[float] = []
    uzun_borc_parts: list[float] = []
    alt_cash_parts: list[float] = []
    alt_rev_ytd: float | None = None
    alt_rev_3m: float | None = None
    alt_cogs_ytd: float | None = None
    alt_cogs_3m: float | None = None

    cf_priorities: dict[str, int] = {}
    alternative_revenue_parts = []
    alternative_cost_parts = []
    flags = set()
    financial_gross = None

    for label, v_ytd, v_3m in rows:
        out.reading(label, v_ytd, v_3m)
        ln = normalize_tr(label)
        if not ln:
            continue

        # Tablo geçişlerini tespit et (geri dönüşlere de izin ver, örn. TTRAK_2014_Q2 kapak satırları)
        if ln in ("bilanco", "finansal durum tablosu", "finansal durum tablosu (bilanco)", "donen varliklar", "aktif kalemler"):
            statement = "BS"
            bs_section = "DONEN"
            if ln == "donen varliklar" and v_ytd is not None:
                out["donen_varliklar"] = scale(v_ytd)
            continue
        elif ln == "nazim hesaplar":
            statement = "OFF_BS"
            continue
        elif ln in (
            "gelir tablosu",
            "kapsamli gelir tablosu",
            "kar veya zarar ve diger kapsamli gelir tablosu",
            "kar veya zarar tablosu",
            "kar veya zarar kismi",
            "surdurulen faaliyetler",
        ):
            statement = "IS"
            continue
        elif (
            ln in ("nakit akim tablosu", "nakit akis tablosu", "nakit akis tablosu dolayli yontem", "nakit akis tablosu dogrudan yontem")
            or "isletme faaliyetlerine iliskin nakit akimlari" in ln
            or "a. isletme faaliyetlerinden nakit akislari" in ln
            or "a - esas faaliyetlere iliskin nakit akislari" in ln
            or "faaliyetlerden kaynaklanan nakit akimlari" in ln
        ):
            statement = "CF"
            heading_total = cash_flow_total(ln)
            if v_ytd is not None and heading_total is not None:
                field, priority = heading_total
                out[field] = scale(v_ytd)
                cf_priorities[field] = priority
            cf_section = "OP"
            continue
        elif "ozsermaye degisim tablosu" in ln or "ozkaynak degisim tablosu" in ln or "ozkaynaklar degisim tablosu" in ln or "finansal tablo dipnot" in ln:
            statement = "EQ"
            continue

        # ---------------- 1. BİLANÇO (BS) ----------------
        if statement == "BS":
            if ln == "donen varliklar":
                bs_section = "DONEN"
                if v_ytd is not None:
                    out["donen_varliklar"] = scale(v_ytd)
                continue
            elif ln == "toplam donen varliklar":
                if v_ytd is not None:
                    out["donen_varliklar"] = scale(v_ytd)
                bs_section = "DURAN"
                continue
            elif ln == "duran varliklar":
                bs_section = "DURAN"
                if v_ytd is not None:
                    out["duran_varliklar"] = scale(v_ytd)
                continue
            elif ln == "toplam duran varliklar":
                if v_ytd is not None:
                    out["duran_varliklar"] = scale(v_ytd)
                continue
            elif ln in ("toplam varliklar", "toplam aktifler", "aktif toplami"):
                if v_ytd is not None:
                    out["T11_toplam_varliklar"] = scale(v_ytd)
                bs_section = "KISA_YUK"
                continue
            elif ln in ("kisa vadeli yukumlulukler", "pasif kalemler"):
                bs_section = "KISA_YUK"
                if ln == "kisa vadeli yukumlulukler" and v_ytd is not None:
                    out["kisa_vadeli_yukumlulukler"] = scale(v_ytd)
                continue
            elif ln == "toplam kisa vadeli yukumlulukler":
                if v_ytd is not None:
                    out["kisa_vadeli_yukumlulukler"] = scale(v_ytd)
                bs_section = "UZUN_YUK"
                continue
            elif ln == "uzun vadeli yukumlulukler":
                bs_section = "UZUN_YUK"
                if v_ytd is not None:
                    out["uzun_vadeli_yukumlulukler"] = scale(v_ytd)
                continue
            elif ln == "toplam uzun vadeli yukumlulukler":
                if v_ytd is not None:
                    out["uzun_vadeli_yukumlulukler"] = scale(v_ytd)
                continue
            elif ln == "toplam yukumlulukler":
                if v_ytd is not None:
                    out["T13_toplam_yukumlulukler"] = scale(v_ytd)
                bs_section = "OZKAYNAK"
                continue
            elif ln in ("o z k a y n a k l a r", "ozkaynaklar", "toplam ozkaynaklar"):
                bs_section = "OZKAYNAK"
                if v_ytd is not None:
                    out["T14_toplam_ozkaynaklar"] = scale(v_ytd)
                continue
            elif ln == "ana ortakliga ait ozkaynaklar":
                if v_ytd is not None:
                    out["T14_ana_ortakliga_ait_ozkaynaklar"] = scale(v_ytd)
                continue
            elif ln in ("odenmis sermaye", "sermaye", "cikarilmis sermaye") and (out["odenmis_sermaye"] is None or out["odenmis_sermaye"] == 0):
                if v_ytd is not None and v_ytd != 0:
                    out["odenmis_sermaye"] = scale(v_ytd)
                continue

            if bs_section == "DONEN":
                if ln in ("nakit ve benzerleri", "nakit ve nakit benzerleri") and out["T08_nakit_ve_nakit_benzerleri"] is None:
                    out["T08_nakit_ve_nakit_benzerleri"] = scale(v_ytd)
                elif ln in ("nakit degerler", "bankalar") and v_ytd is not None:
                    alt_cash_parts.append(scale(v_ytd))
                elif ln == "ticari alacaklar" and out["F10_kisa_vadeli_ticari_alacaklar"] is None:
                    out["F10_kisa_vadeli_ticari_alacaklar"] = scale(v_ytd)
                elif ln == "stoklar" and out["T10_stoklar"] is None:
                    out["T10_stoklar"] = scale(v_ytd)
            elif bs_section == "DURAN":
                if ln == "ticari alacaklar" and out["F10_uzun_vadeli_ticari_alacaklar"] is None:
                    out["F10_uzun_vadeli_ticari_alacaklar"] = scale(v_ytd)
            elif bs_section == "KISA_YUK":
                if ln in ("finansal borclar", "kisa vadeli borclanmalar", "uzun vadeli borclanmalarin kisa vadeli kisimlari", "alinan krediler"):
                    if v_ytd is not None:
                        kisa_borc_parts.append(scale(v_ytd))
                elif ln == "ticari borclar" and out["kisa_vadeli_ticari_borclar"] is None:
                    out["kisa_vadeli_ticari_borclar"] = scale(v_ytd)
            elif bs_section == "UZUN_YUK":
                if ln in ("finansal borclar", "uzun vadeli borclanmalar"):
                    if v_ytd is not None:
                        uzun_borc_parts.append(scale(v_ytd))
                elif ln == "ticari borclar" and out["uzun_vadeli_ticari_borclar"] is None:
                    out["uzun_vadeli_ticari_borclar"] = scale(v_ytd)

        # ---------------- 2. GELİR TABLOSU (IS) ----------------
        elif statement == "IS":
            if ln in ("satis gelirleri", "hasilat") and (out["T01_hasilat_ytd"] is None or out["T01_hasilat_ytd"] == 0):
                if v_ytd is not None:
                    out["T01_hasilat_ytd"] = scale(v_ytd)
                    out["T01_hasilat_3m_raw"] = scale(v_3m)
            elif (
                ln in ("finans sektoru faaliyetleri hasilati", "faiz, ucret, prim, komisyon ve diger gelirler", "esas faaliyet gelirleri")
                or ln.startswith("- denizcilik sektoru gelirleri")
                or ln.startswith("- denizcilik sektoru hasilati")
                or ln.startswith("- grup-ici hizmet faaliyetlerinden gelirler")
            ):
                if v_ytd is not None and v_ytd != 0:
                    alt_rev_ytd = (alt_rev_ytd or 0.0) + scale(v_ytd)
                    alternative_revenue_parts.append({"label": label, "value": scale(v_ytd)})
                    if "finans sektoru" in ln:
                        flags.add("mixed_activity_income_statement")
                    if v_3m is not None:
                        alt_rev_3m = (alt_rev_3m or 0.0) + scale(v_3m)
            elif ln in ("satislarin maliyeti (-)", "satislarin maliyeti") and (out["T02_satislarin_maliyeti_ytd"] is None or out["T02_satislarin_maliyeti_ytd"] == 0):
                if v_ytd is not None:
                    out["T02_satislarin_maliyeti_ytd"] = scale(v_ytd)
                    out["T02_satislarin_maliyeti_3m_raw"] = scale(v_3m)
            elif (
                ln in ("finans sektoru faaliyetleri maliyeti (-)", "faiz, ucret, prim, komisyon ve diger giderler (-)", "esas faaliyet giderleri (-)")
                or ln.startswith("- denizcilik sektoru giderleri")
                or ln.startswith("- grup-ici hizmet faaliyetlerinden giderler")
            ):
                if v_ytd is not None and v_ytd != 0:
                    alt_cogs_ytd = (alt_cogs_ytd or 0.0) + scale(v_ytd)
                    alternative_cost_parts.append({"label": label, "value": scale(v_ytd)})
                    if v_3m is not None:
                        alt_cogs_3m = (alt_cogs_3m or 0.0) + scale(v_3m)
            elif ln in ("finans sektoru faaliyetlerinden brut kar (zarar)", "finans sektoru faaliyetlerinden brut kar/zarar"):
                financial_gross = scale(v_ytd)
                if v_ytd not in (None, 0):
                    flags.add("mixed_activity_income_statement")
            elif ln in ("brut kar/zarar", "brut kar (zarar)", "ticari faaliyetlerden brut kar (zarar)", "ticari faaliyetlerden brut kar/zarar"):
                # Some templates report zero in the aggregate while reporting a
                # nonzero commercial subtotal and explicitly zero financial gross.
                # Preserve the complete subtotal reconciliation and flag the
                # contradictory aggregate, rather than replacing it with zero.
                if ln in ("brut kar/zarar", "brut kar (zarar)") and v_ytd == 0 and financial_gross == 0 and out["T03_brut_kar_ytd"] not in (None, 0):
                    flags.add("gross_total_conflicts_with_complete_subtotals")
                    out.fields["T03_brut_kar_ytd"]["status"] = "reconciled_from_gross_subtotals"
                    continue
                if ln in ("brut kar/zarar", "brut kar (zarar)") or out["T03_brut_kar_ytd"] is None or (out["T03_brut_kar_ytd"] == 0 and v_ytd):
                    if v_ytd is not None:
                        out["T03_brut_kar_ytd"] = scale(v_ytd)
                        out["T03_brut_kar_3m_raw"] = scale(v_3m)
            elif ln in ("faaliyet kari/zarari", "esas faaliyet kari/zarari", "esas faaliyet kari (zarari)", "net faaliyet k/z", "esas faaliyet kari veya zarari") and out["T04_esas_faaliyet_kari_ytd"] is None:
                if v_ytd is not None:
                    out["T04_esas_faaliyet_kari_ytd"] = scale(v_ytd)
                    out["T04_esas_faaliyet_kari_3m_raw"] = scale(v_3m)
            elif ln in ("finansal gelirler", "finansman gelirleri", "esas faaliyet disi finansal gelirler") and out["F07_finansman_geliri_ytd"] is None:
                if v_ytd is not None:
                    out["F07_finansman_geliri_ytd"] = scale(v_ytd)
                    out["F07_finansman_geliri_3m_raw"] = scale(v_3m)
            elif ln in ("finansal giderler (-)", "finansman giderleri (-)", "finansman giderleri", "esas faaliyet disi finansal giderler (-)") and out["T05_finansman_gideri_ytd"] is None:
                if v_ytd is not None:
                    out["T05_finansman_gideri_ytd"] = scale(v_ytd)
                    out["T05_finansman_gideri_3m_raw"] = scale(v_3m)
            elif ("surdurulen faaliyetler vergi" in ln or ln == "vergi karsiligi (-)") and not ln.startswith("-") and out["T06_vergi_gideri_geliri_ytd"] is None:
                if v_ytd is not None:
                    out["T06_vergi_gideri_geliri_ytd"] = scale(v_ytd)
                    out["T06_vergi_gideri_geliri_3m_raw"] = scale(v_3m)
            elif ln in (
                "donem kari/zarari",
                "donem kari (zarari)",
                "surdurulen faaliyetler donem kari/zarari",
                "surdurulen faaliyetler donem kari (zarari)",
                "net donem kari/zarari",
                "net donem kari (zarari)",
                "donem net kari veya zarari",
            ):
                if out["T07_donem_net_kari_ytd"] is None or ln in ("donem kari/zarari", "donem kari (zarari)", "donem net kari veya zarari"):
                    if v_ytd is not None:
                        out["T07_donem_net_kari_ytd"] = scale(v_ytd)
                        out["T07_donem_net_kari_3m_raw"] = scale(v_3m)
            elif ln in ("ana ortaklik paylari", "- ana ortaklik paylari") and out["T07_ana_ortaklik_net_kari_ytd"] is None:
                if v_ytd is not None:
                    out["T07_ana_ortaklik_net_kari_ytd"] = scale(v_ytd)
                    out["T07_ana_ortaklik_net_kari_3m_raw"] = scale(v_3m)
            elif ln in (
                "hisse basina kazanc",
                "pay basina kazanc",
                "adi hisse basina kazanc",
                "surdurulen faaliyetlerden pay basina kazanc",
                "- surdurulen faaliyetlerden pay basina kazanc",
                "surdurulen faaliyetlerden hisse basina kazanc",
            ) and out["kap_raporlanan_hbk_ytd"] is None:
                if v_ytd is not None:
                    out["kap_raporlanan_hbk_ytd"] = float(v_ytd)

        # ---------------- 3. NAKİT AKIŞ TABLOSU (CF) ----------------
        elif statement == "CF":
            total = cash_flow_total(ln)
            if total is not None:
                field, priority = total
                if v_ytd is not None and priority >= cf_priorities.get(field, 0):
                    out[field] = scale(v_ytd)
                    cf_priorities[field] = priority
                continue
    out.deriving()

    # Hasılat yedeği (GSDDE 2010-2016 gibi esas faaliyet / denizcilik geliri alt satırda yer alanlar için)
    if (out["T01_hasilat_ytd"] is None or out["T01_hasilat_ytd"] == 0) and alt_rev_ytd is not None:
        out["T01_hasilat_ytd"] = round(alt_rev_ytd, 2)
        out["T01_hasilat_3m_raw"] = round(alt_rev_3m, 2) if alt_rev_3m is not None else None
    if (out["T02_satislarin_maliyeti_ytd"] is None or out["T02_satislarin_maliyeti_ytd"] == 0) and alt_cogs_ytd is not None:
        out["T02_satislarin_maliyeti_ytd"] = round(alt_cogs_ytd, 2)
        out["T02_satislarin_maliyeti_3m_raw"] = round(alt_cogs_3m, 2) if alt_cogs_3m is not None else None

    # Bilanço türetilmiş toplam kontrolü:
    if out["T08_nakit_ve_nakit_benzerleri"] is None and alt_cash_parts:
        out["T08_nakit_ve_nakit_benzerleri"] = round(sum(alt_cash_parts), 2)
    if out["F10_kisa_vadeli_ticari_alacaklar"] is not None or out["F10_uzun_vadeli_ticari_alacaklar"] is not None:
        out["T09_ticari_alacaklar"] = optional_round(
            finite_sum([out["F10_kisa_vadeli_ticari_alacaklar"], out["F10_uzun_vadeli_ticari_alacaklar"]]), 2
        )
    if kisa_borc_parts:
        out["F13_kisa_vadeli_finansal_borclar"] = round(sum(kisa_borc_parts), 2)
    if uzun_borc_parts:
        out["F13_uzun_vadeli_finansal_borclar"] = round(sum(uzun_borc_parts), 2)
    if out["F13_kisa_vadeli_finansal_borclar"] is not None or out["F13_uzun_vadeli_finansal_borclar"] is not None:
        out["T12_finansal_borclar"] = optional_round(
            finite_sum([out["F13_kisa_vadeli_finansal_borclar"], out["F13_uzun_vadeli_finansal_borclar"]]), 2
        )
    if out["kisa_vadeli_ticari_borclar"] is not None or out["uzun_vadeli_ticari_borclar"] is not None:
        out["F12_ticari_borclar"] = optional_round(
            finite_sum([out["kisa_vadeli_ticari_borclar"], out["uzun_vadeli_ticari_borclar"]]), 2
        )
    if out["T11_toplam_varliklar"] is None:
        if out["donen_varliklar"] is not None and out["duran_varliklar"] is not None:
            out["T11_toplam_varliklar"] = round(out["donen_varliklar"] + out["duran_varliklar"], 2)
    if out["T13_toplam_yukumlulukler"] is None:
        if out["kisa_vadeli_yukumlulukler"] is not None and out["uzun_vadeli_yukumlulukler"] is not None:
            out["T13_toplam_yukumlulukler"] = round(
                (out["kisa_vadeli_yukumlulukler"] or 0.0) + (out["uzun_vadeli_yukumlulukler"] or 0.0), 2
            )
        elif out["T11_toplam_varliklar"] is not None and out["T14_toplam_ozkaynaklar"] is not None:
            out["T13_toplam_yukumlulukler"] = round(out["T11_toplam_varliklar"] - out["T14_toplam_ozkaynaklar"], 2)
    if out["T03_brut_kar_ytd"] is None and out["T01_hasilat_ytd"] is not None and out["T02_satislarin_maliyeti_ytd"] is not None:
        out["T03_brut_kar_ytd"] = round(out["T01_hasilat_ytd"] + out["T02_satislarin_maliyeti_ytd"], 2)
        if out["T01_hasilat_3m_raw"] is not None and out["T02_satislarin_maliyeti_3m_raw"] is not None:
            out["T03_brut_kar_3m_raw"] = round(out["T01_hasilat_3m_raw"] + out["T02_satislarin_maliyeti_3m_raw"], 2)

    if audit is not None:
        audit.update(out.diagnostics(rows))
        audit["flags"] = sorted(flags)
        audit["alternative_revenue_parts"] = alternative_revenue_parts
        audit["alternative_cost_parts"] = alternative_cost_parts
        audit["financial_gross_subtotal"] = financial_gross
    return dict(out)


def load_catalog_dates() -> tuple[dict[tuple[str, int, int], tuple[str, str]], dict[str, str]]:
    """
    data/kap_fr_catalog_2010_2020.json dosyasından:
    1) (ticker, year, quarter) -> (first_published_at, disclosure_index)
    2) disclosure_index -> first_published_at
    sözlüklerini oluşturur.
    """
    cat_path = ROOT_DIR / "data" / "kap_fr_catalog_2010_2020.json"
    if not cat_path.is_file():
        return {}, {}
    data = json.loads(cat_path.read_text(encoding="utf-8"))
    disclosures = data.get("disclosures", [])
    donem_map = {
        "3 Aylık": 1,
        "03 Aylık": 1,
        "1. Çeyrek": 1,
        "6 Aylık": 2,
        "06 Aylık": 2,
        "2. Çeyrek": 2,
        "9 Aylık": 3,
        "09 Aylık": 3,
        "3. Çeyrek": 3,
        "Yıllık": 4,
        "12 Aylık": 4,
        "4. Çeyrek": 4,
    }
    alias_map = {"KRDMA": "KRDMD", "KRDMB": "KRDMD", "KRDMD": "KRDMD"}
    result: dict[tuple[str, int, int], tuple[str, str]] = {}
    by_disc_idx: dict[str, str] = {}

    for d in disclosures:
        basic = d.get("disclosureBasic", d)
        subj = (basic.get("subject") or "").strip()
        if "Faaliyet Raporu" in subj or "Sorumluluk Beyan" in subj:
            continue
        pub_raw = (basic.get("publishDate") or "").strip()
        pub_iso = pub_raw
        m_dt = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)$", pub_raw)
        if m_dt:
            t_part = m_dt.group(4) if len(m_dt.group(4)) == 8 else f"{m_dt.group(4)}:00"
            pub_iso = f"{m_dt.group(3)}-{m_dt.group(2)}-{m_dt.group(1)} {t_part}"
        disc_idx = str(basic.get("disclosureIndex") or "")
        if disc_idx and pub_iso:
            by_disc_idx[disc_idx] = pub_iso

        codes = [c.strip() for c in re.split(r"[, \-]+", basic.get("stockCodes") or basic.get("stockCode") or "") if c.strip()]
        matched_t = None
        for c in codes:
            m = alias_map.get(c, c)
            if m in SELECTED_COMPANIES:
                matched_t = m
                break
        if not matched_t:
            continue
        yr = basic.get("year")
        q = basic.get("period")
        if not q:
            donem = (basic.get("ruleType") or basic.get("ruleTypeTerm") or basic.get("donem") or "").strip()
            q = donem_map.get(donem)
        if not yr or not q or int(q) not in (1, 2, 3, 4):
            continue
        key = (matched_t, int(yr), int(q))
        if key not in result or (pub_iso and pub_iso < result[key][0]):
            result[key] = (pub_iso, disc_idx)
    return result, by_disc_idx


def derive_quarterly_flows(df):
    """Derive single-quarter flows and retain the exact method for each value."""
    quarter_methods = {}
    needs_previous_date = pd.Series(False, index=df.index)
    # ---------------- YTD -> ÇEYREKLİK (3 AYLIK) AKIŞ DÖNÜŞÜMÜ ----------------
    is_flow_items = [
        ("T01_hasilat", "T01_hasilat_ytd", "T01_hasilat_3m_raw"),
        ("T02_satislarin_maliyeti", "T02_satislarin_maliyeti_ytd", "T02_satislarin_maliyeti_3m_raw"),
        ("T03_brut_kar", "T03_brut_kar_ytd", "T03_brut_kar_3m_raw"),
        ("T04_esas_faaliyet_kari", "T04_esas_faaliyet_kari_ytd", "T04_esas_faaliyet_kari_3m_raw"),
        ("T05_finansman_gideri", "T05_finansman_gideri_ytd", "T05_finansman_gideri_3m_raw"),
        ("F07_finansman_geliri", "F07_finansman_geliri_ytd", "F07_finansman_geliri_3m_raw"),
        ("T06_vergi_gideri_geliri", "T06_vergi_gideri_geliri_ytd", "T06_vergi_gideri_geliri_3m_raw"),
        ("T07_donem_net_kari", "T07_donem_net_kari_ytd", "T07_donem_net_kari_3m_raw"),
        ("T07_ana_ortaklik_net_kari", "T07_ana_ortaklik_net_kari_ytd", "T07_ana_ortaklik_net_kari_3m_raw"),
    ]

    for base_col, ytd_col, raw3m_col in is_flow_items:
        prev_ytd = df.groupby(["ticker", "year"])[ytd_col].shift(1)
        diff_ytd = df[ytd_col] - prev_ytd
        q_col = f"{base_col}_ceyrek"
        # Q4 is defined by the annual-minus-nine-month convention. For interim
        # reports a supplied quarter value, including zero, takes precedence.
        use_reported = df[raw3m_col].notna() & (df["quarter"] != 4)
        df[q_col] = np.where(
            df["quarter"] == 1,
            df[ytd_col],
            np.where(
                use_reported,
                df[raw3m_col],
                diff_ytd,
            ),
        )
        needs_previous_date |= (df["quarter"] != 1) & ~use_reported & df[q_col].notna()
        for index, row in df.iterrows():
            identity = (row["ticker"], int(row["year"]), int(row["quarter"]))
            method = "q1_ytd" if row["quarter"] == 1 else "reported_3m" if use_reported.loc[index] else "ytd_difference"
            quarter_methods.setdefault(identity, {})[q_col] = {"method": method, "current_component": ytd_col, "previous_component_required": method == "ytd_difference"}
        df.drop(columns=[raw3m_col], inplace=True)

    for cf_base in ["T15_isletme_nakit_akisi", "T16_yatirim_nakit_akisi", "T17_finansman_nakit_akisi"]:
        ytd_col = f"{cf_base}_ytd"
        prev_ytd = df.groupby(["ticker", "year"])[ytd_col].shift(1)
        df[f"{cf_base}_ceyrek"] = np.where(df["quarter"] == 1, df[ytd_col], df[ytd_col] - prev_ytd)
        needs_previous_date |= (df["quarter"] != 1) & df[f"{cf_base}_ceyrek"].notna()
        for _, row in df.iterrows():
            identity = (row["ticker"], int(row["year"]), int(row["quarter"]))
            quarter_methods.setdefault(identity, {})[f"{cf_base}_ceyrek"] = {"method": "q1_ytd" if row["quarter"] == 1 else "ytd_difference", "current_component": ytd_col, "previous_component_required": row["quarter"] != 1}

    if "source_available_at" in df:
        current = pd.to_datetime(df["source_available_at"], errors="coerce")
        previous = current.groupby(df["ticker"]).shift(1)
        effective = pd.concat([current, previous.where(needs_previous_date)], axis=1).max(axis=1)
        effective = effective.mask(current.isna() | (needs_previous_date & previous.isna()))
        df["available_at"] = effective.dt.strftime("%Y-%m-%d %H:%M:%S")
    return df, quarter_methods


def select_source_files(paths, by_disc_idx):
    """Choose the earliest dated file, not the lexicographically largest revision."""
    file_map: dict[tuple[str, int, int], Path] = {}
    ranks = {}
    for fp in sorted(paths):
        m = re.match(r"^([A-Z0-9]+)_(\d{4})_Q([1-4])(?:_(\d+))?\.xls$", fp.name)
        if m:
            t, y, q, index = m.groups()
            if t in SELECTED_COMPANIES:
                key = (t, int(y), int(q))
                date = by_disc_idx.get(index, "")
                rank = (not bool(date), date, fp.name)
                if key not in ranks or rank < ranks[key]:
                    ranks[key] = rank
                    file_map[key] = fp
    return file_map


def build_dataset(*, return_quality=False):
    cat_dates, by_disc_idx = load_catalog_dates()
    file_map = select_source_files(KAP_RAW_DIR.glob("*.xls"), by_disc_idx)

    records: list[dict[str, Any]] = []
    report_audits = {}
    quarter_methods = {}
    for ticker, comp_info in SELECTED_COMPANIES.items():
        for yr in range(2010, 2021):
            for q in [1, 2, 3, 4]:
                fp = file_map.get((ticker, yr, q))
                period_end = f"{yr}-{QUARTER_END_DATES[q]}"
                row_data: dict[str, Any] = {
                    "ticker": ticker,
                    "company_name": comp_info["title"],
                    "sector_group": comp_info["sector_group"],
                    "C01_kap_main_sector": comp_info["kap_main_sector"],
                    "C01_kap_sub_sector": comp_info["kap_sub_sector"],
                    "year": yr,
                    "quarter": q,
                    "observation_period": f"{yr}Q{q}",
                    "period_end_date": period_end,
                    "first_published_at": "",
                    "disclosure_index": "",
                    "consolidation": "",
                    "original_unit": "",
                    "currency": "TRY",
                    "source_file": "",
                    "source_sha256": "",
                    "unit_multiplier": None,
                    "report_available_at": "",
                    "source_available_at": "",
                    "earliest_known_publication_at": "",
                    "publication_status": "unknown",
                    "qa_flags": "",
                }

                if fp and fp.is_file():
                    head = fp.read_bytes()[:16]
                    if head.startswith(b"\xd0\xcf\x11\xe0"):
                        meta, rows = extract_rows_from_biff8(fp)
                    else:
                        meta, rows = extract_rows_from_html_xls(fp)

                    orig_unit, mult = detect_unit_multiplier(meta.get("original_unit", "TL"))
                    # KAP ham Excel'inde Raporlama Birimi 'TL' yazılıp gerçekte Bin TL veya Milyon TL girilen (veya tersi) raporların düzeltmesi:
                    if (ticker, yr, q) in (("THYAO", 2015, 4), ("THYAO", 2016, 1)):
                        orig_unit, mult = "1.000.000 TL (Ham: TL)", 1_000_000.0
                    elif (ticker, yr, q) in (("TOASO", 2013, 1), ("TOASO", 2014, 3)):
                        orig_unit, mult = "1.000 TL (Ham: TL)", 1_000.0
                    elif (ticker, yr, q) == ("SARKY", 2017, 2):
                        orig_unit, mult = "TL (İlk bildirim 626777 birim düzeltmesi: 626866)", 1.0

                    report_audit = {}
                    fin = parse_financial_rows(rows, mult, report_audit)
                    report_audit["embedded_csv_rows_recovered"] = meta.get("embedded_csv_rows_recovered", 0)
                    row_data["source_file"] = str(fp.relative_to(ROOT_DIR))
                    row_data["source_sha256"] = sha256(fp)
                    row_data["unit_multiplier"] = mult
                    # KAREL 2012Q1 ham BIFF8 dosyasındaki bozuk kayan nokta hücrelerinin (115.28 trilyon -> 11,528,269 TL) düzeltmesi:
                    if (ticker, yr, q) == ("KAREL", 2012, 1):
                        corrections = {
                            "T15_isletme_nakit_akisi_ytd": (115282692945205.0, 11528269.0),
                            "T16_yatirim_nakit_akisi_ytd": (-477891329452055.0, -4778913.0),
                        }
                        for field, (expected_raw, verified_amount) in corrections.items():
                            if fin[field] not in (expected_raw, verified_amount):
                                raise ValueError(f"Unrecognized KAREL correction source: {field}={fin[field]}; revalidate the original report")
                            fin[field] = verified_amount
                        report_audit["correction_evidence"] = {
                            "source_file": "data/kap_raw_xls/KAREL_2013_Q1.xls",
                            "source_cells": {"CFO": "D181", "CFI": "D192"},
                            "evidence_available_at": "2013-05-03 14:07:20",
                            "note": "Later comparative confirms amounts; original first-release PDF is still required for PIT certification.",
                        }
                        report_audit["flags"].append("correction_uses_later_comparative")
                        for field in ("T15_isletme_nakit_akisi_ytd", "T16_yatirim_nakit_akisi_ytd"):
                            report_audit["fields"][field].update({"status": "corrected_from_comparative", "value": fin[field], "evidence_available_at": "2013-05-03 14:07:20"})

                    cat_pub, cat_idx = cat_dates.get((ticker, yr, q), ("", ""))
                    m_fn = re.match(r"^([A-Z0-9]+)_(\d{4})_Q([1-4])(?:_(\d+))?\.xls$", fp.name)
                    fn_idx = m_fn.group(4) if (m_fn and m_fn.group(4)) else ""
                    pub_by_idx = by_disc_idx.get(fn_idx, "") if fn_idx else ""

                    hdr_pub = meta.get("published_at_header", "")
                    selected_dates = [p for p in (pub_by_idx, meta.get("financial_report_published_at", "")) if p]
                    selected_pub = max(selected_dates) if selected_dates else ""
                    row_data.update(publication_metadata(selected_pub, cat_pub, hdr_pub))
                    row_data["source_available_at"] = max(row_data["report_available_at"], report_audit.get("correction_evidence", {}).get("evidence_available_at", ""))
                    if row_data["publication_status"] == "selected_version_later_than_earliest":
                        report_audit["flags"].append("selected_version_later_than_earliest")
                    row_data["qa_flags"] = "|".join(sorted(set(report_audit["flags"])))
                    row_data["disclosure_index"] = fn_idx or cat_idx
                    row_data["consolidation"] = meta.get("consolidation", "")
                    row_data["original_unit"] = orig_unit
                    row_data.update(fin)
                    report_audits[(ticker, yr, q)] = report_audit

                records.append(row_data)

    df = pd.DataFrame(records)
    df.sort_values(["ticker", "year", "quarter"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    df, quarter_methods = derive_quarterly_flows(df)

    df["F07_net_finansman_ytd"] = df["F07_finansman_geliri_ytd"] + df["T05_finansman_gideri_ytd"]
    df["F07_net_finansman_ceyrek"] = df["F07_finansman_geliri_ceyrek"] + df["T05_finansman_gideri_ceyrek"]

    # ---------------- HİSSE BAŞINA KÂR (HBK / EPS) ----------------
    # BIST'te 1 adet (lot) pay = 1 TL nominal ödenmiş sermayedir.
    paid_cap = df["odenmis_sermaye"].replace(0, np.nan)
    df["hisse_basina_kar_ytd"] = (df["T07_ana_ortaklik_net_kari_ytd"] / paid_cap).round(6)
    df["hisse_basina_kar_ceyrek"] = (df["T07_ana_ortaklik_net_kari_ceyrek"] / paid_cap).round(6)

    # ---------------- P0 FİNANSAL ORANLAR VE GECİKMELER (F01-F14) ----------------
    rev_q = df["T01_hasilat_ceyrek"].replace(0, np.nan)
    cogs_q_abs = df["T02_satislarin_maliyeti_ceyrek"].abs().replace(0, np.nan)
    assets = df["T11_toplam_varliklar"].replace(0, np.nan)
    equity = df["T14_toplam_ozkaynaklar"].replace(0, np.nan)

    df["F01_hasilat_qoq_buyume"] = df.groupby("ticker", group_keys=False)["T01_hasilat_ceyrek"].pct_change(1, fill_method=None)
    df["F01_hasilat_yoy_buyume"] = df.groupby("ticker", group_keys=False)["T01_hasilat_ceyrek"].pct_change(4, fill_method=None)
    df["F03_brut_kar_marji"] = df["T03_brut_kar_ceyrek"] / rev_q
    # Overall gross profit can include a finance business while Hasılat is the
    # commercial revenue line. Do not publish an ordinary gross margin for it.
    df.loc[df["qa_flags"].str.contains("mixed_activity_income_statement", na=False), "F03_brut_kar_marji"] = np.nan
    df["F04_esas_faaliyet_marji"] = df["T04_esas_faaliyet_kari_ceyrek"] / rev_q
    df["F05_net_kar_marji"] = df["T07_donem_net_kari_ceyrek"] / rev_q
    df["F06_cfo_aktif_orani"] = df["T15_isletme_nakit_akisi_ceyrek"] / assets
    df["F06_tahakkuk_aktif_orani"] = (df["T07_donem_net_kari_ceyrek"] - df["T15_isletme_nakit_akisi_ceyrek"]) / assets
    df["F09_nakit_aktif_orani"] = df["T08_nakit_ve_nakit_benzerleri"] / assets
    df["F10_alacak_satis_orani"] = df["T09_ticari_alacaklar"] / rev_q
    df["F11_stok_maliyet_orani"] = df["T10_stoklar"] / cogs_q_abs
    df["F12_ticari_borc_maliyet_orani"] = df["F12_ticari_borclar"] / cogs_q_abs
    df["F13_finansal_borc_aktif_orani"] = df["T12_finansal_borclar"] / assets
    df["F13_kisa_finansal_borc_aktif_orani"] = df["F13_kisa_vadeli_finansal_borclar"] / assets
    df["F13_net_borc"] = df["T12_finansal_borclar"] - df["T08_nakit_ve_nakit_benzerleri"]
    df["F14_ozkaynak_aktif_orani"] = df["T14_toplam_ozkaynaklar"] / assets
    df["F14_borc_ozkaynak_orani"] = df["T13_toplam_yukumlulukler"] / equity

    # ---------------- DIŞSAL MAKRO VE KÜRESEL RİSK SERİLERİNİ BİRLEŞTİRME ----------------
    df = merge_external_macro_and_risk(df)

    # ---------------- ETKİLEŞİM DEĞİŞKENLERİ (X02 & X03) ----------------
    df["X02_faiz_degisimi_x_finansal_borc_aktif"] = (
        df["M03_Faiz_3Aylik_Degisim"] * df["F13_finansal_borc_aktif_orani"]
    )
    df["X03_ofr_fsi_x_kisa_borc_aktif"] = (
        df["R03_OFR_FSI_60d_mean"] * df["F13_kisa_finansal_borc_aktif_orani"]
    )

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    missing = missing_details(df, report_audits, quarter_methods)
    quality = {
        "reports": [{"ticker": key[0], "year": key[1], "quarter": key[2], **value,
                     "quarter_methods": quarter_methods.get(key, {})} for key, value in report_audits.items()],
        "missing_values": missing,
    }
    return (df, quality) if return_quality else df


def merge_external_macro_and_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dis serileri acik takvim/gecikme varsayimlariyla esler. Tarihsel yayin/vintage
    arsivleri olmadan gercek point-in-time dogrulugu iddia etmez:
    - Aylik GPR, GPRT, GPRA, GEPU_ppp, TUFE, YI-UFE: ay bittikten sonra yayinlandigi icin
      t0 aninda bilinen son tamamlanmis ve yayinlanmis ay (m - 1) eslenir.
    - Aylik Sanayi Uretimi (M06): ~45 gun gecikmeyle yayinlandigi icin (m - 2) eslenir.
    - OFR FSI: gercek gozlemler uzerinde 60 gozlem ortalamasi ve ABD federal
      tatil takviminde 2 is gunu yayin gecikmesi varsayimi.
    """
    monthly_path = EXTERNAL_DIR / "monthly_macro_and_risk.csv"
    daily_path = EXTERNAL_DIR / "daily_fx_and_fsi.csv"

    if monthly_path.is_file():
        m_df = pd.read_csv(monthly_path).drop_duplicates(subset=["ym"]).sort_values("ym").reset_index(drop=True)
        # m_df['ym'] gözlem ayıdır.
        # 1 ay gecikmeli yayınlanan seriler (GPR, GEPU, TÜFE, Yİ-ÜFE, Faiz): gözlem ayı m olan veri (m+1) sonundaki t0'da bilinir
        m_df["ym_lag1"] = (pd.PeriodIndex(m_df["ym"], freq="M") + 1).strftime("%Y-%m")
        # 2 ay gecikmeli yayınlanan seri (Sanayi Üretimi): gözlem ayı m olan veri (m+2) sonundaki t0'da bilinir
        m_df["ym_lag2"] = (pd.PeriodIndex(m_df["ym"], freq="M") + 2).strftime("%Y-%m")

        df["t0_ym"] = df["period_end_date"].str.slice(0, 7)
        df["macro_observation_month"] = (pd.PeriodIndex(df["t0_ym"], freq="M") - 1).strftime("%Y-%m")
        df["industrial_production_observation_month"] = (pd.PeriodIndex(df["t0_ym"], freq="M") - 2).strftime("%Y-%m")

        lag1_cols = ["M03_Faiz_Orani", "M03_Faiz_3Aylik_Degisim", "M04_TUFE_YoY", "M05_YIUFE_YoY", "GPR", "GPRT", "GPRA", "GEPU_ppp"]
        m_lag1 = m_df[["ym_lag1"] + [c for c in lag1_cols if c in m_df.columns]].rename(columns={"ym_lag1": "t0_ym"})
        df = df.merge(m_lag1, on="t0_ym", how="left")

        if "M06_SanayiUretimi_YoY" in m_df.columns:
            m_lag2 = m_df[["ym_lag2", "M06_SanayiUretimi_YoY"]].rename(columns={"ym_lag2": "t0_ym"})
            df = df.merge(m_lag2, on="t0_ym", how="left")

        df.rename(
            columns={
                "GPR": "R01_GPR",
                "GPRT": "R04_GPRT",
                "GPRA": "R04_GPRA",
                "GEPU_ppp": "R02_GEPU_ppp",
            },
            inplace=True,
        )
        df.drop(columns=["t0_ym"], inplace=True)

    if daily_path.is_file():
        d_df = pd.read_csv(daily_path)
        d_df["date"] = pd.to_datetime(d_df["date"])
        d_df.sort_values("date", inplace=True)
        d_df["M01_USDTRY_seviye"] = d_df["USDTRY"]
        d_df["M02_EURTRY_seviye"] = d_df["EURTRY"]
        for raw_col, target_col in (("USDTRY", "M01_USDTRY_90g_degisim_pct"), ("EURTRY", "M02_EURTRY_90g_degisim_pct")):
            changes = calendar_fx_change(d_df, raw_col).rename(columns={"change": target_col})
            d_df = d_df.merge(changes, on="date", how="left")
        df["t0_dt"] = pd.to_datetime(df["period_end_date"])
        fx_cols = ["date", "M01_USDTRY_seviye", "M01_USDTRY_90g_degisim_pct", "M02_EURTRY_seviye", "M02_EURTRY_90g_degisim_pct"]
        merged = pd.merge_asof(df.sort_values("t0_dt"), d_df[fx_cols].sort_values("date"), left_on="t0_dt", right_on="date", direction="backward")
        ofr = ofr_available_series(d_df)
        merged = pd.merge_asof(merged.sort_values("t0_dt"), ofr, left_on="t0_dt", right_on="ofr_assumed_available_at", direction="backward")
        for col in ("ofr_observation_date", "ofr_assumed_available_at"):
            merged[col] = merged[col].dt.strftime("%Y-%m-%d")
        merged.drop(columns=["t0_dt", "date"], inplace=True)
        df = merged.sort_values(["ticker", "year", "quarter"]).reset_index(drop=True)
    df["macro_availability_policy"] = "assumed_month_lags_latest_vintage;ofr_us_federal_calendar_estimate"

    return df


def save_dataset(dataset, output_dir=None, *, quality):
    """Write one canonical CSV and diagnostics; publish the manifest last.

    os.replace failures preserve the existing canonical CSV and fail the build.
    Consumers must verify all hashes recorded in the completed manifest.
    """
    from collections import Counter

    paths = [OUTPUT_CSV] if output_dir is None else [Path(output_dir) / OUTPUT_CSV.name]
    quality_dir = (ROOT_DIR / "data" if output_dir is None else Path(output_dir)) / "quality"
    text = "\ufeff" + dataset.to_csv(index=False)
    for path in paths:
        atomic_text(path, text)
    save_jsonl_gzip(quality_dir / "financial_sources.jsonl.gz", quality["reports"])
    save_jsonl_gzip(quality_dir / "missing_values.jsonl.gz", quality["missing_values"])
    summary = {
        "rows": len(dataset), "columns": len(dataset.columns),
        "missing_by_column": {c: int(dataset[c].isna().sum() + dataset[c].eq("").sum()) for c in dataset.columns if c != "qa_flags"},
        "missing_reason_counts": dict(Counter(r["reason"] for r in quality["missing_values"])),
        "flagged_reports": [{"ticker": r["ticker"], "year": r["year"], "quarter": r["quarter"], "flags": r["flags"]} for r in quality["reports"] if r["flags"]],
        "fully_point_in_time_verified": False,
        "known_limitations": [
            "Monthly macro publication dates and historical vintages are not reconstructed.",
            "OFR availability uses a declared US federal calendar estimate, not historical release timestamps.",
            "Mixed financial/commercial income statement scopes need separate validation.",
            "Later comparative KAREL correction requires original first-release evidence for PIT use.",
            "M03 is the OECD overnight interbank proxy, not a commercial loan rate.",
        ],
    }
    save_json(quality_dir / "summary.json", summary)
    manifest = {
        "schema_version": 2,
        "timestamp_timezone": "Europe/Istanbul for KAP timestamps; daily market series retain source date conventions",
        "csv_files": [{"path": str(path.relative_to(ROOT_DIR)) if path.is_relative_to(ROOT_DIR) else str(path), "sha256": sha256(path)} for path in paths],
        "parser_sha256": sha256(Path(__file__)),
        "quality_code_sha256": sha256(Path(__file__).with_name("financial_quality.py")),
        "catalog_sha256": sha256(ROOT_DIR / "data/kap_fr_catalog_2010_2020.json"),
        "external_sha256": {name: sha256(EXTERNAL_DIR / name) for name in ("monthly_macro_and_risk.csv", "daily_fx_and_fsi.csv")},
        "diagnostics_sha256": {name: sha256(quality_dir / name) for name in ("financial_sources.jsonl.gz", "missing_values.jsonl.gz", "summary.json")},
    }
    save_json(quality_dir / "manifest.json", manifest)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build financial observations and source/missingness diagnostics; does not train a model.")
    parser.add_argument("--output-dir", type=Path, help="Build into a separate directory instead of replacing the canonical copies.")
    args = parser.parse_args()
    print("Veri seti ve kaynak/eksiklik denetimi olusturuluyor...", flush=True)
    dataset, quality = build_dataset(return_quality=True)
    summary = save_dataset(dataset, args.output_dir, quality=quality)
    print(f"Uretildi: {summary['rows']} satir, {summary['columns']} sutun. Eksiklik nedenleri: {summary['missing_reason_counts']}")
    print("Bu cikti otomatik olarak PIT-dogrulanmis veya egitime hazir sayilmaz; quality/summary.json dosyasini inceleyin.")
