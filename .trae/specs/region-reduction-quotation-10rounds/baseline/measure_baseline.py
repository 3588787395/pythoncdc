"""基线测量：反编译 quotation.pyc（区域归约路径）+ 字节码一致性统计。

输出：
- /tmp/rr_baseline_decompiled.py  反编译产物（只读，禁止修改）
- baseline/region_baseline.txt     一致函数数 / 总函数数 / 成功率
- baseline/baseline_diff.json      按函数 diff 详情
"""
import sys
import time
import json
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
OUT = '/tmp/rr_baseline_decompiled.py'
SPEC_DIR = '/workspace/.trae/specs/region-reduction-quotation-10rounds/baseline'

from pycdc import decompile_pyc

# 1. 反编译
t0 = time.time()
src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
elapsed = time.time() - t0
print(f"[decompile] elapsed={elapsed:.2f}s, len={len(src)}")

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(src)
print(f"[decompile] wrote {OUT}")

# 2. 加载原始 code objects
from core.pyc_loader_v2 import load_pyc_file_v2
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

orig_cos = {}
def walk_orig(co, prefix=''):
    name = prefix + co.co_name if prefix else co.co_name
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    orig_cos[name] = co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            walk_orig(const, sub_prefix)
walk_orig(code_obj)

# 3. 编译反编译产物
try:
    new_code = compile(src, '<decompiled>', 'exec')
    compile_ok = True
    compile_err = ''
except SyntaxError as e:
    compile_ok = False
    compile_err = f"{type(e).__name__}: {e}"
    print(f"[compile] FAILED: {compile_err}")
    new_code = None

new_cos = {}
if new_code is not None:
    def walk_new(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        new_cos[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk_new(const, sub_prefix)
    walk_new(new_code)

# 4. 比较字节码
def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs

def instr_equal(a, b):
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        return all(instr_equal(x, y) for x, y in zip(ia, ib))
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b

results = {}
matched = 0
missing = 0
mismatched = 0
for name, orig_co in orig_cos.items():
    if name in new_cos:
        oa = get_instr_list(orig_co)
        na = get_instr_list(new_cos[name])
        if len(oa) != len(na):
            results[name] = {'status': 'len_diff', 'orig_len': len(oa), 'new_len': len(na)}
            mismatched += 1
        else:
            ok = all(instr_equal(x, y) for x, y in zip(oa, na))
            if ok:
                results[name] = {'status': 'match'}
                matched += 1
            else:
                # find first diff
                first_diff = -1
                for i, (x, y) in enumerate(zip(oa, na)):
                    if not instr_equal(x, y):
                        first_diff = i
                        break
                results[name] = {'status': 'instr_diff', 'orig_len': len(oa), 'first_diff': first_diff,
                                 'orig_at': oa[first_diff] if first_diff >= 0 else None,
                                 'new_at': na[first_diff] if first_diff >= 0 else None}
                mismatched += 1
    else:
        results[name] = {'status': 'missing'}
        missing += 1

total = len(orig_cos)
success_rate = matched / total * 100 if total else 0

with open(f'{SPEC_DIR}/region_baseline.txt', 'w', encoding='utf-8') as f:
    f.write(f"=== 区域归约路径反编译基线 ===\n")
    f.write(f"pyc: {PYC}\n")
    f.write(f"decompile_elapsed_s: {elapsed:.2f}\n")
    f.write(f"compile_ok: {compile_ok}\n")
    if not compile_ok:
        f.write(f"compile_error: {compile_err}\n")
    f.write(f"total_functions: {total}\n")
    f.write(f"matched_functions: {matched}\n")
    f.write(f"mismatched_functions: {mismatched}\n")
    f.write(f"missing_functions: {missing}\n")
    f.write(f"success_rate_pct: {success_rate:.2f}\n")

with open(f'{SPEC_DIR}/baseline_diff.json', 'w', encoding='utf-8') as f:
    json.dump({'total': total, 'matched': matched, 'mismatched': mismatched, 'missing': missing,
               'success_rate_pct': success_rate, 'compile_ok': compile_ok,
               'results': results}, f, indent=2, default=str)

print(f"[baseline] total={total} matched={matched} mismatched={mismatched} missing={missing} success_rate={success_rate:.2f}% compile_ok={compile_ok}")
print(f"[baseline] wrote {SPEC_DIR}/region_baseline.txt")
