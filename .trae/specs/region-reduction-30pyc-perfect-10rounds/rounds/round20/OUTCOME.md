# Round 20 结果（OUTCOME）

一条根因线（R20-A，两层各一处），按门禁顺序完成：单点修到完全 OK → quotation.pyc 单验 →
全量产物门 → 全量逐函数 A/B 归因 → 电池 → 索引回填 → 提交 push。
设计稿 `arm-design.md`，验证记录 `fixes.md`，逐条两世界实测
`test_repros/round20_rollover/ANALYSIS.md`。

## 一、解决了什么

`for x in …: if c: break / else: …` 这类形状里，`break` 在 CPython 3.11 下编成一个
**只含 `POP_TOP`（弹循环迭代器）＋ 一条无条件前向跳转** 的块。两处缺陷缺一不可：

1. **分析层** `core/cfg/region_analyzer.py::_collect_natural_loop_body`（6172-6175）的
   `[R102 for-else fix]` break-target 判别只有两条判据：目标 ∈ `_exit_reachable`、
   目标 ∉ `_fwd_candidates`。而 6140 起构造 `_fwd_candidates` 的 BFS **会穿过 break 自身的
   无条件跳转**，把 break 落点登记成「循环内前向块」⇒ `_break_targets=∅` ⇒
   6258 的 `_return_reachable`（以循环体内 RETURN 为种子）把循环后的全部块
   （实测 302/336/396/428/556）吞进 `body_blocks`、`has_break=False`。
   修法：追加**第三条同层次结构析取项** `_r20_is_break_stub_block(_bb)`
   （去噪后 = ≥1 条 `POP_TOP` ＋ 恰好一条无条件前向跳转；`_bb` 是既有循环里的块变量，
   不新增遍历维度）。只登记 break 出口，归给既有的「以 `_break_targets` 为屏障重建」路径。
2. **生成层** `core/cfg/region_ast_generator.py::_if_generate_normal` 的 W15-C
   「then-独占 merge 块并入 then 臂」（16988-17004）在**臂尾已是终止语句**时仍无条件
   `then_stmts = _kept + _merge_then_stmts`。同一函数 16934-16942（臂内终止截断）与
   `_process_if_blocks:20541`（终止后不再发射块）早已用 `('Break','Continue','Return','Raise')`
   这条同层判据，三处同层同判据只有 16988 漏用 ⇒ 按「同层同结构必同结论 ＋ 优先接线既有判据」
   补第③条件，**不新建谓词**。少了这一半，只修分析器会把循环后代码缩进在 `break` 之后 ⇒
   CPython 3.11 死代码消除 ⇒ 119 塌到 50（实测候选 `c_a1`）。

代码净改动：`region_analyzer.py` `+46/−3`（判据代码 `+19/−3`，其余中文 `[R20-A 修复]` 注释）、
`region_ast_generator.py` `+23/−1`（判据代码 `+5/−1`）。不看名字、不看常量、不看原始字节码偏移；
四条区域归约原则（内层→外层次序、每块唯一归属、嵌套区域在父层为单一抽象节点、父层只引用子区域
入口块）逐条核对未被触碰（`arm-design.md` §四）。

`POP_TOP` 是本判据的必需组成，不得简化掉：放宽成「恰好一条无条件前向跳转」的候选 `f1`
两孪生也过（119/127），但全量 A/B `broken=1`——`IQEngine/plugins/plugin_system_finance/slippage.pyc`
的 `create_new_price.check_and_return` 19→18，其块 124 = `[JUMP_FORWARD 130]` 是链式比较的
out-of-line 臂桩（无迭代器可弹、语义上也无循环可退）。`f3` 收窄后该处保持原样、全量 `broken=0`。

被翻正的函数（`fixes.md` §二）：

| pyc | 函数 | 本轮前 → 落地后 |
|---|---|---|
| `site-packages/IQEngine/utils/logger/handlers.pyc` | `RotatingFileHandler.perform_rollover` | 严格 16/17 → **17/17**（127/127），条目 `partial 0.928…` → `ok 1.0`，`single` 报 `ok 14/14 100.00%` |
| `site-packages/IQCommon/logger/handlers.pyc` | `RotatingFileHandler.perform_rollover` | 严格 28/30 → **29/30**（119/119），条目 `partial 0.944…` → `ok 1.0`，`single` 报 `ok 18/18 100.00%`；同文件 `TWHThreadController._target` 仍 `orig=192 decomp=190`（上一棒已登记的独立残差，本轮按 mandate 原样保留） |

全语料只有这两个条目变好（镜像核全量 A/B：improved=2、broken=0、signature-only=0，
402/402 记录、0 异常），对应产物改动只有那两份 `handlersOK.py`。

## 二、门禁与归因

1. 单点（修到完全 OK）：两孪生 `single` 各报 `ok 14/14 100.00%`、`ok 18/18 100.00%`；
   严格尺子 17/17 与 29/30（残差只剩 `_target`，逐字未动）。落地核与已实测候选 `f3` 做过
   **剥注释后逐行等价核对**（`code-only diff lines: 0` ×2）⇒ 候选上的全部实测对本落地核有效。
2. quotation.pyc：`single` 实测 `partial 142/143 99.30%`、唯一缺陷
   `change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377`，与 Round 19
   记录逐字相同；产物 `quotationOK.py` sha256 前后相同（`c0d3c312…`）、`git status` 干净
   ⇒ 本补丁对该文件零副作用。
3. 全量产物门（402 条目分 8 片，基线 = 落地前磁盘产物逐函数严格比对）＝
   CLEAN 336 + UNCHANGED 57 + WORSENED(rolled back) 8 + REGRESSION(rolled back) 1。
   9 项异常与 Round 19 的 9 项**逐文件、逐数值相同**，无第 10 项 ⇒ 本轮零新增回退、回滚全部生效；
   落地后 `git status` 只有 5 个受控路径（2 核 ＋ 索引 ＋ 两孪生产物）。
   另用不受尺子「每文件 12 条」打印上限影响的产物层名集全量复核：402 文件里名集变化 = 2，
   且两处 `new=[]`（无任何新出现的缺陷函数名）。
4. 全量逐函数 A/B 归因（与门 3 分开、零仓库写入）：`git archive 5c63ce6b` 重建的 pre-landing
   核镜像与工作区**逐字节相同**（sha256 前 16 位 `255d53d3c8707a07` / `faf70dafbce09acf`），
   cand 镜像只差本补丁 ⇒ `improved=2（恰为两孪生） broken=0 signature-only=0`，
   `sum(n_ok) 5985 → 5987`。
5. 电池：`test_repros/round20_rollover/`（26 项，测试工程师交付）`--strict` 退出码 0、
   `MISMATCH=7 MATCH=19 ERROR=0 UNEXPECTED=0`；`EXPECT` 整表按落地后实测重写
   （11 个锚点→`SENTINEL`、7 项同族别因→`MISMATCH`、8 项守卫/负对照→`MATCH`、`UNCONFIRMED` 为空）。
   落地前核镜像同批实测 `MISMATCH=18 MATCH=8`，与被改写前的 HEAD 表逐条相同。
   既有 10 套（round13/13b/14/14_join/15_arm/16_arm/16_sink/17_arm/18_arm/19_cont）
   在新核上 `--strict` 全部退出码 0、UNEXPECTED=0、ERROR=0，与 Round 19 收尾时逐套相同，
   唯一变化是 `round13::r13_20_for_else_break_lost` 由「复现缺陷」变「已修」（改标 `SENTINEL`）
   —— 同一族缺陷 Round 13 就记过形状。

## 三、索引与对外序列

`pyc_index.json` 只有 2 个条目变动（上述两孪生，全部由 `single` 工具自己写回；
402 条目、每条 `function_count` 一律不变、Σ=5746）。

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
本轮开始前（HEAD 5c63ce6b）：total_pyc 402  ok_pyc 361  total_functions 5746  matched_functions 5630  97.98%
本轮收尾                  ：total_pyc 402  ok_pyc 363  total_functions 5746  matched_functions 5632  98.02%
```

## 四、代价与残留

1. **9 文件产物/核漂移族已彻底归因（本轮收口，不再每轮重猜）**： culprit 是单个提交
   `f89b85f2`（`Round 13: 修 return 被降级为 break（区域归约边界），回退 A2 前缀判据`），
   其内有 **三处独立回退判据 J1/J2/J3**（J1 = `region_analyzer.py`「if-arm 是 sink ⇒ 抹掉 else 臂」，
   负责 15 个漂移函数里的 13 个；J2 = `region_ast_generator.py` `_discover_predicate_and_chain*`
   一族，负责 `market_time.MarketTime.trade_is_open`；J3 = 生成器 `[A4/V-M]` hunk，
   负责 `flytools.whitelist_filter`）。Round 14-19 全部排除（没有一个移动过这 15 个函数）。
   证据与逐候选实测见 `D:/Temp/drift/REPORT.md`。
   **整体回退不可发货**：`nomerge`（删 J1 的 10 行）实测 `improved=8 broken=5 signature-only=5`、
   `j1j3` 实测 `improved=8 broken=5`（净 +7 但破 5 个文件），⇒ J1 是 load-bearing。
   这正是每轮产物门都出现同样 9 项 WORSENED/REGRESSION 回滚的原因：闸门每轮都在保护磁盘产物，
   而不是本轮补丁造成的回退。**回退改造（给 J1 找一条能同时清掉 5 个 BROKEN 反例的同层判据、
   J2 的非破坏性中和）留下一轮，本轮按 mandate 未动。**
2. `round20_rollover` 残留 7 项同族别因仍 `MISMATCH`：`07`(32→7) `11`(43→36)
   `17`(47→39，本轮从 47→40 略改善但量级未变) `18`(seq_diff #17) `21`(23→19) `23`(29→26)
   `26`(48→46)。共同点：break 出口块不止一个、或出口块落在 `except`/`while` 等别的区域种类里、
   或链式比较与循环出口共享 merge。全量 A/B 证明这些形状在语料里未被本修复触碰（base 也 MISMATCH
   ⇒ 非回归），属后续轮次。
3. `_if_generate_normal` elif 链返回路径 ~17134（落地后 17156）还有一处同形状 splice，本轮未守：
   两孪生＋26 项电池＋402 条目 A/B 都不经过它。按「不为不重现的形状预先加守卫」处理，
   下一轮以「该处能否构造出翻正例」决定。
4. `TWHThreadController._target`（`orig=192 decomp=190`，孪生 A 同文件）＝ 上一棒已登记的独立残差，
   本轮逐字未动（实测复核）。
5. quotation 残留 2：`change_his_to_forward` seq_len +1、`get_trend` 跳转终点不同。
6. 本轮 26 项电池里 `UNCONFIRMED` 为空（不像 Round 19 有 7 项构造不出）——代价是每个形状都要
   在两世界上实测出确定结论，`--core <落地前镜像>` 复跑是必要的双向自检。
7. `strategy.pyc`、`calexrights_func` 孪生、`trade_live_broker` 26、`r16a_05`、
   `r15a_08`/`r15a_09`、`r17a_25`、`r18a_05`、`round19_cont` 残留 4 锚点、
   T1/T2 then 臂收集顺序、SubTask 13.4、Task 5 遗留（`decrypt_database_url` +29、`cgroup` +2/+1）。

## 五、提交物

核：`core/cfg/region_analyzer.py`（+46/−3，判据代码 +19/−3）、
`core/cfg/region_ast_generator.py`（+23/−1，判据代码 +5/−1）。
产物：`site-packages/IQCommon/logger/handlersOK.py`（+11/−10）、
`site-packages/IQEngine/utils/logger/handlersOK.py`（+12/−11）。
记录：`pyc_index.json`（2 条目）、`test_repros/round20_rollover/`（26 复现 + `run_all.py`
＋ EXPECT 整表按落地后实测重写 + `ANALYSIS.md`）、`test_repros/round13/run_all.py`
（`r13_20` 改标 SENTINEL）、`rounds/round20/{arm-design.md,fixes.md,OUTCOME.md}`、
`tasks.md`（Task 20）。
