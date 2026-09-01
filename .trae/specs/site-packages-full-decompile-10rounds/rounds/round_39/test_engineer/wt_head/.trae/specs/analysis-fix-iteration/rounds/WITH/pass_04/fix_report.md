# Pass 4 WITH 修复报告

## 修复内容

### Fix 1: 同步 Pass 3 WITH 注释中过时的 early pass 行号引用

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:14767`（Pass 3 添加的 `[Pass3-WITH]` 注释）

**问题根因**：
Pass 3 在删除 async-with target 冗余兜底块时添加的 `[Pass3-WITH]` 注释引用了
early pass 的行号「L14312-L14336」。经多轮 Pass 3 后续修改（MATCH/ASSERT/BOOLOP/
TERNARY/CC/SEQ 各自的删除/注释操作使 region_ast_generator.py 行数下移），当前
early pass 实际行号已下移至 L14314-L14355（含注释段；`if region.is_async and
region.target is None:` 起始于 L14331）。注释行号与实际不符，误导读者。

**修复策略**：
保留原 `[Pass3-WITH]` 注释文本不变（历史追溯用），追加 `[Pass4-WITH]` 段落，说明：
1. 经多轮 Pass 3 修改后，early pass 实际行号已下移至 L14314-L14355。
2. `if region.is_async and region.target is None:` 起始于 L14331。
3. 原 L14312-L14336 引用为 Pass 3 写入时的快照。
4. 本轮仅同步注释行号引用，未触碰可执行代码，控制流不变。

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

附加验证：全量 with_region 套件（191 文件）实测 `191 passed in 2.12s`，0 failed，
0 skipped，与 docstring「100% 完全匹配（with_region 191/191）」表述一致（无需校正）。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用 | **已同步**（追加 [Pass4-WITH] 段落） |

## 未完成项

1. **early pass 仍存**（L14314-L14355）：待归约期统一 async-with target 检测后，
   将 early pass 与 async body 提取（L14708-L14765）合并为识别期单次归属。
2. **`_generate_with` 内 `_try_else_fixup` / `_if_blocks_fixup` save-mutate-restore 模式**
   （Pass 1 test_findings.md 已登记）：违反「每块唯一归属」原则，待识别期排除 cleanup 块归属冲突。
3. **`_filter_if_blocks_in_with` / `_is_with_exit_cleanup` 改为区域归属查表**
   （Pass 1 test_findings.md 已登记）：消除生成期 isinstance 遍历与 opname 启发式。
4. **`_generate_with` 内 L14789-L14954 ~165 行字符串字面量**（与 MATCH 区域 L15610-L15819
   同型）：技术上属冗余 no-op 表达式，但内容为意图性文档，本轮保留（与 MATCH Pass 2/3 决策一致）。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：追加 [Pass4-WITH] 注释段落）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/WITH/pass_04/fix_report.md`（本报告）
