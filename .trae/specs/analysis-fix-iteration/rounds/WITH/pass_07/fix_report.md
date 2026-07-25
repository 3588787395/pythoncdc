# Pass 7 WITH 修复报告

## 修复内容

### Fix 1: 同步 Pass6-WITH 段落中再次漂移的 early pass 行号引用

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:14866-14875`（Pass6-WITH 同步注释段后追加 [Pass7-WITH] 段落）

**问题根因**（与 Pass6-WITH 同型行号漂移）：

Pass 6 WITH 在同步 Pass5-WITH 注释时，引用了当时实际的 early pass 行号：
```
# [Pass6-WITH] 同步：Pass 5 写入后经 Pass6-IF/Pass6-LOOP 上游修改
# 使行号再次下移——early pass 现实际位于 L14363-L14404
# （[Round5-08] 注释起始 L14363，`if region.is_async and
# region.target is None:` 起始 L14380，`_async_target_early = None`
# L14385，`region.target = _async_target_early` L14396）。...
```

经 Pass6-TRY / Pass6-MATCH / Pass6-ASSERT / Pass6-BOOLOP / Pass6-TERNARY /
Pass6-CC / Pass6-SEQ 上游修改（在 region_ast_generator.py / region_analyzer.py
多处追加段落），early pass 行号再次一致下移 +19：

| 引用项 | Pass 6 引用 | Pass 7 实际 | 偏差 |
|---|---|---|---|
| `[Round5-08] async with` 注释起始 | L14363 | L14382 | +19 |
| `if region.is_async and region.target is None:` | L14380 | L14399 | +19 |
| `_async_target_early = None` | L14385 | L14404 | +19 |
| `region.target = _async_target_early` | L14396 | L14415 | +19 |
| early pass 整体区间 | L14363-L14404 | L14382-L14435 | +19 |

四项引用均一致漂移 +19（grep 验证），与 Pass6-WITH 同型行号漂移问题一致。
Pass6-WITH 段落中的行号引用已与实际不符，误导读者。

**修复策略**（与 Pass6-WITH 同型——仅注释文本同步）：

保留原 Pass6-WITH 注释文本不变（历史追溯用），追加 `[Pass7-WITH]` 段落，说明：
1. Pass 6 写入后经 Pass6-TRY/MATCH/ASSERT/BOOLOP/TERNARY/CC/SEQ 上游修改使行号再次一致下移 +19
2. 现实际位置：early pass L14382-L14435，`[Round5-08]` 注释起始 L14382，
   `if region.is_async and region.target is None:` 起始 L14399，
   `_async_target_early = None` L14404，`region.target = _async_target_early` L14415
3. 原 Pass 6 引用 L14363-L14404/L14380/L14385/L14396 为 Pass 6 写入时的快照
4. 验证方法不变：grep `if region.is_async and region.target is None:` 在本文件仅 1 处命中（可执行代码处，非本注释段）
5. 本轮仅同步注释行号引用，未触碰可执行代码，控制流不变

**为什么不引用具体行号**（与 Pass6-MATCH/ASSERT/BOOLOP/TERNARY/SEQ 不同）：
Pass6-WITH 段落本身就保留了「验证方法不变：grep ... 可重新定位」的兜底口径。
本轮 Pass7-WITH 沿用 Pass6-WITH 的引用 + grep 兜底方式（与 Pass6-WITH 同型），
而非改用纯 grep 验证方式描述（与 Pass6-MATCH/ASSERT 不同型）。
原因：WITH 区域的 early pass 代码块跨度大（约 53 行），完全用 grep 描述每个引用点
会过于冗长，保留行号引用 + grep 兜底更可读。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py WITH
```
**结果**：`80 0 0 80 2.3 WITH files=80` —— 与基线一致（80 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用 | **已同步**（追加 [Pass7-WITH] 段落，L14363-L14404/L14380/L14385/L14396 → L14382-L14435/L14399/L14404/L14415，一致漂移 +19） |

## 未完成项

1. **early pass 仍存**（L14382-L14435）：待归约期统一 async-with target 检测后，
   将 early pass 与 async body 提取合并为识别期单次归属。
2. **`_generate_with` 内 `_try_else_fixup` / `_if_blocks_fixup` save-mutate-restore 模式**
   （Pass 1 test_findings.md 已登记）：违反「每块唯一归属」原则，待识别期排除 cleanup 块归属冲突。
3. **`_filter_if_blocks_in_with` / `_is_with_exit_cleanup` 改为区域归属查表**
   （Pass 1 test_findings.md 已登记）：消除生成期 isinstance 遍历与 opname 启发式。
4. **`_generate_with` 内 ~165 行字符串字面量**（与 MATCH 区域同型）：技术上属冗余 no-op
   表达式，但内容为意图性文档，本轮保留。
5. **early pass 行号引用仍可能继续漂移**：本注释段依赖行号硬引用，每轮上游修改后
   需重新同步。后续 Pass 若实施「early pass 与 async body 合并」可彻底消除漂移源。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：追加 [Pass7-WITH] 注释段落同步 early pass 行号，一致漂移 +19）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/WITH/pass_07/fix_report.md`（本报告）
