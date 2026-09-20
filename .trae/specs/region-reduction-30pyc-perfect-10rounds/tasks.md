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
  - [x] SubTask 12.5: 批量回归：全量 402 严格尺子 + 官方口径双复验，零回归（产物门 CLEAN=320 FLIPPED-CLEAN=3 IMPROVED=1，11 个劣化自动回滚）
  - [x] SubTask 12.6: 提交并 push（f89b85f2 → origin/main；仅 add 本轮实际改动文件，未用 git add -A）

- [ ] Task 13: Round 14 — 区域归属层解决「前缀语句已发射」判据（A2 回退项的正解）
  - [ ] SubTask 13.1: 在**归属层**记录「块语句序列由哪个区域发射」：
        为 BoolOp/三元链的 first_chain_block 判定「其前缀语句是否已随该块发射」
        提供唯一权威来源。禁止再生成期标记集合上弥补
        （实测：块级 generated_blocks 被表达式消费路径污染；
        generated_offsets 只零散登记 start_offset；新增台账也覆盖不到 create_order
        的第一份发射路径 —— 三种判据全部失败，见 OUTCOME.md §四）
  - [ ] SubTask 13.2: 恢复 A2 想解决的问题且不复发重复发射：
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
  - [ ] SubTask 13.6: 全量 402 严格尺子 + 官方口径双复验，产物零回退
  - [ ] SubTask 13.7: 提交并 push

# Round 13 记录补充
- 双口径数字、翻正清单、回退证据与工序：`rounds/round13/OUTCOME.md`
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
  - [x] SubTask 14.7: 全量产物门 406 targets：CLEAN=327 UNCHANGED=67 WORSENED(回滚)=9
          REGRESSION(回滚)=2 NO-OKPY=1；翻正到 100% 的 pyc = IQCommon/profiler_func 16/16、
          IQData/utils/profiler_func 14/14（满足「每轮至少解决一个 pyc」）
  - [ ] SubTask 14.8: 本轮未完项移交：SubTask 13.1/13.2（`round14_join` 11 个 MISMATCH：
          前缀重复 +13 与 then 区截断同族）、SubTask 13.4（R13-C 链尾吸收，含 A-2
          `PluginManager.set_engine` ×2）、Task 5 遗留（`decrypt_database_url` +29、cgroup +2/+1）
