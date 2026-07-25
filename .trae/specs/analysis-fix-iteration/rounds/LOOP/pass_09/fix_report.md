# Pass 9 LOOP 修复报告

## 修复内容

### Fix 1: 同步 Pass8-LOOP 注释中再次漂移的行号引用（+8）

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:2996-3000`
（`_loop_generate_for` 内 `# Build iterator expression` 段落后的 [Pass8-LOOP] 注释段，紧随追加 [Pass9-LOOP] 段落）

**问题根因**（与 Pass7-IF / Pass8-WITH 同型行号漂移）：

Pass 8 LOOP 在删除 `for_iter_setup` 冗余重赋值时，引用了当时实际的行号：

```
# [Pass8-LOOP] 删除冗余重赋值：`for_iter_setup` 已在 L2975 由同一表达式
# `region.metadata.get('for_iter_setup')` 赋值。L2975-2987 之间仅访问
# region.init_blocks / self.generated_blocks / self.generated_offsets /
# pre_stmts，从未修改 region.metadata，故本行重赋值恒为 no-op。
# 删除后行为完全等价（保留作 Build iterator expression 段落起始锚点）。
```

经 Pass8-ASSERT 在 L2507 处插入 [Pass8-ASSERT] 标记段落（位于本函数
`_loop_generate_for` 之前，`_build_assert_boolop_condition` 内），使本函数
整体一致下移 +8（git diff 364f64a..HEAD 验证：hunk `@@ -2507,6 +2507,14 @@`
共新增 8 行）：

| 引用项 | Pass 8-LOOP 引用 | Pass 9 实际 | 偏差 |
|---|---|---|---|
| `for_iter_setup` 首次赋值 | L2975 | L2983 | +8 |
| `if region.init_blocks:` 块范围 | L2975-L2987 | L2985-L2993 | +8/+6 |
| `# Build iterator expression` 锚点 | L2987 | L2995 | +8 |

两项起始引用均一致漂移 +8（grep 验证 `for_iter_setup = region.metadata.get`
在本文件仅 1 处命中，紧邻本注释段上方），与 Pass7-IF / Pass8-WITH 同型行号
漂移问题一致。Pass8-LOOP 段落中的行号引用已与实际不符，误导读者。

**修复策略**（与 Pass7-IF / Pass8-WITH 同型——仅注释文本同步）：

保留原 Pass8-LOOP 注释文本不变（历史追溯用），追加 `[Pass9-LOOP]` 段落，说明：

1. Pass8-LOOP 写入后经 Pass8-ASSERT 在 L2507 处插入 [Pass8-ASSERT] 标记段落
   （位于 `_loop_generate_for` 之前），使本函数整体一致下移 +8
2. 现实际位置：`for_iter_setup` 首次赋值 L2983（原 L2975），`if region.init_blocks:`
   块 L2985-L2993（原 L2977-L2987），`# Build iterator expression` 锚点 L2995
   （原 L2987）
3. 原 Pass8-LOOP 引用 L2975/L2987 为写入时快照，已过时
4. 验证方法：grep `for_iter_setup = region.metadata.get` 在本文件仅 1 处命中
   （紧邻本注释段上方）
5. 本轮仅同步注释行号引用，未触碰可执行代码，控制流不变

**为什么不引用具体行号**（与 Pass6-MATCH/ASSERT/BOOLOP/TERNARY/SEQ 不同）：
Pass8-WITH 段落本身就保留了「验证方法不变：grep ... 可重新定位」的兜底口径。
本轮 Pass9-LOOP 沿用 Pass7-IF / Pass8-WITH 的引用 + grep 兜底方式（与
Pass8-WITH 同型）。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py LOOP
```
**结果**：`79 0 0 79 2.1 LOOP files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。
无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（与 Pass7-IF / Pass8-WITH 同型） | **已同步**（追加 [Pass9-LOOP] 段落，L2975/L2987 → L2983/L2995，一致漂移 +8，原因是 Pass8-ASSERT 在 L2507 插入 8 行） |

## 未完成项

1. **3 处 Pass 2 已标记的反模式**仍挂账 Pass 3+：
   - `_preceding_if_cond` 跨区域反向抓 IfRegion
   - 跨 LoopRegion 去重后处理
   - `_is_except_handler_block` 指令模式启发式
   本轮未重构这些反模式（需识别阶段统一改造）。

2. **`_loop_generate_pre_stmts` 重命名**（如改为 `_loop_extend_inner_for_iter_pre_stmts`）：
   收益小、改动面大，本轮保守不动。

3. **docstring 首行「init_blocks」表述**：Pass7-LOOP 仅追加段落说明，未直接修改首行。
   本轮不动。

4. **`_identify_loop_regions` / `_generate_loop` docstring 中「100% 完全匹配
   （while_loop 120/120 + for_loop 193/193 = 313/313）」表述**：文件计数实测仍为
   120 + 193 = 313，与 docstring 一致；bounded subset 80 文件实测 79/0/0（0 failed）。
   「100% 完全匹配」应理解为「0 failed」（无字节码不匹配），与 Pass4-TRY /
   Pass7-TRY/MATCH/BOOLOP 同型表述校正口径一致。本轮未追加校正段落（与
   Pass4-TRY / Pass7-TRY/MATCH/BOOLOP 不同型——此处无 skipped，0 failed 表述
   准确），保留原表述。

5. **行号引用仍可能继续漂移**：本注释段依赖行号硬引用，每轮上游修改后需重新
   同步。后续 Pass 若实施「彻底删除原 L2975/L2987 引用」可同步两处（Pass8-LOOP
   段落 + Pass9-LOOP 段落）。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：追加 [Pass9-LOOP] 注释段落同步
  Pass8-LOOP 行号引用，一致漂移 +8，原因是 Pass8-ASSERT 在 L2507 插入 8 行）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/LOOP/pass_09/fix_report.md`（本报告）
