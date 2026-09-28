# Round 75 · diag1 · 71 失败单元子机理归属 — FACTS

工作区 `D:/Temp/opencode/r75gate/diag1` · 基线 HEAD **`78679fd0`**（R75 start）·
mandated 尺 `6546/6617 = 98.93%`（34 支 failure / 71 失败单元）· 官方尺 `5720/5746 = 99.55%` ·
repo `F:/Downloads/pythoncdc-main` **本批零写入**（无创建/修改/删除、无 git 写操作、未动任何 `*OK.py`、
未跑 402 全量；`git status` 的既有脏项见 §9）· 所有读数只写本区 `dump/` · 无 `specs/` 交付（BRIEF_diag1 §4）。

---

## 0. 结论（五问各一句）

1. **Q1 F-ABSORB 61 四选一 = `a-shared-merge-absorbed` 34 / `b-orphan-child` 11 /
   `a2-shared-tail-extpred` 7 / `d-displacement` 5 / `c-target-diff-instr` 4**。
   flag incidence（F-ABSORB）：`mergeabs>0` **34**、`orphan>0` **22**、`outpred>0` **47**、
   三 flag 全零 **9**（= c4 + d5）。另有 F-PAD 8（b5/a2 2/d1）、F-POLARITY 1（a）、F-OTHER 1（c）。
2. **Q2 9 个 inside-try 单元 = 异常表字节全同 2 / 条目数差 3 / 同数异字节 4**；
   字节全同的 `trade_operation`、`tick_worker_thread` 判 **try=载体**（根因在 try 内的区域归约），
   其余 7 个 try 结构是差异来源之一，须按 `lineB` 落点逐条对照 handler 起止行。
3. **Q3 `real_quote.get_tick_direction` 回退 = ADR-1 计分形状效应（真实叠加）**：
   `try7_3` 的 5 处编辑**根本没碰该单元**（读数与 landed 逐位相同，过 ADR-1 是「没改」而非「改好」）；
   `try7_9`/`try7_10d` 新增的 T7（`2b9410cc`）把结构摆正后 `sd 184→4`、`hunks 12→5`，
   但**丢了尾部共享 `return pd_dict`**，3 个归一化 hunk 全是这一件事的三个投影
   ⇒ `hunks_norm 2→3` 触发 ADR-1 拒收。
4. **Q4 7 个点名单元（et>0、首分歧区外）= try=根因 0 / try=载体 3 / 并列 4**；
   全部 7 个 `intry=0`（首分歧确在异常区外）。
5. **Q5 跨文件同构 = 指令级 0 簇 / 机制级 7 簇覆盖 66/69 单元**：
   三大头部（trade_live_broker 13 / quote 11 / trade_info_utils 5）的残留单元**指令级不同构**，
   但按 `(family, cls)` 归并后 F-ABSORB/a 横跨 **20 个文件 33 单元**、F-ABSORB/b 横跨 8 文件 11 单元
   ⇒ 修一处区域归约缺陷，同簇多文件同时受益。

主表：`dump/submech75.txt`（Q1 71 行全量，20 列含 flag/evidence）·
`dump/inside75.md`（Q2 9/9 + §10 汇总裁决）·
`dump/tick_direction75.md`（Q3 986 行 + §5 解剖结论）·
`dump/q45_75.md`（Q4 表 + Q5 机制级聚类）。

---

## §1 Q1 · 71 单元子机理四选一（`dump/submech75.txt`）

命令：`python -W ignore -X utf8 D:/Temp/opencode/r75gate/diag1/submech75.py`

### §1.1 判据与优先级（BRIEF_diag1 §2.1 的落成实现）

三个结构 flag 全部来自 `chain.json`（链成员/孤儿/外扩谓词），**互斥优先级已改为 mergeabs 在前**：

| 优先级 | cls | 判据 |
|---|---|---|
| 1 | `a-shared-merge-absorbed` | `mergeabs>0`：链成员条件跳转汇聚到祖先 merge block，该 block 被祖先 `IfRegion` 的 else 臂吸收（`region_analyzer.py:27334-27362` R68-E 守卫 `_w14_p in entry.dominators` 豁免 W14-C 剪枝） |
| 2 | `b-orphan-child` | `orphan>0` 且 `mergeabs=0`：区域树 children 覆盖差，合并后 child 不在 `blocks/then_blocks` |
| 3 | `a2-shared-tail-extpred` | `outpred>0` 且前两者为 0：共享尾被外扩谓词吃掉 |
| 4 | `c-target-diff-instr` | 三 flag 全零 且 fam `reason` ∈ {`C-target-diff-instr`, `C3-opname-diff`} |
| 5 | `d-displacement` | 三 flag 全零 且 fam `reason` ∈ {`C2-target-same-instr`, `D-or-len`} |

> **口径变更提示**：`b` 从优先级 1 降到 2（原实现 orphan 在前）。两 flag 并存的 11 个单元
> （`mergeabs>0 ∧ orphan>0`）在旧口径会记成 b、新口径记成 a ⇒ 切换前后等价读数为
> **旧 `a 23 / b 22` → 新 `a 34 / b 11`**（F-ABSORB 内；`mergeabs>0` 34、`orphan>0` 22 不变）。
> F-PAD 无 mergeabs（`mergeabs=0`）故不受影响。

### §1.2 计数（`dump/submech75.txt` 全量，与 fam75 71 行逐条 join，缺失 0）

| family | a | b | a2 | c | d | 合计 |
|---|---|---|---|---|---|---|
| **F-ABSORB** | **34** | **11** | **7** | **4** | **5** | **61** |
| F-PAD | 0 | 5 | 2 | 0 | 1 | 8 |
| F-POLARITY | 1 | 0 | 0 | 0 | 0 | 1 |
| F-OTHER | 0 | 0 | 0 | 1 | 0 | 1 |
| **合计** | **35** | **16** | **9** | **5** | **6** | **71** |

### §1.3 flag incidence × cls（F-ABSORB 61；判据自洽性读数）

| cls | n | mergeabs>0 | orphan>0 | outpred>0 | 三 flag 全零 |
|---|---|---|---|---|---|
| a-shared-merge-absorbed | 34 | **34** | 11 | 32 | 0 |
| b-orphan-child | 11 | 0 | **11** | 8 | 0 |
| a2-shared-tail-extpred | 7 | 0 | 0 | **7** | 0 |
| c-target-diff-instr | 4 | 0 | 0 | 0 | **4** |
| d-displacement | 5 | 0 | 0 | 0 | **5** |

- F-ABSORB 合计 `mergeabs 34 / orphan 22 / outpred 47 / 全零 9`；F-PAD `orphan 5 / outpred 5 / mergeabs 0`。
- **`orphan 22 = a 类 11 + b 类 11`**：即 11 个 MERGEABS 单元**同时**有未覆盖 orphan
  （A∩B 形态，与 R74 §1.2 的 3 个 A∩B 同源、放大到 11 个）⇒ fix 批改 MERGEABS 守卫时，
  这 11 个单元的 orphan 覆盖差会同时变化，必须同批回归。
- 三 flag 全零 9 个即 `c`4+`d`5，全部靠 fam `reason` 派生（evidence 列为空）；
  其中 `wizard_quant_api.get_DMI.calculate_di.<genexpr>` 在 fam75 中**重复 2 行**（见 §7 重复键提醒）。

### §1.4 落点形态 × family（fam75 `reason` 分布，与 R74 §1.4 同口径）

| 落点形态 | F-ABSORB | F-PAD | F-POLARITY | F-OTHER |
|---|---|---|---|---|
| L1 落点不同指令（`lands on DIFFERENT instr`） | **31** | — | — | — |
| L3 落点同、len 变（`target instr same but len…`） | **23** | — | — | — |
| L5 opname 变（`opname …`） | **7** | — | — | **1** |
| L2 落点同、len 等（`SAME instr, len equal`） | — | **8** | — | — |
| 极性翻转（`POP_JUMP_FORWARD_IF_TRUE → POP_JUMP_…_FALSE`） | — | — | **1** | — |

---

## §2 Q2 · 9 个 inside-try 单元行级根因（`dump/inside75.md`）

命令：`python -W ignore -X utf8 D:/Temp/opencode/r75gate/diag1/inside75.py`

### §2.1 判据

- `ET orig→prod`：`marshal.loads(pybytes[16:]).co_exceptiontable` 条目数（`_parse_exception_table`）；
  `bytes_equal` = 两张表**逐字节**全同。
- `prod ast.Try n/nest`：产品 OK.py 源 `ast.walk` 出的 `Try` 节点数 / 最大嵌套深度。
- `lineB` = 首分歧产品行；`lineB 在 try 内` = 落在产品任一 `ast.Try` 的 `lineno..end_lineno`。
- `co_lines()` 对 `line=None` 的条目按前后最近行回填（编译器填充字节的空行）。

### §2.2 汇总裁决（`inside75.md` §10，9/9）

| file | unit | family | ET orig→prod | bytes_equal | prod ast.Try n/nest | lineB 在 try 内 | lineA/lineB | 判决 |
|---|---|---|---|---|---|---|---|---|
| IQCommon/util/trade_info_utils.pyc | trade_operation | F-ABSORB | 18→18 | **True** | 1/1 | False | 288/133 | **try=载体** |
| IQEngine/…/strategy.pyc | tick_worker_thread | F-ABSORB | 3→3 | **True** | 1/1 | True | 311/223 | **try=载体** |
| fly/data/quote.pyc | run_tick_socket | F-PAD | 13→12 | False | 2/2 | True | 2156/1431 | 条目数差 ⇒ try 边界/层次有差 |
| IQData/…/real_quote.pyc | get_real_minute_kline | F-ABSORB | 7→8 | False | 1/1 | False | 584/370 | 条目数差 ⇒ 同上 |
| IQCommon/util/cgroup_utils.pyc | set_cgroup_config | F-ABSORB | 4→5 | False | 1/1 | True | 75/34 | 条目数差 ⇒ 同上 |
| IQCommon/data/finance.pyc | get_fields | F-ABSORB | 8→8 | False | 1/1 | True | 655/432 | 同数异字节 ⇒ handler 落点/depth 有差 |
| IQCommon/util/email_utils.pyc | send_email | F-ABSORB | 5→5 | False | 1/1 | True | 57/38 | 同上 |
| IQEngine/…/realtime_event_source.pyc | clock_worker | F-ABSORB | 24→24 | False | **4/2** | True | 189/100 | 同上（产品 4 层 try、nest 2） |
| fly/common/flytools.pyc | modify_batcktes_info | F-PAD | 22→22 | False | 1/1 | True | 1133/796 | 同上 |

- **字节全同 2/9 ⇒ try=载体**：根因在 try 内的区域归约（`trade_operation` = a3 假臂直跳 merge、
  `tick_worker_thread` = (c) `or` 链），**不必动 try 生成路径**。
- **条目数差 3/9**：13→12、7→8、4→5 —— 产品多/少一条 protected range，须对照 handler 起止行。
- **同数异字节 4/9**：条目数与 depth 相同但 start/end/target 有漂移。
- `lineB` 在产品 try 行区间内的 **7/9**（首分歧即产品 try 的行上）；`trade_operation`、
  `get_real_minute_kline` 两单元首分歧在 try 之外的语句行。
- 与 R74 11 单元三选一（`a 10 / c 1`）读数**并列存档**：本批 9 个是 R75 口径
  （`firstdiv.origTryDepth=1`），R74 的 11 个是 R74 口径，两者不可直接相减。

---

## §3 Q3 · `real_quote.get_tick_direction` 解剖（`dump/tick_direction75.md`）

命令：`python -W ignore -X utf8 D:/Temp/opencode/r75gate/diag1/tick75.py`（§4 字节段由 `patch_tick.py` 一次性改写）

### §3.1 臂 × 指标（adr73 同口径：hunks / 归一化 hunks / 首分歧 / sdelta）

| 臂 | spec | 指标 `hunks / norm / first / sd` | 相对 landed |
|---|---|---|---|
| landed | `abs1` | 12 / **2** / 4 / 184 | — |
| absj | abs1+`abs2_orphan_child_emit` | 12 / 2 / 4 / 184 | **零变化** |
| absj3 | absj+`try7_3` | 12 / 2 / 4 / 184 | **零变化** |
| absj9 | absj+`try7_9` | 5 / **3** / 4 / **4** | 结构被改写 |
| absjt / try7_10d | absj+`try7_10d` | 5 / 3 / 4 / 4 | 与 absj9 逐位相同 |
| try7_3（重建） | — | 与 landed **逐位相同** | — |

- **`try7_3` = 5 edits**（`78eea71b` T1/T2、`343e05ae` T4、`66486c1d`、`0b10b201`、`861c978c` T6）
  **完全不含**改变该单元的那两处；`try7_9` = 上述 5 处 + **`31b0d3fa` `_try_has_return` 守卫** +
  **`2b9410cc` T7**（7 edits）；`try7_10d` = 同 7 处但守卫换成 2931 B 长版（带 BDBG）。
- ⇒ **absj3 过 ADR-1 是因为它没碰这个单元的形状**，不是因为做得更好。

### §3.2 结构差（`build_landed` vs `build_absj9`，各 78 行）

- landed：`if redata:` 把 `flag==1 / flag==-1 / return redata` 当同级 `elif` 挂在 try 外侧，
  `return pd_dict` 停在 if 链内（结构错）。
- absj9（T7）：改成 `if A: P else: <flag 链>; return redata`，try 从 if 链切出、在链后重发——
  **正是 T7 注释描述的原始结构** ⇒ `sd 184→4`、`hunks 12→5`（三条跳转差只剩 1 条 `to 512→to 516`）。
- 代价：切出/重发后**尾部共享 `return pd_dict` 没有被重新发射**，产品函数尾变成
  `return redata` + 隐式 `return None`。

### §3.3 3 个归一化 hunk 的字节（matched Inst `offset/bytecode`，`tick75.py` §4）

| # | 归一化 hunk | orig | absj9 产品 | 字节 |
|---|---|---|---|---|
| 1 | replace | `231 JUMP_FORWARD to 512` | `231 LOAD_CONST None` + `232 RETURN_VALUE` | 跳转被物化成 `return None` |
| 2 | replace | `247 JUMP_FORWARD to 512` | `248 LOAD_CONST None` + `249 RETURN_VALUE` | `6400 5300` @496/498 |
| 3 | replace | `256 LOAD_FAST pd_dict` @512 | `258 LOAD_CONST None` @516 | orig `7c08 5300` vs 产品 `6400 5300` |

三条 hunk 全是同一件事的三个投影：**产品少了共享尾 `return pd_dict`**。

### §3.4 判读与 fix1 处方

1. landed/absj/absj3 的 2 个归一化 hunk 是「整块搬移」形状（`delete orig[148:174]` +
   `insert prod[232:259]`），尾部 `return pd_dict` 差异被包进 insert 段**不单独计数**。
2. T7 摆正结构后大块搬移消失，剩下 3 处**真实出口差**被逐个计为独立 hunk ⇒ `hunks_norm 2→3`。
3. ADR-1 任一指标变差即拒收：`hunks ✓ 12→5`、`sd ✓ 184→4`、`first 4→4` 都不触发，
   只有 `hunks_norm 2→3` 触发 ⇒ 拒收。
4. **回退 = ADR-1 计分形状效应（真实叠加）+ 一个真实缺陷（共享尾未重发）**。
   **fix1 正确姿势不是放弃 T7**，而是给 T7 补尾部共享块重发射（或按 `handlers._target` 已验证的
   行表判据：不物化编译器生成的 `return None`、让各出口 `JUMP_FORWARD` 到共享尾），
   使 `hunks_norm ≤ 2` 后重跑 ADR-1。
5. **edit5 vs edit6 归因隔离留 fix 批**：`absj+edit5`（`31b0d3fa`）与 `absj+edit6`（`2b9410cc`）
   各建一臂跑 ADR，diag1 只读不建臂。

---

## §4 Q4 · et>0 首分歧区外单元「try 是载体还是根因」（`dump/q45_75.md`）

命令：`python -W ignore -X utf8 D:/Temp/opencode/r75gate/diag1/q4575.py`

### §4.1 判据（分层规则，7 单元点名来自 BRIEF_diag1 §2.4）

1. `产品异常表深度 > 原深度`（`dp>do`）或 `产品条目数 > 原条目数`（`ep>eo`）
   ⇒ **try=根因**（产品多建层/多开 protected range）；
2. 否则 `ET 字节全同` ⇒ **try=载体**（异常表一致，差异全在 try 内控制流落点）；
3. 否则 ⇒ **并列**（条目数与深度全同 → 「handler 起止/target 漂移」；否则「产品未多建层」；
   两支都用 `lineB` 是否落在产品 try 行区间 tiebreak）。

> 实现：`q4575.py:157-177`（`extra = (dp>do) or (ep>eo)` → `elif beq` → `elif (eo,do)==(ep,dp)` → else）。

### §4.2 逐单元判决

| file | unit | cls | ET ents o→p | ET depth o→p | bytes_eq | prod ast.Try n/nest | intry | lineB 在产品 try 内 | lineA/lineB | 判决 |
|---|---|---|---|---|---|---|---|---|---|---|
| klinedata.pyc | get_kline_by_count_new | a | 8→8 | 1→1 | **True** | 1/1 | 0 | False | 339/219 | **载体** |
| trade_info_utils.pyc | kill_trade_process | b | 24→24 | 1→1 | **True** | 4/1 | 0 | True | 411/240 | **载体** |
| trade_info_utils.pyc | get_trade_status | a2 | 11→11 | 1→1 | **True** | 1/1 | 0 | False | 1515/1026 | **载体** |
| quote.pyc | check_frequency | b | 2→2 | 1→1 | False | 1/1 | 0 | False | 1341/996 | 并列 |
| quote.pyc | run_individual_transform | a | **13→10** | 1→1 | False | 2/2 | 0 | False | 2052/1314 | 并列（产品**少** 3 条 protected range） |
| ptradeAccount.pyc | order_response_order_update | b | 8→8 | 1→1 | False | 2/2 | 0 | True | 1907/891 | 并列 |
| ptradeAccount.pyc | trade_response_order_update | b | 2→2 | 1→1 | False | 1/1 | 0 | True | 1932/914 | 并列 |

**计数：try=根因 0 / 载体 3 / 并列 4（共 7）**；`intry=0` 7/7（点名单元确在首分歧区外）。

- **根因 0** 是硬读数：没有一个点名单元出现「产品多建 try 层」；并列 4 个里
  `run_individual_transform` 反而**少** 3 条 protected range（13→10，产品欠发射/合并了 handler），
  另 3 个条目数相同但字节异（start/end/target 漂移）。
- ⇒ **「try 是根因」在本批没有直接证据**；7/7 残留形状都是区域归约（a/b/a2）的投影。

### §4.3 附：71 单元 `exctable × intry × cls` 交叉（全量读数）

| exctable | intry | cls | n |
|---|---|---|---|
| DIFF | 0 | a / a2 / b | 10 / 1 / 7 |
| DIFF | 1 | a / b | 4 / 3 |
| SAME | 0 | a / a2 / b / c / d | 18 / 8 / 6 / 5 / 5 |
| SAME | 1 | a | 2 |

- `DIFF` 25 / `SAME` 44（合计 69 唯一键）；**`DIFF ∩ intry=1` 的 7 个恰好就是 §2 Q2 里 ET 有差的那 7 个**
  （`run_tick_socket`、`get_real_minute_kline`、`get_fields`、`set_cgroup_config`、`send_email`、
  `clock_worker`、`modify_batcktes_info`），`SAME ∩ intry=1` 的 2 个即 Q2 的 `trade_operation`、
  `tick_worker_thread` ⇒ **Q2 9 单元与本节点名 7 单元完全不相交**（Q4 全部 `intry=0`）。

---

## §5 Q5 · 跨文件同构聚类（`dump/q45_75.md` §Q5）

### §5.1 指令级聚类（放宽键 = `(family, cls, lenA-lenB, 首异 opname, 首异跳转 opname)`）

**跨 ≥2 文件的簇：0 个。** 三大头部残留单元在指令级**不同构**，
不存在「一处修多支」的指令级共同修法。

### §5.2 机制级聚类（`(family, cls)` × 文件，全量 71）

**7 个跨 ≥2 文件的机制簇，覆盖 66/69 唯一单元**：

| 机制簇 | n | files | 代表 |
|---|---|---|---|
| **F-ABSORB / a-shared-merge-absorbed** | **33** | **20** | `api_base.get_history_df`、`quote.*`×5、`trade_live_broker.*`×7、`real_quote.get_tick_direction`、`get_real_minute_kline` |
| **F-ABSORB / b-orphan-child** | **11** | **8** | `handlers._target`、`jq_trans_module.replace_args`×2、`ptradeAccount.*`×2、`risk_calculation._on_publish…`/`_save_testds_to_csv`、`cgroup_utils` |
| **F-ABSORB / a2-shared-tail-extpred** | **7** | **5** | `future_contract_info.check_user/info_conbine`、`order_api.base_order`、`get_trade_status` |
| **F-PAD / b-orphan-child** | **5** | **3** | `kill_trade_process`、`query_strategy_id`、`quote.check_frequency/run_tick_socket`、`modify_batcktes_info` |
| **F-ABSORB / c-target-diff-instr** | **4** | **4** | `logger.check_baseFilename`、`quote.get_price`、`trading_dates_reload` |
| **F-ABSORB / d-displacement** | **4** | **4** | `stock_position.make_trade`、`get_DMI.<genexpr>`、`etf_purchase_redemption` |
| **F-PAD / a2-shared-tail-extpred** | **2** | **2** | `query_trade_strategy_info`、`etf_basket_order` |

**判读**：同 `(family, cls)` = 同一区域归约缺陷在不同文件的投影 ⇒
**一处修，同簇多文件同时受益**；这正是 fix 批应按「机制」而非按「文件」选靶的依据。

### §5.3 三大头部 `family × cls` 交叉（同构性的粗粒度读数）

| family | cls | trade_live_broker | quote | trade_info_utils | 合计 |
|---|---|---|---|---|---|
| F-ABSORB | a | **7** | **5** | 1 | 13 |
| F-ABSORB | a2 | 2 | 1 | 1 | 4 |
| F-ABSORB | c | 1 | 1 | 0 | 2 |
| F-ABSORB | d | 1 | 1 | 0 | 2 |
| F-PAD | b | 0 | **2** | **2** | 4 |
| F-PAD | a2 | 1 | 0 | 1 | 2 |
| F-OTHER | c | 0 | 1 | 0 | 1 |
| F-POLARITY | a | 1 | 0 | 0 | 1 |

- 头部主导形状是 **F-ABSORB/a（13/29）**；`ptradeAccount` 的 2 个与 `quote.check_frequency`、
  `run_tick_socket`、`kill_trade_process` 同属 **F-PAD/b**。
- 三大头部 29 单元中 29/29 落在 7 个机制簇内 ⇒ 机制级修法可一次覆盖全部头部。

### §5.4 全量按文件分布（71）

`trade_live_broker 13` · `quote 11` · `trade_info_utils 5` · `klinedata 3` · `order_api 3` ·
`wizard_quant_api 2` · `jq_trans_module 2` · `real_quote 2` · `risk_calculation(__init__) 2` ·
`future_contract_info 2` · `ptradeAccount 2` · 其余单单元文件若干（`finance`、`handlers`、
`cgroup_utils`、`email_utils`、`flytools`、`logger`、`stock_position`…）。

---

## §6 机理附录（fix 批的两条已验证读数）

### §6.1 MERGEABS 守卫（a 类 34 单元的共同根因候选）

- 站点：`core/cfg/region_analyzer.py:27334-27362`，R68-E 守卫
  `_w14_p in entry.dominators` 豁免 W14-C 剪枝。
- 后果：祖先 merge block（`trade_operation` 例：block 1000）被 `IfRegion@726` 的 else 臂吸收
  ⇒ 假臂绕过 `write_info.append(items)`；区域归约信号在 `submech75.txt` `evidence` 列形如
  `MERGEABS r=IfRegion@862 merge=[1200] s=IfRegion@980 hit=[1200]`。
- 与 orphan 的耦合：F-ABSORB 内 `orphan>0` 的 11 个单元**同时** `mergeabs>0`
  （§1.3）⇒ 收紧守卫会同时改变它们的 orphan 覆盖读数，须同批回归。

### §6.2 `handlers._target` 的已验证修复形状（b 类可复刻模板）

- 差异根因：原品多一对 `LOAD_CONST None; RETURN_VALUE`，**行表证明为编译器生成**。
- 已验证操作：删产品 OK.py line40 `return None` + line41 `if` → `elif`
  ⇒ `co_exceptiontable` 与 `co_code` 与原品**逐字节相等**、`unified_diff` 0 行。
- ⇒ b 类 16 单元的修复方向是**判据化地不物化编译器生成的隐式 `return None`**，
  而非改 try/except 生成路径（与 §4「根因 0」互相印证）。

### §6.3 mandated 单支复测（可复现读数）

- 命令（detached，规避同进程 import `pyc_verify` 的 0xC0000409 崩溃）：
  `python D:\Temp\opencode\r75gate\center\launch.py D:/Temp/opencode/r75gate/diag1/run_pycverify.py`
- 读数：`dump/pycverify_rq.json` —— `real_quote 43/45 status=failure`，
  失败单元 = `get_real_minute_kline`、`get_tick_direction`（均为 F-ABSORB/a）。
- 走 API：`pyc_verify.evaluate(pyc, source, tmpdir, compare_pyc)` + `load_compare_pyc(PYLINGUAL)`。

---

## §7 dump 索引与命令行（全部在 `D:/Temp/opencode/r75gate/diag1`，每条 <300s）

| 命令 | 产物 | 内容 |
|---|---|---|
| `python -W ignore -X utf8 d74_join.py`（R74 探针适配 R75 输入） | `dump/units75_join.json` / `.tsv`、`dump/join_gap.txt` | 五方 join 主表（fam75 × filecat × firstdiv × exctable × tryverdict）；`join_gap.txt` 记 join 缺失 0、重复键 2 组 |
| `python -W ignore -X utf8 submech75.py` | `dump/submech75.txt` | **Q1**：71 行 20 列（file/unit/family/cls/verdict/lenA/lenB/mcls/stream/njump/ret/orphan/mergeabs/outpred/lineA/lineB/firstA/firstB/reason/evidence）+ flag incidence 打印 |
| `python -W ignore -X utf8 inside75.py` | `dump/inside75.md` | **Q2**：9 单元 ET/handler 区间/nest/产品 `ast.Try`/lineB 上下文 + §10 汇总裁决 |
| `python -W ignore -X utf8 tick75.py` | `dump/tick_direction75.md` | **Q3**：7 臂 metrics + 归一化 hunk + matched Inst 字节（§4）+ §5 解剖结论 |
| `python -W ignore -X utf8 q4575.py` | `dump/q45_75.md` | **Q4** 7 单元分层判决 + 71 交叉；**Q5** 指令级簇 0 + 机制级 7 簇 + 头部交叉 + 文件分布 |
| `python D:\Temp\opencode\r75gate\center\launch.py diag1/run_pycverify.py` | `dump/pycverify_rq.json`、`dump/pycverify_rq_log.txt` | mandated 单支复测（detached） |
| `python -W ignore -X utf8 patch_tick.py` | 改写 `tick75.py` §4 一次 | matched Inst 的 `offset/bytecode` 打字节（`seq_of` 改返回 Inst 列表、`metrics` 调用处 `tup()`） |
| 手写 + 拼接 | `dump/_concl_tick.md` → `tick_direction75.md` §5 | Q3 解剖结论源文件（§5 由其追加） |

只读中心件（未覆盖其 dump）：`center/dump/exctable_diff75.txt`、`center/dump/tryverdict75.txt`、
`center/fam75.json`（= `diag1/fam75.json` 同源）、`center/adr73.py`、`scripts/pyc_verify.py`、
`r74gate/diag1/FACTS.md`（结构参照）；`diag1/dump/crosstab75.txt` 是 `center/dump/crosstab75.txt`
的**逐字节同一拷贝**（md5 相等，只读）。

本区 `dump/`（20 文件）内的 R74 只读拷贝（对照用，未重新生成）：`trisect74.txt`、`root11.txt`、
`try_units.txt`~`try_units4.txt`、`abs1.json`、`chain.json`。

早期探索探针（`align.py`、`disf.py`、`genif75.py`、`nested_diff.py`、`nhunks.py`、
`regdump.py`、`probe_chain.py`、`fixprev74.py`、`driver75b.py`→`dump/_driver75b.log`、
`strict_repo67.py`）：其读数已并入上列各 dump 或仅 stdout 落 `_driver75b.log`。

**重复键提醒**：`fam75.json` **71 行、`(pyc_base, name)` 唯一键 69** —— 两组重复：
`calexrights_func.pyc <module>.change_his_to_forward` ×2、
`wizard_quant_api.pyc <module>.get_DMI.calculate_di.<genexpr>` ×2
（`join_gap.txt:5`）。⇒ **引用计数一律按「文件+单元」去重**；Q5 覆盖读数写作 `66/69`。

---

## §8 对 fix1 / fix2 / fix3 的建议与风险

**fix1（a 类 34 + tick_direction）**
- 优先级 1 = **MERGEABS 守卫**（`region_analyzer.py:27334-27362`），靶集直接取
  `submech75.txt` 中 `cls=a-shared-merge-absorbed` 的 34 行（§1.2），
  其中 11 个 A∩B（`mergeabs>0 ∧ orphan>0`）必须与 orphan 补发射同批验证。
- **tick_direction 不是放弃 T7，而是给 T7 补尾部共享块重发射**（§3.4），
  使 `hunks_norm ≤ 2` 后重跑 ADR-1；edit5/edit6 分臂隔离归因。
- 收敛判据：该单元 `hunks_norm ≤ 2` 且 `sd ≤ 184` 且回归 4/4 金丝雀、strict worse=0。

**fix2（b 类 16 + orphan 覆盖）**
- 模板已验证：`handlers._target` 的「不物化编译器生成 `return None` + `if`→`elif`」
  ⇒ 字节全等（§6.2）。**b 类 16 个按定义全部 `orphan>0`**（F-ABSORB 11 + F-PAD 5，
  §1.3），即「合并后 child 不在 `blocks/then_blocks`」的 27 条 R74 清单在 R75 放大到 16 单元量级，
  补发射判据仍只依赖「child 不在 blocks/then_blocks」这一结构事实（不用偏移阈值/函数名）。
- F-PAD/b 的 5 个（`kill_trade_process`、`query_strategy_id`、`check_frequency`、
  `run_tick_socket`、`modify_batcktes_info`）是 **R74 §3「同形态未覆盖 3 + 新形态 4」的延续**，
  pad_e2fix 不覆盖，需新判据分支。
- 风险：`check_frequency` 在 Q4 判「并列」（ET 2/2 字节异）⇒ 改 orphan 未必动它的 ET，
  归因要与 `run_individual_transform` 的 13→10 欠发射分开。

**fix3（inside-try 9）**
- **try=载体 2 个**（`trade_operation`、`tick_worker_thread`）不必动 try 生成路径，
  根因分别是 a3 假臂直跳与 (c) `or` 链归约 —— 与 R74 的 `a 10 / c 1` 并列存档。
- **条目数差 3 个**（`run_tick_socket` 13→12、`get_real_minute_kline` 7→8、
  `set_cgroup_config` 4→5）是唯一「try 边界/层次有差」的硬读数，优先按 `lineB` 对照 handler 起止行。
- `get_real_minute_kline` 与 `get_tick_direction` 同在 `real_quote.pyc` 的 mandated 43/45 内
  ⇒ **改 try 归约会直接触碰 R75 mandate 的两支**，必须 `pyc_verify single` 先过再上 battery。

**跨批风险**
- a 类 34 与 inside-try 9、F-ADSORB/b 16 三面有交叠（§1.3、§4.3）；
  任何单一 edit 的 arm 都要跑 `battery + sstrict + adr73.py` 三件套，禁以少发射换全绿。
- ADR-1 的 `hunks_norm` 对「结构修好」是**惩罚性**的（§3.4）⇒ 判读回退时必须先看字节内容再下结论。

---

## §9 只读与纪律自证

- repo 内**本批零**创建/修改/删除；未执行任何 `git` 写操作；未运行 402 全量；未使用 `land75.py --apply`；
  未手改任何 `*OK.py`（探针仅 `compile(src, ok, 'exec')` 内存编译 / `marshal.loads` 读 pyc[16:]）。
  `git status` 仍显示的脏项（`.gitignore` 修改、`2026-09-29.md`、`test_repros/out_*`、
  `tools/`、`wiki/` 等 untracked）**均为本轮之前既有**，与 diag1 无关；HEAD 仍为 `78679fd0`。
- 单命令 <300s；长任务走 `center/launch.py`（DETACHED_PROCESS）；
  中文输出一律 `python -W ignore -X utf8`，文件一律 UTF-8 `newline='\n'`（禁 PowerShell `>` 写 UTF-16）。
- 跨批只读引用：`D:/Temp/opencode/r74gate/diag1/FACTS.md`（结构参照）、
  `D:/Temp/opencode/r74gate/center/build_{landed,absj,absj3,absj9,absjt,try7_9,try7_10d,try7_3}/`（Q3 对照臂产物）、
  `F:/Downloads/pythoncdc-main/.trae/specs/.../rounds/round74/batches/fix3/specs/{try7_3,try7_9,try7_10d}.json`、
  `round74/specs/fix1/absj.json` —— 均只读，未写入。
- 本区产物：**26 个探针 `.py`**（其中 diag1 主探针 `submech75 / inside75 / tick75 / q4575 /
  run_pycverify / patch_tick / d74_join`，其余为早期探索）+ `dump/` 20 文件 + 本 `FACTS.md`；
  **无 `specs/` 交付**（BRIEF_diag1 §4）。
