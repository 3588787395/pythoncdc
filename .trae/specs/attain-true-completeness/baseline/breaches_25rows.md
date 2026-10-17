# 破口 25 行承接名单（WIKI_REVIEW §3.1 原样摘录）

- 源：`.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round10/WIKI_REVIEW.md` §3.1（行 163-182）
- 版本：v7 复审终表（2026-10-17；冻结树 HEAD `3e0d6905`；评审工程师执行，主代理验收）
- 用途：Task 0 承接基线——25 行破口 × 族锚点，供 Task 1「25 行破口逐行现状定案表」（tasks.md 1.3，Σ=25）逐行对账。

## 分母口径（WIKI_REVIEW.md:165）

> 口径（II.3/III.2–III.5）：Σ 行枚举权威 = `docs/refactor/syntax-coverage.json` + `tools/kb/syntax_coverage.py` 大写过滤实测 **97 = 29 语句 + 31 表达式 + 8 match 模式 + 29 操作符叶**（小写辅助节点 alias/arg/arguments/comprehension/keyword/match_case/withitem/excepthandler 不计分母），+ 表C 31 = **128**。

## 3.1 三态终表（v7）（WIKI_REVIEW.md:167-174）

| 台账表 | 行数 | 完备 | 破口 | 零能力 |
|---|---|---|---|---|
| 表A 语句与结构 | 29 | 15 | **14** | 0 |
| 表B 表达式（31+8+29） | 68 | 62 | **6** | 0 |
| 表C 扩展形态 | 31 | 26 | **5** | 0 |
| **Σ** | **128** | **103** | **25** | **0** |

## 破口 25 行清单（行内锚点 = 总纲 §5 各表「判定」列）（WIKI_REVIEW.md:176-180）

- **表A（14）**：If（B46 尾项+B78）、While（B94）、Break（B79）、Continue（B97）、Try（B87/B73/B75）、With（B93）、Match（B74+B122）、Raise（B87 变体）、Assert（B56）、Return（B88）、Delete（B84）、AugAssign（B76+B48 残留变体）、Import（B73）、Global（B75）
- **表B（6）**：BoolOp（B98）、IfExp（B123；B124 已封闭留档）、Slice（B127）、ListComp（B112②）、Await（B112①+B128）、Yield（round3 F9 存量，探针重建待办）
- **表C（5）**：augmented_assign（B76+B48 残留变体）、await_expr（B112①+B128）、global_nonlocal（B75）、match_statement（B74+B122）、slice（B127）

> 核算注（WIKI_REVIEW.md:182 原样摘录）：round9 评审表A 分组显示 Σ=28（`Delete/Assign/AnnAssign（3）` 组注缺失）与声明「29 行 14 破」差 1——按 Σ=128 与表C augmented_assign 破口唯一解 = **AugAssign 行**（破口，B76+B48 残留变体），本轮按解落账。

## 增量对照要点（WIKI_REVIEW.md:184-193，供对账参考）

- 较 round9 评审（101/27/0）**升格 2 行**：chained_comparison（表C，round9 位A B104 族）；for_else（表C，含 while-else，round9 位B B125）。
- 封闭但行不升：B124 族 5 单元全转（IfExp 行存量 B123 维持破口）；B126 n9_stmt_sweep 5→6/6（Assert 行存量 B56 维持破口）。
- 其余 22 行破口与 round9 逐位一致（`REVIEW_DRAFT.md` §3.2 移交读数维持）。
