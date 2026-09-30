---
type: entity
title: ASTIf
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTIf
defined_at: core/ast_nodes.py:3086
class_lines: 657
method_count: 13
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTIf

定义于 `core/ast_nodes.py:3086`（类体 657 行，13 个方法），所属模块 [[core-ast-nodes]]。

> if语句节点 - 性能优化版本

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :3098
- `test()` :3112
- `test()` :3116
- `condition()` :3120
- `condition()` :3125
- `body()` :3130
- `then()` :3134
- `orelse()` :3139
- `orelse()` :3143
- `else_block()` :3147
- `else_block()` :3152
- `to_code()` :3155
- `_generate_orelse()` :3668

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
