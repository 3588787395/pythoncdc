import sys, os
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.environ['R23N21_DEBUG'] = '1'

from core.cfg.cfg_builder import ControlFlowGraph
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc'
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find handle_exrights
for const in code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'handle_exrights':
        code = const
        break

cfg = ControlFlowGraph(code)
generator = RegionASTGenerator(cfg)
generator.region_analyzer.analyze()

# Find BoolOpRegion containing the relevant blocks
from core.cfg.region_analyzer import BoolOpRegion, IfRegion
for r in generator.region_analyzer.regions:
    if isinstance(r, BoolOpRegion):
        print(f"BoolOpRegion: entry={r.entry.start_offset if r.entry else None}, op_chain={[(b.start_offset, op) for b, op in r.op_chain]}, merge={r.merge_block.start_offset if r.merge_block else None}")
        if r.op_chain:
            for b, op in r.op_chain:
                last = b.get_last_instruction()
                print(f"  block@{b.start_offset}: last_instr={last.opname if last else None}, op={op}")
                instrs = [i for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                for i in instrs[:-1] if last and last.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE') else instrs:
                    print(f"    {i.offset}: {i.opname} {i.argval if hasattr(i, 'argval') else ''}")

# Find IfRegion for handle_exrights
for r in generator.region_analyzer.regions:
    if isinstance(r, IfRegion):
        print(f"IfRegion: entry={r.entry.start_offset if r.entry else None}, cond={r.condition_block.start_offset if r.condition_block else None}, then={[b.start_offset for b in r.then_blocks]}, else={[b.start_offset for b in r.else_blocks]}, merge={r.merge_block.start_offset if r.merge_block else None}")
