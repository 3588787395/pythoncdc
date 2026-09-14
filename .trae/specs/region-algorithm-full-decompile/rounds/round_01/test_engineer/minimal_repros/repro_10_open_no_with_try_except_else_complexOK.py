# Source Generated with Decompyle++ (Python version)
# File: repro_10_open_no_with_try_except_else_complex.cpython-311.pyc (Python 3.11)

import json
import re
import os
def get_last_stat(user_id, trade_id):
    result_data = {'data': {'stat': {'alpha': {'time': [], 'value': []}}}, 'count': 0}
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
            readob = fp.read()
            readob = readob.decode('utf-8', 'ignore')
            if readob == 'end':
                if not fp:
                    fp.close()
                offset = len(paths)
                path = paths[offset - 2]
                fp = open(path, 'rb')
                readob = fp.read()
                readob = readob.decode('utf-8', 'ignore')
            readjson = json.loads(readob)
            result_data['data']['stat']['alpha']['time'].append(readjson.get('time'))
            index = 0
            for i in readjson.get('columns', []):
                if pattern.match(i):
                    index += 1
            item = readjson['data'][-1]
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
