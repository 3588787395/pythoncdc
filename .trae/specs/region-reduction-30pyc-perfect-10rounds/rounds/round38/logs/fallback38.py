# -*- coding: utf-8 -*-
"""Round 38 fallback line C: aligned hunks for the clusters the two dispatched agents do NOT own.

Purpose: if both candidates come back NOT-READY the orchestrator needs a third shape already
measured, and the round must not stall. Rows here are the 'one EXTRA jump emitted' trio and the
klinedata return-shape pair, plus the 5 equal-length transpositions.

usage: python -X utf8 fallback38.py
"""
import difflib
import dis
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
M = r'D:/Temp/r38gate/r38m'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

GROUPS = {
 'extra-jump': [('IQCommon/api/klinedata.pyc', '_all_bars_of_cache'),
                ('IQEngine/plugins/plugin_system_log/__init__.pyc', 'trade_logs_control'),
                ('fly/data/quote.pyc', 'check_stock')],
 'klinedata-return': [('IQCommon/api/klinedata.pyc', 'get_history_new'),
                      ('IQCommon/api/klinedata.pyc', 'get_multiminute_his_data')],
 'equal-length-transposition': [
     ('IQCommon/graph.pyc', '_process_task_queue'),
     ('IQCommon/util/fileio_utils.pyc', 'write'),
     ('IQEngine/utils/scheduler.pyc', 'get_checked_time'),
     ('fly/logger.pyc', 'write_logging_thread'),
     ('IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc', 'after_trading_cancel_order')],
}


def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (str(r10._norm_arg(i)), i.opname)


def line(i):
    av = '<code>' if hasattr(i.argval, 'co_code') else i.argrepr
    return '%-4d %-30s %-22r %s%s' % (i.offset, i.opname, av,
                                      '' if i.starts_line is None else 'L%d' % i.starts_line,
                                      (' -> %s' % i.argval) if r10._is_jump(i.opname) else '')


out = io.open(M + '/fallback38.txt', 'w', encoding='utf-8', newline='\n')
for gname, cases in GROUPS.items():
    out.write('\n########## group %s (%d rows)\n' % (gname, len(cases)))
    for rel, name in cases:
        pyc = os.path.join(REPO, 'site-packages', rel.replace('/', os.sep))
        ok = os.path.join(M, 'build_head', rel[:-4].replace('/', '__') + 'OK.py')
        origs = r10._load_map(pyc)
        decs = r10._compile_map(ok)
        cands = [k for k in origs if k.split('.')[-1] == name]
        if len(cands) > 1:
            cands = [k for k in cands if r10.strict_compare(origs[k], decs[k])[2]]
        assert len(cands) == 1, (rel, name, cands)
        key = cands[0]
        o, d = r10.filtered(origs[key]), r10.filtered(decs[key])
        so, sd = [tok(i) for i in o], [tok(i) for i in d]
        out.write('\n=== %s :: %s  orig=%d decomp=%d delta=%+d  (%s)\n'
                  % (rel, name, len(so), len(sd), len(sd) - len(so),
                     r10.strict_compare(origs[key], decs[key])[:2]))
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=so, b=sd, autojunk=False).get_opcodes():
            if tag == 'equal':
                continue
            out.write('--- %s orig[%d:%d] decomp[%d:%d]\n' % (tag, i1, i2, j1, j2))
            for k in range(max(0, i1 - 2), min(len(o), i2 + 2)):
                out.write('    O#%-3d %s%s\n' % (k, line(o[k]), '   <<ORIG-ONLY' if i1 <= k < i2 else ''))
            for k in range(max(0, j1 - 2), min(len(d), j2 + 2)):
                out.write('    D#%-3d %s%s\n' % (k, line(d[k]), '   <<PRODUCT-ONLY' if j1 <= k < j2 else ''))
out.close()
print(io.open(M + '/fallback38.txt', encoding='utf-8').read()[:6000])
print('\n... full file: D:/Temp/r38gate/r38m/fallback38.txt  (%d bytes)'
      % os.path.getsize(M + '/fallback38.txt'))
