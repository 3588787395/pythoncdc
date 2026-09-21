# -*- coding: utf-8 -*-
"""Round 18-A 复现电池：_discover_predicate_and_chain（生成端 and 短路链发现回退）新增
「前驱候选已被外层 elif 链区域认领」的唯一归属守卫后，`elif X:` 臂的测试块不再被跨层次
吸收成臂内尾随 `if` 的首个合取支。

形状病根（quotation.pyc 的 <module>.change_future_real_date）：
    elif delivery_date:              ← 条件块 B0: LOAD_FAST delivery_date / POP_JUMP_IF_FALSE → 436
        delivery_date = ...strftime  ← 臂体与尾随 if 同处一块 B1，块尾 POP_JUMP_IF_FALSE → 436
        if delivery_date < end[:8]:
            end = delivery_date
B0 与 B1 跳转目标同一、B0 的真路径 fallthrough 恰为 B1 ⇒ 反向链发现把 B0 当作首合取支，
生成 `if delivery_date and delivery_date < end[:8]:`（多发射一条 LOAD_FAST/POP_JUMP 拓扑）。
B0 不是任何区域的 entry（它只是父链区域的 elif_conditions 成员），所以既有的
「entry + condition_block 同一块」守卫抓不到它 —— 这就是本轮补的洞。

对 test_repros/round18_arm/r18a_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r18arm/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译该 .pyc，输出仍写到 D:/Temp/r18arm/build/；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较，
     报告 MATCH / MISMATCH。

判定完全委托给 _r10_strict_check（仅 import，不复制、不修改）。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round18_arm/run_all.py
  PYTHONIOENCODING=utf-8 python test_repros/round18_arm/run_all.py 01 08
  PYTHONIOENCODING=utf-8 python test_repros/round18_arm/run_all.py --show-diff
  PYTHONIOENCODING=utf-8 python test_repros/round18_arm/run_all.py --strict

EXPECT 四态（沿用 round13/run_all.py 语义）：
  MISMATCH   = 缺陷复现（实测必须 MISMATCH）
  MATCH      = 负对照（实测必须 MATCH，用于证明守卫不误伤合法 and 链）
  SENTINEL   = 曾复现、已被本轮守卫修掉；实测必须 MATCH，否则记 REGRESSED
  UNCONFIRMED= 目标缺陷真实存在但该形状未复现；实测应为 MATCH，不计失败
首轮实测（补丁前核 = HEAD 8145f6ff，补丁后核 = 工作区 +15/−1）：
  11 个锚点（01/02/03/04/06/07/08/09/10/11/12）MISMATCH → MATCH，
  全部为 seq_len +1（多发射一条 LOAD_FAST），缺陷函数名逐名消失；
  8 个负对照（20-27）两个世界都 MATCH ⇒ 守卫零误伤；
  05（for 循环内的 elif 臂）两世界都 MATCH ⇒ 该形状走别的生成路径，记 UNCONFIRMED。
交叉验证脚本：D:/Temp/r18arm/measure.py --core <核目录>（镜像核与仓库工作区核各跑一遍）。
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
from _r10_strict_check import _load_map, strict_compare, filtered  # noqa: E402

from pycdc import decompile_pyc  # noqa: E402

BUILD = Path(r'D:/Temp/r18arm/build')
BUILD.mkdir(parents=True, exist_ok=True)

EXPECT = {
    'r18a_01_anchor_elif_body_assign_trailing_cmp': 'SENTINEL',
    'r18a_02_anchor_elif_augassign_trailing_eq': 'SENTINEL',
    'r18a_03_anchor_elif_call_prefix_trailing_lt': 'SENTINEL',
    'r18a_04_anchor_third_elif_prefix_trailing': 'SENTINEL',
    'r18a_05_anchor_elif_in_for_prefix_trailing': 'UNCONFIRMED',
    'r18a_06_anchor_elif_in_method_prefix_trailing': 'SENTINEL',
    'r18a_07_anchor_elif_prefix_trailing_in_op': 'SENTINEL',
    'r18a_08_anchor_two_elif_prefix_trailing': 'SENTINEL',
    'r18a_09_anchor_elif_trailing_call_cmp': 'SENTINEL',
    'r18a_10_anchor_module_scope_elif': 'SENTINEL',
    'r18a_11_anchor_while_elif_prefix_trailing': 'SENTINEL',
    'r18a_12_anchor_elif_inside_elif_prefix_trailing': 'SENTINEL',
    'r18a_20_neg_real_and_chain': 'MATCH',
    'r18a_21_neg_real_and_chain_in': 'MATCH',
    'r18a_22_neg_elif_real_and_chain': 'MATCH',
    'r18a_23_neg_plain_if_elif_chain': 'MATCH',
    'r18a_24_neg_and_chain_with_prefix_assign': 'MATCH',
    'r18a_25_neg_plain_if_arm_trailing_cmp': 'MATCH',
    'r18a_26_neg_nested_if_in_then_arm': 'MATCH',
    'r18a_27_neg_elif_prefix_trailing_and_chain': 'MATCH',
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
        kind, msg, _ = strict_compare(a[key], b[key])
        if kind is not None:
            defects.append('%s [%s] %s' % (key, kind, msg))
    for key in sorted(set(a) - set(b)):
        defects.append('%s [missing]' % key)
    verdict = 'MISMATCH' if defects else 'MATCH'
    if show_diff:
        for key in sorted(set(a) & set(b)):
            print('      %-24s orig=%d decomp=%d'
                  % (key, len(filtered(a[key])), len(filtered(b[key]))))
    return (name, verdict, '', defects)


def main():
    sel = [x for x in sys.argv[1:] if x not in ('--show-diff', '--strict')]
    show = '--show-diff' in sys.argv
    strict = '--strict' in sys.argv
    reps = sorted(HERE.glob('r18a_*.py'))
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    n_bad = n_good = n_err = n_unexp = n_unconf = 0
    for r in reps:
        try:
            name, verdict, err, defects = run_one(r, show)
        except Exception:
            print('%-46s ERROR (harness)' % r.stem)
            traceback.print_exc()
            n_err += 1
            continue
        exp = EXPECT.get(name, '?')
        if verdict == 'ERROR':
            print('%-46s ERROR  %s' % (name, err))
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
        print('%-46s %-8s (expect %-11s) %-11s instr=%s  %s'
              % (name, verdict, exp, tag, _instr_hint(name),
                 defects[0][:70] if defects else ''))
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
