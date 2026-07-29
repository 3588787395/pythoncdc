"""R23-N6: 详细调试 block@456 在 _generate_block_statements 中的处理路径"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
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
    print(f"instructions: {len(b456.instructions)}")
    for i in b456.instructions:
        print(f"  {i.offset:>5} {i.opname:<30} {i.argval!r}")
    print(f"succs: {[s.start_offset for s in b456.successors]}")
    print(f"block_role: {analyzer.get_block_role(b456)}")
    print(f"is_generated: {b456 in analyzer.cfg.blocks}")

    # 模拟 _generate_block_statements 的早期检查
    print(f"\n=== 早期检查 ===")
    print(f"loop_depth (initial): 0")  # 假设
    print(f"has POP_TOP + LOAD_CONST None + RETURN_VALUE: {any(i.opname == 'POP_TOP' for i in b456.instructions) and any(i.opname == 'LOAD_CONST' and i.argval is None for i in b456.instructions) and any(i.opname == 'RETURN_VALUE' for i in b456.instructions)}")

    # 检查 block_role
    role = analyzer.get_block_role(b456)
    print(f"role: {role}")
    print(f"role is BREAK: {role in (BlockRole.BREAK, BlockRole.PURE_BREAK)}")
    print(f"role is RETURN: {role in (BlockRole.RETURN, BlockRole.RETURN_NONE)}")
    print(f"role is CONTINUE: {role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE) if hasattr(BlockRole, 'CONTINUE') else False}")


if __name__ == '__main__':
    main()
