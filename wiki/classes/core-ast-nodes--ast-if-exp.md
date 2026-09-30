---
type: entity
title: ASTIfExp
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTIfExp
defined_at: core/ast_nodes.py:3745
class_lines: 42
method_count: 8
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTIfExp

定义于 `core/ast_nodes.py:3745`（类体 42 行，8 个方法），所属模块 [[core-ast-nodes]]。

> 条件表达式节点 (x if condition else y)

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :3750
- `test()` :3757
- `test()` :3761
- `body()` :3765
- `body()` :3769
- `orelse()` :3773
- `orelse()` :3777
- `to_code()` :3780

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
