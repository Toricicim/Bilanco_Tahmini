# Güncellenebilir değişken listesi

Sürüm: **0.2.0** · Son inceleme: **2026-11-08** · Durum: **taslak, eğitilmiş sonuç yok**.

Finans dışı BIST şirketlerinin açıklanmamış hedef çeyreğine ait ana finansal kalemleri tahmin etmek için yaşayan aday girdi sözlüğü. Şirket özelinde kurulmaz; savunma yalnızca aynı olayın farklı sonuç doğurabileceği faaliyetlerden biridir. Hisse fiyatı yönü bu kayıt kapsamındaki hedef değildir.

Çalışma alanı: [model öncesi / geliştirme ve eğitim](README.md). Aynı tanım sözlüğü [model sonrası tahmin ve işletimde](../model_sonrasi/README.md) de kullanılır; seçilmiş modelin kesin girdi sürümü ayrıca sabitlenir.

**Yetkili kayıt:** [degiskenler.json](degiskenler.json). Bu Markdown aynı kayıttan üretilir. Kaynak dosyayı güncelledikten sonra depo kökünde `python3 scripts/render_feature_list.py` çalıştırın; eşleşmeyi denetlemek için `--check` ekleyin. [Üretici betik](../../scripts/render_feature_list.py).

Listede **51 özellik ailesi** var: **26 P0**, **19 P1**, **6 P2**. Bunlar sütun sayısı değildir: bir aile birden fazla ham kalem, gecikme veya oran içerebilir. İlk deneyde hepsi açılmayacak.

## Kabul edilen kararlar

- GPR, GEPU ve OFR FSI ayrı girdiler olarak seçildi. Birleşik stres skoru yalnız alternatif deney olabilir.
- Tek şirket çalışması yapılmayacak. Ortak olay + tarihsel şirket profili + hedef/zaman ayrımı kullanılacak.
- Şirketlere savaşta kazanır/kaybeder etiketi verilmeyecek; etki işareti ve gecikmesi veriden öğrenilecek.
- Sektör kategorisi başlangıç bilgisi; faaliyet payı, coğrafya, finansman ve tedarik profilleri ayrıca değerlendirilecek.
- Bütün adaylar aynı anda kullanılmayacak. P0 pilot, P1 veri uygunsa ek, P2 sonraki aşama.

## Öncelik ve durumlar

- **P0:** İlk temel deney ve veri pilotu için önerilen aile; kullanımı/faydası henüz doğrulanmış değil.
- **P1:** Güvenilir kapsama ve kaynak doğrulaması varsa eklenecek aile/uzantı.
- **P2:** Dipnot, özel veri veya olay/metin altyapısı isteyen sonraki aşama.

Seçim, veri hazırlığı ve deney kanıtı ayrı tutulur. `accepted` kullanma kararı; `verified` veri doğrulaması; `locked_test_evaluated` sabit test değerlendirmesidir. Biri diğerini garanti etmez. Şimdilik bütün aileler veri eşleme aşamasındadır ve test edilmemiştir.

## Şirketlerin aynı olaya farklı tepkisi

Model için talep, maliyet, tedarik, finansman ve nakit dönüşümü ayrı kanallardır. Ortak risk göstergesi tek başına da tahmin değeri taşıyabilir; şirketler arasındaki farklı etkileri temsil etmek için önceden bilinen profille birlikte değerlendirilir; tek sektör etiketi aynı sektördeki şirket farklarını tam açıklamaz. Aşağıdaki satırlar ekonomik hipotezdir, pozitif/negatif eğitim etiketi değildir. Toplu GPR/GEPU/FSI her olayın türünü, coğrafyasını ve ürününü tek başına anlatmaz; ayrıntılı bağlam E01 sonraki aşamadır.

| Ortak olay | Şirket profili | Olası kanallar; beklenen sonuç etiketi değildir |
|---|---|---|
| Jeopolitik gerilim/çatışma | Savunma faaliyeti, siparişli üretim | Talep/sipariş ihtimali; karşı yönde girdi, ambargo, kapasite ve işletme sermayesi baskısı. İfa zamanına göre gelir; tahsilat ayrıca. |
| Aynı jeopolitik gerilim | Turizm/taşımacılık; etkilenen coğrafya ve müşteri | Talep, rota ve maliyet değişebilir; başka pazara yönelme veya rakip kaybı farklı sonuç doğurabilir. |
| Petrol/enerji fiyat artışı | Enerji üreticisi, enerji yoğun tüketici veya karma faaliyet | Satış fiyatı ve girdi maliyeti kanalları farklıdır; sözleşme ve korunma etkiler. |
| Kur hareketi | İhracat, ithal girdi, döviz borcu ve korunma dengesi | Satış, maliyet ve finansal kur farkı aynı şirkette ters yönlerde olabilir. |
| Faiz/piyasa stresi | Kısa vade, değişken faiz, nakit tamponu | Faiz gideri, kredi yenileme, yatırım ve tahsilat farklı zamanlarda değişebilir. |

## Özellik aileleri

### Finansal geçmiş ve finansal yapı

| ID / öncelik / karar | Değişken ailesi | İlk temsil | En ilgili hedefler | Kaynak |
|---|---|---|---|---|
| F01 · P0 · aday | Şirket ölçeği | Bilinen aktif; ölçek ayrıca korunur. | Bütün hedefler | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F02 · P0 · aday | Hasılat geçmişi | q−1 / q−4; sınırlı yıllık değişim. | T01, T03, T04, T07, T09, T10 | [S01](https://arxiv.org/html/2608.11327v1), [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) |
| F03 · P0 · aday | Satış maliyeti ve brüt marj | Maliyet/aktif; (hasılat−maliyet)/hasılat. | T02, T03, T04, T07 | [S01](https://arxiv.org/html/2608.11327v1), [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) |
| F04 · P0 · aday | Faaliyet kârı ve marjı | Kâr/aktif ve faaliyet marjı. | T04, T07, T15 | [S01](https://arxiv.org/html/2608.11327v1), [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) |
| F05 · P0 · aday | Dönem net kârı | q−1 / q−4; değişim/bilinen aktif. | T07, T14, T15 | [S01](https://arxiv.org/html/2608.11327v1), [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) |
| F06 · P0 · aday | İşletme nakit akışı ve tahakkuk | CFO/aktif; (net kâr−CFO)/aktif. | T07, T08, T15 | [S01](https://arxiv.org/html/2608.11327v1), [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) |
| F07 · P0 · aday | Vergi gideri/geliri | Tutar/aktif; aktif ölçekli yıllık değişim. | T06, T07 | [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F08 · P0 · aday | Finansman ve faiz giderleri | Ayrı raporlanan tutarlar/aktif. | T05, T07, T17 | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F09 · P0 · aday | Nakit ve nakit benzerleri | Bakiye/aktif; önceki karşılaştırılabilir dönem. | T08, T12, T15 | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F10 · P0 · aday | Ticari alacak | Alacak/aktif; sınırlı değişim; alacak/satış aday. | T08, T09, T15 | [S01](https://arxiv.org/html/2608.11327v1), [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) |
| F11 · P0 · aday | Stok | Stok/aktif ve yıllık değişim. | T02, T08, T10, T15 | [S01](https://arxiv.org/html/2608.11327v1), [S02](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) |
| F12 · P0 · aday | Ticari borç | Bakiye/aktif ve değişim. | T08, T13, T15 | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F13 · P0 · aday | Finansal borç ve vade dağılımı | Borç/aktif; kısa vadeli borç/aktif. | T05, T08, T12, T17 | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F14 · P0 · aday | Yükümlülük ve özkaynak | Ayrı bakiyeler/aktif. | T11, T13, T14 | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F15 · P1 · aday | Yatırım, duran varlık ve amortisman | CAPEX/hasılat; maddi ve maddi olmayan duran varlık/aktif; amortisman ayrı. | T02, T04, T11, T16 | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F16 · P1 · aday | Faaliyet giderleri ve Ar-Ge | Pazarlama, genel yönetim ve Ar-Ge giderleri; satış veya aktif ölçekli ayrı kalemler. | T04, T07, T11, T16 | [S01](https://arxiv.org/html/2608.11327v1), [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) |
| F17 · P1 · aday | Sözleşme varlığı | Bakiye/aktif ve değişim. | T01, T08, T09, T15 | [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a), [S11](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/) |
| F18 · P1 · aday | Müşteri avansı ve sözleşme yükümlülüğü | Kısa ve uzun vadeli ertelenmiş gelir / alınan avans bakiyeleri ve aktif oranı. | T01, T08, T13, T15 | [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a), [S11](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/) |
| F19 · P1 · aday | Net döviz pozisyonu | İşareti korunmuş pozisyon/aktif; mümkünse para birimi ayrımı. | T05, T07, T08, T12 | [S08](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a), [S12](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%207.pdf) |
| F20 · P2 · aday | Borç koşulları ve korunma | Önceki açıklanmış paylar ve koşullar. | T05, T07, T08, T12, T17 | [S12](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%207.pdf), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |

Tanım ve veri sınırları:

- **F01:** Son açıklanmış toplam varlık ve tutarların dönüşümünde kullanılacak pozitif ölçek. **Sınır:** Hedef dönemin aktif değeri ölçek olarak kullanılamaz.
- **F02:** Önceki satışlar ve dönemsel devamlılık. **Sınır:** Sıfır/negatif paydada büyüme oranı zorlanmaz.
- **F03:** Maliyet ve hasılat arasındaki ilişki. **Sınır:** Giderin işareti standartlaştırılmalı; brüt kâr aynı bilgiden türetilir.
- **F04:** Esas faaliyet sonucunun geçmiş seviyesi. **Sınır:** Şirketlerin esas faaliyet/FAVÖK tanımları karıştırılmaz.
- **F05:** Dönem net kârı ve ölçekli değişimi. **Sınır:** Ana ortaklık kârı ile toplam konsolide dönem kârı ayrılır.
- **F06:** Kârın nakitle desteklenmesi. **Sınır:** Kâr/CFO aynı dönem ve konsolidasyonda olmalı; basit fark tam tahakkuk ayrıştırması değildir.
- **F07:** Vergi bileşeninin seviyesi ve değişimi. **Sınır:** Efektif vergi oranı sıfıra yakın vergi öncesi kârda kullanılmaz.
- **F08:** Borçlanma ve diğer finansman giderlerinin geçmişi. **Sınır:** Finansman gideri faizden daha geniş olabilir; gelirlerle körlemesine netlenmez.
- **F09:** Şirketin raporlanmış nakit bakiyesi. **Sınır:** Bakiye bir çeyrek akışı değildir; kısıtlı nakit kapsamı kaydedilir.
- **F10:** Satışların tahsilata dönüşümünü temsil eden bakiye. **Sınır:** Sözleşme varlığı ile koşulsuz ticari alacak aynı değildir.
- **F11:** Üretim ve satış döngüsündeki stok bakiyesi. **Sınır:** Stok/maliyet oranı stok ve akış döneminin tanımı korunarak üretilir.
- **F12:** Tedarikçi finansmanı ve ödeme döngüsü. **Sınır:** Finansal borçla aynı hesap sayılmaz.
- **F13:** Kısa/uzun vadeli finansal borç ve refinansman ihtiyacı. **Sınır:** Toplam yükümlülük finansal borç değildir; kısa vadeye aktarılan uzun borç doğru eşlenir.
- **F14:** Finansal yapının iki ayrı toplamı. **Sınır:** Kontrol gücü olmayan pay kapsamı ve bilanço eşitliği tanımları tutarlı olmalı.
- **F15:** Üretim kapasitesi yatırımı ve varlık tüketimi. **Sınır:** Nakit CAPEX toplam yatırım nakit akışı veya toplam yatırım taahhüdüyle aynı değildir.
- **F16:** Faaliyet giderleri ve giderleşen/aktifleştirilen Ar-Ge. **Sınır:** Ar-Ge aktifleştirmesi kâr ve nakdi farklı etkiler; aynı kalem gibi toplanmaz.
- **F17:** İfa ile koşulsuz faturalama/tahsilat hakkı arasındaki fark. **Sınır:** Proje sektörlerinde önemli aday; ticari alacağa otomatik eklenmez.
- **F18:** Müşteri ön finansmanı ve henüz ifa edilmemiş yükümlülükler. **Sınır:** Avans nakit yaratabilir; aynı anda gelir veya kâr sayılmaz.
- **F19:** Döviz varlık/yükümlülük dengesi ve açıklanmış duyarlılık. **Sınır:** Türev/korunma kapsamı korunur; finansal araç duyarlılığı tüm operasyonel etki değildir.
- **F20:** Borç faiz türü, para birimi, sözleşmesel vade ve korunma ayrıntıları. **Sınır:** Türev nominali ekonomik korunma oranı değildir; net değer/vade temelleri farklı olabilir.

### Türkiye makrosu ve sektör koşulları

| ID / öncelik / karar | Değişken ailesi | İlk temsil | En ilgili hedefler | Kaynak |
|---|---|---|---|---|
| M01 · P0 · aday | USD/TL değişimi | İlk aday: son bilinen 90 günlük değişim. | T01, T02, T05, T07, T12 | [S06](https://evds3.tcmb.gov.tr/) |
| M02 · P0 · aday | EUR/TL değişimi | İlk aday: son bilinen 90 günlük değişim. | T01, T02, T05, T07, T12 | [S06](https://evds3.tcmb.gov.tr/) |
| M03 · P0 · aday | Ticari kredi faizi | Son yayımlanan seviye ve tek değişim özeti. | T05, T07, T12, T17 | [S06](https://evds3.tcmb.gov.tr/) |
| M04 · P0 · aday | TÜFE | Son yayımlanmış aylık yıllık değişim. | Bütün hedefler | [S06](https://evds3.tcmb.gov.tr/), [S07](https://tuik.gov.tr/Kurumsal/Veri_Takvimi), [S14](https://www.kgk.gov.tr/ContentAssignmentDetail/5079/Enflasyon-Muhasebesi-Uygulama-Rehberinin-Gu%CC%88ncellenmesi) |
| M05 · P0 · aday | Yİ-ÜFE | Son yayımlanmış aylık yıllık değişim. | T01, T02, T03, T04 | [S06](https://evds3.tcmb.gov.tr/), [S07](https://tuik.gov.tr/Kurumsal/Veri_Takvimi) |
| M06 · P0 · aday | Sanayi üretimi | Son yayımlanmış yıllık değişim ve gözlem yaşı. | T01, T02, T10, T15 | [S06](https://evds3.tcmb.gov.tr/), [S07](https://tuik.gov.tr/Kurumsal/Veri_Takvimi) |
| M07 · P1 · aday | İlgili emtia fiyatı | Sektör için önceden seçilmiş az sayıda emtia değişimi. | T01, T02, T03, T10, T15 | [S06](https://evds3.tcmb.gov.tr/), [S15](https://aclanthology.org/2024.findings-emnlp.486/) |
| M08 · P1 · aday | Sektör talep ve faaliyet göstergesi | Önceden belirlenen tek/az sayıda yayımlanmış gösterge. | T01, T04, T10, T15 | [S06](https://evds3.tcmb.gov.tr/), [S07](https://tuik.gov.tr/Kurumsal/Veri_Takvimi), [S15](https://aclanthology.org/2024.findings-emnlp.486/) |

Tanım ve veri sınırları:

- **M01:** Tahmin anına kadar gerçekleşmiş dolar kuru hareketi. **Sınır:** Gelecek çeyrek gerçekleşmiş kuru kullanılamaz; satış ve bilanço etkileri farklıdır.
- **M02:** Avro satış/maliyet/bilanço kanalı. **Sınır:** Dolar ve avro maruziyetleri birbirinin yerine varsayılmaz.
- **M03:** TL şirket finansman maliyetine yakın makro aday. **Sınır:** Şirketin gerçek kredi marjı/faiziyle aynı değildir; EVDS seri kodu eşlenecek.
- **M04:** Tüketici fiyatlarının yayımlanmış yıllık değişimi. **Sınır:** Fiyat endeksi girdisi, TMS 29 raporlama temelinin otomatik düzeltilmesi değildir.
- **M05:** Üretici fiyatları ve maliyet koşulları. **Sınır:** Sektörün gerçek girdi sepetini tam temsil etmeyebilir.
- **M06:** Genel üretim/talep koşulları. **Sınır:** Açıklama gecikmesi ve mevsimsel revizyonlar var; hedef aya göre doldurulmaz.
- **M07:** Enerji, metal veya başka temel girdinin/ürünün fiyatı. **Sınır:** Bir emtia bütün sektörleri aynı yönde etkilemez; uygun tarihsel kaynak eşlenecek.
- **M08:** İlgili sektörün üretim, tüketim veya talep bilgisi. **Sınır:** Hangi seri olduğu pilotta eşlenir; her sektörde aynı gösterge kullanılmaz.

### Hazır küresel risk ölçüleri

| ID / öncelik / karar | Değişken ailesi | İlk temsil | En ilgili hedefler | Kaynak |
|---|---|---|---|---|
| R01 · P0 · seçildi | GPR: jeopolitik risk | Son yayımlanmış aylık küresel seviye (GPR), Türkiye makale payı (GPRC_TUR) ve günlük GPRD (+7g gecikmeli) çeyrek içi dağılım özellikleri. | Bütün hedefler | [S03](https://www.matteoiacoviello.com/gpr.htm) |
| R02 · P0 · seçildi | GEPU: ekonomik politika belirsizliği | Son yayımlanmış aylık seviye; tek tanımlı sürüm. | Bütün hedefler | [S04](https://policyuncertainty.com/global_monthly.html) |
| R03 · P0 · seçildi | OFR FSI: finansal stres | Bilinen son 60 işlem günü ortalaması. | Bütün hedefler | [S05](https://www.financialresearch.gov/financial-stress-index/) |
| R04 · P1 · aday | GPR tehdit / gerçekleşen eylem ayrımı | GPRT / GPRA; toplam GPR’ye alternatif veya kontrollü ek. | Bütün hedefler | [S03](https://www.matteoiacoviello.com/gpr.htm) |

Tanım ve veri sınırları:

- **R01:** Jeopolitik tehdit ve olaylarla ilişkili haber yoğunluğu (küresel GPR, Türkiye GPRC_TUR ve günlük GPRD). **Sınır:** Aylık ay başı, günlük küresel seri haftalık (+7g gecikme varsayımı) güncellenir; GPRC_TUR 100 bazlı değil % makale payıdır.
- **R02:** Küresel ekonomik politika belirsizliği; ilk tercih PPP ağırlıklı sürüm. **Sınır:** Tarihsel ilk yayımlanma saati/sabit gecikme varsayılmaz; arşiv veya snapshot gerekir.
- **R03:** Küresel piyasa stresi ve finansman koşulları. **Sınır:** İki iş günü geriden gelir; negatif değer alabilir; revizyonlar kaydedilir.
- **R04:** Talep beklentisiyle fiilî üretim/tedarik olayını ayırabilecek alt seriler. **Sınır:** Aynı haber bilgisini çoğaltabilir; ek katkı test edilmeden birlikte tutulmaz.

### Şirketin faaliyet ve maruziyet profili

| ID / öncelik / karar | Değişken ailesi | İlk temsil | En ilgili hedefler | Kaynak |
|---|---|---|---|---|
| C01 · P0 · aday | Tarihsel sektör ve faaliyet kategorisi | Kaynaklı kategori; çok faaliyetli yapı ayrıca işaretlenir. | Bütün hedefler | [S09](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/), [S10](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%208.pdf), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |
| C02 · P1 · aday | Ürün / faaliyet gelir karması | Son açıklanmış faaliyet gelir payları ve kapsama. | T01, T02, T03, T04, T07 | [S09](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/), [S10](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%208.pdf), [S13](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html) |
| C03 · P1 · aday | Yurtdışı gelir ve ihracat payları | Kaynakta ayrı açıklanıyorsa iki ayrı pay. | T01, T02, T07, T09 | [S09](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/), [S10](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%208.pdf), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |
| C04 · P1 · aday | Satış coğrafyası ve yoğunlaşma | Açıklanmış paylar; kapsama; uygun yoğunlaşma. | T01, T04, T07, T09 | [S09](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/), [S10](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%208.pdf), [S16](https://doi.org/10.1016/j.jaccpubpol.2026.107407) |
| C05 · P2 · aday | Müşteri türü ve yoğunlaşması | Kaynaklı kategori/pay; açıklanmadıysa eksik. | T01, T07, T09, T15 | [S09](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/), [S10](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%208.pdf) |
| C06 · P2 · aday | Tedarik ve ithal girdi profili | Açıklanmış pay veya kaynaklı nitel kategori. | T02, T03, T10, T15 | [S17](https://kap.org.tr/tr/icerik/Diger/yardim), [S13](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html) |
| C07 · P1 · aday | Enerji / emtia üretici-tüketici rolü | Kaynaklı rol kategorisi; maliyet payı varsa ayrı. | T01, T02, T03, T04 | [S13](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |
| C08 · P2 · aday | Sözleşme fiyatlama yapısı | Kaynakta açıklanan şartlar ve varsa paylar. | T01, T02, T03, T04, T07 | [S11](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |
| C09 · P1 · aday | Sipariş ve ifa görünürlüğü | Backlog/TTM satış; book-to-bill=yeni sipariş_q/satış_q; ifa aralığı. | T01, T03, T07, T08, T15 | [S11](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |
| C10 · P1 · aday | Üretim kapasitesi, hacim ve birim fiyat | Sektöre uygun açıklanmış hacim/kapasite; büyüme. | T01, T02, T03, T10, T16 | [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |

Tanım ve veri sınırları:

- **C01:** Şirketin o tarihte bilinen faaliyet kategorisi. **Sınır:** Bugünkü sektör geçmişe taşınmaz; kategori gelir payı değildir.
- **C02:** Savunma/sivil, üretim/hizmet gibi açıklanmış faaliyet payları. **Sınır:** Şirket ismi veya sektör etiketiyle sayısal pay uydurulmaz; kategori ve pay ayrılır.
- **C03:** İki ayrı kavramla dış talep ve döviz satış bağlantısı. **Sınır:** Yabancı iştirakin yerel satışı Türkiye’den ihracat değildir.
- **C04:** Satışların ülke/bölge dağılımı ve kapsama. **Sınır:** TFRS 8 tam ülke matrisi garanti etmez; bölgeden ülke payı üretilmez; satış coğrafyası tedarik değildir.
- **C05:** Açıklanmış kamu/özel müşteri veya büyük müşteri yoğunlaşması. **Sınır:** Büyük müşteri kimliği zorunlu olmayabilir; ilişkili taraf payı kamu payı değildir.
- **C06:** Girdi/tedarikçi coğrafyası ve bağımlılığı. **Sınır:** Genel panelde hazır tedarik matrisi beklenmez; satış ülkesi yerine kullanılamaz.
- **C07:** Şirketin emtiayı üretme veya tüketme rolü. **Sınır:** Sektör kategorisi gerçek enerji maliyet oranı değildir; korunma ve ürün karması etkiyi değiştirebilir.
- **C08:** Sabit/endeksli fiyat ve sözleşme para birimi. **Sınır:** Fiyatlama gücü doğrudan gözlenmeyebilir; marj geçmişi bunun kesin ölçüsü değildir.
- **C09:** Yeni sipariş, bakiye ve beklenen ifa/teslimat dönemleri. **Sınır:** Bakiye ve TTM satış aynı para/ölçüm temelinde olmalı; book-to-bill pay ve paydası aynı çeyreğe ait olmalı. İmza anında otomatik gelir yok; bildirimler bütün siparişleri kapsamayabilir.
- **C10:** Talebin fiilî üretim ve satışa dönüşme imkânı. **Sınır:** Şirketler arasında ölçü birimleri farklıdır; talep kapasite doluyken hemen satışa dönüşmeyebilir.

### İsteğe bağlı olay bağlamı

| ID / öncelik / karar | Değişken ailesi | İlk temsil | En ilgili hedefler | Kaynak |
|---|---|---|---|---|
| E01 · P2 · aday | Olay türü, coğrafyası ve ekonomik kanalı | Önceden tanımlı etiketler; kaynak ve ilk açıklama zamanı. | Bütün hedefler | [S13](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |

Tanım ve veri sınırları:

- **E01:** Çatışma, yaptırım/ticaret kısıtı veya arz kesintisinin doğrulanmış bağlamı. **Sınır:** GPR tek başına olayın bütün ayrıntısını içermez. Haber/LLM toplama ayrı iş; sonradan bilinen sonuç etiketlenmez.

### Sınırlı olay–profil etkileşimleri

| ID / öncelik / karar | Değişken ailesi | İlk temsil | En ilgili hedefler | Kaynak |
|---|---|---|---|---|
| X01 · P1 · aday | Kur × net döviz pozisyonu | Uygun para birimi değişimi × önceki net FX/aktif. | T05, T07, T08, T12 | [S12](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%207.pdf), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |
| X02 · P0 · aday | Faiz × finansal borçluluk | Faiz değişimi × önceki finansal borç/aktif. | T05, T07, T12, T17 | [S06](https://evds3.tcmb.gov.tr/), [S12](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%207.pdf) |
| X03 · P0 · aday | Finansal stres × kısa vadeli borç | OFR FSI × önceki kısa vadeli finansal borç/aktif. | T05, T08, T12, T17 | [S05](https://www.financialresearch.gov/financial-stress-index/), [S12](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%207.pdf) |
| X04 · P1 · aday | Jeopolitik risk × faaliyet karması | GPR / GPRC_TUR / GPRT / GPRA (cari ve gecikmeli) × alt sektör (SAVUNMA, ULAŞTIRMA, BİLİŞİM) ve F18 avans/ertelenmiş gelir oranı. | T01, T02, T03, T04, T07 | [S03](https://www.matteoiacoviello.com/gpr.htm), [S09](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/), [S13](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html) |
| X05 · P1 · aday | Coğrafi satış ağırlıklı ülke riski | Toplam: bilinen satış payı × normalize ülke GPR. | T01, T04, T07, T09 | [S03](https://www.matteoiacoviello.com/gpr.htm), [S10](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%208.pdf), [S16](https://doi.org/10.1016/j.jaccpubpol.2026.107407) |
| X06 · P1 · aday | Emtia × üretici/tüketici profili | Emtia değişimi × rol/pay; güvenilir maliyet payı varsa ayrıca. | T01, T02, T03, T04, T10 | [S13](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |
| X07 · P1 · aday | Kur × ihracat / yurtdışı satış | İki farklı payla ayrı etkileşimler. | T01, T03, T07, T09 | [S09](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/), [S12](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%207.pdf) |
| X08 · P2 · aday | Olay bağlamı × ilgili şirket profili | Önceden seçilmiş az sayıda olay/profil etkileşimi. | Bütün hedefler | [S13](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html), [S17](https://kap.org.tr/tr/icerik/Diger/yardim) |

Tanım ve veri sınırları:

- **X01:** Kur şokunun şirketin finansal döviz dengesiyle ilişkisi. **Sınır:** Toplam net pozisyon ile tek kur yalnız vekildir; işaret dayatılmaz.
- **X02:** Finansman maliyetinin borç profiline göre değişmesi. **Sınır:** Toplam borç ilk vekildir; değişken faizli borç varsa ayrı geliştirilir; bileşenleri de modelde tut.
- **X03:** Ortak piyasa stresinin refinansman ihtiyacıyla ilişkisi. **Sınır:** Vade/likidite profili eksikse sıfır sayılmaz; risk artışı otomatik sonuç etiketi olmaz.
- **X04:** Aynı jeopolitik durumun farklı ürün/iş paylarına, alt sektörlere ve sipariş avansı yapısına yansıması. **Sınır:** Savunma gibi bir faaliyet için etki zorla pozitif yapılmaz; kategori ve F18 etkileşimi veriden öğrenilir.
- **X05:** Ülke riskinin şirketin satış pazarlarıyla eşleşmesi. **Sınır:** Eksik ülke payı yeniden 1’e normalize edilerek kapsama gizlenmez; bu tedarik riski değildir.
- **X06:** Fiyat hareketinin satış ve maliyet kanalını ayırmak. **Sınır:** Aynı emtia artışı iki rolde farklı ilişki kurabilir; işaret ve gecikme öğrenilir.
- **X07:** Döviz satış kanalını finansal döviz bilançosundan ayırmak. **Sınır:** İhracat payı net kur kazancı değildir; ithal maliyet ve korunma başka kanallar.
- **X08:** Özel olayın ürün, müşteri, pazar veya tedarik bağıyla eşleştirilmesi. **Sınır:** Tam çapraz çarpım veya olaydan sonra kazanan etiketi yok; kaynaklı bağ ve zaman gerekir.

## Hedef sözlüğü

Bunlar tahmin edilen gelecekteki kalemlerdir; yukarıdaki girdiler bunların geçmiş değerlerini de içerebilir.

| ID | Hedef | Tür |
|---|---|---|
| T01 | Hasılat | akış |
| T02 | Satışların maliyeti | akış |
| T03 | Brüt kâr | türetilmiş akış |
| T04 | Esas faaliyet kârı | akış |
| T05 | Finansman gideri | akış |
| T06 | Vergi gideri/geliri | akış |
| T07 | Dönem net kârı | akış |
| T08 | Nakit ve nakit benzerleri | dönem sonu bakiye |
| T09 | Ticari alacak | dönem sonu bakiye |
| T10 | Stok | dönem sonu bakiye |
| T11 | Toplam varlık | dönem sonu bakiye |
| T12 | Finansal borç | dönem sonu bakiye |
| T13 | Toplam yükümlülük | dönem sonu bakiye |
| T14 | Toplam özkaynak | dönem sonu bakiye |
| T15 | İşletme faaliyetlerinden nakit akışı | akış |
| T16 | Yatırım faaliyetlerinden nakit akışı | akış |
| T17 | Finansman faaliyetlerinden nakit akışı | akış |

## Zaman ve veri sözleşmesi

- q hedef mali çeyrek, t0 sabit tahmin anıdır. Finansal referanslar q−1 ve q−4 ancak available_at ≤ t0 ise kullanılabilir. Son rapor t ve hedef t+1 ise aynı hedefin geçen yılki karşılığı t−3 olur.
- q−1 açıklanmadıysa sonradan açıklanan veriyle doldurulmaz. Son kullanılabilir değer ve yaşı ayrıca tutulabilir. Eğitim etiketleri de eğitim kesiminde açıklanmış olmalı.
- İlk adayda az sayıda referans ve dönüşüm kullanılır; 12 gecikme × tüm oranlar × bütün etkileşimler açılmaz. İlk profil etkileşim bütçesi en fazla 3–5 aile.
- Kâr büyümesi sıfır/negatif paydada zorlanmaz; değişim/bilinen aktif adaydır. Negatif tutara log uygulanmaz. Ölçek ve uç değer işlemleri yalnız eğitimde öğrenilir.
- Bilanço bakiyesi ile gelir/nakit akışı ayrılır. Para birimi, konsolidasyon ve satın alma gücü temeli eşleştirilir; farklı TMS 29 temellerindeki YTD tutarlar doğrudan çıkarılmaz.
- GPR günlük gözlemi yayımlanma gününde bilinmeyebilir; GEPU için sabit tarih uydurulmaz; OFR iki iş günü geriden gelir. Güncel veri dosyası tarihsel vintage değildir.
- Profil payları ve sektör sınıfı tarihsel sürümle kullanılır. Yeni yıllık profil geçmişe taşınmaz; yaş/kapsam tutulur. İhracat, yurtdışı hasılat, satış coğrafyası ve tedarik coğrafyası ayrılır.
- Eksik sıfır değildir. not_disclosed, not_applicable, not_extracted, unavailable_vintage ayrılır. Payı bilinmeyen coğrafya gizlice sıfır veya yeniden normalize edilmiş tam kapsama yapılmaz.
- Ağaç modelleri etkileşimleri kendileri öğrenebilir. Çarpım sütunlarının ek katkısı ayrıca ölçülür; uzman görüşüyle dayatılan etki varsa öğrenilmiş tahmin diye sunulmaz.
- Yıllık değişim, gözlemin kendi mali çeyreğinin dört çeyrek öncesine göre hesaplanır: son bilinen r için değer(r) − değer(r−4). r=q−1 ise karşılık q−5 olur. Hedef q için q−4 mevsimsel referansı ayrı kavramdır.
- depends_on aile düzeyindeki ilişkili girdileri listeler. dependency_policy=all seçilen temsilin bütün girdilerini, channel_specific ise kur/ürün/coğrafya kanalına uygun alt kümeyi gerektirir; ilgisiz para birimi veya tedarik alanı zorunlu değildir.

Her ham gözlemde tutulacak alanlar:

| Alan | Anlamı |
|---|---|
| `feature_id` | Bu sözlükteki değişken ailesi. |
| `entity_id` | Şirket/ülke veya ortak seri kimliği. |
| `observation_period` | Verinin anlattığı dönem; t0 ile aynı şey değildir. |
| `first_published_at` | İlk kamuya açıklama zamanı; mümkünse saat ve saat dilimiyle. |
| `available_at` | Operasyonel olarak modelin kullanabileceği zaman. |
| `vintage` | Kullanılan sürüm veya snapshot kimliği. |
| `value_and_unit` | Değer, para/miktar birimi ve yüzde/puan ayrımı. |
| `period_type` | Bakiye, akış, profil veya olay. |
| `consolidation` | Konsolide/solo ve raporlama kapsamı. |
| `price_level_date` | Enflasyon düzeltmesinin satın alma gücü tarihi. |
| `source_document_id_url` | Kaynak bildirim kimliği ve bağlantısı. |
| `page_or_note` | Sayfa/dipnot veya seri metaverisi. |
| `coverage_ratio` | Satış/ülke/segment kapsamının ölçüsü. |
| `age_days` | t0 anındaki gözlem eskiliği. |
| `is_proxy` | Gerçek ölçü yerine vekil kullanılıp kullanılmadığı ve tanımı. |
| `missing_reason` | not_disclosed / not_applicable / not_extracted / unavailable_vintage. |
| `extraction_method_reviewer` | Otomatik/elle çıkarım yöntemi ve doğrulayan kişi. |

## Karşılaştırma planı

| Deney | Girdi | Sorduğu soru |
|---|---|---|
| E0 | Finansal geçmiş + mali takvim / tarihsel sektör | Mevsimsel basit tahmin ve son değer kıyasını geçiyor mu? |
| E1 | E0 + küçük Türkiye makro kümesi | Yerel koşullar ek bilgi sağlıyor mu? |
| E2 | E1 + ayrı GPR, GEPU ve OFR FSI | Küresel riskin ek katkısı var mı? |
| E3 | E2 + doğrulanmış şirket profillerinin ana etkileri | Profil tek başına ne katıyor? |
| E4 | E3 + önceden seçilmiş 3–5 etkileşim | Aynı olayın şirketlere farklı yansımasını temsil etmek ne katıyor? |
| E5 | E1 + eğitimden ölçeklenen birleşik stres özeti | Ayrı endeksli E2’ye alternatif tek skor nasıl? |

Karşılaştırmalar aynı şirket–hedef–tarih örnekleminde ve benzer ayar bütçesiyle yapılır. Önce takvim çeyrekleri bölünür; bütün şirket satırları o tarih bloklarına atanır. Ortak risk değerinin çok şirkete kopyalanması bağımsız makro örneklem sayısını artırmaz. Kalem bazında hata, mevsimsel kıyasa göre fark, kapsama ve çeyrek bloklu belirsizlik raporlanır. SHAP açıklamaya yardımcıdır; ek katkı veya nedensellik kanıtı değildir. Kriz ve başarılı örnekler test sonucuna bakılarak seçilmez.

## İki haftalık veri pilotu

Dört farklı ekonomik profilden ikişer şirket: 8 şirket × 4 çeyrek ve her şirketin o tarihte erişilebilir yıllık rapor/dipnotu. İlk hafta P0 kalemleri, birim ve yayın tarihleri; ikinci hafta 5–8 profil ailesinin kapsama ve çıkarım süresi. İki kişi kaynak kontrolü yapar. Çıktı tahmin başarısı değil; hangi adayın gerçekten toplanabildiği ve hangi önceliğe alınacağıdır.

## Listeyi güncelleme

- Önce degiskenler.json güncellenir, sonra üretici betik çalıştırılır. Markdown elle değiştirilmez; --check eşleşmeyi doğrular.
- Yeni aday benzersiz ID, tanım, ilk temsil, kaynak, hedef, erişilebilirlik ve eksik politikasıyla eklenir.
- selection_status, data_status ve evidence_status bağımsız güncellenir. Seçili endeksin yararlı olduğu otomatik işaretlenmez.
- Reddedilen ID silinmez; gerekçe decision_note alanına yazılır. Tanım değişince definition_version ve change_log artırılır.
- Kaynak veya tanım değişirse owner / last_reviewed ve veri kapsamı kaydedilir. P1/P2 ancak güvenilir pilot sonucuyla öne alınır.
- Bankalar/sigortalar ayrı tablo ve model kapsamıdır. Bu ilk sözlük finans dışı evren içindir.

## Beş uzman incelemesinin kapsamı

- **Finansal değişkenler:** 20 aile, q−1/q−4 referansı, stok/akış ve muhasebe ölçeği.
- **Makro ve hazır risk ölçüleri:** Üç ayrı risk, az sayıda yerel makro, yayım/sürüm kontrolü.
- **Genel sektör ve şirket maruziyeti:** Tek şirket odağı kaldırıldı; faaliyet, coğrafya, talep–maliyet–tedarik–finansman kanalları.
- **Veri uygulanabilirliği:** KAP ilk açıklama sınırı; ihracat/yurtdışı ayrımı; ülke/müşteri/tedarikte eksik veri ve pilot.
- **Deney ve kayıt tasarımı:** Seçim/hazırlık/kanıt ayrımı; işaret dayatmama, sınırlı etkileşim ve tarih blokları.

Bu incelemeler model başarısı kanıtı veya beş bağımsız deney değildir; tasarım kontrolüdür.

## Kaynaklar ve kanıt sınırı

- **S01:** [Forma: yöntem ve sonuçlar](https://arxiv.org/html/2608.11327v1) — Çok kalemli finansal tahmin; BIST başarısı kanıtı değil.
- **S02:** [Cao–You, 2021 açık taslak](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Cao%20and%20You%2020210120.pdf) — Yıllık kâr için finansal kalem ve değişimler; burada 2024 yayımlanan sürümün tamamı doğrulanmış sayılmıyor.
- **S03:** [GPR resmi veri ve sürüm arşivi](https://www.matteoiacoviello.com/gpr.htm) — GPR, tehdit/eylem ayrımı, yayım ve revizyonlar; özellik faydası ayrıca test edilecek.
- **S04:** [GEPU resmi açıklaması](https://policyuncertainty.com/global_monthly.html) — Aylık belirsizlik; PPP sürümü ilk tercih. İlk yayımlanma tarihleri ayrıca doğrulanmalı.
- **S05:** [OFR Financial Stress Index](https://www.financialresearch.gov/financial-stress-index/) — Günlük stres ve iki iş günlük gecikme; revizyon kontrolü gerekiyor.
- **S06:** [TCMB EVDS 3](https://evds3.tcmb.gov.tr/) — Makro kaynak adayı; seri kodları ve tarihsel sürümler henüz eşlenmedi.
- **S07:** [TÜİK veri takvimi](https://tuik.gov.tr/Kurumsal/Veri_Takvimi) — Gerçek yayım takvimi; güncel dosya eski sürüm garantisi değildir.
- **S08:** [KAP site kılavuzu](https://www.kap.org.tr/tr/api/about/content-file/402832a195b3017d0195bd17e2e07e9a) — Kalem sorgusu ilgili dönemin son yayımlanan cari sütununu içerir; ilk açıklama için kaynak bildirime gidilir.
- **S09:** [IFRS 8 Operating Segments](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/) — Faaliyet, coğrafya ve büyük müşteri açıklamaları; tam ülke/müşteri matrisi garantisi yok.
- **S10:** [2026 TFRS 8, özellikle §33–34](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%208.pdf) — Ülke içi/yabancı ve önemli ülkeler; büyük müşteri eşiği kimliğin zorunlu açıklanması anlamına gelmez.
- **S11:** [IFRS 15 Revenue from Contracts with Customers](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/) — Hasılat ifa yükümlülüğüne göre zaman içinde veya belirli anda tanınabilir; imza anında otomatik gelir değildir.
- **S12:** [2026 TFRS 7](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/TMS_TFRS_Setleri/2026/Kirmizi_Kitap/TFRS/TFRS%207.pdf) — Finansal araçların vade ve piyasa riski açıklamaları; bütün operasyonel maruziyetle aynı değil.
- **S13:** [Fed: sektörlerin farklı jeopolitik risk maruziyeti](https://www.federalreserve.gov/econres/notes/feds-notes/measuring-geopolitical-risk-exposure-across-industries-a-firm-centered-approach-20250829.html) — Tehdit/fırsat ve sektör farklılığı; sonuçlar hisse tepkileri için, bizim finansal tahmin kazancımız değil.
- **S14:** [KGK enflasyon muhasebesi rehberi](https://www.kgk.gov.tr/ContentAssignmentDetail/5079/Enflasyon-Muhasebesi-Uygulama-Rehberinin-Gu%CC%88ncellenmesi) — Satın alma gücü ve raporlama temeli kontrolü; basit TÜFE bölmesi tam TMS 29 motoru değildir.
- **S15:** [Koval ve diğerleri, Financial Forecasting from Textual and Tabular Time Series](https://aclanthology.org/2024.findings-emnlp.486/) — Muhasebe, makro ve metnin kâr sürprizi görevindeki katkısı; üç tablonun bütün kalemleri için kanıt değil.
- **S16:** [Coğrafi segmentlerle şirket jeopolitik riski, 2026](https://doi.org/10.1016/j.jaccpubpol.2026.107407) — Yayınevi özeti/girişi incelendi; satış ağırlıklı risk mevcut bir fikir. Tam PDF incelenmedi.
- **S17:** [KAP bildirim ve finansal rapor sorguları](https://kap.org.tr/tr/icerik/Diger/yardim) — Finansal/operasyonel ham kaynaklar; şirket bazında rapor/dipnot ve kapsam pilotta doğrulanacak.
- **S18:** [SHAP: tahmin ve nedensellik sınırı](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html) — SHAP, değişkenin ek test değerini veya olayın nedensel etkisini kanıtlamaz.

## Geliştirici deneyimi notları

İki uygulama yazısının tam metni ve yorumları incelendi; ikisinde de yorum bulunmadı. İlki bir veri sağlayıcısının deneyimidir; bu inceleme akademik kanıt veya topluluk uzlaşısı değildir.

- 🗂️ [How to Build a Point-in-Time Fundamentals Database from SEC EDGAR (and When Not To)](https://dev.to/tradevodata/how-to-build-a-point-in-time-fundamentals-database-from-sec-edgar-and-when-not-to-2gn6) [@tradevodata](https://dev.to/tradevodata) — İlk açıklama ve sonraki düzeltmeleri ayırma deneyimi, kayıttaki available_at ve vintage alanlarını destekliyor. 🔗 [Read Full Discussion on DEV](https://dev.to/tradevodata/how-to-build-a-point-in-time-fundamentals-database-from-sec-edgar-and-when-not-to-2gn6)
- 🔧 [Feature Stores Version Tables. They Should Version Transforms](https://dev.to/aiexplore369zoho/feature-stores-version-tables-they-should-version-transforms-3gnm) [@aiexplore369zoho](https://dev.to/aiexplore369zoho) — Aynı isimli özelliğin farklı pencere/eksik kurallarıyla hesaplanabilmesi, tanım ve dönüşüm sürümünü de kaydetmemizi gerekçelendiriyor. 🔗 [Read Full Discussion on DEV](https://dev.to/aiexplore369zoho/feature-stores-version-tables-they-should-version-transforms-3gnm)

## Değişiklik kaydı

- **0.2.0 / 2026-11-08:** T06 vergi/EBT ayrımı, T15 işletme nakit akışı üst-toplam önceliği ve OCI bölüm koruması düzeltildi; mevcut XLS dosyalarından F15, F16 ve F18 kalemleri çıkarıldı; GPRC_TUR, günlük GPRD (+7g gecikme) ve çeyrek içi dağılım özellikleri ile P0-C çok ufuklu nowcasting eğitim matrisi (X04 etkileşimleri dahil) eklendi.
- **0.1.0 / 2026-11-06:** Kullanıcının istediği beş uzman incelemesiyle ilk genel aday listesi. GPR/GEPU/OFR seçili; tek şirket odağı yok; hiçbir aday için test başarısı iddia edilmiyor.
