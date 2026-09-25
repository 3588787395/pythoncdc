# Round 65 · diag1 · ANALYSIS（机制结论）

工具与原始读数在 `FACTS.md`；本文件只写「为什么」。所有结论都绑定到本层的区域字段
（`entry / blocks / exit / parent / children / merge_block / then_blocks / else_blocks / body_blocks /
try_blocks / handler_entry_blocks / try_offset_start / try_offset_end / has_trailing_return_none`），
不含函数名/文件名/偏移阈值/字面量计数型启发式。

---

## 1. 被修掉的形状：try 的「体尾 return-none 终止块」被留给父层（graph）

### 1.1 机制
CPython 3.11 把 **try 体最后一条 `return`** 发射在保护跨度**之外**、handler **之前**
（异常表 `[body_start, body_end) -> handler`，`body_end` 恰好就是这条 `LOAD_CONST None` 的偏移；
FACTS §1.6 用最小合成样本实测了这一点）。于是这类 code object 里存在一个
**不属于 try_blocks、也不属于 handler、入口 == `try_offset_end`、无后继、内容只有
`LOAD_CONST None; RETURN_VALUE`** 的块。

analyzer 的 BASIC 兜底归约（`region_analyzer.py` L26876–26894）把它归成一个
**单块 `Region(BASIC)`**，并且因为 `_is_return_none_block(block)`（L7463）为真而
`region.mark_trailing_return_none()`（L26888）。它的 `parent` 被挂到 **try 的父区域**上
（因为块的归属按结构化抢占后的剩余处理，try 区域不认领这块），于是它成了 try 区域的
**同层右兄弟**。

### 1.2 为什么归约「没失败」而发射失败了
归约层是对的（该块确实不在保护跨度内，把它塞进 `try_blocks` 反而会让异常表错一层），
失败在**发射层的槽位分配**：`_generate_try`（gen L25042–26408）在 `try_offset_end` 处收尾，
它既不认领该块（不属于 try_blocks），也不把它让给一个明确的接收者；父层序列按 children/entry
顺序发射时，该块可能
1. 被父层当成**下一个兄弟语句**发在 try 之后 → graph 的 site1（landed 产物 L399）；
2. 或者被 dedup（`generated_blocks`）吃掉，父层已经推进到下一个区域 → graph 的 site2
   （`Region@1114` 在 landed 产物里**完全没出现**）。

同一根因的两种症状，长度上正好抵消，所以官方尺是 **715/715 同长度 + jumpdiff=1** 这种
「看起来只差顺序」的读数。真正的判据不是「谁多谁少」，而是
**这个块在源语言里的结构身份 = try 体的最后一条语句**。

### 1.3 候选 A 的同层次结构身份（三要素）
- **识别条件**（全部是本层/兄弟层字段，无跨层比较）：
  `region` 是正在生成的 `TryExceptRegion`；`t = region.try_offset_end` 存在；
  `h = min(b.start_offset for b in region.handler_entry_blocks)` 存在且 `t < h`
  （⇒ 该入口**在保护跨度结束处、handler 之前**，正是「体尾」的唯一可能位置）；
  在 `self.region_analyzer.regions` 里存在一个区域 `r`，满足
  `r.parent is region.parent`（**同层兄弟**）、`type(r) is Region and r.region_type is BASIC`、
  `r.has_trailing_return_none`、`len(r.blocks)==1`、`r.blocks[0].start_offset == t`、
  `r.blocks[0].successors == []`（终止块）、且 `r.blocks[0] not in self.generated_blocks`（未被发射）。
- **归约方式**：不新建区域、不改边界；在 `_generate_try` 的收尾处（post-try 机器之后、
  `return try_ast` 之前）把该兄弟块按「每块唯一归属」原则**并入已存在的 try 节点**，
  并登记 `generated_blocks / generated_offsets / _generated_regions`
  ⇒ 从而抑制父层的兄弟发射（一次登记同时修掉 §1.2 的两种症状）。
- **AST 映射**：`ast.Try.body` 末尾追加该块生成的 `Return(value=None)`；
  不是 `finalbody`（会多一个 `POP_EXCEPT`/`JUMP` 形状），不是 `orelse`，不是父层新语句。
  守卫条件 `not try_ast.get('finalbody')` 保证有 `finally` 时不动（那时体尾 return 的发射位置由 finally 决定）。

### 1.4 为什么它不会外溢
判据的合取里有 4 个「收窄」项：`t < h`（把 `TRY@1274 try_end==handler==1618` 这种
共享入口的形状排除）、`len(blocks)==1`、`successors==[]`、`has_trailing_return_none`。
实测整个语料只有 graph 的两处命中：**全语料 398 支 sha 逐支不变**，
battery 19 支、canary 4 支也不变，而 graph 在官方尺与严格尺上同时全绿（FACTS §1.5）。
另外两处同族的 `SAME-LEN + jumpdiff=1`（`r64d5_contsink::probe`、logger）保持原状，
说明这不是一个「万能换位补丁」，而是一个点状结构修复。
合成 witness（FACTS §1.7）把「为什么这么稀有」说清楚了：触发它需要
**外层 try 体内含一个内层 try，且外层 `if` 分支以（隐式）return 结尾**；
单层 `try: …; return None / except: …`、`finally`、嵌套不同 handler 六种变体两臂都全绿。
`synth/r65_trytail_w.pyc` 在落地上 7/8、在候选 A 上 8/8，可作为入库电池。

---

## 2. 未被修的三个形状（两支证据已量化）

### 2.1 位移族（matcher 312 条 / realtime 112 条 / logger 9 条）＝ 同一个机制
三支的共同指纹（FACTS §2.1/§3/§4）：
- 归一化后 orig 与 decomp 的**总长度几乎相等**（matcher 715/715，realtime 只差 18，logger 只差 1 条 EXTENDED_ARG）；
- 一个**完整连续段**从它原来的槽位消失，出现在**父序列的末尾**；
- 段内出现 `JUMP_FORWARD ↔ JUMP_BACKWARD` 的**方向翻转**与成堆 `EXTENDED_ARG`
  ⇒ 被搬的段里有指向「它原来位置之前」的回边，这是**换位**而非丢失的物证；
- 用 `SequenceMatcher` 直接比较「消失段」与「末尾多出段」：similarity **0.9748 / 0.8907**，
  非 equal 部分只有前缀 3 条、12/19 条 EXTENDED_ARG 与一次空臂 ⇒ 同一段代码。

机制推断（未做修改验证，故本轮不交候选）：**父层发射序列是「按 children 逐个 append」构建的，
append 的顺序是区域被发现/被认领的顺序，而不是 `entry.start_offset` 的顺序**；
当一个兄弟区域的认领发生在父循环已推进到更靠后的槽之后，它就被追加到末尾。
realtime 还提供第二条线索：追加到末尾的那一段**同时被重复发射了一次 elif 测试**
（`check_trading_time` LOAD 4→5，产物第 312 行 `elif …: pass` 空臂，实测值 18 条指令）
⇒ 同一段在「槽内」与「末尾」各走了一遍，`generated_blocks` 的 dedup 只在**块**层面生效，
elif 链的**测试**是现场从 block 指令里合成的，所以测试可以重复而体不重复。
这就是 R64 说的「归属没坏、发射坏了」，本轮给出了定量版本。

修它需要的同层次判据（给 R66）：父序列的 append 结果按**每个语句的来源块 entry** 做稳定排序，
来源 entry 需要在 `_generate_block_statements`（gen L43356 / L43409）产出 AST dict 时随行携带；
这是**契约改动**（938 个 `generated_blocks` 使用点、所有 append 点），不可能塞进一份 spec 的一处锚点，
因此本轮明确不交，避免交一个「只能在一支上碰运气」的半成品。

logger 的 9 条位移有一个额外条件（FACTS §2.2）：`if q:` 的测试是**在 B4 内联合成**的
（B4 同时含语句前缀），因此 then 侧收口必须用
「同层兄弟区域 entry ∈ (test_offset, test 的假分支目标)」这个开区间判据；
现存 `[R64-B1 sibling merge-entry dispatch]`（gen L33174）只在**有真实 IfRegion** 的通道里生效。

### 2.2 真缺语句族（api_base 24 条）
`get_history_df` 缺的是 `if not tmp_dividends: tmp_dividends = engine_obj.basic_data_handler.get_dividend(symbol, None)`
整个 guard（产物里 `get_dividend` 只剩另一函数的 1 次，`grep -n` 为证），
下一条语句 `dividends = tmp_dividends[symbol]` 立刻消费该名字。
形状 = `IfRegion.then` 是单块、块内唯一语句是 `Assign(target=T)`、`T` 紧接着在同层被 LOAD、
且 test 是 `UnaryOp(Not, T)` ⇒ 这是「值上下文吞并」把**赋值目标本身**吞了。
该判据可直接检验，但它的 witness 正是 battery 里已全绿的 `r64d2_valuectx_consumer.pyc`，
改错会立刻损失一次已入库复现，本轮预算下不试。

---

## 3. 对整体算法的一句话结论
R63/R64 系列把「谁拥有块」修得基本正确（本支 4 个残余里 3 个都是**长度已对齐**的纯顺序问题），
剩下的缺陷集中在**发射层的顺序与重复**：
1. 「try 体尾的终止块」没有明确接收者 → 本轮候选 A 已修（graph 31/31 + strict 34/34，全语料惰性）；
2. 父序列 append 顺序 ≠ entry 顺序 → 需要一个携带来源 entry 的稳定排序（matcher/realtime/logger 三支同因）；
3. 内联合成测试的 then 区间没有收口步骤 → logger 的专属子形状；
4. 值上下文吞并可以吞掉赋值目标本身 → api_base 的专属形状。

优先级建议：先落候选 A（它使 `IQCommon/graph.pyc` 变成完全 OK 文件，且在全语料上零外溢），
再开一条「append-order」实验线（2 与 3 同一条判据，可以一次覆盖 matcher/realtime/logger 三支）。
