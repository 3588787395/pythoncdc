# Pass 5 WITH 修复报告

## 修复内容

### Fix 1: 同步 Pass4-WITH 注释中再次漂移的 early pass 行号引用

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:14811-14815`（Pass4-WITH 同步注释段）

**问题根因**（与 Pass4-WITH 同型行号漂移）：
Pass 4 WITH 在同步 Pass3-WITH 注释时，引用了当时实际的 early pass 行号：
```
# [Pass4-WITH] 同步：经多轮 Pass 3 修改后，early pass 实际行号
# 已下移至 L14314-L14355（含注释段；`if region.is_async and
# region.target is None:` 起始于 L14331）。原 L14312-L14336
# 引用为 Pass 3 写入时的快照，本轮仅同步注释行号引用，未触碰
# 可执行代码，控制流不变。
```

经 Pass 4 自身修改（注释段扩展使行号下移），当前实际 early pass 位置已进一步漂移：
- `[Round5-08] async with` 注释段起始：L14350
- `if region.is_async and region.target is None:` 起始：**L14367**（非 L14331）
- `_async_target_early = ...` STORE 提取：L14372-L14381
- `region.target = _async_target_early`：L14383
- early pass 整体区间：L14350-L14391（非 L14314-L14355）

Pass 4 注释中的 L14314-L14355 / L14331 已与实际不符，误导读者。

**修复策略**：
保留原 Pass4-WITH 注释文本不变（历史追溯用），追加 `[Pass5-WITH]` 段落，说明：
1. 经 Pass 4 修改后行号再次漂移
2. 现实际位置：early pass L14350-L14391，`if region.is_async and region.target is None:` 起始 L14367
3. 原 Pass 4 引用 L14314-L14355 / L14331 为 Pass 4 写入时的快照
4. 验证方法：grep `if region.is_async and region.target is None:` 可重新定位（全仓仅 1 处命中）
5. 本轮仅同步注释行号引用，未触碰可执行代码，控制流不变

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
**结果**：`80 0 0 80 2.4 WITH files=80` —— 与基线一致（80 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用 | **已同步**（追加 [Pass5-WITH] 段落，L14314-L14355/L14331 → L14350-L14391/L14367） |

## 未完成项

1. **early pass 仍存**（L14350-L14391）：待归约期统一 async-with target 检测后，
   将 early pass 与 async body 提取合并为识别期单次归属。
2. **`_generate_with` 内 `_try_else_fixup` / `_if_blocks_fixup` save-mutate-restore 模式**
   （Pass 1 test_findings.md 已登记）：违反「每块唯一归属」原则，待识别期排除 cleanup 块归属冲突。
3. **`_filter_if_blocks_in_with` / `_is_with_exit_cleanup` 改为区域归属查表**
   （Pass 1 test_findings.md 已登记）：消除生成期 isinstance 遍历与 opname 启发式。
4. **`_generate_with` 内 ~165 行字符串字面量**（与 MATCH 区域同型）：技术上属冗余 no-op
   表达式，但内容为意图性文档，本轮保留。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：追加 [Pass5-WITH] 注释段落同步 early pass 行号）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/WITH/pass_05/fix_report.md`（本报告）
