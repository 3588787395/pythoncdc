## Context

- 区域归约算法当前形态（2026-09-28 实测）：
  - `core/cfg/region_analyzer.py` 28,337 行 = 9 个区域类型类（`Region` L204 / `IfRegion` L363 / `LoopRegion` L506 / `TryExceptRegion` L784 / `WithRegion` L926 / `MatchRegion` L983 / `AssertRegion` L1016 / `BoolOpRegion` L1055 / `TernaryRegion` L1147）+ 3 个语义枚举（`BlockRole` L127 / `RegionType` L170 / `BlockSemantics` L192）+ `RegionAnalyzer` L1197（27,175 行 / 212 方法）。
  - `core/cfg/region_ast_generator.py` 51,751 行 = 7 个模块级纯函数（L46–L235）+ `_IfRegionProxy` L236 + `RegionASTGenerator` L252（51,488 行 / 248 方法）+ `generate_ast_from_regions()` L51743。
  - 两文件 80,088 行 = 白名单（61 文件 / 22 万行）的 36%。
- 迭代现状：`.trae/specs/` 27 个 spec 目录，round74 进行中；mandated 尺 6,540/6,617 = 98.84%，official 尺 5,717/5,746 = 99.50%，严格缺陷 75；每轮修补都写进这两个 god class。
- 唯一确证重复：`parsers/ast_builder.py`（255 函数 / 1,748,549 B）与 `parsers/ast_builder_cleaned.py`（253 函数 / 1,705,502 B）——253 个同名函数中 **221 个函数体 AST 逐字相同**；两文件各约 2.6 万行。`core/cfg/code_generator.py` vs `parsers/code_generator.py`（仅 5 个同名、0 同体）、`core/control_flow.py` vs `core/cfg/cfg_builder.py`（3 同名 0 同体）、`core/fast_stack.py` vs `utils/stack.py`（9 同名 0 同体）**不构成重复**，需在文档里显式排除以免误删。
- 验证体系可用：`tests/` 4,057 个测试文件；round 级 gate G0（ast+py_compile+跨层 code-only）、G1（41 靶一致性）、G2（金丝雀 4 支）、G3（批量 402 支）、G4/G4′（official 尺 / 严格缺陷尺）、G5（索引）、G5′（blast）、G6/G7（prev vs landed 逐项）、G8/G9（合成回归）。

## Goals / Non-Goals

**Goals:**

- 把 460 个方法（212 + 248）映射到七阶段模型的**唯一**阶段，产出可核对的方法归属表。
- 用函数级证据判定白名单内所有可比较文件对的重复关系，并给出三类处置结论。
- 产出一条分步路线：每步有"允许触碰的模块集合 + 必过 gate + 回滚方式 + 预计净减行数"，使后续搬移变更可被机械执行。
- 证据可复现：文档里的每个数字都由 `tools/anatomy/extract_stages.py` 从当前源码生成。

**Non-Goals:**

- 本变更**不搬移任何代码**、不改任何函数签名、不改测试口径、不动 `.trae/` 历史 spec。
- 不新增反编译器能力（不修 bug、不提通过率）。
- 不重建页面/知识库体系（上一版 `code-knowledge-base` 已归档退役，见 `openspec/changes/archive/`）。
- 不对 98.84% 剩余 77 个失败单元做归因分析（另立变更）。

## Decisions

**D1：阶段归属按"方法体实际构造/消费的数据结构"判定，方法名只作次级先验**

阶段边界取"输入/输出数据结构发生变化处"。实现上的判据（`tools/anatomy/extract_stages.py`）：

1. **构造 vs 消费**是核心信号：`IfRegion(...)` 这类**构造**调用是识别侧（S3）证据；仅作为 `isinstance`/注解/属性**读取**是生成侧（S5）证据。仅做"出现即计分"会把 `RegionASTGenerator._loop_generate_while` 误判为 S3（它只是读 `LoopRegion`）。
2. **类级角色先验**：`region_analyzer.py` 的类整体属识别侧（S1–S4 权重 ×1.2，生成侧 ×0.25），`region_ast_generator.py` 反之。两个 god class 就是管线两半，类归属本身是可靠证据。
3. **名族先验次之**（命中 +2）：`_identify_/_detect_ → S3`、`generate/_gen_ → S5`、`expr/reconstruct → S6`、`fix/patch/cleanup/merge → S7` 等。名族与 token 证据冲突时**以 token 为准**，且该方法进入"冲突项"清单供人工确认（当前 97 项）。
4. **不可归类者进 `Unclassified`**，并以 15% 占比为阶段模型正确性的判据（当前 3.2%）。

代价：静态分析给不出"该方法属于哪一步业务语义"的真值，因此文档同时给出每方法的体长、`self` 读/写字段数与 token 证据，供人工抽查；**禁止把归属表当作搬移指令**，搬移前必须按 `anatomy-evidence.json` 的 AST 哈希做"只搬移不改语义"校验。

**D2：证据优先，结论其次**
`dup-matrix.md` 中每条重复关系必须带"同名数 / 同体数 / AST 哈希"三件套；无法给出证据的相似性（如 `code_generator.py` 两份）一律记为"不同构，保留"并写明理由。禁止用行数量级相似作为重复判据。

**D3：路线以"gate 契约"而非"代码搬移顺序"组织**
每步的准入条件写成"必须先通过 G0/G1 现状基线"，准出写成"改动后 G0–G9 全部过且 mandated/official 尺不退步（WORSE=0）"。当前 round74 有 WORSE 门槛约定（ADR-1：不得以少发射换成功数），路线沿用该原则。

**D4：文档不手改数字**
`region-anatomy.md` / `dup-matrix.md` 的表格由 `tools/anatomy/extract_stages.py` 生成正文片段，文档内标注生成时刻；并行迭代改动源码后重跑工具即可。并行代理与人工同时改同一文件时，以工具输出为准（路线文档写明此协作规则）。

**D5：净减行数按"可删行"折算，不承诺"总行数下降"**
ast_builder 去重净减 ≈ 2.4 万行（删 cleaned 的 221 个同体函数 + 差异部分需人工判定）；阶段化搬移**不减少行数**（只降复杂度）。路线里两栏分开写：`净减行数` 与 `复杂度收益（god class 拆分数/最大类行数）`，避免用"减行"混淆两件事。

**D6：不引入新依赖**
提取器只用标准库 `ast`/`hashlib`/`json`/`re`（python 3.11 本机可用），不装 numpy/pandas、不引入包管理变更。

## Risks / Trade-offs

- [并行 round74 正在改 `region_*.py`，解剖表可能 1 天内过期] → 文档标注生成时刻 + D4 的重跑规则；路线第 0 步就是"跑一次提取器取基线"。
- [把 460 个方法硬塞进七阶段会诱导"为分类而分类"] → 阶段必须有可验证的输入/输出差异（Requirements 里写清每阶段数据结构）；无法归类的进 `Unclassified` 桶并在文档中显式列出数量，若 >15% 则判定阶段模型有误并回到 D1。
- [ast_builder 去重可能引入回归（cleaned 与原版有 32 个函数体差异）] → 去重列为独立步骤，必过 G3 批量 402 支 + G7 prev/landed 逐项重放；32 个差异函数逐一判定保留哪一侧并记录理由。
- [路线过长导致无人执行] → 每步独立可交付、可单独回滚；路线只承诺"阶段 1（RegionAnalyzer 识别阶段外提）"为下一次搬移变更的准入材料，其余阶段为后续排期。
- [7,075 行 ast_generator 顶部已有纯函数先例，但类内同族方法可能强依赖 self 状态] → 阶段表标注每个方法的 `self` 依赖面（读/写字段数），外提成本高的阶段排在后面。

## Migration Plan

1. 第 0 步：跑 `tools/anatomy/extract_stages.py` 取基线数字，写入文档。
2. 第 1 步：定稿七阶段表 + Unclassified 桶（若超标则修 D1）。
3. 第 2 步：定稿重复矩阵（含 32 个差异函数逐个判定）。
4. 第 3 步：定稿 roadmap（阶段 1 准入材料齐备即可结束本变更）。
5. 回滚：本变更仅新增 `docs/refactor/` 与 `tools/anatomy/`，删除即回滚；不动源码故无运行时回滚面。

## Open Questions

- 七阶段里"后处理"是否应独立成段，还是并入"表达式重建"？取决于 `RegionASTGenerator` 中后处理类方法对已生成 AST 的实际改写规模（解剖时统计）。
- `ast_builder` 32 个差异函数中，`ast_builder.py` 侧是否有 0 调用死代码？需静态引用扫描（未验证）。
- round74 结束后 region 文件的最终形态未知，阶段表的"稳定基线"应取哪一版？默认取路线签署时的 HEAD。
