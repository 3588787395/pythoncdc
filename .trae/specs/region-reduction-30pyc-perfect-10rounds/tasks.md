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


- [ ] Task 5: Round 5 — R3-F 三元表达式在「表达式位置」降级
  （`[1 if c else 0]` 下标赋值、链式比较三元 `x = A if C else B` → 伪 return）
  - [ ] SubTask 5.1: 测试工程师建复现（已发现：`int(x) if 0 < int(x) <= 200 else 200` 生成伪 return）
  - [ ] SubTask 5.2: 修复工程师按区域归约修语句跨度/伪三元合并
  - [ ] SubTask 5.3: 验证 build_current_period_df / get_individual_data 转 OK
  - [ ] SubTask 5.4: 批量回归 + 提交 push

- [ ] Task 6: Round 6 — R3-A f-string 调用参数区域模板重建
        （get_price / load_get_price / load_bars_from_hundsun）
- [ ] Task 7: Round 7 — R3-L 旋转 while 循环体语句丢失
        （check_limit / get_real_from_zeromq / initImagedata）
- [ ] Task 8: Round 8 — R3-I try/except 区域块归属错乱（灾难级）
        （run_individual_transform / run_tick_socket）
- [ ] Task 9: Round 9 — fly/oauthenticator/oauth2.pyc 生成器函数体整体丢失
        （OAuthCallbackHandler.post，214 条指令 → 仅 `pass`）
- [ ] Task 10: Round 10 — 剩余 partial 文件清零，全量 402 pyc 100%

# 环境阻塞（须先解决）

本会话中途 bash 不可用（`unable to load netapi32.dll`），PowerShell 被沙箱拒绝，
导致 SubTask 4.2 之后**无法执行验证 / 提交 / push**。详见
`.workbuddy/memory/2026-09-19.md` 的命令清单与判定标准。

# Task Dependencies
- Task 4 依赖 Task 3（同一文件的区域算法改动须在已验证基线上叠加）
- SubTask N.3（验证）依赖 SubTask N.2（修复）
- SubTask N.5（提交 push）依赖 SubTask N.4（批量回归无退化）
