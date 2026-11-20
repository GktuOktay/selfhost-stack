# shellcheck shell=bash
# stacks/penpot/hooks.sh: Penpot hook functions for ./stack (see HOOK SOZLESMESI in ./stack).
# Only function definitions; no side effects when sourced.
#
# Removed from upstream: penpot-mailpit, penpot-mcp, penpot-admin-console (AC-6: all three removed
# cleanly; the 2.18.6 frontend does not depend on them once the enable-mcp/enable-admin-console
# flags and the depends_on entries are gone). Runtime behavior is verified live in T-8.
#
# First user (registration is disabled, no bootstrap possible without prepl):
#   1. add PENPOT_EXTRA_FLAGS=enable-prepl-server to local/.env, ./stack up penpot
#   2. docker exec -ti selfhost-penpot-penpot-backend-1 python3 manage.py create-profile
#   3. remove the flag from local/.env, ./stack up penpot (recreates backend without prepl)

app_health() {
  local code
  code=$(curl -sS -m 5 -o /dev/null -w '%{http_code}' "$STACK_URL/" 2>/dev/null) || return 1
  [ "$code" = 200 ]
}

app_status_extra() {
  local f
  f=$(stack_env PENPOT_EXTRA_FLAGS 2>/dev/null || true)
  case $f in
    *prepl*) echo "UYARI: enable-prepl-server acik (kimliksiz REPL); ilk profilden sonra PENPOT_EXTRA_FLAGS'i bosalt" ;;
  esac
  echo "registration: disabled"
}

app_up_note() {
  echo "Penpot: kayit kapali. Ilk profil icin README prosedurunu izle (gecici PENPOT_EXTRA_FLAGS=enable-prepl-server)."
}

# $1 = target dir (700, already open). db.sql + assets.tar (600). DB password is taken from the
# container env (never on argv). tar from the app image (penpot-backend, volume penpot_assets).
# Not verified live (T-8): tar presence in the backend image.
app_backup() {
  local dir=$1
  stack_compose exec -T penpot-postgres sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
    >"$dir/db.sql" || { echo "db dump basarisiz"; return 1; }
  [ -s "$dir/db.sql" ] || { echo "db.sql bos"; return 1; }
  stack_compose exec -T penpot-backend tar -C /opt/data -cf - assets \
    >"$dir/assets.tar" || { echo "assets tar basarisiz"; return 1; }
  [ -s "$dir/assets.tar" ] || { echo "assets.tar bos"; return 1; }
  chmod 600 "$dir/db.sql" "$dir/assets.tar"
  tar -tf "$dir/assets.tar" >/dev/null || { echo "assets.tar okunamadi"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Proje tasima (./stack export|import penpot): Penpot RPC (binfile v3), backend 2.17/2.18 kaynagina gore:
#   login-with-password {email,password} | access token ("Authorization: Token ...", enable-access-tokens)
#   get-all-projects, get-teams, get-projects {team-id}, get-project-files {project-id}, create-project
#   export-binfile {file-id,include-libraries,embed-assets} (ikisi ayni anda true OLAMAZ; SSE, son olay
#     "end" = /assets/by-id/<uuid> adresi)  |  import-binfile (multipart: name, project-id, version=3, file; SSE)
# Kimlik bilgisi: ortamdan PENPOT_ACCESS_TOKEN ya da PENPOT_EMAIL+PENPOT_PASSWORD; yoksa terminalde sorulur.
# Secret ARGV'ye girmez: curl yapilandirmasi ve JSON govdesi 600 gecici dosyalarda tutulur.
# Hook cagrilari: app_export list | app_export run <dizin> <proje|id> <include|embed>
#                 app_import <dizin> <takim|""> <proje|"">   (dizin dogrulanmis arsiv; hash'ler burada kontrol edilir)
# Cikis: 0 ok, 1 kullanim/secim hatasi, 2 on kosul (jq, kimlik), diger = 5.
# ---------------------------------------------------------------------------

pp_cleanup() { [ -n "${PP_TMP:-}" ] && rm -rf "$PP_TMP"; return 0; }

pp_sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

# curl, kimlik yapilandirmasi (-K) ile; ARGV'de secret yok.
pp_curl() { curl -sS -K "$PP_TMP/auth.cfg" "$@"; }

# JSON govdeli RPC: pp_rpc <komut> <json-dosyasi|-> ; stdout = yanit JSON'u
pp_rpc() {
  local cmd=$1 body=${2:-}
  [ -n "$body" ] || { printf '{}' >"$PP_TMP/empty.json"; body=$PP_TMP/empty.json; }
  pp_curl -m 60 -H 'Content-Type: application/json' -H 'Accept: application/json' \
    --data-binary @"$body" -w '\n%{http_code}' "$STACK_URL/api/rpc/command/$cmd" >"$PP_TMP/resp.out" 2>"$PP_TMP/resp.err" || return 1
  PP_CODE=$(tail -n1 "$PP_TMP/resp.out")
  sed '$d' "$PP_TMP/resp.out" >"$PP_TMP/resp.json"
  [ "$PP_CODE" = 200 ] || return 1
  cat "$PP_TMP/resp.json"
}
pp_rpc_json() { # pp_rpc_json <komut> <jq-filtresi-obje> : govdeyi jq ile uretir (degerler ortamdan: A, B)
  local cmd=$1 filter=$2
  jq -n "$filter" >"$PP_TMP/body.json" || return 1
  pp_rpc "$cmd" "$PP_TMP/body.json"
}
pp_fail_hint() { echo "Penpot yaniti: HTTP ${PP_CODE:-?} $(head -c 200 "$PP_TMP/resp.json" 2>/dev/null | tr -d '\r\n')"; }

pp_init() { # gecici dizin + kimlik dogrulama
  command -v jq >/dev/null 2>&1 || { echo "jq bulunamadi; kur ve PATH'e ekle"; return 2; }
  command -v curl >/dev/null 2>&1 || { echo "curl bulunamadi"; return 2; }
  PP_TMP=$(mktemp -d "${TMPDIR:-/tmp}/stack-penpot.XXXXXX") || { echo "gecici dizin acilamadi"; return 2; }
  chmod 700 "$PP_TMP"
  trap pp_cleanup EXIT
  trap 'exit 130' INT TERM
  : >"$PP_TMP/auth.cfg"; chmod 600 "$PP_TMP/auth.cfg"
  local tok=${PENPOT_ACCESS_TOKEN:-} em=${PENPOT_EMAIL:-} pw=${PENPOT_PASSWORD:-}
  if [ -n "$tok" ]; then
    case $tok in *[!A-Za-z0-9_.-]*) echo "PENPOT_ACCESS_TOKEN gecersiz karakter iceriyor"; return 2 ;; esac
    printf 'header = "Authorization: Token %s"\n' "$tok" >"$PP_TMP/auth.cfg"
    return 0
  fi
  if [ -z "$em" ] || [ -z "$pw" ]; then
    if [ -t 0 ]; then
      echo "Penpot kimlik bilgisi gerekli (PENPOT_ACCESS_TOKEN ya da PENPOT_EMAIL/PENPOT_PASSWORD ortam degiskeni de olur)."
      echo "Penpot e-posta:"
      read -r em || { echo "e-posta okunamadi"; return 2; }
      echo "Penpot parola (gizli):"
      stty -echo 2>/dev/null
      read -r pw
      stty echo 2>/dev/null
    else
      echo "Kimlik yok: PENPOT_ACCESS_TOKEN ya da PENPOT_EMAIL+PENPOT_PASSWORD ortam degiskenini ayarla"
      return 2
    fi
  fi
  [ -n "$em" ] && [ -n "$pw" ] || { echo "e-posta/parola bos"; return 2; }
  EM=$em PW=$pw jq -n '{email: env.EM, password: env.PW}' >"$PP_TMP/login.json"
  chmod 600 "$PP_TMP/login.json"
  printf 'cookie-jar = "%s"\ncookie = "%s"\n' "$PP_TMP/jar" "$PP_TMP/jar" >"$PP_TMP/auth.cfg"
  if ! pp_rpc login-with-password "$PP_TMP/login.json" >/dev/null; then
    rm -f "$PP_TMP/login.json"
    echo "Penpot girisi basarisiz (HTTP ${PP_CODE:-?}); e-posta/parolayi kontrol et"
    return 2
  fi
  rm -f "$PP_TMP/login.json"
  return 0
}

# SSE yanitini coz: stdout = son "end" olayinin verisi; hata olayi ya da end yoksa 1
pp_sse_end() {
  awk '/^event:/ { ev = $2 } /^data:/ { d = substr($0, 7); if (ev == "end") last = d; if (ev == "error") err = d }
       END { if (err != "") { print substr(err, 1, 300) > "/dev/stderr"; exit 1 } if (last == "") exit 1; print last }' "$1"
}

pp_slug() { printf '%s' "$1" | tr -c 'A-Za-z0-9_-' '_' | cut -c1-40; }

pp_version() {
  sed -n 's#^ *image: *"penpotapp/backend:\([^"]*\)".*#\1#p' "$STACK_ROOT/stacks/penpot/compose.yaml" | head -n1
}

pp_projects() { # JSON dizi: [{id,name,teamId,teamName}]
  pp_rpc get-all-projects >"$PP_TMP/projects.json" || { echo "proje listesi alinamadi"; pp_fail_hint; return 1; }
}

app_export() {
  local mode=$1 dir sel kind rc
  shift
  pp_init || return $?
  pp_projects || return 1
  case $mode in
    list)
      jq -r 'sort_by(.teamName, .name)[] | [.teamName, .name, .id] | @tsv' "$PP_TMP/projects.json" |
        awk -F'\t' 'BEGIN { print "TAKIM\tPROJE\tID" } { print }'
      return 0 ;;
    run) dir=$1 sel=$2 kind=$3 ;;
    *) echo "app_export: bilinmeyen mod"; return 1 ;;
  esac
  local n pid pname tname
  n=$(jq --arg s "$sel" '[.[] | select(.id == $s or .name == $s)] | length' "$PP_TMP/projects.json")
  [ "$n" -ge 1 ] 2>/dev/null || { echo "proje bulunamadi: $sel (./stack export penpot --list)"; return 1; }
  if [ "$n" -gt 1 ]; then
    echo "birden fazla proje eslesti; ID ile sec:"
    jq -r --arg s "$sel" '.[] | select(.id == $s or .name == $s) | "  \(.id)  \(.teamName) / \(.name)"' "$PP_TMP/projects.json"
    return 1
  fi
  jq -r --arg s "$sel" '.[] | select(.id == $s or .name == $s) | [.id, .name, .teamName] | @tsv' "$PP_TMP/projects.json" >"$PP_TMP/sel.tsv"
  IFS="$(printf '\t')" read -r pid pname tname <"$PP_TMP/sel.tsv"
  PID=$pid pp_rpc_json get-project-files '{projectId: env.PID}' >"$PP_TMP/files.json" || { echo "dosya listesi alinamadi"; pp_fail_hint; return 1; }
  local count i=0 fid fname slug out url uuid sum bytes
  count=$(jq 'length' "$PP_TMP/files.json")
  [ "$count" -ge 1 ] || { echo "projede dosya yok: $pname"; return 1; }
  : >"$PP_TMP/entries.jsonl"
  while [ "$i" -lt "$count" ]; do
    fid=$(jq -r ".[$i].id" "$PP_TMP/files.json")
    fname=$(jq -r ".[$i].name" "$PP_TMP/files.json")
    i=$((i + 1))
    slug=$(printf '%02d-%s.penpot' "$i" "$(pp_slug "$fname")")
    out=$dir/$slug
    echo "[$i/$count] $fname"
    if [ "$kind" = embed ]; then
      FID=$fid jq -n '{fileId: env.FID, includeLibraries: false, embedAssets: true}' >"$PP_TMP/body.json"
    else
      FID=$fid jq -n '{fileId: env.FID, includeLibraries: true, embedAssets: false}' >"$PP_TMP/body.json"
    fi
    pp_curl -m 900 -H 'Content-Type: application/json' -H 'Accept: text/event-stream' \
      --data-binary @"$PP_TMP/body.json" -o "$PP_TMP/sse.out" "$STACK_URL/api/rpc/command/export-binfile" ||
      { echo "export istegi basarisiz: $fname"; return 1; }
    url=$(pp_sse_end "$PP_TMP/sse.out" 2>"$PP_TMP/sse.err") || { echo "export hatasi: $fname $(cat "$PP_TMP/sse.err")"; return 1; }
    uuid=$(printf '%s' "$url" | tr -d '"' | sed 's#.*/##')
    case $uuid in
      ????????-????-????-????-????????????) ;;
      *) echo "beklenmeyen export yaniti: $fname"; return 1 ;;
    esac
    pp_curl -m 900 -o "$out" "$STACK_URL/assets/by-id/$uuid" || { echo "indirme basarisiz: $fname"; return 1; }
    chmod 600 "$out"
    [ -s "$out" ] && [ "$(head -c2 "$out")" = PK ] || { echo "indirilen dosya gecerli bir .penpot (zip) degil: $fname"; return 1; }
    sum=$(pp_sha256 "$out")
    bytes=$(wc -c <"$out" | tr -d ' ')
    NAME=$fname FID=$fid FILE=$slug SUM=$sum BYTES=$bytes \
      jq -nc '{name: env.NAME, id: env.FID, file: env.FILE, sha256: env.SUM, bytes: (env.BYTES | tonumber)}' >>"$PP_TMP/entries.jsonl"
  done
  jq -s --arg v "$(pp_version)" --arg pn "$pname" --arg pid "$pid" --arg tn "$tname" --arg k "$kind" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{format: "selfhost-penpot-export/1", penpotVersion: $v, exportedAt: $at,
      libraries: (if $k == "embed" then "embed-assets" else "include-libraries" end),
      project: {name: $pn, id: $pid, team: $tn}, files: .}' "$PP_TMP/entries.jsonl" >"$dir/manifest.json" || return 1
  chmod 600 "$dir/manifest.json"
  echo "$count dosya, proje: $pname"
  return 0
}

# $1 = dogrulanmis arsiv dizini (manifest.json + .penpot dosyalari), $2 = takim adi ("" = varsayilan), $3 = proje adi ("" = manifest)
app_import() {
  local dir=$1 team=${2:-} proj=${3:-} m=$1/manifest.json
  command -v jq >/dev/null 2>&1 || { echo "jq bulunamadi; kur ve PATH'e ekle"; return 2; }
  [ -f "$m" ] || { echo "manifest.json yok"; return 1; }
  jq -e '.format == "selfhost-penpot-export/1" and (.files | type == "array" and length > 0)' "$m" >/dev/null 2>&1 ||
    { echo "manifest.json gecersiz ya da desteklenmeyen bicim"; return 1; }
  local count i=0 f want got
  count=$(jq '.files | length' "$m")
  # 1) once TUM hash'ler (ag cagrisi yok)
  while [ "$i" -lt "$count" ]; do
    f=$(jq -r ".files[$i].file" "$m")
    want=$(jq -r ".files[$i].sha256" "$m")
    i=$((i + 1))
    case $f in
      [0-9][0-9]-*.penpot) ;;
      *) echo "manifest'te gecersiz dosya adi"; return 1 ;;
    esac
    case $f in */*|*..*) echo "manifest'te gecersiz dosya adi"; return 1 ;; esac
    [ -f "$dir/$f" ] && [ ! -L "$dir/$f" ] || { echo "dosya eksik: $f"; return 1; }
    got=$(pp_sha256 "$dir/$f")
    [ "$got" = "$want" ] || { echo "hash uyusmuyor: $f (arsiv bozuk ya da degistirilmis); hicbir sey iceri alinmadi"; return 1; }
  done
  echo "hash dogrulamasi tamam ($count dosya)"
  [ -n "$proj" ] || proj=$(jq -r '.project.name' "$m")
  [ -n "$proj" ] && [ "$proj" != null ] || { echo "proje adi yok; --project ver"; return 1; }
  pp_init || return $?
  pp_rpc get-teams >"$PP_TMP/teams.json" || { echo "takim listesi alinamadi"; pp_fail_hint; return 1; }
  local tid
  if [ -n "$team" ]; then
    tid=$(jq -r --arg t "$team" '[.[] | select(.name == $t)][0].id // empty' "$PP_TMP/teams.json")
    [ -n "$tid" ] || { echo "takim bulunamadi: $team"; return 1; }
  else
    tid=$(jq -r '([.[] | select(.isDefault == true)][0] // .[0]).id // empty' "$PP_TMP/teams.json")
    [ -n "$tid" ] || { echo "takim bulunamadi"; return 1; }
  fi
  TID=$tid pp_rpc_json get-projects '{teamId: env.TID}' >"$PP_TMP/tprojects.json" || { echo "proje listesi alinamadi"; pp_fail_hint; return 1; }
  local pid
  pid=$(jq -r --arg p "$proj" '[.[] | select(.name == $p)][0].id // empty' "$PP_TMP/tprojects.json")
  if [ -z "$pid" ]; then
    pid=$(TID=$tid PN=$proj pp_rpc_json create-project '{teamId: env.TID, name: env.PN}' | jq -r '.id // empty')
    [ -n "$pid" ] || { echo "proje olusturulamadi: $proj"; pp_fail_hint; return 1; }
    echo "proje olusturuldu: $proj"
  else
    echo "proje var, dosyalar icine eklenir: $proj (mevcut dosyalar degismez)"
  fi
  i=0
  local fname
  while [ "$i" -lt "$count" ]; do
    f=$(jq -r ".files[$i].file" "$m")
    fname=$(jq -r ".files[$i].name" "$m")
    i=$((i + 1))
    echo "[$i/$count] $fname"
    ( cd "$dir" && pp_curl -m 900 -H 'Accept: text/event-stream' \
        --form-string "name=$fname" --form-string "project-id=$pid" --form-string "version=3" \
        -F "file=@$f;type=application/octet-stream" -o "$PP_TMP/sse.out" "$STACK_URL/api/rpc/command/import-binfile" ) ||
      { echo "import istegi basarisiz: $fname"; return 1; }
    pp_sse_end "$PP_TMP/sse.out" >/dev/null 2>"$PP_TMP/sse.err" || { echo "import hatasi: $fname $(cat "$PP_TMP/sse.err" 2>/dev/null)"; return 1; }
  done
  echo "$count dosya iceri alindi"
  return 0
}
