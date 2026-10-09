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
| 4 | **B99 残** for 宿主 BoolOp return | B99_min | 8/9 | （在途） | |
| 5 | **B98 拆分** 分组 boolop | B98_matrix / B98_hosts / B98_resid | 5/15、11/18、2/5 | （在途） | |
| 6 | **B77** match 臂三元 return | B77_face | 7/8 | （在途） | |
| 7 | **B78** 条件位融合三元 | B78_face | 1/4 | （在途） | |
| 8 | **B79** 嵌套双层 finally×continue | B79_face | 3/4 | （在途） | |
| 9 | **B80** finally 条件段 × else 臂 import × handler return | B80_face | 2/3 | （在途） | |
| 10 | **B82** B75 残留两臂 return 互换 | B82_face | 1/3 | （在途） | |
| 11 | **B83** 循环体镜像块泄漏 finalbody | B83_face | 1/2 | （在途） | |

### §0.1 任务 0：插桩清零 + B108/B111 注释合规（已完成）

- **R8FIXBDBG 插桩 2 处已删**（region_ast_generator.py ≈L29115-29117 child walk print + ≈L31242-31246 finalbody legacy print，含 `_os_r8fb`/`_os_r8fb2` import 行）；grep `R8FIXBDBG` / `_os_r8fb` 全树零命中。
- **B108/B111 docstring 合规修正**（以代码真实算法为准，I.7；触及方法 4 个）：
  - `region_ast_generator.py _generate_try_body`（:27956 docstring）：③唯一归属判定补声明 [B108] finally 体 normal path 副本 ternary 跳过守卫（entry ∉ finally 块集 + 等块数 sibling ∈ finally 块集 ⇒ 副本 ⇒ 标记 generated 唯一归属 finalbody）+ handler/else 块集跳过守卫——原 docstring 未声明该行为，属「注释与代码行为不一致」，已修正注释。
  - `region_ast_generator.py _generate_handler_body_statements`（:31882 docstring）：③补声明 [B108] DELETE_FAST/NAME/GLOBAL/DEREF → Delete([Name(ctx='Del')])、DELETE_ATTR/DELETE_SUBSCR 经 _build_delete_stmt，及 as-var 清理守卫（本块内紧邻前驱 LOAD_CONST None + STORE 同名）不发射——原 docstring 未声明 DELETE 语句分支。
  - `ast_generator_v2.py _process_instruction`（:223）：docstring 由单行「处理单条指令」补齐六项模板 + C1/C2/C3（③声明 [B111] 加载指令族含 LOAD_CLOSURE/LOAD_CLASSDEREF；C2 声明与 _load_instr_to_ast 同集同语义）。
  - `ast_generator_v2.py _load_instr_to_ast`（:2388）：docstring 由单行补齐六项模板 + C1/C2/C3（③声明 [B111] cell 引用族，未知 opcode 显式占位符豁免）。
- **复验**：B108_main 14/14、B111_main 28/28、B111_cross 22/22 维持（`r8v8fixB_repro_task0_check.json`）。

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

## §4 B99 残：for 宿主 BoolOp return（在途）

（待补）

---

## §5 B98 拆分：R1/R2/R3 + B44 存量（在途）

（待补）

---

## §6 B77：match case 臂内三元 return（在途）

（待补）

---

## §7 B78：条件位融合三元（在途）

（待补）

---

## §8 B79：嵌套双层 finally×continue（在途）

（待补）

---

## §9 B80：finally 条件段 × else 臂 import × handler return（在途）

（待补）

---

## §10 B82：B75 残留（在途）

（待补）

---

## §11 B83：try 体 while 内 raise 镜像块泄漏（在途）

（待补）

---

## §12 自测门禁读数（定稿前批量重放，在途）

（待补）

---

## §13 代码已落地声明（I.6）

（待补）

---

## §14 未竟项与移交（如实登记）

（待补）
