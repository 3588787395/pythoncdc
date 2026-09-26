# -*- coding: utf-8 -*-
"""Round 71 archive packer: copy gate/dump/spec/batch/script artifacts from the
r71gate workspace into the repo archive tree. Read-only w.r.t. the gate workspaces."""
import io
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
RT = r'D:/Temp/opencode/r71gate'
C = RT + '/center'
ARCH = REPO + '/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round71'


def copy(src, dst_dir, name=None):
    if not os.path.isfile(src):
        print('  !! missing', src)
        return
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, name or os.path.basename(src)))


gate = os.path.join(ARCH, 'logs/gate')
dumpd = os.path.join(ARCH, 'logs/dump')

for n in ('G0_syntax_form_r71.txt', 'G1_targets_r71.txt', 'G2_canary_r71.txt',
          'G2_canary_pin_r71.txt', 'G2_quotation_pycverify_r71.txt',
          'G3_batch_r71.txt', 'G3_batch_r71.err',
          'G3v_pycverify_r71.json', 'G3v_delta_r71.txt',
          'G4_stats_r71.txt', 'G4p_strict_after_r71.txt', 'G5_index_audit_r71.txt',
          'G5p_blast_r71.txt', 'G6_battery_ext_r71.txt',
          'G7_witness_repro71.txt', 'G8_artifacts_r71.txt',
          'Land71_landproof_r71.txt', 'Land71_replay_r71.txt',
          'blast71_expected.json'):
    copy(os.path.join(C, 'logs', n), gate)
print('gate artifacts copied')

for n in ('landed56_r71.jsonl', 'm71_56.jsonl', 'landed_canary_r71.jsonl', 'm71_canary.jsonl',
          'c1_56.jsonl', 'c1_canary.jsonl', 'f3ab_56.jsonl',
          'repro65_prev.jsonl', 'repro65_m71.jsonl', 'repro65_landed.jsonl',
          'reprolist65.txt',
          'strict_landed_r71.json', 'strict_m71_r71.json', 'strict_m71_all56.json',
          'strict_landed_div48_c.json', 'strict_m71_f3tgt.json',
          'm71_verdict.md', 'm71_precheck.txt', 'm71_mkfinal.txt', 'm71_union.txt',
          'm71_pv_m71.txt', 'm71_pv_landed56_a.txt', 'm71_sha_changed.txt',
          'm71_strict_ab.txt', 'm71_battery.txt', 'm71_synth.txt', 'm71_quo_pv.txt',
          'c1_verdict.md', 'c1_pv_summary.txt'):
    copy(os.path.join(C, 'dump', n), dumpd)
for i in range(8):
    copy(os.path.join(C, 'chunks', 'rep%d.json' % i), dumpd)
# pyc_index.json as of HEAD(R70), the baseline for G5
blob = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:pyc_index.json'],
                      capture_output=True).stdout
if blob:
    os.makedirs(dumpd, exist_ok=True)
    io.open(os.path.join(dumpd, 'index_before71.json'), 'wb').write(blob)
print('dumps copied')

specs = os.path.join(ARCH, 'specs')
copy(os.path.join(RT, 'm71_region_analyzer.py.json'), specs)
copy(os.path.join(RT, 'm71_region_ast_generator.py.json'), specs)
copy(os.path.join(RT, 'r71f2_region_ast_generator.py.json'), specs)
copy(os.path.join(C, 'specs', 'c1_exception_exit.json'), specs, 'cand_r71c1_exception_exit.json')
for f in ('R71-exception_exit.json', '_v1_rejected_R71-exception_exit.json',
          '_v2_rejected_R71-exception_exit.json'):
    copy(os.path.join(RT, 'fix1', 'specs', f), specs,
         f if not f.startswith('_') else f)
for f in ('r71f2_full.json', 'r71f2_safe.json'):
    copy(os.path.join(RT, 'fix2', 'specs', f), specs)
for f in ('R71-exctable.json', 'R71-exctable-analyzer.json', 'R71-assert.json',
          'R71-analyzer-merged.json'):
    copy(os.path.join(RT, 'fix3', 'specs', f), specs)
print('specs copied')

for d, ws in (('diag1_salvage', 'diag1_salvage'), ('fix1', 'fix1'), ('fix2', 'fix2'),
              ('fix3', 'fix3'), ('diag1', 'diag1')):
    b = os.path.join(ARCH, 'batches', d)
    os.makedirs(b, exist_ok=True)
    src = os.path.join(RT, ws)
    for f in ('BRIEF.md', 'FACTS.md', 'DIAG1_FACTS.md', 'filecat.json'):
        p = os.path.join(src, f)
        if os.path.isfile(p):
            copy(p, b)
    sd = os.path.join(src, 'specs')
    if os.path.isdir(sd):
        for f in sorted(os.listdir(sd)):
            if f.endswith('.json'):
                copy(os.path.join(sd, f), os.path.join(b, 'specs'))
    sdir = os.path.join(src, 'synth')
    if os.path.isdir(sdir):
        for f in sorted(os.listdir(sdir)):
            if f.endswith(('.py', '.txt', '.md')):
                copy(os.path.join(sdir, f), os.path.join(b, 'synth'))
print('batches copied')

scripts = os.path.join(ARCH, 'scripts')
for n in ('provision71.py', 'gates71a.py', 'gates71a_fix.py', 'gates71b.py', 'mkfinal71.py',
          'mbuild71.py', 'land71.py', 'mkarchive71r.py', 'mkmirr_prev71.py', 'mkblast71.py',
          'merge_g3v71.py', 'h62.py', 'closeout69.py', 'audit5_g5_67.py', 'sstrict67.py'):
    copy(os.path.join(C, n), scripts)
copy(os.path.join(RT, 'filecat.json'), scripts)
# round briefs / provision live in the archive already (rounds/round71/scripts, briefs/)
print('scripts copied')
print('archive packed at', ARCH)
