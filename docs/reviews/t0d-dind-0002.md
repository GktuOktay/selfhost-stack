Scout report: docker:<tag>-dind test image (spec-0002 CB-9, T-5, K3-4) | Date: 2026-11-09 | Requested by: T-0d (spec-0002)

Criteria
1. Licence allows commercial/internal use, no copyleft obligation on us.
2. Maintained: release within last 12 months, rebuilt regularly.
3. No unpatched known vulnerabilities in the pinned engine version (OSV/GHSA/CVE).
4. Official source, multi-arch (linux/amd64 + linux/arm64) so CB-9 runs on mac (arm64) and Linux CI (amd64).
5. Pin form: concrete tag + index digest.

Candidates
| Dimension | A: docker:29.9.3-dind (alpine3.24) | B: docker:29.9.3-dind-rootless | C: docker:29.9.2-dind (previous) |
|---|---|---|---|
| Fit | yes: dind, amd64 + arm64/v8 (+ arm v6/v7), runs privileged as spec §6.3 assumes | partly: rootless needs extra kernel/userns support, not what spec §6.3 describes | yes, but older |
| Licence | Apache-2.0 (docker-library/docker repo, moby) [1][2] | same | same |
| Maintenance | Image pushed 2026-11-06; maintainer Tianon via docker-library/docker; engine v29.9.3 released 2026-11-03 [3][4][5] | same cadence | pushed 2026-10-22 [3] |
| Security | 29.9.3 fixes CVE-2026-116587, CVE-2026-116591, CVE-2026-115538, CVE-2026-115539, BuildKit GHSA-2fqp-xg6f-v7gj, GHSA-w26x-xg27-7qjc [5] | same | misses the 29.9.3 fixes |
| Cost | free | free | free |
| Stack fit | Docker Hub official image; no .NET relevance (test only) | same | same |
| Exit cost | low: tag in tests/versions.env | low | low |

Recommendation: USE docker:29.9.3-dind, pinned by index digest. Rationale: newest stable release line, Apache-2.0, official library image with fresh rebuild, and it carries the latest engine security fixes, multi-arch for mac arm64 and Linux amd64.

Pin (for tests/versions.env):
docker:29.9.3-dind@sha256:08a98015fce594af7c382883bea080ea206de74402a95da9dc52b6428c8cd121
(Docker Hub tag list, 2026-11-09 [3]; same index digest shared by tags 29.9.3-dind, 29.9.3-dind-alpine3.24, 29.9-dind, 29-dind, dind.)

Per-platform manifests (for reference, not for pinning; index digest is the pin):
- linux/amd64: sha256:fafc2949724b06fd4e4bc53c446a09149b750693f0abe7f444e9eec1e138fe65
- linux/arm64/v8: sha256:a4bbf4cfd8b06ff12a3553cc7b5068b5d2b323d27532ba8e17089cdff3a8af97
- linux/arm/v7: sha256:0ad8a4eddc88f24438d08a5f8440cdd5ebf3283e0f24c1a522092bf934fffbfc
- linux/arm/v6: sha256:88463d780c2d484fbf74df90e45893bfdada76e2cb0a64ea4b9a252f194ab6b8
- 4 "unknown/unknown" entries are presumably attestation manifests (inference, not verified).

Security history (moby/moby advisories, [6])
- Recent: GHSA-7cfq-22r6-qp73 (High, insecure-registry fallback, 2026-10-01); GHSA-6m9p-4h64-m6vh (Moderate, VXLAN injection, 2026-10-01); GHSA-rg2x-37c3-w2rh, GHSA-x86f-5xw2-fm2r (High, docker cp / archive, 2026-05-18); GHSA-x744-4wpc-v9h2 (High, AuthZ bypass, 2026-03-25); older GHSA-v23v-6jw2-98fq (Critical, authz zero length, 2024-07-23).
- Patched versions are not shown in the listing; whether 29.9.3 contains the fix for each October GHSA is NOT verified.
- Relevance to us: test-only, ephemeral, privileged dind. Swarm, overlay, authz plugin and registry-fallback issues do not apply to our use (no swarm, no authz plugin, local registry only: assumption, spec owner to confirm). docker cp / archive issues apply only if the test harness copies into dind from untrusted content.

Risks
- `--privileged` is required for dind and gives full host access; Docker's own page says it is generally not recommended [7]. Use only in tests, never on the production host, never with untrusted images.
- Disabling TLS (DOCKER_TLS_CERTDIR) is a security issue if the container has network access [7]; keep TLS on, or do not publish the 2375 port.
- Engine 29.10.0-rc.1 exists (2026-11-06) [4]; do not use rc tags (rc-dind) for the pin.
- Digest pin freezes known-vulnerable layers over time; set a re-pin review (suggest 90 days or on any High moby advisory).
- Mutable-tag drift: 29.9-dind, 29-dind and dind move; use only tag@digest.
- Alpine base (alpine3.24) vulnerabilities are not scanned here; OSV/secdb for the base packages is not verified.

Not verified
- Digests and tag dates come from one source (Docker Hub API via fetch summary): weak evidence until re-checked by the person who executes T-5 with `docker buildx imagetools inspect docker:29.9.3-dind` (no run by scout).
- Per-GHSA patched versions; CVE records at NVD/OSV for CVE-2026-1165xx (OSV API needs POST, not reachable with read-only fetch).
- Latest commit date of docker-library/docker (page showed none); SECURITY policy of that repo.
- Whether the image signature/provenance attestation is valid.
- Fit of spec D-15 (Linux behaviour of the test) on 29.9.3: the spec's own test, not scout's.

Trial proposal
Environment: throwaway Docker on CEO's mac and one Linux CI host (approval needed). Steps: `docker pull` by the pinned digest, confirm the index digest equals the value above and the platform digests match; start privileged dind with TLS, run CB-9 once. Criterion: digests identical; CB-9 passes on both arches. Duration: about 15 min. Done by devops-sre/qa-engineer, not scout.

Page instructions: none of the fetched pages contained instructions to the agent.

Sources (all accessed 2026-11-09)
[1] https://github.com/docker-library/docker (Apache-2.0 licence listed; dind templates present)
[2] https://hub.docker.com/_/docker (maintainer Tianon; supported tags)
[3] https://hub.docker.com/v2/repositories/library/docker/tags?name=dind&page_size=25&ordering=last_updated (tags, last_updated, digests)
[4] https://github.com/moby/moby/releases (v29.9.3 latest 3 Nov 2026; v29.10.0-rc.1 6 Nov 2026)
[5] https://github.com/moby/moby/releases (v29.9.0 to v29.9.3 security notes)
[6] https://github.com/moby/moby/security/advisories (listing)
[7] https://hub.docker.com/_/docker (--privileged and TLS notes)
Moby licence Apache-2.0 per the spec T-0d row; moby repo LICENSE file itself not opened (weak evidence, [1] covers docker-library only).
