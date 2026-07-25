# Pass 5 ASSERT 修复报告

## 修复内容

### Fix 1: 标记 `_identify_assert_regions` 内 `_reach_raise_varargs_block` Fallback 补丁反模式

**问题位置**：`/workspace/core/cfg/region_analyzer.py:9442-9456`（`_identify_assert_regions` 内 `mb = self._reach_raise_varargs_block(succ)` 兜底分支）

**问题根因**（Pass 1 已登记、Pass 4 fix_report.md §未完成项 4 已识别但未添加内联标记）：
`_identify_assert_regions` 内 message_block 查找采用「主路径 + 兜底补丁」二段式结构：

```python
mb = self._find_assertion_error_block(succ)   # 主路径
if mb is not None:
    message_block = mb
    break
# Fallback: walk fall-through chain for cases where
# LOAD_ASSERTION_ERROR is in a later block (legacy behavior
# preserved for any edge cases not covered by the new helper).
mb = self._reach_raise_varargs_block(succ)   # 兜底补丁
if mb is not None:
    message_block = mb
    break
```

主路径 `_find_assertion_error_block` 与兜底路径 `_reach_raise_varargs_block` 形成
「主路径 + 兜底补丁」结构，违反「识别阶段一次正确」原则——若主路径漏识别某些
LOAD_ASSERTION_ERROR 位置，兜底路径用 walk fall-through chain 补救。

Pass 4 fix_report.md §未完成项 4 引用的行号 `L9436` 已过时——经多轮修改行号已下移至
**L9442-L9448**（Fallback 注释起始 L9442，`_reach_raise_varargs_block` 调用 L9453）。
原引用误导读者。

**修复策略**：
仅添加 `[Pass5-ASSERT]` 内联标记注释，登记：
1. 本 Fallback 块为「Fallback 补丁」反模式（违反「识别阶段一次正确」）
2. Pass 1 已登记、Pass 4 fix_report §未完成项 4 已识别但未添加内联标记
3. 原 Pass 4 引用 L9436 已过时，现实际位于 L9442-L9448
4. 改写需统一 `_find_assertion_error_block` / `_reach_raise_varargs_block` 为单一查询路径
5. 待后续 Pass 统一两查询路径后一并删除本 Fallback 块

不触及任何可执行代码，控制流不变。

**为什么不直接消除（与 Pass4-ASSERT docstring 同步不同）**：
统一两查询路径属控制流变更——主路径 `_find_assertion_error_block` 基于反向 RAISE_VARARGS
扫描定位，兜底路径 `_reach_raise_varargs_block` 基于 walk fall-through chain 兜底。两路径
在不同 LOAD_ASSERTION_ERROR 位置场景下互补，直接删除兜底会导致主路径漏识别的边角场景
message_block 丢失。本轮保守仅添加标记，把消除留给后续 Pass。

控制流不变，仅注释文本追加。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py ASSERT
```
**结果**：`21 6 0 27 2.4 ASSERT files=27` —— 与基线一致（21 passed, 6 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| Fallback 补丁（主路径 + 兜底二段式） | **已标记**（追加 [Pass5-ASSERT] 内联注释，同步 Pass 4 过时行号 L9436 → L9442-L9448） |

## 未完成项

1. **`_reach_raise_varargs_block` Fallback 补丁消除**（本轮已标记）：控制流变更，需统一
   `_find_assertion_error_block` / `_reach_raise_varargs_block` 为单一查询路径后删除。
2. **`_build_assert_message` 非 build_string 分支未同步主路径 [Round8-12] walrus 反向
   RAISE_VARARGS 扫描**（Pass 2 已标记）：属控制流变更，超出本轮约束。
3. **6 例预存失败**（3 ternary-in-assert-test + 3 assert-in-if-body 链式比较变体）：需
   识别顺序调整，非本轮范围。
4. **四条 fall-through 遍历器逻辑近似可统一**（Pass 2 已评估）：终止条件有细微差别，
   统一会改变边界行为，超出保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_assert_regions` L9442 添加 `[Pass5-ASSERT]` Fallback 补丁反模式标记）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/ASSERT/pass_05/fix_report.md`（本报告）
