"""R22: batch verify ALL pending pyc files and update index"""
import json
import os
import sys

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

INDEX_PATH = r'f:/Downloads/pythoncdc-main/pyc_index.json'

with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    index = json.load(f)

from scripts.pyc_batch_verify import decompile_single, bytecode_diff

# Find pending entries
pending = [(i, e) for i, e in enumerate(index) if e.get('decompile_status') == 'pending']
print(f'Pending pyc files: {len(pending)}')

verified = 0
ok_count = 0
partial_count = 0
error_count = 0

for idx, entry in pending:
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        dec_result = decompile_single(pyc_path)
        ok_py_path = dec_result.get('ok_py_path', '')
        if ok_py_path and os.path.exists(ok_py_path):
            diff_result = bytecode_diff(pyc_path, ok_py_path)
            matched = diff_result.get('matched_functions', 0)
            total = diff_result.get('total_functions', 0)
            rate = matched / total if total > 0 else 0
            status = 'ok' if rate == 1.0 else 'partial'

            index[idx]['decompile_status'] = status
            index[idx]['bytecode_match_rate'] = rate
            index[idx]['ok_py_generated'] = True
            index[idx]['last_tested_round'] = 22

            if status == 'ok':
                ok_count += 1
            else:
                partial_count += 1

            name = os.path.basename(pyc_path)
            sym = 'V' if status == 'ok' else 'X'
            print(f'  [{sym}] {name}: {matched}/{total} ({rate:.1%})')
        else:
            index[idx]['decompile_status'] = 'failed'
            index[idx]['last_tested_round'] = 22
            error_count += 1

        verified += 1
    except Exception as e:
        error_count += 1
        name = os.path.basename(pyc_path)
        print(f'  [!] {name}: ERROR {e}')

# Save
with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print(f'\nVerified: {verified}, OK: {ok_count}, Partial: {partial_count}, Error: {error_count}')
