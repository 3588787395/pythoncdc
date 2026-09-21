# -*- coding: utf-8 -*-
"""Round 20 复现电池：`for ... else` 循环里 **裸 break 块** 的跳转被整体吞掉。

缺陷锚点（同一模块的两份孪生产物，各自唯一缺陷，strict 尺子报 [seq_len]）：

    IQCommon/logger/handlers.pyc        <module>.RotatingFileHandler.perform_rollover
                                        orig=119 decomp=117   (-2)
    IQEngine/utils/logger/handlers.pyc  <module>.RotatingFileHandler.perform_rollover
                                        orig=127 decomp=125   (-2)

丢失的两条指令在两孪生里逐字相同，都是 **两条无条件跳转**：

    1) `break` 的 JUMP_FORWARD（跳向循环后的 else-merge 块，孪生A idx 31 → 302）
    2) 该 `for x` 循环的回边 JUMP_BACKWARD（孪生A idx 32 → 102）

非跳转指令的多重集在两孪生里完全相等（唯一差量就是 `+2 <J JUMP>`）。

根因（**两层各一处、缺一不可**，全部实测，见 ANALYSIS.md §2/§4）：
① 分析层 `RegionAnalyzer._collect_natural_loop_body`
   （core/cfg/region_analyzer.py:6101）的 [R102 for-else fix] break-target 判别
   （同文件 6156-6175）在 6172/6174 两条判据上都判 False：6140-6154 构造
   `_fwd_candidates` 的 BFS **会穿过 break 自身的无条件跳转**，于是 break 落点
   被登记成"循环内前向块" ⇒ `_break_targets` 保持空 ⇒ 6186 的屏障重建被跳过 ⇒
   6245-6259 走 `_return_reachable` 分支，把 `[192,302,336,338,396,428,556]`
   全量吞进外层循环 `body_blocks`，`has_break=False / break_blocks=[]`。
   实测 `region_ast_generator.py` 全部 120 个 Break/Continue 发射点对
   `perform_rollover` 命中数 = **0**（HEAD 核，`where_gen_A.txt`）。
② 生成层 `RegionASTGenerator._if_generate_normal`
   （core/cfg/region_ast_generator.py:16988 的 W15-C "then-独占 merge 块并入 then 臂"）
   在 **臂尾已经是终止语句** 时仍无条件 `_generate_block_statements(merge_block)`
   并拼到 `then_stmts` 尾（16999/17004）。只修①会让循环后代码缩进在 `break` 之后
   ⇒ CPython 3.11 编译器死代码消除 ⇒ 119 塌到 50（实测 `c_a1` 核，`twin_all2.txt`）。
   同一函数 16934-16942 与 `_process_if_blocks` 20541 已经用
   `('Continue','Break','Return','Raise')` 这条"臂尾终止"判据，只有 16988 漏用。

对 test_repros/round20_rollover/r20a_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r20arm/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译，产物写回 build 目录；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round20_rollover/run_all.py
  PYTHONIOENCODING=utf-8 python test_repros/round20_rollover/run_all.py --strict
  PYTHONIOENCODING=utf-8 python test_repros/round20_rollover/run_all.py --core D:/Temp/r20b/mirror/f3
  PYTHONIOENCODING=utf-8 python test_repros/round20_rollover/run_all.py --show-defects 01 02

两张真值表（键集合 == repro 文件名去后缀，脚本自带双向自检；留 None 会 fail-closed）：
  EXPECT      = 落地核（R20-A 已在 core/ 内）真值（不带 --core 时使用）
  EXPECT_CAND = 仓库外镜像核真值（带 --core <镜像> 时使用），R20-A 落地后与 EXPECT 同源
四态：
  MISMATCH   = 缺陷复现（该核上确实丢/错位）
  MATCH      = 负对照（该核上必须正确，用来证伪过宽规则）
  SENTINEL   = 已被候选规则修掉的锚点（候选核上必须 MATCH）
  UNCONFIRMED= 目标缺陷真实存在但该形状未复现（不计失败）
"""
import sys

sys.dont_write_bytecode = True   # 绝不向仓库/镜像写 __pycache__

import py_compile  # noqa: E402
import shutil  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

# 唯一真值尺子（只 import，不修改）
from _r10_strict_check import _load_map, strict_compare  # noqa: E402

BUILD = Path(r'D:/Temp/r20arm/build')
BUILD.mkdir(parents=True, exist_ok=True)

# ---- 可选 --core <镜像核目录>：用仓库外的核跑同一电池（补丁前/后对照）------
_args = [a for a in sys.argv[1:]]
if '--core' in _args:
    _i = _args.index('--core')
    _core = Path(_args[_i + 1]).resolve()
    sys.argv = [sys.argv[0]] + _args[:_i] + _args[_i + 2:]
    while len(sys.path) > 0 and Path(sys.path[0]).resolve() == ROOT:
        sys.path.pop(0)
    sys.path.insert(0, str(_core))
else:
    _core = ROOT

import pycdc  # noqa: E402

decompile_pyc = pycdc.decompile_pyc

# R20-A 已落地（core/cfg/region_analyzer.py 第三析取项 + region_ast_generator.py
# W15-C 臂尾终止守卫）后的真值表 = 落地核实测：
#   D:/Temp/r20c/logs/batt_repo_prefix_table.txt（旧表跑出 UNEXPECTED=11 = 被修好的 11 项）
#   D:/Temp/r20c/logs/batt_base_mirror.txt      （落地前核镜像跑同一批：MISMATCH=18 MATCH=8）
# 四态含义不变：
#   SENTINEL   = 由 R20-A 修掉的锚点，实测必须 MATCH；退回 MISMATCH 即 REGRESSED。
#   MISMATCH   = 同族但**不同根因**的残留缺陷（不得被本规则"顺带修好"，也不得恶化）。
#   MATCH      = 负对照/守卫，本核上必须正确（10/19/23 三条正是防"无 POP_TOP 也算 break"
#                的过宽反例：slippage.create_new_price.check_and_return 块 124）。
#   UNCONFIRMED= 本表为空：26 项形状在两世界上都实测到了确定结论，无"构造不出"项。
EXPECT = {
    'r20a_01_anchor_for_else_bare_break': 'SENTINEL',
    'r20a_02_anchor_rollover_shape': 'SENTINEL',
    'r20a_03_anchor_break_target_is_next_loop': 'SENTINEL',
    'r20a_04_anchor_tryexcept_in_body': 'SENTINEL',
    'r20a_05_anchor_nested_if_break': 'SENTINEL',
    'r20a_06_anchor_method_in_class': 'SENTINEL',
    'r20a_07_neg_break_target_shared': 'MISMATCH',
    'r20a_08_neg_for_else_no_break': 'MATCH',
    'r20a_09_neg_plain_for_break': 'MATCH',
    # 名字叫 anchor，两世界实测都正确：它是 6172 注释点名的"then 臂裸跳转不得判成
    # break"守卫（偏移 196 反例），所以真值 = MATCH（守卫而非缺陷）。
    'r20a_10_anchor_create_daily_stats': 'MATCH',
    'r20a_11_neg_break_inside_except': 'MISMATCH',
    'r20a_12_unconf_twinb_method_call': 'SENTINEL',
    'r20a_13_anchor_two_bare_exit_jumps': 'SENTINEL',
    'r20a_14_anchor_break_target_is_while': 'SENTINEL',
    'r20a_15_anchor_break_target_is_try': 'SENTINEL',
    'r20a_16_anchor_elif_arm_break': 'SENTINEL',
    'r20a_17_anchor_nested_for_else_double_break': 'MISMATCH',
    'r20a_18_anchor_break_with_handler_after': 'MISMATCH',
    'r20a_19_neg_bare_jump_merge_in_body': 'MATCH',
    'r20a_20_neg_nested_break_target_outer_body': 'MATCH',
    'r20a_21_neg_while_true_break': 'MISMATCH',
    'r20a_22_neg_while_else_break': 'MATCH',
    'r20a_23_neg_chain_compare_merge': 'MISMATCH',
    'r20a_24_neg_if_arm_return_in_loop': 'MATCH',
    'r20a_25_neg_try_finally_in_body': 'MATCH',
    'r20a_26_neg_break_in_nested_except': 'MISMATCH',
}

# 落地后"候选核"真值表 = 本表（同一判据世界）：带 --core 跑仓库外镜像时，锚点仍须
# MATCH（SENTINEL 语义一致），7 项同族别因仍须 MISMATCH，守卫仍须 MATCH。
EXPECT_CAND = dict(EXPECT)



def _compile(src_py, out_pyc):
    """编译 .py -> .pyc（写到指定位置，不产生 __pycache__ 残留）。"""
    tmp = BUILD / (Path(out_pyc).stem + '.c.tmp')
    pyc = py_compile.compile(str(src_py), cfile=str(tmp), doraise=True, quiet=2)
    shutil.move(str(pyc), str(out_pyc))
    return Path(out_pyc)


def run_one(repro_py, show=False):
    name = repro_py.stem
    src = BUILD / (name + '.py')
    shutil.copyfile(str(repro_py), str(src))
    orig_pyc = BUILD / (name + '.pyc')
    try:
        _compile(src, orig_pyc)
    except Exception as e:
        return (name, 'ERROR', 'compile failed: %s' % e, [])

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
    for key in sorted(set(b) - set(a)):
        defects.append('%s [extra]' % key)
    verdict = 'MISMATCH' if defects else 'MATCH'
    if show:
        for dd in defects[:6]:
            print('      - %s' % dd)
    return (name, verdict, '', defects)


def selfcheck(table, tname):
    """真值表的键必须 == repro 文件名的去后缀，双向自检；且不得留 None。"""
    files = {p.stem for p in HERE.glob('r20a_*.py')}
    missing = sorted(files - set(table))
    extra = sorted(set(table) - files)
    for k in missing:
        print('SELF-CHECK FAIL: repro file without EXPECT key: %s.py' % k)
    for k in extra:
        print('SELF-CHECK FAIL: EXPECT key without repro file: %s' % k)
    none = sorted(k for k, v in table.items() if v is None)
    for k in none:
        print('SELF-CHECK FAIL: %s key has no measured expectation: %s' % (tname, k))
    return (not missing and not extra and not none), len(files)


def main():
    argv = sys.argv[1:]
    show = '--show-defects' in argv
    strict = '--strict' in argv
    sel = [x for x in argv if not x.startswith('--')]
    # 跑候选核（--core != 仓库）时用候选真值表：锚点必须已翻成 MATCH。
    if _core != ROOT:
        table, tname = EXPECT_CAND, 'EXPECT_CAND'
    else:
        table, tname = EXPECT, 'EXPECT'
    ok, nfiles = selfcheck(table, tname)
    if not ok:
        return 2
    if nfiles < 20:
        print('SELF-CHECK FAIL: only %d repro files (need >= 20)' % nfiles)
        return 2
    reps = sorted(HERE.glob('r20a_*.py'))
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    n_bad = n_good = n_err = n_unexp = n_unconf = 0
    print('core = %s   table = %s' % (_core, tname))
    print('repro files = %d (keys = %d)' % (nfiles, len(table)))
    for r in reps:
        name, verdict, err, defects = run_one(r, show)
        exp = table.get(name, '?')
        if verdict == 'ERROR':
            print('%-52s ERROR  %s' % (name, err))
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
        print('%-52s %-8s (expect %-11s) %-11s %s'
              % (name, verdict, exp, tag, defects[0][:66] if defects else ''))
        if verdict == 'MISMATCH':
            n_bad += 1
        else:
            n_good += 1
    print()
    print('BATTERY %s :: repros=%d  MISMATCH=%d  MATCH=%d  ERROR=%d  '
          'UNEXPECTED=%d  NOT-REPRODUCED=%d'
          % (_core.name, len(reps), n_bad, n_good, n_err, n_unexp, n_unconf))
    if strict:
        return 0 if (n_err == 0 and n_unexp == 0) else 1
    return 0 if n_err == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
