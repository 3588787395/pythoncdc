# Round 8 修复批 位B续作（发射域）修复报告（任务 8.2 · 批次二·续）

- 修复工程师子代理（位B续作·发射/装配域；前任位A/位B两批已完成并提交，HEAD=8f528733 承接）
- 工作树：`F:\Downloads\pythoncdc-main`（win32 / PowerShell 5.1 / python 3.11）
- 涉改文件边界遵守声明：`core/cfg/region_ast_generator.py`（发射/装配域）+ `core/cfg/ast_generator_v2.py`（表达式重建）+ `core/cfg/region_analyzer.py`（仅 B77/B78 判据族确需识别层协同时，锚 `_is_ternary_block`/`_identify_ternary_regions`；位A B121/B109 守卫未动）；禁改 pattern_parser.py / exception_handler.py / comprehension_generator.py / code_generator.py / ast_converter.py（位C域）
- 判据唯一：`scripts/pyc_verify.py`（ruler = pylingual equivalence_check；读数全部 RV2 口径 = 先 regen（pycdc -o）后 verify）
- 证据前缀：`r8v8fixB_*`（`rounds/round8/`）
- 零 git 写操作；探针 .py 源/pyc 零改动；regen 副作用结束时统一 `git checkout --` 还原

---

## §0 修复成果总览（增量维护，配额中断防丢）

| 序 | 族 | 探针 | before（after_b108_del 基线） | after | 状态 |
|----|----|------|------------------------------|-------|------|
| 0a | **B108**（try-finally-only finally 体复制/`del` 蒸发） | B108_main（c4_06） | 12/14 → **14/14**（前任位B落地；本批复验维持 + docstring 合规补正） | 14/14 | 封闭（前任落地，本批复验） |
| 0b | **B111**（decorator-with-args 退元组） | B111_main（c4_19）/ B111_cross（r5v5_12） | 27/28→**28/28**、21/22→**22/22**（前任位B落地；本批复验维持 + docstring 合规补正） | 28/28、22/22 | 封闭（前任落地，本批复验） |
| 1 | **B104** chained_compare | B104_main | 11/14 | **14/14**（§1） | 封闭 |
| 2 | **B105** walrus | B105_main / B105_call | 8/13、6/12 | **13/13**、**12/12**（§2） | 封闭 |
| 3 | **B107** multi_target | B107_main | 10/14 | **14/14**（§3） | 封闭 |
| 4 | **B99 残** for 宿主 BoolOp return | B99_min | 8/9 | **9/9**（§4；§0.2 回退修复后复验维持） | 封闭 |
| 5 | **B98 拆分** 分组 boolop | B98_matrix / B98_hosts / B98_resid | 5/15、11/18、2/5 | matrix **7/15**（R1 封闭 §5；hosts/resid 持平）、hosts **13/18**（B99 外溢）、resid 2/5 | 部分封闭（R1 落地，R2/R3/B44 如实登记） |
| 6 | **B77** match 臂三元 return | B77_face | 7/8 | **8/8**（§6） | 封闭 |
| 7 | **B78** 条件位融合三元 | B78_face | 1/4 | 1/4 维持（§7 判据分析移交：hop 判别元 + 折叠常量合成在案） | 移交（分析在案） |
| 8 | **B79** 嵌套双层 finally×continue | B79_face | 3/4 | 3/4 维持（§8 判据分析移交：分区混装在识别层） | 移交（分析在案） |
| 9 | **B80** finally 条件段 × else 臂 import × handler return | B80_face | 2/3 | 2/3 维持（§9 移交） | 移交 |
| 10 | **B82** B75 残留两臂 return 互换 | B82_face | 1/3 | **2/3**（§10，n_fin_noseg 封闭；v_swap 移交识别层） | 部分封闭 |
| 11 | **B83** 循环体镜像块泄漏 finalbody | B83_face | 1/2 | **2/2**（§11） | 封闭 |

### §0.1 任务 0：插桩清零 + B108/B111 注释合规（已完成）

- **R8FIXBDBG 插桩 2 处已删**（region_ast_generator.py ≈L29115-29117 child walk print + ≈L31242-31246 finalbody legacy print，含 `_os_r8fb`/`_os_r8fb2` import 行）；grep `R8FIXBDBG` / `_os_r8fb` 全树零命中。
- **B108/B111 docstring 合规修正**（以代码真实算法为准，I.7；触及方法 4 个）：
  - `region_ast_generator.py _generate_try_body`（:27956 docstring）：③唯一归属判定补声明 [B108] finally 体 normal path 副本 ternary 跳过守卫（entry ∉ finally 块集 + 等块数 sibling ∈ finally 块集 ⇒ 副本 ⇒ 标记 generated 唯一归属 finalbody）+ handler/else 块集跳过守卫——原 docstring 未声明该行为，属「注释与代码行为不一致」，已修正注释。
  - `region_ast_generator.py _generate_handler_body_statements`（:31882 docstring）：③补声明 [B108] DELETE_FAST/NAME/GLOBAL/DEREF → Delete([Name(ctx='Del')])、DELETE_ATTR/DELETE_SUBSCR 经 _build_delete_stmt，及 as-var 清理守卫（本块内紧邻前驱 LOAD_CONST None + STORE 同名）不发射——原 docstring 未声明 DELETE 语句分支。
  - `ast_generator_v2.py _process_instruction`（:223）：docstring 由单行「处理单条指令」补齐六项模板 + C1/C2/C3（③声明 [B111] 加载指令族含 LOAD_CLOSURE/LOAD_CLASSDEREF；C2 声明与 _load_instr_to_ast 同集同语义）。
  - `ast_generator_v2.py _load_instr_to_ast`（:2388）：docstring 由单行补齐六项模板 + C1/C2/C3（③声明 [B111] cell 引用族，未知 opcode 显式占位符豁免）。
- **复验**：B108_main 14/14、B111_main 28/28、B111_cross 22/22 维持（`r8v8fixB_repro_task0_check.json`）。

### §0.2 P0 回退修复：round1face 416/423 → 417/423（get_last_stat；已完成）

- **回退事实**：前任批（HEAD d06846d7）站桩 round1face 416/423（基线 417/423），回退单元 = `site-packages/IQCommon/util/trade_info_utils.pyc::<module>.get_last_stat`（基线 success → `Failure: Different control flow`）；该 pyc 其余 5 个失败单元（trade_operation/kill_trade_process/get_trade_status/query_trade_strategy_info/query_strategy_id）为基线存量。
- **定位（亲跑 regen + dis + 区域树 dump 双树对比）**：get_last_stat 源语句 `result_data['data']['stat']['information']['value'].append((item[12 + index] and [item[12 + index]] or [0])[0])`——值位分组 BoolOp `(X and Y) or Z`，消费点 = append 实参位（非 exit）。块形态：@2336 `X; POP_JUMP_FORWARD_IF_FALSE→@2958(Z)`、@2934 `Y; JUMP_IF_TRUE_OR_POP→@2962(续接块)`、@2958 `Z=[0]` fall→@2962。**引入源 = B99 残 hunk「值位分组 BoolOp 前缀段反向吸收」（`_detect_boolop_short_circuit_chain`）**：吸收判据「前驱 P 以 FORWARD 条件跳转收尾 ∧ P 跳转目标 == 锚点 fall-through 后继」对 `(X and Y) or Z` 同样命中（P=@2336 跳 @2958 == @2934 的 ft）——但该 hunk 落地后与主走查的共享 merge 判据（Phase 3 adv14：链首块跳转目标 == 当前块跳转目标，否则断链）不相容：吸收前缀后链首 @2336 跳 @2958、锚点 @2934 跳 @2962，两目标不等且均非 exit-like（续接块 @2962 为 LOAD_CONST+BINARY_SUBSCR 大块、@2958 为 BUILD_LIST 块），Phase 7 豁免（exit-like 终点）不命中 ⇒ **锚点在首迭代被截断，链退化为仅前缀半链 `[(2336,'and')]`**。半链建区 `BOOL_OP entry=@2336 blocks=[@2336] merge=@2958`（无值块）：①压制了既有的全形态 `TERNARY entry=@2336 blocks=[2336,2934,2958,2962]`（唯一归属，修复前区域树实测在案）；②B99 skip 守卫对 @2336 不命中（跳转目标 @2958 ∉ 该半链区域块集）⇒ `_identify_conditional_regions` 新建 `IF_THEN entry=@2336 then=[@2934]` 语句路径接管 ⇒ 错构输出 `if item[12 + index] and [item[12 + index]]: count = [item[12 + index]]` + 游离 `[0]`（append 实参值链整体蒸发）。b99min 之所以不触发：其分组形态 `return (a or b) and c` 的外层 and 短路目标 = 裸 `RETURN_VALUE` 块（exit-like），Phase 7 豁免命中、锚点存活——吸收仅在 exit 终点消费位安全，普通块消费位系统性半链化（C1：半链无值消费点却整体建区）。
- **修复（判据收紧，不回滚 hunk；判据 = 链成员集合，I.4 白名单：区域成员关系）**：`_detect_boolop_short_circuit_chain` 新增 `_b99_absorb` 参数（默认 True，唯一调用点 `_detect_boolop_chain_start` 兼容）+ **提交收紧**：前缀吸收已发生但锚点（本方法起点块）未入链 ⇒ 吸收结果为非法半链，放弃前缀、以 `_b99_absorb=False` 重走一次（递归深度 ≤1），行为 = 吸收前原链逐位复原。锚点入链 ⇔ 走查通过共享 merge 判据/已建区前驱判据——吸收仅在产出合法全链时提交（C3 封闭：吸收不再越过走查自身判据面）。
- **代码已落地（I.6）**：`core/cfg/region_analyzer.py` `_detect_boolop_short_circuit_chain`：签名 + `_b99_absorb` 门控 + [B99-C3] 判据注释块（≈:30700-30731）；提交收紧重走（≈:30966-30983）。
- **复核读数**：round1face **417/423**（`r8v8fixB_full_round1face.json` 重跑，trade_info_utils 36/41 仅剩 5 基线存量失败）；四修复负对照 `B104_main 14/14、B105_main 13/13、B105_call 12/12、B107_main 14/14、B99_min 9/9`（62/62，`r8v8fixB_repro_r0fix.json`）——B99 已封闭探针零回退，hunk 未回滚。
- 条款引用：C1（半链区域只读自身块集即建区，无值消费点）、C3（吸收越过走查判据面无显式封闭 ⇒ 收紧为「锚点入链才提交」显式守卫）；判据白名单 = 链成员集合（区域成员关系），无黑名单项。

---

## §1 B104：chained_compare（封闭）

### 破口回顾（round8 REVIEW.md §3 行 #14；机制权威 = round4 REVIEW §4.1）
三个失败单元三个宿主形态：**e04_deep**（for 体 `if 0 < x < 10 < x*2:` → `if 0 < x and 10 < True:`，链尾被常量/布尔占位替换）、**e08_while**（`while 0 < x < n < 100:` → `if …: pass else: return n`，循环头折叠为 if、体蒸发）、**CCMP.m**（with 体 `return a < b < c < len(f.read())` → `return None`，return 链整体蒸发）。判据方向（在案）：末操作数块整体归 Compare 节点、禁常量/布尔占位、宿主无关。

### 根因（亲跑逐块/区域树核实）
1. **e04_deep / CCMP.m（C2 破坏：链协议块被语句路径接管）**：`_identify_chained_compare_regions` 把 Phase 1 宿主区域（loop/try/with/match/assert）**全部块**并入 claimed 整体跳过——for 体/with 体内的链式比较协议块永得不到链式比较归约；下游以错误形态认领：for 体 3+ 元链的中间段共享短路清理目标，被 R37 inline and 链合并 + `_detect_chained_compare_pattern(condition_block)` 在**重定向后的链末块**上运行 → 首操作数丢失 + 半链重建出 `10 < True` 占位（e04_deep 实测区域树：IF_THEN entry=@8、cond=@26、cc_ops=['<','<']——首段 @8 的操作数不在 ops 覆盖内）；with 体 return 位链（JUMP_IF_FALSE_OR_POP 协议）被 BOOL_OP 抢占（`_identify_conditional_regions` 对 SHORT_CIRCUIT 结尾块显式 continue，值位链在宿主内无任何认领者，最终 `return None`）。
2. **e08_while（C3 破坏：while 条件链守卫未封闭 + 体装配泄漏）**：`_identify_loop_regions` 的 pre-loop 链回溯（:4480 起）沿 JUMP_FORWARD 前驱回溯找 `_is_chained_compare_header` 命中即停——链式比较**中间段同样携带 COPY(2)+COMPARE_OP 指令对**，3+ 元链在第二段即停、真链头（首段块，含前驱语句 `n = 0`）未被循环唯一归属（原则 2 破坏）→ 链头被 `_identify_chained_compare_regions` 抢占为重叠 IF 区域（blocks 与 WHILE_LOOP 交叠）→ 生成层循环整体折叠为 if。次要：w1 最小复现（`while 0 < x < 10: x += 1; return x`）暴露体装配两处泄漏——重检假出口的纯清栈块（POP_TOP）经 `_generate_block_statements` 沿 fall-through 吸入循环后 return（`return x` 伪入体、循环后语句蒸发），3+ 元链的纯重检中间段（非回边块）未被抑制。

### 守卫设计（判据逐条 I.4 白名单；修复 = 封闭守卫、恢复 C2/C3，宿主无关）
1. **[B104-H1] `_identify_chained_compare_regions` claimed 跳过面收窄**（region_analyzer.py）：动态认领集（claimed，本方法自建区域防重复）与 Phase 1 结构保护集（protected）分离；protected = WHILE 全块（while 体含条件回边重检副本，COPY+COMPARE 与真链同形，逐块不可区分）∪ for 结构边界块（header/condition/back_edge/condition_chain/else/init）∪ try/match/assert 全块 ∪ with cleanup+exception+entry；**for 体块与 with 体块放行**——嵌套链得到链式比较归约，与 `_identify_boolop_regions` 嵌套 claimed 放宽（Phase 32/33/34）同构。依据：区域成员关系 + 块身份。
2. **[B104-H2] pre-loop 链回溯协议续接**（`_identify_loop_regions` :4499 起）：回溯命中 `_is_chained_compare_header` 后不即停，按**协议续接判据**继续向前：前驱 P 以 FORWARD 条件/短路跳转收尾 ∧ P 的跳转目标 == 当前段短路跳出目标（共享清理块同一性）∧ 当前段 ∈ P 后继集（fall-through 续接）⇒ P 是前一段；回溯至真链头（条件块、condition_chain_blocks、cc_ops 全链恢复，`n = 0` 前驱语句经 STORE 前缀过滤保持为 pre_stmt）。外层语句前缀（跳转目标指向自身合并块）不满足共享目标判据被显式排除。
3. **[B104-H3] conditional 链头守卫扩展**（`_identify_conditional_regions` :18710 起）：块已是链式比较 IfRegion 的 entry 时跳过独立 IfRegion 创建——block_to_region 在宿主嵌套形态下指向 Phase 1 宿主（先到先得），原守卫命不中；改经 self.regions 按 entry + chained_compare_ops/blocks 结构字段直接查找（与 `_detect_boolop_conditional_chain` 的链式比较原子操作数查找同构）。
4. **[B104-H4] while 体重检/清栈抑制扩展**（region_ast_generator.py `_loop_generate_while` 链式比较分支）：①纯清栈块（块内全 POP_TOP/SWAP/COPY+噪声 ∧ 全部后继越出循环区域成员关系）整块抑制——协议假路径清栈段非用户语句，出口块由父层顺序归约；②纯重检中间段（非回边块：块内全比较求值 opcode 白名单 ∧ 条件跳出目标为纯协议清理块或越出循环体）整块抑制——与既有 back_edge 纯重检判据同族，真 body if 的假出口落在含 STORE/CALL 的合并块不命中。
5. **[B104-H5] while-cc 条件成员 boolop 抢占封闭**（`_identify_boolop_regions`）：`loop_cc_cond_blocks`（is_chained_compare_cond 循环的 condition_block + condition_chain_blocks，metadata 标志 + 区域成员关系）不作 BoolOp 链起点——链协议段共享清理目标与 and 短路同形，误装配会以条件子区域叠加到循环条件（实测 w2 修复中间态 `while 0 < x < n < 100 and n < 100`）；并扩展 `_detect_boolop_conditional_chain` 的 B115 循环守卫映射至 condition_chain_blocks（非首成员吸收封闭）。
6. **[B104-H6] 专用重建器前缀 STORE 剥离**（region_ast_generator.py `_try_build_method_call_chained_compare` / `_try_build_call_middle_from_blocks` / `_try_build_attr_middle_from_blocks`）：镜像 `_try_build_complex_operand_chained_compare_from_blocks` 的 [R106] 前导 STORE_* 剥离——宿主目标绑定（STORE_FAST f / STORE_FAST x）合入链头块时其消费的栈值不在本块产生，逆向栈模拟越过它吸收前缀指令、污染 left/middle 切分（块内 opcode 序事实）。

### 触及方法与注释合规（I.7）
- `_identify_chained_compare_regions`：docstring「唯一归属判定」与 C 条款按收窄后口径修正（[B104] 标注）；实现内新增 protected 构建注释块（六项要素 + C1/C2/C3）。
- `_identify_loop_regions`：链回溯处新增 [B104] 协议续接注释块（判据/归约/AST 映射/C 条款）。
- `_identify_conditional_regions`：[B104] 守卫注释块（原则 2/3 + I.4 白名单）。
- `_identify_boolop_regions`：loop_cc_cond_blocks 构建处注释块（唯一归属 + C 条款）；`_detect_boolop_conditional_chain` B115 映射扩展注释。
- `_loop_generate_while`：[B104] 抑制分支注释块（判据 = 块内 opcode 序 + 后继/区域成员关系）。
- 三个 `_try_build_*` 重建器：[B104] 前缀剥离注释。

### 自测读数
- **B104_main（c4_09_chained_compare）：11/14 → 14/14**（e04_deep / e08_while / CCMP.m 全部转 MATCH；负对照 e01_root/e02_shallow/e03_mixed/e05_is_in/e06_notin/e07_comp/e09_closure 维持）。
- 邻域负对照（本批复现中间态实测，w1/w2 最小复现）：`while 0 < x < 10:`（2 元链 + 前驱无语句）与 `while 0 < x < n < 100:`（3 元链 + 前驱语句）均逐字节 MATCH（修复前 w1 体泄漏 `return x`、w2 折叠为 if）。
- 全 30 探针中间态重放（`r8v8fixB_repro_b104_full.json`）：B104_main +3 单元（271→274），**其余 29 探针逐探针与 after_b108_del 基线持平、WORSE=0**。
- 站桩 6 面（`r8v8fixB_*` 本批独立驱动副本）：round2face **235/251**、probe42 **176/196**、round1face **417/423**、residual **418/446**（251/277+167/169）、oldface **664/692**（217/227+447/465）、quotation **152/153**——全部持平基线。
- 34 小测试集（8 分片）：**1505/1568**，NEWFAIL=0。

### 代码已落地（I.6）
- `region_analyzer.py`：`_identify_chained_compare_regions` claimed/protected 分离 + protected 构建（≈:17891-17976）；`_identify_loop_regions` 协议续接（≈:4506-4560）；`_identify_conditional_regions` [B104] 链头守卫（≈:18716-18734）；`_identify_boolop_regions` loop_cc_cond_blocks（≈:26317-26334 + 主循环 skip ≈:26399）；`_detect_boolop_conditional_chain` B115 映射扩展（≈:29007-29019）。
- `region_ast_generator.py`：`_loop_generate_while` 纯清栈/纯重检抑制（≈:7927-7990）；三个 `_try_build_*` 前缀剥离（≈:16646-16658 / ≈:16915-16928 / ≈:17034-17046）。

证据：`r8v8fixB_repro_b104_try1.json`（14/14）、`r8v8fixB_repro_b104_try2.json`（邻域 5 探针持平）、`r8v8fixB_repro_b104_full.json`（30 探针中间态全量）。

---

## §2 B105：walrus（封闭）

### 破口回顾（round8 REVIEW.md §3 行 #15；机制权威 = round4 §4.1 / round5 §3）
条件位/实参位值链丢失：**e01_root/e05_nested/CW2.m/e09_with**（`if (n := len(x)) > 3:` → `if 3:`，walrus 值链蒸发、条件退化为比较右操作数占位）；**e06_call_arg/w_call/w_nested_call**（`return f((n := x + 1), n)` → `n = x + 1` + return 蒸发）；**w_deep**（while 条件 walrus 的回边重检泄漏为体尾 `m = x * 2`）。判据方向（在案）：STORE 前值消费链块集合成员关系，「STORE 目标 + 值链块」整体认领（B88 同族）。

### 根因（亲跑逐块/trace 核实；全部为 C1 破坏——值消费链被语句边界切断）
1. **if 条件位**：`_if_extract_cond_instructions` 的 `_last_store_in_iter` 把 walrus 的 `COPY(1)+STORE_*` 副作用对当作「最后语句 STORE」切分条件源——cond_instrs 从 walrus STORE 之后起算，整个值链被排除，条件只剩比较右操作数（`if 3:`）。walrus COPY 把值留栈供 COMPARE 消费，STORE 只是 NamedExpr 副作用，不是语句边界。
2. **实参/返回值位**：`_generate_block_statements_body` 通用 STORE 归约点把 walrus 副作用对按独立赋值刷出（`n = x + 1`），后续 PRECALL/CALL/RETURN 因栈缺操作数重建失败蒸发（Return(None)）；双 walrus 实参（`f((a := g(x)), (b := a + 1))`）另被 [Round7/8/9] walrus 整合路径的 `_final_store` 扫描误终结在第二个 walrus 的 STORE 上。
3. **while 回边重检位**：`_loop_find_cond_start_idx` 的 LOAD-only 逆向扫描在 walrus STORE 处截断，重检求值段（walrus 值计算 + COPY/STORE + 比较右操作数）被误划为前驱体语句（`m = x * 2` 泄漏进体）。

### 守卫设计（判据逐条 I.4 白名单：块内 opcode 序 + CPython 值栈净效应；与既有 walrus 判据族同源——AugAssign/POP_TOP/RETURN/UNPACK 四分支「值消费链延续」同族）
1. **[B105-H1] 条件源边界 walrus 排除**（`_if_extract_cond_instructions`）：`_last_store_in_iter` 跳过前邻 COPY(1) 的 STORE_*（镜像 `_loop_handle_exit_successors` 同名判据先例）；链式赋值 `a=b=f()` 的首 STORE 虽亦前邻 COPY(1) 但后继为 STORE_*，仍作语句边界（行为不变）。
2. **[B105-H2] 通用 STORE 归约点 walrus 值链保持**（`_generate_block_statements_body` 55999 区）：B85 链扫描未命中 ∧ STORE 后继非 STORE_*（链式赋值排除面）∧ 净栈深弹出该 STORE 后 > 0（值仍留栈待消费）⇒ 不切分语句，保持累积交 expr_reconstructor 重建 NamedExpr 子节点（原则 3：walrus 是外层表达式子节点非兄弟语句）。
3. **[B105-H3] `_final_store` walrus 排除**（[Round7/8/9] walrus 整合路径）：向前扫描命中的终结 STORE 若前邻 COPY(1)（第二个 walrus 的副作用落点）则非语句终结，放弃整合路径落回 H2 续接。
4. **[B105-H4] 回边重检起点栈需求模拟**（`_loop_find_cond_start_idx`）：块含 COPY(1)+STORE_* 对时，以「条件跳转恰需 1 个栈值」自块尾逆向模拟（镜像 `_loop_generate_while` walrus 重检分支同名算法）求重检起点；无 walrus 对或模拟不可判定时落回原扫描（逐位不变）。

### 触及方法与注释合规（I.7）
四处 hunk 均在实现处带 [B105] 注释块（判据/归约/AST 映射/C1-C3 条款）；触及方法 `_if_extract_cond_instructions` / `_generate_block_statements_body` / `_loop_find_cond_start_idx` 的既有 docstring 行为描述不变部分未动，新增行为已在各自 hunk 注释中按六项要素声明。

### 自测读数
- **B105_main（c4_10_walrus）：8/13 → 13/13**；**B105_call（r5v5_09_walrus_callsite）：6/12 → 12/12**。
- 负对照（合成探针亲跑，pyc_verify single）：`a = b = f()` 链式赋值（COPY(1)+STORE+STORE 形，排除面）、`while 0 < x < 10:`/`while 0 < x < n < 100:`（B104 面）、t2 walrus 实参——3+4 单元全 MATCH。
- 全 30 探针重放（`r8v8fixB_repro_b105_full.json`）：BETTER={B104_main, B105_main, B105_call}，**WORSE=0**（271→285，+14 = B104 3 + B105_main 5 + B105_call 6）。
- 站桩 6 面：全部持平基线（235/251、176/196、417/423、418/446、664/692、152/153）。
- 34 小测试集（8 分片）：**1505/1568，NEWFAIL=0**。

### 代码已落地（I.6）
- `region_ast_generator.py`：`_if_extract_cond_instructions` walrus STORE 排除（≈:17910-17933）；`_generate_block_statements_body` 通用 STORE 归约点 walrus 值链保持分支（≈:56010-56048）；[Round7/8/9] 整合路径 `_final_store` walrus 排除（≈:55860-55890）；`_loop_find_cond_start_idx` 栈需求模拟前置（≈:13699-13731）。

证据：`r8v8fixB_repro_b105_try4.json`（B104+B105 三探针 39/39）、`r8v8fixB_repro_b105_full.json`（30 探针全量，WORSE=0）。

---

## §3 B107：multi_target（封闭）

### 破口回顾（round8 REVIEW.md §3 行 #17；机制权威 = round4 §4.1）
四个失败单元三个子形态：**e06_chain_target/e09_attr_chain**（`a[0] = b[1] = x + 1` → `a[0] = x + 1; b[1] = None`——链式下标/属性目标第二目标值丢失退 None）；**e04_unpack**（`a, b = c, d = (x, x+1)` 链正确但链后 return 蒸发）；**e05_star_unpack**（`a, *b = c, *d = [...]` 第二目标组 `(c, *d)` 整组丢失）。判据方向（在案）：链式目标 STORE 序列 + 同值块集合成员关系，禁后续目标退 None。

### 根因（亲跑 trace 核实）
1. **链式复杂目标（C1 破坏：COPY 复制值链被语句边界切断）**：CPython 3.11 链式赋值协议 `<值>; COPY 1×(N-1); [<目标前缀>; STORE_SUBSCR|STORE_ATTR]×N`——每个目标段消费一份复制值（每段净栈效应 -1，末段后归零）。两条语句重建路径（`_generate_block_statements_body` 通用走查 + `_build_statements_from_instructions`）的 STORE_SUBSCR/STORE_ATTR 归约点都在首个复杂 STORE 处切分语句：首目标按单目标赋值发射、复制值滞留在后续段的重建栈之外 → 第二目标重建时值缺省退 None / 整段蒸发。
2. **多目标解包链**：`_build_multi_target_unpack` 只支持 UNPACK_SEQUENCE 目标组且不归约链后尾随语句（e04 的 return 整段丢失）；含 UNPACK_EX 的块被 `_has_unpack_ex` 单组路径优先接管，星号解包链（COPY 1 + UNPACK_EX 双组）无法整链归约（e05 第二组丢失）。

### 守卫设计（判据逐条 I.4 白名单：块内 opcode 序 + CPython 值栈净效应）
1. **[B107-H1] 复杂目标值链保持**（两条语句重建路径的 STORE_SUBSCR/STORE_ATTR 归约点）：本 STORE 弹出目标槽后净栈深仍 > 0 ⇒ 值是 COPY 复制出的链式份额、后续目标段仍待消费——保持累积不切分（与 [B105-H2] walrus 值链保持同一判据族）；单目标/AugAssign 协议（COPY(2)+BINARY_SUBSCR+SWAP+SWAP）弹后恒为 0，不命中（行为逐位不变）。
2. **[B107-H2] 链式复杂目标整链归约**（新增 `_build_chained_complex_target_assign`，六项模板 + C 条款 docstring）：复杂 STORE 数 ≥ 2；值段边界 = 首个「后继非 STORE_* 的 COPY(1)」（前向扫描，排除 walrus 副作用对）；全量正向栈模拟验证每段以复杂 STORE 收尾、段后深度 == 剩余段数、末段后归零且为序列末条；目标段两段逆向需求模拟切分（容器/键 for STORE_SUBSCR、对象 for STORE_ATTR）；产出 `Assign(targets=[...], value=..., is_chain_assign=True)` 单一节点（原则 3：整链黑箱，code_generator 按 `t1 = t2 = v` 渲染再生 COPY 协议）。任一判据不中返回 None 落回单目标路径（C3 封闭）。
3. **[B107-H3] `_build_multi_target_unpack` 扩展**：目标组收集支持 UNPACK_EX（arg = before | after<<8 协议，Starred elts，镜像 `_has_unpack` 分支消费协议）；链后剩余指令（`_mt_idx` 之后）交 `_build_statements_from_instructions` 按语句边界重建尾随语句（每块唯一归属——此前链后 return 整段蒸发）。
4. **[B107-H4] 星号解包链路由**：`_has_unpack_ex` 分支前置「COPY(1) 紧邻 UNPACK_EX = 多目标链标志」检查（与 UNPACK_SEQUENCE 链同源判据），命中即委托 `_build_multi_target_unpack` 整链归约；单组星号解包（无 COPY(1) 前邻）维持既有单目标路径。

### 自测读数
- **B107_main（c4_07_multi_target）：10/14 → 14/14**（e04/e05/e06/e09 全转 MATCH）。
- 负对照（合成探针 p3，pyc_verify single 9/9 MATCH）：单目标 `d[k]=v`/`o.a=x`、AugAssign `d[k]+=v`（COPY(2) 读回协议不命中）、嵌套下标 `d[a][k]=v`、新链式形态 `a[0]=b[1]=v`/`o.a=p.b=v`、B105 面 `f((n:=x+1),n)`、名字链 `a=b=c`。
- 全 30 探针重放（`r8v8fixB_repro_b107_full.json`）：BETTER={B104_main, B105_main, B105_call, B107_main}，**WORSE=0**（271→289，+18）。
- 站桩 6 面：全部持平基线；34 小测试集（8 分片）：**1505/1568，NEWFAIL=0**。

### 代码已落地（I.6）
- `region_ast_generator.py`：`_build_chained_complex_target_assign` 新增（≈:58104-58310，六项 + C 条款）；`_generate_block_statements_body` STORE_ATTR/STORE_SUBSCR 归约点 [B107] 分支（≈:55572-55610 / ≈:55750-55790）；`_build_statements_from_instructions` 同源分支（≈:33589-33646 / ≈:33665-33700）；`_build_multi_target_unpack` UNPACK_EX 组 + 尾随语句（≈:58460-58560）；`_has_unpack_ex` 链路由（≈:54427-54437）。

证据：`r8v8fixB_repro_b107_try4.json`（14/14）、`r8v8fixB_repro_b107_full.json`（30 探针全量，WORSE=0）。

---

## §4 B99 残：for 宿主 BoolOp return（封闭）

### 破口回顾（round8 REVIEW.md §3.1 行 #9；机制权威 = round3 REVIEW §4.1）
单一交叠形态：`for i in y: if i: return (a or b) and c`（b99min::for_grouped）——值位分组 BoolOp 的 or 前缀段被 IfRegion 语句路径抢占，`return` 值链蒸发为 `if …: pass` 形（C2 破坏）。round3 已封闭平坦链/负对照；本批封闭 for 宿主交叠残 unit。

### 根因（亲跑 dis/区域树核实）
`(a or b) and c` 值位 lowering：`a; POP_JUMP_FORWARD_IF_TRUE→X(c)`、`b; JUMP_IF_FALSE_OR_POP→END`、`X: c`、`END: RETURN`——b 段块（短路链起点）的前驱 a 段块以 FORWARD 条件跳转收尾且跳转目标 == b 段块的 fall-through 后继（c 块），是同一值链的前缀段；`_detect_boolop_short_circuit_chain` 从 b 段起查时看不到 a 段（短路链只沿 fall-through 前向走）⇒ a 段块无值链认领者 ⇒ `_identify_conditional_regions` 把 a 段错认为独立 if（`a; POP_JUMP_FORWARD_IF_TRUE→c` 形似 `if a: <c>`）⇒ 语句路径接管，return 值链蒸发。

### 守卫设计（判据逐条 I.4 白名单）
1. **[B99-H1] 前缀段反向吸收**（`_detect_boolop_short_circuit_chain`）：短路链起点（锚点，块末 ∈ SHORT_CIRCUIT）的逐前驱回溯——前驱 P 以 FORWARD 条件跳转收尾 ∧ P 的跳转目标 == 锚点的 fall-through 后继 ⇒ P 是同一值链前缀段，反转序整体认领为链首（op 由 P 块末 opcode FALSE 极性定 and/or）；多前驱同目标递归吸收（多操作数前缀组）；无命中时行为逐位不变（C3）。
2. **[B99-H2] 值位链成员/入口 IfRegion 抢占封闭**（`_identify_conditional_regions`）：块是某 BoolOpRegion 的非入口非 merge 成员（值位 or/and 前缀段）⇒ 跳过独立 IfRegion 创建（C2：值链被语句路径接管）；值上下文（is_condition_context=False）BoolOpRegion 的 entry 以 FORWARD 条件跳转收尾且跳转目标 ∈ 本区域块集 ⇒ 入口是值链首段非用户 if 条件，同判跳过；条件上下文入口（`if a and b:`）不命中，维持既有创建流。判据只读 BoolOpRegion.blocks 成员关系。
3. **[B99-H3] 提交收紧（§0.2 回退修复，本续作批落地）**：前缀吸收仅在锚点确实入链（走查通过共享 merge 判据）时提交；锚点未入链 ⇒ 放弃前缀按无吸收路径重走（= 吸收前原链，`_b99_absorb=False` 递归深度 ≤1）。封闭「普通块消费位半链化」越权面（C1/C3，详见 §0.2）。

### 触及方法与注释合规（I.7）
两处 hunk 均带 [B99 残] 判据注释块（判据/归约/AST 映射/C1-C3 条款）；`_detect_boolop_short_circuit_chain` 为 `_detect_*` 辅助谓词（非 `_identify_*_regions`/`_generate_*` 六项模板强制对象），判据注释按既有 hunk 注释风格。

### 自测读数
- **B99_min（b99min）：8/9 → 9/9**（for_grouped 转 MATCH；其余 8 单元维持）。
- **B98 面正向外溢**：B98_matrix 5/15→**6/15**、B98_hosts 11/18→**13/18**（前缀段吸收对 for/while 宿主 and/or 分组同族单元的直接改善，归属 B98-R1/R3 子形态证据链）。
- 全 31 探针重放（`r8v8fixB_repro_b99_full.json`）：位B目标族 B108 14/14、B99 9/9、B104 14/14、B105 13/13+12/12、B107 14/14、B111 28/28+22/22 全 success；WORSE=0（站桩 6 面中 round1face 的 -1 回退已由 §0.2 修复，其余 5 面持平）。
- §0.2 修复后复验：B99_min 9/9 维持（`r8v8fixB_repro_r0fix.json`）。

### 代码已落地（I.6）
- `region_analyzer.py`：`_identify_conditional_regions` [B99 残] 链成员/入口抢占封闭（≈:19002-19042）；`_detect_boolop_short_circuit_chain` 前缀段反向吸收（≈:30700-30761）+ [B99-H3] 提交收紧重走（≈:30966-30983，§0.2）。

证据：`r8v8fixB_repro_b99_try1.json`（9/9 首验）、`r8v8fixB_repro_b99_try2.json`（负对照）、`r8v8fixB_repro_b99_full.json`（31 探针全量）、`r8v8fixB_repro_r0fix.json`（§0.2 后四族负对照 62/62）。

---

## §5 B98 拆分：R1/R2/R3 + B44 存量（部分封闭：R1 已落地）

### 破口回顾（round8 REVIEW.md §3.1 行 #8；机制权威 = round3 REVIEW §4.1）
分组 boolop 保真残余，一号多形态拆分登记：**B98-R1 尾组边界**（or 尾+and 组 / and 尾+or 组）、**B98-R2 表达式位交叉**（三元/比较/海象 × 分组）、**B98-R3 宿主交叠**（for/try/match/with/comp）、**B44 存量**（resid r_d1/r_e3/r_g2 ≥3 层）。before（b99_full 基线）= matrix 6/15、hosts 13/18、resid 2/5。

### 根因（亲跑区域树 dump + dis 双向核实）
1. **R1（`(a or b) and c` 值位被语句/伪三元路径接管）**：CPython fused lowering `a; POP_JUMP_FORWARD_IF_TRUE→c块` + `b; JUMP_IF_FALSE_OR_POP→merge` + `c块`（共享块：and 右操作数 == or 捷径落点）。既有 `_identify_ternary_regions` 把该钻石建为 TernaryRegion（条件 a 块 IF_TRUE 极性）+ `_generate_ternary` 的 [R38] 负极性还原产 `not a` 包裹 → 错构 `r = b and c if not a else c`（IfExp 重编译多出独立 else 块 + JUMP_FORWARD，控制流不等）。B99 的前缀吸收在普通块消费位被共享 merge 判据截断（§0.2 修复如实回退），and-region 只认领 b 块，a 块归伪三元。
2. **R2（分组 boolop 作子表达式操作数时消费点蒸发）**：`(a or b) and c` 在 **return 位**（B99 已修，merge 为裸 RETURN 块 exit-like 吸收存活）；在 **STORE 位**（R1 镜像修，merge_ctx='store' 消费完整）；在 **比较位**（`return ((a or b) and c) > 2`：analyzer merge 扫描把 merge 块判 merge_context='compare'，但该 ctx 生成路径 `_try_build_ternary_chained_compare` 只覆盖链式比较（SWAP2+COPY2+JIF_OR_POP 签名），单 COMPARE_OP + RETURN 消费者无重建路径 → 退化为裸 Expr + `return None`）；**海象位**（`if (w := ...): return w` 的 walrus 绑定已重建、then 体 return 蒸发）；**实参位**（`sink(...)` merge 块 = PRECALL/CALL 块非 exit-like，吸收截断后 a 块被 IfRegion 语句路径抢占 → `if (a or b) and c: pass`）；**外层三元 then 臂位**（`return ((a or b) and c) if d else 0`：外层三元真臂含内层分组 boolop + JUMP_FORWARD hop，[B46] 嵌套真臂放行门要求内层 merge 以 STORE/RETURN 终结被 hop 块拒绝 → 外层被 IfRegion 抢占为 if 语句）。
3. **R3（宿主交叠）**：handler/comp×3/with 体宿主——分组 boolop 值链在宿主域内的消费点形态与 R2 同源，宿主本身不引入新机制（同判据方向）。
4. **B44 存量**（resid r_d1/r_e3/r_g2）：≥3 层嵌套分组，双入口归纳分支链嵌套右臂（round3 判据草案），本批未触及。

### 守卫设计（判据逐条 I.4 白名单；R1 已落地）
1. **[B98-R1-H1] 镜像极性共享块重建**（region_ast_generator.py 新增 `_try_build_orprefix_and_boolop_from_ternary` + `_generate_ternary` 调用点重构）：与既有 [P1-2] `_try_build_andor_boolop_from_ternary`（`cond and X or Y`）严格镜像——签名四判据：①条件块末 IF_TRUE 族（or 前缀极性）∧ 跳转目标 == 本三元 false_value_block；②true_value_block（条件块 fall-through）是纯 and 链 BoolOpRegion entry ∧ merge 与本三元同一；③and 链首块 fall-through == false_value_block（**共享块签名**，真三元 `(b and c) if not a else c` 的 then 链 fall-through 落 then 路径内部续接块、else 值块为独立复制块，二者必不同块——共享块是 fused 形态的唯一判别元）；④and 链重建恰两操作数。命中重建 `BoolOp(And,[BoolOp(Or,[a,b]),c])`（括号保真），未命中逐位回退 IfExp。
2. **[B98-R1-H2] [R38] 负极性包裹豁免**（`_generate_ternary`）：镜像命中时跳过 [R38] `not` 包裹（镜像极性 IF_TRUE 与 [R38] 包裹条件同域竞争，先包裹再重建会产 `(not a or b) and c` 错构）；调用序 = 镜像检查 → [R38]（以镜像未命中为条件）→ [P1-2]（IF_FALSE 极性不受 [R38] 影响，行为不变）。

### 自测读数（R1 落地后）
- **B98_matrix：6/15 → 7/15**（f_or_in_and_deep 转 MATCH：`r = (a or b) and c` 逐字节等价）；f_or_in_and_pair_deep 由 `b and (c or d) if not a else c` 改善为部分镜像（and 链重建非两操作数时保守回退，仍败）；ternary_cross/compare_cross/walrus_cross 内层分组 boolop 渲染已转正确（消费点仍蒸发，R2 在案）。
- **B98_hosts 13/18、B98_resid 2/5 持平**（未回退）。
- 负对照：get_last_stat `(X and Y) or Z`（镜像的 or-outer 方向，走既有 [P1-2] 路径）维持 36/41 success——镜像不腐蚀既有混合链路径；b99min 9/9 维持。
- 全 31 探针重放（`r8v8fixB_repro_b98r1_full.json`）：**WORSE=0**，唯一 BETTER = B98_matrix +1。

### 未竟子形态登记（如实移交，机制与已排除方向）
| 子形态 | 失败单元 | 已排除方向 | 剩余修复点 |
|--------|---------|-----------|-----------|
| B98-R2 比较位 | f_b98_compare_cross | 链式比较重建器不适用单 COMPARE_OP；merge_ctx='compare' 分类正确 | `_try_build_ternary_chained_compare` 旁增设单比较 + RETURN 消费重建（Compare(ternary, R) → Return） |
| B98-R2 实参位 | f_b98_call_arg_pos | 吸收截断（§0.2）后 a 块 IfRegion 抢占；M1 前缀豁免实验证伪（吸收成链后 fat merge 块建区吞语句，get_last_stat 反退） | 实参位消费链整体认领需 BoolOpRegion merge 块消费点栈位归属重建，涉跨探针回归面 |
| B98-R2 外层三元 then 臂 | f_b98_ternary_cross | [B46] 嵌套真臂放行门拒 hop merge（正确性存疑：hop 块是 passthrough） | `_detect_ternary_pattern` [B46] 门扩展（内层 merge 为单 JUMP_FORWARD passthrough 且目标 == 外层 merge 时放行）——识别层 `_identify_ternary_regions` 锚（B77/B78 判据族协同位） |
| B98-R2 海象 then 体 | f_b98_walrus_cross | walrus 绑定重建已正确；then 体 return 蒸发 | if 体装配对 ternary 条件子区域块的 then 臂发射 |
| B98-R1 尾组（多组） | f_or_in_and_pair_deep、f_b98_and_tail_or_group | and 链重建非两操作数（嵌套 or 组）时镜像保守回退 | `_build_boolop_expression` 对 and-region 含嵌套 or 子组的两值分组重建 |
| B98-R1 条件位 or 尾 | f_b98_or_tail_and_group | `(a and b) or c or d` 条件位：`(a and b)` 组已正确入条件，or 尾装配错位（return i 进 else 分支） | 条件链 or 尾成员的 IfRegion else 臂归属 |
| B98-R2 not 包裹 | f_b98_not_wrapped | `return 1 if not ((a or b) and c) else 2` 整句蒸发 | UNARY_NOT 包裹分组 boolop 的条件位重建 |
| B98-R3 宿主 | CB98.m_handler、comp×3、f_with_body_host | 与 R2 同源消费点形态，宿主不引入新机制 | 随 R2 判据族认领 |
| B44 存量 | r_d1/r_e3/r_g2 | ≥3 层双入口归纳分支链嵌套右臂（round3 判据草案） | `_build_boolop_expression` 双入口归纳——工程量大，独立批次认领 |

- **M1 前缀豁免实验证伪记录**（方法论存证）：曾尝试在 `_detect_boolop_short_circuit_chain` 共享 merge 判据为 [B99 残] 吸收前缀设豁免（链首为吸收前缀时不断链）——b99min 维持但 get_last_stat append 实参位反退（分组 BOOL_OP 建区吞 fat merge 块的续接语句，信息 append 及后续 6 句整体蒸发），已回滚。结论：吸收前缀豁免在普通块消费位系统性不安全，正确方向 = 生成层共享块镜像（R1-H1 落地方案）。

### 代码已落地（I.6）
- `region_ast_generator.py`：`_try_build_orprefix_and_boolop_from_ternary` 新增（≈:42377-42489，判据/归约/AST 映射/C1-C3 全声明）；`_generate_ternary` 镜像调用点 + [R38] 豁免门（≈:43701-43740）。

证据：`r8v8fixB_repro_b98r1.json`（3 探针）、`r8v8fixB_repro_b98r1_full.json`（31 探针全量 WORSE=0）。

---

## §6 B77：match case 臂内三元 return（封闭）

### 破口回顾（round8 REVIEW.md §3.1 行 #22 补录 #44，designated；机制权威 = round1 REVIEW2 §5）
`match x: case 1: return "one" if flag else "1"`（r7_08::t_host_match_case）——case 臂内 return 位三元退化为 if/else 语句（`if flag: return 'one' else: return '1'`）。若分支语句重编译产生分支内独立 RETURN，与原字节码共享 merge RETURN 布局不一致 ⇒ Different control flow。B46 族 match 臂宿主变体。

### 根因（亲跑区域树 dump 核实）
case 臂块形态：`@16 POP_TOP(subject 丢弃)+LOAD flag+POP_JUMP→@26`、`@22 'one'+JUMP_FORWARD→@28`、`@26 '1'`、`@28 RETURN_VALUE`。识别层 `_identify_ternary_regions` 经 `_can_be_ternary_header` 的 `existing.can_be_ternary_header` 多态拒绝臂块建 TernaryRegion（臂块 block_to_region → MatchRegion，MatchRegion 覆写为禁止——tn20/tn21 防模式检查链误吞，识别侧全臂禁令正确但无表达式位例外）⇒ `_identify_conditional_regions` 在臂内建 IF_THEN_ELSE entry=@16 [16,22,26] merge=@28 ⇒ 生成层 `_generate_match` case 体装配按语句区域派发 `_generate_region` → if/else 语句（值钻石被语句路径接管，C2）。

### 守卫设计（判据逐条 I.4 白名单；修复点 = `_generate_match` case 体装配发射域，与派发预期一致）
1. **[B77-H1] 臂内值钻石就地重建**（新增 `_try_build_match_case_ternary_stmt`）：case 臂块集（body）内 IfRegion 判据五项——①if_region.blocks ⊆ 臂块集 ∧ merge ∈ 臂块集（case 臂块集成员）；②条件块末 ∈ FORWARD_CONDITIONAL_JUMP_OPS ∧ 恰两条件后继；③then 值块（then_blocks 唯一成员）以 JUMP_FORWARD 收尾且目标 == merge，else 值块（条件跳转目标）唯一后继 == merge；④值块为纯值生产者（块内 opcode 序：剥尾跳后无 STORE/POP_TOP/RETURN/跳转），merge 为纯消费块（首条非噪声指令 RETURN_*/Name 目标 STORE_* 且无续接指令——含续接语句不认领，防吞臂内后续语句）；⑤重建 `Return(IfExp(test,body,orelse))` / `Assign(Name, IfExp)`，cond 前导协议噪声剥离（POP_TOP = subject 残余丢弃、NOP = [B16] 显式 case 体标记）。判据 = 「判定位块值被臂内 STORE/RETURN 消费（块内 opcode 序）⇒ 表达式位」（B46 判据族 match 臂适用位）。
2. **调用点**：`_generate_match` case 体块走查的 IfRegion 派发分支前置（`_generate_region` 前），命中即整臂块集标记 generated（cond/then/else/merge 四块 + if_region.blocks）。

### 自测读数
- **B77_face（r7_08）：7/8 → 8/8**（t_host_match_case 转 MATCH，其余 7 单元维持）。
- 负对照（match 域全探针）：B103_main 10/13、B103_guard 5/8、B113_host 12/14、B98_matrix 7/15——与 b99_full 基线逐探针持平（`r8v8fixB_repro_b77_check.json`）。
- 首版落地教训（如实登记）：调用点首版误写 `case_blocks`（实际臂块集变量名 = `body`）→ NameError 被走查外层 except 吞掉致 match 节点整体丢失（r7_08 7/8→更差形态）；修正后 8/8。属实现 bug 非判据问题，无树中残留。

### 代码已落地（I.6）
- `region_ast_generator.py`：`_try_build_match_case_ternary_stmt` 新增（≈:36400-36543，六项模板 + C1/C2/C3 全声明）；`_generate_match` case 体走查 IfRegion 派发前置调用（≈:37292-37308，[B77] 注释块）。

证据：`r8v8fixB_repro_b77_check.json`（B77_face 8/8 + match 域负对照持平）。

---

## §7 B78：条件位融合三元（移交，判据分析在案）

### 破口回顾（round8 REVIEW.md §3.1 行 #2；前任位A FIX_A.md §5 移交）
`while/if 条件位`融合嵌套三元（v_while_cond_nest / v_if_cond_nest）+ `for 体 append 位`融合嵌套三元（n_for_body_nest）——v_b46_face 1/4（模块 docstring 单元 success，三个函数单元全败）。

### 本批亲跑分析（dis + 区域树 dump，新增判据事实；未硬修）
1. **条件位形态**（`if (a if f1 else b) if (c if f2 else d) else 0:`）：CPython 把整棵三元判定树**融合**进 if 的真值测试——每叶值（c/d/a/b）自带 POP_JUMP_FORWARD_IF_FALSE 直跳 if 假出口，真路径经 JUMP_FORWARD **hop 块**汇入 then。区域树：全树被 IF_ELIF_CHAIN 语句区域整体认领（识别层 `_detect_ternary_pattern` 的 JUMP_FORWARD 终结校验对融合叶不匹配，无 TernaryRegion），错构为 pass 体 if 链。
2. **hop 块 = 三元链 vs 嵌套 if/and 链的判别元（实测）**：`if X if C else 0:` 与 `if C:\n if X:` 的字节码**不同**——三元形的 falsy 叶路径经裸 JUMP_FORWARD hop 块汇入 if 假出口（`else 0` 的常量 0 被折叠为跳转、**LOAD_CONST 不在字节码中**）；嵌套 if 形叶路径直跳。⇒ 反编译必须重建三元形态，嵌套 if 替代输出验证必败。
3. **折叠常量合成**：`else 0`（falsy）/`else 1`（truthy）的常量不在字节码中（编译器把常量真值折叠进跳转结构），重建时需合成任意同真值常量（0/False、1/True 重编译逐指令一致，验证实测候选 A 重编译 == 探针字节码）。
4. **append 位形态**（`out.append((x if f1 else 0) if (x if f2 else 1) else 2)`）：内层 X=(x if f1 else 0) 已正确建 TERNARY [46,50,54,60]；外层 T 与 C=(x if f2 else 1) 未建区——C 的钻石被融合（C 的 then 值 x 在 @42 自带真值测试跳 T 的 else 块 58；C 的 else 1 truthy 常量折叠为 f2 假边直跳 X 求值）⇒ T 级被 IF_THEN_ELSE 语句区域认领，C 无认领者。
5. **判据方向（B46 判据族条件位/值位适用位）**：融合三元链签名 = 叶值块末 POP_JUMP_FORWARD_IF_FALSE ∧ 假目标 ∈ {if 假出口, T-else 值块} ∧ 真路径经单 JUMP_FORWARD hop 汇合 + 折叠常量合成位（falsy → 0 / truthy → 1）。修复点：识别层 `_identify_ternary_regions`/`_is_ternary_block` 融合叶放行（JUMP_FORWARD 终结校验扩展为「POP_JUMP 叶 + hop 汇合」同构签名）+ 生成层 IfRegion/调用实参条件重建内联嵌套 IfExp——跨层协作量大，单批零回退收敛范围外（与位A评估一致）。

### 移交登记（如实）
- **未落地代码**（零 hunk）；本批贡献 = 上列判据事实（hop 判别元、折叠常量合成、A/B 字节码差异实测、两形态区域树/块布局在案）。
- 已排除方向：①嵌套 if/and 链替代输出（字节码不同，验证必败，见 2）；②生成层单独内联（无 TernaryRegion 载体，条件重建入口拿到的只是链首块）；③`_try_build_andor_boolop_from_ternary` 式生成层就地重建（融合树无钻石形状可签名，判据不可表达）。
- 探针读数维持 1/4（`r8v8fixB_repro_b78_handover.json`）。

证据：`r8v8fixB_repro_b78_handover.json`、`d:\Temp\opencode\b78_dump.txt`（v_if_cond_nest 块/区域布局）、`b78b_dump.txt`（n_for_body_nest）——后两者为会话临时产物，判据事实已转录上文。

---

## §8 B79：嵌套双层 finally×continue（移交，判据分析在案）

### 破口回顾（round8 REVIEW.md §3.1 行 #3；前任位A FIX_A.md §5 移交）
`for r in rows: try: try: if r == 0: continue; finally: out.append(1); finally: out.append(2); out.append(r)`（v_b71_face::v_nest_fin_continue）——内层 finally 正常路径副本与 continue 路径副本被误装配进 try 体（append(1) 双发、嵌套层级错位、continue 蒸发）。

### 本批亲跑分析（区域树 dump 新增事实；未硬修）
块布局（dump 在案）：内层 finally 三副本 = @32（continue 路径）/ @120（正常路径）/ @164+@210（异常路径）；外层 finally 三副本 = @74（**continue 路径，块尾 JUMP_BACKWARD → for header @10 = continue 回边**）/ @216（正常路径）/ @262+@308（异常路径）。区域树：**两个重叠 TRY_FINALLY**（entry=@18 blocks=[18,30,32,74,118,120,164,210,262,308] 与 entry=@30 blocks=同集+216）——内/外层域的块集合划分本身交叉混装（entry=18 域吞了外层异常副本 262/308，entry=30 域吞了内层全部+外层正常副本），生成层在混装分区上装配必然错位。
- 判据方向（dispatch 在案）：continue 回边目标与循环 header 块同一性（@74 尾 JUMP_BACKWARD→@10）+ finally 域成员关系 ⇒ @74 是外层 finally 的 continue 路径副本（发射归属 = 供 Continue 语义边重建，禁作语句发射）；@32 是内层 continue 副本。B71 边类型封闭判据（fb ∉ pred.exception_successors）外推：@32/@74 前驱全为正常边（continue 路径），@164/@262 前驱全为异常边。
- 已排除方向：①单改 `_generate_try` 副本选择（分区混装在识别层 `_identify_try_except_regions` 的嵌套 try 块集合划分——两个重叠 TRY_FINALLY 的 try_blocks/finally_blocks 未按内/外层分离，生成层拿到的是混装输入，单侧收紧无合法输入可用）；②B83 的 `_find_finally_normal_copy_blocks` 锚点过滤（外层域的可达集交子在环体下同样被 try_blocks 过滤保护，但对嵌套双层分区无效——分区问题先于锚点问题）。
- **移交**：识别层嵌套 try 分区修复（`_identify_try_except_regions`，位A 领地）+ 生成层 continue 副本归属消费，两段协作；本批零 hunk。
- 探针读数维持 3/4（`r8v8fixB_repro_b83_try1.json`）。

---

## §9 B80：finally 条件段 × else 臂 import × handler return（移交）

### 破口回顾（round8 REVIEW.md §3.1 行 #4；前任位A FIX_A.md §5 移交）
v_b73_face::v_imp_cond_fin 2/3——finally 条件段（`if fh: closer(fh)`）被复制进 except 臂且 `return fb(str(e))` 退化为表达式。

### 移交登记（如实）
- 本批未及（B98/B77/B83/B82 优先级消耗配额）；判据方向 = FIX_A.md §5 在案：「尾随块前驱仅含 finally 域末块 ⇒ 归 finally 域；多前驱汇合块禁止复制到多域（前驱集合 + finally_copy_blocks 键集）」，消费点 = 生成器 handler/finalbody 装配（`_generate_try` finalbody 分支 + `_find_finally_normal_copy_blocks` 出界校验的邻域）。
- 本批落地的 [B82] 无条件副本消费与 [B83] 锚点过滤均未触及该单元（B80_face 2/3 持平，`r8v8fixB_repro_b83_try1.json`）。

---

## §10 B82：B75 残留（部分封闭）

### 破口回顾（round8 REVIEW.md §3.1 行 #6）
两臂 return 互换（v_swap_arm_returns）+ finally 无条件段 × except 臂 return（n_fin_noseg）。

### 根因（亲跑 dis + 区域树 dump）
1. **n_fin_noseg（无条件段子型）**：`finally: print("done")` 无条件段——每条臂 return 路径的无条件副本是**裸块**（无 IfRegion 包装：handler 副本 @82 = [print 调用; POP_TOP; LOAD_CONST 'miss'; RETURN]，try 臂副本 @28 = [print 调用; POP_TOP; RETURN]，值由前驱值尾块压栈）。[B75] 预归约只扫 IfRegion 候选（条件段副本），裸块副本无人消费 ⇒ handler 臂把副本+return 整块发射（`print('done'); return 'miss'`）。
2. **v_swap_arm_returns（两臂互换）**：`try: return "miss"` 的**整条 return 路径被 CPython 布局在函数入口（offsets 0-56，含 finally 条件段副本 if _CACHE: print("hit")），位于异常表区间之外 ⇒ 识别层 try 区域（entry=@58=分派块）的 blocks 完全不含 try 主臂路径**，B75 预归约的 region.blocks 成员判据必不命中，副本块被顶层 if/else 语句路径发射（`if _CACHE: print('hit'); return 'miss' else: return 'miss'` + 幻影 try: pass）。

### 守卫设计（[B82-H1] 已落地；判据 = 剥噪序列同构，块内 opcode 序 + 块末 opcode，I.4 白名单）
`_b75_consume_arm_return_copies` 扩展**无条件段副本裸块扫描**（IfRegion 扫描之后）：①块 ∈ region.blocks ∧ ∉ 硬保留集 ∧ ∉ 其它 Try 域；②以 RETURN 终结且未 generated；③剥噪+剥 RETURN 尾后的 opname 序列以 _exc_seq 为前缀（指令级同构）；④前驱守卫：外部前驱 ∈ try_blocks 且为**纯值尾块**（无前置语句 boundary==-1 ∧ 以值生产指令收尾——控制终结（POP_JUMP_*/FOR_ITER/MATCH_*/SEND）收尾的前驱是 try 体结构块，拒绝）⇒ try 臂（Return 值 = 值尾重建）；外部前驱经透明块链回溯到 CHECK_EXC_MATCH ⇒ except 臂（Return 值 = 本块 RETURN 前装载尾重建；装载尾为空（SWAP 保栈形态）拒绝——归约不完整不半应用，C3）。命中后副本块标记 generated、臂 Return 挂同键瞬态属性（_b75_try_arm_returns/_b75_handler_returns，与 [B75] 同键约定）。
- **三道收紧（回归修复实测驱动）**：收紧1（boundary>=0 拒绝）——值尾块含前置用户语句时整块替代吞语句（实测 r8_ret_finally_overwrite 丢 `r = xs[i]`，首版回退后还原）；收紧2（POP_JUMP_*/FOR_ITER/MATCH_*/SEND 收尾拒绝）——副本与 then 臂融合、前驱为 if 条件头的形态（实测 r8_dh_try_finally_return 蒸发 if+raise，首版回退后还原）；收紧3（SWAP 保栈空装载尾拒绝）——防错值 Return(None) 替换正确臂发射。

### 自测读数
- **B82_face：1/3 → 2/3**（n_fin_noseg 转 MATCH：`except KeyError: return 'miss'` + finalbody `print('done')` 正确；v_swap_arm_returns 维持失败——识别层移交）。
- 负对照：r8_01_return_positions 11/11、r8_09_deep_host_combo 7/10（两处首版回归经收紧后还原基线）；oldface 665/692（**+1** vs 基线 664，WORSE=0——+1 = B77 外溢 r7_08 8/9）；round1face 417/423、B108_main 14/14、B79_face 3/4、B80_face 2/3、B83_face 2/2 持平。

### 未竟登记
- **v_swap_arm_returns 移交识别层**：try 主臂 return 路径位于异常表区间外（函数入口布局），`_identify_try_except_regions`（位A 领地）的 try 区域块集合不含主臂路径——生成层无合法输入（C1：区域只读自身块集），单侧不可闭合。判据事实：异常表无 0-56 区间条目（finally 副本内 raise 语义正确不入 except）+ try 区域 entry=分派块形态 + 副本序列与 finally 条件段指令级同构。

### 代码已落地（I.6）
- `region_ast_generator.py` `_b75_consume_arm_return_copies`：[B82] 无条件段裸块扫描 + 三道收紧（≈:28084-28260）。

证据：`r8v8fixB_repro_b82_try1.json`（首版 2/3 + 两处回退暴露）、`r8v8fixB_repro_b82_try2/try3.json`（收紧后 2/3 维持 + 回退还原）、`r8v8fixB_repro_b83_try1.json`（族负对照）。

---

## §11 B83：try 体 while 内 raise 镜像块泄漏 finalbody（封闭）

### 破口回顾（round8 REVIEW.md §3.1 行 #7；前任位A FIX_A.md §5 移交）
rvC_v2::drain——`try: while q: ...raise...; finally: sink.append(len(out))` 的 finalbody 被错构为循环体镜像（`v = q.pop(); if v > limit: pass; raise ValueError(v); out.append(v); q`），真 finalbody（sink.append）蒸发。

### 根因（亲跑 trace 核实：`_find_finally_normal_copy_blocks` 返回 [12,64,94] = try 体循环块）
双缺陷（判据均为块结构事实，I.4 白名单）：
1. **可达集交集在含环 try 体下退化为「全体可达」**：`while` 循环体块（@12/@64/@94）经环内互达从每个出口源都可达，被误纳锚点候选集；真副本入口 @140（@94 的 fall-through）被首个候选 @12 的错误序列淹没。
2. **条件回跳 fall-through 丢失**：收集 BFS 把 POP_JUMP_BACKWARD_*（while 回边，条件跳转）与无条件跳转同分支处理（`continue` 跳过后继收集），@94 的 fall-through @140（真副本入口）永不入序列——序列 [12,64,94] 过复合门控（含 IF_THEN 子区域）后作为「正常副本」交 finalbody 装配 ⇒ 循环体二次发射、finalbody 错构。

### 守卫设计（[B83-H1/H2]）
1. **[B83-H1] try 域体成员块不作锚点**：候选 ∈ 可达集交集后追加过滤 `∉ try_blocks ∪ else_blocks ∪ handler 体块`（区域成员关系）——正常副本首块按 CPython 布局在 try 体/handler/else 全部成员之后（W11-A 收敛定义的显式化）；含环 try 体的环内块全部 ∈ try_blocks，被过滤后真副本入口成为唯一候选。
2. **[B83-H2] 条件回跳 fall-through 收集**：BFS 遇 POP_JUMP_*（条件跳转）结尾块时，除跳转目标外一并收集其后继集合中的 fall-through（块末 opcode + 后继集合）；无条件跳转（JUMP_*）无 fall-through 维持原 continue。判据（round8 REVIEW §3 #7 在案）：镜像块前驱 ⊆ exception_successors 来源（异常边）⇒ 留 finalbody；**正常前驱 ⇒ 认领**（@94→@140 是正常边）。

### 自测读数
- **B83_face（rvC_v2）：1/2 → 2/2**（drain 转 MATCH：finalbody = `sink.append(len(out))` 正确，try 体 while 唯一发射）。
- 负对照：B108_main 14/14、B79_face 3/4、B80_face 2/3、B82_face 1/3（修复时点）全持平；round1face **417/423**、residual **419/446**（+1 = B77 外溢）、oldface **665/692**（+1 同）——W11/W13 既有面（op_station/user_log_control/main.pyc 形态经 oldface/residual 面覆盖）零回退。

### 代码已落地（I.6）
- `region_ast_generator.py` `_find_finally_normal_copy_blocks`：[B83-H1] 锚点 try 域过滤（≈:29748-29776）+ [B83-H2] 条件回跳 fall-through（≈:29798-29818），判据注释块齐全。

证据：`r8v8fixB_repro_b83_try1.json`（B83 2/2 + 族负对照持平）。

---

## §12 自测门禁读数（定稿批量重放）

| 门禁 | 读数 | 判定 |
|------|------|------|
| 攻击面全量重放（31 探针，`r8v8fixB_repro_final.json`，R8FB_STAMP=final） | 297/357；对 b99_full 基线逐探针：**BETTER={B77_face +1、B82_face +1、B83_face +1、B98_matrix +1}，NEWFAIL=0**（B98_matrix 的 compare_cross/and_tail_or_group 为同单元失败模式位移 control flow→bytecode，非新增失败单元） | 通过 |
| round1face | **417/423**（§0.2 回退修复后 = 基线；trade_info_utils 36/41 剩 5 基线存量失败） | 通过 |
| round2face | **238/251**（基线 235/251，**+3** = B77/B82/B83 已封闭单元正向外溢，WORSE=0） | 通过（改善） |
| probe42 | **176/196**（= 基线） | 通过 |
| residual | **419/446**（基线 418/446，**+1** = B77 外溢 r7_08 7→8；a 252/277 + b 167/169） | 通过（改善） |
| oldface | **665/692**（基线 664/692，**+1** = B77 外溢；a 218/227 + b 447/465；B82 首版两处回退经三道收紧后还原） | 通过（改善） |
| quotation | **152/153**（唯一失败 change_his_to_forward 基线一致） | 通过 |
| 34 小测试集（8 分片，`r8v8fixB_34set_shard0-7.json`） | **1505/1568**，NEWFAIL=0（对 failing_index 逐文件：WORSE=0；jq_trans_module/trade_live_broker/quote 三件 +8 为前序轮次改善的陈旧索引差，34 集操作基线 1505 持平） | 通过 |
| IV.2 自检 | py_compile 两涉改文件通过；import OK（全部探针/站桩运行隐式验证）；BOM 单头（region_ast_generator/region_analyzer head3=efbbbf count=1）；**本批新增调试插桩 0**（diff 新增行 print=0）；G3 新增前缀方法 0；G4 新增硬编码上限 0（[B82] 透明链回溯 `_steps < 8` 为 [B75] 落地存量同型镜像，同常数同语义） | 通过 |
| 命令时限 | 全部命令 ≤300s（34 集 8 分片、residual/oldface a\|b 分片） | 通过 |

---

## §13 代码已落地声明（I.6）

本批（续作五）全部代码已落地，树中 grep 标记核验：

| Hunk | 锚点（file:line） | 标记 |
|------|------------------|------|
| §0.2 P0 回退修复：[B99-C3] 提交收紧 | `core/cfg/region_analyzer.py` `_detect_boolop_short_circuit_chain` ≈:30700-30731（签名 `_b99_absorb` + 门控 + 判据注释）、≈:30966-30983（锚点入链检查 + 无吸收重走） | `[B99-C3 提交收紧]` |
| §5 [B98-R1-H1] 镜像极性共享块重建 | `core/cfg/region_ast_generator.py` `_try_build_orprefix_and_boolop_from_ternary` ≈:42537-42649（新增方法，六项要素 + C1/C2/C3） | `[B98-R1]` |
| §5 [B98-R1-H2] [R38] 包裹豁免门 | 同文件 `_generate_ternary` ≈:43701-43740（镜像调用点 + [R38] `_b98_andor_expr is None` 门 + [P1-2] 调用门） | `[B98-R1 镜像极性]` |
| §6 [B77-H1] 臂内值钻石重建 | 同文件 `_try_build_match_case_ternary_stmt` ≈:36395-36543（新增方法，六项模板 + C1/C2/C3）；`_generate_match` case 体走查派发前置 ≈:37292-37308 | `[B77]` |
| §10 [B82-H1] 无条件段副本裸块扫描 + 三道收紧 | 同文件 `_b75_consume_arm_return_copies` ≈:28084-28260 | `[B82]`/`[B82-收紧]`/`[B82-收紧2]`/`[B82-收紧3]` |
| §11 [B83-H1] 锚点 try 域过滤 | 同文件 `_find_finally_normal_copy_blocks` ≈:29748-29776 | `[B83]` |
| §11 [B83-H2] 条件回跳 fall-through 收集 | 同文件 同方法 ≈:29798-29818 | `[B83]` |

- 涉改文件 = `core/cfg/region_analyzer.py`（+93/-41：§0.2 唯一 hunk）+ `core/cfg/region_ast_generator.py`（+510/-41：§5/§6/§10/§11）；`ast_generator_v2.py` 零改动。
- 位A B121/B109 守卫未动；R8CDBG 插桩（位C遗留）未动；探针 .py 源/pyc 零改动。

---

## §14 未竟项与移交（如实登记）

| 项 | 状态 | 移交原因与已排除方向 | 判据事实贡献 |
|----|------|---------------------|-------------|
| B98-R2 表达式位交叉（matrix 4 单元） | 移交 | 消费点（return/compare/walrus/call-arg/外层三元 then 臂）各自需独立重建路径（§5 未竟表逐项）；M1 前缀豁免实验证伪（吸收成链后 fat merge 建区吞语句，get_last_stat 反退——已回滚） | §5 未竟子形态表 + 验伪记录 |
| B98-R1 尾组多组/条件位 or 尾 | 移交 | `_build_boolop_expression` 对 and-region 含嵌套 or 子组的两值分组重建 + or 尾 IfRegion else 臂归属（§5） | §5 |
| B98-R3 宿主交叠（hosts 5 单元） | 移交 | 与 R2 同源消费点形态，宿主不引入新机制（§5） | §5 |
| B44 存量（resid 3 单元） | 移交 | ≥3 层双入口归纳分支链嵌套右臂（round3 判据草案），工程量大独立批次 | §5 |
| B78 条件位融合三元 | 移交 | 融合决策树重建需识别-发射协同重构（与位A §5 评估一致）；**本批新增判据事实**：hop 块 = 三元链 vs 嵌套 if/and 判别元（A/B 候选字节码实测）、折叠常量合成（else 0/1 不在字节码中）、两形态区域树/块布局 | §7 |
| B79 嵌套双层 finally×continue | 移交 | 识别层嵌套 try 分区混装在案（两重叠 TRY_FINALLY 块集合交叉）；continue 副本判据（@74 尾 JUMP_BACKWARD→header 同一性 + B71 边类型外推）已核实待识别层修复后消费 | §8 |
| B80 finally 条件段×else import | 移交 | 本批未及（配额消耗于优先级更高族）；FIX_A §5 判据在案 | §9 |
| B82 v_swap_arm_returns | 移交识别层 | try 主臂 return 路径布局在异常表区间外（函数入口 0-56），`_identify_try_except_regions` 的 try 区域不含主臂路径（位A 领地），生成层无合法输入 | §10 |
| B99-M1 前缀豁免 | 证伪归档 | §5 验伪记录在案（方法论存证） | §5 |

### 纪律声明（本续作批）
- 涉改文件边界遵守（见 §13）；禁改文件零改动；探针 .py/.pyc 零改动。
- 零 git 写操作（主代理职责）；regen 副作用（tracked `*OK.py` M态）结束时统一 `git checkout --` 还原。
- 修复期临时实验（[B98-EXPERIMENT] ternary 头守卫、M1 豁免）均已在定位结论后完整回滚，最终 diff 中零残留；会话临时 dump 脚本（r8v8fb_dump2.py/r8v8fb_ternctx.py）为调查驱动，留 rounds/round8/ 供复审（非 core 插桩）。
- 全部命令 ≤300s。
