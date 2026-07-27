"""R23-N4: 详细跟踪 block 198 在 _process_if_blocks 中的处理路径"""
import sys
import dis
import types
import ast

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion, BlockRole
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

    # 找到 FOR_LOOP 区域
    for_loop = None
    for r in analyzer.regions:
        if r.region_type.name == 'FOR_LOOP' and r.entry and r.entry.start_offset == 198:
            for_loop = r
            break

    print(f"FOR_LOOP region: {for_loop}")
    print(f"  blocks: {[b.start_offset for b in for_loop.blocks]}")
    print(f"  header_block: {for_loop.header_block.start_offset if for_loop.header_block else None}")
    print(f"  body_blocks: {[b.start_offset for b in for_loop.body_blocks]}")
    print(f"  metadata: {for_loop.metadata}")
    print(f"  for_iter_setup: {for_loop.metadata.get('for_iter_setup')}")

    # 检查 block 198 的 role
    block_198 = cfg.get_block_by_offset(198)
    role = analyzer.get_block_role(block_198)
    print(f"\nBlock@198 role: {role}")

    # 检查 IF_ELIF_CHAIN 的 else_blocks
    if_elif = None
    for r in analyzer.regions:
        if r.region_type.name == 'IF_ELIF_CHAIN' and r.entry and r.entry.start_offset == 70:
            if_elif = r
            break

    print(f"\nIF_ELIF_CHAIN region:")
    print(f"  then_blocks: {[b.start_offset for b in if_elif.then_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in if_elif.else_blocks]}")
    print(f"  elif_conditions: {[b.start_offset for b in if_elif.elif_conditions]}")
    print(f"  elif_bodies: {[[b.start_offset for b in body] for body in if_elif.elif_bodies]}")
    print(f"  elif_final_else: {[b.start_offset for b in if_elif.elif_final_else] if if_elif.elif_final_else else None}")
    print(f"  children: {[(c.region_type, c.entry.start_offset if c.entry else None) for c in (if_elif.children or [])]}")

    # 检查 for_iter_setup 是否是 block 198
    fis = for_loop.metadata.get('for_iter_setup')
    print(f"\nfor_iter_setup is block 198? {fis is block_198}")
    print(f"for_iter_setup: {fis}")

    # 检查 FOR_LOOP 是否在 IF_ELIF_CHAIN 的 children 中
    print(f"\nFOR_LOOP in IF_ELIF_CHAIN.children? {for_loop in (if_elif.children or [])}")
    print(f"FOR_LOOP.parent: {for_loop.parent}")


if __name__ == '__main__':
    main()
