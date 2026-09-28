# -*- coding: utf-8 -*-
"""Round 74 archive packer: copy gate/dump/spec/brief/script artifacts from the
r74gate workspace into the repo archive tree.  Read-only w.r.t. the gate workspaces."""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
RT = r'D:/Temp/opencode/r74gate'
C = RT + '/center'
ARCH = REPO + '/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round74'
ARM = os.environ.get('R74ARM', 'absj3')


def copy(src, dst_dir, name=None):
    if not os.path.isfile(src):
        print('  !! missing', src)
        return
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, name or os.path.basename(src)))


copy(os.path.join(C, 'OUTCOME74.md'), ARCH, 'OUTCOME.md')

gate = os.path.join(ARCH, 'logs/gate')
dumpd = os.path.join(ARCH, 'logs/dump')
copy(os.path.join(C, 'EVIDENCE74.md'), os.path.join(ARCH, 'logs'), 'EVIDENCE.md')

for n in ('G0_syntax_form_r74.txt', 'G1_targets_r74.txt', 'G2_canary_pin_r74.txt',
          'G2_quotation_pycverify_r74.txt', 'G4_stats_r74.txt', 'G4p_strict_after_r74.txt',
          'G5_index_audit_r74.txt', 'G5p_blast_r74.txt', 'blast73_expected.json',
          'G6_battery_ext_r74.txt', 'G7_witness_repro73.txt', 'G8_artifacts_r74.txt',
          'G9_synth_r74.txt', 'G3v_pycverify_r74.json', 'G3v_delta_r74.txt',
          'Land73_landproof_r74.txt', 'Land74_replay_r74.txt', 'TRYVERDICT_r74.txt'):
    copy(os.path.join(C, 'logs', n), gate)
copy(os.path.join(C, 'dump', 'G3_batch_r74.txt'), gate)
copy(os.path.join(C, 'dump', 'G3_batch_r74.err'), gate)
print('gate artifacts copied')

for n in ('prev_c.jsonl', 'prev_c402.jsonl', 'landed_c.jsonl', 'landed_c2.jsonl',
          'index_before73.json', 'strict_prev73.json', 'strict_landed73.json',
          'strict_prev73.txt', 'strict_landed73.txt',
          'strict_%s.json' % ARM, 'strict_%s.txt' % ARM,
          'repro65_prev.jsonl', 'repro65_landed.jsonl', 'repro65_%s.jsonl' % ARM,
          'batt_prev_landed74.txt', 'adr74_%s.json' % ARM, 'adr74_%s.txt' % ARM,
          'adr74_absj.json', 'adr74_absjt.json', 'adr74_pad7_89.json',
          'fam74_r74.json', 'crosstab74.txt', 'tryverdict74.txt',
          'tryverdict_summary74.txt', 'filecat74.json',
          'md_%s_focus9.json' % ARM, 'md_absjt_focus9.json',
          'off_%s_402.jsonl' % ARM, 'off_landed41.jsonl', 'off_absj9_402.jsonl',
          'can_landed.jsonl', 'can_%s.jsonl' % ARM, 'list45.txt', 'tgt45.txt',
          'firstdiv73.txt', 'exctable_diff73.txt', 'tryverdict73.txt'):
    copy(os.path.join(C, 'dump', n), dumpd)
for f in sorted(os.listdir(os.path.join(C, 'dump'))):
    if f.startswith(('mand_%s' % ARM, 'mand_absj_s', 'mand_m74', 'off_%s_s' % ARM,
                     'prev_c_s', 'md_abs', 'sstrict_')):
        copy(os.path.join(C, 'dump', f), dumpd)
print('dumps + shards copied')

specd = os.path.join(ARCH, 'specs')
copy(os.path.join(RT, 'm74_region_ast_generator.py.json'), specd,
     'R74-m74-region_ast_generator.json')
copy(os.path.join(RT, 'm74_region_analyzer.py.json'), specd, 'R74-m74-region_analyzer.json')
for ws in ('fix1', 'fix2', 'fix3'):
    sp = os.path.join(RT, ws, 'specs')
    if os.path.isdir(sp):
        os.makedirs(os.path.join(specd, ws), exist_ok=True)
        for f in sorted(os.listdir(sp)):
            if f.endswith('.json'):
                copy(os.path.join(sp, f), os.path.join(specd, ws))
for f in ('abs2t.json', 'abs2t9.json'):
    copy(os.path.join(C, 'dump', f), specd)
print('specs copied')

batchd = os.path.join(ARCH, 'batches')
for ws in ('diag1', 'fix1', 'fix2', 'fix3'):
    wd = os.path.join(batchd, ws)
    for n in ('BRIEF.md', 'ROUND.md', 'FACTS.md', 'filecat.json', 'targets.md'):
        copy(os.path.join(RT, ws, n), wd)
    sp = os.path.join(RT, ws, 'specs')
    if os.path.isdir(sp):
        os.makedirs(os.path.join(wd, 'specs'), exist_ok=True)
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
print('batches copied')

scriptd = os.path.join(ARCH, 'scripts')
for f in ('gates74.py', 'merge_g3v74.py', 'g4g8replay74.py', 'g9run74.py',
          'tryverdict_summary74.py', 'mkarchive74.py', 'mkfinal74.py', 'mbuild74.py',
          'land74.py', 'h62.py', 'adr73.py', 'mkmirr_prev74.py', 'sstrict67.py',
          'closeout69.py', 'crosstab74.py', 'fam73.py', 'driver74b.py', 'driver74c.py',
          'fam73.py'):
    copy(os.path.join(C, f), scriptd)
print('scripts copied')

n = 0
for root, dirs, files in os.walk(ARCH):
    for f in files:
        n += 1
print('ROUND 74 ARCHIVE: %d files under %s' % (n, ARCH))
