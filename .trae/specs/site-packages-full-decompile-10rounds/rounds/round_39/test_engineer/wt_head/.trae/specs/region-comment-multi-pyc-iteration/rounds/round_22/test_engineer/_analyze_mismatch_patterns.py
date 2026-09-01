"""R22: analyze mismatch patterns in non-syntax-error partial pyc"""
import json, os, sys, marshal, types, dis
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

INDEX_PATH = r'f:/Downloads/pythoncdc-main/pyc_index.json'
with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    index = json.load(f)

from pycdc import decompile_pyc

partial = [(i, e) for i, e in enumerate(index)
           if e.get('decompile_status') == 'partial'
           and 0 < e.get('bytecode_match_rate', 0) < 1.0
           and e.get('function_count', 0) > 5]

# Sort by function count descending
partial.sort(key=lambda x: -x[1].get('function_count', 0))

print(f'Partial pyc files with 0<rate<1 and >5 funcs: {len(partial)}')
print(f'\nTop 15 by function count:')
for idx, entry in partial[:15]:
    rate = entry.get('bytecode_match_rate', 0)
    name = os.path.basename(entry['path'])
    fc = entry.get('function_count', 0)
    matched = int(fc * rate)
    print(f'  {matched}/{fc} ({rate:.1%}): {name}')

# Pick the first and analyze mismatch patterns
target = partial[0][1] if partial else None
if not target:
    print('No target found')
    sys.exit(0)

pyc_path = target['path']
name = os.path.basename(pyc_path)
print(f'\n=== Analyzing: {name} ===')

try:
    dec_src = decompile_pyc(pyc_path)
    compiled = compile(dec_src, '<dec>', 'exec')

    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)

    def collect(code, out):
        out.append(code)
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                collect(c, out)
        return out

    orig_funcs = {}
    for c in collect(orig_code, []):
        orig_funcs.setdefault(c.co_name, []).append(c)
    dec_funcs = {}
    for c in collect(compiled, []):
        dec_funcs.setdefault(c.co_name, []).append(c)

    mismatches = []
    for fn, ocs in orig_funcs.items():
        dcs = dec_funcs.get(fn, [])
        for oi, oc in enumerate(ocs):
            if oi < len(dcs):
                dc = dcs[oi]
                oi_len = len([1 for i in dis.get_instructions(oc) if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL','EXTENDED_ARG')])
                di_len = len([1 for i in dis.get_instructions(dc) if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL','EXTENDED_ARG')])
                if oi_len != di_len:
                    mismatches.append((fn, oi_len, di_len, oi_len - di_len))
            else:
                mismatches.append((fn, -1, -1, 'MISSING'))

    print(f'Mismatched functions ({len(mismatches)}):')
    for fn, ol, dl, diff in mismatches[:15]:
        if diff == 'MISSING':
            print(f'  {fn}: MISSING in dec')
        else:
            print(f'  {fn}: orig={ol} dec={dl} diff={diff:+d}')
except Exception as e:
    print(f'Error: {e}')
