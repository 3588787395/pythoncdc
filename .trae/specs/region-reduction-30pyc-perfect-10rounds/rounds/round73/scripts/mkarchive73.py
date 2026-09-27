# -*- coding: utf-8 -*-
"""Round 73 archive packer: copy gate/dump/spec/brief/script artifacts from the
r73gate workspace into the repo archive tree.  Read-only w.r.t. the gate workspaces."""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
RT = r'D:/Temp/opencode/r73gate'
C = RT + '/center'
ARCH = REPO + '/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round73'


def copy(src, dst_dir, name=None):
    if not os.path.isfile(src):
        print('  !! missing', src)
        return
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, name or os.path.basename(src)))


copy(os.path.join(C, 'OUTCOME73.md'), ARCH, 'OUTCOME.md')

gate = os.path.join(ARCH, 'logs/gate')
dumpd = os.path.join(ARCH, 'logs/dump')
copy(os.path.join(C, 'EVIDENCE73.md'), os.path.join(ARCH, 'logs'), 'EVIDENCE.md')

for n in ('G0_syntax_form_r73.txt', 'G1_targets_r73.txt', 'G2_canary_pin_r73.txt',
          'G2_quotation_pycverify_r73.txt', 'G4_stats_r73.txt', 'G4p_strict_after_r73.txt',
          'G5_index_audit_r73.txt', 'G5p_blast_r73.txt', 'blast73_expected.json',
          'G6_battery_ext_r73.txt', 'G7_witness_repro73.txt', 'G8_artifacts_r73.txt',
          'G9_synth_r73.txt', 'G3v_pycverify_r73.json', 'G3v_delta_r73.txt',
          'Land73_landproof_r73.txt', 'Land73_replay_r73.txt', 'TRYVERDICT_r73.txt'):
    copy(os.path.join(C, 'logs', n), gate)
copy(os.path.join(C, 'dump', 'G3_batch_r73.txt'), gate)
copy(os.path.join(C, 'dump', 'G3_batch_r73.err'), gate)
print('gate artifacts copied')

for n in ('prev_c.jsonl', 'landed_c.jsonl', 'landed_c2.jsonl', 'm73_merged.jsonl',
          'index_before73.json', 'strict_prev73.json', 'strict_landed73.json',
          'strict_prev73.txt', 'strict_landed73.txt', 'strict_m73.json', 'strict_m73.txt',
          'repro65_prev.jsonl', 'repro65_landed.jsonl', 'repro65_m73.jsonl',
          'reprolist65.txt', 'batt_m73.txt', 'batt_prev_landed73.txt',
          'adr73_m73.json', 'adr73_m73.txt', 'adr73_pad6.json', 'adr73_pad6.txt',
          'adr73_surgm.json', 'adr73_surgm.txt', 'adr73_absm.json', 'adr73_absm.txt',
          'mand_pad6.json', 'mand_surgm.json', 'tryverdict73.txt', 'firstdiv73.txt',
          'exctable_diff73.txt', 'fam73_pad_r73.json', 'list41.txt', 'list41c.txt',
          'synth73.txt', 'mand_synth_prev_r73.json', 'mand_synth_landed_r73.json',
          'prev_synth73_r73.jsonl', 'landed_synth73_r73.jsonl',
          'g9_h62_prev.txt', 'g9_h62_landed.txt', 'g9_mand_prev.txt', 'g9_mand_landed.txt'):
    copy(os.path.join(C, 'dump', n), dumpd)
for f in ('adr73_pad6.err.txt',):
    copy(os.path.join(C, 'dump', f), dumpd)
for i in range(8):
    copy(os.path.join(C, 'chunks', 'rep%d.json' % i), dumpd)
    copy(os.path.join(C, 'chunks', 'ix%d.json' % i), dumpd, 'ix%d.json' % i)
for f in sorted(os.listdir(os.path.join(C, 'dump'))):
    if f.startswith(('mand_m73_s', 'mand_absm_s', 'm73_s', 'mand_rest')):
        copy(os.path.join(C, 'dump', f), dumpd)
print('dumps + shards copied')

specd = os.path.join(ARCH, 'specs')
copy(os.path.join(RT, 'm73_region_ast_generator.py.json'), specd,
     'R73-m73-region_ast_generator.json')
copy(os.path.join(RT, 'm73_region_analyzer.py.json'), specd, 'R73-m73-region_analyzer.json')
for ws, names in (('fix1', ('pad_e2fix.json', 'pad_e2.json', 'pad_e1.json',
                            'pad_r2m.json', 'pad_r2m_r71.json')),
                  ('fix2', ('absm_abs1_abs2.json', 'abs2_r57b_jump_target.json',
                            'abs1_nested_same_exit.json')),
                  ('fix3', ('merged_analyzer.json', 'polarity_gen.json',
                            'polarity.json', 'ternary.json', 'exctable.json', 'quote.json'))):
    for n in names:
        copy(os.path.join(RT, ws, 'specs', n), specd)
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
for f in ('gates73.py', 'merge_g3v73.py', 'g4g8replay73.py', 'g9run73.py',
          'tryverdict_summary73.py', 'mkarchive73.py'):
    copy(os.path.join(C, f), scriptd)
for f in ('mkfinal73.py', 'mbuild73.py', 'land73.py', 'h62.py', 'adr73.py',
          'mkmirr_prev73.py', 'fixprev73.py', 'sstrict67.py', 'closeout69.py'):
    copy(os.path.join(C, f), scriptd)
copy(os.path.join(C, 'gates73.py'), scriptd)
# briefs (rounds/round73/scripts/briefs) were committed at round73 start -- not overwritten here
print('scripts copied')

n = 0
for root, dirs, files in os.walk(ARCH):
    for f in files:
        n += 1
print('ROUND 73 ARCHIVE: %d files under %s' % (n, ARCH))
