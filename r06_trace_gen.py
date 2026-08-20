#!/usr/bin/env python3
"""Trace which blocks are generated for validate_data"""

import sys
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator
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

target = "DataProcessor.validate_data"
orig_co = orig_codes[target]

cfg = CFGBuilder().build(orig_co)
ra = RegionAnalyzer(cfg)
ra.analyze()

blocks = cfg.get_blocks_in_order()

# Show all block roles
print("=== Block Roles ===")
for block in blocks:
    role = ra.get_block_role(block)
    if block.start_offset >= 72 and block.start_offset <= 610:
        last_i = block.get_last_instruction()
        last_op = last_i.opname if last_i else 'None'
        last_arg = last_i.argval if last_i else 'None'
        print(f"  Block @{block.start_offset:4d}: role={role}, last={last_op} {last_arg}")

# Generate AST and check which blocks were generated
gen = RegionASTGenerator(cfg, ra, orig_co)
result = gen.generate()

print("\n=== Generated Blocks ===")
generated_offsets = sorted(gen.generated_offsets)
print(f"Generated offsets: {generated_offsets}")

all_block_offsets = sorted(b.start_offset for b in blocks)
not_generated = [o for o in all_block_offsets if o not in generated_offsets]
print(f"Not generated: {not_generated}")

# Check specifically blocks 448 and 488
print(f"\nBlock @448 generated: {448 in generated_offsets}")
print(f"Block @488 generated: {488 in generated_offsets}")

# Print the AST
print("\n=== Generated AST ===")
import json
def simplify(node, depth=0):
    if isinstance(node, dict):
        t = node.get('type', '?')
        indent = '  ' * depth
        if t == 'If':
            test = node.get('test', {})
            test_s = f"({test.get('type', '?')})"
            print(f"{indent}If test={test_s}")
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
            print(f"{indent}Return")
        elif t == 'Expr':
            print(f"{indent}Expr")
        else:
            print(f"{indent}{t}")

for node in result:
    simplify(node)