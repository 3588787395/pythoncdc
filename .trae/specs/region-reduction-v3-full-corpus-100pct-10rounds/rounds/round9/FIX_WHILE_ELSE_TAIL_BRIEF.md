# Round 9 工单 #16 简报：`while True:` 的体尾被降格成 `while … else:`（3 个单元，codegen 复演已证）

取证口径：输入 `.pyc` 从不被重写，故直接读盘；产物一律 `git show HEAD:` 副本。
本轮只读 `dis`＋`compile`（stdlib），**未导入 core、未跑发射器**，因在飞工单
`r9-fix-elif-chain-grouping` 正在写 `core/cfg/region_ast_generator.py`（工作树 +7 KB／131 插 29 删）。
**`core/cfg/region_analyzer.py` 工作树＝HEAD**（`git status -- core` 只列 generator），
本票落点 `region_analyzer._find_loop_else:6028` 与在飞票零争用；
但按「同一条流水线不得两头改」，本票**先入库排队，等在飞票封表后再派**。
复演脚本：`D:/Temp/r9main/tailpred.py`（逐边事实）、`D:/Temp/r9main/shape.py`、`D:/Temp/r9main/shape2.py`（同 interpreter 复现真源形状）。

## 一、靶面（完整路径 + qualname 钉死）

`IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
→ `<module>.TradeLiveBroker._process_order` / `_process_cancel_order` / `_trade_status_handle`
（HEAD 产物 `trade_live_brokerOK.py` line 425 / 524 / 897 三处 `while … else:`，`else` 体分别是 `sleep(0.001)/sleep(0.001)/sleep(0.5)`）。

锚点：`_find_loop_else`（`region_analyzer.py:6028`），WHILE 分支出口收集 `:6361–6394`，
`natural_exit` 求解 `:6423`，既有 no-break 兄弟结构判据 `_is_post_merge_sibling_head`；
生成端消费者 `_loop_generate_while`（`region_ast_generator.py:6638`）／`_loop_generate_body:8251`。

## 二、真源形状：本机 3.11.7 `compile` 复演三种写法的回边结构（铁证）

| 写法 | 循环测试 | if／exit 假边落点 | 体尾或 else 体的**末指令** |
|---|---|---|---|
| **B2 `while True:` + 体内首句 `if cond:` + 体尾句** | 头 NOP@2，测试@4..@40 | 假边 → **@108＝体尾块** | 体尾：**`JUMP_BACKWARD->4`**（回到 NOP 之后的体首）；`continue` 另有 `JUMP_BACKWARD->2`（回到 NOP） |
| **C 真 `while cond: … else: sleep`** | 测试在顶 | 假边 → 循环之后 | else 体**无任何向后边**（`continue` 写在 `while…else` 里是 SyntaxError），末句落空到函数尾 |
| **D `while cond:` + try/except + 体尾句** | 测试在顶，假边 → 循环之后@254 | — | 重测用 **`POP_JUMP_BACKWARD_IF_TRUE->40`**，**没有**无条件 `JUMP_BACKWARD` |

⇒ 判据的字节级依据：**真 else 体永远不带「跳回本循环」的向后边；带无条件向后边跳回本循环区段的块只能是循环体尾。**

三个失败单元读盘实测，**全部是 B2 形状**（本票判据的正面证据）：

| 单元 | 头/锚 | 「条件块」 | 其假边落点 E | E 的入边 | E 的末指令 | 其余回边 |
|---|---|---|---|---|---|---|
| `_process_order` | NOP@44 | @46..@94（`len(self.open_orders) > 0`） | **@3128** | `POP_JUMP_FORWARD_IF_FALSE@94`、`JUMP_FORWARD@3024`、`JUMP_FORWARD@3118`（后两条源自循环内） | `JUMP_BACKWARD@3170 -> 46`＝函数最后一条 | 6 条 `-> 44` |
| `_process_cancel_order` | NOP@44 | @46..@94 | **@2000** | `POP_JUMP_FORWARD_IF_FALSE@94`、`JUMP_FORWARD@1826`、`JUMP_FORWARD@1920`（后两条源自循环内） | `JUMP_BACKWARD@2042 -> 46`＝函数最后一条 | 4 条 `-> 44` |
| `_trade_status_handle` | NOP@44 | @46..@148 | **@830** | `POP_JUMP_FORWARD_IF_FALSE@148`、`JUMP_FORWARD@720`、**FALL**`POP_TOP@828` | `JUMP_BACKWARD@872 -> 46`＝函数最后一条 | `@294 -> 44` |

⇒ 真源写的是 `while True:` + 体内 `if <cond>:` + 体尾一句 `time.sleep(...)`；
分析端把**那条 `if` 的测试当成了循环测试**，又把**该 if 的汇合块（＝体尾）当成了 else 体**。
三处语义与字节序同时错（`while True` 变 `while cond`、每轮必执行的体尾变成只在离开后执行一次）。

**注意（主代理自纠）**：本简报上一版把判据写成「E 须有顺序续入前驱」——**错**：
`_process_order`/`_process_cancel_order` 的 E **只有跳入边、没有 FALL 入边**。
形状差异来自 if 体尾是否紧邻汇合块，判据不得依赖它。

## 三、判据（只取白名单事实：块末 opcode / 后继前驱 / 区域成员）

对 WHILE 循环 `L`（header、`body_set`、`condition_block`）的候选 else 入口 `E`：

1. **取消认领**：`E` 的末条指令是**向后跳转**（`JUMP_BACKWARD`／向后相对跳转）且其目标 ∈
   `{header} ∪ {condition_block} ∪ body_set`（即跳回本循环自身区段）。
   依 §二 的 C 行：合法 `while…else` 的 else 体不可能有这种边 ⇒ 有即是循环内部块。
   → `E` 归循环体（原则 2：每块唯一归属），`else_blocks` 置空，`E` 由体尾发射。
2. **连带改判（本案根因）**：若被取消的 `E` 恰是 `condition_block` 假边的落点，
   则该「条件块」是**体内的 `if`**，`L` 的 `condition_block` 应为 `None`（`while True:`），
   该 `if` 须作为体内的 `IfRegion` 独立识别（原则 3：嵌套即抽象节点；原则 4：入口引用）。
   只发第 1 步会把 `while True: if …` 塌成「无条件体 + 丢失的 if」，读数会变好但语义仍错——
   两步必须同做，并以逐单元名单证明产物形状（`while True:` ∧ 内层 `if` ∧ 体尾句）。
3. **必须保住**（真 else／真 for-else 桩）：`E` 只由循环**出口边**进入、且 `E` 内不跳回本循环区段
   （`else: continue` 桩属 FOR 循环：其回边目标是 FOR_ITER 头，本判据第 1 步只在 WHILE 上生效，
   且 FOR 侧另有 §R3-B10 的 break 证据判据，不得改动其语义）。

禁止：以 opcode 名／块数／深度／偏移／文件名为特判；禁止「见 `While.orelse` 就不发 else」的输出端禁令（违反 C3）。
§二 表中的一切 offset **不得进入代码**，它们只是取证的复演凭据。

## 四、负对照与复现臂（既有资产，必须复跑）

- `test_repros/round9/r9lo_probe_index.json`：6 臂（`r9lo_01/02/03` 红复现、`r9lo_04/05/06` 绿对照）。
  被回退工单在 HEAD 态实测 **9/12 单元**（3 红 3 绿），与本票无关但可作形状哨兵：
  验收要求 **3 条红臂转绿 ∧ 3 条绿臂保持绿**，逐臂名单写进 FIX.md。
- 语料负对照：`api_base.decorate_api_exc`（While@33，`else` 体是 `while False: pass`）**在 HEAD 读 Equal**；
  若本票把它一起改掉＝以改判据换读数，判 FAIL。
- 全量占比：407 产物穷举 `ast` 仅 **7 处** `while…else`（4 处单元失败、3 处通过）——
  本轴解释 42 残差中的 4 个，**不是**落点族 35 个的通用解释，不得当主因记账。

## 五、与 #13 / #14 / #15 的分家（不得并案，不得重复计功）

| 单元 | 本轴关掉的部分 | 同单元还欠的账 |
|---|---|---|
| `_trade_status_handle` | 体尾降格 + `while True` 改判 | 内容与重排耦合（附二记为 #16-coupled），本轴**不保证**翻正 |
| `_process_order` | 同上 | **#13 OMISSION 主体**：orig 507 条 vs prod 42 条（删 470／5 段）——补回 if 只多一小块，差距仍巨 |
| `_process_cancel_order` | 同上 | 同上（333 vs 40，删 299） |
| `_save_testds_to_csv` | **不属本轴**（其 `else` 体是 `return None`，隐式尾声落点） | 归 #15 判据面 |

⇒ 文件级门禁：`trade_live_broker` 当前 118/128（差 10 单元），本轴最好情形 118→121，
**不产出**「≥1 个 pyc 由 failure 转 success」。轮门禁仍须由 §X 十字名单文件（#14/#13/#15）交付；
把本票当门禁来源记账即虚报。

## 六、交付要求

1. 先臂后码：在当前 HEAD 字节下把 §三 判据做成/复用 `r9lo_*` 臂并读红，再动生产码。
2. 落地以 grep 标记为凭（建议 `[r9-b124-whiletrue-ifjoin-else]`），`FIX.md` 声明「代码已落地」或「仅归档 spec 未落地」。
3. 触及方法（`_find_loop_else`，以及若改动的 `_annotate_loop_structural_roles:4041`／`_is_loop_exit_block:2954`／
   `_loop_generate_while:6638`）补六项模板 docstring（①算法依据②归约顺序③唯一归属判定④嵌套处理⑤入口引用语义⑥反编译流程）＋ C 条款，且与行为一致。
4. 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀新方法（G3）；无硬编码深度／计数／偏移／文件名特判（G4）。
5. 自测门禁顺序：`r9lo` 6 臂 → 34 小测试集 batch → `trade_live_broker` 单验逐单元名单（须见 `while True:` 形状）
   → 402 八分片双门禁（REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0）。零翻转即按 sha256 逐字节回滚（B123 已立此例）。
