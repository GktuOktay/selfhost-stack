# Spec 0002 — BookStack ana sayfası ve proje rafları: selfhost dashboard

- Status: Awaiting approval (Faz 1)
- Phase status:
  - **Faz 1:** Awaiting approval. Kalan ön koşullar: (1) ADR-0007'nin bu revizyonla senkronu (T-A7b), (2) board'un K3 koşullarını yeniden kontrolü, (3) T-5'ten önce dind lisans doğrulaması ve tag + digest pini (K3-4, T-0d). Faz 1 imzasında CEO'ya yeni test image'ı olarak `docker:<tag>-dind` (privileged, yalnız test) gösterilir.
  - **Faz 2a:** Draft. Ön koşullar: T-0a2 ve D-20 taraması (K2-4, tamamlanmazsa toplayıcı image'ı reddedilir), T-0c (KR-9), ADR-0006 güncellemesi (K2-8), K3-5, Faz 2a kapı turu.
  - **Faz 2b:** Draft. Ön koşullar: Faz 2a teslimi ve Faz 2b kapı turu.
- Tier: full. Üç imza: Faz 1, Faz 2a, Faz 2b (KR-3, KR-10).
- Source: CEO isteği (chat, 2026-11-09): "BookStack için default sayfaya (homepage) kendi dashboardumuzu yapamaz mıyız?" + ek cevaplar ve on karar (§1, §16).
- Extends: Spec 0001 revizyon 3. **0001'in metni değişmez**, ama 0001'in teslim edeceği bazı dosyaların ve komutların davranışı değişir (§2.2). Faz 1, 0001 imzası ve 0001 T-2 ile T-5 teslimi sonrası uygulanır. Faz 2a ayrıca 0001 T-4'ü bekler.
- Previous spec: 0001
- Revision: 5. İşlenenler: board tur 3 (K3-1..K3-5, A3-1..A3-7), spec-critic tur 3 (H1-H6, M1-M6, L1-L9), appsec tur 3 (S3-01..S3-07). İşlenemeyenler §15.3'te.
- Kimlik notu: görev ve kriter kimlikleri 0002'ye aittir, 0001'inkiler "0001 T-n", "0001 AC-n" diye anılır. Kriter numaraları sabittir. CB-19 ve CB-27 birleştirildi (boş), yeniler CB-30'dan başlar.
- Self-critique: done (§15).
- Budget: **zaman ve token tavanı yok, durdurma kuralı yok** (KR-7). Saatler bilgi amaçlı tahmindir (§13). **Para: 0.** Gerçek para harcayan her adım her seferinde ayrıca CEO onayı ister.

**Özet (revizyon 5).** BookStack'in ana sayfası, tüm projelerin özetini veren bir dashboard'a dönüşüyor. Her proje rafı aynı özeti o proje için gösteriyor.
- **Faz 1** (token yok, yeni container yok, dosya okuyan kod yok, 12 kriter): uygulama kartları, bizim bloğumuz BookStack'in kullanıcıya göre düzenlenebilir ana sayfa bloklarının üstünde, etiketli raflarda proje başlığı ve son güncellenen kitaplar. Tema yalnız `./stack up bookstack` sırasında, kontroller geçtikten sonra makineye kopyalanır. BookStack sürümü temanın doğrulandığı sürümden farklıysa tema kendiliğinden kapanır.
- **Faz 2a** (15 kriter): toplayıcı container (`dashfeed`), iç ağ, Plane'den CEO soruları, açık işler ve son değişiklikler.
- **Faz 2b** (3 kriter): spec dosyalarından açık sorular, imza bekleyen ve taslak spec'ler.
- Her iki fazda geçerli 8 korunan davranış (PB). Açık CEO sorusu: 0.

> Doğrulama durumu: T-0a kısmi, T-0b tamam (Docker Desktop, arm64; gerçek Linux ve amd64 hariç). T-0a2 ve T-0c yapılmadı. §5 her maddeyi kaynak raporundaki hükümle gösterir.

## 1. Intent

**CEO'nun cümleleri ve cevapları (ana oturumdan aktarım):**
1. "BookStack için default sayfaya (homepage) kendi dashboardumuzu yapamaz mıyız?"
2. Dashboard şunları göstermeli: (1) açık işler, (2) son değişiklikler, (3) CEO'ya yöneltilmiş sorular. Başka neyin işe yarayacağını sordu.
3. Proje bazında dashboard'lar da istiyor.
4. Linux testi Docker içinde (Linux container) yapılır, VM gerekmez.
5. Gerçek Plane testi CEO'nun canlı Plane'ine karşı yalnız okuma olarak çalışabilir. Düşük rollü Plane kullanıcısını ve token'ı CEO kendisi oluşturur. Claude asla token oluşturmaz.
6. On karar (2026-11-09, §16 KR-1..KR-10).

**Yorumum:** BookStack'e girildiğinde açılan ana sayfa, tüm projelerin özetini veren bir "komuta ekranı" olur. En üstte CEO'nun cevabını ya da imzasını bekleyenler, sonra açık işler, sonra son değişiklikler ve üç uygulamaya giriş kartları gelir. Altında BookStack'in kendi blokları, her kullanıcının kendi düzeniyle durur. Her proje için bir raf vardır, o rafın sayfası aynı özeti o proje için gösterir. Ekranın yapısı her makinede aynıdır ve git'le gelir. İçerik makinenin kendi verisidir ve git'e girmez.

**0001 ile gerilim, çözüldü (KR-1):** tema dosyaları ve toplayıcı script'i merkezi araçtır. Projeler, raf eşlemeleri ve Plane token'ı makinede kalır. Her makine dashboard'u kapatabilir, makinenin kendi teması her zaman kazanır. Kayıt: ADR-0007 D6.

**Bilerek yapılmayanlar (v1):** Penpot/BookStack sağlık göstergesi, Penpot son dosyaları, kullanıcıya göre düzenlenebilir dashboard, BookStack'in blok sistemine kendi bloğumuzu eklemek, ana sayfa ve raf dışındaki görünümler, markalama, tarayıcıda JavaScript, dashboard'dan Plane'e yazma.

## 2. 0001 ile ilişki

### 2.1 0001 revizyon 3'ün hangi bölümlerini genişletiyor?

| 0001 öğesi | Bu spec'teki etkisi |
|---|---|
| §1 Intent, §13 ("uygulama içi özelleştirme") | Tema + toplayıcı merkezi araç (KR-1) |
| §6.2 katmanlar (`--project-directory stacks/<s>`, hiç `--profile` yok) | Korunur. Toplayıcı `--scale` ile kapatılır |
| §6.3 yükseltme prosedürü | C-9, C-14 |
| §7.4 env, §7.9 parser | C-4 |
| §7.10 guard listesi | G-net (C-12), G-tok (C-15) |
| §9.1 health | `dashfeed` eklenir (C-11) |
| REQ-2, REQ-4, REQ-5, REQ-7, REQ-7a, REQ-10, REQ-11, REQ-14, REQ-18, REQ-20 | Korunur |
| AC-1 (idempotent `up`) | Korunur: tema değişikliği container'ı yeniden yaratmaz (CB-9) |
| AC-2 (`init`, sha256 sabit) | Korunur: `init` mevcut dosyalara yeni anahtar eklemez (§7.3) |
| AC-3 loopback | PB-2 |
| AC-4 guard'lar | `dashfeed-init` `cap_add` kullanmaz. G-net, G-tok |
| AC-5 pin | PB-3 |
| AC-6 parser | Yeni anahtarlar izinli kümeye girer |
| **AC-7 git hijyeni** | PB-1 |
| **AC-10 silme yok** | PB-5 |
| **AC-11 / AC-12 yedek, restore** | PB-4 |
| AC-13 pin farkı | PB-7, CB-29 |
| AC-15 maskeleme, status | PB-8 |

### 2.2 0002'nin değiştirdiği 0001 sözleşmeleri

| # | 0001 sözleşmesi | Değişiklik | Faz |
|---|---|---|---|
| C-1 | §13 "uygulama içi özelleştirme" kapsam dışı | Tek istisna `selfhost-dashboard` teması (KR-1) | 1 |
| C-2 | 0001 T-2 BookStack compose | Uygulama ve MariaDB yalnız açık `environment:` alır, `env_file:` yok. `APP_URL` her zaman verilir. Tema mount'u **`local/state/theme/selfhost-dashboard/`** dizininden (repo'dan değil, C-16), read-only. Kart env'leri | 1 |
| C-3 | `./stack up` | (a) kart URL'leri diğer stack'in normalize config'inden 0001 §7.4 fonksiyonuyla hesaplanır. (b) **`./stack up bookstack` `--remove-orphans` kullanır** (Faz 1'den itibaren, yalnız BookStack projesi, board A3 ve critic M2). (c) Faz 2a: toplayıcı kapalıyken `--scale dashfeed=0 --scale dashfeed-init=0` | 1, 2a |
| C-4 | §7.4/§7.9 parser, `./stack init` | `local/bookstack.env`: `SELFHOST_DASHBOARD`, `APP_THEME` (Faz 1). Yeni dosya `local/dashfeed.env` (Faz 2a), `DASHBOARD_TZ` dahil. `init` yalnız yeni dosyaları oluşturur, var olan dosyalara anahtar eklemez. `PLANE_API_TOKEN` AC-15 maskeleme listesine girer | 1, 2a |
| C-5 | 0001 T-4 Plane overlay | `proxy` servisi `selfhost-dashfeed` ağına alias `plane-proxy-dashfeed` ile katılır, `default` ağı korunur. Faz 2a deploy'u proxy'yi bir kez yeniden yaratır | 2a |
| C-6 | `up bookstack`, `up plane` | Ağı AC-13 kontrolünden sonra, `pull`'dan önce garanti eder ve doğrular. `config`, `status`, `down` oluşturmaz. Hiç silmez | 2a |
| C-7 | BookStack compose çağrısı | `local/dashfeed.env` varsa `--env-file` (yoksa verilmez). Faz 2b: üretilmiş `-f local/state/bookstack.specmounts.yaml` | 2a, 2b |
| C-8 | `stacks/bookstack/versions.env` | `DASHFEED_IMAGE` (tag + digest), 0001 AC-13 toplayıcıya da uygulanır | 2a |
| C-9 | §6.3 yükseltme prosedürü | BookStack bump PR'ı CB-8'i, Plane bump PR'ı CB-28'i geçmeli. Appsec incelemesi §6.1 M-1/M-2 (S3-02). Bump PR açıklaması "orijinal sha256 değişti mi" ve "yeniden port süresi" alanlarını taşır | 1, 2a |
| C-10 | AC-15 `status` | Faz 1: tema kararı (repo kararı ve çalışan container'ın `APP_THEME`'i, farklıysa "`./stack up bookstack` gerekli"). Faz 2a: `dashfeed` satırı, snapshot `status`'u, köprü uyarısı | 1, 2a |
| C-11 | §9.1 BookStack health | Toplayıcı etkinse `dashfeed` `healthy` (heartbeat) | 2a |
| C-12 | §7.10 guard | **G-net:** `selfhost-dashfeed`'e bağlı servis kümesi BookStack'te tam `{dashfeed}`, Plane'de tam `{proxy}`, diğer her projede boş. Değilse exit 3 | 2a |
| C-13 | (r5'te kaldırıldı) | `TZ` artık `local/machine.env`'de değil, Faz 2a'da `local/dashfeed.env`'de `DASHBOARD_TZ` (C-4, K3-3) | – |
| C-14 | `./stack up bookstack`, `./stack config bookstack` | **Tema kilidi (KR-8, K3-1):** §6.1'deki girdi-çıktı tablosu. `config` ve `up` aynı kararı gösterir | 1 |
| C-15 | §7.10 guard | **G-tok:** token değeri yalnız `services.dashfeed.environment` altında, değilse exit 3. Biçim ihlali exit 2 | 2a |
| C-16 | `./stack up bookstack` | **Tema dağıtım sınırı (S3-03):** tema dosyaları yalnız `up bookstack` sırasında, parser, guard'lar, AC-13 ve C-14 geçtikten sonra `local/state/theme/selfhost-dashboard/`'a kopyalanır. `up` 5 ile ya da başka bir hatayla durursa kopyalanmaz | 1 |

## 3. Requirements (EARS)

Faz 1:
- REQ-D1: BookStack'in ana sayfa ayarı varsayılan değerdeyken, sistem giriş yapmış kullanıcıya ana sayfa olarak dashboard'u gösterecek.
- REQ-D2: Sistem, dashboard'un yapısını ve metnini her makinede aynı tutacak ve dashboard için elle kurulum adımı istemeyecek. İstisnalar yalnız Faz 2a'nın Plane adımları ve Faz 2b'de ek spec klasörlerinin tanımlanması.
- REQ-D3: Dashboard, giriş yapmış kullanıcıya etkin her uygulama için o makinedeki erişim adresine giden bir kart gösterecek. Uygulama etkin değilse ya da adresi hesaplanamıyorsa kart bağlantısız olacak. Misafirlere kart gösterilmeyecek.
- REQ-D4: Dashboard, BookStack'in kendi ana sayfa bloklarını ve her kullanıcının blok düzenini değiştirmeyecek. Bu bloklar yalnız kullanıcının görme yetkisi olan içeriği gösterecek.
- REQ-D5: Bir makine ayarı dashboard'u kapatırsa ya da makine kendi temasını seçerse, sistem repo'daki hiçbir dosyayı değiştirmeden standart görünümü ya da makinenin temasını gösterecek, uyarı basmayacak ve toplayıcıyı çalıştırmayacak.
- REQ-D6: Dashboard hiçbir harici kaynak yüklemeyecek, tarayıcıda script çalıştırmayacak ve BookStack'in içerik güvenlik ayarlarını gevşetmeyecek.
- REQ-D7: Değiştirilen bir BookStack görünümünün upstream kaynağı pinlenmiş sürümde değiştiyse ya da Plane'in pinlenmiş sürümü toplayıcının test edildiği sürümden farklıysa, değişiklik testleri geçmeyecek.
- REQ-D20: Dashboard teması seçilecekken BookStack'in çalışacak sürümü temanın doğrulandığı sürümden farklıysa ya da tema kaydı bozuksa, sistem o makinede dashboard temasını kapatacak ve bunu bildirecek. Makinenin kendi temasına dokunmayacak.
- REQ-D23: Repo'daki tema değişikliği makinede yalnız `./stack up bookstack` ile ve kontroller geçtikten sonra etkili olacak.
- REQ-D15: Bir raf bir Plane projesiyle eşlenmişse, raf sayfası standart raf içeriğini değiştirmeden projenin başlığını ve son güncellenen kitaplarını (Faz 1), ayrıca projenin Plane bloklarını (Faz 2a) gösterecek.
- REQ-D16: Sistem bir rafın bir projeyle eşlenmesine, repo'daki dosyayı değiştirmeden ve yeniden başlatma gerektirmeden, BookStack içinden izin verecek.
- REQ-D17: Eşlemesi olmayan raf standart görünecek. Geçersiz bir eşleme (Faz 1) ya da Plane'de bulunmayan bir proje (Faz 2a) bir mesajla, geri kalanı standart olarak görünecek.

Faz 2a:
- REQ-D8a: Dashboard en üstte CEO'nun cevabını bekleyen Plane işlerini gösterecek.
- REQ-D9: Dashboard tamamlanmamış Plane işlerini duruma göre gruplu ve öncelikleriyle gösterecek.
- REQ-D10: Dashboard son değişiklikleri (BookStack sayfaları, son güncellenen Plane işleri ve son 7 günde kapanan işler) zamanıyla gösterecek.
- REQ-D11: Sistem Plane verisini sadece sunucu tarafında ve sadece okuma istekleriyle alacak. Erişim anahtarı tarayıcıya, BookStack sürecine, git'e, yedeklere ya da dashboard verisine ulaşmayacak.
- REQ-D12: Plane kapalı, erişilemez, yetkisiz, aşırı yetkili, rolü belirlenemeyen ya da yapılandırılmamış olduğunda BookStack sayfaları açılacak, `./stack up` bu yüzden başarısız olmayacak ve Plane blokları durumu gösterecek.
- REQ-D13: Dashboard, Plane'den, spec dosyalarından ve raf etiketlerinden gelen her metni güvenilmeyen girdi olarak gösterecek.
- REQ-D14: Plane ve spec blokları ve bunlarla ilgili mesajlar yalnız BookStack ayarlarını yönetme yetkisi olan kullanıcılara gösterilecek.
- REQ-D18: Toplayıcı Plane'in istek sınırının yarısını aşmayacak ve tamamlanmamış bir döngünün sonucunu yayımlamayacak.
- REQ-D19: Toplayıcı Plane'den gelen kişisel verileri hiçbir yere yazmayacak.
- REQ-D21: Toplayıcı, token sahibinin rolünü belirleyemezse ya da rol çalışma alanı sahibi/yöneticisi ise Plane'den iş verisi çekmeyecek.

Faz 2b:
- REQ-D8b: Dashboard "Sizi bekleyenler" bloğunda spec dosyalarındaki açık soruları, imza bekleyen spec'leri ve ayrı bir grupta taslak spec'leri gösterecek.
- REQ-D22: Sistem yalnız açıkça tanımlanmış spec klasörlerini salt okunur okuyacak, başka dosyaları ya da klasör dışını okumayacak.

## 4. User experience

### 4.1 Hangi ekranda ne görünür?

```mermaid
%% Soru: kullanıcı türüne ve sayfaya göre hangi dashboard parçaları görünüyor?
flowchart LR
  V["ziyaretçi"] --> L{"giriş yaptı mı?"}
  L -- "hayır, misafir kapalı" --> LG["giriş sayfası"]
  L -- "misafir açık" --> G["BookStack blokları"]
  G --> GS["etiketli raf: başlık + son kitaplar"]
  L -- evet --> A{"settings-manage?"}
  A -- hayır --> N["kartlar + BookStack blokları"]
  N --> SN["etiketli raf: başlık + son kitaplar"]
  A -- evet --> F["kartlar + Plane/spec blokları + BookStack blokları"]
  F --> S["etiketli raf: + proje Plane blokları"]
```
Açıklama: giriş yoksa BookStack'in kendi davranışı geçerlidir. Giriş yapan herkes kartları ve BookStack bloklarını görür. Plane ve spec verisini yalnız ayar yönetme yetkisi olanlar görür. Misafir kart görmez ama etiketli rafta başlığı ve son kitapları görür. Metin karşılığı:

| Kullanıcı | Ana sayfa | Etiketli raf |
|---|---|---|
| Oturum yok, misafir kapalı | giriş sayfası | giriş sayfası |
| Misafir | BookStack blokları, kart yok, Plane/spec yok | standart raf + proje başlığı + son kitaplar |
| Giriş yapmış, `settings-manage` yok | kartlar + BookStack blokları | standart raf + proje başlığı + son kitaplar |
| Giriş yapmış, `settings-manage` var | Faz 1: yukarıdaki. Faz 2a: + Plane blokları. Faz 2b: + spec blokları | Faz 2a: + projenin Plane blokları |

Misafir tespiti `user()->isGuest()` ile yapılır (A-6, D-23).

### 4.2 Ana sayfa taslağı (Faz 2b, yönetici)

```
+------------------------------------------------------------------+
| BookStack üst menü (değişmez)                                    |
+------------------------------------------------------------------+
| SİZİ BEKLEYENLER                            Son veri: 2 dk önce  |
|  Plane (2a):        WEB-12  Ödeme ekranı: iade 30 gün mü? [aç]   |
|  Spec soruları (2b): selfhost-stack 0003  S-1: Yedek nereye...   |
|  İmza bekliyor (2b): selfhost-stack docs/spec-0003-... (Faz 2)   |
|  Taslak (2b):        selfhost-stack docs/spec-0004-...           |
+------------------------------------------------------------------+
| AÇIK İŞLER (2a)  In Progress (4) ... Todo (11) ... Backlog: 22   |
+------------------------------------------------------------------+
| SON DEĞİŞİKLİKLER (2a)  son güncellenen + son 7 günde kapanan    |
+------------------------------------------------------------------+
| [ BookStack ]      [ Penpot ]            [ Plane ]   (Faz 1)     |
+==================================================================+
| BookStack'in #home-default ızgarası (kullanıcının düzeni)        |
+------------------------------------------------------------------+
```
Faz 1'de yalnız kartlar ve ızgara vardır. İşaretler: ana sayfa bloğu `data-selfhost-dashboard`, Plane blokları `data-selfhost-plane` (2a), spec blokları `data-selfhost-specs` (2b), raf bloğu `data-selfhost-shelf`.

### 4.3 Proje rafı taslağı

```
+------------------------------------------------------------------+
| Proje: WEB                                                       |
| Son güncellenen kitaplar (en fazla 5)                            |
| Faz 2a, yönetici: WEB sizi bekleyenler | açık işler | son değ.   |
+------------------------------------------------------------------+
| BookStack'in standart raf içeriği ve kenar blokları (değişmez)   |
+------------------------------------------------------------------+
```
`data-selfhost-shelf` işareti yalnız geçerli bir `plane-project` etiketi varken ve tema açıkken basılır (critic M3).

### 4.4 BookStack ana sayfa blokları (REQ-D4, CB-3)

v26.09.2'de `home/default.blade.php` liste içermez (D-4). Üç sütunlu `#home-default` ızgarası `common.view-blocks` ile dolar, listeler kullanıcıya göre düzenlenebilir view block'lardır. Varsayılan düzen: sol HomeRecentDrafts, HomeRecentlyViewedOrRecentBooks; orta HomeTopFavourites, HomeRecentlyUpdatedPages; sağ HomeRecentActivity. Bizim `@include('selfhost.home')` satırımız ızgaranın üstündedir (D-1b, ölçüldü). Izgara ve kullanıcı düzeni değişmez.

### 4.5 Ekran durumları

Faz 1 durumları:

| # | Durum | Koşul | Metin (tema sahibi, Türkçe) | Kriter |
|---|---|---|---|---|
| U-1 | Faz 1 | Faz 2a dosyaları yok | Plane/spec blokları basılmaz, `data-selfhost-plane` ve `data-selfhost-specs` yok, snapshot okuyan kod yok | CB-1 |
| U-18 | Kart adresi geçersiz | durum `ok` ama URL http/https değil | kart bağlantısız, "adres geçersiz" | CB-4 |
| U-19 | Uygulama etkin değil | `SELFHOST_<S>_STATE=disabled` | kart bağlantısız, "Bu makinede etkin değil" | CB-2 |
| U-27 | Adres hesaplanamadı | `SELFHOST_<S>_STATE=error` | kart bağlantısız, "adres hesaplanamadı" | CB-2 |
| U-20a | Tema kilidi: doğrulanmadı | pin uyuşmazlığı ya da `UPSTREAM` bozuk/eksik | standart görünüm. `up`, `config`, `status`: "Dashboard teması bu BookStack sürümü için doğrulanmadı, kapatıldı." | CB-30 |
| U-20b | Tema kilidi: kaldırıldı (KR-8) | `UPSTREAM`'de `VIEW` satırı yok | standart görünüm. `up`, `config`, `status`: "Dashboard bu BookStack sürümünde geçici olarak kaldırıldı." | CB-30 |
| U-21 | Raf: etiket yok | `plane-project` adlı etiket yok | standart raf, işaret yok | CB-11 |
| U-22 | Raf: etiket geçersiz | ilk `plane-project` etiketinin değeri geçersiz | "Proje etiketi geçersiz: <kaçışlanmış ham değer>" + standart raf | CB-11 |
| U-23 | Raf: birden çok etiket | birden fazla `plane-project` etiketi | "Birden fazla proje etiketi var, ilki kullanıldı." (+ ilk etiket geçerliyse başlık, geçersizse U-22) | CB-11 |
| U-28 | Raf: görünen kitap yok | `$sortedVisibleShelfBooks` boş | "Bu rafta görebileceğiniz kitap yok." | CB-10 |
| U-25 | Yetkisiz kullanıcı | §4.1 | ilgili bloklar basılmaz | CB-6 |

Faz 2a/2b durumları (U-2..U-17, U-24, U-26): öncelik sırası (1) snapshot yok U-2, (2) okunamadı U-3, (3) biçim uyumsuz U-4, (4) eski U-5, (5) `status` değeri (U-6 `not_configured`, U-7 `plane_disabled`, U-8 `token_too_privileged`, U-26 `token_role_unknown`, U-9 `auth_failed` (24 saat), U-10 `rate_limited`, U-11 `plane_unreachable`, U-12 `error`, U-13 başarı, U-14 boş, U-15 blok kesildi, U-16 snapshot kesildi, U-17 etiketsiz proje, U-24 proje bulunamadı). U-2 ile U-3 ayrımı (dosya yok ile okunamadı) Faz 2a'daki `data` partial'ının işidir (K3-3). Metinlerin tam listesi:

| # | Metin |
|---|---|
| U-2 | "Plane verisi alınıyor. 10 dakikadan uzun sürerse: `./stack logs bookstack dashfeed`" |
| U-3 | "Dashboard verisi okunamadı. `./stack logs bookstack dashfeed`" |
| U-4 | "Dashboard veri biçimi uyumsuz (şema <n>). Tema ve toplayıcı aynı sürümde mi?" |
| U-5 | "Veri eski (son deneme: <zaman>). Toplayıcı çalışıyor mu? `./stack status`" |
| U-6 | "Plane bağlantısı kurulmadı: `local/dashfeed.env` içine `PLANE_API_TOKEN` ve `PLANE_WORKSPACE_SLUG` girin, sonra `./stack up bookstack`." |
| U-7 | "Plane bu makinede etkin değil ya da dashboard'da kapalı." |
| U-8 | "Bu token bir Plane çalışma alanı sahibine ya da yöneticisine ait. Kullanılmıyor. Düşük rollü ayrı bir kullanıcının token'ını girin." |
| U-26 | "Token'ın Plane rolü belirlenemedi. Güvenlik nedeniyle Plane verisi çekilmiyor. `./stack logs bookstack dashfeed`" |
| U-9 | "Plane token'ı geçersiz, süresi dolmuş ya da iptal edilmiş olabilir. Yeni token'ı `local/dashfeed.env` içine girin." |
| U-10 | "Plane istek sınırına ulaşıldı, bir sonraki döngüde yeniden denenecek. Son veri: <zaman>" |
| U-11 | "Plane'e ulaşılamıyor. Son veri: <zaman>" |
| U-12 | "Plane verisi alınamadı (<error_detail>). Çalışma alanı adı (`PLANE_WORKSPACE_SLUG`) doğru mu?" |
| U-14 | "Sizi bekleyen soru yok." / "Açık iş yok." / "Son 7 günde değişiklik yok." (2b: "Sizi bekleyen soru, imza ya da taslak yok.") |
| U-15 | "Plane'de tümünü gör (N)" ya da bağlantısız "Toplam N" |
| U-16 | "Plane'deki işlerin bir kısmı gösterilmiyor (proje sınırı 30, proje başına en son güncellenen 500 iş, toplam 500 açık iş)." |
| U-17 | "Şu projelerde `<etiket>` etiketi yok: WEB, API" |
| U-24 | "Plane'de <KOD> projesi bulunamadı. Dashboard kullanıcısı bu projeye eklendi mi?" |

U-17, U-24 ve Plane/spec durum mesajları yalnız `settings-manage` yetkisi olanlara görünür.

**Zaman biçimi (Faz 2a):** göreli metin sunucuda UTC'den hesaplanır: < 60 s ya da gelecekte "az önce", < 60 dk "N dk önce", < 24 sa "N sa önce", diğer "N gün önce". Mutlak zaman `title` niteliğinde, toplayıcının snapshot'a yazdığı yerel zaman dizesinden (`*_local`, `DASHBOARD_TZ`'de `YYYY-MM-DD HH:MM`, board A3-7 (a)). Tema saat dilimi hesaplamaz. Zaman alanı biçime uymazsa "zaman bilinmiyor".

## 5. Upstream gerçekleri

Kaynaklar: T-0a (`docs/reviews/t0a-upstream-verification-0002.md`), T-0b (`docs/reviews/t0b-measurements-0002.md`, Docker Desktop, Engine 29.9.2, arm64, `lscr.io/linuxserver/bookstack:v26.09.2-ls295`).

| # | Bilgi | Hüküm | Kalan iş |
|---|---|---|---|
| D-1 | Visual theme: `themes/<ad>/`, aynı göreli yol orijinali geçersiz kılar, `APP_THEME`. Kararlılık garantisi yok | verified (T-0a) | – |
| D-1b | `@include('selfhost.x')` partial'a çözülür, ebeveyn değişkenleri geçer, include ızgaradan önce render edilir | PASS (T-0b) | – |
| D-2 | Logical theme kullanılmaz | verified | – |
| D-3 | `themes` → `/config/www/themes` symlink. Volume içinde iç içe read-only bind ilk başlatmada çalışır. Her başlatmada init "chown ... Read-only file system" ve "Permissions could not be set" basar, uygulama çalışır. Hiçbir kriter bu metne bağlı değil | PASS, gürültülü (T-0b) | – |
| D-3b | `VIEW_ROOT=/app/www/resources/views`. sha256 `home/default.blade.php` = `566ef9ce18437aeea4e50d6a8e670aa2a86da4de9467ddfc17caf49c1db9a33c`, `shelves/show.blade.php` = `c9b32a3fbec368c1f449f4553db73fc1c969bd6f9d7a55b56b05a02386e9ed7a` (`v26.09.2-ls295`, arm64) | PASS (T-0b, yalnız arm64) | amd64'te ve 0001 T-1'in son pin'inde CB-8 |
| D-4 | `home/default` liste içermez, `#home-default` + `common.view-blocks` | verified | – |
| D-5 | "Her güncellemeden sonra test et" | verified | – |
| D-6 | `ALLOW_CONTENT_SCRIPTS` kullanımdan kalktı, `APP_CONTENT_FILTERING` (ayarlanmamış = en sıkı). CSP dış img/style host'larını engellemez | partly wrong (düzeltildi) | – |
| D-7 | Container env `env()`'e ulaşır, özel karakterler korunur. `APP_URL` verilmezse `https://example.com` | PASS (T-0b) | – |
| D-8 | Göreli yollar `--project-directory`'ye göre | verified | – |
| D-9 | `opcache.validate_timestamps=1`, `revalidate_freq=2`, mount edilmiş dosyadaki düzenleme yeniden başlatmadan 2-4 s içinde görünür | PASS (T-0b, Docker Desktop) | CB-8 (7) her pin'de statik kontrol |
| D-10 | Controller `shelf`, `sortedVisibleShelfBooks` (PHP dizisi), `view`, `listOptions` verir. Upstream view etiketleri göstermez. `$shelf->tags` yüklü (0 ek sorgu). `order` her zaman 0, sıra pratikte id sırası. Etiket adı büyük/küçük harfini korur (`Plane-Project`) | PASS (T-0b) | – |
| D-11 | `Permission::SettingsManage = 'settings-manage'` | verified | – |
| D-12 | Plane `X-API-Key`, anahtar sahibinin izinleriyle çalışır, okuma-only kapsam yok | verified (T-0a) | – |
| D-12r | 60/dk/anahtar, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, 429. Self-hosted `API_KEY_RATE_LIMIT` (varsayılan `60/minute`). `X-RateLimit-Limit` doğrulanmadı | verified (Cloud) + self-host | T-0c |
| D-12p | Cursor `value:offset:is_prev`, `per_page` varsayılan 20, en fazla 100 | verified | – |
| D-12b | `/users/me/`, `/workspaces/{slug}/members/` (e-posta, isim döner). Rol sayıları belgelenmemiş. `fields=id,role` ve `id` eşleşmesi okunmadı | partly | T-0a2, T-0c |
| D-13 | `projects/`, `work-items/` uç noktaları. State/label liste yolları bulunamadı | verified with changes | T-0a2, T-0c |
| D-13b | Etiketler proje kapsamlı | verified | – |
| D-13c | İş listesinde sunucu tarafı filtre yok, "tümünü gör" URL kalıbı bulunamadı | negative | T-0c |
| D-14 | Çalışma alanı Owner/Member/Guest, proje Admin/Contributor/Commenter/Guest. İşleri listeleyen en düşük rol proje Commenter | wrong terminology (düzeltildi) | T-0c (KR-9) |
| D-15 | `internal` ağ dış çıkışı, DNS'i, host gateway'i ve diğer ağları keser. Alias yalnız iç ağda çözülür, servis adı da çözülür (asıl sınır G-net). Docker Desktop'ta `host.docker.internal` loopback yayınına ulaşır, Linux benzeri gateway ulaşamaz. Gerçek Linux ölçülmedi | partly (T-0b) | T-0c |
| D-16 | `ALLOWED_HOSTS` yok, Caddy `SITE_ADDRESS`, Host yönlendirmesi doğrulanmadı | partly | T-0c |
| D-16b | Plane `proxy`'nin iç dinleme portu | – | T-0c |
| D-20 | CPython EOL ve image bakımı verified, CVE taraması eksik, Alpine paketleri ve lisanslar doğrulanmadı | mixed | **T-0a2 (K2-4), Faz 2a ön koşulu** |
| D-21 | Davetsiz kayıt anahtarı var, SMTP olmadan kullanıcı oluşturma yolu belgelenmemiş | partly | T-0c |
| D-22 | CLI aynı adla ikinci ağı reddeder (Engine 29.9.2), ham API test edilmedi | partly (T-0b) | T-0c |
| D-17 | View enjeksiyonu yalnız logical theme ile | verified | – |
| D-18 | `open_basedir` yok, php-fpm `abc` (uid 1000), dünya-okunur dosyalar gerekli | PASS (T-0b) | – |
| D-19 | Tema ve `/dashfeed` yolları oturumlu ve oturumsuz 404 | PASS (T-0b) | – |
| D-23 | Pinli image'da `user()->isGuest()` var, `collect()` ve Laravel koleksiyonunun dizi biçimli `sortBy([[alan, yön], ...])` sözdizimi var, PHP 8.5'te `strtoupper` yalnız ASCII dönüştürür | – (genel bilgi, doğrulanmadı) | T-3'te pinli image'da doğrulanır, CB-6/CB-10/CB-11 yakalar. Biri yoksa appsec'e döner, kural gevşetilmez |

## 6. Architecture and technology decision

### 6.1 Ana sayfa ve raf mekanizması (ADR-0007)

| Seçenek | Karar |
|---|---|
| A: ana sayfa = bir BookStack sayfası | Red |
| **B-copy: iki view'un birebir kopyası + yalnız `@include` satırları, sha256 + ham bayt diff** | **Seçildi** (board APPROVE) |
| B-part, B', C, D | Red (revizyon 4 gerekçeleriyle) |

**Override biçimi:** `home/default.blade.php` ve `shelves/show.blade.php` pinli upstream dosyasının birebir kopyası. Tek fark, `^\s*@include\('selfhost\.[a-z0-9_.-]{1,64}'\)\s*$` kalıbına uyan eklenmiş satırlar. `home/default`: `@include('selfhost.home')` ızgaranın öncesinde. `shelves/show`: `@include('selfhost.shelf')` ana içerik alanının başında.

**`UPSTREAM` dilbilgisi (critic M5, S3-07):** satır türleri: boş satır, `#` ile başlayan yorum, `BOOKSTACK_IMAGE=<değer>` (tam bir tane), `VIEW_ROOT=<yol>` (tam bir tane), `VIEW <göreli yol> <64 hex>` (sıfır ya da daha fazla, yol tekil), `ALLOW <göreli yol>` (bir ya da daha fazla, yol tekil). Başka her satır, tekrar ya da eksik bir zorunlu satır dosyayı bozuk yapar. Bozuk ya da eksik `UPSTREAM` → CB-8 başarısız ve `stack`'te kilit açık (U-20a, fail closed).

**`ALLOW` ve `VIEW` eşlemesi (critic H6, L4):** `ALLOW` tema klasöründeki **her** dosyayı listeler, meta dosyalar dahil: `UPSTREAM`, `PHP_ALLOWLIST`, `ACCESS_ALLOWLIST`, `README`. `selfhost/` altındaki ve meta olmayan her `ALLOW` yolunun bir `VIEW` satırı vardır ve her `VIEW` satırının bir `ALLOW` satırı vardır (CB-8 (6)). KR-8 silmesi **ya hep ya hiç**: ya bütün override'lar ve onların `VIEW`/`ALLOW` satırları silinir ya da hiçbiri.

**Tema kilidi (KR-8, C-14, board K3-1, critic H1, S3-07).** `stack` container'a verilecek `APP_THEME`'i şu tablodan seçer. "Tema kaydı geçerli" = `UPSTREAM` dilbilgisine uyar, `BOOKSTACK_IMAGE` normalize config'teki BookStack image değerine tam dize eşit ve en az bir `VIEW` satırı var.

| `SELFHOST_DASHBOARD` | `local/bookstack.env` `APP_THEME` | Tema kaydı | Container `APP_THEME` | Uyarı | Tema kopyalanır mı (C-16) |
|---|---|---|---|---|---|
| `0` | herhangi (boş dahil) | – | makinenin değeri (boşsa boş) | yok | hayır |
| `1` (ya da anahtar yok) | başka tema | – | makinenin teması, olduğu gibi | yok | hayır |
| `1` | boş / `selfhost-dashboard` | geçerli | `selfhost-dashboard` | yok | evet |
| `1` | boş / `selfhost-dashboard` | pin uyuşmuyor ya da `UPSTREAM` bozuk/eksik | boş | U-20a, exit 0 | hayır |
| `1` | boş / `selfhost-dashboard` | `VIEW` satırı yok (KR-8) | boş | U-20b, exit 0 | hayır |

Uyarı yalnız kilit durumunda basılır, `SELFHOST_DASHBOARD=0` ve makinenin kendi teması uyarı üretmez. Kilit yalnız dashboard temasını etkiler. `./stack config bookstack` aynı tabloya göre aynı `APP_THEME`'i ve aynı uyarıyı gösterir. `./stack status` iki değeri gösterir: repo'nun bugünkü kararı ve çalışan container'ın `APP_THEME`'i, farklıysa "`./stack up bookstack` gerekli" (C-10).

**Tema dağıtım sınırı (S3-03, C-16).** Container'a mount edilen tema repo klasörü değil, `local/state/theme/selfhost-dashboard/` kopyasıdır (gitignored, yedeğe girmez çünkü 0001 AC-11 yedeğe hiç `local/` dosyası almaz). `./stack up bookstack` parser, guard'lar, AC-13 kontrolü ve tema kilidi geçtikten sonra, ve yalnız tabloda "evet" satırında, repo'daki `stacks/bookstack/theme/selfhost-dashboard/`'ı bu dizine eşitler. Eşitleme **yerinde** yapılır: her dosya aynı dizinde geçici dosya + `rename` ile yazılır, repo'da olmayan dosyalar silinir. Dizinin kendisi değiştirilmez, çünkü bind mount dizinin kendisine bağlıdır ve değiştirilen bir dizin container'da görünmez (aynı sebep: board K-3). Kopyada modlar her zaman dosya `0644`, dizin `0755`'tir (D-18, `abc` kullanıcısı okuyabilsin). Bu, board'un "dünya-okunur değilse uyar" önerisini gereksiz kılar. `up` 5 ile ya da başka bir hatayla durursa ya da kilit açıksa kopya değişmez. İsteğe bağlı ek kontrol (appsec LOW): kopyalamadan önce `VIEW` sha256'ları yerel pinli image'a karşı (`--network none --entrypoint cat`) yeniden doğrulanır. Uygulanıp uygulanmayacağına T-2 karar verir, kriter değildir.

T-0b'nin ölçtüğü davranışla ilişkisi: T-0b, mount edilmiş dosyadaki bir düzenlemenin 2-4 s içinde göründüğünü ölçtü (D-9). Önceki revizyonda mount repo'yu gösterdiği için `git pull` tek başına sayfayı değiştiriyordu. Şimdi `git pull` mount edilmiş kopyaya dokunmaz, sayfa değişmez (CB-30 (g)). `up bookstack` kopyayı yerinde güncellediği için aynı opcache yeniden doğrulaması devreye girer ve metin 2-4 s içinde görünür. Container yeniden yaratılmaz (CB-9).

**Opcache koruması (board K3-2).** Etiketsiz yayılma pinli image'ın opcache ayarına bağlıdır. CB-8 (7) quick profilde pinli image'ın etkin `opcache.validate_timestamps` değerinin `1` ve `opcache.revalidate_freq` değerinin ≤ 2 olduğunu ve php-fpm havuz dosyalarında bunları ezen bir `php_admin_value`/`php_value` satırı olmadığını doğrular. CB-8 bump alt kümesindedir. Bir bump bu ayarı değiştirirse test kırmızı olur ve container etiketi kararı yeniden açılır (ADR-0007 tetikleyicisi).

**Veri erişimi: `ACCESS_ALLOWLIST` (K2-1, board A3-4).** Partial'ların okuyabildiği nesne erişimleri repo'daki numaralı listededir (Faz 1):

| # | Erişim | Not |
|---|---|---|
| A-1 | `$shelf->tags->sortBy('id')->where('name', 'plane-project')` ve bunun `->first()`, `->count()` | etiketler yüklü (D-10), bellekte |
| A-2 | etiket öğesi `->value` | başka alan yok |
| A-3 | `collect($sortedVisibleShelfBooks)->sortBy([['updated_at', 'desc'], ['id', 'desc']])->take(5)` ve `->isEmpty()`, öğe `->name`, `->getUrl()`, `->updated_at` | gösterim alanları |
| A-4 | `userCan('settings-manage')` | fonksiyon |
| A-6 | `user()->isGuest()` | misafir tespiti (critic H3, D-23) |

Faz 2a'da A-5 (snapshot anahtarları) ve `data` partial'ı eklenir (K3-3). Liste değişikliği disiplini (board A3-4): yalnız (i) A-3 öğelerinin gösterim alanları ve (ii) listedeki koleksiyonlar üzerinde yalnız sabit dize, sayı ya da sabitlerden oluşan dizi argümanlı, bellekte çalışan koleksiyon metodları (`sortBy`, `sortByDesc`, `take`, `first`, `where`, `isEmpty`, `count`) eklenebilir. İlişki yükleyen ya da sorgu çalıştıran her metod (`load`, `loadMissing`, `fresh`, `refresh`, `query`, `->books()` gibi ilişki metodu çağrısı) ve callable argüman yasaktır. `ACCESS_ALLOWLIST`'in her diff'i tam appsec stop-B ister.

**PHP ve Blade kuralları (S2-02, S3-01, critic H2).** Tarama iki aşamalıdır, pinli BookStack image'ında `--network none` ile:

1. **Blade kaynağı üzerinde** (aşağıdaki bütün kurallar):
   - Değişken allowlist'i: `$shelf`, `$sortedVisibleShelfBooks`, `ACCESS_ALLOWLIST`'te adı geçen `@foreach` takma adları, `$loop`. Faz 2a: `data` partial'ının snapshot değişkeni. Yasak: `$app`, `$this`, `$cspNonce`, `$errors`, her `$__*`, bütün süper globaller (`$_SERVER`, `$_ENV`, `$_GET`, `$_POST`, `$GLOBALS` ...).
   - Üye erişimi sayılanlar: `->`, `?->`, `::`, `[...]`, `{...}`. Hepsi `ACCESS_ALLOWLIST`'e karşı kontrol edilir. Dizi erişimi yalnız snapshot'tan türetilen değişkenlerde (Faz 1'de hiç yok). `::` izinli listesi boştur.
   - `@foreach` kaynakları yalnız allowlist'teki ifadeler. `@foreach` başlıkları dışında atama operatörü yok.
   - Çağrı tespiti `T_STRING`, `T_NAME_FULLY_QUALIFIED`, `T_NAME_QUALIFIED` token'larını kapsar. Her fonksiyon `PHP_ALLOWLIST`'te. Sabit, dizi ya da parantezli ifade üzerinde çağrı, closure (`fn`, `function`) ve `(...)` callable sözdizimi yasak.
   - `env()`/`getenv()` tam bir sabit dize argümanla ve yalnız `'SELFHOST_PENPOT_URL'`, `'SELFHOST_PLANE_URL'`, `'SELFHOST_PENPOT_STATE'`, `'SELFHOST_PLANE_STATE'` için. Argümansız çağrı yasak.
   - `file_get_contents` Faz 1'de yasak. Faz 2a'da yalnız `data` partial'ında ve yalnız `('/dashfeed/snapshot.json', false, null, 0, 1048577)` sabit argüman kümesiyle.
   - Yasak çağrılar ve yapılar: `config(`, `@inject`, `@php`, `new `, `app(`, `resolve(`, `call_user_func`, değişken çağrıları, `{!!`, `HtmlString`, `Html::`, `include`/`require`, `exec`, `shell_exec`, `system`, `passthru`, `proc_open`, `popen`, backtick, `eval`, `Storage::`, `File::`, `readfile`, `SplFileObject`, `Process`, `request(`, `DB::`, `Http::`, `curl`, `fsockopen`, `stream_socket`, `file_put_contents`, `unlink`. Kaynakta `<?` yok.
   - Blade direktif allowlist'i: `@if`, `@elseif`, `@else`, `@endif`, `@foreach`, `@endforeach`, `@forelse`, `@empty`, `@endforelse`, `@isset`, `@endisset`, `@include`. Başka her direktif (`@each`, `@includeWhen`, `@includeIf`, `@json`, `@verbatim` dahil) başarısız. Partial'lardaki `@include` da tek argümanlı `selfhost.*` kalıbına uyar.
   - `/` ile başlayan dize sabitleri Faz 1'de yalnız `'/books'`.
   - Partial HTML'inde statik yasak: `<script`, `on*=` öznitelikleri, `<base`, `<meta http-equiv`, `<form`, `<iframe`, `<object`, `<embed`, `<link`, `javascript:`.
2. **Derlenmiş çıktı üzerinde:** partial'lar Laravel'in Blade derleyicisiyle derlenir. Derleyicinin ürettiği **tam** ifadeler, yalnız derleyici şablonlarıyla birebir eşleştiklerinde çıkarılır: `$__env->make(...)->render()` (`Arr::except(get_defined_vars(), ['__data', '__path'])` argümanıyla), `$__env->addLoop(...)`, `$__env->incrementLoopIndices()`, `$__env->getLastLoop()`, `$__env->popLoop()`, `\Illuminate\Support\Arr::except(...)`, `get_defined_vars()`, `e(...)` (`{{ }}` escape'i), `echo`, `<?php`/`?>`. Kalan token'lar 1. aşamanın kurallarından geçer. Şablona uymayan bir `$__env` kullanımı (ör. `$__env->getContainer()`) başarısızdır.

Her kural için `tests/` altında bir negatif fixture vardır ve tarayıcı onu yakalamalıdır (CB-7 (e)).

**Yükseltmede appsec incelemesi (appsec S3-02, ADR-0007 G-4 kararı, son metin).**
- **M-1, normal BookStack bump:** yalnız şunların **hepsi** sağlanırsa mekanik inceleme yeterlidir:
  - (a) Merge base'e göre diff tam iki dosyaya dokunur, her birinde bir satır değişir (2 silme + 2 ekleme): `stacks/bookstack/versions.env`'deki BookStack app image satırı ve `UPSTREAM`'deki `BOOKSTACK_IMAGE=` satırı. İki yeni değer bayt düzeyinde aynıdır ve tag + digest biçimindedir. Diff denetleyicisi **base dalından** çalıştırılır, PR head'inden asla. Script'in sahibi T-5 (qa-engineer).
  - (b) CB-8, base dalının test script'leriyle arm64 ve amd64'te geçer.
  - (c) Otomatik güvenlik alt kümesi yeni pin'de geçer: CB-1, CB-3, CB-4, CB-6 (a)-(c), CB-7 (hepsi), CB-10 (S3-06 doğrulaması dahil), CB-11, CB-30, ve Faz 2a'dan CB-21 ile CB-24.
  - (d) PR atlanan her sürümün sürüm notlarına, sadece revizyon bump'ında (`-ls295` → `-ls296`) linuxserver değişiklik günlüğüne bağlantı verir ve şu alanların her biri için "dokunuyor: evet/hayır" yazar: tema sistemi, view'lar ve view block'lar, izinler/roller/görünürlük, CSP ve içerik filtreleme, Blade escape'i, entity/raf controller'ları, PHP sürümü, nginx ve php-fpm yapılandırması, güvenlik bildirimleri.
  - (a)-(d)'den biri tutmazsa (diff iki satırdan büyükse dahil) tam appsec stop-B. Appsec örnekleme yapabilir ya da M-1'i geri çekebilir.
- **M-2, KR-8 silme PR'ı:** diff = M-1 (a)'daki satırlar + **bütün** override dosyalarının, bütün `VIEW` satırlarının ve onların `ALLOW` satırlarının silinmesi, başka ekleme yok. CB-8 (5) ve CB-30 geçer. (d) gerekmez, çünkü kilit temayı tamamen kapatır. Kısmi silme tam stop-B.
- M-1 ancak 0001 T-11'in (branch protection, 2FA) uygulandığı doğrulandıktan sonra kullanılabilir (appsec I-1). O zamana kadar her bump tam stop-B.
- Plane bump metni Faz 2a'nın işidir.

### 6.2 Plane verisi nerede çekilir? (Faz 2a)

| Seçenek | Karar |
|---|---|
| S1 tema PHP'si her açılışta | Red |
| **S2 toplayıcı sidecar `dashfeed`** | **Seçildi** |
| S3 `up` sırasında host'ta | Red |
| S4 tarayıcı JS'i | Yasak |

### 6.3 Image'lar

**Toplayıcı image'ı (B-3, Faz 2a):**

| Alternatif | Karar |
|---|---|
| (0) pinli linuxserver/bookstack PHP'si | Red: s6 ile root başlar, BookStack kodu ve servisleri, bump bağımlılığı |
| **(a) `python:3.14.<patch>-alpine3.24@sha256:...`** | **Seçildi, K2-4 koşullu** |
| (a') `python:3.15.<patch>-alpine3.24` (board K3-5) | Red (v1): en uzun destek penceresi onda, ama 3.15 yeni bir `.0`/`.1` serisi (PEP 790'a göre 2026-10'da çıkmış olması beklenir, doğrulanmadı), 3.14 ise yaklaşık bir yıllık bugfix sürümüyle olgun. T-0a2 3.15'in yayın durumunu ve `alpine3.24` varyantını kaydeder. Yükseltme tetikleyicisi: 3.15.2'nin çıkması ya da 3.14 bugfix desteğinin bitmesi (2027-10), hangisi önce |
| (b) `-slim` | Red |
| (c) distroless | Red (v1): patch düzeyinde tag ve taban dağıtım bağlılığı doğrulanmadı |
| (d) busybox + jq | Red |

**K2-4 kabul eşiği (T-0a2):** seçilen pin için CPython advisory listesi (en az `urllib`, `http.client`, `socket`, `json`, `re`), CVE-2026-116566'nın düzeltildiği sürüm okunur ve pin o sürüm ya da sonrası olur, pinli image'daki Alpine paketleri (`apk info -v`) için OSV/Alpine secdb sorgusu, lisanslar kaynağından. Toplayıcının kullandığı bir bileşende düzeltmesi olan ama pinde düzeltilmemiş High/Critical açık olmamalı. Düzeltmesi olmayan High/Critical açık appsec'e ve CEO'ya gider. T-0a2 tamamlanmazsa image reddedilir ve Faz 2a imzalanamaz.

**Test image'ı `docker:<tag>-dind` (K2-7, K3-4):** ihtiyaç §1 madde 4 (Linux Engine davranışı: CB-9 Faz 1'de, CB-13 Faz 2a'da). Alternatifler: Linux VM (CEO istemedi), testi atlamak, Linux CI runner (gelecek). Pin: `tests/versions.env` içinde `DIND_IMAGE=docker:<tag>-dind@sha256:...`, 0001 G-img kapsamı dışı (test harness). Lisans: Moby, Apache-2.0, **T-0d doğrular (T-5'ten önce)**. `privileged` yalnız test harness'ında. Kalan sınır: Docker Desktop VM çekirdeğini paylaşır. Faz 1 imzasında CEO'ya yeni test image'ı olarak gösterilir.

### 6.4 Sidecar Plane'e nasıl ulaşır? (ADR-0006, Faz 2a)

| Seçenek | Karar |
|---|---|
| N1 `host.docker.internal:8703` | Red. Docker Desktop'ta çalışır ama Linux benzeri gateway loopback yayınına ulaşamaz (D-15). Mac'te çalışıp Linux'ta kırılacak bir tasarım olur |
| **N2 paylaşılan iç ağ `selfhost-dashfeed`** | **Seçildi** |
| N3 bridge IP'ye bind | Red |
| Plane `default` ağına bağlamak | Red |

Ağ kuralları:
- `selfhost-dashfeed`: `driver: bridge`, `internal: true`, etiket `com.selfhost.managed=dashfeed`. Compose'da yalnız `external: true` ve `name` (D-15). `stack` oluşturur.
- Garanti adımı (C-6): `up bookstack` ve `up plane`'de AC-13 kontrolünden sonra, `pull`'dan önce. Yoksa oluşturur. Varsa `Internal=true`, `Driver=bridge` ve etiketi doğrular. Aynı adla birden fazla ağ görünürse ya da biri eksikse exit 2, silmeden. `config`, `status`, `down` ağı oluşturmaz.
- **G-net (C-12):** bağlı servis kümesi BookStack'te tam `{dashfeed}`, Plane'de tam `{proxy}`, diğer her projede boş. İç ağda servis adı da çözüldüğü için (D-15) asıl sınır budur.
- `dashfeed` yalnız bu ağa bağlı, hiçbir portta dinlemez. Plane `proxy` alias `plane-proxy-dashfeed` taşır ve `default`'u korur.
- İç adres sabit: `PLANE_INTERNAL_URL=http://plane-proxy-dashfeed:<D-16b>`. `Host` header'ı `SELFHOST_PLANE_URL`'in host:port'u, `^[A-Za-z0-9.-]{1,253}(:[0-9]{1,5})?$` ile doğrulanır.
- README: `stacks/plane` altında `stack`'siz `docker compose up` desteklenmez.

### 6.5 Toplayıcı davranışı (Faz 2a; spec toplama Faz 2b)

**Yaşam döngüsü:** `dashfeed` yalnız §6.1 tablosunda container `APP_THEME`'i `selfhost-dashboard` olan satırda çalışır. Diğer satırlarda `stack` `--scale dashfeed=0 --scale dashfeed-init=0` verir (volume'lar korunur). `up bookstack` `--remove-orphans` kullanır (Faz 1'den itibaren).

**Çalışma modları:** (1) tam mod: Plane (2a) + spec'ler (2b). (2) Plane kapalı: `plane` `ENABLED_STACKS` dışında ya da `DASHBOARD_PLANE=0`. Plane'e istek yok, token container'a verilmez, `status: plane_disabled`, Plane bölümleri snapshot'ta temizlenir, spec'ler (2b) toplanır. (3) Token ya da slug boş, ya da `local/dashfeed.env` yok: `not_configured`.

**Sertleştirme:** `user: "65534:65534"`, `read_only: true`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, `tmpfs: /tmp`, soket yok. Yazılabilir tek yer `/out`.

**`dashfeed-init` (S2-12, K-1):** aynı pinli image, `network_mode: none`, `user: "0:0"`, `read_only: true`, `security_opt: [no-new-privileges:true]`, **`cap_add` yok** (0001 G-iso). `cap_drop` varsayılan yeteneklerin `CHOWN` dışındaki hepsini listeler (`AUDIT_WRITE`, `DAC_OVERRIDE`, `FOWNER`, `FSETID`, `KILL`, `MKNOD`, `NET_BIND_SERVICE`, `NET_RAW`, `SETFCAP`, `SETGID`, `SETPCAP`, `SETUID`, `SYS_CHROOT`). Yalnız `/out` bağlı. Sabit, özyinelemesiz komut: `chown 0:0 /out && chmod 0755 /out && chown 65534:65534 /out`. `dashfeed` buna `depends_on: condition: service_completed_successfully` ile bağlıdır. Çıkmış init container'ının yeniden başlatılması yeniden yaratma değildir (0001 AC-1).

**Mount biçimi:** snapshot her iki tarafta **dizin**: `dashfeed` → `/out` (rw), BookStack → `/dashfeed` (ro). Yazma: aynı dizinde geçici dosya + `rename`. Dosya `0644`, dizin `0755`.

**Sağlık (C-11):** toplayıcı her döngü denemesinin başında `/out/heartbeat`'e zaman yazar, ilk yazma süreç başlar başlamaz. Healthcheck: heartbeat yaşı < max(3 × etkin aralık, 120 s), `start_period: 30s`. `up`'ın health beklemesi ilk döngünün bitmesine ya da Plane'e bağlı değildir.

**HTTP istemci kuralları (S-08, S2-09):** yalnız `GET`, yalnız `PLANE_INTERNAL_URL` + §7.4 sabit yol ve parametreler. Yönlendirme izlenmez (3xx `error`). Boş `ProxyHandler({})`. Yanıttaki URL'ler istenmez. Cursor `^[A-Za-z0-9:_-]{1,64}$` ve URL-encode. İstek başına 5 s duvar saati. Okuma 5 MB'ta kesilir (`error`). `Accept-Encoding` gönderilmez. Döngü başına üst süre 10 dakika, aşılırsa yayımlanmadan `error` (`cycle_timeout`).

**Rol kontrolü (S-01, S2-01, S2-11):** ilk döngüde ve her 10 döngüde bir çalışma alanı rolü okunur, üye çağrısı en aza indirilir (T-0a2). Rol sayılarının anlamı T-0c ile `feed.py`'de sabitlenir. Owner ya da Workspace Admin → `token_too_privileged`. Rol belirlenemez (bozuk yanıt, alan yok, bilinmeyen sayı, `id` eşleşmiyor) → `token_role_unknown`, iş verisi çekilmez (fail closed). Her iki durumda Plane bölümleri temizlenir. Üye listesindeki e-posta ve isimler bellekte hemen atılır.

**Filtreleme (D-13c):** işler proje başına `order_by=-updated_at`, `per_page=100` ile sayfalanır. Açık/kapalı, etiket ve "son 7 gün" toplayıcıda uygulanır. State/label listeleri bulunan yollardan, yoksa `expand=state,labels`.

**İstek bütçesi (K-4, S2-09):** etkin bütçe = min(`DASHFEED_REQ_PER_MIN`, ⌊`X-RateLimit-Limit` / 2⌋ header varsa). `Remaining` < 5 → bekleme = min(`Reset` − şimdi, 60 s), geçmişteki ya da sayı olmayan `Reset` yok sayılır. Kalemler: projeler 1 (≤ 30 proje), proje başına işler 1-5 sayfa (en son güncellenen 500), rol 1-2 her 10 döngüde, proje başına state ve label 2 her 10 döngüde (expand yolunda 0). Proje sınırı 30. Tipik ≈ 46 istek → ~1,5 dk, en kötü ≈ 151 istek → ~5 dk. Etkin aralık = max(`DASHBOARD_REFRESH_SECONDS`, ⌈döngü istekleri / bütçe⌉ × 60 s). 429 → `rate_limited`, son veri korunur. Tamamlanmamış döngü yayımlanmaz.

**Kesme:** açık işler toplam 500: önce her projeden bütün açık `ceo_question` işleri ve en az 10 diğer açık iş, sonra kalan kota `ceo_question` önce, `updated_at` azalan. Son 7 günde kapananlar toplam 100, her projeden en az 3. `items_truncated` = bir projede 500 sayfa sınırı **ya da** toplam kesmede bir iş düştü.

**Zaman (A3-7 (a)):** toplayıcı her zaman alanının yanına `DASHBOARD_TZ`'de yerel zaman dizesi (`<alan>_local`, `YYYY-MM-DD HH:MM`) yazar. `DASHBOARD_TZ` boşsa `up` anında host'un saat dilimi verilir, okunamazsa `UTC` + uyarı.

**Log (S-11):** yalnız durum değişiklikleri. Yanıt gövdesi, header, token, kişisel veri loglanmaz.

### 6.6 Plane projesi ↔ BookStack rafı eşlemesi

| Seçenek | Karar |
|---|---|
| **P1 raf etiketi `plane-project` = `<KOD>`** | **Seçildi** |
| P2 `?project=`, P3 git, P4 `local/` | Red |

Etiket kuralları (S3-01 ile uygulanabilir hale getirildi, §15.3):
- Etiketler `id` sırasıyla okunur (A-1). Yalnız adı **tam olarak** `plane-project` (küçük harf) olan etiketler aday sayılır. BookStack etiket adının harfini korur (D-10). README küçük harf yazılmasını söyler, `Plane-Project` adlı bir etiket aday değildir.
- Karar **ilk adaya** göre verilir: değeri `trim`, sonra ASCII `strtoupper`, sonra `^[A-Z0-9]{1,12}$`. Geçerliyse başlık "Proje: <KOD>". Geçersizse U-22 (ham değer kaçışlanmış gösterilir), sonraki adaylara bakılmaz.
- Birden fazla aday varsa U-23 ek notu.
- Etiket değeri yalnız (Faz 2a'da) snapshot içinde sözlük anahtarıdır, hiçbir isteğe, yola ya da sorguya girmez.

### 6.7 CEO soruları ve spec'ler (Faz 2a, 2b)

**Plane soruları (KR-2, Faz 2a):** etiket `ceo-soru` (`DASHBOARD_CEO_LABEL`), her projede ayrı oluşturulur (D-13b). Toplayıcı etiketi olmayan projeleri yalnız label listesi alınabildiğinde `projects_missing_label`'a yazar, alınamadıysa alan `null`. Kural: etiketli ve state grubu `completed`/`cancelled` olmayan iş "sizi bekliyor" sayılır.

**Spec soruları, imzalar, taslaklar (KR-2, KR-5, Faz 2b):**
- Klasörler: `local/dashfeed.env` içindeki `DASHBOARD_SPEC_DIRS` (iki nokta üst üste ile ayrılmış mutlak yollar). Boş = bu repo'nun `docs/` klasörü.
- `stack` doğrulaması (S-05, S2-08): her yol önce `realpath` ile çözülür, bütün kontroller çözülmüş yola uygulanır: `^[A-Za-z0-9._/ -]+$`, mutlak, var, dizin, son bileşeni `docs` ya da `specs`, ya da `specs/active` ile biter, içinde doğrudan `.git` yok, 0001 G-iso'nun `/` ve `$HOME` kuralını geçer. Aksi halde `up` exit 2 ve yol adıyla mesaj. Mount'lar uzun sözdizimiyle, tırnaklı yolla, `read_only: true` olarak `/specs/<kaynak>` altına üretilir.
- Toplayıcı: yalnız derinlik 1'deki `*.md`. Her girdi `lstat`, sembolik bağlantılar atlanır, `O_NOFOLLOW`, dosya başına 64 KB, toplam 500 dosya. Kökünde `.git` olan kaynağı reddeder.
- Ayrıştırma: `Status` = ilk 30 satırdaki ilk `^(?:- )?Status:\s*(.+?)\s*$`, değer ilk ` (`'den önceki kısım. Başlık = ilk `^# `. Bölüm başlıkları önek ve büyük/küçük harf duyarsız: `## Signature record` ile başlayan başlık, "Open questions" ya da "açık sorular" içeren `## ` başlığı. İmza satırları `^Approved by / on(?: \(([^)]{1,20})\))?:\s*(.*)$`, boş değer = bekleyen parça. Sorular `^- \*\*(S-\d{1,3}):\s*(.+?)\*\*`.
- Gösterim: "İmza bekliyor" = `Awaiting approval`, ya da `Approved` ama bekleyen imza parçası var. "Taslak" = `Draft`. Bekleyen sorular "Spec soruları" altında. `In progress`, `Shipped` listelenmez. Sıra: kaynak, sonra yol. Bağlantısız.

### 6.8 Bileşenler nasıl bağlanıyor? (Faz 1)

```mermaid
%% Soru: Faz 1'de tema dosyaları repo'dan BookStack'e nasıl ve ne zaman ulaşıyor?
flowchart LR
  R["repo: stacks/bookstack/theme (git)"] --> UP["./stack up bookstack"]
  UP --> CK{"parser, guard, AC-13, tema kilidi"}
  CK -- "geçti, tablo 'evet'" --> CP["local/state/theme (kopya, 0644/0755)"]
  CK -- "kilit ya da hata" --> NO["kopya değişmez"]
  CP -- "ro bind" --> B["BookStack container"]
  B --> U["tarayıcı: 127.0.0.1:8701"]
```
Açıklama: repo'daki tema yalnız `up bookstack` sırasında ve bütün kontroller geçtikten sonra makinedeki kopyaya taşınır. Container yalnız kopyayı görür. Metin karşılığı: (1) `git pull` repo'yu değiştirir, kopyaya dokunmaz. (2) `./stack up bookstack` kontrolleri çalıştırır. (3) Geçerse ve tablo "evet" diyorsa kopya yerinde güncellenir. (4) Kilit açıksa ya da bir hata varsa kopya değişmez. (5) BookStack kopyayı read-only görür ve 2-4 s içinde yeni metni sunar.

**Faz 2a:** Plane verisi token tarayıcıya ya da BookStack'e girmeden nasıl ulaşıyor?

```mermaid
%% Soru: Plane verisi, token tarayıcıya ya da BookStack'e girmeden dashboard'a nasıl ulaşıyor?
flowchart LR
  L["local/dashfeed.env (token, 600)"] --> F["dashfeed (sadece iç ağ)"]
  SP["spec klasörleri (ro, 2b)"] --> F
  F -- "GET, selfhost-dashfeed (internal)" --> P["Plane proxy (alias)"]
  F -- "/out (rw)" --> J["snapshot volume (dizin)"]
  J -- "/dashfeed (ro)" --> B["BookStack + tema"]
  B --> U["tarayıcı: 127.0.0.1:8701"]
```
Açıklama: token yalnız toplayıcıda durur. Toplayıcı Plane'i iç ağdan okur, temizlenmiş veriyi bir dizine yazar, BookStack o dizini salt okunur görür. Metin karşılığı:

| Bileşen | Ağlar | Okur | Yazar |
|---|---|---|---|
| BookStack app | bookstack `default` | tema kopyası (ro), `/dashfeed` (ro) | kendi `/config` |
| MariaDB | bookstack `default` | – | kendi volume'u |
| dashfeed-init | yok | – | `/out` sahipliği |
| dashfeed | yalnız `selfhost-dashfeed` | env, `/specs/*` (ro, 2b), `feed.py` (ro) | yalnız `/out` |
| Plane proxy | plane `default` + `selfhost-dashfeed` | – | değişmez |
| Diğer Plane servisleri, Penpot | kendi `default`'ları | – | köprüye kapalı (G-net) |

## 7. Data and contract

### 7.1 Dosyalar

| Yol | Git | İçerik | Faz |
|---|---|---|---|
| `stacks/bookstack/theme/selfhost-dashboard/home/default.blade.php`, `shelves/show.blade.php` | evet | upstream kopyası + `@include` satırları | 1 |
| `.../selfhost/home.blade.php`, `shelf.blade.php`, `cards.blade.php` | evet | Faz 1 partial'ları | 1 |
| `.../selfhost/data.blade.php` ve Faz 2a/2b blok partial'ları | evet | snapshot okuma ve bloklar | 2a, 2b |
| `.../UPSTREAM` | evet | §6.1 dilbilgisi, `VIEW_ROOT=/app/www/resources/views` | 1 |
| `.../PHP_ALLOWLIST`, `.../ACCESS_ALLOWLIST`, `.../README` | evet | §6.1 | 1 |
| `local/state/theme/selfhost-dashboard/` | **hayır** | tema kopyası (C-16) | 1 |
| `stacks/bookstack/dashfeed/*`, `stacks/plane/compose.yaml` değişikliği, `DASHFEED_IMAGE` | evet | Faz 2a | 2a |
| `local/bookstack.env` | **hayır** | `SELFHOST_DASHBOARD`, `APP_THEME` | 1 |
| `local/dashfeed.env` | **hayır** (600) | §7.3 Faz 2a, `DASHBOARD_TZ` dahil | 2a |
| `local/state/bookstack.specmounts.yaml` | **hayır** | Faz 2b | 2b |
| `tests/bookstack-dashboard.sh`, `tests/blade_scan/` (tarayıcı + negatif fixture'lar), `tests/upgrade_diff_check.sh` (M-1 (a)), `tests/versions.env` | evet | §11 | 1 |
| `tests/fake-plane/`, `tests/schema_check.py` | evet | Faz 2a | 2a |

### 7.2 Snapshot sözleşmesi (Faz 2a)

```mermaid
%% Soru: snapshot'ta hangi varlıklar var ve birbirine nasıl bağlı?
erDiagram
  SNAPSHOT ||--o{ PROJECT : projects
  PROJECT ||--o{ ITEM : "items (açık)"
  PROJECT ||--o{ RECENT_CLOSED : "recent_closed (7 gün)"
  SNAPSHOT ||--o{ SPEC : "specs (2b)"
  SPEC ||--o{ QUESTION : questions
```
Açıklama: snapshot projeleri ve (Faz 2b'de) spec'leri taşır. İş-proje bağı `project` = `identifier` ile kurulur. Metin karşılığı: aşağıdaki tablolar.

**Şema dosyası ve doğrulayıcı (K2-6):** `snapshot.schema.json` yalnız `type`, `required`, `enum`, `pattern`, `maxLength`, `maxItems`, `properties`, `items`, `additionalProperties: false` ve tür listesi kullanır. `tests/schema_check.py` (stdlib, qa-engineer) bu alt kümeyi uygular, başka bir anahtar görürse başarısız olur. `specs` alanı isteğe bağlıdır, Faz 2a yazmaz, Faz 2b yazar.

**SNAPSHOT (kök):** `schema` (1), `tz` (string, kullanılan saat dilimi), `generated_at` (string|null, son tamamlanmış Plane döngüsü, UTC), `last_attempt_at` (string), `refresh_seconds` (int), `status` (enum: `ok`, `not_configured`, `plane_disabled`, `token_too_privileged`, `token_role_unknown`, `auth_failed`, `rate_limited`, `plane_unreachable`, `error`), `token_role` (enum|null: `owner`, `admin`, `member`, `guest`, `unknown`), `error_detail` (string|null, ≤ 200, sabit kalıp), `plane_base_url` (string|null), `projects_truncated`, `items_truncated` (bool), `projects_missing_label` (string[]|null), `open_counts`, `ceo_counts` (object), `specs_skipped` (int, 2b). Her zaman alanının yanında `<alan>_local` (string|null, `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$`, `tz`'de).

**Duruma göre alanlar:**

| `status` | `generated_at` | projects/items/recent_closed | `plane_base_url` | `token_role` | `error_detail` | Tema veri gösterir mi? |
|---|---|---|---|---|---|---|
| `ok` | dolu | veri | dolu | `member`/`guest` | null | evet |
| `not_configured` | null | boş | `SELFHOST_PLANE_URL` ya da null | null | null | hayır |
| `plane_disabled` | null | boş (temizlenir) | null | null | null | hayır |
| `token_too_privileged` | null | boş (temizlenir) | dolu | `owner`/`admin` | null | hayır |
| `token_role_unknown` | null | boş (temizlenir) | dolu | `unknown` | sabit kalıp | hayır |
| `auth_failed` | önceki | önceki | dolu | önceki | `HTTP 401`/`HTTP 403` | yalnız `generated_at` 24 saatten yeniyse |
| `rate_limited` | önceki | önceki | dolu | önceki | `HTTP 429` | evet |
| `plane_unreachable` | önceki | önceki | dolu | önceki | `timeout`/`connect` | evet |
| `error` | önceki | önceki | dolu | önceki | sabit kalıp (`HTTP 404`, `cycle_timeout` ...) | evet |

**PROJECT** (≤ 30): `identifier`, `name` (≤ 200), `url`, `all_items_url` (null, D-13c). **ITEM** (≤ 500, açık): `key`, `project`, `name` (≤ 200), `state` (≤ 60), `state_group`, `priority`, `ceo_question`, `updated_at`, `updated_at_local`, `url`. **RECENT_CLOSED** (≤ 100, en az 3/proje): `key`, `project`, `name`, `state_group`, `updated_at`, `updated_at_local`, `url`. "Son 7 gün" = kapalı state grubu ve `updated_at` son 7 gün içinde. **SPEC** (2b, ≤ 50): `source`, `path`, `title`, `status`, `pending_parts` (string[]), `group` (`imza`/`taslak`). **QUESTION** (2b, spec başına ≤ 10): `id`, `text`.

**Kurallar:** yalnız bu alanlar. Açıklama, yorum, kişi bilgisi yazılmaz. Bütün `url`'ler toplayıcıda `plane_base_url` + sabit kalıp + doğrulanmış UUID/identifier ile kurulur. Dosya ≤ 1 MB.

**Tema tarafı doğrulama (güven sınırı 6, S2-07):** `data` partial'ı dosyayı yalnız §6.1'deki sabit argüman kümesiyle okur: dosya yoksa U-2, okunamazsa, 1 MB'ı aşarsa ya da türler yanlışsa U-3. Bağlantı kuralı: `SELFHOST_PLANE_URL` boşsa hiçbir Plane `href`'i basılmaz. Değilse URL ayrıştırılır, şema, host ve port `SELFHOST_PLANE_URL`'inkilerle tam eşit olmalı, `userinfo` olmamalı, yol `/` ile başlamalı. Aksi halde bağlantısız metin. Her metin `{{ }}` ile escape edilir. Dış bağlantılar `rel="noopener noreferrer"` taşır.

**Blok sınırları:** Sizi bekleyenler en fazla 20 Plane işi (2b'de + 20 spec satırı + 20 spec sorusu). Açık işler: grup sırası `started` > `unstarted`, grup içinde öncelik `urgent > high > medium > low > none`, sonra `updated_at` azalan, toplam en fazla 50. Grup başlığında `open_counts`. `backlog` tek satır "Backlog: N iş". Son değişiklikler: Plane tarafında 10 açık iş + en fazla 10 kapanan ("kapandı"). Raf görünümü aynı blokları `project == <KOD>` ile süzer.

### 7.3 Env değişkenleri

**Eksik anahtar = boş değer (critic H5).** Yeni bir anahtarın satırı dosyada yoksa değeri boş sayılır ve boş değerin anlamı (aşağıdaki "Boş değer" sütunu) uygulanır. `./stack init` var olan `local/*.env` dosyalarına yeni anahtar **eklemez**. Böylece 0001 AC-2'nin "ikinci `init` sha256'yı değiştirmez" kuralı korunur ve 0001 altında kurulmuş makineler hiçbir şey eklemeden çalışır. Yeni anahtarlar `.env.example` ve `local.example/` içinde belgelenir.

| Değişken | Yer | Tür | Boş değer | Kural | Faz |
|---|---|---|---|---|---|
| `SELFHOST_DASHBOARD` | `local/bookstack.env` | M | `1` | `0`/`1`, başka değer exit 2 | 1 |
| `APP_THEME` | `local/bookstack.env` | M | dashboard teması | `^[a-z0-9-]{1,40}$`, ihlal exit 2 | 1 |
| `APP_URL` | BookStack env | T | – | 0001 §7.4, her zaman verilir | 1 |
| `SELFHOST_PENPOT_URL`, `SELFHOST_PLANE_URL` | BookStack env | T | durum `ok` değilse boş | diğer stack'in normalize config'inden 0001 §7.4 fonksiyonu (`PENPOT_PUBLIC_URI`, `WEB_URL`) | 1 |
| `SELFHOST_PENPOT_STATE`, `SELFHOST_PLANE_STATE` | BookStack env | T | – | `ok` (URL hesaplandı), `disabled` (`ENABLED_STACKS` dışında), `error` (diğer stack'in parser'ı, G-src, bir guard ya da compose config'i başarısız) | 1 |
| `PLANE_API_TOKEN` | `local/dashfeed.env` | M/S | `not_configured` | CEO girer. Biçim `^[A-Za-z0-9_-]{20,200}$` (T-0c sonrası daraltılır), ihlal exit 2. Yalnız tam modda `dashfeed`'e. Sahip, yönetici ya da CEO token'ı yasak | 2a |
| `PLANE_WORKSPACE_SLUG` | `local/dashfeed.env` | M | `not_configured` | `^[a-z0-9-]{1,48}$`, ihlal exit 2 | 2a |
| `DASHBOARD_PLANE` | `local/dashfeed.env` | M | `1` | `0`/`1` | 2a |
| `DASHBOARD_REFRESH_SECONDS` | `local/dashfeed.env` | M | `120` | 60-3600 | 2a |
| `DASHFEED_REQ_PER_MIN` | `local/dashfeed.env` | M | `30` | 5-30 | 2a |
| `DASHBOARD_CEO_LABEL` | `local/dashfeed.env` | M | `ceo-soru` | `^[A-Za-z0-9 _-]{1,40}$` | 2a |
| `DASHBOARD_TZ` | `local/dashfeed.env` | M | `up` anında host'un saat dilimi, okunamazsa `UTC` + uyarı | `^(UTC|[A-Za-z_]+(/[A-Za-z0-9_+-]+){1,2})$`, ihlal exit 2. Yalnız `dashfeed`'e verilir | 2a |
| `DASHBOARD_SPEC_DIRS` | `local/dashfeed.env` | M | bu repo'nun `docs/` | §6.7 | 2b |
| `DASHFEED_IMAGE` | `stacks/bookstack/versions.env` | P | – | tag + digest | 2a |

Kart URL kaynağı (critic M6): diğer stack'in **normalize config'i** kullanılır, böylece `local/<s>.override.yaml`'daki port değişiklikleri de kartlara yansır (0001 §7.4 "port = normalize config'teki giriş portu"). Diğer stack'in normalize config'i hangi sebeple olursa olsun üretilemezse durum `error` olur, kart U-27 gösterir, `up bookstack` uyarı basar ve exit 0 verir.

Geçersiz değer kodları 0001 §7.3 ile tutarlı: exit 2. `local/dashfeed.env`: `600`, 0001 parser'ı ile okunur. **Dosya yoksa** `up bookstack` dosyayı oluşturmaz, `--env-file` vermez ve `not_configured` ile çalışır. `./stack init` dosyayı boş değerlerle `600` oluşturur.

`dashfeed` container env'i yalnız şu anahtarları içerir: `PLANE_API_TOKEN` (tam modda), `PLANE_WORKSPACE_SLUG`, `SELFHOST_PLANE_URL`, `DASHBOARD_PLANE`, `DASHBOARD_REFRESH_SECONDS`, `DASHBOARD_CEO_LABEL`, `DASHFEED_REQ_PER_MIN`, `DASHBOARD_TZ`, ve Faz 2b'de `DASHBOARD_SPEC_SOURCES` (`stack`'in ürettiği kaynak adı listesi, yol değil).

**Plane kullanıcısı ve kalan risk (S-01, S2-05, KR-9):**
1. Ayrı bir kullanıcı (ör. `dashboard-okur`), öneri: çalışma alanı **Guest** + her projede **Commenter**. Birleşimin mümkün olduğunu ve token'ın yazma yeteneklerini T-0c yalnız atılabilir bir Plane'de ölçer. Yedek: çalışma alanı Member + her projede Commenter. Yedek gerekirse ölçülen yetenek listesini CEO Faz 2a imzasında açıkça kabul eder.
2. **Kalan risk:** API anahtarı sahibinin izinleriyle çalışır. Önerilen rollerle yazma yeteneği yorumla sınırlıdır (T-0c doğrular). Toplayıcı yalnız çalışma alanı rolünü kontrol eder: kullanıcıya bir projede proje Admin rolü verilirse bu kontrol yakalamaz. README bunu yasaklar.
3. Owner/Workspace Admin reddi, rol belirlenemezse fail closed (§6.5).
4. Token süresi en fazla 90 gün.
5. Her yeni projede kullanıcı Commenter olarak eklenir, aksi halde U-24.
6. Davetsiz kayıt geçici açılırsa işlemden sonra kapatılır, bu sürede 0001 AC-14'ün sign-up kontrolü kırmızıdır.
7. `docker` grubu `docker inspect` ile token'ı okuyabilir (0001 §8 kalan riskleriyle aynı sınıf).
8. Kullanıcıyı ve token'ı her zaman CEO oluşturur, atılabilir Plane'dekiler dahil.

### 7.4 Toplayıcının izinli Plane istekleri (Faz 2a)

| # | Yöntem ve yol | Parametreler | Durum |
|---|---|---|---|
| R-1 | `GET /api/v1/users/me/` | – | verified |
| R-2 | `GET /api/v1/workspaces/{slug}/members/` | `per_page=100`, `cursor`, (destekleniyorsa) `fields=id,role` | verified, T-0a2 |
| R-3 | `GET .../projects/` | `per_page=100`, `cursor`, `fields` | verified |
| R-4 | `GET .../projects/{uuid}/states/` | `per_page=100`, `cursor` | yol doğrulanmadı |
| R-5 | `GET .../projects/{uuid}/labels/` | `per_page=100`, `cursor` | yol doğrulanmadı |
| R-6 | `GET .../projects/{uuid}/work-items/` | `per_page=100`, `cursor`, `order_by=-updated_at`, `fields`, (R-4/R-5 yoksa) `expand=state,labels` | verified, v1.4.3 adı T-0c |

Başka yol ya da parametre yok. `{slug}` = `^[a-z0-9-]{1,48}$`, `{uuid}` = UUID regex'i. Kesin tablo T-0a2/T-0c sonrası `feed.py`'de, CB-14 aynı tabloyu kullanır.

## 8. Threat model and security

Sensitive area: Plane API token'ı, iş içeriği, Plane üye listesindeki kişisel veri (Faz 2a). Faz 1'de: BookStack yetkileri ve sunucu tarafında çalışan tema kodu.

Güven sınırları: (1) git ↔ BookStack/toplayıcı süreçleri, **dağıtım anı `up bookstack`'tir** (C-16). (2) `local/` ↔ container env. (3) toplayıcı ↔ Plane. (4) Plane/spec/etiket metni ↔ tarayıcı. (5) BookStack yetkileri ↔ Plane yetkileri. (6) snapshot ↔ tema.

| # | Tehdit | Önlem | Derece | Kriter |
|---|---|---|---|---|
| TD-1 | Kart URL'iyle XSS | şema kontrolü, escape | – | CB-4 |
| TD-2 | Tema = yetkili sunucu kodu | git + PR + CEO merge + appsec (M-1/M-2). Logical theme yok. İki aşamalı Blade/PHP taraması, `ACCESS_ALLOWLIST`, HTML yasakları. Override = kopya + tam satır include. Tema kilidi. Dağıtım yalnız `up` sırasında, kontrollerden sonra | – | CB-7, CB-8, CB-30 |
| TD-3 | Diğer stack secret'larının BookStack'e sızması | yalnız T değerleri ve durum değerleri, `env_file` yok | – | CB-2 |
| TD-4 | Yetkisiz içerik | ızgara değişmez, raf yalnız `$sortedVisibleShelfBooks`, `ACCESS_ALLOWLIST` | – | CB-3, CB-7, CB-10 |
| TD-13 | Tema dosyalarının web'den okunması | `public/` yok | – | CB-7 |
| TD-17 | Doğrulanmamış BookStack sürümünde eski override | tema kilidi (bozuk `UPSTREAM` dahil, fail closed) | – | CB-30 |
| TD-18 | `git pull` ile denetlenmemiş tema kodunun çalışması | dağıtım sınırı C-16 | – | CB-30 (g) |
| TD-5 | Token sızıntısı | yalnız `local/dashfeed.env` ve dashfeed env. Yedekte `local/` yok (0001 AC-11). G-tok. Maskeleme. Log politikası | – | CB-12, PB-4 |
| TD-6 | Kapsamsız token'la yazma | Guest + Commenter (T-0c, atılabilir Plane), Owner/Admin reddi, fail closed, `GET`, 90 gün. Kalan: yorum yazma, proje Admin boşluğu, yedek rolde geniş yetki (CEO kabulü, KR-9) | – | CB-14, CB-28 |
| TD-7 | Stored XSS | düz metin, escape, href kuralı, şemadan üretilen fixture | – | CB-21, CB-35 |
| TD-8 | SSRF | tema ağ isteği yapmaz, toplayıcı hedefi sabit, yönlendirme/proxy yok, cursor regex'i, etiket sözlük anahtarı, internal ağ | – | CB-11, CB-13, CB-14 |
| TD-9 | Köprüden başka ağlara erişim ya da köprüye başka servis | tek ağ, ağ doğrulaması, G-net (bütün projeler) | – | CB-13 |
| TD-10 | Spec mount'uyla gizli dosyaların açığa çıkması | `realpath`, yol regex'i, `docs`/`specs`, `.git` reddi, `ro`, `lstat` + `O_NOFOLLOW`, sınırlar | – | CB-17 |
| TD-11 | İki yetki modeli | Plane/spec blokları yalnız `settings-manage` (kabul: o yetkiye sahip her rol bütün dashboard verisini görür) | – | CB-24 |
| TD-12 | Plane kapalıyken sayfanın kilitlenmesi | sayfa açılışında ağ yok, heartbeat sağlığı | – | CB-22 |
| TD-14 | Canlı Plane testinde CEO verisinin kanıta girmesi | yalnız sayılar ve anahtar adları, yazma yoklamaları yalnız atılabilir Plane'de | – | CB-28 |
| TD-15 | Token'ın iç ağda şifresiz HTTP ile gitmesi | koşullar: G-net zorlanır, host ağında container yok, tek kullanıcılı loopback makinesi. Yeniden açma: ADR-0006 tetikleyicileri | **appsec r2: LOW, kabul** | CB-13 |
| TD-16 | Üye listesindeki kişisel verinin yazılması | bellekte atılır, şemada alan yok, log politikası | **appsec r2: LOW, kabul** | CB-14 |

CSP notu: CSP dış img/style host'larını engellemez, REQ-D6 Faz 1'de CB-7 (c)'nin kaynak taraması ve partial HTML yasaklarıyla zorlanır.

## 9. Changed behavior (acceptance criteria)

### 9.1 Faz 1 (12 kriter)

- [ ] CB-1 — (a) Temiz bir makinede `./stack init && ./stack up bookstack` sonrası admin girişiyle `GET http://127.0.0.1:8701/` 200, HTML `data-selfhost-dashboard` işaretini ve üç kartı içerir, `data-selfhost-plane` ve `data-selfhost-specs` yoktur. Tema klasöründe `selfhost/data.blade.php` yoktur. Elle adım yok. (b) Mevcut makine: 0001 altında kurulmuş, kullanılmış ve §9.2 marker verisi olan, `local/bookstack.env`'de yeni anahtar bulunmayan bir makinede `git pull && ./stack up bookstack` exit 0 verir, dashboard görünür, marker sayıları aynıdır, `git status --porcelain` boştur, `local/*.env` sha256'ları değişmez.
- [ ] CB-2 — Kartlar: (a) varsayılan portlarla Penpot `http://localhost:8702`, Plane `http://localhost:8703`, BookStack kartı `url('/books')`. (b) `PENPOT_PORT=8712` + `./stack up` → `http://localhost:8712`. (c) Yalnız `./stack up penpot` port değişikliğinden sonra BookStack kartı değişmez. BookStack container'ı (herhangi bir durumda) varsa ve container'daki `APP_THEME` `selfhost-dashboard` ise, `stack` container env'indeki değeri yeni değerle karşılaştırır, farklıysa "BookStack kartları eski: `./stack up bookstack`" basar. Container yoksa ya da tema kapalıysa uyarı yoktur. (d) `ENABLED_STACKS=bookstack` → `SELFHOST_PENPOT_STATE=disabled`, `SELFHOST_PLANE_STATE=disabled`, iki kart U-19, `href` yok. (e) `docker compose config`'te uygulama ve MariaDB'de `env_file` yok. Uygulama env'inde `PENPOT_SECRET_KEY`, `PLANE_SECRET_KEY`, `PLANE_DB_PASSWORD`, `PLANE_RABBITMQ_PASSWORD`, `PLANE_S3_SECRET_KEY`, `PLANE_API_TOKEN` yok. (f) `APP_URL` 0001 §7.4 değerine eşit. (g) `local/penpot.env`'de parser ihlali varken, ve ayrı bir çalıştırmada Penpot'un vendored dosyasında 1 baytlık değişiklik (G-src ihlali) varken, `./stack up bookstack` exit 0, uyarı basar, `SELFHOST_PENPOT_STATE=error`, Penpot kartı U-27. Her durumda `git status --porcelain` boş.
- [ ] CB-3 — Bizim blok `#home-default` ızgarasının üstündedir. Izgara, tema kapalıyken aynı kullanıcı için üretilenle aynı blokları aynı sırada içerir. Bir kullanıcı Arayüz tercihlerinden HomeRecentActivity'yi kaldırınca onun sayfasında blok yoktur, bizim blok üsttedir, başka kullanıcının düzeni değişmez. Temiz kurulumda bloklar kendi boş mesajlarını gösterir. B kullanıcısının görme yetkisi olmayan bir kitaptaki sayfa, A güncellese bile B'nin HTML'inde geçmez.
- [ ] CB-4 — Enjeksiyon yolu: `local/bookstack.override.yaml` ile bookstack servisinin `environment:`'ına `SELFHOST_PLANE_URL` verilir. (a) `javascript:alert(1)` → U-18, `href` yok. (b) `http://x/"><script>alert(1)</script>` → kartta `href` vardır ve değeri kaçışlanmıştır (`href="http://x/&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"`), HTML'de `<script>alert(1)` metni ham olarak geçmez, yeni bir öğe oluşmaz. Penpot ve Plane kartları `rel="noopener noreferrer"` taşır.
- [ ] CB-5 — `SELFHOST_DASHBOARD=0` + `up bookstack` → `/` ve raflar standart görünüm (işaret yok), `up`, `config` ve `status` çıktısında U-20a/U-20b uyarısı yok. `1` → geri gelir. `2` → exit 2 ve `local/bookstack.env:<satır>`. `APP_THEME=baska` → container'da `APP_THEME=baska`, dashboard yok, uyarı yok. Her durumda `git status --porcelain` boş.
- [ ] CB-6 — (a) Oturumsuz, misafir kapalı: `/` `/login`'e yönlenir. (b) Misafir açık: `/`'da kart ve Penpot/Plane adresi yok (`user()->isGuest()` doğru), etiketli rafta proje başlığı ve son kitaplar var. (c) `settings-manage` yetkisi olmayan giriş yapmış kullanıcı kartları ve BookStack bloklarını görür (`user()->isGuest()` yanlış). (d) (elle, mekanik alt kümede değil) Ana sayfa ayarı "Kitaplar" → kitap görünümü, "Varsayılan" → dashboard.
- [ ] CB-7 — Sertleştirme: (a) `docker inspect` tema mount'unu `RW=false` ve kaynağı `local/state/theme/selfhost-dashboard` gösterir, container içinden `touch` başarısız. Hiçbir kontrol BookStack init'inin "chown"/"Permissions could not be set" log satırlarına bakmaz. (b) `<script` sayısı tema kapalıyken standart sayfadakiyle aynı. (c) Kaynak taraması (tarayıcı garantisi değil): `src=` ve `url(` yalnız BookStack origin'ine gider, kart host'ları yalnız `href`'te. (d) Tema dosya kümesi `UPSTREAM`'deki `ALLOW` listesine eşit (meta dosyalar dahil), `functions.php` ve `public/` yok. (e) `selfhost/` partial'ları §6.1'deki iki aşamalı taramayı geçer ve §6.1'deki her kural için bir negatif fixture (en az: yasak değişken `$app`, `$__env->getContainer()`, `$_SERVER`, closure, `(...)`, atama, `?->` ile listede olmayan üye, `@json`, `@includeIf`, argümansız `env()`, listede olmayan `env('APP_KEY')`, `file_get_contents`, `<script`, `onclick=`, `javascript:`, `<form`, `<?`) tarayıcı tarafından yakalanır. (f) `/` ile başlayan dize sabitleri yalnız `'/books'`. (g) Container env'de `ALLOW_CONTENT_SCRIPTS` ve `APP_CONTENT_FILTERING` tanımlı değil ve `/config/www/.env`'de bu iki anahtarın yorum olmayan satırı yok. (h) `/theme/selfhost-dashboard/UPSTREAM`, `/theme/selfhost-dashboard/selfhost/home.blade.php` ve `/dashfeed/snapshot.json` oturumsuz ve oturumlu 404 döner, yanıt gövdesi dosya içeriğinden satır içermez.
- [ ] CB-8 — Upstream uyumu (quick, bump alt kümesinde): (1) `UPSTREAM` §6.1 dilbilgisine uyar ve `BOOKSTACK_IMAGE`, normalize config'teki BookStack image değerine tam dize eşittir. (2) Her `VIEW` satırı için orijinal dosya `docker run --rm --network none --entrypoint cat <pin> /app/www/resources/views/<yol>` ile okunur, sha256 eşittir, arm64 ve amd64 manifest'lerinde (`--platform`). (3) Override ile orijinal arasındaki ham bayt satır diff'inde silinmiş ya da değiştirilmiş satır yok, her eklenmiş satır tam satır `@include` kalıbına uyar. (4) Tema dosya kümesi `ALLOW`'a eşit. (5) `VIEW` satırı olmayan `UPSTREAM` geçerlidir, (2) ve (3) atlanır. (6) `selfhost/` dışındaki ve meta olmayan her `ALLOW` yolunun bir `VIEW` satırı, her `VIEW` satırının bir `ALLOW` satırı vardır. (7) Pinli image'da (`--network none`) etkin `opcache.validate_timestamps` = `1`, `opcache.revalidate_freq` ≤ 2, php-fpm havuz dosyalarında bunları ezen satır yok. Fixture'lar: bozuk `UPSTREAM` (bilinmeyen satır türü, iki `BOOKSTACK_IMAGE`, hiç `BOOKSTACK_IMAGE`), `VIEW`'siz `ALLOW` yolu, `validate_timestamps=0` içeren sahte havuz dosyası → her biri test başarısız.
- [ ] CB-9 — Tema partial'ındaki bir metin değişikliği `git pull` ile gelince, `./stack up bookstack` sonrası yeni metin en geç 10 s içinde görünür ve BookStack container ID'si değişmez. Kopyadaki dosyalar `0644`, dizinler `0755`. Tema değişmeden ikinci `up` hiçbir container'ı yeniden yaratmaz (0001 AC-1). Kontrol mac'te ve dind'de yapılır. 0001 §9.2 marker sayımı değişmez.
- [ ] CB-10 — `plane-project`=`WEB` etiketli raf: `data-selfhost-shelf` işareti, başlık "Proje: WEB", "Son güncellenen kitaplar" en fazla 5 kitabı `updated_at` azalan, eşitlikte `id` azalan sırada gösterir, görünen kitap yoksa U-28. B kullanıcısının ve misafirin göremediği bir kitap bu listede yoktur (S3-06). Standart raf içeriği etiketsiz raftaki gibi kalır. Kullanıcı `ShelvesShowTags` kenar bloğunu kaldırsa da başlık görünür. Tema kapalıyken (`SELFHOST_DASHBOARD=0` ya da kilit) `data-selfhost-shelf` yoktur. Etiket eklemek git değişikliği ya da `up` gerektirmez.
- [ ] CB-11 — Raf etiketleri (`id` sırasıyla, yalnız ad `plane-project`): (a) etiketsiz raf → `data-selfhost-shelf` yok. (b) yalnız `<b>x` → U-22, ham değer kaçışlanmış, standart raf, `data-selfhost-shelf` yok. (c) ` web ` → "Proje: WEB". (d) önce `API` sonra `WEB` → "Proje: API" + U-23. (e) önce `<b>x` sonra `WEB` → U-22 + U-23, başlık yok. (f) `wıb` (noktasız ı) → U-22. (g) Ad `Plane-Project` olan etiket aday değildir → U-21.
- [ ] CB-30 — Tema kilidi ve dağıtım sınırı: (a) `UPSTREAM`'deki `BOOKSTACK_IMAGE` BookStack pin'inden farklıyken `up bookstack` exit 0, container `APP_THEME` boş, `/` standart, `up`/`config`/`status`'ta U-20a, kopya değişmez. (b) `VIEW` satırı olmayan `UPSTREAM` → aynı, U-20b. (c) Bozuk `UPSTREAM` (bilinmeyen satır, iki `BOOKSTACK_IMAGE`, hiç `BOOKSTACK_IMAGE`) ve hiç `UPSTREAM` yok → her biri U-20a. (d) M-2 PR fixture'ı (bütün override'lar ve `VIEW`/`ALLOW` satırları silinmiş, `BOOKSTACK_IMAGE` yeni pin) CB-8'i geçer ve `/` yeni pin'in standart görünümünü gösterir. Kısmi silme fixture'ı (bir override silinmiş, diğeri duruyor) CB-8 (6)'yı kırar. (e) `APP_THEME=baska` + pin uyuşmazlığı → container `APP_THEME=baska`, uyarı yok. (f) `./stack config bookstack` her durumda `up`'ın vereceği `APP_THEME`'i ve aynı uyarıyı gösterir. (g) Tema metni değişikliği `git pull` ile gelir ama `up` çalıştırılmazsa HTML değişmez (60 s gözlem). `up` 5 ile durursa (AC-13 pin farkı) kopya değişmez. (h) Repo kararı ile çalışan container'ın `APP_THEME`'i farklıyken (ör. `SELFHOST_DASHBOARD=0` yapılıp `up` çalıştırılmadan) `status` iki değeri ve "`./stack up bookstack` gerekli" satırını gösterir. (i) Eşitlik geri gelince ve `up` çalışınca dashboard geri gelir.

### 9.2 Faz 2a (15 kriter)

Testler `tests/fake-plane/` ile çalışır: sabit yanıtlar, istek kaydı, komutla 401/429/kapalı/3xx/büyük yanıt/bozuk üye listesi modları, 60/dk sınırı ve `X-RateLimit-*` header'ları. Sahte sunucu pinli toplayıcı image'ında çalışır. Faz 2a kriterleri Faz 2a kapı turunda ayrıca incelenecek.

- [ ] CB-12 — Token yalıtımı: `init` `local/dashfeed.env`'yi `600` ve boş değerlerle oluşturur, ikinci `init` sha256'yı değiştirmez. `PLANE_API_TOKEN=test-token-1234567890ab` ile `up bookstack` sonrası bu dize yalnız `dashfeed` container env'indedir. BookStack env'inde, snapshot'ta, `docker compose -p selfhost-bookstack logs` ve `docker compose -p selfhost-plane logs` çıktılarında, HTML'de, `./stack config bookstack` ve `./stack status` çıktılarında yoktur. Compose'un `dashfeed`'e verdiği env anahtarları §7.3 listesinin alt kümesidir. G-tok: bir `local/bookstack.override.yaml` token'ı başka bir servisin env'ine koyarsa `up` ve `config` exit 3, container başlamaz. Token biçim kuralı ihlali exit 2. Bilinmeyen anahtar exit 2 ve `<dosya>:<satır>`. `git status --porcelain` boş.
- [ ] CB-13 — Ağ, G-net ve garanti: (a) `dashfeed` tek ağda (`selfhost-dashfeed`), `dashfeed-init` `network_mode: none`. (b) `dashfeed` içinden `1.1.1.1:443`, `mariadb:3306` ve Plane `api` servis adına bağlantı başarısız, `dashfeed` içinde dinleyen soket yok, host'ta yeni dinleyen port yok. (c) Ağ `Internal=true`, `Driver=bridge`, etiket `com.selfhost.managed=dashfeed`. Etiketsiz ya da internal olmayan aynı adlı ağ önceden varsa `up bookstack` ve `up plane` exit 2, hiçbir ağ silinmez. (d) G-net: `local/bookstack.override.yaml` uygulamayı ya da MariaDB'yi, `local/plane.override.yaml` `api`'yi, `local/penpot.override.yaml` herhangi bir Penpot servisini köprüye bağlarsa `up` ve `config` exit 3. (e) Ağı olmayan temiz makinede `ENABLED_STACKS=plane`, `SELFHOST_DASHBOARD=0` ile `./stack up plane` exit 0, ağ etiketiyle oluşur, 0001 §9.1 Plane health geçer. (f) Ağ yokken `config bookstack`, `status` ve `down plane` ağı oluşturmaz. (g) `status` `dashfeed` satırını ve snapshot `status`'unu gösterir, ağa elle bir container bağlanınca uyarı satırı basar, exit değişmez. Testler mac'te ve dind'de.
- [ ] CB-14 — HTTP disiplini ve rol (10 döngü): yalnız `GET`, her istek §7.4 tablosuna uyar, her listede `per_page=100`. 302 → izlenmez, `error`. 6 MB yanıt → `error`, okuma 5 MB'ta kesilir. Kötü cursor (`../x`, `http://evil`) kullanılmaz. Yanıttaki tam URL istenmez. Override ile `dashfeed`'e `HTTP_PROXY=http://evil:1` verilse de istekler sahte Plane'e gider. `Accept-Encoding` yok. Rol fixture'ları: Owner → U-8. Bozuk üye listesi, bilinmeyen rol sayısı ve eşleşmeyen `id` → her biri `token_role_unknown`, U-26, R-1/R-2 dışında istek yok, Plane bölümleri boş. Üye listesindeki e-posta ve isimler snapshot'ta ve loglarda yok. `feed.py` birim testleri aynı kuralları doğrular.
- [ ] CB-15 — İlk döngü ve sahiplik: temiz makinede `dashfeed-init` exit 0. Normalize config'te `dashfeed-init`: `cap_add` yok, `cap_drop` §6.5 listesi, `no-new-privileges`, `network_mode: none`, yalnız `/out` bağlı, komut §6.5'teki sabit dize. `/out` `65534:65534` `0755`, `snapshot.json` `0644`. İkinci `up` sonrası init yine exit 0. İlk döngü `status: ok`, BookStack dosyayı okur, bloklar dolar. Snapshot `tests/schema_check.py` ile şemaya karşı geçerli. BookStack'e `Type=volume`, hedef `/dashfeed`.
- [ ] CB-16 — Sizi bekleyenler (Plane): `ceo-soru` etiketli 3 iş (biri `completed`) ve etiketsiz 2 iş → tam 2 iş, `updated_at` azalan, `<KOD>-<sıra>` ve bağlantıyla. 25 etiketli açık iş → 20 + U-15. Yoksa U-14. `DASHBOARD_CEO_LABEL=karar` → `karar` etiketli işler. Etiketi olmayan iki projeli fixture → U-17 o iki kodu listeler. Label listesi alınamayan fixture → `projects_missing_label: null`, U-17 yok.
- [ ] CB-18 — Açık işler ve kesme: `started` 4, `unstarted` 11, `backlog` 22, `completed` 5 → gruplar `started`, `unstarted` iş satırlarıyla ve sayılarla, `backlog` tek satır "Backlog: 22 iş", `completed` yok. Öncelik ve zaman sırası §7.2. 60 açık iş → 50 satır, sayılar doğru. Yoksa "Açık iş yok.". Kesme: A projesinde 600 açık iş (görülen en eskisi `ceo-soru`), B projesinde 5 açık iş → B'nin 5 işi de snapshot'ta, A'nın `ceo-soru` işi "Sizi bekleyenler"de, `items_truncated: true`, U-16.
- [ ] CB-20 — Son değişiklikler: 10 açık iş ve son 7 günde güncellenmiş kapalı işler ("kapandı", en fazla 10). 8 gün önce güncellenmiş kapalı iş yok. Göreli zaman §4.5 kovalarına uyar (30 s → "az önce", 5 dk, 3 sa, 2 gün, gelecekte → "az önce"). `DASHBOARD_TZ=Europe/Istanbul` ile snapshot'taki `updated_at_local` değerleri UTC+03:00 uygulanmış hâldedir ve `title` niteliği bu dizeyi gösterir. Tema saat dilimi hesaplamaz.
- [ ] CB-21 — Güvenilmeyen metin: test `snapshot.schema.json`'dan Faz 2a alanlarındaki her string ve string[] alanına ve her nesne anahtarına `<img src=x onerror=alert(1)>` ve `"><svg onload=alert(1)>` koyan snapshot'lar üretir. Zaman alanlarına öznitelik kırma yükü (`2026-11-09T10:00:00Z" onmouseover="x`). Her yük kaçışlanmış görünür ya da hiç görünmez, etkin öğe oluşmaz, zaman alanları "zaman bilinmiyor" gösterir. Raf etiket değerine de aynı yük. Sahte Plane'in 500 gövdesindeki yük ne snapshot'ta ne HTML'de. Href fixture'ları: `javascript:alert(1)`, `http://evil.test/x`, `http://localhost:8703.evil.test/x`, `http://localhost:8703@evil.test/x`, `http://localhost:87031/` ve `SELFHOST_PLANE_URL` boşken geçerli URL → hiçbirinde `href` yok. 250 karakterlik ad 200'de kesilir.
- [ ] CB-22 — Durumlar. Her durumda `/` 200, kartlar ve ızgara görünür, `up bookstack` exit 0, `dashfeed` healthy ((e) hariç): (a) snapshot yok, heartbeat taze → U-2, healthy. (b) token ve slug boş → U-6. (c) başarılı bir döngüden sonra 401 → U-9 + son veri, `generated_at` 25 saat önceye çekilince veri gizlenir. (d) başarılı bir döngüden sonra Plane kapalı → U-11 + son veri. (e) `dashfeed` durdurulup `last_attempt_at` eskiye çekilince U-5. (f) `schema: 2` → U-4. (g) bozuk JSON ve 1,1 MB dosya → U-3. (h) yanlış slug (404) → U-12. (i) `schema: 2` + eski zaman → yalnız U-4. (j) Plane kapalıyken 20 `/` isteğinin `time_total` medyanı, Plane açıkkenkinden en fazla 50 ms fazla (kanıtta makine, runtime, sürüm). Ölçüm (kriter değil): 1 MB ile boş snapshot arasındaki fark.
- [ ] CB-23 — İstek bütçesi: sahte Plane 60/dk ve header'lar uygular. 30 proje × 500 işlik fixture'la iki etkin döngü boyunca 429 yok, snapshot en geç ikinci döngüde tamam, `refresh_seconds` §6.5 formülüne eşit, hiçbir dakikada istek sayısı etkin bütçeyi aşmaz. `X-RateLimit-Limit: 20` → etkin bütçe 10/dk. 31 proje → `projects_truncated`, U-16. Döngü ortasında 429 → `rate_limited`, önceki veri korunur, yarım döngü yayımlanmaz. `Remaining: 3`, `Reset` = şimdi + 30 s → yaklaşık 30 s bekler. `Reset` = şimdi + 1 saat → en fazla 60 s bekler. Geçmişte ya da sayı olmayan `Reset` yok sayılır. 10 dakikayı aşan döngü → `error` (`cycle_timeout`), yayımlanmaz.
- [ ] CB-24 — Yetki kapısı: `settings-manage` yetkisi olmayan kullanıcı ve misafir, ana sayfada ve `plane-project=WEB` rafında Plane bloğu, U-17, U-24 ya da durum mesajı görmez. HTML'de `WEB-` ile başlayan iş anahtarı ve `data-selfhost-plane` yok. Adı "Admin" olmayan ama `settings-manage` yetkili bir rol blokları görür.
- [ ] CB-25 — Proje dashboard'u: `WEB` ve `API` projeli fixture'da `WEB` rafında yalnız `WEB` işleri ve "Plane'de WEB projesini aç". HTML'de `API-` yok. Ana sayfa ikisini birlikte gösterir. `plane-project=NOPE` → U-24 + standart raf, sahte Plane'e `NOPE` içeren istek gitmez. Plane kapalıyken rafta U-11. (full) Yeni `NEW` projesi + raf etiketi → bir etkin döngü içinde dolar, git değişikliği ve `up` olmadan.
- [ ] CB-26 — Yaşam döngüsü ve ayarlar: (a) `SELFHOST_DASHBOARD=0` + `up` → `docker ps -a`'da `dashfeed` ve `dashfeed-init` yok, volume yerinde. (b) `APP_THEME=baska` → aynı. (c) `DASHBOARD_PLANE=0` → `plane_disabled`, Plane bölümleri boş, sahte Plane kaydı boş, token container env'inde yok. (d) `ENABLED_STACKS=bookstack` → (c) ile aynı. (e) Faz 2a commit'i revert edilip `up bookstack` → `--remove-orphans` (Faz 1 kodu) `dashfeed`'i kaldırır, volume ve ağ yerinde. (f) `DASHBOARD_REFRESH_SECONDS=30`, `PLANE_WORKSPACE_SLUG=Kötü Slug`, `DASHFEED_REQ_PER_MIN=100`, `DASHBOARD_TZ=Mars/Base` → her biri exit 2 ve `<dosya>:<satır>`. (g) Slug ve token boşken `ENABLED_STACKS=bookstack plane` ile `up` exit 0. (h) Normalize config'te `profiles:` yok. (i) Faz 1'le kurulmuş, `local/dashfeed.env` olmayan makinede `git pull && ./stack up bookstack` → exit 0, dosya oluşmaz, U-6. (j) Tema kilidi açıkken (CB-30 (a)) `dashfeed` çalışmaz.
- [ ] CB-28 — Plane uyumu (KR-9): (a) **quick, her PR:** `PLANE_COMPAT`'taki `PLANE_API_IMAGE`, normalize config'teki Plane `api` image değerine tam dize eşit, değilse test başarısız. (b) **merge öncesi, yeni pin'de, 0001 K-8 test ortamında atılabilir bir Plane'le:** gerçek yanıtların anahtar kümeleri `PLANE_COMPAT` ve sahte Plane fixture'larıyla aynı. Rol sayıları ve token yetenekleri (iş oluşturma/güncelleme/silme, yorum, proje oluşturma, projeye katılma) yalnız burada yoklanır. (c) **merge sonrası, CEO'nun canlı Plane'inde, yalnız okuma:** bir döngü `status: ok`, `token_role` `owner`/`admin` değil, bir örnek projede blok sayıları Plane web'dekiyle aynı. Kanıt yalnız sayılar ve anahtar adları. Canlı Plane'e `GET` dışında istek gitmez.
- [ ] CB-29 — Toplayıcı pin'i ve birim testleri: `config all` `dashfeed` ve `dashfeed-init` image'ını `DASHFEED_IMAGE` ile birebir gösterir (G-img). Çalışan kurulumda yalnız `DASHFEED_IMAGE` değişince `up bookstack` exit 5, container değişmez (0001 AC-13). `backup` + `up --i-have-a-backup` yeni toplayıcıyı başlatır. Önceki BookStack yedeğinin restore'u exit 5 vermez. Birim testleri pinli image'da `--network none` ile geçer, host `python3` yok.

### 9.3 Faz 2b (3 kriter)

- [ ] CB-17 — Spec klasörü güvenliği: `DASHBOARD_SPEC_DIRS`'te (a) repo kökü (`.git` içerir), (b) var olmayan yol, (c) son bileşeni `notes`, (d) göreli yol, (e) `docs`'a giden ama gerçek yolu repo kökü olan sembolik bağlantı, (f) `;` ya da `$` içeren yol → her biri `up` exit 2 ve yol adıyla mesaj. Kabul edilen mount'lar uzun sözdizimi ve `read_only: true`, `docker inspect`'te `RW=false`. Fixture'da `evil.md -> /proc/self/environ`, `.env`, 70 KB `big.md`, `sub/x.md` ve 600 dosya → snapshot'ta bunlardan iz yok, en fazla 500 dosya, `specs_skipped` doğru. Linux dind'de `0600` ve başka UID'li dosya atlanır ve sayılır.
- [ ] CB-34 — Spec blokları: `- Status: Draft` + iki `- **S-1: ...**` sorusu → "Taslak" + iki soru "Spec soruları" altında. `Status: Awaiting approval (Faz 1)` → "İmza bekliyor". `Status: Approved` + `Approved by / on (Faz 1): CEO 2026-11-10` + `(Faz 2):` boş → "İmza bekliyor (Faz 2)". `Approved`, imzalar dolu → listelenmez. `## Signature record (CEO only)` ve `## 16. Açık sorular` başlıkları tanınır. Spec yoksa U-14 (2b metni). `DASHBOARD_PLANE=0` ve `not_configured` durumlarında spec blokları dolu. Blok yalnız `settings-manage` yetkisi olanlara (`data-selfhost-specs`).
- [ ] CB-35 — Spec metni güvenilmez: spec başlığına, dosya adına, soru metnine ve imza parçası adına (`Approved by / on (<svg onload=alert()>):`) yük konunca her biri kaçışlanmış görünür, etkin öğe oluşmaz. `tests/schema_check.py` Faz 2b alanlarını da doğrular.

## 10. Preserved behavior (her biri Faz 1 ve Faz 2 biçimiyle)

- [ ] PB-1 — 0001 AC-7. Faz 1: bütün komutlardan sonra `git status --porcelain` boş, `local/state/theme/` git'te değil, iki makine senaryosunda A'daki Penpot portu B'nin kartlarını değiştirmez. Faz 2a/2b: ek olarak 10 toplayıcı döngüsü sonrası da boş, A'daki Plane verisi B'yi etkilemez.
- [ ] PB-2 — 0001 AC-3. Faz 1: yalnız `127.0.0.1:8701-8703` dinlenir. Faz 2a: Plane `proxy`'nin host yayını değişmez.
- [ ] PB-3 — 0001 AC-5. Faz 1: image kümesi değişmez. Faz 2a: `dashfeed` ve `dashfeed-init` tag + digest, `versions.env` ile birebir.
- [ ] PB-4 — 0001 AC-11/AC-12. Faz 1: dashboard açıkken `backup bookstack` AC-11 dosya kümesini üretir, `shasum -c` geçer, tar'da tema dosyası yok (en fazla boş mount noktası klasörü), `local/state/theme/` yedekte yok, restore round-trip geçer. Faz 2a: ek olarak token yedekte yok, tar'da snapshot yok.
- [ ] PB-5 — 0001 AC-10. Her iki faz: `down` + `up` sonrası marker veri yerinde, `grep -nE 'down +-v|volume +(rm|prune)|system +prune|network +rm' stack lib/*.sh` boş.
- [ ] PB-6 — 0001 §9.1 ve AC-8. Faz 1: BookStack `/status` 200 ve `true`'lar. Penpot ve Plane için ikinci `up` sonrası container kümesi ve ID'leri ilk `up`'takiyle aynı (`--remove-orphans` yalnız BookStack'te). Faz 2a: Plane health proxy'ye ağ eklendikten sonra da geçer, vendored dosyalar değişmez.
- [ ] PB-7 — 0001 AC-13 ve geri dönüş. Faz 1: app pin'i değişince `up` exit 5 ve `--i-have-a-backup` davranışı aynen. **0002 öncesine dönüş sırası (merkezi revert ya da `git switch --detach`)**: (1) `local/bookstack.env`'den `SELFHOST_DASHBOARD` ve `APP_THEME` satırları silinir (makinenin kendi teması da kapanır, README), (2) Faz 2a uygulanmışsa `local/dashfeed.env`, `local/dashfeed.env.off` olarak yeniden adlandırılır, (3) revert commit'i `git pull` ile alınır (ya da `git switch --detach <0002-öncesi>`), (4) `./stack up` → exit 0 (eski parser reddetmez). Faz 2a: ek olarak (4)'teki `up bookstack` `--remove-orphans` ile `dashfeed`'i kaldırır. Faz 1 de geri alınıyorsa ve `dashfeed` container'ı kaldıysa: `docker ps -aq --filter label=com.docker.compose.project=selfhost-bookstack --filter label=com.docker.compose.service=dashfeed` ile bulunup `docker rm -f` ile kaldırılır (volume'suz, T-6'da denenir).
- [ ] PB-8 — 0001 AC-15. Faz 1: `status`'ta mevcut satırlar değişmez, tema kararı satırı eklenir (C-10), kilit açıksa U-20a/U-20b. Faz 2a: ek olarak `dashfeed` satırı ve köprü uyarısı, `PLANE_API_TOKEN` maskelenir.

## 11. Test and evidence (Faz 1)

| Criterion | Test | Layer | Profile |
|---|---|---|---|
| CB-1 | (a) temiz kurulum, (b) 0001 makinesi + marker veri + `git pull && up` | e2e | quick / full |
| CB-2 | yedi alt durum, `config`, `exec env`, parser ve G-src ihlali | e2e | quick |
| CB-3 | açık/kapalı ızgara, kullanıcı tercihi, iki kullanıcı | e2e | full |
| CB-4 | override ile iki değer, `rel` | e2e | quick |
| CB-5 | dört çalıştırma + uyarı yokluğu | integration | quick |
| CB-6 | (a)-(c) otomatik, (d) elle | e2e + elle | full |
| CB-7 | `inspect`, `touch`, `<script` sayısı, host taraması, dosya kümesi, iki aşamalı tarayıcı + negatif fixture'lar, env + `.env`, 404 + gövde | integration + statik | quick |
| CB-8 | dilbilgisi, `cat` (arm64 + amd64), sha256, ham bayt diff, `VIEW`↔`ALLOW`, opcache ayarı, bozuk fixture'lar | statik | quick |
| CB-9 | `git pull` + `up`, 10 s yoklama, container ID, modlar, mac + dind | e2e | full |
| CB-10, CB-11 | BookStack API ile raf/etiket/kitap fixture'ları, iki kullanıcı, misafir | e2e | quick |
| CB-30 | dokuz alt durum, M-2 ve kısmi silme fixture'ları | integration | quick |
| M-1 (a) | `tests/upgrade_diff_check.sh`, base dalından | statik | quick (bump PR'larında) |
| CB-12 | token `grep`'i (iki projenin logları dahil), G-tok override, parser | integration | quick |
| CB-13 | `inspect`, bağlantı denemeleri, sahte ağ, üç override, temiz makine, `config/status/down` | integration | full |
| CB-14 | sahte Plane modları, istek kaydı, rol fixture'ları, `unittest` | integration + unit | quick |
| CB-15 | temiz volume, config, `stat`, ikinci `up`, `schema_check.py` | e2e | quick |
| CB-16, CB-18, CB-20 | fixture'lar, HTML | integration | quick |
| CB-21 | şemadan üretilen fixture'lar, href fixture'ları | integration | quick |
| CB-22 | on alt durum, `restart dashfeed` ile hızlandırma | e2e | full |
| CB-23 | 30/31 proje, header modları, deadline | integration | full |
| CB-24, CB-25 | rol ve proje fixture'ları | e2e | full |
| CB-26 | alt durumlar, yükseltme yolu | e2e | full |
| CB-28 | (a) statik quick, (b) test ortamı atılabilir Plane, (c) canlı salt okuma | statik / e2e | quick / full / elle |
| CB-29 | pin değişimi, exit 5, bayraklı up, restore, birim testleri | integration | quick |
| CB-17, CB-34, CB-35 | yol durumları, spec fixture klasörü, yükler | integration | full / quick / quick |
| PB-1..PB-8 | Faz 1 biçimi T-5'te, Faz 2a/2b biçimi T-12b ve T-18'de | e2e | full |

Ortam: mac'te CEO'nun Docker runtime'ı, Linux Engine davranışı pinli dind'de (§6.3). Elle kontrol: tarayıcı konsolunda CSP ihlali yok. Ekran görüntüsü repo'ya girmez.

## 12. Deployment and rollback

```mermaid
%% Soru: bir faz makineye nasıl gelir ve nasıl geri alınır?
flowchart LR
  PR["faz PR'ı"] --> SB["appsec + §11"]
  SB --> M{"CEO merge onayı"}
  M --> U["makine: git pull && ./stack up"]
  U --> H{"sayfa ve status OK?"}
  H -- evet --> OK["dashboard açık"]
  H -- "hayır, acil" --> K["SELFHOST_DASHBOARD=0 + up"]
  H -- "hayır, kalıcı" --> R["PB-7 sırası + revert"]
```
Açıklama: her faz ayrı PR ve ayrı CEO onayıyla gelir. Tema makinede yalnız `up` ile değişir. Sorun çıkarsa makinede kapatılır ya da PB-7'deki sırayla geri alınır. Veri değişmez. Metin karşılığı:
1. Faz PR'ı → appsec incelemesi (M-1/M-2 ya da tam stop-B) ve §11.
2. CEO merge onayı → her makinede `git pull && ./stack up`. Hiçbir ajan bunu CEO yerine yapmaz.
3. Faz 2a'nın ilk `up`'ı Plane proxy'sini bir kez yeniden yaratır. Faz 2a'da CEO Plane kullanıcısını ve token'ı kendisi oluşturur.

**Mekanik taşınamayan BookStack güvenlik yaması (KR-8, M-2):** PR bütün override dosyalarını ve onların `VIEW`/`ALLOW` satırlarını siler, `BOOKSTACK_IMAGE`'ı yeni pin'e günceller. BookStack yamalı upstream view'u sunar, dashboard merkezi olarak kaybolur (U-20b), CB-8 yeşil kalır, makinelerde elle adım yoktur. Port PR'ı dosyaları geri ekler. Kısmi silme yasaktır.

**Geri alma (veri riski yok):** makinede `SELFHOST_DASHBOARD=0` + `up bookstack` (yalnız Plane: `DASHBOARD_PLANE=0`). Merkezi revert ve 0002 öncesine dönüş PB-7'deki dört adımlık sırayla. Token ifşası: Plane'de iptal, yeni token, `up bookstack`.

## 13. Task list (atomic)

Süreler bilgi amaçlı tahmindir (KR-7).

| ID | Task | Kriter | Owning unit | Dependency | Tahmin |
|---|---|---|---|---|---|
| **Faz 1 imza öncesi** | | | | | |
| T-0a, T-0b | Doğrulama ve ölçüm | – | scout, devops-sre | – | **yapıldı** |
| T-A7 | ADR-0007 r3 | – | software-architect | – | **yapıldı** (appsec S3-04'e göre) |
| T-A7b | ADR-0007'nin revizyon 5 ile senkronu: S3-01 iki aşamalı tarama ve direktif/değişken allowlist'leri, M-1/M-2 son metni, dağıtım sınırı (C-16), tema kilidi girdi-çıktı tablosu (K3-1) ve `UPSTREAM` dilbilgisi, opcache koruması (K3-2), etiket kuralının sadeleşmesi (§6.6), `ALLOW`/`VIEW` eşlemesi ve ya hep ya hiç silme | CB-7, 8, 30 | software-architect (board K3'ü yeniden kontrol eder) | – | 0,5 sa |
| **Faz 1, T-5'ten önce** | | | | | |
| T-0d | dind lisans ve bakım doğrulaması (Moby, Apache-2.0), `tests/versions.env`'de tag + digest pini (K3-4) | CB-9 | scout + devops-sre | – | 0,25 sa |
| **Faz 1** | | | | | |
| T-1 | `stacks/bookstack/compose.yaml`: açık `environment:` (`APP_URL`, kart URL ve durum env'leri), tema mount'u `local/state/theme/selfhost-dashboard` ro. `.env.example`, `local.example/` | CB-2, 5, 7 | devops-sre | 0001 T-2, T-A7b | 0,5 sa |
| T-2 | `stack` + `lib/`: kart URL ve durumları (normalize config, U-27 yolu), karşılaştırmalı uyarı (CB-2 (c)), parser'a yeni anahtarlar (`init` eklemez), tema kilidi tablosu ve `UPSTREAM` ayrıştırıcısı, `config`/`status` gösterimi, dağıtım sınırı ve yerinde kopya (modlar), `up bookstack`'te `--remove-orphans` | CB-1, 2, 5, 9, 30, PB-6, PB-7 | polyglot-engineer | 0001 T-5, T-1 | 1,5 sa |
| T-3 | Tema: `home/default` kopya + include, `selfhost/home` ve `cards` partial'ları, URL ve durum mantığı, `UPSTREAM`, `PHP_ALLOWLIST`, `ACCESS_ALLOWLIST`, `README`. D-23'ü pinli image'da doğrular | CB-1, 3, 4, 6, 7, 8 | polyglot-engineer | T-A7b | 1,5 sa |
| T-4 | Tema: `shelves/show` kopya + include, `selfhost/shelf` (§6.6 kuralı, U-21..U-23, U-28, son kitaplar, `data-selfhost-shelf`) | CB-10, 11 | polyglot-engineer | T-3 | 0,75 sa |
| T-5 | `tests/bookstack-dashboard.sh` Faz 1, `tests/blade_scan/` (iki aşamalı tarayıcı + negatif fixture'lar), `tests/upgrade_diff_check.sh` (M-1 (a)), CB-8 arm64 + amd64 ve opcache kontrolü, PB'lerin Faz 1 biçimi, dind | Faz 1 + PB | qa-engineer | T-0d, T-1..T-4 | 1,75 sa |
| T-6 | README Faz 1: kapatma, ana sayfa ayarı ve kullanıcı blokları, raf etiketi (küçük harf `plane-project`, ilk etiket kuralı), tema kilidi uyarıları, "tema değişikliği `up` ile gelir", yükseltme prosedürü (M-1/M-2, KR-8), PB-7 dönüş sırası ve `docker rm -f` adımı (denenir), `APP_THEME` satırını silmenin makinenin kendi temasını da kapattığı notu, `restart` notu | CB-5, 6, 8, 30, PB-7 | tech-comms | T-4 | 0,3 sa |
| T-7 | Faz 1 teslim zinciri: appsec stop-B (TD-1..TD-4, TD-13, TD-17, TD-18) → internal-auditor → quality-office | Faz 1 | appsec, internal-auditor, quality-office | T-5, T-6 | 0,75 sa |
| – | Faz 1 düzeltme payı | | ilgili birim | | 1,75 sa |
| **Faz 2a imza öncesi** | | | | | |
| T-0a2 | T-0a'nın kalanı + K2-4 + K3-5: D-20 (pin 3.14.<patch>, advisory listesi, CVE-2026-116566'nın düzeltildiği sürüm, `apk info -v` + OSV/secdb, lisanslar), 3.15 yayın durumu ve `alpine3.24` varyantı, state/label yolları, `fields=id,role` ya da kendi rolü uç noktası, `/users/me/` `id` eşleşmesi | CB-14, 29 | scout (+ devops-sre `apk info`) | – | 0,75 sa |
| T-0c | KR-9'a göre atılabilir Plane'de (0001 K-8 test ortamı, CEO'nun oluşturduğu kullanıcı ve token'larla): rol sayıları, Guest + Commenter birleşimi, yazma yetenek yoklamaları, D-12r, D-13 (v1.4.3 adları, URL kalıpları), D-15 (dind / Linux CI), D-16, D-16b, D-21, D-22 (ham API), ağ helper'ı 3.14 pin'iyle, `selfhost-plane` loglarında token yok. Canlı Plane'e yalnız CB-28 (c) | CB-13, 14, 23, 28 | devops-sre | 0001 T-4 | 1,25 sa |
| T-A6 | ADR-0006 güncellemesi (K2-8, K2-5): T-0c sonuçları, 0001 r3 numaraları, Host header ölçüm + risk modeli, regex = PB-5, TD-15 derecesi, G-net bütün projeler, CB-27 artık CB-13 (e)-(g) | CB-13 | software-architect (board inceler) | T-0c | 0,5 sa |
| **Faz 2a** | | | | | |
| T-8 | `feed.py` (Plane kısmı) + `unittest` + `snapshot.schema.json` + `PLANE_COMPAT`: istemci kuralları, rol ve fail closed, PII atma, filtreleme, bütçe ve header'lar, kesme ve taban, heartbeat, atomik yazma, durum alanları, `*_local` zaman dizeleri, log | CB-12..16, 18, 20..23, 26, 29 | polyglot-engineer | Faz 1, T-0a2, T-0c | 3 sa |
| ⏸ | Ara durum raporu (bilgi, durdurmaz) | | delivery-manager | T-8 | – |
| T-9 | Compose: `dashfeed`, `dashfeed-init`, snapshot volume, `/dashfeed` ro, `DASHFEED_IMAGE`, healthcheck. Plane overlay: alias + `default` | CB-13, 15, 26, 29, PB-2, 3, 6 | devops-sre | T-A6 | 1,25 sa |
| T-10 | `stack` + `lib/`: ağ garantisi (C-6 sırası), G-net, G-tok, `local/dashfeed.env` (init, parser, maskeleme, yoksa davranış), `DASHBOARD_TZ` (host zone okuma), `--scale`, `status`, health | CB-12, 13, 26, 29 | polyglot-engineer | T-9 | 1 sa |
| T-11 | Tema: `selfhost/data.blade.php` (K3-3, U-2/U-3 ayrımı, sınırlı okuma), A-5'in `ACCESS_ALLOWLIST`'e eklenmesi, `'/dashfeed/snapshot.json'` sabitinin izinli kümeye eklenmesi, Faz 2a partial'ları, snapshot doğrulaması, href kuralı, durum öncelikleri, zaman kovaları, yetki kapısı, raf süzmesi | CB-16, 18, 20..22, 24, 25 | polyglot-engineer | T-8 | 1,25 sa |
| T-12a | `tests/fake-plane/`, `tests/schema_check.py`, şemadan fixture üreteci + CB-12..16, 21, 23 | Faz 2a ilk yarı | qa-engineer | T-8..T-10 | 1,5 sa |
| T-12b | CB-18, 20, 22, 24..26, 28 (a, b), 29 + PB'lerin Faz 2a biçimi (mac + dind) | Faz 2a ikinci yarı + PB | qa-engineer | T-11, T-12a | 1,5 sa |
| T-13 | README Faz 2a: kullanıcı ve roller (proje Admin yasağı), 90 gün, kayıt aç/kapat, projelere kullanıcı ve etiket, `API_KEY_RATE_LIMIT`, `stack`'siz compose uyarısı, `docker` grubu, `DASHBOARD_TZ`, faz geri alma sırası | CB-12, 16, TD-6 | tech-comms | T-11 | 0,5 sa |
| T-14 | Faz 2a teslim zinciri: appsec stop-B (TD-5..TD-9, TD-11, TD-12, TD-14..TD-16) → internal-auditor → quality-office. CB-28 (c) canlı smoke merge sonrası CEO'yla | Faz 2a | appsec, internal-auditor, quality-office | T-12b, T-13 | 1 sa |
| – | Faz 2a düzeltme payı | | ilgili birim | | 2,75 sa |
| **Faz 2b** | | | | | |
| T-15 | `feed.py` spec toplama ve ayrıştırma + `unittest` | CB-17, 34, 35 | polyglot-engineer | Faz 2a | 0,75 sa |
| T-16 | `stack`: `DASHBOARD_SPEC_DIRS` doğrulaması (realpath, regex, G-iso), uzun sözdizimli mount üretimi | CB-17 | polyglot-engineer | T-15 | 0,5 sa |
| T-17 | Tema: spec blokları | CB-34, 35 | polyglot-engineer | T-15 | 0,5 sa |
| T-18 | Faz 2b testleri + PB'lerin Faz 2b biçimi | Faz 2b | qa-engineer | T-15..T-17 | 0,75 sa |
| T-19 | README Faz 2b: spec klasörleri | CB-17 | tech-comms | T-17 | 0,1 sa |
| T-20 | Faz 2b teslim zinciri: appsec (TD-7, TD-10) → internal-auditor → quality-office | Faz 2b | appsec, internal-auditor, quality-office | T-18, T-19 | 0,5 sa |
| – | Faz 2b düzeltme payı | | ilgili birim | | 0,8 sa |
| T-ADR | ADR'lerin `docs/adr/`'ye taşınması | – | CEO/delivery-manager karar verir, software-architect taşır | – | 0,1 sa |

Toplam tahmin (bilgi): Faz 1 imza öncesi 0,5 sa, Faz 1 9,5 sa (T-0d dahil), Faz 2a 13,75 sa, Faz 2b 3,9 sa.

Dosya sahipliği: `stacks/bookstack/theme/`, `stacks/bookstack/dashfeed/`, `stack`, `lib/` → polyglot-engineer. `stacks/*/compose.yaml`, `versions.env`, `.env.example`, `local.example/` → devops-sre. `tests/` → qa-engineer. `README.md` → tech-comms. ADR'ler → software-architect.

## 14. Out of scope ve "sonra" listesi

Kapsam dışı (KR-3): dashboard'dan Plane'e yazma, sağlık göstergesi, ayrı dashboard uygulaması, kendi view block'umuz, ana sayfa ve raf dışındaki görünümler, markalama, tarayıcı JS'i, `?project=`, rafta proje bazında spec listesi, logical theme, birden fazla Plane çalışma alanı, LAN/uzaktan erişim.

"Sonra" adayları: bugün/bu hafta odak, takılmış işler, spec/pipeline durumu, stack sağlığı, Penpot son dosyalar, dashboard'u BookStack bloğu yapmak (logical theme ister), büyük/küçük harf duyarsız raf etiketi adı (S3-01'in izin verdiği bir yolla).

## 15. Gate findings and self-critique

### 15.1 Tur 3 iz tablosu

| Bulgu | Nerede |
|---|---|
| K3-1 / H1 kilit yalnız dashboard teması için | §6.1 girdi-çıktı tablosu, REQ-D5, REQ-D20, CB-5, CB-30 (e) |
| K3-2 opcache koruması | §6.1, CB-8 (7), bump alt kümesi |
| K3-3 Faz 2a parçalarının Faz 1'den çıkarılması | §6.1 (A-5 yok), §7.1, CB-1 (a), CB-7 (f), C-13 kaldırıldı, `DASHBOARD_TZ` |
| K3-4 dind | §6.3, T-0d, başlık |
| K3-5 3.15 alternatifi | §6.3 |
| A3-4 liste disiplini, tarayıcı semantiği | §6.1 |
| A3-7 partial'da TZ | §4.5, §6.5, §7.2, CB-20 |
| Board engellemeyen: U-20 ayrı sebep, `config` = `up`, `--remove-orphans` yalnız BookStack, dünya-okunurluk | U-20a/U-20b, CB-30 (f), C-3 (b), PB-6, C-16 kopya modları |
| H2 + S3-05 derleyici token kümesi | §6.1 aşama 2, CB-7 (e) |
| H3 misafir tespiti | A-6, D-23, CB-6 (b)(c) |
| H4 durum env'leri | §7.3, CB-2 (d)(g) |
| H5 eksik anahtar, `init`, mevcut makine | §7.3, CB-1 (b) |
| H6 `VIEW`↔`ALLOW`, ya hep ya hiç | §6.1, CB-8 (6), CB-30 (d) |
| M1 merkezi revert sırası | PB-7, §12 |
| M2 `--remove-orphans` kapsamı | C-3 (b), PB-6 |
| M3 raf işareti | §4.3, CB-10, CB-11 |
| M4 diff > iki satır, script sahibi, elle madde | §6.1 M-1, T-5, CB-6 (d) |
| M5 `UPSTREAM` dilbilgisi, `status` | §6.1, C-10, CB-8 (1), CB-30 (c)(h) |
| M6 kart URL kaynağı | §7.3, CB-2 (g) |
| L1 enjeksiyon yolu | CB-4 |
| L2 ham değer, ASCII | §6.6, CB-11 (f) |
| L3 uyarı koşulu | CB-2 (c) |
| L4 meta dosyalar | §6.1, CB-7 (d) |
| L5 `docker rm -f` | PB-7, T-6 |
| L6 `data` partial'ı | K3-3 |
| L7 `APP_THEME` notu | PB-7, T-6 |
| L8 S2-04 | S3-02 son metniyle değiştirildi (§6.1) |
| L9 ikincil sıralama | A-3, CB-10 |
| S3-01 kurallar | §6.1 aşama 1, CB-7 (e) |
| S3-02 G-4 son metni | §6.1, C-9 |
| S3-03 dağıtım sınırı | C-16, §6.1, §6.8, CB-9, CB-30 (g) |
| S3-04 ADR senkronu | T-A7b |
| S3-06 CB-10 görünürlük | CB-10 |
| S3-07 ya hep ya hiç, bozuk `UPSTREAM` | §6.1, CB-30 (c)(d) |

**Appsec tur 1 ve tur 2 iz tablosu (I-2):**

| Bulgu | Nerede |
|---|---|
| S-01 token rolü ve kalan risk | §6.5 rol kontrolü, §7.3 Plane kullanıcısı 1-3, TD-6, CB-14 |
| S-02 token ayrı dosyada | §7.3, C-4, TD-5, CB-12, PB-4 |
| S-03 escape, güven sınırı 6 | §7.2 tema tarafı doğrulama, CB-21 |
| S-04 yetki kapısı | REQ-D14, TD-11, CB-24 |
| S-05 spec klasörü kuralı | §6.7, CB-17 |
| S-06 logical theme yasağı | §6.1, D-2, D-17 |
| S-07 ağ doğrulaması, alias, dinleme yok | §6.4, CB-13 |
| S-08 HTTP istemci kuralları | §6.5, CB-14 |
| S-09 env allowlist, web yolları | §7.3, CB-7 (h), CB-12 |
| S-10 digest pin | §6.3, CB-29 |
| S-11 log, kayıt aç/kapat, docker grubu | §6.5, §7.3 Plane kullanıcısı 6-7 |
| S2-01 fail closed | §6.5, REQ-D21, U-26, CB-14 |
| S2-02 PHP kuralları | §6.1 (S3-01 ile genişledi), CB-7 (e) |
| S2-03 bayat görünüm | KR-8, C-14, CB-30 |
| S2-04 bump incelemesi | §6.1 M-1/M-2 (S3-02 son metni) |
| S2-05 KR-9, proje Admin boşluğu | §7.3, TD-6, CB-28 |
| S2-06 şemadan üretilen XSS fixture'ı | CB-21, CB-35 |
| S2-07 href kuralı | §7.2, CB-21 |
| S2-08 realpath, regex, uzun sözdizimi | §6.7, CB-17 |
| S2-09 Reset beklemesi, süreler, sınırlı okuma | §6.5, CB-14, CB-23 |
| S2-10 Plane loglarında token | CB-12, T-0c |
| S2-11 üye çağrısı, temizleme, 24 saat | §6.5, §7.2, CB-14, CB-22 (c), CB-26 (c) |
| S2-12 `dashfeed-init` | §6.5, CB-15 |
| S2-13 G-tok | C-15, CB-12 |
| TD-15, TD-16 derecesi | §8 |
| I-1 eski atıflar | T-A7b, T-A6 |
| I-3 anahtar adları | §7.3 |
| I-4 sınırlı okuma | §6.1, §7.2 |
| I-5 dağıtım varsayımı | Assumptions |

Board tur 2 (K2-1..K2-8) ve spec-critic tur 2 (#1..#40) bulgularının yerleri: K2-1 §6.1 ve CB-7 (e); K2-2 T-A7 (yapıldı) ve T-A7b; K2-3 §5; K2-4 §6.3 ve T-0a2; K2-5 C-12 ve CB-13 (d); K2-6 §7.2 ve CB-15; K2-7 §6.3; K2-8 T-A6. Critic tur 2 maddeleri §4.5 (zaman, U-durumları), §6.5 (heartbeat, kesme, bütçe), §6.7 (ayrıştırma), §7.2 (durum tablosu), §7.3 (boş değer), §10 (PB faz biçimleri), CB-2, CB-7, CB-12, CB-18, CB-21..CB-28'e işlendi.

### 15.2 Kendi incelemem

- Dağıtım sınırıyla `git pull` artık sayfayı değiştirmiyor. Bu, CEO'nun "tema değişikliğini görmek için `up`" alışkanlığına uyuyor (0001'de de dağıtım `git pull && ./stack up`). README bunu yazar.
- Yerinde eşitleme atomik değildir: dosyalar tek tek değişir ve bir istek iki dosyanın farklı sürümlerini görebilir (milisaniyeler). Override dosyaları yalnız bump'ta, partial'lar yalnız tema PR'ında değişir, risk düşük ve kabul edilebilir.
- Etiket kuralı sadeleşti (§6.6, §15.3). Raf kullanıcısının gözünden fark: ad büyük harfle yazılırsa tanınmaz ve ilk etiket geçersizse sonraki geçerli etikete bakılmaz. Her iki durumda da sayfa bir mesaj gösterir.

### 15.3 Tam işlenemeyen ya da kapsamı daraltılan bulgular

- **Etiket kuralı ile S3-01'in çatışması (tasarım değişikliği, appsec'e bilgi):** S3-01 atamayı, closure'ı ve `@php`'yi yasaklıyor. Revizyon 4'teki "büyük/küçük harf duyarsız ad" ve "ilk **geçerli** değer" kuralları Blade'de ancak bir bayrak değişkeni ya da callback ile yazılabiliyordu. Kural, yalnız sabit argümanlı koleksiyon metodlarıyla yazılabilecek hale getirildi: ad tam `plane-project`, karar ilk adaya göre (§6.6, CB-11 (e)(g) değişti). Bu, kullanıcıya görünen küçük bir davranış değişikliği, front-end/UX alanında BA kararı olarak alındı, CEO sorusu değil. Appsec bir sonraki turda kuralın S3-01'e uyduğunu teyit etmeli.
- **D-23 doğrulanmadı:** `user()->isGuest()`, `collect()`, dizi biçimli `sortBy` ve PHP 8.5'te `strtoupper`'ın ASCII davranışı genel bilgiye dayanıyor. T-3 pinli image'da doğrular, CB-6/CB-10/CB-11 yakalar. Biri yoksa kural gevşetilmez, appsec'e döner.
- **Faz 2a/2b metinleri** bu revizyonda yalnız K3-3/A3-7 değişiklikleriyle (`DASHBOARD_TZ`, `*_local`, `data` partial'ının T-11'e taşınması, CB-26 (j)) güncellendi. Faz 2a'nın kendi kapı turu bu metni tam inceler.
- **0001 KR-7 hizalaması** (critic #26, önceki tur): 0001'in başlığı ve §12.1'i hâlâ durdurma kuralları içeriyor. 0001 sahibine yönlendirilmeli.
- **Opcache etiket kararı:** K3-2'nin tercihli yolu (statik kontrol) seçildi. Container etiketi tutulmadı.

## 16. CEO kararları

Kararlar imza değildir.

| # | Karar (2026-11-09) | Spec'teki etkisi |
|---|---|---|
| KR-1 | Dashboard merkezi araçtır, her makine kapatabilir, makinenin teması kazanır | §1, C-1, §6.1 tablo |
| KR-2 | CEO soruları: Plane `ceo-soru` (2a) ve spec `S-n` (2b) | §6.7 |
| KR-3 | Fazlı teslim, her faz ayrı imza, "sonra" listesi kapsam dışı (KR-10 ile üç faz, KR-7 ile saatler tahmin) | başlık, §9, §13 |
| KR-4 | Son 7 günde kapananlar gösterilir | §6.5, CB-20 |
| KR-5 | Taslaklar ayrı grupta | §6.7, CB-34 |
| KR-6 | (KR-8 ile değiştirildi) | – |
| KR-7 | Zaman/token bütçesi durdurmaz, para 0, gerçek para her seferinde CEO onayı | başlık, §13 |
| KR-8 | Override edilen view'u değiştiren güvenlik yaması PR'ı bütün override'ları ve satırlarını siler, CB-8 yeşil, elle adım yok, port PR'ı geri ekler. `stack up` pin uyuşmazlığında dashboard temasını kapatır | §6.1, §12, C-9, C-14, U-20a/b, CB-8, CB-30 |
| KR-9 | Plane yazma yoklamaları yalnız atılabilir Plane'de, canlı Plane yalnız okuma. Member yedeği gerekirse CEO yetenek listesini Faz 2a imzasında kabul eder. Kullanıcıyı ve token'ı CEO oluşturur | §7.3, T-0c, CB-28 |
| KR-10 | Faz 2a ve Faz 2b ayrımı, üç imza satırı | başlık, §9, §13 |

**Açık soru: yok.**

**İmza ön koşulları:** Faz 1: T-A7b, board K3 yeniden kontrolü, T-0d (T-5'ten önce). Faz 2a: T-0a2 (K2-4, K3-5), T-0c, T-A6 (K2-8), Faz 2a kapı turu. Faz 2b: Faz 2a teslimi, kapı turu.

---
## Signature record (CEO only)
Approved by / on (Faz 1): CEO 2026-11-09 — "ok min token tüket /caveman bitir" (approved in chat)
Approved by / on (Faz 2a):
Approved by / on (Faz 2b):

## Assumptions
- 0001 revizyon 3 imzalanır. 0001 T-2/T-5 Faz 1'den, T-4 Faz 2a'dan önce teslim edilir.
- Her makinede tek bir Plane çalışma alanı bağlanır.
- CB-28 (c)'deki canlı Plane, 0001 ile kurulmuş, pinli v1.4.3 yerel Plane'dir.
- Makineler tek kullanıcılı (0001). Çok kullanıcılı testler yetki süzmesini kanıtlamak içindir.
- `git pull && ./stack up` sunucu tarafı kodu dağıtır. Tema için dağıtım anı `up bookstack`'tir (C-16). 0001 T-11 (branch protection, 2FA) uygulandı mı doğrulanmadı. M-1 bu doğrulamaya kadar kullanılmaz.
- Kart adresleri diğer stack'in normalize config'inden 0001 §7.4 fonksiyonuyla hesaplanır.
- BookStack ana sayfa ayarı ve kullanıcı blok tercihleri makinenin DB'sindedir.
- Spec dosyası `docs/` yolunda.

## Scorecard (end of job)
| Measure | Value |
|---|---|
| Spec revisions | 5 (r1..r4 önceki turlar, r5 Faz 1 kapı turu 3) |
| Fix rounds | |
| Findings: real / noise / deferred | tur 3: board K3-1..K3-5 + A3-1..A3-7, critic H1-H6 + M1-M6 + L1-L9, appsec S3-01..S3-07. Ertelenen: §15.3 |
| Regressions | |
| Escaped defects | |
| Estimated / actual time and quota | tahmin: Faz 1 kalan 10 sa, Faz 2a 13,75 sa, Faz 2b 3,9 sa (bilgi, tavan yok) |
