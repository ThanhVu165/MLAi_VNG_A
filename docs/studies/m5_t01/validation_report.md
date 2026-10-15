# M5-T01 — Correction validation report

Baseline: `dev@16f584fa213416db30b247a431b92fffb94be075`.
Existing Draft PR: [#32](https://github.com/ThanhVu165/MLAi_VNG_A/pull/32).
Inherited correction: `debe7c33686f9dce2ff8180a68f653cc4c97621a`.
Date: 11/10/2026 (Asia/Saigon); Python 3.11.9 / Windows, offline docs checks.

## Reproduction

From the PR checkout, save this code to a temporary file outside the repository
and run `python -X utf8 <temporary-file>`. It reads Git blobs and Markdown only;
no app imports, provider execution, DB writes or Gold access.

```python
from pathlib import Path
import hashlib, json, re, subprocess, unicodedata
root = Path.cwd()
docs = root / 'docs/studies/m5_t01'
files = sorted(docs.glob('*.md'))
assert len(files) == 9
links = 0
for file in files:
    text = file.read_text(encoding='utf-8')
    assert '\ufffd' not in text and text == unicodedata.normalize('NFC', text)
    assert not re.search(r'(?:C|F):[/\\]|sk-[A-Za-z0-9]{20,}', text)
    # Exclude fenced examples from Markdown table validation.
    rendered = re.sub(r'```.*?```', '', text, flags=re.S)
    width = None
    for line in rendered.splitlines():
        if line.startswith('|'):
            n = len(line.split('|')) - 2
            if width is None: width = n
            assert width == n, (file.name, 'table columns')
        else: width = None
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', rendered):
        if '://' not in target and not target.startswith('#'):
            assert (file.parent / target.split('#')[0]).exists(), (file.name, target)
            links += 1
pack = (docs/'cases_xy.md').read_text(encoding='utf-8')
assert re.findall(r'^### ([XY][1-4])$', pack, re.M) == ['X1','X2','X3','X4','Y1','Y2','Y3','Y4']
assert len(re.findall(r'^> ', pack, re.M)) == 8
assert not re.search(r'P0[1-5]|AUTO_REPLY|ESCALATE|Điều \d', pack)
original_pack = subprocess.check_output(['git','show','debe7c33686f9dce2ff8180a68f653cc4c97621a:docs/studies/m5_t01/cases_xy.md']).decode()
assert pack == original_pack.replace('\r\n','\n')
protocol = (docs/'study_protocol.md').read_text(encoding='utf-8')
assert [x.strip() for x in protocol.splitlines() if re.match(r'\| S[1-4] \|', x)] == [
    '| S1 | B0-X | B2-Y |', '| S2 | B2-Y | B0-X |',
    '| S3 | B0-Y | B2-X |', '| S4 | B2-X | B0-Y |']
for name in ['study_protocol.md','xy_equivalence_assessment.md','gold_review.md','owner_handoff.md']:
    text = (docs/name).read_text(encoding='utf-8')
    # No case-level rule/answer/locator/complexity rows or commentary in public support docs.
    assert not re.search(r'\b[XY][1-4]\b', text), name
assert 'PENDING COORDINATOR DECISION' in (docs/'gold_review.md').read_text(encoding='utf-8')
manifest = (docs/'owner_handoff.md').read_text(encoding='utf-8')
statuses = []
for file in sorted((root/'data/seed_docs').glob('*.json')):
    rel = file.relative_to(root).as_posix()
    baseline = subprocess.check_output(['git','show','origin/dev:'+rel])
    current = subprocess.check_output(['git','show','HEAD:'+rel])
    assert baseline == current
    obj = json.loads(baseline)
    assert obj['is_synthetic'] is True
    assert hashlib.sha256(baseline).hexdigest() in manifest
    statuses.append(obj['status'])
assert statuses.count('ACTIVE') == 5 and statuses.count('SUPERSEDED') == 1
changed = subprocess.check_output(['git','diff','origin/dev','--name-only']).decode().splitlines()
untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard']).decode().splitlines()
assert all(x.startswith('docs/studies/m5_t01/') and x.endswith('.md') for x in changed + untracked)
print(f'PASS: {len(files)} Markdown files; {links} relative links; UTF-8/NFC/tables/path-secret heuristics; 8 unchanged case emails; 4 unchanged sequences; public support-doc case-cue scan; 6 corpus hashes/statuses; docs-only scope.')
```

Also run `git diff origin/dev --check` before commit and inspect
`git diff origin/dev --name-only`: only study Markdown is permitted. Verify remote
refs via `git ls-remote origin refs/heads/dev refs/heads/sprint/m5-t01-review-corrections`
and Draft/base/head/mergeability via `gh pr view 32 --repo ThanhVu165/MLAi_VNG_A
--json headRefOid,headRefName,baseRefName,isDraft,mergeable`.

## Actual result

- PASS (exit 0): 9 Markdown files; 32 relative links; UTF-8/NFC, table column
  consistency, local-path/secret heuristics; 8 unchanged emails versus inherited
  correction HEAD; 4 unchanged crossover sequences; public support-doc case-cue
  scan; 6 corpus hashes/statuses; docs-only scope.
- PASS (exit 0): local matrix has 8/8 IDs/email hashes/source hashes/locator
  fields, source states, rationale/facts, 4 pair assessments; all signatures
  remain PENDING. Verified outside Git; contents not uploaded or printed.
- PASS (exit 0): `git diff --check` after public-doc correction.
- Manual self-review: source/intent check on all 8 local candidate rows, full
  inherited PR diff and final correction diff; independent review NOT performed.
- Original dirty workspace retained; scoped changes only in separate worktree.
  Final staged scope checked before commit, remote refs checked before push.
- Runtime tests: NOT RUN (docs-only); study sessions 0; LIVE provider calls 0.
  These checks do not close CR-01 or establish equivalence/study readiness.

## Limits

Manual source/diff review complements pattern checks; scans do not prove absence
of all answer cues, secrets or historic exposure. Historical solution cues remain
accessible in Git history; participant exposure screening is required. External
URLs are known task/PR references, not an exhaustive remote link availability audit.
Runtime tests, study sessions and provider execution were not run; this does not
certify B2 runtime or Study isolation. Gold matrix stays local outside Git with
8 candidate rows and PENDING signatures; controlled handoff/Minh verdict remain
PENDING. No Gold output is part of this report or the reproducible public checks.
