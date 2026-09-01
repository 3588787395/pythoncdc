# Pass 9 ASSERT 修复报告

## 修复内容

### Fix 1: 同步 `_identify_assert_regions` docstring Step 4 / Step 5，补记可达性遍历与 LOAD_ASSERTION_ERROR 主路径

**问题位置**：`/workspace/core/cfg/region_analyzer.py:9371`（`_identify_assert_regions` docstring §1 归约过程 Step 4 + Step 5）

**问题根因**（与 Pass9-IF / Pass9-MATCH 同型——docstring 与实际控制流不同步）：

`_identify_assert_regions` docstring §1 归约过程 Step 4 原文：
```
Step 4: 检查任一非自身条件后继块是否包含 LOAD_ASSERTION_ERROR 指令；
        若无则跳过（非 assert 模式，可与 IfRegion 区分）。
```

Step 5 原文：
```
Step 5: 在所有非自身后继块中按 start_offset 升序查找包含 RAISE_VARARGS
        的块作为 message_block（错误抛出块，可能为 None）。
```

与实际控制流存在两处口径差异：

(a) **Step 4 实际使用可达性遍历**：表述为「检查任一非自身条件后继块是否包含
LOAD_ASSERTION_ERROR 指令」，但实际代码（grep `_reach_assertion_error_block(succ)`
在本文件仅 1 处命中，L9489，[Round4-12] 修复）使用 `_reach_assertion_error_block`
做**可达性遍历**——链式比较 assert (`assert 0 < a < 10`) 的第一段 COMPARE_OP 块的
两个后继为「继续链」与「跳到 POP_TOP 中转块」，后者经单后继 fall-through 才到达
LOAD_ASSERTION_ERROR 块；直接后继只看一层会漏识别。即 Step 4 实际判据是
「后继可达 LOAD_ASSERTION_ERROR 块」而非「后继本身含 LOAD_ASSERTION_ERROR 指令」。

(b) **Step 5 实际主路径查找 LOAD_ASSERTION_ERROR 块**：表述为「查找包含
RAISE_VARARGS 的块作为 message_block」，但实际代码（grep
`mb = self._find_assertion_error_block(succ)` 在本文件仅 1 处命中，L9511）
主路径使用 `_find_assertion_error_block` 查找 **LOAD_ASSERTION_ERROR 块**
（[R8 fix]，注释说明对 ternary/complex message 场景 `assert x, (a if c else b)`
LOAD_ASSERTION_ERROR 块是 TernaryRegion 入口），RAISE_VARARGS walk
(`_reach_raise_varargs_block`) 仅作 [Pass5-ASSERT] 已标记的 Fallback 兜底路径。
即 Step 5 实际主路径查找的是 LOAD_ASSERTION_ERROR 块而非 RAISE_VARARGS 块，
原表述未提及主路径 / Fallback 二段式结构与 [R8 fix] / [Round4-12] 修复。

原表述可能误导读者认为 Step 4 是直接指令检查、Step 5 是直接 RAISE_VARARGS 查找。

**修复策略**（与 Pass9-IF / Pass9-MATCH 同型——仅 docstring 文本同步，不改控制流）：

在 docstring §1 归约过程 Step 7 之后追加 `[Pass9-ASSERT]` 段落，补记：
1. (a) Step 4 实际使用 `_reach_assertion_error_block` 可达性遍历（[Round4-12] 修复）
2. (b) Step 5 实际主路径使用 `_find_assertion_error_block` 查找 LOAD_ASSERTION_ERROR 块
   （[R8 fix]），RAISE_VARARGS walk 仅作 [Pass5-ASSERT] 已标记 Fallback
3. 采用 grep 验证方式引用行号（避免递归漂移，与 Pass8-LOOP / Pass9-LOOP 同型）
4. 不重写「Step 4 / Step 5」列表（与 Pass9-IF / Pass9-MATCH 同型保守策略一致）

控制流不变，仅 docstring 文本同步。

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
| 控制流改变 | 未改变（仅 docstring 文本同步） |
| 测试文件修改 | 未修改任何测试文件 |
| docstring 与实际控制流不同步（与 Pass9-IF / Pass9-MATCH 同型） | **已同步**（补记 Step 4 可达性遍历 + Step 5 LOAD_ASSERTION_ERROR 主路径） |

## 未完成项

1. **`_reach_raise_varargs_block` Fallback 补丁消除**（Pass 5 已标记、Pass6-ASSERT 同步行号引用）：
   控制流变更，需统一 `_find_assertion_error_block` / `_reach_raise_varargs_block`
   为单一查询路径后删除。本轮 [Pass9-ASSERT] 段落已补记此二段式结构。
2. **`_build_assert_message` 非 build_string 分支未同步主路径 [Round8-12] walrus 反向
   RAISE_VARARGS 扫描**（Pass 2 已标记）：属控制流变更，超出本轮约束。
3. **6 例预存失败**（3 ternary-in-assert-test + 3 assert-in-if-body 链式比较变体）：需
   识别顺序调整，非本轮范围。
4. **四条 fall-through 遍历器逻辑近似可统一**（Pass 2 已评估）：终止条件有细微差别，
   统一会改变边界行为，超出保守修复范围。
5. **`'TRUE' in cond_last.opname` / `'NOT_NONE' in cond_last.opname` / `'NOT_NONE' in
   last_instr.opname` 子串匹配统一替换为 frozenset 常量**（Pass7-ASSERT + Pass8-ASSERT
   已标记两处）：与 Pass5/Pass6-BOOLOP 同型，需统一全量替换 17+ 处。
6. **Step 4 / Step 5 表述与实际控制流差异**：本轮已在 §1 归约过程 Step 7 后追加
   [Pass9-ASSERT] 段落补记。后续 Pass 若实施「彻底重写 Step 4 / Step 5 列表」可一并同步。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_assert_regions` docstring §1 归约过程 Step 7 后追加 [Pass9-ASSERT] 段落，补记 Step 4 可达性遍历 + Step 5 LOAD_ASSERTION_ERROR 主路径）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/ASSERT/pass_09/fix_report.md`（本报告）
