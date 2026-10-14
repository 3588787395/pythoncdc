# FIX_B106 — except 处理器尾 `POP_EXCEPT + JUMP_BACKWARD`（continue）的跨区出口认领

轮次：Round 2 / 破口 B106（登记见 `REVIEW.md` §3.4）。执行人：round-2 修复 agent（工单 `rr-v3r01-f557fd`）。
判定尺：`scripts/pyc_verify.py`（**未修改**）。所有被判产物一律「先删 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」
重生成，**未手改任何 `*OK.py`**。

## 0. 落地标记（grep 用）

```
[R2-B106 修复·处理器尾回边按循环入口归属]
```

落地站点（全部在 `core/cfg/region_ast_generator.py`，行号为落地后当前字节）：

| 行 | 站点 | 作用 |
|---|---|---|
| 23294 | 新方法 `_except_tail_backedge_is_loop_continue(block, loop, region)`（六项 docstring ①-⑥） | 白名单谓词本体 |
| 23370 | `_handler_backedge_is_explicit_continue(hb, region=None)` 重写 | 委托谓词 + 隐式迭代排除 |
| 26577 | `_is_continue_like`（登记站点，当前字节 26564 起）LOOP_BACK_EDGE 分支 | 白名单穷举不再否决「回边前有帧簿记」的块 |
| 30011 | Pattern TE handler 出口认领调用点（改传 `region`） | 在区域上下文中消费同一谓词 |

`core/cfg/region_analyzer.py` **零改动**（31914 行全 CRLF、单个前导 BOM，与开工前逐字节一致）。
B108 的 5 个 `[R2-B108 …]` 站点（现字节行 19162 / 23887 / 37931 / 38326 / 38458）未被触碰，
`grep -c "R2-B108"` 仍为 **5**。

## 1. 误分类本身（2-3 句）

处理器尾块 `POP_EXCEPT + JUMP_BACKWARD→循环入口` 在两处白名单判据里都被错认：
`_is_continue_like` 对 `LOOP_BACK_EDGE` 角色做「块内指令穷举」时把 `POP_EXCEPT` 当作用户语句 ⇒ 判为非 continue-like；
`_handler_backedge_is_explicit_continue` 则把「回边」隐含限定为**块末指令**且要求该块就是
`loop.back_edge_block`、目标等于 `loop.header_block` —— 而 `while not stop:` 形里循环登记的 `back_edge_block`
是环尾的 `POP_JUMP_BACKWARD_IF_FALSE` 复验块、`header_block` 是体首 NOP，continue 的回边目标是**循环的
条件入口块**，三条件全不成立 ⇒ 该块落到「普通顺序后继」分支，发射成 `JUMP_FORWARD` 直落 try 之后的语句
（`continue` 蒸发为 `pass`，循环不再迭代）。修正后的分类只读三条白名单输入：块末 opcode 为无条件回跳、
回跳目标满足 `LoopRegion.is_block_entry`（区域成员关系）且是该块唯一普通后继（后继关系）、
块内余下指令全为异常帧簿记（`_W13_FRAME_OPS ∪ 噪声`，且含 `_W13_NORMAL_BAN_OPS` 的异常路径标记）并属于
`region.except_handlers` 登记的 except 臂（异常表归属）。§1.3 单向数据流：定类发生在归约那一刻，
无发射后文本改写。

## 2. b06 ↔ b08 具体 before/after 字节码行

b08（对照，处理器写 `pass`，今日与修复后均 success）：处理器尾 `POP_EXCEPT` 之后**没有**回边，
块以落穿结束 ⇒ 正常顺序边，正确。

b06（标本）原始字节码（`_r2diag blocks` on `.pyc`）：

```
ORIG B19 off80 last=POP_EXCEPT  succ=['fall:20'] preds=[18]
ORIG B20 off82 last=JUMP_BACKWARD succ=['jump:1'] preds=[19]     # B1=off2 `LOAD_FAST stop` = 循环条件入口
```

修复前产物（判据原文 failure 1/2）：

```
PROD B20 off82 last=POP_EXCEPT  succ=['fall:21'] preds=[19]
PROD B21 off84 last=JUMP_FORWARD succ=['jump:25'] preds=[20]     # B25=off94 `PUSH_NULL,LOAD_FAST…` = try 之后的 w(...) 语句
（ORIG 循环头 preds=[15,37] → PROD preds=[15]，处理器边丢失）
```

修复后产物：

```
PROD B20 off82 last=POP_EXCEPT    succ=['fall:21'] preds=[19]
PROD B21 off84 last=JUMP_BACKWARD succ=['jump:2']  preds=[20]    # 与 ORIG 同形：回边重指循环入口
```

语料锚点 `site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` /
`<module>.PluginRiskCalculation._save_testds_to_csv`：修复前 `off208 POP_EXCEPT → off210 JUMP_FORWARD→off220`
（try 之后语句，`except Empty` 退化为 `pass`）；修复后产物 `__init__OK.py` 该处理器已还原为
`except Empty:` + `continue`（B106 签名消失，见 §5 的剩余分歧）。

## 3. 现在的白名单谓词（读什么、不读什么）

`_except_tail_backedge_is_loop_continue(block, loop, region=None)`：

1. `block` 终止 opcode ∈ `BACKWARD_JUMP_OPS` 且 ∉ `CONDITIONAL_JUMP_OPS`（两个既有集合，**未新增任何 opcode 字面量**）。
2. `LoopRegion.is_block_entry(target)`（`header_block`/`entry`/`condition_block` 之一）+ `successors − exception_successors == {target}`。
3. `block.instructions[:-1]` 全部 ∈ `_W13_FRAME_OPS ∪ _W13_NOISE_OPS ∪ NOISE_OPS`，且至少一条 ∈ `_W13_NORMAL_BAN_OPS`
   （该集合的既有定义即「正常路径绝不出现的异常帧标记」），且块 ∈ `region.except_handlers[*][2]`（异常表登记的 except 臂）。
4. `_handler_backedge_is_explicit_continue` 在 1-3 之后再排除 `_handler_backedge_is_natural_loop_iteration`
   （hb 之后循环体内无待执行普通语句块 ⇒ 隐式迭代，不补 Continue）。

不读：语句条数上限、嵌套深度、函数名/文件名、偏移阈值、任何发射后文本。C1（只消费 blocks/out_edges/exception_table）、
C2（不窥子区域内部）、C3（跨区 continue 目标显式认领）逐条对应 §1.5。

## 4. 永久臂（新增两条，已入索引）

| 臂 | 形状 | 判据分支 | 今日读数 |
|---|---|---|---|
| `r2v3_b20_except_continue_after_pop_except.py` | `for x: try: v=w(x) except ValueError: continue` + try 后仍有 `w(v)` | 谓词 1-3 命中 + 自然迭代排除为 False ⇒ 发射 `continue` | **success 2/2** |
| `r2v3_b21_except_pass_iteration_backedge.py` | `for x: try: w(x) except ValueError: pass`（try/except 即循环体末条） | 字节码同形（`POP_EXCEPT@56 → JUMP_BACKWARD@58→FOR_ITER@6`），自然迭代排除为 True ⇒ **不得**发射 `continue` | **success 2/2** |

两臂的处理器尾回边形状逐条相同，唯一区别是「循环体内是否还有待执行普通语句块」——正是本守卫现在划出的界线。

索引读数：

```
$ python -X utf8 scripts/pyc_verify.py batch --index test_repros/round2/r2v3_probe_index.json --json D:/Temp/r2_b106.json
files_total=58  units_success=95/118  success_rate=0.8050847457627118
files_by_status={'compile_error': 0, 'error': 0, 'failure': 23, 'success': 35}
```

## 5. 门禁全量读数

| 命令 | before | after | 结论 |
|---|---|---|---|
| `batch --index test_repros/round2/r2v3_probe_index.json`（56 臂基线） | 90/114 units，32 success / 24 failure | **95/118 units，35 success / 23 failure**（含新增 2 臂 4 单元） | 去掉新臂即 91/114、33/23：+1 文件 / +1 单元，**零回退** |
| B106 六臂 | 全 failure | `r2v3_b07` **success 2/2**；b06 1/2、b09 2/3、b10 1/2、b11 1/2、b18 1/2 仍 failure | 未达「六臂全绿」，原因见 §6 |
| 对照 `r2v3_b08` / `r2v3_b19` | success | **success 2/2 保持** | 过伸展检查通过（`pass` 形与嵌套 while 形未被误认领） |
| 其余对照（a 族 / c 族 / m 族 / c 类） | 全 success | **全部保持 success** | 无过伸展 |
| `batch --index test_repros/round1/r1_probe_index.json` | 108/110，44/2 | **108/110，44 success / 2 failure** | 保持 |
| `batch --index test_repros/round1/r1_regress_index.json` | 34/34 | **34/34，17 success / 0 failure** | 保持 |
| `single …/plugin_system_risk_calculation/__init__.pyc` | 41/43 | **41/43**（失败单元仍是 `_on_publish_after_trading_end`、`_save_testds_to_csv`） | 未达 42/43，见 §6 |
| `single site-packages/fly/common/future_contract_info.pyc` | 28/29 | **28/29** | 保持 |
| `single …/plugin_system_realquote/real_quote.pyc` | 43/45 | **43/45** | 保持 |
| `single site-packages/IQCommon/util/cgroup_utils.pyc` | 8/8 | **8/8** | 保持 |
| `single site-packages/IQCommon/logger/handlers.pyc` | 29/30 | **29/30** | 保持 |
| `single site-packages/fly/data/quotation.pyc` | 152/153，失败单元 `get_fundflow_day` | **152/153，失败单元仍是 `<module>.get_fundflow_day`** | 未跌、单元未换 |
| `pytest -q tests/{test_algorithm_correctness,test_deep_nesting_pressure,test_control_flow_completeness_matrix,test_complete_syntax_coverage,test_boundary_cases,test_core_functional}.py` | 2 failed / 277 passed / 2 xpassed | **2 failed / 277 passed / 2 xpassed**（同一两条：`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`TestBoundaryConditions::test_BOUNDARY_02_large_function`） | 保持 |
| `python -X utf8 -c "import core.cfg.region_analyzer, core.cfg.region_ast_generator, core.cfg.code_generator"` | ok | **ok** | — |
| `python -X utf8 -m compileall -q core` | ok | **ok** | — |

字节完整性：`region_ast_generator.py` 现 58358 行**全 CRLF**、bare-LF=0、恰 1 个前导 BOM（补丁区未做整文件归一）；
`region_analyzer.py` 未改动。

## 6. 未闭环如实登记（B106 的 continue 认领已修，五臂仍被**第二条分歧**卡住）

逐臂实测第一分歧（修复后，`_r2diag diff`）：

* `r2v3_b06` / `…_save_testds_to_csv`：`except …: continue` 已按 ORIG 同形发射（§2 的 off82/84 行对），
  剩余分歧是 B107 的锚点形状——凭空 `while True:` 外层 + 凭空 `else: return None` + 第二 while 的体尾兄弟
  （语料里是 `time.sleep(0.01)`）丢失。⇒ 语料单元须 B107 落地才能转绿，故 **41/43 而非 42/43**。
* `r2v3_b09` / `r2v3_b18`：处理器回边已正确（b18 的 `off102 POP_EXCEPT + off104 JUMP_BACKWARD<BACK>` 落在 equal 段），
  剩余分歧是环出口 sink 的归属：ORIG `break` 的 `JUMP_FORWARD→LOAD_CONST None;RETURN_VALUE` 在产物里变成
  顺序落入 + 重复 sink（b09 +3 指令、b18 +3 指令），属 §7 的 sink/出口归属族（B99/B107 判据面），非处理器 continue 认领。
* `r2v3_b10`（try 套 try + finally）/ `r2v3_b11`（with 宿主）：修复后产物里**整个 try/except 未被作为 TryRegion 交付**
  （b10 产物无 try、b11 把 handler 摊平成 `if ValueError: pass` 后在 with 体层挂一条 `continue`），
  Pattern TE 认领点根本未被到达（插桩 `[DBG explicit_continue]` 零命中）。这是 try 区域交付缺陷，另一条判据面。
* `r2v3_b13_except_break_in_while`（处理器里 `break`）：其出口是 `POP_EXCEPT + JUMP_FORWARD→区域外`，
  走 30030 起的 Round6-B29 break 分支（`find_enclosing_parent((LoopRegion,))` 认领），与本票的**回边**谓词无交集 ⇒
  按工单指示留给 B107/后续票，未强行拉绿（读数 1/2 未变）。

## 7. 声明

**「代码已落地」**：白名单谓词 `_except_tail_backedge_is_loop_continue` 与三处接线已在
`core/cfg/region_ast_generator.py`（4 个 `[R2-B106 修复·处理器尾回边按循环入口归属]` 标记站点，行号见 §0），
`region_analyzer.py` 零改动。证据：b06 与语料 `_save_testds_to_csv` 的 `POP_EXCEPT + JUMP_BACKWARD→循环入口`
边已按 ORIG 同形恢复（§2）、b07 转绿、新臂 b20/b21 双绿（同形状下 continue 与隐式迭代被区分开）、
b08/b19 两条对照与 r1 两电池（108/110、34/34）、6 个哨兵 pyc、pytest 277/2/2 全部零回退。

**B106 未闭环**：六臂仅 1 臂转 MATCH，`plugin_system_risk_calculation/__init__.pyc` 仍 41/43
（`_save_testds_to_csv` 的第二分歧 = B107 的循环交付/凭空 while-else/体尾兄弟丢失）。
未使用任何新增 opcode 字面量、语句计数上限、深度上限、per-function/per-file 例外或发射后文本改写来换绿。
