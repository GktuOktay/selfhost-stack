#!/bin/sh
# M-1 (a), spec 0002 section 6.1: mechanical check of a normal BookStack bump PR.
#
#   tests/upgrade_diff_check.sh <base-ref> <head-ref>      (run inside the repository)
#
# Passes only if the diff from merge-base(base, head) to head
#   - touches exactly two files: stacks/bookstack/versions.env and the theme's UPSTREAM
#   - changes exactly one line in each (1 deletion + 1 addition), no mode change, no rename
#   - replaces the BookStack app image line in versions.env and the BOOKSTACK_IMAGE= line in UPSTREAM
#   - makes both new values byte-identical and of the form name:tag@sha256:<64 hex> (tag not floating)
# It reads git objects only, never the working tree.
#
# It must run from the BASE branch's copy, never from the PR head: the script refuses to run when its
# own bytes differ from `git show <base>:tests/upgrade_diff_check.sh` (exit 2).
#
# Exit: 0 pass, 1 check failed, 2 usage / guard / git error.
#
# ASSUMPTION: the key of the BookStack app image line in versions.env is BOOKSTACK_IMAGE (0001 T-1 is
# not delivered yet). Change VERSIONS_KEY here, in the base branch, when T-1 fixes the name.
set -u

VERSIONS_KEY=BOOKSTACK_IMAGE
VERSIONS_FILE=stacks/bookstack/versions.env
UPSTREAM_FILE=stacks/bookstack/theme/selfhost-dashboard/UPSTREAM
UPSTREAM_KEY=BOOKSTACK_IMAGE
SELF_REL=tests/upgrade_diff_check.sh

usage() { echo "usage: $0 <base-ref> <head-ref>" >&2; exit 2; }
fail() { echo "FAIL: $*" >&2; exit 1; }
die() { echo "ERROR: $*" >&2; exit 2; }

[ $# -eq 2 ] || usage
base=$1
head=$2

git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"
git rev-parse --verify --quiet "$base^{commit}" >/dev/null || die "unknown base ref: $base"
git rev-parse --verify --quiet "$head^{commit}" >/dev/null || die "unknown head ref: $head"
mb=$(git merge-base "$base" "$head") || die "no merge base for $base and $head"

# Guard: run the base branch's script, not the PR's.
if ! git show "$base:$SELF_REL" 2>/dev/null | cmp -s - "$0"; then
  die "this script differs from $base:$SELF_REL; run the base branch's copy, never the PR head's"
fi

# 1. exactly two files, plain modifications of regular files
want=$(printf '%s\n%s' "$UPSTREAM_FILE" "$VERSIONS_FILE" | LC_ALL=C sort)
got=$(git diff --no-renames --name-only "$mb" "$head" | LC_ALL=C sort)
[ "$got" = "$want" ] || fail "diff must touch exactly $VERSIONS_FILE and $UPSTREAM_FILE; it touches: $(printf '%s' "$got" | tr '\n' ' ')"

raw=$(git diff --no-renames --raw "$mb" "$head")
echo "$raw" | while IFS= read -r l; do
  case "$l" in
    ":100644 100644 "*" M	"*) ;;
    *) echo "FAIL: not a plain modification of a regular file: $l" >&2; exit 1 ;;
  esac
done || exit 1

# 2. one line changed in each file
git diff --no-renames --numstat "$mb" "$head" | while IFS='	' read -r a d p; do
  [ "$a" = "1" ] && [ "$d" = "1" ] || { echo "FAIL: $p must change exactly one line (+$a -$d)" >&2; exit 1; }
done || exit 1

# 3. the changed line is the image line, and extract the new values
changed() { # file key -> prints "old<TAB>new" values
  f=$1; k=$2
  d=$(git diff --no-renames -U0 "$mb" "$head" -- "$f")
  minus=$(printf '%s\n' "$d" | grep '^-' | grep -v '^---' || true)
  plus=$(printf '%s\n' "$d" | grep '^+' | grep -v '^+++' || true)
  case "$minus" in "-$k="*) ;; *) echo "FAIL: $f: the removed line is not $k=..." >&2; return 1 ;; esac
  case "$plus" in "+$k="*) ;; *) echo "FAIL: $f: the added line is not $k=..." >&2; return 1 ;; esac
  [ "$(printf '%s\n' "$minus" | wc -l)" -eq 1 ] && [ "$(printf '%s\n' "$plus" | wc -l)" -eq 1 ] || { echo "FAIL: $f: more than one line changed" >&2; return 1; }
  printf '%s\n' "${plus#+$k=}"
}
vnew=$(changed "$VERSIONS_FILE" "$VERSIONS_KEY") || exit 1
unew=$(changed "$UPSTREAM_FILE" "$UPSTREAM_KEY") || exit 1

# 4. the new values (read from the head commit's blobs) are the changed lines, identical, tag + digest
vhead=$(git show "$head:$VERSIONS_FILE" | grep "^$VERSIONS_KEY=" | sed "s/^$VERSIONS_KEY=//")
uhead=$(git show "$head:$UPSTREAM_FILE" | grep "^$UPSTREAM_KEY=" | sed "s/^$UPSTREAM_KEY=//")
[ "$(git show "$head:$VERSIONS_FILE" | grep -c "^$VERSIONS_KEY=")" -eq 1 ] || fail "$VERSIONS_FILE: $VERSIONS_KEY must appear exactly once"
[ "$(git show "$head:$UPSTREAM_FILE" | grep -c "^$UPSTREAM_KEY=")" -eq 1 ] || fail "$UPSTREAM_FILE: $UPSTREAM_KEY must appear exactly once"
[ "$vhead" = "$vnew" ] && [ "$uhead" = "$unew" ] || fail "changed line does not match the head file content"
[ "$vnew" = "$unew" ] || fail "new values differ between versions.env and UPSTREAM"

printf '%s' "$vnew" | grep -Eq '^[a-z0-9][a-z0-9./_-]*:[A-Za-z0-9_][A-Za-z0-9._-]{0,127}@sha256:[0-9a-f]{64}$' \
  || fail "new value is not name:tag@sha256:<64 hex>: $vnew"
tag=${vnew#*:}; tag=${tag%%@*}
case "$tag" in latest|stable|main|develop|preview) fail "floating tag: $tag" ;; esac

echo "PASS: mechanical bump check (M-1 a) for $base..$head: $vnew"
exit 0
