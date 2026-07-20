# Tasks

> 目标：从「run_test_matrix 100%」虚假完成 → 「全测试集 100% + 字节码完全匹配」真实完成。
> 通过算法根本性反思 + 每区域深度迭代循环，消除 200+ 失败用例。
> 所有任务遵守区域归约算法 4 原则：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口。
> 每区域循环：**测试 → 字节码 diff → 算法根因修正 → 注释重写 → 回归测试**。
>
> **当前已知失败基线**（来自仓库内 .txt 文件）:
> - `if_region_failures.txt`: ~75 失败（指令数不匹配 / 区域未识别 / 语法错误）
> - `loop_errors.txt`: 128 失败 / 181 通过
> - `match_errors.txt`: 74 失败 / 93 通过
> - `tests/nook/`: 13 failures + 25 errors（前置 spec Phase 5.3 记录）
> - `tests/control_flow_matrix/`: 未纳入 run_test_matrix，未知失败数
>
> **核心约束**:
> - 禁止跨区域跨层次的启发式规则
> - 禁止破坏算法对嵌套的天然支持
> - 禁止后处理补丁（必须识别阶段一次正确）
> - 禁止硬编码深度上限
> - 每个修改后全测试集回归，不退化

## Phase 0: 全测试集基线建立 — 算法反思前置

> **目标**：建立全测试集基线 + 失败用例 → 区域类型 → 算法根因映射表。
> 不修改任何测试，仅运行并归档结果。

- [ ] Task 0.1: 建立全测试集运行脚本
  - [ ] 子任务：扫描 `tests/exhaustive/{if_region,loop,with_region,try_except,match_region}/`
        全部测试用例，统计通过/失败/跳过
  - [ ] 子任务：扫描 `tests/control_flow_matrix/` 全部测试用例
  - [ ] 子任务：扫描 `tests/nook/` 全部测试用例
  - [ ] 子任务：扫描 `ok/` + `testqouter/round1/round2/round3/` 全部测试用例
  - [ ] 子任务：合并为「全测试集基线报告」（含每测试集通过率 + 总通过率）
- [ ] Task 0.2: 失败用例分类与算法根因映射
  - [ ] 子任务：对每个失败用例执行 `_compare_code_objects(original, recompiled)`，
        记录差异类型（指令数 / 操作码 / 参数 / 嵌套 code object / 语法错误 / 区域未识别）
  - [ ] 子任务：按区域类型（IF/LOOP/TRY/WITH/MATCH/ASSERT/BOOLOP/TERNARY/CC/SEQ）分类
  - [ ] 子任务：对每类失败，分析算法根因（不是个别 case 修补）
  - [ ] 子任务：输出「失败用例 → 区域类型 → 算法根因」映射表
        （保存为 `failures_root_causes.md`）

## Phase 1: 算法根本性反思

> **目标**：基于 Phase 0 的根因映射表，深度反思是否需要更多区域类型或更好的方法。
> 输出「算法评估报告」（保存为 `algorithm_evaluation.md`）。

- [ ] Task 1.1: 现有 19 个 RegionType 覆盖范围审计
  - [ ] 子任务：对每个 RegionType，列出能正确识别的字节码模式（含具体测试用例）
  - [ ] 子任务：列出不能识别的字节码模式（含具体失败用例）
  - [ ] 子任务：识别「该类型不足以覆盖」的情况（候选新类型）
- [ ] Task 1.2: 新区域类型论证
  - [ ] 子任务：论证 `WITH_EXIT`（with 清理块作为独立区域）的必要性与风险
  - [ ] 子任务：论证 `LOOP_ELSE`（for/while-else 的 else 作为独立区域）的必要性与风险
  - [ ] 子任务：论证 `MATCH_GUARD`（match case 的 guard 作为独立区域）的必要性与风险
  - [ ] 子任务：论证 `IMPLICIT_RETURN`（隐式 return None 作为独立区域）的必要性与风险
  - [ ] 子任务：论证 `ASYNC_WITH` / `ASYNC_FOR`（异步语义区域）的必要性与风险
  - [ ] 子任务：对每个候选，输出「采用 / 不采用 + 理由」结论
- [ ] Task 1.3: 新方法论证
  - [ ] 子任务：论证「迭代归约」替代「固定优先级流水线」的可行性与风险
        （含算法正确性证明：满足 4 原则）
  - [ ] 子任务：论证「异常表驱动识别」替代「指令模式匹配」的可行性与风险
  - [ ] 子任务：论证「支配树驱动边界」替代「跳转目标距离启发式」的可行性与风险
  - [ ] 子任务：对每个候选方法，输出「采用 / 不采用 + 理由」结论
- [ ] Task 1.4: 2 个 WARN 消除方案
  - [ ] 子任务：设计 `_merge_consecutive_with_regions` 前移至识别阶段的方案
  - [ ] 子任务：设计 try_except `depth` 字段特例改为异常表结构判定的方案
  - [ ] 子任务：评估两个方案的风险（含回归测试集）
- [ ] Task 1.5: 输出算法评估报告
  - [ ] 子任务：合并 Task 1.1-1.4 结果为 `algorithm_evaluation.md`
  - [ ] 子任务：报告中每个候选有明确「采用 / 不采用」结论
  - [ ] 子任务：报告中列出本 spec 后续 Phase 的优先级与依赖关系

## Phase 2: 算法基础重构（基于 Phase 1 结论）

> **目标**：实施 Phase 1 论证通过的新区域类型 / 新方法 / WARN 消除方案。
> 每步小步快跑 + 全测试集回归。

- [ ] Task 2.1: 实施 2 个 WARN 消除（最低风险，最高优先级）
  - [ ] 子任务：`_merge_consecutive_with_regions` 前移至 `_identify_with_regions`
  - [ ] 子任务：try_except `depth` 字段特例改为异常表结构判定
  - [ ] 子任务：全测试集回归（不退化）
- [ ] Task 2.2: 实施新区域类型（若 Phase 1 论证通过）
  - [ ] 子任务：在 `RegionType` 枚举中新增成员
  - [ ] 子任务：实现 `_identify_<new>_regions` 方法（6 节模板 docstring）
  - [ ] 子任务：实现 `_generate_<new>` 方法（4 节模板 docstring）
  - [ ] 子任务：在 `analyze()` 中编排新类型的归约顺序
  - [ ] 子任务：全测试集回归（不退化）
- [ ] Task 2.3: 实施新方法（若 Phase 1 论证通过）
  - [ ] 子任务：若采用迭代归约，改造 `analyze()` 为迭代归约循环
  - [ ] 子任务：若采用异常表驱动，重构 `_identify_try_except_regions`
  - [ ] 子任务：若采用支配树驱动，重构 if/loop 区域边界判定
  - [ ] 子任务：全测试集回归（不退化）
- [ ] Task 2.4: 算法 4 原则不变量检查
  - [ ] 子任务：在 `analyze()` 末尾增加「每块唯一归属」不变量检查（debug 模式）
  - [ ] 子任务：在 `_generate_*` 中增加「子区域抽象节点」不变量检查（debug 模式）
  - [ ] 子任务：在 `_generate_*` 中增加「入口引用语义」不变量检查（debug 模式）
  - [ ] 子任务：全测试集回归（debug 模式下不变量全部通过）

## Phase 2.5: CPython Peephole 模式库（反思第 4 块）

> **目标**：重建 CPython 3.11+ peephole 优化器产生的「反归约」字节码模式库，
> 让区域识别阶段一次正确处理这些模式，避免后处理补丁。
> 4 块反思：迭代归约 + 异常表驱动 + 支配树驱动 + **CPython peephole 模式库**。

- [x] Task 2.5.1: P1 模式（module-level/function-tail 三元表达式语句 → double RETURN_VALUE）
  - [x] 子任务：在 `peephole_patterns.py` 中建立 P1 模式识别库
  - [x] 子任务：TernaryRegion 增加 `has_pop_top` 字段区分三元与 if-return
  - [x] 子任务：115/116 ternary 测试通过（1 跳过）
- [x] Task 2.5.2: P1 if-return 与三元表达式区分
  - [x] 子任务：含 POP_TOP → 三元表达式语句；不含 POP_TOP → if-return
  - [x] 子任务：让 IfRegion 处理 if-return 模式
- [x] Task 2.5.3: P1 peephole 模式库测试覆盖
  - [x] Task 2.5.3a: P1 peephole 模式库测试覆盖（ternary 全集）
  - [x] Task 2.5.3b: Scenario B 修复（while 条件位三元：merge_block IS LoopRegion.header_block）
  - [x] Task 2.5.3c: P1 if-return 修复（peephole_patterns.py 让 IfRegion 处理 if-return）
  - [x] Task 2.5.3d: bool03_not 测试框架识别 UnaryOp(Not) 作为 BOOL_OP
  - [x] Task 2.5.3e: bool20_complex_logic 修复（混合 and/or 链不丢中间操作数）
        - 算法根因：CPython 3.11 为每个操作数的短路目标发射独立的 trivial exit 块，
          链检测因 target 不同而中断。修正：在 `_detect_boolop_conditional_chain`
          两处（链中断判定 + all_same_target 循环）增加 `_is_equivalent_exit_block` 检查。
  - [x] Task 2.5.3f: bool19_ternary_combo 修复（or None 尾部操作数保留）
        - 算法根因：`_build_grouped_boolop_expression` 只迭代 `op_chain` 块，
          但最后一个 `None` 操作数位于最后链块的 fall-through 块（无条件跳转）。
          修正：增加 fall-through 块处理逻辑，提取最终外部操作数。
  - [x] Task 2.5.3g: bool11_in_while 修复（while 条件位 and 链不被拆分为 if+while+if）
        - 算法根因 1：`_identify_loop_regions` 反向走查只接受 jump target 为 _cb/body/header
          的前驱。对于 `not done and has_data()`，`not done` 块的 target 是 trivial exit
          块（与 condition_block 的 exit 等价）。修正：增加 `_is_equivalent_exit` 检查
          与 `_back_edge_recheck_count` 配额（限制接受数量等于 back-edge 重评估操作数数），
          避免误吸外层 `if` 条件块。
        - 算法根因 2：重分类逻辑将首块 IF_TRUE 误判为 `X or Y`。修正：增加合并块
          判别 — IF_TRUE target 是合并块（最后块的非跳转后继）→ `X or Y`；
          IF_TRUE target 是 exit → `not X and Y`。
        - 算法根因 3：CPython 3.11 优化掉 UNARY_NOT 通过反转跳转方向。修正：在
          `_build_boolop_expression` 与 `_build_grouped_boolop_expression` 中，
          当 chain_op 是 'and' 且跳转是 IF_TRUE 时，对操作数包裹 `UnaryOp(not, ...)`。
        - 算法根因 4：back-edge 条件重查块（无 STORE）被误识为 IfRegion。修正：在
          `_should_skip_block_for_if_region` 的 `not _has_store_before_cond` 分支
          增加 back-edge 重查检测（fallthrough 是 LOOP_BACK_EDGE 且 jump target 是 BREAK）。
        - 算法根因 5：boolop 链检测的 `_equivalent_exits` 过宽导致 ternary12 退化。
          修正：增加 Scenario B 三元守卫 — 走查 fallthrough 链查找 JUMP_FORWARD 到
          循环头（有反向边前驱），若命中则断链让 TernaryRegion 识别器接管。
- [ ] Task 2.5.4: P3 模式（while-true + break）枚举
- [ ] Task 2.5.5: P4 模式（chained compare）枚举
- [ ] Task 2.5.6: P5+ 模式（CPython peephole 全模式枚举）
- [ ] Task 2.5.7: CPython 模式库全测试集回归

## Phase 3: IF 区域深度迭代

> **目标**：IF 区域全测试集 100% + 字节码完全匹配。
> 失败用例基线：`if_region_failures.txt` ~75 失败。
> 测试集：`tests/exhaustive/if_region/`（~370 用例） + `tests/control_flow_matrix/test_l1_basic.py`
> 中 if 部分 + `tests/nook/test_if_*.py` + `testqouter/round1/test_r1_if_*.py`

- [ ] Task 3.1: IF 区域失败用例分类与根因分析
  - [ ] 子任务：对 75 个失败用例执行字节码 diff
  - [ ] 子任务：按失败类型分类（指令数 / 操作码 / 语法错误 / 区域未识别）
  - [ ] 子任务：识别共性问题（如 walrus in cond / nested ternary in cond / await in cond）
- [ ] Task 3.2: IF 区域算法根因修正（按共性根因分批）
  - [ ] 子任务：批次 1 — walrus in cond 失败（如 `test_adv01_simple_walrus.py`）
  - [ ] 子任务：批次 2 — nested ternary in cond 失败（如 `test_adv01_nested_ternary_cond.py`）
  - [ ] 子任务：批次 3 — await in cond 失败（如 `test_adv01_await_compare.py`）
  - [ ] 子任务：批次 4 — lambda call in cond 失败（如 `test_adv01_lambda_call_cond.py`）
  - [ ] 子任务：批次 5 — chained compare + boolop 混合 cond 失败
  - [ ] 子任务：批次 6 — assert 与 if 混淆（LOAD_ASSERTION_ERROR vs LOAD_CONST）
  - [ ] 子任务：批次 7 — 嵌套 code object 不匹配（如 class_def_in_if）
  - [ ] 子任务：批次 8 — 其余个例
- [ ] Task 3.3: IF 区域注释重写
  - [ ] 子任务：更新 `_identify_conditional_regions` docstring（6 节，含全部失败模式 + 算法根因）
  - [ ] 子任务：更新 `_generate_if` docstring（4 节，含子区域不变量）
  - [ ] 子任务：注释中明确「walrus/await/lambda in cond」的算法处理策略
- [ ] Task 3.4: IF 区域全测试集回归
  - [ ] 子任务：`tests/exhaustive/if_region/` 通过率 = 100%
  - [ ] 子任务：`tests/control_flow_matrix/` if 部分通过率 = 100%
  - [ ] 子任务：`tests/nook/test_if_*.py` 通过率 = 100%
  - [ ] 子任务：`testqouter/round1/test_r1_if_*.py` 通过率 = 100%
  - [ ] 子任务：全测试集无退化

## Phase 4: LOOP 区域深度迭代

> **目标**：LOOP 区域全测试集 100% + 字节码完全匹配。
> 失败用例基线：`loop_errors.txt` 128 失败 / 181 通过。
> 测试集：`tests/exhaustive/while_loop/` + `tests/exhaustive/for_loop/` +
> `tests/exhaustive/loop/`（含 while01-while20 + wl01-wl32 + while_loop 子目录） +
> `tests/nook/test_loops.py` + `testqouter/round1/test_r1_*while*for*.py`

- [ ] Task 4.1: LOOP 区域失败用例分类与根因分析
  - [ ] 子任务：对 128 个失败用例执行字节码 diff
  - [ ] 子任务：按失败类型分类
  - [ ] 子任务：识别共性问题（while-else / for-else / break-else / nested loop /
        try-in-loop / loop-with-continue）
- [ ] Task 4.2: LOOP 区域算法根因修正（按共性根因分批）
  - [ ] 子任务：批次 1 — while-else / for-else 归约边界（评估是否需要 LOOP_ELSE 新类型）
  - [ ] 子任务：批次 2 — break-else 复合结构（break 与 else 的语义绑定）
  - [ ] 子任务：批次 3 — nested loop（外层 break 与内层 break 的区分）
  - [ ] 子任务：批次 4 — try-in-loop（try 与 loop 的归约顺序）
  - [ ] 子任务：批次 5 — loop-with-continue（continue 的归属）
  - [ ] 子任务：批次 6 — while-true 与 while-false 的特殊处理
  - [ ] 子任务：批次 7 — 嵌套 code object（lambda/listcomp in loop body）
  - [ ] 子任务：批次 8 — 其余个例
- [ ] Task 4.3: LOOP 区域注释重写
  - [ ] 子任务：更新 `_identify_loop_regions` docstring（6 节，含全部失败模式 + 算法根因）
  - [ ] 子任务：更新 `_generate_loop` docstring（4 节，含子区域不变量）
  - [ ] 子任务：注释中明确「while-else / for-else / break-else」的算法处理策略
- [ ] Task 4.4: LOOP 区域全测试集回归
  - [ ] 子任务：`tests/exhaustive/while_loop/` + `for_loop/` 通过率 = 100%
  - [ ] 子任务：`tests/exhaustive/loop/` 通过率 = 100%
  - [ ] 子任务：`tests/nook/test_loops.py` + `test_loop_*.py` 通过率 = 100%
  - [ ] 子任务：`testqouter/round1/test_r1_*while*for*.py` 通过率 = 100%
  - [ ] 子任务：全测试集无退化

## Phase 5: MATCH 区域深度迭代

> **目标**：MATCH 区域全测试集 100% + 字节码完全匹配。
> 失败用例基线：`match_errors.txt` 74 失败 / 93 通过。
> 测试集：`tests/exhaustive/match_region/`（198 用例，已 100%） +
> `tests/exhaustive/loop/` 中的 match 部分 + `tests/nook/test_match_*.py` +
> `tests/exhaustive/if_region/test_adv16_match_*.py` + `test_adv10_match_*.py` +
> `test_adv06_match_*.py` + `test_adv07_match_*.py`

- [ ] Task 5.1: MATCH 区域失败用例分类与根因分析
  - [ ] 子任务：对 74 个失败用例执行字节码 diff
  - [ ] 子任务：识别共性问题（match in if / match in loop / match+guard+boolop /
        match class 多属性 / match mapping 多键 / match OR 模式 / match 星号模式）
- [ ] Task 5.2: MATCH 区域算法根因修正
  - [ ] 子任务：批次 1 — match 嵌套在 if/loop 中（归约顺序问题）
  - [ ] 子任务：批次 2 — match+guard+boolop（guard 块归属）
  - [ ] 子任务：批次 3 — match class 多属性 + 多 case
  - [ ] 子任务：批次 4 — match mapping 多键 + **rest
  - [ ] 子任务：批次 5 — match OR 模式（A | B | C）
  - [ ] 子任务：批次 6 — match 星号模式（[1, *rest]）
  - [ ] 子任务：批次 7 — 其余个例
- [ ] Task 5.3: MATCH 区域注释重写
  - [ ] 子任务：更新 `_identify_match_regions` docstring（6 节，含全部失败模式）
  - [ ] 子任务：更新 `_generate_match` docstring（4 节，含子区域不变量）
- [ ] Task 5.4: MATCH 区域全测试集回归
  - [ ] 子任务：`tests/exhaustive/match_region/` 通过率 = 100%（不退化）
  - [ ] 子任务：`tests/nook/test_match_*.py` 通过率 = 100%
  - [ ] 子任务：`tests/exhaustive/if_region/test_adv*_match_*.py` 通过率 = 100%
  - [ ] 子任务：全测试集无退化

## Phase 6: TRY / WITH 区域深度迭代

> **目标**：TRY 与 WITH 区域全测试集 100% + 字节码完全匹配。
> 测试集：`tests/exhaustive/try_except/`（230，已 100%） + `with_region/`（191，已 100%）
> + `tests/exhaustive/loop/` 中 try/with 部分 + `tests/nook/test_try_*` + `test_with_*`
> + `testqouter/round1/test_r1_*try*with*.py` + `test_e01-e13` + `test_w01-w06`

- [ ] Task 6.1: TRY/WITH 区域失败用例分类与根因分析
  - [ ] 子任务：扫描全部 try/with 失败用例
  - [ ] 子任务：识别共性问题（try-in-loop / try-with-nested / multi-context with /
        try-except-as / try-else-finally / bare except / exception groups）
- [ ] Task 6.2: TRY 区域算法根因修正
  - [ ] 子任务：批次 1 — try-in-loop 归约顺序（依赖 Phase 4 LOOP 修复）
  - [ ] 子任务：批次 2 — try-with-nested（嵌套 with 在 try 内）
  - [ ] 子任务：批次 3 — try-else-finally（else 与 finally 的归约边界）
  - [ ] 子任务：批次 4 — bare except 与 exception groups（Python 3.11+ except*）
  - [ ] 子任务：批次 5 — try-except-as（异常变量绑定）
- [ ] Task 6.3: WITH 区域算法根因修正
  - [ ] 子任务：批次 1 — multi-context with（评估是否需要 WITH_EXIT 新类型）
  - [ ] 子任务：批次 2 — nested with（嵌套 with 的归约边界）
  - [ ] 子任务：批次 3 — with-as 与 with-no-as 混合
  - [ ] 子任务：批次 4 — async with（评估是否需要 ASYNC_WITH 新类型）
  - [ ] 子任务：批次 5 — with-try 复合清理块（te046 类问题）
- [ ] Task 6.4: TRY/WITH 区域注释重写
  - [ ] 子任务：更新 `_identify_try_except_regions` docstring
  - [ ] 子任务：更新 `_generate_try` docstring
  - [ ] 子任务：更新 `_identify_with_regions` docstring
  - [ ] 子任务：更新 `_generate_with` docstring
- [ ] Task 6.5: TRY/WITH 区域全测试集回归
  - [ ] 子任务：`tests/exhaustive/try_except/` + `with_region/` 通过率 = 100%（不退化）
  - [ ] 子任务：`tests/nook/test_try_*` + `test_with_*` 通过率 = 100%
  - [ ] 子任务：`testqouter/round1/test_r1_*try*with*.py` 通过率 = 100%
  - [ ] 子任务：全测试集无退化

## Phase 7: BOOLOP / TERNARY 区域深度迭代

> **目标**：BOOLOP 与 TERNARY 区域全测试集 100% + 字节码完全匹配。
> 测试集：`tests/exhaustive/boolop/`（132，已 100%） + `ternary/`（116，已 100%）
> + `tests/exhaustive/if_region/test_adv01-adv15` 中 boolop/ternary 部分 +
> `tests/nook/test_*ternary*boolop*.py`

- [ ] Task 7.1: BOOLOP/TERNARY 区域失败用例分类与根因分析
  - [ ] 子任务：扫描全部 boolop/ternary 失败用例（来自 if_region_adv 与 nook）
  - [ ] 子任务：识别共性问题（ternary in cond / ternary in boolop /
        boolop in ternary / nested ternary / walrus in ternary / await in boolop）
- [ ] Task 7.2: BOOLOP/TERNARY 区域算法根因修正
  - [ ] 子任务：批次 1 — ternary in cond（与 IF 区域协同）
  - [ ] 子任务：批次 2 — ternary in boolop / boolop in ternary
  - [ ] 子任务：批次 3 — nested ternary（3+ 层嵌套）
  - [ ] 子任务：批次 4 — walrus in ternary（walrus 与 ternary 的归约顺序）
  - [ ] 子任务：批次 5 — await in boolop（async 语义）
- [ ] Task 7.3: BOOLOP/TERNARY 区域注释重写
  - [ ] 子任务：更新 `_identify_boolop_regions` / `_generate_boolop` docstring
  - [ ] 子任务：更新 `_identify_ternary_regions` / `_generate_ternary` docstring
- [ ] Task 7.4: BOOLOP/TERNARY 区域全测试集回归
  - [ ] 子任务：`tests/exhaustive/boolop/` + `ternary/` 通过率 = 100%（不退化）
  - [ ] 子任务：`tests/exhaustive/if_region/test_adv*_ternary_*.py` 通过率 = 100%
  - [ ] 子任务：`tests/nook/test_*ternary*boolop*.py` 通过率 = 100%
  - [ ] 子任务：全测试集无退化

## Phase 8: ASSERT / CHAINED_COMPARE / SEQUENCE 区域深度迭代

> **目标**：ASSERT / CHAINED_COMPARE / SEQUENCE 区域全测试集 100%。
> 测试集：`tests/exhaustive/assert/`（如有） + `tests/exhaustive/chained_compare/`（如有）
> + `tests/exhaustive/basic/`（122，已 100%） + `tests/nook/test_*assert*.py` +
> `tests/exhaustive/if_region/test_adv04_assert_*.py` + `test_adv10_assert_*.py`

- [ ] Task 8.1: ASSERT/CC/SEQUENCE 区域失败用例分类与根因分析
- [ ] Task 8.2: ASSERT 区域算法根因修正
  - [ ] 子任务：批次 1 — assert 与 if 混淆（LOAD_ASSERTION_ERROR vs LOAD_CONST）
  - [ ] 子任务：批次 2 — assert with message（f-string / ternary in msg）
  - [ ] 子任务：批次 3 — assert with multi-cond（chain compare + boolop）
- [ ] Task 8.3: CHAINED_COMPARE 区域算法根因修正
  - [ ] 子任务：批次 1 — chain compare in if cond
  - [ ] 子任务：批次 2 — chain compare with walrus
  - [ ] 子任务：批次 3 — chain compare in assert/boolop/ternary
- [ ] Task 8.4: SEQUENCE 区域算法根因修正
  - [ ] 子任务：批次 1 — 嵌套 code object 的 sequence 归约
  - [ ] 子任务：批次 2 — 隐式 return None 的 sequence 归约（te046 类问题）
- [ ] Task 8.5: ASSERT/CC/SEQUENCE 区域注释重写
  - [ ] 子任务：更新 `_identify_assert_regions` / `_generate_assert` docstring
  - [ ] 子任务：更新 `_identify_chained_compare_regions` docstring
  - [ ] 子任务：更新 `_identify_sequence_regions` / `_generate_basic_region` docstring
- [ ] Task 8.6: ASSERT/CC/SEQUENCE 区域全测试集回归
  - [ ] 子任务：相关测试集通过率 = 100%
  - [ ] 子任务：全测试集无退化

## Phase 9: 跨区域解耦与 nook/真实代码迭代

> **目标**：解决跨区域交互问题 + nook 真实代码模式 100% 通过。
> nook 失败基线：13 failures + 25 errors（前置 spec Phase 5.3）。

- [ ] Task 9.1: 跨区域归约顺序验证
  - [ ] 子任务：审计 `analyze()` 中所有区域的归约顺序
  - [ ] 子任务：验证每对相邻区域类型的归约不破坏 4 原则
  - [ ] 子任务：识别跨区域特例（若有），改为算法判定
- [ ] Task 9.2: nook 真实代码模式迭代
  - [ ] 子任务：分类 nook 失败（async / cfg_complex / decorators / classes / comprehensions）
  - [ ] 子任务：async 失败修复（async with/for/await/comprehension）
  - [ ] 子任务：cfg_complex 失败修复
  - [ ] 子任务：decorators/classes 失败修复
  - [ ] 子任务：comprehensions 失败修复
- [ ] Task 9.3: nook 测试集回归
  - [ ] 子任务：`tests/nook/` 通过率 = 100%（或失败为已知限制并记录）
  - [ ] 子任务：全测试集无退化

## Phase 10: 最终验证与字节码完全匹配

> **目标**：全测试集 100% + 字节码完全匹配 + 算法 4 原则全部 PASS。

- [ ] Task 10.1: 全测试集 100% 验证
  - [ ] 子任务：`tests/exhaustive/` 全部子目录通过率 = 100%
  - [ ] 子任务：`tests/control_flow_matrix/` 通过率 = 100%
  - [ ] 子任务：`tests/nook/` 通过率 = 100%（或已知限制并记录）
  - [ ] 子任务：`ok/` + `testqouter/` 通过率 = 100%
- [ ] Task 10.2: 字节码完全匹配验证
  - [ ] 子任务：所有失败用例的 `_compare_code_objects()` 返回 `None`
  - [ ] 子任务：嵌套 code object 全部字节码匹配
- [ ] Task 10.3: 算法 4 原则最终审计
  - [ ] 子任务：反模式1 跨区域特例：PASS
  - [ ] 子任务：反模式2 后处理补丁：PASS
  - [ ] 子任务：反模式3 启发式优先级覆盖：PASS
  - [ ] 子任务：反模式4 破坏嵌套的扁平化：PASS
  - [ ] 子任务：无硬编码深度上限
  - [ ] 子任务：debug 模式下 4 原则不变量检查全部通过
- [ ] Task 10.4: docstring 模板合规验证
  - [ ] 子任务：10 个 `_identify_*_regions` 方法 docstring 符合 6 节模板
        （含「算法根因」「修复策略」「修复状态」字段）
  - [ ] 子任务：9 个 `_generate_*` 方法 docstring 符合 4 节模板
        （含子区域不变量检查）
  - [ ] 子任务：`analyze()` docstring 包含算法评估报告结论
- [ ] Task 10.5: 2 个 WARN 消除验证
  - [ ] 子任务：`_merge_consecutive_with_regions` 不再作为后处理调用
  - [ ] 子任务：try_except `depth` 字段特例已改为异常表结构判定
  - [ ] 子任务：算法符合度 FULLY COMPLIANT（0 WARN）
- [ ] Task 10.6: 累计验证
  - [ ] 子任务：若新增 RegionType，所有新类型的识别/生成方法 docstring 合规
  - [ ] 子任务：若改造 analyze() 为迭代归约，算法正确性证明文档化
  - [ ] 子任务：核心模块编译通过，无临时标记残留

# Task Dependencies

- Phase 0（基线建立）→ 所有后续 Phase
- Phase 1（算法反思）→ Phase 2（基础重构）→ Phase 3-8（每区域迭代）
- Phase 3（IF）可与 Phase 7（BOOLOP/TERNARY）协同（ternary in cond 共性问题）
- Phase 4（LOOP）可与 Phase 6（TRY/WITH）协同（try-in-loop 共性问题）
- Phase 5（MATCH）依赖 Phase 2 完成（若新增 MATCH_GUARD 类型）
- Phase 9（跨区域 + nook）依赖 Phase 3-8 完成
- Phase 10（最终验证）依赖 Phase 1-9 全部完成

# 并行化建议

- **第一轮（并行）**: Phase 0（基线） + Phase 1.1（19 RegionType 审计）
- **第二轮（串行）**: Phase 1.2-1.5（算法评估报告）
- **第三轮（串行）**: Phase 2.1（WARN 消除）→ Phase 2.2/2.3（新类型/新方法）→ Phase 2.4（不变量）
- **第四轮（部分并行）**:
  - Phase 3（IF） + Phase 4（LOOP） + Phase 5（MATCH） 可部分并行（不同区域）
  - Phase 6（TRY/WITH）依赖 Phase 4（try-in-loop）
  - Phase 7（BOOLOP/TERNARY）依赖 Phase 3（ternary in cond）
- **第五轮（串行）**: Phase 8（ASSERT/CC/SEQ） + Phase 9（跨区域 + nook）
- **第六轮**: Phase 10（最终验证）

# 验证标准（每个 Phase 完成的判定）

每个 Phase 完成时**必须**满足：
1. 该 Phase 涉及的所有识别/生成方法 docstring 符合统一模板（含「算法根因」节）
2. 该 Phase 涉及的测试集通过率 = 100%（或失败为已知限制并明确记录）
3. 该 Phase 涉及的所有失败用例的 `_compare_code_objects()` 返回 `None`
4. 该 Phase 的修改未引入其他测试集的回归
5. 算法符合度保持 FULLY COMPLIANT（4 条核心原则 + 0 WARN + 无硬编码深度上限）
6. debug 模式下 4 原则不变量检查全部通过

# 关键约束（重申）

- **禁止跨区域跨层次的启发式规则**
- **禁止破坏算法对嵌套的天然支持**
- **禁止后处理补丁**（必须识别阶段一次正确）
- **禁止硬编码深度上限**
- **禁止以「run_test_matrix 100%」为完成标志**（必须全测试集 100%）
- 每个修改后全测试集回归，不退化
- 每个失败用例必须算法根因修正，不是个别 case 修补
- 深度思考是否需要更多区域类型或更好的方法（不局限于现有 19 个 RegionType）
