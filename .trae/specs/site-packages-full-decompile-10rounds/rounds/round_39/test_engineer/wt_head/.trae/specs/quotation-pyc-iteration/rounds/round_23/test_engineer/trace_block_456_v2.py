"""R23-N6: 追踪 block@456 在 _generate_block_statements 中的处理路径"""
import sys
import os

sys.path.insert(0, '/workspace')

os.environ['R23N6_DEBUG'] = '1'
os.environ['R23N6_DEBUG2'] = '1'
os.environ['R23N6_DEBUG3'] = '1'
os.environ['R23N6_DEBUG4'] = '1'
os.environ['R23N6_DEBUG5'] = '1'

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'


def find_code_obj(co, name):
    for const in co.co_consts:
        if isinstance(const, type(co)):
            if const.co_name == name:
                return const
            sub = find_code_obj(const, name)
            if sub:
                return sub
    return None


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = find_code_obj(code_obj, 'api_get_financial')
    if not target:
        print("api_get_financial not found")
        return

    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # 找 block@456
    b456 = None
    for b in cfg.blocks.values():
        if b.start_offset == 456:
            b456 = b
            break

    if not b456:
        print("block@456 not found")
        return

    print(f"=== block@456 ===")
    print(f"block_role: {analyzer.get_block_role(b456)}")
    print(f"instructions: {len(b456.instructions)}")
    for i in b456.instructions:
        print(f"  {i.offset:>5} {i.opname:<30} {i.argval!r}")
    print(f"succs: {[s.start_offset for s in b456.successors]}")

    # 检查 block@456 是否在某个 region 中
    print(f"\n=== block@456 所属 region ===")
    for region in analyzer.regions:
        if b456 in region.blocks:
            print(f"  {type(region).__name__}: entry={region.entry.start_offset if hasattr(region, 'entry') and region.entry else 'N/A'}")

    # 调用 _generate_block_statements
    print(f"\n=== 调用 _generate_block_statements(block@456) ===")
    gen = RegionASTGenerator(cfg, analyzer)
    # 设置 try_depth
    print(f"try_depth (before): {gen._try_depth}")
    # 检查 block 是否在 try_region 中
    for region in analyzer.regions:
        if hasattr(region, 'try_blocks') and b456 in (region.try_blocks or []):
            print(f"  block@456 in try_region: try_blocks={[b.start_offset for b in region.try_blocks]}")
        if hasattr(region, 'handler_entry_blocks') and b456 in (region.handler_entry_blocks or []):
            print(f"  block@456 is a handler entry")
        if hasattr(region, 'except_handlers'):
            for exc_type, exc_name, handler_blocks in region.except_handlers:
                if b456 in handler_blocks:
                    print(f"  block@456 in except_handler (type={exc_type}, name={exc_name}): blocks={[b.start_offset for b in handler_blocks]}")

    stmts = gen._generate_block_statements(b456)
    print(f"\n=== 结果 ===")
    print(f"stmts count: {len(stmts)}")
    for i, s in enumerate(stmts):
        print(f"  [{i}] {s!r}")


if __name__ == '__main__':
    main()
