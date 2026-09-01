"""R30 测试工程师：完整对比get_option_info的字节码"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r30_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    codes = {}
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(code_obj)
    return codes


def load_src_code_objects(src_path):
    with open(src_path) as f:
        src = f.read()
    codes = {}
    mod = compile(src, src_path, 'exec')
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(mod)
    return codes


def dump(co, label):
    print(f"\n=== {label} {co.co_name} (argcount={co.co_argcount}) ===")
    for ins in dis.get_instructions(co):
        print(f"  {ins.offset:4d}: {ins.opname:30s} {ins.argval}")


pyc_codes = load_pyc_code_objects(PYC)
src_codes = load_src_code_objects(SRC)

dump(pyc_codes['get_option_info'], 'PYC')
dump(src_codes['get_option_info'], 'SRC')
