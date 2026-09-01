"""R28 测试工程师：验证复现实例的反编译字节码一致性"""
import os
import sys
import dis
import importlib.util

sys.path.insert(0, '/workspace')

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_28/test_engineer/minimal_repros'


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE', 'RESUME'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instrs_equal(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x[1] != y[1]:
            return False
        if x[2] != y[2]:
            return False
    return True


def decompile_pyc(pyc_path):
    from pycdc import decompile_pyc
    return decompile_pyc(pyc_path, use_cfg=False, cfg_hybrid=False)


CASES = [
    'repro_r28_01_and_is_not_none_and_is_none',
    'repro_r28_02_and_none_chain_two_branches',
    'repro_r28_03_and_none_with_return',
    'repro_r28_04_and_none_three_branches',
    'repro_r28_05_and_mixed_false_none',
    'repro_r28_06_and_mixed_none_false',
    'repro_r28_07_and_none_in_if',
    'repro_r28_08_and_none_elif_only',
    'repro_r28_09_and_none_with_continue',
    'repro_r28_10_or_none_chain',
    'repro_r28_11_or_not_none_chain',
    'repro_r28_12_and_none_nested_in_while',
    'repro_r28_13_nested_if_else_none',
    'repro_r28_14_nested_if_else_not_none',
    'repro_r28_15_nested_if_none_else_not_none',
    'repro_r28_16_nested_if_with_elif',
]

passed = 0
failed = 0
for name in CASES:
    pyc_path = os.path.join(OUT_DIR, name + '.pyc')
    src_path = os.path.join(OUT_DIR, name + '.py')

    try:
        decompiled = decompile_pyc(pyc_path)
        decompiled_path = os.path.join(OUT_DIR, name + '_decompiled.py')
        with open(decompiled_path, 'w') as f:
            f.write(decompiled)

        # 编译原始源码和反编译源码，比较字节码
        with open(src_path) as f:
            orig_src = f.read()
        orig_co = compile(orig_src, '<orig>', 'exec')
        decomp_co = compile(decompiled, '<decomp>', 'exec')

        # 获取f函数的code object
        orig_f = None
        decomp_f = None
        for const in orig_co.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'f':
                orig_f = const
        for const in decomp_co.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'f':
                decomp_f = const

        if orig_f is None or decomp_f is None:
            print(f"[FAIL] {name}: 无法找到f函数")
            failed += 1
            continue

        orig_instrs = get_instr_list(orig_f)
        decomp_instrs = get_instr_list(decomp_f)

        if instrs_equal(orig_instrs, decomp_instrs):
            print(f"[PASS] {name}: 字节码一致 ({len(orig_instrs)}条)")
            passed += 1
        else:
            print(f"[FAIL] {name}: 字节码不一致 (orig={len(orig_instrs)}, decomp={len(decomp_instrs)})")
            # 显示前几个差异
            min_len = min(len(orig_instrs), len(decomp_instrs))
            diffs = 0
            for i in range(min_len):
                if orig_instrs[i][1] != decomp_instrs[i][1] or orig_instrs[i][2] != decomp_instrs[i][2]:
                    print(f"  idx={i}: orig={orig_instrs[i][1]} {orig_instrs[i][2]} | decomp={decomp_instrs[i][1]} {decomp_instrs[i][2]}")
                    diffs += 1
                    if diffs >= 3:
                        break
            failed += 1
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        failed += 1

print(f"\n总计: PASS={passed}, FAIL={failed}")
