Capacity report: Spec 0001 selfhost-stack | Date: 2026-11-09 | Data: n=0 scorecards

Capacity opinion (for a spec): MISSING ESTIMATE (partial) / cannot be sanity-checked — insufficient data (n=0)
- The spec has a time ceiling: "12 saat ajan çalışma süresi (T-0..T-9)" (spec.md line 7; §14 S-5). It is a proposal, not a CEO-approved value.
- The spec has NO token ceiling and NO money ceiling (spec.md line 7, scorecard row line 346: only "12 saat"). No quota statement from the CEO is available. Token and money are "not verified".
- The estimate is a single total. It has no per-task or per-unit split, so the load per unit cannot be computed from it.
- There are no scorecards: searched `/Users/goktugoktay/Desktop/ClaudeAgencyV2/**/scorecards/*.md` and `/Users/goktugoktay/Desktop/Projects/selfhost-stack/**`; the only file in the project is `docs/spec.md`. So the playbook's 1.5x / 3x test (optimistic / inflated) cannot be run. I do not label 12 h "optimistic" or "inflated"; no data.
- Judgment (not data, only reading the task list): the ceiling is not provably unrealistic, but the following risks point to an overrun. Because of this I do not give a "FITS".

Task owners (spec §12) and load per unit (counted from the task list)
| Unit | Tasks | Note |
|---|---|---|
| devops-sre | T-1, T-2, T-3, T-4 (4) | Has Bash. Docker/Compose is its core area. Owner fit is good. |
| polyglot-engineer | T-5, T-6 (2, both on the single `stack` file) | Highest load and sits on the critical path. |
| qa-engineer | T-7 (1, but covers 15 AC + gate G-1) | Heavy: 6+ e2e tests, clean machine/VM, two-machine scenario. |
| scout | T-0 (1) | Has WebSearch/WebFetch. Right owner. |
| business-analyst | T-0 revision | Small. |
| tech-comms | T-8 (1) | Small. |
| appsec, internal-auditor, quality-office | T-9 (1 chain, 3 units) | Sequential; cost not separated in the estimate. |

Critical path (from the dependency column): T-0 → T-1 → (T-5 ∥ T-2..4) → T-6 → T-7 → T-8/T-9. T-5 and T-6 both write `stack`, so they are serial; T-7 waits for all. Parallelism is limited, so 12 h is closer to the serial total than a parallel one.

Required expertise and coverage
| Area | Covering unit/playbook | Status |
|---|---|---|
| Docker Compose, overlay, `!override` merge, healthcheck | devops-sre | present |
| bash 3.2 CLI (set -euo pipefail, shellcheck, macOS/Linux portability) | polyglot-engineer (agent description: foreign stacks/migration; bash is not named) | partial |
| Penpot / Plane / BookStack upstream details (F-1..F-9, tags, MinIO risk) | scout (T-0) | present, but F-1..F-9 are all "not verified" |
| DB backup/restore: mariadb-dump, pg_dump, volume tar, restore consistency | devops-sre (backup/DR plan), polyglot-engineer (implementation) | partial |
| E2E test on a clean machine / Linux VM, two-machine scenario | qa-engineer (has Bash) | partial: no VM/Linux access in the unit list; whether the test environment exists is not verified |
| Secrets, entropy, perms, threat model | appsec | present |
| Docs/README | tech-comms | present |
| Arm64 / Apple Silicon image behavior | no dedicated unit; falls to the qa-engineer measurement in T-7 | partial |

Missing expertise: no dedicated bash/shell specialist. Proposal: have the architecture-board / CEO decide whether polyglot-engineer's playbook covers "bash CLI with shellcheck gate" or whether devops-sre should own `stack`. Scout is not needed for this; it is a routing question, not a research question.

Bottlenecks and trends
- insufficient data (n=0). No trend or bottleneck is claimed from history.
- Structural (from the spec itself, not a trend): (1) `stack` single file, one owner, T-5 → T-6 serial; (2) T-7 is one task covering 15 ACs and has 6 "full"-profile e2e tests; (3) T-0 is not verified and may revise ACs (spec line 9) which resets downstream work.

Playbook update proposals
- None. No violation history (n=0).

Tool inventory
- Not verified: no installed-tool inventory, no usage data, no quota statement. Nothing proposed as removable.

Recommendations (ordered, at most 5)
1. Before signature, have the BA split the 12 h into per-task / per-unit figures and add a token ceiling and a money ceiling (money is probably 0 unless Docker Desktop/OrbStack licensing counts) | evidence: spec.md line 7 and line 346 have only a total time | cost: ~1 BA revision | risk if not done: the ceiling is not checkable; "aşılırsa dur" cannot trigger on token or money.
2. Run T-0 (Scout) before signature, not "önerilir", and fold the results into the spec | evidence: spec.md lines 9 and 123-133, every upstream fact is "doğrulanmadı", AC-1/4/15 and health paths depend on them | cost: ~1 Scout run | risk if not done: an AC changes after signature, spec revision and rework inside the 12 h.
3. Add a rule that T-7 is split (for example quick-profile tests and full e2e) and name where the clean machine/Linux VM comes from (CEO to confirm) | evidence: §9.3 has 8 "full" e2e/integration rows plus the two-machine scenario in AC-8; qa-engineer tools are Read, Grep, Glob, Bash, Write, Edit with no VM access listed | cost: spec text plus one CEO answer | risk if not done: T-7 is the slowest task and may stall waiting on environment.
4. Decide the owner of `stack` (polyglot-engineer vs devops-sre) and consider whether T-5/T-6 can be split by function to reduce the serial chain | evidence: §12 file-ownership line, polyglot-engineer description targets foreign-stack/migration | cost: a routing decision, no new unit | risk if not done: one agent carries the critical path in a language outside its stated profile; quality risk (shellcheck, bash 3.2).
5. Treat 12 h as a stop-and-report checkpoint at T-6 completion (an intermediate reading), not only at the end | evidence: critical path above; the spec's own rule "aşılırsa iş durur" | cost: one status report | risk if not done: overrun is only seen at T-9.

Not verified / insufficient data
- Scorecards: n=0, so no actual/estimate ratio, no deviation, no trend (needs n≥3).
- Token and money ceilings: absent from the spec; quota statement: not provided by the CEO.
- Real duration of any task: no source; the 12 h has no stated basis.
- Whether a Linux VM / clean macOS machine is available for T-7: not verified.
- Installed tool inventory and usage: not verified.
- Upstream facts F-1..F-9: marked "doğrulanmadı" by the spec itself.

Scope note: I added/removed no unit, role, tool or playbook; I wrote only this review file (path given by the caller) and edited no spec.
