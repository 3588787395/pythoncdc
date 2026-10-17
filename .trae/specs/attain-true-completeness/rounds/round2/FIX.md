# Round 2 · 条件合并块族封闭（If / BoolOp / IfExp）— FIX 报告（进行中）

- 规范：`.trae/specs/attain-true-completeness/`（简称 R）；批次 R2（tasks.md Task 2）
- 树：HEAD `e1c0aabe` 承接（round1 交付后）
- 纪律：只改 `core/cfg/**`；判据 = I.4 白名单；G3=0/G4=0；标记 `[Bn-V3R2]`；不提交 git
- 本文件随进度增量追加（防中断）。

## §0 范围与结论摘要（草稿，待终稿）

R2 红单元（round1 BREACH_RECON §2 行1/15/16 + §4 R2 映射）：

| 族 | 探针 | 红单元 | round1 读数 |
|---|---|---|---|
| If/B78 | `v_b46_face` | v_while_cond_nest / v_if_cond_nest / n_for_body_nest | 1/4 |
| If/B46 变体 | `r7_12` | b_ternary_lhs_and | 6/8 |
| BoolOp/B98 | `e01_b98matrix` | 8 红 | 7/15 |
| BoolOp/B98 | `e02_b98hosts` | 5 红 | 13/18 |
| BoolOp/B98 | `b98_resid` | r_d1 / r_e3 / r_g2 | 2/5 |
| IfExp/B123 | `exprtail` | v3 | 4/5 |
| B43 | `r7_10` | c_chain_and_combo | 7/8 |
| B44 | `r7_12` | b_nest_deep_right | 6/8 |
| B51 | `rv7_02` | chain_two_ternary / chain_three_ternary | 2/4 |
| B42 | `r7_04` | t_compare_lhs_only | 6/7 |
| B42 | `r7_05` | t_listcomp_ternary_filter.<listcomp> | 15/16 |
| 复验 | `r7_07` | （全绿） | 7/7 |
| 复验 | `r7_08` | （全绿） | 8/8 |

（结论与分析随修复进展填充。）

### 复现基线（本轮实跑，`rec1_run.py`，stamp=r2pre1/2/3）

| run | 探针 | 读数 |
|---|---|---|
| r2pre1 | v_b46_face 1/4；b44_r712 6/8；r7_10 7/8；r7_04 6/7；r7_05 15/16；rv7_02 2/4；exprtail 4/5 | units=41/52 |
| r2pre2 | e01_b98matrix 7/15；e02_b98hosts 13/18；b98_resid 2/5 | units=22/38 |
| r2pre3 | r7_07 7/7；r7_08 8/8；rv8_01 7/7；rv8_02 7/7；r10_04 3/3；r10_15 6/6；r10_21 4/4；rv10_32 8/8；r8_06 10/10 | units=60/60 |

与 round1 逐位一致。

## §1 修复日志（增量，终稿归并）

机制修复（`core/cfg/region_ast_generator.py` + `core/cfg/region_analyzer.py`，标记 [B98-V3R2]）：

1. compare_cross（r2fix1 8/15）：`_try_build_ternary_merge_consumer_expr` 成对剥尾 `SWAP n; POP_TOP`（编辑 A）+ merge-consumer 分支条件放宽（编辑 B）+ `_build_ternary_no_target_consumer_stmt` 回退收窄（编辑 C）。cmp 语境 merge 非噪声恰 `[STORE, JUMP_IF_FALSE_ORDER, RETURN]` → compare_cross 翻绿。
2. pair_deep / and_tail（r2fix2 10/15）：Fix 1 store 语境全链重建 + Fix 2 If-guard Assign 重写（`_generate_if` 末尾 If(test,body=[Pass],无 orelse)+merge 首条 STORE_* → Assign）。
3. ternary_cross（r2fix3 11/15）：新增 `_build_value_block_expr` + `_try_build_value_diamond_return`（值菱形 Return 折叠，hook 于 `_generate_if` 的 `_if_as_while` 检查之后）。
4. not_wrapped（r2fix4 12/15）：新增 `_try_build_notwrapped_fused_value_ternary`（外梅花形脆弱值三元重建），hook 于 `_generate_ternary` 的 Cluster-6 守卫（原 `return None` 前）。
5. or_tail（r2fix5 13/15）：`_b1b_loop_body_run_continuation` 增 (1') and-run 尾→or-run 头边界判据（prev_and = chain[-2] 为 'and'）+ R3-K 校验 walk 增 or-run 终段成员接受（ft 假边离开本链、真边 fall-through == body_t）。or_tail 链由 [(40,'and'),(44,'or')] 恢复为 [(40,'and'),(44,'or'),(48,'or')]（unify 扩展至 [(…),(52,'and')]）→ Or[And[a,b],c,d]。
6. walrus + call_arg（r2fix6 15/15）：
   a) walrus 确认：`_try_build_ternary_as_if_cond` PIB 先处理再标记（r2fix5 已落盘，本次 stamp 确认 `if (w := (a or b) and c): return w`）。
   b) call_arg 根因定位（行级 trace）：值语境融合链 `sink((a or b) and c)` 的 or 前缀块（46）被 B99 吸收为链首后，`_detect_boolop_short_circuit_chain` 的 [Phase 3 adv14] 共享 merge 守卫拿「前缀块跳转目标 vs 锚点 merge」比较，两组短路口天然不同 → 锚点 append 前 break（L34107）→ B99-C3 重走丢前缀 → BoolOpRegion@54 半链；块 46 再被 or 链检测划成伪 IfRegion → 值链蒸发。
      修复一（region_analyzer `_detect_boolop_short_circuit_chain`）：新增 `_b99_n_prefix` 前缀计数，R565 共享 merge 守卫改读 `_r565_chain = chain[_b99_n_prefix:]`（只对链的真实成员生效，前缀成员间的合法性已由 B99 吸收判据结构性校验；无前缀时切片为原链，C3 不变）。→ BoolOpRegion@46 [(46,'or'),(54,'and')] merge=60，镜像 return_pos 形态。
      修复二（生成端 `_generate_boolop_impl` P2-1 分支）：迭代器拆除-返回尾识别——汇合块尾 `[消费段, SWAP n, POP_TOP, RETURN_VALUE]` 且 POP_TOP 为倒数第二条时，成对剥尾拆除对后把表达式整体归约为 `Return(value=expr)`（原判据把 CALL 结果当被丢弃表达式语句 → `sink(...)` 丢 return、多出 `return None`）。
      修复三（`_try_build_orprefix_and_boolop_from_ternary`）：B98-R1 镜像折叠增全链头前缀变体（链首 == 三元条件块、次成员 == true 值块、共享 merge），直接以 `_build_boolop_expression` 黑箱重建；形状不过回退 IfExp（C3）。此项为修复一的回归消除：全链头进入后 compare_cross / ternary_cross 的镜像 TernaryRegion 找不到旧形态 anchor-entry BoolOpRegion。
      验证：中间态曾出现 compare_cross / ternary_cross 回退（r2fix6 首跑 13/15），经临时中和修复一确认归因（BoolOpRegion entry=48 anchor-only 时镜像命中 vs entry=44 全链时不命中），落修复三后复跑 stamp r2fix6 → 15/15。

e01 进度：r2pre2 7/15 → r2fix1 8/15 → r2fix2 10/15 → r2fix3 11/15 → r2fix4 12/15 → r2fix5 13/15 → r2fix6 15/15（e01 全绿）。


7. e02 宿主族（r2fix7 18/18）：本批根因三处，全部落在既有「融合 or-前缀链」族：
   a) m_handler（
eturn ((a or b) and c) if a else -1）：值菱形 Return 钩子（r2fix3）
      已能把 except 内条件合并块折成 Return(IfExp(...))，但体部由
      _build_value_block_expr(@86) 镜像重建 TernaryRegion@86 时未命中 orprefix
      折叠——_try_build_orprefix_and_boolop_from_ternary 全链头变体的次成员
      判据曾要求 op_chain[1][1] == 'and'；该链由 _detect_boolop_conditional_chain
      的「三元形状检测」分支生成（region_analyzer.py 32687-32699：非首成员
      op_type 继承 chain[0][1]，JIFOP 块得到 'or' 标签），标签并非真实算子。
      修复：全链变体改以链成员关系（链首==条件块、次成员==true 值块、共享 merge）
      为判据，算子语义完全交 _build_boolop_expression 黑箱结果的形状校验
      （And[Or[..], ..]）承担；形状不过回退 IfExp（C3）。产出
      Return(IfExp(a, BoolOp(and,[BoolOp(or,[a,b]),c]), -1))。
   b) f_with_body_host（with+for 内 
eturn (a or b) and c）：P2-1 无 target 布尔
      路径把「迭代器拆除 + __exit__ 调用」尾（[SWAP 2, POP_TOP] 拆迭代器；[SWAP 2,
      LOAD None×3, PRECALL, CALL, POP_TOP] 调 __exit__）误当语句消费，导致 return
      整句丢失（regen 只剩 if i: pass）。既有 _teardown_ret_p21 仅识别
      [拆除, SWAP n, POP_TOP, RETURN] 相邻形态。新增 with-exit 变体
      _wex_ret_p21：首 POP_TOP == len-2 且末为 RETURN_VALUE、其前两条为
      CALL/PRECALL 时，回溯连续 LOAD_CONST None(argval None) >=2 界定 __exit__
      实参段与可选 SWAP，剥除拆除段后余段以 P2-1 初始栈重建为 Return 值。
   c) 推导式元素/值位融合（f_comp_cond_host.<listcomp> / f_genexp_cond_host.<genexpr>
      过滤条件、f_dictcomp_value_host.<dictcomp> 值位）：comprehension_generator
      两处独立缺陷：
      ① _extract_comp_ifs B6 混合分组只覆盖 A and B or C（and 组内、or 接组间），
         对偶形 (A or B) and C（seg0 前向 IF_TRUE 跳转目标==后续段起始，真值边
         跳过中间成员直达后续条件检查）按 or→and 边界误分组为 A or (B and C)。
         新增 or-前缀支路：识别条件=is_or_pattern 且存在边界 t（前 t-1 段跳转均
         为前向 IF_TRUE 且目标同为第 t 段起始偏移、t 段起全部 'and'）；归约 =
         And[Or[前 t 段], ...]；不命中逐位回落原 B6 分组（C3）。无括号源码
         A or B and C 的 A 真边直达元素产出、目标非段起始，天然不命中。
      ② _detect_comp_ternary 对表达式位同型融合（a; PJIF_TRUE c; b; JIFOP merge;
         c; 追加点）按 IF_TRUE 取反解成假三元  if not a else c（b 为真时丢失
         c 检查）。新增识别条件=首条件跳转为前向 IF_TRUE、真值区末指令为
         keep-or-pop 族且目标==追加点偏移、真值区无其它条件跳转；归约 =
         直接返回 BoolOp(and, [BoolOp(or,[A,B]), C])；不命中逐字回落既有
         取反路径（C3）。另修 _extract_dict_comp_key_before_ternary 的 cond
         定位：跳过 BACKWARD 条件跳转（过滤器回跳）再取首个前向跳转，键窗
         不再为空、键不再丢失（无过滤器前导时行为逐位不变）。
      验证：e02 stamp r2fix7b_e02 18/18（含 f_comp_cond_host / f_genexp_cond_host /
      f_dictcomp_value_host 全绿）；回归 e01 r2fix7_e01 15/15、负对照 60/60
      （r2fix7_negctl，注意 rv8/r10 探针在 round8/round10 目录，round7 路径会静默 None）。

e02 进度：r2pre2 13/18 → r2fix7 18/18（e02 全绿）。
8. b98_resid 值链族（r2fix8 5/5；e01 回归 15/15、负对照 60/60）：本批根因 =
   BoolOp 值链三类「keep-or-pop/边界跳转」混合形态缺分组重建——
   扁平 or_groups 对同标签序列重结合、B45 skip 边算法误并尾值。
   新增 _try_build_keeppop_target_grouped（标记 [B98-V3R2 keep-or-pop 目标收敛分组]），
   按成员跳转目标分段右折叠，三形态：
   a) r_e3（a or (b and (c or d))）全员 keep-or-pop 且目标全为 merge：保留极性
      右折叠（JITOP→'or'、JIFOP→'and'），尾值块接入折叠终端；
   b) r_g2（(a and (b or c)) or (d and e)）首成员 PF 跳过中段落于链内成员
      （and 组假边直达 or 尾求值起点）、中段 JT 目标 merge、末段 keep+尾值；
   c) r_d1（((a or b) and c) or d）首成员 PT 真边落于链内成员、中段 PF
      落于尾值块（尾值 d 也是 B45 误并对象：→ (a or b) and (c or d)）；
      识别条件均为同层结构事实（块末 opcode 族 + 跳转目标 + 后继集合，
      I.4 白名单）；接入点在 _build_boolop_expression_inner 的 B98 尾值边界
      守卫之后、B45 skip 边重建之前（B45 会先手误建 r_d1）；未命中/
      重建失败返回 None 逐位回落；条件上下文不接手（C3）。
   验证：b98_resid stamp r2fix8_b98 5/5（r_d1/r_d2/r_e3/r_g2 全绿）；同跑 e01 15/15；
   负对照 r2fix8_negctl 60/60。

b98_resid 进度：r2fix7_rest 2/5 → r2fix8 5/5（本批全绿）。

9. rv7_02 三元操作数链式比较（r2fix9 4/4；回归 42/42、负对照 60/60）：本批根因 =
   链式比较的可比较操作数由**三元表达式**经外栈供给时，既有链式比较重建器全部不接手——
   a) chain_two_ternary（(a if c1 else b) < (x if c2 else y) < c）：链头 @22 [SWAP 2,
      COPY 2, COMPARE_OP 0(<), JUMP_IF_FALSE_OR_POP→cleanup]，cleanup @44 [SWAP 2,
      POP_TOP]，merge @48 RETURN_VALUE；两个操作数分别由 TernaryRegion T1@0
      （merge=@12）与 T2@12（merge=@22、merge_context='compare'、
      vt='__compare_target__'）以外栈值供给（头块无任何 LOAD 前导），
      _build_chained_compare_from_region_data 依赖的 region.chained_left_instr 为空
      → None；IfRegion@22 被降级为 `if (x if c2 else y): pass`，T1 裸 Expr 外漏。
   b) chain_three_ternary（(a if c1 else b) <= (x if c2 else y) < (m if c3 else n)）：
      宿主是 BoolOpRegion@22（op_chain=[(22,'and')] 单成员，非 IfRegion）；链段比较块
      @44 前无操作数指令——第三操作数 (m if c3 else n) 以**值钻石**（@34 LOAD c3 条件
      跳 → @38 LOAD m 跳 join / @42 LOAD n 直落）到达 @44 COMPARE_OP；
      _detect_chained_compare_pattern 在 @34 无 COMPARE_OP 处断链 → None。
   修复（标签 [B98-V3R2]，判据均为同层结构事实）：
   ① 新方法 _try_build_ternary_operand_chained_compare(cc_block, ops, chain_blocks,
      merge_hint)：头块非噪声首三指令 == [SWAP(2), COPY(2), 比较指令族] 且末 ∈
      SHORT_CIRCUIT_JUMP_OPS；cleanup=跳转目标块 [SWAP,POP_TOP]；merge 值上下文为
      RETURN_*/STORE_*；沿 merge 链反查提供者——T2=TernaryRegion(merge is cc_block)、
      T1=TernaryRegion(merge is T2.condition_block)，均要求
      _compute_ternary_cond_preload_exprs 为空；left/mid 由 _build_nested_ternary_expr
      重建；comparators=[mid]+逐链段块（三元=merge 命中的嵌套三元 / 前缀 LOAD 重建 /
      值钻石内联）；新增 _extract_inline_ternary_operand_at 重建值钻石（真路径块
      JFL→join、假路径直落、共同前驱 p 的条件跳正常后继集恰 {t,f}）；命中后标记全部
      被消费块（T1/T2/T3.blocks、钻石块、cleanup、链段块），merge 归调用方。
   ② 两处消费者接入：W1=_build_chained_compare_from_region_data 内（IfRegion 宿主：
      _generate_if → _generate_value_context_chain_compare_assign R82 return 分支）；
      W2=_try_build_chained_compare_in_boolop 的 [R106] 回落内（BoolOpRegion 宿主）。
   ③ 发射端抑制守卫 _ternary_chain_compare_host（+静态判定
      _is_ternary_chain_compare_host_block）：TernaryRegion 的 merge 链上溯命中链式比较
      宿主块且恰两个提供者时，该三元不得独立发射（区域迭代序 entry@0/@12 先于宿主
      @22，否则裸 Expr 先出）；_generate_region TernaryRegion 分支改为**代持交权**——
      与 [R59-B Fix2] 同构把宿主结构区域（IfRegion/BoolOpRegion，entry is merge_block）
      就地生成并返回其 AST，比较消费者在宿主生成中以 T1/T2 区域图引用重建完整
      Compare。非命中形状（如 `if (x if c else y):` 普通条件三元、中段单独三元
      `0 < T < 10`）守卫不触发，行为逐位不变（C3）。
   验证：AST chain_two = Return(Compare(IfExp, ['<','<'], [IfExp, c]))、chain_three =
   Return(Compare(IfExp, ['<=','<'], [IfExp, IfExp]))，无裸 Expr 前导；stamp
   r2fix9_rv702 4/4；回归 r2fix9_reg 42/42（e01 15 + e02 18 + b98_resid 5 + 最小重现
   _rv7m 4）；负对照 r2fix9_negctl 60/60；r2fix9_rest 红集合与 r2fix7_rest 逐项一致
   （无回归）。

rv7_02 进度：r2fix7_rest 2/4 → r2fix9 4/4（本批全绿）。

