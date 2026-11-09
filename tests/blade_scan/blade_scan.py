"""Runs tests/blade_scan/scan.php inside the pinned BookStack image (--network none)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _docker  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Every rule of spec section 6.1 (stage 1 + stage 2) must have at least one negative fixture.
REQUIRED_RULES = [
    "php-open-tag", "raw-echo", "directive-not-allowed", "include-pattern", "var-not-allowed",
    "variable-variable", "member-not-allowed", "static-access", "array-access", "brace-access",
    "interpolation", "assignment", "foreach-source", "call-not-allowed", "call-nonname",
    "closure", "env-arg", "forbidden-call", "forbidden-construct", "slash-string",
    "constant-not-allowed", "token-not-allowed", "unterminated-echo",
    "html-script", "html-onattr", "html-base", "html-meta-http-equiv", "html-form",
    "html-iframe", "html-object", "html-embed", "html-link", "html-javascript",
    "html-src", "html-style",
    "s2-env-misuse", "s2-unbalanced",
]


def expected_rule(path):
    """Negative fixtures are named <rule>--<description>.<ext>."""
    return os.path.basename(path).split("--", 1)[0]


def check_results(results):
    """Return a list of problems: theme partial violations, uncaught negative fixtures, flagged positives,
    rules without a fixture."""
    problems = []
    for k, v in sorted(results.items()):
        rules = {e["rule"] for e in v}
        if k.startswith("/theme/selfhost/") or "/fixtures/pos/" in k:
            if v:
                problems.append(f"{k}: unexpected violations {sorted(rules)}")
        elif "/fixtures/neg/" in k or "/fixtures/stage2/" in k:
            if expected_rule(k) not in rules:
                problems.append(f"{os.path.basename(k)}: expected {expected_rule(k)}, got {sorted(rules)}")
    have = {expected_rule(k) for k in results if "/fixtures/neg/" in k or "/fixtures/stage2/" in k}
    problems += [f"no negative fixture for rule {r}" for r in REQUIRED_RULES if r not in have]
    names = {os.path.basename(k) for k in results if k.startswith("/theme/selfhost/")}
    problems += [f"theme partial missing: {n}" for n in ("home.blade.php", "cards.blade.php", "shelf.blade.php") if n not in names]
    return problems


def scan(theme=_docker.THEME, fixtures=True, extra_dirs=()):
    """Return {path-relative-to-mount: [{stage, rule, detail}]} for theme partials and fixtures."""
    mounts = [(HERE, "/scan"), (theme, "/theme")]
    args = ["/scan/scan.php", "/theme", "/theme/selfhost"]
    if fixtures:
        args += ["/scan/fixtures"]
    for i, d in enumerate(extra_dirs):
        mounts.append((d, f"/extra{i}"))
        args.append(f"/extra{i}")
    p = _docker.run(_docker.pinned_image(theme), args, mounts=mounts, entrypoint="php")
    out = p.stdout.decode()
    try:
        data = json.loads(out)
    except ValueError:
        raise RuntimeError("scan.php produced no JSON: rc=%s out=%r err=%r" %
                           (p.returncode, out[:300], p.stderr.decode(errors="replace")[:300]))
    if data.get("config_error"):
        raise RuntimeError("scan.php config error: " + data["config_error"])
    return data["results"]


if __name__ == "__main__":
    res = scan()
    bad = {k: v for k, v in res.items() if "/fixtures/neg/" not in k and "/fixtures/stage2/" not in k and v}
    print(json.dumps(bad, indent=1))
    sys.exit(1 if bad else 0)
