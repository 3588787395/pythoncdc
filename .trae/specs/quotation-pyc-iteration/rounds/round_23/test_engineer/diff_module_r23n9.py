"""R23-N9 调试 <module> 的 opname 差异"""
import sys
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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    name = '<module>'
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = []
    for ins in dis.get_instructions(pc):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        pi.append(ins)
    si = []
    for ins in dis.get_instructions(sc):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        si.append(ins)
    # Find first diff
    for i in range(min(len(pi), len(si))):
        p = pi[i]
        s = si[i]
        if p.opname != s.opname or p.argval != s.argval:
            print(f"First diff at idx {i} (offset P={p.offset} S={s.offset})")
            ctx_start = max(0, i - 5)
            ctx_end = min(len(pi), i + 10)
            print(f"--- PYC context [{ctx_start}:{ctx_end}] ---")
            for j in range(ctx_start, ctx_end):
                pp = pi[j]
                marker = ">>>" if j == i else "   "
                print(f"  {marker} P: {pp.offset:>6} {pp.opname:<35} argval={repr(pp.argval)[:60]}")
            print(f"--- SRC context [{ctx_start}:{min(len(si), ctx_end)}] ---")
            for j in range(ctx_start, min(len(si), ctx_end)):
                ss = si[j]
                marker = ">>>" if j == i else "   "
                print(f"  {marker} S: {ss.offset:>6} {ss.opname:<35} argval={repr(ss.argval)[:60]}")
            break


if __name__ == '__main__':
    main()
