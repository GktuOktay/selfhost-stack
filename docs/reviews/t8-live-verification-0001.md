T-8 live verification, spec-0001-sade (AC-11..AC-19)
Date: 2026-11-15. Verifier: qa-engineer. Production code unchanged.
Environment: Docker Server 29.9.2, aarch64 (arm64 images, no emulation), Docker memory 13368987648 B (~12.4 GiB). Default local/ used (gitignored). Ports 8701-8703 were free before start. No secret values printed.

RESULT: UNPROVEN CRITERIA (no FAIL rows remain). Plane proxy and app_health defects fixed and re-verified live 2026-11-15; remaining items below were not exercised.

Table
| AC | Status | Evidence |
|---|---|---|
| AC-11 | PASS | `./stack init` exit 0, local/.env mode 600. `./stack up bookstack` exit 0 (35 s): "OK bookstack http://127.0.0.1:8701". `curl /status` 200; `curl -sSL /login` 200, body contains "BookStack" (4 hits). `./stack status bookstack` -> "bookstack: healthy ... default-login: no". |
| AC-12 Penpot | PASS | `./stack up penpot` exit 0 (6 min incl. pulls). `curl :8702/` 200, "penpot" 14 hits. status "penpot: healthy / registration: disabled". |
| AC-12 Plane | PASS (re-verified 2026-11-15) | Fix: removed `CERT_ACME_CA: ""` from x-proxy-env (stacks/plane/compose.yaml); Caddyfile default applies when unset (SITE_ADDRESS `:80` is HTTP-only). `python3 -I tests/test_plane_proxy_acme.py` OK; `tests/run.sh` PASS 109 FAIL 0 BLOCKED 1. Live `./stack up plane`: proxy Up, `curl 127.0.0.1:8703/` -> 200. Second defect found and fixed: app_health returned 200 from web before api was ready, so the gate ran early and exit 5 ("/api/instances/ okunamadi", /api/instances/ gave 502); stacks/plane/hooks.sh app_health now also requires /api/instances/ readable. Earlier FAIL text superseded. |
| AC-13 | PASS (partial) | 2nd `up bookstack` exit 0, container IDs identical. `nc -l 127.0.0.1 8701` held, bookstack down: `up bookstack` exit 3, msg "port 8701 dolu (bookstack): BOOKSTACK_PORT değerini local/.env içinde değiştir", 0 containers started. `HEALTH_TIMEOUT=1 ./stack up plane` exit 4. NOT tested: `up all` continuing after one app exits 3 with summary line. |
| AC-14 BookStack | PASS | probe `SELECT COUNT(*) FROM users WHERE email='admin@admin.com'` -> 0 (users total 2). Login POST with BOOKSTACK_ADMIN_EMAIL + local/.env password: 302 -> `/`, then `/` 200 (session valid). Login with admin@admin.com/password: 302 -> /login (rejected). status "default-login: no". Not tested: the `YES (UYARI)` / exit 6 branch (needs a default user planted). |
| AC-14 Plane gate | PARTIAL (unclaimed PASS; claimed NOT tested) | Fresh: `./stack up plane` -> "Plane instance admin talep edilmedi ... /god-mode/", exit 6; `./stack status plane` -> "plane: healthy" + "plane-admin: unclaimed (http://127.0.0.1:8703/god-mode/)". Admin was not claimed (no throwaway admin created), so claimed -> exit 0 is not tested. |
| AC-14 Penpot | PASS (partial) | status "registration: disabled". Not tested: PENPOT_EXTRA_FLAGS filled -> UYARI. |
| AC-15 | PASS | Every secret value in local/.env (12 keys: *PASSWORD*, *SECRET*, APP_KEY, *ACCESS_KEY*) checked with `grep -F` against: status, backup bookstack, `logs` last 200 lines of bookstack/penpot/plane, and the saved up logs: 0 matches each. `init` output (seen live) lists key names only. Plane logs were taken while the proxy crash-looped. |
| AC-16 | PASS | `./stack backup all` ran; modes: backups/ 700, each `<UTC>/` dir 700, all files 600. bookstack: db.sql 53545 B, config.tar 96768 B; penpot: db.sql 119989 B, assets.tar 10240 B; plane: db.sql 469675 B, uploads.tar 52736 B. `tar -tf` exit 0 on all three tars. After `down`, `backup bookstack` exit 2. Note: "plane-minio icinde tar yok/basarisiz; plane-db image'i ile yedekleniyor" (fallback worked). `ps` password check is static only: hooks use `sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" ...'` / `PGPASSWORD="$POSTGRES_PASSWORD"` inside exec (hooks.sh bookstack:84, penpot:38, plane:69); not observed with a live `ps` during a dump. |
| AC-17 | PASS | Created book "qa-t8-marker" via web (302 to /books/qa-t8-marker). `./stack down bookstack` exit 0, `up bookstack` exit 0, book list shows marker (4 hits). `grep -nE 'down +-v|volume +(rm|prune)|system +prune' stack stacks/*/hooks.sh` -> no output. Volumes after final `down all`: 14 selfhost volumes kept. |
| AC-18 | PASS | compose: `APP_THEME: selfhost-dashboard`; bind mount target /config/www/themes/selfhost-dashboard, `read_only: true`; `docker inspect` -> "rw=false". `git diff --stat stacks/bookstack/theme` empty. |
| AC-19 | PASS (Plane partial) | `docker stats --no-stream`, summed per app (all up, idle, right after start): bookstack 175 MiB (2 containers); penpot 2883 MiB (5 containers); plane 1493 MiB (11 containers, proxy not running, so slightly low; api/workers were still warming up). Sum 4551 MiB. Docker memory limit here 12.4 GiB. The "Plane >= 8 GB recommended" claim is NOT confirmed or refuted: idle Plane used ~1.5 GiB. Absolute numbers are local Docker, relative evidence only; the Plane figure must be re-measured after the proxy fix. |
| AC-19 Plane re-measure | PASS | `docker stats --no-stream`, 30 s after up, all 12 containers incl. proxy, unclaimed idle: ~1448 MiB (worker 640, beat 147, api 146, live 144, mq 126, minio 87, space 72, db 56, proxy 16, redis 9, web 5, admin 5). Replaces the 1493 MiB figure (proxy was down then). Still idle, no workspace; the 8 GB recommendation is not confirmed. |
| shellcheck (spec ref) | BLOCKED | `which shellcheck` -> not found. |

Other observations
- Superseded: earlier Plane `up` timeout (600 s, exit 5) came from the proxy crash loop and early app_health; fixed. `status` always exits 0 (unhealthy included), not changed.
- Penpot RAM (~2.9 GiB) is the largest, not Plane.
- `./stack down all` exit 0, 0 selfhost containers left. local/ and volumes kept. Other projects' containers (instaanalytic-*) untouched.
- Repro test (only repo write): tests/test_plane_proxy_acme.py. Failed before the fix (CERT_ACME_CA empty broke Caddyfile acme_ca); now `python3 -I tests/test_plane_proxy_acme.py` passes.

Unproven criteria (open)
- shellcheck: BLOCKED (not installed); spec shellcheck check not run.
- AC-14 Plane claimed state: admin deliberately not claimed, so `claimed` status and exit 0 after claim are untested (only unclaimed -> exit 6 proven).
- AC-13: `up all` where an app exits 3 (port busy) with 3 summary lines and exit 3 not exercised. Verified instead: `up all` with Plane unclaimed -> OK bookstack, OK penpot, `FAIL plane kod 6`, exit 6, ports 8701/8702/8703 all 200, `status all` healthy x3 (spec REQ-20 order/first-failure rule met for this case).
- AC-14: BookStack `default-login: YES (UYARI)` / exit 6 branch and Penpot filled PENPOT_EXTRA_FLAGS warning not exercised.
- AC-16: live `ps` check for DB passwords during dump not observed (static read only).
- AC-19: idle-only RAM figures on local Docker (relative evidence); Plane 8 GB recommendation neither confirmed nor refuted.
- No test was broken in a temporary copy (live verification).

Final re-run 2026-11-15: `./stack up plane` exit 6 (unclaimed gate, ~38 s), `status plane` healthy + unclaimed, `curl :8703/` 200, `backup plane` exit 0 (backups 700, dir 700, db.sql/uploads.tar 600, 469674/39936 B, tar -tf 0), `up all` exit 6, `/bin/bash tests/run.sh` PASS 109 FAIL 0 BLOCKED 1, `down all` exit 0, 0 selfhost containers, local/ and volumes kept.
