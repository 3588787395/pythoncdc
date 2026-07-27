"""R23-N4: 通过 monkey-patch 跟踪 get_fundflow_day 的 elif body 处理"""
import sys
import dis
import types
import ast

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator


PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    co = pyc_codes['get_fundflow_day']

    cfg = build_cfg(co)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    gen = RegionASTGenerator(cfg, analyzer)

    # Monkey-patch _process_if_blocks to trace
    original_process = gen._process_if_blocks
    def traced_process(blocks, region, branch='then'):
        print(f"\n[_process_if_blocks] branch={branch}, region.entry={region.entry.start_offset if region.entry else None}")
        print(f"  blocks: {[b.start_offset for b in blocks]}")
        print(f"  generated_blocks before: {sorted(b.start_offset for b in gen.generated_blocks)}")
        for b in blocks:
            in_gen = b in gen.generated_blocks
            entry_r = analyzer.get_entry_region_for_block(b)
            print(f"    block@{b.start_offset}: in_generated={in_gen}, entry_region={entry_r.region_type if entry_r else None}")
        result = original_process(blocks, region, branch)
        print(f"  result: {[s.get('type') if isinstance(s, dict) else type(s).__name__ for s in result]}")
        print(f"  generated_blocks after: {sorted(b.start_offset for b in gen.generated_blocks)}")
        return result
    gen._process_if_blocks = traced_process

    # Also patch _generate_region to trace
    original_gen_region = gen._generate_region
    def traced_gen_region(region):
        print(f"\n[_generate_region] region={region.region_type}, entry={region.entry.start_offset if region.entry else None}")
        result = original_gen_region(region)
        if isinstance(result, dict):
            print(f"  result: type={result.get('type')}")
        elif isinstance(result, list):
            print(f"  result: list of {len(result)} items")
        return result
    gen._generate_region = traced_gen_region

    print("=== AST 生成 ===")
    result = gen.generate()
    print(f"\n=== Final result ===")
    if isinstance(result, dict):
        body = result.get('body', [])
        print(f"Body length: {len(body)}")
        for i, stmt in enumerate(body):
            print(f"  Body[{i}]: {stmt.get('type') if isinstance(stmt, dict) else type(stmt).__name__}")


if __name__ == '__main__':
    main()
