# stacks/bookstack/hooks.sh (selfhost-stack, spec 0001 rev 1, T-2)
# Yalnız fonksiyon tanımlar (sözleşme: ./stack başlığı). bash 3.2 uyumlu.
#
# Doğrulandı (image lscr.io/linuxserver/bookstack:v26.09.2-ls295, kaynak okuma, 2026-11-15):
#   - app/Console/Commands/CreateAdminCommand.php imzası:
#       bookstack:create-admin {--email=} {--name=} {--password=} {--external-auth-id=}
#                              {--generate-password} {--initial}
#     `--initial`: admin@admin.com varsa onu verilen e-posta/parola ile günceller (çıkış 0);
#     varsayılan yok ve başka bir admin varsa atlar (çıkış 2); hiç admin yoksa oluşturur (0).
#     Parola min 8 karakter (Password::default()).
#   - APP_KEY: config 'cipher' => 'AES-256-CBC' => `base64:` + base64(32 bayt) (44 karakter).
#   - Migration, admin@admin.com / `password` kullanıcısını ekler; probe bunu sayar.
#   - Image'da /bin/tar ve (mariadb image'ında) mariadb-dump vardır.
# Doğrulanmadı (canlı çalıştırma T-8): artisan çıktısı/çıkış kodları gerçek DB ile.
# Parola notu: parola container ortamından okunur; ARGV'de yalnız container içindeki php
# işleminde görünür (host `ps`te görünmez).

_bs_artisan() {
  stack_compose exec -T -u abc bookstack php /app/www/artisan "$@"
}

app_health() {
  local code
  code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$STACK_URL/status" 2>/dev/null) || return 1
  [ "$code" = "200" ]
}

# stdout: varsayılan kullanıcı sayısı; dönüş 0 = sorgu çalıştı
_bs_default_count() {
  local out
  out=$(stack_compose exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -N -u"$MARIADB_USER" "$MARIADB_DATABASE" -e "SELECT COUNT(*) FROM users WHERE email='"'"'admin@admin.com'"'"'"' 2>/dev/null) || return 1
  out=$(printf '%s' "$out" | tr -d '[:space:]')
  case $out in
    ''|*[!0-9]*) return 1 ;;
  esac
  printf '%s' "$out"
}

# İdempotent: varsayılan admin'i .env e-posta/parolasıyla değiştirir; ikinci çalıştırmada
# (varsayılan yok, başka admin var) artisan 2 döner = zaten kurulu.
app_bootstrap() {
  local rc
  stack_compose exec -T -u abc bookstack sh -c \
    'php /app/www/artisan bookstack:create-admin --initial --name=Admin --email="$BOOKSTACK_ADMIN_EMAIL" --password="$BOOKSTACK_ADMIN_PASSWORD"' \
    >/dev/null 2>&1
  rc=$?
  case $rc in
    0|2) return 0 ;;
  esac
  echo "bookstack:create-admin çıkış kodu $rc"
  return 1
}

app_gate() {
  local n
  n=$(_bs_default_count) || { echo "varsayılan giriş probu çalışmadı"; return 5; }
  if [ "$n" = "0" ]; then
    return 0
  fi
  echo "BookStack'te upstream varsayılan kullanıcı (admin@admin.com) duruyor; elle sil ya da e-postasını değiştir."
  return 6
}

app_status_extra() {
  local n
  if n=$(_bs_default_count); then
    if [ "$n" = "0" ]; then
      echo "default-login: no"
    else
      echo "default-login: YES (UYARI)"
    fi
  else
    echo "default-login: unknown"
  fi
}

app_up_note() {
  echo "admin: $(stack_env BOOKSTACK_ADMIN_EMAIL) (parola: BOOKSTACK_ADMIN_PASSWORD, local/.env)"
}

# $1 = hedef dizin (700, önceden açık). db.sql + config.tar (600).
app_backup() {
  local dir=$1
  stack_compose exec -T db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb-dump --single-transaction -u"$MARIADB_USER" "$MARIADB_DATABASE"' \
    >"$dir/db.sql" || { echo "db dump başarısız"; return 1; }
  [ -s "$dir/db.sql" ] || { echo "db.sql boş"; return 1; }
  # Tema bind mount'u git'te; yedeğe girmez.
  stack_compose exec -T bookstack tar -cf - -C /config --exclude=./www/themes/selfhost-dashboard . \
    >"$dir/config.tar" || { echo "config tar başarısız"; return 1; }
  [ -s "$dir/config.tar" ] || { echo "config.tar boş"; return 1; }
  chmod 600 "$dir/db.sql" "$dir/config.tar"
  tar -tf "$dir/config.tar" >/dev/null || { echo "config.tar okunamadı"; return 1; }
  return 0
}
