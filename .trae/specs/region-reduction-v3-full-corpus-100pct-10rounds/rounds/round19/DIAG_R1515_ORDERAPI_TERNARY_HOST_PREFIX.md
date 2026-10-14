# DIAG R15-15（T19-4）order_api 根因：三元的条件测试与「未闭合调用」融在同一块，识别端照建 TernaryRegion

目标：`IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` 35/37，失败单元
`<module>.future_order`（内容差 −27）、`<module>.option_order`（−39）。两单元同形，
且都是所在文件的唯一失败单元 ⇒ 修好即两个整文件翻绿之一档。

## 1. 实测：识别端给出的区域（只读普查 `D:/Temp/r150/memb_census.py`，`future_order`，块区间 380..560）

```
@414 len=17 tail=POP_JUMP_FORWARD_IF_FALSE   block_to_region=IfRegion@340
     同时属于 TernaryRegion@414[ENTRY,COND] 与 IfRegion@340[else_blocks,elif_body]
@552 len=2  JUMP_FORWARD   ∈ TernaryRegion@414[blocks-only]
@556 len=1  LOAD_CONST     ∈ TernaryRegion@414[blocks-only]
@558 len=9  POP_JUMP_FORWARD_IF_FALSE ∈ TernaryRegion@558[ENTRY,COND] 且 = TernaryRegion@414[MERGE]
orphan blocks: 0
```

该 17 指令块的原始指令（`dis`，数字为源文件行）：

```
@414 LOAD_GLOBAL NULL+strategy_log                                     458
@426 LOAD_ATTR   info
@436 LOAD_CONST  '生成订单，订单号：{order_id}…数量：{share}手'          459
@438 LOAD_METHOD  format
@460/@462  LOAD_FAST order_ ; LOAD_ATTR order_id                        460
@472/@474  LOAD_FAST order_ ; LOAD_ATTR symbol                          461
@484/@486/@496/@506 LOAD_FAST order_ ; LOAD_ATTR entrust_direction ;
                     LOAD_ATTR value ; LOAD_METHOD upper                462
@528/@532  PRECALL ; CALL            ← 到这里仍是**条件自身**的求值（.upper()）
@542/@544  LOAD_CONST 'BUY' ; COMPARE_OP ==
@550 POP_JUMP_FORWARD_IF_FALSE -> @556   ← 三元条件测试在此结束
@552 LOAD_CONST '买入' ; @554 JUMP_FORWARD -> @558 ; @556 LOAD_CONST '卖出'
@558 …（同一语句里的第二个三元，作下一个关键字实参）…                    463
```

⇒ 源形状是**一条**语句
`strategy_log.info('…'.format(order_id=…, symbol=…, side=('买入' if … else '卖出'), …))`：
三元的条件测试与宿主 `.format(...)` / `info(...)` 的求值前缀被 CPython 融在同一个基本块内，
且**跳转时栈上仍有未消费的下层元素**（宿主调用的接收者与已成型实参）。
识别端把整块登记成 `TernaryRegion` 的 entry/condition_block
（`region_analyzer.py:26004-26016`，`entry=block, condition_block=block`），
发射端于是只发出裸三元，宿主调用整条语句（连同其后第二个三元实参）消失。

## 2. 落点判据其实已经存在，只是被一条 VALUE 逃逸放行

`region_ast_generator.py:41700` `_ternary_nested_in_container_construction(cond_block)`
—— 前向模拟条件块内、块末条件跳转之前的值栈，逐格标记来源；判据落在**栈底元素性质**：

```
if len(syms) <= 1: return False
return syms[0] == 'CONTAINER'          # :41748-41750
```

其 docstring 明确写了第三条逃逸：「栈深 > 1 但栈底是其它表达式：那是若干彼此独立的表达式
被顺序求值……不构成『未闭合的构造』，按既有行为处理」。**本缺陷正落在这条逃逸上**：
@550 处栈底是 `strategy_log`（其 `.format` 的 PRECALL/CALL 尚未执行 / `info` 的 CALL 更远未执行），
是**未闭合调用**的接收者，而不是「彼此独立的表达式」——独立求值完的值不会滞留在栈上
（要嘛被 STORE 消费、要嘛被同一条语句的后续操作数消费）。

同一判据族的另一处已用「栈效应」定性同类问题：`_generate_ternary` 的 `[R102 fix]`
（`:42151-42164`，条件起点回扫的栈效应表）与 `_instruction_stack_effect` /
`_ternary_prefix_stack_effect`（`:49058`）。⇒ 复用该表，勿新建第二真相源。

归约路径也是现成的：`_generate_container_construction_region`（`:41752-41790`）把区域全部块
的指令按 offset 排序交 `expr_reconstructor.reconstruct` 归约为**一个**表达式并整块标记已生成；
它对「容器」并无特化，缺的只是**指令跨度**：本形的宿主调用在本区域块之外才闭合
（@558 起是同一语句的第二个三元，`info(...)` 的 CALL 更在其后），而 `region.blocks` 只到 @558。

## 3. 已实测排除的两条修法（勿重复）

- 把 `_EXPR_REGION_TYPES`（`:314`）去掉 `TernaryRegion` ⇒ 产物**逐字节不变**（该常量不参与本路径分派）。
- 旁路 `_process_if_blocks:25422` 的 `child_expr_regions` 分派 ⇒ 三元整个消失而宿主调用**并未回来**
  （父 IfRegion 的臂路径不会把该块当普通语句重建）。顺带证实「逻辑死支路的编辑」也会改产物
  （35/37→34/37），已登记 REGISTER §9。

## 4. 复现电池（本轮新建，已在 landed 字节上复跑确认）

`repro_orderapi/run_orderapi.py`（判决只喂 `pycdc.py --region` 产物 + `scripts/pyc_verify.py single`）：

```
o1_ternary_kwarg_in_format    status=failure   ← 宿主语句被折成 return（实参三元留下）
o2_plain_kwarg_no_ternary     status=success   ← GREEN 对照（关键字实参不含三元）
o3_ternary_then_use           status=success   ← GREEN 对照（三元先赋值再作实参）
o4_ternary_positional         status=failure   ← 位置实参三元，同族
o5_two_ternary_kwargs         status=failure   ← 只剩两个裸三元，宿主调用消失（与 order_api 同形）
GREEN=2 RED=3 / 5
```

o5 是与整文件缺陷同形的忠实复现；o1/o4 是同判据下的相邻形态（宿主调用被误折成 `return`）。

## 5. 可施工判据（一句话）与验收

**判据**：条件块末为条件跳转，且前向模拟值栈在该跳转处的**残留深度 > 1 且栈底元素属于一个
尚未被 PRECALL/CALL（或 STORE/POP_TOP）消费的构造**（容器开器 *或* 调用前缀：
`LOAD_GLOBAL/PUSH_NULL`、`LOAD_METHOD`、`LOAD_ATTR` 链的接收者）⇒ 该跳转不是语句级分派，
三元是**嵌套表达式**，不得作为顶层 `TernaryRegion` 独立归约；应把跨度扩到「栈平衡回到 0」
的那条语句（含其后的兄弟三元块），整体交 `reconstruct` 归约为一个表达式（`Expr` 或 `Return`
按原终结指令决定）。
**只读判据**：栈效应表、块内指令、跳转目标；不读名字/常量/绝对偏移/函数名。

**验收（顺序不可颠倒）**：
1. 电池 `run_orderapi.py` ⇒ o1/o4/o5 全绿且 o2/o3 保持绿（GREEN=5 RED=0）；
2. `order_api.pyc` 35/37 → **37/37**（`pyc_verify single`）；
3. 面板（既有 16 个具名相关文件）零回退；
4. 全 402 门链 label 19 vs 18（单元数不得下降），`quotation.pyc` 153/153，`pytest` 无新增失败。
任一档不过 ⇒ 逐字节回退并在 REGISTER 登记负极性。
