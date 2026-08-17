#!/usr/bin/env python3
"""R94: 深入分析 get_kline_by_date_one 等函数"""
import sys, dis, marshal, types
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs
import marshal
def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
ok_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedataOK.py"

orig_code = load_pyc(pyc_path)
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok_path, 'exec')

def extract_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

for func_name in ['get_kline_by_date_one', 'get_kline_by_date_new', 'get_kline_by_count']:
    print(f"\n{'='*60}")
    print(f"Function: {func_name}")
    print(f"{'='*60}")
    
    if func_name not in orig_map or func_name not in decomp_map:
        print("  MISSING in one side!")
        continue
    
    orig_co = orig_map[func_name]
    decomp_co = decomp_map[func_name]
    
    result = compare_bytecode(orig_co, decomp_co)
    true_diffs = result.get('true_diffs', [])
    jump_diffs = result.get('jump_diffs', [])
    
    print(f"orig_count={result['orig_count']}, decomp_count={result['decomp_count']}")
    print(f"true_diffs={len(true_diffs)}, jump_diffs={len(jump_diffs)}")
    
    fd = true_diffs[0] if true_diffs else {}
    fd_idx = fd.get('index', 0)
    
    print(f"\nFirst 10 true_diffs:")
    for td in true_diffs[:10]:
        print(f"  idx={td['index']}: {td.get('orig_op','?')}({td.get('orig_arg','?')}) -> {td.get('decomp_op','?')}({td.get('decomp_arg','?')})")
    
    orig_instrs = _filter_noise_instrs(get_bytecode_instructions(orig_co))
    decomp_instrs = _filter_noise_instrs(get_bytecode_instructions(decomp_co))
    
    print(f"\nOriginal instructions around idx {fd_idx}:")
    start = max(0, fd_idx - 5)
    end = min(len(orig_instrs), fd_idx + 15)
    for i in range(start, end):
        instr = orig_instrs[i]
        marker = ">>>" if i == fd_idx else "   "
        argval = instr.argval
        if isinstance(argval, str) and len(argval) > 40:
            argval = argval[:40] + '...'
        print(f"  {marker} [{i}] {instr.opname}({argval})")
    
    print(f"\nDecompiled instructions around idx {fd_idx}:")
    start = max(0, fd_idx - 5)
    end = min(len(decomp_instrs), fd_idx + 15)
    for i in range(start, end):
        instr = decomp_instrs[i]
        marker = ">>>" if i == fd_idx else "   "
        argval = instr.argval
        if isinstance(argval, str) and len(argval) > 40:
            argval = argval[:40] + '...'
        print(f"  {marker} [{i}] {instr.opname}({argval})")
