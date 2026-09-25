# Round 69 · FACTS · diag1

靶支：site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
（官方 108/119 gap 11，严格 106/123 缺陷 17）

## Step 0 · baseline replay   （landed 实测，2026-09-25）

| 项 | BRIEF/targets.md 预读数 | 我的 landed 实测 | 相符? |
|---|---|---|---|
| 官方尺 target | 108/119 gap 11 | 108/119 | ✔ |
| 官方 11 缺陷 | 见下逐函数 | 逐函数 orig/decomp/hunks/first_diff 全部逐字段相同 | ✔ |
| 严格尺 target | 106/123 缺陷 17 missing0 extra0 | 106/123 defects=17 missing=0 extra=0 | ✔ |
| 严格 17 条 | 见 targets.md L17-33 | 17 条 kind/orig/decomp 逐条相同 | ✔ |
| 金丝雀 quotation | sha 4d41187e356544e0 / 143/143 | 4d41187e356544e0 / 143/143 | ✔ |
| 金丝雀 market_time | af77224b34b203c4 / 10/10 | af77224b34b203c4 / 10/10 | ✔ |
| 金丝雀 IQCommon datetime_func | e711b8ea86d49a15 / 26/26 | e711b8ea86d49a15 / 26/26 | ✔ |
| 金丝雀 IQData datetime_func | 9d09af09249da177 / 25/25 | 9d09af09249da177 / 25/25 | ✔ |
| 45 项电池 | 182/200、缺陷 18、worse=0、ERR=0 | matched=182 total=200 bad=18、worse-than-landed=0、ERR=0 | ✔ |

官方 11 缺陷 landed 实测（h62 run --arm=landed）：
```
_process_cancel_order   294/293 hunks=16 first_diff=22
_process_order          454/396 hunks=9  first_diff=349
_sync_worker            349/347 hunks=0  first_diff=296
_trade_status_handle    114/112 hunks=0  first_diff=107
after_trading_cancel_order 155/155 hunks=3 first_diff=122
etf_basket_order        693/693 hunks=11 first_diff=216
etf_purchase_redemption 377/369 hunks=1  first_diff=37
get_max_amount          201/213 hunks=2  first_diff=18
ipo_stocks_order        1075/1075 hunks=18 first_diff=278
on_order_response       445/444 hunks=6  first_diff=57
on_trade_response       392/391 hunks=6  first_diff=57
```
**结论：Step 0 与 brief/targets.md 预读数逐字段相符，无需更正。**

产物：dump/landed.jsonl、dump/landed_canary.jsonl、dump/repro65_landed.jsonl、
dump/landed_strict.json、logs/strict_landed.txt

## Step 1 · hunk tables（nested_diff.py，按 code-object 全路径配对；jump 目标被归一化抹掉）

原文件 128 个 code object，15 个有归一化差异：
```
/TradeLiveBroker#28                         434/430 hunks=2   → 全是 NOP delete ⇒ 伪影（官方判 matched）
/get_orders#4/<listcomp>#7                   14/15  hunks=1   insert LOAD_ATTR symbol ⇒ 真（官方未列）
_process_order#22                          520/464 hunks=27   ⇒ 真·缺语句（最大矿）
_process_cancel_order#24                   344/344 hunks=5    ⇒ 位移 + NOP/EXTENDED_ARG 伪影
_sync_worker#34                            412/410 hunks=8    ⇒ 真（大块早退丢语句）
_trade_status_handle#35                    130/126 hunks=3    ⇒ 真
on_order_response#36                       511/509 hunks=3    ⇒ 真（log 语句位移）
on_trade_response#37                       448/446 hunks=3    ⇒ 真（同上）
etf_basket_order#56                        769/769 hunks=2    ⇒ 纯位移（warning 语句换位）
etf_purchase_redemption#57                 427/415 hunks=5    ⇒ 真·缺语句 + 常量被合并成串
get_max_amount#64                          218/233 hunks=1    ⇒ 纯过冲 +15（插在尾部）
ipo_stocks_order#84                       1206/1208 hunks=7   ⇒ 全 EXTENDED_ARG/JUMP 伪影+位移
after_trading_cancel_order#87              177/180 hunks=2    ⇒ 纯位移（tail return 形状）
on_order_response_list_handle#90           125/126 hunks=1    ⇒ EXTENDED_ARG 伪影
on_trade_response_list_handle#91           125/126 hunks=1    ⇒ EXTENDED_ARG 伪影
```
归一化 hunk 表全文见 `logs/nested_landed.txt`。
注意：nested_diff 的 `norm()` 把 jump 目标抹成 `J` ⇒ 严格尺的 6 个 `target_diff`
（_process_tick_order / get_ipo_stocks / on_*_list_handle / on_pre_before_trading_start /
rzrq_credit_order）在本表里**不可见**，必须用 sstrict67.py 单独量。

## Step 2 · 根因（实测，probe2.py 打印区域全字段 + CFG 指令）

### 2.1 `get_max_amount`（过冲族，official 201/213，Σ|Δ|=12；nested 218/233 hunks=1）
CFG（probe2.py orig pyc 实测，`logs/p2_getmax.txt`）：
`
@564  if error_dict.get('error_no') != 0:  IF_FALSE -> 758 ; true -> 666(return)
@666  return out_info                                   (arm1)
@758  entrust_bs == '1'          IF_FALSE -> 778 ; true -> 770
@770  entrust_type in ('6','7','9')  IF_TRUE -> 802 ; false -> 778
@778  entrust_bs == '2'          IF_FALSE -> 910 ; true -> 790
@790  entrust_type == '7'        IF_FALSE -> 910 ; true -> 802
@802  max_amount = int(float(result[0].get('enable_buy_amount')))  JUMP_FORWARD 1016
@910  max_amount = int(float(result[0].get('enable_amount')))      fall -> 1016
@1016 out_info[sid] = max_amount ; return out_info
`
真源码形状必为 `elif (A and B) or (C and D): <802> else: <910>`（802 在 orig 只有一份、
双前驱 770/790；`BoolOpRegion@758 op_chain=[(758,'and'),(770,'or')]` 佐证）。

区域树实测（同文件）：
`
IfRegion@564 region_type=IF_ELIF_CHAIN
  elif_conditions   = [758]
  elif_bodies       = [[778, 790, 910]]        <-- 802 不在 body 里
  elif_final_else   = [802]                    <-- 802 又被当 else 发一次
  _shared_block_info= {'shared_block': 802, 'inner_then_succ': 778, 'new_merge': 1016}
  children          = [Region@564, Region@666, IfRegion@778(then=[802], else=[910])]
`
**根因（函数/层/条件）**：`core/cfg/region_analyzer.py` `_check_elif_chain` 的
**shared-block 双发**：
- 判据构造点 L19420-19449：`_shared_block = inner_else_succ`，当
  `_sb_from_cond`（802 的前驱含 `_cond_chain_blocks={758,770}`）与
  `_sb_from_body`（802 的前驱 790 ∈ `inner_then_blocks`）同时成立即命中；
- 双发点 L19679-19680：`if merge_ is None or _shared_block != merge_: result['final_else'] = [_shared_block]`；
  本例 `merge_=1016 != 802` ⇒ 必然触发。
- 发射侧：`elif_final_else=[802]` 发一次，子区 `IfRegion@778.then_blocks=[802]` 又发一次
  ⇒ 产物 `trade_live_brokerOK.py` L1654-1657 与 L1658-1659 **完全重复同一句**
  `max_amount = int(float(result[0].get('enable_buy_amount')))`（+15 指令）。
- 早退条件：L19638-19677 的「链自然汇合豁免」本应拦下，但
  `_sb_then_falls_through` 要求 ① `inner_then_blocks[-1]` 的末指令**非**终结跳转
  （本例 790 末为 `POP_JUMP_IF_FALSE` 满足）、且 ② `_shared_block` 末指令为**条件跳转**
  （本例 802 末为 `JUMP_FORWARD` ⇒ 不满足）⇒ 豁免未触发，退化为双发。

### 2.2 `after_trading_cancel_order`（位移族，official 155/155 hunks=3；nested 177/180 hunks=2）
CFG 实测（`logs/p2_atco.txt`）：
`
@0    if order_param is None:  IF_NOT_NONE -> 76 ; true -> 6
@6    warning + return None                                 (arm1)
@76   isinstance(order_param, str)   true -> 118(循环) ; false -> 168
@118/132/134/158/166  for-loop（158=break 块 POP_TOP+JUMP_FORWARD ->168，166=JUMP_BACKWARD）
@168  isinstance(order_param, str)  preds=[76, 132, 158] ; true->210(return None) ; false->214
`
168 的三个前驱：76（链条件的 false 出口）+ 132（for 的 FOR_ITER 出口）+ 158（break 的
`JUMP_FORWARD`）⇒ **168 是整条 if/elif 链的 merge**，其后的 `if isinstance(...): return None
else: ...` 是链后的**独立语句**。

区域树实测：
`
IfRegion@0 region_type=IF_ELIF_CHAIN merge_block=None has_trailing_return_none=True
  elif_conditions   = [76]
  elif_bodies       = [[118,132,134,158,166]]
  elif_final_else   = [168]                 <-- 链后独立 if 被吸收成链的 else
  _shared_block_info= {'shared_block': 168, 'inner_then_succ': 118, 'new_merge': None}
  children 含 IfRegion@168(then=[210], else=[214,...])
`
**根因**：同一处 `_check_elif_chain` shared-block 双发/吸收
（L19420-19449 判据 + L19679-19680 `final_else=[_shared_block]`）。
- `_sb_from_cond`：168 的前驱 76 ∈ `_cond_chain_blocks={76}` ✓
- `_sb_from_body`：168 的前驱 132/158 ∈ `inner_then_blocks` ✓
- `merge_` 为 None ⇒ L19679 `merge_ is None` 恒真 ⇒ 无条件把 168 写进 `final_else`；
- 豁免 L19638-19650 未触发：`inner_then_blocks[-1]`=block166 末指令 `JUMP_BACKWARD`
  属终结跳转列表 ⇒ `_sb_then_falls_through=False`。
- 产物后果（实测 `trade_live_brokerOK.py` L2514-2524 + `dis`）：
  链被拉成 `elif isinstance(..): for.. / elif isinstance(..): return None / else: entrust_no=..`；
  `break` 编译为 `POP_TOP; LOAD_CONST None; RETURN_VALUE`（off=162/164/166），
  而 orig 为 `POP_TOP; JUMP_FORWARD->168` ⇒ 归一化 hunk 位移 + first_diff 前移。

### 2.3 小结（Step 2 判定）
**两支同源**：`region_analyzer.py::_check_elif_chain` 的 shared-block 处理
（L19420-19449 识别 + L19679-19680 `final_else=[_shared_block]` 注入）。
共同结构事实：`inner_else_succ` 同时是「链条件的 false 出口」与「链体内部控制流出口的汇入点」。
按 BRIEF §2「同层次结构身份判据」，可用的本区域判据是：**该块是否被本链的
`elif_bodies`/`then_blocks` 内部块直接跳入**（`_sb_from_body` 已经在算，但当前它被当成
「要双发」的充分条件，而非「这是链的 merge、不该双发」的信号）。
实测探针：`logs/p2_getmax.txt`、`logs/p2_atco.txt`、`logs/p2_atco_top.txt`（probe2.py）。

## Step 3 · 最小合成复现（synth/，landed 实测失败签名）

文件（`synth/r69d1_atco.py`、`synth/r69d1_gma.py` → 编译 `synth/r69d1_atco.pyc`、`synth/r69d1_gma.pyc`，名单 `synth/r69d1.txt`）：

```
python -X utf8 h62.py run --arm=landed --list=synth/r69d1.txt --out=dump/synth_landed.jsonl
  landed r69d1_atco.pyc  1/2  [['r69d1_atco', 33, 35, jump=3, true=12]]
  landed r69d1_gma.pyc   1/2  [['r69d1_gma',  48, 60, jump=2, true=14]]
python -X utf8 sstrict67.py build_landed synth/r69d1.txt dump/synth_landed_strict.json
  r69d1_atco  [seq_len] orig=34 decomp=37   (missing=0 extra=0)
  r69d1_gma   [seq_len] orig=48 decomp=60   (missing=0 extra=0)
  STRICT TOTAL ok=2 / functions=4 / defects=2
```

失败签名与靶支**逐字同形**（`build_landed/*r69d1*OK.py`）：

- `r69d1_atco`（对应 `after_trading_cancel_order`，+2/+3）——链后独立 `if` 被吸收成第二个 `elif`：
  ```
  elif isinstance(order_param, str):
      for order in orders: ...
  elif isinstance(order_param, str):   <-- 源码里是链后的独立 if
      return None
  else:
      return order_param.no
  ```
- `r69d1_gma`（对应 `get_max_amount`，+12，与靶支 201→213 的 +12 同量）——共享语句双发：
  ```
  elif not (entrust_bs == '1' and entrust_type in ('6','7','9')):
      if entrust_bs == '2' and entrust_type == '7':
          max_amount = int(float(result[0].get('enable_buy_amount')))
      else:
          max_amount = int(float(result[0].get('enable_amount')))
  else:
      max_amount = int(float(result[0].get('enable_buy_amount')))   <-- 与上分支重复
  ```

（Step 3 硬规则满足：有合成复现 ⇒ 才允许写 spec。）


## Step 4 · 候选与 A/B

判据三要素（识别条件 / 归约方式 / AST 映射）已随 spec 写入 `core/cfg/region_analyzer.py`
锚点上方的 `[R69-diag1 链尾合并豁免·臂末判据放宽]` 注释；只读本链自身字段
（`inner_then_blocks` / `_shared_block` / 本块末指令 opname），无新 self 状态、无跨区域包含、
无偏移或计数启发。

### 4.1 四版候选

| 版本 | spec / 臂 | 唯一改动 | synth atco | synth gma | 官方 targets | 金丝雀 quotation | battery | strict | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| A | `specs/cand_r69d1_a.json` / `r69diag1a` | L19679 `if merge_ is not None and _shared_block == merge_: set` | 2/2 | 2/2 | **106/119** | **2d5db155f62c1176 139/143** | - | - | 否决：金丝雀硬回退 |
| B | `specs/cand_r69d1_b.json` / `r69diag1b` | L19679 `if merge_ is None or _shared_block == merge_: set` | 1/2 | 1/2 | **104/119** | **2d5db155f62c1176 139/143** | - | - | 否决 |
| C | `specs/cand_r69d1_c.json` / `r69diag1c` | L19679 `if merge_ is not None and _shared_block != merge_: set` | 2/2 | 2/2 | 110/119 | 4 支 sha 全同 | worse=0 | 107/123 d=16 | **否决：语义回退，见 4.3** |
| **D** | **`specs/cand_r69d1_d.json` / `r69diag1d`** | L19637 `_sb_then_falls_through` 臂末判据 `inner_then_blocks[-1]` -> 遍历 `inner_then_blocks`（末尾 `break`） | **2/2** | 1/2（=landed，刻意不动） | **109/119** | 4 支 sha 全同 | 45 行与 landed 逐格相同 | 107/123 d=16，target_diff 集合不变 | **候选** |

读数出处：`dump/tgt|can|synth_r69diag1{a,b,c,d}.jsonl`、`dump/strict_r69diag1{c,d}.json`、
`closeout67.py battery landed r69diag1d`、`h62.py run` 全程 `ERR=None`。

### 4.2 根因：同一注入点，两族相反

唯一注入点 `core/cfg/region_analyzer.py::_check_elif_chain` **L19678-19680**
（`result['final_else'] = [_shared_block]`，L19681 挂 `shared_block_info`）。
`probe3.py` 实测区域全字段（绝对 pyc 路径，见更正 6）：

| 靶函数 | synth 见证 | sb | sb 末指令 | new_merge | sb owners | merge_（镜像 DBGSB 实测） | baseline 注入 | 语义 |
|---|---|---|---|---|---|---|---|---|
| `after_trading_cancel_order` | `r69d1_atco` | 168 / 92 | `POP_JUMP_FORWARD_IF_FALSE`（前向条件跳转） | None | `IfRegion@<sb自身>` + `Region@<sb自身>` | None | 是 | **错** |
| `get_max_amount` | `r69d1_gma` | 802 / 62 | `JUMP_FORWARD`（无条件） | 1016 / 276 | `IfRegion@778` + `IfRegion@790`（臂内嵌套 if） | None | 是 | **对**，只是多发一遍 |

- **族甲（链尾合并被当 final_else）**：sb 是整条 if/elif 链之后那个独立 `if` 的条件块
  （owners 含 `IfRegion@<sb自身>`），臂体经 FOR_ITER 出口 / break 汇入它。当成 `else:` 发射
  会换掉臂体出口 -> 产物多一条重复 elif（`build_landed/*atcoOK.py`、
  `trade_live_brokerOK.py` L2514-2524）。
- **族乙（共享语句双发）**：sb 是 `or` 链真分支的共享**语句体**，正确源形是
  `elif (A and B) or (C and D): <sb> else: <else>`。baseline 多发一遍（+12 指令），
  但 `A∧B` 真分支的赋值靠那一遍才可达，**语义正确**。
- 现有豁免 L19637-19650 `_sb_then_falls_through` 的**第二半**
  （`_shared_block` 末指令 ∈ `FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS`）
  本来就恰好分开两族；失效的是**第一半**——它只看 `inner_then_blocks[-1]`，
  而族甲的臂尾块是 `JUMP_BACKWARD` 回边块，不是汇入 sb 的那一块。
  候选 D 把第一半放宽为「遍历臂体块，任一块汇入 sb 且其末指令非显式转移」。

### 4.3 候选 C 必须否决：四把尺全绿仍是假修

`scripts/pyc_batch_verify.py` 的 **[R35] `jump_only`** 把「指令序列相同、仅跳转终点不同」计为
matched。候选 C 恰好只改了跳转终点：

- `trade_live_broker.get_max_amount`：orig `776 POP_JUMP_FORWARD_IF_TRUE -> 802 (LOAD_GLOBAL int)`；
  landed `-> 1018 (LOAD_GLOBAL int)` 可达赋值；**C `-> 1016 (LOAD_FAST max_amount)`**
  => `entrust_bs=='1' and entrust_type in (...)` 为真时**跳过赋值**，
  `out_info[sid] = max_amount` 抛 UnboundLocalError。
- `synth/r69d1_gma` 同形：landed `-> 278 (LOAD_GLOBAL int)`；**C `-> 276 (LOAD_FAST max_amount)`**，
  官方尺仍报 2/2。
- `probe4.py`（逐缺陷全量）：`get_max_amount` landed `target_diff count=0`，C `count=1 (#163)`；
  `after_trading_cancel_order` landed `count=7`，C `count=0`。

=> C 违反 ADR-1「不得以少发射换」并新增 `target_diff`，**否决**。

### 4.4 候选 D 五列读数（采纳合同逐项）

| 合同项 | 读数 | 结果 |
|---|---|---|
| 金丝雀 4 支 sha | `4d41187e356544e0` 143/143、`af77224b34b203c4` 10/10、`e711b8ea86d49a15` 26/26、`9d09af09249da177` 25/25 | 逐字节同 landed |
| 45 项电池 | `closeout67.py battery landed r69diag1d` 45 行每格相同，`worse-than-landed on 0 repro(s)`，bad 总数 18 同 landed | 过 |
| 靶支官方尺 | 108/119 -> **109/119**，缺陷 11 -> 10，**新增缺陷 0**（`get_max_amount` 仍 `201,213,2,18`，与 landed 完全一致，未被触碰） | 过 |
| ADR-1 族甲 `after_trading_cancel_order` | 官方 155/155 hunks 3 -> `nested_diff` **0 hunks、0 差异 code object**（128 全过）；严格 `seq_len 156/159` -> 156/156 缺陷消失；严格 target_diff 7 -> 0；全支 `target_diff` 函数集合 6 -> 6 **未新增**；官方+严格成对落地 | 过 |
| 合成见证咬合 | `r69d1_atco` landed 1/2 `[33,35,jump=3,true=12]` -> D **2/2** | 过 |
| 无 ERR / 锚点唯一 | 全部 `h62.py run` `ERR=None`；`mk_spec_d.py` 打印 `count = 1`；无 402 全量扫描 | 过 |

## VERDICTS

- `trade_live_broker.pyc`：**候选 `specs/cand_r69d1_d.json`（臂 `r69diag1d`）**。
  修好族甲 1 支 `after_trading_cancel_order`（官方 108->109、严格 106->107、缺陷 17->16），
  其余 10 支读数与 landed 逐项相同，金丝雀/电池零回退。
- `get_max_amount`（+ synth `r69d1_gma`，族乙共享语句双发）：**候选 NONE（本轮不修）**。
  baseline 语义正确，唯一错误是多发一遍；正解是把两个条件合成 `or` 链（generator 侧条件合成），
  不属于本根因。直接不发（候选 C）会引入官方尺看不见的分支错误。
- `etf_basket_order`（official 693/693 hunks=11）：**候选 NONE**，须靠块物理次序，违反
  「禁止按偏移启发」，与 BRIEF §8 一致，不提 spec。
- 其余 8 支（`_process_cancel_order`、`_process_order`、`_sync_worker`、`_trade_status_handle`、
  `etf_purchase_redemption`、`ipo_stocks_order`、`on_order_response`、`on_trade_response`）：
  **候选 NONE**，本轮未定位到本根因覆盖的机制。

## 对 BRIEF 的更正

1. **§8 把 11 支官方缺陷当成同一个矿，实际至少三类**：族甲（`after_trading_cancel_order`，
   链尾合并被当 final_else）、族乙（`get_max_amount`，共享语句双发）、以及与本根因无关的
   8 支位移/丢块类。按同一根因一刀切必回退（A/B/C 三版即为此）。
2. **「双发」不等于「错」**：`get_max_amount` baseline 多发的那一遍承担 `A∧B` 真分支的赋值，
   只按 hunk / 条数会把它当成必修项，删掉即候选 C 的假修。
3. **官方尺对跳转终点是盲的**：`pyc_batch_verify.bytecode_diff` 的 `[R35] jump_only` 把
   「指令序列相同、仅跳转终点不同」计为 matched。候选 C 在官方 110/119、金丝雀 4 支 sha 全同、
   电池 worse=0 全绿，产物却会 UnboundLocalError。=> **ADR-1 的「严格尺不得新增
   `target_diff`」不能只挂在位移族下，必须对本轮全部改动生效**，否则 A/B 会系统性奖励假修。
4. **严格尺每函数只报第一个缺陷**（`strict_compare` 顺序 `seq_len` -> `seq_diff` ->
   `target_diff` 即 return）。跨版本比较「缺陷种类」必须用逐缺陷全量探针（本轮
   `probe4.py`），否则会把「遮蔽解除」误读成「新增 target_diff」。本轮 C 的 #163 经
   probe4 双向证实是真新增（landed count=0，C count=1），不是遮蔽。
5. **`merge_`（`_check_elif_chain` 形参）!= `region.merge_block`**：镜像内 `DBGSB` 打点实测
   `get_max_amount` 与 `after_trading_cancel_order` 的 `merge_` **都是 None**，
   用 `merge_` 做判别式对这两支毫无区分力 —— A/B/C 三版全栽在此。
6. **`probe3.py` 内部 `os.chdir(repo)`**：传相对 pyc 路径会 `FileNotFoundError` 静默失败，
   只能传绝对路径（本轮已踩一次，得到的 `blocks=[]` 表是错位数据）。


## 勘误（Step 2，以 Step 4 实测为准）

- Step 2.1 写的 merge_=1016 != 802 是 **
egion.merge_block**，不是 _check_elif_chain
  的形参 merge_。镜像 DBGSB 打点实测：get_max_amount 与
  fter_trading_cancel_order 的 **merge_ 都是 None**（见更正 5）。
  Step 2 的根因结论（shared-block 双发注入点 L19678-19680、豁免 L19637-19650 未触发）
  不变，仅该处参数名需更正；两族的判别式也因此**不能**用 merge_，改用
  「sb 末指令是否前向条件跳转 + sb owners 是否含 IfRegion@<sb 自身>」（Step 4.2）。
- Step 2.1 早退条件里「① 790 末为 POP_JUMP_IF_FALSE 满足」是对 _sb_then_falls_through
  第一半的误读：第一半比的是 inner_then_blocks[-1] 与 _shared_block 的后继关系，
  不是块内指令本身；族甲失效的真正原因是臂尾块是 JUMP_BACKWARD 回边块
  （Step 4.2 末段、候选 D 的改动点）。
