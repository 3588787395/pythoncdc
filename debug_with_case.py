#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ast
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator

def debug_test_case():
    source_code = """if a > 0:
    with open("f") as f:
        a = f.read()"""
    
    print("=== Source Code ===")
    print(source_code)
    
    # Compile to bytecode
    print("\n=== Compiling ===")
    tree = ast.parse(source_code)
    code_obj = compile(tree, '<test>', 'exec')
    
    print("\n=== Original Bytecode ===")
    import dis
    dis.dis(code_obj)
    
    print("\n=== Building CFG ===")
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code_obj)
    
    print("\n=== Analyzing Regions ===")
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    
    print("\n=== Regions Found ===")
    for region in analyzer.regions:
        print(f"  - {type(region).__name__}: entry={region.entry.start_offset if region.entry else None}")
        print(f"    region_type: {region.region_type}")
        if hasattr(region, 'items'):
            print(f"    items: {region.items}")
        if hasattr(region, 'resource_expr'):
            print(f"    resource_expr: {region.resource_expr}")
        if hasattr(region, 'target'):
            print(f"    target: {region.target}")
        if hasattr(region, 'with_blocks'):
            print(f"    with_blocks: {[b.start_offset for b in region.with_blocks]}")
        if hasattr(region, 'body_offset_start'):
            print(f"    body_offset_start: {region.body_offset_start}")
        if hasattr(region, 'body_offset_end'):
            print(f"    body_offset_end: {region.body_offset_end}")
    
    print("\n=== Generating AST ===")
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    
    print("\n=== Generated AST ===")
    print(result)
    
    print("\n=== Generating Code ===")
    code_gen = CodeGenerator()
    decompiled = code_gen.generate(result)
    print("\n=== Decompiled ===")
    print(decompiled)
    
    # 验证语法
    print("\n=== 验证语法 ===")
    try:
        parsed_decompiled = ast.parse(decompiled)
        print("语法检查通过")
    except Exception as e:
        print(f"语法检查失败: {e}")
        import traceback
        traceback.print_exc()
    
    return decompiled

if __name__ == "__main__":
    debug_test_case()
