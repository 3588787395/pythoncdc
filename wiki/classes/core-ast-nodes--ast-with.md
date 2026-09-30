---
type: entity
title: ASTWith
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTWith
defined_at: core/ast_nodes.py:4025
class_lines: 112
method_count: 9
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTWith

定义于 `core/ast_nodes.py:4025`（类体 112 行，9 个方法），所属模块 [[core-ast-nodes]]。

> with语句节点

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :4031
- `is_async()` :4044
- `items()` :4048
- `items()` :4052
- `context()` :4056
- `optional_vars()` :4063
- `body()` :4070
- `body()` :4074
- `to_code()` :4077

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
