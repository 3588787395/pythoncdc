---
type: entity
title: ASTBinary
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTBinary
defined_at: core/ast_nodes.py:1292
class_lines: 166
method_count: 9
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTBinary

定义于 `core/ast_nodes.py:1292`（类体 166 行，9 个方法），所属模块 [[core-ast-nodes]]。

> 二元操作节点 - 性能优化版本

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :1330
- `left()` :1342
- `left()` :1346
- `right()` :1350
- `right()` :1354
- `op()` :1358
- `__eq__()` :1361
- `__hash__()` :1379
- `to_code()` :1383

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
