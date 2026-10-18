# Round 2 · 条件合并块族封闭（If / BoolOp / IfExp）— FIX 报告（终稿）

- 规范：`.trae/specs/attain-true-completeness/`（简称 R）；批次 R2（tasks.md Task 2）
- 树：HEAD `e1c0aabe` 承接（round1 交付后）；`70ed1ec6` 中断存证基线，续作完成后由主代理 `rr-v3r02:` 提交
- 纪律：只改 `core/cfg/**`；判据 = I.4 白名单；G3=0/G4=0；标记 `[Bn-V3R2]`；不提交 git
- 本文件随进度增量追加（防中断）；§1 为增量日志（全程保留），§2-§6 为终稿节。

## §0 范围与结论摘要（终稿）

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

**终稿结论（2026-10-18，主代理验收）**：R2 红单元全部翻绿——十探针复现基线 63/90（r2pre1 41/52 + r2pre2 22/38）→ **终态 90/90**（主代理独立复跑 stamp=r2fix10，逐探针见 §3）。共 17 项修复（§1），涉改 4 文件 54 hunks（+2426/−56，§2），落地标记 `[Bn-V3R2]` 47 处。复核与门禁全过（§4/§5）：负对照九件 60/60、合成非语料 16 探针 79/79、402 八分片 402/402 success + 6617/6617 单元 DEGRADED=0 逐位一致、34 集 1568/1568 REGRESSIONS=0、IV.2 全绿、tests 七套件与基线名单一致、site-packages 零字节差异。新登记两项存量缺口 **B129/B130**（非回归，证据 rec1_probes_r2synth1.json / r2synthcand.json）——主代理裁决：归 **Round 8 全行对抗终审**封闭（登记见 §6 与 tasks.md Task 2）。

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

10. 回归一 b_nest_not_layers（r2fix10_bnnl；e01 15/15、b98_resid 5/5、e02 18/18、
   负对照 60/60）：if not (a and (b or c)): pass 值链经
   _try_build_keeppop_target_grouped（r2fix8 新增）三形态提前折叠返回，
   绕过 or_groups 路径的汇合块 UNARY_NOT 整链包裹（44690-44708 仅查 merge 块
   是否含 UNARY_NOT）→ 外层 not 丢失（if a and (b or c):，真值表翻转）。
   修复：hook 内新增 _wrap_merge_unary_not 闭包（判据同源：merge 块非噪声
   指令含 UNARY_NOT 即包裹 UnaryOp(not)，仅复刻检查 1、不复刻剩余块检查 2——
   三形态 A/B/C 均显式消解并消费尾块，外 not 恒驻汇合块），三个返回点
   （形态 A _folded / 形态 B Or[seg1,seg2_expr] / 形态 C BoolOp(_outer_op,
   [inner,tail])）统一过闭包；None 逐位放行（C3）。
   验证：r7_12 stamp r2fix10_bnnl 7/8（b_nest_not_layers 翻绿，仅剩
   b_ternary_lhs_and）；e01 15/15、b98_resid 5/5 无回归。

11. 回归二 trade_info_utils.get_last_stat（r2fix11_tiu；十探针 83/90、负对照
   60/60、site-packages git clean、pyc_verify single 41/41）：8 语句丢失
   （
esult_data[..]['information']['value'].append((item[12+index] and
   [item[12+index]] or [0])[0]) 及其后 7 条 append）。
   根因链：r2fix6 修复一（_b99_n_prefix）使 B99 前缀块（条件块 @2336）被吸收
   为全链成员，BoolOpRegion entry 从 or 锚块 @2934 前移至 @2336，与镜像
   TernaryRegion@2336 发生「同 entry + 同块集」碰撞；_generate_try_body 派发
   按区域列表序取首个 entry 命中（BoolOp 阶段先于 Ternary 阶段）→ BoolOp 恒
   先命中；其值目标扫描越过汇合块的 [0] 下标消费 + CALL append 抓到下游
   STORE count（假 value_target），值发射既无法表达下标消费语句，汇合块
   整段内容（8 语句）蒸发。基线（cb24db60）中 BoolOp entry=@2934 ≠ 三元
   entry=@2336，try 体派发自然命中 TernaryRegion → andor 旧形查找
   （entry==true_block、纯 or 链、共享 merge）→ Or[And[X,Y],Z] →
   merge-consumer 发射 append 正确。
   修复（两处，判据均为同层结构事实，I.4 白名单）：
   a) _try_build_andor_boolop_from_ternary 增全链头变体（镜像 r2fix6 修复三
      的 _r98r6_full_chain 模式）：BoolOpRegion entry is 条件块、op_chain[0]
      == (条件块,and)、op_chain[1] == (真值块,or)、共享 merge →
      _build_boolop_expression 黑箱重建 + 形状校验 Or[And[..,..],..]，不过
      返回 None 逐位回落（C3）。
   b) _generate_try_body 派发碰撞裁决：命中 BoolOpRegion 且存在未生成、
      entry 同块、块集全同的镜像 TernaryRegion 时跳过 BoolOp（continue），
      让扫描自然推进到镜像 TernaryRegion——与 get_entry_region_for_block
      的同优先级稳定排序裁决（Ternary 后插入列表胜出）对齐，恢复 r2fix6
      修复一之前的等效派发；无镜像或块集不同（纯 and / 纯 or 链无独立假臂）
      判据不命中，BoolOp 派发原样保留。
   验证：regen trade_info_utils git diff 空（与 cb24db60 提交版一字不差）+
   pyc_verify single 41/41；stamp r2fix11_tiu（e01 15 + e02 18 + b98_resid 5 +
   rv7_02 4 + r7_12 7/8）49/50、r2fix11_neg 60/60、r2fix11_ten 十探针 83/90
   （仅剩 b/a/c/d/e 五族）。

12. b_ternary_lhs_and（r2fix12；r7_12 8/8、回归 69/75 无新增红、负对照 60/60）：
   eturn a if flag else b and d\ 输出 \if flag: return a else: return b and d   （真值等价但控制流不同——两臂各自 RETURN vs 单 RETURN 汇合，verify 报
   Different control flow）。结构：IfRegion@0 值菱形（cond=@0 PJF→else，
   then=[@6: a; JUMP_FORWARD→merge]，else=[@10,@14: b and d 链]），
   merge=@16 非噪声恰 [RETURN_VALUE]（函数级裸返回尾，无循环迭代器/
   except 处理器拆除对）；无 TernaryRegion（假臂为多块 BoolOpRegion@10
   merge=@16，三元识别未及此形）。
   修复（_try_build_value_diamond_return 增第三尾形，全部同层结构事实）：
   a) merge 非噪声恰 [RETURN_VALUE] 即命中（反证：字面 if/else-return 两臂
      各以 RETURN_VALUE 收尾无公共汇合块；函数隐式收尾为 [LOAD_CONST None,
      RETURN_VALUE] 两条——均不满足恰一条 RETURN_VALUE 指纹）；
   b) 命中后附加 then 臂流守卫：末条非噪声指令为 JUMP_FORWARD 且落点 IS
      merge（IfExp then 臂恒跳过 else 臂直达汇合；字面 if/else-return 无此
      跳转被排除）；不满足逐位回落既有 if/else 发射（C3）。
   两臂值重建复用既有 _build_value_block_expr（else 臂经 BoolOpRegion@10
   见证重建 And[b,d]，then 臂 Name(a)，黑箱验证）。
   验证：AST Return(IfExp(flag, a, BoolOp(and,[b,d])))；stamp r2fix12_btla
   r7_12 8/8 + r7_04/r7_07/r7_08 22/22；回归 r2fix12_reg（e01 15 + e02 18 +
   b98_resid 5 + rv7_02 4 + exprtail 4/5 + r7_05 15/16 + r7_10 7/8 + v_b46_face
   1/4）红集合与修复前逐项一致；负对照 r2fix12_neg 60/60。
    十探针进度：r2fix11_ten 83/90 → 本修复后 84/90。

13. r7_05 t_listcomp_ternary_filter（r2fix13b 16/16；r2fix17_ten 复跑 16/16、
    负对照 60/60）：listcomp 过滤位三元共存形
    ``[x if flag else 0 for x in xs if (x % 2 if flag else True)]``——CPython
    把 filter 位三元表达式的真值常量 orelse 折叠（cond 假路径直达通过点，
    无假臂指令、无真臂尾 JUMP_FORWARD 融合标记），既有
    `_detect_comp_ternary` 的 Pattern A/B 均不命中 → 过滤条件退化为
    ``flag and x % 2``。修复（comprehension_generator + code_generator，均
    同层结构事实）：
    a) `_detect_comp_ternary` 新增折叠真值 orelse 变体支路：①无前导
       filter 成员（last_filter_end 未被 BACKWARD 跳转推进）；②cond 跳转
       为前向 IF_FALSE；③真臂（cond 至 false_target 间）非空、除末指令外
       无条件跳转、末指令为 BACKWARD IF_FALSE filter 回跳；④false_target
       即通过点（其后至 append 间无 BACKWARD 条件跳转）。归约 =
       IfExp(cond, 真臂剥尾跳, Constant(True))（真值常量 orelse 在 filter
       位由编译器折叠，True/1 同码不可分辨，取规范真值）。
    b) 元素窗含三元（filter 位三元与 elt 位三元共存）：单/双 for 两处
       元素窗重建先以 `_tf_elt_start - 1`（最后一条 filter 回跳）为窗起点
       调 `_detect_comp_ternary` 折叠元素位三元，None 逐字回落 reconstruct
       （C3）。
    c) code_generator 推导式 if 子句括号守卫：ASTNode `__slots__` 使
       `hasattr(if_clause, '_node_type')` 恒 False，IfExp 括号守卫从未生
       效（输出 ``if x % 2 if flag else True`` 语法错，r2fix13 首跑
       compile_error）。判据改 isinstance(if_clause, ASTIfExp)（[C1] 节点
       类型同层事实）；dict 分支与遗留 _node_type 判据原样保留。
    验证：stamp r2fix13b（e01 15 + e02 18 + resid 5 + rv7_02 4 + r7_04 7 +
    r7_05 16/16 + r7_10 7/8 + r7_12 8/8 + r7_07 7/7）。
    十探针进度：r2fix12 后 85/90（v_b46_face n_for_body_nest 随 item14
    前置 WIP 翻绿）→ r7_05 翻绿后 87/90。

14. B78 嵌套三元宿主折叠 v_b46_face 3 红（r2fix14_b78 4/4；r2fix17_ten
    复跑 4/4、负对照 60/60、trade_info_utils git diff 空 + 41/41）：
    ``X if (Y if c2 else Z) else W`` 处于 if 条件位 / while 条件位 / 值
    消费位。前任 WIP 已落 `_try_build_b78_nested_ternary_host`（hook 于
    _generate_if 顶端，值宿主 C 路径已验绿 n_for_body_nest），本批完成
    if/while 宿主（A/B 路径）重写——前任实现的臂出口族判别（T1 双臂
    POP_JUMP_BACKWARD_IF_TRUE→T）与实际字节码不符（while 宿主**首次
    求值链**与 if 宿主逐形相同：双臂 PJF→F + 真值蹦床→体入口 T），
    while 宿主被误判为 if、体/出口全吞。修复（全部同层结构事实）：
    a) 宿主判别重写：先按首次求值指纹提取共享真值落点 T（双臂假值跳
       转 == F、fall-through 蹦床共享）；再以「回边镜像臂」分派——T 存在
       起偏移更大的前驱 p 以回边条件跳转→T 收尾、且 p 值前缀与 bt1/bf1
       值前缀 (opname,argval) 逐位相同（循环尾重求值同一 X 的 a/b 臂）→
       while；否则 if（真 if 宿主 then 体无回边，体内嵌套 while 的回边块
       非条件跳转收尾且值前缀不重合，不误判）。
    b) if 宿主：then 体 T 不预标记（前任预标记使 _process_if_blocks 跳过
       → 体退化为 pass），交其按 entry 锚点发射；区域块集守卫
       （blocks ⊆ 链成员 ∪ {T}，then 多块/异形逐位回落）。F 归属：F 已
       生成不加发；未生成且直线语句块（无控制跳转/循环指令）→ 折叠在 If
       之后加发并登记（F 常被分析层判给永不派发的兄弟 IfRegion，交父级
       静默蒸发，v_if_cond_nest 的 return 0 丢失即此）；未生成且含控制
       跳转 → 放弃折叠（C3）。
    c) while 宿主：LoopRegion（entry/header is T）成员 = 体 + 重求值镜
       像机械。机械走查：root 候选（块尾 = cb2 值指纹后缀）按偏移序逐个
       全链验证——m_bt2/m_bf2 值指纹同源、共享折叠常量假出口通过点
       （F/蹦床→F/NOP 直落 F）、m_K 同源、双 T1 镜像臂值前缀同源 + 回边
       条件跳转→T + 假值蹦床→F；全部成员须在循环成员集内。体切分 =
       成员 − 机械；体块须直线（无任何控制跳转/循环指令）且偏移先于
       root，root 前缀（体尾语句）最后发射；while-else 块存在 / F ∈ 成
       员集 / 区域块集 ⊄ 链 ∪ 成员 → 逐位回落（C3）。F 归属同 b）。
    验证：v_while_cond_nest → ``while ((a if f1 else b) if (c if f2 else
    d) else 0): n -= 1; return n``；v_if_cond_nest → ``if (...): return 1;
    return 0``；n_for_body_nest 保持绿。stamp r2fix14_bnnl 系列后继。
    十探针进度：87/90 → 88/90。

15. B43 链式比较 and 尾操作数（r2fix15b_b43 r7_10 8/8；r2fix17_ten 复跑
    8/8、r7_12 8/8、负对照 60/60）：``return a < b < c and d`` 的
    BoolOpRegion（entry=@32 单成员 [JUMP_IF_FALSE_OR_POP]）经
    `_try_build_chained_compare_in_boolop` 的 [R36] **merge 命中**（chain
    IfRegion 的 merge_block == 链成员块）取得链式比较操作数后，扁平
    or_groups 路径的 fall-through 值块吸收被「chained_compare_expr is
    None」守卫整体跳过——该守卫本意只针对 **entry 命中**（ft 块是链内
    后续 COMPARE 段），对 merge 命中误伤：链内块全部位于成员块之前，
    ft 块（LOAD d）是真操作数，跳过致 ``and d`` 整段丢失（regen 只剩
    ``return a < b < c``）。修复（`_build_boolop_expression_inner` 扁平
    路径守卫收窄，[B43-V3R2]）：chained-compare 钩子命中时按命中形分派
    ——chain_block 自身是链头（R106 直检）或存在 entry/condition_block
    同为 chain_block 的链 IfRegion（entry 命中）→ 跳过 ft 吸收（旧行
    为）；仅 merge 命中 → 保留 ft 吸收（真操作数）。判据 = 区域结构身
    份（entry/merge 指针 + 链头 opcode 形态），I.4 白名单。首版曾把布
    尔条件写反（r2fix15 实测 c_chain_or_and_combo / b_nest_with_chain 两
    回归），修正后 r2fix15b 全绿。
    验证：r7_10 8/8（c_chain_and_combo → ``return a < b < c and d``）；
    r7_12 8/8 无回归。
    十探针进度：88/90 → 89/90。

16. B123 while 头链式比较 + IfExp 尾操作数（exprtail v3，r2fix16b_b123
    5/5；r2fix17_ten 复跑 5/5、负对照 60/60）：``while 0 < x < 10 and
    (y if y else x):`` 的尾操作数是多块钻石（test/then/else），超出
    B104-R2a 单块尾吸收判据域（v2 round8 REVIEW2 §5 登记的判据方向 =
    尾操作数吸收扩为块集）。while-true cc 回溯把钻石 test/then 半途认领
    （else 臂漏出），循环头退化为纯链、钻石泄漏为体
    （``if y: continue / y / continue`` 垃圾）。修复（判据全部 I.4 白名
    单，v2 登记方向落地）：
    a) 识别层新方法 `_b123_absorb_ifexp_tail_diamond`（region_analyzer，
    hook 于 while-true cc 回溯链头命中后，与前置 and 吸收镜像序对偶）：
    (a) arm1 = header 蹦床前驱，PJF 收尾且失败边收敛链末段出口；b) test
    = arm1 前驱，PJF 收尾、ft==arm1、jt==arm2；c) arm2 出口协议同
    arm1，两臂 ft 直落 header 或经透明蹦床；d) 三块求值窗纯值求值（无
    STORE/DELETE/POP_TOP/IMPORT/RETURN/内部跳转）；e) 回边重检副本：
    then/else 各有 `_b104r2_has_recheck_mirror`，test 镜像 = 体内块段序
    同 + jt/ft 双后继均回边条件跳转→header + 段序对位。命中则三块并入
    _cc_pre_loop_blocks + metadata `cc_mixed_cond_tail_diamond`。
    b) 生成层 `_loop_generate_while` cc 分支：`_b123_ifexp_from_tail_diamond`
    三窗黑箱重建 IfExp 追加为 BoolOp(And) 末位（[Compare, IfExp]）；
    三块登记 generated；体内钻石重检镜像集（arm 镜像 = 回边条件跳转→
    header + 段序 ∈ {then,else} 段序；test 镜像 = 段序同 + jt/ft 双臂
    镜像段序对位；透明蹦床 = 全协议噪声 + 后继全落镜像集）整块抑制。
    c) 循环出口归属（与 B78 F 块同构）：出口块（then/else 臂共享假值目
    标，如 ``return n``）被分析层判给永不派发的臂内 IfRegion（else=出
    口）→ 交父级静默蒸发。已生成不加发；未生成且直线语句块 → While 之
    后加发并登记；含控制跳转 → 不加发（C3）。仅钻石元数据命中时执行。
    验证：v3 → ``n = 0; while 0 < x < 10 and (y if y else x): x += 1;
    n += 1; return n``（regen 与源码逐字一致）；exprtail 5/5。
    十探针进度：89/90 → **90/90 全绿**（r2fix17_ten）。

17. 合成非语料交叉变体实证（r2synth2 16 探针 79/79 全绿）+ 对抗攻击新登记
    两项（B129/B130，如实移交，非打回）：对 items 1-16 全部九个修复族各构造
    ≥2 个合成非语料探针（rec1_synth_* 16 文件 stage 于 test_repros/round2/，
    rec1_run.py @ 前缀跑绿）：B98 值链族（b98val_a/b）、e02 宿主族
    （e02host_a/b）、三元链式比较族（rv7cctern_a/b）、派发碰撞族
    （dispatch_a）、值菱形 Return 族（vdret_a）、推导式折叠过滤器族
    （compfilter_a/b）、B78 宿主族（b78host_a/b：if/while/值宿主·多位
    形）、B43 族（b43tail_a/b：尾/首/双链/混合算符）、B123 族（b123dia_a/b：
    变名/调用 else 臂/测试变量异名/双语句体/混合链算符）。首攻（r2synth1
    73/78）暴露 5 个域外新破口，按 v2 round8 B123 登记先例如实登记移交：
    - **B129**（新登记）：B98 值语境融合链**裸宿主位**——`return ((p or q)
      and r) > 2`（裸 return 位 compare-cross）、裸 `return sink((p or q)
      and r)`（无 for+if 双层包装的 call 消费）、裸/单层 `if (w := (p or
      q) and r):`（walrus-if）。items 1/6 修复（锚点走查/P2-1/merge-
      consumer）实证依赖 for+if 双层包装宿主形状；裸位产物 = 链裸 Expr +
      消费语句蒸发（`return` 整句丢失）。证据：rec1_probes_r2synth1.json
      / r2synthcand.json（x1/x2/x3）。
    - **B130**（新登记）：**双栈三元简单比较**——`t = (a if c1 else b) <
      (x if c2 else y)`（store 位）与 `if (a if c1 else b) <= (x if c2
      else y):`（if-cond 位）：单条 COMPARE_OP 直消费两栈上三元结果，无
      SWAP(2)+COPY(2) 链协议 ⇒ item 9 判据域外；产物 = T1 裸 Expr 外漏 +
      T2 退化为赋值/裸条件。证据：rec1_probes_r2synth1.json。
    两项均为存量缺口（本轮修复前后行为一致，非回归；十探针 90/90、负对
    照 60/60、trade_info_utils 41/41 无回退佐证），建议主代理裁决归 R2 续
    批或 R8 对抗终审封闭。**终稿裁决：归 Round 8 全行对抗终审封闭**（存量
    缺口不阻塞 R2 交付；R2 交付范围 = round1 定案红单元，已全部翻绿）。

## §2 变更清单（54 hunks · +2426 / −56，vs `cb24db60`）

| 文件 | hunks | 增/删 | 行锚（新增侧，前 10） |
|---|---|---|---|
| core/cfg/code_generator.py | 1 | +7 / −1 | 5569（[B98-V3R2 修复] 推导式 filter 位 IfExp 括号守卫 isinstance 化；原 `hasattr(_node_type)` 判据恒 False） |
| core/cfg/comprehension_generator.py | 7 | +142 / −30 | 1205, 1555, 2346, 2406, 2426, 2734, 2986 |
| core/cfg/region_analyzer.py | 14 | +199 / −5 | 4852, 5440, 5610, 6095, 32556, 32951, 33614, 33627, 33766, 33974, … |
| core/cfg/region_ast_generator.py | 32 | +2078 / −20 | 4787, 8624, 8637, 8727, 8809, 9481, 15968, 16164, 18158, 18186, … |

- 完整逐 hunk `@@ … +a,b @@` 清单：`_r2_hunks.txt`（`git diff cb24db60 --unified=0 -- core/cfg`）。
- 标记分布：region_ast_generator 34 / region_analyzer 6 / comprehension_generator 6 / code_generator 1 = 47 处。

## §3 前后读数（复现基线 → 终态）

| 探针 | r2pre 基线 | 终态（r2fix10 主代理复跑） |
|---|---|---|
| v_b46_face | 1/4 | 4/4 |
| b44_r712（r7_12） | 6/8 | 8/8 |
| r7_10 | 7/8 | 8/8 |
| r7_04 | 6/7 | 7/7 |
| r7_05 | 15/16 | 16/16 |
| rv7_02 | 2/4 | 4/4 |
| exprtail | 4/5 | 5/5 |
| e01_b98matrix | 7/15 | 15/15 |
| e02_b98hosts | 13/18 | 18/18 |
| b98_resid | 2/5 | 5/5 |
| **合计** | **63/90** | **90/90** |

修复中途逐探针进度见 §1（e01 7→8→10→11→12→13→15；e02 13→18；… → r2fix17_ten 90/90 全绿）。

## §4 复核（原探针 + 合成交叉变体 + 负对照）

- 原探针：§3 终态 90/90（修复会话 r2fix17_ten 与主代理独立复跑 r2fix10 双向一致）。
- 负对照九件（r7_07 / r7_08 / rv8_01 / rv8_02 / r10_04 / r10_15 / r10_21 / rv10_32 / r8_06）：基线 60/60 → 终态 60/60（站桩回归不变差；主代理独立复跑 stamp=r2fix18_neg，`rec1_probes_r2fix18_neg.json`）。
- 合成非语料交叉变体（9 修复族 × ≥2 探针 = 16 件，stage 于 `test_repros/round2/`，`rec1_synth_*.py`）：r2synth2 79/79 全绿；主代理独立复跑 stamp=r2fix18_synth 79/79（`rec1_probes_r2fix18_synth.json`）。首攻 r2synth1 暴露的 5 个域外单元按登记先例如实转为 B129/B130（§0/§6 裁决）。
- trade_info_utils（P0 回归器）：regen 后 `git diff --stat site-packages/` 为空（字节一致）+ verify 41/41。

## §5 门禁读数（终态）

| 门禁 | 读数 | 证据 |
|---|---|---|
| 402 八分片 | 8/8 shard success，files 402/402，units 6617/6617 | `shard0..7_report_new.json` |
| REGRESSIONS | 0（402 全 success ∧ 单元数无降 ∧ 无缺失/新增文件） | `_r2fix18_regcmp.json`（vs `baseline/kit/baseline42` 逐文件对比，主代理产出） |
| 34 集 small34 | 1568/1568，success_rate 1.0，REGRESSIONS=0，IMPROVED=33 | `small34_report_new.json`（a/b 分跑 515+1053） |
| IV.2 | IMPORT_OK / COMPILE_OK / BOM 单头 / G3=0 / G4=0 全绿 | `r2_fv_iv2.json`（`iv2_recheck_r2.py`） |
| tests 七套件 | 2 failed / 282 passed / 2 xpassed，失败名单与基线一致（test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function） | `_r2fix18_pytest7.txt` |
| 产物字节 | site-packages 零差异（git 工作树干净） | `git diff --stat` 空 |

## §6 落地声明

- **代码已落地**（树内 4 文件 54 hunks，§2；主代理以 `rr-v3r02:` 提交）。
- 标记审计：`grep [Bn-V3R2]` = 47 处（region_ast_generator 34 / region_analyzer 6 / comprehension_generator 6 / code_generator 1）；G3=0（diff 新增方法无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_temp_` 前缀）；G4=0（diff 新增行无硬编码规模上限疑似）；BOM：region_ast_generator.py / region_analyzer.py 保持 efbbbf 单头，comprehension_generator.py / code_generator.py 原无 BOM 维持——均与改动前一致。
- 判据合规：全部新增识别走 I.4 白名单（块末 opcode / 前驱后继 / 异常边 / 区域成员关系）；形状不过一律 C3 回退（IfExp / 原路径），无语料特判、无文件名/行号分支。
- 裁决登记（主代理）：**B129**（B98 值链裸宿主位：裸 return compare-cross / 无包装 call 消费 / walrus-if）与 **B130**（双栈三元简单比较：store 位 / if-cond 位）为存量缺口（修复前后行为一致，非回归），归 **Round 8 全行对抗终审**封闭；届时按每行探针齐备要求一并处理，必要时回插小批次。已记入 tasks.md Task 2 增补行。

