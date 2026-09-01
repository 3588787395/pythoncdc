# Pass 6 SEQ (Sequence) 修复报告

## 修复内容

### Fix 1: 同步 Pass5-SEQ 标记中过时的「L12204/L12216/L12259 等已使用 RETURN_TERMINATOR_OPS」行号引用

**问题位置**：`/workspace/core/cfg/region_analyzer.py:16409-16425`（`_is_trivial_return_block`
内 Pass5-SEQ 标记注释段后追加 [Pass6-SEQ] 段落）

**问题根因**（与 Pass6-TERNARY / Pass6-BOOLOP / Pass6-MATCH / Pass6-ASSERT 同型行号漂移）：
Pass5-SEQ 在 `_is_trivial_return_block` 内标记 `('RETURN_VALUE', 'RETURN_CONST')` 字面量→
`RETURN_TERMINATOR_OPS` 替换时，写入：
```
# [Pass5-SEQ] 重复代码消除：原 `meaningful[0].opname in ('RETURN_VALUE', 'RETURN_CONST')`
# 字面量替换为模块级常量 RETURN_TERMINATOR_OPS（L54 定义，...
# 本文件 L12204/L12216/L12259 等已使用 RETURN_TERMINATOR_OPS，本替换使
# _is_trivial_return_block 与之一致。...
```

经 Pass6 上游修改（Pass6-TERNARY 在 L11779 追加 [Pass6-TERNARY] 段落约 14 行 +
Pass6-CC 在 L9842 追加 [Pass6-CC] 段落约 9 行 + 此前 Pass6-IF/LOOP/TRY/WITH/MATCH/
ASSERT/BOOLOP 各处段落追加）后，原三处引用已下移至 L12265/L12277/L12320（grep 验证）。
Pass5-SEQ marker 中的 L12204/L12216/L12259 引用与实际偏差 +61。

**修复策略**（与 Pass6-TERNARY/BOOLOP/MATCH/ASSERT 同型——仅注释文本同步 + 改用 grep
验证 + 相对位置描述）：
保留原 Pass5-SEQ 注释文本不变（历史追溯用），追加 `[Pass6-SEQ]` 段落，说明：
1. Pass5-SEQ 引用「L12204/L12216/L12259 等已使用 RETURN_TERMINATOR_OPS」经 Pass6 上游
   修改后已下移至 L12265/L12277/L12320
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
3. 原 Pass 5 引用 L12204/L12216/L12259 与当前 L12265/L12277/L12320 偏差 +61，本轮不再追究

**为什么不引用具体行号**（与 Pass5-SEQ 不同）：
与 Pass6-TERNARY/BOOLOP/MATCH/ASSERT 同型思路——每轮上游修改都会使行号继续漂移。本轮
Pass6-SEQ 改用 grep 验证 + 相对位置描述方式，从根因上消除漂移源。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py SEQ
```
**结果**：`127 10 0 137 1.6 SEQ files=80` —— 与基线一致（127 passed, 10 预存失败,
0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（Pass5-SEQ 同型） | **已同步**（追加 [Pass6-SEQ] 段落，改用 grep 验证 + 相对位置描述避免递归漂移） |

## 未完成项

1. **文件其他位置 50+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量**未替换（Pass5-TERNARY/SEQ
   已替换 3 处，本轮同步行号引用；余 40+ 处待统一替换）：全量替换需逐处评估语义等价性，
   留待后续 Pass 统一处理。
2. **`_loop_depth > 0` 跨层启发式消除**（Pass 4 已标记，对应 TODO[pass3-SEQ]-F）：中风险，
   需先在识别阶段完善 break 块标记。
3. **`_cond_jump_bs` 兜底分支删除**（Pass 1 TODO[pass2-SEQ]-C，已标记）：中风险，需先在
   `_identify_conditional_regions` 末尾扫描未认领条件跳转块。
4. **`_generate_block_statements` god-method 瘦身**（Pass 2 TODO[pass3-SEQ]-E）：高风险，
   需把语句边界判定移到识别阶段。
5. **`_is_trivial_return_block` Pattern 1 收紧为 `argval is None`**（Pass 2 TODO[pass2-SEQ]-B）：
   低风险但属控制流变更，需评估影响（本轮仅同步行号引用，未收紧 argval 检查）。
6. **10 例预存失败**：L1_basic NameError 类（测试基础设施问题）+ basic/test_b23yieldfrom_complex
   （字节码重建差异），非保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_is_trivial_return_block` 内 Pass5-SEQ
  标记追加 [Pass6-SEQ] 同步段落，改用 grep 验证 + 相对位置描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/sequence/pass_06/fix_report.md`（本报告）
