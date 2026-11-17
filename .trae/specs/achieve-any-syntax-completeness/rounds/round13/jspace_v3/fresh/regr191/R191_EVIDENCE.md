# rr-v5r191 — e02 回归收窄：De Morgan 极性反转（[v172-NEGAND] 弹栈族判据）

树：`F:\Downloads\pythoncdc-main`（未 commit / 未 push）；解释器 `D:/Python/python.exe -I -X utf8`，
cwd=仓库根；判官 `scripts/pyc_verify.py single`。
补丁：`D:\temp\opencode\cl_layout\r191\fix191.py`（anchor `count==1` / utf-8-sig / BOM `efbbbf` 单头 /
`py_compile` / 幂等 / `--revert` 往返 sha 一致）。
改动：`core/cfg/region_analyzer.py` **+17 / −2**（唯一程序文件；两处 hunk：判据 + docstring C2）。

---

## 0. 结论

- **根因**：r172 `9d236f9d` 的 `_v172_negated_and_operand_op_types` 把「末成员 FALSE 极性跳转 ⇒
  其目标 = and 链失败出口」当成充分条件，但该前提只对**弹栈型条件跳转**（`POP_JUMP_*`）成立。
  值语境的 `JUMP_IF_TRUE_OR_POP` 是**保值型**短路跳转（跳转时把操作数留作表达式结果送往 merge），
  于是 `a or (b and c)` 的链 `[(JUMP_IF_TRUE_OR_POP,'or'), (JUMP_IF_FALSE_OR_POP,'and')]`
  （两条短路目标重合于同一 merge）被误判为「负极性 and 链」，or 成员被改标 `'and'`，
  构建层再按 TRUE 极性补隐式 `not` ⇒ `not a and b and c`。附带：L34138 的
  `'FALSE' not in last_i.opname` 闸门对 `JUMP_IF_FALSE_OR_POP` 也成立（子串命中），不构成区分。
- **收窄**（`[v191-POPPOL]`）：候选成员**还**必须是 `CONDITIONAL_JUMP_OPS` 成员（弹栈族）；
  接受集合是 r172 的严格子集，不命中逐位不变（C3），判据只读成员末指令 opcode/argval（I.4 白名单 / [C1]）。
- **结果**：`e02_g1_b98_hosts` **16/18 → 18/18**，产物 `b87f2cd1590d49be` → **`9f4b826eed3298d7`**
  （= r171 正确产物）；直跑 57/57 与原件一致；r172 原始收益逐字节保留（subprocess `557b9b0bfe9e`、75/78）。

## 1. 复现（收窄前）

| 项 | 读数 |
|---|---|
| 产物 sha16 | `b87f2cd1590d49be` |
| 判官 | `failure 16/18`（`<module>.CB98.m_class_body_host`、`<module>.f_match_arm_host`：Different bytecode） |
| 产物文本 | 两处 `return a or (b and c)` → `return not a and b and c` |
| 直跑 | `CB98().m_class_body_host(1,1,1)` 原件 `1` / 产物 `False`；`f_match_arm_host(1,1,1,'zz')` 同理 |

**18 条 J 条目对应的函数/源码形态**（`test_repros/round3/e02_g1_b98_hosts.py`）：

| 单元 | 源码 | 受影响 |
|---|---|---|
| `<module>`(M1/M2) | `(_P or _Q) and _R` / `_P or (_Q and _R)` | 否（赋值语境由块布局复原） |
| `CB98`(C1/C2) | 同上 | 否 |
| `CB98.m_handler` | `return (a or b) and c` + try/except + 三元 | 否 |
| **`CB98.m_class_body_host`** | **`return a or (b and c)`**（L24） | **是** |
| `f_comp_cond_host` / `f_genexp_cond_host` / `f_dictcomp_value_host` | `(a or b) and c`（推导式条件位） | 否 |
| `f_nested_func_host` / `f_with_body_host` / `f_try_body_host` | `(a or b) and c`（宿主） | 否 |
| **`f_match_arm_host`** | `case 1: return (a or b) and c` / **`case _: return a or (b and c)`**（L68） | **是** |

即：**本仓 `or` 之下嵌 and 组、且处于值语境（return）** 的形态才翻转；`(a or b) and c`
与条件语境 `if a or (b and c)` 均不受影响（后者 or 成员 TRUE 目标 = then 块 ≠ exit）。

## 2. 根因（插桩实测，非阅读猜测）

探针 `dbg_chain2.py`（只包装 `_v172_negated_and_operand_op_types`，打点链成员末指令 opcode/argval）：

```
收窄前 e02：chains=12 converted=4
  <module>            JUMP_IF_TRUE_OR_POP off=38   or -> and
  CB98                JUMP_IF_TRUE_OR_POP off=32   or -> and
  m_class_body_host   JUMP_IF_TRUE_OR_POP off=50   or -> and      ← 病形
  f_match_arm_host    JUMP_IF_TRUE_OR_POP off=80   or -> and      ← 病形
收窄后 e02：chains=12 converted=0
```
（`<module>`/`CB98` 两处的改标不改变产物：赋值语境 `_build_boolop_expression_inner` 由块布局
复原 `_P or (_Q and _R)`；但判据本身同样是错的，收窄后一并消失。）

关键行（收窄前 L34153–34155）：
```python
if (_li is not None and 'TRUE' in _li.opname
        and getattr(_li, 'argval', None) == exit_off):
    op = 'and'
```
`exit_off` 由 L34138–34140 取「末成员末指令 opname 含 `FALSE` 的 argval」——对
`JUMP_IF_FALSE_OR_POP` 同样成立，故值语境的两条短路目标（winner merge）被当成 and 链失败出口。

r172 原目标形态（同插桩，subprocess 语料）：

```
subprocess：chains=33 converted=1（收窄前后逐字节相同）
  _execute_child  POP_JUMP_FORWARD_IF_TRUE off=610  or -> and   （3 个成员）
```
即 `not close_fds and not pass_fds and cwd is None` / `not start_new_session and
process_group == -1` 的负极性合取项 —— 全部是**弹栈型** `POP_JUMP_FORWARD_IF_TRUE`，
收窄后照旧改标；`Popen._check_timeout` 的 raise 表达式收益（r172 ①②）不经本函数，未受影响。

## 3. 收窄（只收窄，不回退）

```python
if (_li is not None and 'TRUE' in _li.opname
        and _li.opname in CONDITIONAL_JUMP_OPS      # [v191-POPPOL] 新增唯一条件
        and getattr(_li, 'argval', None) == exit_off):
```
| | 收窄前 | 收窄后 |
|---|---|---|
| 候选判据 | TRUE 极性且目标 == exit_off | **+ 弹栈型条件跳转（`CONDITIONAL_JUMP_OPS`）** |
| `JUMP_IF_TRUE_OR_POP`（保值型，目标 = 值 merge） | 放行（病形） | 跳过（C3：逐位不变） |
| `POP_JUMP_FORWARD/BACKWARD_IF_TRUE`（弹栈型，目标 = 失败出口） | 放行 | 放行（逐字保留） |
| 接受集合 | — | r172 的**严格子集** |
| 判据来源 | 成员末指令 opcode/argval | 同（I.4 白名单；无名字/偏移/阈值/新状态） |

## 4. 验证读数（全部实测）

### 4.1 回归案 e02
| 项 | 收窄前 | 收窄后 |
|---|---|---|
| 产物 sha16 | `b87f2cd1590d49be` | **`9f4b826eed3298d7`** |
| 判官 | failure 16/18 | **success 18/18** |
| 直跑（57 例：M1/M2/C1/C2 + 8 函数 × 多组实参） | **7 DIFF**（两函数返回 `False`） | **0 DIFF** |

### 4.2 前置回归（A/B）
| 案 | 收窄前 | 收窄后 |
|---|---|---|
| `e01_g1_b98_matrix` | `e5b02d5ef81ebf46` 15/15 | **同 sha，15/15**（SAME） |
| `v_b71_face` | `010ad39367f036fa` 4/4 | **同 sha，4/4**（SAME） |
| `r9_02_b2_dual_continue` | `bb86df782296d705` 5/5 | **同 sha，5/5**（SAME） |

### 4.3 五语料（与收窄前逐字节比较 + 判官）
| 语料 | sha12 | 判官 |
|---|---|---|
| request | `db2172e8f1a6` SAME | 194/194 |
| tarfile | `8b35ed1396ac` SAME | 158/160（`TarFile.add`、`main` 既有） |
| cookiejar | `d39c77eeb677` SAME | 103/105（`_timegm`、`set_ok_path` 既有） |
| subprocess | `557b9b0bfe9e` SAME | 75/78（`__init__`、`_internal_poll`、`_wait` 既有） |
| difflib | `d70df6006a50` SAME | 62/62 |

### 4.4 J 空间
- 只有 e02 系 pyc 的产物字节变动 ⇒ 取 e02 的 **18 条** J 条目重跑 `semantic_runner.py`：
  **18/18 EQUAL（covered_5tuple）**，产物与本树一致。
- overlay 进 r190 冻结集（`work/semantic_r191_frozen_plus.json`，replaced=18）后
  `coverage_checker`：**covered_5tuple = 1174**（= r190 值，未下降），
  `r7_only_different=6`、`uncovered=382`、`J_total=1556` 不变。

### 4.5 458 电池（old = 收窄前树 `r191/base`，new = 收窄后树，8 分片合并）
`rows=458`；**TEXT-DIFF 0/458**（⇒ ⊆ 17 项允许集，`extra=[]`，`all-byte-equal=True`）；
`C7_skipedge = TEXT-SAME`；`NO-SRC 0`、`COMPILE-ERR 0`；
458/458 行 `(text, sig)` 与 **r190 电池读数逐行相同，changed=NONE**（R110 组 169 案同值）。

### 4.6 AST 剪枝
- 五语料 `(If, stmt, Pass)`：request 286/1725/17、tarfile 324/1750/12、cookiejar 240/1213/8、
  subprocess 270/1125/22、difflib 114/737/9 —— **收窄前后逐项相同**。
- e02：模块 (10, 68, 0) 三树同值；`CB98.m_class_body_host` 源 (1,5,0) / base (1,5,0) / fix (1,5,0)；
  `f_match_arm_host` 源 (1,7,0) / base / fix 同 → **无语句减少、无幻影 `pass`**。

### 4.7 红线
五语料 `text=SAME`，逐 code object `changed=NONE`（request 184 / tarfile 157 / cookiejar 104 /
subprocess 66 / difflib 59 个 code object）；tarfile/cookiejar/subprocess 各 12 具名单元 **36/36 BYTE-SAME**。

### 4.8 全量影响面（普查 2507 pyc × 2 树，逐 pyc 产物 sha A/B）
`test_repros/` + `.trae/specs/` + `_b142_probes` + 五语料，>1.5MB 的 `_chk*` 排除；**0 ERR**。
**产物变化恰 8 个**，全部是 e02 形态族：

| pyc | 收窄前 | 收窄后 |
|---|---|---|
| `test_repros/round3/e02_g1_b98_hosts.pyc`（+6 个 rec1_/name_/synth_ 派生） | 16/18 | **18/18**（`rec1_synth_e02host_a` 5/6 → **6/6**） |
| `.../jspace_v3/.../shard0/__pycache__/JS-IF-043.cpython-311.pyc` | 16/18 | **18/18** |
| `.../round6/offcorpus/repo_core_cfg_builder.pyc` | 37/42 | 37/42（同 5 个失败单元，**文本转正**：`is_leader = instr.offset in self.jump_targets or …` 而非 `not instr.offset in … and …`） |

判官 A/B：**0 个单元由通过转失败**（variants 全部升到满额）。

### 4.9 卫生
- `scripts/validate_region_generator_signatures.py` → **`统计: 14 个错误, 6 个警告`**（与 r189/r190 同值）。
- `core/cfg/region_analyzer.py`：首 3 字节 `efbbbf`，BOM 计数 **1**，`\r\n` **0**、`\n` 39709（全 LF）。
- `git status`（tracked）：仅 `core/cfg/region_analyzer.py` M（另一条 `.trae/.../r10v10_fv_iv2.json`
  为本轮开始前既有改动，未触碰）；`git diff --numstat` = `17 2 core/cfg/region_analyzer.py`。
- `fix191.py`：apply → `352d42345639…`；二次 apply skip；`--revert` → `3641f94d84d7…`（= 改前原文 sha256）；
  再 apply → `352d4234…`；独立副本（`r191/rt`）上同样往返一次，结果一致；两向均过 `py_compile`。

## 5. 复现命令

```powershell
cd F:\Downloads\pythoncdc-main
D:/Python/python.exe -I -X utf8 pycdc.py test_repros/round3/e02_g1_b98_hosts.pyc -o <out>.py
D:/Python/python.exe -I -X utf8 scripts/pyc_verify.py single test_repros/round3/e02_g1_b98_hosts.pyc --source <out>.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\gate\cases191.py        # e01/v_b71/r9_02/e02 A/B
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\gate\corpus_run191.py   # 五语料 + 判官
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\gate\redline191.py     # 红线
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\gate\ast191.py         # AST
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\gate\judge_changed191.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\merge_census191.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\merge_battery191.py    # 需先跑 battery191.py 0..7
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r191\overlay191.py
D:/Python/python.exe -X utf8 tools\completeness\coverage_checker.py --space .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_b275.json --evidence D:\temp\opencode\cl_layout\r191\work\semantic_r191_frozen_plus.json --out D:\temp\opencode\cl_layout\r191\work\coverage_r191_frozen_plus.json
```

## 6. 产物清单（`D:\temp\opencode\cl_layout\r191`）
`fix191.py`、`census191.py`/`build_list191.py`/`merge_census191.py`、`merge_battery191.py`、
`battery191.py`、`overlay191.py`、`mk_space_e02.py`、`behave191_e02.py`、`dbg_chain2.py`、
`gate/{corpus_run191,redline191,ast191,judge_changed191,cases191}.py` +
`gate/{corpus191,redline191,ast191,cases191,changed191,behave191_e02*}.*`、
`census/{base,fix}_0..7.json`、`base/`（收窄前冻结树）、`rt/`（往返副本）、
`work/{space_e02,semantic_r191_e02,semantic_r191_frozen_plus,coverage_r191_frozen_plus}.json`、
`log/conv_{sub,e02}_*.txt`。
