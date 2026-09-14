#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode
import marshal, types, py_compile

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

with open('pyc_index.json') as f:
    entries = json.load(f)

partials = [e for e in entries if e.get('decompile_status') == 'partial']
partials.sort(key=lambda e: e.get('match_rate', 1.0))

other_mismatches = []

for entry in partials:
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        orig_code = load_pyc_code(pyc_path)
        orig_map = extract_code_objects(orig_code)
        source = decompile_pyc(pyc_path)
        ok_py = pyc_path.replace('.pyc', 'OK.py')
        with open(ok_py, 'w', encoding='utf-8') as f:
            f.write(source)
        cfile = py_compile.compile(ok_py, doraise=True, quiet=2)
        if cfile is None:
            import importlib.util
            cfile = importlib.util.cache_from_source(ok_py)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
        decomp_map = extract_code_objects(decomp_code)
        common = set(orig_map.keys()) & set(decomp_map.keys())
        for name in sorted(common):
            cmp = compare_bytecode(orig_map[name], decomp_map[name])
            if cmp.get('match') or cmp.get('jump_only'):
                continue
            true_diffs = cmp.get('true_diffs', [])
            jump_diffs = cmp.get('jump_diffs', [])
            first_diff = true_diffs[0] if true_diffs else (jump_diffs[0] if jump_diffs else None)
            if first_diff is None:
                continue
            orig_op = first_diff.get('orig_op', '')
            decomp_op = first_diff.get('decomp_op', '')
            orig_arg = first_diff.get('orig_arg', '')
            decomp_arg = first_diff.get('decomp_arg', '')

            is_with = (orig_op in ('BEFORE_WITH', 'SETUP_WITH') or decomp_op in ('BEFORE_WITH', 'SETUP_WITH')
                       or (orig_op == 'PUSH_NULL' and decomp_op in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_CONST'))
                       or (orig_op == 'SWAP' and decomp_op == 'POP_TOP'))
            is_try = (orig_op == 'PUSH_EXC_INFO' or decomp_op == 'PUSH_EXC_INFO'
                      or (orig_op == 'POP_EXCEPT' and decomp_op != 'POP_EXCEPT')
                      or (orig_op == 'JUMP_FORWARD' and decomp_op in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_CONST', 'LOAD_ATTR'))
                      or (decomp_op == 'JUMP_FORWARD' and orig_op in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_CONST', 'LOAD_ATTR'))
                      or (orig_op == 'JUMP_BACKWARD' and decomp_op in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_CONST', 'POP_TOP'))
                      or (decomp_op == 'JUMP_BACKWARD' and orig_op in ('LOAD_CONST', 'POP_TOP', 'LOAD_FAST'))
                      or (orig_op.startswith('POP_JUMP_') and decomp_op in ('POP_TOP', 'JUMP_FORWARD'))
                      or (decomp_op.startswith('POP_JUMP_') and orig_op in ('POP_TOP', 'JUMP_FORWARD', 'LOAD_CONST'))
                      or (orig_op == 'POP_JUMP_FORWARD_IF_NONE' and decomp_op == 'POP_JUMP_FORWARD_IF_TRUE'))
            is_return = (orig_op == 'RETURN_VALUE' and decomp_op == 'POP_TOP') or (orig_op == 'POP_TOP' and decomp_op == 'RETURN_VALUE')
            is_for_while = (orig_op == 'LOAD_CONST' and decomp_op in ('JUMP_BACKWARD', 'PUSH_EXC_INFO'))
            is_boolop = (orig_op in ('LOAD_FAST', 'LOAD_GLOBAL') and decomp_op in ('LOAD_FAST', 'LOAD_GLOBAL') and orig_arg != decomp_arg)
            is_break = (orig_op in ('BREAK', 'CONTINUE') and decomp_op not in ('BREAK', 'CONTINUE')) or (decomp_op in ('BREAK', 'CONTINUE') and orig_op not in ('BREAK', 'CONTINUE'))
            is_is = ('COMPARE_OP' in orig_op and 'is' in str(orig_arg).lower()) or ('COMPARE_OP' in decomp_op and 'is' in str(decomp_arg).lower())

            if not is_with and not is_try and not is_return and not is_for_while and not is_boolop and not is_break and not is_is:
                other_mismatches.append({
                    'file': os.path.basename(pyc_path),
                    'func': name,
                    'orig_op': orig_op,
                    'decomp_op': decomp_op,
                    'orig_arg': orig_arg,
                    'decomp_arg': decomp_arg,
                    'true_diffs': len(true_diffs),
                    'jump_diffs': len(jump_diffs),
                    'orig_count': cmp.get('orig_count', 0),
                    'decomp_count': cmp.get('decomp_count', 0),
                })
    except Exception as e:
        pass

patterns = {}
for m in other_mismatches:
    key = m['orig_op'] + ' vs ' + m['decomp_op']
    if key not in patterns:
        patterns[key] = []
    patterns[key].append(m)

print('OTHER sub-patterns:')
for key, items in sorted(patterns.items(), key=lambda x: -len(x[1])):
    print(f'  {key}: {len(items)} functions')
    for m in items[:3]:
        print(f'    {m["file"]}:{m["func"]} td={m["true_diffs"]} orig_arg={m["orig_arg"]} decomp_arg={m["decomp_arg"]}')
