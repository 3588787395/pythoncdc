# Round 23 设计（arm-design）：把「本帧归约上下文」留在帧内（R23-A）＋ loop 条件块前导的发射权（R23-B）

落地前 HEAD = `177774b0`（Round 22 收尾）。诊断出处：任务 #28（Round 23 诊断）、任务 #33
（R23-A 之后 `clock_worker` 残余），最小复现与实测在 `test_repros/round23_clobber/ANALYSIS.md`；
本轮落地与门禁读数见 `fixes.md`，收尾见 `OUTCOME.md`。

---

## 一、靶子：`realtime_event_source.clock_worker` 的 −197（Round 22 SubTask 22.9 ① 移交项）

Round 22 收尾时该条官方读数 `partial 11/12`，唯一缺陷 `clock_worker` 严格尺 `orig=1276 decomp=1079`
（−197）。Round 22 把它从「人工保全产物」里揭出来交给本轮，当时的假设（任务 #22 时期的旧标题）
是「截断 BoolOp 链后父臂未收养子表达式」。

**该假设已被本轮实测否证**（`ANALYSIS.md` §1.1）：402 文件严格 A/B 下，按旧标题实现的候选核
只让 1 个文件指标变化；手写 6 个 or-extension 形状（含 ddmin 最小形）在两个核上产物**逐字节相同**。
⇒ 旧假设不是机制，只是同一文件上的巧合。

**复核成立的归因**（`ANALYSIS.md` §1.2）：or-extension 的三块臂状态 `self._or_then_block` /
`self._or_else_block` / `self._or_rhs_block` 挂在 `self` 上，`_if_generate_normal` 在
`if _has_or_ext:` 分支里两次调用 `_process_if_blocks`（递归归约嵌套 `IfRegion`），被调方在
`_if_generate_normal` 开头（`16526-16528`）无条件把这三个字段复位为 `None` ⇒ **父区域返回后读到
的是子区域的（None）状态**，父的 else 臂被静默丢弃。这是"跨帧可变状态被嵌套归约踩掉"，
与本轮标题（clobber 家族）同名不同源：踩它的不是别的区域，是**自己递归下去的那一层**。

## 二、R23-A：臂状态 callee-saved（本帧局部量）

谓词形状：`if _has_or_ext:` 内所有 `self._or_*` 读取改为本帧快照
`_r23_or_then/_r23_or_else/_r23_or_rhs`（快照点在两次递归调用之前，`_has_or_ext` 求值之后）。

**为什么这是同层判据而不是新启发**：

| 原则 | 审计 |
|---|---|
| P1 自底向上归约 | 不改变归约顺序，只改变"谁的值被读到"。快照发生在本区域自己的帧内、递归之前。 |
| P2 每块唯一归属 | 本区域的臂必须由本区域的归约决定。现状是子区域复位 `self` ⇒ 本区域的臂被**别人的**归约改写，等于臂的归属不确定。 |
| P3 嵌套即抽象节点 | 不涉及节点形状。 |
| P4 父引用子入口 | 不涉及 then/else 列表引用对象。 |
| 禁止跨区域/层启发 | 无 block 集合比较、无其他区域查询；只是把已经是本帧语义的量从 `self` 挪进本帧。 |

一致性核对（本轮实测，非推测）：`_if_generate_normal` 内 `self._or_*` 共 19 处使用，
**全部落在 `if _has_or_ext:` 分支内**（`16829-16879`），函数其余部分与另外两个函数
（`_if_extract_condition_from_instructions` 6 处 = 生产端；`__init__` 3 处 = 复位）都在本帧
快照点之外 ⇒ 快照后不存在任何"读 `self._or_*` 的消费者"，无需写回。

**可测性告警（`ANALYSIS.md` §5 事实 1）**：R23-A 在 `.py` 最小形状层**不可测** —— 6 个手写
or-extension 形状在两核上产物逐字节相同（`fixed by c1a = 0`）。它的非虚证只能由语料锚点给出：
`realtime_event_source` 严格尺 198 → 12。电池因此把 G1 改成打印 `NOT EVALUATED`（空集）而不是谎报 True。

## 三、R23-B：loop 条件块前导语句的发射权归父序列

R23-A 之后 `clock_worker` 从「−197 塌陷」变成「+11 过量发射」，残余拆成三层（`ANALYSIS.md` §3.4）：

* **D1（Q1）`: dt = datetime.datetime.now()` 整条被丢弃** —— 旋转 while 的条件块是「极大直线块 =
  前导完整语句 + 尾部条件表达式」；当该块同时是祖先 `LoopRegion` 的 `header_block` 时，
  `_loop_generate_while` 的 `_cond_is_ancestor_header` 守卫**正确地**跳过 `_eps` 前缀扫描，
  但 else 分支只把整块 `generated_blocks.add(cond_block)`，块内前导语句于是无人认领 ——
  祖先的 body 扫描在「直接子 `LoopRegion` 入口块」分支处 `continue`，从不扫描该块指令。
  产物里 `dt` 在该点未绑定 ⇒ 语义错误。
* **D2 过量发射（+11 → +16）**、**D3 同形块换位**：都排在 D1 之后。

**顺序论证（为什么本轮必须做 D1，即使标尺读数变差）**：`_r10_strict_check.py:105-106`
在 `len(so) != len(sd)` 时立刻 `return 'seq_len'`，逐 token 比较与跳转落点比较根本不执行 ⇒
只要 D1 的 −6 还在，`sad=12` 全是长度差，D2/D3 **完全不被任何一把尺子计分**。
必须 D1 → D2 → D3。

**谓词**（`ANALYSIS.md` §4，落地在 `_loop_generate_while` 帧内）：切点复用既有
`_split_block_condition_prefix`（块内栈深前向模拟，最后一次回到深 0 之后），切出前导段后经
`_build_statements_from_instructions` 归约为语句放进 `pre_stmts`；函数尾部既有
`if pre_stmts: output = list(pre_stmts); output.append(result)` 已负责把它们发射在 `While`
节点之前返回父序列。发射权用 Round 15 的指令粒度台账 `_register_prefix_emitted` 登记。
**不新增 `self` 上的帧态字段**（那正是 R23-A 治的那类错误的再发条件）；切点不存在时返回空 ⇒
与修改前逐字节相同。

| 原则 | 审计 |
|---|---|
| P1 | 谓词只在**本区域自己的** `cond_block` 上求值，求值时本区域已是最内层。 |
| P2 | 块的**条件语义**归 `LoopRegion`、块的**前导语句**归父序列，以指令偏移划界（`prefix_emitted_upto` 正是 A2 台账为此量纲准备的）。现状"整块登记为已生成而前导无人发射"= 把指令摊到无人所有，本谓词把它收回 P2 正轨。 |
| P3 | 产物形状不变：父序列得到 `[pre_stmts..., While]`，`While` 仍是单个抽象节点；前导不是子区域的第二个节点，而是同块内不属于任何区域的语句 —— 与 `AssertRegion` 已落地的 `_collect/_take_assert_prefix_stmts` 契约同构（docstring 里把这两个消费者并写，就是为了留同层证据）。 |
| P4 | 不改 `then_blocks/else_blocks/body_blocks` 任何列表，也不改 `generated_blocks` 对 `cond_block` 的入口引用；只把入口块内部的前缀指令显式化。 |
| 禁止跨区/跨层启发 | 无 block 集合比较、无"其他区域是否也认领此块"查询、无父/兄弟区域类型嗅探；切点只由块内指令栈深给出。 |

## 四、门禁指标：本轮为什么不能用 Σ\|orig−decomp\|

`ANALYSIS.md` §4 的**门禁指标警告**在落地前就被写下：R23-B 会把 `clock_worker` 的长度从 1287 推到
1293（\|Δ\| 从 11 升到 17）。**以 Σ\|orig−decomp\| 为门禁会直接否决这个正确修复**（§7 已把该候选
连同测量一起否决）。本轮改用三条替换指标：

1. **(i) 产物含该语句**：`dt = datetime.datetime.now()` 出现在内层 `while dt.replace(...)` 之前；
   电池另加 `MUST_CONTAIN` 文本断言与 16 case 真值表。
2. **(ii) 官方尺 `first_diff` 索引后移**：从 `index=666`（orig `LOAD_GLOBAL 'datetime'` vs
   decomp `LOAD_FAST 'dt'`）移动到 `index=794`。
3. **(iii) 其余 401 文件逐文件不回退**：全量 A/B 实测「产物长度变化的文件数 = 1」，
   即谓词在语料里的**真实触发面只有 1 个文件**；形状前驱面（`LoopRegion.condition_block`
   内含完整 STORE）在 39 个文件出现，其中 14 个当时已完全匹配，这 14 个必须逐字节零变化。

主门禁仍是 §5 的电池：`b07/b08/b11 → OK` ＋ `b09/b10/a06/c12..c15 → 零变化`，
其中 **b09（同形状但内层是 `if`）是 loop/if 判别子**，b10/c 族是负对照。
