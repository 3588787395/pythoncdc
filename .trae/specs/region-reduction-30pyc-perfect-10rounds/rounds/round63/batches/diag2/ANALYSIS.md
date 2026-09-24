# Round 63 batch 2 — ANALYSIS（K 线/行情族三 pyc：klinedata / real_quote / scheduler）

工作树基线：core/cfg/region_ast_generator.py sha256 前缀 b9778ee0130865d55888（HEAD=96a5f310）。
诊断脚本（全部只读、产物只落 diag2/）：
- `dlist.py <pyc> [filter]` —— 列出 code object 与指令数
- `dexc.py <pyc> <fn>` —— 原 pyc 的 dis + co_exceptiontable 转储（用 `dis._parse_exception_table`）
- `dside.py <pyc> <fn> <okpy> [lo hi]` —— 尺子口径（噪声过滤后）orig/decomp 逐指令并排
- `dshow.py <pyc> <fn> <okpy>` —— 尺子 true_diffs / jump_diffs 明细
- `drun.py <arm> <pyc>` —— 用指定臂核心反编译一个 pyc 并打印
- `dreg.py <pyc> <fn>` —— 该函数的 CFG 块 / 区域（含 merge_block 等字段）/ 产物
- `dtrace2.py <pyc> <fn> <arm>` —— monkeypatch `_find_nearest_common_post_dominator` /
  `_compute_merge_from_jump_targets` / `_build_elif_region` 等，打印 merge 求解过程
  （只 patch 内存中的类，不写仓库）

---

## 1. scheduler.pyc :: Scheduler.get_checked_time（orig=106 decomp=106 jumpdiff=0 truediff=43）

**实测（dside 并排，尺子口径）**：差异是一整段错位，区间 `[18..60]`：

```
orig  18..24  LOAD_GLOBAL divmod ... STORE_FAST minute     <- `hour, minute = divmod(...)`
orig  25      JUMP_FORWARD
orig  26..60  PUSH_EXC_INFO ... handler ... POP_EXCEPT JUMP_FORWARD RERAISE COPY POP_EXCEPT RERAISE
decomp 18     JUMP_FORWARD
decomp 19..53 PUSH_EXC_INFO ... handler ...（同一批指令）
decomp 54..60 LOAD_GLOBAL divmod ... STORE_FAST minute     <- 同一批，位置被排到 handler 之后
```

`co_exceptiontable` 原始条目（`dexc.py` 转储）：
`(6,130,170,0)`、`(130,170,436,0)`、`(170,378,384,1)`、`(378,382,436,0)`、
`(382,384,384,1)`、`(384,434,436,0)`、`(436,470,640,1)`、`(470,620,630,1)`、`(630,640,640,1)`

**探针实测（probe_gct.py / probe_harness.py，本机 CPython 3.11.7）**：
把候选源码编成字节码，与原始序列比对，三个形状都被否掉：

| 探针源码形状 | 指令序列 | 异常表 |
| --- | --- | --- |
| A `try{...}except{...}` 之后接 `divmod`（= 当前产物的形状） | 与原始**不同**：`divmod` 落在 handler 之后 | 条目集与原始**同构**（9 条、depth 一致），只是偏移平移 38 |
| B `divmod` 写在内层 try 体内 | 与原始**相同** | **不同**：内层 try 覆盖 `(6,168,170)`，divmod 被内层 handler 保护 |
| C `try/except/else: pass` | 与 A 同（不等价于原始） | 与 A 同 |

结论：**原始 .pyc 的语义与 A 完全一致，但块线性化是「body → 臂后续块 → 跳 handler → handler」**，
即 CPython 3.11 `_PyCompile_OptimizeCfg` 的落块结果；语义等价的 B 会给出正确序列却给出
**不同的异常表**（divmod 被内层 except 捕获，语义改变）。
=> 该函数在「保持语义正确」的前提下无法用任何源码形状复现原始布局。
**判定：本函数为 CPython 布局产物（layout artifact），非区域归约缺陷，本轮不可攻。**
（这也解释了它为何长期停在 truediff=43 / jumpdiff=0。）

---

## 2. scheduler.pyc :: Scheduler.run_interval_trade.is_run_interval_time_now（225/201，deficit −24）

**真实缺陷：臂尾整条语句被丢弃（代码丢失），不是布局问题。**

原始 dis（`dexc.py`）关键片段：
```
line 387  198 LOAD_FAST interval_timer_ranges / 200 POP_JUMP_FORWARD_IF_TRUE -> 514   <- elif 测试
line 388  202 NOP                        <- 内层 try
line 389  204..268  current_time = int(time.strftime('%H%M%S'))
        270 JUMP_FORWARD -> 410
line 390  272 PUSH_EXC_INFO ... except BaseException
line 391  292 LOAD_CONST 0 / STORE_FAST current_time
line 392  296..396 system_log.error(...)
        398 POP_EXCEPT / 400 JUMP_FORWARD -> 410 / 402 RERAISE / 404 COPY ...
line 394  410 LOAD_GLOBAL RI_STOCK_AM_OPEN ... 512 RETURN_VALUE
```
line 394 就是 `return (RI_STOCK_AM_OPEN < current_time < RI_STOCK_AM_CLOSE) or
(RI_STOCK_PM_OPEN < current_time < RI_STOCK_PM_CLOSE)`，共 24 条尺子口径指令 ——
**与 deficit=−24 完全对应**。当前产物（build_landed/IQEngine__utils__schedulerOK.py L276-281）
的 elif 臂在 try/except 之后就结束了，这条 return 根本不存在。

### 最小合成复现（已落盘，仓库内）
`F:/Downloads/pythoncdc-main/test_repros/round63_b2/probe_r63b2_cases.py`（c1..c8）与
`probe_r63b2_cases2.py`（d1..d8）；同名 `.pyc` 已用本机 3.11.7 编好。
跑法：
```
cd D:/Temp/opencode/r63gate/diag2
python -X utf8 drun.py landed F:/Downloads/pythoncdc-main/test_repros/round63_b2/probe_r63b2_cases2.pyc
python -X utf8 dreg.py   F:/Downloads/pythoncdc-main/test_repros/round63_b2/probe_r63b2_cases2.pyc d1_elif_try
python -X utf8 dtrace2.py F:/Downloads/pythoncdc-main/test_repros/round63_b2/probe_r63b2_cases2.pyc d1_elif_try <arm>
```
（`repro_r63b2_tail_cmp_return.py/.pyc` 是贴近真实函数的一条式复现。）

### 探针矩阵（landed 臂实测，逐条看产物里那条 return 还在不在）
| 用例 | 形状 | 结果 |
| --- | --- | --- |
| c1 | elif 臂 + try + `return cur` | 正常 |
| c2 | elif 臂 + try + `return A < cur < B`（单链式，无 boolop） | 正常 |
| c3 | elif 臂 + try + `return A < cur or C < D`（boolop，无链式） | 正常 |
| d1 | elif 臂 + try + `return A<cur<B or C<cur<D` | **丢弃** |
| d4 | 函数顶层 try + `return A<cur<B or C<cur<D` | 正常 |
| d5 | elif 臂 + try + `return A or B` | 正常 |
| d6 | elif 臂 + try + `return A<cur<B and C<cur<D` | **丢弃** |
| d7 | elif 臂 + try + `r = A<cur<B or C<cur<D; return r` | **赋值整条丢弃**（产物只剩 `return r`）|
| d8 | elif 臂 + try + `return A<cur<B or C<D` | **丢弃** |
| d2 | elif 臂 + 无 try + `return A<cur<B or C<cur<D` | 变形：return 被抬到 if/elif 链之外 |

=> **生效条件 = 「链式比较参与 BoolOp 的表达式语句」位于某个条件臂内**；
try/except 只影响变形方式（d2 说明它不是必要条件），顶层则正常（d4）。
d7 尤其说明问题：不是 return 的语法问题，而是**该表达式语句所在的块被区域接管后没有发射**。

### 区域侧实测（dreg.py，d1）
```
B@190 succs=[206,216]  A<cur 比较 + JUMP_IF_FALSE_OR_POP
B@206 succs=[220]      cur<B + JUMP_FORWARD
B@216 succs=[220]      SWAP POP_TOP
B@220 succs=[252,222]  JUMP_IF_TRUE_OR_POP                <- BoolOp 'or' 的入口
B@222 succs=[238,248]  第二条链式
B@252 succs=[]         RETURN_VALUE                       <- BoolOp 的 merge_block
regions:
  IfRegion entry=190 merge=220 (chained_compare_blocks=[206])
  IfRegion entry=222 merge=252 (chained_compare_blocks=[238])
  BoolOpRegion entry=220 merge=252 value_target=None
  IfRegion entry=0 (IF_ELIF_CHAIN) merge=252  <-- 可疑：链的汇合点落在臂内部
```

### 已证伪 / 已观察但无效
**假设 H1（`_build_elif_region` 的单臂 merge 误判）**：`region_analyzer.py` L19621-19636，
当「各臂末端后继里只有一臂非空」时直接把该臂的后继集当 merge 候选；d1 里该后继正是臂内的
BoolOp merge 块 252，于是外层 elif 链 `merge_block=252`。
按区域归约原则 2（每块唯一归属，链的 merge 必须在所有臂之外）收窄：候选中剔除
`block ∪ then_blocks ∪ conditions ∪ 各 body ∪ final_else`。

spec：`specs/FALSIFIED_cand_chainmerge_armowned.json`（改 `core/cfg/region_analyzer.py`）。
实测 dtrace2：`IF entry=0 merge=252 -> merge=None`，**区域层确实被修正**；
但 `drun.py c1` 产物里 d1 的 return **仍然丢失** ——
**H1 被见证测量证伪：merge 归属不是这条语句丢失的生效机制。**（未落地。）

三目标 A/B 实测（`dump/landed.jsonl` vs `dump/c1.jsonl`，`cmp_arms.py`）：
```
files=3 errors=0  landed: matched=123 clean=0  ->  c1: matched=123 clean=0
TALLY  landed->c1 : REGRESSION=0 IMPROVED=0 MOVED=0 SAME=3
```
即该候选在三支 pyc 上**字节级完全 inert**（逐函数元组纹丝不动），符合红线里
「R62 两支候选死在自己见证上」的形态，已改名为 FALSIFIED_ 前缀、不提交。

### 修正后的机制假设（指向发射侧，供下一批）
d2（elif 臂内**无** try）把 `return 链式 or 链式` 整个抬到 if/elif 链**之外**；
d1/d6/d8 直接丢失；d7（`r = 链式or链式` 后 `return r`）丢失的是**赋值**整条；
d4/d5（顶层 / 非链式 boolop）全部正常。
⇒ 丢失的不是 Return 语法，而是「含链式比较的 BoolOp 表达式语句」这个**语句宿主块**：
`_if_generate_full_elif_chain` 逐臂取语句时，把归属嵌套表达式子区域
（BoolOpRegion entry=220 / merge=252；链式 IfRegion 190→220、222→252）的臂尾块
截断到臂外，随后这些块被子区域标为已生成却从未发射（或在父层发射）。
下一步应比对**臂内发射路径 vs 顶层序列路径（d4 走通的那条）**对
「子区域 merge_block 同时是本条语句落点块」的处理差异，改在
`core/cfg/region_ast_generator.py`，而不是 `region_analyzer.py` 的 merge 求解。

---

## 3. 下一步判据方向（未做完的部分）
1. 丢失发生在**发射侧**：`region_ast_generator._if_generate_full_elif_chain` 逐臂生成语句时，
   臂内「表达式区域（BoolOpRegion entry=220，merge=252）+ 末端 RETURN_VALUE 块」没有被
   折算成一条 `Return`；顶层序列路径（d4 走的那条）能折对。应比较两条路径对
   「子区域 merge_block 同时是本语句的落点块」的处理差异，而不是继续在 analyzer 侧加判据。
2. `BoolOpRegion.value_target=None` 值得查：d4（正确）与 d1（丢失）的 value_target 是否不同；
   若臂内场景下表达式没有宿主（既不是赋值目标也不是 return 值），就会被丢掉。
3. klinedata.pyc 的 `get_all_real_daily_kline`/`get_multiminute_his_data`（deficit −1、
   jumpdiff 3）与 real_quote.pyc 五支（deficit −2/−1/+1/−1/+2，truediff 100~424）本轮未展开，
   需先按 §1 方法判定是「布局产物」还是「真实丢失」，再决定是否攻。
