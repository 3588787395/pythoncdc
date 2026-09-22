# Round 26 候选 R26-A：出环臂的裸 `Break` 不得吞掉该块自己的前导语句

## 一、缺陷与根因（实测，非推断）

锚点 `IQEngine/plugins/plugin_fly_data/__init__.pyc :: ApiMethodPlugin._on_before_trading_start_trading_thread`
`orig=66 decomp=62`（严格尺 −4；官方尺读成 62/62 等长、`jump_diffs=2 true_diffs=19`，即 R97 裁剪把删掉的
4 条对齐掉了对齐不掉的错觉）。原始 L238-242（`logs/dump_thread.txt`，带字节偏移）：

```
o38 LOAD_FAST now | o41 COMPARE_OP >= | o42 POP_JUMP_FORWARD_IF_FALSE ->328
o43 LOAD_FAST order | o44 LOAD_METHOD commit | o45 CALL 0 | o46 POP_TOP      L239  ┐ 同一个基本块 B286
o47 JUMP_FORWARD ->404                                                        L240  ┘ 404 = 外层 while 重测块 ⇒ break
o48 LOAD_GLOBAL time … time.sleep(min(order_time - now, 30))  (328..402)     L242
```
⇒ 真实源码 `if now >= order.order_time: order.commit(); break`。产物写成
`if now >= order.order_time: break` —— **臂块自身的前导语句被整段丢弃**。

现场定位法（不是读代码猜的）：`region_ast_generator.py` 里有 18 处赋裸 `[{'type': 'Break'}]`，
逐处插 stderr 身份戳（行号 + 所在函数 + 局部变量里所有块的起始偏移）跑镜像核，
命中的唯一站点是 **L10084 `_loop_build_if_with_exit_branches`，blocks=[286, 328]**
（`D:/Temp/r26self/probe_break26.py`、`probe_break_out.txt`）。

同层不对称（判据的来源，全部是同层结构事实）：紧挨其下的 `_block_succ_return` 分支对 return 臂
**先看块角色**（`BlockRole.RETURN/RETURN_NONE` ⇒ 发射 return AST；否则 `_generate_block_statements`），
而 break 臂没有这一层角色分派；同一形状在 L8965-8974 的 else 侧**已经落地过**
（`_jt_user_stmts + [{'type': 'Break'}]`）。⇒ R26-A 就是把已有判据补到 break 侧。

## 二、判据（唯一一条，单文件单站点）

`core/cfg/region_ast_generator.py` L10084：出环臂块 `_then_succ` 属于 `_block_succ_break` 时，
只有当它的块角色是 `BlockRole.PURE_BREAK`（该块除终止跳转外不带自己的语句）才发射裸 `Break`；
否则先 `_generate_block_statements(_then_succ)`，滤掉其中已生成的 `Break/Continue`，再接 `Break`，
并把该块登记进 `generated_blocks` / `generated_offsets`（与 return 分支同构）。
只读：块角色、块自身指令、后继集合成员关系。不读偏移量比较、不读函数名、无跨层启发。

镜像补丁规格：`D:/Temp/r26land26/r26a.py`（`ANCHOR` 唯一性断言 + CRLF 保持 + BOM 保持断言）。

## 三、门禁（严格串行，逐条实测）

| 门 | 判据 | 实测 |
|---|---|---|
| G0 非空 | 语料外最小复现能在落地核上复现缺陷 | `repro/r26a_b2.py :: drain` 落地核 `3/4`，`drain 35 vs 31`（−4，同形） |
| G1 FIX 翻转 | 复现与锚点在候选核上翻转 | 复现 `3/4 → 4/4`；锚点文件 `plugin_fly_data/__init__.pyc 19/20 → 20/20`（`mism=[]`） |
| G2 前轮电池 | 92 个 `test_repros/**.pyc` 产物逐字节不变 | `SAME=92 IMPROVED=0 BROKEN=0 MOVED=0 ERR=0`（`logs/batt92_head_vs_cand.txt`） |
| G3 无 OK→FAIL | 全量 A/B | `REGRESSION=0 ERR=0` |
| G4 全量 A/B（发货判据） | 402 文件双臂 | `SAME=400 IMPROVED=1 MOVED=1 REGRESSION=0 ERR=0`；整文件全匹配数 366 → 367（`logs/ab402_head_vs_cand.txt`） |

G4 的唯一 MOVED：`plugin_system_event_source/default_event_source.pyc :: events`
`decomp 486 → 491`（orig=510，长度缺口 24 → 19 收敛），两侧仍 mismatch、`matched_functions` 未变 ⇒ 非回归，
记为本轮残余（该函数仍有独立的次序/布局缺陷，#39/#41 族）。

## 四、与承重件/既往否证的关系

* 不碰 `_if_arm_is_sink`（`project-r16-lead-sink-collapse` 的 5 个反例来源），不碰跳转发射
  （Round 24 线 A 否证形状），不碰 `region_analyzer.py` 的 `final_else` 认领（R25-A 已落，本轮不同站点）。
* `logs/insp_canresume.txt`（代理侧）与本轮 B1 同函数：B1 的「嵌套 elif 展平」形状**不由 R26-A 覆盖**，
  仍留作移交项。

## 五、移交项（本轮不解）

* B1 `can_resume_strategy` −32：发射现场未定，且 L11145-11147 守卫已实测与本缺陷无关
  （`lineB-bulk-loss.md` 的否证段）。
* B3 / #39 异常尾声按出口复制（`save_testds_to_json` −4）。
* `DefaultMatcher.match` −26 的 259 条大块换位。
* `quotation.pyc` 自 R25 起 `ok 143/143`，本轮起是承重锚点：落地后必须仍 143/143。
