# 区域归约算法精炼 Spec

## Why

`region-decompile-perfection` 已完成，达到 99.95% 通过率（2067/2068），但算法符合度审计为 PARTIALLY COMPLIANT（2 个 WARN），且 `region_analyzer.py` 中存在 50+ 处 `isinstance.*Region` 分支判断、2 处 `depth > 3` 硬编码嵌套上限、以及 2 处违反「一次正确」原则的工程补丁。本次变更在保持 99.95% 基线的前提下，精炼算法使其完全符合区域归约算法四原则，并支持无限嵌套。

## What Changes

* **提交并推送当前仓库更新**（删除 11 个 fix-\* spec 目录、修改 7 个核心文件、归档调试产物）

* **移除硬编码嵌套深度上限** `_is_with_exit_leading_to_break/continue` 中的 `depth > 3`（region\_analyzer.py L3404, L3454），改用 `visited` 集合终止递归

* **消除 WARN-1**：`_identify_try_except_regions` 中基于异常表 `depth` 字段的跨区域特例判断（L3689-3700），改为基于异常表结构的算法判定

* **消除 WARN-2**：`_merge_consecutive_with_regions` 后处理补丁（L5986-6005），将合并逻辑前移至 `_identify_with_regions` 识别阶段

* **减少 isinstance 分支**：将 50+ 处 `isinstance(region, XxxRegion)` 类型分发替换为多态方法或分派表，目标降至 < 20 处

* **保持 99.95% 基线**：所有改动后 `run_test_matrix.py` 全量通过率 ≥ 99.95%（2067/2068），`match_region` 独立测试 198/198（2 skipped）

* **支持无限嵌套**：移除所有硬编码深度上限，依赖 `visited` 集合与归约算法的天然终止性

## Impact

* Affected specs: `region-decompile-perfection`（已完成，作为基线参考，不再修改）

* Affected code:

  * `core/cfg/region_analyzer.py`（\~13000 行）— 主要改动文件：移除 depth>3、消除 2 个 WARN、减少 isinstance 分支

  * `core/cfg/region_ast_generator.py`（\~15500 行）— 次要改动：配合识别阶段前移的 with 合并逻辑

  * `tests/exhaustive/run_test_matrix.py` — 仅验证用，不改动

* 算法符合度：PARTIALLY COMPLIANT → FULLY COMPLIANT（0 WARN）

* 风险：改动触及核心识别逻辑，需在每步后回归测试

## ADDED Requirements

### Requirement: 无限嵌套支持

系统 SHALL 支持任意深度的嵌套区域识别与归约，不依赖任何硬编码的深度常量。

#### Scenario: 深层嵌套的 with-break 识别

* **WHEN** 反编译包含 5 层以上嵌套的 `with` 语句且内层含 `break`

* **THEN** `_is_with_exit_leading_to_break` 正确识别所有层级的 break 语义，不因 `depth > 3` 提前终止

#### Scenario: 深层嵌套的 with-continue 识别

* **WHEN** 反编译包含 5 层以上嵌套的 `with` 语句且内层含 `continue`

* **THEN** `_is_with_exit_leading_to_continue` 正确识别所有层级的 continue 语义

### Requirement: 算法完全符合度

系统 SHALL 在所有 `_identify_*_regions` 与 `_generate_*` 方法中完全符合区域归约算法四原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义），无跨区域特例、无后处理补丁、无启发式优先级覆盖、无破坏嵌套的扁平化。

#### Scenario: try\_except 识别无跨区域特例

* **WHEN** `_identify_try_except_regions` 处理嵌套异常表

* **THEN** 嵌套关系判定基于异常表结构（start/end/target 区间包含关系），不依赖 `depth` 字段的数值比较特例

#### Scenario: with 识别无后处理补丁

* **WHEN** 连续多个 `with` 语句被识别

* **THEN** 合并在 `_identify_with_regions` 识别阶段完成，`_merge_consecutive_with_regions` 不再作为后处理调用

### Requirement: 分支复杂度降低

系统 SHALL 通过多态分派或分派表减少 `isinstance.*Region` 类型判断分支，使 `region_analyzer.py` 中的 `isinstance.*Region` 出现次数 < 20。

#### Scenario: 类型分派使用多态

* **WHEN** `process_regions` 或其他方法需要按区域类型执行不同逻辑

* **THEN** 优先调用区域对象的多态方法（如 `region.merge_into_parent()`）或通过分派表查找，而非 `isinstance` 链

## MODIFIED Requirements

### Requirement: 区域识别算法

区域识别遵循自底向上归约顺序，每个块在任意层级只属于一个区域，嵌套区域在父区域中作为单个抽象节点表示，父区域引用子区域入口块。识别阶段一次正确，不依赖后处理修正。所有方法不包含硬编码深度上限。

## REMOVED Requirements

### Requirement: 硬编码嵌套深度上限

**Reason**: `_is_with_exit_leading_to_break` (L3404) 与 `_is_with_exit_leading_to_continue` (L3454) 中的 `depth > 3` 上限违反「支持无限嵌套」原则，且为启发式安全阀，非算法性终止条件。
**Migration**: 改用 `visited: Set[int]` 集合记录已访问块，依赖 CFG 的有限性与归约算法的终止性保证递归终止。

### Requirement: try\_except handler depth 跨区域特例

**Reason**: L3689-3700 基于 `depth` 字段数值比较的特例判断属于跨区域启发式规则，违反「禁止跨区域跨层次启发式规则」约束。
**Migration**: 改为基于异常表 `(start, end, target)` 区间的结构包含关系判定嵌套层级。

### Requirement: \_merge\_consecutive\_with\_regions 后处理补丁

**Reason**: L5986-6005 在 `analyze()` 末尾作为后处理调用，违反「一次正确」原则。
**Migration**: 将连续 with 合并逻辑前移至 `_identify_with_regions` 识别阶段，识别时即合并相邻 WithRegion。
