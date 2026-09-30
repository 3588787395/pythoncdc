---
type: entity
title: astree.py
tags:
  - code-kb
related: []
created: 2026-09-28
updated: 2026-09-28
kind: module
file: core/astree.py
content_hash: 267d06cbe54165f9b41de7c4b77a6d50
lines: 1231
patch_markers: 0
method_count: 59
sources:
  - core/astree.py
---

# core/astree.py

源文件：`core/astree.py`（1231 行，md5 `267d06cbe54165f9b41de7c4b77a6d50`）

## 指标

| 指标 | 值 |
|---|---|
| lines | 1231 |
| patch_markers | 0 |
| method_count | 59 |
| 顶层类/函数 | 11/14 |

## 摘要

AST构建和反编译模块

## 关键符号

### 类

- `BlockType` :16
- `BlockState` :70
- `ASTCondBlock` :153
- [[core-astree--ast-iter-block|ASTIterBlock]] :208
- `ASTWithBlock` :284
- `ASTContainerBlock` :330
- `LoadContext` :1182
- `StoreContext` :1188
- `ASTBlock` :1195
- `ASTMatchClass` :1218
- `ASTLoadBuildClass` :1227

### 顶层函数

- `stack_pop_top()` :367
- `check_if_expr()` :374
- `append_to_chain_store()` :413
- `build_from_code()` :446
- `handle_opcode()` :548
- `bc_next()` :1064
- `bc_load_name()` :1087
- `bc_load_global()` :1094
- `bc_load_const()` :1101
- `bc_load_fast()` :1108
- `bc_load_deref()` :1115
- `handle_fstring_build()` :1124
- `print_src()` :1137
- `decompyle()` :1160

## 相关页面

- [[index|Wiki Index]]
