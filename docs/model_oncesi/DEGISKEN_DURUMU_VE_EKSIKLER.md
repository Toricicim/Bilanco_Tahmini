# Değişken Eşleme, Kullanım ve Kapsam Durumu

Bu belge, yetkili değişken sözlüğü olan [degiskenler.json](degiskenler.json) ([DEGISKEN_LISTESI.md](DEGISKEN_LISTESI.md)) içindeki **17 hedef** ve **51 girdi ailesi (26 P0, 19 P1, 6 P2)** ile kanonik veri tablomuz [data/bist_bilanco_tahmini_2010_2020.csv](../../data/bist_bilanco_tahmini_2010_2020.csv) (**1.320 satır × 110 sütun**) ve ilk deney betiği [scripts/run_demo_models.py](../../scripts/run_demo_models.py) arasındaki birebir eşlemeyi tutar.

> **Kural:** Yeni bir değişken/sütun CSV'ye eklendiğinde, çıkarıldığında, adı değiştiğinde veya model deneyine dahil edildiğinde [degiskenler.json](degiskenler.json), [DEGISKEN_LISTESI.md](DEGISKEN_LISTESI.md) (`scripts/render_feature_list.py`) ile birlikte **bu dosya da güncellenmelidir**.

---

## 1. Yönetici Özeti (Sayısal Dağılım)

| Kategori | Sözlükteki Toplam | CSV'de Karşılığı Olan | CSV'de Henüz Olmayan (Eksik) | İlk Demo Betiğinde (`run_demo_models.py`) Kullanılan |
|---|---|---|---|---|
| **Hedefler (`T01`–`T17`)** | **17** | **17 / 17** (Hem YTD hem çeyrek akış/bakiye) | **0** | **4** (`T01`, `T07`, `T11`, `T14` hedef olarak; `T01`, `T07`, `T11`, `T14` geçmiş gecikmeleri girdi olarak) |
| **P0 Girdi Aileleri** | **26** | **26 / 26** (`M03` bankalararası faiz vekiliyle) | **0** | **21 / 26** (5 P0 ailesi CSV'de var ama ilk demo betiğinde girdi listesine eklenmedi) |
| **P1 Girdi Aileleri** | **19** | **1 / 19** (`R04`: `R04_GPRT`, `R04_GPRA`; ayrıca `F15` için kısmi `duran_varliklar`) | **18** (Dipnot, segment, ihracat, CAPEX/amortisman, emtia, sektörel talep ve etkileşimler) | **0 / 19** |
| **P2 Girdi Aileleri** | **6** | **0 / 6** | **6** (Borç vade/korunma detayı, müşteri/tedarik yoğunlaşması, sözleşme fiyatlama, olay bağlamı) | **0 / 6** |
| **Sözlük Dışı / Ekstra Sütunlar** | — | **38 sütun** (24 kimlik/zaman/kalite metadatası + 14 ek finansal alt kalem, türev ve HBK sütunu) | — | `sector_group`, `quarter`, `period_end_date`, `available_at` |

---

## 2. Önemli Önek (Prefix) ve İsimlendirme Uyarıları

CSV'deki bazı sütun adlarının başındaki `Fxx` önekleri, [degiskenler.json](degiskenler.json) sözlüğündeki `id` numaralarıyla **birebir aynı değildir** ([AGENTS.md](../../AGENTS.md) P0-C uyarısı):

1. **Sözlük `F01` (Şirket ölçeği) ≠ CSV `F01_*` (Hasılat büyümesi):**
   * Sözlükte `F01` "Şirket ölçeği (son bilinen toplam varlık)" iken, CSV'de `F01_hasilat_qoq_buyume` ve `F01_hasilat_yoy_buyume` sütunları aslında sözlükteki **`F02` (Hasılat geçmişi)** ailesinin büyüme türevleridir. Şirket ölçeği (`F01`), `T11_toplam_varliklar` sütununun geçmiş (`q-1`) değerinden üretilir.
2. **Sözlük `F07` (Vergi gideri/geliri) ≠ CSV `F07_*` (Finansman geliri ve net finansman):**
   * Sözlükte `F07` "Vergi gideri/geliri" ailesidir ve CSV'deki karşılığı `T06_vergi_gideri_geliri_ytd` / `T06_vergi_gideri_geliri_ceyrek` sütunlarının geçmiş değerleridir.
   * CSV'deki `F07_finansman_geliri_ytd`, `F07_finansman_geliri_ceyrek`, `F07_net_finansman_ytd`, `F07_net_finansman_ceyrek` sütunları ise sözlükteki **`F08` (Finansman ve faiz giderleri)** ailesinin yardımcı/ekstra bileşenleridir.
3. **CSV'deki Eşzamanlı Etkileşim Sütunları (`X02_*`, `X03_*`):**
   * CSV'deki `X02_faiz_degisimi_x_finansal_borc_aktif` ve `X03_ofr_fsi_x_kisa_borc_aktif` sütunları **aynı satırın (`q` çeyreğinin)** borç oranlarıyla çarpılmıştır. Tahmin anında (`t0`) hedef çeyreğin bilançosu henüz açıklanmadığı için modelde doğrudan bu iki CSV sütunu **kullanılmaz**; bunun yerine `q-1` borç oranlarıyla çarpılan `X02_pit` ve `X03_pit` kullanılır.

---

## 3. Hedef Değişkenlerin (`T01`–`T17`) Durumu

17 hedefin tamamı CSV'de mevcuttur. Akış kalemleri (gelir tablosu ve nakit akışı) hem kümülatif (`_ytd`) hem tek çeyrek (`_ceyrek`) olarak tutulur; model hedefi tek çeyrek (`_ceyrek`) ve dönem sonu bilanço bakiyeleridir.

| Sözlük ID | Hedef Tanımı | Tür | CSV Hedef Sütunu | CSV YTD Sütunu | Boşluk (`NaN` / 1.320) | Şu Anki Kullanım Durumu |
|---|---|---|---|---|---|---|
| **T01** | Hasılat | Akış | `T01_hasilat_ceyrek` | `T01_hasilat_ytd` | `0 / 1320` | **Aktif (Öncelikli 4 Hedeften 1'i)** |
| **T02** | Satışların maliyeti | Akış | `T02_satislarin_maliyeti_ceyrek` | `T02_satislarin_maliyeti_ytd` | `1 / 1320` (YTD: `1`) | CSV'de hazır; ilk 4 hedef sonrası sırada |
| **T03** | Brüt kâr | Türetilmiş akış | `T03_brut_kar_ceyrek` | `T03_brut_kar_ytd` | `0 / 1320` | CSV'de hazır (76 karma kapsam bayrağına dikkat) |
| **T04** | Esas faaliyet kârı | Akış | `T04_esas_faaliyet_kari_ceyrek` | `T04_esas_faaliyet_kari_ytd` | `1 / 1320` (YTD: `1`) | CSV'de hazır |
| **T05** | Finansman gideri | Akış | `T05_finansman_gideri_ceyrek` | `T05_finansman_gideri_ytd` | `16 / 1320` (YTD: `11`) | CSV'de hazır |
| **T06** | Vergi gideri/geliri | Akış | `T06_vergi_gideri_geliri_ceyrek` | `T06_vergi_gideri_geliri_ytd` | `0 / 1320` | CSV'de hazır |
| **T07** | Dönem net kârı | Akış | `T07_donem_net_kari_ceyrek` | `T07_donem_net_kari_ytd` | `0 / 1320` | **Aktif (Öncelikli 4 Hedeften 1'i)** |
| **T08** | Nakit ve nakit benzerleri | Bakiye | `T08_nakit_ve_nakit_benzerleri` | — | `0 / 1320` | CSV'de hazır |
| **T09** | Ticari alacak | Bakiye | `T09_ticari_alacaklar` | — | `750 / 1320` | Uzun vadeli alacak çoğu raporda ayrı olmadığı için toplam `NaN`; kısa vadeli (`F10_kisa_...`, `129` eksik) ayrı kullanılabilir |
| **T10** | Stok | Bakiye | `T10_stoklar` | — | `27 / 1320` | CSV'de hazır |
| **T11** | Toplam varlık | Bakiye | `T11_toplam_varliklar` | — | `0 / 1320` | **Aktif (Öncelikli 4 Hedeften 1'i + Ölçekleyici)** |
| **T12** | Finansal borç | Bakiye | `T12_finansal_borclar` | — | `139 / 1320` | Alt bileşen eksikliğinde `NaN`; kısa vadeli (`23` eksik) ayrı korunuyor |
| **T13** | Toplam yükümlülük | Bakiye | `T13_toplam_yukumlulukler` | — | `0 / 1320` | CSV'de hazır |
| **T14** | Toplam özkaynak | Bakiye | `T14_toplam_ozkaynaklar` | — | `0 / 1320` | **Aktif (Öncelikli 4 Hedeften 1'i)** |
| **T15** | İşletme nakit akışı | Akış | `T15_isletme_nakit_akisi_ceyrek` | `T15_isletme_nakit_akisi_ytd` | `2 / 1320` (YTD: `1`) | CSV'de hazır |
| **T16** | Yatırım nakit akışı | Akış | `T16_yatirim_nakit_akisi_ceyrek` | `T16_yatirim_nakit_akisi_ytd` | `10 / 1320` (YTD: `5`) | CSV'de hazır |
| **T17** | Finansman nakit akışı | Akış | `T17_finansman_nakit_akisi_ceyrek` | `T17_finansman_nakit_akisi_ytd` | `11 / 1320` (YTD: `8`) | CSV'de hazır |

---

## 4. P0 Girdi Aileleri: Kullanılanlar ve CSV'de Olup Henüz Modele Verilmeyenler (26 Aile)

26 P0 ailesinin **tamamı** CSV'de ham veya türetilmiş sütun olarak mevcuttur.

### A. Hem CSV'de Olan Hem İlk Demo Betiğinde (`run_demo_models.py`) Aktif Kullanılanlar (21 P0 Ailesi)

| Sözlük ID | Aile Adı | CSV'deki Kaynak Sütun(lar) | Boşluk (`/1320`) | Demo Modelde (`run_demo_models.py`) Nasıl Kullanılıyor? |
|---|---|---|---|---|
| **F01** | Şirket ölçeği | `T11_toplam_varliklar` (geçmiş `q-1` / `q-2`) | `0` | `known_scale_assets` (hedef/girdi normalizasyonu) ve `log_known_assets` |
| **F02** | Hasılat geçmişi | `T01_hasilat_ceyrek`, `F01_hasilat_qoq_buyume` (`30`), `F01_hasilat_yoy_buyume` (`120`) | `0` (`T01`) | `T01_hasilat_ceyrek_q1_scaled`, `_q4_scaled`, `_yoy_diff_scaled` |
| **F03** | Satış maliyeti ve brüt marj | `T02_satislarin_maliyeti_ceyrek` (`1`), `T03_brut_kar_ceyrek` (`0`), `F03_brut_kar_marji` (`84`) | `84` (marj) | `F03_brut_kar_marji_q1` (Not: `T02` maliyetin kendisi henüz modele verilmedi) |
| **F04** | Faaliyet kârı ve marjı | `T04_esas_faaliyet_kari_ceyrek` (`1`), `F04_esas_faaliyet_marji` (`1`) | `1` | `F04_esas_faaliyet_marji_q1` |
| **F05** | Dönem net kârı | `T07_donem_net_kari_ceyrek` (`0`), `F05_net_kar_marji` (`0`) | `0` | `T07_donem_net_kari_ceyrek_q1_scaled`, `_q4_scaled`, `_yoy_diff_scaled`, `F05_net_kar_marji_q1` |
| **F06** | İşletme nakit akışı ve tahakkuk | `T15_isletme_nakit_akisi_ceyrek` (`2`), `F06_cfo_aktif_orani` (`2`), `F06_tahakkuk_aktif_orani` (`2`) | `2` | `F06_cfo_aktif_orani_q1` (Not: `F06_tahakkuk_aktif_orani` CSV'de var ama betikte henüz ekli değil) |
| **F09** | Nakit ve nakit benzerleri | `T08_nakit_ve_nakit_benzerleri` (`0`), `F09_nakit_aktif_orani` (`0`) | `0` | `F09_nakit_aktif_orani_q1` |
| **F13** | Finansal borç ve vade dağılımı | `F13_kisa_vadeli_finansal_borclar` (`23`), `F13_uzun_vadeli_finansal_borclar` (`133`), `T12_finansal_borclar` (`139`), `F13_finansal_borc_aktif_orani` (`139`), `F13_kisa_finansal_borc_aktif_orani` (`23`) | `23`–`139` | `F13_finansal_borc_aktif_orani_q1` ve `X02_pit` / `X03_pit` içinde |
| **F14** | Yükümlülük ve özkaynak | `T13_toplam_yukumlulukler` (`0`), `T14_toplam_ozkaynaklar` (`0`), `F14_ozkaynak_aktif_orani` (`0`) | `0` | `T14_toplam_ozkaynaklar_q1_scaled`, `_q4_scaled`, `_yoy_diff_scaled`, `F14_ozkaynak_aktif_orani_q1` |
| **M01** | USD/TL değişimi | `M01_USDTRY_90g_degisim_pct` (`0`), `M01_USDTRY_seviye` (`0`) | `0` | `M01_USDTRY_90g_degisim_pct` (90 takvim günü değişimi) |
| **M02** | EUR/TL değişimi | `M02_EURTRY_90g_degisim_pct` (`0`), `M02_EURTRY_seviye` (`0`) | `0` | `M02_EURTRY_90g_degisim_pct` (90 takvim günü değişimi) |
| **M03** | Ticari kredi faizi *(Vekil)* | `M03_Faiz_Orani` (`0`), `M03_Faiz_3Aylik_Degisim` (`0`) | `0` | Her ikisi de kullanılıyor (**Uyarı:** Mevcut seri OECD gecelik bankalararası faiz vekilidir, ticari kredi faizi değildir) |
| **M04** | TÜFE | `M04_TUFE_YoY` | `0` | `M04_TUFE_YoY` (1 ay gecikmeli yıllık değişim) |
| **M05** | Yİ-ÜFE | `M05_YIUFE_YoY` | `0` | `M05_YIUFE_YoY` (1 ay gecikmeli yıllık değişim) |
| **M06** | Sanayi üretimi | `M06_SanayiUretimi_YoY` | `30` (2010Q1) | `M06_SanayiUretimi_YoY` (2 ay gecikmeli yıllık değişim) |
| **R01** | GPR: jeopolitik risk | `R01_GPR` | `0` | `R01_GPR` (1 ay gecikmeli aylık küresel endeks) |
| **R02** | GEPU: ekonomik politika belirsizliği | `R02_GEPU_ppp` | `0` | `R02_GEPU_ppp` (1 ay gecikmeli PPP ağırlıklı endeks) |
| **R03** | OFR FSI: finansal stres | `R03_OFR_FSI` (`0`), `R03_OFR_FSI_60d_mean` (`0`) | `0` | Her ikisi de kullanılıyor (2 ABD iş günü gecikmeli, 60 gerçek gözlem ortalaması) |
| **C01** | Tarihsel sektör ve faaliyet kategorisi | `sector_group` (`0`), `C01_kap_main_sector` (`0`), `C01_kap_sub_sector` (`0`) | `0` | `sector_group` one-hot (`sec_*`) kukla değişkenleri olarak kullanılıyor |
| **X02** | Faiz × finansal borçluluk | `X02_faiz_degisimi_x_finansal_borc_aktif` (`139`) | `139` | Betikte sızıntısız `X02_pit = M03_Faiz_3Aylik_Degisim * F13_finansal_borc_aktif_orani_q1` olarak üretiliyor |
| **X03** | Finansal stres × kısa vadeli borç | `X03_ofr_fsi_x_kisa_borc_aktif` (`23`) | `23` | Betikte sızıntısız `X03_pit = R03_OFR_FSI_60d_mean * F13_kisa_finansal_borc_aktif_orani_q1` olarak üretiliyor |

*(Not: Yukarıdaki listede 21 P0 ailesi yer alır; aşağıda CSV'de olup henüz demo modelde kullanılmayan 5 P0 ailesi listelenmiştir. Toplam = 26 P0 ailesi.)*

### B. CSV'de Mevcut Olup İlk Demo Betiğinde (`run_demo_models.py`) Henüz Kullanılmayan P0 Aileleri (5 P0 Ailesi)

Bu 5 aile CSV'de hazırdır ancak ilk demo yalnızca 4 ana hedef (`T01`, `T07`, `T11`, `T14`) üzerine odaklandığı için henüz `fin_features` listesine eklenmemiştir:

| Sözlük ID | Aile Adı | CSV'deki Sütun(lar) | Boşluk (`/1320`) | Neden Henüz Kullanılmadı / Ne Zaman Eklenecek? |
|---|---|---|---|---|
| **F07** | Vergi gideri/geliri | `T06_vergi_gideri_geliri_ceyrek` (`0`), `T06_vergi_gideri_geliri_ytd` (`0`) | `0` | CSV'de %100 dolu; `T06` ve `T07` modellerinde `q-1` / `aktif` oranı olarak doğrudan eklenebilir. |
| **F08** | Finansman ve faiz giderleri | `T05_finansman_gideri_ceyrek` (`16`), `T05_finansman_gideri_ytd` (`11`) | `16` | CSV'de mevcut; `T05` ve `T07` modellerinde aktif ölçekli gecikme olarak eklenebilir. |
| **F10** | Ticari alacak | `F10_kisa_vadeli_ticari_alacaklar` (`129`), `F10_uzun_vadeli_ticari_alacaklar` (`659`), `T09_ticari_alacaklar` (`750`), `F10_alacak_satis_orani` (`750`) | `129` (kısa), `750` (toplam) | Uzun vadeli ticari alacak çoğu şirkette ayrı raporlanmadığı için toplam `T09` ve `F10_alacak_satis_orani` 750 satırda `NaN`. Modellemede kısa vadeli ticari alacak / aktif oranı tercih edilmeli. |
| **F11** | Stok | `T10_stoklar` (`27`), `F11_stok_maliyet_orani` (`27`) | `27` | CSV'de yüksek dolulukla (%98) hazır; `T02`, `T10`, `T15` tahminlerinde eklenebilir. |
| **F12** | Ticari borç | `kisa_vadeli_ticari_borclar` (`143`), `uzun_vadeli_ticari_borclar` (`815`), `F12_ticari_borclar` (`860`), `F12_ticari_borc_maliyet_orani` (`860`) | `143` (kısa), `860` (toplam) | Uzun vadeli ticari borç çoğu şirkette olmadığı/ayrı sunulmadığı için toplam `F12_ticari_borclar` 860 satırda `NaN`. Kısa vadeli ticari borç / aktif oranı kullanılmalı. |

---

## 5. Eksik Olan (CSV'de Henüz Bulunmayan veya Kısmi Olan) P1 ve P2 Değişken Aileleri (25 Aile)

Sözlükteki **19 P1** ve **6 P2** ailesinden yalnızca **`R04`** tam olarak CSV'de yer almaktadır (`F15` ise yalnızca toplam `duran_varliklar` düzeyinde kısmidir). Geriye kalan **24 aile** henüz veri hattına bağlanmamıştır:

| Sözlük ID | Öncelik | Grup | Aile Adı | CSV Durumu | Eksikliği Gidermek İçin Gereken Veri Kaynağı / İş |
|---|---|---|---|---|---|
| **R04** | **P1** | Risk | GPR tehdit / gerçekleşen eylem ayrımı | **CSV'de VAR** (`R04_GPRT`, `R04_GPRA`, `0` eksik) | CSV'de hazır; E2 alternatif risk deneyinde test edilecek. |
| **F15** | **P1** | Finansal | Yatırım, duran varlık ve amortisman | **Kısmi** (Yalnız `duran_varliklar` var, `8` eksik; CAPEX, PPE ve amortisman yok) | KAP nakit akışı/dipnotlarından maddi/maddi olmayan duran varlık alımları (CAPEX) ve amortisman/itfa satırlarının ayrıştırılması. |
| **F16** | **P1** | Finansal | Faaliyet giderleri ve Ar-Ge | **Eksik** | KAP gelir tablosundan pazarlama/satış/dağıtım, genel yönetim ve Ar-Ge gideri satırlarının (`parse_financial_rows`) çekilmesi. *(Mevcut `.xls` dosyalarından çıkarılabilir!)* |
| **F17** | **P1** | Finansal | Sözleşme varlığı | **Eksik** | TFRS 15 (2018+) sonrası bilançolarda "Sözleşme Varlıkları" kaleminin ayrıştırılması. |
| **F18** | **P1** | Finansal | Müşteri avansı ve sözleşme yükümlülüğü | **Eksik** | Bilançodaki "Ertelenmiş Gelirler / Sözleşme Yükümlülükleri / Alınan Sipariş Avansları" satırlarının ayrıştırılması. *(Mevcut `.xls` dosyalarından kısmen çıkarılabilir!)* |
| **F19** | **P1** | Finansal | Net döviz pozisyonu | **Eksik** | Dipnotlarda (Yabancı Para Pozisyonu tablosu) yer alır; özet `.xls` tablosunda standart satır değildir, PDF/dipnot ayrıştırıcısı gerekir. |
| **M07** | **P1** | Makro | İlgili emtia fiyatı | **Eksik** | Brent petrol, çelik/demir cevheri, alüminyum, buğday/tarım vb. dış fiyat serilerinin indirilip sektörlerle eşlenmesi. |
| **M08** | **P1** | Makro | Sektör talep ve faaliyet göstergesi | **Eksik** | EVDS / TÜİK sektörel ciro, kapasite kullanım veya turizm/havacılık yolcu istatistiklerinin eklenmesi. |
| **C02** | **P1** | Profil | Ürün / faaliyet gelir karması | **Eksik** | TFRS 8 faaliyet bölümleri dipnotlarından gelir paylarının çıkarılması. |
| **C03** | **P1** | Profil | Yurtdışı gelir ve ihracat payları | **Eksik** | Gelir tablosu dipnotlarından yurt içi / yurt dışı satış kırılımının çıkarılması. |
| **C04** | **P1** | Profil | Satış coğrafyası ve yoğunlaşma | **Eksik** | Faaliyet raporu ve dipnotlardan ülke/bölge satış paylarının çıkarılması. |
| **C07** | **P1** | Profil | Enerji / emtia üretici-tüketici rolü | **Eksik** | Şirketlerin enerji/emtia üreticisi mi yoğun tüketicisi mi olduğunu belirten tarihsel kaynaklı profil tablosu. |
| **C09** | **P1** | Profil | Sipariş ve ifa görünürlüğü | **Eksik** | Savunma/proje şirketleri (ör. ASELS, OTKAR) için faaliyet raporlarındaki bakiye sipariş (backlog) ve yeni sözleşme verisi. |
| **C10** | **P1** | Profil | Üretim kapasitesi, hacim ve birim fiyat | **Eksik** | KAP faaliyet raporlarındaki üretim/satış tonaj ve kapasite kullanım verileri. |
| **X01** | **P1** | Etkileşim | Kur × net döviz pozisyonu | **Eksik** | `F19` (net döviz pozisyonu) tamamlandığında `M01`/`M02` ile çarpılarak üretilecek. |
| **X04** | **P1** | Etkileşim | Jeopolitik risk × faaliyet karması | **Eksik** | `C02` (veya başlangıç vekili olarak `C01` sektör/faaliyet kategorisi) × `R01_GPR`. |
| **X05** | **P1** | Etkileşim | Coğrafi satış ağırlıklı ülke riski | **Eksik** | `C04` (satış coğrafyası) ve ülke bazlı GPR serileri eşlendiğinde üretilecek. |
| **X06** | **P1** | Etkileşim | Emtia × üretici/tüketici profili | **Eksik** | `M07` (emtia fiyatı) ve `C07` (üretici/tüketici rolü) tamamlandığında üretilecek. |
| **X07** | **P1** | Etkileşim | Kur × ihracat / yurtdışı satış | **Eksik** | `C03` (ihracat/yurtdışı satış payı) tamamlandığında `M01`/`M02` ile üretilecek. |
| **F20** | **P2** | Finansal | Borç koşulları ve korunma | **Eksik** | Dipnotlardan sabit/değişken faizli borç ve türev korunma (hedge) oranları. |
| **C05** | **P2** | Profil | Müşteri türü ve yoğunlaşması | **Eksik** | Dipnotlardan kamu/özel müşteri ve %10 üzeri tekil müşteri yoğunlaşması. |
| **C06** | **P2** | Profil | Tedarik ve ithal girdi profili | **Eksik** | Dipnot/faaliyet raporlarından ithal girdi payı. |
| **C08** | **P2** | Profil | Sözleşme fiyatlama yapısı | **Eksik** | Sabit fiyatlı vs maliyet artı / döviz endeksli sözleşme yapısı. |
| **E01** | **P2** | Olay | Olay türü, coğrafyası ve ekonomik kanalı | **Eksik** | Yapılandırılmış tarihsel olay takvimi. |
| **X08** | **P2** | Etkileşim | Olay bağlamı × ilgili şirket profili | **Eksik** | `E01` ve ilgili `C*` profilleri tamamlandığında üretilecek. |

> **Hızlı Kazanım Notu:** `F16` (Pazarlama/Satış, Genel Yönetim, Ar-Ge giderleri) ve `F18` (Ertelenmiş gelirler / Alınan avanslar) aslında şu an elimizdeki `data/kap_raw_xls/*.xls` dosyalarının çoğunda ana tablo satırı olarak **mevcuttur**; PDF/dipnot indirmeye gerek kalmadan `parse_and_build_dataset.py` içine etiket kuralları eklenerek doğrudan CSV'ye kazandırılabilir.

---

## 5.1. Planlanan Yapılacak İş: Günlük/Aylık Verilerin 3 Aylık Hedeflerle Birleştirilmesi (3. Yaklaşım — MIDAS Dağılım Özeti + Nowcasting Ufukları)

Hedef değişkenlerimiz (`T01`–`T17`) **3 ayda bir (çeyreklik)** açıklanırken, kur (`M01`, `M02`), finansal stres (`R03`) ve jeopolitik risk (`R01` günlük `GPRD`) **günlük** frekanstadır. Bu frekans farkını yönetmek ve **gün geçtikçe keskinleşen tahmin** üretmek için karar verilen **3. Yaklaşım** uygulanacaktır:

1. **Sözde-Tekrar (Pseudoreplication) Yasağı:**
   * 1.320 çeyreklik satırı 90 güne çoğaltıp aynı çeyrek bilanço hedefini ($y_q$) 90 satıra kopyalamak istatistiksel bağımsızlığı bozduğu için **yapılmayacaktır**.
2. **Günlük Serilerden Çeyrek İçi Dağılım/Yörünge Özellikleri Üretilmesi:**
   * Günlük `GPRD` (`data_gpr_daily_recent.xls`) veri hattına eklenecektir.
   * Günlük serilerden (`USDTRY`, `EURTRY`, `OFR_FSI`, `GPRD`) yalnız tek bir gün veya basit fark yerine, tahmin kesim anına ($t_0$) kadar bilinen **çeyrek içi ortalama (`mean`)**, **kesim günü seviyesi (`last`)**, **volatilite (`std`)**, **zirve şok (`max`)** ve **son 15 gün / ilk 75 gün ivmesi** çıkarılacaktır. (Gelir tablosu akış kalemleri çeyrek ortalamasına, bilanço bakiye kalemleri dönem sonu kur/stres seviyesine duyarlıdır.)
3. **Çoklu Bilgi Kesim Ufku (Nowcasting Horizons — $t_0$):**
   * Her şirket–çeyrek için çeyrek başından bilanço açıklanma gününe kadar belirli bilgi kesim noktaları ($t_0 \in \{+30\text{g (1. ay sonu)}, +60\text{g (2. ay sonu)}, +90\text{g (çeyrek sonu)}, +120\text{g (bilanço öncesi)}\}$) ve `days_since_quarter_start` (bilgi olgunluk günü) tanımlanacaktır.
   * Her $t_0$ kesiminde yalnızca `available_at <= t0` koşulunu sağlayan günlük ve aylık veriler kullanılarak, çeyrek ilerledikçe tahmin hatasının (MAE) nasıl düştüğü ölçülecek ve canlı kullanımda (Model Sonrası) o güne kadar birikmiş günlük verilerle anlık tahmin güncellenebilecektir.

---

## 6. Sözlükte Ayrı Bir ID Olarak Yazılmamış Olup CSV'ye Eklediğimiz Ekstra Sütunlar (38 Sütun)

CSV'deki 110 sütunun 72 tanesi doğrudan yukarıdaki `T01`–`T17` hedeflerine (YTD + çeyrek) ve sözlükteki `F* / M* / R* / C01 / X02 / X03` ailelerine karşılık gelir. Geriye kalan **38 sütun**, veri izlenebilirliği, zaman sızıntısı kontrolü ve finansal alt kırılımlar için **fazladan/destekleyici** olarak eklenmiştir:

### A. Kimlik, Kaynak, Yayın Zamanı ve Kalite Metadatası (24 Sütun — Model Girdisi Değildir)
1. `ticker`: BIST işlem kodu (30 şirket).
2. `company_name`: Şirket tam unvanı.
3. `year`: Mali yıl (`2010`–`2020`).
4. `quarter`: Mali çeyrek (`1`–`4`).
5. `observation_period`: `YYYYQ#` dönem anahtarı (ör. `2010Q1`).
6. `period_end_date`: Çeyrek sonu takvim tarihi (tahmin anı `t0` referansı).
7. `first_published_at`: Geriye dönük uyumluluk için seçilmiş raporun yayın zamanı (`report_available_at` ile aynı).
8. `disclosure_index`: KAP bildirim numarası.
9. `consolidation`: Konsolide (`CS`) / Solo (`NC`) bilgisi.
10. `original_unit`: Ham rapordaki birim metni (`TL`, `1.000 TL`, `1.000.000 TL` vb.).
11. `currency`: Para birimi (`TRY`).
12. `source_file`: Okunan ham `.xls` dosyasının yolu.
13. `source_sha256`: Ham `.xls` dosyasının SHA-256 özeti.
14. `unit_multiplier`: Tutarı tam TL'ye çevirmek için uygulanan çarpan (`1`, `1000`, `1000000`).
15. `report_available_at`: Seçilen rapor sürümünün KAP yayın zamanı.
16. `source_available_at`: Karşılaştırmalı düzeltme kanıtı varsa onun zamanını da içeren kaynak kullanılabilirlik zamanı.
17. `earliest_known_publication_at`: Aynı şirket–dönem için katalogda bilinen en erken bildirim zamanı.
18. `publication_status`: Rapor sürüm durumu (`earliest_known_version` veya `selected_version_later_than_earliest`).
19. `qa_flags`: Kapsam/kaynak/düzeltme uyarı bayrakları (105 satırda dolu).
20. `available_at`: Çeyrek farkı (`YTD_q - YTD_{q-1}`) için önceki raporun yayın zamanını da kapsayan **temkinli finansal kullanılabilirlik zamanı** (modelde sızıntı kontrolü için zorunlu sütun).
21. `macro_observation_month`: Aylık makro/risk serilerinin bağlandığı gözlem ayı (`t - 1 ay`).
22. `industrial_production_observation_month`: Sanayi üretiminin bağlandığı gözlem ayı (`t - 2 ay`).
23. `ofr_observation_date`: OFR FSI için kullanılan son geçerli ABD iş günü tarihi.
24. `ofr_assumed_available_at`: OFR FSI gözleminin 2 ABD iş günü sonrası varsayılan yayın tarihi (`<= period_end_date`).
25. `macro_availability_policy`: Makro gecikme ve takvim politikasını açıklayan sabit izlenebilirlik etiketi.

### B. Eklenen Yardımcı Finansal Alt Kalemler ve Türevler (13 Sütun)
1. `T07_ana_ortaklik_net_kari_ytd` ve `T07_ana_ortaklik_net_kari_ceyrek` (`133` / `134` eksik): Toplam dönem net kârından (`T07`) ayrı olarak ana ortaklık payları.
2. `T14_ana_ortakliga_ait_ozkaynaklar` (`0` eksik): Toplam özkaynaktan (`T14`) ayrı olarak ana ortaklığa ait özkaynaklar.
3. `donen_varliklar` (`8` eksik) ve `duran_varliklar` (`8` eksik): `T11_toplam_varliklar` alt bileşenleri.
4. `kisa_vadeli_yukumlulukler` (`8` eksik) ve `uzun_vadeli_yukumlulukler` (`8` eksik): `T13_toplam_yukumlulukler` alt bileşenleri.
5. `F07_finansman_geliri_ytd` (`107` eksik), `F07_finansman_geliri_ceyrek` (`110` eksik), `F07_net_finansman_ytd` (`111` eksik), `F07_net_finansman_ceyrek` (`115` eksik): Finansman giderinin (`T05`/`F08`) yanında finansman gelirini ve net finansmanı ayrı görmek için eklendi.
6. `F13_net_borc` (`139` eksik): `T12_finansal_borclar - T08_nakit_ve_nakit_benzerleri` türevi (borç bileşenlerinden biri bilinmiyorsa sahte `-nakit` üretmemek için `NaN` bırakılır).
7. `F14_borc_ozkaynak_orani` (`0` eksik): `T13_toplam_yukumlulukler / T14_toplam_ozkaynaklar` kaldıraç oranı.
8. `odenmis_sermaye` (`1` eksik), `kap_raporlanan_hbk_ytd` (`642` eksik), `hisse_basina_kar_ytd` (`134` eksik), `hisse_basina_kar_ceyrek` (`135` eksik): Raporlanan HBK ve ödenmiş sermayeye bölünen yaklaşık HBK vekili ([AGENTS.md](../../AGENTS.md) uyarınca ağırlıklı ortalama pay sayısı doğrulanmadan gerçek EPS hedefi sayılmaz).
