#!/usr/bin/env python3
"""
字节码一致性验证工具 v2
比较原始pyc文件与反编译后重新编译的pyc文件的字节码
v2: 规范化比较 - 忽略文件路径差异、常量池索引差异，只比较指令结构
"""
import dis
import marshal
import sys
import os
import types
from typing import List, Tuple, Dict, Any, Optional


def load_code_from_pyc(pyc_path: str) -> types.CodeType:
    """从pyc文件加载code对象"""
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = int.from_bytes(f.read(4), 'little')
        if flags & 0x1:
            f.read(8)
        else:
            f.read(8)
        code = marshal.load(f)
    return code


def extract_all_code_objects(code: types.CodeType, prefix: str = '') -> Dict[str, types.CodeType]:
    """递归提取所有code对象"""
    result = {}
    if code.co_name == '<module>':
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name if prefix else code.co_name
    result[name] = code
    
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = name if name != '<module>' else ''
            result.update(extract_all_code_objects(const, child_prefix))
    return result


def normalize_instructions(code: types.CodeType) -> List[Tuple[str, str]]:
    """
    规范化指令序列用于比较
    返回 (opname, normalized_argval) 列表
    
    规范化规则：
    - 忽略 RESUME, NOP, CACHE, EXTENDED_ARG
    - code对象的argval只比较类型('code')，不比较具体内容
    - 文件路径差异忽略
    - 常量值比较时，None/True/False/数字/字符串直接比较
    - 跳转目标用相对偏移规范化
    """
    instrs = []
    for instr in dis.get_instructions(code):
        if instr.opname in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG'):
            continue
        
        # 规范化argval
        argval = instr.argval
        
        if isinstance(argval, types.CodeType):
            # code对象只标记为'code'，不比较具体内容
            argval_str = '<code>'
        elif isinstance(argval, str) and argval.startswith('d:\\') or (isinstance(argval, str) and '\\' in argval and '.py' in argval):
            # 文件路径，忽略
            argval_str = '<filepath>'
        else:
            argval_str = str(argval)
        
        instrs.append((instr.opname, argval_str))
    return instrs


def compare_bytecode(orig_code: types.CodeType, decomp_code: types.CodeType) -> Dict[str, Any]:
    """比较两个code对象的字节码"""
    orig_instrs = normalize_instructions(orig_code)
    decomp_instrs = normalize_instructions(decomp_code)
    
    if orig_instrs == decomp_instrs:
        return {'match': True, 'diff': [], 'orig_count': len(orig_instrs), 'decomp_count': len(decomp_instrs)}
    
    diffs = []
    max_len = max(len(orig_instrs), len(decomp_instrs))
    for i in range(max_len):
        orig_i = orig_instrs[i] if i < len(orig_instrs) else None
        decomp_i = decomp_instrs[i] if i < len(decomp_instrs) else None
        if orig_i != decomp_i:
            diffs.append({
                'offset': i,
                'original': orig_i,
                'decompiled': decomp_i
            })
    
    return {'match': False, 'diff': diffs, 'orig_count': len(orig_instrs), 'decomp_count': len(decomp_instrs)}


def compare_pyc_files(orig_pyc: str, decomp_py: str) -> Dict[str, Any]:
    """比较原始pyc文件与反编译后的py文件"""
    orig_code = load_code_from_pyc(orig_pyc)
    orig_codes = extract_all_code_objects(orig_code)
    
    with open(decomp_py, 'r', encoding='utf-8') as f:
        source = f.read()
    
    try:
        decomp_code = compile(source, decomp_py, 'exec')
    except SyntaxError as e:
        return {
            'total_functions': len(orig_codes),
            'matched': 0,
            'mismatches': [{'function': '<module>', 'error': f'SyntaxError: {e}'}],
            'success_rate': 0.0,
            'syntax_error': str(e)
        }
    
    decomp_codes = extract_all_code_objects(decomp_code)
    
    matched = 0
    mismatches = []
    
    for name, orig_co in orig_codes.items():
        decomp_co = decomp_codes.get(name)
        if decomp_co is None:
            mismatches.append({
                'function': name,
                'error': 'Function not found in decompiled code'
            })
            continue
        
        result = compare_bytecode(orig_co, decomp_co)
        if result['match']:
            matched += 1
        else:
            mismatches.append({
                'function': name,
                'diffs': result['diff'][:30],
                'total_diffs': len(result['diff']),
                'orig_count': result['orig_count'],
                'decomp_count': result['decomp_count']
            })
    
    total = len(orig_codes)
    success_rate = (matched / total * 100) if total > 0 else 0.0
    
    return {
        'total_functions': total,
        'matched': matched,
        'mismatches': mismatches,
        'success_rate': success_rate
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_bytecode_v2.py <original.pyc> <decompiled.py>")
        sys.exit(1)
    
    orig_pyc = sys.argv[1]
    decomp_py = sys.argv[2]
    
    result = compare_pyc_files(orig_pyc, decomp_py)
    
    print(f"Total functions: {result['total_functions']}")
    print(f"Matched: {result['matched']}")
    print(f"Success rate: {result['success_rate']:.2f}%")
    print(f"Mismatches: {len(result['mismatches'])}")
    
    if result.get('syntax_error'):
        print(f"\nSyntax Error: {result['syntax_error']}")
    
    if result['mismatches']:
        print("\nMismatch Details:")
        for m in result['mismatches']:
            func = m['function']
            if 'error' in m:
                print(f"  {func}: {m['error']}")
            else:
                print(f"  {func}: {m['total_diffs']} diffs (orig={m.get('orig_count','?')} decomp={m.get('decomp_count','?')})")
                for d in m.get('diffs', [])[:10]:
                    orig = d.get('original')
                    decomp = d.get('decompiled')
                    print(f"    offset {d['offset']}: orig={orig} decomp={decomp}")


if __name__ == '__main__':
    main()
