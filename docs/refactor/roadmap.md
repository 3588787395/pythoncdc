# 区域归约重构路线

> 数字全部来自 `tools/anatomy/extract_stages.py`（生成时刻见 `docs/refactor/region-anatomy.md` 头部与 `anatomy-evidence.json`）。
> 引用扫描见任务 0.2（`grep ast_builder_cleaned` 全仓 0 命中）。
> gate 名称沿用 round 级既有体系（G0–G9，入口在 `scripts/`），本变更不新造验收口径。

## 现状基线（本次交付的解剖结论）

| 阶段 | 方法数 | 行数 | 占比 |
|---|---:|---:|---:|
| S1 CFG 构建 | 87 | 5,349 | 6.7% |
| S2 块语义标注 | 15 | 833 | 1.0% |
| S3 区域识别 | 88 | 19,983 | 25.0% |
| S4 区域层级装配 | 8 | 525 | 0.7% |
| S5 结构化语句生成 | 89 | 33,179 | 41.6% |
| S6 表达式重建 | 82 | 13,843 | 17.3% |
| S7 后处理 | 28 | 1,784 | 2.2% |
| Unclassified | 63 | 2,517 | 3.2% |

两个 god class 合计 460 方法 / 77,880 行：

- `RegionAnalyzer`（`core/cfg/region_analyzer.py:1197`）27,175 行 / 212 方法 → 识别侧 S1–S4 占 25,538 行
- `RegionASTGenerator`（`core/cfg/region_ast_generator.py:252`）51,488 行 / 248 方法 → 生成侧 S5–S7 占 48,806 行（95%）

**最大单体方法**（前 10 个方法合计 21,934 行 = 两个 god class 的 28%）：

| # | 方法 | 类 | 行数 | 阶段 | self 读/写 | 锚点 |
|---|---|---|---:|---|---:|---|
| 1 | `_generate_block_statements_body` | RegionASTGenerator | 4,022 | S5 | 42/1 | `core/cfg/region_ast_generator.py:44955` |
| 2 | `_generate_ternary` | RegionASTGenerator | 3,639 | S5 | 44/0 | `core/cfg/region_ast_generator.py:35757` |
| 3 | `_identify_ternary_regions` | RegionAnalyzer | 2,898 | S3 | 9/8 | `core/cfg/region_analyzer.py:20515` |
| 4 | `_identify_conditional_regions` | RegionAnalyzer | 2,198 | S3 | 26/1 | `core/cfg/region_analyzer.py:15981` |
| 5 | `_process_if_blocks` | RegionASTGenerator | 1,696 | S5 | 32/1 | `core/cfg/region_ast_generator.py:21776` |
| 6 | `_loop_generate_while` | RegionASTGenerator | 1,561 | S5 | 32/0 | `core/cfg/region_ast_generator.py:5230` |
| 7 | `_build_elif_region` | RegionAnalyzer | 1,523 | S3 | 13/0 | `core/cfg/region_analyzer.py:18719` |
| 8 | `_detect_boolop_conditional_chain` | RegionAnalyzer | 1,506 | S3 | 11/0 | `core/cfg/region_analyzer.py:25183` |
| 9 | `_generate_try` | RegionASTGenerator | 1,500 | S5 | 22/3 | `core/cfg/region_ast_generator.py:26128` |
| 10 | `_identify_try_except_regions` | RegionAnalyzer | 1,391 | S3 | 9/1 | `core/cfg/region_analyzer.py:7603` |

注意 S5 三个头部方法 `_generate_block_statements_body` / `_generate_ternary` / `_process_if_blocks` 的 `self` 读字段数为 42/44/32——它们是典型的"该拆"信号：几乎读遍实例状态，说明职责边界已糊在类里。

## 步骤

### 步骤 1：删除死副本 `parsers/ast_builder_cleaned.py`（先做，因为它零风险且立刻见效）

- **证据**：全仓（白名单 61 文件 + `tests/` 4,057 个测试文件 + `scripts/` + `tools/`）对 `ast_builder_cleaned` 的引用数 = **0**；在用实现是 `parsers/ast_builder.py`（入口 `pycdc.py:494`，另见 `parsers/code_generator.py:1474`、`parsers/unified_generator.py:343`）。两文件同名函数 245 个，其中 **212 个函数体 AST 逐字相同**。
- **触碰集**：`parsers/ast_builder_cleaned.py`（单文件删除；不新增、不修改其他文件）。
- **净减行数**：**29,479 行 / 1,705,502 字节**（该文件当前实测行数；注意早前统计的 26,256 行为旧快照）。
- **准入**：G0（`ast.parse` + `py_compile` 现状全绿）、G1（41 靶一致性）基线已记录。
- **准出**：G0 通过；G3 批量 402 支 0 failed；G4 official 尺分子分母**均不退步**（WORSE=0，ADR-1）；G7 prev/landed 逐项 REGRESSED=0。
- **复杂度收益**：0（不拆类）；收益是删除 29k 行重复代码与一个 1.7MB 编译单元。
- **回滚**：`git revert` 该删除提交，或从 prev 字节镜像还原；回滚后 G0 立即可验。

### 步骤 2：`RegionASTGenerator` 的 S5 拆分（阶段 1 交付材料）

- **范围**：S5 的 89 方法 / 33,179 行 → 目标 `core/cfg/stmt/` 下的模块级生成器（沿用文件顶部 `_negate_expr`/`_fallthrough_cond_for_jump` 的纯函数先例）。
- **首批候选**（按体长 + `self` 读/写字段数）：`_generate_block_statements_body` 4,022（`self` 读/写 42/1）、`_generate_ternary` 3,639（44/0）、`_process_if_blocks` 1,696（32/1）、`_loop_generate_while` 1,561（32/0）、`_generate_try` 1,500（22/3） —— 合计 12,418 行 = 该类 24%。
- **触碰集**：`core/cfg/region_ast_generator.py` + 新增 `core/cfg/stmt/*.py`；**不得**触碰 `core/cfg/region_analyzer.py`。
- **净减行数**：0（搬移不改行数）。
- **复杂度收益**：最大方法体 4,022 → 目标 < 1,500；S5 从"单类 33k 行"变为"模块化分片"。
- **准入/准出**：同步骤 1，另加 G2 金丝雀 4 支全中、G4′ 严格缺陷数不增（当前 75）。
- **回滚**：`git revert` 步进提交；因新文件独立，回滚不影响既有导入。

### 步骤 3：`RegionAnalyzer` 的 S3 拆分

- **范围**：S3 的 88 方法 / 19,983 行 → 按区域类型分模块（`if_region.py` / `loop_region.py` / `try_region.py` / `boolop_region.py` / `ternary_region.py`），与已有 9 个区域类型类一一对应。
- **首批候选**：`_identify_ternary_regions` 2,898、`_identify_conditional_regions` 2,198、`_build_elif_region` 1,523、`_detect_boolop_conditional_chain` 1,506 —— 合计 8,125 行 = 该类 30%。
- **触碰集**：`core/cfg/region_analyzer.py` + 新增 `core/cfg/region_detect/*.py`。
- **准入/准出/回滚**：同步骤 2；额外要求 G0 的"跨层 code-only new=0"断言（禁止引入新跨层模式）。
- **净减行数**：0；复杂度收益：最大方法体 2,898 → 目标 < 1,200。

### 步骤 4：S7 后处理收口（低优先，最后做）

- **范围**：S7 的 28 方法 / 1,784 行 + 97 个"名族与 token 冲突项"里被判为 S7 的部分。
- **理由**：补丁标记最集中的修复函数集中在这一片；先把识别/生成骨架稳住，再动后处理，回归面最小。
- **准入/准出**：同步骤 2；G4′ 严格缺陷尺必须**下降或持平**。

## 本轮不动（明确排除）

- `ASTBuilder` 三胞胎（`ast_builder.py` / `ast_builder_cleaned.py` / `ast_builder_unified.py`）的**行为统一**：步骤 1 只删除死副本，不改 `ast_builder.py` 行为，也不把 `unified` 门面接进主链路。
- `core/cfg/code_generator.py`（127 方法）与 `parsers/code_generator.py`（146 方法）：同名仅 5、同体 0，**不同构，保留双份**。
- `core/control_flow.py` 与 `core/cfg/cfg_builder.py`、`core/fast_stack.py` 与 `utils/stack.py`：同上，判定为不同构。
- Category C（match 与 if-elif 字节码等价）、Category D（`while True` 尾块不可区分）：属 CPython 侧不可判定，不在重构范围。
- `tests/` 口径、`.trae/` 历史 spec、`pyc_index.json` 索引产物。

## 门槛与协作规则

- **不退步门槛**：mandated 与 official 两把尺分子分母均不得下降（WORSE=0）；沿用 ADR-1「不得以少发射换成功数」。
- **门禁顺序**：G0 → G1 → G2 → G3 → G4/G4′ → G7，任一不过即停在本步，不进下一步。
- **并行协作**：round74 代理正在改 `core/cfg/region_*.py`。触碰集与代理重叠时：先跑 `python tools/anatomy/extract_stages.py` 刷新行号锚点，再判断是否仍按本路线执行；禁止依据过期行号搬移。
- **每次搬移前**：记录被移动方法的 AST 哈希（`anatomy-evidence.json` 已有），搬移后哈希应保持一致（仅位置变化）——这是"只搬移不改语义"的机械校验。

## 排期建议

| 步骤 | 可独立交付 | 触碰文件数 | 净减行数 | 复杂度收益 |
|---|---|---:|---:|---|
| 1 删除死副本 | 是 | 1 | **−29,479** | 无（去重） |
| 2 S5 拆分 | 是（分批） | 1 + N 新增 | 0 | 最大方法体 4,022 → <1,500 |
| 3 S3 拆分 | 是（分批） | 1 + N 新增 | 0 | 最大方法体 2,898 → <1,200 |
| 4 S7 收口 | 是 | 1 | 0 | 严格缺陷尺下降 |
