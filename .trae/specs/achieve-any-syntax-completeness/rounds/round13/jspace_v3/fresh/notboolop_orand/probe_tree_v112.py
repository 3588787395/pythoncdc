# rr-v5r112 区域树完整 dump（m8 族 + 真嵌套控制案），用于定位
# 「or 真出口极性反 + and 尾拆嵌套 if」的判别器。
import sys, os, marshal, types, py_compile
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg import region_analyzer as RA

EV = 'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/notboolop_orand'
DIAG = 'D:/temp/opencode/cl_layout/r112diag_b'

CASES = {
 'm8_getfield': None,
 'n8_true_nested': '''def p(a, b, c, f):
    if not a:
        if b and c:
            f.v = 1
    return f
''',
 'n8_or_and': '''def p(a, b, c, f):
    if a or (b and c):
        f.v = 1
    return f
''',
 'n8_or_and_term': '''def p(a, b, c, f):
    if a or (b and c):
        raise TypeError('x')
    return f
''',
}

def li(b):
    i = b.get_last_instruction()
    return '%s->%s' % (i.opname, i.argval) if i else '?'

def dump(gen, out):
    regs = getattr(gen.region_analyzer, 'regions', None) or []
    out.append('==== cfg=%s regions=%d ====' % (gen.cfg.name, len(regs)))
    out.append('--- CFG blocks ---')
    _blocks = list(gen.cfg.blocks.values()) if isinstance(gen.cfg.blocks, dict) else list(gen.cfg.blocks)
    for b in sorted(_blocks, key=lambda x: x.start_offset):
        out.append('  @%-5d last=%-42s succs=[%s]' % (
            b.start_offset, li(b),
            ', '.join(str(s.start_offset) for s in b.successors)))
    for r in regs:
        p = '  '
        cls = type(r).__name__
        entry = getattr(r, 'entry', None)
        merge = getattr(r, 'merge_block', None)
        _par = getattr(r, 'parent', None)
        _par_s = ('@'+str(_par.entry.start_offset)) if (_par is not None and getattr(_par, 'entry', None) is not None) else 'None'
        out.append('%s%s entry=@%s merge=@%s parent=%s' % (
            p, cls, entry.start_offset if entry else '?',
            merge.start_offset if merge else '?', _par_s))
        out.append('%s  blocks=[%s]' % (p, ', '.join(str(b.start_offset) for b in getattr(r, 'blocks', []) or [])))
        if isinstance(r, RA.BoolOpRegion):
            oc = getattr(r, 'op_chain', None) or []
            out.append('%s  op_chain=%s value_target=%s cond_ctx=%s' % (
                p, [(b.start_offset, op, li(b)) for b, op in oc],
                getattr(r, 'value_target', '?'), getattr(r, 'is_condition_context', '?')))
            mb = merge
            if mb:
                out.append('%s  merge_instrs=%s' % (p, [i.opname for i in mb.instructions if i.opname not in ('RESUME','NOP','CACHE')]))
        if isinstance(r, RA.IfRegion):
            cb = getattr(r, 'condition_block', None)
            out.append('%s  condition_block=@%s rtype=%s then=[%s] else=[%s]' % (
                p, cb.start_offset if cb else '?', getattr(r, 'region_type', '?'),
                ', '.join(str(b.start_offset) for b in (getattr(r, 'then_blocks', None) or [])),
                ', '.join(str(b.start_offset) for b in (getattr(r, 'else_blocks', None) or []))))
            out.append('%s  elif_conditions=[%s] cond_lastj=%s has_trailing=%s' % (
                p, ', '.join(str(b.start_offset) for b in (getattr(r, 'elif_conditions', None) or [])),
                li(cb) if cb else '?', getattr(r, 'has_trailing_return_none', '?')))

_orig_generate = RegionASTGenerator.generate
CUR = []
def w_generate(self):
    r = _orig_generate(self)
    CUR.append(self)
    return r
RegionASTGenerator.generate = w_generate

for name, src in CASES.items():
    if src is None:
        pyc = DIAG + '/%s.pyc' % name
    else:
        sp = EV + '/%s.py' % name
        pyc = EV + '/%s.pyc' % name
        open(sp, 'w', encoding='utf-8').write(src)
        py_compile.compile(sp, pyc, doraise=True)
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
        out.append('EXCEPTION %r' % e)
    open(EV + '/tree_%s.txt' % name, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(name, '->', len(out), 'lines')
