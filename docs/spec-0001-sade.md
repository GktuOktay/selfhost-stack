# Spec 0001 (sade): selfhost-stack, BookStack + Penpot + Plane

- Status: Awaiting approval
- Tier: quick, Lane 2 (yeni dış image bağımlılıkları, secret üretimi, loopback ağ yüzeyi, public repo)
- Revision: 1 (spec-critic B2..B8/M1..M5/N1..N2, appsec S-01..S-07, board C-1..C-5 ve CEO varsayılanları işlendi)
- Replaces: `docs/spec-r2-full.md` (CEO: "sade sürüm"). Girdiler: `docs/reviews/scout-upstream.md`, `docs/architecture/gorus-0001-sade-2026-11-15.md`.
- Budget ceiling: zaman ve token tavanı işi asla durdurmaz. Para harcaması CEO onayı ister (öneri: 0, ücretli servis yok).

## 0. CEO kararları (varsayılan uygulandı; imza = kabul)

1. Spec 0002 Faz 1 teması olduğu gibi kalır (`stacks/bookstack/theme/selfhost-dashboard/`). dashfeed ve Faz 2 ertelendi. 0002'nin sade modele hizalanması imzadan sonra ayrı iş (BA). Tema ile BookStack sürümü arasındaki bağ bu spec'te zorlanmaz (§9).
2. amd64 emülasyonu (Apple Silicon) uyarıyla kabul edilir; AC-12 emülasyonla da geçer.
3. Platform: şimdilik yalnız macOS. Linux desteği iddia edilmez.
4. Tavan: zaman/token tavanı engel değil, para onay ister.
5. `pgsty/silo` riski kabul: yalnız Plane, yalnız `127.0.0.1`, tam tag + digest, ADR-0004 (yazıldı: `docs/architecture/tasarim/ADR-0004-silo-object-storage.md`).
6. Repo PUBLIC ve Plane AGPL-3.0: kopyalanan upstream compose dosyaları upstream lisans başlığını korur, `NOTICE` kaynakları ve lisansları listeler. Repo'nun kendi dosyaları için `LICENSE` seçimi CEO'ya aittir; seçilene kadar eklenmez.

## 1. Intent

**CEO'nun cümleleri (r2 §1):** Araçlar (compose, pinli versiyonlar, CLI) git'te merkezi yönetilir; her makine `git pull && ./stack up` ile alır. Veri, secret ve makine ayarları makineye özeldir, gitignored `local/` içinde durur, git'e girmez. Bir makinedeki özelleştirme diğerini etkilemez.

**Yorumum:** Temiz Mac'te `git clone` → `./stack init` → `./stack up` ile üç uygulama yalnızca `127.0.0.1` üzerinde, pinli versiyonlarla, rastgele secret'larla ve upstream varsayılan kimlik bilgisi olmadan açılır. `git status` temiz kalır.

**Non-goals:** TLS, LAN/uzaktan erişim, restore otomasyonu, upgrade prosedürü, kayan-tag koruması dışındaki digest guard'ları, izleme, makineler arası senkron, SMTP/SSO, veri göçü, Linux.

## 2. Requirements (EARS)

- REQ-1: Sistem, `stacks/{bookstack,penpot,plane}/compose.yaml` ve her biri için `hooks.sh` (health, bootstrap, backup tanımı) sağlayacak.
- REQ-2: Sistem, her image'ı tam patch etiketiyle sabitleyecek; `bookstack` ve `silo` image'larına ayrıca `@sha256` digest ekleyecek.
- REQ-3: Sistem, tek bir bash 3.2 uyumlu `./stack` sunacak: `init`, `up`, `down`, `status`, `logs`, `backup`. `<app>` ∈ {bookstack, penpot, plane, all}; argümansız = `all`; `logs` tek uygulama ister.
- REQ-4: `init` çalışınca sistem, `local.example/` içeriğinden eksik dosyaları `local/` altına koyacak ve eksik anahtarları ekleyecek; üretilen secret'lar rastgele olacak.
- REQ-5: Var olan bir anahtarı `init` değiştirmeyecek; `local/.env` yazımı kısmi dosya bırakmayacak (geçici dosya + yeniden adlandırma).
- REQ-6: Sistem, secret, port ve yedekleri yalnızca gitignored `local/` altında (ya da `STACK_LOCAL_DIR` ile verilen mutlak dizinde) tutacak; dosya modu 600, dizin 700 (`umask 077`).
- REQ-7: Sistem, `local/.env`'i satır satır okuyacak, hiçbir satırı çalıştırmayacak; izin verilmeyen anahtar, `KEY=` biçimi dışındaki satır ya da boş zorunlu anahtar için `<dosya>:<satır>` ile reddedecek.
- REQ-8: Sistem, uygulama adını izin listesinden, portu 1024-65535 aralığından ve üç portun birbirinden farklı olmasından doğrulayacak.
- REQ-9: Sistem, giriş servisini `127.0.0.1:<port>` olarak yayınlayacak; diğer tüm servisler yalnızca `internal: true` bir ağda olacak ve host'a hiçbir port açmayacak.
- REQ-10: Sistem, host izolasyonunu kaldıran ayarı (host ağı, privileged, `cap_add`, `docker.sock`, host pid) hiçbir serviste kullanmayacak.
- REQ-11: Uygulamanın dış adresi (`APP_URL`, `PENPOT_PUBLIC_URI`, `WEB_URL`/`CORS_ALLOWED_ORIGINS`) her zaman `http://127.0.0.1:<port>` olacak; port değişince başka bir şey düzenlenmeyecek.
- REQ-12: Upstream kapatmaya izin veriyorsa sistem, açık kaydı, telemetriyi ve ihtiyaç dışı servisleri (Penpot: mailpit, mcp, admin-console) kapalı kuracak; Penpot `enable-prepl-server` bayrağı varsayılan kapalı olacak.
- REQ-13: `up`, port doluysa o uygulamayı başlatmayacak ve portu ile düzeltilecek anahtarı bildirecek. Port, bu projenin kendi container'ında yayınlıysa çakışma sayılmayacak; tekrar `up` değişiklik yapmayacak.
- REQ-14: `up`, bir uygulamayı çekip başlattıktan sonra uygulamaya özel health probunu `HEALTH_TIMEOUT` (varsayılan 600 sn, çekme süresi hariç, uygulama başına) boyunca bekleyecek.
- REQ-15: `up`, BookStack'te upstream varsayılan girişin (`admin@admin.com`) kaldırıldığını, Plane'de instance admin'in talep edildiğini doğrulayana kadar sıfırdan farklı kodla (6) çıkacak. BookStack admin parolasını `init` üretir.
- REQ-16: `backup <app|all>` çalışan uygulamanın DB dump'ını ve dosya volume'larını `local/backups/<app>/<UTC>/` altına yazacak; DB parolası komut satırında görünmeyecek.
- REQ-17: Sistem hiçbir veri volume'unu silmeyecek; `down` yalnız container ve ağları kaldıracak.
- REQ-18: `init`, `local/.env` yokken `selfhost-<app>_*` volume'ları varsa uyaracak: yeni secret eski veriyle uyuşmaz.
- REQ-19: Sistem `init`, `up`, `status`, `backup` ve `logs` çıktılarında secret değerlerini (değere göre) `***` yapacak.
- REQ-20: Her hatada sistem tek satırlık `HATA: <düzeltme>` mesajını stderr'e yazıp aşağıdaki kodlardan biriyle çıkacak. `all` komutunda her uygulama denenecek, uygulama başına bir özet satırı basılacak, çıkış kodu sıradaki (bookstack, penpot, plane) ilk başarısızınki olacak; ortak ön koşul başarısızsa hiçbiri denenmeyecek.
- REQ-21: Her `up` ve `status`, upstream image'ı host mimarisinden farklıysa `UYARI: <image> amd64 emülasyonla çalışıyor` yazacak.
- REQ-22: BookStack temayı `stacks/bookstack/theme/selfhost-dashboard/` dizininden salt-okunur bağlayacak ve `APP_THEME=selfhost-dashboard` verecek.
- REQ-23: Repo, kopyalanan upstream dosyalarının lisans başlığını ve `NOTICE` dosyasını içerecek.

**Çıkış kodları:** 0 başarı · 1 kullanım (bilinmeyen komut/uygulama, `logs all`) · 2 ön koşul (Docker/araç yok, `local/` yok, bozuk `.env`, eksik anahtar, geçersiz port) · 3 port dolu · 4 health zaman aşımı · 5 yedek/başlatma işlemi başarısız · 6 güvenlik kapısı (varsayılan kimlik, admin yok).
`logs <app> [service]` son 200 satırı basar, `-f` ile izler. Gerekli araçlar: `docker` (Compose v2), `curl`, `lsof` (yoksa `nc`), `openssl` (yoksa `od`).

## 3. User experience

UI yok, CLI.

| Durum | Davranış |
|---|---|
| Boş (`local/` yok) | `up/down/status/logs/backup` exit 2 "önce ./stack init" |
| Yükleniyor | `up` her 5 sn'de `bekleniyor <app> <geçen>/<HEALTH_TIMEOUT> sn` |
| Hata | tek satır `HATA:` (stderr) + kod |
| Başarı | `OK <app> http://127.0.0.1:<port>`; ilk kurulumda admin e-postası ve parolanın `local/.env` içindeki anahtar adı (parolanın kendisi basılmaz) |
| Yetkisiz | Docker erişilemiyor: exit 2 |

## 4. Acceptance criteria

Testler `tests/run.sh` ile `STACK_LOCAL_DIR=<temp>` kullanır, gerçek `local/`'e dokunmaz. `docker compose config` çıktısı (secret içerir) mode 600'lük temp dosyaya yazılır, ekrana basılmaz, test sonunda silinir. Gerekli araç yoksa test `BLOCKED <AC> <araç>` yazar; BLOCKED geçti sayılmaz ve süit 0 vermez.

**Statik (otomatik)**
- [ ] AC-1 (REQ-1,2): Üç stack için `docker compose config` exit 0. Her image `^[^:@]+:(v?[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9._-]+)?|[0-9]+\.[0-9]+(-alpine)?|RELEASE\.[0-9TZ-]+)(@sha256:[0-9a-f]{64})?$` ile eşleşir (`postgres:15`, `latest` reddedilir). `linuxserver/bookstack` ve `pgsty/silo` image'larında `@sha256` vardır.
- [ ] AC-2 (REQ-3): `shellcheck --shell=bash stack stacks/*/hooks.sh tests/run.sh` exit 0; `/bin/bash -n stack` exit 0; `grep -nE 'mapfile|readarray|declare +-A|\$\{[a-zA-Z_]+(,,|\^\^)' stack stacks/*/hooks.sh` boş; süit macOS `/bin/bash` (3.2) ile koşar.
- [ ] AC-3 (REQ-4,5,6,7): Temp `STACK_LOCAL_DIR`'de `init` sonrası dizin 700, `.env` 600; her secret anahtarı boş değil, hex ≥ 48 karakter (`BOOKSTACK_APP_KEY` `base64:` + 44 karakter), hepsi birbirinden farklı. İkinci `init` sonrası `shasum` aynı. Bir anahtar silinip `init` tekrarlanırsa yalnız o satır eklenir, diğerleri byte düzeyinde aynı. `*.tmp` kalıntısı yok. Değerinde `=` bulunan bir satır (`BOOKSTACK_APP_KEY`) doğru okunur. `export X=1`, `=`'siz satır, küçük harfli anahtar `up` sırasında `<dosya>:<satır>` ile exit 2; `X=$(touch <tmp>/pwn)` değeri çalışmaz (`pwn` oluşmaz).
- [ ] AC-4 (REQ-6): Temiz bir `git clone` kopyasında (varsayılan `local/`) `./stack init` sonrası `git status --porcelain` boş; `git check-ignore local/.env local/backups` ikisini gösterir.
- [ ] AC-5 (REQ-9,10): Her stack'in config'inde `published:` satırı tam 1, `host_ip: 127.0.0.1` satırı tam 1; `network_mode`, `privileged`, `cap_add`, `docker.sock`, `pid:` anahtarlarının hiçbiri yok; `internal: true` bir ağ var. Çalışırken `lsof -nP -iTCP -sTCP:LISTEN` 8701/8702/8703'ü yalnız `127.0.0.1`'de gösterir; `docker inspect` ile DB container'ı yalnız internal ağdadır.
- [ ] AC-6 (REQ-11,12): Penpot config'inde `penpot-mailpit`, `penpot-mcp`, `penpot-admin-console` servisi yok (admin-console çıkarılamazsa T-3 gerekçeyi `hooks.sh` başına yazar ve her `depends_on` `config` ile geçerli); `PENPOT_FLAGS` içinde `disable-registration` var, `enable-smtp`, `enable-mcp`, `enable-prepl-server`, `enable-telemetries` yok; `PENPOT_TELEMETRY_ENABLED=false`. Plane'de kayıt kapatma anahtarı T-4'te upstream'de aranır: varsa kapalı değerdedir, yoksa sonuç README'ye yazılır. `APP_URL`/`PENPOT_PUBLIC_URI`/`WEB_URL`/`CORS_ALLOWED_ORIGINS` değerleri `http://127.0.0.1:<port>` ile aynıdır; port değişince config yeni portu gösterir.
- [ ] AC-7 (REQ-12): Config'te şu anahtar adları vardır ve değerleri `local/.env`'deki karşılık değerle birebir aynıdır (varsayılan upstream değerleri anahtar adına göre denetlenir, değer parçasına göre değil): `SECRET_KEY`, `LIVE_SERVER_SECRET_KEY`, `POSTGRES_PASSWORD`, `RABBITMQ_PASSWORD`/`RABBITMQ_DEFAULT_PASS`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `PENPOT_SECRET_KEY`, `APP_KEY`, `DB_PASSWORD`, `MARIADB_PASSWORD`. Zorunlu anahtar eksik/boşken `up` docker çağırmadan exit 2 verir (compose `${VAR:?}` ikinci savunma).
- [ ] AC-8 (REQ-8,20): Bilinmeyen komut, bilinmeyen uygulama, `logs all` exit 1; port 80, 70000, `abc` ya da iki aynı port exit 2; her durumda stderr tam 1 satır `HATA:`. Docker PATH'ten çıkarılınca exit 2 (araç adı mesajda). Gerekli her araç için aynı test.
- [ ] AC-9 (REQ-18): PATH'te sahte `docker` ile `selfhost-bookstack_config` volume'u "var" iken `.env` yokken `init` uyarı satırı basar (exit 0, secret'lar yine üretilir).
- [ ] AC-10 (REQ-23): `NOTICE` üç upstream'i (repo, tag, lisans) listeler; `penpot` ve `plane` compose dosyalarının ilk satırlarında upstream URL + tag + lisans yorumu vardır.

**Canlı (Mac, Docker; çıktı rapora girer)**
- [ ] AC-11 (REQ-13,14,15): `./stack up bookstack` exit 0; `curl -fsS http://127.0.0.1:8701/status` 200; giriş sayfası (`curl -sSL http://127.0.0.1:8701/login`) 200 ve gövdede `BookStack`; `./stack status` bookstack için `healthy`, `default-login: no`. Kanıt: taze çıktı + Docker runtime adı/versiyonu. Docker yoksa BLOCKED.
- [ ] AC-12 (REQ-14,21): Penpot (`GET /` 8702: 200, gövdede `penpot`) ve Plane (`curl -sSL http://127.0.0.1:8703/` son durum 200, gövde boş değil; `/api/instances/` JSON döner) için `up` geçer. Her uygulamada saat çekmeden sonra başlar. amd64 emülasyonu uyarıyla geçerli sayılır; çalışmayan image varsa raporda adıyla yazılır.
- [ ] AC-13 (REQ-13,20): Zaten çalışan stack'te ikinci `up` exit 0, container ID'leri aynı, port çakışması bildirmez. Port 8701'i `nc -l` ile tutarken (BookStack kapalı) `up bookstack` exit 3, mesajda `BOOKSTACK_PORT` ve `local/.env`, hiçbir container başlamaz. `up all` sırasında bir uygulama 3 ile düşerse diğerleri denenir, 3 özet satırı basılır, çıkış 3'tür. `HEALTH_TIMEOUT=1 ./stack up plane` exit 4.
- [ ] AC-14 (REQ-15): BookStack: `up` sonrası `users` tablosunda `admin@admin.com` sayısı 0 (probe: `docker compose exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -N -u"$MARIADB_USER" "$MARIADB_DATABASE" -e "SELECT COUNT(*) FROM users WHERE email='"'"'admin@admin.com'"'"'"'`) ve `BOOKSTACK_ADMIN_EMAIL` kullanıcısı `local/.env` parolasıyla girer. `status` çıktısı: durum temiz `default-login: no`, aksi `default-login: YES (UYARI)`; ikinci durumda `up` exit 6. Admin oluşturma/varsayılanı kaldırma komutları T-2'de doğrulanıp `hooks.sh`'e yazılır (aday: `artisan bookstack:create-admin`; doğrulanamazsa SQL fallback, T-2 kayda geçer). Plane: instance admin talep edilmemişse (`/api/instances/` kurulum bayrağı; alan adı T-4'te doğrulanır) `up` exit 6 ve `http://127.0.0.1:8703/god-mode/` yönergesi, `status` `plane-admin: unclaimed`; talep sonrası `claimed` ve exit 0. Penpot'ta ilk profil README prosedürüyle (geçici `PENPOT_EXTRA_FLAGS=enable-prepl-server`, ardından kaldır); bayrak doluyken `status` UYARI basar.
- [ ] AC-15 (REQ-19): `local/.env`'deki her secret değeri için `grep -F` şu çıktılarda 0 eşleşme verir: `init`, `up`, `status`, `backup`, `logs <app>` (son 200 satır). `logs` ve `status` çıktısı değer maskeleyiciden geçer.
- [ ] AC-16 (REQ-16): `backup bookstack` sonrası `local/backups/bookstack/<UTC>/` altında boş olmayan `db.sql` ve dosya volume tar'ı; dizin 700, dosyalar 600; `tar -tf` exit 0. Penpot ve Plane için de (§6 tablosu). Uygulama kapalıyken `backup` exit 2. `ps` çıktısında DB parolası görünmez (dump `exec` içinde container ortamından alır).
- [ ] AC-17 (REQ-17): `down` + `up` sonrası BookStack'te önceden açılan sayfa durur. `grep -nE 'down +-v|volume +(rm|prune)|system +prune' stack stacks/*/hooks.sh` boş.
- [ ] AC-18 (REQ-22): BookStack config'inde tema mount'u `...selfhost-dashboard` hedefinde `read_only: true`, `APP_THEME=selfhost-dashboard`; `git diff --stat stacks/bookstack/theme` boş.
- [ ] AC-19 (I-3): T-8 raporu `docker stats --no-stream` toplam belleği her uygulama için yazar (Plane için ≥ 8 GB Docker belleği önerisi doğrulanır).

## 5. Architecture and technology

| Konu | Seçenekler | Seçim ve gerekçe |
|---|---|---|
| CLI | bash 3.2 / Python / Make | **bash 3.2**: macOS'ta hazır, ek runtime yok; shellcheck ile disiplin. |
| Compose düzeni | vendor + overlay (`!override`) / upstream'i kopyalayıp tek `compose.yaml` | **kopya**: sade, Compose sürüm şartı yok. Maliyet: upstream güncellemesi elle diff (non-goal). |
| Config deposu | tek `local/.env` / uygulama başına dosya | **tek `local/.env`** (CEO: ports `local/.env`'de). Secret'lar `${VAR:?}` ile geçer. Uygulamaya özel gizli olmayan ayarlar (Plane `variables.env` değerleri, Penpot bayrakları) compose içine gömülüdür, git'tedir. |
| Pin | tag / tag+digest | **tam patch tag** (CEO "sade"); `linuxserver/bookstack` ve `pgsty/silo` ek olarak digest (kullanıcı yolundaki topluluk image'ları). Diğerleri Docker Official/vendor, tag içeriği değişebilir (kabul). |
| BookStack image | linuxserver / solidnerd | **linuxserver** (scout F-1/F-2). DB `mariadb:11.4.x` (BookStack SQLite desteklemez). |
| Yedek tar | (a) app image'ında `--entrypoint tar`, (b) `alpine` | **(a) önce** (yeni image yok); (b) yalnız bir image'da `tar` yoksa, T-5 gerekçeyi yazar. |
| `ports` denetimi | `jq` / `config` + grep | **grep** (jq bağımlılığı yok). |

Katman: `docker compose -p selfhost-<app> -f stacks/<app>/compose.yaml --env-file $LOCAL/.env`. Proje adı ve volume adları (`selfhost-<app>_<vol>`) veri kimliğidir (ADR-0001, tek sayfa, T-7). Env'de yalnız `HEALTH_TIMEOUT` ve `STACK_LOCAL_DIR` kabul edilir.

Upstream gerçekleri (scout): BookStack `/status` 200 sağlıklı; varsayılan `admin@admin.com`/`password`. Penpot 2.18.6, frontend `9001:8080`, compose varsayılanı `enable-smtp enable-mcp`, telemetri `true`, mailpit 8025'i açar. Plane v1.4.3 release asset `docker-compose.yml` (healthcheck yok, proxy 80/443 host-mode). Doğrulanmamış: Penpot backend health yolu (frontend `/` kullanılır), Plane kayıt kapatma anahtarı ve admin kurulum bayrağı, arm64 her image.

### Yeni dış bağımlılıklar (hepsi CEO'ya gösterilir)

| Image | Etiket (T-2..T-4'te varlık + arm64 manifest doğrulanır) | Lisans | Çıkış maliyeti |
|---|---|---|---|
| `lscr.io/linuxserver/bookstack` | `v26.09.2-ls<N>@sha256` | MIT / GPL-3.0 | düşük |
| `mariadb` | `11.4.<patch>` | GPL-2.0 | düşük |
| `penpotapp/{frontend,backend,exporter}`, `postgres`, `valkey/valkey` | `2.18.6`, `15.<patch>`, `8.1.<patch>` | MPL-2.0 | yüksek (uygulama) |
| `makeplane/*`, `postgres`, `valkey`, `rabbitmq` | `v1.4.3`, `15.7-alpine`, `7.2.11-alpine`, `3.13.6-management-alpine` | AGPL-3.0 | yüksek |
| `pgsty/silo` | `RELEASE.2026-09-16T00-00-00Z@sha256` | doğrulanmadı (scout'a sorulur) | orta (ADR-0004) |
| `alpine` | yalnız gerekirse | MIT | düşük |

OSV/GHSA taraması bu spec'te yapılmadı; appsec kapısı yapar.

## 6. Data and API contract

Şema yok. Dosyalar ve CLI:

| Yol | Git | İçerik |
|---|---|---|
| `stack`, `stacks/<app>/{compose.yaml,hooks.sh}`, `tests/run.sh`, `NOTICE` | evet | CLI, tanım, probe/bootstrap/backup fonksiyonları, test |
| `local.example/.env.example` | evet | anahtarlar, secret'lar `__GENERATE__` |
| `local/.env` (600), `local/backups/` (700) | hayır | gerçek değerler, yedekler |

`local/.env` zorunlu anahtarlar: `BOOKSTACK_PORT BOOKSTACK_DB_PASSWORD BOOKSTACK_DB_ROOT_PASSWORD BOOKSTACK_APP_KEY BOOKSTACK_ADMIN_EMAIL BOOKSTACK_ADMIN_PASSWORD` · `PENPOT_PORT PENPOT_SECRET_KEY PENPOT_DB_PASSWORD` (isteğe bağlı `PENPOT_EXTRA_FLAGS`) · `PLANE_PORT PLANE_SECRET_KEY PLANE_LIVE_SECRET_KEY PLANE_DB_PASSWORD PLANE_RABBITMQ_PASSWORD PLANE_STORAGE_ACCESS_KEY PLANE_STORAGE_SECRET_KEY`. Varsayılan portlar 8701/8702/8703. Secret: `openssl rand -hex 24` (yoksa `od`); `APP_KEY`: `base64:` + `openssl rand -base64 32` (T-2 biçimi doğrular). Ayrıştırma `${line#*=}` ile, `source` yok.

Sağlık probları (hooks.sh `app_health`): bookstack `GET /status` 200 · penpot `GET /` 200 · plane `GET /` (yönlendirme izlenir) 200.

Yedek tanımı (servis ve volume adları T-2..T-4'te `config`/`volume ls` ile doğrulanır, aşağıdakiler adaydır):

| App | DB dump (container içinde, parola container ortamından) | Dosya volume'ları |
|---|---|---|
| bookstack | `exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb-dump --single-transaction -u"$MARIADB_USER" "$MARIADB_DATABASE"'` | `config` |
| penpot | `exec -T penpot-postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"'` (yerel soket) | `assets` |
| plane | `exec -T plane-db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"'` | `uploads` (silo verisi) |

DB volume'ları tar'lanmaz (canlı DB tutarsız); DB yalnız dump ile yedeklenir.

## 7. Threat model

Sensitive area: yok (para/kimlik/kişisel veri yok; kimlik bilgileri secret).
- Secret'lar commit'lenmez (`.gitignore`, AC-4/15), mod 600, çıktıda maskelenir. `docker inspect` bunları gösterir (kabul: tek kullanıcılı Mac).
- Yalnız `127.0.0.1`; DB/cache/kuyruk/depolama internal ağda. Aynı Mac'teki yerel kullanıcı ve tarayıcıdan DNS rebinding (Host header koruması yok) riski kabul edilir (§9).
- Varsayılan kimlik bilgisi çıkarılır; BookStack/Plane'de `up` kapıda durur (REQ-15). Penpot'ta kayıt kapalı, ilk kullanıcı elle.
- Pinli sürümler; digest yalnız iki topluluk image'ında.
- Girdi: komut, uygulama adı, port ve `local/.env` satırları izin listesi/aralıkla doğrulanır; hiçbiri shell'e yorumlatılmaz.

## 8. Rollout and rollback

Hedef: CEO'nun Mac'i; `main`'e push CEO onayıyla. Geri alma `git revert`; `down` veriyi silmez. Yedek yalnız manuel `backup`. `local/` kaybında: `local/.env` yoksa `init` yeni secret üretir ve eski DB'ye uymaz (REQ-18 uyarır); çözüm `local/.env` yedeğini geri koymak ya da ilgili volume'ları CEO elle silmek (stack silmez).

## 9. Task list

| # | Görev | Sahip | Bağımlılık | Dosyalar |
|---|---|---|---|---|
| T-1 | `stack` çekirdeği: init, up, down, status, logs, ayrıştırıcı, maskeleyici, port kontrolü (`lsof -nP -iTCP:<p> -sTCP:LISTEN`, kendi container'ı `docker ps --filter publish=<p> --filter label=com.docker.compose.project=selfhost-<app>` ile ayıklanır), health bekleme, çıkış kodları, `STACK_LOCAL_DIR`, `local.example/` | polyglot-engineer | yok | `stack`, `local.example/` |
| T-2 | BookStack compose + `hooks.sh` (health, admin rotasyonu, default-login probu, yedek), tema mount, image tag/digest/arm64 doğrulama | polyglot-engineer | T-1 | `stacks/bookstack/` |
| T-3 | Penpot compose (2.18.6'dan kopya, kopya başlığı, mailpit/mcp/admin-console çıkar) + `hooks.sh` | polyglot-engineer | T-1 | `stacks/penpot/` |
| T-4 | Plane compose (v1.4.3 asset'inden kopya, proxy `127.0.0.1`, gömülü ayarlar, silo digest) + `hooks.sh` (admin-claim probu, kayıt anahtarı araştırması) | polyglot-engineer | T-1 | `stacks/plane/` |
| T-5 | `backup` komutu (önce app image'ında `tar`; alpine yalnız gerekirse) | polyglot-engineer | T-2, T-3, T-4 | `stack` |
| T-6 | `tests/run.sh` (statik AC'ler, BLOCKED kuralı) | polyglot-engineer | T-1..T-5 | `tests/` |
| T-7 | README (kurulum, ilk admin, `local/` kaybı, `local/`'i bulut senkronundan hariç tut, Postgres/MariaDB major bump `up` ile korunmaz: elle dump/restore), `NOTICE`, ADR-0001 (tek sayfa) | tech-comms / software-architect | T-6 | `README.md`, `NOTICE`, `docs/architecture/tasarim/` |
| T-8 | Canlı doğrulama (AC-11..AC-19), RAM ölçümü | qa-engineer | T-7 | rapor |

T-2..T-4 farklı dizinler (çakışma yok); `stack`'e T-1 sonra T-5 dokunur. Yapan doğrulamaz.

## 10. Assumptions and risks

- Docker'ın bu Mac'te çalıştığı doğrulanmadı (BA'nın shell'i yok); yoksa canlı AC'ler BLOCKED.
- Plane ~12 container: ≥ 8 GB Docker belleği gerekebilir (AC-19 ölçer).
- silo: üçüncü taraf MinIO fork'u, lisans/bakım doğrulanmadı; ADR-0004 çıkış tetikleyicileri geçerli.
- Tag-only pin (iki image hariç): aynı tag'in içeriği değişebilir.
- Host header koruması yok: tarayıcıdan DNS rebinding ile loopback servisleri erişilebilir olabilir; kabul, TLS/proxy non-goal.
- Compose'da shell'den gelen `COMPOSE_*` değişkenleri temizlenmez; image'lar compose'a gömülü olduğundan etkisi sınırlı.
- Plane admin-claim bayrağı, kayıt kapatma anahtarı, BookStack admin CLI komutu ve `APP_KEY` biçimi T-2/T-4'te doğrulanır; doğrulanamazsa README'de belgelenir, AC-14 `exit 6` kapısı bu durumda elle yönergeyle sağlanır.
- BookStack sürüm bump'ı temayı sessizce bozabilir (tema kilidi 0002'ye ait, ertelendi).
- Upstream tag'i kaldırırsa `up` çekmede düşer; çözüm elle.
- Yeni dış bağımlılıklar için architecture-board görüşü: `docs/architecture/gorus-0001-sade-2026-11-15.md` (C-1..C-5 bu spec'e işlendi). appsec ve spec-critic ikinci turu bu revizyon üzerinde.
- Açık soru: yok.
