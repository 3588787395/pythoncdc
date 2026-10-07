# Round 4 主代理验证序（VERIFICATION）

轮次：rr-v3r04 · Task 5（单单元损失族 / 分析端 sink 归属）
封表时点：2026-10-07
before = `baseline/shards/shard*_report.json`（units 6554/6617、files 369/402）
after  = `rounds/round4/after/shard*_report.json`（402 产物在终态代码上先删后重生成，8 片 failed 合计 0）
判据唯一 `scripts/pyc_verify.py`（ruler sha `9c7567bd6776b36b`、interp 3.11.7 64 位）

## I. 验证序读数

| # | 步骤 | 读数 | 判定 |
|---|------|------|------|
| 1 | 402 八分片 batch + compare（对基线） | units 6554→**6571/6617（99.3048%）**、files 369→**380/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 1b | 对 Round 3 终态增量核对 | units 6569→6571、files 378→380（NEW-OK = `trading_dates_mixin`、`stock_position`） | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 2 | quotation 单验 | **152/153**，失败单元仍 `<module>.get_fundflow_day` | 零新增失败；B102 未回退（仍未闭）✓ |
| 3 | tests 六套件 | **277 passed / 2 failed / 2 xpassed**（test_B01 + test_BOUNDARY_02） | 零新增失败 ✓ |
| 4 | IV.2 自检 | IMPORT_OK、`compileall -q core` rc=0、禁止前缀新增方法 **0**、调试残留 **0**、硬编码上限 **0**、`region_analyzer.py` 2030385→2037812B / 31979→32073 行 / 单头 BOM / 全 CRLF、`region_ast_generator.py` 逐字节未动 | 全过 ✓ |
| 5 | 电池（主代理独立复算） | `r4_probe_index` **64/75**（23 success / 11 failure；起点 51/67）、`r1_probe` **108/110**、`r1_regress` **34/34**、`r2v3` **105/126**、`r3` **101/122** | 本轮 r4 +13 单元、**零条绿臂转红** ✓ |

## II. 本轮批次的真实成色：1 落地 + 4 整批回滚

**落地：B116/B99 族（分析端 sink 归属）** — `trading_dates_mixin` 13/14→**14/14**、`stock_position` 36/37→**37/37**。
根因：`if A: if not B: body` 处于套件尾时，每个短路出口各有 `LOAD_CONST None; RETURN_VALUE` 块（off118/off122），
但 `_detect_boolop_conditional_chain` 仍把两操作数收进同一条链、`_boolop_resolve_merge` 取**末位**成员目标作唯一 merge，
于是唯一建区点 `_create_boolop_region_from_chain` 建成单汇合区域：第一个出口成 IfRegion 的 else 臂，
第二个出口（off122）掉成 `parent=None` 孤块 ⇒ 少发射一对 None-return（−2）。
修复＝新增 `_boolop_chain_exits_are_distinct_sinks` + 建区前置不变式门（与 R14b/R38 并列第 3 条）；
判据只读块末 opcode / 后继前驱 / 区域成员关系；决定性探针事实：b01（嵌套 if）与 b03（扁平 and）编译后逐字节相同
⇒ 源码形态不可辨识，发射嵌套 if 不付代价，故按 sink 归属拆区是正解而非形态特判。
标记 `[R4-B116 sinkexit]`：12 次 True / 72 次调用，其中 11 次通向 7 处翻转，**1 次（handlers off412）命中而未翻转，如实登记**。

**四次整批回滚（全部「仅归档 spec 未落地」，零残留、零读数变化）**——按「命中必须换成翻转」的验收线当场否决：

| 工单 | 尝试 | 实测 |
|------|------|------|
| B99/B116（生成端） | 删死计数器换 3 个区域局部消费点 | 633 调用 / 12 True / **0 翻转** ⇒ 回滚；换得关键结论：本族归并发生在**分析端**，遂有上表落地批 |
| B100/B110 汇合同一性 | 分析端条件(6)「仅可经 J 到达」＋生成端 B108 拆分子句 | +0 命中→0 翻转；4 命中→0 翻转 ⇒ 双双删除 |
| or-run 完整性 | 链式比较双腿并入同一元操作（抑制 `[R64-diag1] chain.pop()`）＋三处同事实补丁 | or-run 确实完整（merge 564→612、R14c 取反消失）但 **0 翻转** ⇒ 回滚；配方留档可复用 |
| or-run＋elif 宿主 | α `_boolop_run_terminal_member`（区域尾成员短路边恰为 merge_block） | `elif_conditions [512]→[512,612]`、臂体 22 块恢复，仍 **0 翻转**；β/γ 两形实测**变差**当场删除 ⇒ 回滚 |

四次回滚把 A 族（7 文件）的病灶逐层收窄，当前最有价值的未执行线索：
测试工程师实测 `strategy`/`api_base` 的成员边**全为 `POP_JUMP_FORWARD_IF_TRUE` 族且目标相同（不分裂 S/F）**，
指认 `_boolop_mixed_polarity_or_chain`（`region_ast_generator.py:38240`）「目标必须分裂为 S 与 F」这一判据**过严**；
且 `a06`（两臂链）/`a07`（无 or）/`a09`（无 elif）皆仍 MISMATCH ⇒ 「跳族混合 / or 成员 / elif 层」均非必要条件。

## III. 工具与流程事实（本轮新增，供后续轮次）

1. **陈旧读数防线已常驻**：`driver.py cmd_verify` 先删同名旧报告、跑完无新报告即 fatal。
   本轮它真的挡住一次事故——shard5 首跑 `rc=TIMEOUT`，若无此守卫，盘上的**上一轮** shard5 报告会被当作本轮读数。
2. **`split_verify.py` 落盘**：分片对半/四分合规拆跑（每跑 <280s）→ 合并 rows → 断言 files/rows 与分片索引等量后写 `shardN_report.json`，
   报告内记 `merged_from` 与 `split_reason`。本轮 shard5/6/7 由它产出（机器争用致整片超 290s 内部上限）。
3. **本机存在并行会话**：实测 10 个 python 进程，其中非本会话的包括
   `pytest -q new_tests tests`、`adversarial-complete-forms-v2-10rounds/rounds/round7/r7v7fix_{station,attack}.py`、
   以及两个跑在 `F:\Downloads\pythoncdc-main` 上的 `pyc_verify single`。
   ⇒ 本轮多次命令超时源于**外部争用 + 我自己并发两条链**（后者是我的处置失误：并发链相互拖累）。
   后续 gate 一律串行、单条链、按分片拆跑。
4. 语料与判据不在 git 内（`*.pyc`、`pylingual`），本工作树为镜像；F: 工作区仍零写入。

## IV. 轮门禁判定

- ≥1 个 pyc 由 failure 转 success：本轮 **2 个**（`trading_dates_mixin` 14/14、`stock_position` 37/37，同目录 `+OK.py` 由 pycdc 重生成、全单元 Equal）✓
- 全量单元读数净增：6569 → 6571（+2；对基线 +17）✓
- `REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`（对基线与对 Round 3 终态双向）✓
- 产物零手改（先删后重生成，8 片 failed 合计 0）✓；派发子代理前均有本地提交 ✓；已 push `origin/rr-v3-full-corpus` ✓
- **Round 4 判定：通过，可开启 Round 5**
- 效率如实记：**5 个修复工单只有 1 个落地**；A 族 7 个文件整轮未被推进一次，四次尝试均止步于「命中但零翻转」。

## V. 语料残局（封表时点 22 文件 / 46 单元）与实名移交

未闭：**A 族 7 文件**（`strategy` 26/27、`api_base` 27/28、`matcher` 16/17、`finance` 31/32、`bar` 84/85、`function` 70/71、`strategy_universe` 10/11、`load_daily` 26/27 —— 含 `#5` 系 Round-1 B100 原锚点逐位复现，三轮未闭）；
**B117 内吞族 2 文件**（`realtime_event_source` 12/13 出口边 `jump_off=9214→None` 被吞 + 100 条尾随语句段不发射 −102；`profiler_func` 17/18 同机制 −58）；
**B111 轴 1 文件**（`quote_handler` 78/79，if 臂出口新增 None 尾 sink +2）；
**B 族残 2 文件**（`handlers` 29/30 循环双出口、`quotation` 152/153 边目标 268/272 互换）；
**未归族 1 文件**（`flytools` 65/66 唯一分歧为 prod off700 单条 NOP，不足以定形）；
**大户**：`trade_live_broker` 118/128、`quote` 86/92、`trade_info_utils` 37/41、`klinedata` 61/64、`wizard_quant_api` 55/58、`real_quote` 43/45、`risk_calculation/__init__` 41/43、`order_api` 35/37；
在册未动：B99（`r1_73` 本轮未翻转，卡在 for 宿主 try/else 轴）、B101（合成线索，禁止据此改判据）、B102、B114、B110 残臂。
