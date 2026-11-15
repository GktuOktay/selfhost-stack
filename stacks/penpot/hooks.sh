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
