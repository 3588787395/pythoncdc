# Round 9 评审 REVIEW_DRAFT（任务 9.1 分析段续 · 合并后树 e42b8509 独立评审）

- 评审对象 = HEAD `e42b8509`（v2 round8 归档 + v3 全量语料规范合并后；MERGE_RECORD = `.trae/specs/MERGE_RECORD_rr-v3r01-f557fd_to_main.md`）
- 证据 = 前任 30 份（`rounds/round9/r9v9_*`：31 探针 _m 两半、历史主题面 _m 抽验 r2/r3/r4/r5/r67/r8a/r8b/rev3/n9、站桩 probe42 c0-14 + round2face c0-45、B122 读数、premerge_check=91f8d27d worktree 对照）+ 本段补 8 项（residual c0-72 四分片、probe42 c14-42 两分片、oldface c0-59 四分片、B123 exprtail RV2 单验 `r9v9_repro_b123_rv2.json`、n9 复现电池 `r9v9_repro_n9char.json`、round1face/quotation 合并读数抢救件 `r9v9_full_round1face_merged.json`/`r9v9_quotation_merged.json`）
- 口径 = 判据唯一 `scripts/pyc_verify.py`，RV2（先 regen `pycdc -o` 再 verify single）；三态 = spec II.3；所有命令 ≤300s 分片
- 纪律 = 只审不修、零 core/ 改动、零 git commit；regen M 态 `*OK.py` 终态 `git checkout --` 还原

## §0 总判（128 形态三态统计，Σ=128，对 v6 台账差异）

**三态读数（合并后树，II.3 口径）：完备 101 / 破口 27 / 零能力 0，Σ = 128。**

| 口径 | 完备 | 破口 | 零能力 | 依据 |
|---|---|---|---|---|
| 本轮实测（merged e42b8509） | **101** | **27** | **0** | §2 矩阵（行行有证据指针） |
| v2-tip 终态对照（91f8d27d） | 103 | 25 | 0 | 27 行中 chained_comparison、for_else 两行在 v2 tip 为完备（B104/B109 于 round8 封闭，`r8v8fixB_repro_r9pre.json` 侧 B104_main 14/14、b109 9/9 实证） |
| v6 台账（wiki §5 形式层） | 128 | 0 | 0 | round1 REVIEW §1 A 核对口径；**差异 = 27 行** |

27 行降级构成（II.7 #7：禁不改台账维持「完备」，Round 10 终审统一落账纪律不变）：

1. **25 行 = v2 规范轮次已确证、台账未落账**（round3 VERIFICATION §6「BoolOp 完备→破口 128→127」、round4 REVIEW §8「B100–B113 → 128→117」均已预告落账方向；本行矩阵按实测证据重申，无新增翻案）。
2. **2 行 = 本轮合并新增翻案（非 v2 存量）**：
   - `chained_comparison`（表C）：B104 while 宿主族在合并树重开（B104_main 12/14 + 4 电池 10 红单元 + w3 三单元，共 14 失败单元；v2 tip 同面全绿）；
   - `for_else`（表C，含 while-else 口径）：B125 嵌套循环宿主 while-else 子句蒸发（2 失败单元；v2 tip 双绿）。
3. 附注：IfExp 行（表B）在本轮证据下破口加重（B123 存量 + B124 合并新增 3 单元），但该行在 v2 tip 已因 B123 为破口，不计入翻案行。

**合并净判定**：门禁面全优、语法对抗面检出 3 个合并新增破口族共 21 失败单元（B104×14 / B124×5 / B125×2），**全部位于 402 语料之外**（与 gate-42 6617/6617 不矛盾——II.5 三维度禁互替，IV.1 门禁口径不反证语法面）。站桩 7 面（面间文件有重叠，§1 逐面列示）去重后：唯一翻正单元 = trade_info_utils ×5、change_his_to_forward、email_utils/cgroup_utils/executor/strategy_universe/trading_dates_mixin/realtime_event_source 各 ×1、m03_module_ifchain、r7_01::t_arg_multi_mixed（合计 14 单元，皆 v3 支修复）；**唯一回退单元 = r8_10::r8_x_with_ternary（归 B124，在 residual 与 oldface 两面重复可见）**。合并 hunk 全部合规落地且承重（§4），无一需回退；三个新破口族均为「调和缝隙」型（两方判据共存的组合面缺口），非黑名单违规、非规则丢失。

## §1 站桩新基线（合并后树 = 9.2/9.3 回归基线）

| 面 | round8 终态（fixB/rev） | 合并后树（本段实测） | Δ | 逐位对照结论 |
|---|---|---|---|---|
| 402 全量 | 6554/6617（369/402） | **6617/6617（402/402）** | +63 单元 / +33 文件 | gate-42 八分片 + v2 基线 compare REGRESSIONS=0（MERGE_RECORD；33 文件改善先验证 join 重叠防伪零） |
| round1face | 417/423 | **423/423** | +6 | trade_info_utils ×5 + quotation ×1 经 v3 支恢复；读数存 `r9v9_full_round1face_merged.json`（前任误写 round8 证据件，本段抢救至 round9，原件待还原） |
| round2face | 239/251 | **245/251** | +6，WORSE=0 | 6 文件各 +1（email_utils/cgroup_utils/executor/strategy_universe/trading_dates_mixin/realtime_event_source）；4 失败文件 = B78/B79/B80/B82 移交面**逐位同 round8**（c15-30/c30-45 分片） |
| probe42 | 177/196 | **178/196** | +1，WORSE=0 | m03_module_ifchain 0/1→1/1；13 失败文件（c04/c06/c07/c13/m02/m06/x01-x05/x08/x10）逐位同 round8 fixB（c0-14 前任 + c14-42 本段补全 = 42/42 文件全覆盖） |
| residual | 419/446 | **419/446** | 净 0 | r7_01 +1（t_arg_multi_mixed 翻正）vs r8_10 −1（r8_x_with_ternary 翻败 → B124 第 5 单元）；其余 70 文件逐位一致（c0-72 四分片全覆盖） |
| oldface | 665/692 | **671/692** | +6，WORSE=1 | trade_info_utils +5、quotation +1、r7_01 +1；WORSE=1 = 同一 B124 单元（c0-59 四分片全覆盖） |
| quotation | 152/153 | **153/153** | +1 | change_his_to_forward（round10 起存量）经合并翻正；`r9v9_quotation_merged.json` |
| small34 | 1505/1568 | 1568/1568 | +63 | gate-42（MERGE_RECORD） |
| tests 六套件 | 277p/2f/2x | 同基线名单 | 0 新增 | gate-42 BY NAME 核验（test_B01 + test_BOUNDARY_02） |

- 31 探针攻击面（replay31A/B `_m`）：位B/C 已封闭族全绿唯 B104_main 12/14；移交族维持逐位（B98_matrix 7/15、B98_hosts 13/18、B98_resid 2/5、B78 1/4、B79 3/4、B80 2/3、B82 2/3、B112 21/24）；B83 2/2、B77 8/8、B81 4/4 绿。
- B122 读数维持：双探针（n1_nestnoguard / v2_bmatch_guard）合并树仍 >75s 硬杀挂死（`r9v9_b122_readings.json`）= 存量维持非合并扰动。
- **站桩结论**：7 面 WORSE 合计 = 1 个失败单元（B124），无面级回退；round9 基线即上表右列。

## §2 128 形态矩阵要点（表A/B/C 按族归组；Σ 逐组核算到 128）

> 行枚举权威 = `docs/refactor/syntax-coverage.json` + `tools/kb/syntax_coverage.py`（大写过滤实测 97 = 29 语句节点 + 31 表达式节点 + 8 match 模式节点 + 29 操作符叶；小写辅助节点 alias/arg/arguments/comprehension/keyword/match_case/withitem/excepthandler 不计分母）。表C 31 = covered_extra_forms 全名单。三态判据 II.3；「破口」行行有锚点+机制（§3/§5 及沿袭登记）。

### 表A 语句与结构（29 行：破口 14 / 完备 15）

| 形态组（行数） | 三态 | 破口编号 | 证据指针（合并树实测） |
|---|---|---|---|
| Module/FunctionDef/AsyncFunctionDef/ClassDef（4） | 完备 | — | m09 1/1、c12 3/3、r5_01 3/3、r5_02 9/9、x09 10/10、c10/c11/c14 全绿（宿主嵌套失败归内层形态行） |
| If（1） | **破口** | B46尾项 + B78 | v_b46_face 1/4 双树同败（v_while_cond_nest/v_if_cond_nest/n_for_body_nest）；t_nest_in_condition 沿袭（III.5 实施降级未封闭） |
| For/AsyncFor（2） | 完备 | — | neg_for3 绿、x06 7/7、async 电池绿（x02 宿主失败归 B87/B88 行） |
| While（1） | **破口** | B94 | x01::if_in_while NOP 残段假循环，双树同败（probe42 c28-42 = round8 逐位） |
| Break/Continue（2） | **破口** | B71 + B97 | v_b71_face 3/4（fin_continue）双树；x10::h_basic handler break 双树 |
| Try/TryStar（2） | Try **破口** / TryStar 完备 | B87/B73/B75；B102 已封闭 | c04 5/6、m02 2/3、m06 0/1、x04 6/7 双树存量；c4_03 13/13 + b102 电池 8/8+4/4+10/10 绿 |
| With/AsyncWith（2） | With **破口** / AsyncWith 完备 | B93 | x05::with_in_match 幻影镜像 6/7 双树（round8 fixB 逐位）；r6_05/06/12 全绿 |
| Match（1） | **破口** | B74 + B122 | B122 双探针挂死维持（r9v9_b122_readings）；B74 沿袭（III.5 未封闭） |
| Raise/Assert（2） | **双破口** | B87 变体；B56 + B126 | x08::raise_leaf 双树；x08::assert_leaf（B56）+ n9::assert_deep（B126，双树新发现） |
| Return/Pass/Expr（3） | Return **破口** / Pass、Expr 完备 | B88 | x08::return_leaf、c13 2/3、c02 沿袭双树；pass_arms/expr_stmt_deep 绿 |
| Delete/Assign/AnnAssign（3） | Delete **破口** / Assign、AnnAssign 完备 | B84 | m01/m08/c13 del 蒸发（round2 登记，III.5 域）；r5_03 11/11、r8_05 11/11 绿 |
| Import/ImportFrom（2） | Import **破口** / ImportFrom 完备 | B73；B100 已封闭 | try 四段 import 宿主泄漏（III.5 未封闭）；c4_14 5/5、c4_15 7/7 绿 |
| Global/Nonlocal（2） | Global **破口** / Nonlocal 完备 | B75；B72 已封闭 | try 宿主 global 声明错位（III.5 未封闭）；r10_13/14、rv10_31 13/13 绿 |
| ExceptHandler（1） | 完备 | —（B97 归 Break 行） | handler 归并/except* 电池绿 |

### 表B 表达式（31 行 + 8 match 模式 + 29 操作符叶：破口 6 / 完备 62）

| 形态组（行数） | 三态 | 破口编号 | 证据指针 |
|---|---|---|---|
| BoolOp（1） | **破口** | B98（R1 部分） | matrix 7/15、hosts 13/18、resid 2/5——双树逐位同败（B98-R2/R3 移交维持） |
| And/Or 等 29 操作符叶（29） | 完备 | — | e06 14/14（32 叶口径注记：分母枚举 29 叶全绿） |
| IfExp（1） | **破口** | B123 + B124 | exprtail v3 双树同败（B123 存量）；f_call_ternary_arg / r8_x_with_ternary 合并新增（B124） |
| Compare（1） | 完备 | —（链式归表C 行） | 基本双元比较全绿（e05/e10 绿单元、bmatch 电池 2/2×4） |
| BinOp/UnaryOp/Constant/Name/Attribute/Subscript/Starred/List/Tuple/Dict/Set（11） | 完备 | — | e06 14/14、e07 15/16（唯一败归 Slice 行）、c4_13 13/13 |
| Slice/Index（2） | Slice **破口** / Index 完备 | B127（round3 F4 存量补编号） | e07::f_slice_expr_bounds 双树同败，6 轮未编号，本轮落 B127 |
| Lambda（1） | 完备 | — | e08 30/30、r5_15 27/27 |
| ListComp/SetComp/DictComp/GeneratorExp（4） | ListComp **破口** / 其余完备 | B112② | c4_20 21/24 双树（e07_async_closure.outer.inner[+listcomp]）；B113 封闭 c4_18 30/30、comp2 9/9 |
| Call（1） | 完备 | —（e10 唯一败归 IfExp 行） | e10 31/32；keyword_args/star_args 表C 电池绿 |
| FormattedValue/JoinedStr（2） | 完备 | — | e11 13/13、c4_17 12/12、r5_10 13/13 |
| Await/Yield/YieldFrom（3） | Await、Yield **破口** / YieldFrom 完备 | B112① + B128；round3 F9 存量 | e12d::f_await_cond_pos 双树同败（B128 补编号）；yield 实参/boolop 产物非法（round3 REVIEW §3.4 F9，e12b/c/f 探针 compile_error 空转，9.2 重建）；e12e 7/7、r6_15 8/8 |
| NamedExpr（1） | 完备 | —（B105 已封闭） | c4_10 13/13 + walrus 电池 5/5+3/3 |
| Load/Store/Del（3） | 完备 | — | 语境叶随宿主全绿 |

### 表C 31 扩展形态（破口 7 / 完备 24）

| 形态组（行数） | 三态 | 破口编号 | 证据指针 |
|---|---|---|---|
| elif_chain/multi_context_with/multi_target_assign/walrus/keyword_args/star_args/relative_import/star_import/fstring_conversion/nested_comprehension/decorator_with_args/try_finally_only/case_guard/capture/class_keyword/mapping/or/sequence/value_pattern/async_def/async_for/async_with/yield_from（24） | 完备 | — | c4_01 14/14、r6_09 8/8、b107 电池 6/6+4/4+6/6、b105 电池全绿、c4_11/r5_06 绿、b106 电池 18/18+7/7、c4_14 5/5、c4_15 7/7、e11/c4_17/r5_10 绿、c4_18 30/30、b111 28/28+22/22、c4_06 14/14、b103_guard 8/8、c4_04 13/13 全模式绿、e09b/c4_20 async 主体绿、e12e 7/7 |
| chained_comparison（1） | **破口（合并翻案）** | B104（重开）+ B124 | B104_main 12/14（e08_while+CCMP.m）+ chain4 4/6 + chain5 2/5 + opdeep 2/4 + exprtail 2/5 + whilehost w3 三单元 = 14 合并新增；v2 tip 同面全绿（r9v9_premerge_check） |
| for_else（含 while-else，1） | **破口（合并翻案）** | B125 | b109::nested_loop_else（while 的 else 臂整臂蒸发）+ r5_13::fe_while_deep（内层 while-else 蒸发 + 幻影尾 return）= 2 合并新增；v2 tip 双绿（premerge 9/9、11/11） |
| augmented_assign（1） | **破口** | B76 + B48 残留变体 | III.5 未封闭沿袭（本轮未抽验，9.2 复验；注：r7_08 宿主单元现绿 8/8） |
| await_expr（1） | **破口** | B112① + B128 | 同表B Await 行 |
| global_nonlocal（1） | **破口** | B75 | 同表A Global 行 |
| match_statement（1） | **破口** | B74 + B122 | 同表A Match 行 |
| slice（1） | **破口** | B127 | 同表B Slice 行 |

**Σ 核算**：表A 29（14 破 + 15 完）+ 表B 31（6 破 + 25 完）+ match 模式 8（0 破 + 8 完）+ 操作符叶 29（0 破 + 29 完）+ 表C 31（7 破 + 24 完）= **128 = 27 破 + 101 完 + 0 零能力** ✓（与 §0 一致；零能力 = 0 由 syntax-coverage 分子 128/128 + gate-42 全量隐式三路径背书）。

## §3 开放族详查（合并树现读数 + 双树定性）

### 3.1 合并新增三族（本轮主发现，9.2 首选对象）

**B104 while 宿主链式比较族 —— 合并重开，14 失败单元**（MERGE_RECORD 已自declared 为合并唯一 open residual；本轮实测边界比合并记录更宽）：

| 探针::单元 | v2 tip | 合并树 | 形态 |
|---|---|---|---|
| B104_main::e08_while / CCMP.m | 14/14 绿 | 12/14 败 | `while 0<x<n<100:` 3 元链 + 类方法宿主链 |
| chain4::v2/v4 | 6/6 绿 | 4/6 败 | `while 0<x<10 and flag:` / `while 0<x<10<x*2<100:` |
| chain5::v1/v2/v4 | 5/5 绿 | 2/5 败 | 5 元链+and 尾 / H5 原设计 3 元+and 比较尾 / 4 元+and 尾双宿主 |
| opdeep::v1/v2 | 4/4 绿 | 2/4 败 | and 尾=海象表达式值段 / 纯比较 and 尾同序重演 |
| exprtail::v1/v2 | 4/5（仅 v3 存量败） | 2/5 败 | and 尾=f-string / and 尾=字典推导式（v1/v2 新败；v3=B123 存量） |
| n9_whilehost::w3_plain/w3_deep/w3_and | 8/9（仅 w3_nostore 败） | 5/9 败 | e08 同形 3 元链 / for 宿主深度 2 3 元链 / chain4-v2 同形 |

- 机制（MERGE_RECORD §「v2's own round-8 variant battery」已述）：while 条件链的回边重检副本未按纯 recheck 抑制，被发射为体语句（`if 0<x<10: ... elif 10<True and x*2<True:`）。v3 tip 同面读 2/6（chain4）⇒ 合并未删规则、是 [B104-R2a] 追加路与 [R21-65]/[R21-66] 重构的组合缝隙；两调和门（[B104-R3]/[B99 收窄]）四臂同 sha 实证对本族惰性（MERGE_RECORD attrib_r148）。
- **w3_nostore（无 STORE 体）双树同败** ⇒ v2 tip 的 B104 族存量缝隙（round8 电池未含此形），登记为 B104-R4 边界证据，非合并新增。
- 违反条款：C3（回边重检抑制守卫在 while 宿主链式条件下未封闭）+ 原则 4（while 条件入口引用语义退化为体语句）。

**B124 值位链式比较/IfExp 嵌套宿主重建族 —— 合并新增，5 失败单元**（详见 §5）：
- e05::f_compare_chain6 / f_compare_binop_inside / f_compare_subscript_inside：`for→if→while` 宿主 return 位 6 元链/含 BinOp/含 Subscript 链，产物签名 = 宿主 if 融合为 `if i and i:` + while 体整体蒸发 + `pass`；
- e10::f_call_ternary_arg：同宿主 return 位调用实参 IfExp，产物 `if i and i:` + 实参幸存但 return None 常量错；
- r8_10::r8_x_with_ternary（residual/oldface 面双见）：with-item 内 `open(x if t else y)` → 幻影 `context()` 占位符。
- v2 tip 五单元全绿（premerge_check + r8fixB 电池基线 9/12）⇒ 全部合并新增。锚点方向：H3 臂尾提升（:23918-24049 [R21-36 r62a]/[R21-15 HOIST]）×[B99 收窄]（:25433）×[B104-R3]（:19878）4-arm 待归属（§6）。

**B125 嵌套循环宿主 while-else 蒸发族 —— 合并新增，2 失败单元**（详见 §5）：
- b109::nested_loop_else：`for→while(+else return None)→if/break` 产物中 while 的 else 臂整臂丢失（for-else 幸存）；
- r5_13::fe_while_deep：内层 `while j<m(+else i=n)` 的 else 臂丢失 + 函数尾幻影 `return -1`（原函数无 return）。
- v2 tip 双绿（premerge 9/9、11/11）⇒ 合并新增。锚点方向：H4 else 块认领组合（[B117]+[R21-86] 串联守卫）/ [R21-92 D3] implicit-tail loop else。

### 3.2 移交族维持读数（round8 移交名单，合并树逐位不恶化）

| 族 | 合并树读数 | 双树定性 | 备注 |
|---|---|---|---|
| B78（B46 族外推） | v_b46_face 1/4 | 双树同败存量 | hop 块判别元/折叠常量合成；判据事实在案（round8 移交） |
| B79（B71 fin_continue） | v_b71_face 3/4 | 双树同败存量 | 嵌套 try 分区混装 |
| B80 | v_b73_face 2/3 | 双树同败存量 | FIX_A §5 判据在案 |
| B82-v_swap | v_b75_face 2/3 | 双树同败存量 | 异常表区间外布局→识别层；B82 主体 2/3 部分封闭维持 |
| B98-R2/R3 | matrix 7/15 / hosts 13/18 / resid 2/5 | 双树逐位同败 | 分组 boolop 保真；R1 部分封闭维持 |
| B44 | **本轮未抽验** | 沿袭登记维持 | ≥3 层双入口归纳；round8 移交，round9 证据集无对应探针——9.2 需重建（II.7 #13 不得以未测当维持，此处如实标注证据缺口） |
| B112①② | c4_20 21/24 | 双树同败存量 | e05_async_compound.go + e07_async_closure.outer.inner[+listcomp]；判据方向 FIX_C §6.1 |
| B122 | 双探针 >75s 硬杀挂死 | 双树同挂存量 | 字面量 case 臂嵌套 match；r9v9_b122_readings.json |
| B123 | exprtail v3 败（2/5 中 1） | 双树同败存量 | IfExp 尾操作数钻石块集；合并树 v1/v2 新败归 B104 族（and 尾吸收缝隙），B123 本体维持 |

### 3.3 双树同败新发现/补编号（非合并新增，9.2 次优先）

- **B126**（新发现）：n9_stmt_sweep::assert_deep——`for×while` 宿主 `assert 0<a<b, a` 产物 = 幻影 break + 死 store + 幻影 for-else；双树同败 ⇒ 存量非合并扰动；AssertRegion 链归约吞并 while 回边载体（§5）。
- **B127**（补编号）：e07::f_slice_expr_bounds——切片边界表达式，round3 REVIEW §3.4 F4 已实测「破」但 6 轮未编号；双树同败。
- **B128**（补编号）：e12d::f_await_cond_pos——await 条件位，round3 F9 同上未编号；与 B112①（await 链消费门）同域不同形。
- **Yield 行注记**：round3 F9 的 yield 实参/boolop 产物非法证据在案，但 e12b/c/f 探针 compile_error 空转（探针退化，round2 §4.3 口径同类）⇒ 破口判定维持、当前无可用读数，9.2 重建探针复验（不因探针缺失改判完备——II.7 #2/#13）。

## §4 合并 hunk 审计（[B104-R3]/[B99 收窄]/H1-H4，I.4 逐 hunk）

| hunk | 锚点（本段 grep 实测） | I.4 判据核验 | 承重证据 | 审计结论 |
|---|---|---|---|---|
| H1 while 条件构建 union | region_ast_generator.py:8505（[B104-R2a] 混合条件 compose）、:8546-:8634（[R21-66] SEG identity/latch-copy） | 两定义独立共存，判据 = opcode 序/块成员（白名单） | broker 128/128 + nb 电池（MERGE_RECORD） | **合规**；B104 族缝隙非本 hunk 违规而是覆盖面缺口（§3.1） |
| H2 回边重检抑制双路 | :8640-:8699：路 B = [R21-66] COPY/COMPARE+IS_OP/CONTAINS_OP 尾 + latch copy + 末 STORE 边界；路 A = [B104-R2a] 追加 `elif`，`_cc_mixed_tails/leads` 前置 + `_b104r2_cond_eval_seq` 操作码序等值 + v2 多段 STORE 抽取器 | 全部块内指令 opname/序/段边界（白名单）；不回写 `_is_recheck`，两路原判定形态各自保留 | MERGE_RECORD：三次失败组合实证后终版 broker 128/128 | **合规**；14 B104 单元 = 路 A 前置（and 尾/无 store/深嵌形）未覆盖——扩展点即在 `_cc_mixed_*` 判据面 |
| H3 if 臂归约 | :23918-:24049（[R21-86 RENDER-SCOPED CLAIM] → [R21-36 r62a] continue 臂提升 → [R21-15 HOIST-EMIT] :3578） | 守卫先行、分支调用恰一次（v2 重复调用为同一调用，弃之无损） | quote_handler 79/79（[B117] 撤除即 79→77，MERGE_RECORD 实测） | **合规**；B124 主嫌疑面（4-arm 待归属，§6） |
| H4 嵌套块认领 union | :536（[R21-86] released else 块）+ [B117] 挂起循环回边块双 continue 串联 | 区域成员/后继集合（白名单） | 同上 | **合规**；B125 主嫌疑面 |
| [B104-R3] | region_analyzer.py:19878-:19935：released 差集（for/async-for 体块−结构边界成员 + with_blocks）+ 块末 `opname in SHORT_CIRCUIT_JUMP_OPS` 跳过门 | 区域成员关系 + 块末 opcode 族（白名单；[Round4-04] 同一判据词汇）；C1/C2/C3 注释齐全 | 四臂真值表 matcher 17/17 + nb_for/nb_with 2/2（MERGE_RECORD ana_ab3_r137） | **合规且承重**；条件位链头（POP_JUMP_IF_*）不命中 ⇒ 非破口成因的充分性已由 census 实证 |
| [B99 收窄] | :25433-:25472：值上下文 conjunct（`not getattr(region,'is_condition_context',True)` 本区域自声明事实）+ `_is_chained_compare_header`（块内指令对）复用 | 两条均同层结构事实；口径与 [B99 残]/[Phase 7] 一致 | cf_b99_r143 反事实：删守卫 matcher 17/17 但 nb_b99 3/4 ⇒ 只能收窄不能删 | **合规且承重** |

- G3：合并新增 def 全量扫描（git diff 91f8d27d..HEAD `+def`），零禁前缀；`_merge_block_is_then_exclusive`（:23001）为双树 context 行 = v2 存量非合并引入。
- G4：合并 hunk 无 start_offset 阈值/深度上限/命名白名单（H2/[B104-R3]/[B99] 三现场逐行核验）；无新增跨层反查。
- BOM/插桩：两核心文件 BOM 单头口径随 round8 VERIFICATION §5；合并插桩标记零残留（R21/B104 标记皆为判据注释非调试插桩）。
- **总判**：六 hunk 全部 I.4 合规落地、各有承重实证，无一回退项；合并的三破口族均为组合缝隙（覆盖面缺口），修复方向 = 在既有判据面上扩门（§6），禁止回退任何 hunk。

## §5 新 Bn 登记（B124 起；wiki §8.3 状态机：已定位）

| 编号 | 形态（锚点+机制） | 失败单元（证据） | 双树定性 | 违反条款 |
|---|---|---|---|---|
| **B124** | 值位链式比较/IfExp 在嵌套宿主下重建破口。锚点方向：region_ast_generator.py:23918-24049（H3 臂尾提升区）× region_analyzer.py:25433（[B99 收窄]）× :19878（[B104-R3]）——4-arm 待归属。机制：宿主 if 与内层 while 条件融合（产物签名 `if i and i:`）致 while 体蒸发；with-item 形为幻影 `context()` 占位 | e05::f_compare_chain6/f_compare_binop_inside/f_compare_subscript_inside、e10::f_call_ternary_arg、r8_10::r8_x_with_ternary（5 单元；产物实证 `r9v9_repro_n9char.json` + e05/e10/r8_10 OK.py 现读） | v2 tip 全绿 ⇒ **合并新增** | C2（嵌套宿主值位重建 ≠ 浅层）+ 原则 3（嵌套即抽象节点，while 被融合吞并） |
| **B125** | 嵌套循环宿主 while-else 子句蒸发。锚点方向：region_ast_generator.py:536（[R21-86] released else 块）+ [B117] 串联守卫 + [R21-92 D3] implicit-tail。机制：while 的 else 臂块被释放/未认领 ⇒ 整臂丢失；深层伴随幻影尾 return | b109::nested_loop_else、r5_13::fe_while_deep（2 单元；产物实证：else 臂缺失 + 幻影 `return -1`） | v2 tip 双绿（premerge 9/9、11/11）⇒ **合并新增** | C3（else 臂发射守卫未认领）+ 原则 2/3 |
| **B126** | assert 链条件 + 消息操作数在 for×while 宿主下吞并 while 回边载体。锚点方向：region_analyzer.py:14799 族 `_identify_assert_regions`（chained_compare_ops + `_build_assert_chained_compare` 归约）。机制：assert 链区域吞并体尾 store（回边载体）⇒ 回边丢失、幻影 break + 幻影 for-else | n9_stmt_sweep::assert_deep（产物：`assert 0<a<b,a; break; a+=1` 死码 + `else: return a` 幻影） | 双树同败 ⇒ **存量新发现**（round9 探针首测） | C1（归约读了回边载体块）+ C3 |
| **B127** | 切片边界表达式重建破口（补编号：round3 REVIEW §3.4 F4 实测「破」后 6 轮未编号） | e07::f_slice_expr_bounds | 双树同败 ⇒ **存量补编号** | C2 |
| **B128** | await 条件位重建破口（补编号：round3 §3.4 F9 同源未编号；与 B112① 消费门不同形） | e12d::f_await_cond_pos | 双树同败 ⇒ **存量补编号** | C2 |
| （并入既有族） | w3_nostore → **B104 族 R4 边界证据**（无 STORE 体形，v2 tip 亦败 ⇒ 族存量缝隙非合并新增）；r8_x_with_ternary 归 B124；exprtail v1/v2 归 B104 族 and 尾吸收缝隙、v3 维持 B123 | n9_b104_whilehost::w3_nostore 等 | 双树同败 / 合并新增如注 | 如注 |

- B122 维持、B123 维持（3.2/3.1）；无 Bn 从「已落地/已复审」回退。
- 台账落账路径：25 行 v2 轮次确证 + 2 行合并翻案 + B124-B128 ⇒ 按纪律随 Round 10 终审 wiki §8.2 六步统一落账（本报告提供全部锚点；II.7 #7）。

## §6 9.2 修复批派发建议

**并行派发判据（spec：破口族不相交 ∧ 涉改文件不相交）先验**：B104 与 B125 主嫌疑均在 region_ast_generator.py（H2 区 vs H4/else 区）⇒ 不相交但涉改文件相同 ⇒ **串行**；B124 归属未定 ⇒ 先做只读 4-arm 归属再定桶。建议编排：

1. **位0（只读归属，9.2 首动作，≤300s/臂）**：B124 四臂 A/B——①关 [B104-R3] ②关 [B99 收窄] ③关 H3 臂尾提升 ④全开对照，重生成 e05/e10/r8_10 三探针定单元归属（方法 = MERGE_RECORD ana_ab3_r137 同款，恢复字节再哈希）。产出决定 B124 入 generator 桶或 analyzer 桶。
2. **位A（region_ast_generator.py，首选冲刺）**：B104 while 条件位族（14 单元，含 MERGE_RECORD 自declared residual）。判据方向 = H2 路 A 的 `_cc_mixed_tails/leads` 前置面扩至：无 STORE 体形（w3_nostore 同判据族）、纯比较 and 尾（opdeep v2 形）、f-string/字典推导 and 尾（exprtail v1/v2 形——尾操作数吸收沿 B123 已给「块集判据」方向并轨）；全程 I.4 白名单（块末 opcode/操作码序/STORE 边界/区域成员），门禁 = 本表 14 单元全转 MATCH ∧ matcher 17/17 ∧ broker 128/128 ∧ nb 电池 2/2+2/2+4/4 不回退。
3. **位B（串行于位A 后，同文件）**：B125 while-else 嵌套宿主（2 单元）。判据方向 = [R21-86]/[R21-92 D3] else 块认领对嵌套 while 宿主补认领（嵌套即抽象节点，else 臂归 WhileRegion 不因外层循环释放）；门禁 = b109 9/9 ∧ r5_13 11/11 ∧ c4_02 14/14 ∧ r9_01/09/10 全绿不回退。
4. **位C（region_analyzer.py，可与位A 并行——文件不相交）**：B126 assert 链归约吞回边载体（1 单元）——AssertRegion 归约以循环回边块为 L(A) 外弃收（[B17] try 体边界同构白名单）；门禁 = n9_stmt_sweep 6/6 ∧ r8_07 11/11 不回退。若位0 把 B124 判归 analyzer（[B104-R3]/[B99]），B124 并入本位。
5. **位D（低优先，存量补编号收尾）**：B127 切片边界 + B128 await 条件位 + Yield 行探针重建复验 + B44 移交探针重建（证据缺口补齐）。
6. **约束**：全程禁止回退六 hunk（§4 承重实证）；站桩门禁 = §1 新基线七面 WORSE=0（唯 B124 的 r8_x_with_ternary 单元按位翻正计入改善）；每批 docstring 六项 + C1/C2/C3 声明（I.7）+「代码已落地」（I.6）。
7. **优先级一句话**：位0 → 位A（B104，14 单元最大族）→ 位B（B125）∥ 位C（B126，文件不相交可并行）→ 位D。

## §7 II.7 十三条误解自查（本报告宣告「破口」与矩阵结论前逐条对准）

| # | 误解 | 是否犯 | 事实依据 |
|---|---|---|---|
| 1 | 循环论证分母 | 否 | 128 分母 = ast 权威（syntax_coverage.py 大写过滤实测 97+31），未取 RegionType/探针面 |
| 2 | 有过就算 | 否 | 21 合并新增单元逐一登记 Bn；r8_10 面单元回退未被 r7_01 改善掩蔽（§0 明示 WORSE=1） |
| 3 | 语料证据口径 | 否 | 破口判定基于构造探针 + 产物字节形态，非语料覆盖面；B44/B76 未测即如实标「未抽验」不判完备 |
| 4 | 无限分母 | 否 | Σ 逐组核算到 128（§2 末行），无随嵌套膨胀项 |
| 5 | 节点词汇当完备 | 否 | 形态行判定依据三路径 + 不变式证据，非词汇存在性 |
| 6 | 浅层测试当无感证明 | 否 | B124/B125 均深层宿主形态；w3_deep 深度 2 入证；未以浅层绿宣告族完备 |
| 7 | 门禁读数当完备性 | 否 | gate-42 6617/6617 与 27 破口行并报（IV.1/II.5 三维度禁互替，§0 明示） |
| 8 | 顶层构造粗清单 | 否 | §2 矩阵逐行到形态族 + Σ 核算；§3 逐族到单元/产物签名 |
| 9 | 识别率当完备性 | 否 | 完备判定 = 三路径 ∧ 无破口证据（II.3），非成功率读数 |
| 10 | 维度互替 | 否 | 门禁面（+19 净）与语法面（3 新族 21 单元）分列不互抵 |
| 11 | 错误检测标准 | 否 | 判据唯一 pyc_verify（3.11 标记口径随树），未引入 3.12 标记 |
| 12 | 改工具不改方法 | 否 | 本段零 core/ 改动；建议全部落在归约算法判据面（§6） |
| 13 | 语料上限当能力上限 | 否 | 21 单元全部来自构造探针（402 语料之外）；Yield 行不因探针空转改判完备（§3.3） |

## 附：证据清单与本段遗留处置

- 本段新增证据：`r9v9_full_residual_c0-18/c18-36/c36-54/c54-72.json`（419/446 逐位）、`r9v9_regress_probe42_c14-28/c28-42.json`（178/196 补全）、`r9v9_full_oldface_c0-15/c15-30/c30-45/c45-59.json`（671/692 全覆盖）、`r9v9_repro_b123_rv2.json`（B123 单验 2/5）、`r9v9_repro_n9char.json`（B124/B125/B126 复现+产物定性）、`r9v9_full_round1face_merged.json`/`r9v9_quotation_merged.json`（合并读数抢救件，来源见下）。
- **前任证据卫生事故（如实登记）**：前任在本树重跑 r8v8fixB 站桩/复现驱动，覆写 round8 两份已提交证据（提交态经 `git show HEAD:` 核实 = 417/423、152/153，与 VERIFICATION §6 终态一致；覆写后 = 合并树读数 423/423、153/153）并在 round8/ 落两个未跟踪 r9pre/reprodump 件。本段处置：合并读数已抢救至 round9（上列）；round8 两文件随本段终态 `git checkout --` 还原为提交态（禁覆盖 round8 证据纪律恢复）；未跟踪两件为前任新增证据（非覆写），留原位待 9.2 归档决策。
- 终态工作树处置：全部 regen M 态 `*OK.py`（54 件）+ 上述 round8 两 JSON `git checkout --` 还原；round9/ 证据与 REVIEW_DRAFT.md 为本段唯一新增。
