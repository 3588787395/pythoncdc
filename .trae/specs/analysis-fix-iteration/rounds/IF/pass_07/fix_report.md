# Pass 7 IF 修复报告

## 修复内容

### Fix 1: 同步 Pass6-IF 注释中过时的第三个调用点行号引用 6607 → 6627

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:11983-11987`（`_if_generate_branch_stmts` 内 Pass6-IF 标记注释段后追加 [Pass7-IF] 段落）

**问题根因**（与 Pass6-MATCH/Pass6-ASSERT/Pass6-BOOLOP/Pass6-TERNARY/Pass6-SEQ 同型行号漂移）：

Pass6-IF 在完成「`region=None` 死形参与不可达分支删除」时，写入：
```
# [Pass6-IF] 完成 Pass5-IF deferred 的死形参与不可达分支删除：
# 1. 删除 `region=None` 形参（3 处调用点 line 3211/3949/6607 均不传 region=）
# ...
```

其中 `6607` 是 Pass6-IF 写入时第三个调用点 `branch_stmts = self._if_generate_branch_stmts(body_blocks_no_header)` 的行号快照。经 Pass6 后续上游修改（Pass6-LOOP / Pass6-TRY / Pass6-WITH / Pass6-MATCH / Pass6-ASSERT / Pass6-BOOLOP / Pass6-TERNARY / Pass6-CC / Pass6-SEQ 在 region_ast_generator.py / region_analyzer.py 多处追加段落），第三个调用点现位于 L6627（grep 验证）。

Pass6-IF 注释中的 `6607` 引用与实际不符（偏差 +20），误导读者。前两处调用点 3211/3949 仍准确（位于 region_ast_generator.py 早期，未受 Pass6 后续上游修改影响）。

**修复策略**（与 Pass6-MATCH/ASSERT/BOOLOP/TERNARY/SEQ 同型——仅注释文本同步 + 改用 grep 验证方式描述）：

保留原 Pass6-IF 注释文本不变（历史追溯用），追加 `[Pass7-IF]` 段落，说明：
1. Pass6-IF 引用「3 处调用点 line 3211/3949/6607」经 Pass6 后续上游修改使行号再次下移
2. **不再引用具体行号**——改为 grep 验证方式描述（避免递归漂移）：
   - `grep _if_generate_branch_stmts\(` 在 region_ast_generator.py 共 4 处命中
   - 3 处调用点（`else_stmts = self._if_generate_branch_stmts(...)` × 2 + `branch_stmts = self._if_generate_branch_stmts(...)` × 1） + 1 处定义
3. 原 Pass5/Pass6-IF 引用 6607 为写入时快照，已过时
4. 前两处 3211/3949 仍准确，本轮不强制重写为 grep 描述（保留原样，仅追加段落说明漂移）
5. 后续 Pass 若实施「`_if_generate_branch_stmts` 与 `_process_if_blocks` 合并」可一并消除行号引用漂移源

**为什么不引用具体行号**（与 Pass6-IF 不同）：
与 Pass6-MATCH/ASSERT/BOOLOP/TERNARY/SEQ 同型思路——每轮上游修改都会使行号继续漂移。本轮 Pass7-IF 改用 grep 验证方式描述，从根因上消除漂移源。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py IF
```
**结果**：`79 1 0 80 7.0 IF files=80` —— 与基线一致（79 passed, 1 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（Pass6-IF 同型） | **已同步**（追加 [Pass7-IF] 段落，改用 grep 验证方式描述避免递归漂移） |

## 未完成项

1. **TODO[pass2-CC] 未完成**：`_detect_boolop_after_chained_compare` 与
   `_if_generate_full_elif_chain` 中的 save/restore 块仍存在，等待后续 Pass
   将「CC + and/or 短路块」识别阶段统一为 `BoolOpRegion` 后一并删除。
2. **baseline_failures.txt 中的 1 处预存失败**：非本轮引入，未处理。
3. **`_if_generate_branch_stmts` 末尾 `return []` 防御性兜底**：调用点已 guard
   （`if _filtered_else_blocks else []`），但保留以维持函数纯防御性契约，
   不视为可删死代码，本轮不动。
4. **前两处调用点行号 3211/3949 仍准确**：本轮未强制重写为 grep 描述，
   保留原样。后续若再发生漂移可一并处理。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_if_generate_branch_stmts` 内 Pass6-IF 标记追加 [Pass7-IF] 同步段落，改用 grep 验证方式描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/IF/pass_07/fix_report.md`（本报告）
