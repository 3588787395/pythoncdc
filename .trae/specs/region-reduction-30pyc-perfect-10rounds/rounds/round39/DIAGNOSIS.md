# Round 39 开工诊断（线 A：子形状 A / elif 臂尾 `continue` 少发一条回边）—— 只测不改

字节基线沿用 Round 38：commit `4d3657ac`（核未动，`core/cfg/region_ast_generator.py`
sha256[:20] `6b0759b1a0a566a4eb8f`），全部插桩在进程外完成（包装类方法，不写 core）。
Scratch：`D:/Temp/r39diagA/{dump39.py, probe39.py, probe39b.py, src39.py}`。

## 一、Round 38 记录的候选站点被实测否证

`:15990-16018` 那段「把链尾 `Continue` 提升到链级」的判据（`_elif_shared_merge_tail`，A3 修）
在**见证函数的整个反编译过程中一次都没有到达**：把包含 `_elif_shared_merge_tail` 的方法
`_if_generate_elif_chain`（`def` 在第 14977 行）包一层计数器，对合成见证跑一遍 ⇒
`_if_generate_elif_chain` 调用数 **0**。⇒ 本轮靶的发射路径不是它；任何照抄 Round 38 §五 的行号
去改 `:16001-16018` 的候选都无需再测。

## 二、见证与逐条指令实测（不依赖语料）

`src39.py :: ctl_two_cont`（`for` → `try` → 两个各带 `continue` 的顺序 `if`）在落地字节上
`strict_compare = ('seq_len', 'orig=37 decomp=36', True)`，缺的正是一条 `JUMP_BACKWARD`。

原始（37 条，节选）：

```
@46 POP_JUMP_FORWARD_IF_FALSE -> 60     # 第二个 test 的假分支落在 @60
@48 LOAD_CONST '-1' … @54 STORE_SUBSCR  # 第二臂体
@58 JUMP_BACKWARD -> 6                  # 臂自己的 continue
@60 JUMP_BACKWARD -> 6                  # 「两臂都没走」的汇合块，独立的一条物理回边
```

产物（36 条，节选）：

```
@46 POP_JUMP_FORWARD_IF_FALSE -> 58     # 假分支被改指到 @58
@48 … @54 STORE_SUBSCR
@58 JUMP_BACKWARD -> 6                  # 只剩一条：@58 与 @60 合并
```

产物源码是 `if …: 赋值; continue / elif …: 赋值` 之后在**链级**再补一个 `continue`；
忠实形态应是 `elif …: 赋值; continue` ＋ 链级 `continue`（两支各一条物理回边）。

## 三、发射时刻的真实结构（进程外包装 17 个会构造 `Continue` 的方法）

命中这一形状的调用（外层 `if` 区域，`region_entry=12`）：

```
_if_generate_normal (def 16638)  region=IfRegion entry=12
   then_blocks=[24, 34]   else_blocks=[36, 48]   merge_block=<offset 6>
   -> {'body': [Assign(d[k]=1), Continue], 'orelse': [If(…)]}
```

* `then_blocks` 的第二块 @34 就是臂的 `JUMP_BACKWARD`，它**被表示成了 `Continue`**（正确）。
* `else_blocks=[36, 48]`：@48 块尾同样有一条 `JUMP_BACKWARD -> 6`（@58），但它**没有**被表示成
  `Continue` —— 发射器认为「臂的出口就是 merge，落到后面那条就行」。
* 关键结构事实：本区域的 `merge_block` 就是**循环头块**（offset 6，`FOR_ITER` 所在块），
  而链级那个 `continue` 来自另一个独立块（@60）。也就是说：**同一条 merge 被两条不同的物理块
  跳到**（臂尾 @58、未取臂的 @60），产物只保留了后者。

⇒ 待找的是「臂尾块的终止跳转被当作落到 merge 而丢弃」那一步，它在
`_process_if_blocks`（def 20147）→ `_generate_block_statements_body`（def 41761）这一带；
`_if_generate_then_branch`（def 13997）已经把 then 臂的 Continue 正确带出，可作对照。

## 四、下一轮可直接用的判据草图（尚未验证，勿当结论）

同层表述：*当某臂（`then_blocks`／`else_blocks`）的尾块以「无条件跳到本区域的 merge」结束，
而该 merge 块自身也会被独立物化成一条 `Continue`（即存在另一条同样跳到 merge 的物理块被发射），
则该臂尾块的跳转不得被 merge 的吸收吞掉，臂内必须补一条 `Continue`。*
只消费块同一性、区域角色（`then_blocks`/`else_blocks`/`merge_block`）与后继关系。

先要测清的两件事：①该「merge 被两条物理块跳进」的事实在发射期从哪个结构读到
（`region.merge_block` 的入边？`block.successors`？）；②全语料有多少函数含此形状
（Round 38 的 8 行里 2 行属此族，另 6 行是 `diag r39diagB` 正在查的臂摊平族，两者判据不同层）。

## 五、门禁状态

本轮**未发货**：`core/` 零改动、无候选 spec，G0–G7 无对象。语料基线与 Round 38 §七 的
`logs/g4_head.all.jsonl`（402 行 / 0 error / 与索引 0 冲突）同源同字节，仍然有效，
Round 39 落地时可直接复用为 G4 的「改前」侧。

## 六、已把删除动作定位到一条在册抑制规则（下一手就改这里）

`_process_if_blocks`（def 20147）内的 **[R100 fix]「纯连接 continue 块的冗余抑制」**：
文档串在 `:20183-20188`，实现在 `:20842-20954`，判据形状是
「分支末块是 PURE_CONTINUE 回边块，且 `region.merge_block` 的末指令也是
`JUMP_BACKWARD → 当前 loop 的 header`（`_r100_mtgt is _r100_hdr`，`:20868-20875`）
⇒ 抑制该臂尾块的 `Continue`」。另有两处同族判定：`:15665-15674`（elif 体内版本）与
`:20876-20879`（`merge_block is header` 变体），以及一条**已存在的反向豁免**
`[R4-H 修复] 显式 continue 优先于 R100 冗余抑制`（`:20955-20970`，`_r4h_explicit_continue`）。

对照本形状：臂尾 @58 与 merge @60 是**两个不同的物理块**、各自跳回 loop header，
R100 认为「merge 已带这条回边」于是吞掉臂尾那条 —— 而产物源码里 merge 的 `continue`
确实单独发射了（链级那条），所以两条被并成一条。⇒ 候选判据应加在 R100 这一层：
*被抑制的臂尾回边不得与 merge 的回边合并，当且仅当 merge 块自身会被单独物化*
（同层事实：臂尾块 `is not` merge 块、merge 块在发射序里位于链之后）。
下一手先测 `_r4h_explicit_continue` 为何没兜住这一形状（它在 `:20970` 与
`_r100_suppress` 同判据里已经OR进来），再决定是扩这条豁免还是收紧 R100 本体。

## 七、§六 的 R100 线索**已被下一步实测否证**（勿再沿此路走）

把 `_process_if_blocks` 包一层，只观察「臂块列表里以 `JUMP_BACKWARD` 结尾」的调用：
整个 `ctl_two_cont` 反编译过程中**只有 1 次**命中，且是 then 臂 `[24, 34]`（它正确地发出了
`Continue`）。出问题的 else 臂 `[36, 48]` **不在命中之列**，因为按 `bytecode` 的分块，
@48 块以 `STORE_SUBSCR@54` 结束（** fall-through **），那条 `JUMP_BACKWARD@58` 属于
**另一个独立块 @58，而 @58 根本不在 `else_blocks` 里**。

⇒ 缺口不在发射侧的任何 continue 抑制（R100 / RC3 / R4-H 都到不了），而在**更上一层的块归属**：
臂尾那条回边块没有被认给这条臂，于是被当成链后公共汇合块发射了一次。
下一轮（或本轮下一手）要测的是：**块 @58 的 owner 是谁、由哪一步决定**
（`region_analyzer` 的 `else_blocks` / merge 归属，与 Round 37 落地的 R37-A 同一层），
而不是再在 `region_ast_generator.py` 的发射判据里找。

## 八、§六 遗留的那一手已经做完：块 @58 的 owner 与判据（候选 R39-A）

`logs/probe_owner.py`（在 `RegionAnalyzer.analyze` 外套壳，核内零改动）实测合成见证
`logs/src39.py :: ctl_two_cont`（16 块）的归属层：

| 块 | 终止符 | `block_to_region` | `block_roles` | 备注 |
|----|--------|-------------------|----------------|------|
| @34 | JUMP_BACKWARD→6 | TryExceptRegion@12 | PURE_CONTINUE | then 臂尾，**在** `then_blocks=[24,34]` 里 ⇒ 臂内发出 Continue |
| @58 | JUMP_BACKWARD→6 | **LoopRegion@6** | PURE_CONTINUE | elif 臂尾，**不在** `else_blocks=[36,48]` 里 |
| @60 | JUMP_BACKWARD→6 | TryExceptRegion@12 | LOOP_BACK_EDGE | = `LoopRegion.back_edge_block`（`back_edge_blocks=[60]`） |

即 §七 推断成立：臂尾回边块没有被认给那条臂，它被循环区域认领。
`logs/probe_trace.py`（包住 `_generate_region/_process_if_blocks/_if_generate_*`，记录每次
调用新吃掉的块与返回的语句树）给出发射序：`_process_if_blocks([36,48], IfRegion@12)` 返回
`[If(then=[Assign] orelse=[])]`（臂尾无终止符）→ 链外 `_process_if_blocks([58], None)` 返回
`[Continue]` → @60 被 try 区域吸收不出语句。产物因此只剩一条 `JUMP_BACKWARD`。

**目标源码形状已用编译器反证**（`logs/candcmp.py` + `logs/cand_c1.py`）：把那条 `continue`
放进臂内、链外不补，重编译后与原字节码**逐条 37/37 同偏移一致**（`strict (None,'ok',None)`）。
⇒ 缺的不是新语句，而是这条 `Continue` 的**归属位置**。

**语料同构性**：同一探针跑 `site-packages/IQCommon/strategy/wizard_quant_api.pyc ::
wizard_quant_check_limit`（28 块，链有 7 个臂）⇒ 前 6 个臂的 PURE_CONTINUE 块（@112/@152/…/@316）
都在各臂的 `then_blocks` 内并发出了 `Continue`；只有末臂 @330 的尾块 **@340 owner=LoopRegion@92、
role=PURE_CONTINUE**，而 @342 是 `back_edge_block/LOOP_BACK_EDGE` —— 与见证逐字同形。

**R39-A（同层判据，站点 `_process_if_blocks` 末尾）**：本臂最后一条已发射语句所属块 L
（终止符不含 `JUMP`）的**直落后继**（后继里排除 `start_offset` 更靠前的与以
`PUSH_EXC_INFO`/`WITH_EXCEPT_START` 开头的异常入口块）唯一确定为 T，且 T 只含一条
`JUMP_BACKWARD→当前循环 header`、T ∉ 本区域块集、T 未被认领、且 T **不是**该循环的
`back_edge_block`/`back_edge_blocks` ⇒ T 是源码级显式 `continue` 的唯一实体，认给本臂：
`stmts.append({'type':'Continue'})` 并标记 T 已生成（链外扫描不再重复发射）。

第一版把「直落后继」写成 `len(L.successors)==1` ⇒ G0 无效果。`logs/probe39g.py` 逐条评估
判据才看清：@330 在 try 保护区内，`successors=[340, 344]`（344 是 `PUSH_EXC_INFO` 异常入口），
唯一后继判据永远不成立。改成上面的异常入口排除后：

```
G0（电池 test_repros/round39_arm_tail_continue/，驱动器 logs/g0_head.txt / g0_r39a.txt）
  head  镜像：r39w_witness DEFECT 1  ctl_two_cont:seq_-1   r39c_controls CLEAN
  r39a  镜像：r39w_witness CLEAN 0                          r39c_controls CLEAN   （无 DEGRADED / 无 EXC）
```
5 支对照（`ctl_plain_elif` / `ctl_single_cont` / `ctl_elif_more_body` / `ctl_tail_cont` /
`ctl_while_tail`）改前改后皆 CLEAN，其中 `ctl_tail_cont` 正是「链外显式 continue == 循环自身
`back_edge_block`」的负对照，被 `T 不是 back_edge_block` 这一项挡住。




## 九、G4 否证 R39-A（过火 16 处）⇒ 实测分离出「私有 vs 合流」一项 ⇒ R39-B

**R39-A 的 G4（402 文件 A/B，`logs/g4_r39a_perfunc.txt`）**：

```
TALLY SAME=383 IMPROVED=0 REGRESSION=16 MOVED=3 ERR=0   files fully matched: a=375 b=366
```

但它并非无用 —— 靶确实被它修好了：`wizard_quant_api :: wizard_quant_check_limit`
`orig=91 decomp=90` ⇒ **匹配**（该文件计数不变只因同时碰坏了 `add_to_strategy_info 38/39`），
`klinedata :: get_all_real_daily_kline 188/187 → 188/188`（指令数复原，仍差 5 条）。
破的 16 处全是同一方向：**产物比原始多一条指令**（`orig=N decomp=N+1`）＝多补了一条
`continue`，重编译便多出一条 `JUMP_BACKWARD`。⇒ 形状判据只差「私有 vs 合流」这一条区分。

**实测判据（`logs/probe39h.py` → `logs/h_out.txt`：在 `_process_if_blocks` 每个返回点，
把候选臂尾直落后继逐条评估，含前驱集／merge／back_edge／owner，只测不改）**：

| 站点 | 臂尾 L | 候选 T | T 的前驱 | 是本区域 `merge_block` | 是循环 `back_edge_block` | 判别 |
|---|---|---|---|---|---|---|
| `wizard_quant_check_limit` 末臂 | @330 | @340 | **[@330]** | 否 | 否（@342 才是） | 应认 ⇒ 认了就修好 |
| `add_to_strategy_info` | @264 | @394 | [10, @264] | 否 | **是** | 不应认（R39-A 认了 ⇒ +1） |
| `add_to_strategy_info` | @92 | @222 | [84, @92] | **是** | 否 | 不应认（R39-A 认了 ⇒ +1） |
| `get_vip_user_info` | @832 | @854 | [562, @832] | **是** | 否 | 不应认（R39-A 认了 ⇒ +1） |

⇒ 分界不在「是否纯回边块」「是否属于本区域块集」，而在**归属的私有性**：源码里那条显式
`continue` 对应的回边块只有一个前驱、且那个前驱恰是本臂末块；前驱 ≥2 的后继（含本
`IfRegion` 的 `merge_block` 与循环自身的 `back_edge_block`）表示「臂自然落到链外合流点」，
那里源码本没有 `continue`。这正是原则 2（每块唯一归属）读在臂尾上的形态：私有的才归本臂。

**R39-B（同层判据，站点与 R39-A 同为 `_process_if_blocks` 末尾）**＝R39-A 的判据串 ＋
两项 `len(T.predecessors) == 1 and T.predecessors[0] is L`。规格 `logs/spec39b.json`
（由 `logs/mkspec39b.py` 派生，插入 53 行）。门禁结果与落地见 `OUTCOME.md`。

**纠正 §八 的一处记录错误**：§八 写「r39a 镜像 G0 ⇒ `r39w_witness CLEAN 0`」，而归档
`logs/g0_r39a.txt` 实为 `r39w_witness DEFECT 1  ctl_two_cont:seq_-1`，且
`test_repros/out_r39a/r39w_witness.py` 与 head 产物逐字节相同 ⇒ **R39-A 在合成见证上根本没触发**，
它只在语料上触发。（未再追这条差异的成因：加上私有性一项后见证与语料同时触发，见
`logs/g0_r39b.txt` 的 `cases=2 CLEAN=2 DEFECT=0`，说明该项正是见证所缺的一条。）
教训并入采纳前置检查：**G0 电池必须在同一镜像臂上重跑并留档，不能沿用另一次构建的结论**。
