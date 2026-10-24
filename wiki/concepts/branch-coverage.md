---
type: concept
title: 语法完备性衡量标准（已并入总纲）
tags:
  - code-kb
  - redirect
related:
  - "[[decompile-invariant-completeness]]"
created: 2026-09-29
updated: 2026-10-23
kind: concept
---

# 语法完备性衡量标准（已并入总纲）

本页内容已**全量并入总纲** [[decompile-invariant-completeness]]，以消除信息散乱。

**v9 读数（2026-10-23）**：**形态基线 128/128 仅历史回归口径，不是完备**。判定空间 J v2 全量 0/1556；集成样本 51/1556（3.28%）、45 EQUAL / 6 DIFF；G4 339 条 0 proved；G6 20/24 local-bootstrap；`overall=BLOCKED`。**历史 v8（2026-10-21）**：路径 128/128；旧形式层 128/0/0 ⇒ 100%；组合级 241/242。**历史 v7（2026-10-17）**：103/25/0 ⇒ 80.47%。

转址映射：

| 本页旧位置 | 总纲位置 |
|---|---|
| §1 无感不变式 | 总纲 §1 |
| §2 三级判定 | 总纲 §2.2 |
| §3 误解清单（17 条） | 总纲 §3 |
| §4 T1–T8 映射 | 总纲 §4 |
| §5 except\* 纠正记录 | 总纲 §7 |
| §6 破口登记 B1a/B1b/B2/B3/B4 | 总纲 §6 |
| §7 迭代机制（落地标记/复审六步/状态机） | 总纲 §8 |
| §8 数字规则 | 总纲 §0 + §2.2 + §9 |

## 检索词

双读数 / 形态基线 128/128（历史 v8） / 判定空间 0/1556（全量）、51/1556（样本） / 语义差分 45 EQUAL / 6 DIFF / G4 INCONCLUSIVE / G6 FAIL / BLOCKED / 误解清单 17 条 / 落地标记 / 复审六步


## 双读数（rr-v5r08 终态，2026-10-24）

- shape: 402 八分片 6617/6617、small34 1568/1568、quotation 153/153、fuzz 24/24 EQUAL、pytest 406 失败清单与冻结基线逐字节一致（rr-v5r05c..r07 树）
- judgment: J 1556 全量 C1–C5：covered_equal 250 / uncovered 189（15 探针文件 25 失配单元）/module_only 675 / unjudgeable 442；G2b 57E/3D/342 环境；G2c 5E/24D/17 环境；G3 样本 32k/602m；G4 trace 187/339 命中 152 never-hit；G6 ASSURANCE_BLOCKED
- 反编译器自身行覆盖（G4 trace）：339 规则锚点行 187 命中 / 152 未执行；
  ast_generator_v2 34、code_generator 35、region_ast_generator 46 条未执行为最大缺口簇。
