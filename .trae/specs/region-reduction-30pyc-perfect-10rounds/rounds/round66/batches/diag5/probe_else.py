# -*- coding: utf-8 -*-
"""read-only probe: for a function, print try regions + else-detection internals."""
import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('no')

def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out

pyc, name = sys.argv[1], sys.argv[2]
c = [x for x in walk(load_pyc(pyc), []) if x.co_name == name][0]
cfg = build_cfg(c)
gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
an = gen.region_analyzer
regions = an.analyze()
from core.cfg.region_analyzer import TryExceptRegion
def o(b):
    return getattr(b, 'start_offset', None)
for r in regions:
    if not isinstance(r, TryExceptRegion):
        continue
    print('== TryRegion entry@%s try_span=(%s,%s) handlers=%s blocks=%s' % (
        o(r.entry), getattr(r, 'try_offset_start', None), getattr(r, 'try_offset_end', None),
        [o(b) for b in (r.handler_entry_blocks or [])], sorted(o(b) for b in r.blocks)))
    print('   try_blocks=%s' % sorted(o(b) for b in (getattr(r, 'try_blocks', None) or [])))
    print('   handler_blocks=%s' % sorted(o(b) for b in (getattr(r, 'handler_blocks', None) or [])))
    print('   else_blocks=%s orelse=%s' % (sorted(o(b) for b in (getattr(r, 'else_blocks', None) or [])),
                                           sorted(o(b) for b in (getattr(r, 'orelse_blocks', None) or []))))
    print('   except_handlers=%s' % [(h[0], h[1], sorted(o(b) for b in h[2])) for h in (getattr(r, 'except_handlers', None) or [])])
    print('   has_finally=%s finally=%s' % (getattr(r, 'has_finally', None), sorted(o(b) for b in (getattr(r, 'finally_blocks', None) or []))))
    try:
        eb = an._find_try_else_blocks(r)
        print('   _find_try_else_blocks -> %s' % sorted(o(b) for b in eb))
    except Exception as e:
        print('   _find_try_else_blocks EXC %r' % e)
    te = getattr(r, 'try_offset_end', None)
    blk = cfg.get_block_by_offset(te) if te is not None else None
    print('   block@try_offset_end = %s  in_region_blocks=%s w11=%s' % (
        o(blk), blk in r.blocks,
        an._w11_unprotected_else_candidate(r, blk) if blk is not None else None))
    # successors of the try body: what does the last protected block fall through to
    print('   parent=%s children=%s' % (type(getattr(r,'parent',None)).__name__ + '@' + str(o(getattr(getattr(r,'parent',None),'entry',None))), [ '%s@%s'%(type(x).__name__,o(x.entry)) for x in (r.children or [])]))
