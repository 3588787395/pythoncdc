import json

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    data = json.load(f)

pending = [x for x in data if x['decompile_status'] != 'ok']
print(f'Total: {len(data)}, OK: {len(data) - len(pending)}, Pending: {len(pending)}')
if pending:
    print('Next pending file:', pending[0]['path'])
else:
    print('All files completed!')
