# T-0b: container measurements for spec 0002

Date: 2026-11-09 | Unit: devops-sre | Approval: CEO approved this measurement run | Status: DONE (with listed limits)

## 0. Setup and limits

- Host: macOS, Docker Desktop, Engine 29.9.2 (API 1.56), VM kernel 7.0.14-linuxkit, **arm64**. Not a real Linux host.
- Images (all already local or pulled, none changed):
  - `lscr.io/linuxserver/bookstack:v26.09.2-ls295` = `sha256:29ca3f94...` index digest `lscr.io/linuxserver/bookstack@sha256:33f61a72d9aaa021f7e687987b9fcb992673d9ca3fc08f63f5ddaddf59e94efc`. PHP 8.5.12.
  - `lscr.io/linuxserver/mariadb:11.8.9-r0-ls239` = `lscr.io/linuxserver/mariadb@sha256:7b4b9904c151bc50caf2ec9c5bc2213ceedc82c30eaf9ed2b0d47492ebffbe08`.
  - `python:3.13-alpine3.24` (pulled by me; spec does not name an X.Y.Z tag yet) = `python@sha256:1e1f6334529d1fb26a2ef619d7cffb30a7c7d7cc1cc7338ebee283a58d1aeaca`, Python 3.13.18, Alpine 3.24.4. First pull timed out on the registry, second succeeded.
- Resources: only `t0b-` names (`t0b-db`, `t0b-app`, networks `t0b-net`, `t0b-dashfeed`, volumes `t0b-config`, `t0b-dbdata`, `t0b-snap`, plus `--rm` helpers `t0b-cat*`, `t0b-p1..4`, `t0b-col*`, `t0b-snapinit`, `t0b-pyv`). One host port, random, `127.0.0.1:50470->80` only. Ports 8701-8703 untouched. No prune.
- Secrets: DB passwords and APP_KEY were random throwaway values in a scratch file (deleted). No value appears here. The API token used for shelf fixtures was a throwaway token of the throwaway BookStack (deleted with the volume). No Plane token or Plane access.
- Theme used for the test was a measurement theme (real `home/default` and `shelves/show` copies plus one `@include` line each, and measurement partials `selfhost/home.blade.php`, `selfhost/shelf.blade.php`). It is not the product theme. Raw outputs were kept in the agent scratchpad and are quoted below.
- Not tested: a real Linux host, amd64, the product theme, CB-7(a) `touch` failure inside the container (only `RW=false` shown), Plane in any form.

## 1. Results summary

| D | Result | Changes spec? |
|---|---|---|
| D-1b | PASS. `@include('selfhost.x')` resolves to the theme partial. Parent variables pass. | text only |
| D-3 | PASS with noise. Nested read-only bind inside `/config` volume works at first start. Init prints chown errors every start. | CB wording |
| D-3b | PASS. `--entrypoint cat` works. `VIEW_ROOT=/app/www/resources/views`. | fill value |
| D-7 | PASS. Container env reaches `env()`, `getenv()`, `$_SERVER`. Fallback `/dashcards` not needed. **`APP_URL` must be set.** | yes (small) |
| D-9 | `opcache.validate_timestamps=1`, `revalidate_freq=2`. Edits show without restart in 2-4 s. | yes (design option) |
| D-10 | Tag relation is already loaded (0 extra queries). Tag order = edit form order = id order. `order` column is always 0. | yes (small) |
| D-15 | Partly measured. Internal net and Desktop vs Linux-like gateway behaviour measured. Real Linux not available. | note |
| D-18 | PASS. No `open_basedir`. php-fpm user `abc`. `/dashfeed` and `/dashcards` readable. | no |
| D-19 | PASS. All 8 probed URLs 404, even logged in. | no |
| D-22 (bonus) | CLI refuses a second network with the same name on 29.9.2. | no |

## 2. Evidence per D-n

### D-3b: `cat` entrypoint and views root

```
docker run --rm --name t0b-cat --network none --entrypoint cat lscr.io/linuxserver/bookstack:v26.09.2-ls295 /app/www/resources/views/home/default.blade.php | sha256sum
566ef9ce18437aeea4e50d6a8e670aa2a86da4de9467ddfc17caf49c1db9a33c
... shelves/show.blade.php
c9b32a3fbec368c1f449f4553db73fc1c969bd6f9d7a55b56b05a02386e9ed7a
```
- `VIEW_ROOT=/app/www/resources/views` (listing shows `home`, `shelves`, `common`, ...). `/app/www/themes -> /config/www/themes` (symlink, as in D-3). `sha256sum` exists in the image too.
- These two hashes are for the `v26.09.2-ls295` image (arm64 manifest). Check on amd64 in CB-8 because the file comes from the app tarball, but the image layer is arch specific: not measured.
- `home/default.blade.php` content matches D-4 (no lists, 3 `common.view-blocks` columns).

### D-3: nested bind mount at first start

```
docker run -d --name t0b-app ... -v t0b-config:/config \
  -v <host>/theme/selfhost-dashboard:/config/www/themes/selfhost-dashboard:ro ...
docker inspect: volume t0b-config -> /config RW=true ; bind ... -> /config/www/themes/selfhost-dashboard RW=false
```
- Clean (empty) `/config` volume, first start: container comes up, migrations run, home returns 200 and the theme partial renders.
- **Noise on every start** (`docker logs`):
  ```
  chown: changing ownership of '/config/www/themes/selfhost-dashboard': Read-only file system
  ... (one line per theme file)
  **** Permissions could not be set. This is probably because your volume mounts are remote or read-only. ****
  **** The app may not work properly and we will not provide support for it. ****
  ```
  The app worked despite the message. CB tests must not treat this log text or any "chown" line as a failure.
- Mount point dir `/config/www/themes/selfhost-dashboard` is created by Docker inside the volume. After the mount is removed the empty dir stays in the volume (`drwxr-xr-x abc users`).
- Switching the dashboard off:
  - no mount, `APP_THEME` unset: home 200, no partial.
  - no mount, `APP_THEME=selfhost-dashboard` (empty leftover dir): home 200, standard grid, no partial.
  - `APP_THEME=does-not-exist`: home 200, standard grid.
  So a stale `APP_THEME` does not break BookStack (good for CB-5 and REQ-D5).
- On macOS the mount shows owner 0:0 via `fakeowner`. On a Linux host the files keep the host user's uid. They need to be world-readable (`0644`/`0755`) for php-fpm user `abc`.

### D-1b: include resolution and variable passing

Home page, request as admin: `#t0b-home` rendered before `id="home-default"` (include-before-grid: True). Variables visible in the home partial: `app, __themeViews, dates, viewBlocks, cspNonce, errors, locale, homeView, __env, __data, __path`. No page-specific data (as D-4 says).
Shelf page, variables visible in the shelf partial: `... pageTitle, shelf, sortedVisibleShelfBooks, view, listOptions` (no `$activity`, matches D-10).
`userCan('settings-manage')` returned `true` for the admin in the partial (D-11).

### D-7: env reaches PHP; APP_URL / URL derivation

```
container env: APP_URL=http://localhost:50470  T0B_CARD_URL=http://localhost:9999/card
partial: env('T0B_CARD_URL'), getenv(...), $_SERVER[...] => http://localhost:9999/card ; $_ENV[...] => null
config_cached: false
url('/') = config('app.url') = env('APP_URL') = http://localhost:50470
```
- Special characters are preserved byte for byte: `T0B_CARD_SPECIAL=http://h:8712/p?a=1&b=$X#f"q' sp` came out identical (also inside the container env).
- php-fpm pool has `clear_env = no` (`/etc/php85/php-fpm.d/www.conf:448`).
- With `php artisan config:cache` (forced as root, `abc` cannot write `bootstrap/cache`): `config_cached: true`, and `env('T0B_CARD_URL')` still returned the value. The app does not cache config by default.
- **APP_URL unset in the container**: `/config/www/.env` contains the default `APP_URL=https://example.com`. Then `url('/')` = `https://example.com` and login redirects to `https://example.com/`. Container env wins when set (`.env` had `example.com` in phase A and was overridden). So `./stack` must always pass `APP_URL`.
- A request with `Host: evil.example:81` is redirected to `http://localhost:50470/login`, not to the sent host (URL generation uses APP_URL, not the Host header).
- Verdict: the `/dashcards/cards.json` fallback (§7.3) is not needed.

### D-9: opcache and Blade after a theme edit

```
php-fpm (web request): opcache.validate_timestamps=1  opcache.revalidate_freq=2  opcache.enable=1
php -i (CLI):          same; opcache.enable_cli=Off ; open_basedir => no value
```
Edit of the theme partial on the host (bind mount), no restart:
```
before edit: V3
0s after edit V4: V3
1s: V3
4s: V4
default.blade.php edit (the overridden view) visible after 3 s: yes
```
- Behaviour matches `revalidate_freq=2`: new content within about 2-4 s. A `touch` without content change changed nothing visible, as expected.
- The "mtime restored after content change" probe is **inconclusive**: the content change was still picked up (V5), most likely because the bind mount (virtiofs) showed the container a newer mtime than the host reported. Do not rely on this probe.
- Consequence: the tema-hash container label (§6.1) is not needed for correctness on this image. It is still harmless and keeps AC-1 idempotence. Decision for the CEO/architect: keep (restart on every theme change) or drop (2-4 s propagation, no restart). Measured on Docker Desktop only. A Linux host with ext4 bind mounts should behave the same, not measured.

### D-18: open_basedir, user, readable paths

```
/etc/php85/php-fpm.d/www.conf:28:user = abc          (workers: "abc php-fpm: pool www")
open_basedir => no value (php.ini and CLI; web request ini_get('open_basedir') = "")
abc = uid 1000 (PUID=1000)
/dashfeed (named volume, ro, dir 0755, file 0644 owned 65534:65534): exists, readable, content read by PHP in a web request
/dashcards (bind, ro): readable
/dashfeed-outside/x.json (absent): exists=false
```
- `/config/php` is a scanned ini dir, so a user can add `open_basedir` there. Not set by default. Nothing to move.
- Snapshot file mode matters: uid 1000 is neither the owner (65534) nor in its group, so `0644` file and `0755` dir are required (matches CB-15). A `0640` or `0750` would break reading. Not tested negatively.

### D-10 / CB-11(d): shelf tags

Fixtures created by API (shelf A: WEB, API; shelf B: ZED, ABC, MID; shelf D: `Plane-Project`=` web `, `plane-project`=`<b>x`; shelf C: no tags).
```
$shelf->tags relation: relationLoaded=True before our code touches it; queries run by our access: []
Tags relation definition (Entity.php:231): morphMany(Tag::class,'entity')->orderBy('order','asc')
API create A: [('plane-project','WEB',0), ('plane-project','API',0)]    <- order always 0
Shelf B page partial order:   ZED, ABC, MID          Shelf B edit form order: ZED, ABC, MID
After saving shelf B through the web form with MID, ZED, ABC:
   partial order: MID, ZED, ABC (ids 8,9,10, new rows)   edit form order: MID, ZED, ABC
DB: select id,name,value,`order` from tags  -> all `order` = 0, ids ascend in submitted order
```
- Result: tag order in `$shelf->tags` equals the edit form order, so the §6.6 rule "first valid in `$shelf->tags` order" stays and the alphabetical fallback is NOT triggered.
- Caveat: `order` is always 0, so the tie order is whatever MariaDB returns (in practice primary key order). Both the form and the partial use the same query, so they agree. A sort by `id` inside the partial makes the rule deterministic. Recommended.
- The API stored ` web ` as `web` (trimmed). The tag name kept its case (`Plane-Project`). Normalization must still be case-insensitive on the name and trim/upper on the value (CB-11 c).
- D-10 text "tembel ilişki, bir sorgu çalıştırabilir" can be corrected: in v26.09.2 `tags` is already eager loaded on the shelf page, zero extra queries (measured with the query log on a request as admin).

### D-19 / CB-7(h): 404 probes

A `UPSTREAM` file at theme root, no `public/` dir:
```
/theme/selfhost-dashboard/UPSTREAM                  anon:404 authed:404
/theme/selfhost-dashboard/home/default.blade.php    anon:404 authed:404
/theme/selfhost-dashboard/selfhost/home.blade.php   anon:404 authed:404
/dashfeed/snapshot.json                             anon:404 authed:404
/dashfeed/                                          anon:404 authed:404
/dashcards/cards.json                               anon:404 authed:404
/themes/selfhost-dashboard/UPSTREAM                 anon:404 authed:404
/theme/nonexistent/x                                anon:404 authed:404
control: public/t.txt present -> /theme/selfhost-dashboard/t.txt anon:200   (route works; file then removed)
```

### D-15: host.docker.internal vs internal network (Docker Desktop, Linux VM)

Helper: python:3.13-alpine3.24 with a small socket connect script. `P` = the 127.0.0.1-published port of `t0b-app`.
```
1. user bridge net t0b-net, Desktop built-in name:
   host.docker.internal -> 192.168.65.254:P   CONNECT-OK (HTTP 302)       <- reaches host 127.0.0.1 publish
   1.1.1.1:443  CONNECT-OK (normal bridge has egress)
2. --add-host host.docker.internal:host-gateway: resolves to 192.168.65.254 (and fdc4:...::254), CONNECT-OK
3. network gateway 172.22.0.1:P  -> Connection refused
4. --network host in the VM: 127.0.0.1:P OK ; docker0 172.17.0.1:P -> Connection refused
```
- Reading: on Docker Desktop `host.docker.internal` is a Desktop proxy that reaches a loopback-only publish. That would make N1 look fine on the CEO's Mac while failing on a Linux Engine. Inside the Desktop VM (a Linux Engine), a bridge gateway IP does not reach a `127.0.0.1` publish (items 3 and 4). A real Linux `host-gateway` resolves to the docker0 gateway, so N1's rejection is supported. A real Linux host was **not** tested.

Internal network (`docker network create --driver bridge --internal --label com.selfhost.managed=dashfeed t0b-dashfeed`):
```
inspect: Internal=true Driver=bridge Labels=map[com.selfhost.managed:dashfeed]
t0b-app joined with: docker network connect --alias t0b-proxy-dashfeed t0b-dashfeed t0b-app   (kept t0b-net too)
collector on t0b-dashfeed only:
  t0b-proxy-dashfeed:80   CONNECT-OK        t0b-app:80  CONNECT-OK (container name also resolves)
  1.1.1.1:443             Network unreachable
  host.docker.internal (with --add-host host-gateway, 192.168.65.254):P   Network unreachable
  host.docker.internal (no add-host)   DNS-FAIL
  t0b-db:3306 (other net)             DNS-FAIL
  example.com:80                      DNS-FAIL
  route table: only 172.24.0.0/16 dev eth0 (no default route)
peer on t0b-net: t0b-proxy-dashfeed:80 -> DNS-FAIL   (the alias exists only on the net where it was set)
published port stays 127.0.0.1:50470 only
```
- Internal net blocks egress, external DNS, the host gateway and other networks' services. The alias resolves only inside the internal network.
- The container's own name also resolves on the internal net, not only the alias. For Plane this means the collector could reach the proxy by its service/container name too. Not harmful, but G-net's exact service-set check is the real limit.

D-22 (bonus): `docker network create --driver bridge t0b-dashfeed` a second time: `Error response from daemon: network with name t0b-dashfeed already exists`. Only the CLI path was tested. T-0c still has to confirm in the pinned Engine for the raw API path.

## 3. Cleanup (removed, only `t0b-`)

```
containers: t0b-app, t0b-db   (all --rm helper containers exited on their own)
networks:   t0b-net, t0b-dashfeed
volumes:    t0b-config, t0b-dbdata, t0b-snap
leftover check: docker ps -a / network ls / volume ls with name filter t0b- -> 0 / 0 / 0
```
- Pre-existing containers, volumes and networks were not touched (29 running containers, 52 volumes, 23 networks counted afterwards).
- Images: nothing deleted. `python:3.13-alpine3.24` stays in the local image cache (newly pulled; remove with `docker rmi python:3.13-alpine3.24` if the CEO wants it gone). The BookStack and MariaDB images were already local (used by the live stack).
- Scratch secrets, cookie jars and the API key file in the agent scratchpad were deleted. The scratchpad still holds the test theme (no secrets).

## 4. Results that change a criterion or the design

1. **APP_URL is mandatory in the container env** (D-7): unset gives `https://example.com` for URLs and login redirects. Add to CB-2/T-1: `stack` always passes `APP_URL`. The `/dashcards` fallback is dropped.
2. **Theme hash label / restart is optional** (D-9): validate_timestamps on, 2 s revalidate, edits visible in 2-4 s. Needs a decision: keep (idempotent, restarts) or drop.
3. **Init chown noise** (D-3): every start logs "Permissions could not be set" for the read-only nested mount. App works. No CB should fail on that text. Stale `APP_THEME` with no mount is harmless (200, standard page).
4. **Tag rule confirmed with a caveat** (D-10): `$shelf->tags` order = edit form order, so no alphabetical fallback. But `order` is always 0, so sort by `id` in the partial. D-10 text should say tags are already eager loaded (0 queries).
5. **File modes** (D-18): snapshot `0644`, dir `0755`, theme world-readable. php-fpm user is `abc` (uid 1000 by PUID), not the owner. No `open_basedir`.
6. **D-15 caveat**: on Docker Desktop `host.docker.internal` works against a loopback publish, so the Mac cannot prove the Linux failure. The Linux-like gateway test supports rejecting N1. The real Linux check stays with T-0c/CI on a Linux runner.
7. **Same-name alias vs container name** (D-15): the collector can also reach the Plane proxy by its service/container name on the internal net. G-net's exact-set check covers this.
