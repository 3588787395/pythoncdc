# -*- coding: utf-8 -*-
"""Round 19 复现电池：if 臂尾「自然回边块」被误发射为显式 `continue`。

缺陷锚点（IQCommon/util/user_info_utils.pyc 的 <module>.remove_lock_files，
唯一缺陷，strict 尺子报 [seq_len] orig=96 decomp=97）：

    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for file in files:                      ← header 块 FOR_ITER@420
                    if file.endswith('.lock'):          ← IfRegion(entry=422, merge=420)
                        file_path = os.path.join(...)   ← 臂已产语句（Assign）
                        try: os.unlink(file_path)       ← 臂已产语句（Try）
                        except BaseException: ...
                        ← 臂尾块 b@572 = 纯 JUMP_BACKWARD→420，恰为 merge 块

CPython 里 `for: if c: <stmts>` 的臂尾「自然回边」与显式 `continue` 的回边**逐比
特相同**（continue 落到循环头 = 自然迭代尾），区分二者的唯一结构事实是：
**IfRegion.merge_block 是否就是当前循环头块**（是 ⇒ if 是循环体末条语句 ⇒ 自然回边；
否 ⇒ 后面还有语句 ⇒ 真 continue）。`_process_if_blocks` 的 `_r100_suppress`
（core/cfg/region_ast_generator.py:20646-20666）正是据此抑制，实测对本锚点
**已生效**（`_r100_suppress=True`，`EMITS_CONTINUE=False`）。

真正的发射点在**另一处**：`_if_generate_normal` 的 [R3-Continue] 补发射
（core/cfg/region_ast_generator.py:16877-16896）——它先调 `_if_generate_then_branch`
（内部即 `_process_if_blocks`，已正确抑制），随后看到「then_blocks 末块
JUMP_BACKWARD 直达 merge 且 merge is 循环头」就**重新 append 一个 Continue**，
把上层刚做对的区域归并结论推翻。实测发射行 = 16896（唯一命中）。

对 test_repros/round19_cont/r19c_NN_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r19arm/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译该 .pyc，输出写到 build 目录；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较。

判定完全委托给 _r10_strict_check（仅 import，不复制、不修改）。

用法：
  PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py
  PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py --strict
  PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py --show-defects
  PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py --show-continue
  PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py --core D:/Temp/r19/mirror/cand
  PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py 01 20

EXPECT 四态：
  MISMATCH   = 缺陷复现（当前核实测必须 MISMATCH；修复后必须 MATCH）
  MATCH      = 负对照（修复前后都必须 MATCH）
  SENTINEL   = 已被修掉的锚点（实测必须 MATCH，否则 REGRESSED）
  UNCONFIRMED= 目标缺陷真实存在但该形状未复现（实测应为 MATCH，不计失败）
补丁前实测（HEAD 26e330ca）见 EXPECT 注释与 ANALYSIS.md。
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

BUILD = Path(r'D:/Temp/r19arm/build')
BUILD.mkdir(parents=True, exist_ok=True)

# ---- 可选 --core <目录>：用仓库外的镜像核跑同一电池（补丁前/后对照）---------
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

# 锚点 = 曾因「if 臂尾自然回边被误发射为显式 continue」而 MISMATCH 的形状
# 负对照 = 真实源码级 continue / 其他形状，必须 MATCH
# R19-A 已落地：core/cfg/region_ast_generator.py 的 [R3-Continue] 守卫补上第⑤条
# 末判据 `and not self._if_false_path_is_loop_iteration(region)`，与
# _process_if_blocks 的 _r100_suppress（同一谓词）结构结论收口一致。
# 逐条实测（HEAD 26e330ca 核 vs 打补丁核 / 镜像 cand_d，见 ANALYSIS.md §四）：
#   SENTINEL  = 已由 R19-A 修掉的锚点（01/02/03/06/08/09/10/13/16），实测必须
#               MATCH；退回 MISMATCH 即 REGRESSED，计入 UNEXPECTED。
#   MISMATCH  = R19-A 不覆盖的残留锚点（04 try_finally / 05 except_else /
#               12 臂尾嵌套 while / 14 elif 臂）——复现成立但属残留，修复前后
#               都应为 MISMATCH，不得当作已修。
#   UNCONFIRMED = 目标缺陷真实存在、但该形状在两个世界上都 MATCH（未复现）。
#   MATCH     = 负对照，修复前后都必须 MATCH。
EXPECT = {
    # --- R19-A 已修掉的锚点（实测必须 MATCH）---
    'r19c_01_anchor_corpus_try_except': 'SENTINEL',
    'r19c_02_anchor_one_loop_try_except': 'SENTINEL',
    'r19c_03_anchor_try_except_pass': 'SENTINEL',
    'r19c_06_anchor_two_excepts': 'SENTINEL',
    'r19c_08_anchor_two_deep_try': 'SENTINEL',
    'r19c_09_anchor_in_method_try': 'SENTINEL',
    'r19c_10_anchor_module_scope_try': 'SENTINEL',
    'r19c_13_anchor_second_if_try': 'SENTINEL',
    'r19c_16_anchor_handler_raises': 'SENTINEL',
    # --- 残留锚点（R19-A 不覆盖，实测仍 MISMATCH）---
    'r19c_04_anchor_try_finally': 'MISMATCH',
    'r19c_05_anchor_try_except_else': 'MISMATCH',
    'r19c_12_anchor_arm_ends_nested_while': 'MISMATCH',
    'r19c_14_anchor_elif_arm_try': 'MISMATCH',
    # --- 未复现的形状（两世界都 MATCH）---
    'r19c_07_anchor_while_outer_try': 'UNCONFIRMED',
    'r19c_11_anchor_else_arm_try': 'UNCONFIRMED',
    'r19c_15_anchor_try_in_with_arm': 'UNCONFIRMED',
    'r19c_17_anchor_while_finally': 'UNCONFIRMED',
    'r19c_18_anchor_inner_for_break': 'UNCONFIRMED',
    'r19c_19_anchor_try_then_sibling_stmt': 'UNCONFIRMED',
    'r19c_30_anchor_while_in_if_deep': 'UNCONFIRMED',
    # --- negatives（两世界都必须 MATCH）---
    'r19c_20_neg_real_if_continue': 'MATCH',
    'r19c_21_neg_real_stmt_then_continue': 'MATCH',
    'r19c_22_neg_real_continue_then_body_stmts': 'MATCH',
    'r19c_23_neg_continue_in_try_finally': 'MATCH',
    'r19c_24_neg_chained_sibling_ifs': 'MATCH',
    'r19c_25_neg_if_elif_at_loop_tail': 'MATCH',
    'r19c_26_neg_if_else_at_loop_tail': 'MATCH',
    'r19c_27_neg_arm_with_return': 'MATCH',
    'r19c_28_neg_outer_continue_after_inner_loop': 'MATCH',
    'r19c_29_neg_while_body_call': 'MATCH',
    'r19c_31_neg_nested_if_deep_arm_tail': 'MATCH',
    'r19c_32_neg_try_except_in_body_not_arm': 'MATCH',
    'r19c_33_neg_try_except_arm_then_if_tail': 'MATCH',
    'r19c_34_neg_real_continue_in_nested_if': 'MATCH',
    'r19c_35_neg_arm_call_then_continue_after_if': 'MATCH',
    'r19c_36_neg_plain_arm_call': 'MATCH',
    'r19c_37_neg_plain_arm_augassign': 'MATCH',
    'r19c_38_neg_arm_with_block': 'MATCH',
    'r19c_39_neg_arm_nested_for': 'MATCH',
}


def _compile(src_py, out_pyc):
    """编译 .py -> .pyc（写到指定位置，不产生 __pycache__ 残留）。"""
    tmp = BUILD / (Path(out_pyc).stem + '.c.tmp')
    pyc = py_compile.compile(str(src_py), cfile=str(tmp), doraise=True, quiet=2)
    shutil.move(str(pyc), str(out_pyc))
    return Path(out_pyc)


def run_one(repro_py, show=False, cont=False):
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
    if cont:
        n_src = src.read_text(encoding='utf-8').count('continue')
        n_dec = len([ln for ln in text.splitlines() if ln.strip() == 'continue'])
        print('      continue nodes: source=%d decompiled=%d %s'
              % (n_src, n_dec, 'SPURIOUS' if n_dec > n_src else ''))
    if show:
        for dd in defects[:6]:
            print('      - %s' % dd)
    return (name, verdict, '', defects)


def main():
    argv = sys.argv[1:]
    show = '--show-defects' in argv
    strict = '--strict' in argv
    cont = '--show-continue' in argv or '--classify' in argv
    classify = '--classify' in argv
    sel = [x for x in argv if not x.startswith('--')]
    reps = sorted(HERE.glob('r19c_*.py'))
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    if classify:
        for r in reps:
            name, verdict, err, defects = run_one(r, False, True)
            print('%-46s %-8s %s' % (name, verdict, defects[:1]))
        return 0
    n_bad = n_good = n_err = n_unexp = n_unconf = 0
    print('core = %s' % _core)
    for r in reps:
        try:
            name, verdict, err, defects = run_one(r, show, cont)
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
        print('%-46s %-8s (expect %-11s) %-11s %s'
              % (name, verdict, exp, tag, defects[0][:70] if defects else ''))
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
