# Round 9 修复批次 FIX_R9（任务 9.2，算法修复，不 git commit）

- 基线 = REVIEW_DRAFT §1 站桩新基线（合并树 e42b8509 → 本批起始 a2d1e15e）；判据唯一 `scripts/pyc_verify.py`，RV2（先 regen `pycdc -o` 再 verify single）
- 纪律 = 只动 `core/cfg/region_analyzer.py` / `region_ast_generator.py` 的归约算法判据面；禁止回滚合并调和 hunk [B104-R3]/[B99 收窄]/H1-H4（REVIEW §4 承重实证）；I.4 白名单判据、I.6 落地声明、I.7 注释同步；命令 ≤300s 分片；regen M 态 `*OK.py` 终态 `git checkout --` 还原；插桩用完即删
- 工作队列 = §6 派发：位0（B124 四臂归属）→ 位A（B104 while 链族 14 单元）→ 位B（B125）→ 位C（B126）→ 尽力项（B127/B128/B44/Yield 探针）
- 9.3b 整改（REVIEW2 处置：R-1 方案 a 移除 [B126-R1]、R-2 合计口径对齐 2161/六面、R-3 改可复核表述 + 行 104 g2 校正）：详见 §3 末段与 §5 末段；证据前缀 `r9v9fix3b_`

## §0 位0：B124 四臂归属（只读，已完成）

方法 = MERGE_RECORD ana_ab3_r137 同款：字节级备份→改臂→regen+verify→还原→sha256 校验（每臂）；靶 = B124 五单元（e05×3 + e10×1 + r8_10×1）。

**证据**：`r9v9fix_b124_4arm.json`（control/off_b104r3/off_b99/off_h3/成对臂/off_all3/v3tip/v2tip/v2a_mg/ma_v2g 全臂读数）。

| 臂 | e05 | e10 | r8_10 | 判定 |
|---|---|---|---|---|
| control（全开） | 3/11，B124×3 败 | 31/32，1 败 | 8/12，1 败 | 基线 |
| off_b104r3（关 [B104-R3] released 值位跳过门） | **6/11，B124×0 败** | 31/32 | 8/12 | **e05×3 → [B104-R3]** |
| off_b99（关 [B99 收窄]）/ off_h3（关 [R21-15]+[R21-36] 臂尾提升） | 不变 | 不变 | 不变 | 非单因 |
| 成对臂/off_all3 | e05 同 off_b104r3 | 不变 | 不变 | 非组合因 |
| v3tip（两文件=v3 tip 996a1b1a/566ff5c5） | 4/11，B124×3 败 | 31/32，1 败 | 8/12，1 败 | **v3 tip 同败 ⇒ 非合并新增而是 v3 侧代码 + v2 独占覆盖未被组合恢复** |
| v2tip（两文件=91f8d27d） | 6/11，B124×0 败 | 32/32 | 9/12，B124×0 败 | v2 tip 全绿复核 |
| v2a_mg（v2 ana + merged gen） | 0/11 | 0/32 | 0/12 | 整体不相容（合并树 gen 依赖合并树 ana 元数据），无归属信息 |
| **ma_v2g（merged ana + v2 gen）** | 3/11（B124×3 仍败） | **32/32** | **9/12（B124×0 败）** | **e10×1 + r8_10×1 → generator 桶** |

**归属结论（修正 REVIEW §5 B124 的「4-arm 待归属」）**：
- B124 拆双桶：e05 三单元（f_compare_chain6/f_compare_binop_inside/f_compare_subscript_inside）→ **analyzer 桶**（[B104-R3] released 值位跳过门对嵌套宿主值位链过宽，与 matcher 承重门（cf_b99_r143/battery nb_for/nb_with）同文件不冲突）；e10 f_call_ternary_arg + r8_10 r8_x_with_ternary → **generator 桶**（调用实参位 IfExp 重建，v3 tip 亦败 = v2 独占覆盖被 v3 生成层重构覆盖后未恢复）。
- 双树定性修正：五单元并非「v2 tip 全绿 ⇒ 合并新增」的调和缝隙——v3 tip 亦红 ⇒ 属 v3 侧存量代码在合并树原样保留；v2 的独占覆盖在冲突调和时未被并列。修复向 = 判据面扩门（恢复 v2 覆盖 + 保留 v3 门），非回滚任何 hunk。

## §1 位A：B104 while 条件位链式比较族（14 合并新增单元 + w3_nostore 存量）

**根因（诊断实据 `r9v9fix_diag_*.py` 驱动 + [T] 插桩追踪）**：CPython 3.11 旋转 while 的**入口**条件段块（cond_block）可携带循环前缀语句（`n = 0; while 0 < x < n < 100:` 的初始化赋值被识别层条件块搜索并入链头块），而**回边**副本所在体块的尾段按语句边界（末条 STORE_*/POP_TOP 之后）截取、永不含前缀语句 ⇒ [R21-66] SEG 副本身份判据的全块变体永不相等（实测 chain4/e08_while 全族 `latch_copy=False`），路 B（`_is_recheck and latch_copy and boundary==store`）永不命中 ⇒ 重检副本泄漏为体语句幻影 `if 0<x<10: pass` / `if 0<x and n<True: ... elif n<100:`。第二缺口：路 B 的单段 `_build_store_statement` 只重建单语句，多语句前缀（`x += 1; n += 1`）丢码。第三缺口（w3_nostore，存量 R4）：`out.append(x); x += 1` 闩锁块中 POP_TOP 结尾的表达式语句与赋值并段，重建只存赋值、表达式语句蒸发。

**修复（region_ast_generator.py，三处扩门 + 一处因子化，「代码已落地」）**：
1. `[B104-R9 语句前缀变体]`：SEG 集追加「末条 STORE_*/POP_TOP 语句边界之后的求值尾段」变体（与体块尾段截取方式对称，同一终结 opcode 族；无前缀段块边界 -1 不产生新项，既有全块变体全保留，加性扩门）。锚点 = `_r2166_seg_set` 构造环内（`_loop_generate_while` cc 分支，`region_ast_generator.py:8649-8659` 一带）。
2. `[B104-R9 混合操作数求值段集]`：`_r2166_mixed_seq_set` = 识别层 [B104-R2a] 操作数块的条件求值段（`_b104r2_cond_eval_seq`，与路 A 同一判据），并入 case C 回边纯重检身份集（`and flag` 尾块等）。
3. 路 B 多语句前缀改用 STORE 边界多段抽取器 + `[B104-R4]` POP_TOP 表达式语句终结符并入切分集（split_expr_stmts=True；路 A 不传此参、v2 语义逐位不变）。
4. 路 A 内联抽取器因子化为 `_extract_recheck_store_stmts`（六项 docstring + C1/C2/C3 声明齐全），路 A 调用参数缺省 = 段切分/重建序与 v2 原内联实现逐位一致；路 B 单语句前缀逐字节同既有行为。

**读数（before → after，证据 `r9v9_repro_r92pre_b104.json` → `r9v9_repro_r92fixA2_b104.json` / `r92fixA_b104.json`）**：

| 探针 | before | after |
|---|---|---|
| B104_main（c4_09） | 12/14 | **13/14**（e08_while 翻正；CCMP.m = with 宿主值位链 → B124 分析器桶，§2） |
| chain4 电池 | 4/6 | **6/6** |
| chain5 电池 | 2/5 | **5/5** |
| opdeep 电池 | 2/4 | **4/4** |
| exprtail 电池 | 2/5 | **4/5**（v1/v2 翻正；v3 = B123 存量，§4 移交） |
| foror 电池 | 3/3 | 3/3 |
| n9_whilehost | 5/9 | **9/9**（w3_plain/w3_deep/w3_and 翻正 + 存量 w3_nostore 翻正 = B104-R4 一并封闭） |

- **B104 while 条件位族 14 合并新增单元全转 MATCH，存量 R4（w3_nostore）一并封闭**。
- 承重面（`r9v9fix_bearing.json`）：broker 128/128、matcher 17/17、finance success（single 32/32，402 批量口径 132/132 由 34 集复核）、quote_handler 79/79、realtime 13/13、quotation 153/153、nb_for 2/2、nb_with 2/2、nb_b99 4/4 全绿。
- I.4 白名单核验：全部判据 = 块内 opcode 序 + 语句终结 opcode 族（STORE_*/POP_TOP/UNPACK 计数）+ 既有 `_b104r2_cond_eval_seq`；零名字/偏移/阈值/跨层反查。G3：新增方法 `_extract_recheck_store_stmts` 无禁前缀。

## §1.5 位0 续：B124 双桶修复（分析器桶 + 生成器桶，「代码已落地」）

**分析器桶（e05×3 + c4_09::CCMP.m，region_analyzer.py）**：根因 = [B104-R3] released 值位跳过门对「自足 return 链」形态过宽——该形链求值钻石的 merge 块 = 链清理指令（SWAP/POP_TOP/COPY/NOP；with 宿主另编入 `SWAP+LOAD_CONST None×3+PRECALL+CALL+POP_TOP` 退出协议）+ RETURN_VALUE 终结，链与 return 构成一条完整自足语句，认领不抽走宿主语句流；而 matcher 值位赋值形（merge 以 STORE_* 开头，[R50] 口径）认领会抽走语句流（实测 gate-off matcher 17→16，`r9v9fix_diag_gateoff.json`）。修复 = 门后移 + **[B124-R1 自足 return 形扩门**（`_b124r1_chain_region_is_self_return`：merge 块 RETURN_VALUE 终结 ∧ 其余指令全在 {SWAP, POP_TOP, COPY, NOP, LOAD_CONST, PRECALL, CALL} 清理/协议族（无名字加载/STORE/用户操作）⇒ 放行认领恢复 v2 覆盖；否则维持 v3 跳过）。`_build_chained_compare_region` 为纯构造（无 self 副作用），先建后判对未命中门的块逐位不变；`_identify_chained_compare_regions` docstring C3 段同步（I.7）。

**生成器桶（e10::f_call_ternary_arg + r8_10::r8_x_with_ternary，region_ast_generator.py）**：根因 = [T19-4] 宿主调用前缀跨度两处越界（[T]/[W] 插桩实证，`r9v9fix_diag_t194.txt`/`r9v9fix_diag_withtern.txt`/`r9v9fix_diag_withitem.txt`）：① e10 形——旧 3.11 pyc 的 IfExp 编译约定为非弹跳 POP_JUMP + merge 处 SWAP(2)+POP_TOP 对清理保留测试副本，栈模拟按弹跳约定计残差，把该 POP_TOP 误当语句终结（close op=POP_TOP off=80）⇒ RETURN_VALUE 被切进尾段 ⇒ 产物 = `sink(a if b else c)` 裸表达式 + 幻影 `return None`；② r8_10 形——merge 链游走越过 BEFORE_WITH with 协议边界一路吞到函数尾 RETURN_VALUE@130 ⇒ 三元归约输出整条 Return ⇒ `_resolve_nested_ternary_context_expr` 只接受 Expr/Assign ⇒ 退化占位 `context()`。修复 = **[B124-R2a 连接清理对守卫**（闭合候选 POP_TOP 同块紧邻前指令为 SWAP(arg==2) ⇒ return None）+ **[B124-R2b with 协议边界守卫**（模拟体含 BEFORE_WITH/BEFORE_ASYNC_WITH ⇒ return None）；两守卫命中即退回无 [T19-4] 的既有路径（v2 覆盖在案，four-arm ma_v2g 实证该形正确渲染：e10 32/32、r8_10 9/12）。`_ternary_host_call_prefix_span` docstring 判据第 4 条同步（I.7）。

**读数（before → after，证据 `r9v9fix_pre_b124_b126.json`（修复前）→ 修复后现值 = 同驱动重跑）**：

| 探针 | before（合并树 §1 后） | after | 说明 |
|---|---|---|---|
| e05_g3_compare_chain | 3/11 | **6/11** | B124×3（chain6/binop/subscript）转 MATCH = v2 tip 同读数；余 5 败 = is/in/walrus/in_cond/notin（v2 tip 亦败，存量非合并新增） |
| c4_09_chained_compare | 13/14 | **14/14** | CCMP.m（with 宿主值位链）翻正 |
| e10_g7_call_args | 31/32 | **32/32** | f_call_ternary_arg 翻正 |
| r8_10_expr_cross_stmt | 8/12 | **9/12** | r8_x_with_ternary 翻正；余 3 败 = assert/for_iter/raise_ternary（v2 tip 亦败，存量） |
| b104_exprtail_battery | 4/5 | 4/5 | v3 = B123 存量，§4 移交 |

- **B124 五单元全转 MATCH**（§0 四臂归属的 4+1 全部封闭；第五单元 r8_10::r8_x_with_ternary 同步翻正 ⇒ residual/oldface 两面的 WORSE=1 消除）。
- 承重面（`r9v9fix2_bearing.json`）：broker 128/128、matcher 17/17（[B104-R3] 门保真）、finance 32/32、quote_handler 79/79、realtime 13/13、quotation 153/153、nb_for 2/2、nb_with 2/2、nb_while 2/2、nb_b99 4/4 全绿。
- I.4 白名单核验：两处判据全部 = 块内指令 opcode 序（merge 块清理/协议族、SWAP(arg==2)+POP_TOP 邻接对、BEFORE_WITH 族）+ 区域成员关系；零名字/偏移/阈值/跨层反查。G3：新增方法 `_b124r1_chain_region_is_self_return` 无禁前缀；两守卫为既有方法内加性 return None（未新方法）。

## §2 位B：B125 嵌套循环宿主 while-else 蒸发（2 单元，「代码已落地」）

**根因（[A]/[B] 插桩实证，`r9v9fix_diag_b125.txt` + `dump_loop.py` 区域 dump）**：`_loop_generate_while` 的 else 块渲染（region_ast_generator.py:9056 一带）做「else 块由子区域持有 → 跳过并经其 entry 递归生成」的全局区域扫描时，**未区分祖先与子区域**——祖先循环的 blocks 是含全部嵌套后代块的超集，嵌套 while 的 else 块必然同时登记在祖先 blocks 里，被误判为「子区域持有」而跳过；`_r2114_else_owned_skipped == len(_filtered_else_blocks)` 随即触发 [R21-14] fallback 把 else_stmts 清空 ⇒ else 臂整臂蒸发。实测：nested_loop_else 的内层 while else 块 42 ∈ 外层 for blocks（`[A] while-else blk@42 gen=False child=True`）、fe_while_deep 的内层 else 块 70 ∈ 外层 while blocks；浅层同形（normal_while/while_else_not_returnnone，无祖先容器）全绿 ⇒ C2 嵌套破口（深层才错）。REVIEW §6 的「`_find_loop_else` break-only 守卫外推」方向不成立——`_find_loop_else` 实测两形均正确返回 else（b109 dump：while else=[42]；fe_while_deep dump：内层 else=[70]），外层 fe_while_deep else=None 是无 break 形的正确不可区分（顺序渲染字节码等价）。

**修复（region_ast_generator.py，[B125-R1 祖先链排除]）**：全局扫描沿 `region.parent` 链收集祖先 id 集，祖先区域不再进入 `_child_region_blocks_r23`（祖先容器 ≠ 子持有证据；子/兄弟区域命中路径逐位不变）。判据 = 区域父子成员关系（I.4 白名单）；注释含识别条件/归约方式/AST 映射 + C1/C2/C3 三行声明。

**读数（before → after）**：

| 探针 | before | after | 门禁 |
|---|---|---|---|
| r4v4r_b109_loopelse | 8/9 | **9/9**（nested_loop_else 翻正） | c4_02 14/14 ✓ |
| r5v5_13_for_else_cross | 10/11 | **11/11**（fe_while_deep 翻正） | r9_01 5/5、r9_09 4/4、r9_10 5/5 ✓ |
| r9w16 while-else 族电池（13/14/17/18/08） | 新编译 | 全 2/2 | `r9v9fix_b125_family.json` |

- **B125 两单元全转 MATCH**（v2 tip 双绿复核恢复）。
- 存量登记（非 B125、双臂同败、如实移交）：r9w16_05_nested_in_for（无限 while-true-in-for，非 else 族）1/2、r6_q2_whilehost_spec（while 宿主 if/else+return，B94 邻接）1/2——[B125-R1] 关闭对照臂同败（`r9v9fix_b125_arm.py`），非本修复引入。
- I.4 白名单核验：判据 = region.parent 链成员关系 + else 块表（区域结构事实）；G3/G4 无新增方法、无阈值。

## §3 位C：B126 assert 链归约吞 while 回边载体（1 单元，「代码已落地」）

**根因（判据实证 + 六变体实验，`r9v9fix3_diag_b126.py` + `r9v9fix3_exp_b126.py` + 新编译探针 `probe_for_assert`/`probe_break_raise`）**：REVIEW §6「AssertRegion 归约以循环回边块为 L(A) 外弃收」方向**证伪**——①analyze 时序 = `_identify_loop_regions`（:1463 调用，:5071 定义）先于 `_identify_assert_regions`（:1466 调用），break 角色在 assert 认领之前已由 :5880 落定，assert 侧收窄不可能触及角色判定；②E3 变体（撤除 assert 认领）产物崩坏级退化（`if a < True: if b: break ... assert False, a`）——认领对 while 链渲染是承重面，非病灶。**真实根因 = break 候选误注册**：`_detect_break_continue`（:7862）[R8]「清理后继」注册点（:8179 `break_blocks_set.add(s)`）对 for×while assert_deep 形把链段假边蹦床 **74/76 注册为 break 候选**——for 自然体 = [32,34,48,64,98,120] 不含 74/76（其唯一出口为纯 RAISE 块 78，不可达回边源 32），蹦床指令仅 POP_TOP/JUMP_FORWARD（清理型）⇒ 旧判据「清理后继且落点体外」全命中；实测 `verified_break_blocks={74,76}` → :5880 `BlockRole.BREAK` → has_break=True ⇒ 幻影 for-else + 体内幻影 break + 死 store。while 侧 74/76 ∈ body 不误注册、逐位正确（同判定面仅 for 漏网；REVIEW §5「回边丢失」表述按实测更正为「回边完好、幻影候选误注册」）。六变体裁决：E3 崩坏；E1（认领扩展）幻影 Break 消除但幻影 else 残留（has_break 未清）；E1b（扩展+清角色）/E4（守卫+扩展）/E6（守卫单点）全对；E5 初版守卫（仅 raise 终结判据）负控 g1（`for: if y: break` 后接 raise）回退为循环内 raise ⇒ 精化加「终点及其余前驱结构域外」条件。取 **E6 判据面**（守卫单点，不做认领扩展；R2 守卫在浅层 r8_assert_chain 上调用计数 0（不触发）⇒ 块归属逐位不变平凡成立，面风险最小；证据 `r9v9fix3b_s3_guard.json`）。

**修复（region_analyzer.py，[B126-R2 异常路径尾闩守卫]）**：`_detect_break_continue` [R8] 注册点前置调用新方法 `_b126r2_raise_only_trampoline_exit(s, body_set, header, natural_exit, for_iter_exit, condition_block, _else_only_set)`（:8174 调用点；:8404 定义）：自 s 沿单普通后继（排除异常边/已访问块）行 ≤8 跳、每跳须清理型（指令全在 NOISE/跳转/条件跳转/短路跳转/POP_TOP/EXTENDED_ARG 族，[R8] `_s_meaningful` 同口径），终点须含 RAISE_VARARGS/RERAISE 且终点及其其余前驱与本循环结构域无关（∉ body/else、非 header/condition_block/natural_exit/for_iter_exit，其余前驱亦须清理型）⇒ 判定为 assert 失败消息路径等**异常尾闩**，不注册；任一条件不满足返回 False 逐位维持既有注册（[R101] 融合形、真 break 落点不受影响）。`_detect_break_continue` docstring 补 [B126-R2] 段（:7914），新方法含六段式 + C1/C2/C3（I.7）。

**读数（before → after）**：

| 探针 | before | after | 门禁 |
|---|---|---|---|
| n9_stmt_sweep | 5/6（assert_deep：幻影 break + 死 store + 幻影 for-else） | **6/6**（while 体 = `assert 0 < a < b, a; a += 1`，for 后 `return a`，无 else） | `r9v9_repro_fix3_b126_impl1.json` |
| probe_for_assert（新编译） | f_for 幻影 else | f_for/f_while 全正确 | `r9v9fix3_exp_b126.py` E6 臂 |
| probe_break_raise（新编译） | g1/g2/g3 基线 | g1 break 保留+后置 raise、g2 渲染存续折叠 `assert y, 'done'`（**非字节等价**：pyc_verify 存量 `Different control flow`；R2-off 同形，非本修复引入，见 §3 末段）、g3 while+raise 保留；全模块 3/4（g1/g3 字节等价） | 同上（E5→E6 精化对照）+ `r9v9fix3b_s3_probe_align.json` |
| r8_07_assert_forms | 10/11 | 10/11（同单元 r8_assert_nested_func = 自 round8 基线同败存量，`r8v8_full_oldface_b.json`；REVIEW「11/11」为口径过宽，实义 = 不回退） | 不回退 ✓ |

- **循环族 68/68 不回退**（`r9v9_repro_fix3_b126_loops1.json`）：r4_c4_02_loopelse 14/14、r4_b109_loopelse 9/9、r5_13_for_else_cross 11/11、r5_b115_battery 2/2、r5_b116_bare 2/2、B99_min 9/9、r7_b121_whilehdr 5/5、r7_b117_f2tail 7/7、n9_b104_whilehost 9/9。
- **B104 族不回退**（`r9v9_repro_fix3_b126_fam1.json`）：B104_main 14/14、chain4 6/6、chain5 5/5、foror 3/3、opdeep 4/4、exprtail 4/5（v3 = B123 存量）、e05 6/11（B124 后读数）、e10 32/32。
- **r8 电池扫 20 探针 135/141**（`r9v9_repro_fix3_b126_r8sweep.json`）：全部失败面与登记存量逐位一致（b102 8/10 ideg/pin、b96 14/18 b3/b7.<listcomp>，`r9v9_repro_spots_r8a_m.json` 同读数），零新增。
- **承重面全绿**（`r9v9fix3_bearing.json`）：broker 128/128、matcher 17/17、finance 32/32、quote_handler 79/79、realtime 13/13、quotation 153/153、nb_for 2/2、nb_with 2/2、nb_while 2/2、nb_b99 4/4。
- **station 六面重跑 WORSE=0**（§5 详表）；附带改善（非本单元声明范围，如实登记）：probe42 +1（x08_stmt_leaves 5/8→6/8，raise_leaf 单元翻正，同构 RAISE 尾闩）、residual/oldface +1（r8_x_with_ternary，B124 归属，本次全量重跑首测计账）。
- I.4 白名单核验：判据 = 块内指令 opname 序（清理族 + RAISE_VARARGS/RERAISE）+ 区域结构成员关系（body/else 成员表 + header/condition_block/natural_exit/for_iter_exit 块相等）；零名字/偏移/阈值/跨层反查。G3：新方法 `_b126r2_raise_only_trampoline_exit` 无禁前缀（与 `_b124r1_*` 同式）；G4：无 start_offset 阈值（≤8 跳为声明式链长上限、非偏移阈值）。BOM/插桩：单 BOM 头维持、零调试插桩（判据注释除外）。

**9.3b 整改记录（REVIEW2 R-1 方案 a 执行后）**：[B126-R1] `_b126_claimed` 全量移除（`region_analyzer.py` docstring/定义/守卫/更新点四站点；`git diff` = 1+/26-，为 `3803fa73` 增量的逐字逆操作），树 = R1-off 态（assert_deep：HEAD 1 个 AssertRegion → 现 2 个）；§3 承重 = [B126-R2] 单点，与「不做认领扩展/E6 单点」声明一致。复跑（REVIEW2 R-1 要求）：§3 六单元（`r9v9fix3b_s3_units.json`）n9 6/6、r8_07 10/11、r8_10 9/12、x08 6/8、probe_for_assert 3/3、probe_break_raise 3/4（g2 渲染存续折叠，R2-off 同形，见上表校正）；循环族 68/68（`r9v9fix3b_s3_loops.json`）、B104 族 74/80（`r9v9fix3b_s3_fam1.json`）、r8 电池扫 135/141（`r9v9fix3b_s3_r8sweep.json`），均与 fix3 逐位一致；R2 守卫计数（`r9v9fix3b_s3_guard.json`）：assert_deep calls=2 hits=2 sites=[(76,True),(74,True)]、x08::raise_leaf calls=1 hits=1 sites=[(42,True)]、**r8_assert_chain calls=0 ⇒ R-3 可复核口径**；probe g1/g2 守卫均不触发（calls=1 hits=0 sites=[(14,False)]）。

## §4 尽力项：B127/B128/Yield 探针重建/B44 证据缺口（本轮复验登记，未修复——预算集中于 §3 位C + 终态门禁；按 REVIEW §6 位D 低优先口径整体移交 round10）

- **B127**（e07_g4_star_slice_containers::f_slice_expr_bounds）：本段复验 15/16，产物实证 = 嵌套宿主 `for→if→while` 下 while 体坍缩为裸名 `b`（`if i and i: b`；源 = `while i: return xs[a+1 : b*2] + xs[a if b else 0 : 3]`）——与 B104/B124 宿主融合族同谱（条件融合 `if i and i:` + 归约吞体），非快修形，移交。
- **B128**（e12d_g9_awaits::f_await_cond_pos）：本段复验 10/11，失败面与 REVIEW 登记逐位一致，移交。
- **Yield 复验**（e12b/e12c/e12f）：本段复核 confirm `compile_error 0/0` 空转；根因实证 = 产物非法（`yield sink(yield i)` 实参位缺括号，OK.py 不编译）⇒ 单元级读数不可得，破口判定维持；探针重建（产出可编译对照）未做，移交。
- **B44**（≥3 层双入口归纳）：证据缺口维持（round9 证据集无对应探针），本段未重建探针，移交 round10 按 REVIEW §3.2 行 141 口径补齐。

## §5 站桩回归（六面 + 承重面 + 34 集，终态汇总）

**六面（RV2 重跑 = 本段 B126-R2 后在案树全量，逐单元对 §1 基线（10-15 读数）比差，`r9v9_station.py`）**：

| 面（证据） | §1 基线 | 终态（B126-R2 后） | WORSE |
|---|---|---|---|
| round1face（`r9v9_full_round1face_c0-12/c12-24.json`） | 423/423 | 423/423 | 0 |
| quotation（`r9v9_quotation.json`） | 153/153 | 153/153 | 0 |
| round2face（`r9v9_regress_round2face_c0-15/c15-30/c30-45.json`） | 245/251 | 245/251 | 0 |
| probe42（`r9v9_regress_probe42_c0-14/c14-28/c28-42.json`） | 178/196 | **179/196** | 0（+1：x08_stmt_leaves 5/8→6/8 = raise_leaf 单元翻正，B126-R2 附带改善，guard-off 反事实 `x08_guardoff.py` 复现 5/8 归因实证） |
| residual（`r9v9_full_residual_c0-18/…/c54-72.json`） | 419/446 | **420/446** | 0（+1：r8_10::r8_x_with_ternary，B124 已落地单元首测计账） |
| oldface（`r9v9_full_oldface_c0-15/…/c45-59.json`） | 671/692 | **672/692** | 0（+1：同 r8_x_with_ternary） |
| 合计 | 2089/2161 | **2092/2161** | **0（逐单元失败集比差，见下）** |

- 逐单元失败集比差（`r9v9_diffcheck` 口径，本段终态 vs `d:\Temp\opencode\r9v9_station_pre_b126\` 备份）：全六面仅 3 处差异、全部为失败单元翻正（r8_x_with_ternary ×2 面 + raise_leaf），**零 pass→fail**。另有旧单文件读数核验：r8_07_assert_forms 10/11 同单元存量（`r8v8_full_oldface_b.json` 同败，非本修复引入）。
- 承重面（`r9v9fix3_bearing.json`）：broker 128/128、matcher 17/17、finance 32/32、quote_handler 79/79、realtime 13/13、quotation 153/153、nb_for/nb_with/nb_while 2/2、nb_b99 4/4 全绿（§3 同源）。
- 34 集（`rounds/round8/r8v8rev_34set.py` 0..7/8 全片 rc=0，`r8v8rev_34set_shard0..7.json`）：34/34 文件 success、failure/error/compile_error 全 0 ⇒ NEWFAIL=0（对照 2026-10-12 旧单 shard 基线 failure 5/0 success，满额翻正；回归基线 `failing_index.json` 全 34 行）。
- 探针面附加回归（§3 全列）：循环族 68/68、B104 族不回退、r8 电池扫 20 探针 135/141（失败面与存量逐位一致）、r8_07 10/11 不回退、B125 家族 `r9v9fix_b125_family.json` 逐位等同。
- **9.3b 全量复跑（R-1 移除后，终态）**：六面 17 分片复跑聚合 **2092/2161**（`r9v9fix3b_station_agg.json`；分片 `r9v9fix3b_full_*` / `r9v9fix3b_regress_*` / `r9v9fix3b_quotation.json`），与本表终态逐位一致；逐单元失败集比差（`r9v9fix3b_station_diffcheck.json`，同 `d:\Temp\opencode\r9v9_station_pre_b126` 备份）：**pass→fail = 0**、fail→pass = 3（r8_x_with_ternary ×2 面 + raise_leaf）。承重面复跑全绿（`r9v9fix3b_bearing.json`）。34 集复跑（`r9v9fix3b_34set_shard0..7.json`）：34/34 文件 success、**1568/1568**、failure/error/compile_error 全 0、NEWFAIL=[]（`r9v9fix3b_34set_summary.json`）。
