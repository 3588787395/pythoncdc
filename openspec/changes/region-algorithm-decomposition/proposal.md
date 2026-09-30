# 区域归约算法阶段化解剖与去重路线

## Why

30+ 轮 region 迭代（`.trae/specs/` 27 个 spec 目录、round74 进行中）把 mandated 通过率推到 6,540/6,617 = 98.84%、official 尺 5,717/5,746 = 99.50%，但**每一次修补都落在同一批巨型函数体里**，边际收益递减、回归成本上升。实测结构事实：

| 事实 | 实测值 | 含义 |
|---|---|---|
| `core/cfg/region_analyzer.py` | 28,337 行；`RegionAnalyzer` 单类 27,175 行 / 212 方法（占文件 96%） | god class，阶段边界不可见 |
| `core/cfg/region_ast_generator.py` | 51,751 行；`RegionASTGenerator` 单类 51,488 行 / 248 方法 | god class，且是该仓最大单体 |
| 两文件合计 | ≈ 80k 行 ≈ 白名单 22 万行的 36% | 复杂度高度集中 |
| `parsers/ast_builder.py` vs `ast_builder_cleaned.py` | 255/253 函数，253 同名，**221 个函数体逐字相同**；各 ≈ 26k 行 | 唯一经函数级证据确证的重复，可直接去重约 2.4 万行 |
| 补丁标记（`#*(修复|补丁|临时|workaround|hack|兼容)` 或 `def _(fix|patch|...)\w*`） | 9,098 个，97% 集中在 5 个文件 | 补丁债务与 god class 高度重合 |
| 已验证的良性先例 | `region_ast_generator.py:46-235` 已有 7 个模块级纯函数（`_negate_expr`/`_flip_is_none_compare`/`_fallthrough_cond_for_jump`/`_cleanup_epilogue_pops`…） | "把纯函数从 god class 外提"在本仓已跑通，风险可控 |
| 验证体系 | `tests/` 4,057 个测试文件；round 级 gate G0–G9 + mandated 尺 + official 尺 + G4′ 严格缺陷尺 | 阶段化重构有现成的安全网，不需要新造 |

问题不是"缺知识库"，而是**没人说得清这 80k 行在做什么阶段、哪 2.4 万行是纯冗余、每一步重构该被哪道 gate 拦住**。因此本变更不做页面体系，只产出决策级解剖 + 可执行路线。

## What Changes

- 新增 `docs/refactor/region-anatomy.md`：区域归约算法的阶段划分（阶段名、输入/输出、关键不变量、逐阶段方法归属表与 `file:line` 锚点），覆盖 `RegionAnalyzer`（212 方法）与 `RegionASTGenerator`（248 方法）全部方法，**每个方法必须归入且仅归入一个阶段**。
- 新增 `docs/refactor/dup-matrix.md`：白名单内逐对重复矩阵，函数级证据（同名/同体/同哈希），并对每对给出处置结论（合并 / 删除 / 保留并说明理由）与预计净减行数。
- 新增 `docs/refactor/roadmap.md`：阶段化重构路线——每步的前置条件、允许触碰的模块集合、必过 gate（G0 语法+G1 靶一致+G3 批量 402+G4 official 尺+G4′ 严格尺+G7 同源重放）、回滚方式、预计收敛行数，以及**明确"本轮不动"清单**。
- 新增 `tools/anatomy/extract_stages.py`：从源码 AST 自动产出阶段/方法归属表与重复矩阵的**证据数据**（JSON/Markdown），使文档可随代码刷新而不腐烂；`region-anatomy.md` 与 `dup-matrix.md` 的数字必须来自该工具。
- 明确阶段模型作为后续实现的契约：区域归约 = `CFG → 块语义标注 → 区域识别（9 类） → 区域层级装配 → 结构化语句生成 → 表达式重建 → 后处理` 七阶段，阶段之间只允许通过显式数据结构传递。

## Capabilities

### New Capabilities

- `region-stage-model`: 区域归约七阶段模型 + 阶段边界的显式数据结构契约；`RegionAnalyzer`/`RegionASTGenerator` 全部方法可归入唯一阶段。
- `dup-triage`: 白名单内重复代码的函数级识别与处置规则（合并/删除/保留三类结论 + 证据要求）。
- `refactor-verification`: 每个重构步骤的 gate 准入/准出契约（复用 round 级 G0–G9 体系，禁止"先改后测"）。

### Modified Capabilities

- 无（本变更不修改任何反编译器源码与既有测试口径）。

## Impact

- **不影响运行时**：不改 `core/`、`parsers/`、`bytecode/`、`utils/` 任何一行；仅新增 `docs/refactor/` 与 `tools/anatomy/`。
- **不影响并行迭代**：round74 代理继续在 `core/cfg/region_*.py` 上工作；本变更的证据表以"生成时刻"标注，路线文档给出并发协作规则（同一文件被并行修改时以 regenerate 为准，禁止在文档里手改数字）。
- **验证方式**：`python tools/anatomy/extract_stages.py` 可复现全部数字；`openspec validate region-algorithm-decomposition` 通过。
- **后续受益**：任何"抽取 RegionASTGenerator 某一阶段为独立模块"的实际搬移变更，都以本变更的阶段表 + roadmap 的 gate 契约为准入材料。
