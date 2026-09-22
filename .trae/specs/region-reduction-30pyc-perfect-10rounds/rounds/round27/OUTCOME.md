# Round 27 落地记录：R27-A（`_then_has_ctrl_exit` 的 raise 半边读的是第 0 臂闭包变量 ⇒ 链中段纯条件头被降级成语句表表头）

落地提交前基线：`d7a9901e`（Round 26 R26-A 之后，工作树 `dirty=0`、`ahead=0`）。
被改文件：`core/cfg/region_analyzer.py`（唯一），
git blob `64dbaa11e5e2dc436cb8f57c1e0b27da0c4c32dc` → `b98df3d2e150e8573cf37b9d38aa3595f21679d2`
（`git diff --numstat` = `59 0`，纯插入，无删改既有语句；CRLF 26842 → 26901，LF-only 0，无 BOM）。
`core/cfg/region_ast_generator.py` 本轮未动（`c10972d0586acf7339eaf32daff41cf43465dae0`）。

## 一、缺陷与根因（详述见 `arm-design.md`，实测复跑见 `logs/`）

缺陷族：一条 `if / elif / …` 链的某一递归级上，**下一个候选条件块是「纯条件块」**
（除尾部条件跳转外不携带自己的语句）时，`_check_elif_chain` 的 `_then_has_ctrl_exit`
否决把它降级成链尾扁平语句表 `elif_final_else` 的表头。降级之后生成器对该块发射 **0 条**
（打戳实测 `_generate_block_statements_body` 走 `region_ast_generator.py:44175` 的
`continue`、`_generate_block_statements` 走 `44262` 返回 `[]`），该条件的文本永久丢失；
它的 then 臂退化成 else 体里的一条无条件语句，其后的兄弟语句在重编译时位于该无条件
`return` 之后，被 CPython 3.11 当死代码整段消除。

靶子：`site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc`
:: `<module>.ObjectPersistancePlugin.can_resume_strategy`，严格尺 `orig=89 decomp=57`（−32），
该文件唯一缺陷（官方尺 14/15）。消失的 32 条 = 第 4 级条件块 B374（`if … == self._meta['end_date']:`）
的 9 条 + 其后的 B424/B544/B548 共 25 条死代码。区域树实测（`logs/insp_current.txt` 同型）：
B178..B548 同时属于外层链（`elif_conditions=[B178,B198]`＋`elif_final_else=[B374,B420,B424,B544,B548]`）
与内层子链（`elif_conditions=[B198,B374]`）⇒ 违反原则 2（每块唯一归属）。

根因（打戳定位，非阅读）：否决位 `region_analyzer.py:18170` 的 `_then_has_ctrl_exit`
由 18104-18113 的 `_then_has_raise` 半边置位，而 `_then_has_raise` 遍历的是**闭包变量
`then_blocks`** —— 即 `_build_elif_region` 第 0 臂（最外层 if 的 then 体）的块集合，
不是当前递归级前一臂。于是同一入参 `(header_=B198, else_blocks_=[B374,…], merge_=None)`
在两条发起路径上结论相反（`logs/probe_elif_v1.txt`）：

| 发起层 | `then_blocks` | `_then_has_raise` | 结果 |
|---|---|---|---|
| 外层 if（B0，臂 = B48 `raise`） | `[(48,[],'RAISE_VARARGS')]` | True | 18171 `return None` ⇒ 链在 B374 前中止 |
| 子区域（B178，臂 = B194 `return False`） | `[(244,[],'RAISE_VARARGS')]` 不出现 | False | 18145 救援生效 ⇒ 链吃到 B374 |

即：**第 0 臂是不是 raise 与「第 3 级的候选头块属于哪条链」没有关系**，它只是一条被
闭包带错层的陈旧事实。

## 二、判据 R27-A（同层 · 两条合取的结构谓词）

位置：`_check_elif_chain` 内，紧跟既有 `if not _then_has_raise:` 救援（`region_analyzer.py:18144`）
之后新增一条 `elif`；两个谓词作为嵌套函数插在 `def _check_elif_chain` 之前（同属
`_build_elif_region`，`region_analyzer.py:17902`）。

放行条件（合取，缺一不放行）：

1. `_r27_fe_carries_own_statements(_first_else, _fe_last)` 为假。
   判据与本函数下方 `region_analyzer.py:18289-18339` 既有的 `_has_body_stmt` **逐字相同**
   （同一 opcode 集，含 R21-A 补全的 `CALL`→(`YIELD_VALUE`/`RESUME`)*→`POP_TOP` 弹栈间隙半），
   只改为可调用形式。读的是块自身的指令与末指令偏移。
   —— 纯条件块没有语句化表示，把它降级必然吞掉它的条件文本。
2. `_r27_tail_is_self_contained(else_blocks_)` 为真：候选链尾块集在**后继**一侧闭合
   （集内任何块都不跳到集外）。取材面与既有 `_chain_merge_candidates`／`_body_succs_to_fe`
   相同（只看臂末块的 successors）。
   —— 不闭合则集外那个目标是**外层**结构的汇合点，`else_blocks_[0]` 是外层 else 体自己的头，
   不是本链的兄弟条件。

同层性：两条谓词都只读链自身的块集合、块自身指令与块的后继；不读绝对偏移次序、不读
函数名／常量、不读源码形状，不引入跨区域跨层启发。带前导语句的块仍由 `18340` 的同一
`_has_body_stmt` 判据终止扩展 —— 本放行不会把「有自己语句的块」吞进链。

## 三、门禁（严格串行；原始日志见 `logs/`）

| # | 门禁 | 结果 |
|---|---|---|
| G0 | 非空判据（语料无关合成复现） | `test_repros/round27_elif_pure_head/r27a_01_elif_head_after_raise.pyc`：head 读 `3/4`，缺陷函数 `case_elif_head_after_raise orig=71 decomp=41`，与语料靶子同一「整段条件＋其后死代码」签名；两条 CONTROL（首臂 return 形、候选头自带语句）在 head 已匹配 |
| G1/G2 | FIX 翻转 + CONTROL 不变 | 同一复现 cand `4/4`、`mism=[]`；`logs/g0_head.jsonl`、`logs/g0_cand.jsonl` |
| G1′ | 语料靶子 | `plugin_system_persist/__init__.pyc` head `14/15`（`can_resume_strategy 89/57`）→ cand `15/15`、`mism=[]` |
| G3 | 93 条承重锚点电池（含 R26 靶子 `r26a_01_break_prefix_in_while.pyc 4/4`） | `logs/batt93_head_vs_cand.txt`：`SAME=93 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`；空读数 0。head 与上轮落地基线 `base_landed93.jsonl` 亦 93 条逐条相同 ⇒ 臂隔离未失效 |
| G3′ | 同一电池对**落地字节**复跑 | `logs/batt_landed93.jsonl`：上一轮基线 / cand / landed 三臂 93 条记录 `sha` 与 `mism` 差异 **0 条**（Σmatched 266、Σtotal 294）⇒ 电池测的字节即落地的字节 |
| G4 | 全 402 文件 A/B（head vs cand，同一 runner、独立产物目录，发货判据） | `logs/ab402_head.jsonl`、`logs/ab402_cand.jsonl`：`SAME=397 IMPROVED=1 REGRESSION=0 MOVED=4 ERR=0` ⇒ 没有 ok→fail，爆炸半径 = **5/402 产物** |
| G4′ | 对 G4 的 5 个变化产物逐一跑严格尺 | `logs/strict_ab_moved.json`：靶子 `clean 14/15→15/15`、`sigma 32→0`；另 4 个 MOVED 文件逐函数的 `(orig 长, decomp 长, 缺陷类型)` 三元组**全等**（`klinedata 52/63 σ5`、`history_api 17/18 σ2`、`trade_live_broker 98/123 σ227`、`oauth2 12/12 σ0` 两侧不变） |
| G5 | `single` 靶子与承重锚点 | `plugin_system_persist/__init__.pyc ok 15/15 100.00%`；金丝雀 `fly/data/quotation.pyc` 保持 `ok 143/143 100.00%`；`risk_calculation/function.pyc partial 14/15`、`fly/common/flytools.pyc partial 64/65`（本轮未动，见 §六） |
| G6 | `batch --index pyc_index.json --round 27 --all` 全量复验 | `logs/batch_all27.txt`：rc=0，`total=402` 全跑完（`[402/402]`），无 `PARTIAL` 之外的异常行、无 traceback／timeout；索引写回 `pyc_index.json`。索引改动逐字段核对：`last_tested_round` ×402，`bytecode_match_rate`／`decompile_status`／`matched_functions` 各只落在**同 1 条**翻转型目（`0.9333…→1.0`、`partial→ok`、`14→15`），键集合无增删，Σ`function_count` 5746 不变，条目数 402 |
| G7 | `stats --index pyc_index.json` | `logs/stats27.txt`：`total_pyc 402 / verified_pyc 402 / ok_pyc 368 / partial_pyc 34 / failed_pyc 0 / total_functions 5746 / matched_functions 5640 / cumulative_match_rate 98.16%` |

## 四、5 个产物变化的逐项交代

* `IQEngine/plugins/plugin_system_persist/__init__OK.py` :: `can_resume_strategy`：
  第 4 级条件 `if persist_meta['last_calendar_dt'] == self._meta['end_date']:` 回到链内，
  其后的两条赋值与末级 `if` 退回链后直落。⇒ 15/15、严格尺 89/89。
* 另 4 个 MOVED 产物是**同一处**、且经 G4′ 证明严格尺中性的规范化：`raise` 终结臂之后的
  第一个 `if` 改写为 `elif`（CPython 3.11 下二者逐条同形，臂本身无后继）：
  `IQCommon/api/klinedata.pyc`（`if unit in OVER_WEEK_FREQUENCY:` → `elif …`）、
  `IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc`（同形）、
  `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`（`if self.frequency == 'tick':` → `elif …`）、
  `fly/oauthenticator/oauth2.pyc`（`if self.fly_sys_version == 'sns':` → `elif …`）。
  这四处不是新缺陷也不是修复，是判据的既定作用面；承重锚点 `trade_live_broker` 的
  严格尺读数（98/123、σ227）逐函数不变。

## 五、本轮的关键方法论收获：裸放行版被判据②否证

诊断线交来的初版候选只含判据 ①（无 ②），其自带的 402 文件 A/B 读数为
`SAME=394 IMPROVED=1 MOVED=7 REGRESSION=0 ERR=0` —— 官方尺**没有任何回退**。
但它把 `fly/common/tradingday_calendar.pyc :: get_start_day` 从**严格尺完全一致**
改成 `target_diff`（该函数官方尺两侧都读 `28/28`）：

```
#79  JUMP_FORWARD   orig 终点 = ('start_date', LOAD_FAST)      （函数级汇合点 1294）
                   cand 终点 = ('get_minite_time', LOAD_GLOBAL) （被抬出 else 体的语句 670）
```

即它把外层 else 体自己的头 `if end_date is None:` 当成本链的兄弟条件吞掉，连带把
`else:` 体内与其并列的 `start_date, end_date = get_minite_time(end_date, count)` 抬到了
整条链之后 ⇒ `if type == 'daily':` 臂的出口跳转从「跳过该语句」变成「跳进该语句」。
打戳对照（`logs/probe_fires_v1.txt`、`logs/probe_fires_v2.txt`）给出两案在该点的差异：
被否证案的 `else_blocks_` 含跳到集外的块（`670 → 1294`），本案全部块的后继都在集内。
补上判据 ② 后，`MOVED` 由 7 降到 4、`get_start_day` 的产物逐字节不变，靶子仍然翻转。

**结论**：只读官方尺的 402 文件 A/B 不足以充当唯一发货判据 —— 凡 `MOVED` 都必须回到
严格尺逐函数三元组核一遍。本轮已把这条固化进门禁表（G4′）。

## 六、残余与移交

* `plugin_system_risk_calculation/function.pyc` 仍 `14/15`（严格尺 −4）、
  `fly/common/flytools.pyc` 仍 `64/65`（异常清理复制 + 丢失的 `JUMP_BACKWARD` 混形）：
  两者都不是本轮形状，见 `D:/Temp/r27self/NOTES-r27-pool.md`。
* 诊断线 A（异常尾声按退出路径内联复制丢失，`save_testds_to_json 314/310`）本轮未收口：
  代理在交付 `ANALYSIS.md` 之前耗尽轮次上限（Round 26 的代理同样如此），其私有目录
  `D:/Temp/r27diagA/` 的 `r27a.py`/`shape27.py`/`funnel_out.txt` 已列为 Round 28 起点。
  本轮只落地一条判据，故该族继续单线推进。
* 「链双认领」第二诊断线（代理耗尽轮次）留下的合成复现对 `r27b_01_elif_midchain_condition_drop.pyc` /
  `r27b_02_control_rejoin_keeps_veto.pyc` 已实测：两臂（落地前核 / 落地核）读数**逐条相同**
  （`r27b_01 3/3 mism=[]`；`r27b_02 2/3`，其 `guard_rejoin orig=34 decomp=35`、2 处跳转差、11 处实差），
  故该形状既不是 R27-A 修复的、也不是 R27-A 造成的 —— 是一条独立线。`guard_rejoin` 的 **+1 过量发射**
  属 D2 族，列入 Round 28 候选靶子。因其标签与实测相反（名为 CONTROL 却带缺陷），这对文件已从
  `test_repros/` 移到 `D:/Temp/r27self/quarantine/round27_elif_double/`（未进仓库，可逆）。
* Round 28 电池基线：`logs/anchors94.txt`（93 条 + 本轮复现）已对**落地字节**跑完，
  `logs/base_landed94.jsonl` ＋ 原始读数 `logs/logs_landed94.txt`：94 条记录、error 0、空读数 0；
  与上轮 93 条基线的共有 93 条 `sha`/`mism` **零漂移**，新增的 1 条即本轮复现 `4/4`。
  下一轮候选必须以 `base_landed94.jsonl` 为基线，并换用新文件名（不得就地覆盖）。
* `plugin_system_persist/__init__.pyc` 自本轮起 `ok 15/15`，后续轮次它是**必须保持 15/15**
  的承重锚点；`fly/data/quotation.pyc` 继续要求 143/143。
