# Round 6 · FIX_B121 —— 出口落点唯一归属判据的推广（终结 sink / 汇合块 / 回边块）

判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；interp 3.11.7 64 位）。
轴：承 R4-B116 `_boolop_chain_exits_are_distinct_sinks`（`core/cfg/region_analyzer.py:28009`，
消费点 `:28564`）与 R5-B119 `_loop_tail_exit_sink_pair`（`:28064`，唯一消费点
`core/cfg/region_ast_generator.py:51571`）的**同一不变式**——每条送出区域的出口边各有自己的落点。
插桩全部在 `D:/Temp/rrv6/`（`b121_census2.py` 链门真机普查 / `dump_cfg.py` 逐 code object CFG+区域
读数 / `hunkdiff.py` 逐指令 hunk / `widen_exp.py` 推广判据进程内实验 / `pins.py` pin 电池 /
`cand_q_freq.py` 接受形态候选），**生产目录零新增脚本、生产文件零写入**。

**结论标记：「仅归档 spec 未落地」** —— 推广后的归属判据在 B121 全部 8 个语料单元上
**True-hits = 0、翻转 = 0**，按硬性验收规则（语料单元翻转决定成败；只命中不翻转的守卫本战役
已被否决五次）不予落地。`core/cfg/region_analyzer.py` / `region_ast_generator.py` /
`code_generator.py` **本轮从未被编辑**（入轮备份 sha 与终态逐字节相同，见 §5），
故「byte-exact revert」在本票是**平凡成立**的：不存在需要回滚的改动。

---

## 1. B121 具体复现（named arm + 语料原文，含落点块与前驱集）

### 1.1 合成臂侧（交付物 1 的诚实回答：本簇在认证索引里**没有**红臂）

certified 读数 64/73 单元 / 34 文件 / 25 MATCH / 9 MISMATCH（本轮复跑逐位相同，见 §4）。
唯一属于短路链出口族的臂是 `test_repros/round6/r6_g3_chainexit_spec.pyc` / `r6_g3_chainexit_ctl.pyc`，
两者在真机管线上确实把链交到了 `:28009` 门前，且门为假：

```
CHAIN gate=False q=r6_g3_chainexit_spec@1 len=2
  m@36(or) last=POP_JUMP_FORWARD_IF_TRUE -> 目标为汇合块（非终结 return None sink）
```

⇒ 门在合成臂上同样「沉默」，但该臂**当前是 MATCH**（产物逐指令等于原始），所以它**不能**作
为反证臂：它演示的是「链出口落点不同 + 门不折叠 = 已经正确」，不是 B121 的错边形。
Round-6 REVIEW §VI 自证伪条目 2 已登记「按汇合/搬移/常量/genexpr 写的 12 条 spec 未能复现对应
语料形」，本票把这条**确认为机制层原因**（见 §3）：这些臂与语料单元里被裁决的链，其出口都
**收敛到同一个目标块**，因而根本进不了门的 `len(_targets) < 2` 分支。

### 1.2 语料侧（三个落点极性的原文读数，`dump_cfg.py` 真机管线）

**极性 A｜出口落点是汇合块（`klinedata.get_multiminute_his_data@1009`，535/536，+1）**

```
 blk@2708  n=1   preds=[1468]              succs=[2758]  last=JUMP_FORWARD 2758      own=IfRegion@1432
 blk@2710  n=14  preds=[0, 68]              succs=[2758]  last=STORE_FAST his_data_dict own=Region@2710
 blk@2758  n=2   preds=[820, 2708, 2710]    succs=[]      last=RETURN_VALUE None      own=IfRegion@0
 建区门所见：CHAIN len=2  m@0(and)/m@68(and) → 同一目标 t@2710(preds=[0,68], succs=[2758])
            ⇒ len(_targets)=1 ⇒ 门 `:28055` 直接 return False（与 sink 形状条件无关）
 hunk：replace o@2708 [JUMP_FORWARD→2758] ⇒ p@2708 [LOAD_FAST his_data_dict; RETURN_VALUE]
            = 二条边落到同一落点被换成「臂内多材料化一份」的镜像形
```

**极性 B｜出口落点是回边块（`klinedata.get_kline_by_count_new@321`，650/649）**

```
 建区门所见：CHAIN len=3  m@2742(and)/m@2746(and)/m@2764(and) → 同一目标 t@3076
            t@3076 n=2 preds=[2742,2746,2764,3068] succs=[1268]   ← 唯一后继是循环头 1268 = 回边块群
            ⇒ len(_targets)=1 ⇒ 门恒假
 hunk：replace o@2924 [EXTENDED_ARG + JUMP_BACKWARD→#230@1268] ⇒ p@2924 [JUMP_FORWARD→#608@3074]
            = 回边落点被换成正向退出落点（与极性 A 同一条边的反极性）
```

**极性 C｜出口落点应是臂内私有终结 sink，产物把它折进了尾部汇合（`quote.check_frequency@1335`，132/133）**

```
 blk@424  n=4  preds=[360,372]  succs=[436,456] last=POP_JUMP_FORWARD_IF_TRUE 456  own=TryExceptRegion@314
 blk@456  n=2  preds=[424]      succs=[]        last=RETURN_VALUE None             own=IfRegion@304   ← 私有落点
 blk@554  n=3  preds=[460,478,552] succs=[]     last=RERAISE 1                     own=TryExceptRegion@314
 blk@560  n=2  preds=[304]      succs=[]        last=RETURN_VALUE None             own=IfRegion@304   ← 区域尾落点
 blk@570/594 见链：CHAIN len=4 m@72/100/128/140(or) → 同一目标 t@204(preds=[72,100,128,140,152])
                ⇒ 门 `len(_targets)=1` 恒假（本单元的短路链是真的 BoolOp，缺陷不在折叠）
 R5-B119 亦恒假：其 C3 要求「本 CFG 偏移最大的**相邻**二块」——末二块是 554/560，
                554 是 RERAISE 协议块不是 sink ⇒ 456/560 这一对看不见。
 hunks（4 条，全部实为同一处）：
   replace o@456 [LOAD_CONST None; RETURN_VALUE] ⇒ p@456 [JUMP_FORWARD→558]
   insert  尾部 p@562 [LOAD_CONST None; RETURN_VALUE]（orig 只有 @560 一份）
```

`quote.get_real_from_zeromq` / `run_tick_socket` / `get_individual_data`（三者的首真分歧都是
「多插一条 `JUMP_FORWARD→正向汇合块`」）与极性 C 同形；`run_individual_transform` 是 B122 语句
搬移族、`build_current_period_df` 是常量族 ⇒ 不在本轴。

## 2. 推广的归属判据（一视同仁的落点所有权测试）及其真机 census

按交付物 2 的要求，把「落点是语句还是每条边自己的落点」写成**一条**与极性无关的判据
（进程内实验，未进生产文件；输入全在白名单内：块末 opcode、前驱/后继集、异常边、区域成员关系）：

```
私有落点(T, member) ⟺ preds(T) = {member} 且 T 无异常后继 且 member 的本块末指令
                        ∈ {POP_JUMP_IF_*, POP_JUMP_FORWARD/BACKWARD_IF_*, FOR_ITER} 且 argval = T.start
拒绝折叠 ⟺ 短路链的出口目标集中，存在 ≥2 个各自持有私有落点的出口边
```

该式**不要求** T 是终结 `return None` sink（汇合块、回边块同样入式），也不新增第二道特例，
只是将 R4-B116 的「≥2 互不相同 sink」换成「≥2 各自私有落点」。实测（`widen_exp.py census`，
真机全管线，逐文件统计走到「目标≥2」分支的链）：

```
site-packages/fly/data/quote.pyc                    走到 ≥2 目标的链 = 10 条  私有落点数分布 = {0×8, 1×2}  ⇒ hits=0
site-packages/IQCommon/api/klinedata.pyc            14 条                    私有落点数分布 = {0×12, 1×2} ⇒ hits=0
site-packages/IQCommon/strategy/wizard_quant_api.pyc 2 条                     私有落点数分布 = {1×2}        ⇒ hits=0
```

**True-hits = 0 / 翻转 = 0。** 原因即 §1 的三张原文：B121 的 8 个单元里，被裁决的短路链全部
**收敛到同一个目标块**（`preds(T) ⊇ 多条入边`），门在 `:28055` 的 `len(_targets) < 2` 处就已返回，
「sink 形状」那一条成员条件对这些单元**从未被求值**——所以把它推广成任意极性的私有落点测试，
对这些单元是恒等变换。反向证据同样成立：把条件放宽到「≥2 互不相同目标即拒绝折叠」（去掉
私有性要求）会在 `Quote`/`get_kline_by_count_new` 的 10+14 条**合法** or/and 链上误折
（条件上下文的 or 链本就有 then-body 与 merge 两个不同目标），那是过宽、不是欠 Reach。

## 3. 落点缺口的真实位置（把 B121 从「门欠 Reach」重归因为「折叠之后的边落地」）

- 折叠决策是正确的（这些链确实是 BoolOp 表达式），**错在折叠之后每条出口边被送到哪个块**：
  极性 A/C 是「应跳向既有落点却在臂内材料化一份」，极性 B 是「应落回回边块却落向正向退出」，
  极性 C（quote 4 条）是「臂尾私有 sink 被折进函数尾 sink」。三者在分析端的共同事实是
  `block_to_region[T] ≠ block_to_region[P]`（check_frequency 的 P@424 ∈ TryExceptRegion@314、
  T@456 ∈ IfRegion@304；get_multiminute 的 P@2708 ∈ IfRegion@1432、T@2758 ∈ IfRegion@0），
  即边跨越了区域边界 ⇒ 归属裁决需要的是**跨区域边落地表**（每条边 → 目标块身份），
  而现在两处守卫（R4 建区门 / R5 生成漏斗）都只在「块自身形状」这一层判定，读不到边集合。
- 交付物 3（不推翻 Round 5）无需检验即成立：本轮零代码改动，quotation 仍 **153/153 status=success**，
  `[R4-B116 sinkexit]`×4 与 `[R5-B119 loopsink]`×3 逐位存活（§5）。

## 4. 接受形态实测（否证，如实登记）

若极性 C 的修复只是「把臂尾 `return None` 写成真语句 + 在函数级补一条尾 `return None`」，
则在候选源码上应复原 o@456 的私有 sink。实做（`D:/Temp/rrv6/cand_q_freq.py` = quoteOK.py 的
`check_frequency` 臂尾之后补一条函数级 `return None`，判据 `single --source`，产物只在 scratch）：

```
cand_q_freq（函数级补 return None）      86/92，check_frequency 仍 Different control flow
hunkdiff(orig, cand) = 与终态逐位相同的 4 条 hunk（o@456 仍是 JUMP_FORWARD→558）
⇒ CPython 3.11 对臂尾 return None 的「折到函数尾公共 sink」不随语句位置改变而复原；
   极性 C 不可由发射序/语句补写解决 ⇒ 该形态属生成端边落地裁决，不是分析端归属判据。
```

六门禁读数（终态 = 入轮态，产物未重生成亦无需重生成）：

```
batch round6/r6_probe_index   64/73 单元  34 文件  25 success / 9 failure     = 基线（D:/Temp/r6_b121.json）
batch round1/r1_probe_index  108/110 单元  46 文件  44 / 2                     STAY
batch round1/r1_regress_index 34/34 单元   17 文件  17 / 0                     STAY
batch round2/r2v3_probe_index 105/126 单元  62 文件  41 / 21                   STAY
batch round3/r3_probe_index   101/122 单元  56 文件  35 / 21                   STAY
batch round4/r4_probe_index    77/87 单元   40 文件  30 / 10                   STAY
pytest 六套件                 277 passed / 2 failed / 2 xpassed
                              （仍 test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core OK
```

## 5. 终态完整性 · 标记 · True-hits vs flips · 残留 grep

```
core/cfg/region_analyzer.py      2052197 B / CRLF 32266 / bare LF 0 / 前导 BOM 1 / sha256[:16] 0212c54e4d0c790e
core/cfg/region_ast_generator.py 3685863 B / CRLF 58685 / bare LF 0 / 前导 BOM 1 / sha256[:16] 9c36c741bd972593
core/cfg/code_generator.py        299897 B / CRLF  6022 / 无 BOM           / sha256[:16] 28aba10bae133952
（三值与 Round-5 FIX_LOOP_SINK §4.2 登记的落地终态逐位相同 ⇒ 本轮零编辑，revert 平凡成立）

标记（core/cfg 三文件合计，逐条 = 基线）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4 · [R5-B119 loopsink] 3
残留 grep：硬编码深度/数量/语句上限 0；文件名·函数名·偏移特判 0；文本后处理 0；
  禁止前缀（_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_）新增 0；
  Region.exit 未读未写；_trailing_rn_exit_count 未动；生产目录新增脚本 0。
True-hits vs flips：推广判据 True-hits 0（quote 0/10 链、klinedata 0/14 链、wqa 0/2 链）
                    ⇒ 语料单元翻转 0、合成臂翻转 0；未追加索引臂（交付物 4 条件不成立）。
Pin（37 条同名文件全测，逐位 = 基线）：
  quotation 153/153 success ★ · trading_dates_mixin 14/14 · stock_position 37/37 · cgroup_utils 8/8 ·
  email_utils 4/4 · calexrights_func 8/8（二份）· future_contract_info 29/29 · fly/logger 64/64 ·
  logger/logger 28/28 · ptradeAccount 137/137 · executor 10/10 · history_api 19/19 · quote 86/92 ·
  trade_live_broker 118/128 · strategy 2/2·20/20·26/27 · api_base 27/28·49/49 · matcher 16/17 ·
  finance 31/32·132/132 · bar 84/85·22/22 · function 4/4·15/15·70/71 · load_daily 26/27 ·
  realtime_event_source 12/13 · profiler_func 17/17·15/15·17/18 · quote_handler 78/79 · flytools 65/66 ·
  klinedata 61/64 · wizard_quant_api 55/58（目标文件亦未回退）。未跑 402 八分片批（由主代理持有）。
```

## 6. 收窄后的残余（下一票的可执行表述）

1. **B121 不在建区门上**：把 `:28009` 的成员条件推广到任意极性落点，对 8 个单元是恒等变换
   （实测 hits 0）。任何以「推广 sinkexit/loopsink 条件」为表述的票都会得到同样的零翻转，
   应停止在此轴上继续投递。
2. 真正站点是**跨区域的出口边落地**：需要一张「边 (P→T) → 落点块」的裁决，输入仍限白名单
   （块末 opcode、succ/pred 关系、异常边、`block_to_region` 成员），语义为
   *当 `block_to_region[P] ≠ block_to_region[T]` 且 T 是既有落点（无后继终结块 / 汇合块 / 回边块）
   时，父区域不得为边 (P→T) 复制 T 的内容，也不得把 T 折进自身尾落点*。三条极性（A 复制、
   B 换向、C 折叠）在该表上是同一条边记录的三个取值。
3. 最小可证靶：`quote.check_frequency`（**仅 1 处语义差**，其余 3 条 hunk 是它的位移伪影）与
   `quote.get_individual_data`（REVIEW 登记为「仅 1 个 hunk」）——单块、单边，可作反证臂；
   `klinedata` 整文件翻面仍需 B100/B104 join 轴（`kline_datetime_list` 7 hunk 未逐个归因）
   ⇒ **klinedata 61/64 的全文件翻面在本轴不可达，如实声明**。
4. `wizard_quant_api.filter_desicion`（195/197，尾多一条 `LOAD_CONST None; RETURN_VALUE`）
   属 B112 共享 None-sink，未被本推广覆盖（其链出口同样单目标），**未取**。
