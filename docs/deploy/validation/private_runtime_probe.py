import hashlib
import json
import os
import socket
import sqlite3
import sys
import tempfile
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

os.chdir('/app')
sys.path.insert(0, '/app')
from scripts.audit_runtime_replay import CONFIG, forbidden, observe_runtime
from scripts import audit_runtime_replay as audit

for key, value in CONFIG.items():
    assert os.getenv(key) == value, (key, os.getenv(key), value)
assert os.getenv('DATABASE_PATH') == '/runtime/demo.db'
assert not os.getenv('OPENAI_API_KEY')

def demo_snapshot():
    with sqlite3.connect('file:/runtime/demo.db?mode=ro', uri=True) as connection:
        return {
            'cases': connection.execute('SELECT COUNT(*) FROM cases').fetchone()[0],
            'sources': connection.execute('SELECT COUNT(*), SUM(is_synthetic) FROM sources').fetchone(),
            'audit': connection.execute('SELECT COUNT(*) FROM audit_events').fetchone()[0],
            'db_sha256': hashlib.sha256(Path('/runtime/demo.db').read_bytes()).hexdigest(),
        }

before = demo_snapshot()
def observe_selected_human(process_case, db):
    from core.types import CaseInput, CaseStatus
    from core.worker import worker_tick
    from streamlit.testing.v1 import AppTest
    inp = CaseInput('synthetic@example.invalid', audit.HUMAN_INPUT['subject'], audit.HUMAN_INPUT['body'], datetime.fromisoformat('2026-09-21T09:04:00+07:00'), 'paste')
    result = process_case(inp)
    assert result.status is CaseStatus.AWAITING_HUMAN
    case_id = result.case_id
    page = AppTest.from_file('/app/pages/2_Hang_cho_duyet.py').run(timeout=20)
    assert not page.exception
    page.selectbox(key='selected_case_id_select').set_value(case_id).run(timeout=20)
    assert not page.exception
    page.radio(key=f'choice_{case_id}').set_value(audit.HUMAN_INPUT['choice'])
    page.text_area(key=f'reason_{case_id}').set_value(audit.HUMAN_INPUT['reason'])
    page.run(timeout=20)
    page.button(key=f'decide_{case_id}').click().run(timeout=20)
    assert not page.exception
    assert db.fetch_one('SELECT status FROM cases WHERE case_id = ?', (case_id,))[0] == 'HUMAN_DECIDED'
    worker_tick()
    return {'flow': 'DEV_HUMAN_R11', 'intake_result': asdict(result),
            'final_case': dict(db.fetch_one('SELECT status FROM cases WHERE case_id = ?', (case_id,))),
            'job': dict(db.fetch_one('SELECT state FROM case_jobs WHERE case_id = ?', (case_id,))),
            'draft_count': db.fetch_one('SELECT COUNT(*) FROM drafts WHERE case_id = ?', (case_id,))[0]}

with tempfile.TemporaryDirectory(prefix='m6-t04-container-', dir='/tmp') as directory, ExitStack() as guards:
    os.environ['DATABASE_PATH'] = str(Path(directory) / 'test.db')
    for name in ('connect', 'connect_ex', 'sendto'):
        guards.enter_context(patch.object(socket.socket, name, forbidden))
    guards.enter_context(patch.object(socket, 'create_connection', forbidden))
    guards.enter_context(patch.object(socket, 'getaddrinfo', forbidden))
    from corpus.seed import ensure_seeded
    from infra import db
    assert db.DEFAULT_DATABASE_PATH == Path(directory) / 'test.db'
    assert db.fetch_one('SELECT COUNT(*) FROM sources')[0] == 6
    assert db.fetch_one('SELECT COUNT(*) FROM chunks')[0] == 72
    seed = ensure_seeded()
    again = ensure_seeded()
    assert not seed.seeded, seed
    assert not again.seeded, again
    with patch.object(audit, 'observe_human_resume', observe_selected_human):
        calls, outcomes, _ = observe_runtime(Path('/app/tests/cassettes'), False)
    summary = []
    expected = {
        'DEV_ROUTINE': ('AUTO_REPLY', None),
        'DEV_AUTHORITY': ('ESCALATE', 'AUTHORITY_REQUIRED'),
        'DEV_FACT': ('ESCALATE', 'FACT_UNRESOLVED'),
    }
    for outcome in outcomes:
        row = {key: outcome[key] for key in ('flow', 'prompt_calls', 'replay_misses', 'draft_count')}
        row['persisted_status'] = outcome['persisted_case']['status']
        if 'verify_result' in outcome:
            result = outcome['verify_result']
            row.update(passed=result['passed'], decision=result['actual_decision'], escalation_type=result['actual_type'])
        elif 'result' in outcome:
            result = outcome['result']
            decision = result['decision']
            row.update(status=result['status'], decision=decision['decision'], escalation_type=decision['escalation_type'])
            row['passed'] = (row['decision'], row['escalation_type']) == expected[row['flow']]
        else:
            row.update(final_status=outcome['final_case']['status'], job_state=outcome['job']['state'])
            row['passed'] = row['final_status'] == 'PENDING_APPROVAL' and row['draft_count'] == 1 and row['job_state'] == 'done'
        summary.append(row)
    checks = {
        'replay_calls': len(calls),
        'replay_hits': sum(call['replay_ok'] for call in calls),
        'replay_misses': sum(not call['replay_ok'] for call in calls),
        'flow_summary': summary,
        'temporary_database': str(Path(directory) / 'test.db'),
        'seed': asdict(seed), 'second_seed': asdict(again),
        'network_and_live_guards': True, 'live_provider_calls': 0,
        'test_db_counts': {table: db.fetch_one('SELECT COUNT(*) FROM ' + table)[0] for table in ('cases', 'sources', 'chunks', 'audit_events', 'drafts', 'case_jobs')},
        'calls': [{key: call[key] for key in ('flow', 'step', 'prompt_hash', 'replay_ok', 'error')} for call in calls],
    }
    with sqlite3.connect(Path(directory) / 'test.db') as connection:
        checks['test_db_quick_check'] = connection.execute('PRAGMA quick_check').fetchone()[0]
after = demo_snapshot()
checks.update(demo_before=before, demo_after=after, demo_unchanged=before == after)
checks['passed'] = all(row['passed'] for row in summary) and checks['replay_misses'] == 0 and checks['demo_unchanged'] and checks['test_db_quick_check'] == 'ok'
print(json.dumps(checks, ensure_ascii=False, default=str))
