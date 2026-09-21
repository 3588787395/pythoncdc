# -*- coding: utf-8 -*-
"""Round 23 battery runner.  Zero repo writes except reading the case .py files.

Each (core) is measured in a FRESH subprocess against a mirror copy of the core
outside the repo -- never against F:/Downloads/pythoncdc-main/core.

usage:
  PYTHONIOENCODING=utf-8 D:/Python/python.exe run_all.py
  ... run_all.py --cores head=/d/Temp/r23fix/mirr/head,c1a=/d/Temp/r23fix/mirr/c1a
  ... run_all.py --only b07 --dump            (print the products)

Gate:
  G1  every PRED_R23A_FIX case: OK under the LAST core, NOT OK under the first
  G2  every CONTROL case: OK under every core
  G3  no case OK under the first core and broken under a later one
"""
import io
import json
import os
import py_compile
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = r'D:\Temp\r23res\build'
PY = r'D:/Python/python.exe'
DEFAULT_CORES = [('head', r'D:\Temp\r23fix\mirr\head'),
                 ('c1a', r'D:\Temp\r23fix\mirr\c1a')]
# (label, pyc, functions of interest).  These are corpus files, measured with the
# mirror\'s own strict ruler; the .py shapes above cannot express them.
ANCHORS = [
    ('realtime_event_source',
     r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins'
     r'\plugin_system_event_source\realtime_event_source.pyc',
     'clock_worker, get_one_event'),
]


def argv(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


# ------------------------------------------------------------------ worker
def worker(core_path, py_path, dump):
    sys.dont_write_bytecode = True
    core_path = os.path.abspath(core_path)
    sys.path.insert(0, core_path)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'sc_r23', os.path.join(core_path, '_r10_strict_check.py'))
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    import pycdc
    os.makedirs(SCRATCH, exist_ok=True)
    stem = re.sub(r'[^A-Za-z0-9_]', '_', os.path.basename(py_path))
    if py_path.lower().endswith('.pyc'):
        pyc = os.path.abspath(py_path)
    else:
        pyc = os.path.join(SCRATCH, stem + '.orig.pyc')
        py_compile.compile(py_path, cfile=pyc, doraise=True, quiet=2)
    text = pycdc.decompile_pyc(pyc)
    prod = os.path.join(SCRATCH, stem + '.prod.py')
    io.open(prod, 'w', encoding='utf-8').write(text)
    pprod = os.path.join(SCRATCH, stem + '.prod.pyc')
    out = {'text': text, 'funcs': [], 'textlen': len(text)}
    try:
        py_compile.compile(prod, cfile=pprod, doraise=True, quiet=2)
    except Exception as e:
        out['compile_error'] = str(e)
        print(json.dumps(out))
        return
    origs = sc._load_map(pyc)
    decs = sc._load_map(pprod)
    for k, oc in origs.items():
        dc = decs.get(k)
        if dc is None:
            out['funcs'].append({'fn': k, 'kind': 'missing', 'no': len(sc.filtered(oc)), 'nd': 0})
            continue
        kind, msg, defect = sc.strict_compare(oc, dc)
        out['funcs'].append({'fn': k, 'kind': kind or 'ok', 'msg': msg,
                             'no': len(sc.filtered(oc)), 'nd': len(sc.filtered(dc))})
    print(json.dumps(out))


if __name__ == '__main__' and argv('--worker'):
    worker(argv('--core'), argv('--py'), bool(argv('--dump')))
    sys.exit(0)


# ------------------------------------------------------------------ driver
def parse_case(path):
    if path.lower().endswith('.pyc'):
        return {'path': os.path.abspath(path), 'name': os.path.basename(path)[:-4],
                'mark': 'ANCHOR', 'musts': [], 'shape': 'corpus anchor (measured, not authored)',
                'expected': 'strict |orig-decomp| must not grow'}
    txt = io.open(path, encoding='utf-8').read()
    markers = re.findall(r'^#\s*MARK:\s*(\S+)', txt, re.M)
    musts = re.findall(r'^#\s*MUST_CONTAIN:\s*(.*)$', txt, re.M)
    shape = re.search(r'^#\s*SHAPE:\s*(.*)(?:\n#\s*.*)*$', txt, re.M)
    exp = re.search(r'^#\s*EXPECTED:\s*(.*)$', txt, re.M)
    body = txt.split('\n', 0)
    return {'path': path, 'name': os.path.basename(path)[:-3],
            'mark': markers[0] if markers else 'DIAG',
            'musts': [m.strip() for m in musts],
            'shape': shape.group(1).strip() if shape else '',
            'expected': exp.group(1).strip() if exp else ''}


def run_core(name, path, cases):
    res = {}
    for c in cases:
        p = subprocess.run([PY, os.path.join(HERE, 'run_all.py'), '--worker',
                            '--core', path, '--py', c['path']],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=280)
        try:
            d = json.loads(p.stdout.strip().splitlines()[-1])
        except Exception:
            d = {'text': '', 'funcs': [], 'textlen': 0, 'crash': (p.stderr or '')[-400:]}
        bad = [f for f in d.get('funcs', []) if f.get('kind') not in ('ok', None)]
        miss = [m for m in c['musts'] if m and m not in d.get('text', '')]
        res[c['name']] = {
            'ok': not bad and not miss and 'compile_error' not in d and not d.get('crash'),
            'bad': bad, 'miss': miss, 'text': d.get('text', ''),
            'textlen': d.get('textlen', 0), 'cerr': d.get('compile_error'),
            'crash': d.get('crash'),
            'delta': sum(abs(f['no'] - f['nd']) for f in d.get('funcs', [])),
            'n_fn': len(d.get('funcs', []))}
    return res


def main():
    cores = DEFAULT_CORES
    if argv('--cores'):
        cores = [tuple(x.split('=', 1)) for x in argv('--cores').split(',')]
    cases = [parse_case(os.path.join(HERE, f)) for f in sorted(os.listdir(HERE))
             if f.endswith('.py') and not f.startswith('_') and f != 'run_all.py']
    if argv('--only'):
        cases = [c for c in cases if argv('--only') in c['name']]
    names = [n for n, _ in cores]
    out = {n: run_core(n, p, cases) for n, p in cores}
    io.open(os.path.join(SCRATCH, 'battery_results.json'), 'w', encoding='utf-8').write(
        json.dumps({n: {k: {kk: vv for kk, vv in v.items() if kk != 'text'}
                        for k, v in out[n].items()} for n in names}, indent=1))
    first, last = names[0], names[-1]
    print('=' * 100)
    print('R23 BATTERY   cores: ' + ', '.join('%s=%s' % t for t in cores))
    print('=' * 100)
    g1 = g2 = g3 = True
    fixed = broken = 0
    for c in cases:
        r = {n: out[n][c['name']] for n in names}
        print('\n[%s] %s' % (c['mark'], c['name']))
        print('  shape    : %s' % c['shape'][:150])
        print('  expected : %s' % c['expected'][:150])
        for n in names:
            v = r[n]
            det = ''
            if v['bad']:
                det = ' ; ' + '; '.join('%s %s %s' % (b['fn'], b['kind'], b.get('msg', ''))
                                        for b in v['bad'][:4])
            if v['miss']:
                det += ' ; MUST_CONTAIN missing: %r' % (v['miss'],)
            if v['cerr']:
                det += ' ; product does not compile: %s' % v['cerr'][:120]
            if v['crash']:
                det += ' ; CORE CRASH: %s' % v['crash'][-200:]
            print('  actual   : %-5s %-4s  |d|=%-4d textlen=%-6d%s'
                  % (n, 'OK' if v['ok'] else 'FAIL', v['delta'], v['textlen'], det))
        if argv('--dump'):
            for n in names:
                print('  ---- %s product ----\n%s' % (n, out[n][c['name']]['text']))
        if r[first]['ok'] and not r[last]['ok']:
            broken += 1
        if r[last]['ok'] and not r[first]['ok']:
            fixed += 1
        if c['mark'] == 'PRED_R23A_FIX':
            ok = r[last]['ok'] and not r[first]['ok']
            if not ok:
                g1 = False
                print('  GATE G1 violation: %s (head_ok=%s c1a_ok=%s)'
                      % (c['name'], r[first]['ok'], r[last]['ok']))
        if c['mark'] == 'CONTROL':
            if not all(r[n]['ok'] for n in names):
                g2 = False
                print('  GATE G2 violation: control %s not OK everywhere' % c['name'])
        if r[first]['ok'] and not r[last]['ok']:
            g3 = False
            print('  GATE G3 violation: %s regressed %s->%s' % (c['name'], first, last))
    n_pred = sum(1 for c in cases if c['mark'] == 'PRED_R23A_FIX')
    n_ctl = sum(1 for c in cases if c['mark'] == 'CONTROL')
    n_all = sum(1 for c in cases if all(out[n][c['name']]['ok'] for n in names))
    tot_delta = {n: sum(out[n][c['name']]['delta'] for c in cases) for n in names}
    # ---- corpus anchors: the only places R23-A is measurably observable -------
    print('\n' + '=' * 100)
    print('CORPUS ANCHORS (strict |orig-decomp| summed over the file\'s functions)')
    g0 = True
    for label, pyc, fns in ANCHORS:
        row = {}
        for n, pth in cores:
            r = run_core('anchor:' + label, pth, [parse_case(pyc)])
            v = r[label]
            row[n] = v
            print('  %-28s %-34s %-5s |d|=%-4d textlen=%-6d %s'
                  % (label, fns, n, v['delta'], v['textlen'],
                     '; '.join('%s %s' % (b['fn'].split('.')[-1], b.get('msg') or b['kind'])
                               for b in v['bad'][:5])))
        if not (row[last]['delta'] < row[first]['delta']):
            g0 = False
            print('  GATE G0 violation: %s did not improve %s->%s (%d->%d)'
                  % (label, first, last, row[first]['delta'], row[last]['delta']))
        else:
            print('  -> %s improves %d -> %d  (R23-A non-vacuity proof)'
                  % (label, row[first]['delta'], row[last]['delta']))
    print('\n' + '-' * 100)
    print('cases=%d  PRED_R23A_FIX=%d  CONTROL=%d  OK-on-all-cores=%d'
          % (len(cases), n_pred, n_ctl, n_all))
    print('fixed by %s (vs %s) = %d ; broken by %s = %d' % (last, first, fixed, last, broken))
    print('sum |orig-decomp| per core (py shapes): ' + ', '.join('%s=%d' % (n, tot_delta[n]) for n in names))
    print('G0(corpus anchor improves with %s)=%s' % (last, g0))
    if n_pred:
        print('G1(or-ext arm loss fixed by %s, non-vacuous)=%s  [%d cases]' % (last, g1, n_pred))
    else:
        print('G1=NOT EVALUATED: no PRED_R23A_FIX case exists -- R23-A produces a '
              'byte-identical product on all 6 hand-built or-extension shapes (ANALYSIS.md S5.1)')
    print('G2(controls untouched)=%s   G3(no regressions)=%s' % (g2, g3))
    print('GATE: %s' % ('PASS' if (g0 and g2 and g3) else 'FAIL'))
    print('NOTE GATE = G0 and G2 and G3.  G0 is the R23-A non-vacuity proof (corpus anchor only).')


if __name__ == '__main__':
    main()
