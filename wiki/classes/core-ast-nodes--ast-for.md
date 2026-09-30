---
type: entity
title: ASTFor
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTFor
defined_at: core/ast_nodes.py:3789
class_lines: 134
method_count: 15
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTFor

定义于 `core/ast_nodes.py:3789`（类体 134 行，15 个方法），所属模块 [[core-ast-nodes]]。

> for循环节点 - 性能优化版本

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :3795
- `is_async()` :3805
- `target()` :3809
- `target()` :3813
- `iter()` :3817
- `iter()` :3821
- `iter_node()` :3825
- `body()` :3830
- `body()` :3834
- `else_block()` :3838
- `else_block()` :3842
- `else_block()` :3846
- `orelse()` :3850
- `test()` :3854
- `to_code()` :3858

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
