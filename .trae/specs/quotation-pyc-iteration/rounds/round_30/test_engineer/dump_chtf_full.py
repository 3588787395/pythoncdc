"""R30-6: Dump full bytecode of change_his_to_forward for pyc and src."""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_30/test_engineer/r30_decompiled.py'


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


def show_full(name, pyc_codes, src_codes, start=100, end=220):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = list(dis.get_instructions(pc))
    si = list(dis.get_instructions(sc))
    print(f"\n=== {name}: pyc={len(pi)} src={len(si)} ===")
    print(f"\n--- pyc[{start}:{end}] ---")
    for i in range(start, min(end, len(pi))):
        ins = pi[i]
        offset = ins.offset
        print(f"  [{i:4d}] @{offset:4d} {ins.opname:25s} {repr(ins.argval)[:60]}")
    print(f"\n--- src[{start}:{end}] ---")
    for i in range(start, min(end, len(si))):
        ins = si[i]
        offset = ins.offset
        print(f"  [{i:4d}] @{offset:4d} {ins.opname:25s} {repr(ins.argval)[:60]}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    show_full('change_his_to_forward', pyc_codes, src_codes, 100, 220)


if __name__ == '__main__':
    main()
