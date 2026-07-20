# Round 05 — IF 区域修复报告

**修复范围**：IF 体内特殊语句类型与构造指令族（async 语义 / 推导式 / lambda 嵌套 / 链式比较段数扩展 / 多层属性链 / 特殊前导指令 / f-string 嵌套）
**修复轮次**：11 个确认错误（分 3 批提交）
**遗留**：test_adv03_nested_ternary_chain（链式比较中嵌套三元，19 vs 3，独立根本 bug，与本轮无关）
**回归**：if_region 418 passed / 1 failed（仅遗留 nested_ternary_chain）；control_flow_matrix 323 passed / 4 failed（全部预存，已 git stash 验证非本轮回归）；with_region+for_loop+while_loop 503 passed / 1 skipped

## 修复进度与提交分批

| 批次 | 提交 | 修复错误 | 状态 |
| --- | --- | --- | --- |
| batch 1 | `59bdbaf` | 1（import asname）、6（ann-assign）、11（augassign attr chain） | 已 push |
| batch 2 | `4c9939c` | 3（setcomp multi-for）、4（dictcomp walrus）、5（chaincmp 5 levels）、7（f-string format spec） | 已 push |
| batch 3 WIP | `d47f160` | 2（nested lambda） + 测试文件 | 已 push |
| batch 3 final | 本次 | 8（async with as）、9（async for）、10（await list elem） | 本次 push |

## 错误 01 — if 体内 `from m import x as y`，asname y 丢失变 `from m import x`

- 文件：test_adv05_import_asname.py（已通过）
- 根因：`_build_statement` 对 IMPORT_FROM 后接 STORE_NAME 的 asname 模式重建缺失，把 IMPORT_FROM 的参数 x 直接当作 STORE 目标，丢失真正的 STORE_NAME 目标 y。
- 修复（batch 1）：在 IMPORT_FROM 处理分支中新增 asname 检测 — IMPORT_FROM 之后紧接 STORE_NAME 时，把 STORE_NAME 的 argval 作为 asname 绑定目标，构建 `alias(name=x, asname=y)`。

## 错误 02 — if 体内嵌套 lambda，内层 lambda 走占位路径

- 文件：test_adv05_nested_lambda.py（已通过）
- 源码：`f = lambda x: (lambda y: x + y)`
- 根因：嵌套 lambda `lambda y: x + y` 捕获外层 x，字节码走 `MAKE_CELL + LOAD_CLOSURE + BUILD_TUPLE` 闭包路径。if body 区域分析对嵌套 lambda code object 的反编译走了「未知 lambda」占位路径 `lambda *args, **kwargs: None`，丢失原始形参 y 与函数体 `x + y`，且未处理闭包绑定。
- 修复（batch 3 WIP）：嵌套 lambda code object 走完整反编译路径，识别 MAKE_CELL/LOAD_CLOSURE 闭包绑定，重建内层 lambda 形参与函数体。

## 错误 03 — if 体内 setcomp 多 for 子句，第二 for 退化为元组解包

- 文件：test_adv05_setcomp_multi_for.py（已通过）
- 源码：`r = {x + y for x in a for y in b}`
- 根因：setcomp 多 for 子句的字节码含两个独立的 `GET_ITER + FOR_ITER` 块。if body 区域分析对 setcomp 第二个 `GET_ITER`（针对源 b）的识别失败，把它与前一个 `STORE_FAST x` 组合误判为 `UNPACK_SEQUENCE`（元组解包 `x, y`），导致第二个迭代源 b 丢失，整体退化为 `for x, y in a`。
- 修复（batch 2）：在 setcomp code object 反编译中识别多 for 子句的独立 GET_ITER+FOR_ITER 块序列，保留每个 for 子句的迭代源。

## 错误 04 — if 体内 dictcomp + walrus，walrus 丢失变裸调用

- 文件：test_adv05_dictcomp_walrus.py（已通过）
- 源码：`r = {k: (v := f(k)) for k in s}`
- 根因：dictcomp 中 walrus `(v := f(k))` 作 value，字节码在 `CALL` 后插入 `COPY + STORE_GLOBAL v`（walrus 副作用块）+ `MAP_ADD`。if body 区域分析对 dictcomp 内 walrus 求值块的识别失败，丢弃了 `COPY + STORE_GLOBAL v`，walrus 退化为普通调用 `f(k)`。
- 修复（batch 2）：在 dictcomp code object 反编译中识别 CALL 后的 COPY+STORE walrus 副作用块，重建 NamedExpr(value=Call(f, [k]), target=v)。

## 错误 05 — if 体内 5 段链式比较作赋值右值，幽灵表达式 + 占位符泄漏

- 文件：test_adv05_chaincmp_5_levels.py（已通过）
- 源码：`z = 0 < a < b < c < d`
- 根因：5 段链式比较 `0 < a < b < c < d` 作赋值右值时，字节码含 4 次 `COMPARE_OP + JUMP_IF_FALSE_OR_POP + 多个 COPY`。if body 区域分析对 5 段（含 4 个 comparator）链式比较的中间操作数（COPY 暂存）重建失败，把中间 COPY 暂存变量当作独立表达式语句输出（含内部占位符 `<copy_placeholder_2>`），同时正确生成了 `z = (0 < a < b < c < d)` 赋值。导致反编译结果出现「幽灵表达式」+ 内部占位符泄漏，语法错误无法编译。
- 修复（batch 2）：在链式比较 rhs 重建中，识别全部 comparator 的 COPY 暂存，把它们合并到主 Compare 节点，避免泄漏为独立语句。

## 错误 06 — if 体内注解赋值 `x: int = 1`，SETUP_ANNOTATIONS 前导丢失

- 文件：test_adv05_ann_assign.py（已通过）
- 根因：带注解的赋值 `x: int = 1` 字节码为 `SETUP_ANNOTATIONS + ... + STORE_NAME x + LOAD_NAME int + LOAD_NAME __annotations__ + LOAD_CONST 'x' + STORE_SUBSCR`。`SETUP_ANNOTATIONS` 是模块/函数级前导指令（在 if 之前）。if body 区域分析把注解的 `STORE_SUBSCR __annotations__['x']` 误判为独立赋值语句输出，且丢失了 `SETUP_ANNOTATIONS` 前导。
- 修复（batch 1）：识别 AnnAssign 模式（STORE_NAME x 后跟 LOAD int + STORE_SUBSCR __annotations__['x']），合并为 AnnAssign(target=x, annotation=int, value=1)，保留 SETUP_ANNOTATIONS 前导。

## 错误 07 — if 体内 f-string 嵌套格式说明符，被误判为 dict 字面量

- 文件：test_adv05_fstring_format_spec.py（已通过）
- 源码：`s = f'{x:{width}.2f}'`
- 根因：f-string `f'{x:{width}.2f}'` 含嵌套格式说明符 `{width}.2f`，字节码为 `LOAD x + LOAD width + FORMAT_VALUE 0 + LOAD_CONST '.2f' + BUILD_STRING 2 + FORMAT_VALUE 4 + STORE_NAME s`。if body 区域分析对 `FORMAT_VALUE + BUILD_STRING + FORMAT_VALUE` 嵌套 f-string 序列的识别失败，把它误判为 `BUILD_MAP`（dict 字面量 `{x: f'{width}.2f'}`）。
- 修复（batch 2）：识别 `FORMAT_VALUE + BUILD_STRING + FORMAT_VALUE` 三段序列为 f-string 嵌套格式说明符，重建 JoinedStr/FormattedValue 节点。

## 错误 08 — if 体内 async with `as x` 绑定丢失

- 文件：test_adv05_async_with.py（已通过，batch 3 final）
- 源码：
  ```python
  async def f():
      if c:
          async with g() as x:
              y = x
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令13操作码不匹配：`STORE_FAST vs POP_TOP`（原始 `BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND/YIELD + STORE_FAST x`；重编 `STORE_FAST x` 退化为 `POP_TOP`，as x 绑定丢失）
- 根因：`async with g() as x:` 字节码在 `BEFORE_ASYNC_WITH + await setup（GET_AWAITABLE/SEND/YIELD/RESUME）+ STORE_FAST x`（as x 绑定）。原 fallback target 检测在 `if region.is_async and not body_stmts:` 闸门后，但 body_stmts 已含 `y = x`，fallback 永不触发，导致 WithRegion.target=None，`STORE_FAST x` 退化为 `POP_TOP`。
- 修复（batch 3 final / Round5-08）：在 `_generate_with` 主循环处理 `with_blocks` 之前添加 early target detection — 仅受 `region.is_async and region.target is None` 限制，无条件扫描 with_blocks 的首条非平凡指令，若为 STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF，则设为 region.target 并同步更新 region.items 中 target=None 的项。
- 修改位置：`core/cfg/region_ast_generator.py` `_generate_with` 主循环之前（L11001-11036）

## 错误 09 — if 体内 async for 结构坍塌，迭代源退化为 None

- 文件：test_adv05_async_for.py（已通过，batch 3 final）
- 源码：
  ```python
  async def f():
      if c:
          async for x in g():
              y = x
  ```
- 失败信息（两阶段）：
  1. 初次：嵌套 code object 不匹配（指令1）：指令7操作码不匹配：`GET_AITER vs POP_TOP`
  2. 第一次修复后转为：指令数不匹配 21 vs 19，AST 含多余 `while True: pass` 且 `y = x` 丢失
- 根因（两阶段）：
  1. `_classify_loop_type` 在 `is_get_anext` 分支返回 `None` 给 `for_iter_setup`，导致 `iter_expr` 无法重建（GET_AITER 在前驱块，GET_ANEXT 在 header）
  2. async for 的 SEND/YIELD 子循环被识别为嵌套 LoopRegion，生成多余 `while True: pass`
- 修复（batch 3 final / Round5-09，两处修改）：
  1. `core/cfg/region_analyzer.py` `_classify_loop_type` 中 `is_get_anext` 分支：检测前驱块的 GET_AITER 作 for_iter_setup，BFS 搜索 SEND fall_through 和 END_ASYNC_FOR exit
  2. `core/cfg/region_ast_generator.py` `_loop_dispatch_block`：在 `natural_back_edge` 检查之后、block_role 分发之前，检测子 LoopRegion entry 仅含 SEND/YIELD/RESUME/JUMP_BACKWARD_NO_INTERRUPT 时跳过（标记为 generated_blocks + _generated_regions）
- 修改位置：
  - `core/cfg/region_analyzer.py` `_classify_loop_type`（L3096-3137）
  - `core/cfg/region_ast_generator.py` `_loop_dispatch_block`（L3235-3250）

## 错误 10 — if 体内 await 作列表元素，列表字面量与 await 全丢

- 文件：test_adv05_await_list_elem.py（已通过，batch 3 final）
- 源码：
  ```python
  async def f():
      if c:
          r = [await g(), await h()]
  ```
- 失败信息：嵌套 code object 不匹配（指令1）：指令数不匹配 26 vs 28（原始含 RETURN_GENERATOR/POP_TOP/RESUME + 完整 LOAD_GLOBAL g/PRECALL/CALL/GET_AWAITABLE/YIELD_VALUE ×2 + BUILD_LIST 2 + STORE_FAST r；重编多出 POP_TOP，列表字面量 BUILD_LIST 2 与 await 元素绑定全丢，await 退化为独立语句 `await g(); await h()`，赋值目标 r 变空列表 `[]`）
- 根因：`[await g(), await h()]` 列表字面量含两个 await 元素。CPython 把每个 await 展开为独立的 (setup_block, SEND/YIELD 自循环块) 对，最后 BUILD_LIST 块消费两个 await 的栈结果。if body 区域分析按块单独重建：每个 await setup 块的栈顶 Await 结果被作为独立 Expr 语句输出（值被 POP_TOP 丢弃），BUILD_LIST 块到达时栈空，列表字面量退化为空 `[]`。这是「跨块表达式」失效 — 单块内 ExpressionReconstructor 能识别 GET_AWAITABLE→Await，但跨块链（setup → SEND/YIELD loop → merge）未被识别为单一表达式。
- 字节码结构（5 块）：
  - @ 20: `LOAD_GLOBAL, PRECALL, CALL, GET_AWAITABLE, LOAD_CONST`（await g() setup）
  - @ 50: `SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT`（await g() yield loop，自循环）
  - @ 58: `LOAD_GLOBAL, PRECALL, CALL, GET_AWAITABLE, LOAD_CONST`（await h() setup）
  - @ 88: `SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT`（await h() yield loop，自循环）
  - @ 96: `BUILD_LIST 2, STORE_FAST r, LOAD_CONST None, RETURN_VALUE`（merge + assign）
- 修复（batch 3 final / Round5-10）：新增 `_try_generate_await_list_assign` 辅助方法，在 `_process_if_blocks` 主循环早期（_nested_if_skip 之后、child_expr_regions 之前）调用。
  - 模式识别：入口块含 GET_AWAITABLE 且末尾为 LOAD_CONST None → 找后继中仅由 SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT/NOP/CACHE 组成的 SEND/YIELD 自循环块 → 通过 SEND 的 argval 确定 fall-through 目标 → 若 fall-through 是 BUILD_LIST 块则终结，若是另一个含 GET_AWAITABLE 的 setup 块则继续链
  - 重建：收集整条链（所有 setup/send_loop 块的完整指令 + BUILD_LIST 块直到 BUILD_LIST 含 + 紧接的 STORE_*）作为单一指令序列，调用 `expr_reconstructor.reconstruct()` 一次重建。栈模拟依次压入 Await(Call(g)) → 保留 → 压入 Await(Call(h)) → 保留 → BUILD_LIST 2 弹出两个 Await 压入 List([Await(g), Await(h)]) → STORE_FAST r 弹出 List 创建 Assign(targets=[r], value=List([...]))
  - 标记：所有链块加入 generated_blocks / generated_offsets，主循环后续到达 @ 50/58/88/96 时直接跳过
- 修改位置：`core/cfg/region_ast_generator.py` 新增 `_try_generate_await_list_assign` 方法（L8096-8217）+ `_process_if_blocks` 调用点（L8253-8255）

## 错误 11 — if 体内 `a.b.c += 1`，中间属性 b 丢失

- 文件：test_adv05_augassign_attr_chain.py（已通过）
- 源码：`a.b.c += 1`
- 根因：`a.b.c += 1` 多层属性链 AugAssign 字节码为 `LOAD_NAME a + LOAD_ATTR b + COPY 1 + LOAD_ATTR c + LOAD_CONST 1 + BINARY_OP += + SWAP 2 + STORE_ATTR c`。if body 区域分析对多层 `LOAD_ATTR` 链的 AugAssign 目标重建失败，丢弃了中间 `LOAD_ATTR b`，把 `a.b.c` 截断为 `a.c`。
- 修复（batch 1）：在 AugAssign 目标重建中保留 COPY 之前的所有 LOAD_ATTR 链，构建完整 Attribute(Attribute(a, 'b'), 'c') 目标。

## 根因分类汇总

| 根因类别 | 涉及错误 | 修复批次 |
|----------|----------|----------|
| if 体内「async 语义」整体未重建 | 8, 9, 10 | batch 3 final |
| if 体内「推导式」 walrus 与多 for 子句未识别 | 3, 4 | batch 2 |
| if 体内「lambda code object」嵌套走占位路径 | 2 | batch 3 WIP |
| if 体内「5 段链式比较」占位符泄漏 | 5 | batch 2 |
| if 体内「特殊前导指令」未识别 | 1, 6 | batch 1 |
| if 体内「f-string 嵌套格式说明符」误判为 dict 字面量 | 7 | batch 2 |
| if 体内「多层属性访问链」被截断 | 11 | batch 1 |

## 修改文件清单

| 文件 | 修改内容 |
| --- | --- |
| `core/cfg/region_ast_generator.py` | batch 1：错误 1（IMPORT_FROM asname）、6（AnnAssign）、11（AugAssign 属性链）；batch 2：错误 3（setcomp multi-for）、4（dictcomp walrus）、5（chaincmp 5 levels）、7（f-string）；batch 3 final：错误 8（async with early target detection, L11001-11036）、9（async for SEND/YIELD 子循环跳过, L3235-3250）、10（`_try_generate_await_list_assign` 新方法, L8096-8217 + 调用点 L8253-8255） |
| `core/cfg/region_analyzer.py` | batch 3 final：错误 9（`_classify_loop_type` 中 `is_get_anext` 分支完善, L3096-3137） |

## 复现与验证命令

```bash
# 单个
python -m pytest tests/exhaustive/if_region/test_adv05_await_list_elem.py -v
python -m pytest tests/exhaustive/if_region/test_adv05_async_with.py -v
python -m pytest tests/exhaustive/if_region/test_adv05_async_for.py -v
# 全部 adv05
python -m pytest tests/exhaustive/if_region/test_adv05_*.py -q
# if_region 全量回归（除 nested_ternary_chain 遗留外 0 新增失败）
python -m pytest tests/exhaustive/if_region/
# control_flow_matrix 回归（≤4 预存失败）
python -m pytest tests/control_flow_matrix/
# with_region + for_loop + while_loop 回归（无新增失败）
python -m pytest tests/exhaustive/with_region/ tests/exhaustive/for_loop/ tests/exhaustive/while_loop/
```

## 最终汇总运行结果

```
if_region:                   418 passed, 1 failed (nested_ternary_chain 遗留)
control_flow_matrix:         323 passed, 4 failed (全部预存，git stash 验证非本轮回归), 11 skipped
with_region+for_loop+while_loop: 503 passed, 1 skipped
adv05 async trio (8,9,10):   3 passed
```

11 个确认错误全部修复，0 新增回归。
