---
type: concept
title: 语法完备性审计台账（已并入总纲）
tags:
  - code-kb
  - redirect
related:
  - "[[decompile-invariant-completeness]]"
created: 2026-09-29
updated: 2026-09-29
kind: concept
---

# 语法完备性审计台账（已并入总纲）

128 形态逐形态台账（共享管线锚点 / 表A 语句与结构 / 表B 表达式 / 表C 扩展形态 / 判定汇总）已**全量并入总纲** [[decompile-invariant-completeness]] §5。

**汇总**：路径 128/128；完备 127 / 破口 1（BoolOp B1，`region_ast_generator.py:47629-47643` + B1b 未定位）/ 零能力 0 ⇒ **99.2%**。

台账更新按总纲 §8 复审六步执行（fix 批落位 → grep 落地标记 → 台账更新 → 路径层重测 → 占比重算 → log）。

## 检索词

逐形态台账 / 128 形态 / 三锚点 / B1 / 表A 表B 表C
