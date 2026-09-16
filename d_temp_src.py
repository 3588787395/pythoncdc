import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import decompile_pyc
src = decompile_pyc('F:/Downloads/pythoncdc-main/site-packages/IQCommon/util/replace_utils.pyc')
lines = src.split('\n')
for i, line in enumerate(lines):
    if 'decrypt_database_url' in line or (i >= 140 and i <= 200):
        print(f'{i+1:4d}: {line}')
