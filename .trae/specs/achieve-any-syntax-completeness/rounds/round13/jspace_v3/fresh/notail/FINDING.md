# rr-v5r148 [v148-NOTTAIL] FINDING — B116 sinkexit 否定 and 尾豁免（difflib get_grouped_opcodes 闭合）

## 1. 缺陷（真实 R1）

REAL46-012 difflib 判官 6 个 DIFF 单元之首 `SequenceMatcher.get_grouped_opcodes`
尾部 `if group and not (len(group)==1 and group[0][0]=='equal'): yield group`
（生成器尾，体= `yield group`+隐式 return None sink）反编译为嵌套 if 碎片：

- v147 渲染：`if group: / if len(group)==1: / if not group[0][0]=='equal': yield group; return None`
  ——一般分支（len≠1 的多元素尾组，doctest 主用例）的 yield **整体丢失**，
  调用 doctest 语义破损；重编译控制流与原始不一致 → 判 Different control flow。
- 语义：源码条件 `group and not (B and C)` 的真路径（B 假或 C 假）必须每次
  迭代到达 yield；v147 渲染只保留 C 假一条腿。

## 2. 根因（两层）

### 2.1 分析器层：B116 sinkexit 门误拒

`_create_boolop_region_from_chain` 的 [R4-B116] 出口不变量门
（`_boolop_chain_exits_are_distinct_sinks`）：链成员短路目标为 ≥2 个互不相同、
无后继、以隐式 return None 收尾的 sink 块 → 拒绝折叠（该门为逐语句嵌套 if
`if A: if B: return None` 形设立，b01/b03 冻结失败对即其保护对象）。

否定 and 尾 `P and not (B and C)`（尾组 ≥2 成员）CPython 3.11 编译：

```
前缀 P:  PJF→E   （全链假出口）
尾组次末 B: PJF→X  （X = if 体 = 条件真出口）
尾组末 C:  PJT→E′  （假出口）
C 落空边→X（体）
```

生成器尾形态下 X 与 E/E′ **都是** return-None sink（`yield`+隐式 return），
B116 把「两个互不相同的 None-sink 出口」判为嵌套 if 而拒绝折叠 → 链
[66,104] 不产 BoolOpRegion → 块交还 IfRegion 逐层嵌套 → 一般分支 yield 丢失。

对照实证（v1_mid `if a and not (b and c): x()`）：E==E′ 合并为同一块（42），
且体非 sink → B116 不触发 → 既有路径已正确渲染。缺陷域 = twin 出口形
（E≠E′ 两个等价 None-sink）∧ 体也是 None-sink。

### 2.2 生成器层：折叠链渲染仍为嵌套 + else 臂布局漂移

分析器放行后渲染层 `_fold_chain_consistent`（嵌套 if 折叠为目标一致性守卫）
既有 'and' 判据要求全员跳转目标同块：折叠链 [A(316), C(332)] 目标 {358,362}
twin 出口不满足 → 保持嵌套。嵌套文本重编译后两出口块线性序与原始**交换**
（原始 A-出口@358 前置/C-出口@362 后置；重编译 A-出口后置/C-出口前置），
pyc_verify `is_control_flow_equivalent` 按偏移序 zip 映射 → Different control flow。

## 3. 修复（只增不破，双文件 +225/−4）

### 3.1 region_analyzer.py（+106/−1）

- 新增 `_boolop_chain_is_negated_and_tail(chain)`（B116 豁免侧判据）：
  ①末成员真跳族 PJT→E′；②次末成员假跳族 PJF→X；③**核心结构区分**——末成员
  落空边 == 次末成员假边（同一 if 体 X，`not(...)` 真路径汇合；逐语句嵌套 if
  两出口语义不同不汇合）；④X ∉ 链块集；⑤前缀成员（n≥3）假边全员同块 E 且
  E≡E′ 等价出口（`_is_equivalent_exit_block` 既有判据）；⑥p=0 时链首须有
  假跳前驱 P（落空边续接链首+假边目标≡E′，外层 and 成员结构事实）。
- B116 门改豁免式：`_boolop_chain_exits_are_distinct_sinks(chain) and not
  _boolop_chain_is_negated_and_tail(chain)` 才拒绝。

### 3.2 region_ast_generator.py（+119/−3）

- 新增 `_and_chain_nottail_targets_consistent(cond_blocks)`：折叠链
  [外层, 内层1..k] 的否定 and 尾 twin 出口判据（E 与 E′ 互不相同且
  `_is_equivalent_exit_block` 等价；同块形返回 False 交既有 'and' 判据）。
- `_fold_chain_consistent` 既有两判定后追加第三判定（R142-D 放宽之前），
  带**极性守卫**——仅当内层候选条件为 `UnaryOp(not, BoolOp(and,...))`
  （内层 IfRegion 已由 BoolOpRegion 重建 `not (B and C)`）才触达；正极性
  内层（裸名/plain and/or 链）不触达（v111_plain_and / v111_m4_single_if
  首跑回归→守卫闭合，两案回到 TEXT-SAME+BYTE-EQUAL）。
- If 装配前新增 else 隐式 return None 抑制：折叠已发生（末位 not 的 and
  BoolOp）+ else 恰为一条隐式 Return(None) + else 首块 trailing-return-None
  sink + 链 [外层, 末折叠子] 满足 twin 出口等价 → 不发射 orelse
  （显式 else 使重编译把末成员出口并入 else 后继块，与原始 twin 布局偏移序不齐）。

## 4. 判定链证据

- 区域树（v147）：IfRegion[62,66,104,128,140,144]/IfRegion[144,66,104]/IfRegion[128,144,104]
  三层嵌套；BoolOpRegion 缺位。
- 门探针：`_detect_boolop_chain_start(66)` 返回 [(66,'and'),(104,'or')] ✓；
  `_create_boolop_region_from_chain` 返回 None（B116）；resolve_merge=144。
- 最小复现 ggo.pyc：v147 嵌套碎片（yield 丢失）→ v148
  `if group and not (len(group)==1 and group[0]=='equal'): yield group; return None`。
- 判官 CFG 映射：折叠+else 抑制后 62/62 边全同（唯一余差 332→[348,358] vs
  [348,362] 由 else 臂造成，抑制后消除）。
- 可行性实验：源级平坦形重编译 vs 原始 pyc 判官 compare_pyc = Equal
  （twin→合并出口的 patch 归一被 `fix_unreachable` 系吸收）。

## 5. 验收

- 矩阵 13 案：E1/E2/E3 功效（HEAD-TEXT-DIFF→v148 JUDGE-EQUAL 字节验证）、
  C1 合并出口/C2 ret1/C3 三成员尾/C4 k=1/C5 负极性 or/C8 na5/C9 orandtail
  零漂移 SAME+JUDGE-EQUAL；C6/C7 B116 原形/C10 守卫嵌套 SAME（预存在
  JUDGE-DIFF 维持，B116 原形不触发豁免）。
- 电池 280 案（R110 169 + V111..V122 + V148 13）：TEXT-DIFF 3/280=E1/E2/E3
  登记改进案（嵌套碎片→源级平坦形，BYTE-EQUAL）；R110 169 案 TEXT 一致
  168/签名一致 167（与 r147 基线逐位一致）；REG-10 其余 9 案 ALL
  SAME-SIGNATURE（含 SUBST-SIG pd8_prod）、na5=r144 登记改进 A/B 口径归一
  （与 r147 相同模式）；NO-SRC 0。首跑曾出 v111_plain_and/v111_m4_single_if
  两案漂移（折叠缺极性守卫），守卫闭合后归位——细节见 §3.2。
- pytest 7 套件：2F/277P/2XP 冻结基线（B01/BOUNDARY_02）。
- difflib 判官：56/62 → **57/62（91.94%）**，get_grouped_opcodes 闭合；
  其余 5 单元（get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper）维持。

## 6. 域名与登记

域名 NOTTAIL（if 条件否定 and 尾 twin 出口族）。下轮候选：
- difflib 其余 5 判官单元；
- k=1 twin 形（`if a and not b: yield` twin 出口，本轮未触——既有 B116 拒绝
  维持，独立登记）；
- p=0 独立 `not (B and C)` if 条件（无外层 and 成员前驱，本轮不豁免，维持原状）；
- 守卫嵌套族（G1，Task 74 探查结论：需 4+ 子系统协同专项轮）；
- REAL46-014 tarfile / 016 urllib.request 余差。

## 7. 证据与中间件

证据（本目录）：`r148_regress.py`+result、`fix_patch_v5r148.diff`、
`difflib_judge_v148.txt`、本文件。中间件（D:/temp/opencode/cl_layout/r147diag/）：
ggo*.pyc/probe*.py/dbg*.py/matrix_v5r148.py/variants_nandtail.py/probe_cfg_diff.py、
r148matrix/。
