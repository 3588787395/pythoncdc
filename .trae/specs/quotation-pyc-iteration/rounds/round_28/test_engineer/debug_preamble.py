"""R28 测试工程师：验证前导代码对AND链检测的影响"""
import os
import sys
import dis
import py_compile

sys.path.insert(0, '/workspace')

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_28/test_engineer/minimal_repros'

# 带前导代码的AND链（模拟share_change结构）
CASES = {
    'repro_r28_13_with_preamble': '''def f(security, start_year, end_year, params):
    x = eval(security)
    if start_year is not None and end_year is None:
        params['start_year'] = start_year
    elif start_year is None and end_year is not None:
        params['end_year'] = end_year
    elif start_year is not None and end_year is not None:
        params['start_year'] = start_year
        params['end_year'] = end_year
''',
    'repro_r28_14_with_more_preamble': '''def f(security, start_year, end_year, params):
    return_data = {}
    return_data['data'] = []
    url = '%s/info' % 'x'
    params = {'page_no': '1'}
    security = eval(security)
    if start_year is not None and end_year is None:
        params['start_year'] = start_year
    elif start_year is None and end_year is not None:
        params['end_year'] = end_year
    elif start_year is not None and end_year is not None:
        params['start_year'] = start_year
        params['end_year'] = end_year
''',
    'repro_r28_15_preamble_single_and': '''def f(security, a, b):
    x = eval(security)
    if a is not None and b is None:
        return 1
    return 0
''',
}

for name, src in CASES.items():
    src_path = os.path.join(OUT_DIR, name + '.py')
    pyc_path = os.path.join(OUT_DIR, name + '.pyc')
    with open(src_path, 'w') as f:
        f.write(src)
    py_compile.compile(src_path, pyc_path, doraise=True)
    print(f"[created] {name}")

# 反编译并验证
from pycdc import decompile_pyc

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
        if x[1] != y[1] or x[2] != y[2]:
            return False
    return True

for name in CASES:
    pyc_path = os.path.join(OUT_DIR, name + '.pyc')
    src_path = os.path.join(OUT_DIR, name + '.py')

    decompiled = decompile_pyc(pyc_path)
    decompiled_path = os.path.join(OUT_DIR, name + '_decompiled.py')
    with open(decompiled_path, 'w') as f:
        f.write(decompiled)

    with open(src_path) as f:
        orig_src = f.read()
    orig_co = compile(orig_src, '<orig>', 'exec')
    decomp_co = compile(decompiled, '<decomp>', 'exec')

    orig_f = None
    decomp_f = None
    for const in orig_co.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'f':
            orig_f = const
    for const in decomp_co.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'f':
            decomp_f = const

    orig_instrs = get_instr_list(orig_f)
    decomp_instrs = get_instr_list(decomp_f)

    if instrs_equal(orig_instrs, decomp_instrs):
        print(f"[PASS] {name}: 字节码一致 ({len(orig_instrs)}条)")
    else:
        print(f"[FAIL] {name}: 字节码不一致 (orig={len(orig_instrs)}, decomp={len(decomp_instrs)})")
        min_len = min(len(orig_instrs), len(decomp_instrs))
        diffs = 0
        for i in range(min_len):
            if orig_instrs[i][1] != decomp_instrs[i][1] or orig_instrs[i][2] != decomp_instrs[i][2]:
                print(f"  idx={i}: orig={orig_instrs[i][1]} {orig_instrs[i][2]} | decomp={decomp_instrs[i][1]} {decomp_instrs[i][2]}")
                diffs += 1
                if diffs >= 5:
                    break
        print(f"  --- decompiled ---")
        print(decompiled)
