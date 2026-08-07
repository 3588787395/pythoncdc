import sys, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQData/plugins/plugin_system_db/iqdata_db_base.pyc'
source = decompile_pyc(pyc_path)

lines = source.split('\n')
for i, line in enumerate(lines):
    if '__load_table' in line or '__load_view' in line:
        print(f"{i}: {line}")
