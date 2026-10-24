---
type: concept
title: 语法完备性审计台账（已并入总纲）
tags:
  - code-kb
  - redirect
related:
  - "[[decompile-invariant-completeness]]"
created: 2026-09-29
updated: 2026-10-23
kind: concept
---

# 语法完备性审计台账（已并入总纲）

128 形态逐形态台账（共享管线锚点 / 表A 语句与结构 / 表B 表达式 / 表C 扩展形态 / 判定汇总）已**全量并入总纲** [[decompile-invariant-completeness]] §5。

**v9 汇总（2026-10-23）**：本页只保留 v8 历史形态基线；**v8 的 128/128 = 形状基线，不是完备**。v9 双读数：形态基线 128/128（历史）；判定空间 J v2 全量 0/1556、集成样本 51/1556（3.28%），语义样本 45 EQUAL / 6 DIFF；G4 339 条 0 proved；G6 20/24 local-bootstrap；`overall=BLOCKED`。B163–B219 共 57 项未封闭，B142 已由 B181 重新定性为形态级缺口。**历史 v8（2026-10-21）**：路径 128/128；旧形式层 128/0/0 ⇒ 100%（v3 规范十轮终值；25 行矩阵 257/257、组合级 241/242、E 门禁 6617/6617；机制 B129–B162；终表 = `.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md` + `REVIEW2.md`）。**历史 v7（2026-10-17）**：103/25/0 ⇒ 80.47%。

台账更新按总纲 §8 复审六步执行（fix 批落位 → grep 落地标记 → 台账更新 → 路径层重测 → 占比重算 → log）。

## 检索词

逐形态台账 / 128 形态 / 三锚点 / B1 / 表A 表B 表C


## 双读数（rr-v5r08 终态，2026-10-24）

- shape: 402 八分片 6617/6617、small34 1568/1568、quotation 153/153、fuzz 24/24 EQUAL、pytest 406 失败清单与冻结基线逐字节一致（rr-v5r05c..r07 树）
- judgment: J 1556 全量 C1–C5：covered_equal 250 / uncovered 189（15 探针文件 25 失配单元）/module_only 675 / unjudgeable 442；G2b 57E/3D/342 环境；G2c 5E/24D/17 环境；G3 样本 32k/602m；G4 trace 187/339 命中 152 never-hit；G6 ASSURANCE_BLOCKED
- uncovered 189 归并为 15 探针文件 25 失配单元（`TASK5_THREE_LISTS.md`）：最大族 JS-EXCEPTSTAR 96
  （e03_deep 幻影 continue＝B214 行为等价级 OPEN + e08_match_host match 坍缩）、JS-IFEXP 12、
  match 坍缩族（x02/x05/x08/x09/c4_04/r8_11/g2b/g3b）等。
