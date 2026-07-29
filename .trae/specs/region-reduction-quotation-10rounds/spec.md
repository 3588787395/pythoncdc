# 区域归约算法驱动的 quotation.pyc 反编译 10 轮迭代 Spec

## Why

现有 `quotation-pyc-iteration` 已迭代 19 轮，但走的是 `use_cfg=False` 路径（纯模式匹配），导致反编译逻辑散落在大量启发式补丁中，违反区域归约算法的 4 项核心原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）。

本次目标：以 "No More Gotos" (Launez et al., 2013) 论文的结构化算法为核心，由两位工程师协作 10 轮，把区域识别与反编译逻辑沉淀到 `core/cfg/region_analyzer.py` 的 11 个 `_identify_*_regions` 识别方法与对应 `_generate_*` 生成方法的 docstring 注释中，对 `quotation.pyc` 反编译产物逐轮提升字节码一致率，最终达到 100% 一致。

## What Changes

- 分析当前 11 个 `_identify_*_regions` 识别方法所覆盖的区域模式（Loop / TryExcept / With / Match / NestedMatch / Assert / ChainedCompare / Conditional / Ternary / BoolOp / Sequence），逐个规划反编译逻辑并以 6 节统一模板写入方法 docstring
- 由测试工程师对 `quotation.pyc` 反编译 + 字节码 diff，按不一致函数提取 ≥10 个最小复现实例
- 由修复工程师依据测试工程师分析结果，按区域归约算法 4 原则修复 `region_analyzer.py` / `region_ast_generator.py` / `ast_converter.py` / `code_generator.py` / `cfg_builder.py` 等相关方法，禁止跨区域跨层次启发式规则
- 每轮独立目录 `rounds/round_NN/{test_engineer,repair_engineer}/`，每轮 commit + push（commit 前缀 `rr-rNN:`）
- 持续 10 轮，每轮后统计一致函数数 / 成功率，要求成功率单调递增，直至 100% 字节码完全匹配
- **禁止修改反编译生成的产物文件**（`quotation_decompiled.py`、`/tmp/r*_decompiled.py` 等只读）
- **所有命令执行不得超过 300 秒**

## Impact

- Affected specs: `quotation-pyc-iteration`（沿用其 baseline 与测试基础设施，但走区域归约路径）、`analysis-fix-iteration`（区域测试矩阵作为回归基线）
- Affected code:
  - `core/cfg/region_analyzer.py` — 11 个 `_identify_*_regions` 方法 docstring + 识别逻辑
  - `core/cfg/region_ast_generator.py` — `_generate_*` 方法 + 入口引用语义
  - `core/cfg/ast_converter.py` — AST 节点映射
  - `core/cfg/code_generator.py` — 表达式 / 语句发射
  - `core/cfg/cfg_builder.py` — CFG 构建 / 跳转目标识别
  - `core/cfg/dominator_analyzer.py` — 回边 / 支配树
  - `core/cfg/pattern_parser.py` — match 模式提取
- 受约束的核心算法原则（贯穿所有方法）：
  1. **自底向上归约**：从最内层到最外层识别区域，归约后才在父区域出现
  2. **每块唯一归属**：每个块在任何层级只属于一个区域（`block_to_region` canonical owner）
  3. **嵌套即抽象节点**：嵌套区域在其父区域中作为单个抽象节点表示
  4. **入口引用语义**：归约后父区域的 then/else 列表引用子区域的 entry，而不是子区域的所有块

## ADDED Requirements

### Requirement: 区域识别方法 docstring 6 节统一模板

系统 SHALL 在所有 `_identify_*_regions` 与对应 `_generate_*` 方法 docstring 中按以下 6 节模板写明反编译逻辑：

1. **算法依据** — 引用 "No More Gotos" 算法条款 + Python 字节码特性映射
2. **归约顺序** — 该区域相对其它区域的识别顺序（自底向上）
3. **唯一归属判定** — 如何判定一个块属于本区域而非其它区域（含 `block_to_region` 守卫）
4. **嵌套处理** — 子区域如何作为单个抽象节点参与本区域识别
5. **入口引用语义** — 父区域如何引用本区域 entry（then/else 列表）
6. **反编译流程** — 本区域归约后如何映射为唯一 AST 节点类型

#### Scenario: docstring 已更新
- **WHEN** 修复工程师修改任一 `_identify_*_regions` 或 `_generate_*` 方法
- **THEN** 该方法 docstring 必须包含上述 6 节，且每节内容与代码逻辑一致
- **AND** `grep -c "算法依据\|归约顺序\|唯一归属判定\|嵌套处理\|入口引用语义\|反编译流程"` 在该方法 docstring 范围内 ≥ 6

### Requirement: 双工程师迭代流程

系统 SHALL 每轮由两位工程师协作完成：

#### Scenario: 测试工程师职责
- **WHEN** 进入轮 N
- **THEN** 测试工程师反编译 `/workspace/quotation.pyc`
- **AND** 与原始字节码做精确 diff，统计一致函数数 / 总函数数 / 成功率
- **AND** 从不一致函数中提取 ≥10 个最小复现实例到 `rounds/round_NN/test_engineer/minimal_repros/`
- **AND** 输出 `decompile_report.md`（含一致函数数、成功率、缺陷分类、repro 清单）

#### Scenario: 修复工程师职责
- **WHEN** 测试工程师完成 decompile_report.md
- **THEN** 修复工程师依据 repro 与 `decompile_report.md`
- **AND** 定位根因到 `_identify_*_regions` 或 `_generate_*` 方法
- **AND** 按区域归约算法 4 原则修复，禁止跨区域跨层次启发式规则
- **AND** 同步更新相关方法 docstring（6 节模板）
- **AND** 输出 `fix_report.md`（含修复点、算法依据、4 原则对应条款、回归结果、残留不一致数）

### Requirement: 成功率单调递增

系统 SHALL 保证每轮反编译一致函数数不退化。

#### Scenario: 成功率提升
- **WHEN** 轮 N 修复完成并回归后
- **THEN** 轮 N 的 quotation.pyc 一致函数数 ≥ 轮 N-1 的一致函数数
- **AND** 成功率（一致函数数 / 总函数数）单调递增
- **AND** 若某轮出现退化，修复工程师必须先回退退化再推进新修复

### Requirement: 每轮 commit + push

系统 SHALL 每轮独立 commit 并 push 到远程。

#### Scenario: 提交并推送
- **WHEN** 轮 N 的 fix_report.md 与回归测试完成
- **THEN** 使用 commit 前缀 `rr-rNN:` 提交（NN 为 01..10）
- **AND** push 到 `origin/main`（远程 `https://github.com/3588787395/pythoncdc`）
- **AND** 使用提供的 GitHub token 完成鉴权
- **AND** 单次命令执行 ≤ 300 秒

### Requirement: 反模式零新增

系统 SHALL 禁止在修复中引入反模式。

#### Scenario: 反模式自检
- **WHEN** 修复工程师提交代码
- **THEN** `core/cfg/` 下无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法
- **AND** 无新增硬编码深度上限
- **AND** 禁止跨区域跨层次启发式规则（违反 4 原则）

## MODIFIED Requirements

### Requirement: 区域归约算法合规性

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

### Requirement: 所有区域类型同等完善（Round 8 强化）

系统 SHALL 对全部 11 类区域（Loop / TryExcept / With / Match / NestedMatch / Assert / ChainedCompare / Conditional / Ternary / BoolOp / Sequence）的 `_identify_*_regions` 识别方法与对应 `_generate_*` 生成方法**同等**完成算法逻辑沉淀，禁止仅完善"当前出错"的区域类型。

#### Scenario: 全区域 docstring 覆盖
- **WHEN** Round 8 完成
- **THEN** 全部 11 类区域的 `_identify_*_regions` / `_generate_*` 方法 docstring 均已按 6 节统一模板填写（算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程）
- **AND** 每节内容与该方法代码逻辑**一致**（注释即文档，注释即算法规约）
- **AND** `grep -cE "算法依据|归约顺序|唯一归属判定|嵌套处理|入口引用语义|反编译流程"` 在每个目标方法 docstring 范围内 ≥ 6

#### Scenario: 反编译逻辑写入识别方法注释
- **WHEN** 修复工程师分析任一区域模式
- **THEN** 该区域的反编译逻辑（CFG 模式 → 区域分类 → 归约 → AST 映射的完整推理链）MUST 写入对应 `_identify_*_regions` / `_generate_*` 方法的 docstring 注释
- **AND** 注释中明确标注该区域相对其它区域的归约顺序（自底向上层级）
- **AND** 注释中明确标注本区域的唯一归属判定（含 `block_to_region` canonical owner 守卫）

#### Scenario: 算法驱动而非出错驱动
- **WHEN** 修复工程师完善某区域类型
- **THEN** 完善依据是区域归约算法对该区域类型的规约，而非"该区域当前是否在 quotation.pyc 中出错"
- **AND** 即使某区域类型在 quotation.pyc 中当前无错误，也 MUST 按 6 节模板完成 docstring 与逻辑审查

## REMOVED Requirements

无移除项。沿用 `quotation-pyc-iteration` 的 baseline 与测试基础设施，但不复用其 `use_cfg=False` 路径的修复历史。
