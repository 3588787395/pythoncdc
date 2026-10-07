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

- [ ] Task 10: Round 9 — 402 全量终局复验（目标 units 6617/6617、files 402/402）
  - [ ] 10.1 八分片 regen + batch + compare（before = Task 1 基线），双门禁 REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0
  - [ ] 10.2 逐文件 `+OK.py` 存在性与 `single` status 抽验（≥30 文件覆盖各区域族）
  - [ ] 10.3 残余非 success 文件（若有）逐 pyc 登记 → 同轮封闭 → 重跑
  - [ ] 10.4 验证序六步 + push

- [ ] Task 11: Round 10 — 注释合规终审与台账定稿
  - [ ] 11.1 `_identify_*` 十族 + 对应生成方法 docstring 六项模板逐方法一致性审计（不一致即修：以代码真实算法为准修注释，或以注释声明的正确算法为准修代码，禁含糊）
  - [ ] 11.2 `tools/kb/syntax_coverage.py` 重跑 + wiki 台账数字同步（禁手改矛盾数字）
  - [ ] 11.3 终验（全量 + quotation + tests 六套件 + 普查反向夹钳）+ 汇报终态读数（单元级/文件级/破口状态/注释合规面）+ push

注：10 轮用尽仍未达 100% 时，如实上报残余清单（文件 × 单元 × 违反条款），不得为凑读数改判据或手改产物。

# Task Dependencies

- Task 0 → Task 1 → Task 2 … Task 11 严格顺序（前一轮门禁未过禁止开启下一轮）
- 每轮内：测试工程师 → 修复工程师 → 主代理验证 → 提交 push 串行；多位修复工程师仅在破口族 ∧ 涉改文件不相交时可并行
- Task 10 的终局复验依赖 Task 2–9 全部封闭标记落盘（grep 落地标记为凭）
- 每次派发子代理前必须先有本地提交（用户硬约束）
