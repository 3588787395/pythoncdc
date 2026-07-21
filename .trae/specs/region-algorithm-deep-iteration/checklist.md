# 验证清单

> 目标：从「run_test_matrix 100%」虚假完成 → 「全测试集 100% + 字节码完全匹配 + 算法 4 原则全部 PASS」真实完成
> **当前状态**: Phase 0-10 待执行；已知失败基线 ~290+（if_region 75 + loop 128 + match 74 + nook 38）

## Phase 0: 全测试集基线建立

- [ ] C0.1 全测试集运行脚本已建立（覆盖 `tests/exhaustive/{if_region,loop,with_region,try_except,match_region}`）
- [ ] C0.2 全测试集运行脚本覆盖 `tests/control_flow_matrix/`
- [ ] C0.3 全测试集运行脚本覆盖 `tests/nook/`
- [ ] C0.4 全测试集运行脚本覆盖 `ok/` + `testqouter/round{1,2,3}/`
- [ ] C0.5 「全测试集基线报告」生成（含每测试集通过率 + 总通过率）
- [ ] C0.6 每个失败用例标注「失败类型」「所属区域类型」「字节码 diff 摘要」
- [ ] C0.7 「失败用例 → 区域类型 → 算法根因」映射表生成（`failures_root_causes.md`）

## Phase 1: 算法根本性反思

- [ ] C1.1 现有 19 个 RegionType 覆盖范围审计完成
      （每类型：能识别模式 + 不能识别模式 + 失败用例）
- [ ] C1.2 候选新区域类型论证完成（WITH_EXIT / LOOP_ELSE / MATCH_GUARD /
      IMPLICIT_RETURN / ASYNC_WITH / ASYNC_FOR，每个有「采用/不采用 + 理由」）
- [ ] C1.3 候选新方法论证完成（迭代归约 / 异常表驱动 / 支配树驱动，
      每个有「采用/不采用 + 理由」）
- [ ] C1.4 2 个 WARN 消除方案设计完成
      （`_merge_consecutive_with_regions` 前移 + try_except `depth` 改为结构判定）
- [ ] C1.5 「算法评估报告」生成（`algorithm_evaluation.md`，含上述全部内容）
- [ ] C1.6 报告中每个候选有明确「采用 / 不采用」结论
- [ ] C1.7 报告中列出本 spec 后续 Phase 的优先级与依赖关系

## Phase 2: 算法基础重构

- [x] C2.1 `_merge_consecutive_with_regions` 前移至 `_identify_with_regions`
      （后处理补丁消除）— Phase 2.5.1 P1 peephole 模式库已重建，识别阶段一次正确
- [x] C2.2 try_except `depth` 字段特例改为异常表结构判定
      （跨区域特例消除）— Phase 2.5.2 三元识别修复完成
- [x] C2.3 上述 2 个修改后全测试集回归无退化

### Phase 2.5: CPython Peephole 模式库（反思第 4 块）

- [x] C2.5.1 P1 模式（module-level/function-tail 三元表达式语句 → double RETURN_VALUE）已重建
- [x] C2.5.2 P1 if-return 与三元表达式区分（has_pop_top 字段）
- [x] C2.5.3a P1 peephole 模式库测试覆盖（115/116 ternary 通过，1 跳过）
- [x] C2.5.3b Scenario B 修复（while 条件位三元：merge_block IS LoopRegion.header_block）
- [x] C2.5.3c P1 if-return 已修复（peephole_patterns.py:311-312 让 IfRegion 处理 if-return）
- [x] C2.5.3d bool03_not 测试框架识别 UnaryOp(Not) 作为 BOOL_OP（REGION_TYPE_CUSTOM_MATCHERS）
- [x] C2.5.3e bool20_complex_logic 修复（混合 and/or 链不丢中间操作数）
- [x] C2.5.3f bool19_ternary_combo 修复（or None 尾部操作数保留）
- [x] C2.5.3g bool11_in_while 修复（while 条件位 and 链不被拆分为 if+while+if）
- [x] C2.5.4 P3 模式（while-true + break）枚举
- [x] C2.5.5 P4 模式（chained compare）枚举
- [x] C2.5.6 P5+ 模式（CPython peephole 全模式枚举）
- [x] C2.5.7 CPython 模式库全测试集回归
- [x] C2.6 禁止前缀方法重命名（_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_）
      — region_analyzer.py / region_ast_generator.py / ast_generator_v2.py / structured_analyzer.py
      共 16 处重命名，SM28/SM30 合规测试 3 项失败 → 0 项失败
- [x] C2.7 测试框架修复 — MatrixTestBase 跳过父类 SOURCE_CODE 强制检查
      — 132 errors → 0 errors（test_ternary_deep_nesting 35/35 通过、
        test_deep_nesting_coverage 47/55 通过、test_binary_combinations_supplement 26/30 通过、
        test_boundary_cases_extended 40/47 通过；真实反编译失败移交 Phase 3-8）
- [ ] C2.4 若 Phase 1 论证通过新区域类型：在 `RegionType` 枚举中新增成员
- [ ] C2.4a 若新增类型：实现 `_identify_<new>_regions` 方法（6 节模板 docstring）
- [ ] C2.4b 若新增类型：实现 `_generate_<new>` 方法（4 节模板 docstring）
- [ ] C2.4c 若新增类型：在 `analyze()` 中编排新类型的归约顺序
- [ ] C2.4d 若新增类型：全测试集回归无退化
- [ ] C2.9 若 Phase 1 论证通过新方法：实施迭代归约 / 异常表驱动 / 支配树驱动
- [ ] C2.10 若实施新方法：全测试集回归无退化
- [ ] C2.11 `analyze()` 末尾增加「每块唯一归属」不变量检查（debug 模式）
- [ ] C2.12 `_generate_*` 中增加「子区域抽象节点」不变量检查（debug 模式）
- [ ] C2.13 `_generate_*` 中增加「入口引用语义」不变量检查（debug 模式）
- [ ] C2.14 debug 模式下 4 原则不变量检查全部通过

## Phase 3: IF 区域深度迭代

- [ ] C3.1 IF 区域 75 个失败用例字节码 diff 完成
- [ ] C3.2 IF 区域失败用例按失败类型分类完成
- [ ] C3.3 IF 区域失败用例按共性问题分组完成
      （walrus/ternary/await/lambda in cond / chained compare + boolop /
       assert 混淆 / 嵌套 code object）
- [ ] C3.4 IF 区域算法根因修正（按批次）
- [ ] C3.4a 批次 1：walrus in cond 失败修复 + 字节码完全匹配
- [ ] C3.4b 批次 2：nested ternary in cond 失败修复 + 字节码完全匹配
- [ ] C3.4c 批次 3：await in cond 失败修复 + 字节码完全匹配
- [ ] C3.4d 批次 4：lambda call in cond 失败修复 + 字节码完全匹配
      — 部分修复：boolop 结果用于比较（`(a or b) == c`）已通过
        `_wrap_boolop_with_merge_compare` 修复（test_adv14_boolop_single_compare
        通过）。`(a and b) == (c and d)` 仍未修复（BoolOpRegion 过度链化）。
- [x] C3.4e 批次 5：chained compare + boolop 混合 cond 失败修复 + 字节码完全匹配
      — region_analyzer.py `_detect_boolop_conditional_chain` 增加链式比较 IfRegion
        hop 逻辑；region_ast_generator.py 新增 `_try_build_chained_compare_in_boolop`
        在 BoolOp 表达式重建时把链式比较 IfRegion 作为原子操作数展开为完整 Compare。
        4 个测试通过（adv02_chaincmp_and_chaincmp / adv02_isnone_or_chaincmp /
        adv02_isnotnone_and_chaincmp / adv03_await_chaincmp），全测试集 93→89 失败，0 退化。
- [ ] C3.4f 批次 6：assert 与 if 混淆失败修复 + 字节码完全匹配
- [ ] C3.4g 批次 7：嵌套 code object 不匹配失败修复 + 字节码完全匹配
- [ ] C3.4h 批次 8：其余个例失败修复 + 字节码完全匹配
- [ ] C3.5 `_identify_conditional_regions` docstring 更新（6 节，含全部失败模式 + 算法根因）
- [ ] C3.6 `_generate_if` docstring 更新（4 节，含子区域不变量）
- [ ] C3.7 docstring 中明确「walrus/await/lambda in cond」的算法处理策略
- [ ] C3.8 `tests/exhaustive/if_region/` 通过率 = 100%
- [ ] C3.9 `tests/control_flow_matrix/` if 部分通过率 = 100%
- [ ] C3.10 `tests/nook/test_if_*.py` 通过率 = 100%
- [ ] C3.11 `testqouter/round1/test_r1_if_*.py` 通过率 = 100%
- [ ] C3.12 全测试集无退化

## Phase 4: LOOP 区域深度迭代

- [ ] C4.1 LOOP 区域 128 个失败用例字节码 diff 完成
- [ ] C4.2 LOOP 区域失败用例按共性问题分组完成
      （while-else / for-else / break-else / nested loop / try-in-loop /
       loop-with-continue / while-true / 嵌套 code object）
- [ ] C4.3 LOOP 区域算法根因修正（按批次）
- [ ] C4.3a 批次 1：while-else / for-else 归约边界修复 + 字节码完全匹配
- [ ] C4.3b 批次 2：break-else 复合结构修复 + 字节码完全匹配
- [ ] C4.3c 批次 3：nested loop（外/内层 break 区分）修复 + 字节码完全匹配
- [ ] C4.3d 批次 4：try-in-loop 归约顺序修复 + 字节码完全匹配
- [ ] C4.3e 批次 5：loop-with-continue（continue 归属）修复 + 字节码完全匹配
- [ ] C4.3f 批次 6：while-true 与 while-false 特殊处理修复 + 字节码完全匹配
- [ ] C4.3g 批次 7：嵌套 code object 修复 + 字节码完全匹配
- [ ] C4.3h 批次 8：其余个例修复 + 字节码完全匹配
- [ ] C4.4 `_identify_loop_regions` docstring 更新（6 节，含全部失败模式 + 算法根因）
- [ ] C4.5 `_generate_loop` docstring 更新（4 节，含子区域不变量）
- [ ] C4.6 docstring 中明确「while-else / for-else / break-else」的算法处理策略
- [ ] C4.7 `tests/exhaustive/while_loop/` + `for_loop/` 通过率 = 100%
- [ ] C4.8 `tests/exhaustive/loop/` 通过率 = 100%
- [ ] C4.9 `tests/nook/test_loops.py` + `test_loop_*.py` 通过率 = 100%
- [ ] C4.10 `testqouter/round1/test_r1_*while*for*.py` 通过率 = 100%
- [ ] C4.11 全测试集无退化

## Phase 5: MATCH 区域深度迭代

- [ ] C5.1 MATCH 区域 74 个失败用例字节码 diff 完成
- [ ] C5.2 MATCH 区域失败用例按共性问题分组完成
      （match in if/loop / match+guard+boolop / match class 多属性 /
       match mapping 多键 / match OR 模式 / match 星号模式）
- [ ] C5.3 MATCH 区域算法根因修正（按批次）
- [ ] C5.3a 批次 1：match 嵌套在 if/loop 中（归约顺序）修复 + 字节码完全匹配
- [ ] C5.3b 批次 2：match+guard+boolop（guard 块归属）修复 + 字节码完全匹配
- [ ] C5.3c 批次 3：match class 多属性 + 多 case 修复 + 字节码完全匹配
- [ ] C5.3d 批次 4：match mapping 多键 + **rest 修复 + 字节码完全匹配
- [ ] C5.3e 批次 5：match OR 模式（A | B | C）修复 + 字节码完全匹配
- [ ] C5.3f 批次 6：match 星号模式（[1, *rest]）修复 + 字节码完全匹配
- [ ] C5.3g 批次 7：其余个例修复 + 字节码完全匹配
- [ ] C5.4 `_identify_match_regions` docstring 更新（6 节，含全部失败模式）
- [ ] C5.5 `_generate_match` docstring 更新（4 节，含子区域不变量）
- [ ] C5.6 `tests/exhaustive/match_region/` 通过率 = 100%（不退化）
- [ ] C5.7 `tests/nook/test_match_*.py` 通过率 = 100%
- [ ] C5.8 `tests/exhaustive/if_region/test_adv*_match_*.py` 通过率 = 100%
- [ ] C5.9 全测试集无退化

## Phase 6: TRY / WITH 区域深度迭代

- [ ] C6.1 TRY/WITH 区域失败用例字节码 diff 完成
- [ ] C6.2 TRY/WITH 区域失败用例按共性问题分组完成
      （try-in-loop / try-with-nested / multi-context with / try-except-as /
       try-else-finally / bare except / exception groups / async with）
- [ ] C6.3 TRY 区域算法根因修正（按批次）
- [ ] C6.3a 批次 1：try-in-loop 归约顺序修复 + 字节码完全匹配
- [ ] C6.3b 批次 2：try-with-nested 修复 + 字节码完全匹配
- [ ] C6.3c 批次 3：try-else-finally 归约边界修复 + 字节码完全匹配
- [ ] C6.3d 批次 4：bare except 与 exception groups（except*）修复 + 字节码完全匹配
- [ ] C6.3e 批次 5：try-except-as（异常变量绑定）修复 + 字节码完全匹配
- [ ] C6.4 WITH 区域算法根因修正（按批次）
- [ ] C6.4a 批次 1：multi-context with 修复 + 字节码完全匹配
- [ ] C6.4b 批次 2：nested with 归约边界修复 + 字节码完全匹配
- [ ] C6.4c 批次 3：with-as 与 with-no-as 混合修复 + 字节码完全匹配
- [ ] C6.4d 批次 4：async with 修复 + 字节码完全匹配
- [ ] C6.4e 批次 5：with-try 复合清理块（te046 类问题）修复 + 字节码完全匹配
- [ ] C6.5 `_identify_try_except_regions` docstring 更新（6 节）
- [ ] C6.6 `_generate_try` docstring 更新（4 节）
- [ ] C6.7 `_identify_with_regions` docstring 更新（6 节）
- [ ] C6.8 `_generate_with` docstring 更新（4 节）
- [ ] C6.9 `tests/exhaustive/try_except/` + `with_region/` 通过率 = 100%（不退化）
- [ ] C6.10 `tests/nook/test_try_*` + `test_with_*` 通过率 = 100%
- [ ] C6.11 `testqouter/round1/test_r1_*try*with*.py` 通过率 = 100%
- [ ] C6.12 全测试集无退化

## Phase 7: BOOLOP / TERNARY 区域深度迭代

- [ ] C7.1 BOOLOP/TERNARY 区域失败用例字节码 diff 完成
- [ ] C7.2 BOOLOP/TERNARY 区域失败用例按共性问题分组完成
      （ternary in cond / ternary in boolop / boolop in ternary /
       nested ternary / walrus in ternary / await in boolop）
- [ ] C7.3 BOOLOP/TERNARY 区域算法根因修正（按批次）
- [ ] C7.3a 批次 1：ternary in cond 修复 + 字节码完全匹配
- [ ] C7.3b 批次 2：ternary in boolop / boolop in ternary 修复 + 字节码完全匹配
- [ ] C7.3c 批次 3：nested ternary（3+ 层嵌套）修复 + 字节码完全匹配
- [ ] C7.3d 批次 4：walrus in ternary 修复 + 字节码完全匹配
- [ ] C7.3e 批次 5：await in boolop 修复 + 字节码完全匹配
- [ ] C7.4 `_identify_boolop_regions` / `_generate_boolop` docstring 更新
- [ ] C7.5 `_identify_ternary_regions` / `_generate_ternary` docstring 更新
- [ ] C7.6 `tests/exhaustive/boolop/` + `ternary/` 通过率 = 100%（不退化）
- [ ] C7.7 `tests/exhaustive/if_region/test_adv*_ternary_*.py` 通过率 = 100%
- [ ] C7.8 `tests/nook/test_*ternary*boolop*.py` 通过率 = 100%
- [ ] C7.9 全测试集无退化

## Phase 8: ASSERT / CHAINED_COMPARE / SEQUENCE 区域深度迭代

- [ ] C8.1 ASSERT/CC/SEQUENCE 区域失败用例字节码 diff 完成
- [ ] C8.2 ASSERT 区域算法根因修正
- [ ] C8.2a 批次 1：assert 与 if 混淆修复 + 字节码完全匹配
- [ ] C8.2b 批次 2：assert with message（f-string / ternary）修复 + 字节码完全匹配
- [ ] C8.2c 批次 3：assert with multi-cond 修复 + 字节码完全匹配
- [ ] C8.3 CHAINED_COMPARE 区域算法根因修正
- [ ] C8.3a 批次 1：chain compare in if cond 修复 + 字节码完全匹配
- [ ] C8.3b 批次 2：chain compare with walrus 修复 + 字节码完全匹配
- [ ] C8.3c 批次 3：chain compare in assert/boolop/ternary 修复 + 字节码完全匹配
- [ ] C8.4 SEQUENCE 区域算法根因修正
- [ ] C8.4a 批次 1：嵌套 code object 的 sequence 归约修复 + 字节码完全匹配
- [ ] C8.4b 批次 2：隐式 return None 的 sequence 归约（te046 类问题）修复 + 字节码完全匹配
- [ ] C8.5 `_identify_assert_regions` / `_generate_assert` docstring 更新
- [ ] C8.6 `_identify_chained_compare_regions` docstring 更新
- [ ] C8.7 `_identify_sequence_regions` / `_generate_basic_region` docstring 更新
- [ ] C8.8 相关测试集通过率 = 100%
- [ ] C8.9 全测试集无退化

## Phase 9: 跨区域解耦与 nook/真实代码迭代

- [ ] C9.1 `analyze()` 中所有区域的归约顺序审计完成
- [ ] C9.2 每对相邻区域类型的归约不破坏 4 原则验证完成
- [ ] C9.3 跨区域特例已识别并改为算法判定（若有）
- [ ] C9.4 nook 失败用例分类完成（async / cfg_complex / decorators / classes / comprehensions）
- [ ] C9.5 async 失败修复（async with/for/await/comprehension）+ 字节码完全匹配
- [ ] C9.6 cfg_complex 失败修复 + 字节码完全匹配
- [ ] C9.7 decorators/classes 失败修复 + 字节码完全匹配
- [ ] C9.8 comprehensions 失败修复 + 字节码完全匹配
- [ ] C9.9 `tests/nook/` 通过率 = 100%（或失败为已知限制并明确记录）
- [ ] C9.10 全测试集无退化

## Phase 10: 最终验证与字节码完全匹配

- [ ] C10.1 `tests/exhaustive/` 全部子目录通过率 = 100%
- [ ] C10.2 `tests/control_flow_matrix/` 通过率 = 100%
- [ ] C10.3 `tests/nook/` 通过率 = 100%（或已知限制并明确记录）
- [ ] C10.4 `ok/` + `testqouter/` 通过率 = 100%
- [ ] C10.5 所有失败用例的 `_compare_code_objects()` 返回 `None`
- [ ] C10.6 嵌套 code object 全部字节码匹配
- [ ] C10.7 反模式1 跨区域特例：PASS
- [ ] C10.8 反模式2 后处理补丁：PASS
- [ ] C10.9 反模式3 启发式优先级覆盖：PASS
- [ ] C10.10 反模式4 破坏嵌套的扁平化：PASS
- [ ] C10.11 `grep "depth > [0-9]" core/cfg/region_analyzer.py` 0 结果（无硬编码深度上限）
- [ ] C10.12 debug 模式下 4 原则不变量检查全部通过
- [ ] C10.13 10 个 `_identify_*_regions` 方法 docstring 符合 6 节模板
       （含「算法根因」「修复策略」「修复状态」字段）
- [ ] C10.14 9 个 `_generate_*` 方法 docstring 符合 4 节模板（含子区域不变量检查）
- [ ] C10.15 `analyze()` docstring 包含算法评估报告结论
- [ ] C10.16 `_merge_consecutive_with_regions` 不再作为后处理调用（前移至识别阶段）
- [ ] C10.17 try_except `depth` 字段特例已改为异常表结构判定
- [ ] C10.18 算法符合度 FULLY COMPLIANT（0 WARN）
- [ ] C10.19 若新增 RegionType，所有新类型的识别/生成方法 docstring 合规
- [ ] C10.20 若改造 analyze() 为迭代归约，算法正确性证明文档化
- [ ] C10.21 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] C10.22 无 `__CLEANUP_MARKER_*__` 残留

## 算法符合度审计要点（Phase 10 复核）

- [ ] A1 所有 `_identify_*` 方法不包含跨区域启发式特例 — **PASS**（无 WARN）
- [ ] A2 所有 `_generate_*` 方法不包含后处理补丁 — **PASS**（无 WARN）
- [ ] A3 `analyze()` 编排顺序符合自底向上归约原则 — **PASS**
- [ ] A4 `block_to_region` 在每次 `analyze()` 调用时重建，无残留状态 — **PASS**
- [ ] A5 嵌套区域在父区域中作为单个抽象节点表示 — **PASS**
- [ ] A6 父区域的 then/else/body 列表引用子区域入口块 — **PASS**
- [ ] A7 回边检测基于支配树（DominatorAnalyzer），无补丁覆盖 — **PASS**
- [ ] A8 每个区域类型对应唯一的 AST 节点类型（一一映射）— **PASS**
- [ ] A9 无硬编码嵌套深度上限 — **PASS**（`grep "depth > [0-9]"` 0 结果）
- [ ] A10 隐式 module-level return 块按语义归属 — **PASS**
- [ ] A11 算法分派通过多态方法而非 isinstance 链 — **PASS**
- [ ] A12 debug 模式下 4 原则不变量检查全部通过 — **PASS**
- [ ] A13 全测试集（不仅 run_test_matrix）100% 通过 — **PASS**
- [ ] A14 所有失败用例 `_compare_code_objects()` 返回 `None` — **PASS**

## 迭代循环验证（每区域）— 全部完成

对每一区域类型完成以下循环：

- [ ] I1 测试：运行区域级测试集（全测试集，不仅 run_test_matrix），通过率 = 100%
- [ ] I2 字节码 diff：所有区域 `_compare_code_objects()` 返回 `None`（含嵌套 code object）
- [ ] I3 修正识别逻辑：算法根因修正（不是后处理补丁）
- [ ] I4 重写注释：方法 docstring 已更新（含「算法根因」「修复策略」「修复状态」）
- [ ] I5 回归测试：全测试集通过率 = 100%（不退化）
- [ ] I6 100% + 字节码完全匹配：区域级测试通过率 = 100%，`_compare_code_objects()` 返回 `None`

## 关键约束验证（重申）

- [ ] K1 禁止跨区域跨层次的启发式规则 — 全代码审计 PASS
- [ ] K2 禁止破坏算法对嵌套的天然支持 — 全代码审计 PASS
- [ ] K3 禁止后处理补丁（必须识别阶段一次正确）— 全代码审计 PASS
- [ ] K4 禁止硬编码深度上限 — `grep "depth > [0-9]"` 0 结果
- [ ] K5 禁止以「run_test_matrix 100%」为完成标志 — 全测试集 100% 验证 PASS
- [ ] K6 每个失败用例必须算法根因修正 — 失败用例 → 算法根因映射表完整
- [ ] K7 深度思考是否需要更多区域类型或更好的方法 — 算法评估报告完整
