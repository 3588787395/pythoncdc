# Round 68 · FACTS · diag2（只读诊断）

## Step 0 · baseline replay
（h62.py run --arm=landed；out 文件名带 r68d2_ 前缀避免撞车）

### targets（2 支）—— 与 BRIEF/targets.md **逐字段相同**
| 文件 | 读数 | mism |
|---|---|---|
| fly/data/quote.pyc | **70/81** sha=1a0cf2ff86193662 | build_current_period_df 115/108(5,12)、check_frequency 121/120(1,21)、check_limit 330/311(2,248)、get_individual_data 312/311(1,156)、get_price 230/232(0,172)、get_real_from_zeromq 703/678(0,660)、initImagedata 243/225(0,190)、load_bars_from_hundsun 477/483(0,410)、load_get_price 171/171(0,1)、run_individual_transform 362/321(2,263)、run_tick_socket 306/307(2,228) |
| .../matcher.pyc | **16/17** sha=74f9b8dcce12798c | match 715/715(hunks=10, first_diff=517) |

- 名下合计：defect funcs **12**（brief gap 11+1=12 ✓）、Σ\|Δ\| **121**、Σjumpdiff **23**。
- matcher 的 `715/715 数量相等、hunks=10、first_diff=517` **与 targets.md 预读数逐字段一致** ⇒ 纯发射次序缺陷的前提成立。

### canary（4 支）—— sha **逐字节命中** BRIEF §3 四个钉值
```
4d41187e356544e0  fly/data/quotation.pyc            143/143
af77224b34b203c4  fly/common/market_time.pyc          10/10
e711b8ea86d49a15  IQCommon/util/datetime_func.pyc     26/26
9d09af09249da177  IQData/utils/datetime_func.pyc      25/25
```

### battery landed（45 项）
`repro pycs discovered: 45`；**matched=174/200、defectfuncs=26、Σ|Δ|=101、ERR=0、worse-than-landed=0** —— 与 brief §4 四项全等（174/200、26、101、worse=0）。

**Step 0 结论：landed 复放 100% 与 brief 相符，无需更正。全部对照列已锁定。**

## Step 1 · hunk tables

### 仪器读数（nested_diff，CACHE-only 归一，含 EXTENDED_ARG）
```
DIFF /DefaultMatcher#11/match#16      orig=800 decomp=809 hunks=4
  insert  orig[168:168]            decomp[168:169]  = ['EXTENDED_ARG']            ← 计数伪影
  delete  orig[207:519] (312 条)   decomp[208:208]  = []                          ← 真缺陷①整块位移
  delete  orig[644:648] (4 条)     decomp[333:333]  = []                          ← 真缺陷②整块位移
  insert  orig[798:798]            decomp[483:807]  (324 条 = 312+4+8 个 EXT_ARG)  ← 两块都落到尾部
TOTAL differing code objects: 1 of 17
```
去掉 EXTENDED_ARG/CACHE 后（官方尺同尺）A=777、B=777：
- `delete A[199:500]`（301 条）+ `delete A[622:626]`（4 条）+ `insert A[775:775] B[470:775]`（305 条）
- ⇒ **数量完全相等，纯次序**；两块被**拼接后整体投到函数尾部**（紧接 `LOAD_CONST None/RETURN_VALUE` 之前）。
- quote.pyc 的 11 处：见后表；均为「少/多若干条 + 首个差异在中间」型，与 matcher 的纯次序型不同类。

### matcher::match 真原始结构（用 pyc 自带行号还原，行号即原 matcher.py 行号）
| 原行 | 语句 | 原字节码位置 |
|---|---|---|
| L198 | `if order.type == OrderType.LIMIT.value:` → POP_JUMP_IF_FALSE **2468** | o662 |
| L200/L202 | 两个 `if … : continue` | o726/o794 |
| L205 | `if self._price_limit:` → POP_JUMP_IF_FALSE **2464** | o814 |
| L207-210 | 4 个赋值 | o876-1022 |
| **L211** | `if symbol[:3] not in ('300','688','689'):` → POP_JUMP_IF_FALSE **1324** | o1066 |
| L212-217 | then：两个 `if … : continue`；末尾 `JUMP_FORWARD 2464`(A[199]) | o1108-1322 |
| **L219-247** | **L211 的 else 分支** = o1324..2462 = **A[200:499]** ⇒ 被投到尾部 |  |
| L249ish | then 出口 `JUMP_FORWARD 3210`（A[499] 后） | o2466 |
| L257-275 | L198 的 else：`if self._price_limit:` … | o2482-3206 |
| **L292** | `if self._volume_limit:` → POP_JUMP_IF_FALSE 3954（**for 体级语句，非嵌套在 L205 内**） | o3224 |
| **L317-319** | L292 的 else：`fill = order.unfilled_amount`（含 `JUMP_FORWARD 3968`）= **A[622:626]** ⇒ 被投到尾部 |  |
| L320+ | position/trade/order.fill … | o3968- |

⇒ 真实源码次序：`L211-else` 在 **中位**（o1324..2462），`L292 if / L319 else` 在 **后位**（o3224/3952..3966）。
⇒ 产物次序：`L292 if` 被塞进 L211-then 内（错挂父），`L319 else` 与 `L211-else` 被**依 (②,①) 顺序**追加到函数尾部，
   且 L211-else 被重新挂成 `if self._price_limit:`(L205) 的 `elif`。**两个位移块都属于「then 分支以 continue 结尾、
   区域 exit 被判成回边 6」的那类 if-then-else。**

### region tree 实测（regtree.py，landed 生成器 analyze()）
```
LoopRegion@6  parent=NONE  (唯一顶层)
IfRegion@664   parent=LoopRegion@6  children=[]  merge/exit 含 2464/3210 全量
IfRegion@1068  parent=LoopRegion@6  children=[]  condition_block=1110 merge_block=6  exit=6
              blocks=[3210,3226,…,4960, 1068,1110,1190,1194,1236,1316,1320,2464]   ← 3210..4960 被吸收、1324 缺席
IfRegion@1324  parent=LoopRegion@6  children=[]  condition_block=1324 merge_block=1384 exit=1384
              blocks=[1324,…,2460, 3210,3226,…,4960]                                ← 同样吸收后位
IfRegion@816   parent=LoopRegion@6  children=[]  condition_block=816 merge_block=2464 exit=2464
IfRegion@3210  parent=LoopRegion@6  children=[]  condition_block=3210 merge_block=3968 exit=3968
IfRegion@2468  parent=LoopRegion@6  children=[]  merge_block=3208
```
⇒ 49 个区域 **全部 children=[]、parent 一律 LoopRegion@6**（扁平），blocks 互相重叠且**含 set 迭代序**
   （`IfRegion@1068.blocks` 头部就是 3210…4960）。

## Step 2 · root cause（生成器线性化次序）—— 运行时 monkey-patch 探针（probe_order.py / probe_cut.py，零仓库写入）

### (a) 发射次序实测（match，PROBE_MAXD 限深）
```
_if_generate_else_branch(IfRegion@1068) | cond=1110 merge=6 exit=6 then=[1190]
     else=[1194,1236,1316,1320,2464,3210,3226,3230,3432,...]     ← 3210 起是 **for 体级** L292 的代码
   _generate_region(IfRegion@1194)
   _generate_region(IfRegion@3210)      ← L292 `if self._volume_limit:` 被挂进 L211 的 else 臂
... (IfRegion@1068 返回后，外层)
_generate_region(IfRegion@1324)         ← L211 真正的 else（o1324..2462）被排到最后
```
⇒ 与 Step 1 的位移表严丝合缝：`IfRegion@1324`（=被删的 A[200:499]）在产物里出现在尾部；
   `IfRegion@3210` 的 else（=被删的 A[622:626]，L319 `else: fill=...`）同样被推到尾部。

### (b) 泄漏代码点（core/cfg/region_ast_generator.py，只读定位）
- 函数 `_if_generate_else_branch` 在 **第 15189 行**。
- 决定性片段在 **~15414 行**：
```python
_entry_to_child_c3 = {c.entry: c for c in _reachable_children_c3}
_sorted_else_c3 = sorted(region.else_blocks, key=lambda b: b.start_offset)
_seq_buffer_c3 = []
```
  随后 `for _blk in _sorted_else_c3:` 把 **region.else_blocks 里所有块**（含被分析师误吸收进来的
  后位块 3210/3226/…）一律当作「本 if 的 else 臂」逐单元 `_process_if_blocks(unit[1], region, branch='else')`。
- 故缺陷根因 = **else_blocks 集合被跨语句吸收（region.blocks 重叠、扁平树）+ 生成器无边界地吃整个集合**；
  不是缺语句，也不是分析器判据（R64/R66 已在分析器层试过、实测 INERT）。

### (c) 判别特征（可用于收窄）
若 else 序列按 start_offset 递增走到某个块 `_blk`，其**所有前驱都不在 `region.blocks` 内**
（= 控制流从「区域外」进来 ⇒ 它其实是一条独立的 for 体级语句的入口，被吸收误判），
则该块及其后继**不属于本 else 臂**，应截断。
probe_cut.py 实测：matcher 里 29 个含多块的 IfRegion 中 **20 个会触发截断**，其中大量 `kept=[]`
（整个 else 臂被吃掉）⇒ 特征本身太宽，必须再加保护/再加门。

## Step 3 · 最小合成复现（synth/）
`synth/r68d2_else_join.py` → 编译为 `r68d2_else_join.pyc`（同为 3.11.7 win32）：
for 体内 `if A: …（then 以 continue 结尾）else: …` 之后紧跟一条 for 体级 `if B: … else: …`，
复刻 matcher 的结构身份。
```
landed:  1/2 matched   mism=[["join_after_else", 48, 48, 1, 19]]
```
⇒ 数量 48/48 相等、jumpdiff=1、首差在中位 —— **与 matcher::match 的 715/715 / hunks=10 / first_diff=517 同一签名**。
合成复现成立（landed 失败），可用于验候选是否真的咬住。

## Step 4 · 候选 cand_r68_else_join_cut（**已实测被证伪**）
spec：`diag2/specs/cand_r68_else_join_cut.json`；锚点 `count==1`（在当前落地字节上）；
只触 `core/cfg/region_ast_generator.py`；repl 在 `_sorted_else_c3` 之后插入截断循环
（判据三要素已写进注释：识别条件=else 序列中首个「全前驱皆在 region.blocks 之外」的块；
归约方式=把该块及其后从 else 臂中剔除；AST 映射=被剔除块回归外层 for 体的兄弟语句）。
构建：`h62.py build --arm=r68d2ej --dst=r68d2ej` → BOM=True / CRLF / 1 处编辑，成功。

### 五列读数（全部实测）
| 列 | landed | r68d2ej |
|---|---|---|
| synth | 1/2（48/48, jd=19） | **1/2（46/38, jd=14）** ← 计数被打破、丢语句 `if order.e: order.f=1 else: order.g=2` |
| targets quote | 70/81 | **64/81** |
| targets matcher | 16/17（match 715/715） | 16/17（**match 713/466, hunks=32**） |
| battery | 174/200 worse=0 | 未跑（已无意义） |
| canary | 4/4 sha 不变 | 未跑 |

quote 新增/恶化的 defect funcs（arm 读数）：
`build_future_fill_time 458/441`、`change_his_to_backward 356/183`、`change_his_to_forward 527/212`、
`get 62/13`、`get_Ashares_real 73/46`、`load_get_index_stocks_from_zeromq 102/91`；
`check_limit 330/311→302`。原有 11 处**一个都没修好**。

### 证伪结论
「(c) 的截断特征 + `_sorted_else_c3[0]` 无条件保护」在 45 项电池所覆盖的真实分布上是**大幅回归**：
- 它区分不出「被误吸收的后位块」与「合法的 else 臂续块」（二者在 region.blocks 污染下前驱集合同构）；
- 一旦截断，被剔除的块不会被任何外层 walker 重新发射（外层 `_process_if_blocks` 以 region 的块集合为准），
  于是**丢语句** —— synth 的 46/38 与 quote 的 `527/212` 皆由此而来。
⇒ 该路线（在 `_if_generate_else_branch` 里做 else 序列截断）**否决**；spec 不成立，撤回，不交采纳。

### 回归机理（为何「截断」必然丢语句）
arm 读数一律是 **decomp 计数远低于 orig**（`change_his_to_forward 527/212`、`get 62/13`、
`match 715/466`、synth `48→46/38`），而非「计数相等但位置不同」
⇒ 被从 `_sorted_else_c3` 剔掉的块 **没有任何外层 walker 会重新发射**：
   子区域是由本 else 序列自己经 `_entry_to_child_c3` 递归生成的（Step 2(a) 的调用树里
   `IfRegion@3210` 只在 1068 的 else 生成期出现一次），外层（LoopRegion@6 / IfRegion@816）
   的枚举按各自的 `else_blocks/then_blocks` 走，被吸收的子区域不在其中。
   所以截断＝删除。要修次序必须「截断 + 把剩余部分**让给外层重排后发射**」两件事同时做。

## Step 4b · 决定性结构读数（probe_units.py，零写入运行时探针）
```
IfRegion@1068  cond=1110 merge=6 exit=6 nblocks=22
  then_blocks = [1190]
  else_blocks = [1194,1236,1316,1320, 2464, 3210,3226,3294,3432,3574,3626,3760,3764,
                 3828,3952,3954,3968,4678,4960]
    blk@ 1194 preds=[1068,1110]                 OUT=[]                      ← 真 else 入口
    blk@ 2464 preds=[800,1320,2164,2208,2338,2380] in=[1320]  OUT=[800,2164,2208,2338,2380]
    blk@ 3210 preds=[2464,3208]                 in=[2464]     OUT=[3208]
    blk@ 3226..4960 …（每条都只被链内前驱指着）
IfRegion@816   cond=816 merge=2464 exit=2464 nblocks=39
  then_blocks = [1068,1110,1190,1194,1236,1316,1320]
  else_blocks = [1324,1372,…,2460]        ← **止于 2460，完全不含 2464/3210..4960**
```
⇒ ① 缺陷边界块 = **2464**（五条外部前驱汇入），截断判据本身指对了位置；
⇒ ② 但 **3210..4960 在整棵区域树里只出现在 1068 的 else_blocks 中**：外层 816 的 then/else 序列止于 1320/2460。
   故一旦截断，这些块没有任何消费者 ⇒ Step 4 的「截断＝删除」被逐块证实（不是偶发，是必然）。
⇒ ③ 污染来源已定位到两处可修点（均在白名单内）：
   - 分析器：`merge_block is exit` 且 exit 是回边（此处 exit=6）时，if 的 blocks/else_blocks 闭包
     **没有可停靠的汇合点**，于是一路顺着 fall-through 吃掉后继兄弟语句（2464→3210→…→4960）。
   - 生成器 `region_ast_generator.py:1590-1635` 的「孤儿块释放 / top_level_regions 过滤」：
     entry 落在外层区域 blocks 内的区域被**从顶级列表里过滤掉**（注释原话「当内部区域被过滤掉
     （因为其entry在外层区域的blocks中）时…」），于是 3210 的 IfRegion 永远拿不到外层归属 ⇒
     外层 walker 不会补发射。这正是「位移后无人认领」的机制。
⇒ ④ 所以真正的修法是「**闭包止于外部汇合点 + 被排除的区域回归外层顶级序列并按偏移发射**」两件事
   同时做（跨 region_analyzer 与 region_ast_generator），不是 `_if_generate_else_branch` 的单点截断。
   本轮 150 轮预算内无法完成该两件事并通过 45 项电池回归 ⇒ 交 NONE。

## VERDICTS
- **matcher.pyc::match → NONE（带实测）**：根因已由 Step1/2/4b 完全定量（纯次序位移 305 条、边界块 2464、
  唯一消费者是被污染的 1068-else 序列）。已证伪路线：
  (a) 在 `_if_generate_else_branch` 截断 else 序列（本臂实测：synth 48/48→46/38 丢语句、
      quote 70/81→64/81、match 715/715→713/466，全为**删除型**回归）；
  (b) `_sorted_else_c3[0]` 豁免 + 「全前驱在外」宽判据（实测 29 个多块 IfRegion 中 20 个触发、大量 kept=[]）；
  (c) 仅在 else 臂内部重排单元顺序（不可行：3210 的代码在 orig 里位于 1068 的 else 臂**之后**的
      另一条跳转目标之后，嵌在 orelse 内就不可能产生相同的跳转拓扑）。
  R64/R66 的分析器位移候选 INERT + 本臂截断候选致命回归 ⇒ 两条单点路线均被排除。
- **quote.pyc → NONE（本轮未攻）**：11 处 defect funcs 全为「计数不等 + 首差在中位」型（Step 1 表），
  与 matcher 的纯次序型不同类；且 `h62.py` 尺子下 Σ|Δ|=121 全部由 quote 贡献。
  本轮实测的 else 序列截断判据在 quote 上**净负收益**（70→64），说明该判据与 quote 的缺陷无因果交集。
- **交采纳的候选数：0**。spec `specs/cand_r68_else_join_cut.json` 已构建并实测否决，**不送采纳**（保留作反例）。

## 给中心的两条提示（带读数）
1. **采纳契约与本目标的张力**：match 在 landed 已是 715/715（数量相等），修好它只把
   `matched_functions` 5701→5702、matcher 16/17→17/17，而 **Σ|Δ| 恒为 121 不变**
   （brief §3 判据 3 要求 Σ|Δ| 净下降）。若按字面执行，任何只修纯次序缺陷的候选都会被误杀，
   建议判据 3 对「hunk 数下降且 matched_functions 上升」的纯次序修法治外。
2. **下一步该攻的确切位置**：`region_ast_generator.py:1590-1635`（顶级区域过滤/孤儿释放）与分析器
   中 `merge is exit == 回边` 的闭包停止条件；判据用「外部汇入前驱」定位边界块（matcher 实测=2464）。

## 对 BRIEF 的更正
无。Step 0 全部读数（quote 70/81、matcher 16/17 与 match 715/715/hunks=10/first_diff=517、
canary 四 sha 与 143/10/26/25、battery 174/200/26/101/worse=0/ERR=0、targets Σ|Δ|=121、12 缺陷函数）
与 brief/targets.md **逐字段一致**；targets.md 的「数量已相等 ⇒ 纯次序问题」前提成立。
