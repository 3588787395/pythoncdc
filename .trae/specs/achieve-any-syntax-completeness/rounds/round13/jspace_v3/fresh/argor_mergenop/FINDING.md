# FINDING — rr-v5r114 [v114-ARGOR] + [v114-MERGENOP]：REAL46-031（packaging/version.py）整案闭合

## 0. 结论速览

- REAL46-031（`D:\Python\Lib\site-packages\packaging\version.cpython-311.pyc`，sha
  `a0c62d37…`）权威判官 `semantic_diff.compare_case`：DIFFERENT（2 R7）→ **EQUAL
  （diffs=[]）**。
- 本轮闭合两个根因族（均在 `core/cfg/region_ast_generator.py`，只增不破）：
  1. **[v114-ARGOR]**（R67 值目标路径调用续接拼接）——判官盲区内、上轮登记的真实
     语义缺陷：`self._post = _parse_letter_version(a, b or c)` 降为
     `self._post = b or c`（归一化调用全部旁路）。
  2. **[v114-MERGENOP]**（三元 merge 块孤立常量语句 NOP 占位）——判官可见的唯一
     R7：模块级 `VERSION_PATTERN = <三元>` 后随属性 docstring 惯用法（裸字符串
     表达式语句），重编译短 2 字节 NOP。
- 判官盲区核查（68 个嵌套 code object 递归字段比对）：v113 产品 3 差异 → v114
  产品仅剩 1（`/Version/__setstate__` co_code 818 vs 816，**预存在**、新登记、
  与本轮两修复无关，见 §5）。

## 1. 前置事实（判官与字段级基线）

- 修复前（rr-v5r113 HEAD `65606ef3`）单案权威判官（`sd_v113_baseline.py` →
  `semantic_REAL46-031_v113_baseline.json`）：`DIFFERENT`，2 diff：
  `$.metadata.code.co_code.len` 1094 vs 1092、`$.metadata.code.co_code.sha256`。
  即全部差异集中在**模块级** code object（判官 R7 不递归类内 layer-2）。
- v113 产品字段级递归比对（`fieldcheck_031.py`，68 code objects）：3 个差异——
  `<module>`（1094 vs 1092）、`Version.__init__`（1266 vs 1200，缺 66 字节）、
  `Version.__setstate__`（818 vs 816，缺 2 字节）。

## 2. 根因 1：[v114-MERGENOP] 三元 merge 块孤立常量语句 NOP 丢失（判官可见 R7）

### 2.1 差异定位

- 模块级逐指令比对（`fieldcmp2.py` 思路）：原件 offset 778 有 `NOP`（
  `starts_line=241`），产品缺失，其后指令全体 −2 字节。
- 源 241–255 行是 `VERSION_PATTERN = (...)` 赋值后的**裸字符串表达式语句**
  （属性 docstring 惯用法）。CPython 3.11 `compiler_visit_stmt_expr` 对 Constant
  语句直接发射行标记 NOP 且不驻留常量（[Round 33] 已判定的机制）；实测
  `pass`/裸字符串在该位置均恰编译 1 条 NOP、零常量、零跳转（`nopform.py`）。

### 2.2 机制链（逐层实证）

- 简单形复现（`repro2_nop.py`：普通赋值 + 裸字符串）产品正确渲染 `""` 占位、
  重编译逐字节相等——孤立 NOP 的既有消费点是 `_build_statements_from_instructions`
  的 [Round 33] 分支（`_rag_is_orphan_nop_statement`，42263/41047/70157 三站点）。
- 三元形复现（`repro4_noptern.py`：前置 if 边界 + 三元赋值 + 裸字符串）**语句
  整体丢失**（无占位）。
- 区域归属探针（`probe_mergenop_regions.py`）：NOP 所在块 @194 =
  TernaryRegion（entry=50，value_target=`VERSION_PATTERN`）的 **merge_block**，
  无其它区域共享入口 → 走 `_generate_ternary` value_target 路径的 merge 剩余
  语句处理。
- 根因位点：`_generate_ternary` 尾部 merge 剩余重建的 `merge_all` 头部噪声过滤
  （`RESUME/NOP/CACHE/PUSH_NULL`）把 NOP 连同其语句位置一并剔除，
  `_build_statements_from_instructions` 的 [Round 33] 孤立 NOP 分支**永不触达**。
  通用块走查路径（BSS/BSI）与 boolop R78 路径的重建窗口含 STORE 边界指令，
  孤立 NOP 由既有分支处理；本位点缺同款消费即根因（原则 2：语句边界事实归
  语句重建者发射）。
- boolop 路径对照（`repro5_boolop.py`）：`VAL = _X or _Y` + 裸字符串 → 产品渲染
  `if 1: OTHER = 'z'`（[x01-V5R03] 折叠行头发射），重编译**逐字节相等**——
  boolop 路径非缺陷，不修（C3）。

### 2.3 修复（[v114-MERGENOP]，只增不破）

- 新辅助 `_v114_merge_orphan_nop_segments(merge_block, store_instr,
  non_noise_remaining)`：按 merge 块**原始指令序**把 STORE 之后窗口切分为
  「语句段 / 孤立 NOP」交错序列；每条 NOP 以全块原始指令为上下文跑既有
  `_rag_is_orphan_nop_statement`（prev=STORE 语句边界、next=下一条语句开始，
  判据与 Round 33 完全同源）；语句段去噪后交同一
  `_build_statements_from_instructions` 重建，仅末段做 `_b89_trim_trailing_at_
  cond_jump` 修剪与尾部隐式 return None 剥离（与既有路径同款）。
- 接入点：value_target 路径 merge 剩余 `else` 分支（"有实际后续语句"）——
  **无孤立 NOP（或窗口定位失败）时返回 None 逐位走既有路径**（C2/C3）；
  占位语句形与 Round 33 三站点逐字同（`Expr(Constant(''))` + `_nop_placeholder`）。

## 3. 根因 2：[v114-ARGOR] R67 值目标路径调用续接拼接（判官盲区，上轮登记缺陷）

### 3.1 差异定位

- `Version.__init__` 逐指令比对（difflib 对齐）：原件 `self._post =
  _parse_letter_version(match.group("post_l"), match.group("post_n1") or
  match.group("post_n2"))`（源 444 行），产品缺 `LOAD_GLOBAL
  _parse_letter_version`（链首块）与 `PRECALL 2 / CALL 2`（merge 块）——调用
  前后缀双蒸发，只剩 `self._post = match.group('post_n1') or
  match.group('post_n2')`。最小复现 `repro1_postcall.py` 精确复现。

### 3.2 机制链（逐层实证）

- 块结构：链首块 A（878–970：`LOAD_GLOBAL _parse_letter_version` + 第一实参
  post_l 装载 + or 链首操作数 post_n1 装载，尾 `JUMP_IF_TRUE_OR_POP`）、成员块
  B（post_n2）、merge 块 C（1012：`PRECALL 2; CALL 2; LOAD_FAST self;
  STORE_ATTR _post` 及后续 `_dev` 语句）。
- BoolOpRegion：entry=0/A，merge=C，value_target=None（探针
  `probe_argor_splice.py`）→ 落 R67 分支（`not region.value_target` 且 merge
  含 STORE_ATTR）。
- 根因位点：R67 发射 `_obj_r67 = reconstruct(_mb_r67[:_sa_r67])`——把 merge
  前缀 `[PRECALL 2, CALL 2, LOAD_FAST self]` **整段当赋值目标重建**（reconstruct
  只取栈顶 → `self`），调用后缀蒸发、链首块调用前缀（函数 + 先行实参）无人
  消费，`value=boolop_expr` → 赋值值退化为裸 or 链。
- 姊妹域边界：`_v105_try_kwarg_chain_continuation` 守卫①显式排除「merge 块含
  STORE」形态（注释：既有 value_target 路径域）；[R02] POP_TOP-before-STORE_ATTR
  分支要求 merge 前缀含 POP_TOP（本形无）——两既有守卫均不覆盖本形。
- 简单名目标形（`post = _parse_letter_version(a, b or c)`，`repro6_sib.py`）：
  HEAD 下**本已正确**（analyzer 设 value_target 走另一路径）——控制案。

### 3.3 修复（[v114-ARGOR]，只增不破）

- R67 发射前插调用续接拼接分支。识别条件全同层结构事实：
  ①merge 前缀（`_mb_r67[:_sa_r67]`）含 `PRECALL/CALL`；
  ②op_chain 非空，链首块前缀（`identify_block_prefix_instructions` 后剥最后
  STORE——[R02]/[P2-1]/[B56] 同款消费契约）reconstruct 得非空残留栈，栈顶即
  or 链首操作数（已被 boolop_expr 吸收），替换为完整 boolop 作 initial_stack；
  ③merge 前缀以该栈重建得 ≥2 条残留——栈顶 ∈ {Name, Attribute, Subscript}
  （目标对象）、次顶为非语句节点（完整调用表达式）。
- 归约：`Assign(targets=[Attribute(栈顶, attr)], value=次顶)`——R78 剩余语句
  处理（`_dev` 语句/后续）与块归属登记**逐字不动**；任一校验失败逐位落回
  既有 R67 发射（C3，`value=boolop_expr` 旧行为保留）。
- 归一化验证：拼接干跑（probe）栈 = [前序语句 Assign 簿记, 完整
  `_parse_letter_version(post_l, post_n1 or post_n2)` Call, `self`]——次顶/栈顶
  恰为 value/target。

## 4. 验证（全实测）

### 4.1 变体矩阵（`matrix_v5r114.py` 12 案，A/B 文件交换 HEAD `65606ef3` vs v114）

| 案 | 形 | HEAD | v114 | 判定 |
|---|---|---|---|---|
| E1_argor_method | 方法 `self._post = f(a, b or c)`（REAL46-031 精确形） | TEXT-DIFF | 重编译 BYTE-EQUAL | PASS |
| E2_mergenop_ternary | 三元赋值 + 裸字符串（REAL46-031 精确形） | TEXT-DIFF | 重编译 BYTE-EQUAL | PASS |
| E4_argor_single_arg | `self.x = f(v or "d")` 单实参 | TEXT-DIFF | 重编译 BYTE-EQUAL | PASS |
| E8_argor_postfix_binop | `self.x = f(v or "d") + 1` 后缀二元 | TEXT-DIFF | 重编译 BYTE-EQUAL | PASS |
| E3_argor_simplename | 简单名目标 `post = f(a, b or c)` | HEAD 本已正确 | 逐字节同 + BYTE-EQUAL | PASS（控制） |
| E7_mergenop_before_for | 三元 + 裸字符串 + for | HEAD 本已正确 | 逐字节同 + BYTE-EQUAL | PASS（控制） |
| C1_no_ternary_orphan | 普通赋值 + 裸字符串（BSI Round 33 域） | — | 逐字节同 + BYTE-EQUAL | PASS |
| C2_boolop_orphan | or 赋值 + 裸字符串（[x01-V5R03] `if 1:` 域） | — | 逐字节同 + BYTE-EQUAL | PASS |
| C3_ternary_no_orphan | 三元 + 普通后续语句 | — | 逐字节同 + BYTE-EQUAL | PASS |
| C4_r67_plain | `self.x = v or d`（R67 既有形） | — | 逐字节同 + BYTE-EQUAL | PASS |
| C5_no_boolop_call | 无 or 的调用赋值 | — | 逐字节同 + BYTE-EQUAL | PASS |
| E6_mergenop_two_orphans | **两条相邻**裸字符串 | — | v114==HEAD 逐字节同；重编译仍缺 2 NOP | UNCLAIMED（既有 [Round 33] 相邻 NOP 回归守卫排除域——类体行锚 NOP 对与连续常量语句 NOP 对同形不可分；两版逐字节同零漂移，如实登记） |

### 4.2 REAL46-031 单案权威判官 + 判官盲区核查

- `sd_v114_031.py` → `semantic_REAL46-031_v114.json`：**EQUAL（diffs=[]）**
  （此前 DIFFERENT 2 R7 全消）。
- `fieldcheck_031.py`（68 code objects 递归 co_code/exceptiontable/names/
  varnames/argcount/flags/consts 按名归一）：v114 仅剩
  `/Version/__setstate__` co_code 818 vs 816（见 §5）；`<module>` 与
  `Version.__init__` 全部闭合。

### 4.3 A/B 回归电池（`r114_regress.py`，226 案）

- 案源：r110 的 169 案 + v111 15 案 + v112 15 案 + v113 15 案 + 本轮 12 案。
- 结果：**TEXT-DIFF 4 / 226**，恰为本轮 4 个功效案（E1/E2/E4/E8）且重编译签名
  全部 BYTE-EQUAL；其余 222 案 TEXT-SAME。
- R110 案 169：TEXT 状态一致 168、签名一致 168——唯一差异 mc1（r110 轮功效案，
  两侧已同持修复 → TEXT-SAME，历史功效案正常归一，签名 BYTE-EQUAL 前后一致）；
  另 3 条为语料替代案签名注记差（pd8_prod/pd10_prod/pe8_target，TEXT-SAME 状态
  一致）。
- 既有登记差 10 案（w28_shapes w2/w3、na5、pe8、pe8_target、nb2、ca6、ca13、
  ca15、cb5、pd8_prod）：**ALL SAME-SIGNATURE**（与 r110 记录逐字节同签名）。

### 4.4 pytest 7 套件 + 比较器冻结

- `test_algorithm_correctness / test_boundary_cases / test_complete_syntax_coverage
  / test_control_flow_completeness_matrix / test_core_functional /
  test_deep_nesting_pressure / test_product_freshness`：
  **3 failed / 277 passed / 2 xpassed**——与 v113 基线逐项一致（2 冻结对
  `TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、
  `TestBoundaryConditions::test_BOUNDARY_02_large_function`；第 3 failed
  `TestProductFreshness` 在位产物预存在陈旧：3 个 stale 条目行数/字节比与
  v113 日志逐字相同（283 行 26229/26134、71 行 13299/13537、1016 行
  61506/61895），非本轮引入）。零新增失败。
- `scripts/pyc_verify.py` SHA256 `FE1902A90CEBD4A15925F7C34924269FD324418B9FB
  50B43A21BD4DBF38DDFF4` 冻结一致；`tools/completeness/semantic_diff.py`
  SHA256 `DBCB1E24…` 与基线 judge_sha256 一致；`git diff -- tests/
  scripts/pyc_verify.py tools/completeness/semantic_diff.py
  core/cfg/region_analyzer.py` 为空；已跟踪改动仅
  `M core/cfg/region_ast_generator.py`（`+190/−13`，标记 `[v114-ARGOR]`、
  `[v114-MERGENOP]`）。

## 5. 判官盲区剩余登记（下一轮候选，未修）

- `/Version/__setstate__` co_code 818 vs 816（**预存在**：v113 产品同差，本轮
  A/B 零漂移）：源 794 行 `if len(state) == 6:` 臂尾的**裸 `return`**（内联
  `LOAD_CONST None + RETURN_VALUE`）被反编译器省略，第二 `if len(state) == 2:`
  被合并为 `elif`（R1–R6 语义等价；字节差 = 显式 return 4 字节 vs JUMP_FORWARD
  2 字节）。疾病域 = if 臂尾裸 return 省略 + if-elif 合并族，与 ARGOR/MERGENOP
  正交，登记下一轮。
- E6 相邻 NOP 对（两条连续裸字符串语句）：[Round 33] 相邻 NOP 回归守卫
  （类体行锚 NOP 对）排除域，两版逐字节同，未领。

## 6. 证据文件清单

| 文件 | 内容 |
|---|---|
| `fix_patch_v5r114.diff` | 唯一源码改动（region_ast_generator.py） |
| `matrix_v5r114.py` | 12 案案源（与回归电池同源） |
| `r114_regress.py` + `r114_regress_result.txt` | 226 案 A/B 回归电池 |
| `sd_v113_baseline.py` / `semantic_REAL46-031_v113_baseline.json` | 修复前判官读数（DIFFERENT 2 R7） |
| `sd_v114_031.py` / `semantic_REAL46-031_v114.json` | 修复后判官读数（EQUAL diffs=[]） |
| `REAL46-031_product_v113.py` / `REAL46-031_product_v114.py` | 修复前后真实产品 |
| `fieldcheck_031.py` | 68 code objects 递归字段比对（判官盲区核查） |
| `repro1_postcall.py`（ARGOR）/ `repro2_nop.py` / `repro4_noptern.py`（MERGENOP）/ `repro5_boolop.py`（boolop 路径非缺陷对照）/ `repro6_sib.py`（简单名控制） | 复现矩阵 |
| `probe_argor_splice.py` / `probe_mergenop_regions.py` | 拼接干跑 / 区域归属探针 |
| `semantic_46_v5r114.json` + report | REAL46 sweep（v114） |
| `../../semantic_shard{0,1,2}_v5r114.json` + report | 1556 三分片闸门 |
| `GATE_V5R114.md` | 闸门读数与逐案对比 |

## 7. 复现命令

```bash
# 判官单案（EQUAL 期望）
D:/Python/python.exe -I -X utf8 .trae/.../argor_mergenop/sd_v114_031.py
# 回归电池（226 案 A/B）
D:/Python/python.exe -I -X utf8 .trae/.../argor_mergenop/r114_regress.py --phase=0
# 判官盲区字段比对（仅剩 __setstate__）
D:/Python/python.exe -I -X utf8 .trae/.../argor_mergenop/fieldcheck_031.py
# 1556 三分片 + 46 sweep：见 GATE_V5R114.md §0
```
