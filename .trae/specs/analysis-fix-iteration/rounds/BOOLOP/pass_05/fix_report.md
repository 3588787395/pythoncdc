# Pass 5 BOOLOP 修复报告

## 修复内容

### Fix 1: 标记 `_detect_while_condition_boolop_chain` 内 `'FALSE' in opname` 子串匹配 DRY 违背反模式

**问题位置**：`/workspace/core/cfg/region_analyzer.py:14204`（`_detect_while_condition_boolop_chain` 内 `op_type = 'and' if 'FALSE' in last.opname else 'or'`）

**问题根因**（Pass 1 test_findings §反模式检查已登记、Pass 2/3/4 fix_report §未完成项 2 反复列出但未添加内联标记）：

`'FALSE' in last.opname` / `'TRUE' in last.opname` 子串匹配判据散布 17+ 处：
- `_identify_boolop_regions`（L14157）
- `_detect_while_condition_boolop_chain`（L14204, L14340）
- `_detect_boolop_chain_start`、`_detect_boolop_conditional_chain`、`_detect_boolop_short_circuit_chain`（L14463, L14488, L15160, L15339, L15458, L15460, L15545, L15550, L15558, L15700, L15779, L15859）
- 其他区域（L9550, L11636, L11639, L11651）

属「实例驱动判据 DRY 违背」反模式——重复子串匹配判据散布多处，违反 DRY 原则。
Pass 2/3/4 fix_report §未完成项 2 反复列出但均未添加内联标记，仅在外部报告记录。

**修复策略**：
仅添加 `[Pass5-BOOLOP]` 内联标记注释（在 `_detect_while_condition_boolop_chain` 内
首处使用 L14214 `op_type = 'and' if 'FALSE' in last.opname else 'or'` 前），登记：
1. 该子串匹配判据散布 17+ 处
2. Pass 1 test_findings §反模式检查已登记
3. Pass 2/3/4 fix_report §未完成项 2 反复列出但未添加内联标记
4. 同函数 L14340（现 L14352）`pred_op = 'and' if 'FALSE' in pred_last.opname else 'or'` 同型
5. 统一替换为结构判据（如 `last.opname in _FORWARD_FALSE_JUMP_OPS` frozenset 常量）属
   高风险重构——需先按 FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE 多类归类，再分别定义常量
6. 涉及 17+ 处调用点，本轮保守不动，待后续 Pass 统一常量库后一次性替换

不触及任何可执行代码，控制流不变。

**为什么不直接替换（与 Pass4-BOOLOP docstring 同步不同）**：
Pass 4 TERNARY 已说明「字面量→常量替换属纯重构，不在『仅做』清单内」。本轮遵循相同
约束——子串匹配→frozenset 替换虽属纯重构（语义等价），但涉及 17+ 处调用点 + 多类
归类（FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE），单点替换收益小且破坏一致性，本轮保守
仅添加内联标记。

控制流不变，仅注释文本追加。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py BOOLOP
```
**结果**：`79 0 0 79 1.7 BOOLOP files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 子串匹配 DRY 违背（`'FALSE' in opname` 散布 17+ 处） | **已标记**（首处使用 L14214 添加 `[Pass5-BOOLOP]` 内联标记，待后续 Pass 统一常量库后一次性替换） |

## 未完成项

1. **`'FALSE' in opname` / `'TRUE' in opname` 子串匹配统一替换为结构判据**（本轮已标记
   首处，余 16+ 处待统一替换）：需先按 FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE 多类归类，
   再分别定义 frozenset 常量，高风险重构。
2. **`_identify_boolop_regions` 两段重复 docstring 合并**（Pass 2/3 已评估）：长版 +
   短版「保留供快速参考」，删除任一段都会损失独有信息，需谨慎合并。
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
4. **`_detect_boolop_after_chained_compare` 生成期后处理**（Pass 1 已列为后续建议）：
   与 IF 区域 TODO[pass2-CC] 同源，需识别阶段统一为 BoolOpRegion 后删除。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_detect_while_condition_boolop_chain` L14214 添加 `[Pass5-BOOLOP]` 子串匹配 DRY 违背反模式标记）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/BOOLOP/pass_05/fix_report.md`（本报告）
