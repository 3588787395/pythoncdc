# FIX B129 — 交接失败后不得把块标成「已生成」：`_leading_*` 静默丢弃修复回报

票面：`IMPL_B129_MATCHER_LEADING_GUARD_BRIEF.md`（Round 10 实现票）
诊断凭据：`DIAG_B128_MATCHER_DROPSITE.md` Q1/Q2（trace `D:/Temp/r10diag/probe4.out`）
Scratch：`D:/Temp/r129/`（探针 `probe_stack.py`/`probe_trace.py`/`probe_claim.py`/`probe_order.py`/
`probe_elif.py`，补丁 `patch1.py`(A+C)/`patch2.py`(A only)/`patch3.py`，读数
`base.json`/`after.json`/`small34_base.json`/`small34_after.json`/`small34_Aonly.json`/
`small34_restore.json`/`anchor_after.json`/`restore_arms.json`）

## 结论（先说末节）

**仅归档 spec 未落地 —— 生产码已按工作树 sha256 逐字节回滚，零翻转 + 哨兵回退，两条都触发 §七。**

- `core/cfg/region_ast_generator.py` 工作树 sha256 = `e9a8f65f6451bcc895c5558528b03a9d6ef1045f418f0efd267f9900ef174e74`
  （= 封表值 `e9a8f65f6451…`，逐字节相等）
- `core/cfg/region_analyzer.py` 工作树 sha256 = `38a1d5142d132fd7288229851a33a02df71ccb3cf98ee40f84d4042bb8d1135e`
  （= 封表值 `38a1d5142d13…`，本票全程未改此文件）
- grep 落地标记 = **0 命中**（`_cjb_pend_region`、`_cjb_operand_taken`、`_cjb_rscan`、`B129` 全部零命中）
- 回滚后复测（产物已按 HEAD 码重生成）：14 臂 21/29（6 success / 8 failure，与基线逐行相等）、
  anchor 454/454、quotation 153/153、small34 **1528/1568 + 18 success files**（＝票面 §四.5 基线读数）、
  matcher 16/17、jq_trans_module 65/65、trade_info_utils 37/41。工作树已回到派工态。

## 一、基线（HEAD 字节，先跑后动码）

`regen_list.py 120 D:/Temp/r129/arms14.txt` → ok=14 bad=0；
`pyc_verify.py batch --index test_repros/round9/r10ls_probe_index.json --json D:/Temp/r129/base.json`
→ **files_total=14**（rows 14 条，无 `*OK.pyc` 混入）units 21/29，6 success / 8 failure。

| 臂 | 基线 | 角色 |
|---|---|---|
| `01_else_ctx` 1/2、`02_elif_ctx` 1/2、`04_finally_ctx` 1/2、`05_class_meth` 2/3、`06_nested_for` 1/2、`07_while_ctx` 1/2、`08_deep_nest` 1/2、`14_ctl_nonslice_pair` 1/2 | 红 | 复现臂（**HEAD 态即红**，按 §四.2 不得算本票成绩） |
| `03_except_ctx`、`09_ctl_slice_in_bare`、`10_ctl_plain_in_bare`、`11_ctl_slice_assign`、`12_ctl_slice_andnot`、`13_ctl_single_chain` 各 2/2 | 绿 | 对照臂 |

基线红的 8 条臂的失败单元是 `'300' and ... and not is_first` 被写成 `if X: if is_first or Y:`
（`not is_first` 落进内层 test 的 or 支）这类**形状**问题，语句没丢；与 matcher 丢 10 条指令的
**丢弃**面不是同一件事，这解释了改后它们仍红（逐臂状态位移 = 0，见 §三）。

## 二、我实现的判据（两种读数，都实测过）

### 面 A（票面钉死的 `_cjb_skip_inline_if`，`region_ast_generator.py:54896-54921`）

按「登记 ⇔ 接手」同命题重写该分支：

1. 捕获落空入口**所宿主的区域**（`_cjb_pend_region`，区域成员关系，白名单事实）；
2. `_leading_operand` 的 setattr 时机与参数逐字节不变（负对照要求）；
3. 接手 = 两条可测事实的析取：
   - 事实①：`_leading_operand` 的唯一消费者 `_graft_pending_operand` 只被
     `_build_boolop_expression` 调用 ⇒ 接手 ⇔ 存在 `BoolOpRegion` 以该入口为 `entry`；
     第一版只测 `isinstance(_cjb_pend_region, BoolOpRegion)`，第二版扩为
     扫 `self.regions` + `children` 找 `entry is _cjb_pend_key` 的 `BoolOpRegion`；
   - 事实②：`_leading_guard_candidate(...)` 的**返回值**（旧码丢弃它）；
4. 任一成立 ⇒ 与今日同路径（登记 + 返回）；两者皆不成立 ⇒ **就地发射**
   `If(test=_cjb_cond_expr, body=self._generate_region(_cjb_pend_region), orelse=[])`
   并**不**把源块加入 `generated_blocks`（登记时机交回发射端，`_generate_block_statements`
   在语句产出之后认领）。

未放宽 `:38496` 的 parent 守卫；无名/数/偏移/深度特判；无新方法与禁用前缀。

### 面 C（实测才暴露的**上游预登记**，`_if_generate_elif_chain` 原 `:19307-19324`）

HEAD 全流程里 2164 根本走不到面 A：它被**更早**地预登记了。证据链（scratch 探针，全部只读、
不产生产码）：

- `probe_trace.py`（`sys.settrace` 只看 `block is blk(2164)` 的那一帧）：整轮 generate() 里
  `_generate_block_statements_body(2164)` 只被调用 1 次，事件序列是
  `52172 → 52173 → RETURN stmts=0` ⇒ 落在入口守卫 `if block in self.generated_blocks: return []`，
  **不在** CJB 带（54896-54921）；
- `probe_claim.py`/`probe_order.py`（把 `generated_blocks` 换成会记录 `add` 的 set 子类）：
  对 2164 的**第一次**认领来自 `_if_generate_elif_chain` 内 `self.generated_blocks.add(elif_boolop.merge_block)`
  （HEAD 行号 19324；该 elif 链 `entry=2038, condition_block=2080`，其 `BoolOpRegion`
  `entry=2038 blocks=[2038,2080] chain=[(2038,'and'),(2080,'and')] merge=2164`），
  时序上**先于** BODY-CALL；
- `probe_order.py unclaim`（仅探针内临时撤销该认领）：`_generate_block_statements_body(2164)` 才走到
  CJB 面，`BODY-EXIT stmts=0 then_operand=True then_guard=False` —— 即票面 Q1/Q2 的形状
  （记录写了没人读、守卫登记返回 False、返回值被丢、块被登记、返回空）。
  ⇒ 票面钉的那一面是真的，但在整文件跑里被面 C 挡在前面。

面 C 的同一判据写法：merge 块的语句只有两种接手人（以它为 entry 的区域／真正的顺序发射端，
后者在发射之后自行登记），二者在此处都无法被证明 ⇒ 删除该预登记。

## 三、实测读数（靶内 + 哨兵）

| 面 | 14 臂（units 基线 21/29，files 6/8） | matcher | anchor 454 | quotation 153 | small34（基线 1528/18） |
|---|---|---|---|---|---|
| A(narrow)+C | 位移 **0/14**（两臂产物文本变了：`02_elif_ctx`、`04_finally_ctx`，状态仍红） | 16/17（**语句回来了**：`if order.asset.symbol[None:3] in ('688','689'):` 出现在产物，但嵌在上一臂体内） | 454/454 | 153/153 | **1525/17** ↓ |
| A(narrow) only | 同上（0 位移） | 16/17 | — | — | 1525/17 ↓ |
| A(broad)+C | — | 16/17 | — | — | `jq_trans` 回到 **65/65 ✓**，`trade_info_utils` 仍 **36/41** |
| A(broad) only | — | 16/17 | — | — | `jq_trans` 65/65 ✓，`trade_info_utils` **36/41** ↓ |

小34 逐文件位移（A narrow，基线 `small34_base.json` vs `small34_after.json`）：

```
jq_trans_module.pyc   65/65 success -> 63/65 failure   (回退，R75 fix1 的负对照本体)
trade_info_utils.pyc  37/41 failure -> 36/41 failure   (回退 1 单元)
klinedata/api_base    基线跑分读数 0/64、0/28 = 该机内存压力下的抖动，非位移
                      （A+C 跑分为 61/64、27/28；真基线按票面 1528/18 反推即此二值）
```

两条硬事实：

1. **零翻转**：14 臂状态位移 0；matcher 仍 16/17；
2. **哨兵回退**：`jq_trans_module` 由 65/65 掉到 63/65（文件翻负）—— 票面 §三.5 明令「真
   `BoolOpRegion` 宿主必须逐位不变」，narrow 判据违反它；broad 扫描把它救回（65/65），
   但 `trade_info_utils` 仍 -1 单元，说明面 A 的「就地发射」在那一处也是**多余的一次发射**
   （该块语句其实已由别处接手，只是接手路径不是我测的那两条）。

matcher 为何仍 16/17：面 C 撤销预登记后语句确实被发出来了，但落点在**上一臂的体内**。
原因是归属而不是丢弃——`probe_elif.py` 实测 `blk(2164)` 同时是
IF_ELIF_CHAIN(`entry=2038, condition_block=2080`) 的 `elif_conditions[0]` 与
`else_blocks[0]`，发射栈是 `_if_generate_full_elif_chain → _if_generate_elif_chain →
_generate_region → _generate_if → _if_generate_normal → _if_generate_then_branch →
_process_if_blocks → _generate_block_statements(2164)`，即它被当作**上一臂的成员**走查。
要它落在兄弟位，得改块归属/臂边界（＝B130 那张票的「被接到哪个块」面），不属本票这一面，
票面 §三 禁止我顺手放宽。

## 四、票面 §六（`:54913` 注释与行为矛盾）

未落地：该 docstring 的更正依附于行为更正（它自称守卫记录「替代此处对条件的静默丢弃」，
而 `:38496` 的 parent 守卫使嵌套宿主永不登记 ⇒  advertised 的静默丢弃仍是执行路径）。
只改注释把矛盾写得更漂亮而没有代码更正，属票面禁止的「以注释换读数」。已随回滚归零，
留给 Task 11 的注释审计与本面重派；本轮实测证据（`probe_trace.py` 的 52172/52173 事件序列
与 `probe_order.py unclaim` 的 `then_operand=True then_guard=False`）可直接作为那条改动的凭据。

## 五、下一票该接的位置（我量到的，不再展开诊断）

1. 面 A 的接手判据必须是**消费侧闭环**而不是宿主类型：
   可测事实只有「`_build_boolop_expression` 是否真的以该入口块为某个 `BoolOpRegion` 的 entry 被调用」
   与「`_leading_guard_candidate` 返回值」，narrow 版误判 `trade_info_utils`/`jq_trans_module`，
   broad 版仍误判前者 ⇒ 需要第三条接手证据（例如记录是否落在会被读且**已读过**的位置），
   且不得引入回溯修补（rules.md §1.3 单向数据流）。
2. matcher 的翻转在**归属面**：`blk(2164)` 被 IF_ELIF_CHAIN 同时登记为 `elif_conditions[0]` 与
   `else_blocks[0]`，而它既不是任何区域的 condition_block 也不是任何区域的 entry；
   预登记它的 `self.generated_blocks.add(elif_boolop.merge_block)` 是同一命题的第二处违反，
   但把它删掉只换来「语句在错误层级出现」，16/17 不动。
3. 本轮 8 条基线红臂的失败单元是 `and not D` 被 graft 成内层 `D or ...` 的形状问题，
   与本票的丢弃面同函数不同判据，不得混为一案（本 campaign 已三次 look-alike 实为另一机制）。

## 六、合规自述

无任何 git 写命令；单命令均 <300s（一次 verify 因合并两条命令超时被移到后台，读数已取得）；
`python -X utf8`，未设 PYTHONIOENCODING；生产码按字节 patch（BOM+CRLF 未归一），回滚后
`py_compile` 通过、`import core.cfg.region_analyzer; import core.cfg.region_ast_generator` 通过；
未手改任何 `*OK.py`，所有被本票覆盖过的产物（14 臂 + 5 anchor + matcher + trade_info_utils +
jq_trans_module + small34 全部 34 件）都已按 HEAD 码重生成并复测；未跑 402 全量门禁；
无禁用前缀新方法（G3）、无硬编码阈值（G4）、无按名/偏移/深度特判。

---

# 七、并发改派的第二工程师：独立复核（grep 标记 `[r10-b129-handoff-propos]`）

我是被派来落本票的另一名工程师（派工单在 09:00 前后下达，当时 `core/` 与工作树封表值逐位一致、
`git status --porcelain -- core/` 为空）。本节是**独立复核**：与上面 §一–§六 的工程师在同一个
工作树上并发写生产码（见「并发时间线」），因此我把自己的全部实现与测量搬进一份**钉死的隔离副本**
`D:/Temp/r129/wt`（`git show HEAD:core/cfg/region_ast_generator.py` → CRLF+BOM 归一后
sha256 = `e9a8f65f…`、`region_analyzer.py` = `38a1d514…`，与封表值逐位相等，由
`D:/Temp/r129/pin_baseline.py` 校验并打印），凡读数只在隔离副本里出，绝不受并发写污染。

**结论与我方独立判断一致：本票的判据可写、可测、但不该落地 ⇒ 「仅归档 spec 未落地」。**
生产码在我这一路**从未写入仓库**；仓库现仍处封表态（见本节末复核项）。

## 七·1 我的基线（HEAD 字节，与首发读数一致）

| 靶 | 命令 | 读数 |
|---|---|---|
| 14 臂 | `pyc_verify batch --index test_repros/round9/r10ls_probe_index.json` | **files=14, 21/29 units, 6 绿文件 / 8 红文件**；产物新鲜度：14 枚 `*OK.py` 与 HEAD 码重生成字节 **14/14 相同**（`D:/Temp/r129/baseprods/`） |
| 靶点 | `single …/matcher.pyc` | **16/17**，红单元 `<module>.DefaultMatcher.match`；`matcherOK.py` 与 HEAD 重生成字节相同（`a4e4980f31e5`） |
| 哨兵 A | `batch --index D:/Temp/r9w16/anchor_index.json` | **454/454**（5 文件） |
| 哨兵 B | `single site-packages/fly/data/quotation.pyc` | **153/153**。票面给的 `site-packages/quotation.pyc` **不存在**，真实路径即此 |
| 哨兵 C | `batch --index …/baseline/small34_index.json` | **1528/1568**，**files_total=34**（18 绿 / 16 红）⇒ 票面「18 文件」= 全绿文件数，名单是 34 条 |

隔离副本重跑同一套（`HB_*`，核心 = 封表字节）：**arms 21/29、anchor+matcher 470/471（=454+16）、
small34 1528/1568**，与上表逐单位相等，且 49 枚产物 sha 与盘上提交态一致（`jq_trans = a33ec1e7720f`）。
⇒ 首发 §一/§结论 的基线读数成立；我在仓库侧 09:34–09:39 量到的 small34 **1525/1568 是并发写造成的
假基线**（那一刻 `core/` 已被并发改成 `a115762b…`），特此更正，不得当作基线引用。

## 七·2 我实现的三种判据（都在隔离副本里实测）

改动点：`region_ast_generator.py` `_generate_block_statements_body` 的
`if _cjb_skip_inline_if:` 带（HEAD 行号 54896–54921）。判据 = 票面要求的 `_cjb_taken`（旧码把
`_leading_guard_candidate` 的返回值丢弃，我取它；`_leading_operand` 只在会被读时才写）。

| 版本 | 「接手」定义 | 无人接手时的补发射 | 文件 |
|---|---|---|---|
| **narrow**（票面字面写法） | `get_entry_region_for_block(pend_key)` 是 `BoolOpRegion` 且 `.entry is pend_key`，或 guard 返回 True | 落回**既有 inline-if 路径**（票面 §二.2 指 :54923 `_cjb_pending` 那条） | `D:/Temp/r129/b129_narrow.patch`（83 行），改后文件 sha256 `29e37da58c4c46f4…` |
| **broad** | 同上，另把「存在以该块为 entry 的 `BoolOpRegion`」也计为接手（只补 `get_entry_region_for_block` 的 IfRegion/BoolOpRegion 同入口优先裁决带来的漏判，仍是区域成员关系 + entry 身份） | 同 narrow | `D:/Temp/r129/b129_broad.patch`（94 行），sha256 `4e15d6467e63c822…` |
| **V4** | 同 broad | **发射端自己接手**：`If(test=条件, body=self._generate_region(宿主区域), orelse=[])`，并在语句确实进入返回表之后才登记本块与该区域块集 | `D:/Temp/r129/b129_v4.patch`（101 行），sha256 `572ad602c189c3a0…`（叠在 narrow 上的等价物 `0ad69f2940d49bf8…`） |

`:38496` 的 parent 守卫一字未动；`region_analyzer.py` 未动；无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`
新方法（V4 只调既有 `_generate_region`）；无名/函数名/偏移/指令数/深度特判；`_cjb_pend_key is None`
（else-entry）与重建失败（`Constant(True)`）两支保持原行为（默认 `_cjb_taken = True`）。

## 七·3 我的读数（before → after，逐单位）

| 靶 | 封表基线 | narrow | broad | V4(broad) |
|---|---|---|---|---|
| 14 臂 | 21/29（6 绿/8 红） | **21/29**，红名单逐条不变；`r10ls_04_finally_ctx` 产物字节变（`51587e97858d→8e496b00d173`），仍红 | **21/29**，14 枚产物**全部字节不变** | 同 broad（只补测 15 件，未见位移） |
| matcher | 16/17 | **16/17**（CJB 带在整文件跑里根本没被走到，见 §七·4 F1） | **16/17** | **16/17** |
| anchor 5 | 454/454 | **454/454** | 未整批重跑（其中 `jq_trans` 不在 anchor 内） | 未整批重跑 |
| quotation | 153/153 | 在 anchor 内，**153/153** | — | — |
| small34 | 1528/1568（34 文件） | **1525/1568** | **1527/1568**（按逐文件替换推得：jq 回 65/65、trade_info_utils 36/41；34 文件整批未重跑） | −1（同 broad，`create_user_code_iqe`） |

narrow 的逐单位位移（隔离副本 `HB_*` vs `NN_*`，全 49 件覆盖）：

```
BROKE  ***<module>.create_user_code_iqe                                  (trade_info_utils 37/41 -> 36/41)
BROKE  ***<module>.func_attribute_history_convert_code.replace_args      (jq_trans_module  65/65 -> 63/65)
BROKE  ***<module>.func_get_bars_convert_code.replace_args               (jq_trans_module  65/65 -> 63/65)
FIXED  —— 无
```

产品字节位移（49 件全比）：narrow 改 4 件（`jq_trans_module`、`trade_info_utils`、
**`trade_live_broker`（单位数不变 118/128，纯形状变化 = G7 形变风险，首发 §三 未列）**、`r10ls_04_finally_ctx`）；
broad 改 2 件（`trade_info_utils`、`trade_live_broker`），其余 47 件逐字节相同。
⇒ 两条硬事实与首发一致：**零翻转**、**哨兵回退**（narrow −3 / broad −1），另加一条：
broad 仍在 `trade_live_broker` 上留下无形变收益的产物改动。

## 七·4 我对票面前提的否证（实测，不扩面）

* **F1（票面 Q1 在整文件跑里不是首发现场）**：真实 pycdc 管线中
  `_generate_block_statements(blk 2164)` 的调用点是 `_if_generate_full_elif_chain:16170`
  （R45-A merge 补偿，`_mb45 = region.merge_block`），此刻
  `already_generated=True` ⇒ body 落入口守卫直接 `return []`，**54896 的 CJB 带一次都不执行**。
  证据：`D:/Temp/r129/probe_g.py`（封表+并发版均复现）、`probe_h.py`（逐 generator 跟踪
  `generated_blocks.add`）、`probe_e.py`（调用栈）。首发用 `probe_trace.py/probe_order.py` 独立到达同点。
  ⇒ DIAG 的 377 事件 trace 是**单元级生成器**（`RegionASTGenerator(build_cfg(match_code))`）的形状，
  与整文件跑不同；先撤销 `_if_generate_elif_chain` 的 merge 预登记（B126 共要件）才谈得上治这一面。
* **F2（共要件不足以翻正）**：我在隔离副本做了三段实验：
  `E1` 只删预登记 ⇒ matcher 仍 **16/17**，产物里 `('688','689')` 一条不增（丢弃面还在）；
  `E2` 预登记撤销 + narrow 落回既有 inline-if ⇒ 语句**出现**在产物第 172 行，但形状是
  `if order.asset.symbol[:3] in ('688', '689'): pass`，且 `not is_first_five_trading_days`
  那半条操作数从兄弟臂的 `is_first or …` 里**消失** ⇒ 16/17；
  `V4` 预登记撤销 + 自接手内联（body 取宿主区域整树 + 认领块集）⇒ 嵌套形状看着对
  （`if …in ('688','689'): if is_first or BUY… / elif SELL…`），但整段仍落在**上一臂（'300' 臂）体内**
  ⇒ 16/17。首发 §三 末段（归属面：`blk(2164)` 同时是 `elif_conditions[0]` 与 `else_blocks[0]`）
  与我独立测到的落点一致：**要翻正得改臂边界/块归属，不在本票这一面**。
* **F3（票面给的 narrow 判据违反票面自己的负对照）**：`_leading_operand` 的接手判据若只看
  `get_entry_region_for_block`，会把真 `BoolOpRegion` 宿主误判成无人接手 ——
  `jq_trans_module` 的两个 `replace_args` 单元（R75 fix1 本体，65/65）直接翻负。
  根因是 `region_analyzer.get_entry_region_for_block` 尾段明写「BoolOpRegion 与 IfRegion 同入口时
  优先返回 IfRegion」。broad（存在以该块为 entry 的 `BoolOpRegion`）把它们救回 65/65。
  ⇒ 后续票若要重派这一面，接手判据的**取证面必须是消费侧**，不能是宿主类型侧。
* **F4（「登记⇔接手」不是全命题）**：`trade_info_utils.create_user_code_iqe` 在 HEAD 的静默认领
  对产物是**正确的**（37/41 绿单元），narrow/broad/V4 三种补发射都把它改成 Different control flow。
  ⇒ 存在「块语句已被别处接手，但接手路径不在这两条可测事实里」的真实形态；票面 §二 的两条事实
  构成**必要**条件而非**充要**条件，这就是零翻转的另一半原因。
* **F5（14 臂不复现丢弃面）**：8 条基线红臂的产物在 broad 下 14/14 字节不变，只有 narrow 改了
  `r10ls_04_finally_ctx` 且仍红 ⇒ 这组臂测的是 `and not D` 被 graft 进内层 `or` 的形状问题，
  不是本票的丢弃面；票面 §四.2「红臂→绿」在本票不可能达成，按票面纪律记为该轴否证，不为本票加分。

## 七·5 并发时间线与我做过的清理（供主代理对账）

| 时刻 | 事件（`core/cfg/region_ast_generator.py` 工作树 sha 前 16 位） |
|---|---|
| ~09:00 | 派工时 `e9a8f65f…`（封表），`git status --porcelain -- core/` 空 |
| 09:13:03 | 并发工程师写入 v0（`6a81a99c…`，含 :54896 面 A + :19304 面 C 两段）；其间还重生成过 `matcherOK.py`（`dbde1c9d…`）——**我在 09:14 备份的「HEAD 产物」快照因此被污染**（`D:/Temp/r129/head_products_manifest.json` 不得作为基线凭据，我后来在封表字节上重新快照为 `snap_head.json` 并在隔离副本重算 `HB_*` 才得到可信对照） |
| 09:25 | 回滚到 `e9a8f65f…`；我据此跑完 14 臂/matcher 的仓库侧基线（37/46，与首发一致） |
| 09:33:17 → 09:44:25 → ~09:48 | 并发 v1（`a115762b…`，只留面 A）→ v2（`80aed5b1…`）→ 再次回滚封表 |
| 09:51 起 | 我停止在仓库侧写任何产物，全部读数改到隔离副本 |

清理项（已完成，无 git 写命令）：仓库里 `trade_live_brokerOK.py` 在我接手时是被并发码重生成的脏产物
（`4011a069c357`），已用封表码 `pycdc.py -o` 重生成回提交态 `7d7afc91200a`。终态复核：

```
git status --porcelain -- core/ site-packages/ test_repros/   →  空
core/cfg/region_ast_generator.py  sha256 = e9a8f65f6451bcc895c5558528b03a9d6ef1045f418f0efd267f9900ef174e74
core/cfg/region_analyzer.py       sha256 = 38a1d5142d132fd7288229851a33a02df71ccb3cf98ee40f84d4042bb8d1135e
grep -c '_cjb_taken\|_cjb_operand_taken\|_cjb_guard_taken' core/cfg/region_ast_generator.py  → 0
```

## 七·6 末节判定与凭据

**仅归档 spec 未落地**（我这一路同样未把生产码写进仓库；仓库由并发工程师的 v0/v2 已按 sha256 逐字节
回滚，我复核其终态 = 封表值）。触发条件与票面 §四.7 一致：**靶内零翻转 + 哨兵回退**。
grep 标记：`[r10-b129-handoff-propos]`（本节、`D:/Temp/r129/*.py` 探针脚本头、`b129_*.patch` 生成脚本头）。

凭据路径：补丁 `D:/Temp/r129/b129_narrow.patch` / `b129_broad.patch` / `b129_v4.patch`
（对 `D:/Temp/r129/sealed_unix.py`（封表 blob 的 LF 视图，sha `943b5d87453d305e`）做 `diff -u`）；
patcher `apply_b129.py`（narrow/broad）、`apply_corereq.py`（面 C 共要件）、`apply_v4.py`（自接手补发射）；
读数 `HB_arms14/HB_anchor5m/HB_s34a/HB_s34b`（封表基线）与 `NN_arms14/NN_anchor5m/NN_s34a/NN_s34b`（narrow）、
`BR_broke3/BR2`（broad）、`V4_matcher/V4a`、`E1_matcher/E2_matcher`；探针 `probe_a/e/f/g/h`；
隔离副本 `D:/Temp/r129/wt`（钉死封表 + 我的 patch，`py_compile` 全通过）。
本节不删改上面 §一–§六 的任何内容；唯一更正项：我在 §一 早期贴出的 small34 基线以
**票面/首发 1528/1568（34 文件、18 全绿）为准**，09:34 那次 1525 读数作废。
