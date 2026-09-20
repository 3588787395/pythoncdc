# -*- coding: utf-8 -*-
"""Round 16-A 复现电池（测试工程师交付物）：if 臂的表达式子区域预生成抢走结构兄弟的入口块。

对 test_repros/round16_arm/r16a_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r16arm/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译该 .pyc，输出仍写到 D:/Temp/r16arm/build/；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较，
     报告 MATCH / MISMATCH。

判定完全委托给 _r10_strict_check（仅 import，不复制、不修改）。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round16_arm/run_all.py
  PYTHONIOENCODING=utf-8 python test_repros/round16_arm/run_all.py 01 07
  PYTHONIOENCODING=utf-8 python test_repros/round16_arm/run_all.py --show-diff
  PYTHONIOENCODING=utf-8 python test_repros/round16_arm/run_all.py --strict

EXPECT 四态（沿用 round13/round15/run_all.py 语义）：
  MISMATCH   = 缺陷复现（实测必须 MISMATCH）
  MATCH      = 负对照（实测必须 MATCH，用于隔离触发成分）
  SENTINEL   = 曾复现、已被修复；实测必须 MATCH，否则记 REGRESSED
  UNCONFIRMED= 目标缺陷真实存在但该形状未复现；实测应为 MATCH，不计失败

受害真源：site-packages/IQCommon/arg_checker.pyc
`<module>.ArgumentChecker._is_valid_quarter`，实测 seq_len orig=90 decomp=74，
丢的 16 条全部是 try 外壳 + except 处理块（`238 JUMP_FORWARD 290` 起、
`240 PUSH_EXC_INFO` … `288 RERAISE 1`）；if / 守卫 / else 臂都在。

机制（结构层已排除：区域树里 TryExceptRegion@94.parent **就是** IfRegion@86，
IfRegion@86.children = [Region@92, TryExceptRegion@94, BoolOpRegion@94,
TernaryRegion@94] —— round15 记录的「分析层未建父子」结论被否证）：
`_if_generate_then_branch` 的表达式子区域预生成（region_ast_generator.py:13947 起、
标记在 14070-14071）把 BoolOpRegion@94 的 blocks 全量写进 generated_blocks，
而这批块恰好等于 TryExceptRegion@94.try_blocks；随后 `_process_if_blocks` 的
`_try_entry_generate`（20153-20167，守卫 20154-20155）见入口已 generated 即空转，
try/except 整块无人发射。else 臂的 `_try_collect_c3` 因为**先**收结构子区域
（14665-14668 在 14677-14680 之前）而免疫 —— 见 r16a_09 差分。

实测（裸核心）MISMATCH=10 / MATCH=6；Round 16-A 补丁后 MISMATCH=1（仅 r16a_05）。
EXPECT 已按两轮实测回填：9 项 SENTINEL（补丁翻正），r16a_05 保持 MISMATCH（另一族）。
docstring 里被否证的预测在 ANALYSIS.md「预测被否证清单」一节逐条记录。
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

BUILD = Path(r'D:/Temp/r16arm/build')
BUILD.mkdir(parents=True, exist_ok=True)

# EXPECT 由两轮实测回填（裸核心 vs D:/Temp/r16_arm/gen_R16.py 播种后落地）：
#   裸核心 MISMATCH=10 / MATCH=6；补丁后 MISMATCH=1（仅 r16a_05）、MATCH=15。
#   r16a_05/06/12 原判为负对照，实测均为真缺陷 —— 06/12 由 Round 16-A 补丁翻正改标
#   SENTINEL；05 是 loop 入口的「重复发射」族（orig=31 / decomp=39），留 MISMATCH 作本轮残留。
EXPECT = {
    'r16a_01_anchor_real_shape_func': 'SENTINEL',
    'r16a_02_anchor_min_entry_steal': 'SENTINEL',
    'r16a_03_anchor_module_scope': 'SENTINEL',
    'r16a_04_probe_ternary_body': 'SENTINEL',
    'r16a_05_probe_while_boolop_entry': 'MISMATCH',
    'r16a_06_neg_try_entry_offset': 'SENTINEL',
    'r16a_07_neg_no_enclosing_if': 'MATCH',
    'r16a_08_neg_if_inside_try': 'MATCH',
    'r16a_09_diff_try_in_else_arm': 'MATCH',
    'r16a_10_neg_with_in_then_arm': 'MATCH',
    'r16a_11_probe_try_except_else': 'SENTINEL',
    'r16a_12_probe_try_finally_boolop': 'SENTINEL',
    'r16a_13_unconf_shape_inside_for': 'UNCONFIRMED',
    'r16a_14_probe_or_boolop_body': 'SENTINEL',
    'r16a_15_probe_two_sibling_tries': 'SENTINEL',
    'r16a_16_neg_plain_try_body': 'MATCH',
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
    reps = sorted(HERE.glob('r16a_*.py'))
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
