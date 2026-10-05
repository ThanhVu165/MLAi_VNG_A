# Immutable M1 closure evidence — 2026-10-06 (Asia/Saigon)

Existing final synthetic DEV/REGRESSION runs only; no evaluation was rerun for this archive.
These files are immutable M1 closure evidence. Preserve them; future runs need separate artifacts.
No SQLite DB, WAL/SHM, environment file, credential, auth header, raw input body,
prompt or provider request/response payload is archived. JSON retains synthetic subject/question
validation artifacts. Source subjects and expected labels were checked against repository fixtures.

JSON files are byte-for-byte copies. Console logs are curated UTF-8 derivatives: decoded
from UTF-16, joined PowerShell-wrapped provider metadata into complete JSON lines, and
retained the original result table/total. Only PowerShell NativeCommandError framing,
command echo and line-location decorations were omitted; these decorations accompany
stderr metadata and do not establish provider failure. All source files remain untouched.
No secret or unsafe raw payload was found before archiving; no secret redaction was needed.
Provider events contain only existing safe metadata, including prompt length/hash, not prompts.
Source SHA-256 identifies original bytes; archive SHA-256 identifies committed bytes.
The local `.gitattributes` disables Git newline conversion for JSON/log evidence,
so committed bytes and their SHA-256 remain stable across checkout platforms.

## Results

| Run | Provider / model from JSON | Mode / cache_enabled | Semantic labels | TECHNICAL_ERROR | Elapsed | within_time_limit | Provider attempts |
|---|---|---|---|---|---|---|---|
| verify4 | openai / gpt-6-luna | live / false | 4/4 | 0/4 | 35.28s | True | 12 successful / 0 retries |
| escalation5 | openai / gpt-6-luna | live / false | 4/5 | 0/5 | 44.48s | True | 17 successful / 0 retries |
| full15 | openai / gpt-6-luna | live / false | 14/15 | 0/15 | 93.19s | True | 42 successful / 0 retries |

Full15: 15/15 executed; TECHNICAL_ERROR = 0/15; Gate threshold <=1/15;
**M1 Gate PASS**. The harness exit code = 1 because of E04 semantic expected-label
mismatch, NOT because of a TECHNICAL_ERROR. Exit status follows the existing harness
return condition and coordinator run record; it is not stored as a JSON field.
Escalation5 likewise has semantic mismatch exit 1, but 44.48s <=90s and
within_time_limit=True. Verify4 exit 0. Full15's within_time_limit=True is the
harness flag; the 90s constraint applies only to escalation5, not full15.

E04 expected ESCALATE / FACT_UNRESOLVED / P03, actual ESCALATE /
AUTHORITY_REQUIRED / P01 in escalation5 and full15. **Known M2 correctness issue**:
provider/model-sensitive correctness issue; exact non-regression against the old
Gemini/dev path has not been proven. Expected labels are unchanged. No claim is made
that M1 definitively caused or did not cause this behavior. This is runtime Gate
evidence, not independent held-out evaluation or general provider reliability proof.

Final Code Review PASS (no blocker/high/medium) and independent Anti PASS WITH
DOCUMENTED DEBT are coordinator-provided closure decisions, not newly executed reviews.
Runtime checkpoint: d1b4e2a; this documentation archive adds no runtime changes.

## Provenance and SHA-256

### `reports/evidence/m1/verify4_final.json`

- Original local source: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_verify4_rerun2_20261006_000228\verify4.json`
- Archived path: `reports/evidence/m1/verify4_final.json`
- Archive SHA-256: `351b9573f35d7953b075c6d96cadf7abd8d6665fbc861d5f5ada523e2142e6e2`
- Source SHA-256: `351b9573f35d7953b075c6d96cadf7abd8d6665fbc861d5f5ada523e2142e6e2`

### `reports/evidence/m1/verify4_final_console.log`

- Original local source: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_verify4_rerun2_20261006_000228\console.log`
- Archived path: `reports/evidence/m1/verify4_final_console.log`
- Archive SHA-256: `a6dfaa17a70288abd994cdeb8002feb015549795faf064189cdaf314402f9b7b`
- Source SHA-256: `8d54cd7b526209bc73cab7751304fbd5174d940d581a1a74958831ea21aa5efd`

### `reports/evidence/m1/escalation5_final.json`

- Original local source: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_escalation5_20261006_004954\escalation5.json`
- Archived path: `reports/evidence/m1/escalation5_final.json`
- Archive SHA-256: `07869713037ca86aa59b9456a7bb2a55e66c8609cbbf04fe17d0fe3241787fa8`
- Source SHA-256: `07869713037ca86aa59b9456a7bb2a55e66c8609cbbf04fe17d0fe3241787fa8`

### `reports/evidence/m1/escalation5_final_console.log`

- Original local source: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_escalation5_20261006_004954\console.log`
- Archived path: `reports/evidence/m1/escalation5_final_console.log`
- Archive SHA-256: `ec2bbba6e4d4ba2e5c0ed7af464ef8326452daacc612a29664aeb8e248d5f6a1`
- Source SHA-256: `d3b2f189f91ffb184a6e4de9d08c8fabb745a6367220b7cce33ec08150b4e573`

### `reports/evidence/m1/full15_gate_final.json`

- Original local source: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_full15_gate_20261006_005305\full15.json`
- Archived path: `reports/evidence/m1/full15_gate_final.json`
- Archive SHA-256: `81203a4a50eb01c68595555a7f7ce8c3b0060d8e8451ed5e81c9138cc705ddaf`
- Source SHA-256: `81203a4a50eb01c68595555a7f7ce8c3b0060d8e8451ed5e81c9138cc705ddaf`

### `reports/evidence/m1/full15_gate_final_console.log`

- Original local source: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_full15_gate_20261006_005305\console.log`
- Archived path: `reports/evidence/m1/full15_gate_final_console.log`
- Archive SHA-256: `89a380edf71d05e764e95767c3bcf51ac48d4cbee564c24483364a61f26ff3df`
- Source SHA-256: `32a3bdf995a06eef0cf8dac75391eef2479d3e421b7bf29062ba3a832928de6a`
