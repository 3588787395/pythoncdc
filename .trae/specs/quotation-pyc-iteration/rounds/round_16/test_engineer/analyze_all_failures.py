"""R16 测试工程师：分析所有失败函数的 diff 模式。"""
import sys
import types
import marshal
import dis
import re
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r16_decompiled.py'


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


def get_instr_list(code):
    instrs = []
    for ins in dis.get_instructions(code):
        instrs.append((ins.offset, ins.opname, repr(ins.argval)))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    common = set(pyc_codes.keys()) & set(src_codes.keys())

    exact_match = []
    instr_diff = []

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        p_instrs = get_instr_list(pc)
        s_instrs = get_instr_list(sc)
        if p_instrs == s_instrs:
            exact_match.append(name)
        else:
            instr_diff.append((name, p_instrs, s_instrs))

    print(f"完全匹配: {len(exact_match)} / {len(common)}")
    print(f"指令差异: {len(instr_diff)}")

    # 分析差异模式
    patterns = Counter()
    detail = []
    for name, p, s in instr_diff:
        # 计算长度差
        delta = len(s) - len(p)
        # 找出第一个差异
        first_diff = None
        for i, (pi, si) in enumerate(zip(p, s)):
            if pi != si:
                first_diff = (pi, si)
                break

        # 分类
        if delta != 0:
            patterns['length_diff'] += 1
            detail.append((name, f'length_diff delta={delta}', first_diff))
        elif first_diff:
            p_off, p_op, p_arg = first_diff[0]
            s_off, s_op, s_arg = first_diff[1]
            if p_op != s_op:
                key = f'opname_diff:{p_op}_vs_{s_op}'
                patterns[key] += 1
                detail.append((name, key, first_diff))
            elif p_arg != s_arg:
                # 跳转目标差异
                if 'JUMP' in p_op or 'POP_JUMP' in p_op:
                    try:
                        d = int(s_arg) - int(p_arg)
                        key = f'jump_target_diff:delta={d}'
                        patterns[key] += 1
                        detail.append((name, key, first_diff))
                    except ValueError:
                        key = f'argval_diff:{p_op}'
                        patterns[key] += 1
                        detail.append((name, key, first_diff))
                else:
                    key = f'argval_diff:{p_op}'
                    patterns[key] += 1
                    detail.append((name, key, first_diff))

    print(f"\n=== 差异模式分布 ===")
    for pat, cnt in patterns.most_common():
        print(f"  {pat}: {cnt}")

    print(f"\n=== 前 30 个失败函数详情 ===")
    for name, pat, first_diff in detail[:30]:
        short_name = name.replace('<module>.', '')
        print(f"  {short_name:35s} {pat}")
        if first_diff:
            p_off, p_op, p_arg = first_diff[0]
            s_off, s_op, s_arg = first_diff[1]
            print(f"    pyc:  {p_off:4d} {p_op:25s} {p_arg}")
            print(f"    src:  {s_off:4d} {s_op:25s} {s_arg}")


if __name__ == '__main__':
    main()
