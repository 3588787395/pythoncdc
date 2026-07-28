"""R23-N19: 汇总所有失败函数的第一个opcode差异"""
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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval, ins.argrepr))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r23_failures.txt', 'r') as f:
        failures = [l.strip() for l in f if l.strip()]

    for name in failures:
        if name not in pyc_codes or name not in src_codes:
            continue
        pa = get_instr_list(pyc_codes[name])
        sa = get_instr_list(src_codes[name])
        # 找第一个 opname 或 argval(非跳转target) 差异
        first_opname_diff = None
        first_real_diff = None  # 非jump target差异
        for i in range(max(len(pa), len(sa))):
            a = pa[i] if i < len(pa) else None
            b = sa[i] if i < len(sa) else None
            if a is None or b is None:
                first_opname_diff = (i, a, b)
                break
            if a[1] != b[1]:  # opname不同
                first_opname_diff = (i, a, b)
                break
            if a[2] != b[2]:  # argval不同
                is_jump = 'JUMP' in a[1] or 'IF_' in a[1] or 'BACKWARD' in a[1]
                if not is_jump:
                    first_real_diff = (i, a, b)
                    break
                if first_real_diff is None:
                    first_real_diff = (i, a, b)  # 记录第一个jump target差异

        if first_opname_diff:
            i, a, b = first_opname_diff
            a_str = f"@{a[0]} {a[1]} {a[3]}" if a else "(none)"
            b_str = f"@{b[0]} {b[1]} {b[3]}" if b else "(none)"
            print(f"  {name:30s} OPNAME_DIFF @{i}: a={a_str} | b={b_str}")
        elif first_real_diff:
            i, a, b = first_real_diff
            a_str = f"@{a[0]} {a[1]} {a[3]}" if a else "(none)"
            b_str = f"@{b[0]} {b[1]} {b[3]}" if b else "(none)"
            print(f"  {name:30s} JUMP_TGT_DIFF @{i}: a={a_str} | b={b_str}")
        else:
            print(f"  {name:30s} NO DIFF FOUND")


if __name__ == '__main__':
    main()
