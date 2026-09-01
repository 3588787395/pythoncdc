# Pass 10 TERNARY 修复报告

## 修复内容

### Fix 1: 标记 `_build_ternary_wrapped_expr` 内 `'NOT_NONE' in op` 子串匹配判据（Pass9-TERNARY §未完成项 5 兑现）

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:9781`（`_build_ternary_wrapped_expr` 栈模拟 NONE_CHECK_OPS 分支）

**问题根因**（与 Pass8-ASSERT 在 `_build_assert_boolop_chain` 内标记的
`_is_not_none_op = 'NOT_NONE' in last_instr.opname` 同型——子串匹配 DRY 违背
未标记）：

Pass9-TERNARY fix_report §未完成项 5 已登记：

> **`_sim_wrapping_instr` 内 `'NOT_NONE' in op` 子串匹配判据未标记**
> （ternary 栈模拟路径，Pass8-TERNARY grep 发现 1 处命中）：与 Pass5/Pass6-BOOLOP /
> Pass7-ASSERT / Pass8-BOOLOP 同型 DRY 违背，待后续 Pass 统一标记或替换。

实际位置在 `_build_ternary_wrapped_expr`（非 `_sim_wrapping_instr`，Pass9-TERNARY
原文表述偏差——`_build_ternary_wrapped_expr` 调用 `_sim_wrapping_instr` 处理
trapped 指令，但 NONE_CHECK 方向判定位于 `_build_ternary_wrapped_expr` 自身
NONE_CHECK_OPS 分支内），grep `'NOT_NONE' in ` 在 region_ast_generator.py 共
14 处命中，本处为 ternary 栈模拟路径唯一未标记点：

```python
# 原文（region_ast_generator.py L9779-L9781 修复前）：
                    # IF_NOT_NONE: 跳=值不是None; IF_NONE: 跳=值是None
                    # 条件 = 走 then 的条件
                    if 'NOT_NONE' in op:
                        op_str = 'is not' if jumps_to_then else 'is'
                    else:
                        op_str = 'is' if jumps_to_then else 'is not'
```

与 Pass8-ASSERT 在 L2510 标记的 `_is_not_none_op = 'NOT_NONE' in last_instr.opname`
（`_build_assert_boolop_chain` 内）、Pass8-BOOLOP 在 L17770 标记的
`'TRUE' in cond_last.opname` / `'NOT_NONE' in cond_last.opname` 同型——
均为 `'X' in opname` 子串匹配判据，散布文件 17+ 处之一。

**修复策略**（与 Pass8-ASSERT / Pass8-BOOLOP 同型——仅添加内联标记，不触碰
可执行代码）：

在 `if 'NOT_NONE' in op:` 上方追加 `[Pass10-TERNARY]` 内联标记段落：

1. 标注同型反模式（与 Pass8-ASSERT / Pass8-BOOLOP 已标记同型）
2. 引用 Pass9-TERNARY §未完成项 5（兑现登记项）
3. 校正 Pass9-TERNARY 原文「`_sim_wrapping_instr` 内」表述偏差（实际位于
   `_build_ternary_wrapped_expr` 内）
4. 说明 op 已先经 `op in NONE_CHECK_OPS` 集合判据筛选，此处子串匹配仅用于
   区分 IF_NOT_NONE / IF_NONE 方向（语义上下文）
5. 引用 grep 验证方式（避免行号漂移，与 Pass8-LOOP / Pass9-LOOP / Pass9-BOOLOP
   同型保守策略一致）

控制流不变，仅添加内联注释。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python /workspace/.trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY
```
**结果**：`69 7 0 76 5.3 TERNARY files=80` —— 与基线一致（69 passed, 7 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加内联注释） |
| 测试文件修改 | 未修改任何测试文件 |
| `'NOT_NONE' in op` 子串匹配判据未标记（与 Pass8-ASSERT / Pass8-BOOLOP 同型，Pass9-TERNARY §未完成项 5） | **已标记**（追加 [Pass10-TERNARY] 内联标记段落） |

## 未完成项

1. **文件其他位置 50+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量**未替换（Pass5-TERNARY/SEQ
   已替换 3 处，Pass7-TERNARY 已同步行号引用；余 40+ 处待统一替换）：全量替换需逐处评估语义
   等价性，留待后续 Pass 统一处理。
2. **7 例预存失败**（ternary 值被外层表达式消费的模式：assert method call / listcomp body
   / await call arg / for-iter subscript / compare in both / tuple-unpack / starred-list scalar）：
   需针对各自消费模式单独设计，非保守修复范围。
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
4. **`_detect_ternary_pattern` / `_generate_ternary` 函数过长**（~1600 / ~3000 行，Pass 1
   已登记）：可维护性改进。
5. **`'NOT_NONE' in op` 子串匹配判据统一替换为 frozenset 常量**：本轮已标记
   `_build_ternary_wrapped_expr` 内 1 处（Pass9-TERNARY §未完成项 5 兑现），
   与 Pass8-ASSERT / Pass8-BOOLOP 已标记处合计仍余 14+ 处待统一替换（grep
   `'NOT_NONE' in ` 在 region_ast_generator.py 共 14 处命中）。
6. **`_build_ternary_wrapped_expr` 内 `if 'NOT_NONE' in op:` 子串匹配标记已完成**：
   后续 Pass 若实施「子串匹配 → frozenset 常量统一替换」需同步替换本处及
   14+ 处同型。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_build_ternary_wrapped_expr` 内 `if 'NOT_NONE' in op:` 上方追加 [Pass10-TERNARY] 内联标记段落，与 Pass8-ASSERT / Pass8-BOOLOP 同型保守标记）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TERNARY/pass_10/fix_report.md`（本报告）
