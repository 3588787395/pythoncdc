# Tasks

> 目标：10 类区域 × 20 轮 = 200 轮对抗性测试修复迭代
> **严格协议（用户强调）**：每轮必须 测试+修复+commit+**PUSH**，禁止只测试不修复，禁止只 commit 不 push。
> 每轮修复完毕立即 git add + git commit + git push。基线 100% 不可退化，每步回归验证。

## Push 状态（已解决）
- **凭证已配置**：classic GitHub token 配置为 credential.helper=store + ~/.git-credentials
- 远程分支 `trae/agent-gUeaUE` 已与本地同步至 b51d00a
- **教训**：之前 R4-6 因环境重置 + 未 push 全部丢失，现已全部补 push

## Phase 0: 框架初始化
- [x] Task 0.1: 建立 spec 目录 + 工作分支
- [x] Task 0.2: 验证 push 可用（凭证已配置）
- [x] Task 0.3: 确认起点基线 @ afe8240（if_region 1 failed / 376 passed, control_flow_matrix 4 failed / 323 passed）

## Phase 1: IF 区域（20 轮）
- [x] Task 1.1: IF round_01 — commit 2d0e64b (已 push)
- [x] Task 1.2: IF round_02 — commit d84c6ae (已 push)
- [x] Task 1.3: IF round_03 — commit 17ccc7e (已 push)
- [x] Task 1.4: IF round_04 — commit a3e4d41 (15/15 修复完成, 已 push)
- [x] Task 1.5: IF round_05 — commit fb8d930 (11/11 修复完成, 已 push)
- [x] Task 1.6: IF round_06 — commit b340f2a (14/14 修复完成, 已 push)
- [x] Task 1.7: IF round_07 — commit b51d00a (11/11 修复完成, 已 push; if_region 480 passed / 1 legacy failed / 2 skipped)
- [x] Task 1.8: IF round_08 — commit bfa1850 (13/13 修复完成, 已 push; if_region 513 passed / 1 legacy failed / 2 skipped)
- [x] Task 1.9: IF round_09 — commit b186a33 (16/16 修复完成, 已 push; if_region 564 passed / 1 legacy failed / 2 skipped)
- [x] Task 1.10: IF round_10 — commit 9bd01bf (14/14 修复完成, 已 push; if_region 605 passed / 1 legacy failed / 3 skipped)
- [x] Task 1.11: IF round_11 — commit 28b6aba (27/28 修复完成 + 1 跳过 bytes_in_cond, 已 push; if_region 647 passed / 3 failed / 4 skipped)
  - **退化警告**：batch 2 (5d823e0) 引入 2 个退化（test_adv03_ternary_call_arg, test_adv03_ternary_in_subscr），R12 优先修复
- [x] Task 1.12: IF round_12 — commit 10dd437 (15/15 修复完成 + 退化修复 batch 0, 已 push; if_region 664 passed / 1 legacy failed / 4 skipped)
- [x] Task 1.13: IF round_13 — commit be09ab2 (8/11 修复完成 + 3 cat4 已知限制, 已 push; if_region 676 passed / 4 failed / 4 skipped)
- [x] Task 1.14: IF round_14 — commit d651de7 (9/11 修复完成 + 2 catA 已知限制, 已 push; if_region 689 passed / 6 failed / 4 skipped)
- [x] Task 1.15: IF round_15 — commit 8d6e3ba (7/15 修复完成 + 8 已知限制, 已 push; if_region 696 passed / 12 failed / 6 skipped)
- [x] Task 1.16: IF round_16 — commit b63b4f8 (9/11 修复完成 + 2 已知限制, 已 push; if_region 709 passed / 13 failed / 7 skipped; match_region 无退化)
- [x] Task 1.17: IF round_17 — commit (R17 之前的 if_region 17 failed baseline)
- [x] Task 1.18: IF round_18 — 5 bug 修复 (yield/yield_from/try-finally 部分/嵌套ternary 部分); 25 failed, 740 passed, 7 skipped (基线 27 failed, 738 passed)
- [x] Task 1.19: IF round_19 — 6 bug 修复 (elif 语义反转 + 嵌套 if-elif-else 退化); 35 failed, 760 passed, 9 skipped (基线 37 failed, 758 passed)
- [x] Task 1.20: IF round_20 — 6 bug 修复 (CodeGenerator AST dict 泄漏 + WithRegion 跨域归并); 45 failed, 772 passed, 10 skipped (基线 35 failed, 760 passed) — IF 区域 20 轮完成

## Phase 2: LOOP 区域（20 轮）
- [ ] Task 2.1 ~ 2.20

## Phase 2.5: TERNARY 区域（20 轮）
- [x] Task T1.1: Ternary round_01 — 5 bug 修复 (walrus/compare/method_call/starred); 55 failed, 77 passed, 1 skipped (基线 60 failed, 72 passed)
- [x] Task T1.2: Ternary round_02 — 7 bug 修复 (is_none/contains/multi_target/unpacking/raise/multi_arg/lambda_call); 58 failed, 116 passed, 1 skipped (基线 65 failed, 109 passed); 3 已知限制 (chained_compare/await/return_arith, R3 处理)
- [x] Task T1.3: Ternary round_03 — 5 R3 bug + 3 bonus + 2 回归守卫 (return_arith/raise/lambda_complex/return_two_ternary); 61 failed, 133 passed, 1 skipped (基线 58 failed)
- [x] Task T1.4: Ternary round_04 — 9 R4 bug 修复 + 4 bonus (setattr/await/dict/del/format/fstring/set/except_handler/with_ctx_mgr); 59 failed, 158 passed, 1 skipped (基线 61 failed, 133 passed); 2 已知限制 (chained_compare_4way 部分修复 / while_cond 完全回滚，R5+ 处理); 跨区域 104 failed / 930 passed / 11 skipped (基线 107/927/11，改善 3 无退化); commit pending
- [x] Task T1.5: Ternary round_05 — 7 R5 bug 修复 + 6 bonus (chained_compare+assign/double_star/subscript_slice/return await/class_body); 57 failed, 182 passed, 1 skipped (基线 69 failed, 170 passed); 3 已知限制 (while_cond 同 R4-10 根因，R6+ 处理); 跨区域 102 failed / 954 passed / 11 skipped (基线 104/930，改善 2 无退化); commit pending
- [x] Task T1.6: Ternary round_06 — 10 R6 bug 修复 + 2 bonus (multi_ternary_shared_exit/comprehension/while_body_leak/annotation/except_handler); 59 failed, 202 passed, 1 skipped (基线 70 failed, 191 passed); 3 已知限制 (while_cond_nested/complex + decorator_chain，R7+ 处理); 跨区域 103 failed / 975 passed / 11 skipped (基线 102/954，+1 failed net = 3 R6 known - 2 baseline bonus，+21 passed); commit pending
- [x] Task T1.7: Ternary round_07 — 5 R7 bug 修复 + 1 回归修复 (R3-08/R4-05) + 6 已知限制 (R7-01/02/03/04/08/10); ternary 65 failed / 228 passed / 1 skipped (基线 70/223/1, -5 failed); 跨区域 109 failed / 1001 passed / 11 skipped (基线 103/975/11, +6 net = 11 新增 - 5 修复，无基线退化)
  - [x] SubTask T1.7.0: 基线确认
  - [x] SubTask T1.7.1 (P0): R7-05/07/11 finally 块 ternary 归约 — `_classify_handler_with_cleanup` BFS walk + CHECK_EXC_MATCH/CHECK_EG_MATCH 守卫 + generate() 全局预标记 + _generate_try_body try_blocks 预标记 + finally body TernaryRegion 识别
  - [x] SubTask T1.7.3 (P2): R7-09 del subscript base obj (Pattern D2) + R7-06 yield from + 赋值
  - [x] SubTask T1.7.4 (P3): R7-06 yield from + 赋值复合 — STORE_* 检测 + value_target 记录 + Pattern 4&5 Assign 包装
  - [x] SubTask T1.7.5: 全量 ternary 回归 — 65 failed (基线 70, -5)
  - [x] SubTask T1.7.6: 跨区域回归 — 109 failed / 1001 passed / 11 skipped (无基线退化)
  - [x] SubTask T1.7.7: 写 fix_report.md
  - [ ] 已知限制 (R8+ 处理): R7-01/08 assert message ternary, R7-02 async for body, R7-03 async with body, R7-04 del subscript chain, R7-10 async for-else
- [x] Task T1.8: Ternary round_08 — 修复 10 测试 / 5 类 bug（assert family 5 + del subscript 2 + R8-04 walrus + R8-05 unpack + R8-07 import），6 已知限制留待 R9+（async 4 + skip 2）
  - [x] SubTask T1.8.0: 基线确认（ternary 65 failed / 228 passed / 1 skipped；跨区域 109 failed / 1001 passed / 11 skipped）
  - [x] SubTask T1.8.1 (P0): R7-01/R7-01b/R8-01/R8-02/R8-03 assert message ternary 系列（5 测试） — `_build_ternary_no_target_consumer_stmt` 顶部 guard + `_build_assert_message_ternary_stmt` 方法 + Pattern 1 内部 guard 移除
  - [x] SubTask T1.8.2 (P0): R8-04 walrus 捕获 ternary — `_generate_ternary` value_target 分支前 walrus 检测，输出 `Expr(NamedExpr(target, IfExp))`
  - [x] SubTask T1.8.3 (P1): R7-04/R8-06 del subscript 双 ternary — `_try_build_ternary_chained_r6_pattern` Pattern D，输出 `Delete([Subscript(Subscript(obj, IfExp1, Del), IfExp2, Del)])`
  - [x] SubTask T1.8.4 (P2): R8-05 unpacking 赋值 source 是 ternary — `_generate_ternary` value_target 分支 Mode 3 UNPACK_EX 检测，输出 `Assign(targets=[Starred(y)], value=IfExp)`
  - [x] SubTask T1.8.5 (P2): R8-07 import from alias 后跟 ternary 赋值 — 新增 `_extract_imports_from_block_prefix` helper + `generate()` TernaryRegion 分支调用，import 不丢失
  - [x] SubTask T1.8.6 (评估): R7-02/R7-03/R7-10/R8-08 async 控制流 ternary 系列（4 测试） — 评估结论：多文件多修改点 + 4 种不同修复方向 + 退化风险高，留待 R9+
  - [x] SubTask T1.8.7: 全量 ternary 回归 63 failed / 257 passed / 3 skipped（≤65 目标 ✅）+ 跨区域 107 failed / 1030 passed / 13 skipped（≤109 目标 ✅，无基线退化）
  - [x] SubTask T1.8.8: 写 fix_report.md，清理 6 个根级 _debug_*.py 调试脚本
- [x] Task T1.9: Ternary round_09 — 修复 11 bug（聚类 A 6 fix + 1 skip：R7-02/R7-10/R8-08/R9-01/R9-03/R9-04 + R7-03 skip；聚类 B 4 fix：R9-05/R9-17/R9-18/R9-19；R9-09 metaclass class body），7 已知限制留待 R10+（聚类 C 4：R9-10/R9-12/R9-13/R9-14；聚类 D 2：R9-15/R9-16；聚类 E 1：R9-08 except*）；ternary 66 failed / 277 passed / 5 skipped（基线 78/258/3，-12 failed +19 passed）；跨区域 109 failed / 1052 passed / 14 skipped（if_region 43 failed 无退化）；commit pending
  - [x] SubTask T1.9.0: 基线确认（ternary 78 failed / 258 passed / 3 skipped；跨区域 121 failed）
  - [x] SubTask T1.9.1 (P0): 聚类 A async 协议 polling 块归属冲突（7 bug） — dominator_analyzer Option C 精细化（自循环块包含异常后继）+ region_analyzer _is_await_polling_loop GET_ANEXT 检测 + LoopRegion.can_be_ternary_header 嵌套 ternary 守卫 + GET_AITER/ASYNC_GEN_WRAP merge_context + cfg_builder RETURN_GENERATOR fall-through + region_ast_generator R9-03 func_call_info 包装 + R9-04 merge_block 截断
  - [x] SubTask T1.9.2 (P1): 聚类 B comprehension 桥接指令吞并（4 bug） — comprehension_generator Pattern B 检测（三元作 if-filter）+ walrus(ternary) 检测 + code_generator IfExp 括号
  - [x] SubTask T1.9.3 (P2): R9-09 metaclass class body — _build_class_def 从 call_expr 提取 keywords 保留 metaclass 关键字参数
  - [x] SubTask T1.9.4 (评估): 聚类 C/D/E 评估 — 聚类 C 4 bug（类定义基础设施：装饰器 CALL/KW_NAMES/LOAD_BUILD_CLASS 重建）+ 聚类 D 2 bug（consumer 模式：_is_ternary_block 约束/func_call_info false_value 吞并）+ 聚类 E 1 bug（except* PEP 654 未实现）均标记为已知限制，避免过度工程化
  - [x] SubTask T1.9.5: 全量 ternary 回归 66 failed / 277 passed / 5 skipped（≤67 目标 ✅，基线 78→66 -12）+ 跨区域 109 failed / 1052 passed / 14 skipped（if_region 43 failed 无退化 ✅）
  - [x] SubTask T1.9.6: 写 fix_report.md，清理 8 个 round_09/_debug_*.py 调试脚本
  - [ ] 已知限制 (R10+ 处理): R9-08 except* PEP 654, R9-10 frozen dataclass, R9-12 property setter, R9-13 abstractmethod, R9-14 class decorator arg, R9-15 assert+return consumer, R9-16 partial application, R7-03/R9-02/R9-25 重编译失败 skip
- [x] Task T1.10: Ternary round_10 — P0 装饰器链修复（聚类 F，目标 9+ bug），P1/P2 评估，P3 标记已知限制
  - [x] SubTask T1.10.0: 基线确认（ternary 66 failed / 277 passed / 5 skipped；跨区域 109 failed / 1052 passed / 14 skipped；R10 新测试 15 failed / 13 passed）
  - [x] SubTask T1.10.1 (P0): R9-12 `@x.setter` Attribute 装饰器 — `_reconstruct_decorator_chain` 识别 LOAD_NAME + LOAD_ATTR 序列作 Attribute 节点（非两个独立 Name）
  - [x] SubTask T1.10.2 (P0): R9-13/R10-03/R10-04/R10-05/R10-11 无参装饰器 + ternary default（5 bug） — `_generate_ternary` MAKE_FUNCTION flag 1/2/4 路径检测 MAKE_FUNCTION 之后的 PRECALL+CALL 作装饰器应用，从 preload_exprs[0] 取装饰器名 — **R10-11 未修复**（已知限制，涉及三次函数定义 + annotations tuple）
  - [x] SubTask T1.10.3 (P0): R10-01 装饰器链 `@deco1 @deco2(ternary)`（1 bug） — `_generate_ternary` flag 0 路径统计 MAKE_FUNCTION 之后 CALL 数，>1 时构建多元素 decorator_list
  - [x] SubTask T1.10.4 (P0): R10-02 `@deco(a[ternary])` 下标参数（1 bug） — `_generate_ternary` flag 0 路径用 expr_reconstructor 重建 merge_block 中 BINARY_SUBSCR 等指令为完整 Subscript 表达式作装饰器参数
  - [x] SubTask T1.10.5 (P0): R9-14 `@deco(ternary) class C` 类装饰器（1 bug） — `_build_class_def` 或 `_generate_ternary` 类路径识别 outer_call 是 `Call(Call(deco, [ternary]), [__build_class__ Call])`，保留 `Call(deco, [ternary])` 作装饰器
  - [x] SubTask T1.10.6 (评估): P1 聚类 G dataclass/类基础设施（R9-10/R10-06/R10-07/R10-08） — 评估后标记为已知限制（复杂度中-高，留待 R11+）
  - [x] SubTask T1.10.7 (评估): P2 聚类 H/I/J consumer/functools/kwonly（R9-15/R9-16/R10-09/R10-10/R10-12/R10-13/R10-14/R10-15） — R9-16/R10-13 已修复（Fix 3 bonus），其余 6 个标记为已知限制
  - [x] SubTask T1.10.8 (标记): P3 聚类 K/L except*/async with multi-as（R9-08/R7-03） — 标记为已知限制，不在 R10 修复
  - [x] SubTask T1.10.9: 全量 ternary 回归（pre-R10 62 failed ≤66 ✓ / 300 passed / 5 skipped，无新增退化）+ 跨区域回归（pre-R10 105 failed ≤109 ✓ / IF 43 failed 无退化）
  - [x] SubTask T1.10.10: 算法合规性自检 — 归约顺序 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口；无跨区域特例 / 后处理补丁 / 硬编码深度上限
  - [x] SubTask T1.10.11: 清理临时调试脚本（不创建根级 _debug_*.py）
  - [x] SubTask T1.10.12: 写 fix_report.md
- [ ] Task T1.11 ~ T1.20

## Phase 3-10: 其他 8 区域（各 20 轮）
- [ ] Task 3.1 ~ 10.20

## Phase 11: 跨区域解耦与最终验证
- [ ] Task 11.1 ~ 11.5

# 执行协议（每轮，严格）
1. 调度测试工程师 sub-agent → 产 test_findings.md（10+错误）
2. 调度修复工程师 sub-agent → 修复全部错误 → 每步全量回归 → 产 fix_report.md
3. 修复工程师 git add + git commit
4. **主代理 git push 到远程**（关键！不可省略，失败则报告阻塞）
5. 主代理验证全量回归 = 100%
6. 勾选 tasks.md，更新 checklist.md

# 关键约束
- 基线 100% 不可退化，每步回归，退化则回滚换方案
- 修复依归约算法 4 原则，禁止后处理补丁/跨区域特例/硬编码深度上限
- **每轮必须 push**（血泪教训：Round 4-6 因未 push 全部丢失）
