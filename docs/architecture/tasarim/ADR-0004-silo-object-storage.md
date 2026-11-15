# ADR-0004: Plane object storage, `pgsty/silo` risk kabulü (stub)

- Status: Proposed (CEO imzası spec 0001 ile birlikte; spec §0 madde 5)
- Date: 2026-11-15
- Related: `docs/spec-0001-sade.md`, `docs/architecture/gorus-0001-sade-2026-11-15.md` (C-3), `docs/reviews/scout-upstream.md` (F-7)

## Context
Plane v1.4.3 upstream compose, S3 uyumlu depolama için `pgsty/silo:RELEASE.2026-09-16T00-00-00Z` (MinIO fork'u) kullanıyor. MinIO topluluk image dağıtımı durdu; silo üçüncü taraf bir fork ve kullanıcı dosyalarının yolunda. Lisans (AGPL-3.0 varsayımı), bakım ve güvenlik geçmişi doğrulanmadı (scout F-7, zayıf kaynak).

## Decision
Upstream'in seçtiği silo kabul edilir, şu koşullarla:
- Yalnız Plane stack'inde; internal ağda, host'a port açılmaz.
- Tam tag + `@sha256` digest ile pinlenir.
- Uygulama loopback dışına açılmaz (non-goal: LAN/TLS).
- Dosya verisi `./stack backup plane` ile `uploads` volume tar'ı olarak yedeklenir.

## Alternatives
1. Eski MinIO tag'i: kaynak/dağıtım belirsiz, CVE-2025-62506 topluluk sürümünde yamasız (zayıf kaynak).
2. SeaweedFS/Garage: Plane v1.4.3 desteği doğrulanmadı.
3. Plane'siz kurulum: CEO'nun üç uygulama kararına aykırı.

## Consequences
Depolama değişimi veri göçü demektir (pahalı). Lisans ve bakım doğrulaması scout'a açık soru; hukuki yorum gerekirse avukat.

## Exit triggers
silo için duyurulan CVE · Plane depolama bileşenini değiştirir · LAN/uzaktan erişim açılır · bakım durur (son sürüm > 12 ay).
