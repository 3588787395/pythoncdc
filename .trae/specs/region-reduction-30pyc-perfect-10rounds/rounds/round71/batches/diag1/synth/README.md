# diag1 synth 最小复现集（Round 71）

编译 → 反编译 → 重编译 → 判据，全部用仓库落地版 core（工作区 HEAD a31d3f79）。

## 跑法

```bat
python -X utf8 mksynth.py                       rem :: 全部 30 支
python -X utf8 mksynth.py synth\t27_try_except_else_range.py
python -X utf8 scripts\pyc_verify.py single <pyc> --source <ok.py>   rem :: 官方/mandated 尺（在 repo 根目录跑）
```

`mksynth.py` 用 `pylingual.equivalence_check.compare_pyc`；`scripts/pyc_verify.py single` 是
mandated 尺，读数见 `verify_readings.txt`。

## 已确认复现（14 / 30，mandated 尺全部 status=failure）

| # | 文件 | 失败单元 | mandated 尺读数 | 归族 |
|---|------|----------|-----------------|------|
| t01 | t01_if_absorb_following_if.py | `<module>.get_trend` | status=failure units=1/2 50.00% | F-THENOVER |
| t02 | t02_if_absorb_trailing_stmts.py | `<module>.filter_abnormal` | status=failure units=1/2 50.00% | F-THENOVER |
| t03 | t03_andchain_else.py | `<module>.f` | status=failure units=1/2 50.00% | F-ORELSE |
| t05 | t05_bareexcept_boolop_orchain.py | `<module>.rep` | status=failure units=1/2 50.00% | F-BOOLOP |
| t06 | t06_try_finally_tail_return.py | `<module>.upd` | status=failure units=1/2 50.00% | F-FINALLYTAIL |
| t07 | t07_try_finally_tail_pass.py | `<module>.upd2` | status=failure units=1/2 50.00% | F-FINALLYTAIL |
| t08 | t08_ternary_return_in_try.py | `<module>.BarData.limit_up` | status=failure units=2/3 66.67% | F-TERNARY |
| t12 | t12_elif_not_orchain_raise.py | `<module>.Cache.info_conbine` | status=failure units=3/4 75.00% | F-ORELSE（极性） |
| t16 | t16_mixed_and_or_chain.py | `<module>.BarData._history_bars` | status=failure units=2/3 66.67% | F-BOOLOP（混合链） |
| t22 | t22_cross_loop_tail_stmt.py | `<module>.trade_operation` | status=failure units=1/2 50.00% | F-CROSS（循环尾语句） |
| t24 | t24_assert_in_try.py | `<module>.init_time` | status=failure units=1/2 50.00% | F-ASSERT |
| t25 | t25_sibling_return_none_merge.py | `<module>.post` | status=failure units=1/2 50.00% | F-ADJRETURN |
| t27 | t27_try_except_else_range.py | `<module>.parse_time_info` | status=failure units=1/2 50.00% | F-EXCTABLE |
| t29 | t29_try_wrapped_shared_tail.py | `<module>.get_fields` | status=failure units=1/2 50.00% | F-THENOVER/ORELSE（共享尾） |

逐支读数：`synth/verify_readings.txt`。产物在 `synth/out/`（`.pyc` 原件、`.src.py` 输入、
`*OK.py` 反编译产物）。

## 关键"近失"负对照（16 支 success，用来钉住触发条件）

这些形状是**正确**的，说明 bug 需要更具体的结构，不是"只要这样写就错"。

| 文件 | 为什么它不复现（= 触发条件的反证） |
|------|------------------------------------|
| t15_assert_then_unreachable | `assert` 在 **try 之外** → 中转块只有 1 个 successor，`_reach_assertion_error_block`=True，生成 `AssertRegion×2`。**必须在 try 区域内**：try 的 handler 边（`PUSH_EXC_INFO` 入口）使 `len(succs)!=1` → `reach=False` → 无 AssertRegion（→ t24 复现） |
| t17/t28/t29 对照 | `if/elif/else` + 共享尾但**整个函数不套 try** → 正确。**必须套 try/except**（→ t29 复现） |
| t23 / t30 | `else: return None` 形状各变体都正确；真实 `query_trade_strategy_info` 还需 `with`+`for` 与 handler 的具体布局 |
| t18 | 单层 `if` + 循环尾语句 → 正确。**需要 if 内部再串多个 if/continue**（→ t22 复现） |
| t19 / t25 对照 | 单个相邻 `return None` 不触发；**需要兄弟分支各自 `return None`**（→ t25 复现） |
| t20 | 两个顺序 `try/except`（无 `else`）→ 正确。**必须有 `try/except/else`**（→ t27 复现） |
| t21 | 顶层 `return <ternary>`（无 try）→ 正确。**ternary 在 try 内**才触发（→ t08 复现） |
| t04 | `if A and B: X else: Y` 的 or-chain 变体 → 正确 |
| t09/t10/t13 | try 内 if/else + return 各变体 → 正确 |
| t11 | genexpr 内 ternary → 正确（真实 `calculate_di.<genexpr>` 的差异在别处） |
| t14 | None 守卫链 → 正确 |
| t26 | 后续 `if` 吸收（不带 try/多返回尾）→ 正确；真实 `get_history_common` 还需 `fq`/`is_dict` 双层守卫 + 长尾 |
