# Round 10 门禁验证与终态台账（region-reduction-v3-full-corpus-100pct-10rounds）

封表口径：唯一判据 `scripts/pyc_verify.py`（pylingual `compare_pyc`，本机 CPython 3.11.7 64 位，
**只比较、不产码**，故每项读数都须先按当前字节删除旧产物再 `pycdc.py -o` 重生成）。
本轮所有产物的生成方式一律为流水线上重生成，**未手改任何 `*OK.py`**。

## 一、门禁读数（HEAD 基线 → round10 终态）

| # | 门禁项 | 命令 | HEAD 基线（2026-10-08 02:47 实测，core 为封表字节） | round10 终态 |
|---|---|---|---|---|
| 1 | 全量 402 文件重生成 | `gate_round.py 10 9 --stage regen` | ok=402 bad=0（产率实测空闲约 1.7 s/文件） | ⟨填：ok/bad⟩ |
| 2 | 单元级全量比较 | `--stage verify` + `--stage report` | 6577/6617（99.3955%）、386/402 文件 | ⟨填：单元/文件/四项门禁⟩ |
| 3 | quotation 单验 | `single site-packages/fly/data/quotation.pyc` | 153/153 status=success | ⟨填⟩ |
| 4 | small34 小集 | `batch --index baseline/small34_index.json` | 1528/1568，34 文件中 18 全绿 | ⟨填⟩ |
| 5 | 尺子自检 | `selfcheck` | 153/153 Equal；变异「常量」1/153、「极性」1/153 抓到 | ⟨填⟩ |
| 6 | pytest 七套件 | 六套件 + `tests/test_repo_tool_hygiene.py` | 2 failed / 280 passed / 2 xpassed，二条既有红逐名不变（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`，与 round9 封表同名）| ⟨填：判据为零**新增**失败⟩ |

四项硬门禁（`report` 段打印）：文件级回退=0 ∧ UNIT_REGRESSIONS=0 ∧ 新增失败单元=0 ∧ 翻正单元按**逐单元名单**列名。

## 二、本轮工单台账（每条以字节读数为凭，不以守卫命中为凭）

| 工单 | 机制面 | 终态 | 证据 |
|---|---|---|---|
| #13 / B129 | 「登记块为已生成 ⇔ 语句确被接手」于 `region_ast_generator.py:54896-54921` | **否证并逐字节回滚**（三名工程师 × 三变体：matcher 16/17→16/17，small34 1528→1525/1527，破掉本票自带负对照 `jq_trans_module` 65/65→63/65） | `FIX_B129_LEADING_GUARD_HANDOFF.md`；core 工作树 sha256 与封表一致 |
| #16 / B126 | `while True:` 体内 `if` 被当循环测试、体尾降格成 `while…else` | **判据成立但零翻转 ⇒ 回滚**；补丁归档为它票共要件（电池 26/37→33/37，6 对照不动，但目标单元另带 465/293/3 条省略） | `FIX_B126_WHILE_TRUE_IFJOIN.md`、`ADJUDICATION_R10_B126_REVERTED.md` |
| B128 → B131 | matcher 被吞的 10 条切片测试语句 | **诊断完成**：真实宿主链为 R(entry 1912)，`@2164` 是其 `merge_block`；两条**独立**丢弃通道（`:19324` 认领 + `:54896-54921` 递延无人接手），仅抑制前者产物**逐字节不变**；病根在分析端——R(1912)∩R(2038)={2038,2160} 的幽灵链与 `BlockRole.IF_ELIF_CONDITION` 在 `match` 中命中 0 次（循环先 stamp `LOOP_BODY` + `_assign_region_role` 先写者胜） | `DIAG_B131_ELIF_ARM_DUALROLE.md` 三.1–三.4/五/六 |
| B132 | 同上之**修复**（臂入口身份写回识别阶段 + 禁链块集相交 + 发射端事后认领限于自有块） | ⟨填：补丁是否落地、matcher 是否 17/17、两哨兵读数⟩ | `FIX_B132_ELIF_ROLE_PRIORITY.md`、`D:/Temp/r132/b132.patch` |
| #15 / B127 | 共享隐式尾声 epilogue 未被认成单一落点；以区域成员事实替换 `:51806-51812` 的 `POP_TOP` 巧合支 | ⟨填：`handlers._target` hunks 17→0 与 single 29/30→30/30；负对照 `TWHThreadRotatingFileHandler._target` 须仍 0 hunks⟩ | `FIX_B127_G7_MEMBER.md`、`D:/Temp/r15b/b127.patch` |
| B130 | F1「try/except 之后的顺序续体被让给 handler 尾声」 | **诊断完成且否证本票前提**：`load_daily` 的 `@2478` 实为 try 体内末条语句且是 `IfRegion(cond@740)` 的汇合块，该 if 的 `merge_block` 被解到整个 try 结构之外（`@2768`）；`trade_info_utils.get_trade_status` 的真实缺口是 try 体尾的 `break`/`else: break` 未发射。**两文件机制不同，禁止并案**；另更正 `TryExceptRegion` 根本没有 `merge_block`/`natural_exit` 字段 | `DIAG_B130_POSTTRY_LANDING.md` §1/§1.1/§1.2 |
| #21–#24 | 生成器内下标操作数链 / `order_api` 被吞条件语句与三元操作数链 / 函数内 import 丢失（4 处复制的硬编码前瞻窗）/ f-string 字面碎片拼接外来标识符 | 本轮未派工（各自机制已在 `UNITMAP_R10.md` 具名登记） | 同档 §五–§七 |

## 三、判据纪律（本轮实际执行方式）

1. 零翻转即按**工作树 sha256** 逐字节回滚（不比 blob 哈希——本仓配文本过滤器，blob 与工作树恒不等）。
2. 禁「改松判据换读数」：B122/B123/B129 三次先例均以回滚收束；本轮未放宽 `:38496` parent 守卫。
3. 禁用无判别力计数作证据（「块是区域成员但非 condition」12/13 是正常值）；吞并/错接证据须为
   **身份 ∧ 产物 AST 有无对应语句** 的合取。
4. 复现臂与语料读数冲突时以语料逐单元名单为准，但最小样例若无判别力须如实写明（B131 三.4：
   7 条样例全部 2/2，故本票门禁不含样例）。
5. 产码前先删旧产物（`regen_list.py` 内置），并断言 `ok=402 bad=0`；缺行不当通过。

## 四、Task 11（注释合规终审与台账定稿）本轮状态

- 11.1 注释 vs 代码一致性普查：⟨填：`AUDIT_TASK11_COMMENT_COMPLIANCE.md` 的 census 与 COMMENT_OVERCLAIMS 计数⟩
  本轮坐实一例：`:54913` docstring 自称该守卫「替代此处对条件的静默丢弃」，实测为**注释与行为矛盾**（B129 诊断）。
  另**撤销**一处我先前的错误断言（连同样写进了提交 `274b6a2c`/`110f5236`，以本条为准）：
  `region_ast_generator.py:19316-19323` 的注释「不限于顶级区域」**并非**与行为矛盾——`self.regions` 是
  展平的 45 区域列表，本就含嵌套区域，故该循环覆盖嵌套入口；我此前据此立案是错的。
  还有一条**待裁定**的自相矛盾登记给 B132：`DIAG_B131` §三.3 结论「修复属分析端」与其收尾发现
  「发射端 0 次读 `block_roles` ⇒ 分析端角色修正对产物无效率」互斥，须以 def/use 计数裁定并写回该档 §七。
- 11.2 台账同步：`tools/kb/syntax_coverage.py` 在本工作树实测 **分母 ast 97 + 扩展 31 = 128，分子 128，占比 100.0%**，
  未覆盖清单为空——注意此项是**语法面覆盖**，不是语料反编译成功率，两者禁止混报。
  `tools/kb/check_stale.py` 本工作树实测 `checked=60 stale=41`（此前 10 是拿用户原始 checkout 的 wiki 页比对的假数）。
  同类硬编码 ROOT 已清除 10 处，并落常驻牙 `tests/test_repo_tool_hygiene.py`（已入 checks 段）。
- 11.3 终验与 push：见 §一 与文末提交记录。

## 五、终态与残余（如实上报，10 轮用尽未达 100%）

用户原始要求：每个 `.pyc` 都须反编译成功并在同目录生成同名 `+OK` 的 `.py`。
本轮终态读数：⟨填：单元 x/6617、文件 x/402⟩；未达标文件与单元逐条列于
`residual_report.py` 生成的「文件 × 单元 × 台账机制」表（自带夹钳：八份分片报告不齐即拒绝出表，
任何失败单元在 `UNITMAP_R10.md` 查不到即标 UNREGISTERED 并非零退出）。

HEAD 基线残余（本轮起点）：**16 文件 / 40 单元**，机制分组见 `UNITMAP_R10.md`：
`FINE_LANDING` 20 / `CONTENT_OMISSION` 11 / `CONTENT_MIXED` 4 / `CONTENT_SPREAD` 2 /
`COPY_AMBIG` 2 / `FINE_TRANSPOSED` 1。差 1 单元即可翻正的文件共 8 个：
`handlers` 29/30、`api_base` 27/28、`bar` 84/85、`strategy_universe` 10/11、`strategy` 26/27、
`realtime_event_source` 12/13、`matcher` 16/17、`load_daily` 26/27。

## 六、下一轮（若续）路线

1. B130 否证后应拆成两票：`load_daily` 之「体内 if 的 merge_block 被解到 try 结构之外」，
   与 `trade_info_utils` 之「try 体尾 `break` 未发射」。二者身份判据不同，不得并案。
2. #14 落点面（`bar`/`strategy_universe`/`strategy` 三条 ANCHOR/纯落点）、#15 剩余 8 条、
   #21–#24 四条独立机制仍在册。
3. `r10g7_` 隐式尾声电池读数：⟨填：臂数、复现/对照红绿名单⟩。
