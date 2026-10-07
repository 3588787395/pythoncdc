# Round 7 · FIX_CHAIN_TAIL —— 链尾「落点叶 vs 语句」归属规则的推广（B99 第四机制）

判定尺：唯一判据 `scripts/pyc_verify.py`（未改、未替代；interp 3.11.7 64 位）。
靶文件 `site-packages/IQCommon/logger/handlers.pyc` / `<module>.TWHThreadController._target`（入轮 29/30）。
插桩全部在 `D:/Temp/rrv7/`（`trace_creator2.py` = 全方法 Return 语句**造点**追踪、
`trace_c4d.py` = 链尾落点判据逐条件拒因读数、`probe_subsets.py` = 认领子集可行性、
`final_battery.sh` = 七批 + pytest 终态读数），生产目录零新增脚本。

**结论标记：「仅归档 spec 未落地」** —— 三条判据（本轮按交办全部落地过）把区域事实重建到与
OVERWRITE 相同的口径（block 42→43、404/408 各自独立、`elif …==3 and …==11` 链成立、臂一多余
`return None` 消失），第四机制也按交办原文实现并在靶上 **True-hit**，但本轮实测推翻了交办对
「该机制即破口」的归因：多余的 `return None` **不是** `blk@1012` 造的，而是 `blk@408` 造的
（造点实测，见 §3）。按 408 这一真实形状推广会过认领（同宿主 and 链塌成
`if sys.version_info[1] == 11: pass`），语料翻转 **0**（handlers 恒 29/30）⇒ 按硬性验收规则
逐字节回滚（终态 sha256[:16] 与入轮逐位相同，见 §6）。

---

## 1. blk@1012 的归属 before→after（本轮实测，单位=块起始偏移，宿主 `_target` 44 块 / maxoff 1020）

```
                          入轮(基线)                        三处齐改后(本轮落地态)
 blk@1012 preds=[412]     own=IfRegion@412  merge_block     own=IfRegion@0（外层区域成员）
         succs=[]  rn=True 发射=函数体尾 `return None`       发射=函数体尾 `return None`（仍在）
 blk@408  preds=[90]      own=LoopRegion@90 else_blocks     own=LoopRegion@90 尾块（与 404 独立）
         发射=无（基线并臂）                                  发射=函数体尾 `return None` ← 真破口
 blk@404  preds=[390]     own=LoopRegion@90                 own=LoopRegion@90（正落落点，不发射）
 blk@412 preds=[0,46]     own=IfRegion@412（被当 merge）     own=IfRegion@0 的 else 臂入口，merge=None
 blk@1016 preds=[458]     own=IfRegion@458（entry==前驱）    同；已由 [R5-B119 loopsink] 尾声对不发射
 blk@1020 preds=[504]     own=LoopRegion@504（entry==前驱）  同；已由 B119 尾声对不发射
```

`blk@1012` 的 owner 在「本轮三处齐改」前后都**有唯一 owning 区域**（原则 2 未破坏）；它只是角色
从「merge 块的落点」变为「外层区域的成员」。本轮新判据对它 **True-hit**（认领为落点叶、不材料化），
但产物文本一字未变 ⇒ 它本来就没被材料化，认领是空转（§3）。

## 2. 本轮落地的四条判据（已实现、已命中、已回滚）

1. **上游认领**（`region_analyzer.py:20006-20023` 短路链兜底）：新增谓词
   `_else_arm_entry_is_sink_closed(block, then_succ, else_succ, struct_blocks)`，四条白名单条件
   (a) else_succ 前驱 ⊆ {header, then_succ} ∪ 短路链块 ∪ {else_succ}；(b) else_succ ∉ then 前向闭包
   （闭包不越条件结构块，异常后继不计）；(c) then 闭包每叶末 opcode ∈ {RETURN_VALUE, RETURN_CONST,
   RAISE_VARARGS, RERAISE}；(d) 至少一叶为隐式 return None。成立且 `_r49a_tail is None` ⇒ merge 保持 None。
   实测 True-hit：`CLAIM hdr@0 then@90 else@412 struct=[0,46,90] else preds=[0,46] all_in_allowed=True -> True`。
2. **站点 A**（`:20704-20741`，标记 `[R7-B99 sinkleaf]`）：共有块若为「无正常流后继 + 隐式 return None」
   落点叶，不得据其推断 merge；按前驱落点单侧保留（前驱全在 then ⇒ 退出 else_blocks）。实测 404/408 独立。
3. **链尾落点叶规则**（新，本票主交付物，标记 `[R7-B99 chaintail]`，与 `[R4-B116 sinkexit]` /
   `[R5-B119 loopsink]` / `[R6-B111 armscope]` 同族，落在 `region_analyzer.py` 同一片方法区）：
   分析端 `_chain_tail_landing_sinks()` 返回「每边落点叶」集合，生成端 `_generate_block_statements`
   单一漏斗消费（与 B119 同一漏斗、同一裁决口径）。分支 (a) 的形状判据（全部白名单输入）：
   S 为 `LOAD_CONST None; RETURN_VALUE` 隐式叶 + 无正常流后继 + 恰一正常前驱 P + P 末指令为
   `POP_JUMP_*_IF_*` 且 argval==S + P 恰有两个条件后继且另一侧非隐式叶 + **S 的所属区域 entry ≠ P**
   + S 不在「以 P 为 entry 的子区域」块集内 + S 落在本 CFG 尾部 sink 段内（C3）。
   实测靶上 `claimed=[1012]`（1008/1016/1020 依 entry/角色关系正确不认领）。
   分支 (b)（把 B119 的「函数尾声相邻双 sink 对」推广到「区域尾声」）：LoopRegion 偏移最大块为落点叶
   且其唯一前驱是该区域 condition_block/header_block/back_edge_block ⇒ 不材料化。
4. **发射侧背书**：`_process_if_blocks` 臂尾「后继是 RETURN 块就拉入语句序列」一步（
   `region_ast_generator.py:26415`）改为**尊重**分析端落点裁决，不在漏斗已返回空语句列之后用
   `_generate_return_ast`/裸 Return 再造一份（否则同一块两主、落点塌陷）。

站点 B（`:20742-20755` `[R7-B99 elseentry]`）本轮未实现：OVERWRITE 已实测其在站点 A 生效后惰性，
且本轮区域事实与 OVERWRITE 逐条相同（§2.2 的效果复现），无须该保险。

## 3. 本轮新实测：多余 `return None` 的**真实造点是 blk@408**，不是 blk@1012

`trace_creator2.py` 把 `RegionASTGenerator` 全部可调用方法包起来，按 dict 对象身份记录
`{'type':'Return','value':Constant None}` 的**首次创建点**（宿主过滤 maxoff==1020）：

```
CREATOR _generate_block_statements_body args=[408]
        stack=_loop_generate_while(core/cfg/region_ast_generator.py:8019  _eb_stmts=self._generate_block_statements(_eb))
CREATOR _generate_block_statements_body args=[408]
        stack=_process_if_blocks(:26195 bs=self._generate_block_statements(block))
CREATOR _generate_block_statements_body args=[408]
        stack=_if_generate_full_elif_chain(:16012 _post_if_stmts_elif=self._generate_block_statements(region.merge_block))
```

三条都是 **blk@408**；`blk@1012` 从未产生 Return 语句。与之自洽的实验序列：

| 认领集合（scratch 猴补丁，非产物） | 产物相对 `cand_now` | handlers |
|---|---|---|
| ∅（仅三处齐改） | 12 行差 = 多一条 indent-8 `return None` | 29/30 |
| {(a) 分支：1012} | 12 行差（同一行仍在） | 29/30 |
| {(1012,1016)} | 10 行差（改的是别处，该行仍在） | — |
| {(1008,1012,1016,1020) 全放行} | 10 行差：`elif …==3 and …==11` 塌成 `if …==11: pass` | — |
| {(b) 分支：区域尾叶（含 408）} | 13 行差：`return None` **消失**，但 and 链臂塌成 `if sys.version_info[1] == 11: pass` | 29/30 |

⇒ 交办 brief 的「删该行 = 30/30」证伪实验仍然成立（该行确实是唯一多余语句），但**该行不属于 1012**；
它属于 408——`_loop_generate_while` 在 8019 为循环出口块 `_eb` 取语句，再由同函数
`has_trailing_return_none` 机制（`region_ast_generator.py:8028` 设、`:8251-8259`
`output.extend(_trailing_return_none_stmts)`）把这条 `return None` 逐出循环、提升到父作用域序列尾。
所以「按交办原样实现链尾规则」是空转，而「按 408 的真实形状推广 B119」在同宿主上过认领：
408 与 1016/1020 一样是「区域 entry 即其唯一前驱」的出口叶，把这类叶一律不发射会同时抹掉
and-chain 出口臂的落点，链条件重建退化为嵌套 `if … : pass`（OVERWRITE §3 的
`elif ≡ else: if` 字节全等结论不受影响）。

## 4. r1_73 状态

本轮未触 `try/except/else` else 体归属轴；`test_repros/round1/r1_73_cand_fortry_sinkpair.pyc`
读数与入轮相同（1/2 MISMATCH），终态 r1 批读数见 §5（44/2 不变）。

## 5. 门禁读数（终态 = 回滚态；生产码与入轮逐位相同 ⇒ 读数即基线）

七项 + pytest 在**回滚终态**逐条实测（脚本 `D:/Temp/rrv7/final_battery.sh`，日志
`D:/Temp/rrv7/final_battery.log`（首跑 index 路径写错、六批全 FileNotFoundError，已重跑）与
`D:/Temp/rrv7/final_battery2.log`（六批实测），逐批 JSON 见下；pytest 与 single 在首跑日志内实测）：

```
single IQCommon/logger/handlers                29/30 status=failure（同一失败单元 <module>.TWHThreadController._target）
batch round1/r1_probe_index      46 文件 108/110 单元  44 success / 2 failure   STAY（D:/Temp/r1_fin.json）
batch round1/r1_regress_index    17 文件  34/34 单元   17 success / 0 failure   STAY（D:/Temp/r1reg_fin.json）
batch round2/r2v3_probe_index    62 文件 105/126 单元  41 / 21                  STAY（D:/Temp/r2_fin.json）
batch round3/r3_probe_index      56 文件 101/122 单元  35 / 21                  STAY（D:/Temp/r3_fin.json）
batch round4/r4_probe_index      40 文件  77/87 单元   30 / 10                  STAY（D:/Temp/r4_fin.json）
batch round6/r6_probe_index      37 文件  70/79 单元   28 / 9                   STAY（D:/Temp/r6_fin.json）
pytest 六套件                    2 failed, 277 passed, 2 xpassed in 9.49s = 基线那二条
                                 （test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core rc=0
```

elif 链同族 pin 的回滚终态复测（`single`，判据原文读数）：
`fly/data/quotation.pyc 153/153 success` · `fly/data/quote_handler.pyc 79/79 success` ·
`IQCommon/data/finance.pyc 31/32 failure（未移动）` ·
`IQEngine/plugins/plugin_system_matcher/matcher.pyc 16/17 failure（未移动）`。
⇒ 交办问「别的 elif 文件是否移动」：**没有**（finance/matcher 保持 31/32 与 16/17）。
落地态（§2/§3 的实验序列）未单独复测 pin：该态在靶上即已判死（同宿主过认领、翻转 0），
预算内不投入 29-pin；回滚终态三文件与入轮 **sha256 逐位相同**（§6）⇒ 其余 pin 数学上不可能变动。
402-file 八分片批按交办禁止，未跑。

## 6. 终态文件完整性 · 标记 · True-hits vs flips · 残留 grep

```
core/cfg/region_analyzer.py      入轮 2058547 B / CRLF 32336 / bare LF 0 / 前导 BOM 1 / sha256[:16] 38a1d5142d132fd7
                                 终态 2058547 B / CRLF 32336 / bare LF 0 / BOM 1 / sha256[:16] 38a1d5142d132fd7  ← 逐字节相同
core/cfg/region_ast_generator.py 入轮 3685863 B / CRLF 58685（行 58686，末行无 EOL）/ BOM 1 / sha 9c36c741bd972593
                                 终态 3685863 B / CRLF 58685 / bare LF 0 / BOM 1 / sha 9c36c741bd972593  ← 逐字节相同
core/cfg/code_generator.py        299897 B / sha 28aba10bae133952  ← 全程未触碰
site-packages/IQCommon/logger/handlersOK.py 由回滚后代码 delete+produce 重生成，读数 29/30 = 入轮读数

必须存活的标记（core/cfg 三文件合计，实测原文口径 = 基线）：
  R2-B106 4 · R2-B107 7 · R2-B108 5 · R3-B115 1 · R3-B109 3 · R4-B116 sinkexit 4 ·
  R5-B100-armjoin-trueentry 4 · R5-B119 loopsink 3 · R6-B111 armscope 3（前缀口径，逐条=基线）
残留 grep（python 计数，全 0）：`R7-B99` 0 · `[R7-B99 sinkleaf]` 0 · `[R7-B99 chaintail]` 0 ·
  `_else_arm_entry_is_sink_closed` 0 · `_chain_tail_landing_sinks` 0 · `sink_leaves` 0 ·
  禁止前缀新增方法 0 · 硬编码深度/数量/语句上限 0 · 文件名·函数名·偏移特判 0 ·
  文本后处理 0 · 生产目录新增脚本 0（插桩全在 D:/Temp/rrv7）。
True-hits vs flips：True-hits = 3（① 上游认领 True@hdr0/then90/else412；② 站点 A 对 404/408 的
  sinkleaf 归并生效（43 块 / elif 链成立 / 臂一无多余 return）；③ 链尾落点判据 (a) 对 blk@1012
  认领并命中单一漏斗）；产物文本相对入轮**已改变**（区域事实重建），相对 `cand_now` 差 1 行；
  语料单元翻转 **0** ⇒ 不予落地；交付物 4（r6 索引追加 ≥3 臂）条件不成立，未追加。
```

## 7. 收窄后的残余（下一票的可执行表述）

1. **破口块已换成 blk@408**（不是 1012）。1012 的落点叶规则（本票分支 (a)）在靶上空转，可作为
   同族规则的**陈述**保留但**不构成翻转**；408 的 `return None` 是 `_loop_generate_while:8019`
   出口块取语句 + `has_trailing_return_none`（`:8251-8259`）提升到父序列的结果 ⇒ 下一票的正解是
   「while 出口叶被逐出循环后在父作用域的**再归位**」这条发射链，而不是链尾规则。
2. **不得采用的捷径（本轮实测否证）**：把「区域 entry 即其唯一前驱」的区域尾 sink 一律不材料化
   （分支 (b)）→ and-chain/elif 的出口臂落点同批被抹，`elif A and B:` 退化为 `if B: pass`，
   handlers 仍 29/30 且新增缺陷；放宽 B116（`:28055` 的 `len(_targets)<2`）与 B119 形状门亦不得动
   （OVERWRITE §3、R5 §2.1、R6 B121 §6.1 三次否证，本轮复现同类失败）。
3. 三条已验证可复用件：上游认领谓词四条条件（闭包停止集须减 then_succ）、站点 A sinkleaf 归并、
   以及 `_chain_tail_landing_sinks` 分支 (a) 的形状门（六 items + C1/C2/C3 文档已随本票归档，
   实现体在回滚中消失，可照 §2 与本文口径重写）。
4. 若要给「区域尾落点叶」补一条安全门，候选白名单判据：该叶所属 LoopRegion 的**出口边在父区域里
   没有落点**（即父序列之后确无块）且该区域不是父 if 的**唯一出口臂**——本轮未及实现与实测，
   留给下一票；注意本靶上 408 与 1016/1020 同属「entry==前驱」形状，可辨识性必须来自
   区域/序列归属而非偏移或块号。

## 8. 交付物 2 文本（已写过、随回滚消失，供下一票原样复用）

`_else_arm_entry_is_sink_closed` 六 items（①算法依据 merge 须有正常流后继 / else 臂入口只被本 if
条件结构假边指向，白名单=块末 opcode + pred/succ + 异常后继 + 条件结构块归属；②归约顺序 NCPD、
`_compute_merge_from_jump_targets`、`_r49a_shared_sink_tail_merge` 全失败后、短路链兜底赋值前，
不回退已建区域；③唯一归属只裁 else_succ 角色、闭包不越条件结构块、sink 叶只归持其正常前驱一侧；
④嵌套按 conditional_successors 正向展开、异常叶正确计入 (c)(d)；⑤入口引用 else_blocks[0]==else_succ
时按原则 4 引用且 **merge=None 被保留**；⑥反编译流程 认领→merge None→建区保留 else 臂→AST 出
嵌套 if（与 elif 字节全等）→各臂出口叶各自独立；反向条件维持原 merge 赋值。C1 块唯一归属 ·
C2 归约顺序单调 · C3 收窄显式 return/RAISE/外部前驱不认领）——与 OVERWRITE §8 逐条一致，未改。

`_chain_tail_landing_sinks` 六 items（落点叶版）：①依据 = B116 已实测的「块优化器不合并尾部相邻两个
`LOAD_CONST None; RETURN_VALUE`」+「CPython 为每条落到函数尾的边各复制一份 sink」，故「无正常流后继 +
单前驱 + 前驱以条件跳转送出所属条件结构」的隐式叶是该边的**落点**而非语句，源文本里不存在对应语句；
落点身份与真 `else: return None` 语句身份的唯一区别是**区域归属**（真 else 体的 sink 属于「以该条件块
为 entry 的子区域」，链尾落点属于外层区域）；②归约顺序=区域识别完成后评估，不参与识别、不改成员集合；
③唯一归属=S 仍由其外层区域唯一认领、只被一条入边指向，认领只改**角色**（语句→落点），块不搬迁、
不向任何区域追加块；④嵌套=只消费 entry 侧边与成员关系，与层数/宿主类型无关；⑤入口引用=父只经子区域
entry 引用该链，S 无后继故不是任何结构体入口，且 P 的另一侧出口须有真实内容（退化 if 不认领）；
⑥反编译流程=命中→单一漏斗登记 generated 并发射空语句列→重编译在函数尾按**边数**各产一份 sink，
指令数与边归属复原；C1 局部消费（块级事实 + block_to_region/regions 成员关系，无全局态）·
C2 黑箱组合（对外只交付块集合）· C3 守卫封闭（S 须落在本 CFG 尾部 sink 段，消费点唯一）。
**本轮实测的不足**：该规则对本靶为空转（1012 本就不发射），故它虽是交办要求的正确推广，
**不是** B99 的破口判据；下一票勿再以 1012 为靶。
