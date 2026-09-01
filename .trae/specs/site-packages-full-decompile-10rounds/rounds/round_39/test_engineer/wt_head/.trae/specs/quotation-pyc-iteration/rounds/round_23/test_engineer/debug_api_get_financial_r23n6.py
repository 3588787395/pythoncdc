"""R23-N6: 调试 api_get_financial 函数的 SWAP+POP_EXCEPT+RETURN_VALUE 模式检测"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'


def find_code_obj(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            r = find_code_obj(c, name)
            if r:
                return r
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

    print(f"found api_get_financial: {len(target.co_code)} bytes")

    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # 找包含 offset 546/550/552/554/562 的块
    target_offsets = [546, 550, 552, 554, 556, 558, 560, 562, 564]
    blocks_by_offset = {}
    for b in cfg.blocks.values():
        for off in target_offsets:
            instr_offsets = [i.offset for i in b.instructions]
            if off in instr_offsets or b.start_offset == off:
                blocks_by_offset.setdefault(b.start_offset, b)

    print(f"\n=== 关键块（按 start_offset 排序） ===")
    for off in sorted(blocks_by_offset.keys()):
        b = blocks_by_offset[off]
        print(f"\nBlock@{b.start_offset} (id={b.id}):")
        for i in b.instructions:
            print(f"  {i.offset:>5} {i.opname:<30} {i.argval!r}")
        print(f"  succs: {[s.start_offset for s in b.successors]}")

    # 调试 _find_return_chain_via_successors
    print(f"\n=== _find_return_chain_via_successors 调试 ===")
    gen = RegionASTGenerator(cfg, analyzer)
    for off in sorted(blocks_by_offset.keys()):
        b = blocks_by_offset[off]
        chain = gen._find_return_chain_via_successors(b)
        print(f"Block@{b.start_offset}: chain={[c.start_offset for c in chain] if chain else None}")

    # 检查 try_depth
    print(f"\n=== _try_depth 检查 ===")
    print(f"_try_depth (initial): {gen._try_depth}")


if __name__ == '__main__':
    main()
