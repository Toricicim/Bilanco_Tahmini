# Geliştirme günlüğü

Her commit için kayıt eklenir; **en yeni kayıt üstte** durur. Çalışmaya başlamadan ilgili son kayıtları oku. Kalıcı çalışma kuralları [AGENTS.md](../AGENTS.md) dosyasındadır.

Kayıt aynı committe değişiklikle birlikte bulunmalı. Küçük değişiklik için kısa kayıt yeterlidir. Yeni commitin kendi hash'i yerine benzersiz kayıt kimliği ve commit başlığı yazılır; hash eklemek amacıyla ikinci commit oluşturulmaz. `git log --oneline -- docs/GELISTIRME_GUNLUGU.md` kayıtların Git geçmişini gösterir. İlk iki tarihsel kayıt, günlük oluşturulurken mevcut commitlerden geriye dönük özetlenmiştir; eski commitler değiştirilmemiştir.

## 2026-11-08 — AI ekip rehberi ve commit devir kuralı

- **Kayıt ID:** `2026-11-08-ai-rehberi-ve-gunluk`
- **Commit konusu:** `docs: add AI collaboration guide and per-commit development log`
- **Neden:** Ekipte farklı AI'lar kullanılıyor. Yeni ajanların projenin amacını, veri kalitesi sınırlarını, yapılan işi ve sonraki adımları sohbet geçmişi olmadan anlayabilmesi gerekiyor. Kullanıcı her committe neyin ve neden yapıldığının açıklanmasını istedi.
- **Değişiklik:** Kök `AGENTS.md`; okuma sırası, mevcut durum, dosya haritası, ortam/denetim komutları, finansal/zamansal veri kuralları, P0/P1 iş paketleri ve bitiş ölçütleriyle eklendi. Günlük ayrı tutuldu; her committen önce güncelleme kuralı kondu. Ana README ve belge dizininden rehbere/günlüğe bağlantı eklendi.
- **Kontrol:** Yeni Markdown bağlantıları, `git diff --check`, özellik listesi uyumu ve mevcut veri manifestosu/denetimi kontrol edildi. Kod veya CSV bu committe değişmiyor; 23 testin geçtiği veri hattı sürümü korunuyor. Mevcut denetim `errors=[]`, çıkış `2`; kaynak/sürüm incelemesi sürüyor.
- **Açık işler / sonraki AI:** Önce kalite kayıtlarından P0 kaynak veya yayın sürümü işini seç. Dört hedefin dolu olması tam eğitim onayı değil. Ayrı kaynak-link CSV'si onay bekleyen öneri. Bu branch pushlanıp main'e PR açılacak; main'e merge bu teslimin parçası değil.
- **İlgili dosyalar:** [AGENTS.md](../AGENTS.md), [README](../readme.md), [belge dizini](README.md), bu günlük.

## 2026-11-08 — Önceki yerel denetim çalışmalarını koruma

- **Kayıt ID:** `2026-11-08-yerel-denetimleri-koruma`
- **Commit:** `8edba7b` — `docs: preserve prior audits and document current data pipeline`
- **Neden:** Arkadaşın branch'i ile önceki yerel çalışma aynı rapor/betik adlarını kullanıyordu. Veri hattı güncellenirken kullanıcının önceki belgeleri ve kodu kaybolmamalıydı.
- **Değişiklik:** Önceki 9 yerel dosya ZIP ve SHA-256 manifestosuyla arşivlendi; eski denetim betiği tarihsel metin olarak korundu. Eski raporların kaynak bağlantıları incelenen Git sürümlerine sabitlendi. Arkadaşın `cd10910` raporu ayrı tarihsel dosyaya taşındı. Güncel rehber bağlantıları eklendi.
- **Kontrol:** Arşivdeki 9 dosyanın hash'leri doğrulandı; Markdown bağlantıları ve sözlük üreticisi kontrol edildi. Yeni çalışma alanında 23 regresyon testi yeniden geçti; veri denetimi `errors=[]`, çıkış `2` verdi.
- **Açık işler:** Arşivdeki eski veri ve demo başarı iddiaları güncel veri için kullanılmamalı. Güncel kalite özeti ve 8 Kasım raporu esas alınmalı.
- **İlgili dosyalar:** [arşiv rehberi](model_oncesi/arsiv/README.md), [güncel veri hattı raporu](model_oncesi/VERI_HATTI_DUZELTMELERI_2026-11-08.md), [tarihsel arkadaş raporu](model_oncesi/VERI_DENETIMI_ARKADAS_cd10910.md).

## 2026-11-08 — Finansal veri okuma ve eksiklik takibi

- **Kayıt ID:** `2026-11-08-parser-ve-kalite`
- **Commit:** `b02bee9` — `fix(data): recover financial values and track missingness`
- **Neden:** Raporda bulunan nakit akışları farklı başlıklar yüzünden kaçıyordu; bazı BIFF hücreleri bütün satırı CSV metni olarak taşıyordu. KAREL düzeltmesi hatalı, GSDDE hasılat eşlemesi eksik, borç/alacak toplamlarında bilinmeyen bileşenler sıfır kabul ediliyordu. Yayın/sürüm eşlemesi ve takvim pencereleri de güvenilir değildi.
- **Değişiklik:** Başlık varyantları ve gömülü CSV satırları okundu. KAREL/GSDDE örnekleri düzeltildi; genel/alt brüt kâr ayrıldı. Son sayısal satır yedeği ve eksik bileşeni sıfırlama kaldırıldı. Kaynak/sürüm zamanları, eksiklik nedenleri, kalite kanıtları ve hash manifestosu eklendi. FX 90 takvim günü, OFR 60 gerçek gözlem ve açık iş günü varsayımıyla hesaplandı. Kök CSV kaldırılıp tek çıktı `data/` altında tutuldu. Demo betiğinin dosya yolu ve finansal kullanılabilirlik sütunu güncellendi; model eğitilmedi.
- **Kontrol:** 23 regresyon testi; gerçek KAP örnekleri, KAREL nakit uzlaşması, sıfır/eksik ayrımı, tarih/pencere hesapları, atomik yazma ve manifest değişiklik tespiti. Denetimde dosya/hash/üretim hatası yok; çıkış `2` ile kaynak incelemesi açık.
- **Sonuç:** Çeyrek yatırım nakit akışında eksik `65 → 10`, finansman nakit akışında `151 → 11`. Bazı toplam alacak/borç alanlarında belirsizlik artık görünür; bilinen alt kalemler ayrı korunuyor. Dört öncelikli hedef dolu. 110 sütunun bir bölümü metadata.
- **Açık işler:** 14 olağan brüt kâr uzlaşması, 76 karma faaliyet kapsamı, toplam 105 işaretli şirket–dönem kaydı; kaynak PDF/dipnot, birim istisnaları, ilk yayım sürümleri ve makro vintage doğrulaması. Bu sayılar farklı kontrollerin sonucudur; birbirine toplanmamalı veya kesin hata sayısı gibi sunulmamalı.
- **İlgili dosyalar:** [script rehberi](../scripts/README.md), [veri hattı raporu](model_oncesi/VERI_HATTI_DUZELTMELERI_2026-11-08.md), [kalite kayıtları](../data/quality/README.md), [regresyonlar](../tests/test_financial_pipeline.py).

## Yeni kayıt şablonu

Yeni kaydı bu şablonla **günlüğün başına**, giriş açıklamasından sonra ekle:

```markdown
## YYYY-MM-DD — Kısa konu

- **Kayıt ID:** `tarih-benzersiz-konu`
- **Commit konusu:** `diff ile uyumlu commit başlığı`
- **Neden:** Hangi somut sorun/istek ele alındı?
- **Değişiklik:** Davranış/veri/sözleşmede ne değişti, hangi dosyalar etkilendi?
- **Kontrol:** Gerçekten çalıştırılan komutlar ve sonuçlar; çalıştırılmayanlar varsa nedeni.
- **Açık işler / sonraki AI:** Kalan belirsizlik, kapsam ve bir sonraki adım.
- **İlgili dosyalar:** Göreli bağlantılar.
```
