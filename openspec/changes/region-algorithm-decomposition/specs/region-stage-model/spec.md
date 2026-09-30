## ADDED Requirements

### Requirement: 区域归约七阶段模型
区域归约算法 SHALL 建模为七个阶段：`CFG 构建 → 块语义标注 → 区域识别 → 区域层级装配 → 结构化语句生成 → 表达式重建 → 后处理`。每个阶段 SHALL 声明其输入数据结构与输出数据结构，且相邻阶段之间 SHALL 只通过这些显式数据结构传递（不得跨阶段直接读写对方内部状态）。

#### Scenario: 阶段输入输出可核对
- **WHEN** 审阅 `docs/refactor/region-anatomy.md` 的阶段定义
- **THEN** 七个阶段各自列出了具体输入类型（如 `BasicBlock`/`BlockSemantics`/`Region` 子类/区域树/语句 AST/表达式树）与输出类型，且无两个阶段共享同一对输入输出

#### Scenario: 构造与消费被区分对待
- **WHEN** 某方法体仅**读取** `LoopRegion`（如生成 while 语句）而另一方法**构造** `LoopRegion`（如识别循环）
- **THEN** 前者归生成侧（S5 系）、后者归识别侧（S3），且两者的 token 证据分别记录 `use:LoopRegion` 与 `new:LoopRegion`

#### Scenario: 名族先验与 token 冲突
- **WHEN** 方法名族指向 S5 但 token 证据（构造/消费模式）指向 S3
- **THEN** 归类以 token 证据为准，且该方法出现在"冲突项"清单中等待人工确认

### Requirement: 全部方法唯一归类
`RegionAnalyzer` 与 `RegionASTGenerator` 的全部方法（基线 212 + 248 = 460）SHALL 归入且仅归入一个阶段；无法归类者 SHALL 进入 `Unclassified` 桶并在文档中显式列出数量。

#### Scenario: 覆盖完整性
- **WHEN** 对照工具输出核对方法计数
- **THEN** 各阶段方法数之和 + `Unclassified` 数 = 460，且无方法在两个阶段中重复出现

#### Scenario: Unclassified 超标
- **WHEN** `Unclassified` 占比 > 15%
- **THEN** 判定阶段模型有误，须回到 design D1 修订阶段划分后重跑归属表，不得带着超标桶进入路线定稿

### Requirement: 阶段表随代码可刷新
方法归属表与阶段行数占比 SHALL 由 `tools/anatomy/extract_stages.py` 从当前源码 AST 生成，文档 SHALL 标注生成时刻；源码变化后重跑工具即可刷新，禁止人工编辑文档中的数字。

#### Scenario: 源码变更后刷新
- **WHEN** `core/cfg/region_analyzer.py` 被新增或删除方法后重跑提取器
- **THEN** 工具输出的方法计数与 `Unclassified` 数量同步变化，文档中标注的生成时刻需同步更新

### Requirement: 外提成本可评估
每个方法 SHALL 标注其 `self` 依赖面（读取与写入的实例字段数），以便对"从 god class 外提为模块级纯函数"的成本排序。

#### Scenario: 阶段排序依据
- **WHEN** roadmap 对阶段 1..N 排序
- **THEN** 排序依据包含 `self` 读写字段数与阶段行数占比，而非仅按方法数量
