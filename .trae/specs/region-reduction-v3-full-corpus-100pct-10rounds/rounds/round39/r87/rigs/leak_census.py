"""Census for the §9h direction: over a list of pyc, count LoopRegions whose break_blocks contain
a block that lies inside a SIBLING loop region's body (ownership leak), plus how many loop regions
share their entry block with another loop region.

Counting rule (stated for reproducibility):
  leak      = one (loop, break_block) pair where break_block is in loop.break_blocks and there
              exists another LoopRegion R2 != loop with break_block in R2.body_blocks and
              loop.entry.start_offset != R2.entry.start_offset (i.e. R2 is a sibling/other loop,
              not the same region);
  shared    = one LoopRegion whose entry BasicBlock is also the entry of a different LoopRegion.
usage: python -X utf8 work/leak_census.py <pathlist.txt>
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

paths = []
for _l in open(sys.argv[1], encoding='utf-8'):
    _r = _l.strip()
    if not _r:
        continue
    if not _r.startswith('site-packages/'):
        _r = 'site-packages/' + _r
    paths.append(_r)
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"

LEAK = 0
SHARED = 0
NARROW = 0
FILES = 0
DETAILS = []
for rel in paths:
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
    if not os.path.isfile(pyc):
        continue
    try:
        mod = load_pyc_file_v2(pyc)
        code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
        if hasattr(code, 'to_python_code'):
            code = code.to_python_code()
    except Exception as e:
        DETAILS.append('LOADFAIL %s %r' % (rel, e))
        continue

    def walk(c):
        yield c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                yield from walk(k)

    FILES += 1
    for co in walk(code):
        try:
            cfg = build_cfg(co)
            regions = RegionAnalyzer(cfg).analyze()
        except Exception:
            continue
        loops = [r for r in regions if isinstance(r, LoopRegion)]
        entries = {}
        for r in loops:
            if r.entry is not None:
                entries.setdefault(r.entry.start_offset, []).append(r)
        for off, rs in entries.items():
            if len(rs) > 1:
                SHARED += 1
                DETAILS.append('SHARED %-58s %s entry=%d loops=%d' % (
                    rel, co.co_name, off, len(rs)))
        byid = {id(r): r for r in loops}
        body_owners = {}
        for r in loops:
            for b in (r.body_blocks or []):
                body_owners.setdefault(b.start_offset, set()).add(id(r))
        for r in loops:
            for b in (r.break_blocks or []):
                owners = body_owners.get(b.start_offset, set())
                if owners and id(r) not in owners:
                    LEAK += 1
                    if r.condition_block is not None:
                        NARROW += 1
                        kinds = []
                        for oid in sorted(owners):
                            o = byid.get(oid)
                            anc = []
                            q = o
                            while q is not None and len(anc) < 8:
                                anc.append((id(q), q.entry.start_offset if q.entry else None))
                                q = getattr(q, 'parent', None)
                            kinds.append('sibling' if id(r) in anc else 'NOT-descendant-of-loop')
                        DETAILS.append('NARROW %-52s %s loop_entry=%s cond=%s break=%d owner_kinds=%s' % (
                            rel, co.co_name, r.entry.start_offset if r.entry else None,
                            r.condition_block.start_offset, b.start_offset, kinds))
                    DETAILS.append('LEAK %-58s %s loop_entry=%s cond=%s break=%d owned_by_other=%s' % (
                        rel, co.co_name, r.entry.start_offset if r.entry else None,
                        r.condition_block.start_offset if r.condition_block else None,
                        b.start_offset, sorted(owners)))
print('files=%d LEAK=%d SHARED=%d NARROW_cond_not_None=%d' % (FILES, LEAK, SHARED, NARROW))
for d in DETAILS[:80]:
    print('  ' + d)
print('details_total=%d' % len(DETAILS))
