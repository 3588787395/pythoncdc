# Round 4 独立对抗复核（Task 4.3）—— 修复批次 `fa9778a5` 复核报告

> 角色：复核人（只读审计 + 独立复跑 + 新变体攻击）。**禁止改 `core/`、禁手改 `*OK.py`、禁 git commit**——本报告期间 `core/` 零改动、零提交。
> 被复核对象：评审批次 `9836400d` → 修复批次 `fa9778a5`（HEAD）。审计命令 `git diff 9836400d fa9778a5 -- core/`：3 文件、+294/−35
> （`region_ast_generator.py` +230、`region_analyzer.py` +72、`pattern_parser.py` +27）。
> 口径：一切读数 RV2（先 `python pycdc.py <pyc> -o <同目录>OK.py` 重建，再 `pyc_verify`）。复核人自建驱动 `r4v4r_*`（零覆盖 `r4v4_*` 与 round3 证据）。
> 修复前基线：`git worktree add d:\Temp\r4v4r_base 9836400d`（**只读检出**，未改主树）。

---

## §0 复核人立场

修复工程师自述概览（**不采信，逐条独立验证**）：位1 封闭 B100/B101（`_import_level_from_prefix`，level=0 不变）；位2 封闭 B102（transition 探测走 `conditional_successors` + 去 `range(8)`）、B109（break+尾部 return None 守卫）、B103 部分（守卫极性 + NONE 族）；B113 主张不改（「peephole 扁平化不可逆」）。

---

## §1 逐 hunk 合规审计表

审计方法：`git diff 9836400d fa9778a5` 全文逐 hunk 阅读 + 树内 grep + 字节级 BOM 计数 + `git status --porcelain`。

| 红线（条款） | 扫描方法 | 命中 | 判定 |
|---|---|---|---|
| I.4-① 文件/函数名白名单 | 新增行逐条读 | 0（新增判据全为 opcode/argval/后继集合事实） | **PASS** |
| I.4-② `start_offset` 魔法阈值 | 新增行 grep `start_offset` | 1 处：`region_analyzer.py` B102 `sorted(_probe.conditional_successors, key=lambda s: s.start_offset)`。**用作程序序排序键，非常数阈值比较**；树内既有同型用法 ≥8 处（`region_ast_generator.py:24080/37188/37353/38450…`）。**不构成黑名单命中** | **PASS**（附注） |
| I.4-③ 跨层 `entry in blocks` 反查 | 新增行 | 0（新增集合运算均为**同层**：`_b109_s in body`、`_probe_succ in _probe_visited/visited`、`successors/conditional_successors`） | **PASS** |
| I.4-④ 新增 `self.` 跨方法状态 | 新增行 | 0（全部为局部变量 `_b109_*`/`_probe_*`/`_imp_*`） | **PASS** |
| I.4-⑤ 硬编码深度/计数上限 · 少发射换绿 | 新增行 | **`range(8)` 已删除**，改为 `while _probe_queue` + `visited` 封闭（有限块集保证终止），**无新计数上限**；无「少发射换绿」 | **PASS**（专项核验通过） |
| I.5 七前缀方法（新增） | 新增行 `def (_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)` | 0；新增唯一方法名 `_import_level_from_prefix` 清白 | **PASS** |
| I.7 注释六项模板 + C1/C2/C3 | 4 个改写/新增 docstring（`_extract_imports_from_block_prefix`/`_generate_handler_body_statements`/`_import_level_from_prefix`/`_process_instruction`）逐项核对 | 4/4 齐备 ①算法依据②归约顺序③唯一归属④嵌套处理⑤入口引用语义⑥反编译流程 + C1/C2/C3；inline `[Bxx]` 注释含判据+条款 | **PASS** |
| I.7 注释↔代码行为一致 | 逐条比对注释断言与实现 | 一致（详见 §1.1） | **PASS** |
| BOM 单头（IV.2） | 逐文件首 3 字节 + 全文计数 | `region_ast_generator.py`=`efbbbf`×1；`region_analyzer.py`=`efbbbf`×1；`pattern_parser.py` 无 BOM（与树内既有态一致，非本轮引入） | **PASS** |
| 插桩残留 | 新增行 grep `print(\|pdb\|breakpoint(\|# TODO\|# FIXME\|# DEBUG` | 0 | **PASS** |
| 在途变更（core/） | `git status --porcelain core/` | 空 | **PASS** |
| `*OK.py` 手改 | `git status --porcelain`（全树） | 0 个 tracked `OK.py` 显示 modified；复核人 regen 产物与 `fa9778a5` 提交字节**逐位一致**（见 §2 注） | **PASS** |
| 命令时限 | 全部 ≤300s（站桩分面执行） | — | **PASS** |

### §1.1 注释↔代码一致性专项核验（I.7）

- `_import_level_from_prefix`：注释称「从 IMPORT_NAME 前导回看，跳过 fromlist(tuple/None)，取最近 int」。实现 `for _ins in reversed(prefix): if != 'LOAD_CONST': break; if isinstance(argval,int) and not isinstance(bool): return`。**行为一致**。判据为 opcode+argval 类型结构事实，**纯白名单**（专项核验通过）。
- B102 transition 探测：注释称「只走 `conditional_successors`（=successors−exception_successors，排除异常边）」。实现 `sorted(_probe.conditional_successors,…)`。**一致**（`conditional_successors` 定义于 `basic_block.py:92`）。
- B109：注释称「仅当未命中『有 break 证据 ∧ 尾部 return None 恰为循环正常出口入口块』时标记」。实现 `not (verified_break_blocks and else_blocks[-1] in _b109_exit_entry)`，`_b109_exit_entry` 由 `(condition_block|header)` 的非 body/非 header/非异常后继构成。**一致**。
- pattern_parser 守卫极性：注释称「真值臂终结跳转在 i+1，比较臂在 i+3」`_ge_scan_from = i+1 if is_truthiness else i+3`；NONE 族改写 `Compare(is/is not None)`。**一致**。

---

## §2 独立复跑读数表（含 NEWFAIL 判定）

驱动 `r4v4r_attack.py`（25 自有探针）→ `r4v4r_probe_full.json`；比对器 `r4v4r_newfail.py` → `r4v4r_newfail.json`。
解法：`python py_compile.compile(src,cfile,doraise=True,optimize=0)` 显式落同目录 `.pyc` → `pycdc -o` 重建 → `pyc_verify batch`。

| 探针 | 修复前(9836400d) | 本轮(HEAD) | 逐单元 diff | 判定 |
|---|---|---|---|---|
| c4_02_loop_else | 13/14 | **14/14** | miss=1（`CL.m`）extra=0 | 改善（B109） |
| c4_03_except_star | 11/13 | **12/13** | miss=1（`e01_root`）extra=0 | 改善（B102） |
| c4_04_match_patterns | 8/13 | **10/13** | miss=2（`e07_capture.inner`,`CM.m`）extra=0 | 改善（B103） |
| c4_14_relative_import | **0/0 compile_error** | **5/5 success** | 转 success | 改善（B100） |
| c4_15_star_import | 5/7 | **7/7 success** | miss=2 extra=0 | 改善（B101） |
| n4_05_neg_except_star | 2/3 | **3/3 success** | miss=1 extra=0 | 改善（B102 负对照） |
| c4_08/09/10/12/19/20 | 13/13·11/14·8/13·7/13·27/28·21/24 | **同** | miss=0 extra=0 | 持平（未误伤） |
| c4_01/05/06/07/11/13/16/17/18 | 各自 | **同** | miss=0 extra=0 | 持平 |
| n4_01/02/03/04 | 全 success | **全 success** | miss=0 extra=0 | 持平 |

**NEWFAIL（真实 success→failure）= 0**（`r4v4r_newfail.json.newfail_count=0`）。全部变动均为单侧改善，无任何单元新增失败。
> 注：HEAD 提交的 `c4_14OK.py` 即 `from . import mod`（修复后产物），复核人重跑 regen 后 `git status` 显示 **0 个 tracked OK.py 被 modify** —— 复核产物与 `fa9778a5` 提交**逐位一致**，复现性成立。

---

## §3 站桩回归 6 面（RV2，复核人自跑）

驱动 `r4v4r_station.py` + `r4v4r_compare_regress.py` → `r4v4r_station_regress_compare.json`。

| 面 | 承接基线 | 本轮复跑 | same/improved/**WORSE** | 判定 |
|---|---|---|---|---|
| v2 round2 45 文件面 | 234/251 | **234/251** | 45/0/**0** | 逐位持平 ✓ |
| v2 round2 42 探针面 | 154/189(tail) | **172/196** | 32/10/**0** | 无回退、10 改善 ✓ |
| v2 round1 哨兵面 | 417/423 | **417/423** | 24/0/**0** | 逐位持平 ✓ |
| v1 残余面 | 404/446 | **417/446** | 62/10/**0** | 无回退、10 改善 ✓ |
| 旧规范 round6–10 面 | 658/692 | **664/692** | 55/4/**0** | 无回退、4 改善 ✓ |
| quotation.pyc 单验 | 152/153（唯一失败 `change_his_to_forward`） | **152/153**，失败单元相同 | — | 持平 ✓ |

**站桩总判：6 面 WORSE=0、only_base=0、失败单元无新增。** 与 `9836400d` 时点读数逐位相同（修复未触及站桩面，但零回退门禁成立）。

---

## §4 新变体攻击（HEAD vs 修复前 9836400d）

5 个新探针（`test_repros/round4/r4v4r_*.py`，零覆盖既有文件）；驱动 `r4v4r_variant.py`（两侧各自隔离 tmp regen+verify）→ `r4v4r_variant_results.json` + 4 份 `*_product.txt`。

| 变体探针 | 攻击点 | HEAD | 修复前 | 误伤 | 结论 |
|---|---|---|---|---|---|
| `r4v4r_b100_levels` | 相对导入 level 1/2/3 + handler/finally 体 + module 三元宿主 | **5/5 success** | **0/0 compile_error** | 无 | **B100 封闭（外推成立）** |
| `r4v4r_b101_star` | 交叠 star/non-star/plain + 后随函数 | **6/6 success** | 5/6 | 无 | **B101 封闭（外推成立）** |
| `r4v4r_b102_except` | 1/2/3 handler、普通 except、finally、else+finally、嵌套 | 5/8 | 5/8 | **无** | 存量外推（见 §4.1） |
| `r4v4r_b109_loopelse` | 多宿主 while-else、for-else、非纯 return None、嵌套 | **8/9** | 7/9 | 无 | 修复外推成立；`nested_loop_else` 存量 |
| `r4v4r_b103_guard` | 真值/NONE/比较守卫、真三元/真 if 对照、嵌套 | 5/8 | 5/8 | **无** | 存量外推（见 §4.1） |

### §4.1 双向攻击关键证据（区分误伤 vs 存量）

- **B100 强证据**（`r4v4r_b100_levels_base_product.txt`）：修复前产物 `from  import a`（**非法**）、`from pkg import c`/`from deep.mod import d`（level 2/3 **降为 0**）、handler 体 `from catcher import j`、finally 体 `from fin import k`（level 丢失）；**HEAD 全数还原** `from .`/`from ..`/`from ...`。**level=0 绝对导入（`import os`/`from os import path`）逐位不变**；函数体相对导入（`plain()` 的 `from ..inner import h`）在两侧均正确——**误伤=0**。
- **B101 强证据**（`r4v4r_b101_star_base_product.txt`）：修复前 `from os.path import *`→`import os.path`、`from collections import *`→`import collections`、`from sys import *`→`import sys`（star 全丢）；**HEAD 全数还原**。**non-star（`from json import loads, dumps`、`from math import sqrt`）与 plain（`import os`、`import os.path as op`）逐位不变**——**误伤=0**。
- **B102 存量（非误伤）**：`nested_star`/`normal_finally`/`star_else_finally` 在 HEAD 与修复前**同集合失败**（Different bytecode）；单 `except*`、双/三 `except*`、普通 `except` 均 MATCH。→ B102 fix 修复了 c4_03 的特定子形态（`e01_root`），`except*/else/finally` 与 `try/except/finally` 仍未闭合，属**存量外推**（可续 B102/B108 域）。
- **B109 存量（非误伤）**：`CL2.m`（精确修复形态）由 failed→MATCH；`normal_while`/`for_else_ctrl`/`while_else_not_returnnone` 全 MATCH（**误伤=0**）；`nested_loop_else` 双宿主嵌套仍双失败=存量。
- **B103 存量（非误伤）**：`cmp_guard`/`real_ternary`/`real_if` 全 MATCH；`GT.m`（mapping+真值守卫，等价 c4_04 `CM.m` 但少一中间 case）/`none_guard`（`is None` 支）/`nested_guard` 双侧同失败=存量。→ 守卫极性修复**形状敏感**，未误伤真三元/真 if/比较守卫。

---

## §5 B113 分类复核（「peephole 扁平化不可逆」主张）

**独立判据实验**（`d:\Temp\r4v4r_b113_probe.py`，编译 4 源比对 `<listcomp>` 字节码）：

| 源 | 与原始字节码 |
|---|---|
| `[(a,b) for x in xs for a in [x] for b in [x]]`（原源） | = 原始（定义）|
| `[(a,b) for x in xs for a in (x,) for b in (x,)]` | **== 原始**（`[x]`≡`(x,)`，peephole 均扁平为 `LOAD x; STORE a`）|
| `[(a,b) for x in xs]`（**现反编译产物**） | **≠ 原始**（`LOAD_GLOBAL a/b`）|
| `[(x,x) for x in xs]` | ≠ 原始 |

**结论**：
1. 「源形不可唯一还原」= **成立**——`for a in [x]` 与 `for a in (x,)` 编译到**同一**扁平字节码 `LOAD x; STORE a`，故源级保真不可逆。
2. 「不可修复/证伪」= **不成立**——判据是**字节等价**而非源形保真；存在**等价源**（`(x,)` 形）可**逐字节复现**原始字节码。现产物 `[(a,b) for x in xs]` 引用未绑定名 a/b、编译后字节码不同，是**真实能力缺口**。
3. **裁定：B113 维持「破口」**（驳回「证伪降级」）。缺口机制 = 推导式体内未识别扁平子句 `LOAD <iter>; STORE <tgt>` 并重构为等价 `for <tgt> in (<iter>,)`；落 `comprehension_generator.py` 子句块归约。c4_18（30/30）不含单元素 list 字面量迭代源，故未暴露此缺口——**B113 非探针伪差**。

---

## §6 终审结论

**判定：通过（不被打回）。**

零容忍门禁逐项：
- I.4 黑名单五项：**0 命中**（② 的 `start_offset` 为既有同型排序键，非阈值）。PASS。
- 注释↔代码行为不一致（I.7）：**0**。PASS。
- 真实 success→failure 回退：**NEWFAIL=0**。PASS。
- 站桩 WORSE：**0**。PASS。
- 少发射换绿：**0**（`range(8)` 实为删除）。PASS。

自述逐条验证：位1 B100/B101 **确认成立且外推无界**；位2 B102/B109 **确认成立**、B103 **部分成立（形状敏感）**；「去 `range(8)` 上限」**确认**；B113「不改」的**理由被驳回**（维持破口，见 §5）。
**遗留（非打回项，供后续轮次）**：B102 `except*/else/finally`、B103 mapping/`is None`/嵌套守卫、B109 双宿主嵌套、B113 等价重构、B108 `try/except/finally` 存量。

### II.7 十三条误解自查（复核人自身）

循环论证分母（用外部 ruler）/有过就算/语料证据口径/无限分母/节点词汇当完备/浅层测试当无感证明/门禁读数当完备性/顶层构造粗清单/识别率当完备性/维度互替/改工具不改方法 —— 均未犯（读数一律 pylingual 字节等价单元级，探针含深嵌套+浅收缩双向）。
**错误检测标准**：B102 分析只用 3.11 标记 `CHECK_EG_MATCH`/`PREP_RERAISE_STAR`/`is_except_star`，未用 3.12 `PRELOAD_RERAISE` —— 合规。
**语料上限当能力上限**：#12 自查中**主动拒绝**将「源形不可还原」当作「能力上限」（§5）——未犯。

---

## §7 移交主代理验证清单

1. 复核读数 JSON：`rounds/round4/r4v4r_probe_full.json`、`r4v4r_newfail.json`、`r4v4r_variant_results.json`、`r4v4r_station_regress_compare.json`（+ `r4v4r_full_*`/`r4v4r_regress_*`/`r4v4r_quotation.json`）。
2. 变体探针与产物：`test_repros/round4/r4v4r_b100_levels.py`、`r4v4r_b101_star.py`、`r4v4r_b102_except.py`、`r4v4r_b109_loopelse.py`、`r4v4r_b103_guard.py`；`rounds/round4/r4v4r_b100_levels_{head,base}_product.txt`、`r4v4r_b101_star_{head,base}_product.txt`。
3. 驱动：`r4v4r_attack.py`、`r4v4r_newfail.py`、`r4v4r_station.py`、`r4v4r_compare_regress.py`、`r4v4r_variant.py`。
4. 复核起点/基线：HEAD=`fa9778a5`；修复前 worktree=`d:\Temp\r4v4r_base`（9836400d）。可复跑命令见各脚本 docstring。
5. 建议：B113 若要在台账「确证」，须以**等价源**为目标而非源形保真；B102/B103 遗留域建议下一轮专项派发。

**（本复核未改 `core/`、未手改任何 `*OK.py`、未 git commit；`git worktree` 为只读检出。）**