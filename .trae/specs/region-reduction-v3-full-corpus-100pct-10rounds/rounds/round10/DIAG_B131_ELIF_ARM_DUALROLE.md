# Round 10 诊断票 B131 简报：`matcher.DefaultMatcher.match` 的 elif 臂 —— 块 2164 在同一区域内身兼两角

**范围：只诊断，禁改 `core/`，禁 git 写，不跑全量门禁。** Scratch：`D:/Temp/r131/`。
探针可复用（只读，HEAD 字节有效）：`D:/Temp/r129/probe_elif.py`、`D:/Temp/r129/probe_h.py`（后者插桩全部
`RegionASTGenerator` 实例与 `generated_blocks` 写入栈）。

## 一、B129 被否证的部分（必须先读，否则会重跑同一死路）

B129 把丢弃点钉在 `region_ast_generator.py:54896-54921`（`_cjb_skip_inline_if` 把条件递给无人读的
`_leading_operand` / 被丢弃返回值的 `_leading_guard_candidate`）。两名工程师各以三个变体实现过该判据，
**共同读数**：`matcher.pyc` 16/17 → 16/17（零翻转）、small34 1528 → 1525/1527（`jq_trans_module`
65/65→63/65、`trade_info_utils` 37/41→36/41 破坏），故按 §四.7 逐字节回滚，`core/` 现为封表值
`e9a8f65f6451bcc8` / `38a1d5142d132fd7`。实测否证三条：

1. 整条流水线里 `blk 2164` 的 `_generate_block_statements` **根本没走到 `:54896`**：它在 `:52172-52173`
   就因 `block in self.generated_blocks` 直接返回；第一次认领者是
   `_if_generate_elif_chain` 的 `self.generated_blocks.add(elif_boolop.merge_block)`（`:19307-19324`）。
   `DIAG_B128` 那条 377 事件 trace 是**单元级**生成器，不是模块级的实际认领路径 —— 这是本票的教训：
   认领者要用「插桩所有 generator 实例 + 打印写入栈」定位，不能只看一个单元的调用栈。
2. 把该认领去掉后语句**确实回来了**（产物出现 `if order.asset.symbol[:3] in ('688','689'):`），
   但它落在**前一个 `'300'` 臂体内**（臂边界错），仍 16/17 ⇒ 只治认领不够，还须治臂归属。
3. `trade_info_utils.create_user_code_iqe` 在 HEAD 是**正确**的，而它的形状同样走「静默认领」；
   任何「登记 ⇔ 被接手」的全称式实现都会把它改红 ⇒ 本票不得以全称判据为解，须以身份判据为解。

## 二、主代理 2026-10-08 02:21 在 HEAD 字节实测的区域事实（勿重推，可直接引用）

`build_cfg(match.co)` → 78 块；块 `@2164` 的归属（`probe_elif.py` 原样输出）：

```
BoolOpRegion with merge==tb: entry=2038 blocks=[2038, 2080]
        chain=[(2038,'and'), (2080,'and')] parent=IfRegion
IfRegion cond=2080 entry=2038 type=IF_ELIF_CHAIN parent=IfRegion   (blocks 共 11)
   elif_conditions=[2164]
   elif_bodies=[[2208, 2212, 2254, 2338, 2334, 2380, 2460]]
   elif_final_else=[]  then=[2160]  else=[2164, 2208, 2212, 2254, 2334, 2338, 2380, 2460]  merge=2464
   TB membership: condition_block=False  in elif_conditions=True  in elif_bodies=False
                  in elif_final_else=False  in then_blocks=False  in else_blocks=True
```

⇒ **同一个 `@2164` 同时是**：① 该 IF_ELIF_CHAIN 的 `elif_conditions[0]`（须发射成 `elif <test>:`），
② 同区域 `else_blocks` 的成员（须发射成 else 臂内容），③ 前置 BoolOp（`2038 and 2080`）的
`merge_block`（被 `:19324` 认领为「已生成」）。三种身份互斥，违反 `rules.md` §1.2 原则 2（每块唯一归属）。
另注：`:19318-19323` 的既有豁免只检查「`merge_block` 是否为 `self.regions` 中某区域的 `entry`」，
而 `@2164` 不是任何区域的 entry（实测）—— 所以该豁免**结构上不可能**命中本例；它的 docstring 自称
「不限于顶级区域」，而循环只遍历 `self.regions`，此注释/行为矛盾另记 Task 11。

## 三、要回答的四个问题（边做边写进本文件）

1. **渲染路径**：`match` 单元里这条链由 `_if_generate_elif_chain` 还是 `_if_generate_full_elif_chain`
   发射？给出实际命中的 `文件:函数:行` 与该函数读的是哪些列表（`elif_conditions`/`elif_bodies`/
   `else_blocks`/`elif_final_else`）。为何 `elif_conditions[0]` 的 test 没出现在产物里 —— 是被
   `generated_blocks` 挡住，还是被 `else_blocks` 路径当普通语句吞掉？
2. **臂边界**：为什么去掉认领后该臂体落进**前一个臂**内部？发射端按什么身份决定「臂体到此结束」
   （`merge_block`？下一个 `elif_conditions` 的入口？`JUMP_FORWARD` 落点？）给行号。
3. **`else_blocks` 的双重身份从哪来**：`region_analyzer` 里构造 IF_ELIF_CHAIN 的
   `elif_conditions`/`else_blocks` 的赋值处（`region_analyzer.py:22580` 一带、`:4115` 一带）分别用什么
   判据；`else_blocks` 是否本应只含「链后 else 臂」而错误地把 elif 条件块一并塞入（Python 的
   `elif` 在 AST 里就是 `orelse` 里的嵌套 `If`，故 **条件块本身属于 orelse 的第一个节点**）——
   若是，正确判据应表达为「`elif_conditions` 成员在 `else_blocks` 中以臂入口身份出现，不得再以
   普通语句块发射」，须给出这是分析端职责还是发射端职责的**依据**（不得凭「哪边改起来小」决定）。
4. **最小复现** ≤4 条并说明哪些复现：
   `if A and B: x() elif C: y()`（C 为单块条件，本例形状）、
   `if A and B: x() elif C: y() else: z()`、
   `for` 内上述链、对照 `if A: x() elif C: y()`（BoolOp 缺席 ⇒ 应已正确）。
   用本机 CPython 3.11.7 `py_compile` 生成 pyc，`python -X utf8 pycdc.py -o` 到 scratch 后
   `python -X utf8 scripts/pyc_verify.py single <pyc>` 读数；**不得**覆盖 `site-packages/` 下任何产物。

## 四、约束

单命令 ≤300s；`python -X utf8`，禁 `PYTHONIOENCODING`；读源码 `encoding='utf-8-sig'`；
禁任何 git 写；禁改 `core/`；禁「成员非 condition」这类无判别力计数（吞并证据须是
**身份 ∧ 产物 AST 有无对应语句**的合取，见 `DIAG_B128` Q0-Q1）；禁为让两文件好看而强行并案。
产出四样：宿主 `文件:函数:行`、误发条件的白名单表述（opcode／块末／后继／区域身份）、
是否静默豁免（若是即 `rules.md §1.5 C3` 违例，须同票封闭）、复现臂名单与逐臂读数。

## 五、B131 诊断答复（DIAG 工程师，2026-10-08，HEAD 字节 `e9a8f65f6451bcc8`/`38a1d5142d132fd7` 实测）

探针（只读，产物已断言与 `python -X utf8 pycdc.py matcher.pyc` 的 HEAD 产物逐字节相等）：
`D:/Temp/r131/probe_q1v4.py`（+ `--suppress-claim`）、`D:/Temp/r131/probe_regions_real.py`、
`D:/Temp/r131/isolate.py`、日志 `D:/Temp/r131/q1v4_log.txt`、`q1v4b_log.txt`、`q1v4_supp.txt`。
复现/产物 `D:/Temp/r131/q1v4_src.txt`、`q1v4_src_supp.txt`、`m_HEAD.py`。

### 三.0 先否证简报（与我自己的）前提 —— 区域身份搞错了

`probe_elif.py` 是在**新建** `RegionASTGenerator(cfg)` 后手调 `ra.analyze()`，量到的是
「R2 = IfRegion entry=2038 cond=2080 type=IF_ELIF_CHAIN elif_conditions=[2164]
else_blocks∋2164 merge=2464」。在**真实流水线**里这块区域确实存在于 `ra.regions`，
但**从未被派发**：`match` 单元里 `_generate_if` 只把 5 个 IF_ELIF_CHAIN 交给
`_if_generate_full_elif_chain`，entry 分别是 `0 / 1444 / 1912 / 2212 / 2484`（实测，
2038 不在其中）。真实渲染的是**它的父链** R1：

```
IfRegion entry=1912 cond=1954 type=IF_ELIF_CHAIN blocks=[1912, 1954, 2034, 2038, 2160]
   elif_conditions=[2038]  elif_bodies=[[2160]]  elif_final_else=[]
   then_blocks=[2034]  else_blocks=[2038, 2160]  merge_block=2164
```

⇒ **块 2164 在真正被渲染的那个区域内既不在 `blocks`、也不在 `elif_conditions`、
也不在 `else_blocks`——它是 R1 的 `merge_block`**（实测 `2164: in_blocks=False
in_elif_conditions=False in_else_blocks=False`）。所以简报第二节的「同一区域内三身份互斥」
不成立于发射路径：双重 `elif_conditions/else_blocks` 归属属于**从未渲染**的 R2。
`@2164` 的真实双重身份跨两个区域：它是 **R1 的 merge_block**，同时是 **R2 的
elif_conditions[0]**（且是 BoolOpRegion(entry=2038, blocks=[2038,2080]) 的 merge_block）。
两条 IF_ELIF_CHAIN 的块集本身相交（R1∩R2 = {2038, 2160}），违反 §1.2 原则 2 的位置在
**分析端的链切分**，不在简报说的 `else_blocks` 塞入。

### 三.1 答：渲染路径与丢弃原因（实测，非读码）

命中路径（`file:function:line`，全部实测于 `q1v4b_log.txt`）：

1. `core/cfg/region_ast_generator.py:_generate_region:4070` →
   `_generate_if:14331`（`region.region_type.name == 'IF_ELIF_CHAIN'`）→
   **`_if_generate_full_elif_chain:15176`**（不是 `_if_generate_elif_chain` 直接接手的分支；
   后者由前者在 **`:15757`** 委托调用）。宿主单元 `gen#17[match]`。
2. `_if_generate_full_elif_chain` 读的列表：`condition_block`(1954) + BoolOp entry(1912)
   组成外层 test、`then_blocks`=[2034]、`elif_conditions`/`elif_bodies`（经 `:15757` 委托）、
   最后 `merge_block`=[2164] 在 **`:16140-16177`** 作「链后尾随语句」处理。
3. `_if_generate_elif_chain` 读的列表：`elif_conditions`=[2038]、`elif_bodies`=[[2160]]、
   `elif_final_else`=[]、`inline_boolop_chains`。它对 `elif_conditions[0]=2038` 查到
   BoolOpRegion(blocks=[2038,2080], merge_block=2164)，于是
   **`:19305-19306`** 认领 `elif_boolop.blocks`（合法：块确属该 BoolOp 区域），
   **`:19324`** 认领 `elif_boolop.merge_block`＝2164（**该块不在 BoolOp 区域的 blocks 内**）。
   实测 `GB.ADD | _if_generate_elif_chain:19324 <- _if_generate_full_elif_chain:15757 <-
   _generate_if:14331 <- _generate_region:4070 <- _process_if_blocks:25188`。
4. R2 的 `else_blocks` 路径**根本没参与**（R2 未被派发），故「被 `else_blocks` 当普通语句吞掉」
   否证；「渲染了但挂错父节点」也否证（`<<_if_generate_elif_chain RET_JSON` 显示 R1 的 elif 臂
   正常返回 `If(_is_elif=True, test=SELL and deal_price<=limit_down, body=[Continue])`，
   与 2164 无关）。

**丢弃点（实测两处，且相互独立）**：`_if_generate_full_elif_chain:**16170**`
`self._generate_block_statements(_mb45)`（`_mb45 = region.merge_block` = 2164）返回 `[]`。

- 通道①：`_generate_block_statements:52172-52173` 因 `block in self.generated_blocks` 早退
  （实测 `>>gbs 2164_in_GB=True` → `<<gbs ret(0)=[]`）。
- 通道②：**把①的认领抑制后仍然丢**。实测 `--suppress-claim` 下 `>>gbs 2164_in_GB=False`，
  但 `<<gbs n=0 ret=[]`，且 `GB.ADD | _generate_block_statements_body:54920 <-
  _generate_block_statements:51913 <- _if_generate_full_elif_chain:16170` —— 即块走到
  **`:54896-54921` `_cjb_skip_inline_if`** 分支，把已重建的条件 `_cjb_cond_expr` 交给无人读的
  `_leading_operand` 属性 + 丢弃返回值的 `_leading_guard_candidate`，然后 `:54920`
  登记块、`:54921` 返回不含该语句的 `stmts`。

⇒ **否证 B129 前提 1**：「整条流水线里 blk 2164 的 `_generate_block_statements` 根本没走到
`:54896`」。真相是它**走不到是因为 `:19324` 先认领**；一旦抑制 `:19324`，`:54896-54921` 命中并
以同一结果丢弃该块。⇒ **否证 B129 前提 2**：「把该认领去掉后语句确实回来了」在 HEAD 字节**不成立**
——`q1v4_src_supp.txt` 与 `q1v4_src.txt` **逐字节相等**（`equal: True`），仅去掉 `:19324` 认领
产物零变化。这也解释了三名工程师「零翻转」：他们只治了通道①，通道②把同一块再吞一次。

**静默豁免判定**：是。两处认领都**无日志、无计数器、无回退**——`:19324` 的唯一守卫
`:19318-19323` 只遍历 `self.regions` 查 `_tr.entry is merge_block`（实测 2164 不是任何区域
entry ⇒ 结构上不可能命中本例）；`:54896-54921` 直接 `return stmts`。语句凭空消失且流水线
不记录，属 **`rules.md` §1.5 C3（守卫封闭）违例**：登记（`generated_blocks.add`）与接手
（谁负责发射该块）之间没有显式守卫把「merge_block 不是 BoolOp 自有块」「块的条件由兄弟区域
承载」这两种情形排除或认领。本票同案封闭该判据。

### 三.2 答：臂边界身份 —— 三套身份互不一致，实测误发条件

发射端决定「本臂体到此结束」用了**三个不同身份**，且彼此不重合：

| 身份 | 位置 | 读法 |
|---|---|---|
| ① 分析器给的臂块集 `region.elif_bodies[0]` | `region_ast_generator.py:_if_generate_elif_chain:19469`（`self._process_if_blocks(region.elif_bodies[0], region, branch='elif')`）、`:19481`、`:19495-19497`、`:19501`、`:19529`、`:19537`（`_eb_last_block = region.elif_bodies[0][-1]`）、`:19736`、`:19765` | 臂范围 = 成员列表，末端 = 列表末块 |
| ② 链出口 `region.merge_block` | `_if_generate_full_elif_chain:16140-16177`（`_mb45 = region.merge_block` → 尾随语句）、`_if_generate_elif_chain:19556` | 臂后一切语句挂在**链**的结果之后 |
| ③ 块尾条件跳转的后继/落空后继 | `_generate_block_statements_body:54773-54791`（`len(block.conditional_successors) >= 2`；`_cjb_jump_target = _cond_jump_bs.argval`；跳转落点＝else 入口、另一侧＝then 入口）、`:54870-54872`（极性由 then 入口是否等于跳转落点决定） | 逐块内联 if |

实测（`probe_q2b.py` 双通道抑制，产物 `q2_src_s19_s54.txt`，与 HEAD 产物**不同**）：
块 2164 的 `If` 节点确实生成 —— `GB.ADD@_generate_block_statements_body:55001`、
`GBS(2164)->1`、随后 `GB.ADD@_if_generate_full_elif_chain:16172`（即 `:16171` 的
`if _tail45:` 分支）。它落在产物第 **169** 行：

```
164  if order.asset.symbol[:3] == '300' and trading_date >= gem_change_date and ...:
165      if is_first_five or BUY and deal_price >= get_limit_up(...): continue
167      elif SELL and deal_price <= get_limit_down(...): continue
169      if order.asset.symbol[:3] in ('688', '689'):   ← 恢复的语句，落在上一臂体内
170          pass
171  if BUY and deal_price >= get_limit_up(...): continue     ← 真正的兄弟语句
```

原因是身份②与身份①的**层级错配**：`region.merge_block`（2164）的尾随语句被
`result = result + _tail45`（`:16175`）接到**本链结果之后**，而本链 R(1912) 自身是作为
子区域在父区域的臂内被发射的（实测调用栈
`_if_generate_full_elif_chain:16170 <- _generate_if:14331 <- _generate_region:4070 <-
_process_if_blocks:25188 <- _if_generate_then_branch:18173`）⇒ 尾随语句继承**臂的缩进层级**，
而不是 2164 的真实归属层级（`block_to_region[2164] = LoopRegion@6`，实测）。
（170 行的 `pass` 是本探针把 2208 的区域归属一并抹平所造的伪影，不计入结论。）

**误发条件的白名单表述**（只用 opcode / 块末 / 后继与前驱身份 / 区域角色与成员关系；无计数、无深度、无绝对偏移、无名字）：

设 B = 本链最后一个臂的条件 BoolOp 区域的 `merge_block`（即该 BoolOp 短路链尾块的条件跳转落点）。
则以下全部成立时本形状误发：

- `B ∉ BoolOpRegion.blocks`（B 不是该 BoolOp 的自有块，只是它的**汇合目标**）；
- B 的块末指令是**前向条件跳转**（`POP_JUMP_FORWARD_IF_*`），且 `|B.conditional_successors| = 2`
  ⇒ B 是一条**语句级 `if` 的头块**，不是纯汇合/连接块；
- `get_entry_region_for_block(B) is None`（B 不是任何区域的入口），且 B 同时是**多个区域**的
  `merge_block`（实测 5 个：`BoolOpRegion@2038`、`IfRegion@1912/1908/1884/1834`）；
- B 的**落空后继**（then 侧）是某区域的入口（实测 2208 是 `IfRegion@2208` 的 entry），
  而 B 的跳转落点侧区域亦存在；
- B 的 `block_roles` 为 `LOOP_BODY`（实测：`BlockRole.IF_ELIF_CONDITION` 在整个 `match` 中
  **一次都没被赋值**，见三.3），即 B 的「臂入口」身份在角色表里不存在。

⇒ 三条发射路径同时拒绝 B：`:19324` 把它登记成「已生成」；`:16158-16163` 的兄弟区域补发要求
`_own46.entry is B`（B 非任何区域入口 ⇒ 假）；`:54886-54894` 的内联 if 要求两个后继都不是区域入口
（then 后继是区域入口 ⇒ 跳过）。三者一致地把 B 判给「别人」，而角色表里没有那个人。

### 三.3 答：双重身份的出处（分析端），以及为什么修在分析端

构造处（`core/cfg/region_analyzer.py`）：

- `:22576-22584` 一次性装配 `IfRegion(region_type=IF_ELIF_CHAIN, ..., else_blocks=else_blocks,
  merge_block=merge, elif_conditions=elif_info["conditions"], elif_bodies=elif_info["bodies"],
  elif_final_else=elif_info.get("final_else"))`；`all_blocks`（`:22560-22566`）把
  `else_blocks` **和** `elif_info["conditions"]` 一起并入 `blocks`。
- `elif_info` 来自闭包函数 `_check_elif_chain(header_, else_blocks_, merge_)`（定义
  `:21207`）。其 elif 条件候选的身份是 **`first_else = else_blocks_[0]`**（`:21379`，
  最终 `conditions = [first_else]` 于 `:21619`），门槛是
  `len(first_else.conditional_successors) == 2`（`:21329`）与尾跳转 opcode ∈
  `FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS`（`:21331`）、
  `_header_last.argval == _fe_last.argval`（`:21369-21375`，同汇流点 ⇒ 同一链），
  以及 `:21350-21351` 的 R27-A 双合取（头块不自带语句 ∧ 尾部自成汇流）。
- ⇒ **`elif_conditions[0] ⊆ else_blocks` 是分析器的设计事实**，不是误塞：`region_analyzer.py:4102-4123`
  的 `_annotate_if_structural_roles` 先按 `else_blocks` 标 `BlockRole.IF_ELSE`（`:4111-4114`），
  再按 `elif_conditions` 标 `IF_ELIF_CONDITION`（`:4115-4118`），而 `_assign_region_role`
  （`:4150-4152`）是 **first-writer-wins**。简报担心的「塞入」正是 Python AST 的正确事实
  （elif 就是 `orelse` 里嵌套的 `If`，其条件块确实是 orelse 的第一个节点）。

**这条双重身份在本例不是病根**（实测）：真正被渲染的 R(1912) 里 2164 既不在 `blocks`、
也不在 `elif_conditions`、也不在 `else_blocks`；简报量的那个 R(2038)（2164 三位于一体）
**从未被派发**。病根是下面两条分析端事实：

1. **区域重叠**：`R(1912).blocks ∩ R(2038).blocks = {2038, 2160}`（实测）。同一条物理 if/elif
   序列被切成两条彼此嵌套却又各自宣称臂块的 IF_ELIF_CHAIN（R(2038) 是 R(1912) 的 elif 臂
   再递归 `_check_elif_chain` 产生的第二个视图），违反 **§1.2 原则 2「每块唯一归属」**。
   R(2038) 后来被 BoolOp 认领/被跳过，成为**不可达的幽灵区域**，而它宣称拥有的 2164 于是
   变成「有人登记、无人发射」。
2. **臂入口身份从未落地**：`match` 的 `block_roles` 计数实测为
   `LOOP_BODY×59 / CONTINUE×16 / NORMAL×1 / LOOP_HEADER×1 / LOOP_ELSE×1`，
   `IF_ELIF_CONDITION` 命中数 **0**；5 条链（entry 1444/1912/2038/2212/2484）的
   `elif_conditions` 块角色全是 `LOOP_BODY`。因为循环标注 `:4086` 先把所有循环体块 stamp 成
   `LOOP_BODY`，`:4108/:4112/:4116` 的 `== NORMAL` 前置条件在循环内永远为假 ⇒
   **分析器为「臂入口 vs 普通语句块」准备的区分在循环嵌套里是死代码**。

**判端依据（按算法原则，不按改动大小）**：
原则 2 要求「每一层唯一归属」，而本例的失败是**归属在识别阶段就没写进唯一权威载体**
（`block_roles` 里臂入口身份缺失；两个 IF_ELIF_CHAIN 块集相交）；原则 4 要求「父引用子入口」，
即 2164 作为「链后兄弟语句」的入口身份应当由**它的 owner** 引用——但它的 owner 只有
`LoopRegion@6`，链区域把自己的 `merge_block` 当作汇合点而非子入口来消费；
「识别即正确、不做事后修复」禁止用 `generated_blocks.add(...)`（`:19324`/`:54920`）这种
**事后登记**去替代缺失的归属声明。
⇒ **正确修复属于分析端**：在 `_check_elif_chain`/`_annotate_if_structural_roles`
（`region_analyzer.py:4115-4118` 与 `:4150-4152`）把「块是某链 `elif_conditions` 的成员
⇒ 其角色为臂入口」作为**优先于 `LOOP_BODY`/`IF_ELSE`** 的赋值（first-writer-wins 改为
按身份优先级覆盖），并禁止两条 IF_ELIF_CHAIN 的 `blocks` 相交（重叠时降级内层为普通
IF_THEN_ELSE，与 `region_ast_generator.py:15247-15259` 的降级判据同族）。
发射端 `:19324` 的 merge 认领是**该缺失身份的代偿**；只在发射端打补丁会重演 B129 的零翻转
（实测：单通道抑制产物逐字节不变）。

### 三.4 答：最小复现清单与逐臂读数（本机 CPython 3.11.7 实编译实测）

尺子：`python -X utf8 pycdc.py X.pyc -o X_out.py` →
`python -X utf8 scripts/pyc_verify.py single X.pyc --source X_out.py`。
全部产物写在 `D:/Temp/r131/repro/`，**未触碰 `site-packages/` 任何 `*OK.py`**。

| # | 源码形状 | verify 读数 |
|---|---|---|
| r1 | `if A and B: x() elif C: y()` | `status=success units=2/2 success_rate=100.00%` |
| r2 | `if A and B: x() elif C: y() else: z()` | `status=success units=2/2 success_rate=100.00%` |
| r3 | r2 整链放进 `for i in items:` | `status=success units=2/2 success_rate=100.00%` |
| r4 | 对照 `if A: x() elif C: y()`（无 BoolOp） | `status=success units=2/2 success_rate=100.00%` |
| r5 | 补测：matcher 形状仿写（`not in ('300','688','689')` 外层 + 内层 and 链 + 兄弟 `in ('688','689')`） | `2/2 100%` |
| r6 | 补测：`for` 内 `if a and b: … continue / elif d and e: … continue /` 后接兄弟 `if h:` | `2/2 100%` |
| r7 | 补测：r6 外套 `if not (a and b):` | `2/2 100%` |

⇒ **简报的 4 条例证一条都不复现**（连「控制组应已正确」的 r4 也一样正确 —— r4 与 r1/r2/r3
读数相同，无法区分）。我另加的 3 条形状仿写也不复现。

**不复现的判别性证据（即缺的那味药）**：本缺陷要求那个汇合块 B 同时满足
「是 **≥2 个**区域的 `merge_block`」（实测 5 个）**且**「是另一条**幽灵** IF_ELIF_CHAIN 的
`elif_conditions[0]`」**且**「不是任何区域的 entry」**且**「在循环内，故 `block_roles[B]=LOOP_BODY`」。
`units=2/2` 的小样例每条只有一层链、一个汇合点、一条臂以 `x()` 落空（非 `continue`）终结，
分析器不会切出第二条重叠链，因此 `:54886-54894` 与 `:16158-16163` 不会同时拒绝同一块。
⇒ 本票的可复现标本只有 `site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc`
一个（`match` 单元 16/17）；**不得**用最小样例当落地门禁，须用 matcher 单文件 +
`trade_info_utils`/`jq_trans_module` 两个哨兵（B129 实测它们会被全称判据打红）。

### 五.补充结论（交付四样）

1. **宿主**：`core/cfg/region_ast_generator.py:_if_generate_elif_chain:19324`（登记 `elif_boolop.merge_block`）
   ＋ `core/cfg/region_ast_generator.py:_generate_block_statements_body:54896-54921`（`:54920` 第二次吞块）
   ＋ `core/cfg/region_ast_generator.py:_if_generate_full_elif_chain:16158-16170`（唯一应有的接手者，因
   `_own46.entry is B` 前置为假而放弃）。归属与角色的**出处**在
   `core/cfg/region_analyzer.py:_check_elif_chain:21379/21619`、`:22560-22584`、
   `:_annotate_if_structural_roles:4111-4118`、`:_assign_region_role:4150-4152`。
2. **误发条件白名单表述**：见三.2 的合取式（opcode 前向条件跳转 / 块末 / 后继与前驱身份 /
   `get_entry_region_for_block(B) is None` / B ∈ 多区域 `merge_block` / B ∉ BoolOp.blocks /
   角色为 LOOP_BODY 而非臂入口）。
3. **静默豁免**：**是**。两处登记均无日志、无计数器、无回退，且互不知情；
   `:19324` 的守卫 `:19318-19323` 只问「是否任何区域的 entry」，对本例结构上不可能命中。
   ⇒ **`rules.md` §1.5 C3（守卫封闭）违例**，本票同案封闭。
4. **复现臂名单与逐臂读数**：见三.4 表（7 条全部 2/2 100%，无一复现；标本仅 matcher.pyc 的 `match` 单元 16/17）。

**单点建议（一句话）**：把归属声明补回识别阶段 ——
`core/cfg/region_analyzer.py:_annotate_if_structural_roles:4115-4118` 与
`:_assign_region_role:4150-4152`：`elif_conditions` 成员的身份赋权须**优先于** `LOOP_BODY`/`IF_ELSE`
（先写者让位于身份更高者），使「臂入口 / 链后兄弟语句」成为可被发射端直接读到的唯一事实，
并禁止两条 IF_ELIF_CHAIN 的 `blocks` 相交；发射端 `:19324` 的事后 merge 认领随之成为可删除的代偿。
（落地须以 matcher.pyc 单文件 + 两哨兵为门禁，最小样例无判别力。）

## 六、对简报（含主代理自己）前提的否证清单 + 一处自我更正

1. **否证（简报二）**「`@2164` 同时是 IF_ELIF_CHAIN 的 `elif_conditions[0]`、该区域 `else_blocks` 成员、
   且该区域 BoolOp(2038 and 2080) 的 `merge_block` ⇒ 同一区域内三身份互斥」。
   实测：三条归属**分属两个区域**。`2164 ∈ R(2038).elif_conditions ∧ R(2038).else_blocks ∧
   R(2038).blocks` 全部为真，**但 R(2038) 在真实流水线里从未被 `_generate_if` 派发**
   （`match` 单元只有 5 次 IF_ELIF_CHAIN 派发：entry `0 / 1444 / 1912 / 2212 / 2484`）。
   真实渲染者 R(1912) 中 2164 **不在** `blocks`/`elif_conditions`/`else_blocks` 任何一条里，
   只是它的 `merge_block`。`probe_elif.py` 的读数没错，但**它量的区域不是发射的那个区域**
   （它手调 `ra.analyze()`，与流水线里由 `generate()` 递归驱动的嵌套 generator 同一份
   `regions` 却走不同派发）——这正是 B129 教训「认领者要用插桩所有 generator 实例定位」的复发。
2. **否证（简报二/三 与 B129 前提 1）**「丢弃发生在 R(2038) 的 `elif_conditions[0]` 渲染上」。
   实测丢弃点是 `region_ast_generator.py:_if_generate_full_elif_chain:16170`
   （`self._generate_block_statements(region.merge_block)` 返回 `[]`），属「链尾汇合块的兄弟
   语句补发」，与 R(2038) 的 elif 渲染无关。
3. **否证（B129 前提 1）**「整条流水线里 blk 2164 的 `_generate_block_statements` 根本没走到 `:54896`」。
   实测：它走到 `:54896` 并被 `:54920` 吞掉——只要先移除 `:19324` 的认领
   （`GB.ADD@_generate_block_statements_body:54920`，`>>gbs 2164_in_GB=False` → `n=0`）。
   它是**第二道**独立吞并，不是「走不到」。
4. **否证（B129 前提 2）**「把该认领去掉后语句确实回来了，落在前一个 `'300'` 臂体内」。
   实测：在 HEAD 字节下**只**抑制 `:19324` 时产物与 HEAD 产物**逐字节相等**（0 行变化，
   语句并没有回来）；必须**同时**取消 `:54886-54894` 的内联 if 跳过，语句才回到产物第 169 行。
   ⇒ 这解释了三名工程师的三个变体为何全部零翻转：他们各治一条通道，另一条通道把同一块再吞一次。
5. **否证（简报四.4）**「`if A and B: x() elif C: y()` 一类最小样例能复现本形状」。
   实测 r1–r4（外加形状仿写 r5/r6/r7）**全部 `units=2/2 100%`**，无一复现（见三.4 表）。
6. **新测得的重叠事实（简报未列）**：`R(1912).blocks ∩ R(2038).blocks = {2038, 2160}`
   —— 两条 IF_ELIF_CHAIN 块的**相交**才是原则 2 的破口；且 `2164` 同时是 **5 个区域**的
   `merge_block`（`BoolOpRegion@2038`、`IfRegion@1912/1908/1884/1834`）。
7. **新测得的死判据（简报未列）**：`BlockRole.IF_ELIF_CONDITION` 在 `match` 中命中数 **0**
   （角色 census：`LOOP_BODY×59 / CONTINUE×16 / NORMAL×1 / LOOP_HEADER×1 / LOOP_ELSE×1`；
   连 `IF_CONDITION/IF_THEN/IF_ELSE` 也是 0）。原因：`region_analyzer.py:4086` 先把循环体块
   stamp 成 `LOOP_BODY`，而 `:4108/:4112/:4116` 与 `:4150-4152` 的赋值要求当前角色 `== NORMAL`
   ⇒ 循环内的 If 区域角色标注整体失效。
8. **否证（简报二末句 与 `region_ast_generator.py:19311-19317` 注释之争）**「既有豁免的循环只遍历
   顶级 `self.regions`，与其 docstring『不限于顶级区域』矛盾」——**注释是对的，简报是错的**。
   实测 `region_ast_generator.py:770` `self.regions = self.region_analyzer.analyze()`，且
   `mg.regions is mg.region_analyzer.regions == True`、两者同为 **45** 条，entry 列表含
   嵌套区域（1912/2038/2212/2484/2208/1834/1884/1908 皆在内）。所以 `:19318-19323` 的
   `for _tr in self.regions: if _tr.entry is elif_boolop.merge_block` **确实覆盖全部嵌套区域**；
   它不命中本例的原因是「2164 真的不是任何区域的 entry」（实测 `entry==2164` 的区域数为 0），
   不是遍历范围太小。⇒ 该「注释/行为矛盾」不应记入 Task 11；应记的是**判据选错身份**
   （用「是否区域 entry」代偿「是否该 BoolOp 的自有块 / 是否已被 owner 接手」）。
9. **否证（我自己给的复用探针适用性）**：`D:/Temp/r129/probe_elif.py` 的**区域读数可用**，
   但由它推论「发射路径」不可用；`probe_h.py` 的写入栈可用，但它只 wrap 了
   `_generate_block_statements/_body/_leading_guard_candidate`，未 wrap `_if_generate_*` 与
   `_process_if_blocks`，因此把「第一条 ADD 栈」当成唯一认领者会漏掉 `:54920` 这道下游吞并。

### 六.1 自我更正（对已写入 §三.1 的一句话）

§三.1 里我写了「`_cjb_cond_expr` 交给**无人读**的 `_leading_operand`」。准确表述应为：
`_leading_operand` **有一个**消费者 ——
`core/cfg/region_ast_generator.py:_build_boolop_expression:38412`（`:38426` 唯一调用点）→
`_graft_pending_operand:38289/38305`，其配对判据是「记录挂在 `region.entry` 块上，且该 region 是
BoolOpRegion（读 `region.op_chain`）」。**本形状结构上不可能被接住**：记录挂在
`_cjb_pend_key = 2164 的落空后继 2208` 上，而实测 `get_entry_region_for_block(2208) =
IfRegion@2208 (IF_THEN)`，且 `match` 的 BoolOpRegion entry 只有 `1912/2038/2212/2484`，
不含 2208 ⇒ 交接无接收者（**登记 ∧ 无接收者**，C3 违例的准确形态，而非「无人读」）。

### 六.2 静默豁免判定（重复以强调，须同票封闭）

是。三个相关分支实测**均无任何日志/诊断/计数器/print**（对 `:19307-19324`、
`:54886-54921`、`:16140-16177` 三段逐行扫描，命中数 0），且无异常抛出，故
`generate():1910-1918` 的「区域生成异常逐语句降级」兜底也不会触发。语句凭空消失而流水线
不留痕迹 ⇒ **`rules.md` §1.5 C3（守卫封闭）违例**：`generated_blocks` 的登记与
「谁负责发射该块」之间缺少显式守卫/认领闭环（两处登记、三处拒绝、一个无接收者的交接）。

### 六.3 更正 §五 的「单点建议」—— 分析端角色修复是**惰性的**，不可作为落地判据

实测否证：`core/cfg/region_analyzer.py` 里的 `block_roles` 表有 66 处引用，但
**`core/cfg/region_ast_generator.py`（发射端）对 `block_roles` 的引用数为 0**。
⇒ 即使把 `BlockRole.IF_ELIF_CONDITION` 的优先级修对（§六 第 7 条），
发射端三条拒绝路径（`:19324` 登记 / `:16158-16163` 要求 `_own46.entry is B` /
`:54886-54894` 要求后继非区域入口）**一条都不读它**，产物必然零翻转。
**§五「补充结论」末句与 §三.3 末段推荐的「单点 = 修 `region_analyzer.py:4115-4118`」据此作废**，
降级为「分析端可解释性修复（值得做，但非本缺陷落地判据）」
（角色优先级本身仍宜修正——`region_analyzer.py:4115-4118` / `:4150-4152`）。

**更正后的落地判据（实测驱动，供 FIX 票使用，本票不实现）**：
本缺陷的丢弃由两条**各自独立充分**的吞并通道串成（另见 §六 第 7 条的角色失效证据），
实测单通道抑制 = 产物逐字节不变，双通道抑制 = 语句回来但挂错层级（三.2）。因此

- 若只允许**一个**发射端实现点，须落在
  `core/cfg/region_ast_generator.py:_if_generate_full_elif_chain` 的 merge 尾块处理块
  **`:16140-16177`**（唯一同时能覆盖两条通道的接手点）：把现有
  `_own46.entry is _mb45` 的「兄弟区域入口」身份测试，改为按 **B 自身的块末身份**判定 ——
  「B 的末指令 ∈ 前向条件跳转族 **且** `|B.conditional_successors| = 2`」**⇒** B 是一条
  **兄弟语句的头块**（而非汇合/连接件），此时不得走 `_generate_block_statements(B)`
  （它已被通道①/② 判死），须把 B 交回**包围序列层级**（`_process_if_blocks` 于 parent 的
  块列表）发射，并在交接前对 B 做显式 `generated_blocks.discard` + 接收者断言。
- 同一票内须**同时**封闭两处登记身份（否则 C3 仍不闭合，且实测各自单改零翻转）：
  `:19324` 的认领判据从「B 是否任何区域的 entry」改为身份式「**B ∈ `elif_boolop.blocks`**
  才可认领」（BoolOpRegion 只能登记自有块：实测 `BoolOpRegion@2038.blocks={2038,2080}`，
  `merge_block=2164 ∉ blocks`）；`:54886-54894` 的跳过须加**接收者前置**
  「`get_entry_region_for_block(B)` 非 None **且** 该区域当前未发射」——
  实测本例 `get_entry_region_for_block(2164) = None` 且其 `_leading_operand` 唯一接收者
  `_build_boolop_expression:38426` 要求 B 是 **BoolOpRegion 的 entry**（2208 是 IfRegion entry，
  且 match 的 BoolOpRegion entry 集合不含 2208）⇒ 无接收者的交接必须显式拒绝，不得静默 return。
- 门禁：`matcher.pyc` 的 `match` 单元 16/17 → 须见翻转；两个哨兵
  `trade_info_utils`（HEAD 正确，同走静默认领族）与 `jq_trans_module` 不得变红；
  **最小样例 r1–r7 无判别力，不得用作复现门禁**（三.4）。
