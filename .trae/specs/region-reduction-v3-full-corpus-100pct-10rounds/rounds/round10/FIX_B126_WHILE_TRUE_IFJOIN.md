# Round 10 工单 #16（B126）：`while True:` 的体内 `if` 被当循环测试、其汇合块（体尾）被降格成 `while … else:`

状态：**进行中**（本文件随进度增量落盘，防截断；终态见文末「落地声明」）。

## 〇、工单摘要（取自 `rounds/round9/FIX_WHILE_ELSE_TAIL_BRIEF.md`）

靶面：`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
→ `<module>.TradeLiveBroker._process_order` / `_process_cancel_order` / `_trade_status_handle`
（3 单元）。产物发 `while <cond>: … else: time.sleep(x)`；真源是
`while True:` + 体首句 `if <cond>:` + 体尾句 `time.sleep(x)`（体尾块以
`JUMP_BACKWARD` 跳回体首测试块＝循环区段内部）。

判据依据（简报 §二，本机 3.11.7 `compile` 复演）：**合法 `while…else` 的 else 体
永不含「跳回本循环自身区段」的向后边**（该处写 `continue` 是 SyntaxError）。
故 else 认领可从块事实直接否证，不需要文件名/偏移/计数特判。

两步同做（只第 1 步＝语义仍错，判为窄门控换读数）：

1. **取消 else 认领**（分析端 `_find_loop_else`）：候选 else 入口 `E` 的末条指令为
   向后跳转且目标 ∈ `{header} ∪ {condition_block} ∪ body_set` ⇒ `E` 归循环体，
   `else_blocks` 不再认领它。
   **不得**要求 `E` 有 fall-through 前驱——三站点中两站的 `E` 只有跳入边（简报 §二 注意）。
2. **连带改判**：若被取消的 `E` 恰是当前 `condition_block` 的假边落点，则该「条件块」
   是体内的 `if`，`L.condition_block = None`（`while True:`），该 `if` 须作为体内独立
   `IfRegion` 识别/发射。

违反条款（修复前）：**原则 2（每块唯一归属）**——体尾块同时被 else 认领与回边归属；
**原则 3/4**——体内 `if` 未成为抽象节点、其入口未被父级引用；**C3（守卫封闭）**——
「else 体含跳回本循环的向后边」这一非局部事实没有显式守卫排除。
修复语义＝封闭守卫恢复 C1/C2/C3，禁输出端「见 `While.orelse` 就不发 else」（违反 C3）。

## 一、复现臂电池（先臂后码）

前缀 `r9w16_`，索引 `test_repros/round9/r9w16_probe_index.json`（18 臂：12 复现 + 6 对照）。
基线读数（**HEAD 字节**，产物由 `pycdc.py -o` 删除后重生成，未手改任何产物）：
`D:/Temp/r9w16/base.json` → units **26/37**，files success **7** / failure **11**。

| 臂 | 角色 | HEAD 读数 |  failing unit |
|---|---|---|---|
| r9w16_01_bare_tail | 复现（裸循环，最浅层） | failure 1/2 | `<module>.r9w16_01_bare_tail` Different control flow |
| r9w16_02_break_in_arm | 复现（臂内 break） | failure 1/2 | 同上格式 |
| r9w16_03_continue_in_arm | 复现（臂内 continue） | failure 1/2 | 同上 |
| r9w16_04_multi_arm_join | 复现（多臂同汇体尾） | failure 1/2 | 同上 |
| r9w16_05_nested_in_for | 复现·深度2（循环嵌 for） | failure 1/2 | 同上 |
| r9w16_06_in_try_except | 复现·深度2（循环在 try 体内） | failure 1/2 | 同上 |
| r9w16_07_except_epilogue_join | 复现·深度3（except 尾声汇入体尾） | failure 1/2 | 同上 |
| r9w16_08_while_in_while | 复现·深度2（while 嵌 while） | failure 1/2 | 同上 |
| r9w16_09_tail_is_cond | **意外对照**（体尾本身是 if） | **success 2/2** | HEAD 已发 `while True:` + 内层 if + 体尾 if ⇒ 证明发射端能渲染目标形状，缺的是分析端认领 |
| r9w16_10_class_method_ctx | 复现（类方法语境＝语料形状） | failure 2/3 | `<module>.R9W16Ten._trade_status_handle` |
| r9w16_11_deep_three | 复现·深度3（while>for>with>while） | failure 1/2 | 同上 |
| r9w16_12_after_join_stmts | 复现（循环后有顺序语句） | failure 1/2 | 同上 |
| r9w16_13_ctl_while_else | **对照**：真 `while…else` | success 2/2 | — |
| r9w16_14_ctl_while_else_break | **对照**：真 `while…else` + break | success 2/2 | — |
| r9w16_15_ctl_for_else_continue | **对照**：真 `for…else: continue` 桩 | success 2/2 | — |
| r9w16_16_ctl_plain_while_tail | **对照**：`while cond:` + 体尾 | success 2/2 | — |
| r9w16_17_ctl_else_nested_loop | **对照**：else 体是嵌套 while（回边目标在 else 体内，**不**在本循环区段） | success 2/2 | — |
| r9w16_18_ctl_while_else_cont_outer | **对照**：else 桩 `continue` 跳**外层 for** 头 | success 2/2 | — |

⇒ 11 条复现臂读红（≥10 达标）、6 条对照读绿（含意外绿的 09），深度变体 05/06/07/08/11 覆盖
「裸循环 / 循环嵌 for / 循环嵌 while / 循环在 try 体内 / except 尾声汇入体尾 / 深度3」。

### 一B、逐单元取证（HEAD 字节，只读探针 `D:/Temp/r9w16/probe_regions.py`）

**简报 §一 的定位需订正**（按「先复验工单前提」纪律）：`_find_loop_else` 对这三单元**返回
`(None, None)`**——它没有认领 else。实测认领面是**同文件调用方**
`_identify_loop_regions` Step 8 之后的 `_else_backedge_blocks` 构造段
（`region_analyzer.py:4810` 起，条件 `condition_block == header and not else_blocks`）：
它读「header 的前向假边落点 ∈ body ∧ 该落点末条 = `JUMP_BACKWARD → header`」，
把该落点及其 `JUMP_FORWARD` 入边块整体从 `body` 摘出塞进 `else_blocks`。
⇒ 该段的**成立条件本身就是简报 §三.1 的否证条件**（else 入口末条是跳回本循环区段的向后边）。
配套第二处：`_is_while_true`（`:5790` 之后）对同一形状显式 `return False`
（体尾有 body 前驱 ⇒ 判成「非 while True」），于是 Step 7 把该 if 块当作 `condition_block`。

语料三单元实测（`backedge_into_span=True` 即简报 §二 B2 形状）：

```
_process_order         header=cond=@46  ELSE @3128..3170 JUMP_BACKWARD->46  backedge_into_span=True
                       COND @46..94 POP_JUMP_FORWARD_IF_FALSE->3128  false_target=3128 in_else=True
_process_cancel_order  header=cond=@46  ELSE @2000..2042 JUMP_BACKWARD->46  True   （false_target=2000 in_else=True）
_trade_status_handle   header=cond=@46  ELSE @830..872  JUMP_BACKWARD->46  True   （false_target=830  in_else=True）
```

对照臂 13/14/17/18 的 else 认领 `backedge_into_span=False`（末条 `RETURN_VALUE`，或回边目标
是**外层 for** 头 @6 ∉ 本循环区段）⇒ 判据不触碰它们。

## 二、判据实现（两步同做）

