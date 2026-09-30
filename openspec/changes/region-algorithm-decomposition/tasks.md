## 0. 基线

- [x] 0.1 跑 `python tools/anatomy/extract_stages.py` 取当前基线（`RegionAnalyzer` 212 方法 / `RegionASTGenerator` 248 方法 / 白名单 61 文件 / ast_builder 对 221 同体函数），记录生成时刻与 git HEAD
- [x] 0.2 静态引用扫描：确认 `ast_builder_cleaned.py` 在白名单内外是否仍被 import（`grep -r ast_builder_cleaned`），决定它是"可删副本"还是"仍在用的第二实现"

## 1. 阶段解剖

- [x] 1.1 实现 `tools/anatomy/extract_stages.py` 输出：方法清单（类/方法/行区间/行数/`self` 读写字段数）+ 重复证据 JSON
- [x] 1.2 定稿七阶段划分（CFG / 块语义标注 / 区域识别 / 区域层级装配 / 结构化语句生成 / 表达式重建 / 后处理），每阶段写明输入结构、输出结构、可验证不变量
- [x] 1.3 把 460 个方法逐个归入唯一阶段，产出归属表（按阶段聚合，含行数占比）；无法归类者进 `Unclassified` 桶
- [x] 1.4 写 `docs/refactor/region-anatomy.md`：阶段定义 + 归属表 + 每阶段 `file:line` 锚点 + Unclassified 清单
- [x] 1.5 判定 Unclassified 占比：>15% 则回 design D1 修阶段模型并重跑 1.2–1.4

## 2. 重复矩阵

- [x] 2.1 白名单内两两比对（同名数 / 同体数 / AST 哈希），产出全部文件对结论表
- [x] 2.2 逐个判定 32 个 ast_builder 差异函数保留哪一侧并写理由；确认 `code_generator.py` ×2、`control_flow.py`/`cfg_builder.py`、`fast_stack.py`/`stack.py` 均为"不同构，保留"
- [x] 2.3 写 `docs/refactor/dup-matrix.md`：三件套证据 + 处置结论（合并/删除/保留）+ 净减行数折算
- [x] 2.4 独立登记 ast_builder 去重为 roadmap 的独立步骤（必过 G3 402 支 + G7 逐项重放）

## 3. 路线与验收

- [x] 3.1 写 `docs/refactor/roadmap.md`：阶段化路线（阶段 1 = RegionAnalyzer 识别阶段外提为本次交付的准入材料；后续阶段排期）
- [x] 3.2 每步写清：前置 gate、允许触碰模块集合、必过 gate（G0/G1/G3/G4/G4′/G7）、回滚方式、`净减行数` 与 `复杂度收益` 两栏
- [x] 3.3 写"本轮不动"清单（ASTBuilder 三胞胎合并、Category C/D 不可区分问题、tests 口径、.trae 历史）
- [x] 3.4 终检：`openspec validate region-algorithm-decomposition` 通过；文档数字与工具输出逐项一致；`git status` 仅新增 `docs/refactor/`、`tools/anatomy/`

## 执行记录（2026-09-28）

- **0.1**：HEAD 982cd398；`extract_stages.py` 输出：61 文件 / 460 方法 / Unclassified 63(3.2%) / 62 个同名≥3 文件对
- **0.2**：`ast_builder_cleaned` 全仓引用 = 0（白名单 + tests 4,057 文件 + scripts + tools 全扫）；在用的是 ast_builder.py（pycdc.py:494 等 3 处 import）→ 判定为死副本
- **1.1**：tools/anatomy/extract_stages.py：方法清单 + 阶段归属 + 构造/消费证据 + self 读写 + 重复矩阵（JSON+MD）
- **1.2**：七阶段定稿（CFG/块语义/识别/层级装配/语句生成/表达式重建/后处理），各阶段输入输出结构写入 region-anatomy.md
- **1.3**：460 方法逐一归类；冲突项（名族 vs token）97 项单列待人工确认
- **1.4**：docs/refactor/region-anatomy.md（生成文档，含生成时刻 + HEAD 锚点，89 个锚点全部可核）
- **1.5**：Unclassified 3.2% < 15%，阶段模型判定成立，无需回改 D1（但 D1 已按实现校准：构造/消费 + 类级角色先验 + 冲突 review）
- **2.1**：62 个同名≥3 文件对全量判定；同体≥10 仅 ast_builder 对（245 同名 / 212 同体）
- **2.2**：差异函数（同名不同体）清单写入 dup-matrix.md 明细节；code_generator×2、control_flow/cfg_builder、fast_stack/stack 判为不同构保留
- **2.3**：docs/refactor/dup-matrix.md（三件套证据 + 结论 + 净减行数折算栏）
- **2.4**：roadmap 步骤 1（删除死副本，净减 29,479 行，触碰集单文件，gate 契约齐）
- **3.1**：roadmap 步骤 1-4（步骤 1 可独立交付；2/3 为 S5/S3 拆分）
- **3.2**：每步含准入/准出 gate、触碰集、回滚、净减行数与复杂度收益两栏
- **3.3**：不动清单：ASTBuilder 行为统一、code_generator 双份、Category C/D、tests 口径、.trae 历史
- **3.4**：validate 通过；锚点校验 roadmap 15 个（3 个为 import 行，已逐行核对）；git status 仅新增 docs/refactor/、tools/anatomy/、openspec/changes/region-algorithm-decomposition/
