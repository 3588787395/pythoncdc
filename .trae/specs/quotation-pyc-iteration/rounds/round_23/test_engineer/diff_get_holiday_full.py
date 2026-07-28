"""R23-N19: 找出 get_holiday_online 中PYC比SRC多出的指令"""
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

    name = 'get_holiday_online'
    pa = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(pyc_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]
    sa = [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(src_codes[name]) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]

    # 找出所有 opname 不同的位置（忽略 offset 和 jump target 差异）
    print(f"=== {name} (p={len(pa)}, s={len(sa)}) ===")
    # 用 opname 序列对齐
    i = 0
    j = 0
    while i < len(pa) or j < len(sa):
        a = pa[i] if i < len(pa) else None
        b = sa[j] if j < len(sa) else None
        if a is None:
            print(f"  EXTRA in SRC: {b[0]:4d} {b[1]:30s} {b[3]}")
            j += 1
            continue
        if b is None:
            print(f"  EXTRA in PYC: {a[0]:4d} {a[1]:30s} {a[3]}")
            i += 1
            continue
        if a[1] != b[1]:
            # opname不同，可能是多出的指令
            # 尝试看下一个SRC是否匹配PYC
            if i + 1 < len(pa) and pa[i+1][1] == b[1]:
                print(f"  EXTRA in PYC: {a[0]:4d} {a[1]:30s} {a[3]}")
                i += 1
                continue
            elif j + 1 < len(sa) and sa[j+1][1] == a[1]:
                print(f"  EXTRA in SRC: {b[0]:4d} {b[1]:30s} {b[3]}")
                j += 1
                continue
            else:
                print(f"  DIFF: a={a[0]:4d} {a[1]:30s} {a[3]} | b={b[0]:4d} {b[1]:30s} {b[3]}")
                i += 1
                j += 1
                continue
        # opname相同，检查argval
        if a[2] != b[2]:
            # argval不同（可能是jump target偏移）
            # 检查是否只是offset偏移
            if 'JUMP' in a[1] or 'IF_' in a[1]:
                # 跳转指令，可能是target偏移
                pass
            else:
                print(f"  ARGVAL DIFF: a={a[0]:4d} {a[1]:30s} {a[3]} | b={b[0]:4d} {b[1]:30s} {b[3]}")
        i += 1
        j += 1

    # 打印 offset 320 之后的完整对比
    print(f"\n=== offset 320+ 完整对比 ===")
    for idx in range(len(pa)):
        a = pa[idx]
        if a[0] < 320:
            continue
        b = sa[idx] if idx < len(sa) else None
        a_str = f"{a[0]:4d} {a[1]:30s} {a[3]}" if a else "(none)"
        b_str = f"{b[0]:4d} {b[1]:30s} {b[3]}" if b else "(none)"
        match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
        print(f"  {match} a: {a_str}")
        print(f"  {match} b: {b_str}")


if __name__ == '__main__':
    main()
