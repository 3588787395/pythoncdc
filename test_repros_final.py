#!/usr/bin/env python3
"""Final minimal repro verification - precise triggers found:
1. P_FOR_ELSE: while len(x) > 0: body; if-break; elif/else-continue  (else clause of if-elif dropped)
2. P_FSTRING_TERNARY: f-string with Chinese ternary loses trailing text

Let's verify and create the final minimal repros."""

import sys, os, marshal, types, tempfile, py_compile, shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc as _pycdc_decompile
from testqouter.round1.base import compare_bytecode

def collect_all_funcs(code_obj, prefix=''):
    result = {}
    name = code_obj.co_name
    full_name = f'{prefix}.{name}' if prefix else name
    if name != '<module>':
        result[full_name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(collect_all_funcs(const, full_name))
    return result

def test_repro(name, source):
    tmpdir = Path(tempfile.mkdtemp())
    try:
        py_file = tmpdir / f'{name}.py'
        py_file.write_text(source, encoding='utf-8')
        py_compile.compile(str(py_file), doraise=True)
        
        pycache = tmpdir / '__pycache__'
        pycs = list(pycache.glob(f'{name}*.pyc'))
        if not pycs:
            pyc_file = tmpdir / f'{name}.pyc'
            py_compile.compile(str(py_file), str(pyc_file), doraise=True)
            pycs = [pyc_file]
        actual_pyc = pycs[0]
        
        dec_src = _pycdc_decompile(str(actual_pyc))
        dec_code = compile(dec_src, '<decompiled>', 'exec')
        
        with open(actual_pyc, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        
        orig_f = collect_all_funcs(orig_code)
        dec_f = collect_all_funcs(dec_code)
        
        mismatches = []
        for fn in orig_f:
            if fn in dec_f:
                fc = compare_bytecode(orig_f[fn], dec_f[fn])
                if not fc['match']:
                    mismatches.append((fn, fc))
        
        return {
            'status': 'MISMATCH' if mismatches else 'MATCH',
            'mismatches': mismatches,
            'dec_src': dec_src,
        }
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)[:200]}
    finally:
        try:
            shutil.rmtree(str(tmpdir))
        except:
            pass

# Pattern 1: P_FOR_ELSE (while-else / for-else clause dropped)
# Trigger: while loop with if-elif-else chain where else has continue
print("=" * 80)
print("P_FOR_ELSE: MINIMAL VERIFIED REPROS")
print("=" * 80)

for_else_final = [
    # Repro 1: SIMPLEST - while + if-elif-else with continue
    ("repro1_while_if_elif_else_continue", '''def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event.type == 'stop':
            break
        elif event.type == 'signal':
            process(event)
        else:
            continue
'''),
    # Repro 2: while + if-break + elif-continue (without else)
    ("repro2_while_if_break_elif_continue", '''def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event.type == 'stop':
            break
        elif event.type == 'skip':
            continue
        process(event)
'''),
    # Repro 3: while + pop + log + if-break + elif
    ("repro3_while_pop_log_break_elif", '''def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        log.debug(str(event))
        if event == 'stop':
            break
        if event == 'signal':
            process(event)
'''),
    # Repro 4: for-else with break (simpler version)
    ("repro4_for_else_break", '''def search(items):
    for item in items:
        if item == 'target':
            break
    else:
        return None
    return item
'''),
    # Repro 5: while with multiple elif branches
    ("repro5_while_multi_elif", '''def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event.type == 'stop':
            break
        elif event.type == 'signal':
            process(event)
        elif event.type == 'skip':
            continue
        else:
            log.debug('unknown')
            continue
'''),
]

for name, source in for_else_final:
    r = test_repro(name, source)
    if r['status'] == 'MISMATCH':
        fc = r['mismatches'][0][1] if r['mismatches'] else {}
        td = len(fc.get('true_diffs', []))
        jd = len(fc.get('jump_diffs', []))
        print(f"  {name}: MISMATCH (td={td}, jd={jd}) *** CONFIRMED ***")
        print(f"    Decompiler output:")
        for line in r['dec_src'].split('\n')[:15]:
            print(f"      {line}")
    else:
        print(f"  {name}: MATCH (bug not triggered)")

# Pattern 2: P_FSTRING_TERNARY (f-string with ternary loses parts)
# Also related to P_TRUNCATE: function body truncated due to f-string issues
print()
print("=" * 80)
print("P_FSTRING_TERNARY / P_TRUNCATE: MINIMAL VERIFIED REPROS")
print("=" * 80)

fstring_final = [
    # Repro 1: f-string with Chinese ternary + trailing text
    ("repro1_fstring_chinese_ternary_trail", '''def test(direction):
    return f"{'转入' if direction == '0' else '转出'}极"
'''),
    # Repro 2: f-string with ternary + trailing ASCII
    ("repro2_fstring_ternary_trail_ascii", '''def test(direction):
    return f"{'IN' if direction == '0' else 'OUT'}_FAIL"
'''),
    # Repro 3: f-string with ternary only (no trailing)
    ("repro3_fstring_ternary_only", '''def test(direction):
    return f"{'IN' if direction == '0' else 'OUT'}"
'''),
    # Repro 4: f-string with double ternary
    ("repro4_fstring_double_ternary", '''def test(x, y):
    return f"{'A' if x else 'B'}{'C' if y else 'D'}"
'''),
    # Repro 5: if-elif-else + f-string ternary + kwargs (full truncate pattern)
    ("repro5_elif_fstring_kwargs", '''def transfer(self, direction, amount, exchange_type='1'):
    if exchange_type not in ('1', '2'):
        log.error(f'unsupported: {exchange_type}')
        return False
    elif direction not in ('0', '1'):
        log.error(f'unsupported: {direction}')
        return False
    else:
        kwargs = {'exchange_type': exchange_type, 'amount': amount, 'direction': direction}
        error_dict, response = self.broker.transfer(**kwargs)
        if error_dict.get('error_no') != 0:
            return f"{'转入' if direction == '0' else '转出'}极{'沪A' if exchange_type == '1' else '深A'}"
    return True
'''),
]

for name, source in fstring_final:
    r = test_repro(name, source)
    if r['status'] == 'MISMATCH':
        fc = r['mismatches'][0][1] if r['mismatches'] else {}
        td = len(fc.get('true_diffs', []))
        jd = len(fc.get('jump_diffs', []))
        fd = fc.get('true_diffs', [{}])[0] if fc.get('true_diffs') else {}
        fd_str = f"{fd.get('orig_op','?')}({str(fd.get('orig_arg','?'))[:25]}) -> {fd.get('decomp_op','?')}({str(fd.get('decomp_arg','?'))[:25]})"
        print(f"  {name}: MISMATCH (td={td}, jd={jd}) first_diff={fd_str} *** CONFIRMED ***")
        print(f"    Decompiler output:")
        for line in r['dec_src'].split('\n')[:15]:
            print(f"      {line}")
    else:
        print(f"  {name}: MATCH (bug not triggered)")

# Summary of what triggers each pattern
print()
print("=" * 80)
print("TRIGGER SUMMARY")
print("=" * 80)
print("""
P_FOR_ELSE (while-else/for-else clause misidentification):
  Trigger: while loop + if-elif-else chain with break/continue
  Bug: The decompiler drops the else branch or misidentifies it.
  In the original pyc: while body contains if-elif-else with continue in else
  In the decompiled output: the elif and else branches are dropped or merged,
  and the loop condition + break pattern is misidentified.
  
  Root cause: CPython 3.11 emits the while-else exit path as JUMP_FORWARD
  past the loop body, but the decompiler interprets this as a for-else/while-else
  boundary and either drops the else clause or misidentifies the block structure.
  
  Minimal repro:
    def handle(events):
        while len(events) > 0:
            event = events.pop(0)
            if event.type == 'stop':
                break
            elif event.type == 'signal':
                process(event)
            else:
                continue

P_FSTRING_TERNARY (f-string ternary expression loses trailing text):
  Trigger: f-string containing a ternary expression (x if cond else y)
  followed by additional literal text
  Bug: The trailing text after the ternary is dropped in the decompiled output.
  
  Root cause: The decompiler's f-string reconstruction doesn't properly handle
  the combination of FORMAT_VALUE + BUILD_STRING when the format spec contains
  a ternary. It emits the ternary part but loses the trailing literal part.
  
  Minimal repro:
    def test(direction):
        return f"{'转入' if direction == '0' else '转出'}极"
        
  Decompiled as:
    def test(direction):
        return f"{'转入' if direction == '0' else '转出'}"
  (trailing '极' is lost)
""")
