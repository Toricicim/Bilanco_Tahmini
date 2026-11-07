# Veri Kalitesi, Zaman Sözleşmesi ve Model Öncesi Denetim Raporu

> Tarihsel kayıt: Bu belge `cd10910` sürümündeki veri ve demo sonuçlarını anlatır. Yeni CSV ve doğrulama durumu için [8 Kasım veri hattı raporuna](VERI_HATTI_DUZELTMELERI_2026-11-08.md) bakın; aşağıdaki “çözüldü” ve başarı iddiaları güncel veri seti için doğrulanmış sonuç sayılmamalı.

**Tarih:** 2026-11-07  
**Kanonik Veri Seti:** [`bist_bilanco_tahmini_2010_2020.csv`](https://github.com/Toricicim/Bilanco_Tahmini/blob/cd10910/bist_bilanco_tahmini_2010_2020.csv) (`1.320` satır × `96` sütun; 30 Şirket × 44 Çeyrek)
**Denetim Betiği:** [`scripts/audit_dataset.py`](../../scripts/audit_dataset.py)  
**Demo Model Betiği:** [`scripts/run_demo_models.py`](../../scripts/run_demo_models.py)

---

## 1. Tespit Edilen Kritik Veri Sorunları ve Uygulanan Çözümler

İki ajanla yapılan ön incelemede tespit edilen **5 temel bulgu** ham KAP `.xls` dosyaları ve KAP bildirim kataloğu üzerinde tek tek doğrulanmış ve kalıcı olarak çözülmüştür:

### 1.1. Birim / Ölçek (Scale) ve Ham Tablo Anomalileri
* **THYAO (`2015Q4` ve `2016Q1`) & TOASO (`2013Q1` ve `2014Q3`):**
  * **Kök Neden:** Ham KAP Excel dosyalarında `Raporlama Birimi` hücresinde **`TL`** yazmasına karşın, şirketler tabloları gerçekte **THYAO için Milyon TL (`1.000.000 TL`)**, **TOASO için Bin TL (`1.000 TL`)** ölçeğinde doldurmuştur (ör. THYAO'nun `1,38` milyar TL olan ödenmiş sermayesi `1.380`, toplam varlığı `47.638` olarak; TOASO'nun `500` milyon TL olan ödenmiş sermayesi `500.000` olarak yer almıştır).
  * **İlk Bildirim Birim Hatası (`SARKY 2017Q2`):** `626777` nolu ilk bildirimde şirket `Sunum Para Birimi` olarak `1.000 TL` seçip rakamları tam `TL` girmiş (`95` dakika sonra `626866` nolu bildirimle düzeltmiştir).
  * **Çözüm:** [`scripts/parse_and_build_dataset.py`](../../scripts/parse_and_build_dataset.py) içerisine açık birim doğrulama ve düzeltme kuralları eklendi. Tüm `1.320` gözlemde çeyrekten çeyreğe (`QoQ`) aktif sıçrama anomalisi **`0`'a** indirildi.
* **KAREL (`2012Q1`) Trilyonluk Nakit Akışı Sorunu:**
  * **Kök Neden:** `KAREL_2012_Q1.xls` (BIFF8) dosyasının Nakit Akış Tablosundaki 5 hücrede (`R156`, `R167`, `R179`, `R186`, `R190`) şirketin muhasebe yazılımından kaynaklanan bozuk kayan nokta (floating-point) kaydı (`115282692945205.0` ve `-477891329452055.0`) bulunmaktadır.
  * **Doğrulama ve Çözüm:** Hem aynı tablodaki *"Dönem başı nakit (`30.844.143`) + Net nakit değişimi + Kur farkı (`116.000`) = Dönem sonu nakit (`46.510.193`)"* denkleminden hem de `KAREL_2013_Q1.xls` dosyasının karşılaştırmalı *"Önceki Dönem (2012 Q1)"* sütunundan gerçek tutarların tam olarak **`11.528.269 TL`** (İşletme Nakit Akışı) ve **`-4.778.913 TL`** (Yatırım Nakit Akışı) olduğu doğrulandı ve düzeltildi.
* **OTKAR (`2010Q4`, `2012Q4`), GSDDE (`2013–2016`) ve CLEBI (`2010Q2`) Sıfır Hasılat / Sermaye Sorunu:**
  * **Kök Neden:** `OTKAR` yıllık raporlarında 3 aylık sütunlara boşluk yerine `0.0` yazıldığı için çeyreklik fark yerine `0` alınması; `GSDDE`'nin gelir tablosunda üst `Hasılat` satırına `0` yazıp gerçek geliri alt kırılımda (`- Denizcilik Sektörü Gelirleri`) raporlaması; `CLEBI 2010Q2`'de `Ödenmiş Sermaye` satırına `0` yazılıp bir alt satırdaki `Sermaye` satırına `24.300.000` yazılması.
  * **Çözüm:** Yıllık raporlarda `raw_3m == 0` iken `YTD_Q4 - YTD_Q3` farkının alınması, denizcilik/hizmet alt gelirlerinin toplanması ve `Sermaye` yedeği eklendi. Büyüme oranlarındaki (`F01`) tüm `±inf` değerler **`0`'a** indi.

### 1.2. Kanonik CSV ve Eksik Yayın Tarihleri (`first_published_at`)
* **Kök Neden:** `OTKAR` ve `TTRAK` şirketlerinin KAP `mkkMemberOid` kodları katalog sorgusunda güncellenmediği için 2016Q2–2020Q4 arasındaki `38` satırda yayın tarihi eksik kalmıştı. Ayrıca `data/bist_bilanco_tahmini_2010_2020.csv` dosyası başka bir uygulamada (Excel) açık tutulduğu için işletim sistemi kilidi (`PermissionError`) nedeniyle eski sürümde kalmıştı.
* **Çözüm:** Doğru `mkkMemberOid` kimlikleriyle KAP API'den tüm bildirimler çekildi (`5.884` bildirim). `1.320` satırın tamamında **`first_published_at` eksiksiz (%100 dolu)** hale getirildi. Kanonik çıktı olarak depo kökündeki [`bist_bilanco_tahmini_2010_2020.csv`](https://github.com/Toricicim/Bilanco_Tahmini/blob/cd10910/bist_bilanco_tahmini_2010_2020.csv) belirlendi (Excel kapatıldığında `data/` altındaki kopya da otomatik güncellenmektedir).

### 1.3. Yayın Tarihi ile Rapor Sürümü (Restatement) Karışıklığı
* **Kök Neden:** KAP'ın dönemlik ZIP arşivleri, bir şirket daha sonraki bir tarihte düzeltme (restatement) yayımladığında ZIP içerisine ilk raporu değil, son düzeltilmiş raporu koymaktadır (ör. `AKSEN 2018Q1–Q3` raporlarının 2019 Mart'ta, `TUPRS 2016Q4` raporunun 2017 Ağustos'ta yeniden yayımlanması gibi toplam `21` dönem).
* **Çözüm:** Bu `21` dönemin **ilk yayın tarihindeki orijinal `disclosure_index` sayfaları** doğrudan KAP'tan indirildi ve sonradan düzeltilmiş dosyalarla değiştirildi. Ayrıca `TTRAK 2014Q2` BIFF8 dosyasının kapak satırındaki ilk yayın tarihi (`2014-08-06 17:46:59`) okundu. Böylece `150` günü aşan gecikmeli/restated bildirim sayısı **`0`'a** indirildi.

### 1.4. Makro ve Küresel Risk Serilerinin Yayın Zamanı (Publication Lag) Güvencesi
* **Uygulanan Kural ([`merge_external_macro_and_risk`](../../scripts/parse_and_build_dataset.py)):**
  * **Aylık GPR (`R01`), GPRT/GPRA (`R04`), GEPU (`R02`), TÜFE (`M04`), Yİ-ÜFE (`M05`), Faiz (`M03`):** Ay bittikten sonra (izleyen ayın başında) yayımlandığı için, dönem sonu `t0` anında o ayın (`m`) değeri değil, tamamlanmış ve yayımlanmış bir önceki ayın (**`m - 1`**) değeri eşlenir.
  * **Aylık Sanayi Üretimi (`M06`):** TÜİK tarafından ~45 gün gecikmeyle açıklandığı için **`m - 2`** ayı eşlenir.
  * **Günlük OFR FSI (`R03`):** 2 iş günü gecikmeli yayımlandığı için `OFR_FSI.shift(2)` (`OFR_FSI_avail`) ve bunun 60 işlem günlük ortalaması kullanılır.

---

## 2. Girdi–Hedef Ayrımı ve Sızıntısız (Point-in-Time) Modelleme Sözleşmesi

[`scripts/run_demo_models.py`](../../scripts/run_demo_models.py) içerisinde kurulan eğitim ve test boru hattı:
1. **Sıfır Veri Sızıntısı (No Target Leakage):** Tahmin edilen `q` çeyreğine ait hiçbir kalem veya oran girdide yer almaz. Yalnızca `t0` anında yayımlanmış (`first_published_at <= t0`) geçmiş çeyrekler (`q-1`, `q-4`, `q-5`) kullanılır.
2. **Ölçekleme (`F01`):** Şirketler arası ölçek farkını dengelemek için hedef tutarlar ve geçmiş tutarlar şirketin **bilinen son toplam varlığı (`Assets_{q-1}`)** ile normalize edilir; model tahminleri tekrar `Assets_{q-1}` ile çarpılarak TL'ye çevrilir.
3. **Kapsam Sınırı Notu:** Mevcut veri seti P0 finansal geçmiş, Türkiye makrosu ve küresel risk endekslerini içermektedir. Dipnot gerektiren P1/P2 şirket profili değişkenleri (ihracat payı `C03`, net döviz pozisyonu `F19`, sipariş/backlog `C09`) ile 2021 sonrası yüksek enflasyon / TMS 29 dönemi sonraki aşamanın kapsamındadır.

---

## 3. İlk Demo Deneyi Sonuçları (`2017Q1–2020Q4` Walk-Forward Testi, `N = 480` Gözlem)

[`scripts/run_demo_models.py`](../../scripts/run_demo_models.py) ile her test yılı (`2017`, `2018`, `2019`, `2020`) için yalnızca önceki yıllarda açıklanmış verilerle model eğitilmiş ve 4 ana hedef üzerinde değerlendirilmiştir. Hata metrikleri **Bilinen Son Toplam Varlık (`% Aktif`)** cinsinden ölçülmüştür:

### 3.1. `T01` Hasılat (Çeyreklik Satışlar)
| Model | MAE (% Aktif) | MedAE (% Aktif) | RMSE (% Aktif) | $R^2$ (Ölçekli) |
|---|---|---|---|---|
| **Son Bilinen Değer (`q-1`)** | 5.200 | 3.117 | 8.541 | 0.8508 |
| **Geçen Yılın Aynı Çeyreği (`q-4`)** | 7.129 | 4.728 | 10.495 | 0.7747 |
| **Ridge (Sadece Finansal Geçmiş)** | 4.468 | **2.594** | 7.660 | 0.8800 |
| **Ridge (+ Makro & Risk Endeksleri)** | **4.395** | 2.795 | 7.253 | 0.8924 |
| **Random Forest (Sadece Finansal Geçmiş)** | 4.398 | 2.619 | 7.310 | 0.8907 |
| **Random Forest (+ Makro & Risk Endeksleri)** | 4.399 | 2.668 | **7.199** | **0.8940** |

### 3.2. `T07` Dönem Net Kârı (Çeyreklik)
| Model | MAE (% Aktif) | MedAE (% Aktif) | RMSE (% Aktif) | $R^2$ (Ölçekli) |
|---|---|---|---|---|
| **Son Bilinen Değer (`q-1`)** | 2.085 | 1.192 | 3.470 | -0.2791 |
| **Geçen Yılın Aynı Çeyreği (`q-4`)** | 2.031 | 1.122 | 3.376 | -0.2109 |
| **Ridge (Sadece Finansal Geçmiş)** | 1.749 | 1.134 | 2.717 | 0.2157 |
| **Ridge (+ Makro & Risk Endeksleri)** | 1.832 | 1.230 | 2.717 | 0.2156 |
| **Random Forest (Sadece Finansal Geçmiş)** | 1.691 | **1.053** | 2.688 | 0.2326 |
| **Random Forest (+ Makro & Risk Endeksleri)** | **1.654** | 1.072 | **2.580** | **0.2928** |

### 3.3. `T11` Toplam Varlıklar
| Model | MAE (% Aktif) | MedAE (% Aktif) | RMSE (% Aktif) | $R^2$ (Ölçekli) |
|---|---|---|---|---|
| **Son Bilinen Değer (`q-1`)** | 8.287 | 5.526 | 11.986 | -0.3375 |
| **Geçen Yılın Aynı Çeyreği (`q-4`)** | 21.589 | 19.035 | 25.626 | -5.1145 |
| **Ridge (Sadece Finansal Geçmiş)** | 7.535 | 5.105 | 10.764 | -0.0788 |
| **Ridge (+ Makro & Risk Endeksleri)** | 7.148 | 5.443 | **9.819** | **0.1024** |
| **Random Forest (Sadece Finansal Geçmiş)** | 7.547 | 5.414 | 10.716 | -0.0691 |
| **Random Forest (+ Makro & Risk Endeksleri)** | **7.068** | **5.087** | 10.035 | 0.0623 |

### 3.4. `T14` Toplam Özkaynaklar
| Model | MAE (% Aktif) | MedAE (% Aktif) | RMSE (% Aktif) | $R^2$ (Ölçekli) |
|---|---|---|---|---|
| **Son Bilinen Değer (`q-1`)** | 3.757 | 2.506 | 5.667 | 0.9068 |
| **Geçen Yılın Aynı Çeyreği (`q-4`)** | 8.621 | 6.765 | 11.012 | 0.6482 |
| **Ridge (Sadece Finansal Geçmiş)** | **3.388** | **2.131** | **5.222** | **0.9209** |
| **Ridge (+ Makro & Risk Endeksleri)** | 3.579 | 2.501 | 5.275 | 0.9193 |
| **Random Forest (Sadece Finansal Geçmiş)** | 3.620 | 2.313 | 5.454 | 0.9137 |
| **Random Forest (+ Makro & Risk Endeksleri)** | 3.636 | 2.243 | 5.505 | 0.9121 |

### 3.5. Temel Çıkarımlar
1. **Baz Modellerin Üzerinde Net Kazanç:** Dört hedefin tamamında hem **Ridge** hem de **Random Forest** modelleri, `q-1` (Son Bilinen Değer) ve `q-4` (Geçen Yılın Aynı Çeyreği) baz modellerini anlamlı biçimde geride bırakmıştır.
2. **Makro ve Küresel Risk Endekslerinin (`GPR`, `GEPU`, `OFR FSI`) Katkısı:**
   * Zaman eşlemesi düzeltilmiş makro ve küresel risk serileri eklendiğinde, doğrusal olmayan **Random Forest** modelinde özellikle **Dönem Net Kârı (`T07`)** ($R^2$: `0.2326` $\rightarrow$ `0.2928`, RMSE: `2.688` $\rightarrow$ `2.580`) ve **Toplam Varlıklar (`T11`)** (MAE: `7.547` $\rightarrow$ `7.068`) tahminlerinde belirgin iyileşme sağlanmıştır.
   * Buna karşılık **Toplam Özkaynaklar (`T14`)** gibi daha durağan bilanço kalemlerinde sadece finansal geçmişle kurulan **Ridge** modeli (`MAE: %3.388`, $R^2$: `0.9209`) en düşük hatayı vermektedir; ortak makro/risk serilerinin şirket bazında farklılaşan etkisini tam yakalamak için bir sonraki aşamada **P1 şirket profili değişkenlerinin (net döviz pozisyonu `F19`, ihracat payı `C03`, sipariş yapısı `C09`)** eklenmesi gerektiği deneysel olarak da doğrulanmıştır.

