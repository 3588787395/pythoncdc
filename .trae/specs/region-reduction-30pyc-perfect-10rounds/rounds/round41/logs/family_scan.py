# -*- coding: utf-8 -*-
"""Orchestrator-side family scan: which of the 15 "+1 instruction" functions show a
mid-arm unconditional back edge to the enclosing loop header inside an if-region whose else
arm is empty and whose merge_block is set.

Analyzer only — no codegen, no decompilation, no writes into the repo.
Purpose: decide whether one predicate can plausibly pay for several functions this round.
"""
import importlib.util
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)

_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

from core.cfg.cfg_builder import build_cfg           # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

JUMPS = ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')


def soff(b):
    return getattr(b, 'start_offset', None) if b is not None else None


def scan(code, label):
    cfg = build_cfg(code)
    ra = RegionAnalyzer(cfg)
    try:
        ra.analyze()
    except Exception as e:
        print('  %-46s ANALYZER-ERR %s' % (label, type(e).__name__))
        return
    hits = []
    for r in ra.regions:
        then = getattr(r, 'then_blocks', None)
        if not then or getattr(r, 'merge_block', None) is None:
            continue
        if getattr(r, 'else_blocks', None):
            continue
        rblocks = set(getattr(r, 'blocks', None) or [])
        # nearest enclosing loop region
        hdrs = []
        for q in ra.regions:
            if q is r or 'LOOP' not in str(getattr(q, 'region_type', '')).upper():
                continue
            qb = set(getattr(q, 'blocks', None) or [])
            h = getattr(q, 'header_block', None)
            if rblocks and rblocks <= qb and h is not None:
                hdrs.append((soff(h), h, q))
        if not hdrs:
            continue
        hdrs.sort(key=lambda t: len(t[2].blocks or []))   # innermost enclosing loop first
        # a `continue` targets the innermost loop, but the region may sit in a chain of
        # enclosing loops, so test every header from innermost outward
        tset = set(then)
        for b in tset:
            succs = set(b.successors or ())
            if succs & tset:
                continue                       # not a tail within the arm
            last = b.get_last_instruction()
            if last is None or last.opname not in JUMPS:
                continue
            tgt = cfg.get_block_by_offset(last.argval)
            for h_off, hdr, loop in hdrs:
                if tgt is not hdr:
                    continue
                mid = any((c is not b) and (b in set(c.successors or ()))
                          for c in (rblocks - {b}))
                hits.append((soff(b), last.opname, h_off, soff(r.merge_block),
                             soff(getattr(loop, 'back_edge_block', None)),
                             'MID-ARM' if mid else 'tail',
                             'merge==back_edge' if soff(r.merge_block) == soff(
                                 getattr(loop, 'back_edge_block', None)) else 'merge!=back_edge'))
                break
    if hits:
        print('  %-46s arm->enclosing-loop-header jumps: %d  (mid-arm=%d, merge!=back_edge=%d)'
              % (label, len(hits),
                 sum(1 for h in hits if h[5] == 'MID-ARM'),
                 sum(1 for h in hits if h[6] == 'merge!=back_edge')))
        for h in hits[:4]:
            print('        blk@%-5s %s -> hdr@%-5s merge@%-5s back_edge@%-5s %s %s' % h)
    else:
        print('  %-46s no such shape' % label)


TARGETS = [
    ('IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc',
     ['_process_cancel_order', 'etf_basket_order', 'get_all_orders', 'ipo_stocks_order']),
    ('IQData/plugins/plugin_system_realquote/real_quote.pyc',
     ['get_cache_l2_data_by_one', 'get_tick_direction', 'one_prod_to_dataframe']),
    ('fly/data/quote.pyc', ['check_frequency', 'one_prod_to_dataframe']),
    ('fly/data/quote_handler.pyc', ['get_kline_binary', 'is_delisting_stock_local']),
    ('fly/simtradding/flyAccount.pyc', ['init_connection']),
    ('IQCommon/api/klinedata.pyc',
     ['get_all_real_daily_kline', 'get_history_new', 'get_multiminute_his_data']),
]

for rel, subs in TARGETS:
    pyc = REPO + '/site-packages/' + rel
    print('=' * 78)
    print(rel)
    m = r10._load_map(pyc)
    for name, code in sorted(m.items()):
        if any(('%s.' % s) in name or name.endswith('.' + s) or name == '<module>.' + s
               for s in subs):
            try:
                scan(code, name[-46:])
            except Exception as e:
                print('  %-46s SCAN-ERR %s %s' % (name[-46:], type(e).__name__, str(e)[:60]))
