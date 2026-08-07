import sys
sys.path.insert(0, '.')
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc'
source = decompile_pyc(pyc_path)
lines = source.split('\n')
in_func = False
for i, line in enumerate(lines):
    if 'def load_from_kwargs' in line:
        in_func = True
    if in_func:
        print(f"{i}: {line}")
        if in_func and line.strip().startswith('def ') and i > 0 and 'load_from_kwargs' not in line:
            break
        if in_func and i > 0 and (line.strip().startswith('def ') or line.strip().startswith('class ')) and 'load_from_kwargs' not in line:
            break
