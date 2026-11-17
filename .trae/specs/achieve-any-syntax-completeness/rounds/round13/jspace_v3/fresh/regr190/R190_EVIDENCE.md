# rr-v5r190 — D2 回归收窄：嵌套 try/finally 的 finally 对调（[v124-LOOPHEAD] 宿主环判据）

树：`F:\Downloads\pythoncdc-main`（未 commit / 未 push）；解释器 `D:/Python/python.exe -I -X utf8`
补丁：`D:\temp\opencode\cl_layout\r190\fix190.py`（anchor `count==1` / utf-8-sig / BOM `efbbbf` 单头 /
`py_compile` / 幂等 / `--revert` 往返 sha 一致）
改动：`core/cfg/region_analyzer.py` **+11 / −1**（唯一程序文件；单 hunk；全 LF；BOM 保持）

---

## 0. 结论速览

- **D2 根因**：r124 `0c6308fc` 的 `[v124-LOOPHEAD]` 重挂 pass 的宿主环判据
  `if _lp is not _p and _lp is not None:`（口径名「L 与 child 同宿：`L.parent is P` **或** `L.parent is None`」）。
  第二个分支（`L.parent is None`）放行的正是「环是 P 的**祖先**」拓扑
  （`for → try(外层) → try(内层)`：P 本身就在环体内）。此时 child 相对 P 的位置在环之下，
  把它从 P 重挂到环 = 把 P 的真子节点拍平成环的兄弟 ⇒ 两层 finally 的正常/异常副本谱系错位。
- **收窄**：`[v190-LOOPHOST]` —— **只删掉 `or L.parent is None`**，保留 `L.parent is P` 与既有防环守卫；
  接受集合是 r124 的**严格子集**（只留下「环被吸收成 P 的子节点」的 `/iterfind` 病形）。
  判据只读区域树父子关系（[C1] 同层结构事实），无数字上限（§2.2），未新增方法名（§2.1）。
- **结果**：`v_b71_face` 判官 **3/4 → 4/4**，产物 sha16 `ce39c5a6…` → **`010ad39367f036fa`**
  （= r123 正确产物 = G3 快照），直跑与原件逐项相等；r124 的原始收益（`/iterfind`，ElementPath
  **39/39**）逐字节保留；五语料、458 电池、红线、AST 全部零漂移。

---

## 1. 复现（收窄前，本轮起点）

| 项 | 读数 |
|---|---|
| 产物 sha16 | `ce39c5a6d479128a` |
| 判官 | `failure 3/4`（唯一失败单元 `<module>.v_nest_fin_continue: Different control flow`） |
| 直跑 `v_nest_fin_continue([0,1,-1])` | 原件 `[1,2,1,2,1,1,2,-1]` / 产物 `[2,1,1,1,1,-1]` |
| 产物文本 | 内层 `finally: out.append(1)` 与外层 `finally: out.append(2)` 对调，内层 try 退化成 `pass` |

字节码（同版本 3.11.7）：外层 try 入口 18、内层 try 入口 30；正常副本
`32..72`（内层 1）、`120..162`（内层 1）、`74..116`（外层 2）、`216..260`（外层 2）；
异常副本 `164..208`（内层 1）+ handler `210`、`262..306`（外层 2）+ handler `308`。

## 2. 根因（层级探针实测，非阅读猜测）

探针 `probe/hier.py`（只包装 `_build_region_hierarchy` / `_generate_try`，不改树）：

```
收窄前（base） v_nest_fin_continue：
  LoopRegion@10  body=[10,12,18,30,32,74,118,120,216,314]  children=[Try@18, Try@30]
  Try@18  finally=[164,210] copy_keys=[32,120]  parent=Loop@10   <== 被 v124 重挂
  Try@30  finally=[262,308] copy_keys=[74,216]  parent=Loop@10
  生成：_generate_try(18) -> Try(body=[If], finalbody=[append(1)])   [外层帧，内层 finally]
        _generate_try(30) -> Try(body=[Pass], finalbody=[append(2)]) [内层帧]
去掉 v124 块（t_nov124）：
  Try@18 parent=Try@30（Try@30.children=[Try@18]）
  生成：_generate_try(30) -> Try(body=[Try], finalbody=[append(2)])
        _generate_try(18) -> Try(body=[If],  finalbody=[append(1)])  ⇒ 与源码同形
```

- 主裁决（`_build_region_hierarchy` 主循环 L38772–38786）本来把 Try@18 挂到 Try@30：
  容器候选 `Try@30` 区间 (18,308) 罩住 child (18,210)，走
  `_container_cands and _loop_cands` 分支取容器。
- v124 pass 在其后运行：`child=Try@18`、`P=Try@30`（TryExceptRegion）、`L=Loop@10`，
  `child.entry(18) ∈ L.body_blocks` ✔、`L.entry(10) ≠ P.entry(18)` ✔，而 `L.parent is None`
  （环是根 = **P 的祖先**）⇒ 旧判据的 `or L.parent is None` 分支放行 ⇒ 重挂到 Loop@10。
- 重挂后 Try@30 不再是 Try@18 的父：`_generate_try(Try@30)` 的 try 体（`[30,74,118]`，全是副本/胶水 NOP）
  发成 `pass`；`Try@18` 以「外层帧 + `append(1)`」先发射 ⇒ 两层 finally 对调。
- 判据名：**`[v124-LOOPHEAD]` 宿主环判据（`L.parent is P` 或 `L.parent is None`）**；
  关键行（收窄前 L38923–38925）：
  ```
  _lp = _lr.parent
  if _lp is not _p and _lp is not None:
      continue
  ```

## 3. 收窄（只收窄，不回退）

```python
_lp = _lr.parent
# [v190-LOOPHOST] 宿主环 L 必须是现父 P 的直接子节点（L.parent is P）……
if _lp is not _p:          # 原：if _lp is not _p and _lp is not None:
    continue
# L 不得是 child 的后代（防环）  ← 以下逐字不动
_anc = _lp
_cyc = False
while _anc is not None:
    if _anc is child:
        _cyc = True
        break
    _anc = _anc.parent
if _cyc:
    continue
```

| | 收窄前 | 收窄后 |
|---|---|---|
| 拓扑判据 | `L.parent is P` **或** `L.parent is None` | **仅** `L.parent is P` |
| `L→P`（环是 P 的祖先，P 在环体内） | 放行（**病形**：v_b71 / B142 嵌套 finally 族） | 跳过（C3：逐位不变） |
| `P→L`（环被吸收成 P 的子节点，`/iterfind` 形） | 放行 | 放行（逐字保留） |
| 防环 / `entry` 判据 / 块判据 | 原有 | **逐字不动** |
| 接受集合 | — | r124 的**严格子集**（无新增接受面） |
| 判据来源 | 区域树父子关系 | 区域树父子关系（I.4 白名单；无偏移/名字/阈值/新状态） |

## 4. 验证读数（全部实测）

### 4.1 回归案

| 项 | 收窄前 | 收窄后 |
|---|---|---|
| `v_b71_face` 产物 sha16 | `ce39c5a6d479128a` | **`010ad39367f036fa`** |
| 判官 | failure 3/4 | **success 4/4** |
| 直跑 `[0,1,-1]` / `[0,1]` / `[1,0,2]` / `[]` | 全部 DIFF | **全部 SAME**（`v_fin_else_continue`、`n_fin_noctrl` 也 SAME） |
| `finally` 体语句形状（源码/产物） | 内层=1、外层=2 对调 | `[['Expr'],['Expr']]` 逐项相同；函数语句数 11 = 源码 11 |

### 4.2 r124 原始收益核查（`[v124-LOOPHEAD]` 在哪些案例有效）

层级命中普查（`probe/census.py`，打点即 pass 真正重挂的站点，`fn, child.entry, P.entry, L.entry`）：

| 案例 | 站点 | 收窄后 | 判官/文本 |
|---|---|---|---|
| `stdlib_xml_ElementPath.pyc::iterfind` | (652,150,492)、(494,150,492) | **仍重挂**（L.parent is P） | 39/39，文本逐字节不变 |
| `subprocess.pyc::Popen.__init__` | (3310,2700,3304) | **仍重挂** | 75/78，文本逐字节不变（仅层级） |
| `subprocess.pyc::Popen._on_error_fd_closer` | (126,12,120) | **仍重挂** | 同上（该单元 BYTE-SAME） |
| request / tarfile / cookiejar / difflib | 无站点 | — | 逐字节不变 |
| `x10_handler_hosts::h_basic` | (78,4,64) | 仍重挂（同站点） | 文本逐字节不变 |
| `r2_05_try_loop_try` / `rv3_01_b87_try_loop_mix` / `x02_for_deep_hosts` / `r7v7_b4a02` | 各自 1–2 站点 | 仍重挂 | 逐字节不变 |
| `real_run_individual_transform` | (686,640,586) | **不再重挂**（L 为根） | 文本逐字节不变 |

收窄后全库命中面：**52 个 pyc** 仍触发重挂（对应 r124 的原始收益面），其中产物文本变化的只有 §4.3 的 14 个。

- **收益量化**：把 v124 整块删掉（`t_nov124`）⇒ ElementPath 产物 `6860b2260dfc3e76`、判官
  **38/39**（`iterfind: Different control flow`）；保留（收窄后）= **39/39**、`3bb3eb9e55f03387`。
  五语料在 `t_nov124` 下与本树逐字节相同（r124 对五语料无文本收益）。
- 结论：r124 的**唯一**文本收益（`/iterfind`）在收窄后逐字节保留；五语料侧无收益可失。

### 4.3 全量受影响面（普查 2965 个 pyc × 2 树；文本变化 14 个，判官逐条 A/B）

普查范围：`test_repros/`(1062) + `.trae/specs/`(1438) + `_b142_probes/` + r189 电池 458 + 五语料 +
ElementPath + `v_b71_face`，共 2968 个 pyc；3 个 2MB 级 `_chk*.pyc`
（`region-reduction-30pyc-perfect-10rounds/…/logs/`）排除，实跑 **2965/2968**（两树同集）。
结果：**产物 sha 变化恰 14 个 pyc**；与「祖先链（descendant）」备选收窄的 14 个产物**逐字节相同**，
故判官读数共用 A/B 表：

| pyc | 收窄前 | 收窄后 |
|---|---|---|
| `v_b71_face` / `JS-IF-017`(product pyc) / `l0_d4_repl_v_b71_face` / `rec1_v_b71_face*3` | 3/4 | **4/4** |
| `p_g1_fin_paths` | 1/3 | **3/3** |
| `p_g2_loopctrl` | 1/3 | 2/3（`g2_cont` 由失败转通过） |
| `p_g3_double_fin` | 1/3 | 2/3（`g3_two_fin` 转通过；`g3_three_fin` 仍失败=既有 B142 缺口） |
| `l3_b142_nested_finally_copy` | 1/3 | 2/3 |
| `l3_g7b_r8_finally_sideeffect` | 3/4 | **4/4** |
| `repro_r2_06_nested_try_else` | 1/2 | **2/2** |
| `l0_a3_triple_nested_finally_continue` | 1/2 | 1/2（单元不变） |
| `l3_g7_r8_finally_conditional_return` | 1/3 | 1/3（单元不变） |

判官 A/B：**0 回退**（无一单元由通过转失败），10 个升到满额，2 个部分上升，2 个单元读数不变。

B142 探针（`rounds/round12/probes_b142/` + `_b142_probes/`）直跑：`g1_fin_normal`、
`g1_fin_raise_in_try`、`g2_cont`、`g3_two_fin`、`v_nest_fin_continue` 全部回到原件输出；
`g2_brk`、`g3_three_fin` 在**收窄前后都**与原件不同（既有缺口，判官单元数不变）；
`p1_single`/`p2_shapes`/`p3_match`/`p5_docstring` 判官 2/2、4/4、4/4、4/4 不变，`p4_nest_plain` 1/2 不变。

### 4.4 五语料（与 r189 基线逐字节比较）

| 语料 | sha12 | vs r189 | 判官 |
|---|---|---|---|
| request | `db2172e8f1a6` | SAME | 194/194 |
| tarfile | `8b35ed1396ac` | SAME | 158/160 |
| cookiejar | `d39c77eeb677` | SAME | 103/105 |
| subprocess | `557b9b0bfe9e` | SAME | 75/78 |
| difflib | `d70df6006a50` | SAME | 62/62 |

### 4.5 J 空间（任务口径：冻结 r187/r189 证据 + 仅替换产物变化条目）

- J 空间 1180 条 callable 只落在 **124 个 pyc**；`base` vs 收窄后逐 pyc 比对：**仅 1 个 pyc 变化**
  （`v_b71_face.pyc` ⇒ 19 条 JS-*：CONTINUE-010/029、IF-017/021/088/090/097/102、
  RAISE-016/034、TRY-004/005/046/047/076/083/084/092/093）。
- 这 19 条用本树重跑 `tools/completeness/semantic_runner.py`：**19/19 EQUAL（covered_5tuple）**，
  产物与仓库产物逐字节相同（`010ad39367f036fa`）。overlay 进 r189 冻结集
  （`work/semantic_r190_frozen_plus.json`）后 **covered_5tuple = 1174**（= r189 值，未下降；
  这 19 条在冻结记录里本就是 EQUAL，刷新后仍 EQUAL，逐条见 `work/semantic_r190_vb71.json`）。
  `r7_only_different=6`、`semantic_failures=6` 不变。

### 4.6 458 电池（old = 收窄前树，new = 收窄后树，8 分片合并，new 侧全量重建）

`rows=458`；**TEXT-DIFF 0/458**（⇒ ⊆ 17 项允许集，`extra=[]`，`all-byte-equal=True`）；
`C7_skipedge = TEXT-SAME`；`NO-SRC 0`、`COMPILE-ERR 0`；
R110 组 169 案逐案 `(text, sig)` 与 r189 电池行 **458/458 相同，changed=NONE**。

### 4.7 AST 剪枝

- 五语料 `(If,stmt,Pass)`：request 286/1725/17、tarfile 324/1750/12、cookiejar 240/1213/8、
  subprocess 270/1125/22、difflib 114/737/9 —— **与 r189 逐项相同（EQUAL）**。
- `v_b71_face`：源码 (5,33,0) / 收窄前 (5,34,1) / **收窄后 (5,33,0)**；
  `v_nest_fin_continue` 源码 11 语句 / 收窄后 11（收窄前 12 + 1 个幻影 `pass`）；
  两处 `finally` 体形状 `[['Expr'],['Expr']]` 与源码一致（不重复、不丢失）。
- B142 探针语句数全部朝源码收敛（`g1_fin_normal` 9→10=源码 10、`g1_fin_raise_in_try` 11→12=12、
  `g2_cont` 11→12=12、`g3_three_fin` 12→14=14、`g3_two_fin` 13→12=12 且 Pass 1→0）。

### 4.8 红线

五语料 `text=SAME`、逐 code object `changed=NONE`；tarfile/cookiejar/subprocess 各 12 具名单元
**36/36 BYTE-SAME**。

### 4.9 卫生

- `scripts/validate_region_generator_signatures.py` → **`统计: 14 个错误, 6 个警告`**（与 r189 同值）。
- `core/cfg/region_analyzer.py`：首 3 字节 `efbbbf`，BOM 计数 **1**，`\r\n` **0**、`\n` 39694（全 LF）。
- `git status`（已跟踪）：仅 `core/cfg/region_analyzer.py` M（另一条 `.trae/.../r10v10_fv_iv2.json` 为
  本轮开始前既有改动，未触碰）；`git diff --numstat` = `11 1 core/cfg/region_analyzer.py`；单 hunk。
- `fix190.py`：apply → `3641f94d84d7…`；二次 apply skip；`--revert` → `a5e560e2…`（= 改前原文 sha256）；
  再 apply → `3641f94d…`；独立副本（`r190/base`）上同样往返一次，结果一致；两向均过 `py_compile`。

## 5. 复现命令

```powershell
cd F:\Downloads\pythoncdc-main
# 目标案
D:/Python/python.exe -I -X utf8 pycdc.py .trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc -o <out>.py
D:/Python/python.exe -I -X utf8 scripts/pyc_verify.py single <pyc> --source <out>.py    # 4/4
# 层级探针（R190_ROOT 指向冻结树；base=收窄前，t_fix=收窄后）
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r190\probe\hier.py <pyc> <out.py> v_nest_fin_continue
# 五语料 / 红线 / AST / 电池
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r190\gate\corpus_run190.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r190\gate\redline190.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r190\gate\ast190.py
for ($s=0; $s -lt 8; $s++) { D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r190\battery190.py $s 8 }
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r190\merge_battery190.py
# J 空间 overlay
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r190\overlay190.py
D:/Python/python.exe -I -X utf8 tools/completeness/coverage_checker.py --space .../judgment_space_v3m_b275.json --evidence D:\temp\opencode\cl_layout\r190\work\semantic_r190_frozen_plus.json --out ...
```

## 6. 产物清单（`D:\temp\opencode\cl_layout\r190`）

`fix190.py`、`overlay190.py`、`merge_battery190.py`、`battery190.py`、
`gate/{corpus_run190,redline190,ast190}.py` + `gate/{corpus190,redline190,ast190,behave190,judge14,judge_b142}.txt`、
`gate/{fix_products,b142,cmps,nov124,final14}`、`probe/{hier,treeop,census,join_census,cmp_trees,judge_pair,behave190}.py`、
`work/{space_vb71,semantic_r190_vb71,semantic_r190_frozen_plus,coverage_r190_frozen_plus}.json`、
`work/semantic_products_all/`、`cen/`（普查 2965 pyc × 2 树，`base_*` / `fix2_*`）、
`base/`（收窄前冻结树）、`t_fix/`、`t_nov124/`。
