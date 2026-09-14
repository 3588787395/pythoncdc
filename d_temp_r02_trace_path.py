import sys, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, BoolOpRegion, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator, FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS
from core.cfg.dominator_analyzer import PLACEHOLDER_OPS
import marshal

with open('site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            result = find_code(const, name)
            if result:
                return result
    return None

tick = find_code(code, 'tick_worker_thread')

builder = CFGBuilder()
cfg = builder.build(tick)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find inner loop (header=50)
inner_loop = None
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 50:
        inner_loop = region
        break

block_50 = cfg.get_block_by_offset(50)
header = inner_loop.header_block

# Step 1: _header_expr_region check (line 6821-6830)
header_expr_region = None
for _child in (inner_loop.children or []):
    from core.cfg.region_ast_generator import TernaryRegion
    _EXPR_REGION_TYPES = (BoolOpRegion, TernaryRegion)
    if isinstance(_child, _EXPR_REGION_TYPES) and _child.entry == block_50:
        header_expr_region = _child
        break
if header_expr_region is None:
    for _r in analyzer.regions:
        if isinstance(_r, _EXPR_REGION_TYPES) and _r.entry == block_50 and _r is not inner_loop:
            header_expr_region = _r
            break
print("Step 1: _header_expr_region =", header_expr_region)

# Step 2: _header_with_region (line 6849-6854)
from core.cfg.region_analyzer import WithRegion
header_with_region = None
for _r in inner_loop.iter_descendants((WithRegion,)):
    if _r.entry == block_50:
        header_with_region = _r
        break
print("Step 2: _header_with_region =", header_with_region)

# Step 3: condition_block == header (line 6868)
print("Step 3: condition_block == header:", inner_loop.condition_block == header)
print("        condition_block:", inner_loop.condition_block)

# Step 4: self-loop check (line 6871-6878)
print("Step 4: back_edge_block == header:", inner_loop.back_edge_block == header)
print("        condition_block is not None:", inner_loop.condition_block is not None)
print("        condition_block != header:", inner_loop.condition_block != header if inner_loop.condition_block else 'N/A')

# Step 5: _header_if_region (line 6880-6884)
header_if_region = None
for _r in inner_loop.iter_descendants((IfRegion,)):
    if _r.condition_block == block_50 or _r.entry == block_50:
        header_if_region = _r
        break
print("Step 5: _header_if_region =", header_if_region)

# Step 6: condition_block is not None (line 6885-6888)
print("Step 6: condition_block is not None:", inner_loop.condition_block is not None)

# Step 7: PLACEHOLDER_OPS check (line 7153-7158)
print("Step 7: first instr in PLACEHOLDER_OPS:", block_50.instructions[0].opname in PLACEHOLDER_OPS)
print("        any non-placeholder:", any(i.opname not in PLACEHOLDER_OPS for i in block_50.instructions))

# Step 8: _header_if_region check (line 7161-7165)
header_if_region2 = None
if header_if_region is None:
    for _r in inner_loop.iter_descendants((IfRegion,)):
        if _r.condition_block == block_50 or _r.entry == block_50:
            header_if_region2 = _r
            break
print("Step 8: _header_if_region (2nd check) =", header_if_region2)

# So what happens? Since condition_block is None and header starts with LOAD_FAST (not PLACEHOLDER),
# the code skips _loop_handle_header_no_condition.
# Then at line 7161, _header_if_region is None (no IfRegion for block 50).
# So it falls through to... what?

# Let me check what happens after line 7166
print()
print("=== Since _header_if_region is None, checking subsequent conditions ===")
# Line 7166: _header_if_region is not None -> False, skip

# What about _is_for_iter_setup (line 7060)?
print("_is_for_iter_setup: need to check")

# Actually, for while-True with condition_block=None and no IfRegion,
# the path depends on which condition_block checks are hit.
# Let me check the _child_while_cond path (line 7069)
child_while_cond = None
for _cr in analyzer.regions:
    if (isinstance(_cr, LoopRegion) and _cr.region_type.name == 'WHILE_LOOP'
        and hasattr(_cr, 'condition_block') and _cr.condition_block == block_50
        and _cr != inner_loop):
        child_while_cond = _cr
        break
print("_child_while_cond:", child_while_cond)

# Check if it's _loop_extract_self_loop_stmts path (line 7132)
# This happens when none of the above conditions match
# Let me check the _hdr_last / _exit_succs path
hdr_last = block_50.get_last_instruction()
exit_succs = [s for s in block_50.successors
               if analyzer.get_block_role(s) in
               (BlockRole.BREAK, BlockRole.PURE_BREAK,
                BlockRole.RETURN, BlockRole.RETURN_NONE)]
back_edge_succ = (inner_loop.back_edge_block in block_50.successors)

print()
print("hdr_last:", hdr_last.opname, hdr_last.argval)
print("exit_succs:", [(s.start_offset, analyzer.get_block_role(s)) for s in exit_succs])
print("back_edge_succ:", back_edge_succ)
print("header.successors:", [(s.start_offset, analyzer.get_block_role(s)) for s in block_50.successors])

# Check condition at line 7127-7129:
# _hdr_last in FORWARD_CONDITIONAL_JUMP_OPS and len(_exit_succs) == 1 and _back_edge_succ and len(header.successors) == 2
is_forward_cond = hdr_last.opname in FORWARD_CONDITIONAL_JUMP_OPS
print()
print("hdr_last in FORWARD_CONDITIONAL_JUMP_OPS:", is_forward_cond)
print("len(exit_succs) == 1:", len(exit_succs) == 1)
print("back_edge_succ:", back_edge_succ)
print("len(header.successors) == 2:", len(block_50.successors) == 2)

# Since these conditions are not all met, the code falls through to line 7132:
# _self_loop_stmts = self._loop_extract_self_loop_stmts(header)
print()
print("==> Block 50 goes to _loop_extract_self_loop_stmts at line 7132!")
print("    But wait - block 50 has 3 successors (168, 210, 1290)!")
print("    1290 is an exception handler block.")
