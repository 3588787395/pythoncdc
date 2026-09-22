# -*- coding: utf-8 -*-
"""PROBE 7: corpus exposure for the swallowed `_fold_break_to_return` crash.

Runs the LANDED core over an explicit list of pyc files and reports, per file,
every exception that the per-region fallback at region_ast_generator.py:1683
swallowed, with the raising file:line.  Read-only; no repo file is touched.
"""
import io
import os
import sys
import time
import traceback

REPO = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

import core.cfg.region_ast_generator as RAG   # noqa: E402
import pycdc                                  # noqa: E402

GEN_REGION = RAG.RegionASTGenerator._generate_region
CRASHES = []


def gen_region(self, region, *a, **k):
    try:
        return GEN_REGION(self, region, *a, **k)
    except Exception as e:
        tb = sys.exc_info()[2]
        frames = traceback.extract_tb(tb)
        site = frames[-1]
        fn = frames[-1].name
        CRASHES.append((type(e).__name__, str(e)[:60], '%s:%d' % (
            os.path.basename(site.filename), site.lineno), fn))
        raise
RAG.RegionASTGenerator._generate_region = gen_region

paths = [l.strip() for l in io.open(sys.argv[1], encoding='utf-8') if l.strip()]
print('%-62s %-6s %s' % ('file', 'secs', 'swallowed exceptions'))
tot = {}
for p in paths:
    CRASHES.clear()
    t0 = time.time()
    try:
        pycdc.decompile_pyc(p)
    except Exception as e:
        print('  !! %s failed: %s: %s' % (p, type(e).__name__, e))
    dt = time.time() - t0
    rel = p.replace('\\', '/').split('site-packages/')[-1]
    agg = {}
    for kind, msg, site, fn in CRASHES:
        key = '%s @ %s in %s' % (kind, site, fn)
        agg[key] = agg.get(key, 0) + 1
        tot[key] = tot.get(key, 0) + 1
    print('%-62s %5.1f %s' % (rel, dt, '; '.join('%dx %s' % (v, k) for k, v in sorted(agg.items())) or '-'))
print()
print('=== corpus-wide totals ===')
for k, v in sorted(tot.items(), key=lambda x: -x[1]):
    print('  %4dx  %s' % (v, k))
