# -*- coding: utf-8 -*-
"""CENSUS_r93 — re-run the P census using the ACTUAL rule predicate
RegionAnalyzer._r2164_duplicated_test_predicate over every loop-condition LoopRegion
in the 402-file corpus. Prints per-file evaluations/fires and the fire lines.
Usage: python -X utf8 census_r93.py"""
import os, sys, types, marshal
MIRROR = 'D:/Temp/r93'
sys.path.insert(0, MIRROR); sys.path.insert(0, MIRROR + '/core')
from core.cfg import build_cfg
import core.cfg.region_analyzer as ra

paths = [l.strip() for l in open('D:/Temp/r93/repro/corpus_paths.txt', encoding='utf-8') if l.strip()]

def objs(root):
    st = [root]
    while st:
        c = st.pop(); yield c
        for k in c.co_consts:
            if isinstance(k, types.CodeType): st.append(k)

def census(co):
    cfg = build_cfg(co); ana = ra.RegionAnalyzer(cfg); regions = ana.analyze()
    ev = fire = 0; det = []
    for r in regions:
        if not isinstance(r, ra.LoopRegion) or r.condition_block is None:
            continue
        ev += 1
        if ana._r2164_duplicated_test_predicate(r):
            fire += 1
            hdr = r.header_block
            ch = ana._detect_duplicated_while_test_chain(r.condition_block, r)
            det.append('cond=@%d hdr=@%d chain=%s' % (
                r.condition_block.start_offset,
                hdr.start_offset if hdr else -1,
                [(b.start_offset, o) for b, o in ch] if ch else None))
    return ev, fire, det

te = tf = 0
for i, p in enumerate(paths):
    if not os.path.isfile(p):
        print('MISSING', p); continue
    try:
        code = marshal.loads(open(p, 'rb').read()[16:])
    except Exception as e:
        print('UNMARSHAL_FAIL', p, e); continue
    fe = ff = 0
    for co in objs(code):
        try:
            ev, fire, det = census(co)
        except Exception as e:
            print('  ANALYZE_FAIL %s %s: %s' % (p, co.co_name, e)); continue
        fe += ev; ff += fire
        for d in det:
            print('FIRE %s :: %s :: %s' % (os.path.basename(p), co.co_name, d))
    te += fe; tf += ff
    if ff:
        print('FILE %s evals=%d fires=%d' % (p, fe, ff))
print('=== DONE files=%d evaluations=%d fires=%d ===' % (len(paths), te, tf))
