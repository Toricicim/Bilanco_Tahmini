# Veri çekme, ayrıştırma ve denetim

Kanonik çıktı **`data/bist_bilanco_tahmini_2010_2020.csv`** dosyasıdır. Depo kökünde ikinci CSV üretilmez. Mevcut kapsam 30 şirket × 44 çeyrek (2010–2020); bu tablo hazır bir girdi/hedef eğitim matrisi değildir.

## Ortam ve mevcut dosyalardan üretim

Python **3.12.2** ile doğrulandı. Veri hattının doğrudan bağımlılıkları [requirements-data.txt](../requirements-data.txt) dosyasında sabitlendi; model eğitiminin bağımlılıkları ayrıdır.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-data.txt
.venv/bin/python -B scripts/parse_and_build_dataset.py
.venv/bin/python -B scripts/audit_dataset.py
.venv/bin/python -B -m unittest discover -s tests -v
```

Ham dosyalar depoda mevcutsa üretici bunları okur ve ağ isteği yapmaz. Ayrı bir klasöre deneme çıktısı yazmak için:

```bash
.venv/bin/python -B scripts/parse_and_build_dataset.py --output-dir /tmp/bilanco-deneme
.venv/bin/python -B scripts/audit_dataset.py --data-dir /tmp/bilanco-deneme
```

## Betikler

| Betik | Görev |
|---|---|
| [fetch_kap_financials_2010_2020.py](fetch_kap_financials_2010_2020.py) | KAP çeyreklik arşivlerini, seçilmiş şirketlerin XLS dosyalarını ve finansal bildirim kataloğunu indirir. Önbellek varsa kullanır. |
| [fetch_external_macro_and_risk.py](fetch_external_macro_and_risk.py) | GPR/GPRT/GPRA (Iacoviello), GEPU (Policy Uncertainty), FSI (OFR), kurlar (Yahoo), makro (TCMB ve DBnomics üzerinden OECD) verilerini indirip önbellekler. M03 hâlâ gecelik bankalararası faiz vekilidir; ticari kredi faizi değildir. |
| [parse_and_build_dataset.py](parse_and_build_dataset.py) | Mevcut ham dosyaları okur; birim, satır eşlemesi ve çeyrek dönüşümlerini uygular; tek CSV ve kalite kanıtlarını üretir. |
| [financial_quality.py](financial_quality.py) | Kaynak satırı takibi, eksiklik nedenleri, takvim hesapları ve atomik dosya yazma yardımcıları. |
| [audit_dataset.py](audit_dataset.py) | Şema, kaynak/hash, manifest, sonlu sayı, bilanço, zaman ve kapsam kontrollerini yapar; veri değiştirmez. |

İlk indirme gerektiğinde sırasıyla dış veri ve KAP indirme betikleri çalıştırılır; ardından üretici çağrılır. Veri setini tekrar üretmek için yeniden indirmek gerekmez.

## Boş değer ve kaynak kuralları

- Gerçek sayısal sıfır korunur. Boş/tanınamayan değer için sıfır uydurulmaz.
- `unresolved_source_or_mapping`, şirketin açıklamadığı anlamına gelmez; kaynak veya eşleme denetimi gerekir.
- Kısa/uzun vadeli bileşenlerden biri bilinmiyorsa kesin toplam bilinmiyor kabul edilir. Bilinen alt bileşenler ayrı sütunlarda korunur.
- Eksik borç, net borç hesabında sıfır yapılmaz. Toplam/ana ortaklık kârı ve özkaynağı birbirine otomatik eşitlenmez.
- Çeyrek dönüşüm yöntemi ve gereken kümülatif bileşenler kaydedilir. Eksik bileşen sonraki çeyrek farkını da etkileyebilir.
- Karma finansal/ticari faaliyetlerde toplam brüt kâr ile ticari hasılatın kapsamı farklı olabilir. Standart brüt marj bu durumda boş bırakılıp neden kaydedilir.

Kaynak dosya/hash/birim bilgileri CSV'de, alanların kaynak satır etiketleri ve eksiklik nedenleri [data/quality](../data/quality/README.md) altında tutulur. Ayrı kaynak-link CSV'si bu değişikliğin kapsamında üretilmedi.

## Yayın zamanları

- `report_available_at`: seçilmiş finansal rapor sürümünün yayın zamanı.
- `source_available_at`: bu rapor için kullanılan ek düzeltme kanıtının zamanı da hesaba katılmış kaynak zamanı.
- `available_at`: çeyrek farkında önceki rapora ihtiyaç varsa onun kaynak zamanını da kapsayan, finansal satırın tamamı için temkinli kullanılabilirlik zamanı.
- `earliest_known_publication_at`: bulunan en erken başlık/katalog zamanı; aynı tutarların o gün bilindiğini kanıtlamaz.
- `first_published_at`: eski tüketiciler için korunan seçilmiş rapor zamanı takma adı; gerçek ilk yayımlanan sürümün kesin kanıtı olarak kullanılmamalı. Yeni finansal zaman kontrolleri `available_at` kullanmalı.

Makrolar için 1/2 aylık gecikmeler hâlâ varsayım; eski veri sürümleri yeniden kurulmadı. OFR takvimi ABD federal tatilleriyle iki iş günü varsayımı kullanır ve gerçek yayın kayıtlarının yerini tutmaz. Kur değişimi 90 takvim günlük ankora, FSI ortalaması 60 gerçek gözleme göre hesaplanır.

## Denetim sonucu

- Çıkış `0`: denetlenen alanlarda hata veya açık inceleme maddesi yok.
- Çıkış `1`: dosya/şema/hash veya hesap tutarlılığı hatası var.
- Çıkış `2`: üretim kontrolleri geçiyor; kaynak, faaliyet kapsamı veya tarihsel yayın/sürüm incelemesi devam ediyor. **Eğitime hazır onayı değildir.**

Güncel düzeltmeler ve kalan sınırlar [veri hattı raporunda](../docs/model_oncesi/VERI_HATTI_DUZELTMELERI_2026-11-08.md). Eski demo sonuçları önceki CSV'ye aittir; bu sürümde model yeniden eğitilmedi.
