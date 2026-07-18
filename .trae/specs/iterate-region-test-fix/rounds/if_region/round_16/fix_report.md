# IF Region Round 16 — 修复报告

## 修复概览

- **测试总数**：15 个（10 failed + 1 skipped + 4 passed）
- **已修复**：9 个（模式 A 6 + 模式 B/E 2 + 模式 C 1）
- **已知限制**：2 个（模式 D 1 failed + 模式 F 1 skipped）
- **IF 全量回归**：709 passed / 13 failed / 7 skipped（基线 696 passed / 12 failed / 6 skipped，+13 passed 修复，+1 failed 模式 D 尝试，+1 skipped 模式 F）
- **CFM 全量回归**：4 failed / 323 passed / 11 skipped（无退化）
- **match_region 回归**：3 failed / 193 passed / 2 skipped（无退化）

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `core/cfg/region_analyzer.py` | `_is_implicit_default_body` 添加 NOP 前缀检查（模式 A）；`_mr_collect_case_body` guard 块排除（模式 B） |
| `core/cfg/pattern_parser.py` | `_collect_pattern_blocks` 识别简单变量 guard 块（模式 B）；`_extract_case_guard_from_blocks` 放宽 pattern_store_names 检查（模式 B/E）；`_extract_class_pattern` 移除 POP_TOP 过滤（模式 C）；新增 `_count_class_pattern_instrs` 方法 + 嵌套 class pattern 检测（模式 D） |

## 模式 A: case _: 通配分支丢失（6 个，已修复）

- test_adv16_match_or_pattern_in_if.py
- test_adv16_match_or_string_in_if.py
- test_adv16_match_or_multi_value_in_if.py
- test_adv16_match_class_pattern_in_if.py
- test_adv16_match_class_positional_in_if.py
- test_adv16_match_class_mixed_args_in_if.py

**根因**: `_is_implicit_default_body` 未识别显式 `case _: pass` body 的 NOP 前缀标记。CPython 为显式 case _: body 添加 NOP 前缀以区分隐式 default fall-through。

**修复**: 在 `_is_implicit_default_body` 中添加 NOP 前缀检查，识别显式 `case _: pass` body。

## 模式 B/E: guard 守卫丢失（2 个，已修复）

- test_adv16_match_class_guard_in_if.py（模式 B）
- test_adv16_match_guard_in_if.py（模式 E）

**根因**: 简单变量 guard（如 `if z`）的字节码 `LOAD_NAME z / POP_JUMP_FORWARD_IF_FALSE` 无 COMPARE_OP，未被识别为 guard 块；同时 pattern_store_names 检查过严，不允许 guard 引用外部变量。

**修复**:
1. `_collect_pattern_blocks` 识别简单变量 guard 块（LOAD_NAME + POP_JUMP_IF_FALSE 模式）
2. `_extract_case_guard_from_blocks` 放宽 pattern_store_names 检查
3. `_mr_collect_case_body` 将 guard 块排除出 body，加入 `pattern_check_blocks`
4. 回归防护：guard 位于 case header 块内时不提取

## 模式 C: wildcard positional 退化（1 个，已修复）

- test_adv16_match_class_wildcard_pos_in_if.py

**根因**: `_extract_class_pattern` 中的 `filtered` 列表过滤掉了 POP_TOP，但函数后续有专门处理 POP_TOP 作为通配符 `_` 的代码，导致该代码永远无法执行。`Point(_, _)` 退化为 `Point()`。

**修复**: 从 `filtered` 过滤列表中移除 POP_TOP。

## 模式 D: 嵌套 class pattern（1 个，已知限制）

- test_adv16_match_class_nested_in_if.py

**现象**: `case Outer(x=Inner(1))` → `<MatchClass>` 占位符泄漏

**尝试修复**: 新增 `_count_class_pattern_instrs` 方法和嵌套 class pattern 检测，但反编译输出结构仍有错误（指令顺序不对）。

**风险**: 高 — 嵌套 class pattern 的字节码结构复杂，修复需要深入理解 MATCH_CLASS + UNPACK_SEQUENCE 的交互。

**状态**: 已知限制，R17 修复。

## 模式 F: mapping pattern `**rest`（1 个，已知限制）

- test_adv16_match_mapping_pattern_in_if.py

**现象**: `case {**rest}` → 重命名为 `**v` 编译失败

**状态**: 已知限制（SKIPPED）。

## 回归验证

### R16 新测试
```
13 passed, 1 failed (模式 D), 1 skipped (模式 F)
```

### IF 区域全量回归
```
709 passed, 13 failed (基线 12 + 模式 D), 7 skipped (基线 6 + 模式 F)
```

### CFM 全量回归
```
4 failed (与基线一致), 323 passed, 11 skipped
```

### match_region 回归
```
3 failed (与基线一致), 193 passed, 2 skipped
```

### 退化检查
- 无退化：CFM 4 failed 完全一致，match_region 3 failed 完全一致
- IF 709 passed 比基线 696 多 13（9 修复 + 4 通过的对照测试）

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| 模式 A: case _: 通配分支丢失 | 6 | 6 | 0 |
| 模式 B/E: guard 守卫丢失 | 2 | 2 | 0 |
| 模式 C: wildcard positional 退化 | 1 | 1 | 0 |
| 模式 D: 嵌套 class pattern | 1 | 0 | 1 |
| 模式 F: mapping pattern `**rest` | 1 | 0 | 1 |
| **合计** | **11** | **9** | **2** |

## 下一轮计划

R17 优先修复模式 D（嵌套 class pattern），需要深入分析 MATCH_CLASS + UNPACK_SEQUENCE 的字节码交互。
