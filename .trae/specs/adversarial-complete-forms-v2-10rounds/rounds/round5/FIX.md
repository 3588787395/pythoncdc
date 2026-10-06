# FIX.md —— Round 5 修复批次（Task 5.2）

- 基线 HEAD：`9b3eea38`。开工确认 `core/` 零在途变更。
- 判据唯一工具：`scripts/pyc_verify.py`（ruler = pylingual `equivalence_check.py::compare_pyc`，单位 = code object，含嵌套）。
- 方法学 RV2：一切读数先 `python pycdc.py <pyc> -o <同目录>OK.py` **regen** 再 verify；`batch` 只吃磁盘既有 `*OK.py` 产物，不得跳过 regen。
- 权威评审：`rounds/round5/REVIEW.md`（§3.1 三破口机制、§4 登记表、§5.1 优先级 P0/B116、P0/B114、P1/B115）。
- 证据一律 `r5v5fix_*` 前缀，**未覆盖** REVIEW 阶段 `r5v5_*` 证据。
- 未 `git add` / 未 `git commit`。

---

## 1. B116 —— 函数内裸注解 `b: str` 丢弃 → 局部名退化 `LOAD_GLOBAL`

**机制（REVIEW §3.1）**：CPython 对函数局部**裸注解** `b: <T>`（无值）不发射任何指令，仅把 `b` 登记进 `co_varnames`。区域→AST 名称消费阶段丢弃该声明、又未登记该局部名，导致 `return b` 退化为 `LOAD_GLOBAL`（重编后 `co_varnames` 丢失 `b`，字节码不一致）。违反 C1 局部消费。

**修复（代码已落地）**：`core/cfg/region_ast_generator.py` L2486–L2503（`_build_function_def`，`result = {...}` 之前）。
- 算法依据（I.4 白名单：co 元数据 `co_varnames` + 指令流）：候选本地名 = `co_varnames` 中**既非形参**（`args/posonlyargs/kwonlyargs/vararg/kwarg`）、**又无** `STORE_*`/`DELETE_*`/`MAKE_CELL`、**且非** `co_cellvars` 的标识符——正是裸注解声明的无语义绑定名。
- 幂等：先递归扫描已归约 `filtered_body` 中既有 `AnnAssign` target，避免重复注入（早前发现重复 `b: str` 两次，已修）。
- 发射 `{'type':'AnnAssign','target':Name(n,Store),'annotation':Name'str','value':None}`，插入点在 docstring（`filtered_body[0]` 为 Constant str）**之后**，保表序。
- 注释六项模板 + C1/C2/C3 声明见 L2486–L2502。

**复现读数**：`r5v5_03_annassign.pyc` → success（转 MATCH）；最小复现 `k4_bare_ann.pyc` → success；负对照 `k5_bare_ann_assign`、`k6_ann_only` → success。

---

## 2. B114 —— 未别名点号 import 的幻影别名

**机制（REVIEW §3.1）**：CPython `import a.b`（无 `as`）编译为 `IMPORT_NAME 'a.b'` + `STORE_NAME a`，绑定名 = **模块名首段** `a`（`module.split('.')[0]`），**无** `IMPORT_FROM`；只有 `import a.b as c` 才带 `IMPORT_FROM`。原实现在「无 `IMPORT_FROM` 的普通 import」路径拿 `STORE` 名与**完整点号模块名**比较，未别名路径被误判为别名，凭空发射 `import a.b as a`（多 `IMPORT_FROM`+`POP_TOP`）。违反 C1 局部消费 / C3 守卫封闭。

**修复（代码已落地）**：`core/cfg/region_ast_generator.py`，三条 import 归约路径统一改为「绑定名首段」判定：
- L32633（注释六项）+ L32651–L32652：`_build_statements_from_instructions` 普通 import 分支 —— `_bound_n = _module.split('.')[0]`，仅当 `_bound_n != _sto_n` 才追加 asname。
- L53598（注释六项）+ L53624–L53625：`_generate_block_statements_body` 的 `_ua_`（解包/多目标/链式赋值）import 子路由 —— `_bound_name = (_ua_pending_import.argval or '').split('.')[0]`，`_instr.argval != _bound_name` 才是真别名。
- L56403（注释六项）+ L56421–L56424：`_generate_stmts_from_instrs` 的 for 回边块重建路径 —— `_gi_bound_root = _gi_imp_module.split('.')[0]`，`len(_gi_store_names)==1 and store[0] != _gi_bound_root` 才发别名。
- 真别名分支（带 `IMPORT_FROM`，`_gi_has_from` / `_imp_from_pending`）**不动**。
- 判据取自 I.4 白名单：`IMPORT_NAME` 后继 `STORE_*` 的指令 oparg。

**复现读数**：`r5v5_01_module_root.pyc` → success（转 MATCH）；变体 `y1`–`y6`、`s1/s2/s5/s6/s34`、`t1`–`t5`、`z1`–`z6` 全 success（无回退）。

---

## 3. B115 —— 外层 `if` 体首语句为 `while` → 条件融合

**机制（REVIEW §3.1）**：外层 `if` 守卫块与其首个子块（while 头）在区域归约时被合并，if 条件求值块被当作 while 条件的一部分 → `if i: while i>0:` 输出 `while i and i > 0`（凭空 BoolOp，Different control flow）。违反 C3 守卫封闭 + 原则 2 每块唯一归属。触发方向单向（外层 `if` 体首 = `while`）。

**修复（代码已落地）**：分两处护栏，均以「循环区域成员关系」为判据（I.4 白名单）。

1. `core/cfg/region_analyzer.py` L18196–L18221（`_identify_conditional_regions`）+ L19074–L19082：新增 `_loop_guard_blocks` = 各 `LoopRegion` 的 `{entry, condition_block, header_block}`；内联 and 链游走在候选 `ft_next ∈ _loop_guard_blocks` 时终止。注释六项 + C1/C2/C3 见 L18197–L18214。
2. `core/cfg/region_analyzer.py` L28495–L28524（`_detect_boolop_conditional_chain`，`while current ...` 之前）新增 `_b115_loop_guard_map`（守卫块 → LoopRegion）；L28899–L28939 处非首成员候选块命中守卫时截断。
   **收窄判据（本轮关键修正）**：`while A and B:` 与 `if A: while B:` 在守卫点**局部同形**（A 的假后继 == B 的假后继），仅凭块末 opcode 无法区分，须看该循环是否在**自身回边重检中重新求值链首操作数 A**：
   - 真复合 while 条件的回边块会重检 A（`while not redata and count < 3:` 的回边前块重复 `LOAD_FAST:redata; POP_JUMP_FORWARD_IF_TRUE:<exit>`）⇒ 链首属本循环条件装配，**放行**。
   - `if A: while B:` 的回边只重检 B，A 从不重求值（`if i: while i>0:` 回边块仅 `POP_JUMP_BACKWARD_IF_TRUE:<header>`）⇒ 链首为循环之外的外层守卫，**截断**。
   实现：取链首块末二指令 `(opname, argval)`，在本循环任一非守卫块中找寻连续重现；未命中才截断。判据 = 块末 opcode / 后继-前驱指令集合 / 区域成员关系（I.4 白名单）。

> 早前「过宽护栏」（凡候选 ∈ 循环 `{entry,condition_block,header_block}` 即截断）会把**合法复合 while 条件**一起截断，令 34 集 3 文件回退（quote 84→83、klinedata 61→60、real_quote 43→40）。经二分定位确认唯一元凶为该护栏；现收窄为上述「回边重检」判据后回退消除。

**复现读数**：`r5v5_08_slice_callsite.pyc` → success（转 MATCH，输出正确的 `for i in xs: if i: while i > 0:`）；最小复现 `k1_ifwhile.pyc`、`k2_ifwhile_flag.pyc` → success；触发边界对照 `k3_ifwhile_swap.pyc`（内外互换）→ success；`g1/g3/g5/g6/g7` → success。
`g2_while_and3`、`g4_if_while_and` 仍 FAIL —— 经 `git stash` 基线复核为**既有**（非本轮引入，且不在官方 34 集门禁与站桩面内）。

---

## 4. 自测读数（IV.2 门禁，缺一不可）

| 门禁 | 读数 | 判定 |
|---|---|---|
| ① 三最小复现 regen+`single` | B114 `r5v5_01` success；B115 `r5v5_08`+`k1`+`k2` success；B116 `r5v5_03`+`k4` success（**三个全转 MATCH**） | PASS |
| ② 负对照逐位不变 | `y1`–`y6`、`s1/s2/s5/s6/s34`、`t1`–`t5`、`z1`–`z6`、`k3/k5/k6` 全 success | PASS |
| ③ 34 小测试集 `batch`（拆两半 CUT=17，基准 `baseline/small_test_report.json`） | `r5v5fix_batch34.json`：`{compile_error:0,error:0,failure:33,success:1}` units=**1505/1568** == 基线 1505/1568；**NEWFAIL=0** | PASS |
| ④ 站桩回归 6 面（单进程串行；`r5v5fix_station.py <face>` + `r5v5fix_compare_regress.py`） | round2face 234/251（same45）；probe42 176/196（improved14）；round1face 417/423（same24）；residual 417/446（improved10）；oldface 664/692（improved4）；quotation 152/153。**WORSE=0** | PASS |
| ⑤ 门禁自检 | IMPORT_OK；compile_error=0；无 `[B115DBG]`/`print`/`pdb` 插桩残留；未新增方法（无 I.5 七前缀 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）；各修复点均含 I.4 说明；落地标记 `[B114 fix]`×3 / `[B115 fix]`×4 / `[B116 fix]`×1（grep 命中） | PASS |
| ⑥ 逐轮足量 regen | 全部走 RV2：先 `pycdc -o` 再 verify | PASS |

> 站桩 `probe42/residual/oldface` 的 improved 计数系相对 round1/2/3 基线，含 round4+round5 累计修复；本轮只需 **WORSE=0**（达成）。

---

## 5. 涉改文件与证据

**core/ 源码（代码已落地，无占位/无 disabling `if False`）**
- `core/cfg/region_analyzer.py`：L18196–L18221、L19074–L19082（B115 ①）；L28495–L28524、L28899–L28939（B115 ②，含收窄判据）。
- `core/cfg/region_ast_generator.py`：L2486–L2503（B116）；L32633/L32651–L32652、L53598/L53624–L53625、L56403/L56421–L56424（B114）。
- 明细：`git diff --stat -- core/` = `region_analyzer.py +107`、`region_ast_generator.py +153/-3`。

**证据 JSON / 驱动（`rounds/round5/`，`r5v5fix_*` 前缀）**
- `r5v5fix_batch34.json`、`r5v5fix_station_regress_compare.json`
- `r5v5fix_regress_round2face.json`、`r5v5fix_regress_probe42.json`、`r5v5fix_full_round1face.json`、`r5v5fix_full_residual_a/b.json`、`r5v5fix_full_oldface_a/b.json`、`r5v5fix_quotation.json`
- 驱动：`r5v5fix_station.py`、`r5v5fix_compare_regress.py`（与原 `r5v5_*` 同逻辑，仅改前缀，**不覆盖** REVIEW 证据）

**探针产物（`test_repros/round5/`）**
- `r5fix_regen_verify.py`、`r5fix_batch34.py`、`r5fix_dump_regions.py`、`r5fix_dump_ast.py`、`r5fix_trace_import.py`
- `_scratch_r5v5/`：`k1/k2/k3`（B115 复现）、`k4/k5/k6`（B116）、`y*`/`s*`/`t*`/`z*`（B114）、`g1`–`g7`（B115 边界）、`probe_loop_fields.py`（LoopRegion 字段探针）

**未落地/待办**：无。B114/B115/B116 三者代码均已在 HEAD 之上落地并通过 IV.2 全部门禁。