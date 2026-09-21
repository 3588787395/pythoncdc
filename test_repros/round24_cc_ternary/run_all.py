# -*- coding: utf-8 -*-
"""Round 24 battery (R24-A: chained-compare IfRegion as ternary header).

Zero repo writes.  Reads the case .py files in this directory, compiles them to a
scratch dir, and decompiles each with a *mirror* core -- never against
F:/Downloads/pythoncdc-main/core.

usage:
  D:/Python/python.exe -X utf8 run_all.py
  ... -X utf8 run_all.py --cores head=/d/Temp/r24land/mirr/head24,cand=/d/Temp/r24land/mirr/patchA4
  ... -X utf8 run_all.py --only a01 --dump   (also print the products)

NOTE: never set PYTHONIOENCODING for this harness -- on this machine that variable (any
value) makes python.exe exit with code 0 and zero bytes on both streams.  UTF-8 comes
from -X utf8, which is re-passed to every worker subprocess.

Verdict per (case, core) -- the OFFICIAL ruler is the currency, because that is what
`stats` publishes:  OK  <=>  the product compiles, every function is matched by
scripts/pyc_batch_verify.bytecode_diff, and every # MUST_CONTAIN line appears.

Gates
  G0  anchor corpus file: cand matched > head matched            (non-vacuity)
  G1  every PRED_R24A_FIX case: OK on the LAST core, NOT OK on the FIRST
  G2  every CONTROL case: OK on every core
  G3  no case OK on the FIRST core and broken on the LAST
  G4  every CONTROL and every PRED_R24A_STABLE case: product sha256 identical across cores

PRED_R24A_STABLE is the byte-identity class only: several authored shapes here are broken
on HEAD by an *unrelated* pre-existing defect (see each case's ACTUAL-HEAD line), so their
value is that R24-A leaves them exactly as HEAD emits them, which is what G4 asserts.
"""
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SCRATCH = r'D:\Temp\r24land\build'
PY = r'D:/Python/python.exe'
DEFAULT_CORES = [('head', r'D:\Temp\r24land\mirr\head24'),
                 ('cand', r'D:\Temp\r24land\mirr\patchA4')]
# (label, pyc, what R24-A is supposed to change there)
ANCHORS = [
    ('real_quote_get_real_L2_data',
     os.path.join(REPO, 'site-packages', 'IQData', 'plugins',
                  'plugin_system_realquote', 'real_quote.pyc'),
     'get_real_L2_data: 359/359 chained-compare ternary body dropped -> matched'),
]


def argv(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


# ------------------------------------------------------------------ worker
def worker(core_path, py_path):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.dont_write_bytecode = True
    core_path = os.path.abspath(core_path)
    sys.path.insert(0, core_path)
    import pycdc
    assert os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/') \
        .startswith(core_path.replace('\\', '/')), \
        'pycdc resolved to %s, not the mirror %s' % (pycdc.__file__, core_path)
    spec = importlib.util.spec_from_file_location(
        'pbv_r24', os.path.join(REPO, 'scripts', 'pyc_batch_verify.py'))
    pbv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pbv)

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
    out = {'sha': hashlib.sha256(text.encode('utf-8')).hexdigest()[:16],
           'text': text, 'textlen': len(text)}
    try:
        py_compile.compile(prod, cfile=os.path.join(SCRATCH, stem + '.prod.pyc'),
                           doraise=True, quiet=2)
    except Exception as e:
        out['compile_error'] = str(e)[:200]
        print(json.dumps(out))
        return
    r = pbv.bytecode_diff(pyc, prod)
    out['total'] = r.get('total_functions')
    out['matched'] = r.get('matched_functions')
    out['error'] = r.get('error')
    out['mis'] = [[m['name'], m.get('orig_count'), m.get('decomp_count')]
                  for m in (r.get('mismatches') or [])]
    print(json.dumps(out))


if __name__ == '__main__' and argv('--worker'):
    worker(argv('--core'), argv('--py'))
    sys.exit(0)


# ------------------------------------------------------------------ driver
def parse_case(path):
    if path.lower().endswith('.pyc'):
        return {'path': os.path.abspath(path), 'name': os.path.basename(path)[:-4],
                'mark': 'ANCHOR', 'musts': [], 'shape': 'corpus anchor (measured)',
                'expected': 'official matched must not decrease'}
    txt = io.open(path, encoding='utf-8').read()
    marks = re.findall(r'^#\s*MARK:\s*(\S+)', txt, re.M)
    musts = re.findall(r'^#\s*MUST_CONTAIN:\s*(.*)$', txt, re.M)
    shape = re.search(r'^#\s*SHAPE:(.*)$', txt, re.M)
    exp = re.search(r'^#\s*EXPECTED:(.*)$', txt, re.M)
    return {'path': path, 'name': os.path.basename(path)[:-3],
            'mark': marks[0] if marks else 'DIAG',
            'musts': [m.strip() for m in musts if m.strip()],
            'shape': (shape.group(1).strip() if shape else ''),
            'expected': (exp.group(1).strip() if exp else '')}


def run_core(core_name, core_path, case):
    env = {k: v for k, v in os.environ.items() if k.upper() != 'PYTHONIOENCODING'}
    p = subprocess.run([PY, '-X', 'utf8', os.path.join(HERE, 'run_all.py'), '--worker',
                        '--core', core_path, '--py', case['path']],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=600, env=env)
    try:
        d = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        d = {'text': '', 'textlen': 0, 'crash': (p.stderr or '')[-500:]}
    miss = [m for m in case['musts'] if m and m not in d.get('text', '')]
    total, matched = d.get('total'), d.get('matched')
    ok = (not d.get('crash') and 'compile_error' not in d and not miss
          and not d.get('error') and total is not None and matched == total
          and (total or 0) > 0)
    return {'ok': ok, 'matched': matched, 'total': total, 'mis': d.get('mis'),
            'sha': d.get('sha'), 'textlen': d.get('textlen'), 'miss': miss,
            'cerr': d.get('compile_error'), 'crash': d.get('crash'),
            'err': d.get('error'), 'text': d.get('text', '')}


def main():
    cores = DEFAULT_CORES
    if argv('--cores'):
        cores = [tuple(x.split('=', 1)) for x in argv('--cores').split(',')]
    cases = [parse_case(os.path.join(HERE, f)) for f in sorted(os.listdir(HERE))
             if f.endswith('.py') and not f.startswith('_') and f != 'run_all.py']
    if argv('--only'):
        cases = [c for c in cases if argv('--only') in c['name']]
    names = [n for n, _ in cores]
    out = {n: {c['name']: run_core(n, p, c) for c in cases} for n, p in cores}
    io.open(os.path.join(SCRATCH, 'battery_results.json'), 'w',
            encoding='utf-8').write(json.dumps(
        {n: {k: {kk: vv for kk, vv in v.items() if kk != 'text'}
             for k, v in out[n].items()} for n in names}, indent=1))
    first, last = names[0], names[-1]

    print('=' * 100)
    print('R24 BATTERY   cores: ' + ', '.join('%s=%s' % t for t in cores))
    print('=' * 100)
    g1 = g2 = g3 = g4 = True
    fixed = broken = 0
    n_pred = n_ctl = n_stab = 0
    tot = {n: [0, 0] for n in names}
    for c in cases:
        r = {n: out[n][c['name']] for n in names}
        print('\n[%s] %s' % (c['mark'], c['name']))
        print('  shape    : %s' % c['shape'][:120])
        print('  expected : %s' % c['expected'][:120])
        for n in names:
            v, t = r[n], tot[n]
            t[0] += v['matched'] or 0
            t[1] += v['total'] or 0
            det = ''
            if v['mis']:
                det += ' ; ' + '; '.join('%s %s/%s' % (m[0], m[1], m[2])
                                         for m in v['mis'][:5])
            if v['miss']:
                det += ' ; MUST_CONTAIN missing: %r' % (v['miss'],)
            if v['cerr']:
                det += ' ; product does not compile: %s' % v['cerr'][:120]
            if v['crash']:
                det += ' ; CORE CRASH: %s' % v['crash'][-220:]
            print('  actual   : %-5s %-4s matched=%-4s/%-4s sha=%-18s len=%-6d%s'
                  % (n, 'OK' if v['ok'] else 'FAIL', v['matched'], v['total'],
                     v['sha'], v['textlen'], det))
        if argv('--dump'):
            for n in names:
                print('  ---- %s product ----\n%s' % (n, out[n][c['name']]['text']))
        if r[first]['ok'] and not r[last]['ok']:
            broken += 1
        if r[last]['ok'] and not r[first]['ok']:
            fixed += 1
        if c['mark'] == 'PRED_R24A_FIX':
            n_pred += 1
            if not (r[last]['ok'] and not r[first]['ok']):
                g1 = False
                print('  GATE G1 violation: %s head_ok=%s cand_ok=%s'
                      % (c['name'], r[first]['ok'], r[last]['ok']))
        if c['mark'] in ('CONTROL', 'PRED_R24A_STABLE'):
            n_ctl += 1 if c['mark'] == 'CONTROL' else 0
            n_stab += 1 if c['mark'] == 'PRED_R24A_STABLE' else 0
            if c['mark'] == 'CONTROL' and not all(r[n]['ok'] for n in names):
                g2 = False
                print('  GATE G2 violation: %s (CONTROL) not OK on every core'
                      % c['name'])
            shas = {r[n]['sha'] for n in names}
            if len(shas) != 1:
                g4 = False
                print('  GATE G4 violation: %s product differs across cores %s'
                      % (c['name'], shas))
        if r[first]['ok'] and not r[last]['ok']:
            g3 = False
            print('  GATE G3 violation: %s regressed %s->%s' % (c['name'], first, last))

    # ---- corpus anchor: the only place the gain is measured in currency ----
    print('\n' + '=' * 100)
    print('CORPUS ANCHOR (official matched/total for the whole file)')
    g0 = None
    for label, pyc, what in ANCHORS:
        row = {}
        for n, pth in cores:
            v = run_core(n, pth, parse_case(pyc))
            row[n] = v
            print('  %-32s %-5s matched=%s/%s  %s'
                  % (label, n, v['matched'], v['total'], what[:60]))
        g0 = (row[last]['matched'] or 0) > (row[first]['matched'] or 0)
        if not g0:
            print('  GATE G0 violation: anchor did not improve %s->%s (%s->%s)'
                  % (first, last, row[first]['matched'], row[last]['matched']))
        else:
            print('  -> improves %s -> %s  (R24-A non-vacuity proof)'
                  % (row[first]['matched'], row[last]['matched']))

    print('\n' + '-' * 100)
    print('cases=%d  PRED_R24A_FIX=%d  CONTROL=%d  STABLE=%d'
          % (len(cases), n_pred, n_ctl, n_stab))
    print('fixed by %s (vs %s) = %d ; broken by %s = %d' % (last, first, fixed, last, broken))
    print('official matched over the py shapes: '
          + ', '.join('%s=%d/%d' % (n, tot[n][0], tot[n][1]) for n in names))
    print('G0(anchor improves with %s)=%s' % (last, g0))
    print('G1(FIX cases fail->ok, non-vacuous)=%s  [%d cases]' % (g1, n_pred))
    print('G2(controls OK on every core)=%s   G3(no OK->FAIL)=%s' % (g2, g3))
    print('G4(controls+stables byte-identical)=%s' % g4)
    print('GATE: %s' % ('PASS' if (g0 and g1 and g2 and g3 and g4) else 'FAIL'))


if __name__ == '__main__':
    main()
