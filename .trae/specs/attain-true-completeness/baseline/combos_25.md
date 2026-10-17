# 组合级挂账 25 号分层（WIKI_REVIEW §3.3 原样摘录）

- 源：`.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round10/WIKI_REVIEW.md` §3.3（行 195-236）
- 版本：v7 终表（2026-10-17；冻结树 HEAD `3e0d6905`）
- 用途：Task 0 承接基线——组合级 25 号「清零 9 / 维持 16」；供 Task 1「组合级 25 号现状复核」（tasks.md 1.4）逐项对账。

## 25 号清单口径（WIKI_REVIEW.md:197）

> 25 号清单（权威 = `harden-completed-forms-10rounds` spec `rounds/round10/REVIEW.md` §4.1 残留决策表 + `REVIEW2.md`）：B42–B51 / B56–B65 / B69–B71 / B73–B76 内未封闭部分，扣除已划除 B45/B64。

## 清零 9（对抗规范 v2 round1 批次 A/B/C + 同链实证）（WIKI_REVIEW.md:199-213）

| 编号 | 口径/依据（一行） |
|---|---|
| B46 尾项 | 批次 A（`FIX_A.md` §2，t_nest_in_condition）† |
| B48 残留变体 | 批次 A（`FIX_A.md` §1，t_host_try_sections / B50 同链；`REVIEW2.md` §3 如实登记 t_host_while_body 另存变体）† |
| B74 | 批次 A（`FIX_A.md` §3，match case 体首幻影 guard） |
| B65 | 批次 B（`VERIFICATION.md:44`） |
| B71 | 批次 B（fin_continue/fin_break）+ 批次 C（边类型封闭 `12d7ddb9`；残余 fin_continue 转 B79 续接）† |
| B73 | 批次 B（`FIX_B.md` §4，try 四段 import 宿主泄漏） |
| B75 | 批次 B（`FIX_B.md` §5，try 宿主 global 5/6→6/6） |
| B76 | 批次 B（`FIX_B.md` §2，augassign×BoolOp RHS 体蒸发） |
| B50 | round1 `REVIEW2.md` §3 实测「封闭真实（+2），外推过」（v_two_except_fin 4/4；归因链 6/8→7/8 真实 +1） |

> 注（WIKI_REVIEW.md:213 原样摘录）：v2 round1 登记封闭 = 批次 A（B48 残留变体/B46 尾项/B74）+ 批次 B（B71/B73/B75/B76/B65）+ 批次 C（B71 边类型）= 8 项（`VERIFICATION.md:44`）；+ B50 同链实证 = **清零 9**。† = 台账/round9 仍以该编号作行内沿袭锚点的**保守带账**项，归属裁决留主代理。

## 维持 16（WIKI_REVIEW.md:215-234）

| 编号 | 残余/现状（一行，源 = round1 `REVIEW.md` §2 逐项复验表） |
|---|---|
| B42 | 部分（r7_01 t_arg_multi_mixed 于合并期翻正）；r7_04 t_compare_lhs_only、r7_05 t_listcomp_ternary_filter 维持（C1 参数栈位/比较 LHS/推导式 filter） |
| B43 | r7_10 c_chain_and_combo（链式比较×BoolOp 汇合块消费点错位） |
| B44 | r7_11/r7_12 BoolOp 重复/三层/深右嵌套（B1 双入口同族）；round9 证据缺口（未抽验如实标注） |
| B47 | r7_06 await×三元臂 ×3（外提越 POP_JUMP 对） |
| B49 | r7_08 t_host_for_else（else 体三元增强赋值，前驱集归属） |
| B51 | rv7_02 if 三元链复合值 ×2 |
| B56 | r8_07 r8_assert_nested_func（幻影 else 源）；r8_10 assert×三元 |
| B57 | r8_10 r8_x_for_iter_ternary |
| B58 | r8_10 r8_x_raise_ternary_class |
| B59 | r8_09 r8_dh_for_else_del（深宿主 with 首赋值族） |
| B60 | r8_09 r8_dh_with_assert |
| B61 | r8_09 r8_dh_match_multi + r8_11 r8_dh2_match_guard |
| B62 | r7_14 h_return_composite（return(call+BoolOp) 尾语句蒸发） |
| B63 | rv8_02 tryfin_then_more（空 try/fin 后非纯常量尾随段） |
| B69 | rv9_01 emptyfin_in_if（if 臂内空 try/fin 吞尾随 return） |
| B70 | rv9_02 while_with_whole_body（while True+with 幻影 break） |

## 口径差另册（如实登记）（WIKI_REVIEW.md:236 原样摘录）

> **口径差另册（如实登记）**：round1 `REVIEW.md` §2.2(g) 已登记「决策表含 B52/B53/B63 而 III.5 区间名单未列」的子集差——**B52/B53**（决策表含、25 号区间外，实测残留持平）+ **B11-R2**（r4_or4_and2，1/2 持平，独立另册）建议 10.3 归档时统一口径；**B63 在 25 号区间内（B56–B65），维持**（非另册）。
