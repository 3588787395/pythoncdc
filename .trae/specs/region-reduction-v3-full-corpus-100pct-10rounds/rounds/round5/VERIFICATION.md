# Round 5 主代理验证序（VERIFICATION）

轮次：rr-v3r05 · Task 6
封表时点：2026-10-07
before = `baseline/shards/shard*_report.json`（units 6554/6617、files 369/402）
after  = `rounds/round5/after/shard*_report.json`（402 产物在本轮终态代码上先删后重生成，8 片 regen failed 合计 0、8 片 verify 全部 rc=0）
判据唯一 `scripts/pyc_verify.py`（ruler sha `9c7567bd6776b36b`、interp 3.11.7 64 位）

## I. 验证序读数

| # | 步骤 | 读数 | 判定 |
|---|------|------|------|
| 1 | 402 八分片 batch + compare（对基线） | units 6554→**6572/6617（99.3199%）**、files 369→**381/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 1b | 对 Round 4 终态增量核对 | units 6571→6572、files 380→381 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 2 | **quotation 单验（本规范点名锚点）** | `site-packages/fly/data/quotation.pyc` **153/153 status=success** | 锚点文件首次整文件 100% ✓（B102 关闭） |
| 3 | tests 六套件 | **277 passed / 2 failed / 2 xpassed**（test_B01 + test_BOUNDARY_02） | 零新增失败 ✓ |
| 4 | IV.2 自检 | IMPORT_OK、compileall rc=0、禁止前缀 0、调试残留 0、硬编码上限 0、两文件各单头 BOM 全 CRLF | 全过 ✓ |
| 5 | 电池（主代理独立复算） | `r1_probe` **108/110**（44/2）、`r1_regress` **34/34**、`r4_probe` **77/87**（40 臂，30 success/10 failure）、`r2v3` **105/126**、`r3` **101/122** | 零绿臂转红 ✓ |

## II. 本轮 7 张工单的成色：2 落地 / 5 整批回滚（这是本轮最重要的管理事实）

**落地 1 —— B116/B99 族（分析端 boolop 链 sink 归属）**：`trading_dates_mixin` 13/14→**14/14**、
`stock_position` 36/37→**37/37**。判据 `_boolop_chain_exits_are_distinct_sinks` + 建区前置第三不变式门；
决定性探针事实：`if A: if not B: body` 与 `if A and not B: body` 两种源形**编译后逐字节相同**
⇒ 源码形不可辨识，故只能按 sink 归属拆区，不是形态特判。标记 `[R4-B116 sinkexit]`×4（12 True / 72 调用 / 11 通向 7 处翻转）。

**落地 2 —— B119（循环/for-iter 出口 sink 落点）＝本轮关键成果**：`quotation.pyc` 152/153→**153/153**。
判据 `_loop_tail_exit_sink_pair`：函数 CFG 末两块相邻、各为无后继的 `LOAD_CONST None; RETURN_VALUE` 对、
各恰一前驱，且前驱属本区域、其末 opcode 为条件跳转/FOR_ITER 且该边离开本区域、至少一条边来自 LoopRegion 角色块
⇒ 两块是**逐边落点**而非语句，均不得材料化（材料化任一即并边＝B99 −2，或换序＝B102 的 268/272 互换）。
标记 `[R5-B119 loopsink]`×3；9 次 True → 1 单元 + 1 臂翻转；**变形反证**：关掉守卫即落回并冒出多余 `return None`，
对照组命中 0 ⇒ 判据承重。逐指令复核 orig=203 cand=203 posdiff=0 equal=True。

**5 张回滚票（全部「命中但未翻转」当场否决，零残留）**——本簇连续六票零翻转后的轴切换记录：

| 工单 | 攻击面 | 实测 |
|------|--------|------|
| B99（生成端消费点） | 删死计数器换 3 个区域局部消费点 | 633 调用 / 12 True / **0 翻转** ⇒ 回滚；换来关键结论：归并发生在**分析端** |
| B100/B110 汇合同一性 | 分析端条件(6)「仅可经 J 到达」＋生成端 B108 拆分子句 | +0 命中→0；4 命中→0 ⇒ 双双删除 |
| or-run 完整性 | 链式比较双腿并入同一元操作（抑制 `[R64-diag1] chain.pop()`）＋三处同事实补丁 | or-run 完整（merge 564→612、R14c 取反消失）但 **0 翻转** ⇒ 回滚，配方留档 |
| or-run＋elif 宿主 / 父边级联 | α `_boolop_run_terminal_member`；后续 `_membership_enclosing_region` | S1 −102→−4、S2 −387（闭包误播宿主条件块）、S3/S4 −17 但兄弟臂塌成 pass；父边票 9 次重挂 / **0 翻转**；v1 曾**重新打开一个绿单元**（r1_42 8/8→7/8）当场拦下 |
| LoopRegion exit 交付 | 主代理提出的 `exit=` 未交付假设 | **被实测否证**：`Region.exit` 在生成端**零消费者**，补交付后全局读数一字不变 ⇒ 死假设，后续不得再提 |

轴切换的回报：if/elif 汇合簇六票零翻转后，第 7 票改打**从未碰过**的「相邻隐式 None 出口 sink 归属」轴，
一击翻转本规范点名锚点。⇒ 残差收窄（−102→−4）买到的是信息而非进度；对同一轴的第 3 次零翻转应作为换轴阈值。

## III. 流程与工具事实（本轮新增）

1. **`split_verify.py` 上岗**：分片 2/3/4 等分合规拆跑（每跑 <280s）→ 合并 rows → 断言 files/rows 与分片索引等量再写 `shardN_report.json`，报告内记 `merged_from`/`split_reason`。
2. **守卫在真实事故中生效**：`driver.py verify` 的「先删旧报告、跑完无新报告即 fatal」本轮挡住两次——
   一次 rc=TIMEOUT（shard5 首跑），一次是我自己的命令外层 `timeout 100` 小于工具内部 290s 上限，
   逐片被杀且**未留下任何**可读文件，避免了把上一轮报告当本轮读数。教训归位：外层预算必须大于被包产物的内部上限，
   该报错是生产者的缺席证明，不是结果。
3. **并发纪律**：本轮两次自造争用（同时跑两条自有 gate 链、又叠等待任务），使多片超 290s；改为单链串行后
   8 片 regen + 8 片 verify 全部 rc=0。机器上另有**并行会话**（v2 round7 脚本、`pytest new_tests`、跑在 F: 的 pyc_verify），争用为外部既有条件。
4. `quotation` 153/153 与 handlers 29/30 的差别由 B119 工单实测给出：handlers 的 off404/off408 **不是**末两块相邻对，
   还需第二条机制（merge 412 重判为 else 入口），故 **B99 仍未闭**、r1_73 亦确认为另一面（else 体 blk54 被 LoopRegion@18 认领而其前驱 24 ∈ TryExceptRegion@24）。

## IV. 轮门禁判定

- ≥1 个语料 pyc 由 failure 转 success：**quotation.pyc 153/153**（本规范点名锚点，同目录 `+OK.py` 由 pycdc 重生成、153 单元全 Equal）✓
- 全量单元读数净增：6571 → 6572（对基线 +18）✓
- `REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`（对基线与对 Round 4 终态双向）✓
- 产物零手改（先删后重生成，402/402 成功）✓；每条命令 ≤300s（超者已按分片拆分）✓；派发子代理前均有本地提交 ✓
- 已 push `origin/rr-v3-full-corpus`（`579f0dc1..81c284aa` 起，本轮各提交逐一上链）✓
- **Round 5 判定：通过，可开启 Round 6**

## V. 语料残局（21 文件 / 45 单元）与移交

未闭实名：**A 族 7 文件**（strategy 26/27、api_base 27/28、matcher 16/17、bar 84/85、function 70/71、load_daily 26/27、finance 31/32）
——已推进到「区域树父子边 + 级联裁决」层，下一最窄残差＝`region_analyzer.py:31534` 的
`len(_loop_cands) >= 2` 类型优先级级联把认领臂的 IfRegion 丢弃；
**B117 内吞 2 文件**（realtime_event_source 12/13 —— B119 票测得该形需第 4 处正交改动：AND 腿语句 `debug('获取重登信号量')` 被吞；profiler_func 17/18 —— or-extension 分支 0 次调用，另站点）；
**B99 残** handlers 29/30（需 merge 412 重判 else 入口）；**B111 轴** quote_handler 78/79；**未归族** flytools 65/66（唯一分歧为 prod off700 单条 NOP）；
大户：trade_live_broker 118/128、quote 86/92、trade_info_utils 37/41、klinedata 61/64、wizard_quant_api 55/58、real_quote 43/45、risk_calculation 41/43、order_api 35/37；
在册未动：B101（合成线索，禁止据此改判据）、B114、B110 残臂、r1_73（try-else 认领面）。
