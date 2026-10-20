# Round 7 修复终稿（赋值-删除-return-slice 族：AugAssign / Delete / Return / Slice）

基线 = rr-v3r06 = 8c088ef7（冻结树）。域内目标：B59（for-else del）、B60（with assert）、B62（return 复合/列表推导过滤/三元条件）、B127（slice 悬挂链）；待复验项 B76 / B48 残留变体 / B84 / B88（x08::return_leaf 已绿）。

## §0 范围与基线读数

- 轮次定位：Task 7（`tasks.md` L35-39）——赋值-删除-return-slice 族封闭；登记破口 B76 / B48 残留 / B84 / B88 / B62 / B127 / B59 / B60。
- 基线探针（stamp `rec1_probes_r7pre1.json`，9 探针 **69/76**）：
  - `e07=test_repros/round3/e07_g4_star_slice_containers.pyc` → 15/16，红 `f_slice_expr_bounds`（B127）
  - `r809=test_repros/round8/r8_09_deep_host_combo.pyc` → 8/10，红 `r8_dh_for_else_del`（B59）、`r8_dh_with_assert`（B60）
  - `r714=test_repros/round7/r7_14_boolop_deep_host.pyc` → 5/9，红 `h_return_composite` / `h_listcomp_filter_composite`(+`<listcomp>`) / `h_if_ternary_chain_composite`（B62）
  - 待复验全绿：`x08` 8/8（B88）、`c13` 3/3、`rv1032` 8/8（B76）、`r806` 10/10、`r708` 8/8（B48 残留）、`v_b76_face` 4/4
- 终态读数（stamp `rec1_probes_r7fin_main.json`，9 主探针 + 6 合成 = **98/98**）：e07 16/16、r809 10/10、r714 9/9、合成 6 件 22/22。

## §1 修复日志（增量）

### B144-V3R7（for-else 体以 raise/return 收尾 → break 落点独占可达；B59）

- 症状：`for … else: raise …` 形态中，break 落点（for 语句之后的代码）既不在 FOR_ITER 耗尽出口可达集内、也不是循环体内 if 分支汇合块 ⇒ 无 break 证据 ⇒ `has_break=False` ⇒ else 子句退化、`return xs` 被吞进循环体、break 丢失。
- 机制（`region_analyzer.py:8750` 新方法 `_b144_break_only_target` + `:8924` 调用点）：CPython 3.11 的 for-break 签名为「迭代器清理 POP_TOP + 无条件前向跳转」，落点是整个 for 之后的代码块。判据（I.4 白名单）：(a) 源块末条为无条件前向跳转且 argval 指向 target，且紧邻该跳转的前一条指令为 `POP_TOP`（for-break 签名——无此前缀的无条件前向跳转是别的控制流，如链式比较真值路径跳到 return 块）；(b) 去掉该边后 target 自 fall_through 在 CFG **正常边**上不可达（异常边不扩张）；(c) target 正向不可达任一回边源 ⇒ target 在循环体外。命中块登记为 break 落点屏障，循环体收集排除该落点及其后继（每块唯一归属）。

### B145-V3R7（break 源块补发 break + del 归约为 ast.Delete）

- 机制（`region_ast_generator.py:61783` 新方法 `_b145_is_break_landing_block`、`:62643`/`:63038`/`:63058`）：break 源块（以无条件前向跳转跳出循环）须在其用户语句之后补发 `ast.Break`；`del x[i]` / `del x.y` 归约为 `ast.Delete`（旧路径把 DELETE_* 混入表达式重建成裸 Expr，语义错误）。
- **收窄（E 门禁首跑自捕获）**：首版判据「末条为无条件前向跳转且本块不是 break 落点」过宽——循环内的顺序跳转（if 臂汇合跳到 merge 块、if 臂假边跳回边重检块 = continue 语义）被误判为 break，误杀两个真实模块（`function.pyc::order_entrust_info_handle`、`trade_live_broker.pyc::get_trades` 各退一单元，6615/6617）。收窄为「跳转必须**离开所属循环**（目标块不在该循环的块集/体集合/条件块内）」后两文件复原 71/71、128/128，r809 与合成探针仍绿。

### B146-V3R7 / B147-V3R7（with 体内断言前的语句前缀被吞；B60）

- 症状：`with open(path) as fh: data = fh.read(); assert data, "empty file"` 中 `data = fh.read()` 整句蒸发，只剩 assert。
- 机制：`region_ast_generator.py:694` 新方法 `_b146_split_block_condition_prefix` + `:769` 新方法 `_b146_block_entry_stack_depth`：with 体首块的入口栈深度 = 2（`BEFORE_WITH` 已压入 `__enter__`/`__exit__`，`STORE_FAST fh` 弹出一层 ⇒ 深度 1），旧「入口深度 = 0」模拟在 `STORE_FAST fh` 处下溢并放弃 ⇒ 前缀无归属。新的切分：基线 B = H−1 = 1，前缀 = 体指令 `[LOAD_FAST fh; LOAD_METHOD read; PRECALL; CALL; STORE_FAST data]`（with 目标存储作为继承值前导排除）。B147（`:41250`）使 with 体嵌套 Assert 路径消费 `_take_assert_prefix_stmts`（与 `_process_if_blocks`/`_loop_handle_header` 同契约），前缀在 `ast.Assert` 之前发射而非蒸发。

### B148-V3R7（三元作切片边界时的 cond 前缀折叠；B127）

- 症状：`xs[a + 1 : b * 2] + xs[a if b else 0 : 3]` 整条 return 表达式丢失，只剩三元条件的裸名 `b`。
- 机制（`region_ast_generator.py:55909` `_compute_ternary_cond_preload_exprs`）：cond 块前缀此前按「仅 LOAD_*」扫描，折叠类 opcode（BINARY_OP / BUILD_SLICE / BINARY_SUBSCR / COMPARE_OP …）的算子散落成碎片，merge 侧从碎片重建出 `xs[a+1:b*2]`。现将折叠类 opcode 族纳入既有 compound-prefix 门 ⇒ 经 `_split_preload_into_siblings` + `reconstruct` 产出真实 `Subscript/Slice/BinOp`。I.4：opcode 序 + 值测试跳转极性。

### B149-V3R7（SWAP/POP_TOP/RETURN_VALUE 跨块 return 链的尾对剥离）

- CPython 在 for 迭代器清理形态下发出 `… ; SWAP 2 ; POP_TOP ; RETURN_VALUE`；既有 SWAP/POP_TOP 剥离因 `RETURN_VALUE` 在末位而漏剥，残留 SWAP 触发 `_has_control_flow_or_store` ⇒ 整个 merge 表达式被丢弃。修复：在 RETURN 剥离后**重复**一次尾对剥离（`region_ast_generator.py:58167` `_try_build_ternary_merge_consumer_expr`）。

### B150-V3R7（双臂共享单一 RETURN 落点 ⇒ Return(IfExp)；B62 之一）

- 症状：`return (a and b) if flag else (a < b < c or flag)` 被展开为 `if flag: return a and b else: return a < b < c or flag`（两个独立 RETURN 块，控制流形状与原码不同）。
- 机制（`region_ast_generator.py:27026` 挂钩 + `:27032` 新方法 `_b150_fold_shared_return_diamond`）：两臂各产生一条带值 Return 且**汇合到同一 RETURN_VALUE 落点**是 `return (X if c else Y)` 的 CPython 签名（源码级 if/else 双 return 有两个独立 RETURN 块）⇒ 归约为 `Return(IfExp(...))`。I.4：merge 块末 opcode = RETURN_VALUE、merge ∉ region.blocks、merge 的正常前驱同时与 then_blocks 和 else_blocks 相交（异常边排除）、两臂各恰一条带值 Return、非 elif / 非嵌套 if。

### B151-V3R7（列表推导过滤项的 and/or 分组重建；B62 之二）

- 症状：`[x for x in xs if 0 < x < lim and (flag or x % 2)]` 的 `and (flag or x % 2)` 整段被丢（链式比较快路径提前返回）。
- 机制（`core/cfg/comprehension_generator.py:2230` 挂钩 + `:2433` 新方法 `_b151_filter_stack_effect`、`:2476` 新方法 `_b151_parse_comp_filter_terms`、`:2561` 新方法 `_b151_compose_comp_filter_terms`）：按**项级**解析（项 = 表达式 + 条件跳转；表达式由向后栈扫描定位，受元素表达式起点约束）＋ and/or 分组合成（FWD-IF_TRUE 头开 or 组；某项目标是后项起点 ⇒ 该组闭合为 `(A or B) and C`，否则 or 组延伸至链尾 ⇒ `A or (B and C)`）。

### B152-V3R7（if 条件为三元时 if 体/else 体被吞；B62 之三）

- 症状：`if a if flag else b < c: return "t"` / `return "f"` → 产物 `if (a if flag else b < c): pass` + `return 't'`（if 体与 else 分支双失）。
- 机制（`region_ast_generator.py:17966`）：`if <三元>:` 形态下 analyzer 把三元的汇合块记为 IfRegion 的 `merge_block`——而该块**就是** if 体；`_process_if_blocks` 跳过 merge（视作 post-if 兄弟），致 if 体为空且 if 假边落点块无人认领。现：当 elif 分支产出空体且该臂的 fall-through 恰为 region's `merge_block`（∉ region.blocks）时，直接把该块归约为 if 体，并把假边落点块作为 `orelse`（若其属 `region.else_blocks`）或作为 post-if 兄弟发射。

## §2 变更清单（增量）

- `core/cfg/region_analyzer.py` +107/−3；`core/cfg/region_ast_generator.py` +462/−4；`core/cfg/comprehension_generator.py` +225/−2；合计 3 文件 **+785/−9**。
- 标记 `[Bn-V3R7]` 21 处（B144×2、B145×5、B146/B147×3、B148/B149×2、B150×1、B151×4、B152×1，另 3 处为方法 docstring 段）；新增方法 8 个（`_b144_break_only_target` / `_b145_is_break_landing_block` / `_b146_split_block_condition_prefix` / `_b146_block_entry_stack_depth` / `_b150_fold_shared_return_diamond` / `_b151_filter_stack_effect` / `_b151_parse_comp_filter_terms` / `_b151_compose_comp_filter_terms`），均六项 docstring（①–⑥ + C1/C2/C3）。
- 新破口编号 B144–B152（B142/B143 为 R6 登记残余）；G3=0、G4=0、I.4 白名单判据齐备；只改 `core/cfg/**`。
- 新增合成探针 6 个（源 `test_repros/round7/r7_synth_*.py`，pyc 入 stage）：`r7_synth_b144_for_else_break`、`r7_synth_b146_with_assert`、`r7_synth_b148_slice_ternary`、`r7_synth_b150_return_ternary`、`r7_synth_b151_listcomp_filter`、`r7_synth_b152_if_ternary`。

## §3 前后读数

| 组 | 基线 | 终态 | 备注 |
|---|---|---|---|
| R7 主探针 9 件 | 69/76 | **76/76** | e07 15/16→16/16、r809 8/10→10/10、r714 5/9→9/9；其余 6 件本就全绿 |
| R7 合成 6 件 | — | **22/22** | b144/b146/b148/b150/b151/b152 各 2–3 单元 |
| 主集合计（9+6） | — | **98/98** | stamp `r7fin_main` |
| 邻域 16 探针 | 83/86 | **83/86** | 失败集 = r810 11/12、c04 5/6、m02 2/3（域外/park），逐位一致 |
| 命名 8 探针 | 44/46 | **46/46** | +r809 8/10→10/10；余 0 |
| 负对照九件 | 60/60 | **60/60** | 逐位一致 |
| R4 保护 5 组 | 71/71 | **71/71** | 逐位一致 |
| R5 合成 20 探针 | 65/65 | **65/65** | 逐位一致 |
| R5 三真实文件 | 172/172 | **172/172** | trade_info_utils 41/41、scheduler 52/52、quote_handler 79/79 |

## §4 复核

- 主代理独立复跑（非继承子代理读数）：`r7acc2` 9 探针 76/76、`r7fin_main` 98/98、`r7fin2_neigh1` 83/86、`r7fin2_named1` 46/46、`r7fin2_neg9_1` 60/60、`r7fin2_r4prot1` 71/71、`r7fin2_synth1` 65/65、`r7fin2_real3` 172/172。
- E 门禁自捕获回归：首跑 6615/6617（shard6 两真实文件：function.pyc `order_entrust_info_handle`、trade_live_broker.pyc `get_trades`）→ 定位 B145 break 判据过宽（循环内顺序跳被误判为 break）→ 按 I.4 收窄为「跳转必须离开所属循环」→ 两文件单验 71/71 + 128/128 复原且 r809/合成仍绿 → 二跑 6617/6617 files_failure=0。
- 诊断证据：`_r7_dis.py`（按名反汇编，含异常表）、`_r7_regions.py`（CFG + 区域快照）、`_r7_rerun.py`（从既有 stamp JSON 重建批跑命令）、`_r7_grep.py`；BASE 对照用 git worktree（`8c088ef7`）逐文件 diff（`d:\Temp\opencode\fn_base.py` vs `fn_cur.py`、`tlb_base.py` vs `tlb_cur.py`）。

## §5 门禁读数

- 脚本 `rounds/round7/final_verify_run_r7.py`（`verify_driver.py`/`verify7_split.py` 复制自 R6；BASE_COMMIT=8c088ef7；G3 判据 `git diff 8c088ef7 -- core/`），产 `final_verify_summary.json` / `final_verify_log.txt`。
- **二跑（最终树，496s）**：402 八分片 **6617/6617**、files_failure=0（shard0 786、shard1 469、shard2 538、shard3 887、shard4 855、shard5 999、shard6 801、shard7 1282）。
- small34：**1568/1568**（files success 34）；quotation：**success**。
- pytest 七套件：**2 failed / 282 passed / 2 xpassed**（失败名单与基线逐位一致：`test_B01_simple_if_then_else_merge` + `test_BOUNDARY_02_large_function`）。
- IV.2：IMPORT_OK / COMPILE_OK、BOM 单头、instrumentation code 命中 0、`G3_forbidden_prefix_new_defs=0`。
- 首跑（记录）：6615/6617、files_failure=2 —— 已按 §1/B145 收窄修复，二跑归零。

## §6 落地声明

- Task 7 域内封闭：B59（for-else + del/break，r809 10/10）、B60（with 体内 assert 前缀，r809 10/10）、B62 三处（return 三元归约 / 列表推导 and-or 过滤 / if 三元条件的体与 else 派发，r714 9/9）、B127（切片悬挂链，e07 16/16）。
- 待复验项全部维持绿：x08::return_leaf 8/8（B88）、rv10_32 8/8（B76）、r8_06 10/10、r7_08 8/8（B48 残留变体）、v_b76_face 4/4（B76 变体）、c13 3/3。
- 通用性实证：6 个非语料合成探针 22/22（新机制逐条覆盖 + 交叉形态）。
- **残余登记（承 R6）**：B142（`v_b71_face::v_nest_fin_continue` 嵌套 finally 副本归属）、B143（finally 体内 break 的 finalbody 子区域派发）——两域均非本轮赋值/删除/返回/切片族，且需重构 try 区域/副本归属，留待后续轮次。
- 本轮无新增拖延破口；E 门禁首跑自捕获的 B145 误杀已在提交前收窄并双门禁复验（两文件单验 + E 二跑 + 六组回归）。
- 变更面：3 文件 **+785/−9**，标记 21 处，只改 `core/cfg/**`。
