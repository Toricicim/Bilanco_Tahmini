# Bilanço tahmini belgeleri

Son düzenleme: **8 Kasım 2026**. Belgeler iki çalışma alanına ayrılır. Henüz eğitilmiş model veya çalışan site yoktur.

Yeni AI/geliştirici önce [çalışma rehberini](../AGENTS.md) ve [geliştirme günlüğünü](GELISTIRME_GUNLUGU.md) okumalıdır. Her commitin gerekçesi, kontrolleri ve kalan işleri günlükte kaydedilir.

| Alan | Amaç | Başlangıç |
|---|---|---|
| **Model öncesi** | Araştırma, geçmiş veri, değişken seçimi, eğitim ve doğrulamayla kullanılabilir model paketi üretmek | [Geliştirme/eğitim rehberi](model_oncesi/README.md) |
| **Model sonrası** | Modeli sitede kullanmak; yeni veriyi almak, tahmin/rapor üretmek, performansı izlemek | [Ürün/işletim rehberi](model_sonrasi/README.md) |

## 1. Model öncesi: geliştirme ve eğitim

- [Güncel veri hattı düzeltmeleri ve kalan işler](model_oncesi/VERI_HATTI_DUZELTMELERI_2026-11-08.md) · [Kanonik CSV](../data/bist_bilanco_tahmini_2010_2020.csv) · [Kalite kayıtları](../data/quality/README.md)
- [Yeni veri seti denetimi ve ilk demo kararı](model_oncesi/VERI_DENETIMI_2026-11-07.md) · [Sayısal denetim çıktısı](model_oncesi/veri_denetimi_2026-11-07.json)
- [Güncellenebilir değişken listemiz](model_oncesi/DEGISKEN_LISTESI.md) · [JSON kaydı](model_oncesi/degiskenler.json)
- [Araştırma, ilk üç proje ve seçim gerekçeleri](model_oncesi/arastirma/2026-11-06-bilanco-tahmini/ARASTIRMA.md)
- [İncelenen projelerin değişkenleri](model_oncesi/arastirma/2026-11-06-bilanco-tahmini/PROJELERIN_DEGISKENLERI.md)
- [Makaleler ve değişken seçimi](model_oncesi/arastirma/2026-11-06-bilanco-tahmini/MAKALELER.md)
- [Algoritmalar ve çalışma mekanikleri](model_oncesi/arastirma/2026-11-06-bilanco-tahmini/ALGORITMALAR_VE_CALISMA_MEKANIKLERI.md)
- [Araştırma projesi önerisi](model_oncesi/arastirma/2026-11-06-bilanco-tahmini/ARASTIRMA_PROJESI_ONERISI.md)
- [Risk ve maruziyet değişkenlerinin gerekçesi](model_oncesi/arastirma/2026-11-06-bilanco-tahmini/DEGISKEN_SECIMI_VE_RISK_SKORU.md)

PDF'ler, kaynak ZIP'leri, ek değişken sözlükleri ve manifestolar `model_oncesi/arastirma/2026-11-06-bilanco-tahmini/` altında korunur. Kaynak kodu, model ağırlığı ve finansal veri lisansları ayrı olabilir; arşivlerdeki lisanslar korunmuştur.

## 2. Model sonrası: ürün ve işletim

- [İstenilen Hedef](model_sonrasi/ISTENILEN_HEDEF.md)
- [Sistem Mimarisi](model_sonrasi/SISTEM_MIMARISI.md)
- [Yeni veri ve Model Yaşam Döngüsü](model_sonrasi/MODEL_YASAM_DONGUSU.md)

## İki tarafı bağlayan sözleşme

Veri/değişken tanımları tek yerde, [model öncesi sözlüğünde](model_oncesi/degiskenler.json) tutulur. Model sonrası taraf seçilmiş modelin sabit girdi ve dönüşüm sürümünü kullanır. Yeni veriyle tahmin üretmek ile modeli yeniden eğitmek farklı işlemlerdir. Sahadaki sonuçlar yeni eğitim ihtiyacı doğurursa birinci çalışma alanına geri dönülür.
