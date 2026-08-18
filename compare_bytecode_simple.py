#!/usr/bin/env python3
"""
字节码一致性验证工具
比较原始pyc文件与反编译后重新编译的pyc文件的字节码
"""
import dis
import marshal
import sys
import os
import types
import importlib.util
from typing import List, Tuple, Dict, Any, Optional


def load_code_from_pyc(pyc_path: str) -> types.CodeType:
    """从pyc文件加载code对象"""
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = int.from_bytes(f.read(4), 'little')
        # Python 3.7+: timestamp + size, or hash-based
        if flags & 0x1:  # hash-based
            f.read(8)  # source hash
        else:
            f.read(8)  # timestamp + size
        code = marshal.load(f)
    return code


def extract_all_code_objects(code: types.CodeType, prefix: str = '') -> Dict[str, types.CodeType]:
    """递归提取所有code对象（包括嵌套的函数/类）"""
    result = {}
    name = prefix + code.co_name if prefix else code.co_name
    if name == '<module>':
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name if prefix else code.co_name
    result[name] = code
    
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = name if name != '<module>' else ''
            result.update(extract_all_code_objects(const, child_prefix))
    return result


def normalize_instructions(code: types.CodeType) -> List[Tuple[str, int, Any]]:
    """
    规范化指令序列用于比较
    返回 (opname, arg, argval) 列表
    过滤掉行号差异
    """
    instrs = []
    for instr in dis.get_instructions(code):
        # 忽略 RESUME, NOP, CACHE 等噪声指令
        if instr.opname in ('RESUME', 'NOP', 'CACHE'):
            continue
        # 忽略 EXTENDED_ARG
        if instr.opname == 'EXTENDED_ARG':
            continue
        instrs.append((instr.opname, instr.arg if instr.arg is not None else 0, instr.argval))
    return instrs


def compare_bytecode(orig_code: types.CodeType, decomp_code: types.CodeType) -> Dict[str, Any]:
    """比较两个code对象的字节码"""
    orig_instrs = normalize_instructions(orig_code)
    decomp_instrs = normalize_instructions(decomp_code)
    
    if orig_instrs == decomp_instrs:
        return {'match': True, 'diff': []}
    
    # 找出差异
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
    
    return {'match': False, 'diff': diffs}


def compare_pyc_files(orig_pyc: str, decomp_py: str) -> Dict[str, Any]:
    """
    比较原始pyc文件与反编译后的py文件
    
    Returns:
        {
            'total_functions': int,
            'matched': int,
            'mismatches': List[Dict],
            'success_rate': float
        }
    """
    # 加载原始pyc
    orig_code = load_code_from_pyc(orig_pyc)
    orig_codes = extract_all_code_objects(orig_code)
    
    # 编译反编译后的py文件
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
                'diffs': result['diff'][:20],  # 只保留前20个差异
                'total_diffs': len(result['diff'])
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
        print("Usage: python compare_bytecode.py <original.pyc> <decompiled.py>")
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
        for m in result['mismatches'][:20]:
            func = m['function']
            if 'error' in m:
                print(f"  {func}: {m['error']}")
            else:
                print(f"  {func}: {m['total_diffs']} diffs")
                for d in m.get('diffs', [])[:5]:
                    orig = d.get('original')
                    decomp = d.get('decompiled')
                    print(f"    offset {d['offset']}: orig={orig} decomp={decomp}")


if __name__ == '__main__':
    main()
