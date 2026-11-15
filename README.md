# selfhost-stack

BookStack, Penpot ve Plane'i kendi makinende çalıştırmak için tek merkez. Depo araçları ve belgeleri taşır. Veri, parola ve token taşımaz.

`./stack` komutu üç uygulamayı Docker Compose ile kurar, yalnızca `127.0.0.1` üzerinde yayınlar ve parolaları makinede rastgele üretir. BookStack ana sayfasını dört bölümlü bir panele çeviren [`dashboard/`](dashboard/README.md) (Seni bekliyor, Devam eden, Son değişiklikler, Projeler) ayrıca çalışır.

Tanıtım sayfası (3D, animasyonlu): [`site/index.html`](site/index.html). Tarayıcıda aç.

## İçerik

| Klasör | İçerik | Durum |
|---|---|---|
| `stack`, `stacks/` | `./stack` komutu; BookStack, Penpot ve Plane için Docker Compose kurulumu (macOS, Apple Silicon üzerinde çalıştırıldı) | Hazır |
| `local.example/` | `local/` için şablon (`.env.example`) | Hazır |
| `dashboard/` | BookStack ana sayfa paneli | Çalışıyor |
| `site/` | Tanıtım sayfası (tek HTML dosyası) | Hazır |
| `docs/` | Spec 0001 (üç uygulamanın ortak kurulumu), spec 0002 (panel), incelemeler, mimari notlar | Belge |
| `stacks/bookstack/theme/`, `tests/` | BookStack theme dilimi ve statik testleri | Hazır |
| `NOTICE` | Üçüncü taraf bileşenler, kaynakları ve lisansları | Belge |

## Gereksinimler

- macOS. Linux için destek iddia edilmez.
- Docker ve Docker Compose (v2.24.4 ya da üstü). Plane yaklaşık 12 container çalıştırır. Ölçülen boşta bellek kullanımı: BookStack ~175 MiB, Penpot ~2,9 GiB, Plane ~1,4 GiB; iş yüküyle artar.
- `curl`, `lsof` (yoksa `nc`) ve `openssl` (yoksa `od`).
- Apple Silicon'da amd64 image'ları emülasyonla çalışabilir. `up` ve `status` bunu `UYARI: <image> amd64 emülasyonla çalışıyor` satırıyla bildirir.

## Kurulum: üç uygulamayı çalıştırmak

1. Depoyu indir ve `local/` dizinini üret:

   ```bash
   git clone https://github.com/GktuOktay/selfhost-stack
   cd selfhost-stack
   ./stack init
   ```

   `init`, `local.example/` içindeki şablondan `local/.env` dosyasını oluşturur. `__GENERATE__` yazan her secret rastgele bir değerle dolar. Var olan bir anahtarı `init` değiştirmez; eksik anahtarları ekler.

2. Uygulamaları başlat:

   ```bash
   ./stack up          # üçü birden (all ile aynı)
   ./stack up bookstack
   ./stack up penpot
   ./stack up plane
   ```

   `up`, her uygulamanın sağlık denetimini en çok `HEALTH_TIMEOUT` saniye (varsayılan 600, image çekme süresi hariç) bekler. Başarıda `OK <app> http://127.0.0.1:<port>` yazar.

3. Adresler:

   | Uygulama | Adres |
   |---|---|
   | BookStack | http://127.0.0.1:8701 |
   | Penpot | http://127.0.0.1:8702 |
   | Plane | http://127.0.0.1:8703 |

   Portlar `local/.env` içindeki `BOOKSTACK_PORT`, `PENPOT_PORT` ve `PLANE_PORT` anahtarlarındadır. Değiştirirsen başka bir yeri düzenlemen gerekmez. Port doluysa `up` o uygulamayı başlatmaz ve düzeltilecek anahtarı söyler.

### Komutlar

| Komut | Ne yapar |
|---|---|
| `./stack init` | `local/` dizinini ve `local/.env` dosyasını oluşturur, eksik anahtarları ekler |
| `./stack up [bookstack\|penpot\|plane\|all]` | Uygulamayı çeker, başlatır, sağlık denetimini bekler. Argümansız `all` |
| `./stack status [app]` | Durumu yazar (ör. BookStack için `default-login: no`, Plane için `plane-admin: unclaimed`) |
| `./stack logs <app> [servis]` | Son 200 satırı basar, `-f` ile izler. Tek uygulama ister |
| `./stack backup [app]` | Veritabanı dökümünü ve dosya volume'larını `local/backups/<app>/<UTC>/` altına yazar. Uygulama çalışıyor olmalı |
| `./stack down [app]` | Container ve ağları kaldırır. Veri volume'larını silmez |

`init`, `up`, `status`, `backup` ve `logs` çıktılarında secret değerleri `***` olarak görünür. Çıkış kodları: 0 başarı, 1 kullanım hatası, 2 ön koşul eksik, 3 port dolu, 4 sağlık zaman aşımı, 5 yedek ya da başlatma hatası, 6 güvenlik kapısı (varsayılan kimlik ya da talep edilmemiş admin).

## İlk yönetici adımları

### BookStack

`init` yönetici e-postasını `BOOKSTACK_ADMIN_EMAIL` anahtarına (varsayılan `admin@selfhost.local`) ve rastgele parolayı `BOOKSTACK_ADMIN_PASSWORD` anahtarına yazar. `up` upstream'in varsayılan `admin@admin.com` hesabını bu e-posta ve parolayla değiştirir. Parolanın kendisi ekrana basılmaz; `local/.env` dosyasından oku. Varsayılan hesap kalırsa `up` 6 koduyla çıkar.

`BOOKSTACK_ADMIN_PASSWORD` değerini sonradan değiştirirsen `up` bunu uygulamaz: varsayılan hesap yoksa ve başka bir yönetici varsa `up` atlar. Parolayı BookStack içinden değiştir.

### Penpot

Kayıt kapalıdır. İlk profil için upstream'in `prepl` sunucusunu geçici olarak aç:

1. `local/.env` içine `PENPOT_EXTRA_FLAGS=enable-prepl-server` yaz ve `./stack up penpot` çalıştır.
2. `docker exec -ti selfhost-penpot-penpot-backend-1 python3 manage.py create-profile`
3. `PENPOT_EXTRA_FLAGS` değerini `local/.env` içinde boşalt ve `./stack up penpot` çalıştır. Backend `prepl` olmadan yeniden oluşur.

`enable-prepl-server` kimliksiz bir REPL açar; kalıcı bırakma. Bayrak doluyken `status` uyarı verir.

### Plane

`up`, instance yöneticisi talep edilene kadar 6 koduyla çıkar. Tarayıcıda `http://127.0.0.1:8703/god-mode/` adresini aç ve yönetici hesabını oluştur. Sonra `./stack up plane` komutunu tekrar çalıştır.

Plane telemetri bildirimi için ortam değişkeni yoktur; `god-mode` ekranından kapatılır. Compose dosyasındaki `ENABLE_SIGNUP=0` değeri yalnızca instance'ın ilk başlangıcında okunur; sonraki değişiklik `god-mode` ekranından yapılır.

## `local/` dizini

`local/` makineye özeldir ve git'e girmez:

| Yol | İçerik | Mod |
|---|---|---|
| `local/.env` | Portlar ve secret'lar | 600 |
| `local/backups/<app>/<UTC>/` | `backup` çıktıları | 700 (dizin), 600 (dosya) |

Başka bir konum için `STACK_LOCAL_DIR` ortam değişkenine mutlak yol ver.

- **`local/` bulut senkronuna girmesin.** iCloud Drive ve Time Machine gibi yedekleme ya da senkron araçlarının dışında tut: içinde parolalar var.
- **`local/` kaybolursa:** `local/.env` yokken `init` yeni secret üretir; bunlar eski veritabanıyla uyuşmaz. `selfhost-<app>_*` volume'ları varsa `init` bunu uyarı olarak yazar. Çözüm, `local/.env` yedeğini geri koymak ya da ilgili volume'ları elle silmektir. `./stack` hiçbir volume silmez.
- **Veritabanı ana sürüm atlaması `up` ile korunmaz.** Postgres (Penpot, Plane) ya da MariaDB (BookStack) imajının ana sürümünü değiştirirsen eski veri dizini açılmaz. Önce `./stack backup` ile dökümü al, sonra elle dump/restore yap.

## Kurulum: paneli kendi BookStack'ine taşımak

1. Depoyu indir (yukarıdaki `git clone` adımı).
2. BookStack'e yönetici olarak giriş yap. "Panel" adlı bir kitap aç, içinde "Panel" adlı bir sayfa oluştur.
3. Sayfayı HTML (WYSIWYG) düzenleyicide aç, kaynak koduna `dashboard/panel-page.html` içeriğini yapıştır ve kaydet.
4. Settings, Customization, "Özel HTML başlık içeriği" alanının sonuna `dashboard/panel-head.html` içeriğini ekle (`selfhost-panel-start` ve `selfhost-panel-end` işaretleri dahil). Alandaki mevcut içeriği silme.
5. Aynı ekranda "Ana sayfa içeriği" ayarını "Spesifik Sayfa" yap ve "Panel" sayfasını seç. Kaydet.
6. Ana sayfayı yenile. Dört panel dolmalı.

Ayrıntı ve geri alma adımları: [`dashboard/README.md`](dashboard/README.md).

## Makineye göre değiştirmen gerekenler

- `dashboard/panel-page.html` içindeki Plane (`localhost:8090`) ve Penpot (`localhost:9001`) adresleri. `./stack` ile kurduysan portlar 8703 ve 8702'dir.
- Panelin veri kaynakları BookStack'teki sayfa adlarına dayanır: her projenin "Sorular" ve "Beklenenler" sayfaları ve "İş Planı" kitapları. Farklı adlar kullanıyorsan `panel-head.html` içindeki betiği düzenle.

## Sorun giderme

- **Paneller "Yüklenemedi" diyor:** BookStack API sınırı dakikada 180 istektir. Bir dakika bekle ve sayfayı yenile. Sonuçlar tarayıcıda 2 dakika önbelleğe alınır.
- **Sayfa dar görünüyor, yan paneller duruyor:** Özel başlık içeriği kaydedilmemiş ya da `selfhost-panel-start` bloğu eksik. Panel kurulumunun 4. adımını tekrarla.
- **Paneli kaldırmak:** "Ana sayfa içeriği"ni "Varsayılan"a çevir. Özel başlık alanında `selfhost-panel-start` ile `selfhost-panel-end` arasını sil.
- **`up` 3 koduyla çıktı:** Port başka bir süreçte açık. Mesajdaki anahtarı `local/.env` içinde değiştir.
- **`up` 6 koduyla çıktı:** Yukarıdaki "İlk yönetici adımları" bölümüne bak.

## Güvenlik notları

- Parola, token ve `.env` dosyalarını depoya ekleme. `.gitignore` bunları dışarıda tutar.
- Üç uygulama yalnızca `127.0.0.1` üzerinde yayınlanır; veritabanı ve önbellek servisleri host'a port açmaz.
- Penpot'ta kayıt, e-posta, MCP ve telemetri kapalı kurulur.
- Panel tarayıcıda, açık oturumun yetkisiyle BookStack API'sini okur. Ayrı bir token kullanmaz.

## Lisans ve kaynaklar

Bu deponun kendi dosyaları [MIT](LICENSE) lisanslıdır. Uygulamalar ve upstream'den kopyalanan compose dosyaları kendi lisanslarını korur. Ayrıntı: [`NOTICE`](NOTICE).

| Uygulama | Kaynak | Lisans |
|---|---|---|
| BookStack | [github.com/BookStackApp/BookStack](https://github.com/BookStackApp/BookStack), image: [linuxserver/docker-bookstack](https://github.com/linuxserver/docker-bookstack) | MIT |
| Penpot | [github.com/penpot/penpot](https://github.com/penpot/penpot) | MPL-2.0 |
| Plane | [github.com/makeplane/plane](https://github.com/makeplane/plane) | AGPL-3.0 |
