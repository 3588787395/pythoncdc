import sys, os, marshal, types, importlib.util, dis
sys.path.insert(0, '.')

# Load real pyc via marshal (skip 16-byte header) to get code object
pyc = "site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc"
with open(pyc, 'rb') as f:
    data = f.read()
code = marshal.loads(data[16:])

def find(code, name):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            r = find(c, name)
            if r:
                return r

fn = find(code, 'get_stock_info')
print("=== ORIG get_stock_info ===")
dis.dis(fn)

ok_py = "site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_sourceOK.py"
src = open(ok_py, encoding='utf-8').read()
import re
m = re.search(r"    def get_stock_info.*?(?=\n    def |\nclass )", src, re.S)
print("\n=== DECOMPILED SOURCE ===")
print(m.group(0) if m else "NOT FOUND")
