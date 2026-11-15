# shellcheck shell=bash
# stacks/plane/hooks.sh: Plane v1.4.3 hooks (contract: header of ./stack). Function definitions only.
#
# Upstream research (makeplane/plane tag v1.4.3, read from source, not run):
#  * Registration switch: env ENABLE_SIGNUP (apps/api/plane/utils/instance_config_variables/core.py,
#    default "1"). It is only SEEDED into the DB InstanceConfiguration on first start
#    (configure_instance uses get_or_create, so later env changes are ignored); afterwards it
#    is changed in god-mode UI. compose sets ENABLE_SIGNUP=0. The first instance admin is created via
#    /god-mode/ (InstanceAdminSignUpEndpoint), which does not read ENABLE_SIGNUP, so it still works.
#    NOT verified live: whether workspace members can still be invited/sign up with signup=0 (T-8).
#  * Admin-claim flag: GET /api/instances/ -> {"instance": {"is_setup_done": bool, ...}}; set true
#    inside the admin sign-up transaction, response cache is invalidated on sign-up. Public endpoint.
#  * Telemetry: no env switch upstream. Metrics push is gated by DB flag Instance.is_telemetry_enabled
#    (default true, changed only in god-mode UI) and goes to OTLP_ENDPOINT. Not disabled by compose.
#    Mitigation: all Plane app containers are on the internal network (no route out), so the push
#    cannot leave the host (not verified live).

plane_instances_json() {
  curl -fsS -m 5 "${STACK_URL}/api/instances/" 2>/dev/null
}

app_health() {
  # -L follows redirects; -f fails on >=400; final status must be 200 with non-empty body.
  local code
  code=$(curl -sS -L -m 5 -o /dev/null -w '%{http_code}' "${STACK_URL}/" 2>/dev/null) || return 1
  [ "$code" = 200 ] || return 1
  # web answers before api is ready; the gate needs the api, so health requires /api/instances/ too.
  plane_instances_json >/dev/null
}

# 0 = claimed, 1 = not claimed, 2 = unknown (API unreachable / unexpected body)
plane_admin_state() {
  local body
  body=$(plane_instances_json) || return 2
  case $body in
    *'"is_setup_done":true'*|*'"is_setup_done": true'*) return 0 ;;
    *'"is_setup_done":false'*|*'"is_setup_done": false'*) return 1 ;;
  esac
  return 2
}

app_gate() {
  plane_admin_state
  case $? in
    0) return 0 ;;
    1)
      printf 'Plane instance admin talep edilmedi. Tarayicida %s/god-mode/ acip admin hesabini olustur, sonra ./stack up plane tekrar.\n' "$STACK_URL"
      return 6
      ;;
  esac
  printf 'Plane /api/instances/ okunamadi.\n'
  return 5
}

app_status_extra() {
  plane_admin_state
  case $? in
    0) printf 'plane-admin: claimed\n' ;;
    1) printf 'plane-admin: unclaimed (%s/god-mode/)\n' "$STACK_URL" ;;
    *) printf 'plane-admin: unknown\n' ;;
  esac
}

# $1 = target dir (700, already open). db.sql + uploads.tar (600). DB password never on argv:
# pg_dump uses the local unix socket inside plane-db and PGPASSWORD from the container env.
# uploads.tar: first `tar` in the app image (plane-minio = silo, volume uploads:/export);
# fallback (only if silo has no tar): the already-present plane-db image (busybox tar), volume
# mounted read-only, no network, no new image. NOT verified live (T-8): whether silo ships tar.
app_backup() {
  local dir=$1 cid img
  stack_compose exec -T plane-db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h /var/run/postgresql -U "$POSTGRES_USER" "$POSTGRES_DB"' \
    >"$dir/db.sql" || { echo "db dump basarisiz"; return 1; }
  [ -s "$dir/db.sql" ] || { echo "db.sql bos"; return 1; }
  if ! stack_compose exec -T plane-minio tar -C /export -cf - . >"$dir/uploads.tar" 2>/dev/null \
    || [ ! -s "$dir/uploads.tar" ]; then
    echo "plane-minio icinde tar yok/basarisiz; plane-db image'i ile yedekleniyor"
    cid=$(stack_compose ps -q plane-db 2>/dev/null | head -n 1)
    [ -n "$cid" ] || { echo "plane-db container bulunamadi"; return 1; }
    img=$(docker inspect --format '{{.Image}}' "$cid" 2>/dev/null)
    [ -n "$img" ] || { echo "plane-db image'i okunamadi"; return 1; }
    docker run --rm --network none -v "${STACK_PROJECT}_uploads:/export:ro" --entrypoint tar "$img" \
      -C /export -cf - . >"$dir/uploads.tar" || { echo "uploads tar basarisiz"; return 1; }
  fi
  [ -s "$dir/uploads.tar" ] || { echo "uploads.tar bos"; return 1; }
  chmod 600 "$dir/db.sql" "$dir/uploads.tar"
  tar -tf "$dir/uploads.tar" >/dev/null || { echo "uploads.tar okunamadi"; return 1; }
  return 0
}
