# Yeni CSV denetimi — cd10910 — 7 Kasım 2026

**Karar: Önceki CSV'ye göre belirgin düzelme var; fakat yeni CSV henüz tamamen doğru veya yayın zamanı güvenli kabul edilemez.** KAREL yatırım nakit akışında yanlış düzeltme, GSDDE hasılatında atlanan satır ve OFR zaman eşlemesinde kalan ihlaller doğrudan doğrulandı. TTRAK'ta yayın zamanı ile seçilmiş rapor sürümü ayrıca uzlaştırılmalı.

İncelenen branch: `origin/fix/veri-denetimi-ve-demo-model`, commit: `cd10910`. İnceleme CSV ve üretim kaynaklarıyla sınırlı tutuldu; demo modeli çalıştırılmadı veya değerlendirilmedi. [Sayısal sonuçlar ve kayıt anahtarları](veri_denetimi_cd10910_2026-11-07.json).

## Çalışmaların korunması

Mevcut `main` checkout'u ve önceki yerel değişiklikler korundu. Yeni branch ayrı bir detached worktree'de incelendi: `../reviews/csv-cd10910/`. Bu belge incelenen sürümü anlatır; mevcut ana checkout'taki eski CSV değiştirilmedi.

İşlem öncesinde 7 yerel dosyanın kopyası, SHA-256 manifestosu ve Git patch'leri `../local_backups/csv-inceleme-oncesi-20261107-192609/` altında saklandı. Önceki çalışma; rapor, JSON denetim çıktısı, `scripts/audit_dataset.py` ve dört README düzenlemesinden oluşuyordu. Bu 7 dosyanın hash'leri inceleme sonunda da başlangıçtakiyle aynı kaldı. Önceki rapor ve arkadaşın branch'indeki rapor/betik aynı yolları kullandığı için bu yeni inceleme farklı dosya adlarıyla saklandı.

## Düzelmiş olanlar

| Kontrol | Önceki kök CSV | Yeni CSV |
|---|---:|---:|
| Gözlem / sütun | 1.320 / 92 | 1.320 / 96 |
| Eksik yayın tarihi | 38 | **0** |
| Eksik bildirim numarası | 50 | **0** |
| Kök ve data/ kopyaları | Farklı metadata | **Byte düzeyinde aynı** |
| Sonsuz sayısal değer | 10 | **0** |
| >20 kat / <1/20 komşu dönem varlık sıçraması | 6 | **0** |
| Mutlak çeyrek nakit akışı / varlık >10 | 9 hücre | **0** |

Yeni CSV SHA-256: `0b40c3c0308f61d6516602209b275c90d5382c36e45997dcbe7f641f4df3e133`.

Dört demo hedefi (çeyrek hasılat, çeyrek net kâr, toplam varlık, toplam özkaynak) 1.320 satırda dolu. Yeni dört kolon: ödenmiş sermaye, KAP'ta raporlanan HBK, hesaplanan YTD HBK ve hesaplanan çeyreklik HBK. Hesaplanan HBK, ağırlıklı ortalama pay sayısı doğrulanmadan gerçek EPS sayılmamalı.

Güncel parser tüm ham dosyalar üzerinden **yalnız bellekte** yeniden çalıştırıldı. Üretilen 1.320 × 96 tablo, kaydedilmiş CSV ile aynı şemayı verdi; sayısal alanlarda `rtol=1e-10, atol=1e-6`, metinlerde eksik/boş normalizasyonu ile fark bulunmadı. Kaynak CSV'lere yazılmadı. Bu, kod–çıktı uyumunu doğrular; finansal doğruluğu tek başına doğrulamaz.

## P1-01 — KAREL yatırım nakit akışı 10 kat hatalı düzeltilmiş

| Alan | CSV'de | Doğrulama için kullanılan karşılaştırmalı raporda |
|---|---:|---:|
| KAREL 2012Q1 `T16_yatirim_nakit_akisi_ytd` ve `_ceyrek` | **−47.789.133 TL** | **−4.778.913 TL** |

[KAREL 2013Q1 ham XLS](https://github.com/Toricicim/Bilanco_Tahmini/blob/cd10910/data/kap_raw_xls/KAREL_2013_Q1.xls), `Sheet1!D192`, “Önceki Dönem” sütununda yatırım faaliyetlerinden net nakdi **−4.778.913 TL** gösteriyor. Sütunun dönemi `D152`'de **31.03.2012**. Aynı karşılaştırmalı sütunda CFO `D181` = **11.528.269 TL**.

[Branch parser'ı, satır 839–840](https://github.com/Toricicim/Bilanco_Tahmini/blob/cd10910/scripts/parse_and_build_dataset.py#L839), bozuk CFI hücresini CFO ile aynı `1e7` bölenine bölüyor. Sonuç bu nedenle 10 kat büyük. Arkadaşın denetim belgesi doğru karşılaştırmalı tutarı yazsa da gerçek CSV farklı tutarı içeriyor.

Bu fark sonraki çeyreğe de taşınıyor: 2012Q2 CFI YTD = **−9.704.867 TL** iken, CSV çeyreklik CFI'yi **+38.084.266 TL** hesaplıyor. Karşılaştırmalı Q1 tutarıyla fark **−4.925.954 TL** olur.

**Gerekli işlem:** düzeltmeyi kaynak hücre ve onaylı tutarla tanımlamak; sonraki çeyrek türevlerini yeniden hesaplamak. 2013 karşılaştırması tek başına 2012 ilk yayım sürümünün doğrulanması değildir; ilk rapor/PDF veya aynı ilk raporun nakit uzlaşmasıyla tarihsel sürüm ayrıca doğrulanmalıdır. Bu incelemede CSV düzeltilmedi.

## P1-02 — GSDDE 2014Q1 denizcilik hasılatı atlanıyor

[GSDDE 2014Q1 ham XLS](https://github.com/Toricicim/Bilanco_Tahmini/blob/cd10910/data/kap_raw_xls/GSDDE_2014_Q1.xls), **Bin TL** biriminde şu satırları içeriyor:

| Satır | Ham değer | TL karşılığı |
|---|---:|---:|
| Grup içi hizmet faaliyetlerinden gelirler | 74 | 74.000 |
| **Denizcilik Sektörü Hasılatı** | **3.538** | **3.538.000** |
| Finans sektörü faaliyetleri hasılatı | 51 | 51.000 |

CSV `T01_hasilat_ytd` ve Q1 `_ceyrek` = **125.000 TL**; yalnız 74 + 51'i topluyor. Denizcilik hasılatı eklenmiyor. [Parser, satır 490–493](https://github.com/Toricicim/Bilanco_Tahmini/blob/cd10910/scripts/parse_and_build_dataset.py#L490) “denizcilik sektörü gelirleri” ifadesini tanıyor, “denizcilik sektörü hasılatı” ifadesini tanımıyor.

Brüt kârda da kapsam karışıklığı sürüyor: 2014Q1 CSV **171.000 TL ticari brüt kârı** alırken ham tabloda toplam brüt kâr **349.000 TL**. 2016Q1'de CSV **−3.606.000 TL ticari brüt kârı**, kaynak toplam brüt kârı ise **−3.734.000 TL**. Finansal faaliyet gelirlerini hasılata ekleyip yalnız ticari brüt kârı almak aynı kapsamı temsil etmiyor.

**Gerekli işlem:** etiket varyantlarını kapsayan, toplam ve alt toplamları ayıran açık eşleme; ticari ve finansal faaliyetlerin hangi hedef tanımına dahil edildiğinin tutarlı seçimi. Bu, ilk demonun hasılat hedefini doğrudan etkiliyor.

## P1-03 — TTRAK'ta ilk tarih ile seçilmiş bildirim eşleşmiyor

| Kayıt | CSV `first_published_at` | CSV kimliğine ait bildirim / finansal bölüm tarihi |
|---|---|---|
| TTRAK 2010Q1, bildirim `120510` | 27.04.2010 18:37:49 | **28.06.2010 23:54:29** |
| TTRAK 2014Q2, bildirim `407025` | 06.08.2014 17:46:59 | **08.01.2015 17:49:07** |

Ham BIFF dosyalarının başında erken duyuru başlıkları, finansal bölümünde ise sonraki bildirim tarihleri bulunuyor. [Parser, satır 847–850](https://github.com/Toricicim/Bilanco_Tahmini/blob/cd10910/scripts/parse_and_build_dataset.py#L847), farklı aday tarihlerin minimumunu seçip dosyanın bildirim kimliğini koruyor.

Bu karşılaştırma finansal tutarların iki sürümde kesin değiştiğini kanıtlamaz; **tutar–kaynak–yayın zamanı eşleşmesinin doğrulanmadığını** gösterir. İlk tarihin dolu olması ve dönem sonundan 150 günden az uzakta olması, doğru point-in-time veri kanıtı değildir. İlk dosya sürümü veya tutarların sürümler arasında eşitliği doğrulanmalıdır.

## P1-04 — OFR'de iki satır hâlâ iki iş günü sayılıyor

OFR'nin [resmî yayın kuralı](https://www.financialresearch.gov/financial-stress-index/) iki iş günü gecikmedir. Yeni parser gecikmesiz ham FSI yerine `OFR_FSI_avail` kullanmaya geçmiş; ancak bu hazır kolon eski birleşik takvimde `shift(2)` ile oluşturulmuş. Birleşik günlük tabloda **427 hafta sonu satırı** var.

En az **4 farklı çeyrekte / 120 şirket–çeyrekte** CSV'deki FSI'nin kaynak günü, t0'dan yalnız bir hafta içi iş günü önce:

| t0 | Kullanılan FSI gözlem günü | Takvim ilişkisi |
|---|---|---|
| 30.09.2013 | 27.09.2013 | Cuma → Pazartesi |
| 31.03.2014 | 28.03.2014 | Cuma → Pazartesi |
| 30.06.2014 | 27.06.2014 | Cuma → Pazartesi |
| 30.09.2019 | 27.09.2019 | Cuma → Pazartesi |

Kontrol yalnız hafta sonlarını ayırdı; ABD tatilleri hesaba katıldığında başka durumlar da çıkabilir. İki iş günü kuralını sağladığını iddia etmek için kaynak/gerçek yayın takvimiyle eşleme gerekir. Aylık serileri sabit 1/2 ay kaydırmak da geçmiş revizyonları ve endeksin o tarihte mevcut sürümünü otomatik çözmez.

## Kalan diğer kalite noktaları

- Brüt kâr eşitliğinde 1 TL üzeri **27 YTD bayrağı** sürüyor: TUPRS 13, GSDDE 12, ALCTL 1, RYSAS 1. Bunların hepsi otomatik parser hatası sayılamaz; birim yuvarlaması ve kaynak biçimi incelenmeli.
- Çeyrek toplamı–Q4 YTD farkı hasılatta **40**, net kârda **52 şirket-yılda** 1 TL üzerinde; %1'i aşan sayılar **20 / 25**. Sürüm/çeyrek yöntemiyle uzlaştırılmalı; körlemesine yeniden hesaplanmamalı.
- Finansal borcu eksik **17 satırda** net borç, borç sıfır kabul edilerek `−nakit` hesaplanıyor. Eksik borç, sıfır borç anlamına gelmiyor.
- Yatırım nakit akışı **65**, finansman nakit akışı **151 satırda** eksik. Sanayi üretimi **2015Q1'in 30 şirketinde** eksik. İlk dört hedefin dolu olması bütün veri setinin eksiksiz olduğu anlamına gelmez.
- M03 hâlâ gecelik OECD bankalararası faizidir; ticari kredi faizi değildir. “90 günlük” kur değişimi hâlâ 63 birleşik veri satırından hesaplanıyor; çeyrek sonlarında ortalama **79,7 takvim günü** kapsıyor. FSI'nin 60 satır ortalaması ortalama **52,7 dolu gözlem** içeriyor.
- Branch'teki `audit_dataset.py` çalıştırıldığında “BAŞARILI” diyor; ancak finansal satır eşlemesini, çeyrek/YTD uzlaşmasını veya gerçek yayın takvimini doğrulamıyor. Bu mesajın kapsamı temel doluluk ve kaba büyüklük kontrolleriyle sınırlı.

## Sonuç ve düzeltme sırası

1. KAREL CFI onaylı tutarını ve etkilenen Q2 farkını düzeltmek.
2. GSDDE hasılat varyantını ve gelir–maliyet–brüt kâr kapsamını düzeltmek; eşlemenin etkilendiği tüm dönemleri taramak.
3. İlk yayın zamanı ile seçilmiş finansal sürümü TTRAK örneklerinden başlayarak uzlaştırmak.
4. OFR için gerçek iş günü/yayın takvimi; makrolar için açık availability/vintage kaydı oluşturmak.
5. Eksik borçtan net borç üretmemek; bu gerçek hata örneklerini denetim kapsamına eklemek.

**Bu sürüm önceki veriden daha iyi bir temel; fakat “tüm sorunlar kalıcı çözüldü” sonucu desteklenmiyor.** İlk iki madde doğrudan tutar hatası, sonraki maddeler zaman güvenilirliği ve anlam tutarlılığı sorunu. Yalnız kaba uç değerlerin kaybolması doğruluk kanıtı değil. İnceleme kapsamında kod/CSV onarımı, model eğitimi, branch birleştirmesi veya push yapılmadı.
