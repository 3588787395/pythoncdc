---
type: entity
title: ASTFunctionDef
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTFunctionDef
defined_at: core/ast_nodes.py:2493
class_lines: 340
method_count: 13
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTFunctionDef

定义于 `core/ast_nodes.py:2493`（类体 340 行，13 个方法），所属模块 [[core-ast-nodes]]。

> 函数定义节点

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :2496
- `name()` :2518
- `args()` :2522
- `body()` :2526
- `returns()` :2530
- `decorators()` :2534
- `code_obj()` :2538
- `add_nonlocal()` :2542
- `nonlocal_names()` :2548
- `is_async()` :2553
- `__eq__()` :2557
- `__hash__()` :2577
- `to_code()` :2582

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
