# Veri hattı düzeltmeleri — 8 Kasım 2026

Bilinen ayrıştırma ve hesap hataları düzeltildi; ham dosyalar yeniden indirilmeden CSV tekrar üretildi. **Bu değişiklik bütün finansal tutarların veya tarihsel yayın sürümlerinin doğrulandığı anlamına gelmez.** Açık kaynak/kapsam sorunları kalite raporunda tutulur; model eğitilmedi.

Temel alınan sürüm: arkadaşın `fix/veri-denetimi-ve-demo-model` branch'indeki `cd10910`. Önceki yerel belgeler, kod ve CSV kopyaları yedeklendi. Kök CSV kaldırıldı; tek kanonik çıktı [data/bist_bilanco_tahmini_2010_2020.csv](../../data/bist_bilanco_tahmini_2010_2020.csv).

## Düzeltilen hatalar

1. **Nakit akışı başlıkları:** “faaliyetlerine ilişkin”, “faaliyetlerinde (kullanılan) / elde edilen”, parantezler ve eski raporlardaki yazım farkları tanınıyor. Örneğin AEFES 2011Q1'de yayımlanan yatırım **−117.029.000 TL** ve finansman **42.700.000 TL** akışları artık okunuyor.
2. **Tek hücre içindeki CSV satırları:** bazı BIFF dosyalarında satırın bütün metin ve tutarları A sütununda CSV olarak tutuluyordu. Gerçek sütunlara ayrılıp okunuyor; bu onarım sayısı kaynak kaydında tutuluyor. Örneğin TOASO 2013Q1 nakit akışları bu nedenle önceki sürümde yanlış/boştu.
3. **KAREL 2012Q1:** yanlış `1e7` CFI bölmesi yerine, doğrulanmış karşılaştırmalı tutar **−4.778.913 TL** kullanılıyor; Q2 farkı **−4.925.954 TL** oluyor. CFO **11.528.269 TL**, CFF **8.800.694 TL**. Dönem başı nakit + üç akış + kur etkisi, aynı rapordaki dönem sonu nakitle uzlaşıyor. Düzeltme yalnız beklenen ham bozuk tutar veya doğrulanmış tutar için uygulanır; farklı kaynak gelirse üretim hata verir.
4. **GSDDE 2014Q1:** atlanan “Denizcilik Sektörü Hasılatı” eşlendi. Denizcilik + hizmet + finansal gelir parçaları toplamı **3.663.000 TL**; rapordaki genel brüt kâr **349.000 TL** okunuyor. Ticari ve finansal faaliyet kapsamı ayrıca işaretli; sıradan satış−maliyet eşitliği bu şirket biçimine doğrudan uygulanmıyor.
5. **Toplam/alt toplam:** genel brüt kâr ile yalnız ticari brüt kâr ayrılıyor. CCOLA 2013Q2 gibi genel toplamı sıfır, ticari alt toplamı dolu, finansal alt toplamı açıkça sıfır olan çelişkiler; eksiksiz alt toplam uzlaşmasıyla korunup kaynak çelişkisi olarak işaretleniyor.
6. **Yanlış yedekler:** nakit akışı bölümündeki son sayısal satırın toplam sayılması kaldırıldı. Toplam kâr/özkaynak, ana ortaklık kârı/özkaynağı yerine otomatik yazılmıyor. Eksik finansal gelir/gider ve borç sıfırla tamamlanmıyor.
7. **Eksik bileşenler:** kısa/uzun vadeli bileşenlerden biri bilinmiyorsa kesin toplam üretilmiyor. Örneğin uzun vadeli alacak bilinmiyorsa bilinen kısa vadeli alacak korunuyor, toplam alacak belirsiz kalıyor. Boşluk nedeni kaydediliyor.
8. **Gerçek sıfır ve çeyrek hesabı:** tek bir raporlanan sıfır, “eksik” sayılarak YTD farkıyla ezilmiyor. Q4 için sözleşme açık: yıllık YTD − dokuz aylık YTD. Böylece sıfırın eksik olduğu yönünde tahmin yürütülmüyor; ara dönemlerde raporlanmış üç aylık sıfır korunuyor ve Q4 kaynaktaki üç aylık hücre ayrıca kanıtta saklanıyor. Her değerin dönüşüm yöntemi kayıtlı.
9. **Rapor sürümü:** dosyalar bildirim tarihine göre seçiliyor; dosya adındaki büyük numara otomatik tercih edilmiyor. TTRAK gibi erken kapak + sonraki finansal içerik durumlarında seçilmiş rapor daha erken tarihe taşınmıyor.
10. **Kullanılabilirlik:** KAREL düzeltmesinin 2013 karşılaştırmalı raporla doğrulanması ve çeyrek farkının önceki rapora ihtiyaç duyması, `source_available_at` / `available_at` alanlarında temkinli biçimde izleniyor. Finansal satırın bütünü için geç tarih kullanılması bazı önceden bilinen alanları da bekletebilir; güvenli ve muhafazakâr bir ilk temsildir.
11. **Dış göstergeler:** FX değişimi 63 birleşik satır yerine 90 takvim günlük ankordan hesaplanıyor. OFR ortalaması 60 gerçek gözlemde; yayın tarihi iki ABD federal iş günü varsayımıyla eşleniyor. Ham veri önbelleğindeki eski hatalı `shift(2)` kolonuna güvenilmiyor.
12. **Tek çıktı ve yazma:** yalnız `data/` CSV'si üretiliyor. Dosya atomik değiştirilir; yazma başarısız olursa önceki dosya korunur ve işlem hata verir. Tamamlanmış üretimin manifestosu en son yazılır.

## Doluluk değişimleri

Karşılaştırma `cd10910` CSV'siyledir. Yeni boşlukların önemli bir kısmı önceki kodun eksik bileşeni sıfır sayarak kesin toplam üretmesinin kaldırılmasından gelir; bilinen alt kalemler kaybolmaz.

| Alan | Önce eksik | Sonra eksik |
|---|---:|---:|
| Çeyrek hasılat / net kâr / toplam varlık / toplam özkaynak | Her biri 0 | Her biri 0 |
| Çeyrek işletme nakit akışı | 0 | 2 |
| Çeyrek yatırım nakit akışı | 65 | 10 |
| Çeyrek finansman nakit akışı | 151 | 11 |
| Toplam ticari alacak | 38 | 750 |
| Toplam finansal borç | 17 | 139 |
| Toplam ticari borç | 98 | 860 |
| Net borç | 0 | 139 |

Örneğin uzun vadeli ticari alacak boşken kısa vadeli alacağı doğrudan toplam saymak, toplamı doğrulamaz. Bu kayıtlar dipnot/özgün rapor kontrolü gerektirir. Kaynak gerçekten sıfır veya uygulanamaz olduğunu doğrularsa ayrı durum kaydıyla tamamlanabilir. Şirketin yayımlamadığı henüz kanıtlanmamışsa neden “açıklanmamış” diye etiketlenmez.

## Kaynak ve eksiklik kayıtları

[data/quality/README.md](../../data/quality/README.md) dosyası üretilen manifest, özet ve sıkıştırılmış JSONL kanıtlarını açıklar. Şirket/yıl/çeyrek anahtarıyla finansal alan kayıtları CSV'deki kaynak dosya/hash/birim bilgilerine bağlanır. Ek bir kaynak-link CSV'si kullanıcı onayı bekleyen ayrı öneridir; bu değişiklikte üretilmedi.

110 sütunun bir bölümü kaynak ve zaman metadatasıdır; bunlar 110 model girdisi anlamına gelmez. Aday değişken sözlüğü hâlâ ayrı tutulur.

## Doğrulama ve açık işler

**23 regresyon testi**; ham AEFES/GSDDE/TOASO/CCOLA raporlarını, KAREL nakit uzlaşmasını, gerçek sıfırı, eksik bileşenleri, ileri tarihli düzeltmenin etkisini, takvim pencerelerini, atomik yazmayı ve manifest değişiklik tespitini kapsar. Testler ağ isteği veya model eğitimi yapmaz.

Üretim denetimi, kaynak/çıktı hash'leri ve hesap kontrolleri bozulduğunda `1`; üretim tutarlı olup inceleme maddeleri kaldığında `2` döner. “Uyarı yok” gibi sahte bir eğitim onayı verilmez.

Kalan işler:

- CLEBI gibi bazı ham Excel alanları gerçekten boş; özgün rapor PDF'si/dipnot ve tablo biçimi incelenmeli.
- Karma finansal/ticari faaliyetlerin gelir–maliyet–brüt kâr kapsamı normalleştirilmeli. Bu aşamada kapsamı farklı standart brüt marj boş bırakılır.
- Bazı kaynak satış/maliyet/brüt kâr farkları ve dönem–YTD uzlaşmaları incelenmeli; her fark otomatik parser hatası veya otomatik düzeltme sayılmamalı.
- KAREL için ilk yayım PDF'si veya aynı zamandaki tutar kanıtı, geriye dönük düzeltmenin tarihsel kullanımını kesinleştirmeli.
- THYAO/TOASO/SARKY birim istisnalarının özgün rapor kanıtları daha ayrıntılı kaydedilmeli.
- Makroların tarihsel ilk yayımlanan sürümleri ve gerçek yayın takvimleri yeniden kurulmadı. OFR federal takvimi açık bir varsayım; sağlayıcının tarihsel yayın kayıtları yerine geçmez.
- M03 hâlâ OECD gecelik bankalararası faiz vekili; dokümandaki ticari kredi faiziyle aynı seri değil.

Eski demo skorları yeni CSV'nin başarısı olarak kullanılmamalı. Model betiğinde yalnız kanonik dosya yolu ve finansal kullanılabilirlik sütunu güncellendi; eğitim bu çalışmanın kapsamında yapılmadı.
