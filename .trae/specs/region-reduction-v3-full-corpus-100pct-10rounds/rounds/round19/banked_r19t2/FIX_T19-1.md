# FIX T19-1 (R14-05 residual) — 识别端臂归属/汇合身份：实测追踪读数 + 已落地判据（判决 FALSIFIED）

作用域：仅 `core/cfg/region_analyzer.py`（识别端），交付完整替换文件
`D:/Temp/r19t2/DELIVER/region_analyzer.py`（sha16 `a6861f946f750aca`，32895 行，全 CRLF，
`py_compile` 通过）。live 仓库 `core/` 未被本代理写入。
测量全在镜像 `D:/Temp/r19t2/`，判决只走
`python -X utf8 scripts/pyc_verify.py single <pyc> --source <pycdc 产物>`。

## 0 判据/镜像设施

- 镜像构建：`pycdc.py core/ parsers/ utils/ bytecode/ scripts/` + 五个电池同深度副本。
- 施加器 `D:/Temp/r19t2tools/var.py`：以 difflib 把存档补丁拆成 12 个 hunk，按编号选择施加，
  再叠加额外判据块（`x_w14a.txt` / `x_term2.txt` / `x_nest.txt`），CRLF 还原。
- 测量器 `D:/Temp/r19t2tools/m.py`（产物+判决+五电池）、`panel.py`（15 文件面板基线/施加同跑）、
  `probe.py`（**独立进程**重建 CFG 打区域表与谓词逐项读数）、`trace.py`（独立进程外包装
  `_detect_boolop_chain_start` 等 7 个方法的入参/返回值）。
- 探针纪律：`probe.py`/`trace.py` 都是**另起进程**、不产出反编译文本；分析器内部零打印。

## 1 阶段 1：未打补丁镜像复现封存基线（实测）

| 读数 | 镜像 pristine | 文档记录 |
|---|---|---|
| api_base | 27/28 | 27/28 ✔ |
| strategy | 26/27 | 26/27 ✔ |
| repro_arm | GREEN=0 RED=3/3 | 3/3 红 ✔ |
| repro_ccneg | GREEN=3 RED=1（m04_cc_cc 红） | 3G/1R ✔ |
| repro | RED=9/9 | 9/9 红 ✔ |
| repro_orderapi | GREEN=2 RED=3 | 2G/3R ✔ |
| repro_retbreak | GREEN=2 RED=2（r01、r02 红；镜像 core 实测 sha16 `640d33a77dcb71c2` = 封存基线字节） | — |

注：`m.py` 首轮把「pristine」副本取自当时镜像里的 core（那时已被存档补丁覆盖），故
`batt_both.log` 的 “CAND pristine” 行读的是**存档补丁**（api_base 25/29），不是基线；
基线行以 §1 与 §5 的 `panel.py`（直接从 live 仓库取字节，实测 sha16 `640d33a77dcb71c2`）为准。

## 2 阶段 2：谓词逐项读数（本票缺的那份）

### 2.1 api_base `get_history_df`，cand=B@1008，prefix=[B@992,B@996]（and-run 起链走）

施加存档补丁后（`D:/Temp/r19t2tools/probe.py`，独立进程实测）：

```
(1a) _is_chained_compare_header(B@1008) = True
(1b) _detect_chained_compare_pattern: compare_ops n=2, extra_chain_blocks=[B@1024]
(2)  成员 B@992 末指令 POP_JUMP_FORWARD_IF_TRUE -> B@1098   （_T 取首个成员 ⇒ _T=B@1098）
     成员 B@996 末指令 POP_JUMP_FORWARD_IF_TRUE -> B@1040   （与 _T 不同块 ⇒ 拒绝）
     (2) result: _T=B@1098 all_share=False              ← 假的那一项就是这一项
(3)  _r16_cc_operand_success_edge(B@1008) = B@1040（末段 B@1024 的落空边 B@1034 纯 JUMP_FORWARD → B@1040）
     末段条件后继集 = {B@1034, B@1098}；any is _T(B@1098) = True（但因 (2) 已 return False 而未走到）
PREDICATE = False
```

**为什么 (2) 在这块上必然为假**：prefix 横跨**两条算子 run**。B@992 是 `and` 成员
（`not include`），其尾跳边是**整条 run 的落空出口** B@1098（下一个 elif 臂）；
B@996 是 `or` 成员，其尾跳边是**该 or 段的短路真出口** B@1040（真臂体）。
CPython 对 `A and (B or C)` 的降级把这两个落点编到不同块，「全员同目标」这条合取项
对任何混合极性前缀都不可满足 —— 与块内容、函数名、偏移无关，是结构性不可满足。

同一 cand 在 or-run 走（prefix=[B@996]）时谓词为 **True**（`_T=B@1040`，success edge=B@1040），
故 or-run 能建：`BoolOpRegion e=996 op_chain=[(996,'or'),(1008,'or')] merge=1098`（实测区域表）。

### 2.2 strategy `tick_worker_thread`，cand=B@536，prefix=[B@512,B@524]

```
(1a) True  (1b) compare_ops n=2 extra_chain=[B@552]
(2)  B@512 IF_TRUE -> B@568 ；B@524 IF_TRUE -> B@568 ；all_share=True，_T=B@568
(3)  success edge(B@536) = B@568 is _T ⇒ True
PREDICATE = True        ← 准入通过；阻塞在 W14-A 修剪，不在谓词
```

实测阻塞（未接 cc success edge 时）：`BoolOpRegion e=512 op_chain=[(512,'or'),(524,'or')] merge=568`
—— 第三名 B@536 被 `[W14-A 修复·or 首链真出口一致性裁剪]` 剥掉：该修剪用
`_w14_last_ft`（取链末成员**自身**落空边 = B@552）与 `_w14_t0`（首成员真边 = B@568）比较，
二者不等 ⇒ 裁剪到同目标前缀。同一次链走里 `_r16_cc_operand_success_edge(B@536)` 已经等于 B@568。

### 2.3 父 and-run 走不到的原因（独立进程外包装实测，施加本判据后）

```
_r16_boolop_cc_run_operand cand=B@996 prefix=[992] -> False     （B@996 不是链式比较头）
_t19_nested_run_operand    cand=B@996 prefix=[chain] -> False   （见下）
chain_start B@992 -> []
chain_start B@996 -> [(996,'or'), (1008,'or')]                  （晚于 B@992）
chain_start B@1008 -> [] ; chain_start B@1024 -> [] ; chain_start B@1034 -> []
```
`_t19_nested_run_operand` 为假的实测理由是**时序**：B@992 起链时 `block_to_region[B@996]`
还不是 BoolOpRegion（同层兄弟 run 按偏移递增依次发现，内层/后段 run 尚未登记），
「嵌套即抽象节点」的前提在该走时刻不成立。因此该项无法在不动起链次序的前提下做到
correct-at-identification。

## 3 已落地的识别端判据（原文即代码注释原文）

### 3.1 `_r16_boolop_cc_run_operand` 第 (2) 项：共享出口按 run 段要求（`x_term2`）

```
        # [T19-1] 同一条件里的前缀成员可横跨两条算子 run（`A and (B or cc)`）:
        # and 成员的尾跳边是本 run 的落空出口，or 成员的尾跳边是上一条 run 的
        # 短路出口，二者按 CPython 降级永不同块，故「全员同目标」只在 cand 所属
        # 的终端 run 段上要求。终端段 = 从末成员向前、目标相同的最长后缀；
        # 其前置成员段若存在，必须自身同目标（外层 run 的出口已定）且不与终端段
        # 同块。命中后 _T 取终端段目标，(3) 仍要求 cand 的「比较成立」落点正是 _T。
```

### 3.2 W14-A 一致性裁剪读链式比较 success edge（`x_w14a`）

```
            # [T19-1] 末成员是链式比较 run 操作数时，它的「比较成立」落点不在
            # 自身块的落空边（那是它的内部续段），而在链式比较末段之后（必要时
            # 越过 run 接线用的纯 JUMP_FORWARD 控制块）。同目标一致性裁剪必须以
            # 该落点为准，否则 cc 成员被剥掉、or-run 退回 IfRegion 层级拆成嵌套
            # if，真臂体落在臂外。判据与链 walk 端同一处复用，不认领块。
```

### 3.3 嵌套 run 即抽象节点的认领豁免（`x_nest`，helper `_t19_nested_run_operand`）

```
        算法依据（原则 3 嵌套即抽象节点 + 原则 2 每块唯一归属）：CPython 把
        `A and (B or C)` 降级为 A 的落空边进入内层 run 的 entry，内层 run 的
        汇合出口与 A 的跳转目标同块；此时整条内层 run 是外层 run 的单名操作数，
        该 entry 已登记为 BoolOpRegion 不构成断链理由。判据只读同层区域入口、
        该 run 已解析的 merge_block 与链末成员尾条件跳边落点；不认领块、不新增
        区域、不读函数名/常量/绝对偏移。形状不符返回 False，调用方维持原守卫。
```

三者都是结构判据：只用块内指令集、末指令 opcode、跳边/落空边身份、同层区域 entry 与
已解析 merge，无名称、无常量、无绝对偏移、无成员数阈值；单向数据流（识别端定身份，
不回看任何已渲染区域）。

### 3.4 同时移除的两条存档臂（实测为 api_base 回退源）

交付文件 = 存档补丁的**链侧** hunk（#4..#11）+ 上述三判据 + 存档 hunk #0/#1，
**不含** hunk #2（强制 `merge = BoolOpRegion.merge_block`）与 hunk #3（elif 臂归属修剪）。
消融实测（每变体只差 hunk 集合，产物逐字节由 pycdc 产出）：

| 变体 | hunk 集 | api_base | strategy |
|---|---|---|---|
| 未打补丁 | — | 27/28 | 26/27 |
| ALL（=存档补丁） | 0..11 | **25/29** | 26/27 |
| V_A | 4..11 | 27/28 | 26/27 |
| V_B | 0,1,4..11 | 27/28 | 26/27 |
| V_C | 0,1,2,4..11 | **25/29** | 26/27 |
| V_D | V_B + §3.2 | 27/28 | 26/27 |
| V_E | V_B + #3 + §3.2 | 27/28 | 26/27 |
| V_F | V_D + §3.1 | 27/28 | 26/27 |
| V_H（交付） | V_F + §3.3 | 27/28 | 26/27 |

⇒ hunk #2 单独把 api_base 从 27/28 打到 25/29（区域表实测：强制 `merge=@1098` 后
`_collect_branch_blocks(@1040, @1098)` 越界，`IfRegion e=996 then=[1040, 5924, 5978, …]`
灌进函数尾部 14+ 块）；去掉 #2 后同一区域的臂身份**正确**：
`IfRegion e=996 cond=1008 merge=1782 then=[1040] else=[1098, 1142, 1200]`（实测）。

## 4 阶段 3：两个目标单元未翻转（实测，本票止于此）

判据把识别端的**或 run 成员归属**与**子区域臂身份**都改对了，但两单元的产物仍不复现原字节：

* api_base：产物从「三层嵌套 if（两处 IF_TRUE 落 @1254）」变为
  ```
            if not include:
                if _query_date > pm_close_market_datetime or am_close < … <= pm_open:
                    pass
  ```
  即条件文本已折叠成扁平 or-run（这是相对基线的实质进展），但臂体 `@1040..@1096` 整段丢失。
  实测父区域仍把臂体记在自己名下：`IfRegion e=992 cond=992 merge=1098 then=[996, 1024, 1034, 1036, 1040]`
  —— @1040 同时是子区域 e=996 的 then 首块与 cc 区域 e=1008 的 then/merge（`then=[1040] merge=1040`）。
  父/子在同级争同一块 ⇒ 生成端按唯一归属只渲染 `pass`。要消掉它必须**同时**改写父区域的
  then 收集与 cc 子区域的 merge 语义，而后者又依赖父 and-run 成立（§2.3 时序阻塞）。
* 父 and-run 在本仓现有机构里无处安放：`_main_inline_boolop_chain` 的 and 游走要求
  区域条件末指令为 `IF_FALSE`（`region_analyzer.py:19528-19531`）且每名后续成员
  `'IF_TRUE' in _main_ft_last.opname: break`、`_main_ft_last.argval != _main_merge_offset: break`
  （`:19583-19600`）。本字形 B@992 末指令是 `IF_TRUE -> @1098`、B@996 是 `IF_TRUE -> @1040`：
  两处各自独立拒绝，`not include and (… or …)` 这条混合极性 run 在该机构下不可表达。
* strategy：§3.2 接线后 3 成员链确实建立（`BoolOpRegion e=512 op_chain=[(512,'or'),(524,'or'),(536,'or')] merge=612`），
  但父 `IfRegion e=512` 从区域表消失（实测 V_H 表只剩 BoolOpRegion@512 与 IfRegion@612），
  单元仍 26/27 —— 与 api_base 同一类「父臂身份未随子 run 更新」的问题，方向相反（子建全，父散架）。

⇒ 阶段 3 未过，按验收阶梯停在此处（阶段 4 数字见 §5，只作「无回退」证据，不作落地理由）。
交付文件**不可安装**：不新增单元，也不回退任何单元；它把本票缺失的两项读数转成了
可复用的判据代码与两处实测缺口（本节的父/子同级争块、§2.3 的起链时序），
下一票只需接这两条线，不必重新诊断。

## 5 阶段 4：电池与 15 文件面板（基线 vs 施加同跑，镜像内）

五电池（施加 V_H 后与基线逐项相同，零变化）：

| 电池 | 基线（镜像 pristine） | 施加 V_H |
|---|---|---|
| repro_arm | GREEN=0 RED=3/3 | GREEN=0 RED=3/3 |
| repro_ccneg | GREEN=3 RED=1（m04 红） | GREEN=3 RED=1 |
| repro | RED=9/9 | RED=9/9 |
| repro_retbreak | GREEN=2 RED=2（r01、r02 红） | GREEN=2 RED=2 |
| repro_orderapi | GREEN=2 RED=3 | GREEN=2 RED=3 |

15 文件面板（`pyc_verify single` 逐文件两侧同判，DECREASES=0）：

```
klinedata 63/64  handlers 29/30  wizard_quant_api 55/58  trade_info_utils 38/41
real_quote 43/45  order_api 35/37  realtime_event_source 12/13  risk_calculation/__init__ 41/43
trade_live_broker 118/128  quote 86/92  matcher 17/17  quotation 153/153
bar 85/85  strategy_universe 11/11  load_daily 27/27        （全部 SAME）
```

⇒ 阶段 4 无回退；阶段 3 未过 ⇒ 停止，不跑 402 门链（非本代理职责）。

## 6 判决

FALSIFIED — 判据本身在两项实测上成立（§2.1 的 (2) 项与 §2.2 的 W14-A 缺口都能被
结构判据修好，且 api_base 的条件折叠与子臂身份实测转正），但两目标单元均未翻转，
负向臂读数：api_base 27/28（产物改为 `if <flat or-run>: pass`，臂体 @1040 整段丢失）、
strategy 26/27（3 成员链建立、父 IfRegion@512 消失）。真正的剩余闸门是
**父 IfRegion 与子 run 的臂/汇合身份要在同一层一起定**，而现有 and-run 起链的
「兄弟 run 按偏移顺序发现」时序使「嵌套即抽象节点」在父走时刻读不到子区域（§2.3）。
