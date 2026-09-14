# Source Generated with Decompyle++ (Python version)
# File: repro_10_open_no_with_try_except_else_missing_else.cpython-311.pyc (Python 3.11)

import json
import re
import os
def get_last_stat(user_id, trade_id):
    result_data = {'data': {'stat': {'alpha': {'time': [], 'value': []}}}, 'count': 0, 'offset': 0}
    pattern = re.compile('^a_')
    count = 0
    testds_dir = f'/tmp/{user_id!s}/result/{trade_id!s}/'
    paths = []
    for parent, dirnames, filenames in os.walk(testds_dir):
        for fi in filenames:
            if fi.startswith('testds'):
                paths.append(parent + fi)
    paths.sort()
    offset = len(paths)
    if offset >= 1:
        path = paths[offset - 1]
        fp = open(path, 'rb')
        try:
            data = fp.read()
            data = data.decode('utf-8', 'ignore')
            if data == 'end':
                if not fp:
                    fp.close()
                offset = len(paths)
                path = paths[offset - 2]
                fp = open(path, 'rb')
                data = fp.read()
                data = data.decode('utf-8', 'ignore')
            parsed = json.loads(data)
            result_data['data']['stat']['alpha']['time'].append(parsed.get('time'))
            index = 0
            for i in parsed.get('columns', []):
                if pattern.match(i):
                    index += 1
            item = parsed['data'][-1]
            result_data['data']['stat']['alpha']['value'].append(item[2 + index])
            if item[12 + index]:
                count = 1
            if fp is not None:
                fp.close()
        except BaseException:
            print('parse error')
    result_data['count'] = count
    result_data['offset'] = offset
    return result_data
