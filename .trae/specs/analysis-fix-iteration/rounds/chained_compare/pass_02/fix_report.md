# Pass 2 第 19 轮（CC 区域）修复报告

## 概述

本轮聚焦链式比较（Chained Compare, CC）区域的低风险文档/注释治理。
遵循「不改变控制流、不删除高风险结构」约束，仅做死代码/行号引用同步/
反模式标记三类保守修复。`_try_build_*` patch chain 与
`_detect_boolop_after_chained_compare` 按约束保留，留待 Pass 3+。

## 架构工程师分析

### 审阅范围

- `core/cfg/region_analyzer.py`
  - `_identify_chained_compare_regions`（Phase 2a CC 识别，L9718–9831）
  - `_identify_conditional_regions` 内 Phase 3 CC 相关代码：
    - CC extra_blocks 预扫描（L10177–10184）
    - `_detect_chained_compare_pattern` 重检测 + then/else 调整（L10444–10470）
    - 末尾 `region.chained_compare_blocks/ops` 字段回填（L10649–10651）
  - `_build_chained_compare_region`（L11356–11389，Phase 2a 字段设置路径）
- `core/cfg/region_ast_generator.py`
  - `_build_chained_compare_from_region_data`（L7114–7157）含 `_try_build_*` 三连
  - `CC_NOISE_OPS` 常量定义（L94–109）

### 识别的低风险问题（共 3 项）

#### 问题 1：TODO 注释行号引用过时（region_analyzer.py）

`_identify_conditional_regions` 内 L10172–10176 的 `TODO[pass2-CC]` 注释引用
「10429-10455 重检测、10634-10636 字段回填」。实际：
- 重检测位于 L10444（`chained_compare_info = self._detect_chained_compare_pattern(condition_block)`）至 L10470（`if _else_is_cleanup:` 块末），非 10429-10455。
- 字段回填位于 L10649–10651（`region.chained_compare_blocks = ...` / `chained_compare_ops = ...`），非 10634-10636。L10634-10636 实际是 await 前驱链注释，与字段回填无关。

行号引用随编辑漂移，已失准且会继续失准。

#### 问题 2：CC_NOISE_OPS 注释行号引用过时（region_ast_generator.py）

L94–96 注释引用 `_skip_ops` 四处行号「7186/7413/7511/8927」与
`_CMP_SKIP_OPS` 三处行号「6828/9798/16322」。实际位置已漂移至
7219/7443/7538/8951（_skip_ops）与 6861/9819/16338（_CMP_SKIP_OPS）。
全部 7 个行号均失准。

#### 问题 3：`_try_build_*` patch chain 缺反模式标记（region_ast_generator.py）

`_build_chained_compare_from_region_data`（L7118+）内 `_try_build_walrus_chained_compare`
→ `_try_build_literal_middle_chained_compare` → `_try_build_method_call_chained_compare`
三连为典型 patch chain 反模式：每个特例独立探测+重建，绕过统一的
`compute_chained_compare_operands` 路径。任务约束明确该 chain 为高风险，
本轮不删除，但应添加标记注释以便 Pass 3+ 定位。

### 已评估但未动手的高风险项（留待 Pass 3+）

- **统一 CC 操作数提取，删除 `_try_build_*` patch chain**：高风险，需保证
  walrus / literal-middle / method-call 三特例的栈模拟语义被统一路径覆盖。
- **删除 `_detect_boolop_after_chained_compare`**：中风险。
- **删除 Phase 3 CC 重检测与字段回填**：低风险但**前置依赖未满足**——TODO 明确
  需先放宽 Phase 2a 触发条件（去掉「恰 2 个 conditional_successors 且未占用」
  过严约束）让所有 CC 头块一次识别完毕，否则直接删除会改变控制流并丢识别。
  本轮按约束「不改变控制流」保留。

## 修复工程师实施

### Fix 1：同步 TODO 行号引用为描述性引用

**文件**：`core/cfg/region_analyzer.py`（L10172–10179）

将「10429-10455 重检测、10634-10636 字段回填」替换为以方法名 + 语义定位的
描述：「`_identify_conditional_regions` 中对 condition_block 的
`_detect_chained_compare_pattern` 重检测（紧随其后的 then/else 调整块）、以及
方法末尾对 `region.chained_compare_blocks`/`chained_compare_ops` 的字段回填」。
并补充说明「行号引用易随编辑漂移，故以方法名 + 语义定位」。

### Fix 2：同步 CC_NOISE_OPS 行号引用为函数名引用

**文件**：`core/cfg/region_ast_generator.py`（L94–101）

将 7 个失准行号替换为 enclosing 函数名：
- 4 处 `_skip_ops`：`_try_build_walrus_chained_compare` /
  `_try_build_method_call_chained_compare` /
  `_try_build_literal_middle_from_blocks` / `_try_build_await_condition`
- 3 处 `_CMP_SKIP_OPS`：`_build_chained_compare_with_ternary_middle` /
  `_build_compare_ternary_condition` / `_wrap_boolop_with_merge_compare`

（注：实施过程中发现初稿将第 3 处 `_CMP_SKIP_OPS` 误标为
`_precompute_chained_compare_analysis`——该函数实际位于 region_analyzer.py
而非 region_ast_generator.py。已核实 L16338 的 enclosing 函数为
`_wrap_boolop_with_merge_compare` 并修正。）

### Fix 3：`_try_build_*` patch chain 添加反模式标记

**文件**：`core/cfg/region_ast_generator.py`（L7121–7125）

在 `_build_chained_compare_from_region_data` 早期 return 之后、首个 `_try_build_*`
调用之前，插入 `TODO[pass2-CC]` 标记注释，说明：
- 该三连为 CC 操作数提取的 patch chain 反模式；
- 统一操作数提取以删除该 chain 为高风险重构，留待 Pass 3+；
- 本轮仅添加标记，不改控制流。

## 验证

- **编译验证**：`python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 退出码 0，输出「OK: both modules imported successfully」。
- **控制流不变**：3 项修复均为注释/文档同步，无代码逻辑变更。
- **约束合规**：未修改测试文件；未引入 `_fix_`/`_merge_`/`_patch_` 前缀；未引入硬编码深度上限；未删除 `_try_build_*` chain；未删除 `_detect_boolop_after_chained_compare`；未删除 Phase 3 重检测/字段回填（前置依赖未满足）。

## 影响文件

- `core/cfg/region_analyzer.py`（Fix 1，+3 行 / -2 行净 +1 行注释）
- `core/cfg/region_ast_generator.py`（Fix 2 + Fix 3，注释扩展）

## 后续建议（Pass 3+）

1. **放宽 Phase 2a CC 触发条件**：去掉「恰 2 个 conditional_successors 且未被占用」
   过严约束，让所有 CC 头块在 Phase 2a 一次识别完毕。前置完成后即可删除：
   - Phase 3 CC extra_blocks 预扫描
   - Phase 3 `_detect_chained_compare_pattern` 重检测 + then/else 调整
   - Phase 3 末尾字段回填
2. **统一 CC 操作数提取**：将 `_try_build_*` 三连的栈模拟语义收敛到
   `compute_chained_compare_operands` 统一路径，删除 patch chain。
3. **评估 `_detect_boolop_after_chained_compare` 的可消除性**。
