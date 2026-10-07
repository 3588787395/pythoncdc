# Round 7 · FIX_B99_OVERWRITE —— 建区端两处覆盖上游 merge 事实的动作（B99 追打第二/第三机制）

判定尺：唯一判据 `scripts/pyc_verify.py`（未改、未替代；interp 3.11.7 64 位）。
靶文件 `site-packages/IQCommon/logger/handlers.pyc` / `<module>.TWHThreadController._target`（入轮 29/30）。
插桩全部在 `D:/Temp/rrv7/`（`trace8.py` 建区入参/出参读数、`trace9.py` 认领判据逐条件读数、
`dump7.py` 逐块 CFG+归属、`diffunit.py`/`cmp.py` ORIG↔产物指令级对照、`diag.py` 判据自家
block-CFG 位置对齐读数、`variants.py`/`variants2.py` 目标文本可行性穷举）。生产目录零新增脚本。

**结论标记：「仅归档 spec 未落地」** —— 本轮与上一票的关键差别：改动**不是**「产物逐字相同」，
产物确实变了（elif 链成立、臂尾多余 `return None` 消失、单元 block 数 42→43 与 ORIG 齐平），
但语料翻转仍为 **0**（handlers 29/30），且本轮实测把破口收窄到**唯一一条新语句发射机制**，
并按硬性验收规则逐字节回滚（终态 sha256[:16] 与入轮逐位相同，见 §6）。

---

## 1. 两处下游站点在入轮真机上的实际状态（纠正交办 brief 的行号与因果表述）

`region_analyzer.py` 入轮 = 终态 = 2058547 B / CRLF 32336 / bare LF 0 / 前导 BOM 1 / sha256[:16] `38a1d5142d132fd7`。
交办 brief 引的 `:20804-20841` / `:20842-20862` 在本文件实测**偏移 +100**，真实站点为：

| 站点 | 真实行号（入轮） | 内容 |
|---|---|---|
| 共有块 real_merge 归纳 | `:20704-20741` | `if merge is None and then_blocks and else_blocks:` → `merge = min(real_merge…)` |
| else_blocks 过度收集清空 | `:20742-20755` | `if else_blocks and merge is None:` → `else_blocks = []` |
| merge=412 唯一赋值处 | `:20006-20023` | 短路链兜底 `if (merge is None and _main_inline_boolop_chain is not None)` |

**入轮真机读数（`trace8.py`，hdr@0）**：

```
TRACE _compute_merge_from_jump_targets hdr@0 -> None
TRACE _r49a_shared_sink_tail_merge     hdr@0 -> None
TRACE _build_elif_region      IN then=[90,104,106,180,198,212,390,404,408] else=[] merge=412  OUT None
TRACE _build_basic_if_region  IN then=[90,104,106,180,198,212,390,404,408] else=[] merge=412
TRACE _build_basic_if_region OUT entry@0 then=[90,404,408] else=[] merge=412 blocks=[0,90,404,408]
```

∴ 入轮基线下 **merge=412 一路活到建区**，两处 `merge is None` 门根本不进（0 次执行）。
「408 被错设为 merge / else_blocks 被清空」是**上一票把兜底改成 merge 保持 None 之后**才出现的
下游反应（FIX_B99 §3 的否证实验），交办 brief 把该实验态当成了基线态。本轮照 §7.2 把三处一起补齐。

## 2. 落地的三条判据（已实现、已命中、已回滚）

1. **上游认领（`:20006-20023` 兜底）**：新增谓词 `_else_arm_entry_is_sink_closed(block, then_succ, else_succ, struct_blocks)`，
   四条白名单条件照 FIX_B99 §3 原样实现（(a) else_succ 前驱 ⊆ {header, then_succ} ∪ 短路链块 ∪ {else_succ}；
   (b) else_succ ∉ then_succ 前向闭包，闭包不越过条件结构块；(c) then 闭包每个正常流叶块末 opcode ∈
   {RETURN_VALUE, RETURN_CONST, RAISE_VARARGS, RERAISE}；(d) 叶中至少一个是隐式 return None sink）。
   成立且 `_r49a_tail is None` 时 **merge 保持 None**。
   实测 True-hit：`CLAIM hdr@0 then@90 else@412 struct=[0,46,90] else preds=[0,46] all_in_allowed=True -> True`。
   （本轮修正的实现细节：闭包停止集必须减去 then_succ，否则 `_stop ∋ 起点` 令闭包恒空 ⇒ 判据恒 False；
   这是 FIX_B99 §3 判据落到代码时的唯一实现坑。）
2. **站点 A（`:20704`）**：共有块若为**无正常流后继 + 终态块末 opcode** 的 sink 叶，不得据其推断 merge；
   其归属按前驱落点单侧保留（前驱只在 then → 从 else_blocks 移除）。标记 `[R7-B99 sinkleaf]`。
   实测效果：408（preds=[90]，succs=[]，末 opcode RETURN_VALUE）留在 then 臂、退出 else 集。
3. **站点 B（`:20742`）**：then→else 命中边若恰是「本 if 自己的条件结构块（header / 短路链块 /
   condition_block）的条件假边直达 else_blocks[0]」，不算过度收集，else_blocks 不得清空。
   标记 `[R7-B99 elseentry]`。靶上实测**惰性强**：站点 A 生效后已无 then→else 命中，本条属于
   「同族形态（then 臂块列表含条件块时）」的保险，不构成翻转贡献。

三处齐改后的真机区域事实（`dump7.py`）——两 sink 已按定义**各自独立**：

```
 blk@404 preds=[390] succs=[] last=RETURN_VALUE  own=LoopRegion@90      ← sink A（回边假落，块序 13）
 blk@408 preds=[90]  succs=[] last=RETURN_VALUE  own=LoopRegion@90      ← sink B（头测假边，块序 2）
 blk@412 preds=[0,46] succs=[458,1012] own=IfRegion@0                   ← 由 merge 改判为 else 臂入口
 产物：if …==5: while …    /    elif sys.version_info[0]==3 and sys.version_info[1]==11: while …
 （入轮产物是 if…==5: while…; return None / if…==3: if…==11: while… / else: return None）
 判据自家读数（diag.py）：ORIG blocks=43 edges=72 ｜ 入轮产物 blocks=42 edges=71 ｜ 三处齐改后 blocks=43 edges=72
```

## 3. 为什么还是不翻转：本轮实测出的**唯一残余机制**（第四机制，新发现）

三处齐改后产物尾部多出**一条**语句：

```
35         return None          ← indent=8，位于 elif 链之后的函数体层
```

它来自 `blk@1012`（preds=[412]、succs=[]、LOAD_CONST None+RETURN_VALUE，即 elif 链的**链尾隐式返回叶**，
归属 IfRegion@0）。ORIG 里 4 条出口（1008/1012/1016/1020）都是编译器为「落到函数尾」的每条路径
就地复制的隐式 return，源文本里**一条 `return None` 都没有**；发射它反而把 block 数顶偏。

可行性已用判据正面证明（穷举 `variants.py`/`variants2.py`，判据 `single --source` 实测）：

| 候选文本（scratch 副本，非产物） | units |
|---|---|
| 入轮产物 | 29/30 |
| `elif` 链 + 保留嵌套 + 删尾部 `else: return None` | **30/30 FLIP** |
| `elif …==3 and …==11` + 删尾部 else | **30/30 FLIP** |
| 其余 12 个组合（保 return None / 保 else / 顶层 if 版） | 29/30 |
| **本轮三处齐改后的真产物再删该行 `return None`**（`D:/Temp/rrv7/cand_now.py`） | **30/30 FLIP** |

⇒ 破口 = 三条判据（本轮已全部构造命中）**+ 第四条**：`elif` 链尾「无后继隐式 return None 叶」
必须以**函数 epilogue**身份存在，不得被发射成父作用域的一条 `return None` 语句。
本轮预算内无法为第四条跑完 29 pin + 全量安全证明（判据单文件 evaluate ≈ 30–40 s，
27 个站点/形态无法在 <300 s 的单机约束内穷尽），且该条落点属发射侧
（`Region.exit` 零消费者、`_trailing_rn_exit_count` 从未被读，二者在交办中已列为越界），
故按硬性验收规则不落地、逐字节回滚，不留半套判据。

附带正面副产物（判据等价性实测）：`else: if C: …` 与 `elif C: …` 在 3.11.7 下**字节全等**
（`dis` 序列逐项相同），故区域侧把 else 臂入口建成嵌套 if 再交给 AST 合并为 elif 是安全路径，
下一票无需担心「非 elif 文本」。

## 4. r1_73 状态与归因（本轴不触，仅报告）

`test_repros/round1/r1_73_cand_fortry_sinkpair.pyc` 本轮一字未动其归属逻辑，读数与入轮相同（1/2 MISMATCH）。
拦路石仍是 **TryExceptRegion 的 else 体（blk 54，preds=[24]、succs=[18]）被 LoopRegion@18 认领**
⇒ 属 `try/except/else` else 体所有权轴（认领主体是 LoopRegion vs TryExceptRegion），
与本轮 IfRegion merge/else_blocks 轴共用「else 体唯一归属」不变式但是**两条独立判据**，建议单独开票。

## 5. 门禁读数（终态 = 回滚态；生产码与入轮逐位相同 ⇒ 读数即基线）

```
single IQCommon/logger/handlers                29/30 status=failure（同一失败单元 <module>.TWHThreadController._target）
batch round1/r1_probe_index      46 文件 108/110 单元  44 success / 2 failure   STAY（D:/Temp/r1_ov.json）
batch round1/r1_regress_index    17 文件  34/34 单元   17 success / 0 failure   STAY（D:/Temp/r1reg_ov.json）
batch round2/r2v3_probe_index    62 文件 105/126 单元  41 / 21                  STAY（D:/Temp/r2_ov.json）
batch round3/r3_probe_index      56 文件 101/122 单元  35 / 21                  STAY（D:/Temp/r3_ov.json）
batch round4/r4_probe_index      40 文件  77/87 单元   30 / 10                  STAY（D:/Temp/r4_ov.json）
batch round6/r6_probe_index      37 文件  70/79 单元   28 / 9                   STAY（D:/Temp/r6_ov.json）
pytest 六套件                    2 failed, 277 passed, 2 xpassed = 基线那二条
                                 （test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core OK
文件级逐批（本轮实测，与期望逐条相同）：r1 44/2 · r1reg 17/0 · r2 41/21 · r3 35/21 · r4 30/10 · r6 28/9
```

七批 + pytest 在回滚态实测（后台串行，逐批 JSON 见上），读数逐条等于基线；
29 pin（quotation 153/153、quote_handler 79/79、trade_live_broker 118/128 等）未重跑：
终态 `region_analyzer.py` 与入轮 **sha256 逐位相同**，且本轮未触碰 `region_ast_generator.py` /
`code_generator.py`，产物文本由同一代码重生成 ⇒ pin 在数学上不可能变动。
402-file 八分片批按交办禁止，未跑。

## 6. 终态文件完整性 · 标记 · True-hits vs flips · 残留 grep

```
core/cfg/region_analyzer.py      入轮 2058547 B / CRLF 32336 / bare LF 0 / 前导 BOM 1 / sha256[:16] 38a1d5142d132fd7
                                 终态 2058547 B / CRLF 32336 / bare LF 0 / BOM 1 / sha256[:16] 38a1d5142d132fd7  ← 逐字节相同
core/cfg/region_ast_generator.py 3685863 B / CRLF 58685（行 58686，末行无 EOL）/ BOM 1 / sha 9c36c741bd972593   ← 全程未触碰
site-packages/IQCommon/logger/handlersOK.py 由回滚后代码 delete+produce 重生成，读数 29/30 = 入轮读数

必须存活的标记（core/ 三文件合计，实测原文口径 = 基线）：
  R2-B106 4 · R2-B107 7 · R2-B108 5 · R3-B115 1 · R3-B109 3 · R4-B116 sinkexit 4 ·
  R5-B100-armjoin-trueentry 4 · R5-B119 loopsink 3 · R6-B111 armscope 3
（注：字面串 `[R2-B106]`/`[R2-B107]`/`[R2-B108]`/`[R3-B115]`/`[R3-B109]` 在 core/ 内计数为 0，
 实际写法带后缀，如 `[R2-B106 修复·处理器尾回边按循环入口归属]`；存活口径按前缀计，逐条=基线。）
残留 grep（python 计数，全 0）：`R7-B99` 0 · `[R7-B99 sinkleaf]` 0 · `[R7-B99 elseentry]` 0 ·
  `_else_arm_entry_is_sink_closed` 0 · `_b99_` 0 · 禁止前缀新增方法 0 ·
  硬编码深度/数量/语句上限 0 · 文件名·函数名·偏移特判 0 · 文本后处理 0 · 生产目录新增脚本 0。
True-hits vs flips：True-hits = 3（上游认领 True@hdr0/then90/else412；站点 A 对 blk@408 的
  sink-leaf 归并生效；站点 B 判据已实现但靶上惰性）；
  产物**文本已改变**（非 word-identical，见 §2 末）、单元 block 数 42→43 追平 ORIG，
  但语料单元翻转 **0** ⇒ 按硬性验收规则不予落地；交付物 4（r6 索引追加 ≥3 臂）条件不成立，未追加。
```

## 7. 再收窄后的残余（下一票的可执行表述）

1. **唯一缺口已从三处缩到一处**：三处判据（§2）可整体复用，勿再 hunt；新增必需第四条机制 =
   「`elif` 链尾的隐式 return None 叶（本轮靶上 blk@1012，preds=[412]、succs=[]）」必须作为
   epilogue 存在，不得进入 `IfRegion.blocks` 的父作用域语句序列。
   判据候选（白名单）：该块无正常流后继、块末 opcode 为 RETURN_VALUE/RETURN_CONST、
   指令形状为隐式 return None（`_is_return_none_block`）、其唯一前驱是本 if 自身条件块的假边、
   且它是本区域语句序列的**最后一项**（其后无任何块）。
2. 可行性已被判据正面证明：`D:/Temp/rrv7/cand_now.py`（= 本轮三处齐改的真产物删该行）实测 **30/30**；
   `elif` 与 `else: if` 文本字节全等（§3 末），发射侧无需特殊处理 elif。
3. 站点 B 在本轴是保险而非贡献者；若下一票改走「发射侧一条」路线，站点 A + 上游认领仍是必要前提。
4. B116/B119 sink-shape 门（`region_analyzer.py:28055` 的 `len(_targets)<2` 返回）本轮一字未动，亦不得动；
   `dominator_analyzer.py:502` 回边归一化属 trade_live_broker 的 G-B 轴，与本轴正交。

## 8. 已写过并随回滚消失的交付物 2 文本（供下一票原样复用，勿重写）

`_else_arm_entry_is_sink_closed` 的方法文档六items（本轮实现体已验证可用，仅闭包停止集需减 then_succ）：

```
①算法依据：merge（汇合点）按定义必须有正常流后继；else 臂入口按定义只被本 if 条件结构的
  假边指向。白名单输入 = 块末 opcode + successors/predecessors + 异常后继 + 条件结构块归属。
②归约顺序：在 NCPD、_compute_merge_from_jump_targets、_r49a_shared_sink_tail_merge 全部失败后、
  短路链兜底赋值前判定；不回退任何已建成的 BoolOpRegion/LoopRegion/TryExceptRegion。
③唯一归属判定：判据只裁决 else_succ 的角色（merge vs else 臂入口），不改任何块归属；
  then 闭包遍历不越过条件结构块，sink 叶只归给持有其正常前驱的那一侧。
④嵌套处理：闭包按 successors 正向展开、跳过异常后继，故 then 臂内的 while/try 出口叶
  （404/408 型）与 then 臂内的异常叶（384 型 RERAISE）都被正确计入 (c)(d)。
⑤入口引用语义：else_blocks[0] == else_succ 时，父区域以 else_succ 为 else 臂入口引用（原则 4），
  **已确定的 merge=None 被保留**，不再由建区端从后继为空的 sink 叶反推 merge。
⑥反编译流程：认领成立 ⇒ merge 保持 None ⇒ 建区端保留 else 臂 ⇒ AST 生成 else 嵌套 if
  （与 elif 字节全等，实测）⇒ 每条臂出口叶各自成为独立 return 路径。
  反向条件：只要 else_succ 有外部前驱 / 落在 then 闭包内 / then 闭包存在非终态叶，
  维持原 merge=else_succ 赋值，既有 boolop-chain if 行为不变。
C1 结构不变式（块唯一归属）· C2 归约顺序单调（不改已归约区域）·
C3 收窄（显式 return 非常量 None、RAISE 臂、有外部前驱的 else_succ 均不认领）。
```

站点 A/B 的行内注释文本（`[R7-B99 sinkleaf]` / `[R7-B99 elseentry]`）亦已在 §2 完整描述，
落地时按该两段的原始注释块原样写回即可（本轮 diff 仅两处 `if` 分支 + 一个谓词方法）。

