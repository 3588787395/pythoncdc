# Round 65 — OUTCOME

## 1. 本轮形态

18 支 partial（57 个缺陷函数）按缺陷函数数排序后分 6 批（diag0-diag5）由 6 个只读诊断代理并行
诊断，各自在私有工作区 `D:/Temp/opencode/r65gate/diag{0..5}` 建臂实测，再由主代理集中验证与回退。

本轮的形态变化来自**代理预算**：diag2 / diag3 / diag4 三支都在 150 轮子代理上限处中断，
diag2 的 `FACTS.md` 实测一节停在「（进行中）」，diag3 与 diag4 根本没写报告。三批的候选 spec
与逐臂 dump 留在各自工作区，其结论由主代理按下文的集中实测重新判定（不是采信中断前的自述）。
diag1 交出了本轮唯一的「修到完全 OK」候选，diag5 交出 twins 候选。

批次起点缺陷函数数排序见 `logs/r65_targets_view.txt`；靶清单 `logs/partial18.txt`（18 支）。

## 2. 修到完全 OK 的 pyc（本轮 mandate：至少一支，实测一支）

| pyc | 轮初 | 轮末 | 依据 |
|---|---|---|---|
| `site-packages/IQCommon/graph.pyc` | partial 30/31 96.77% | **ok 31/31 100.00%** | 官方 `single`（G1）+ 严格尺 **34/34**（`missing=0 extra=0`），`graphOK.py` 由工具链重写 |

缺陷本体（diag1 §1.1-§1.6）：`_process_task_queue` 的 `_process_task_queue [378,378,1,118]` 是
**两个「try 体末条 `return None`」被发射到 try/except 之后**——一个变成父层兄弟槽的多余语句
（产物 L399），一个整块丢失（`Region@1114` 未被发射）。diag1 用异常表实测证明 CPython 3.11 把
try 体尾部的 `return` 发射在保护跨度**之外**（`[560,566)->570` 与 `[1108,1114)->1118` 都不覆盖
`@566`/`@1114` 的 `LOAD_CONST None; RETURN_VALUE`），因此「并进 `ast.Try.body` 末尾」同时复现
指令流与保护跨度。源码手术台（§1.3）三种变异都归零，`drop 399` 单独归零的是另一件事——这条
证明判据方向充分而非凑数。

## 3. 落地集（5 处编辑，全部先对 R64 落地字节单变量实测）

```
core/cfg/region_ast_generator.py  3 103 668 -> 3 123 069 B  4 edits +260 行
                                  BOM 保留，CRLF 50 409，裸 LF 0，sha e0cf887ecb7430d662c28ca84c40f291a2087c2a364b9df648cd09d3ca871444
core/cfg/region_analyzer.py       1 725 369 -> 1 727 576 B  1 edit  +29 行
                                  无 BOM，CRLF 27 664，裸 LF 0，sha 9fd4618b7bd2647f111f8ce8138ba9f3bbd3d52036d1c27c04b6748c18acb263
```

`land65.py land --spec … --mirror mirr_m65 --apply` 逐条重放：replay == 实测镜像字节；
`closeout65.py landproof mirr_m65` ⇒ 33 个 core 文件 same=33 diff=0。
合并集由 `mkfinal65.py`（按落地字节偏移排序 + 链式 anchor 唯一性）产生，`mbuild65.py` 建镜像时
断言「镜像==工作树、BOM 不变、行尾统一、插入行数==spec 声明」。

标记行号是**最终字节**上的位置（不是 spec 锚点的旧行号）：

| 落地行号 | 标记 | 来源 | 识别条件 / 归约方式 / AST 映射（摘要，全文在代码注释里） |
|---|---|---|---|
| L11584、L17424 说明块 | `[R65-D5-A]` | diag5 a | `_generate_if` 的汇合块为空 ⇒ 该 if 的 then 侧只欠一条 `return`；兄弟入口整条 if 由同层身份找回 |
| L17387、L11611 说明块 | `[R65-D5-B]` | diag5 b | `_if_generate_normal` 的入口提取门控：`region.entry is not cond_block` 的同层结构身份，缺一支则 twins 只回到 20/21 |
| L26483 | `[R65-diag1-A try-body-tail-return-none]` | diag1 A | 单块 BASIC 兄弟区域 `has_trailing_return_none` 且 `try_offset_end < min(handler_entry_blocks)` 且 `post_try` 为空 ⇒ 追加进 `ast.Try.body` 尾部并登记认领 |
| L36109 / L36193 / L36254 | `[R65-d3 C1a]`/`[C1b]`/`[C1c]` | diag3 c1 | 单三元 f-string 区域：前缀里跨块待定被调对象的压栈链剔除、链尾自包含插值段归约 + conversion 回填、f-string 作为待定调用实参时整体归约为语句调用 |
| analyzer L25599 | `[R65-diag4 n1 operand-rejoin exemption]` | diag4 n1 | `current` 的某条后继末指令属于 `BOOLOP_CHAIN_JUMPS` 且目标 `is T` ⇒ `current` 是本算子 run 的第 n 个操作数（`and` 子链头），不 pop、不 break，链继续扩展 |

禁止形态核查：5 处编辑全部为同层次结构身份判据（`region.entry is …`、`parent is …`、
`try_offset_end < min(handler_entry)`、后继边的跳转目标 `is T`），无按函数名/文件名/偏移/阈值的
启发，无 `region.entry in r.blocks` 型跨区域跨层次包含。

未采纳（集中在 §5 与 EVIDENCE 里给了逐条读数）：diag2 `c1…c1f` 六臂、diag3 `c2`/`c3`、
diag4 `n2`/`n3`、diag0 `stripdbg`（13 处 `import os as _os_dbg_*` 清理，纯删除 −78 行，本轮不与会
改变产物字节的行为补丁混在一次落地里）。

## 4. 门禁（严格串行，全部实测；每条命令 <300 秒）

| 门禁 | 读数 |
|---|---|
| G0 语法/字节 | 两文件 `py_compile` + `ast.parse` OK；BOM/CRLF 形态保持（裸 LF 0）；`landproof mirr_m65` ⇒ 33/33 core 文件与工作树相同 |
| G1 `single` 靶 | `IQCommon/graph.pyc` → decompile_status **ok 31/31 100.00%**，`missing_in_decomp=[]`、`extra_in_decomp=[]`，`graphOK.py` 由工具链重写 |
| G2 金丝雀 | `fly/data/quotation.pyc` 官方 **143/143**、严格 **148/150** 且缺陷集逐字未变（`change_his_to_forward #250`、`get_trend #10`）；`fly/common/market_time.pyc` 官方 **10/10**、严格 10/10 |
| G3 `batch --index pyc_index.json --all --round 65` | 402 verified / **ok 385** / partial 17 / **failed 0**（1 m48 s；首跑见 §4.1） |
| G4 `stats` | total_functions **5746**、matched_functions **5693**、cumulative_match_rate **99.08%** |
| G4′ 严格尺（22 支仓库产物） | 合计 **915/994**；`graph` 34/34、`klinedata` 56/63、两支 twins 21/22 与 26/27、`trade_live_broker` 104/118、`quote` 74/89（与落地同）；全部 22 份产物 sha 与实测镜像产物相同 |
| G5 402 支 A/B（落地前 dump vs 落地后 dump） | `SAME=396 IMPROVED=4 REGRESSION=0 MOVED=2 ERR=0`；产物逐字节比对 **396 相同 / 6 变化**，指令缺口 `Σ|orig-decomp| 545 -> 418` |
| G6 电池（落地字节，19 项） | matched 61 -> **62**/68，全清文件 14 -> **15**，worse-than-landed **0** |

### 4.1 G3 首跑的三支瞬时 failed（如实记录，不作为改动结论）

第一次 `batch --all --round 65` 把 3 支记成 `failed`：`IQCommon/common/__init__.pyc`、
`IQData/enumerate.pyc`、`IQData/fly_enum.pyc`，错误文本 `RuntimeError: Failed to decompile`
（`pycdc.py:719`，即 `decompiler.decompile()` 返回假）。同三支在当前字节下由 `h62.py run`
读出 1/1、14/14、1/1 且产物 `compile()` 通过，`single site-packages/IQData/fly_enum.pyc` 亦为
`ok 1/1`；重跑 `batch --all` 后三支全部回来、`failed=0`。**未定位到根因**（候选是同目录
`__pycache__`/产物写入竞争），入库为 R66 待查项：`batch` 路径存在一次性的 `Failed to decompile`，
`stats` 只有在复跑后才可信。发布数字取自复跑。

## 5. 附带改善与代价（逐支，官方尺）

| 支 | 轮初 | 轮末 | 归属 |
|---|---|---|---|
| `IQCommon/graph.pyc` | 30/31，`_process_task_queue [378,378,1,118]` | **31/31，残余清空** | diag1 A |
| `IQCommon/util/common_func.pyc` | 19/21 | **20/21**（`get_kline_time_by_section [210,190,0,84]` 恢复） | diag5 A+B（成对，缺一支只到 20/21 的另一半） |
| `IQData/utils/common_func.pyc` | 22/24 | **23/24**（同名函数恢复，严格尺 25/27→26/27） | 同上 |
| `IQEngine/.../trade_live_broker.pyc` | 105/119 | **106/119**（`market_fund_transfer [94,77,1,41]` 清空；`etf_purchase_redemption [377,355,2,100]→[377,369,1,37]`） | diag3 C1 |
| `IQCommon/api/klinedata.pyc` | 42/45，`get_multiminute_his_data [479,478,**5**,16]` | 42/45，同函数 **jumpdiff 5→3**；严格尺 54/63→**56/63**（`get_kline_by_date_new`、`get_multiminute_his_data_by_date` 两支 `target_diff` 清空） | diag4 n1，收回 R64 的实测代价 |
| `fly/data/quote.pyc` | 70/81 | 70/81（计数不变）：`get_price [230,188,0,227]→[230,**228**,0,224]`、`load_get_price [171,136,1,167]→[171,**167**,2,164]` | diag3 C1 |

**本轮唯一实测代价**：同一支里 `load_bars_from_hundsun [477,470,0,464] → [477,524,3,507]`
（缺 7 条变**过冲 47 条**、jumpdiff 0→3）。逐字节核对：原始 `load_bars_from_hundsun` code object
的日志常量 `'调用函数load_bars_from_hundsun，参数为：stocks='` **只出现 1 次**，而落地产物里那条
被压平的 f-string 语句**已经出现两次**——即「同一条日志语句重复发射」是 R64 遗留缺陷，diag3 的
C1 把这条重复项从「裸 f-string」放大成「完整 `debug(...)` 调用 + 其后 3 条语句」，于是 +47。
采纳理由：该函数官方计数与严格尺都不变（`quote` 严格 74/89 两臂相同），同支另两个函数分别收窄
40 与 31 条，全语料 `Σ|Δ|` 仍 −127；重复发射本体作为 R66 头号 f-string 线索移交（§6.1）。

严格尺 18 支合计 700→706（+6），**新增缺陷 0 项**（逐文件缺陷集取差，见 `logs/EVIDENCE.md` §D）。

残余 17 支 partial 清单：`logs/partial17_after_r65.txt`。

## 6. 移交下一轮的线索

1. **f-string 重复发射本体**（新）：落地字节下 `fly/data/quote.pyc::load_bars_from_hundsun`
   把同一条 `self.log.quote.debug(f'调用函数…')` 发射两次（原始常量 1 次），站点在
   `_generate_ternary()` 的 `merge_ctx == 'fstring'` 分支（R65 落地后 L36109 起）。
   最小复现 `test_repros/round65_diag2/fs2.pyc`（v1…v8 矩阵，9 行源码；`v5` 无三元对照 14/14）。
2. `diag1 §2.2 logger::write_logging_thread`：`IfRegion@368` 归属正确但被排到回边之后，
   `if q:` 是**现场合成**的（无 IfRegion），合成通道没有 R64-B1 的兄弟汇合入口收口。
   判据：内联合成测试的 then 区间 = 同层兄弟区域 entry ∈ (owner_block.test_offset, jump_target)；
   先在 `r64d5_contsink.pyc::probe`（122/122 + jumpdiff=1，同族）单点验证。
3. `diag1 §3 matcher::match`：orig[207:519] 312 条与产物尾部 324 条 similarity **0.9748**、
   两处 `JUMP_FORWARD↔JUMP_BACKWARD` 翻转 ⇒ 纯换位；需要的同层判据是「父序列按兄弟区域
   `entry.start_offset` 升序发射」，但 `ast_*` dict 不携带来源块 entry，实验方案（`_stmt_origin`
   只写不读 + 单次稳定排序）见 §3.1。`realtime_event_source::clock_worker` 同因
   （112 条位移 + 一条**空** `elif check_trading_time(...)` 臂，值 18 条，删它不减任何大 hunk）。
4. `diag1 §5 api_base::get_history_df`：真缺 24 条 = `if not tmp_dividends:
   tmp_dividends = engine_obj.basic_data_handler.get_dividend(symbol, None)` 的 guard 整个消失
   （产物里该函数内 `get_dividend` 命中 0 次）。可检验判据（`IfRegion.then` 单块、唯一语句
   `Assign(target=T)`、`T` 在同层下一条语句被 LOAD、test 是 `UnaryOp(Not, T)`）与它必须先在
   `r64d2_valuectx_consumer.pyc`（2/2 全绿 witness）上不退的证据要求，都在 §5.1。
5. diag4 的 `n2`（字面执行 R64 移交判据）与 `n3`（cfg-entry-value-diamond 豁免）两臂**未经集中
   实测**（该代理中止于报告之前，dump 只有 `n2_qh`/`n3*`）；diag3 的 `c2`、diag2 的 `c1b…c1f` 同理。
   下一轮若要重提，须按 §4 的门禁重新单变量实测。
6. 技术债（diag0 已量化，本轮未落地）：`region_ast_generator.py` 里 13 处
   `import os as _os_dbg_*` 调试导入（补丁后 `_os_dbg` 行数 26→0，−78 行）。diag0 自测
   402 支 `SAME=402 / MOVED=0 / ERR=0`、电池 SAME=19、金丝雀 SAME=4，**主代理未复测**；
   须作为独立一轮、以「产物 402 支逐字节相同」为唯一门禁落地。
7. `batch` 路径一次性 `Failed to decompile`（§4.1）未定位，复跑前 `stats` 不可信。

## 7. 归档

`rounds/round65/`：`OUTCOME.md`（本文件）、`batches/diag{0..5}/`（每批 FACTS/ANALYSIS/BRIEF +
specs + dump + 选录 logs + 靶/电池/金丝雀清单 + synth 复现，含未采纳臂与其读数）、
`logs/EVIDENCE.md`（集中验证全记录 A–F）、`logs/`（G0-G6 原始输出与四份中心记录、
列表文件、中心实测工具）、`specs/`（合并后的落地 spec）。
最小复现入库 `test_repros/round65_diag{1,2,5}/`（仓库惯例只入库 `.py`，`.pyc` 被 .gitignore 排除；
电池实跑前用 `py_compile` 现编）。
