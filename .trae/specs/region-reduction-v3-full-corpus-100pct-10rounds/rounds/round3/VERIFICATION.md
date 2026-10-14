# Round 3 主代理验证序（VERIFICATION）

轮次：rr-v3r03 · Task 4（三单元损失族）
封表时点：2026-10-06
before = `baseline/shards/shard*_report.json`（units 6554/6617、files 369/402）
after = `rounds/round3/after/shard*_report.json`（402 产物在终态代码上先删后重生成，8 片 regen failed 合计 0）
判据唯一 `scripts/pyc_verify.py`（ruler sha `9c7567bd6776b36b`、interp 3.11.7 64 位）

## I. 验证序读数

| # | 步骤 | 读数 | 判定 |
|---|------|------|------|
| 1 | 402 八分片 batch + compare（对基线） | units 6554→**6569/6617（99.2746%）**、files 369→**378/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 1b | 对 Round 2 终态增量核对 | units 6566→6569、files 377→378 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0**（NEW-OK = `future_contract_info`）✓ |
| 2 | quotation 单验 | **152/153**，失败单元仍 `<module>.get_fundflow_day` | 零新增失败；B102 未回退 ✓ |
| 3 | tests 六套件 | **277 passed / 2 failed / 2 xpassed**（test_B01 + test_BOUNDARY_02） | 零新增失败 ✓ |
| 4 | IV.2 自检 | IMPORT_OK、compileall rc=0、禁止前缀新增方法 0、调试残留 0、硬编码上限 0、两个被改文件各单头 BOM 全 CRLF | 全过 ✓ |
| 5 | 电池（主代理独立复算，不引用工程师自报） | `r3_probe_index` 56 臂 **101/122**（35/21）；`r2v3` **105/126**；`r1_probe` **108/110**；`r1_regress` **34/34** | 三枚电池逐位未变差，零绿臂转红 ✓ |

## II. 本轮批次的真实成色（含一次全量回滚）

| 批次 | 家族 | 落地 | 净效应 |
|------|------|------|--------|
| 测试工程师 | 3/3 目标 pyc 逐指令第一分歧；登记 B109-B113；电池 52 臂 84/114（30 MISMATCH / 22 MATCH，主代理复算逐位一致）；引用符号经我方 grep 复核（`_main_inline_boolop_chain` 实为局部变量而非 def，行号 19281 属实） | — | 证据面 |
| **B109** | elif 臂 or 链成员真边同一性：核验前先追加、核验结果被 break 丢弃 ⇒ 臂的**出口边**被当链成员真边，`not A` 折成 `A or B` 摧毁臂体 | `region_analyzer.py`，标记 `[R3-B109 …]` ×3；首版零命中守卫 `_elif_or_chain_join_is_shared` 经 54 文件实测 0 次 True 后自行删除 | r3 84/114→97/118（11 标本翻 9）；`order_api` 34/37→**35/37**；语料 +2 单元（order_api、quote） |
| **B114**（IfExp 兄弟三元） | 同一实参表内 ≥2 个兄弟三元，前者 merge_block 恰为后者 condition_block 被双重认领 | **「仅归档 spec 未落地」**：判据修正可行且已测通，但补完链式调用实参装配需改 `func_call_info` 热路径，越出工单许可 ⇒ 整树按行数/BOM/标记计数还原 | 零读数变化（主代理复核：还原后 git 仅剩 `quoteOK.py` 一处滞后，已以终态代码重生成补齐 86/92） |
| **B115** | handler 臂终态块 finally 副本前缀唯一归属：`_generate_try` 的臂循环问 `_generate_handler_body_statements`（只过滤异常框架 opcode），未消费 `TryExceptRegion.finally_copy_blocks` 台账 ⇒ 臂块把属主已发射的清理块再物化（原则2 过度认领面，与 B99 认领不足面相反） | `region_ast_generator.py`，标记 ×1；谓词实测 True 命中：语料 1、标本 a18 1、孪生 1（不落零命中守卫） | `future_contract_info` 28/29→**29/29 整文件转绿**；r3 97/118→101/122（新增 a18/a19 永久臂）；B112 经测为不同判据（该谓词在 wizard 上命中 0 次），未冒领 |

## III. 轮门禁判定

- ≥1 个 pyc 由 failure 转 success：**1 个**（`fly/common/future_contract_info.pyc` 29/29，同目录 `+OK.py` 由 pycdc 重生成、全单元 Equal）✓
- 全量单元读数净增：6566 → 6569（+3；对基线 +15）✓
- `REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`（对基线与对轮内前态双向）✓
- 产物零手改；命令 ≤300s；派发前本地提交；已 push `origin/rr-v3-full-corpus` ✓
- **Round 3 判定：通过，可开启 Round 4**
- 但须如实记下效率：**本轮三批只有 2 批落地，且 3 单元损失族（klinedata/wizard/order_api）本身未被攻穿**，
  翻转来自 B115 的单单元残项。若下一轮仍按「族」派发，应先做族内单元数排序而非按 spec 目录顺序。

## IV. 一次非确定性红的处置（不靠「重跑过了」下结论）

`driver.py verify 4` 首次运行 **rc=1 / MemoryError**（栈顶 `pyc_verify.py:96 evaluate → :74 sha256 → f.read(1<<20)`，
崩在 51 文件中的第 26 个之前），**未写报告**；同命令序列里我随后读到的 `shard4_report.json`（851/855）实为
**上一轮的陈旧文件**——若直接采信，本轮 aggregate 会把陈旧读数当本轮。
处置：① 复跑确证 rc=0 且报告 `generated_at` 刷新、51 文件、compile_error/error 均为 0；
② 排除判据面因素——解释器为 64 位 3.11.7，shard4 最大 pyc 48KB / 最大 OK.py 59KB，非大文件问题，
属 pylingual CFG 重建期的瞬时内存压力；③ **落常驻牙**：`driver.py cmd_verify` 现在先删同名旧报告，
跑完若目标报告不存在即 fatal（`本次未产出报告——其上的任何数字都不属于本轮`），使陈旧读数冒充本轮这条路被永久封死；
④ 已复测守卫生效（shard2 重跑 10.9s、报告 mtime 刷新、`compileall` 通过）。

## V. 语料残局与移交（封表时点，24 文件 / 48 单元）

未闭环实名：**B99**（`handlers._target` 双 sink 归并，原则2 认领不足面）、**B110**（混合跳转族 or 链，`_boolop_mixed_polarity_or_chain` 的「全员 IF_TRUE 族」认领条件不足）、**B111**（LoopRegion 自然出口物化共享终态 return）、**B112**（`filter_desicion` 共享 None-sink 重复，独立终态块）、**B113**（`<genexpr>` 区域森林根的三元 and 首合取 + else 边丢失）、**B101**（合成线索，语料无实例）、**B102**（quotation 单元替换）、**B114**（仅归档未落地）；
已登记未绿标本：r3 电池 21 臂（a08 自反驳、a14、b01、b03、b12-b15、c01-c11 等）、r2v3 21 臂。
`order_api` 35/37 卡在 B114；`wizard_quant_api` 55/58；`klinedata` 61/64；`trade_live_broker` 118/128 与 `quote` 86/92 为最大两坨。
