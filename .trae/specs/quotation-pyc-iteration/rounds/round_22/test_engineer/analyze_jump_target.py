"""R22 测试工程师：详细分析 jump_target 类失败函数的指令差异。
重点分析最小的几个 case: get_quote, convert_to_list, get_holiday_online。
"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'

TARGETS = ['get_quote', 'convert_to_list', 'get_holiday_online',
           'get_index_stocks', 'get_fundflow_day', 'get_block_stocks']


def load_pyc_code_objects(pyc_path):
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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append(ins)
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for name in TARGETS:
        if name not in pyc_codes or name not in src_codes:
            print(f"\n{'='*70}")
            print(f"[SKIP] {name} not found")
            continue
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)

        print(f"\n{'='*70}")
        print(f"=== {name} ===  pyc={len(pi)} instrs, src={len(si)} instrs")
        print(f"  pyc co_varnames={pc.co_varnames}")
        print(f"  src co_varnames={sc.co_varnames}")
        print(f"  pyc co_consts={pc.co_consts[:20]}")
        print(f"  src co_consts={sc.co_consts[:20]}")

        # Find first diff
        min_len = min(len(pi), len(si))
        first_diff = None
        for i in range(min_len):
            a = pi[i]
            b = si[i]
            if a.opname != b.opname or a.argval != b.argval:
                first_diff = i
                break

        # Show instructions with diff context
        print(f"\n  --- instructions (first_diff={first_diff}) ---")
        max_len = max(len(pi), len(si))
        for i in range(max_len):
            a = pi[i] if i < len(pi) else None
            b = si[i] if i < len(si) else None
            mark = ''
            if a and b:
                if a.opname != b.opname or a.argval != b.argval:
                    mark = '  <<< DIFF'
            elif a or b:
                mark = '  <<< LEN_DIFF'
            a_str = f"{a.offset:4d} {a.opname:35s} {a.argval!r}" if a else f"{'':4s} {'(none)':35s}"
            b_str = f"{b.offset:4d} {b.opname:35s} {b.argval!r}" if b else f"{'':4s} {'(none)':35s}"
            print(f"  [{i:3d}] PYC: {a_str}")
            print(f"        SRC: {b_str}{mark}")
            # Stop after a few diffs
            if mark and i > (first_diff or 0) + 15:
                print(f"  ... (truncated, showing first ~15 diffs)")
                break

    # Now also dump the decompiled source for get_quote
    print(f"\n{'='*70}")
    print("=== get_quote decompiled source ===")
    with open(SRC) as f:
        src = f.read()
    import ast
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'get_quote':
            print(ast.unparse(node))
            break


if __name__ == '__main__':
    main()
