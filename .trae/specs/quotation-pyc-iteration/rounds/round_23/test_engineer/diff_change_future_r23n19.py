"""R23-N19 调试 change_future_real_date 的字节码差异"""
import sys
import dis
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

pyc_codes = {}
def walk_pyc(co, prefix=''):
    name = prefix + co.co_name if prefix else co.co_name
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    pyc_codes[name] = co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            walk_pyc(const, sub_prefix)
walk_pyc(code_obj)

with open(SRC, 'r', encoding='utf-8') as f:
    src = f.read()
src_co = compile(src, '<decompiled>', 'exec')
src_codes = {}
def walk_src(co, prefix=''):
    name = prefix + co.co_name if prefix else co.co_name
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    src_codes[name] = co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            walk_src(const, sub_prefix)
walk_src(src_co)

name = 'change_future_real_date'
pa = [(ins.offset, ins.opname, ins.argval, getattr(ins, 'argrepr', ins.arg if ins.arg is not None else '')) for ins in dis.get_instructions(pyc_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
sa = [(ins.offset, ins.opname, ins.argval, getattr(ins, 'argrepr', ins.arg if ins.arg is not None else '')) for ins in dis.get_instructions(src_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
print(f"=== {name} PYC vs SRC (p={len(pa)}, s={len(sa)}) ===")
max_len = max(len(pa), len(sa))
first_diff = None
for i in range(max_len):
    a = pa[i] if i < len(pa) else None
    b = sa[i] if i < len(sa) else None
    if a is None or b is None or a[1] != b[1] or a[2] != b[2]:
        first_diff = i
        break
start = max(0, first_diff - 10)
end = min(max_len, first_diff + 40)
for i in range(start, end):
    a = pa[i] if i < len(pa) else None
    b = sa[i] if i < len(sa) else None
    a_str = f"@{a[0]:4d} {a[1]:30s} {a[3]}" if a else "(none)"
    b_str = f"@{b[0]:4d} {b[1]:30s} {b[3]}" if b else "(none)"
    match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
    print(f"  {match} a: {a_str}")
    print(f"  {match} b: {b_str}")
