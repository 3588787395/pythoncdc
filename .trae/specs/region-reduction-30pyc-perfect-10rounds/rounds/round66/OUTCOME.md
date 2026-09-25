# Round 66 — OUTCOME

## 1. 本轮形态

17 支 partial（53 个缺陷函数）按缺陷函数数排序后分 6 批（diag1-diag6）由 6 个只读诊断代理并行
诊断，各自在私有工作区 `D:/Temp/opencode/r66gate/diag{1..6}` 建臂实测，再由主代理集中验证与回退。
靶清单 `logs/all17.txt`（17 支），批次划分见各批 `batches/diagN/targets.txt`。

本轮的中断情况与 R65 同类：**diag2 与 diag3 两支在 150 轮子代理上限处被杀**（见 memory
`project-subagent-turn-cap`）。两批都在中断前写完了 `FACTS.md` 与候选 spec，逐臂 dump 留在各自
工作区；其结论由主代理按下文 §5 的集中实测重新判定（不采信中断前的自述），并且主代理替
diag2 补完了它没跑完的 402 全量扫描、替 diag3 补完了 402 分片。

## 2. 修到完全 OK 的 pyc（本轮 mandate：至少一支）

| pyc | 轮初 | 轮末 | 依据 |
|---|---|---|---|
| `site-packages/IQCommon/util/common_func.pyc` | partial 20/21 95.24% | **ok 21/21 100.00%** | 官方 `single`（G1）+ 严格尺 **22/22**，`common_funcOK.py` 由工具链重写 |

缺陷本体（diag6 §1）：`get_kline_by_multi_count_code` 的 for_iter_setup 前置语句段把
`del freq_k_minute[0]` 吞掉——该方法（`_loop_extract_for_iter_pre_stmts`）的终止符集合里有
`STORE_*`/`STORE_SUBSCR`/`STORE_ATTR`/`POP_TOP`，**唯独缺 `DELETE_*`**，于是 DELETE 前的 LOAD 段
留在缓冲里被下一条语句的归并吞掉。同文件的兄弟方法 `_loop_extract_self_loop_stmts` 与
`_generate_stmts_from_instrs` 各有一份 DELETE 终止符（落地字节 L5706 / L8931 附近，另 L2856
一份），被改的这条是异类，所以判据是「同一条直线块语句流的同一层次语句边界」，不是为某个
函数名开的洞。最小复现 `test_repros/round66_diag6/r66_delrepro.py`（落地 1/3 → 2 项归零 → 3/3）。

## 3. 落地集（2 个文件，8 处编辑，+316 行）

```
core/cfg/region_ast_generator.py  3 123 069 -> 3 140 634 B  7 edits +217 行
                                  BOM 保留，CRLF 50 626，裸 LF 0，sha256 3db80082b87ecca06e8c…
core/cfg/region_analyzer.py       1 727 576 -> 1 734 099 B  1 edit  +99 行
                                  无 BOM，CRLF 27 763，裸 LF 0，sha256 0e9740cc1836f3201312…
```

两文件 `py_compile` + `ast.parse` 均 OK。`land66.py land --spec … --mirror center/mirr_m66e --apply`
逐条重放：两份都打印 `replay == measured mirror bytes: OK`，落地后 `equals measured mirror=True`；
`closeout66.py landproof mirr_m66e` ⇒ **33 个 core 文件 same=33 diff=0**（电池跑的就是落地字节）。
合并集由 `mkfinal66.py`（按落地字节偏移排序 + 链式 anchor 唯一性断言）产生，`mbuild66.py` 建镜像时
断言「head 镜像==工作树字节、BOM 不变、行尾统一、插入行数==spec 声明」。

标记行号是**最终字节**上的位置（不是 spec 锚点的旧行号）：

| 落地行号 | 标记 | 来源 | 识别条件 / 归约方式 / AST 映射（摘要，全文在代码注释里） |
|---|---|---|---|
| generator L7219 | `[R66-diag6-A for-iter-delete-terminator]` | diag6 | for_iter_setup 前置段中 `DELETE_SUBSCR`/`DELETE_ATTR` 与既有 `STORE_*`/`POP_TOP` 同层次同粒度 ⇒ 交 `_build_delete_stmt` 归约为 `Delete(targets=[Subscript|Attribute(ctx='Del')])`；归约失败则缓冲原样保留（无新增抑制路径） |
| generator L16876 | `[R66-diag1 E1 单测试空臂不得吞并 if/else 之后的汇合块]` | diag1 | 把同一条「无语句」过滤器（`_noise_ops` ∪ `JUMP*`）原样作用到本区域自己的 `else_blocks` ⇒ else 含语句，且 `chained_compare_blocks` 为空 ⇒ 源码只能是 `if cond: pass` + 非空 else；返回 False 后 merge_block 不再被 `_merge_then_stmts` 并入，回到父序列发射一次 |
| generator L17055 | `[R66-d2 P4] 链首前缀赋值的同层唯一归属守卫` | diag2 | 候选表达式区域自身的 `blocks` 已全部登记在 `self.generated_blocks`（实测快照 mask=GGGG 而 `id(region)` 不在 `_generated_regions`）⇒ 块级已认领即不再二次 own；与循环里既有的 `_generated_regions`/`_generating_regions` 守卫同一不变量，只是把「已认领」从区域 id 换成区域自身块 |
| generator L26644 | `[R66-diag5-B try-tail-unprotected-else]` | diag5 | try 体尾部落在保护跨度之外的 `else` 语义块：经 `self.region_analyzer._w11_unprotected_else_candidate(try_region, block)`（analyzer L10360，既有通道）判定 ⇒ 语句归 `ast.Try.orelse`，映射 `try/else` 而非 try 之后的兄弟 |
| generator L36319 | `[R66-d2 P3] 前缀以 FORMAT_VALUE 为右界逐段归约` | diag2（代理自隔离，主代理采纳） | f-string 前缀扫描按 `[R65-d3 C1b]` 已有的同层 helper `_fstring_parts_from_segment`（def L41294）逐段归约，不可解释段退回改前结果 ⇒ 不再把 `stocks[:10]` 的后缀操作数拆成字面 part |
| generator L41633 | `[R66-d2 P1] 裸名跨块待定被调对象 callee` | diag2（代理自隔离，主代理采纳） | `_ternary_pending_callee` 原只认 `Attribute` 型 callee ⇒ 放宽到同层的裸 `Name`（fs2 `v3` 的 `print`），不新增逃逸口 |
| generator L44564 | `[R66-diag4 D1 augsub-continue-role]` | diag4 | CONTINUE 角色块的增强下标赋值：把 `[R102 fix]` 的读回协议判据（`COPY 2, COPY 2, BINARY_SUBSCR, …, SWAP, STORE_SUBSCR`）原样移植到本分裂器，归约为 `self.x['k'] += 1` 型 `AugAssign`，委托既有 `_build_subscript_assign` |
| analyzer L20949 | `[R66-diag3 value-context chained-compare gate]` | diag3 | 四合取：`block is cfg.entry_block` 且是 chained-compare `IfRegion` 的 entry（正是 `[R24-A]` 拒绝面）∧ 链末段两条出边皆 `_is_single_expression_block` 值块 ∧ 唯一共同后继块首条非噪声指令为 `STORE_*` ∧ 头块自身无已完结语句 ⇒ 值语境链不是语句，把该 IfRegion 从 `self.regions`/`block_to_region`/`conditional_regions` 一并撤销交给 Phase-7-D 建 `TernaryRegion`，复查 `_can_be_ternary_header` 仍拒则逐字回滚 |

禁止形态核查：8 处编辑全部为**同层次结构身份**判据（自身 blocks 的登记状态、自身
then/else 臂的语句性、`chained_compare_blocks` 是否为空、merge 块首条非噪声指令的类别、
`region.entry`/`try_offset_end` 与保护跨度的比较），无按函数名/文件名/偏移/阈值的启发，无
`region.entry in r.blocks` 型跨区域跨层次包含，无发射抑制（撤销的是归属，不是输出）。
其中 7 处在生成器、1 处在分析器；分析器那处是唯一动到 `region_analyzer.py` 的编辑。

## 4. 串行门禁（严格串行，逐条见 `logs/gate/`）

| 门 | 命令 | 读数 |
|---|---|---|
| G0 语法+字节 | `py_compile` + `ast.parse` + 指纹 | 两文件 OK；生成器 BOM=True/CRLF 50 626/裸 LF 0，分析器 BOM=False/CRLF 27 763/裸 LF 0 |
| G0′ 落地证明 | `closeout66.py landproof mirr_m66e` | 33 个 core 文件 same=33 diff=0 |
| G1 修到完全 OK | `single site-packages/IQCommon/util/common_func.pyc` | `decompile_status ok`、21/21、100.00%、`missing=[] extra=[]`，源 16 366 字符由工具链写入 `common_funcOK.py` |
| G2 金丝雀官方 | `single fly/data/quotation.pyc` | ok **143/143 100.00%**，源 176 722 字符 |
| G2′ 金丝雀严格 | `_r10_strict_check.py …/quotation.pyc` | **148/150**，缺陷集逐字未变：`change_his_to_forward [target_diff] #250`、`get_trend [target_diff] #10` |
| G2″ 第二金丝雀 | `single fly/common/market_time.pyc` + 严格 | 官方 **10/10**、严格 **10/10**、文件级 1/1 |
| G3 批量回归 | `batch --index pyc_index.json --all --round 66` | **402 verified / 0 failed**，ok 385→**386**，partial 17→**16**。（402 支全量复跑本身 > 300 s，按后台任务执行以免阻塞会话；前台每条命令 < 300 s，逐支读数见日志） |
| G4 统计 | `stats --index pyc_index.json` | total_functions **5746**、matched **5698**、rate **99.16%** |
| G4′ 严格尺（出货产物） | `strict_repo66.py center/all17.txt` | 17 支 **677/749**；`common_func` **22/22**；`missing=0 extra=0` 全部成立；**17/17 出货产物 sha == 落地前实测镜像产物**（`=measured`，0 处 `!=`） |
| G5 索引逐条比对 | `audit5_g5.py`（`git show HEAD:pyc_index.json` vs 工作树） | 条目 402→402，增删 0，键形变 0，**仅轮次戳 397 条**，实质变化 **5 条**（下表）；status `{ok 385, partial 17}` → `{ok 386, partial 16}`，matched 5693→5698 |
| G5′ 产物影响面 | `git status --porcelain site-packages/` | 400 份产物逐字节不变，**恰好 6 份 `*OK.py` 变化**＝5 支 IMPROVED + `quote.pyc`（MOVED），未手改任何生成文件 |
| G6 电池（31 支复现，两列对照） | `closeout66.py battery head landed` | R65 字节 → 落地字节：**9 项改善、0 项变差**；R63/R64 的 19 项老见证逐支读数不变；「candidate columns worse-than-landed on **0** repro(s)」 |

G5 的 5 条实质索引变化（其余 397 条只有 `last_tested_round` 65→66）：

| pyc | 字段变化 |
|---|---|
| `IQCommon/util/common_func.pyc` | status `partial→ok`、matched 20→21、rate 0.9524→1.0 |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | matched 39→40、rate 0.8864→0.9091 |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | matched 32→33、rate 0.9143→0.9429 |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | matched 106→107、rate 0.8908→0.8992 |
| `IQEngine/utils/scheduler.pyc` | matched 43→44、rate 0.9556→0.9778 |

G5′ 的产物级标本核对（每支都逐行读过，不是只看计数）：

* `common_funcOK.py` +1/-0：`del freq_k_minute[0]` 语句复原（diag6）。
* `quoteOK.py` +3/-7：三处序言日志的重复发射删掉一份（P4），且
  `stocks=stocksNone{10!s}等` → `stocks={stocks[:10]!s}等`（P3 前缀段归约）。
* `real_quoteOK.py` +2/-8：`get_cache_l2_data` 与 `get_cache_l2_data_by_one` 两支同时归位——
  原先两臂被当表达式语句发射、值被 `POP_TOP` 丢弃（`if 0 < int(data_count) <= 200:`
  `int(data_count)` `else:` `200`），汇合块的 `STORE_FAST data_count` 因此整条丢失，
  现还原为一条 `data_count = int(data_count) if 0 < int(data_count) <= 200 else 200`（diag3）。
* `risk_calculation/__init__OK.py` 7/7：三处被拆坏的 `'win_time'[1] = …` 型语句还原为
  `self.TradeMode_trade_statistic['win_time'] += 1`（diag4）。
* `trade_live_brokerOK.py` 1/1：空 then 臂内被吞并的重复 `in_stock = []` → `pass`（diag1）。
* `schedulerOK.py` +2/-1：无条件外提的 `hour, minute = divmod(minute_time, 100)` 回到复原的
  `else:` 臂下（diag5）。

G6 电池逐支读数存 `logs/gate/G6b_battery_head_vs_landed_r66.txt`；本轮新增的 5 支复现全部达标：
diag1 2/3→3/3、diag3 `shared_store` 2/3→3/3、`var` 3/6→6/6、`pred` 1/3→2/3（残差 `v6` 是判据
(d) 有意保留的落地读数）、diag4 1/2→2/2、diag5 2/3→3/3、diag6 1/3→3/3。

## 5. 六批判定（代理交付 + 主代理集中复测）

| 批 | 靶 | 采纳 | 主代理复测（落地前，单变量臂） |
|---|---|---|---|
| diag1 | `trade_live_broker`（13 支缺陷）等 | **E1** | 17 支 `SAME=16 IMPROVED=1 REG=0 MOV=0`，电池 `SAME=24`，金丝雀 `SAME=4`，复现 2/3→3/3；其 variant-1（不带 `chained_compare_blocks` 条款）在 402 上把 `strategy.pyc` 24/24→23/24 ⇒ 否决该变体（电池没抓到，402 抓到） |
| diag2 | `fly/data/quote.pyc`（11 支 + R65 遗留的 `load_bars_from_hundsun` 过冲） | **P4 + P3 + P1** | P4：quote `load_bars_from_hundsun` 缺陷元组 `[477,524,3,507]`→`[477,479,0,471]`（orig 477，实质 hunk 3 段→0 段）、重复日志语句 2→1；P3：fsrepro 6/7→7/7、fs2 `v8` truediff 28→14；P1：fs2 5/10→6/10。三支 402 扫描均由主代理代跑（代理已被轮次上限杀掉） |
| diag3 | `real_quote` + `klinedata`（8 支） | **1 支（analyzer 侧）** | real_quote 39/44→**40/44**（`get_cache_l2_data` 双尺全对齐）、`by_one` jd 300→197；klinedata 42/45 逐读数不变；电池 `SAME=24`、金丝雀 `SAME=4`；其 8 支里 6 支被判「候选：NONE」并给了排除证据 |
| diag4 | `risk_calculation` 等 | **D1** | 32/35→**33/35**（`get_TradeMode_trades` 清空），严格 33/37→34/37 |
| diag5 | `scheduler` 等 | **B** | 43/45→**44/45**（`get_checked_time` 清空），严格 49/52→50/52 |
| diag6 | `common_func` 等 | **A** | 20/21→**21/21**（本轮唯一「修到完全 OK」），严格 21/22→22/22 |

合并集在落地前的全套复扫（`m66e`）：17 支 `SAME=11 IMPROVED=5 REGRESSION=0 MOVED=1 ERR=0`；
电池 24 项 `IMPROVED=2 SAME=22 REGRESSION=0`（完全匹配 17→18）；金丝雀 `SAME=4`（四支产物 sha
逐字节 `4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177`）；
402 A/B `SAME=396 IMPROVED=5 REGRESSION=0 MOVED=1 ERR=0`，matched 5693→5698、clean 385→386、
Σ|orig−decomp| 418→**328**、Σjumpdiff 196→**184**、Σtruediff 11977→**9405**、缺陷函数 53→**48**；
产物 blast `identical=396 changed=6 unresolved=0`。逐臂中间件（`m66b`、`m66d`、`d3`、`p1`、`p3`、
`p4`）留在 `batches/` 与 `specs/` 供复核。

## 6. 未采纳（每条都有实测读数，全文在 `logs/EVIDENCE.md`）

* **diag2 `p2 storeepi`**：前提被证伪——`region.value_target` 对所有 f-string 三元都是哨兵
  `'__fstring_target__'`，实测产物零变化。
* **diag3 `drop` / `pair`**：`drop` 只删 `[R24-A]` 合取 ⇒ 三元建出来了但留下多余的
  `if 0 < int(data_count) <= 200: pass`（synth 33/31→33/46 变差）；`pair` 用两个 anchor、跨两个
  层次（越界），读数与单 anchor 版相同，仅作为「L20948 是那对编辑的承重折叠点」的证据保留。
* **diag3 的 6 支分类后无判据**：`get_all_real_daily_kline`（编译器重入块的产物复制，源码无对应
  构造）、`get_multiminute_his_data`（生成器侧共享出口内联顺序）、`kline_datetime_list`（纯次序
  颠倒，区域图正确）、`get_real_minute_kline`/`get_tick_direction`（纯位移：删除区间与插入区间
  同尺寸同跳转目标）、`one_prod_to_ndarray`（同一位移机制与已归因类交织，merge 环带非 store-clean）。
* **diag4 `_do_request` / `order_api`**：提升分支在 L47665/L47668 提前 bail、`POP_TOP` 测试 0 命中；
  `order_api` 的 kwarg 槽位 bail 在 L43098，两处都与本轮判据不同层。
* **diag5 `fileio_utils::write` / `params_analysis`**、**diag6 位移族 / `handle_exrights` /
  `api_base::get_history_df`**：归因完成但无可落地判据。
* **diag1 variant-1**（见 §5）。

## 7. 下一轮线索

1. 位移（displacement）族在 diag3/diag6 两批里独立出现 5 次，同一机制：多目标块被搬到函数尾部。
   `matcher::match` 也属这族（见 memory `project-r64-matcher-displacement-lead`），值得单独立批。
2. diag3 的 `r66d3_pred::v6`：判据 (d) 为了不退化「头块带前导已完结语句」的情形而保留落地读数，
   要把这一支也修掉，需要让撤销动作对「头块内的前导语句」做同层拆分而不是整体拒绝。
3. f-string 家族残余：`load_bars_from_hundsun` 的 `os.path.exists(DumploadDailyFile)` 裸表达式
   （P4 后余 7 条指令）、fs2 `v1/v6/v7/v8`。
4. diag0 型技术债：13 处 `_os_dbg_*` 调试导入清理（R65 起就记为「纯删除、402 中性」），
   仍应作为独立轮次，不与改变产物字节的行为补丁混落地。
5. 仪器问题：`batch` 偶发「Failed to decompile」而 `single` 正常（本轮 0 failed，未复现）；
   `closeout66.py` 的电池清单靠 glob 发现，`.pyc` 不入库 ⇒ 克隆后电池只剩 pinned 项。
