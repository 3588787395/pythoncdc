# FIX_B107 — if 臂内的 `while` 未被作为抽象节点交付：循环层丢失 + 体尾兄弟/环后兄弟被吞

轮次：Round 2 / 破口 B107（登记见 `REVIEW.md` §3.5）。执行人：round-2 修复 agent（工单 `rr-v3r01-f557fd`）。
判定尺：`scripts/pyc_verify.py`（**未修改**）。所有被判产物一律「先删 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」
重生成，**未手改任何 `*OK.py`**。`core/cfg/region_analyzer.py` **零改动**（字节校验见 §5）。

## 0. 落地标记（grep 用）

```
[R2-B107 修复·if 臂按循环入口认领抽象节点]
```

站点（全部在 `core/cfg/region_ast_generator.py`，行号为落地后当前字节，`grep -n` 原文可复现）：

| 行 | 站点 | 作用 |
|---|---|---|
| 24517 | 新方法 `_arm_loop_child_entry(block, region, branch)` | 认领谓词本体（六项 docstring ①-⑥ + C1/C2/C3） |
| 24595 | 新方法 `_r2_b107_block_is_outer_exit(block, region)` | 出口边归属判据 |
| 24625 | 新方法 `_loop_preheader_blocks(loop)` | 循环前导块识别 |
| 24911 | `_process_if_blocks` 预扫描：建 `_r2_b107_child_generate` | 认领登记 |
| 25002 | `_process_if_blocks` 块扫描：抽象节点派发分支入口 | 认领消费 |
| 25019 | 同分支的出口边归属（撤销非成员块的认领） | 环后兄弟交外层 |
| 25047 | 同分支的循环成员集标记（外层汇合块不认领） | b03 形不误吞兄弟 |

`grep -c "R2-B107"` = **7**；`grep -c "R2-B106"` = **4**、`grep -c "R2-B108"` = **5**（两条同批守卫未被触碰）。

## 1. 误分类（2-3 句）

分析器**已经**把 `while` 交付为 `LoopRegion` 并把它登记为父 `IfRegion` 的直接子区域（`child.parent is region`），
臂的 `then/else` 列表按原则 4 以**入口块**引用它；但 `_process_if_blocks` 的臂块扫描只对
for_iter_setup（R59）/TryExceptRegion/BoolOp-Ternary/嵌套 IfRegion 四类入口做抽象节点派发，
**唯独缺 LoopRegion 入口这一支** ⇒ 入口块被当普通顺序块展开，`while` 层凭空消失、
`break`/`return` 臂退化为 `pass`，`LoopRegion` 其余成员块（体尾兄弟、回边）在
`block in child_region_blocks and block not in child_entries` 处被静默跳过；随后
`_if_generate_then_branch` 的 children 派发也因 entry 已进入 `generated_blocks` 而失效。
即 **C3 守卫没闭合到 if 臂层 + 原则 1/3 被破坏**，与 B99 同一出口/汇合归属判据面。

## 2. 幻影循环证据：原始 vs 产物指令窗（修复前）

标本 `test_repros/round2/r2v3_b01_whiletrue_break_tail_in_if`（`_on_publish_after_trading_end` 同形）：

```
ORIG（_r2diag blocks f，31 块）              PROD（修复前，23 块，-8 指令）
B2  off4  POP_JUMP_FORWARD_IF_FALSE          B2  off4  POP_JUMP_FORWARD_IF_FALSE
       succ=[jump:B20(off80), fall:B3]               succ=[jump:B12, fall:B3]
B3  off6  NOP      ← 循环前导块 preds=[2]     B3  off6  LOAD_CONST 0   ← 直接落到体首
B4  off8  …POP_JUMP_FORWARD_IF_FALSE         B9  off18 LOAD_FAST THREAD_STATUS
       （from mod import… + if TH）          B10 off20 POP_JUMP_FORWARD_IF_FALSE → jump:B12
B12 off24 JUMP_FORWARD → B20  ← break        B11 off22 NOP → fall:B12   ← break 变 pass
B13 off26 LOAD_GLOBAL time …                 （无 B13-B19：sleep 调用体 6 条整体缺失）
B18 off76 POP_TOP                            （无回边）
B19 off78 JUMP_BACKWARD → B4  ← 回边         B12 off24 LOAD_GLOBAL get_bus  ← 环后兄弟
                                             （无 while 头、无 else、无 return None）
```
产物文本（修复前 `r2v3_b01…OK.py`）：`if is_end:` → `from mod import THREAD_STATUS` →
`if THREAD_STATUS: pass` → `event_bus = …`——**`while True:` 整层丢失**，与 REVIEW §3.1
语料 `_on_publish` 的 -8（break 1 + sleep 6 + 回边 1）完全同签名。语料
`_save_testds_to_csv` 的凭空 `while True:` + `else: return None` 属登记书 §3.2 的另一侧
（出口/sink 归属，见 §6）。

## 3. 现在的白名单谓词（读什么 / 不读什么）

`_arm_loop_child_entry`（认领）——五判据全真才认领：
(a) 成员关系 `LoopRegion ∈ region.children` 且 `child.parent is region`；
(b) 入口身份 `child.entry is block` 且 block ∈ 本臂块集；
(c) 臂间排斥 block ∉ 另一臂块集；
(d) 区域类型排斥 block 不是任何 TryExceptRegion/WithRegion 的 entry（沿用 R1 的 try/with 优先）；
(e) 出口归属 block 不是 `region` 或任一**祖先**区域的 merge_block。
祖先链从 `region` 起走（**不**从 block 自身所属区域起，避开 `[r1-b98-elsescope]`），
已访问集合保证终止。

`_loop_preheader_blocks`（原则 2）——`block ∈ loop.blocks` 且 `block is not entry/header` 且
所有前驱（自环除外）都 ∉ `loop.blocks` ⇒ 该块只能从区域外进入，属外层臂的单次入口语句
（b01/b02 的 off6 NOP 即此形），先由臂发射再派发循环，消除「体语句双发射」。

`_r2_b107_block_is_outer_exit`（C3 出口边）——块是 `region` 或任一祖先区域的 merge_block/exit。
命中即**不认领**：`_generate_region(LoopRegion)` 附带返回并登记的「循环出口之后的顺序代码」
其块不在 `loop.blocks` 内 ⇒ 撤销认领登记，交外层在其自身位置发射一次（b01/b02 的
`event_bus` 回到函数体层）；`loop.blocks` 内被误纳的外层汇合块同样跳过标记（b03 形）。

不读：语句条数/指令数上限、嵌套深度、文件名、函数名、opcode 偏移、任何发射后的 AST 文本。
无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 新方法；无新增 opcode 字面量。
§1.3 单向数据流：归属在归约那一刻（`_process_if_blocks` 预扫描 + 派发分支）一次成型。

## 4. 翻转与永久臂

| 项 | 修复前 | 修复后 |
|---|---|---|
| `r2v3_b02_whiletrue_break_no_tail` | failure 1/2 | **success 2/2** |
| `r2v3_b05_whiletrue_return_tail_in_if` | failure 1/2 | **success 2/2** |
| `r2v3_b01/b03` | 无 `while` / 兄弟丢失 | `while` + `break` + 体尾兄弟全部恢复；b01 仅剩 §6 的 import 重建伪影、b03 仅剩 §6 的环后兄弟 |
| 全部对照（b04/b08/b16/b17/b19 + a 族 + c 族） | success | **success 保持** |

新增永久臂（已入 `test_repros/round2/r2v3_probe_index.json`，本票 4 条，全部到档即绿）：

| 臂 | 钉住的判据分支 |
|---|---|
| `r2v3_b22_while_after_stmt_in_ifarm_break_tail` | 循环是臂的**非首块**（`bus = get_bus()` 之后）：入口身份 (b) + 环后兄弟出口归属 |
| `r2v3_b23_while_in_ifarm_no_arm_sibling` | **臂末循环且 if 之后无兄弟**：(e) 不命中时不得凭空造 `else`/`return None` |
| `r2v3_b24_while_in_ifarm_returntail_no_arm_sibling` | 臂内 `return` 收尾 + 无环后兄弟（break/return 两侧同判据） |
| `r2v3_b25_while_inside_for_body_control` | **宿主轴对照**：循环宿主是 for 体（非 if 臂）⇒ 守卫不得改变行为 |

索引读数（含新臂，62 臂）：

```
$ python -X utf8 scripts/pyc_verify.py batch --index test_repros/round2/r2v3_probe_index.json --json D:/Temp/rrv3/b107_index_after.json
files_total=62  units_success=105/126  success_rate=0.8333333333333334
files_by_status={'compile_error': 0, 'error': 0, 'failure': 21, 'success': 41}   elapsed_sec=2.1
```
（同批 58 臂读数：修复前 95/118、35 success / 23 failure → 修复后 **97/118、37 success / 21 failure**；
逐臂差集仅 `b02`、`b05` 两条 failure→success，**无任何臂变红**。）

## 5. 门禁全量读数

| 命令 | 基线 | 本次 | 结论 |
|---|---|---|---|
| `batch --index test_repros/round2/r2v3_probe_index.json` | 95/118，35/23（58 臂） | **97/118，37/21**（同 58 臂）；含 4 新臂 **105/126，41/21**（62 臂） | +2 文件 / +2 单元，零回退 |
| `batch --index test_repros/round1/r1_probe_index.json` | 108/110，44/2 | **108/110，44 success / 2 failure** | 保持 |
| `batch --index test_repros/round1/r1_regress_index.json` | 34/34 | **34/34，17 success / 0 failure** | 保持 |
| `single …/plugin_system_risk_calculation/__init__.pyc` | 41/43 | **41/43**；`_on_publish_after_trading_end` 由 `Different control flow` 改为 `Different bytecode`（循环层/`break`/体尾兄弟已恢复，仅剩 import 重建伪影），`_save_testds_to_csv` 仍 control flow | **未达 43/43**，见 §6 |
| `single …/plugin_system_realquote/real_quote.pyc` | 43/45 | **43/45**（get_real_minute_kline / get_tick_direction 未变） | 未跌 |
| `single site-packages/fly/common/future_contract_info.pyc` | 28/29 | **28/29**（check_user） | 未跌 |
| `single …/IQCommon/util/cgroup_utils.pyc` | 8/8 | **8/8** | 保持 |
| `single …/IQCommon/util/email_utils.pyc` | 4/4 | **4/4** | 保持 |
| `single …/IQCommon/logger/handlers.pyc` | 29/30 | **29/30**（`_target`，B99） | 保持（B99 未被顺带关闭） |
| `single …/fly/data/quotation.pyc` | 152/153 `get_fundflow_day` | **152/153，失败单元仍是 `<module>.get_fundflow_day`** | 未跌、单元未换 |
| `single …/IQCommon/data/finance.pyc` | 31/32 | **31/32**（`get_fields`） | 未跌 |
| `single …/plugin_system_trade/trade_live_broker.pyc` | 118/128 | **118/128** | 未跌 |
| `single …/fly/data/quote.pyc` | 85/92 | **85/92** | 未跌 |
| `pytest -q tests/{test_algorithm_correctness,test_deep_nesting_pressure,test_control_flow_completeness_matrix,test_complete_syntax_coverage,test_boundary_cases,test_core_functional}.py` | 2 failed / 277 passed / 2 xpassed | **2 failed / 277 passed / 2 xpassed**（同一两条：`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`TestBoundaryConditions::test_BOUNDARY_02_large_function`） | 保持 |
| `python -X utf8 -c "import core.cfg.region_analyzer, core.cfg.region_ast_generator, core.cfg.code_generator"` | ok | **ok** | — |
| `python -X utf8 -m compileall -q core` | ok | **ok** | — |

字节完整性：`region_ast_generator.py` **58576 行全 CRLF、bare-LF=0、恰 1 个前导 BOM**（补丁区未做整文件归一）；
`region_analyzer.py` 未改动（31914 行全 CRLF、单个前导 BOM、bare-LF=0，与本票开工前逐字节一致——
本票的误分类在**生成层的认领缺失**，§2 的 `_r2diag`/region dump 实测显示分析器交付的
`LoopRegion@8` 与 `child.parent is IfRegion@0` 均正确，故按工单授权只改 `region_ast_generator.py` 单文件）。

## 6. 未闭环如实登记（B107 未闭合）

1. **b01 与语料 `_on_publish_after_trading_end` 仅剩 `from <mod> import <name>` 在循环体内被重建为
   `THREAD_STATUS = ('THREAD_STATUS',)`**。实测该重建**先于本票存在**且与 if 臂无关：
   顶层 `def f(TH): while True: from mod import THREAD_STATUS; if TH: break; …` 在未打补丁的代码里
   同样产出 `THREAD_STATUS = ('THREAD_STATUS',)`。它是语句重建面的另一条破口，不属 B107 的认领判据面，
   本票未强行拉绿。
2. **b03（`while <cond>` 在 if 臂内）环后兄弟仍丢**：`LoopRegion@6.blocks` 把外层
   `IfRegion@0.merge_block`（off72）误纳为成员，而该块**同时**是内层 `IfRegion@10.merge_block`，
   祖先链判据 (e) 命中「本区域的 merge」即被循环自身消费；需区分「哪个区域的 merge 才是真出口」，
   属出口归属判据的第二侧（与 B99 同面），本票的 `_r2_b107_block_is_outer_exit` 只封了
   「非成员块」与「本臂/祖先汇合块」两支，b03 的这支未闭。
3. **b12 / b14 / b15 / b13 读数未变（仍 1/2）**，且实测其**首分歧签名不是** B107 的幻影循环：
   `b14` 首分歧 off10 `LOAD_CONST None;RETURN_VALUE`（臂的终态 sink）在产物里变成
   `JUMP_FORWARD → 单一尾 sink`——即「循环的两个隐式 return sink 塌成一条」的 **B99 签名**；
   `b12`/`b15` 同形（臂内 `return` 被写成 `break` / sink 互换）。b01/b02/b05/b03 四臂才是
   phantom-while / lost-tail-sibling 签名。按工单「先验证签名再认领」，这四臂归 B99 的出口/sink
   归属轴，本票未据 REVIEW 的备注强行认领，也未用任何特判换绿。
4. **新臂发现的一条邻接形**：`if …: / else: while True: …`（循环在 **else 臂**且臂末无兄弟）今日
   发射重复的 `if TH: break`（else 臂扫描先把臂块当 standalone 下探子区域，再派发循环）。
   已按实测把该形换成同判据可覆盖的 b23（then 臂、臂末无兄弟），else 臂这支如实留档，未混入本票。

## 7. 声明

**「代码已落地」**：认领谓词 `_arm_loop_child_entry`、前导块判据 `_loop_preheader_blocks`、
出口边归属判据 `_r2_b107_block_is_outer_exit` 与 `_process_if_blocks` 的预扫描 + 派发分支
已在 `core/cfg/region_ast_generator.py`（7 个 `[R2-B107 修复·if 臂按循环入口认领抽象节点]` 站点，行号见 §0），
`region_analyzer.py` 零改动。证据：b02/b05 两臂转绿、b01/b03 的 `while` 层与 `break`/体尾兄弟已按
ORIG 同形恢复、4 条新永久臂全绿、r2v3 电池 95/118→97/118 且**无臂变红**、Round-1 两电池
（108/110、34/34）、9 个哨兵 pyc、pytest 277/2/2、import/compileall 全部零回退。

**B107 尚未闭环**：`plugin_system_risk_calculation/__init__.pyc` 仍 **41/43**（非 43/43），
剩余分歧为 §6 的四条独立判据面（import 语句重建、b03 的 merge 归属第二侧、B99 的 sink 塌缩、
else 臂 standalone 下探）。未使用即时否决形（无名字/偏移/计数/深度特判，无 AST 文本手术）。
