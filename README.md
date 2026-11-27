# selfhost-stack

Penpot'u kendi makinende çalıştırmak için kurulum ve araçlar. Veri, parola ve token taşımaz.

`./stack` komutu Penpot'u Docker Compose ile kurar, yalnızca `127.0.0.1` üzerinde yayınlar ve parolaları makinede rastgele üretir. Penpot projelerini dışa ve içe aktarma komutları da buradadır. Proje yönetimi (eski BookStack ve Plane yerine) TabTab (http://localhost:7300) ile yapılır.

## İçerik

| Yol | İçerik |
|---|---|
| `stack`, `stacks/penpot/` | `./stack` komutu ve Penpot için Docker Compose kurulumu (macOS, Apple Silicon üzerinde çalıştırıldı) |
| `local.example/` | `local/` için şablon (`.env.example`) |
| `tests/` | `./stack` ve Penpot dışa/içe aktarma testleri |
| `docs/` | Spec'ler, incelemeler, mimari notlar |
| `NOTICE` | Üçüncü taraf bileşenler, kaynakları ve lisansları |

## Gereksinimler

- macOS. Linux için destek iddia edilmez.
- Docker ve Docker Compose (v2.24.4 ya da üstü). Ölçülen boşta bellek kullanımı: Penpot ~2,9 GiB; iş yüküyle artar.
- `curl`, `lsof` (yoksa `nc`) ve `openssl` (yoksa `od`).
- Apple Silicon'da amd64 image'ları emülasyonla çalışabilir. `up` ve `status` bunu `UYARI: <image> amd64 emülasyonla çalışıyor` satırıyla bildirir.

## Kurulum

1. Depoyu indir ve `local/` dizinini üret:

   ```bash
   git clone https://github.com/GktuOktay/selfhost-stack
   cd selfhost-stack
   ./stack init
   ```

   `init`, `local.example/` içindeki şablondan `local/.env` dosyasını oluşturur. `__GENERATE__` yazan her secret rastgele bir değerle dolar. Var olan bir anahtarı `init` değiştirmez; eksik anahtarları ekler. Eski kurulumlardan kalan `BOOKSTACK_*` ve `PLANE_*` anahtarları `local/.env` içinde durabilir; yok sayılır.

2. Başlat:

   ```bash
   ./stack up penpot
   ```

   `up`, sağlık denetimini en çok `HEALTH_TIMEOUT` saniye (varsayılan 600, image çekme süresi hariç) bekler. Başarıda `OK penpot http://127.0.0.1:<port>` yazar.

3. Adres: http://127.0.0.1:8702. Port `local/.env` içindeki `PENPOT_PORT` anahtarındadır. Port doluysa `up` başlatmaz ve düzeltilecek anahtarı söyler.

### Komutlar

| Komut | Ne yapar |
|---|---|
| `./stack init` | `local/` dizinini ve `local/.env` dosyasını oluşturur, eksik anahtarları ekler |
| `./stack up [penpot\|all]` | Uygulamayı çeker, başlatır, sağlık denetimini bekler |
| `./stack status [app]` | Durumu yazar |
| `./stack logs penpot [servis]` | Son 200 satırı basar, `-f` ile izler |
| `./stack backup [app]` | Veritabanı dökümünü ve dosya volume'larını `local/backups/<app>/<UTC>/` altına yazar. Uygulama çalışıyor olmalı |
| `./stack export penpot <proje\|id> [-o dizin] [--embed-assets]` / `--list` | Penpot projesini `.penpot` dosyaları ve `manifest.json` (hash'li) olarak `local/exports/penpot/<UTC>/` altına (ve `.tar` olarak yanına) yazar. Penpot çalışıyor olmalı |
| `./stack import penpot <dizin\|.tar> [--team ad] [--project ad]` | Arşivi önce hash'lerle doğrular, projeyi yoksa oluşturur, dosyaları içeri alır |
| `./stack down [app]` | Container ve ağları kaldırır. Veri volume'larını silmez |

`init`, `up`, `status`, `backup` ve `logs` çıktılarında secret değerleri `***` olarak görünür. Çıkış kodları: 0 başarı, 1 kullanım hatası, 2 ön koşul eksik, 3 port dolu, 4 sağlık zaman aşımı, 5 yedek ya da başlatma hatası, 6 güvenlik kapısı.

## Penpot

Kayıt kapalıdır. İlk profil için upstream'in `prepl` sunucusunu geçici olarak aç:

1. `local/.env` içine `PENPOT_EXTRA_FLAGS=enable-prepl-server` yaz ve `./stack up penpot` çalıştır.
2. `docker exec -ti selfhost-penpot-penpot-backend-1 python3 manage.py create-profile`
3. `PENPOT_EXTRA_FLAGS` değerini `local/.env` içinde boşalt ve `./stack up penpot` çalıştır. Backend `prepl` olmadan yeniden oluşur.

`enable-prepl-server` kimliksiz bir REPL açar; kalıcı bırakma. Bayrak doluyken `status` uyarı verir.

**Projeyi başka bilgisayara taşıma.** `export`/`import` Penpot'un kendi `binfile` biçimini kullanır. Kimlik için ortamda `PENPOT_EMAIL` ve `PENPOT_PASSWORD` (ya da `enable-access-tokens` bayrağıyla üretilmiş `PENPOT_ACCESS_TOKEN`) ver; yoksa terminalde sorulur. Parola komut satırına yazılmaz.

```
./stack export penpot --list
./stack export penpot "Marka Seti"          # local/exports/penpot/<UTC>/ ve <UTC>.tar
./stack import penpot marka.tar --team "Ekibim"
```

Varsayılan olarak dosyalar kütüphaneleriyle birlikte (`include-libraries`) dışa aktarılır; kütüphaneleri dosyanın içine gömmek için `--embed-assets` ver (ikisi birlikte kullanılamaz, Penpot izin vermez). Çıktı kullanıcının tasarım verisidir; yalnız sende kalan `local/` altında 700/600 izinle durur. Var olan bir projeye içe aktarırsan dosyalar eklenir, mevcutlar değişmez.

## `local/` dizini

`local/` makineye özeldir ve git'e girmez:

| Yol | İçerik | Mod |
|---|---|---|
| `local/.env` | Port ve secret'lar | 600 |
| `local/backups/<app>/<UTC>/` | `backup` çıktıları | 700 (dizin), 600 (dosya) |

Başka bir konum için `STACK_LOCAL_DIR` ortam değişkenine mutlak yol ver.

- **`local/` bulut senkronuna girmesin.** iCloud Drive ve Time Machine gibi yedekleme ya da senkron araçlarının dışında tut: içinde parolalar var.
- **`local/` kaybolursa:** `local/.env` yokken `init` yeni secret üretir; bunlar eski veritabanıyla uyuşmaz. `selfhost-<app>_*` volume'ları varsa `init` bunu uyarı olarak yazar. Çözüm, `local/.env` yedeğini geri koymak ya da ilgili volume'ları elle silmektir. `./stack` hiçbir volume silmez.
- **Veritabanı ana sürüm atlaması `up` ile korunmaz.** Penpot'un Postgres imajının ana sürümünü değiştirirsen eski veri dizini açılmaz. Önce `./stack backup` ile dökümü al, sonra elle dump/restore yap.

## Sorun giderme

- **`up` 3 koduyla çıktı:** Port başka bir süreçte açık. Mesajdaki anahtarı `local/.env` içinde değiştir.
- **`up` 6 koduyla çıktı:** Güvenlik kapısı geçmedi; mesajdaki yönergeyi uygula.

## Güvenlik notları

- Parola, token ve `.env` dosyalarını depoya ekleme. `.gitignore` bunları dışarıda tutar.
- Penpot yalnızca `127.0.0.1` üzerinde yayınlanır; veritabanı ve önbellek servisleri host'a port açmaz.
- Penpot'ta kayıt, e-posta, MCP ve telemetri kapalı kurulur.

## Lisans ve kaynaklar

Bu deponun kendi dosyaları [MIT](LICENSE) lisanslıdır. Penpot ve upstream'den kopyalanan compose dosyası kendi lisansını korur (MPL-2.0, kaynak: [github.com/penpot/penpot](https://github.com/penpot/penpot)). Ayrıntı: [`NOTICE`](NOTICE).
