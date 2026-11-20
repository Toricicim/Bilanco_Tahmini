"""Non-destructive forensic audit of missing KAP values with clickable disclosure links.

Inspects all `source_value_unavailable` and `unresolved_source_or_mapping` entries in
`data/quality/missing_values.jsonl.gz` directly against the underlying raw KAP `.xls`
files (both 2010-2015 BIFF8 and 2016-2020 HTML) using only the Python standard library.

Writes `data/quality/missing_audit_with_links.csv` and prints a summary table to
distinguish genuine blanks in KAP from likely parser misses. Does not modify any
canonical dataset, training matrix, parser script, or quality manifest.
"""

from __future__ import annotations

import collections
import csv
import gzip
import html
import json
import math
import re
import struct
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
CANONICAL_CSV = ROOT_DIR / "data" / "bist_bilanco_tahmini_2010_2020.csv"
CATALOG_JSON = ROOT_DIR / "data" / "kap_fr_catalog_2010_2020.json"
MISSING_JSONL_GZ = ROOT_DIR / "data" / "quality" / "missing_values.jsonl.gz"
OUT_AUDIT_CSV = ROOT_DIR / "data" / "quality" / "missing_audit_with_links.csv"

TARGET_REASONS = ("source_value_unavailable", "unresolved_source_or_mapping")

RE_UNIT = re.compile(r"Sunum Para Birimi\s*</td>\s*<td[^>]*>\s*([^<]+)", re.I | re.S)
RE_LABEL_TR = re.compile(r'content-tr"[^>]*>\s*([^<]+)', re.I | re.S)
RE_TYPED_CAPTION = re.compile(r'typed-dimension-field-caption"[^>]*>\s*([^<]+)', re.I | re.S)
RE_BASIC_EPS_ROLE = re.compile(r"general_role_310\d+-row-66\b")
RE_CTX_CELL = re.compile(r'<td\s+class="taxonomy-context-value[^"]*"[^>]*>(.*?)</td>', re.I | re.S)
RE_TITLE_VAL = re.compile(r'title="([^"]+)"', re.I | re.S)
RE_INNER_TEXT = re.compile(r"<[^>]+>")


def normalize_tr(text: Any) -> str:
    """Normalize Turkish labels to lowercase ASCII with collapsed whitespace."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    s = str(text).strip()
    s = s.replace("İ", "i").replace("I", "ı").lower()
    s = s.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))
    return re.sub(r"\s+", " ", s).strip()


def parse_number(val: Any) -> float | None:
    """Parse KAP numeric cell text to float, returning None for empty cells."""
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
    if not s or s in ("-", "."):
        return None
    try:
        res = float(s)
        return -abs(res) if neg else res
    except ValueError:
        return None


def _read_ole_workbook_stream(path: Path) -> bytes:
    """Extract the Workbook/Book stream from a BIFF8 OLE2 compound document."""
    data = path.read_bytes()
    sec_sz = 1 << struct.unpack_from("<H", data, 30)[0]
    mini_sz = 1 << struct.unpack_from("<H", data, 32)[0]
    dir_start = struct.unpack_from("<i", data, 48)[0]
    mini_cutoff = struct.unpack_from("<I", data, 56)[0]
    minifat_start = struct.unpack_from("<i", data, 60)[0]
    difat_start = struct.unpack_from("<i", data, 68)[0]
    num_difat = struct.unpack_from("<I", data, 72)[0]

    fat_sectors = [s for s in struct.unpack_from("<109i", data, 76) if s >= 0]
    difat_cur = difat_start
    seen_difat: set[int] = set()
    per_sec = sec_sz // 4
    while difat_cur >= 0 and difat_cur not in seen_difat and len(seen_difat) <= num_difat + 1:
        seen_difat.add(difat_cur)
        off = (difat_cur + 1) * sec_sz
        entries = struct.unpack_from(f"<{per_sec}i", data, off)
        fat_sectors.extend(s for s in entries[:-1] if s >= 0)
        difat_cur = entries[-1]

    fat: list[int] = []
    for s in fat_sectors:
        off = (s + 1) * sec_sz
        fat.extend(struct.unpack_from(f"<{per_sec}i", data, off))

    def read_chain(start: int) -> bytes:
        out = bytearray()
        s = start
        seen: set[int] = set()
        while s >= 0 and s not in seen:
            seen.add(s)
            off = (s + 1) * sec_sz
            out.extend(data[off : off + sec_sz])
            s = fat[s] if s < len(fat) else -2
        return bytes(out)

    dir_bytes = read_chain(dir_start)
    root_start = -2
    root_size = 0
    wb_entry: tuple[int, int] | None = None

    for i in range(0, len(dir_bytes), 128):
        entry = dir_bytes[i : i + 128]
        if len(entry) < 128:
            break
        nlen = struct.unpack_from("<H", entry, 64)[0]
        if nlen < 2 or nlen > 64:
            continue
        name = entry[: nlen - 2].decode("utf-16le", errors="ignore").lower()
        etype = entry[66]
        start = struct.unpack_from("<i", entry, 116)[0]
        size = struct.unpack_from("<I", entry, 120)[0]
        if etype == 5 or i == 0:
            root_start, root_size = start, size
        if name in ("workbook", "book"):
            wb_entry = (start, size)
            break

    if wb_entry is None:
        raise RuntimeError(f"Missing Workbook stream in {path}")
    wb_start, wb_size = wb_entry
    if wb_size < mini_cutoff and minifat_start >= 0 and root_start >= 0:
        ministream = read_chain(root_start)[:root_size]
        minifat_bytes = read_chain(minifat_start)
        minifat = list(struct.unpack_from(f"<{len(minifat_bytes) // 4}i", minifat_bytes, 0))
        out = bytearray()
        s = wb_start
        seen: set[int] = set()
        while s >= 0 and s not in seen:
            seen.add(s)
            off = s * mini_sz
            out.extend(ministream[off : off + mini_sz])
            s = minifat[s] if s < len(minifat) else -2
        return bytes(out)[:wb_size]
    return read_chain(wb_start)[:wb_size]


def _decode_rk(rk: int) -> float:
    """Decode a BIFF8 RK numeric value with signed 30-bit integer handling."""
    if rk & 2:
        raw = rk >> 2
        if raw & 0x20000000:
            raw -= 0x40000000
        val = float(raw)
    else:
        val = struct.unpack("<d", struct.pack("<II", 0, rk & 0xFFFFFFFC))[0]
    return val / 100.0 if (rk & 1) else val


def _decode_xl_unicode(payload: bytes, offset: int = 0) -> str:
    """Decode a single-chunk XLUnicodeString (2-byte length + 1-byte flags)."""
    if offset + 3 > len(payload):
        return ""
    cch = struct.unpack_from("<H", payload, offset)[0]
    flags = payload[offset + 2]
    pos = offset + 3
    if flags & 8:
        pos += 2
    if flags & 4:
        pos += 4
    high = flags & 1
    byte_len = cch * (2 if high else 1)
    raw = payload[pos : pos + byte_len]
    return raw.decode("utf-16le" if high else "latin1", errors="ignore")


def _parse_sst(chunks: list[bytes]) -> list[str]:
    """Decode BIFF8 Shared String Table across CONTINUE record boundaries."""
    ci, off = 0, 8
    _, uniq = struct.unpack_from("<II", chunks[0], 0)

    def read_bytes(n: int) -> bytes:
        nonlocal ci, off
        out = bytearray()
        while len(out) < n and ci < len(chunks):
            if off >= len(chunks[ci]):
                ci += 1
                off = 0
                continue
            take = min(n - len(out), len(chunks[ci]) - off)
            out.extend(chunks[ci][off : off + take])
            off += take
        return bytes(out)

    sst: list[str] = []
    for _ in range(uniq):
        hdr = read_bytes(3)
        if len(hdr) < 3:
            break
        cch = struct.unpack("<H", hdr[:2])[0]
        flags = hdr[2]
        high = flags & 1
        rt_runs = struct.unpack("<H", read_bytes(2))[0] if (flags & 8) else 0
        ext_len = struct.unpack("<I", read_bytes(4))[0] if (flags & 4) else 0
        parts: list[str] = []
        rem = cch
        while rem > 0 and ci < len(chunks):
            if off >= len(chunks[ci]):
                ci += 1
                if ci >= len(chunks):
                    break
                high = chunks[ci][0] & 1
                off = 1
            step = 2 if high else 1
            avail = (len(chunks[ci]) - off) // step
            if avail <= 0:
                ci += 1
                if ci >= len(chunks):
                    break
                high = chunks[ci][0] & 1
                off = 1
                continue
            take = min(rem, avail)
            raw = chunks[ci][off : off + take * step]
            off += take * step
            parts.append(raw.decode("utf-16le" if high else "latin1", errors="ignore"))
            rem -= take
        if rt_runs:
            read_bytes(rt_runs * 4)
        if ext_len:
            read_bytes(ext_len)
        sst.append("".join(parts))
    return sst


def _update_section(
    ln: str,
    statement: str,
    bs_section: str,
    saw_net_kar: bool,
) -> tuple[str, str, str, str, bool]:
    """Determine (row_section, next_statement, next_bs_section, next_saw_net_kar) for a label."""
    if ln in (
        "bilanco",
        "finansal durum tablosu",
        "finansal durum tablosu (bilanco)",
        "varliklar",
        "aktifler",
        "aktif kalemler",
    ):
        return ("BS_DONEN", "BS", "DONEN", saw_net_kar)
    if ln == "nazim hesaplar":
        return ("OFF_BS", "OFF_BS", bs_section, saw_net_kar)
    if ln in (
        "diger kapsamli gelir tablosu",
        "diger kapsamli gelir",
        "diger kapsamli gelirler",
        "diger kapsamli gelir unsurlari",
        "diger kapsamli giderler",
    ) or (ln == "kapsamli gelir tablosu" and saw_net_kar):
        return ("OCI", "OCI", bs_section, saw_net_kar)
    if ln in (
        "gelir tablosu",
        "kapsamli gelir tablosu",
        "kar veya zarar ve diger kapsamli gelir tablosu",
        "kar veya zarar tablosu",
        "kar veya zarar kismi",
        "surdurulen faaliyetler",
    ):
        return ("IS", "IS", bs_section, saw_net_kar)
    if (
        ln
        in (
            "nakit akim tablosu",
            "nakit akis tablosu",
            "nakit akis tablosu dolayli yontem",
            "nakit akis tablosu (dolayli yontem)",
            "nakit akis tablosu dogrudan yontem",
            "nakit akis tablosu (dogrudan yontem)",
            "nakit akis tablolari",
        )
        or "isletme faaliyetlerine iliskin nakit akimlari" in ln
        or "a. isletme faaliyetlerinden nakit akislari" in ln
        or "a - esas faaliyetlere iliskin nakit akislari" in ln
        or "faaliyetlerden kaynaklanan nakit akimlari" in ln
    ):
        return ("CF", "CF", bs_section, saw_net_kar)
    if (
        "ozsermaye degisim tablosu" in ln
        or "ozkaynak degisim tablosu" in ln
        or "ozkaynaklar degisim tablosu" in ln
        or "finansal tablo dipnot" in ln
    ):
        return ("EQ", "EQ", bs_section, saw_net_kar)

    if statement == "BS":
        if ln in ("donen varliklar", "a. donen varliklar"):
            return ("BS_DONEN", "BS", "DONEN", saw_net_kar)
        if ln == "toplam donen varliklar":
            return ("BS_DONEN", "BS", "DURAN", saw_net_kar)
        if ln in ("duran varliklar", "b. duran varliklar"):
            return ("BS_DURAN", "BS", "DURAN", saw_net_kar)
        if ln in ("toplam varliklar", "toplam aktifler", "aktif toplami"):
            return (f"BS_{bs_section}", "BS", "KISA_YUK", saw_net_kar)
        if ln in ("kisa vadeli yukumlulukler", "pasif kalemler", "kisa vadeli borclar"):
            return ("BS_KISA_YUK", "BS", "KISA_YUK", saw_net_kar)
        if ln == "toplam kisa vadeli yukumlulukler":
            return ("BS_KISA_YUK", "BS", "UZUN_YUK", saw_net_kar)
        if ln in ("uzun vadeli yukumlulukler", "uzun vadeli borclar"):
            return ("BS_UZUN_YUK", "BS", "UZUN_YUK", saw_net_kar)
        if ln == "toplam yukumlulukler":
            return (f"BS_{bs_section}", "BS", "OZKAYNAK", saw_net_kar)
        if ln in ("o z k a y n a k l a r", "ozkaynaklar", "toplam ozkaynaklar"):
            return ("BS_OZKAYNAK", "BS", "OZKAYNAK", saw_net_kar)
        return (f"BS_{bs_section}", "BS", bs_section, saw_net_kar)

    if statement == "IS" and ln in (
        "donem kari/zarari",
        "donem kari (zarari)",
        "net donem kari/zarari",
        "net donem kari (zarari)",
        "donem net kari veya zarari",
    ):
        saw_net_kar = True
    return (statement, statement, bs_section, saw_net_kar)


def extract_biff8_rows(path: Path) -> list[tuple[str, bool, str, str, float | None]]:
    """Parse first worksheet of a 2010-2015 BIFF8 .xls file with section tagging."""
    wb = _read_ole_workbook_stream(path)
    pos = 0
    recs: list[list[Any]] = []
    while pos + 4 <= len(wb):
        rt, rl = struct.unpack_from("<HH", wb, pos)
        payload = wb[pos + 4 : pos + 4 + rl]
        pos += 4 + rl
        if rt == 0x003C and recs:
            recs[-1][1].append(payload)
        else:
            recs.append([rt, [payload]])

    sst: list[str] = []
    for rt, chunks in recs:
        if rt == 0x00FC:
            sst = _parse_sst(chunks)
            break

    grid: dict[int, dict[int, Any]] = {}
    in_sheet = False
    bof_depth = 0
    pending_formula_rc: tuple[int, int] | None = None

    for rt, chunks in recs:
        p = b"".join(chunks)
        if rt == 0x0809:
            btype = struct.unpack_from("<H", p, 2)[0]
            if not in_sheet:
                if btype == 0x0010:
                    in_sheet = True
                    bof_depth = 1
                continue
            bof_depth += 1
            continue
        if not in_sheet:
            continue
        if rt == 0x000A:  # EOF
            bof_depth -= 1
            if bof_depth <= 0:
                break
            continue

        if rt == 0x00FD and len(p) >= 10:  # LABELSST
            r, c, _, idx = struct.unpack_from("<HHHI", p, 0)
            grid.setdefault(r, {})[c] = sst[idx] if idx < len(sst) else ""
        elif rt in (0x0204, 0x00D6) and len(p) >= 9:  # LABEL / RSTRING
            r, c, _ = struct.unpack_from("<HHH", p, 0)
            grid.setdefault(r, {})[c] = _decode_xl_unicode(p, 6)
        elif rt == 0x0203 and len(p) >= 14:  # NUMBER
            r, c, _, val = struct.unpack_from("<HHHd", p, 0)
            grid.setdefault(r, {})[c] = val
        elif rt == 0x027E and len(p) >= 10:  # RK
            r, c, _, rk = struct.unpack_from("<HHHI", p, 0)
            grid.setdefault(r, {})[c] = _decode_rk(rk)
        elif rt == 0x00BD and len(p) >= 10:  # MULRK
            r, c1 = struct.unpack_from("<HH", p, 0)
            c2 = struct.unpack_from("<H", p, len(p) - 2)[0]
            for i in range(c2 - c1 + 1):
                rk = struct.unpack_from("<I", p, 4 + i * 6 + 2)[0]
                grid.setdefault(r, {})[c1 + i] = _decode_rk(rk)
        elif rt == 0x0006 and len(p) >= 14:  # FORMULA
            r, c = struct.unpack_from("<HH", p, 0)
            if p[12:14] != b"\xff\xff":
                grid.setdefault(r, {})[c] = struct.unpack_from("<d", p, 6)[0]
                pending_formula_rc = None
            elif p[6] == 0:
                pending_formula_rc = (r, c)
            else:
                pending_formula_rc = None
        elif rt == 0x0207 and pending_formula_rc is not None:  # STRING after FORMULA
            pr, pc = pending_formula_rc
            grid.setdefault(pr, {})[pc] = _decode_xl_unicode(p, 0)
            pending_formula_rc = None
        else:
            pending_formula_rc = None

    parsed_rows: list[tuple[str, bool, str, str, float | None]] = []
    col_ytd = 2
    statement = "BS"
    bs_section = "DONEN"
    saw_net_kar = False

    for r_idx in sorted(grid):
        row_dict = grid[r_idx]
        max_col = max(row_dict.keys())
        r_vals = [row_dict.get(j) for j in range(max_col + 1)]
        c0 = str(r_vals[0]).strip() if r_vals and r_vals[0] is not None else ""

        if c0.startswith('"') and '","' in c0:
            try:
                decoded = next(csv.reader([c0], skipinitialspace=True))
            except csv.Error:
                decoded = []
            if len(decoded) >= 3:
                r_vals = decoded
                c0 = str(r_vals[0]).strip()

        row_norms = [
            normalize_tr(r_vals[j]) if j < len(r_vals) and r_vals[j] not in (None, "") else ""
            for j in range(min(8, len(r_vals)))
        ]
        if any(rn == "cari donem" or rn.startswith("cari donem ") for rn in row_norms[1:]):
            for j in range(1, len(row_norms)):
                if row_norms[j] == "cari donem":
                    col_ytd = j
                    break
            continue

        if not c0:
            continue
        ln = normalize_tr(c0)
        if not ln:
            continue
        if ("[]" in c0 or "[" in c0) and re.search(r"\]\s*\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}", c0):
            continue
        if ln in ("finansal tablo turu", "raporlama birimi"):
            continue

        c_ytd_raw = r_vals[col_ytd] if col_ytd < len(r_vals) else None
        val_ytd = parse_number(c_ytd_raw)
        if val_ytd is None and col_ytd == 2 and len(r_vals) > 4:
            alt_ytd = parse_number(r_vals[4])
            v2 = parse_number(r_vals[2]) if len(r_vals) > 2 else None
            v3 = parse_number(r_vals[3]) if len(r_vals) > 3 else None
            if alt_ytd is not None and v2 is None and v3 is None:
                val_ytd = alt_ytd

        row_sec, statement, bs_section, saw_net_kar = _update_section(ln, statement, bs_section, saw_net_kar)
        parsed_rows.append((row_sec, True, c0, ln, val_ytd))

    return parsed_rows


def extract_html_rows(path: Path) -> list[tuple[str, bool, str, str, float | None]]:
    """Parse all rows (enabled, disabled, abstract, new-type-row) of a 2016-2020 HTML .xls file."""
    html_text = path.read_bytes().decode("utf-8", errors="ignore")
    chunks = html_text.split('<tr class="')
    parsed_rows: list[tuple[str, bool, str, str, float | None]] = []

    statement = "BS"
    bs_section = "DONEN"
    saw_net_kar = False
    last_role = ""
    last_typed_enabled = False

    for ch in chunks[1:]:
        head_part = ch[:140]
        m_role = re.search(r"general_role_(\d{3})", head_part)
        if m_role:
            role_prefix = m_role.group(1)
            if role_prefix != last_role:
                last_role = role_prefix
                if role_prefix.startswith("21"):
                    statement, bs_section = "BS", "DONEN"
                elif role_prefix.startswith(("31", "32")):
                    statement = "IS"
                elif role_prefix.startswith(("41", "42")):
                    statement = "OCI"
                elif role_prefix.startswith(("51", "52")):
                    statement = "CF"
                elif role_prefix.startswith("61"):
                    statement = "EQ"

        if "typed-dimension-row" in head_part:
            last_typed_enabled = ("presentation-enabled" in head_part) and bool(RE_BASIC_EPS_ROLE.search(head_part))
            continue

        if head_part.startswith("new-type-row"):
            enabled = last_typed_enabled
        else:
            last_typed_enabled = False
            enabled = ("presentation-disabled" not in head_part) and ("abstract-row" not in head_part)

        m_lbl = RE_TYPED_CAPTION.search(ch) if head_part.startswith("new-type-row") else (RE_LABEL_TR.search(ch) or RE_TYPED_CAPTION.search(ch))
        if not m_lbl:
            continue
        label = html.unescape(m_lbl.group(1)).strip()
        ln = normalize_tr(label)
        if not ln:
            continue

        ctx_cells = RE_CTX_CELL.findall(ch)
        val_ytd: float | None = None
        if ctx_cells:
            cell_html = ctx_cells[0]
            m_t = RE_TITLE_VAL.search(cell_html)
            if m_t:
                val_ytd = parse_number(m_t.group(1))
            else:
                txt_val = html.unescape(RE_INNER_TEXT.sub(" ", cell_html)).strip()
                val_ytd = parse_number(txt_val)

        row_sec, statement, bs_section, saw_net_kar = _update_section(ln, statement, bs_section, saw_net_kar)
        parsed_rows.append((row_sec, enabled, label, ln, val_ytd))

    return parsed_rows


def load_xls_rows(path: Path) -> list[tuple[str, bool, str, str, float | None]]:
    """Dispatch between BIFF8 OLE2 and HTML KAP .xls formats."""
    if path.read_bytes()[:4] == b"\xd0\xcf\x11\xe0":
        return extract_biff8_rows(path)
    return extract_html_rows(path)


def _match_candidate(column: str, sec: str, ln: str) -> bool:
    """Section-scoped candidate matcher for missing KAP columns."""
    if column == "F10_kisa_vadeli_ticari_alacaklar":
        return sec == "BS_DONEN" and "ticari alacak" in ln and not any(x in ln for x in ("karsilik", "deger dusuklugu", "supheli"))
    if column == "F10_uzun_vadeli_ticari_alacaklar":
        return sec == "BS_DURAN" and "ticari alacak" in ln and not any(x in ln for x in ("karsilik", "deger dusuklugu", "supheli"))
    if column == "kisa_vadeli_ticari_borclar":
        return sec == "BS_KISA_YUK" and "ticari borc" in ln and not any(x in ln for x in ("karsilik", "deger dusuklugu"))
    if column == "uzun_vadeli_ticari_borclar":
        return sec == "BS_UZUN_YUK" and "ticari borc" in ln and not any(x in ln for x in ("karsilik", "deger dusuklugu"))
    if column == "F13_kisa_vadeli_finansal_borclar":
        return sec == "BS_KISA_YUK" and any(
            k in ln for k in ("finansal borc", "borclanma", "alinan kredi", "banka kredi", "kiralama", "tahvil", "bono", "ihrac edilmis")
        )
    if column == "F13_uzun_vadeli_finansal_borclar":
        return sec == "BS_UZUN_YUK" and any(
            k in ln for k in ("finansal borc", "borclanma", "alinan kredi", "banka kredi", "kiralama", "tahvil", "bono", "ihrac edilmis")
        )
    if column == "F18_kisa_vadeli_ertelenmis_gelir_ve_avanslar":
        return sec == "BS_KISA_YUK" and any(
            k in ln for k in ("ertelenmis gelir", "alinan avans", "siparis avans", "musteri sozlesme", "gelecek aylara ait gelir")
        )
    if column == "F18_uzun_vadeli_ertelenmis_gelir_ve_avanslar":
        return sec == "BS_UZUN_YUK" and any(
            k in ln for k in ("ertelenmis gelir", "alinan avans", "siparis avans", "musteri sozlesme", "gelecek yillara ait gelir")
        )
    if column == "T10_stoklar":
        return sec == "BS_DONEN" and ("stok" in ln)
    if column == "F15_maddi_olmayan_duran_varliklar":
        return sec == "BS_DURAN" and "maddi olmayan duran varlik" in ln
    if column == "donen_varliklar":
        return sec in ("BS_DONEN", "BS_DURAN") and ln in (
            "donen varliklar",
            "toplam donen varliklar",
            "a. donen varliklar",
            "donen varliklar toplami",
        )
    if column == "duran_varliklar":
        return sec in ("BS_DONEN", "BS_DURAN") and ln in (
            "duran varliklar",
            "toplam duran varliklar",
            "b. duran varliklar",
            "duran varliklar toplami",
        )
    if column == "kisa_vadeli_yukumlulukler":
        return sec in ("BS_KISA_YUK", "BS_UZUN_YUK") and ln in (
            "kisa vadeli yukumlulukler",
            "toplam kisa vadeli yukumlulukler",
            "kisa vadeli borclar",
            "toplam kisa vadeli borclar",
        )
    if column == "uzun_vadeli_yukumlulukler":
        return sec in ("BS_KISA_YUK", "BS_UZUN_YUK") and ln in (
            "uzun vadeli yukumlulukler",
            "toplam uzun vadeli yukumlulukler",
            "uzun vadeli borclar",
            "toplam uzun vadeli borclar",
        )
    if column == "odenmis_sermaye":
        return sec == "BS_OZKAYNAK" and (
            any(k in ln for k in ("odenmis sermaye", "cikarilmis sermaye")) or ln == "sermaye"
        )
    if column == "F16_pazarlama_giderleri_ytd":
        return sec == "IS" and any(k in ln for k in ("pazarlama", "satis ve dagitim"))
    if column == "F16_genel_yonetim_giderleri_ytd":
        return sec == "IS" and "genel yonetim" in ln
    if column == "F16_ar_ge_giderleri_ytd":
        return sec == "IS" and any(k in ln for k in ("arastirma", "ar-ge"))
    if column == "T05_finansman_gideri_ytd":
        return (
            sec == "IS"
            and any(k in ln for k in ("finansman gider", "finansal gider"))
            and not any(x in ln for x in ("oncesi", "gelir", "net"))
        )
    if column == "F07_finansman_geliri_ytd":
        return (
            sec == "IS"
            and any(k in ln for k in ("finansman gelir", "finansal gelir"))
            and not any(x in ln for x in ("oncesi", "gider", "net"))
        )
    if column == "T06_vergi_gideri_geliri_ytd":
        return sec == "IS" and "vergi" in ln and not any(k in ln for k in ("vergi oncesi", "vergi sonrasi", "durdurulan"))
    if column == "T07_ana_ortaklik_net_kari_ytd":
        return sec == "IS" and "ana ortaklik" in ln
    if column == "kap_raporlanan_hbk_ytd":
        return (
            sec == "IS"
            and any(k in ln for k in ("pay basina", "hisse basina"))
            and any(k in ln for k in ("kazanc", "kar", "zarar", "kayip"))
            and not any(x in ln for x in ("sulandirilmis", "durdurulan", "pay bazli"))
            and ("seyreltilmis" not in ln or "adi ve seyreltilmis" in ln)
        )
    if column == "T02_satislarin_maliyeti_ytd":
        return sec == "IS" and any(
            k in ln for k in ("satislarin maliyeti", "satis maliyeti", "hizmet maliyeti", "faaliyetleri maliyeti")
        )
    if column == "T04_esas_faaliyet_kari_ytd":
        return sec == "IS" and any(k in ln for k in ("esas faaliyet kar", "faaliyet kar", "net faaliyet k")) and "oncesi" not in ln
    if column == "F15_capex_ytd":
        return (
            sec == "CF"
            and ("maddi" in ln or "sabit kiymet" in ln)
            and any(k in ln for k in ("alim", "satin al", "edinim", "yatirim harcama"))
            and not any(
                x in ln for x in ("satis", "satim", "elden cikar", "amortisman", "itfa", "deger dusuklugu", "avans", "net", "tahsil", "satilan")
            )
        )
    if column == "F15_amortisman_ve_itfa_ytd":
        return (
            sec == "CF"
            and any(k in ln for k in ("amortisman", "amortisan", "itfa", "tukenme"))
            and not any(
                x in ln
                for x in (
                    "imtiyaz kira",
                    "kira gideri",
                    "pesin oden",
                    "kredi",
                    "tahvil",
                    "bono",
                    "borclanma",
                    "finansman",
                    "iskonto",
                    "prim",
                    "durdurulan",
                    "ertelenmis",
                    "satis",
                    "elden cikar",
                    "deger dusuklugu",
                    "stok",
                    "alacak",
                    "karsilik",
                    "vergi",
                    "kur farki",
                )
            )
        )
    if column == "T15_isletme_nakit_akisi_ytd":
        return sec == "CF" and any(k in ln for k in ("isletme faaliyet", "esas faaliyet", "faaliyetlerden")) and "nakit" in ln
    if column == "T16_yatirim_nakit_akisi_ytd":
        return sec == "CF" and "yatirim faaliyet" in ln and "nakit" in ln
    if column == "T17_finansman_nakit_akisi_ytd":
        return sec == "CF" and any(k in ln for k in ("finansman faaliyet", "finansal faaliyet")) and "nakit" in ln
    return False


def _fmt_val(v: float) -> str:
    if float(v).is_integer():
        return str(int(v))
    return f"{v:.6f}".rstrip("0").rstrip(".")


def _statement_for_summary(summary: str) -> str:
    norm = normalize_tr(summary)
    if not norm or norm == "finansal rapor":
        return "UNIFIED"
    if "bilanco" in norm or "finansal durum" in norm:
        return "BS"
    if "gelir tablosu" in norm or "kar veya zarar" in norm:
        return "IS"
    if "nakit akim" in norm or "nakit akis" in norm:
        return "CF"
    return ""


def _column_statement(column: str) -> str:
    if column in (
        "T15_isletme_nakit_akisi_ytd",
        "T16_yatirim_nakit_akisi_ytd",
        "T17_finansman_nakit_akisi_ytd",
        "F15_amortisman_ve_itfa_ytd",
        "F15_capex_ytd",
    ):
        return "CF"
    if column.startswith(("T01_", "T02_", "T03_", "T04_", "T05_", "T06_", "T07_", "F07_", "F16_")) or column in (
        "vergi_oncesi_kar_zarar_ytd",
        "kap_raporlanan_hbk_ytd",
    ):
        return "IS"
    return "BS"


def load_statement_disclosure_map(
    tickers: set[str],
) -> tuple[dict[tuple[str, int, int, str], dict[str, str]], dict[tuple[str, int, int], dict[str, str]]]:
    """Map (ticker, year, quarter[, pub_day]) -> statement ('BS'/'IS'/'CF'/'UNIFIED') disclosureIndex."""
    if not CATALOG_JSON.is_file():
        return {}, {}
    data = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    alias_map = {"KRDMA": "KRDMD", "KRDMB": "KRDMD", "KRDMD": "KRDMD"}
    donem_map = {
        "3 Aylık": 1, "03 Aylık": 1, "1. Çeyrek": 1,
        "6 Aylık": 2, "06 Aylık": 2, "2. Çeyrek": 2,
        "9 Aylık": 3, "09 Aylık": 3, "3. Çeyrek": 3,
        "Yıllık": 4, "12 Aylık": 4, "4. Çeyrek": 4,
    }
    by_day: dict[tuple[str, int, int, str], dict[str, str]] = collections.defaultdict(dict)
    earliest_stmt: dict[tuple[str, int, int], dict[str, tuple[str, str]]] = collections.defaultdict(dict)

    for d in data.get("disclosures", []):
        basic = d.get("disclosureBasic", d)
        subj = (basic.get("subject") or "").strip()
        if "Faaliyet Raporu" in subj or "Sorumluluk Beyan" in subj:
            continue
        stmt = _statement_for_summary(basic.get("summary") or "")
        if not stmt:
            continue
        disc_idx = str(basic.get("disclosureIndex") or "")
        if not disc_idx:
            continue
        pub_raw = (basic.get("publishDate") or "").strip()
        pub_iso = pub_raw
        m_dt = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)$", pub_raw)
        if m_dt:
            t_part = m_dt.group(4) if len(m_dt.group(4)) == 8 else f"{m_dt.group(4)}:00"
            pub_iso = f"{m_dt.group(3)}-{m_dt.group(2)}-{m_dt.group(1)} {t_part}"
        pub_day = pub_iso[:10] if pub_iso else ""

        codes = [c.strip() for c in re.split(r"[, \-]+", basic.get("stockCodes") or basic.get("stockCode") or "") if c.strip()]
        matched_t = next((alias_map.get(c, c) for c in codes if alias_map.get(c, c) in tickers), None)
        if not matched_t:
            continue
        yr = basic.get("year")
        q = basic.get("period") or donem_map.get((basic.get("ruleType") or basic.get("ruleTypeTerm") or basic.get("donem") or "").strip())
        if not yr or not q or int(q) not in (1, 2, 3, 4):
            continue
        key = (matched_t, int(yr), int(q))
        if pub_day and stmt not in by_day[(*key, pub_day)]:
            by_day[(*key, pub_day)][stmt] = disc_idx
        prev = earliest_stmt[key].get(stmt)
        if prev is None or (pub_iso and pub_iso < prev[0]):
            earliest_stmt[key][stmt] = (pub_iso, disc_idx)

    earliest_map = {k: {s: idx for s, (_, idx) in v.items()} for k, v in earliest_stmt.items()}
    return by_day, earliest_map


def main() -> None:
    with CANONICAL_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        canonical_map = {
            (r["ticker"], r["observation_period"]): r for r in csv.DictReader(f)
        }

    stmt_by_day, stmt_earliest = load_statement_disclosure_map({t for t, _ in canonical_map})

    with gzip.open(MISSING_JSONL_GZ, "rt", encoding="utf-8") as f:
        missing_records = [json.loads(line) for line in f]

    target_records = [r for r in missing_records if r.get("reason") in TARGET_REASONS]

    xls_cache: dict[str, list[tuple[str, bool, str, str, float | None]]] = {}
    parse_errors: list[tuple[str, str]] = []
    unique_files = sorted({r.get("source_file", "") for r in target_records if r.get("source_file")})
    for rel_fp in unique_files:
        fp = ROOT_DIR / rel_fp
        try:
            xls_cache[rel_fp] = load_xls_rows(fp)
        except Exception as exc:
            parse_errors.append((rel_fp, repr(exc)))
            xls_cache[rel_fp] = []

    audit_rows: list[dict[str, str]] = []
    verdict_counts: collections.Counter[str] = collections.Counter()
    by_reason_verdict: collections.Counter[tuple[str, str]] = collections.Counter()
    by_era_verdict: collections.Counter[tuple[str, str]] = collections.Counter()
    col_verdict: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    missed_labels_by_col: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    missed_samples_by_col: dict[str, list[tuple[str, str, str, str]]] = collections.defaultdict(list)
    blank_samples: list[tuple[str, str, str, str, str, str]] = []

    for rec in target_records:
        ticker = rec["ticker"]
        period = rec["period"]
        column = rec["column"]
        reason = rec["reason"]
        rel_fp = rec.get("source_file", "")
        parser_lbl = str(rec.get("source_label") or "")

        c_row = canonical_map.get((ticker, period), {})
        yr = int(period[:4])
        q_num = int(period[-1])
        stmt = _column_statement(column)
        rep_day = (c_row.get("report_available_at") or "")[:10]
        day_map = stmt_by_day.get((ticker, yr, q_num, rep_day), {}) if rep_day else {}
        earl_map = stmt_earliest.get((ticker, yr, q_num), {})
        disc_idx = (
            day_map.get(stmt)
            or day_map.get("UNIFIED")
            or earl_map.get(stmt)
            or earl_map.get("UNIFIED")
            or (c_row.get("disclosure_index") or "").strip()
        )
        consolidation = (c_row.get("consolidation") or "").strip()
        era = "2010-2015_BIFF8" if yr <= 2015 else "2016-2020_HTML"
        kap_url = f"https://www.kap.org.tr/tr/Bildirim/{disc_idx}" if disc_idx else ""

        rows = xls_cache.get(rel_fp, [])
        matches = [(sec, en, raw_l, norm_l, val) for sec, en, raw_l, norm_l, val in rows if _match_candidate(column, sec, norm_l)]

        with_vals = [(raw_l, val) for _, en, raw_l, _, val in matches if en and val is not None]
        blanks = [raw_l for _, en, raw_l, _, val in matches if (not en) or (val is None)]

        cons_norm = normalize_tr(consolidation)
        is_solo = ("konsolide olmayan" in cons_norm) or ("solo" in cons_norm)

        if with_vals:
            verdict = "LIKELY_PARSER_MISS"
            for raw_l, _ in with_vals:
                missed_labels_by_col[column][raw_l] += 1
            val_str = "; ".join(f"{lbl}={_fmt_val(v)}" for lbl, v in with_vals)
            if len(missed_samples_by_col[column]) < 2:
                missed_samples_by_col[column].append((ticker, period, kap_url, val_str))
        elif column == "T07_ana_ortaklik_net_kari_ytd" and is_solo:
            verdict = "SOLO_NO_MINORITY_SPLIT"
            val_str = ""
        elif blanks:
            verdict = "SOURCE_BLANK_IN_XLS"
            val_str = ""
            if len(blank_samples) < 5 and reason == "source_value_unavailable" and yr >= 2016:
                blank_samples.append((ticker, period, column, verdict, kap_url, "; ".join(blanks[:3])))
        else:
            verdict = "ROW_ABSENT_IN_XLS"
            val_str = ""
            if len(blank_samples) < 8 and yr >= 2016 and verdict == "ROW_ABSENT_IN_XLS":
                blank_samples.append((ticker, period, column, verdict, kap_url, ""))

        blank_str = "; ".join(dict.fromkeys(blanks))
        verdict_counts[verdict] += 1
        by_reason_verdict[(reason, verdict)] += 1
        by_era_verdict[(era, verdict)] += 1
        col_verdict[column][verdict] += 1

        audit_rows.append(
            {
                "ticker": ticker,
                "period": period,
                "era": era,
                "consolidation": consolidation,
                "column": column,
                "original_reason": reason,
                "verdict": verdict,
                "disclosure_index": disc_idx,
                "kap_url": kap_url,
                "source_file": rel_fp,
                "parser_source_label": parser_lbl,
                "candidate_rows_with_values": val_str,
                "blank_matching_labels": blank_str,
            }
        )

    fieldnames = [
        "ticker",
        "period",
        "era",
        "consolidation",
        "column",
        "original_reason",
        "verdict",
        "disclosure_index",
        "kap_url",
        "source_file",
        "parser_source_label",
        "candidate_rows_with_values",
        "blank_matching_labels",
    ]
    OUT_AUDIT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_AUDIT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)

    print(f"Audited records : {len(audit_rows)}")
    print(f"Unique raw files: {len(unique_files)} | Parse errors: {len(parse_errors)}")
    if parse_errors:
        for fp, err in parse_errors[:5]:
            print(f"  PARSE ERROR {fp}: {err}")
    print(f"Output CSV      : {OUT_AUDIT_CSV.relative_to(ROOT_DIR)}")

    print("\n=== OVERALL VERDICT COUNTS ===")
    total_audit = max(1, len(audit_rows))
    for v, n in verdict_counts.most_common():
        print(f"  {v:26s}: {n:4d} ({100.0 * n / total_audit:5.1f}%)")

    print("\n=== BY ORIGINAL REASON x VERDICT ===")
    for (rs, v), n in sorted(by_reason_verdict.items()):
        print(f"  {rs:28s} | {v:26s}: {n:4d}")

    print("\n=== BY ERA x VERDICT ===")
    for (er, v), n in sorted(by_era_verdict.items()):
        print(f"  {er:16s} | {v:26s}: {n:4d}")

    print("\n=== PER-COLUMN BREAKDOWN ===")
    hdr = (
        f"{'Column':46s} | {'Miss':>5s} | {'Solo':>5s} | {'Blank':>5s} | {'Absent':>6s} | {'Total':>5s}"
    )
    print(hdr)
    print("-" * len(hdr))
    sorted_cols = sorted(
        col_verdict.items(),
        key=lambda kv: (-kv[1]["LIKELY_PARSER_MISS"], -sum(kv[1].values()), kv[0]),
    )
    for col, cnt in sorted_cols:
        tot = sum(cnt.values())
        print(
            f"{col:46s} | {cnt['LIKELY_PARSER_MISS']:5d} | {cnt['SOLO_NO_MINORITY_SPLIT']:5d} | "
            f"{cnt['SOURCE_BLANK_IN_XLS']:5d} | {cnt['ROW_ABSENT_IN_XLS']:6d} | {tot:5d}"
        )

    print("\n=== TOP MISSED LABELS & SAMPLE KAP LINKS (LIKELY_PARSER_MISS > 0) ===")
    for col, cnt in sorted_cols:
        if cnt["LIKELY_PARSER_MISS"] == 0:
            continue
        print(f"\n[{col}] LIKELY_PARSER_MISS={cnt['LIKELY_PARSER_MISS']}")
        for lbl, n in missed_labels_by_col[col].most_common(5):
            print(f"  label ({n:3d}x): {lbl}")
        for tk, per, url, val_s in missed_samples_by_col[col]:
            print(f"  sample: {tk} {per} -> {url} | {val_s[:180]}")

    print("\n=== SAMPLE GENUINE BLANKS / ABSENT ROWS FOR SPOT-CHECK ===")
    for tk, per, col, vd, url, bl in blank_samples[:6]:
        print(f"  {tk} {per} | {col} | {vd} | {url} | {bl}")


if __name__ == "__main__":
    main()
