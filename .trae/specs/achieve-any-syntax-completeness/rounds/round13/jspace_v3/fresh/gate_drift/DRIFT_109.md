# rr-v5r188 — 109 条 G3 漂移的定性报告（重点是 40 条含行为维的条目）

树：`F:\Downloads\pythoncdc-main`（含 r187 补丁，`git status` 仅 `core/cfg/comprehension_generator.py` M）
解释器：`D:/Python/python.exe -X utf8`，cwd = 仓库根
判官：`tools/completeness/semantic_diff.py::compare_case`（sha256 见 `drift_109.json.judge`）
只读：core/ scripts/ tests/ tools/ 未改动；产物只在 `fresh/gate_drift/` 与 `D:\temp\opencode\cl_layout\drift\`

---

## 0. 结论（一句话）

**109 条里 82 条是产品真缺陷（a），0 条是判官/环境伪差（b），27 条是尺子效应（c）**；
40 条行为维条目**全部是 (a)**，但只由 **3 个 pyc 上的 3 处反编译错误**造成；
69 条 R7-only 里 **42 条同样是 (a)（R1 网没罩到的潜伏语义错）**，27 条是纯文本重整（(c)）；
**69 条全部不是 r187 T1/T2 的死常量族**——它们的 `co_consts` **一处都没变**。

| 分类 | 条数 | 说明 |
|---|---:|---|
| (a) 产品真缺陷 | **82** | 40 行为维（R1×39 + R6×1）+ 42 R7-only 潜伏 |
| (b) 判官/执行环境伪差 | **0** | 无一条能被环境解释（唯一的环境影响见 §3.3 的维度归属） |
| (c) 尺子效应（文本变、行为不变） | **27** | x02 6 + x05 6 + c4_12 12 + rec1_b70a 3 |
| 合计 | 109 | 69 R7-only + 39 R1+R7 + 1 R6+R7 |

---

## 1. 复算：drift_109.json 怎么来的

1. 基线集：`D:\temp\opencode\cl_layout\gap\g3fix\semantic_v3m_b275_g3fix_merged.json`
   里 `c4.verdict == EQUAL` 的 **1151** 条（= R187_EVIDENCE §4 的 G3 产品集）。
2. 候选漂移：拿 r187 全量重跑（`r187/work/semantic_r187_merged.json`，当前树）对照，
   `base==EQUAL 且 now!=EQUAL` → **109**（脚本 `recompute109.py::candidate_ids`）。
3. **复算**（本次实测，不引用旧读数）：对 109 条各自的**原件 pyc**用**当前树**重新反编译，
   再跑冻结判官。逐条落 `{entry_id, pyc, r7_only, dims, diffs(前3), product_sha}` → `drift_109.json`。

```
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\recompute109.py \
    --out drift109_raw.json --products D:\temp\opencode\cl_layout\drift\products
...
[recompute] rows=109 elapsed=109.7s
  ('R7',)                  DIFFERENT  69
  ('R1', 'R7')             DIFFERENT  39
  ('R6', 'R7')             DIFFERENT  1
  r7_only=69  with_R1=39  other=1
```

复算与旧读数**逐条一致**：69 / 39 / 1。`drift_109.json.summary` 即上述计数。

**关键结构事实：109 条只落在 10 个 pyc 上**（每条 entry 只是同一 pyc 的一个「判定维度」）：

| pyc | 条数 | 维 |
|---|---:|---|
| e01_g1_b98_matrix.pyc | 20 | R1+R7 |
| v_b71_face.pyc | 19 | R1+R7 |
| e02_g1_b98_hosts.pyc | 18 | R7 |
| r9_02_b2_dual_continue.pyc | 12 | R7 |
| r1_10_while_mixed.pyc | 12 | R7 |
| c4_12_star_args.pyc | 12 | R7 |
| x02_for_deep_hosts.pyc | 6 | R7 |
| x05_with_deep_hosts.pyc | 6 | R7 |
| rec1_synth_b70a_wt_with_bc.pyc | 3 | R7 |
| rec1_synth_g4b_b70_whiletrue_with.pyc | 1 | R6+R7 |

所以「109 条」实际只有 **10 个产物文件**，`textdrift.py` 逐 pyc 与基线产物做文本 diff：
**10/10 文本都变了**（`textdrift_by_pyc.txt`）。基线产物本体用两个尺子复判仍是 EQUAL：

```
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round3/e01_g1_b98_matrix.pyc \
    --source .trae/.../fresh/semantic_products/shard0/JS-BOOLOP-008.py
[single] status=success units=15/15 success_rate=100.00%      <- 冻结产物仍 EQUAL
# 同一 pyc 用当前树产物：
[single] status=failure units=13/15 success_rate=86.67%
    ***<module>.f_b98_while_cond_pos: Failure: Different control flow
    ***<module>.f_b98_or_tail_and_group: Failure: Different control flow
```
⇒ 漂移是**产品文本漂移**，不是判官/基线文件出了错。

---

## 2. 40 条含行为维：只有 3 个根因

| # | pyc | 出错函数 | entry 数 | 判官维 | 直跑差异 |
|---|---|---|---:|---|---|
| D1 | e01_g1_b98_matrix.pyc | `f_b98_or_tail_and_group`（并伴随 `f_b98_while_cond_pos`） | 20 | R1+R7 | `1` → `0`；另一函数 `3` → **死循环** |
| D2 | v_b71_face.pyc | `v_nest_fin_continue` | 19 | R1+R7 | `[1,2,1,2,1,1,2,-1]` → `[2,1,1,1,1,-1]` |
| D3 | rec1_synth_g4b_b70_whiletrue_with.pyc | `g4b_wt_with_continue` | 1 | R6+R7 | 原件**死循环** / 产物 `4` |

### 2.1 D1 — `if (a and b) or c or d:` 被摊成嵌套 if

- **R1 表现**：`$.call[4].return.v` original `1` → product `0`
  （entry 声明的 `f_b98_or_tail_and_group(1, 1, 1, 1)`）。
- **文本**（`products/JS-BOOLOP-008.py`）：
  ```
  if i:
      if b:
          if c:
              if d:
                  pass
      else:
          return i
  ```
  原件是 `if i: if (a and b) or c or d: return i`。
- **最小复现**：`repro/JS-BOOLOP-008.py`（8 行，逐条入口各一份，共 20 份）
  ```
  [single] status=failure units=1/2 success_rate=50.00%
  judge : DIFFERENT ['R1','R7']   R1 $.call[0].return.v  orig=1  prod=0
  direct: original_pyc {"return":"1"} | product_py {"return":"0"}
  ```
- **定性：(a) 产品真缺陷**。
- **根因**：`core/cfg/region_ast_generator.py::RegionASTGenerator._generate_if`（L19513）。
  trace（`trace_emit.py`，包装 RegionASTGenerator 后跑真反编译）实测：
  ```
  RegionAnalyzer._identify_boolop_regions -> list[1]  BoolOpRegion(entry=Block 4 ...)
  RegionASTGenerator._generate_if -> dict{"type":"If","test":{"type":"Name","id":"i"},
                                         "body":[{"type":"If","test":{"type":"Name","id":"b"},...
  （_build_boolop_expression 全程 0 次调用）
  ```
  触发形态：`for i: if i: <BoolOpRegion>` —— BoolOpRegion 的 `entry`（Block 4，`LOAD a`）**不是**
  IfRegion 的 entry（Block 3，`LOAD i`），`_generate_if` 里按 `c.entry == region.entry` 找
  `boolop_child`（L19738–19747）找不到它 ⇒ 不把该链当条件表达式，而是把成员块当语句下钻，
  于是 or/and 混合链变成「嵌套 if + pass」。
- 同 pyc 第二处（pylingual 也报 `f_b98_while_cond_pos: Different control flow`）：
  `while (a or b) and c:` 里的 `if n > 2: break` 丢失 ⇒ 直跑 `f_b98_while_cond_pos(1,1,1)`
  原件 `3`、产物**超时（死循环）**。同一个产物文件，故同样算进这 20 条。

### 2.2 D2 — 嵌套 try/finally 被对调

- **R1 表现**：`$.call[1].return.len` original `8` → product `6`。
- **文本**：内层 `finally: out.append(1)` 与外层 `finally: out.append(2)` **互换**，且内层 try 退化成 `pass`：
  ```
  try:
      if r == 0:
          try:
              pass
          finally:
              out.append(2)
          continue
  finally:
      out.append(1)
  ```
- **最小复现**：`repro/JS-IF-017.py`（15 行，共 19 份）
  ```
  [single] status=failure units=1/2 success_rate=50.00%
  judge : DIFFERENT ['R1','R7']  R1 $.call[0].return.len orig=8 prod=6
  direct: original_pyc [1, 2, 1, 2, 1, 1, 2, -1] | product_py [2, 1, 1, 1, 1, -1]
  ```
- **定性：(a) 产品真缺陷**。
- **根因**：`RegionASTGenerator._generate_try`（+ 其嵌套层级判据）。
  trace 实测 `_count_nested_try_marker_levels -> 0`、`_find_finally_normal_copy_blocks -> []`
  之后：
  ```
  _generate_try -> dict{"type":"Try","body":[{"type":"If",...}],
                        "handlers":[],"finalbody":[out.append(1)]...}
  ```
  触发形态：`for → try → try → (if: continue) → finally → finally`，两层 finally 的
  正常副本块被折叠到同一层，`finally` 归属按最外层记账。

### 2.3 D3 — `while True: with ...: if a: continue` 里的 continue 退化成 pass

- **R6 表现**：`one side raised while the other returned`——
  原件 `OSError [WinError 6] 句柄无效。`（第二次 `open(1)`；第一次 `with` 退出时已把 fd 1 关掉），
  产物直接 `return 4`。
- **文本**：`if a: continue` → `if a: pass`。
- **最小复现**：`repro/JS-WHILE-042.py`（8 行）
  ```
  [single] status=failure units=1/2 success_rate=50.00%
  judge : INCONCLUSIVE（原件在该形状下死循环 ⇒ 判官按超时记 INCONCLUSIVE，不记 DIFFERENT）
  direct: original_pyc {"timeout": true} | product_py {"return": "4"}
  ```
  真实工件（args `(1, 1)`，fd 1 被关）在判官下是 **R6+R7**（见 §1 的 109 复算）。
- **定性：(a) 产品真缺陷**；只是它落在 R6 而不是 R1，是「原件第二次 open 抛 OSError」决定的，
  换环境会变成 R1/超时——**维度归属受环境影响，缺陷本身不受**。
- **根因**：`RegionASTGenerator._b66_is_with_exit_continue_chain_head` 守卫判 False，
  随后 `_generate_with` 把 with 体发成 `If(pass)`；`_try_generate_conditional_break_or_continue`
  同一站点三次全返回 `None`：
  ```
  _b66_is_with_exit_continue_chain_head -> False
  _try_generate_conditional_break_or_continue -> None
  _generate_with -> dict{"type":"With","items":[...],"body":[{"type":"If",...,"body":[{"type":"Pass"}]...
  ```
  触发形态：`while True → with <ctx> as f → if <cond>: continue`。

### 2.4 40 条的 (a)/(b)/(c) 分布

| 类 | 条数 | 依据 |
|---|---:|---|
| (a) 真缺陷 | **40** | 39 条 R1 的返回值实测不同；1 条 R6 原件抛/产物返回，直跑也复现（死循环 vs 4） |
| (b) 环境伪差 | **0** | 没有一条差异能被外部文件/随机/时间/路径解释；`original_stderr`/`product_stderr` 全空 |
| (c) 尺子效应 | **0** | R1 差异都是真实返回值差异，不是口径问题 |

> 说明：`tests/` 里 `keep()`/`_A` 未定义的 fixture 缺陷只会让两边**同样**抛错，不制造 R1 差异；
> 唯一受影响的是 §3.4 的 r9_02（我们用注入 recorder 把它变成可观测的副作用差异）。

---

## 3. 69 条 R7-only：字段分布与「是否 T1/T2 同族」

### 3.1 字段分布（每条 entry 的 R7 diff 路径最内层字段，`r7_fields.py`）

| 字段组合 | entry 数 |
|---|---:|
| 仅 `co_code` | 48 |
| `co_code` + `co_stacksize` | 12 |
| `co_code` + `co_exceptiontable` + `co_stacksize` | 6 |
| `co_code` + `co_exceptiontable` | 3 |

diff 条目级计数（69 条共 120 条 R7 diff）：`co_code` **93**、`co_stacksize` **18**、
`co_exceptiontable` **9**；**`co_consts` 的「顺序 / 拼写 / 长度 / 死常量」= 0 条**。

### 3.2 与 r187 的 T1/T2（死常量）**不同族**

r187 的 T1/T2 签名是「`co_consts` 池子少一项 / 值被换成 True/False」，即
`$.metadata.code...co_consts.v[i].v` 或 `.co_consts.len` 上必有 diff。
这 69 条**一条都没有**：常量池逐字节一致，变的只是嵌套 code object 的 `co_code`（+ 栈深/异常表）。
它们的文本改动是**控制结构重整**，例如（`textdrift_by_pyc.txt`，基线 → 当前树）：

| pyc | 文本变化 | 直跑是否等价 |
|---|---|---|
| e02_g1_b98_hosts | `return a or (b and c)` → `return not a and b and c` | **否**（1 vs False） |
| r1_10_while_mixed | `while a and b or c:` → `if a: while b or c: ... if not a: break` | **否**（10 vs 0） |
| r9_02_b2_dual_continue | `keep(x); continue` → `continue; keep(x)`（keep 变死代码） | **否**（keep 副作用丢失） |
| rec1_synth_b70a | `if b: continue` + `use(f)` → `if b: pass else: use(f)` | 是 |
| c4_12_star_args | `f(*xs, *ys, **({'k': i}))` → `f(*xs, *ys, k=i)` | 是 |
| x02_for_deep_hosts | 多一个 `pass`；try/finally 拉直 | 是 |
| x05_with_deep_hosts | `break` 后多一个 `pass` | 是 |

⇒ **r187 修的是「推导式过滤位折叠臂的死常量」；这 69 条在 co_consts 上根本无差，不在同一族**，
r187 的族级谓词（`_b256_filter_boolchain` / `_fold_arm_value` / `_try_folded_true_arm`）覆盖不到它们。
r187 没覆盖到的原因不是漏了同一族，而是**族不同**（BoolOp 条件重整 / continue-pass / try-finally 折叠）。

### 3.3 69 条里藏着 42 条真缺陷（R1 的盲区）

判官只在 entry 声明的 `call_exprs` 上比 R1。这 10 个 pyc 里被文本改动到的 def，
很多**不在**该 pyc 各 entry 的 call 列表里，于是「行为维全绿、只有 R7 红」。
为了不靠肉眼，本次对**每个被改动的 def** 用原件 pyc 与当前产物**各自真跑**同一组入参
（`probe_func.py`，每调用一个子进程 + 5s 超时；`latent_behavior.json`，33 次调用）：

| pyc | 改动函数 | 实测差异 | 归属 |
|---|---|---|---|
| e02_g1_b98_hosts | `f_match_arm_host(1,1,1,'zz')` | `1` vs `False` | (a) 潜伏 |
| r1_10_while_mixed | `f(0,1,1)` | `10` vs `0` | (a) 潜伏 |
| r9_02_b2_dual_continue | `break_continue_mix([0,1,-1],False,False)` | 原件 `keep` 被调 3 次，产物 **0 次** | (a) 潜伏 |
| x02_for_deep_hosts | `for_in_while()` / `for_in_try()` | `2`/`3` 相同 | (c) |
| x05_with_deep_hosts | `with_in_while()` | 两边同 `NameError: _A` | (c) |
| c4_12_star_args | `e04_deep(marker,[1,2],[3])` | `('called',(1,2,3),[('k',1)])` 相同 | (c) |
| rec1_synth_b70a | `wbc(tmp,1,0)` / `wbc(tmp,1,1)` / `wbc(tmp,0,1)` | 全相同 | (c) |

⇒ 69 R7-only 拆分：**42 条 (a) 潜伏**（e02 18 + r1_10 12 + r9_02 12）、**27 条 (c) 尺子效应**。

> 42 条 (a) 的 (a) 与 40 条行为维的 (a) 是同一性质：**产物文本错了，只是判官的 call 列表没碰到**。
> 它们不是「已通过的条目」——它们证明 `r7_only_different` 这个读数同时混了 (a) 和 (c)。

### 3.4 r9_02 的一处细节

`r9_02_b2_dual_continue.py` 的 `keep()` 在 fixture 里**从未定义**（原文即如此），
所以原件直跑会 `NameError`。为把「控制流差异」和「fixture 缺函数」分开，探针在两边都注入同一个
`keep` recorder，再比调用序：原件 `["0","1","-1"]`、产物 `[]` ⇒ 差异是**控制流**造成的，不是环境。

---

## 4. 真缺陷优先级（按影响面）

| # | 根因（core/cfg 具体函数） | 影响 entry | 后果 | 触发形态 |
|---|---|---:|---|---|
| 1 | `region_ast_generator.py::_generate_if`（boolop_child 只在 `entry==entry` 时认领） | **20** | 返回值错（1→0）；同产物另一函数 `while` 丢 `break` → **死循环** | `for/if: if i: (a and b) or c or d:` |
| 2 | `region_ast_generator.py::_generate_try`（`_count_nested_try_marker_levels==0`） | **19** | 返回值错（8 项→6 项，1/2 顺序反） | `for → try → try → if: continue → finally → finally` |
| 3 | `region_ast_generator.py::_build_boolop_expression_inner`（De Morgan 化） | **18** | 返回值错（`a or (b and c)` → `not a and b and c`） | 混合 and/or 的**值上下文** Return/BoolOp |
| 4 | `region_ast_generator.py::_loop_generate_while`（发出的 test 只剩 `b or c`，`a` 被提升成 `if a:` 守卫；**识别端未定死**） | **12** | 返回值错（10→0） | `while a and b or c:` |
| 5 | 未定死（continue 与后继语句的顺序被对调，`keep(x)` 成死代码；同 pyc 的 `_detect_boolop_*` 未命中） | **12** | 副作用丢失（`keep(x)` 0 次调用） | `for → if b: continue → keep(x)` |
| 6 | `region_ast_generator.py::_b66_is_with_exit_continue_chain_head` → `_generate_with` | **1** | 死循环 vs 返回 4 | `while True → with ctx → if a: continue` |

（1–5 的根因均由 trace 的**调用 digest** 直接指认，唯 #5 只拿到「顺序对调」的产物证据、
未抓到具体 emitter；#6 在同一站点上由 `_b66_...->False` + `_generate_with` 的 `If(Pass)` 指认。）

---

## 5. 复现命令与产物

```powershell
cd F:\Downloads\pythoncdc-main

# 1) 109 条复算（decompile + judge）
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\recompute109.py `
   --out D:\temp\opencode\cl_layout\drift\drift109_raw.json `
   --products D:\temp\opencode\cl_layout\drift\products

# 2) 40 条完整 diff + 观测（R1 明细）
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\dump40.py

# 3) 40 条最小复现：编译 / 反编译 / pyc_verify single / judge / 直跑
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\build_repros.py

# 4) 潜伏差异探针（每个被改动 def 在两边真跑）
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\latent.py

# 5) R7 字段分布 / 文本漂移 / 根因 trace
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\r7_fields.py
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\textdrift.py
$env:PYTHONPATH='F:\Downloads\pythoncdc-main'
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\drift\trace_emit.py  <repro.pyc> <out.py> <log>
```

产物清单：

| 路径 | 内容 |
|---|---|
| `fresh/gate_drift/drift_109.json` | **任务 1 交付**：109 条 × `{entry_id, pyc, r7_only, dims, diffs(前3), product_sha, class, repro, latent}` |
| `fresh/gate_drift/repro/*.py` | 40 份最小复现（≤15 行，逐条一份） |
| `fresh/gate_drift/repro/MEASURED.json` | 每条的 `pyc_verify` 状态 + judge R1 + 直跑两边输出 |
| `fresh/gate_drift/repro_pyc/`、`repro_products/` | 复现的 pyc 与当前树产物 |
| `fresh/gate_drift/DRIFT_109.md` | 本报告 |
| `fresh/gate_drift/evidence/` | `drift109_raw.json`、`drift109_full.json`、`drift40_full.json`、`latent_behavior.json`、`textdrift_by_pyc.txt`、`r7_fields.json`、`changed_defs.json` |
| `D:\temp\opencode\cl_layout\drift\` | 全部脚本 + 中间产物（同上，脚本在根） |

---

## 6. 边界

1. 42 条 (a) 潜伏的「真缺陷」判定基于**对改动 def 的定向真跑**（每 def 2–6 组入参），
   不是穷举；对被测入参之外是否还有更大差异未做穷举证明。
2. 27 条 (c) 的「行为不变」同理是**未观察到差异**，不是形式化等价证明。
3. D1 的第二处（`f_b98_while_cond_pos` 丢 `break`）由 pylingual 的
   `Different control flow` + 直跑死循环证实，但其 emitter 未逐函数定死（与 `_generate_if` 同产物）。
4. 109 条集合本身依赖 r187 的全量重跑产物 `semantic_r187_merged.json` 作为「当前树读数」；
   本次对 109 条**逐条重跑**并全部复核为非 EQUAL，未复核其余 1042 条。
