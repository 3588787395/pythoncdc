# quotation.pyc 双工程师反编译迭代 Spec

## Why

`/workspace/quotation.pyc` 是 pythoncdc 反编译器在真实业务场景下的代表性目标文件。当前反编译结果与原始字节码之间存在不一致，需要通过「测试工程师 + 修复工程师」的对抗性迭代，逐轮暴露并修复缺陷，最终达到 **100% 字节码完全匹配**。

与既有规范（`iterate-region-test-fix`/`region-decompile-perfection`/`analysis-fix-iteration`）的区别：
- 前述规范按区域类型组织迭代，本规范以**单一真实 pyc 文件**为闭环验证对象；
- 每轮必须由测试工程师从该文件反编译结果中**提取 10+ 可复现的最小实例**，再由修复工程师按区域归约算法修正；
- 每轮独立目录，禁止跨轮合并产物，禁止任何投机取巧。

## What Changes

- **新建 10 轮迭代目录**：`/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_NN/{test_engineer/, repair_engineer/}`
- **每轮测试工程师产物**：`decompile_report.md`（quotation.pyc 反编译 + 字节码一致性 diff）+ `minimal_repros/`（10+ 个最小复现 `.py`/`.pyc` 用例）
- **每轮修复工程师产物**：`fix_report.md`（修复点列表 + 区域归约算法依据 + 回归结果）
- **反编译逻辑注释同步**：修复涉及到的 `_identify_*_regions` 方法必须将完整反编译逻辑写入方法注释（统一模板）
- **算法合规性强制**：所有修复必须符合区域归约算法 4 原则，禁止跨区域启发式 / 后处理补丁 / 启发式优先级覆盖 / 展平嵌套
- 每轮 commit + push 到 `origin/main`，commit message 前缀 `qpyc-rNN:`

## Impact

- 影响规范：`/workspace/.trae/specs/quotation-pyc-iteration/`（新建）
- 影响代码：
  - `core/cfg/region_analyzer.py`（识别方法注释 + 逻辑修正）
  - `core/cfg/region_ast_generator.py`（AST 映射逻辑修正）
  - `core/cfg/ast_generator_v2.py` / `core/cfg/code_generator.py`（必要时）
- 影响测试：每轮新增 10+ 最小复现用例归档到 `rounds/round_NN/test_engineer/minimal_repros/`
- 不变更既有测试矩阵基线；quotation.pyc 的字节码一致性 = 0 不一致 为退出条件
- 命令执行：所有命令 ≤ 300s，单轮内 commit + push 必须 ≤ 300s

## ADDED Requirements

### Requirement: quotation.pyc 字节码 100% 等价反编译

系统 SHALL 能够反编译 `/workspace/quotation.pyc`，使得「原始字节码 ↔ 反编译后重新编译字节码」**完全等价**（0 不一致指令序列）。

#### Scenario: 反编译成功且字节码等价
- **WHEN** 执行 `python pycdc.py /workspace/quotation.pyc`
- **THEN** 产出 `.py` 源码，且该源码 `compile()` 后与原 `.pyc` 指令序列逐条匹配
- **AND** 0 处字节码不一致

#### Scenario: 每轮闭环
- **WHEN** 测试工程师反编译 quotation.pyc 并提取最小复现实例
- **THEN** 至少 10 个可独立复现的字节码不一致问题归档至 `minimal_repros/`
- **WHEN** 修复工程师按区域归约算法修复后
- **THEN** 该轮 10+ 复现实例全部通过；既有测试矩阵无退化；commit + push 完成

### Requirement: 反编译逻辑注释统一模板

所有 `_identify_*_regions` 方法 MUST 在 docstring 中包含以下统一结构：
1. **算法依据**：本区域识别所依据的「No More Gotos」算法章节 + 区域归约 4 原则对应条款
2. **归约顺序**：本区域在 CFG 归约序列中的位置（自底向上）
3. **唯一归属判定**：本区域如何保证每个块仅属于一个区域
4. **嵌套处理**：嵌套子区域如何作为单个抽象节点表示
5. **入口引用语义**：父区域的 then/else 列表如何引用本区域入口
6. **反编译流程**：从字节码模式到 AST 节点的完整映射步骤（禁止「补丁式」描述）

### Requirement: 算法合规性强制

所有代码变更 MUST 通过以下静态检查：
1. 无 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法（已知遗留 `_merge_block_is_loop_back_edge` 必须在本规范过程中重命名）
2. 无跨区域启发式（如 `_detect_boolop_after_chained_compare`）
3. 无后处理补丁（如对归约结果的事后修正）
4. 无硬编码深度上限（`depth < N` / `count < N` 等魔法数字）
5. 无展平嵌套（强制把嵌套区域拍平到外层）

## MODIFIED Requirements

### Requirement: 区域归约算法 4 原则持续 FULLY COMPLIANT

继承 `analysis-fix-iteration` 的 F3 验证项，本规范过程中：
1. **自底向上归约**：从最内层到最外层识别区域，每层归约后替换为抽象节点
2. **每块唯一归属**：任意 CFG 块在任何层级仅属于一个区域
3. **嵌套即抽象节点**：嵌套区域在父区域中作为单个抽象节点
4. **入口引用语义**：归约后父区域的 then/else 引用子区域入口，而非子区域所有块

任何修复不得违背上述任一原则。

## REMOVED Requirements

### Requirement: 跨区域启发式与后处理补丁
**Reason**：违反区域归约算法 4 原则，导致算法通用性下降、维护成本上升、新场景易退化
**Migration**：通过完善识别逻辑本身（如扩充入口条件、补充嵌套判定）替代补丁；已有补丁逐轮消除

## 双工程师工作流

### 测试工程师职责
1. 反编译 `/workspace/quotation.pyc`（`python pycdc.py /workspace/quotation.pyc`，≤300s）
2. 对比反编译产物与原 `.pyc` 字节码（`python -c "import dis; ..."` 或专用 diff 工具）
3. 定位每一处不一致的具体位置（函数名、指令偏移、字节码差异类型）
4. 针对每处不一致，构造**最小复现**实例（最小 `.py` 源码 → 编译 → 反编译 → 字节码 diff）
5. 归档 ≥10 个最小复现实例至 `rounds/round_NN/test_engineer/minimal_repros/repro_NN_*.py`
6. 输出 `decompile_report.md`：不一致清单 + 根因初判（涉及的区域类型 + 字节码模式）

### 修复工程师职责
1. 阅读测试工程师的 `decompile_report.md` 与 `minimal_repros/`
2. 对每个不一致，定位到 `_identify_*_regions` 或 `_generate_*` 方法
3. 按「No More Gotos」+ 区域归约算法完善逻辑（不得引入补丁）
4. 同步更新方法 docstring（统一模板）
5. 运行回归测试（既有测试矩阵不退化）
6. 验证该轮 10+ 复现实例全部通过
7. 输出 `fix_report.md`：修复点 + 算法依据 + 回归结果 + 残留不一致数
8. commit + push（前缀 `qpyc-rNN:`）

### 退出条件
- quotation.pyc 反编译字节码 0 不一致
- 且最近 1 轮测试工程师无可新增最小复现实例（< 10 个）

## 区域顺序提示

quotation.pyc 中可能涉及的区域类型（非强制顺序，由测试工程师按不一致热点选取）：
IF / LOOP / TRY / WITH / MATCH / TERNARY / BOOLOP / CHAINED_COMPARE / ASSERT / SEQUENCE / COMPREHENSION / DECORATOR / LAMBDA / CLASSDEF

## 命令预算

| 命令类别 | 上限 |
|---------|------|
| 单条命令执行 | 300s |
| 单轮内 commit + push | 300s |
| 单轮回归测试（既有矩阵子集）| 280s |
| 反编译 quotation.pyc | 60s |
| 字节码 diff | 60s |
