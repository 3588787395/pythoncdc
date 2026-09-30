---
type: entity
title: bytecode_ops.py
tags:
  - code-kb
related: []
created: 2026-09-28
updated: 2026-09-28
kind: module
file: bytecode/bytecode_ops.py
content_hash: 3ff67057df753983e1ae344a2ec3e797
lines: 995
patch_markers: 3
method_count: 28
sources:
  - bytecode/bytecode_ops.py
---

# bytecode/bytecode_ops.py

源文件：`bytecode/bytecode_ops.py`（995 行，md5 `3ff67057df753983e1ae344a2ec3e797`）

## 指标

| 指标 | 值 |
|---|---|
| lines | 995 |
| patch_markers | 3 |
| method_count | 28 |
| 顶层类/函数 | 1/28 |

## 摘要

字节码操作模块

## 关键符号

### 类

- `Opcode` :10

### 顶层函数

- `opcode_to_name()` :245
- `byte_to_opcode()` :602
- `bc_next()` :607
- `bc_read_byte()` :634
- `bc_read_signed_byte()` :645
- `bc_read_int()` :651
- `bc_read_int_signed()` :661
- `bc_read_long()` :666
- `_parse_varint()` :671
- `bc_load_name()` :695
- `bc_load_global()` :706
- `bc_load_const()` :717
- `bc_load_fast()` :724
- `bc_load_deref()` :735
- `bc_load_closure()` :756
- `bc_load_classderef()` :761
- `opcode_description()` :807
- `version_supports_opcode()` :912
- `disassemble_instruction()` :961
- `disassemble_bytecode()` :979
- …共 28 个顶层函数，仅列体长前 20

## 相关页面

- [[index|Wiki Index]]
