# Task 118–121 终验残留逐条定性（x02_for_deep_hosts 6/7 · c4_12_star_args 12/13）

- 日期：2026-11-23；执行树：`F:\Downloads\pythoncdc-main`（main @ `767f50c4` = rr-v5r197，2026-11-23 08:18）
- 解释器：`D:/Python/python.exe -X utf8`（3.11.7）；判官：`scripts/pyc_verify.py single`（冻结）
- 本任务**零代码改动**：core/ scripts/ tests/ tools/ specs/ test_repros/ 全部未写；产物与证据全部落在本目录（residual2/）

---

## 0. 冻结校验（全部通过，不符即停——未触发停止）

| 文件 | SHA256 前缀 | 期望 | 结果 |
|---|---|---|---|
| `scripts/pyc_verify.py` | `FE1902A90CEBD4A15` | FE1902A90CEBD4A15 | ✅ |
| `D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py` | `9C7567BD6776B36B` | 9C7567BD6776B36B | ✅ |
| `test_repros/round2/x02_for_deep_hosts.pyc` | `9B22215422369DDD` | 9B22215422369DDD | ✅ |
| `test_repros/round4/c4_12_star_args.pyc` | `B72B77301CEC2713` | B72B77301CEC2713 | ✅ |

注：equivalence_check.py 实际路径是默认根目录下再进一层包目录（`<root>\pylingual\equivalence_check.py`），与 pyc_verify.py 装载逻辑一致。

---

## 1. 读数全景（6 次判定，逐次单跑）

| # | pyc | source 路线 | 读数 | 失败 unit |
|---|---|---|---|---|
| 1 | x02_for_deep_hosts.pyc | in-place `x02_for_deep_hostsOK.py`（d8590c9c，2026-10-25 刷新） | **success 7/7** | — |
| 2 | c4_12_star_args.pyc | in-place `c4_12_star_argsOK.py`（9836400d，rr-v2r04 2026-10-06，**从未刷新**） | **failure 7/13** | e02_shallow / e03_mixed / e04_deep / e06_nested.inner / CSA.m / e07_match_host（6 个） |
| 3 | x02_for_deep_hosts.pyc | `--source` HEAD 新产物（本目录 `_HEAD.py`） | **failure 6/7** | `***<module>.for_in_try: Different control flow` |
| 4 | c4_12_star_args.pyc | `--source` HEAD 新产物 | **failure 12/13** | `***<module>.e04_deep: Different bytecode` |
| 5 | x02 | `--source` FIXTEST（HEAD 产物仅恢复 for_in_try 内层 try/finally） | **success 7/7** | — |
| 6 | c4_12 | `--source` FIXTEST（HEAD 产物仅还原 e04 的 `**({'k': i})`） | **success 13/13** | — |

### 登记读数的路线澄清（重要观测）

tasks.md 2117–2122 登记的 6/7、12/13 出自 `fresh/gate_drift/drift_109_after.json`；其生成脚本
`gate_drift/drift_after.py` 的流程是 **pycdc（当时 HEAD）→ `--source <drift2 产物>` 判定**，`per_pyc.sha16`
是**反编译产物的哈希**（不是 pyc 的）。已核对：`drift2/x02_for_deep_hosts.py`=`E8E95F95676E9D7F`、
`drift2/c4_12_star_args.py`=`D114C14B842D5FF2`，与 drift_109_after.json 登记值逐字符一致。

本次以当前 HEAD（r197）重新生成的产物（`*_HEAD.py`）与 drift2（r193 时点）**逐字节相同**
（E8E95F95…/D114C14B…）⇒ **r194–r197 未改变这两个 pyc 的反编译输出**，登记读数在当前树逐条复现（#3、#4）。
所以两条均为**真残留**（不是 in-place OK.py 陈旧导致的假残留），进入逐条定性。

（in-place 路线的两个读数与登记不同属预期外但可解释：x02 的 OK.py 是 10-25 刷新过的且本身 7/7；
c4_12 的 OK.py 是 round4 时代旧产物，7/13 反而**差于** HEAD 产物 12/13——旧产物里 e02/e03/e06.inner/
CSA.m/e07 的错序/丢参在 HEAD 已全部修复，仅 e04_deep 与真残留重叠。见 §4 决策项。）

---

## 2. x02_for_deep_hosts —— 失败 unit `***<module>.for_in_try`（Different control flow）

### 2.1 三方源码对照

原始源码（tracked `test_repros/round2/x02_for_deep_hosts.py`，pyc 即由它编译，见 2.2 [A]≡[C]）：

```python
def for_in_try():
    try:
        for i in range(1):
            try:
                for j in range(1):
                    R = j
            finally:
                F = 1
    except ValueError:
        R = 2
    return 3
```

HEAD r197 产物（`residual2/x02_for_deep_hosts_HEAD.py` L21-29，**内层 try/finally 被拉直蒸发**）：

```python
def for_in_try():
    try:
        for i in range(1):
            for j in range(1):
                R = j
            F = 1          # ← finally 体被吸收为 for-i 体内的顺序语句
    except ValueError:
        R = 2
    return 3
```

应然形态（in-place OK.py 的同函数，d8590c9c 时代输出，冻结判据 7/7 接受）：与原始源码同构
（内层 `try: for j … finally: F = 1` 保留）。

### 2.2 pyc 侧证据（`residual2/x02_for_in_try_dis.txt`，marshal 载入 + dis）

[A] pyc 内 `for_in_try` code object —— 异常表 **7 条**，内层 finally 是独立保护区：

```
 40  LOAD_GLOBAL range … 68 GET_ITER        ← 内层 for-j 的迭代器构建也在保护区内
 70  FOR_ITER → 80 / STORE j / R=j / JUMP_BACKWARD
 80  NOP
 82  LOAD_CONST 1 / 84 STORE F / 86 JUMP_BACKWARD   ← 正常路径的 F=1
 88  PUSH_EXC_INFO / 90 LOAD_CONST 1 / 92 STORE F / 94 RERAISE   ← 异常路径同样执行 F=1
 96  COPY 3 / 98 POP_EXCEPT / 100 RERAISE
ExceptionTable:
  4 to 36 -> 104 [0]           ← 外层 try
  40 to 78 -> 88 [1]           ← 内层 try 体（含内层 for-j）→ finally 异常入口 88
  82 to 86 -> 104 [0]
  88 to 94 -> 96 [2] lasti     ← finally 异常路径自身的保护
  96 to 100 -> 104 [0]
  …
```

[B] HEAD 产物重编译后 —— 异常表仅 **3 条**：`40 to 78 -> 88`、`88 to 94 -> 96` 两条内层 finally 区域
**整体消失**；`PUSH_EXC_INFO/F=1/RERAISE`（88-94）异常路径代码不存在。F=1 只剩正常路径一份。

[A vs C]（pyc vs 原始源码重编译）：**逐指令一致** ⇒ pyc 确系 tracked 源的编译产物，基准无瑕。

### 2.3 差异的具体语法构造（三方对照结论）

**内层 `try/finally`（体为 for 循环）嵌套在 `外层 try/except → for-i` 之内时，region 重建丢弃该
finally 保护区**：finally 体被下放为 for-i 体内的顺序语句，异常表少 2 个区域、少整段异常路径
（`PUSH_EXC_INFO → F=1 → RERAISE`）。控制流图（含异常区域）真实不同 ⇒ 判据 "Different control flow" 准确。

### 2.4 根因初判

**反编译器缺陷（结构保真级，非行为级）**。证据链：

- 判据无伪差：dis 实测 [A]/[B] 异常表与指令序列真实不同（非超时/容差/unit 设计问题）；
- 非容差缺口：应然形态（OK.py 形态）过同一冻结判据 7/7（读数 #1），且 FIXTEST（读数 #5）把 HEAD 产物
  **仅恢复这一处**后 6/7→7/7——不需要放宽任何判据口径，需要的是反编译器恢复该构造；
- 行为维度无差（先前证据）：DRIFT_109.md §3.3 直跑 `for_in_try()` 两边同返 `3`；本语料 unit 中
  `F` 为局部变量、异常路径只写不读，故拉直在**该 unit 的可观测行为**上不可见——属"潜伏/保真"缺陷，
  非 82 条那类行为级错。但在 finally 有可观测副作用的变体（如全局/容器写入）下会出错。

疑似机理（初判，未动代码）：`core/cfg/region_ast_generator.py::_generate_try` 一族对
`_count_nested_try_marker_levels`/嵌套 try 的记账（Task 119/r190 修的是 D2 形态
`for→try→try→if:continue→finally→finally`，`_build_region_hierarchy` 删 `or L.parent is None`）；
x02 形态是**另一拓扑**（外层 try/except → for → 内层 try/finally → for），未被 r190 覆盖，
内层 finally 区域在层级裁决中被丢弃。

### 2.5 修复建议草案（只建议，不实现）

在 try/finally region 重建处增加对下述形状的接受：外层 try 存在时，for-i 体内若存在指向
`PUSH_EXC_INFO…RERAISE` 出口的独立异常表区域（形如 `X to Y -> H [1]`、`H to H' -> H'' [2] lasti`），
必须生成 `try: <体> finally: <finally体>` 节点，禁止把 finally 体下放为循环体尾部的顺序语句。
验收判据即本目录 FIXTEST：`pyc_verify.py single … --source <修复后产物>` = 7/7，且 x05/e01 等
前置回归面不回退。

---

## 3. c4_12_star_args —— 失败 unit `***<module>.e04_deep`（Different bytecode）

### 3.1 三方源码对照

原始源码（tracked `test_repros/round4/c4_12_star_args.py`）：

```python
def e04_deep(f, xs, ys):
    r = 0
    for i in range(2):
        if i:
            r = f(*xs, *ys, **{'k': i})
    return r
```

HEAD r197 产物（`residual2/c4_12_star_args_HEAD.py` L10-15，**`**{dict 字面量}` 被折叠成关键字实参**）：

```python
def e04_deep(f, xs, ys):
    r = 0
    for i in range(2):
        if i:
            r = f(*xs, *ys, k=i)     # ← **{'k': i} 折叠为 k=i
    return r
```

基线（r72/G3 时代）形态（DRIFT_109.md §3.2 在案）：`f(*xs, *ys, **({'k': i}))` —— 括号不改变编译。

### 3.2 pyc 侧证据（`residual2/c4_12_e04_deep_dis.txt`）

[A] pyc 内 `e04_deep`（kwargs 构建三步）：

```
 44 PUSH_NULL / 46 LOAD_FAST f
 48 BUILD_LIST 0 / 50 xs LIST_EXTEND / 54 ys LIST_EXTEND / 58 LIST_TO_TUPLE
 60 BUILD_MAP 0                                  ← 空 kwargs 映射
 62 LOAD_CONST 'k' / 64 LOAD_FAST i / 66 BUILD_MAP 1   ← **{'k': i} 字典字面量
 68 DICT_MERGE 1                                 ← 并入 kwargs
 70 CALL_FUNCTION_EX 1
```

[B] HEAD 产物重编译（kwargs 单步）：

```
 44 PUSH_NULL / 46 LOAD_FAST f
 48 BUILD_LIST 0 / 50 xs LIST_EXTEND / 54 ys LIST_EXTEND / 58 LIST_TO_TUPLE
 60 LOAD_CONST 'k' / 62 LOAD_FAST i / 64 BUILD_MAP 1    ← k=i 直接打包
 66 CALL_FUNCTION_EX 1
```

差异＝2 条指令（`BUILD_MAP 0` 与 `DICT_MERGE 1` 被折叠掉），跳转结构完全一致 ⇒ 与
"Different bytecode"（而非 control flow）判定吻合。[A vs C] 逐指令一致 ⇒ 基准无瑕。

### 3.3 差异的具体语法构造（三方对照结论）

**调用实参中 `**<dict 字面量>` 的解包被折叠为等价的关键字实参**：`f(*xs, *ys, **{'k': i})` →
`f(*xs, *ys, k=i)`。调用语义（kwargs={'k': i}）不变，但字节码不回环（BUILD_MAP 0 + 字面量 +
DICT_MERGE 三步 vs 直接 BUILD_MAP 1 一步）。这是 c4_12 语料（star-args 族）**唯一**残留的构造；
同 pyc 其余 12 unit（e01/e02/e03/e05/e06.inner/CSA.m/e07/e08/e09/…）HEAD 产物已全部严格相等
（对比旧 OK.py 时代还错 5 个 unit：e02 错序、e03 错序、e06.inner 丢参、CSA.m 错序、e07 match 错构）。

### 3.4 根因初判

**反编译器缺陷（表示折叠/保真级，非行为级）**。证据链：

- 判据无伪差：dis 实测指令序列真实不同（非浮点/超时/unit 设计）；
- 非容差缺口：应然形态 `**({'k': i})` 编译后与 pyc 逐指令一致（[C]≡[A]），FIXTEST（读数 #6）仅还原
  这一处即 12/13→13/13——判据无需放宽；
- 行为维度无差（先前证据）：DRIFT_109.md §3.3 直跑 `e04_deep(marker,[1,2],[3])` 两边同返
  `('called',(1,2,3),[('k',1)])`；语义层判官本就把它归 (c) 尺子效应/27 条之列。

与 Task 122「30 条语义 DIFFERENT 中 Starred 族 12 条」的关系：**未验证，不预设**。本条残留的构造
（`**<dict 字面量>` 折叠为关键字实参）与 star-args 谱系同域，但两者分属不同判层（pyc_verify 严格层
vs 语义行 t30 判层），是否同谱系需父代理另行核对 12 条的逐条 diff 后才能断言（本报告不下结论）。

疑似机理（初判，未动代码）：CALL_FUNCTION_EX 的 kwargs 重建路径把
`BUILD_MAP 0 + <dict 显示> + DICT_MERGE` 序列读成"键值对集合"，遇常量字符串键即输出 `k=i`；
该路径未保留"`**` 解包一个 dict 字面量"这一表示。基线（r72 产物）保留 `**({...})` 形态 ⇒ 属
r72→r187 窗口内引入的表示级回归（DRIFT_109 §3.2 在案），非"从未正确"。

### 3.5 修复建议草案（只建议，不实现）

在 CALL_FUNCTION_EX kwargs 重建处区分两种来源：`(a)` 关键字对（`LOAD_CONST key; value; BUILD_MAP n`
直入）与 `(b)` `**` 解包 dict 字面量（先 `BUILD_MAP 0`，后跟字面量 `BUILD_MAP n`，再 `DICT_MERGE`）。
遇到 (b) 应输出 `**({'k': i})`（保留解包语法），不得折叠为 `k=i`；变量解包（e08/e09 的 `**(d)`）现有
输出保持不变。验收判据即 FIXTEST：13/13，且 e08/e09/e01-e03 等已绿 unit 不回退。

---

## 4. 决策项（移交父代理）

1. **c4_12 in-place OK.py 刷新**：`c4_12_star_argsOK.py` 停留在 rr-v2r04（2026-10-06）旧产物，读数 7/13，
   已落后 HEAD 产物（12/13）。若走刷新路线，建议刷新为修复 e04 折叠**之后**的 13/13 产物（现在刷新只能
   到 12/13）；x02 的 OK.py 是新快照（7/7），无需刷新。
2. **tasks.md 终验勾选**：两条残留均已定性（构造、根因类别、应然形态、验收判据齐备），但**未修复**——
   严格相等口径下 x02=6/7、c4_12=12/13 仍红。勾选与否及是否附"定性完毕/修复另立任务"注记由父代理裁决。
3. **Starred 族 12 条语义 DIFFERENT 与 e04_deep 是否同谱系**：需另行核对（见 §3.4）。

## 5. 观测 vs 推断

- 观测：全部读数（§1 六次判定）、四份 SHA、dis 指令序列与异常表、HEAD 产物与 drift2 逐字节相同、
  [A]≡[C] 逐指令一致、FIXTEST 翻绿、git 零写入。
- 推断（均有证据支撑但未穷举）：根因类别归属（§2.4/§3.4）；疑似 emitter 机理（r190 覆盖面外拓扑 /
  kwargs 折叠路径）；r72→r187 窗口引入（依据 DRIFT_109 §3.2 基线形态记录，未重跑 r72 树）；
  Starred 谱系关联（明确存疑，未验证）。

## 6. 证据与产物清单（均在 `D:\temp\opencode\cl_layout\g4d\residual2\`）

| 文件 | 内容 |
|---|---|
| `x02_for_deep_hosts_HEAD.py` | HEAD r197 产物（=drift2 逐字节，6/7 的直接物证） |
| `c4_12_star_args_HEAD.py` | HEAD r197 产物（=drift2 逐字节，12/13 的直接物证） |
| `x02_for_deep_hosts_FIXTEST.py` | 仅恢复 for_in_try 内层 try/finally 的验证产物 → 7/7 |
| `c4_12_star_args_FIXTEST.py` | 仅还原 e04 `**({'k': i})` 的验证产物 → 13/13 |
| `x02_for_in_try_dis.txt` | for_in_try 三方 dis + 指令级 diff（[A] 7 条异常表 vs [B] 3 条） |
| `c4_12_e04_deep_dis.txt` | e04_deep 三方 dis + 指令级 diff（差 BUILD_MAP 0/DICT_MERGE 两条） |
| `residual2_dis.py` | 取证脚本（marshal 载入 pyc + 编译三方源码 + 对齐 diff） |
| `RESIDUAL2_QUALIFICATION.md` | 本报告 |

## 7. 全部命令清单（按执行序）

```powershell
# 冻结校验
Get-FileHash -Algorithm SHA256 "scripts/pyc_verify.py", "D:\Desktop\ptrade相关\pylingual\equivalence_check.py", "test_repros/round2/x02_for_deep_hosts.pyc", "test_repros/round4/c4_12_star_args.pyc"
Get-FileHash -Algorithm SHA256 "D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py"
# 基线（单跑）
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round2/x02_for_deep_hosts.pyc        # 7/7
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round4/c4_12_star_args.pyc           # 7/13
# HEAD 新产物
D:/Python/python.exe -X utf8 pycdc.py -o D:/temp/opencode/cl_layout/g4d/residual2/x02_for_deep_hosts_HEAD.py test_repros/round2/x02_for_deep_hosts.pyc
D:/Python/python.exe -X utf8 pycdc.py -o D:/temp/opencode/cl_layout/g4d/residual2/c4_12_star_args_HEAD.py test_repros/round4/c4_12_star_args.pyc
# HEAD 对照（单跑）
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round2/x02_for_deep_hosts.pyc --source D:/temp/opencode/cl_layout/g4d/residual2/x02_for_deep_hosts_HEAD.py     # 6/7
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round4/c4_12_star_args.pyc --source D:/temp/opencode/cl_layout/g4d/residual2/c4_12_star_args_HEAD.py            # 12/13
# dis 取证
D:/Python/python.exe -X utf8 residual2_dis.py    # cwd=residual2
# FIXTEST 因果验证（单跑）
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round2/x02_for_deep_hosts.pyc --source D:/temp/opencode/cl_layout/g4d/residual2/x02_for_deep_hosts_FIXTEST.py   # 7/7
D:/Python/python.exe -X utf8 scripts/pyc_verify.py single test_repros/round4/c4_12_star_args.pyc --source D:/temp/opencode/cl_layout/g4d/residual2/c4_12_star_args_FIXTEST.py          # 13/13
# 零写入确认
git status --porcelain   # 本任务写入=0（详见 §8）
```

## 8. 仓库零写入确认（终验）

- 本任务对仓库（含 test_repros/）**零写入**：全部产物/证据/脚本都在
  `D:\temp\opencode\cl_layout\g4d\residual2\`；未 commit/push；未触碰 site-packages。
- `git status --porcelain`（终验）tracked 修改仅 1 条：`M tools/completeness/rule_proof_check.py`
  （mtime 2026-11-23 09:58:53；diff 为 "Revision 1.2.0 -- counting policy for guard-only rules
  (G4_REVIEW_PACKET adjudication 2)"）。该修改出现于本任务开始基线（0 个 tracked 修改，08:32 实测）
  之后，是**并行 G4 工作流子代理**的写入，与本任务无关；本任务未读过也未写过该文件。
- test_repros/：tracked 干净；untracked 集合与任务开始时一致（round4/_scratch_m4 2 条 + round5 4 条 OK.py）。
- 两个 pyc 的 SHA 终值与 §0 冻结校验一致（未被任何环节改动）。
