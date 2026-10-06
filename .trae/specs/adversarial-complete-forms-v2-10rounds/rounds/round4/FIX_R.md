# Round 4 Task 4.2 · 修复交接单（位 2：识别/解析层）—— FIX_R.md

> 修复工程师：位 2（`core/cfg/region_analyzer.py`、`core/cfg/pattern_parser.py`，本轮唯一改动文件）。
> 理论基准：`spec.md`（I.1 四原则 / I.3 C1-C2-C3 / I.4 判据白名单 / I.5 禁止事项 / I.6 落地声明 / I.7 注释六项模板）。
> 破口登记：`rounds/round4/REVIEW.md` §4.1（B100–B113）。
> 口径：一切读数以 RV2 重建（`python pycdc.py <pyc> -o <同目录>OK.py`）后 `python scripts/pyc_verify.py single <pyc>` 为准。
> **代码已落地**；落地标记 grep：`[B102 fix]` 命中 **2** 处、`[B109 fix]` 命中 **1** 处、`[B103 fix]` 命中 **2** 处（见 §5）。

---

## 0 结论摘要

| 破口 | 形态 | 探针 | 前读数 | 后读数 | 判定 |
|---|---|---|---|---|---|
| **B102** | except* 多 handler 丢失 / except*-finally 无法配对 | `n4_05_neg_except_star` | 2/3 | **3/3** | **已封闭（机制 1+2）** |
| **B102** | 同上 | `c4_03_except_star` | 11/13 | **12/13** | 部分（残留 `e04_with`） |
| **B109** | while-else 丢失（体末为 break 分支） | `c4_02_loop_else` | 13/14 | **14/14** | **已封闭** |
| **B103** | match mapping 守卫丢失 / `is not None` 守卫极性 | `c4_04_match_patterns` | 8/13 | **10/13** | 部分（残留 e04/e05/e06） |
| **B113** | 多 for 子句推导式 | `c4_18_nested_comprehension` | **30/30** | **30/30** | **基线已绿（无改动）** |

**本席位交付 = B102（2 机制）+ B109 全封闭，B103 封闭 2 单元（CM.m 守卫、e07 `is not None`）**，读数自测前→后逐位推进；其余项据实登记残留（§7）。

---

## 1 B102 · except* 多 handler / except*+finally 配对

### 1.1 判据（I.4 白名单）
- **机制 1**：块内指令 opcode 族（`CHECK_EG_MATCH` / `PREP_RERAISE_STAR` / `RERAISE`）+ **同层后继/前驱集合 + 异常边**（`block.conditional_successors` = `successors - exception_successors`）。
- **机制 2**：handler 类型元数据（`handler_type ∈ {'except','except_star'}`）+ code object **异常表条目**（`try_start/try_end/handler_start`）。
- **禁用**：文件名/函数名白名单、`start_offset` 魔数、跨层 `X.entry in Y.blocks`、新增 `self` 跨方法状态、硬编码深度/计数上限。

### 1.2 机制（为何是 C1/C3 破口）
1. `_follow_except_chain` 沿 `successors` 取首元素探测「清理过渡块」时，CPython 3.11 对任何可抛指令登记**异常边**到外层 cleanup 块（`COPY; POP_EXCEPT; RERAISE`）。异常边与正常边共处 `successors`，取首元素先命中 cleanup 块（含 `RERAISE`）→ 误判「无下一 handler」，第 2 及后续 `except*` handler 被丢弃、其块降级为 else 臂。违反 C1（handler 链未消费全部异常组块）。
2. except-finally 配对判据只认 `handler_type == 'except'`，未认 `'except_star'`（`_classify_handler_type` 规则 4），使 `try/except*/else/finally` 的 `except*` 手无法与 `finally` 配对，`finally` 被拆成独立 `TryExceptRegion`，其 try 范围吞掉 else 体块 → 外层 `ast.Try.orelse` 丢失。违反 C1 + I.1 原则 2（每块唯一归属）。

### 1.3 算法修复（封闭守卫，非个案补丁）
- **机制 1**：过渡块探测改走 `conditional_successors`（排除异常边），BFS 遍历用 `_probe_visited` 集合封闭（终结性由块数有限保证，**去掉 `for _ in range(8)` 硬编码上限**），遇 `PREP_RERAISE_STAR`/`RERAISE` 停，遇 `_CHAIN_CHECK_OPS` 认领下一 handler。
- **机制 2**：配对判据放宽为 `other.get('handler_type') not in ('except', 'except_star')`。

### 1.4 改动 hunk（`core/cfg/region_analyzer.py`）
| 站点 | 行 | 说明 |
|---|---|---|
| `_follow_except_chain`（过渡块 BFS） | 11124–11162 | `conditional_successors` + visited 封闭 |
| `_identify_try_except_regions`（except-finally 配对） | 8333–8343 | 认领 `except_star` |

### 1.5 复现读数（前 → 后，RV2）
| 探针 | 覆盖 | 前 | 后 |
|---|---|---|---|
| `n4_05_neg_except_star`（登记负对照） | 多 handler except* 形态 | 2/3 | **3/3**（`n_except_star_two` 转 MATCH） |
| `c4_03_except_star`（登记探针） | 13 单元 | 11/13 | **12/13**（`e01_root` 转 MATCH） |

**残留**：`e04_with`（`except* + else + finally`，else 体位置识别错——`_find_inner_else_blocks` 搜索窗口假设 else 在 handler 之前，与 except* 布局冲突；属独立链，未在安全域内）。

---

## 2 B109 · while-else 丢失（体末为 break 分支）

### 2.1 判据（I.4 白名单）
- **break 落点集合**（同层事实）+ **条件求值块（`condition_block|header`）的非异常、非循环体后继集合**（同层后继/前驱集合事实）。
- **禁用**：文件名/函数名白名单、`start_offset` 阈值、跨层反查、新增 `self` 状态、硬编码深度/计数上限。

### 2.2 机制（为何是 C1/C3 破口）
`while xs: … if y>3: break \n else: return None \n return y` 形态下，`else` 体自身即 `return None`。原 `region_analyzer.py:4855` **无条件**调用 `region.mark_trailing_return_none()`，生成器（`region_ast_generator.py:7957`，**禁改**）据此把 else 体的 `return None` 摘出 `orelse` 并移到循环后 → 变成无条件 `return None`，令后续 `return y` 被判为死代码丢弃。违反 C1（else 体语句被错位消费）+ C3（未封闭 break 与 else 的归属）。

### 2.3 算法修复（封闭守卫）
仅当**命中真实 loop-else 结构事实**时跳过标记（`has_trailing_return_none` 维持 False → 生成器按 `has_break=True` 分支正常发射 `orelse=[Return None]`）。真实 loop-else 判据：`verified_break_blocks` 非空 ∧ 循环**每个**条件求值块（`condition_block|header` 与回边块 `back_edge_block`）的越体条件假后继都收敛到**同一个块**，且 `else_blocks[-1]` 即该块。其余形态（无 break 循环、for-else、else 体非纯 return None、else 体后另有隐式 return None 的布局）逐位不变（C2 黑箱组合）。
> ⚠ 本判据在首批实现中过宽（仅看首个条件块），触发**回退**，已收紧——详见 **§10 回退拦截整改**。

### 2.4 改动 hunk（`core/cfg/region_analyzer.py`）
| 站点 | 行 | 说明 |
|---|---|---|
| `_create_loop_region` 末端（`mark_trailing_return_none` 调用点） | 4855–4904 | 加封闭守卫（收敛判据，§10 收紧后） |

### 2.5 复现读数（前 → 后，RV2）
| 探针 | 前 | 后 |
|---|---|---|
| `c4_02_loop_else`（登记探针，14 单元） | 13/14 | **14/14**（`CL.m` 转 MATCH；输出恢复 `else: return None` + `return y`） |

**回归验证**：`_scratch_m4/r4_b109_shapes.pyc` 的 fallthrough 形态与修复前逐字节一致（该形态本就有 break→return 折叠旧缺陷，**非本次引入**）。

---

## 3 B103 · match mapping 守卫 / `is not None` 守卫极性

### 3.1 判据（I.4 白名单）
- **机制 1**：`pattern_blocks` 指令序列的**相邻操作码**（真值臂 = `LOAD x; POP_JUMP`，终结跳转紧邻 `LOAD` 之后；比较臂 = `LOAD x, [LOAD_CONST|LOAD y], (COMPARE|IS_OP), POP_JUMP`，终结跳转在 `i+3`）。
- **机制 2**：段末**跳转操作码族**（`IF_NONE`/`IF_NOT_NONE` 族 → None-ness 比较，非真值测试）。
- **禁用**：文件名/函数名白名单、`start_offset` 魔数、跨层反查、新增 `self` 状态、硬编码计数上限。

### 3.2 机制（为何是 C1/C3 破口）
1. `_extract_case_guard_from_blocks` 的 `guard_end` 定位一律从 `i+3` 起扫，**真值臂**（形式 b：`LOAD x; POP_JUMP → G`）的终结跳转在 `i+1` 被跳过 → `guard_end` 落空（或误取后续 case 的跳转）→ 守卫被吞（`CM.m` 的 `case {'a': v} if v:` 守卫丢失根因）。违反 C1（守卫块未消费）。
2. `_extract_arithmetic_guard` 对 `LOAD a; POP_JUMP_IF_NONE` 直接返回 `_eval_guard_expr_stack` 的裸 `Name(a)` 作守卫 → `case a if a is not None:` 被发射成 `if a:`。违反 C3（未按跳转族封闭 None-ness 语义）。

### 3.3 算法修复（封闭守卫）
- **机制 1**：`_ge_scan_from = i + 1 if is_truthiness else i + 3`（只读相邻 opcode 结构事实）。
- **机制 2**：`IF_NONE` 族臂 → `Compare(expr, 'is not', None)`；`IF_NOT_NONE` 族臂 → `Compare(expr, 'is', None)`；`IF_TRUE/IF_FALSE` 族逐位不变（C3 仅 NONE 族改写）。

### 3.4 改动 hunk（`core/cfg/pattern_parser.py`）
| 站点 | 行 | 说明 |
|---|---|---|
| `_extract_case_guard_from_blocks`（guard_end 定位） | 447–460 | `_ge_scan_from` 真值/比较臂分派 |
| `_extract_arithmetic_guard`（NONE 族极性） | 741–757 | None-ness 比较包装 |

### 3.5 复现读数（前 → 后，RV2）
| 探针 | 前 | 后 |
|---|---|---|
| `c4_04_match_patterns`（登记探针，13 单元） | 8/13 | **10/13**（`CM.m`、`e07_capture.inner` 转 MATCH） |

---

## 4 B113 · 多 for 子句推导式子句丢失（**基线已绿，无改动**）

`c4_18_nested_comprehension`（登记探针，30 单元）RV2 **基线即 30/30 success**；`comprehension_generator.py` **未改动**。

**根因探明（非可修复对象）**：`_scratch_m4/comp.py`、`comp2.py` 中 `for a in [x]`（单元素 list/tuple 字面量迭代）在推导式内被 CPython peephole **完全扁平化**为 `LOAD x; STORE a`，字节码层丢失该子句（`r4_dis_comp.txt`/`r4_dis_comp2.txt` 证据：`comp.py a2`、`comp2.py e1/e2` 等案例内层子句无 `FOR_ITER`）。此属编译器不可逆折叠，**不能从字节码区分内层子句**，非识别层破口。

---

## 5 落地标记 grep（I.6 复审入口）
```
[B102 fix] × 2  → region_analyzer.py:8334 、:11124
[B109 fix] × 1  → region_analyzer.py:4855
[B103 fix] × 2  → pattern_parser.py:447 、:741
```
`git status --porcelain core/` = ` M core/cfg/pattern_parser.py`、` M core/cfg/region_analyzer.py`（本席改动；`region_ast_generator.py` 为位 1 改动，本席**未改**）；`git diff --stat`：`region_analyzer.py` +72/−，`pattern_parser.py` +27/−。**未**改 `region_ast_generator.py` / `code_generator.py` / `comprehension_generator.py` / `exception_handler.py`；无 `git commit`。

---

## 6 I.7 注释六项 + C 条款自检
触及的识别/解析方法与新增守卫均已按 I.7 六项模板（①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程）以行内 `[Bxxx fix]` 注释写明，并注明满足/恢复的 C 条款；注释与代码真实行为一致：
- `region_analyzer.py:4855`（B109 封闭守卫，六项 + C1/C2/C3）
- `region_analyzer.py:8334`、`:11124`（B102 两机制，判据/白名单 + C1）
- `pattern_parser.py:447`、`:741`（B103 两机制，判据/C3）

---

## 7 残留与原因（未封闭，据实登记）

| 破口 | 状态 | 原因 |
|---|---|---|
| **B102 `c4_03/e04_with`** | 未封闭 | `except* + else + finally` 的 else 体位置识别错：`_find_inner_else_blocks` 搜索窗口假设 else 位于 handler 之前，与 except* 的异常组布局冲突。属独立链，改动面涉及 else 窗口重构，超出本轮已充分验证域。 |
| **B103 `c4_04/e04_mapping`** | 未封闭 | `_collect_all_pattern_instrs` 在第 1 个 mapping case 沿 `POP_JUMP_FORWARD_IF_NONE` 跳转目标（全 `POP_TOP` 清理块）被判为「pattern 延续」，随后无条件 fall-through **越界进入下一 case 头块**，把第 2 case 的 `DICT_UPDATE/STORE rest` 与键并入第 1 case 的指令集 → 第 1 case 带上 `**rest`、第 2 case 模式被覆写。边界判据需区分「同 case 成功路径嵌套延续」与「失败路径下一 case 头」（`case {'key': [first,*rest]}` 的嵌套 `MATCH_SEQUENCE` 是合法延续，与下一 case 头同为首指令 `MATCH_*`，**不能**用「首指令是否 `MATCH_*`」一刀切）。在无法跑全量语料回归的前提下引入该边界有回归已绿单元与语料风险，据实留待后续轮次专项。 |
| **B103 `c4_04/e05_class_kw`** | 未封闭 | 第 2/3 class case 在区域行走（`_identify_match_regions` 的 `current = jt` + 连接桩跳过）被拆成独立 MatchRegion（诊断显示 entry 4 与 entry 62 两块各自成区），归属链需重构；同属高危面。 |
| **B103 `c4_04/e06_or_guard`** | 未封闭 | `or + guard` 链（`case 1|2|3 if …`）完全错构：模式检查块被降级为 `if 2: pass / else …` 语句，match 被挪出 `with`。牵涉 or 短路链与 guard 链的交叉识别，风险高于收益。 |
| **B113** | 无需修复 | `c4_18_nested_comprehension` 基线 30/30；`comp.py`/`comp2.py` 的失败属 CPython peephole 不可逆扁平化形态（§4）。 |

---

## 8 IV.2 门禁自检（全过）
| 项 | 方法 | 结果 |
|---|---|---|
| py_compile | `python -m py_compile core/cfg/region_analyzer.py core/cfg/pattern_parser.py` | **OK（exit 0）** |
| import | `python -c "import core.cfg.region_analyzer, core.cfg.pattern_parser"` | **import_ok** |
| BOM 单头 | 首 3 字节 + 全文计数 | `region_analyzer.py` `efbbbf` / count=1（**存量，非本轮新增**）；`pattern_parser.py` 首 3 字节 `222222`（无 BOM）→ **PASS** |
| I.4 新增违规 | 名称白名单 / `start_offset` 魔数 / 跨层 `X.entry in Y.blocks` / 新增 `self` 跨方法状态 / 硬编码深度·计数 / 少发射换绿 | **新增 0**（两文件内新增判据均为 opcode 族/异常边/块成员关系/异常表事实；B102 机制 1 反而**移除**了 `range(8)` 硬编码上限） |
| I.5 禁止前缀 | `def (_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)` | **新增 0**（未新增任何方法） |
| 插桩残留 | `print(|pdb|breakpoint(|TODO|FIXME|DEBUG` | **新增 0** |
| `*OK.py` 手改 | 仅由 RV2 工具重建（`pycdc.py`），无手改 | **PASS** |
| 未改禁改文件 | `region_ast_generator.py`（位 1 属主）/ `comprehension_generator.py` / `exception_handler.py` | **未改** |
| 未提交 | `git commit` | **未执行** |

### 8.1 无回退验证（本轮自测探针）
`c4_02_loop_else` 14/14、`n4_05_neg_except_star` 3/3、`c4_03_except_star` 12/13、`c4_04_match_patterns` 10/13、`c4_18_nested_comprehension` 30/30 —— 各项 ≥ 登记基线（前→后单调不降，**WORSE=0**）。因任务约束未跑 402 全量 / 242 站桩批，跨语料无回退未做全量断言。

---

## 9 探针清单（`test_repros/round4/_scratch_m4/`）
- B109 形态复现：`r4_b109_shapes.py/.pyc/OK.py`
- **回退整改复现**：`r4b_loop_else.py/.pyc/OK.py`（① 末尾 while+break 无 else ② 真 while-else ③ for-else）+ `r4b_diag.py` / `r4b_diag_out.txt`（回退文件结构）/ `r4b_clm.txt`（CL.m 结构）
- B113 peephole 证据：`comp.py`、`comp2.py`（+ `r4_dis_comp.txt` / `r4_dis_comp2.txt`）
- 诊断工具（`r4_diag*.py`、`r4_dis_all.py`、`r4_dis_c4_04.txt`）为只读诊断脚本，含绝对 `sys.path` 引导行，不影响交付产物，保留作复审证据。

---

## 10 回退拦截整改（B109 守卫收紧）

### 10.1 根因（主代理实测回退）
- **回退文件**：`site-packages/IQEngine/plugins/plugin_fly_data/__init__.pyc`（全量 shard4）——基线 **success** → 首批修复后 **failure**（`ApiMethodPlugin._on_handle_order`，-1 单元）。
- **产物 diff**：`_on_handle_order` 的 while 循环之后**凭空多发射** `else:\n    return None`；该函数源码循环后**无 else 子句、无 return**，`RETURN_CONST None` 只是函数收尾。
- **根因一句话**：首批 B109 守卫只检查了**首个**条件求值块（`condition_block|header`）的越体后继，未检查**回边复判块**的越体后继，故把「无 else 时各出口各自重复的隐式 RETURN None」误判为「共享 else 块」，跳过标记 → 生成器未摘除 → 凭空补出 `else: return None`。
- **结构对照**（`r4b_diag.py` 实测）：
  | | 条件初判块 | 回边复判块 | 越体条件假后继 | 结论 |
  |---|---|---|---|---|
  | **CL.m**（真 else） | `@0 → @64` | `@60 → @64` | **收敛于 @64** | 真 loop-else |
  | **`_on_handle_order`**（无 else） | `@0 → @276` | `@258 → @272` | **互异（@276 vs @272）** | 隐式重复收尾 |

### 10.2 判据收紧（I.4 白名单事实）
真实 loop-else ⟺ `verified_break_blocks` 非空 ∧ **每个**条件求值块（`condition_block|header` + `back_edge_block`，须 ≥2 个）的 `conditional_successors` 中「不在 body、非 header、非 break 落点」的越体后继**恰好各 1 个且并集收敛为同一块** ∧ `else_blocks[-1]` 为该块。命中才跳过标记；否则维持 `has_trailing_return_none=True`（生成器经 `_other_return_none_blocks` 判定重复隐式 return 并摘除）。判据只用**同层后继集合 + 区域成员关系（body/break 落点）**——无文件名/函数名、无 `start_offset` 常数、无跨层 `entry in blocks`、无新增 `self` 状态、无计数/深度上限（C3 守卫封闭）。

### 10.3 改动 hunk（`core/cfg/region_analyzer.py`）
| 站点 | 行 | 说明 |
|---|---|---|
| `_create_loop_region` 末端 `mark_trailing_return_none` 调用点 | 4855–4904 | 收敛判据（I.7 六项 + C1/C2/C3，注释与行为一致） |

### 10.4 前 → 后读数（RV2）
| 探针 | 首批（回退） | 收紧后 | 判定 |
|---|---|---|---|
| `plugin_fly_data/__init__.pyc` | failure **20/21** | **success 21/21** | **回退封闭（恢复基线）** |
| `c4_02_loop_else` | 14/14 | **14/14** | B109 目标保持 |
| `c4_03_except_star` | 12/13 | **12/13** | B102 未误伤 |
| `c4_04_match_patterns` | 10/13 | **10/13** | B103 未误伤 |
| `_scratch_m4/r4b_loop_else.pyc` | — | **success 4/4** | 新复现 |

**新复现** `_scratch_m4/r4b_loop_else.py`（`r4b_*` 前缀）：① `f` = 函数末尾 while+break **无 else**（产物**不**发射 else ✓）；② `h` = 真 while-else（产物发射 `else: return None` + 末尾 `return y` ✓）；③ `k` = for-else 变体（产物发射 `else: return None` + 末尾 `return xs` ✓）。

### 10.5 「代码已落地」声明 + 落地标记 grep
```
[B109 fix] × 1  → region_analyzer.py:4855
```
`git status --porcelain core/`：` M core/cfg/pattern_parser.py`、` M core/cfg/region_analyzer.py`（本席）；`region_ast_generator.py` 为位 1 属主，本席**未改**。**未**改 `comprehension_generator.py` / `exception_handler.py` / `code_generator.py`；无 `git commit`；`*OK.py` 全部经 `pycdc.py` 重建（无手改）。

### 10.6 IV.2 自检（本轮整改）
| 项 | 方法 | 结果 |
|---|---|---|
| py_compile | `python -m py_compile core/cfg/region_analyzer.py` | **OK（exit 0）** |
| import | `python -c "import core.cfg.region_analyzer"` | **IMPORT_OK** |
| I.4 新增违规 | 名称白名单 / `start_offset` 魔数 / 跨层反查 / 新增 `self` 状态 / 硬编码计数·深度上限 | **新增 0** |
| I.5 禁止前缀 | 未新增任何方法 | **新增 0** |
| `*OK.py` 手改 / git commit | — | **无 / 未执行** |
| 未跑全量 | 402 全量 / 242 桩批 regen·verify | 由主代理统一重验 |