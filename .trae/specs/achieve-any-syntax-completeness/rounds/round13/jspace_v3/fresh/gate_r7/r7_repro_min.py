# -*- coding: utf-8 -*-
"""R7 task-2 / task-3 experiments.

Part A: per-entry repro chain for 3 T1 / 3 T2 / 3 T3 entries (p_j -> pyc ->
        current-tree decompile -> recompile) with const-pool comparison.
Part B: mechanism micro-probes (folded constant arms in truth-test context,
        const-pool order/dedup rules, unreachable-code residue).
Part C: counterfactual product patch: re-emit the original source form, run the
        real judge (tools/completeness/semantic_diff.compare_case) and see
        whether the entry becomes EQUAL.  Proves sufficiency + blast radius.

Read-only w.r.t. core/, scripts/, tests/, tools/; all artefacts go to
D:/temp/opencode/cl_layout/r7/ and fresh/gate_r7/.
"""
from __future__ import annotations

import hashlib
import json
import marshal
import os
import py_compile
import shutil
import sys
import types

ROOT = r'F:\Downloads\pythoncdc-main'
WORK = r'D:\temp\opencode\cl_layout\r7'
PROBES = os.path.join(WORK, 'probes')
PATCHED = os.path.join(WORK, 'patched')
OUT = os.path.join(WORK, 'repro_min.json')
LOG = os.path.join(ROOT, 'fresh', 'gate_r7', 'repro_min.log')
sys.path.insert(0, os.path.join(ROOT, 'tools', 'completeness'))

import semantic_diff as sd  # noqa: E402

PY = sys.executable
DECOMPILER = os.path.join(ROOT, 'pycdc.py')


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def load_pyc(path):
    return marshal.loads(open(path, 'rb').read()[16:])


def comp(path):
    return compile(open(path, 'r', encoding='utf-8-sig').read(), path, 'exec', dont_inherit=True)


def consts_of(code):
    return [(type(v).__name__, repr(v) if not isinstance(v, types.CodeType)
             else '<code %s>' % v.co_qualname) for v in code.co_consts]


def walk_pairs(o, p, path, out):
    """collect every code-object pair (orig, prod) keyed by const path."""
    out.append((path, o, p))
    for i in range(min(len(o.co_consts), len(p.co_consts))):
        a, b = o.co_consts[i], p.co_consts[i]
        if isinstance(a, types.CodeType) and isinstance(b, types.CodeType):
            walk_pairs(a, b, '%s.co_consts[%d]' % (path, i), out)
    return out


def code_tree_equal(o, p):
    """(equal, [diff notes]) over the whole nested code tree, judge field set.

    Constants are compared by (type, repr), never by ``==``: ``(0,) == (False,)``
    is True in Python, which is exactly the T2 trap this analysis is about.
    """
    notes = []
    for path, a, b in walk_pairs(o, p, '$.code', []):
        if a.co_code != b.co_code:
            notes.append('%s.co_code %d!=%d' % (path, len(a.co_code), len(b.co_code)))
        ca, cb = consts_of(a), consts_of(b)
        if ca != cb:
            notes.append('%s.co_consts %s != %s' % (path, ca, cb))
        if a.co_names != b.co_names:
            notes.append('%s.co_names %s != %s' % (path, a.co_names, b.co_names))
        if a.co_exceptiontable != b.co_exceptiontable:
            notes.append('%s.co_exceptiontable differs' % path)
        if a.co_flags != b.co_flags:
            notes.append('%s.co_flags %s != %s' % (path, a.co_flags, b.co_flags))
    return (not notes), notes


def decompile(pyc, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    import subprocess
    proc = subprocess.run([PY, '-X', 'utf8', DECOMPILER, pyc, '-o', out_path],
                          cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=120)
    return proc.returncode, (proc.stderr or proc.stdout or '')[-400:]


def judge(pyc, product_src, call_exprs):
    case = {'case_id': 'probe', 'original': {'pyc': pyc},
            'product': {'source': product_src}, 'entrypoint': 'module',
            'args': [], 'kwargs': {}, 'timeout_s': 20, '_base': ROOT}
    if call_exprs:
        case['call_exprs'] = call_exprs
    res = sd.compare_case(case)
    return {'status': res.get('status'),
            'diffs': [d.get('dimension') for d in res.get('diffs', [])],
            'paths': [d.get('path') for d in res.get('diffs', [])],
            'errors': res.get('errors', [])[:3]}


def probe_row(name, src_text, patches, log):
    """compile -> decompile -> recompile; then re-emit the original form."""
    os.makedirs(PROBES, exist_ok=True)
    src = os.path.join(PROBES, name + '.py')
    open(src, 'w', encoding='utf-8', newline='\n').write(src_text)
    pyc = src + 'c'
    py_compile.compile(src, cfile=pyc, doraise=True)
    prod = os.path.join(PROBES, name + '_prod.py')
    rc, note = decompile(pyc, prod)
    row = {'probe': name, 'source': src_text, 'decompile_rc': rc,
           'product_text': open(prod, encoding='utf-8').read() if os.path.exists(prod) else None}
    o = load_pyc(pyc)
    p = comp(prod)
    eq, notes = code_tree_equal(o, p)
    row['orig_consts'] = consts_of(o)
    row['prod_consts'] = consts_of(p)
    row['tree_equal'] = eq
    row['diffs'] = notes
    # counterfactual: patch the product text back to the original form
    if patches:
        text = open(prod, encoding='utf-8').read()
        applied = []
        for old, new in patches:
            if old in text:
                text = text.replace(old, new, 1)
                applied.append({'old': old, 'new': new})
        patched = os.path.join(PROBES, name + '_patched.py')
        open(patched, 'w', encoding='utf-8', newline='\n').write(text)
        pq = comp(patched)
        eq2, notes2 = code_tree_equal(o, pq)
        row['patched'] = {'applied': applied, 'text': text, 'tree_equal': eq2,
                         'diffs': notes2, 'consts': consts_of(pq)}
    log.write('\n[probe %s]\n' % name)
    log.write('  source     : %s\n' % src_text.replace('\n', ' | '))
    log.write('  product    : %s\n' % (row['product_text'] or '').replace('\n', ' | '))
    log.write('  orig consts: %s\n  prod consts: %s\n' % (row['orig_consts'], row['prod_consts']))
    log.write('  tree_equal : %s %s\n' % (eq, notes))
    if patches:
        log.write('  patched    : tree_equal=%s %s\n' % (row['patched']['tree_equal'],
                                                        row['patched']['diffs']))
        log.write('  patched consts: %s\n' % (row['patched']['consts'],))
    return row


def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(PATCHED, exist_ok=True)
    log = open(LOG, 'w', encoding='utf-8', newline='\n')
    payload = {'groups': [], 'probes': [], 'pool_rules': [], 'counterfactual': []}

    ev = {r['entry_id']: r for r in json.load(open(
        r'D:\temp\opencode\cl_layout\gap\g3fix\semantic_v3m_b275_g3fix_merged.json',
        encoding='utf-8'))['records']}
    tr = json.load(open(r'D:\temp\opencode\cl_layout\gap\g3gap\r7_transfer.json', encoding='utf-8'))
    deep = json.load(open(os.path.join(ROOT, 'fresh', 'gate_r7', 'r7_deep_diff.json'),
                          encoding='utf-8'))

    groups = {g['group']: g for g in deep['groups']}
    by_id = {}
    for g in deep['groups']:
        for eid in g['ids']:
            by_id[eid] = g['group']

    # ---------- Part A: entry repro chains (3 per group) ----------
    samples = {'T2': ['JS-IFEXP-001', 'JS-IFEXP-002', 'JS-IFEXP-003'],
               'T1': ['JS-IFEXP-024', 'JS-IFEXP-025', 'JS-LISTCOMP-012'],
               'T3': ['JS-BREAK-001', 'JS-BREAK-011', 'JS-BREAK-023']}
    for tag, ids in samples.items():
        for eid in ids:
            rec = ev[eid]
            pyc = os.path.join(ROOT, rec['c2']['pyc_path'])
            prod = os.path.join(ROOT, rec['c3']['product_path'])
            row = {'tag': tag, 'entry': eid, 'group': by_id[eid],
                   'p_j': rec['c1']['path'], 'p_j_sha': rec['c1']['sha256'],
                   'pyc': rec['c2']['pyc_path'], 'pyc_sha': sha(pyc),
                   'product': rec['c3']['product_path'], 'product_sha': sha(prod),
                   'judge_paths': [d for d in (rec['c4'].get('diff_paths') or [])]}
            o, p = load_pyc(pyc), comp(prod)
            eq, notes = code_tree_equal(o, p)
            row['tree_equal'] = eq
            row['code_diffs'] = notes
            payload['groups'].append(row)
            log.write('[entry %s %s] p_j=%s pyc=%s product=%s\n'
                      % (tag, eid, row['p_j'], row['pyc'], row['product']))
            log.write('   sha(pyc)=%s sha(product)=%s\n' % (row['pyc_sha'][:16],
                                                           row['product_sha'][:16]))
            log.write('   tree_equal=%s %s\n' % (eq, notes))

    # ---------- Part B: mechanism probes ----------
    probes = [
        # group 1 / T2: falsy folded arm in a comprehension filter
        ('A1_falsy_arm_0', 'def f(xs, b):\n    return [x for x in xs if (x if b else 0)]\n',
         [('else False', 'else 0')]),
        ('A2_falsy_arm_1', 'def f(xs, b):\n    return [x for x in xs if (x if b else 1)]\n',
         [('else True', 'else 1')]),
        ('A3_falsy_arm_none', 'def f(xs, b):\n    return [x for x in xs if (x if b else None)]\n',
         [('else False', 'else None')]),
        ('A4_real_false', 'def f(xs, b):\n    return [x for x in xs if (x if b else False)]\n',
         []),
        # group 2 / T1b: truthy folded orelse -> `not a or b`
        ('B1_true_orelse', 'def f(xs, flag):\n    return [x for x in xs if (x % 2 if flag else True)]\n',
         [('if not flag or x % 2', 'if (x % 2 if flag else True)')]),
        ('B2_true_orelse_1', 'def f(xs, flag):\n    return [x for x in xs if (x % 2 if flag else 1)]\n',
         [('if not flag or x % 2', 'if (x % 2 if flag else 1)')]),
        # group 3 / T3: unreachable `if 0:` body + `pass`
        ('C1_dead_if0',
         'def boom():\n    if 0:\n        raise ValueError(\'x\')\n    for i in range(2):\n'
         '        if i > 0:\n            while True:\n                if i:\n'
         '                    break\n                else:\n                    continue\n'
         '    pass\n    return None\n',
         []),
    ]
    for name, src, patches in probes:
        payload['probes'].append(probe_row(name, src, patches, log))

    # ---------- Part C: const-pool rules ----------
    rules = {}
    m = compile('x = [0, False, 0.0, 1, True, "", 0j]\n', 'r1', 'exec', dont_inherit=True)
    rules['distinct_by_type'] = consts_of(m)
    a = compile('def f(c):\n    return 1 if c else 2\n', 'r2', 'exec', dont_inherit=True)
    b = compile('def f(c):\n    return 2 if c else 1\n', 'r3', 'exec', dont_inherit=True)
    rules['order_first_appearance'] = {'1if2': consts_of(a.co_consts[0]),
                                       '2if1': consts_of(b.co_consts[0])}
    d = compile('def f(c):\n    return (1 if c else 2), (2 if c else 3)\n', 'r4', 'exec',
                dont_inherit=True)
    rules['order_across_arms'] = consts_of(d.co_consts[0])
    e = compile('def f(c):\n    return c if 0 else 0\n', 'r5', 'exec', dont_inherit=True)
    rules['dead_from_folded_test'] = consts_of(e.co_consts[0])
    f = compile("if 0:\n    raise ValueError('x')\n", 'r6', 'exec', dont_inherit=True)
    rules['dead_from_unreachable_body'] = {'consts': consts_of(f), 'names': list(f.co_names)}
    g = compile('def f(xs, b):\n    return [x for x in xs if (x if b else 0)]\n', 'r7', 'exec',
                dont_inherit=True)
    lc = [c for c in g.co_consts[0].co_consts if isinstance(c, types.CodeType)][0]
    used = set()
    import dis
    for ins in dis.get_instructions(lc):
        if ins.opname == 'LOAD_CONST':
            used.add(ins.arg)
    rules['dead_const_in_listcomp'] = {'consts': consts_of(lc), 'loaded_indices': sorted(used)}
    payload['pool_rules'] = rules
    log.write('\n[pool rules]\n')
    for k, v in rules.items():
        log.write('  %-28s %s\n' % (k, v))

    # ---------- Part D: counterfactual full-product patch + real judge ----------
    patched_specs = [
        # group 1 (12 entries): f_ternary_comp_cond listcomp arm  False -> 0
        ('G1_ifexp_deep', 'e04_g2_ifexp_deep.pyc',
         os.path.join(ROOT, '.trae/specs/achieve-any-syntax-completeness/rounds/round13/'
                            'jspace_v3/fresh/semantic_products/shard0/JS-IFEXP-001.py'),
         [('else False)', 'else 0)')], ['_run(1)', '_run(2)']),
        # group 2 (11 entries): filter form back to the folded-True ternary
        ('G2_ternary_comp', 'r7_05_ternary_comprehension.pyc',
         os.path.join(ROOT, '.trae/specs/achieve-any-syntax-completeness/rounds/round13/'
                            'jspace_v3/fresh/semantic_products/shard0/JS-IFEXP-024.py'),
         [('if not flag or x % 2', 'if (x % 2 if flag else True)')], None),
        # group 3 (6 entries): restore unreachable body + pass
        ('G3_class_misc', 'c13_class_misc.pyc',
         os.path.join(ROOT, '.trae/specs/achieve-any-syntax-completeness/rounds/round13/'
                            'jspace_v3/fresh/semantic_products/shard1/JS-BREAK-001.py'),
         [('    def boom(self):\n        while 1:\n            for i in range(2):\n'
           '                if i > 0:\n                    while 1:\n                        if i:\n'
           '                            break\n                continue\n            break\n',
           '    def boom(self):\n        if 0:\n            raise ValueError(\'x\')\n'
           '        for i in range(2):\n            if i > 0:\n                while True:\n'
           '                    if i:\n                        break\n'
           '                    else:\n                        continue\n        pass\n'
           '        return None\n')], ['_run(1)']),
    ]
    for name, pycname, prod, patches, calls in patched_specs:
        text = open(prod, 'r', encoding='utf-8').read()
        applied = []
        for old, new in patches:
            if old in text:
                text = text.replace(old, new, 1)
                applied.append({'old': old.strip(), 'new': new.strip()})
        out = os.path.join(PATCHED, name + '.py')
        open(out, 'w', encoding='utf-8', newline='\n').write(text)
        pyc = os.path.join(ROOT, 'test_repros', 'round7', pycname)
        if not os.path.exists(pyc):
            pyc = os.path.join(ROOT, 'test_repros', 'round3', pycname)
        if not os.path.exists(pyc):
            pyc = os.path.join(ROOT, 'test_repros', 'round2', pycname)
        eq_before, notes_before = code_tree_equal(load_pyc(pyc), comp(prod))
        eq_after, notes_after = code_tree_equal(load_pyc(pyc), comp(out))
        base_calls = None
        for eid, rec in ev.items():
            if pycname.replace('.pyc', '.py') in rec['c1']['path']:
                base_calls = rec['input_model']['calls']
                break
        j_before = judge(pyc, prod, base_calls)
        j_after = judge(pyc, out, base_calls)
        row = {'group': name, 'pyc': pyc, 'patched_product': out,
               'applied': applied, 'patches_matched': len(applied) == len(patches),
               'tree_equal_before': eq_before, 'diffs_before': notes_before,
               'tree_equal_after': eq_after, 'diffs_after': notes_after,
               'calls': base_calls, 'judge_before': j_before, 'judge_after': j_after}
        payload['counterfactual'].append(row)
        log.write('\n[counterfactual %s]\n' % name)
        log.write('  patches applied=%s/%s\n' % (len(applied), len(patches)))
        log.write('  before: tree_equal=%s judge=%s\n' % (eq_before, j_before))
        log.write('  after : tree_equal=%s judge=%s\n' % (eq_after, j_after))

    json.dump(payload, open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False,
              indent=1)
    log.close()
    shutil.copyfile(OUT, os.path.join(ROOT, 'fresh', 'gate_r7', 'repro_min.json'))
    print('wrote', OUT)
    for row in payload['counterfactual']:
        print('%-18s before=%-10s after=%-10s tree %s -> %s'
              % (row['group'], row['judge_before']['status'], row['judge_after']['status'],
                 row['tree_equal_before'], row['tree_equal_after']))


if __name__ == '__main__':
    main()
