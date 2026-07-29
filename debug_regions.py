"""Debug: dump region structure for one_prod_to_dataframe."""
import sys, types, marshal
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TernaryRegion, LoopRegion

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find(c, name):
    for const in c.co_consts:
        if hasattr(const, 'co_name') and const.co_name == name:
            return const
        if hasattr(const, 'co_consts'):
            r = find(const, name)
            if r:
                return r
    return None

fn = find(code, 'one_prod_to_dataframe')
print(f"Function: {fn.co_name}")

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(fn)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

def blk(b):
    if b is None:
        return 'None'
    return f'@{b.start_offset}'

print(f"\n=== {len(regions)} regions ===")
region_list = []
for r in regions:
    eo = r.entry.start_offset if r.entry else -1
    region_list.append((eo, r))
region_list.sort()

for eo, r in region_list:
    rtype = type(r).__name__
    entry = blk(r.entry)
    blocks_offs = sorted(b.start_offset for b in r.blocks) if hasattr(r, 'blocks') else []
    extra = ''
    if isinstance(r, IfRegion):
        cb = blk(r.condition_block)
        mb = blk(r.merge_block)
        tb = sorted(b.start_offset for b in r.then_blocks) if r.then_blocks else []
        eb = sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []
        elc = sorted(b.start_offset for b in r.elif_conditions) if r.elif_conditions else []
        elb = [sorted(b.start_offset for b in body) for body in r.elif_bodies] if r.elif_bodies else []
        efe = sorted(b.start_offset for b in r.elif_final_else) if r.elif_final_else else []
        cco = getattr(r, 'chained_compare_ops', None)
        ibc = getattr(r, 'inline_boolop_chains', {})
        # ibc keyed by id(block); resolve to offset
        ibc_resolved = {}
        if ibc:
            id_to_block = {id(b): b for b in cfg.blocks.values()}
            for k, v in ibc.items():
                kb = id_to_block.get(k)
                kname = f'@{kb.start_offset}' if kb else f'id{k}'
                ibc_resolved[kname] = [blk(b) for b in v.get('blocks', [])]
        extra = f' cond={cb} merge={mb} then={tb} else={eb} elif_cond={elc} elif_bodies={elb} final_else={efe} cco={cco} ibc={ibc_resolved} rtype={r.region_type}'
    elif isinstance(r, BoolOpRegion):
        mb = blk(r.merge_block)
        op_chain = [(blk(b), op) for (b, op) in r.op_chain] if hasattr(r, 'op_chain') else []
        vt = getattr(r, 'value_target', None)
        extra = f' merge={mb} op_chain={op_chain} value_target={vt!r}'
    print(f'  [{rtype}] entry={entry} blocks={blocks_offs}{extra}')

print("\n=== block_to_region for offsets 620-1640 ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    if b.start_offset < 620 or b.start_offset > 1640:
        continue
    r = analyzer.block_to_region.get(b)
    rtype = type(r).__name__ if r else 'None'
    reoff = r.entry.start_offset if (r and r.entry) else -1
    last = b.get_last_instruction()
    last_desc = f'{last.opname}->{last.argval}' if last else 'None'
    print(f'  block@{b.start_offset:4} last={last_desc:35} -> region={rtype}@{reoff}')
