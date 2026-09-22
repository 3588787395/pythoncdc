# -*- coding: utf-8 -*-
"""Orchestrator-side re-verification of line B's premise against the LANDED bytes.

Round 39/40 handover quoted `one_prod_to_dataframe` as orig=485 decomp=484 with the lost
instruction `@1862 JUMP_BACKWARD` in `B@1818 succs=[742]`. Re-measure that claim on the bytes
that shipped in Round 40 (the official per-function row now reads 484/483 — a different ruler,
so quote the strict one directly) and print the exact deletion plus its neighbourhood.
"""
import difflib
import dis
import importlib.util
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def seq(code):
    return [(i.offset, i.opname, i.argval if not isinstance(i.argval, (str, bytes)) else i.argrepr)
            for i in dis.get_instructions(code)]


PAIRS = [
    ('fly/data/quote.pyc',
     ['<module>.Quote.one_prod_to_dataframe']),
    ('IQData/plugins/plugin_system_realquote/real_quote.pyc',
     ['<module>.RealQuoteAPI.one_prod_to_dataframe', '<module>.one_prod_to_dataframe']),
]

for rel, want in PAIRS:
    pyc = REPO + '/site-packages/' + rel
    py = pyc[:-4] + 'OK.py'
    o = r10._load_map(pyc)
    d = r10._compile_map(py)
    print('=' * 78)
    print(rel)
    names = [n for n in o if 'one_prod_to_dataframe' in n]
    for name in names:
        kind, msg, defect = r10.strict_compare(o[name], d.get(name))
        print('  %-52s %-14s defect=%s' % (name, msg, defect))
        a = seq(o[name])
        b = seq(d[name])
        sa = ['%d %s %s' % x for x in a]
        sb = ['%d %s %s' % x for x in b]
        sm = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
        ops = [t for t in sm.get_opcodes() if t[0] != 'equal']
        print('    instr sequences: orig=%d decomp=%d  differing blocks=%d' % (len(sa), len(sb), len(ops))
              )
        for tag, i1, i2, j1, j2 in ops[:4]:
            print('    %-8s orig[%d:%d]=%s  decomp[%d:%d]=%s'
                  % (tag, i1, i2, sa[i1:i2], j1, j2, sb[j1:j2]))
            lo = max(0, i1 - 3)
            print('      context before: %s' % (sa[lo:i1],))
            hi = min(len(sa), i2 + 3)
            print('      context after : %s' % (sa[hi:hi + 3],))
