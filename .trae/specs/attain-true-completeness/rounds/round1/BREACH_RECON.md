# Round 1 · 破口现状全量复现与证据重建（BREACH_RECON）

- 执行：评审工程师（主代理验收）；日期 2026-10-17
- 树：HEAD `e1c0aabe`（rr-v3r00 承接；`git diff --stat 3e0d6905..HEAD` 证实 core/ 与冻结树零差异，仅 wiki/ + 本规范新增）；工作树干净
- 判据唯一 = `scripts/pyc_verify.py single`（RV2 口径：先 `python pycdc.py <pyc> -o <base>OK.py` regen，再 verify；pylingual compare_pyc）；python 3.11.7
- 探针纪律：源树 `test_repros/` 只读引用 → 拷入 `test_repros/round1/`（stage，前缀 `rec1_`）后 regen；绝不回写源树（test_repros/ 内 *OK.py 为 git 追踪件）
- 纪律声明：零 `core/`、`wiki/`、`tests/` 改动；零 git 写操作；命令 ≤300s（B122 挂死探针用 60s 分片硬杀）；非 ASCII 输出先落文件

---

## §0 探针工作流与命令（可复现）

驱动：`rounds/round1/rec1_run.py`（RV2；逐探针记录 `pyc_src_rel`/`pyc_src_sha`/`staged_pyc`/regen_rc/status/units/failures；挂死探针支持 `rel#T<secs>` 超时覆盖，regen HANG 时记录 `status=hang` 并跳过 verify）。

命令形式（全部实测通过，共 10 个 run）：

```
python -X utf8 .trae/specs/attain-true-completeness/rounds/round1/rec1_run.py \
  --stage .trae/specs/attain-true-completeness/test_repros/round1 \
  --log   .trae/specs/attain-true-completeness/rounds/round1 \
  --stamp <stamp> name1=rel1 name2=rel2 ...
```

| 证据 JSON（`rounds/round1/`） | 批次 | 探针数 | 摘要 |
|---|---|---|---|
| `rec1_probes_transfers_b127_b128.json` | 移交复跑 | 2 | B127 15/16、B128 10/11（真实破口） |
| `rec1_probes_yield_b44.json` | 移交复跑 | 5 | Yield 存量 3 探针空转 + B44 r7_11/r7_12 |
| `rec1_probes_yf9_rebuild.json` | 重建 | 7 | Yield-F9 单元级重建（arg/boolop/ret/cond 非法；prec 语义漂移） |
| `rec1_probes_rec1_rowsA1.json` | 表A 行锚点① | 12 | v_b46_face/r7_07/x01/v_b71_face/x10/c04/m02/m06/x04/x05/v_b74_face/x08 |
| `rec1_probes_rec1_rowsA2.json` | 表A 行锚点② | 12 | c13/c02/m01/m08/rv10_32/r7_08/r10_04/v_b73_face/r10_15/v_b75_face/n9v9_stmt_sweep/r8_07 |
| `rec1_probes_rec1_combos1.json` | 表B/C + 组合 | 12 | e01/e02/b98_resid/exprtail/c4_20/r7_10/r7_01/r7_04/r7_05/r7_06/rv7_02/r7_14 |
| `rec1_probes_rec1_combos2.json` | 组合 + 另册 | 13 | r8_09/r8_11/rv8_02/rv9_01/rv9_02/rv8_01/r10_21/v_b50_face/v_b76_face/rv7_04/r4_or4_and2/r8_08/r8_10 |
| `rec1_probes_rec1_extra.json` / `rec1_probes_rec1_extra2.json` | 补充 | 2+1 | x02、r8_04；r8_06 |
| `rec1_probes_rec1_b122.json` | B122 专项 | 2 | 双探针 60s 硬杀 HANG（`rel#T60`） |

对账基线：round9 `r9v9_full_residual_c*` / `r9v9_regress_probe42_c*` / `r9v9_b122_readings.json` / v2 round1 `REVIEW.md` §2 / round9 `REVIEW_DRAFT.md` §3.2 / `FIX_R9.md` §6。**全表读数与基线逐位持平或改善，零 pass→fail（WORSE=0）**。

---

## §1 移交项四项终判

| 移交项 | 终判 | 实测读数 | 关键证据 |
|---|---|---|---|
| **B127**（slice 悬挂链，round3 F4 存量补编号） | **真实破口** | `e07_g4_star_slice_containers` **15/16**；fail = `f_slice_expr_bounds`（Different control flow） | 产物 `if i and i:` + while 体坍缩为裸名 `b`，与 `FIX_R9.md` §4 逐字一致；`rec1_probes_transfers_b127_b128.json` |
| **B128**（await×条件，round3 F9 同源） | **真实破口** | `e12d_g9_awaits` **10/11**；fail = `f_await_cond_pos`（Different control flow） | 产物含幻影 `await src(i)` 语句重复于 `if await src(i):` 前；同上 JSON |
| **Yield-F9**（round3 存量探针重建） | **真实破口**（证据缺口已补齐，单元级读数在案） | 存量 e12b/e12c/e12f：compile_error 0/0 空转复现（探针退化）；重建 7 探针：**assign 2/2 绿、from 6/6 绿**；**arg/boolop/ret/cond = compile_error**（产物非法）；**prec 1/2**：`f_yield_binop` Different bytecode（line 7 offset 22）——原 `(yield i) + 1` 被重建为 `yield i + 1`（语义漂移，可编译） | `rec1_probes_yield_b44.json` + `rec1_probes_yf9_rebuild.json`；重建源 `rec1_yf9_*.py/pyc` 在 stage |
| **B44**（BoolOp 重复/三层/深右嵌套） | **真实破口**（部分封闭） | `r7_11_boolop_mixed` **7/7 全绿**（`b_and_or_repeat` 翻正；历史 6/7）；`r7_12_boolop_nest` **6/8**（`b_nest_three_layers` 翻正；残余 = `b_nest_deep_right` + `b_ternary_lhs_and`） | pyc_sha r7_11 `5577bb96a009`、r7_12 `f69583856ec6` 与历史一致；`b_ternary_lhs_and` 按 round1 REVIEW 独立行「B46-b_ternary_lhs_and」归 If 行 |

---

## §2 25 行破口逐行现状定案表（Σ=25）

口径：行清单 = `baseline/breaches_25rows.md`（WIKI_REVIEW §3.1）；三分 = **真实破口**（存在归于本行族系的 live 红单元）/ **已封闭待复验**（本行全部 live 锚点绿，待对抗复验裁决）/ **证据缺口**（无可用读数）。

| # | 行（表） | 台账族锚点 | 本轮实跑读数（failures） | 三分 | 备注 |
|---|---|---|---|---|---|
| 1 | If（A） | B46 尾项+B78 | `v_b46_face` **1/4**（v_while_cond_nest/v_if_cond_nest/n_for_body_nest）；`r7_12::b_ternary_lhs_and` 红；`r7_07::t_nest_in_condition` **7/7 绿** | **真实破口** | B46 尾项翻正；残余 = B78×3 + B46 变体 `b_ternary_lhs_and` |
| 2 | While（A） | B94 | `x01` **4/7**：`if_in_while`（B94）+ `if_in_try`/`if_in_match`（归 Try/Match 行） | **真实破口** | 与 probe42 基线逐位持平 |
| 3 | Break（A） | B79 | `v_b71_face` **3/4**：`v_nest_fin_continue` | **真实破口** | B71 本体已清、残余转 B79 续接（与清零口径一致） |
| 4 | Continue（A） | B97 | `x10` **2/3**：`h_basic` | **真实破口** | 持平 |
| 5 | Try（A） | B87/B73/B75 | `c04` 5/6（CTryNest）、`m02` 2/3、`m06` 0/1、`x04` 6/7（try_in_if）、`x02` 5/7（for_in_try） | **真实破口** | B73（r10_04 3/3 绿）、B75（r10_15 6/6 绿）子锚点已翻正；行红由 B87 宿主系承担 |
| 6 | With（A） | B93 | `x05` **6/7**：`with_in_match` | **真实破口** | 持平 |
| 7 | Match（A） | B74+B122 | `B122` 双探针 60s 硬杀 **HANG**（维持）；`x01::if_in_match` 红；`v_b74_face` **4/4 绿**（B74 翻正） | **真实破口** | 行红 = B122 挂死 + match 宿主单元；B74 清零证实 |
| 8 | Raise（A） | B87 变体 | `x08::raise_leaf` **翻正**（B126-R2 附带）；`r8_08` **9/9 绿**；残余红：`r8_10::r8_x_raise_ternary_class`（B58）、`c13::CMisc.boom`（raise 蒸发+循环降级） | **真实破口**（证据重组） | 原锚点失效；新红单元行归属见 §5-9 |
| 9 | Assert（A） | B56 | `x08::assert_leaf` 红；`r8_07` 10/11（r8_assert_nested_func）；`r8_10::r8_x_assert_ternary` 红；`n9v9_stmt_sweep` **6/6 绿**（B126 翻正） | **真实破口** | B126 清除证实 |
| 10 | Return（A） | B88 | `x08::return_leaf` 红；`c13` 2/3（CMisc.boom）；`c02` 7/7 绿 | **真实破口** | c02 锚点引用已过时（live 绿） |
| 11 | Delete（A） | B84 | `r8_04_delete_forms` **10/10 绿**；`x08::delete_leaf` 绿；`m01` 5/5、`m08` 2/2 绿；c13 红单元非 del 形态 | **已封闭待复验** | 台账「m01/m08/c13 del 蒸发」全数翻正（§5-1） |
| 12 | AugAssign（A） | B76+B48 残留变体 | `rv10_32` **8/8 绿**；`r7_08` **8/8 绿**（t_host_while_body/t_host_try_sections/t_host_for_else 全绿）；`v_b76_face` 4/4 绿；`r8_06_augassign_ops` 10/10 绿 | **已封闭待复验** | 含 B48 残留变体（r7_08）一并翻正（§5-1） |
| 13 | Import（A） | B73 | `r10_04_import_try_cross` **3/3 绿**（B73 清零证实）；残余红 = `v_b73_face` 2/3：`v_imp_cond_fin`（B80 形態） | **真实破口** | B73 本体翻正；残余归 B80（25 行外编号，行内沿袭） |
| 14 | Global（A） | B75 | `r10_15_global_hosts` **6/6 绿**（B75 清零证实）；残余红 = `v_b75_face` 2/3：`v_swap_arm_returns`（try 区间错位 + global 声明随体丢失，B82-v_swap） | **已封闭待复验** | v_swap 归 B82/Try 系（§5-1）；行归属留主代理裁决 |
| 15 | BoolOp（B） | B98 | `e01` **7/15**（8 单元红）、`e02` **13/18**（5 单元红）、`b98_resid` **2/5**（r_d1/r_e3/r_g2） | **真实破口** | 双树逐位同败维持 |
| 16 | IfExp（B） | B123；B124 已封闭留档 | `exprtail` **4/5**：`v3` 红（B123）；v1/v2（B104 族）已翻正；B124 单元 `r8_10::r8_x_with_ternary` 绿 | **真实破口** | B124 封闭留档 live 证实 |
| 17 | Slice（B） | B127 | `e07` 15/16：`f_slice_expr_bounds`（§1） | **真实破口** | 本轮补编号重建 |
| 18 | ListComp（B） | B112② | `c4_20` **21/24**：`e07_async_closure.outer.inner.<listcomp>`（Different bytecode Missing） | **真实破口** | 持平 |
| 19 | Await（B） | B112①+B128 | `c4_20::e05_async_compound.go` 红（B112①）；`e12d::f_await_cond_pos` 红（B128）；`e12e` 绿 | **真实破口** | 持平 |
| 20 | Yield（B） | round3 F9 存量 | 重建单元级读数（§1）；存量 e12b/c/f 探针退化 | **真实破口** | 证据缺口已补齐 |
| 21 | augmented_assign（C） | B76+B48 残留变体 | 同 #12（全绿） | **已封闭待复验** | 镜像行随 #12 |
| 22 | await_expr（C） | B112①+B128 | 同 #19 | **真实破口** | 镜像行随 #19 |
| 23 | global_nonlocal（C） | B75 | 同 #14 | **已封闭待复验** | 镜像行随 #14 |
| 24 | match_statement（C） | B74+B122 | 同 #7 | **真实破口** | 镜像行随 #7 |
| 25 | slice（C） | B127 | 同 #17 | **真实破口** | 镜像行随 #17 |

**三分统计**：真实破口 **20**（表A 11 + 表B 6 + 表C 3）＋ 已封闭待复验 **5**（Delete / AugAssign / Global / augmented_assign / global_nonlocal）＋ 证据缺口 **0** = **Σ 25 ✓**（表A14 + 表B6 + 表C5 = 25 与台账逐行一致）。

---

## §3 组合级 25 号现状表

### 3.1 清零 9（抽样复核 ≥3 → 本轮 9/9 全数实跑）

| 编号 | 本轮实测 | 判定 |
|---|---|---|
| B46 尾项 | `r7_07::t_nest_in_condition` **7/7 绿**（round1 时 6/7） | **清零成立** |
| B48 残留变体 | `r7_08::t_host_while_body`（同文件 t_host_try_sections/t_host_for_else）**8/8 全绿** | **清零成立**（含另存变体） |
| B74 | `v_b74_face` **4/4 绿** | **清零成立** |
| B65 | `rv8_01_chain3_subscript` **7/7 绿** | **清零成立** |
| B71 | `v_b71_face` 3/4 + `r10_21_fin_loopctrl` **4/4 绿** — 唯一红 = `v_nest_fin_continue`（残余转 B79 续接） | **清零成立**（残余按口径归 B79） |
| B73 | `r10_04_import_try_cross` **3/3 绿**；残余 `v_b73_face::v_imp_cond_fin`（B80） | **清零成立**（残余归 B80） |
| B75 | `r10_15_global_hosts` **6/6 绿**；残余 `v_b75_face::v_swap_arm_returns`（B82-v_swap） | **清零成立**（残余归 B82） |
| B76 | `v_b76_face` **4/4 绿** + `rv10_32` 8/8 绿 | **清零成立** |
| B50 | `v_b50_face` **4/4 绿** | **清零成立** |

### 3.2 维持 16（逐项实跑）

| 编号 | 本轮实测 | 判定 |
|---|---|---|
| B42 | `r7_01` **9/9 绿**（t_arg_multi_mixed 翻正）；`r7_04` 6/7（t_compare_lhs_only）、`r7_05` 15/16（t_listcomp_ternary_filter.<listcomp>）红 | 维持（红 2 单元；r7_01 翻正） |
| B43 | `r7_10` 7/8（c_chain_and_combo） | 维持 |
| B44 | `r7_11` 7/7 绿（翻正）；`r7_12` 6/8（b_nest_deep_right 红；b_nest_three_layers 翻正；另 b_ternary_lhs_and 归 B46 变体） | 维持（残余 1 单元） |
| B47 | `r7_06` 7/10（t_await_ternary_branches / t_await_assign_ternary / t_await_deep_ternary） | 维持 |
| B49 | `r7_08::t_host_for_else` **8/8 绿** | **已翻正**（§5-2） |
| B51 | `rv7_02` 2/4（chain_two_ternary / chain_three_ternary） | 维持 |
| B56 | `r8_07` 10/11（r8_assert_nested_func）；`r8_10::r8_x_assert_ternary` 红 | 维持 |
| B57 | `r8_10::r8_x_for_iter_ternary` 红 | 维持 |
| B58 | `r8_10::r8_x_raise_ternary_class` 红（产物 = `pass` 整体蒸发） | 维持 |
| B59 | `r8_09::r8_dh_for_else_del` 红 | 维持 |
| B60 | `r8_09::r8_dh_with_assert` 红 | 维持 |
| B61 | `r8_09::r8_dh_match_multi` + `r8_11::r8_dh2_match_guard` 红 | 维持 |
| B62 | `r7_14` 5/9（h_return_composite 等 4 单元） | 维持 |
| B63 | `rv8_02_with_tryfin_constret` **7/7 绿**（tryfin_then_more 在内） | **已翻正**（§5-2） |
| B69 | `rv9_01` 4/5（emptyfin_in_if） | 维持 |
| B70 | `rv9_02` 4/5（while_with_whole_body） | 维持 |

小结：维持 16 中 **14 项维持红、2 项已翻正**（B49/B63）；B42/B44 部分翻正（残余红各 2/1 单元）。

### 3.3 口径差另册（如实登记）

| 编号 | 本轮实测 | 判定 |
|---|---|---|
| B52 | `rv7_02::chain_two_ternary/chain_three_ternary` 红（与 B51 同单元——口径差重叠，§5-7） | 维持红 |
| B53 | `rv7_04_dict3_ternary` 2/3（dict3_nested_value 红） | 维持红 |
| B11-R2 | `r4_or4_and2` 1/2（or4_and2 红） | 维持红 |

---

## §4 行→批次映射（R2–R7；对齐 tasks.md Task 2–7 攻击名单 + 本轮 live 残红）

| 批次 | 升格行 | 行清单（Σ） | 转移交红单元（live） | 组合号（tasks.md 名单） |
|---|---|---|---|---|
| **R2** 条件合并块族 | If / BoolOp / IfExp | If、BoolOp、IfExp（3） | v_b46_face×3（B78）、r7_12::b_ternary_lhs_and（B46 变体）、e01×8/e02×5/b98_resid×3（B98）、exprtail::v3（B123） | B98、B43、B44（r7_12::b_nest_deep_right）、B46 尾项【已清·复验】、B78、B123、B51、B42（r7_04/r7_05）、B49【已翻正·复验】 |
| **R3** try-raise-assert-宿主族 | Try / Raise / Assert / Import / Global | Try、Raise、Assert、Import、Global、global_nonlocal（6） | c04::CTryNest、m02、m06、x04::try_in_if、x02::for_in_try（B87 系）、v_b73_face::v_imp_cond_fin（B80）、r8_07::r8_assert_nested_func、x08::assert_leaf、r8_10::r8_x_assert_ternary（B56）、r8_10::r8_x_raise_ternary_class（B58）、c13::CMisc.boom | B87、B73【已清·复验】、B75【已清·复验】、B56、B58、B63【已翻正·复验】、B69 |
| **R4** await-挂起链族 | Await / ListComp / await_expr / Yield | Await、ListComp、await_expr、Yield（4） | c4_20::e05_async_compound.go（B112①）、c4_20::e07_async_closure.outer.inner(.listcomp)（B112②）、e12d::f_await_cond_pos（B128）、yf9 arg/boolop/ret/cond/prec（F9） | B112①、B112②、B128、B47 |
| **R5** match-with 幻影族 | Match / With / match_statement | Match、With、match_statement（3） | B122 双探针 HANG、x01::if_in_match、x05::with_in_match（B93） | B74【已清·复验】、B122、B93、B61、B70 |
| **R6** 循环控制族 | Break / Continue / While | Break、Continue、While（3） | v_b71_face::v_nest_fin_continue（B79）、x10::h_basic（B97）、x01::if_in_while（B94） | B79、B94、B97、B71 残余（fin_continue 转 B79） |
| **R7** 赋值-删除-return-slice 族 | Delete / AugAssign / Return / Slice / augmented_assign / slice | Delete、AugAssign、Return、Slice、augmented_assign、slice（6） | x08::return_leaf（B88）、c13::CMisc.boom、e07::f_slice_expr_bounds（B127）【#12/#11 待复验：rv10_32/r8_06/r8_04 全绿】 | B76【已清·复验】、B48 残留变体【已清·复验】、B84【待复验】、B88、B62、B127、B59、B60 |

> 归属裁决点：`c13::CMisc.boom`（raise 蒸发 + while/break/continue 降级混合宿主）横跨 Raise/Return/Break 行——按产物主形态建议归 R3（raise 尾闩）或 R6（循环控制），留主代理裁决（§5-9）；`x01::if_in_try` 归 R3；`x01::if_in_match` 归 R5；`v_b75_face::v_swap_arm_returns`（B82-v_swap）建议随 Try 行入 R3 评估（台账未列 B82 于 Task 3.1，需主代理确认范围）。Σ 行归属：3+6+4+3+3+6 = **25 ✓**。

---

## §5 异常/矛盾（对账发现，如实登记）

1. **台账 4 行锚点已失效/转换（round10 WIKI_REVIEW 未同步）**：
   - Delete（B84）：`r8_04` 10/10 + `x08::delete_leaf` + `m01`/`m08` 全绿——台账「m01/m08/c13 del 蒸发（round2 登记）」引用已过时；c13 红单元 `CMisc.boom` 非 del 形态（raise+循环混合）。
   - AugAssign（B76+B48 残留变体）：`rv10_32` 8/8、`r8_06` 10/10、`r7_08` 8/8、`v_b76_face` 4/4 全绿——round9「本轮未抽验」注记 + 清零 9（B76/B48）合并后，行内已无红单元。
   - Global（B75）：`r10_15` 6/6 绿；残余 `v_swap_arm_returns` 产物 = try 区间错位 + global 声明随体丢失（B82-v_swap 系，round9 §3.2 已归 B82）。
   - Raise（B87 变体）：锚点 `x08::raise_leaf` 由 B126-R2 附带翻正（`FIX_R9.md` §6 已登记 5/8→6/8）；现 raise 系红单元 = B58 电池 + c13。
2. **维持 16 内 2 项已翻正（台账 stale）**：B49（`r7_08::t_host_for_else` 随文件 8/8 全绿）、B63（`rv8_02` 7/7 绿且 round9 residual 面即已绿）。建议主代理裁决是否提前闭环并从维持名单调整。
3. **部分翻正**：B42（`r7_01::t_arg_multi_mixed` 8/9→**9/9**）；B44（`r7_11::b_and_or_repeat` + `r7_12::b_nest_three_layers` 翻正；残余 `b_nest_deep_right`）。
4. **B46 尾项翻正**：`t_nest_in_condition` 6/7→**7/7**（清零 9 样本证实）；If 行残余 = B78×3 + `b_ternary_lhs_and`（round1 REVIEW 独立行 B46-b_ternary_lhs_and，归 If 行）。
5. **B122 挂死维持**：双探针（`r8v8rev_bmatch_nestnoguard` / `r8v8rev_bmatch_guards_battery::v2`）60s regen 硬杀 HANG，与 `r9v9_b122_readings.json`（>75s）同族；`status=hang` 无单元读数（判据引擎同源，verify 跳过）。
6. **零 pass→fail**：全部读数与 round9 `r9v9_*` 基线逐位持平或改善（改善 = raise_leaf、r8_x_with_ternary、t_nest_in_condition、b_and_or_repeat、b_nest_three_layers、t_arg_multi_mixed、r7_08 全文件、rv8_02、r10_04、r10_15、n9v9_stmt_sweep）。
7. **B51/B52 同单元口径差**：两编号同引 `rv7_02::chain_two_ternary/chain_three_ternary`（round1 §2.2(g) 已登记子集差）——本轮两行读数一致（2/4 红），并入终表时需统一裁决归属。
8. **B124 封闭留档 live 证实**：`r8_10::r8_x_with_ternary` 翻正（residual/oldface 双面 +1 为 9.2 登记改善）；IfExp 行 red 仅存 B123（exprtail v3）。
9. **`c13::CMisc.boom` 产物**：`if 0: raise` 整句蒸发 + `while True→while i>0`、`else: continue` 蒸发、`return None` 蒸发——多族混合宿主；行归属建议按主形态裁决（Raise 尾闩 vs 循环控制）。
10. **B80 编号索引**：`v_b73_face`/`v_b75_face` 文件名沿用 FIX 面编号（B73/B75 face），其实测红单元归 B80/B82（round9 §3.2 口径）——行内引用需防混淆。

---

- 移交结论：**20 行真实破口**（残红单元清单见 §2/§4）+ 5 行已封闭待复验；组合级清零 9 全数证实、维持 16 中 14 维持红 + 2 翻正；另册 B52/B53/B11-R2 维持红。B127/B128/Yield-F9/B44 四项移交全部完成终判。
- 主代理验收建议序：抽验 §2 任 3 行读数（如 If/BoolOp/B122）→ 复核 Σ=25 与批次映射 → 勾选 tasks.md 1.1–1.5 → 提交 push（`rr-v3r01:`）。
