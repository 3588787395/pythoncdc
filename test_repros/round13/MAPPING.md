# Round 13 — 复现 ↔ 根因类 ↔ 目标 pyc 对照表

实测快照：**2026-09-20 21:05 与 21:20 两次复跑一致**，
`PYTHONIOENCODING=utf-8 python test_repros/round13/run_all.py --strict`
→ `repros=25  MISMATCH=15  MATCH=10  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2`（退出码 0）。
「真实 pyc 现状」= 直接对 `site-packages/**.pyc` 跑严格尺子（21:09 复跑，与 20:55 一致）。

EXPECT 取值：`MISMATCH`=缺陷复现 | `MATCH`=负对照（必须一致）|
`SENTINEL`=曾复现、已被并发修复，转为回归哨兵 | `UNCONFIRMED`=未复现占位（实测 MATCH）。

| repro | 类 | 对应真实函数 | 18 文件中的目标 | EXPECT | 实测 | 真实 pyc 现状 |
|---|---|---|---|---|---|---|
| r13_01_return_becomes_break | R13-A | `AccountPlugin._terminate`、`PluginManager.set_engine`×2 | plugin_system_control/__init__.pyc；IQData/manager/plugin_manager.pyc；IQEngine/core/plugin_manager.pyc（基线 3）| SENTINEL | MATCH | 3 个 `seq_len` 症状已全部翻正（_terminate 43→43；set_engine 184/194→同数），但 set_engine×2 转成了 `target_diff` ⇒ 归入 R13-N（见文末表）|
| r13_02_spurious_continue_loop | R13-B | `remove_lock_files`、`parse_config` | IQCommon/util/user_info_utils.pyc；IQEngine/config/config.pyc（基线 2）| MISMATCH | MISMATCH 70→71 | user_info_utils **仍缺陷** 96→97；config 已翻正 293→293 ⇒ 本类现存 1 文件 |
| r13_03_join_tail_sunk_after_loop | **R13-C** | `creat_sheet1`（基线）| IQCommon/util/backtest_info_utils.pyc | MISMATCH | MISMATCH 23→22 (-1) | 该 pyc 现 bad=0（1655→1655 MATCH）⇒ 类活跃、该成员已被并发 A3 修掉 |
| r13_04_join_tail_sunk_into_branch | **R13-C** | `set_parameters`（基线）| IQEngine/plugins/plugin_fly_data/fly_api/setting_api.pyc | MISMATCH | MISMATCH 16→18 (+2) | 该 pyc 现 bad=0（170→170 MATCH）⇒ 同上 |
| r13_05_dict_two_comprehensions | R13-D | `SimulationBroker.save`、`DefaultLiveBroker.save` | plugin_system_simulation/broker.pyc；…/live.pyc（2）| MISMATCH | MISMATCH 16→12 | 两个都**仍缺陷**：broker 22→15、live 16→12 ⇒ **2 文件** |
| r13_06_if_not_none_else_return | R13-E | `DataProxy.get_bar` | IQEngine/data/data_proxy.pyc（1）| MISMATCH | MISMATCH 87→104 | 仍缺陷 86→102 ⇒ 1 文件 |
| r13_07_stmt_dropped_before_break | R13-F | `_on_before_trading_start_trading_thread` | IQEngine/plugins/plugin_fly_data/__init__.pyc（1）| MISMATCH | MISMATCH 66→62 | 仍缺陷 66→62（同文件另有 `resist_api` 107→105 未被任何复现覆盖）⇒ 1 文件 |
| r13_08_chain_then_if_return_dropped | R13-G | `ObjectPersistancePlugin.can_resume_strategy` | IQEngine/plugins/plugin_system_persist/__init__.pyc（1）| MISMATCH | MISMATCH 70→37 | 仍缺陷 89→57 ⇒ 1 文件（疑似 R13-C 的反面症状）|
| r13_09_nested_except_return_merge | R13-H | `save_testds_to_json` | IQEngine/plugins/plugin_system_risk_calculation/function.pyc（1）| MISMATCH | MISMATCH 106→108 | 仍缺陷 314→310 ⇒ 1 文件 |
| r13_10_empty_if_pass_duplicated | R13-I | `Executor.check_before_trading` | IQEngine/core/executor.pyc（1）| MISMATCH | MISMATCH 82→85 | 仍缺陷 243→254 ⇒ 1 文件 |
| r13_11_loop_prologue_sunk | R13-J | `DefaultEventSource.events` | IQEngine/plugins/plugin_system_event_source/default_event_source.pyc（1）| UNCONFIRMED | MATCH | 真实文件**仍缺陷** 512→488，但形状（含 4 个变体）不复现 ⇒ **未复现** |
| r13_12_elif_branch_rotated | R13-K | `DefaultMatcher.match` | IQEngine/plugins/plugin_system_matcher/matcher.pyc（1）| MISMATCH | MISMATCH 155→151 | 仍缺陷 715→689 ⇒ 1 文件 |
| r13_13_bare_raise_sunk | R13-L | `FileLock.acquire` | fly/common/flytools.pyc（1）| MISMATCH | MISMATCH 84→79 | 仍缺陷 90→85（同文件 `get_mem_under_oom_status` 47→18、`whitelist_filter` 116→114 未被覆盖）⇒ 1 文件 |
| r13_14_neg_plain_if_chain | 负对照 | — | — | MATCH | MATCH | if/elif 链普通臂：不得被 R13-C 的修复改坏 |
| r13_15_neg_dict_two_scalars | 负对照 | — | — | MATCH | MATCH | dict 两个标量值：R13-D 的反例 |
| r13_16_neg_try_except_return | 负对照 | — | — | MATCH | MATCH | try/except + return：R13-H 的反例 |
| r13_17_neg_nested_loops | 负对照 | — | — | MATCH | MATCH | 嵌套循环：R13-A/B 的反例 |
| r13_18_join_tail_wide_chain | **R13-C** | `set_parameters`/`creat_sheet1`（宽链变体）| 同 r13_03/04 | MISMATCH | MISMATCH 37→36 (-1) | 宽链（5 臂）+ 3 条链尾语句 |
| r13_19_spurious_continue_elif | R13-B 子形状 | `parse_config` | IQEngine/config/config.pyc（基线 1）| UNCONFIRMED | MATCH | 真实 parse_config **已翻正** 293→293；4 个变体形状均不复现 ⇒ **未复现**（R13-B 以 r13_02 为准）|
| r13_20_for_else_break_lost | R13-M | `RotatingFileHandler.perform_rollover` | IQEngine/utils/logger/handlers.pyc（1；leverage 显示 `IQCommon/logger/handlers.pyc` 同函数 ×2）| MISMATCH | MISMATCH 119→117 | 仍缺陷 127→125 ⇒ 1 文件（跨仓库 ×2）|
| **r13_21_chain_arm_try_rotation**（新）| **R13-C** | 臂尾 try/except 变体 | 类级证据（本轮 18 文件成员 0）| MISMATCH | MISMATCH seq_diff #23 `'2'`→`'7'` | 证明本类与循环无关，禁 FOR_ITER 特判 |
| **r13_22_chain_arm_if_no_else**（新）| **R13-C** | 臂尾无 else 的 if 变体 | 类级证据 | MISMATCH | MISMATCH 18→17 (-1) | 同上（最小组合：无 for、无 try）|
| **r13_23_neg_two_fallthrough_arms**（新）| R13-C 负对照 | — | — | MATCH | MATCH | 两臂都落空 ⇒ 不触发（谓词条件 2 的边界）|
| **r13_24_neg_non_fallthrough_arm**（新）| R13-C 负对照 | — | — | MATCH | MATCH | `while True`+break / 普通赋值臂尾 / 完整 if-else 臂尾 ⇒ 不触发（条件 3）|
| **r13_25_neg_chain_boundary**（新）| R13-C 负对照 | 含真实 creat_sheet1/set_parameters **内层**形状 | backtest_info_utils.pyc、setting_api.pyc（回归哨兵）| MATCH | MATCH | 落空臂非末臂 / raise 终结 / 链后无语句 / for 体内链 ⇒ 不触发（条件 1、4）|

## 未覆盖的真实缺陷（本轮没拿到复现的）

| 真实函数 | pyc | 实测 | 归类 |
|---|---|---|---|
| `PluginManager.set_engine` ×2 | IQData/manager/plugin_manager.pyc、IQEngine/core/plugin_manager.pyc | `target_diff #60 JUMP 终点 orig=('utils'/'time',LOAD_GLOBAL) decomp=('system_log',LOAD_GLOBAL)`，指令数已相等 | **R13-N**（新类，**未复现**）⇒ 2 文件 |
| `ApiMethodPlugin.resist_api` | IQEngine/plugins/plugin_fly_data/__init__.pyc | 107→105 (-2) | 未归类，无复现 |
| `get_mem_under_oom_status` | fly/common/flytools.pyc | 47→18 (-29) | 未归类（整段区域被吞，`diagnosis_wave2` §5 那一族）|
| `whitelist_filter` | fly/common/flytools.pyc | 116→114 (-2) | 未归类，无复现 |
