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
