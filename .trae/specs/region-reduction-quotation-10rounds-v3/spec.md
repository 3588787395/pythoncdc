# 区域归约算法驱动的 quotation.pyc 反编译 10 轮迭代 V3 Spec

## Why

V2（R11-R20）10 轮迭代已完成，一致函数数从 143/150 (95.33%) 提升至 **147/150 (98.00%)**，但仍残留 3 个不一致函数，未达 100% 字节码一致目标。V2 已确认这 3 个函数均涉及区域识别层/生成层深层结构性改动，R12/R13/R18/R19 的局部修复尝试因暴露并放大深层缺陷导致退化（按"0 退化"硬约束已回退）。

本次目标：以区域归约算法（No More Gotos）继续驱动 10 轮双工程师迭代（R21-R30），**优先攻克深层结构性缺陷**而非局部补丁，最终达到 100% 字节码一致。

## 残留不一致函数清单（V2 输出，V3 输入，3 个）

### P0 — get_str_data（len_diff -48，317→269，Loop 区域语句丢失）

**类型**: dict 构造消费模式未建模（区域识别层功能扩展）

**三层根因**:

| 根因层 | 描述 | V2 处置 |
|--------|------|--------|
| A | `BUILD_CONST_KEY_MAP`+`STORE_SUBSCR` dict 构造消费模式未完整建模。TernaryRegion@1226 被误赋 `value_target='i'` | R18 **部分修复**（`value_target=None`，`container_type='dict'`，7 键完整捕获）；消费模式整体归约未建模 |
| B | `_process_if_blocks` 仅从 region.children 收集表达式子区域，遗漏 IfRegion@614 else_blocks 中的兄弟 TernaryRegion@844/@1226 | R19 修复因暴露 A 导致 -48→-84 退化，回退 |
| C | TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry 链式共享，前驱独占标记 merge_block 为 generated，后继三元 entry 被跳过 | R19 修复因暴露 A 导致 -48→-84 退化，回退 |

**V3 修复顺序**: 先建模 A 消费模式 → 边界对齐 → 再应用 B/C（R12/R19 教训：B/C 必须在 A 之后）

### P1 — get_date_and_count（len_diff -27，714→687，Loop+Conditional while 循环 if/elif 链丢失）

**类型**: Loop 反向链吸收外层条件块 + loop_else 误识别

**双层根因**:

| 根因层 | 描述 | V2 处置 |
|--------|------|--------|
| A | `_identify_loop_regions` 反向链走 fall-through 吸收外层 if/elif/else 条件块 | R13 修复因 -27→-63 退化，回退 |
| B | `_find_loop_else` 在 while 无 break 时误识别 else_blocks，循环后语句被错误归入循环 else | R13 修复因 -27→-63 退化，回退 |

**V3 修复顺序**: 先解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion → 再修复 A 反向链 fall-through 校验 → 最后修复 B loop_else 无 break 守卫（R13 教训：A/B 必须在穿透缺陷解决之后）

### P2 — change_his_to_backward（instr_diff@296，len 578=578，指令重排）

**类型**: code_generator if/else 分支布局未对齐（生成层重构）

**根因**: code_generator 的 if/else 分支布局与原始字节码不一致，@idx296 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标 orig=330 vs new=342，@idx329 起指令完全重排（不同 opcodes/结构）。这是**真实的指令重排**，非语义等价跳转目标偏移，V2 R20 确认不可在 exact_match_stats.py 安全归一化。

**V3 修复**: 在 `core/cfg/code_generator.py` 对齐 if/else 跳转目标布局，使分支生成顺序与原始字节码一致。属生成层重构，影响面广，需配套最小复现实例回归。

## What Changes

- 继承 V2 的双工程师迭代流程（测试工程师 → 修复工程师 → 回归 → commit + push）
- **优先攻克深层结构性缺陷**（建模新区域消费模式 / 解决跨区域块收集穿透 / 生成层布局对齐），而非局部补丁
- 重点分析 `_identify_ternary_regions` 对 `BUILD_CONST_KEY_MAP`+`STORE_SUBSCR` 消费模式的归约建模
- 重点分析 `_identify_loop_regions` 反向链 fall-through 校验 + `_find_loop_else` 无 break 守卫
- 重点分析 IfRegion else-branch 块收集对嵌套 LoopRegion 的穿透缺陷
- 重点分析 `code_generator.py` if/else 分支布局对齐
- 每轮独立目录 `rounds/round_NN/{test_engineer,repair_engineer}/`（NN=21..30），每轮 commit + push（commit 前缀 `rr-rNN:`）
- 持续 10 轮，每轮后统计一致函数数 / 成功率，**要求成功率单调递增且尽快增加**，直至 100% 字节码完全匹配
- **禁止修改反编译生成的产物文件**（`quotation_decompiled.py`、`/tmp/r*_decompiled.py` 等只读）
- **所有命令执行不得超过 300 秒**

## Impact

- Affected specs:
  - `region-reduction-quotation-10rounds`（V1，沿用其 baseline、测试基础设施）
  - `region-reduction-quotation-10rounds-v2`（V2，沿用其 `final_residual_v2.md` 残留清单、`exact_match_stats.py` 归一化增强、`<module>` 传递性委托）
  - `quotation-pyc-iteration`（沿用 baseline 与测试基础设施）
  - `analysis-fix-iteration`（区域测试矩阵作为回归基线）
- Affected code:
  - `core/cfg/region_analyzer.py` — `_identify_ternary_regions`（BUILD_CONST_KEY_MAP 消费模式建模）/ `_identify_loop_regions`（反向链 fall-through 校验）/ `_find_loop_else`（无 break 守卫）/ 区域边界对齐
  - `core/cfg/region_ast_generator.py` — `_process_if_blocks`（兄弟表达式子区域收集 + 链式共享 merge_block discard）/ `_generate_loop` / IfRegion else-branch 块收集穿透嵌套 LoopRegion
  - `core/cfg/code_generator.py` — if/else 分支布局对齐 / 跳转目标布局
  - `core/cfg/cfg_builder.py` — CFG 构建 / 跳转目标识别（如需）
  - `.trae/specs/region-reduction-quotation-10rounds-v2/rounds/round_NN/test_engineer/exact_match_stats.py` — 复用并按需增强归一化（仅在确认语义等价时）
- 受约束的核心算法原则（贯穿所有方法，继承 V1/V2）：
  1. **自底向上归约**：从最内层到最外层识别区域，归约后才在父区域出现
  2. **每块唯一归属**：每个块在任何层级只属于一个区域（`block_to_region` canonical owner）
  3. **嵌套即抽象节点**：嵌套区域在其父区域中作为单个抽象节点表示
  4. **入口引用语义**：归约后父区域的 then/else 列表引用子区域的 entry，而不是子区域的所有块

## ADDED Requirements

### Requirement: get_str_data 完全一致（P0，BUILD_CONST_KEY_MAP 消费模式建模）

系统 SHALL 通过建模 `BUILD_CONST_KEY_MAP`+`STORE_SUBSCR` dict 构造消费模式修复 `get_str_data`。

#### Scenario: 消费模式归约建模
- **WHEN** `_identify_ternary_regions`（region_analyzer.py）识别到三元/载入表达式的 merge_block 直接进入 `BUILD_CONST_KEY_MAP n` + `STORE_SUBSCR`
- **THEN** 这些值表达式 SHALL 作为整体 dict 构造语句归约，而非独立 TernaryRegion/bare expr
- **AND** 归约依据区域归约算法 4 原则（每块唯一归属 + 入口引用语义）
- **AND** 同步更新 `_identify_ternary_regions` docstring（6 节模板）

#### Scenario: 三层根因顺序修复
- **WHEN** 修复 get_str_data
- **THEN** 修复顺序 SHALL 为：A 消费模式建模 → 边界对齐（entry 不含前驱载入块）→ B 兄弟表达式子区域收集 → C 链式共享 merge_block discard
- **AND** 禁止跳过 A 直接修复 B/C（R12/R19 教训：会暴露 A 导致 -48→-84 退化）

#### Scenario: 字节码完全一致
- **WHEN** V3 任一轮修复完成
- **THEN** `get_str_data` 字节码 diff = 0（一致）
- **AND** 一致函数数 147→148

### Requirement: get_date_and_count 完全一致（P1，Loop 反向链 + loop_else）

系统 SHALL 通过解决 IfRegion else-branch 穿透 + Loop 反向链校验 + loop_else 无 break 守卫修复 `get_date_and_count`。

#### Scenario: IfRegion else-branch 穿透修复
- **WHEN** `_process_if_blocks`（region_ast_generator.py）收集 IfRegion else-branch 块
- **THEN** SHALL 不穿透嵌套 LoopRegion 吸收循环后语句
- **AND** 守卫：若块 parent 是嵌套 LoopRegion，交由嵌套 LoopRegion 统一生成

#### Scenario: Loop 反向链 fall-through 校验
- **WHEN** `_identify_loop_regions`（region_analyzer.py）走反向链
- **THEN** SHALL 校验 fall-through 不吸收外层 IfRegion else-branch 块
- **AND** 同步更新 `_identify_loop_regions` docstring（6 节模板）

#### Scenario: loop_else 无 break 守卫
- **WHEN** `_find_loop_else`（region_analyzer.py）识别 else_blocks
- **THEN** while 无 break 时 SHALL 不识别 else_blocks
- **AND** 同步更新 `_find_loop_else` docstring（6 节模板）

#### Scenario: 双层根因顺序修复
- **WHEN** 修复 get_date_and_count
- **THEN** 修复顺序 SHALL 为：穿透缺陷 → A 反向链校验 → B loop_else 守卫
- **AND** 禁止在穿透缺陷未解决时直接修复 A/B（R13 教训：会暴露穿透缺陷导致 -27→-63 退化）

#### Scenario: 字节码完全一致
- **WHEN** V3 任一轮修复完成
- **THEN** `get_date_and_count` 字节码 diff = 0（一致）
- **AND** 一致函数数 147→148 或与 P0 叠加达 149

### Requirement: change_his_to_backward 完全一致（P2，code_generator 布局对齐）

系统 SHALL 通过 `code_generator.py` if/else 分支布局对齐修复 `change_his_to_backward`。

#### Scenario: if/else 分支布局对齐
- **WHEN** `code_generator.py` 生成 if/else 分支
- **THEN** 分支生成顺序 SHALL 与原始字节码一致
- **AND** 跳转目标布局对齐，消除 @idx296 起的真实指令重排
- **AND** 属生成层重构，需配套最小复现实例回归避免引入退化

#### Scenario: 字节码完全一致
- **WHEN** V3 任一轮修复完成
- **THEN** `change_his_to_backward` 字节码 diff = 0（一致）
- **AND** 一致函数数 147→148 或与 P0/P1 叠加达 150

### Requirement: 双工程师迭代流程（继承 V1/V2）

系统 SHALL 每轮由两位工程师协作完成：

#### Scenario: 测试工程师职责
- **WHEN** 进入轮 N（N=21..30）
- **THEN** 测试工程师反编译 `/workspace/quotation.pyc`
- **AND** 与原始字节码做精确 diff，统计一致函数数 / 总函数数 / 成功率
- **AND** 从不一致函数中提取 ≥10 个最小复现实例到 `rounds/round_NN/test_engineer/minimal_repros/`（若残留 < 10 个不一致函数，记录为已达成退出条件 E2）
- **AND** 输出 `decompile_report.md`（含一致函数数、成功率、缺陷分类、repro 清单）

#### Scenario: 修复工程师职责
- **WHEN** 测试工程师完成 decompile_report.md
- **THEN** 修复工程师依据 repro 与 `decompile_report.md`
- **AND** 定位根因到 `_identify_*_regions` 或 `_generate_*` 方法
- **AND** 按区域归约算法 4 原则修复，禁止跨区域跨层次启发式规则
- **AND** 同步更新相关方法 docstring（6 节模板）
- **AND** 输出 `fix_report.md`（含修复点、算法依据、4 原则对应条款、回归结果、残留不一致数）

### Requirement: 成功率单调递增且尽快增加（继承 V1/V2，强化）

系统 SHALL 保证每轮反编译一致函数数不退化，并尽快增加。

#### Scenario: 成功率提升
- **WHEN** 轮 N 修复完成并回归后
- **THEN** 轮 N 的 quotation.pyc 一致函数数 ≥ 轮 N-1 的一致函数数
- **AND** 若某轮出现退化，修复工程师必须先回退退化再推进新修复
- **AND** 修复优先级 SHALL 按 P0 → P1 → P2 排序（预期收益最大 + 风险递增）

### Requirement: 每轮 commit + push（继承 V1/V2）

系统 SHALL 每轮独立 commit 并 push 到远程。

#### Scenario: 提交并推送
- **WHEN** 轮 N 的 fix_report.md 与回归测试完成
- **THEN** 使用 commit 前缀 `rr-rNN:` 提交（NN 为 21..30）
- **AND** push 到 `origin/main`（远程 `https://github.com/3588787395/pythoncdc`）
- **AND** 使用提供的 GitHub token 完成鉴权
- **AND** 单次命令执行 ≤ 300 秒

### Requirement: 反模式零新增（继承 V1/V2）

系统 SHALL 禁止在修复中引入反模式。

#### Scenario: 反模式自检
- **WHEN** 修复工程师提交代码
- **THEN** `core/cfg/` 下无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法
- **AND** 无新增硬编码深度上限
- **AND** 禁止跨区域跨层次启发式规则（违反 4 原则）

## MODIFIED Requirements

### Requirement: 区域归约算法合规性（继承 V1/V2）

修复工程师所有改动 MUST 符合区域归约算法 4 原则：

1. **自底向上归约**：`_build_region_hierarchy` 在所有区域识别完成后统一构建层级，识别阶段不跨层引用
2. **每块唯一归属**：`block_to_region` 为 canonical owner，`_ni_is_peer` 守卫不把共享 entry 的子区域误判为祖先
3. **嵌套即抽象节点**：嵌套区域（如 TryExcept 在 IfRegion else 分支）作为单个抽象节点
4. **入口引用语义**：父区域 then/else 列表引用子区域 entry，不展开子区域所有块

**禁止**：
- 跨区域跨层次的启发式规则
- 破坏算法对嵌套的天然支持
- 用模式匹配替代算法
- 后处理修正（一次正确原则）

### Requirement: 所有区域同样完善（用户强调）

系统 SHALL 对所有区域同样完善，所有识别/生成方法 MUST 符合区域归约算法 4 原则。

#### Scenario: 区域方法统一合规
- **WHEN** V3 任一轮修改 `_identify_*_regions` 或 `_generate_*` 方法
- **THEN** 该方法 docstring SHALL 按 6 节模板更新
- **AND** 修复 SHALL 不引入跨区域跨层次启发式规则
- **AND** 11 类识别方法 docstring 维持 6 节统一模板（11/11）

## REMOVED Requirements

无移除项。沿用 V1 (`region-reduction-quotation-10rounds`) 与 V2 (`region-reduction-quotation-10rounds-v2`) 的 baseline、测试基础设施、`final_residual_v2.md` 残留清单、`exact_match_stats.py` 归一化增强、`<module>` 传递性委托，以及已补全的 11 类 `_identify_*_regions` 识别方法 docstring（6 节模板，11/11）。
