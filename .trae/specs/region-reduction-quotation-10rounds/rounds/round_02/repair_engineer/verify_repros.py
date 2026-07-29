"""R2 修复工程师：repro 回归 + quotation.pyc 整体回归。

用法：
    python verify_repros.py                  # 仅验证 13 个有效 repro
    python verify_repros.py --quotation      # 仅 quotation.pyc 整体回归
    python verify_repros.py --all            # 两者都做

输出每个 repro 的 matched/total + 缺陷函数状态，最后汇总。
"""
import sys
import os
import json
import types
import dis
import py_compile
import tempfile

sys.path.insert(0, '/workspace')

REPRO_DIR = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_02/test_engineer/minimal_repros'
PYC = '/workspace/quotation.pyc'

# 13 个复现缺陷的 repro
EFFECTIVE_REPROS = [
    'repro_01_for_loc_subscr_assign_lost.py',
    'repro_02_for_post_loop_panel_construct.py',
    'repro_03_for_iter_target_early.py',
    'repro_05_for_method_chain_append.py',
    'repro_06_ternary_merged_with_call.py',
    'repro_08_ternary_and_short_circuit.py',
    'repro_09_nested_for_listcomp_jump_target.py',
    'repro_15_long_or_chain_body_pass.py',
    'repro_16_nested_for_dict_subscr_post_loop.py',
    'repro_17_ternary_in_dict_method_chain.py',
    'repro_19_for_while_loc_subscr_append.py',
    'repro_20_ternary_in_return_and_or.py',
    'repro_21_for_continue_dict_subscr_assign.py',
]

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')


def get_instr_list(co):
    return [(i.offset, i.opname, i.argval) for i in dis.get_instructions(co)
            if i.opname not in SKIP_OPS]


def instr_equal(a, b):
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia, ib = get_instr_list(av_a), get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        return all(instr_equal(x, y) for x, y in zip(ia, ib))
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub = '' if name == '<module>' else name + '.'
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk_code(c, sub, sink)
    return sink


def compare_codes(orig_code, new_code):
    """返回 (total, matched, details)。"""
    orig_cos = walk_code(orig_code)
    new_cos = walk_code(new_code)
    matched = 0
    total = len(orig_cos)
    details = []
    for name, oc in orig_cos.items():
        if name not in new_cos:
            details.append((name, 'missing', None))
            continue
        oa, na = get_instr_list(oc), get_instr_list(new_cos[name])
        if len(oa) != len(na):
            details.append((name, 'len_diff', f'orig={len(oa)} new={len(na)}'))
            continue
        fd = -1
        for i, (x, y) in enumerate(zip(oa, na)):
            if not instr_equal(x, y):
                fd = i
                break
        if fd < 0:
            matched += 1
            details.append((name, 'match', None))
        else:
            details.append((name, 'instr_diff', f'idx={fd} orig={oa[fd]} new={na[fd]}'))
    return total, matched, details


def verify_repro(repro_py):
    """返回 dict：file, total, matched, details, src。"""
    with open(repro_py, 'r', encoding='utf-8') as f:
        orig_src = f.read()
    with tempfile.TemporaryDirectory() as d:
        pyc = os.path.join(d, 'repro.pyc')
        py_compile.compile(repro_py, pyc, doraise=True)
        from pycdc import decompile_pyc
        src = decompile_pyc(pyc, use_cfg=False, cfg_hybrid=False)
        try:
            new_code = compile(src, '<decompiled>', 'exec')
        except SyntaxError as e:
            return {'file': os.path.basename(repro_py), 'compile_ok': False,
                    'err': str(e), 'total': 0, 'matched': 0, 'details': []}
        orig_code = compile(orig_src, repro_py, 'exec')
        total, matched, details = compare_codes(orig_code, new_code)
        return {'file': os.path.basename(repro_py), 'compile_ok': True,
                'total': total, 'matched': matched, 'details': details, 'src': src}


def verify_quotation():
    """反编译 quotation.pyc，与原始 code objects 比较，返回 (total, matched, mism_list)。"""
    from pycdc import decompile_pyc
    from core.pyc_loader_v2 import load_pyc_file_v2
    src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
    try:
        new_code = compile(src, '<quotation_decompiled>', 'exec')
    except SyntaxError as e:
        print(f"[quotation] compile FAILED: {e}")
        return 0, 0, []
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    total, matched, details = compare_codes(code_obj, new_code)
    mism = [(n, s, e) for (n, s, e) in details if s != 'match']
    return total, matched, mism


def main():
    args = set(sys.argv[1:])
    do_repros = '--all' in args or '--repros' in args or not args
    do_quotation = '--all' in args or '--quotation' in args

    if do_repros:
        print('=' * 70)
        print('repro 回归（13 个有效 repro）')
        print('=' * 70)
        pass_count = 0
        for fn in EFFECTIVE_REPROS:
            path = os.path.join(REPRO_DIR, fn)
            if not os.path.exists(path):
                print(f"[MISSING] {fn}")
                continue
            r = verify_repro(path)
            if not r['compile_ok']:
                print(f"[COMPILE_FAIL] {fn}: {r.get('err')}")
                continue
            tag = 'PASS' if r['matched'] == r['total'] else 'FAIL'
            if tag == 'PASS':
                pass_count += 1
            print(f"[{tag}] {fn}: matched={r['matched']}/{r['total']}")
            for name, status, extra in r['details']:
                if status != 'match':
                    print(f"    [{status}] {name}: {extra}")
        print(f"\n[repro summary] {pass_count}/{len(EFFECTIVE_REPROS)} fully matched")

    if do_quotation:
        print()
        print('=' * 70)
        print('quotation.pyc 整体回归')
        print('=' * 70)
        total, matched, mism = verify_quotation()
        print(f"[quotation] total={total} matched={matched} mismatched={len(mism)}")
        print(f"[quotation] success_rate={matched/total*100:.2f}% (baseline=141/150=94.00%)")
        print(f"[quotation] mismatched functions ({len(mism)}):")
        for n, s, e in mism:
            print(f"  - {n}: {s} {e or ''}")


if __name__ == '__main__':
    main()
