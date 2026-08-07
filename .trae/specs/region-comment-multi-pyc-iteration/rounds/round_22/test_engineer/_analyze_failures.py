"""R22: analyze partial pyc failure patterns"""
import json, os
import sys
import marshal
import types
import dis

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

INDEX_PATH = r'f:/Downloads/pythoncdc-main/pyc_index.json'

with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    index = json.load(f)

# Find partial entries with significant function counts
partial = [(i, e) for i, e in enumerate(index)
           if e.get('decompile_status') == 'partial'
           and e.get('function_count', 0) > 5]

# Sort by match rate (lowest first) with significant function count
partial.sort(key=lambda x: x[1].get('bytecode_match_rate', 0))

print(f'Partial pyc files with >5 functions: {len(partial)}')
print(f'\nWorst 15 by match rate:')
for idx, entry in partial[:15]:
    rate = entry.get('bytecode_match_rate', 0)
    name = os.path.basename(entry['path'])
    fc = entry.get('function_count', 0)
    print(f'  {rate:.1%} ({fc} funcs): {name}')

# Now pick a representative partial pyc and analyze mismatched functions
# Pick one with medium function count and not too low rate
target = None
for idx, entry in partial:
    rate = entry.get('bytecode_match_rate', 0)
    fc = entry.get('function_count', 0)
    if 0.5 < rate < 0.9 and fc > 10:
        target = entry
        break

if target:
    pyc_path = target['path']
    name = os.path.basename(pyc_path)
    print(f'\n=== Target: {name} (rate={target["bytecode_match_rate"]:.1%}) ===')

    # Decompile and check
    from pycdc import decompile_pyc
    try:
        dec_src = decompile_pyc(pyc_path)
        ok_path = pyc_path.replace('.pyc', 'OK.py')

        # Load orig
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)

        # Compile dec
        compiled = compile(dec_src, '<dec>', 'exec')

        def collect(code, out):
            out.append(code)
            for c in code.co_consts:
                if isinstance(c, types.CodeType):
                    collect(c, out)
            return out

        orig_funcs = {c.co_name: c for c in collect(orig_code, [])}
        dec_funcs = {c.co_name: c for c in collect(compiled, [])}

        mismatches = []
        for name, oc in orig_funcs.items():
            dc = dec_funcs.get(name)
            if dc is None:
                mismatches.append((name, 'MISSING'))
                continue
            oi = [(i.opname, i.argval) for i in dis.get_instructions(oc)
                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')]
            di = [(i.opname, i.argval) for i in dis.get_instructions(dc)
                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')]
            if oi != di:
                mismatches.append((name, f'orig={len(oi)} dec={len(di)}'))

        print(f'Mismatched functions ({len(mismatches)}):')
        for fn, detail in mismatches[:10]:
            print(f'  {fn}: {detail}')
    except Exception as e:
        print(f'Error: {e}')
