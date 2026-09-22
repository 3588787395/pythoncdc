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
