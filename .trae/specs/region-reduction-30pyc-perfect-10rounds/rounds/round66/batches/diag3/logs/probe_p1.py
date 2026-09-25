import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
from core.cfg import build_cfg
from core.cfg import region_analyzer as RA

def load(p):
    d = io.open(p, 'rb').read()
    return marshal.loads(d[16:])

top = load(sys.argv[1])
name = sys.argv[2]
cs = [c for c in RA.__dict__.get('_x', [])] if False else None
def walk(c, o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType): walk(k, o)
    return o
code = [c for c in walk(top, []) if c.co_name == name][0]
cfg = build_cfg(code)
print('FORWARD_CONDITIONAL_JUMP_OPS =', getattr(RA, 'FORWARD_CONDITIONAL_JUMP_OPS', 'N/A'))
BL = cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks
for b in sorted(BL, key=lambda x: x.start_offset)[:14]:
    ins = [(i.opname, i.argval if not isinstance(i.argval, types.CodeType) else 'CODEOBJ') for i in b.instructions]
    print('BLK@%-4d %s  succ=%s cond_succ=%s' % (
        b.start_offset, ins,
        [getattr(s,'start_offset',s) for s in (b.successors or [])],
        [getattr(s,'start_offset',s) for s in (getattr(b,'conditional_successors',None) or [])]))
from core.cfg.region_ast_generator import RegionASTGenerator
gen = RegionASTGenerator(cfg, top_level_code=None)
an = gen.region_analyzer
regions = an.analyze()
print('--- regions ---')
for r in regions:
    print(type(r).__name__, 'entry=', getattr(r.entry,'start_offset',None),
          'blocks=', [getattr(x,'start_offset',None) for x in r.blocks],
          'cc_ops=', getattr(r,'chained_compare_ops',None),
          'cc_blocks=', [getattr(x,'start_offset',None) for x in (getattr(r,'chained_compare_blocks',None) or [])],
          'then=', [getattr(x,'start_offset',None) for x in (getattr(r,'then_blocks',None) or [])],
          'else=', [getattr(x,'start_offset',None) for x in (getattr(r,'else_blocks',None) or [])],
          'merge=', getattr(getattr(r,'merge_block',None),'start_offset',None),
          'vt=', getattr(r,'value_target',None), 'mc=', getattr(r,'merge_context',None))
# replay Phase-7-D guards on entry block
blk = [b for b in BL if b.start_offset == int(sys.argv[3])][0]
print('=== guard replay on BLK@%d ===' % blk.start_offset)
fn = getattr(an, '_can_be_ternary_header', None)
print('has _can_be_ternary_header:', fn is not None and fn(blk))
li = blk.get_last_instruction()
print('last_instr', li.opname, li.argval)
heads = sorted(blk.conditional_successors, key=lambda s: s.start_offset)
print('cond_succ', [h.start_offset for h in heads])
cc = None
for r in an.regions:
    if isinstance(r, RA.IfRegion) and r.region_type == RA.RegionType.IF and r.entry is blk:
        print('found IfRegion entry==blk cc_ops', r.chained_compare_ops, 'cc_blocks', [x.start_offset for x in r.chained_compare_blocks])
        if r.chained_compare_ops and len(r.chained_compare_ops) >= 2 and r.chained_compare_blocks:
            cc = r
        break
print('_is_chained_compare_header(blk) =', an._is_chained_compare_header(blk))
if cc is not None:
    allc = [blk] + list(cc.chained_compare_blocks)
    lastc = allc[-1]
    ll = lastc.get_last_instruction()
    print('last_cc_block@%d last=%s %s inFCJ=%s' % (lastc.start_offset, ll.opname, ll.argval,
          ll.opname in getattr(RA,'FORWARD_CONDITIONAL_JUMP_OPS',())))
    succs = sorted(lastc.conditional_successors, key=lambda s: s.start_offset)
    print('last_cc cond_succ', [s.start_offset for s in succs], 'len', len(succs))
    if len(succs) == 2:
        ct = next((s for s in succs if s.start_offset != ll.argval), None)
        cf = next((s for s in succs if s.start_offset == ll.argval), None)
        print('ct@%s cf@%s' % (getattr(ct,'start_offset',None), getattr(cf,'start_offset',None)))
        if ct and cf:
            eff = [i for i in ct.instructions if i.opname not in RA.NOISE_OPS]
            print('ct_eff', [(i.opname, i.argval) for i in eff])
            print('single_expr(ct)=', an._is_single_expression_block(ct), 'single_expr(cf)=', an._is_single_expression_block(cf))
