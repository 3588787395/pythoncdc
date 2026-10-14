# FIX_JOIN_IDENTITY — 臂出口 / 成员真边汇合块身份（B100 / B110 轴）

轮次：Round 4 / 簇 = REVIEW.md §6 的 A 族（B100 / B104 / B110 同判据轴）。
判定尺 = 唯一判据 `scripts/pyc_verify.py`（全程未改、未替代）。

**结论标记：「仅归档 spec 未落地」**。两个候选站点都被**实测否决**（各有插桩计数），
生产代码已逐字节回到入轮态（§6）。本轮**翻转的语料文件数 = 0**。

---

## 1. 归属失败的表述（2–3 句）

臂的「跳过边 / 成员真边」被投到**外层作用域出口**而不是紧随链的同层汇合块，其后果是臂体丢掉
成员前驱（实测 #8 `off1098 preds=[17,20,22]→[20,22]`、`off1040 preds=[18,21]→[21]`；#3 `off522/534
568→820`、`off992/1004 1038→1286`）。真正丢掉归属的不是 merge 选择，而是**一条 or 短路 run 被链识别
截断**：#3 的完整 run 是 `dt>'15:15:00' or dt<'08:30:00' or ('09:00:00'<=dt<='11:30:00')`，
`region_analyzer._detect_boolop_conditional_chain` 只交出前两个 'or' 成员（链式比较块 off536/off552
的双腿留在子区域），消费端于是按 R14c「全员 IF_TRUE 同目标 ⇒ 负极性整链」把 `A or B` 整体取反成
`not (A or B)`——公共目标 568 实际是 run 的**真入口**（臂体 `time.sleep(60)`），不是假入口。
取反改变真值表并互换两臂入口，成员真边因此外推到 820/1286。

## 2. 被实测否决的两个判别式

### 2.1 判别式 A（analyzer）：`_compute_arm_level_join` 条件 (6) 的「前向可达即弃权」

改动形：`_forward_reachable(arms, through=J)` —— current_merge 只有在**不穿过候选 J** 才可达时才保留原判，
否则交付更近的 J（J 是每条前向路径上的同层汇合块）。

实测否决证据（`D:/Temp/rrv4/p_join.py`，逐调用日志）：

```
靶 #8 <module>.get_history_df：73 次调用、1 次判真（与改动前同一处）
  arms=off1008,off1040 merge=off1782 -> None   struct=off996,off1008,off1040
  arms=off996,off1098  merge=off1782 -> None   struct=off992,off996,off1098
```

候选 off1098 在 (4) 确实被认领（off992 的块末 `POP_JUMP_FORWARD_IF_TRUE` 命中 `_armjoin_is_skip_edge`
⇒ E 箱非空），但 (6) 仍判 False：off1782 可经 **off1040 自身的 JUMP_FORWARD** 直达，不穿 off1098
——off1040 是臂体、它直接跳到外层链出口。故「穿 J 才可达」在此不成立，改动**未产生任何新判真**：
`r4_probe_index` 仍 51/67、四个语料靶读数逐位不变、`quotation` 仍 152/153。⇒ 零翻转判据，按票面即时否决形移除。

顺带定位到 (4) 的一个真实空档（本轮未修，供下一手）：**臂入口种子块从不进入候选评估**
（BFS 里 `if _s in _arm_of: continue` 先于 `_struct` 判定，种子块也不计入 `_newly`）。
最小标本 `r4v3_a14_min_arm`（`while True: if A: if B: sleep(3)`）即此形：内层 if 的前向流到达
else_succ off82（回边块），off82 是种子 ⇒ `_layers` 全空 ⇒ 返回 None。这解释了 a14 的 +6 就地材料化，
但它不是 #3/#8 的形。

### 2.2 判别式 B（generator）：`_boolop_mixed_polarity_or_chain` 的「目标必须分裂 S/F」

改动形：新增 `_boolop_or_run_continues(success, targets, chain_blocks)` —— 只读
「末成员非跳后继 S 的块末 opcode 族 + S 的落空侧正常后继 + 该后继的前向可达集是否命中链的公共目标」；
命中即返回全 False 极性表，令三处整体取反闩锁失效。

实测计数（`D:/Temp/rrv4/p_chain.py`，逐链打印成员 opcode / 目标 / S / merge）：

```
靶 #3 <module>.Strategy.tick_worker_thread：or 链 4 条，全部 ['IF_TRUE','IF_TRUE'] 同目标
  tgts=[off568[LOAD_GLOBAL,LOAD_ATTR,LOAD_CONST,PRECALL]]  S=off536[LOAD_CONST,LOAD_FAST,SWAP,COPY]  merge=off568
  tgts=[off1038[…PRECALL]]                                 S=off1006[LOAD_CONST,LOAD_FAST,SWAP,COPY]  merge=off1038
改动前 RESULT=None（4/4）  ⇒ 改动后 RESULT=HIT {0: False, 1: False}（4/4 判真）
```

**判真 4 次，单元翻转 0**：`strategy.pyc` 重生成后仍 **26/27**。首分歧从
`off522 IF_TRUE 568 vs prod 820` 变为 `568 vs prod 536`——整体取反确被抑制，产物从
`elif not (dt>'15:15:00' or dt<'08:30:00'):` 变成 `elif dt>'15:15:00' or dt<'08:30:00':` + 嵌套，
但第三个操作数（链式比较）**没有被接回同一条条件**，成员真边仍不落 568 ⇒ 边差未闭，只是换了形状。
即：本判别式修正的是**下游症状**（错误极性），根因在**上游认领**（run 截断）。按票面
「判真却零单元翻转的新谓词 = 即时否决」移除，不留零命中守卫。

## 3. 逐文件 before / after（本轮读数全部为实测原文）

| 文件 | 单元 | 入轮（= 复位后） | 判别式 A 态 | 判别式 B 态 | 首分歧证据 |
|---|---|---|---|---|---|
| `site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | `Strategy.tick_worker_thread` | 26/27 | 26/27 | 26/27 | orig off522 `IF_TRUE→568`(臂体 `time.sleep(60)`) vs prod→820；off992/1004 `1038→1286`；off568 的 preds ORIG=[512,524,562] 在 prod 少一条 |
| `site-packages/IQData/api/api_base.pyc` | `get_history_df` | 27/28 | 27/28 | 27/28 | orig off994 `IF_TRUE→1098`、off1006 `IF_TRUE→1040` vs prod→1254；块级 off1040 preds [18,21]→[21]、off1098 [17,20,22]→[20,22] |
| `site-packages/IQCommon/data/finance.pyc` | `get_fields` | 31/32 | 31/32 | 31/32 | 现行产物首分歧已移到 off8 `POP_JUMP_FORWARD_IF_NOT_NONE 740→742`（两侧目标内容同签名，`_r4v3_diag` 报「only argval deltas」）——Round-1/4 记的 off92 `236→742` 在当前字节态**已不复现**，本靶不再支持 A 族认领 |
| `site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc` | `DefaultMatcher.match` | 16/17 | 16/17 | 未测（同族未动） | 未翻；两个判别式均未在该单元产生判真 |

次靶（bar / function / strategy_universe / load_daily）未单独重测：两个改动形对四主靶的判真/翻转均为
§2 所列，未延伸到次靶（预算内优先测量主靶）。**本轮翻转的语料文件数 = 0。**

## 4. 电池与 pins 读数（复位后实测，五批 + 12 单靶 + pytest）

```
batch round4/r4_probe_index    51/67  files 15 success / 16 failure / compile_error 0 / error 0   （= 基线）
batch round1/r1_probe_index   108/110  files 44 / 2                                              （STAY）
batch round1/r1_regress_index  34/34   files 17 / 0                                              （STAY）
batch round2/r2v3_probe_index 105/126  files 41 / 21                                             （STAY）
batch round3/r3_probe_index   101/122  files 35 / 21                                             （STAY）
single fly/data/quotation.pyc                       152/153  失败单元仍 <module>.get_fundflow_day
single IQCommon/logger/handlers.pyc                  29/30
single IQEngine/data/trading_dates_mixin.pyc         13/14
single IQCommon/util/cgroup_utils.pyc                 8/8
single IQCommon/util/email_utils.pyc                  4/4
single IQData/utils/calexrights_func.pyc              8/8
single fly/common/future_contract_info.pyc           29/29
single fly/logger.pyc                                64/64
single fly/simtradding/ptradeAccount.pyc            137/137
single fly/data/quote.pyc                            86/92   （未跌）
single IQCommon/util/trade_info_utils.pyc            37/41   （未跌）
single IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc  118/128 （未跌）
pytest 6 文件                        2 failed / 277 passed / 2 xpassed（同两条 B01_simple_if_then_else_merge、BOUNDARY_02_large_function）
import 三模块 + compileall -q core   OK
四主靶 single                        strategy 26/27 · api_base 27/28 · finance 31/32 · matcher 16/17（= 入轮）
```

方法论提示（供后续票）：`pyc_verify batch` 比的是**已存在的 `*OK.py` 产物**（行内 `source_sha`），
不自动重生成。改判据后若要电池读数有意义，必须先重生成 31 条臂的 `OK.py`
（本轮按预算只做单靶 `single` + 手工重生成四主靶）。

## 5. 标记与计数（grep 用）

- 本轮试验标记：`[r4-b110-armjoin-nearjoin]`（analyzer）**残留 0**；`[R4-B110 修复·or 短路 run 完整性]`
  与 `_boolop_or_run_continues`（generator）**残留 0**。
- 实测判真 vs 翻转：判别式 A 判真 **+0** 次 ⇒ 翻转 0；判别式 B 判真 **4** 次（#3 的两条链各 2 次）
  ⇒ 翻转 **0**。二者均已移除，不留零命中守卫。
- 必须存活的原标记实测计数（复位后）：`[R2-B106` 4、`[R2-B107` 7、`[R2-B108` 5、`[R3-B115` 1、
  `[R3-B109` 3、`r3-b100-armjoin` 8（其中 `r3-b100-armjoin-tailexit` 4、`r3-b103-armjoin-termexit` 4）。

## 6. 字节复位核验（无 git）

```
core/cfg/region_ast_generator.py  bytes=3684310  lines=58669  前导 BOM=1  CRLF=58668  LF-only=0  ast.parse OK
core/cfg/region_analyzer.py       bytes=2030385  lines=31979  前导 BOM=1  CRLF=31978  LF-only=0  ast.parse OK
core/cfg/code_generator.py        未触碰
```
四主靶产物以复位后代码「先删再 `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」重生成，无手编产物。

## 7. 下一手（本轮证据指向的认领点）

1. **`region_analyzer._detect_boolop_conditional_chain`**：让 or run 把**链式比较续行成员**
   （块末为正向条件跳转、且其真/假两侧分别落到 run 的公共目标与 run 的另一出口）认作同一 run 的
   操作数，交出完整 op_chain；#3 的两条链、#8 的 `include or not (a>b or chained)` 都是同一形。
   这条同时解释 §2.2 的「抑制取反后仍不闭合」——第三个操作数无人接回。
2. **`_compute_arm_level_join` (4)**：臂入口种子块不参与候选评估的空档（a14 形），
   需在 BFS 后补「一条臂的前向流落入对侧臂入口 ⇒ 该臂入口即同层汇合块」的判定，
   并与 (6) 的退化 merge 弃权条件对齐（现有 `current_merge in _arms` 只覆盖 merge 已被填的情形）。
3. `finance.get_fields` 本轮首分歧已是纯 argval 位移（两侧目标内容同签名），**不该再记在 A 族账上**，
   建议按 EXTENDED_ARG/布局位移另查。

B99 / B116 / B117 臂本轮未触碰、仍红（不同根，见 `FIX_B99_B116.md` §8）。
本轮**未**向 `test_repros/round4/r4_probe_index.json` 追加永久臂——票面要求「修复后全绿」，
未落地即不写红臂入索引（与上一票同一处置）。
