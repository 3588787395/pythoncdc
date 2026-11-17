# rr-v5r188 — 5 个漂移形态的冻结树 bisect（首次变坏提交 + 可疑函数 + G3 基线溯源）

树：`F:\Downloads\pythoncdc-main`（只读；`git status` 仅 `.trae` 下证据/JSON 变动，`core/ scripts/ tests/ tools/` 未改）
解释器：`D:/Python/python.exe -X utf8`，cwd 由脚本设置；判官：`scripts/pyc_verify.py single`（内部 `pylingual/equivalence_check.py::compare_pyc`）
只读约束：所有实验都在 `D:\temp\opencode\cl_layout\bisect\` 的 `git archive` 冻结树里；当前树无 checkout/reset/stash
基线：`G3` 快照 = `.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_products/shard{0,1}/*.py`
（证据记录在 `D:\temp\opencode\cl_layout\gap\g3fix\semantic_v3m_b275_g3fix_merged.json` 的 `c3.product_path/sha256` + `c4.verdict=EQUAL`）

---

## 0. 结论（先看这一张表）

| # | 形态 | 目标 pyc | 首次变坏提交 | 可疑函数（该提交 diff 的 hunk 归属） | 上一次正确 | 与 f7d80873 的关系 |
|---|---|---|---|---|---|---|
| D1a | `(a and b) or c or d` 摊成嵌套 if/pass，直跑 `1→0` | `test_repros/round3/e01_g1_b98_matrix.pyc` | **r171 `d677817c`** | `core/cfg/region_ast_generator.py::_process_if_blocks`（+29 @L33964，`[v171-NESTED-ARM]`） | r170 `7e12e48b` | f7d80873 上**仍正确** |
| D1b | `while` 丢 `if n > 2: break` ⇒ `f_b98_while_cond_pos(1,1,1)` 死循环 | 同上 | **r117 `85982510`** | `core/cfg/region_ast_generator.py::_loop_generate_while`（+12 @L10060，`[v117-ELIFTEST]` 入口 Region 排除吸收） | r116 `2292a8c2` | f7d80873 上**已错**（早于候选窗口） |
| D2 | 嵌套 try/finally 的 finally 对调，`[1,2,1,2,1,1,2,-1]→[2,1,1,1,1,-1]` | `.trae/.../probes_rv2/v_b71_face.pyc` | **r124 `0c6308fc`** | `core/cfg/region_analyzer.py::_build_region_hierarchy`（+69 @L37066，`[v124-LOOPHEAD]` 层级裁决后重挂） | r123 `7474b0e6` | f7d80873 上**已错** |
| e02 | `a or (b and c)` → `not a and b and c`（De Morgan 反转） | `test_repros/round3/e02_g1_b98_hosts.pyc` | **r172 `9d236f9d`** | `core/cfg/region_analyzer.py::_v172_negated_and_operand_op_types`（+73 @L33688，经 `_create_boolop_region_from_chain` +1 接线） | r171 `d677817c` | f7d80873 上**仍正确** |
| r1_10 | `while a and b or c` → `if a: while b or c` | `test_repros/round1/r1_10_while_mixed.pyc` | **r143 `d0ab6e94`** | `core/cfg/region_analyzer.py::_detect_while_boolop_forward_chain`（+47 @L32471，`[v143-ORCHAIN]`） | r142 `13610dcc` | f7d80873 上**已错** |
| r9_02 | `keep(x)` 变死代码（`continue` 之后），副作用 3 次→0 次 | `test_repros/round9/r9_02_b2_dual_continue.pyc` | **r171 `d677817c`** | `core/cfg/region_ast_generator.py::_if_generate_normal`（+34/−1 @L29852，`[v171-ITER-EXIT-b]` merge 认领守卫） | r170 `7e12e48b` | f7d80873 上**仍正确** |

**判定：6 个子形态全部是回归，没有一条“从未正确”。**
3 条（D1b / D2 / r1_10）在任务给定的候选窗口（r171…r187）之外就已变坏（r117 / r124 / r143），
但它们在 **真正的 G3 基线** 上是正确的——见 §4：G3 快照产物逐字节等于 **r72 `d9e532d5`** 的树输出，
而不是 `f7d80873`（r160）。因此：**G3 的 EQUAL 读数本身可复算、不错；错的是把它归到 `f7d80873` 上。**
按 f7d80873 判，会把 r117/r124/r143 的三条误判成“从未正确”。

---

## 1. 方法（逐条可复现）

### 1.1 当前树确实错（先确认，再 bisect）

`D:/Python/python.exe -X utf8 pycdc.py <pyc> -o <out>`（cwd=当前树）+ `pyc_verify.py single`：

| pyc | 当前树产物 sha16 | judge | 失败单元 |
|---|---|---|---|
| e01_g1_b98_matrix | `6f317b37938cc37e` | failure 13/15 | `f_b98_while_cond_pos`、`f_b98_or_tail_and_group` |
| v_b71_face | `ce39c5a6d479128a` | failure 3/4 | `v_nest_fin_continue` |
| e02_g1_b98_hosts | `b87f2cd1590d49be` | failure 16/18 | `f_match_arm_host`、`CB98.m_class_body_host` |
| r1_10_while_mixed | `3a2a6cc5f15fc278` | failure 1/2 | `f` |
| r9_02_b2_dual_continue | `a889c714da4bc923` | failure 4/5 | `break_continue_mix` |

**直接运行**（原件 pyc 与产物各跑一次；`r9_02` 两边注入同一 `keep` 记录器）：

| 形态 | 原件 pyc | 当前树产物 | r160 树产物 | G3 快照产物（= r72） |
|---|---|---|---|---|
| e01 `f_b98_or_tail_and_group(1,1,1,1)` | `1` | **`0`** | `1` | `1` |
| e01 `f_b98_while_cond_pos(1,1,1)` | `3` | **超时（死循环）** | **超时** | `3` |
| vb71 `v_nest_fin_continue([0,1,-1])` | `[1,2,1,2,1,1,2,-1]` | **`[2,1,1,1,1,-1]`** | 同当前（错） | `[1,2,1,2,1,1,2,-1]` |
| e02 `f_match_arm_host(1,1,1,'zz')` / `CB98().m_class_body_host(1,1,1)` | `1` / `1` | **`False` / `False`** | `1` / `1` | `1` / `1` |
| r1_10 `f(0,1,1)` | `10` | **`0`** | **`0`** | `10` |
| r9_02 `break_continue_mix([0,1,-1],F,F)`（`keep` 调用次数） | `keep=3` | **`keep=0`** | `keep=3` | `keep=3` |

### 1.2 冻结树

- 主扫描：`git archive <rev> pycdc.py core bytecode scripts` → `trees/<label>`（r160…HEAD 共 47 个提交；其中 27 个改动过 `pycdc.py/core/bytecode`，20 个 docs/evidence 提交按“上一代码提交继承”记录）。
- 扩展二分：`d9e532d5 (r72) .. f7d80873 (r160)` 共 75 个代码提交，按 **每提交是否改动 `pycdc.py/core/bytecode`** 作为可归因点，二分 15 次探针（每个探针都落盘产物、sha16、judge、形态标志）。
- 每个产物的判官都是该树自己的 `scripts/pyc_verify.py`（实测该文件在 r160…HEAD 未变，故与当前树同实现；判官内部只依赖 `pylingual`）。

关键命令（每个树/提交各一次）：

```powershell
# 冻结树
git archive --format=tar -o <tmp>.tar <rev> pycdc.py core bytecode scripts
tar -xf <tmp>.tar -C D:\temp\opencode\cl_layout\bisect\trees\<label>
# 反编译（cwd = 该冻结树）
D:/Python/python.exe -X utf8 pycdc.py <abs pyc> -o <products>\<rev>\<key>.py
# 判官（cwd = 当前仓库；--source 用冻结树产物）
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single <abs pyc> --source <products>\<rev>\<key>.py
```

### 1.3 形态标志（AST 判定，避免“看文本猜”）

| 标志 | 含义 | 判据 |
|---|---|---|
| `d1a_bad` | `f_b98_or_tail_and_group` 的 `i and (a and b or c or d)` 被摊平 | 函数内不存在任何同时含 `And`+`Or` 的 BoolOp 测试；出现 `Pass` |
| `d1b_bad` | `f_b98_while_cond_pos` 丢 break | 函数内无 `Break` |
| `d2_bad` | 两层 finally 对调 | 外层 finally 常量=1 且内层=2（正确为内层 1、外层 2） |
| `e02_bad` | De Morgan 反转 | `return not X and ...` 形态（`BoolOp(And)` 首操作数为 `UnaryOp(Not)`） |
| `r110_bad` | while 条件被拆 | 函数体顶层出现 `If`（正确形态是 `While` 直接作语句） |
| `r902_bad` | `keep(x)` 成死代码 | 同一语句表内 `Continue` 出现在 `keep(...)` 之前 |

同一批数据也保留了 judge 逐单元失败名，用于交叉校验（例如 r170 的 e01 只挂 `f_b98_while_cond_pos`，r171 起再挂 `f_b98_or_tail_and_group`）。

### 1.4 归因实验（文件级 / 单 hunk 级）

- **文件级 swap**：把坏提交的单个文件覆盖到其父提交的冻结树上，只有目标文件能复现形态翻转（其余文件不动）。
- **单 hunk 级**：用 `git diff -U0` 的 hunk 逐组重建文件（已验证“全 hunk 重建 == `git show <rev>:<file>`”逐字节相等），只放入一个函数的改动再跑。

结果：

| 提交 | 只放 `region_analyzer.py` | 只放 `region_ast_generator.py` | 只放 `code_generator.py` | 结论 |
|---|---|---|---|---|
| r171（D1a / r9_02） | 不翻转 | **两者都翻转** | 不翻转 | 根因在 `region_ast_generator.py` |
| r172（e02） | **翻转** | 不翻转 | — | 根因在 `region_analyzer.py` |
| r143（r1_10） | **翻转** | 不翻转 | — | 根因在 `region_analyzer.py` |

单 hunk 级（同一文件内再分）：

| 提交 | 放入的 hunk | D1a | D1b | r9_02 | e02 | r1_10 |
|---|---|---|---|---|---|---|
| r171 | `_if_generate_normal`（+34/−1） | 不翻转 | — | **翻转** | — | — |
| r171 | `_process_if_blocks`（+29） | **翻转** | — | 不翻转 | — | — |
| r171 | 全部 3 个 hunk | 翻转 | — | 翻转 | — | — |
| r172 | `_v172_negated_and_operand_op_types` + 接线（+73/+1） | — | — | — | **翻转** | — |
| r172 | 其余 3 个 hunk | — | — | — | 不翻转 | — |
| r143 | `_detect_while_boolop_forward_chain`（+47） | — | — | — | — | **翻转** |
| r143 | `_identify_boolop_regions`（+16） | — | — | — | — | 不翻转 |

⇒ r171 一个提交里其实是两处独立回归：`_if_generate_normal` 改坏 r9_02，`_process_if_blocks` 改坏 D1a。

---

## 2. 每个形态的取证细节

### 2.1 D1a — r171 `d677817c`（`_process_if_blocks`）

- 上一正确 r170 `7e12e48b` 产物 `73cf27c674cf1873`，judge 14/15（只挂 while）；文本：
  ```python
  if i and (a and b or c or d):
      return i
  ```
- r171 产物 `6f317b37938cc37e`，judge **13/15**，新增失败 `f_b98_or_tail_and_group: Different control flow`；文本：
  ```python
  if i:
      if b:
          if c:
              if d:
                  pass
      else:
          return i
  ```
- 直跑 `f_b98_or_tail_and_group(1,1,1,1)`：r170 `1` → r171 `0`。
- 单 hunk 实测：只放 `_process_if_blocks` 的 +29 行即复现；`_if_generate_normal` 的 +34/−1 不触发。
- 该 hunk 的注释即 `[v171-NESTED-ARM]`（父 IfRegion 臂块列表收进嵌套 IfRegion 的臂块），
  与“BoolOpRegion 入口不再等于 IfRegion 入口、`_generate_if` 认领失败 → 嵌套 if/pass”一致。

### 2.2 D1b — r117 `85982510`（`_loop_generate_while`）

- 上一正确 r116 `2292a8c2` 产物 `e5b02d5ef81ebf46`，judge **15/15**（与 G3 快照同 sha）：
  ```python
  while (a or b) and c:
      if n > 2:
          break
      n += 1
  ```
- r117 产物 `73cf27c674cf1873`，judge 14/15（`f_b98_while_cond_pos: Different control flow`），`if n > 2: break` **整段消失**，直跑 `(1,1,1)` 死循环。
- 提交只改 `core/cfg/region_ast_generator.py` 12 行（0 删除），hunk 归属 `_loop_generate_while`，
  注释 `[v117-ELIFTEST]`：块若是另一 Region 的入口则不当作“条件闩锁重检块”吸收。
  该守卫使 break 所在块不再被吸收/发射。

### 2.3 D2 — r124 `0c6308fc`（`_build_region_hierarchy`）

- 上一正确 r123 `7474b0e6` 产物 `010ad39367f036fa`，judge **4/4**（= G3 快照 sha）：
  ```python
  try:
      try: ...
      finally:
          out.append(1)
  finally:
      out.append(2)
  ```
- r124 产物 `ce39c5a6d479128a`，judge 3/4（`v_nest_fin_continue`）：
  内外 finally 对调为 `2`/`1`，内层 try 退化成 `pass`；直跑 `[1,2,1,2,1,1,2,-1]` → `[2,1,1,1,1,-1]`。
- 提交只改 `core/cfg/region_analyzer.py` +69（0 删除），单 hunk 归属 `_build_region_hierarchy`，
  注释 `[v124-LOOPHEAD]`：层级裁决后把 try 区域重挂到最窄宿主 L，可能改变嵌套 try 的父子/归属。
- 文件级 swap 证实只有该文件能翻转；无第二 hunk 可再分。

### 2.4 e02 — r172 `9d236f9d`（`_v172_negated_and_operand_op_types`）

- 上一正确 r171 产物 `9f4b826eed3298d7`，judge **18/18**：
  `return a or (b and c)`（`f_match_arm_host` case _ 与 `CB98.m_class_body_host` 各一处）。
- r172 产物 `b87f2cd1590d49be`，judge 16/18（两个单元 `Different bytecode`）：
  `return not a and b and c`；直跑 `1` → `False`。
- 提交改 `region_analyzer.py` 5 个 hunk；单 hunk 实测 `_v172_negated_and_operand_op_types`(+73)
  + `_create_boolop_region_from_chain` 的 +1 接线 即翻转，其余 hunk 不翻转。

### 2.5 r1_10 — r143 `d0ab6e94`（`_detect_while_boolop_forward_chain`）

- 上一正确 r142 `13610dcc` 产物 `6db8e097cb6d353b`，judge **2/2**（= G3 快照 sha）：
  ```python
  while a and b or c:
      ...
  ```
- r143 产物 `3a2a6cc5f15fc278`，judge 1/2（`f: Different control flow`）：
  `if a: while b or c: ... if not a: break`；直跑 `f(0,1,1)`：`10` → `0`。
- 提交双文件；文件级 swap 只有 `region_analyzer.py` 翻转；单 hunk 只有
  `_detect_while_boolop_forward_chain`(+47 @L32471) 翻转（`_identify_boolop_regions` +16 不翻转）。
- `region_ast_generator.py` 同提交的 +12/−1（`_loop_generate_while`）不是充分条件。

### 2.6 r9_02 — r171 `d677817c`（`_if_generate_normal`）

- 上一正确 r170 产物 `3aa5d94000e9bd52`，judge **5/5**：
  ```python
  keep(x)
  continue
  ```
- r171 产物 `a889c714da4bc923`，judge 4/5（`break_continue_mix: Different control flow`）：
  ```python
  continue
  keep(x)
  ```
  直跑 `keep` 调用次数 3 → 0。
- 单 hunk 实测：只放 `_if_generate_normal`（+34/−1，`[v171-ITER-EXIT-b]` merge 认领守卫）即翻转；
  `_process_if_blocks` 不触发。该守卫把“then 臂是裸 continue、merge 以 JUMP_BACKWARD 收尾”的 merge
  认成 if 之后同层语句块并吸进臂内，导致 `keep(x)` 落到 `continue` 之后。

---

## 3. 提交级审计表（逐提交落盘，便于复核）

`ok` = 该形态的 AST 判据正常；`**BAD**` = 判据命中；`·` = 该提交上没有为该形态跑过产物（扩展二分只探 3 个 pyc）。
判官读数在 `results.json` / `ext_r72_160.json` 的每行 `judge_status/units/judge_failures` 里。

| commit | date | D1a | D1b | D2 | e02 | r1_10 | r9_02 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| r72_d9e532d5 `d9e532d5` | 2026-10-27 | ok | ok | ok | ok | ok | ok |
| r117_85982510 `85982510` | 2026-11-06 | ok | **BAD** | ok | · | ok | · |
| r124_0c6308fc `0c6308fc` | 2026-11-07 | ok | **BAD** | **BAD** | · | ok | · |
| r143_d0ab6e94 `d0ab6e94` | 2026-11-08 | ok | **BAD** | **BAD** | · | **BAD** | · |
| r160_f7d80873 `f7d80873` | 2026-11-11 | ok | **BAD** | **BAD** | ok | **BAD** | ok |
| r170_7e12e48b `7e12e48b` | 2026-11-15 | ok | **BAD** | **BAD** | ok | **BAD** | ok |
| r171_d677817c `d677817c` | 2026-11-15 | **BAD** | **BAD** | **BAD** | ok | **BAD** | **BAD** |
| r172_9d236f9d `9d236f9d` | 2026-11-15 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r173_73ea3a0e `73ea3a0e` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r174_645fb375 `645fb375` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r175_dfb5b7f8 `dfb5b7f8` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r176_bfd67c6e `bfd67c6e` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r177_fa2b708c `fa2b708c` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r178_1785e67a `1785e67a` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r180_a20aa311 `a20aa311` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r181_4753cc05 `4753cc05` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| x_d2949e56 `d2949e56` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r184_d8f343e4 `d8f343e4` | 2026-11-16 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r186_572f35d2 `572f35d2` | 2026-11-17 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |
| r187_154f7784 `154f7784` | 2026-11-17 | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** | **BAD** |

每行产物 sha16：

| commit | e01 | vb71 | e02 | r110 | r902 |
|---|---|---|---|---|---|
| r72 `d9e532d5` | `e5b02d5ef81ebf46` | `010ad39367f036fa` | `9f4b826eed3298d7` | `6db8e097cb6d353b` | `3aa5d94000e9bd52` |
| r117 `85982510` | `73cf27c674cf1873` | `010ad39367f036fa` | · | `6db8e097cb6d353b` | · |
| r124 `0c6308fc` | `73cf27c674cf1873` | `ce39c5a6d479128a` | · | `6db8e097cb6d353b` | · |
| r143 `d0ab6e94` | `73cf27c674cf1873` | `ce39c5a6d479128a` | · | `3a2a6cc5f15fc278` | · |
| r160 `f7d80873` | `73cf27c674cf1873` | `ce39c5a6d479128a` | `9f4b826eed3298d7` | `3a2a6cc5f15fc278` | `3aa5d94000e9bd52` |
| r170 `7e12e48b` | `73cf27c674cf1873` | `ce39c5a6d479128a` | `9f4b826eed3298d7` | `3a2a6cc5f15fc278` | `3aa5d94000e9bd52` |
| r171 `d677817c` | `6f317b37938cc37e` | `ce39c5a6d479128a` | `9f4b826eed3298d7` | `3a2a6cc5f15fc278` | `a889c714da4bc923` |
| r172 `9d236f9d` | `6f317b37938cc37e` | `ce39c5a6d479128a` | `b87f2cd1590d49be` | `3a2a6cc5f15fc278` | `a889c714da4bc923` |
| r173…r187（含 docs/evidence 提交） | `6f317b37938cc37e` | `ce39c5a6d479128a` | `b87f2cd1590d49be` | `3a2a6cc5f15fc278` | `a889c714da4bc923` |

逐形态边界证据：

| 形态 | 上一正确（sha16 / judge） | 首次变坏（sha16 / judge） |
|---|---|---|
| D1a | r170 `7e12e48b` `73cf27c674cf1873` failure 14/15（只挂 while） | r171 `d677817c` `6f317b37938cc37e` failure 13/15（+`f_b98_or_tail_and_group`） |
| D1b | r116 `2292a8c2` `e5b02d5ef81ebf46` **success 15/15** | r117 `85982510` `73cf27c674cf1873` failure 14/15 |
| D2 | r123 `7474b0e6` `010ad39367f036fa` **success 4/4** | r124 `0c6308fc` `ce39c5a6d479128a` failure 3/4 |
| e02 | r171 `d677817c` `9f4b826eed3298d7` **success 18/18** | r172 `9d236f9d` `b87f2cd1590d49be` failure 16/18 |
| r1_10 | r142 `13610dcc` `6db8e097cb6d353b` **success 2/2** | r143 `d0ab6e94` `3a2a6cc5f15fc278` failure 1/2 |
| r9_02 | r170 `7e12e48b` `3aa5d94000e9bd52` **success 5/5** | r171 `d677817c` `a889c714da4bc923` failure 4/5 |

### 3.1 候选提交列表覆盖

任务给的 14 个候选（r171…r187）全部实跑落盘：`r171 d677817c`、`r172 9d236f9d`、`r173 73ea3a0e`、
`r174 645fb375`、`r175 dfb5b7f8`、`r176 bfd67c6e`、`r177 fa2b708c`、`r178 1785e67a`、`r180 a20aa311`、
`r181 4753cc05`、`r182 d2949e56`（docs，继承）、`r184 d8f343e4`、`r186 572f35d2`、`r187 154f7784`。
r179/r183 在历史里不存在（编号跳过），未实跑。
由于 3 个形态的首次变坏早于 r171，额外把 r72…r160 的 75 个代码提交纳入二分（15 个探针 + 4 个边界提交按 hunk 实验复核）。

---

## 4. G3 快照溯源（本轮最重要的发现）

### 4.1 G3 基线记录指向的产物

`gap/g3fix/semantic_v3m_b275_g3fix_merged.json` 里这些 entry 的 `c3.sha256`（`c4.verdict=EQUAL`，
judge `semantic_diff/1.0.0+g3fix`）：

| entry | product_path | `c3.sha256`（前 16） |
|---|---|---|
| JS-BOOLOP-008 | `.../semantic_products/shard0/JS-BOOLOP-008.py` | `e5b02d5ef81ebf46` |
| JS-IF-017 | `.../semantic_products/shard0/JS-IF-017.py` | `010ad39367f036fa` |
| JS-IF-043 | `.../semantic_products/shard0/JS-IF-043.py` | `9f4b826eed3298d7` |
| JS-WHILE-001 | `.../semantic_products/shard1/JS-WHILE-001.py` | `6db8e097cb6d353b` |
| JS-CONTINUE-003 | `.../semantic_products/shard1/JS-CONTINUE-003.py` | `3aa5d94000e9bd52` |

这些文件 mtime = **2026-10-27 20:22–20:46**；同一时刻的 HEAD 是 `d9e532d5`（rr-v5r72, 2026-10-27 16:45），
下一个提交 `4610223c` 在 21:16。用 `d9e532d5` 冻结树重跑 5 个 pyc：

```
e01 e5b02d5ef81ebf46   vb71 010ad39367f036fa   e02 9f4b826eed3298d7
r110 6db8e097cb6d353b  r902 3aa5d94000e9bd52
```

**5/5 与 `c3.sha256` 逐字节相同**；对这 5 个产物跑判官：`15/15`、`4/4`、`18/18`、`2/2`、`5/5` 全 success —
与 G3 的 EQUAL 读数一致。直跑也与原件一致（§1.1 最后一列）。

⇒ **G3 基线产物来自 r72 `d9e532d5`（2026-10-27），不是 `f7d80873`（r160, 2026-11-11）。**

### 4.2 f7d80873 并不是基线

`f7d80873` 树产物为 `e01 73cf27c6`、`vb71 ce39c5a6`、`e02 9f4b826e`、`r110 3a2a6cc5`、`r902 3aa5d940`：
3/5 与 G3 快照不同，且这 3 个在 f7d80873 上已经判官失败（14/15、3/4、1/2）。
即 D1b / D2 / r1_10 早在 r117 / r124 / r143 就坏了，落在 r160 之前。

### 4.3 对“读数可疑”的结论

- **EQUAL 读数本身可复算，不是判官/环境伪差**：用 r72 树 + 当前判官重跑，5/5 精确复现，产物直跑 = 原件。
- **可疑的是来源标签**：若把这些 EQUAL 当作 `f7d80873` 的读数（任务假设 / DRIFT_109 的口径），
  就与实测矛盾——`f7d80873` 上其中 3 个形态已判官失败。
- 因此“**f7d80873 基线也错 ⇒ 从未正确**”的判定不成立；正确口径是
  “**G3 基线 = r72，5 形态全部是 r72→r187 的回归**”，drift 窗口是 r73…r187，不是 r160…r187。

---

## 5. 回归 vs 从未正确 的最终判定

| 形态 | 判定 | 依据 |
|---|---|---|
| D1a | 回归（r171） | r72/r170 正确且 judge 通过该单元；r171 起 `f_b98_or_tail_and_group` 单元失败 |
| D1b | 回归（r117） | r72…r116 均 `15/15`（sha 与快照同）；r117 起丢 break |
| D2 | 回归（r124） | r72…r123 均 `4/4`（sha 与快照同）；r124 起 finally 对调 |
| e02 | 回归（r172） | r72…r171 均 `18/18`；r172 起 De Morgan 反转 |
| r1_10 | 回归（r143） | r72…r142 均 `2/2`（sha 与快照同）；r143 起 while 条件截断 |
| r9_02 | 回归（r171） | r72…r170 均 `5/5`；r171 起 keep 成死代码 |

没有“从未正确”的形态。若只看 `f7d80873`，D1b/D2/r1_10 会被误判为“从未正确”——这正是 §4 纠正的口径。

---

## 6. 复现命令

```powershell
cd F:\Downloads\pythoncdc-main

# 1) 当前树确认（产物 + 判官 + 直跑）
D:/Python/python.exe -X utf8 pycdc.py test_repros/round3/e01_g1_b98_matrix.pyc -o <out>.py
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round3/e01_g1_b98_matrix.pyc --source <out>.py
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\bisect\work\run_probe.py

# 2) 主扫描：r160…HEAD 全提交（47 个），每提交 5 个产物 + 判官 + 形态标志
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\bisect\work\bisect_driver.py `
    --out D:\temp\opencode\cl_layout\bisect\results.json --jobs 5

# 3) 扩展二分：r72…r160（75 个代码提交）的 D1b / D2 / r1_10
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\bisect\work\bisect_range.py `
    --lo d9e532d5 --hi f7d80873 --keys vb71,r110,e01b `
    --out D:\temp\opencode\cl_layout\bisect\ext_r72_160.json

# 4) 归因：文件级 swap / 单 hunk
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\bisect\work\swap_test.py
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\bisect\work\hunk_patch.py

# 5) 提交 diff 的 hunk→函数 归属
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\bisect\work\commit_evidence.py `
    d677817c core/cfg/region_ast_generator.py
```

产物：

| 路径 | 内容 |
|---|---|
| `fresh/gate_drift/BISECT.md` | 本报告 |
| `D:\temp\opencode\cl_layout\bisect\results.json` | 47 提交 × 5 产物的 sha16 / judge / 形态标志 / 失败单元 |
| `D:\temp\opencode\cl_layout\bisect\ext_r72_160.json` | r72…r160 二分 15 个探针 + 逐 key 判定 |
| `D:\temp\opencode\cl_layout\bisect\swap_results.json`、`hunk_results.json`、`hunk172.json` | 文件级/单 hunk 归因结果 |
| `D:\temp\opencode\cl_layout\bisect\products\<label>\<key>.py` | 每个冻结树的产物 |
| `D:\temp\opencode\cl_layout\bisect\trees\<label>\` | 冻结树（`pycdc.py core bytecode scripts`） |
| `D:\temp\opencode\cl_layout\bisect\work\*.py` | 全部脚本（driver / bisect_range / swap / hunk / probe / 表生成） |
| `D:\temp\opencode\cl_layout\bisect\work\probe_current.json` | 原件/当前/r160/快照 四方的直跑读数 |

---

## 7. 边界与注意事项

1. “首次变坏”只在**改动过 `pycdc.py/core/bytecode` 的提交**上归因；docs/evidence 提交按“继承上一代码提交”记录（其 diff 不含这三个路径）。
2. 扩展二分是 15 次探针（不是 75 个提交逐个跑）；但每个形态的“上一正确 / 首次变坏”两端都落盘了产物、sha16、judge、形态标志，并做了 hunk 级复核。
3. G3 溯源的决定性证据是**产物 sha256 逐字节相等**（5/5），mtime 只作旁证；即使 mtime 被复制保留，sha 相等仍成立。
4. 只审了这 5 个 pyc（6 个子形态）；DRIFT_109 的其余 104 条未逐条复核。
5. 形态标志是 AST 判据，judge 是字节码判据；两者在本文所有边界提交上一致（唯一差别是 e01 文件级 judge 会同时受另一个子形态影响，已按单元失败名区分）。
6. 冻结树均未跑 `pytest`/全量电池；本报告的结论仅覆盖上述 5 个目标 pyc。
