# Round 3 评审报告（Task 3.1）—— 表B 表达式形态对抗

> 独立对抗评审（只读审计 + 探针构建 + 报告）。HEAD = `434e732e`；工作树除 RV2 regen 产物与新增证据外无源码改动。
> 口径：一切读数以 HEAD 代码 regen（RV2）后 verify；结论逐条引用条款编号（I.x / C1/C2/C3 / II.3 / 13 误解编号）。

## §0 终判预备结论与两态口径

**两态口径（II.3）**：本轮对表B 表达式形态逐一给出「完备 / 破口 / 零能力」三态。判定证据 = 深层探针 ≥3 层嵌套 + 宿主矩阵交叉，负对照要求（若宣称「完备」）为「深层 MATCH ∧ 浅层等价物 MATCH」。

**终判预备**：
1. **表B BoolOp 形态确证由「完备」降为「破口」**——新登记 **B98**（or-in-and 分组保真破口，浅层/模块根/类体即触发）与 **B99**（`for` 宿主 `return <BoolOp>` 表达式蒸发，`while` 宿主不受影响）。二者机理不同、宿主不同，均非既有 B1（B1b 封闭守卫）机理。
2. **B1 台账口径不足**——B1b 五臂封闭守卫（`region_analyzer.py:17902/19299/27978/27988/28245`，`_sb_has_body` 谓词）经外推+收缩双向攻击，仍有 5 单元失败（e03），且 `for`/`while` 宿主 + 深右嵌套面未覆盖。
3. **表B 其余形态大面积维持完备**（F3 操作符叶子 14/14、F6 同步推导式 30/30、F8 f-string 13/13、F5 lambda 28/30、F7 call 31/32、F9 yield-from 7/7），但 **F2 三元 / F9 yield 作实参 / F10 海象** 三族在深宿主显著破口。
4. **站桩回归全过**（§2）——6 面零回退；部分面较基线**改善**。

---

## §1 合规审计表（HEAD=434e732e，只统计新增/清除；审计基准 = 承接旧规范终态 `f831eeae`）

审计方法：`git diff f831eeae..HEAD -- core/`（2572 insertions / 98 deletions，涉改 7 文件）+ grep 全树。

| 红线 | 扫描方法 | 命中 | 判定 |
|---|---|---|---|
| 在途变更 | `git status --porcelain`（全树） | core/ 零改动；唯一 tracked 修改 = `test_repros/round7/r7_11_boolop_mixedOK.py`（**RV2 regen 截断覆盖产物**，非手改、非源码） | **PASS**（源码零在途） |
| I.4-① 文件/函数名白名单 | 新增行 grep `co_name\|func_name\|filename\|WHITELIST\|_name in (` | 1 处：`ast_converter.py:33 _COMPREHENSION_CODE_NAMES` + `:1317`（B96），判据 = `co_name ∈ {<listcomp>,<dictcomp>,<setcomp>,<genexpr>}`——**编译器合成名，Python 语法禁止用户取得尖括号标识符**（docstring :28-32 明示「非用户标识符白名单」，I.4 白名单「code object 元数据」判据） | 新增 0（合法豁免） PASS |
| I.4-② start_offset 魔数阈值 | 新增行 grep `start_offset` | 32 处，**全部**为 `block.start_offset` 作序键 / 集合成员 / 身份键（`sorted(key=start_offset)`、`{b.start_offset for b in ...}`、`in _fin_off`）；**零** `start_offset >/</== 常数` | 新增 0 PASS |
| I.4-③ 跨层 `entry in blocks` 反查 | 新增行 grep `in blocks` | 0 | 新增 0 PASS |
| I.4-④ self 新增跨方法状态 | 新增行 grep `^\+\s*self\.\w+\s*=` | 3 处：`_ChainAwareStoreDelegate.__init__`（`region_ast_generator.py:71-74`）的 `self._gen/_block/_chain_consumed`——**文档声明为委托实例闭包局部状态**（docstring :60-68 明示「每次认领新建，非 self 跨方法状态，I.4 黑名单零命中」，B85）；无主生成器类跨方法可变状态新增 | 新增 0 PASS |
| I.4-⑤ 少发射/硬编码深度上限 | 新增行 grep `depth\|MAX_DEPTH\|max_depth [<>]=? \d+` | 0 | 新增 0 PASS |
| I.5 禁止前缀方法（新增） | 新增行 grep `^\+\s*def\s+(_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)` | 0（全树存量：`_fix_`6 / `_merge_`529 / `_patch_`4 / `_fallback_`6 / `_hack_`0 / `_workaround_`0 / `_temp_`2，**均为历史局部变量/方法名**，本轮零新增） | 新增 0 PASS |
| BOM 单头（IV.2） | 字节级首 3 字节 + 全文 BOM 计数 | `region_analyzer.py` = `efbbbf`/计数 1；`region_ast_generator.py` = `efbbbf`/计数 1；其余 5 涉改文件无 BOM | PASS |
| 插桩残留 | 新增行 grep `print(\|pdb\|breakpoint(\|# TODO\|# FIXME\|# DEBUG\|# XXX` | 0 | 新增 0 PASS |
| 命令时限 | 全部命令 ≤300s（重放分片 ≤36 文件/片） | — | PASS |

**审计结论：I.4 五项 + I.5 七前缀 + BOM + 插桩 + 在途变更全 PASS，新增违规 0。** 唯一观察项：RV2 regen 会改写 tracked 的 `*OK.py`（本轮 1 个：`r7_11_boolop_mixedOK.py`，因该文件读数本身由 6/7 改善为 7/7），属方法学规定动作，非人工改动。

---

## §2 站桩回归读数表（RV2 方法学：先 HEAD regen 再 verify）

对照脚本 `r3v2_compare_regress.py` → `r3v2_station_regress_compare.json`；全量失败单元读数 `r3v2_full_*.json`。

| 面 | 文件 | 基线读数 | 本轮读数 | same/improved/**WORSE** | 判定 |
|---|---|---|---|---|---|
| v2 round2 45 文件面 | 45 | 234/251 | 234/251 | 45/0/**0** | 逐位持平 ✓ |
| v2 round2 42 探针面 | 42 | 154/189 | **172/196** | 32/10/**0** | 无回退，10 文件改善 ✓ |
| v2 round1 哨兵面 | 24 | 417/423 | 417/423 | 24/0/**0** | 逐位持平（含 quotation 152/153）✓ |
| v1 残余面（round1 r1_residual） | 72 | 404/446 | **416/446** | 63/9/**0** | 无回退，9 文件改善 ✓ |
| 旧规范 round6–10 面 | 59 | 658/692 | **663/692** | 56/3/**0** | 无回退，3 文件改善 ✓ |
| quotation.pyc 单验 | 1 | 152/153（唯一失败 `change_his_to_forward`） | 152/153，失败单元逐一相同 | — | 持平 ✓ |

**改善明细**（全部为失败单元减少，`extra=0`，无新增失败）：
- probe42：c01/c06/c11/c13/m01/m07/m08/m12/x04/x09（+18 单元）
- 残余面：r10_04/r10_06/r10_15/r10_21/rv10_32/r7_07/r7_08/r7_11/rv8_01（+12 单元；r7_08 4/8→7/8 减 3 失败单元）
- 旧规范面：r7_07/r7_08/r7_11（+5 单元）

**站桩总判：6 面零回退（WORSE=0）、零缺失文件、失败单元逐一相同或无新增失败；5 面较基线改善。** PASS。

> 注：`round2face`/`probe42` 基线文件自身仅存 tail 读数（失败单元名截断），故对这两面仅做「状态 + units 读数」逐位对照；`round1face`/`residual`/`oldface` 基线含完整 failures，采用全量 stdout 捕获驱动 `r3v2_verify_full.py` 做**逐单元**集合比对（`miss`/`extra` 均 0）。

---

## §3 完备形态攻击结果表

探针生成：`test_repros/round3/gen_probes.py`（程序化批量，28 文件；E01–E13 攻击 + NE01–NE10 负对照，新增探针一律 `e*`/`ne*` 前缀，零覆盖既有 133 文件）。
读数：`r3v2_probe_results.json`（TOTAL **241/305 = 79.0%**，compile_error 3）、`r3v2_rv3_repro.json`。

### 3.1 ★F1 BoolOp 专攻（B98 第一主题；B1 台账重点复核）

| 探针/单元 | 形态（宿主） | 读数 | 判定 | 结论 |
|---|---|---|---|---|
| 最小复现 `return (a or b) and c`（D:\Temp\r3min\b98.py b1） | 函数根 return | 产物 `return a or b or c` | ✗ | **B98**（or-in-and 分组丢失） |
| 最小复现 `x=(a or b) and c` | 赋值位 | `x = a or b or c` | ✗ | **B98** |
| e02 `<module>` M1 `_P or _Q or _R` | **模块根**值位 | `M1 = _P or _Q or _R`（源 `(_P or _Q) and _R`） | ✗ | **B98** 宿主外推至模块根 |
| e02 `CB98` C1 | **类体**值位 | `C1 = _P or _Q or _R`（源 `(_P or _Q) and _R`） | ✗ | **B98** 宿主外推至类体 |
| e01 f_or_in_and_deep / f_or_in_and_pair_deep | 函数深宿主 + 三元交叉 | ✗ | ✗ | **B98** |
| e01 f_b98_ternary_cross / f_b98_compare_cross / f_b98_walrus_cross | 三元/比较/海象交叉 | ✗ | ✗ | **B98**（与 F2/F3/F10 交叉） |
| e01 f_b98_or_tail_and_group / f_b98_and_tail_or_group | or 尾+and 组 / and 尾+or 组 | ✗ | ✗ | **B98** |
| 最小复现 `a and (b or c)`（b98.py b4） | 函数根 | `return a and b`（or 子组蒸发） | ✗ | **B98**（对称变体：子组整体消失） |
| e02 `CB98.m_handler` / `f_try_body_host` / `f_match_arm_host` / `f_with_body_host` | for/try/match/with 宿主 | `return None` / `if …: pass` | ✗ | **B99**（for 宿主 return-BoolOp 蒸发） |
| e02 `f_comp_cond_host.<listcomp>` / `f_genexp_cond_host.<genexpr>` / `f_dictcomp_value_host.<dictcomp>` / `f_nested_func_host.inner` | 推导式条件/嵌套闭包宿主 | ✗ | ✗ | **B98/B99 交叉**（内层 code object 亦破） |
| 最小复现 `for i: if i: return a or b or c`（b99.py for_host_plain） | for 宿主 | `return None`（**平坦 or 链也蒸发**） | ✗ | **B99**（与分组无关，纯宿主机理） |
| 最小复现 `for i: return a or b or c`（b99.py for_noif） | for 宿主 | `return 0`（**return 语句整体消失**） | ✗ | **B99** |
| 对照 `while n<3: if n: return a or b or c`（b99.py w_host） | while 宿主 | MATCH | ✓ | B99 **仅 for 宿主** |
| 对照 `return a or b or c` / `if flag: return a or b or c`（b99.py top/if_top） | 函数根/if 宿主 | MATCH | ✓ | B98/B99 之外形态成立 |
| 对照 `return a or b and c`（平坦 and-or，e01 f_and_in_or_deep） | 函数深宿主 | MATCH | ✓ | 平坦混排成立；仅**显式分组**破 |
| 最小复现 `((a or b) and c) or d`（b98.py d1） | ≥3 层 | `if not a: return c or d; if b: pass` | ✗ | **同 B44 存量**（≥3 层布尔嵌套错构） |
| 最小复现 `a and ((b or c) and d)`（b98.py d2） | ≥3 层 | `a and b or c and d` | ✗ | **同 B44 存量** |
| e03 f_b1b_and_or_and / f_b1b_deep_right / f_b1b_none_check_prefix / f_b1b_loop_body_chain / f_b1b_ifexp_trueval | B1b 五臂外推+收缩 | ✗（5 单元） | ✗ | **B1 台账口径不足**（守卫未覆盖深右嵌套/while 体/B2 交叠） |
| e03 其余 9 单元（stmt_or_tail/shrink_or3/shrink_and3/not_group/body_before_cond/import_prefix/loop_header_cond/elif_mixed 等） | B1b 已封闭臂 | MATCH | ✓ | B1b 收缩面部分有效 |
| **NE01 负对照**（平坦 or/and、已知分组对、简单二元） | 浅层 for 宿主 | **1/5**（4 单元失败） | ✗ | **负对照失效**：浅层亦破 ⇒ BoolOp 破口**非深层专属**（比 C2「深层才错」更强） |

**F1 结论**：BoolOp 形态 **破口确证**（22/52）。机理三层：**B98**（or-in-and 分组保真，浅层/模块根/类体即破）＋ **B99**（for 宿主 BoolOp 表达式蒸发，与分组无关）＋ 同 B44 存量（≥3 层）；外加 B1b 守卫外推缺口（台账口径）。负对照 1/5 反证「浅层也破」，C2 深层专属前提不成立。

**锚点**：`core/cfg/region_ast_generator.py:37277 _build_grouped_boolop_expression`（INNER/OUTER/LAST 分类 + [B89] 外层操作数边界守卫）、`:37649 _build_boolop_expression`、`:37947 _detect_boolop_grouping`、`:37959 _try_build_and_inner_or_pattern`（or_groups 平坦化）。

**台账影响（II.3）**：BoolOp 现于 wiki 台账列为「完备」（`wiki/concepts/decompile-invariant-completeness.md §5`：形式层 完备128/破口0/零能力0）。**本轮证据要求 BoolOp 由「完备」降为「破口」**，形式层计数相应 完备127/破口1。禁止不改台账而维持「完备」（违 13 误解 #7「门禁读数当完备性」、#6「浅层测试当无感证明」）。

### 3.2 B1 台账口径重点复核

| 维度 | 结果 |
|---|---|
| 外推（深度≥3 / 混合链 / 深宿主） | e03 f_b1b_deep_right（`a or (b and (c or d))`）、f_b1b_and_or_and（`a and b or c and d`）失败 |
| 收缩（更短链） | f_b1b_shrink_or3 / shrink_and3 / stmt_or_tail MATCH（收缩面守得住） |
| while 宿主 | f_b1b_loop_body_chain（while 体 if 内 and-or）失败 ⇒ B1b 的 LoopRegion body 守卫（`region_analyzer.py:27978`）未覆盖该形态 |
| B2/B1b 交叠 | f_b1b_none_check_prefix（`if s is None or a: if i: return s`）失败 |
| ifexp 真值臂 | f_b1b_ifexp_trueval（`(a and b) if c else (a or b)`）失败 ⇒ B1b fix-r2 的 IfExp 真值块守卫（`:27988`）未覆盖 |
| 结论 | **B1b 封闭为「部分有效」，台账不得据 B1b 判 BoolOp 完备**；B98/B99 为独立机理，须独立登记 |

### 3.3 F2–F10 各族读数汇总

| 族 | 形态 | 探针（读/总） | 失败单元要点 | 判定 |
|---|---|---|---|---|
| **F2** | IfExp 三元 | e04 8/19、ne02 3/3 | `f_chain_ternary`/`f_ternary_deep_right`/`f_ternary_boolop_group`/`f_ternary_return`/`f_ternary_comp_cond`/`f_ternary_default_arg`/`f_ternary_subscript`/`f_ternary_walrus_rhs`/`f_ternary_as_cond`/`f_ternary_nested_in_boolop` + **`***None: Failure: Extra bytecode`（幻影 code object）** | 破口(深宿主/与 BoolOp 交叉) |
| **F3** | Compare 链 + 32 操作符叶子 | e05 4/11、e06 **14/14**、ne03 4/4 | 叶子操作符全过（e06 满）；链式 `f_compare_chain6`/`f_compare_is_chain`/`f_compare_in_chain`/`f_compare_notin_chain`/`f_compare_binop_inside`/`f_compare_subscript_inside`/`f_compare_walrus_value` 破 | 叶子完备 / 链式深宿主破口 |
| **F4** | BinOp/Unary/Starred/Slice/容器 | e07 15/16、ne04 4/4 | 仅 `f_slice_expr_bounds`（切片边界表达式）破 | 基本完备 |
| **F5** | Lambda | e08 28/30、ne05 5/5 | `f_lambda_deco_factory.deco.<lambda>`、`f_lambda_starargs.<lambda>`（Different bytecode） | 近完备 |
| **F6** | 推导式族 | e09 **30/30**、e09b 11/13、ne06 7/7 | 同步推导式完备；async `a_three`、`a_four.<genexpr>` 破（与 B96/B98 交叉） | 同步完备 / async 破口 |
| **F7** | Call/keyword/star_args | e10 31/32、ne07 6/6 | 仅 `f_starargs_mixed` 破 | 近完备 |
| **F8** | JoinedStr/f-string | e11 **13/13**、ne08 3/3 | — | **完备维持** |
| **F9** | Await/Yield | e12d 10/11、e12e 7/7、ne09 4/4；e12b/e12c/e12f **COMPILE_ERROR** | `f_await_cond_pos` 破；yield 作实参 / yield in boolop → 产物非法（`yield yield i or 0`、`yield sink(yield i)`，同类 B90 产物非法） | 部分完备 / 产物非法破口 |
| **F10** | NamedExpr 海象 | e13 11/18、ne10 1/3 | `f_walrus_chain`/`f_walrus_rhs_ternary`/`f_walrus_rhs_boolop`/`f_walrus_call_arg`/`f_walrus_deep_host`/`f_walrus_in_while_body`/`f_walrus_elif_chain` + NE10 n_simple_walrus/n_walrus_while | 破口（浅层即破） |

**族合计读数**：F1 22/52、F2 11/22、F3 22/29、F4 19/20、F5 33/35、F6 48/50、F7 37/38、F8 16/16、F9 21/22(+3 CE)、F10 12/21；**TOTAL 241/305**。

### 3.4 II.7 十三条误解自查（对本轮「完备维持/未破」宣告）

| # | 误解 | 本轮自查 |
|---|---|---|
| 1 | 循环论证分母 | 分母 305 由探针文件真实单元数求和，非循环定义；F8/F6 同步/F3 叶子分母来自独立探针 |
| 2 | 有过就算 | 未用「有成功单元」充完备；F1/F2/F10 均按单元失败数计破口 |
| 3 | 语料证据口径 | 探针单元 = 逐函数字节码等价，非文本比对 |
| 4 | 无限分母 | 分母固定 305，无动态扩张 |
| 5 | 节点词汇当完备 | F8/F6 同步/F3 叶子宣告「完备」基于**全部单元 MATCH ∧ 负对照 MATCH**，非仅词汇覆盖 |
| 6 | 浅层测试当无感证明 | F1 负对照 NE01 浅层即破 ⇒ 明确不据浅层判完备 |
| 7 | 门禁读数当完备性 | §2 站桩合格 ≠ 完备；§3 独立攻击给三态 |
| 8 | 顶层构造粗清单 | F1–F10 按 II.3 表B 全名单细分形态，非粗清单 |
| 9 | 识别率当完备性 | 未以「识别到」充「保真」；F9 识别到 yield 但产物非法 → 判破口 |
| 10 | 维度互替 | 宿主维度（模块根/类体/for/while/try/with/match）与形态维度交叉独立取证 |
| 11 | 改工具不改方法 | 未改核心；读数为 HEAD 原样 |
| 12 | 错误检测标准（3.11=CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star） | 本轮错误均为 `Different control flow/bytecode` 与 `Extra bytecode`，未见 except* 系列误报 |
| 13 | 语料上限当能力上限 | 未以语料规模推论能力上限 |

---

## §4 新破口登记（B98 起）

登记规则：与既有 Bn 同机理者标「同 Bn 存量」，不重复编号；新机理自 **B98** 续接。

### 4.1 新编号破口

| 编号 | 形态 | 最小复现（探针名+单元） | 锚点 file:line | 机制 | 违反条款 | 探针 |
|---|---|---|---|---|---|---|
| **B98** | **分组 boolop 保真破口**：`(or 组) and X` 的分组边界丢失，or 组被并入外层操作数链 → `a or b or c`；对称变体 `a and (b or c)` → or 子组整体蒸发 `a and b` | b98-b1 `return (a or b) and c`→`return a or b or c`；b98-b4 `a and (b or c)`→`a and b`；b98-b5 赋值位；e01.f_or_in_and_deep / f_or_in_and_pair_deep；e02 `<module>.M1` / `CB98.C1`（模块根/类体） | `region_ast_generator.py:37277 _build_grouped_boolop_expression`（INNER/OUTER/LAST 分类与 B89 外层操作数边界守卫）、`:37649 _build_boolop_expression`、`:37947 _detect_boolop_grouping`、`:37959 _try_build_and_inner_or_pattern` | 分组重建器在「内层 or + 外层 and」链上未产出 INNER→OUTER 边界（分类退化为全 OUTER/LAST），把内层 or 组平坦化进外层链；or 组作为「外层操作数」的唯一归属丢失 | **C2**（黑箱组合：抽象节点须整体保真组合）+ **C3**（守卫封闭：分组边界守卫未封闭操作数边界）+ 破坏 §1 原则三「嵌套即抽象节点」 | b98-b1/b4/b5、e01×2、e02×2 |
| **B99** | **`for` 宿主 BoolOp 表达式蒸发**：`for` 循环体内 `return <BoolOp>`（含平坦链）退化为 `return None`，或整条 `return` 语句消失（`for i: return a or b or c`→`return 0`）；`while` 宿主不受影响 | b99-for_host_plain `for i: if i: return a or b or c`→`return None`；b99-for_noif `for i: return a or b or c`→`return 0`；e02.CB98.m_class_body_host / f_try_body_host；别型 `if (a or b) and c: pass`（return 转 pass） | 候选定位：`region_analyzer.py:27978 _b1b_loop_body_run_continuation`（LoopRegion body_blocks 守卫邻域）、`region_ast_generator.py` 循环体尾随 return 归属区（参 B88 :1748-1794）；**待修复工程师定位**（本轮只给出宿主矩阵事实） | for 域循环体块认领时，BoolOp 值消费链的 Return 节点未被发射（`RETURN_VALUE` 前消费链在 for 体宿主断链）——静默蒸发，无报错 | **C1**（局部消费：for 体宿主下消费链断）+ **C2**（宿主相关发射）；同类 B88 但机理为「值位 BoolOp 消费链断裂」而非「块归属错位」 | b99-for_host_plain/for_noif、e02×2 |

### 4.2 「同 Bn 存量」机理外推证据（不重复编号）

| 同 Bn | 本轮新证据（单元） | 外推结论 |
|---|---|---|
| **B44**（≥3 层布尔嵌套错构） | b98-d1 `((a or b) and c) or d`、b98-d2 `a and ((b or c) and d)`、e03.f_b1b_deep_right `a or (b and (c or d))` | 触发面外推至「3 层混合分组的显式括号形」；d2 与 B98 交叠（同时含分组丢失与 ≥3 层错构） |
| **B1**（BoolOp 台账存量） | e03 五失败单元（and_or_and / deep_right / none_check_prefix / loop_body_chain / ifexp_trueval） | B1b 五臂封闭守卫（`region_analyzer.py:17902/19299/27978/27988/28245`）**未覆盖**：深右嵌套、`while` 体 if 链、`is None or` 前缀、IfExp 真值臂；台账口径不足 |
| **B96**（async 推导式） | e09b.a_three / a_four.<genexpr> | async 推导式在深宿主仍破（承接 round2 B96） |
| **B90**（产物非法） | e12b/e12c/e12f COMPILE_ERROR：`yield yield i or 0`、`yield sink(yield i)` | yield 作实参 / yield in boolop 的产物非法（同类 B90 生成路径产物非法），跨至 F9 |

### 4.3 探针退化伪差（口径注记，不登记为破口）

本轮**未复现** round2 的 `if 1:`/`while 1:`+break 折叠伪差——探针协议已全改用非常量条件。e04 中 `***None: Failure: Extra bytecode` 为**幻影 code object**（产物含多余 code 对象，比较器报 Extra bytecode），属真实破口表征（不是探针退化），已计入 F2 破口。

---

## §5 修复交接单（致 Task 3.2 修复工程师）

### 5.1 判据草案（只取 I.4 白名单：块末 opcode / 后继前驱集合 / 异常边 / 区域成员关系 / code object 元数据 / 指令 oparg）

| 破口 | 判据草案 |
|---|---|
| **B98** | 分组边界判据 = 链块短路跳转目标集合成员关系（指令 oparg 事实）：当某内层组操作数块的**跳转目标 ∉ 后续链块 fall-through 候选集**时，该操作数必为内层组封闭点（INNER→OUTER 边界）；`_build_grouped_boolop_expression` 须据跳转目标选出边界，禁止把「内层 or 组」并入外层操作数链。对称守卫：外层 and 的操作数数 = 顶层跳转边界计数。C1（内层组唯一归属内层发射）/C2（混合链重建与 CPython 求值序一致）/C3（判据不命中维持既有路径） |
| **B99** | for 域循环体块集内，`RETURN_VALUE`/`RETURN_CONST` 前消费链若为 BoolOp（块末跳转序 = 短路跳转 + RETURN），该返回块须整体认领并发射 Return(BoolOp)；判据 = 块集成员关系 + 块末 opcode 序，禁止按宿主（for vs while）分支裁剪发射。C1（for 体宿主消费链完整）+ C2（发射宿主无关） |
| **B44（同存量外推）** | ≥3 层混合分组：嵌套层级判据 = 分组重建递归深度，边界由跳转目标集合逐层封闭；d2 类交叠形须先修 B98 |
| **B1 台账口径** | 补齐 B1b 守卫域：① 深右嵌套（递归右子链）；② `while` 体 if 链（LoopRegion body_blocks 守卫域扩展）；③ `is None or` 前缀（前缀消费链）；④ IfExp 真值臂（B1b fix-r2 域扩展）。全部走跳转目标/后继集合判据，禁个案白名单 |

### 5.2 并行派发建议（破口族不相交 ∧ 涉改文件不相交）

- **位 1（`region_ast_generator.py` 分组重建层）**：B98 + B44 外推——同函数域（`_build_grouped_boolop_expression` / `_build_boolop_expression` / `_detect_boolop_grouping`），高内聚，建议串行。
- **位 2（`region_analyzer.py` 循环体认领层）**：B99 + B1b 守卫域扩展——同文件识别/认领域。
- **注**：B98 与 B99 涉改文件不相交（生成层 vs 识别层），可**并行**；但两者在 for 宿主探针上交叠，修复后须联合回归 e01/e02/e03/ne01。

### 5.3 门禁与回归提醒（对 3.2 修复工程师自测）

- 自测门禁 = 本轮全部 MISMATCH 转 MATCH ∧ NE01–NE10 负对照转 MATCH（现 NE01 1/5、NE10 1/3）∧ 站桩回归 6 面（§2）不变差 ∧ IV.2 门禁自检全过。
- **新增回归基准**：`test_repros/round3/` 28 探针本轮读数 **241/305 + 3 COMPILE_ERROR**，修复后不得低于本轮；已破单元修复后以 MATCH 为目标。
- **台账同步（强制）**：B98 确证后须同步 wiki 台账 §5 形式层计数（完备128→127 / 破口0→1），否则违 II.7 #7。
- 触及方法 docstring 六项模板（I.7）+ C1/C2/C3 条款；落地声明「代码已落地」（I.6）；判据禁止名字白名单/start_offset 魔数/深度特判/少发射换绿。
- B98 修复须对称覆盖「内层 or + 外层 and」与「内层 and + 外层 or」两向，且验证模块根 / 类体 / 函数宿主三宿主一致。

---

## 附：本轮产物清单

- `rounds/round3/`：REVIEW.md、`r3v2_attack.py`、`r3v2_verify_full.py`、`r3v2_compare_regress.py`、`r3v2_oldface_prep.py`、`r3v2_probe_index.json`、`r3v2_probe_results.json`、`r3v2_rv3_repro.json`、`r3v2_regress_*.json`、`r3v2_full_*.json`、`r3v2_oldface_*.json`、`r3v2_station_regress_compare.json`、`r3v2_core_delta.txt`
- `test_repros/round3/`：`gen_probes.py` + 28 探针（e01–e13、e09b、e12b–f、ne01–ne10，各 .py/.pyc/*OK.py）