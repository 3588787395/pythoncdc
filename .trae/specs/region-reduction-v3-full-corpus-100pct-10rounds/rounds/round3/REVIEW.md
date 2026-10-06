# Round 3 — 测试工程师 REVIEW（诊断 only，零生产代码改动）

- 工作树 `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`，分支 `rr-v3r01-f557fd`，`python -X utf8`（3.11.7），未设 `PYTHONIOENCODING`
- 唯一判据 `scripts/pyc_verify.py single` / `batch --index`（**未改判据、未写替代 checker**）
- 三个靶**按序逐个**完成（1 order_api → 2 klinedata → 3 wizard_quant_api），全部产物「先删 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」重生成，**未手改任何 `*OK.py`**；未触碰 `core/** pycdc.py bytecode/** parsers/** utils/** scripts/pyc_verify.py`
- 测试侧工具（本轮新建，只读用途，全在 `test_repros/round3/`）：`_r3gen.py`（靶 1 标本+三步电池）、`_r3gen_f2.py`（靶 2）、`_r3gen_f3.py` + `_r3gen_f3b.py`（靶 3）、`_r3diag_f3.py`（**重名嵌套 code object 的按位配对**：`<genexpr>` 同名多份，`_r2diag` 的名字匹配只能命中第一份，故自建）；逐指令比对复用既往 `test_repros/round2/_r2diag.py`（跳转操作数→目标块内容标签）
- 全部命令 rc=0 且 <300s（最长：靶 2 `pycdc` 3.8s + `single` ≈5s；52 臂 `batch --index` 1.4s）

## 0. 靶读数（本轮实测原文，非沿用基线）

| # | pyc | 实测 | 失败单元（判据原文） |
|---|---|---|---|
| 1 | `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | `status=failure units=34/37` | `<module>.base_order`、`<module>.future_order`、`<module>.option_order` 均 `Failure: Different control flow` |
| 2 | `site-packages/IQCommon/api/klinedata.pyc` | `status=failure units=61/64` | `<module>.get_kline_by_count_new`、`<module>.get_multiminute_his_data`、`<module>.kline_datetime_list` 均 `Different control flow` |
| 3 | `site-packages/IQCommon/strategy/wizard_quant_api.pyc` | `status=failure units=55/58` | `<module>.filter_desicion`、`<module>.get_DMI.calculate_di.<genexpr>`（两条，同名两份）均 `Different control flow` |

与任务书读数逐位一致（三靶九单元全部复现，无一消失、无一换人）。

## 1. 判据口径与伪影排除（本轮实际用到的规则）

`_r2diag.py diff` 把每条跳转操作数替换为**目标块内容标签**，故「目标偏移移动而目标块不变」自动判等。本轮另按既往教训（Round-2 §2.2）显式排除**标签越界伪影**：目标块内容相同、差异只在目标块之后的邻块 ⇒ 不是本单元的边差异。

| 伪影 | 出现处 | 判定 |
|---|---|---|
| 行号位移（orig ln133-148 ↔ prod ln90-100 等） | 九单元全部 | 伪影，产物行号自 1 起，不参与判据 |
| 目标偏移 +2/+4 位移、目标块内容不变 | 靶 1 `base_order` off858/860/864 等 | 伪影（内容标签比对自动判等） |
| **标签越界**：`get_multiminute_his_data` off822 `JUMP_FORWARD` 标签 `LOAD_FAST,RETURN_VALUE` vs `LOAD_FAST,RETURN_VALUE,LOAD_GLOBAL,LOAD_FAST` | 靶 2 单元 2 | **伪影，已排除**：两版目标块前 2 条同为 `LOAD_FAST(his_data_dict),RETURN_VALUE`，差在邻块；真正的该单元首分歧在 off1470/2708（§3.2） |
| **标签越界**：`kline_datetime_list` off544 `POP_JUMP_IF_FALSE` 两版标签同为 `LOAD_FAST,POP_JUMP_FORWARD_IF_TRUE,…` | 靶 2 单元 3 | **伪影，已排除**；真首分歧在同区域后一条 off558（§3.3） |
| **标签越界**：`filter_desicion` off700 `POP_JUMP_IF_FALSE` 两版目标块内容同为 `LOAD_CONST,RETURN_VALUE` | 靶 3 单元 1 | **伪影，已排除**；真首分歧 off704（§4.1） |
| `EXTENDED_ARG` 插入 | `kline_datetime_list` off558(+`EXTENDED_ARG 2`)、`filter_desicion` 无、靶 1 无 | **不可豁免**（§5.3）：与「目标块内容同时改变」同现，是跳距算术后果；`get_kline_by_count_new`/`multiminute` 两侧 EXTENDED_ARG 逐位相同，属等值 |
| `LOAD_CONST <code object <genexpr>>` 的 repr（地址/co_filename） | 靶 3 宿主 `<module>.get_DMI.calculate_di` off156/off 两处 replace | 伪影（判据对嵌套 code 递归比较且元数据豁免）⇒ **宿主 90↔90 指令、除这两行外零分歧**（§4.3） |

## 2. 靶 #1 `order_api.pyc`（34/37）—— 三单元同一构造

### 2.1 每单元第一分歧（原文行）

| 单元 | orig/prod 指令数 | 首分歧 |
|---|---|---|
| `base_order` | 200 / 200（**条数相同 ⇒ 纯边差异**） | off **890** `POP_JUMP_FORWARD_IF_TRUE`：ORIG 目标内容 `LOAD_FAST,LOAD_ATTR,RETURN_VALUE`，PROD 目标内容 `LOAD_CONST,STORE_FAST,JUMP_FORWARD,LOAD_FAST` |
| `future_order` | 115 / **99**（−16） | off **412** 同一 opcode：ORIG 目标 `LOAD_FAST,LOAD_ATTR,RETURN_VALUE`，PROD 目标 `JUMP_FORWARD,NOP,LOAD_FAST,LOAD_ATTR`；其后 88/91/93/98/100 号 replace 全是同一臂重归属的下游 |
| `option_order` | 94 / **85**（−9） | off **204** 同签名（ORIG 目标 `LOAD_FAST,LOAD_ATTR,RETURN_VALUE` → PROD `JUMP_FORWARD,NOP,LOAD_FAST,LOAD_ATTR`） |

块级决定性事实（`base_order`）：

| | ORIG | PROD |
|---|---|---|
| off890 `POP_JUMP_IF_TRUE`（紧随 `LOAD_GLOBAL is_trade/PRECALL 0/CALL 0`） | `succ=['jump:197','fall:155']` | `succ=['jump:164','fall:155']` |
| 终态块 off1124 `LOAD_FAST order_obj; LOAD_ATTR order_id; RETURN_VALUE`（ln148） | **preds=[154, 196]**（臂跳 + 臂体末 `POP_TOP` 落穿） | **preds=[196]**（只剩 1 条） |
| off892 起臂体（`asset.symbol[:2] in ('11','12')` → `info=`可转债 / `info=`股 → `strategy_log.info(...)`） | 只在 `is_trade()` 假路执行 | 变成 `elif is_trade() or asset.symbol[:2] in ('11','12')` 的两臂，**无条件执行** |

原始形状（行号取自 ORIG 行追踪，137-148）：

```python
if order_obj is None:        # 137 -> 138 return None
    return None
if not is_trade():           # 139  POP_JUMP_IF_TRUE -> 函数尾终态 return
    if asset.symbol[:2] in ('11', '12'):   # 140
        info = '…可转债…'                    # 141
    else:
        info = '…股'
    strategy_log.info(info.format(...))    # 144-147
return order_obj.order_id    # 148  ← 终态块，被两条路径汇入
```

产物文本（`order_apiOK.py:56-63`）把它写成 `if order_obj is None: return None / elif is_trade() or asset.symbol[:2] in ('11','12'): info=… / else: info=… / strategy_log.info(...) / return order_obj.order_id` —— **臂跳从「跳过日志直达尾 return」改成「进入日志臂」**，`is_trade()` 为真时原始永不执行的 `strategy_log.info` 现在必然执行 ⇒ 语义与边同时不等价。`future_order`/`option_order` 同一条边外，臂体语句进一步被毁形（`order_apiOK.py:227-235`：`elif is_trade() or …: pass / else: """卖出"""`、`side = …` 退化为裸表达式、`strategy_log.info(...)` 整条丢失 ⇒ −16 / −9）。

### 2.2 跨单元家族分析（任务书点名的 lead）

**是同一构造形，且三处 offsets 完全同签名**：三条臂头都是 `LOAD_GLOBAL is_trade → PRECALL 0 → CALL 0 → POP_JUMP_FORWARD_IF_TRUE`，偏移分别 **890 / 412 / 204**，ORIG 目标内容三处都恰好是 `LOAD_FAST,LOAD_ATTR,RETURN_VALUE`（各自的 `return order_*.order_id` 终态块），PROD 三处目标都改投臂体首块。三单元的兄弟前驱都是同一条 `if order_ is None: return None`（`base_order` 为 `if order_obj is None`）+ `if not is_trade():` + 函数尾终态 return，`future_order`/`option_order` 只是臂体内容不同（三元 + `.format` 调用 vs 多一层实参）。⇒ **B109 一条登记覆盖三单元；闭掉它该文件应 34/37 → 37/37**（本结论为形状同一性的推论，非本轮实测：本轮未改生产代码，无法验证翻转后读数）。同名单元 `order_api_backtest/order_api_trade` 未进本轮靶，修复面自若命中它们，属同一族的自然外溢。

### 2.3 B109 登记

**B109 — 「前一条臂以终态 return 收束」的 IfRegion 之后紧跟 `if not A(): <臂体>` 时，链构造器把该否定臂并入 elif 并把臂体首条件折进臂条件（`not A` → `A or B`），终态汇合块被臂跳的落点从「尾块」改投「臂体首块」，尾块丢失臂前驱、臂体语句被毁/被丢**

- 锚点：`site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc`
  / `<module>.base_order` off **890**（200=200，纯 `POP_JUMP_IF_TRUE` 操作数：`jump:197`→`jump:164`；终态块 off1124 preds `[154,196]`→`[196]`）
  / `<module>.future_order` off **412**（115→99）
  / `<module>.option_order` off **204**（94→85）。
- 机制（blocks/edges/region-membership 语言）：终态块 `B197` 的正常前驱 = {该 if 自己的臂跳 154, 同臂体末 196}，**两条都落在同一条臂的前向流内** ⇒ `_compute_arm_level_join` 判据 (4) 的「箱数 = 1 ⇒ J 在单条臂内部（子区域的汇合点，属子区域，原则2/3），拒绝并继续向外走」分支命中并弃权；链构造器随后把 `if not A()` 折进 elif（`region_analyzer.py:19038/19275/19281 _main_inline_boolop_chain`，`{'op':'or'}` / `{'op':'or','negate':True}`；消费侧 `region_ast_generator.py:18757 _if_generate_elif_chain`），折叠按「成员真边指向同侧」重排 then/else，**臂的出边不再指向原终态块**，终态块被留在链外且只剩一条前驱；臂体在 `future_order/option_order` 因两臂内容互换而退化发射（`pass` + 裸表达式 + 调用整体丢失）。
- 违反条款：§1.2 **原则2 每块唯一归属**（终态块的臂边被丢弃 ⇒ 归属塌成单臂专属）+ **原则4 入口引用语义**（臂引用被改写成条件折叠而非臂跳）+ §1.5 **C1 局部消费**（`A or B` 折叠消费了本区域出边之外的终态块身份）+ §3.2.3「统一不拆分/不并 any 复合条件」的对应面（此处为不当 `or` 并）。
- 与 Round-2 守卫的关系（点名条件）：**是 `_compute_arm_level_join` 判据 (4) 的第二处欠伸**。Round-2 B104 报的是「箱数 ≥ 2 且 E 箱为空 ⇒ 明文不介入」那一支；本轮是同一判据的 **「箱数 = 1」拒绝支**：被拒的 J 不是子区域内部汇合点，而是**父级兄弟序列里的终态块**（`RETURN_VALUE` 收尾、无后继、其中一条前驱就是本 if 的臂跳本身）。缺的成员条件：拒绝时未区分「J 全部前驱都在同一条臂内且 J 无后继 = 本作用域末尾语句」与「J 在子区域内部」。
- 不是深度形：标本 `r3_a01`（深度 2：函数体 + 一层臂内 if）即 MISMATCH；`r3_a10`（同深度、把 `if not is_trade()` 改为正极性）、`r3_a04`（同深度、臂体去掉嵌套 if/else）、`r3_a02`（同深度、删掉前一条 `if o is None: return None`）同深度全 MATCH ⇒ 判别维度 = **终态块的臂前驱有无 + 臂是否为负极性单臂 + 前一条臂是否终态**，与深度无关（承 Round-1 §9/§11 结论）。

## 3. 靶 #2 `klinedata.pyc`（61/64）—— 三单元三种机制（不合并）

### 3.1 单元 `get_kline_by_count_new`（650/649）→ B110

首分歧 off **974** `POP_JUMP_FORWARD_IF_NONE`：ORIG 目标内容 `LOAD_CONST,STORE_FAST,JUMP_FORWARD,LOAD_FAST`（=then 臂体首块 B216），PROD 目标内容 `LOAD_FAST,GET_ITER,EXTENDED_ARG,FOR_ITER`（=链后的 for 循环头 B228）。

块级决定性事实（同区域逐块对照，B173-B232 两版逐位同构，只有边不同）：

| | ORIG | PROD |
|---|---|---|
| then 臂体块 off1200 `LOAD_CONST 0; STORE_FAST need` | **preds=[180, 182, 192, 215]**（4 条成员真边汇入） | **preds=[192, 215]**（只剩 2 条） |
| off974 `POP_JUMP_IF_NONE` / off978 `POP_JUMP_IF_FALSE`（链首两名成员） | 均 `jump:216`（=臂体） | 均 `jump:228`（=链的汇/其后 `for` 头） |
| off1028 `POP_JUMP_IF_TRUE`、off1198 `POP_JUMP_IF_FALSE` | `jump:216` | 仍 `jump:216` |

即原始 `if fq is None or not dividends_all or (isinstance(fields, str) and 'x' in fields) or (…len(set&set) > 0): need = 0 else: need = 1` 里，**前两名成员（IF_NONE 族、IF_FALSE 族）的真边被从 then 臂入口改投到区域汇合块** ⇒ `need = 0` 在这两条路径上不执行（少 1 条指令 = 该臂的 JUMP 重排后果）。

**B110 — 短路链成员跳族混合（IF_NONE / IF_FALSE / IF_TRUE 共存）且含 `and` 子成员时，非 IF_TRUE 族成员的「真边 = then 臂入口」身份被判成「链出口 = 区域 merge」，then 臂体在这些路径上被跳过**
- 锚点：`site-packages/IQCommon/api/klinedata.pyc` / `<module>.get_kline_by_count_new` off **974 + 978**（臂体块 preds `4→2`）。
- 机制：`region_analyzer.py:28332 _detect_boolop_conditional_chain` 交出的链成员把「真出口」按跳族分派；`region_ast_generator.py:38148 _boolop_mixed_polarity_or_chain` 的认领条件（Round-2 B108 落地判据）明文要求 **「全员 IF_TRUE 族 + 目标分裂为 S 与 F」**，本形状里两名成员是 `IF_NONE`/`IF_FALSE` 族 ⇒ 判据不命中、返回 `None`，随后 `_build_boolop_expression_inner`（`:38454`）/`_if_extract_condition_from_instructions` 走默认极性表，把这两名成员的真边当链尾出口。**是 B108 守卫的欠伸侧，点名条件 = 「全员 IF_TRUE 族」这一条**（同函数其余判据「目标离开必须落在本区域 merge」在本形恰好成立，故不是那条）。
- 违反条款：§1.2 **原则4 入口引用语义**（「哪个操作数真 → 哪个入口」的引用被改成「→ 汇合块」）+ **原则2**（臂体块的边丢失）+ §1.5 **C1**（消费了成员真边的目标身份却未按区域成员关系认领）。
- 标本：`r3_b01`（原形：三名混合链 + then/else + 链后 `for`）/`b02`（链后换普通语句仍错）/`b03`（`if a or not b or isinstance(c,str) and d` ⇒ 与 `is None` 无关，纯跳族混合即触发）/`b06`（方法宿主）/`b07`（汇合块本身是 `return` 仍错）。
- 对照（今日 MATCH、修复后必须仍 MATCH）：`r3_b05`（**b01 删掉第三名字成员 `isinstance… and 'x' in…` ⇒ `NO divergence at all`**，唯一改动的决定性对照）/`r3_b04`（`if a and b or c and d` 全 IF_FALSE 首族 ⇒ 现判据正确，禁「一刀切拒绝混合链」）。

### 3.2 单元 `get_multiminute_his_data`（535/536，+1）→ B111

off822 的首个 `replace` 已按 §1 判为**标签越界伪影并排除**。真首分歧在循环出口/尾块归属：

| | ORIG | PROD |
|---|---|---|
| `for symbol in symbols` 的 FOR_ITER(off1470) 跳目标 | B518 off2708 `JUMP_FORWARD → 533`（**preds=[275]，纯跳块**） | B518 off2708 `LOAD_FAST his_data_dict; RETURN_VALUE`（**preds=[161, 275]**） |
| 尾块 off2758 `LOAD_FAST his_data_dict; RETURN_VALUE`（ln1095） | **preds=[161, 518, 532]** 三条汇入 | **该块不存在** |
| ln1093 语句块（`his_data_dict = get_kline_by_count_new(...)`，ORIG off2710 / PROD off2712） | preds=[19,24]，**succ 落穿 → 尾 return** | preds=[19,24] 不变，**落穿 → 新增 off2760 `LOAD_CONST None; RETURN_VALUE`（preds=[533]）** |

即：循环的自然出口把**函数尾的终态 `return his_data_dict` 就地材料化**（该 return 的三条汇入边塌成 2 条），而真正穿过 ln1093 赋值的那条路径改为落到**凭空生成的隐式 `return None`**（+1 指令恰为 `LOAD_CONST None`）⇒ 该路径返回值由 `his_data_dict` 变成 `None`，语义不等价。

**B111 — 区域（LoopRegion）自然出口的汇合块与函数尾终态 `return <expr>` 共享时，终态 return 被在出口位置材料化，另一条穿过区域后顺序语句的同值返回被改投为凭空 `return None` 隐式尾**
- 锚点：`site-packages/IQCommon/api/klinedata.pyc` / `<module>.get_multiminute_his_data` / orig off **2708（JUMP_FORWARD→2758）+ 2758 尾块 preds [161,518,532]** vs prod off **2708（就地 `LOAD_FAST,RETURN_VALUE`）+ 2760 凭空 `LOAD_CONST None,RETURN_VALUE`**。
- 机制（候选站点，均已 grep 核实存在，非本轮实证插桩）：Round-2 B107 落地的 **「循环出口之后的顺序代码交外层在其自身位置发射一次」** 那一步（`core/cfg/region_ast_generator.py:24595 _r2_b107_block_is_outer_exit`、`:24625 _loop_preheader_blocks`、`:24517 _arm_loop_child_entry` 判据 (e)「block 不是 region 或任一祖先区域的 merge_block」）在「出口块本身是一条纯跳、其目标 = 函数尾终态 return」这一成员关系下，把终态 return 的**位置**当成了出口的顺序延续；函数尾侧则由 `core/cfg/code_generator.py:2232 _filter_trailing_return_none` 家族补出隐式 `return None`。**指认到面，不指认到行**：本轮未插桩，B107 §6.3 已把「臂内 `return`/sink 互换」归到 B99 的出口/sink 归属轴，本条是它在 **LoopRegion 自然出口 + 跨区域共享终态 return** 上的另一侧。
- 违反条款：§1.5 **C3 守卫封闭**（终态块被区域外两条路径引用时未显式认领唯一发射点）+ §1.2 **原则2**（终态块三条汇入边塌成两条）+ **原则1**（区域出口交付的「出口后顺序代码」与其自身汇合出口未分离）。
- 标本：`r3_b09`（`if a: res=mk(1) / else: for…break / for-else: res=mk(x)` + 尾 `return res`；首分歧 off36 `JUMP_FORWARD → LOAD_FAST,RETURN_VALUE` 1→2 条，同签名）/`r3_b10`（`if cond: for… / else: x=mk(1) / return x`，off44 同签名）。
- 对照（今日 MATCH，修复后必须仍 MATCH）：`r3_b08`（同形但 break 前无跨区共享终态：`if a: res=mk(1)` 在循环外）/`r3_b11`（`for…else` 汇在函数尾但循环体无中途 `break` 臂）/`r3_b12`（`if cond: for…if s: break… / else: x=mk(1)`）。**b10 ↔ b12 的唯一改动 = 循环体内那条 `if s: break` 的有无** ⇒ 判据维度 = 区域出口是否存在「纯跳出口块 + 与函数尾终态共享」，不是深度。

### 3.3 单元 `kline_datetime_list`（413/417，+4）→ **既有破口 B100/B104 的新实例，不另立编号**

off544 首个 `replace` 判为标签越界伪影（两版目标内容同串）并排除。真首分歧 off **558**（PROD 处 `EXTENDED_ARG 2 + POP_JUMP_FORWARD_IF_TRUE`）：

| | ORIG | PROD |
|---|---|---|
| `include` 的臂边 | `jump:165` | `jump:415` |
| 汇合块 off666（ln1241，链后同层兄弟语句首块） | **preds=[133, 139, 145, 154, 160, 164]（6 条）** | **preds=[157, 164]（2 条）** |
| 被改投的目标 | — | off1712 `LOAD_FAST; RETURN_VALUE`（**函数尾 sink**，preds 由 `[72,83,279,294,300,414]` 变为新增 134/141/148 三条） |

原始 `if not include and frequency == Frequency.MINUTE.value and query_date not in (am_open, pm_open) and (…)` 的**链出口（6 前驱同层兄弟汇）被取成函数尾 sink**，链后语句被吸收进臂（+4 = 被重排/复制的尾部指令）。这正是 Round-1 **B100**（IfRegion 臂的 merge/join 取成外层作用域尾 ⇒ 紧随 if 链之后的同层兄弟被吸收）与 Round-2 **B104**（终态汇合块因 E 箱/箱数判据弃权后 merge 外推）的已登记机制在本语料上的第三个实例（前例：`finance.get_fields` off92、`real_quote.get_tick_direction` off1102）。**按「不得把已知机制重报为新破口」的要求，本轮只补锚点与标本，不另立 B 编号。**
- 补充判据事实（供 B104/B100 修复参考，非新条）：本形的链**首成员是 `not X` 的 IF_TRUE 跳**、其余成员是 IF_FALSE 跳，且所有成员真/假边**同指一个 6 前驱兄弟汇块**——与 B108（目标分裂 S/F）与 B110（跳族混合且真边指臂体）都不同；`_compute_arm_level_join` 判据 (4) 在此应命中（E 箱非空、箱数 ≥ 2），但实测边仍被外推 ⇒ 该单元的第一消费点**未在本轮定位**（如实状态：已定位到锚点，未定位到站点）。
- **标本缺口如实登记**：`r3_b13/b14/b15`（三臂 `not X and A and B` 链 + 链后兄弟 + 尾 return）今日**全部 MATCH** ⇒ 本轮**未能**为 `kline_datetime_list` 造出最小合成孪生（与 Round-2 B105 同样处境）。验收面须用真文件 `klinedata.pyc` 的 64 单元读数。

## 4. 靶 #3 `wizard_quant_api.pyc`（55/58）

### 4.1 单元 `filter_desicion`（195/197，+2）→ B112

off700 首个 `replace` 判为标签越界伪影并排除。真首分歧 off **704** `POP_JUMP_FORWARD_IF_NONE`：

| | ORIG | PROD |
|---|---|---|
| `short_values is None` 成员真边 | `jump:181` | `jump:195` |
| 共享 then 臂块 off710 `LOAD_CONST None; RETURN_VALUE`（ln135） | **preds=[178, 180]**（两成员汇入同一 sink） | **preds=[180]**（只剩第二条成员） |
| off774 `LOAD_CONST None; RETURN_VALUE`（**尾后新增，+2**） | 不存在 | **preds=[178]** ⇒ 首成员被改投到凭空复制的第二条 sink |

产物文本（`wizard_quant_apiOK.py:93-98`）：`elif filter_type == 'short_status' and short_values is not None:` + `if long_values is None: return None else: return down_v_desicion(...)`，另有 `if not short_values is not None or long_values is not None:`（`is None` 被写成 `not … is not None` 的双重取反）。即：**elif 臂与后随 if 的短路链被 `and` 并条件，链首成员的真边不再汇入两成员共享的 then sink，而是复制出第二条 sink 挂在函数最后一个块之后**。语义虽同为 `return None`，判据口径（控制流结构）不等价，且 `and` 并条件改变了 `filter_type` 测试的相对次序。

**B112 — if/elif 链臂内「多成员同 sink 短路链」被并入臂条件（`and`）后，链首成员的真边不再汇入成员共享的 then 臂终态块，而是指向在函数末块之后复制出的第二条同值终态块（终态 sink 复制 + 边重投）**
- 锚点：`site-packages/IQCommon/strategy/wizard_quant_api.pyc` / `<module>.filter_desicion` / orig off **704 `POP_JUMP_IF_NONE → 710`（共享 sink preds=[178,180]）** vs prod off **704 → 774（新增 preds=[178] 的第二 sink；710 只剩 preds=[180]）**，+2 指令恰为该复制体。
- 违反条款：§1.2 **原则2 每块唯一归属**（同值终态块被复制 ⇒ 一条边被两条块争抢）+ **原则4**（成员真边 → 臂入口的引用被改投）+ §1.5 **C1**（臂内链的条件被外提并入 elif 臂条件，消费了臂级而非链级的汇合事实）+ §3.2.3「统一不拆分/不并复合条件」的对应面（不当 `and` 并）。
- 站点（grep 核实存在）：`region_ast_generator.py:18757 _if_generate_elif_chain`（elif 臂条件折叠与终态块发射）、`region_analyzer.py:21166 _check_elif_chain`（`inner_merge ≠ merge_` 的 elif 阻断判据，本轮形状未被阻断）、`code_generator.py:2232 _filter_trailing_return_none`（尾 `return None` 家族）。
- 标本：`r3_c12`（三臂 elif 链原形）/`r3_c17`（去掉链后 `return None` 仍错）/`r3_c18`（臂体不带 `[-1]` 下标仍错）/`r3_c22`（三成员链仍错）。
- 对照（今日 MATCH，修复后必须仍 MATCH）：`r3_c13`（同链但只有 `is None`/`is not None` 两形之一）、`r3_c19`（**c18 把 `or` 链改成单成员 `if sv is None:` ⇒ MATCH**，决定性对照）、`r3_c20`（**c18 把 elif 换成普通 `if` 臂 ⇒ MATCH**：缺陷专属 elif 链层）、`r3_c21`（**c18 把 then 臂的 `return None` 换成 `return 0` ⇒ MATCH**：专属 None-sink 复制）、`r3_c14`（`and` 而非 `or`）、`r3_c15`（then 臂是语句不是 return）、`r3_c16`（最小单层形）。

### 4.2 单元 `get_DMI.calculate_di.<genexpr>` ×2（各 64/50，−14）→ B113

两份同名 `<genexpr>`（`_r2diag` 按名只命中第一份且报 `NO divergence`，故自建 `_r3diag_f3.py` 做**按位配对**：ORIG 3 份 / PROD 3 份）：

- pair0（`tr = sum((max(max(...), abs(...)) for i in range(n1)))`，ORIG=PROD=46 insns）：**零分歧**。
- pair1/pair2（`dmp`/`dmm`，64 → 50）：首分歧 = ORIG off56 `LOAD_CONST 0` vs PROD off56 `LOAD_DEREF`；ORIG 有**两条** `POP_JUMP_FORWARD_IF_FALSE → 202`（off64、off156）+ `JUMP_FORWARD 200→204`，PROD 只剩**一条** `POP_JUMP_IF_FALSE 104→150` + `JUMP_FORWARD 148→152`。

ORIG pair1 的元素表达式实测结构：`A`（`high[-i]-high[-(i+1)]`，off14-52）→ **`A > 0`**（off56-58，假边 off64 → else 值 `LOAD_CONST 0`@202）→ **`A - B > 0`**（off114-150，假边 off156 → 同一 else 块 202）→ 值 `A` 重算（off158-196）→ `JUMP_FORWARD 200→204` → 202 `LOAD_CONST 0` → 204 `YIELD_VALUE`。
产物文本（`wizard_quant_apiOK.py:263-264`）：`dmp = sum((high[-i] - high[-(i+1)] if high[-i] - high[-(i+1)] > low[-(i+1)] - low[-i] else 0 for i in range(1, n1+1)))` —— **测试的 `and` 链只剩末位合取，第一合取 `A > 0` 及其到共享 else 块的出边整体消失**（−14 = 该合取的操作数重算 + 一条条件跳）。

### 4.3 lead 核实：缺陷在 genexpr 自身还是宿主方法？

**在 `<genexpr>` 自身的区域结构，宿主方法干净。** 证据：
1. `single` 原文只列 `<module>.get_DMI.calculate_di.<genexpr>` 两条，**不含** `<module>.get_DMI.calculate_di`。
2. `_r2diag diff get_DMI.calculate_di`：**orig 90 ↔ prod 90 条数相同**，仅 index 40/off156 与 59 两行 `replace`，两处都是 `LOAD_CONST <code object <genexpr>>` 的 repr（地址/co_filename）⇒ §1 已判伪影。宿主指令序列逐位等值（`('equal',0,0),('replace',40,40),('equal',41,41),('replace',59,59),('equal',60,60)`）。
3. 分歧块（`POP_JUMP_IF_FALSE → 202` 及其操作数）全部位于 genexpr code object 内部，宿主的 `FOR_ITER/JUMP_BACKWARD` 集合与 genexpr 的 `co_freevars=('high','low')`、`co_consts=(1,0,None)` 两版一致。
⇒ **不是「宿主区域把子区域摊平」，而是嵌套 code object 独立区域森林里 TernaryRegion 的测试子链认领缺失**。

**B113 — 嵌套 code object（生成器/列表推导/lambda）内 `A if <and 链> else B` 形 TernaryRegion：测试的 `and` 短路链首合取及其「假边 → 共享 else 块」出边未被认领，三元测试被降级为只剩末位合取（元素表达式少 14 条指令）**
- 锚点：`site-packages/IQCommon/strategy/wizard_quant_api.pyc` / `<module>.get_DMI.calculate_di.<genexpr>`（两份）/ orig off **56 `LOAD_CONST 0` / 58 `COMPARE_OP '>'` / 64 `POP_JUMP_FORWARD_IF_FALSE → 202`** 三处整体缺失（prod 56 起为 `LOAD_DEREF low`，`202` 的第二个前驱消失），并伴随 `POP_JUMP_IF_FALSE 156→202` 塌为唯一一条条件跳。
- 机制（候选站点，grep 核实存在）：`region_analyzer.py:22805 _identify_ternary_regions`（TernaryRegion 的测试/值/else 三段边界）与 `region_ast_generator.py:41749 _generate_ternary`、`region_ast_generator.py:38217/38454 _build_boolop_expression(_inner)`、`region_analyzer.py:28332 _detect_boolop_conditional_chain`。**本轮实证到的是「缺失发生在嵌套 code object 的森林根上」**（c07/c08 对照证明同一表达式在函数体内正常还原），站点内具体哪一条判据在嵌套根下未触发，属 fix 侧插桩面，不在本轮结论内。
- 违反条款：§1.2 **原则2 每块唯一归属**（首合取的三块 `LOAD_CONST/COMPARE_OP/POP_JUMP` 既未归测试区也未归 else 区 ⇒ 语句丢失）+ **原则3 嵌套即抽象节点**（测试子链未作为 BoolOp 抽象节点交付三元）+ §1.5 **C1 局部消费**（三元区域只读到末位比较的出边）。§3.2.3「统一不拆分任何 `and` 复合条件」在此被违反（拆到只剩末位）。
- 标本：`r3_c01`（语料原形 `sum(... if A>0 and A>B else 0 ...)`）/`r3_c02`（同形但结果先赋值）/`r3_c03`（**listcomp** 宿主 `<listcomp>`）/`r3_c04`（**类方法**宿主 `<module>.C.m.<genexpr>`）/`r3_c05`（`max(..., default=0)` 宿主）/`r3_c09`（**lambda 宿主 + genexpr 双层**：`<module>.<lambda>.<genexpr>`）/`r3_c10`（`or` 测试链）/`r3_c11`（三合取 `and` 链 ⇒ 与链长无关，只与「测试是短路链」有关）。
- 对照（今日 MATCH，修复后必须仍 MATCH）：`r3_c06`（**c01 删掉首合取 `A > 0` ⇒ MATCH**，决定性单改动对照）/`r3_c07`（**同一表达式放在函数体内直接赋值（非嵌套 code object）⇒ MATCH** ⇒ 判据维度 = 嵌套 code object 的区域森林根，不是深度）/`r3_c08`（同表达式放进 `for`+`try` 体内的赋值（仍非推导）⇒ MATCH，宿主扩展轴对照）。

## 5. 复现电池（`test_repros/round3/`，前缀 `r3_`）

生成方式＝写 `.py` → `py_compile` 同名 `.pyc` → `pycdc.py -o <base>OK.py` → 判据。索引 `test_repros/round3/r3_probe_index.json`（**52 臂**，格式与 `round1/r1_probe_index.json`、`round2/r2v3_probe_index.json` 逐字相同：`[{"path": "test_repros/round3/<x>.pyc"}, ...]`）。

| 破口 | 标本（今日 MISMATCH，修复后必须全部转 MATCH） | 对照（今日 MATCH，修复后必须保持 MATCH） | 标本→对照的唯一改动 |
|---|---|---|---|
| **B109**（靶 1 三单元） | `a01`(1/2) `a03`(1/2) `a05`(2/3) `a07`(1/2) `a08`(1/2)† `a09`(1/2) `a11`(1/2) `a12`(1/2) `a13`(1/2) `a14`(1/2) `a15`(1/2) | `a02` `a04` `a06` `a10` | a01→**a02** 删前一条 `if o is None: return None`；a01→**a10** `if not is_trade()` 改正极性；a01→**a04** 臂体去掉嵌套 if/else；a01→**a06** 宿主换 for+模块级 |
| **B110**（靶 2 单元 1） | `b01` `b02` `b03` `b06`(2/3) `b07` | `b04` `b05` | b01→**b05** 删第三名字成员（`_r2diag`：`NO divergence at all`）；b01→**b04** 换成 `a and b or c and d` 全 IF_FALSE 首族 |
| **B111**（靶 2 单元 2） | `b09` `b10` | `b08` `b11` `b12` | b10→**b12** 在循环体里加/删 `if s: break`（纯跳出口块的有无） |
| B100/B104（靶 2 单元 3，**未另立编号**） | —（**0 标本**，§3.3 缺口如实登记） | `b13` `b14` `b15` | 三臂 `not X and A and B` 链宿主扩展全部未复现 |
| **B112**（靶 3 单元 1） | `c12` `c17` `c18` `c22` | `c13` `c14` `c15` `c16` `c19` `c20` `c21` | c18→**c19** `or` 链改单成员；c18→**c20** elif 臂改普通 if 臂；c18→**c21** then 臂 `return None` 改 `return 0` |
| **B113**（靶 3 单元 2/3） | `c01` `c02` `c03` `c04` `c05` `c09` `c10` `c11` | `c06` `c07` `c08` | c01→**c06** 删首合取 `A > 0`；c01→**c07** 表达式移出推导（函数体直接赋值）；c01→**c08** 移入 for+try 体 |

† `a08`（with 宿主）已标记为**自我否证标本**，见 §6.2。

**电池汇总（本轮实测原文，唯一判据 `batch --index`）**

```
$ python -X utf8 scripts/pyc_verify.py batch --index test_repros/round3/r3_probe_index.json --json D:/Temp/rrv3/r3_battery_full.json
files_total=52  units_total=114  units_success=84  success_rate=0.7368421052631579
files_by_status={'compile_error': 0, 'error': 0, 'failure': 30, 'success': 22}   elapsed_sec=1.4
```
即 **30 臂今日 MISMATCH（标本）/ 22 臂今日 MATCH（对照）**，无 `error`/`compile_error`。
分族：B109 = 11 标本 + 4 对照；B110 = 5 标本 + 2 对照；B111 = 2 标本 + 3 对照；B112 = 4 标本 + 7 对照；B113 = 8 标本 + 3 对照；B100/B104 新实例 = 0 标本 + 3 对照。合计 30 + 22 = 52，与上表逐条吻合。
分靶读数（`single`，本轮实测原文）：`order_api.pyc units=34/37`、`klinedata.pyc units=61/64`、`wizard_quant_api.pyc units=55/58`。

## 6. 未完成 / 风险 / 如实声明

1. **`kline_datetime_list` 无最小合成孪生**（§3.3）：三臂 `not X and A and B` 宿主扩展臂 `b13/b14/b15` 今日全 MATCH。该单元只有真文件锚点，验收面须用 `klinedata.pyc` 的 64 单元读数；且其首分歧消费点本轮**未定位到站点**（只定位到锚点与判据面）。
2. **自我否证标本**：`r3_a08_with_host`（B109 的 with 宿主扩展臂）今日虽 MISMATCH，但其**首分歧在 off52**（`with` 退出簿记序列 `NOP;LOAD_CONST None×3;PRECALL 2;CALL 2;POP_TOP;LOAD_CONST None;RETURN_VALUE`）而**非** `is_trade` 臂跳；产物文本还凭空多出 `while False: pass`。⇒ 它证明的是「`return None` 在 with 体内 + elif 链」的另一条机制，**不得**用作 B109 的证据；B109 的合成证据由 a01/a03/a05/a09/a11-a15 承担（首分歧均在 `POP_JUMP_IF_TRUE`/`is_trade` 测试处，条数与语料同形）。该臂保留在索引里，要求修复后**仍为 MISMATCH 之外的其它判据面**，不与 B109 绑定。
3. 未把靶 1/靶 2 的**第二处以后分歧**逐条拆分（`future_order` index 88/91/93/98/100、`option_order` 55/58/60/65/67、`get_kline_by_count_new` 565/572、`kline_datetime_list` 133/139/145/155/160、`filter_desicion` 178/195）：均按同一首分歧的下游后果处理，块级 preds 证据已给出，未另立编号。
4. 未跑 402 全量 / 八分片 / 34 套（硬约束）。本轮只跑：3 个靶的 `single`、52 臂 `batch --index`、以及靶内 pyc↔OK.py 只读逐指令/块级比对。
5. 回归哨兵（修复后任何一条转 MISMATCH 即为过伸展）：B109 的 `r3_a02/a04/a06/a10`、B110 的 `r3_b04/b05`、B111 的 `r3_b08/b11/b12`、B112 的 `r3_c13/c14/c15/c16/c19/c20/c21`、B113 的 `r3_c06/c07/c08`，以及 B100/B104 面 `r3_b13/b14/b15`（这三条**禁止**被「一刀切拒绝 elif 链折叠」顺带拉绿或拉红）。既往 `round1/r1_probe_index.json`、`round2/r2v3_probe_index.json` 两批须同批复跑。
6. 本轮引用的**全部生产符号已 grep 核实存在**（函数名 + 当前行号）：`region_analyzer.py` `_compute_arm_level_join:3054`（判据 (4) 原文在 3113-3121）、`_check_elif_chain:21166`、`_main_inline_boolop_chain:19038/19275/19281`、`_detect_boolop_conditional_chain:28332`、`_identify_ternary_regions:22805`、`_find_loop_else:6028`；`region_ast_generator.py` `_if_generate_elif_chain:18757`、`_generate_ternary:41749`、`_build_boolop_expression:38217`、`_build_boolop_expression_inner:38454`、`_boolop_mixed_polarity_or_chain:38148`、`_arm_loop_child_entry:24517`、`_r2_b107_block_is_outer_exit:24595`、`_loop_preheader_blocks:24625`；`code_generator.py:2232 _filter_trailing_return_none`。**未核实**（不得引用）：`_w14_uniform`、`_is_terminal_sink`、`comprehension_code`、`co_stack` —— 这些名字在 `core/cfg/*.py` 中 `def` 与字符串双查均零命中，本轮结论未使用它们。
7. 破口登记：本轮新立 **B109 / B110 / B111 / B112 / B113** 五条 + 靶 2 单元 3 归 **B100/B104 既有编号的新实例**。五条全部是**成员关系 / 宿主区域类型（含嵌套 code object 区域森林根）形**，无一条深度形（§1.5 推论用法：修守卫，不加深度门控、不加名字/偏移/计数特判）。
