# M7 Technical Closeout — Freeze Candidate V1

## Disposition

- **Task ID:** M7 — Freeze & Final Submission (technical scope only)
- **Owner/Approver:** Project Coordinator, acting as the single operator under direct authorization in the current session
- **Prepared:** 2026-10-15 (Asia/Ho_Chi_Minh)
- **Result:** `READY_FOR_COORDINATOR_REVIEW`
- **Freeze candidate:** `47a1fcd9686b5409674979b34a521ead2f65ae8d`
- **Freeze status:** `HOLD / FREEZE_CANDIDATE_ONLY`
- **Gold/GO-B:** `NO_GO_B / HOLD`
- **M7 DONE:** No
- **LIVE/API calls in this closeout:** 0
- **Official Set B evaluation:** `NOT RUN`

The Coordinator explicitly waived role reassignment and Trello verification for this technical closeout. This authorization does not waive the Gold Seal, provenance, deployment-alignment, GO-A, or GO-B technical gates.

## Baseline and freeze proposal

Remote `dev` was verified at `47a1fcd9686b5409674979b34a521ead2f65ae8d`. The closeout branch was created from that exact commit without checkout/reset/clean/stash/rebase of the prior working tree.

The proposed source freeze is `47a1fcd9686b5409674979b34a521ead2f65ae8d`, because it is the accepted `dev` checkpoint containing the merged M6 work and evaluation protocol. The accompanying public-safe machine-readable record is [M7_FREEZE_CANDIDATE_V1.json](M7_FREEZE_CANDIDATE_V1.json). The report commit is documentation-only and does not replace the proposed source freeze SHA.

### Locked component identity

| Component | Git tree / SHA-256 |
|---|---|
| `core/` | `a90c2f6a0cd35f7ec8ba72973929857a16a30e1e` |
| `corpus/` | `6a148eea2fcea6f9cf40a627204e9d3aabbc90db` |
| `infra/` | `d7f935c2adb2d4560dae9492046c6e2a7575c595` |
| `policies/` | `c426e2cddcccde1129a91a4142adbc1c1f674922` |
| `data/seed_docs/` | `e918b8c940e5a139ba89fbf58b5ca29f351f58a9` |
| `verify/` | `b577a6058b18a7dcffe3ec394068a9e66f6ee817` |
| `tests/cassettes/` | `3606888be58303a267e97c3a5bf4367d7f0e9619` |
| `docs/evaluation/` | `1161729ae3d91a9a8073b8063a3c0787a782282f` |
| `Dockerfile` | `324dcfcce544b69a5893970034eb1c2085a26196473ee1766cc658ddb0bd5128` |
| `compose.yaml` | `5cb06af0e5df87befa963cb7e4ca5297c49370e5f21a46f299ade7304dac9e89` |
| `requirements.txt` | `2384055990789840679cb8ce52089c035dc57d177a402bc88cfdc465fbf41e2d` |
| `policies/policy.yaml` | `274ea8f0fceb3bdec6a23edbd0af96a7639d1112f93b96a7a85c37900a6d40aa` |

The six seed-document hashes and the M2 DEV cases hash are recorded in the JSON manifest. No corpus, policy, runtime, routing, or Task Contract file was changed by this closeout.

### Runtime/configuration lock

- Local Python: 3.11.17 from the repository virtual environment.
- Container base: `python:3.11-slim`; its registry digest is not pinned, which remains a reproducibility risk.
- Dependency lock source: `requirements.txt` at the hash above; the Dockerfile separately installs `torch==2.5.1+cpu`.
- Offline replay configuration: `OPENAI_MODEL=gpt-6-luna`, `LLM_MODE=replay`, `LLM_CACHE=0`, `APP_MODE=restricted_demo`, no API key.
- Runtime settings: timeout 30 seconds, one retry, reasoning effort `none`, temperature 0.

## Acceptance-criteria status

| AC | Status | Evidence / finding |
|---|---|---|
| Baseline and component identities are exact | **PASS** | Remote `dev`, Git trees, and file hashes were verified at `47a1fcd...`. |
| M6 technical evidence is present and current offline checks pass | **PASS** | M6 reports/JSON are present; protocol/collector/config 39/39, restricted-demo/replay 30/30, Verify4 4/4. |
| Railway deployment equals proposed freeze | **FAIL / HOLD** | Railway source is `fe8c2db...`; proposed freeze is 27 commits ahead. The deployed commit is an ancestor, but `compose.yaml` differs. No redeploy was performed. |
| Set B candidate identity and accepted adjudication are recorded | **PASS** | `M7_SET_B_V2_CANDIDATE`, 16 cases, SHA-256 `9377eb0e...14086e`; Coordinator states adjudication 16/16 is accepted. |
| Independent Gold provenance, seal receipt, custodian/access history are verified | **NOT VERIFIED** | No authorized seal/provenance metadata was available for this closeout. Private Gold was not read or disclosed. |
| GO-B and official Set B run are authorized | **HOLD / NOT RUN** | Protocol gate is not met; `NO_GO_B / HOLD`. No official evaluation was run. |
| Public-safe technical handoff is prepared | **PASS** | This report and the metadata manifest contain no Gold labels, expected outputs, private storage path, or PII. |

## Validation performed

All executions below were offline. No provider or LIVE/API call was made.

| Check | Result | Method |
|---|---|---|
| Evaluation protocol, collector, compose contract | **PASS** | `python -m pytest docs/evaluation/test_protocol.py docs/evaluation/test_collector.py tests/test_compose_runtime_config.py -q` → 39 passed. |
| Restricted DEMO and replay audit, first attempt | **FAIL (environment mismatch)** | Run without `OPENAI_MODEL` failed closed: 4 failed, 26 passed. No product defect was inferred; required locked config was absent. |
| Restricted DEMO and replay audit, locked config | **PASS** | `OPENAI_MODEL=gpt-6-luna LLM_MODE=replay LLM_CACHE=0 APP_MODE=restricted_demo OPENAI_API_KEY= python -m pytest tests/test_restricted_demo.py tests/test_runtime_replay_audit.py -q` → 30 passed. |
| Verify4, fresh local database, replay mode | **PASS** | Same locked environment plus a fresh temporary database; `python -m verify.harness --set verify4` → 4/4 in 0.17 seconds, corpus runtime `cv_f6eb04187bb0`. |
| Docker CLI/config/build/runtime on this host | **NOT RUN** | Docker CLI is unavailable on this Mac (`command not found`). Committed Docker/config tests and prior M6 evidence were inspected instead. |
| LIVE/API validation | **NOT RUN** | Explicitly out of scope; call count 0. |
| Official Set B evaluation | **NOT RUN** | GO-B and seal metadata are not verified. |

The initial environment-mismatch failure is retained for auditability. The corrected locked-config rerun passed fully and did not invoke a provider.

## Existing technical evidence

- M6-T01 through M6-T05 and M6-V02-R01 reports are present under `reports/sprints/` and `reports/readiness/`.
- BASE24 recorded-pack evidence reports integrity 24/24; its replay result reports 24 hits, 0 misses, and 0 live calls.
- Historical Restricted DEMO evidence identifies deployed source `fe8c2dbca013e9344a678ba52f70588495c897ef` and Verify4 4/4. This closeout did not repeat the historical LIVE run.
- PR #60 remains open at head `f45d0a0557ed8e9057c956aba63038f8afe37107`; M4-T02 freeze/GO-A therefore remains incomplete.

## Deployment comparison

The verified Railway source commit `fe8c2dbca013e9344a678ba52f70588495c897ef` is an ancestor of the freeze candidate. The candidate is 27 commits ahead. Runtime source directories, policy, seed corpus, Dockerfile, and dependency file did not change in that interval, but `compose.yaml` did change to pin study/private and demo/restricted modes. Consequently, deployment equivalence is not established and freeze cannot be declared PASS. No source, Railway deployment, or production configuration was changed.

## Set B and Gold disposition

The Coordinator's accepted 16/16 adjudication is preserved without reopening historical recovery. Only the candidate identifier, case count, and candidate hash are recorded publicly. No labels, rationale, expected outputs, private path, or Gold payload were read or published.

Under the M4-T01 protocol, a claimed candidate hash does not prove an independently authored Gold or a valid seal. Independent Gold provenance, reviewer sign-off, Gold version/hash commitment, seal registry receipt, custodian/ACL, and access history remain `NOT VERIFIED`. Therefore the binding disposition is `NO_GO_B / HOLD`; Gold Seal and official Set B evaluation remain `NOT RUN`.

## Risks and blockers

1. Railway is not at the proposed freeze SHA, and compose configuration differs.
2. Independent Gold provenance and seal/access metadata are not verified; this blocks GO-B.
3. PR #60 is open and GO-A is incomplete.
4. The Docker base image uses a mutable tag rather than a pinned digest.
5. Docker validation could not be repeated locally because Docker is unavailable.
6. Untracked/ignored local work was preserved and excluded from this handoff; no clean, reset, stash, or overwrite was performed.

## Coordinator decisions required

Before handing the frozen technical baseline to UX/UI, the Coordinator must:

1. Accept or reject `47a1fcd9686b5409674979b34a521ead2f65ae8d` as the source freeze candidate.
2. Decide how Railway alignment will be established without changing the accepted source unexpectedly.
3. Resolve or explicitly sequence the open M4-T02/GO-A dependency.
4. Supply and approve protocol-compliant private Gold provenance, seal, custodian/ACL, and access-history metadata before granting GO-B.
5. Decide whether Docker build/runtime validation must be repeated on a Docker-capable host.

Until those decisions are recorded and the missing gates pass, this PR is a technical handoff only: do not mark M7 DONE, grant GO-B, merge as a freeze declaration, run Set B officially, or redeploy.
