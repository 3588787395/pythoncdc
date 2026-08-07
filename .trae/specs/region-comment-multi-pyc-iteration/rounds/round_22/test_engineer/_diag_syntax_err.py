"""R22: diagnose syntax error in a partial pyc"""
import sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

# Pick a small syntax-error pyc
PYC = r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/manager/instance.pyc'
OK_PATH = PYC.replace('.pyc', 'OK.py')

dec_src = decompile_pyc(PYC)
print(f'Decompiled source length: {len(dec_src)}')

# Save
with open(OK_PATH, 'w', encoding='utf-8') as f:
    f.write(dec_src)

# Try to compile
try:
    compile(dec_src, '<dec>', 'exec')
    print('Compile: OK')
except SyntaxError as se:
    print(f'Compile: SyntaxError at line {se.lineno}: {se.msg}')
    # Show context
    lines = dec_src.split('\n')
    for i in range(max(0, se.lineno - 3), min(len(lines), se.lineno + 2)):
        marker = '>>>' if i + 1 == se.lineno else '   '
        print(f'{marker} {i+1:4d}: {lines[i]}')
