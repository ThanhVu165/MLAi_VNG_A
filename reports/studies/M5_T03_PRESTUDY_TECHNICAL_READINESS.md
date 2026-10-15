# M5-T03 — Post-Merge Study Candidate Verification

## Metadata

- Task reference: `M5-T03 — Pre-Study Technical Readiness`
- Owner/Approver: Project Coordinator
- Exact merged/tested SHA: `e9f3fd2ce85b5290ff1fd9593c6de9c0ef6fae44`
- Git tree: `a6c4b4450af6877724adb6a174dfbb9d1fc706e7`
- Merge provenance: PR #56, parents
  `2ce699c6a0d5b3d4ac6252a394468fb2aab329cd` and
  `b6b5afbf24496c473f203b777915e3cba3179f90`
- Validation ref: detached exact merged SHA
- Participant sessions: `0`
- LIVE/API calls: `0`
- GO-STUDY: `NOT ISSUED`

## Disposition

`STUDY_CANDIDATE_READY`

The exact technical candidate is:

`e9f3fd2ce85b5290ff1fd9593c6de9c0ef6fae44`

This disposition pins a technical runtime candidate only. It does not authorize a
participant session, LIVE/API use, GO-STUDY or task completion.

## Runtime manifest

| Item | Verified value |
| --- | --- |
| Docker | Desktop Server `29.1.3`, Linux/WSL2, `overlayfs` |
| Compose | `v2.40.3-desktop.1` |
| Exact image | `sha256:385313bf907001356fdd46e550588e38045ebf958fb96d02214622a8b1030200` |
| Validation project | `exodia-m6t02-validation-m5t03postmerge-20261015a` |
| STUDY mode | `APP_MODE=private` |
| Database | `DATABASE_PATH=/runtime/app.db` on isolated `study_data` |
| LLM | `LLM_MODE=replay`, `LLM_CACHE=0` |
| Binding | loopback only; disposable override `127.0.0.1:29512` → `8511` |
| Health | HTTP `200`, body `ok` |
| DEMO control | `APP_MODE=restricted_demo`, separate `demo_data` |

The disposable port overrides avoided unrelated local containers. The service,
container port, environment, image and volume topology remained the canonical Compose
definitions from the exact merged source.

## Validation evidence

| Command/check | Result |
| --- | --- |
| `git fetch origin`; `git rev-parse origin/dev` | PASS after one transient DNS retry; exact required SHA |
| Detached checkout and merge-parent inspection | PASS; PR #56 merge content present without conflict drift |
| Source and resolved Compose inspection | PASS; exact STUDY/DEMO modes and shared environment retained |
| Targeted Compose plus direct mode/access/replay guard tests | PASS — `6 passed in 1.40s` |
| `docker compose ... build study` from clean detached merge SHA | PASS |
| STUDY start/wait/health/loopback/mount inspection | PASS |
| Environment read inside running STUDY container | PASS; all four required values exact |
| In-container offline replay audit | PASS runtime evidence — 24 calls/hits, 0 misses/errors, LIVE=0 |
| Human R11 flow | PASS — job `done`, final `PENDING_APPROVAL`, one draft |
| PRESTUDY-D01 negative control | PASS — omitted mode reproduced `restricted_demo`, `DemoAccessDenied`, `ERROR/TECHNICAL_ERROR` |
| PRESTUDY-D01 canonical STUDY control | PASS — same synthetic intake reached `private`, `AWAITING_HUMAN/R1` |
| DEMO restricted privilege guard | PASS — privileged action raised `DemoAccessDenied` |
| STUDY/DEMO isolation | PASS — distinct labeled volumes; DEMO contained no STUDY probe table |
| STUDY restart/persistence | PASS — returned healthy; private mode and synthetic probe persisted |
| Precise STUDY log scan | PASS — no live/provider/OpenAI endpoint/runtime-error markers |
| Safe disposable cleanup | PASS — 0 project containers and 0 project volumes remained |

The minimal runtime image does not contain a Git executable. The replay audit reads Git
only to stamp `tested_sha`, so validation injected the already verified exact merge SHA
for that metadata call. Pipeline execution, socket/provider guards, cassette lookup and
evidence generation were unchanged. Audit exit `2` remains the expected provenance
status, not a replay/runtime failure.

## Defect status

- `PRESTUDY-D01`: `FIXED` — explicit private STUDY mode survived merge and legitimate
  B2 intake no longer fails because of the former mode omission.
- `PRESTUDY-D02`: `RESOLVED` — Docker environment and canonical STUDY validation pass.
- New defects: none.

## Candidate decision

All required merge-content, resolved-config, targeted regression, canonical container,
B2, restart and isolation checks passed. No fallback to LIVE occurred. Therefore:

`STUDY_CANDIDATE = e9f3fd2ce85b5290ff1fd9593c6de9c0ef6fae44`

## Remaining GO-STUDY blockers

- At least three confirmed M5-T02 participants.
- Actual participant consent.
- Actual prior-exposure screening.
- Proof that the private Google Drive is configured `Restricted` with the approved
  folder separation and access boundary.
- Approval of the Gold/replay provenance condition where still required by the study
  contract; current recorded replay pack provenance remains unapproved.
- Explicit Project Coordinator GO-STUDY decision.

No commit, push or pull request was created for this first-round verification artifact.
