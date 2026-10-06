# Round 3 独立对抗复核（Task 3.3）—— REVIEW2

> 复核人 = 评审工程师（子代理）；只在读审计 + 独立复跑 + 新变体攻击，**未改 `core/`、未手改任何 `*OK.py`、未提交 git**。
> 被复核对象 = HEAD `7090ad96`（round3 修复批次，任务 3.2）相对评审批次 `1aecc150` 的全部改动。
> 判据唯一 = `scripts/pyc_verify.py`（ruler `pylingual-equivalence_check.py` sha256 `9c7567bd6776b36b`）；一切读数均在本机 **先 regen（`pycdc.py -o`）后 verify** 取得。
> 所有读数为本复核人亲自跑出；与 FIX 文档不一致处已显式标注。

---

## §1 逐 hunk 合规审计表

审计方法：`git diff 1aecc150 7090ad96 -- core/`（新增行 **319** 行，涉改 2 文件）+ 树内 grep + 字节级 BOM 计数 + `git status` + `*OK.py` regen 逐文件比对。

| # | hunk（file:行） | 内容 | I.4 黑名单五项 | I.5 七前缀 | 注释六项+C1/C2/C3 | 判定 |
|---|---|---|---|---|---|---|
| H1 | `region_ast_generator.py:37204-37333` | 新增 3 方法 `_resolve_boolop_tail_value_block`/`_reconstruct_boolop_tail_value_operand`/`_has_boolop_tail_value_boundary` | 无白名单/无阈值/无跨层反查/无 `self` 状态/无少发射/无深度上限 | 语义化命名，无禁用前缀 | 三方法 docstring 六项齐全 + C1/C2/C3，与 FIX_P1 §6 表一致 | **PASS** |
| H2 | `:37365-37380` | `_detect_boolop_grouping` 末尾值块 INNER 信号 | 判据 = 块末 opcode 族 + 后继集合 + 指令 `argval`（白名单） | — | 内联注释含【I.7 六项】①–⑥ + C1/C2/C3 | **PASS** |
| H3 | `:37691-37715` | `_build_grouped_boolop_expression` 末尾 fall-through 归属守卫 `_ft_is_chain_target` | 判据 = 链块跳转目标集合成员（指令 `argval`） | — | 内联注释含【I.7 六项】+ C1/C2/C3 | **PASS** |
| H4 | `:38105-38119` | `_build_boolop_expression_inner` 分组重建前置守卫 | 判据 = 非末链块跳转目标是否命中末尾值块（同层结构事实） | — | 内联注释含【I.7 六项】+ C1/C2/C3 | **PASS** |
| H5 | `:38726-38741` | `_try_build_and_inner_or_pattern` 内层 or 组末位补收 | 判据 = 末 or 块块末 opcode 族 + 后继集合 | — | 内联注释含【I.7 六项】+ C1/C2/C3 | **PASS** |
| H6 | `region_analyzer.py:22580-22594` | `_can_be_ternary_header` 收尾极性守卫 `if last.opname in SHORT_CIRCUIT_JUMP_OPS: return False` | 判据 = 块末 opcode 族（白名单） | 未新增方法 | 注释为**散文**，**未含** C1/C2/C3 与②–⑥结构化条目 | **观察项（见 §5-B）** |
| H7 | `:30069-30076` | R113 分支调用点加 `_has_compare_chain_step_predecessor` 守卫 | 判据 = 块末 opcode 族 + 前驱集合 + 前驱块指令 opcode | — | 调用点注释说明充分 | **PASS** |
| H8 | `:31131-31179` | 新增方法 `_has_compare_chain_step_predecessor` | 无白名单/无阈值/无跨层反查/无 `self` 状态/无少发射/无深度上限 | 语义化命名 | docstring 六项齐全 + C1/C2/C3，与 FIX_P2 §6 表一致 | **PASS** |
| H9 | `:31182-31218` | `_is_chained_compare_cleanup_block` 加 docstring（方法体**未变**） | — | — | **docstring ① 与代码行为不一致**：声称本方法内加「前驱守卫才认定为清理块」，实际方法体仍对任意 `SWAP+POP_TOP` 返 True；守卫只在 H7 调用点施加 | **FAIL（I.7）见 §5-A** |

### 1.1 grep 计数（全部针对新增行）

| 红线 | 扫描方法（新增行） | 命中 | 判定 |
|---|---|---|---|
| I.4-① 文件/函数名白名单 | `co_name\|func_name\|filename\|WHITELIST\|co_names\|name ==` | **0** | PASS |
| I.4-② `start_offset` 魔法阈值 | `start_offset` | 7 处，全部为 `== / != 指令 argval` 身份比较或 `{...}` 集合成员 / `sorted(key=)`（**无任何 `> / < / == 常数`**） | PASS |
| I.4-③ 跨层 `X.entry in Y.blocks` 反查 | `in blocks` | **0**（`_s in region.blocks` 为**本区域**成员判定，白名单允许） | PASS |
| I.4-④ 新增 `self.` 跨方法状态 | `^\+\s*self\.\w+\s*=` | **0** | PASS |
| I.4-⑤ 少发射 / 硬编码深度·计数上限 | `MAX_DEPTH\|max_depth\|depth [<>]=?` | **0** | PASS |
| I.5 七前缀新增方法 | `^\+\s*def\s+(_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)` | **0**（新增 4 def 全语义化：H1×3 + H8×1） | PASS |
| 插桩残留 | `^\+.*(print(\|pdb\|breakpoint(\|# TODO\|# FIXME\|# DEBUG\|# XXX)` | **0** | PASS |
| BOM 单头（IV.2） | 字节级全文 `efbbbf` 计数 | `region_analyzer.py` = **1**（首 3 字节 `EFBBBF`）；`region_ast_generator.py` = **1** | PASS |
| 在途变更 | `git status --porcelain` | **core/ 零改动**；唯一新增 = 本任务 `r3v3_*` 探针与证据（未跟踪、已声明）；`.pyc` 被 gitignore | PASS |
| 命令时限 | 全部 ≤ 300s | 单批最慢 42.5s（242 站桩文件 batch） | PASS |
| 落地标记（I.6） | `grep "[B98]"` / `grep "[B99 fix]"` | `[B98]` **7** 处（`:37209/37265/37302/37368/37694/38105/38729`）；`[B99 fix]` **4** 处（`:22580/30069/31135/31190`）；新方法定义 `:37204/:37260/:37300/:31131` —— 全部与 FIX 文档声明**逐个一致**，代码确在树内 | PASS |

### 1.2 `*OK.py` 是否手改（方法学核验）

- `git diff 1aecc150 7090ad96` 共改动 **12** 个 tracked `*OK.py`（`rv3_02_b89_boolop_chainOK.py`、`_scratch_b98/hostsOK.py`、`_scratch_b98/residOK.py`、`_scratch_b99/b99minOK.py`、e01/e02/e03/e04/e05/e13/ne01 OK.py、`round7/r7_12_boolop_nestOK.py`）。
- 复核动作：对上述 12 个 `*OK.py` **逐一 `python pycdc.py <pyc> -o <OK.py>` 重建**，随后 `git status --porcelain` → **0 个 tracked `*OK.py` 显示 modified**（即重建产物与提交内容**逐字节一致**）。
- 结论：这 12 个差异**确为「改善/中性的重生成产物」，非人工伪造**。旁证：e01 产物 `r = b and (c or d) if not a else c`、`ne01` 三单元转 `return a or b or c` 等均为可解释的 B98/B99 改善，且与探针读数改善同向。**判定 PASS**。

### §1 小结
I.4 五项 / I.5 七前缀 / BOM / 插桩 / 在途 / 落地标记 / `*OK.py` 全部 **PASS**；仅 **H9（I.7 注释与代码行为不一致）FAIL**，另有 H6 一处**声明不实观察项**。

---

## §2 独立复跑读数表

### 2.1 28 探针（`test_repros/round3/`，索引 `r3v2_probe_index.json`）

复核动作：对 28 个 `.pyc` 全部 **重新 regen**，再 `pyc_verify.py batch --index … --json r3v3_probe_results.json`。
证据：`r3v3_probe_results.json`（我的读数）、`r3v3_probe_compare.json`（逐单元集合比对）。

| 读数 | 我的读数 | FIX 声明 | 是否一致 |
|---|---|---|---|
| 单元级 | **248/305** | FIX_P2 = 248/305 | ✓ 一致 |
| 文件级 success/failure/compile_error | **12 / 13 / 3** | 12 / 13 / 3 | ✓ 一致 |
| COMPILE_ERROR 文件 | **e12b/e12c/e12f**（3 个） | 3 个 | ✓ 一致 |

**真实回退判定（success→failure 逐单元集合比对，按单元名前缀去「failure 信息形态」干扰）**：

| 对照基线 | 基线读数 | NEWFAIL（新失败单元） | FIXED（转 MATCH 单元） | 判定 |
|---|---|---|---|---|
| `r3v2_probe_results_fixP1.json` | 244/305 | **0** | 4 | **无真实回退** |
| `r3v2_probe_results_fixP2.json` | 248/305 | **0** | 0 | **与 FIX_P2 逐单元一致** |
| `r3v2_probe_results.json`（评审 241） | 241/305 | **0** | 7 | **无真实回退** |

- FIXED 明细（vs 评审 241）：`e02 <module>`、`e02 CB98`、`e02 CB98.m_class_body_host`、`e02 f_try_body_host`、`ne01 n_flat_and/n_flat_or/n_simple_two`（共 7）。
- **结论：FIX_P2 声称的「NEWFAIL=0」经本复核人独立逐单元比对，判定为真。** 未发现任何 success→failure 的真实单元回退（仅有 failure 文件内部的信息形态变化，已被单元名规范化剥离）。

### 2.2 站桩回归 6 面（`r3v3_station.py`，242 文件 regen+batch，证据 `r3v3_station_results.json` / `r3v3_station_compare.json`）

| 面 | 文件数 | 我的读数 | FIX 声明读数 | same/improved/**WORSE** | 是否一致 |
|---|---|---|---|---|---|
| round2face 45 | 45 | **234/251** | 234/251 | 45/0/**0** | ✓ |
| probe42 42 | 42 | **154/189 → 172/196** | 172/196 | 32/10/**0** | ✓ |
| round1face 24 | 24 | **417/423** | 417/423 | 24/0/**0** | ✓ |
| residual 72 | 72 | **404/446 → 417/446** | 417/446 | 62/10/**0** | ✓ |
| oldface 59 | 59 | **658/692 → 664/692** | 664/692 | 55/4/**0** | ✓ |
| quotation 单验 | 1 | **152/153**（唯一失败 `change_his_to_forward`；失败单元数 1） | 152/153 | 持平 | ✓ |

- **6 面 WORSE=0**，`only_base` 全为空（无缺失文件），与 FIX_P1/FIX_P2 §4.4 读数**逐面一致**。
-  améliorations 面：probe42（+18 单元，10 文件）、residual（+13 单元，10 文件）、oldface（+6 单元，4 文件）；与 FIX 声明的改善落点一致。
- 口径注记：round2face/probe42 基线仅存 **tail**（失败单元名截断），其比对条目中的 `new_extras` 系基线字符串截断造成的**伪差**；两面的 **units 读数逐位持平、WORSE=0**，故不判回退。

### 2.3 最小复现抽查（独立复跑）

| 复现 | 我的读数 | FIX 声明 | 是否一致 |
|---|---|---|---|
| `_scratch_b98/hosts.pyc` | **success 7/7** | 7/7 | ✓ |
| `_scratch_b98/resid.pyc` | **2/5**，失败 `r_d1/r_e3/r_g2`（`r_d2` MATCH） | 2/5 同失败集 | ✓ |
| `_scratch_b99/b99min.pyc` | **8/9**，唯一失败 `for_grouped` | 8/9 | ✓ |
| `e01_g1_b98_matrix` / `e03_g1_b1b_stress` / `ne01_g1_neg` / `ne10_g10_neg` | **5/15 / 9/14 / 4/5 / 1/3** | 同 | ✓ |

---

## §3 新变体攻击结果表

**方法**：自建 5 个 `r3v3_` 探针（`test_repros/round3/`，各 .py 独立、含宿主矩阵；不含 `if 1:`/`while 1:`+break 折叠宿主），在 **HEAD（含两处修复）** 与 **`1aecc150`（修复前，经 `git worktree` 只读检出）** 上分别 regen+verify，做「新/旧」逐单元对照以区分**误伤**与**存量**。
证据：`r3v3_attack_results.json`（HEAD）、worktree `…/r3v3_attack_results.json`（旧码）。

| 探针 | 攻击面 | 旧码(1aecc150) | HEAD(7090ad96) | HEAD 失败单元 | 判定 |
|---|---|---|---|---|---|
| `r3v3_a_ternary_boolop_cond`（12 单元） | 位2 `_can_be_ternary_header` 收尾守卫误杀真三元/真条件头 | 8/12 | **8/12** | `t_or_cond_pair`、`t_cond_or_of_and`、`t_cond_chain_or`、`t_in_for_return` | **无新增失败（旧新失败集逐单元相同）＝无误伤**；其中 4 单元为**存量** |
| `r3v3_b_compare_chains`（16 单元） | 位2 `_has_compare_chain_step_predecessor` 前驱守卫误伤真链式比较 | 10/16 | **10/16** | `cc_while`、`cc_for_value`、`cc_for_return`、`cc_ternary`、`cc_and`、`cc_or` | **无新增失败＝无误伤**；`cc_basic/cc_mixed/cc_in/cc_notin/cc_is/cc_if/cc_for/cc_comp` 全部 MATCH |
| `r3v3_c_b98_group`（15 单元，含收缩形/非 boolop if 链） | 位1 B98 tail-value 守卫误伤（`a and (b or c) and d`、`(a or b) and (c or d)`、`(a and b) or c and d`、多层显式括号、非 boolop 同形跳转） | 9/15 | **15/15（+6）** | 无 | **零失败、零回退；纯改善** |
| `r3v3_d_interaction`（9 单元） | 位1×位2 在 for/while 宿主 + boolop 分组交叠（`for: return (a or b) and c`、`while c: if i: return (a and b) or c`） | 1/9 | **2/9（+1）** | `i_for_return_group`、`i_for_if_return_group`、`i_while_if_return_group`、`i_for_return_group_pair`、`i_for_return_chain_compare`、`i_for_return_group_and_chain`、`i_while_group_value` | **无回退（`i_for_return_flat_or` 转 MATCH）；7 失败单元在旧码同样失败＝存量；无相互遮蔽/新错构** |
| `r3v3_e_negctl`（11 单元，负对照） | 已封闭形态的浅层等价物应同时 MATCH | 9/11 | **11/11（+2）** | 无 | **负对照全部 MATCH，封闭成立**（`(a or b) and c` 与 `a or b and c` 同时 MATCH） |

**总判：新变体攻击未发现任何误伤（假阴性）或由本轮修复引入的新破口。** 5 探针在 HEAD 上合计 **46/63**，旧码 **37/63**，净 +9，失败单元集**只减不增**。关键判据：
- 位2 守卫对**真三元**（`t_simple`/`t_and_cond`/`t_nested`）、**真链式比较**（`cc_basic/mixed/in/notin/is/if/for/comp`）**全部保持 MATCH** → 收尾极性与前驱守卫未误杀真形态。
- 位1 B98 守卫在新造 15 单元上 **15/15**（旧码 9/15），含对称形、多层显式括号、收缩形与非 boolop 同形跳转 → 无误伤。
- 位1×位2 交叠面：无「相互遮蔽」现象（出现的 7 个失败单元在旧码同样失败，非新错构）。

**负对照配对结果（宣称已封闭形态 ∧ 浅层等价物）**：

| 配对 | 形态 | HEAD | 判定 |
|---|---|---|---|
| `n_deep_grouped_or_in_and` / `n_shallow_flat_or_and` | `(a or b) and c` / `a or b and c` | 均 MATCH | 封闭成立 |
| `n_deep_and_or_right` / `n_shallow_flat_and_or` | `a and (b or c)` / `a and b or c` | 均 MATCH | 封闭成立 |
| `n_for_flat_return` / `n_flat_and3` | for 宿主平坦 and 链 | 均 MATCH | 封闭成立 |

---

## §4 发现的新破口或误伤

**本轮未发现由 `7090ad96` 引入的新破口或误伤**（新变体攻击失败单元集 ⊂ 旧码失败单元集，零新增）。

下列为攻击中暴露的**存量残余**（旧码同样失败，属同 Bn 存量而非新编号，不计 B100）：

| 单元 | 形态 | 现象 | 归类 | 旧码是否同样失败 |
|---|---|---|---|---|
| `t_cond_chain_or` | `return a if (b or c or d) else 0` | 输出 `a if b or c else 0`（丢失 `or d`） | **同 B98/B1 存量**（三元条件平坦 or 链截断） | ✓ |
| `t_or_cond_pair` / `t_cond_or_of_and` | `(a and b) if (c or d) else e` / `a if (b and c or d) else e` | 输出 if/else 形（语义等价但结构不同→ Different control flow） | 同 F2 三元存量（结构非等价） | ✓ |
| `cc_and` / `cc_or` | `a < b < c and d` / `a < b < c or d` | 输出 `a < b < c`（丢失 `and d`/`or d`） | **同 B1/B98 存量**（链式比较后 boolop 截断） | ✓ |
| `cc_while` / `cc_for_value` / `cc_for_return` / `cc_ternary` | 链式比较在 while / 推导取值 / for-return / 三元宿主 | 错构/蒸发/结构非等价 | **同 F3/B99 存量** | ✓ |
| `i_for_return_group` / `i_for_if_return_group` / `i_for_return_group_pair` / `i_for_return_group_and_chain` | `for: [if i:] return <分组 boolop>` | `return` 消失为 `if …: pass` | **同 B99 存量**（FIX_P2 §7 已登记 `for_grouped`） | ✓ |
| `i_while_if_return_group` | `while: if n: return (a and b) or c` | 输出 `if a: return b or c`（错误重组） | **同 B98 存量**（宿主交叠面） | ✓ |
| `i_for_return_chain_compare` / `cc_for_return` | `for: return a < b < c` | `b; return None` | **同 B99 存量**（for 体值消费链） | ✓ |

> 上述均**未**由本轮修复引入，且 FIX_P1 §7 / FIX_P2 §7 已如实登记其主类（B44 深层全-merge、B99 `for_grouped`、B1b 五单元、d1/g2 移交）。本复核人仅**补充外推证据**（三元平坦 or 条件、链式比较后 boolop、for-return 链式比较等），建议 Task 3.4 视情并入台账。

---

## §5 终审结论

### 5.1 功能面：全部达标

| 门禁 | 要求 | 我的读数 | 判定 |
|---|---|---|---|
| 28 探针不低基线 | ≥241/305 | **248/305** | ✓ |
| 真实 success→failure 回退 | 0 | **0**（三基线逐单元比对） | ✓ |
| 站桩 6 面 | WORSE=0 | **WORSE=0**（6 面逐位与 FIX 声明一致） | ✓ |
| 轮门禁 | ≥1 破口封闭 **或** ≥1 pyc 读数改善 | **二者皆有**：B98/B99 封闭（28 探针 +7、`rv3_02` 0/1→1/1、`hosts` 7/7）+ 站桩 5 面改善 | ✓ |
| I.4 五项 / I.5 七前缀 / BOM / 插桩 / 在途 | 零违规 | **全 PASS** | ✓ |
| `*OK.py` 手改 | 无 | **12 文件重建逐字节一致** | ✓ |

### 5.2 合规面：**打回（I.7 注释与代码行为不一致）**

> 依 spec.md I.7「注释与代码行为不一致 = 评审不通过」及行 226「算法合规审计…发现即打回，零容忍」，判 **打回**。**打回项为纯文档级，不涉及算法/读数**——功能面证据充分，最小整改后可直接放行。

**打回项 A（I.7，识别层方法注释与代码行为不符）**
- 位置：`core/cfg/region_analyzer.py:31182-31194`（`_is_chained_compare_cleanup_block` docstring ①）。
- 事实：docstring 声称「[B99 fix] 追加 `_has_compare_chain_step_predecessor` 守卫：只有存在…前驱块时才认定为清理块」；但方法体（`:31219-31222`）**未变**，仍对任意 `SWAP+POP_TOP` 返回 True。守卫实际只在 R113 调用点 `:30074-30076` 施加；另有 3 处调用点（`:27274` `_boolop_resolve_merge`、`:27639` `_create_boolop_region_from_chain`、`:31231` `_get_effective_merge_through_cleanup`）**不经守卫**。docstring 对该方法的契约描述与真实行为不符。
- 最小复现（只读）：`python -c "import re;print([l for l in open('core/cfg/region_analyzer.py',encoding='utf-8')][31218:31222])"` 可见方法体仅 4 行判定，无前驱守卫调用；而 `:30074` 调用点才出现 `and self._has_compare_chain_step_predecessor(_jt_block)`。
- 最小整改（建议，doc-only）：将 docstring ① 改述为「本方法只判定 `SWAP+POP_TOP` 同形；真·比较链清理块的排除守卫 `_has_compare_chain_step_predecessor` 由 `_detect_boolop_short_circuit_chain` R113 调用点施加，其余调用点（`_get_effective_merge_through_cleanup` 等）按可穿透语义使用」。**不得**直接把守卫塞进方法体（会改变 `_get_effective_merge_through_cleanup` 的下溯语义，风险高）。

**打回项 B（I.7 声明不实 / 模板缺失，次级）**
- 位置：`core/cfg/region_analyzer.py:22580-22594`（`_can_be_ternary_header` 新增段）。
- 事实：FIX_P2 §6 对照表声明该新增段「C1/C2/C3 齐全」，但代码注释为散文，**未显式给出 C1/C2/C3 声明，也未给出 ②–⑥ 结构**（仅提「原则 2 / I.4 白名单」）。
- 最小整改（doc-only）：在该注释末尾补 C1/C2/C3 三行（可直接复用 FIX_P2 §3 自证文字：C1 只读块末 opcode 族；C2 真 ternary 与 BoolOp 各自独立保真；C3 守卫封闭 ternary 认领域）；或在 §6 表如实标注「C1/C2/C3 见所在 `_identify_ternary_regions` docstring」。

### 5.3 终审判定
**打回**（仅打回项 A、B，均为文档级、无算法/读数风险）。整改后无需重跑全量回归（改动不触及判据与发射），Task 3.4 只需复验该 2 处注释文本。

### 5.4 II.7 十三条误解自查（本复核人自身）
- #6「浅层测试当无感证明」：未犯——三态判定不以浅层 MATCH 充完备，且负对照与深层矩阵交叉取证。
- #7「门禁读数当完备性」：未犯——§2 站桩合格仅作回归旁证，§3 独立攻击另给三态；未据门禁判任何形态「完备」。
- #11「改工具不改方法」：未犯——本复核人**未改 core/**，读数为 HEAD 原样；对照旧码经独立 worktree 检出（未污染工作树）。
- 其余各条（循环论证分母 / 有过就算 / 语料口径 / 无限分母 / 节点词汇 / 顶层粗清单 / 识别率 / 维度互替 / 3.11 错误检测标准 / 语料上限）：本报告未据以立论，未犯。

---

## §6 移交 Task 3.4 主代理验证清单

**需重点复验的读数（本复核人已独立跑出，建议主代理抽验同值）**
1. 28 探针 **248/305**、COMPILE_ERROR **3**（e12b/e12c/e12f）、**NEWFAIL=0**（对照 fixP1=244 / 评审=241）——证据 `r3v3_probe_results.json`、`r3v3_probe_compare.json`。
2. 站桩 6 面 **WORSE=0**：round2face 234/251、probe42 172/196、round1face 417/423、residual 417/446、oldface 664/692、quotation 152/153——证据 `r3v3_station_results.json`、`r3v3_station_compare.json`。
3. 新变体 5 探针 HEAD **46/63** vs 旧码 **37/63**（零误伤）——证据 `r3v3_attack_results.json` 与 worktree 对照。

**需重点复验的风险面**
- **打回项 A/B 的整改文本**是否落地为 doc-only（不做算法改动），整改后确认 `_is_chained_compare_cleanup_block` 方法体仍为 4 行、`_can_be_ternary_header` 守卫未移动。
- **未守卫的 3 处 `_is_chained_compare_cleanup_block` 调用点**（`:27274/:27639/:31231`）是否需要同步加守卫：本复核的新探针未证明其引发回归（HEAD 无 NEWFAIL），但属潜在残余风险，建议登记而非本轮改动。
- **§4 存量残余**（`t_cond_chain_or`、`cc_and/cc_or`、for-return 链式比较等）是否为既有 Bn 覆盖面，建议并入台账外推证据，勿误记为 B100。

**本任务新增产物（`r3v3_` 前缀，未覆盖任何 r3v2 评审/FIX 证据，未提交 git）**
- 探针：`test_repros/round3/r3v3_a_ternary_boolop_cond.py`、`r3v3_b_compare_chains.py`、`r3v3_c_b98_group.py`、`r3v3_d_interaction.py`、`r3v3_e_negctl.py`（各含 .pyc 与 `*OK.py`）。
- 驱动/证据：`r3v3_attack.py`、`r3v3_attack_index.json`、`r3v3_attack_results.json`、`r3v3_probe_results.json`、`r3v3_probe_compare.py`、`r3v3_probe_compare.json`、`r3v3_station.py`、`r3v3_station_index.json`、`r3v3_station_results.json`、`r3v3_station_compare.json`、`r3v3_station_log.txt`。

---

## §5.5 整改闭环复核与终审放行（Task 3.3 追加，2026-10-06）

> 本节为对整改提交 **`3b098f99`**（父 `7090ad96`，commit message「round3 复核打回整改（任务 3.3 打回项 A/B 闭环）——纯文档级」）的**独立闭环复核**，只读审计，未改 `core/`，未提交 git。`§1–§5.4` 结论原样保留，本节仅追加。

### 5.5.1 整改范围（git 逐 hunk）

`git diff --name-only 7090ad96 HEAD` → 仅 4 个 tracked 文件，其中 `core/` **只有 `region_analyzer.py`**（`region_ast_generator.py` 未触碰）：`FIX_P2.md`（+83/-1）、`core/cfg/region_analyzer.py`（**3 hunk，16 insertions / 11 deletions**）、`_scratch_b99/doconly_check.py`（新增）、`_scratch_b99/doconly_sample.json`（新增）。3 个 hunk 全为注释/docstring 行增删，**无可执行语句行改动**。

### 5.5.2 打回项 A 闭环核验（`_is_chained_compare_cleanup_block` docstring ①）

| 核验点 | 事实 | 判定 |
|---|---|---|
| docstring ① 是否与**方法体真实行为**一致 | 改后 ①（`:31188-31197`）明述「**本方法只按 `SWAP 2 + POP_TOP` …判定「清理块形态」，不做任何前驱判定**；B99 的「比较链步前驱」追加条件由**调用点**（`_detect_boolop_short_circuit_chain` 的 R113 分支）以 `_has_compare_chain_step_predecessor` 施加，不在本方法内」——与真实行为一致 | ✓ 闭环 |
| C 条款尾行同步改述 | `:31219-31222` 改为「C1 只读本块指令序列与 opcode…／C2…／C3 本方法只判形态；对循环返回拆除段的显式排除由**调用点** `_has_compare_chain_step_predecessor` 施加，守卫封闭在**调用侧**」——与调用点事实一致 | ✓ |
| 方法体**仍为原样** | `:31224-31227` 仍为原 **4 行**：`meaningful = [...] / if len(meaningful) == 2 and meaningful[0].opname == 'SWAP' and meaningful[1].opname == 'POP_TOP': / return True / return False`，**无任何前驱守卫调用** | ✓ 未改逻辑 |
| 守卫调用点**未移动/未增删** | `and self._has_compare_chain_step_predecessor(_jt_block))` 仍在同一条 R113 判定式内（`:30078-30080`，结构位置与父版一致；绝对行号因上方 +4 注释行而 +4） | ✓ |

### 5.5.3 打回项 B 闭环核验（`_can_be_ternary_header` 新增段）

- 改后注释段末尾**已补显式 C1/C2/C3 三行**（`:22594-22597`）：「C1：只读本块末指令 opcode 族（SHORT_CIRCUIT_JUMP_OPS），同层结构事实／C2：真 ternary 条件恒以条件跳转收尾…各自独立保真／C3：守卫封闭 ternary 认领域，令值位 BoolOp 链步块唯一归 BoolOpRegion」——**措辞与代码真实行为一致**（守卫判据即 `last.opname in SHORT_CIRCUIT_JUMP_OPS` → `return False`）。
- **守卫位置未移动**：`if last.opname in SHORT_CIRCUIT_JUMP_OPS:` 段（`:22570` 起）仍在 `_can_be_ternary_header` 内、`if block not in self.block_to_region:`（`:22599`）之前；仅注释块内追加 3 行注释，`return False` 顺延至 `:22598`。**判定 ✓ 闭环**。

### 5.5.4 零算法改动的独立证据（不采信 FIX_P2 §9 自证）

| 证据 | 方法（本复核自建） | 结果 |
|---|---|---|
| **AST 恒等** | `test_repros/round3/_scratch_b99/r3v3_doconly_indep.py`：父版直接由 `git show 7090ad96:core/cfg/region_analyzer.py` 取，与当前工作树文本各自 `ast.parse` → 剥离 docstring → `ast.dump` 比较 | **`LOGIC_AST_EQUAL = True`**（`cur_len=1687539`、`pre_len=1687185`、`delta=354`，全部为注释/docstring 文本） |
| **可执行 token 恒等** | 同上脚本对两侧文本 `tokenize`，剔除 `COMMENT/NL/NEWLINE/INDENT/DEDENT/ENCODING/ENDMARKER/**STRING**` 后比较 token 流 | **`EXEC_TOKEN_EQUAL = True`**（无任何非字符串、非注释 token 变化） |
| 双向印证 | 另跑工程师自证脚本 `_scratch_b99/doconly_check.py`（反向还原法） | `LOGIC_AST_EQUAL = True`（`delta=354`）——与本复核独立结论一致 |
| 编译/导入 | `python -m py_compile core/cfg/region_analyzer.py` / `import core.cfg.region_analyzer` | `RC=0` / `IMPORT_OK` |

**结论：整改为纯文档级，可执行代码语义恒等（零算法改动），独立于 FIX_P2 自证。**

### 5.5.5 FIX_P2 §6/§8/§9 与整改后代码的一致性核验

| 项 | FIX_P2 表述 | 整改后代码实测 | 判定 |
|---|---|---|---|
| §8 证据文件名校正 | 9 个 `*_fixP2.json` + 驱动 `r3v2_fixP2_station.py` | 目录内**逐个存在** | ✓ 校正正确 |
| §6 `_is_chained_compare_cleanup_block` 行号 `:31185` | — | def 实在 `:31185` | ✓ |
| §6 `_can_be_ternary_header` 新增段 `:22580`、C1/C2/C3 显式齐全 `:22594-22597` | — | 一致 | ✓ |
| §9.2 打回项 B 改后文本 / 位置 `:22594-22597`、`return False` `:22598` | — | 一致 | ✓ |
| §9.3 AST 恒等表（`True`、1687539/1687185/354、3 hunk、16/11） | — | 本复核逐位复现 | ✓ |
| §6 `_has_compare_chain_step_predecessor` 行号 `:31131` | — | 实测 `:31135`（**+4 陈旧**） | ⚠ 非阻断登记 |
| §8 `grep "[B99 fix]" → 4 处（`:22580`/`:30069`/`:31135`/`:31190`）` | — | 实测 **3 处**（`:22580`/`:30073`/`:31139`；① 改写删去 1 处字面量） | ⚠ 非阻断登记 |
| §8 `def … :31131`、`R113 守卫行 :30076` | — | 实测 `:31135` / `:30080`（**+4 陈旧**） | ⚠ 非阻断登记 |
| §9.1 方法体范围 `:31223-31226` | — | 实测 `:31224-31227`（**+1 陈旧**） | ⚠ 非阻断登记 |

> **说明**：上述陈旧项**全部为报告文档的行号/计数坐标**，由打回项 B「在 `:22591` 插入 4 行注释」使其后锚点整体 +4 所致；而 §9.1 内部又有一处 +1 的手工偏移。**代码本体、判据、发射逻辑、读数均不受影响**；`[B98]` 7 处、落地事实（`grep` 命中 / IMPORT_OK / PY_COMPILE_OK / BOM=1）仍然成立。**登记为归档时校正项（不触及 `core/`），不构成打回。**

### 5.5.6 顺带核验（合规面零新增）

| 项 | 方法 | 结果 |
|---|---|---|
| BOM 恰 1 个 | `efbbbf` 全文计数 | `region_analyzer.py = 1`、`region_ast_generator.py = 1` | ✓ |
| I.5 七前缀 | 本提交新增行 grep `def (_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)` | **0** | ✓ |
| I.4 黑名单（名字白名单 / `start_offset` 阈值 / 跨层 `entry in blocks` / 新增 `self` 状态 / 硬编码深度计数） | 本提交新增行 grep | **0** | ✓ |
| 插桩残留 | 本提交新增行 grep `print(\|breakpoint(\|pdb.\|traceback` | **0** | ✓ |
| 在途变更 | `git status --porcelain` | tracked modified = **0**（core 与 `*OK.py` 均无改动；仅未跟踪的 `r3v3_*` 证据与 `_scratch_b99/r3v3_doconly_indep.py`） | ✓ |

### 5.5.7 抽验读数（doc-only 不应改变任何读数；regen 后 `pyc_verify batch`，判据唯一）

| 抽验 pyc | 期望 | 实测 | 判定 |
|---|---|---|---|
| `test_repros/round3/e02_g1_b98_hosts.pyc` | 11/18 | **11/18** | ✓ 持平 |
| `test_repros/round3/ne01_g1_neg.pyc` | 4/5 | **4/5** | ✓ 持平 |

> 两者均**先 `pycdc.py <pyc> -o <OK.py>` 重建**再 batch verify；证据 `round3/r3v3_closure_sample.py` → `r3v3_closure_sample.json`（regen 后 tracked `*OK.py` 仍 0 处 modified）。读数与整改前逐位一致，印证零算法改动。

### 5.5.8 终审判定

**终审放行。** 打回项 A（`:31188-31197` + C 条款 `:31219-31222`）与 B（`:22594-22597`）**均已闭环**：代码注释/docstring 现与**方法体/守卫的真实行为**逐字一致，方法体仍为原 4 行、守卫位置未移动。**零算法改动**由独立 AST 恒等 + 可执行 token 恒等（`LOGIC_AST_EQUAL/EXEC_TOKEN_EQUAL = True`）双向证实；`e02` 11/18、`ne01` 4/5 抽验持平；BOM=1、I.5/I.4/插桩零新增。

唯一残留为 **FIX_P2 §6/§8/§9 的 5 处行号/计数坐标陈旧**（§5.5.5 表内 ⚠ 项），属报告文档元数据、由注释插入所致的坐标漂移，**不影响代码正确性、判据、发射与任何读数**，**登记为归档时校正项**，不构成打回。Round 3 修复批次（`7090ad96` + `3b098f99`）**通过终审**。
