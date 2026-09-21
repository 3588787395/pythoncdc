# -*- coding: utf-8 -*-
"""Round 21 复现电池：`fly/oauthenticator/oauth2.pyc` 两个 `post` 各 **−9** 的同层判据缺半。

缺陷锚点（同一模块的两份孪生产物，各自唯一缺陷，strict 尺子报 [seq_len]）：

    site-packages/fly/oauthenticator/oauth2.pyc
        <module>.HSIDOAuthCallbackHandler.post    orig=175 decomp=166  (-9)
        <module>.OAuthCallbackHandler.post        orig=190 decomp=181  (-9)

丢的 9 条 = 一个 `yield self.spawn_single_user(user)` 语句块（7 条：
LOAD_FAST self / LOAD_METHOD spawn_single_user / LOAD_FAST user / CALL /
YIELD_VALUE / RESUME / POP_TOP）+ 一对 `LOAD_CONST None; RETURN_VALUE`。
**实测是 ABSENT（整块消失），不是 relocated**：非跳转指令多重集差量恰好
`CALL-1 LOAD_FAST-2 LOAD_METHOD-1 POP_TOP-1 RESUME-1 RETURN_VALUE-1 YIELD_VALUE-1
LOAD_CONST-1`，且 `spawn_single_user` 出现次数 orig=2 → decomp=1。

根因（**同一结构判据在两处各缺半，缺一不可**，全部实测，见 ANALYSIS.md）：
① `RegionAnalyzer._detect_boolop_conditional_chain` 非首成员块守卫
   （core/cfg/region_analyzer.py:24186-24200）只查 `STORE_*`，漏掉**同一函数**
   起始块守卫（24013-24035）已有的另一半「CALL 紧跟 POP_TOP ⇒ 块内含值丢弃语句」
   ⇒ then 臂首块被并成 BoolOp `and` 操作数 → `if status is not None and cgroupmode
   == '1':`，嵌套 if 的 else 臂（块 730 的 return）整块消失。
② `RegionAnalyzer._check_elif_chain` 的 `_has_body_stmt`
   （core/cfg/region_analyzer.py:18216-18243）**已有**「CALL 紧跟 POP_TOP」判据，
   但它的过滤表只排除 `NOISE_OPS + ('RESUME','NOP','CACHE','EXTENDED_ARG')`，
   没排除 CPython 3.11 协程语句插在 CALL 与 POP_TOP 之间的 `YIELD_VALUE`
   ⇒ else 臂首块被当纯 elif 条件块吸收，前缀语句退到 if/elif/else 链之后，
   被编译器死代码消除。

对 test_repros/round21_oauth2/r21_*.py 每个最小复现源文件：
  1. 复制到 D:/Temp/r21arm/build/ 并编译成 .pyc（绝不落在仓库里）；
  2. 用本项目反编译器 decompile_pyc() 反编译，产物写回 build 目录；
  3. 把反编译结果再编译成 .pyc；
  4. 用 **唯一真值尺子** _r10_strict_check.strict_compare 逐个限定名比较。

用法（本工程的并发纪律：**禁止**用工作树 core/ 跑基线，基线一律走仓库外镜像）：
  PYTHONIOENCODING=utf-8 python test_repros/round21_oauth2/run_all.py \
      --core D:/Temp/r21d/mirr/base --base          # 基线核镜像（未修）
  PYTHONIOENCODING=utf-8 python test_repros/round21_oauth2/run_all.py \
      --core D:/Temp/r21d/mirr/c6                   # 候选核镜像（R21-A）
  PYTHONIOENCODING=utf-8 python test_repros/round21_oauth2/run_all.py --strict
  PYTHONIOENCODING=utf-8 python test_repros/round21_oauth2/run_all.py --measure --core ...
  PYTHONIOENCODING=utf-8 python test_repros/round21_oauth2/run_all.py --show-defects 01 10

三张真值表（键集合 == repro 文件名去后缀，脚本自带双向自检；留 None 会 fail-closed）：
  EXPECT       = 修好后（R21-A 落地核 / 候选镜像）真值 —— 不带 --base 时使用
  EXPECT_CAND  = 带 --core <候选镜像> 时使用的真值，与 EXPECT 同源
  EXPECT_BASE  = 带 --base（基线核镜像或未修工作树）时使用的真值
四态：
  MISMATCH   = 缺陷复现（该核上确实丢/错位）
  MATCH      = 负对照（该核上必须正确，用来证伪过宽规则）
  SENTINEL   = 已被 R21-A 修掉的锚点（修好的核上必须 MATCH，退回 MISMATCH 即 REGRESSED）
  UNCONFIRMED= 目标缺陷真实存在但该形状未复现（不计失败）
"""
import sys

sys.dont_write_bytecode = True   # 绝不向仓库/镜像写 __pycache__

import os  # noqa: E402
import py_compile  # noqa: E402
import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

# 唯一真值尺子（只 import，不修改）
from _r10_strict_check import _load_map, strict_compare  # noqa: E402

BUILD = Path(r'D:/Temp/r21arm/build')
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

# ---------------------------------------------------------------------------
# 实测数据来源（全部为 `--measure` 跑出来的真值，非推断）：
#   基线核镜像（git archive 5c63ce6b）  : D:/Temp/r21d/logs/batt_measure_base.txt
#   基线核镜像（git archive 15a8de06 = R20-A 落地后 HEAD）: D:/Temp/r21d/logs/batt_head_base.txt
#   候选核镜像（5c63ce6b + R21-A c6）   : D:/Temp/r21d/logs/batt_c6.txt
#   候选核镜像（15a8de06 + R21-A c6）   : D:/Temp/r21d/logs/batt_head_c6.txt
# 四个世界的逐项结论：两基线完全一致（本族形状不受 R20-A 影响），两候选完全一致。
# ---------------------------------------------------------------------------
EXPECT = {
    # 5 个锚点：基线核 MISMATCH，R21-A 后必须 MATCH
    'r21_01_anchor_twin_full': 'SENTINEL',
    'r21_03_anchor_elif_yield_prefix': 'SENTINEL',
    'r21_08_anchor_elif_bodies_yield': 'SENTINEL',
    'r21_10_anchor_hsid_twin_clone': 'SENTINEL',
    'r21_16_anchor_yield_prefix_real_merge': 'SENTINEL',
    # 负对照：两个世界都必须 MATCH（R21-A 不得改变结论）
    'r21_02_anchor_boolop_then_yield': 'MATCH',
    'r21_04_neg_plaincall_prefix': 'MATCH',
    'r21_05_anchor_plaincall_boolop': 'MATCH',
    'r21_06_neg_assign_prefix_both': 'MATCH',
    'r21_07_neg_pure_elif_chain': 'MATCH',
    'r21_09_anchor_double_nested_yield': 'MATCH',
    'r21_11_neg_call_in_elif_condition': 'MATCH',
    'r21_15_anchor_try_except_yield': 'MATCH',
    # 同族但**不同根因**的残留缺陷：两世界都 MISMATCH，不得被本规则"顺带修好"
    # 12 = async/await 协程（GET_AWAITABLE/SEND 记账，−3）
    # 13 = 循环体内的同族形状（−6 → R21-A 后 +1，仍未收口，见 ANALYSIS.md §7）
    # 14 = 真 and/or 短路链 + 协程 body 的过量发射（+2，Round 22 目标）
    'r21_12_neg_await_shape': 'MISMATCH',
    'r21_13_anchor_yield_prefix_in_loop': 'MISMATCH',
    'r21_14_neg_real_and_chain': 'MISMATCH',
}

EXPECT_CAND = dict(EXPECT)

# 基线核真值 = 修好后真值的机械映射：SENTINEL（被本规则修掉的锚点）在基线上
# 必然 MISMATCH；其余三态与修复无关，保持同值。
EXPECT_BASE = {k: ('MISMATCH' if v == 'SENTINEL' else v) for k, v in EXPECT.items()}


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


def selfcheck(table, tname, files):
    """真值表的键必须 == repro 文件名的去后缀，双向自检；且不得留 None。"""
    missing = sorted(files - set(table))
    extra = sorted(set(table) - files)
    for k in missing:
        print('SELF-CHECK FAIL: repro file without EXPECT key: %s.py' % k)
    for k in extra:
        print('SELF-CHECK FAIL: EXPECT key without repro file: %s' % k)
    none = sorted(k for k, v in table.items() if v is None)
    for k in none:
        print('SELF-CHECK FAIL: %s key has no measured expectation: %s' % (tname, k))
    bad = sorted(v for v in table.values()
                 if v not in (None, 'MISMATCH', 'MATCH', 'SENTINEL', 'UNCONFIRMED'))
    for v in bad:
        print('SELF-CHECK FAIL: %s has illegal expectation value: %s' % (tname, v))
    return (not missing and not extra and not none and not bad), len(files)


def main():
    argv = sys.argv[1:]
    show = '--show-defects' in argv
    strict = '--strict' in argv
    measure = '--measure' in argv
    use_base = '--base' in argv
    sel = [x for x in argv if not x.startswith('--')]
    if measure:
        strict = False
    # --base 选基线真值表；否则带 --core（候选镜像）用 EXPECT_CAND，落地核用 EXPECT。
    if use_base:
        table, tname = EXPECT_BASE, 'EXPECT_BASE'
    elif _core != ROOT:
        table, tname = EXPECT_CAND, 'EXPECT_CAND'
    else:
        table, tname = EXPECT, 'EXPECT'
    reps = sorted(HERE.glob('r21_*.py'))
    files = {p.stem for p in reps}
    if not measure:
        ok, nfiles = selfcheck(table, tname, files)
        if not ok:
            return 2
        if nfiles < 10:
            print('SELF-CHECK FAIL: only %d repro files (need >= 10)' % nfiles)
            return 2
    if sel:
        reps = [r for r in reps if any(s in r.stem for s in sel)]
    n_bad = n_good = n_err = n_unexp = n_unconf = 0
    print('core = %s   table = %s' % (_core, tname))
    print('repro files = %d (keys = %d)' % (len(reps), len(table)))
    for r in reps:
        name, verdict, err, defects = run_one(r, show)
        if verdict == 'ERROR':
            print('%-52s ERROR  %s' % (name, err))
            n_err += 1
            continue
        if measure:
            print('%-52s %-9s %s'
                  % (name, verdict, defects[0][:78] if defects else ''))
            continue
        exp = table.get(name, '?')
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
    if measure:
        return 0
    print()
    print('BATTERY %s :: repros=%d  MISMATCH=%d  MATCH=%d  ERROR=%d  '
          'UNEXPECTED=%d  NOT-REPRODUCED=%d'
          % (os.path.basename(str(_core)), len(reps), n_bad, n_good, n_err, n_unexp, n_unconf))
    if strict:
        return 0 if (n_err == 0 and n_unexp == 0) else 1
    return 0 if n_err == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
