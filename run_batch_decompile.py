#!/usr/bin/env python3
"""
quotation.pyc 批量反编译与字节码比对脚本
1) 对整个 quotation.pyc 做一次性反编译
2) 编译反编译结果
3) 对每个函数逐一比对原始/反编译字节码
4) Top 15 失败函数输出详细信息
"""

import os
import sys
import marshal
import types
import dis
import re
import io
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# 同时输出到文件和终端
OUTPUT_PATH = os.path.join(HERE, 'batch_output.txt')

class Tee:
    def __init__(self, file_path):
        self.file = open(file_path, 'w', encoding='utf-8')
        self.stdout = sys.stdout
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()
        self.stdout.flush()
    def close(self):
        self.file.close()

sys.stdout = Tee(OUTPUT_PATH)

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions

PYC_PATH = os.path.join(HERE, 'quotation.pyc')

# ──── 工具函数 ────

def extract_code_objects(code_obj, prefix=''):
    results = []
    name = prefix + code_obj.co_name if prefix else code_obj.co_name
    if name == '<module>':
        name = '<module>'
    results.append((name, code_obj))
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            results.extend(extract_code_objects(const, sub_prefix))
    return results


def fix_syntax_errors(source):
    fixed = source
    changed = True
    iterations = 0
    while changed and iterations < 50:
        changed = False
        iterations += 1
        try:
            compile(fixed, '<decompiled>', 'exec')
            break
        except SyntaxError as e:
            lineno = e.lineno
            msg = str(e)
            if lineno is None:
                break
            lines = fixed.split('\n')
            if lineno < 1 or lineno > len(lines):
                break
            idx = lineno - 1
            prev_line = lines[idx - 1] if idx > 0 else ''
            prev_stripped = prev_line.rstrip()
            indent_match = re.match(r'^(\s*)', prev_stripped)
            base_indent = indent_match.group(1) if indent_match else ''

            if 'expected an indented block' in msg:
                if prev_stripped.endswith(':'):
                    insert_indent = base_indent + '    '
                    lines.insert(idx, insert_indent + 'pass')
                    fixed = '\n'.join(lines)
                    changed = True
                else:
                    break
            elif 'unexpected indent' in msg:
                break
            elif "expected ':'" in msg:
                break
            else:
                break
    return fixed


def extract_function_source_marker(full_source, func_name):
    """从完整反编译源码中提取单个函数的源码（用缩进边界找）"""
    lines = full_source.split('\n')
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('def ' + func_name + '('):
            start = i
            break
    if start is None:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def ') and func_name in stripped:
                start = i
                break
    if start is None:
        return None

    base_indent = len(lines[start]) - len(lines[start].lstrip())
    func_lines = [lines[start]]
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == '':
            func_lines.append(lines[j])
            continue
        indent = len(lines[j]) - len(lines[j].lstrip())
        if lines[j].strip().startswith('@'):
            continue
        if indent <= base_indent and lines[j].strip() != '':
            break
        func_lines.append(lines[j])
    return '\n'.join(func_lines)


# ──── 主流程 ────

print('=' * 100)
print('  quotation.pyc 批量反编译 & 字节码比对')
print('=' * 100)
print(f'  PYC: {PYC_PATH}')

# 步骤 1: 加载原始 pyc，提取 code objects
print()
print('>>> 步骤 1: 加载原始 pyc，提取 code objects')
with open(PYC_PATH, 'rb') as f:
    header = f.read(16)
    top_co = marshal.load(f)

orig_codes = extract_code_objects(top_co)
print(f'    原始 code objects: {len(orig_codes)} 个')
func_codes = [(n, c) for n, c in orig_codes if n != '<module>']
print(f'    非 <module>: {len(func_codes)} 个函数/类/推导式')

# 步骤 2: 一次性反编译整个 pyc
print()
print('>>> 步骤 2: 反编译整个 quotation.pyc')
decompiled_src = decompile_pyc(PYC_PATH)
print(f'    反编译完成，{len(decompiled_src)} 字符')

lines = decompiled_src.split('\n')
clean_lines = [l for l in lines if not l.startswith('# Source') and not l.startswith('# File:')]
clean_src = '\n'.join(clean_lines)

# 步骤 3: 编译反编译结果
print()
print('>>> 步骤 3: 编译反编译源码')
try:
    decomp_code = compile(clean_src, '<decompiled>', 'exec')
    print('    编译成功')
except SyntaxError as e:
    print(f'    编译失败 (SyntaxError): {e}')
    print('    尝试语法修复...')
    clean_src = fix_syntax_errors(clean_src)
    try:
        decomp_code = compile(clean_src, '<decompiled>', 'exec')
        print('    修复后编译成功')
    except SyntaxError as e2:
        print(f'    修复后仍然失败: {e2}')
        sys.exit(1)

decomp_codes = extract_code_objects(decomp_code)
print(f'    反编译后 code objects: {len(decomp_codes)} 个')

# 构建名字 → code 的映射
decomp_name_map = {}
for name, co in decomp_codes:
    decomp_name_map[name] = co

# 步骤 4: 逐函数比对
print()
print('>>> 步骤 4: 逐函数比对字节码')

results = []
match_count = 0
mismatch_count = 0

for idx, (orig_name, orig_co) in enumerate(func_codes):
    print(f'    [{idx+1}/{len(func_codes)}] {orig_name} ', end='')
    
    # 在反编译结果中查找对应 code
    decomp_co = decomp_name_map.get(orig_name)
    if decomp_co is None:
        # 尝试模糊匹配
        for dname, dco in decomp_codes:
            if dname.endswith('.' + orig_co.co_name) or dname == orig_co.co_name:
                decomp_co = dco
                break
    
    if decomp_co is None:
        results.append({
            'name': orig_name,
            'orig_count': len(get_bytecode_instructions(orig_co)),
            'decomp_count': 0, 'diff': len(get_bytecode_instructions(orig_co)),
            'status': 'MISSING',
            'source': None, 'orig_instrs': get_bytecode_instructions(orig_co),
            'decomp_instrs': [], 'cmp': {}
        })
        print('MISSING')
        continue
    
    try:
        cmp_result = compare_bytecode(orig_co, decomp_co)
        orig_count = cmp_result['orig_count']
        decomp_count = cmp_result['decomp_count']
        diff = abs(orig_count - decomp_count) + len(cmp_result.get('true_diffs', []))
        
        if cmp_result['match']:
            status = 'MATCH'
            match_count += 1
        elif cmp_result.get('jump_only'):
            status = 'JUMP_ONLY'
            mismatch_count += 1
        else:
            status = 'MISMATCH'
            mismatch_count += 1
        
        results.append({
            'name': orig_name,
            'orig_count': orig_count,
            'decomp_count': decomp_count,
            'diff': diff,
            'true_diff_count': len(cmp_result.get('true_diffs', [])),
            'jump_diff_count': len(cmp_result.get('jump_diffs', [])),
            'status': status,
            'source': extract_function_source_marker(clean_src, orig_co.co_name),
            'orig_instrs': get_bytecode_instructions(orig_co),
            'decomp_instrs': get_bytecode_instructions(decomp_co),
            'cmp': cmp_result,
        })
        print(status, f'(diff={diff})')
    except Exception as e:
        results.append({
            'name': orig_name,
            'orig_count': len(get_bytecode_instructions(orig_co)),
            'decomp_count': 0, 'diff': len(get_bytecode_instructions(orig_co)),
            'status': 'ERROR',
            'source': None, 'orig_instrs': get_bytecode_instructions(orig_co),
            'decomp_instrs': [], 'cmp': {}
        })
        print(f'ERROR: {e}')

# 步骤 5: 排序，取 Top 15 失败函数
total = len(func_codes)
failing = sorted(
    [r for r in results if r['status'] not in ('MATCH',)],
    key=lambda r: r['diff'],
    reverse=True
)[:15]

# 确保用户关注的函数也包含在内
PINNED = ['check_stock', 'date_convert', 'get_quote', 'change_his_to_forward',
          'change_his_to_backward', 'build_future_fill_time', 
          'build_current_period_df', 'get_real', 'get_index_stocks']
pinned_map = {r['name']: r for r in results if r['name'] in PINNED}

# 去重，top15在前
all_detailed = failing[:]
for fn in PINNED:
    if fn in pinned_map and pinned_map[fn] not in all_detailed:
        all_detailed.append(pinned_map[fn])

print()
print('=' * 100)
print(f'  汇总: {match_count}/{total} 匹配 ({match_count*100//total if total else 0}%), '
      f'{mismatch_count} 不匹配')
print(f'  以下是 Top {len(all_detailed)} 差异最大的函数 + 用户关注函数')
print('=' * 100)

# 步骤 6: 逐个详细输出
for rank, entry in enumerate(all_detailed, 1):
    name = entry['name']
    status = entry['status']
    orig_instrs = entry['orig_instrs']
    decomp_instrs = entry.get('decomp_instrs', [])
    
    print()
    print('#' * 100)
    print(f'  #{rank}: {name}  [status={status}]')
    print(f'  原始指令数: {entry["orig_count"]}  |  反编译指令数: {entry["decomp_count"]}  '
          f'|  真差: {entry.get("true_diff_count", "?")}  |  跳转差: {entry.get("jump_diff_count", "?")}')
    print('#' * 100)
    
    # 6a. 反编译源码
    source = entry.get('source')
    if source:
        source_lines = source.split('\n')
        print()
        print('── 反编译源码 ──')
        print()
        for line in source_lines[:40]:
            print(f'    {line}')
        if len(source_lines) > 40:
            print(f'    ... (共 {len(source_lines)} 行)')
    
    # 6b. 原始字节码
    print()
    print('── 原始字节码 (dis) ──')
    for inst in orig_instrs[:30]:
        arg_str = repr(inst.argval) if inst.argval is not None else ''
        print(f'  {inst.offset:6d}: {inst.opname:<30s} {arg_str}')
    if len(orig_instrs) > 30:
        print(f'  ... (共 {len(orig_instrs)} 条指令)')
    
    # 6c. 反编译字节码
    if decomp_instrs:
        print()
        print('── 反编译字节码 (dis) ──')
        for inst in decomp_instrs[:30]:
            arg_str = repr(inst.argval) if inst.argval is not None else ''
            print(f'  {inst.offset:6d}: {inst.opname:<30s} {arg_str}')
        if len(decomp_instrs) > 30:
            print(f'  ... (共 {len(decomp_instrs)} 条指令)')
    
    # 6d. 并排差异
    cmp_result = entry.get('cmp', {})
    true_diffs = cmp_result.get('true_diffs', [])
    jump_diffs = cmp_result.get('jump_diffs', [])
    
    if true_diffs:
        print()
        print(f'── 真实差异 (共 {len(true_diffs)} 条) ──')
        for diff in true_diffs[:25]:
            dtype = diff.get('type', 'diff')
            ix = diff.get('index', '?')
            if dtype == 'extra_in_decomp':
                print(f'  [{ix:>3}] + (反编译多出) {diff["decomp_op"]:30s} arg={diff["decomp_arg"]}')
            elif dtype == 'missing_in_decomp':
                print(f'  [{ix:>3}] - (反编译缺失) {diff["orig_op"]:30s} arg={diff["orig_arg"]}')
            else:
                print(f'  [{ix:>3}]   {diff["orig_op"]:30s} arg={diff["orig_arg"]}  -->  {diff["decomp_op"]:30s} arg={diff["decomp_arg"]}')
        if len(true_diffs) > 25:
            print(f'  ... (共 {len(true_diffs)} 条)')
    
    if jump_diffs:
        print()
        print(f'── 跳转差异 (共 {len(jump_diffs)} 条) ──')
        for diff in jump_diffs[:10]:
            print(f'  [{diff["index"]:>3}]   {diff["orig_op"]:30s} arg={diff["orig_arg"]}  -->  {diff["decomp_op"]:30s} arg={diff["decomp_arg"]}')
        if len(jump_diffs) > 10:
            print(f'  ... (共 {len(jump_diffs)} 条)')

# ──── 终末汇总 ────
print()
print('=' * 100)
print('  完整排名 (Top 30 不匹配)')
print('=' * 100)
all_fail = sorted(
    [r for r in results if r['status'] != 'MATCH'],
    key=lambda r: r['diff'], reverse=True
)
for i, r in enumerate(all_fail[:30], 1):
    print(f'  {i:>2}. {r["name"]:<48s} {r["status"]:<12s} '
          f'orig={r["orig_count"]:>4d}  decomp={r["decomp_count"]:>4d}  '
          f'diff={r["diff"]:>4d}  true={r.get("true_diff_count","?"):>4}')

print()
print(f'总函数数 = {total},  完全匹配 = {match_count},  不匹配/缺失 = {mismatch_count}')
print('Done.')
sys.stdout.close()
