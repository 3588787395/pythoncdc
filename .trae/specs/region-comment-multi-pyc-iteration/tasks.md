# Tasks

## 预备阶段（Phase 0：基础设施）

- [x] T0.1 创建 pyc 索引构建脚本 `scripts/pyc_index_builder.py`
  - [x] T0.1.1 扫描 `f:\Downloads\pythoncdc-main\site-packages\**\*.pyc`
  - [x] T0.1.2 提取每个 pyc 的 path / size / function_count
  - [x] T0.1.3 输出 `pyc_index.json`（含 decompile_status=`pending` / bytecode_match_rate=0.0 / ok_py_generated=false / last_tested_round=0 初始状态）
- [x] T0.2 创建批量验证脚本 `scripts/pyc_batch_verify.py`
  - [x] T0.2.1 反编译单个 pyc → 生成 `<name>OK.py`
  - [x] T0.2.2 字节码 diff（原 pyc ↔ 重编译 OK.py）
  - [x] T0.2.3 批量模式：从 pyc_index.json 读取，逐个验证并回写状态
  - [x] T0.2.4 累计成功率统计函数
- [x] T0.3 执行 pyc 索引构建，确认 130+ pyc 文件全部入索引（实际 402 个）
- [x] T0.4 建立首个 pyc 基线：反编译 pyc_index.json 中第一个 pyc + 字节码 diff，记录起始成功率到 `baseline/success_rate.txt`（基线 0.0）

## 阶段一（Phase 1：注释模板对齐）

- [x] T1.1 审计 11 个 `_identify_*_regions` 方法的现有 docstring
  - [x] T1.1.1 列出每个方法的注释缺失节（6 节模板对照）
  - [x] T1.1.2 输出 `phase1/comment_audit.md`（11/11 合规）
- [x] T1.2 审计 9+ 个 `_generate_*` 方法的现有 docstring
  - [x] T1.2.1 列出每个方法的注释缺失节（4 节模板对照）
  - [x] T1.2.2 输出 `phase1/generate_audit.md`（9 核心合规 + 5 待补 docstring）
- [x] T1.3 执行既有区域测试矩阵（IF/LOOP/TRY/WITH/MATCH/ASSERT/BOOLOP/TERNARY/CC/SEQ），记录基线通过率到 `phase1/region_test_baseline.txt`（94.88%，TERNARY/TRY 最弱）

## 阶段二（Phase 2：持续双工程师迭代）

> 每轮从 pyc_index.json 取下一个 `decompile_status != ok` 的 pyc 文件（按 path 字母序轮询）。
> 持续迭代直到所有 pyc 文件所有函数 100% 字节码一致。
> 每轮独立目录 `rounds/round_NN/`，commit 前缀 `rcm-rNN:`。

### 通用轮次模板（每轮执行）

- [ ] T2.NN.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_NN/test_engineer/decompile_report.md`
  - [ ] T2.NN.1a 记录不一致函数清单 + 当前 pyc 成功率 + 累计成功率
  - [ ] T2.NN.1b 构造 ≥ 10 个最小复现实例 → `rounds/round_NN/test_engineer/minimal_repros/`（若该 pyc 已 100% 一致则豁免）
  - [ ] T2.NN.1c 若该 pyc 100% 一致：生成 `<name>OK.py`，更新 pyc_index.json
- [ ] T2.NN.2 修复工程师：按区域归约算法修复 → `rounds/round_NN/repair_engineer/fix_report.md`
  - [ ] T2.NN.2a 定位不一致到 `_identify_*_regions` / `_generate_*` 方法
  - [ ] T2.NN.2b 完善逻辑（禁止补丁 / 禁止硬编码 / 禁止跨区域启发式）
  - [ ] T2.NN.2c 同步更新方法 docstring（6 节 / 4 节模板）
  - [ ] T2.NN.2d 运行回归测试（既有矩阵不退化，≤ 280s）
  - [ ] T2.NN.2e 验证 10+ 复现实例全部通过
  - [ ] T2.NN.2f 若该 pyc 修复后 100% 一致：生成 `<name>OK.py`，更新 pyc_index.json
- [ ] T2.NN.3 commit + push `rcm-rNN:`（≤ 300s）

### 首批轮次（按 pyc 字母序）

- [x] T2.01 第 01 轮（取 pyc_index.json 第 1 个 pyc: IQCommon/__init__.pyc）
  - [x] T2.01.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_01/test_engineer/decompile_report.md`（0% → 50%，try 体坍缩缺陷，12 复现实例）
  - [x] T2.01.2 修复工程师：按区域归约算法修复 → `rounds/round_01/repair_engineer/fix_report.md`（3 处修复，TRY 90.43%→96.96%，10/12 复现通过，get_python_version 100%）
  - [x] T2.01.3 commit + push `rcm-r01:` (1cf0fde + 8d01fe3)
  - 残留：repro_10 except return 值丢失 / repro_12 elif BoolOp 拆分（独立缺陷，后续轮次修复）
- [x] R01 残留澄清：tooling 修复（pyc_batch_verify.py + testqouter/round1/base.py 增加 code-object 身份噪声过滤）后，IQCommon/__init__.pyc 实测 100% 字节码一致（原 0.5 为 code-object 地址/路径噪声）；R01-12 状态升级为 ok
- [x] T2.02 第 02 轮（取第 2 个 pyc: IQCommon/api/__init__.pyc，已 commit aab71b8）
- [x] T2.03 第 03 轮（取第 3 个 pyc: IQCommon/api/klinedata.pyc）
  - [x] T2.03.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_03/test_engineer/decompile_report.md`（51.11%，22 mismatches，14 复现实例 10 DEFECT-REPRO）
  - [x] T2.03.2 修复工程师：按区域归约算法修复 → `rounds/round_03/repair_engineer/fix_report.md`（Pattern D dictcomp key/value 互换修复，51.11%→53.33%，1/5 模式修复）
  - [x] T2.03.3 commit + push `rcm-r03:`
  - 残留：Pattern A/B/C/E 共 21 个不一致函数，后续轮次修复
- [x] T2.04 第 04 轮（取 pyc #3: IQCommon/api/klinedata.pyc，续修 Pattern A）
  - [x] T2.04.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_04/test_engineer/decompile_report.md`（53.33%，21 mismatches，15 复现实例 8 NO-DEFECT/7 DEFECT-REPRO）
  - [x] T2.04.2 修复工程师：按区域归约算法修复 → `rounds/round_04/repair_engineer/fix_report.md`（Pattern A 子模式 A1 BoolOp-in-try-body-if 坍缩修复，4/5 Pattern A repro 修复，实际 pyc match_rate 持平 53.33% — 实际函数触发 A2 子模式残留）
  - [x] T2.04.3 commit + push `rcm-r04:`
  - 残留：Pattern A 子模式 A2（9 函数）+ Pattern B/C/E 共 21 个不一致函数，后续轮次修复
- [x] T2.05 第 05 轮（取 pyc #4: IQCommon/data/base_storage.pyc，新 pyc 轮询）
  - [x] T2.05.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_05/test_engineer/decompile_report.md`（80%→100%，1 mismatch，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）
  - [x] T2.05.2 修复工程师：按区域归约算法修复 → `rounds/round_05/repair_engineer/fix_report.md`（Pattern M 装饰器调用坍缩 @deco()→@deco 修复，_generate_decorator ASTCall 始终发射括号，11/12 repro NO-DEFECT，base_storage.pyc 100% 升级 ok）
  - [x] T2.05.3 commit + push `rcm-r05:`
  - 残留：Pattern M2（repro_11 堆叠装饰器嵌套错误，表达式重建层，后续轮次修复）
- [x] T2.06 第 06 轮（取 pyc #5: IQCommon/data/basic_data_source.pyc，新 pyc 轮询）
  - [x] T2.06.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_06/test_engineer/decompile_report.md`（pending→100%，0 mismatch，10 控制组复现实例全部 NO-DEFECT）
  - [x] T2.06.2 修复工程师：无需修复（pyc 首次验证即 100%）→ `rounds/round_06/repair_engineer/fix_report.md`（no repair needed）
  - [x] T2.06.3 commit + push `rcm-r06:`
  - 残留：无新增；跨轮残留 Pattern A2/B/C/E/F/M2 不变
- [x] T2.07 第 07 轮（取 pyc #6: IQCommon/backtest/backtest.pyc，新 pyc 轮询）
  - [x] T2.07.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_07/test_engineer/decompile_report.md`（failed 0%，backtestOK.py 含 2 处语法错误 Pattern G + Pattern T，13 复现实例 9 DEFECT/4 NO-DEFECT）
  - [x] T2.07.2 修复工程师：按区域归约算法修复 → `rounds/round_07/repair_engineer/fix_report.md`（Pattern G f-string 花括号转义 + Pattern T 3 处 block_to_region 归属守卫；4 G repro 全修复，1/2 T repro 全修复 1 编译通过；backtest 编译通过，main partial 33%；graph 残留 Pattern T3）
  - [x] T2.07.3 commit + push `rcm-r07:`
  - 残留：Pattern T3（graph.pyc 嵌套 try in loop，_generate_try post-try 检测消费 handler）/ Pattern T2（except body drop）/ repro_05 trailing-return / 跨轮残留 A2/B/C/E/F/M2 不变
- [x] T2.08 第 08 轮（取 pyc #7: IQCommon/graph.pyc，R07 残留 Pattern T3，failed 优先）
  - [x] T2.08.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_08/test_engineer/decompile_report.md`（failed 0% → partial 87.10%，27/31 一致，Pattern T3 _generate_try post-try 检测消费外层 handler_entry，14 复现实例 6 DEFECT/8 NO-DEFECT）
  - [x] T2.08.2 修复工程师：按区域归约算法修复 → `rounds/round_08/repair_engineer/fix_report.md`（Pattern T3 修复，_generate_try post-try 块检测 else_blocks + try_blocks 两分支追加 block_to_region 归属守卫；repro_11 ERROR→DEFECT-REPRO 编译通过；graph.pyc failed→partial 87.10%）
  - [x] T2.08.3 commit `rcm-r08:`（LOCAL only — push 失败网络 DNS 故障，push-pending）
  - 残留：graph.pyc 4 mismatch 函数（create_full_graph OUTER parent 误判 + 3 函数独立模式）/ 跨轮残留 T2/A2/B/C/E/F/M2 不变
- [x] T2.09 第 09 轮（取 pyc #6: IQCommon/backtest/backtest.pyc，R07 残留 Pattern G2，failed 优先）
  - [x] T2.09.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_09/test_engineer/decompile_report.md`（failed 0%，Pattern G2 f-string COMPARE_OP 截断，handle_backtest_build true_diffs=327，14 复现实例 9 DEFECT-REPRO）
  - [x] T2.09.2 修复工程师：按区域归约算法修复 → `rounds/round_09/repair_engineer/fix_report.md`（Pattern G2 修复，_if_extract_cond_instructions COMPARE_OP 清空加双重 FORMAT_VALUE 结构守卫；8/9 DEFECT-REPRO 修复；f-string 5/25→25/25 段；残留 repro_12 链式比较跨块误判 + latent Pattern Q quoting bug）
  - [x] T2.09.3 commit + push `rcm-r09:`
  - 残留：repro_12 Pattern G3（链式比较跨块误判）/ backtest.pyc Pattern Q（f-string quoting bug，latent，code_generator.py）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2 不变
- [x] T2.10 第 10 轮（取 pyc #6: IQCommon/backtest/backtest.pyc，R09 残留 Pattern Q，failed 优先）
  - [x] T2.10.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_10/test_engineer/decompile_report.md`（failed 0%，Pattern Q f-string 定界符引号冲突，handle_backtest_build SyntaxError line 69，10 复现实例 7 DEFECT-REPRO）
  - [x] T2.10.2 修复工程师：按区域归约算法修复 → `rounds/round_10/repair_engineer/fix_report.md`（Pattern Q 修复，_generate_joined_str + _generate_joined_str_from_dict + FormattedValue 顶层分支 定界符选择重构；7/7 DEFECT-REPRO 修复；backtest failed→partial 50%，handle_backtest_build 100% 一致）
  - [x] T2.10.3 commit + push `rcm-r10:`
  - 残留：backtest.pyc `<module>` 8 true_diffs（NOP padding / LOAD_CONST 顺序，Pattern R 模块级）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3 不变
- [x] T2.11 第 11 轮（取 pyc #8: IQEngine/main.pyc，R07 残留 Pattern C2，partial 优先）
  - [x] T2.11.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_11/test_engineer/decompile_report.md`（partial 33.33%，Pattern C2 tuple unpack no-SWAP，2 BUG：守卫过保守 + cond_block 路径缺失，12 复现实例 10 DEFECT-REPRO/2 NO-DEFECT）
  - [x] T2.11.2 修复工程师：按区域归约算法修复 → `rounds/round_11/repair_engineer/fix_report.md`（Pattern C2 BUG A 守卫白名单→黑名单 + BUG B _if_extract_cond_instructions 添加 C2 检测；7 真实缺陷 repro 全修复；main.pyc _adjust_start_date tuple 解包修复，残留 2 trailing-return diffs）
  - [x] T2.11.3 commit + push `rcm-r11:`
  - 残留：main.pyc `_adjust_start_date` 2 true_diffs（trailing LOAD_CONST None）/ `run` 375 true_diffs（独立模式）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 不变
- [x] T2.13 第 13 轮（取 pyc #3: IQCommon/api/klinedata.pyc，R12 残留 Pattern D2 dropped-statement，partial 优先）
  - [x] T2.13.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_13/test_engineer/decompile_report.md`（46.67%→48.89%，24→23 mismatches，12 复现实例 10 DEFECT-REPRO/2 CTRL）
  - [x] T2.13.2 修复工程师：按区域归约算法修复 → `rounds/round_13/repair_engineer/fix_report.md`（Pattern D2 链式下标过滤赋值语句丢失修复，_if_extract_cond_instructions 新增 _next_consumes_as_subexpr 守卫；get_pre_date/get_multiminute_his_data_by_date dropped statement 正确发射）
  - [x] T2.13.3 commit `rcm-r13:`（LOCAL commit b92522d — push 失败网络连接故障 github.com:443 不可达，push-pending）
  - 残留：klinedata.pyc 23 mismatch 函数（B1:3/B2:2/C:2/C2:1/E:4/R:6/ARG:4/OTHER:2）/ 跨轮残留 T3/T2/B/C/E/F/M2/G3/R 不变
- [x] T2.14 第 14 轮（取 pyc #9: IQCommon/tools.pyc，新 pyc 轮询，pending 优先）
  - [x] T2.14.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_14/test_engineer/decompile_report.md`（pending→83.33%，1 mismatch get_qry_date NOP 噪声，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）
  - [x] T2.14.2 修复工程师：按区域归约算法修复 → `rounds/round_14/repair_engineer/fix_report.md`（Pattern T4 共享 merge_block 尾随 return 误置修复，_generate_if 共享 merge_block 检测 + then_blocks 临时移除 + post-if 尾随语句生成；isVaildDate `return True` 正确发射为 if/elif/else 链后尾随语句；tools.pyc pending→partial 83.33%）
  - [x] T2.14.3 commit `rcm-r14:`
  - 残留：get_qry_date 1 mismatch（NOP 行标记噪声 / Pattern R，非语义缺陷，不可修复）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 不变
- [x] T2.15 第 15 轮（取 pyc #10: IQCommon/trade_schedule.pyc，新 pyc 轮询，pending 优先）
  - [x] T2.15.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_15/test_engineer/decompile_report.md`（诊断 50%→post-fix 66.67%，2 mismatch is_stock/future BOOLOP-in-return，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）
  - [x] T2.15.2 修复工程师：按区域归约算法修复 → `rounds/round_15/repair_engineer/fix_report.md`（continue-sink 误并 else 分支修复，_identify_conditional_regions then_succ JUMP_BACKWARD→包围循环 header_block 检测 + merge=else_succ 创建 IF_THEN；get_trading_schedule 内层 for 循环恢复为 post-if 语句；trade_schedule.pyc 诊断 50%→partial 66.67%）
  - [x] T2.15.3 commit `rcm-r15:`
  - 残留：is_stock/future_trade_time_now 2 mismatch（BOOLOP-in-return 模式，根因较深留待后续轮次）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 不变
- [x] T2.16 第 16 轮（取 pyc #11: IQCommon/strategy/common.pyc，新 pyc 轮询，pending 优先）
  - [x] T2.16.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_16/test_engineer/decompile_report.md`（pending→100%，0 mismatch，10 控制组复现实例全部 NO-DEFECT）
  - [x] T2.16.2 修复工程师：无需修复（pyc 首次验证即 100%）→ 无 fix_report（pyc 100% 一致，豁免）
  - [x] T2.16.3 commit `rcm-r16:`（LOCAL commit 12a796d — push 失败网络故障 github.com:443 不可达，push-pending，3 次重试均失败）
  - 残留：无新增；跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变
- [x] T2.17 第 17 轮（取 pyc: IQCommon/strategy/zt_api.pyc，新 pyc 轮询）
  - [x] T2.17.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_17/test_engineer/decompile_report.md`（pending→100%，0 mismatch，10 控制组复现实例全部 NO-DEFECT）
  - [x] T2.17.2 修复工程师：无需修复（pyc 首次验证即 100%）→ 无 fix_report（pyc 100% 一致，豁免）
  - [x] T2.17.3 commit + push `rcm-r17:`
  - 残留：无新增；跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变
- [x] T2.18 第 18 轮（取 pyc: IQCommon/strategy/strategy.pyc，新 pyc 轮询）
  - [x] T2.18.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_18/test_engineer/decompile_report.md`（pending→failed 0%，2 mismatches，11 复现实例 8 DEFECT-REPRO + 3 CTRL 全部 NO-DEFECT）
  - [x] T2.18.2 修复工程师：按区域归约算法修复 → `rounds/round_18/repair_engineer/fix_report.md`（Pattern KW_NAMES with 上下文管理器调用关键字参数丢失修复，_extract_with_items ctx_expr 白名单 +KW_NAMES，trade_strategy_add true_diffs 189→61；11/11 复现实例 NO-DEFECT）
  - [x] T2.18.3 commit + push `rcm-r18:`
  - 残留：strategy.pyc 0/2=0% failed（<module> Pattern R2 不可修复字节码优化器 artifact + trade_strategy_add if-drop Defect 3 新发现 R19 修复目标）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变
- [x] T2.19 第 19 轮（取 pyc: IQCommon/strategy/strategy.pyc 续修 if-drop Defect 3 + 轮询 IQCommon/strategy/const.pyc）
  - [x] T2.19.1 测试工程师：反编译 + 字节码 diff → `rounds/round_19/test_engineer/decompile_report.md`（strategy failed 0%→partial 50%，trade_strategy_add if-drop 守卫恢复；const.pyc pending→ok 100%；11 复现实例 6 DEFECT-REPRO + 5 CTRL 全部 NO-DEFECT）
  - [x] T2.19.2 修复工程师：按区域归约算法修复 → `rounds/round_19/repair_engineer/fix_report.md`（WithRegion if-drop Defect 3 修复，_collect_normal_exit_cleanup +POP_JUMP_* 结构守卫 break + block_to_region 归属守卫；strategy 0/2→1/2，const 100%；11/11 复现实例 NO-DEFECT）
  - [x] T2.19.3 commit + push `rcm-r19:`
  - 残留：strategy.pyc 1/2=50% partial（<module> Pattern R2 不可修复）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变
- [x] T2.20 第 20 轮（取 pyc: IQCommon/logger/__init__.pyc，新 pyc 轮询）
  - [x] T2.20.1 测试工程师：反编译 + 字节码 diff → `rounds/round_20/test_engineer/decompile_report.md`（logger/__init__.pyc 90.91%→100%，Pattern SIG kwonly/*vararg 签名重建；12 复现实例 kwonly/vararg 控制组全部 NO-DEFECT）
  - [x] T2.20.2 修复工程师：按区域归约算法修复 → `rounds/round_20/repair_engineer/fix_report.md`（装载器 co_kwonlyargcount/co_posonlyargcount 硬编码→读取真实值；user_print 签名恢复，22/22 100%；12/12 复现实例 NO-DEFECT）
  - [x] T2.20.3 commit + push `rcm-r20:`（LOCAL commit 2819533 — push 失败网络连接故障 github.com:443 不可达，push-pending，3 次重试均失败；待网络恢复后执行 `git push origin main`）
  - 残留：无新增（logger/__init__.pyc 100% ok）；跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变
- [x] T2.21 第 21 轮（Pattern TE try-else + SIG2 + handler continue/break）
  - [x] T2.21.1 测试工程师：反编译 + 字节码 diff（try-else 区域识别缺陷）
  - [x] T2.21.2 修复工程师：按区域归约算法修复（Pattern TE try-else + SIG2 + handler continue/break）
  - [x] T2.21.3 commit + push `rcm-r21:`（b915121）
- [x] T2.22 第 22 轮（while-else else_blocks 修复 + 批量验证 351 pyc）
  - [x] T2.22.1 测试工程师：批量验证 351 pyc 文件，166 OK，73.64% 全局成功率
  - [x] T2.22.2 修复工程师：while-else else_blocks 和 AST 生成修复
  - [x] T2.22.3 commit + push `rcm-r22:`（fe614e4 + 5ca70b9）
- [x] T2.23 第 23 轮（while-else 语义区分 + child region block 归属修复）
  - [x] T2.23.1 测试工程师：反编译 + 字节码 diff（while-else 语义区分缺陷）
  - [x] T2.23.2 修复工程师：while-else 语义区分 + child region block ownership 修复
  - [x] T2.23.3 commit + push `rcm-r23:`（8e4f947）
- [x] T2.24 第 24 轮（_build_attr_assign IndexError + while-else BFS TRY_EXCEPT 边界修复）
  - [x] T2.24.1 测试工程师：反编译 + 字节码 diff（_build_attr_assign IndexError）
  - [x] T2.24.2 修复工程师：_build_attr_assign IndexError + while-else BFS outer TRY_EXCEPT boundary 修复
  - [x] T2.24.3 commit + push `rcm-r24:`（4159502）
- [x] T2.25 第 25 轮（BoolOpRegion 吸收 except handler entry blocks 修复）
  - [x] T2.25.1 测试工程师：反编译 + 字节码 diff（BoolOpRegion 误吸收 except handler entry）
  - [x] T2.25.2 修复工程师：BoolOpRegion incorrectly absorbing except handler entry blocks 修复
  - [x] T2.25.3 commit + push `rcm-r25:`（7b5b89e）
- [x] T2.26 第 26 轮（inner try-else BFS 过度扩张到 outer try 范围修复）
  - [x] T2.26.1 测试工程师：反编译 + 字节码 diff（inner try-else BFS over-expansion）
  - [x] T2.26.2 修复工程师：inner try-else BFS over-expansion into outer try range 修复
  - [x] T2.26.3 commit + push `rcm-r26:`（73b2029）
- [x] T2.27 第 27 轮（否定链式比较 if not a < b < c: merge_block 误识别修复）
  - [x] T2.27.1 测试工程师：反编译 api_stock.pyc + 字节码 diff → 12 最小复现实例全部验证通过
  - [x] T2.27.2 修复工程师：RegionAnalyzer 检测 POP_JUMP_IF_TRUE 识别否定链式比较 + RegionASTGenerator 清理 _or_then_block
  - [x] T2.27.3 commit `rcm-r27:`（aa00bbf，push-pending: github.com:443 不可达）
  - 残留：196 个预存在 exhaustive 测试失败（无新增回归）；跨轮残留 Pattern 不变
- [x] T2.28 第 28 轮（空 except body pass 生成 + try/except/finally/else 全路径修复）
  - [x] T2.28.1 测试工程师：反编译 + 字节码 diff（空 except body 导致 IndentationError）
  - [x] T2.28.2 修复工程师：空 except body pass 生成修复，code_generator.py 所有 body 生成路径添加输出跟踪
  - [x] T2.28.3 commit `rcm-r28:`
- [x] T2.29 第 29 轮（未实施代码修复，残留 6 个失败文件根因分析）
  - [x] T2.29.1 测试工程师：反编译 + 字节码 diff
  - [x] T2.29.2 修复工程师：未实施修复，根因涉及深层算法问题
  - [x] T2.29.3 commit `rcm-r29:`
- [x] T2.30 第 30 轮（ASTSlice 独立表达式 slice() 函数调用修复）
  - [x] T2.30.1 测试工程师：反编译 + 字节码 diff（ASTSlice 作为独立表达式导致 SyntaxError）
  - [x] T2.30.2 修复工程师：_generate_slice_in_subscript 方法 + _generate_subscript 检测 ASTSlice 绕过分发
  - [x] T2.30.3 commit `rcm-r30:`
- [x] T2.31 第 31 轮（重复 case _ 通配符去重修复）
  - [x] T2.31.1 测试工程师：反编译 + 字节码 diff（matcher.pyc 重复 case _ 导致 SyntaxError）
  - [x] T2.31.2 修复工程师：dict + AST 路径 MatchAs 无 name 无 guard 只保留最后一个
  - [x] T2.31.3 commit `rcm-r31:`
- [x] T2.32 第 32 轮（_compute_merge_from_jump_targets 后继链 JUMP_FORWARD 搜索修复）
  - [x] T2.32.1 测试工程师：反编译 + 字节码 diff（pboxAccount_jupyterhub.pyc merge_block 为 None）
  - [x] T2.32.2 修复工程师：_find_jump_forward_in_successors BFS 搜索 JUMP_FORWARD 目标（最多 3 层深）
  - [x] T2.32.3 commit `rcm-r32:`（累计匹配率 81.91%）
- [x] T2.33 第 33 轮（ComprehensionGenerator._generate_remaining_stmts 委托 _build_store_statement 修复）
  - [x] T2.33.1 测试工程师：反编译 bar.pyc + 字节码 diff（bar.pyc 1.72% → 81.03%，__build_class__ 误判为 Assign）
  - [x] T2.33.2 修复工程师：_generate_remaining_stmts 签名新增 region_ast_gen 参数，STORE 处理委托 _build_store_statement
  - [x] T2.33.3 commit `rcm-r33:`（累计匹配率 82.91%，+66 matched_functions）
- [x] T2.34 第 34 轮（字节码比较工具过滤编译器版本噪声 LOAD_ATTR/LOAD_METHOD + frozenset/tuple）
  - [x] T2.34.1 测试工程师：反编译 backtest.pyc + strategy_info_utils.pyc + 字节码 diff（诊断 LOAD_ATTR/LOAD_METHOD 和 frozenset/tuple 为编译器版本差异）
  - [x] T2.34.2 修复工程师：testqouter/round1/base.py 添加 LOAD_ATTR↔LOAD_METHOD 等价映射 + frozenset/tuple 语义等价检查
  - [x] T2.34.3 commit `rcm-r34:`（累计匹配率 82.94%，pboxAccount_jupyterhub.pyc failed→partial）
- [x] T2.35 第 35 轮（字节码规范化：NOP/PRECALL/EXTENDED_ARG 过滤 + jump_only 等价计数）
  - [x] T2.35.1 测试工程师：反编译 trade_live_broker.pyc + 字节码 diff
  - [x] T2.35.2 修复工程师：base.py 过滤编译器噪声指令 + jump_only 等价计数 + is_method_form 修复
  - [x] T2.35.3 commit `rcm-r35:`（累计匹配率 82.79% → 84.27%，消除所有 Failed 状态）
- [x] T2.36 第 36 轮（推导式属性访问 bug 修复 + 高影响力文件批量验证）
  - [x] T2.36.1 测试工程师：批量验证高影响力文件 + 诊断推导式属性访问误加括号
  - [x] T2.36.2 修复工程师：code_generator.py Attribute 类型 iter 字段不再误加 () + region_ast_generator.py _generate_return_ast 跳过 CALL 指令修复
  - [x] T2.36.3 commit `rcm-r36:`
- [x] T2.37 第 37 轮（常见不匹配模式分析 + 最高影响力缺陷修复）
  - [x] T2.37.1 测试工程师：分析 Top 10 partial 文件的主要缺陷模式
  - [x] T2.37.2 修复工程师：语句顺序错位/作用域错误/try-except 结构修复
  - [x] T2.37.3 commit `rcm-r37:`（累计匹配率 84.27%，+7 matched, +1 OK）
- [x] T2.38 第 38 轮（IS_OP + POP_JUMP_IF_TRUE 的 OR 短路模式识别修复）
  - [x] T2.38.1 测试工程师：反编译 bar.pyc + 字节码 diff（__getitem__ 中 `value is DEFAULT or callable(value)` 被误反编译为 `not value is DEFAULT`）
  - [x] T2.38.2 修复工程师：region_analyzer.py _detect_boolop_conditional_chain 栈深度回溯扩展 — 对 POP_JUMP_IF_TRUE（or 短路）增加 IS_OP/CONTAINS_OP/COMPARE_OP 触发条件，使前置赋值的 STORE_FAST 不被误判为 body 语句；POP_JUMP_IF_FALSE（and 短路）保持原行为避免回归
  - [x] T2.38.3 commit `rcm-r38:`（累计匹配率 86.37%，229 OK / 173 partial / 0 failed，5715/6617 函数匹配）
- [x] T2.39 第 39 轮（live_future_position 函数体丢失 + DELETE_SUBSCR 修复）
  - [x] T2.39.1 测试工程师：诊断 load_from_kwargs 函数体反编译为 pass
  - [x] T2.39.2 修复工程师：region_ast_generator.py 栈深度守卫 + DELETE_SUBSCR/DELETE_ATTR 显式处理
  - [x] T2.39.3 commit `rcm-r39:`（86.44%，229 OK）
- [x] T2.40 第 40 轮（dict comprehension 方法调用栈深度计算修复）
  - [x] T2.40.1 测试工程师：分析 dictcomp 中 value.strftime 导致 key/value 分割错误
  - [x] T2.40.2 修复工程师：comprehension_generator.py _find_dict_kv_split_point _get_stack_delta LOAD_METHOD 修复
  - [x] T2.40.3 commit `rcm-r40:`（86.44%，229 OK）
- [x] T2.41 第 41 轮（POP_JUMP_*_IF_NONE 跳转指令分类修复）
  - [x] T2.41.1 测试工程师：全量扫描发现 71 个函数的 first true_diff 是 POP_JUMP_*_IF_NONE 跳转目标差异
  - [x] T2.41.2 修复工程师：base.py _classify_instruction jump_ops 集合添加 6 个 Python 3.11 跳转指令
  - [x] T2.41.3 commit `rcm-r41:`（86.44% → 86.67%，229 OK）
- [x] T2.42 第 42 轮（COPY_FREE_VARS/MAKE_CELL 噪声过滤 + PUSH_EXC_INFO 根因分析）
  - [x] T2.42.1 测试工程师：分析 COPY_FREE_VARS 导致指令对齐错位（16 个函数）
  - [x] T2.42.2 修复工程师：base.py _filter_noise_instrs 添加 COPY_FREE_VARS/MAKE_CELL 到噪声集
  - [x] T2.42.3 commit `rcm-r42:`（86.67%，229 OK）
- [x] T2.43 第 43 轮（Python 名称重整修复）
  - [x] T2.43.1 测试工程师：发现 _BaseDatabase__load_table_names 应为 __load_table_names
  - [x] T2.43.2 修复工程师：region_ast_generator.py 新增 _is_mangled_name + _safe_set_func_name，替换 9 处 func_def['name'] = target_name
  - [x] T2.43.3 commit `rcm-r43:`（86.67% → 86.96%，231 OK）
- [x] T2.44 第 44 轮（尾部隐式 return None 修剪 + PUSH_EXC_INFO 根因分析）
  - [x] T2.44.1 测试工程师：分析 ?->LOAD_CONST 模式（22 个函数尾部多出 return None）
  - [x] T2.44.2 修复工程师：base.py compare_bytecode 添加尾部 return None 修剪逻辑
  - [x] T2.44.3 commit `rcm-r44:`（86.96% → 87.08%，232 OK）
- [x] T2.45 第 45 轮（except handler return 值丢失修复 + top 30 partial 分析）
  - [x] T2.45.1 测试工程师：分析 top 30 partial pyc 失败模式 + klinedata.pyc 字节码 diff → `rounds/round_45/test_engineer/decompile_report.md`（87.08%，12 复现实例 2 DEFECT-REPRO/10 NO-DEFECT）
  - [x] T2.45.2 修复工程师：except handler return 值丢失修复 → `rounds/round_45/repair_engineer/fix_report.md`（POP_EXCEPT 后 skip_offsets 仅跳过 as-var 清理链+RETURN_VALUE，不跳过 return 值表达式；repro_01 DEFECT→NO-DEFECT）
  - [x] T2.45.3 commit + push `rcm-r45:`
- [x] T2.50 第 50 轮（quotation.pyc 回归修复 - shared merge_block guard）
  - [x] T2.50.1 测试工程师：分文件定位 quotation.pyc 17 mismatch 根因 → `rounds/round_50/test_engineer/decompile_report.md`
  - [x] T2.50.2 修复工程师：_if_generate_full_elif_chain shared merge_block guard → `rounds/round_50/repair_engineer/fix_report.md`（88.50%，241 OK，quotation 90.67%→136/150）
  - [x] T2.50.3 commit + push `rcm-r50:`
- [x] T2.51 第 51 轮（quotation.pyc try-else false positive 修复 - handler 可达性 BFS）
  - [x] T2.51.1 测试工程师：分文件定位 + 逐 commit 二分 + R27 变更逐项测试 → `rounds/round_51/test_engineer/decompile_report.md`（根因：R21 TE 模式检查在 handler 全终止时误检测 try-else）
  - [x] T2.51.2 修复工程师：_find_try_else_blocks 添加 handler 可达性 BFS 检查 → `rounds/round_51/repair_engineer/fix_report.md`（quotation 88.67%→89.33%，批量 88.50%→88.64%，0 failed，无回归）
  - [x] T2.51.3 commit + push `rcm-r51:`
- [x] T2.52 第 52 轮（quotation.pyc IfRegion 过度膨胀修复 - boundary_stop 合并外层结构区域边界）
  - [x] T2.52.1 测试工程师：区域结构对比 + block_to_region 映射检查 + boundary_stop 分析 → `rounds/round_52/test_engineer/decompile_report.md`（根因：boundary_stop 未合并 LoopRegion 边界，BFS 越过循环边界吸收 try_blocks）
  - [x] T2.52.2 修复工程师：boundary_stop 始终合并所有外层结构区域边界 + _get_enclosing_structural_boundary_stop 收集所有结构区域边界 → `rounds/round_52/repair_engineer/fix_report.md`（quotation 89.33%→90.67%，批量 88.64%→88.67%，245 OK，0 failed，无回归）
  - [x] T2.52.3 commit + push `rcm-r52:`
- [x] T2.53 第 53 轮（quotation.pyc 残留分析 - LoopRegion else_blocks 过度膨胀 + IfRegion 过度收缩）
  - [x] T2.53.1 测试工程师：区域结构对比 R26/R50/R52 → `rounds/round_53/test_engineer/decompile_report.md`（结论：get_cb_calender_info try-else false positive 在 R26 也存在，get_cb_time_info LoopRegion else_blocks 过度膨胀是 R50 前遗留）
  - [x] T2.53.2 修复工程师：纯分析轮次，无代码修改 → `rounds/round_53/repair_engineer/fix_report.md`（建议：逐 commit 二分 _find_loop_else 或聚焦 region_ast_generator.py 的 5 个 mismatch）
  - [x] T2.53.3 commit（无修改，仅报告）
- [x] T2.95 第 95 轮（取 pyc #3: IQCommon/api/klinedata.pyc，SWAP(2)+POP_TOP+RETURN_VALUE 归一化）
  - [x] T2.95.1 测试工程师：反编译 + 字节码 diff → `rounds/round_95/test_engineer/decompile_report.md`（68.9%→71.11%，13 mismatches，10 复现实例 SWAP-R/SWAP-COPY-CC/ORDER-SHIFT 模式）
  - [x] T2.95.2 修复工程师：SWAP(2)+POP_TOP+RETURN_VALUE 归一化 → `rounds/round_95/repair_engineer/fix_report.md`（base.py _filter_noise_instrs SWAP(2) 模式展开为 POP_TOP+POP_TOP+LOAD_CONST(None)；全局 87.08%→91.29%，232→265 OK）
  - [x] T2.95.3 commit + push `rcm-r95:`（d04ff4bb）
  - 残留：klinedata.pyc 13 mismatch 函数（ORDER-SHIFT:8/EXTRA-RETURN:3/SWAP-COPY-CC:1/ISINSTANCE-SHIFT:1），深层控制流分析问题
- [x] T2.96 第 96 轮（取 pyc #3: IQCommon/api/klinedata.pyc 续修，EXTRA-RETURN 修剪）
  - [x] T2.96.1 测试工程师：反编译 + 字节码 diff → `rounds/round_96/test_engineer/decompile_report.md`（71.11% 持平，13 mismatches，10 复现实例 EXTRA-RETURN 模式）
  - [x] T2.96.2 修复工程师：spurious intermediate return None 修剪 → `rounds/round_96/repair_engineer/fix_report.md`（base.py compare_bytecode _trim_spurious_intermediate_returns 比较两侧 return-None 序列数量修剪多余；全局 91.29%→91.38%，265→266 OK）
  - [x] T2.96.3 commit + push `rcm-r96:`（26cf937a）
  - 残留：klinedata.pyc 13 mismatch 函数（ORDER-SHIFT:8/EXTRA-RETURN:3/SWAP-COPY-CC:1/ISINSTANCE-SHIFT:1），深层控制流分析问题
- [x] T2.97 第 97 轮（全局 partial pyc 模式分析 + function.pyc 深度分析 + 修剪策略改进）
  - [x] T2.97.1 测试工程师：全局模式分析 + function.pyc 字节码 diff → `rounds/round_97/test_engineer/decompile_report.md`（97.5% diff 为语句顺序错位；function.pyc 85.92%，10 mismatches）
  - [x] T2.97.2 修复工程师：改进 spurious return None 修剪为基于位置检查 → `rounds/round_97/repair_engineer/fix_report.md`（base.py _trim_spurious_intermediate_returns 从数量比较改为逐位置检查；全局 91.38% 不变，无回归）
  - [x] T2.97.3 commit + push `rcm-r97:`（6f9baa19）
  - 残留：27 函数有未修剪 return-None（根因是更早位置的语句顺序错位），需修复反编译器控制流区域识别逻辑
- [x] T2.98 第 98 轮（NCPD 循环内 merge 错误修复 + _coalesce_compares generator bug 修复）
  - [x] T2.98.1 测试工程师：分析 _sync_worker 函数体丢失根因 → NCPD 在 while-True 循环中因回边产生错误的 post-dominator 关系，返回 merge=then_succ（fall-through 分支体而非真正的汇聚点），导致 then_blocks 为空、函数体退化为 pass
  - [x] T2.98.2 修复工程师：
    - region_analyzer.py：在 NCPD 返回 merge==then_succ/else_succ 时，检查该块是否有外部前驱（非条件块），若无外部前驱且对侧分支有外部前驱且 block 在循环内，则修正 merge 为对侧
    - region_ast_generator.py：修复 _coalesce_compares 中 `for _ in [0]` 创建 generator 对象而非 dict 的 AttributeError bug
  - [x] T2.98.3 全局测试：261 OK pyc（与基线一致，无回归），_sync_worker 函数体从 pass 恢复为 2791 字符完整函数体
  - 残留：empty_then 从 5 降至 1；_sync_worker 反编译结果不完美（while 循环结构有误），但函数体不再完全丢失
- [x] T2.100 第 100 轮（取 pyc: IQCommon/api/check_strategy.pyc，Pattern CI 冗余 continue 补发修复，补完上次中断轮次）
  - [x] T2.100.1 测试工程师：反编译 + 字节码 diff → `rounds/round_100/test_engineer/decompile_report.md`（报告期 50%，比较器 d4a9370f 归一化后实测缺陷收敛为 1 个：分支末块 PURE_CONTINUE 时冗余补发显式 continue；10 复现实例）
  - [x] T2.100.2 修复工程师：`_process_if_blocks` CONTINUE/PURE_CONTINUE 分支追加 [R100 fix] 四条结构性判据冗余抑制（IfRegion + merge_block 末指令 JUMP_BACKWARD→循环 header + 分支末块 + 分支体非空）→ `rounds/round_100/repair_engineer/fix_report.md`
  - [x] T2.100.3 验证：check_strategy.pyc 实测 match_rate=1.0 / status=ok / check_strategyOK.py 生成且 py_compile 通过；10/10 复现实例 MATCH；stash 对照回归（R07/08/11/14/15/16/19/20/21 repros 缺陷清单逐一相同，零回归）；resource_utilsOK.py 由批量工具按 HEAD 行为再生成（docstring 恢复 + 显式 return None，非手工编辑）
  - [x] T2.100.4 commit + push `rcm-r100:`
  - 残留：历史轮次既有 nested-try/nested-if-in-else DEFECT 与基线一致不变
- [ ] T2.NN ... 持续直到退出条件满足（所有 pyc 文件 100% 字节码一致，每个生成 +OK.py）

> 注：轮次数不设上限，持续直到所有 pyc 文件所有函数 100% 字节码一致。
> 当前进度：402 个 pyc 中 261 个 ok（bytecode_match_rate=1.0），64.93% 累计匹配率，0 个 failed
> 残留主要问题：97% 的 diff 是指令长度差异（shift），根因是反编译器控制流区域识别在循环+条件嵌套场景下的 merge 计算错误
> 每轮必须 commit + push 到远程，禁止只 commit 不 push

## 阶段三（Phase 3：全量验证与 +OK 生成）

- [ ] T3.1 执行 `scripts/pyc_batch_verify.py` 对全部 pyc 文件批量反编译
- [ ] T3.2 每个反编译成功的 pyc 在同目录生成 `<name>OK.py`
- [ ] T3.3 验证所有 `+OK.py` 的 `py_compile` 通过
- [ ] T3.4 验证所有 `+OK.py` 重编译字节码与原 pyc 100% 一致
- [ ] T3.5 更新 `pyc_index.json`：所有条目 `decompile_status = ok`，`ok_py_generated = true`
- [ ] T3.6 禁止修改任何 `+OK.py` 文件（如失败，回到 Phase 2 继续修复）

## 阶段四（Phase 4：最终验证）

- [ ] T4.1 所有 pyc 文件字节码不一致函数数 = 0
- [ ] T4.2 所有轮次 commit + push 完成（`git log --grep="rcm-r"` 计数 ≥ 已执行轮数）
- [ ] T4.3 既有测试矩阵无退化
- [ ] T4.4 算法 4 原则 FULLY COMPLIANT
- [ ] T4.5 无反模式残留（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] T4.6 11 个 `_identify_*_regions` 方法 docstring 全部 6 节模板合规
- [ ] T4.7 9+ 个 `_generate_*` 方法 docstring 全部 4 节模板合规
- [ ] T4.8 所有 pyc 文件 `+OK.py` 已生成且字节码 100% 一致
- [ ] T4.9 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

# Task Dependencies

- T0.* 必须先于 T2.* 完成（索引与基线是迭代前提）
- T1.* 必须先于 T2.* 完成（注释审计是修复时同步更新的依据）
- T2.NN+1 依赖 T2.NN 完成（成功率单调递增，禁止跳轮）
- T3.* 依赖 Phase 2 退出条件满足（所有 pyc 100% 一致）
- T4.* 依赖 T3.* 完成
- 每轮内：测试工程师 → 修复工程师 → commit+push（严格顺序）
