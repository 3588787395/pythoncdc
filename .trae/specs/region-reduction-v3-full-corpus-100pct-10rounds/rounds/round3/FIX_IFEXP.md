# FIX_IFEXP — 三元/IfExp 族：实参表内并列三元的区域归属（B114 登记，**未落地**）

轮次：Round 3 / 单票（ternary-IfExp 族，目标 `order_api.pyc` 35/37 → 37/37）
执行人：round-3 IfExp 修复 agent
判定尺：`scripts/pyc_verify.py`（未修改、未替代、未写替代 checker）
**声明：本轮「仅归档 spec 未落地」** —— 生产代码零改动，两个被试文件已按字节精确回退到认证状态。

---

## 0. 回退完整性（实测）

| 文件 | 认证值 | 回退后实测 |
|---|---|---|
| `core/cfg/region_analyzer.py` | 31978 行、全 CRLF、单前导 BOM | 31978 行 / CRLF 31978 / bare LF 0 / BOM True |
| `core/cfg/region_ast_generator.py` | 58576 行、全 CRLF、单前导 BOM | 58576 行 / CRLF 58576 / bare LF 0 / BOM True |
| `grep -c "R3-IFEXP"` 两文件 | 0 | **0 / 0** |
| `grep -c "_mb_owned_by_sibling_ternary\|_TERNARY_TEST_CONSUMER_OPS\|_sibling_ternary_owns_merge_block"` | 0 | **0** |
| `python -X utf8 -m compileall -q core` | ok | **ok（rc=0）** |

> 事实校正（不改 REVIEW.md，仅在此登记）：任务书写 `region_analyzer.py` 无 BOM，实测**有**单前导
> BOM（与 `region_ast_generator.py` 同）；本轮所有编辑均以「保留原前导 BOM + 全 CRLF」方式做字节级替换。

回退后基线复验（与认证值逐位相同）：

```
batch --index test_repros/round3/r3_probe_index.json  -> units 97/118, files 54 = 33 success / 21 failure
single …/fly_api/order_api.pyc                        -> status=failure units=35/37
single …/strategy/wizard_quant_api.pyc                -> status=failure units=55/58
```

---

## 1. 合成孪生（evidence-gathering，实测）

三个变体（`py_compile` → `.pyc` → `pycdc.py -o …OK.py` → `single`）：

| 标本 | 源码形状 | 单元数 | 判据 |
|---|---|---|---|
| `t1_inline_arg_ternary` | `if not is_trade(): LOG.info('{a}{b}'.format(side='BUY' if …else 'SELL', sym=o.symbol))` —— **实参表内 1 个三元** | 3/3 | **success** |
| `t5_two_kw_before` | 同上但三元前后各 1 个普通实参 —— 仍 **1 个三元** | 3/3 | **success** |
| `t4_two_arg_ternary` | `LOG.info('{sym} {side}{oper} {n}'.format(sym=…, side=<三元1>, oper=<三元2>, n=…))` —— **实参表内 2 个并列三元** | 2/3 | **failure** |
| `t3_toplevel_inline` | 函数体顶层（非臂内）单三元实参 + 尾 return | 1/2 | failure（**另一形状**，见 §5） |

`t4` 是 `order_api` 的合成孪生。`_r2diag diff` 首分歧同签名（ORIG↔PROD）：

```
t4  f              orig 48 | prod 24 insns   delete orig[9:15]  off38
future_order       orig 115 | prod 88 insns   delete orig[72:80] off414
```

两处被删的都是**调用前导**（`LOAD_GLOBAL LOG/strategy_log → LOAD_ATTR/LOAD_METHOD info →
LOAD_CONST 格式串 → LOAD_METHOD format → 首个普通实参装载`），PROD 从 `POP_JUMP_FORWARD_IF_TRUE`
（`not is_trade()` 的臂跳，两侧目标内容同为 `LOAD_FAST,LOAD_ATTR,RETURN_VALUE` ⇒ B109 边已正确）
之后直接落入第一个三元的测试。产物文本同为 `elif not is_trade():` 臂内只剩裸三元。
⇒ **`future_order` 与合成孪生是同一机制，不是两条。**

`t1`/`t5` 与 `t4` 的唯一差别是**实参表内三元的个数**（1 → 2），且 `r3_a03`（先赋值后 format）
今日 MATCH ⇒ 判别维度 = 「同一外层表达式内并列 ≥2 个 IfExp」，与臂/链/深度无关。

## 2. B114 登记（误分类本体）

**B114 — 同一外层表达式（调用实参表 / 容器字面量 / f-string 字段）内并列 ≥2 个 IfExp 时，
前序 IfExp 的 `merge_block` 与后继 IfExp 的 `condition_block` 是同一个基本块，识别端把该块
同时收进前序区域的 `blocks` 并读作前序三元值的「条件测试消费者」（`merge_context='compare'` +
`value_target='__compare_target__'`），于是外层调用语句失去值消费点，整条
`strategy_log.info(fmt.format(…, side=<IfExp>, oper=<IfExp>, …))` 退化为裸 IfExp 表达式语句**

区域森林实测（`t4` 的 `f`，`RegionAnalyzer.analyze()` 直读；识别端为 **CFG 逆序块扫描**
`for block in list(reversed(self.cfg.get_blocks_in_order()))`，`region_analyzer.py:25968`，
故后继三元先建区、先登记 `block_to_region`）：

```
修复前  TernaryRegion entry=B38  COND=B38  TRUE=B166 FALSE=B170 MERGE=B172
                              CTX='compare'  TARGET='__compare_target__'  CONTAINER='call'
                              blocks=[B38,B166,B170,B172]
        TernaryRegion entry=B172 COND=B172 TRUE=B230 FALSE=B234 MERGE=B236 CONTAINER='call'
                              blocks=[B172,B230,B234,B236]
        ⇒ B172 同时属于两个 TernaryRegion（违反 §1.2 原则2 每块唯一归属）
```

触发站点（精确）：`_detect_ternary_pattern` 的 merge_block 消费者扫描
（`region_analyzer.py:24785` 起）里，`elif instr.opname in ('LOAD_ATTR','LOAD_METHOD')` 臂
（`region_analyzer.py:24937`，`_mb_has_cond_jump` 只看 `_mb_prefix` 是否含条件跳转）先于
`COMPARE_OP` 臂命中 —— B172 以 `LOAD_FAST o; LOAD_ATTR fd; …` 开头，**该 LOAD_ATTR 是兄弟
测试自己的操作数装载，与本三元的值无关**。既有 `_net_stack` 栈形守卫只保护 `COMPARE_OP` 臂
（`region_analyzer.py:24972` 的 `net_stack==2 ⇒ compare_uses_ternary=False`，且其注释已点名
「merge_block 中的 COMPARE_OP 属于第二个三元」这一族），`LOAD_ATTR/LOAD_METHOD` 臂无对应保护。

违反条款：§1.2 **原则2 每块唯一归属**（B172 双认领）+ **原则4 入口引用语义**（前序区域冒充
消费端，父调用区域无从经入口引用）+ §1.5 **C1 局部消费**（消费了落在兄弟区域内的指令）。
非深度形：`t1`/`t5`（同深度）MATCH、`t4` MISMATCH，唯一维度是并列三元个数。

## 3. 两条语料形状是否同一机制：**否**（不强行合并）

| | `order_api` `future_order`/`option_order`（B114） | `wizard_quant_api` `get_DMI.calculate_di.<genexpr>` ×2（B113） |
|---|---|---|
| 丢失内容 | **调用前导 + KW_NAMES + 外层 CALL**（整条语句），三元自身完整 | 三元**测试的首合取** `A > 0` 及其 `POP_JUMP_IF_FALSE → 202` 共享 else 边 |
| ORIG 首分歧 | `delete` 调用前导（off414 / 合成孪生 off38），无 `replace` 三元测试 | off56 `LOAD_CONST 0` vs `LOAD_DEREF`（比较操作数装载整体缺失） |
| 单元增减 | 115→88（−27）/ 94→55 | 64→50（−14，与 REVIEW §4.2 一致） |
| 归属判据 | 前序三元 merge = 后继三元 cond（**同层兄弟**衔接） | `<genexpr>` 嵌套 code object 森林根上的测试子链认领 |
| 嵌套 code object | 无关（普通函数体臂内） | 决定性（`r3_c07` 把同一表达式移出推导即 MATCH） |

⇒ 两个机制**不同**。本轮只针对 B114；**B113 零改动、零翻转**（`wizard_quant_api` 55/58 未变，
`r3_c01/c02/c03/c04/c05/c09/c10/c11` 八条红臂原样保留）。

## 4. 已试判据与为何未落地（如实登记 ruled-out 清单）

试过的两处修改（均无名字/偏移/深度/计数特判、无 `_fix_/_merge_/_patch_/_fallback_/_hack_` 命名）：

1. **识别端归属（`region_analyzer.py`）**：新增谓词
   `_merge_block_owned_by_sibling_ternary(merge_block, cond_block, value_blocks)`，
   只读白名单事实 —— 块末 opcode ∈ `FORWARD_CONDITIONAL_JUMP_OPS`、恰 2 个条件后继、
   区域成员关系 `block_to_region[merge_block]` 是 `TernaryRegion` 且其 `entry`/`condition_block`
   恰为该块、该兄弟区域自有 `merge_block`、该块不是本区域值块。判 True 时：
   消费者扫描对条件测试类 opcode 弃权（不再设 `compare`/`__compare_target__`），且 merge_block
   不并入 `all_blocks`（与既有 `merge_context=='store'` 的 `_mb_is_nested_if_cond` 同源先例）。
   **效果**：分类已纠正（实测 `CTX=None TARGET=None blocks=[B38,B166,B170]`，B172 单一归属）；
   r3 电池 97/118 逐位不变、无绿臂变红。
2. **生成端路由（`region_ast_generator.py`）**：`_try_build_ternary_merge_consumer_expr` 头部早退
   —— 该构建器只检视 `merge_block.instructions` 的单三元指令流；块归属兄弟区域时按截断流重建
   会得到伪表达式并短路掉链路径。加此早退后**整条调用语句重新出现**，两个三元及其测试/值全部正确。

**未闭环的确切位置**：链装配器 `_try_build_ternary_chained_container`
（`region_ast_generator.py:49052`，其 docstring 本就声明覆盖
「outer ternary's merge_block is an inner TernaryRegion's entry … a call pattern
(PRECALL+CALL in merge_block, e.g. `.format()`)」）在本形状下返回 None，因为
`is_call_pattern = (not container_type and merge_ctx != 'fstring' and not region.func_call_info)`
—— 本例 `innermost.container_type == 'call'`（`_detect_ternary_context` 已把 `.format` 调用
归给后继区域）⇒ 该分支被 `not container_type` 挡死；`_try_build_ternary_chained_pattern`
同样要求 `not container_type`。落到 func_call_info 链吸收路径后产出扁平结果：

```
LOG.info('{sym} {side}{oper} {n}'.format, o.symbol,
         'BUY' if … else 'SELL', 'OPEN' if … else 'CLOSE', o.amount)
```

即 `.format` 的方法调用退化为裸属性节点、KW_NAMES 键名（`sym=`/`side=`/`oper=`/`n=`）丢失。
补这一段需要**重写生成端的实参装配**（嵌套调用重建 + KW_NAMES 键名分发），既超出本票
「识别端一次定形」的许可面（§1.3），也在 `func_call_info` 这条全语料共用的热路径上改动，
回归面远超剩余预算 ⇒ 按纪律回退，不换取局部文本改善。

## 5. 顺带发现（不在本票内换绿，如实登记）

`t3_toplevel_inline`（函数体顶层，非 elif 臂内）`LOG.info('{s}'.format(side=<单三元>))` +
尾 `return` 今日 **1/2 failure**，产物把两条语句合成
`return LOG.info('no {side}'.format(side=…))` —— 单三元实参在**无臂宿主**下的 merge 归属，
与本票的「并列 ≥2」维度正交，登记为独立残口候选，未追。

## 6. 建议永久臂（**未写入 `r3_probe_index.json`**）

本票零落地，若把三条恒红臂追加进认证索引会破坏他人依赖的 97/118·54 文件·33/21 基线，
故只归档源码，待 B114 真落地时由落地方一并登记（索引格式与现臂逐字相同）：

| 建议臂名 | 要求 | 源码（≤20 行） |
|---|---|---|
| `r3_a18_two_inline_arg_ternaries_fold` | **必须重建整条调用**（must-fold） | `t4_two_arg_ternary.py`：`def is_trade(): return True` + `def f(o): if o is None: return None` / `if not is_trade(): LOG.info('{sym} {side}{oper} {n}'.format(sym=o.symbol, side='BUY' if o.dir.upper()=='BUY' else 'SELL', oper='OPEN' if o.fd.upper()=='OPEN' else 'CLOSE', n=o.amount))` / `return o.order_id` —— 今日 2/3 failure（B114 标本） |
| `r3_a19_one_inline_arg_ternary_ok` | **必须保持绿**（must-not-fold / 防过伸展对照） | `t1_inline_arg_ternary.py`：同宿主、实参表内**只 1 个**三元 —— 今日 3/3 success，修复后必须仍 success |
| `r3_a20_kw_ternary_between_plain_args` | 必须保持绿（第二对照） | `t5_two_kw_before.py`：三元前有 `a=`、后有 `b=` 普通实参，仍 1 个三元 —— 今日 3/3 success |
| `r3_a21_genexpr_with_two_arg_ternaries` | genexpr-with-ternary（本票未及生成） | 待落地方在 `t4` 宿主上把 `LOG.info(...)` 移入 `[... for i in xs]` 元素位构造 |

标本源文件现存放于 `D:/Temp/rrv3/{t1,t4,t5}_*.py`（含同名 `.pyc` 与 `*OK.py` 产物）。

## 7. grep 标记

计划落地的标记串（本轮**在生产代码中 0 命中**，与「未落地」声明一致）：

```
[R3-IFEXP 修复·兄弟三元头块唯一归属]      —— region_analyzer.py（识别端归属 + 消费者弃权）
[R3-IFEXP 修复·兄弟三元实参链归属外层调用]  —— region_ast_generator.py（链路径路由）
```
