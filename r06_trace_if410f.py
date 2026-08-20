#!/usr/bin/env python3
"""Trace elif chain handling for IfRegion@76"""

import sys, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, IfRegion
from core.cfg.region_analyzer import BlockRole
import marshal

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

# Monkey-patch _if_generate_full_elif_chain
_orig_full = RegionASTGenerator._if_generate_full_elif_chain
def traced_full(self, region):
    is_target = region.entry and region.entry.start_offset == 76
    if is_target:
        print(f"\n=== _if_generate_full_elif_chain @76 ===")
        print(f"  condition_block: {region.condition_block.start_offset if region.condition_block else None}")
        print(f"  then_blocks: {[b.start_offset for b in region.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in (region.else_blocks or [])]}")
        print(f"  elif_conditions: {[b.start_offset for b in (region.elif_conditions or [])]}")
        print(f"  elif_bodies: {[[b.start_offset for b in body] for body in (region.elif_bodies or [])]}")
        print(f"  elif_final_else: {[b.start_offset for b in (region.elif_final_else or [])]}")
        print(f"  merge_block: {region.merge_block.start_offset if region.merge_block else None}")
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in (region.children or [])]}")

    result = _orig_full(self, region)

    if is_target:
        print(f"  After: result type={type(result).__name__}")
        if isinstance(result, dict):
            print(f"  result: {result.get('type', '?')}")
            body = result.get('body', [])
            orelse = result.get('orelse', [])
            print(f"  body: {len(body)} stmts")
            for s in body:
                if isinstance(s, dict):
                    print(f"    {s.get('type','?')}")
            print(f"  orelse: {len(orelse)} stmts")
            for s in orelse:
                if isinstance(s, dict):
                    print(f"    {s.get('type','?')}")
        print(f"  448: {448 in self.generated_offsets}")
        print(f"  488: {488 in self.generated_offsets}")

    return result

RegionASTGenerator._if_generate_full_elif_chain = traced_full

# Also patch _if_generate_elif_chain
_orig_elif = RegionASTGenerator._if_generate_elif_chain
def traced_elif(self, region):
    is_target = region.entry and region.entry.start_offset == 76
    if is_target:
        print(f"\n  --- _if_generate_elif_chain @76 ---")
        print(f"    elif_conditions: {[b.start_offset for b in (region.elif_conditions or [])]}")
        print(f"    elif_bodies: {[[b.start_offset for b in body] for body in (region.elif_bodies or [])]}")

    result = _orig_elif(self, region)

    if is_target:
        print(f"    After: result type={type(result).__name__}")
        if isinstance(result, list):
            for r in result:
                if isinstance(r, dict):
                    print(f"      {r.get('type','?')}")
                    body = r.get('body', [])
                    print(f"      body: {len(body)} stmts")
                    for s in body:
                        if isinstance(s, dict):
                            print(f"        {s.get('type','?')}")
                    orelse = r.get('orelse', [])
                    print(f"      orelse: {len(orelse)} stmts")
                    for s in orelse:
                        if isinstance(s, dict):
                            print(f"        {s.get('type','?')}")
        print(f"    448: {448 in self.generated_offsets}")
        print(f"    488: {488 in self.generated_offsets}")

    return result

RegionASTGenerator._if_generate_elif_chain = traced_elif

# Also patch _process_if_blocks
_orig_pib = RegionASTGenerator._process_if_blocks
def traced_pib(self, blocks, region, branch='then'):
    is_target = any(b.start_offset == 410 for b in blocks)
    if is_target:
        print(f"\n  >>> _process_if_blocks branch={branch}")
        print(f"    blocks: {[b.start_offset for b in blocks]}")

    result = _orig_pib(self, blocks, region, branch)

    if is_target:
        print(f"    After: result={len(result) if isinstance(result,list) else 1} stmts")
        for s in (result if isinstance(result, list) else [result]):
            if isinstance(s, dict):
                print(f"      {s.get('type','?')}")
        print(f"    448: {448 in self.generated_offsets}")
        print(f"    488: {488 in self.generated_offsets}")

    return result

RegionASTGenerator._process_if_blocks = traced_pib

gen = RegionASTGenerator(cfg, recursive=True, parent_code=orig_co)
result = gen.generate()

print(f"\n=== Final ===")
print(f"448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}")