---
type: entity
title: bytecode_comparator_cfg.py
tags:
  - code-kb
related: []
created: 2026-09-28
updated: 2026-09-28
kind: module
file: utils/bytecode_comparator_cfg.py
content_hash: f8573a00ce154995eedbd6e11d0c936e
lines: 542
patch_markers: 0
method_count: 12
sources:
  - utils/bytecode_comparator_cfg.py
---

# utils/bytecode_comparator_cfg.py

源文件：`utils/bytecode_comparator_cfg.py`（542 行，md5 `eb8ec0946df933823f68b7dfcbd29174`）

## 指标

| 指标 | 值 |
|---|---|
| lines | 542 |
| patch_markers | 0 |
| method_count | 12 |
| 顶层类/函数 | 4/10 |

## 摘要

字节码对比工具 (CFG模式专用) - 用于比较原始PYC和CFG反编译后的字节码差异

## 关键符号

### 类

- `DiffType` :20
- `BytecodeDiff` :40
- `FunctionAnalysis` :53
- `AnalysisReport` :68

### 顶层函数

- `analyze_const_pool_diff()` :107
- `classify_diff()` :128
- `analyze_function_bytecode()` :219
- `extract_functions()` :294
- `analyze_bytecode_detailed()` :308
- `decompile_with_cfg()` :389
- `test_cfg_decompile_and_compare()` :403
- `compare_bytecode_detailed()` :457
- `print_diff_report()` :467
- `analyze_pyc_with_cfg()` :490

## 相关页面

- [[index|Wiki Index]]
