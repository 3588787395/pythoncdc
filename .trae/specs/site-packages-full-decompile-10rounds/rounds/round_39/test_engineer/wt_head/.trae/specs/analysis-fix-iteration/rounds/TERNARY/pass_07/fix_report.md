# Pass 7 TERNARY 修复报告

## 修复内容

### Fix 1: 同步 Pass5-TERNARY 标记中过时的「L12204/L12216/L12259 已使用 RETURN_TERMINATOR_OPS」行号引用

**问题位置**：`/workspace/core/cfg/region_analyzer.py:11815-11832`（`_is_ternary_block` 内 Pass5-TERNARY 标记注释段后追加 [Pass7-TERNARY] 段落）

**问题根因**（与 Pass6-SEQ 同型行号漂移，对称缺失）：

Pass5-TERNARY 在 `_is_ternary_block` 内完成 `('RETURN_VALUE', 'RETURN_CONST')` 字面量→
`RETURN_TERMINATOR_OPS` 替换时，写入：
```
# [Pass5-TERNARY] 已完成 Pass 4 deferred 的「重复代码消除」替换：
# 下方两处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量已替换为
# `RETURN_TERMINATOR_OPS` 模块级常量（L54 frozenset）。
# 语义等价性验证：`x in tuple` 与 `x in frozenset` 均为成员检测，
# 当 x 为 hashable 字符串时两者语义完全等价（frozenset 略快 O(1)，
# 但 2 元素差异可忽略）。本函数外 L12204/L12216/L12259 等已使用
# RETURN_TERMINATOR_OPS，本替换使 _is_ternary_block 与之一致。
# 控制流不变——`in` 判据的 True/False 结果在替换前后完全一致。
```

其中 `L12204/L12216/L12259` 是 Pass5-TERNARY 写入时三处使用 `RETURN_TERMINATOR_OPS` 的
行号快照（与 Pass5-SEQ marker 中的同型引用完全一致——Pass6-SEQ 已校正 Pass5-SEQ marker）。

经 Pass6 上游修改（Pass6-TERNARY 在 L11779 追加 [Pass6-TERNARY] 段落约 14 行 +
Pass6-CC 在 L9842 追加 [Pass6-CC] 段落约 9 行 + 此前 Pass6-IF/LOOP/TRY/WITH/MATCH/
ASSERT/BOOLOP 各处段落追加）后，原三处引用已下移至 L12292/L12304/L12347（grep 验证，
与 Pass6-SEQ fix_report 描述的「现实际 L12265/L12277/L12320」再有偏差，本轮再次漂移）。

Pass5-TERNARY marker 中的 `L12204/L12216/L12259` 引用与实际严重不符（偏差 +88/+88/+88）。

**对称缺失**（Pass6-SEQ 已在 `_is_trivial_return_block` 内校正同型引用）：

Pass6-SEQ fix_report 已对 `_is_trivial_return_block` 内 Pass5-SEQ marker 的同型
`L12204/L12216/L12259` 引用追加了 `[Pass6-SEQ]` 校正段落。但 `_is_ternary_block` 内
Pass5-TERNARY marker 的同型 `L12204/L12216/L12259` 引用**未校正**——
对称缺失。

**修复策略**（与 Pass6-SEQ/TERNARY/BOOLOP/MATCH/ASSERT 同型——仅注释文本同步 + 改用 grep
验证 + 相对位置描述）：

保留原 Pass5-TERNARY 注释文本不变（历史追溯用），追加 `[Pass7-TERNARY]` 段落，说明：
1. Pass5-TERNARY 引用「本函数外 L12204/L12216/L12259 等已使用 RETURN_TERMINATOR_OPS」
   经多轮上游修改已下移至 L12292/L12304/L12347（与 Pass6-SEQ 已校正的 Pass5-SEQ marker
   中同型行号引用一致漂移）
2. **不再引用具体行号**——改为 grep 验证 + 相对位置描述（避免递归漂移）：
   - 首处：`_identify_ternary_regions` 内嵌套函数 `_block_is_return_body` 中
     `if last.opname not in RETURN_TERMINATOR_OPS:`
     （grep `last.opname not in RETURN_TERMINATOR_OPS` 在本文件仅 1 处命中）
   - 次处：内嵌函数 `_block_ends_with_return` 中
     `return last is not None and last.opname in RETURN_TERMINATOR_OPS`
     （grep 该串在本文件仅 1 处命中）
   - 三处：内嵌函数 `_is_value_block_nested_if_header` 中
     `if _succ_last and _succ_last.opname in RETURN_TERMINATOR_OPS:`
     （grep `_succ_last and _succ_last.opname in RETURN_TERMINATOR_OPS` 在本文件仅 1 处命中）
3. 原 Pass 5 引用 L12204/L12216/L12259 与当前 L12292/L12304/L12347 偏差，本轮不再追究

**为什么不引用具体行号**（与 Pass5-TERNARY 不同）：
与 Pass6-SEQ/BOOLOP/MATCH/ASSERT 同型思路——每轮上游修改都会使行号继续漂移。本轮
Pass7-TERNARY 改用 grep 验证 + 相对位置描述方式，从根因上消除漂移源。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY
```
**结果**：`69 7 0 76 5.4 TERNARY files=80` —— 与基线一致（69 passed, 7 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（与 Pass6-SEQ 同型，对称缺失） | **已同步**（追加 [Pass7-TERNARY] 段落，改用 grep 验证 + 相对位置描述避免递归漂移） |

## 未完成项

1. **文件其他位置 50+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量**未替换（Pass5-TERNARY/SEQ
   已替换 3 处，本轮同步行号引用；Pass7-TERNARY 已再次同步 Pass5-TERNARY marker；
   余 40+ 处待统一替换）：全量替换需逐处评估语义等价性，留待后续 Pass 统一处理。
2. **7 例预存失败**（ternary 值被外层表达式消费的模式：assert method call / listcomp body
   / await call arg / for-iter subscript / compare in both / tuple-unpack / starred-list scalar）：
   需针对各自消费模式单独设计，非保守修复范围。
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
4. **`_detect_ternary_pattern` / `_generate_ternary` 函数过长**（~1600 / ~3000 行，Pass 1
   已登记）：可维护性改进。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_is_ternary_block` 内 Pass5-TERNARY 标记
  追加 [Pass7-TERNARY] 同步段落，改用 grep 验证 + 相对位置描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TERNARY/pass_07/fix_report.md`（本报告）
