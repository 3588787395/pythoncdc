# -*- coding: utf-8 -*-
"""R35 probe #7: how many corpus products carry a *handler-tail* `return None`, and how many
of those sit at the end of a terminal chain (nothing follows the enclosing try statement in
any enclosing scope up to the function's own end)?

That terminal-chain subset is the candidate R35-B's actual scope.  Stage 1 (default) only
parses and counts -- no compilation, so it is cheap enough to run over all 402 products.
Stage 2 (--measure) re-measures each counted site with the official ruler after deleting
exactly that statement, and reports IMPROVED / REGRESSED / SAME per function.

usage: python -X utf8 probe7_handler_tail.py [--measure] [--nshard=N --shard=I]
"""
import ast
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

MEASURE = '--measure' in sys.argv
opts = dict(x[2:].split('=', 1) for x in sys.argv if x.startswith('--') and '=' in x)
NS = int(opts.get('nshard', 1))
SH = int(opts.get('shard', 0))

if MEASURE:
    _bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
    pbv = importlib.util.module_from_spec(_bv)
    _bv.loader.exec_module(pbv)


def product_of(pyc):
    d, f = os.path.split(pyc)
    return os.path.join(d, f[:-4] + 'OK.py')


def terminal_chain(start, parents):
    """Is the handler's fall-out path the *function's own end*?

    Walk up from the except clause: at every level the statement we came from must be the
    last statement of the block we are in, no `finally` may be pending, and the chain must
    not pass through a loop / with / match (there the exit is not the function end).
    Reaching a function body (or the module) means nothing follows it.
    """
    cur = start
    while True:
        p = parents.get(cur)
        if p is None or isinstance(p, FN_NODES):
            return True
        if isinstance(p, (ast.For, ast.AsyncFor, ast.While, ast.TryStar, ast.With, ast.AsyncWith)):
            return False
        if type(p).__name__ in ('Match', 'ExceptHandlerMatch'):
            return False
        if isinstance(p, ast.ExceptHandler):
            if not p.body or p.body[-1] is not cur:
                return False
            cur = p
            continue
        if isinstance(p, (ast.If, ast.Try)):
            if isinstance(p, ast.Try) and p.finalbody:
                return False
            seq = None
            for attr in ('body', 'handlers', 'orelse'):
                v = getattr(p, attr, None)
                if isinstance(v, list) and any(x is cur for x in v):
                    seq = attr
                    break
            if seq is None:
                return False
            if seq in ('orelse',):
                return False
            if getattr(p, seq)[-1] is not cur:
                return False
            cur = p
            continue
        return False



FN_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
MODULES = ast.Module


def scan(path):
    txt = io.open(path, encoding='utf-8-sig').read().replace('\r\n', '\n')
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        return None
    lines = txt.split('\n')
    parents = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parents[ch] = node
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not node.body:
            continue
        last = node.body[-1]
        if not isinstance(last, ast.Return):
            continue
        seg = '\n'.join(lines[last.lineno - 1:last.end_lineno])
        if seg.strip() != 'return None':
            continue                         # bare `return` is a different emission
        out.append({'handler_entry_line': node.lineno, 'line': last.lineno,
                    'end': last.end_lineno, 'indent': last.col_offset,
                    'terminal_chain': terminal_chain(node, parents),
                    'seg': seg.strip()})
    return {'sites': out, 'nlines': len(lines)}


paths = [p.strip() for p in io.open(os.path.join(OUT, 'all402.txt'), encoding='utf-8') if p.strip()]
paths = [p for i, p in enumerate(paths) if i % NS == SH]

rows = []
tally = {'files': 0, 'with_site': 0, 'sites': 0, 'terminal': 0, 'skip_parse': 0}
for p in paths:
    prod = product_of(p)
    if not os.path.isfile(prod):
        continue
    scan_r = scan(prod)
    if scan_r is None:
        tally['skip_parse'] += 1
        continue
    tally['files'] += 1
    if not scan_r['sites']:
        continue
    tally['with_site'] += 1
    tally['sites'] += len(scan_r['sites'])
    tally['terminal'] += sum(1 for s in scan_r['sites'] if s['terminal_chain'])
    rows.append({'pyc': p, 'product': prod, 'sites': scan_r['sites']})

if not MEASURE:
    io.open(os.path.join(OUT, 'probe7_count.sh%s.jsonl' % SH), 'w', encoding='utf-8',
            newline='\n').write('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n')
    print('TALLY %s' % tally)
    print('sites per file (top): %s' % sorted(((len(r['sites']), os.path.basename(r['pyc']))
                                              for r in rows), reverse=True)[:8])
    for r in rows:
        for s in r['sites']:
            if s['terminal_chain']:
                print('TERMINAL  %-56s line %-6d indent %-3d handler@%d' % (
                    os.path.relpath(r['pyc'], REPO + '/site-packages/').replace('\\', '/'),
                    s['line'], s['indent'], s['handler_entry_line']))
else:
    out = io.open(os.path.join(OUT, 'probe7_measure.sh%d.jsonl' % SH), 'w', encoding='utf-8',
                  newline='\n')
    nimp = nreg = nsame = nskip = 0
    for r in rows:
        sites = [s for s in r['sites'] if s['terminal_chain']]
        if not sites:
            continue
        base = pbv.bytecode_diff(r['pyc'], r['product'])
        if base.get('error'):
            print('BASELINE-ERR %s %s' % (r['pyc'], base['error']))
            continue
        bnames = {str(m['name']) for m in base['mismatches']}
        for s in sites:
            txt = io.open(r['product'], encoding='utf-8-sig').read().replace('\r\n', '\n')
            lines = txt.split('\n')
            seg = '\n'.join(lines[s['line'] - 1:s['end']])
            if seg.strip() != 'return None':
                nskip += 1                       # line numbers drifted, refuse to guess
                continue
            new = lines[:s['line'] - 1] + lines[s['end']:]
            v = os.path.join(OUT, 'm7_%d_%d.py' % (SH, s['line']))
            io.open(v, 'w', encoding='utf-8', newline='\n').write('\n'.join(new))
            res = pbv.bytecode_diff(r['pyc'], v)
            if res.get('error'):
                print('VAR-ERR %s line %d %s' % (os.path.basename(r['pyc']), s['line'], res['error']))
                os.remove(v)
                nskip += 1
                continue
            anames = {str(m['name']) for m in res['mismatches']}
            changed = sorted(bnames ^ anames)
            verdict = 'SAME'
            if res['matched_functions'] > base['matched_functions']:
                verdict, nimp = 'IMPROVED', nimp + 1
            elif res['matched_functions'] < base['matched_functions']:
                verdict, nreg = 'REGRESSED', nreg + 1
            else:
                nsame += 1
            rec = {'pyc': r['pyc'], 'product': r['product'], 'line': s['line'],
                   'verdict': verdict, 'matched_before': base['matched_functions'],
                   'matched_after': res['matched_functions'], 'total': base['total_functions'],
                   'funcs_changed': changed}
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
            out.flush()
            os.remove(v)
            if verdict != 'SAME' or changed:
                print('%-9s %-52s line %-5d %d/%d -> %d/%d  %s' % (
                    verdict, os.path.relpath(r['pyc'], REPO + '/site-packages/').replace('\\', '/'),
                    s['line'], base['matched_functions'], base['total_functions'],
                    res['matched_functions'], res['total_functions'], changed[:3]))
    out.close()
    print('SHARD %d/%d sites_measured=%d IMPROVED=%d REGRESSED=%d SAME=%d SKIPPED=%d' % (
        SH, NS, nimp + nreg + nsame, nimp, nreg, nsame, nskip))
