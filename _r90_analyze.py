#!/usr/bin/env python3
"""R90 测试工程师：深入分析 klinedata.pyc 的字节码差异"""

import sys
import os
import dis
import marshal
import types

sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')

from testqouter.round1.base import compare_bytecode, _filter_noise_instrs, _normalize_argval

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
ok_py = "site-packages/IQCommon/api/klinedataOK.py"

# 加载原始 pyc
with open(target_pyc, 'rb') as f:
    f.read(16)  # skip header
    orig_code = marshal.loads(f.read())

# 编译 OK.py
with open(ok_py, 'r', encoding='utf-8') as f:
    ok_source = f.read()
ok_code = compile(ok_source, ok_py, 'exec')

# 提取函数
def extract_functions(code):
    funcs = {}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            funcs[const.co_name] = const
            for inner in const.co_consts:
                if isinstance(inner, types.CodeType):
                    funcs[inner.co_name] = inner
    return funcs

orig_funcs = extract_functions(orig_code)
ok_funcs = extract_functions(ok_code)

# 逐函数比较
mismatched = []
matched_count = 0
total_count = 0

all_func_names = set(orig_funcs.keys()) | set(ok_funcs.keys())
for name in sorted(all_func_names):
    if name in orig_funcs and name in ok_funcs:
        total_count += 1
        result = compare_bytecode(orig_funcs[name], ok_funcs[name])
        if result['match'] or (not result['true_diffs'] and result.get('jump_only')):
            matched_count += 1
        else:
            true_diffs = len(result['true_diffs'])
            jump_diffs = len(result['jump_diffs'])
            first_diff = result['true_diffs'][0] if result['true_diffs'] else (result['jump_diffs'][0] if result['jump_diffs'] else {})
            mismatched.append((name, true_diffs, jump_diffs, first_diff))
    elif name in orig_funcs:
        total_count += 1
        mismatched.append((name, -1, 0, {'type': 'missing_in_decomp'}))
    elif name in ok_funcs:
        mismatched.append((name, -2, 0, {'type': 'extra_in_decomp'}))

print(f"匹配: {matched_count}/{total_count} = {matched_count/total_count*100:.2f}%")
print(f"不匹配: {len(mismatched)}")
print()

mismatched.sort(key=lambda x: -(x[1] if x[1] > 0 else 999))

print("不匹配函数 (前10个):")
for name, td, jd, fd in mismatched[:10]:
    if td == -1:
        print(f"  MISSING - {name}")
    elif td == -2:
        print(f"  EXTRA   - {name}")
    else:
        print(f"  {td:4d} true_diffs, {jd:3d} jump_diffs - {name}")
        if fd:
            print(f"         first: idx={fd.get('index','?')} orig={fd.get('orig_op','?')}({fd.get('orig_arg','?')}) decomp={fd.get('decomp_op','?')}({fd.get('decomp_arg','?')})")

# 深入分析第一个不匹配函数
if mismatched:
    target_name = mismatched[0][0]
    print(f"\n=== 深入分析: {target_name} ===")
    
    if target_name in orig_funcs and target_name in ok_funcs:
        orig_instrs = _filter_noise_instrs(list(dis.get_instructions(orig_funcs[target_name])))
        ok_instrs = _filter_noise_instrs(list(dis.get_instructions(ok_funcs[target_name])))
        
        print(f"\n原始字节码 ({len(orig_instrs)} 条):")
        for i, instr in enumerate(orig_instrs[:40]):
            print(f"  {i:3d} {instr.offset:4d} {instr.opname:25s} {instr.argrepr}")
        
        print(f"\n反编译字节码 ({len(ok_instrs)} 条):")
        for i, instr in enumerate(ok_instrs[:40]):
            print(f"  {i:3d} {instr.offset:4d} {instr.opname:25s} {instr.argrepr}")