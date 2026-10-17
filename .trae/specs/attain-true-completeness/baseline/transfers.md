# 移交项承接名单（FIX_R9 §4 + WIKI_REVIEW 遗留与建议）

- 源A（S9）：`.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round9/FIX_R9.md` §4（行 117-122）
- 源B（S1）：`.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round10/WIKI_REVIEW.md`「遗留与建议」（行 293-299）与「异常节」（行 153-161）
- 用途：Task 0 承接基线——移交项 B127/B128/Yield-F9/B44 + `_graft_pending_operand` 在树事实；供 Task 1 探针重建（tasks.md 1.1/1.2）逐项对账。
- 读数核对：源文件读数与任务口径「15/16」「10/11」**逐项一致，无差异**（见下）。

## 1. B127（slice 悬挂链）

- 复验读数：**15/16**（源：`FIX_R9.md:119`，逐字「本段复验 15/16」）——与任务口径一致。
- 详情（`FIX_R9.md:119`）：e07_g4_star_slice_containers::f_slice_expr_bounds；产物实证 = 嵌套宿主 `for→if→while` 下 while 体坍缩为裸名 `b`（`if i and i: b`；源 = `while i: return xs[a+1 : b*2] + xs[a if b else 0 : 3]`）——与 B104/B124 宿主融合族同谱（条件融合 `if i and i:` + 归约吞体），非快修形，移交。
- 台账锚点：表B Slice 行 + 表C slice 行（`WIKI_REVIEW.md:179/180`）。

## 2. B128（await×条件）

- 复验读数：**10/11**（源：`FIX_R9.md:120`，逐字「本段复验 10/11」）——与任务口径一致。
- 详情（`FIX_R9.md:120`）：e12d_g9_awaits::f_await_cond_pos；失败面与 REVIEW 登记逐位一致，移交。
- 台账锚点：表B Await 行 + 表C await_expr 行（`WIKI_REVIEW.md:179/180`）。

## 3. Yield-F9 探针重建

- 源：`FIX_R9.md:121`；`WIKI_REVIEW.md:179`（「Yield（round3 F9 存量，探针重建待办）」）。
- 现状（`FIX_R9.md:121`）：round3 F9 存量；本段复核 confirm `compile_error 0/0` 空转；根因实证 = 产物非法（`yield sink(yield i)` 实参位缺括号，OK.py 不编译）⇒ 单元级读数不可得，破口判定维持；探针重建（产出可编译对照）未做，移交。

## 4. B44 证据缺口（r7_11/r7_12）

- 源：`FIX_R9.md:122`；`WIKI_REVIEW.md:221`（维持 16 表行：B44 = r7_11/r7_12 BoolOp 重复/三层/深右嵌套（B1 双入口同族）；round9 证据缺口（未抽验如实标注））。
- 详情（`FIX_R9.md:122`）：≥3 层双入口归纳；round9 证据集无对应探针；本段未重建探针，移交 round10 按 REVIEW §3.2 行 141 口径补齐。
- 台账锚点：表B BoolOp 行（存量 B98 同族；`WIKI_REVIEW.md:179`）。

## 5. `_graft_pending_operand` 在树事实（异常节）

- 源：`WIKI_REVIEW.md` 异常节（行 153-161；处置引用另见 `:298`）。
- 事实（只读实测，HEAD `3e0d6905`；`WIKI_REVIEW.md:155`，**与 wiki/log/spec 旧表述矛盾**）：
  - `core/cfg/region_ast_generator.py:43043`（`def _graft_pending_operand` 定义）、`:43174`（docstring 判据）、`:43180`（调用）；
  - 同族：`[R75 fix1]` 注释 ×3（`:43033/:43044/:43167`）；`_leading_operand` ×6（`:43052/:43059/:43170/:43230` + 发射端 `:60525/:60529`）；`_cjb_skip_inline_if` ×6（`:43044` + 发射段 `:60503-60515`）；`_contains_identity` ×6。
- 引入提交：`c53df077`（2026-09-30 harden round1 在途快照；`WIKI_REVIEW.md:156`）。
- 矛盾面（`WIKI_REVIEW.md:157-160`，勿自修代码）：总纲 §6 B1a「仅存归档 spec、未落地」+ §8.1「已废弃不落地」；`wiki/log.md` 2026-10-04 条目「确证废弃」；本规范 `spec.md:55`「落地标记 `_graft_pending_operand` 树中零命中」。
- 处置（`WIKI_REVIEW.md:161`）：总纲按在树事实更正（「路线废弃」判据不变——B1 封闭以五臂算法为准；嫁接符号族未清理、随快照在树）；log 只增不删；spec.md 冻结不改；是否追加规则面清理由主代理裁决（另 `:298` 遗留建议 4「是否清理代码符号（删除性变更）待裁决」）。
- 判定读数（grep 全表）：72 项中唯一 FAIL = `_graft_pending_operand` 应 0 实 3（`WIKI_REVIEW.md:31-32/110`）。

## 6. 遗留与建议其余项（源：`WIKI_REVIEW.md:293-299`）

| # | 项（行号） | 摘要 |
|---|---|---|
| 1 | 全表重锚未做（`:295`） | round1 `REVIEW.md` §6.2 曾建议统一重锚 §5 `file:line` 锚点；保留 2026-09-29 快照锚点（合 §5 证据规则），建议另立批次 |
| 3 | 25 vs 29 口径统一（`:297`） | B52/B53（决策表含、25 号区间外）+ B11-R2（r4_or4_and2 1/2 持平，独立另册）建议 10.3 归档时处理 |
| 5 | cfg-anatomy.md L105（`:299`） | 「B1 破口」历史叙述是否追注 v7 口径（`WIKI_REVIEW.md:286` 同注），待裁决 |

- 遗留建议 2 = B127/B128/Yield 探针重建 + B44 证据缺口（`WIKI_REVIEW.md:296`），即上文 §1-§4。
