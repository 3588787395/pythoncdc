# Round 36 OUTCOME —— 落地 R36-A：break→return 折叠读臂容器必须走语句容器表示不变量

## 一、结论

* 本轮靶 **`IQEngine/plugins/plugin_fly_data/fly_api/base.pyc` 的两个孪生方法**
  `FutureSettingStore.get_close_position_type`（strict `30/9`）与
  `has_close_position_type`（`27/6`）：**整条 `for` 语句连同体内的副作用赋值一起消失**，
  产物只剩函数尾的 `return`。
* 根因不是区域归约判据，而是**一处被上层异常兜底吞掉的 `TypeError`**：
  `_loop_generate_for` 内闭包 `_fold_break_to_return` 取臂容器写作 `s.get('orelse', [])`
  （`region_ast_generator.py:4817`），而本项目 If 节点存在 `{'orelse': None}` 这一表示——
  `dict.get` 的默认值只在**键缺失**时生效，键在值为 `None` 时取到 `None`，`len(None)`（`:4824`）抛错。
  核内 `_normalize_stmt_lists`（`:573`）的 docstring 早已把这条契约与这条故障链写死，
  并把修复声明为两层（发射点统一 list ＋ 汇总处 `:1697` 归一）；汇总归一**晚于**区域生成，
  而**同一个折叠的 while 路径 `:6381` 早已改用安全惯式**，for 路径 `:4817` 是同一处逻辑的漏网第二半。
* 发货判据 **R36-A**（`arm-design.md` §六）：break→return 折叠读臂容器时 `None` 与缺键一律按
  语句容器表示不变量归一为空表——for 路径取值式与 while 路径既有归一读取同式。
  补丁 1 处编辑、0 增删行、2 字节。
* 靶文件 **39/41 → 41/41**（整文件翻转，两个孪生一起回来），产物 `baseOK.py:313-324` 与原始源码
  逐字符一致；`logs/g4prime_r36a.txt`：严格尺 `strict clean 60/63 sigma-defect=3 sum_abs_delta=66`
  → `62/63 sigma-defect=1 sum_abs_delta=24`（残余 1 条 `OverNightOrder.__init__ -24` 属另一形状）。
* 全量 A/B（G4，发货权威）：`SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`——只动了一个文件，
  且是往好的方向。索引由 G6 拉回实测。

## 二、门禁（严格按序，逐条实测）

| 门禁 | 判据 | 实测 |
|---|---|---|
| **G0** 合成见证/控制（7 件，`test_repros/round36_for_loop_dropped/`） | 见证须在落地字节上 FAIL，控制须 PASS；候选臂须把 FAIL 全转 PASS 且不动其余 | 落地/`head` 臂 `logs/g0_landed.txt`＝`logs/g0_head.txt`：`PASS 3/7`——`r36_01/02/03` FAIL 均 `delta-21`、`r36_06` FAIL `delta-25`，`r36_04/05/07` PASS；候选臂 `logs/g0_r36a.txt`：`PASS 7/7` |
| **G1** deficit-1 池（6 件，官方尺） | 逐条 SAME（sha-first） | `TALLY SAME=6 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` |
| **G1** deficit-2 池（12 件，含靶） | 靶翻转，其余 SAME | `IMPROVED=1(base 39/41 -> 41/41) SAME=11 REGRESSION=0 MOVED=0 ERR=0` |
| **G2′** 上一轮合成复现电池（44 件，已含 R35-B 的 5 件） | 候选 vs 落地逐条 SAME=44 | `TALLY SAME=44 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（33 条全匹配不变） |
| **G3** 承重锚点电池（105 件，已含 R35-B 靶 `function.pyc`） | 候选 vs 落地逐条 SAME=105 | `TALLY SAME=105 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（75 条全匹配不变） |
| **G4** 全 402 A/B（sha-first，唯一发货权威） | 无 REGRESSION、无 ERR，且 IMPROVED≥1 | `SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`；整文件全匹配 373 → 374 |
| **G4′** 严格尺读每一个变更产物 | 变更文件在严格尺下 sigma-defect 与 Σ\|Δ\| 都不得升高 | 靶：改前 `strict clean 60/63 sigma-defect=3 sum_abs_delta=66` → 改后 `62/63 sigma-defect=1 sum_abs_delta=24` |
| **G5** `single` 靶子 | 官方尺 41/41，且在册产物 == 候选臂产物 | `total_functions 41 matched 41 rate=100.00%`；`tracked == cand-arm: True`（18163 字节）；产物 diff 恰为 +8 行（两条 `for` 循环各 4 行），无其他改动行 |
| **G5** canary | 一个在册全匹配文件产物字节不变 | `fly/data/quotation.pyc 143/143 rate=100.00%`，重生成产物 == 在册产物（183261 字节，sha256[:16] `3f2242e73d7fd56a` 两侧相同） |
| **G6** `batch --index pyc_index.json --all --round 36` | 402/402 复验、索引回写 | 402 条逐条读完、`failed_pyc 0`、`index written back`（`logs/g6_batch36.log.txt`）；索引逐条目差异（`logs/g6_index_diff.txt`，改前侧取 `git show HEAD:pyc_index.json`）：402 条 `last_tested_round → 36`，**非轮次字段变化只有 1 条**＝靶 `fly_api/base.pyc` 的 `decompile_status partial→ok`、`matched_functions 39→41`、`bytecode_match_rate 0.9512195121951219→1.0`；除此之外无状态翻转。全 ok 文件 373 → 374，Σmatched 5647 → 5649，Σfunction_count 5746 不变 |
| **G7** `stats` | 本轮只发布这一行 | 见 §五 |

零副作用面：G6 之后 `git status --porcelain` 的已跟踪改动恰为 3 项，与 G4 的 `SAME=401` 一致——
`core/cfg/region_ast_generator.py`（1 增 1 删）、`pyc_index.json`（405/405，逐条目重写）、
靶产物 `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/baseOK.py`（+8 行）；
402 份产物里只有靶那一份字节变化。

每一条 TALLY 都已就归档的两侧 `.jsonl` 复算并留档（`logs/tally_g1d1.txt`／`tally_g1d2.txt`／
`tally_g1d2head.txt`／`tally_g2p.txt`／`tally_g3.txt`／`tally_g4.txt`／`tally_b44growth.txt`）。
G2′／G4 的「改前」侧沿用上轮落地臂记录 `logs/ref_b39_landed.jsonl`（sha256[:20]
`ffb706100f285f1fb7fd`）／`logs/ref_g4_r35b.all.jsonl`（`7ac9248fe4d6f9291da2`）；沿用成立的前提
本轮由两处一手证据支撑：`r36c.py build` 断言 `mirr_head` 与工作区核文件**字节全等**，
且 `head` 臂对 deficit-2 池 12 件（含靶）重读给出 `SAME=12`。

## 三、落地内容与字节身份

* 补丁经镜像臂 `mirr_r36a` 测量后由 `land36.py` 重放（`spec36a.json`，1 处编辑，锚点两行在
  2984322 字节文件中唯一），dry-run 与 `--apply` 均以「同一份 spec 重放 == 被测镜像字节」为准：
  `applied: 2984322 -> 2984324 bytes, CRLF 48418, BOM=True, equals measured mirror=True`。
* 核身份（`logs/core_identity36.txt`）：改前 raw `92c8c2aabdcd37b9f32b`（2984322 字节）→
  改后 raw `bbfe1a414032436921ab`、正规化 `761d927617bd162b5d9f`，2984324 字节，
  CRLF 48418 = LF 48418（行尾仍统一），UTF-8 BOM 保留，`compile()` 通过。
* 站点：`core/cfg/region_ast_generator.py:4817`（`_loop_generate_for` → 闭包
  `_fold_break_to_return`）
  `_orelse = s.get('orelse', [])` → `_orelse = s.get('orelse') or []`。
* 同族第三处 `:2118`（`_build_function_def` 内同款 `s.get('orelse', [])` 读取）本轮**未改**：
  崩溃扫描（`logs/diag_p7c_crashscan128.txt`，输入名单同名 `logs/diag_p7c_roster.txt`，
  128 行里只有 21 行是语料 `.pyc`、107 行是 `test_repros/` 合成件）显示被扫到的 21 个语料
  文件中只有靶文件崩溃 2 次，`:2118` 无触发证据 ⇒ 不改无读数支撑的地方。该扫描不承担
  全语料暴露面——那由 G4 全 402 A/B（`SAME=401 IMPROVED=1 REGRESSION=0`）实测。

## 四、方法论收获

1. **「整块消失」优先怀疑机械故障，再怀疑判据**：本轮之前，`-21` 级整块丢失被记在
   #41/#43「整块丢失族」名下当作假定的算法缺陷。最便宜的判别实验不是造 CFG 探针，而是
   **给发射过程挂一次异常探针再跑一遍文件**（本轮最大一份 128 行、约 60 秒）：崩溃点、异常
   类型、抛出处的函数名一次全给。但它只量得出**名单内**的暴露面（21/402 个语料文件），
   全语料暴露面必须回到 G4 的 402 文件 A/B——把「扫过的名单」写成「全语料」是本轮记录里
   需要事后订正的一处过断。
2. **上层 `except` 兜底会把「崩溃」伪装成「判据太严」**。退化产物的形状（只剩尾 `return`）
   与「区域被判据拒绝」的形状无法从官方尺区分——必须显式测异常，否则会在消费侧加一条
   永远不该存在的判据。核心里已有的 `_normalize_stmt_lists` docstring（`:573`）其实已经
   把这个故障链写下来了；本轮的教训包括**先读自己写过的文档**。
3. **一条已修过的惯式要当契约看待**：同一个折叠的 while 路径（`:6381`）早已用
   `s.get('orelse') or []`，for 路径留着 `s.get('orelse', [])`。同层判据最稳的形态不是新增
   条件，而是**让漏网的一半向已修的的一半对齐**——它不改变任何可判形状的分类，只在原本
   必然抛错的那个求值点停止抛错。
4. **边界电池要同时留下「为什么三个控制没崩」**：`r36_04` 站在 `:4818`（单条 `break` 臂）
   先命中的一侧、`r36_05/07` 站在 `_break_to_return_map` 为空的一侧（`:4809` 根本不进折叠）。
   这三条解释把「判据范围」与「崩溃触发条件」绑在同一张表上，也顺手否证了「汇合块兼作函数尾
   才触发」（`r36_03` 中间隔一条语句照样整块丢）。
5. **代理产出的证据要分开处置**：本轮诊断代理 150 轮耗尽、未交 `ANALYSIS.md`，它自己的
   in-memory 修补产物（`logs/diag_p10_agentpatch_product.txt` 把循环摊平成三条裸表达式语句）
   被边界电池直接否证；但它的崩溃扫描（`logs/diag_p7b_crashscan.txt` 48 行、
   `logs/diag_p7c_crashscan128.txt` 128 行）就「崩溃点在哪」是决定性的，
   根因与判据由编排方接手闭合。采纳二手结论前先问：这条证据能否被一个便宜的独立实验重做、
   以及它的**覆盖面**是否配得上结论的措辞。

## 五、本轮索引读数（`stats` 原样）

G7 于 G6 回写之后执行，输出逐字符抄自 `logs/g7_stats.txt`：

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                374
  partial_pyc:           28
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5649
  cumulative_match_rate: 98.31%
======================================================================
```

## 六、残余与移交 Round 37

1. **同一文件内的另一形状**：靶 `base.pyc` 改后仍有 1 条严格尺缺陷
   `OverNightOrder.__init__ 172/148 delta-24`，它**不属**本族（本文件只崩过 2 次，都在孪生上）；
   它是台账 #41「整块丢失族 −21..−32」的在册成员，现在成了该文件唯一残余。
2. `tick_worker_thread 268/247`：单个 29 条指令的 elif 臂缺失、首合取支被借走
   （`logs/probe1_strategy_tick_worker_thread.txt`：hunk `delete orig[114:143]`）——已排除与本族同源。
3. `matcher :: match 713/689`：281 删除 + 259 插入的换位，另丢 `STORE_FAST is_first_five_trading_days`
   （`logs/probe1_matcher_match.txt`）。
4. 台账继续在册：`decrypt_database_url 295/324`（+29）、`clock_worker 1275/1291`（R22/R23 移交
   D2/D3）、`events 510/508`（已判字节码层欠定）、`_init_config 86/84`（R16 J1 在册反例，受保护）、
   #61 汇合块归属残余 ＋ 语料外见证 `r29x_01 <module> 142/138`。
5. **崩溃探针应制度化，但名单必须是全 402**：`logs/diag_p7c_crashscan128.txt` 那种「逐文件挂
   异常探针再跑一遍」本轮把一整族「算法缺陷」改判成一处两字节的漏网，成本约 60 秒；
   它的教训反面同样有用——名单里只有 21 个语料文件时，结论就只能覆盖 21 个。
   Round 37 起把该扫描的输入换成 `logs/all402.txt` 全量名单，跑一遍即可同时给出「谁崩」与
   「谁被兜底降级」。
6. 电池增量：G2′ 的 44 件应加本轮 7 件（尤其见证 `r36_01` 与控制 `r36_04`/`r36_07`），
   G3 的 105 件应加已全匹配的靶 `plugin_fly_data/fly_api/base.pyc`。
