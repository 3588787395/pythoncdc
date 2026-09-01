# LOOP 区域 Round 05 修复报告

## 概述

- **范围**：测试工程师在 LOOP 区域 Round 05 发现的 13 个反编译错误（8 类根因），本轮聚焦 4 个 P0 bug。
- **修复结果**：**3/4 P0 bug 修复**（Bug #2 / #5 / #8），1 个已知限制（Bug #10，R06+ 处理）。
- **修改文件**：
  - `core/cfg/region_analyzer.py` — `_classify_handler_type` 检测 cleanup-only 异常表条目
  - `core/cfg/region_ast_generator.py` — `_generate_try_body` 排除嵌套 try / `_process_if_blocks` BREAK/CONTINUE 角色块跳过 merge-block 检查
  - `core/cfg/pattern_parser.py` — match pattern 相关调整
- **基线回归**：无退化（详见末节「回归验证」）。
- **算法符合度**：所有修复遵循区域归约算法 4 原则。

---

## 修复总览

| # | 错误 | 测试文件 | 根因聚类 | 状态 |
|---|------|---------|---------|------|
| 02 | while + ternary break 条件丢失 | test_r5_while_break_ternary | A ternary+break 归属 | ✅ |
| 05 | for + nested try in except handler | test_r5_for_nested_try_in_except | B 嵌套 try 边界 | ✅ |
| 08 | while + raise in finally | test_r5_while_raise_finally | C finally raise 分类 | ✅ |
| 10 | while + try/finally + break + except | test_r5_while_try_finally_break_except | D cleanup 复制污染 | ⏳ 已知限制 |

---

## 簇 A — ternary 条件 + break 归属（#02）

### 根因
`while a: if (x if cond else y): break` 中，ternary 条件的 IfRegion then 分支含 BREAK 角色块。`_process_if_blocks` 在 then 分支先取块角色时，BREAK/CONTINUE 角色块被 merge-block 检查拦截，break 未正确发射。

### 修复（`region_ast_generator.py` :: `_process_if_blocks`）
BREAK/CONTINUE 角色块跳过 merge-block 检查，由下方 BREAK/CONTINUE 逻辑直接发射 `ast.Break` / `ast.Continue`。

### 验证
`test_r5_while_break_ternary.py` 通过。字节码等价（12 vs 12 指令）。

---

## 簇 B — except handler 内嵌套 try 边界（#05）

### 根因
`for i in r: try: do() except E: try: x=1 except E2: y=2` 中，内层 try-except 的 entry 在外层 except_handler body 集合内。`_generate_try_body` 未排除此类内层 try，导致内层 try 被外层 try body 生成逻辑吞并。

### 修复（`region_ast_generator.py` :: `_generate_try_body`）
排除 entry 在外层 except_handler body / finally_blocks 集合内的内层 try，让内层 try 作为 handler body 抽象节点由 `_generate_handler_body_statements` 处理。

### 验证
`test_r5_for_nested_try_in_except.py` 通过。字节码等价（33 vs 33 指令）。

---

## 簇 C — finally 块内 raise（#08）

### 根因
`while a: try: raise E finally: cleanup()` 中，finally 块内 raise 使正常路径不可达。`_classify_handler_type` 未识别 cleanup-only 异常表条目（COPY+POP_EXCEPT+RERAISE，非 PUSH_EXC_INFO 开头），误将 try-finally 分类为 try-except-else，while 退化为 if。

### 修复（`region_analyzer.py` :: `_classify_handler_type`）
检测 cleanup-only 异常表条目（COPY+POP_EXCEPT+RERAISE，非 PUSH_EXC_INFO 开头）保护 finally body，正确分类为 'finally'。

### 验证
`test_r5_while_raise_finally.py` 通过。字节码等价（23 vs 23 指令）。

---

## 簇 D — except handler break + finally cleanup 复制污染（#10，已知限制）

### 根因
`while a: try: do() except E: if b: break finally: cleanup()` 中：
1. finally cleanup_blocks（`cleanup()`）被复制进 except handler 的 break 路径，与外层 finally: cleanup() 共存，cleanup 翻倍（违反「每块唯一归属」）。
2. TRY_FINALLY region 的块归属抑制了 `_identify_conditional_regions` 对 except handler 内 `if b:` 的 IfRegion 识别（违反「父引用子入口」）。

### 评估
此 bug 涉及 try/except/finally + break + if 的四重交互，修复方向已明确（跳过 finally_copy_blocks 中属于 except handler break 路径的 cleanup 块 + 放开 except handler body 内 IfRegion 识别），但修复复杂度高且退化风险大，留待 R06+ 处理。

### 验证
`test_r5_while_try_finally_break_except.py` 仍失败（41 vs 44 指令）。

---

## 回归验证

| 指标 | 基线（R04 后） | 当前（R05） | 结论 |
|------|---------------|------------|------|
| `tests/exhaustive/loop/round_05/` | 4 failed, 7 passed, 2 skipped | **1 failed, 10 passed, 2 skipped** | ✅ 3/4 修复 |
| `tests/exhaustive/while_loop/` + `for_loop/` | 5 failed, 308 passed | **5 failed, 308 passed** | ✅ 无退化 |
| `tests/exhaustive/loop/round_01/` | 4 failed, 10 passed, 2 skipped | **4 failed, 10 passed, 2 skipped** | ✅ 无退化 |
| `tests/exhaustive/loop/round_02/` | 12 passed | **12 passed** | ✅ 无退化 |
| `tests/exhaustive/loop/round_03/` | 12 passed | **12 passed** | ✅ 无退化 |
| `tests/exhaustive/loop/round_04/` | 12 passed | **12 passed** | ✅ 无退化 |
| `tests/exhaustive/ternary/` | 22 failed, 483 passed | **22 failed, 483 passed** | ✅ 无退化 |

**结论**：所有基线指标均满足约束，Round 05 修复 3/4 且零退化。

---

## 算法原则符合度

- **自底向上归约**：簇 B 中内层 try-except 先归约，作为外层 except handler 的抽象节点。
- **每块唯一归属**：簇 A 中 BREAK 角色块唯一归属 IfRegion then 分支；簇 C 中 cleanup-only 异常表条目唯一归属 finally body。
- **嵌套即抽象节点**：簇 B 中内层 try 在外层 except handler 中作为单抽象节点。
- **父引用子入口**：簇 A 中 IfRegion 引用 BREAK 块入口。

无跨区域启发式特例、无后处理补丁、无启发式优先级覆盖、无扁平化、无硬编码深度上限、无禁用前缀命名。
