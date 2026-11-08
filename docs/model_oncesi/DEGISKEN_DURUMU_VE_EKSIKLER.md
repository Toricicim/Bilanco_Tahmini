# Değişken Eşleme, Kullanım ve Kapsam Durumu

Bu belge, yetkili değişken sözlüğü olan [degiskenler.json](degiskenler.json) ([DEGISKEN_LISTESI.md](DEGISKEN_LISTESI.md)) içindeki **17 hedef** ve **51 girdi ailesi (26 P0, 19 P1, 6 P2)** ile kanonik veri tablomuz [data/bist_bilanco_tahmini_2010_2020.csv](../../data/bist_bilanco_tahmini_2010_2020.csv) (**1.320 satır × 157 sütun**) ve çoklu ufuklu (point-in-time nowcasting) eğitim matrisimiz [data/training_matrix_pit_2010_2020.csv](../../data/training_matrix_pit_2010_2020.csv) (**5.280 satır × 113 sütun**) arasındaki birebir eşlemeyi, eksik olan değişkenleri ve sözlük dışında eklenen yardımcı/metadata sütunlarını tutar.

> **Kural:** Yeni bir değişken/sütun CSV'ye eklendiğinde, çıkarıldığında, adı değiştiğinde veya model eğitim matrisine dahil edildiğinde [degiskenler.json](degiskenler.json), [DEGISKEN_LISTESI.md](DEGISKEN_LISTESI.md) (`scripts/render_feature_list.py`) ile birlikte **bu dosya da güncellenmelidir**.

---

## 1. Yönetici Özeti (Sayısal Dağılım)

| Kategori | Sözlükteki Toplam | CSV / Eğitim Matrisinde Karşılığı Olan (Mevcut) | Henüz Olmayan (Eksik) | Açıklama |
|---|---|---|---|---|
| **Hedefler (`T01`–`T17`)** | **17** | **17 / 17** (Hem YTD hem çeyrek akış/bakiye) | **0** | İlk aşamada öncelikli 4 hedef (`T01`, `T07`, `T11`, `T14`) %100 doludur (`0` eksik). |
| **P0 Girdi Aileleri** | **26** | **26 / 26** (`M03` bankalararası faiz vekiliyle; `M01`/`M02`/`R01`/`R03` günlük yörüngeleri dahil) | **0** | 26 P0 ailesinin tamamının CSV'de ve sızıntısız eğitim matrisinde karşılık sütun(lar)ı mevcuttur. |
| **P1 Girdi Aileleri** | **19** | **5 / 19** (`R04`, `F15`, `F16`, `F18` CSV'de; `X04` alt sektör vekili eğitim matrisinde) | **14** | Mevcut `.xls` raporlarından `F15`, `F16`, `F18` ve `X04` çıkarılmıştır; kalan 14 aile PDF dipnotu veya dış emtia/sektör serisi gerektirir. |
| **P2 Girdi Aileleri** | **6** | **0 / 6** | **6** | Borç vade/korunma detayı, müşteri/tedarik yoğunlaşması, sözleşme fiyatlama, olay bağlamı. |
| **Sözlük Dışı / Ekstra Sütunlar** | — | **42 sütun** (kanonik CSV'de) | — | 27 kimlik/zaman/kalite metadatası + 15 ek finansal alt kalem (`vergi_oncesi_kar_zarar_*` dahil), türev ve HBK sütunu. |

---

## 2. Önemli Önek (Prefix) ve İsimlendirme Uyarıları

CSV'deki bazı sütun adlarının başındaki `Fxx` önekleri, [degiskenler.json](degiskenler.json) sözlüğündeki `id` numaralarıyla **birebir aynı değildir** ([AGENTS.md](../../AGENTS.md) P0-C uyarısı):

1. **Sözlük `F01` (Şirket ölçeği) ≠ CSV `F01_*` (Hasılat büyümesi):**
   * Sözlükte `F01` "Şirket ölçeği (son bilinen toplam varlık)" iken, CSV'de `F01_hasilat_qoq_buyume` ve `F01_hasilat_yoy_buyume` sütunları aslında sözlükteki **`F02` (Hasılat geçmişi)** ailesinin büyüme türevleridir. Şirket ölçeği (`F01`), `T11_toplam_varliklar` sütununun geçmiş (`q-1`) değerinden üretilir.
2. **Sözlük `F07` (Vergi gideri/geliri) ≠ CSV `F07_*` (Finansman geliri ve net finansman):**
   * Sözlükte `F07` "Vergi gideri/geliri" ailesidir ve CSV'deki karşılığı `T06_vergi_gideri_geliri_ytd` / `T06_vergi_gideri_geliri_ceyrek` sütunlarının geçmiş değerleridir (`vergi_oncesi_kar_zarar_*` sütunlarından ayrıştırılmıştır).
   * CSV'deki `F07_finansman_geliri_ytd`, `F07_finansman_geliri_ceyrek`, `F07_net_finansman_ytd`, `F07_net_finansman_ceyrek` sütunları ise sözlükteki **`F08` (Finansman ve faiz giderleri)** ailesinin yardımcı/ekstra bileşenleridir.
3. **CSV'deki Eşzamanlı Etkileşim Sütunları (`X02_*`, `X03_*`):**
   * Kanonik CSV'deki `X02_faiz_degisimi_x_finansal_borc_aktif` ve `X03_ofr_fsi_x_kisa_borc_aktif` sütunları **aynı satırın (`q` çeyreğinin)** borç oranlarıyla çarpılmıştır. Tahmin anında (`t0`) hedef çeyreğin bilançosu henüz açıklanmadığı için [scripts/build_training_matrix.py](../../scripts/build_training_matrix.py) tarafından üretilen eğitim matrisinde doğrudan bu iki eşzamanlı sütun **kullanılmaz**; bunun yerine `available_at <= t0` koşulunu sağlayan geçmiş (`q-1`) borç oranlarıyla çarpılan sızıntısız `X02_faiz_x_fin_borc_q1` ve `X03_ofr_x_kisa_borc_q1` etkileşimleri üretilir.

---

## 3. Hedef Değişkenlerin (`T01`–`T17`) CSV Durumu

17 hedefin tamamı CSV'de mevcuttur. Akış kalemleri (gelir tablosu ve nakit akışı) hem kümülatif (`_ytd`) hem tek çeyrek (`_ceyrek`) olarak tutulur; model hedefi tek çeyrek (`_ceyrek`) ve dönem sonu bilanço bakiyeleridir.

| Sözlük ID | Hedef Tanımı | Tür | CSV Hedef Sütunu | CSV YTD Sütunu | Boşluk (`NaN` / 1.320) | Kapsam ve Notlar |
|---|---|---|---|---|---|---|
| **T01** | Hasılat | Akış | `T01_hasilat_ceyrek` | `T01_hasilat_ytd` | `0 / 1320` | **Öncelikli 4 Hedeften 1'i** (Tam dolu; `TUPRS 2010Q1–2012Q4` hizmet gelirleri uzlaştırıldı) |
| **T02** | Satışların maliyeti | Akış | `T02_satislarin_maliyeti_ceyrek` | `T02_satislarin_maliyeti_ytd` | `1 / 1320` (YTD: `1`) | CSV'de hazır (`RYSAS 2011Q1` işaret istisnası brüt kârla doğrulandı) |
| **T03** | Brüt kâr | Türetilmiş akış | `T03_brut_kar_ceyrek` | `T03_brut_kar_ytd` | `0 / 1320` | Tam dolu (75 karma kapsam ve 1 olağan kaynak farkı `ALCTL 2010Q3` bayrağına dikkat) |
| **T04** | Esas faaliyet kârı | Akış | `T04_esas_faaliyet_kari_ceyrek` | `T04_esas_faaliyet_kari_ytd` | `1 / 1320` (YTD: `1`) | CSV'de hazır |
| **T05** | Finansman gideri | Akış | `T05_finansman_gideri_ceyrek` | `T05_finansman_gideri_ytd` | `16 / 1320` (YTD: `11`) | CSV'de hazır |
| **T06** | Vergi gideri/geliri | Akış | `T06_vergi_gideri_geliri_ceyrek` | `T06_vergi_gideri_geliri_ytd` | `10 / 1320` (YTD: `8`) | Vergi öncesi kâr/zarar (`vergi_oncesi_kar_zarar_*`) satırından ayrıldı; üst vergi satırı boş olduğunda dönem + ertelenmiş vergi alt kalemlerinden türetildi (`%99.4` dolu) |
| **T07** | Dönem net kârı | Akış | `T07_donem_net_kari_ceyrek` | `T07_donem_net_kari_ytd` | `0 / 1320` | **Öncelikli 4 Hedeften 1'i** (Tam dolu; OCI bölüm geçiş koruması eklendi) |
| **T08** | Nakit ve nakit benzerleri | Bakiye | `T08_nakit_ve_nakit_benzerleri` | — | `0 / 1320` | Tam dolu |
| **T09** | Ticari alacak | Bakiye | `T09_ticari_alacaklar` | — | `750 / 1320` | Uzun vadeli alacak çoğu raporda ayrı olmadığı için toplam `NaN`; kısa vadeli (`F10_kisa_...`, `129` eksik) ayrı korunuyor |
| **T10** | Stok | Bakiye | `T10_stoklar` | — | `27 / 1320` | CSV'de hazır |
| **T11** | Toplam varlık | Bakiye | `T11_toplam_varliklar` | — | `0 / 1320` | **Öncelikli 4 Hedeften 1'i** (Tam dolu) |
| **T12** | Finansal borç | Bakiye | `T12_finansal_borclar` | — | `139 / 1320` | Alt bileşen eksikliğinde `NaN`; kısa vadeli (`23` eksik) ayrı korunuyor |
| **T13** | Toplam yükümlülük | Bakiye | `T13_toplam_yukumlulukler` | — | `0 / 1320` | Tam dolu |
| **T14** | Toplam özkaynak | Bakiye | `T14_toplam_ozkaynaklar` | — | `0 / 1320` | **Öncelikli 4 Hedeften 1'i** (Tam dolu) |
| **T15** | İşletme nakit akışı | Akış | `T15_isletme_nakit_akisi_ceyrek` | `T15_isletme_nakit_akisi_ytd` | `2 / 1320` (YTD: `1`) | Üst toplam (`A. İŞLETME FAALİYETLERİNDEN NAKİT AKIŞLARI`) önceliği korundu; vergi/faiz öncesi alt toplam ezmesi önlendi |
| **T16** | Yatırım nakit akışı | Akış | `T16_yatirim_nakit_akisi_ceyrek` | `T16_yatirim_nakit_akisi_ytd` | `10 / 1320` (YTD: `5`) | CSV'de hazır |
| **T17** | Finansman nakit akışı | Akış | `T17_finansman_nakit_akisi_ceyrek` | `T17_finansman_nakit_akisi_ytd` | `11 / 1320` (YTD: `8`) | CSV'de hazır (`RYSAS 2010Q1` mükerrer etiket koruması eklendi) |

---

## 4. Mevcut P0 Girdi Ailelerinin CSV Eşlemesi (26 / 26 Aile CSV'de ve Eğitim Matrisinde Mevcut)

26 P0 ailesinin **tamamı** CSV'de ham veya türetilmiş sütun olarak mevcuttur. Model eğitim matrisinde ([data/training_matrix_pit_2010_2020.csv](../../data/training_matrix_pit_2010_2020.csv)) finansal ailelerin (`F01`–`F14`) hedef çeyrek (`q`) değerleri değil, `available_at <= t0` koşulunu sağlayan geçmiş (`q-1`, `q-4` vb.) değerleri kullanılır:

| Sözlük ID | Aile Adı | CSV'deki Karşılık Sütun(lar) | Boşluk (`/1320`) | Eğitim Matrisi (`training_matrix_pit_2010_2020.csv`) Kullanımı |
|---|---|---|---|---|
| **F01** | Şirket ölçeği | `T11_toplam_varliklar` | `0` | Tahmin anında bilinen son toplam varlık (`scale_assets_q1`, `log_scale_assets_q1`) ölçekleyici olarak kullanılır. |
| **F02** | Hasılat geçmişi | `T01_hasilat_ceyrek` (`0`), `F01_hasilat_qoq_buyume` (`30`), `F01_hasilat_yoy_buyume` (`120`) | `0`–`120` | `T01_hasilat_ceyrek_scaled_q1`, `_q4`, `F01_hasilat_qoq_buyume_q1`, `F01_hasilat_yoy_buyume_q1`. |
| **F03** | Satış maliyeti ve brüt marj | `T02_satislarin_maliyeti_ceyrek` (`1`), `T03_brut_kar_ceyrek` (`0`), `F03_brut_kar_marji` (`84`) | `1`–`84` | `T03_brut_kar_ceyrek_scaled_q1`, `F03_brut_kar_marji_q1` (karma kapsamlı raporlarda marj `NaN` korunur). |
| **F04** | Faaliyet kârı ve marjı | `T04_esas_faaliyet_kari_ceyrek` (`1`), `F04_esas_faaliyet_marji` (`1`) | `1` | `T04_esas_faaliyet_kari_ceyrek_scaled_q1`, `F04_esas_faaliyet_marji_q1`. |
| **F05** | Dönem net kârı | `T07_donem_net_kari_ceyrek` (`0`), `F05_net_kar_marji` (`0`) | `0` | `T07_donem_net_kari_ceyrek_scaled_q1`, `_q4`, `F05_net_kar_marji_q1`. |
| **F06** | İşletme nakit akışı ve tahakkuk | `T15_isletme_nakit_akisi_ceyrek` (`2`), `F06_cfo_aktif_orani` (`2`), `F06_tahakkuk_aktif_orani` (`2`) | `2` | `T15_isletme_nakit_akisi_ceyrek_scaled_q1`, `F06_cfo_aktif_orani_q1`, `F06_tahakkuk_aktif_orani_q1`. |
| **F07** | Vergi gideri/geliri | `T06_vergi_gideri_geliri_ceyrek` (`10`), `T06_vergi_gideri_geliri_ytd` (`8`) | `8`–`10` | `T06_vergi_gideri_geliri_ceyrek_scaled_q1` (`vergi_oncesi_kar_zarar` satırından ayrıştırılmış gerçek vergi). |
| **F08** | Finansman ve faiz giderleri | `T05_finansman_gideri_ceyrek` (`16`), `T05_finansman_gideri_ytd` (`11`) | `11`–`16` | `T05_finansman_gideri_ceyrek_scaled_q1`. |
| **F09** | Nakit ve nakit benzerleri | `T08_nakit_ve_nakit_benzerleri` (`0`), `F09_nakit_aktif_orani` (`0`) | `0` | `T08_nakit_ve_nakit_benzerleri_scaled_q1`, `F09_nakit_aktif_orani_q1`. |
| **F10** | Ticari alacak | `F10_kisa_vadeli_ticari_alacaklar` (`129`), `F10_uzun_vadeli_ticari_alacaklar` (`659`), `T09_ticari_alacaklar` (`750`), `F10_alacak_satis_orani` (`750`) | `129` (kısa), `750` (toplam) | `F10_kisa_vadeli_ticari_alacaklar_scaled_q1`. |
| **F11** | Stok | `T10_stoklar` (`27`), `F11_stok_maliyet_orani` (`27`) | `27` | `T10_stoklar_scaled_q1`, `F11_stok_maliyet_orani_q1`. |
| **F12** | Ticari borç | `kisa_vadeli_ticari_borclar` (`143`), `uzun_vadeli_ticari_borclar` (`815`), `F12_ticari_borclar` (`860`), `F12_ticari_borc_maliyet_orani` (`860`) | `143` (kısa), `860` (toplam) | `kisa_vadeli_ticari_borclar_scaled_q1`. |
| **F13** | Finansal borç ve vade dağılımı | `F13_kisa_vadeli_finansal_borclar` (`23`), `F13_uzun_vadeli_finansal_borclar` (`133`), `T12_finansal_borclar` (`139`), `F13_finansal_borc_aktif_orani` (`139`), `F13_kisa_finansal_borc_aktif_orani` (`23`) | `23`–`139` | `F13_kisa_finansal_borc_aktif_orani_q1`, `F13_finansal_borc_aktif_orani_q1`. |
| **F14** | Yükümlülük ve özkaynak | `T13_toplam_yukumlulukler` (`0`), `T14_toplam_ozkaynaklar` (`0`), `F14_ozkaynak_aktif_orani` (`0`) | `0` | `T13_toplam_yukumlulukler_scaled_q1`, `T14_toplam_ozkaynaklar_scaled_q1`, `_q4`, `F14_ozkaynak_aktif_orani_q1`, `F14_borc_ozkaynak_orani_q1`. |
| **M01** | USD/TL değişimi | `M01_USDTRY_90g_degisim_pct` (`0`), `M01_USDTRY_seviye` (`0`) + **5 çeyrek içi yörünge sütunu**: `M01_USDTRY_q_mean`, `_q_last`, `_q_std`, `_q_max`, `_last15d_diff` (`0`) | `0` | Her $t_0 \in \{+30\text{g}, +60\text{g}, +90\text{g}, +120\text{g}\}$ kesimi için gerçek iş günü gözlemlerinden dinamik hesaplanır. |
| **M02** | EUR/TL değişimi | `M02_EURTRY_90g_degisim_pct` (`0`), `M02_EURTRY_seviye` (`0`) + **5 çeyrek içi yörünge sütunu**: `M02_EURTRY_q_mean`, `_q_last`, `_q_std`, `_q_max`, `_last15d_diff` (`0`) | `0` | Her $t_0$ kesimi için gerçek iş günü gözlemlerinden dinamik hesaplanır. |
| **M03** | Ticari kredi faizi *(Vekil)* | `M03_Faiz_Orani` (`0`), `M03_Faiz_3Aylik_Degisim` (`0`) | `0` | **Uyarı:** Mevcut seri OECD gecelik bankalararası faiz vekilidir; `EVDS_API_KEY` ile gerçek TCMB ticari kredi faizi eklenecek. |
| **M04** | TÜFE | `M04_TUFE_YoY` | `0` | $t_0$'dan 1 ay gecikmeli yıllık değişim. |
| **M05** | Yİ-ÜFE | `M05_YIUFE_YoY` | `0` | $t_0$'dan 1 ay gecikmeli yıllık değişim. |
| **M06** | Sanayi üretimi | `M06_SanayiUretimi_YoY` | `30` (2010Q1) | $t_0$'dan 2 ay gecikmeli yıllık değişim (2010Q1 $+30\text{g}/+60\text{g}/+90\text{g}$ kesimlerinde yayın gecikmesi nedeniyle dürüstçe `NaN`). |
| **R01** | GPR: jeopolitik risk | `R01_GPR` (`0`), **`R01_GPRC_TUR` (`0`)**, **`R01_GPRD` (`0`)** + **5 çeyrek içi yörünge sütunu**: `R01_GPRD_q_mean`, `_q_last`, `_q_std`, `_q_max`, `_last15d_diff` (`0`) | `0` | Küresel aylık GPR, **Türkiye GPR (`R01_GPRC_TUR`)**, $+7\text{ gün}$ haftalık yayın gecikmeli günlük `R01_GPRD` ve gecikmeli `R01_GPRC_TUR_q1`/`_q2`/`_q4`. |
| **R02** | GEPU: ekonomik politika belirsizliği | `R02_GEPU_ppp` | `0` | $t_0$'dan 1 ay gecikmeli PPP ağırlıklı küresel endeks. |
| **R03** | OFR FSI: finansal stres | `R03_OFR_FSI` (`0`), `R03_OFR_FSI_60d_mean` (`0`) + **5 çeyrek içi yörünge sütunu**: `R03_OFR_FSI_q_mean`, `_q_last`, `_q_std`, `_q_max`, `_last15d_diff` (`0`) | `0` | 2 ABD iş günü gecikmeli, 60 gerçek gözlem ortalaması ve çeyrek içi yörünge özeti. |
| **C01** | Tarihsel sektör ve faaliyet kategorisi | `sector_group` (`0`), `C01_kap_main_sector` (`0`), `C01_kap_sub_sector` (`0`) | `0` | Özellikle `C01_kap_sub_sector` (`SAVUNMA` vs `BİLİŞİM` vb.) şirketlerin olaylara farklı tepkisini ayırmak için kullanılır. |
| **X02** | Faiz × finansal borçluluk | `X02_faiz_degisimi_x_finansal_borc_aktif` (`139`) | `139` | Eğitim matrisinde `q-1` borç oranıyla çarpılan sızıntısız `X02_faiz_x_fin_borc_q1` kullanılır. |
| **X03** | Finansal stres × kısa vadeli borç | `X03_ofr_fsi_x_kisa_borc_aktif` (`23`) | `23` | Eğitim matrisinde `q-1` kısa vadeli borç oranıyla çarpılan sızıntısız `X03_ofr_x_kisa_borc_q1` kullanılır. |

---

## 5. P1 ve P2 Değişken Ailelerinin Durumu (5 P1 Ailesi Eklendi, 14 P1 + 6 P2 Ailesi Eksik)

Sözlükteki **19 P1** ailesinden **`R04`**, **`F15`**, **`F16`**, **`F18`** ve **`X04`** veri hattına ve eğitim matrisine kazandırılmıştır. Geriye kalan **14 P1** ve **6 P2** ailesi PDF dipnot ayrıştırıcısı veya ek dış veri kaynağı gerektirir:

| Sözlük ID | Öncelik | Grup | Aile Adı | CSV / Eğitim Matrisi Durumu | Açıklama / Kalan Eksikliği Gidermek İçin Gereken İş |
|---|---|---|---|---|---|
| **R04** | **P1** | Risk | GPR tehdit / gerçekleşen eylem ayrımı | **CSV'de VAR** (`R04_GPRT`, `R04_GPRA`, `R04_GPRD_ACT`, `R04_GPRD_THREAT`, `0` eksik) | Hem aylık hem $+7\text{ gün}$ gecikmeli günlük tehdit/eylem serileri tam doludur. |
| **F15** | **P1** | Finansal | Yatırım, duran varlık ve amortisman | **CSV'de VAR (8 yeni sütun)**: `F15_maddi_duran_varliklar` (`0` eksik), `F15_maddi_olmayan_duran_varliklar` (`13` eksik), `F15_amortisman_ve_itfa_ytd`/`_ceyrek` (`160`/`178` eksik), `F15_capex_ytd`/`_ceyrek` (`292`/`325` eksik) + oranlar | KAP `.xls` bilanço ve nakit akışı tablolarından ayrıştırıldı; eğitim matrisinde `_q1` gecikmeli ölçekli/oran sütunları hazır. |
| **F16** | **P1** | Finansal | Faaliyet giderleri ve Ar-Ge | **CSV'de VAR (8 yeni sütun)**: `F16_pazarlama_giderleri_ytd`/`_ceyrek` (`120` eksik), `F16_genel_yonetim_giderleri_ytd`/`_ceyrek` (`8` eksik, `%99.4` dolu), `F16_ar_ge_giderleri_ytd`/`_ceyrek` (`448`/`453` eksik) + oranlar | KAP `.xls` gelir tablolarından ayrıştırıldı; eğitim matrisinde `_q1` gecikmeli oran sütunları hazır. |
| **F18** | **P1** | Finansal | Müşteri avansı ve sözleşme yükümlülüğü | **CSV'de VAR (3 yeni sütun)**: `F18_kisa_vadeli_ertelenmis_gelir_ve_avanslar` (`423` eksik), `F18_uzun_vadeli_ertelenmis_gelir_ve_avanslar` (`896` eksik), `F18_ertelenmis_gelir_kisa_aktif_orani` (`423` eksik) | Bilançodaki "Ertelenmiş Gelirler" ve 2013 öncesi "Alınan Sipariş Avansları" satırları birleştirilerek ayrıştırıldı (`ASELS`: `37/44`, `OTKAR`: `44/44` dolu). |
| **X04** | **P1** | Etkileşim | Jeopolitik risk × faaliyet karması | **Eğitim Matrisinde VAR (5 sütun)**: `X04_savunma_x_GPRC_TUR`, `X04_savunma_x_GPRD_q_mean`, `X04_ulastirma_x_GPRC_TUR`, `X04_enerji_x_GPRC_TUR`, `X04_bilisim_x_GPRC_TUR` | `C01_kap_sub_sector` vekili ile Türkiye GPR (`R01_GPRC_TUR`) ve günlük `R01_GPRD_q_mean` çarpımları [data/training_matrix_pit_2010_2020.csv](../../data/training_matrix_pit_2010_2020.csv) içinde üretildi. |
| **F17** | **P1** | Finansal | Sözleşme varlığı | **Eksik** | TFRS 15 (2018+) sonrası bilançolarda "Sözleşme Varlıkları" kaleminin ayrıştırılması. |
| **F19** | **P1** | Finansal | Net döviz pozisyonu | **Eksik** | Dipnotlarda (Yabancı Para Pozisyonu tablosu) yer alır; özet `.xls` tablosunda standart satır değildir, PDF/dipnot ayrıştırıcısı gerekir. |
| **M07** | **P1** | Makro | İlgili emtia fiyatı | **Eksik** | Brent petrol, çelik/demir cevheri, alüminyum, buğday/tarım vb. dış fiyat serilerinin indirilip sektörlerle eşlenmesi. |
| **M08** | **P1** | Makro | Sektör talep ve faaliyet göstergesi | **Eksik** | EVDS / TÜİK sektörel ciro, kapasite kullanım veya turizm/havacılık yolcu istatistiklerinin eklenmesi. |
| **C02** | **P1** | Profil | Ürün / faaliyet gelir karması | **Eksik** | TFRS 8 faaliyet bölümleri dipnotlarından gelir paylarının çıkarılması. |
| **C03** | **P1** | Profil | Yurtdışı gelir ve ihracat payları | **Eksik** | Gelir tablosu dipnotlarından yurt içi / yurt dışı satış kırılımının çıkarılması. |
| **C04** | **P1** | Profil | Satış coğrafyası ve yoğunlaşma | **Eksik** | Faaliyet raporu ve dipnotlardan ülke/bölge satış paylarının çıkarılması. |
| **C07** | **P1** | Profil | Enerji / emtia üretici-tüketici rolü | **Eksik** | Şirketlerin enerji/emtia üreticisi mi yoğun tüketicisi mi olduğunu belirten tarihsel kaynaklı profil tablosu. |
| **C09** | **P1** | Profil | Sipariş ve ifa görünürlüğü | **Eksik** | Savunma/proje şirketleri (ör. ASELS, OTKAR) için faaliyet raporlarındaki bakiye sipariş (backlog) ve yeni sözleşme verisi (`F18` bilanço vekili hazır). |
| **C10** | **P1** | Profil | Üretim kapasitesi, hacim ve birim fiyat | **Eksik** | KAP faaliyet raporlarındaki üretim/satış tonaj ve kapasite kullanım verileri. |
| **X01** | **P1** | Etkileşim | Kur × net döviz pozisyonu | **Eksik** | `F19` (net döviz pozisyonu) tamamlandığında `M01`/`M02` ile çarpılarak üretilecek. |
| **X05** | **P1** | Etkileşim | Coğrafi satış ağırlıklı ülke riski | **Eksik** | `C04` (satış coğrafyası) ve `data_gpr_export.xls` içindeki ülke bazlı GPR serileri (`GPRC_*`) eşlendiğinde üretilecek. |
| **X06** | **P1** | Etkileşim | Emtia × üretici/tüketici profili | **Eksik** | `M07` (emtia fiyatı) ve `C07` (üretici/tüketici rolü) tamamlandığında üretilecek. |
| **X07** | **P1** | Etkileşim | Kur × ihracat / yurtdışı satış | **Eksik** | `C03` (ihracat/yurtdışı satış payı) tamamlandığında `M01`/`M02` ile üretilecek. |
| **F20** | **P2** | Finansal | Borç koşulları ve korunma | **Eksik** | Dipnotlardan sabit/değişken faizli borç ve türev korunma (hedge) oranları. |
| **C05** | **P2** | Profil | Müşteri türü ve yoğunlaşması | **Eksik** | Dipnotlardan kamu/özel müşteri ve %10 üzeri tekil müşteri yoğunlaşması. |
| **C06** | **P2** | Profil | Tedarik ve ithal girdi profili | **Eksik** | Dipnot/faaliyet raporlarından ithal girdi payı. |
| **C08** | **P2** | Profil | Sözleşme fiyatlama yapısı | **Eksik** | Sabit fiyatlı vs maliyet artı / döviz endeksli sözleşme yapısı. |
| **E01** | **P2** | Olay | Olay türü, coğrafyası ve ekonomik kanalı | **Eksik** | Yapılandırılmış tarihsel olay takvimi. |
| **X08** | **P2** | Etkileşim | Olay bağlamı × ilgili şirket profili | **Eksik** | `E01` ve ilgili `C*` profilleri tamamlandığında üretilecek. |

---

## 5.1. Uygulanan Yaklaşım: Günlük/Aylık Verilerin 3 Aylık Hedeflerle Birleştirilmesi (3. Yaklaşım — MIDAS Dağılım Özeti + Nowcasting Ufukları)

Hedef değişkenlerimiz (`T01`–`T17`) **3 ayda bir (çeyreklik)** açıklanırken, kur (`M01`, `M02`), finansal stres (`R03`) ve jeopolitik risk (`R01` günlük `GPRD`) **günlük** frekanstadır. Bu frekans farkını yönetmek ve **gün geçtikçe keskinleşen tahmin** üretmek için **3. Yaklaşım** [scripts/financial_quality.py](../../scripts/financial_quality.py), [scripts/parse_and_build_dataset.py](../../scripts/parse_and_build_dataset.py) ve [scripts/build_training_matrix.py](../../scripts/build_training_matrix.py) üzerinde uygulanmıştır:

1. **Sözde-Tekrar (Pseudoreplication) Yasağı:**
   * 1.320 çeyreklik satırı 90 güne çoğaltıp aynı çeyrek bilanço hedefini ($y_q$) 90 satıra kopyalamak istatistiksel bağımsızlığı bozduğu için **yapılmamıştır**.
2. **Günlük Serilerden Çeyrek İçi Dağılım/Yörünge Özellikleri (`20 sütun`):**
   * Günlük `GPRD` (`data/external/data_gpr_daily_recent.xls`, $+7\text{ gün}$ haftalık yayın gecikmesiyle) ve aylık Türkiye GPR (`R01_GPRC_TUR`) veri hattına eklenmiştir.
   * Hafta sonu `ffill` kur değerlerinin volatiliteyi (`_q_std`) ve 90 günlük kur değişimini yapay olarak bozmaması için gerçek iş günü gözlemleri (`USDTRY_obs`, `EURTRY_obs`) ayrı korunmuş; her bilgi kesim anına ($t_0$) kadar bilinen **çeyrek içi ortalama (`_q_mean`)**, **kesim günü seviyesi (`_q_last`)**, **volatilite (`_q_std`)**, **zirve şok (`_q_max`)** ve **son 15 gün − önceki çeyrek içi günler ivmesi (`_last15d_diff`)** çıkarılmıştır.
3. **Çoklu Bilgi Kesim Ufku (Nowcasting Horizons — [data/training_matrix_pit_2010_2020.csv](../../data/training_matrix_pit_2010_2020.csv)):**
   * Her şirket–çeyrek için $t_0 \in \{+30\text{g}, +60\text{g}, +90\text{g (çeyrek sonu)}, +120\text{g (bilanço öncesi)}\}$ (`5.280 satır × 113 sütun`) üretilmiştir.
   * $+120\text{g}$ ufkunda hedef bilançosu $t_0$ tarihinde zaten açıklanmış olan **189 şirket–dönem** `already_published_at_t0 = True` ile işaretlenmiştir (değerlendirmede maskelenir).

---

## 6. Sözlükte Ayrı Bir ID Olarak Yazılmamış Olup Kanonik CSV'ye Eklediğimiz Ekstra Sütunlar (42 Sütun)

Kanonik CSV'deki **157 sütunun** **115 tanesi** doğrudan yukarıdaki `T01`–`T17` hedeflerine (YTD + çeyrek) ve sözlükteki `F* / M* / R* / C01 / X02 / X03` ailelerine karşılık gelir. Geriye kalan **42 sütun**, veri izlenebilirliği, zaman sızıntısı kontrolü ve finansal alt kırılımlar için **fazladan/destekleyici** olarak eklenmiştir:

### A. Kimlik, Kaynak, Yayın Zamanı ve Kalite Metadatası (27 Sütun — Model Girdisi Değildir)
1. `ticker`: BIST işlem kodu (30 şirket).
2. `company_name`: Şirket tam unvanı.
3. `year`: Mali yıl (`2010`–`2020`).
4. `quarter`: Mali çeyrek (`1`–`4`).
5. `observation_period`: `YYYYQ#` dönem anahtarı (ör. `2010Q1`).
6. `period_end_date`: Çeyrek sonu takvim tarihi (kanonik CSV'de $t_0$ referansı).
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
19. `qa_flags`: Kapsam/kaynak/düzeltme uyarı bayrakları (**109 satırda** dolu; `manual_unit_override`, `service_revenue_reconciled_with_gross_profit` ve `cogs_sign_normalized_from_gross_profit` dahil).
20. `available_at`: Çeyrek farkı (`YTD_q - YTD_{q-1}`) için önceki raporun yayın zamanını da kapsayan **temkinli finansal kullanılabilirlik zamanı** (modelde sızıntı kontrolü için zorunlu sütun).
21. `macro_observation_month`: Aylık makro/risk serilerinin bağlandığı gözlem ayı (`t - 1 ay`).
22. `industrial_production_observation_month`: Sanayi üretiminin bağlandığı gözlem ayı (`t - 2 ay`).
23. `ofr_observation_date`: OFR FSI için kullanılan son geçerli ABD iş günü tarihi.
24. `ofr_assumed_available_at`: OFR FSI gözleminin 2 ABD iş günü sonrası varsayılan yayın tarihi (`<= period_end_date`).
25. `gprd_observation_date`: Günlük GPRD için kullanılan son geçerli gözlem tarihi (`t0 - 7 gün`).
26. `gprd_assumed_available_at`: Günlük GPRD gözleminin 7 takvim günü sonrası varsayılan haftalık yayın tarihi (`<= period_end_date`).
27. `macro_availability_policy`: Makro gecikme ve takvim politikasını açıklayan sabit izlenebilirlik etiketi.

### B. Eklenen Yardımcı Finansal Alt Kalemler ve Türevler (15 Sütun)
1. `vergi_oncesi_kar_zarar_ytd` (`0` eksik) ve `vergi_oncesi_kar_zarar_ceyrek` (`0` eksik): `T06_vergi_gideri_geliri_*` satırının "Vergi Öncesi Kâr/Zarar" satırıyla karışmasını önlemek için ayrı ayrıştırılan vergi öncesi kâr/zarar kalemi (`%100` dolu).
2. `T07_ana_ortaklik_net_kari_ytd` ve `T07_ana_ortaklik_net_kari_ceyrek` (`140` / `142` eksik): Toplam dönem net kârından (`T07`) ayrı olarak ana ortaklık payları.
3. `T14_ana_ortakliga_ait_ozkaynaklar` (`0` eksik): Toplam özkaynaktan (`T14`) ayrı olarak ana ortaklığa ait özkaynaklar.
4. `donen_varliklar` (`8` eksik) ve `duran_varliklar` (`8` eksik): `T11_toplam_varliklar` alt bileşenleri.
5. `kisa_vadeli_yukumlulukler` (`8` eksik) ve `uzun_vadeli_yukumlulukler` (`8` eksik): `T13_toplam_yukumlulukler` alt bileşenleri.
6. `F07_finansman_geliri_ytd` (`107` eksik), `F07_finansman_geliri_ceyrek` (`110` eksik), `F07_net_finansman_ytd` (`111` eksik), `F07_net_finansman_ceyrek` (`115` eksik): Finansman giderinin (`T05`/`F08`) yanında finansman gelirini ve net finansmanı ayrı görmek için eklendi.
7. `F13_net_borc` (`139` eksik): `T12_finansal_borclar - T08_nakit_ve_nakit_benzerleri` türevi (borç bileşenlerinden biri bilinmiyorsa sahte `-nakit` üretmemek için `NaN` bırakılır).
8. `F14_borc_ozkaynak_orani` (`0` eksik): `T13_toplam_yukumlulukler / T14_toplam_ozkaynaklar` kaldıraç oranı.
9. `odenmis_sermaye` (`1` eksik), `kap_raporlanan_hbk_ytd` (`642` eksik), `hisse_basina_kar_ytd` (`141` eksik), `hisse_basina_kar_ceyrek` (`143` eksik): Raporlanan HBK ve ödenmiş sermayeye bölünen yaklaşık HBK vekili ([AGENTS.md](../../AGENTS.md) uyarınca ağırlıklı ortalama pay sayısı doğrulanmadan gerçek EPS hedefi sayılmaz).
