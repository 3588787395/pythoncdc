# 第 20 轮开工前提：IfRegion 识别的**顺序墙**（本轮实测得出，非推测）

已落地（门 19）：`region_ast_generator.py dff6e81a5f2ff9f6`、`ast_generator_v2.py beeaf14435e22922`、
`region_analyzer.py 640d33a77dcb71c2`；语料 **6586/6617 单元、391/402 文件**，残余 11 文件 / 31 单元
（名册 `rounds/round19/RESIDUAL_ROUND19.md`）。

## 事实（grep/读码所得，行号为 pristine 分析端）

1. `_identify_conditional_regions` 在 **:18463**，其主循环遍历 `self.cfg.get_blocks_in_order()`
   ＝**按块偏移升序** ⇒ 父区（@992）先于子区（@996）构造。这与原则1「自底向上归约」相反。
2. 该函数内 **没有任何跨 IfRegion 的 claimed 集合**：`claimed` 只存在于
   `_identify_chained_compare_regions`（**:17994**，初值取 loop/try/with/match/assert 区域的 blocks）。
   ⇒ 构造父区时「子区已成形」这一前提不成立。
3. `_collect_branch_blocks`（**:31494**）docstring 自己声明两件事：
   「不使用 block_to_region 排除，区域归属冲突由上层调用者处理」，以及原则4 的例外
   「entry 是子入口块，必须被收集」（`stop.discard(entry)`）。
   ⇒ 把「已识别区域的内部块」当边界既拿不到（见 2），拿错了又把臂体退化成 `pass`（见下）。

## 已实测否决的一条写法（勿重复）

在 `else_stop = {then_succ} | (boundary_stop - {else_succ})` 之后加入
「`self.regions` 中 entry 等于本臂入口的区域，其 blocks 减 entry 并入本臂停止集」：

```
api_base 27/28（未翻正）  strategy 26 -> 25  klinedata 63 -> 61
quotation 153 -> 151      matcher 17 -> 16
```

⇒ 零翻正 + 四处回退。原因即上面的 2：那一刻区域集合尚未定序，
把未定形的块集当边界会切掉正常臂体。

## 下一手的可用出口（api_base + strategy，两文件各只差落点 2/4）

- 父区的正确 merge 就是**子区的 merge（@1098）**，且不必依赖子区身份即可由结构推出：
  复用 `_find_nearest_common_post_dominator`（:2354）、`_compute_in_loop_if_merge`（:2974，3 调用点）、
  `_compute_merge_from_jump_targets`、`get_if_branch_boundary_stop`（:864）、
  `[R31-B]` 同层停止集规则（:20366 / :22744）、merge-claim 守卫（:22920、:29975-29993）。
- 若要真正把子区先归约（改识别顺序），波及面大，必须先证明其余 15 个面板文件逐读数不动。
- 修 `klinedata` 的两处之一（臂尾出口身份）同样落在这条 merge/边界带上（见
  `rounds/round19/banked_r19t3/` 与 `DIAG_R1516`），三处可能共一条判据。

镜像工程师 r20d 正按上述出口施工（`D:/Temp/r20d`，只交整文件，不动实时仓库）。

## 附：`real_quote.<module>.RealQuoteData.get_tick_direction`（+1 单元档，生成端，唯一真差已定位）

`unit_diff … --all` 读 `hunks=1 landings=1 delta=1`；把对齐后**逐条带操作数**比出来，
真差只有**一处插入**，其余 11 条 `replace` 全是它造成的 2 字节位移影子：

```
ORIG  @1090 CALL ; @1100 POP_TOP ; @1102 LOAD_FAST redata ; @1104 RETURN_VALUE
PROD  @1090 CALL ; @1100 POP_TOP ; @1102 JUMP_FORWARD ->1108 ; @1104 LOAD_FAST redata ; @1106 RETURN_VALUE
                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                          原来「顺序落入共享 return redata」的那条路径，
                                                          被改成先无条件跳到 @1108（下一段 redata 检查块），
                                                          于是多插 1 条 JUMP_FORWARD（+2 字节）
```

⇒ 缺陷形状：**一条臂体以 `Call`（`self.log.quote.debug(…)`）语句结尾时，发射端在该语句之后
补了一条无条件跳转**，而原字节码此处**落空进入共享的 `return redata`**（该 `return` 在产物里也发了，
所以不是丢语句，是多插一条死跳）。
开票要点：判据应为「臂尾语句本身以无条件跳/返回结尾 or 臂的后继就是区域的 merge 且 merge 由落空边进入」
时不发这条跳；`landings=1` 那处 `@1022 JUMP_FORWARD ->199 vs ->202` 同为位移影子，不是第二缺陷
（勿按 11 条记账）。该文件另有 1 个失败单元 `get_real_minute_kline`（+2 ⇒ 不产生整文件翻绿）。
