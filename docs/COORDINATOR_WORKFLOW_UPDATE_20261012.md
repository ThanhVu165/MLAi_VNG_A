# Coordinator Workflow Update — 2026-10-12

## Result

`READY_FOR_COORDINATOR_REVIEW`

This is a Coordinator-authorized, cardless documentation update. No Trello card or Task
ID was supplied; no ID was invented. The work is isolated from PR #40 on branch
`codex/coordinator-workflow-docs`.

## Baseline and scope

- Repository: `ThanhVu165/MLAi_VNG_A`
- Baseline: remote `dev` `73e23f916f2d9f8904c4b47a0a4370d241d796c8`
- Branch: `codex/coordinator-workflow-docs`
- Scope: `AGENT.md`, `docs/TEAM_WORKFLOW.md`, this report
- Out of scope: `PROJECT_SPEC.md`, `STATUS.md`, roadmap, product code, tests, PR #40,
  and the 95-test remediation

## Changes

- Defined ChatGPT Project MLAI as the analysis/coordination/review surface and Codex as
  the implementation/validation surface.
- Added explicit session roles and required task analysis before implementation.
- Made one Owner responsible for the complete AC/checklist, self-review, validation and
  evidence handoff.
- Made independent review risk-based instead of a default two-person requirement.
- Separated research/review sessions from implementation flow.
- Required a repository `.md` evidence report for official work, including cardless
  Coordinator authorization when no Trello card exists.
- Allowed the Owner to handle ordinary in-scope technical details without reporting a
  mechanical blocker; preserved stop rules for scope, safety, contract, conflict and
  data-loss risks.
- Preserved safety rules, technical-contract authority, baseline checks, Git protections,
  LIVE/API restrictions and Coordinator acceptance/merge authority.

## Validation

| Check | Result |
|---|---|
| `git status --short --branch` | PASS before edits; only pre-existing local SQLite sidecars were untracked |
| `git rev-parse origin/dev` | PASS: `73e23f916f2d9f8904c4b47a0a4370d241d796c8` |
| `git diff --check` | PASS |
| UTF-8 read of changed Markdown | PASS |
| Scope check (`git diff --name-only`) | PASS: only the three scoped Markdown files |
| Markdown link/heading scan | PASS: changed links use existing repository paths; no new broken link found |
| Terminology/conflict scan | PASS: AGENT and TEAM_WORKFLOW agree on Owner, ChatGPT/Codex roles, evidence and risk-based review |
| Full pytest | NOT RUN; documentation-only scope |
| LIVE LLM/API/email calls | 0 |

## Self-review and risks

Self-review checked the full diff for scope leakage, loss of safety rules, contradictory
authority statements, accidental changes to technical contracts, and private data. No
product code, test, status, roadmap, evidence set, secret, or PR #40 file was changed.

Remaining process risk: the cardless exception is valid only when the Coordinator's
authorization is recorded with the evidence report. Any later code, schema, policy,
evaluation or safety change still requires the normal contract and review path.

## Handoff

- Commit: `1c2d901` (`docs(workflow): align coordinator and owner process`).
- Draft PR: will target `dev`; not created yet.
- Trello: no update requested for this cardless directive.
- Reviewer: Coordinator review required; additional reviewer only if later scope adds
  higher-risk behavior.
