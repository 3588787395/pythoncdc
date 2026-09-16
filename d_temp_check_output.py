import sys, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc'
result = decompile_pyc(pyc)
# Print just the setup function
lines = result.split('\n')
in_setup = False
for line in lines:
    if 'def setup' in line:
        in_setup = True
    if in_setup:
        print(line)
        if line and not line.startswith(' ') and not line.startswith('\t') and 'def ' in line and 'setup' not in line:
            break
        if in_setup and line.strip().startswith('def ') and 'setup' not in line:
            break
