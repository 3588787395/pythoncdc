# IF 区域 Round 8 修复报告

- 修复日期：2026-07-18
- 修复工程师：Repair Engineer (Round 8)
- 测试发现文档：`test_findings.md`（同目录）
- 确认错误数：**13**，已修复：**13/13**
- 修复文件：`core/cfg/region_ast_generator.py`、`core/cfg/ast_generator_v2.py`、`core/cfg/code_generator.py`
- 约束遵守：未在 `code_generator.py` 内做后处理补丁；所有修复落在 AST 重建源头；无跨区域特殊分支；无硬编码深度限制

## 区域归约算法四原则遵守

1. **自底向上归约**：每个修复在基本块语句生成阶段（`_generate_block_statements` / `_build_store_statement` / `_build_statement` / `_build_subscript_assign` / `_build_attr_assign` / `_build_chained_compare_from_region_data` / `_generate_assert`）按模式自底向上识别，先识别内层表达式再归约为语句。
2. **每个块唯一归属**：所有新增/扩展的识别逻辑命中后即 `return stmts` 并标记 `self.generated_blocks.add(block)`，不重复消费同一块。
3. **嵌套即抽象节点**：混合目标链 / tuple unpack / walrus 副作用均归约为单一 `Assign` / `AnnAssign` / `AugAssign` / `Assert` 节点，嵌套表达式（方法调用、下标、属性、NamedExpr）作为子树挂载，不拆分为多语句。
4. **父区域引用子区域入口**：IF 区域通过子块入口生成 body，修复点全部在 body 块的语句归约层，不影响 IF 区域对子块入口的引用关系。

## 批次与提交记录

| 批次 | 错误 | 提交 | 摘要 |
|------|------|------|------|
| Batch 1 | err1, err2 | `b0ee828` | 注解（复杂类型 / 无值）—— 泛化 AnnAssign 识别 |
| Batch 2 | err3 | `95005d8` | 链式比较中段方法调用 —— 重建 LOAD_METHOD+CALL 操作数 |
| Batch 3 | err4, err5 | `e36d663` | dict 解包 —— 处理 DICT_MERGE 嵌套 + DICT_UPDATE |
| Batch 4 | err6, err8, err13 | `7763cbd` | walrus（lambda 默认 / 嵌套下标 / f-string FORMAT_VALUE） |
| Batch 5 | err7, err12 | `69c87b5` | 多目标 subscr/attr 链 + assert 消息 walrus |
| Batch 6 | err9 | `bda6135` | subscr augassign + 方法调用右值 |
| Batch 7 | err10, err11 | `51bb8d2` | SWAP tuple unpack 混合 attr/subscr 目标 |

## 逐错误修复详情

### 错误 01 — 复杂类型注解 `x: List[Dict[str, int]] = {}` 退化为 `x = {}` + `__annotations__['x'] = ...`
- 根因：if body 的语句生成把 `AnnAssign` 拆成 `Assign` + `__annotations__['x'] = annotation`，重编丢失 `SETUP_ANNOTATIONS`。R5 仅覆盖简单 `x: int = 1`，未覆盖含 `BINARY_SUBSCR` 嵌套下标的复杂注解。
- 修复：在 `_build_statement` / `_build_store_statement` 路径泛化 AnnAssign 识别，识别 `STORE_SUBSCR __annotations__` 模式后回溯构造 `AnnAssign` 节点（保留 `target` / `annotation` / `value`），覆盖含 `BINARY_SUBSCR` 的复杂注解类型表达式。

### 错误 02 — 无值注解 `x: int` 退化为 `__annotations__['x'] = int`
- 根因：与 err1 同源，R5 未覆盖无初值的纯声明形式 `x: int`（无 `STORE_NAME x`）。
- 修复：err1 的 AnnAssign 识别泛化同时覆盖无 value 分支（`value=None`）。

### 错误 03 — 链式比较中段方法调用 `a.f() < b.g() < c.h()` 退化为语法错误
- 根因：`_build_chained_compare_from_region_data` 假设所有 comparator 都是单条 `LOAD_*`，对 `LOAD_METHOD` 返回占位符 `<LOAD_METHOD>`，且 `region.chained_comparator_instrs` 只保存了 `LOAD_METHOD` 一条指令，未捕获后续 `PRECALL/CALL`。
- 修复：重建 comparator 操作数时识别 `LOAD_METHOD + PRECALL + CALL` 序列，将其归约为完整 `Call(Attribute(...))` 表达式，替代单条 `LOAD_*` 假设。

### 错误 04 — 调用双 dict 解包 `f(**a, **b)` 丢失一个 `DICT_MERGE`
- 根因：`CALL_FUNCTION_EX` 路径重建 kwargs 时只保留最后一个 `DICT_MERGE` 对应的 `b`，前面的 `**a` 被丢弃并额外生成空 tuple `*()`。
- 修复：在 `expr_reconstructor` / `ast_generator_v2` 的 kwargs 重建中处理 `DICT_MERGE` 链式嵌套，保留全部 `**dict` 解包项。

### 错误 05 — dict 字面量双解包 `r = {**a, **b, "k": v}` 丢失解包项
- 根因：`BUILD_MAP` 字面量处理只识别「LOAD key; LOAD value; BUILD_MAP N」固定对，未识别 `DICT_UPDATE` 链式合并，`**a`/`**b` 丢失。
- 修复：扩展 `_flatten_dict_merge_to_dict_items` 处理 `BUILD_MAP; DICT_UPDATE; DICT_UPDATE` 链式合并，生成含 `Starred` key 的 dict 项；`code_generator.py` 的 Dict 渲染支持 `Starred` key 输出 `**expr`。

### 错误 06 — lambda 默认参数 walrus `lambda x=(n := 1): x` 退化为独立赋值
- 根因：`_build_store_statement` 遇 `COPY + STORE_NAME n`（无后续 `_LITERAL_BUILD_OPS`）触发 walrus 独立赋值分支，把 walrus 提前为 `n = 1`，从 lambda 默认值 tuple 移除 walrus。
- 修复：扩展 walrus 副作用识别的「后续字面量构造」触发条件，识别 `BUILD_TUPLE + MAKE_FUNCTION`（lambda 默认值）路径，将 walrus 作为 NamedExpr 保留在默认值表达式中。

### 错误 07 — 多目标赋值链含下标和属性 `a = b[k] = c.d = e` 错位
- 根因：多目标链检测只识别连续相邻的 `STORE_NAME`，遇 `STORE_SUBSCR/STORE_ATTR` 中断，链被拆成 3 个独立语句。
- 修复：新增块级预扫描 `_mixed_chain_result`，检测混合 `STORE_NAME/STORE_SUBSCR/STORE_ATTR` 链。每个非末目标前有 `COPY 1`（值复制），末目标复用栈上剩余值（无 `COPY 1`，匹配 CPython codegen）。构建单一 `Assign` 节点，targets 为 `[Name, Subscript, Attribute]`。

### 错误 08 — 嵌套 walrus 下标 `r = d[a[(n := f())]]` 丢失整个赋值
- 根因：walrus 识别（line 16567-16713）触发条件仅匹配 `_LITERAL_BUILD_OPS`，嵌套下标 `BINARY_SUBSCR` 不在列表，walrus 被错误提取为独立 `n = f()`，丢失 `d[...]`/`a[...]`/`r = ...`。
- 修复：扩展 walrus 副作用识别的「后续构造」触发条件，加入 `BINARY_SUBSCR`（嵌套下标路径），将 walrus 作为 NamedExpr 保留在下标表达式中。

### 错误 09 — subscr augassign + 方法调用右值 `a[b] += f(c, d)` 方法调用丢失
- 根因：`_build_subscript_assign` 的 AugAssign 右值提取只反向收集 `LOAD_*`，遇 `PUSH_NULL/PRECALL/CALL` 即中断，`f(c, d)` 调用退化为常量 0。
- 修复：右值提取改为定位目标 `BINARY_SUBSCR`（COPY-2 复制模式之后的那条），取其与 `BINARY_OP` 之间的全部指令作为右值（处理方法调用 / 下标），简单右值回退到原 `LOAD_*` 反向收集。

### 错误 10 — tuple unpack 含属性目标 `a.b, c.d = e, f` 错位
- 根因：SWAP-based tuple unpack 重建只识别纯 `STORE_NAME` 链，遇 `STORE_ATTR` 设 `_swap_valid=False`，退化为 `a.b = f; c.d = None`。
- 修复：将「N 个连续 STORE_*」检查替换为统一 store 序列解析器，遍历恰好 N 个目标（N 来自 SWAP arg），每个目标可为 name(`STORE_*`) / attr(`LOAD obj, STORE_ATTR`) / subscr(`LOAD obj, LOAD key, STORE_SUBSCR`)。纯名字路径守卫（N 个 store 后下一条不能仍是 `STORE_*`）通过 `_all_simple_names` 标志保留。

### 错误 11 — tuple unpack 含下标目标 `a[0], b = c, d` 丢失赋值
- 根因：与 err10 同源，`STORE_SUBSCR` 中断 unpack 重建，`STORE_NAME b` 被丢失。
- 修复：err10 的统一 store 序列解析器同时覆盖 subscr 目标（用 `expr_reconstructor` 处理 `LOAD obj + LOAD key` 栈，取栈顶两项作 `value`/`slice`）。

### 错误 12 — assert 带 walrus 消息 `assert x, (n := f())` 退化为 dict 字面量字符串
- 根因：`_generate_assert` 重建 assert 消息时跳过了所有 `PRECALL/CALL` 和 `COPY`，walrus 的 `COPY+STORE` 模式无法被 `expr_reconstructor` 识别为 NamedExpr，内部 AST dict 被 `str()` 输出为占位字面量。
- 修复：统一 assert 消息重建为始终使用反向 `RAISE_VARARGS` 边界扫描，从 `base_skip` 移除 `COPY`（保留 walrus 的 `COPY+STORE` 模式供 `expr_reconstructor` 识别），`SWAP` 仍在 `base_skip`。

### 错误 13 — f-string 含 walrus `s = f"{(n := x)}"` 退化为独立赋值
- 根因：与 err06/err08 同源，walrus 识别触发条件 `_LITERAL_BUILD_OPS` 未包含 `FORMAT_VALUE`（f-string 格式化指令），walrus 被提取为独立 `n = x`，`FORMAT_VALUE + STORE_NAME s` 整段丢弃。
- 修复：扩展 walrus 副作用识别的「后续构造」触发条件，加入 `FORMAT_VALUE`，将 walrus 作为 NamedExpr 保留在 f-string 格式值中。

## 最终回归结果

### R8 全部 13 个错误（逐个验证）
```
13 passed in 1.03s
```
全部通过。

### IF 区域全量回归
```
1 failed, 513 passed, 2 skipped in 4.34s
```
- 唯一失败：`test_adv03_nested_ternary_chain`（legacy，R8 开始前就已失败，不在本轮 13 个错误范围内）
- R8 基线（修复前）：480 passed / 1 legacy failed / 2 skipped
- R8 修复后：513 passed / 1 legacy failed / 2 skipped（新增 33 个 adv08 测试，33-13=20 通过 + 13 修复后通过）

### 跨区域验证（control_flow_matrix）
```
4 failed, 323 passed, 11 skipped in 2.17s
```
- 与 R8 基线完全一致（323 passed / 4 failed），未引入任何跨区域回退。
- 4 个失败均为既有问题（`TestL12WhileBreakContinue` / `TestN11TryWhileContinue` / `TestCF2WhileIfBreakContinue` 的 Break/Continue 结构识别 + `TestXP04BoolOpInIf` 的 BoolOp 节点），与本轮 IF 区域修复无关。

## 修复策略归纳

本轮 13 个错误的根因集中在三类 AST 重建源问题，全部在归约源头修复：

1. **walrus 副作用触发条件过严**（err6, err8, err12, err13）：原 `_LITERAL_BUILD_OPS` 白名单仅含 `BUILD_MAP/SET/LIST/TUPLE/CONST_KEY_MAP`，未覆盖 `BUILD_TUPLE+MAKE_FUNCTION`（lambda 默认）、`BINARY_SUBSCR`（嵌套下标）、`FORMAT_VALUE`（f-string）、assert 消息路径的 `COPY` 保留。修复方式是泛化触发条件，不针对单一位置特殊处理。

2. **多目标 / tuple unpack 目标识别仅支持连续 STORE_NAME**（err7, err10, err11）：原 chain-assign / SWAP-unpack 检测遇 `STORE_SUBSCR/STORE_ATTR` 即中断。修复方式是引入统一的 store 序列解析器，按 SWAP arg / COPY 1 模式权威地确定目标数 N，逐目标解析 name/attr/subscr。

3. **操作数指令集对方法调用 / 复杂右值不支持**（err3, err9）：chained-compare comparator 和 augassign 右值假设单条 `LOAD_*`，遇 `LOAD_METHOD+CALL` / `PUSH_NULL+PRECALL+CALL` 序列中断。修复方式是扩展指令收集范围至完整调用序列。

所有修复均泛化为模式识别，不针对特定测试用例硬编码，不依赖跨区域信息，无硬编码深度限制。
