"""R23-N19: 分析 get_cb_calender_info 的差异 (p=380, s=381)"""
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

    name = 'get_cb_calender_info'
    pa = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(pyc_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    sa = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(src_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    print(f"=== {name} PYC vs SRC (p={len(pa)}, s={len(sa)}) ===")

    # 对齐 opname 序列找差异
    i = 0
    j = 0
    while i < len(pa) or j < len(sa):
        a = pa[i] if i < len(pa) else None
        b = sa[j] if j < len(sa) else None
        if a is None:
            print(f"  EXTRA in SRC @{b[0]:4d}: {b[1]:30s} {b[3]}")
            j += 1
            continue
        if b is None:
            print(f"  EXTRA in PYC @{a[0]:4d}: {a[1]:30s} {a[3]}")
            i += 1
            continue
        if a[1] != b[1]:
            if i + 1 < len(pa) and pa[i+1][1] == b[1]:
                print(f"  EXTRA in PYC @{a[0]:4d}: {a[1]:30s} {a[3]}")
                i += 1
                continue
            elif j + 1 < len(sa) and sa[j+1][1] == a[1]:
                print(f"  EXTRA in SRC @{b[0]:4d}: {b[1]:30s} {b[3]}")
                j += 1
                continue
            else:
                # 打印周围上下文
                start = max(0, i - 5)
                end = min(max(len(pa), len(sa)), i + 15)
                for k in range(start, end):
                    aa = pa[k] if k < len(pa) else None
                    bb = sa[k] if k < len(sa) else None
                    aa_str = f"@{aa[0]:4d} {aa[1]:30s} {aa[3]}" if aa else "(none)"
                    bb_str = f"@{bb[0]:4d} {bb[1]:30s} {bb[3]}" if bb else "(none)"
                    match = "OK" if aa and bb and aa[1] == bb[1] and aa[2] == bb[2] else "!!"
                    print(f"  {match} a: {aa_str}")
                    print(f"  {match} b: {bb_str}")
                i += 1
                j += 1
                continue
        if a[2] != b[2]:
            is_jump = 'JUMP' in a[1] or 'IF_' in a[1] or 'BACKWARD' in a[1]
            if not is_jump:
                print(f"  ARGVAL DIFF: a=@{a[0]:4d} {a[1]:30s} {a[3]} | b=@{b[0]:4d} {b[1]:30s} {b[3]}")
        i += 1
        j += 1


if __name__ == '__main__':
    main()
