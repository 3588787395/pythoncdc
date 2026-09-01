"""R24-N1 调试：valuation_new 函数指令大量丢失（91 vs 334）"""
import sys
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code_obj = compile(src, '<decompiled>', 'exec')
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


pyc_codes = load_pyc_code_objects(PYC)
src_codes = load_src_code_objects(SRC)

for name in ['valuation_new', 'valuation', 'fill_minute_or_day_blank', 'get_str_data', 'change_his_to_backward', 'load_get_price']:
    print(f"\n=== {name} ===")
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(pc) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    si = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(sc) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    print(f"pyc: {len(pi)} instrs, src: {len(si)} instrs, loss: {len(pi) - len(si)}")
    print(f"  First 15 pyc instrs:")
    for i, x in enumerate(pi[:15]):
        print(f"    [{i:3d}] {x[0]:4d} {x[1]:30s} {x[3]}")
    print(f"  First 15 src instrs:")
    for i, x in enumerate(si[:15]):
        print(f"    [{i:3d}] {x[0]:4d} {x[1]:30s} {x[3]}")
    print(f"  Last 10 pyc instrs:")
    for x in pi[-10:]:
        print(f"    {x[0]:4d} {x[1]:30s} {x[3]}")
    print(f"  Last 10 src instrs:")
    for x in si[-10:]:
        print(f"    {x[0]:4d} {x[1]:30s} {x[3]}")
