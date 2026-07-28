"""R30 调试get_cb_time_info函数的df赋值丢失问题"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find get_cb_time_info
def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, type(co)):
            r = find_code(c, name)
            if r:
                return r
    return None

target = find_code(code_obj, 'get_cb_time_info')
print(f"Found: {target.co_name}")

# Build CFG
builder = CFGBuilder()
cfg = builder.build(target)

# Find the block containing "df = returnDf[...]" (STORE_FAST 'df')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    instrs = [(i.opname, i.argval) for i in b.instructions]
    has_store_df = any(i[0] == 'STORE_FAST' and i[1] == 'df' for i in instrs)
    has_load_len = any(i[0] == 'LOAD_GLOBAL' and i[1] == 'len' for i in instrs)
    if has_store_df or (has_load_len and any('df' in str(i[1]) for i in instrs)):
        print(f"\n=== Block {b.start_offset} (store_df={has_store_df}, load_len={has_load_len}) ===")
        for i in b.instructions:
            print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
        print(f"  predecessors: {[p.start_offset for p in b.predecessors]}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Check what region the df-store block belongs to
print("\n=== get_region_for_block for df-store block ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    instrs = [(i.opname, i.argval) for i in b.instructions]
    if any(i[0] == 'STORE_FAST' and i[1] == 'df' for i in instrs):
        r = analyzer.get_region_for_block(b)
        print(f"Block {b.start_offset}: region={type(r).__name__ if r else None}, entry={r.entry.start_offset if r and r.entry else None}")
        er = analyzer.get_entry_region_for_block(b)
        print(f"  entry_region={type(er).__name__ if er else None}, entry={er.entry.start_offset if er and er.entry else None}")

# Check the LoopRegion containing this block
print("\n=== LoopRegion containing for stock in stock_list2 ===")
for r in analyzer.regions:
    if type(r).__name__ == 'LoopRegion':
        for b in r.blocks:
            instrs = [(i.opname, i.argval) for i in b.instructions]
            if any(i[0] == 'FOR_ITER' for i in instrs):
                print(f"LoopRegion entry={r.entry.start_offset if r.entry else None}")
                print(f"  blocks: {sorted(bb.start_offset for bb in r.blocks)}")
                if hasattr(r, 'body_blocks'):
                    print(f"  body_blocks: {sorted(bb.start_offset for bb in r.body_blocks)}")
                if hasattr(r, 'header_block'):
                    print(f"  header_block: {r.header_block.start_offset if r.header_block else None}")
                if hasattr(r, 'children'):
                    for c in r.children:
                        print(f"  child: {type(c).__name__} entry={c.entry.start_offset if c.entry else None}")
                        if hasattr(c, 'condition_block') and c.condition_block:
                            print(f"    condition_block: {c.condition_block.start_offset}")
                        if hasattr(c, 'then_blocks'):
                            print(f"    then_blocks: {[bb.start_offset for bb in c.then_blocks]}")
                        if hasattr(c, 'else_blocks'):
                            print(f"    else_blocks: {[bb.start_offset for bb in c.else_blocks]}")
                break

# Show the IfRegion that has the df-store block
print("\n=== IfRegion containing df-store block ===")
for r in analyzer.regions:
    if type(r).__name__ == 'IfRegion':
        for b in r.blocks:
            instrs = [(i.opname, i.argval) for i in b.instructions]
            if any(i[0] == 'STORE_FAST' and i[1] == 'df' for i in instrs):
                print(f"IfRegion entry={r.entry.start_offset if r.entry else None}")
                print(f"  blocks: {sorted(bb.start_offset for bb in r.blocks)}")
                if hasattr(r, 'condition_block') and r.condition_block:
                    print(f"  condition_block: {r.condition_block.start_offset}")
                    print(f"  condition_block instructions:")
                    for i in r.condition_block.instructions:
                        print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")
                if hasattr(r, 'then_blocks'):
                    print(f"  then_blocks: {[bb.start_offset for bb in r.then_blocks]}")
                if hasattr(r, 'else_blocks'):
                    print(f"  else_blocks: {[bb.start_offset for bb in r.else_blocks]}")
                break
