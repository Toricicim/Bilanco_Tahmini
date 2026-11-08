# AI ve geliştirici çalışma rehberi

Bu rehber bütün depo için geçerlidir. Son durum özeti **8 Kasım 2026** tarihlidir. Güncel kullanıcı talebi bu rehberdeki önerilerden önceliklidir. Önce mevcut işi ve değişiklikleri incele; yapılmış çalışmayı yeniden başlatma.

## 1. Her işe başlarken ve her committe

**Kullanıcının istediği ekip kuralı: Her commit, yapılan işin nedenini ve sonucunu geliştirme günlüğüne de kaydetmelidir.**

1. `git status --short`, mevcut branch ve son commitleri kontrol et. Başkasının yerel değişikliklerini sahiplenme veya silme.
2. Bu dosyayı, ardından [geliştirme günlüğünün](docs/GELISTIRME_GUNLUGU.md) en yeni kayıtlarını oku. İlgili iş paketinin belgelerini aşağıdaki sıradan seç.
3. Değişikliği istenen kapsamda yap; veri veya kodla ilgili varsayımları kaydet.
4. **Committen önce** günlüğün başına o commitin kaydını ekle: ne değişti, neden, hangi kontroller yapıldı, sonuç ve kalan işler. Günlük değişikliği aynı committe bulunmalı. Küçük bir değişiklik için kısa kayıt yeterlidir.
5. `AGENTS.md` dosyasını proje kuralları, giriş noktaları, veri sözleşmesi veya durum özeti gerçekten değiştiğinde güncelle. Her küçük işin ayrıntısını bu dosyaya yığma.
6. Commit mesajı, günlük kaydının konusu ve gerçek diff aynı işi anlatmalı. Başarısız veya çalıştırılmamış kontrolü başarılı diye yazma.

Yeni commitin kendi hash'i aynı committeki dosyaya yazılamaz. Günlükte benzersiz kayıt kimliği ve commit başlığı kullan; sırf kendi hash'ini eklemek için tekrar commit/amend yapma. Geçmiş commitlerin bilinen hash'leri tarihsel kayıtlarda kullanılabilir. Günlük kuralı eski commitleri yeniden yazma gerekçesi değildir.

## 2. Projenin amacı ve çalışma alanları

Dört kişilik bir araştırma ekibi, BIST şirketlerinin **henüz açıklanmamış finansal raporlarındaki ana kalemleri** makine öğrenmesiyle tahmin etmek istiyor. Hedef yalnız EPS veya hisse fiyatı değildir: gelir tablosu, finansal durum tablosu (dar anlamıyla bilanço) ve nakit akışı tablosu ayrı kalemler içerir.

- **Model öncesi:** araştırma, kaynak/veri hazırlama, özellik ve hedef tanımı, eğitim, zaman dışı değerlendirme ve sürümlü model paketi.
- **Model sonrası:** paketi sitede kullanma, yeni veriyi işleme, tahmin/rapor saklama, izleme ve yeniden eğitim için geri besleme.

Şu an öncelik **model öncesi veri kalitesi**. Kullanıcı, bilinen veri hataları dururken demo skoruna odaklanılmasını istemiyor. Yeni veri indirmek, veriyi ayrıştırmak, eğitim tablosu hazırlamak, model eğitmek ve siteyi çalıştırmak ayrı işlerdir.

Araştırmanın farklılaşma fikri: aynı olayın farklı faaliyet, coğrafya, döviz, girdi ve borç profillerine sahip şirketleri farklı etkilemesi. Savunma sanayisi bunun örneklerinden biridir; çalışmayı tek şirkete daraltma. “Savaş → savunma şirketinin kârı/hisse fiyatı kesin yükselir” gibi sabit yönler kodlama. Sipariş, ifa, gelir, maliyet ve tahsilat farklı zamanlarda etkilenebilir.

## 3. Önce hangi belgeler okunmalı?

| Sıra | Kaynak | Ne için? |
|---|---|---|
| 1 | [Geliştirme günlüğü](docs/GELISTIRME_GUNLUGU.md) | Son değişiklik, gerekçe, doğrulama ve sonraki iş |
| 2 | [Ana README](readme.md) ve [belge dizini](docs/README.md) | Amaç, kapsam ve iki çalışma alanı |
| 3 | [Model öncesi rehberi](docs/model_oncesi/README.md) | Araştırma/veri/eğitim teslimleri |
| 4 | [8 Kasım veri hattı raporu](docs/model_oncesi/VERI_HATTI_DUZELTMELERI_2026-11-08.md) | Düzeltilen hatalar, doluluk değişimleri ve açık kaynak işleri |
| 5 | [Script rehberi](scripts/README.md) | Çalıştırma sırası, zaman alanları, denetim çıkışları |
| 6 | [Kalite kayıtları](data/quality/README.md), [özet](data/quality/summary.json), [manifest](data/quality/manifest.json) | Güncel veri sürümü ve kanıtlar; eski sohbet özetinden daha güncel olabilir |
| 7 | [Değişken JSON kaydı](docs/model_oncesi/degiskenler.json), [üretilmiş liste](docs/model_oncesi/DEGISKEN_LISTESI.md) ve [değişken kullanım/eksik durumu](docs/model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md) | Aday girdiler, hedefler, CSV'de mevcut/eksik/ekstra sütunlar ve modelde kullanım durumu |
| 8 | [Algoritmalar](docs/model_oncesi/arastirma/2026-11-06-bilanco-tahmini/ALGORITMALAR_VE_CALISMA_MEKANIKLERI.md), [araştırma önerisi](docs/model_oncesi/arastirma/2026-11-06-bilanco-tahmini/ARASTIRMA_PROJESI_ONERISI.md), [makaleler](docs/model_oncesi/arastirma/2026-11-06-bilanco-tahmini/MAKALELER.md) | Model seçimi, temel kıyaslar ve bilimsel gerekçeler |
| 9 | [Ürün hedefi](docs/model_sonrasi/ISTENILEN_HEDEF.md), [mimari](docs/model_sonrasi/SISTEM_MIMARISI.md), [model yaşam döngüsü](docs/model_sonrasi/MODEL_YASAM_DONGUSU.md) | Site/işletim işi yapılıyorsa; bunlar tasarım belgeleridir |

Eski 7 Kasım denetimleri ve arkadaşın `cd10910` sürümündeki demo raporu **tarihsel kayıttır**. O raporlardaki “çözüldü”, “sızıntısız” veya başarı ifadelerini bugünkü veri seti için otomatik doğru sayma. Kaynak projelerin makale skorları da bu depoda yeniden üretilmiş başarı değildir.

## 4. Son doğrulanmış durum

Bu tablo bir durum fotoğrafıdır; sayıları gelecekte zorla eşitlemek için test yazma. Veri değiştiğinde güncel manifest, kalite özeti ve denetim çıktısından yeniden kontrol et.

| Konu | 8 Kasım 2026 durumu |
|---|---|
| Kanonik gözlem tablosu | **30 şirket × 44 çeyrek = 1.320 satır**, 2010Q1–2020Q4 |
| Sütun | **110**; kimlik, kaynak/zaman metadatası, finansallar ve türevler dahil; 110 model girdisi değil |
| Şirket kapsamı | Altı gruptan beşer şirket; tüm BIST ve bütün raporlama şemaları değil |
| Öncelikli dört hedef | Hasılat, dönem net kârı, toplam varlık ve toplam özkaynak; mevcut tabloda boşluk yok |
| Kod kontrolü | **23 regresyon testi geçti** |
| Üretim denetimi | `errors=[]`, **çıkış 2**: kaynak/kapsam/yayın sürümü incelemesi sürüyor |
| Kaynak/kapsam bayrağı | **105 şirket–dönem kaydı**; bayraklar birbiriyle örtüşebilir ve hepsi kesin tutar hatası değildir |
| Brüt kâr taraması | 1 TL eşiğinde **14 olağan kaynak uzlaşması**, **76 karma faaliyet kapsamı** incelemesi |
| Tarihsel kullanılabilirlik | `fully_point_in_time_verified=false` |
| Model/site | Mevcut veriyle doğrulanmış, üretime hazır model paketi ve çalışan tahmin sitesi yok |

**Bu veri seti henüz bütün satır/sütunlarıyla güvenilir model demosuna hazır kabul edilmiyor.** Testlerin geçmesi, düzeltilen kod davranışını doğrular; bütün kaynak tutarlarını ve tarihsel sürümleri doğrulamaz. “Main'e alındı”, “CSV üretildi” veya “alan dolu” ifadeleri eğitim onayı değildir.

Son veri hattı düzeltmesi `b02bee9`, önceki yerel belgelerin korunması `8edba7b` commitlerindedir. Bunlar araştırma geçmişidir; işe başlarken güncel HEAD'i ayrıca kontrol et.

## 5. Dosya ve kod haritası

- **Tek kanonik CSV:** `data/bist_bilanco_tahmini_2010_2020.csv`. Kök dizindeki eski kopya kaldırıldı; tekrar oluşturma.
- **Ham finansallar:** `data/kap_raw_xls/`; eski BIFF XLS ve HTML içerikli XLS biçimleri var. Bazı BIFF hücrelerinde bütün satır CSV metni olarak tutuluyor.
- **KAP arşivleri/kataloğu:** `data/kap_zips/`, `data/kap_fr_catalog_2010_2020.json`.
- **Dış veri önbelleği:** `data/external/`; aylık makro/risk ve günlük FX/FSI tabloları ile özgün indirmeler.
- **İndirme:** `scripts/fetch_kap_financials_2010_2020.py`, `scripts/fetch_external_macro_and_risk.py`.
- **Ayrıştırma/üretim:** `scripts/parse_and_build_dataset.py`. Önce `extract_rows_from_*`, `parse_financial_rows`, `derive_quarterly_flows`, `select_source_files`, `build_dataset`, `merge_external_macro_and_risk`, `save_dataset` akışını incele.
- **Kalite yardımcıları:** `scripts/financial_quality.py`; kaynak satırı takibi, eksiklik sınıfları, takvim pencereleri, atomik yazma.
- **Denetim:** `scripts/audit_dataset.py`; mevcut çıktıyı okur, indirme/eğitim yapmaz.
- **Regresyon örnekleri:** `tests/test_financial_pipeline.py`; gerçek AEFES/GSDDE/TOASO/CCOLA raporları ve KAREL nakit uzlaşması dahil.
- **Önceki yerel çalışmalar:** `docs/model_oncesi/arsiv/`; ZIP ve SHA-256 manifestosu korunur. Buradaki `.py.txt` bir tarihsel kopyadır, güncel çalıştırılacak betik değildir.

## 6. Ortam ve kontrol komutları

Veri hattı **Python 3.12.2** ile doğrulandı. [requirements-data.txt](requirements-data.txt) doğrudan veri bağımlılıklarını sabitler. Sistem `python3` yorumlayıcısının aynı ortam olduğunu varsayma. Model betiği ek ML bağımlılıkları ister; veri ortamının kurulması model ortamının tamamlandığı anlamına gelmez.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-data.txt

# Mevcut kaynaklardan üretim; ağ isteği yapmaz.
.venv/bin/python -B scripts/parse_and_build_dataset.py

# Denetim; dönüş kodunu aşağıdaki anlamıyla değerlendir.
.venv/bin/python -B scripts/audit_dataset.py

# Kod/veri hattı değişikliği için regresyonlar.
.venv/bin/python -B -m unittest discover -s tests -v

# Değişken sözlüğünün üretilmiş Markdown ile uyumu.
.venv/bin/python scripts/render_feature_list.py --check
```

Kanonik dosyayı değiştirmeden denemek için `parse_and_build_dataset.py --output-dir /tmp/bilanco-deneme`, ardından `audit_dataset.py --data-dir /tmp/bilanco-deneme` kullanılabilir.

Denetim çıkışları:

- **0:** denetlenen alanlarda hata veya açık inceleme maddesi yok; denetimin kapsamını yine belirt.
- **1:** dosya/şema/hash veya hesap tutarlılığı hatası. Önce hatayı çöz.
- **2:** üretim kontrolleri geçti; kaynak, faaliyet kapsamı veya tarihsel yayın incelemesi devam ediyor. Bunu başarısız birim testiyle karıştırma veya “veri tamamen hazır” diye sunma.

Belge değişikliğinde ilgili bağlantıları ve gerçeklerle uyumu kontrol et; kod değişmemişse sırf commit oluşturmak için bütün veriyi tekrar üretme veya model eğitme. Parser, kalite yardımcıları, ham girdi veya veri tanımı değişmişse etkisine uygun testleri çalıştır, gerekli çıktıları yeniden üret ve manifestoyu güncelle. Eski manifestoya yeni CSV hash'i elle yazmak yeniden üretilebilirlik sağlamaz.

## 7. Veri sözleşmesinde korunacak kurallar

### Finansal anlam, birim ve kapsam

- Akış kalemlerini YTD ve tek çeyrek olarak ayır; bilanço kalemleri dönem sonu stok değeridir. Q4 sözleşmesi yıllık YTD − dokuz aylık YTD'dir. Ara dönem raporunda sağlanan üç aylık değer, gerçek sıfır dahil, korunur.
- TL / bin TL / milyon TL, para birimi, konsolidasyon ve dönem aynı temelde olmalı. Yeni dönemlere genişlerken enflasyon muhasebesi ve karşılaştırmalı yeniden düzenlemeleri ayrıca ele al.
- Kaynak satırı, özgün tutar, çarpan, dosya/hash, dönüşüm yöntemi ve düzeltme kanıtını koru. Ham dosyayı CSV ile aynı sonucu versin diye değiştirme.
- Hasılat/satış maliyeti ile genel brüt kâr farklı faaliyet kapsamlarından geliyorsa standart marj üretme. Finansal faaliyet alt toplamı içeren TOASO/GSDDE gibi biçimleri sıradan tabloya zorla uydurma.
- Toplam kâr ≠ ana ortaklık kârı; toplam özkaynak ≠ ana ortaklık özkaynağı. Otomatik birbirine yedekleme.
- Yatırım nakit akışı tek başına CAPEX değildir. FAVÖK için amortisman/itfa gibi ek bileşenler gerekir. Sermayeye bölünen yaklaşık HBK, ağırlıklı ortalama pay sayısı doğrulanmadan gerçek EPS sayılmaz.
- Bilanço eşitliği türetilmiş toplamlarla sağlanmış olabilir; bağımsız kaynak doğruluğu kanıtı sayma.

### Eksikler ve sıfırlar

- `None`/boş; **şirket yayımlamadı**, **sıfırdır** veya **uygulanamaz** demek değildir.
- `unresolved_source_or_mapping`: kaynak/eşleme incelemesi gerekli. `source_value_unavailable`: okuyucu sayıya ulaşamadı; özgün PDF/dipnot gerekebilir. `missing_component`: gerekli bileşen yok. `insufficient_history`: istenen geçmiş bulunmuyor. Karma marjlar `income_statement_scope_mismatch` ile işaretlenir.
- Eksik bileşeni sıfırlayıp toplam/net borç üretme. Bilinen alt bileşeni ayrı tut; bilinmeyen toplamı kesin gibi sunma.
- Eksik etiketi modelle/ortalama ile doldurup gerçek hedef diye kullanma. Girdi doldurma daha sonra gerekçeli ve yalnız eğitim verisinden öğrenilen bir işlem olabilir.
- Tüm boşlukları gidermek veya doluluğu artırmak tek başına başarı ölçütü değildir. Sıfır/uygulanamaz kararı kaynak kanıtıyla verilmelidir.
- Nakit akışı bölümündeki son sayısal satırın toplam olduğunu varsayma. Başlık varyantlarını toplam/alt kalem ayrımını koruyarak eşle.

### Tahmin anı ve rapor sürümü

- Her deney `target_period=q`, `forecast_origin=t0`, hedef sürümü ve bilgi kesimini açıkça tanımlar. İlk görev adayı, çeyrek sonu gün sonunda henüz açıklanmamış o çeyreğin sonucunu tahmin etmektir.
- Girdiler için yalnız `available_at <= t0` bilgisi kullanılabilir. Aynı satırdaki hedef çeyrek hasılatı/kârı/oranı model girdisi değildir.
- `report_available_at`: seçilmiş rapor sürümünün zamanı. `source_available_at`: kullanılan ek düzeltme kanıtını da kapsar. `available_at`: çeyrek farkının önceki rapora ihtiyacını da kapsayan temkinli finansal satır zamanı.
- `earliest_known_publication_at` aynı tutarın o gün bilindiğini kanıtlamaz. `first_published_at` mevcut şemada seçilmiş rapor zamanının eski takma adıdır; gerçek ilk sürümün kesin tarihi diye kullanma.
- İlk tarih ile sonraki düzeltmenin tutarını birleştirme. İlk açıklanan hedef ile son düzeltilmiş hedef politikasını ayır. KAREL düzeltmesinin karşılaştırmalı kanıtı 2013'te biliniyor; bu tarihi 2012'ye taşıma.
- q−1/q−4 veya başka bir gecikme yalnız satır kaydırılarak güvenli olmaz. Dönemi ve yayın zamanını kontrol et. q−2'ye fallback yapılıyorsa onun tarihi de doğrulanmalı; yeni/eksik dönemli şirketlerde satır sayısı takvim çeyreği sayısı olmayabilir.
- Eğitim ve ayar etiketleri de modelin fit kesiminde yayımlanmış olmalı. Rastgele şirket–çeyrek satır bölmesi yapma; aynı mali dönem bütün şirketleriyle aynı zaman bloğunda kalmalı.
- Aylık makroyu 1/2 ay kaydırmak, tarihsel yayın kaydı ve veri sürümü arşivini yerine getirmez. Mevcut OFR takvimi açık bir federal iş günü varsayımıdır. Geriye dönük revize seri deneyi ile gerçek zaman koşullu test iddiasını ayır.
- M03'ü ticari kredi faizi diye etiketleme: mevcut seri OECD gecelik bankalararası faiz vekilidir.

## 8. Kalite kanıtlarını okuma

`data/quality/manifest.json` en son tamamlanmış üretimin CSV/kod/girdi/denetim hash'lerini içerir. `summary.json` güncel doluluk, açık bayraklar ve doğrulama sınırlarını verir. Manifestoyla uyuşmayan CSV'nin eski özetini güncelmiş gibi kullanma.

`financial_sources.jsonl.gz` ve `missing_values.jsonl.gz` dosyalarında her satır bir JSON nesnesidir. Şirket/yıl/çeyrek anahtarıyla CSV'nin kaynak dosyası ve birim alanlarına bağlanır.

```python
import gzip, json

with gzip.open("data/quality/missing_values.jsonl.gz", "rt", encoding="utf-8") as stream:
    for line in stream:
        item = json.loads(line)
        if item["ticker"] == "AEFES":
            print(item)
```

Yeni doğrulama/düzeltmede kaynak raporu, ilgili satır/hücreyi, birim ve dönemini, seçilmiş sürümü, kanıtın kullanılabilirlik zamanını ve etkilenen türevleri kaydet. Aynı kaynak örneğini anlamlı bir regresyonla koru; yalnız implementasyonu tekrar eden test yazma.

## 9. Sıradaki işler ve bitiş ölçütleri

### P0-A — Kaynak ve eksiklik denetimini tamamla

1. Kalite kayıtlarındaki örnekleri şirket/dönem/sütun bazında gruplandır. Önce ilk dört hedefi veya onların girdilerini etkileyenleri ele al.
2. Kaynakta gerçekten boş alanları özgün rapor PDF'si/dipnotla karşılaştır. KAREL ilk yayım kanıtını, THYAO/TOASO/SARKY birim istisnalarını ve karma faaliyet kapsamlarını doğrula.
3. Olağan brüt kâr farklarıyla karma faaliyet farklarını ayrı değerlendir; yuvarlama birimini dikkate al. “Bayrak sayısı sıfır olsun” diye satır silme veya değer uydurma.
4. Kısa/uzun bileşenlerin boşluğunu yapısal sıfır, ayrı sunulmama, kaynağa erişememe ve parser hatası olarak kanıtla ayır.

**Bitiş:** kullanılacak kapsamın her önemli bayrağı için çözüm veya gerekçeli dışlama kaydı; özgün değerler korunmuş; etkilenen türevler yeniden üretilmiş; regresyonlar ve manifest tutarlı. Dışlanan satırları ve hedef bazındaki kullanılabilir örnek sayısını raporla.

### P0-B — Yayın sürümü ve makro kullanılabilirliğini doğrula

- Seçilen tutarın hangi bildirimde ilk görüldüğünü doğrula; dosya tarihini tek başına erkene çekme.
- Dış serilerde gözlem tarihi, gerçek yayın zamanı, indirme/sürüm bilgisi ve revizyon politikasını ayır. Eski önbelleğin indirme zamanı bilinmiyorsa uydurma.
- M03 için doğru ticari kredi serisini araştır veya bankalararası vekilini ayrı tanımla.
- Tarihsel vintage bulunamayan deneyi açıkça sınırlı/geriye dönük deney olarak etiketle; gerçek zaman koşullarına uygun başarı iddiası üretme.

**Bitiş:** seçilen deneyin her girdisi için denetlenebilir kullanılabilirlik kuralı; desteklenmeyen tarih/kapsam için açık dışlama veya deney sınırı.

### P0-C — Sözlük eşlemesi ve eğitim matrisi

- Kanonik özellik kaydı [degiskenler.json](docs/model_oncesi/degiskenler.json): **51 girdi ailesi = 26 P0 + 19 P1 + 6 P2**; ayrıca **17 hedef**. Aile sayısı model sütun sayısı değildir; bütün adayları kullanmak zorunlu değildir.
- Sözlükteki değişkenlerin CSV ve modelde kullanım/eksik/ekstra durumu [DEGISKEN_DURUMU_VE_EKSIKLER.md](docs/model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md) dosyasında tutulur.
- CSV öneklerini sözlük ID'si sanma. Sözlük F01 “şirket ölçeği”, CSV F01 büyüme; sözlük F07 “vergi”, CSV F07 finansman geliridir. Açık kolon/tanım/birim/dönem eşlemesi gerekli.
- Yeni bir değişken/sütun eklendiğinde, çıkarıldığında, adı değiştiğinde veya model deneyine dahil edildiğinde önce [degiskenler.json](docs/model_oncesi/degiskenler.json) kaydını güncelle, sonra `scripts/render_feature_list.py` ile [DEGISKEN_LISTESI.md](docs/model_oncesi/DEGISKEN_LISTESI.md) dosyasını üret (üretilmiş listeyi elle değiştirme) ve ardından [DEGISKEN_DURUMU_VE_EKSIKLER.md](docs/model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md) dosyasındaki kullanım/eksik/ekstra tablolarını güncelle. CSV'de kolon bulunması `data_status=verified` veya model katkısı kanıtı değildir.
- Seçilen hedefler için q/t0, girdi kaynak dönemleri/sürümleri, kullanılabilirlik ve kalite maskelerini içeren eğitim matrisi oluştur. Hedef dönemin varlığını geçmiş ölçek yerine kullanma.
- **Karma frekanslı (günlük/aylık → çeyreklik) ve ufuk-bağımlı (nowcasting) yaklaşım:** Tabloyu 90 güne çoğaltıp aynı çeyreklik hedefi ($y_q$) 90 satıra kopyalama (pseudoreplication/sözde-tekrar yasaktır). Bunun yerine **3. yaklaşımı** uygula:
  1. Günlük serilerden (`USDTRY`, `EURTRY`, `OFR FSI` ve eklenecek günlük `GPRD`) her bilgi kesim anı ($t_0$) için çeyrek içi **dağılım/yörünge özellikleri** (çeyrek ortalaması, kesim günü seviyesi, volatilite/std, zirve şok/max ve son günlerin ağırlığı) üret (gelir tablosu akış kalemleri dönem ortalamasına, bilanço stok kalemleri dönem sonu seviyesine duyarlıdır).
  2. Gün geçtikçe tahminin keskinleşmesini sağlamak için her şirket–çeyrek üzerinde belirli **bilgi kesim ufukları** ($t_0 \in \{+30\text{g}, +60\text{g}, +90\text{g (çeyrek sonu)}, +120\text{g (bilanço öncesi)}\}$) ve `days_since_quarter_start` (bilgi olgunluk günü) tanımlayarak, yalnız o güne kadar açıklanmış (`available_at <= t0`) günlük/aylık verilerle ufuk-bağımlı tahmin (nowcasting) kur.

**Bitiş:** veri/özellik/etiket sözleşmesi, sızıntı kontrolleri, hedef bazında kapsama ve dondurulmuş zaman bölmeleri. Kaynak denetimi açık bütün CSV'yi doğrudan modele verme.

### P1 — İlk bilimsel model deneyi

Veri kapsamı doğrulandıktan sonra dört hedefle başla: hasılat, net kâr, toplam varlık ve özkaynak. Her hedef için şirketleri birlikte kullanan küçük modeller; şirket başına 44 satırla ayrı model kurmak başlangıç tercihi değil.

- Önce geçen yıl aynı çeyrek ve son bilinen değer kıyasları; sonra Ridge ve sınırlı karmaşıklıkta Random Forest.
- Deney sırası kayıtlıdır: E0 finansal geçmiş/takvim/sektör; E1 yerel makro; E2 ayrı GPR/GEPU/OFR; E3 şirket profilleri; E4 sınırlı etkileşimler. E5 birleşik stres özeti alternatifidir.
- Eksik doldurma/ölçekleme eğitimde öğrenilir; testte yeniden öğrenilmez. Test dönemine tekrar tekrar bakarak seçim yapılmaz.
- Kalem bazında MAE, geçmiş ölçeğe göre hata ve temel kıyasa göre kazanım raporla. Sıfır/negatif kâr nedeniyle MAPE'yi ana metrik yapma. R²'yi “yüzde doğruluk” diye anlatma.
- 30 şirkette tekrarlanan makrolar yalnız 44 ortak çeyrek içerir. 2010–2020 sonucu bütün BIST'e, 2021 sonrası rejimlere veya 2026 canlı kullanıma genellenmiş kabul edilmez.

### P1/P2 — Şirket profilleri ve ürün

Araştırma farklılaşması için faaliyet/ürün gelir karması, ihracat/yurt dışı gelir payı, net döviz pozisyonu, enerji/emtia rolü, coğrafi satış ve uygun sektörlerde sipariş/ifa görünürlüğü öncelikli adaylardır. Güvenilir kapsama ve yayın tarihleri sağlanmadan türetilmiş etkileri kesinleştirme.

Ürün önerisi; baştan katalog, talepte arka plan hazırlığı, kalıcı rapor ve düzenli artımlı güncellemedir. Site açılışı yeni model eğitimi değildir. Katalogda bulunma, veri hazır olma ve model kapsamına girme ayrı durumlardır. Mimari teknoloji adayları henüz kurulmuş altyapı sayılmaz.

Abonelik/yenileme hakkı fikri mimariye eklenmesi istenmiş bir gereksinim değildir. Kullanıcı ayrı bir kaynak-link CSV'sini de henüz açıkça onaylamadı; bu öneriyi otomatik uygulamaya alma. Güncel görev veya sonraki açık kullanıcı talebi bu durumu değiştirebilir.

## 10. Ekip, Git ve teslim alışkanlığı

Dört kişilik ekip için önerilen iş paketleri: finansal kaynak/doğrulama; yayın tarihi ve makro sürümleri; veri sözlüğü ve kalite/eğitim matrisi; kapsam onayından sonra model değerlendirmesi. Aynı parser, sözlük ve üretilen CSV üzerinde eşzamanlı değişiklikler paylaşılmalı; iş paylaşımı otomatik olarak yeni ajan başlatma talimatı değildir.

- Başlangıçta yerel diff'i incele. Başkasının değişikliklerini `reset --hard`, `clean` veya üzerine yazma ile kaldırma. Gerekirse izole branch/worktree ve doğrulanmış yedek kullan.
- Mevcut ham kaynaklarla başla; tüm arşivi sebepsiz tekrar indirme. Yeni kaynak sürümünü eski kanıtı kaybetmeden sakla.
- Kaynak dosyaları, aday sözlükleri, tarihsel raporları ve lisansları koru. Düzeltmeyi geçmişi daha iyi gösterecek sessiz veri değişikliği olarak yapma.
- Kullanıcı push/PR istediğinde mevcut feature branch'i yayımla ve gerçek diff'i anlatan PR aç. PR açma talebi tek başına main'e merge veya force push talebi değildir.
- PR'da veri üretimi ile bilimsel hazır olma durumunu ayrı yaz. Kalan kalite uyarılarını, kırılan tüketici yollarını ve model skorlarının hangi veri sürümüne ait olduğunu belirt.
- Her committe [günlüğü](docs/GELISTIRME_GUNLUGU.md) güncelle. Teslimde değişen davranışı, doğrulamayı ve açık işleri kısa, somut biçimde anlat.

Yeni bir AI için ilk somut görev, güncel günlük ve kalite özetinden bir P0 iş paketini seçip ilgili kaynak kayıtları üzerinde kanıt üretmektir. Kullanıcı farklı bir iş verdiyse o kapsamı izle.
