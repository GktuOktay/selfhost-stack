#!/usr/bin/env python3
"""CB-8 (spec 0002 section 6.1): upstream compatibility of the selfhost-dashboard theme.

Checks (numbers as in the spec):
  (1) UPSTREAM obeys the grammar; BOOKSTACK_IMAGE equals the image value from the normalized config
  (2) every VIEW line: sha256 of the original inside the pinned image (docker --network none, cat)
  (3) override vs original: raw-byte line diff has no deleted/changed line; every added line is an @include
  (4) theme file set == ALLOW set (meta files included)
  (5) no VIEW lines is valid; (2) and (3) are then skipped
  (6) every non-selfhost/, non-meta ALLOW path has a VIEW line and every VIEW line has an ALLOW line
  (7) opcache.validate_timestamps == 1, revalidate_freq <= 2, no override in php-fpm pool / ini files

Stdlib only. Usage:
  cb8_upstream_check.py [--theme DIR] [--config-image REF] [--platform P ...] [--skip-image]
"""
import argparse
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docker  # noqa: E402

META = ("UPSTREAM", "PHP_ALLOWLIST", "ACCESS_ALLOWLIST", "README")
_REL = r"[A-Za-z0-9][A-Za-z0-9._/-]*"
_INCLUDE = re.compile(rb"^[ \t]*@include\('selfhost\.[a-z0-9_.-]{1,64}'\)[ \t]*$")


class Upstream:
    def __init__(self):
        self.image = None
        self.view_root = None
        self.views = {}   # relative path -> sha256 hex
        self.allow = []   # relative paths, in order


def _safe_rel(p):
    return re.fullmatch(_REL, p) is not None and ".." not in p.split("/") and not p.endswith("/") and "//" not in p


def parse_upstream(text):
    """Return (Upstream, [errors]). The spec grammar is closed: anything else is an error."""
    up = Upstream()
    errors = []
    images = roots = 0
    for n, line in enumerate(text.split("\n"), 1):
        if n == len(text.split("\n")) and line == "":
            continue  # trailing newline
        if line.strip() == "" and "\r" not in line:
            continue
        if line.startswith("#"):
            continue
        if "\r" in line:
            errors.append(f"UPSTREAM:{n}: carriage return")
            continue
        m = re.fullmatch(r"BOOKSTACK_IMAGE=(\S+)", line)
        if m:
            images += 1
            up.image = m.group(1)
            continue
        m = re.fullmatch(r"VIEW_ROOT=(/\S*)", line)
        if m:
            roots += 1
            up.view_root = m.group(1)
            continue
        m = re.fullmatch(r"VIEW (\S+) ([0-9a-f]{64})", line)
        if m and _safe_rel(m.group(1)):
            if m.group(1) in up.views:
                errors.append(f"UPSTREAM:{n}: duplicate VIEW {m.group(1)}")
            up.views[m.group(1)] = m.group(2)
            continue
        m = re.fullmatch(r"ALLOW (\S+)", line)
        if m and _safe_rel(m.group(1)):
            if m.group(1) in up.allow:
                errors.append(f"UPSTREAM:{n}: duplicate ALLOW {m.group(1)}")
            up.allow.append(m.group(1))
            continue
        errors.append(f"UPSTREAM:{n}: unknown or malformed line: {line[:60]!r}")
    if images != 1:
        errors.append(f"UPSTREAM: BOOKSTACK_IMAGE must appear exactly once (found {images})")
    if roots != 1:
        errors.append(f"UPSTREAM: VIEW_ROOT must appear exactly once (found {roots})")
    if not up.allow:
        errors.append("UPSTREAM: at least one ALLOW line is required")
    return up, errors


def check_image_equal(up, config_value):
    if up.image != config_value:
        return [f"BOOKSTACK_IMAGE {up.image!r} != configured image {config_value!r}"]
    return []


def check_raw_diff(orig, override):
    """(3): override == orig plus added @include lines, compared on raw bytes."""
    a = orig.split(b"\n")
    b = override.split(b"\n")
    j = 0
    errors = []
    for n, line in enumerate(b, 1):
        if j < len(a) and line == a[j]:
            j += 1
        elif _INCLUDE.match(line):
            continue
        else:
            errors.append(f"override line {n} is neither the next upstream line nor an @include: {line[:60]!r}")
            return errors
    if j != len(a):
        errors.append(f"upstream line {j + 1} missing in the override (deleted or changed): {a[j][:60]!r}")
    return errors


def check_views(theme, up, fetch, platforms=(None,)):
    """(2)+(3). fetch(relative_path, platform) -> bytes of the original in the pinned image."""
    errors = []
    for rel, want in sorted(up.views.items()):
        path = os.path.join(theme, *rel.split("/"))
        if not os.path.isfile(path):
            errors.append(f"VIEW {rel}: override file missing in the theme")
            continue
        with open(path, "rb") as f:
            override = f.read()
        for plat in platforms:
            try:
                orig = fetch(rel, plat)
            except Exception as e:  # docker failure is a failure, not a skip
                errors.append(f"VIEW {rel} [{plat or 'native'}]: cannot read original: {e}")
                continue
            got = hashlib.sha256(orig).hexdigest()
            if got != want:
                errors.append(f"VIEW {rel} [{plat or 'native'}]: sha256 {got} != UPSTREAM {want}")
                continue
            errors += [f"{rel} [{plat or 'native'}]: {e}" for e in check_raw_diff(orig, override)]
    return errors


def theme_files(theme):
    files, bad = set(), []
    for root, dirs, names in os.walk(theme):
        for d in list(dirs):
            if os.path.islink(os.path.join(root, d)):
                bad.append(os.path.relpath(os.path.join(root, d), theme))
                dirs.remove(d)
        for nme in names:
            p = os.path.join(root, nme)
            rel = os.path.relpath(p, theme).replace(os.sep, "/")
            if os.path.islink(p) or not os.path.isfile(p):
                bad.append(rel)
            else:
                files.add(rel)
    return files, bad


def check_allow_equal(theme, up):
    """(4)"""
    files, bad = theme_files(theme)
    errors = [f"not a regular file: {b}" for b in bad]
    allow = set(up.allow)
    errors += [f"in theme but not in ALLOW: {f}" for f in sorted(files - allow)]
    errors += [f"in ALLOW but not in theme: {f}" for f in sorted(allow - files)]
    return errors


def check_view_allow_mapping(up):
    """(6)"""
    errors = []
    for rel in up.allow:
        if rel in META or rel.startswith("selfhost/"):
            continue
        if rel not in up.views:
            errors.append(f"ALLOW {rel} has no VIEW line")
    for rel in up.views:
        if rel not in up.allow:
            errors.append(f"VIEW {rel} has no ALLOW line")
    return errors


_POOL = re.compile(r"^(php_admin_value|php_value|php_admin_flag|php_flag)\s*\[\s*opcache\.(validate_timestamps|revalidate_freq)\s*\]\s*=", re.I)
_INI = re.compile(r"^opcache\.(validate_timestamps|revalidate_freq)\s*=", re.I)


def check_opcache(values, texts):
    """(7) values: effective ini values; texts: {path: file text} of fpm pool / conf.d files."""
    errors = []
    v = values.get("opcache.validate_timestamps")
    if v != "1":
        errors.append(f"opcache.validate_timestamps is {v!r}, must be '1'")
    f = values.get("opcache.revalidate_freq")
    try:
        if f is None or not (0 <= int(f) <= 2):
            errors.append(f"opcache.revalidate_freq is {f!r}, must be 0..2")
    except ValueError:
        errors.append(f"opcache.revalidate_freq is {f!r}, must be 0..2")
    for path, text in sorted(texts.items()):
        for n, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if not s or s[0] in ";#":
                continue
            if _POOL.match(s) or _INI.match(s):
                errors.append(f"{path}:{n}: overrides an opcache revalidation setting: {s[:80]}")
    return errors


def gather_opcache(image, platform=None):
    code = ('foreach (["opcache.validate_timestamps","opcache.revalidate_freq"] as $k) '
            'echo $k, "=", ini_get($k), "\\n";')
    p = _docker.run(image, ["-r", code], entrypoint="php", platform=platform)
    if p.returncode != 0:
        raise RuntimeError("php -r failed: " + p.stderr.decode(errors="replace")[:200])
    values = {}
    for line in p.stdout.decode().splitlines():
        k, _, v = line.partition("=")
        values[k] = v
    script = ('for f in /etc/php85/php-fpm.conf /etc/php85/php-fpm.d/*.conf /etc/php85/conf.d/*.ini; do '
              '[ -f "$f" ] && { echo "@@@FILE@@@ $f"; cat "$f"; echo; }; done')
    p = _docker.run(image, ["-c", script], entrypoint="sh", platform=platform)
    if p.returncode != 0:
        raise RuntimeError("reading php-fpm config failed: " + p.stderr.decode(errors="replace")[:200])
    texts, cur = {}, None
    for line in p.stdout.decode(errors="replace").split("\n"):
        if line.startswith("@@@FILE@@@ "):
            cur = line[len("@@@FILE@@@ "):]
            texts[cur] = ""
        elif cur is not None:
            texts[cur] += line + "\n"
    if not texts:
        raise RuntimeError("no php-fpm config files found in the image")
    return values, texts


def run_all(theme, config_image=None, platforms=(None,), image=None, skip_image=False):
    results = []  # (label, [errors] | "SKIPPED: reason")
    with open(os.path.join(theme, "UPSTREAM"), encoding="utf-8") as f:
        text = f.read()
    up, errs = parse_upstream(text)
    results.append(("(1) UPSTREAM grammar", errs))
    if errs:
        return results
    if config_image is None:
        results.append(("(1) BOOKSTACK_IMAGE == normalized config", "SKIPPED: no --config-image (stack CLI not delivered yet)"))
    else:
        results.append(("(1) BOOKSTACK_IMAGE == normalized config", check_image_equal(up, config_image)))
    image = image or up.image
    if skip_image:
        results.append(("(2)(3)(7) image checks", "SKIPPED: --skip-image"))
    else:
        if not up.views:
            results.append(("(2)(3) VIEW sha256 + raw diff", "SKIPPED: no VIEW lines (5)"))
        else:
            fetch = lambda rel, plat: _docker.cat_in_image(image, up.view_root + "/" + rel, plat)  # noqa: E731
            results.append(("(2)(3) VIEW sha256 + raw diff [%s]" % ",".join(p or "native" for p in platforms),
                            check_views(theme, up, fetch, platforms)))
        try:
            values, texts = gather_opcache(image, platforms[0])
            results.append(("(7) opcache", check_opcache(values, texts)))
        except Exception as e:
            results.append(("(7) opcache", [str(e)]))
    results.append(("(4) file set == ALLOW", check_allow_equal(theme, up)))
    results.append(("(6) VIEW <-> ALLOW", check_view_allow_mapping(up)))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", default=_docker.THEME)
    ap.add_argument("--config-image", default=None)
    ap.add_argument("--platform", action="append", default=None,
                    help="e.g. linux/arm64, linux/amd64 (the image for it must be local; nothing is pulled here)")
    ap.add_argument("--skip-image", action="store_true")
    a = ap.parse_args(argv)
    results = run_all(a.theme, a.config_image, tuple(a.platform) if a.platform else (None,), skip_image=a.skip_image)
    failed = False
    for label, res in results:
        if isinstance(res, str):
            print(f"SKIP  {label}: {res}")
        elif res:
            failed = True
            print(f"FAIL  {label}")
            for e in res:
                print(f"        {e}")
        else:
            print(f"PASS  {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
