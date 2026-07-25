# Pass 10 SEQ (Sequence) 修复报告

## 修复内容

### Fix 1: 标记 2 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量元组 DRY 违背（Pass9-SEQ §未完成项 1 兑现）

**问题位置**：
- `/workspace/core/cfg/region_ast_generator.py:25294`（`_generate_block_statements` 内 break 检测扩展段，`_meaningful_no_pop[1].opname in ('RETURN_VALUE', 'RETURN_CONST')`）
- `/workspace/core/cfg/region_ast_generator.py:20741`（`_generate_ternary` 内 trivial return 检测段，`_no_pop[1].opname in ('RETURN_VALUE', 'RETURN_CONST')`）

**问题根因**（与 Pass7-SEQ 在 `_generate_block_statements` 内标记的
`_no_pop[1].opname in ('RETURN_VALUE', 'RETURN_CONST')` 同型——
`('RETURN_VALUE', 'RETURN_CONST')` 字面量元组 DRY 违背未标记）：

Pass9-SEQ fix_report §未完成项 1 已登记：

> **`_generate_block_statements` 内 3 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量
> 统一替换为 `RETURN_TERMINATOR_OPS`**（Pass7-SEQ 已标记 L25092 首处，余 L25128 / L20595
> 同型未标记）：全量替换需逐处评估 break 模式判别语义等价性，留待后续 Pass 统一处理
> （与 Pass6-SEQ §未完成项 1 同源扩展）。

实际验证（grep `_no_pop[1].opname in ('RETURN_VALUE', 'RETURN_CONST')` 在本文件
3 处实际代码命中，不含 1 处注释文本命中）：

| Pass7-SEQ 原引行号 | 当前实际行号 | 所在方法 | 标记状态 |
|---|---|---|---|
| L25092 | L25247 | `_generate_block_statements` | Pass7-SEQ 已标记 |
| L25128 | L25294 | `_generate_block_statements` | **本轮 [Pass10-SEQ] 标记** |
| L20595 | L20741 | `_generate_ternary` | **本轮 [Pass10-SEQ] 标记** |

**Pass7-SEQ 原文表述偏差校正**：Pass7-SEQ 标记段落原文「本方法
_generate_block_statements 内尚有同模式 3 处命中」表述不准确——3 处中 L20595
（现 L20741）实位于 `_generate_ternary` 内，非 `_generate_block_statements`。
本轮 [Pass10-SEQ] 标记段落已校正此表述偏差。

**修复策略**（与 Pass7-SEQ / Pass8-CC / Pass8-ASSERT / Pass10-TERNARY 同型——
仅添加内联标记，不触碰可执行代码）：

在两处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量元组上方各追加 `[Pass10-SEQ]`
内联标记段落：

1. 标注同型反模式（与 Pass7-SEQ 已标记同型）
2. 引用 Pass9-SEQ §未完成项 1（兑现登记项）
3. 校正 Pass7-SEQ 原文「本方法 _generate_block_statements 内」表述偏差
   （L20595/L20741 实位于 `_generate_ternary` 内）
4. 引用 grep 验证方式（避免行号漂移，与 Pass8-LOOP / Pass9-LOOP /
   Pass9-BOOLOP / Pass10-CC 同型保守策略一致）
5. 本轮仅添加内联标记，未触碰可执行代码，控制流不变

控制流不变，仅添加内联注释。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python /workspace/.trae/specs/analysis-fix-iteration/run_region_tests.py SEQ
```
**结果**：`127 10 0 137 1.6 SEQ files=80` —— 与基线一致（127 passed, 10 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加内联注释） |
| 测试文件修改 | 未修改任何测试文件 |
| `('RETURN_VALUE', 'RETURN_CONST')` 字面量元组 DRY 违背未标记（Pass9-SEQ §未完成项 1，与 Pass7-SEQ 已标记同型） | **已标记**（追加 2 处 [Pass10-SEQ] 内联标记段落，并校正 Pass7-SEQ 原文「本方法 _generate_block_statements 内」表述偏差） |

## 未完成项

1. **`_generate_block_statements` 内 3 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量
   统一替换为 `RETURN_TERMINATOR_OPS`**：本轮已标记余下 2 处（L25294 / L20741），
   Pass7-SEQ 已标记首处（L25247）。3 处均已完成内联标记，后续 Pass 可统一替换为
   RETURN_TERMINATOR_OPS 模块级常量。全量替换需逐处评估 break 模式判别语义等价性。
2. **文件全量 75 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量未替换**（本轮 grep
   统计：region_ast_generator.py 75 处命中）：全量替换需逐处评估语义等价性，留待
   后续 Pass 统一处理。
3. **`_loop_depth > 0` 跨层启发式消除**（Pass 4 已标记 `TODO[pass3-SEQ]-F`，对应
   `[Pass4-SEQ]` 注释）：中风险，需先在识别阶段完善 break 块标记。
4. **`_cond_jump_bs` 兜底分支删除**（Pass 1 TODO[pass2-SEQ]-C，已标记）：中风险，
   需先在 `_identify_conditional_regions` 末尾扫描未认领条件跳转块。
5. **`_generate_block_statements` god-method 瘦身**（Pass 2 TODO[pass3-SEQ]-E）：
   高风险，需把语句边界判定移到识别阶段。
6. **`_is_trivial_return_block` Pattern 1 收紧为 `argval is None`**（Pass 2
   TODO[pass2-SEQ]-B）：低风险但属控制流变更，需评估影响。
7. **10 例预存失败**：L1_basic NameError 类（测试基础设施问题）+
   basic/test_b23yieldfrom_complex（字节码重建差异），非保守修复范围。
8. **2 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量元组标记已完成**：后续 Pass 若
   实施「字面量元组 → RETURN_TERMINATOR_OPS 模块级常量统一替换」需同步替换本 2 处
   及 Pass7-SEQ 已标记首处、本文件 75 处同型。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_block_statements` 内 L25294 与 `_generate_ternary` 内 L20741 两处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量元组上方各追加 [Pass10-SEQ] 内联标记段落，与 Pass7-SEQ 同型保守标记，并校正 Pass7-SEQ 原文「本方法 _generate_block_statements 内」表述偏差）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/sequence/pass_10/fix_report.md`（本报告）
