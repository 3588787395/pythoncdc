# Round 21 结果（OUTCOME）

一条根因线（R21-A，一条规则、两个接线点、同一文件），按门禁顺序完成：单点修到完全 OK →
quotation.pyc 单验 → 全量产物门 → 全量逐函数 A/B 归因 → 电池 → 索引回填 → 提交 push。
设计稿 `arm-design.md`，验证记录 `fixes.md`，逐条两世界实测
`test_repros/round21_oauth2/ANALYSIS.md`。

## 一、解决了什么

`site-packages/fly/oauthenticator/oauth2.pyc` 的两份同形孪生 `post` 各差 **9 条**，且实测是
**ABSENT（整块消失）而非 relocated**。丢的是「一个完整的 `yield self.spawn_single_user(user)`
语句 ＋ 一对 `LOAD_CONST None; RETURN_VALUE`」。同一形状（协程语句前缀 ＋ 条件跳转结尾）
在 then 臂与 else 臂各出现一次，按「同层同结构必同结论」必须同判决，基线核两处都判错，
错在**同一条 body 判据的两个缺半**上：

1. **站点 A** `core/cfg/region_analyzer.py::_detect_boolop_conditional_chain`（落地前 24236-24243）
   的非首成员块守卫只查 `STORE_*`，漏掉了**同一函数**起始块判据 `_sb_has_body`
   （落地前 24056-24078）已有的另一半「`CALL` … `POP_TOP` ⇒ 块内含值丢弃语句」⇒
   then 臂首块被并成 BoolOp `and` 操作数 → 产物 `if status is not None and cgroupmode == '1':`，
   嵌套 if 的 else 臂 `return` 整块消失（−2）。
2. **站点 B** `_build_elif_region` 内嵌 `_check_elif_chain`（落地前 18274-18284）**已有**
   `CALL`+`POP_TOP` 判据，但其过滤表 `('RESUME','NOP','CACHE','EXTENDED_ARG')` 漏了
   CPython 3.11 协程语句插在 `CALL` 与 `POP_TOP` 之间的 `YIELD_VALUE` ⇒ else 臂首块被当成
   纯 elif 条件块吸进链，前缀语句退到链之后、链上三支全部 return ⇒ 死代码消除整块删除（−7）。

−2 ＋ −7 = −9，与指令级删除窗口逐条吻合。修法是把**同一条同层结构谓词**在两处各补全一次
（间隙只容忍 `YIELD_VALUE`/`RESUME`，遇其他指令立即停止），零新判据、不看函数名/字符串常量/
原始字节码偏移、不跨区域跨层次。四条区域归约原则逐条复核未被触碰，且两处都是**减少**块的
多重认领（`arm-design.md` §四）。

代码净改动：`region_analyzer.py` `+74/−2`（判据代码净增 29 行：站点 A 22、站点 B 7；
其余 43 行是中文 `[R21-A 修复]` 注释），落地核与已实测候选 `c6` 做过**判据代码逐行 assert 等价**。

| pyc | 函数 | 本轮前 → 落地后 |
|---|---|---|
| `site-packages/fly/oauthenticator/oauth2.pyc` | `HSIDOAuthCallbackHandler.post` | 严格 `orig=175 decomp=166` → **逐条一致** |
| `site-packages/fly/oauthenticator/oauth2.pyc` | `OAuthCallbackHandler.post` | 严格 `orig=190 decomp=181` → **逐条一致** |

该文件严格尺子 `DEFECT 10/12` → **`OK 12/12`**，官方 `single` `partial 10/11` → **`ok 11/11 100.00%`**，
产物 `oauth2OK.py` 154 → 162 行（只有那两处 hunk）。全语料逐函数 A/B 只有这一个条目变好
（improved=1、broken=0，402/402 记录、两侧 0 异常）。

## 二、门禁与归因

1. 单点（修到完全 OK）：`single` 自打印 `decompile_status: ok / 11 / 11 / 100.00% /
   missing_in_decomp: [] / extra_in_decomp: []`；严格尺子 `OK 12/12`、无任何 DEFECT 行；
   产物 `ast.parse` 通过、逐行 diff 只有被恢复的 `yield`/`return`（`fixes.md` §二）。
2. quotation.pyc：`single` 实测 `partial 142/143 99.30%`、唯一缺陷
   `change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377`，与 Round 20 记录
   **逐字相同**；产物 `quotationOK.py` sha256 前后相同（`c0d3c312…`）、`git status` 干净
   ⇒ 本补丁对该文件零副作用。
3. 全量产物门（402 条目分 8 片，基线 = 落地前磁盘产物逐函数严格比对，打补丁之前先跑）＝
   CLEAN 337 + UNCHANGED 56 + WORSENED(rolled back) 8 + REGRESSION(rolled back) 1。
   9 项异常与 Round 20 的 9 项**逐文件、逐数值相同**，无第 10 项 ⇒ 本轮零新增回退、回滚全部生效。
   与 Round 20 相比净变化 1 项（UNCHANGED→CLEAN）＝本轮目标文件。落地后 `git status` 只有
   3 个受控路径（核 ＋ 索引 ＋ 该产物）。
   **例外（本轮新发现，`fixes.md` §九）**：`realtime_event_sourceOK.py` 被产物门按计数裁决
   放行（`UNCHANGED`）后人工保全回落地前版本——详见 §四第 1 条。
4. 全量逐函数 A/B 归因（与门 3 分开、零仓库写入）：按 mandate 在**真正的落地基** `15a8de06`
   上重跑（诊断的 402 全量是在 `5c63ce6b` 上做的）——`git archive 15a8de06` 镜像与落地前工作区
   逐字节相同（sha256 前 16 位 `eb378bd197e2efba`），cand 镜像只差本补丁（`8529b7e8e36dc336`）
   ⇒ `improved=1（恰为目标 pyc） broken=0 signature-only=1`，`sum(n_ok) 5987 → 5989`。
5. 电池：`test_repros/round21_oauth2/`（16 项，测试工程师交付）`--strict` 退出码 0、
   `MISMATCH=3 MATCH=13 ERROR=0 UNEXPECTED=0`，逐项与 ANALYSIS §7 候选列相同；
   其 `EXPECT` 表交付时**已是**落地后实测真值（01/03/08/10/16→`SENTINEL`、12/13/14→`MISMATCH`、
   8 项负对照→`MATCH`、`UNCONFIRMED` 为空），本步无需改写。
   既有 11 套（round13/13b/14/14_join/15_arm/16_arm/16_sink/17_arm/18_arm/19_cont/20_rollover）
   在落地核上 `--strict` **全部退出码 0、UNEXPECTED=0、ERROR=0**，逐套计数与 Round 20 收尾时
   **逐字相同** ⇒ 本轮既没有既有锚点被顺带修好（无需改标 `SENTINEL`），也没有任何一项被改坏。

## 三、索引与对外序列

`pyc_index.json` 只有 1 个条目变动（`fly/oauthenticator/oauth2.pyc`，由 `single` 自己写回
`partial 0.909…/matched 10` → `ok 1.0/matched 11`；402 条目、每条 `function_count` 一律不变、
Σ=5746，脚本 assert 通过；added=0 / removed=0）。

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
本轮开始前（HEAD 15a8de06 的索引）：total_pyc 402  verified_pyc 402  ok_pyc 363  total_functions 5746  matched_functions 5632  98.02%
本轮收尾                        ：total_pyc 402  verified_pyc 402  ok_pyc 364  total_functions 5746  matched_functions 5633  98.03%
```

对外序列只 +1（不是 +2）：官方尺子在落地前只把两个 `post` 里的一个记成 mismatch
（条目里 `mismatch_count: 1`），另一个只有严格尺子抓得到 ⇒ 官方 `matched_functions` 只回补 1。
任务书预期的 `5634 / 98.05%` 未达成，门下限 `402/5746/5632/98.02%` 满足（`fixes.md` §八）。

## 四、代价与残留

1. **站点 A 有一个严格尺子看不见的副作用（本轮如实登记，未修）**：
   `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
   的 `RealtimeEventSource.clock_worker`（本来就已缺陷）产物由 `orig=1276 decomp=1251`
   变成 `decomp=1079` —— bad **计数**不变（10/12 ⇒ 产物门 `UNCHANGED`、A/B 只记
   `signature-only`），但丢的指令从 25 涨到 197；官方 `bytecode_diff` 同向
   （`decomp_count 1250 → 1078`）。单开一半的归因实验：只站点 A ⇒ 与全开逐字节相同
   （sha16 `3e367cad6833514f`），只站点 B ⇒ 与落地前逐字节相同 ⇒ **100% 出自站点 A**。
   全语料盲区扫描（`Σ|orig−decomp|` 逐文件，`fixes.md` §九）：`worse=1 better=1`，
   即全语料只有这一个函数因本补丁变差。处置 = 产物按「不得变差」保全回落地前版本
   （内容未手写，仅 `git checkout HEAD --`），`single` 已按要求重跑并复核索引一致。
   ⇒ 这是**第 10 个产物/核不一致文件**（但**不是**第 10 项产物门异常）。根因与 SubTask 20.9
   的 J1 同族（截断 BoolOp 链后父臂对块的双认领没收口），移交 Round 22，并且**此类修复的门禁
   今后必须同时看 `Σ|orig−decomp|`，不能只看 `n_ok`**。
2. `round21_oauth2` 残留 3 项 `MISMATCH`（同族异因，两世界都坏，非本轮回归）：
   `12`（`await`/`GET_AWAITABLE`/`SEND` 记账族，44→41）、`14`（真 and/or 短路链过量发射
   +2，Round 22 目标）、`13`（循环体内同族形状：R21-A 把 −6 变成 +1，仍 MISMATCH；
   多出的 1 条是 `JUMP_FORWARD`，与候选 c1 残留同族，站点在 `LoopRegion` 的 body/merge 归属里，
   本轮为避免与 R20-A 站点纠缠而未动）。
3. **ANALYSIS §10 的未闭依赖链**：A 族的触发条件比「块含协程语句」更窄——复现 02/05/09/15
   同形状但在基线核上就是 MATCH。即错误链 `[(566,'or'),(624,'and')]` 只在 566 本身是
   「某 if 臂的落点块」时才形成；上游为什么会走到成员块扩展，仍依赖外层 IfRegion 的
   `IF_FALSE` 同目标判据（`NONE_CHECK_OPS` 豁免段），本轮不需要动它，但这条链没有画清。
4. 顺手发现、不属 R21-A 范围的发射缺陷：`if (yield self.g(x)):` 产物丢外层括号
   → `if yield self.g(x):` SyntaxError（ANALYSIS §10）。
5. `TWHThreadController._target`（`IQCommon/logger/handlers.pyc`，`orig=192 decomp=190`）＝
   上一棒已登记的独立残差，本轮逐字未动。
6. quotation 残留 2：`change_his_to_forward` seq_len +1、`get_trend` 跳转终点不同（逐字未动）。
7. 9 文件产物/核漂移族（`klinedata`、`common_func`、`real_quote`、`plugin_fly_data/__init__`、
   `history_api`、`json_persistance`、`flytools`、`market_time`、`quote_handler`）仍每轮触发
   WORSENED/REGRESSION 回滚， culprit 单提交 `f89b85f2` 的 J1/J2/J3 回退改造未动（SubTask 20.9）。
8. Round 20 移交项照旧：`round20_rollover` 残留 7 项、`_if_generate_normal` elif 链 ~17156 的
   同形状 splice、SubTask 19.9 其余项（`trade_info_utils`、`strategy`、`calexrights_func`、
   `trade_live_broker`、`r16a_05`、`r15a_08`/`r15a_09`、`r17a_25`、`r18a_05`、`round19_cont`
   4 锚点、T1/T2 then 臂顺序、SubTask 13.4、Task 5）。

## 五、提交物

核：`core/cfg/region_analyzer.py`（+74/−2，判据代码净增 29 行）。
产物：`site-packages/fly/oauthenticator/oauth2OK.py`（+28/−20，工作树纯 CRLF；
唯一被工具改写的产物。`realtime_event_sourceOK.py` 经产物门改写后已保全回 HEAD 版本，
不在提交内）。
记录：`pyc_index.json`（1 条目）、`test_repros/round21_oauth2/`（16 复现 + `run_all.py`
+ `ANALYSIS.md`，本轮首次入库）、`rounds/round21/{arm-design.md,fixes.md,OUTCOME.md}`、
`tasks.md`（Task 21）。既有 11 套电池的 EXPECT 本轮无改动。
