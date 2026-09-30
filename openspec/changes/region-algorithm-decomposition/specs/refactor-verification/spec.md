## ADDED Requirements

### Requirement: 每步重构的 gate 准入与准出
roadmap 中每个重构步骤 SHALL 声明准入条件（改动前必须通过的基线 gate）与准出条件（改动后必须全过的 gate）。任何步骤 SHALL 包含"当前状态基线全绿"作为准入前提。

#### Scenario: 准入条件可执行
- **WHEN** 审阅 roadmap 中任一步骤
- **THEN** 该步骤列出的准入 gate 均为现存 round 级 gate 名称（G0 语法/一致性、G1 靶一致、G3 批量 402 支、G4 official 尺、G4′ 严格缺陷尺、G7 prev/landed 逐项重放）且可在 `scripts/` 找到执行入口

#### Scenario: 准出含不退步约束
- **WHEN** 某步骤完成
- **THEN** mandated 与 official 两把尺的分子分母均不得下降（WORSE=0），与 ADR-1「不得以少发射换成功数」一致

### Requirement: 每步限定触碰面与回滚方式
每个步骤 SHALL 声明允许修改的模块集合，超出集合的改动 SHALL 拆为新步骤；每个步骤 SHALL 有可执行的回滚方式（还原到 HEAD 字节或 revert 单次提交）。

#### Scenario: 触碰面越界
- **WHEN** 实现阶段需要修改步骤声明集合之外的文件
- **THEN** 该步骤停止推进，先修改 roadmap 增补步骤并重过准入

#### Scenario: 字节级回滚
- **WHEN** 需要回滚某步
- **THEN** 存在与 HEAD 字节对齐的还原方式（`git checkout` / 从 prev 基线镜像还原），且回滚后 G0 立即可验证通过

### Requirement: 路线不承诺"总行数下降"
阶段化搬移步骤 SHALL NOT 以"减少行数"作为收益承诺；收益 SHALL 以 god class 拆分与阶段可测性表述。

#### Scenario: 收益栏口径
- **WHEN** 审阅 roadmap 步骤收益栏
- **THEN** 搬移类步骤的收益写作复杂度/可测性指标，去重类步骤额外标注净减行数

### Requirement: 并行迭代协作规则
roadmap SHALL 声明与并行迭代代理的协作规则：同一文件被并行修改时以重新运行提取器为准，禁止人工改写文档数字或据过期行号直接搬移。

#### Scenario: 过期基线
- **WHEN** 执行某步时发现源码行号与文档锚点不符
- **THEN** 先重跑提取器刷新解剖表与行号锚点，再判断是否仍按原计划执行
