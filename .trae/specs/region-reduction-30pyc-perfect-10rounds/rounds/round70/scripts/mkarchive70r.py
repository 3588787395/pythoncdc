# -*- coding: utf-8 -*-
"""Round 70 archive packer: copy gate/dump/spec/batch/script artifacts from the
r70gate workspace into the repo archive tree. Read-only w.r.t. the gate workspaces."""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
RT = r'D:/Temp/opencode/r70gate'
C = RT + '/center'
ARCH = REPO + '/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round70'


def copy(src, dst_dir, name=None):
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, name or os.path.basename(src)))


def jcopy(txt, dst_dir, name):
    os.makedirs(dst_dir, exist_ok=True)
    io.open(os.path.join(dst_dir, name), 'w', encoding='utf-8', newline='\n').write(txt)


gate = os.path.join(ARCH, 'logs/gate')
dumpd = os.path.join(ARCH, 'logs/dump')

for n in ('G0_syntax_form_r70.txt', 'G1_targets_r70.txt', 'G2_canary_r70.txt',
          'G2_strict_canary_head_r70.txt', 'G2_strict_canary_m70_r70.txt',
          'G3_batch_r70.txt', 'G3_batch_r70.err',
          'G3v_pycverify_r70.json',
          'G4_stats_r70.txt', 'G4p_strict_after_r70.txt', 'G5_index_audit_r70.txt',
          'G5p_blast_r70.txt', 'G6_battery_cands_r70.txt', 'G6_battery_ext_r70.txt',
          'G7_witness_repro70.txt', 'G8_artifacts_r70.txt', 'Land70_landproof_r70.txt'):
    copy(os.path.join(C, 'logs', n), gate)
print('gate artifacts copied')

dumps = ['landed10_r70.jsonl', 'm70_10.jsonl', 'landed_canary_r70.jsonl', 'm70_canary.jsonl',
         'r70c1_10.jsonl', 'r70c1_canary.jsonl', 'r70c2_10.jsonl', 'r70c2_canary.jsonl',
         'r70c2a_mini.jsonl', 'r70c2g_mini.jsonl',
         'r70c3_10.jsonl', 'r70c3_canary.jsonl', 'r70c4_10.jsonl', 'r70c4_canary.jsonl',
         'synth_landed.jsonl', 'synth_r70c1.jsonl', 'synth_r70c3.jsonl', 'synth_r70c4.jsonl',
         'synth_m70.jsonl', 'b4_head.jsonl', 'b4_m70.jsonl', 'h1a.jsonl', 'h1b.jsonl']
for n in dumps:
    p = os.path.join(C, 'dump', n)
    if os.path.isfile(p):
        copy(p, dumpd)
    else:
        print('  !! missing dump', n)
for n in ('strict_landed_r70.json', 'strict_m70_r70.json', 'strict_r70c1_r70.json',
          'strict_r70c3_r70.json', 'strict_r70c4_r70.json',
          'strict_canary_head.json', 'strict_canary_m70.json',
          'strict_b4_head.json', 'strict_b4_m70.json'):
    p = os.path.join(C, 'dump', n)
    if os.path.isfile(p):
        copy(p, dumpd)
    else:
        print('  !! missing dump', n)
for i in range(8):
    copy(os.path.join(C, 'chunks', 'rep%d.json' % i), dumpd)
copy(os.path.join(C, 'dump', 'index_before70.json'), dumpd)
print('dumps copied')

# merged + candidate specs
specs = os.path.join(ARCH, 'specs')
copy(os.path.join(C, 'specs', 'm70_region_analyzer.py.json'), specs, 'm70_region_analyzer.py.json')
copy(os.path.join(C, 'specs', 'cand_r70diag1_exc.json'), specs)
copy(os.path.join(C, 'specs', 'cand_r70diag3_25b.json'), specs)
copy(os.path.join(C, 'specs', 'cand_r70diag4_c3.json'), specs)
copy(os.path.join(C, 'specs', 'cand_r70diag2_af_0.json'), specs)
copy(os.path.join(C, 'specs', 'cand_r70diag2_af_1.json'), specs)
print('specs copied')

# batches: per-diag FACTS + BRIEF + their own spec copies
for d in ('diag1', 'diag2', 'diag3', 'diag4', 'diag5'):
    b = os.path.join(ARCH, 'batches', d)
    for f in ('FACTS.md', 'BRIEF.md', 'targets.md'):
        p = os.path.join(RT, d, f)
        if os.path.isfile(p):
            copy(p, b)
    sd = os.path.join(RT, d, 'specs')
    if os.path.isdir(sd):
        for f in os.listdir(sd):
            if f.endswith('.json'):
                copy(os.path.join(sd, f), b)
# c2 rejection evidence (split arms) as plain readings
ev = []
for n in ('r70c2a_mini.jsonl', 'r70c2g_mini.jsonl'):
    p = os.path.join(C, 'dump', n)
    if os.path.isfile(p):
        ev.append('== %s' % n)
        ev.extend(io.open(p, encoding='utf-8').read().splitlines())
jcopy('\n'.join(ev) + '\n', os.path.join(ARCH, 'batches', 'b0_diag2_rejected'),
      'split_arm_readings.jsonl.txt')
print('batches copied')

# scripts actually used this round
scripts = os.path.join(ARCH, 'scripts')
for n in ('provision70.py', 'gates70a.py', 'gates70b.py', 'mkfinal70.py', 'mbuild70.py',
          'land70.py', 'mkarchive70r.py', 'h62.py', 'closeout69.py', 'blast67.py',
          'audit5_g5_67.py', 'sstrict67.py', 'cstrict67.py', 'g8_artifacts70.py'):
    p = os.path.join(C, n)
    if os.path.isfile(p):
        copy(p, scripts)
    else:
        print('  !! missing script', n)
copy(os.path.join(RT, 'batches.txt'), scripts)
for d in ('diag1', 'diag2', 'diag3', 'diag4', 'diag5'):
    p = os.path.join(RT, '%s_targets.md' % d)
    if os.path.isfile(p):
        copy(p, scripts)
print('scripts copied')

# diag briefs (workspace root copies already archived via scripts; also mirror to batches)
print('archive packed at', ARCH)
