# Round 23 Checklist — C7 簇修复 + 回归修复

## 已完成（15 测试全部通过）
- [x] C7 根因已定位：`_collect_branch_blocks` BFS 进入已归约 region 内部块
- [x] inner_merge 检测已修改：both-sink-terminal + 外部前驱检查
- [x] final_else 收集逻辑已修改：添加 inner_merge 检查
- [x] else_blocks 协调逻辑已添加：仅保留属于 elif 链结构的块
- [x] LoopRegion else_blocks 过滤逻辑已修复
- [x] UNPACK_EX trailing 语句丢失修复
- [x] trailing_return_none 仅顶层 LoopRegion 过滤
- [x] Bug 1 (模式 3): TernaryRegion 停止延伸进嵌套 IfRegion cond（三阶段修复）
- [x] Bug 2 (模式 4): walrus 副作用残留过滤
- [x] Bug 3 (模式 F): 多 not 链 if-elif-else `_ie_has_external_pred` 排除 boolop_chain
- [x] R-A if59 系列: `_else_has_external_pred` 检查（region_analyzer.py:10754-10804）
- [x] R-B adv11 系列: generated_blocks 守卫（region_ast_generator.py:21460-21474）
- [x] R-C if84 系列: 扩展排除集含 chain_blocks + _else_succ_original（region_analyzer.py:10681-10684 + 10803-10818）

## 单测验证（全部通过）
- [x] test_adv18_try_finally_in_if_body 通过
- [x] test_adv19_try_except_else_in_if_body 通过
- [x] test_adv19_while_else_break_in_elif_body 通过
- [x] test_adv19_tuple_unpack_in_if_body 通过
- [x] test_adv20_yield_in_while_in_if_body 通过
- [x] test_adv19_multiline_return_in_if_body 通过
- [x] test_adv20_walrus_in_while_cond_nested_if 通过
- [x] test_adv19_multi_not_chain_in_if_cond 通过
- [x] test_if59ifelifreturn_a/n/x 通过
- [x] test_adv11_nested_ternary_walrus_cond / test_adv11_walrus_ternary_if_cond 通过
- [x] test_if84ifchainedcompareelse_a/n/x 通过

## 全量回归验证
- [x] IF region: 21 failed / 796 passed / 10 skipped（基线 28/789/10，-7 failed ✓ ≤23 目标）
- [x] ternary region: 0 failed / 506 passed / 36 skipped（无退化 ✓）
- [x] 跨区域退化检查: comm -13 R22 R23 = 空（无新回归）

## 算法原则与规范
- [x] 修复未引入跨区域启发式特殊 case（遵循 4 原则）
- [x] 修复未破坏 R21/R22 已有 C2/C3 修复
- [x] 未修改任何测试文件
- [x] 未在源码中添加 print/pdb/breakpoint 语句
- [x] 未创建根级 _debug_*.py 调试文件（已全部删除）
- [x] 未在 round_23 目录留 _tmp_dbg_*.py / _debug_*.py 调试文件（已全部删除）

## 收尾
- [x] fix_report.md 已写入 /workspace/.trae/specs/iterate-region-test-fix/rounds/if_region/round_23/fix_report.md
- [ ] commit + push 待主代理处理
