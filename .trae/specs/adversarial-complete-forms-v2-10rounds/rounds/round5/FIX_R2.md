# Round 5 复核整改报告（Task 5.3）—— B114 path3 else 分支语义修正

- 规范：`.trae/specs/adversarial-complete-forms-v2-10rounds`
- 角色：修复工程师子代理（算法修复 + 注释合规；**未 git add / commit**）
- 输入基线：HEAD `dcca6518`（复核批次已提交；复核判「有条件放行」，仅 B114 §4.1 打回）
- 权威打回报告：`rounds/round5/REVIEW2.md` §4.1
- 判据唯一：`scripts/pyc_verify.py`（ruler = pylingual `equivalence_check.py::compare_pyc`，sha256 `9c7567bd6776b36b`）
- 方法学：**RV2** —— 一切读数先 `python pycdc.py <pyc> -o <同目录>OK.py` regen，再 verify；`batch` 只吃磁盘既有 `*OK.py`
- 证据前缀：`r5v5fix2_*`（不覆盖既有 `r5v5fix_*` / `r5v5r_*` / `r5v5_*`）

---

## §1 打回项与整改

### 1.1 打回项（REVIEW2 §4.1）

- 位置：`core/cfg/region_ast_generator.py`（B114 第 3 条路径 `_generate_stmts_from_instrs`，for 回边块重建路径的 **else 分支**；REVIEW2 hunk 锚点 `@@ -56272 +56400`，实测当前 HEAD 在 L56434）。
- 机制：新增条件 `len(_gi_store_names)==1 and _gi_store_names[0] != _gi_bound_root` 使**未别名点号 import**（`import os.path` → `IMPORT_NAME 'os.path'` + `STORE_NAME os`，store='os' == `_gi_bound_root`='os'）落入 **else** 分支 `[{name:_n, asname:None}]`，以 store 名 `os` 作 name，**丢失 `.path`**，发射 `import os`（应 `import os.path`）。
- 复现：`test_repros/round5/r5v5r_b114_in_for.pyc`（源 `for i in range(3): import os.path; r.append(os.path)`），修复前产物 `r5v5r_b114_in_forOK.py:6 = import os`。

### 1.2 整改内容（`core/cfg/region_ast_generator.py`，唯一改动文件）

统一判据：**非 from-import 分支的 STORE 名恒等于 `module.split('.')[0]`（顶级绑定名）**，故以首段判定别名；**单 STORE 时 name 一律取完整点号模块名**。

| # | 锚点（整改后） | 归属 | 改动 |
|---|---|---|---|
| 1 | L56434-56448 | B114 path3（for 回边块重建，**打回项**） | else 分支改为：`if len(_gi_store_names)==1: _gi_alias = store if store != _gi_bound_root else None; _aliases=[{name:_gi_imp_module, asname:_gi_alias}]`；多 STORE 保留防御性逐名发射。同步修正注释 ③④⑤（原 ⑤「name 保持完整模块名」与旧 else 不符，现一致） |
| 2 | L11500-11543 | B114 **while 宿主**（`_loop_extract_self_loop_stmts`「普通 import」扫描分支） | 同机制遗漏：原 `store[0] != _imp_module`（与完整点号名比较）→ 幻影 `import os.path as os`。改为与 `_imp_module.split('.')[0]` 比较，单 STORE 时 name 取完整模块名 |
| 3 | L11627-11656 | B114 **while 宿主**（同方法「import 序列终结」STORE 处收口分支） | 同机制遗漏：原 `_sto_n if _sto_n != _module else None` → 同一幻影。改为与 `_module.split('.')[0]` 比较 |

> 三处均为**同一机制**（STORE 名 vs 完整点号名的误判别名），Task 书要求「while 宿主是否同机制，若是则同修」——经核查**是同机制**，已一并修复；while 宿主确由 #2/#3 两条路径处理（#2 前看扫描命中即 `continue`，#3 为 STORE 处收口兜底）。

### 1.3 整改后产物（RV2 实测）

```
r5v5r_b114_in_forOK.py:6   -> for i in range(3):
r5v5r_b114_in_forOK.py:7       import os.path     ✔（原 import os）
r5v5r_b114_in_whileOK.py:7 ->     import os.path   ✔（原 import os.path as os）
```

---

## §2 自测（RV2）结果

### 2.1 打回复现（Task 自测 1）

| 复现 | 修复前 | **整改后** | 判定 |
|---|---|---|---|
| `r5v5r_b114_in_for` | 0/1（`import os`） | **1/1 success** | **转 MATCH** |
| `r5v5r_b114_in_while` | 0/1（幻影 `import os.path as os`） | **1/1 success** | **转 MATCH** |

### 2.2 B114 变体不回退（Task 自测 2）

`r5v5r_b114_{module,multi,realias,from,deep3,tuple,in_func_for,in_try,in_for,in_while}` **全 success**（含之前 1/2 的 `in_func_for` 现亦 success）。
负对照 `_scratch_r5v5/{y*,s*,t*,z*,q*,r*,v*,w*,x*,k*,g1,g3,g5,g6,g7}` 全 success；仅 `g2_while_and3`、`g4_if_while_and` 失败，二者经 `git stash` 基线核实为**既有失败**（B115 三操作数/嵌套，非本批引入，不在官方门禁集）。
核心最小复现 `r5v5_01_module_root`、`r5v5_03_annassign`、`r5v5_08_slice_callsite` 全 success（`r5v5_07/09` 为 REVIEW 阶段已登记既有 failure，与 import 无关）。

### 2.3 34 小测试集（Task 自测 3）

驱动 `test_repros/round5/r5fix2_batch34.py`（regen 全部 34 pyc → batch 拆两半 17+17 → 合并 → compare `baseline/small_test_report.json`）→ 证据 `rounds/round5/r5v5fix2_batch34.json`

```
=== batch34 merged: {'compile_error': 0, 'error': 0, 'failure': 33, 'success': 1} units=1505/1568 base_units=1505/1568 ===
NEWFAIL=0
```

**与基线逐位吻合，NEWFAIL = 0。**

### 2.4 站桩 6 面（Task 自测 4；单进程串行）

驱动 `r5v5fix2_station.py <face>` × 6（串行）+ 对照 `r5v5fix2_compare_regress.py` → 证据 `r5v5fix2_{regress,full}_*.json`、`r5v5fix2_station_regress_compare.json`

| 面 | 既有基线 | **整改后回读** | common | same | improved | **WORSE** |
|---|---|---|---|---|---|---|
| round2 45 文件面 | 234/251 | 234/251 | 45 | 45 | 0 | **0** |
| round2 42 探针面 | 154/189 | 176/196 | 42 | 28 | 14 | **0** |
| round1 哨兵面 | 417/423 | 417/423 | 24 | 24 | 0 | **0** |
| v1 残余面 | 404/446 | 417/446 | 72 | 62 | 10 | **0** |
| 旧规范 round6–10 面 | 658/692 | 664/692 | 59 | 55 | 4 | **0** |
| quotation.pyc 单验 | 152/153 | 152/153 | — | — | — | 持平 |

**六面 WORSE = 0，无任何文件回退**，且改善项与 REVIEW2 阶段读数一致（probe42 +14 / residual +10 / oldface +4）。

### 2.5 B115 / B116 面无新增 failure（Task 自测 4 附带）

- `r5v5r_b115_*`：10 例中 9 success，仅 `r5v5r_b115_while_and3`（三操作数 `while a and b and c`）为**既有失败**（与 REVIEW2 基线逐字一致）。
- `r5v5r_b116_*`：12 例中 10 success，仅 `r5v5r_b116_closure_bare`、`r5v5r_b116_default` 为 REVIEW2 已登记既有 failure；**无误注入新失败**。

---

## §3 IV.2 门禁自检（Task 自测 5）

| 项 | 方法 | 结果 |
|---|---|---|
| I.4 判据白名单 | 通读 3 处改动 | 判据仅取指令 `oparg`/`argval`（`IMPORT_NAME`/`STORE_*`），无 name 白名单、无 `start_offset` 常数比较、无跨层 `entry in blocks` |
| 新增 `self.` 跨方法状态 | 通读 diff | **无**；新增标识符 `_gi_bound_root/_gi_alias/_sl_bound_root/_sl_alias` 全为方法内局部 |
| 硬编码深度上限 / 少发射换绿 | 通读 diff | **无** |
| I.5 七前缀方法名 | `grep 'def (_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)' core/cfg` | 仅 2 命中，均历史存量（`region_ast_generator.py:20096 _merge_block_is_then_exclusive`、`:41197 _merge_block_is_loop_back_edge`，round4 已登记）；本批新增标识符无一命中 |
| BOM（单头） | 字节级读 | `region_ast_generator.py` BOM 计数 = **1**，头 3 字节 `efbbbf` |
| 注释 I.7 六项 + C1/C2/C3 | 通读 3 处 | 3 处均含 ①②③④⑤⑥ + C1/C2/C3；**path3 注释 ⑤ 已与真实 else 行为对齐**（原 REVIEW2 指出的失真已消除） |

改动范围：`git diff --stat -- core/` = 仅 `core/cfg/region_ast_generator.py`（+43/-12，注释扩写后行数略增），**无其他 core 文件改动**。

---

## §4 残余登记（非阻断，与整改无关）

1. `r5v5r_b115_while_and3`（三操作数复合 while）、`r5v5r_b116_closure_bare`（闭包捕获裸注解）、`r5v5r_b116_default`：均为 REVIEW2 阶段已登记的**既有失败**，本批未新增。
2. `_scratch_r5v5/g2_while_and3`、`g4_if_while_and`：既有失败（基线逐字相同），不在门禁集。
3. REVIEW2 §4.2/§4.3 登记项（`posonlyargs` 潜在缺口、闭包裸注解、注解硬编码 `Name('str')`）**行为未变**，本轮未涉及。

---

## §5 结论

- **打回项 B114 path3 else 分支：已修，`r5v5r_b114_in_for` 转 MATCH。**
- **while 宿主 `r5v5r_b114_in_while`：同机制，已一并修复（`_loop_extract_self_loop_stmts` 两条收口路径），转 MATCH。**
- 34 集 NEWFAIL = 0；站桩 6 面 WORSE = 0；B115/B116 面无新增 failure；IV.2 自检全通过。
- 无新增残余；未 `git add` / `commit`。

## §6 证据清单（`r5v5fix2_*`）

- `rounds/round5/r5v5fix2_batch34.json`（34 集 merged + NEWFAIL）
- `rounds/round5/r5v5fix2_station_regress_compare.json`（6 面逐文件 WORSE 对照）
- `rounds/round5/r5v5fix2_regress_{round2face,probe42}.json`、`r5v5fix2_full_{round1face,residual_a,residual_b,oldface_a,oldface_b}.json`、`r5v5fix2_quotation.json`
- 驱动脚本：`rounds/round5/r5v5fix2_station.py`、`r5v5fix2_compare_regress.py`；`test_repros/round5/r5fix2_batch34.py`