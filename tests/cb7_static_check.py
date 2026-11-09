#!/usr/bin/env python3
"""CB-7 static parts (spec 0002): (d) theme file set, (e) two-stage Blade scan, (f) '/'-strings.

  (d) theme file set == UPSTREAM ALLOW list (meta files included); no functions.php; no public/
  (e) selfhost/ partials pass the two-stage scan; every rule has a negative fixture the scanner catches
  (f) string constants that start with '/' are only '/books'

(a), (b), (c), (g), (h) need a running BookStack and belong to the integration suite (blocked on the
stack CLI). Stdlib only; (e) runs scan.php inside the pinned image with --network none.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "blade_scan"))
import _docker  # noqa: E402
import blade_scan  # noqa: E402
import cb8_upstream_check as cb8  # noqa: E402


def check_d(theme):
    errors = []
    with open(os.path.join(theme, "UPSTREAM"), encoding="utf-8") as f:
        up, perr = cb8.parse_upstream(f.read())
    if perr:
        return perr
    errors += cb8.check_allow_equal(theme, up)
    for root, dirs, files in os.walk(theme):
        for d in dirs:
            if d == "public":
                errors.append("forbidden directory: " + os.path.relpath(os.path.join(root, d), theme))
        for n in files:
            if n.lower() == "functions.php":
                errors.append("forbidden file: " + os.path.relpath(os.path.join(root, n), theme))
    return errors


_STR = re.compile(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*\"""", re.S)


def check_f(theme):
    errors = []
    sdir = os.path.join(theme, "selfhost")
    for root, _dirs, files in os.walk(sdir):
        for n in sorted(files):
            p = os.path.join(root, n)
            with open(p, encoding="utf-8") as f:
                text = f.read()
            text = re.sub(r"\{\{--.*?--\}\}", "", text, flags=re.S)
            for m in _STR.finditer(text):
                val = m.group(0)[1:-1]
                if val.startswith("/") and val != "/books":
                    errors.append(f"{os.path.relpath(p, theme)}: string constant {m.group(0)[:40]} starts with '/'")
    return errors


def check_e(theme=_docker.THEME):
    return blade_scan.check_results(blade_scan.scan(theme))


def main():
    failed = False
    for label, res in (("(d) file set, no functions.php/public", check_d(_docker.THEME)),
                       ("(e) two-stage Blade scan + negative fixtures", check_e()),
                       ("(f) '/'-strings only '/books'", check_f(_docker.THEME))):
        if res:
            failed = True
            print("FAIL  CB-7 " + label)
            for e in res:
                print("        " + e)
        else:
            print("PASS  CB-7 " + label)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
