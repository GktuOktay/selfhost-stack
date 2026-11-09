Scout report: spec §6.4 F-1..F-9 upstream fact verification | Date: 2026-11-09 | Requested by: T-0 (selfhost-stack/docs/spec.md)

Note: all pages were read via WebFetch, whose summarizer is a small model. Quotes below are the summarizer's output, not byte-exact. Nothing was installed, downloaded or run. No page contained instructions aimed at the agent.

## Criteria
1. Each F-n claim is checked against a current official source (docs, upstream repo, registry API), accessed 2026-11-09.
2. Verdict is one of confirmed / partly / refuted / unknown. A single secondary source counts as weak evidence.

## Summary table

| ID | Claim | Verdict | Evidence |
|---|---|---|---|
| F-1 | BookStack ships no official image; docs list community images (LinuxServer.io, solidnerd) | Confirmed | BookStack install page lists no official image and calls them "Community docker setups" (1) |
| F-2 | linuxserver/bookstack env, port 80, /config, multi-arch | Confirmed, with note | `APP_URL`, `APP_KEY`, `DB_HOST/DB_PORT/DB_USERNAME/DB_PASSWORD/DB_DATABASE`, port 80, `/config`, amd64+arm64 (2). The `base64:` + 32 byte format is NOT stated on the page; it says generate with `docker run -it --rm --entrypoint /bin/bash lscr.io/linuxserver/bookstack:latest appkey`. Page also lists `PUID/PGID/TZ`, optional `QUEUE_CONNECTION`. DB_PASSWORD min 4 chars. No healthcheck documented. |
| F-3 | Default login admin@admin.com / password | Confirmed (2)(1) | |
| F-3b | `/status` returns DB/cache/session JSON | Confirmed, spec detail missing | Public route in `routes/web.php` to `StatusController::show` (3). Returns `{"database": true, "cache": true, "session": true}`, HTTP 200 only if all pass, HTTP 500 otherwise (4). Install page says error >= 400 (1). `curl -fsS` works as the spec §228 uses it. |
| F-4 | Penpot compose services: frontend, backend, exporter, postgres 15, valkey, mailcatch | Partly refuted | Current compose (5) has 8 services: penpot-frontend, penpot-backend, **penpot-admin-console (new)**, **penpot-mcp (new)**, penpot-exporter, penpot-postgres (`postgres:15`), penpot-valkey (`valkey/valkey:8.1`), **penpot-mailpit (`axllent/mailpit:v1`, not "mailcatch")**. Mailpit publishes 8025 to host. |
| F-4b | Frontend `9001:8080` | Confirmed (5) | Internal port 8080, host 9001. |
| F-4c | Image tag `${PENPOT_VERSION:-latest}` | Refuted | Default is `${PENPOT_VERSION:-2.18}` (all penpotapp/* images) (5). The help page says "latest" (6): doc and file disagree; the file is newer. |
| F-5 | PENPOT_PUBLIC_URI, PENPOT_SECRET_KEY | Confirmed (7) | |
| F-5b | Flags `disable-registration`, `disable-email-verification`, `disable-secure-session-cookies`, `enable-login-with-password` | Confirmed (7) | The compose default sets `disable-email-verification enable-smtp enable-prepl-server disable-secure-session-cookies enable-mcp` (5). Note `enable-mcp` is on by default: security review item. |
| F-5c | `python3 manage.py create-profile` | Confirmed (6) | Command: `docker exec -ti penpot-penpot-backend-1 python3 manage.py create-profile` (+ `--skip-tutorial --skip-walkthrough`). Container name varies with project name; use `docker compose exec` instead of a fixed name. Requires `enable-prepl-server` flag (present in default compose). |
| F-5d | Readiness `/readyz` | Unknown (weak) | Only mention: config page's backend draining section, returns `503 OFFLINE` when drained (7). No health endpoint documented in the install page (6). Not found in `backend/src/app/http.clj` routes (8) (may live in mgmt/debug namespaces). Backend port (6060 assumed) not verified. Spec §230 must stay "to be measured" or use frontend `/` / postgres healthcheck. Compose file defines healthchecks only for postgres (`pg_isready`) and valkey (`valkey-cli ping`) (5). |
| F-5e | Telemetry opt-out (spec asks T-0 for telemetry flags) | Found | Compose sets `PENPOT_TELEMETRY_ENABLED: "true"` by default (5). Config page documents only opt-in flag `enable-telemetries` and no opt-out (7). Env var `PENPOT_TELEMETRY_ENABLED=false` is used by third-party templates (weak, 9). Use the env var, verify in trial. |
| F-6 | Plane `setup.sh` as release asset | Confirmed (10)(11) | `curl -fsSL -o setup.sh https://github.com/makeplane/plane/releases/latest/download/setup.sh`. Release v1.4.3 assets: docker-compose.yml, restore-airgapped.sh, restore.sh, setup.sh, swarm.sh, variables.env (11). |
| F-6b | Env: APP_RELEASE, APP_DOMAIN, WEB_URL, CORS_ALLOWED_ORIGINS, LISTEN_HTTP_PORT, LISTEN_HTTPS_PORT, SECRET_KEY, LIVE_SERVER_SECRET_KEY, POSTGRES_PASSWORD, RABBITMQ_*, AWS_ACCESS_KEY_ID/SECRET | Confirmed (12) | From v1.4.3 `variables.env` asset: `APP_RELEASE=stable`, `APP_DOMAIN=localhost`, ports 80/443, `SECRET_KEY` and `LIVE_SERVER_SECRET_KEY` = `change-this-key-on-deployment`, `POSTGRES_PASSWORD=plane`, `RABBITMQ_USER/PASSWORD=plane`, `AWS_ACCESS_KEY_ID=access-key`, `AWS_SECRET_ACCESS_KEY=secret-key`, `USE_MINIO=1`. Also `SITE_ADDRESS`, `TRUSTED_PROXIES=0.0.0.0/0`. |
| F-6c | `DOCKERHUB_USER`, `PULL_POLICY`, `CUSTOM_BUILD` | Refuted (for v1.4.3 variables.env) | Absent from release asset (12) and from preview-branch file. May be exported by setup.sh only; not verified (setup.sh not read). Remove from spec or mark unknown. |
| F-6d | Docs say file is `variables.env` | Partly refuted | Developer docs say setup.sh creates `plane-app/` with `docker-compose.yaml` and `plane.env` (10). Release assets are named `docker-compose.yml` + `variables.env` (11). Naming differs between the setup.sh path and raw assets. Spec must pick one path. |
| F-6e | Default secrets in variables.env | Confirmed (12) | Also AWS keys default to `access-key`/`secret-key` in the release asset (the preview-branch file leaves them empty and says install.sh generates keys (13)): sources differ. |
| F-6f | Instance admin at `/god-mode`, created by first visitor | Partly confirmed | Official docs: `/god-mode` is for Instance admin; on new install whoever sets up the instance creates admin email+password on the "secure your instance" screen; admin can skip God Mode and go to workspace setup (14). Via search summary; page not fetched in full. "First visitor" = weak. Flow changed around v0.14. |
| F-7 | MinIO restricted community Docker image distribution (2025); pinned image sustainability is a risk | Confirmed, plus new fact | Search summary: community images no longer on Docker Hub/Quay, source-only distribution; GitHub README "no longer maintained"; sources conflict on dates (15). **Plane v1 compose now uses `docker.io/pgsty/silo:RELEASE.2026-09-16T00-00-00Z` (a MinIO fork) as `plane-minio`**, fixed tag, not tied to APP_RELEASE (13). Silo tag has amd64+arm64 (16). Weak: dates are single/conflicting sources; Silo is a third-party fork (maintenance and security not assessed). Chainguard reports CVE-2025-62506 unpatched in community edition (15, weak). |
| F-8 | `!reset`/`!override` tags, Compose >= 2.24.4 | Tags confirmed, version unknown | Official merge page documents `!reset` and `!override` but states no version (17). Only a Japanese mirror of the docs mentions 2.24.4 (weak) (18). The v2.24.4 GitHub release page text does not mention them (19). Latest Compose release: v5.7.0, 2026-11-02 (20). Recommendation: keep "Compose >= 2.24.4" as unverified; the preflight should probe by running `docker compose config` on a tiny file. Known bug: tags ignored when `extends` is combined with YAML anchors (18). |
| F-8b | `ports` merge by append | Confirmed (17) | Merged by unique key {ip, target, published, protocol}; new entries appended. |
| F-8c | `--env-file` repeatable, later wins; shell beats env-file | Partly | Shell value beats `.env` file: confirmed (21). Multiple `--env-file` ordering: NOT documented on fetched pages; the `env_file` attribute (different thing) states "evaluated in order and can override values set in previous files" (22). Treat as unknown, test in AC. |
| F-9 | Penpot and Plane images publish arm64 | Confirmed for tested tags | Docker Hub API: penpotapp/frontend 2.18, 2.18.3-2.18.6 amd64+arm64 (23). makeplane/plane-backend v1.4.3 and plane-frontend v1.4.3 amd64+arm64, but **v1.4.3-rc2 amd64 only** (24)(25). Other penpot/plane images (backend, exporter, admin-console, mcp, proxy, live, space, admin) not individually checked; pgsty/silo amd64+arm64 (16). Plane docs list an "Install (arm64)" setup option and AArch64 prerequisite (10). |

## Current stable tags (for versions.env, T-0 item)

| Product | Latest stable | Date | Source |
|---|---|---|---|
| Penpot | 2.18.6 (compose default tag 2.18) | 2026-11-04 | (26)(5) |
| Plane | v1.4.3 (v1.4.3-rc1/rc2 are prereleases) | 2026-10-28 | (11) |
| BookStack | v26.09.2 | 2026-10-20 | (27) |
| linuxserver/bookstack | `latest`; page changelog top entry 28.10.26 | | (2) |
| Plane MinIO substitute | pgsty/silo `RELEASE.2026-09-16T00-00-00Z` | 2026-09-16 | (13)(16) |
| Postgres / cache in Plane | `postgres:15.7-alpine`, `valkey/valkey:7.2.11-alpine`, `rabbitmq:3.13.6-management-alpine` | | (13) |

Spec note: the Plane compose in the preview branch was the file read for services (13). The release v1.4.3 compose asset redirect was not read (signed URL, unnecessary); verify equality of tags before pinning. Plane compose defines no healthchecks (13): spec health checks for Plane must use HTTP probes via proxy or be defined in an override.

## Other findings worth folding into the spec
- Plane has no telemetry variables in the compose file (13); a telemetry flag for Plane was not found (unknown).
- Penpot `PENPOT_SECRET_KEY` compose default `change-this-insecure-key`, postgres password `penpot` (5): the stack must override.
- Penpot compose publishes mailpit on host 8025 (5): must be removed/!reset on a shared host.
- Penpot compose backend/frontend etc. have `restart: always`; frontend only publishes 9001 (5).
- Plane proxy publishes 80/443 in `mode: host` (13): needs `!override` to remap ports.

## Recommendation
USE this report as input to the spec revision (business-analyst). Do not treat F-4, F-5d, F-6c, F-6d, F-8 version, F-8c as settled.

## Risks
- Several facts rely on a summarizer reading pages; the key numbers (ports, tags, architectures, endpoints) came from machine-readable sources (raw files, GitHub and Docker Hub APIs) and are stronger than the doc-page claims.
- Plane's MinIO is now a third-party fork (pgsty/silo): maintenance, license, security not assessed.
- Penpot compose default (`2.18`, `enable-mcp`, `enable-prepl-server`, telemetry true) changes quickly; pin tags.

## Not verified
- Penpot `/readyz` path, backend port, and whether it is reachable without the proxy.
- Plane `DOCKERHUB_USER`, `PULL_POLICY`, `CUSTOM_BUILD` (setup.sh not read).
- Compose minimum version for `!override`/`!reset` from an official source.
- Multiple `--env-file` ordering.
- arm64 for every Penpot/Plane image other than those listed above.
- Penpot marker table names (spec T-0 mentions "marker tablo adları") and any BookStack/Plane marker tables: not addressed in this pass.
- Plane docs fetched via WebSearch summary for /god-mode, not full page.
- Whether Plane has a telemetry opt-out.

## Trial proposal (CEO approval needed)
Isolated Docker host (arm64 Mac and amd64 Linux): run each compose once, measure `curl` status of BookStack `/status`, Penpot backend `/readyz` and `/` on 9001, `docker compose version` against a 3-line `!override` test file, and a two `--env-file` precedence test. Duration about 1 hour. Done by another unit.

## Sources (all accessed 2026-11-09)
1. https://www.bookstackapp.com/docs/admin/installation/
2. https://docs.linuxserver.io/images/docker-bookstack/
3. https://raw.githubusercontent.com/BookStackApp/BookStack/development/routes/web.php
4. https://raw.githubusercontent.com/BookStackApp/BookStack/development/app/Settings/StatusController.php
5. https://raw.githubusercontent.com/penpot/penpot/develop/docker/images/docker-compose.yaml
6. https://help.penpot.app/technical-guide/getting-started/docker/
7. https://help.penpot.app/technical-guide/configuration/
8. https://raw.githubusercontent.com/penpot/penpot/develop/backend/src/app/http.clj
9. Web search "Penpot readyz telemetry" (third-party compose templates, weak)
10. https://developers.plane.so/self-hosting/methods/docker-compose
11. https://api.github.com/repos/makeplane/plane/releases?per_page=3
12. https://github.com/makeplane/plane/releases/download/v1.4.3/variables.env (redirect to release-assets.githubusercontent.com)
13. https://raw.githubusercontent.com/makeplane/plane/preview/deployments/cli/community/docker-compose.yml and .../variables.env
14. https://docs.plane.so/self-hosting/govern/instance-admin (via web search summary)
15. Web search "MinIO community edition docker images": https://github.com/minio/MinIO, https://www.chainguard.dev/unchained/secure-and-free-minio-chainguard-containers, https://coolify.io/docs/services/minio-community-edition, https://www.besthub.dev/articles/why-minio-dropped-official-docker-images-and-what-it-means-for-users-7d88d2c3bfe4 (secondary)
16. https://hub.docker.com/v2/repositories/pgsty/silo/tags/?page_size=5&name=RELEASE.2026-09
17. https://docs.docker.com/reference/compose-file/merge/
18. Web search on !override/!reset: https://matsuand.github.io/docker.docs-ja/reference/compose-file/merge , https://www.github.com/docker/compose/issues/11706
19. https://github.com/docker/compose/releases/tag/v2.24.4
20. https://api.github.com/repos/docker/compose/releases/latest
21. https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/
22. https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/
23. https://hub.docker.com/v2/repositories/penpotapp/frontend/tags/?page_size=5&name=2.18
24. https://hub.docker.com/v2/repositories/makeplane/plane-backend/tags/?page_size=5&name=v1.4.3
25. https://hub.docker.com/v2/repositories/makeplane/plane-frontend/tags/?page_size=3&name=v1.4.3
26. https://api.github.com/repos/penpot/penpot/releases/latest
27. https://api.github.com/repos/BookStackApp/BookStack/releases/latest
