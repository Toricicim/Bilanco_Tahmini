# Bilanço Tahmini

BIST şirketlerinin sıradaki açıklanacak finansal raporlarındaki ana kalemleri makine öğrenmesiyle tahmin etmeyi amaçlayan araştırma projesi.

Hedef; gelir tablosu, bilanço ve nakit akışındaki kalemleri aralarındaki muhasebe ilişkilerini gözeterek birlikte tahmin etmek. EPS (hisse başına kâr), bu sonuçlardan hesaplanabilecek göstergelerden biri.

**Mevcut durum:** Kaynak araştırması ve yöntem karşılaştırması tamamlandı. 30 şirketin 2010–2020 döneminden 1.320 şirket–çeyrek gözlemi [tek kanonik CSV](data/bist_bilanco_tahmini_2010_2020.csv) altında tutuluyor. [Veri hattı düzeltmeleri](docs/model_oncesi/VERI_HATTI_DUZELTMELERI_2026-11-08.md) 23 regresyon testiyle doğrulandı; kaynak kapsamı ve tarihsel yayın sürümü incelemesi sürüyor. Üretime hazır model veya çalışan tahmin uygulaması henüz bulunmuyor.

## Tahmin kapsamı

İlk sürüm için planlanan ana çıktılar:

| Finansal tablo | Hedef kalemler |
|---|---|
| Gelir tablosu | Ciro, brüt kâr, faaliyet kârı, FAVÖK, ana ortaklık net kârı |
| Bilanço | Nakit, ticari alacaklar, stoklar, duran varlıklar, kısa ve uzun vadeli finansal borçlar, ticari borçlar, özkaynak |
| Nakit akış tablosu | İşletme faaliyetlerinden nakit akışı, yatırım harcamaları, nakitteki net değişim |

Bazı temel kalemler modelle tahmin edilecek; brüt kâr, marjlar ve EPS gibi türetilmiş sonuçlar uygun hesaplarla üretilecek. Bilanço eşitliği ve tablolar arası bağlantılar ayrıca kontrol edilecek. Banka ve sigorta şirketleri için ayrı kalemler ve modeller gerekecek.

## İki çalışma alanı ve belgeler

| Alan | İşler | Rehber |
|---|---|---|
| **Model öncesi: geliştirme/eğitim** | Makaleler, yöntemler, geçmiş veri, değişken seçimi, eğitim ve dönem dışı doğrulama | [Model öncesi](docs/model_oncesi/README.md) |
| **Model sonrası: ürün/işletim** | Site, API, veri güncelleme, yeni tahmin, rapor saklama ve performans izleme | [Model sonrası](docs/model_sonrasi/README.md) |

İlk taraf doğrulanmış model paketini üretir; ikinci taraf yeni veriyi bu paketle işler. Yeni model gerektiğinde geliştirme/eğitim sürecine geri dönülür. Veri yenileme, rapor yenileme ve model eğitimi aynı işlem değildir.

Başlıca belgeler: [İstenilen Hedef](docs/model_sonrasi/ISTENILEN_HEDEF.md), [Sistem Mimarisi](docs/model_sonrasi/SISTEM_MIMARISI.md), [Model Yaşam Döngüsü](docs/model_sonrasi/MODEL_YASAM_DONGUSU.md), [güncellenebilir değişken listesi](docs/model_oncesi/DEGISKEN_LISTESI.md).

6 Kasım 2026 tarihli araştırmada 16 GitHub projesi değerlendirildi. Proje/makale incelemeleri, ek sözlükler, HTML dışa aktarımı, PDF/ZIP arşivleri ve kaynak kayıtları model öncesi klasörüne taşındı. [Bütün belgeler](docs/README.md).

## İncelenen başlıca yaklaşımlar

- **Forma:** Finansal kalemleri ve gelecek dönemleri birlikte işleyen özel Transformer.
- **Quarterly EPS Forecast Study:** Gecikmeli finansal özelliklerle OLS ve gradient boosting.
- **EPS Forecasting:** Klasik ML, zaman serisi ağları ve Chronos-2 karşılaştırmaları; veri zamanı kontrolleri ve model birleştirme.
- **Zincirlenmiş LightGBM:** Önce tahmin edilen kalemleri sonraki kalemlerin modellerinde kullanma.

Kaynak projelerde bildirilen başarılar bu depoda yeniden üretilmedi. BIST verisi üzerindeki yöntem seçimi, ortak veri ve test dönemlerinde yapılacak karşılaştırmayla belirlenecek.

## Geliştirme planı

**Model öncesi:** Kaynak ve yayın zamanı doğrulanmış geçmiş veriyi hazırlamak; dönem/birim/enflasyon temellerini eşlemek; basit kıyasları ve ML modellerini dönem dışında karşılaştırmak; model, girdi şeması ve dönüşümleri sürümlü paket olarak teslim etmek.

**Model sonrası:** Katalog ve şirket sayfasını kurmak; ilk hazırlığı arka plan işine almak; hazır raporu saklayıp göstermek; yeni verilerle aynı model üzerinden tahmin üretmek; gerçekleşenlerle hatayı izleyip gerektiğinde yeni eğitim adayına geri beslemek.

İki taraf aynı veri/değişken tanımlarını kullanır. Testlerde ve geçmiş tahminlerde yalnız o tarihte açıklanmış bilgi kullanılacak; üretimde modelin sabitlenmiş dönüşüm ve girdi sürümü korunacak.

## Dizin yapısı

```text
docs/
├── README.md
├── model_oncesi/
│   ├── README.md
│   ├── DEGISKEN_LISTESI.md
│   ├── degiskenler.json
│   └── arastirma/2026-11-06-bilanco-tahmini/
│       ├── ARASTIRMA.md
│       ├── PROJELERIN_DEGISKENLERI.md
│       ├── ALGORITMALAR_VE_CALISMA_MEKANIKLERI.md
│       ├── MAKALELER.md
│       ├── EK_*.md
│       ├── makaleler/    # Makale PDF'leri
│       ├── projeler/     # Kaynak kod arşivleri
│       └── *.json       # Kaynak ve değişken kayıtları
└── model_sonrasi/
    ├── README.md
    ├── ISTENILEN_HEDEF.md
    ├── SISTEM_MIMARISI.md
    └── MODEL_YASAM_DONGUSU.md
```

Arşivlenen projelerin lisansları kendi dosyalarında korunmuştur. Kaynak kodu, model ağırlıkları ve finansal veri için kullanım koşulları ayrı olabilir.
