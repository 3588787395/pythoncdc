# DIAG R14-05 — 臂归属污染的实测定位（api_base 与 strategy 的共同根，未解）

尺：`scripts/pyc_verify.py single <pyc> --source <pycdc 产物>`；本轮全程 core/ 只临时改、按哈希还原，
收尾 `git status --porcelain -- core/` = 0 行，基线字节 `region_analyzer 640d33a77dcb71c2`、
`region_ast_generator 851b0723732a2402` 未变。语料仍 390/402 文件、6583/6617 单元。

## 1. 两个目标单元的现状（R14-04 共要件施加后的读数）

* `IQData/api/api_base.pyc` ⇒ 27/28，唯一失败单元 `<module>.get_history_df`：
  基线 `hunks 20 / real 5 / reloc 15 / deleted 36 / inserted 36` →
  施加 R14-04（同目标真值边取反判据）后 `hunks 2 / real 0 / reloc 2`，
  只剩两处 `IF_TRUE` 落点差：orig `@994 ->@1098`、`@1006 ->@1040`，产物都指向 `@1254`。
* `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` ⇒ 26/27，唯一失败单元
  `<module>.Strategy.tick_worker_thread`：`@522/@534` 的 `IF_TRUE` 应为 `->@568`，产物为 `->@820`。

两处同形（见 §2），R14-04 只解掉「取反」那一半，落点一半属本票。

## 2. 原字形与区域表的偏差（实测，只读 `RegionAnalyzer(cfg).analyze()`）

api_base @994-@1040 段（`dis` 实测）：

```
@992 LOAD_FAST include          @994 POP_JUMP_FORWARD_IF_TRUE  ->@1098
@996 _query_date > pm_close     @1006 POP_JUMP_FORWARD_IF_TRUE ->@1040
@1008 链式比较 am_close < _query_date <= pm_open：@1022 IF_FALSE->@1036(清理)
                                     @1032 IF_FALSE->@1098 ; @1034 JUMP_FORWARD ->@1040
@1040 real_data = …get_real_minute_kline(symbol, True)…  @1096 JUMP_FORWARD ->@1782  ← 真臂体
@1098 下一臂（line 371 起）
```

⇒ 源码字形是 `if not include and (_query_date > pm_close or am_close < _query_date <= pm_open): 体`。

识别端实际给出的区域（关键读数）：

```
IfRegion e=996  cond=996  merge=1040  then=[1008,1024,1034,1036,1098,1142,1200]  else=[]
IfRegion e=1008 cond=1008 merge=1040  then=[1040]                                 else=[1098]
strategy: IfRegion e=512 cond=524 merge=568 then=[536,552,562,564,612,628,…]      else=[]
```

即：**条件 run 的真值边落点被登记成 merge，而 then 臂被填成「run 的其余操作数 + 后续臂」**。
`@1040`（api_base 真臂体）/ `@568`（strategy 真臂体）都不在 then_blocks 里。

## 3. 为什么生成端的极性判据必然失效（三处实测）

1. `_if_extract_condition_from_instructions` 的取反测试是
   `jumps_to_then = jump_target in _then_entry_offsets_excluding_connectors(region)`
   （`region_ast_generator.py:24256-24269`）。因 §2 的污染，落点不在 then 集 ⇒ 判成
   「需取反」，于是 `A or B` 被写成 `not A`，落点随之改投远端汇合块。
2. 已入库的 W15-C 判据 `_merge_block_is_then_exclusive`（`:20264`，正是为
   「条件跳转跨过真身、真臂整体在 merge_block」设计的）对这两个区域**返回 False**（实测：
   `tick_worker_thread` 的 512/982、`get_history_df` 的 996/1008 全 False），
   因为它的第 2 条要求「then 臂自身无有效语句」，而被污染的 then_blocks 装着操作数求值块与
   后续臂语句，条件永不成立 ⇒ 复用该判据这条路被实测堵死。
3. R14-04 的正镜像（「全员 IF_TRUE 同目标 ⇒ 正极性 or」）也实测无效：
   施加 `arms/r14_05_positive_or_reps.py` 后 api_base 仍 `hunks 2`、strategy 仍 26/27，
   因为该测试同样以 then 成员集为准（`_b138_pos_or` 永假）。

## 4. 被实测否决的一条「显而易见的修法」

把臂入口按**跳转方向**决定（`IF_TRUE ⇒ 跳边=then`）——**不成立**：
`if not c: A else: B` 编译为 `c; POP_JUMP_IF_TRUE -> B; A; …`，跳边是 **else 臂**；
而按偏移排序的现行回退（`region_analyzer.py:20338` 等三处 `sorted(cond_succs, key=start_offset)`）
对该形给出的 (A, B) 恰好正确。故方向单条判据会把普通 `if not c:` 全数改错，
必致回归；本票据此**未落地任何改动**。可用的判据必须同时看
「跳边落点是否语句体且其尾部无条件跳出」与「落空边是否直接进入后续臂」，
即需 §5 的汇合块身份一起决定。

## 5. 下一票的施工点

臂入口与汇合块的身份要一起决定，而不是先定 merge 再按 merge 反推 then：
候选是 `_identify_conditional_regions` 内 merge 计算族
（`region_analyzer.py:20225`、`:20255`、`:20310`、`:20340` `_find_nearest_common_post_dominator`）
与 `_collect_branch_blocks(then_succ, merge, then_stop)`（`:20406`）之间——
当条件的**某条真值边落点 T 自身含用户语句且尾部无条件跳到 J≠T**、
而另一条边通向的块也通向 J 时，应有 `then=T`、`merge=J`、假臂=另一条边；
现行实现把 T 认成 merge，于是 then 被 BFS 从「链的其余操作数」灌满。
先做复现电池（把 §2 的 api_base 段写成 5-8 行最小例，配合既有 `repro/`、`repro_ccneg/`），
再谈改动；改动后验收顺序：三电池全绿 → 13 文件面板 → 完整门链 label 17 vs 16（零回归）→ 提交推送。

## 6. 三个可复用红色复现例（本轮新建电池 repro_arm/，RED=3/3）

跑法：python -X utf8 .trae/specs/.../rounds/round14/repro_arm/run_arm.py（判据只喂 pycdc 产物）

| 例 | 字形 | 产物（实测） | 对应语料单元 |
|---|---|---|---|
| a01_not_and_or_cc | if not include and (qd > pm_close or am_close < qd <= pm_open): 体 | if not include: / if not qd > pm_close: / if am_close < qd <= pm_open: | api_base.get_history_df |
| a02_not_and_or_cc_tailreturn | 同上但臂体是 return | 同上，且函数尾 return 被并入 | api_base.get_history_df |
| a03_while_then_body | while 内 if dt > 'a' or 'b' < dt < 'c': 体; continue | while: / if not dt > 'a': / if 'b' < dt < 'c': | strategy.tick_worker_thread |

⇒ 该族在 5-8 行源码上即可复现，修复无需再在 1881 指令单元上迭代。

## 7. 本轮又排除的两条路（实测）

1. 生成端取反点加「前驱判据」（新 helper _r14_true_target_is_body：真值边落点 T 若除链成员与
   纯控制块外无其它语句前驱 ⇒ T 是体 ⇒ 正极性不取反），作用点
   region_ast_generator:24249-24270 的 negate 计算：三例产物**逐字节未变**
   ⇒ 该 negation 不是这些字形的发射路径（这些形根本没有 BoolOpRegion：
   api_base 的区域表里 @996/@1008 只有 IfRegion，or-run 从未被识别为布尔区域）。
2. 按跳转方向决定臂入口（IF_TRUE ⇒ 跳边=then）：反例是普通 if not c: A else: B
   （编译为 c; POP_JUMP_IF_TRUE -> B; A），跳边是 else 臂 ⇒ 该判据会把普通形全部改错，
   未做即否决（理由记录在此，避免下一票重试）。

⇒ 收敛结论：修复点在**识别端**——为正极性 or-run（真值边落进语句体）建立 BoolOpRegion，
   并同时给出 then=T、merge=T 的尾部跳出去向 J；即 R14-02 的 cc 成员归属票，
   现在有 3 个小复现例可作前置门。core 仍基线字节，未落地任何改动。
