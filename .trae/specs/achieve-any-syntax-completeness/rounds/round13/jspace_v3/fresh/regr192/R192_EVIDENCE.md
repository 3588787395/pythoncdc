# rr-v5r192 — r1_10 回归收窄：while or 链闭合的链首完整性判据（[v192-CHAINENTRY]）

树：`F:\Downloads\pythoncdc-main`（未 commit / 未 push）；解释器 `D:/Python/python.exe -I -X utf8`，cwd=仓库根。
判官：`scripts/pyc_verify.py single`。补丁：`D:\temp\opencode\cl_layout\r192\fix192.py`
（anchor `count==1` / utf-8-sig / BOM `efbbbf` 单头 / `py_compile` / 幂等 / `--revert` 往返 sha 一致）。
改动：`core/cfg/region_analyzer.py` **48 / 0**（纯插入，唯一程序文件）。

---

## 0. 结论

- **根因（截断点）**：r143 `d0ab6e94` 的 `[v143-ORCHAIN]` 闭合判据**①**——
  `if _oc_fjt is not None and _oc_fjt is loop.header_block:`（改前 L33457）——只问
  「链首的跳转目标是否为循环体入口」，无法区分「**or 链首**」与「**and 组末成员**」。
  旋转 while 的 `loop.condition_block` 恰是后者：`while a and b or c:`
  编译为 `a: IF_FALSE→c / b: IF_TRUE→header / c: IF_FALSE→exit`，前向走查自 `b`
  起步收成 `[(b,'or'), (c,'and')]`；判据 ①②③④ 逐条成立（① b 的 TRUE 边=header；
  ② c 的 FALSE 边=exit 且不在体语义集；③ c 落空=header；④ 非首成员无 STORE），
  于是闭合返回**半条链**，`a`（Block 0）被外提成 `if a:` 守卫。
- **为什么 r142 对**：改前 `_detect_while_condition_boolop_chain` 的顺序是
  dup → **forward** → nested → backward；r142 的 forward 返回 None，backward 走查
  收齐 `[(0,'and'), (14,'or'), (18,'and')]`（= 正确条件）。r143 起 forward 抢先返回
  半链，backward 不再有机会。
- **收窄 [v192-CHAINENTRY]**（只增不破，接受集是 r143 的**严格子集**）：
  当链首存在「**非链成员、非循环体**」的 fall-through 前驱，其条件跳转
  **FALSE 极性**、目标 == 本链**末**成员、且链首在其后继集合中 ⇒ 链首不是条件入口
  （更早的操作数把整条 or 尾一次跳过 = 扁平 `A and B or C` 结构特征）。此时候选链
  只有在闭合**已经把该 and 组前缀前置**（r144/r145/r146 路径成功，`_oc_prefixed=True`）
  时才保留；仍为半条链则 `return None`，交回 backward 走查（= r142 行为）。
- **结果**：`r1_10_while_mixed` **1/2 → 2/2**，产物 `3a2a6cc5f15fc278` →
  **`6db8e097cb6d353b`**（= r142 / G3 快照 sha），直跑 27/27 与原件一致（改前 6/27 不同）。
- **r143 原始收益逐字节保留**（§3），五语料/电池/J 空间/红线/卫生全部维持（§4）。
- **影响面（2507 pyc × 预补丁树 vs 补丁树）恰 3 个产物变化**，全部是该形状族且判官
  **无一个单元回退**（2 个 pyc 判官上升、1 个同分）。

---

## 1. 复现（改前，当前树）

| 项 | 读数 |
|---|---|
| 产物 sha16 | `3a2a6cc5f15fc278` |
| 判官 | `failure units=1/2`（`***<module>.f: Failure: Different control flow`） |
| 直跑 | `f(0,1,1)` 原件 `10` / 产物 `0`；8 组布尔实参中 2 组不同（27 组 0/1/2 网格中 6 组不同） |

产物 vs 源码（关键差异行）：

```python
# 产物（改前）                          # 源码
def f(a, b, c):                         def f(a, b, c):
    total = 0                               total = 0
    n = 0                                   n = 0
    if a:                                   while a and b or c:
        while b or c:                           total += 1
            total += 1                          n += 1
            n += 1                              if n > 9:
            if n > 9:                               break
                break                       return total
            if not a:
                break
    return total
```

插桩（`probe_all.py`，包装 `_detect_while_boolop_forward_chain`，打点链/前驱）：

```
CALL cond=14 header=22 body=[22,54,56,60,64]
     -> [(B@14(POP_JUMP_FORWARD_IF_TRUE,22),'or'), (B@18(POP_JUMP_FORWARD_IF_FALSE,68),'and')] all_same=False
   headpreds = [(0, POP_JUMP_FORWARD_IF_FALSE, argval=18, succ=[14, 18])]
```

强制 forward 返回 None（隔离实验）：

```
FWD cond=14 -> [(14, 'or'), (18, 'and')]
NESTED cond=14 -> None
FINAL cond=14 -> [(0, 'and'), (14, 'or'), (18, 'and')]     ← backward 走查的完整链
```

→ 产物恢复 `while a and b or c:`（`6db8e097cb6d353b`）。**证明截断只由 forward 的 or 链闭合引入。**

---

## 2. 定位：hunk 里哪条条件截断了条件

- 截断判据名：**判据①「链首 op='or' 且链首跳转目标 == loop.header_block」**
  （`_oc_fjt is loop.header_block`，改前 L33457；闭合入口 L33452）。
- 判据 ②③④ 不是充分条件也不是必要条件，本例全部成立：
  ② `'FALSE' in _oc_ll.opname and opname in FORWARD_CONDITIONAL_JUMP_OPS`（c 块，
  目标 68=循环出口、不在体语义集）；③ 末成员落空 == header；④ 非首成员无 `STORE_*`。
- 反例结构事实：链首 `B@14` 的有个**外部**前驱 `B@0`（`a`），以 `POP_JUMP_FORWARD_IF_FALSE`
  收尾、假边目标 `18` == **本链末成员**、落空 == 链首 `14` —— 即「and 组的失败边直达
  or 尾求值起点」的**扁平 `A and B or C`** 形状（与
  `_detect_while_condition_nested_and_or_chain` 文档中「嵌套形 and 头假边越过整个 or run
  直达出口」的对照判据同源）。这说明 `B@14` 不是条件入口。
- r146 的 `[v146-ORFLAT]` 扁平前缀回溯**已经**收集到 `B@0`（判据与本条一致），但其
  **回边副本贪心匹配门**（`_on_pre_ok`，要求每个成员在循环环内有独立重检副本）在
  r1_10 上判否 ⇒ 不前置 ⇒ 直接 `return chain`（半链）。本补丁正是把「收集到前缀但门判否」
  这一状态显式化：不前置就不接受半链。

**改动**（两处，均在 `_detect_while_boolop_forward_chain`）：

```python
        _oc_entry_skip = False
        _oc_prefixed = False
        if len(chain) >= 2 and chain[0][1] == 'or':
            _oc_member_offsets = {_oc_b.start_offset for _oc_b, _ in chain}
            _oc_tail_off = chain[-1][0].start_offset
            _oc_head = chain[0][0]
            for _oc_pp in _oc_head.predecessors:
                ...  # 非链成员 / 非 loop.blocks / 非 body_blocks
                if _oc_plast.opname not in FORWARD_CONDITIONAL_JUMP_OPS: continue
                if 'FALSE' not in _oc_plast.opname: continue          # 取反族不命中
                if _oc_plast.argval != _oc_tail_off: continue        # 只认「直达末成员」
                if any(_oc_s.start_offset == _oc_head.start_offset
                       for _oc_s in _oc_pp.conditional_successors):
                    _oc_entry_skip = True
                    break
        ...
                                        _oc_prefixed = True          # 前缀已前置
                                if _oc_entry_skip and not _oc_prefixed:
                                    return None
                                return chain
```

判据只用 **块末 opcode 极性 + 跳转/落空目标同一性 + 块归属（pred-succ）**（I.4 白名单）；
无数字上限、无名字/偏移常量、不新增跨层 `X.entry in Y.blocks`、不新增 self 状态。
新增名 `_oc_entry_skip` / `_oc_prefixed`（无 §2.1 禁用前缀）。

---

## 3. r143 原始收益：形态与保留核对

r143 的目标形态（`[v143-ORCHAIN]`）：**or 首** while 条件（链首即条件入口，
TRUE 边→体入口、末成员 FALSE 边→循环出口），以及 r144/r145/r146 在其上叠加的
`while A and (B or C):` 嵌套/扁平前缀族。

| 单元 | 改前 sha16 | 改后 sha16 | 判官 |
|---|---|---|---|
| `E1_while_or2`（`while i > 3 or b[i] == 1:`） | `5ceb298d0f1a732a` | 同 | 矩阵 BYTE-EQUAL（r143 已记） |
| `E2_while_or3`（3 首 or 链） | `425d493d7e2efa19` | 同 | 同上 |
| `E3_while_or_call`（or 次操作数带调用） | `1974e7dcb1f9c726` | 同 | 同上 |
| `C1_and_chain_guard` / `C2_if_or` | `5e5f4d89a2b32fd6` / `41a7910331c3bc24` | 同 | 控制案 |
| r144 `E1_and_or_nest` / `E2_and_or_nest2` / `C3_flat_and_or` | `467269181c1b4cd6` / `5a0837a1affb966b` / `b95e6408f087b321` | 同 | 嵌套/扁平前缀族 |
| difflib（含 `_line_pair_iterator` or 链） | `d70df6006a50` | 同 | **62/62**（r143 当时 56/62，未降） |
| 458 电池 `na5`（r143 登记改进案） | `TEXT-SAME` | 同 | 未变 |

闭合判据在 E1 上**仍在生效**（插桩：`CALL cond=0 -> [(0,'or'),(18,'and')] all_same=False`，
`headpreds=[]` ⇒ `_oc_entry_skip=False`）；difflib 两处 or 链闭合（`COND=38/42`）同样仍生效。
`while A and (B or C):` 族由 v144/v145/v146 前缀路径处理，其 and 头假边**越过整个 or run
直达假出口**，不满足本条（目标==链末成员），且 `_oc_prefixed=True` 时一律保留。

---

## 4. 验证读数（全部实测）

### 4.1 回归案 r1_10
| 项 | 改前 | 改后 |
|---|---|---|
| 产物 sha16 | `3a2a6cc5f15fc278` | **`6db8e097cb6d353b`** |
| 判官 | failure 1/2（`f`） | **success 2/2** |
| 直跑 `f`（27 组 `a,b,c∈{0,1,2}`） | 6/27 与原件不同 | **0/27** |
| AST（If,stmt,Pass） | (3,12,0) | **(1,9,0) = 源码** |

### 4.2 前置回归（A/B，pre-patch 树 vs 补丁树）
| 案 | 改前 | 改后 |
|---|---|---|
| `e01_g1_b98_matrix` | `e5b02d5ef81ebf46` 15/15 | 同 sha 15/15（SAME） |
| `v_b71_face` | `010ad39367f036fa` 4/4 | 同 sha 4/4（SAME） |
| `e02_g1_b98_hosts` | `9f4b826eed3298d7` 18/18 | 同 sha 18/18（SAME） |
| `r9_02_b2_dual_continue` | `bb86df782296d705` 5/5 | 同 sha 5/5（SAME） |

### 4.3 五语料（与预补丁树逐字节比较 + 与 r191 产物比较）
| 语料 | sha12 | 判官 | = r191 |
|---|---|---|---|
| request | `db2172e8f1a6` SAME | 194/194 | True |
| tarfile | `8b35ed1396ac` SAME | 158/160（`TarFile.add`、`main` 既有） | True |
| cookiejar | `d39c77eeb677` SAME | 103/105（`_timegm`、`set_ok_path` 既有） | True |
| subprocess | `557b9b0bfe9e` SAME | 75/78（3 个 `Popen.*` 既有） | True |
| difflib | `d70df6006a50` SAME | 62/62 | True |

### 4.4 J 空间
- r1_10 的 **12 条** J 条目（JS-WHILE-001/004/005/006/008/009/010/011/012/013/015/016）：
  `semantic_runner` 对当前树 **12/12 EQUAL / covered_5tuple=12**；对预补丁树 **12/12 DIFFERENT**。
- overlay 进 r191 冻结集后 `coverage_checker`：**covered_5tuple = 1174**（= 基线值，未下降），
  `r7_only_different=6`、`excluded=376`、`uncovered=382`、`J_total=1556` 均不变。
  对照（把 12 条换成预补丁树记录）：**covered_5tuple = 1162、r7_only_different=18**。

### 4.5 458 电池（old = 预补丁树，new = 补丁树，8 分片合并）
`rows=458`；**TEXT-DIFF 0/458**（⇒ ⊆ 17 项允许集，`extra=[]`，`all-byte-equal=True`）；
`C7_skipedge = TEXT-SAME`；`NO-SRC 0`、`COMPILE-ERR 0`；
**458/458 行 (text, sig) 与 r191 基线逐行相同，changed=NONE**（R110 169 案同值）。
（首跑出现 `pv5` 一处 87 字节截断产物 = 高并发下的瞬时失败，单跑复现为 `d9979fa1` 与 old 相同；
删除该缓存产物重跑分片 0 后归零，其余 457 个产物无截断。）

### 4.6 AST 剪枝
- 五语料 `(If, stmt, Pass)`：request (286,1725,17)、tarfile (324,1750,12)、
  cookiejar (240,1213,8)、subprocess (270,1125,22)、difflib (114,737,9) —— 改前改后逐项相同。
- r1_10：`f` 源码 (1,9,0) / 改前 (3,12,0) / 改后 **(1,9,0)**；无语句减少、无幻影 `pass`。

### 4.7 红线
五语料 `text=SAME`，逐 code object **changed=NONE**
（request 184 / tarfile 157 / cookiejar 104 / subprocess 66 / difflib 59 个 code object）；
tarfile / cookiejar / subprocess 各 12 具名单元 **36/36 BYTE-SAME**。

### 4.8 影响面普查（2507 pyc：`test_repros/` + `.trae/specs/` + `_b142_probes` + 五语料，>1.5MB 的 `_chk*` 排除）
`0 ERR`；**产物变化恰 3 个**：

| pyc | 改前 | 改后 | 判官 |
|---|---|---|---|
| `test_repros/round1/r1_10_while_mixed.pyc` | `b54d2725…` | `be0b590d…` | 1/2 → **2/2** |
| `…/semantic_products/shard1/__pycache__/JS-WHILE-001.cpython-311.pyc` | `5c0f0f9e…` | `2b840e00…` | 1/2 → **2/2** |
| `test_repros/round3/r3_28_while_mixed_chain.pyc` | `8ee94f30…` | `76360e99…` | 3/5 → **4/5**（`while_and_or` 修复，`while_chain3` 仍既有失败） |

判官 A/B：**0 个单元由通过转失败**；直跑：r1_10 `f` 6→0 差异、r3_28 `while_and_or` 8→0
差异、`while_chain3` 改前改后 0 差异（文本不变）。
形状矩阵（S1–S10、T1–T10）：只有 `T9_prefix2`（`n=0; m=m+1; while a and b or c`）由
半链变为 `while a and b or c:`（重编译 BYTE-EQUAL）；`T10_call`
（`while a and g(b) or c:`，预补丁已正确）与 `T5/T10 not` 族、多 or 尾族全部 TEXT-SAME。

### 4.9 卫生
- `scripts/validate_region_generator_signatures.py` → **`统计: 14 个错误, 6 个警告`**（r189/r190/r191 同值）。
- `core/cfg/region_analyzer.py`：首 3 字节 `efbbbf`，BOM 计数 **1**，`\r\n` **0**、`\n` 39757（全 LF）。
- `git status`（tracked）：仅 `core/cfg/region_analyzer.py` M + 本轮开始前既有的
  `.trae/.../r10v10_fv_iv2.json`；`git diff --numstat` = **`48 0 core/cfg/region_analyzer.py`**。
- `fix192.py`：apply → `4880bf1eead4…`；二次 apply skip（sha 不变）；`--revert` →
  `352d42345639…`（= 改前原文 sha256）；再 apply → `4880bf1e…`；两向均过 `py_compile`。

---

## 5. 复现命令

```powershell
cd F:\Downloads\pythoncdc-main
D:/Python/python.exe -I -X utf8 pycdc.py test_repros/round1/r1_10_while_mixed.pyc -o <out>.py
D:/Python/python.exe -I -X utf8 scripts/pyc_verify.py single test_repros/round1/r1_10_while_mixed.pyc --source <out>.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\gate\cases192.py     # 四前置案 + r1_10 A/B
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\gate\corpus_run192.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\gate\redline192.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\gate\ast192.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\gate\shapes192b.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\gate\judge_changed192.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\merge_census192.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\merge_battery192.py   # 需先跑 battery192.py 0..7
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\overlay192.py
D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r192\run_coverage.py --space .trae\specs\achieve-any-syntax-completeness\rounds\round13\jspace_v3\fresh\judgment_space_v3m_b275.json --evidence D:\temp\opencode\cl_layout\r192\work\semantic_r192_frozen_plus.json --out D:\temp\opencode\cl_layout\r192\work\cov_r192.md --json D:\temp\opencode\cl_layout\r192\work\cov_r192.json
```

## 6. 产物清单（`D:\temp\opencode\cl_layout\r192`）
`fix192.py`、`gate/{cases192,corpus_run192,ast192,redline192,judge_changed192,shapes192,shapes192b}.py`
+ 同名 `.txt` 读数、`gate/{base_products,fix_products,cases,changed,matrix}`、
`census192.py` + `census/{base,fix}_0..7.json`、`merge_census192.py` + `gate/census192.json`、
`battery192.py` / `merge_battery192.py` + `battery/`、`overlay192.py`、`mk_space_r110.py`、
`run_semantic.py` / `run_coverage.py` + `work/{space_r110,semantic_r192_r110,
semantic_r192_frozen_plus,cov_r192}.json`、`probe_all.py` / `probe_crit2.py` / `behave192.py`、
`base/tree`（预补丁冻结树，`region_analyzer.py` = `352d4234…`）。
