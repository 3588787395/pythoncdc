# Pass 7 ASSERT 修复报告

## 修复内容

### Fix 1: 标记 `_detect_assert_boolop_chain` 中 `'TRUE' in cond_last.opname` 子串匹配 DRY 违背

**问题位置**：`/workspace/core/cfg/region_analyzer.py:9595-9601`（`_detect_assert_boolop_chain` 内 op 判定逻辑前追加 [Pass7-ASSERT] 标记段落）

**问题根因**（与 Pass5-BOOLOP / Pass6-BOOLOP 标记的同型 DRY 违背）：

`_detect_assert_boolop_chain` 在判定 BoolOp assert chain 首段 op 时使用子串匹配判据：
```python
cond_last = condition_block.get_last_instruction()
if not cond_last or cond_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
    return None
first_op = 'and'
if 'TRUE' in cond_last.opname or 'NOT_NONE' in cond_last.opname:
    first_op = 'or'
```

其中 `'TRUE' in cond_last.opname` / `'NOT_NONE' in cond_last.opname` 子串匹配判据与 Pass5-BOOLOP / Pass6-BOOLOP 在 `_detect_while_condition_boolop_chain` 内标记的同型反模式一致：

- Pass5-BOOLOP 已标记：`'FALSE' in last.opname` / `'TRUE' in last.opname` 子串匹配判据散布 17+ 处
- Pass6-BOOLOP 已同步行号引用，改用 grep 验证方式描述避免递归漂移
- 但 `_detect_assert_boolop_chain` 中的同型子串匹配判据**未标记**——属散布 17+ 处之一但此前未被识别

**修复策略**（与 Pass5-BOOLOP 同型——仅添加内联标记）：

在 `cond_last = condition_block.get_last_instruction()` 行前追加 `[Pass7-ASSERT]` 标记段落：
1. 说明此处子串匹配判据与 Pass5-BOOLOP / Pass6-BOOLOP 在 `_detect_while_condition_boolop_chain` 内标记的同型 DRY 违背一致
2. 后续 Pass 实施「子串匹配 → frozenset 常量统一替换」时需同步替换此处
3. 本轮仅添加内联标记，未触碰可执行代码，控制流不变
4. 验证方法：grep `'TRUE' in cond_last.opname` 在本文件仅 1 处命中（紧邻本注释段下方）

**为什么不直接替换为 frozenset 常量**：
Pass5-BOOLOP / Pass6-BOOLOP fix_report §未完成项 1 已说明全量替换需先按
FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE 多类归类，再分别定义 frozenset 常量，
属高风险重构。本轮保守仅标记，待后续 Pass 统一替换。

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
| 子串匹配 DRY 违背（与 Pass5/Pass6-BOOLOP 同型） | **已标记**（追加 [Pass7-ASSERT] 内联标记段落，与 Pass5-BOOLOP 标记同型） |

## 未完成项

1. **`_reach_raise_varargs_block` Fallback 补丁消除**（Pass 5 已标记、Pass6-ASSERT 同步行号引用）：
   控制流变更，需统一 `_find_assertion_error_block` / `_reach_raise_varargs_block`
   为单一查询路径后删除。
2. **`_build_assert_message` 非 build_string 分支未同步主路径 [Round8-12] walrus 反向
   RAISE_VARARGS 扫描**（Pass 2 已标记）：属控制流变更，超出本轮约束。
3. **6 例预存失败**（3 ternary-in-assert-test + 3 assert-in-if-body 链式比较变体）：需
   识别顺序调整，非本轮范围。
4. **四条 fall-through 遍历器逻辑近似可统一**（Pass 2 已评估）：终止条件有细微差别，
   统一会改变边界行为，超出保守修复范围。
5. **`'TRUE' in cond_last.opname` / `'NOT_NONE' in cond_last.opname` 子串匹配统一替换为
   frozenset 常量**（本轮已标记）：与 Pass5/Pass6-BOOLOP 同型，需统一全量替换 17+ 处。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_detect_assert_boolop_chain` 内 op 判定逻辑前追加 [Pass7-ASSERT] 同型反模式标记段落）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/ASSERT/pass_07/fix_report.md`（本报告）
