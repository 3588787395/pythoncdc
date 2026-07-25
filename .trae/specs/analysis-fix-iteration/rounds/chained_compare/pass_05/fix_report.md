# Pass 5 CC (Chained Compare) 修复报告

## 修复内容

### Fix 1: 删除 `compute_chained_compare_operands` 内 `if block_idx == 0 and last_store_idx >= 0: pass` 死代码块

**问题位置**：`/workspace/core/cfg/region_analyzer.py:2650-2660`（`compute_chained_compare_operands` 内 for 循环 `if instr.opname.startswith('LOAD_'):` 分支）

**问题根因**（Pass 1-4 未触及的死代码，与 Pass3-LOOP `_loop_collect_child_regions` 内 `if ... pass` 死代码同型）：

原代码结构：
```python
if instr.opname.startswith('LOAD_'):
    if block_idx == 0 and last_store_idx >= 0:
        pass                              # <- 死代码：内层仅 pass
    load_instrs.append(instr)             # <- 无条件执行
```

判据分析：
1. **内层 `if ... pass` 块无副作用**：`pass` 不修改任何状态变量，不 break/continue/return。
2. **`load_instrs.append(instr)` 无条件执行**：在外层 `if instr.opname.startswith('LOAD_'):` 内，
   无论内层 `if` 条件是否为真，`load_instrs.append(instr)` 都会执行。
3. **`block_idx == 0 and last_store_idx >= 0` 的实际过滤由下方独立块完成**：紧随 for 循环后的
   `if block_idx == 0 and last_store_idx >= 0: filtered_loads = []` 块基于 `last_store_idx`
   截断 `block.instructions`，重新构建 `filtered_loads` 并覆盖 `load_instrs`。
4. **疑为重构遗留**：早期版本可能在此处做内联过滤（如 `if block_idx == 0 and last_store_idx >= 0:
   continue` 跳过 last_store_idx 之前的 LOAD），后改为下方独立过滤块后未同步清理内层 if-pass。

与 Pass3-LOOP `_loop_collect_child_regions` 内两处 `if ... pass` 死代码同型——都是「内层仅 pass
无副作用」的典型重构遗留。

**修复策略**：
- 移除内层 `if block_idx == 0 and last_store_idx >= 0: pass` 死代码块
- 保留 `load_instrs.append(instr)` 无条件追加（行为不变）
- 新增 `[Pass5-CC]` 注释说明删除依据、与 Pass3-LOOP 同型性、下方独立过滤块的存在

**控制流影响**：无。删除的是无副作用 `pass` 语句，`load_instrs.append(instr)` 行为不变。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py CC
```
**结果**：`37 3 0 40 3.7 CC files=40` —— 与基线一致（37 passed, 3 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（删除无副作用 `pass` 语句） |
| 测试文件修改 | 未修改任何测试文件 |
| 死代码（`if ... pass` 无副作用块） | **已消除**（与 Pass3-LOOP 同型，重构遗留） |

## 未完成项

1. **`_try_build_*` patch chain 统一**（Pass 2 已标记 `TODO[pass2-CC]`）：高风险，需保证
   walrus / literal-middle / method-call 三特例的栈模拟语义被统一路径覆盖。
2. **Phase 3 CC extra_blocks 预扫描 / 重检测 / 字段回填删除**（Pass 2 已识别为后处理补丁）：
   前置依赖（放宽 Phase 2a CC 触发条件）未满足，直接删除会改变控制流并丢识别。
3. **`_detect_boolop_after_chained_compare` 消除**（Pass 1/2 已列）：中风险。
4. **3 例预存失败**：需针对各自模式单独设计，非保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：删除 `compute_chained_compare_operands` 内 `if ... pass` 死代码块 + 添加 [Pass5-CC] 注释）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/chained_compare/pass_05/fix_report.md`（本报告）
