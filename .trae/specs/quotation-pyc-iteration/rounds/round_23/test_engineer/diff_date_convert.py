"""R23-N4: 详细分析 date_convert 函数的 JUMP_FORWARD argval 差异"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


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

    pc = pyc_codes['date_convert']
    sc = src_codes['date_convert']
    pi = list(dis.get_instructions(pc))
    si = list(dis.get_instructions(sc))
    pi = [i for i in pi if i.opname not in ('EXTENDED_ARG', 'CACHE')]
    si = [i for i in si if i.opname not in ('EXTENDED_ARG', 'CACHE')]

    print(f"PYC len: {len(pi)}, SRC len: {len(si)}")
    print(f"PYC code size: {pc.co_code.__len__() if hasattr(pc.co_code, '__len__') else 'n/a'}")
    print(f"SRC code size: {sc.co_code.__len__() if hasattr(sc.co_code, '__len__') else 'n/a'}")

    # 找到首个分歧点
    i = j = 0
    diff_idx = None
    while i < len(pi) and j < len(si):
        if pi[i].opname != si[j].opname or (
            pi[i].argval != si[j].argval
            and not (isinstance(pi[i].argval, types.CodeType) and isinstance(si[j].argval, types.CodeType))
        ):
            diff_idx = (i, j)
            break
        i += 1
        j += 1

    if diff_idx is None:
        print("No diff found")
        return

    i, j = diff_idx
    print(f"\n首个分歧点: pyc[{i}]@{pi[i].offset} vs src[{j}]@{si[j].offset}")

    # 显示分歧点前后 30 条指令
    print(f"\n=== PYC (around {pi[i].offset}) ===")
    for k in range(max(0, i-10), min(len(pi), i+30)):
        mark = ">>>" if k == i else "   "
        print(f"  {mark} {pi[k].offset:4d}  {pi[k].opname:35s} {pi[k].argrepr}")

    print(f"\n=== SRC (around {si[j].offset}) ===")
    for k in range(max(0, j-10), min(len(si), j+30)):
        mark = ">>>" if k == j else "   "
        print(f"  {mark} {si[k].offset:4d}  {si[k].opname:35s} {si[k].argrepr}")

    # 检查 JUMP_FORWARD 差异
    print(f"\n=== JUMP_FORWARD 差异 ===")
    pyc_jumps = [(ins.offset, ins.argval, ins.argrepr) for ins in pi if ins.opname == 'JUMP_FORWARD']
    src_jumps = [(ins.offset, ins.argval, ins.argrepr) for ins in si if ins.opname == 'JUMP_FORWARD']
    print(f"PYC JUMP_FORWARD count: {len(pyc_jumps)}")
    print(f"SRC JUMP_FORWARD count: {len(src_jumps)}")
    for p_off, p_tgt, p_repr in pyc_jumps:
        match = next(((s_off, s_tgt, s_repr) for s_off, s_tgt, s_repr in src_jumps if s_off == p_off), None)
        if match:
            if match[1] != p_tgt:
                print(f"  JUMP_FORWARD @{p_off}: pyc→{p_tgt} ({p_repr}) vs src→{match[1]} ({match[2]}) (diff={match[1]-p_tgt})")
            else:
                print(f"  JUMP_FORWARD @{p_off}: BOTH→{p_tgt} ({p_repr})")
        else:
            print(f"  JUMP_FORWARD @{p_off}: only in PYC (→{p_tgt}, {p_repr})")
    for s_off, s_tgt, s_repr in src_jumps:
        if s_off not in [p[0] for p in pyc_jumps]:
            print(f"  JUMP_FORWARD @{s_off}: only in SRC (→{s_tgt}, {s_repr})")

    # 显示反编译源码
    print(f"\n=== SRC date_convert 源码 ===")
    import ast
    src_text = open(SRC, 'r', encoding='utf-8').read()
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'date_convert':
            print(ast.unparse(node))
            break


if __name__ == '__main__':
    main()
