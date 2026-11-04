# rr-v5r113 区域树 / CFG 完整 dump（r1 尾 break vs r3 无 break 对照）
# 定位「尾部 break 让 WhileRegion 消失」：哪一层没建出 LoopRegion，
# 哪个块被误判为入口/出口，哪个 IfRegion 把条件渲染成裸表达式。
import sys, os, marshal
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg import region_analyzer as RA

REPRO = 'D:/temp/opencode/cl_layout/r112diag_a/repro'
OUT = 'D:/temp/opencode/cl_layout/r113diag'
CASES = ['r1_while_yield_break', 'r2_while_yield_preinit',
         'r3_while_yield_no_break', 'r4_exact_shape']


def li(b):
    i = b.get_last_instruction()
    return '%s->%s' % (i.opname, i.argval) if i else '?'


def off(b):
    return b.start_offset if b is not None else None


def so(bs):
    return ', '.join(str(x.start_offset) for x in sorted(bs, key=lambda z: z.start_offset)) if bs else ''


def dump(gen, out):
    cfg = gen.cfg
    ra = gen.region_analyzer
    regs = getattr(ra, 'regions', None) or []
    out.append('==== cfg=%s regions=%d ====' % (cfg.name, len(regs)))
    try:
        out.append('--- loop_analyzer.back_edges (src->tgt) ---')
        for src, tgt in ra.loop_analyzer.back_edges:
            out.append('  @%s -> @%s' % (src.start_offset, tgt.start_offset))
        out.append('--- get_all_loops headers ---')
        for h in ra.loop_analyzer.get_all_loops():
            out.append('  header=@%s' % h.start_offset)
    except Exception as e:
        out.append('  (loop_analyzer err %r)' % e)
    out.append('--- CFG blocks ---')
    _blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    for b in sorted(_blocks, key=lambda x: x.start_offset):
        out.append('  @%-5d last=%-38s succs=[%s] preds=[%s] loop_header=%s is_back_edge=%s' % (
            b.start_offset, li(b), so(b.successors), so(b.predecessors),
            getattr(b, 'loop_header', False), getattr(b, 'is_back_edge', False)))
        ins = ' | '.join('%s(%s)' % (i.opname, i.argval)
                         for i in b.instructions
                         if i.opname not in ('CACHE', 'RESUME', 'NOP', 'PRECALL', 'EXTENDED_ARG'))
        out.append('       %s' % ins)
    try:
        b2r = getattr(ra, 'block_to_region', None) or {}
        out.append('--- block_to_region ---')
        for b, r in sorted(b2r.items(), key=lambda kv: kv[0].start_offset if hasattr(kv[0], 'start_offset') else -1):
            out.append('  @%s -> %s(@%s)' % (b.start_offset, type(r).__name__, off(getattr(r, 'entry', None))))
    except Exception as e:
        out.append('  (b2r err %r)' % e)
    out.append('--- REGIONS ---')
    for r in regs:
        cls = type(r).__name__
        par = getattr(r, 'parent', None)
        par_s = ('@%s' % par.entry.start_offset) if (par is not None and getattr(par, 'entry', None) is not None) else 'None'
        out.append('%s entry=@%s parent=%s rtype=%s' % (
            cls, off(getattr(r, 'entry', None)), par_s, getattr(r, 'region_type', '?')))
        out.append('  blocks=[%s]' % so(getattr(r, 'blocks', None)))
        if isinstance(r, RA.LoopRegion):
            out.append('  LoopRegion header=@%s cond=@%s back_edge=@%s back_edges=[%s]' % (
                off(r.header_block), off(r.condition_block), off(r.back_edge_block),
                so(getattr(r, 'back_edge_blocks', None))))
            out.append('  body=[%s] init=[%s] else=[%s] break=[%s] precond=[%s] cond_recheck=[%s]' % (
                so(getattr(r, 'body_blocks', None)), so(getattr(r, 'init_blocks', None)),
                so(getattr(r, 'else_blocks', None)), so(getattr(r, 'break_blocks', None)),
                so(getattr(r, 'pre_condition_blocks', None)),
                so(getattr(r, 'condition_recheck_blocks', None))))
            out.append('  is_while_true=%s has_break=%s is_yield_from=%s else_is_follow=%s' % (
                getattr(r, 'is_while_true', '?'), getattr(r, 'has_break', '?'),
                getattr(r, 'is_yield_from', '?'), getattr(r, 'else_is_follow', '?')))
        if isinstance(r, RA.IfRegion):
            cb = getattr(r, 'condition_block', None)
            out.append('  IfRegion cond=@%s merge=@%s then=[%s] else=[%s] elif=[%s]' % (
                off(cb), off(getattr(r, 'merge_block', None)),
                so(getattr(r, 'then_blocks', None)), so(getattr(r, 'else_blocks', None)),
                so(getattr(r, 'elif_conditions', None))))
            out.append('    cond_lastj=%s has_trailing=%s' % (
                li(cb) if cb else '?', getattr(r, 'has_trailing_return_none', '?')))


_orig_generate = RegionASTGenerator.generate
CUR = []


def w_generate(self):
    r = _orig_generate(self)
    CUR.append(self)
    return r


RegionASTGenerator.generate = w_generate

os.makedirs(OUT, exist_ok=True)
for name in CASES:
    pyc = REPRO + '/%s_orig.pyc' % name
    code = marshal.loads(open(pyc, 'rb').read()[16:])
    cfg = build_cfg(code)
    CUR = []
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    out = []
    try:
        gen.generate()
        for g in CUR:
            if g.cfg.name != '<module>':
                dump(g, out)
    except Exception as e:
        import traceback
        out.append('EXCEPTION %r' % e)
        out += traceback.format_exc().splitlines()
    open(OUT + '/tree_%s.txt' % name, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(name, '->', len(out), 'lines, gens=', len(CUR))
