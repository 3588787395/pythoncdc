---
type: entity
title: ast_builder.py
tags:
  - code-kb
related: []
created: 2026-09-28
updated: 2026-09-28
kind: module
file: parsers/ast_builder.py
content_hash: ed1d227dad5ef67f35e0d5e0d0ce9bc6
lines: 30264
patch_markers: 2261
method_count: 283
sources:
  - parsers/ast_builder.py
---

# parsers/ast_builder.py

源文件：`parsers/ast_builder.py`（30264 行，md5 `ed1d227dad5ef67f35e0d5e0d0ce9bc6`）

## 指标

| 指标 | 值 |
|---|---|
| lines | 30264 |
| patch_markers | 2261 |
| method_count | 283 |
| 顶层类/函数 | 3/1 |

## 摘要

AST构建模块

## 现状

本文件是 **v2 路线（CFG 系）的实际实现**，由 `pycdc.py:494`（`--cfg`/`cfg_hybrid` 路线）与 `parsers/code_generator.py:1474`、`parsers/unified_generator.py:343` 使用。`[[parsers-ast-builder-cleaned|ast_builder_cleaned.py]]` 是它的零引用副本（212 个同体函数），见 [[duplicate-code-matrix]]。

## 关键符号

### 类

- [[parsers-ast-builder--control-flow-analyzer|ControlFlowAnalyzer]] :40
- [[parsers-ast-builder--data-flow-analyzer|DataFlowAnalyzer]] :792
- [[parsers-ast-builder--ast-builder|ASTBuilder]] :1060

### 顶层函数

- `get_instr_attr()` :12

## 相关页面

- [[index|Wiki Index]]
