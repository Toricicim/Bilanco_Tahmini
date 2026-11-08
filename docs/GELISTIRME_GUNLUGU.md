# Geliştirme günlüğü

Her commit için kayıt eklenir; **en yeni kayıt üstte** durur. Çalışmaya başlamadan ilgili son kayıtları oku. Kalıcı çalışma kuralları [AGENTS.md](../AGENTS.md) dosyasındadır.

Kayıt aynı committe değişiklikle birlikte bulunmalı. Küçük değişiklik için kısa kayıt yeterlidir. Yeni commitin kendi hash'i yerine benzersiz kayıt kimliği ve commit başlığı yazılır; hash eklemek amacıyla ikinci commit oluşturulmaz. `git log --oneline -- docs/GELISTIRME_GUNLUGU.md` kayıtların Git geçmişini gösterir. İlk iki tarihsel kayıt, günlük oluşturulurken mevcut commitlerden geriye dönük özetlenmiştir; eski commitler değiştirilmemiştir.

## 2026-11-08 — Türkiye GPR (`GPRC_TUR`), şirket–risk etkileşimi (`X04`) ve `F16`/`F18` planının `AGENTS.md` rehberine işlenmesi

- **Kayıt ID:** `2026-11-08-turkiye-gpr-ve-etkilesim-plani`
- **Commit konusu:** `docs: document GPRC_TUR, sub-sector interactions (X04), and F16/F18 extraction in AGENTS.md`
- **Neden:** Şirketlerin aynı jeopolitik/makro şoktan farklı yönde ve farklı gecikmeyle etkilenmesini (ör. savunma vs ulaştırma/enerji) sabit kural yazmadan öğrenebilmek için gereken Türkiye GPR (`GPRC_TUR`), alt sektör etkileşimi (`C01_kap_sub_sector` × risk), gecikmeli risk (`q-1..q-4`) ve sipariş avansları (`F18`) / faaliyet giderleri (`F16`) planının `DEGISKEN_DURUMU_VE_EKSIKLER.md` ile uyumlu biçimde `AGENTS.md` içinde de yer alması sağlandı.
- **Değişiklik:** `AGENTS.md` P0-C bölümüne `GPRC_TUR`, `X04` etkileşim terimleri, gecikmeli risk ve mevcut `.xls` bilançolarından `F16`/`F18` çıkarımı maddeleri eklendi.
- **Kontrol:** `git diff --check` ve Markdown bağlantıları doğrulandı.
- **Açık işler / sonraki AI:** `fetch_external_macro_and_risk.py` ve `parse_and_build_dataset.py` üzerinde `GPRC_TUR`, günlük `GPRD`, `F16` ve `F18` çıkarımının uygulanması.
- **İlgili dosyalar:** [AGENTS.md](../AGENTS.md), [değişken kullanım ve eksik durumu](model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md), bu günlük.

## 2026-11-08 — Eski demo model betiğinin (`run_demo_models.py`) kaldırılması ve değişken raporunun sadeleştirilmesi

- **Kayıt ID:** `2026-11-08-remove-demo-model-script`
- **Commit konusu:** `chore: remove legacy run_demo_models.py and clean up variable status report`
- **Neden:** `scripts/run_demo_models.py` önceki `cd10910` dalından kalan ve mevcut veri/modelleme yaklaşımını temsil etmeyen eski bir deneme betiğiydi; kullanıcı bu betiğin `main` dalından tamamen kaldırılmasını ve değişken durum raporunun yalnız sözlük vs CSV kapsamını baz alacak şekilde temizlenmesini istedi.
- **Değişiklik:** `scripts/run_demo_models.py` silindi; `AGENTS.md` dosya haritasındaki referansı kaldırıldı; `docs/model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md` içindeki demo betiği sütunları çıkarılarak doğrudan sözlükteki 17 hedef + 51 girdi ailesinin CSV'de mevcut/eksik durumu, `GPRC_TUR` (Türkiye GPR) hızlı kazanım notu ve 38 ekstra sütun üzerinden düzenlendi.
- **Kontrol:** `git diff --check`, Markdown bağlantıları ve `unittest discover -s tests -v` (23/23 test) doğrulandı.
- **Açık işler / sonraki AI:** P0-C kapsamında `GPRC_TUR`, günlük `GPRD`, çeyrek içi dağılım özellikleri ve çoklu $t_0$ kesimlerine dayalı temiz eğitim matrisinin kurulması.
- **İlgili dosyalar:** [AGENTS.md](../AGENTS.md), [değişken kullanım ve eksik durumu](model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md), bu günlük.

## 2026-11-08 — Karma frekanslı (nowcasting) 3. yaklaşım kararı ve `.env.example` şablonu

- **Kayıt ID:** `2026-11-08-nowcasting-3-yaklasim-ve-env`
- **Commit konusu:** `docs: add mixed-frequency nowcasting plan and .env.example template`
- **Neden:** Günlük frekanstaki döviz/risk verileri ile 3 aylık bilanço hedeflerinin birleştirilmesinde 90 günlük satır çoğaltma (pseudoreplication) yapmadan, gün geçtikçe tahminin keskinleşmesini sağlayan 3. yaklaşımın (çeyrek içi dağılım özellikleri + çoklu bilgi kesim ufukları $t_0$) yapılacaklara kaydedilmesi ve veri çekimi için `.env` ihtiyacının netleştirilmesi istendi.
- **Değişiklik:** `AGENTS.md` (P0-C bölümü) ve `docs/model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md` (Bölüm 5.1) içine günlük GPRD eklenmesi, çeyrek içi dağılım/yörünge özellikleri (`mean`, `last`, `std`, `max`) ve çoklu bilgi kesim ufukları ($t_0 \in \{+30\text{g}, +60\text{g}, +90\text{g}, +120\text{g}\}$) planı eklendi. Mevcut veri çekimi açık uç noktalar kullandığı için zorunlu anahtar gerektirmediği, ancak P0-B (`M03` gerçek TCMB EVDS ticari kredi faizi) ve P1 (`M07`/`M08` FRED/ALFRED emtia ve vintage verileri) için kullanılacak `.env.example` şablonu oluşturuldu ve `.gitignore` içine `.env` koruması eklendi.
- **Kontrol:** `git diff --check` ve Markdown bağlantıları doğrulandı.
- **Açık işler / sonraki AI:** `fetch_external_macro_and_risk.py` içine günlük `GPRD` indirme ve isteğe bağlı `EVDS_API_KEY` / `FRED_API_KEY` okuma desteği eklenebilir; ardından P0-C kapsamında çeyrek içi dağılım özellikleri ve çoklu $t_0$ kesim matrisi üretilebilir.
- **İlgili dosyalar:** [.env.example](../.env.example), [.gitignore](../.gitignore), [AGENTS.md](../AGENTS.md), [değişken kullanım ve eksik durumu](model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md), bu günlük.

## 2026-11-08 — Değişken kullanım, eksik ve ekstra sütun durum tablosu

- **Kayıt ID:** `2026-11-08-degisken-durumu-ve-eksikler`
- **Commit konusu:** `docs: add variable usage/missing/extra mapping report and update AGENTS rule`
- **Neden:** Sözlükteki (`degiskenler.json`) 17 hedef ve 51 girdi ailesinden (26 P0, 19 P1, 6 P2) hangilerinin şu anki 110 sütunlu CSV'de ve ilk model deneyinde (`run_demo_models.py`) kullanıldığı, hangilerinin henüz eksik olduğu ve sözlük dışında eklenen 38 yardımcı/metadata sütununun ne olduğu tek bir referans dosyada görünür olmalıydı.
- **Değişiklik:** `docs/model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md` oluşturuldu; 17 hedef, 26 P0 (21 kullanılan + 5 CSV'de hazır ama henüz modele verilmeyen), 25 P1/P2 (1 hazır `R04`, 1 kısmi `F15`, 23 eksik) ve 38 ekstra/metadata sütunu boşluk sayılarıyla eşlendi. `F01`/`F07` önek farkları ve `X02`/`X03` eşzamanlı sütun uyarıları belgelendi. `AGENTS.md` ve `docs/model_oncesi/README.md` içine yeni değişken/sütun eklendiğinde veya modelde kullanıldığında bu dosyanın da güncellenmesi kuralı eklendi.
- **Kontrol:** `git diff --check`, Markdown göreli bağlantıları ve `scripts/render_feature_list.py --check` kontrol edildi. Kod veya veri dosyaları değişmedi.
- **Açık işler / sonraki AI:** P0-C kapsamında eğitim matrisi kurulurken bu eşleme tablosundaki P0 sütunları ve `F16`/`F18` gibi mevcut `.xls` dosyalarından çıkarılabilecek hızlı kazanım adayları değerlendirilebilir.
- **İlgili dosyalar:** [değişken kullanım ve eksik durumu](model_oncesi/DEGISKEN_DURUMU_VE_EKSIKLER.md), [AGENTS.md](../AGENTS.md), [model öncesi rehberi](model_oncesi/README.md), bu günlük.

## 2026-11-08 — PR #1 incelemesi ve `fix/veri-hatti` dalının `main` dalına kabulü

- **Kayıt ID:** `2026-11-08-pr1-kabul-ve-main-merge`
- **Commit konusu:** `docs: record PR #1 review and acceptance rationale for main`
- **Neden:** `main` (`91a7d0e`) dalındaki eski CSV birbiriyle uyumsuz iki kopya (`bist_bilanco_tahmini_2010_2020.csv` ve `data/bist_bilanco_tahmini_2010_2020.csv`), `10` adet `±inf` oran değeri, birim/ölçek sapmaları (`TOASO`, `KAREL`, `GSDDE` vb.), eksik borç/alacak bileşenlerini sıfır sayan sahte toplamlar (`F13_net_borc = -nakit`) ve `570` satırda eksik yayın tarihi içeriyordu. Ara dal (`cd10910`) üzerindeki yayın tarihini erkene çekme, son satırı nakit akışı toplamı sanma ve takvim penceresi sızıntıları da `fix/veri-hatti` dalında giderildiği için PR #1'in `main` dalına kabul edilme gerekçesi ve yapılan iki aşamalı denetim kayıt altına alındı.
- **Değişiklik:** PR #1 (`fix/veri-hatti` → `main`) kabul gerekçesi, `main` ile karşılaştırmalı bulgular, doğrulanan kontroller ve merge sonrası kalan P0/P1 teknik notlar geliştirme günlüğüne eklendi. Kod veya veri dosyalarında değişiklik yapılmadı.
- **Kontrol:** Python 3.12 ortamında `python3 -B -m unittest discover -s tests -v` (23/23 test geçti), `python3 -B scripts/audit_dataset.py` (`errors=[]`, çıkış `2`), `python3 -B scripts/render_feature_list.py --check` (51 girdi ailesi / 17 hedef uyumlu), `data/quality/manifest.json` tüm SHA-256 özet eşleşmeleri, 21 yeni `.xls` dosyasının ayrıştırılabilirliği ve tüm Markdown iç bağlantıları (`git diff --check` dahil) doğrulandı.
- **Açık işler / sonraki AI:** `main` dalına kabul, veri hattı ve kalite altyapısının kanonikleşmesi demektir; doğrudan model eğitimi onayı değildir (`audit_dataset.py` çıkış `2`, `fully_point_in_time_verified=false`). Sıradaki işler: (1) P0-A/B kapsamında 105 işaretli raporun (14 olağan brüt kâr uzlaşması, 76 karma faaliyet kapsamı, birim istisnalarında `qa_flags` ve `SARKY 2017Q2` `626866` düzeltme saati izlenebilirliği) ve makro vintage takvimlerinin tamamlanması; (2) alternatif gelir/maliyet 3 aylık toplamlarında kısmi toplam kenar durumunun `finite_sum` ile korunması; (3) P1 aşamasında `run_demo_models.py` içinde `q-2`/`q-4` gecikmeleri ve eğitim etiketleri için `available_at <= t0` kontrolünün sıkılaştırılması.
- **İlgili dosyalar:** [AGENTS.md](../AGENTS.md), [8 Kasım veri hattı raporu](model_oncesi/VERI_HATTI_DUZELTMELERI_2026-11-08.md), [kalite özeti](../data/quality/summary.json), [manifest](../data/quality/manifest.json), bu günlük.

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
