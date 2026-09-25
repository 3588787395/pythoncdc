# -*- coding: utf-8 -*-
"""Archive Round 68 evidence into the spec's rounds/round68/ tree (repo docs only).

  python -X utf8 archive68.py

Read-only w.r.t. the decompiler sources; it copies harness dumps / gate logs / batch
artifacts / specs from D:/Temp/opencode/r68gate into the repository's round folder.
"""
import io
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
SPEC = REPO + r'\.trae\specs\region-reduction-30pyc-perfect-10rounds'
GATE = r'D:\Temp\opencode\r68gate\center'
DIAG = r'D:\Temp\opencode\r68gate'
DST = SPEC + r'\rounds\round68'
sys.stdout.reconfigure(encoding='utf-8')

GATES = [
    'G0_syntax_form_r68.txt',
    'G1_single_scheduler.txt',
    'G1_single_flyAccount.txt',
    'G2_canary_post68.log',
    'G2_strict_canary_r68.txt',
    'G3_batch_r68.log',
    'G4_stats_r68.txt',
    'G4p_strict_after_r68.txt',
    'G5_index_audit_r68.txt',
    'G5p_blast_r68.txt',
    'G6_battery_prev_r68.txt',
    'G6_battery_landed_r68.txt',
    'G6_battery_table_r68.txt',
    'G7_witness_repro68.txt',
    'G8_artifacts_r68.txt',
]
DUMPS = [
    'landed15b.jsonl', 'landed_canary2.jsonl', 'landed_bat.jsonl',
    'm68_all15.jsonl', 'm68_canary.jsonl', 'm68_bat.jsonl',
    'landed15_strict.json', 'm68_strict.json',
    'landed_canary_strict.json', 'm68_canary_strict.json',
    'G4p_strict_after_r68.txt', 'G2_strict_canary_r68.txt',
    'prev402.jsonl', 'landed402.jsonl',
    'repro65_prev.jsonl', 'repro65_landed.jsonl',
    'repro68_staged.txt', 'repro68_prev.jsonl', 'repro68_landed.jsonl',
    'landed_canary_post68.jsonl',
    'index_before68.json',
    'G3_batch68.log', 'G3_batch68.err',
    'merged_comments_r68.txt',
    'b1_all15.jsonl', 'b1_canary.jsonl', 'b1_bat.jsonl',
    'b2_all15.jsonl', 'b2_canary.jsonl', 'b2_bat.jsonl',
    'b3_all15.jsonl', 'b3_canary.jsonl', 'b3_bat.jsonl',
    'b4_all15.jsonl', 'b4_canary.jsonl', 'b4_bat.jsonl',
    'b5_all15.jsonl', 'b5_canary.jsonl', 'b5_bat.jsonl',
    'landed_strict.json',
]
TOOLS = ['h62.py', 'mbuild68c.py', 'mkfinal68.py', 'land68.py', 'mkmirr_prev68.py',
         'closeout67.py', 'blast67.py', 'audit5_g5_67.py', 'sstrict67.py',
         'strict_repo67.py', 'battable67.py', 'mk_spec.py', 'all15.txt', 'canary.txt',
         'battery45.txt', 'all402.txt', 'g8_artifacts68.py', 'archive68.py',
         'mkreadme68.py']
SPECS = [
    r'D:\Temp\opencode\r68gate\m68_region_analyzer.py.json',
    r'D:\Temp\opencode\r68gate\m68_region_ast_generator.py.json',
    r'D:\Temp\opencode\r68gate\center\ADR1_contract_fix.md',
    r'D:\Temp\opencode\r68gate\diag1\specs\cand_r68_b1.json',
    r'D:\Temp\opencode\r68gate\diag2\specs\cand_r68_else_join_cut.json',
    r'D:\Temp\opencode\r68gate\diag3\specs\cand_r68b2_final_gen.json',
    r'D:\Temp\opencode\r68gate\diag3\specs\cand_r68b2_andchain.json',
    r'D:\Temp\opencode\r68gate\diag4\specs\cand_r68b3_combo.json',
    r'D:\Temp\opencode\r68gate\diag5\specs\cand_r68_wizapib.json',
    r'D:\Temp\opencode\r68gate\diag6\specs\cand_r68b5_initc.json',
]
# batch label -> (workspace, batch folder name); b0 = diag2 (candidate withdrawn, ADR-1)
BATCHES = [('diag1', 'b1'), ('diag2', 'b0'), ('diag3', 'b2'), ('diag4', 'b3'),
           ('diag5', 'b4'), ('diag6', 'b5')]


def cp(src, dst):
    if not os.path.isfile(src):
        print('  MISS %s' % src)
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main():
    logs = DST + r'\logs\gate'
    dumpd = DST + r'\logs\dump'
    os.makedirs(logs, exist_ok=True)
    os.makedirs(dumpd, exist_ok=True)
    n = 0
    for g in GATES:
        n += cp(os.path.join(GATE, 'dump', g), os.path.join(logs, g))
    for d in DUMPS:
        n += cp(os.path.join(GATE, 'dump', d), os.path.join(dumpd, d))
    for t in TOOLS:
        n += cp(os.path.join(GATE, t), os.path.join(DST, 'logs', t))
    for s in SPECS:
        n += cp(s, os.path.join(DST, 'specs', os.path.basename(s)))
    for ws, lab in BATCHES:
        src = os.path.join(DIAG, ws)
        dd = os.path.join(DST, 'batches', lab + '_' + ws)
        os.makedirs(dd, exist_ok=True)
        for name in ['FACTS.md', 'ANALYSIS.md']:
            n += cp(os.path.join(src, name), os.path.join(dd, name))
        sp = os.path.join(src, 'specs')
        if os.path.isdir(sp):
            os.makedirs(os.path.join(dd, 'specs'), exist_ok=True)
            for f in sorted(os.listdir(sp)):
                if f.startswith('cand_r68') or f.startswith('cand_r67'):
                    n += cp(os.path.join(sp, f), os.path.join(dd, 'specs', f))
        sy = os.path.join(src, 'synth')
        if os.path.isdir(sy):
            os.makedirs(os.path.join(dd, 'synth'), exist_ok=True)
            for f in sorted(os.listdir(sy)):
                p = os.path.join(sy, f)
                if os.path.isfile(p) and not f.endswith('.pyc'):
                    n += cp(p, os.path.join(dd, 'synth', f))
    print('archived %d files into %s' % (n, DST))
    # repo .gitignore drops *.log -> keep .txt twins of the two log-named gate files
    for g in ['G2_canary_post68', 'G3_batch_r68']:
        src = os.path.join(logs, g + '.log')
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(logs, g + '.txt'))
            n += 1
    print('total %d files (incl. .txt twins of *.log gate files)' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
