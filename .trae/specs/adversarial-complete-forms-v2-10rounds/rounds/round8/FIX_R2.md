# Round 8 打回复整改批 FIX_R2（任务「残余破口清零冲刺」·整改批收尾续作二）

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md 理论基准 I 全部 + II.7）
- 被整改对象：REVIEW2.md（任务 8.3 独立评审）§0 终判打回的 **4 族 5 形态域内缺口**
- 整改基线 → 终态：`49603022`（评审提交）→ `6c4468ef`（修复批提交）；累计 diff = `git diff 49603022..HEAD -- core/`（3 文件 +676/−42：pattern_parser.py +29、region_analyzer.py +378、region_ast_generator.py +311；**零插桩、零 print、G3 违禁前缀零命中**）
- 判据唯一：`scripts/pyc_verify.py`（RV2 口径 = 先 regen 后 verify）
- 证据前缀：`r8v8fixB_repro_r2*`（修复批两前任段）+ 本续作新增 `r8v8fixB_regress_round2face_r2a/_r2b.json`、`r8v8fixB_r2_34set_shard0.json`；评审证据 `r8v8rev_*` 引用不覆盖（tracked 原件在本续作复跑后已 `git checkout --` 还原）
- 纪律：无新算法修复（本批只跑门禁 + 写文档）；零 git commit/push；命令 ≤300s（round2face 全量超限被硬杀后改用驱动内建 a/b 半片纪律分跑）；regen 副作用（M 态 `*OK.py`）结束时 `git checkout --` 全部还原

---

## §0 整改成果表（打回 5 项 → after 读数）

| # | 打回项（机制引用 = REVIEW2.md §0 同号行） | 违反条款 | after 读数（证据） |
|---|------------------------------------------|---------|-------------------|
| 1 | **B104-R2a**（while 头链+and 混合形折叠：`while 0 < x < 10 and flag:` 被拆 `if 0<x<10:` + `while flag:` + 幻影 `pass/break`，H5 设计案例同形复发） | C2/C3 + I.3 推论 + I.2 | `r8v8rev_b104_chain4_battery` **6/6**（v2 复活；v1/v3/v4/v5 维持）——`r8v8fixB_repro_r2variant.json` |
| 2 | **B104-R2b**（while 头 4 元链重检泄漏：`while 0 < x < 10 < x*2 < 100:` 体首幻影 `if 0 < x and 10 < True and x*2 < True`，e04 注册 `10 < True` 折叠常量占位签名） | C1/C2 + I.4-⑤ | 同上 **6/6**（v4 复活；e08×CCMP.m 交集域封闭） |
| 3 | **B105-R2**（嵌套海象深度 2 值链蒸发：`return g((a := h((b := h()))), a + b)` 外层调用+第二实参+return 整体蒸发） | C1 + I.3 推论 | `r8v8rev_b105_walrus_battery` **5/5**（v2 复活；v1/v3/v4 维持）——同上 |
| 4 | **B107-R2**（≥3 目标复杂链 + 同块前置普通语句 → 目标 2+ 蒸发：`o.a = p[k] = q.r = v` → 仅 `o.a = v`） | C1 + I.3 推论 | mtarget3 **6/6**、iso **5/5**、iso2 **4/4**（v1/t2/t3/u1/u2 五失败单元全复活）——同上 |
| 5 | **B103-R2**（or 模式+裸名守卫静默丢弃：`case 1\|2\|3 if g:` → `case 1\|2\|3:`，形态敏感的静默语义腐蚀） | C1/C3 + I.2 | `r8v8rev_bmatch_v3` **2/2** + `r8v8rev_bmatch_or3iso` **5/5**（v3/w2/w3 复活；w1 比较形/w4 单字面量维持保真）——同上 |

**读数与声称对照**：5 项打回失败单元全复活、原登记探针全维持（`r2fix_b104/b105/b107`：B104_main 14/14、B105_main 13/13、B105_call 12/12、B107_main 14/14、B99_min 9/9、B108_main 14/14）；变体负对照（b105::v3 `a = b = f()`）维持 PASS。

---

## §1 B104-R2a：while 头链式比较 + and 尾/首混合条件协议吸收（识别层 + 生成层）

**根因一句话**：`while <cc 链> and <尾>:` 的前置链段经「透明 JUMP_FORWARD 桥 + 共享清理块」收敛入 and 尾块，条件块搜索只认领尾块（header 直接前驱），链段未被循环归属 ⇒ 被 `_identify_chained_compare_regions` 抢占为 IfRegion（then=尾块），循环头折叠为 `if <链>: while <尾>:`（REVIEW2 §4.4 机制补充所指「链头唯一归属未达真链头/条件链整体」）。

**守卫设计**（识别层 `RegionAnalyzer`，判据全为块末 opcode + 跳转目标集合同一性 + 栈净效应 + 区域成员关系，**I.4 白名单五项之外无他**；外层 if 一次性守卫与循环条件操作数的判别元 = rotate-while 回边重检副本存在性，**I.3 协议判据**非模式匹配）：

- `_b104r2_absorb_mixed_cc_chain`（仅 WHILE_LOOP ∧ condition_block 已由块前驱搜索找到 ∧ 非 while-true 时调用；未命中返回 None，调用方行为逐位不变 = C3 封闭）：(a) 尾块前驱经透明 JUMP_FORWARD 桥（桥内全为无条件跳转/噪声/POP_TOP）到达链末段；(b) 链末段以 FORWARD 条件/短路跳转收尾、fall-through 即桥；(c) 自链末段按链协议逐段回溯（前驱 P 以 FORWARD 条件/短路跳转收尾 ∧ P 跳转目标 == 当前段跳出目标，或经纯清理块桥接）至真链头（`_is_chained_compare_header`，COPY(2)+COMPARE 对）；(d) 全链段失败边收敛同一循环出口（或经纯清理块/等价平凡出口，and 失败路径同一性）；(e) 回边重检副本存在性 `_b104r2_has_recheck_mirror`（`_b104r2_cond_eval_seq` 条件求值段 opcode 序同一 + `_b104r2_cond_jump_exits_loop` 失败边收敛，指令级）；(f) and 尾操作数逐块回溯吸收（fall-through 续接 + 共享失败出口 + 副本存在，多操作数尾同判）。
- `_b104r2_absorb_leading_and_operands`（while-true cc 回溯命中后调用，镜像序 `while <a> and <cc 链>:`）：候选 P 以 FORWARD 条件/短路跳转收尾 ∧ P 跳转目标 == 链末段跳出目标（同一循环出口）∧ 链头 ∈ P 后继集（fall-through 续接）∧ 回边重检副本存在；逐前驱回溯吸收多操作数，**终止性由 `_seen` 有限集保证（无计数上限，G4 合规）**。
- 命中后链段/桥/尾/首操作数块整体并入 LoopRegion（每块唯一归属，C2），`condition_block` 改指真链头、metadata 记尾/首操作数块、`region.entry` = 首操作数块（原则 4 入口引用语义）。

**AST 生成侧**（`_loop_generate_while` cc 分支消费 metadata）：`_b104r2_cond_expr_from_operand_block` 取操作数块「条件求值段」（块内 opcode 序 + 栈净效应，前缀语句按栈深回零点剥离——与识别侧 `_b104r2_cond_eval_seq` 同判据）经 expr_reconstructor 重建，按块序组合 `ast.BoolOp(And, [首操作数..., Compare, 尾操作数...])`；极性按跳转极性定否（IF_FALSE 族原样 / IF_TRUE、NONE 族取 not，[R38] 同族口径）；首操作数块承载的循环前置语句按源序提入 pre_stmts；尾/首/桥块标记已生成（防游离发射）。

**落地锚点**（全部 grep 标记核验在树）：

- region_analyzer.py:**4270** `_b104r2_cond_eval_seq`（六项 docstring+C 条款齐全）、**:4304** `_b104r2_is_cleanup_to`、**:4329** `_b104r2_cond_jump_exits_loop`、**:4350** `_b104r2_has_recheck_mirror`、**:4379** `_b104r2_absorb_mixed_cc_chain`、**:4540** `_b104r2_absorb_leading_and_operands`（六方法 docstring ①-⑥+C1/C2/C3 逐条与代码一致，I.7 实测过）
- region_analyzer.py:**4790-4792**（`_cc_mixed_tail_blocks`/`_cc_mixed_lead_blocks` 初始化）、**:4948-4960**（首操作数吸收调用点）、**:5244-5254**（混合吸收调用点：命中后 claim/chain/ops/tails 写入 + `condition_block = head` + `is_while_true = False`）、**:5389-5400**（metadata `cc_mixed_cond_tail_blocks`/`cc_mixed_cond_lead_blocks` + `region.entry = 首操作数块`）
- region_ast_generator.py:**6827** `_b104r2_cond_expr_from_operand_block`（新方法，识别条件/归约方式/AST 映射 + I.4 白名单 docstring）、**:8009-8034**（cc 分支 metadata 消费 + BoolOp 组合 :8020-8022 + 尾/首块标记已生成 + 首块前置语句提入 pre_stmts :8031-8034）、**:8061-8072**（后继守卫放宽至 back_edge_block——回边重检透明连接块）、**:8098-8104**（混合条件回边重检与体语句同块时以「条件求值段 opcode 序同一性」判 `_ps_ops_r2a` 镜像命中）

**I.7 注释合规**：宿主 `_loop_generate_while`（region_ast_generator.py:6876）**无 docstring = 存量状态**（5f784272 即无；REVIEW2 §1.5 已按「存量 + 既有 hunk 注释口径」登记）——本批新守卫行为由 hunk 内联注释块承载（:7996-7998、:8026-8030、:8061-8064 等），**登记维持，非本轮引入失同步**；六个识别层新方法 + `_b104r2_cond_expr_from_operand_block` docstring 合规实测过。

---

## §2 B104-R2b：链式比较回边重检段白名单完备化（4+ 元链 True 占位泄漏）

**根因一句话**：[B104-H4] 重检/清栈抑制的两处固定 opcode 元组只覆盖 3 元链的「装载+协议」段，4+ 元链/调用/算术操作数（`x*2` = BINARY_OP、`f(y)` = CALL、`len(y)` = PRECALL+CALL）的重检段含操作数计算 opcode 不在集合内 ⇒ 未被抑制的中间段被生成层以折叠常量占位重建为体首幻影 `if 0 < x and 10 < True and x*2 < True`（e04 注册占位签名逐字复发）。

**守卫设计**（生成层，判据 = **块内 opcode 序 + 跳转目标块指令序 + 区域成员关系**，I.4 白名单；对任意链长/任意操作数表达式形态同判，I.3 协议判据）：

- 新常量 `_B104_CC_RECHECK_EVAL_OPS`（纯值求值段 opcode 集）：覆盖全部表达式求值 opcode（装载/COPY/SWAP/比较协议/二元一元/下标切片/构造器/PRECALL+CALL 族/KW_NAMES/FORMAT_VALUE/噪声）；**语句副作用 opcode（STORE_*/DELETE_*/RETURN_*/IMPORT_*/异常帧/跳转控制/UNPACK_*）不在集合内 ⇒ 含用户语句的块不命中**（块内 opcode 序判据的封闭性）。
- 两处替换：(i) back_edge 纯重检块（`_b is region.back_edge_block` 分支）；(ii) 纯重检链段（非回边块，条件跳出目标为纯协议清理块 POP_TOP/JUMP 序列或直接越体）——`10 < True` 幻影 if 的复发点即 (ii)。
- 噪声集补 JUMP_FORWARD/JUMP_ABSOLUTE（链+and 尾混合条件的回边重检清理块 `[POP_TOP; JUMP_FORWARD→循环出口]` 位形）；JUMP_BACKWARD 仍在集外 ⇒ continue 语句块不命中（越体守卫不变）。
- [B104-R2] 回边重检与体语句同块的「多语句前缀」切分：原实现把「最后 STORE 之前」整段交单次 `_build_store_statement`，体重含 2+ 条语句（`x += 1; n += 1`）时除末条外整体蒸发；改按 STORE 边界分段（UNPACK_SEQUENCE/UNPACK_EX 组整段保持、UNPACK_EX oparg 位域解码），每段独立重建。判据 = 块内 opcode 序的 STORE 边界（I.4 白名单）；**单语句位形分段结果与原整段逐位一致**。

**落地锚点**：region_ast_generator.py:**242**（`_B104_CC_RECHECK_EVAL_OPS` 常量 + 协议注释块 :229-241）、**:8159-8171**（back_edge 白名单替换 (i)）、**:8180-8200**（清理出口中间段白名单替换 (ii)）、**:8065-8067**（噪声集补 JUMP_FORWARD/JUMP_ABSOLUTE）、**:8116-8135**（多语句前缀 STORE 边界切分 `_store_segs_b104r2`）。

**I.7 注释合规**：宿主 `_loop_generate_while` 无 docstring = 存量（同 §1 登记维持）；白名单/切分行为由各 hunk 内联注释块（:8159-8164、:8180-8186、:8110-8115）承载，判据声明与代码一致。

---

## §3 B105-R2：海象净栈深模拟完备化（嵌套海象值链蒸发）

**根因一句话**：[B105-H2/H3] 净栈深模拟按 `stmt_instrs`（自上次刷出以来的累积段）求和，但累积段过滤了 PUSH_NULL（SKIP_OPS），而 CALL 的 stack_effect 已按 3.11 空槽调用约定把 NULL 弹栈计入（-1）——漏计使深度系统性低估 = 块内调用条数；单层实参位（e06_call_arg 块内无调用）恰零差通过，嵌套海象（`g((a := h((b := h()))), a + b)` 块内三处调用 → 差 3）使外层 COPY(1)+STORE 对的判据 ③ 误判为 0 ⇒ 误切分 ⇒ 外层调用 + 第二实参 + return 整体蒸发。

**守卫设计**（判据 = **块内 opcode 序 + CPython 值栈净效应**，I.4 白名单；不读名字/常量/偏移，I.3）：

- 净栈深改按**本块指令前缀**逐条 stack_effect 求和：绝对栈深、含 PUSH_NULL；基本块无内部跳转，前缀求和即该指令处真值栈深；前置语句净效应归零不干扰（教科书「深层才错」的推论封口——判据对任意嵌套深度同判，非深度枚举）。
- 前缀不可得（`block.instructions.index(instr)` 抛 ValueError）时**回退原累积段模拟，行为逐位不变（C3 封闭）**。

**落地锚点**：region_ast_generator.py:**56955-56970**（[B105-R2] 根因/判据注释块）、**:56971-56992**（前缀求和实现 :56973-56985 + ValueError 回退 :56976/:56986-56992；判据 ③ 消费点 `not _b105_next_is_store and _b105_depth_ok and _b105_depth > 0` 维持不变）。

**I.7 注释合规**：宿主 `_generate_block_statements_body`（:53198，**I.7 强制类 `_generate_*`**）存量六项 docstring + C1/C2/C3 保持、与代码一致；**但 B105-R2 子守卫未扩充进 docstring**（② 归约顺序只列既有跨块守卫 [B31]/[R2-SWAP]/[B34c]/GET_ITER/[W22]，未列 [B105] 海象值链判据与本次完备化）——新行为由内联 [B105-R2] 注释块完整承载（:56955-56970 判据+协议+回退逐条与代码一致）。**勘误登记：docstring 六项为方法整体协议描述、无失实陈述；子守卫层注释合规、docstring 未同步扩充 = 按 `_loop_generate_while` 存量口径同类登记**（非强制类失实，非打回事由；建议后续批次在 ② 中补 [B105] 条目）。

---

## §4 B107-R2：链式复杂目标段深度不变式修正（交错 COPY 协议）

**根因一句话**：段数一致性判据「段后深度 == 剩余段数」按「COPY×(N-1) 连续堆叠 + 每段净 -1」立式，而 CPython 3.11 链式复杂目标协议为**交错 COPY 布局**（每非末段自带前置 COPY 1、末段无 COPY 消费原值）——2 目标链两种读法同值恰通过（评审前登记探针全为 2 目标），3+ 目标第 1 段后实际深度 = 1 ≠ 剩余段数（2+）⇒ 判据恒不中 ⇒ 整链验证失败回退单目标路径 ⇒ 目标 2+ 整体蒸发；同块前置普通语句由既有值段边界判据（首个复杂 STORE 前最后一条后继非 STORE_* 的 COPY(1)，排除 walrus 副作用对 COPY(1)+STORE_*）剥离，新不变式下随段验证通过而整体认领。

**守卫设计**（判据 = **块内 opcode 序 + CPython 值栈净效应**，I.4 白名单；不变式为协议代数性质，对任意目标数同判，I.3）：

- 正确不变式：**非末段 STORE 后深度 == 1**（段内 COPY 份额被本段 STORE 消费，栈上仅剩供末段消费的原值份额）；**末段后 == 0**（原值份额被末段消费，全链栈归零）。2 目标链在新不变式下逐位同判（seg1 后 == 1 == 原判据剩余段数 1；seg2 后 == 0）⇒ 既有 2 目标读数零扰动。
- C3 同步收紧：任一判据不满足（**末段后深度非零、非末段段后深度 != 1**、复杂 STORE 数 < 2、值段重建失败）返回 None 交回既有单目标路径。

**落地锚点**：region_ast_generator.py:**58921-58936**（docstring ① 交错 COPY 布局修订 + ③ 不变式修订）、**:58951-58953**（C3 修订）、**:59004-59016**（[B107-R2] 根因/不变式注释块）、**:59024-59025**（`_b107_expected = (0 if 末段 else 1)` 实现）。

**I.7 注释合规**：`_build_chained_complex_target_assign`（:58918）docstring **已随新不变式同步修订**（①③+C3 三处，修订后判据陈述与代码逐条一致）——本批 I.7 正面合规样例 ✓。

---

## §5 B103-R2：or 模式守卫块 POP_TOP 丢弃段剥离（形态敏感修复）

**根因一句话**：`_collect_pattern_blocks` 的单守卫块判据「首条 meaningful ∈ LOAD_VAR_OPS」对守卫表达式形态敏感——or 模式成功点（S 块）位形下守卫块 = `POP_TOP; LOAD g; POP_JUMP_*_IF_FALSE → 下一 case`（前导 POP_TOP 是 or 臂链协议对主体副本的丢弃，与 `_extract_case_pattern` 的通配丢弃同一栈协议），单字面量 `case 1 if g:` 无 S 点、守卫块以 LOAD 起始恰通过 ⇒ or+裸名守卫块不被收集 ⇒ 守卫静默丢弃（`case 1|2|3 if g:` → `case 1|2|3:`）；而守卫 fail 边（POP_JUMP_*_IF_FALSE → 下一 case）对两种形态结构同一 = 模式匹配非协议判据（I.2）。

**守卫设计**（判据 = **块内 opcode 序 + 跳转目标**，I.4 白名单；协议完备化，I.3）：

- 剥离前导 POP_TOP 丢弃段（`_b103r2_guard_ops = meaningful` 去头部 POP_TOP 链）后再按真值守卫臂形态判定：首条 ∈ LOAD_VAR_OPS ∧ 末条 ∈ POP_JUMP 族（FORWARD_IF_FALSE/IF_FALSE/FORWARD_IF_TRUE/IF_TRUE + NONE_JUMP_OPS）∧ middle 全 POP_TOP 或空。
- 丢弃段只能是 POP_TOP 序列的协议保证：守卫在基本块首个条件跳转处终结，体语句不可能位于守卫块内。
- 跳转目标纪律不变：`_simple_guard_jump_target >= jump_target_offset`（指向下一 case/after-match，与 body 内 if 区分）。

**落地锚点**：pattern_parser.py:**251-261**（[B103-R2] S 点位形/协议/判据注释块）、**:265-268**（POP_TOP 丢弃段剥离循环）、**:269-277**（判据重写：`_b103r2_guard_ops` 首末/middle/jump target 消费——命中后进入既有 guard 收集路径，宿主 `_collect_pattern_blocks` :108）。

**I.7 注释合规**：宿主 `_collect_pattern_blocks`（pattern_parser.py:108）为**存量单行 docstring**（「收集case体内的模式匹配块（排除pattern continuation）」），本 hunk 未扩充该 docstring——新守卫行为由内联注释块承载（:251-261 判据+协议与代码一致）。**勘误登记：docstring 未同步扩充（非强制类方法；单行存量 docstring 无失实陈述，注释块合规）——建议后续批次扩充**；比较形守卫收集（`has_compare_and_jump` 分支）不受本 hunk 影响（实测 or3iso w1 维持保真）。

---

## §6 批量门禁读数

### 6.1 攻击面 31 探针（对 rev2B/rev2C 基线逐位核对；前任段证据，本续作逐条通读引用）

| 半 | 证据 | 读数 | 对照 |
|----|------|------|------|
| 位B 域 16 项 | `r8v8fixB_repro_r2fixallB.json` | B108 14/14、B99 9/9、B104_main 14/14、B105_main 13/13、B105_call 12/12、B107_main 14/14、B111 28/28+22/22、B83 2/2 全绿；B98_matrix 7/15、B98_hosts 13/18、B98_resid 2/5、B78 1/4、B79 3/4、B80 2/3、B82 2/3 | = REVIEW2 §2 rev2B 逐位一致；**WORSE=NONE**（移交项失败单元名单逐位同） |
| 位C 域 14 项 | `r8v8fixB_repro_r2fixallC.json` | B77 8/8、B81 4/4、B103 13/13+8/8、B102 13/13+8/8+10/10、B113 9/9+14/14、B96 13/13、B106 13/13+13/13+27/27 全绿；B112 21/24（e05/e07/e07.\<listcomp\> 三移交单元） | = REVIEW2 §2 rev2C 逐位一致；**WORSE=NONE** |

### 6.2 变体电池（打回探针复活读数；前任段证据）

`r8v8fixB_repro_r2variant.json`：b104_chain4 **6/6**（v2 折叠 + v4 重检泄漏双复活）、b105_walrus **5/5**（v2 嵌套海象复活）、b107_mtarget3 **6/6**、b107_iso **5/5**、b107_iso2 **4/4**（五蒸发单元全复活）、bmatch_v3 **2/2**、bmatch_or3iso **5/5**（v3/w2/w3 or+裸名守卫复活，w1/w4 保真维持）。

### 6.3 站桩 3 面（本续作实测；`r8v8fixB_station.py`，RV2 先 regen 后 verify）

| 面 | 实测 | 预期 | 判定 |
|----|------|------|------|
| quotation | **152/153**，唯一失败 `change_his_to_forward` | 152/153 | ✓（重跑 JSON 与 tracked 证据字节级相同） |
| round1face | **417/423**（24 文件：trade_info_utils 36/41 五基线存量 + quotation 面；其余 22 文件全绿） | 417/423 | ✓（同上字节级相同） |
| round2face | **239/251**（a 半 141/141 全绿 + b 半 98/110；失败 = v_b46 1/4、v_b71 3/4、v_b73 2/3、v_b75 2/3 + email_utils 3/4、cgroup_utils 7/8、executor 9/10、strategy_universe 10/11、trading_dates_mixin 13/14、realtime_event_source 12/13；v_b74 4/4、rvC_v2 2/2 维持） | 239/251 | ✓（失败名单与 REVIEW2 §2 逐位一致；全量超 300s 被 shell 硬杀且 dump 未写盘，改用驱动内建 a/b 半片分跑后合计，半片证据 = `r8v8fixB_regress_round2face_r2a/_r2b.json`，tracked 原 45 文件全量证据已还原未覆盖） |

### 6.4 34 集分片 0（本续作实测；`r8v8rev_34set.py 0 8`，5 文件 190 单元）

**183/190 = 基线 `r8v8rev_34set_shard0.json`（评审批次实测）逐位一致**：per-file units_success/units_total 全等、failures 单元集合逐文件全等（email_utils 3/4、strategy_universe 10/11、wizard_quant_api 55/58、finance 31/32、bar 84/85）、pyc_sha 逐文件全等、**NEWFAIL = 0**；regen index 内容相同（仅换行符 CRLF/LF 差异）。本续作证据 = `r8v8fixB_r2_34set_shard0.json`（副本落盘，tracked 评审证据两件复跑后已 `git checkout --` 还原）。

### 6.5 IV.2 合规自检（本续作实测）

| 项 | 实测 | 判定 |
|----|------|------|
| py_compile（pattern_parser/region_analyzer/region_ast_generator） | rc=0 | ✓ |
| import（三模块） | OK | ✓ |
| BOM | region_analyzer.py 首 3 字节 `efbbbf` ×计数 1（单头）；region_ast_generator.py 同（单头）；pattern_parser.py **无 BOM**（首 3 字节 = `"""`，计数 0）——**存量状态如实记录**：49603022 与 5f784272 两基线经 `git show` 原始字节核验均无 BOM，非本轮引入 | ✓ |
| 新增行 print( | `git diff 49603022..HEAD -- core/ \| Select-String "^\+.*print\("` = **0 命中** | ✓ |
| G3 违禁前缀 | `^\+.*def (_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)` = **0 命中**；新增 def 7 个全为 `_b104r2_*` 族（:4270/:4304/:4329/:4350/:4379/:4540 region_analyzer + :6827 region_ast_generator） | ✓ |
| G4 硬编码深度/计数上限 | 逐 hunk 肉眼扫新增 544 行：数值字面量仅循环初始化/插入索引（`depth = 0`、`start = 0`、`insert(0, …)`、`segments[-1]`、UNPACK_EX oparg 位域解码）与不变式常数（非末段 == 1/末段 == 0，协议不变式非上限）；回溯环终止性全由 `_seen` 有限集保证（注释明示「无计数上限」）；**零新增深度/计数上限**；存量 `_steps < 8` 三处（region_ast_generator.py:28214/:28384/:34954）与本批 diff 无交（行号自 :28019/:28189/:34759 正向单调漂移 +195 系上方插入所致） | ✓ |

---

## §7 「代码已落地」声明（I.6 逐项锚点清单）+ 未竟登记

### 7.1 I.6 落地锚点清单（全部 grep 标记核验在树，HEAD = 6c4468ef）

| 项 | 锚点（file:line） |
|----|------------------|
| B104-R2a 识别层六方法 | core/cfg/region_analyzer.py:4270、:4304、:4329、:4350、:4379、:4540 |
| B104-R2a 调用点（首操作数吸收 / 混合吸收） | region_analyzer.py:4957-4958、:5246-5247（命中消费 :5249-5254） |
| B104-R2a metadata/entry | region_analyzer.py:5395、:5397、:5400 |
| B104-R2a 初始化 | region_analyzer.py:4791-4792 |
| B104-R2a 生成层（操作数表达式重建 / BoolOp 组合 / 前置语句提入 / 后继守卫放宽 / 重检镜像判定） | core/cfg/region_ast_generator.py:6827、:8020-8022、:8031-8034、:8071、:8098-8104 |
| B104-R2b 纯值求值白名单（常量 / back_edge / 清理出口中间段 / 噪声集 / 多语句切分） | region_ast_generator.py:242、:8166、:8198、:8065-8067、:8116-8135 |
| B105-R2 净栈深前缀求和（+回退） | region_ast_generator.py:56973-56992（注释块 :56955-56970） |
| B107-R2 交错 COPY 不变式（docstring ①③/C3/注释块/实现） | region_ast_generator.py:58921-58936、:58951-58953、:59004-59016、:59024-59025 |
| B103-R2 POP_TOP 丢弃段剥离（注释块/剥离/判据消费） | core/cfg/pattern_parser.py:251-261、:265-268、:269-277 |

**声明**：上表与 §1-§5 所引全部锚点为真实代码位置（非设计愿望）；diff 零插桩、零 print 残留、BOM 单头维持（pattern_parser 无 BOM 为存量如实记录）。

### 7.2 I.7 注释合规汇总（docstring 与新守卫行为同步性）

| 触及方法 | docstring 状态 | 判定 |
|---------|----------------|------|
| `_build_chained_complex_target_assign`（region_ast_generator.py:58918） | ①③+C3 已随 [B107-R2] 同步修订，与代码逐条一致 | ✓ 正面合规 |
| `_b104r2_*` 六方法（region_analyzer.py:4270-4540）+ `_b104r2_cond_expr_from_operand_block`（:6827） | 新增方法 docstring 六项/紧凑判据 + C1/C2/C3 齐全 | ✓ 正面合规 |
| `_loop_generate_while`（:6876） | 无 docstring = **存量**（5f784272 即无，REVIEW2 §1.5 既有口径）；本批行为由 hunk 注释块承载 | 登记维持 |
| `_generate_block_statements_body`（:53198，I.7 强制类） | 存量六项保持；[B105-R2] 子守卫未扩充进 docstring（内联注释块 :56955-56970 承载） | **勘误登记**（无失实，建议后续补 [B105] 条目） |
| `_collect_pattern_blocks`（pattern_parser.py:108） | 存量单行 docstring 未随 hunk 扩充（内联注释块 :251-261 承载） | **勘误登记**（非强制类，建议后续扩充） |

### 7.3 未竟登记（维持移交/登记原判，本批零处置变更）

1. **B122 候选维持域外移交**：字面量 case 臂内嵌套 match 挂死/0 字节崩溃（REVIEW2 §4.1；5f784272 同挂 = 存量缺陷非本轮引入；判据方向 = 内层 match 认领以 case 体块集为 L(A) 上界，[B17] 同构）。
2. **B112 三单元移交维持**（e05 yield await / e07 async 闭包推导式 / e07.\<listcomp\>）：根因 = [Round6-B31] await 挂起协议链消费门 + ExpressionReconstructor 平铺重建，均在整改授权文件外（REVIEW2 §5）；本批读数 21/24 与登记残余逐位一致、零恶化。
3. **8 项移交维持**（B78/B79/B80/B82-v_swap/B98-R2/B98-R3/B44 + B112 上项）：REVIEW2 §5 复核 8/8 成立（判据方向在授权文件外/需跨层协同 + 单侧方案已实测排除）；本批 r2fixallB 半中各移交探针失败单元名单逐位同基线、零恶化。
4. **G4 `_steps < 8` 存量登记维持**：REVIEW2 §1.3/§4.2 判定（[B75] 存量同型镜像声明属实、保守回退不产错误发射）；建议后续批次统一改 visited-set（与 B102/B103 `_seen` 口径对齐）——本批 diff 未触及该三处（§6.5 G4 行），建议维持。

### 7.4 产出物与纪律声明

- 本报告：`rounds/round8/FIX_R2.md`。
- 本续作新增证据：`r8v8fixB_regress_round2face_r2a.json`/`_r2b.json`（round2face 半片）、`r8v8fixB_r2_34set_shard0.json`（34 集分片 0 复跑副本）；quotation/round1face 复跑与 tracked 证据字节级相同（JSON 未变 M 态）。
- 前任段在途证据（引用）：`r8v8fixB_repro_r2variant.json`、`r8v8fixB_repro_r2fixallB.json`、`r8v8fixB_repro_r2fixallC.json`、`r8v8fixB_r2variant.py`（驱动）。
- 纪律：零 git commit/push；无新算法修改；探针不新建；round2face 全量超时按驱动内建 a/b 半片纪律分跑；tracked 评审证据（r8v8rev_34set_shard0(+_index)、r8v8fixB_regress_round2face）复跑后 `git checkout --` 还原未覆盖；regen M 态 `*OK.py`（`git status --short` 所列全量）结束时 `git checkout --` 还原。
