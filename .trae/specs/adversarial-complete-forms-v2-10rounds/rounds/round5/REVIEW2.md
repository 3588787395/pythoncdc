# Round 5 复核报告（Task 5.3）—— 修复批次 `6fa1fa70` 逐 hunk 终审

- 规范：`.trae/specs/adversarial-complete-forms-v2-10rounds`
- 角色：独立对抗评审工程师子代理（只读审计 + 探针/证据构建；**零 core 修改 / 零 git 提交**）
- 基线 `9b3eea38` → 修复批次 HEAD `6fa1fa70`（`git rev-parse HEAD` 实测 = `6fa1fa70df821f8524f059fa5a6e038c0831102c`；`git status --porcelain core/` 为空）
- 判据唯一：`scripts/pyc_verify.py`（ruler sha256 `9c7567bd6776b36b`）
- 方法学：**RV2** —— 一切读数先 `python pycdc.py <pyc> -o <同目录>OK.py` regen，再 verify；`batch` 只吃磁盘既有 `*OK.py`。**禁采信 FIX.md 数字**，全部读数本轮独立复跑
- 修复范围（`git diff --stat 9b3eea38..6fa1fa70 -- core/`）：`region_analyzer.py` +107、`region_ast_generator.py` +153/-3；共 8 个 hunk（各有「①②③④⑤⑥ + C1/C2/C3」注释模板）

---

## §1 逐 hunk 合规结论表（对照 I.1–I.7 / C1/C2/C3 / I.4 黑名单 / I.5 七前缀）

### 1.1 `core/cfg/region_analyzer.py`（B115 护栏）

| # | hunk 锚点 | 实质内容 | I.4 判据归类 | 黑名单核查 | 结论 |
|---|---|---|---|---|---|
| A1 | `region_analyzer.py:18215-18221` | `_loop_guard_blocks` = 各 `LoopRegion` 的 `{entry, condition_block, header_block}`，源为**方法形参 `loop_regions`** | 区域成员关系 | 无文件名/函数名特判；无 `start_offset` 比较；**无新增 `self.` 状态**（形参局部）；无深度上限 | **PASS** |
| A2 | `region_analyzer.py:19081-19082` | `if _main_ft_next in _loop_guard_blocks: break`（**宽判据**，无条件截断 and 链） | 集合成员（区域成员关系） | 纯本地；无魔数 | **PASS**（宽判据，见 §3 变体证不误伤真复合 while） |
| A3 | `region_analyzer.py:28517-28524` | `_b115_loop_guard_map` = 守卫块 → `LoopRegion`，源为 **`self.regions`（只读）** | 区域成员关系 | 只读既有状态，非新增跨方法状态；无特判 | **PASS** |
| A4 | `region_analyzer.py:28916-28939` | **收窄判据**：取 `chain[0][0].instructions[-2:]`（链首块末二指令），在本 `LoopRegion` 的非守卫块中搜连续重现，未命中才 `break` | 块末 opcode / 后继-前驱指令集合 | 纯 `opname`/`argval`；`current in _b115_loop_guard_map` 为本地 dict 查找（**非** `entry in blocks` 跨层反查）；无 `self.` 新增 | **PASS** |

### 1.2 `core/cfg/region_ast_generator.py`（B114 / B116）

| # | hunk 锚点 | 实质内容 | I.4 判据归类 | 黑名单核查 | 结论 |
|---|---|---|---|---|---|
| B1 | `region_ast_generator.py:2487-2567`（B116） | 裸注解登记：候选 = `co_varnames` 中非形参、无 `STORE_*`/`DELETE_*`/`MAKE_CELL`、非 `co_cellvars` 者 → 前置发 `AnnAssign(target=Name,annotation=Name('str'),value=None)` | **code object 元数据**（`co_varnames`/`co_cellvars`）+ 指令流 | 无名字白名单；无 `self.` 新增；无深度上限；仅函数体名称级补全，不动控制流 | **PASS**（覆盖缺口见 §4.2） |
| B2 | `region_ast_generator.py:32633-32657`（B114 path1） | `_bound_n = _module.split('.')[0]`；`_bound_n != _sto_n` ? 别名 `{name:_module,asname:_sto_n}` : `{name:_module,asname:None}` | 指令 oparg（IMPORT_NAME / STORE argval） | 纯 oparg；name 恒为完整模块名 | **PASS（正确）** |
| B3 | `region_ast_generator.py:53598-53626`（B114 path2） | `_bound_name = argval.split('.')[0]`；`_alias = argval if argval != _bound_name else None` | 指令 oparg | 纯 oparg；未别名 → asname=None | **PASS（正确）** |
| B4 | `region_ast_generator.py:56403-56426`（B114 path3） | 新增 `_gi_bound_root = _gi_imp_module.split('.')[0]` + `if len==1 and store[0]!=bound_root` 别名；**then 分支沿用旧 `{name:_gi_imp_module,asname:store}`，else 分支沿用旧 `[{name:_n,asname:None}]`** | 指令 oparg | 判据纯 oparg、不误伤真别名 ✓ | **PASS（判据）／缺陷：else 分支语义错误**，见 §4.1 |

### 1.3 合规横切审计（本轮新增代码）

| 项 | 方法 | 结果 | 判定 |
|---|---|---|---|
| I.5 七前缀（新增） | grep `def (_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)` in `core/cfg` | 仅 2 命中，均**历史存量**（`region_ast_generator.py:20068 _merge_block_is_then_exclusive`、`:41169 _merge_block_is_loop_back_edge`，round4 已登记），8 hunk 新增标识符为 `_loop_guard_blocks`/`_b115_*`/`_b116_*`/`_gi_bound_root`/`_bound_n`/`_bound_name`，**无一命中** | 新增 **0 PASS** |
| BOM（IV.2 单头） | 字节级读 `region_analyzer.py` / `region_ast_generator.py` | 两文件头 3 字节均 `efbbbf`，全文 BOM 计数各 = **1** | **PASS** |
| `start_offset` 常数比较 | 读 8 hunk | 新增行**无一**做 `start_offset == <常数>`（A2 邻近的 `start_offset` 用于 visited 去重/跳转目标比较，属**未改动的上下文**） | **PASS** |
| 新增 `self.` 跨方法状态 | 读 8 hunk | 全部为方法内局部变量；A1 取形参、A3/A4 只读 `self.regions` | **PASS** |
| 硬编码深度上限 / 少发射换绿 | 读 8 hunk | 无 `max_depth`/`depth >` 新增；B116 仅**补一个无字节码声明节点**，未删减发射 | **PASS** |
| 注释模板（I.7 六项 + C1/C2/C3） | 读 8 hunk | 8 hunk 均含 ①②③④⑤⑥ + C1/C2/C3；**唯 B4 的 ⑤「name 保持完整模块名」与实际 else 分支不符**（见 §4.1） | **PASS（1 处注释失真）** |

---

## §2 独立复跑读数表（RV2，本轮实测）

### 2.1 三最小复现（题设 B114/B115/B116 各自转 MATCH？）

执行：`rounds/round5/r5v5r_minrepro.py`（先 regen 再 verify）→ 证据 `r5v5r_minrepro.json`

| 复现 | 归属 | 修复前（REVIEW §3.1） | **本轮回读** | 判定 |
|---|---|---|---|---|
| `r5v5_01_module_root.pyc` | B114 | 2/3（幻影 `import os.path as os`） | **3/3 success** | **真转 MATCH** |
| `r5v5_08_slice_callsite.pyc` | B115 | 10/11（`sl_deep` 条件融合） | **11/11 success** | **真转 MATCH** |
| `_scratch_r5v5/k1_ifwhile.pyc` | B115 | FAIL（`while i and i>0`） | **2/2 success** | **真转 MATCH** |
| `_scratch_r5v5/k2_ifwhile_flag.pyc` | B115 | FAIL | **2/2 success** | **真转 MATCH** |
| `r5v5_03_annassign.pyc` | B116 | 10/11（`ann_root` 裸注解丢名） | **11/11 success** | **真转 MATCH** |
| `_scratch_r5v5/k4_bare_ann.pyc` | B116 | FAIL（`return b`→LOAD_GLOBAL） | **2/2 success** | **真转 MATCH** |

**六项全部转 MATCH**，B114/B115/B116 的**最小复现核**已闭合。

### 2.2 34 小测试集（batch 拆两半 + compare）

执行：`rounds/round5/r5v5r_batch34.py`（34 pyc 逐个 regen → `pyc_verify.py batch` 对半 17+17 → 合并 → compare 基线 `baseline/small_test_report.json`）→ 证据 `r5v5r_batch34_a|b|merged.json`、`r5v5r_batch34_compare.txt`

```
units: 1505/1568 (95.98%) -> 1505/1568 (95.98%)
REGRESSIONS=0 IMPROVED=0
```

**NEWFAIL = 0**（与 FIX.md 声称的 1505/1568 一致；本轮独立复跑逐位吻合）。

### 2.3 站桩 6 面（**单进程串行**，RV2 逐面 regen→verify）

执行：`r5v5r_station.py <face>` × 6（串行）→ 对照 `r5v5r_compare_regress.py` → 证据 `r5v5r_regress_*/*_full_*/*_quotation.json`、`r5v5r_station_regress_compare.json`

| 面 | 既有基线 | **本轮回读** | common | same | improved | **WORSE** | 判定 |
|---|---|---|---|---|---|---|---|
| round2 45 文件面 | 234/251 | **234/251** | 45 | 45 | 0 | **0** | 持平 |
| round2 42 探针面 | 172/196（REVIEW §2） | **176/196** | 42 | 28 | 14 | **0** | +4 改善 |
| round1 哨兵面 | 417/423 | **417/423** | 24 | 24 | 0 | **0** | 持平 |
| v1 残余面 | 417/446 | **417/446** | 72 | 62 | 10 | **0** | 持平/累计改善 |
| 旧规范 round6–10 面 | 664/692 | **664/692** | 59 | 55 | 4 | **0** | 持平/累计改善 |
| quotation.pyc 单验 | 152/153 | **152/153** | 1 | 1 | 0 | **0** | 持平 |

**六面 WORSE = 0，无任何文件回退**（改善项均为历史累计 + 本轮导入/布尔链修复外溢）。并发纪律保持：全部单进程串行。

---

## §3 变体攻击结果（`r5v5r_*`，32 文件 / 58 单元）

执行：`test_repros/round5/gen_probes_r5v5r.py` → `rounds/round5/r5v5r_variant_results.json`

**总读数 51/58**。失败 6 单元：

| 变体 | 读数 | 失败单元 | 基线副本复跑（隔离 `$env:TEMP\r5v5r_base`，`r5v5r_baseline_variant.json`） | 判定 |
|---|---|---|---|---|
| `b114_in_for` | 0/1 | 产物 `import os`（丢 `.b`） | 基线 0/1 | **既有失败** |
| `b114_in_while` | 0/1 | 产物 `import os.path as os`（幻影） | 基线 0/1 | **既有失败** |
| `b114_in_func_for` | 1/2 | `<module>.f` | 基线 1/2 | **既有失败** |
| `b115_while_and3` | 1/2 | `f`：`while a and b and c` 乱码 | 基线 1/2（输出逐字相同） | **既有失败** |
| `b116_closure_bare` | 1/3 | 闭包捕获裸注解 | 基线 1/3 | **既有失败** |
| `b116_default` | 1/2 | `<module>` 幻影 | 基线 **0/2** | **改善** |

**变体 NEWFAIL = 0**（5 项既有失败 + 1 项改善）。

### 3.1 B115（本轮最高风险）专项

- **真复合 while 未被误伤**：`b115_while_and`(2/2)、`b115_while_or`(2/2)、`b115_while_reeval`(2/2)、`b115_while_true_break`(2/2)、`b115_nested_for_while`(2/2)、`b115_while_in_try`(2/2)、`b115_for_if_while`(2/2) **全 PASS** —— 收窄判据（回边是否重检链首操作数 A）在跨宿主真复合 while 上**未产生 success→failure**。
- **if-while 融合未漏放**：`b115_if_while`(2/2)、`b115_if_and_while`(2/2) **全 PASS**（`if A: while B:` 与 `if A and B: while C:` 均被正确拆开）。
- 唯一失败 `b115_while_and3`（三操作数 `while a and b and c`）：基线逐字相同 → **既有失败，非本轮引入**。
- **结论：B115 满足"任何 success→failure 即打回"的反向条件——零 success→failure。**

### 3.2 B114 专项

- **真别名未误伤**：`b114_realias`(1/1)、`b114_multi`(1/1)、`b114_from`(1/1) **全 PASS**。
- **点号深度 ≥3 / 元组解包组合**：`b114_deep3`(1/1)、`b114_tuple`(1/1) **PASS**。
- `b114_module`(1/1) PASS（path1/path2 正确）。
- 宿主嵌套（for/while/函数内 for）仍失败（§4.1），**均为既有失败**。

### 3.3 B116 专项

- **无误注入**：`b116_bare`(2/2)、`b116_posonly`(2/2)、`b116_posonly_kw`(2/2)、`b116_posonly_only`(2/2)、`b116_kwonly`(2/2)、`b116_class_bare`(3/3)、`b116_loop_bare`(2/2)、`b116_cond_bare`(2/2)、`b116_nested_bare`(3/3)、`b116_mix`(2/2) **全 PASS**。
- 直读 `r5v5r_b116_posonlyOK.py` = `def f(a): return a`，**无幻影 `a: str`**（`/` 标记被合并进 `args`，`posonlyargs` 未单列未致误注入，见 §4.2）。
- 闭包捕获 `b116_closure_bare`(1/3) 为既有失败。

---

## §4 打回 / 缺陷登记

### 4.1 【打回】B114 path3 else 分支语义错误（`core/cfg/region_ast_generator.py:56425`）

- **hunk**：`@@ -56272 +56400`（B114 path3，for 回边块重建路径）。
- **条款**：C1 局部消费（模块名绑定信息被丢弃，跨语句语义错误）；并**自相矛盾**于同 hunk 注释⑤「Import 节点 names 的 name 保持完整模块名」。
- **机制**：新增条件 `if len(_gi_store_names)==1 and _gi_store_names[0] != _gi_bound_root` 使**未别名点号 import**（`import a.b` → `IMPORT_NAME 'a.b'` + `STORE_NAME a`，故 store='a' == `_gi_bound_root`='a'）落入 **else 分支** `[{name:_n, asname:None}]`，以 **store 名 `a` 作 name**，**丢失点号子模块**，发射 `import a`（应 `import a.b`）。
- **复现**：`test_repros/round5/r5v5r_b114_in_for.pyc`（源 `for i in range(3): import os.path; r.append(os.path)`）→ 产物 `import os`（`r5v5r_b114_in_forOK.py:6`），verify `***<module>: Different bytecode`。
- **性质**：**非 NEWFAIL**（基线 9b3eea38 同返 0/1，但基线错法为 `import os.path as os` 幻影别名，本 hunk 改后错法变为丢子模块 `import os`——同为失败，未致回退）。**但该 hunk 改动的行为在可达路径上语义错误**，属修复不完整 + 改动行引入新错法。
- **整改**：else 分支单 store 且未别名点号时须 `{name: _gi_imp_module, asname: None}`（即与 path1 `{name:_module,...}` 对齐）；或对该情形直发 `Import(names=[{name:_gi_imp_module, asname:None}])`。
- 附：`b114_in_while`(0/1) 走**另一条未修复路径**仍发幻影 `import os.path as os`（REVIEW §4 B114 原症状未在本批覆盖）——一并移交。

### 4.2 【缺陷·非阻断】B116 两处覆盖缺口

1. **`posonlyargs` 未显式列入形参排除集**（`region_ast_generator.py:2505-2516` 仅收 `args`/`kwonlyargs`/`vararg`/`kwarg`）。**实测无幻影注入**（`b116_posonly*` 全 PASS，直读 OK 无 `a: str`），因反编译器把 `def f(a, /)` 的 `a` 归入 `args`（`/` 标记丢失为既有独立问题）。属**潜在缺口**（若后续 arg 重建改把 posonly 单列即会误注入），建议显式加 `posonlyargs` 防御。
2. **`co_cellvars` 被列入排除集**（`:2517`），致**闭包捕获的裸注解**不登记（`b116_closure_bare` 1/3，既有失败）。为保守收窄、非回归；若要求闭合该族需区分"裸注解 cellvar"（无 `STORE_DEREF`）与"真 cellvar"。

### 4.3 【观察·非阻断】B116 硬编码注解 `Name('str')`

`:2554` 注入的 `annotation` 恒为 `str`。函数局部裸注解在 CPython 不发射字节码、真类型**不可从 code object 恢复**，故取值对判据中性（bytecode 等价成立）；仅属源保真限制（如 `c: float` → `c: str`），登记备查。

---

## §5 终审结论

| 维度 | 结论 |
|---|---|
| 逐 hunk 合规（I.1–I.7 / C1/C2/C3 / I.4 黑名单 / I.5 / BOM） | **PASS**（8 hunk 全合规；I.5 新增 0、BOM 单头、无新 `self.`/无 `start_offset` 阈值/无深度上限；唯 B4 注释⑤失真） |
| 三最小复现转 MATCH | **PASS**（6/6 转 success） |
| 34 小测试集 | **PASS**（1505/1568，**NEWFAIL=0**，与 FIX 一致） |
| 站桩 6 面 | **PASS**（**WORSE=0**，全 6 面；含 +4~+14 累计改善） |
| 变体攻击（B115 高风险 / B114 / B116） | **NEWFAIL=0**；B115 **零 success→failure**（真复合 while 未误伤、if-while 未漏放） |
| **终审** | **有条件放行（B115 / B116 通过；B114 打回 1 项）** |

**判定：本轮修复批次 B115、B116 复核通过；B114 因 §4.1（path3 else 分支语义错误）打回，须修正 `core/cfg/region_ast_generator.py:56425` 后再放行。** 无任何观测到的回退（NEWFAIL=0 / WORSE=0），故打回**不因回归**，而因该改动行在可达的 for 回边宿主路径上产出**语义错误输出**（丢点号子模块），且与自身注释⑤矛盾——属"修复不完整且改动行引入新错法"。§4.2/§4.3 为**非阻断**登记项，随附整改建议。

---

### 交付物清单（本轮 `r5v5r_*`，零覆盖既有 `r5v5_*`/`r5v5fix_*`）

- 本报告：`rounds/round5/REVIEW2.md`
- 驱动脚本（`rounds/round5/`）：`r5v5r_station.py`、`r5v5r_compare_regress.py`、`r5v5r_minrepro.py`、`r5v5r_batch34.py`、`r5v5r_basecheck.py`
- 证据 JSON（`rounds/round5/`）：`r5v5r_minrepro.json`、`r5v5r_batch34_a|b|merged.json` + `r5v5r_batch34_compare.txt`、`r5v5r_regress_round2face.json`、`r5v5r_regress_probe42.json`、`r5v5r_full_round1face.json`、`r5v5r_full_residual_a|b.json`、`r5v5r_full_oldface_a|b.json`、`r5v5r_quotation.json`、`r5v5r_station_regress_compare.json`、`r5v5r_variant_results.json`、`r5v5r_baseline_variant.json`
- 探针：`test_repros/round5/r5v5r_*.py(+.pyc/+OK.py)`（32 变体）、`test_repros/round5/gen_probes_r5v5r.py`

*复核纪律：零 core 修改、零 git 提交。所有读数经 RV2 独立复跑，未采信 FIX.md 数字。判据唯一 = `scripts/pyc_verify.py`。*