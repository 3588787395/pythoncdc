# -*- coding: utf-8 -*-
"""walk_census_r110.py -- r110a POSITIONAL CENSUS of the body-sequence walks (call level).

Question: after the try-body emitter frees @7972..@8588, does any LATER walk revisit them,
and if not which walk owns the position it should have been printed at?

Runtime monkeypatch ONLY -- every hook calls the untouched original and only appends records.
Inertness proven by: (a) re-hashing core/cfg/*.py after the run, (b) product bytes with the
probe installed == un-probed baseline out/base_r110.py (20190 / 192ba0f09e81bbd7).

usage: python -X utf8 walk_census_r110.py [--trace]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)
MIRROR = 'D:/Temp/r110'
sys.path.insert(0, MIRROR)
os.chdir(MIRROR)

PYC = ('D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/'
       'plugins/plugin_system_event_source/realtime_event_source.pyc')

TARGETS = [7972, 7980, 8166, 8170, 8186, 8256, 8282, 8294, 8306, 8350, 8354, 8400, 8450,
           8544, 8588]
TSET = set(TARGETS)

CALLS = []
SEQ = [0]
STACK = []
STATS = {'clock_calls': 0, 'with_targets': 0, 'name_probe': None}


def off(x):
    try:
        return x.start_offset
    except AttributeError:
        return x


def offs(lst):
    out = []
    for b in (lst or ()):
        out.append(off(b) if hasattr(b, 'start_offset') else None)
    return out


import core.cfg.region_ast_generator as RAG      # noqa: E402
GENFILE = os.path.abspath(RAG.__file__).replace('\\', '/')


def is_genfile(fn):
    return (fn or '').replace('\\', '/').endswith('core/cfg/region_ast_generator.py')
G = RAG.RegionASTGenerator


def is_clock(self):
    try:
        cfg = getattr(self, 'cfg', None)
        code = getattr(cfg, 'code', None)
        nm = getattr(code, 'co_name', None) or getattr(cfg, 'name', '')
        if STATS['name_probe'] is None:
            STATS['name_probe'] = (type(cfg).__name__, getattr(cfg, 'name', None), nm,
                                   getattr(code, 'co_qualname', None))
        if nm == 'clock_worker':
            return True
        return 'clock_worker' in (getattr(code, 'co_qualname', '') or '')
    except Exception:
        return False


def gb_offs(self):
    """start_offsets currently marked in generated_blocks"""
    s = set()
    for b in self.generated_blocks:
        o = getattr(b, 'start_offset', None)
        if o is not None:
            s.add(o)
    return s


def reg_id(r):
    if r is None:
        return None
    return '%s@%s' % (type(r).__name__, off(getattr(r, 'entry', None)))


WATCH = ['_process_if_blocks', '_if_generate_branch_stmts', '_if_generate_then_branch',
         '_generate_try_body', '_loop_generate_body', '_if_generate_normal',
         '_generate_region', '_generate_block_statements', '_generate_loop', '_generate_try',
         '_generate_if', '_loop_postprocess']

ORIG = {}


def install(name):
    orig = getattr(G, name)
    ORIG[name] = orig

    def wrapper(self, *a, **kw):
        myseq = SEQ[0]
        SEQ[0] += 1
        clock = is_clock(self)
        rec = None
        if clock:
            STATS['clock_calls'] += 1
            STATS.setdefault('per_meth', {})
            pm = STATS['per_meth']
            pm[name] = pm.get(name, 0) + 1
            tg, info = set(), {}
            for i, x in enumerate(a):
                if isinstance(x, (list, tuple)) and x:
                    ol = offs(x)
                    hits = [o for o in ol if o in TSET]
                    if hits:
                        info['arg%d' % i] = {'n': len(ol), 'order': ol,
                                             'idx': dict((o, ol.index(o)) for o in hits)}
                        tg.update(hits)
            r = None
            for x in a:
                if hasattr(x, 'entry') or hasattr(x, 'blocks'):
                    r = x
                    break
            if r is not None:
                if name == '_generate_block_statements':
                    tg.add(off(r))
                    info['blk'] = off(r)
                else:
                    rb = offs(getattr(r, 'blocks', None))
                    idx = dict((o, rb.index(o)) for o in rb if o in TSET)
                    if idx:
                        info['region_blocks'] = {'n': len(rb), 'hits': sorted(idx), 'idx': idx}
                        tg.update(idx)
                    bb = offs(getattr(r, 'body_blocks', None))
                    bidx = dict((o, bb.index(o)) for o in bb if o in TSET)
                    if bidx:
                        info['body_blocks'] = {'n': len(bb), 'hits': sorted(bidx), 'idx': bidx}
                        tg.update(bidx)
            if tg:
                STATS['with_targets'] += 1
                before = gb_offs(self)
                rec = {'seq': myseq, 'meth': name, 'reg': reg_id(r),
                       'branch': (kw.get('branch') if len(a) > 2 else kw.get('branch'))
                       or (offs(a[2]) if False else None),
                       'targets': sorted(tg), 'info': info,
                       'depth': len(STACK), 'parent_stack': [STACK[-6:]] and list(STACK),
                       'gb_before': dict((o, o in before) for o in sorted(tg)),
                       'name': name}
                CALLS.append(rec)
            else:
                before = None
        STACK.append(myseq)
        try:
            res = orig(self, *a, **kw)
        finally:
            STACK.pop()
        if rec is not None:
            after = gb_offs(self)
            rec['gb_after'] = dict((o, o in after) for o in rec['targets'])
            if isinstance(res, list):
                rec['nret'] = len(res)
            elif res is None:
                rec['nret'] = 0
            else:
                rec['nret'] = 1
            rec['branch'] = kw.get('branch')
        return res
    wrapper.__name__ = 'w_' + name
    setattr(G, name, wrapper)


for _n in WATCH:
    if hasattr(G, _n):
        install(_n)

# ---- --unclaim <entry>: surgical, in-process un-claim of the 14 targets right after
# ---- the IfRegion@<entry> emission returns (emulates neutering line 22505 for them only)
UNCLAIM = None
for i, a in enumerate(sys.argv):
    if a == '--unclaim':
        UNCLAIM = int(sys.argv[i + 1])
UNCLAIMED = []
if UNCLAIM is not None:
    _orig_region2 = ORIG['_generate_region']

    def _unclaiming_region(self, region, *a2, **k2):
        res = _orig_region2(self, region, *a2, **k2)
        if is_clock(self) and getattr(getattr(region, 'entry', None), 'start_offset',
                                      None) == UNCLAIM:
            g = self.generated_blocks
            gone = []
            for b in list(getattr(region, 'else_blocks', None) or []):
                if getattr(b, 'start_offset', None) in TSET and b in g:
                    g.discard(b)
                    gone.append(b.start_offset)
            if gone:
                UNCLAIMED.append({'seq': SEQ[0], 'reg': reg_id(region), 'unclaimed': sorted(gone)})
        return res
    G._generate_region = _unclaiming_region
    ORIG['_generate_region'] = _unclaiming_region

# ---------------- optional per-line tracer ----------------
TRACE_ON = '--trace' in sys.argv
FRAMES = {}
DONE_FRAMES = []
CLAIMS = []
CLAIM_LINES = {22501: 'then_claim', 22505: 'else_claim', 22530: 'then_claim_B',
               22534: 'else_claim_B', 22539: 'inner_else_claim'}
FLIP_ON = '--flip' in sys.argv
CLAIM_ON = '--claims' in sys.argv
if TRACE_ON:
    TRaced_NAMES = ('_process_if_blocks', '_loop_generate_body', '_generate_try_body',
                    '_if_generate_then_branch')
    if FLIP_ON:
        TRaced_NAMES = ('_process_if_blocks', '_loop_generate_body', '_generate_try_body',
                        '_if_generate_normal', '_if_generate_elif_chain',
                        '_if_generate_then_branch')
    if CLAIM_ON:
        TRaced_NAMES = ('_if_generate_normal',)

    def gtrace(frame, event, arg):
        co = frame.f_code
        if not is_genfile(co.co_filename) or co.co_name not in TRaced_NAMES or event != 'call':
            return None
        fl = frame.f_locals
        self = fl.get('self')
        if self is None or not is_clock(self):
            return None
        tgt = set()
        blk = fl.get('blocks')
        if blk:
            tgt |= set(o for o in offs(blk) if o in TSET)
        r = fl.get('region')
        if r is not None:
            tgt |= set(o for o in offs(getattr(r, 'blocks', None)) if o in TSET)
            tgt |= set(o for o in offs(getattr(r, 'body_blocks', None)) if o in TSET)
        if CLAIM_ON:
            if not tgt:
                return None
        elif not tgt:
            return None
        # target BLOCK objects for membership probing (identity, like the real set)
        objs = {}
        for cand in list(blk or []) + (list(getattr(r, 'blocks', None) or [])
                                      + list(getattr(r, 'body_blocks', None) or [])
                                      + list(getattr(r, 'then_blocks', None) or [])
                                      + list(getattr(r, 'else_blocks', None) or [])):
            o = getattr(cand, 'start_offset', None)
            if o in TSET and o not in objs:
                objs[o] = cand
        gb = self.generated_blocks
        state = dict((o, objs[o] in gb) for o in objs)
        st = {'seq': STACK[-1] if STACK else -1, 'fn': co.co_name,
              'reg': reg_id(r), 'nblk_arg': len(blk) if blk else None,
              'log': [], 'flips': [], 'gb_at_entry': dict(state)}
        FRAMES[id(frame)] = st

        def ltrace(fr, ev, ar):
            cur = FRAMES.get(id(fr))
            if cur is None:
                return None
            if ev == 'line':
                b = fr.f_locals.get('block')
                prev = cur['log'][-1][0] if cur['log'] else None
                cur['log'].append((fr.f_lineno, off(b) if b is not None else None))
                if CLAIM_ON and fr.f_lineno in CLAIM_LINES:
                    fl2 = fr.f_locals
                    rb = fl2.get('b')
                    rr = fl2.get('region')
                    CLAIMS.append({
                        'seq': cur['seq'], 'line': fr.f_lineno,
                        'site': CLAIM_LINES[fr.f_lineno],
                        'reg': reg_id(rr), 'added': off(rb),
                        'in_targets': off(rb) in TSET,
                        'then_n': len(offs(getattr(rr, 'then_blocks', None) or [])),
                        'else_n': len(offs(getattr(rr, 'else_blocks', None) or [])),
                        'then_hits': [o for o in offs(getattr(rr, 'then_blocks', None) or [])
                                      if o in TSET],
                        'else_hits': [o for o in offs(getattr(rr, 'else_blocks', None) or [])
                                      if o in TSET],
                        'efe_hits': [o for o in offs(getattr(rr, 'elif_final_else', None) or [])
                                     if o in TSET],
                        'efe_n': len(offs(getattr(rr, 'elif_final_else', None) or [])),
                        'gb_now': (rb in getattr(self, 'generated_blocks', set()))})
                if FLIP_ON:
                    g = getattr(self, 'generated_blocks', None)
                    for o, bo in objs.items():
                        now = bo in g
                        if now != cur['gb_at_entry'].get(o):
                            # 'executed' = the line that actually ran the add/discard
                            # ('seen' = the next line, where the change was observed)
                            cur['flips'].append((prev, fr.f_lineno, o,
                                                 'IN' if now else 'OUT'))
                            cur['gb_at_entry'][o] = now
                return ltrace
            if ev in ('return', 'exception'):
                FRAMES.pop(id(fr), None)
                cur['ev'] = ev
                DONE_FRAMES.append(cur)
            return None
        return ltrace

    sys.settrace(gtrace)

from pycdc import decompile_pyc      # noqa: E402

_prod = decompile_pyc(PYC)
open(MIRROR + ('/out/probe_product%s.py' % ('_unclaim' if UNCLAIM else '')), 'w',
     encoding='utf-8', newline='').write(_prod)
print('unclaim events:', UNCLAIMED)

if TRACE_ON:
    sys.settrace(None)
    json.dump(DONE_FRAMES, open(MIRROR + '/logs/lines_r110.json', 'w'))
    print('traced frames:', len(DONE_FRAMES), 'line events:',
          sum(len(f['log']) for f in DONE_FRAMES))
if CLAIM_ON:
    json.dump(CLAIMS, open(MIRROR + '/logs/claims_r110.json', 'w'))
    print('claim-site events recorded:', len(CLAIMS))

json.dump({'unclaimed_events': UNCLAIMED, 'calls': CALLS, 'stats': STATS,
           'targets': TARGETS},
          open(MIRROR + '/logs/census_r110%s.json' % (
              ('_traced' if TRACE_ON else '') + ('_unclaim' if UNCLAIM else '')), 'w'))
print('STATS', STATS)
print('calls recorded with targets:', len(CALLS))
byt = {}
for c in CALLS:
    byt.setdefault(c['meth'], []).append(c)
print('--- calls containing targets, by method ---')
for m, cs in sorted(byt.items()):
    print('  %-30s %3d' % (m, len(cs)))
