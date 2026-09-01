# Pass 6 BOOLOP 修复报告

## 修复内容

### Fix 1: 同步 Pass5-BOOLOP 标记中过时的 `L14340 pred_op` 行号引用

**问题位置**：`/workspace/core/cfg/region_analyzer.py:14241-14250`（`_detect_while_condition_boolop_chain` 内 Pass5-BOOLOP 标记注释段）

**问题根因**（与 Pass5-MATCH/Pass5-ASSERT 同型行号漂移）：
Pass5-BOOLOP 在标记 `'FALSE' in last.opname` 子串匹配 DRY 违背反模式时，写入：
```
# [Pass5-BOOLOP] 已知反模式（Pass 1 test_findings §反模式检查已登记、Pass 2/3/4
# fix_report §未完成项 2 反复列出但未添加内联标记）：
# `'FALSE' in last.opname` / `'TRUE' in last.opname` 子串匹配判据散布 17+ 处...
# 本处为本函数内首处使用（同函数 L14340 pred_op 同型）...
```

经 `git show 7adf49b:core/cfg/region_analyzer.py | grep -n "pred_op = 'and' if 'FALSE' in pred_last.opname else 'or'"`
确认 Pass5-BOOLOP 写入时该 `pred_op` 行位于 L14350（marker 文本中「L14340」与
Pass5-BOOLOP fix_report 描述「同函数 L14352」均有偏差，存疑）。

经 Pass6-TRY 上游修改（在 `_identify_try_except_regions` docstring L4770-L4781 追加
[Pass5-TRY]/[Pass6-TRY] 段落约 13 行）+ Pass6-ASSERT 上游修改（在
`_identify_assert_regions` Pass5-ASSERT marker 追加 [Pass6-ASSERT] 段落约 10 行），
`pred_op = 'and' if 'FALSE' in pred_last.opname else 'or'` 现位于 L14387（grep 确认）。
Pass5-BOOLOP marker 中的 L14340 / L14352 引用与实际严重不符。

**修复策略**（与 Pass6-MATCH/Pass6-ASSERT 同型——仅注释文本同步 + 改用相对位置描述）：
保留原 Pass5-BOOLOP 注释文本不变（历史追溯用），追加 `[Pass6-BOOLOP]` 段落，说明：
1. Pass 5 写入后经 Pass6-TRY + Pass6-ASSERT 上游修改使行号再次下移
2. **不再引用具体行号**——改为「grep `pred_op = 'and' if 'FALSE' in pred_last.opname else 'or'`
   在 `_detect_while_condition_boolop_chain` 内可重新定位（本文件仅 1 处命中）」
   （避免递归漂移）
3. 原 Pass 5 引用 L14340 / fix_report 描述 L14352 均有偏差（存疑），本轮不再追究
4. 经 git show 7adf49b 验证，Pass 5 写入时该 `pred_op` 行实际位于 L14350
5. 后续 Pass 若实施「子串匹配→frozenset 常量统一替换」可一并消除 17+ 处 DRY 违背
   与行号引用漂移源

**为什么不引用具体行号**（与 Pass5-BOOLOP 不同）：
与 Pass6-MATCH/Pass6-ASSERT 同型思路——每轮上游修改都会使行号继续漂移。本轮
Pass6-BOOLOP 改用 grep 验证方式描述，从根因上消除漂移源。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py BOOLOP
```
**结果**：`79 0 0 79 1.6 BOOLOP files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（Pass5-BOOLOP 同型） | **已同步**（追加 [Pass6-BOOLOP] 段落，改用 grep 验证方式描述避免递归漂移） |

## 未完成项

1. **`'FALSE' in opname` / `'TRUE' in opname` 子串匹配统一替换为结构判据**（Pass 5 已标记
   首处，本轮同步行号引用；余 16+ 处待统一替换）：需先按 FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE
   多类归类，再分别定义 frozenset 常量，高风险重构。
2. **`_identify_boolop_regions` 两段重复 docstring 合并**（Pass 2/3 已评估）：长版 +
   短版「保留供快速参考」，删除任一段都会损失独有信息，需谨慎合并。
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
4. **`_detect_boolop_after_chained_compare` 生成期后处理**（Pass 1 已列为后续建议）：
   与 IF 区域 TODO[pass2-CC] 同源，需识别阶段统一为 BoolOpRegion 后删除。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_detect_while_condition_boolop_chain` 内 Pass5-BOOLOP 标记追加 [Pass6-BOOLOP] 同步段落，改用 grep 验证方式描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/BOOLOP/pass_06/fix_report.md`（本报告）
