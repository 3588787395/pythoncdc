# Round 9 修复批次 FIX_R9（任务 9.2，算法修复，不 git commit）

- 基线 = REVIEW_DRAFT §1 站桩新基线（合并树 e42b8509 → 本批起始 a2d1e15e）；判据唯一 `scripts/pyc_verify.py`，RV2（先 regen `pycdc -o` 再 verify single）
- 纪律 = 只动 `core/cfg/region_analyzer.py` / `region_ast_generator.py` 的归约算法判据面；禁止回滚合并调和 hunk [B104-R3]/[B99 收窄]/H1-H4（REVIEW §4 承重实证）；I.4 白名单判据、I.6 落地声明、I.7 注释同步；命令 ≤300s 分片；regen M 态 `*OK.py` 终态 `git checkout --` 还原；插桩用完即删
- 工作队列 = §6 派发：位0（B124 四臂归属）→ 位A（B104 while 链族 14 单元）→ 位B（B125）→ 位C（B126）→ 尽力项（B127/B128/B44/Yield 探针）

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

## §3 位C：B126 assert 链归约吞 while 回边载体（1 单元）

（待位B）

## §4 尽力项：B127/B128/Yield 探针重建/B44 证据缺口

（待位C）

## §5 站桩回归（七面 + 承重面 + 34 集）

（终态汇总）
