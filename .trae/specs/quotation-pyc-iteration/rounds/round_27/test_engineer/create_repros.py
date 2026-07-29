"""R27 测试工程师：创建10+最小复现实例，验证IF_NONE/IF_NOT_NONE组成的AND链未被识别为BoolOpRegion的问题。

核心问题：`if A is not None and B is None:` 编译为 IF_NONE + IF_NOT_NONE（均跳转到同一merge），
当前反编译器的inline_boolop_chain检测仅接受IF_FALSE，导致该模式被识别为嵌套if-else而非AND链，
生成的字节码跳转目标偏移。

区域归约算法原则：
- 原则1（归约顺序）：从最内层到最外层识别区域。BoolOpRegion是最内层，应优先于IfRegion识别。
- 原则2（唯一归属）：每个块在任何层级只属于一个区域。条件块属于BoolOpRegion，不属于IfRegion的then/else。
- 原则3（嵌套抽象）：嵌套区域在父区域中作为单个抽象节点。
- 原则4（父引用子入口）：归约后父区域的then/else列表引用子区域的入口。

AND链的语义不变量：所有条件块跳转到同一merge点（else后继），fall-through到达body（then后继）。
这与opname无关——IF_FALSE、IF_NONE、IF_NOT_NONE均可构成AND链，只要跳转目标一致且指向merge。
"""
import os
import sys
import dis
import py_compile

sys.path.insert(0, '/workspace')

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_27/test_engineer/minimal_repros'
os.makedirs(OUT_DIR, exist_ok=True)

# 10+ 最小复现实例：覆盖 IF_NONE/IF_NOT_NONE 组成的 AND 链的各种变体
CASES = [
    ('repro_r27_01_and_is_not_none_and_is_none',
     'def f(a, b):\n    if a is not None and b is None:\n        return 1\n    return 0\n'),
    ('repro_r27_02_and_is_none_and_is_not_none',
     'def f(a, b):\n    if a is None and b is not None:\n        return 1\n    return 0\n'),
    ('repro_r27_03_and_is_not_none_and_is_not_none',
     'def f(a, b):\n    if a is not None and b is not None:\n        return 1\n    return 0\n'),
    ('repro_r27_04_and_is_none_and_is_none',
     'def f(a, b):\n    if a is None and b is None:\n        return 1\n    return 0\n'),
    ('repro_r27_05_and_three_is_not_none',
     'def f(a, b, c):\n    if a is not None and b is not None and c is not None:\n        return 1\n    return 0\n'),
    ('repro_r27_06_and_mixed_none_checks',
     'def f(a, b, c):\n    if a is not None and b is None and c is not None:\n        return 1\n    return 0\n'),
    ('repro_r27_07_and_none_in_elif',
     'def f(a, b):\n    if a is None:\n        return 0\n    elif a is not None and b is None:\n        return 1\n    return 2\n'),
    ('repro_r27_08_and_none_with_assign_body',
     'def f(a, b, params):\n    if a is not None and b is None:\n        params[\'x\'] = a\n    elif a is None and b is not None:\n        params[\'y\'] = b\n    elif a is not None and b is not None:\n        params[\'x\'] = a\n        params[\'y\'] = b\n'),
    ('repro_r27_09_and_none_share_change_pattern',
     'def f(start_year, end_year, params):\n    if start_year is not None and end_year is None:\n        params[\'start_year\'] = start_year\n    elif start_year is None and end_year is not None:\n        params[\'end_year\'] = end_year\n    elif start_year is not None and end_year is not None:\n        params[\'start_year\'] = start_year\n        params[\'end_year\'] = end_year\n'),
    ('repro_r27_10_and_none_with_continue',
     'def f(items):\n    for i in items:\n        if i is not None and i > 0:\n            continue\n        return i\n    return None\n'),
    ('repro_r27_11_and_none_nested_in_while',
     'def f(a, b):\n    while True:\n        if a is not None and b is None:\n            return 1\n        elif a is None and b is not None:\n            return 2\n        break\n    return 0\n'),
    ('repro_r27_12_and_none_three_branches',
     'def f(a, b, c):\n    if a is not None and b is None:\n        return 1\n    elif a is None and c is not None:\n        return 2\n    elif b is not None and c is None:\n        return 3\n    return 0\n'),
]


def main():
    from pycdc import decompile_pyc

    results = []
    for name, src in CASES:
        src_path = os.path.join(OUT_DIR, name + '.py')
        pyc_path = os.path.join(OUT_DIR, name + '.pyc')
        dec_path = os.path.join(OUT_DIR, name + '_decompiled.py')

        with open(src_path, 'w', encoding='utf-8') as f:
            f.write(src)

        py_compile.compile(src_path, pyc_path, doraise=True)

        # 反编译
        try:
            dec_src = decompile_pyc(pyc_path, use_cfg=False, cfg_hybrid=False)
            with open(dec_path, 'w', encoding='utf-8') as f:
                f.write(dec_src)
        except Exception as e:
            results.append((name, 'DECOMPILE_ERROR', str(e)[:80]))
            continue

        # 比较字节码
        orig_co = compile(src, '<orig>', 'exec')
        dec_co = compile(dec_src, '<dec>', 'exec')

        def get_instrs(co):
            for c in co.co_consts:
                if isinstance(c, type(co)) and c.co_name == 'f':
                    return [(i.offset, i.opname, i.argval) for i in dis.get_instructions(c)
                            if i.opname not in ('EXTENDED_ARG', 'CACHE', 'RESUME', 'NOP')]
            return []

        orig_instrs = get_instrs(orig_co)
        dec_instrs = get_instrs(dec_co)

        if orig_instrs == dec_instrs:
            results.append((name, 'PASS', f'{len(orig_instrs)} instrs'))
        else:
            # 找第一个差异
            min_len = min(len(orig_instrs), len(dec_instrs))
            first_diff = -1
            for i in range(min_len):
                if orig_instrs[i] != dec_instrs[i]:
                    first_diff = i
                    break
            if first_diff == -1 and len(orig_instrs) != len(dec_instrs):
                first_diff = min_len
            detail = ''
            if first_diff < min_len:
                o = orig_instrs[first_diff]
                d = dec_instrs[first_diff]
                detail = f'idx={first_diff}: {o[1]} {o[2]} -> {d[1]} {d[2]}'
            else:
                detail = f'len: {len(orig_instrs)} -> {len(dec_instrs)}'
            results.append((name, 'FAIL', detail))

    print(f"=== R27 最小复现实例验证 ({len(results)} 个) ===")
    pass_count = 0
    fail_count = 0
    for name, status, detail in results:
        marker = '✓' if status == 'PASS' else '✗'
        print(f"  {marker} {name:<50} {status:<15} {detail}")
        if status == 'PASS':
            pass_count += 1
        else:
            fail_count += 1
    print(f"\n通过: {pass_count}, 失败: {fail_count}")


if __name__ == '__main__':
    main()
