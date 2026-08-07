import sys
sys.path.insert(0, '.')
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_accounts/account_model/future_account.pyc'
source = decompile_pyc(pyc_path)
lines = source.split('\n')
in_func = False
for i, line in enumerate(lines):
    if 'def _on_settlement' in line:
        in_func = True
    if in_func:
        print(f"{i}: {line}")
        if in_func and i > 0 and line.strip().startswith('def ') and '_on_settlement' not in line:
            break
