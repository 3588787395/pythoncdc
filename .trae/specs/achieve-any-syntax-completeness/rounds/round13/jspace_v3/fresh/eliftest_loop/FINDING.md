# FINDING — rr-v5r117 [v117-ELIFTEST]：while 复合条件闩锁重检吸收误吞嵌套 if/elif 测试块（REAL46-019 盲区 1→0 全闭合）

## 0. 结论速览

- REAL46-019（ipaddress）判官盲区最后 1 差异（rr-v5r116 登记：`/_BaseNetwork/
  address_exclude` co_code 762 vs 718）→ **闭合**。全嵌套递归字段比对
  **166 code objects 全部 0 差异**；权威判官维持 **EQUAL（diffs=0）**。
  REAL46-019 整案（v5r114 起 3→1→0）至此全闭合。
- 本族是**真实 R1 语义缺陷**（v5r116 FINDING §5 已定性）：生成器 while 循环内
  if/elif 链的 **elif 测试指令消失、臂折叠进 else 臂尾**——合法排除路径
  （subnet_of(s2) 成立）会误抛 AssertionError。
- 家族面比预想宽：**非生成器同样塌缩**（矩阵 E2/E3 实证，HEAD 将
  `elif b > 2:` 渲染为 `else:`）。

## 1. 根因（TracedSet 标记追踪 + 标记瞬间状态快照，`probe_mark.py`/`probe_order.py`）

### 1.1 差异面（repro2 = address_exclude 精确源最小壳）

源码 while 体内三臂链：

```python
while s1 != other and s2 != other:
    if other.subnet_of(s1):   yield s2; s1, s2 = s1.subnets()
    elif other.subnet_of(s2): yield s1; s1, s2 = s2.subnets()
    else: raise AssertionError(...)
```

产品（HEAD）：`elif` 测试块 496（`LOAD_FAST other; LOAD_METHOD subnet_of;
LOAD_FAST s2; CALL; POP_JUMP_FORWARD_IF_FALSE`）未渲染——`elif` 变 `else`，
`yield s1; s1, s2 = s2.subnets()` 并入 else 臂前部。

### 1.2 机制链（逐层实证）

- 区域树：IfRegion@398（then=[440]）与 IfRegion@496（elif 测试）为兄弟；
  `_process_if_blocks(else_blocks, IfRegion@398, 'else')` 已把
  `_nested_if_entry_generate[496] = IfRegion@496` 登记（else 走查本应派发）。
- 但 else 走查到达 496 时 `if block in self.generated_blocks: continue`
  跳过——**496 已被预标记 generated**。
- TracedSet 追踪标记者：`_loop_generate_while:10062`（BoolOp 重检链吸收的
  标记循环，`_generate_loop ← _generate_region ← _process_if_blocks ←
  _if_generate_elif_chain`）。即 while 循环生成器抢在外层 if 链 else 走查
  之前认领了 496。
- 认领判据缺口：吸收分类以「块内 LOAD 变量集 ⊆ while 条件变量集
  `boolop_cond_var_names`」识别闩锁重检块。496 的 load 集 `{other, s2}` 恰为
  条件变量集 `{s1, s2, other}` 的**子集**（elif 测试 `other.subnet_of(s2)`
  只引用条件变量）→ 误吸。本循环回边直跳 header、并无合法重检块，
  吸收为纯误报。
- 标记瞬间状态快照（probe_order.py，决定性）：标记时
  `region_analyzer.get_entry_region_for_block(496)` **返回 IfRegion**（区域
  树已含 IfRegion@496）；而 `_nested_if_entry_generate` 尚未登记（晚于标记）
  → 守卫只能用前者。

### 1.3 同域排除

- 有 store 的闩锁吸收分支（`i += 1` + 尾部重检形，~10053）未触碰——C3。
- `_loop_handle_header:12475` 的第二标记位点只对 header 判定后继，496 非
  header 后继不入此径（probe 四条标记记录中两条为其余位点的重复到达）。

## 2. 修复（region_ast_generator 只增不破，[v117-ELIFTEST] 单 hunk +12/−0）

load_names 子集吸收位点（`~10060`）增加守卫：**本块若自身是另一 Region 的
入口块（`get_entry_region_for_block(b)` 非 None）则排除吸收**（No More Gotos
「每块唯一归属」：他 Region 入口块属该 Region 结构，不是本循环条件闩锁）。
合法闩锁重检块（旋转 while 条件副本）不构成独立 Region 入口，不受影响；
非入口块吸收路径逐位不变（控制案 C1/C2/C3 零漂移实证）。

## 3. 验证（全实测）

### 3.1 变体矩阵（`matrix_v5r117.py` 6 案，A/B HEAD `2292a8c2` vs v117）

| 案 | 形 | HEAD | v117 | 判定 |
|---|---|---|---|---|
| E1_eliftest_gen | address_exclude 精确形（生成器 while 内三臂链） | TEXT-DIFF（elif→else 塌缩） | 重编译 BYTE-EQUAL | PASS |
| E2_eliftest_nongen | 非生成器方法版三臂链 | TEXT-DIFF（同塌缩） | BYTE-EQUAL | PASS |
| E3_eliftest_twoarm | `while a != b and b > 0:` + `if a>b: … elif b>2: …` | TEXT-DIFF（`elif b > 2:`→`else:`） | BYTE-EQUAL | PASS |
| C1_while_compound_plain | 复合条件 while、体无 if 链 | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C2_if_noncondvar | 体内 if 测试 load 非条件变量 | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C3_while_incr | 经典增量 while（回边无条件跳转） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |

### 3.2 REAL46-019 盲区（`field019.py`，166 code objects 递归字段比对）

- v116：1 差异（address_exclude co_code 762 vs 718）→ v117：**0 差异**。
- 权威判官 `semantic_diff.compare_case`：**EQUAL（diffs=0）**（维持）。

### 3.3 回归

- A/B 回归电池（r117_regress.py：r110 169 + v111 15 + v112 15 + v113 15 +
  v115 9 + v116 4 + 本轮 6 案源 = 233 案，独立 TMP `r117regress/` 干净重跑）：
  **TEXT-DIFF 3 / 233，恰为本轮 3 功效案（E1/E2/E3）且重编译全部
  BYTE-EQUAL**；其余 230 案 TEXT-SAME；R110 案 168/169 一致（唯一差 mc1 =
  r110 轮功效案两侧同持修复正常归一，TEXT-SAME+BYTE-EQUAL）；既有登记差
  10 案 **ALL SAME-SIGNATURE**；NO-SRC 0。
  （过程登记：矩阵脚本曾缺 `__main__` 守卫致 import 时自跑全矩阵、电池漏挂
  foldret_arm 路径致 v116 案源导入失败——均修正后干净重跑，本节数字为修正后
  实测。）
- pytest 7 套件：**3 failed / 277 passed / 2 xpassed**——与基线逐项一致
  （2 冻结对 `TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、
  `TestBoundaryConditions::test_BOUNDARY_02_large_function`；第 3 failed
  `TestProductFreshness` 预存在陈旧）。零新增失败。诚实登记：3 个 stale
  条目中 2 个的 current-code 侧字节数较 v114 时代日志有漂移
  （13299/13537→13299/13462、61506/61895→61753；行数 71→168、1016→1010），
  但 A/B 实证 **HEAD(v116) 与 v117 对这两个 pyc（site-packages
  IQEngine/.../matcher.pyc、IQCommon/.../trade_info_utils.pyc）的反编译产物
  逐字节相同（13462=13462、61753=61753）**——漂移系 v115/v116 轮修复所致、
  早于本轮，v117 零漂移。
- 比较器 pyc_verify.py FE1902A9 / semantic_diff.py DBCB1E24 冻结一致、
  tests/ 零改动；唯一已跟踪改动 `M core/cfg/region_ast_generator.py`
  （+12/−0，标记 `[v117-ELIFTEST]`）。

## 4. 验收口径

小测试收口（全量闸门按用户政策只留给大改动）。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选，未修）

- E6 相邻 NOP 对（[Round 33] 相邻 NOP 守卫排除域）。
- 46 sweep 其余 DIFFERENT（REAL46-022 typing 36 维等 8 案）；46 sweep 17 ERROR。

## 6. 证据文件

`fix_patch_v5r117.diff`、`matrix_v5r117.py`、`r117_regress.py+result`、
本文件；复用 r116 轮 `field019.py`（盲区递归比对）；中间产物一律
`D:/temp/opencode/cl_layout/r117diag|r117matrix|r117regress/` 不入库。
探针：`D:/temp/opencode/cl_layout/r117diag/probe_mark.py`（TracedSet 标记
追踪）、`probe_order.py`（标记瞬间状态快照）、`probe_entry.py`、
`repro2_exact.py/repro2.pyc`（最小复现）。
