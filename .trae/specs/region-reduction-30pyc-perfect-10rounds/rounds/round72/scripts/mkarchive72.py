# -*- coding: utf-8 -*-
"""Round 72 archive packer: copy gate/dump/spec/batch/script artifacts from the
r72gate workspace into the repo archive tree.  Read-only w.r.t. the gate workspaces."""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
RT = r'D:/Temp/opencode/r72gate'
C = RT + '/center'
ARCH = REPO + '/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round72'


def copy(src, dst_dir, name=None):
    if not os.path.isfile(src):
        print('  !! missing', src)
        return
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, name or os.path.basename(src)))


gate = os.path.join(ARCH, 'logs/gate')
dumpd = os.path.join(ARCH, 'logs/dump')

for n in ('G0_syntax_form_r72.txt', 'G1_targets_r72.txt', 'G2_canary_pin_r72.txt',
          'G2_quotation_pycverify_r72.txt', 'G3_batch_r72.txt', 'G3_batch_r72.err',
          'G3v_pycverify_r72.json', 'G3v_delta_r72.txt', 'G4_stats_r72.txt',
          'G4p_strict_after_r72.txt', 'G5_index_audit_r72.txt', 'G5p_blast_r72.txt',
          'blast72_expected.json', 'G6_battery_ext_r72.txt', 'G7_witness_repro72.txt',
          'G8_artifacts_r72.txt', 'G9_synth_r72.txt',
          'Land72_landproof_r72.txt', 'Land72_replay_r72.txt'):
    copy(os.path.join(C, 'logs', n), gate)
print('gate artifacts copied')

for n in ('prev_fail47_r72.jsonl', 'landed_fail47_r72.jsonl',
          'prev_canary_r72.jsonl', 'landed_canary_r72.jsonl',
          'prev_div48_r72.jsonl', 'landed_div48_r72.jsonl',
          'strict_prev72.json', 'strict_landed_after72.json',
          'index_before72.json', 'repro65_prev.jsonl', 'repro65_landed.jsonl',
          'landed_synth72_r72.jsonl', 'prev_synth72_r72.jsonl'):
    copy(os.path.join(C, 'dump', n), dumpd)
for f in sorted(os.listdir(os.path.join(C, 'dump'))):
    if f.startswith('pv_'):
        copy(os.path.join(C, 'dump', f), dumpd)
for i in range(8):
    copy(os.path.join(C, 'chunks', 'rep%d.json' % i), dumpd)
    copy(os.path.join(C, 'chunks', 'ix%d.json' % i), dumpd, 'ix%d_paths.json' % i)
print('dumps + shards copied')

specd = os.path.join(ARCH, 'specs')
copy(os.path.join(RT, 'merged72_comprehension_generator.py.json'), specd,
     'R72-merged-comprehension.json')
copy(os.path.join(RT, 'fix1', 'specs', 'fix1_comp_split.json'), specd)
copy(os.path.join(RT, 'fix2', 'specs', 'broker_comp_return.json'), specd)
print('specs copied')

batchd = os.path.join(ARCH, 'batches')
for ws in ('diag1', 'fix1', 'fix2'):
    wd = os.path.join(batchd, ws)
    for n in ('BRIEF.md', 'ROUND.md', 'FACTS.md', 'filecat.json', 'targets.md'):
        copy(os.path.join(RT, ws, n), wd)
    sp = os.path.join(RT, ws, 'specs')
    if os.path.isdir(sp):
        for f in sorted(os.listdir(sp)):
            if f.endswith('.json'):
                copy(os.path.join(sp, f), os.path.join(wd, 'specs'))
    sy = os.path.join(RT, ws, 'synth')
    if os.path.isdir(sy):
        os.makedirs(os.path.join(wd, 'synth'), exist_ok=True)
        for root, dirs, files in os.walk(sy):
            if '__pycache__' in root:
                continue
            for f in files:
                if f.endswith(('.py', '.json', '.txt')):
                    rel = os.path.relpath(os.path.join(root, f), sy)
                    dd = os.path.join(wd, 'synth', os.path.dirname(rel))
                    os.makedirs(dd, exist_ok=True)
                    shutil.copy2(os.path.join(root, f), os.path.join(dd, f))
    for d in ('dump',):
        pd = os.path.join(RT, ws, d)
        if os.path.isdir(pd):
            for f in sorted(os.listdir(pd)):
                if f.endswith(('.json', '.txt', '.jsonl', '.md')):
                    copy(os.path.join(pd, f), os.path.join(wd, d))
print('batches copied')

scrd = os.path.join(ARCH, 'scripts')
for f in ('provision72.py', 'prep72.py', 'cand72.py', 'gates72.py',
          'mkmirr_prev72.py', 'merge_g3v71.py', 'mkarchive72.py',
          'replay72check.py', 'targets.md', 'filecat.json'):
    copy(os.path.join(C, f), scrd)
copy(os.path.join(RT, 'targets.md'), scrd, 'targets_round.md')
print('scripts copied')

n = sum(len(fs) for _, _, fs in os.walk(ARCH))
print('archive tree now has %d files under %s' % (n, ARCH))
