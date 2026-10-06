# Round 1 主代理验证序（VERIFICATION）

轮次：rr-v3r01 · Task 2（单单元损失族）
封表时点：2026-10-06（本轮终读数）
before = 本规范 fresh 基线 `baseline/shards/shard*_report.json`（units 6554/6617、files 369/402）
after  = `rounds/round1/after3/shard*_report.json`（402 产物在终态代码上「先删后生成」重生成）
判据唯一 `scripts/pyc_verify.py`（ruler sha `9c7567bd6776b36b`、interp 3.11.7）

## I. 验证序六步读数

| # | 步骤 | before | after | 判定 |
|---|------|--------|-------|------|
| 1 | 34 小测试集（a/b1/b2 三片） | 1505/1568 | **1516/1568**（a 473→481、b1 513→513、b2 519→522） | 零位移回退 0 ✓ |
| 2 | 402 八分片 batch + compare | units 6554/6617（99.0479%）、files 369/402 | units **6564/6617（99.1990%）**、files **376/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 3 | quotation 单验 | 152/153（`<module>.change_his_to_forward`） | **152/153**（`<module>.get_fundflow_day`） | 单元数不回退；失败单元发生**替换** → 登记 B102（见 §IV） |
| 4 | tests 六套件 | 277 passed / 2 failed / 2 xpassed | **277 passed / 2 failed / 2 xpassed** | 失败名单 = 基线名单（test_B01 + test_BOUNDARY_02），零新增 ✓ |
| 5 | IV.2 门禁自检 | — | IMPORT_OK、`compileall -q core` rc=0、新增 def 禁止前缀命中 **0**、调试残留（print/breakpoint/TODO/FIXME）**0**、硬编码深度/计数上限 **0**、region_ast_generator 单头 BOM（计数 1）、region_analyzer 全 CRLF 31914/31914 行、无 BOM | 全过 ✓ |
| 6 | 读数汇报 | — | 本文件 | ✓ |

电池面（修复工程师自测门禁，主代理逐条复算）：
- `test_repros/round1/r1_probe_index.json`（46 标本）：91/110（19 failure）→ **108/110 units，44 success / 2 failure**
  残余 2 条 = `_search/handler_ifelse`（B101，登记为线索、非本轮靶）与 `r1_73_cand_fortry_sinkpair`（B99）
  残余 2 条是原 19 条失败集合的**严格子集** ⇒ 27 条负对照零变差
- `test_repros/round1/r1_regress_index.json`（回退哨兵臂，17 臂）：**34/34 units，0 failure**

## II. 本轮封闭的破口

| 破口 | 机制 | 落地标记 | 语料收益 |
|------|------|----------|----------|
| **B98** | TryRegion 自然出口汇合块被末位 handler 的终止 return 吞并，函数级 `return None` 未发射 | `_is_return_none_join_block` / `_is_region_internal_exit_sink`（commit `3adda063`） | `cgroup_utils` 7/8→8/8 |
| **B100** | IfRegion 臂的 merge/join 取成外层作用域尾（循环体尾/try 体尾/函数尾），同层后续兄弟被吸收进臂 | `_compute_arm_level_join` / `_armjoin_is_skip_edge` | `email_utils` 4/4、两份 `calexrights_func` 8/8、`executor` 10/10、`history_api` 19/19、`ptradeAccount` 137/137、`quote` 84→85、`trade_info_utils` 36→37、quotation `change_his_to_forward` 单元转 Equal |
| **B103**（本轮内新登记并封闭） | B100 的 (4b) 判据把「回边耗尽」与「终止码耗尽」同视，`perform_rollover` 的 break 落到外层 LoopRegion 自身出口被误认领为同层兄弟 join | `[r3-b103-armjoin-termexit]`（region_analyzer 4 处） | 恢复 `IQEngine/utils/logger/handlers` 17/17、`IQCommon/logger/handlers` 29/30，同时保住 `strategy_info_utils` 30/30 |

## III. 本轮拦下的三次回退（都在 34 集之外，只有 402 全量能看见）

这是本规范「单元级不回退门禁」存在的理由，逐次记录：

1. **B98 附带**：`plugin_system_accounts/__init__` 6/6→5/6、`benchmark_account` 20/20→19/20、`stock_account` 25/25→24/20 系。
   定位＝`_is_region_internal_exit_sink` 的祖先链从块自身区域起算，而被判定的 sink 恰是该 LoopRegion 的成员块 ⇒ 守卫自指恒真。
   封闭＝`[r1-b98-elsescope]` 跳过「即裁决区域本身」的那个祖先（纯成员关系判据）。三文件读数全恢复，`cgroup_utils` 8/8 保住。
2. **B100 附带**：`IQCommon/util/strategy_info_utils` 30/30→29/30（`get_strategy`）。
   定位＝(4) 判据要求「≥2 前驱 bin 且 E bin 非空」，耗尽臂留下单 bin join 时不接受真 join，BFS 越过 1088 认领 2068（外层 elif 链 skip 边汇入）。
   封闭＝新增 (4b) 尾块直跳认领；该次封闭又引出第 3 项。
3. **B100fix 附带 = B103**：`IQEngine/utils/logger/handlers` 17/17→16/17 与 `IQCommon/logger/handlers` 29/30→28/30（同为 `RotatingFileHandler.perform_rollover`）。
   定位与封闭见 §II。**三次全部在本轮内封闭，未带入下一轮。**

主代理归因手法：把 `core/cfg/region_analyzer.py` / `region_ast_generator.py` 分别回退到指定版本做 A/B 单文件复测，
回退前先 `sha256` 备份未提交代码并在复测后按字节校验还原（`52153981f7c07440…`、`f9c7c2c94f5fc84e…` 两侧 True）。

## IV. 新登记与如实移交

- **B102 — quotation 失败单元替换**：基线 152/153 唯一失败 `<module>.change_his_to_forward`，本轮该单元转 Equal 但
  `<module>.get_fundflow_day` 新失败，**单元总数与文件状态读数不变（152/153、failure）**，故纯计数门禁看不见它。
  登记理由：不以 152/153「持平」掩盖形态替换。移交 Round 4（quotation 终局单元）与 B100 族同治。
- **B99 — 残余**：`r1_73_cand_fortry_sinkpair` 仍 MISMATCH，`IQCommon/logger/handlers` 的 `_target` 仍 Different control flow。
  未封闭，移交 Round 2 面（同属双/单单元损失族的 sink 归并形态）。
- **B101 — 线索**：合成标本 `_search/handler_ifelse`（try 体内两条同形 if/else 兄弟只剩一条，107→76 指令）。
  6 个目标 pyc 中未定位实例，测试工程师明示「禁止据此改判据」，保持登记不处理。
- **finance 31/32（`get_fields`）**：B100 判据面在其宿主形态上仍未覆盖，仍 -1，移交 Round 2。
- 语料残余由 33 文件/63 单元 → **26 文件/53 单元**。

## V. 轮门禁判定

- ≥1 个 pyc 由 failure 转 success：本轮 **7 个**（`cgroup_utils`、`email_utils`、两份 `calexrights_func`、`executor`、`history_api`、`ptradeAccount`），同目录 `+OK.py` 由 `pycdc.py` 重生成且全单元 Equal ✓
- 全量单元读数净增：6554 → 6564（+10）✓
- `REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0` ✓
- 无 `*OK.py` 手改（一律先删后重生成，402/402 重生成 0 失败）✓
- 单条命令 ≤300s（超时者已拆分：34 集拆三片、regen 每片 ≤3 分片、verify 每片 ≤4 分片）✓
- 派发子代理前均有本地提交 ✓
- **Round 1 判定：通过，可开启 Round 2**

## VI. 遗留的工具面事实（供后续轮次，勿重踩）

- `driver.py verify N` 默认把报告写进 `baseline/shards/`，会**覆盖基线**。本轮起一律显式传第二参数指向轮次目录
  （`after`/`after2`/`after3`）；基线被覆盖过一次，已用 `git checkout -- baseline/shards/` 还原并复核 6554/6617 逐位一致。
- `driver.py verify all34` 在本语料上必超 290s 内部上限（rc=TIMEOUT，driver_log 在案），须拆 a/b1/b2 三片。
- `pyc_verify.compare` 以绝对 pyc 路径为键，故本规范全部报告同用 `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` 前缀；
  `*.pyc` 与 `pylingual` 判据均不在 git 内，语料按相对路径镜像进本工作树，F: 工作区零写入（只读 `git -C` 状态查询除外）。
