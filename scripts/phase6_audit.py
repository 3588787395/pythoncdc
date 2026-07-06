#!/usr/bin/env python
"""Phase 6 Audit Data Collection Script"""
import sys
import ast
import re
from collections import Counter

sys.path.insert(0, 'f:/pythoncdc')

def count_hardcoded_opcodes(filepath):
    """统计硬编码操作码引用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 简单匹配常见硬编码操作码模式
    known_opcodes = {
        'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'JUMP_NOT_EXC_MATCH',
        'FOR_ITER', 'GET_ITER', 'GET_ANEXT', 'GET_AITER',
        'LOAD_CONST', 'LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_ATTR',
        'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_ATTR', 'STORE_SUBSCR',
        'COMPARE_OP', 'BINARY_OP', 'BINARY_SUBSCR', 'BINARY_ADD', 'BINARY_MULTIPLY',
        'BEFORE_WITH', 'WITH_EXCEPT_START', 'WITH_EXCEPT_FINISH',
        'PUSH_EXC_INFO', 'RERAISE', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
        'MATCH_CLASS', 'MATCH_MAPPING', 'MATCH_SEQUENCE', 'MATCH_OR',
        'LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT_MERGE', 'UNPACK_SEQUENCE',
        'RETURN_VALUE', 'RAISE_VARARGS', 'RETURN_CONST',
        'BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET', 'BUILD_MAP', 'BUILD_STRING',
        'IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR',
        'DELETE_NAME', 'DELETE_ATTR', 'DELETE_GLOBAL', 'DELETE_SUBSCR',
        'CALL', 'CALL_FUNCTION', 'PRECALL', 'PUSH_NULL',
        'CONTINUE_LOOP', 'BREAK_LOOP',
        'POP_TOP', 'COPY', 'SWAP',
        'NOP', 'UNARY_NOT', 'UNARY_NEGATIVE',
        'GET_ITER', 'FOR_ITER',
        'SETUP_FINALLY', 'SETUP_EXCEPT', 'SETUP_WITH', 'SETUP_ASYNC_WITH',
        'POP_EXCEPT', 'END_ASYNC_FOR',
        'IS_OP', 'CONTAINS_OP',
        'FORMAT_VALUE', 'BUILD_CONST_KEY_MAP',
    }

    opcodes_found = []
    for opcode in known_opcodes:
        count = content.count(f"'{opcode}'") + content.count(f'"{opcode}"')
        if count > 0:
            opcodes_found.extend([opcode] * count)

    return Counter(opcodes_found)

def analyze_method_sizes(filepath):
    """分析方法规模分布"""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)

    methods = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno if hasattr(node, 'end_lineno') else start
            length = end - start + 1
            methods.append({
                'name': node.name,
                'length': length,
                'start': start,
                'type': 'async' if isinstance(node, ast.AsyncFunctionDef) else 'sync'
            })

    return sorted(methods, key=lambda x: -x['length'])

def main():
    files = [
        ('f:/pythoncdc/core/cfg/region_analyzer.py', 'region_analyzer.py'),
        ('f:/pythoncdc/core/cfg/region_ast_generator.py', 'region_ast_generator.py'),
    ]

    print('=' * 80)
    print('PHASE 6 AUDIT DATA COLLECTION')
    print('=' * 80)

    total_methods = 0
    total_lines = 0
    all_hardcoded = Counter()

    for filepath, name in files:
        print(f'\n{"="*60}')
        print(f'FILE: {name}')
        print(f'{"="*60}')

        # Method size analysis
        methods = analyze_method_sizes(filepath)
        total_methods += len(methods)

        lengths = [m['length'] for m in methods]
        total_lines += sum(lengths)

        print(f'\nMethod Size Distribution:')
        print(f'  Total methods: {len(methods)}')
        print(f'  Total lines (methods only): {sum(lengths)}')
        print(f'  Max: {max(lengths)} | Min: {min(lengths)} | Avg: {sum(lengths)/len(lengths):.1f}')

        buckets = {
            '<=30': sum(1 for l in lengths if l <= 30),
            '31-50': sum(1 for l in lengths if 31 <= l <= 50),
            '51-80': sum(1 for l in lengths if 51 <= l <= 80),
            '81-100': sum(1 for l in lengths if 81 <= l <= 100),
            '101-150': sum(1 for l in lengths if 101 <= l <= 150),
            '151-300': sum(1 for l in lengths if 151 <= l <= 300),
            '>300': sum(1 for l in lengths if l > 300),
        }
        print(f'\n  Size buckets:')
        for bucket, count in buckets.items():
            bar = '#' * (count // 2)
            print(f'    {bucket:>8}: {count:>4} {bar}')

        # Top 10 largest methods
        print(f'\n  Top 10 Largest Methods:')
        for i, m in enumerate(methods[:10], 1):
            print(f'    {i:>2}. {m["name"]:<45} {m["length"]:>5} lines (L{m["start"]})')

        # Hardcoded opcodes
        hardcoded = count_hardcoded_opcodes(filepath)
        all_hardcoded += hardcoded

        print(f'\n  Hardcoded Opcode References (Top 20):')
        for opcode, count in hardcoded.most_common(20):
            print(f'    {opcode:<35} {count:>4}')

    # Summary
    print(f'\n{"="*80}')
    print('COMBINED SUMMARY')
    print(f'{"="*80}')
    print(f'Total methods across both files: {total_methods}')
    print(f'Total method lines: {total_lines}')
    print(f'Avg method lines: {total_lines/total_methods:.1f}' if total_methods else 'N/A')
    print(f'\nTotal unique hardcoded opcodes: {len(all_hardcoded)}')
    print(f'Total hardcoded references: {sum(all_hardcoded.values())}')

if __name__ == '__main__':
    main()
