# Tasks

目标：402 真实语料逐文件达到字节码完全一致（units 6617/6617 = 100%，files 402/402 success），quotation 153/153；`_identify_*` 与对应生成方法注释六项模板与代码一致；单元级 + 文件级双不回退门禁全程成立。
理论依据：`rules.md` §1（四原则 + C1/C2/C3 + 判据白名单 + 禁止事项 + 修复语义 + 注释口径）+ 继承 v2 spec 理论基准 I/II/III/IV。角色：主代理 = 调度 + 阶段提交 + 全量验证 + push（零实现）；测试工程师（子代理）= 逐 pyc 复现与登记破口；修复工程师（子代理）= 区域归约算法完善 + 注释合规。
纪律：每轮独立文件夹；派发子代理前必须本地提交；每轮 ≥1 个 pyc 转完全 OK（或读数净增）否则禁止下一轮；每轮提交并 push（前缀 `rr-v3rNN:`）；单条命令 ≤300s；禁止手改 `*OK.py`；判据唯一 `scripts/pyc_verify.py`。

- [x] Task 0: 三件套与语料普查就位（主代理）
  - [x] 0.1 本规范 `spec.md`/`tasks.md`/`checklist.md` 落盘
  - [x] 0.2 落盘 `tools/corpus_census.py`：输出 `total=1721 A=402 B=1312 C=7` + A/B/C 名单 + `A_delta`（A 与 `pyc_index.json` 对称差），非 0 则退出码 1
  - [x] 0.3 普查读数与名单快照写入 `baseline/corpus_census.json`（封表时点 2026-10-05）
  - [x] 0.4 本地提交（派发前置）
  - 落地补记（rr-v3r01）：本工作树重跑夹钳得 `total=1722 A=402 B=1312 C=8 A_delta=0`，+1 为 C-8
    `IQCommon/util/email_utils.py.pyc`（非字节码：magic `2320536f`、前 80 字节是 Decompyle++ 生成的 py 文本），
    已按类别登记；B/C 逐类字节级证据（1722 全量探测，非抽样）落盘 `baseline/exclusion_evidence.md`。

- [x] Task 1: Fresh 全量基线重验（主代理，作废 v2 Round2 过期读数）
  - [x] 1.1 八分片 regen：`verify_driver.py` 同构驱动（`pycdc.py -o <pyc>OK.py <pyc>`，每文件 90s 上限），产物写回 site-packages 同目录
  - [x] 1.2 八分片 `pyc_verify batch` → `baseline/shard{0..7}_report.json`（每片 ≤290s）
  - [x] 1.3 聚合 → `baseline_snapshot.md`：预期 units ≈ 6554/6617、files 369/402、quotation 152/153、34 小测试集 1505/1568
  - [x] 1.4 交叉核对：`trade_info_utils.pyc` batch 读数 = `single` 实测 36/41（证明基线与当前 HEAD 一致）
  - [x] 1.5 tests 六套件基线失败名单落盘 + 本地提交
  - 落地补记（rr-v3r01）：实得 units **6554/6617（99.0479%）**、files **369/402**、compile_error/error **0**；
    34 小测试集 **1505/1568**（all34 触发 driver 290s 上限 rc=TIMEOUT，按 v2 惯例拆 a/b1/b2 三片合规重跑）；
    quotation **152/153**（batch=single，唯一失败单元 `<module>.change_his_to_forward`）；
    trade_info_utils **36/41**（batch=single，坐实 v2 报告 35/41 为过期读数）；
    tests 六套件 277 passed / 2 failed（test_B01 + test_BOUNDARY_02，基线名单不变）/ 2 xpassed；
    逐文件与归档 round2 after 报告位移 = **0**。
    代码起点为 merge `47785867`（rr-v3r00 ⊕ main，含 d8db3448 create_user_code_iqe 回退修复）——主代理裁定项。
    工具纠正两处（非判据）：driver.py `ROOT` 上溯四级→三级 + ROOT 自检 fatal；shard/full/small34 索引 `path` 前缀重绑本工作树。

- [x] Task 2: Round 1 — 单单元损失族（22 个文件各失 1 单元，含 quotation 除外）
  - [x] 2.1 测试工程师：按索引每次只取 1 个 pyc（顺序 `IQCommon/util/cgroup_utils` → `IQCommon/util/email_utils` → `IQData/utils/calexrights_func` → `IQData/plugins/plugin_system_fly_basicdata/calexrights_func` → `IQCommon/data/finance` → `IQCommon/logger/handlers`），逐单元定位不一致点，每个缺陷建 ≥10 最小复现（深度 ≥3 变体 + ≥2 MATCH 负对照），登记破口（B98+ 续接：锚点 + 机制 + 违反条款）→ `rounds/round1/REVIEW.md` + `test_repros/round1/`
  - [x] 2.2 修复工程师：依区域归约算法封闭（判据只取白名单：块末 opcode / 后继前驱 / 异常边 / 区域成员关系；修复语义 = 封闭守卫恢复 C1/C2/C3，禁个案补丁 / 按深度特判 / 窄门控）；触及方法 docstring 六项模板 + C 条款；自测 = 复现转 MATCH ∧ 负对照不变差 ∧ 34 小测试集 ∧ 单元级不回退 ∧ IV.2 门禁自检 → `rounds/round1/FIX.md`（含「代码已落地」声明）
  - [x] 2.3 派发前本地提交；本轮结束按验证序六步验证并 push
  - 落地读数（rr-v3r01，终态详见 `rounds/round1/VERIFICATION.md`）：
    files 369→**376/402**、units 6554→**6564/6617（99.1990%）**、compile_error/error **0**、
    **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0**；电池 91/110→**108/110**（残余 2 = B101 线索 + B99，为原 19 条失败的严格子集⇒负对照零变差）；
    回退哨兵臂 17 臂 **34/34**；34 集 1505→**1516/1568**；tests 六套件 277 passed/2 failed/2 xpassed（基线名单）；
    本轮转完全 OK 的 pyc = **7**（cgroup_utils、email_utils、calexrights_func×2、executor、history_api、ptradeAccount）；
    封闭 B98/B100 及其派生 **B103**，同轮拦下并封闭 **3 次语料回退**（三次都在 34 集之外，唯 402 全量可见）；
    如实移交：B99 残余（`r1_73` + `handlers._target`）、B101 线索、`finance` 31/32、
    **B102 quotation 失败单元替换**（`change_his_to_forward`→`get_fundflow_day`，152/153 计数持平，纯计数门禁不可见）；
    语料残余 33 文件/63 单元 → **26 文件/53 单元**。
    文档落点：`REVIEW.md`、`FIX_B98_REGRESS.md`、`FIX_B100_REGRESS.md`、`FIX_B103.md`、`VERIFICATION.md`；
    未合成单一 `FIX.md`（三份分家族 FIX 文档代替，如实标注，不虚构文件名）。

- [x] Task 3: Round 2 — 双单元损失族（real_quote 43/45、risk_calculation/__init__ 41/43、future_contract_info 27/29、ptradeAccount 135/137）
  - [x] 3.1 测试工程师：同 2.1 攻击协议，逐 pyc 一个，≥10 复现/缺陷
  - [x] 3.2 修复工程师：同 2.2 约束
  - [x] 3.3 复核 + 验证序六步 + push
  - 落地读数（rr-v3r02，详见 `rounds/round2/VERIFICATION.md`）：units 6554→**6566/6617（99.2293%）**、files 369→**377/402**；
    对基线与对 Round 1 终态**双重** compare 均 REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0；compile_error/error 0；
    本轮转完全 OK 的 pyc＝**1**（`fly/logger.pyc` 63/64→64/64）；电池 `r2v3` 62 臂 85/114→**105/126**（零臂由绿转红，新增永久臂 b20/b21/b22-b25 全绿）；
    三批修复＝B108（混合极性 or 链，future_contract 27/29→28/29）、B106（处理器尾回边按循环入口归属）、B107（if 臂按循环入口认领抽象节点），
    全部标为**部分封闭**并逐条实名移交（B99、B104 a 族、B105 无合成孪生、B106 残 b09/b10/b11/b18、B107 残 b01/b03/b12/b13/b15、B108 残 c06/c11/c12）；
    quotation 152/153 失败单元仍 `get_fundflow_day`（B102 未回退）；tests 六套件 277/2/2 同名单；
    语料残局 **25 文件 / 51 单元**（48 Different control flow + 3 Different bytecode）；
    push 至 `origin/rr-v3-full-corpus`（非 main，理由见该文档 §III）。

- [x] Task 4: Round 3 — 三单元损失族（klinedata 61/64、wizard_quant_api 55/58、order_api 34/37）
  - [x] 4.1/4.2/4.3 同 Round 2 结构
  - 落地读数（rr-v3r03，详见 `rounds/round3/VERIFICATION.md`）：units 6554→**6569/6617（99.2746%）**、files 369→**378/402**；
    对基线与对 Round 2 终态双向 compare 均 REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0；compile_error/error 0；
    本轮转完全 OK 的 pyc＝**1**（`fly/common/future_contract_info.pyc` 29/29）；电池 r3 84/114→**101/122**、r2v3 105/126、r1_probe 108/110、r1_regress 34/34；
    quotation 152/153 失败单元仍 `get_fundflow_day`；tests 六套件 277/2/2 同名单；IV.2 全过；语料残局 **24 文件 / 48 单元**
  - 三批成色（如实）：B109 落地（`order_api` 34/37→35/37）、**B114 整批回滚并记「仅归档 spec 未落地」**（补完链式调用实参装配需改
    `func_call_info` 热路径，越出工单许可）、B115 落地并翻转 `future_contract_info`；
    **三单元族本身未被攻穿**（klinedata 61/64、wizard 55/58、order_api 35/37），翻转来自单单元残项——后续轮按族内单元数排序派发，不按目录顺序
  - 非确定性红处置：`verify shard4` 首跑 rc=1/MemoryError 且未写报告，同目录陈旧报告险被当本轮读数；
    已复跑确证 + 排除判据面因素（64 位解释器、最大文件 59KB）+ **落常驻牙**：`driver.py cmd_verify` 先删旧报告、跑完无新报告即 fatal
  - 新登记移交：B110/B111/B112/B113/B114 未闭，B99/B101/B102 原样在册

- [x] Task 5: Round 4 — quotation 终局单元（`<module>.change_his_to_forward` Different control flow，152→153）
  - 实际执行改道（如实记）：本轮开工前 `change_his_to_forward` 已被 Round 3 的 B100 封闭，quotation 的失败单元在
    Round 1 就被替换成 `<module>.get_fundflow_day`（B102），故「quotation 152→153」这一靶已失真。
    本轮按 Round 3 结论改用**族内单元数排序**派发给 16 个单单元文件簇（1 文件 1 单元者最多，翻转性价比最高）。
  - [x] 5.1 测试工程师：8/8 主靶逐指令第一分歧 + 8 次靶钉第一分歧；电池 31 臂 51/67（16 MISMATCH / 15 MATCH，主代理复算逐位一致）；
        结论推翻「一族通吃」假设——16 个单单元文件分为 **4 族**（A 汇合块身份 7 文件、B 双 sink 归并 4 文件、
        B117 内吞 2 文件、B111 轴 1 文件、未归族 1 文件、quotation 归 B 族）；新登记 B116/B117
  - [x] 5.2 修复工程师：**5 个工单，1 落地 + 4 整批回滚**。落地＝B116/B99 分析端 sink 归属
        （`_boolop_chain_exits_are_distinct_sinks` + 建区前置不变式门）→ `trading_dates_mixin` 14/14、`stock_position` 37/37；
        四次回滚均为「守卫命中但零翻转」按验收线当场否决（12/633、0+4、7、α/β/γ 各形），零残留、文档留配方与排除项
  - [x] 5.3 验证序六步 + push
  - 落地读数（详见 `rounds/round4/VERIFICATION.md`）：units 6554→**6571/6617（99.3048%）**、files 369→**380/402**、
        compile_error/error **0**；对基线与对 Round 3 终态**双向** compare 均 REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0；
        r4 电池 51/67→**64/75**（23/11，零绿臂转红）；r1 108/110、r1_regress 34/34、r2v3 105/126、r3 101/122；
        quotation 152/153（失败单元仍 `get_fundflow_day`，B102 未闭）；tests 277/2/2 同名单；
        本轮转完全 OK 的 pyc＝**2**；语料残局 **22 文件 / 46 单元**；
        A 族 7 文件整轮零推进，最有价值未执行线索＝`_boolop_mixed_polarity_or_chain`（`region_ast_generator.py:38240`）
        「目标必须分裂为 S/F」判据**过严**（实测成员边全 IF_TRUE 族且目标相同；a06/a07/a09 仍红 ⇒ 跳族混合/or 成员/elif 层均非必要条件）
  - 流程与工具增量：陈旧读数守卫本轮真的挡住一次（shard5 首跑 rc=TIMEOUT，若无守卫将把上一轮报告当本轮）；
        新增 `split_verify.py`（分片四分合规拆跑合并，每跑 <280s，断言 files/rows 等量）；
        本机存在**并行会话**（v2 round7 脚本、`pytest new_tests`、跑在 F: 的 pyc_verify），争用是本轮多次超时的主因，
        另含我自己的处置失误——并发两条自有链相互拖累，后续 gate 一律单链串行

- [ ] Task 6: Round 5 — Different bytecode 残余（quote 84/92 的 8 单元 + trade_live_broker 的 3 个 bytecode 单元）
  - [ ] 6.1/6.2/6.3 同构；bytecode 差异必须回到发射层归约正确性，禁止字面拼装
  - **本任务仍未执行——如实保持未勾**。第 5 轮（`rr-v3r05`）按「轴切换」纪律改打了**相邻隐式 None 出口 sink 归属轴**，
    未触碰本任务的 bytecode 残余靶（现值：`quote.pyc` 86/92、`trade_live_broker.pyc` 118/128，其中 3 个 Different bytecode 单元在册）。
  - 第 5 轮实际成果（详见 `rounds/round5/VERIFICATION.md`）：7 张工单 = **2 落地 / 5 整批回滚**；
    落地 1＝B116 分析端 boolop 链 sink 归属 → `trading_dates_mixin` 14/14、`stock_position` 37/37；
    落地 2＝**B119 循环/for-iter 出口 sink 落点 → `fly/data/quotation.pyc` 152/153 → 153/153 status=success**
    （本规范点名锚点文件首次整文件 100%，B102 关闭；含变形反证与逐指令 orig=203/cand=203/posdiff=0 复核）；
    回滚 5 张均为「守卫命中而零翻转」当场否决（633 调用/12 True/0、0+4 命中/0、or-run 完整 7 命中/0、
    α/β/γ 形 −387 变差当场删、父边级联 9 次重挂/0 翻转且 v1 曾重新打开绿单元 r1_42 被当场拦下）；
    主代理自己提出的 `LoopRegion exit=` 假设被工单**实测否证**（`Region.exit` 生成端零消费者、补交付后全局读数一字不变）
  - 第 5 轮全量读数：units 6554→**6572/6617（99.3199%）**、files 369→**381/402**、compile_error/error 0、
    对基线与对 Round 4 终态双向 **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0**；电池 r1 108/110、r1_regress 34/34、
    r4 77/87（40 臂 30/10）、r2v3 105/126、r3 101/122；tests 277/2/2 同名单；IV.2 全过；
    语料残局 **21 文件 / 45 单元**；轮门禁（≥1 语料 pyc 转完全 OK）以锚点文件达成
  - 纪律增量（写入 `rounds/round5/VERIFICATION.md` §III）：外层命令 timeout 必须大于被包工具内部 290s 上限
    （我两次把 timeout 设小，逐片被杀且无产出，守卫如实报 fatal 而非留下陈旧读数）；gate 一律单链串行；
    同一轴连续 2-3 张零翻转即换轴，残差收窄是信息不是进度

- [x] Task 7: Round 6 — 大损失文件（trade_live_broker 118/128 剩余 control-flow 单元）
  - [x] 7.1/7.2/7.3 同构
  - 落地读数（rr-v3r06，详见 `rounds/round6/VERIFICATION.md`）：units 6554→**6573/6617（99.3350%）**、files 369→**382/402**、
    compile_error/error 0；对基线与对 Round 5 终态双向 **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0**；
    本轮转完全 OK 的 pyc＝**1**（`fly/data/quote_handler.pyc` 79/79，B111 落地：
    `_boolop_member_is_loop_condition_entry` 禁止把仅反向可达的成员从已建 boolop 链中剥为后缀，
    臂边恢复 344→420 / 382→496 / 420·458→500，凭空 None 尾 sink 消失）；
    电池 r6 **70/79**（37 臂 28/9）、r1 108/110、r1reg 34/34、r2v3 105/126、r3 101/122、r4 77/87；quotation 仍 153/153；
    tests 277/2/2 同名单；IV.2 全过；语料残局 **20 文件 / 44 单元**
  - 成色如实记：**四票 = 1 落地 + 3 否证**。B121 否证（8 单元链皆收敛于单一共享目标，门在
    `region_analyzer.py:28055` 提前返回 ⇒ 加宽＝恒等变换；私有落点逐链 ∈{0,1} 从不 ≥2）；
    B120 否证于所给站点（头 NOP@44 早在 `dominator_analyzer.py:502 get_all_loops` 回边归一化时被折叠 ⇒ 同层加宽仍是恒等变换；
    G-A 经探针确认区域模型本已正确，差在 CPython 行锚放置，拒绝按 offset/文本 hack）；
    测试工程师另**推翻主代理「trade_live_broker 8/10 同源」假设**，改判六组
  - 轴切换纪律在本轮兑现：连续两票零翻转即换轴，第 3 轴（从未触碰的 B111 凭空 sink 面）即翻文件
  - 主代理数据失误登记：我给 B120/B111 简报的 analyzer 字节/行数（2045409/32168）是 B119 之前旧值，
    来树实测为 2052197 B / 32266 行（sha `0212c54e…`）；工单以实测为准故未受损，
    此后简报一律现测现用当轮 sha
  - 未推进项：trade_live_broker 仍 118/128（真根上移至 `dominator_analyzer.py:502`，为 Round 7 首选靶）

- [x] Task 8: Round 7 — 已封闭守卫族外推重放（外推/收缩双向攻击，验证守卫恢复嵌套无感而非窄门控）
  - 执行方式改道（如实记）：本轮未做「已封闭守卫族」的外推重放，而是按 Round 6 立下的**轴切换纪律**继续攻残余簇；
    外推/收缩双向攻击仍属未做项，移交后续轮（其价值：检验 B116/B119/B111/B117 四枚已落地守卫是否真的嵌套无感）。
  - 落地读数（rr-v3r07，详见 `rounds/round7/VERIFICATION.md`）：units 6554→**6574/6617（99.3502%）**、files 369→**383/402**、
    compile_error/error 0；对基线与对 Round 6 终态双向 **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0**；
    本轮转完全 OK 的 pyc＝**1**（`IQEngine/utils/profiler_func.pyc` 18/18）；
    电池 r6 70/79→**76/85**（40 臂 31/9）、r1 108/110、r1reg 34/34、r2v3 105/126、r3 101/122、r4 77/87；
    quotation 仍 **153/153**；tests 六套件 277/2/2 同名单；IV.2 全过；语料残局 **19 文件 / 43 单元**
  - 五张工单成色：1 落地（B117 出口落点认领广播抑制 → `profiler_func` 翻文件，
    `_loop_unemitted_exit_landing` 于 `region_ast_generator.py:51692`）+ 4 回滚/否证：
    B121 否证（链收敛单一目标、门在 `region_analyzer.py:28055` 提前返回 ⇒ 加宽＝恒等变换）、
    B120 否证（头 NOP 早在 `dominator_analyzer.py:502` 被归一化折叠 ⇒ 同层加宽仍是恒等变换；G-A 属行锚放置）、
    B99 两票虽零翻转但把区域结构推到正确形态（块数 42→43、off404/408 各自 distinct 认领、`elif` 链复原），
    且第二票以对象同一性 trace **否证主代理简报给的成因**（多余 `return None` 源自 `_loop_generate_while:8019` 尾随提升，非 blk@1012）
  - 纪律兑现：**轴切换第二次生效**（该簇连续 5 票零翻转 ⇒ 换轴后第一击翻文件）；
    主代理简报数据三次失真（旧字节数、被推翻成因、失效行号）全部由工单实测纠偏；
    标记核查改用**前缀口径**（九枚标记实带「 修复·…」后缀，字面量 grep 计数为 0）；
    新追加 3 条臂虽绿但**不具变形判别力**，按残项登记而非计为成绩

- [x] Task 9: Round 8 — 残余清零冲刺（任何仍未转 success 的文件逐 pyc 处理）
  - [x] 9.1 测试工程师：按残余名单每次取 1 个 pyc，≥10 复现 + 逐项判据形态评估（可封闭 / 需证伪 + C1/C2/C3 归属）
        → 四票取序：`flytools`(隐式尾 return 族) / `clock_worker` / `handlers` / NOP 族普查；
          电池 `test_repros/round8` 25→29→**31 臂**（孤儿标本经形状核对后登记，非删除）
  - [x] 9.2 修复工程师：封闭；不具备判据形态者按 wiki §8.3 证伪降级并记录机制
        → **落地 1 枚**：`[R8-B121 sinkarms]`（`region_ast_generator.py`，G1–G6 逐边落点不发射）；
          NOP 族**证伪**（语料 15 失败单元中纯 NOP 形 0 个：NOP 是行锚足迹不是缺陷）；
          `clock_worker`／尾随 return-None 提升两票回滚（成因链被实测推翻）
  - [x] 9.3 验证序六步 + push
        → **主代理全量门禁抓到工单未报的附带回退**：`history_data_source.get_bars` 19/19→18/19
          （两条 `else: return None` 臂体被误判为尾声落点；工单前提「显式 return None 必为汇合块」被证伪）。
          主代理自行落地 **G7 出口携带门**（handler-epilogue 或前驱末 opcode = POP_TOP 才算落点，
          块级 opcode 事实，无宿主类型特判），探针双向复算：`get_bars` 集合→∅、`flytools` 集合不变；
          随后 **重跑完整门禁**：402 重生成 ok=402 bad=0 → 8 片判据 rc=0 →
          units 6554→**6575/6617（99.3653%）**、files 369→**384/402**、对 Round 7 净 +1 单元 +1 文件、
          **双向零回退**；quotation 153/153、quote_handler 79/79、ptradeAccount 137/137；
          tests 六套件 277/2/2 同名单；七套电池 292 臂产物先删后重生成，读数零绿转红
          （`r4` 77→79、`r8` 56/62）；IV.2 全过。
          证据链：`rounds/round8/VERIFICATION.md`、留证 `rounds/round8/after_preG7_b121_only/`
  - [ ] 9.4 残项（登记不作成绩）：**G7 无变形牙**——`r8b121_*` 六臂只打 G1–G6，
        需补「else 臂唯一语句 = pure-none + 条件假边接入」正反两臂并验 stub-G7 变红；
        `_probe_keep/_probe_strip`（`region_ast_generator.py:48342`）与 `_probe_*`（`region_analyzer.py:11451`）
        为已落地判据的局部变量命名（`check_patch_patterns.py` PASS，不计残留），登记为清理项

- [ ] Task 10: Round 9 — 残余清零续战 + 402 全量终局复验（目标 units 6617/6617、files 402/402）
  - [ ] 10.0 **本轮工单的次序与依据**（2026-10-08 主代理重发整节，替换 2026-10-07 版——旧版仍指着两次已被否证的尝试）：

        **已否证/已回滚（不得重走同轴）**
        - `r9-fix-landing-ordering` B122「前向可达仅取 merge」（`[R9-B122 fwdonly]`）→ 否证，逐字节回滚，
          `FALSIFIED_R9B122_FWDONLY.md`；
        - `r9-fix-landing-ordering` B123「分析端认领 merge_block」→ 零翻转，按 sha256 回滚，
          裁定见 `ADJUDICATION_R9LO_REVERTED.md`（B123 回报的独立裁定）：merge 认领命中却不翻正，
          **发射边界由生成端 `_check_elif_chain` 的 per-arm/`final_else` 收集决定**。

        **在飞**：`r9-fix-elif-chain-grouping`（第三攻，生成端）——`_check_elif_chain` /
        `_if_generate_full_elif_chain`（`:15052`）的臂收集 + or/and 混合链的**嵌套操作数树**。
        涉改文件 `region_ast_generator.py`（工作树 +7 KB／131 插 29 删，仍在写）。

        **排队次序**：#16（`while True` + 体内 `if` 的汇合块被当 else；分析端 `_find_loop_else`）
        → #14（落点/重排，射程上限 14，口径须明示：多重集 14／长度 18）
        → #13（语句省略 16 单元，6 文件 3 机制；`MIN_INSTRS_FOR_SUBSCR_ASSIGN` 六处门控必除）
        → #15（隐式尾声身份，替掉 G7 的 POP_TOP 巧合支；含 #17 的 5 个少量多发射单元）。
        ~~→ #18（跳转种类互换）~~ **已撤销为独立工单**：目标解析后逐 hunk 复验＝**零条孤立极性互换**，
        `api_base.get_history_df` 与 `klinedata.kline_datetime_list` 并入 #14/#13（见
        `REVIEW_RESIDUAL_CENSUS.md` §XVI）；共享靶形「5 指令语句被压成 1 条 ∧ 别处 1 条摊成 9 条」记入 #13 机制清单。

        **#16 提前的理由（本轮新证）**：#16 改的是**区域成员关系**——把被误当循环测试的那条 `if`
        归还成体内 `IfRegion`、把 `LoopRegion.condition_block` 改判为 `None`。
        #14/#13 的取证输入正是「哪些块属于哪个区域」，成员一改，其臂收集名单全部作废重取。
        ⇒ 在飞票的名单是**在 #16 之前**取的，#16 落地后必须按新字节重跑其 `REORDER_ONLY` 12 单元名单，
        不得沿用旧名单报翻转。

        **并行派单已否决**：#16 只动 `region_analyzer.py`、在飞票只动 `region_ast_generator.py`，
        文件确实不相交，形式上符合 spec「破口族 ∧ 涉改文件不相交可并行」；但 402 门禁资源唯一，
        两条 gate 交错即无法把单元翻转归给具体一票 ⇒ 保持串行，一票一 gate 一封表。

        **每票通则**：派发前先有本地提交；翻转只认逐单元名单（完整路径 + qualname，同名多实例用最佳匹配配对），
        不认总数；零翻转即按 sha256 逐字节回滚。

        **轮门禁可达性**：只差 1 单元的 10 个文件其失败单元全部属落点族（§X），故 #14 单独即可满足
        「≥1 pyc 转 success」；#13 为第二条独立路径（`order_api` 35/37→37/37）；#15 是第三条
        （`handlers` 29/30，`_target` −2）。**#16 不产出门禁**（`trade_live_broker` 118/128，最好 121/128）。

        **上界约束**：落点修好≠单元翻正——9 个大单元压着 1–9 条内容差（§XI），#14 的成绩按实际翻转计，禁止按「35 全翻」记账。

        **分桶口径（防再次自相矛盾）**：42 单元在 §XII／§XIII 用了**两条不同的判定链**，
        同一单元可落不同桶——`routing2.py` 对 HEAD 产物实测 `POLARITY` 只含
        `{api_base.get_history_df, klinedata.kline_datetime_list}`（§XII 原表把第二条误记成 `_sync_worker`，
        已在 `REVIEW_RESIDUAL_CENSUS.md` 订正），而 §XIII 的 insert/delete 分列链把
        `get_history_df`(ins=4)、`_sync_worker`(ins=174/del=140) 划入 `NET_EXTRA`。
        ⇒ 桶数 2 与 3 之争是**链之差，不是事实之差**；自本节起只认一条链（首中即止，谓词与阈值随表打印）：
        `A==B → BLIND` ▸ `opcode 多重集相等 → REORDER` ▸ `跳转种类互换 ∧ |net|≤2 → POLARITY` ▸
        `net>0 ∧ 无 LOAD_ATTR/LOAD_METHOD/BUILD_SLICE/CALL 类多出 ∧ RETURN_VALUE+LOAD_CONST 缺 ∧ net≤6 → IMPLICIT_TAIL` ▸
        `net>0 → CONTENT_LOSS` ▸ `else → CONTENT_EXTRA`；
        `#18` 的真实名单待 #14/#13 落地后按新字节用此链重取，当前不作定数（估 2–3）。
  - [ ] 10.1 八分片 regen + batch + compare（before = Task 1 基线），双门禁 REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0
  - [ ] 10.2 逐文件 `+OK.py` 存在性与 `single` status 抽验（≥30 文件覆盖各区域族）
  - [ ] 10.3 残余非 success 文件（若有）逐 pyc 登记 → 同轮封闭 → 重跑
  - [ ] 10.4 验证序六步 + push

- [ ] Task 11: Round 10 — 注释合规终审与台账定稿
  - [ ] 11.1 `_identify_*` 十族 + 对应生成方法 docstring 六项模板逐方法一致性审计（不一致即修：以代码真实算法为准修注释，或以注释声明的正确算法为准修代码，禁含糊）
  - [ ] 11.2 `tools/kb/syntax_coverage.py` 重跑 + wiki 台账数字同步（禁手改矛盾数字）
  - [ ] 11.3 终验（全量 + quotation + tests 六套件 + 普查反向夹钳）+ 汇报终态读数（单元级/文件级/破口状态/注释合规面）+ push

Task 11 本轮实际状态（2026-10-08，逐条按完成度如实标注，勾选项未全做完就不勾）：
- 11.1 **普查在飞、修复未做（本条写入时该档尚未落盘）**：审计工程师仍在工作，预期产出
  `rounds/round10/AUDIT_TASK11_COMMENT_COMPLIANCE.md`，对
  `_identify_/_is_/_find_/_compute_/_split_/_generate_region/_if_generate_/_loop_generate_/_try_` 各族方法
  做六项模板完整度普查并分 MATCH / COMMENT_OVERCLAIMS / CODE_UNDOCUMENTED 三类；
  在其读数落盘前本条不宣称任何计数。已在本轮由其它票实测到的两处注释问题（`region_ast_generator.py:54913`
  注释自称「替代对条件的静默丢弃」而该路径仍被走到）与一处**本方误断的撤销**
  （`:19316` 「不限于顶级区域」并非矛盾——`self.regions` 实为含嵌套区域的展平列表）。
  逐方法的「以代码为准修注释 / 以注释为准修代码」未执行，故本项不勾。
- 11.2 **台账工具取数面已修正、wiki 页未重生成**：`syntax_coverage.py` 在本工作树实测分母 128 / 分子 128
  （语法面 100%，与语料成功率两回事）；`check_stale.py` 实测 `checked=60 stale=41`
  （core 24 / parsers 8 / bytecode 5 / utils 2 / pycdc 1 / pycdas 1），其中
  `parsers-ast_builder_cleaned` 页是**源码已不存在**应作废；同类硬编码仓库根已清 10 处并落常驻牙
  `tests/test_repo_tool_hygiene.py`（已入门禁 checks 段）。41 页 wiki 未逐页重生成，故本项不勾。
- 11.3 **终验读数与 push 见 `rounds/round10/VERIFICATION.md`**：本轮门禁为
  `gate_round.py 10 9 --stage regen/verify/report/checks` 四段串接一次后台跑，
  残余清单由 `residual_report.py` 出表（八份分片报告不齐即拒绝出表、失败单元在台账查不到即非零退出）。
  本轮工单收束：B129 否证回滚、B126 判据成立但零翻转回滚、**B127 装入实测后 handlers 仍 29/30 ⇒ 零翻转回滚**、
  B131/B130 诊断完成（B131 并否证本票与 B129 前提）、B132/B133 在飞。
  **截至本条写入时（03:25）本轮未新增「整文件翻正」**——B132/B133 仍在飞，若其补丁经语料实测翻正则以此处终态为准；
  未翻正则按本节标题所示如实上报残余，不改判据、不手改产物。

注：10 轮用尽仍未达 100% 时，如实上报残余清单（文件 × 单元 × 违反条款），不得为凑读数改判据或手改产物。

# Task 12（计划外续轮）: Round 11+ — 十轮用尽后按同一判据继续，直至 100%

原计划十轮已用尽且第 10 轮**未新增翻正文件**（详见 `rounds/round10/VERIFICATION.md` §二/§五 与
`rounds/round10/RESIDUAL_R10.md`），目标「继续直到 100% 成功」仍要求逐轮推进，故每轮照旧独立建档：
`rounds/round11/`，并按「测试工程师 → 修复工程师 → 主代理验证 → 提交 push」串行。

  - [ ] 12.1 在飞：B133（`load_daily` 越区汇合 + `get_trade_status` try 体尾 `break` 未发射，镜像 `D:/Temp/r133/wt`）、
        B134（`bar._history_bars` / `strategy_universe._on_clear_de_listed` 纯落点宿主诊断，只读）
  - [ ] 12.2 队列与非翻正在册票见 `rounds/round11/TICKETS_ROUND11.md`（该文件不重述读数，只登记宿主归属，
        以免成为第二真相源）
  - [ ] 12.3 并发规则固化在同文件 §三：同一时刻仅一个施工者改 `core/`，其余走镜像交付整份文件；
        改 `core/` 期间不并行派读行号的诊断票；402 门禁唯一由主代理跑
  - [ ] 12.4 每轮终态一律由 `residual_report.py` 出表（八份不齐不出表、未登记即非零退出）
  - [x] 12.5 T12-09（认领豁免 + 已发射台账）**已按门判决处置**：label 12 全量门
        `6580/6617 -> 6580/6617`、`387 -> 387`、`翻正单元=0`、`新增失败单元=0`，
        四门与 round11 同读数 ⇒ fires without flips ⇒ 逐字节撤回
        （`971df5e2c9cd7d0a`，标记 grep 0，漂移产物已删除重生成回 20555 字节）；
        读数与自订正见 `rounds/round12/FIX_T1209_CLAIM_EXEMPTION_FALSIFIED.md`
  - [ ] 12.6 T12-21（收集侧 elif 臂判据，`48b812e60ef52d27`）：matcher 单元由
        `net=+10 hunks=25 real=1` 进到 `net=+0 hunks=4 real=0`（被吞的 10 指令语句头回来了），
        七文件零连带；**落地与否由 402 门（label 13）判**，0 翻正即逐字节撤回为共要件
  - [x] 12.6 T12-21（收集侧 elif 臂判据）：单独落地为 0 翻正（门 label 13 实测），
        作为共要件与 12.7 同装 ⇒ 见 12.8
  - [x] 12.7 T12-22（生成端 or 折叠「disjunct 跨多条短路腿」判据，`851b0723732a2402`）：
        与 T12-21 叠加后 matcher 16/17 → 17/17，宿主与读数见
        `rounds/round12/FIX_T1222_OR_FOLD_MULTI_LEG.md`
  - [x] 12.8 **门 label 14 判决：`387 → 388` 文件、`翻正单元=1`、`新增失败单元=0`、
        regen `ok=402 bad=0`、残余 `14 文件 / 36 单元`、`UNREGISTERED=0`、四门同读数**
        ⇒ 本轮已解决整文件 `IQEngine/plugins/plugin_system_matcher/matcher.pyc`；
        全仓产物漂移面 = 1 个文件（两票除 matcher 外不触及任何产物）
  - [ ] 12.9 下一票 T12-23 已排队（`bar` + `strategy_universe` 各只剩 1 个失败单元，
        同一条「尾巴按区域声明的 merge 落点」判据；镜像诊断已给出：声明的 merge 就是正确落点，
        而尾巴发射处从不读它 ⇒ 合规的归处是分析端链记录，不是生成端事后重排）
# Task Dependencies

- Task 0 → Task 1 → Task 2 … Task 11 严格顺序（前一轮门禁未过禁止开启下一轮）
- 每轮内：测试工程师 → 修复工程师 → 主代理验证 → 提交 push 串行；多位修复工程师仅在破口族 ∧ 涉改文件不相交时可并行
- Task 10 的终局复验依赖 Task 2–9 全部封闭标记落盘（grep 落地标记为凭）
- 每次派发子代理前必须先有本地提交（用户硬约束）

## 14. 第 14 轮（诊断轮，0 落地）

- [x] 14.0 自我纠正：上一会话的合成电池是空判据（手写源当 --source）；改为只判 pycdc 产物后 9 例全红
- [x] 14.1 R14-01 or 链末操作数为链式比较：四处识别端阻塞点全部打开（认领守卫 29975 / hop 安全闸 29786 / W14 尾钳 30234 / _boolop_resolve_merge elif 支 27989），条件文本转对；剩余真障碍=父 IfRegion 条件装配（blocks 组装与标志继承两处已实测排除）；电池 repro/ RED=9/9
- [x] 14.2 R14-03 api_base.get_history_df 收到 5 行最小例：触发条件是「负极性 and 链里有一个操作数是链式比较」；对照 m02（纯比较成员走 BoolOp 链+R14c 闩锁）绿；电池 repro_ccneg/ GREEN=1 RED=3
- [x] 14.3 13 文件面板 A/B：分析端四臂 13/13 与基线逐文件相同（0 翻正 0 回归）⇒ 不落地，core/ 保持基线字节
- [x] 14.4 本轮 checks 阶段零漂移：quotation 153/153、small34 1534/22、自证 153/153（变异常量 1/153、极性 1/153）、pytest 2 failed/280 passed/2 xpassed
- [ ] 14.5 R14-02/R14-04 待下一票：判据「成员真值边==本区域 merge_block? ∧ then 体==落空边?」，链式比较按末段判极性，单点实现两处复用（api_base 需取反、strategy 需取消取反）；验收=两电池先绿→13 文件面板→完整门链 label 17 vs 16→提交推送

## 15-18. 第 15–18 轮（15/16 为诊断+双臂轮，18 为落地轮）

- [x] 15.1 合成电池空判据自我纠正：判据只喂 `pycdc.py --region` 产物；手写源当 `--source` 的 9 例「绿」全部作废，重跑后 9/9 红
- [x] 15.2 识别端四处链走判据（认领守卫 29975 / hop 安全闸 29786 / W14 尾钳 30234 / `_boolop_resolve_merge` elif 支 27989）与 blocks 组装两点、Phase-3 标志继承点全部实测惰性 ⇒ 该族施工点收敛到父 IfRegion 臂成员/merge 身份
- [x] 15.3 R14-04（同目标真值边取反判据）在小电池与面板上零回归，但当时 0 单元翻正 ⇒ 暂存共要件
- [x] 18.1 **口径自我纠正**：`dis.hasjrel/hasjabs` 是操作码编号列表而非名字列表，旧 hunk 工具把内容差与落点差混为一谈；修正后 34 个残差单元中 6 个为纯落点残差、5 个为内容缺失型，名册与优先级据此重排（工具 `unit_diff.py` 已入仓，只做测量，名册仍归 `residual_report.py`）
- [x] 18.2 T12-11 旧前提被推翻：`clock_worker` 识别端完整（unowned 指令=0，字节偏移≠块边界），缺陷在发射端批量认领（`_if_generate_normal:21290` + `_process_if_blocks:25339`）；成员版判据把该单元 −113→−6 并找回三条被吞语句，但门链 label 17 读数 `6583/6617→6583/6617、翻正 0、回退 0` ⇒ 依 fires-without-flips 逐字节回退，脚本与共要件留档
- [x] 18.3 **R14-04 落地**：提交 `1577a2b0`；门链 label 18 vs 16 ⇒ `regen ok=402 bad=0`、`[units] 6583/6617 -> 6584/6617 (99.5013%)`、`[files] 390 -> 390`、`文件级回退=0 / UNIT_REGRESSIONS=0 / 新增失败单元=0 / 翻正单元=1`（`klinedata <module>.kline_datetime_list`，该文件 62→63）；checks：quotation `153/153`、small34 `1535/22`（新封盘）、自证 `153/153 Equal` 且两变异各抓 1/153、pytest `2 failed / 280 passed / 2 xpassed`（零新增失败）；证据与产物提交 `a9dedc29`+`12378d5e`，已推送 `rr-v3r01-f557fd`
- [x] 18.4 handlers._target 三个候选守卫全部实测无效（`_nested_merge_return_skip` 在本码对象内匹配数 0；两条 while 臂尾剥离器消融后逐字节不变；`_is_return_none_join_block` 加 (2c) 后 8 文件面板读数与控制全同）；且产物源码**已含** `return None`，故缺口是 CPython 对循环两条出口边的跳转穿线，不是丢语句 ⇒ 该票改列为形状复现票，禁止再加发射/剥离守卫
- [x] 18.5 R15-10 新族登记 + 仓库常驻电池 `rounds/round18/repro_retbreak/`（4 例：r01 红 / r02 红（控制例因第二缺陷 `while…else` else 子句丢失而无效，须重做配对）/ r03 绿 / r04 绿）；机制：外层 `while True:` 被消除后内层真 `return` 臂被发射成 `break`，角色判定点 `:13280`/`:12178`，正解在识别端块角色（臂块末指令为 RETURN_VALUE 时不得记 BREAK）
- [ ] 19.1 R14-05（镜像修理工进行中，独立复判其电池产物仍 1/2 红）：`api_base.get_history_df` 距 28/28 只差 2 处落点、`strategy.tick_worker_thread` 只差 4 处；施工点=链起点资格（`_identify_boolop_regions`）+ 父臂入口与 merge 身份同判；验收=电池 2/3 全绿 → 13 文件面板 → 门链 label 19 vs **18** → 提交推送
- [ ] 19.2 trade_live_broker 大缺失家族（`_process_order` −465/507、`_process_cancel_order` −293/333）：`@94` 条件臂身份被读反（真边=循环体被发射为 `break`，体成为其后死代码）；先做最小复现再动判据
- [ ] 19.3 本轮推送受阻一次（github 443 连接重置，6 次重试未成，第 2 轮重试成功）：`unit_diff.py` 提交 `ec23262c` 已确认远端=本地
- [x] 19.4 T19-4 order_api 根因落盘（提交 `1637eba7`）：`region_ast_generator.py:41700` `_ternary_nested_in_container_construction` 的「栈底是其它表达式」逃逸（`:41748-41750`）放过**未闭合调用前缀**——`@414` 17 指令块把 `strategy_log.info('…'.format(…))` 的接收者与三元条件测试融在一起，识别端照建 `TernaryRegion(entry=condition_block=@414)`，发射端只发裸三元，宿主语句消失（`future_order −27 / option_order −39`）；新建仓库常驻电池 `rounds/round19/repro_orderapi/`，landed 字节读数 `GREEN=2 RED=3`（o5 与整文件同形，o2/o3 为绿对照）；已实测排除两条修法（`_EXPR_REGION_TYPES` 去 TernaryRegion ⇒ 逐字节不变；旁路 `child_expr_regions` 分派 ⇒ 三元消失而宿主调用不回来）⇒ 镜像修理工 r19t1 施工中（判据＝栈效应跨度扩到栈平衡回 0 的整条语句，复用 `_instruction_stack_effect`，不建第二真相源）
- [x] 19.5 共用尾轴**合形不复现**实测：`rounds/round19/repro_tail/` 13 例（10 靶形 + 3 绿控）在 landed 字节上 `GREEN=13 RED=0`；同轮 `unit_diff.py` 复核 `trade_info_utils.query_strategy_id` 读数成立（`orig[108..109 @634]` 1 条 `JUMP_FORWARD→共用尾` 被写成 2 条内联 `LOAD_CONST None/RETURN_VALUE`，净 −1）⇒ 本族禁止再走「先造最小复现」开票路线，该 13 例改作隐式 return/汇合尾机器的常驻回归护栏（改动该机器必须先保 `GREEN=13`，再跑整文件门）
- [x] 19.6 残余逐读改判（提交 `80d82446`，`rounds/round19/MEASURED_R19_EPILOGUE_SCOPE.md`）：`quote.get_real_from_zeromq` 的两条可读 hunk 是 `orig LOAD_FAST exc_tb` 对 `prod LOAD_GLOBAL exc_tb` ⇒ 从 #15「共用尾」族改判为「except 处理器形参作用域」族（与 #23「函数内 import 丢失」同族两面）；`handlers._target` 复核为 `len orig=199 prod=197 delta=-2`、1 hunk 无成对插删＝`LOAD_CONST None/RETURN_VALUE` 整对未发
- [ ] 19.7 本轮并行派发纪律：两名镜像修理工同时作业且涉改文件不相交（r19t1→`region_ast_generator.py`、r19t2→`region_analyzer.py`），主代理独揽 core 安装权与门链；主代理在两份 DELIVER 回收前不编辑任何 core 文件，只做只读测量与文档落盘
- [x] 19.8 r19t2 判决 **FALSIFIED**（提交 `d170cefe`，存档 `rounds/round19/banked_r19t2/`，交付文件 sha16 `a6861f946f750aca`）：api_base 仍 27/28、strategy 仍 26/27，零回退（5 电池全同 + 15 面板 SAME）；**买到的读数**＝`_r16_boolop_cc_run_operand` 卡在第 (2) 项「前缀成员尾跳转同落一块」对 `A and (B or cc)` 混合前缀结构性不可满足（`_T` 取 B@992 的 and 假出口 @1098，与 B@996 的 or 真出口 @1040 冲突），strategy 侧该判据已 True 而卡在 W14-A 尾钳从 cc 成员自身 fallthrough 取 `@552` 而非成功边 `@568`；并消融隔离出旧补丁的回归臂「强制 `merge = BoolOpRegion.merge_block`」单独施加 ⇒ api_base 27/28→**25/29** 过度收集，去掉后子区反而正确 `IfRegion e=996 cond=1008 merge=1782 then=[1040] else=[1098,1142,1200]`
- [x] 19.9 **测量口径自我纠正（判据是控制流图等价，不是指令文本）**：`unit_diff.py` 的 docstring 承诺的落点列**从未实现**，`dump()` 清空跳转操作数后纯落点残差读成 `hunks=0 delta=0`，与判据 failure 直接矛盾（api_base/strategy/_process_tick_order 三例实测）。已修：新增 `dump_raw()` 在 `equal` 段逐槽比较、`pick()` 接判据点号 qualname 并对裸名多匹配打 `AMBIG_NAMES`、落点判等**经 SequenceMatcher 匹配块映射目标**（只比偏移或只比索引都会被前部一处内容差造成的 2 字节位移造假：实测 `handlers._target` 127 条、`klinedata` 76 条、`quote.check_frequency` 24 条假落点，真差各 1~3 处）。绿控自证 `base_api::<module>`、`matcher::<module>` 均 `hunks=0 landings=0 judge_diff=False`。重排 31 个可测残余单元（表见 `MEASURED_R19_2_LANDING_COLUMN_FIX_AND_RANKING.md`，全表 `D:/Temp/r150/residual_ranked_fixed.txt`）：**纯落点单元 6 个**，其中 api_base（0/2）与 strategy（0/4）各自是本文件唯一失败单元 ⇒ 一条判据两整文件；`klinedata`（1 hunk + 2 影子）同档
- [ ] 19.10 据此重派 r19t4（`region_analyzer.py`，以 19.8 的两张卡点为靶心：A 父 `IfRegion e=992` 与子区争抢 `@1040`、B run 发现顺序使 `chain_start B@992 -> []`），落地口径放宽为「api_base 28/28 **或** strategy 27/27 且另一文件不降、零共面回退」；r19t3 同步做 klinedata 的只读诊断（独立进程建 CFG 普查 + 镜像消融定位发射支）
- [x] 19.11 **T19-4 门链判决＝不落地并逐字节回退**（`ADJUDICATION_R19_T19-4_REVERTED.md` + `rounds/round19/banked_r19t1/`）：order_api 35/37→**37/37**（`future_order`/`option_order` 两单元翻正、整文件翻绿），但门链 label 19 vs 18 读 `[units] 6584/6617 -> 6584/6617`、`[files] 390 -> 389`、`文件级回退=2 / 新增失败单元=2`（`plugin_system_log/__init__.DefaultLogger.setup` 10→9 跨度越界吞后续语句 −16；`plugin_system_trade/function.get_entrust_item_info` 71→70 前缀重复发射 +8），checks 阶段 pytest **3 failed**（封盘 2 failed）⇒ 净下降 ⇒ restore byte_exact（`5066b1367b6de3c7`/`e1e0dcda2e745298`，`git status core/` 空）。17 文件面板对这两处回退**完全失明**，pytest 亦只有 checks 阶段可见 ⇒ 收窄规格与必测四件（三单元 + pytest）已写入 banked README
- [x] 19.12 登记我自己的「假否」教训一次：多文件判据只装一个文件测得 `GREEN=2 RED=3`（与基线同分）被我误读成零翻正；实因该路线必须同时改 `core/cfg/ast_generator_v2.py`（融合三元折叠历史上只接 `IF_NONE` 极性）。⇒ 装前先 `diff -rq` 数清改动文件数，单文件安装的零翻正不作判决
- [ ] 19.13 回退后以 pristine 代码重跑门链（label 19 覆盖 `after/`），使 site-packages 产物、名册 JSON 与代码三者一致；随后 `residual_report.py 19 18` 封表
- [x] 19.14 回退后重封门链（pristine 代码）：`regen ok=402 bad=0`、`[units] 6584/6617 -> 6584/6617`、`[files] 390 -> 390`、`文件级回退=0 / UNIT_REGRESSIONS=0 / 新增失败单元=0 / 翻正单元=0`、quotation 153/153、small34 1535/22、自证 153/153 Equal（两变异各抓 1）⇒ 站点与名册与 pristine 代码一致（回退只还原代码不重扫产物会留下陈旧被打红产物，本轮已重扫）
- [x] 19.15 **pytest 由 2 例升至 3 例的真因不是本轮补丁**：常驻守卫 `tests/test_repo_tool_hygiene.py::TestNoHardcodedRepoRoot` 抓到 `unit_diff.py:17` 写死 checkout 绝对路径（该文件是在门 18 checks 跑完之后才入仓，故封盘读数仍是 2 failed）。⇒ 依 [[register-reds-dont-relax-rulers]] 只改工具不改判据：`unit_diff.py` 与 `repro_tail/make_tail.py` 的 ROOT 改为按 `__file__` 推导（unit_diff 上溯 3 级、make_tail 上溯 6 级；我第一次写 5 级，`make_tail --run` 立刻以 FileNotFoundError 自证错级），复跑七套＝**2 failed / 280 passed / 2 xpassed**（与封盘同），两工具的相对路径调用与 `GREEN=13 RED=0` 均复验通过
- [x] 19.16 T20-2 handlers 诊断回报 **BLOCKED 且推翻本票前提**（`rounds/round19/banked_r19t5/README_T20-2.md`）：`@404` 与 `@408` 是两个不同 CFG 块，均在 `LoopRegion@90`（`else_blocks=[@408]`）与 `IfRegion@0.then_blocks=[@90,@408,@404]` 内；产物里活下来的 `return None` 出自 **@408**，丢的抽象节点是 **@404**；`:5364` 声称 `_generate_block_statements` 对 @404 返回 `[]` 在当前字节上是假的（返回完整 `Return(_explicit_return=True)`），且同时移除 `:5378` 清扫与 `:25301 [R2-B107]` 两处认领点产物仍逐字节相同 ⇒ 折叠既非发射支也非认领/顺序问题；15 次消融 12 次逐字节相同，唯一能动字节的 `[R5-B119 loopsink]`（生成端 `:52045` / 分析端 `_loop_tail_exit_sink_pair` `:28390`）打的是**另一对** @1016/@1020（`landings 3→0` 仍 29/30）。0/1/2/3 条 return 与 `while…else` 最小核全部编译成**一条共享尾**⇒ 原字节码的相邻两对是 CPython 按出口边复制，非反编译可折叠点；本票此前「发射端折叠」的说法作废，改列为「源码形状可表达性」问题

## 19A. 第 19 轮落地（T19-4 收窄后翻正并过门）

- [x] 19A.1 **收窄判据落地**：在 r19t1 的两文件路线上，把 `_is_statement_close_op` 的闭合族**去掉 `STORE_*`**
      （`region_ast_generator.py`，加 3 行注释；理由写进注释：赋值语句的栈深归零点落在存目标指令上，
      此时跨度会把整条赋值语句吞成条件片段）。镜像三点复测：
      `order_api 37/37`、`plugin_system_log/__init__ 10/10`、`plugin_system_trade/function 71/71`
      ⇒ 门 19 的两处回退**同源于这一族**，一处收窄同时解掉两条（不是两个独立缺陷）。
- [x] 19A.2 安装凭据：`region_ast_generator.py 5066b1367b6de3c7 -> dff6e81a5f2ff9f6`、
      `ast_generator_v2.py e1e0dcda2e745298 -> beeaf14435e22922`（均 py_compile 通过；备份在
      `D:/Temp/r150/deliver_backup/`，restore 可逐字节还原）。装后实时树电池：
      `repro_orderapi GREEN=5 RED=0`、`repro_arm 0G/3R`、`repro_ccneg 3G/1R`、`repro_retbreak 2G/2R DRIFT=0`
- [x] 19A.3 **门链 label 19 vs 18 全四阶段通过**：
      `regen ok=402 bad=0`；`[units] 6584/6617 -> 6586/6617 (99.5315%)`；`[files] 390 -> 391`；
      `文件级回退=0 / UNIT_REGRESSIONS=0 / 新增失败单元=0 / 翻正单元=2`
      （FIXED `order_api <module>.future_order`、`<module>.option_order`；UNIT-UP order_api 35 -> 37 ⇒ 整文件翻绿）；
      checks：`quotation 153/153`、`small34 units_success 1536 -> 1537 / success 22 -> 23`、
      自证 `153/153 Equal` 且两变异各抓 1、`pytest 2 failed / 280 passed / 2 xpassed`
      （＝封盘的常驻两红，零新增失败）
- [ ] 19A.4 下一轮：残余 **11 文件 / 31 单元**（`RESIDUAL_ROUND19.md`）。可直接接手的三张：
      ①`api_base`+`strategy`（各只差落点 2/4，卡点＝父 IfRegion 与子区争抢 @1040，归处为调用方停止集
      `get_if_branch_boundary_stop`/`[R31-B]`，见 `banked_r19t4/README.md`）；
      ②`klinedata`（两处同修：臂尾出口身份 + `@974/@978`，见 `banked_r19t3/` 与 `DIAG_R1516`）；
      ③`handlers._target` 前提已否证（CPython 按出口边复制尾对，非发射折叠），改列为源码形状可表达性问题。

## 19B. 第 19 轮收口状态与第 20 轮交接（park 记录，2026-10-09 收尾）

- [x] 19B.1 **当前封盘＝已验证**：`core/cfg` 三件 `region_ast_generator.py dff6e81a5f2ff9f6`、
      `ast_generator_v2.py beeaf14435e22922`、`region_analyzer.py 640d33a77dcb71c2`；
      `git status --porcelain core/` 空；本地=远端 `e3df7faa`；
      语料 **6586/6617 单元、391/402 文件**（门 19 四阶段全过，`rounds/round19/after` 八分片名册入库），
      `order_api.pyc` 就地产物复验 `37/37`。残余 **11 文件 / 31 单元**＝`rounds/round19/RESIDUAL_ROUND19.md`。
- [ ] 19B.2 **在飞工程师（勿重复派发、勿与其争抢同一文件）**：镜像 `D:/Temp/r20d`，
      工单 R20-1（api_base + strategy，任务 #47），**只许动 `core/cfg/region_analyzer.py`**，
      交整文件 + `FIX_T20-1.md`（其文档当前停在 step 0：镜像已建、电池已按同深度放置）。
      其起始材料＝`rounds/round19/banked_r19t4/region_analyzer.py`（`5ea802f2975b1f35`，
      我已实测：无害但惰——api_base 27/28、strategy 26/27、klinedata 63/64、quotation 153/153、broker 118/128）。
      回收时的前四步：①`diff -rq` 数清它改了几个文件（上轮两文件判据只装一个文件＝假惰）；
      ②在自己的丢弃式镜像里装**全套**后测两文件 + 6 电池；③只有出现
      `api_base 28/28` 或 `strategy 27/27` 才安装到实时树；④跑门 **label 20 vs 19**
      （`python -X utf8 -u .trae/specs/.../gate_chain.py 20 19`，先 `--dry`）。
- [ ] 19B.3 已预消化、可直接开工的第二张：R20-2（任务 #48，`real_quote.get_tick_direction`，
      判据＝`elif_final_else` 不得是链的续体块；判决性实编实验在 `rounds/round20/NOTE_T20_ORDERING_WALL.md`；
      **属生成端文件**，与 19B.2 的分析端不冲突，可并行，但两条判据必须**分别跑门**，不得同门混判）。
- [ ] 19B.4 本轮（第 19 轮）满足「至少解决一个 pyc」：`order_api.pyc` 35/37 → **37/37** 整文件翻绿。
      目标「全部 pyc 成功」**未达成**，剩余 11 文件 / 31 单元；已否证的轴见
      `pythoncdc-falsified-residual-axes` 与 `rounds/round19/REGISTER_R19_NEGATIVES.md`，
      下一轮不得重走：handlers `_target` 的发射端折叠（前提被否证）、
      「子区内部块并入父臂停止集」的直白写法（零翻正 + 4 处回退）、
      klinedata 单点修（另一处未修则零翻正）。
- [ ] 19B.5 收尾快照（17:13 本地 00:13）：实时树＝已验证态（`git status core/` 空，
      `dff6e81a5f2ff9f6 / beeaf14435e22922 / 640d33a77dcb71c2`，本地=远端）；
      工程师 r20d **仍在飞行**，此刻刚做完基线面板（`prod/base/*`，镜像分析端仍为
      pristine `640d33a77dcb71c2`，`DELIVER/` 只有其 FIX 文档）⇒ 未产生可安装候选，
      亦**不要**另派第二名分析端工程师重复该票。
      两条待用的判据入口已备好：R20-1＝父区臂边界取子区 merge（`@1098`）而非顺序依赖，
      见 `banked_r19t4/README.md`；R20-2＝`elif_final_else[0]` 若等于任一臂体末跳落点
      或末臂落空后继即判幻影 else（实值 `entry=858 / elif_final_else=[1102] /
      @1022 JUMP_FORWARD->1102`），但**先用只写文件计数器证明插桩命中**，
      我两次未命中的教训写在 `rounds/round20/NOTE_T20_ORDERING_WALL.md`。

## 19C. 候选落地 runbook（照抄即可，约 8 个 turn；勿凭记忆改步骤）

前提：`r20m`（`D:/Temp/r20m/DELIVER/`，只碰 `core/cfg/region_ast_generator.py`，
必要时另交 `ast_generator_v2.py`）带回 `LANDED-READY`。**未翻正单元就不要走这段。**

1. 数清交付文件个数并核对哈希（两文件判据只装一个＝假惰，本轮踩过）：
   `ls -l /d/Temp/r20m/DELIVER/ && sha256sum /d/Temp/r20m/DELIVER/*.py | cut -c1-16`
2. 丢弃式镜像先复测（不动实时仓库）：
   `M=/d/Temp/r20v; rm -rf $M; mkdir -p $M; cd <repo> && cp -r pycdc.py core parsers utils bytecode scripts $M/`
   `cp --parents -r .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round14/{repro,repro_arm,repro_ccneg} .../round18/repro_retbreak .../round19/{repro_orderapi,repro_tail} $M/`
   覆盖交付文件 → `python -X utf8 -m py_compile $M/core/cfg/region_ast_generator.py`
   → 在 `$M` 里跑 6 个 runner 与 `strategy`/`api_base`/`trade_live_broker`/`real_quote` 判决。
   门槛：`strategy 27/27` 或 `api_base 28/28`，另一件不降，六电池不倒。
3. 安装（备份已锚定在落地态 `dff6e81a5f2ff9f6 / beeaf14435e22922`）：
   `python -X utf8 /d/Temp/r150/install_deliver.py install <DELIVER文件> core/cfg/region_ast_generator.py`
   失败或要回退：`python -X utf8 /d/Temp/r150/install_deliver.py restore core/cfg/region_ast_generator.py`（会打印 byte_exact）
4. 门链（一次后台跑完四阶段，勿逐阶段占 turn）：
   `python -X utf8 -u .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/gate_chain.py 20 19`
   覆盖墙钟用一条 `sleep 275` 的有界命令轮询：`grep -E "STAGE_END|units\]|files\]|gates\]" /d/Temp/gate_chain_20_*.log | tail`
   读数必须：`regen ok=402 bad=0`、`files >= 391`、`文件级回退=0`、`新增失败单元=0`、pytest 不新增红。
5. 封表：`python -X utf8 .trae/specs/.../residual_report.py 20 19 > rounds/round20/RESIDUAL_ROUND20.md`
   （UNREGISTERED 必须为 0，否则先补登记再提交）。
6. 提交并推送（含 `rounds/round20/after/` 八份 JSON、工程师 FIX 文档、门链证据）：
   `git add .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/ && git commit -q -m "gate 20: …" && git push origin HEAD:refs/heads/rr-v3r01-f557fd`
   网络会间歇失败：用 `git ls-remote origin refs/heads/rr-v3r01-f557fd` 判真，不要相信管道的退出码。
7. 若门链出现回退：立即 `restore` 两个文件 → `gate_chain.py 20 19` 重跑一遍以把 `after/` 与产物扫回一致态，
   再把负极性写进 `rounds/round20/` 登记（本轮 banked_r19t1 就是这么处理的）。

## 20. 第 20 轮 park 记录（2026-10-10 02:14 封版，编排侧 turn 预算见底）

在飞状态（**勿重复派发，勿在它测量期间改仓库 `core/`**）：
- 工程师 `r20m`（镜像 `D:/Temp/r20m`，只拥有 `core/cfg/region_ast_generator.py`）仍处在**基线取证阶段**：
  `DELIVER/` 里只有 `FIX_T20-3.md`（31 行，仅写了镜像搭建记录），**没有任何 `*.py` 交付文件**，
  镜像内的 `core/` 与仓库字节一致（未打过补丁）。判活依据不是 mtime 而是进程：
  02:13:32 / 02:13:38 两个 `D:\Python\python.exe` 与 `out/*_prod.py` 的写入时刻成对出现。
- 它下一步产出的即是 §19C 的输入；在它写出 `DELIVER/*.py` 之前，§19C 的第 1 步不可能通过。

实时仓库状态（可直接采信，无需重测）：
- `core/cfg/` 三文件哈希 `dff6e81a5f2ff9f6`（generator）/ `beeaf14435e22922`（v2）/ `640d33a77dcb71c2`（analyzer），
  `git status --porcelain -- core/` 为空；门读数 6586/6617 units、391/402 files，残差 11 files / 31 units。
- 本轮新增常驻哨兵 `tests/test_product_freshness.py`（4 个小样本重生成后与在位 `*OK.py` 逐字节比对，
  `1 passed in 4.40s`）：它把"回退后产物是旧字节"这个坑变成每次 `pytest` 都会叫的红灯，不再依赖人的记性。

恢复后的前四步：
1. `ls -l /d/Temp/r20m/DELIVER/`；仍无 `*.py` ⇒ 先读 `FIX_T20-3.md` 判断它是截断还是在飞，截断则按 §19C 第 1 步的失败面处理（不收票）。

02:27 复核（补记，覆盖上一条"基线取证阶段"）：`r20m` 已进入**打补丁并测量**阶段——镜像 `region_ast_generator.py`
在 02:14→02:27 之间换了两次字节（`5d3ff1d071981e84` → `5c2acfa8b4bd5aac`），说明它仍在 A/B 迭代，
`DELIVER/` 里依然只有 10 行的 FIX 文档，`ast_generator_v2.py`/`region_analyzer.py` 与仓库一致（只碰 generator，票面正确）。
**移动中的哈希不是判据**：此时安装等于把一次未完成的实验当成结论（见 §15 快照规则），必须等它自己写出
`DELIVER/*.py` 并在文档里声明翻正读数或 revert。

02:34 收票（票已闭合，见 `rounds/round20/ADJUDICATION_R20_MERGE_LANDING_FALSIFIED.md`）：`r20m` 交付
`DELIVER/region_ast_generator.py`，`cmp` 实测**与落地态逐字节相同**（sha16 两侧 `dff6e81a5f2ff9f6`），
即 **0 落地、不安装**；实时仓库 `core/` 依旧干净，门读数仍是 6586/6617 units / 391/402 files。
它否证了我票面的判据本身：generator **没有"把尾巴跳到声明 merge"的执行通道**
（`:39406` 属 `_try_build_and_inner_or_pattern`@`:39338`，`merge_offset` 全文 6 次且 0 次写进发射目标；
AST 不带跳转操作数，落地全由嵌套涌现），并且 `_if_generate_elif_chain` 在 strategy 全模块只进入 1 次，
所以 `:19454` 与五个裸 `Continue` 分支对这一族是瞎的。残留族的根在 **analyzer**
（`inline_boolop_chains[id(cond_block)] = None`；`else=[1098]` 被给了 `IfRegion@1008` 而非 `@992`），
下一票须拥有 `core/cfg/region_analyzer.py`、generator 禁改，并受 §19B 记录的顺序墙约束。

## 20B. 再 park（2026-10-10 02:40，编排侧 turn 预算 <10）

- 在飞：**工程师 `r20n`**（镜像 `D:/Temp/r20n`，只拥有 `core/cfg/region_analyzer.py`，generator 与 v2 对它只读），
  02:38 派出，票面 = 任务 #50：在**识别期**声明 BoolOp 链成员与 arm 属主
  （`inline_boolop_chains` 对条件块 512/992 实测为空；`else=[1098]` 目前归 `IfRegion@1008`；块 536 归 `IfRegion@536`）。
  它的 `DELIVER/FIX_T20-4.md` 被要求作为 step 1 建立并增量追加，所以截断也能读到判据与读数。
- **此刻不要动 `region_analyzer.py`／`region_ast_generator.py`，也不要跑门链**：它在镜像里测量，
  我改仓库字节会让它的前提失效；402 产物若正在删除重写则任何读数都不可采信。
- 恢复后的第一步 = 照 §19C 执行，只把文件换成 `core/cfg/region_analyzer.py`，备份锚点 `640d33a77dcb71c2`，
  门槛 `strategy 27/27` 或 `api_base 28/28`、另一件不降、六电池不倒
  （`repro 9R / arm 0G3R / ccneg 3G1R / retbreak 2G2R / orderapi 5G / tail 13G`）。
- 仓库此刻：`git status --porcelain -- core/` 空；三哈希 `dff6e81a5f2ff9f6 / beeaf14435e22922 / 640d33a77dcb71c2`；
  门读数 6586/6617 units、391/402 files；残差 11 files / 31 units；
  哨兵 `tests/test_product_freshness.py` 与 R20-3 裁定已推送（远端 `527eeb18`，`git ls-remote` 判真）。

## 20C. 三名并行工程师与两件我实测的新事实（2026-10-10 02:45）

**在飞（两个，互不重叠，都在各自镜像里测量）**：
- `r20n`（`D:/Temp/r20n`，拥有 `core/cfg/region_analyzer.py`）= 任务 #50，BoolOp 链成员与 arm 属主的识别期声明。
- `r20q`（`D:/Temp/r20q`，**只诊断、不许改仓库字节**）= 任务 #51，函数内 `import` 丢失的主机定位。
- 另：`r20m` 已收票（0 落地），不要再派同一机制。

我在落地字节上自己测的（无门链在跑，`tests/test_product_freshness.py` 已证产物新鲜，读数可信）：
- `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` = 41/43，两个失败单元**不是同一机制**，
  所以 #23 那张票只能按一个单元记账：
  - `<module>.PluginRiskCalculation._on_publish_after_trading_end`：`len orig=528 prod=524 delta=-4 hunks=3 landings=1 judge_diff=True`
    ⇒ 一条函数内 `import` 整串未发（#23 轴）；
  - `<module>.PluginRiskCalculation._save_testds_to_csv`：删 `LOAD_CONST 0.01 / PRECALL / CALL / POP_TOP`
    ＋ 多插一条 `JUMP_FORWARD` ＋ 3 处落点差 ⇒ **另一条轴**，禁止与上者捆绑进同一票。
- 发射点 grep 结果（供 #51 用，不必重扫）：真正的语句发射器在
  `core/cfg/ast_generator_v2.py:23759`（`opname == 'IMPORT_NAME'`）与 `:23803`（`IMPORT_FROM`）；
  推导式内的 import 在 `core/cfg/comprehension_generator.py:917/:1028`；
  `region_ast_generator.py` 的 107 处 `IMPORT_NAME` 绝大多数是 opcode 分类集合而非决策点。
- 记账口径：#51 若翻正只到 41→42/43（不翻文件），但单元 6586→6587，符合"以单元翻正收票"的既有口径（gate 18 的 klinedata 62→63 就是这么收的）。

**恢复后的顺序**：先读 `r20n` 的 `DELIVER/FIX_T20-4.md` 走 §19C（换文件为 analyzer，锚点 `640d33a77dcb71c2`）；
门链跑完再动 `r20q` 的诊断结论（它不改字节，因此不占门资源，但它若在测量，仓库 `core/` 一个字节都不要改）。

02:49 判活补记（**两个都还活着，禁止重复派发**）：
- `r20n`：`DELIVER/FIX_T20-4.md` 已 7948 字节（step-1 规则生效），此刻在写 `tools/dump_regions.py`（区域普查），
  尚无 `DELIVER/*.py` 交付文件。
- `r20q`：`FIX_T20-5_DIAG.md` 已建（1522 字节），02:48 正在产出 `out/ast_dict.json` 与 `out/py_ast_unparsed.py`
  ⇒ 它正在做本票第一个交付物"哪一级丢的指令"的阶段归因。
- 编排侧此刻 turn 预算耗尽，未安装任何东西：`git status --porcelain -- core/` 空，
  三哈希仍为 `dff6e81a5f2ff9f6 / beeaf14435e22922 / 640d33a77dcb71c2`，远端 `f877c6b2`。
  **本会话没有半安装态、没有跑中的门链**，恢复时直接从 §19C 第 1 步开始即可。

## 20D. 两名工程师被强制暂停（截断但有效读数）+ #51 主机搜索空间已排除 8 处（2026-10-10 08:30）

**截断状态**（都不是零进度，文档已入库 `be5a43d0`）：
- `r20n`（#50，analyzer）：Stage 1 **PASS** 并给出 corpus-product `cmp` 逐字节等值证明，
  还纠正了**我自己票面的路径**：`strategy_universe/api_base/real_quote/matcher/order_api` 的真实位置是
  `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`、`IQData/api/api_base.pyc`、
  `IQData/plugins/plugin_system_realquote/real_quote.pyc`、`IQEngine/plugins/plugin_system_matcher/matcher.pyc`、
  `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc`——我 brief 里的路径根本不持有这些单元。
  §3–§7 仍是 TODO，没有 `DELIVER/*.py`，所以**不能按"候选"记账**，下一票要重走 §19C。
- `r20q`（#51，诊断）：交付了本票第一个交付物并且**推翻了我的票面表述**——
  那条函数内 import 不是"没发"，而是**发成了退化赋值**：
  丢的 4 条＝ `LOAD_CONST 0 / IMPORT_NAME …function / IMPORT_FROM THREAD_STATUS / POP_TOP`，
  留下的是 `LOAD_CONST ('THREAD_STATUS',)`（fromlist）与 `STORE_FAST THREAD_STATUS`，
  因此产物第 253 行（在 `while True:` 内）是 `THREAD_STATUS = ('THREAD_STATUS',)`。

**我自己做的两件事（都是实测，不是推断）**：
1. 逐行扫描确认 `IMPORT_NAME` 的决策点在仓库里有 **7 处副本**
   （`_extract_imports_from_block_prefix:564`（只做块前缀，遇跳转即停，故覆盖不到循环体深处的 import）、
   `generate()` 内 3 处（926/1127/1227，只对入口块）、`_collect_ternary_load_names:6788`、
   `_loop_extract_for_iter_pre_stmts:8612`、`_loop_extract_pre_stmts_from_block:8800`），
   而通用块级构造器 `_build_statements_from_instructions:33043` **自带完整 IMPORT 状态机**（:33063 起 22 处提及）。
   顺带发现卫生问题：`_take_assert_prefix_stmts` 在 :561 返回之后还留了一行
   `return self.region_analyzer.get_block_role(block)`（:562，不可达死码）。
2. **消融普查排除 8 个候选主机**（脚本 `D:/Temp/r20main/ablate.py`，在进程内把
   `_build_statements_from_instructions / _loop_extract_pre_stmts_from_instrs /
   _loop_extract_for_iter_pre_stmts / _loop_extract_pre_stmts_from_block /
   _build_effective_stmts / _generate_degraded_statements / _build_store_statement /
   _extract_imports_from_block_prefix` 逐个 `return None`，每次跑 `pycdc.py --region` 输出到 `$TEMP`）：
   ```
   BASELINE len=54089 degenerate=1 realimport=1
   8 个 STUB 全部 len=54089 degenerate=1 realimport=1
   RESTORED len=54089 degenerate=1 realimport=1
   ```
   两个要点：(a) **没有一个 stub 改变产物** ⇒ 这 8 个函数都不是退化行的生产者；
   (b) 基线里 `realimport=1` 与 `degenerate=1` **同时存在** ⇒ 同一条 import 在某处被正确地发了一次，
   另有一处把 fromlist 元组当成值发了赋值——所以这不是"整条语句丢失"，而是**重复/错位发射**。
   下一步的生产者搜索应换到 `core/cfg/ast_generator_v2.py` 的栈机与
   `expr_reconstructor.reconstruct(...)`：那里才有 `ImportFromPending` 标记
   （`:22779/:22793/:22824/:23787/:23804`），且退化行的形态正是"栈里剩一个 tuple 常量、被 STORE 消费"。
   （stub 全惰也说明我的度量口径要换：只数 `THREAD_STATUS` 行不够，应当 `cmp` 产物字节。）

**恢复后的第一张票**（#51 的正确形态）：诊断-only、只许改 `core/cfg/ast_generator_v2.py` 的读路径、
判据＝"块窗口被切在 `IMPORT_FROM`/`STORE_*` 之间时，栈机不得把 fromlist 常量交给 STORE"，
度量口径＝该单元 `delta=-4 → 0` 且文件 41/43→42/43（不翻文件，但翻 1 个单元＝门读数 6586→6587，
与 gate 18 收 klinedata 62→63 同口径）。仓库此刻仍是 §20C 的封版态，三哈希未动。
2. 有交付文件 ⇒ 走 §19C 全文（数哈希 → 丢弃镜像复测 → install → 一条后台门链 → 封表 → 提交推送）。
3. 门链期间**不安装、不改 `core/`、不读仓库 `*OK.py`**（产物正在被删除重写）。
4. 任何一张票落地都要提交并 `git push origin HEAD:refs/heads/rr-v3r01-f557fd`，用 `git ls-remote` 判真。

## 20E. R20-5 落地并过门（gate 20 certified，2026-10-10 08:51）

- 生产者定位：先前那次"8 处候选全惰"的消融是**作废读数**——stub 装在我这个进程里，
  反编译却用 subprocess 跑在新进程，补丁从未生效。改成进程内 `pycdc.decompile_pyc()` 后
  调用计数立刻给出真实生产者：`_loop_handle_header` 在 **region_ast_generator.py:9729** 用
  `_build_statement(_acc)` 收尾前导窗口，窗口实测 `[LOAD_CONST, LOAD_CONST, IMPORT_NAME, IMPORT_FROM, STORE_FAST]`，
  于是 fromlist 常量被当成赋值右边，产出 `THREAD_STATUS = ('`'THREAD_STATUS'`',)`（同时正确 import 在别处仍发了一次 ⇒ 是**退化/错位发射**，不是丢失）。
- 判据（复用既有状态机，不再复制第 9 份）：窗口含 `IMPORT_NAME` 时改走 `_build_statements_from_instructions(_acc)`。
- 测量（判决来自外部判据 compare_pyc，非我自己数指令）：目标单元 `delta=-4 → len orig=528 prod=528 hunks=0 landings=0 judge_diff=False`；
  文件 41/43 → **42/43**。**同一份退化行在孪生站点 :12164 仍存在**（那条 accumulator 是第 2 份副本），本票只改了实测命中的 :9729。
- 门 20 vs 19（一次后台链，四阶段全 rc=0）：`regen ok=402 bad=0`；
  `[units] 6586/6617 → 6587/6617 (99.5466%)`；`[files] 391 → 391`；
  `[gates] 文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=1`；
  quotation 153/153、small34 units_success 1537→1538、selfcheck 153/153 且两个变异各被抓到 1/153、
  pytest `2 failed, 280 passed, 2 xpassed`＝第 19 轮封版的那一对既有红，**零新增红**。
- 封表：`rounds/round20/RESIDUAL_ROUND20.md`（6587/6617、11 files / 30 units、UNREGISTERED=0）。
- 下一票：孪生站点 :12164（同一判据的第二处副本，按"一处决定多处复用"应把它接到同一个 helper），
  以及 #50（analyzer 侧 BoolOp 声明，r20n 截断未交付，需重走 §19C）。

## 20F. 孪生站点已按规矩回退 + 下一票的证据已备好（2026-10-10 08:56）

- **孪生 :12171 判据＝零翻正，已逐字节回退**：同一 import 判据装到第二份副本后，
  11 个残余文件全部维持封版读数（handlers 29/30、wizard 55/58、trade_info_utils 38/41、klinedata 63/64、
  api_base 27/28、real_quote 43/45、strategy 26/27、realtime_event_source 12/13、risk_calculation 42/43、
  quote 86/92、trade_live_broker 118/128；口径＝`pycdc.py --region` 重生成到 $TEMP 后
  `pyc_verify single --source`，判决来自外部 compare_pyc）。
  `core/cfg/region_ast_generator.py` 回封版哈希 `e17603a761eaadef`（落地态），`py_compile` 通过。
  ⇒ :9729 那份副本是这一族唯一的实测生产者；:12171 保留旧判据，**已证明它在这 11 个文件上不参与**，
  若日后要为一致性统一两处，须另找会命中它的单元，不能记作翻正。

- **下一票（R20-6）证据已量好，主机候选已缩到 5 处 append 点**：
  `IQCommon/util/trade_info_utils.pyc :: <module>.query_strategy_id`，`len orig=117 prod=116 delta=-1 hunks=2 landings=0 judge_diff=True`，
  唯一内容差是：`@634 JUMP_FORWARD`（被 try/except 的自然出口吞进共享尾 `@648 LOAD_CONST None; RETURN_VALUE`）
  被产物替换为在 handler 体**内部内联** `LOAD_CONST None; RETURN_VALUE`（产物第 1084-1086 行 `except BaseException:` 体后）。
  ⇒ 该发的是"handler 自然出口 = 落到 try 之后的共享 return"，不是"handler 里再返回一次 None"。
  候选发射点（`stmts.append({'type': 'Return', 'value': None})` 全文 5 处）：
  :32159 / :32448 / :32964 / :56716 / :56807，其中 :32159 落在 `_generate_handler_body_statements`（:31911）内＝首要嫌疑；
  可复用的既有判据名：`_is_return_none_join_block`（:3096）、`_w14_join_bare_return_none`（:59118）、
  `_strip_implicit_return_none`（:21552）、`_is_trailing_return_none_statement`（:58995）。
  **测量口径提醒（本会话踩过的坑）**：桩必须装在**同一进程**里跑 `pycdc.decompile_pyc()`，
  用 subprocess 驱动会让所有 stub 全惰＝假否证；先装计数包装打印每个候选的调用次数，确认它真的执行，再打桩。
  收益账：这一族若成立可覆盖 trade_info_utils 的 `query_strategy_id`(+1 单元) 与同形的 `query_trade_strategy_info`，
  门槛按"≥1 单元翻正、其余不降、quotation 153/153、六电池不倒"收票。

## 20G. R20-6 五个候选发射点被"已证明惰性的行迹"排除（2026-10-10 09:01）

- 口径：`sys.settrace` 只观察 `region_ast_generator.py` 的行事件，**同进程**调用 `pycdc.decompile_pyc()`；
  先证明探针惰性——带迹产物与不带迹产物 `len` 与全文一致（57911 字节，TRACER INERT True）。
- 读数：`line hits: {}` ⇒ :32159/:32448/:32964（都在 `_generate_handler_body_statements:31918` 内）、
  :56716（`_cjb_append_continue:55384`）、:56807（`_apply_r23n6_return_promotion:56749`）
  **在 trade_info_utils 整个文件上都不执行** ⇒ `query_strategy_id` 内联的那个 `return None` 不是这 5 处 append 造的。
- 由此改判：原函数里本就有**两个** `return None` 块（`@644/@646` 与共享尾 `@648`），产物把其中一个搬进 handler、
  另一个消失——与 #46 `handlers._target` 登记过的 **CPython 逐出口边复制**同族，不是发射点的重复 append 判据。
  下一票若要动它，应查 region 划分（谁拥有 `@644` 那块与 `@648` 那块）而不是再写第 6 个 append 守卫。
- 本轮 tree 状态不变：`core/cfg/region_ast_generator.py` = 封版 `e17603a761eaadef`，门读数 6587/6617、391/402。

## 20H. R20-7 主机已由"容器监视"定位（quote.build_current_period_df 尾被吞）

- 读数（`unit_diff`）：`len orig=123 prod=113 delta=-10 hunks=1 landings=0`，
  删 12 条＝`LOAD_FAST tempdict; LOAD_CONST 'is_open'; STORE_SUBSCR;` 之后整串
  `LOAD_GLOBAL NULL+pandas; LOAD_ATTR DataFrame; LOAD_FAST tempdict; LOAD_FAST index; KW_NAMES; PRECALL; CALL; STORE_FAST tmp; LOAD_FAST tmp`，
  产物只留 `POP_TOP; LOAD_CONST None`。
- 定位法（可复用，2 条记录就够）：把 `RegionASTGenerator.generated_blocks` 换成记录型 set 子类
  （重写 `add`/`discard`，按 `start_offset in {514,516,524,546,566}` 且 `codename(self)=='build_current_period_df'` 命中），
  同进程调用 `pycdc.decompile_pyc(pyc)`，实测命中：
  `:46121 in _generate_ternary`（经 `:21340 _if_generate_normal → :17993 _if_generate_then_branch`）、
  `:14529 _generate_if → :21340 → :18008 _if_generate_then_branch`。
- 根因读数：`_generate_ternary` 在 :46118-46121 把 **region.blocks 全体**标记为已生成
  （`for block in region.blocks: … self.generated_blocks.add(block)`），
  而被三元消费只用到块的前段，块内 **剩余指令**（上面那 12 条）此后再无人发射 ⇒ 静默丢弃。
  同函数上方已有先例可参照：`_gt_exclude_merge` 分支在标记时 `continue` 跳过 merge 块（:46110-46119）。
- 该票的正确判据形态：三元消费跨度未覆盖整块时，不得把该块整体宣告为已消费（要么留块给后续发射，
  要么把余下指令作为语句一并产出）；这是"识别期宣告 + 每块唯一归属"的违反面，不是第 6 个 append 守卫。
- 收益账：`quote.pyc` 86/92；本机制同时是 `run_individual_transform`（del 84）与
  `realtime_event_source.clock_worker`（110 条体被跳）的同形描述，但**必须逐一实测**，不得按同族记账。

## 20I. 派出 r20r（R20-7 施工）并 park（2026-10-10 09:05）

- 工程师 `r20r`：镜像 `D:/Temp/r20r/wt`，**只拥有 `core/cfg/region_ast_generator.py`**，
  交付 `DELIVER/region_ast_generator.py`（整文件）+ `DELIVER/FIX_T20-7.md`（要求 step 1 建立、增量追加）。
  票面＝任务 #52：`_generate_ternary:46118-46121` 把整块宣告消费、块内余下 12 条指令无人发射；
  要求它按 `_gt_exclude_merge`（:46110-46119）已有先例的形态做"跨度未覆盖整块 ⇒ 不宣告该块"，
  并禁止为其它同形受害者（`run_individual_transform`/`clock_worker`/`filter_desicion`）搭车。
  门槛：`quote.pyc` 86/92 → ≥87/92（至少 1 个具名单元翻正），其余 10 个面板文件不降，
  quotation 153/153 / matcher 17/17 / order_api 37/37，六电池按封版读数不倒。
- **它测量期间我不动仓库字节、不跑门链**（它从仓库读 `.pyc` 输入与逐字节对照用的在位 `*OK.py`）。
- 恢复后的动作：数 `DELIVER/` 交付文件与哈希 → 丢弃镜像里复测（§19C 第 2 步，文件换成 generator，
  备份锚点 `e17603a761eaadef`）→ 有翻正才装、装完跑一次 `gate_chain.py 21 20` → `residual_report.py 21 20` 封表 → 提交推送。
- 本轮已落地并封版的读数不变：**6587/6617 单元 / 391/402 文件**，残差 11 文件 30 单元；
  远端在最后一次次提交为 `fef79e80`（本条提交后即更新），`core/` 工作树干净。

## 20J. 同形受害者已用容器监视否证"一票多吃"（2026-10-10 09:16）

- 先记一条我自己的 rigs 事故：第一次普查把 `mk('x')` 的键写死成字面量，过滤器永远取不到集合 ⇒
  `claim-adds=0` 是 **VOID 读数**，不是"该站点不参与"。修好后同一次跑得到 290 / 1272 条命中。
- 修好后的读数（口径：记录型 `generated_blocks` 子类 + 同进程 `pycdc.decompile_pyc`，只观察不改字节）：
  - `fly/data/quote.pyc :: run_individual_transform`：claim-adds=290，主要路径
    `_generate_region@4076→_generate_try@31595`(37)、`_loop_dispatch_block@9250→_loop_handle_child_region_entry`、
    `_if_generate_branch_stmts@27752→_process_if_blocks@26059`(35)、`_generate_try_body@28260`(30)；
    **`_generate_ternary@46121` 不参与**（any 46121 = False）。
  - `realtime_event_source.pyc :: clock_worker`：claim-adds=1272，主要路径同上但 try/loop 占大头
    （`_generate_region@4076→_generate_try@31595` 217、`_generate_try@30318→_generate_try_body@28578` 183、
    `_generate_region@4060→_generate_loop@5378` 158），**`46121` 亦不参与**。
- 结论：r20r 的三元过消费判据**覆盖不到这两个受害者**，"一票多吃"被实测否证；
  它们各自的主嫌疑路径是 try/loop 侧的块消费（`_generate_try*` 与 `_loop_handle_child_region_entry`），
  应各开一票并各自以"至少 1 个具名单元翻正"收票。此结论也回证了票面里"同族必须逐单元实测"的规矩。
- 仓库仍未动：`core/` 干净、`region_ast_generator.py = e17603a761eaadef`，门读数 6587/6617、391/402。

## 20K. 第 21 轮门已封版落地 + 派出 r20s 并 park（2026-10-10 09:44）

- **门 21 vs 20 已封版（一次后台链，四阶段全 rc=0）**：`regen ok=402 bad=0`；
  `[units] 6587 → 6588/6617 (99.5617%)`；`[files] 391 → 391`；
  `[gates] 文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=1`；quotation 153/153、六电池不倒。
  落地件＝r20r 的 `_generate_ternary:45841`（18 行纯新增）：当三元自己的 `merge_block` 在容器值之后仍有
  `STORE_SUBSCR/STORE_ATTR/DELETE_SUBSCR`，说明消费跨度未覆盖整块 ⇒ 走 `_try_build_ternary_store_assign`
  重放 `before_store`（让 `@514 BUILD_LIST` 把 IfExp 折回列表）补回 `tempdict['is_open'] = [...]`，
  并发射 store 之后的余下语句（`tmp = pandas.DataFrame(tempdict, index=index)` / `return tmp`）。
  我自己复测过的读数：`fly/data/quote.pyc` 86→**87/92**，`build_current_period_df` `delta -10 → 0 hunks=0 landings=0 judge_diff=False`。
- **本票最重要的否证（r20r 实测）**：我在票面上建议的"不宣告该块被消费"单独**不成立**——
  `@514`（以及 `@508/@512`）在 `:46121` 与调用方 `_if_generate_then_branch:18008` **两处同时**被宣告消费，
  只放行一处会被另一处Undo；若不宣告，父 `_generate_block_statements` 又无法重建只存在于栈上的容器值。
  ⇒ 这一族的正确机制是"发射余下部分"，不是"取消标记"。
- 提交与推送：`d235c0f8`（含 `rounds/round21/after` 八份 JSON、`RESIDUAL_ROUND21.md`＝11 文件 **29** 单元、
  r20r 的 `FIX_T20-7_r20r.md`、落地后的 generator 字节与扫新的 402 产物），`git ls-remote` 判真。
- **在飞**：工程师 `r20s`（镜像 `D:/Temp/r20s`，只拥有 `core/cfg/region_ast_generator.py`）＝任务 #53：
  `quote.pyc <module>.Quote.run_individual_transform`（del 84，`socket.recv()`→`message`→空数据告警分支→`list(...)[0]` 被压成 2 条）。
  我给它的普查主路径是 try/loop 侧（`_generate_region@4076→_generate_try@31595` 等），并明确
  `_generate_ternary@46121` 不参与本单元；门槛 `quote 87→88/92` 且十个面板文件与三哨兵不降、六电池不倒。
  **它测量期间我不动 `core/` 字节、不跑门链。**
- 恢复后的动作（照抄）：数 `D:/Temp/r20s/DELIVER/` 交付文件与哈希 → 丢弃镜像复测（§19C 第 2 步，
  备份锚点＝**重新读当前** `core/cfg/region_ast_generator.py` 哈希，今天已是 `4f295dfc6ebd2caa`）→
  有翻正才 `install_deliver.py install` → `gate_chain.py 22 21` → `residual_report.py 22 21` → 提交推送。
- 未开的同形票（各自需要独立翻正证据，禁止搭车）：`clock_worker`（12/13）、`filter_desicion`（仅落点差）、
  `handlers._target`（逐出口边复制族，已否证发射点说）、#50 analyzer 侧 BoolOp 声明。

## 20L. 第 21 轮封版时的廉价阶段读数（下一票落地前的基线，勿凭记忆）

口径＝`gate_chain.py 21 20` 的 checks 阶段日志 `/d/Temp/gate_chain_21_093202.log`（落地字节上实测）：

- `[quotation] rc=0 units=153/153 success_rate=100.00%`（尺子自证目标文件）
- `[small34] rc=0 units_success=1539, success=23`（上一轮 1538/22 ⇒ 本次小批 +1 单元、+1 全绿文件）
- `[selfcheck] rc=0 自证 153/153 Equal｜变异「常量」抓到 1/153｜变异「极性」抓到 1/153｜OK —— 判据可用`
- `[pytest] rc=1 2 failed, 280 passed, 2 xpassed in 3.33s`
  ⇒ **这两条红就是第 19/20 轮封过的那一对**（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`），
  `checks` 阶段的判据是"零新增红"，先前存在的红不构成对本票落地的反证。
- 门 21 主读数：`6588/6617 (99.5617%)`、`391/402` 文件、`regen ok=402 bad=0`、
  `文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=1`；`rounds/round21/RESIDUAL_ROUND21.md`＝11 文件 29 单元，UNREGISTERED=0。
- 下一票的门标签＝**22 vs `rounds/round21/after`**；安装前先重读
  `sha256sum core/cfg/region_ast_generator.py | cut -c1-16`（当前 `4f295dfc6ebd2caa`），别用本文里任何旧哈希。

## 20M. r20s 被截断（无判据、无交付），但它的取证纠正了我两个数（2026-10-10 10:11）

- 判活方式照例是"进程 + 文件"两路：`ps -W | grep -ic python` = **0**，且 `D:/Temp/r20s` 内 12 分钟无任何新文件
  ⇒ 该工程师已被终止，`DELIVER/` 里只有 37 行 FIX 文档，**没有 `region_ast_generator.py` 交付件**，
  镜像 `wt/core/cfg/region_ast_generator.py` 仍是基线 `4f295dfc6ebd2caa`（未打过补丁）。
  所以本票**没有可安装的候选**，不是"候选被判否"——下一位工程师可直接接着它的取证做。
- 它纠正了我票面两个数（它按"信文件不信引用"处理，正确）：
  `quote.pyc <module>.Quote.run_individual_transform` 在**封版字节**上的实测是
  `len orig=407 prod=355 delta=-52 hunks=10 landings=3 judge_diff=True`，
  而非我引用的 `del 84` 单 hunk；三个同形 hunk 是 `del=15 / del=5+3 / del=21(+ins 9)`
  （`socket.recv()`→`message`→`if not message` 告警→`list(keys)[0]`）。全文转储在它镜像的 `out/victim_unidadiff_base.txt`。
- 附带收益（对我独立有意义）：它在**新建镜像**里逐项复现了 13 项面板与三哨兵
  `quote 87/92 · klinedata 63/64 · handlers 29/30 · wizard 55/58 · trade_info_utils 38/41 · api_base 27/28 ·
  real_quote 43/45 · strategy 26/27 · realtime_event_source 12/13 · risk/__init__ 42/43 · trade_live_broker 118/128 ·
  quotation 153/153 · matcher 17/17 · order_api 37/37`
  ⇒ 这是门 21 落地态在异进程/异镜像下的第二次独立复现（不是我自己的读数）。
- 它的 census 中间件留在 `D:/Temp/r20s/probe_census1.py` 与 `out/census1.json`（含 `pristine/` 对照），
  下一票可复用；本票标签仍为 R20-8/#53，门槛不变（`quote 87→88/92`，其余不降）。

## 20N. R20-8 续派 r20t（复用 r20s 的镜像与取证）——本会话最后一次封版（2026-10-10 10:12）

- 工程师 `r20t` 在 `D:/Temp/r20s`（**复用**已验证为封版字节 `4f295dfc6ebd2caa` 的镜像、
  `pristine/` 对照、`run_panel.sh` 面板、`out/victim_unidadiff_base.txt` 与 `out/census1.json` 普查）继续 #53，
  只拥有 `core/cfg/region_ast_generator.py`；交付要求＝整文件 + `DELIVER/FIX_T20-8b.md`（step 1 建档、增量追加）。
  门槛不变：`fly/data/quote.pyc` 87/92 → ≥88/92（`run_individual_transform` 转 Equal），
  其余十个面板文件与三哨兵不降、六电池按封版读数不倒；`delta -52 → -20` 而无翻正＝FALSIFIED-but-supporting。
- 我在票面上强制了今天用一票换来的设计课：动手前先用记录型 `generated_blocks` 证明**本单元每个受害块被几处宣告消费**，
  再在"取消标记"与"发射余下部分"之间选（gate 21 那票就是因为 `@514` 同时被 `:46121` 与调用方 `:18008` 宣告，
  取消标记会被彼此 Undo，而不宣告又让父级无法重建只在栈上的容器值）。
- **它测量期间我不再动 `core/` 字节、不跑门链。** 本会话结束时的仓库状态：
  门 21 已封版（`6588/6617` 单元、`391/402` 文件、残差 11 文件 **29** 单元），
  `git status --porcelain -- core/` 空，`region_ast_generator.py = 4f295dfc6ebd2caa`，远端与本地同为本次最后提交。
- 下一会话的第一个动作：读 `D:/Temp/r20s/DELIVER/`（`FIX_T20-8b.md` / `region_ast_generator.py`）判 R20-8；
  若已 LANDED-READY，走 §19C（数文件与哈希 → 丢弃镜像复测 → `install_deliver.py install`，
  锚点须**重新读**当前 generator 哈希 → `gate_chain.py 22 21` → `residual_report.py 22 21` → 提交推送）。

## 20O. R20-8 在飞臂次轨迹（2026-10-10 10:28–10:33 我逐臂实测镜像产物所得）

- 口径：我直接读 `D:/Temp/r20s/out/victim_unidadiff_v*.txt` 的表头（工程师每打一臂就重跑一次
  `unit_diff.py`），并配合镜像 generator 的 sha16 变化确认"这一臂真的装了不同字节"：
  封版 `4f295dfc6ebd2caa` → v1 `c6bb17006f962f6e` → v3/v4 `9738cebbf9786ca2`。

| 臂 | victim `run_individual_transform` |
|---|---|
| base | `len orig=407 prod=355 delta=-52 hunks=10 landings=3 judge_diff=True` |
| v1 | `delta=-27 hunks=8 landings=3 judge_diff=True` |
| **v2** | `delta=-2 hunks=5 landings=3 judge_diff=True` |
| v3 | `delta=-127 hunks=6 landings=3 judge_diff=True`（**过头：比基线更差 ⇒ 是一次回退臂**） |

- 读法：v2 只剩 **2 条指令 + 5 个 hunk + 3 个落点差**，说明这一族"块被 try/loop 侧过度宣告"的方向是对的，
  但按现判据还差一步；v3 反而 −127 ⇒ 同一判据放宽一处会连带吞别处，**不可按"最接近的那臂"记账**。
- 规矩照旧：我只读它的臂次文件，**没有安装、没有跑门链**（它的 `DELIVER/` 至今没有 `region_ast_generator.py`，
  文档里判据实现/阶段读数/最终声明三段仍是 `(pending)`）。移动中的哈希不是判据。
- 下一会话续做 #53 的第一动作：读 `D:/Temp/r20s/DELIVER/FIX_T20-8b.md` 的 `## Final declaration`；
  若仍为 pending ⇒ 该工程师已死，从 v2 那臂的字节继续（v2 的镜像哈希 `c6bb17006f962f6e` 之后的一步），
  目标是把 `delta=-2 landings=3` 收掉；若 LANDED-READY ⇒ 走 §19C，门标签 **22 vs `rounds/round21/after`**。
- 会话末状态：门 21 封版不变（6588/6617、391/402、残差 11 文件 29 单元），
  仓库 `core/` 干净、`region_ast_generator.py = 4f295dfc6ebd2caa`。
