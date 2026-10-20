# -*- coding: utf-8 -*-
"""R5 B122：dump 嵌套 match 区域结构（abort after N calls）+ CFG 块表。

用法: python -X utf8 _r5_b122_dump.py <pyc> <out.txt> [max_calls=4]
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
pyc, out_path = sys.argv[1], sys.argv[2]
max_calls = int(sys.argv[3]) if len(sys.argv) > 3 else 4

out = open(out_path, 'w', encoding='utf-8')


def log(msg):
    out.write(msg + '\n')
    out.flush()


sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg import region_analyzer as RA  # noqa: E402

orig_id = RA.RegionAnalyzer._identify_nested_match_regions
state = {'calls': 0, 'cached_cfg': False}


def off(b):
    return getattr(b, 'start_offset', None)


def dumpset(bs):
    return sorted(off(b) for b in (bs or []))


def dump_region(tag, r):
    log('%s REG subj=%s case_blocks=%s merge=%s' % (
        tag, off(r.subject_block), [off(b) for b in r.case_blocks], off(r.merge_block)))
    for i, body in enumerate(r.case_bodies or []):
        log('    body[%d]=%s' % (i, [off(b) for b in body]))
    log('    blocks=%s entry=%s' % (dumpset(r.blocks), off(r.entry)))


def wrap_id(self, parent_regions, existing_match_regions):
    state['calls'] += 1
    c = state['calls']
    log('=== id-call=%d parents=%d existing=%d ===' % (
        c, len(parent_regions or []), len(existing_match_regions or [])))
    for p in (parent_regions or []):
        log('  parent: %s subj=%s blocks=%s' % (
            type(p).__name__, off(getattr(p, 'subject_block', None)),
            dumpset(p.blocks)))
        if isinstance(p, RA.MatchRegion):
            for i, body in enumerate(p.case_bodies or []):
                log('    p.body[%d]=%s' % (i, [off(b) for b in body]))
    if c > max_calls:
        raise RuntimeError('ABORT after %d calls' % max_calls)
    r = orig_id(self, parent_regions, existing_match_regions)
    for rr in r:
        dump_region('  new', rr)
    # CFG dump (once)
    if not state['cached_cfg']:
        state['cached_cfg'] = True
        log('--- CFG blocks (in order) ---')
        for b in self.cfg.get_blocks_in_order():
            inss = []
            for ins in b.instructions:
                inss.append('%s%s' % (
                    ins.opname,
                    ('(%r)' % (ins.argval,)) if getattr(ins, 'argval', None) is not None else ''))
            log('  [%s] %s | succ=%s' % (off(b), '; '.join(inss[:10]), dumpset(b.successors)))
    return r


RA.RegionAnalyzer._identify_nested_match_regions = wrap_id

sys.argv = ['pycdc.py', pyc, '-o', os.path.join(HERE, '_r5_b122_dump_ok.py')]
try:
    runpy.run_path(os.path.join(ROOT, 'pycdc.py'), run_name='__main__')
except SystemExit as e:
    log('SystemExit %s' % e)
except Exception as e:
    log('EXC %r' % e)
finally:
    log('calls=%d' % state['calls'])
    out.close()
