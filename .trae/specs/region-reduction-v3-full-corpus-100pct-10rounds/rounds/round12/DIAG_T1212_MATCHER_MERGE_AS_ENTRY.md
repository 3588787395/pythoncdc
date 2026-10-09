# DIAG T12-12 — matcher.DefaultMatcher.match：两处 if 测试**没有被识别为区域**（Round 12）

范围：诊断，不改 `core/`，不跑 402 门。镜像 `D:/Temp/r142/`。
仓库字节（实测）：generator `971df5e2c9cd7d0a`（= HEAD，T12-09 已逐字节撤回），
analyzer `e926a54f17753b33`（封存，含 B133）。
消费的前置结论：`rounds/round11/DIAG_B138_MATCHER_LAST_MILE.md`（三处折叠 + 17/17 oracle 文本）。

## 1. 复现（当前字节，本轮自己的读数）

- `python -X utf8 pycdc.py site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc -o D:/Temp/r142/m_now.py`
  ⇒ rc=0，产物 13255 字节
- `python -X utf8 scripts/pyc_verify.py single …matcher.pyc --source D:/Temp/r142/m_now.py`
  ⇒ `status=failure units=16/17 (94.12%)` —— 与 B138 同读数（B138 时 generator 为 `e9a8f65f6451bcc8`，
  其间只落过注释改动 ⇒ B138 的 oracle 结论仍适用）

## 2. 普查仪器与一次假零（自曝）

仪器 `D:/Temp/r141/p1_census.py`（只跑分析/生成一次，不落文件到仓库；输出 `D:/Temp/r142/census_match.txt`）。
它的 UNIT 过滤原本是 **substring**，于是 `match` 先命中 `set_matching_type@66`、再命中
`is_current_match@169` —— 两次读数都是**另一个 code object** 的（本役第 N 次踩同名/首匹配）。
已给仪器加 `!name` 精确 co_name 模式，正对照 = `dumped=True` 且表头
`===== UNIT match@176 co_lines count=819 blocks=78 regions=45 =====`。
（`co_qualname` 在这些重建 code object 上不存在，label 实为 `co_name@co_firstlineno`。）

## 3. 普查事实（全部是**区域字段/角色**，不是偏移推断）

被吞的那条语句头 = 块 @2164（10 指令）：

```
@2164 LOAD_FAST order|LOAD_ATTR asset|LOAD_ATTR symbol|LOAD_CONST None|LOAD_CONST 3|
      BUILD_SLICE 2|BINARY_SUBSCR|LOAD_CONST ('688','689')|CONTAINS_OP 0|
      POP_JUMP_FORWARD_IF_FALSE 2464          lines=[241…]  succs=[2208, 2464]
  preds: 1834(IF_FALSE) 1884(IF_FALSE) 1896(IF_FALSE) 1908(IF_TRUE) 2038(IF_FALSE) 2080(IF_FALSE)
  roles: LoopRegion@6:body_blocks
         IfRegion@2038:else_blocks  IfRegion@816:else_blocks  IfRegion@800:then_blocks
         IfRegion@732:else_blocks   IfRegion@664:else_blocks  IfRegion@546:then_blocks …
```

关键：**普查里没有任何区域的 `entry=2164`**，而 @2164 自己是一条完正的 if 测试
（CONTAINS_OP + 条件跳转，两条出边 2208/2464）。它被 **四个区域当 merge_block** 认领：

```
IfRegion entry=1834 cond=1896 merge=2164 parent=6
IfRegion entry=1884 cond=1896 merge=2164 parent=6
IfRegion entry=1908 cond=1908 merge=2164 parent=6
IfRegion entry=1912 cond=1954 merge=2164 parent=6
BoolOpRegion entry=2038 merge=2164 parent=2038
```

⇒ **机制定名**：@2164 既是前一串条件的汇合落点、又是下一条语句的测试入口；识别端只承认前者，
于是这条语句**没有 owning 区域**，发射端也就无从发它 —— 这正是 B138 §Task1 看到的
「体（IfRegion@2208 确实存在，cond=2208 merge=3210）被发出来了，但它的**头测试**不在」。

## 4. 这**不是**结构上不可能——同一单元里就有反例

@1444 同样是「既是别人的 merge、又是自己的区域入口」，识别端两个都给了：

```
IfRegion entry=1324 cond=1372 merge=1444 parent=6      （BoolOpRegion entry=1324 merge=1486 也在）
IfRegion entry=1444 cond=1486 merge=1696 parent=6      ← merge 块同时是区域入口，正常发射
```

@1324 甚至有两个同入口区域（BoolOp + If）。所以「merge 块不得再是入口」并非本仓的既有约束，
@2164 缺入口是**识别判定漏掉了它**，不是设计不允许它。

## 5. 与 B138 三处折叠的关系（把症状归位）

| B138 的折叠 | 本轮普查给出的位置 |
|---|---|
| F3 被吞语句头 @2164 | **就是 §3：无 owning 区域**（新事实，B138 只看到 del 10 条） |
| F2 守卫折叠 `… and not is_first_five` → `is_first_five or …`（@1910、@2210） | 条件链被拆成 1834/1884/1908/1912 四个**共用 cond=1896/1954 的小区域**（§3 第二张表）⇒ 折叠发生在链的分段归属，不是单一布尔表达式渲染 |
| F1 or 链折叠 `(A∧B)∨(A∧C)` → `if not (A∧B): if (A∧C):`（@1382） | @1324 有 BoolRegion+IfRegion 双抽象，@1384/@1432/@1612 各成区域；链的分段同样在识别端成形 |

⇒ 三处折叠**同属一个宿主**：`_identify_conditional_regions` 对「一条语句内多个条件跳转块」的
分段与入口判定。@1836 也没有入口区域（同族），@2164 是其中唯一造成整条语句丢失的那块。

## 7. 判决性实测（三轮惰性探针，全部 CLI-vs-CLI 逐字节自证）

**§3/§4 的「识别判定漏掉了它」这句被本轮后续实测否证，就地订正：识别端没错，是识别之后的
elif 归并把它吞了。** 读数顺序如下（每台仪器都先证惰性再用）：

| 探针 | 惰性自证 | 读数 |
|---|---|---|
| t1213（`_should_skip_block_for_if_region` 的 32 个 `return True` 全部改记 clause 号） | 产物 13255 = 13255 **逐字节相同** | `ENTER block@2164` / `ENTER block@1444`，**没有任何 SKIP clause 命中** ⇒ 跳过判据不放也不拒 @2164，它不在拒因里 |
| t1214（analyze 检查点，8 空格语句插进 12 空格块） | **PERTURBING 13255→11031** | 读数作废；教训：行级插入必须用**锚行自己的缩进**，否则静默反缩进改控制流 |
| t1216b（同法但缩进对齐锚行） | 13255 = 13255 | identify 返回 **36** 个区域，到 `:1774` 只剩 **32**；`:1759` 那个 ternary 过滤对 match **根本没执行**（其探针未打印）⇒ 删除发生在 1572–1758 之间 |
| t1217（`:1677` 之前打印链与待吞区域） | 13255 = 13255 | 见下 |

```
[R1217] chain entry= 2038  elif_conditions= [2164]  elif_bodies= 1  final_else= None  nblocks= 11
[R1217] cond_blocks= [1570, 2038, 2164, 2338, 2846]  about_to_subsume= [2846, 2338, 2164, 1570]
```

⇒ **机制定名（不再是推断）**：`IF_ELIF_CHAIN@2038` 把 @2164 收成了自己的 **elif 条件块**，
于是 `region_analyzer.py:1672-1691` 那段「移除 entry 落在 IF_ELIF_CHAIN.elif_conditions 中的内部
IfRegion」按设计执行，把识别端**已经正确建好的** `IfRegion@2164（cond=2164 merge=2464 8 块）`
整条删掉 —— 语句 `if order.asset.symbol[:3] in ('688','689')…` 的头测试就是这么丢的。
§3 里「没有任何区域 entry=2164」的读数仍然成立，但它是**删除之后**的最终区域表（p1_census 读
`self.regions`），不是识别结果；当时的因果解释写反了，登记此订正。

### 7bis. @2164 为什么不是那条 elif 的候选（边事实，可作判据）

@2164 的前驱是 **六个**：`1834/1884/1896/1908(IF_TRUE)/2038/2080`，其中 1834/1884/1896/1908
都在链 @2038 的 11 块之外。真正的 elif 条件块只会被本臂的假边进入。⇒ 候选判据（待实测，
含反例控制）：**若某 elif 条件候选存在来自本链 `blocks` 之外的前驱，则它不是 elif 条件，
而是下一条语句的测试块**。四个控制样本（1570/2038/2338/2846）必须逐条验这条判据不把真 elif 也否掉；
只要有一条否掉，判据即错，不得派单。

### 7ter. 施工层的选择（规则约束，不是口味）

删除点 `:1684-1691` 是**回溯修正**的位置；`_check_elif_chain` 的臂收集才是**识别即正确**（原则 4）
的位置。按 rules.md §1.2/§1.5，修在收集侧；收集侧改不动才允许证明删除侧的判据本身不完备。

### 7quart. 仪器学结论（跨票适用）

- **同构建 A/B 才算自证**：t1211 当时判「PERTURBING」用的对照是 CLI 产物 vs 进程内 harness 产物，
  两者本身差约 90–100 字节；t1213/t1216b/t1217 一律 CLI-vs-CLI，三台都证惰性。
  进程内 `d.decompile(buf, use_region=True)` 与 CLI 不是同一产物口径，不得用作惰性对照。
- **方法包装**（t1211 的 `_generate_region`、t1215 的 `analyze`/`_identify_conditional_regions`）
  会改变产物 —— t1215 读数（identify 返回 36 含 IfRegion@2164；final 45 里 @2164 消失；@1444 出现两次）
  与惰性的 t1216b（36→32）**方向一致**，故采信「identify 创建了它」这一事实，但 t1215 的绝对计数
  不作为判决读数，只作旁证。


## 8. 下一票（T12-18）判据与必测控制

> 本节取代原 §6 草案。草案的前提（「识别端没建 @2164 的区域」）已被 §7 的实测否证，
> 故整段重写而非续写；草案原文留在 git 历史。

**判据（边事实 + 区域成员，不含偏移/计数/名字门）**：
`IF_ELIF_CHAIN` 收集臂条件时，候选块 E 只有当 **E 的全部前驱块都在本链的 `blocks` 内**
才是本链的 elif 条件；否则 E 是**下一条语句的测试块**，不得收进 `elif_conditions`。
@2164 的六个前驱（1834/1884/1896/1908/2038/2080）里至少 1834/1884/1896/1908 在链 @2038
的 11 块之外 ⇒ 应被拒为 elif；若 @2164 不再进 `elif_conditions`，`:1677` 的吞并没有输入，
`IfRegion@2164` 自然存活 —— 修在识别侧，不是事后复原（原则 4）。

## 9. T12-18 实测＝惰性的**原因**（两台账量，都 CLI-vs-CLI 自证惰性）

判据按 §8 施在**删除侧** `:1677`（候选脚本 `D:/Temp/r142/t1218_candidate.py`，只在镜像里跑）：

```
BASE m_t18 16/17   CAND m_t18 16/17  SAME_as_BASE
BASE q_t18 153/153 CAND q_t18 153/153 SAME_as_BASE
BASE h_t18 29/30   CAND h_t18 29/30   SAME_as_BASE
BASE w_t18 55/58   CAND w_t18 55/58   SAME_as_BASE
BASE e_t18 12/13   CAND e_t18 12/13   SAME_as_BASE
```

五个文件的产物**逐字节相同**（不只是读数相同）。原因是 §8 的判据本身成立，但它改的不是决定物：
`D:/Temp/r142/t1219_predprobe.py`（行为不变的纯观察探针，惰性 13255=13255）打印出

```
entry= 2164  preds_is_none= False  n_preds= 6  pred_offs= [1834,1884,1896,1908,2038,2080]
             chain= 2038  chain_blocks= [2038,2080,2160, 2164 ,2208,2212,2254,2334,2338,2380,2460]
entry= 1570  n_preds= 2   pred_offs= [1444,1486]
             chain= 1444  chain_blocks= [1444,1486,1566,1570,1692]
```

两条结论：

1. **不是「表没填」的假象**：`predecessors` 在该点已填好（n_preds=6），判据输入完整；
   1834/1884/1896/1908 确实不在链 @2038 的 blocks 里 ⇒ 判据按预期**拒绝把 @2164 当吞并对象**，
   `IfRegion@2164` 因此在 `conditional_regions` 里活了下来。
2. **但活下来不等于会被发射**：链 @2038 的 `blocks` **本身就含 2164**（见上面的粗体），
   `block_to_region[2164]` 仍归那条链，发射端按链的成员表渲染臂，语句依旧没有自己的节点。
   ⇒ 只动 `:1677` 的吞并判据是**必要不充分**，本票族在此终止；决定物在
   `_check_elif_chain` 的**收集/成员**侧（`:21440` 起，`first_else` 在 `:21852` 被收为
   `conditions`，递归在 `:22406`），要让 @2164 从一开始就不进链的 `blocks`。
   收集侧的局部困难已实测记录：`:21852` 处拿不到祖先链的块集（签名只带
   `header_/else_blocks_/merge_`），所以该处的判据需要**先扩签名传成员集**——
   那是链机构造的本体改动，blast radius 覆盖全仓 elif 形，必须先有可判别的反例控制再动。

**§8 的判据不作废**（它是 t1219 里唯一把 @2164 与四个真 elif 分开的实测事实），
作废的是「施在删除侧就能翻正」这个假设。

   （t1217 读数里同表并列的真 elif 候选）。任一被否 ⇒ 判据错，撤回不落地。
2. 正例验收：matcher `16/17 → 17/17`，与 `rounds/round11/DIAG_B138_MATCHER_LAST_MILE.md`
   的 `m_or_full.py` 字节正确文本逐字对照。
3. 连带不得动：quotation `153/153`、handlers `29/30`、wizard_quant_api `55/58` 产物逐字节相同；
   `realtime_event_source`（同区族另一靶）读数不得变差。
4. 仪器纪律：新探针一律 CLI-vs-CLI 自证惰性后才可引用读数（见 §7quart）。
5. 轴纪律：本轴首次受试；若零翻正，按「fires without flips」逐字节回滚并登记，
   不在同一判据上磨第三次。

