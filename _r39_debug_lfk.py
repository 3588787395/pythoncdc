import sys, traceback
sys.path.insert(0, '.')
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc'

try:
    source = decompile_pyc(pyc_path)
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'load_from_kwargs' in line:
            for j in range(i, min(i+5, len(lines))):
                print(f"{j}: {lines[j]}")
            break
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
