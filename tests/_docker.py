"""Docker helpers for the static tests (spec 0002 CB-7/CB-8). Stdlib only.

Every container runs with --network none, --rm and a `t3-` name prefix.
Nothing here pulls an image: the pinned image must already be local.
"""
import os
import re
import subprocess
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = os.path.join(REPO, "stacks", "bookstack", "theme", "selfhost-dashboard")


def pinned_image(theme=THEME):
    """BOOKSTACK_IMAGE value from the theme's UPSTREAM (tag@digest)."""
    with open(os.path.join(theme, "UPSTREAM"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("BOOKSTACK_IMAGE="):
                return line.rstrip("\n").split("=", 1)[1]
    raise RuntimeError("no BOOKSTACK_IMAGE in UPSTREAM")


def run(image, args, mounts=(), entrypoint=None, platform=None, timeout=300):
    """docker run --rm --network none; mounts are (host, container) pairs, read-only."""
    name = "t3-" + uuid.uuid4().hex[:10]
    cmd = ["docker", "run", "--rm", "--name", name, "--network", "none",
           "--read-only", "--tmpfs", "/tmp"]
    if platform:
        cmd += ["--platform", platform]
    for host, cont in mounts:
        cmd += ["-v", f"{host}:{cont}:ro"]
    if entrypoint:
        cmd += ["--entrypoint", entrypoint]
    cmd.append(image)
    cmd += list(args)
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout)
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)


def cat_in_image(image, path, platform=None):
    """Raw bytes of a file inside the image (the CB-8 (2) command)."""
    p = run(image, [path], entrypoint="cat", platform=platform)
    if p.returncode != 0:
        raise RuntimeError(f"cat {path} failed: {p.stderr.decode(errors='replace')[:200]}")
    return p.stdout
