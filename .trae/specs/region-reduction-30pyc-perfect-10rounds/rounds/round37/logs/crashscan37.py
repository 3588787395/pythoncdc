# -*- coding: utf-8 -*-
"""Round 37 target-selection ruler: whole-corpus exception probe over a chosen core tree.

Round 36 established that a `-21` "whole block missing" reading, previously catalogued as an
algorithmic family (#41/#43), was really a TypeError swallowed by the per-region fallback at
core/cfg/region_ast_generator.py:1681-1683 -- which degrades the region instead of reporting.
This is that probe, run over the *full* 402-file roster (Round 36's scan only covered 21 of
them), so "who crashes" and "who gets degraded" is measured corpus-wide instead of assumed.

--core=<dir> runs a mirror tree instead of the worktree one (used as the positive control:
the pre-R36-A mirror must reproduce base.pyc's 2x TypeError -- a probe that prints nothing is
broken, not empty).

Read-only: patches the in-process module, calls pycdc.decompile_pyc (returns a string, writes
no file), and never touches a repo path.

usage: python -X utf8 crashscan37.py --list=<roster.txt> --out=<file.txt> [--shard=0 --nshard=3]
                                      [--core=<mirror-root>]
"""
import hashlib
import io
import os
import sys
import time
import traceback

kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
SHARD = int(kw.get('shard', 0))
NSHARD = int(kw.get('nshard', 1))
ROOT = os.path.abspath(kw.get('core', r'F:\Downloads\pythoncdc-main'))
REPO = r'F:\Downloads\pythoncdc-main'
ORIGIN = os.getcwd()          # --list/--out are relative to the caller, not to the core tree
for _k in ('list', 'out'):
    if _k in kw:
        kw[_k] = os.path.abspath(os.path.join(ORIGIN, kw[_k]))
sys.path.insert(0, ROOT)
if ROOT != REPO:
    sys.path.append(REPO)          # vendored packages (bytecode/, scripts/) live in the repo
os.chdir(ROOT)
sys.stdout.reconfigure(encoding='utf-8')

CORE = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
print('core tree %s  sha256[:20] %s  bytes %d'
      % (ROOT, hashlib.sha256(io.open(CORE, 'rb').read()).hexdigest()[:20],
         os.path.getsize(CORE)))

import core.cfg.region_ast_generator as RAG   # noqa: E402
import pycdc                                  # noqa: E402

GEN_REGION = RAG.RegionASTGenerator._generate_region
DEGRADED = RAG.RegionASTGenerator._generate_degraded_statements
CRASHES = []


def _site(exc_tb):
    for fr in reversed(traceback.extract_tb(exc_tb)):
        if os.path.basename(fr.filename) != 'crashscan37.py':
            return '%s:%d' % (os.path.basename(fr.filename), fr.lineno), fr.name
    return '?', '?'


def gen_region(self, region, *a, **k):
    try:
        return GEN_REGION(self, region, *a, **k)
    except Exception:
        exc = sys.exc_info()[1]
        site, fn = _site(sys.exc_info()[2])
        CRASHES.append((type(exc).__name__, str(exc)[:70], site, fn))
        raise


def degraded(self, *a, **k):
    CRASHES.append(('(degradation-arm-entered)', '', 'n/a', '_generate_degraded_statements'))
    return DEGRADED(self, *a, **k)


RAG.RegionASTGenerator._generate_region = gen_region
RAG.RegionASTGenerator._generate_degraded_statements = degraded

paths = [l.strip() for l in io.open(kw['list'], encoding='utf-8') if l.strip()]
mine = [p for i, p in enumerate(paths) if i % NSHARD == SHARD]
out = io.open(kw['out'], 'w', encoding='utf-8', newline='\n')
tot = {}
t_all = time.time()
for p in mine:
    CRASHES.clear()
    t0 = time.time()
    fatal = ''
    try:
        pycdc.decompile_pyc(p)
    except Exception as e:
        fatal = 'FATAL %s: %s' % (type(e).__name__, str(e)[:70])
    dt = time.time() - t0
    agg = {}
    for kind, msg, site, fn in CRASHES:
        key = '%s @ %s in %s%s' % (kind, site, fn, (' | ' + msg) if msg else '')
        agg[key] = agg.get(key, 0) + 1
        tot[key] = tot.get(key, 0) + 1
    rel = p.replace('\\', '/').split('site-packages/')[-1]
    out.write('%s\t%.1f\t%s\t%s\n' % (
        rel, dt, fatal,
        '; '.join('%dx %s' % (v, k) for k, v in sorted(agg.items())) or '-'))
    out.flush()
print('shard %d/%d: %d files in %.0fs -> %s' % (SHARD, NSHARD, len(mine), time.time() - t_all, kw['out']))
print('=== shard totals ===')
for k, v in sorted(tot.items(), key=lambda x: -x[1]):
    print('  %4dx  %s' % (v, k))
