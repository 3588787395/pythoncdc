# Tasks

> 目标：将 site-packages 中 111 个 partial pyc 逐个修复为 OK，10 轮迭代。
> 每轮：测试工程师取一个 partial pyc 反编译 + diff + ≥10 复现实例 → 修复工程师按区域归约算法修复 → 回归 → commit + push。
> 当前状态：402 个 pyc，291 OK，111 partial。OK 率 72.4%。
> 所有命令执行 <= 300 秒。每轮 commit + push <= 300 秒。
> 每轮必须至少解决一个 pyc，未解决禁止进入下一轮。

## 通用任务模板（每轮共用）

- [ ] T1: 测试工程师反编译目标 pyc（输出 decompile_report.md）
  - 执行 `python pycdc.py --region -o <tmp.py> <pyc_path>`（<=60s）
  - 反编译产物字节码 vs 原 pyc 字节码 diff（使用 compare_bytecode_v2.py）
  - 不一致清单（函数名 + 偏移 + 字节码模式）
  - 统计一致函数数与成功率
- [ ] T2: 测试工程师提取 >=10 个最小复现实例（输出 minimal_repros/）
  - 每个实例：最小 .py 源码 → compile → 反编译 → 字节码 diff
  - 归档至 rounds/round_NN/test_engineer/minimal_repros/
- [ ] T3: 修复工程师分析 + 定位（依赖 T1/T2）
  - 对每个不一致定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析（涉及的区域类型 + 算法偏离点）
- [ ] T4: 修复工程师实施修复
  - 按区域归约算法 4 原则完善逻辑（禁止补丁）
  - 同步更新方法 docstring（6 节 / 4 节模板）
- [ ] T5: 修复工程师回归测试（<=280s）
  - 该轮 ≥10 最小复现实例全部通过
  - 既有测试矩阵无退化
  - 目标 pyc 字节码完全匹配
  - quotation.pyc 匹配率不退化
- [ ] T6: 修复工程师输出 fix_report.md
  - 修复点 + 算法依据 + 回归结果 + 残留不一致数
- [ ] T7: 更新 pyc_index.json + 生成 OK.py 文件
- [ ] T8: commit + push 到 origin/main（前缀 `rbi-rNN:`，<=300s）
- [ ] T9: 反模式自检（`_fix_`/`_merge_`/`_patch_`/`_fallback_`/`_hack_`/`_workaround_`/`_temp_` 前缀 0 新增）

## Phase 1: Round 01 — IQCommon/strategy/strategy.pyc（fn=2, 1/2 匹配）

> 目标 pyc：IQCommon/strategy/strategy.pyc（fn=2, match=50%）
> module 级字节码不一致（39 diffs），trade_strategy_add 已 OK
> 主要差异：import 语句重排序 / 条件跳转差异

- [ ] T1.1-T1.9: 执行通用任务模板 T1-T9

## Phase 2: Round 02 — fly/dumpload/load_algo.pyc（fn=2, match 待验证）

> 目标 pyc：fly/dumpload/load_algo.pyc（fn=2）
> 含 try/except 嵌套、class 定义

- [ ] T2.1-T2.9: 执行通用任务模板 T1-T9

## Phase 3: Round 03 — fly/common/user_error.pyc（fn=4, match 待验证）

> 目标 pyc：fly/common/user_error.pyc（fn=4）

- [ ] T3.1-T3.9: 执行通用任务模板 T1-T9

## Phase 4: Round 04 — IQEngine/plugins/plugin_system_trade/send_message_api.pyc（fn=3, match=25%）

> 目标 pyc：send_message_api.pyc（fn=3, match=25%，最低匹配率之一）

- [ ] T4.1-T4.9: 执行通用任务模板 T1-T9

## Phase 5: Round 05 — IQData/entry.pyc（fn=5, match 待验证）

> 目标 pyc：IQData/entry.pyc（fn=5）

- [ ] T5.1-T5.9: 执行通用任务模板 T1-T9

## Phase 6: Round 06 — IQEngine/plugins/plugin_system_debug/__init__.pyc（fn=5, match=83%）

> 目标 pyc：plugin_system_debug/__init__.pyc（fn=5, match=83.3%）

- [ ] T6.1-T6.9: 执行通用任务模板 T1-T9

## Phase 7: Round 07 — fly/common/common.pyc（fn=5, match=83%）

> 目标 pyc：fly/common/common.pyc（fn=5, match=83.3%）

- [ ] T7.1-T7.9: 执行通用任务模板 T1-T9

## Phase 8: Round 08 — IQData/modules/WEBCLIENT/web_socket_client.pyc（fn=5, match=71%）

> 目标 pyc：web_socket_client.pyc（fn=5, match=71.4%）

- [ ] T8.1-T8.9: 执行通用任务模板 T1-T9

## Phase 9: Round 09 — IQEngine/core/plugin_manager.pyc（fn=6, match=89%）

> 目标 pyc：plugin_manager.pyc（fn=6, match=88.9%）

- [ ] T9.1-T9.9: 执行通用任务模板 T1-T9

## Phase 10: Round 10 — IQEngine/plugins/plugin_system_persist/json_persistance.pyc（fn=6, match=86%）

> 目标 pyc：json_persistance.pyc（fn=6, match=85.7%）

- [ ] T10.1-T10.9: 执行通用任务模板 T1-T9

# Task Dependencies

- 每轮依赖上一轮完成（成功率单调递增）
- Phase N+1 依赖 Phase N 完成
- 修复工程师 T4 依赖测试工程师 T1/T2 完成
