# IF Region Round 17 — 修复报告

## 修复概览

- **测试总数**：15 个（4 failed + 11 passed）
- **已修复**：1 个测试文件的 elif 链识别问题（Bug 1-3 部分）
- **已知限制**：14 个 bug 未修复（Bug 1-3 剩余 + Bug 4-15）
- **IF 全量回归**：720 passed / 17 failed / 7 skipped（基线 709/13/7 + 11 新通过 + 4 新失败，无退化）
- **CFM 全量回归**：2 failed / 325 passed / 11 skipped（基线 4 failed，**改善 2 个 CFM 测试**，无退化）

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `core/cfg/region_analyzer.py` | `_identify_conditional_regions`: BREAK 分支后 else_succ 是条件块时不设 merge=else_succ（避免空 else_blocks 阻止 elif 链检测）；`_build_elif_region`: 添加 boundary_stop 参数，移除 terminal 块避免过度收集 |

## Bug 1-3: for + if/elif/else + flow control（部分修复）

### 已修复部分：elif 链识别
- **测试**：test_adv17_for_if_elif_else_flow.py
- **现象**：elif 退化为独立 if，`else: return i` 丢失
- **根因**：`_identify_conditional_regions` 中，当 if 的一个分支是 BREAK 块时，`merge` 被设为 `else_succ`，导致 `else_blocks` 为空（entry==merge），elif 链检测失败
- **修复**：
  1. 当 else_succ 是条件块（2 个条件后继 + 前向条件跳转）时不设 merge=else_succ
  2. `_build_elif_region` 添加 boundary_stop 参数，移除 terminal 块（RETURN_VALUE/RETURN_CONST/RAISE_VARARGS/RERAISE）避免过度收集

### 已知限制：continue 被替换为 pass
- **现象**：`continue` 被替换为 `pass`
- **根因**：Block@66 (JUMP_BACKWARD 32) 是 for 循环中唯一跳回 header 的块，被选为 back_edge_block。由于它只含 JUMP_BACKWARD 指令，且没有其他自然回边块，被标记为 LOOP_BACK_EDGE 而非 CONTINUE
- **风险**：高 — 需区分显式 continue 与编译器生成的隐式回边
- **状态**：已知限制

## Bug 4-6: while True + break 字节码歧义（已知限制）

- **测试**：test_adv17_while_multi_if_flow.py
- **现象**：`while True:` 中 break 编译为 LOAD_CONST None / RETURN_VALUE，与函数返回路径字节码相同
- **根因**：反编译器无法区分 break 和 return 的字节码
- **风险**：中 — 需上下文敏感归约
- **状态**：已知限制

## Bug 7-15: except* 异常组处理（已知限制）

- **测试**：test_adv17_try_except_star_in_if.py, test_adv17_try_except_star_multi_in_if.py
- **现象**：`except* ExcType:` 退化为 `except:`，异常类型变为 `if (not X): pass`，as e 绑定丢失等
- **根因**：反编译器完全未实现 CHECK_EG_MATCH / PREP_RERAISE_STAR / LIST_APPEND (except* 上下文) 等专用指令的归约
- **风险**：高 — 需实现 except* 完整支持
- **状态**：已知限制（Python 3.11+ 核心新特性，建议后续专门一轮处理）

## 回归验证

### R17 新测试
```
11 passed, 4 failed (Bug 1-3 部分 + Bug 4-6 + Bug 7-15)
```

### IF 区域全量回归
```
720 passed, 17 failed (基线 13 + 4 新 R17), 7 skipped
```

### CFM 全量回归
```
2 failed (基线 4, 改善 2), 325 passed (基线 323, +2), 11 skipped
```

### CFM 改善详情
elif 链修复连带改善了 2 个 CFM 测试：
- TestL12WhileBreakContinue：之前 failed，现在 passed
- TestCF2WhileIfBreakContinue：之前 failed，现在 passed

### 退化检查
- 无退化：IF 720 passed 比基线 709 多 11（4 通过的对照测试 + 7 修复相关改善）
- CFM 改善 2 个测试，0 退化

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| Bug 1-3: for + elif flow control | 3 | 1 (elif 链) | 2 (continue → pass) |
| Bug 4-6: while True + break 歧义 | 3 | 0 | 3 |
| Bug 7-15: except* 异常组 | 9 | 0 | 9 |
| **合计** | **15** | **1** | **14** |

## 意外收获

elif 链识别修复连带改善了 2 个 CFM 测试（TestL12WhileBreakContinue, TestCF2WhileIfBreakContinue），说明 elif 链识别在循环上下文中的修复具有跨测试套件的正面影响。

## 下一轮计划

R18 优先修复：
1. continue → pass 问题（BlockRole 标注区分显式 continue 与隐式回边）
2. while True + break 字节码歧义（上下文敏感归约）

except* (Bug 7-15) 建议作为独立专题后续处理。
