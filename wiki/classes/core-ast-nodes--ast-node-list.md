---
type: entity
title: ASTNodeList
tags:
  - code-kb
related:
  - "[[core-ast-nodes]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/ast_nodes.py
content_hash: 4058936d0217573b219ea1bd78d0b811
class: ASTNodeList
defined_at: core/ast_nodes.py:274
class_lines: 264
method_count: 11
bases: [ASTNode]
sources:
  - core/ast_nodes.py
---

# ASTNodeList

定义于 `core/ast_nodes.py:274`（类体 264 行，11 个方法），所属模块 [[core-ast-nodes]]。

> 节点列表 - 性能优化版本

## 继承与 override

- `ASTNode`

override（与仓库内基类同名方法）：

- ASTNode: __init__, to_code

## 方法清单

- `__init__()` :280
- `__iter__()` :284
- `__len__()` :288
- `__bool__()` :292
- `__getitem__()` :296
- `nodes()` :301
- `append()` :304
- `remove_first()` :323
- `remove_last()` :328
- `init()` :333
- `to_code()` :337

## 相关页面

- [[core-ast-nodes|core/ast_nodes.py]]
- [[index|Wiki Index]]
