---
type: entity
title: PycFile
tags:
  - code-kb
related:
  - "[[core-pyc-stream]]"
created: 2026-09-28
updated: 2026-09-28
kind: class
file: core/pyc_stream.py
content_hash: 9779d447a27066ffc5762fbdd1ba2459
class: PycFile
defined_at: core/pyc_stream.py:61
class_lines: 117
method_count: 17
bases: [PycData]
sources:
  - core/pyc_stream.py
---

# PycFile

定义于 `core/pyc_stream.py:61`（类体 117 行，17 个方法），所属模块 [[core-pyc-stream]]。

> PYC文件数据源

## 继承与 override

- `PycData`

override（与仓库内基类同名方法）：

- PycData: __init__, get16, get32, get64, get_buffer, get_byte, get_bytes, get_uleb128, is_open, seek, tell

## 方法清单

- `__init__()` :64
- `open()` :70
- `close()` :75
- `is_open()` :81
- `get_byte()` :85
- `get_bytes()` :95
- `get16()` :105
- `get32()` :110
- `get32_be()` :115
- `get_varint()` :120
- `get_uleb128()` :130
- `get64()` :145
- `get_buffer()` :150
- `read_all()` :154
- `tell()` :162
- `seek()` :168
- `__del__()` :175

## 相关页面

- [[core-pyc-stream|core/pyc_stream.py]]
- [[index|Wiki Index]]
