# Round 6 主代理验证序（VERIFICATION）

轮次：rr-v3r06 · Task 7（大损失文件 / 轴切换验证）
封表时点：2026-10-07
before = `baseline/shards/shard*_report.json`（units 6554/6617、files 369/402）
after  = `rounds/round6/after/shard*_report.json`（402 先删后重生成，8 片 regen failed 0、8 片 verify 全 rc=0）
判据唯一 `scripts/pyc_verify.py`（ruler sha `9c7567bd6776b36b`、interp 3.11.7 64 位）

## I. 验证序读数

| # | 步骤 | 读数 | 判定 |
|---|------|------|------|
| 1 | 402 八分片 + compare（对基线） | units 6554→**6573/6617（99.3350%）**、files 369→**382/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 1b | 对 Round 5 终态 | units 6572→6573、files 381→382（NEW-OK = `quote_handler`） | 双向零回退 ✓ |
| 2 | quotation 锚点复验 | **153/153 status=success**（未回退） | ✓ |
| 3 | tests 六套件 | 277 passed / 2 failed / 2 xpassed（test_B01 + test_BOUNDARY_02） | 零新增失败 ✓ |
| 4 | IV.2 | IMPORT_OK、compileall rc=0、禁止前缀 0、调试残留 0、插桩残留 0、analyzer 单头 BOM 全 CRLF、generator/code_generator 逐字节未动 | 全过 ✓ |
| 5 | 电池（主代理复算） | `r6_probe` **70/79**（37 臂 28/9）、`r1_probe` 108/110、`r1_regress` 34/34、`r2v3` 105/126、`r3` 101/122、`r4` 77/87 | 零绿臂转红 ✓ |

## II. 本轮四张工单：1 落地 / 3 否证（否证本身就是产出）

| 工单 | 结论 | 关键实测 |
|------|------|----------|
| **B121**（称＝B116 欠伸） | **否证** | 8 个语料单元的链全部收敛于**单一共享目标**（check_frequency t@204 preds=[72,100,128,140,152]、get_multiminute t@2710 preds=[0,68]、get_kline_by_count_new t@3076 succs=[1268] 回边块），门在 `region_analyzer.py:28055` 的 `len(_targets)<2` 提前返回 ⇒ 加宽形状判据＝恒等变换；普查 quote 10 链 / klinedata 14 / wqa 2，私有落点数逐链 ∈{0,1} 从不 ≥2；去掉私有性则在 24 条正当 or/and 链过度触发 |
| **B120**（无条件循环头 NOP 落点） | **否证（站点错位）** | G-B 的 `while True:` 头 NOP@44 在到达 `region_analyzer.py:4881/4891/5221/5234` **之前**已被 `dominator_analyzer.py:502 get_all_loops` 的回边归一化折叠（只返回 hdr@46）⇒ 在该层任何加宽同样是恒等变换；G-A 的 @178 JUMP_BACKWARD →@130 vs →@114 经探针确认区域模型本已正确（entry@114 hdr@130 back_edge@724），差异是 CPython 行锚放置，不动 offsets 无法改 ⇒ 拒绝行锚/文本 hack |
| **B111**（if 臂出口凭空 None 尾 sink） | **落地** | 与 B119 是不同规则：B119 抑制 CFG 中**已存在**的平凡 None sink，本形 ORIG 末两块皆表达式返回（3524/3528）**无 sink 块**，3534 是重编译错位源时凭空生成 ⇒ 对 sink 加宽归属在此命中 0，且强行加宽会重新破坏 `quotation.get_stock_exrights`。真因＝`_identify_boolop_regions` 的循环条件前缀剥离把已建链 `[(344,and),(382,or),(420,and),(458,and)]` 降为后缀 `[382,420,458]`（成员 344 仅反向可达；5 个循环 cond=710/1070/1430/1790/2150 收集皆 [344,382,420,458,500,…]）。新门 `_boolop_member_is_loop_condition_entry`：再归属必须与该 LoopRegion 的 condition_block 角色同一。`quote_handler` 78/79→**79/79 整文件转绿**；边恢复 344→420 / 382→496 / 420·458→500；变形反证：谓词置桩则 a01/a02 回落 1/2、对照 a03 保持 2/2。标记 `[R6-B111 armscope]`×3 |
| 测试工程师（Round 6 诊断） | 4/4 靶全覆盖 | 34 臂电池 64/73（25 MATCH/9 MISMATCH）主代理复算逐位一致；**推翻主代理「trade_live_broker 8/10 同源」假设**，改为六组（G-A 3 单边错投、G-B 3 头 NOP 丢失、G-C/D/E/F 各 1）；新登记 B120-B124 |

**轴切换纪律在本轮兑现**：B121/B120 两票零翻转后按 2-3 次阈值换轴，第 3 轴（B111）即翻文件。

## III. 主代理数据失误一处（如实登记）
我在 B120/B111 工单简报里给出的 `region_analyzer.py` 字节/行数（2045409 B / 32168 行）是 **B119 落地之前**的旧值；
工单实测来树值为 2052197 B / 32266-32267 行（sha `0212c54e…`）。工单以实测值为准并据此证明自身回滚为逐字节还原，
未造成损失，但**主代理引用的基线常数必须现测现用**——已写入本文件，后续轮次简报一律以当轮实测 sha 为准。

## IV. 轮门禁判定
- ≥1 语料 pyc 由 failure 转 success：**1 个**（`fly/data/quote_handler.pyc` 79/79，`+OK.py` 由 pycdc 先删后重生成、79 单元全 Equal）✓
- 全量单元读数净增：6572 → 6573（对基线 +19）✓
- `REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`（对基线、对 Round 5 终态双向）✓
- 产物零手改、命令 ≤300s（本轮机器空闲，未再触发 290s 上限）、派发前本地提交 ✓
- 已 push `origin/rr-v3-full-corpus`（`7ce77ba4..45bbb25e`）✓
- **Round 6 判定：通过，可开启 Round 7**

## V. 语料残局（20 文件 / 44 单元）
`trade_live_broker` 118/128（-10：G-A 行锚轴 + G-B 上游回边归一化轴，均已否证于 region_analyzer 层，**真根在 dominator_analyzer:502**）、
`quote` 86/92（-6）、`trade_info_utils` 37/41（-4）、`klinedata` 61/64（-3）、`wizard_quant_api` 55/58（-3）、
`real_quote` 43/45、`order_api` 35/37、`risk_calculation/__init__` 41/43 各 -2，
以及 12 个 -1 文件（含 handlers 29/30＝B99 第二机制、finance 31/32＝B100/B104 原锚点、flytools 65/66 纯 NOP 未归族）。
在册未动：B101（合成线索禁改判据）、B114、B110 残臂、B122/B123/B124（仅语料可见，无合成标本）、
r1_73（try-else 认领面）、`genexpr` 最小孪生仍未取得（5 条尝试全 MATCH）。
