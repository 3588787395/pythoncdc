---
type: entity
title: ASTIterBlock
tags:
  - code-kb
related:
  - "[[core-astree]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/astree.py
content_hash: 267d06cbe54165f9b41de7c4b77a6d50
class: ASTIterBlock
defined_at: core/astree.py:208
class_lines: 74
method_count: 11
bases: [ASTNodeList]
sources:
  - core/astree.py
---

# ASTIterBlock

定义于 `core/astree.py:208`（类体 74 行，11 个方法），所属模块 [[core-astree]]。

> 迭代块节点，类似于C++版本的ASTIterBlock

## 继承与 override

- `ASTNodeList`

override（与仓库内基类同名方法）：

- ASTNodeList: __init__, init, to_code

## 方法清单

- `__init__()` :211
- `iter_node()` :223
- `index()` :227
- `condition()` :231
- `is_comprehension()` :235
- `start()` :239
- `set_index()` :242
- `set_condition()` :247
- `set_comprehension()` :251
- `init()` :255
- `to_code()` :260

## 相关页面

- [[core-astree|core/astree.py]]
- [[index|Wiki Index]]
