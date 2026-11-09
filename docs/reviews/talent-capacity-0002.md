Capacity report: Spec 0002 bookstack-dashboard (Draft) | Date: 2026-11-09 | Data: n=0 scorecards

Capacity opinion (for a spec): MISSING ESTIMATE (token ceiling) + time ceilings cannot be sanity-checked (insufficient data, n=0). Structural reading: Phase 1 is tight, Phase 2 has no slack, T-0 is not runnable as scheduled.

Numbers (source: spec-0002 §13 task table, summed by me)
| Item | Stated | Sum of task times | Note |
|---|---|---|---|
| T-0 (T-0a 0.75 + T-0b 0.75) | 1.5 h | 1.5 h | matches |
| Phase 1 (T-1..T-7: 0.5+0.75+1.25+0.75+1+0.25+0.5) | 5.5 h | 5.0 h | 0.5 h unallocated, about 10% buffer, not labelled in the spec |
| Phase 2 (T-8..T-14: 2.5+1+0.75+1+1.75+0.25+0.75) | 8 h | 8.0 h | 0% buffer |
| Total | 15 h | 14.5 h | scorecard row says 15 h |

- Scorecards: `/Users/goktugoktay/Desktop/Projects/selfhost-stack/docs/scorecards/` does not exist (Glob returned nothing); the only prior capacity file is `docs/reviews/talent-capacity.md` (spec 0001, also n=0). No actual/estimate ratio exists, so the 1.5x "optimistic" / 3x "inflated" test cannot be run. I do not label the ceilings optimistic or inflated by that test.
- Basis of the times: none stated in the spec (they are "süre önerisi"). Not verified.
- No fix-round allowance in any phase. Every task is a single pass; spec §13 gives no time for rework after QA/appsec findings. Phase 2 buffer is 0 h, so one fix round exceeds the 8 h ceiling and, by the spec's own rule (§0 header), stops the job.
- Token ceiling: absent ("CEO beyanı yok, belirlenmedi", spec line 9). Money: 0 (stated). Quota statement from the CEO: not provided. The "ceiling exceeded, stop" rule cannot fire on token. This is MISSING ESTIMATE for the token axis.

Polyglot-engineer serial load (source: §13 task table)
| Phase | Tasks (all polyglot) | Hours | Language mix |
|---|---|---|---|
| 1 | T-2 0.75, T-3 1.25, T-4 0.75 | 2.75 | bash (`stack`), Blade/PHP |
| 2 | T-8 2.5, T-10 0.75, T-11 1.0 | 4.25 | Python (stdlib + unittest), bash, Blade/PHP |
| Total | 6 tasks | 7.0 h = about 52% of the 13.5 h in Phases 1+2 | 3 languages, 2 context switches per phase |

- Critical path Phase 1 (my reading of the dependency column): T-0a 0.75 -> T-3 1.25 -> T-4 0.75 -> T-5 1.0 -> T-7 0.5 = 4.25 h; T-2 (0.75 h) is the same unit so it runs serially with T-3, giving about 5.0 h. Against 5.5 h that leaves about 0.5 h. T-0b (0.75 h) and T-1 (0.5 h) are on other units and parallel. Tight but arithmetically feasible, with no rework.
- Critical path Phase 2: T-9 (devops, 1 h, parallel to T-8) -> T-8 2.5 -> T-10 0.75 -> T-11 1.0 -> T-12 1.75 -> T-14 0.75 = 6.75 h wall time with T-13 hidden in parallel. Against 8 h that leaves about 1.25 h, only if QA starts the moment T-11 ends and no fix round occurs.
- Judgment (not data): T-3 (1.25 h) holds the home override, cards, URL allowlist and escape, admin check, state partials, UPSTREAM and README, with 6 CB criteria; T-8 (2.5 h) holds the full collector plus unittests for 7 behaviours. These two are the likely overrun points. No history to confirm.
- Single unit holds the critical path in both phases, in code (Blade, Python) whose upstream facts are all "doğrulanmadı" (§5). If T-0a changes D-2/D-10 (theme mechanism, shelf view), T-3/T-4 are re-estimated.

Structural problem found: T-0b is scheduled "imza öncesi" (§13, §16 last paragraph) but depends on "0001 T-2, T-4", and the header (line 6) says this spec is applied only after 0001 is signed and T-2/T-4/T-5 are delivered. 0001 is an unsigned Draft. T-0b (D-3, D-7, D-15 on mac+Linux, D-16, D-14) therefore cannot run before this spec's signature unless 0001 T-2/T-4 exist. Either the spec is signed before D-15/D-12/D-14 are measured (the spec itself says these "tasarımı değiştirebilir", line 455) or the 0.75 h T-0b needs a throwaway test setup that is not costed.

QA needs (fake Plane server, two platforms) - source: T-5 (1 h), T-12 (1.75 h), §11
- T-12 (1.75 h, qa-engineer) carries: write `tests/fake-plane/` (a server that serves states/labels/work-items with cursor paging, returns 401/429/down on command, records requests with method and path), CB-11..CB-19 tests (CB-15 alone has 8 sub-states a-h including a 20-request timing median and stopping containers; CB-17 six sub-states), PB-1..PB-6 repeats (full profile, restore round trip, `tar -tzf`), plus the real-Plane run CB-19. Judgment: this is the largest single task by scope relative to its time and is the most likely stall point.
- CB-19 needs a running pinned Plane (multi-container) plus a low-role user and a token generated in the Plane UI. A QA agent cannot create the user/token without a browser or the CEO. Who provides this is not stated (§12 says CEO creates the token on each machine). Not verified.
- Two platforms: T-0b says "mac + Linux" for D-15, but T-5/T-12 do not say tests run on Linux, and the unit list for qa-engineer/devops-sre shows no Linux host or VM access (same gap as in the 0001 report). Whether a Linux machine exists: not verified. D-15 is exactly the item (host-gateway vs 127.0.0.1) where platforms differ, so a mac-only run cannot support CB-11 network claims for Linux. Also two-user tests (CB-3, CB-6) and two checkouts (CB-9) need scripted BookStack setup via API; not costed.
- The fake server is a deliverable of QA but also the only evidence for 12 of 19 CB; the maker/verifier rule is held (QA writes tests, polyglot writes feed.py), but QA's fake server encodes the spec's unverified guess of the Plane API (D-13). If D-13 is wrong the fake and the collector are wrong together; only CB-19 (real Plane, last test of the last task) would catch it. Risk, not data.

Required expertise and coverage
| Area | Covering unit/playbook | Status |
|---|---|---|
| Blade/PHP BookStack visual theme | polyglot-engineer (PHP listed in routing) | present, partial depth: BookStack theme internals unverified (D-1, D-2, D-4, D-10) |
| Python stdlib collector + unittest | polyglot-engineer (Python listed in routing) | present |
| bash CLI `stack` (bash 3.2, shellcheck, macOS/Linux) | polyglot-engineer (bash not named in routing); same gap as report for 0001 | partial |
| Docker Compose, internal network, hardening (read_only, cap_drop) | devops-sre | present |
| Linux host/VM for D-15 and tests | none in unit list | missing (environment, not expertise); CEO to confirm availability |
| Plane API behaviour (rate limit, roles, endpoints) | scout (T-0a) | present, all "doğrulanmadı" |
| Fake HTTP server + e2e test harness | qa-engineer | present |
| Threat model: token, SSRF, stored XSS | appsec | present |
| README, user steps | tech-comms | present |

Bottlenecks and trends
- insufficient data (n=0). No trend or bottleneck claimed from history.
- Structural only (not a trend): polyglot-engineer at 7.0 h serial with 3 languages; T-12 scope; T-0b dependency on unsigned 0001; zero buffer in Phase 2; delivery chain (appsec -> auditor -> quality-office) given 0.5 h (Phase 1) and 0.75 h (Phase 2) for three units each, with no fix round.

Playbook update proposals
- None. No violation history (n=0).

Tool inventory
- Not verified. No tool inventory, no usage data, no quota statement. Nothing proposed as removable.

Recommendations (ordered, at most 5)
1. Fix the T-0b sequencing before signature: either state that T-0b runs against throwaway pinned containers (and cost it), or move D-15/D-12/D-14 measurement into a signed Phase 0 | evidence: spec header line 6 vs §13 T-0b dependency and §16 line 455 | cost: one BA revision, maybe +0.5 h | risk if not done: D-12/D-14/D-15 can change the design after signature, which is a spec revision plus rework inside zero-buffer Phase 2.
2. Add a token ceiling (CEO number or an explicit "none, time only") and a labelled fix-round allowance (suggest the BA state a figure, for example 20-30% of build time; this is my judgment, not data) per phase | evidence: spec line 9; sum Phase 1 = 5.0 h vs 5.5 h, Phase 2 = 8.0 h vs 8 h | cost: one BA revision and one CEO answer | risk if not done: the stop-and-report rule cannot trigger on token, and a single fix round stops Phase 2.
3. Accept the two-signature split (S-3) and add a stop checkpoint inside Phase 2 after T-8 (feed.py + unittests) | evidence: T-8 2.5 h is the largest polyglot task and the pivot of 6 later tasks | cost: one status report | risk if not done: overrun is seen only at T-12/T-14.
4. Before signature, have the CEO confirm a Linux host or VM and who produces the real-Plane low-role user and token for CB-19; if neither exists, mark Linux checks and CB-19 as "not verified" in the spec rather than counting them inside the 1.75 h | evidence: T-0b "mac + Linux", T-12, §12 (no Linux access in the unit list; same gap as the 0001 report) | cost: one CEO answer | risk if not done: T-12 stalls on environment or the Linux claim ships unverified.
5. Consider splitting T-12 into T-12a (fake-plane + CB-11..14, 18) and T-12b (CB-15, 17, 19 + PB repeats), and let the BA re-time T-3 and T-8 against the 3-language switching; routing question for the CEO whether devops-sre should own `stack` (T-2, T-10) to reduce polyglot's serial 7.0 h | evidence: §13 table sums above; routing table lists PHP and Python but not bash | cost: a spec edit and a routing decision, no new unit | risk if not done: the single polyglot-engineer holds 52% of the work and the critical path.

Not verified / insufficient data
- Scorecards: n=0 (directory absent), so no actual/estimate ratio, no deviation, no trend (needs n>=3).
- Token ceiling: absent. Quota statement: not provided. Money 0: from the spec, not checked.
- Basis for every task duration: none stated; the 15 h total and the 0.5 h Phase 1 remainder have no stated source.
- Linux host/VM availability and who creates the real-Plane token: not verified.
- Upstream facts D-1..D-16: marked "doğrulanmadı" by the spec itself; their effect on T-3/T-4/T-8 time is unknown.
- Installed tool inventory and usage: not verified.
- I did not read the polyglot-engineer agent file; language coverage comes from the routing table and the spec.

Scope note: I added/removed no unit, role, tool or playbook; I wrote only this file (path given by the caller) and edited no spec.
