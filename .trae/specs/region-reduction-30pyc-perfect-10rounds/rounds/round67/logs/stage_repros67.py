# -*- coding: utf-8 -*-
"""Round 67 stage-3: copy the round's minimal repros from agent workspaces into
F:/Downloads/pythoncdc-main/test_repros/round67_<batch>/ and compile the matching .pyc.

  python -X utf8 center/stage_repros67.py [--compile]

Only .py sources are copied (the repo gitignores *.pyc, .gitignore:2); .pyc files are produced
locally with py_compile so the battery can run them. Nothing in core/ or *OK.py is touched.
Re-running refreshes the same files (idempotent).
"""
import io
import os
import py_compile
import shutil
import sys

REPO = r'F:/Downloads/pythoncdc-main'
G = r'D:/Temp/opencode/r67gate'
sys.stdout.reconfigure(encoding='utf-8')

BATCH = {
    # dir name -> (workspace, [stems], what it witnesses)
    'round67_diag1': ('diag1', ['r67_join_after_noelse'],
                      'j3 循环发射中认领无自身汇合点的顶层兄弟区域'),
    'round67_diag2': ('diag2', ['r67_guard_tern'],
                      'or-chain 尾段自建守卫三元（common_func::handle_exrights）'),
    'round67_diag4': ('diag4', ['r67d4_handler_continue', 'r67d4_controls'],
                      'try-handler 回边显式 continue + 反向控制件'),
    'round67_diag5': ('diag5', ['r67_ccprefix', 'r67_ccprefix2', 'r67_site2'],
                      '值语境链式比较三元的前导语句同层拆分（生成器半边 + analyzer 半边成对）'),
    'round67_diag3': ('diag3', ['r67d3_return_sink', 'r67d3_return_tern',
                                'r67d3_lost_continue', 'r67d3_lostreturn'],
                      'bare-RETURN_VALUE 后继汇点（中心按 Σ|Δ| 否决，留档）'),
    'round67_diag6': ('diag6', ['r67d6_boolop_ternary', 'r67d6_boolop_ternary2',
                               'r67d6_whiletrue_headif'],
                      'comprehension 三元测试的 boolop 段丢失 + while-True 头块换位（单侧否决）'),
}

do_compile = '--compile' in sys.argv
n = c = 0
for d, (ws, stems, why) in sorted(BATCH.items()):
    dst_dir = os.path.join(REPO, 'test_repros', d)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    for stem in stems:
        src_py = os.path.join(G, ws, 'synth', stem + '.py')
        if not os.path.isfile(src_py):
            for extra in ('', 'synth2'):
                alt = os.path.join(G, ws, 'synth', extra, stem + '.py')
                if os.path.isfile(alt):
                    src_py = alt
                    break
        assert os.path.isfile(src_py), 'missing repro source %s' % src_py
        shutil.copyfile(src_py, os.path.join(dst_dir, stem + '.py'))
        n += 1
        if do_compile:
            pyc = os.path.join(dst_dir, stem + '.pyc')
            py_compile.compile(os.path.join(dst_dir, stem + '.py'), cfile=pyc, doraise=True)
            assert os.path.isfile(pyc), 'no pyc for %s' % stem
            c += 1
    io.open(os.path.join(dst_dir, 'README.md'), 'w', encoding='utf-8', newline='\n').write(
        '# %s\n\n来源 `D:/Temp/opencode/r67gate/%s`；见证：%s。\n'
        '`.pyc` 由 `python -X utf8 center/stage_repros67.py --compile` 本机生成，仓库只入库 `.py`'
        '（`.gitignore` 忽略 `*.pyc`）。\n' % (d, ws, why))
    print('%-16s %-24s %s' % (d, ' '.join(stems), why[:40]))
print('staged %d .py sources (%d .pyc compiled=%s) under test_repros/round67_*' % (n, c, do_compile))
