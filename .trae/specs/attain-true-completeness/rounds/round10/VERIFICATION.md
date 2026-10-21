# VERIFICATION.md — v3 `attain-true-completeness` 全量终验（Task 10.1）

> 终验树 = `rr-v3r09`（1c0ea037，工作树与 origin/main 一致）；终值 = 三态 v8 **128/0/0 ⇒ 100%**。
> 所有读数出自终树实跑（B162 之后本次会话最后跑），不采信历史回包。

## §1 验证序六步终读数

| 步 | 门禁 | 终读数 | 证据 |
|---|---|---|---|
| 1 | 402 语料八分片（E 门禁） | **6617/6617 files_failure=0**（compile_error/error/failure 全 0；574s） | `rounds/round8/final_verify_summary.json` + shard0-7 分片 JSON（786+469+538+887+855+999+801+1282） |
| 2 | small34 | **1568/1568**（34/34 files success） | `rounds/round8/small34_report_new.json` |
| 3 | quotation | **153/153 success（rc=0，100.00%）** | `final_verify_summary.json.quotation` |
| 4 | pytest 七套件 | **2 failed / 282 passed / 2 xpassed**（基线名单一致） | `final_verify_summary.json.pytest` |
| 5 | IV.2 | **全绿**：IMPORT_OK/COMPILE_OK；BOM 单头（region_ast_generator/region_analyzer 均 "one"）；instrumentation code 命中 0（仅 in_string 3 处）；G3=0 | `final_verify_summary.json.iv2` |
| 6 | 维度互证 | 25 行矩阵 **257/257**；组合级+另册 **241/242**（红=属地 B142 稀窝）；7 组回归 86/46/60/71/65/172/98 全数 | `r8matrix1` / `r8combo2` / `r8fin_*` stamps |

## §2 终态账目（Task 10.3 汇报数据源）

- **三态 v8（形式层）**：完备 128 / 破口 0 / 零能力 0 ⇒ **100%**（分母 128 = 97 ast 节点 + 31 扩展形态；工具 `tools/kb/syntax_coverage.py` 重跑 sha256 `38003eb46f2bdd6a`，JSON denom/numer/pct 三读一致）。
- **组合级**：25 号终表 + 另册 B52/B53/B11-R2 并入 = 28 项全数处置（清零 9 维持 + 维持 16 全翻正 + 另册 3 翻正）；唯一属地残余 `v_nest_fin_continue`（B142 稀窝，不升格；B143 同记不升格）。破口开档 = **0**。
- **提交链**：rr-v3r00…rr-v3r10 全部在 origin/main；本轮机制 B129–B162，标记 `[Bn-V3Rn]` 174 处（R2:47/R3:25/R4:13/R5:34/R6:12/R7:21/R8:22）。
- **通用性审计面**：本次终审的每个创新都以**形态判据**（opcode 顺序/跳转极性/pred-succ/异常边/区域成员/注册态）而非命名/行号白名单实现；13 误解 13/13 自查未触犯（`round8/REVIEW.md` §4）；B145/B139 两处过宽守卫历史均由 E 门禁首跑自捕获并按 I.4 收窄（记录在案）。
- **wiki v8 落账**：总纲 §0/§5.5/§6/§9.1 + 台账页 + branch-coverage + log.md（六步实录 = `rounds/round8/WIKI_REVIEW.md`）；0 破口终态。

## §3 终归档内容（Task 10.2）

- `rounds/round10/VERIFICATION.md`（本文）
- `rounds/round10/README.md`（终态索引）
- 终验证据沿用 `rounds/round8/`（E 门禁 JSON、25 行矩阵、组合终表、REVIEW.md/REVIEW2.md/WIKI_REVIEW.md、7 组回归 stamps）
