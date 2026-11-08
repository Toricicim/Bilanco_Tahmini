# Veri yeterliliği ve ilk demo kararı — 7 Kasım 2026

**Karar: Veri miktarı küçük bir tarihsel demo için yeterli bir başlangıç; mevcut CSV doğrudan güvenilir model eğitimine hazır değil.** Önce finansal doğruluk, rapor sürümü/yayın zamanı ve girdi–hedef ayrımı tamamlanmalı. Bu incelemede model eğitilmedi ve kaynak veriler değiştirilmedi.

İki ayrı inceleme yapıldı: biri ham dosyalar ve finansal kaliteyi, diğeri tahmin zamanı, değişken kapsamı ve demo deneyini denetledi. Finansal dosyaların tamamı resmî PDF'lerle tek tek karşılaştırılmadı; aşağıdaki şüpheli kayıtlar tam doğruluk sertifikası değildir.

İncelenen depo sürümü: `91a7d0eba593dd90b2d37a4e73bdfbb4756b421c`. Sayısal sonuçlar ve sorunlu kayıt anahtarları [JSON denetim çıktısında](veri_denetimi_2026-11-07.json), tekrar çalıştırılabilir kontroller [audit_dataset.py](arsiv/audit_dataset_ilk_inceleme.py.txt) dosyasındadır. JSON, CSV/kod/katalog özetlerini SHA-256 ile kaydeder; bu bir eğitim veri manifestosunun yerine geçmez.

## 1. Elimizde ne var, neye yeter?

| Özellik | Sonuç | Yorum |
|---|---:|---|
| Şirket × çeyrek | 30 × 44 = **1.320 gözlem** | Şirket başına 2010Q1–2020Q4 |
| Sütun | **92** | Kimlik, aynı dönem finansalları, oranlar, makro/risk; 92 hazır model girdisi değil |
| Sektör grubu | 6 grupta 5'er şirket | Bütün BIST kapsamı değil |
| Tekrarlanan şirket–çeyrek | **0** | Panel düzenli |
| Varlık = yükümlülük + özkaynak | 1.320 satırda 1 TL toleransla sağlanıyor | Bazı toplamlar parser'da bu eşitlikten türetildiği için bağımsız doğruluk kanıtı değil |
| Makro/risk zaman çeşitliliği | **44 çeyrek** | Aynı çeyreğin riskini 30 şirkette tekrarlamak 1.320 bağımsız makro gözlem yaratmaz |

**Yeterli:** finans dışı seçilmiş şirketlerde birkaç kalem için geçmişe dönük temel kıyas ve küçük tablosal ML deneyi.

**Henüz yeterli değil:** tüm BIST'e genelleme, banka/sigorta tabloları, 2026'da canlı tahmin, 2021 sonrası rejimler veya olayların şirketlere farklı etkisini güçlü biçimde öğrenme. Sonraki veri genişletme önce daha yakın dönemleri ve tutarlı muhasebe temelini kapsamalı; enflasyon muhasebesi uygulanan raporların karşılaştırılabilirliği ayrıca ele alınmalı. Yalnız şirket sayısını artırmak zaman çeşitliliğinin yerini tutmaz. Örneklemin hangi tarihli şirket evreninden seçildiği de kaydedilmeli; kapanan/kottan çıkan şirketleri dışlama ihtimali değerlendirilmelidir.

### Finansal hedeflerde doluluk

Doluluk, tutarın doğru veya o tarihte bilinebilir olduğu anlamına gelmez.

| Tek çeyrek akış / dönem sonu stok | Dolu / 1.320 | Eksik |
|---|---:|---:|
| Hasılat, brüt kâr, net kâr, vergi | Her biri 1.320 | 0 |
| Satış maliyeti, esas faaliyet kârı | Her biri 1.319 | 1 |
| Finansman gideri | 1.304 | 16 |
| Nakit, toplam varlık, toplam yükümlülük, özkaynak | Her biri 1.320 | 0 |
| Ticari alacak | 1.282 | 38 |
| Stok | 1.293 | 27 |
| Finansal borç | 1.303 | 17 |
| İşletme nakit akışı | 1.320 | 0; ciddi tutar sorunları var |
| Yatırım nakit akışı | 1.255 | 65 (%4,9) |
| Finansman nakit akışı | 1.169 | 151 (%11,4) |

## 2. Eğitimden önce çözülmesi gerekenler

### A. İki CSV farklı sürümler taşıyor

| Eksik alan | [Kök CSV](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/bist_bilanco_tahmini_2010_2020.csv) | [data/ CSV](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/data/bist_bilanco_tahmini_2010_2020.csv) |
|---|---:|---:|
| `first_published_at` | **38** | **570** |
| `disclosure_index` | **50** | **750** |

İki dosyanın 1.320 şirket–çeyrek anahtarı aynı. Finansal ve makro sayılar `rtol=1e-12, atol=1e-9` karşılaştırmasında aynı; oranlarda metinsel/ondalık gösterim farkları var. Yayın tarihi hücrelerinin 544'ü, bildirim numarası hücrelerinin 700'ü farklı.

Kök dosya metadata bakımından daha iyi bir başlangıç; finansal doğruluk sorunları ikisinde de var. [Çıktı kodu](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/scripts/parse_and_build_dataset.py#L970), kökü önce yazıp `data/` yazılamazsa devam edebiliyor. Bu, kopyaların farklı kalmasına yol açabilen bir yol; mevcut farkın nedenini tek başına ispatlamaz.

**Yapılacak:** tek kanonik çıktı; açık sürüm/üretim zamanı; kaynak dosya hash'leri; parser ve ortam sürümü. Güncel parser'da bulunan `kap_raporlanan_hbk_ytd` ve EPS ile ilgili alanlar mevcut 92 sütunlu çıktıda yok. Yeniden üretim doğrulanmalı. Bağımlılıklar/sürümler bir ortam dosyasında sabitlenmeli; tam veri indirme kontrolsüz tekrarlanmamalı.

### B. Ham kaynağa kadar giden büyüklük ve birim sorunları

| Kayıt | Kanıt | İşlem |
|---|---|---|
| KAREL 2012Q1 | [Ham XLS](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/data/kap_raw_xls/KAREL_2012_Q1.xls) işletme nakit akışı **115.282.692.945.205 TL**, yatırım nakit akışı **−477.891.329.452.055 TL**; toplam varlık **219.501.352 TL**. Sayılar BIFF hücrelerinde de var. | Özgün finansal rapor/PDF ile doğrula; yalnız parser hatası olarak sınıflandırma. YTD farkından etkilenen Q2'yi de incele. |
| THYAO 2015Q4 / 2016Q1 | Varlık **47.638 / 48.349 TL** görünüyor; komşu dönemlerle milyon katına yaklaşan fark. 2015Q4 çeyrek hasılatı **−21.593.390.038 TL** çıkıyor. | Raporlama ölçeğini ve dönem dönüşümünü özgün raporla doğrula. |
| TOASO 2013Q1 / 2014Q3 | Varlık **6.266.179 / 6.550.101 TL**; komşu dönemlerle yaklaşık bin kat fark. | Birim çarpanını özgün rapordan doğrula. |

THYAO ve TOASO ham başlıklarında da TL yazıyor. Başlığa bakarak birim tanımak bütün hataları çözmüyor. Bu dört satır güçlü ölçek şüphelisidir; otomatik `×1.000` / `×1.000.000` düzeltmesi önerilmiyor.

Denetim eşikleriyle **6 komşu dönem varlık sıçraması** (>20 kat veya <1/20), **9 nakit akışı hücresi** (mutlak çeyrek akışı / varlık >10) işaretlendi. Bunlar araştırma bayrağıdır; eşik aşımı tek başına hata kanıtı değildir. Bozuk bir dönem sonraki çeyrek farklarını, büyüme oranlarını ve gecikmeli girdileri de etkiler. Karantina yalnız tek satıra uygulanmamalı; türetme bağımlılıkları izlenmelidir.

### C. Finansal anlam ve türetme kuralları

- `hasılat + imzalı satış maliyeti − brüt kâr` kontrolü **27 YTD satırında 1 TL'yi aşıyor**: TUPRS 13, GSDDE 12, ALCTL 1, RYSAS 1. Bir TL eşiği tarama içindir; özgün birimin yuvarlama toleransı ayrıca hesaba katılmalı.
- GSDDE 2016Q1'de parser ticari faaliyet brüt kârını **−3,606 milyon TL** seçiyor; [ham dosyada](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/data/kap_raw_xls/GSDDE_2016_Q1.xls) toplam brüt kâr **−3,734 milyon TL**. Çok faaliyetli tabloya uygun eşleme gerekiyor. TUPRS/RYSAS örneklerinin bazıları ham kaynakta da uyumsuz; aynı neden varsayılmamalı.
- Dört çeyrek toplamı ile Q4 YTD, hasılatta **42**, net kârda **51 şirket-yılda** 1 TL'den fazla farklı; farkın %1'i aştığı sayılar **24 / 26**. Ayrı üç aylık sütunlar, restatement ve yuvarlama meşru fark yaratabilir. `quarter_method` ve veri sürümü olmadan otomatik hata/düzeltme kararı verilmemeli.
- [Net borç](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/scripts/parse_and_build_dataset.py#L876), eksik finansal borcu sıfırla dolduruyor; borcu eksik 17 satırda net borç yanlış yorumlanabilir. Eksik, sıfır demek değildir. Finansman gelir/gideri toplamı ve alt kalem toplamlarında da aynı ayrım korunmalı.
- Büyümelerde **4 QoQ, 6 YoY sonsuz değer** var. Eğitim öncesi sıfır payda ve sonlu sayı kontrolü gerekli; hedef eksikleri uydurulmamalı.
- Nakit akışı bölümünde [son sayısal satıra düşen yedek eşleme](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/scripts/parse_and_build_dataset.py#L636) her zaman toplamı seçmeyebilir. Ana ortaklık/net kâr ve toplam/ana ortaklık özkaynak alanlarının birbirine yedeklenmesi de raporlanan–türetilen ayrımını gerektirir.
- Güncel koddaki sermaye üzerinden hesaplanan EPS, ağırlıklı ortalama hisse sayısına dayalı gerçek EPS kabul edilmemeli. İlk demo EPS'ye bağlı olmamalı.
- Yatırım faaliyetlerinden toplam nakit akışı, tek başına yatırım harcaması (capex) değildir. FAVÖK için de amortisman/itfa gibi ek bileşenler gerekir; mevcut başlıkların varlığı bu hedeflerin hazır olduğu anlamına gelmez.

**Her finansal değerde gerekli iz:** `source_file`, bildirim kimliği, tablo/satır etiketi, özgün değer/birim, uygulanan çarpan, rapor sürümü, `available_at`, `quarter_method`, `is_derived`, `qa_flags`. Akışlar tek çeyrek; stoklar dönem sonu değeri olarak tutulmalı. YTD farkının iki kaynağı da saklanmalı ve aynı muhasebe/sürüm temelinde oldukları kontrol edilmeli.

### D. Yayın tarihi ile tutarın sürümü birlikte doğrulanmalı

`first_published_at` alanı her kayıtta ilk yayım anlamına gelmiyor. Örnek:

- **AKSEN 2018Q1:** CSV ve seçilen dosya bildirim numarası `748443`, tarih **2019-03-19 00:00:49**.
- [Katalogdaki](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/data/kap_fr_catalog_2010_2020.json) aynı çeyrek için en erken kayıt `683063`, tarih **2018-05-10 21:15:51**; ayrıca aynı akşam başka bildirimler var.
- [Parser](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/scripts/parse_and_build_dataset.py#L802), dosya adındaki bildirim kimliğinin tarihini tercih ediyor. Sonraki sürümün tutarına ilk sürümün tarihini vermek, o gün bilinmeyen bilgiyi geçmişe taşır.

Çözüm, tarih alanını tek başına erkene çekmek değildir. **Tutar, dosya sürümü ve gerçekten açıklanma zamanı eşleşmelidir.** İlk yayımlanan hedefi mi, sonradan düzeltilmiş hedefi mi tahmin ettiğimiz de etiket sözleşmesinde açık yazılmalı. İlk demo için ilk yayımlanan hedef öneriliyor.

Sadece tarih/lag uygunluğu kontrolünde, q−1/q−4 hasılatı yayımlanmış ve geçmiş varlığı pozitif aday sayısı kök CSV'de **1.142**, `data/` kopyasında **643**. Bu sayılar finansal kalite ve gerçek ilk sürüm denetiminden geçmiş eğitim örneği sayısı değildir. Kök dosyada **22 q−1 raporu**, hedef çeyrek sonundan sonra yayımlanmış görünüyor: `.shift(1)` tek başına zaman güvenliği sağlamıyor. CSV zamanlarında saat dilimi alanı yok; bu kontrol yerel KAP saati ve çeyrek sonu gün sonunu varsayıyor.

### E. Aynı dönem finansalları hazır model girdisi değil

Mevcut CSV bir şirket–dönem gözlem tablosu. Örneğin 2020Q2 hasılatı ve o hasılattan hesaplanan net kâr marjı aynı satırda bulunabilir; bu veri saklama açısından normaldir. Ancak **2020Q2 sonucu henüz yayımlanmadan tahmin edilirken bu iki değer girdi olamaz.**

Eğitim veri üreticisi ayrı kurulmalı: `target_period=q`, sabit `forecast_origin=t0`, yalnız `available_at <= t0` girdiler, hangi geçmiş dönemin/sürümün kullanıldığı ve hedef yayım zamanı. Ölçekleme için de hedef dönemin varlığı yerine o tarihte açıklanmış geçmiş pozitif varlık kullanılmalı.

### F. Makro/risk katmanı henüz yayın zamanı güvenli değil

[Aylık eşleme](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/scripts/parse_and_build_dataset.py#L905) çeyreğin son ayını kullanıyor; `available_at` veya tarihsel veri sürümü yok. Son ayın enflasyon/sanayi üretimi/endeks sonucu ayın son gününde otomatik olarak biliniyor sayılamaz.

- [GPR'nin resmî kaynağı](https://www.matteoiacoviello.com/gpr.htm) aylık güncellemenin ay başında yapıldığını, eski sürümlerin arşivlendiğini ve geçmiş değerlerin revize edilebildiğini açıklıyor. Güncel yöntem 2021'de değişmiş; bugünkü seriyle 2010–2020 analizi, o yıllarda fiilen mevcut endeksle test yapıldığını göstermiyor.
- [OFR'nin resmî kaynağı](https://www.financialresearch.gov/financial-stress-index/) verinin **iki iş günü önceye ait** olduğunu belirtiyor. Parser'ın [aynı gün ham FSI'yi ileri doldurması](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/scripts/parse_and_build_dataset.py#L939) bu gecikmeyi uygulamıyor. Ayrı ortalamada kullanılan iki satır kaydırma da otomatik olarak iki iş günü değil.
- Birleşik günlük tabloda **7.332 satırın 427'si hafta sonu**. FX/FSI takvimleri ayrı ele alınmalı. Çeyrek sonu anlık görüntülerinde 63 satırlık “90 gün” penceresi ortalama **79,7 takvim günü**, 60 satırlık FSI penceresi ortalama **52,7 dolu gözlem** içeriyor. Bu sayılar JSON'daki açık satır penceresi hesabıdır; istenen pencere tanımı ayrıca kararlaştırılmalı.
- `M03_Faiz_Orani` için indirilen `OECD/MEI/TUR.IRSTCI01.ST.M`, [yerel kaynak metadatasında](https://github.com/Toricicim/Bilanco_Tahmini/blob/91a7d0e/data/external/oecd_ir.json) **gecelik call money/interbank rate** olarak tanımlı. Değişken sözlüğündeki ticari kredi faiziyle aynı ölçü değil. Ya gerçek seri çekilmeli ya da ayrı proxy adıyla tanımlanmalı.
- GEPU/TÜFE/ÜFE/sanayi üretimi için yayım takvimi ve vintage ayrıca gerekli. Tek bir tahmini sabit gecikme kullanmak gerçek point-in-time veri oluşturmaz.

İlk finansal temel kıyasına bu katmanı yetiştirmek zorunlu değil. Sonraki deneyde yayın zamanı ve sürümü doğrulanan makro/riskler eklenerek katkıları ölçülmeli; tarihsel vintage bulunamayan deneyler açıkça **geriye dönük revize seri deneyi** diye etiketlenmeli.

## 3. Değişken listemizle uyum ve eksik katmanlar

| Aday aile | Mevcut durum | Sonraki işlem |
|---|---|---|
| F01–F14 finansal geçmiş | Ana tutarların çoğu ve bazı oranlar var | Kalite, yayın zamanı ve q−1/q−4 girdileri hazırlanmalı |
| M01–M06 makro | Sayısal değerler var | M03 ölçüsü, pencereler, yayın/vintage düzeltilmeli |
| R01/R02/R03 ve R04 | GPR, GEPU, OFR FSI, tehdit/eylem ayrımı var | Tarihsel kullanılabilirlik ve indeks sürümü doğrulanmalı |
| C01 sektör | Grup ve KAP etiketleri var | Döneme ait faaliyet/etiket olup olmadığı doğrulanmalı |
| X02/X03 | Faiz×borç ve FSI×kısa borç terimleri var | Aynı dönem borcu yerine t0'da bilinen borç kullanılmalı |
| F15–F20, M07/M08 | Bazı kısmi tutarlar dışında yeterli ayrıntı yok | Amortisman/capex, Ar-Ge, kontrat, FX pozisyonu; ilgili emtia/sektör göstergeleri |
| C02–C10, E01, kalan X aileleri | Şirket maruziyeti/olay bağlamı henüz yok | Faaliyet ve coğrafi gelir karması, ihracat, ithal girdi, enerji rolü, sipariş/ifa ve müşteri yoğunlaşması |

**Kod numarası tek başına eşleme değil:** sözlükte F01 “şirket ölçeği”, CSV'de `F01_hasilat_qoq_buyume`; sözlükte F07 “vergi”, CSV'de `F07_finansman_geliri`. Girdiler otomatik olarak yalnız ID önekinden bağlanmamalı. Açık bir sözlük–ham kolon–dönüşüm–birim eşleme tablosu gerekli. [Kanonik kayıt](degiskenler.json) bu incelemeyle otomatik `validated` yapılmadı.

“Aynı olay neden iki şirketi farklı etkiliyor?” sorusu için endeks + sektör etiketi tek başına yeterli temsil değil. İkinci aşamada öncelik: **yurt dışı gelir/ihracat payı, net döviz pozisyonu, enerji/emtia üretici–tüketici rolü, faaliyet karması ve uygun sektörlerde sipariş/ifa görünürlüğü**. Bunlar şirkete özel işaret ezberletmeden farklı gelir, maliyet ve nakit kanallarını temsil eder. Savaşta savunma hissesi yükselmesi, gelecek çeyrek muhasebe kârının artmasıyla aynı hedef değildir; yön önceden sabitlenmemeli.

## 4. İlk demo için somut deney

**Görev önerisi:** çeyrek sonu gün sonunda, henüz yayımlanmamış o çeyreğin ilk açıklanacak sonuçlarını tahmin et. Örneğin 30 Haziran'da Q2 hedeflenir; yalnız o tarihe kadar açıklanmış raporlar girdi olur. Üründeki farklı sorgu tarihleri sonraki görev tanımıdır.

| Karar | İlk demo |
|---|---|
| Hedefler | Temizlenmiş **tek çeyrek hasılat, tek çeyrek net kâr, toplam varlık, toplam özkaynak** |
| Model düzeni | Her hedef için şirketlerin birlikte kullanıldığı bir model; her şirkete ayrı 44 satırlık model değil |
| Girdiler | Bilinebilen q−1/q−4 tutar ve oranları, geçmiş pozitif varlık ölçeği, çeyrek, doğrulanmış sektör; eksikliği ve gözlem yaşı |
| Temel kıyas | Geçen yıl aynı çeyrek; son bilinen değer. Karşılaştırmalar aynı uygun gözlemlerde |
| ML | Önce Ridge, ardından sınırlı karmaşıklıkta Random Forest; küçük veri için iki anlaşılır başlangıç adayı |
| Deney sırası | E0 finansal geçmiş → E1 zaman güvenli makro/risk → E2 şirket maruziyetleri ve etkileşimler |
| Örnek tarih blokları | 2011–2016 eğitim, 2017–2018 doğrulama, 2019–2020 test |
| Zaman kontrolü | Aynı çeyrek tüm şirketleriyle aynı blokta; her fit anında eğitim/ayar etiketleri de açıklanmış olmalı; sonradan açıklanan etiketler çıkarılmalı |
| Dönüşümler | Eksik girdi doldurma ve ölçekleme yalnız eğitimde öğrenilir; eksik hedef doldurulmaz |
| Ölçüm | Kalem bazında MAE, geçmiş varlığa göre ölçeklenmiş hata, temel tahmine göre kazanım; şirket/sektör/çeyrek kırılımları |
| Sınırlar | Sıfır/negatif kâr nedeniyle MAPE ana metrik değil; yalnız 8 ortak test çeyreğinden geniş genelleme yapılmaz |

Tahminler önce özgün TL birimine döndürülmeli. Hasılat/varlık/özkaynak ve net kârın işaret/kapsam kuralları tanımlanmalı; dört kalemlik demo tam üç tablo muhasebe tutarlılığı sağladığını iddia etmemeli. Finansal tablo tutarlılığı daha fazla kalem çıktığında ayrıca sınanır.

İlk demoda Forma benzeri büyük Transformer veya 17 hedefli karmaşık sistem önerilmiyor. Bu bir başarı karşılaştırması değil; 30 şirket/44 ortak dönem ve mevcut veri sorunları dikkate alınarak seçilmiş başlangıç kapsamı. Dönüşümleri eğitim verisinde öğrenip testte aynı şekilde uygulama ilkesi için [resmî scikit-learn rehberi](https://scikit-learn.org/stable/common_pitfalls.html) kullanılabilir.

## 5. Başlama kapısı ve görev sırası

1. **Kanonik veri ve izlenebilirlik:** tek çıktı, dosya/hash/kod/ortam manifestosu; veri sözlüğü eşlemesi. Kopyalar sessizce farklı kalmamalı.
2. **Finansal kalite:** KAREL ve ölçek şüphelilerini raporla doğrula; etkilenen türevleri işaretle; toplam/alt toplam ve eksik–sıfır ayrımını düzelt. Kullanılacak hedef/özelliklerin doğrulanmamış değerlerini maskele.
3. **Sürüm ve yayın zamanı:** ilk rapor ve düzeltmeleri ayrı sakla; bilinmeyen zamanı uydurma; hedef sürümünü tanımla. PIT rekonstrüksiyonu yapılamayan kapsamı başarı iddiasından ayır.
4. **Eğitim tablosu:** q/t0, geçmiş kaynak dönemleri, özellik/etiket yayın zamanları ve kalite maskeleri; q−1/q−4 ve ileriye bakma kontrolleri. Sıfır payda/sonsuz değer kontrolü.
5. **Dört hedefli kıyas ve ML:** tarih bloklarını sabitle, test dönemine bakarak veri temizliği/parametre seçimi yapma; sonuçları temel tahminle aynı satırlarda karşılaştır.
6. **Genişletme:** yayın zamanı düzeltilmiş üç risk endeksi, makrolar ve şirket profilleri; sonra güvenilir nakit akışları/diğer hedefler ve yakın dönemler.

Bir–üç tamamlanmadan altyapı yazılabilir; mevcut veriden güvenilir doğruluk skoru üretildiği söylenemez. Makrosuz ilk modelin de finansal rapor sürümü/yayın zamanı koşullarını sağlaması gerekir. Düzeltme çalışması, yeni eğitim tablosu ve model eğitimi bu denetimde yapılmadı.

## 6. Denetimi yeniden çalıştırma

```bash
python3 scripts/audit_dataset.py
# Ayrı bir JSON raporu kaydetmek için:
python3 scripts/audit_dataset.py --output /tmp/bilanco-veri-denetimi.json
```

Betik Python standart kütüphanesini kullanır; veri indirmez, CSV/XLS değiştirmez, model eğitmez. Panel/doluluk, iki kopya farkı, sonlu sayı, finansal eşitlik, büyüklük sıçraması, çeyrek–YTD uzlaşması, tarih uygunluğu ve günlük pencere kontrollerini tekrarlar. Ham XLS hücre incelemesi, KAP katalog örneğinin anlamı, parser satır eşlemesi ve resmî yayın kurallarının doğrulanması ayrıca yapılan incelemedir; bu betik bunların yerine geçmez.

### 🌐 Community Wisdom

Bulunan iki ilgili DEV yazısı aynı veri sağlayıcısının yazarından; bağımsız görüş birliği sayılmamalı. Yorum uç noktaları iki yazı için boş sonuç verdi. Teknik kararların ana kanıtı yerel kaynak/kod incelemesi ve yukarıdaki resmî kaynaklardır.

- 🗂️ [How to Build a Point-in-Time Fundamentals Database from SEC EDGAR (and When Not To)](https://dev.to/tradevodata/how-to-build-a-point-in-time-fundamentals-database-from-sec-edgar-and-when-not-to-2gn6) [@tradevodata](https://dev.to/tradevodata) — Yazar kendi revizyon algılama hatasını da anlatıyor; burada ilk ve düzeltilmiş tutarları ayrı saklama gereğini somutlaştırıyor. 🔗 [Read Full Discussion on DEV](https://dev.to/tradevodata/how-to-build-a-point-in-time-fundamentals-database-from-sec-edgar-and-when-not-to-2gn6)
- 🔍 [How to Detect Lookahead Bias in a Backtest: A Practical Checklist](https://dev.to/tradevodata/how-to-detect-lookahead-bias-in-a-backtest-a-practical-checklist-2cb6) [@tradevodata](https://dev.to/tradevodata) — Dönem sonunu yayın zamanı sanan eşlemeleri denetleme önerisi yararlı; tek başına sabit gecikme testi doğruluk kanıtı sayılmamalı. 🔗 [Read Full Discussion on DEV](https://dev.to/tradevodata/how-to-detect-lookahead-bias-in-a-backtest-a-practical-checklist-2cb6)

**Sonraki iş:** önce kanonik, finansal kalitesi ve tarihsel kullanılabilirliği doğrulanmış eğitim tablosu; ardından dört kalemli finansal temel kıyas ve küçük ML demosu.
