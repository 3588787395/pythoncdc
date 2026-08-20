#!/usr/bin/env python3
"""Trace validate_data block generation with correct init"""

import sys
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import BlockRole
import marshal, types

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all(code, prefix=""):
    name = prefix + code.co_name if prefix else code.co_name
    result = {name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            new_prefix = name + "." if name != "<module>" else ""
            result.update(extract_all(const, new_prefix))
    return result

orig_code = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
orig_codes = extract_all(orig_code)

# Load module-level code to get validate_data as sub-code
target = "DataProcessor.validate_data"
orig_co = orig_codes[target]

# Build CFG for validate_data
cfg = CFGBuilder().build(orig_co)

# Create generator (it creates its own RegionAnalyzer internally)
gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

ra = gen.region_analyzer
blocks = cfg.get_blocks_in_order()

print("=== Block Roles ===")
for block in blocks:
    role = ra.get_block_role(block)
    if block.start_offset >= 72 and block.start_offset <= 610:
        last_i = block.get_last_instruction()
        last_op = last_i.opname if last_i else 'None'
        last_arg = last_i.argval if last_i else 'None'
        gen_flag = "GEN" if block.start_offset in gen.generated_offsets else "   "
        print(f"  {gen_flag} Block @{block.start_offset:4d}: role={str(role):30s} last={last_op} {last_arg}")

print(f"\n=== Generated Blocks ===")
print(f"Generated offsets: {sorted(gen.generated_offsets)}")
not_gen = [b.start_offset for b in blocks if b.start_offset not in gen.generated_offsets]
print(f"Not generated: {not_gen}")

# Print simplified AST
print(f"\n=== Generated AST ({len(result) if result else 0} nodes) ===")
def simplify(node, depth=0):
    if isinstance(node, dict):
        t = node.get('type', '?')
        indent = '  ' * depth
        if t == 'If':
            test = node.get('test', {})
            test_s = f"({test.get('type', '?')})"
            # Check for Compare
            if test.get('type') == 'Compare':
                ops = test.get('ops', [])
                left = test.get('left', {})
                test_s = f"Compare({left.get('type','?')},{ops})"
            body_count = len(node.get('body', []))
            orelse_count = len(node.get('orelse', []))
            print(f"{indent}If {test_s} body={body_count} orelse={orelse_count}")
            for s in (node.get('body') or []):
                simplify(s, depth+1)
            if node.get('orelse'):
                print(f"{indent}Else:")
                for s in node['orelse']:
                    simplify(s, depth+1)
        elif t == 'For':
            print(f"{indent}For")
            for s in (node.get('body') or []):
                simplify(s, depth+1)
            if node.get('orelse'):
                print(f"{indent}ForElse:")
                for s in node['orelse']:
                    simplify(s, depth+1)
        elif t == 'Try':
            print(f"{indent}Try")
            for s in (node.get('body') or []):
                simplify(s, depth+1)
            for h in (node.get('handlers') or []):
                print(f"{indent}Except:")
                for s in (h.get('body') or []):
                    simplify(s, depth+1)
        elif t in ('Break', 'Continue', 'Pass'):
            print(f"{indent}{t}")
        elif t == 'Return':
            val = node.get('value', {})
            val_s = val.get('type', '?') if val else 'None'
            print(f"{indent}Return({val_s})")
        elif t == 'Expr':
            val = node.get('value', {})
            val_s = val.get('type', '?') if val else '?'
            print(f"{indent}Expr({val_s})")
        elif t == 'Assign':
            print(f"{indent}Assign")
        else:
            print(f"{indent}{t}")

if result:
    for node in result:
        simplify(node)