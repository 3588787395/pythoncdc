# Pass 6 ASSERT 修复报告

## 修复内容

### Fix 1: 同步 Pass5-ASSERT 标记中过时的 `_reach_raise_varargs_block` 行号引用

**问题位置**：`/workspace/core/cfg/region_analyzer.py:9464-9471`（`_identify_assert_regions` 内 Pass5-ASSERT 标记注释段）

**问题根因**（与 Pass5-MATCH 同型行号漂移）：
Pass5-ASSERT 在标记 `_reach_raise_varargs_block` Fallback 补丁反模式时，写入：
```
# [Pass5-ASSERT] 已知反模式（Pass 1 已登记、Pass 4 fix_report
# §未完成项 4 引用 L9436 已过时——现实际位于 L9442-L9448）：
# 本 Fallback 块为「Fallback 补丁」反模式...
```

经 `git show 7bb17e5:core/cfg/region_analyzer.py | grep -n "_reach_raise_varargs_block(succ)"`
确认 Pass5-ASSERT 写入时该调用位于 L9453。但 marker 文本中「L9442-L9448」范围与
fix_report 描述（「Fallback 注释起始 L9442，`_reach_raise_varargs_block` 调用 L9453」）
不完全一致——L9442 实为 `message_block = None` 行，L9448 实为 `[R8 fix]` 注释中段，
均非 Fallback 块本身。该范围在 Pass5-ASSERT 写入时即与实际有偏差。

经 Pass6-TRY 上游修改（在 `_identify_try_except_regions` docstring L4770-L4781
追加 [Pass5-TRY]/[Pass6-TRY] 段落约 13 行），`_reach_raise_varargs_block(succ)` 调用
现位于 L9482。Pass5-ASSERT marker 中的 L9442-L9448 / L9453 引用与实际严重不符。

**修复策略**（与 Pass6-MATCH 同型——仅注释文本同步 + 改用相对位置描述）：
保留原 Pass5-ASSERT 注释文本不变（历史追溯用），追加 `[Pass6-ASSERT]` 段落，说明：
1. Pass 5 写入后经 Pass6-TRY 上游修改使行号再次下移
2. **不再引用具体行号**——改为「`mb = self._reach_raise_varargs_block(succ)` 行
   紧邻本注释段下方」（避免递归漂移：本注释段自身会改变行号）
3. 原 Pass 5 引用 L9442-L9448 / L9453 为 Pass 5 写入时的快照，已过时
4. 同时承认 Pass5-ASSERT marker 中的 L9442-L9448 范围与 Pass5-ASSERT fix_report
   描述不完全一致（存疑），本轮不再追究
5. 行号漂移原因：Pass6-TRY 在 `_identify_try_except_regions` docstring 追加段落
6. 验证方法：grep `_reach_raise_varargs_block(succ)` 在 `_identify_assert_regions`
   内可重新定位（紧邻本注释段下方）
7. 后续 Pass 若实施「主路径 + 兜底统一为单一查询路径」可一并消除此反模式与
   行号引用漂移源

**为什么不引用具体行号**（与 Pass5-ASSERT 不同）：
与 Pass6-MATCH 同型思路——每轮上游修改都会使行号继续漂移，形成「行号引用→漂移→
再同步→再漂移」的递归问题。本轮 Pass6-ASSERT 改用「紧邻本注释段下方的
`mb = self._reach_raise_varargs_block(succ)` 行」相对位置描述，从根因上消除漂移源。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py ASSERT
```
**结果**：`21 6 0 27 2.5 ASSERT files=27` —— 与基线一致（21 passed, 6 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（Pass5-ASSERT 同型） | **已同步**（追加 [Pass6-ASSERT] 段落，改用相对位置描述避免递归漂移） |

## 未完成项

1. **`_reach_raise_varargs_block` Fallback 补丁消除**（Pass 5 已标记、本轮同步行号引用）：
   控制流变更，需统一 `_find_assertion_error_block` / `_reach_raise_varargs_block`
   为单一查询路径后删除。
2. **`_build_assert_message` 非 build_string 分支未同步主路径 [Round8-12] walrus 反向
   RAISE_VARARGS 扫描**（Pass 2 已标记）：属控制流变更，超出本轮约束。
3. **6 例预存失败**（3 ternary-in-assert-test + 3 assert-in-if-body 链式比较变体）：需
   识别顺序调整，非本轮范围。
4. **四条 fall-through 遍历器逻辑近似可统一**（Pass 2 已评估）：终止条件有细微差别，
   统一会改变边界行为，超出保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_assert_regions` 内 Pass5-ASSERT 标记追加 [Pass6-ASSERT] 同步段落，改用相对位置描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/ASSERT/pass_06/fix_report.md`（本报告）
