# Round 2 — 测试工程师 REVIEW（诊断 only，零生产代码改动）

- 工作树 `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`，分支 `rr-v3r01-f557fd`，`python -X utf8`（3.11.7）
- 唯一判据 `scripts/pyc_verify.py single` / `batch --index`（未改判据、未写替代 checker）
- 三个靶全部按序逐个完成（1 real_quote → 2 risk_calculation → 3 future_contract_info），另加两条 Round-1 残留的**分歧钉桩**（§7）
- 产物一律「删除 + `pycdc.py -o`」重生成，**未手改任何 `*OK.py`**；未触碰 `core/** pycdc.py bytecode/** parsers/** utils/** scripts/pyc_verify.py`
- 测试侧工具（本轮新建，只读用途）：`test_repros/round2/_r2diag.py`（逐指令内容标签比对 + 基本块前驱/后继）、`test_repros/round2/_r2gen.py`（标本生成+三步电池）
- 全部命令 rc=0 且 <300s（最长：单文件 pycdc+single ≈ 13s；电池 56 臂 batch 2.9s）

## 0. 靶读数（本轮实测原文，非沿用基线）

| # | pyc | 实测 | 失败单元 |
|---|---|---|---|
| 1 | `site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc` | `status=failure units=43/45` | `<module>.RealQuoteData.get_real_minute_kline`、`<module>.RealQuoteData.get_tick_direction` |
| 2 | `site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | `status=failure units=41/43` | `<module>.PluginRiskCalculation._on_publish_after_trading_end`、`<module>.PluginRiskCalculation._save_testds_to_csv` |
| 3 | `site-packages/fly/common/future_contract_info.pyc` | `status=failure units=27/29` | `<module>.FutureInfoCache.check_user`、`<module>.FutureInfoCache.info_conbine` |

与任务书给出的读数逐位一致（三靶六单元全部复现，无一消失）。

## 1. 判据口径与伪影排除（本轮实际用到的规则）

`_r2diag.py` 的比对把每条**跳转操作数的绝对偏移替换为「目标块内容标签」**（目标起 4 条 opcode，跳 CACHE）。于是
「目标偏移移动但目标块不变」= 自动判等 ⇒ 打印出来的都是**边/成员关系**真差异，不需要再靠肉眼做偏移对齐。

本轮出现的伪影，逐项判定：

| 伪影 | 出现处 | 判定 |
|---|---|---|
| `EXTENDED_ARG` 插入（跳距 >255B） | T1 kline off572、T3 check_user off462、残留 get_fields off92 | **单独不构成缺陷**；但 kline/check_user/get_fields 三处的 EXTENDED_ARG 与「目标块内容同时改变」同现 ⇒ 它是真缺陷的算术后果，不可豁免掉差异本身 |
| 行追踪 `NOP` 增删 | T2 `_on_publish` off2746 | 该 NOP 是 `while True:` 体首块，**不是排版伪影**：它消失 = 循环整体未被发射的证据（伴随 -8 指令） |
| `LOAD_CONST <code object <lambda>>` 的 repr 差异（地址/co_filename） | T2 `_on_publish` off1352 | 纯伪影（判据对嵌套 code 递归比较、且元数据豁免），已在工具侧归一为 `<code name:Nins>` |
| 其余跳转目标 +2/+4 位移 | 六单元 | 伪影，内容标签比对已自动判等 |

## 2. 靶 #1 `real_quote.pyc`（43/45）

### 2.1 单元 `RealQuoteData.get_tick_direction` — 第一分歧

```
orig 297 insns | prod 298 insns（+1）
首个真分歧：off 1102  ORIG (无)  vs  PROD JUMP_FORWARD → 目标块内容 NOP,LOAD_FAST,POP_JUMP_FORWARD_IF_FALSE
（orig[200] 处一次 insert；其余 off 全为等值位移伪影）
```
块级证据（`_r2diag.py blocks`，前驱集合是决定性事实）：

| | ORIG | PROD |
|---|---|---|
| `return redata` 块 | off1102 `LOAD_FAST redata`→1104 `RETURN_VALUE`，**preds=[186, 190, 199]**（3 条臂汇入） | off1104/1106 同内容，**preds=[190]**（只剩 1 条） |
| if/elif 链的汇 | = off1102 终态块（链尾出口即该 `return redata`） | = off1108（`NOP` ln1327 → `if redata:`），**preds=[172, 186, 200]**，其中 172 是**跨区域边**（外层结构的 break/退出落点） |
| off1102 在 PROD 中 | — | 新增 `JUMP_FORWARD`，把原 `flag == -1` 臂的落点改投 1108 |

原始源码形状（行号取自 ORIG 行追踪）：链体各臂以 `system_log.debug(…)` 收尾（POP_TOP），**链的汇合块是一条终态 `return redata`（ln1326）**，ln1328 的 `if redata:` 只能由区域外那条边（172）进入。产物把链的 merge 取成 **1108（终态块之后的块）**，于是终态 `return redata` 被降级成单臂专属语句、原应到达它的臂改为跳过它——该臂此后会执行 ln1328 之后的代码，而原始控制流永不执行 ⇒ **语义也不等价**。

### 2.2 单元 `RealQuoteData.get_real_minute_kline` — 第一分歧

```
orig 280 | prod 283（+3，含 off572 的 EXTENDED_ARG 1）
首个真分歧 off572/574：
  ORIG  POP_JUMP_FORWARD_IF_NONE   → 目标内容 LOAD_FAST,RETURN_VALUE,LOAD_GLOBAL,LOAD_FAST
  PROD  EXTENDED_ARG 1 / POP_JUMP_FORWARD_IF_NONE → 目标内容 LOAD_CONST,RETURN_VALUE,PUSH_EXC_INFO,LOAD_GLOBAL
```
块级证据：ORIG B101(off572) `succ=['jump:B104']`，**B104(off578 `LOAD_FAST kline`) preds=[101, 103]** —— 该 `return kline` 终态块被两条路径汇入：`or` 链第一操作数的真跳 + 第二操作数的假臂直落。PROD B102(off574) `succ=['jump:B253']`（函数尾部 `LOAD_CONST None; RETURN_VALUE`，其后紧跟 PUSH_EXC_INFO），对应 `return kline` 块 **preds=[104]** 只剩 1 条。

即原始 `if fq is None or ex_info is None: return kline`（产物第 386-388 行被还原成 `if fq is not None: if ex_info is None: return kline`）**丢掉了一条臂的返回**：`fq is None` 路径由 `return kline` 变成落到函数隐式 `return None`。语义不等价 + 少一条边。

第二个 replace（orig[224] off1210 的 `FOR_ITER` 目标标签第 3、4 项不同）经块级核对为**工具标签越界伪影**：两版目标块前 2 条 opcode 同为 `LOAD_FAST,RETURN_VALUE`，差异在目标块之后的邻块内容，非本单元的边差异。

### 2.3 两单元是否同一构造？

**不是。** 两者都涉及「终态（`return`）块被当作区域汇合块」，但归属机制不同：
`get_tick_direction` 是 **IfRegion 臂的 merge 选择**（分歧在 off1102 的跳/被跳，3-前驱终态块被降级），
`get_real_minute_kline` 是 **短路条件链的极性改写**（分歧在 off572 的操作数跳转目标身份，2-前驱终态块丢前驱）。
偏移、块角色、修复面均不同 ⇒ 分成 B104 / B105 两条登记（§2.4、§2.5），**不合并为一个机制**。

### 2.4 B104 登记（get_tick_direction）

**B104 — if/elif 链尾的「终态汇合块」因 E 箱为空被 merge 守卫拒认，merge 外推到跨区域边所接入的更外层块，终态兄弟语句被降级为单臂专属**
- 锚点：`site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc` / `<module>.RealQuoteData.get_tick_direction` / orig off **1102-1104 终态块 preds=[186,190,199]** vs prod off 1104-1106 同块 preds=[190]，且 prod off1102 新增 `JUMP_FORWARD → off1108`（1108 preds=[172,186,200]，172 为跨区域边）。
- 标本锚点：`r2v3_a13` off 同形（见 §5 表），`r2v3_a16`（while 宿主）/ `r2v3_a17`（if/else 两臂）/ `r2v3_a22`（方法宿主）/ `r2v3_a23`（链后兄弟为 `return None`）/ `r2v3_a24`（模块体宿主，链尾汇为 `raise SystemExit`，`units=0/1`）。
- 与 B100 的关系（点名哪个条件欠伸）：**是 B100 守卫的欠伸侧**。`_compute_arm_level_join` 判据 (4)（`core/cfg/region_analyzer.py:3112-3121`）要求「箱数 ≥ 2 **且** E 箱非空」，并明文规定「**E 箱为空 ⇒ 该块只被本 if 自己的臂汇入（链尾出口形），本方法不介入**」。本形状里链的汇合块恰是「全部前驱都是本链的臂」的**终态**块（E 箱为空），于是 (4) 主动弃权、把 merge 留给「链构造器/退化 merge 守卫」，而后者把 merge 取成了跨区域边接入的下一块。缺的成员条件：**弃权分支没有区分「链尾出口形 = 可继续向外展开的顺序块」与「链尾出口形 = 终态块（RETURN_VALUE/RETURN_CONST/RAISE_VARARGS，preds 全为臂、且该块无后继）」**；后者按 §1.2 原则2 必属父级兄弟序列（它只能被那几条臂汇入，不可能属于任何子区域）。
- 违反条款：§1.5 **C1 局部消费**（merge 取到了本区域出边之外的目标）+ §1.2 **原则2 每块唯一归属**（终态块被臂内认领）；亦触 **C3 守卫封闭**（1108 被区域外路径 172 引用时无显式认领/排除）。
- 不是深度形：`r2v3_a13/a23` 深度 2 即错；`r2v3_a14`（汇合块非终态）、`r2v3_a15`（无 break）、`r2v3_a18`（链后无兄弟）同深度却 MATCH ⇒ 判据维度是**汇合块的块末 opcode 类别 + 是否存在跨区域入边**，与深度无关（符合 Round-1 §9 结论）。

### 2.5 B105 登记（get_real_minute_kline）

**B105 — 短路 `or` 链的 None 极性翻转把「与第二操作数共享的终态 then 臂」改成嵌套正极性 if，导致第一操作数真臂的落点被改投函数尾（返回值丢失）**
- 锚点：同上 off **572**；ORIG 目标 = off578 `LOAD_FAST kline; RETURN_VALUE`（2-前驱块），PROD 目标 = off1118 区函数尾 `LOAD_CONST None; RETURN_VALUE`（`jump:253`）。产物文本：`real_quoteOK.py:386-388` `if fq is not None:` / `if ex_info is None:` / `return kline`。
- 站点（grep 核实存在）：`core/cfg/region_ast_generator.py:120 _flip_is_none_compare`（docstring 自陈「翻转 `x is None` / `x is not None` 的比较运算符…仅 None 恒等比较可这样翻转；含其它运算符时回退到 `_negate_expr`」，回退链 `:131/:137/:140/:148/:154/:157`）、`:104 _negate_expr`、`:163 _fallthrough_cond_for_jump`。B105 的宿主正是 **None 恒等比较** ⇒ 走的是翻转路径；同形状的 `in/not in`（B108）走的是另一路径，两者需分别核。
- 违反条款：§1.2 **原则2**（共享终态块的一条前驱边被丢弃）+ **原则4 入口引用语义**（then 臂的引用被改写为条件嵌套而非臂跳转）+ §1.5 **C3**（该终态块被条件区域外的路径引用时未显式认领）。§5.3 亦适用：此处的 EXTENDED_ARG 不可当对齐伪影豁免。
- **如实标注**：本轮**未能为该单元造出最小合成孪生件**。`r2v3_a09`（`if a is None or b is None: return c` + 后续兄弟 + 尾 `return c`）、`r2v3_a10`（两条独立 if 的等价嵌套形）、`r2v3_a11`、`r2v3_a20`（try 宿主）、`r2v3_a21`（else 臂宿主）**今日全部 MATCH**；只有把它放进 B104 的宿主（`r2v3_a19`：for+break 宿主里的 `or`-None 终态汇）才 MISMATCH。⇒ B105 已定位到操作码/产物文本/候选函数，但标本集合里它的独立证据只有真文件本身；修复后须以 `real_quote.pyc` 44/45→45/45 作为验收，不能用合成臂代替。

## 3. 靶 #2 `plugin_system_risk_calculation/__init__.pyc`（41/43）

### 3.1 单元 `_on_publish_after_trading_end` — 第一分歧

```
orig 531 | prod 523（-8）
唯一非伪影分歧区：off 2744-2806（线性 idx 482-490）
  ORIG off2744 POP_JUMP_FORWARD_IF_FALSE（`if is_end:` 的假臂 → 链外兄弟 `event_bus = self._engine.event_bus`）
       off2746 NOP（`while True:` 体首，ln381）
       off2752 IMPORT_NAME …  off2760 POP_JUMP_IF_TRUE
       off2764 JUMP_FORWARD → event_bus 块            ← break
       off2766 LOAD_GLOBAL time / … / 2804 POP_TOP     ← time.sleep(0.01)
       off2806 JUMP_BACKWARD → off2748                 ← 无条件回边 = while True
  PROD off2748-2756 同 import，off2760 POP_JUMP_IF_FALSE → 直接落入 off2764（event_bus 语句）
       —— 无 off2764 的 break 跳、无 2766-2804 的 sleep、无 2806 的回边、无体首 NOP
```
-8 = 1（`JUMP_FORWARD` break）+ 6（`time.sleep(0.01)` 调用体）+ 1（`JUMP_BACKWARD` 回边），逐条对得上。
产物文本 `__init__OK.py:251-255`：`if is_end:` → `from … import THREAD_STATUS` → `if THREAD_STATUS:` → `pass` → `event_bus = …`，**`while True:` 整层消失、`break` 变 `pass`、循环体尾语句 `time.sleep(0.01)` 被丢**。
off1352 的 `LOAD_CONST <lambda>` 差异是伪影（§1 已归一）。

### 3.2 单元 `_save_testds_to_csv` — 第一分歧

```
orig 81 | prod 75（-6）
首个真分歧 off208/210（处理器尾）：
  ORIG  off206 POP_EXCEPT → off208 JUMP_BACKWARD → 目标块内容 LOAD_FAST,LOAD_ATTR,POP_JUMP_FORWARD_IF_TRUE,NOP   = 回边到循环头 off108
  PROD  off208 POP_EXCEPT → off210 JUMP_FORWARD  → 目标块内容 PUSH_NULL,LOAD_FAST,LOAD_FAST,LOAD_FAST              = off220（try 之后的语句）
```
块级证据：ORIG B16(off108 循环头) **preds=[15, 37]**（37 = 处理器的 `JUMP_BACKWARD`）；PROD B16 **preds=[15]**，而 PROD B42（`csv_writer(...)` 语句体）**preds=[31, 38]**（38 = 处理器的正向跳）⇒ **`except Empty: continue` 被降级为 `pass`（直落入 try 之后的语句）**。产物文本 `__init__OK.py:537-552`：`while True:`（凭空多出）+ `while not self._stop_save_csv_thread:` + `except Empty: pass` + `else: return None`（凭空多出）+ 第二个 while 里 `if THREAD_STATUS: break`（原始是 `return`，ORIG B65/66 preds=[64] 的终态块）+ **`time.sleep(0.01)` 整条丢失**（ORIG B67-B72 off296-334；-6 恰为该调用体）。

### 3.3 两单元是否同一构造？

**同一族、两个不同的构造侧面**，且共用一条实测规律：**宿主是「if 臂内的循环」时才崩，宿主是函数体尾/try 体/for 体时不崩**。
- `_on_publish`：循环区域整体未被交付（B107）。
- `_save_testds`：处理器尾跨区跳转（continue）的落点被判成 try 之后的顺序语句（B106）；同单元另一处又出现 B107 的形态（第二 while 的体尾兄弟 `time.sleep` 被丢、`while-else` 被凭空造出）。
- 支撑偏移：两者分歧块一个是 `JUMP_BACKWARD→循环头`（208），一个是 `JUMP_BACKWARD→体首 2748`（2806）+ `JUMP_FORWARD→区域出口`；不是同一 offsets，故登记为 **B106 + B107** 两条，不写成一条。

### 3.4 B106 登记

**B106 — except 处理器尾的 `POP_EXCEPT + JUMP_BACKWARD`（continue，回边指向外层 while 头）未作为跨区目标认领，处理器被当成以 `pass` 收尾并直落 try 之后的语句**
- 锚点：`…/plugin_system_risk_calculation/__init__.pyc` / `<module>.PluginRiskCalculation._save_testds_to_csv` / orig off **208 `JUMP_BACKWARD → 108`**（循环头 preds=[15,37]）vs prod off 210 `JUMP_FORWARD → 220`（该语句块 preds=[31,38]）。
- 标本：`r2v3_b06`（函数 while 宿主）/`b07`（try 后无语句仍错）/`b09`（方法宿主）/`b10`（try-in-try+finally）/`b11`（with 宿主）/`b13`（处理器里 `break` 同族，落点为区域出口）/`b18`（try-else 形）。
- 对照（今日 MATCH，修复后必须仍 MATCH）：`b08`（同一形状但处理器写 `pass` —— 唯一改动 `continue`→`pass` 即翻回 MATCH，见 §5）、`b19`（外层再套一个 while ⇒ 现在的代码只在「处理器直落本 while 体尾」这一层成员关系上错）。
- 违反条款：§1.2 **原则4 入口引用语义**（`Continue` 节点必须引用回边 entry；§3.2.2 的显式 `Continue` 兄弟机制未覆盖「处理器尾」这一位置）+ §1.5 **C3 守卫封闭**（continue 目标跨区域时缺显式认领）；亦触 **C1**（处理器区域的出边被读成 try 之后的顺序边）。
- 与 B100/B103 的关系：**不是** (4b) 的欠伸，而是 `_ARMJOIN_EXIT_OPS`/`_exhausted` 的**收束种类**在 merge 之外的第二个消费面（`region_ast_generator.py:26477 _is_continue_like`、`:12836 _block_is_continue_target`）没把「块末 = `POP_EXCEPT` 之后的 `JUMP_BACKWARD`」认成 continue —— 该块的块末 opcode 不是回边本身，回边在 `POP_EXCEPT` 之后一条，故 opcode 白名单判据在 handler 形状上系统性失效（这是可测的：`b06` 与 `b08` 的唯一区别就是那条回边的有无）。

### 3.5 B107 登记

**B107 — 位于 if 臂内的 `while`（含 `while True:` 无条件回边形）区域在非函数尾宿主下未被交付：循环层丢失或退化为 `while … else: return None`，并丢掉体尾（break/return 臂之后、回边之前）的同层兄弟语句**
- 锚点：`_on_publish_after_trading_end` off **2746 NOP / 2764 JUMP_FORWARD(break) / 2766-2804 time.sleep / 2806 JUMP_BACKWARD** 四处整体缺失（orig 531 → prod 523）；同形状第二例 `_save_testds_to_csv` off **296-334 `time.sleep(0.01)`** 整体缺失（orig 81 → prod 75）。
- 产物文本：`__init__OK.py:251-255`（无 `while`）、`__init__OK.py:537 + 546-547 + 548-552`（凭空 `while True:` 与 `else: return None`，第二 while 内无 sleep）。
- 标本：`b01`（while True+break+尾兄弟，在 if 臂内）/`b02`（无尾兄弟仍错）/`b03`（`while <cond>` 形）/`b05`（臂内 `return` 代替 `break`）/`b12`/`b14`（`while not stop: if TH: return None` + 环后 `return None`；**b14 无 sleep 也错**，说明体尾兄弟不是必要条件）/`b15`。
- 对照（今日 MATCH，修复后必须仍 MATCH）：`b04`（同一循环形放在**函数体尾** ⇒ 正确，与 Round-1 B99「既有函数末守卫有效」同侧）、`b16`（循环在 try 体内）、`b17`（循环在 for 体内）。⇒ 判别维度 = **循环区域的宿主是不是 if 臂 + 出口/汇合块的归属**，不是嵌套深度。
- 违反条款：§1.5 **C3 守卫封闭**（既有「函数尾」守卫的作用域没闭合到 if 臂层，与 B99 同族同判据面）+ §1.2 **原则1 自底向上归约**（内层 while 未作为抽象节点交付父级，父级直接把它摊平成顺序语句）。
- 与 B99/B100 的关系：B107 与 **B99** 共用出口/sink 归属判据面（`region_ast_generator.py:2364-2378` 出口计数、`code_generator.py:2232 _filter_trailing_return_none`），是它在「循环 + break/return 臂 + 体尾兄弟」上的另一侧；`while … else: return None` 的凭空 `else` 指向 `_find_loop_else`（`core/cfg/region_analyzer.py:6028`）在 if 臂宿主下的边界判定，此点为**指认候选站点**、非本轮实证结论。

## 4. 靶 #3 `future_contract_info.pyc`（27/29）

### 4.1 单元 `FutureInfoCache.info_conbine` — 第一分歧

```
orig 59 | prod 59（指令条数相同 ⇒ 纯边差异）
唯一真分歧 off66：
  ORIG  POP_JUMP_FORWARD_IF_TRUE → 目标内容 LOAD_GLOBAL,LOAD_CONST,PRECALL,CALL      = raise Exception('Current user is not available') 块(off94)
  PROD  POP_JUMP_FORWARD_IF_TRUE → 目标内容 LOAD_FAST,LOAD_FAST,LOAD_ATTR,LOAD_FAST  = 下一条 elif 的条件块(off68)
同时 off92 的目标内容在两版间互换 ⇒ 两条短路操作数的**跳向互换**。
```
产物文本 `future_contract_infoOK.py:266`：`elif not (username not in self._FutureInfoCache__user_info or self._FutureInfoCache__user_info[username]):`
原始应为：`elif username not in self._FutureInfoCache__user_info or not self._FutureInfoCache__user_info[username]:`
二者**不等价**（前者 = `in and falsy`，后者 = `not in or falsy`），既错语义又错边。

### 4.2 单元 `FutureInfoCache.check_user` — 第一分歧

```
orig 166 | prod 173（+7）
首个真分歧 off462/464：
  ORIG  off460 CONTAINS_OP 1 / off462 POP_JUMP_FORWARD_IF_TRUE → 目标内容 LOAD_FAST,LOAD_ATTR,LOAD_METHOD,PRECALL = self.lock.acquire() 块(off490)
  PROD  off460 CONTAINS_OP 1 / EXTENDED_ARG 1 / off464 POP_JUMP_FORWARD_IF_TRUE → 目标内容 LOAD_CONST,RETURN_VALUE      = 函数尾 return
  且 PROD off466 起的落体 = ORIG 的 `self._FutureInfoCache__user_info[username]` 下标块 ⇒ 两条臂的内容与跳向被整体换位。
第二处 insert（prod[141:147]，off820 区）= 多出的 6 条 `self.lock.release()` 指令 = finally 块被按 PROD 的臂归属复制了一份（下游后果，非独立缺陷）。
```
产物文本 `future_contract_infoOK.py:168`：`if not (username not in self._FutureInfoCache__user_info.keys() or self._FutureInfoCache__user_info[username]):` —— 与 §4.1 **同一构造**（`A or not B` 被写成 `not (A or B)`），只是宿主更复杂（try/except/finally + 返回值 1/2/0）。

### 4.3 两单元同一构造：是

`info_conbine` off66 与 `check_user off462` 的差都是**同一条 `or not <真值>` 短路链的臂跳向互换**，操作数类型同为「CONTAINS_OP + truthiness-not」，产物文本同形（`not (A or B)`）⇒ 一条登记 B108，两个锚点。

### 4.4 B108 登记

**B108 — 混合极性 `or` 链（首成员 IF_TRUE→then、次成员 IF_TRUE→else 的真值取反操作数）被整体取反成 `not (A or B)`，而不是逐操作数还原 `A or not B`：语义不等价 + 两条臂的跳转目标互换**
- 锚点：`info_conbine` off **66 `POP_JUMP_FORWARD_IF_TRUE`** 目标内容由 `LOAD_GLOBAL…(raise)` 变为 `LOAD_FAST,LOAD_FAST,LOAD_ATTR…`（off92 同步互换，指令条数不变）；`check_user` off **462→464（+EXTENDED_ARG 1）** 目标内容由 `LOAD_FAST,LOAD_ATTR,LOAD_METHOD,PRECALL`（acquire）变为 `LOAD_CONST,RETURN_VALUE`（函数尾）；`+7` 来自 finally 的 `release()` 被复制。
- 标本：`r2v3_c01`（info_conbine 原形：elif 链 + 3 处 raise）/`c02`（最小形：函数体 + 单条 `A or not B` if）/`c06`（check_user 原形：`.keys()` + try/except/finally + 返回 1/2/0）/`c08`（`x != 1 or not y` ⇒ 判别维度不是 `not in`）/`c09`（方法宿主）/`c12`（三操作数链）。
- 对照（今日 MATCH，修复后必须仍 MATCH）：`c03`（只留单操作数 —— `c02`→`c03` 的唯一改动即删掉第二操作数，判定由 failure 翻回 success）、`c04`（源码**直接写** `not (A or B)` ⇒ 证明产物当前发射的文本本身能被正确编译，缺陷在选形不在发射）、`c05`/`c13`（`and` 形）、`c07`（**两操作数都是 `is None`** ⇒ MATCH，把 B108 与 B105 的判据面清晰分开：None 恒等比较走 `_flip_is_none_compare`，真值/成员取反走本条）；宿主扩展臂 `c10`（try 体内）与 `c11`（循环体内 + 臂为 `continue`）实测**今日即 MISMATCH**，故它们也是标本而非对照（见 §5 表）。
- 违反条款：§1.2 **原则4 入口引用语义**（短路链的「哪个操作数真 → 哪个入口」引用关系被整体取反）+ **原则2**（then 臂终态块/次条件块归属互换）+ §1.5 **C2 黑箱组合**（条件子结构被按整体取反展开，而不是按每个操作数自己的出边组合）。
- 与既有守卫的关系：`core/cfg/region_analyzer.py:29670-29682` 的 **[R14c 修复·负极性 or 链不归一]** 分支明文「全员 IF_TRUE 族跳转且**目标同一块**（`_w14_uniform and all(t is _w14_tgt_blocks[0] …)`）的链是 `not (A or B)` 的编译形态，必须整体取反发射；若按 De Morgan 归一会被二次取反」，并把「混合极性链（如 `A and not B`：首成员 IF_FALSE、后续 IF_TRUE）」划给 and 路径。**B108 正是落在这两条划分之间的第三种形状：全员 IF_TRUE 但目标不统一（then 与 else 各一）** —— 它的 `_w14_uniform` 为真、`all(t is 同一块)` 为假，按该注释应走 and/逐项 implicit-not 路径，但实测产物发射了整体取反形。指认的消费侧站点（grep 核实存在）：`region_ast_generator.py:104 _negate_expr`、`:146 _flip_contains_compare`（`not in`↔`in` 的运算符翻转）、`:163 _fallthrough_cond_for_jump`（「按 opname 极性分类」的归约方式表）。**本条为判据划分归属的指认，非对 29670 行的改动建议。**

## 5. 复现电池（`test_repros/round2/`，前缀 `r2v3_`）

生成方式＝写 `.py` → `py_compile` 到同名 `.pyc` → `pycdc.py -o <base>OK.py` → 判据 `single`。索引 `test_repros/round2/r2v3_probe_index.json`（56 臂）。

| 臂 | 今日判定（判据原文） | 修复后要求 | 证明什么 / 标本↔对照的唯一改动 |
|---|---|---|---|
| **B104**（靶 #1 `get_tick_direction`） | | | |
| `r2v3_a13_loop_break_chain_join_return` | **MISMATCH** `units=1/2` | success | 最小标本：for 体内 `if i: break` + if/elif 链 + 链汇为终态 `return redata` + 环后兄弟。→ 把 `return redata` 换成 `redata = clean(redata)` 即 `a14` **MATCH** |
| `r2v3_a16_while_host_break_chain_join` | **MISMATCH** `1/2` | success | 宿主换 while，同一判据 |
| `r2v3_a17_ifelse_arms_break_chain_join` | **MISMATCH** `1/2` | success | 两臂（if/else）即可，不需 elif ⇒ 与臂数无关 |
| `r2v3_a19_or_isnone_join_in_loop_break` | **MISMATCH** `1/2` | success | `or`-None 链的终态 then 臂在同宿主下同样外推（B104×B105 交叉形） |
| `r2v3_a22_method_host_break_chain_join` | **MISMATCH** `2/3` | success | 类方法宿主（`<module>.C.m`） |
| `r2v3_a23_postloop_sibling_is_return` | **MISMATCH** `1/2` | success | 环后兄弟本身也是 `return None` 时仍错 |
| `r2v3_a24_module_host_raise_join` | **MISMATCH** `0/1`（`<module>` 整块失败） | success | 模块体宿主 + 汇为 `raise SystemExit` ⇒ 与函数/return 无关，终态即触发 |
| `r2v3_a14_control_join_plain_stmt` | MATCH `2/2` | 必须仍 MATCH | 唯一改动：终态 `return redata` → 普通赋值 ⇒ 决定性对照 |
| `r2v3_a15_control_no_break_in_loop` | MATCH `2/2` | 必须仍 MATCH | 唯一改动：删掉体内 `if i: break`（去掉跨区域入边） |
| `r2v3_a18_control_nothing_after_loop` | MATCH `2/2` | 必须仍 MATCH | 唯一改动：删掉环后兄弟 `if redata:` |
| `r2v3_a20_or_isnone_inside_try` / `a21_or_isnone_nested_in_elsearm` | MATCH `2/2` | 必须仍 MATCH | try 体 / else 臂宿主下的 B105 形（证明 B105 需 B104 宿主才显形） |
| `r2v3_a01…a12`（第一轮 12 臂） | 全 MATCH | 必须仍 MATCH | **诚实记录：这 12 臂未能复现靶 #1**（链汇为终态块但无跨区入边、或宿主为函数/try/while/模块）⇒ B104 的宿主判据由 a13+ 补上，B105 仍无独立合成孪生（§2.5） |
| **B107**（靶 #2 `_on_publish_after_trading_end` 及 `_save_testds` 第二环） | | | |
| `r2v3_b01_whiletrue_break_tail_in_if` | **MISMATCH** `1/2` | success | 最小标本：`if is_end:` 内 `while True: if TH: break / time.sleep` + 环后兄弟。→ 移到函数体尾即 `b04` **MATCH** |
| `r2v3_b02_whiletrue_break_no_tail` | **MISMATCH** `1/2` | success | 去掉体尾 `time.sleep` 仍错 ⇒ 尾兄弟非必要条件 |
| `r2v3_b03_whilecond_break_tail_in_if` | **MISMATCH** `1/2` | success | `while <cond>` 形同族（非只有 `while True`） |
| `r2v3_b05_whiletrue_return_tail_in_if` | **MISMATCH** `1/2` | success | 臂内 `return` 代 `break` 同族 |
| `r2v3_b12_whiletail_return_after_if_arm` | **MISMATCH** `1/2` | success | `_save_testds` 第二环原形（`while not stop: import/if TH: return/sleep` + 环后 `return None`） |
| `r2v3_b14_whiletail_return_no_tailstmt` | **MISMATCH** `1/2` | success | b12 去掉 sleep 仍错 ⇒ 与 B106 的 sleep 丢失解耦 |
| `r2v3_b15_whiletail_break_after_if_arm` | **MISMATCH** `1/2` | success | b12 的 `return`→`break` 侧仍错 |
| `r2v3_b04_whiletrue_break_tail_toplevel` | MATCH `2/2` | 必须仍 MATCH | **函数体尾宿主**对照（B99 的既有函数末守卫侧） |
| `r2v3_b16_whiletrue_break_tail_inside_try` | MATCH `2/2` | 必须仍 MATCH | 循环宿主换 try 体 |
| `r2v3_b17_whiletrue_break_tail_inside_for` | MATCH `2/2` | 必须仍 MATCH | 循环宿主换 for 体 ⇒ 缺陷专属「if 臂内」 |
| **B106**（靶 #2 `_save_testds_to_csv`） | | | |
| `r2v3_b06_except_continue_in_while` | **MISMATCH** `1/2` | success | 最小标本：`while not stop: try: … except ValueError: continue` + try 后语句。→ `continue`→`pass` 即 `b08` **MATCH**（唯一改动，两判据原文见 §3.4） |
| `r2v3_b07_except_continue_nothing_after_try` | **MISMATCH** `1/2` | success | try 之后无语句也错 ⇒ 不只是「直落兄弟」，回边本身丢失 |
| `r2v3_b09_except_continue_method_host` | **MISMATCH** `2/3` | success | 类方法宿主 |
| `r2v3_b10_except_continue_in_try_finally` | **MISMATCH** `1/2` | success | try 套 try + finally（真实单元含 finally） |
| `r2v3_b11_except_continue_inside_with` | **MISMATCH** `1/2` | success | with 宿主 |
| `r2v3_b13_except_break_in_while` | **MISMATCH** `1/2` | success | 处理器里 `break`（第二个跨区目标种类） |
| `r2v3_b18_except_continue_try_else` | **MISMATCH** `1/2` | success | try/else 形 |
| `r2v3_b08_except_pass_then_stmts` | MATCH `2/2` | 必须仍 MATCH | **b06 的对照**（`pass` 代 `continue`） |
| `r2v3_b19_except_continue_nested_while` | MATCH `2/2` | 必须仍 MATCH | 外层再套 while ⇒ 现判据在该成员关系下正确，禁「一刀切拒绝处理器回边」 |
| **B108**（靶 #3 两单元） | | | |
| `r2v3_c01_or_not_operand_elifchain` | **MISMATCH** `1/2` | success | info_conbine 原形（elif 链 + 3 raise）。→ 删掉第二操作数即 `c03` **MATCH** |
| `r2v3_c02_or_not_operand_plain` | **MISMATCH** `1/2` | success | 最小标本（函数体单条 if） |
| `r2v3_c06_keys_call_second_operand` | **MISMATCH** `1/2` | success | check_user 原形（`.keys()` + try/except/finally + return 1/2/0） |
| `r2v3_c08_or_not_compare_operand` | **MISMATCH** `1/2` | success | `x != 1 or not y` ⇒ 与 `not in` 无关，`or not <真值>` 即触发 |
| `r2v3_c09_method_host_or_not_operand` | **MISMATCH** `2/3` | success | 类方法宿主 |
| `r2v3_c10_inside_try_or_not_operand` | **MISMATCH** `1/2` | success | if 在 try 体内仍错 |
| `r2v3_c11_inside_while_or_not_operand` | **MISMATCH** `1/2` | success | if 在循环体内 + 臂为 `continue` |
| `r2v3_c12_or_three_operands` | **MISMATCH** `1/2` | success | 三操作数链 ⇒ 与链长无关 |
| `r2v3_c03_control_single_operand` | MATCH `2/2` | 必须仍 MATCH | c02 去掉第二操作数（决定性对照） |
| `r2v3_c04_control_explicit_not_or` | MATCH `2/2` | 必须仍 MATCH | 源码直接写 `not (A or B)` ⇒ 产物当前选形本身可正确编译，缺陷在选形 |
| `r2v3_c05_control_and_form` / `c13_and_not_operand_control` | MATCH `2/2` | 必须仍 MATCH | `and` 形（`in and not x` / `in and x`）不受影响 |
| `r2v3_c07_or_isnone_two_operands` | MATCH `2/2` | 必须仍 MATCH | 两操作数皆 `is None` ⇒ B108 专属真值/成员取反，与 B105 的 None 路径分开 |

**电池汇总（本轮实测原文，`batch --index`）**

```
$ python -X utf8 scripts/pyc_verify.py batch --index test_repros/round2/r2v3_probe_index.json --json D:/Temp/rrv3/r2v3_battery.json
files_total=56  units_success=85/114  success_rate=0.7456140350877193
files_by_status={'compile_error': 0, 'error': 0, 'failure': 29, 'success': 27}   elapsed_sec=2.9
```
即 **29 臂今日 MISMATCH（标本，修复后必须全部转 MATCH）/ 27 臂今日 MATCH（对照，修复后必须保持 MATCH）**，无 error/compile_error。
分族：B104 = 7 标本 / 17 对照（含第一轮 12 臂全对照）；B106 = 7 标本 / 2 对照；B107 = 7 标本 / 3 对照；B108 = 8 标本 / 5 对照；B105 = **0 标本**（真文件独立承担，§2.5）。合计 29 标本 + 27 对照 = 56 臂，与上表逐条吻合。

## 6. 目录冲突声明（交付路径）

`test_repros/round2/` 是既往 campaign（`adversarial-complete-forms-v2-10rounds` 等）的**已跟踪**目录，内含 224 个旧文件与旧索引 `test_repros/round2/r2_probe_index.json`（42 臂，mtime 2026-10-05 18:49）。任务书要求的索引文件名与之冲突。**本轮未覆盖、未删除、未改名任何旧文件**，改用 `r2v3_*` 前缀 + 索引 `test_repros/round2/r2v3_probe_index.json`，格式与 `r2_probe_index.json` 逐字相同（`[{"path": "test_repros/round2/<x>.pyc"}, …]`），可被 `batch --index` 直接消费。主 agent 若要求严格占名，需先处置旧 42 臂索引。

## 7. Round-1 残留两条：分歧钉桩（未重建电池）

| 单元 | 今日 `single` | 第一分歧（内容标签比对，本轮实测） | 与登记的关系 |
|---|---|---|---|
| `IQCommon/data/finance.pyc` / `<module>.get_fields` | `status=failure units=31/32` | off92 `JUMP_FORWARD`：ORIG 目标内容 `LOAD_FAST(table),LOAD_CONST,BINARY_SUBSCR,LOAD_CONST`（=紧随 if/else 链的同层兄弟语句块，Round-1 记录的 orig 目标 236）vs PROD 在 off92 插 `EXTENDED_ARG 1` 后 off94 `JUMP_FORWARD` 目标内容 `LOAD_FAST,RETURN_VALUE,PUSH_EXC_INFO,LOAD_GLOBAL`（=函数尾，Round-1 记录 742） | **与 Round-1 §6.1 逐位一致 ⇒ B100 未闭，读数未变**。EXTENDED_ARG 是真外推的后果而非对齐伪影（目标块内容同时改变） |
| `IQCommon/logger/handlers.pyc` / `<module>.TWHThreadController._target` | `status=failure units=29/30` | orig[74:76] **delete**：ORIG off404/406 与 off408/410 两个 `LOAD_CONST None; RETURN_VALUE` sink，PROD 只剩一个；off402 `POP_JUMP_BACKWARD_IF_TRUE`（循环头）后随的「循环从未进入」出口边改投合并后的单 sink | **与 Round-1 §7.1 逐位一致 ⇒ B99 仍 un-closed**，本轮无新增信息（未重跑其电池） |

## 8. 未完成 / 风险

1. **B105 无最小合成孪生**（§2.5）：24 臂 A/A2 里 5 臂专门试它的宿主形全 MATCH，只有 B104 宿主下的 `a19` 复现同症状。修复工程师需以真文件 `real_quote.pyc` 的 45 单元读数为验收面，并对 `_flip_is_none_compare` 做插桩才能定位认领点。
2. B107 的 `while … else: return None` 凭空 else 指向 `_find_loop_else`，**属候选指认**，本轮未插桩证明。
3. 未跑 402 全量/八分片/34 套（硬约束）。本轮只跑：3 靶 + 2 残留的 `single`、56 臂 `batch --index`、以及靶内 pyc↔OK.py 只读逐指令比对。
4. 回归哨兵：`r2v3_b04/b08/b16/b17/b19`（B106/B107 的 MATCH 面）、`r2v3_a14/a15/a18/a20/a21`（B104 的 MATCH 面）、`r2v3_c03/c04/c05/c07/c13`（B108 的 MATCH 面）任何一个在修复后转 MISMATCH 即为过伸展。Round-1 的 `test_repros/round1/r1_probe_index.json`（108/110）与 `r1_regress_index.json`（34/34）必须同批复跑。
5. 破口汇总：B104/B105/B106/B107/B108 五条，均为**成员关系/宿主区域类型形**，无一条为深度形（§1.5 推论的直接用法：修守卫，不加深度门控）。
