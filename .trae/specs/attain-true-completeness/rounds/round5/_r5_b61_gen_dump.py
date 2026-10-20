# -*- coding: utf-8 -*-
"""R5 B61 generator-side dump: patch _generate_match to log per-case emission
state (patterns/guards/bodies/body_start_indices), all regions, and
block_to_region ownership for the target function.

用法: python -X utf8 _r5_b61_gen_dump.py <pyc> <func_name> <out_txt>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

pyc, want_fn, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
out = open(out_path, 'w', encoding='utf-8')


def log(m):
    out.write(m + '\n')
    out.flush()


def offs(bs):
    return [getattr(b, 'start_offset', None) for b in (bs or [])]


from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

_orig_gm = RegionASTGenerator._generate_match


def patched_gm(self, region):
    co = getattr(self.cfg, 'code', None)
    name = getattr(co, 'co_name', '?')
    if name == want_fn:
        log('=== _generate_match %s ===' % name)
        log('entry=%s merge=%s' % (offs([region.entry])[0],
                                   offs([region.merge_block])[0] if region.merge_block else None))
        log('case_blocks=%s' % offs(region.case_blocks))
        log('case_body_start_indices=%r' % (sorted(region.case_body_start_indices.items()) if hasattr(region, 'case_body_start_indices') else None,))
        for i in range(len(region.case_blocks)):
            pat = region.case_patterns[i] if i < len(region.case_patterns) else None
            grd = region.case_guards[i] if hasattr(region, 'case_guards') and i < len(getattr(region, 'case_guards', [])) else None
            bod = region.case_bodies[i] if i < len(region.case_bodies) else []
            log('case[%d] blocks=%s pattern=%r' % (i, offs([region.case_blocks[i]]), pat))
            log('   guard=%r' % (grd,))
            log('   body=%s' % offs(bod))
            for b in bod:
                log('   --blk@%s--' % b.start_offset)
                for ins in b.instructions:
                    log('      %4d %s %r' % (ins.offset, ins.opname, ins.argval))
        log('--- all regions (entry-in-MR-blocks or covering MR blocks) ---')
        mrb = set(offs(region.blocks))
        for r in self.region_analyzer.regions:
            re_ = getattr(r, 'entry', None)
            rb = set(offs(getattr(r, 'blocks', None) or []))
            if (re_ is not None and re_.start_offset in mrb) or (rb & mrb):
                log('REGION %s entry=%s blocks=%s' % (
                    type(r).__name__, offs([r.entry])[0] if re_ is not None else None,
                    sorted(rb)))
                cond = getattr(r, 'condition_block', None)
                msg = getattr(r, 'message_block', None)
                if cond is not None or msg is not None:
                    log('   cond=%s msg=%s' % (
                        cond.start_offset if cond is not None else None,
                        msg.start_offset if msg is not None else None))
        log('--- block_to_region (MR blocks) ---')
        b2r = getattr(self.region_analyzer, 'block_to_region', {}) or {}
        for boff in sorted(mrb):
            blk = self.cfg.get_block_by_offset(boff)
            if blk is not None and blk in b2r:
                log('blk@%s -> %s' % (boff, type(b2r[blk]).__name__))
        log('--- pattern store names / body start (case bodies) ---')
        for i in range(len(region.case_blocks)):
            pat = region.case_patterns[i] if i < len(region.case_patterns) else None
            names = set()
            try:
                self._collect_pattern_store_names(pat, names)
            except Exception as e:
                names = {'<err %r>' % (e,)}
            log('case[%d] store_names=%r' % (i, names))
            bod = region.case_bodies[i] if i < len(region.case_bodies) else []
            for b in bod:
                try:
                    cs = self._compute_body_block_start(b, set(names)) if names else -1
                except Exception as e:
                    cs = '<err %r>' % (e,)
                log('   blk@%s computed_start=%r' % (b.start_offset, cs))
    return _orig_gm(self, region)


RegionASTGenerator._generate_match = patched_gm

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(pyc)
log('=== DECOMPILED ===')
log(src)
out.close()
print('written', out_path)
