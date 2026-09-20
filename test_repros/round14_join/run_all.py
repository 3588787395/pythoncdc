# -*- coding: utf-8 -*-
"""Round 14-J 复现电池（测试工程师交付物）：if 臂体含 try 时 then 区被截断。

对 test_repros/round14_join/r14j_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r14join/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译该 .pyc，输出仍写到 D:/Temp/r14join/build/；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较，
     报告 MATCH / MISMATCH。

判定完全委托给 _r10_strict_check（仅 import，不复制、不修改）。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round14_join/run_all.py
  PYTHONIOENCODING=utf-8 python test_repros/round14_join/run_all.py 02 12
  PYTHONIOENCODING=utf-8 python test_repros/round14_join/run_all.py --show-diff
  PYTHONIOENCODING=utf-8 python test_repros/round14_join/run_all.py --strict

EXPECT 四态（沿用 round13/run_all.py 语义）：
  MISMATCH   = 缺陷复现（实测必须 MISMATCH）
  MATCH      = 负对照（实测必须 MATCH，用于隔离触发成分）
  SENTINEL   = 曾复现、已被修复；实测必须 MATCH，否则记 REGRESSED
  UNCONFIRMED= 目标缺陷真实存在但该形状未复现；实测应为 MATCH，不计失败
根因定位见同目录 ANALYSIS.md。
"""
import py_compile
import shutil
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

# 唯一真值尺子（只 import，不修改）
from _r10_strict_check import _load_map, _compile_map, strict_compare, filtered  # noqa: E402

from pycdc import decompile_pyc  # noqa: E402

BUILD = Path(r'D:/Temp/r14join/build')
BUILD.mkdir(parents=True, exist_ok=True)

EXPECT = {
    'r14j_01_neg_if_import_only': 'MATCH',
    'r14j_02_real_shape_module': 'MISMATCH',
    'r14j_03_one_stmt_prefix_try_except': 'MISMATCH',
    'r14j_04_assign_prefix_try_except': 'MISMATCH',
    'r14j_05_two_assign_prefix_try_except': 'MISMATCH',
    'r14j_06_try_first_and_only_stmt': 'MISMATCH',
    'r14j_07_try_except_else_in_then': 'MISMATCH',
    'r14j_08_try_finally_in_then': 'MISMATCH',
    'r14j_09_try_in_else_arm': 'MISMATCH',
    'r14j_10_try_in_elif_arm': 'MISMATCH',
    'r14j_11_function_scope_boolop_try': 'MISMATCH',
    'r14j_12_no_flag_retest_module': 'MISMATCH',
    'r14j_13_neg_plain_flag_no_boolop': 'MATCH',
    'r14j_14_neg_ternary_flag': 'MATCH',
    'r14j_15_neg_non_adjacent_boolop': 'MATCH',
    'r14j_16_neg_if_inside_try': 'MATCH',
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
    if show_diff:
        for key in sorted(set(a) & set(b)):
            na, nb = len(filtered(a[key])), len(filtered(b[key]))
            print('      %-24s orig=%d decomp=%d' % (key, na, nb))
    return (name, verdict, '', defects)


def main():
    sel = [x for x in sys.argv[1:] if x not in ('--show-diff', '--strict')]
    show = '--show-diff' in sys.argv
    strict = '--strict' in sys.argv
    reps = sorted(HERE.glob('r14j_*.py'))
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    n_bad = n_good = n_err = n_unexp = n_unconf = 0
    for r in reps:
        try:
            name, verdict, err, defects = run_one(r, show)
        except Exception:
            print('%-44s ERROR (harness)' % r.stem)
            traceback.print_exc()
            n_err += 1
            continue
        exp = EXPECT.get(name, '?')
        if verdict == 'ERROR':
            print('%-44s ERROR  %s' % (name, err))
            n_err += 1
            continue
        ok = (verdict == exp)
        if exp == 'UNCONFIRMED':
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
        print('%-44s %-8s (expect %-9s) %-11s %s  %s'
              % (name, verdict, exp, tag,
                 'instr=%s' % _instr_hint(name),
                 defects[0][:78] if defects else ''))
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


def _instr_hint(name):
    """该形状模块级语义指令数（orig），用于快速判断规模；失败返回 '?'。"""
    pyc = BUILD / (name + '.pyc')
    try:
        return str(len(filtered(_load_map(str(pyc))['<module>'])))
    except Exception:
        return '?'


if __name__ == '__main__':
    sys.exit(main())
