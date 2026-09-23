# -*- coding: utf-8 -*-
"""Round 53 census: how many REAL code objects carry the "chain-in-boolop" signature?

Signature (same-level, observable on the finished region list):
  an IfRegion with non-empty `chained_compare_blocks` whose `then_blocks[0]` is the
  `condition_block` (== entry) of ANOTHER region R, and whose `merge_block` lies inside R.blocks.
  Reading: the "then arm" is not a statement body at all, it is the next test of an enclosing
  boolean expression, and the "merge" is that test's body => the chained compare is an OPERAND
  of a larger boolop and must not be reduced as a statement-level `if`.

Also reports, for each hit, the sibling shape where `merge_block in then_blocks` (degenerate).

usage: python -X utf8 census53.py <list-file> <out-json>
list-file: pyc paths (absolute), one per line.
"""
import importlib.util
import io
import json
import marshal
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BASE = REPO
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, BASE)
from core.cfg import build_cfg, CFGRegionAnalyzer  # noqa: E402
from core.cfg.region_analyzer import IfRegion, LoopRegion  # noqa: E402

LISTF, OUT = sys.argv[1], sys.argv[2]
paths = [l.strip() for l in io.open(LISTF, encoding='utf-8') if l.strip()]


def walk(co, prefix, out):
    out.append((prefix + '.' + co.co_name if prefix else co.co_name, co))
    for c in co.co_consts:
        if type(c).__name__ == 'code':
            walk(c, (prefix + '.' if prefix else '') + co.co_name, out)


hits, scanned = [], 0
for p in paths:
    p = p.replace('\\', '/')
    full = p if os.path.isabs(p) else REPO + '/site-packages/' + p
    if not os.path.exists(full):
        continue
    try:
        with io.open(full, 'rb') as f:
            f.read(16)
            top = marshal.load(f)
    except Exception as e:
        print('SKIP %s %s' % (p, e))
        continue
    cos = []
    walk(top, '', cos)
    rel = p.split('/site-packages/')[-1]
    for name, co in cos:
        if not co.co_code:
            continue
        scanned += 1
        try:
            cfg = build_cfg(co)
            an = CFGRegionAnalyzer(cfg)
            an.analyze()
            rgs = list(an.regions.values()) if isinstance(an.regions, dict) else list(an.regions)
        except Exception:
            continue
        for r in rgs:
            if not isinstance(r, IfRegion) or not getattr(r, 'chained_compare_blocks', None):
                continue
            th = (r.then_blocks or [None])[0]
            if th is None:
                continue
            own = an.block_to_region.get(th)
            degenerate = r.merge_block is th or (r.merge_block in (r.then_blocks or []))
            cond_is_th = (own is not None and own is not r
                           and getattr(own, 'condition_block', None) is th
                           and getattr(own, 'entry', None) is th)
            merge_in_own = (r.merge_block is not None and own is not None
                            and r.merge_block in set(own.blocks or []))
            if cond_is_th and merge_in_own:
                hits.append({'file': rel, 'fn': name, 'kind': 'chain_operand_of_boolop',
                             'entry': r.entry.start_offset, 'then': th.start_offset,
                             'merge': r.merge_block.start_offset,
                             'own_entry': own.entry.start_offset,
                             'own_type': str(getattr(own, 'region_type', '?')),
                             'else': [b.start_offset for b in (r.then_blocks or [])],
                             'degenerate_merge_in_then': degenerate})
print('scanned code objects: %d over %d files ; hits: %d' % (scanned, len(paths), len(hits)))
seen = set()
for h in hits:
    print('%-62s %-46s %s' % (h['file'][-62:], h['fn'][-46:],
                              'entry=%s then=%s own=%s(%s) merge=%s'
                              % (h['entry'], h['then'], h['own_entry'], h['own_type'], h['merge'])))
    seen.add(h['file'])
print('distinct files: %d' % len(seen))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(hits, ensure_ascii=False, indent=1))
