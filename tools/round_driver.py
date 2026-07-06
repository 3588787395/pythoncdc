import sys
import os
import json
import importlib
import importlib.util
import traceback
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.cfg import decompile as _decompile

BUG_THRESHOLD = 10
MAX_ROUNDS = 20
REGION_TYPES = ['IF', 'WHILE_LOOP', 'FOR_LOOP', 'TRY_EXCEPT', 'WITH', 'MATCH', 'BOOL_OP', 'TERNARY']
ITERATION_DIR = ROOT / 'tests' / 'iteration'


def is_c_class(source1, source2):
    try:
        code1 = compile(source1, '<c1>', 'exec')
        code2 = compile(source2, '<c2>', 'exec')
        return code1.co_code == code2.co_code
    except Exception:
        return False


def decompile_source(source):
    try:
        result = _decompile(source)
        return result.strip(), None
    except Exception as e:
        return None, str(e)


def check_bug(source, test_id=None):
    result, error = decompile_source(source)
    if error:
        return {
            'id': test_id,
            'type': 'CRASH',
            'source': source,
            'actual': None,
            'error': error,
            'c_class': False,
            'fixed': False
        }
    try:
        compile(result, '<decompiled>', 'exec')
    except SyntaxError as se:
        return {
            'id': test_id,
            'type': 'SYNTAX_ERROR',
            'source': source,
            'actual': result,
            'error': str(se),
            'c_class': False,
            'fixed': False
        }
    if 'elif' in source and 'elif' not in result:
        c = is_c_class(source, result)
        return {
            'id': test_id,
            'type': 'MISSING_ELIF',
            'source': source,
            'actual': result,
            'c_class': c,
            'fixed': False
        }
    src_lines = [l.strip() for l in source.strip().split('\n') if l.strip()]
    res_lines = [l.strip() for l in result.strip().split('\n') if l.strip()]
    src_stmts = [l for l in src_lines if not l.startswith('#') and l != 'pass']
    res_stmts = [l for l in res_lines if not l.startswith('#') and l != 'pass']
    if len(res_stmts) > len(src_stmts) * 2:
        c = is_c_class(source, result)
        return {
            'id': test_id,
            'type': 'DUPLICATION',
            'source': source,
            'actual': result,
            'c_class': c,
            'fixed': False
        }
    if 'else:' in source and 'else:' not in result and 'elif' not in source:
        c = is_c_class(source, result)
        return {
            'id': test_id,
            'type': 'MISSING_ELSE',
            'source': source,
            'actual': result,
            'c_class': c,
            'fixed': False
        }
    return None


def write_status(round_dir, region_type, round_num, state, bugs, total_tested):
    status_path = round_dir / 'STATUS.md'
    non_c_bugs = [b for b in bugs if not b['c_class']]
    c_class_bugs = [b for b in bugs if b['c_class']]
    fixed_count = sum(1 for b in bugs if b['fixed'])
    lines = [
        f'# Round {round_num:02d} - {region_type}',
        f'',
        f'- **State**: {state}',
        f'- **Total tested**: {total_tested}',
        f'- **Bugs found**: {len(bugs)} (non-C: {len(non_c_bugs)}, C-class: {len(c_class_bugs)})',
        f'- **Bugs fixed**: {fixed_count}',
        f'- **Threshold met**: {len(non_c_bugs) >= BUG_THRESHOLD}',
        f'',
    ]
    if bugs:
        lines.append('## Bug List')
        lines.append('')
        for b in bugs:
            c_tag = ' [C-CLASS]' if b['c_class'] else ''
            f_tag = ' [FIXED]' if b['fixed'] else ''
            lines.append(f'- **{b["id"]}**: {b["type"]}{c_tag}{f_tag}')
        lines.append('')
    if non_c_bugs:
        lines.append('## Bug Details')
        lines.append('')
        for b in non_c_bugs:
            lines.append(f'### {b["id"]}: {b["type"]}')
            lines.append(f'**Source:**')
            lines.append(f'```python')
            for l in b['source'].strip().split('\n'):
                lines.append(l)
            lines.append(f'```')
            if b.get('actual'):
                lines.append(f'**Actual:**')
                lines.append(f'```python')
                for l in b['actual'].strip().split('\n'):
                    lines.append(l)
                lines.append(f'```')
            if b.get('error'):
                lines.append(f'**Error:** {b["error"]}')
            lines.append('')
    status_path.write_text('\n'.join(lines), encoding='utf-8')


def write_bugs_json(round_dir, bugs):
    bugs_path = round_dir / 'bugs.json'
    bugs_path.write_text(json.dumps(bugs, indent=2, ensure_ascii=False), encoding='utf-8')


def write_test_file(round_dir, region_type, round_num, test_id, source):
    test_path = round_dir / f'test_{test_id}.py'
    lines = [
        f'"""Round {round_num:02d} {region_type} - test {test_id}"""',
        f'import sys',
        f'sys.path.insert(0, r"{ROOT}")',
        f'from core.cfg import decompile',
        f'',
        f'SOURCE = {repr(source)}',
        f'',
        f'def test_{test_id}():',
        f'    result = decompile(SOURCE)',
        f'    assert result is not None, "Decompilation returned None"',
        f'    compiled = compile(result, "<test>", "exec")',
    ]
    test_path.write_text('\n'.join(lines), encoding='utf-8')


def verify_fix(bug):
    result, error = decompile_source(bug['source'])
    if error:
        return False
    try:
        compile(result, '<decompiled>', 'exec')
    except SyntaxError:
        return False
    if bug['type'] == 'MISSING_ELIF':
        return 'elif' in result
    if bug['type'] == 'MISSING_ELSE':
        return 'else:' in result
    if bug['type'] == 'SYNTAX_ERROR':
        return True
    if bug['type'] == 'DUPLICATION':
        src_lines = [l.strip() for l in bug['source'].strip().split('\n') if l.strip()]
        res_lines = [l.strip() for l in result.strip().split('\n') if l.strip()]
        src_stmts = [l for l in src_lines if not l.startswith('#') and l != 'pass']
        res_stmts = [l for l in res_lines if not l.startswith('#') and l != 'pass']
        return len(res_stmts) <= len(src_stmts) * 2
    return result is not None


def run_round(region_type, round_num, generator_func):
    round_dir = ITERATION_DIR / region_type / f'round-{round_num:02d}'
    round_dir.mkdir(parents=True, exist_ok=True)

    status_path = round_dir / 'STATUS.md'
    if status_path.exists():
        content = status_path.read_text(encoding='utf-8')
        if '**State**: complete' in content:
            return 'complete', 0

    bugs = []
    total_tested = 0
    test_id = 0

    write_status(round_dir, region_type, round_num, 'collecting', bugs, total_tested)

    for source in generator_func(round_num):
        test_id += 1
        total_tested += 1
        write_test_file(round_dir, region_type, round_num, test_id, source)
        bug = check_bug(source, test_id=str(test_id))
        if bug:
            bugs.append(bug)

        non_c_bugs = [b for b in bugs if not b['c_class']]
        if len(non_c_bugs) >= BUG_THRESHOLD:
            break

    non_c_bugs = [b for b in bugs if not b['c_class']]
    write_bugs_json(round_dir, bugs)
    write_status(round_dir, region_type, round_num, 'fixing', bugs, total_tested)

    if len(non_c_bugs) < BUG_THRESHOLD:
        write_status(round_dir, region_type, round_num, 'insufficient_bugs', bugs, total_tested)
        return 'insufficient_bugs', len(non_c_bugs)

    print(f'  Collected {len(non_c_bugs)} non-C bugs (threshold met). Awaiting fixes...')

    all_fixed = all(verify_fix(b) for b in non_c_bugs)
    if all_fixed:
        for b in bugs:
            b['fixed'] = True
        write_bugs_json(round_dir, bugs)
        write_status(round_dir, region_type, round_num, 'complete', bugs, total_tested)
        return 'complete', len(non_c_bugs)
    else:
        write_status(round_dir, region_type, round_num, 'fixing', bugs, total_tested)
        return 'fixing', len(non_c_bugs)


def run_region(region_type, generator_func):
    print(f'\n{"="*60}')
    print(f'  Region: {region_type}')
    print(f'{"="*60}')
    completed = 0
    for r in range(1, MAX_ROUNDS + 1):
        print(f'\n  Round {r:02d}/{MAX_ROUNDS}:')
        state, bug_count = run_round(region_type, r, generator_func)
        if state == 'complete':
            completed += 1
            print(f'    COMPLETE - {bug_count} bugs found and fixed')
        elif state == 'insufficient_bugs':
            print(f'    INSUFFICIENT - only {bug_count} non-C bugs (need {BUG_THRESHOLD})')
            break
        elif state == 'fixing':
            print(f'    FIXING - {bug_count} bugs found, fixes pending')
            break
        else:
            print(f'    {state.upper()} - {bug_count} bugs')
            break
    print(f'\n  {region_type}: {completed}/{MAX_ROUNDS} rounds completed')
    return completed


def main():
    region_arg = sys.argv[1] if len(sys.argv) > 1 else None
    round_arg = int(sys.argv[2]) if len(sys.argv) > 2 else None

    generators = {}
    gen_dir = ROOT / 'tools' / 'generators'
    gen_dir.mkdir(parents=True, exist_ok=True)

    for rt in REGION_TYPES:
        mod_name = f'gen_{rt.lower()}'
        mod_path = gen_dir / f'{mod_name}.py'
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(mod_name, str(mod_path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            generators[rt] = mod.generate
        else:
            print(f'WARNING: No generator for {rt} at {mod_path}')

    if region_arg:
        regions = [region_arg] if region_arg in REGION_TYPES else []
        if not regions:
            print(f'Unknown region: {region_arg}. Available: {REGION_TYPES}')
            sys.exit(1)
    else:
        regions = [rt for rt in REGION_TYPES if rt in generators]

    total_completed = 0
    for rt in regions:
        if rt not in generators:
            print(f'Skipping {rt}: no generator')
            continue
        gen_func = generators[rt]
        if round_arg:
            state, bug_count = run_round(rt, round_arg, gen_func)
            print(f'  {rt} round {round_arg}: {state} ({bug_count} bugs)')
        else:
            total_completed += run_region(rt, gen_func)

    if not round_arg:
        print(f'\n{"="*60}')
        print(f'  TOTAL: {total_completed}/{len(regions)*MAX_ROUNDS} rounds completed')
        print(f'{"="*60}')


if __name__ == '__main__':
    main()
