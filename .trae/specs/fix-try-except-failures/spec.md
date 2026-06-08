# 修复 try_except 测试失败规范（第三版）

## Why
当前 try_except 区域有2个测试失败（te104, try20），总失败数25f。之前的多轮修复已将 try_except 从8f降至2f，te088 已通过。需要修复剩余2个失败，同时确保总失败数不超过27f（原始基线）。

## 当前状态

### 测试结果（2026-06-05）
- 总失败：25f/1873p/1898t
- try_except：2f/228p/230t（te104, try20）
- 其他区域：boolop 2f, for_loop 2f, match_region 4f, nested 7f, ternary 7f, with_region 1f

### 已完成的修复
- ✅ te046 — with inside try（_find_next_with_block 修复）
- ✅ te080 — nested try-except in handler
- ✅ te081 — try-finally with nested try-except
- ✅ te100 — triple nested try
- ✅ try15 — try with return (SWAP+POP_EXCEPT+RETURN_VALUE)
- ✅ try16 — multi-nested try
- ✅ te088 — try: pass except: pass finally: pass

### 已应用的代码修改
**region_analyzer.py（4处修改）**：
1. `_classify_handler_type`：PUSH_EXC_INFO+POP_EXCEPT+RERAISE 模式识别为 except 而非 finally
2. successor 遍历中 cleanup reraise 检测：增加 POP_EXCEPT+RERAISE（无PUSH_EXC_INFO）模式
3. try_end 扩展逻辑：raw_start 不在 try 范围内时不扩展
4. paired_except_indices：except handler try_start 与 finally 不同时跳过配对

**region_ast_generator.py（3处修改）**：
1. `_generate_try_body` 嵌套 TryExceptRegion 生成：跳过 finally_blocks 中的 region 和不在 try_blocks 中的 region
2. try_try 嵌套补偿：检查 target_block 是否属于子 region
3. finally body 生成：检测并生成嵌套在 finally_blocks 中的 TryExceptRegion

## What Changes
- **Fix C**: te104 — finally copy 块泄漏到 try body（except handler return 路径上的 finally copy 块被错误放入 try body）
- **Fix E**: try20 — 复杂 try 模式（continue 丢失、条件反转）

## Impact
- Affected specs: try_except 区域反编译逻辑
- Affected code: `core/cfg/region_ast_generator.py`（主要）, `core/cfg/region_analyzer.py`（可能）
- 预期影响: try_except 2f → 0f，总失败 25f → 23f，无回归

## ADDED Requirements

### Requirement: finally copy 块不泄漏到 try body (te104)
系统 SHALL 在 try-except-finally 模式中，当 except handler 包含 return 语句时，不将 handler return 路径上的 finally copy 块放入 try body。

#### Scenario: try-except-finally-return 正确反编译
- **WHEN** 反编译 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()` 时
- **THEN** 生成 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()`
- **AND** try body 不含 `cleanup()` 和 `return 'val'`

**根因分析**：
- te104 的字节码中，except handler（offset 28-62）包含 POP_EXCEPT + cleanup() + return 'val'
- 但 POP_EXCEPT(30) 之后的 cleanup()（32-58）和 return 'val'（60-62）被错误放入 try body
- 这是因为 POP_EXCEPT 之后的代码被 `_collect_body` 当作 try body 的延续
- 实际上这些代码是 except handler 的一部分（handler 通过 finally copy 块执行 return）

**修复策略**：
1. 在 `_generate_try_body` 中，检测 try_blocks 中的块是否属于 except handler 的 return 路径
2. 如果某个 try_block 的前驱在 except_handlers 的 blocks 中，且该块包含 finally copy 代码（如 cleanup() + return），则从 try body 中过滤
3. 或者：在 region_analyzer 中，将 except handler 的 finally copy 块正确归入 handler_blocks 而非 try_blocks

### Requirement: 复杂 try 模式正确反编译 (try20)
系统 SHALL 在 for 循环内 try-except 中正确处理 continue、raise、多 except handler 和 for-else。

#### Scenario: for-try-except-continue 正确反编译
- **WHEN** 反编译 try20 源码时
- **THEN** 生成正确的结构：
  - try body 包含 `result = risky_operation(key, value)` 和 `if not result: continue` 和 `errors.append(result)`
  - except TypeError handler 包含 `errors.append('type error')` 和 `continue`
  - except ValueError handler 包含 `errors.append(str(e))` 和 `raise`
  - for-else 包含 `return 'all processed'`

**当前反编译输出**：
```python
def process_items(items, errors):
    for key, value in dict(items).items():
        try:
            result = risky_operation(key, value)
            if result:
                pass
            else:
                errors.append(result)
        except TypeError:
            errors.append('type error')
        except ValueError as e:
            errors.append(str(e))
            raise
    else:
        return 'all processed'
```

**问题**：
1. `if not result: continue` 被反编译为 `if result: pass else: errors.append(result)` — 条件反转且 continue 丢失
2. except TypeError handler 中缺少 `continue`
3. 字节码指令数不匹配（81 vs 80）

**修复策略**：
1. 修复 `if not result: continue` 的条件反转问题
2. 修复 except handler 中 continue 语句的生成
3. 这可能涉及 `_generate_try_body` 中的 continue 语句检测和条件块处理

## MODIFIED Requirements

### Requirement: 回归测试零回归
每次修复后 SHALL 运行全量回归测试。如果总失败数超过27f（原始基线），必须立即回滚。如果 try_except 区域失败数增加，也必须回滚。

## REMOVED Requirements
（无移除需求）
