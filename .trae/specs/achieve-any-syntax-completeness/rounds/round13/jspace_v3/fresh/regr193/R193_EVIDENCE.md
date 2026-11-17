# rr-v5r193 — D3 残留缺陷修复：`while True → with → if a: continue` 的 continue 退化成 pass（[v193-WTRAMPOLINE]）

树：`F:\Downloads\pythoncdc-main`（未 commit / 未 push）；解释器 `D:/Python/python.exe -I -X utf8`，cwd=仓库根。
判官：`scripts/pyc_verify.py single <pyc> --source <product>`。补丁：`D:\temp\opencode\cl_layout\r193\fix193.py`
（anchor `count==1` / `utf-8-sig` 读写 + BOM 回写 / `py_compile` / 幂等 / `--revert` 往返 sha 一致）。
改动：`core/cfg/region_ast_generator.py` **34 / 2**（唯一程序文件；docstring 判据 (3) + 方法体各一处）。

---

## 0. 结论

- **根因**：`RegionASTGenerator._b66_is_with_exit_continue_chain_head`（L5490）判据 (3) 的
  `_b66_tgt is not self._current_loop.header_block`（改前 L5536）在 `while True:` 形态下**恒不成立**：
  回边 `JUMP_BACKWARD 2` 落点是循环入口的 **NOP 跳板块 B@2**，而
  `_current_loop.header_block` 是 **B@4**（循环体首块 `BEFORE_WITH`）。其余子条件全成立。
- **退化步骤**：NOP-only then 臂块（B@40）在两处发射站点都走 `_is_orphan_boundary_nop` 分支；
  B66=False、B66c=False（B66c 要 RETURN 载荷，本形态的 return 清理属于 else 臂），于是
  `stmts.append(self._folded_statement_placeholder())` → `Pass`；`_generate_if` 装配
  `If(test=a, body=[Pass])`，`_generate_with` 发出 `With(body=[If(pass), Return(4)])`。
  同站点 `_try_generate_conditional_break_or_continue(B@40)` 三次全 `None`
  （`_block_is_continue_target` 只看块末指令，链头块末指令是 NOP）——与 DRIFT_109 §2.3 记录一致。
- **修复谓词**（`[v193-WTRAMPOLINE]`，纯结构性、只增不破）：回边落点 != header 时，若
  ①落点属当前循环帧（`loop.blocks`）②落点剥噪后无任何用户指令 ③落点唯一普通后继**就是**
  `header_block` ⇒ 视作回边回到循环顶（编译器 `while True:` 的入口跳板）。接受集是原判据的
  **严格超集**：原 True 路径逐位不变，新分支只在原判 False 处生效。
- **结果**：该案判官 **4/5 → 5/5**（`ae4ab0ed…` → `c1f2df54…`），直跑 4/4 与原件一致（改前 2/4 不同）；
  同一形态的 `rec1_synth_b70a_wt_with_bc` 顺带 **2/3 → 3/3**（`if b: pass else: use(f)` → 源码原样）。
- 前置五案 / 五语料 / 458 电池 / 红线 / J 空间 / 卫生全部维持；普查 2507 pyc **0 回退**。

---

## 1. 复现（改前，当前树）

| 项 | 读数 |
|---|---|
| 产物 sha256 | `ae4ab0ed070185ce…` |
| 判官 | `failure units=4/5`（`***<module>.g4b_wt_with_continue: Failure: Different control flow`） |
| 直跑 `g4b_wt_with_continue(0,1)` / `(1,1)` | 原件 `OSError [WinError 6] 句柄无效。` / 产物 `4` |

```python
# 产物（改前）                        # 源码 rec1_synth_g4b_b70_whiletrue_with.py
def g4b_wt_with_continue(p, a):      def g4b_wt_with_continue(p, a):
    while True:                          while True:
        with open(p) as f:                   with open(p) as f:
            if a:                                if a:
                pass                                 continue
            return 4                             return 4
```

直跑 A/B（`direct193.py`，4 组实参；stdout 被 fixture 的 `open(p)` 关掉，故结果写文件）：

```
args=[0, 1]   orig={"error": "OSError: [WinError 6] …"} prod={"ret": 4}   DIFF
args=[0, 0]   orig={"ret": 4}                           prod={"ret": 4}   SAME
args=[1, 1]   orig={"error": "OSError: [WinError 6] …"} prod={"ret": 4}   DIFF
args=[1, 0]   orig={"ret": 4}                           prod={"ret": 4}   SAME
```

字节码（`dis193.py`）：`2 NOP`（循环入口）/ `34 STORE_FAST f` / `38 POP_JUMP_FORWARD_IF_FALSE 66`
/ `40 NOP` / `42..62 __exit__(None×3)+CALL+POP_TOP` / `64 JUMP_BACKWARD 2` / `66..88` else 臂清理 /
`90 LOAD_CONST 4 / 92 RETURN_VALUE`；异常表 4 项（34–42、66–68、94–102、108–110）。

---

## 2. 定位：哪条判据不成立、continue 在哪一步变 pass

插桩（`probe193.py` / `probe193c.py`，包装 B66/B66c/TGCBC/`_generate_if`/`_generate_with`）：

```
TGCBC B@40[1](NOP,None) -> None  (last=NOP cont_target=False)
ORPHAN_NOP off=40 -> True
B66 B@40[1](NOP,None) -> False
   curloop=True header=B@4[5](BEFORE_WITH,None)
   c2_no_user=True instrs=[(40,'NOP',None)]
   succs(normal)=['B@42[7](JUMP_BACKWARD,2)'] exc=['B@94…']
   succ_last=JUMP_BACKWARD argval=2
   tgt=B@2[1](NOP,None) isheader=False          <-- 判据 (3) 在此判否
   succ_instrs=[(42,LOAD_CONST None)…(62,POP_TOP) (64,JUMP_BACKWARD 2)]
   withregs=[('B@4', block in r.blocks=True, succ in r.blocks=True, [4,34,40,42,66,68,94,102])]
B66C B@40 -> False
GENIF entry=B@34 body=…"body": [{"type": "Pass"}]
GENWITH entry=B@4 => {"type":"With", … "body":[{"type":"If",…"body":[{"type":"Pass"}]},
                                                {"type":"Return","value":4}]}
```

判据逐条：**(1) 成立**（`_current_loop` = LoopRegion，`is_while_true=True`）；
**(2) 成立**（B@40 只有 `NOP`）；**(3) 半成立**——succ 末指令确为 `JUMP_BACKWARD`，
但 `argval=2` 的块 B@2 `is not header_block`（header=B@4）⇒ **不成立**；
**(4) 成立**（B@40、B@42 都在同一个 WithRegion 的 `blocks` 里）。

循环帧事实：`loop.blocks=[2,4,34,40,42,66,68,94,100,102,108,110]`、
`loop.body_blocks=[4,…]`（**2 不在体内**）、`loop.back_edge_block=B@110`、
B@2 的后继 `[B@4]`、B@2 的前驱 `[B@0（函数入口）, B@42（continue 回边）]`、
header B@4 的前驱 `[B@2, B@110]`。即 B@2 是**循环入口跳板**，回边经它落入 header。

降级链：两处发射站点（`_process_if_blocks` L43367 / 语句路径 L73330）在
`_is_orphan_boundary_nop` 为真后依次试 B66（False）、B66c（False）、
`_folded_statement_placeholder()`（= `Pass`）；`_try_generate_conditional_break_or_continue`
在该块上返回 `None`，于是 `if a: continue` 变成 `if a: pass`。

---

## 3. 修复

```python
        _b66_tgt = self.cfg.get_block_by_offset(_b66_last.argval)
        if _b66_tgt is None:
            return False
        if _b66_tgt is not self._current_loop.header_block:
            # [v193-WTRAMPOLINE] …（注释见补丁）
            _b66_loop = self._current_loop
            _b66_tramp = False
            if _b66_tgt in (getattr(_b66_loop, 'blocks', None) or ()):
                if all(i.opname in _b66_noise for i in _b66_tgt.instructions):
                    _b66_tgt_exc = getattr(_b66_tgt, 'exception_successors', None) or set()
                    _b66_tgt_succs = [s for s in (_b66_tgt.successors or [])
                                      if s not in _b66_tgt_exc]
                    if (len(_b66_tgt_succs) == 1
                            and _b66_tgt_succs[0] is _b66_loop.header_block):
                        _b66_tramp = True
            if not _b66_tramp:
                return False
```

判据只用 **块归属（loop.blocks）+ 块内容 opcode + 后继/落空目标同一性**（I.4 白名单）；
无数字上限、无偏移/名字常量、无 pyc 特判、无跨层 `X.entry in Y.blocks`、不新增 self 状态。
新名 `_b66_loop` / `_b66_tramp` / `_b66_tgt_exc` / `_b66_tgt_succs`（无 §2.1 禁用前缀）。
docstring 判据 (3) 同步登记（第二 hunk）。

---

## 4. 验证读数（全部实测）

### 4.1 回归案 D3
| 项 | 改前 | 改后 |
|---|---|---|
| 产物 sha256 | `ae4ab0ed070185ce…` | **`c1f2df540828a44b…`** |
| 判官 | failure 4/5（`g4b_wt_with_continue`） | **success 5/5** |
| 直跑 4 组实参 | 2/4 与原件不同 | **0/4** |
| AST `g4b_wt_with_continue` | (If,stmt,Pass)=(1,6,1)，有 `Pass` 无 `Continue` | **(1,6,0)，`Continue`×1、`Pass`×0 = 源码** |

### 4.2 前置回归（A/B，pre-patch 树 vs 补丁树）
| 案 | 改前 | 改后 |
|---|---|---|
| `e01_g1_b98_matrix` | `e5b02d5ef81ebf46` 15/15 | 同 sha 15/15（SAME） |
| `v_b71_face` | `010ad39367f036fa` 4/4 | 同 sha 4/4（SAME） |
| `e02_g1_b98_hosts` | `9f4b826eed3298d7` 18/18 | 同 sha 18/18（SAME） |
| `r9_02_b2_dual_continue` | `bb86df782296d705` 5/5 | 同 sha 5/5（SAME） |
| `r1_10_while_mixed` | `6db8e097cb6d353b` 2/2 | 同 sha 2/2（SAME） |

### 4.3 五语料（与 pre-patch 树逐字节 + 与 r192 产物比较）
| 语料 | sha12 | 判官 | = r192 |
|---|---|---|---|
| request | `db2172e8f1a6` SAME | 194/194 | True |
| tarfile | `8b35ed1396ac` SAME | 158/160（`TarFile.add`、`main` 既有） | True |
| cookiejar | `d39c77eeb677` SAME | 103/105（`_timegm`、`set_ok_path` 既有） | True |
| subprocess | `557b9b0bfe9e` SAME | 75/78（3 个 `Popen.*` 既有） | True |
| difflib | `d70df6006a50` SAME | 62/62 | True |

### 4.4 J 空间
- 受影响的 4 条 J 条目（`JS-WITH-006` / `JS-BREAK-022` / `JS-WHILE-034` / `JS-WHILE-042`）
  用补丁树重跑 `semantic_runner`：**4/4 EQUAL**，product sha 与冻结证据集**逐一相同**
  （`61f829d3…` / `c1f2df54…`）。
- overlay 进 r192 冻结集后 `coverage_checker`：**covered_5tuple = 1174**
  （与 r192 证据集基线 1174 **相同**，未下降），`r7_only_different=6`、`excluded=376`、
  `uncovered=382`、`J_total=1556` 全部不变。
- 旁证：冻结证据集里 `JS-WHILE-042` 记录的 product sha 就是 `c1f2df54…`——只有补丁树
  能重现它（改前树是 `ae4ab0ed…`，判官 4/5），即本修复把该条目的证据链恢复为自洽。

### 4.5 458 电池（old = pre-patch 产物，new = 补丁树）
`rows=458`；**TEXT-DIFF 0/458** ⇒ ⊆ 17 项允许集（`extra=[]`），`all-byte-equal=True`；
`C7_skipedge = TEXT-SAME`；`NO-SRC 0`、`COMPILE-ERR 0`。

### 4.6 AST 剪枝
- 五语料 `(If, stmt, Pass)` 改前=改后：request (286,1725,17)、tarfile (324,1750,12)、
  cookiejar (240,1213,8)、subprocess (270,1125,22)、difflib (114,737,9)。
- D3：`g4b_wt_with_continue` 源码 kinds `[FunctionDef, While, With, If, Return, Continue]`
  = 改后产物逐项相同；改前产物同上但 `Continue → Pass`。
- `g4b_wt_nested_with` (1,7,0) vs (1,6,0)：**改前=改后**（既有 `with a: with b:` 合并为一条
  `with a, b:` 语句，非本轮引入，判官该单元一直通过）。

### 4.7 红线
五语料 `text=SAME`，逐 code object **changed=NONE**
（request 184 / tarfile 157 / cookiejar 104 / subprocess 66 / difflib 59）；
tarfile / cookiejar / subprocess 各 12 具名单元 **36/36 BYTE-SAME**。

### 4.8 影响面普查（2507 pyc：`test_repros/` + `.trae/specs/` + `_b142_probes` + 五语料，>1.5MB 排除）
`0 ERR`；**产物变化 8 条路径 = 2 个真实形态**（其余 6 条是同一 pyc 在 `.trae/.../test_repros/`
下的副本，字节相同）：

| pyc（去重后） | 改前 sha16 | 改后 sha16 | 判官 |
|---|---|---|---|
| `test_repros/round5/rec1_synth_g4b_b70_whiletrue_with.pyc`（4 路径副本） | `1394ebfe55d6d343` | `04858bcd5d3f7c30` | 4/5 → **5/5** |
| `test_repros/round5/rec1_synth_b70a_wt_with_bc.pyc`（4 路径副本） | `87c30403c2c4aa83` | `3c520ea5adaf2195` | 2/3 → **3/3** |

判官 A/B：**0 个单元由通过转失败**，2 个单元被修复（`wbc`、`g4b_wt_with_continue`）。
改前树普查读数与 r192 的 `base_*` 冻结读数**逐条相同**（2507/2507；
唯一 3 条差异正是 r192 自己修过的 r1_10 / JS-WHILE-001 / r3_28，属上一轮变化）。
> 说明：首轮 8 分片并发跑出 20 条瞬时 `ERR:RuntimeError`（r192 同期无），串行重算后逐条
> 复现稳定值（其中 4 条与 r192 冻结读数完全相同），最终 `0 ERR`。

### 4.9 卫生
- `scripts/validate_region_generator_signatures.py` → **`统计: 14 个错误, 6 个警告`**（r189–r192 同值）。
- 两 cfg 文件：首 3 字节 `efbbbf`，BOM 计数 **1**，`\r\n` **0**。
- `git status`（tracked）：`core/cfg/region_ast_generator.py` M + 本轮开始前既有的
  `.trae/.../r10v10_fv_iv2.json`；`git diff --numstat` = **`34 2 core/cfg/region_ast_generator.py`**。
- `fix193.py`：apply → `18c25f5e341d…`；二次 apply skip（sha 不变）；`--revert` →
  `d9d60964c92e…`（= 改前原文 sha256）；再 apply → `18c25f5e341d…`；两向均过 `py_compile`。

---

## 5. 复现命令

```powershell
cd F:\Downloads\pythoncdc-main
D:/Python/python.exe -I -X utf8 pycdc.py test_repros/round5/rec1_synth_g4b_b70_whiletrue_with.pyc -o <out>.py
D:/Python/python.exe -I -X utf8 scripts/pyc_verify.py single test_repros/round5/rec1_synth_g4b_b70_whiletrue_with.pyc --source <out>.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\behave193.py <out>.py      # 直跑 A/B（原件 vs 产物）
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\gate\cases193.py          # 五前置案 + D3 A/B
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\gate\corpus_run193.py      # 五语料 A/B
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\gate\judge_changed193.py   # 普查变化案判官 A/B
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\merge_census193.py        # 普查合并/差异
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\battery193.py 0 1         # 458 电池
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\gate\ast193.py            # AST
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\gate\redline193.py        # 红线
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\mk_space_r193.py          # J 子空间
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\run_semantic.py --space D:\temp\opencode\cl_layout\r193\work\space_r193.json --out D:\temp\opencode\cl_layout\r193\work\semantic_r193.json --report D:\temp\opencode\cl_layout\r193\work\semantic_r193_report.json --product-dir D:\temp\opencode\cl_layout\r193\work\semantic_products_all
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r193\overlay193.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\run_coverage.py --space .trae\specs\achieve-any-syntax-completeness\rounds\round13\jspace_v3\fresh\judgment_space_v3m_b275.json --evidence D:\temp\opencode\cl_layout\r193\work\semantic_r193_frozen_plus.json --out D:\temp\opencode\cl_layout\r193\work\cov_r193.md --json D:\temp\opencode\cl_layout\r193\work\cov_r193.json
```

## 6. 产物清单（`D:\temp\opencode\cl_layout\r193`）
`fix193.py`、`base/tree`（pre-patch 冻结树，`region_ast_generator.py` = `d9d60964…`）、
`probe193.py` / `probe193b.py` / `probe193c.py` + `.log`、`dis193.py`、`direct193.py`、
`behave193.py` / `behave193b.py`、`census193.py` + `census/{base,fix}_0..7.json`、
`merge_census193.py` + `gate/census193.json`、`repair_census193.py`、`battery193.py` + `battery/`、
`mk_space_r193.py` + `work/space_r193.json`、`overlay193.py`、
`gate/{cases193,corpus_run193,judge_changed193,ast193,redline193}.py` + 同名 `.txt`、
`gate/{base_products,fix_products,cases,changed}`、`gate/raw_judge_r193_*.txt`、
`work/{semantic_r193,semantic_r193_frozen_plus,cov_r193,cov_base_r192}.json`。
