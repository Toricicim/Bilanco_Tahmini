# Model öncesi: geliştirme, eğitim ve doğrulama

Bu çalışma alanının çıktısı, yeni şirket/dönem verisine uygulanabilen **doğrulanmış ve sürümlenmiş bir model paketidir**. Araştırma, veri hazırlama, değişken seçimi, model eğitimi ve zaman dışı test burada yürütülür. “Model öncesi” ilk modeli hazırlamayı anlatır; yeni sürüm gerektiğinde aynı iş akışına geri dönülür.

## Yapılacak işler

1. Tahmin edilecek finansal kalemleri, mali dönemi ve bilgi kesim zamanını tanımlamak.
2. Birden çok şirketin geçmiş verisini, kaynak ve açıklanma zamanlarıyla hazırlamak.
3. Birim, konsolidasyon, çeyrek/kümülatif ve enflasyon temellerini doğrulamak.
4. Aday değişkenleri ve olay–şirket profili etkileşimlerini seçmek.
5. Basit kıyasları ve ML modellerini eğitip sonraki tarih bloklarında karşılaştırmak.
6. Başarılı adayın girdi şemasını, dönüşümlerini, kapsamını ve ölçümlerini modelle birlikte paketlemek.

## Belgeler

| Belge | Kullanımı |
|---|---|
| [Güncel veri hattı — 8 Kasım](VERI_HATTI_DUZELTMELERI_2026-11-08.md) · [Kalite kayıtları](../../data/quality/README.md) | Ayrıştırıcı düzeltmeleri, tek CSV, eksiklik nedenleri ve kalan kaynak işleri |
| [Veri denetimi ve ilk demo kararı — 7 Kasım 2026](VERI_DENETIMI_2026-11-07.md) · [Sayısal bulgular](veri_denetimi_2026-11-07.json) | Yeni KAP veri setinin kapsamı, kalite/yayın zamanı sorunları ve eğitime başlama koşulları |
| [Güncellenebilir değişken listemiz](DEGISKEN_LISTESI.md) · [JSON kaydı](degiskenler.json) · [Değişken kullanım ve eksik durumu](DEGISKEN_DURUMU_VE_EKSIKLER.md) | Girdi adayları, öncelikler, CSV'de mevcut/eksik/ekstra sütunlar ve deneyde kullanım durumları |
| [Araştırma ve proje karşılaştırması](arastirma/2026-11-06-bilanco-tahmini/ARASTIRMA.md) | İncelenen GitHub projeleri ve seçim gerekçeleri |
| [Projelerin değişkenleri](arastirma/2026-11-06-bilanco-tahmini/PROJELERIN_DEGISKENLERI.md) · [HTML sürümü](arastirma/2026-11-06-bilanco-tahmini/PROJELERIN_DEGISKENLERI.html) | Diğer projelerin girdi/çıktı sözlükleri |
| [Algoritmalar ve çalışma mekanikleri](arastirma/2026-11-06-bilanco-tahmini/ALGORITMALAR_VE_CALISMA_MEKANIKLERI.md) | Forma, standart ML ve diğer model sistemleri |
| [Makaleler](arastirma/2026-11-06-bilanco-tahmini/MAKALELER.md) | Akademik dayanaklar ve inceleme sınırları |
| [Araştırma projesi önerisi](arastirma/2026-11-06-bilanco-tahmini/ARASTIRMA_PROJESI_ONERISI.md) | Dört kişilik ekip için kapsam, deney ve görevler |
| [Değişken seçimi ve risk skoru](arastirma/2026-11-06-bilanco-tahmini/DEGISKEN_SECIMI_VE_RISK_SKORU.md) | Makro/risk ve şirket maruziyetlerinin araştırma gerekçesi |
| [Kaynak manifestosu](arastirma/2026-11-06-bilanco-tahmini/kaynak-manifestosu.json) | Kaynak sürümleri, arşivler, indirme durumu ve dosya özetleri |

Ek sözlükler: [Forma'nın 78 kalemi](arastirma/2026-11-06-bilanco-tahmini/EK_FORMA_78.md), [DeepEarnings](arastirma/2026-11-06-bilanco-tahmini/EK_DEEPEARNINGS.md), [EPSBench](arastirma/2026-11-06-bilanco-tahmini/EK_EPSBENCH_SURUCULERI.md). PDF'ler, kaynak ZIP'leri ve araştırma JSON'ları aynı tarihli araştırma klasöründe korunur.

## Model sonrası tarafa teslim

Teslim yalnız model ağırlığı/dosyası değildir. Kesin girdi adları, tür/sıra/birimler, eksik veri kuralları, öğrenilmiş dönüşümler, hedefler, eğitim kesimi, desteklenen kapsam, doğrulama sonuçları ve sürüm bilgisi birlikte verilir. Aday değişken havuzunun tamamı otomatik olarak model girdisi sayılmaz.

Ortak değişken ve veri tanımları bu klasörde tek kaynak olarak tutulur; ürün tarafı aynı sözlüğe ve kendi model paketinin sabit sürümüne başvurur. Geliştirme ve kullanımda ayrı özellik hesapları yazmak tutarsızlık yaratabilir; [resmi scikit-learn açıklaması](https://scikit-learn.org/stable/common_pitfalls.html#inconsistent-preprocessing) bu ayrımı örnekler.

Ürünün ne sunacağı [İstenilen Hedef](../model_sonrasi/ISTENILEN_HEDEF.md) belgesindedir. Kullanıma alma ve geri besleme [model sonrası](../model_sonrasi/README.md) çalışma alanında, paket sözleşmesi [Model Yaşam Döngüsü](../model_sonrasi/MODEL_YASAM_DONGUSU.md) belgesindedir.
