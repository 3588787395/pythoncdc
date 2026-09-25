# Round 65 · diag5 · ANALYSIS（机制结论 / 判据 / 已证伪路线 / 下一轮线索）

只读诊断。所有行号都是**落地字节**（`region_ast_generator.py` 3 103 668 B / sha `c9099bb0fc35` / BOM+CRLF）
的行号，且都用 `grep -n` 复核过 + 用 monkeypatch 计数证明「运行时真被调用」——见 FACTS §3.3、§5。

---

## 1. 双生 `get_kline_time_by_section`：一个「**generated 标记语义过载**」的两个切面

### 1.1 共同根因
`self.generated_blocks` 这个集合同时承载了**三种互不等价的语义**：

| 语义 | 由谁写入 | 是否代表「该块的语句已进 AST」 |
|---|---|---|
| S1 语句发射 | `generate()` 入口通道 L766 / L996 / L1102（并另记 `_entry_prefix_emitted_blocks`） | **是** |
| S2 表达式操作数认领 | `_generate_boolop` 条件上下文模式（`value_target=None` → `_generate_boolop_impl` 只写 `condition_expr`、`return None`） | **否** |
| S3 汇合点记账 | 区域自己的 `merge_block` / `_chain_blocks[1:]` / `_downstream_r35.blocks` | **否** |

L11528 `if region.entry and region.entry in self.generated_blocks` 与 L17347
`_should_extract_entry = (region.entry not in self.generated_blocks)` 都按 S1 解读这个标记，
于是 S2/S3 造成的标记把「还没发射」误判成「已经发射」。本批两条编辑就是把 S2/S3 与 S1 分开：

* **D5-A（L11581-11584）**：S3 —— 前驱兄弟区域把它的 `merge_block` 记进 generated，
  而这个汇合块**恰好是后继 IfRegion 的 entry**。撤销「已发射」推断。
* **D5-B（L17346-17348）**：S2 —— 条件模式子 BoolOpRegion 认领了 and 链首块，
  而 `generate()` L745 的 passthrough 分支**已经显式把该块前缀语句的发射权让给了这里**。撤销封锁。

### 1.2 判据的同层次结构身份（这是可以进代码注释的版本）

**D5-A**（三条件同时成立，全部只看 entry / merge_block / then_blocks / block_to_region）：
```
(a) block_to_region[region.entry] is region          —— 原则 2「每块唯一归属」：
        entry 块的归属者就是本 IfRegion，没有任何 BoolOp/Ternary 子区域认领它。
        （IfRegion@530 的 entry 归属是 BoolOpRegion@530 ⇒ 不会自触发。）
(b) any(b not in generated_blocks for b in then+else) —— 本区域还有未发射的臂块。
        若整条 if 真被发射过，其臂块必然同时被认领。
(c) any(pr is not region and pr.entry is not region.entry
         and pr.merge_block is region.entry for pr in regions)
        —— 这个 generated 标记只可能是**前驱区域的汇合点记账**（S3）。
```
归约方式：三条成立 ⇒ **不** `return []`，继续 `_detect_if_region_as_while_loop` →
`_if_generate_normal`，由本区域自行认领 entry、重建条件。
AST 映射：`ast.If(test=由 entry 块尾 POP_JUMP_FORWARD_IF_FALSE 重建的 Compare(..., In, ...),
body=then_blocks 语句, orelse=[])`。

**D5-B**（四条件同时成立）：
```
(a) region.entry is not cond_block                   —— and 链首块不是主条件块（外层 if 已给）。
(b) block_to_region[region.entry] is region          —— 同上，原则 2。
(c) 存在直接子 BoolOpRegion c：c.entry is region.entry
    且 not c.value_target（条件上下文模式，c 不产出任何语句）
    且 region.entry ∈ c.op_chain 的成员块            —— 精确刻画「generated 只来自操作数认领」。
(d) region.entry not in self._entry_prefix_emitted_blocks
    —— 前缀语句尚未被 generate() 任何入口通道发射过。
```
归约方式：命中 ⇒ 撤销封锁，照常调用 `_if_extract_cond_instructions(region.entry, region)`；
该方法既有的「cond_block 是 TernaryRegion.merge_block 时跳过首个 `STORE_*`」规则负责不重复发射
`offset = …`，条件操作数仍归 `_if_extract_condition_from_instructions` /
`_discover_predicate_and_chain`。
AST 映射：`pre_stmts=[ast.Assign(Name datetime_list,
Subscript(Name datetime_list, Slice(None,None,Name offset)))]`，排在 `If` 之前。

**(b)+(d) 是关键收窄**。第一版 D5-B 只有 (a)+(c)，实测在
`IQEngine/utils/scheduler.pyc::run_weekly` 上把 `_verify_function('run_weekly', func)` 与
`minute_time = self.get_checked_time(minute_time)` **各重复发射一次**（43/45→42/45，OVER +8）。
`run_weekly` 的块 0 归属是普通 `Region@0`（不是 IfRegion），且它走的是 `generate()` L762/L801
入口通道 ⇒ 前缀已发射并已登记进 `_entry_prefix_emitted_blocks`。两个条件各自排除了这一类。
这个陷阱在落地代码 L17340-17345 的 R23-N21 注释里早就写明过（`get_trading_day_by_date` 的
import 被生成两次），我只是把它换成了可判定的 provenance 事实，而不是继续用块级标记猜。

### 1.3 为什么两条**必须成对**
A 单独：190→203（找回 14 指令段的 if）；B 单独：190→197（找回 6 指令段的赋值）；
两支都仍然 `matched_functions` 不变。只有 A+B 让两条语句同时回到 AST，
双生两支同时 `19/21→20/21` 与 `22/24→23/24`，严格尺同时 `20/22→21/22`、`25/27→26/27`。
合成件 `synth/v2.pyc`（13 行）在这一点上是正品同构的最小证人：landed 1/2、A 1/2、B 1/2、**AB 2/2**。
⇒ **主代理落地时请按 `specs/r65d5_ab.json`（一份 spec 两处 edit，同一文件）整体落地，不要拆开。**

### 1.4 双生同步性（BRIEF 约束 3）
两支 `.pyc` 的 `align.py` opcode 序列**逐字相同**（只差文件名/行号）。候选的每一行读数都是
两支同时测的，全程同读数（190 / 203 / 197 / 203 / 固定消失）。没有出现「只修一支」。

---

## 2. `flyAccount::_do_request`：值语境三元的 **RETURN 折叠被自家 POP_TOP 守卫挡死**

过冲 +7 **完全**由 7 处 `POP_TOP; LOAD_CONST None` 构成，**零条指令被删除**（FACTS §3.1）。
7 处与 7 个「merge 块只有一条 `BUILD_TUPLE 2`、`merge_context is None`」的 TernaryRegion
（280/296/1254/1310/1770/1992/2014）逐一对应。第 8 处 `LOAD_CONST None`@2184 归
`ctx='store'` 的 TERN@2056。

源码事实：`return error_dict, ({} if is_dict else [])` 被归约成
`(error_dict, {} if is_dict else [])` 表达式语句 + 凭空 `return None`。

机制：三元区域把 `error_dict, <IfExp>` 这个元组重建出来后**没有吃掉 merge 块尾部的
`RETURN_VALUE`**，于是该元组按表达式语句发射（自带 POP_TOP），`RETURN_VALUE` 退化成
`Return(value=None)`。负责把尾 `Expr` 提升成 `Return` 的既有方法是
**`_apply_r23n6_return_promotion`（`def` 落地 L47376）**，而它在 **L47420-47423** 有守卫：
「块尾（跳过 JUMP/EXTENDED_ARG 后）是 `POP_TOP` 就不提升」。真品这里那个 POP_TOP 正是
三元先发射 Expr 留下的产物 ⇒ **守卫被自己的上游产物触发，提升通道自我关闭**。
这是本批我认为最值得下一轮动手的点，但**本批没出候选**：动它要改 POP_TOP 守卫的语义，
而该守卫是 R23-N6/W14 为 f-string/boolop 重载文件加的，`canary.txt` 四支
（含 `quotation.pyc` 143/143）正好是它的保护区，我没有轮次再把它做窄并全量回归。

`{'type':'Return','value':None}` 的另外三处合成点在 `_generate_handler_body_statements`
（`def` L26569；行 26793 / 27082 / 27539），L27526-27533 的注释已经在处理「return 值表达式
在前驱块被误判为裸 Expr」这一现象（quotation.pyc HTTPError handler 出现 4 个 `return None`），
说明这是**同族问题的另一处补丁**，不是孤例。

### 2.1 被证伪的路线（BRIEF 包袱 1）
R64 移交给 diag5 的站点 `_loop_build_if_with_exit_branches`「约 L10470」：
`grep -n` 复核 ⇒ 函数**存在**，`def` **正好 L10470**，全文件引用 2 处（def + L10014 调用）。
行号是真的，**但路线是错的**：它是 loop 侧 helper，而 `_do_request` 的 7 个出站点全在
`IfRegion@36` / `IfRegion@820` / `IfRegion@1288` / `IfRegion@1358` 的**臂里**，不在任何 LoopRegion 内；
monkeypatch 计数实测 **`_do_request` 全程调用 0 次**。
⇒ 下一轮别再回 L10470。「过冲由 R63-B4 成对引入」我**无法在只读约束下验证**：
`h62.py build` 有 `head mirror == worktree bytes` 硬断言，装不了旧字节核臂。

---

## 3. `scheduler` 两支 + `fileio_utils::write` + `wizard::params_analysis`：同一族 **try/except/finally 排程**问题

* `get_checked_time` [106,106,0,43]：`orig=122 decomp=122`、**零增删**，
  `hour, minute = divmod(minute_time, 100)`（orig 源码行 241）整块从 **orig@130（内层 try 体内、
  handler `PUSH_EXC_INFO`@170 之前）** 搬到 **decomp@352（handler 汇合之后）**，
  于是两处 `JUMP_FORWARD` 目标从 390 变 352。BRIEF 包袱 4 的「SAME-LEN ⇒ 找块被排到哪儿」成立。
* `fileio_utils::write` [637,637,4,519]：`orig=720 decomp=721`，29 个 hunk 里只有 1 个是实质的：
  `o@206 9->2`，orig 的 `NOP | LOAD_CONST None×3 | PRECALL | CALL | POP_TOP | LOAD_CONST True |
  RETURN_VALUE`（finally 收尾 + `return True`）被换成 `EXTENDED_ARG | JUMP_FORWARD to 778`
  ⇒ **收尾块被搬到函数末尾、用长跳过去**。jumpdiff=4 就是这个长跳的产物。
* `wizard::params_analysis` [133,126,1,117]：`delete o@50 9->0` 丢
  `LOAD_GLOBAL NULL+float | LOAD_FAST value_params | PRECALL | CALL`（`float(value_params)`），
  同时在 40-44 多出 `POP_EXCEPT | LOAD_CONST None | RETURN_VALUE` ⇒ except 收尾排程 + 一条被吞调用。
* `scheduler::run_daily` [77,71,0,56]：**不是**区域归约层问题 —— `minute` 是 cell variable，
  落地丢的是 `MAKE_CELL minute` / `STORE_DEREF minute` / `LOAD_CLOSURE minute` / `SWAP`，
  属于 co_cellvars/freevars 与代码生成层。区域模型里**没有**同层次结构判据能表达它
  （判据只能问 entry/merge_block/parent/then_blocks/body_blocks/控制流角色/指令模式），
  所以本批对它出 `NONE`：硬造判据就会退化成「按变量名 / 按是否闭包」的跨区域启发式。

⇒ 下一轮可检验判据（我建议的方向，纯区域层、同层次）：
**「一个被 `TryExceptRegion.try_blocks` 包含的块 B，若 B 的终结指令是 `JUMP_FORWARD` 且其目标在
`try_blocks ∪ handler_blocks` 之外，则 B 的语句必须留在 try 体内发射；不得把 B 排到 handler 之后的
汇合点」**。上面三个 SAME-LEN/排程案例（get_checked_time、write、params_analysis）形状一致，
都满足这条；而它们分属不同文件、不同函数名、不同偏移，符合「不许按名字/阈值」的要求。
本批未做，因为轮次优先给了双生正品。

---

## 4. `order_api`：R50 结论**未被推翻**，且我补了一条正向证据
BRIEF 包袱 2 说别再碰汇合块归属，要动就动 `_try_build_ternary_kwarg_call` 的 kwarg 槽位 bail
+ 只向前走的链遍历。我复核了这两点是否**在活跃路径上**：
monkeypatch 计数 ⇒ `_try_build_ternary_kwarg_call`（`def` 落地 **L42708**）对
`option_order` 与 `future_order` **各调用 1 次**，`_discover_predicate_and_chain` 分别 1 / 2 次。
⇒ memory `project-r50-ternary-kwarg-bail` 指认的方法是活的，不ghost。
本批未出候选（优先级排 third 之后，轮次不够做「kwarg 槽位 bail 收窄 + 链遍历双向化」这种
需要 generator/analyzer 成对的大改）。

## 5. 本批候选的边界声明
* 只改 `core/cfg/region_ast_generator.py`，**不需要 analyzer 成对**。
  两处判据只读**已存在的分析端字段**（`block_to_region` / `merge_block` / `op_chain` /
  `value_target` / `children` / `inline_boolop_chains`）与生成端**既有**的 provenance 集合
  （`_entry_prefix_emitted_blocks`、`_generated_regions`），没有新增分析端状态。
* 没有任何一条判据读函数名、文件名、偏移阈值或字面量计数。
* 没有破坏「嵌套区域作为单一抽象节点」：D5-A 撤销的是一个**兄弟**汇合块上的过度认领，
  D5-B 撤销的是一个**子表达式区域**在链首块上的过度认领，两者都在同一层回答
  「这块指令归谁发射」，没有让父区域越层展开子区域的内部块。
