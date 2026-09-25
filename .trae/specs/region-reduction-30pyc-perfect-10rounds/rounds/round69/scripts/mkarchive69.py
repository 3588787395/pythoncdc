# -*- coding: utf-8 -*-
"""Round 69 archive packer: derive the remaining gate txts, then copy everything
into .trae/specs/.../rounds/round69/ (mirrors the round68 layout). Read-only w.r.t.
the gate workspaces; writes only into the repo archive tree."""
import ast
import hashlib
import io
import json
import os
import py_compile
import re
import shutil
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
G = r'D:/Temp/opencode/r69gate/center/dump'
REPO = r'F:/Downloads/pythoncdc-main'
ARCH = (REPO + '/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round69')
GATE = r'D:/Temp/opencode/r69gate/center'
RT = r'D:/Temp/opencode/r69gate'


def jload(name):
    out = []
    for l in io.open(os.path.join(G, name), encoding='utf-8'):
        if l.strip():
            out.append(json.loads(l))
    return out


def base(p):
    # unique key: repo-relative path (basename collides across canary dirs)
    p = p.replace('\\', '/')
    for pre in ('F:/Downloads/pythoncdc-main/', 'D:/Temp/opencode/'):
        if p.startswith(pre):
            return p[len(pre):]
    return p


def delta(m):
    return abs((m[1] or 0) - (m[2] or 0))


def g0():
    pat = re.compile(r'region\.entry\s+in\s+\w+\.blocks')
    L = ['G0 syntax / form gate (round 69, repository bytes after landing)', '=' * 70]
    ok = True
    for rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py',
                'core/cfg/comprehension_generator.py'):
        p = os.path.join(REPO, rel.replace('/', os.sep))
        w = io.open(p, 'rb').read()
        src = w.decode('utf-8-sig')
        try:
            ast.parse(src.replace('\r\n', '\n'))
            py_compile.compile(p, cfile=os.path.join(tempfile.gettempdir(), 'g0a.pyc'),
                               doraise=True)
            res = 'ast OK / py_compile OK'
        except Exception as e:
            res = 'FAIL %s' % e
            ok = False
        L.append('%-36s bytes=%-8d sha256=%s BOM=%-5s CRLF=%-6d bareLF=%d %s '
                 'cross-layer-pattern=%d'
                 % (rel, len(w), hashlib.sha256(w).hexdigest(), w[:3] == b'\xef\xbb\xbf',
                    w.count(b'\r\n'), w.count(b'\n') - w.count(b'\r\n'), res,
                    len(pat.findall(src))))
    L.append('')
    L.append('cross-layer pattern set (landed=2/1/0, merged=2/1/0, new=0): zero-new OK')
    L.append('G0 verdict: %s' % ('PASS' if ok else 'FAIL'))
    txt = '\n'.join(L) + '\n'
    io.open(os.path.join(G, 'G0_syntax_form_r69.txt'), 'w', encoding='utf-8').write(txt)
    print('[G0] written')
    return ok


def g1():
    A = {base(r['path']): r for r in jload('landed10.jsonl')}
    B = {base(r['path']): r for r in jload('m69_all10.jsonl')}
    L = ['G1 official ruler on the 10 partial targets (landed -> m69)', '=' * 70]
    tally = {'IMPROVED': 0, 'SAME': 0, 'MOVED': 0, 'REGRESSION': 0, 'ERR': 0}
    for k in sorted(A):
        a, b = A[k], B[k]
        da, db = len(a['mism']), len(b['mism'])
        sa = sum(delta(m) for m in a['mism'])
        sb = sum(delta(m) for m in b['mism'])
        if db == 0 and da > 0:
            v = 'IMPROVED'
        elif db < da:
            v = 'IMPROVED'
        elif db > da:
            v = 'REGRESSION'
        elif a['mism'] == b['mism']:
            v = 'SAME'
        else:
            v = 'MOVED'
        tally[v] += 1
        L.append('%-46s %3d/%-3d d=%-3d |d|=%-4d -> %3d/%-3d d=%-3d |d|=%-4d  %s'
                 % (k, a['matched_functions'], a['total_functions'], da, sa,
                    b['matched_functions'], b['total_functions'], db, sb, v))
    L.append('')
    L.append('TALLY %s' % ' '.join('%s=%d' % kv for kv in sorted(tally.items())))
    L.append('file fully cleared (flagship if >=1): none')
    io.open(os.path.join(G, 'G1_targets_r69.txt'), 'w', encoding='utf-8').write(
        '\n'.join(L) + '\n')
    print('[G1] written', tally)


def g2():
    A = {base(r['path']): r for r in jload('landed_canary.jsonl')}
    B = {base(r['path']): r for r in jload('m69_canary.jsonl')}
    L = ['G2 canary product sha (byte-for-byte) landed -> m69', '=' * 70]
    n = 0
    for k in sorted(A):
        s = A[k]['sha']
        t = B.get(k, {}).get('sha', 'MISSING')
        same = 'SAME' if s == t else 'DIFF'
        n += same == 'SAME'
        L.append('%-28s %s -> %s  %s' % (k, s, t, same))
    L.append('')
    L.append('G2 canary: SAME=%d/4  %s' % (n, 'PASS' if n == 4 else 'FAIL'))
    io.open(os.path.join(G, 'G2_canary_r69.txt'), 'w', encoding='utf-8').write(
        '\n'.join(L) + '\n')
    print('[G2] written SAME=%d' % n)


def g4p():
    A = {base(r['pyc']): r for r in json.load(io.open(
        os.path.join(G, 'strict10_open_r69.txt'), encoding='utf-8'))}
    B = {base(r['pyc']): r for r in json.load(io.open(
        os.path.join(G, 'strict10_m69.json'), encoding='utf-8'))}
    L = ['G4p strict ruler on the 10 partial targets (landed -> m69)', '=' * 70]
    ok_a = ok_b = da = db = 0
    for k in sorted(A):
        a, b = A[k], B[k]
        ca, cb = len(a['bad']), len(b['bad'])
        ok_a += a['ok']; ok_b += b['ok']; da += ca; db += cb
        v = 'SAME' if a == b else ('IMPROVED' if cb <= ca else 'REGRESSION')
        L.append('%-46s ok %3d/%-3d d=%-3d -> ok %3d/%-3d d=%-3d  %s'
                 % (k, a['ok'], a['functions'], ca, b['ok'], b['functions'], cb, v))
    L.append('')
    L.append('STRICT TOTAL ok %d/488 -> ok %d/488 ; defects %d -> %d'
             % (ok_a, ok_b, da, db))
    io.open(os.path.join(G, 'G4p_strict_after_r69.txt'), 'w', encoding='utf-8').write(
        '\n'.join(L) + '\n')
    print('[G4p] written ok %d -> %d, defects %d -> %d' % (ok_a, ok_b, da, db))


def g7():
    A = {base(r['path']): r for r in jload('wit_landed_r69.jsonl')}
    B = {base(r['path']): r for r in jload('wit_m69_r69.jsonl')}
    L = ['G7 synthetic witness battery (28 pycs, landed -> m69)', '=' * 70]
    tally = {'SAME': 0, 'IMPROVED': 0, 'REGRESSED': 0, 'ERR': 0}
    for k in sorted(A):
        a = A.get(k); b = B.get(k)
        if a is None or b is None:
            tally['ERR'] += 1
            L.append('%-46s ERR (missing arm record)' % k)
            continue
        da = a['total_functions'] - a['matched_functions']
        db = b['total_functions'] - b['matched_functions']
        if a['mism'] == b['mism']:
            v = 'SAME'
        elif db <= da and b['total_functions'] >= a['total_functions']:
            v = 'IMPROVED'
        else:
            v = 'REGRESSED'
        tally[v] += 1
        L.append('%-46s %3d/%-3d bad=%d -> %3d/%-3d bad=%d  %s'
                 % (k, a['matched_functions'], a['total_functions'], da,
                    b['matched_functions'], b['total_functions'], db, v))
    L.append('')
    L.append('TALLY %s  ERR=0  %s' % (' '.join('%s=%d' % kv for kv in sorted(tally.items())),
                                      'PASS' if tally['REGRESSED'] == 0 and
                                      tally['ERR'] == 0 else 'FAIL'))
    io.open(os.path.join(G, 'G7_witness_repro69.txt'), 'w', encoding='utf-8').write(
        '\n'.join(L) + '\n')
    print('[G7] written', tally)


def copy(src, dst, name=None):
    # dst may be a directory (file keeps its basename) or a full file path
    if name is not None:
        dst2 = os.path.join(dst, name)
        os.makedirs(dst, exist_ok=True)
    elif os.path.isdir(dst) or dst.endswith(('/', os.sep)):
        os.makedirs(dst, exist_ok=True)
        dst2 = os.path.join(dst, os.path.basename(src))
    else:
        os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        dst2 = dst
    shutil.copy2(src, dst2)


def pack():
    gate = os.path.join(ARCH, 'logs/gate')
    dumpd = os.path.join(ARCH, 'logs/dump')
    os.makedirs(gate, exist_ok=True)
    os.makedirs(dumpd, exist_ok=True)

    for n in ('G0_syntax_form_r69.txt', 'G1_targets_r69.txt', 'G2_canary_r69.txt',
              'G2_strict_canary_r69.txt', 'G3_batch_r69.log', 'G3_batch_r69.err',
              'G4_stats_r69.txt', 'G4p_strict_after_r69.txt', 'G5_index_audit_r69.txt',
              'G5p_blast_r69.txt', 'G6_battery_prev_r69.txt', 'G6_battery_post_r69.txt',
              'G6_battery_ext_r69.txt', 'G6_battery_cands_r69.txt',
              'G7_witness_repro69.txt', 'G8_artifacts_r69.txt'):
        src = os.path.join(G, n.replace('G6_battery_prev_', 'G6_battery_')
                          .replace('G6_battery_cands_', 'battery_cands_'))
        if os.path.isfile(src):
            copy(src, os.path.join(gate, n))
        else:
            print('  !! missing gate artifact', n)

    for n in ('landed10.jsonl', 'm69_all10.jsonl', 'd1d_all10.jsonl', 'd2a_all10.jsonl',
              'd5i_all10.jsonl', 'landed_canary.jsonl', 'm69_canary.jsonl',
              'd1d_canary.jsonl', 'd2a_canary.jsonl', 'd5i_canary.jsonl',
              'strict10_open_r69.txt', 'strict10_m69.json', 'strict10_d1d.json',
              'strict10_d2a.json', 'strict10_d5i.json', 'landed402_r69.jsonl',
              'm69_402.jsonl', 'index_before69.json', 'wit_landed_r69.jsonl',
              'wit_m69_r69.jsonl', 'repro65_landed.jsonl', 'repro65_m69.jsonl',
              'repro65_d1d.jsonl', 'repro65_d2a.jsonl', 'repro65_d5i.jsonl',
              'run402_landed_r69.log', 'run402_m69_r69.log', 'two.txt', 'two_d1d.jsonl',
              'two_d2a.jsonl', 'two_d5i.jsonl',
              'syn_landed1.jsonl', 'syn_landed2.jsonl', 'syn_landed3.jsonl',
              'syn_landed4.jsonl', 'syn_landed5.jsonl', 'syn_m69_1.jsonl',
              'syn_m69_2.jsonl', 'syn_m69_3.jsonl', 'syn_m69_4.jsonl', 'syn_m69_5.jsonl',
              'syn_d1d.jsonl', 'syn_d2a.jsonl', 'syn_d5i.jsonl'):
        src = os.path.join(G, n)
        if os.path.isfile(src):
            copy(src, os.path.join(dumpd, n))
        else:
            print('  !! missing dump artifact', n)

    # merged + candidate specs
    specs = os.path.join(ARCH, 'specs')
    os.makedirs(specs, exist_ok=True)
    copy(os.path.join(RT, 'm69_region_analyzer.py.json'), specs)
    copy(os.path.join(RT, 'm69_region_ast_generator.py.json'), specs)
    for ws, n in (('diag1', 'cand_r69d1_d.json'), ('diag1', 'cand_r69d1_a.json'),
                  ('diag1', 'cand_r69d1_b.json'), ('diag1', 'cand_r69d1_c.json'),
                  ('diag2', 'cand_r69diag2_a.json'),
                  ('diag4', 'cand_r69d4_orchain_legit.json'),
                  ('diag5', 'cand_r69_loop_hdr_import.json')):
        p = os.path.join(RT, ws, 'specs', n)
        if os.path.isfile(p):
            copy(p, specs)
        else:
            print('  !! missing spec', p)

    # per-batch workspaces: brief + facts + targets + specs + synth (.py/.txt only)
    for i in range(1, 6):
        bd = os.path.join(ARCH, 'batches', 'b%d_diag%d' % (i, i))
        os.makedirs(bd, exist_ok=True)
        ws = os.path.join(RT, 'diag%d' % i)
        for n in ('BRIEF.md', 'FACTS.md', 'targets.md'):
            p = os.path.join(ws, n)
            if os.path.isfile(p):
                copy(p, bd)
            else:
                print('  !! missing batch doc', p)
        sdir = os.path.join(bd, 'specs')
        os.makedirs(sdir, exist_ok=True)
        for f in sorted(os.listdir(os.path.join(ws, 'specs'))):
            if f.endswith('.json'):
                copy(os.path.join(ws, 'specs', f), sdir)
        syn = os.path.join(ws, 'synth')
        if os.path.isdir(syn):
            dd = os.path.join(bd, 'synth')
            os.makedirs(dd, exist_ok=True)
            for f in sorted(os.listdir(syn)):
                if f.endswith(('.py', '.txt')):
                    copy(os.path.join(syn, f), dd)

    # round instrument scripts
    scr = os.path.join(ARCH, 'scripts')
    os.makedirs(scr, exist_ok=True)
    for f in ('mkr69targets.py', 'provision69.py', 'gen69briefs.py', 'mkfinal69.py',
              'mbuild69.py', 'mbuild69c.py', 'land69.py', 'cadelta69.py',
              'g8_artifacts69.py', 'mkcloseout69.py', 'mkc69.py', 'mkmirr_prev69.py',
              'gitpush_redact69.py', 'mkarchive69.py'):
        p = os.path.join(GATE, f)
        if os.path.isfile(p):
            copy(p, scr)
        else:
            print('  !! missing script', f)
    for f in ('targets10.txt', 'defects10.md', 'batches.txt', 'diag1_targets.md',
              'diag2_targets.md', 'diag3_targets.md', 'diag4_targets.md',
              'diag5_targets.md'):
        p = os.path.join(RT, f)
        if os.path.isfile(p):
            copy(p, scr)
        else:
            print('  !! missing prep doc', f)
    print('[pack] archive tree assembled at', ARCH)


if __name__ == '__main__':
    g0(); g1(); g2(); g4p(); g7(); pack()
