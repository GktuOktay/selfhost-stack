# Standard stack record: selfhost-stack

Statüler: adopt / trial / assess / retire. Kayıt dışı teknoloji "assess" olarak girer. Kaynak görüşler: `gorus-0001-selfhost-stack-2026-11-09.md`, `gorus-0002-bookstack-dashboard-2026-11-09.md`, `gorus-0002-bookstack-dashboard-2026-11-09-tur2.md`, `gorus-0002-bookstack-dashboard-2026-11-09-tur3.md`.

| Technology | Status | Rationale | Date | ADR |
|---|---|---|---|---|
| Docker Engine + Compose v2 (≥ 2.24.4, `!override`/`!reset`) | adopt | Tercih edilen stack'in parçası (local Docker). Yerel `-f` merge mekanizması katman modelini ek araçsız taşıyor | 2026-11-09 | ADR-0001 (gerekli, yazılmadı) |
| bash 3.2 uyumlu CLI (`stack`) | trial | Ek runtime yok. Koşul: `/bin/bash` 3.2 test kapısı, `COMPOSE_*` temizliği. Yeniden değerlendirme tetikleyicisi görüşte A-13 | 2026-11-09 | ADR-0005 (önerilir) |
| shellcheck (geliştirme kapısı G-1) | trial | Bash hata disiplini için statik kapı. bash 3.2 özelliklerini ayırt etmez, test kapısıyla birlikte kullanılır | 2026-11-09 | - |
| jq (çözümlenmiş compose okuma) | assess | Spec'te yok, guard'lar için gerekli görünüyor. Ön koşul mu container mı kararı bekliyor (A-07) | 2026-11-09 | - |
| BookStack via `lscr.io/linuxserver/bookstack` | assess | Resmi image yok varsayımı (F-1) doğrulanmadı. Bakım ve güvenlik geçmişi eksik | 2026-11-09 | - |
| MariaDB (Docker Official Image) | assess | BookStack DB. LTS seçimi ve major upgrade yolu tanımsız (A-02) | 2026-11-09 | ADR-0002 (gerekli) |
| Penpot (frontend, backend, exporter) | assess | CEO'nun seçtiği uygulama, MPL-2.0. Upstream compose vendored | 2026-11-09 | ADR-0001 |
| Plane Community Edition | assess | CEO'nun seçtiği uygulama, AGPL-3.0 (dahili kullanım). ~12 container | 2026-11-09 | ADR-0001 |
| PostgreSQL (Penpot, Plane) | assess | Upstream gereksinimi. Major değişimi `up` ile yapılmaz (A-02) | 2026-11-09 | ADR-0002 (gerekli) |
| Valkey / Redis (Penpot, Plane) | assess | Upstream gereksinimi, geçici veri, yedek dışı | 2026-11-09 | - |
| RabbitMQ (Plane) | assess | Upstream gereksinimi, yedek dışı | 2026-11-09 | - |
| MinIO (Plane object storage) | assess | Risk: topluluk dağıtımı ve bakımı 2025'te kısıtlandı (doğrulanmadı). Retire adayı, çıkış tetikleyicisi ADR'de yazılmalı (A-11) | 2026-11-09 | ADR-0004 (gerekli) |
| alpine (yedek tar yardımcı image'ı) | assess | Yalnızca read-only tar. Alternatif: yeni image eklememek | 2026-11-09 | ADR-0003 (gerekli, yedek formatı) |
| CPython stdlib via `python:3.14.<patch>-alpine3.24@sha256` (dashfeed sidecar, spec 0002 Faz 2a) | assess | Plane token'ını BookStack'ten ayırmak için (S2). pip yok. Rationale tablosu tam, güvenlik kanıtı eksik (D-20). Board tur 3: minor 3.14 APPROVE (PEP 745; 3.13 yalnız güvenlik aşamasında, PEP 719). 3.15 alternatif satırı istendi (K3-5). Trial'a geçiş: T-0a2 temiz (K2-4) + Faz 2a imzası. T-0a2 tamamlanmazsa REJECT | 2026-11-09 | - |
| Plane public API v1 (salt okuma, `X-API-Key`, `work-items`) | assess | Dashboard verisi. Docs verified (D-12, D-13): 60/dk/anahtar, self-host'ta `API_KEY_RATE_LIMIT` ile ayarlanabilir, sunucu tarafı filtre yok (D-13c), anahtar sahibinin yetkisiyle çalışır. Pinli v1.4.3 davranışı T-0c + CB-28. Uyum `PLANE_COMPAT` anahtar kümeleri | 2026-11-09 | - |
| BookStack visual theme override (B-copy: birebir kopya + tam satır `@include`, sha256 + diff) | trial | Ana sayfa ve raf dashboard'u. Board tur 2: APPROVE. Sapma CB-8 ile mekanik yakalanır (ham bayt diff, arm64 + amd64). Veri erişimi `ACCESS_ALLOWLIST` ile (K2-1 karşılandı, tur 3). Tema kilidi C-14: pin ≠ `UPSTREAM` ya da `VIEW` yoksa tema kapanır (dar tanım, K3-1). Hash etiketi yok, yayılma opcache ile (D-9), opcache ayarı bump'ta izlenir (K3-2). Kullanıma giriş: Faz 1 imzası + ADR-0007 r3 kabulü (K2-2) | 2026-11-09 | ADR-0007 (Proposed) |
| BookStack logical theme (`functions.php`, view enjeksiyonu, view block kaydı) | assess | v1'de kullanılmaz (appsec S-06). Enjeksiyon yalnız bununla mümkün (D-17 verified, R-b). Yeniden açma: ADR-0007 tetikleyici #2, #3 | 2026-11-09 | ADR-0007 (Proposed) |
| Docker cross-project `internal` ağ (`selfhost-dashfeed`) | assess | Stack izolasyonuna tek istisna: yalnız dashfeed + Plane proxy, diğer her projede boş küme (K2-5, spec r4 C-12 ve CB-13 (d) ile karşılandı). Silinmez (0001 r3 AC-10), `Internal`/`Driver`/etiket doğrulanır. Trial'a geçiş: T-0c (D-15, D-16b, D-22) + Faz 2 imzası | 2026-11-09 | ADR-0006 (Proposed) |
| `docker:<tag>-dind` (yalnız test, privileged, spec 0002 §11) | assess | Linux Engine davranışını VM'siz ölçmek için (CEO cevabı, spec 0002 §1 madde 4). Stack'in parçası değil. Rationale spec 0002 §6.3'te (K2-7), pin yeri `tests/versions.env` (G-img dışı). Faz 1'de kullanılıyor (CB-9, T-5): lisans/bakım doğrulaması ve tag + digest T-5'ten önce (K3-4). Lisans doğrulanmadı | 2026-11-09 | - |
