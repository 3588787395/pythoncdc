## ADDED Requirements

### Requirement: 重复判定必须带三件套证据
白名单内任意两个可比文件对的重复关系 SHALL 以「同名函数数 / 同体函数数 / 函数体 AST 哈希」三件套呈现；仅以行数量级或命名相似推断的重复 SHALL NOT 被记为重复。

#### Scenario: ast_builder 对的证据
- **WHEN** 审阅 `docs/refactor/dup-matrix.md` 中 `parsers/ast_builder.py` 与 `parsers/ast_builder_cleaned.py` 一行
- **THEN** 该行列出同名 253、同体 221，并附函数体 AST 哈希样本

#### Scenario: 不同构文件对的否定结论
- **WHEN** 审阅 `core/cfg/code_generator.py` 与 `parsers/code_generator.py`、`core/control_flow.py` 与 `core/cfg/cfg_builder.py`、`core/fast_stack.py` 与 `utils/stack.py`
- **THEN** 各行结论为「不同构，保留」并写明理由（同名数 ≤ 9 且同体 0）

### Requirement: 处置结论三选一且带净减行数
每个文件对 SHALL 给出「合并 / 删除 / 保留」三类之一的处置结论；对「合并」「删除」 SHALL 折算净减行数，对「保留」 SHALL 说明保留理由。

#### Scenario: 差异函数逐个判定
- **WHEN** 存在同名但函数体不同的函数（ast_builder 对的 32 个差异函数）
- **THEN** 每个差异函数都有"保留哪一侧 + 理由"的记录，不得整体判定

#### Scenario: 净减行数与复杂度收益分列
- **WHEN** 文档给出收益数字
- **THEN** 「净减行数」与「复杂度收益（god class 拆分数 / 最大类行数）」分列两栏，阶段化搬移 SHALL NOT 计入净减行数

### Requirement: 重复证据可复现
重复矩阵 SHALL 可由 `tools/anatomy/extract_stages.py` 复现；矩阵中的每条数字 SHALL 能在工具输出中找到同名字段。

#### Scenario: 复现校验
- **WHEN** 在干净检出上运行提取器并对照 `dup-matrix.md`
- **THEN** 同名数、同体数、AST 哈希样本逐项一致
