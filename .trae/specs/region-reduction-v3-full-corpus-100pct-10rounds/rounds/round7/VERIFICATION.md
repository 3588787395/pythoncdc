# Round 7 主代理验证序（VERIFICATION）

轮次：rr-v3r07 · Task 8
封表时点：2026-10-07
before = `baseline/shards/shard*_report.json`（6554/6617、369/402）
after  = `rounds/round7/after/shard*_report.json`（402 先删后重生成，8 片 regen failed 0、8 片 verify 全 rc=0）
判据唯一 `scripts/pyc_verify.py`（ruler sha `9c7567bd6776b36b`、3.11.7 64 位）

## I. 验证序读数

| # | 步骤 | 读数 | 判定 |
|---|------|------|------|
| 1 | 402 八分片 + compare（对基线） | units 6554→**6574/6617（99.3502%）**、files 369→**383/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 1b | 对 Round 6 终态 | units 6573→6574、files 382→383（NEW-OK = `profiler_func`） | 双向零回退 ✓ |
| 2 | quotation 锚点 | **153/153 success**（连续两轮未回退） | ✓ |
| 3 | tests 六套件 | 277 passed / 2 failed / 2 xpassed（同基线名单） | ✓ |
| 4 | IV.2 | IMPORT_OK、compileall rc=0、禁止前缀 0、调试残留 0、探针残留 0（仅存 `D:/Temp/rrv7`）、generator 单头 BOM 全 CRLF | ✓ |
| 5 | 电池（主代理复算） | `r6_probe` **76/85**（40 臂 31/9）、`r1_probe` 108/110、`r1_regress` 34/34、`r2v3` 105/126、`r3` 101/122、`r4` 77/87 | 零绿臂转红 ✓ |

## II. 本轮五张工单：1 落地 / 4 回滚或否证

| 工单 | 结论 | 关键实测 |
|------|------|----------|
| B99 上游认领（生成端消费点） | 回滚 | 633 调用 / 12 True / 0 翻转；换得结论：归并在分析端 |
| B121 加宽 boolop 形状门 | **否证** | 8 单元链全部收敛于单一共享目标，门在 `region_analyzer.py:28055` 提前返回 ⇒ 加宽＝恒等变换；私有落点逐链 ∈{0,1} 从不 ≥2；去掉私有性在 24 条正当链过度触发 |
| B120 循环头 NOP 落点 | **否证（站点错位）** | 头 NOP@44 在 `dominator_analyzer.py:502 get_all_loops` 的回边归一化中早已折叠 ⇒ 在 region_analyzer 层加宽同为恒等变换；G-A 经探针确认区域模型本已正确，差在 CPython 行锚放置 |
| B99 覆写 / 链尾落点 | 回滚 ×2，但两票把结构推到正确形态（块数 42→43＝ORIG、off404/408 由 LoopRegion@90 各自 distinct 认领、`elif` 链复原、伪 return None 消失）；且第二票以对象同一性 trace **否证了主代理简报给的成因**：多余 `return None` 不来自 blk@1012，而来自 `_loop_generate_while:8019` + `has_trailing_return_none` 提升 | True-hits 1/3、flips 0；handlers 仍 29/30 |
| **B117 出口落点认领广播**（从未尝试轴） | **落地** | `_loop_unemitted_exit_landing`（`region_ast_generator.py:51692`）：GET_ITER 守卫的认领广播（`:51818-51820`）把 `LoopRegion@954.blocks` **全部**标为 generated，含从未发射的区域外落点块 blk@1060（58 条指令＝尾随语句段 + 下一循环 for_iter_setup），致 `_generate_basic_region:51147` 跳过它、zip 循环不物化；抑制该认领 ⇒ `profiler_func` **18/18** |

**两实例经证明互不相干**：`clock_worker` 的边死在 or-extension 臂序列 `:21080`，新判据在此**零调用**、差值仍 −112（登记时 −102）⇒ 未强行并案。

## III. 纪律兑现（本轮最有价值的管理结论）
1. **轴切换第二次生效**：B99/B100/B110 所在簇连续 5 票零翻转后，第 6、7 票改打从未尝试的 B117 轴，**第一击即翻文件**。
   与 Round 5 同型（当时换轴第 3 击翻 quotation）。⇒ 同一残差簇在第 3 次零翻转后必须让位给新轴，
   「残差收窄 −102→−4、块数 42→43」这类进展是信息，不能当作进度记。
2. **主代理简报数据三次失真**（旧字节数、被后续证据推翻的成因、失效行号），全部由工单实测纠偏并如实入库；
   ⇒ 本规范已改为「简报中的每个字节数/行号/成因都注明取证轮次，且主代理派票前现场复测」。
3. **标记核查口径**：九枚标记实际带 ` 修复·…` 后缀，按字面量 grep 计数为 0，须按**前缀**口径核；已写入核查约定。
4. 新落地的 3 条 r6 臂虽绿，但**不具备变形判别力**（要带牙需补「合并迭代器 setup」成分），由工单如实登记为残项而非成绩。

## IV. 轮门禁判定
- ≥1 语料 pyc 转 success：**1 个**（`IQEngine/utils/profiler_func.pyc` 18/18，`+OK.py` 由 pycdc 先删后重生成、18 单元全 Equal）✓
- 读数净增：6573→6574（对基线 +20）✓；双向零回退 ✓；产物零手改 ✓；命令 ≤300s ✓；派发前本地提交 ✓
- 已 push `origin/rr-v3-full-corpus`（`4c8772f6..1a376a80`）✓
- **Round 7 判定：通过，可开启 Round 8**

## V. 语料残局（19 文件 / 43 单元，封表时点）
`trade_live_broker` -10、`quote` -6、`trade_info_utils` -4、`klinedata` -3、`wizard_quant_api` -3、
`real_quote` -2、`order_api` -2、`risk_calculation/__init__` -2，以及 11 个 -1 文件
（`finance`、`handlers`、`api_base`、`bar`、`strategy_universe`、`strategy`、`realtime_event_source`、
`matcher`、`function`、`flytools`、`load_daily`）。
在册未闭：B99（结构已正确，只差 while 尾随 return-None 提升处那一处）、B117 的 `clock_worker` 实例与第 4 处正交 AND 腿吞句、
B122/B123/B124（仅语料可见、无合成标本）、B110/B104 残臂、B101（禁据此改判据）、genexpr 最小孪生未取得。
