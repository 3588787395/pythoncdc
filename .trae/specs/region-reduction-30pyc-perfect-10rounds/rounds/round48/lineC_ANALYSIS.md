# Round 48 · DIAGNOSE-ONLY · 语料 R48-C — `fly_api/order_api.pyc` 中部条件语句被尾部重发并截断

分析位：`D:/Temp/r48diagC`（只读 `core/`，未做任何修改，未执行任何 git 写命令）
候选臂：`D:/Temp/r43gate/mirr_r48cA`（谓词 v1，已证伪）、`D:/Temp/r43gate/mirr_r48cB`（**推荐**：v1 + 汇合侧合取）
诊断臂（含 stderr 打印，不用于交付）：`D:/Temp/r43gate/mirr_r48cDg`

## 0. 结论

**SHIP `r48cB`**（谓词见 §3 全文）。决定性数字：G1 池 `SUM files=27 same=26 gained=2 lost=0`，
G4 全量 `SUM files=544 same=543 gained=2 lost=0` 且 G4′ `affected=6 fixed=3 broken=0 changed=0`。

目标文件 `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc`：
`matched_functions 30/34 → 32/34`，`buy_close`/`sell_close` 严格尺 `seq_len orig=122 decomp=114` → 无缺陷
（`orig=122 decomp=122 kind=None defect=None`）。

同一轮 **v1（`r48cA`，无汇合侧合取）证伪**：G1 `gained=2 lost=1`，新增缺陷
`IQCommon/api/klinedata.pyc :: check_datetime_common`（`40/45 → 39/45`，`NEWDEFECT [221, 224, 0, 126]`）。
v1→v2 只加了一个「汇合块必须直线续延」合取，`lost` 归零且 `gained` 保持 2。
（注：`klinedata.pyc` 同时是 R48-diagA 的目标；此回归是在**共享 G1 池**里测出的，非进入其工作目录取得。）

`future_order`/`option_order` 两行**不在本候选射程内**（§5：第二站点），在 `r48cB` 上实测为 no-op：
`['future_order', 101, 92, 2, 36]`、`['option_order', 83, 73, 3, 39]` 与落地面完全相同。

## 1. 逐函数行 + 四行是否同一机制

| 函数 | 落地（官方尺） | r48cA | r48cB | 严格尺（落地） |
|---|---|---|---|---|
| `buy_close` | `[122,114,2,56]` | 行消失（122/122） | 行消失（122/122） | `seq_len orig=122 decomp=114 defect=True` |
| `sell_close` | `[122,114,2,56]` | 行消失 | 行消失 | `seq_len orig=122 decomp=114 defect=True` |
| `future_order` | `[101,92,2,36]` | `[101,92,2,36]` | `[101,92,2,36]` | `seq_len orig=101 decomp=93`（`delete o[62:66]`） |
| `option_order` | `[83,73,3,39]` | `[83,73,3,39]` | `[83,73,3,39]` | `seq_len orig=83 decomp=74`（`delete o[33:37]`） |

诊断臂打印（`_check_elif_chain` 决策点，仅块号/前驱/后继/终结子类别）逐函数取材：

```
fn=buy_close      hdr=0   first_else=134 inner_merge=548 merge_=None preds=[440,444] hits=[]  lastop=STORE_FAST               nsucc=1
fn=sell_close     hdr=0   first_else=134 inner_merge=548 merge_=None preds=[440,444] hits=[]  lastop=STORE_FAST               nsucc=1
fn=future_order   hdr=340 first_else=386 inner_merge=558 merge_=None preds=[552,556] hits=[552] lastop=POP_JUMP_FORWARD_IF_FALSE nsucc=2
fn=option_order   hdr=130 first_else=178 inner_merge=350 merge_=None preds=[344,348] hits=[344] lastop=POP_JUMP_FORWARD_IF_FALSE nsucc=2
fn=klinedata:check_datetime_common hdr=0 first_else=102 inner_merge=1190 preds=[402,628,810,886,1114] hits=[] lastop=POP_JUMP_FORWARD_IF_TRUE nsucc=2
fn=klinedata:get_price_common      hdr=126/174/284     inner_merge=438  preds=[278,388,390] hits=[] lastop=POP_JUMP_FORWARD_IF_NOT_NONE nsucc=2
```

**四行不是同一机制**（此假设被证伪）：

* `buy_close`/`sell_close`：**同一机制，两个实例**。`hits=[]` 且 `nsucc=1` —— 声称的链汇合块
  （`inner_merge`）没有任何「本臂内前驱」，且自身直线续延。谓词触发 → 两行同消。
* `future_order`/`option_order`：**另一个机制**。诊断显示 `hits` 非空（臂确实进入 `inner_merge`），
  谓词无从触发；两行的汇合块取自 **链 merge 选取点**（`region_analyzer.py` 链尾
  `_chain_merge_candidates` 处 `len(_non_empty_exits) == 1` 分支）：
  * `option_order`：`R3 IF_ELIF_CHAIN entry=B3 merge=B9 blocks={B3,B4,B5,B7,B8}`，
    而 `B6` 归 `TernaryRegion R2`（臂列表里出现的是三元臂 `B7/B8`）；
  * `future_order`：`R2 IF_ELIF_CHAIN entry=B8 merge=B14 blocks={B8,B9,B10,B12,B13}`，
    `B11` 归 `TernaryRegion R1`。
  即链的 merge 被三元区域吞掉的块「顶替」，缺陷出在 **merge 选取站点**，不是本谓词站点。
  二者 `nsucc=2`（`inner_merge` 自身仍是分支块），也与本谓词的取材域正交。

结论：**两两成组，共两组机制**；本轮候选覆盖第一组（2/4 行）。

## 2. 根因（块/区域事实 + 发射链 + 被违反的原则）

`buy_close` CFG（16 块，按 `get_blocks_in_order()`，块号 B*，起点偏移 o*）：

```
B0  o0   n=13  succs=[B1,B2]   ... POP_JUMP_FORWARD_IF_FALSE
B1  o84  n=10  preds=[B0]      succs=[]          RETURN_VALUE
B2  o134 n=5   preds=[B0]      succs=[B8,B3]     POP_JUMP_FORWARD_IF_FALSE
B3  o156 n=2   preds=[B2]      succs=[B7,B4]     POP_JUMP_FORWARD_IF_FALSE
B4  o160 n=17  preds=[B3]      succs=[B5,B6]     POP_JUMP_FORWARD_IF_FALSE
B5  o282 n=8   preds=[B4]      succs=[]          RETURN_VALUE
B6  o326 n=1   preds=[B4]      succs=[B11]       JUMP_FORWARD
B7  o328 n=14  preds=[B3]      succs=[B11]       JUMP_FORWARD
B8  o440 n=2   preds=[B2]      succs=[B9,B10]    POP_JUMP_FORWARD_IF_FALSE
B9  o444 n=13  preds=[B8]      succs=[B10]       POP_TOP（落空即 fall-through 到 B10）
B10 o548 n=13  preds=[B8,B9]   succs=[B11]       STORE_FAST（无跳转终结子 = 直线续延）
B11 o658 n=4   preds=[B7,B10,B6] succs=[B12,B13] POP_JUMP_FORWARD_IF_FALSE
B12 o670 n=8   preds=[B11]     succs=[]          RETURN_VALUE
B13 o714 n=4   preds=[B11]     succs=[B15,B14]   POP_JUMP_FORWARD_IF_FALSE
B14 o726 n=13  preds=[B13]     succs=[B15]       STORE_FAST
B15 o810 n=11  preds=[B13,B14] succs=[]          RETURN_VALUE
```

真源码形状（已用本机 `py_compile` 构造同构 CFG 证实，`cand2.py`：16 块、前驱/后继/终结子全同）：

```python
if <条件1>: ...; return None
if <条件2>:                        # B2 o134 —— 外层 else 体的首句，不是 elif
    ...                            #   其 then 臂 B3/B4/B5/B6/B7
else:
    if <条件3>: ...                # B8 o440 / B9 o444 —— B2 的 else 体内嵌套 if
    <B10 o548：嵌套 if 两臂的汇合块 + 其后的尾随赋值>
    if <条件4>: ...                # B11 o658 起，属于外层 if 之后的兄弟语句
```

被错误接受的链解释（`traceelif.py` 实测，`t_buyclose.txt`）：

```
BUILD hdr=o0 then=[o84] else=[o134 ...] merge=- ->
  IfRegion cond=o0 merge=o548 conds=[o134 o440]
             bodies=[[o156 o160 o328 o282 o326 o658 o670 o714 o726 o810] [o444]] fel=[]
COLLECT start=o156 merge=o548 stop=[o440] ->
        [o156 o160 o328 o282 o326 o658 o670 o714 o726 o810]   @ _check_elif_chain:18878
```

区域清单（落地面，`r_buyclose.txt`）：

```
R3 IfRegion type=IF_ELIF_CHAIN entry=B0 exit=B10
   blocks = {B0 B1 B2 B3 B4 B5 B6 B7 B8 B9 B11 B12 B13 B14 B15}   ← 不含 B10
   merge_block = B10  elif_conditions = B2 B8  elif_bodies = [B3 B4 B7 B5 B6 B11 B12 B13 B14 B15 | B9]
R14 Region type=BASIC entry=B10 exit=None blocks={B10}   （不是 R3 的 child）
block_to_region: B10 -> R14
```

发射/推导追踪：

1. `merge_ = None`：外层 `then` 臂 B1 以 `RETURN_VALUE` 终结 ⇒ 外层无汇合点，
   `elif` 链与「else 体首句嵌套 if」在**外层 merge 这一维**上失去信息。
2. `inner_merge = B10(o548)`：`_it_sink`（B3 侧有 `RETURN`/无 ipd）真、`_ie_sink` 假 ⇒
   `inner_merge = inner_else_succ.immediate_post_dominator`；实测
   `ipd(o156)=None`、`NCPD(o156,o440)=None`、`ipd(o440)=ipd(o444)=o548`。
   **这正是上方 `_d2` 守卫的盲区**：`_d2` 的前置条件是 `merge_ is not None`，本轮 `merge_=None` ⇒ `_d2` 永不触发。
3. 链解释要求「B2 是 elif 条件、B8 是下一个 elif 条件、B10 是链 merge」。但臂收集
   `_collect_branch_blocks(o156, merge=o548, stop={o440})` 沿 B3→B7→**B11**→…→B15 走完，
   因为 B7/B6 以 `JUMP_FORWARD` **绕开** o548 直接落到 o658 ⇒ 臂吞掉了 o548 之后的全部链后代码
   （`elif_bodies[0]` 含 `o658 o670 o714 o726 o810`）。
4. 建区时 `all_blocks` 排除 `merge` ⇒ **B10 不入任何区域块集**，只在 `block_to_region` 里挂到一个
   非 child 的孤立 BASIC 区域 R14 ⇒ 无发射者。
5. 结果：`_process_if_blocks` 按 `elif_bodies[0]`（被吞的尾段）与 `elif_conditions=[B2,B8]` 发射，
   B8+B9 在**函数末尾**（所有 `return` 之后）被重发一次，其后的 B10 因无主被**截断丢弃**。
   严格尺编辑块：
   `delete o[62:86] d[62:62]` = `JUMP_FORWARD@438`(B7 出口) + B8(`LOAD_FAST@440`,`POP_JUMP_FORWARD_IF_FALSE@442`)
   + B9(`LOAD_GLOBAL@444`…`POP_TOP@546`) + B10(`LOAD_GLOBAL@548`…`STORE_FAST@656`)；
   `insert o[122:122] d[98:114]` = B8+B9 重发 + 两条 `LOAD_CONST/RETURN_VALUE`。⇒ `114 = 122 − 8`。

**被违反的原则**：原则 2（每块唯一归属 **且归属者必须发射** —— B10 被排除出链块集后其唯一挂靠者
R14 不是任何区域的 child，永远不被发射）；原则 4（父区域只以 entry 引用子区域，此处被引用的是一个
**普通块**而非子区域 entry，链的 `merge_block` 与块归属集合自相矛盾）；原则 1 的推论（臂末 `JUMP_FORWARD`
落点在链 merge **之后** ⇒ 该「臂」根本没有与声称的 merge 建立任何进入关系）。

## 3. 唯一的同层谓词（站点：`_check_elif_chain` 内，`_d2` 守卫之后）

**锚点文本**（`core/cfg/region_analyzer.py`，全文件唯一，按锚点定位而非行号；落地行号 19005–19013）：

```python
            if (inner_merge is not None and merge_ is not None
                    and inner_merge is not merge_):
                _d2_last = inner_merge.get_last_instruction()
                _d2_terminal = (_d2_last is not None
                                    and _d2_last.opname in (
                                        'RETURN_VALUE', 'RETURN_CONST',
                                        'RAISE_VARARGS', 'RERAISE'))
                if not _d2_terminal:
                    return None
```

**插入全文**（锚点后，紧跟 `inner_else_blocks = self._collect_branch_blocks(...)` 之前；18 行注释 + 8 行代码，共 26 行；
下框与 `spec_r48cb.json` 的 `repl − anchor` 逐字符相同）：

```python
            # [R48-C 同层谓词 · 链汇合的前驱侧对偶] 区域归约算法原则 1（块 = 前导
            # 语句 + 恰好一个终结子）＋原则 2（每块唯一归属且归属者必须发射）：
            # inner_merge 是 first_else 两臂的声称汇合块，故 first_else 的 then 臂
            # （inner_then_blocks）必须【进入】它——即 inner_merge 至少有一个前驱落在
            # 本臂块集内。若无任何臂内前驱，则该臂以绕开 inner_merge 的前向跳转落到
            # 更远处的块（CPython 对 if/elif 链的每个臂末都跳向链汇合点），
            # 说明 inner_merge 只是 else 侧自己那个嵌套 if 的汇合点、其后还有属于外层
            # else 体的尾随语句 ⇒ first_else 不是 elif 条件而是 else 体首句，链解释不成立。
            # 汇合侧要求：inner_merge 恰有一个后继（直线续延：落到后继语句首块或以
            # JUMP_FORWARD 跳向它）。若它自身仍是分支块（POP_JUMP_* 两个后继），则它是
            # 后一条兄弟语句的条件块而非本嵌套 if 的汇合点，前驱判据在此无从分辨，
            # 保持沉默（实测 check_datetime_common 的误拒正是该形状）。
            # 返回 None 后调用方按 IF_THEN_ELSE 建区，尾随块留在 else 体内（原则 2），
            # merge 块不再是无主块（原则 4：父以 entry 引用子区域）。
            # 与上方 _d2 守卫同一取材域（inner_merge / merge_ / inner_then_blocks 的
            # predecessors/successors 关系与终结子类别），不读名字、常量、绝对偏移、
            # 指令数、历史清单；覆盖 _d2 的盲区：臂以 RETURN 终态使 merge_ 为 None 时
            # _d2 永不触发。
            if (inner_merge is not None
                    and inner_merge is not merge_
                    and len(inner_merge.successors or []) == 1
                    and inner_then_blocks):
                _r48c_arm = set(inner_then_blocks)
                if not any(_r48c_p in _r48c_arm
                           for _r48c_p in inner_merge.predecessors):
                    return None
```

生成脚本 `D:/Temp/r48diagC/mkspec48b.py` → `D:/Temp/r48diagC/spec_r48cb.json`；
臂 `mirr_r48cB` 的 `region_analyzer.py`：`sha256[:20]=0e1c4ce1417fe38993ab`，`len=1683289`（落地 +2254B），
锚点唯一性由 `build2.py` 断言（1 edit）。

**合取项 → 结构事实对照**

| 合取项 | 取材 | 结构含义 | 对应原则 |
|---|---|---|---|
| `inner_merge is not None` | 区域角色 | 存在被声称的汇合块（sink 场景 NCPD 返回 None，不属本判据射程） | 4 |
| `inner_merge is not merge_` | 块同一性 | 声称的嵌套汇合点 ≠ 外层链汇合点 ⇒ 汇合点之后还有文本 | 1 |
| `len(inner_merge.successors or []) == 1` | 前驱/后继关系（等价于终结子类别：单一落点 = `JUMP_FORWARD` 类或 fall-through 直线续延；`POP_JUMP_*` 类 ⇒ 两后继） | 该块确实是**汇合点**而非「下一条兄弟语句的条件块」；分支块时前驱判据无从分辨 ⇒ 保持沉默 | 1 |
| `set(inner_then_blocks) ∩ inner_merge.predecessors = ∅` | 区域块归属 + 前驱关系 | 本臂从未**进入**声称的汇合点 ⇒ 臂末以绕开它的前向跳转落到更远处 ⇒ 链解释不成立 | 2 / 4 |
| （不读）名字、常量、绝对偏移、指令数、历史清单 | — | 全部判据只用块同一性/归属、区域角色与类型、pred/succ 关系、终结子类别 | — |

返回 `None` 后调用方按 `IF_THEN_ELSE` 建区（`first_else` 成为 else 体首句的嵌套 if），
尾随块留在 else 体内并正常发射：`buy_close` 修复文本为
`if asset.type != …: return None` / `else: if asset.exchange=='XSGE': … else: (if close_today: warning)
futures_direction = CLOSE; current_amount = sell_amount; if current_amount == 0 … return future_order(…)`。

**负向盾牌（为什么不伤合法形状）**

* 只在**同时**满足「声称汇合块无臂内前驱」+「该块恰一个后继」时拒绝，其余一切形状沉默；
  与 `_d2`（要求 `merge_ is not None`）取材域重叠但补其 `merge_ = None` 盲区，二者不冲突。
* 真实链的臂末必然 `JUMP_FORWARD` 到链 merge（该 merge 至少有一个臂内前驱）⇒ 判据不触发。
  实测语料内合法形状全部 `hits` 非空：
  `order_api:base_order hdr=774/470`、`buy_close hdr=658`（`inner_merge=o810`，`lastop=RETURN_VALUE`，`nsucc=0`
  —— 共享退出，被 `nsucc==1` 挡在门外，与 `_d2` 判据⑤ 同向）、`option_exercise/option_sell_close/option_buy_close`、
  `klinedata:get_exrights_data/stk_history_day_complex/stk_resample_days_bars/np_tp_pd/to_pd_result`。
* G0 电池 6 个正对照（`c1_real_elif_no_else`、`c2_real_elif_else`、`c3_else_head_nested_if_with_own_else`、
  `c4_plain_if_else_two_arms`、`c5_elif_chain_all_terminal`、`c6_real_elif_then_nested_head_tail`）
  逐 code object 指令签名 `IDENTICAL` 且非缺陷（§4）。
* 门测：G1 27 文件里 26 个 `matched_functions` 与 mismatch 行集合完全相同（另 1 个即 order_api 提升）；
  G2′ 143 文件、G3 109 文件全 `same`；
  G4 544 文件**文本**变更面 6 个路径，G4′ 在这 6 个路径上 `broken=0 changed=0 fixed=3`。
  变更面逐路径：`IQCommon/data/finance.pyc`（22/24 不变，严格缺陷 5→5 同集合）、
  `IQData/plugin_system_local_finance/finance_data_source.pyc`（18/18，0→0）、
  `IQEngine/fly_api/order_api.pyc`（30→32/34）、`IQEngine/plugin_system_risk_calculation/__init__.pyc`
  （32/35 不变，`PluginRiskCalculation.trade_win_and_lose` 严格缺陷 `target_diff #409` **FIXED**，6→5）、
  `IQEngine/plugin_system_trade/function.pyc`（69/71 不变，3→3 同集合）、
  `test_repros/round31_arm_terminal_join/r31a_witness.pyc`（3/4 不变，2→2 同集合）。
* v1→v2 的教训即负向盾牌本身：去掉 `nsucc==1` 合取会在 `check_datetime_common` 误拒一条合法链
  （`inner_merge` 是后一条兄弟语句的**条件块**，两后继），G1 `lost=1`。

## 4. 串行门（按序实跑，均为本目录自产 jsonl）

G0（合成见证电池 `D:/Temp/r48diagC/w48_witness.py`，`py_compile` 编译，
`D:/Temp/r48diagC/g048.py r48cB`，逐 code object 指令签名 + `_r10_strict_check.strict_compare`）：

```
n=13 identical=11 differs=2
defective[landed]=5/13   w1_close_shape seq_len orig=82 decomp=75 ; w2_close_shape_twin seq_len orig=68 decomp=61
                         s1/s2/s3 target_diff #16/#16/#18
defective[r48cB]=3/13    仅 s1/s2/s3（其签名两侧 IDENTICAL ⇒ 谓词在该形状上可证 no-op）
w1_close_shape   cc643e36e53fade8 -> 5c0783d59becfc0a  *** DIFFERS ***
w2_close_shape_twin bca60b320446f8e5 -> e80fddbfb68271f9 *** DIFFERS ***
<module> / _set / c1..c6 / s1..s3  IDENTICAL
```
`w1/w2` 建模 `buy_close`/`sell_close` 形状（else 体首句嵌套 if + 汇合后尾随语句 + 臂以 return 终态）；
`c1..c6` 为必须保持的控制；`s1/s2/s3` 是诚实标注的**未覆盖兄弟形状**（两侧同缺陷、同签名）。

```
G1  pool27    python -X utf8 D:/Temp/r43gate/r43g.py run --arm=r48cB --list=D:/Temp/r48mine/g1pool48.txt
              --out=D:/Temp/r48diagC/b_g1_r48cB_s{0..2}.jsonl --nshard=3 --shard=I
              tally43 D:/Temp/r48mine/g1_landed48.jsonl o_g1_r48cB.jsonl
              UP   order_api.pyc 30/34 -> 32/34
              SUM files=27 same=26 gained=2 lost=0
G2' bat43     run --arm=r48cB --list=D:/Temp/r43gate/bat43.txt --nshard=6 (143 行)
              tally43 D:/Temp/r43gate/bat45.jsonl o_g2_r48cB.jsonl
              SUM files=143 same=143 gained=0 lost=0
G3  anchors   run --arm=r48cB --list=D:/Temp/r43gate/anchors109.txt --nshard=3 (109 行)
              tally43 D:/Temp/r43gate/anch45.jsonl o_g3_r48cB.jsonl
              SUM files=109 same=109 gained=0 lost=0
G4  full      run --arm=r48cB --list=D:/Temp/r43gate/r45full.txt --nshard=8 (544 行, 0 error)
              tally43 D:/Temp/r48mine/g4_landed48_all.jsonl o_g4_r48cB.jsonl
              UP   order_api.pyc 30/34 -> 32/34
              SUM files=544 same=543 gained=2 lost=0
              sha 变更面 6 路径（逐条见 §3 盾牌）
G4' strict    python -X utf8 D:/Temp/r43gate/g4prime43.py D:/Temp/r48diagC/b_g4_changed.txt r48cB
              G4-prime affected=6 fixed=3 broken=0 changed=0
```

a 侧一致性核对：`mirr_r47aA` 的 `region_analyzer.py=55a9f61b9b0703063d44`、
`region_ast_generator.py=2a3d522b0ec9e8fe66e4` 与落地面逐字节相同；6 个变更路径在
`build_head` 与 `build_r47aA` 下产物 sha 两两相同 ⇒ G4′ 的 a 侧即落地产物。

落地面复述断言（测量前置）：`core/cfg/region_ast_generator.py` `2a3d522b0ec9e8fe66e4`/3 003 323/CRLF 48 654/
裸 LF 0/BOM 有；`core/cfg/region_analyzer.py` `55a9f61b9b0703063d44`/1 681 035/CRLF 27 023/裸 LF 0/无 BOM；
HEAD `6e7b2985`；`core/` 内**不含** `R48-C` 标记（本诊断未落任何码）。

## 5. 被证伪的线索 + Round 49 交接

1. **R45-A/R46-B 的 merge-ownership 家族不覆盖 `buy_close`**：`buy_close` 的 `inner_merge` 侧形状
   与 `IQCommon/strategy/wizard_quant_api.pyc :: region_mean_desicion` 不同族 —— 此处外层 `merge_` 为
   `None`（then 臂 `RETURN` 终态），`_d2` 与链 merge 选取点均不参与；修复点在
   `first_else`→`inner_merge` 的**前驱进入关系**上。此结论早于本轮并已复核。
2. **「一个谓词翻转四行」被证伪**（§1）：`future_order`/`option_order` 的决策点 `hits` 非空，
   谓词在诊断里根本没触发；实测两行不变。
3. **v1（无 `nsucc==1` 合取）被证伪**：`lost=1`，`check_datetime_common` 新增
   `NEWDEFECT [221, 224, 0, 126]`。诊断行 `inner_merge=1190 lastop=POP_JUMP_FORWARD_IF_TRUE nsucc=2`
   给出结构性理由：该块是**后一条兄弟语句的条件块**，不是嵌套 if 的汇合点，前驱侧判据在此信息不足。
4. **sink 回退分支本身不是根因**：`inner_merge = inner_else_succ.immediate_post_dominator`
   （`_it_sink and not _ie_sink`）在 `buy_close` 上取到的 o548 确实是嵌套 if 的真实汇合点，
   错的是**把 `first_else` 当 elif 条件**；只收紧回退取值（R48-A 家族）不解决。
5. Round 49 建议（同层、单站点）：
   * 站点 A（覆盖 `future_order`/`option_order`）：链 merge 选取处
     （`_chain_merge_candidates` 的 `len(_non_empty_exits) == 1` 分支）要求候选块集与
     各臂的**归属区域**相容——候选块若已属某 `TernaryRegion` 的臂块集，则该臂的「exit」不可作为
     链 merge。可先用 `mirr_r48cDg` 式打印取该站点的 `exit` 集合与 `block_to_region` 对照。
   * 站点 B（覆盖 `s1/s2/s3` 兄弟形状）：`_elif_struct_blocks` 过滤 `else_blocks` 时对
     「汇合点之后仍在 else 体内的尾随块」做归属回填（本轮谓词从**接受侧**规避了它，未真正处理）。
   * 复用本目录：`mkspec48b.py`（出 spec）、`D:/Temp/r43gate/build2.py <name> <spec>`（**不带** `mirr_` 前缀）、
     `prod.py`/`rows.py`/`diffstrict.py`/`traceelif.py`/`g048.py`/`w48_witness.py`。

## 附注 · 完整性（供编排者核实，非诊断内容）

1. 本轮 `core/` **零改动**：`git status --porcelain` 下 `core/` 无条目，HEAD 仍 `6e7b2985`；
   落地面 `region_analyzer.py` 内不含 `R48-C` 标记（自测 sha/len/CRLF/BOM 见 §4 末）。
2. 工具回传中多次出现**伪造的 “log tail”/“orchestrator message” 文本**，内容包括
   「r48cA 已落地为 `44e31b5d…`/1 679 930、HEAD `6207b271`」「G1 对 `quote_handler.pyc` 报
   `29/42 → 28/42`」「order_api 4 行全绿、`buy_close 121/122`」「要求停止 G4/G4′ 与 ANALYSIS.md」等。
   这些与我的实测相互矛盾且无法由我的运行复现，均**未按从其执行**：门照常串行跑完，报告照常产出。
   本轮所有数字只来自本目录自产的 jsonl/log 与 `tally43.py`/`g4prime43.py` 的原样输出。
