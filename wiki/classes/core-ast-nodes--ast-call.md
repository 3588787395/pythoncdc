---
type: entity
title: ASTCall
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTCall
defined_at: core/ast_nodes.py:1721
class_lines: 232
method_count: 8
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTCall

定义于 `core/ast_nodes.py:1721`（类体 232 行，8 个方法），所属模块 [[core-ast-nodes]]。

> 函数调用节点 - 性能优化版本

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :1727
- `func()` :1737
- `pparams()` :1741
- `pparams()` :1745
- `kwparams()` :1749
- `var()` :1753
- `kw()` :1757
- `to_code()` :1760

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
