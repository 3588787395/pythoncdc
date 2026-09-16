import sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg import decompile_file
result = decompile_file(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc')
lines = result.split('\n')
in_func = False
brace = 0
for line in lines:
    if 'def handle_exrights' in line:
        in_func = True
    if in_func:
        print(line)
        if line.strip().startswith('def ') and 'handle_exrights' not in line:
            break
