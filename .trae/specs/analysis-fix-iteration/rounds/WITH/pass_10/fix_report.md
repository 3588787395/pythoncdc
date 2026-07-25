# Pass 10 WITH 修复报告

## 修复内容

### Fix 1: 同步 Pass9-WITH 段落中再次漂移的 early pass 行号引用（+11）

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:14933-14944`
（Pass9-WITH 同步注释段后追加 [Pass10-WITH] 段落）

**问题根因**（与 Pass7-WITH / Pass8-WITH / Pass9-WITH 同型行号漂移）：

Pass 9 WITH 在同步 Pass 8-WITH 注释时，引用了当时实际的 early pass 行号：

```
# [Pass9-WITH] 同步：Pass 8 写入后经 Pass8-ASSERT（L2507 处插入
# [Pass8-ASSERT] 标记段落 +8）+ Pass9-LOOP（L3001 处插入 [Pass9-LOOP]
# 段落 +7）上游修改使行号再次一致下移 +15——early pass 现实际位于
# L14419-L14460（[Round5-08] 注释起始 L14419，
# `if region.is_async and region.target is None:` 起始 L14436，
# `_async_target_early = None` L14441，
# `region.target = _async_target_early` L14452，
# early pass 末行 `region.items = _new_items` L14460）。
```

经 Pass10-LOOP（`_generate_loop` docstring 追加 [Pass10-LOOP] 段落 +6，位于
`_generate_with` 之前）+ Pass10-TRY（`_generate_try_body` 内 `[Pass 2 标记]`
注释后追加 [Pass10-TRY] 段落 +5，位于 `_generate_with` 之前）上游修改，early pass
行号再次一致下移 +11：

| 引用项 | Pass 9 引用 | Pass 10 实际 | 偏差 |
|---|---|---|---|
| `[Round5-08] async with` 注释起始 | L14419 | L14430 | +11 |
| `if region.is_async and region.target is None:` | L14436 | L14447 | +11 |
| `_async_target_early = None` | L14441 | L14452 | +11 |
| `region.target = _async_target_early` | L14452 | L14463 | +11 |
| early pass 末行 `region.items = _new_items` | L14460 | L14471 | +11 |
| early pass 整体区间 | L14419-L14460 | L14430-L14471 | +11/+11 |

五项起始引用均一致漂移 +11（grep 验证 `if region.is_async and region.target is None:`
在本文件仅 1 处命中，可执行代码处），与 Pass7-WITH / Pass8-WITH / Pass9-WITH 同型
行号漂移问题一致。Pass9-WITH 段落中的行号引用已与实际不符，误导读者。

**修复策略**（与 Pass7-WITH / Pass8-WITH / Pass9-WITH 同型——仅注释文本同步）：

保留原 Pass9-WITH 注释文本不变（历史追溯用），追加 `[Pass10-WITH]` 段落，说明：

1. Pass 9 写入后经 Pass10-LOOP（`_generate_loop` docstring +6）+ Pass10-TRY
   （`_generate_try_body` 注释 +5）上游修改使行号再次一致下移 +11
2. 现实际位置：early pass L14430-L14471，`[Round5-08]` 注释起始 L14430，
   `if region.is_async and region.target is None:` 起始 L14447，
   `_async_target_early = None` L14452，`region.target = _async_target_early`
   L14463，early pass 末行 `region.items = _new_items` L14471
3. 原 Pass 9 引用 L14419-L14460/L14436/L14441/L14452/L14460 为 Pass 9 写入时的快照
4. 验证方法不变：grep `if region.is_async and region.target is None:` 在本文件
   仅 1 处命中（可执行代码处，非本注释段）
5. 本轮仅同步注释行号引用，未触碰可执行代码，控制流不变

**为什么不引用具体行号**（与 Pass6-MATCH/ASSERT/BOOLOP/TERNARY/SEQ 不同）：
Pass9-WITH 段落本身就保留了「验证方法不变：grep ... 可重新定位」的兜底口径。
本轮 Pass10-WITH 沿用 Pass7-WITH / Pass8-WITH / Pass9-WITH 的引用 + grep 兜底方式。

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
**结果**：`80 0 0 80 2.3 WITH files=80` —— 与基线一致（80 passed, 0 failed, 0 errors）。
无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（与 Pass7/8/9-WITH 同型） | **已同步**（追加 [Pass10-WITH] 段落，L14419-L14460/L14436/L14441/L14452/L14460 → L14430-L14471/L14447/L14452/L14463/L14471，一致漂移 +11，原因是 Pass10-LOOP +6 + Pass10-TRY +5） |

## 未完成项

1. **early pass 仍存**（L14430-L14471）：待归约期统一 async-with target 检测后，
   将 early pass 与 async body 提取合并为识别期单次归属。
2. **`_generate_with` 内 `_try_else_fixup` / `_if_blocks_fixup` save-mutate-restore 模式**
   （Pass 1 test_findings.md 已登记）：违反「每块唯一归属」原则，待识别期排除 cleanup 块归属冲突。
3. **`_filter_if_blocks_in_with` / `_is_with_exit_cleanup` 改为区域归属查表**
   （Pass 1 test_findings.md 已登记）：消除生成期 isinstance 遍历与 opname 启发式。
4. **early pass 行号引用仍可能继续漂移**：本注释段依赖行号硬引用，每轮上游修改后
   需重新同步。后续 Pass 若实施「early pass 与 async body 合并」可彻底消除漂移源。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：追加 [Pass10-WITH] 注释段落同步
  early pass 行号，一致漂移 +11，原因是 Pass10-LOOP +6 + Pass10-TRY +5）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/WITH/pass_10/fix_report.md`（本报告）
