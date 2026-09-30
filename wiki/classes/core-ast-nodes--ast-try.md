---
type: entity
title: ASTTry
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTTry
defined_at: core/ast_nodes.py:4139
class_lines: 139
method_count: 8
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTTry

定义于 `core/ast_nodes.py:4139`（类体 139 行，8 个方法），所属模块 [[core-ast-nodes]]。

> try语句节点

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :4146
- `body()` :4159
- `handlers()` :4163
- `orelse()` :4167
- `else_block()` :4171
- `finalbody()` :4176
- `finally_block()` :4180
- `to_code()` :4184

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
