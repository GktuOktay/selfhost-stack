# ADR-0001: Proje ve volume adları, `local/` düzeni

- Durum: Kabul (spec 0001 imzalı)
- Tarih: 2026-11-15
- Kaynak: `docs/spec-0001-sade.md` §5, §6, §8; `stacks/*/compose.yaml`; `local.example/.env.example`

## Bağlam

Her uygulamanın verisi Docker volume'larında durur. Volume adı compose proje adından türer. Proje adı değişirse Docker aynı adda bir veri bulamaz ve boş volume açar. Bu yüzden ad, verinin kimliğidir.

## Karar

1. Compose proje adı `selfhost-<app>` olur; `<app>` ∈ `bookstack`, `penpot`, `plane`. `./stack` her çağrıda şunu kullanır: `docker compose -p selfhost-<app> -f stacks/<app>/compose.yaml --env-file $LOCAL/.env`.
2. Volume adları `selfhost-<app>_<volume>` biçimindedir. Compose dosyalarındaki volume'lar:

   | App | Volume'lar |
   |---|---|
   | bookstack | `config`, `db` |
   | penpot | `penpot_postgres_v15`, `penpot_assets` |
   | plane | `pgdata`, `redisdata`, `uploads`, `logs_api`, `logs_worker`, `logs_beat-worker`, `logs_migrator`, `rabbitmq_data`, `proxy_config`, `proxy_data` |

3. Makineye özel her şey `local/` altında durur (ya da `STACK_LOCAL_DIR` ile verilen mutlak dizinde). `local/` gitignored'dır.

   | Yol | Git | İçerik |
   |---|---|---|
   | `local.example/.env.example` | evet | Anahtarlar; secret'lar `__GENERATE__` |
   | `local/.env` (mod 600) | hayır | Portlar ve gerçek secret değerleri |
   | `local/backups/<app>/<UTC>/` (mod 700) | hayır | `backup` çıktıları |

4. Env'de yalnız `HEALTH_TIMEOUT` ve `STACK_LOCAL_DIR` kabul edilir.

## Sonuçlar

- Proje adı ya da volume adı sonradan değiştirilirse mevcut veri bağlanmaz. Bu ad değişikliği bir göç işidir ve ayrı karar ister.
- `down` yalnız container ve ağları kaldırır; volume'lara dokunmaz.
- `local/.env` yokken `selfhost-<app>_*` volume'ları varsa `init` uyarır: yeni secret'lar eski veriyle uyuşmaz.
- `local/` kaybında çözüm, `local/.env` yedeğini geri koymak ya da ilgili volume'ları elle silmektir.
- Compose dosyaları `${VAR:?}` ile secret'ları `local/.env`'den alır; uygulamaya özel gizli olmayan ayarlar compose içine gömülüdür ve git'tedir.
