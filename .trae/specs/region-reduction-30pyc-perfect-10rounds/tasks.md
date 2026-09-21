# Tasks

目标：site-packages 下 pyc 逐个反编译，字节码 100% 一致，同目录生成 `<name>OK.py`。
每轮 = 测试工程师（取单个 pyc → 建 10+ 最小复现） + 修复工程师（按区域归约算法改程序） → 验证 → 批量回归 → 提交 push。

- [x] Task 1: Round 1 — 修复 trade_info_utils.pyc (75% → 100%)
  - [x] SubTask 1.1: 测试工程师产出 11 个最小复现（test_repros/round2/）
  - [x] SubTask 1.2: 修复工程师修 try/except 边界 + 控制流
  - [x] SubTask 1.3: trade_info_utils.pyc 达 100%，生成 OK.py
  - [x] SubTask 1.4: 批量回归 373 ok / 29 partial / 0 failed
  - [x] SubTask 1.5: 提交并 push

- [x] Task 2: Round 2 — trade_info_utils.pyc 剩余不匹配函数深挖 + trade_operation
  - [x] SubTask 2.1: 测试工程师分类 2 类根因（A：跳转等价；B：6 个真实结构缺陷）
  - [x] SubTask 2.2: P0-1 orelse None→[] 逐语句降级（5 函数得解）
  - [x] SubTask 2.3: R2-SWAP / R2-With / P1-1a boolop 链纯净性
  - [x] SubTask 2.4: 文档 test_repros/round2/ANALYSIS.md
  - [x] SubTask 2.5: 提交并 push

- [x] Task 3: Round 3 — fly/data/quote.pyc（77.78%）根因分析与区域修复
  - [x] SubTask 3.1: 测试工程师：18 个不匹配函数 → 13 个复现 + 3 个负对照，
        9 类根因 R3-A…R3-M（test_repros/round3/ANALYSIS.md）
  - [x] SubTask 3.2: 修复工程师：R3-D（循环内 if/elif 分支 continue 丢失，语义级）
        + R3-K（boolop/ternary 迭代上下文守卫）+ R3-L/R3-M（POP_TOP 语句段切分、
        while 条件 NONE_CHECK 极性）+ 比较器对称性守卫收紧
  - [x] SubTask 3.3: 验证：r3_04 / r3_09 复现由 MISMATCH → MATCH；
        quote.pyc 0.7778 → 0.8025（65/81）
  - [x] SubTask 3.4: slippage.pyc 0.9286 → **1.0000（完全 OK，生成 slippageOK.py）** —— 本轮至少解决 1 个 pyc
  - [x] SubTask 3.5: 批量回归 **374 ok / 28 partial / 0 failed，累计 98.01%**
  - [x] SubTask 3.6: 提交并 push（commit 6bfc3990，origin/main）

- [x] Task 4: Round 4a — R3-E 共享函数尾 return 被误挂为内层 else
  - [x] SubTask 4.1: 测试工程师：r3_05 复现 + CFG 块表定位
  - [x] SubTask 4.2: 修复工程师：`_generate_boolop` 的 R89 内联 if 提取路径加
        「汇合块不得作 else」结构判据（`_r4e_else_target_is_join`，
        region_ast_generator.py ~30200 / ~31180）+ 入度 ≥2 必要条件收紧
  - [x] SubTask 4.3: 验证 r3_05 → MATCH（orig=211/decomp=211, true_diffs=0）；
        quote.pyc 65→66/81；quotation.pyc 141→142/143
  - [x] SubTask 4.4: 批量回归无退化（仅 3 个文件改善，0 退化）

- [ ] Task 5: Round 4 — 区域归约算法两处结构性缺陷（R4-G / R4-H）
  - [x] SubTask 5.1: 测试工程师：发现并最小化两类新根因
        · R4-G 短路归并块跨越语句边界 → 归并点之后语句被整段吞掉
          （13 形态探针；真实受害 `fly/oauthenticator/oauth2.pyc` 的
           `OAuthCallbackHandler.post` 由 `pass` 恢复出 179 条指令）
        · R4-H 嵌套 for 之后的外层 `continue` 被丢弃
          （5 形态探针；真实受害 `strategy_info_utils.check_python_code`）
  - [x] SubTask 5.2: 修复工程师（R4-G，本人实施）：`cfg_builder.py` 新增
        `_split_blocks_at_short_circuit_merges()` 归并点切分前置归一化 +
        「语句边界必要性守卫」+「异常保护区间守卫」
  - [x] SubTask 5.3: 修复工程师（R4-H，子代理实施）：`region_ast_generator.py`
        `_process_if_blocks` 增加「for_iter_exit 但回边指向外层循环头且
        merge_block 非循环头 ⇒ 显式 continue」判据 + R100 抑制优先级调整
  - [x] SubTask 5.4: 验证 —— **`IQCommon/util/strategy_info_utils.pyc` 28/28 = 100.00%**
        （本轮至少解决 1 个 pyc 达标）；`fly/dockerspawner/dockerspawner.pyc`
        0.96 → **1.0000**；round4 全部 6 个复现 MATCH
  - [x] SubTask 5.5: 全量复验 402 pyc（发现 batch 只跑 pending，ok 计数陈旧：
        committed 标称 373 ok，真实 332 ok；已建立全量复验方法）
  - [x] SubTask 5.6: 无回归确认（arg_checker 97.87% 恢复至基线；round3 复现全绿）
  - [ ] SubTask 5.7: 提交并 push


- [x] Task 5: Round 5 — R3-F 三元表达式在「表达式位置」降级
  （`[1 if c else 0]` 下标赋值、链式比较三元 `x = A if C else B` → 伪 return）
  - [x] SubTask 5.1: 测试工程师建复现（已发现：`int(x) if 0 < int(x) <= 200 else 200` 生成伪 return）
  - [x] SubTask 5.2: 修复工程师按区域归约修语句跨度/伪三元合并
  - [x] SubTask 5.3: 验证 build_current_period_df / get_individual_data 转 OK
  - [x] SubTask 5.4: 批量回归 + 提交 push

- [x] Task 6: Round 6 — R3-A f-string 调用参数区域模板重建
        （get_price / load_get_price / load_bars_from_hundsun）
- [x] Task 7: Round 7 — R3-L 旋转 while 循环体语句丢失
        （check_limit / get_real_from_zeromq / initImagedata）
- [x] Task 8: Round 8 — R3-I try/except 区域块归属错乱（灾难级）
        （run_individual_transform / run_tick_socket）
- [x] Task 9: Round 9 — fly/oauthenticator/oauth2.pyc 生成器函数体整体丢失
        （OAuthCallbackHandler.post，214 条指令 → 仅 `pass`）
- [x] Task 10: Round 10 — 剩余 partial 文件清零，全量 402 pyc 100%

- [x] Task 11: Round 11-12（本会话）— 推导式返回值宽指令 fall-through + 真值重确认
  - [x] SubTask 11.1: 补推 Round 10 欠账提交 675ca714（网络恢复后 PUSH_OK）
  - [x] SubTask 11.2: 严格尺子重确认真值 319/349、4424/4479、30 文件真缺陷，零回归
  - [x] SubTask 11.3: cgroup_utils 定性：add_process_to_cgroup / set_cgroup_config
        为编译器小版本差异（3.11.7 形态探针证实），反编译器正确；
        delete_cgroup_config 为真缺陷（else 体过度吸收），留待下轮
  - [x] SubTask 11.4: 测试工程师定位 merger_storage ×2 同签名根因
        （`_last_off + 2` 对带 CACHE 宽指令失效 → 推导式 return 被降级）
  - [x] SubTask 11.5: 修复 `comprehension_generator.try_generate_comprehension_assign`
        （前向后继平凡 return 判据，含「识别条件→归约方式→AST 映射」注释）
  - [x] SubTask 11.6: 形态探针 6/6 PASS；两个 merger_storage 100% ok
        （官方 349 → 351）；严格尺子全量零回归
  - [x] SubTask 11.7: 提交并 push（8a1b1def，origin/main）

# 环境阻塞（须先解决）

本会话中途 bash 不可用（`unable to load netapi32.dll`），PowerShell 被沙箱拒绝，
导致 SubTask 4.2 之后**无法执行验证 / 提交 / push**。详见
`.workbuddy/memory/2026-09-19.md` 的命令清单与判定标准。

# Task Dependencies
- Task 4 依赖 Task 3（同一文件的区域算法改动须在已验证基线上叠加）
- SubTask N.3（验证）依赖 SubTask N.2（修复）
- SubTask N.5（提交 push）依赖 SubTask N.4（批量回归无退化）

- [ ] Task 12: Round 13 — 严格尺子真值基线 + 18 个「只差 1 函数」partial 文件归因
  - [x] SubTask 12.0: 建立 Round 13 真值基线（已完成，见 rounds/round13/）
        · 官方口径 351 ok / 51 partial（402 pyc）
        · 严格尺子（_r10_strict_check）真值：ok 桶 321/351 全一致（30 文件 55 函数仍不符），
          partial 桶 0/51 全一致（179 函数不符）
        · 全语料真值：**321/402 文件 = 79.85%**，函数 **5970/6204 = 96.23%**
        · partial 桶缺陷类型：seq_len 121 / target_diff 25 / seq_diff 8（结构性为主，非编译器噪声）
  - [x] SubTask 12.1: 测试工程师：18 个「只差 1 函数」partial 文件逐个 dis 对照，
        建 >=12 个最小复现（>=10 MISMATCH + 2~3 MATCH 负对照），
        归类 R13-A…，产出 test_repros/round13/ANALYSIS.md + MAPPING.md
  - [x] SubTask 12.2: 修复工程师：按区域归约算法修 R13-* 真缺陷
        （识别条件→归约方式→AST 映射写入识别方法注释；禁止跨区域跨层次启发式规则）
        R13-A（return 被降级为 break）已落地并验收；R13-C（链尾吸收）/
        R13-D（dict 双推导式折叠）与本轮回退的 A2 前缀判据一并移交 Round 14
        （根因判据见 rounds/round13/OUTCOME.md §四）
  - [x] SubTask 12.3: 验证：重新生成受影响 OK.py（仅经 scripts/pyc_batch_verify.py single，禁手工改），
        严格尺子复验，本轮至少 1 个 pyc 由 partial → 100%
  - [x] SubTask 12.4: quotation.pyc 单文件验证（核心侧 +1 函数劣化，产物门自动回滚，OK.py 仍 148/150 未劣化）
  - [x] SubTask 12.5: 批量回归：全量产物逐函数复验，零回归（产物门 CLEAN=320 FLIPPED-CLEAN=3 IMPROVED=1，11 个劣化自动回滚）
  - [x] SubTask 12.6: 提交并 push（f89b85f2 → origin/main；仅 add 本轮实际改动文件，未用 git add -A）

- [ ] Task 13: Round 14 — 区域归属层解决「前缀语句已发射」判据（A2 回退项的正解）
  - [x] SubTask 13.1: 在**归属层**记录「块语句序列由哪个区域发射」：
        为 BoolOp/三元链的 first_chain_block 判定「其前缀语句是否已随该块发射」
        提供唯一权威来源。禁止再生成期标记集合上弥补
        （实测：块级 generated_blocks 被表达式消费路径污染；
        generated_offsets 只零散登记 start_offset；新增台账也覆盖不到 create_order
        的第一份发射路径 —— 三种判据全部失败，见 OUTCOME.md §四）
  - [x] SubTask 13.2: 恢复 A2 想解决的问题且不复发重复发射：
        repro_01 第二臂 `a2 = 2` 前缀不得被吞；
        order/trade/base_validator/itn/json_persistance/quotation 六处
        整块语句重复必须保持 0（验收命令见 OUTCOME.md §六）
  - [ ] SubTask 13.3: 清核心侧劣化清单（产物已被回滚保护，核心仍需修）：
        region_analyzer A3/R13c 簇 → klinedata / common_func / real_quote /
        plugin_fly_data__init__ / history_api / flytools / market_time /
        quote_handler / json_persistance；
        region_ast_generator 未提交簇 → base_validator._check_order /
        quotation.change_future_real_date；
        已丢失的上一会话改进（无快照）→ trade_live_broker +16 / quote +9
        （Round 14 实测已完成归因：三个 core 文件同时退回提交态后，这 11 个文件的
        严格尺子数字与缺陷集与本轮 hunks **完全相同** ⇒ 纯为 Round 13 提交遗留的
        「产物优于核心」债，证据见 rounds/round14/OUTCOME.md §四）
  - [ ] SubTask 13.4: R13-C 链尾吸收（约 46 个函数字节差，收益面最大）：
        region_analyzer 链 merge 计算为 None 时的合流点归约
  - [x] SubTask 13.5: R13-D dict 两个推导式折叠（broker 29/29、live 29/29，函数级 58/58，翻正 2 个 pyc）
  - [ ] SubTask 13.6: 全量产物逐函数复验，产物零回退
  - [ ] SubTask 13.7: 提交并 push

# Round 13 记录补充
- 翻正清单、回退证据与工序：`rounds/round13/OUTCOME.md`
- 被回退的 A2 原始 hunk 存档：`rounds/round13/r13_a2_reverted_hunk.diff`
- 教训（记录，避免再犯）：`baseline_strict_ok351.txt` 文件名中的 351 是
  **官方**口径数，文件内 `OK` 行实为 321 条（严格口径）；两把尺子的数字
  不得互相减法比较。

- [x] Task 14: Round 14 — 值上下文表达式 merge 块的「双角色」归属（A-1）+ R14-D dict 推导式
  - [x] SubTask 14.1: 测试工程师定位 `region_analyzer.py:15910` 无条件 `continue` 吞掉后继
          语句的 if；证据与判据见 `test_repros/round14_join/ANALYSIS.md`
          （16 复现：11 MISMATCH + 5 负对照 MATCH，全部实测）
  - [x] SubTask 14.2: 修复工程师新增语言级判据 `_value_merge_hosts_next_if`（注释含
          「识别条件→归约方式→AST 映射」），作为原则 2 的例外 3 接入 `_is_merge_next_stmt_if`，
          与例外 1/2 共用 `guard_clause_prefix_end` 切分；三元路径判据统一委托，不再各维护一份
  - [x] SubTask 14.3: 发射侧补齐归属层信息：抽出 `_boolop_merge_owner_for`（生成期丢弃路径
          与 `_if_generate_normal` 双角色路径共用）+ `prefix_stmts_pending` 一次性延迟记录
  - [x] SubTask 14.4: 窄化 `_conditional_value_producing_arms`：两条后继各自以「对同一目标的
          STORE_*」结案 ⇒ 该测试属赋值表达式（三元），例外 3 拒绝；消除唯一劣化 `parse_db_url`
  - [x] SubTask 14.5: 文件级 A/B 归因（14 文件集）：all_HEAD 530/589 → 本轮 534/589，
          优势 4 个函数、劣势 0；11 处劣化证明为 Round 13 遗留债（SubTask 13.3）
  - [x] SubTask 14.6: quotation.pyc 单验 148/150 → 147/150，产物门自动回滚（all_HEAD 同为 147）
  - [x] SubTask 14.7: 全量产物门：CLEAN=327 UNCHANGED=67 WORSENED(回滚)=9
          REGRESSION(回滚)=2 NO-OKPY=1；翻正到 100% 的 pyc = IQCommon/profiler_func 16/16、
          IQData/utils/profiler_func 14/14（满足「每轮至少解决一个 pyc」）
  - [ ] SubTask 14.8: 本轮未完项移交：SubTask 13.1/13.2（`round14_join` 11 个 MISMATCH：
          前缀重复 +13 与 then 区截断同族）、SubTask 13.4（R13-C 链尾吸收，含 A-2
          `PluginManager.set_engine` ×2）、Task 5 遗留（`decrypt_database_url` +29、cgroup +2/+1）
- [x] Task 15: Round 15 — 前置语句发射权登记（A2 正解）+ else 臂「双角色块」收养（H1+H2）
  - [x] SubTask 15.1: 测试工程师定位 15-A 根因：`BoolOpRegion ↔ IfRegion` 双向认领下
          「前缀语句是否已随块发射」无权威来源 ⇒ 新增指令粒度台账
          `prefix_emitted_upto`（`region_ast_generator.py:240`）+ 唯一登记点
          `_register_prefix_emitted`（`:46165`），量纲 = 本次实际消费前缀的末指令偏移
  - [x] SubTask 15.2: 重入保护与交接：`_generate_boolop` 包装层压栈 `_generating_regions`（`:30987`）、
          `_boolop_merge_owner_for(include_generating=…)`（`:16337`/`:16418`/`:11090`）、
          祖先发射情形同样登记 owner 为已生成（A2d），条件提取出口按指令粒度登记（`:13835`）
  - [x] SubTask 15.3: 切片只放链首消费者（`:31328-31342`）+「提取后丢弃 ⇒ 撤销认领」快照回滚
          （`:31001-31014`，A2f）。不做的代价实测：`IQCommon/profiler_func` 模块级
          `PY3 = sys.version_info[0] == 3` 整体丢失 16/16 → 15/16
  - [x] SubTask 15.4: 15-A 验收：`round14_join` 16 复现 MISMATCH=11 → **1**（10 项改标 SENTINEL），
          14 文件严格 A/B 534/589 且缺陷集合与 A1b 逐函数相同 ⇒ 零回归
  - [x] SubTask 15.5: 15-B 设计稿 → 落地前 dry-run（`rounds/round15/elsearm-design.md`）：
          H1 单独不足（`_generate_if:11090` 仍 `return []`，r15a_01 seq_len 61→25）⇒
          定稿 H2「owner 识别与发射权解耦」（`include_generated` 形参 + `:11090` carve-out +
          `_if_generate_normal` 的 `_bo_sib` 兜底）
  - [x] SubTask 15.6: H1+H2 以 6-hunk 断言式字节补丁落地（副本播种 dry-run，仓库零写入）：
          `f8debe9af6b60b20 → d07996aaa20d4665`（BOM/CRLF 不变，48070 → 48122 行）
  - [x] SubTask 15.7: 门禁顺序全绿：单点修到完全 OK（IQData/utils/arg_checker 39/39、
          IQEngine/utils/arg_checker 43/43，逐函数比对与 `single` 同时 100%）→ quotation.pyc 单验（147/150，
          缺陷集合逐函数与基线相同）→ 全量产物门：CLEAN=327→**329**、
          UNCHANGED=67→**65**、WORSENED=9 / REGRESSION=2 与 Round 14 文件集合逐个相同 ⇒ 零新增回退
  - [x] SubTask 15.8: `scripts/pyc_batch_verify.py single` 对两个 arg_checker 报
          `decompile_status: ok` / `match_rate 100.00%`；`pyc_index.json` 按 index-corrected 惯例
          纠正 `IQCommon/arg_checker`（本轮产物实测 100%，HEAD 产物同为 100%
          ⇒ Round 10 的未验证 stale 标记，非本轮造成）
  - [ ] SubTask 15.9: 本轮未完项移交 Round 16：①analyzer 层 then 臂内 Try 的父链归属
          （`IQCommon/arg_checker._is_valid_quarter` 缺口 2→16 条指令、`r15a_01/02`、`r14j_09`）；
          ②R13c sink 塌陷 A/B 已就绪（`D:/Temp/r15_elsearm_diag/cmp3.txt`：257/79 → 250/77，
          FIXED=7 BROKEN=0）⇒ `plugin_manager` ×2 `set_engine`；③`guard_clause_prefix_end`
          只为裸名条件写入（`r15a_08`）；④body-sequence 重复发射（`r15a_09` +9）；
          ⑤SubTask 13.3 / 13.4 / Task 5 遗留照旧
- [x] Task 16: Round 16 — 推翻 Round 15 移交的「分析层未建父子」猜想，改为生成层
      「结构兄弟优先」约束（R16-A：if 臂表达式子区域预生成不得抢占结构兄弟入口块）
  - [x] SubTask 16.1: 否证 Round 15 §四 猜想：`D:/Temp/r16_arm/tool_regions.py` 导出区域树，
          实测 `TryExceptRegion@94.parent == IfRegion@86`、
          `IfRegion@86.children = [Region@92, TryExceptRegion@94, BoolOpRegion@94, TernaryRegion@94]`
          ⇒ 缺口在发射层，analyzer 无需改动（`rounds/round16/arm-design.md`）
  - [x] SubTask 16.2: 定位抢占点：`_if_generate_then_branch` 两处表达式子区域预生成
          （children 循环 `:14052`/标记 `:14070-14071`；回退循环 `:14213`/标记 `:14228-14229`）
          把 `child.blocks` 整批写入 `generated_blocks`，令 `_try_entry_generate`
          （`:20153-20167`，守卫 `:20154-20155`）空转 ⇒ try/except 16 条指令丢失；
          else 臂 `_try_collect_c3` 因先结构后表达式的收集顺序免疫（差分复现 `r16a_09`）
  - [x] SubTask 16.3: 测试工程师交付 16 个最小复现 `test_repros/round16_arm/` + `run_all.py`，
          裸核心实测 MISMATCH=10 / MATCH=6；其报告「EXPECT 已 100% 回填」经复验为 3 项误标
          （`r16a_05/06/12`），已在回填脚本内纠正并留注释
  - [x] SubTask 16.4: 落地前副本播种验证（仓库零写入）：`r16a_patch.py` 4 hunks **+53/−0**
          → `gen_R16.py`（目标 pyc 逐函数 48/49→49/49、`single` 46/47→47/47；全量产物
          FIXED=1 BROKEN=0 CHANGED=0；五套电池 round16_arm 10→1、round15_arm 4→2、
          round14_join/round14/round13 不变；`quotation.pyc` 缺陷集合逐函数相同）
  - [x] SubTask 16.5: mandate 门禁顺序全绿：单点 FLIPPED-CLEAN（arg_checker 48/49→49/49）→
          quotation.pyc 单验（148/150→147/150，缺陷函数逐函数相同 ⇒ SubTask 13.3 产物漂移，非本轮回退）
          → 全量产物回归 `CLEAN=329→330 / UNCHANGED=65→64 / WORSENED=9 / REGRESSION=2`，
          异常文件集合与 R14、R15 逐个相同（11 个）⇒ 零新增回退
  - [x] SubTask 16.6: 落地字节级复核：`d07996aaa20d4665 → 0fc591a8433e7032`（48122→48175 行，
          BOM/CRLF 不变，与已验证副本 sha256 全值相同）；六套电池 `--strict` 退出码 0
          （round16_arm 1 / round15_arm 2 / round14_join 1 / round14 0 / round13 14 / round16_sink 8，
          UNEXPECTED 全 0）；SENTINEL 回填 round16_arm 9 项 + `r15a_01/02`，`r16a_05` 纠正为 MISMATCH
  - [x] SubTask 16.7: `scripts/pyc_batch_verify.py single` 对 `IQCommon/arg_checker` 报
          `decompile_status: ok` / `match_rate 100.00%`；`pyc_index.json` 该条按实测纠正为
          `ok` / `1.0` / round 16
  - [ ] SubTask 16.8: 本轮未完项移交：①`r16a_05` loop 入口重复发射（over-emit +8）；
          ②R16-S sink 族 `plugin_manager` ×2（`_build_elif_region`/`_check_elif_chain` 归并判据，
          与 R16-A 正交：15 复现在裸核心与播种下逐条一致；诊断 agent 耗尽 150 轮，电池完整但无 ANALYSIS.md）；
          ③T1/T2 then 臂收集顺序整体重排（影响面未测）；④`r15a_08` `guard_clause_prefix_end`、
          `r15a_09` body-sequence 重复发射；⑤SubTask 13.3/13.4 与 Task 5 遗留照旧
- [x] Task 17: Round 17 — 移除 `_build_elif_region` D2 守卫的第④判据（循环豁免），
      修「loop 内 else 臂嵌套 if + 尾随语句被展平成 elif 链」（R17-A，翻转 plugin_manager 孪生对 + user_error）
  - [x] SubTask 17.0: 语料不新增条目——`pyc_index.json` 条目与每条 `function_count` 与 `spec.md`
          逐项一致，本轮只按工具实测更新受影响条目的 `matched_functions` / `decompile_status`
  - [x] SubTask 17.1: 承接 SubTask 16.8②：`round16_sink` 15 复现在补丁前实测 MISMATCH=8 / MATCH=7，
          8 个 anchor 全部以 `target_diff`（then 臂 `JUMP_FORWARD` 落点漂移）复现；关键分界对照
          `r16s_08`（循环外，VETO(d2)）与 `r16s_04`（循环内，被④豁免而展平）
          ⇒ 判据④是唯一分界，缺陷签名与真源 `PluginManager.set_engine` 同族
  - [x] SubTask 17.2: 根因判定为**跨层次启发式豁免**：真 elif 链的嵌套汇聚点必等于外层汇聚点，
          已被判据③排除；④按「外层是否在循环内」对同一结构给出两套互斥结论，违反
          「一次正确 / 同层同结构同结论」⇒ 修法为删除④（非新增规则），⑤继续排除终态共享退出
          （`rounds/round17/arm-design.md` §1、`fixes.md` §二）
  - [x] SubTask 17.3: 落地前仓库零写入 A/B（就地方法替换 harness `D:/Temp/r17/h.py`）：
          `round16_sink` 电池 8 MISMATCH→0、5 负对照两臂均 MATCH；全量产物逐函数比对
          修复=7 文件/9 缺陷函数、破坏=0、签名变化仅 `strategy.pyc`（缺陷数 2→2）；
          `quotation.pyc` 缺陷集合两臂逐名相同（中性）
  - [x] SubTask 17.4: 工具链事实纠正：以 `importlib` 模块级替换播种 `core.cfg.region_analyzer`
          会打断类身份（`isinstance` 失效）使产物整体塌缩，**连逐字节相同的 HEAD 副本**都把
          `round16_sink` MISMATCH 从 8 扰动到 13 ⇒ 本轮所有变体测量改用
          `inspect.getsource → 行级改写 → exec(compile(…), dict(RA.__dict__)) → setattr` 就地替换
  - [x] SubTask 17.5: 落地 `D:/Temp/r17/r17a_patch.py`（3 hunk 纯 assert 字节级：锚点唯一 / 无 BOM /
          纯 CRLF / `ast.parse` / 拒绝二次应用）⇒ `region_analyzer.py`
          `110bf739bde62846 → 255d53d3c8707a07`（26643→26651 行，+9/−1；唯一代码改动为删④，
          其余为判据注释块与 docstring 同步改写）；`region_ast_generator.py` 本轮零改动
  - [x] SubTask 17.6: mandate 门禁顺序全绿：单点 **FLIPPED-CLEAN=3**
          （`IQData/manager/plugin_manager` 9/10→10/10、`IQEngine/core/plugin_manager` 8/9→9/9、
          `fly/common/user_error` 2/4→4/4）→ `quotation.pyc` 单验（`WORSENED(rolled back)`
          148/150→再生成 147/150，自动回滚；与 R16 同判 ⇒ SubTask 13.3 产物/核漂移，非本轮引入）
          → 全量产物门 `CLEAN 330→333 / UNCHANGED 64→57 / IMPROVED 0→4 / WORSENED 9 /
          REGRESSION 2 / NO-OKPY 1`，异常文件集合与 R16 **逐个相同**（11+1）⇒ 零新增回退
  - [x] SubTask 17.7: `pyc_index.json` 受影响条目按工具实测更新：`IQData/manager/plugin_manager`、
          `IQEngine/core/plugin_manager`、`fly/common/user_error` 三条转 `decompile_status: ok`；
          `IQCommon/logger/handlers`、`IQEngine/plugins/plugin_system_trade/trade_live_broker`、
          `calexrights_func` 孪生两条按实测重记。`scripts/pyc_batch_verify.py single` 对三个
          翻转文件报 `decompile_status: ok` / `match_rate 100.00%`
  - [x] SubTask 17.8: 电池与索引收尾：七套电池 `--strict` 退出码 0（UNEXPECTED/ERROR 全 0）；
          `round16_sink` 8 个 anchor 回填 `MISMATCH→SENTINEL`；本轮新增 `test_repros/round17_arm/`
          （26 复现 + `run_all.py` + `ANALYSIS.md`：for/while × 赋值/调用/for/while/try/with/
          return/break/continue 尾随、内层 elif 链、两层嵌套、module/class 作用域、BoolOp 变体、
          6 个负对照）——补丁前 MISMATCH=19 → 补丁后 MISMATCH=1（残留 `r17a_25` 即判据⑤终态
          共享退出场景），`--strict` 退出码 0；`pyc_index.json`
          `e7c3724b7b007f01 → 8af93efb770d8db6`（30 行改动全落在上述 7 条：3 项转 ok、
          2 项字段复算、2 项补 note；另将 `single` 因自身 60 s 超时把 `fly/data/quotation.pyc`
          写成的 `failed`/`0.0`/`ok_py_generated:false`+`error` 按 HEAD 逐字节回滚——磁盘上
          `quotationOK.py` 仍在，该写入反映的是工具超时而非产物状态）
  - [ ] SubTask 17.9: 本轮未完项移交：①`strategy.pyc` `tick_worker_thread` 签名 `seq_diff→seq_len`
          （268 vs 247，缺陷数不变）；②`calexrights_func` 孪生对残留 1 个 `target_diff`、
          `handlers` 残留 2、`trade_live_broker` 残留 26；③SubTask 13.3 产物/核漂移（quotation 等
          11 项每轮 WORSENED 回滚，根因在生成层）；④`r16a_05`、`r15a_08`、`r15a_09`、T1/T2
          then 臂收集顺序；⑤SubTask 13.4 与 Task 5 遗留照旧；⑥`pyc_batch_verify.py single` 对
          `fly/data/quotation.pyc` 必然 60 s 超时且超时会把该条目改写成 `failed`——需要么提高
          超时、么禁用超时写回（Round 18 结案：`single` 实测 5.1 s 完成，写回字段与 HEAD 相同）；⑦site-packages 内那 4 个由 `*OK.py`/校验脚本二次编译出的 pyc
          是否清理由用户决定。
          另：全仓 `_find_enclosing_loop` 其余 5 处调用（`:2264`、`:16623`、`:16661`、`:17047`、
          `:18458`）经复核均为**正向**用途（循环内 merge 重算 / 回边继承），无同类「按循环豁免」残留

- [x] Task 18: Round 18 — 移除 Round 13 `_discover_predicate_and_chain` 的跨层次吸收：外层
      `elif` 的测试块被当成 and 短路链前驱，在外层条件之下又发射一遍，成为内层条件的第一个合取支
  - [x] SubTask 18.1: 承接 SubTask 17.9③/13.3：quotation 产物/核漂移用镜像核（`git archive` 到
          `D:/Temp/r18/mirror/<rev8>`，仓库零写入）二分定位——`393d9ff0`/`675ca714`/`8a1b1def`
          三核再生成与磁盘产物一致，`f89b85f2` 起当前核比磁盘产物多一个缺陷函数
          `<module>.change_future_real_date`（`rounds/round18/arm-design.md`）
  - [x] SubTask 18.2: 根因判定为**跨层次唯一归属违例**（原则 2）：`elif X:` 的测试块不是任何区域的
          entry（只是父 if 链区域的 `elif_conditions` 成员），既有「entry 且 condition_block 即该块」
          守卫漏掉它；该块与内层条件块末指令跳同一汇合点、真路径 fallthrough 串联 ⇒ 被吸收为第一
          合取支。复现要条件是 elif 臂体内有前置语句（裸 `elif d: if d < e:` 两世界都 MATCH）
  - [x] SubTask 18.3: 测试工程师交付 20 个最小复现 `test_repros/round18_arm/`（11 锚点 +
          8 负对照 + 1 UNCONFIRMED）+ `run_all.py` + `ANALYSIS.md`（双世界逐条实测表）
  - [x] SubTask 18.4: 落地 `D:/Temp/r18/r18_fix_chain_owner.py`（字节级 assert：BOM / 锚点唯一 /
          纯 CRLF / `ast.parse` / 拒绝二次应用）⇒ `region_ast_generator.py` LF 归一 sha
          `a5e2f7e75fa69cca → a107457c5215daaf`（48175→48189 行，+15/−1；守卫 8 行，其余是判据
          注释块与 docstring `**嵌套处理**` 段同步改写）；`region_analyzer.py` 本轮零改动
  - [x] SubTask 18.5: mandate 门禁顺序全绿：单点 `change_future_real_date`
          `[seq_len] orig=91 decomp=93 → OK` → `quotation.pyc` 重生成后缺陷集合与磁盘产物**逐名
          相同**（SubTask 13.3 的 quotation 项结案）→ 全量产物门（402 条目分 8 片）
          `CLEAN 334 / UNCHANGED 59 / WORSENED(rolled back) 8 / REGRESSION(rolled back) 1`，
          9 项异常在补丁前镜像核上数值与缺陷函数名逐名相同 ⇒ 零新增回退
  - [x] SubTask 18.6: 项目工具 A/B（本轮前 HEAD 产物 vs 落地后产物，只读 `bytecode_diff`，
          唯一差别是产物文本）：`fly/simtradding/pboxAccount_jupyterhub` `getVaildAccount`
          3/4 → **4/4**（`single` 报 `decompile_status: ok` / `100.00%`）、
          `fly/data/quote` `change_future_real_date` 66 → 67、
          `IQCommon/util/replace_utils` `log_request` 7 → 8；另 3 个产物同样去掉重复合取支而
          官方计数不变（`data_proxy`、`realtime_event_source`、`quotation`）
  - [x] SubTask 18.7: `pyc_index.json` 5 条目按工具实测更新。4 条 `partial → ok`
          （`IQCommon/util/backtest_info_utils`、`IQEngine/config/config`、
          `plugin_fly_data/fly_api/setting_api`、`plugin_system_control/__init__`）经全量门 CLEAN
          证实**产物本就全匹配、条目停在 Round 10 旧值**——如实记为索引订正，不是本轮补丁效果；
          第 5 条 `fly/data/quote` `matched 66 → 67` 才是 R18-A 效果。条目 402、每条
          `function_count` 一律不变
  - [x] SubTask 18.8: 电池与确定性收尾：`round18_arm` 20 项 `--strict` 退出码 0
          （`MISMATCH=0 MATCH=20 ERROR=0 UNEXPECTED=0 NOT-REPRODUCED=1`）；既有 8 套
          （round13 / 13b / 14 / 14_join / 15_arm / 16_arm / 16_sink / 17_arm）在新核上全部
          退出码 0、UNEXPECTED=0、ERROR=0；6 个被改写产物用 `single` 重生成后与磁盘逐字节相同
  - [ ] SubTask 18.9: 本轮未完项移交：①`IQCommon/util/user_info_utils.pyc` 唯一缺陷
          `remove_lock_files` `[seq_len] orig=96 decomp=97`——`for file in files:` 里
          `if ...: try/except` 末尾多发射一条 `continue`（多一个 `JUMP_BACKWARD to 420`），该处
          已是 Round 07 / R4-H / R100 / RC3 四条抑制判据叠加之地，单列为下一轮目标（Round 19 结案：R19-A 只给 `[R3-Continue]` 补发射加既有谓词作第⑤条末判据，该 pyc 实测 `single` `ok 9/9 100.00%`、严格尺子 `OK 9/9`）；
          ②`r18a_05`（for 循环内 elif 臂）补丁前后都 MATCH，新守卫未覆盖该形状；
          ③9 文件既有漂移族（`to_pd_result`×3、`resist_api`、`flytools`、`quote_handler`、
          `real_quote`、`market_time`、`json_persistance`）仍会在闸门每轮触发 WORSENED 回滚；
          ④quotation 残留 `change_his_to_forward` seq_len +1、`get_trend` 跳转终点；
          ⑤SubTask 17.9 其余项（`strategy`、`calexrights_func`、`handlers`、`trade_live_broker`、
          `r16a_05`、`r15a_08`/`r15a_09`、`r17a_25`、T1/T2 then 臂顺序、SubTask 13.4、Task 5）照旧

- [x] Task 19: Round 19 — 给 `_if_generate_normal` `[R3-Continue]` 分支终结边补发射加第⑤条末判据
      `not self._if_false_path_is_loop_iteration(region)`，修「if 是循环体末条语句时，臂尾自然迭代
      回边被再补一条源码级 `continue`」（R19-A，翻正 `IQCommon/util/user_info_utils.pyc` 9/9）
  - [x] SubTask 19.0: 语料不新增条目——`pyc_index.json` 条目 402、每条 `function_count` 一律不变，
          本轮只按工具实测更新受影响条目
  - [x] SubTask 19.1: 承接 SubTask 18.9①：`remove_lock_files` 的多余 `continue` 用 `sys.settrace`
          在 HEAD `26e330ca` 实测锁定发射行 `_if_generate_normal:16896`；该守卫的四条判据
          （`then_stmts` 非空 / `_current_loop` 存在 / `merge_block is header` / then 末块
          `JUMP_BACKWARD` 直达 merge）只看 then 臂自身，不看该 if 是否循环体末条语句；同层
          `_process_if_blocks` 的 CONTINUE 角色抑制（`_r100_suppress:20702`）已用既有同层谓词
          `_if_false_path_is_loop_iteration` 得出「不发射」⇒ 同层同结构结论互斥
          （Round 17 删判据④所用的同一标准）
  - [x] SubTask 19.2: 该谓词在四个真实发射点上的取值实测（`D:/Temp/r19/probes/r19_where.py`）：
          目标 `remove_lock_files`（`else_blocks` 空、假出口 blk@712 是单条
          `JUMP_BACKWARD→420` 纯回边）谓词 True ⇒ 补发多余；`get_vip_user_info`
          （`else_blocks` 4 块）、`local_finance::get_local_valuation_factors`（假出口 blk@544
          有 LOAD_GLOBAL/LOAD_ATTR/CALL/POP_TOP 后才 `JUMP_BACKWARD@590`）、
          `plugin_system_fly_basicdata/basic_data_source::get_security_info`（假出口 blk@254 含
          BUILD_MAP/STORE_SUBSCR）谓词 False ⇒ `continue` 必须留；后两个正是宽规则会改坏的形状
  - [x] SubTask 19.3: 四个候选在仓库外用镜像核做全量逐函数 A/B，否掉三个
          （`git archive` 到 `D:/Temp/r19/mirror/`，402 条目重生成后跑严格尺子，
          `D:/Temp/r19/probes/{r19_par.py,r19_sum.py}`）：`cand_a`（整段删 `[R3-Continue]`）
          improved 2 / **broken 5**（净 −3：`IQCommon/data/basic_data_source`、
          `IQCommon/data/local_finance`、`plugin_system_fly_basicdata/basic_data_source`、
          `trade_live_broker`、`fly/data/quote`）；`cand_g`（另加 28 行新谓词「臂尾块由本区域块
          裸 fall-through 进入」）2/2 净 0；`cand_e`（⑤＋`cand_g`）1/0 与 `cand_d`（只加⑤）1/0
          逐条相同 ⇒ 那 28 行是纯冗余，取 `cand_d`：复用同层既有谓词、不新建判据、
          不看名字/常量/偏移。教训（已写进 `ANALYSIS.md` §三）：`cand_a` 在 39 项电池上
          19 个负对照一个没破却在全量上净亏 3 ⇒ 电池绿不等于无回退，门禁必须含全量逐函数 A/B
  - [x] SubTask 19.4: 测试工程师交付 39 个最小复现 `test_repros/round19_cont/`
          （20 锚点：9 修掉 / 4 残留 / 7 `UNCONFIRMED`；另 19 个负对照）+ `run_all.py` + `ANALYSIS.md`
          （双世界逐条实测表）；其交付的 EXPECT 表复现名与实际文件名不符（首跑
          `UNEXPECTED=29`），按两世界实测整表重写
  - [x] SubTask 19.5: 落地 `D:/Temp/r19/fix/r19a_patch.py` + `r19a_fixup.py`（字节级 assert：
          BOM / 锚点唯一 / 纯 CRLF / `ast.parse` / 拒绝二次应用）⇒ `region_ast_generator.py`
          `+38/−1`，其中**代码只有 1 行**（新末判据，原第④条的 `):` 移到新行末），其余 37 行是
          `[R19-A 修复]` 判据注释（识别条件／归约方式／唯一归属·结构结论一致／反编译流程／
          保留理由）；LF 归一 sha `a107457c5215daaf → e7ab6a8d436603a5`，`48189 → 48226` 行
  - [x] SubTask 19.6: mandate 门禁顺序全绿：单点 `user_info_utils.pyc` `partial 8/9` → `single`
          报 `decompile_status: ok` `9/9 100.00%`、严格尺子 `OK 9/9` → `quotation.pyc` 单验
          `partial 142/143 99.30%` 与 Round 18 收尾时逐字相同、产物不被改写 →
          全量产物门（402 条目分 8 片）`CLEAN 335 / UNCHANGED 58 / WORSENED(rolled back) 8 /
          REGRESSION(rolled back) 1`，9 项异常与 Round 18 的 9 项逐文件、逐数值相同
          ⇒ 本轮零新增回退，回滚全部生效
  - [x] SubTask 19.7: 电池：`round19_cont` 39 项 `--strict` 退出码 0（补丁前
          `MISMATCH=13 MATCH=26 NOT-REPRODUCED=7` → 补丁后 `MISMATCH=4 MATCH=35`，
          `ERROR=0 UNEXPECTED=0`；镜像核 `cand_d` 复跑逐项判定与落地核相同）；既有 9 套
          （round13 / 13b / 14 / 14_join / 15_arm / 16_arm / 16_sink / 17_arm / 18_arm）在新核上
          全部退出码 0、UNEXPECTED=0、ERROR=0，唯一变化是 `round13::r13_02_spurious_continue_loop`
          由「复现缺陷」变「已修」（EXPECT 改标 `SENTINEL`）——同族缺陷 Round 13 就记过形状
  - [x] SubTask 19.8: 唯一被核改写的产物 `user_info_utilsOK.py`（`1 file changed, 1 deletion(-)`）
          用 `single` 重生成后与磁盘产物逐字节相同（`cmp`）⇒ 无二次漂移；落地后 `git status`
          只有核、`pyc_index.json`（1 条目 `partial 0.888… → ok 1.0 matched 9`）、该产物与
          `test_repros/` 两处标注 ⇒ R19-A 对全语料产物的净影响就是那一条 `continue`
  - [ ] SubTask 19.9: 本轮未完项移交：①`round19_cont` 残留 4 锚点（04 臂尾 `try/finally`、
          05 `try/except/else`、12 臂尾嵌套 `while`、14 `elif` 臂尾 `try`）实测走另一条发射路径，
          另 7 项 `UNCONFIRMED` 本轮构造不出；②`IQCommon/util/trade_info_utils.pyc`（35/36）的
          同族多余 `continue` 只有宽规则能修，宽规则全量净 −3/0，本轮如实放弃，需另找判据；
          ③9 文件既有产物/核漂移族（`to_pd_result`×3、`resist_api`、`flytools`、`quote_handler`、
          `real_quote`、`market_time`、`json_persistance`）仍每轮触发 WORSENED 回滚（Round 20 结案归因：culprit 单提交 `f89b85f2`，其内三处独立回退判据 J1/J2/J3；整体回退实测 improved=8 broken=5 不可发货，见 `rounds/round20/OUTCOME.md` §四第 1 条）；
          ④quotation 残留 `change_his_to_forward` seq_len +1、`get_trend` 跳转终点；
          ⑤`r18a_05`、SubTask 17.9 其余项（`strategy`、`calexrights_func`、`handlers`（Round 20 结案：R20-A 修好两孪生 `perform_rollover` 119/127 逐条一致，同文件 `_target` 192→190 为独立残差照旧）、
          `trade_live_broker`、`r16a_05`、`r15a_08`/`r15a_09`、`r17a_25`、T1/T2 then 臂顺序、
          SubTask 13.4、Task 5）照旧
- [x] Task 20: Round 20 — 给 `_collect_natural_loop_body` 的 break-target 判别加第三条同层结构析取项
      `_r20_is_break_stub_block(_bb)`，并给 `_if_generate_normal` 的 W15-C「then-独占 merge 块并入
      then 臂」接上**既有**臂尾终止判据，修「`for …: if c: break` 的 break 跳转与循环回边整体丢失」
      （R20-A，翻正 `IQCommon/logger/handlers.pyc` 28/30→29/30 与
      `IQEngine/utils/logger/handlers.pyc` 16/17→17/17）
  - [x] SubTask 20.0: 语料不新增条目——`pyc_index.json` 条目 402、每条 `function_count` 一律不变、
          Σ=5746，本轮只按 `single` 工具实测更新受影响条目（2 条）
  - [x] SubTask 20.1: 承接 SubTask 19.9⑤ 的 `handlers` 孪生对：两孪生唯一真缺陷同为
          `<module>.RotatingFileHandler.perform_rollover`（orig=119 decomp=117 / orig=127
          decomp=125）；`D:/Temp/r20/scratch/recon_A.py` 重编译逐条核对确认真实源码就是
          `for … else …` ＋ 裸 `break`，多重集差里真丢的只有 break 的 `JUMP_FORWARD→302` 与
          外层回边 `JUMP_BACKWARD→102`（`missA.txt`），其余 ± 全是同一指令在两世界的偏移改名
  - [x] SubTask 20.2: 两层根因逐条实测（`D:/Temp/r20/logs/regA.txt`、`D:/Temp/r20b/logs/
          callsite_ca1.txt`、`wherebrk_ca1.txt`）：①分析器 6172/6174 两条判据都判 False
          （6140 的 BFS 穿过 break 自身的无条件跳转）⇒ `_break_targets=∅` ⇒ 6258
          `_return_reachable` 把 302/336/396/428/556 吞进循环体、`has_break=False`；
          ②生成器 16988 的 W15-C splice 在 16934-16942 已按终止语句截断臂之后仍无条件拼接
          （`settrace` 命中 `_if_generate_normal:16999`）；HEAD 核下该函数 Break/Continue
          发射点命中 0 次 ⇒ base 连 break 都没识别
  - [x] SubTask 20.3: 推翻上一棒「`region_analyzer:6172` 已被证伪」的判断：只改分析器（`c_a1`）
          区域层是对的（`body=[102,104,192,196]`、`break_blocks=[302]`），塌到 50/52 的原因是
          `break` 后又被拼进同臂的代码成了不可达死代码、被 CPython 3.11 死代码消除；
          只改生成器（`g1`）117/125 无效 ⇒ **两半缺一不可**（四候选表见 `arm-design.md` §三）
  - [x] SubTask 20.4: 判据收窄实测：宽判据 `f1`（去噪后「恰好一条无条件前向跳转」即算）
          两孪生过但全量 A/B **broken=1**（`slippage.create_new_price.check_and_return` 19→18，
          其块 124 = `[JUMP_FORWARD 130]` 是链式比较 out-of-line 桩、无迭代器可弹）⇒
          POP_TOP 是必需条件，不得简化；`g1b` broken=0 同时证明生成器守卫单独无害；
          最终 `f3` = 本轮回落地核（improved=2 broken=0 signature-only=0）
  - [x] SubTask 20.5: 测试工程师交付 26 个最小复现 `test_repros/round20_rollover/`
          （16 锚点 + 10 负对照/守卫）+ `run_all.py`（双向自检、表随 `--core` 选择）+
          `ANALYSIS.md`（双世界逐条实测）；落地后按其实测把 `EXPECT` 整表改写为落地真值
          （11 锚点→`SENTINEL`、7 项同族别因→`MISMATCH`、8 项守卫→`MATCH`、`UNCONFIRMED` 为空）
  - [x] SubTask 20.6: 落地 `D:/Temp/r20c/fix/r20a_patch.py`（字节级 assert：BOM／锚点唯一／
          纯 CRLF／`ast.parse`／拒绝二次应用）⇒ `region_analyzer.py` `+46/−3`（判据代码
          `+19/−3`）、`region_ast_generator.py` `+23/−1`（判据代码 `+5/−1`），其余是
          `[R20-A 修复]` 判据注释（识别条件／归约方式／唯一归属／反编译流程／保留理由）；
          sha16 raw `255d53d3c8707a07→eb378bd197e2efba`、`faf70dafbce09acf→9dff8c0ea8ece556`；
          落地核与已实测候选 `f3` 做剥注释逐行等价核对（两文件 `code-only diff lines: 0`）
  - [x] SubTask 20.7: mandate 门禁顺序全绿：单点两孪生 `single` `ok 14/14 100.00%`／
          `ok 18/18 100.00%`、严格尺子 17/17／29/30（`_target` 192→190 原样）→ `quotation.pyc`
          单验 `partial 142/143 99.30%` 与 Round 19 逐字相同、产物 sha256 未变 →
          全量产物门（402 条目分 8 片）`CLEAN 336 / UNCHANGED 57 / WORSENED(rolled back) 8 /
          REGRESSION(rolled back) 1`，9 项异常与 Round 19 逐文件逐数值相同 →
          全量逐函数 A/B（`git archive 5c63ce6b` 重建落地前核镜像，与工作区逐字节相同）
          improved=2（恰两孪生）broken=0、`sum(n_ok) 5985→5987`
  - [x] SubTask 20.8: 电池：`round20_rollover` 26 项 `--strict` 退出码 0
          （落地前核镜像 `MISMATCH=18 MATCH=8` → 落地核 `MISMATCH=7 MATCH=19`，
          `ERROR=0 UNEXPECTED=0`）；既有 10 套（round13/13b/14/14_join/15_arm/16_arm/
          16_sink/17_arm/18_arm/19_cont）在新核上全部退出码 0、UNEXPECTED=0、ERROR=0，
          唯一变化是 `round13::r13_20_for_else_break_lost` 由「复现缺陷」变「已修」
          （改标 `SENTINEL`）——同族缺陷 Round 13 就记过形状
  - [x] SubTask 20.9: 9 文件产物/核漂移族归因收口（只记录不动手）：culprit 单提交
          `f89b85f2`，三处独立回退判据 J1（analyzer「if-arm 是 sink ⇒ 抹掉 else 臂」，13/15 个
          漂移函数）/J2（生成器 `_discover_predicate_and_chain*`，`market_time.trade_is_open`）/
          J3（生成器 `[A4/V-M]`，`flytools.whitelist_filter`）；Round 14-19 全部排除。
          整体回退实测 `improved=8 broken=5`（`nomerge`/`j1j3`）⇒ J1 是 load-bearing、不可发货；
          这解释了每轮产物门同样 9 项 WORSENED 回滚的来历。回退改造（给 J1 找能清 5 个 BROKEN
          反例的同层判据、J2 非破坏性中和）移交后续轮次
  - [ ] SubTask 20.10: 本轮未完项移交：①`round20_rollover` 残留 7 项同族别因（07/11/17/18/21/23/26，Round 21 复核：落地核 `--strict` 仍 `MISMATCH=7 MATCH=19`、逐套计数与 Round 20 收尾时逐字相同
          共同点是 break 出口块不止一个、或出口块落在 except/while 别的区域种类里、或链式比较与
          循环出口共享 merge）；②`_if_generate_normal` elif 链返回路径 ~17156 还有一处同形状
          splice，本轮不为其预先加守卫（两孪生＋26 项＋402 条目都不经过它）；③`handlers.pyc`
          `TWHThreadController._target` 192→190 独立残差；④SubTask 20.9 的 J1/J2/J3 回退改造；
          ⑤quotation 残留 `change_his_to_forward`/`get_trend`（Round 21 复核：镜像核全量 A/B 两世界逐字段相同 `orig=548 decomp=549` 与 `target_diff #10`，产物门 `148/150 -> 148/150 UNCHANGED`）；⑥SubTask 19.9 其余项
          （`trade_info_utils`、`strategy`、`calexrights_func`、`trade_live_broker`、`r16a_05`、
          `r15a_08`/`r15a_09`、`r17a_25`、`r18a_05`、`round19_cont` 4 锚点、T1/T2 then 臂顺序、
          SubTask 13.4、Task 5）照旧
- [x] Task 21: Round 21 — 把「协程语句前缀块是 body 块」这条同层判据在两个接线点各补全一半
      （BoolOp 非首成员块守卫 ＋ elif 链 `_has_body_stmt` 过滤表），修
      `fly/oauthenticator/oauth2.pyc` 两个同形孪生 `post` 各丢 9 条（R21-A，10/12→12/12）
  - [x] SubTask 21.0: 语料不新增条目——`pyc_index.json` 条目 402、每条 `function_count` 一律不变、
          Σ=5746（脚本 assert），本轮只按 `single` 工具实测更新受影响条目（1 条）
  - [x] SubTask 21.1: 承接 Task 9（同一 pyc 第二次成为目标：Round 9 修的是「生成器函数体整体
          丢失 214→`pass`」，本轮是另一族）。诊断实测：官方 `partial 10/11`、严格尺子
          `DEFECT 10/12`，`HSIDOAuthCallbackHandler.post orig=175 decomp=166`、
          `OAuthCallbackHandler.post orig=190 decomp=181`；`_r10_difflen.py` 给出**单一 delete
          窗口** orig[116:125]、无配对 insert ⇒ 判决是 ABSENT 而非 relocated，opcode 多重集差
          `CALL-1 LOAD_CONST-1 LOAD_FAST-2 LOAD_METHOD-1 POP_TOP-1 RESUME-1 RETURN_VALUE-1
          YIELD_VALUE-1`、`spawn_single_user orig=2 decomp=1` ⇒ 排除「POP_TOP/PUSH_NULL 记账」假设
  - [x] SubTask 21.2: 块 624 与块 734 完全同形（`yield f()` 语句前缀 ＋ 以条件跳转结尾），
          一处 in then 臂、一处 in else 臂；`sys.settrace`（`r21_trace.py --off 566`）实锤
          执行路径：成员块守卫 `_has_store=False` ⇒ 624 被 `chain.append` 收进链 →
          返回 `[(566,'or'),(624,'and')]` → `BoolOpRegion` → 产物 `and` 合并、else 臂 return 消失；
          `r21_cond.py` monkeypatch 实锤站点 B：`_build_basic_if_region([734,802,836])` 先建出
          IfRegion，随后 `_build_elif_region([210,…,734,802,836])` 把 734 抢成「纯 elif 条件块」，
          链三支全 return ⇒ 前缀语句退到链后被死代码消除。−2（A）＋ −7（B）= −9，逐条吻合
  - [x] SubTask 21.3: 八候选实测表（`r21_mk.py` 表驱动镜像核 + `r21_twins.py` +
          `run_all.py --measure` + 402 全量 A/B）：c1（站点 A 宽版 向前≤5）176/191 残留 B 错位
          +1；c2（块内任意 POP_TOP）与 c1 同测值 ⇒ 宽判据无额外收益、风险更高，**丢弃**；
          c3（只站点 B）173/188 ⇒ 证明两半缺一不可；c5 = c1+c3、**c6 = R21-A**（站点 A 用与
          起始块/elif **同形**的判据文本）均 175/190 = 0 差、strict 12/12；
          c8（c6 + 第三份拷贝也补间隙）目标上零增量、爆炸半径更大 ⇒ **不并入**
  - [x] SubTask 21.4: 零新判据核对：规则文本 = 仓库里已写两遍的 `_sb_has_body` /
          `_has_body_stmt` 的另一半（`CALL` → 只允许 `YIELD_VALUE`/`RESUME` 间隙 → `POP_TOP`，
          遇其他指令立即停止）；不看函数名、不看字符串常量、不看原始字节码偏移
          （`i.offset < 本块末条.offset` 是块内结构边界，与该站点既有判据同写法）；
          四条归约原则逐条复核（自底向上不变、两处都**减少**块的多重认领、内层 if 仍是单个
          抽象子节点、只读被判定块自身指令）见 `rounds/round21/arm-design.md` §四
  - [x] SubTask 21.5: 测试工程师交付 16 个最小复现 `test_repros/round21_oauth2/`
          （5 锚点 + 8 负对照 + 3 同族异因）+ `run_all.py`（三表随 `--core`/`--base` 选择、
          键集合双向自检、留 None 即 fail-closed）+ `ANALYSIS.md`（四世界逐条实测：
          5c63ce6b/15a8de06 两基线一致，c6 两候选一致）；其 `EXPECT` 交付时已是落地后真值，
          落地核复跑逐项同值 ⇒ 本步零改写
  - [x] SubTask 21.6: 落地 `D:/Temp/r21fix/fix/r21a_patch.py`（字节级 assert：无 BOM 保持／
          纯 CRLF／两处锚点各唯一／拒绝二次应用／`ast.parse`／判据代码与候选 `c6` 逐行等价）
          ⇒ `region_analyzer.py` `+74/−2`（判据代码净增 29 行：站点 A 22、站点 B 7；注释 43 行），
          sha16 raw `eb378bd197e2efba→8529b7e8e36dc336`、LF 归一
          `2311fcbbea5c166d→2b9c48a681a2cb23`，26694→26766 行
  - [x] SubTask 21.7: mandate 门禁顺序全绿：单点 `oauth2.pyc` `single` 报 `ok 11/11 100.00%`、
          严格尺子 `OK 12/12`（无 DEFECT 行）、产物 `ast.parse` 通过且逐行 diff 只有被恢复的
          `yield`/`return`（154→162 行）→ `quotation.pyc` 单验 `partial 142/143 99.30%`
          与 Round 20 逐字相同、产物 sha256 `c0d3c312…` 未变、`git status` 干净 →
          全量产物门（402 条目分 8 片，基线 = 打补丁之前先跑的落地前磁盘产物严格比对）
          `CLEAN 337 / UNCHANGED 56 / WORSENED(rolled back) 8 / REGRESSION(rolled back) 1`，
          9 项异常与 Round 20 **逐文件、逐数值相同** ⇒ 零新增回退
  - [x] SubTask 21.8: 全量逐函数 A/B 改在**真正的落地基** `15a8de06` 上重跑（诊断是在
          `5c63ce6b` 上做的）：`git archive 15a8de06` 镜像与落地前工作区逐字节相同
          （`eb378bd197e2efba`），cand 镜像只差本补丁（`8529b7e8e36dc336`）⇒
          两侧 402/402 记录、0 异常，`improved=1 broken=0 signature-only=1`、
          Σn_ok `5987→5989`；电池：新增 16 项 `--strict` 退出码 0
          （`MISMATCH=3 MATCH=13 UNEXPECTED=0 ERROR=0`），既有 **11 套**全部退出码 0 且
          逐套计数与 Round 20 收尾时逐字相同（本轮无锚点被顺带修好，无需改标 `SENTINEL`）；
          对外序列 stats `402/363/5746/5632/98.02% → 402/364/5746/5633/98.03%`（只 +1 而非
          预期 +2：官方尺子落地前只把两个 `post` 里的一个记成 mismatch，条目 `mismatch_count: 1`）
  - [x] SubTask 21.9: **严格尺子的盲区（本轮新发现，如实登记）**：诊断记为 `signature-only` 的
          `realtime_event_source.pyc` 并非中性——`clock_worker`（本已缺陷）产物由
          `orig=1276 decomp=1251` 变 `decomp=1079`（丢 25 → 丢 197），bad **计数**不变 ⇒
          产物门只裁 `UNCHANGED`、A/B 只记 signature-only。单开一半的归因实验：只站点 A ⇒
          与全开逐字节相同（sha16 `3e367cad6833514f`），只站点 B ⇒ 与落地前逐字节相同
          （`e5f216ab559526a1`）⇒ 恶化 100% 出自站点 A。全语料盲区扫描（逐函数
          `Σ|orig−decomp|`，`r21_blind.py`）`worse=1 better=1` ⇒ 全语料只有这一个函数变差。
          处置：按「不得变差」把该产物保全回落地前版本（内容未手写，`git checkout HEAD --`，
          sha256 `125dc621…` 复原），`single` 已按要求重跑并复核索引逐字段一致
          （`partial 11/12 0.9166666666666666`）。⇒ 第 10 个产物/核不一致文件（但非第 10 项
          产物门异常）。纪律更新：此类截断 BoolOp 链的修复，门禁必须同时看
          `Σ|orig−decomp|`，不能只看 `n_ok`
  - [ ] SubTask 21.10: 本轮未完项移交：①SubTask 21.9 的站点 A 副作用根因（截断 BoolOp 链后
          父臂对块的双认领，与 SubTask 20.9 的 J1 同族）；②`round21_oauth2` 残留 3 项
          （12 `await`/`GET_AWAITABLE`/`SEND` 族 44→41、13 循环体内同族 −6→+1 仍未收口、
          14 真 and/or 链过量发射 +2 = Round 22 目标）；③ANALYSIS §10 未闭依赖链（A 族触发
          条件比「块含协程语句」更窄，上游为何走到成员块扩展仍依赖外层 IfRegion 的
          `IF_FALSE` 同目标判据）；④`if (yield self.g(x)):` 产物丢外层括号 → SyntaxError；
          ⑤`handlers.pyc` `TWHThreadController._target 192→190`（镜像核 A/B 两世界逐字段相同，
          本轮逐字未动）；⑥SubTask 20.10 其余项（`round20_rollover` 7 项、~17156 splice、
          9 文件漂移族 J1/J2/J3 回退改造、quotation 2 项、SubTask 19.9 其余项、T1/T2 then
          臂顺序、SubTask 13.4、Task 5）照旧

- [x] Task 22: Round 22 — 把漂移族三条同层判据（J1′ 汇点臂塌缩细化 / J2′ or-短路链首落点判据 /
      J3′ 删跨区域 V-M 判据）收进区域归约框架并落地（R22-A），同时**首次以 `batch --all` 把
      `pyc_index.json` 拉回实测**（Round 18–21 四周期无回写通道，392/402 条停在 Round 10）
  - [x] SubTask 22.0: 语料不新增条目——`pyc_index.json` 条目 402、每条 `function_count` 一律
          不变、Σ=5746（脚本复核），added/removed=0；被改动的字段只有
          `matched_functions`/`decompile_status`/`bytecode_match_rate`/`last_tested_round`
  - [x] SubTask 22.1: 靶子不是"某个 pyc 的某个函数"而是**索引本身**：官方尺在当前 HEAD 上逐文件
          重测语料并与条目逐条对照 ⇒ 11 个文件背离（9 条索引虚高共 −14、2 条低估 +2；净 −12）。
          其中 5 条标着 `ok` 而实测有函数不匹配。机制：`scripts/pyc_batch_verify.py:358-361`
          写明 `batch` 默认跳过 `ok` 条目，而 Round 18–21 收尾无 batch 步骤；逐提交二分另指出
          `trade_info_utils`+`custom_tools` 的 43/46 自 `f89b85f2`（Round 13）即存在
  - [x] SubTask 22.2: 三条判据的逐补丁归属（严格尺子，镜像 `mirror/{base,j1g,j2p,j3}`，
          11 个漂移文件，记录 `ab/attr2_*.jsonl`）：J1′ 12 个函数、J2′ 2 个、J3′ 1 个 = 15；
          两条例外如实登记——`quote_handler.get_kline_local`（760→676）只有三补丁同场才回到
          760→682（J1′ 先恢复臂结构，链判据才用得上），`api_base.get_history_df` 在 J2′ 下
          1742→1722 退到 1742→1718
  - [x] SubTask 22.3: 测试工程师交付 37 个最小复现 `test_repros/round22_drift/`（17 锚点 +
          15 负对照 + 5 同族残留）+ `run_all.py`（before/after 双镜像核、真值表随 `--after`
          选择、键集合双向自检 fail-closed、零仓库写入）+ `ANALYSIS.md`
  - [x] SubTask 22.4: **加强版 J2r 落地后被电池判死并回退**（本轮方法论收获）：J2r 在语料级
          严格优于 J2′（`n_ok` 同为 +15、`Σ|delta|` −85 对 −81、`worse=0` 对 `worse=1`、
          `improved=10/broken=0` 相同），两把尺子都看不出问题；但电池锚点
          `r22_16_j2_andor_three_disjuncts`（`if a and b or c and d or e and g:`）NOT-FIXED
          `orig=17 decomp=9` —— 加强判据要求发跳转前驱块自身承载区域，而 `or` 的短路汇合点
          不成区域 ⇒ 判据不触发 ⇒ 链重建丢掉左半析取支。语料 402 个 pyc 无此形状。
          两种写法日志 `batt_j2r.txt`/`batt_r3.txt`（各 `FIX=16/17 FAIL=1 GATE: FAIL`）；
          回退后落地 J2′，电池 `FIX=17/17 GUARD=15/15 RESIDUE=5/5 FAIL=0 GATE: PASS`
          （`batt_landed.txt`）。纪律更新：候选规则必须先过本轮最小复现集，再谈语料级 A/B
  - [x] SubTask 22.5: 零新判据核对：三条都只用既有同层构件（`_find_enclosing_loop`、
          `_is_return_none_block`、`_chain_block_is_pure`、`FORWARD_CONDITIONAL_JUMP_OPS`），
          不看函数名/字符串常量/原始字节码偏移；J1′ 只否定一次 merge 认定、J2′ 只放弃一次 test
          重建、J3′ 只删一条跨区域全 CFG 扫描的否决分支 ⇒ 四条归约原则逐条复核未被触碰
          （`arm-design.md` §三），且 J3′ 删掉的正是"禁止跨区域启发式"的违例本体
  - [x] SubTask 22.6: 落地 `landing/spec_r22_v2.py`（`build_final2.py` 由 base↔实测候选
          `mirror/j123` 的行级 hunk 自动生成 + 两处纯注释改动；`apply_spec.py` 白名单仅这两文件、
          锚点 `count(old)==1`、按文件 EOL 约定还原 CRLF、内存 `compile()` 自检）：
          `region_analyzer.py` `8529b7e8e36dc336→59b70fa360d19ad0`、
          `region_ast_generator.py` `9dff8c0ea8ece556→a203dd17fe82f824`（BOM 保持）。
          写盘后与工作树复验：与实测候选差 `+6/−9` 行、全部为注释/docstring，
          **剥 docstring 后 AST dump 逐节点相同**（`proof_landed.txt`）
  - [x] SubTask 22.7: mandate 门禁顺序全绿：电池 PASS → `single` 把两个靶子修到完全 OK
          （`json_persistance 7/7 100.00%`、`market_time 10/10 100.00%`）→ `quotation.pyc`
          `partial 142/143 99.30%`、唯一缺陷 `change_his_to_forward orig=547 decomp=548`
          与 Round 21 逐字相同 → `batch --index pyc_index.json --all --round 22`（402/402、
          `failed_pyc 0`）→ `stats`
  - [x] SubTask 22.8: 对外序列（`stats --index pyc_index.json`）：
          `402/362/5746/5633/98.03%`（收尾）；索引被这一步改动的条目 4 条
          （`instance 29/32→31/32`、`trade_live_broker 103/119→104/119`、
          `custom_tools 6/6→5/6` ok→partial、`trade_info_utils 40/40→38/40` ok→partial）。
          序列数字与上一轮同为 5633，但本轮起它是**实测值**：落地前用旧核实测 5621、
          `ok_pyc` 实测 359 ⇒ 本轮真实净增 12 个函数一致、`ok_pyc` 359→362
  - [ ] SubTask 22.9: 本轮未完项移交：①`realtime_event_source.clock_worker` −197（Round 21 的
          人工保全产物被本轮 `batch --all` 按当前核重写，官方读数不变 11/12；当时的根因假设
          = 截断 BoolOp 链后父臂双认领，`test_repros/round22_adoption/ANALYSIS.md` §1–4 + 探针
          `D:/Temp/r22diag/probes/sp_c1.py,c2,c3`，门禁必须同时看 `Σ|orig−decomp|` 与电池。
          **→ Round 23 已实测否证该假设并改判为 `self._or_*` 跨帧被踩＋loop 条件块前导无人发射，
          该假设列在 23.1；−197 现余 D2/D3 两层，见 23.9 ①**）；
          ②电池 5 项残留（`r22_23` `A and B or C`、`r22_24` `X or (A and B)` 括号形、
          `r22_25` `while A and B or C and D`、`r22_26` `or` 后接 `and` 臂、
          `r22_27` `persist` 在 while 内 73→65）；③过量发射族 4 项
          （`executor.check_before_trading 243→254`、`data_proxy.get_bar 86→90`、
          `replace_utils.decrypt_database_url 295→324`、`realtime_event_source.get_one_event 19→20`）；
          ④`f89b85f2` 遗留退化（`trade_info_utils` −2、`custom_tools` −1）；
          ⑤quotation `change_his_to_forward`、`handlers.pyc` `_target 192→190`、
          SubTask 21.10 其余项照旧

- [x] Task 23: Round 23 — 落地 R23-A（or-extension 臂状态 callee-saved）＋ R23-B（loop 条件块
      前导语句发射权归父序列），修掉 `realtime_event_source.clock_worker` −197 里唯一使产物
      **语义错误**的那一层（Q1：`dt = datetime.datetime.now()` 整条被丢弃）
  - [x] SubTask 23.0: 语料不新增条目——`pyc_index.json` 条目 402、每条 `function_count` 一律不变、
          Σ=5746、added/removed=0（脚本复核）；本轮被改动的字段只有 `last_tested_round`
          （402 条 22→23），**实质字段（`matched_functions`/`decompile_status`/
          `bytecode_match_rate`）改动条目 0 条**
  - [x] SubTask 23.1: 测试工程师线（任务 #28/#33）：**否证 22.9 ① 的旧根因**——按旧标题
          「截断 BoolOp 链后父臂双认领」实现的候选核在 402 文件 A/B 里只动 1 个文件，且 6 个手写
          or-extension 形状（含 ddmin 最小形）在两核上产物**逐字节相同** ⇒ 不是机制而是同文件巧合。
          复核成立的归因：`self._or_then_block/_or_else_block/_or_rhs_block` 被**自己递归下去的
          那一层**在 `_if_generate_normal` 开头无条件复位（`16526-16528`），父区域返回后读到
          子区域的 `None` ⇒ 父 else 臂静默丢弃（`ANALYSIS.md` §1.1–1.2）
  - [x] SubTask 23.2: 残余拆三层并证明只剩"顺序"可走（`ANALYSIS.md` §3.4）：D1 = loop 条件块前导
          被丢弃（`dt` 未绑定，语义错误）；D2 = 过量发射 +16；D3 = 同形块换位。**严格尺
          `_r10_strict_check.py:105-106` 在长度不等时立刻 `return 'seq_len'`** ⇒ D1 未消时
          D2/D3 不被任何尺子计分，顺序必须 D1→D2→D3
  - [x] SubTask 23.3: 测试工程师交付 16 个最小 case `test_repros/round23_clobber/`
          （6 CONTROL ＋ 5 DIAG ＋ 5 DIAG_OR_EXT_NOEFFECT）+ `run_all.py`（每核全新子进程、
          镜像核零仓库写入、`MUST_CONTAIN` 文本断言、语料锚点）+ `ANALYSIS.md`。
          关键设计：**b07/b08/b11 各 −3 复现 Q1；b09（内层换成 `if`）是 loop/if 判别子；
          b10/c12..c15 为负对照**
  - [x] SubTask 23.4: 门禁指标先于实现被改写（`arm-design.md` §四）：R23-B 必然把
          `clock_worker` 从 1287 推到 1292（\|Δ\| 11→17），**以 Σ\|orig−decomp\| 为门禁会直接
          否决这个正确修复**（§7 连同测量否决该候选）⇒ 改用 (i) 产物含该语句 + (ii) 官方尺
          `first_diff` 后移 + (iii) 其余 401 文件逐文件不回退；主门禁为电池
          `b07/b08/b11 → OK` ＋ CONTROL/判别子零变化
  - [x] SubTask 23.5: 落地 `D:/Temp/r23land/probes/{mk_spec23.py,sp_landed23.py,apply_spec.py}`：
          spec 由 base(=mirr/head23，与工作树 sha256 相同)→实测候选 (mirr/r23b2) 的行级 hunk 派生
          （analyzer 0 hunks、ast_generator 8 hunks），**内置自证 spec(base)==候选字节**；
          白名单仅两文件、锚点 `count(old)==1`、按文件 EOL 约定还原 CRLF、内存 `compile()` 自检。
          `region_ast_generator.py a203dd17fe82f824→a365c378e6a40fed`（BOM/纯 CRLF 保持），
          `region_analyzer.py 59b70fa360d19ad0` 未动。写盘后由**工作树**重建 `mirr/landed23`
          并逐文件哈希核对：core 33 + bytecode 8 + `pycdc.py` 全等 ⇒ 后续门禁都在落地字节上跑
  - [x] SubTask 23.6: mandate 门禁顺序全绿：电池对落地核复跑 `fixed=3 / broken=0`、
          `.py` 形状 `Σ|d| 21→12`、锚点 `198→17`、`G0/G2/G3=True → GATE: PASS`
          （`G1=NOT EVALUATED`：R23-A 在 `.py` 层不可测，不谎报 True）→
          靶子 `single`（官方尺 11/12、`first_diff 666→794`、`true_diffs 612→480`）→
          `quotation.pyc` `partial 142/143 99.30%`、唯一缺陷 `change_his_to_forward orig=547
          decomp=548` 与 Round 21/22 逐字相同且 `quotationOK.py` 未被改写 →
          `batch --index pyc_index.json --all --round 23`（402/402、`failed_pyc 0`）→ `stats`
  - [x] SubTask 23.7: 语料级严格 A/B（402×3 核镜像）：`Σn_ok 6004/6207` 三核同值、
          `Σsad 1771→1585→1590`；**两候选各自触发面都是 1/402 文件**（按产物长度判定），
          谓词前驱形状 39 文件出现、38 个逐字节不变、其中 14 个当时已完全匹配者全部零变化
  - [x] SubTask 23.8: 对外序列（`stats --index pyc_index.json`）：
          `402/362/5746/5633/98.03%` —— **本轮官方序列零增益**（翻不动 `realtime_event_source`
          是设计里写下的预期），索引条目实质字段 0 改动，差别在于 5633 是用本轮落地核复验的实测值
  - [ ] SubTask 23.9: 本轮未完项移交：①`clock_worker` 残余两层 D2 过量发射（+16，本轮起首次
          可见可测 → Round 24 直接入口）、D3 同形块换位（`ANALYSIS.md` §3.3 token 级实测）；
          ②R23-A 类（callee-saved 跨帧状态）在 `.py` 形状层不可测 ⇒ 验收只能靠语料锚点＋触发面，
          `self` 上其余跨帧字段清点见 `ANALYSIS.md` §3.1；③Round 22 电池 5 项残留
          （`r22_23`…`r22_27`）；④过量发射族其余 3 项（`check_before_trading 243→254`、
          `get_bar 86→90`、`decrypt_database_url 295→324`）与 `get_one_event 19→20`；
          ⑤`f89b85f2` 遗留退化（`trade_info_utils −2`、`custom_tools −1`）、quotation
          `change_his_to_forward`、`handlers.pyc _target 192→190`、SubTask 21.10 其余项照旧
  - [x] SubTask 24.1: 目标池实测（HEAD `3b6143c4`）：40 partial 文件 / 111 个官方不匹配函数 /
          Σdeficit 113，其中 **16 个文件 deficit=1**；按官方 `true_diffs` 排出最便宜九锚并逐个
          镜核复测（head-vs-head 对照 SAME=9、产物零变化）。族划分：纯换位（等长）10 函数/10 文件，
          其中 3 个文件全部缺陷等长 ⇒ 单点即可翻转（`data_proxy.get_bar` t=8、
          `plugin_fly_data/__init__` t=19、`load_daily.<module>` t=19）。
          **否证 Round 23 移交清单的暗示**：`orig LOAD_* vs decomp LOAD_CONST None`
          「过早收尾」签名只有 3 个函数且两个首差后还有更大破坏 ⇒ 不构成一族
  - [x] SubTask 24.2: 线 A（多余无条件跳转/块次序）候选**否证**：以 `get_bar` 为最清晰见证
          （orig 76-83 的 `else: return BarData(…)` 尾块与 84-85 的 `return None` 尾块整体换位，
          3 个 jump_diffs 是随之重接的 `POP_JUMP_FORWARD_IF_NONE` 目标 574→582）。据此提出的
          候选在全量触发面实测 better=2 / equal=8 / **worse=14，打坏 11 个当时已 ok 文件** ⇒ 不落地
  - [x] SubTask 24.3: 线 C 根因（同层判据缺失）：分析端 `IfRegion.can_be_ternary_header`
          在 `chained_compare_blocks` 非空时**一律**返回 False，而生成端 `_detect_ternary_pattern`
          的 Phase-7-D 分支恰以 `region.entry is block` 为键支持该形状 —— 两边判据不同层。
          被拒后的降级路径是致命一环：三元赋值被拆成 if/else 语句，两臂纯值块的栈顶值被丢弃，
          **赋值语句整体消失**（`data_count` 从未重绑 = 语义缺陷，不只是指令错位）
  - [x] SubTask 24.4: 电池 `test_repros/round24_cc_ternary/`（7 case ＋ `run_all.py` 五道闸
          G0 锚点上升 / G1 FIX 形状 FAIL→OK / G2 CONTROL 全核 OK / G3 无 OK→FAIL /
          **G4 CONTROL+STABLE 产物 sha256 逐字节相同**）。`PRED_R24A_STABLE` 只承诺字节相同、
          不承诺 OK：b03/c04/c06 在 HEAD 上就因另一族既有缺陷 FAIL（实测写进每个 case 的
          `ACTUAL-HEAD` 行），把「必须 OK」写进这类用例等于谎报。
          配套负结果：从**产物源码**回推的 6 个形状在 HEAD 镜核下全部官方 2/2 matched
          （回推源码重编译后块布局不同 ⇒ 换位不复现），换位族最小复现必须从**字节码布局**构造；
          且 `t1/t3` 产物含明显死代码仍被判 matched ⇒ 「官方 ok」≠ 产物良构，电池不被官方臂替代
  - [x] SubTask 24.5: 选型 patchA → patchA4。patchA（`entry or chained_compare_blocks[-1]`）
          在 58 文件触发面上过量发射；patchA3 与 patchA4 在该触发面**逐字节相同**
          ⇒ 取最小判据 `block is self.entry and self.entry is not analyzer.cfg.entry_block`
          （R24-A）。触发面读数：**2 文件产物变化、0 个当时已 ok 文件变化、Σmatched 1905→1906**
  - [x] SubTask 24.6: 全量 402 双尺 A/B（都在镜核上跑，官方臂按**产物 sha256** 计数）：
          官方 `Σmatched 5633 → 5634`、**402 个产物里只有 2 个变化**、0 个当时已 ok 文件被改动、0 错误；
          严格 sweep 402/402：按 `textlen` 判定产物变化同为 2/402（`real_quote` sad 10→9 且
          n_ok 37→38、`quote` sad 224→223），`Σn_ok 6004→6005`、`Σsad 1590→1588`、
          **0 文件变差、0 文件 n_ok 变少** ⇒ 本轮不存在 Round 23 那种 Σ|Δ| 否决冲突
  - [x] SubTask 24.7: 落地 `region_analyzer.py 59b70fa360d19ad0 → 6df13cdaf815920c`
          （13 增 1 删，纯 CRLF 26793 行不变、无裸 LF、无 BOM；`region_ast_generator.py`
          `a365c378e6a40fed` **未动** —— 分析端单文件修复）。spec 由实测镜核派生并自证
          `spec(base)==候选字节`；落地后由工作树重建 `mirr/landed24` 逐文件哈希核对，
          后续门禁全在落地字节上跑。落地后又做过一次**纯注释**修正（注释残留 patchA 的
          「最后一个比较块」说法），代码行逐字未变 ⇒ 最终读数对象是 `6df13cdaf815920c`
  - [x] SubTask 24.8: 对外序列（`stats --index pyc_index.json`）：
          `402/362/5746/5634/98.05%` —— 上一轮 `5633 / 98.03%` ⇒ **+1 函数、+0.02pp**。
          索引 402 条里唯一实质变更 `real_quote.pyc matched_functions 37→38`
          （`84.09%→86.36%`），其余 401 条只有 `last_tested_round 23→24`；
          `batch --all --round 24` 只重写 2 个 OK.py（`real_quoteOK.py`、`fly/data/quoteOK.py`），
          无产物漂移爆发
  - [ ] SubTask 24.9: 本轮未完项移交：①R24-A 缺另外两半 —— 三元头位于**函数首块**
          （`self.entry is cfg.entry_block`）时仍不放开，见证 `get_cache_l2_data` /
          `get_cache_l2_data_by_one`（`337→335`、`321→319`，`first_diff index 18
          JUMP_FORWARD vs POP_TOP`）与电池 `b03`（两核逐字节相同、都 FAIL），需生成端配合；
          ②`for` 体内嵌套三元（电池 `c04`，两核相同）；③`quote.get_individual_data` 长度差
          还剩 6；④`data_proxy.get_bar` 纯换位需"同形尾块唯一归属"级同层判据，线 A 第一版已否证；
          ⑤未收口诊断线 B/D/E/F/G（任务 #39/#41/#42/#43/#44）—— 五路代理都在 150 轮上限终止且
          未交 `ANALYSIS.md`，**下轮换协议：单线路径预算内先交 ANALYSIS.md 再交候选核**；
          ⑥Round 23 移交项其余照旧。距 100% 还差 112 函数 / 40 partial 文件
