# 区域归约反编译器：剩余 43 个 pyc 攻坚（10 轮迭代）Spec

## Why

`site-packages` 下 402 个 pyc 已建立索引（`pyc_index.json`），其中 **359 个已达 100% 字节码一致**，
仍有 **43 个为 partial**：这 43 个文件共 1252 个函数，仅 1122 个匹配，**缺口 130 个函数**。
目标是按区域归约算法（Region Reduction，源自 "No More Gotos" Launez et al., 2013）逐轮攻坚，
把这 43 个全部提升到 100%，并把每个结构的反编译逻辑**固化进识别方法的注释**中。

## What Changes

- 逐轮迭代：每轮「测试工程师分析 1 个 pyc → 产出 10+ 最小复现实例 → 修复工程师按区域归约算法完善代码」。
- 完善 `core/cfg/region_analyzer.py` 与 `core/cfg/region_ast_generator.py` 中的区域识别逻辑。
- 每个区域识别方法必须在其 docstring/注释中写明：区域类型、识别条件（基于支配树/回边/归约层级）、
  对应 AST 映射、以及已知边界情形。
- 每轮产出独立目录 `rounds/round_NN/`，内含复现实例、diff 报告、修复说明。
- 每轮结束前：`quotation.pyc` 验证 → `scripts/pyc_batch_verify.py` 批量回归 → git commit + push。

## Impact

- Affected code:
  - `core/cfg/region_analyzer.py`（1.5MB，区域识别）
  - `core/cfg/region_ast_generator.py`（2.8MB，区域→AST）
  - `core/cfg/dominator_analyzer.py`（支配树/回边检测）
  - `scripts/pyc_batch_verify.py`（验证入口，只读/回写索引）
- Affected specs: 区域化分析、单向数据流、一次正确、算法驱动。
- 禁止修改反编译生成的 `*OK.py` 文件（它们是产物，不是源码）。

## ADDED Requirements

### Requirement: 区域识别方法必须自带反编译逻辑注释
每个区域识别方法（Region 识别入口）的注释 SHALL 包含：
1. 区域类型与 CFG 形态（块集合 / 入口 / 出口）
2. 识别判据（基于支配关系、回边、块的前驱后继属性）
3. 归约后如何作为抽象节点参与父区域
4. 对应生成的 AST 节点类型

#### Scenario: 审查者阅读识别方法
- **WHEN** 打开任一 `_recognize_*_region` / `_is_*_region` 方法
- **THEN** 无需阅读实现体即可理解该区域的识别逻辑与 AST 映射

### Requirement: 每轮迭代闭环
系统 SHALL 支持：单 pyc 分析 → 最小复现 → 算法修复 → quotation 验证 → 批量回归 → 提交。

#### Scenario: 一轮迭代
- **WHEN** 一轮结束
- **THEN** 至少 1 个 pyc 由 partial 转为 ok，且已 ok 的 pyc 不回退，且远程有对应 commit

## MODIFIED Requirements

### Requirement: 区域归约顺序
- **OLD**: 允许在父区域识别后对子区域做后处理修正。
- **NEW**: 严格自内向外归约；每个块在任何层级只属于一个区域；
  嵌套区域在父区域中作为单个抽象节点出现；父区域的 then/else 列表引用子区域入口而非其全部块。
- **Reason**: 后处理修正会破坏嵌套的天然支持，导致深层嵌套结构字节码不一致。
- **Migration**: 新增识别能力时必须在内层区域识别阶段完成，禁止在外层做跨层打补丁。

## REMOVED Requirements

### Requirement: 跨区域跨层次的启发式规则
**Reason**: 违反「算法驱动、用数学性质替代启发式规则」的核心原则，是回归的主要来源。
**Migration**: 以支配树/回边/区间分析的结构性质替代；确需保留的补丁必须标注作用层级并附复现实例。
