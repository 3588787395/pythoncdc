# Round 4 Task 4.2 · 修复交接单（位 1：生成/发射层）—— FIX_G.md

> 修复工程师：位 1（`core/cfg/region_ast_generator.py`，唯一改动文件）。
> 理论基准：`spec.md`（I.1 四原则 / I.3 C1-C2-C3 / I.4 判据白名单 / I.5 禁止事项 / I.6 落地声明 / I.7 注释六项模板）。
> 破口登记：`rounds/round4/REVIEW.md` §4.1（B100–B113）。
> 口径：一切读数以 RV2 重建（`python pycdc.py <pyc> -o <同目录>OK.py`）后 `python scripts/pyc_verify.py single <pyc>` 为准。
> **代码已落地**；落地标记 grep：`[B100]` 命中 **6** 处、`[B101]` 命中 **4** 处（见 §3）。

---

## 0 结论摘要

| 破口 | 形态 | 前读数 | 后读数 | 判定 |
|---|---|---|---|---|
| **B100** | relative_import 层级丢失 → 产物非法 | `c4_14` **compile_error 0/0** | **success 5/5** | **已封闭** |
| **B101** | star_import 丢失 | `c4_15` failure **5/7** | **success 7/7** | **已封闭** |

**本席位交付 = B100 + B101 全封闭**，且经**宿主矩阵**（模块根 / 函数 / 类体 / 方法 / for / while / with / try-finally / if / except-handler / 嵌套 for / 嵌套 with / try-finally copy / 解包与多目标子路由 / TernaryRegion 入口）交叉验证 **host 无关性（C1）**。其余 B104–B112 见 §5 残留与原因。

---

## 1 B100 · relative_import 层级丢失

### 1.1 判据（I.4 白名单）
`IMPORT_NAME` **前导 `LOAD_CONST` 的 int argval = level**（编译器写入的指令常量/`oparg` 结构事实）。回看时跳过 `fromlist`（tuple）/`None` 常量，取最近 int。**禁用**文件名/函数名白名单、`start_offset` 魔数、跨层 `X.entry in Y.blocks`、新增 `self` 跨方法状态、硬编码深度上限。

### 1.2 机制（为何是产物非法）
CPython 3.11 编译 `from . import m` / `from .sub import n` / `from ..pkg import o` 时，`IMPORT_NAME` 前压入 `LOAD_CONST(level:int)` + `LOAD_CONST(fromlist)`。原生成层多处 import 归约入口**未读取 level**，`module` 名丢失前缀 → 相对导入降级为绝对，且 `from . import m` 的 `IMPORT_NAME.argval` 为空串 → 发射 `from  import m`（**非法语法 → 整文件 compile_error**）。违反 C1（import 区域未消费 level 结构事实）+ I.1 原则 4（入口引用语义）。

### 1.3 算法修复（封闭守卫，非个案补丁）
新增单一归约入口参数读取器 **`_import_level_from_prefix(prefix_instrs) -> int`**（`region_ast_generator.py:55590` 区），在**每一条实际到达的 import 归约入口**统一调用，`level>0` 时 `module = ('.'*level) + module`：
- `level=0` → module 名逐位不变（**C2 黑箱组合**成立）。
- 相对层级显式封闭进 module 名字符串 → 经 `ast_converter`→`code_generator`（AST 路径丢弃 `ImportFrom.level`）仍能正确发射（**C3 守卫封闭**：不依赖不可改的 `ast_generator_v2.py`）。

### 1.4 改动 hunk（`core/cfg/region_ast_generator.py`）
| 站点（方法 / 归约入口） | 行 | 说明 |
|---|---|---|
| `_import_level_from_prefix`（新增工具，I.7 六项齐全） | 55561–55591 | 从 `IMPORT_NAME` 前导指令取 level |
| `_process_instruction`（`IMPORT_NAME` 分支） | 55611–55622 | 模块根 / 条件前缀主路径 |
| `_extract_imports_from_block_prefix`（TernaryRegion 入口前导扫描） | 599–603 | 模块根 + 末尾三元（原 `from  import m` 站点） |
| `_generate_handler_body_statements`（R64 except/finally 副本体） | 32060–32073 | finally/except 副本体 import |
| `_build_statements_from_instructions`（import 状态机，带回溯 `_imp_module_name`） | 32331–32341 / 32459–32441… | 解包 / 多目标 / 链式赋值子路由及多处 flush 站点（6 处 `_imp_name_instr.argval` → `_imp_module_name`） |
| `_generate_block_statements_body`（`_ua_` 解包子路由） | 53414–53423 | `_ua_mod`，覆盖 ImportFrom 与 Import 两分支 |

### 1.5 复现读数（前 → 后，RV2）
| 探针 | 覆盖 | 前 | 后 |
|---|---|---|---|
| `c4_14_relative_import`（登记探针） | `from . import mod`、`from .sub import`、`from ..pkg import` | **compile_error 0/0** | **success 5/5** |
| `_scratch_m4/g4_import_hosts` | 模块根/函数/类体/方法/for/while/with/try-finally/if | — | success 5/5 |
| `_scratch_m4/g4_import_hosts2` | except-handler/嵌套 for/方法内 try-finally/嵌套 with + 模块根相对导入＋末尾三元 | **compile_error 0/0** | **success 7/7** |
| `_scratch_m4/g4_import_hosts3` | 解包/多目标/链式赋值子路由（`a,b=…`、`p,q=xs`、嵌套解包、`a,*b`、`a=b=5`） | **compile_error 0/0** | **success 7/7** |
| `_scratch_m4/g4_fin_bisect` | try/finally finally 副本体 import（a/b/c/d 四形态） | failure 4/5 | **success 5/5** |

---

## 2 B101 · star_import 丢失

### 2.1 判据（I.4 白名单）
`IMPORT_NAME` **后继 `IMPORT_STAR`**（块内 opcode 族事实）。命中即统一产出 `ImportFrom(names=[{'name':'*'}])`。

### 2.2 机制
`from os.path import *` 的 `IMPORT_NAME` 后继为 `IMPORT_STAR`（无 `IMPORT_FROM`/`STORE_*`）。原模块级直线路径 / TernaryRegion 前导扫描路径未识别 → 降级为普通 `Import(module)`（`import os.path`），star 名与后续 `LOAD_NAME` 自由名全丢（`Missing bytecode`）。违反 C1 + I.1 原则 4。

### 2.3 算法修复
在 import 归约入口增设 `IMPORT_NAME → IMPORT_STAR` 显式判据，与 from-import 共用同一归约入口，统一产出 `ImportFrom(names=[{'name':'*'}])`；`_extract_imports_from_block_prefix` 增 `IMPORT_STAR` 跳过分支（避免其被当作块尾非 import 指令而中断前导扫描，连带丢弃后续 import）。

### 2.4 改动 hunk
| 站点 | 行 | 说明 |
|---|---|---|
| `_process_instruction` | 55626–55634 | 主归约入口建 star 节点 |
| `_extract_imports_from_block_prefix` | 610–625 / 721–723 | TernaryRegion 入口建 star + `IMPORT_STAR` 跳过 |
| `generate()` 内联循环 | 1166–1183 | star 序列被 `_process_instruction` 一次性认领，清空缓冲 |
| `_if_extract_cond_instructions` 内联循环 | 17166–17170 | 条件前缀块路径 |

### 2.5 复现读数（前 → 后）
| 探针 | 前 | 后 |
|---|---|---|
| `c4_15_star_import`（登记探针） | failure **5/7** | **success 7/7** |
| `_scratch_m4/g4_star_hosts` | — | success 5/5 |
| `_scratch_m4/g4_star_hosts2`（模块级多 star + 后续普通 import + 末尾三元） | failure 2/3 | **success 3/3** |

---

## 3 落地标记 grep（I.6 复审入口）
```
[B100] × 6  → :599 、:32092 、:32331 、:32459 、:53414 、:55704
[B101] × 4  → :610 、:1166 、:17166 、:55716
```
`git status --porcelain core/` = ` M core/cfg/region_ast_generator.py`（唯一改动；**未**改 `code_generator.py`；无 `git commit`）。

---

## 4 I.7 注释六项 + C 条款自检
触及方法 docstring 均已按 I.7 六项模板（①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程）写全并注明 C1/C2/C3：
- `_import_level_from_prefix`（新方法，含六项 + C1/C2/C3）
- `_process_instruction`（六项 + C1/C2/C3）
- `_extract_imports_from_block_prefix`（重写为六项 + C1/C2/C3）
- `_generate_handler_body_statements`（重写为六项 + C1/C2/C3，保留原输入契约/字节码一致性约束）
- `_generate_block_statements_body`（已有六项 + C1/C2/C3，本次仅在其 `_ua_` 子路由加 level，无需改 docstring）
- `_build_statements_from_instructions`（非 `_generate_*`；以行内 `[B100]` 注释显式说明判据、归属、C 条款，注释与代码行为一致）

---

## 5 残留与原因（未封闭，据实登记）

| 破口 | 状态 | 原因 |
|---|---|---|
| **B104 / B105 / B107 / B110 / B111 / B112** | 未封闭 | 各属独立值/结构消费链与宿主控制流机理（链式比较末操作数、NamedExpr 消费位、链式赋值目标值、with 出口、局部类方法装饰器、async yield/推导式）。均需在各自归约链深处新增守卫并逐宿主回归，超出本轮位 1 已充分验证的 import 保真域；为避免在 5.8 万行关键文件中引入未验证回退，据实留待后续轮次。 |
| **B106**（star_args 重排） | 未封闭（**根因不在可改文件**） | `f(*x,1)`→`f(1,*(x))` 的顺序在**表达式重建期**已固化：`BUILD_LIST/LIST_EXTEND/LIST_APPEND/LIST_TO_TUPLE/CALL_FUNCTION_EX` 的处理位于 `core/cfg/ast_generator_v2.py`（不可改）。`code_generator.py` 仅按既有 AST 发射，无法在此纠正顺序。 |
| **B108**（finally `del`→`pass`） | 未封闭 | `DELETE_FAST` 在 finally 副本体未映射为 `Delete`；且 as-var 清理同用 `DELETE_FAST`（同名判据），新增 `del` 识别与既有 as-var 清理守卫存在冲突面，需专项设计与回归。 |

### 5.1 新发现（**非 B100，import 无关，既有缺陷**）
`_scratch_m4/g4_imp_unp_abs4`：模块根含 `UNPACK_EX`（`c, *d = [...]`）时，其**之前的语句被整体丢弃**（含**绝对** `import sys`）。对照 `g4_imp_unp_abs3`（`UNPACK_SEQUENCE`）success 3/3 → 触发条件为模块根 `UNPACK_EX`。因绝对 import 同样丢失，**判定与本轮 B100/B101 无关**，属既有模块根多语句归约缺陷，未登记为本轮 B100 破口，建议后续轮次立项。

---

## 6 IV.2 门禁自检（全过）
| 项 | 方法 | 结果 |
|---|---|---|
| py_compile | `python -m py_compile core/cfg/region_ast_generator.py` | **OK** |
| BOM 单头 | 首 3 字节 + 全文计数 | `efbbbf` / count=1 → **PASS** |
| I.4 新增违规 | 名称白名单 / `start_offset` 魔数 / 跨层 `X.entry in Y.blocks` / 新增 `self` 跨方法状态 / 硬编码深度·计数 / 少发射换绿 | **新增 0** |
| I.5 禁止前缀 | `def (_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)` | **新增 0**（树内存量 2 处历史名，非本轮） |
| 插桩残留 | `print(|pdb|breakpoint(|TODO|FIXME|DEBUG` | **新增 0** |
| `*OK.py` 手改 | 仅由 RV2 工具重建，无手改 | **PASS** |
| 未改禁改文件 | `region_analyzer.py` / `pattern_parser.py` / `comprehension_generator.py` / `ast_generator_v2.py` / `code_generator.py` | **未改** |
| 未提交 | `git commit` | **未执行** |

### 6.1 无回退验证（本轮自测探针）
`c4_01` 14/14、`c4_05` 12/14、`c4_06` 12/14、`c4_07` 10/14、`c4_08` 13/13、`c4_09` 11/14、`c4_10` 8/13、`c4_11` 14/14、`c4_12` 7/13、`c4_13` 13/13、`c4_16` 21/21、`c4_17` 12/12、`c4_19` 27/28、`c4_20` 21/24 —— **与 REVIEW §3 基线逐位一致（WORSE=0）**；负对照 `n4_01` 5/5、`n4_02` 12/12、`n4_03` 5/5、`n4_04` 8/8、`n4_05` 2/3 —— 逐位一致。本轮新 fixes 的 import 域探针（§1.5/§2.5）全部转绿。

---

## 7 探针清单（`test_repros/round4/_scratch_m4/`，`g4_*` 前缀，为本席交付证据）
保留：`g4_import_hosts(.py/.pyc/OK.py)`、`g4_import_hosts2`、`g4_import_hosts3`、`g4_star_hosts`、`g4_star_hosts2`、`g4_fin_bisect`、`g4_imp_unp_abs4`（§5.1 证据）。
临时诊断脚本（`g4_diag_*`、`g4_while_*`、`g4_fin_host`、`g4_imp_unp_abs/star/abs3`、`g4_star_hosts3`）已清理。