import sys, marshal, types, dis, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/common/tradingday_calendar.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig)
co = om['reload_data']

# Build CFG
cfg = build_cfg(co)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Generate AST
gen = RegionASTGenerator(cfg, analyzer)

# Get block 1576
block_1576 = cfg.get_block_by_offset(1576)
print("Block 1576 successors:")
for succ in block_1576.successors:
    print(f"  Block {succ.start_offset}: {[i.opname for i in succ.instructions]}")
    is_exc_cleanup = (
        any(i.opname in ('RERAISE', 'POP_EXCEPT', 'PUSH_EXC_INFO') for i in succ.instructions)
        and not any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in succ.instructions)
    )
    print(f"    is_exc_cleanup = {is_exc_cleanup}")

# The POP_JUMP_FORWARD_IF_FALSE target is 1652
# So target_block = 1652
# Non-target successors are 1654 and 1610
# 1654 has COPY, POP_EXCEPT, RERAISE - is_exc_cleanup = True
# 1610 has LOAD_FAST, LOAD_METHOD, CALL, POP_TOP, RERAISE - is_exc_cleanup = True

# So both non-target successors are marked as exc_cleanup!
# Then the fallback picks the first non-target successor (1654 or 1610?)

# Let's check the order
print("\nNon-target successors (in order):")
target = 1652
for succ in block_1576.successors:
    if succ.start_offset != target:
        is_exc_cleanup = (
            any(i.opname in ('RERAISE', 'POP_EXCEPT', 'PUSH_EXC_INFO') for i in succ.instructions)
            and not any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in succ.instructions)
        )
        print(f"  Block {succ.start_offset}: is_exc_cleanup={is_exc_cleanup}")
