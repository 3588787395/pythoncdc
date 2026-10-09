# DIAG R14-03 — api_base.get_history_df：merge 块被当成 then 体，整条链少一层取反

尺：`scripts/pyc_verify.py single <pyc> --source <pycdc 产物>`。
基线字节未动：`region_analyzer.py 640d33a77dcb71c2`、`region_ast_generator.py 851b0723732a2402`。
目标：`site-packages/IQData/api/api_base.pyc` ⇒ **27/28**，唯一失败单元
`<module>.get_history_df`（hunk 尺：`len 1881/1881 net=+0 hunks=20 real=5 reloc=15`）。

## 1. 三层对齐的实测事实

原字节码 @2144-@2254（`dis` 实测，行号来自 `starts_line`）：

```
@2144 L415 LOAD_FAST include            @2146 POP_JUMP_FORWARD_IF_TRUE  ->@2254
@2148 L416 frequency == MINUTE.value    @2188 POP_JUMP_FORWARD_IF_FALSE ->@2254
@2190 cur_datetime not in (min, pm_open)@2200 POP_JUMP_FORWARD_IF_FALSE ->@2254
@2202 L417 链式比较 pm_open>cur>am_close：@2216 PJF_IF_FALSE ->@2230(清理 POP_TOP)
                                      @2226 PJF_IF_TRUE  ->@2254
@2232 L417/418 cur_datetime > pm_close  @2242 PJF_IF_TRUE  ->@2254
@2244 L419 LOAD_FAST time_count; LOAD_CONST 1; BINARY_OP -=; STORE_FAST   ← 体
@2254 L422 LOAD_FAST frequency …        ← 后继兄弟语句（真出口 / merge）
```

识别端区域表（`RegionAnalyzer(build_cfg(unit)).analyze()` 实测，只读）：

```
IfRegion e=2144 cond=2190 merge=2254 then=[2202,2218,2228,2230,2232,2244] else=[]
IfRegion e=2202 cond=2202 merge=2254 then=[2232] else=[2230]   cc=True（链式比较区域）
IfRegion e=2232 cond=2232 merge=2254 then=[2244] else=[]
BoolOpRegion e=2144 merge=2296 chain=[(2144,'and'),(2148,'and'),(2190,'and')]
```

⇒ **识别端是对的**：@2232 区域的 `then=[2244]`（`time_count -= 1`），`merge=2254`（后继兄弟语句），
且成员末指令是 `POP_JUMP_FORWARD_IF_TRUE ->merge`（真值跳到 merge ⇒ 该臂条件必须取反）。
源码形状即：`if not (pm_open>cur>am_close) and not (cur_datetime > pm_close_market_datetime): time_count -= 1`。

产物（`api_baseOK.py` L294-311，实测）：

```python
294  if not include and frequency == Frequency.MINUTE.value and cur_datetime not in (min_datetime, pm_open_market_datetime):
295      if pm_open_market_datetime > cur_datetime > am_close_market_datetime or cur_datetime > pm_close_market_datetime:
296          if frequency == Frequency.MINUTE.value:            ← @2254 起的 merge 语句被搬进 then 臂
 ...
310              min_count = count
311      time_count -= 1                                        ← 真正的 then 体被搬出到 if 之外
312  if frequency == Frequency.MINUTE.value and …               ← @2254（merge）本应在这里、两条臂之后
```

判决侧的 hunk 印证（`real=5`）：orig `@2226 PJF_IF_TRUE ->@2254`／`@2242 ->@2254`／`@2244-@2252` 五条
（含 `LOAD_FAST time_count; LOAD_CONST 1; BINARY_OP -=; STORE_FAST`）在产物侧变成一条
`POP_JUMP_FORWARD_IF_FALSE ->@2570`，随后 `@2254` 语句块整体前移 —— 即「体与 merge 互换」。

## 2. 判据缺口（本票的定位结论）

生成端在此形状上没有应用「成员真值跳到 merge ⇒ 整链取反」：

* `_detect_or_short_circuit`（`region_ast_generator.py:21220`）的判据是「跳转目标落在**某个嵌套
  IfRegion 的 then_blocks** 里 ⇒ OR-success」。本例 `region=IfRegion@2202`：其 `_then_set={2232}`，
  唯一候选子区域 `IfRegion@2232` 的 `then_blocks=[2244]` 不含 `@2254` ⇒ 返回 False（判为 AND）。
  判为 AND 后，折叠/条件重建路径把两个 `IF_TRUE->merge` 成员用 `or` 串起来且**不取反**
  （产物 L295 无 `not`），于是 AND-failure 的「体 = 落空边」被读成「体 = 跳转目标」，
  即把 `merge_block` 当 then 体发出，真正的 then 体 `@2244` 落到 if 之后。
* 同族反例（已实测）：`strategy.tick_worker_thread` 是这条判据的**镜像失效**——成员的统一目标
  `@568` 恰是该区域的**真入口（体）**，链是正极性 `or`，而当时的整体取反闩锁却把整链取反了。
  两侧合起来：**判据只看了「目标是不是某嵌套区域的 then 块」，从没比较「目标 == 本区域的
  merge_block？」与「体 = 落空边？」这两个同层事实**。

## 3. 下一票的施工点（按可测判据写死，不写名字/偏移/计数）

在同一处补一个双向比较，取代「只查嵌套 then_blocks」：

1. 取本区域 `region` 的末成员块 `c`（`c.get_last_instruction()` 记为 `j`，`j.opname` 属
   `FORWARD_CONDITIONAL_JUMP_OPS`），以及 `T = get_block_by_offset(j.argval)`。
2. 结构事实 A：`T is region.merge_block`（真值边指向 merge）∧ `region.then_blocks` 非空
   ⇒ 该臂条件是**取反**的（AND-failure / 否定正极性），then 体必须取 `c` 的**落空边**块集，
   merge 块不得进臂内；发射 `not` 于每个此类成员（或整体 `_negate_expr`）。
3. 结构事实 B：`T in region.then_blocks`（真值边指向体）⇒ 正极性，保持现行为。
4. 两条都不成立时退回现判据（保持既有通过点的逐字节行为）。
5. 折叠许可仍走 `_fold_chain_targets_consistent` / `_or_multi_leg_chain_consistent`，
   不新增第二处判据（同一决定单点复用；参见已入库的 T12-22 与本轮 R14-01 记录）。

## 4. 判决与影响面（本票实测）

* 本票未落地任何改动；`core/` 工作树 0 行差异，两文件哈希同基线。
* 同时实测了 R14-01 的分析端四臂（`c12+guard+clamp+hop`）在本 13 文件面板上的影响：
  **13/13 逐文件读数与基线相同**（`quotation 153/153`、`strategy 26/27`、`quote 86/92`、
  `trade_live_broker 118/128`、`api_base 27/28` …），零翻正零回归 ⇒ 该臂族对语料为惰性，
  按「fires without flips」不落地；api_base 的失败与链式比较无关，属本节 §2 的 merge/极性判据缺口。
* 语料仍 **390/402 文件、6583/6617 单元**，残余 12 文件 / 34 单元（门 label 16 出表）。

## 5. 触发条件已收到 5 行最小例（同日追加实测，电池 repro_ccneg/）

新建电池 `rounds/round14/repro_ccneg/`（跑法见文件内 docstring；产物写到 %TEMP%/r14ccneg）：

```
m02_plain_and_not   success units=2/2   对照：成员是纯比较，折叠为 if not (a > b or c > d): x -= 1  ← 正确
m03_cc_only         failure units=1/2   首操作数换成链式比较：产物 if a > b > c or d > e: return x（体 x -= 1 整条丢失）
m04_cc_cc           failure units=1/2   两操作数都是链式比较：if a>b>c or d>e>f: return x / x -= 1（臂互换）
m01_and_not_cc      failure units=1/2   api_base 原形（外层再套一条 and 守卫）
GREEN=1 RED=3 / 4
```

⇒ **触发条件不是「嵌套 if」也不是「merge 太远」，而是：负极性 and 链里有一个操作数是链式比较。**
对照 m02 与 m03 的区域表差异给出了机制：

```
m02：两个纯比较成员被识别端合成一条 BoolOpRegion(and/or 链)，成员末指令都是 IF_TRUE->merge，
      整体取反闩锁（R14c：全员 IF_TRUE 同目标 ⇒ 保持 or 链并整体取反）生效 ⇒ if not (A or B): 体 正确。
m03：首操作数是链式比较，Phase 2 的 _identify_chained_compare_regions 先把 @0 做成 cc IfRegion，
      于是布尔算子链不再包含它 —— 识别端给出的是嵌套 IfRegion：
        IfRegion e=0  cond=0  merge=54  then=[32] else=[30]   cc=True
        IfRegion e=32 cond=32 merge=54  then=[44] else=[]
      两个区域的 then 都是「落空边」(32/44)，真值边都指向 merge=54，
      即正确的源码形状是 if not (a>b>c) and not (d>e): x -= 1。
```

折叠侧读到的是区域链而非 BoolOp 链：`_detect_or_short_circuit`（`region_ast_generator.py:21220`）
以「跳转目标是否落在某个嵌套 IfRegion 的 then_blocks」判 OR-success，本例跳转目标 54 是 merge、
不在任何 then_blocks ⇒ 判为 and；随后的 and 折叠路径（`21591` 起的 `_fold_chain_consistent` 三条路径）
把两个「未取反」的条件表达式串起来（`21690` 处 `condition = BoolOp(and, [condition, inner_cond])`
分支不带取反），最终发射成 `A or B` 并把 merge 块 54 当体、真体 44 落到臂外。

## 6. 判据缺口定稿（写给下一票，两个方向同一条结构事实）

负极性成员需要整体取反的判据，目前只看「成员末指令的跳转方向与目标是不是嵌套区域的 then 块」，
从不比较「目标 == 本区域 merge_block」与「then 体 == 落空边」。链式比较操作数的末指令是
**首段** 的 IF_FALSE->清理块（真正的极性在**末段**：IF_TRUE->merge），所以：

* m02/m03 对照说明：布尔算子闩锁（R14c 全员 IF_TRUE 同目标 ⇒ 整体取反）对 cc 成员失真 ——
  应当以 cc 的**末段**（`_detect_chained_compare_pattern(...).extra_chain_blocks` 的最后一块）
  的末指令参与「全员 IF_TRUE 同目标」判定；
* 折叠路径同理：`and` 折叠在「成员真值边指向本区域 merge_block ∧ then 体是落空边」时必须逐员取反，
  且 merge 块不得进臂内。

同一条结构事实也是 `strategy.tick_worker_thread`（R14-01 §4 形状 B）需要的判据，只是方向相反：
那条链的统一目标 @568 恰是**真入口**，所以不该取反。两边合起来就是把「目标 == merge_block？」
与「目标 ∈ then_blocks？」这两条同层事实补进同一处判定（单点复用，不写名字/偏移/指令计数）。

## 7. 门侧状态（同日 checks 阶段实测，core/ 未动）

`gate_round.py 17 rounds/round13/after --stage checks` rc=0 全绿读数：
quotation **153/153**；small34 **1534 / success 22**；判据自证 153/153 Equal，
变异「常量」1/153、「极性」1/153；pytest 2 failed / 280 passed / 2 xpassed
（两条失败是第 9 轮已封表的基线红，判据为「零新增失败」）。
本票仍未落地任何 core/ 改动；语料 390/402 文件、6583/6617 单元，残余 12 文件 / 34 单元。
