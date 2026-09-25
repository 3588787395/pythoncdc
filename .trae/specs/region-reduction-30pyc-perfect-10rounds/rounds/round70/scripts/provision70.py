# -*- coding: utf-8 -*-
"""Round 70 step 0: provision the centre workspace.  IDEMPOTENT (re-running only rewrites r70gate).

  python -X utf8 provision70.py

Copies the proven R69 instruments from D:/Temp/opencode/r69gate/center into
D:/Temp/opencode/r70gate/center, retargeting only workspace-root string literals
(r69gate -> r70gate, mirr_m69 -> mirr_m70, build_m69 -> build_m70) and renaming the
build/merge/landing chain to the round-70 prefix.  PY_FILES includes closeout69.py
verbatim (its battery repro_list already covers the round68/69 witnesses) per the R69
handover.  Nothing is executed and no repository file is touched.
"""
import io
import os
import shutil
import sys

SRC = r'D:/Temp/opencode/r69gate/center'
DST = r'D:/Temp/opencode/r70gate/center'
sys.stdout.reconfigure(encoding='utf-8')

# battery list must be the round-69 one (covers round68/69 witnesses) -- R69 handover
PY_FILES = ['h62.py', 'align.py', 'regdump.py', 'disf.py', 'nhunks.py', 'cstrict.py',
            'cstrict67.py', 'sstrict67.py', 'strict_repo67.py', 'closeout69.py',
            'battable67.py', 'dumpfn.py', 'mk_spec.py', 'probe_chain.py', 'blast67.py',
            'audit5_g5_67.py', 'nested_diff.py']
CHAIN = {'mbuild69c.py': 'mbuild70.py', 'mbuild69.py': 'mbuild70_orig.py',
         'mkfinal69.py': 'mkfinal70.py', 'land69.py': 'land70.py',
         'gitpush_redact69.py': 'gitpush_redact70.py', 'mkmirr_prev69.py': 'mkmirr_prev70.py',
         'mkarchive69.py': 'mkarchive70.py', 'replay69.py': 'replay70.py',
         'g8_artifacts69.py': 'g8_artifacts70.py', 'append_tasks69.py': 'append_tasks70.py',
         'cadelta69.py': 'cadelta70.py', 'mkc69.py': 'mkc70.py',
         'mkcloseout69.py': 'mkcloseout70.py', 'patch_copy69.py': 'patch_copy70.py',
         'patch_evidence69.py': 'patch_evidence70.py'}
TXT_FILES = ['battery.txt', 'canary.txt', 'shapes_r63.txt', 'all402.txt', 'all16.txt',
             'targets10.txt']
EXTRA = ['BRIEF_TEMPLATE.md', 'msg69.txt', 'batch_r69_stdout.txt']


def retarget(text):
    text = text.replace('D:/Temp/opencode/r69gate', 'D:/Temp/opencode/r70gate')
    text = text.replace(r'D:\Temp\opencode\r69gate', r'D:\Temp\opencode\r70gate')
    text = text.replace('r69gate', 'r70gate')
    text = text.replace('mirr_m69', 'mirr_m70')
    text = text.replace('build_m69', 'build_m70')
    return text


def provision_diag(target, files, txt_files):
    os.makedirs(target, exist_ok=True)
    for sub in ('dump', 'specs', 'synth', 'logs'):
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    n = 0
    for f in files:
        io.open(os.path.join(target, f), 'w', encoding='utf-8', newline='\n').write(
            retarget(io.open(os.path.join(DST, f), encoding='utf-8').read()))
        n += 1
    for f in txt_files:
        shutil.copyfile(os.path.join(DST, f), os.path.join(target, f))
    print('%s: %d files' % (os.path.basename(target), n))


def main():
    os.makedirs(DST, exist_ok=True)
    for sub in ('dump', 'specs', 'synth', 'logs'):
        os.makedirs(os.path.join(DST, sub), exist_ok=True)
    n = 0
    for f in PY_FILES:
        src = os.path.join(SRC, f)
        assert os.path.isfile(src), f
        io.open(os.path.join(DST, f), 'w', encoding='utf-8', newline='\n').write(
            retarget(io.open(src, encoding='utf-8').read()))
        n += 1
    for src_name, dst_name in sorted(CHAIN.items()):
        src = os.path.join(SRC, src_name)
        assert os.path.isfile(src), src_name
        io.open(os.path.join(DST, dst_name), 'w', encoding='utf-8', newline='\n').write(
            retarget(io.open(src, encoding='utf-8').read()))
        n += 1
    for f in TXT_FILES + EXTRA:
        src = os.path.join(SRC, f)
        if not os.path.isfile(src):
            print('  skip missing %s' % f)
            continue
        shutil.copyfile(src, os.path.join(DST, f))
        n += 1
    print('center: %d files' % n)
    # diagnose workspaces from batches.txt (same format as R69)
    root = os.path.dirname(DST)
    bpath = os.path.join(root, 'batches.txt')
    if os.path.isfile(bpath):
        diag_instr = list(PY_FILES)
        batches = [l.split() for l in io.open(bpath, encoding='utf-8') if l.strip()]
        for row in batches:
            tag, nfiles, _gap, paths = row[0], int(row[1]), row[2], row[3:]
            assert len(paths) == nfiles, row
            d = os.path.join(root, tag)
            provision_diag(d, diag_instr, TXT_FILES)
            io.open(os.path.join(d, 'targets.txt'), 'w', encoding='utf-8', newline='\n').write(
                '\n'.join(paths) + '\n')
            shutil.copyfile(os.path.join(root, '%s_targets.md' % tag),
                            os.path.join(d, 'targets.md'))
            shutil.copyfile(os.path.join(DST, 'BRIEF_TEMPLATE.md'),
                            os.path.join(d, 'BRIEF.md'))
            print('   %s targets=%s' % (tag, [os.path.basename(p) for p in paths]))


if __name__ == '__main__':
    main()
