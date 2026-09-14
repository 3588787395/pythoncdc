import sys, types, marshal
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

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

inner_loop = None
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 50:
        inner_loop = region
        break

# Check: when _generate_loop is called for the inner loop,
# what path does the header block 50 take through _loop_handle_header?

# Let's check the conditions step by step in _loop_handle_header
block_50 = cfg.get_block_by_offset(50)
header = inner_loop.header_block

# The critical path: _loop_handle_header_no_condition is only called when
# condition_block is None AND first instr is in PLACEHOLDER_OPS
# Block 50 starts with LOAD_FAST (NOT in PLACEHOLDER_OPS), so it's NOT called.

# Instead, block 50 goes through _loop_handle_header which checks various conditions.
# Since condition_block is None and block_50 is the header, let's trace:

# Step: _header_if_region check (line 6880)
header_if_region = None
for _r in inner_loop.iter_descendants((IfRegion,)):
    if _r.condition_block == block_50 or _r.entry == block_50:
        header_if_region = _r
        break
print("_header_if_region:", header_if_region)

# Since _header_if_region is None, and condition_block is None:
# We reach line 7153-7158:
# if (condition_block is None and header starts with PLACEHOLDER_OPS...):
#   _loop_handle_header_no_condition(...)
# Block 50 starts with LOAD_FAST, so this is FALSE.

# Then we reach line 7160: _header_region check
header_region = analyzer.get_region_for_block(block_50)
print("header_region:", header_region)

# Since _header_if_region is None, we check line 7166:
# _header_if_region is not None -> False
# So we skip that block.

# What about line 7060+: _is_for_iter_setup?
# This is in the else branch of condition_block is not None
# But condition_block IS None, so we don't reach this.

# Actually wait - let me re-read the code flow more carefully.
# The condition_block checks at lines 6885-6963 are only entered if
# condition_block is not None. Since condition_block is None, we skip them.

# After the condition_block checks, we reach line 7153:
# if (condition_block is None and header starts with PLACEHOLDER...):
# This is False because block 50 starts with LOAD_FAST.

# Then line 7160:
# _header_region = get_region_for_block(block)
# _header_if_region check (line 7161-7165)
# Still None.

# Then line 7166: _header_if_region is not None -> False

# What comes after? Let me check line 7166+
# This is the else branch from condition_block not being None.
# But we're in the case where condition_block IS None.
# So... the code might fall through to something else.

# Actually, I realize the code structure might be different.
# Let me look at the full flow by checking what the outer loop does.

# The outer loop (header=48) processes block 50 as a child LoopRegion entry.
# The inner loop's _generate_loop generates block 50 as its header.
# In the inner loop's _loop_generate_body:
# - Block 50 is the header, so _loop_handle_header is called
# - Since condition_block is None and block 50 doesn't start with PLACEHOLDER_OPS,
#   the code falls through to _generate_block_statements (the generic path)

# Let me verify this by checking what _generate_block_statements produces for block 50
gen = RegionASTGenerator(cfg, analyzer)
block_stmts = gen._generate_block_statements(block_50)
import json
print()
print("=== _generate_block_statements for block 50 ===")
print(json.dumps(block_stmts, indent=2, default=str)[:2000])
