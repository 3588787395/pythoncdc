import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'
source = decompile_pyc(pyc)
# Print just the match function
lines = source.split('\n')
in_match = False
indent = 0
for i, line in enumerate(lines):
    if 'def match(self, open_orders):' in line:
        in_match = True
    if in_match:
        print(f'{i+1:4d}: {line}')
        if line and not line[0].isspace() and i > 0 and 'def match' not in line:
            break
