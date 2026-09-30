---
type: entity
title: ASTNode
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTNode
defined_at: core/ast_nodes.py:218
class_lines: 54
method_count: 11
bases: [ABC]
sources:
  - core/ast_nodes.py
---

# ASTNode

定义于 `core/ast_nodes.py:218`（类体 54 行，11 个方法），所属模块 [[core-ast-nodes]]。

> AST节点基类 - 性能优化版本

## 继承与 override

- `ABC`（仓库外/未建页）

- 仓库内基类无同名方法 override

## 方法清单

- `__init__()` :224
- `type()` :232
- `node_id()` :236
- `processed()` :240
- `parent()` :244
- `parent()` :248
- `line_number()` :252
- `line_number()` :256
- `set_processed()` :259
- `add_child()` :263
- `to_code()` :268

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
