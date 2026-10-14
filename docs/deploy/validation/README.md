# Private checkpoint evidence exported for team handoff

These are existing observations from deployment c8930474 / runtime SHA 61e31e8,
14/10/2026, not validation of the later documentation-only handoff commit or a hotfix.
The team handoff/report binds them to the observed image/config and states limitations.
This export is not an independent attestation or a new Coordinator acceptance.

| Artifact | SHA-256 of preserved file bytes |
| --- | --- |
| [readback](20261014-container-readback.json) | `814cbd1b7ff4d6ea33d6d4e99139feafd9e3324bf50a9409666b9445b8f60200` |
| [source/pack comparison](20261014-container-source-check.json) | `7b446eb8c3d4006fed6adf1a07a6b669364f126b482d68bce8a59f385249d776` |
| [runtime](20261014-container-runtime.json) | `136c042bb033f65aaa878edc73558db0f126e438ad76717b5b1a8f650d65a22e` |
| [recovery](20261014-container-recovery.json) | `267cb00e250b29ec5ad64fe303d206d213ee933632cdcb681a91e1224449bb6c` |
| [executed driver](private_runtime_probe.py) | `009616dca910362f0e72dc0acb62e2ec72b9f82039cc3b9b40df549fd0cddbfd` |

The directory's .gitattributes disables newline conversion for JSON/Python snapshots so
clones can compare these same bytes. Read the driver before running it; it specifically
targets the current private /runtime/demo.db checkpoint and runs product probes only on
a fresh /tmp DB. It is not a Restricted DEMO hotfix and should not be blindly applied to
a new revision or live database layout. See [team handoff](../M6_T04_TEAM_HANDOFF.md).

Only public-safe values/booleans, synthetic counts, source/prompt/file hashes, decisions
and test paths are included. No private key, token, DB file, raw provider response,
private evaluation data or real student input is included. No new runtime test was
performed during export. Earlier driver exceptions/assertions are disclosed in the
report; original failed-driver JSON/stderr/provider logs remain local and ignored.
