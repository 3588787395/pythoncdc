"""R14 调试：显示 cash_collection_ability 的完整字节码对比。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r14_decompiled.py'


def load_pyc_code_objects(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    if not prefix:
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            _collect(c, result, name)


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code = compile(src, src_path, 'exec')
    result = {}
    _collect(code, result, prefix='')
    return result


def show_func(name, pyc_codes, src_codes, start=0, end=None):
    pc = pyc_codes.get(name)
    sc = src_codes.get(name)
    if pc is None or sc is None:
        print(f"  {name} not found")
        return
    pi = list(dis.get_instructions(pc))
    si = list(dis.get_instructions(sc))
    print(f"\n=== {name} ===")
    print(f"  pyc: {len(pi)} instrs, src: {len(si)} instrs")
    n = max(len(pi), len(si))
    for i in range(n):
        p = pi[i] if i < len(pi) else None
        s = si[i] if i < len(si) else None
        if p and p.offset < start:
            continue
        if end and p and p.offset > end:
            break
        p_str = f"{p.offset:4d} {p.opname:30s} {repr(p.argval)[:50]}" if p else "---"
        s_str = f"{s.offset:4d} {s.opname:30s} {repr(s.argval)[:50]}" if s else "---"
        mark = "  " if p_str == s_str else "!!"
        print(f"  {mark} pyc: {p_str}")
        print(f"  {mark} src: {s_str}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    # 只看前200条指令（差异在偏移142附近）
    show_func('<module>.cash_collection_ability', pyc_codes, src_codes, start=120, end=400)


if __name__ == '__main__':
    main()
