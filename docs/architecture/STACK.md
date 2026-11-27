# Standard stack record: selfhost-stack

Güncel durum: BookStack ve Plane kaldırıldı (yerine TabTab); yalnız Penpot çalışır. Satırlar o servislere ait kayıtlar çıkarılmış hâlidir, eski kararlar `docs/` içindeki spec ve ADR'lerde tarihçe olarak durur.

Statüler: adopt / trial / assess / retire. Kayıt dışı teknoloji "assess" olarak girer. Kaynak görüşler: `gorus-0001-selfhost-stack-2026-11-09.md`, `gorus-0002-bookstack-dashboard-2026-11-09.md`, `gorus-0002-bookstack-dashboard-2026-11-09-tur2.md`, `gorus-0002-bookstack-dashboard-2026-11-09-tur3.md`.

| Technology | Status | Rationale | Date | ADR |
|---|---|---|---|---|
| Docker Engine + Compose v2 (≥ 2.24.4 yalnız r2 overlay modeli için; sade spec 0001'de `!override` yok, tek `compose.yaml` + `--env-file`) | adopt | Tercih edilen stack'in parçası (local Docker). Sade spec: proje adı `selfhost-<app>` ve volume adları veri kimliği, ADR-0001 kapsamı bu iki konuya daralır (gerekli, yazılmadı) | 2026-11-15 | ADR-0001 (gerekli, yazılmadı) |
| bash 3.2 uyumlu CLI (`stack`) | trial | Ek runtime yok. Koşul: `/bin/bash` 3.2 test kapısı, `COMPOSE_*` temizliği. Yeniden değerlendirme tetikleyicisi görüşte A-13 | 2026-11-09 | ADR-0005 (önerilir) |
| shellcheck (geliştirme kapısı G-1) | trial | Bash hata disiplini için statik kapı. bash 3.2 özelliklerini ayırt etmez, test kapısıyla birlikte kullanılır | 2026-11-09 | - |
| jq (çözümlenmiş compose okuma) | assess | Sade spec 0001'de yok (grep/cut). AC-5'in servis başına `ports` denetimi grep ile kırılgan; jq gerekirse board'a yeniden gelir | 2026-11-15 | - |
| Penpot 2.18.6 (frontend, backend, exporter) | trial | CEO'nun seçtiği uygulama, MPL-2.0. Upstream compose kopyası; mailpit/mcp çıkarılır (kriter yok). arm64: tüm image'lar manifest'te var, canlı çalıştırma T-8'de (docs/reviews/t8-live-verification-0001.md) | 2026-11-15 | - |
| PostgreSQL (Penpot `15.x`) | trial | Upstream gereksinimi. Tam patch tag. Major bump manuel dump/restore | 2026-11-15 | - |
| Valkey (Penpot `8.1.x`) | trial | Upstream gereksinimi, geçici veri, yedek dışı | 2026-11-15 | - |
| alpine (yedek tar yardımcı image'ı, `3.<minor>`) | assess | CONDITIONAL: alternatif "yeni image yok" (zaten çekilmiş app image'larında `--entrypoint tar`) T-5'te denenir; tüm volume'lar kapsanırsa alpine düşer. Kalırsa tam patch tag | 2026-11-15 | - |
