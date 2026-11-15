#!/bin/bash
# tests/run.sh: static acceptance tests AC-1..AC-10 of docs/spec-0001-sade.md (section 4).
# Live ACs (AC-11..AC-19) are T-8 and are NOT run here; no container is ever started.
#
# Rules (spec section 4):
#  - STACK_LOCAL_DIR is a temp dir; the real local/ is never touched.
#  - `docker compose config` output contains secrets: it goes to mode-600 temp files, is never
#    printed, and is deleted on exit. Failures print only key names, never values.
#  - A missing required tool prints `BLOCKED <AC> <tool>`; BLOCKED is not a pass and the suite
#    then exits 1 (also on any FAIL).
# Usage: /bin/bash tests/run.sh   (bash 3.2 compatible)

set -u
umask 077
LC_ALL=C
export LC_ALL

ROOT=$(cd "$(dirname "$0")/.." && pwd -P) || exit 2
STACK=$ROOT/stack
TMP=$(mktemp -d "${TMPDIR:-/tmp}/stack-tests.XXXXXX") || exit 2
trap 'rm -rf "$TMP"' EXIT
trap 'exit 130' INT TERM

NPASS=0
NFAIL=0
NBLOCK=0
pass() { NPASS=$((NPASS + 1)); printf 'PASS    %s\n' "$*"; }
fail() { NFAIL=$((NFAIL + 1)); printf 'FAIL    %s\n' "$*"; }
blocked() { NBLOCK=$((NBLOCK + 1)); printf 'BLOCKED %s %s\n' "$1" "$2"; }
check() { # check <AC> <description> <command...>: pass if the command succeeds
  local ac=$1 d=$2
  shift 2
  if "$@"; then pass "$ac $d"; else fail "$ac $d"; fi
}

SECRET_KEYS="BOOKSTACK_DB_PASSWORD BOOKSTACK_DB_ROOT_PASSWORD BOOKSTACK_APP_KEY BOOKSTACK_ADMIN_PASSWORD PENPOT_SECRET_KEY PENPOT_DB_PASSWORD PLANE_SECRET_KEY PLANE_LIVE_SECRET_KEY PLANE_DB_PASSWORD PLANE_RABBITMQ_PASSWORD PLANE_STORAGE_ACCESS_KEY PLANE_STORAGE_SECRET_KEY"
APPS="bookstack penpot plane"

fmode() { stat -c %a "$1" 2>/dev/null || stat -f %Lp "$1" 2>/dev/null; }
envval() { sed -n "s/^$2=//p" "$1" | head -n 1; } # file KEY
have() { command -v "$1" >/dev/null 2>&1; }

# ---------- fake docker (no daemon needed, nothing is started) ----------
FAKE=$TMP/fake
FAKELOG=$TMP/fake-docker.log
mkdir -p "$FAKE"
cat >"$FAKE/docker" <<'EOF'
#!/bin/bash
echo "$*" >> "$FAKE_DOCKER_LOG"
case "$1 ${2:-}" in
  "compose version") [ "${FAKE_NO_COMPOSE:-}" = 1 ] && exit 1; echo "Docker Compose version v2.0.0"; exit 0 ;;
  "volume ls") if [ -n "${FAKE_VOLUMES:-}" ]; then printf '%s\n' $FAKE_VOLUMES; fi; exit 0 ;;
esac
case "$1" in
  info) [ "${FAKE_NO_DAEMON:-}" = 1 ] && exit 1; exit 0 ;;
esac
exit 1
EOF
chmod 700 "$FAKE/docker"
: >"$FAKELOG"

# run_stack <path> <local_dir|-> args...: sets RC; stdout in $TMP/out, stderr in $TMP/err
RC=0
run_stack() {
  local p=$1 l=$2
  shift 2
  if [ "$l" = - ]; then
    env -u STACK_LOCAL_DIR -u HEALTH_TIMEOUT PATH="$p" FAKE_DOCKER_LOG="$FAKELOG" \
      FAKE_VOLUMES="${FAKE_VOLUMES:-}" FAKE_NO_COMPOSE="${FAKE_NO_COMPOSE:-}" FAKE_NO_DAEMON="${FAKE_NO_DAEMON:-}" \
      /bin/bash "$STACK" "$@" >"$TMP/out" 2>"$TMP/err"
  else
    env -u HEALTH_TIMEOUT STACK_LOCAL_DIR="$l" PATH="$p" FAKE_DOCKER_LOG="$FAKELOG" \
      FAKE_VOLUMES="${FAKE_VOLUMES:-}" FAKE_NO_COMPOSE="${FAKE_NO_COMPOSE:-}" FAKE_NO_DAEMON="${FAKE_NO_DAEMON:-}" \
      /bin/bash "$STACK" "$@" >"$TMP/out" 2>"$TMP/err"
  fi
  RC=$?
}
FAKEPATH=$FAKE:$PATH

one_hata() { # stderr is exactly one line and it starts with HATA:
  [ "$(wc -l <"$TMP/err" | tr -d ' ')" = 1 ] && grep -q '^HATA: ' "$TMP/err"
}

# ---------- shared temp local (init) ----------
LOC=$TMP/local
run_stack "$FAKEPATH" "$LOC" init
INIT_RC=$RC
ENVF=$LOC/.env

# ---------- config rendering (never printed) ----------
CFG_OK=1
render() { # render <app> <envfile> <outfile>
  ( umask 077; docker compose -p "selfhost-$1" -f "$ROOT/stacks/$1/compose.yaml" --env-file "$2" config >"$3" 2>"$3.err" )
}
cfgvals() { # cfgvals <cfgfile> <KEY>: every value of KEY (quotes stripped), one per line
  sed -n "s/^ *$2: *//p" "$1" | sed "s/^\"\(.*\)\"\$/\1/; s/^'\(.*\)'\$/\1/"
}

echo "== setup"
if [ "$INIT_RC" -ne 0 ]; then
  fail "setup: ./stack init in temp STACK_LOCAL_DIR exit $INIT_RC"
  CFG_OK=0
fi

# ---------- AC-1 ----------
echo "== AC-1 (REQ-1,2) compose config + image pins"
if ! have docker || ! docker compose version >/dev/null 2>&1; then
  blocked AC-1 "docker-compose-v2"
  CFG_OK=0
elif [ "$CFG_OK" = 1 ]; then
  IMG_RE='^[^:@]+:(v?[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9._-]+)?|[0-9]+\.[0-9]+(-alpine)?|RELEASE\.[0-9TZ-]+)(@sha256:[0-9a-f]{64})?$'
  for app in $APPS; do
    [ -f "$ROOT/stacks/$app/compose.yaml" ] && [ -f "$ROOT/stacks/$app/hooks.sh" ] || fail "AC-1 $app: compose.yaml/hooks.sh missing"
    if render "$app" "$ENVF" "$TMP/cfg-$app.yaml"; then
      pass "AC-1 $app: docker compose config exit 0"
    else
      fail "AC-1 $app: docker compose config failed"
      CFG_OK=0
      continue
    fi
    bad=0
    n=0
    while IFS= read -r img; do
      n=$((n + 1))
      if ! grep -Eq "$IMG_RE" <<<"$img"; then
        bad=1
        fail "AC-1 $app: image not pinned to full tag: $img"
      fi
      case $img in
        *linuxserver/bookstack*|*pgsty/silo*)
          grep -Eq '@sha256:[0-9a-f]{64}$' <<<"$img" || { bad=1; fail "AC-1 $app: missing @sha256: $img"; } ;;
      esac
    done <<EOF
$(sed -n 's/^ *image: *//p' "$TMP/cfg-$app.yaml" | sed "s/^\"\(.*\)\"\$/\1/")
EOF
    [ "$n" -gt 0 ] || fail "AC-1 $app: no image lines in config"
    [ "$bad" = 0 ] && [ "$n" -gt 0 ] && pass "AC-1 $app: $n images pinned"
  done
  for need in "linuxserver/bookstack" "pgsty/silo"; do
    cat "$TMP"/cfg-*.yaml 2>/dev/null | grep -E "image:.*$need.*@sha256:[0-9a-f]{64}" >/dev/null &&
      pass "AC-1 digest present: $need" || fail "AC-1 digest missing: $need"
  done
fi

# ---------- AC-2 ----------
echo "== AC-2 (REQ-3) shell quality, bash 3.2"
if have shellcheck; then
  if shellcheck --shell=bash "$ROOT/stack" "$ROOT"/stacks/*/hooks.sh "$ROOT/tests/run.sh" >"$TMP/sc.out" 2>&1; then
    pass "AC-2 shellcheck exit 0"
  else
    fail "AC-2 shellcheck findings (first lines follow)"
    head -n 20 "$TMP/sc.out"
  fi
else
  blocked AC-2 shellcheck
fi
check AC-2 "/bin/bash -n stack" /bin/bash -n "$STACK"
for f in "$ROOT"/stacks/*/hooks.sh "$ROOT/tests/run.sh"; do
  check AC-2 "/bin/bash -n ${f#"$ROOT"/}" /bin/bash -n "$f"
done
if grep -nE 'mapfile|readarray|declare +-A|\$\{[a-zA-Z_]+(,,|\^\^)' "$STACK" "$ROOT"/stacks/*/hooks.sh >/dev/null; then
  fail "AC-2 bash4-only constructs found"
else
  pass "AC-2 no bash4-only constructs (mapfile/readarray/declare -A/,,/^^)"
fi
case $(/bin/bash -c 'echo "${BASH_VERSINFO[0]}"') in
  3) pass "AC-2 /bin/bash is 3.x ($(/bin/bash -c 'echo "$BASH_VERSION"'))" ;;
  *) fail "AC-2 /bin/bash is not 3.x on this host; bash 3.2 not exercised" ;;
esac

# ---------- AC-3 ----------
echo "== AC-3 (REQ-4,5,6,7) init and .env parser"
if [ "$INIT_RC" -eq 0 ]; then
  [ "$(fmode "$LOC")" = 700 ] && pass "AC-3 local dir mode 700" || fail "AC-3 local dir mode $(fmode "$LOC")"
  [ "$(fmode "$ENVF")" = 600 ] && pass "AC-3 .env mode 600" || fail "AC-3 .env mode $(fmode "$ENVF")"
  [ "$(fmode "$LOC/backups")" = 700 ] && pass "AC-3 backups dir mode 700" || fail "AC-3 backups dir mode $(fmode "$LOC/backups")"
  : >"$TMP/vals"
  sbad=0
  for k in $SECRET_KEYS; do
    v=$(envval "$ENVF" "$k")
    if [ "$k" = BOOKSTACK_APP_KEY ]; then
      grep -Eq '^base64:.{44}$' <<<"$v" || { sbad=1; fail "AC-3 $k not base64:+44 chars"; }
    else
      grep -Eq '^[0-9a-f]{48,}$' <<<"$v" || { sbad=1; fail "AC-3 $k not hex >= 48"; }
    fi
    printf '%s\n' "$v" >>"$TMP/vals"
  done
  [ "$(sort "$TMP/vals" | uniq | wc -l | tr -d ' ')" = "$(wc -l <"$TMP/vals" | tr -d ' ')" ] ||
    { sbad=1; fail "AC-3 secrets are not all distinct"; }
  [ "$sbad" = 0 ] && pass "AC-3 12 secrets: non-empty, hex>=48 (APP_KEY base64:+44), distinct"
  # second init: byte-identical
  h1=$(shasum "$ENVF" | cut -d' ' -f1)
  run_stack "$FAKEPATH" "$LOC" init
  h2=$(shasum "$ENVF" | cut -d' ' -f1)
  [ "$RC" = 0 ] && [ "$h1" = "$h2" ] && pass "AC-3 second init leaves .env byte-identical" || fail "AC-3 second init changed .env (rc $RC)"
  # delete one key: only that line comes back, others byte-identical
  cp "$ENVF" "$TMP/env.before"
  grep -v '^PLANE_LIVE_SECRET_KEY=' "$TMP/env.before" >"$TMP/env.minus"
  cp "$TMP/env.minus" "$ENVF"
  run_stack "$FAKEPATH" "$LOC" init
  n_new=$(wc -l <"$ENVF" | tr -d ' ')
  n_old=$(wc -l <"$TMP/env.minus" | tr -d ' ')
  head -n "$n_old" "$ENVF" >"$TMP/env.head"
  if [ "$RC" = 0 ] && [ "$n_new" = $((n_old + 1)) ] && cmp -s "$TMP/env.head" "$TMP/env.minus" &&
    tail -n 1 "$ENVF" | grep -q '^PLANE_LIVE_SECRET_KEY=.\{48,\}$'; then
    pass "AC-3 deleted key re-added alone; other lines byte-identical"
  else
    fail "AC-3 re-adding a deleted key altered other lines"
  fi
  cp "$TMP/env.before" "$ENVF"
  [ -z "$(find "$LOC" -name '*.tmp*' 2>/dev/null)" ] && pass "AC-3 no *.tmp leftovers" || fail "AC-3 tmp leftovers in local dir"
  [ "$(fmode "$ENVF")" = 600 ] || fail "AC-3 .env mode after re-init $(fmode "$ENVF")"
  # parser: '=' inside a value is read correctly (sourced function, no docker)
  sed '/^main "\$@"$/,$d' "$STACK" >"$TMP/stack_lib.sh"
  cat >"$TMP/libtest.sh" <<'EOF'
#!/bin/bash
. "$1"
load_env "$2"
printf '%s' "$ENV_BOOKSTACK_APP_KEY"
EOF
  want=$(envval "$ENVF" BOOKSTACK_APP_KEY)
  got=$(/bin/bash "$TMP/libtest.sh" "$TMP/stack_lib.sh" "$ENVF" 2>/dev/null)
  case $want in *=*) ;; *) fail "AC-3 fixture: BOOKSTACK_APP_KEY has no '=' to test" ;; esac
  [ "$got" = "$want" ] && pass "AC-3 value containing '=' (BOOKSTACK_APP_KEY) parsed exactly" || fail "AC-3 '=' in value mis-parsed"
  # rejected lines, up must exit 2 with <file>:<line> and never reach docker compose
  for case_ in 'export X=1' 'NOEQUALSLINE' 'lower=1' 'X=$(touch '"$TMP"'/pwn)'; do
    cp "$TMP/env.before" "$TMP/bad/.env" 2>/dev/null || { mkdir -p "$TMP/bad" && cp "$TMP/env.before" "$TMP/bad/.env"; }
    chmod 700 "$TMP/bad"
    printf '%s\n' "$case_" >>"$TMP/bad/.env"
    ln_no=$(wc -l <"$TMP/bad/.env" | tr -d ' ')
    : >"$FAKELOG"
    run_stack "$FAKEPATH" "$TMP/bad" up bookstack
    if [ "$RC" = 2 ] && grep -q "bad/.env:$ln_no:" "$TMP/err" && one_hata &&
      ! grep -Ev '^(compose version|info)$' "$FAKELOG" | grep -q .; then
      pass "AC-3 bad line rejected with <file>:$ln_no (exit 2): ${case_%%/*}"
    else
      fail "AC-3 bad line not rejected correctly (rc $RC): ${case_%%/*}"
    fi
  done
  [ ! -e "$TMP/pwn" ] && pass "AC-3 \$(touch pwn) in .env not executed" || fail "AC-3 .env line was executed (pwn exists)"
  # same payload as the VALUE of an allowed key
  sed "s|^PENPOT_EXTRA_FLAGS=.*|PENPOT_EXTRA_FLAGS=\$(touch $TMP/pwn2)|" "$TMP/env.before" >"$TMP/bad/.env"
  run_stack "$FAKEPATH" "$TMP/bad" up penpot
  [ "$RC" = 2 ] && [ ! -e "$TMP/pwn2" ] && pass "AC-3 command substitution in allowed key value rejected, not run" || fail "AC-3 allowed-key value payload (rc $RC)"
else
  fail "AC-3 skipped: init failed"
fi

# ---------- AC-4 ----------
echo "== AC-4 (REQ-6) clean copy: git status stays clean after init"
if have git && have tar; then
  CL=$TMP/clone
  mkdir -p "$CL"
  ( cd "$ROOT" && git ls-files -z -co --exclude-standard | tar --null -T - -cf - ) | tar -xf - -C "$CL" 2>/dev/null
  if [ -x "$CL/stack" ] || [ -f "$CL/stack" ]; then
    ( cd "$CL" && git init -q . && git add -A && git -c user.name=t -c user.email=t@t commit -q -m t ) >/dev/null 2>&1
    ( cd "$CL" && env -u STACK_LOCAL_DIR PATH="$FAKEPATH" FAKE_DOCKER_LOG="$FAKELOG" /bin/bash ./stack init >/dev/null 2>&1 )
    porc=$(cd "$CL" && git status --porcelain)
    [ -z "$porc" ] && pass "AC-4 git status --porcelain empty after init" || fail "AC-4 git status not clean after init (files: $(printf '%s\n' "$porc" | tr -d '\n' | cut -c1-80))"
    ign=$(cd "$CL" && git check-ignore local/.env local/backups | wc -l | tr -d ' ')
    [ "$ign" = 2 ] && pass "AC-4 git check-ignore lists local/.env and local/backups" || fail "AC-4 check-ignore matched $ign of 2"
    [ -f "$CL/local/.env" ] || fail "AC-4 init did not create local/.env in copy"
  else
    fail "AC-4 could not build the repo copy"
  fi
else
  have git || blocked AC-4 git
  have tar || blocked AC-4 tar
fi

# ---------- AC-5, AC-6, AC-7 (config based) ----------
echo "== AC-5 (REQ-9,10) static network posture"
if [ "$CFG_OK" = 1 ]; then
  for app in $APPS; do
    c=$TMP/cfg-$app.yaml
    [ "$(grep -c '^ *published:' "$c")" = 1 ] && pass "AC-5 $app: published: x1" || fail "AC-5 $app: published count $(grep -c '^ *published:' "$c")"
    [ "$(grep -c '^ *host_ip: 127\.0\.0\.1$' "$c")" = 1 ] && pass "AC-5 $app: host_ip 127.0.0.1 x1" || fail "AC-5 $app: host_ip 127.0.0.1 count $(grep -c '^ *host_ip: 127\.0\.0\.1$' "$c")"
    grep -q '^ *host_ip:' "$c" && [ "$(grep -c '^ *host_ip:' "$c")" = 1 ] || fail "AC-5 $app: unexpected host_ip lines"
    if grep -nE '^ *(network_mode|privileged|cap_add|pid):|docker\.sock' "$c" >/dev/null; then
      fail "AC-5 $app: forbidden isolation key present ($(grep -oE '^ *(network_mode|privileged|cap_add|pid):|docker\.sock' "$c" | sort -u | tr -d ' \n'))"
    else
      pass "AC-5 $app: no network_mode/privileged/cap_add/docker.sock/pid"
    fi
    grep -qE '^ *internal: true$' "$c" && pass "AC-5 $app: internal: true network" || fail "AC-5 $app: no internal: true network"
  done
else
  fail "AC-5 skipped: no config (see AC-1)"
fi
echo "   (AC-5 runtime lsof/docker inspect part is live: T-8)"

echo "== AC-6 (REQ-11,12) penpot flags, URLs"
if [ "$CFG_OK" = 1 ]; then
  pc=$TMP/cfg-penpot.yaml
  for s in penpot-mailpit penpot-mcp penpot-admin-console; do
    grep -q "^  $s:\$" "$pc" && fail "AC-6 penpot service present: $s" || pass "AC-6 penpot service absent: $s"
  done
  flags=$(cfgvals "$pc" PENPOT_FLAGS | sort -u)
  [ -n "$flags" ] || fail "AC-6 PENPOT_FLAGS not found in config"
  case " $flags " in *" disable-registration "*) pass "AC-6 PENPOT_FLAGS has disable-registration" ;; *) fail "AC-6 PENPOT_FLAGS lacks disable-registration" ;; esac
  for f in enable-smtp enable-mcp enable-prepl-server enable-telemetries; do
    case " $flags " in *" $f "*) fail "AC-6 PENPOT_FLAGS contains $f" ;; *) pass "AC-6 PENPOT_FLAGS lacks $f" ;; esac
  done
  cfgvals "$pc" PENPOT_TELEMETRY_ENABLED | grep -qx false && pass "AC-6 PENPOT_TELEMETRY_ENABLED=false" || fail "AC-6 PENPOT_TELEMETRY_ENABLED not false"
  # depends_on validity is covered by `config` exit 0 (AC-1)
  cfgvals "$TMP/cfg-plane.yaml" ENABLE_SIGNUP | sort -u | grep -qx '0' && pass "AC-6 plane ENABLE_SIGNUP=0 (registration key closed)" || fail "AC-6 plane ENABLE_SIGNUP not 0"
  # URLs follow the port; port change flows to config
  sed -e 's/^BOOKSTACK_PORT=.*/BOOKSTACK_PORT=18701/' -e 's/^PENPOT_PORT=.*/PENPOT_PORT=18702/' -e 's/^PLANE_PORT=.*/PLANE_PORT=18703/' "$ENVF" >"$TMP/env.ports"
  for pair in "bookstack:APP_URL:8701" "penpot:PENPOT_PUBLIC_URI:8702" "plane:WEB_URL:8703" "plane:CORS_ALLOWED_ORIGINS:8703"; do
    app=${pair%%:*}
    rest=${pair#*:}
    key=${rest%%:*}
    port=${rest#*:}
    got=$(cfgvals "$TMP/cfg-$app.yaml" "$key" | sort -u)
    [ "$got" = "http://127.0.0.1:$port" ] && pass "AC-6 $app $key = http://127.0.0.1:$port" || fail "AC-6 $app $key unexpected: $got"
    render "$app" "$TMP/env.ports" "$TMP/cfgp-$app.yaml" || { fail "AC-6 $app: config with new port failed"; continue; }
    got=$(cfgvals "$TMP/cfgp-$app.yaml" "$key" | sort -u)
    [ "$got" = "http://127.0.0.1:1${port}" ] && pass "AC-6 $app $key follows port change" || fail "AC-6 $app $key did not follow port change: $got"
    pub=$(sed -n 's/^ *published: *//p' "$TMP/cfgp-$app.yaml" | tr -d '"')
    [ "$pub" = "1${port}" ] && pass "AC-6 $app published port follows change" || fail "AC-6 $app published port not changed"
  done
else
  fail "AC-6 skipped: no config (see AC-1)"
fi

echo "== AC-7 (REQ-12) secrets come from local/.env, no upstream defaults"
if [ "$CFG_OK" = 1 ]; then
  # app:CONFIG_KEY:ENV_KEY
  for t in \
    bookstack:APP_KEY:BOOKSTACK_APP_KEY bookstack:DB_PASSWORD:BOOKSTACK_DB_PASSWORD bookstack:MARIADB_PASSWORD:BOOKSTACK_DB_PASSWORD \
    penpot:PENPOT_SECRET_KEY:PENPOT_SECRET_KEY penpot:POSTGRES_PASSWORD:PENPOT_DB_PASSWORD \
    plane:SECRET_KEY:PLANE_SECRET_KEY plane:LIVE_SERVER_SECRET_KEY:PLANE_LIVE_SECRET_KEY plane:POSTGRES_PASSWORD:PLANE_DB_PASSWORD \
    plane:RABBITMQ_DEFAULT_PASS:PLANE_RABBITMQ_PASSWORD plane:AWS_ACCESS_KEY_ID:PLANE_STORAGE_ACCESS_KEY \
    plane:AWS_SECRET_ACCESS_KEY:PLANE_STORAGE_SECRET_KEY; do
    app=${t%%:*}
    rest=${t#*:}
    ck=${rest%%:*}
    ek=${rest#*:}
    want=$(envval "$ENVF" "$ek")
    n=0
    ok=1
    while IFS= read -r v; do
      [ -n "$v" ] || continue
      n=$((n + 1))
      [ "$v" = "$want" ] || ok=0
    done <<EOF
$(cfgvals "$TMP/cfg-$app.yaml" "$ck")
EOF
    if [ "$n" -gt 0 ] && [ "$ok" = 1 ] && [ -n "$want" ]; then
      pass "AC-7 $app $ck == $ek ($n occurrences)"
    else
      fail "AC-7 $app $ck != $ek (occurrences $n)"
    fi
  done
  # keys the spec lists but that may not exist in a given compose file
  for k in RABBITMQ_PASSWORD; do
    if cat "$TMP"/cfg-*.yaml | grep -q "^ *$k:"; then
      cfgvals "$TMP/cfg-plane.yaml" "$k" | sort -u | grep -qx "$(envval "$ENVF" PLANE_RABBITMQ_PASSWORD)" && pass "AC-7 $k == PLANE_RABBITMQ_PASSWORD" || fail "AC-7 $k mismatch"
    fi
  done
else
  fail "AC-7 skipped: no config (see AC-1)"
fi
# missing/empty required key: up exits 2 before any docker call (fake docker records calls)
for k in BOOKSTACK_DB_PASSWORD PENPOT_SECRET_KEY PLANE_STORAGE_SECRET_KEY; do
  for mode in missing empty; do
    mkdir -p "$TMP/miss"
    chmod 700 "$TMP/miss"
    if [ "$mode" = missing ]; then grep -v "^$k=" "$ENVF" >"$TMP/miss/.env"; else sed "s/^$k=.*/$k=/" "$ENVF" >"$TMP/miss/.env"; fi
    : >"$FAKELOG"
    run_stack "$FAKEPATH" "$TMP/miss" up all
    if [ "$RC" = 2 ] && one_hata && grep -q "$k" "$TMP/err" && ! grep -Ev '^(compose version|info)$' "$FAKELOG" | grep -q .; then
      pass "AC-7 up exit 2, no docker call, $mode $k"
    else
      fail "AC-7 $mode $k: rc $RC / docker calls / message"
    fi
  done
done

# ---------- AC-8 ----------
echo "== AC-8 (REQ-8,20) usage errors, ports, missing tools"
exp() { # exp <description> <expected_rc> <path> args...
  local d=$1 e=$2 p=$3
  shift 3
  : >"$FAKELOG"
  run_stack "$p" "$LOC" "$@"
  if [ "$RC" = "$e" ] && one_hata; then pass "AC-8 $d (exit $e, one HATA line)"; else fail "AC-8 $d: rc $RC (want $e) stderr lines $(wc -l <"$TMP/err" | tr -d ' ')"; fi
}
exp "no command" 1 "$FAKEPATH"
exp "unknown command" 1 "$FAKEPATH" frobnicate
exp "unknown app (up)" 1 "$FAKEPATH" up nosuchapp
exp "unknown app (backup)" 1 "$FAKEPATH" backup nosuchapp
exp "two apps" 1 "$FAKEPATH" up bookstack penpot
exp "logs all" 1 "$FAKEPATH" logs all
exp "logs without app" 1 "$FAKEPATH" logs
exp "init with argument" 1 "$FAKEPATH" init x
for badport in 80 70000 abc; do
  mkdir -p "$TMP/port"
  chmod 700 "$TMP/port"
  sed "s/^BOOKSTACK_PORT=.*/BOOKSTACK_PORT=$badport/" "$ENVF" >"$TMP/port/.env"
  run_stack "$FAKEPATH" "$TMP/port" up
  if [ "$RC" = 2 ] && one_hata && grep -q 'BOOKSTACK_PORT' "$TMP/err"; then pass "AC-8 port $badport rejected (exit 2)"; else fail "AC-8 port $badport: rc $RC"; fi
done
sed "s/^PENPOT_PORT=.*/PENPOT_PORT=8701/" "$ENVF" >"$TMP/port/.env"
run_stack "$FAKEPATH" "$TMP/port" status
if [ "$RC" = 2 ] && one_hata; then pass "AC-8 duplicate ports rejected (exit 2)"; else fail "AC-8 duplicate ports: rc $RC"; fi
# no local dir
run_stack "$FAKEPATH" "$TMP/nolocal" status
if [ "$RC" = 2 ] && one_hata && grep -q 'init' "$TMP/err"; then pass "AC-8 no local/.env: exit 2, mentions init"; else fail "AC-8 no local/.env: rc $RC"; fi
# missing tools: PATH holds symlinks to everything except the tool under test
mkbin() { # mkbin <dir> <skip...>
  local d=$1 t p s skip
  shift
  mkdir -p "$d"
  for t in awk sed tr cut sort uniq mktemp chmod rm cat mkdir mv grep head tail date uname dirname cp od openssl curl lsof nc wc; do
    skip=0
    for s in "$@"; do [ "$s" = "$t" ] && skip=1; done
    [ "$skip" = 1 ] && continue
    p=$(command -v "$t") && ln -sf "$p" "$d/$t"
  done
  return 0
}
tool_case() { # tool_case <label> <expected word> <bindir>
  : >"$FAKELOG"
  run_stack "$3" "$LOC" up bookstack
  if [ "$RC" = 2 ] && one_hata && grep -q "$2" "$TMP/err"; then pass "AC-8 $1 missing -> exit 2, names '$2'"; else fail "AC-8 $1 missing: rc $RC"; fi
}
mkbin "$TMP/bin-nodocker"
tool_case docker docker "$TMP/bin-nodocker"
mkbin "$TMP/bin-nocurl" curl
ln -sf "$FAKE/docker" "$TMP/bin-nocurl/docker"
tool_case curl curl "$TMP/bin-nocurl"
mkbin "$TMP/bin-nolsof" lsof nc
ln -sf "$FAKE/docker" "$TMP/bin-nolsof/docker"
tool_case "lsof+nc" lsof "$TMP/bin-nolsof"
FAKE_NO_COMPOSE=1 tool_case "docker compose v2" "docker compose" "$FAKEPATH"
FAKE_NO_DAEMON=1 tool_case "docker daemon" "Docker" "$FAKEPATH"
mkbin "$TMP/bin-noopenssl" openssl od
ln -sf "$FAKE/docker" "$TMP/bin-noopenssl/docker"
run_stack "$TMP/bin-noopenssl" "$TMP/ssl" init
if [ "$RC" = 2 ] && one_hata && grep -q 'openssl' "$TMP/err"; then pass "AC-8 openssl+od missing -> exit 2 (init)"; else fail "AC-8 openssl+od missing: rc $RC"; fi

# ---------- AC-9 ----------
echo "== AC-9 (REQ-18) orphan volume warning"
FAKE_VOLUMES="selfhost-bookstack_config" run_stack "$FAKEPATH" "$TMP/orphan" init
if [ "$RC" = 0 ] && grep -q 'UYARI.*selfhost-bookstack' "$TMP/out" && [ -f "$TMP/orphan/.env" ] &&
  [ -n "$(envval "$TMP/orphan/.env" BOOKSTACK_DB_PASSWORD)" ]; then
  pass "AC-9 warning printed, exit 0, secrets generated"
else
  fail "AC-9 orphan-volume warning (rc $RC)"
fi
run_stack "$FAKEPATH" "$TMP/orphan2" init
grep -q 'UYARI' "$TMP/out" && fail "AC-9 warning printed without volumes" || pass "AC-9 no warning when no volumes exist"

# ---------- AC-10 ----------
echo "== AC-10 (REQ-23) NOTICE and upstream headers"
if [ -f "$ROOT/NOTICE" ]; then
  N=$ROOT/NOTICE
  grep -q 'penpot' "$N" && grep -q '2\.18\.6' "$N" && grep -q 'MPL-2\.0' "$N" && pass "AC-10 NOTICE: penpot repo/tag/license" || fail "AC-10 NOTICE lacks penpot repo/tag/license"
  grep -q 'makeplane/plane' "$N" && grep -q 'v1\.4\.3' "$N" && grep -q 'AGPL-3\.0' "$N" && pass "AC-10 NOTICE: plane repo/tag/license" || fail "AC-10 NOTICE lacks plane repo/tag/license"
  grep -qi 'bookstack' "$N" && grep -q 'v26\.09\.2' "$N" && grep -qE 'GPL-3\.0|MIT' "$N" && pass "AC-10 NOTICE: bookstack repo/tag/license" || fail "AC-10 NOTICE lacks bookstack repo/tag/license"
else
  fail "AC-10 NOTICE file missing (T-7 deliverable)"
fi
for app in penpot plane; do
  h=$(head -n 8 "$ROOT/stacks/$app/compose.yaml")
  if grep -q 'https://' <<<"$h" && grep -Eiq 'tag|v?[0-9]+\.[0-9]+\.[0-9]+' <<<"$h" && grep -q 'License' <<<"$h"; then
    pass "AC-10 $app compose header: URL + tag + license"
  else
    fail "AC-10 $app compose header lacks URL/tag/license"
  fi
done
hp=$(head -n 8 "$ROOT/stacks/penpot/compose.yaml")
hl=$(head -n 8 "$ROOT/stacks/plane/compose.yaml")
if grep -q 'MPL-2\.0' <<<"$hp" && grep -q 'AGPL-3\.0' <<<"$hl"; then
  pass "AC-10 header licenses MPL-2.0 (penpot) / AGPL-3.0 (plane)"
else
  fail "AC-10 header license ids"
fi

# ---------- summary ----------
echo "== summary"
echo "(live ACs AC-11..AC-19 are T-8, not run; no container was started)"
printf 'PASS %s  FAIL %s  BLOCKED %s\n' "$NPASS" "$NFAIL" "$NBLOCK"
[ "$NFAIL" = 0 ] && [ "$NBLOCK" = 0 ] && exit 0
exit 1
