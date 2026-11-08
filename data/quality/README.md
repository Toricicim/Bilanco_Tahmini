# Kaynak ve eksiklik denetimi

Bu dosyalar `scripts/parse_and_build_dataset.py` tarafından kanonik `data/bist_bilanco_tahmini_2010_2020.csv` ile birlikte üretilir.

- `manifest.json`: CSV, ayrıştırıcı, kalite yardımcıları, KAP kataloğu, dış veri önbellekleri ve denetim dosyalarının SHA-256 özetleri. En son yazılır; tamamlanmış üretimin dosyalarıyla eşleşmelidir.
- `summary.json`: sütun dolulukları, eksiklik nedenleri, işaretli raporlar ve doğrulama sınırları. `fully_point_in_time_verified=false`, gerçek tarihsel yayın/sürüm denetiminin tamamlanmadığını belirtir.
- `financial_sources.jsonl.gz`: her raporun finansal alanları için kaynak satır etiketi, özgün tutar, ölçeklenmiş tutar ve raporlanan/türetilen/düzeltilen ayrımı; ayrıca çeyrek dönüşüm yöntemi ve düzeltme kanıtı.
- `missing_values.jsonl.gz`: boş hücrelerin şirket, dönem, sütun ve neden kayıtları. `unresolved_source_or_mapping`, şirketin açıklamadığının kanıtı değildir; eşleme veya kaynak incelemesi gerekir.

Dosyaları düzenlemek yerine üreticiyi yeniden çalıştırın. Gzip içindeki her satır bağımsız bir JSON nesnesidir:

```python
import gzip, json
with gzip.open("data/quality/missing_values.jsonl.gz", "rt", encoding="utf-8") as stream:
    for line in stream:
        record = json.loads(line)
        if record["ticker"] == "AEFES":
            print(record)
```

Boşluğu sıfıra çevirmek doğrulama değildir. Kısa/uzun vadeli iki bileşenden biri bilinmiyorsa kesin toplam üretilmez. Bu nedenle yeni sürümde bazı toplamlar daha fazla boş görünebilir; bilinen alt kalemler ve eksikliğin nedeni korunur.

Bu klasör ek bir kaynak-link CSV'si içermez; o çıktı ayrı kullanıcı kararıdır.
