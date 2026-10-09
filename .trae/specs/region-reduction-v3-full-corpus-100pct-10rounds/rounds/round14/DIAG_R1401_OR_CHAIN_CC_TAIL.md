# DIAG R14-01 — `or` 链的末操作数是链式比较：整族不成，四处阻塞点逐一定位

尺：`scripts/pyc_verify.py single <pyc> --source <pycdc 产物>`（pylingual，CPython 3.11.7 x64）。
基线字节：`core/cfg/region_analyzer.py` sha256[:16] `640d33a77dcb71c2`，
`core/cfg/region_ast_generator.py` `851b0723732a2402`；本票全程 **仓库 core/ 未落地任何改动**
（收尾 `git status --porcelain -- core/` = 0 行，两文件哈希与上同）。
全部臂都在 `D:/Temp/r150/` 里做「临时写入→实测→按哈希还原」，还原断言逐次通过。

## 1. 先纠正我自己的一次空判据（重要，防止后人复用错误读数）

上一会话我用 9 个手写最小例（`if A or B or a<b<c: …`）验证「该形态已正确」，命令是
`pyc_verify.py single <由该 .py 编出的 pyc> --source <同一个 .py>` ⇒ 六/九个读数全绿。
**那是空判据**：判据比的是「源码重编字节码 vs 原 pyc」，而源码就是原 pyc 的来源，必然相等，
跟反编译器无关。本会话改为 `pycdc.py --region <pyc> -o <prod>` 后 `single <pyc> --source <prod>`，
同批 9 例 **9/9 全红**：

```
r01_or_cc_return.py   failure units=1/2   （最小例，7 行）
v1_while_try_cont.py  failure units=1/2   v5_two_elif_cc.py   failure units=1/2
v2_if_only_cont.py    failure units=1/2   v6_guard_clause.py  failure units=1/2
v3_try_no_while.py    failure units=1/2   v7_ccarm_as_elif.py failure units=1/2
v4_cc_in_middle.py    failure units=1/2   v8_two_cc_arms.py   failure units=1/2
RED=9 / 9
```

电池已入库：`rounds/round14/repro/`（9 个源文件 + `run_repro.py`，产物写到 `%TEMP%/r14repro`）。
跑法：`python -X utf8 .trae/specs/…/rounds/round14/repro/run_repro.py`。

⇒ **结论改判**：`if/elif <A or B or 链式比较>: …` 是一个通用缺陷族（识别端），
不是 `strategy.tick_worker_thread` 的个案落点问题。残余表里
`trade_live_broker._sync_worker`（登记「链式比较腿＋搬位」）、`strategy` 等单元属同族候选。

## 2. 最小例的字节码事实（r01，`f(dt_strf)`）

```
@2  COMPARE_OP >            @12 POP_JUMP_FORWARD_IF_TRUE  ->@58   (操作数 A)
@14 COMPARE_OP <            @24 POP_JUMP_FORWARD_IF_TRUE  ->@58   (操作数 B)
@26 LOAD_CONST/LOAD_FAST/SWAP/COPY(2)/COMPARE_OP  @40 PJF_IF_FALSE ->@54  (链式比较头段)
@42 COMPARE_OP <            @50 PJF_IF_FALSE ->@62 ; @52 JUMP_FORWARD ->@58 (末段：真=@58 体, 假=@62 elif)
@54 POP_TOP ; @56 JUMP_FORWARD ->@62                             (链式比较清理块)
@58 LOAD_CONST 1; RETURN_VALUE    @62 elif 条件…
```

识别端现状（实测，未打补丁）：

```
BoolOpRegion e=0  chain=[(0,'or'),(14,'or')]  merge=58  blocks=[0,14]
IfRegion     e=26 merge=58 cc=True            blocks=[26,42,54,58,62]     ← 链式比较区域
IfRegion     e=0  cond=14 merge=58            blocks=[0,26,42,52,54,62,74,78]
产物：if not (A or B):
          if '11:30:00' < dt_strf < '12:30:00': return 1
          elif …                                ← 语义已错（A 真时不发体）
```

## 3. 四处阻塞点（行号按上面基线字节；每一处都用臂实测「打开后走到下一处」）

| # | 位置 | 判据现状 | 打开它的臂 | 实测读数 |
|---|---|---|---|---|
| 1 | `_detect_boolop_conditional_chain` 认领守卫 `region_analyzer.py:29975-29978`（`if ft_succ in claimed: break` / `if ft_succ in self.block_to_region: break`） | 链式比较区域的 **入口块** 已被该区域认领 ⇒ 走链时直接断链 | `c12`＝在两行同一谓词 `_r14_cc_run_member(ft_succ, chain)`（blk 是带 `chained_compare_ops≥2` 的 IfRegion 入口 ∧ 链前缀全员跳同一块 T ∧ 该链式比较成功腿落到 T） | r01 的 walk 是 `skip_claimed_check=False`，**先断在这一处**；打开后链长到 3 成员（marker：`TWZ 29858 cur=26 chain=[(0,'or'),(14,'or'),(26,'and')]`） |
| 2 | hop 安全检查 `:29786-29795` | 拿链式比较头块的 **短路腿**（→清理块 @54）与 chain[0] 的共享目标 T（@58）比，不等就 `chain.pop()` | `guard`＝追加 `and not self._r14_cc_operand_reaches(current, _first_jt)` | 谓词实测 True（`DBG _r14_cc_operand_reaches 26 -> True`）；单用 `guard` 对 r01 无效（因阻塞在 #1） |
| 3 | 链尾裁剪钳 `_w14_*` `:30234-30260`（`len(chain)>=3` ∧ 首成员 IF_TRUE 目标 T0 ∧ 末成员 fall-through ≠ T0 ⇒ 裁剪到 T0 一致前缀） | 链式比较末成员的落空边不是 T0 ⇒ 裁回 2 成员 | `clamp`＝同一谓词豁免（`not self._r14_cc_operand_reaches(_w14_last_blk, _w14_t0)`） | 打开 #1+#2+#3 后 `WALK 0 -> [(0,'or'),(14,'or'),(26,'or')]`（三成员存活） |
| 4 | `_boolop_resolve_merge` 的 `elif` 分支 `:27989-27998`（合并块＝末成员跳转腿落点） | 得到清理块 @54（r01）/ @564（strategy）；既有 `_is_chained_compare_cleanup_block`（`:32231`）**只认 SWAP+POP_TOP**，而 3.11 的清理块是 `POP_TOP; JUMP_FORWARD` ⇒ 解析不通过 | `hop`＝新增 `_r14_cc_cleanup_hop`（恰为 POP_TOP+JUMP_FORWARD 时取其目标） | merge 由 54 → 62（r01）、564 → 612（strategy），与「普通三操作数 or 链末成员 IF_FALSE 直接落 else 入口」一致 |

`#1` 之所以以前没人碰：既有 hop 机制（`:29773-29810`，注释自称「chained compare 区域整体作为单个操作数」）
默认链式比较区域已在 `self.regions` 里 —— 区域确实在（实测 `cc_visible=[(26, 58, ['<','<'], …)]`），
但它同时把入口块登记进 `claimed`/`block_to_region`，于是 walk 在 **#1 就断**，hop 从未被执行。
即 **hop 机制对 `skip_claimed_check=False` 的 walk 是死代码**。

## 4. strategy 是第二种子形（形状 B）

`IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` ⇒ `<module>.Strategy.tick_worker_thread`
（26/27，该文件唯一失败单元；L324 体量 288 条指令）。同一条 or-chain 在 @512/@524/**@536(链式比较)**，
共享真出口 @568、假出口 @612（下一 elif）。镜像 @982/@994/@1006 → @1038/@1080。

实测差异（R64 弹出点插入的只读打印，产物哈希 `a387e7e0f43443c3` 与未打补丁相同＝惰性合格）：

```
CC 536  regions=[]  b2r=('TryExceptRegion', 48)  chain=[(512,'or'),(524,'or')]
CC 1006 regions=[]  b2r=('TryExceptRegion', 48)  chain=[(982,'or'),(994,'or')]
```

⇒ 该 walk 发生时 **`self.regions` 里还没有任何链式比较区域**（区域表里 @536/@1006 的 cc IfRegion 只在
analyze 结束后出现），所以 #1/#2/#3/#4 的形状 A 修法对 strategy 不起作用：形状 B 需要
①「链式比较区域在布尔算子识别之前就已登记」，或②纯结构的链式比较识别（不依赖区域表）。
strategy 的 walk 也是 `skip_claimed_check=True`（循环体路径），断在 R64 `:30044-30096`。

## 5. 臂 × 判决（全部 0 翻正，按「fires without flips」一律不落地）

| 臂 | r01 | strategy 单元 | 备注 |
|---|---|---|---|
| 无（基线） | 1/2 红 | 26/27，`net=+0 hunks=4 real=0`（4 处纯目标差 `@522/@534 ->@568` 应为 `->@820`） | |
| `guard` | 1/2 红 | 26/27 | 惰性（阻塞在 #1） |
| `c12` | 1/2 红 | — | walk 仍 2 成员：#3 钳制未开 |
| `c12+guard` | 1/2 红 | — | walk 2 成员（#3） |
| `c12+guard+clamp(+hop)` | 1/2 红 | 26/27，`len 288/286 net=+2 hunks=39 real=2 reloc=37` | **条件文本已正确**：`if dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00':`；strategy 同文本正确 |
| `all`（exempt+clamp+hop，走 R64 结构豁免，不开 #1） | 1/2 红 | 26/27 | 见 §6 的所有权污染 |

`exempt`＝在 R64 的 `chain.pop()` 前加同样的 `_r14_cc_operand_reaches` 豁免（strategy 形状 B 的那一处）；
它也让 strategy 的条件文本变正确，但同样不翻正。

## 6. 剩下的真障碍＝唯一归属被破坏（下一步施工点，本票未解）

`c12+guard+clamp+hop` 下 r01 的区域表（实测）：

```
BoolOpRegion e=0  chain=[(0,'or'),(14,'or'),(26,'or')]  merge=62  blocks=[0,14,26]
IfRegion     e=26 merge=58 cc=True  blocks=[26,42,54,58,62]      ← @26 同时属于两处
IfRegion     e=0  merge=58 cc=True  blocks=[0,42,52]             ← 父 if 区域被打脏：cc 标志泄漏、体块丢失
产物：if A or B or '11:30:00' < dt_strf < '12:30:00':
          return 1          ← elif dt_strf == 'x' / else 分支整段消失
```

即：把链式比较入口 @26 放进 `BoolOpRegion.blocks` 后，Phase 3 的条件区域装配既把 `chained_compare_ops`
认到父区域头上，又把 @62（下一 elif 入口）留在 cc 区域的 blocks 里 ⇒ elif 臂被吞。
`nocb`/`rb2` 两种「把 cc 入口移出 blocks」的尝试都已实测：加在 `:28577` （`region_blocks = chain_blocks | {merge}`）之后 **无效**，因为条件上下文分支在 `:28666` 重新 `region_blocks = chain_blocks` 覆盖了它；改加在 `:28666` 之后，blocks 确实变干净（`BoolOpRegion e=0 merge=62 blocks=[0,14]`），但父区域依旧被打脏 （`IfRegion e=0 merge=58 cc=True blocks=[0,42,52]`），产物进一步退化成只剩 `if '11:30:00' < dt_strf < '12:30:00': return 1`（A/B 两臂与 elif 全丢），判决仍 1/2 红。⇒ 真正的所有权污染发生在 **Phase 3 条件区域装配**：父 IfRegion 从被引用的 cc 区域继承了 `chained_compare_ops` 并把 cc 内部块 [42,52] 收进 blocks，同时丢掉 @62 起的 elif 臂。下一票的施工点是 `_identify_conditional_regions` 里「条件块落在链式比较区域」的那条继承支路，不是 blocks 组装

## 7. 方法记录（本票实测，写给后续票）

1. **只读打印探针并非一律惰性**：同一套 marker 补丁在 strategy 上产物哈希不变（INERT），
   在 r01 上产物改变（PERTURBING）——该管线存在依赖对象身份/集合迭代顺序的判定点。
   ⇒ 每个探针都要在 **当次目标** 上以「CLI 产物字节对比」自证惰性，不能一次合格全程复用。
2. `sys.settrace` 行追踪对本管线既 **不产生读数**（目标函数 0 行读数）又 **改变产物**（12771→13261 B），
   该手段作废。
3. 进程内 harness（`build_cfg(code)+RegionASTGenerator(...).generate()`）产物与 CLI 产物相差 ~350 B
   （12771 vs 13121），**只能用于读区域表/条件文本形状，判决必须用 CLI 产物**。
4. 判据永远喂 CLI 产物（§1 的空判据教训）。

## 8. 交给下一票的清单

- 形状 A（链式比较区域已在 `self.regions`）：`c12+guard+clamp+hop` 四处的豁免文本已在
  本目录 `r14_arms_reference.py`（`HELPER/OLD_C12/NEW_C12/OLD_GUARD/NEW_GUARD/OLD_CLAMP/NEW_CLAMP/OLD_MERGE/NEW_HOPM`），
  blocks 侧已实测两处（:28577 与 :28666，见 6 节，都不足以翻正——父区域被打脏发生在 Phase 3）；下一施工点是 _identify_conditional_regions 中把链式比较标志继承给父 IfRegion 的那条支路；电池 rounds/round14/repro/ 的 9 例作前置门。
- 形状 B（strategy 一族）：先解决「布尔算子识别时链式比较区域尚未登记」，
  即 `_identify_chained_compare_regions`（`:17994`，Phase 2）与 try/except 嵌套的相互作用；
  在那之前 `exempt`（R64 结构豁免）只是把错误从「取反」搬到「父区域被打脏」，不可落地。
- 本票未翻正任何单元，core/ 保持 `640d33a77dcb71c2 / 851b0723732a2402`，残余仍
  **12 文件 / 34 单元**（门 label 16 出表）。
