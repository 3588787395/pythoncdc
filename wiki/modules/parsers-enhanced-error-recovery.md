---
type: entity
title: enhanced_error_recovery.py
tags:
  - code-kb
related: []
created: 2026-09-28
updated: 2026-09-28
kind: module
file: parsers/enhanced_error_recovery.py
content_hash: 2165f94e9eb34b91c02b02529455e4b3
lines: 576
patch_markers: 0
method_count: 25
sources:
  - parsers/enhanced_error_recovery.py
---

# parsers/enhanced_error_recovery.py

源文件：`parsers/enhanced_error_recovery.py`（576 行，md5 `eb6e93053451c1c8aab0d5e26428b0eb`）

## 指标

| 指标 | 值 |
|---|---|
| lines | 576 |
| patch_markers | 0 |
| method_count | 25 |
| 顶层类/函数 | 6/9 |

## 摘要

增强的异常处理和错误恢复机制

## 关键符号

### 类

- `ErrorContext` :13
- `ErrorRecoveryManager` :130
- `ErrorRecoveryStrategy` :218
- `StackRecoveryStrategy` :226
- `InstructionRecoveryStrategy` :309
- `BlockRecoveryStrategy` :362

### 顶层函数

- `enhanced_recover_from_error()` :379
- `enhanced_mark_uncertain_node()` :427
- `enhanced_generate_error_report()` :453
- `register_recovery_strategies()` :502
- `apply_error_recovery()` :518
- `mark_uncertain_node()` :527
- `generate_error_report()` :537
- `clear_error_state()` :545
- `get_recovery_statistics()` :557

## 相关页面

- [[index|Wiki Index]]
