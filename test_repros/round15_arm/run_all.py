# -*- coding: utf-8 -*-
"""Round 15-B 复现电池（测试工程师交付物）：父臂吸入嵌套区域的内部块 → 中间 if 丢失。

对 test_repros/round15_arm/r15a_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r15arm/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译该 .pyc，输出仍写到 D:/Temp/r15arm/build/；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较，
     报告 MATCH / MISMATCH。

判定完全委托给 _r10_strict_check（仅 import，不复制、不修改）。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round15_arm/run_all.py
  PYTHONIOENCODING=utf-8 python test_repros/round15_arm/run_all.py 01 07
  PYTHONIOENCODING=utf-8 python test_repros/round15_arm/run_all.py --show-diff
  PYTHONIOENCODING=utf-8 python test_repros/round15_arm/run_all.py --strict

EXPECT 四态（沿用 round13/run_all.py 语义）：
  MISMATCH   = 缺陷复现（实测必须 MISMATCH）
  MATCH      = 负对照（实测必须 MATCH，用于隔离触发成分）
  SENTINEL   = 曾复现、已被修复；实测必须 MATCH，否则记 REGRESSED
  UNCONFIRMED= 目标缺陷真实存在但该形状未复现；实测应为 MATCH，不计失败
首轮实测（修复前）：9 MISMATCH / 3 MATCH；
  06/08 两个「负对照」假设被否证（臂体含任意嵌套区域即触发，不限 Try）。
Round 15-B H1+H2（else 臂双角色块豁免 + owner 发射权与识别解耦）落地后实测：
  03/04/05/06/11 已翻为 SENTINEL（MATCH）。
  01（61→45）/02（73→57）仍 MISMATCH —— if 已找回，但臂内嵌套的 TryExceptRegion
    不是该 if 的 children（分析层未建父子），_if_generate_then_branch 先把块 84
    当 BoolOp 归并点标记为 generated，_try_entry_generate 因此空转，try 丢失。
  08（41→19）仍 MISMATCH —— region_ast_generator.py:10969 的 R36 否决仍生效：
    分析层 guard_clause_prefix_end 只在「后继 if 条件是裸同名变量」时写下，
    `if flag != 'q':` 这种比较式条件拿不到豁免（属分析层判据过窄）。
  09（39 vs 48）仍 MISMATCH —— 顶层语句序列里的双角色块把赋值与 if 条件各发一遍，
    与 else 臂路径无关（另一条发射链，H1/H2 未触及）。
根因定位见 rounds/round15/elsearm-design.md。
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

BUILD = Path(r'D:/Temp/r15arm/build')
BUILD.mkdir(parents=True, exist_ok=True)

EXPECT = {
    'r15a_01_anchor_is_valid_quarter': 'MISMATCH',
    'r15a_02_anchor_module_scope': 'MISMATCH',
    'r15a_03_anchor_or_boolop': 'SENTINEL',
    'r15a_04_anchor_try_finally': 'SENTINEL',
    'r15a_05_anchor_nested_for': 'SENTINEL',
    'r15a_06_anchor_nested_if': 'SENTINEL',
    'r15a_07_neg_no_boolop_prefix': 'MATCH',
    'r15a_08_neg_if_condition_compare': 'MISMATCH',
    'r15a_09_anchor_try_in_elif_arm': 'MISMATCH',
    'r15a_10_anchor_nested_try_inside_try': 'UNCONFIRMED',
    'r15a_11_anchor_two_nested_regions': 'SENTINEL',
    'r15a_12_neg_no_inner_if': 'MATCH',
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
    reps = sorted(HERE.glob('r15a_*.py'))
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
        print('%-44s %-8s (expect %-11s) %-11s %s  %s'
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
