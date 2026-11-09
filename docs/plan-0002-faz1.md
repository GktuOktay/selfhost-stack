# Plan 0002 Faz 1 — BookStack dashboard

Spec: `docs/spec-0002-bookstack-dashboard.md` r5. Signature: Faz 1 approved in chat 2026-11-09 (no cryptographic signature; harness not installed in this project). Faz 2a/2b are NOT signed; nothing in this plan touches them.

## Buildable now?

- **Partly.** The folder has only `docs/`. No `stack`, no `lib/`, no `stacks/`. 0001 T-2 (BookStack compose) and T-5 (`stack` CLI) are not delivered.
- Blocked on 0001: T-1 (needs 0001 T-2), T-2 (needs 0001 T-5 + T-1), and every e2e/integration criterion (CB-1, 2, 3, 5, 6, 9, 10, 11, 30, PB-*), because they run `./stack up bookstack`.
- Buildable now (no 0001 code needed): T-A7b, T-0d, T-3, T-4 (theme folder), and the static part of T-5 (CB-7 d/e/f, CB-8, blade_scan).
- Open signature prerequisites in spec header: T-A7b, board K3 re-check, T-0d (before T-5). They gate the first slice below, not the signature itself (CEO signed anyway; delivery treats them as the first tasks).

## Smallest first slice

T-A7b (ADR-0007 sync) then T-3 (theme: `home/default` copy + include, `selfhost/home`, `cards`, `UPSTREAM`, `PHP_ALLOWLIST`, `ACCESS_ALLOWLIST`, `README`) plus the static tests `tests/blade_scan/` and `tests/upgrade_diff_check.sh` for CB-7 (d,e,f) and CB-8 (1-7). CB-8 needs only Docker and the pinned image (`lscr.io/linuxserver/bookstack:v26.09.2-ls295`, `--network none`). Then T-4 (shelf).

## Ordered tasks

| Order | Task | Owner | Depends on | Closes | Parallel |
|---|---|---|---|---|---|
| 1 | T-A7b ADR-0007 sync, board K3 re-check | software-architect | none | CB-7, 8, 30 (design) | with T-0d |
| 1 | T-0d dind licence + tag/digest pin in `tests/versions.env` | scout + devops-sre | none | CB-9 (prereq) | with T-A7b |
| 2 | T-3 theme home + cards, verify D-23 on pinned image | polyglot-engineer | T-A7b | CB-1, 3, 4, 6, 7, 8 (build) | with T-5 static part |
| 3 | T-4 theme shelf | polyglot-engineer | T-3 (same theme dir, sequential) | CB-10, 11 | with T-5 static part |
| 2-3 | T-5a static tests: blade_scan + negative fixtures, `upgrade_diff_check.sh`, CB-8 arm64+amd64, opcache | qa-engineer | T-0d, T-3 (fixtures can start from the grammar) | CB-7 d/e/f, CB-8 | with T-4 |
| BLOCKED | T-1 compose edits | devops-sre | 0001 T-2, T-A7b | CB-2, 5, 7 | with T-2 once unblocked |
| BLOCKED | T-2 `stack`/`lib` (cards, lock table, copy, `--remove-orphans`) | polyglot-engineer | 0001 T-5, T-1 | CB-1, 2, 5, 9, 30, PB-6, PB-7 | none (owns `stack`, `lib/`) |
| BLOCKED | T-5b e2e/integration + PB Faz 1 form, dind | qa-engineer | T-1, T-2, T-4 | CB-1..6, 9..11, 30, PB-1..8 | none |
| 4 | T-6 README Faz 1 | tech-comms | T-4 (final text after T-2) | CB-5, 6, 8, 30, PB-7 | with T-5b |
| 5 | T-7 appsec stop-B, internal-auditor, quality-office | appsec, internal-auditor, quality-office | T-5, T-6 | Faz 1 gate | none |

## File ownership (no conflicts)

Theme `stacks/bookstack/theme/` (T-3, T-4: sequential, one owner). `stack`, `lib/` (T-2). `compose.yaml`, `.env.example`, `local.example/` (T-1). `tests/` (T-5). `README.md` (T-6). Each path has one owner at a time.

## Critical path

T-A7b, T-3, T-4, [0001 T-2/T-5 delivery], T-1, T-2, T-5b, T-7. The 0001 delivery is the long pole and outside this plan.

## Merge and gates

Task PRs go to `integration/0002-faz1`; merge needs audit CLEAN and green CI. Integration to `main` is the CEO's. Estimates (information only, KR-7): 9.5 h Faz 1 plus 0.5 h pre-sign tasks. No time or token ceiling; money 0.

## Open items

- Cryptographic signature: not applicable here (no `harness/`); chat approval recorded in the spec.
- 0001 T-11 (branch protection, 2FA) unverified, so M-1 stays unused (spec Assumptions).
- Issues not opened: no git repo/remote in this folder. Open them once a repo exists.
