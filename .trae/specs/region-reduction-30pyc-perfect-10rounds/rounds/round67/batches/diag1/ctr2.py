# -*- coding: utf-8 -*-
"""diag1 r67: method-call tree of RegionASTGenerator for ONE function's decompile.

Wraps every RegionASTGenerator method that receives a region-like argument and
logs (depth, method, RegionType@entry_offset). Then prints the ancestry chain of
every frame whose watched offsets appear, so we can see WHICH method emits the
join region while still inside the parent's then-branch emission.

usage: python -X utf8 ctr2.py <pyc> <watch_off[,off...]>
"""
import io
import os
import sys

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

WATCH = set()
LOG = []
depth = [0]


def rarg(args, kw):
    for v in list(args) + list(kw.values()):
        e = getattr(v, 'entry', None)
        if e is not None and hasattr(e, 'instructions') and hasattr(v, 'blocks'):
            return v
    return None


def make_wrapper(orig):
    def w(self, *a, **k):
        r = rarg(a, k)
        if r is None:
            return orig(self, *a, **k)
        try:
            eo = r.entry.get_first_instruction().offset
        except Exception:
            eo = None
        LOG.append((depth[0], orig.__name__, type(r).__name__, eo))
        if eo in WATCH:
            cf = sys._getframe(1)
            LOG[-1] = (depth[0], orig.__name__, type(r).__name__, eo,
                       'called from %s:%d in %s' % (os.path.basename(cf.f_code.co_filename),
                                                    cf.f_lineno, cf.f_code.co_name))
            if cf.f_code.co_name == '_process_if_blocks':
                lv = cf.f_locals
                blks = lv.get('blocks')
                cur_r = lv.get('region')
                blk = lv.get('block')
                try:
                    blkoff = blk.get_first_instruction().offset if blk is not None else None
                except Exception:
                    blkoff = getattr(blk, 'start_offset', None)
                owner = self.region_analyzer.get_region_for_block(blk) if blk is not None else None
                try:
                    oentry = owner.entry.get_first_instruction().offset if owner is not None else None
                except Exception:
                    oentry = None
                LOG.append((depth[0], 'CTX', '', '',
                            'block@%s role=%s region=%s@%s owner=%s@%s blocks=%s standalone=%s'
                            % (blkoff, getattr(blk, 'role', None),
                               type(cur_r).__name__ if cur_r is not None else None,
                               (cur_r.entry.get_first_instruction().offset
                                if cur_r is not None and cur_r.entry else None),
                               type(owner).__name__ if owner is not None else None, oentry,
                               [(_b.get_first_instruction().offset
                                 if _b.get_first_instruction() else None) for _b in (blks or [])],
                               cur_r is None)))
        depth[0] += 1
        try:
            return orig(self, *a, **k)
        finally:
            depth[0] -= 1
    return w


def main(pyc, watch):
    global WATCH
    WATCH = set(int(x) for x in watch.split(',') if x.strip())
    import pycdc
    import core.cfg.region_ast_generator as G
    n = 0
    for nm in dir(G.RegionASTGenerator):
        if nm.startswith('__'):
            continue
        f = getattr(G.RegionASTGenerator, nm)
        if callable(f):
            setattr(G.RegionASTGenerator, nm, make_wrapper(f))
            n += 1
    text = pycdc.decompile_pyc(pyc)
    print('wrapped %d methods; log frames=%d' % (n, len(LOG)))
    print('== FULL REGION-ARG CALL TREE ==')
    for ent in LOG:
        d, nm, rn, eo = ent[0], ent[1], ent[2], ent[3]
        star = ('  <<< ' + ent[4]) if len(ent) > 4 else ''
        print('%s%-46s %s@%s%s' % ('  ' * d, nm, rn, eo, star))
    io.open('logs/ast_v3.py', 'w', encoding='utf-8').write(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
