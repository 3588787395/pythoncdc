# -*- coding: utf-8 -*-
"""Round 14 复现电池（测试工程师交付物）—— R14-D：dict/容器字面量里的同级推导式被焊接。

对 test_repros/round14/r14_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r14/build/ 并编译成 .pyc（**绝不落在仓库里**）；
  2. 用本项目反编译器 decompile_pyc() 反编译该 .pyc，输出仍写到 D:/Temp/r14/build/；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较，
     报告 MATCH / MISMATCH。

判定完全委托给 _r10_strict_check（仅 import，不复制、不修改、不另造尺子）。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round14/run_all.py             # 全部 17 形状
  PYTHONIOENCODING=utf-8 python test_repros/round14/run_all.py 01 07 13     # 按编号
  PYTHONIOENCODING=utf-8 python test_repros/round14/run_all.py --show-diff  # 打印全部缺陷行
  PYTHONIOENCODING=utf-8 python test_repros/round14/run_all.py --strict      # 有 UNEXPECTED 时退出码 1

EXPECT 四态（语义与 round13 一致）：
  MISMATCH     该形状应复现缺陷；实测 MISMATCH = AS-EXPECTED，实测 MATCH = UNEXPECTED
               （说明修复把它改掉了 —— 那是**好消息**，但必须显式翻成 SENTINEL 才算记账）。
  MATCH        负对照；必须一致。一旦 MISMATCH 即 UNEXPECTED（修复越界）。
  SENTINEL     曾复现、现已修复，实测必须 MATCH，否则 REGRESSED。
  UNCONFIRMED  目标缺陷真实存在但该形状**未复现**（实测应为 MATCH）；不计失败，
               也不得当作修复依据；若翻成 MISMATCH 记 REVIVED，需回查。

本轮 17 个形状是对 R14-D 缺陷面的**二分法**（详见同目录 ANALYSIS.md）：
容器种类（dict / list / tuple / set / 位置实参 / 关键字实参 / STORE_SUBSCR）、
推导式种类（list / set / dict / genexpr）、兄弟数（1 / 2 / 3）、
宿主语句（return / 赋值 / if 臂）四个轴向各只改一个变量。
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
from _r10_strict_check import _load_map, strict_compare  # noqa: E402

from pycdc import decompile_pyc  # noqa: E402

BUILD = Path(r'D:/Temp/r14/build')
BUILD.mkdir(parents=True, exist_ok=True)

EXPECT = {
    'r14_01_dict_two_listcomps': 'SENTINEL',            # 基准：dict + 两个同级 list 推导式
    'r14_02_dict_two_comps_call_iter': 'SENTINEL',      # broker 字面形状（iterable 是调用）
    'r14_03_dict_three_listcomps': 'UNCONFIRMED',       # 三个兄弟：当前不复现
    'r14_04_neg_dict_one_listcomp': 'MATCH',            # 单推导式 + 标量：正确
    'r14_05_neg_genuine_nested_comps': 'MATCH',         # 合法嵌套：正确（不得改坏）
    'r14_06_dict_nested_plus_sibling': 'SENTINEL',      # 嵌套 + 兄弟混合
    'r14_07_neg_list_two_listcomps': 'MATCH',           # list 字面量：正确（BUILD_LIST 在白名单）
    'r14_08_neg_tuple_two_listcomps': 'MATCH',          # tuple 字面量：正确（BUILD_TUPLE 在白名单）
    'r14_09_call_args_two_listcomps': 'SENTINEL',       # 位置实参：CALL 不在白名单
    'r14_10_kwargs_two_listcomps': 'SENTINEL',          # 关键字实参：同上
    'r14_11_dict_two_setcomps': 'SENTINEL',             # set 推导式值
    'r14_12_dict_two_dictcomps': 'SENTINEL',            # dict 推导式值
    'r14_13_dict_two_gencomps': 'SENTINEL',             # 生成器表达式值（MAKE_FUNCTION flag=1）
    'r14_14_assign_dict_two_comps': 'SENTINEL',         # 赋值 / if 臂宿主（非 return 专属）
    'r14_15_neg_store_subscr_two_comps': 'MATCH',       # 逐键赋值 + 两条独立语句：正确
    'r14_16_dict_two_comps_mixed_kinds': 'SENTINEL',    # list comp + set comp 混合
    'r14_17_neg_set_two_comps': 'MATCH',                # set 字面量：正确（BUILD_SET 在白名单）
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
    decomp_src.write_text(text, encoding='utf-8', newline='\n')

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
    reps = sorted(HERE.glob('r14_*.py'))
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    n_bad = n_good = n_err = n_unexp = n_unconf = 0
    rows = []
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
        if verdict == 'MISMATCH':
            n_bad += 1
        else:
            n_good += 1
        rows.append((name, verdict, exp, tag, len(defects),
                     defects[0][:72] if defects else '', defects))

    print('%-44s %-9s %-12s %-12s %-6s %s'
          % ('repro', 'verdict', 'expect', 'status', 'ndfl', 'first defect'))
    print('-' * 118)
    for nm, verdict, exp, tag, ndefects, first, defects in rows:
        print('%-44s %-9s %-12s %-12s %-6d %s'
              % (nm, verdict, exp, tag, ndefects, first))
        if show and verdict == 'MISMATCH':
            for dd in defects[:8]:
                print('      - %s' % dd)
    print()
    print('repros=%d  MISMATCH=%d  MATCH=%d  ERROR=%d  UNEXPECTED=%d  NOT-REPRODUCED=%d'
          % (len(reps), n_bad, n_good, n_err, n_unexp, n_unconf))
    if strict:
        return 0 if (n_err == 0 and n_unexp == 0) else 1
    return 0 if n_err == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
