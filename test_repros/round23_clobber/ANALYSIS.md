# Round 23 — 诊断报告：R23-A 之后 clock_worker 残余（clobber 家族？）

角色：Round 23 测试/诊断工程师（只诊断，不改产品代码）。
状态：**完成**（两处遗留见 §8）。

---

## 0. 环境与纪律表

| 项 | 值 |
|---|---|
| 仓库 | `F:/Downloads/pythoncdc-main` @ HEAD `177774b0`，本轮 **未做任何 git 写操作**，工作树保持原样 |
| 仓库内唯一写入目录 | `test_repros/round23_clobber/`（16 个 case `.py` + `run_all.py` + 本文件） |
| 被测核 | 仅镜像：`D:/Temp/r23fix/mirr/head`、`D:/Temp/r23fix/mirr/c1a`（`sys.path.insert`，从不 import 仓库 `core/`） |
| 本轮 scratch | `D:/Temp/r23res/`（probes / build / logs），未写入 `r23fix`、`r23land` 任何文件 |
| 解释器 | `D:/Python/python.exe`（CPython 3.11.9），每条命令前置 `PYTHONIOENCODING=utf-8` |
| `.pyc` 生成位置 | 仅 `D:/Temp/r23res/build/`（仓库内 case 目录只有 `.py`） |
| 单命令时长 | 全部 < 300 s（最长：400 文件语料扫描 ~110 s） |

**非破坏性证明（本轮所有观测手段：直接调用 `build_cfg`/`RegionAnalyzer`（`r23_regions.py`、`r23_shape_scan.py`，不生成 AST）+ 未打补丁的 `pycdc.decompile_pyc`（`run_all.py`、`r23_tokdiff.py`）**：

```
baseline  D:/Temp/r23land/build/resid_cand.py   md5=5ac90803ff7e6bf72bdfd632f0716d4a len=22371
baseline  D:/Temp/r23fix/dump/r23_c1a_re.txt    md5=5ac90803ff7e6bf72bdfd632f0716d4a len=22371
本轮产物  D:/Temp/r23res/build/tokdiff_prod.py  md5=5ac90803ff7e6bf72bdfd632f0716d4a len=22371
char-identical to baseline product: True
```

探针确实触发（非空打印）：`r23_regions.py` 输出 68 个区域 / 8 个目标块的归属；语料扫描输出 400 行 JSONL。

---

## 1. 恢复并复核的归因（含对旧标题假设的否证）

### 1.1 旧标题假设「父臂未收养被截断的 BoolOp 子表达式」——**已被否证（superseded）**

否证证据（本轮实测，非引用）：

1. 若「父臂未收养」成立，则缺陷应出现在 **所有** 携带 or-extension 的函数上。实测语料 A/B
   （`sweep_head.jsonl` vs `sweep_c1a.jsonl`，各 402 条）：**只有 1 个文件的任何指标发生变化**
   （`realtime_event_source.pyc` sad 198→12），其余 401 个文件 `sad`/`n_ok`/`kinds` 全部逐字节相同。
   一个只影响 1/402 文件的机制不可能是 BoolOp 截断的普遍收养缺陷。
2. 本轮手写 6 个 or-extension 形状（case `a01`–`a06`，含 `r23fix/dd/g6.txt` 的 ddmin 最小形状 `a02`）：
   **head 与 c1a 的产物逐字符相同**（`fixed by c1a = 0`，见 §5）。即 R23-A 在 `.py` 形状层面无差别，
   「or 链截断 → 父臂未收养」这条因果链在最小形状上不可复现，因此不能是标题所指的那个机制。
3. 真正的现场证据是臂状态被打点日志直接抓到的（§1.2）。

### 1.2 归因（复核成立）：`self` 上的 or-extension 臂状态被嵌套归约踩掉

打点日志 `D:/Temp/r23fix/logs/ext_target.log`（前代 `r23_orstate.py` 产物，本轮复核其语义与行号）：

```
234  has_or_ext    @6344  ln=16768  then=6406  else=6496  rhs=6374  gb=98
237  ENTER         @6890  ln=0      then=6406  else=6496  rhs=6374  gb=100   <- 子区域进入时父臂仍存活
238  reset_then    @6890  ln=16526  then=...  ->  None                        <- 子帧无条件复位
286  ENTER         @7248  ln=0      then=7248  else=7582  rhs=7216  gb=129
287  reset_then    @7248  ln=16526
```

源码侧对得上：`core/cfg/region_ast_generator.py:16526-16528`（`_if_generate_normal` 入口处
`self._or_then_block = self._or_else_block = self._or_rhs_block = None`）与写入点
`19532-19534` / `19611-19614`、读取点 `16768`（`_has_or_ext`）/ `16825` / `16832` / `16857`。
即：**帧局部量被放在 `self` 上，递归归约 = 调用约定被违反**。原则 2 被违反的方式是
「父区域的臂由子区域的复位决定」，与块归属本身无关。

**R23-A（callee-saved）判定：因果正确、方向正确、幅度不足。**
本轮独立复算锚点：`realtime_event_source` 严格 |orig−decomp| **198 → 12**
（clock_worker 1276 vs 1079 → 1276 vs 1287；get_one_event 19 vs 20 不变），与编排方口径一致。

---

## 2. Q1：`dt = datetime.datetime.now()` 的 6 条指令去了哪里

### 2.1 现场

`clock_worker` 中 `blk 5598`（`LOAD_DEREF self; LOAD_ATTR active; POP_JUMP_FORWARD_IF_FALSE 9214`）
是 `while self.active:` 的旋转前置测试；其后继 `blk 5614` 是 **17 条指令的一个极大直线块**：

```
blk 5614 n=17 succ=[9218, 5738, 5902]
  LOAD_GLOBAL datetime; LOAD_ATTR datetime; LOAD_METHOD now; PRECALL; CALL; STORE_FAST dt   @5614..5672   <-- 完整语句
  LOAD_FAST dt; LOAD_METHOD replace; LOAD_CONST 0; LOAD_CONST 0; KW_NAMES; PRECALL; CALL;
  LOAD_DEREF self; LOAD_ATTR last_date_time; COMPARE_OP <=; POP_JUMP_FORWARD_IF_FALSE 5902  @5674..5736   <-- 内层 while 的条件
```

区域归属（本轮 `r23_regions.py` 直读分析器，c1a 核）：

```
LoopRegion  condition_block=5614  body_blocks=[5738]            blocks=[5614, 5738]     <- 内层 while dt.replace(...)
LoopRegion  condition_block=5598  body_blocks=[5614, 5738, ...]                          <- 外层 while self.active:
LoopRegion  (cond=None)           body_blocks=[5598, 5614, ...]  children=[LoopRegion]   <- 外层 while True:
```

即 **@5614..@5672 与内层循环条件同处一块**，该块整体被 `LoopRegion@5614` 认领为 `condition_block`。

### 2.2 语句实际去了哪里：**哪里都没有——被整条丢弃，不是搬走，也不是重复**

* c1a 产物全文只有 2 处 `dt = datetime.datetime.now()`：第 51 行（`__init__`，另一个函数）与第 220 行
  （内层 `while dt.replace(...)` 体内，对应 @5778）。@5614 那一条 **不存在**。
* token 级差分（`r23_tokdiff.py`，与严格标尺同一 token 定义）在 `orig#667..671 / decomp#667..666`
  只报 `delete`，无配对 `insert`。
* 后果是语义错误（`dt` 在首次内层条件求值处未绑定），不只是字节计数问题。
* **该缺陷早于 R23-A**：`head` 产物、`r23fix/logs/ors_pre21.txt.product.txt`（pre-21 核）在同一位置同样缺失；
  即它一直藏在 −197 的塌陷里，R23-A 把塌陷治好之后才露出来（残余从 198 降到 12；本条 = 6 条原始指令，
  过滤 NOISE(PRECALL/EXTENDED_ARG/CACHE/NOP) 后为 5 个 token，与 `orig#667..671` 对齐）。

### 2.3 机制（点名到行）

`core/cfg/region_ast_generator.py`

* `4869 def _loop_generate_while(...)`；`4880 cond_block = region.condition_block`。
* 该函数把 `cond_block` **整块**消费为条件表达式，随后在 `5486` / `5497`
  （`self.generated_blocks.add(cond_block); self.generated_offsets.add(cond_block.start_offset)`）
  把整块登记为「已生成」，块内条件表达式之前的完整语句从此无人认领。
* 非退化分支里唯一的前导语句提取是 `_eps_*` 那一圈（约 `5350-5487`），它只识别
  `IMPORT_NAME / IMPORT_FROM / STORE_*` 的 **import 前缀**（`5440` 处 `pre_stmts.append({'type':'ImportFrom'...})`、
  `5479` 处 `{'type':'Import'...}`），**没有任何通用的「栈深切分 + 语句归约」**。
* 正确的切分逻辑只存在于 **`is_degenerate_while` 分支 `5500-5523`**：
  `5503 for i, instr in enumerate(cond_block.instructions)` 找首个 `CONDITIONAL_JUMP_OPS/COMPARE_OP` 作切点，
  `5509 for instr in cond_block.instructions[:cond_instr_idx]`，遇 `STORE_FAST/STORE_NAME/STORE_DEREF`
  成段 `_build_statement(...)` → `pre_stmts`。`blk 5614` 是正常旋转 while 的条件块，`is_degenerate_while=False`，
  于是走不到这段。
* 对照面（证明这是 loop 专属缺陷）：IfRegion 路径有通用前缀提取器
  `13422 def _if_extract_cond_instructions(...)` → 返回 `(pre_stmts, cond_instrs)`，
  调用点 `659, 11143, 11778, 11878, 11884, 11889, 15066, 16582, 16588, 16613` —— **全部在 if/elif/BoolOp/入口路径，
  一个都不在 loop 路径**。AssertRegion 另有栈深切分器 `260 _split_block_condition_prefix` +
  暂存契约 `339 _collect_assert_prefix_stmts` / `359 _take_assert_prefix_stmts`
  （消费点 `690, 7238, 10700, 10713, 20901, 21203`）。

### 2.4 最小复现（本轮建立，battery case 编号即文件名）

| case | 形状 | 内层 | head | c1a | 结论 |
|---|---|---|---|---|---|
| `b07_outer_body_stmt_then_inner_rotated_while` | 外层 while 体首句 + 内层 while | while | −3 | −3 | **复现 Q1** |
| `b08_outer_true_loop_body_stmt_then_inner_while` | `while True:`/`while active:`/内层 while（clock_worker 三层） | while | −3 | −3 | **复现 Q1** |
| `b11_chained_compare_loop_cond_prefix` | 同 b07，内层条件是链式比较 | while | −3 | −3 | **复现 Q1** |
| `b09_outer_body_stmt_then_inner_if` | 同 b07，内层换成 `if` | if | **OK** | **OK** | **判别子：loop 专属** |
| `b10_plain_while_body_leading_store` | 体首句 + 体内 `if`（CONTROL） | — | OK | OK | 现有能力，不得回退 |

（−3 = 过滤 NOISE 后 `LOAD_GLOBAL tick / CALL / STORE_FAST dt`；与 clock_worker 的 −5/+1(PRECALL) 同族。）

---

## 3. Q2：成对换位是否同族

### 3.1 「`self` 上的跨帧状态」全量清点（本轮实测，非推测）

`RegionASTGenerator.__init__`（`196-255`）声明的全部可变帧态 + 运行期新赋值，按「递归归约前后是否被读」分类：

| 字段 | 写点 | 类别 | 递归归约是否踩 |
|---|---|---|---|
| `_or_then_block/_or_else_block/_or_rhs_block` | `16526-16528` 无条件复位；`19532-19534`、`19611-19614` 写 | **臂状态** | **是（R23-A 唯一治到的）** |
| `_current_loop` | `4183`→`4210` 恢复；`11205`→`11209` 恢复 | 已有 callee-save | 否 |
| `_suppress_boolop_merge_tail` | `16237`→`16249` 恢复 | 已有 callee-save | 否 |
| `_chain_prefix_generating` | `16694`（保存后恢复） | 已有 callee-save | 否 |
| `_chain_head_active` | `16213` 帧内保存 | 已有 callee-save | 否 |
| `_skipped_outer_try` | `23233` 写 / `24846` 清 | try 专用，if 归约不读 | 否 |
| `_chain_compare_expr_cache`(11042)、`_with_jump_exit_blocks_cache`(41513)、`_gbs_seen_ft`(44639)、`_disc_elif_chain_conds`(14975) | — | 纯缓存（丢了顶多重算） | 否（不携带顺序） |
| `generated_blocks`/`generated_offsets`/`prefix_emitted_upto`/`_entry_prefix_emitted_blocks`/`_entry_import_extracted_blocks`/`_with_cleanup_generated_blocks`/`_assert_prefix_emitted_blocks`/`_generating_regions`/`_generated_regions` | — | **只增不减的单调登记表**，被调方无法撤销调用方的登记 | 否 |
| `_post_break_blocks` | `20593-20594` 唯一写点，唯一读点就在同一判断的 `not in` | 只增、无消费语义 | 否（**写死的路径**，不参与排序） |
| `_trailing_returns` | 声明 `209`，消费 `1655-1659` | **无写入者**（全文件仅此 3 处） | 否（死字段） |
| `_loop_depth`/`_try_depth` | 计数器 | 无「递归前捕获、递归后使用」形状 | 否 |
| `_assert_prefix_stmts` | `356` 按 `id(region)` 键控、`361` pop | 键控暂存，天然免踩 | 否 |

结论：**除 `_or_*` 三件套外，`self` 上不存在第二个「被调方复位、调用方回读」的帧态字段**。
`_trailing_returns` 与 `_post_break_blocks` 虽属同族（跨帧 list/set），但前者无人写入、后者无消费语义，
两者都不可能改变语句顺序。→ **Q2 与 R23-A 不是同一族。**

### 3.2 三条独立否证同族的实测

1. **语料 A/B 只差 1 个文件**（§1.1-1）。若两处换位是跨帧踩态所致，245 个携带类似臂形状的文件不可能零变化。
2. **手写「双生同形条件」形状 `d16_twin_conditions_sibling_arms`（两个 textually-identical 的 `if a > k:` 分处兄弟臂，
   体内仅跳转落点不同）在 head 与 c1a 下都是 `OK |d|=0`** —— 不存在通用的「同形臂换位」缺陷。
3. **换位块所在区域与 or-ext 区域无交集**：`@6496` 属 `IfRegion@6280`（IF_ELIF_CHAIN，`elif_conditions=[6846]`），
   `@8666/@8852` 属 `IfRegion@7634`（`elif_bodies=[[8666,8688,8852]]`、`elif_final_else=[8904,8926,9144,8948,8964,8976,8974,8980]`）；
   打点日志里被踩的 or-ext 区域是 `@6344` 与 `@7186`。臂状态复位发生在 `@6890`/`@7248` 的帧，
   与两处换位的块集合互不引用。

### 3.3 那两处换位到底是什么（token 级实测）

用严格标尺的 token 定义（跳转只记 `('<JUMP>', 归一 opname)`，**落点不进 token**）重跑 difflib
（`D:/Temp/r23res/probes/r23_tokdiff.py`，产物 `D:/Temp/r23res/logs/tokdiff_c1a.txt`）：

```
delete   orig#667..671   decomp#667..666      <- Q1 的 dt=now()，5 token
delete   orig#795..859   decomp#790..789      <- 换位 (a) 前段：65 token 整组
insert   orig#907..906   decomp#837..896      <- 换位 (a) 后段：60 token 整组
replace  orig#965..976   decomp#955..955
insert   orig#1051..1050 decomp#1030..1129    <- 换位 (b) 前段：100 token 整组（check_trading_time 群）
delete   orig#1166..1170 decomp#1245..1244    <- 换位 (b) 后段：5 token（check_handle_date 群）
replace  orig#1172..1177 / 1183 / 1189..1248
SUMMARY token-level: delete=75 insert=160 replace-span=79
```

判定：

* 换位 (a) 是 **`@6496` 与 `@6758` 两组同形条件块在产物中被以相反次序发射**；即使在「落点不算」的 token 口径下
  它们仍 **不等长（65 vs 60）**，所以不是 difflib 对相同序列的任意配平（那会报 equal），
  而是 **产物少发了 5 条**（`if not before_trading <= now_time < pm_close:` 的链式比较折叠差异）叠加次序错位。
* 换位 (b) 同理：100 token 群被整体提前/推后。
* 两者都发生在 **elif 链 / merge-block 的发射次序**上：`IfRegion@7634` 的
  `elif_final_else=[8904, 8926, 9144, 8948, 8964, 8976, 8974, 8980]` 与
  `else_blocks=[8592, 8666, 8904, 8688, 8852, 8926, 9144, ...]` 都是 **认领顺序而非偏移顺序**
  （8904 排在 8688/8852 之前、9144 排在 8948 之前）。`_process_if_blocks` 自身按 `20323`
  `for block in sorted(blocks, key=lambda b: b.start_offset)` 排序，因此**单次调臂内部**不会错位；
  错位来自 **elif 链把「一个 arm」拆成多次发射/嵌套区域抽象节点**时，父链以 `elif_bodies` /
  `elif_final_else` 的 **列表顺序** 串联各段。要坐实需逐臂打点发射序列 —— 见 §8 未完成项。

### 3.4 真正的 blocker

**Q1（§2.3 的 loop 条件块前缀丢失）是残余的唯一 blocker**，三条理由：

1. **官方标尺的第一处差异就是它**：`bytecode_diff` 报 `first_diff @ 指令 666`
   （orig `LOAD_GLOBAL 'datetime'` vs decomp `LOAD_FAST 'dt'`）—— head 与 c1a 同一个位置。
2. **严格标尺现在是瞎的**：`_r10_strict_check.py:105-106`
   `if len(so) != len(sd): return 'seq_len', ...` —— 长度不等时**立刻返回**，后面的逐 token 比较与
   跳转落点比较根本不执行。也就是说：只要 Q1 的 −6 还在，`sad=12` 里那 11/1 全是长度差，
   **换位 (a)(b) 完全没有被任何一把标尺计分**；先把 −6 补回来（长度仍不等，变成 +17），
   再把 +17 的过量发射削平（长度相等），标尺才会开始看见 (a)(b)。顺序上必须是 Q1 → 过量发射 → 换位。
3. Q1 是唯一使产物 **语义错误** 的一条（`dt` 未绑定），另两条只影响指令次序。

---

## 4. 同层谓词设计（R23-B）——逐条对照四条区域归约原则

**谓词（可直接实现，全部在 `_loop_generate_while` 帧内）**：

> 设 `cond_block = region.condition_block`（`4880`）。若 `cond_block` 在「块首 → 条件表达式起点」之间
> 含 **至少一条完整语句**，则该语句序列归约为 `pre_stmts`，置于本区域产生的 `While` 节点之前发射；
> `cond_block` 的登记由 `generated_blocks.add(cond_block)`（块粒度）改为
> `prefix_emitted_upto[cond_block] = <条件起点指令偏移>`（指令粒度，A2 台账既有语义）。
> 条件起点 = 复用 `260 _split_block_condition_prefix` 的栈深前向模拟切点（最后一次回到深度 0 的位置），
> **不用** `5503` 的「首个 COMPARE_OP/条件跳转」（它会把 `dt.replace(second=0,microsecond=0) <= x`
> 的调用段一起误判为前导）。若切点不存在（整块都是条件）→ 行为与今日完全相同（谓词自然为假）。

配套：`pre_stmts` 通过 AssertRegion 已经验证过的暂存契约交给父序列
（`_assert_prefix_stmts` 的 `Dict[int, List[...]]` 按 `id(region)` 键控，`359 _take_assert_prefix_stmts` pop），
不要新增 `self._*` 标量 —— 那正是 R23-A 治的那类错误的再发条件。

**逐条审计**：

| 原则 | 审计 |
|---|---|
| P1 从最内层到最外层识别区域 | 谓词只在**本区域自己的** `cond_block` 上求值，求值时本区域已是最内层（`_generate_region` 自底向上到达此处）；不窥探父区域，也不看兄弟区域。 |
| P2 每个块在任何场合只属于一个区域 | 块的 **条件语义** 归 `LoopRegion`，块的 **前导指令** 归父序列，以 `prefix_emitted_upto`（指令粒度）划界；正是 A2 台账为「一个块内并存多条语句 + 下一区域前导」设计的量纲。现状是把整块划给子区域却 **不发射前导**，等于把指令摊到「无人所有」——本谓词是把它收回 P2 的正轨。 |
| P3 嵌套区域在其父区域中作为单个抽象节点表示 | 产物形状不变：父序列得到 `[pre_stmts..., While(...)]`，`While` 仍是一个节点；被提取的前导不是「子区域的第二个节点」，而是「同块内不属于任何区域的语句」，与 AssertRegion 已落地的 `assert` 前导契约同构。 |
| P4 父区域的 then/else 列表引用子区域的入口而不是子区域的所有块 | 谓词不改 `then_blocks/else_blocks/body_blocks` 任何列表，也不改 `generated_blocks` 对 `cond_block` 的入口引用（`cond_block` 本就是入口块）。它只把「入口块内部的前缀指令」显式化。父列表的引用对象不变。 |
| 禁止跨区/跨层启发 | 无 block 集合比较、无「其他区域是否也认领此块」的查询、无偏移区间包含判断、无父/兄弟区域类型嗅探；切点只由 **块内指令的栈深** 决定（同层、同块、单区域）。 |

**风险面（本轮实测，供门禁预算）**：谓词的前置形状（`LoopRegion.condition_block` 内含完整 STORE 语句）
在 402 个语料 pyc 中出现于 **39 个文件**，其中 **14 个文件当前已完全匹配** —— 这 14 个是
「形状出现但不致错」的活证据（体扫描已正确处理），谓词必须对它们 **逐字节零变化**。
`r23_shape_scan.py` + `r23res/logs/scan2.jsonl` 可复算该清单。

**门禁指标警告**：R23-B 会把 `clock_worker` 的 c1a 长度从 1287 推到 **1293**（|Δ| 从 11 升到 17）。
**用 Σ\|orig−decomp\| 当门禁会直接否决这个正确修复。** 必须改用：
(i) 产物文本/AST 含该语句（本轮 `MUST_CONTAIN` 断言已内建）；
(ii) 官方标尺 `first_diff` 索引从 666 向后移动；
(iii) 其余 401 文件逐文件 sad 不回退。

---

## 5. 电池（`run_all.py`）与 GATE

结构：16 个最小 case `.py`（本目录）+ 1 个语料锚点；每个 core 一个 **全新子进程**
（`--worker --core <mirror>`），`.py` 现场编译进 `D:/Temp/r23res/build/`，产物再编译后用镜像自带
`_r10_strict_check.strict_compare` 逐函数判定，另跑 `MUST_CONTAIN` 文本断言。
`--cores a=...,b=...` 可加候选核（默认 head, c1a）。`--only b07 --dump` 打印产物。

门禁：**G0** 语料锚点在最后一个核上必须严格变好（R23-A 非虚证）；
**G2** 全部 `CONTROL` case 在每个核都 OK；**G3** 不得有「head OK、后核 FAIL」的回退；
**G1**（单独报告，不计入 GATE）`PRED_R23A_FIX` 形状须被 R23-A 修复 —— 见下方结论。

实测（`D:/Temp/r23res/logs/battery3.txt`，`D:/Temp/r23res/build/battery_results.json`）：
```
CORPUS ANCHORS (strict |orig-decomp| summed over the file's functions)
  realtime_event_source  head |d|=198  textlen=18560  clock_worker orig=1276 decomp=1079; get_one_event 19->20
  realtime_event_source  c1a  |d|=12   textlen=21774  clock_worker orig=1276 decomp=1287; get_one_event 19->20
  -> improves 198 -> 12  (R23-A non-vacuity proof)
cases=16  CONTROL=6  OK-on-all-cores=9   fixed by c1a=0  broken by c1a=0
sum |orig-decomp| (py shapes): head=21, c1a=21
G0=True  G1=(vacuous, see below)  G2=True  G3=True     GATE: PASS
```

记录清单：完整跑 `battery2.txt`（标记下调前）与 `battery3.txt`（下调后，G0/G2/G3 与 16 case 数字完全一致）；
G1 行在 battery3 里仍打印 `True`（当时 PRED_R23A_FIX 集合已空 = 虚真），
`run_all.py` 已改为打印 `G1=NOT EVALUATED: no PRED_R23A_FIX case exists`，
由 `--only c12` 冒烟跑复核（同样 `GATE: PASS`，`battery_final.txt` 因 290 s 单命令上限未跑完全部 16 case，
故以 `battery3.txt` 为准）。

**电池暴露的两件事实（对接单工程师）**：

1. **R23-A 在 `.py` 形状层不可测**（fixed=0，且 6 个 or-ext 形状产物逐字节相同）→ 它只能靠语料锚点验收。
   本轮把 a01–a05 的标记从 `PRED_R23A_FIX` 下调为 `DIAG_OR_EXT_NOEFFECT`（文件头已注明），
   `G1` 因此打印 `NOT EVALUATED`（空集，不再谎报 True）—— 这是 **测出来的**，不是漏配。
   细分 a01–a05 的 `FAIL`：其 `MUST_CONTAIN: elif ...` 断言 **全部通过**（父的 else/elif 臂没有被丢），
   失败点在 **then 臂自身塌陷为 `pass`**（`a02`：orig 31 → decomp 25，head 与 c1a 同样塌）
   —— 那是 R16 那条「sink-arm 塌陷」线（见 memory `project-r16-lead-sink-collapse`），
   与 `_or_*` 臂状态复位无关，故 R23-A 对它无差别，符合 §3.1 的字段清点。
2. **Q1 形状可测且已被复现三例**（b07/b08/b11 各 −3），并由 b09 提供 loop/if 判别子。
   R23-B 的验收应以 `b07/b08/b11 → OK` + `b09/b10/a06/c12..c15 → 零变化` 为主门禁。

「不得改变已完美文件」的编码方式：CONTROL 6 例 + 语料锚点之外的 401 文件 sad 不回退（G3 的 .py 层代理 +
全量 A/B 的 .pyc 层实证，见 §1.1-1）。

---

## 6. 本轮结论

* **R23-A 可落地**：因果正确、语料零回退（0 worse / 1 better）、Σsad −186，且它是把 `clock_worker`
  从「−197 塌陷」救回「+11 过量发射」从而让 Q1 第一次 **可见可测** 的前置条件。
* **但 R23-A 单独不能收口本轮**：翻转 0 个 pyc（已实测：402 文件里仅 1 个文件指标变化，且该文件仍 bad）。
* **残余本轮能收吗？不能。** `realtime_event_source` 要 12/12 需同时消掉
  D1（Q1，−6）、D2（过量发射，+17）、D3（同形块换位，§3.3）三层；只 D1 有最小复现与明确谓词，
  D2/D3 连标尺都还看不见（§3.4-2）。
* **建议本轮的「≥1 pyc 收口」走 D1 路线**：实现 R23-B 后，优先在 §4 风险面 39 个文件里
  找「bad 函数唯一、且缺的恰是 loop 条件块前缀」的 pyc 作翻转目标；
  本轮给出的低悬候选（`badfn=1`，携带精确形状）：
  `fly/common/common.pyc`、`iqcommon/data/api_data.pyc`（sad=0，属内容级差异）、
  `iqengine/plugins/plugin_system_trade/ptrade_broker.pyc`(sad=1)、
  `iqengine/plugins/plugin_fly_data/fly_api/history_api.pyc`(sad=2)、
  `iqengine/plugins/plugin_fly_data/__init__.pyc`(sad=4)、`fly/common/flytools.pyc`(sad=5)。
  注意 sad=0 者按定义不可能被「补 6 条指令」翻转（长度本就相等），须先单查其 `seq_diff`；
  真正可能因 D1 翻转的是 **badfn=1 且 sad>0** 且其 sad 恰由缺失前导构成的文件。
* 若要本轮即收一个 pyc，**最小工作量组合 = R23-A + R23-B**，且门禁必须按 §4 的三条替换指标执行，
  不能用 Σsad。

---

## 7. 被否决的候选（附杀死它的测量）

| 候选 | 否决理由 / 测量 |
|---|---|
| 「父臂未收养被截断 BoolOp 子表达式」（旧标题） | §1.1：402 文件 A/B 仅 1 文件变化；6 个手写 or-ext 形状（含 ddmin 最小形）两核产物逐字节相同。 |
| 「换位 (a)(b) 属于同一『self 跨帧状态』家族」 | §3.1 穷举：除 `_or_*` 外无第二个「复位+回读」字段；`_trailing_returns` 无写入者、`_post_break_blocks` 无消费语义。§3.2 三条独立否证。 |
| 「通用同形兄弟臂换位缺陷」 | case `d16`：双生同形条件在 head 与 c1a 下均 `OK \|d\|=0`。 |
| 「difflib 对相同序列的任意配平（换位是测量伪影）」 | `tokdiff_c1a.txt`：落点归一后 (a) 仍是 65 vs 60 的 **不等长** 删除/插入对，相等序列会被判 equal。 |
| 「把 `_if_extract_cond_instructions` 直接搬到 loop 路径」 | 未测先否：其签名与 `IfRegion` 语义耦合（`11143/11778/11878/11884/11889/15066/16582/16588/16613` 全在 if 族），且它按 `region` 的 merge/then 集合定切点 = 跨结构读取；R23-B 用块内栈深切点（`260`）更同层。 |
| 「以 Σ\|orig−decomp\| 为 R23-B 门禁」 | §4：R23-B 使 clock_worker |Δ| 11→17，标尺会否决正确修复。 |

---

## 8. 未完成 / 交接缺口（诚实列出）

1. **D3 换位的发射点未点到行**：需要「逐臂发射序列」打点（在 `_if_generate_elif_chain` `14873` 与
   `_process_if_blocks` `20022` 输出处臂语句列表产物的顺序，非破坏性已验证可行）。
   本轮判定的是「不同族」，未判定「谁排的序」。
2. **D2（+17 过量发射）未分解**：`insert orig#1051..1050 decomp#1030..1129`（100 token）与
   产物中 `try/except` 后多发的 `break`（c1a 产物 246/248/249 三处，源仅 246/248 两处）未逐条归因。
3. **R23-B 未建候选核**：本轮纪律为只诊断；`apply_spec.py` 路线与 spec 锚点已备好
   （切点在 `5486/5497` 登记处之前，新函数建议紧邻 `339/359` 的 AssertRegion 契约放置），
   以及 `--cores c1a=...,r23b=...` 的电池接法已就绪。
4. **翻转目标筛选未做**：§4 的 39 文件清单需按「缺失指令是否等于 loop 条件块前导」逐条比对
   （`r23_tokdiff.py --core <mirror> --pyc <file> --fn <func>` 可直接跑）。
