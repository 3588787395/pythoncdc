# -*- coding: utf-8 -*-
"""Round 13 复现电池（测试工程师交付物）。

对 test_repros/round13/r13_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r13/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译该 .pyc，输出仍写到 D:/Temp/r13/build/；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较，
     报告 MATCH / MISMATCH。

判定完全委托给 _r10_strict_check（仅 import，不复制、不修改）。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round13/run_all.py            # 全部
  PYTHONIOENCODING=utf-8 python test_repros/round13/run_all.py 01 04 13    # 按编号
  PYTHONIOENCODING=utf-8 python test_repros/round13/run_all.py --show-diff  # 打印首个差异
  PYTHONIOENCODING=utf-8 python test_repros/round13/run_all.py --strict     # 有 UNEXPECTED/REGRESSED 时退出码 1

EXPECT 四态：MISMATCH（缺陷复现）/ MATCH（负对照）/
SENTINEL（曾复现、已被修复，实测必须 MATCH，否则记 REGRESSED）/
UNCONFIRMED（目标缺陷真实存在但该形状未复现，实测应为 MATCH，不计失败）。
根因分类与逐类证据见同目录 ANALYSIS.md / MAPPING.md。
"""
import importlib.util
import marshal
import py_compile
import shutil
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

# 唯一真值尺子（只 import，不修改）
from _r10_strict_check import _load_map, strict_compare  # noqa: E402

from pycdc import decompile_pyc  # noqa: E402

BUILD = Path(r'D:/Temp/r13/build')
BUILD.mkdir(parents=True, exist_ok=True)

# 期望值：'MISMATCH' = 该复现应能复现缺陷；'MATCH' = 负对照，必须一致；
# 'UNCONFIRMED' = 目标缺陷真实存在但该形状**未复现**（当前实测应为 MATCH），
#                不计入失败，也不得当作修复依据。详见 ANALYSIS.md。
# 'SENTINEL'    = 该形状曾经复现缺陷、现已被修复；保留为**回归哨兵**，
#                实测必须为 MATCH，一旦回到 MISMATCH 即为回归。
EXPECT = {
    'r13_01_return_becomes_break': 'SENTINEL',
    'r13_02_spurious_continue_loop': 'SENTINEL',  # fixed by R19-A
    'r13_03_join_tail_sunk_after_loop': 'MISMATCH',
    'r13_04_join_tail_sunk_into_branch': 'MISMATCH',
    'r13_05_dict_two_comprehensions': 'SENTINEL',
    'r13_06_if_not_none_else_return': 'MISMATCH',
    'r13_07_stmt_dropped_before_break': 'MISMATCH',
    'r13_08_chain_then_if_return_dropped': 'MISMATCH',
    'r13_09_nested_except_return_merge': 'MISMATCH',
    'r13_10_empty_if_pass_duplicated': 'MISMATCH',
    'r13_11_loop_prologue_sunk': 'UNCONFIRMED',
    'r13_12_elif_branch_rotated': 'MISMATCH',
    'r13_13_bare_raise_sunk': 'MISMATCH',
    'r13_14_neg_plain_if_chain': 'MATCH',
    'r13_15_neg_dict_two_scalars': 'MATCH',
    'r13_17_neg_nested_loops': 'MATCH',
    'r13_16_neg_try_except_return': 'MATCH',
    'r13_18_join_tail_wide_chain': 'MISMATCH',
    'r13_19_spurious_continue_elif': 'UNCONFIRMED',
    'r13_20_for_else_break_lost': 'MISMATCH',
    'r13_21_chain_arm_try_rotation': 'MISMATCH',
    'r13_22_chain_arm_if_no_else': 'MISMATCH',
    'r13_23_neg_two_fallthrough_arms': 'MATCH',
    'r13_24_neg_non_fallthrough_arm': 'MATCH',
    'r13_25_neg_chain_boundary': 'MATCH',
}


def _compile(src_py: Path, out_pyc: Path):
    """编译 .py -> .pyc（写到指定位置，不产生 __pycache__ 残留）。"""
    tmp = BUILD / (out_pyc.stem + '.c.tmp')
    pyc = py_compile.compile(str(src_py), cfile=str(tmp), doraise=True, quiet=2)
    shutil.move(str(pyc), str(out_pyc))
    return out_pyc


def run_one(repro_py: Path, show_diff=False):
    name = repro_py.stem
    src = BUILD / (name + '.py')
    shutil.copyfile(str(repro_py), str(src))
    orig_pyc = BUILD / (name + '.pyc')
    _compile(src, orig_pyc)

    decomp_src = BUILD / (name + '_DECOMP.py')
    try:
        text = decompile_pyc(str(orig_pyc))
    except Exception as e:
        return (name, 'ERROR', 'decompile raised %s: %s' % (type(e).__name__, e), [])
    if text is None:
        return (name, 'ERROR', 'decompile returned None', [])
    decomp_src.write_text(text, encoding='utf-8')

    decomp_pyc = BUILD / (name + '_DECOMP.pyc')
    try:
        _compile(decomp_src, decomp_pyc)
    except Exception as e:
        return (name, 'ERROR', 'recompile failed: %s' % e, [])

    a = _load_map(str(orig_pyc))
    b = _load_map(str(decomp_pyc))
    defects = []
    for key in sorted(set(a) & set(b)):
        kind, msg, is_defect = strict_compare(a[key], b[key])
        if kind is not None:
            defects.append('%s [%s] %s' % (key, kind, msg))
    verdict = 'MISMATCH' if defects else 'MATCH'
    return (name, verdict, '', defects)


def main():
    sel = [x for x in sys.argv[1:] if x not in ('--show-diff', '--strict')]
    show = '--show-diff' in sys.argv
    strict = '--strict' in sys.argv
    reps = sorted(HERE.glob('r13_*.py'))
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    n_bad = n_good = n_err = n_unexp = n_unconf = 0
    for r in reps:
        try:
            name, verdict, err, defects = run_one(r, show)
        except Exception:
            print('%-42s ERROR (harness)' % r.stem)
            traceback.print_exc()
            n_err += 1
            continue
        exp = EXPECT.get(name, '?')
        if verdict == 'ERROR':
            print('%-42s ERROR  %s' % (name, err))
            n_err += 1
            continue
        ok = (verdict == exp)
        if exp == 'UNCONFIRMED':
            # 未复现的占位形状：实测应为 MATCH，出现 MISMATCH 反而说明该形状又活了
            tag = 'NOT-REPRO' if verdict == 'MATCH' else 'REVIVED!'
            n_unconf += 1
            if verdict == 'MISMATCH':
                n_unexp += 1
        elif exp == 'SENTINEL':
            tag = 'OK-SENTINEL' if verdict == 'MATCH' else 'REGRESSED!'
            if verdict == 'MISMATCH':
                n_unexp += 1
        else:
            tag = 'AS-EXPECTED' if ok else 'UNEXPECTED'
            if not ok:
                n_unexp += 1
        print('%-42s %-8s (expect %-11s) %s  %s'
              % (name, verdict, exp, tag, defects[0][:78] if defects else ''))
        if show and defects:
            for dd in defects[:4]:
                print('      - %s' % dd)
        if verdict == 'MISMATCH':
            n_bad += 1
        else:
            n_good += 1
    print()
    print('repros=%d  MISMATCH=%d  MATCH=%d  ERROR=%d  UNEXPECTED=%d  NOT-REPRODUCED=%d'
          % (len(reps), n_bad, n_good, n_err, n_unexp, n_unconf))
    if strict:
        return 0 if (n_err == 0 and n_unexp == 0) else 1
    return 0 if n_err == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
