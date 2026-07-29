"""R22 测试工程师：验证 _build_statements_from_instructions 对 UNPACK_SEQUENCE 的处理"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_generator_v2 import ExpressionReconstructor

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
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
    co = pyc_codes['get_quote']

    builder = CFGBuilder()
    cfg = builder.build(co)

    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    # Find the TernaryRegion
    ternary_region = None
    for r in regions:
        if type(r).__name__ == 'TernaryRegion':
            ternary_region = r
            break

    if ternary_region is None:
        print("No TernaryRegion found!")
        return

    print(f"TernaryRegion entry={ternary_region.entry.id}")
    print(f"  condition_block={ternary_region.condition_block.id if ternary_region.condition_block else None}")
    print(f"  true_value_block={ternary_region.true_value_block.id if ternary_region.true_value_block else None}")
    print(f"  false_value_block={ternary_region.false_value_block.id if ternary_region.false_value_block else None}")
    print(f"  merge_block={ternary_region.merge_block.id if ternary_region.merge_block else None}")
    print(f"  value_target={ternary_region.value_target}")

    # Test _build_statements_from_instructions with the condition block's pre-statements
    cond_block = ternary_region.condition_block
    print(f"\nCondition block {cond_block.id} instructions:")
    for ins in cond_block.instructions:
        print(f"  {ins.offset:4d}  {ins.opname:30s} {ins.argval!r}")

    # Get the pre-statement instructions (everything before the ternary condition)
    # The ternary condition is the last LOAD_FAST is_trade before POP_JUMP
    last_instr = cond_block.get_last_instruction()
    cond_instrs_raw = [i for i in cond_block.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]

    # Find the STORE_FAST instructions
    store_indices = []
    for idx, i in enumerate(cond_instrs_raw):
        if i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
            store_indices.append(idx)

    print(f"\nStore indices: {store_indices}")
    if store_indices:
        last_store = store_indices[-1]
        pred_instrs = list(cond_instrs_raw[:last_store + 1])
        print(f"\nPre-statement instructions ({len(pred_instrs)}):")
        for ins in pred_instrs:
            print(f"  {ins.offset:4d}  {ins.opname:30s} {ins.argval!r}")

        # Create an AST generator to test
        ast_gen = RegionASTGenerator(cfg, analyzer, co)
        stmts = ast_gen._build_statements_from_instructions(pred_instrs)
        print(f"\nGenerated statements: {stmts}")


if __name__ == '__main__':
    main()
