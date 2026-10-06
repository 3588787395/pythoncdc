# Round 3 修复位 1（FIX_P1）：B98 分组 BoolOp 保真 + B44 浅层外推

- 涉改文件：`core/cfg/region_ast_generator.py`（**唯一**；未改任何 `region_analyzer.py`、未手改任何 `*OK.py`）
- 对应评审：`rounds/round3/REVIEW.md` §3.1（F1 BoolOp 专攻）、§4.1（B98）、§4.2（B44 存量外推）、§5.1（判据草案）
- 落地状态：**代码已落地**（见 §8 声明与 grep 锚点）

---

## 1 破口 → 修复动作 → 落地位置 → 判据 → 恢复的 C 条款

| 破口 | 修复动作（算法语义） | 落地位置 file:line | 判据（I.4 白名单） | 恢复条款 |
|---|---|---|---|---|
| **B98** 主形：`(a or b) and c` → `a or b or c`（内层 or 组边界丢失） | 分组检测新增「末尾值块」INNER 信号；分组重建末尾 fall-through 归属守卫：被链块跳转目标命中的值块归**外层链**、不再并入内层子组 | `region_ast_generator.py:37368-37380`（`_detect_boolop_grouping`）、`:37694-37705`（`_build_grouped_boolop_expression`） | 块末 opcode 族（`JUMP_IF_FALSE/TRUE_OR_POP`、`POP_JUMP_*`）+ 后继集合（`conditional_successors`）+ 链块跳转目标（指令 `argval`）+ 区域成员关系（`region.blocks`/`merge_block`/链块集） | **C2**（子组作抽象节点整体保真组合）+ **C3**（分组边界守卫封闭操作数边界）+ 原则三「嵌套即抽象节点」 |
| **B98** 对称变体：`a and (b or c)` → `a and b`（or 子组整体蒸发） | 内层 or 组操作数收集末尾，补收末 or 块 fall-through 值块承载的组末位操作数（排除被链块跳转目标命中者） | `region_ast_generator.py:38729-38739`（`_try_build_and_inner_or_pattern`） | 末 or 块块末 opcode 族 + 后继集合 + 链跳转目标集（指令 `argval`） | **C1**（末位操作数唯一归属内层 or 组）+ **C2**（黑箱组合） |
| **B98** 边界形：`(a or b) and (c or d) and e` → `or(c, and(d, e))`（B45 skip 边误重结合） | 分组重建前置守卫：存在「非末链块跳转目标命中末尾值块」时，令分组重建先于 B45 skip 边重建 | `region_ast_generator.py:38105-38116`（`_build_boolop_expression_inner`） | 链块跳转目标（指令 `argval`）+ 块末 opcode 族 + 后继集合 | **C1**（内层组唯一归属内层发射）+ **C3** |
| **B44** 浅层交叠形：`a and ((b or c) and d)` → `a and b or c and d` | 由 B98 边界形 + 末尾值块信号自然封闭（同 `(a or b) and c` 机理，组末位裸值块为 `d`） | 同上 §3.1 三处 | 同上 | **C2** + **C3** |

> 主目标 **B98 已封闭**（含函数根 / 赋值位 / 模块根 / 类体 / try 体宿主、对称变体、`(a or b) and (c or d) and e`）。
> 次要目标 **B44**：浅层交叠形 d2 已封闭；≥3 层「全-merge 出口」深层形与 d1 认领缺陷未封闭，如实登记（§7），**未以少发射 / 硬编码深度上限换绿**。

---

## 2 改动明细（改前 / 改后关键片段）

### 2.0 新增 3 个语义化命名辅助方法（`region_ast_generator.py:37204-37333`）

- `_resolve_boolop_tail_value_block(region, chain, last_block, require_not_chain_target=False)` — `:37204`：读末链块块末 opcode 族 + `conditional_successors`，返回「非跳转目标的 fall-through 值块」（∈`region.blocks`、∉链块、≠`merge_block`，可选排除被链块跳转目标命中的块）。
- `_reconstruct_boolop_tail_value_operand(...)` — `:37260`：定位 + 以语句屏障（`POP_TOP`/`RETURN_*`/`JUMP_*`）截断收尾段后 `expr_reconstructor.reconstruct`。
- `_has_boolop_tail_value_boundary(region, op_chain)` — `:37300`：判定「是否存在非末链块跳转目标恰为末尾值块」（B98 边界形判定）。

三者均带完整六项模板 docstring + C1/C2/C3（对照表见 §6）。命名无 I.5 禁用前缀。

### 2.1 `_detect_boolop_grouping`（`:37335`）——tail-value INNER 信号

```python
# 改前
target_is_chain_block = last_instr.argval in chain_block_offsets
if target_is_chain_block:
    raw_signals.append('INNER')
    ...
# 改后
_tail_value_block = self._resolve_boolop_tail_value_block(
    region, op_chain, op_chain[-1][0])
_tail_value_offset = (_tail_value_block.start_offset
                      if _tail_value_block is not None else None)
...
target_is_chain_block = last_instr.argval in chain_block_offsets
target_is_tail_value = (_tail_value_offset is not None
                        and last_instr.argval == _tail_value_offset)
if target_is_chain_block or target_is_tail_value:
    raw_signals.append('INNER')
    ...
```

**解释**：原 INNER 判据只认「跳转目标 ∈ 链块集」，覆盖不了「内层 or 组末位是裸值块」的浅层形（`(a or b) and c` 中 block@0 的 `IF_TRUE`→值块 `c`，`c` 不在链块集）。`target_is_tail_value` 与 `target_is_chain_block` 互补，共同构成「子组封闭边界」信号。判据仅用指令 `argval` + 后继集合。

### 2.2 `_build_grouped_boolop_expression`（`:37427`）——末尾 fall-through 归属守卫

```python
# 改前
if ft_expr is not None:
    if last_chain_op == outer_op:
        outer_values.append(ft_expr)
    elif current_inner_values:
        current_inner_values.append(ft_expr)
    ...
# 改后
if ft_expr is not None:
    _ft_is_chain_target = any(
        (_li is not None
         and isinstance(getattr(_li, 'argval', None), int)
         and _li.argval == ft_block.start_offset)
        for _cb, _ in op_chain
        for _li in [_cb.get_last_instruction()])
    if _ft_is_chain_target:
        outer_values.append(ft_expr)          # 内层组短路出口 ⇒ 外层操作数
    elif last_chain_op == outer_op:
        outer_values.append(ft_expr)
    elif current_inner_values:
        current_inner_values.append(ft_expr)
    ...
```

**解释**：末尾 fall-through 值块若被某链块的短路跳转目标命中，则它是**内层子组的短路出口 / 外层操作数入口**，不得并入末尾内层子组，否则 `(a or b) and c` 退化为 `or(a,b,c)`。守卫未命中即走原有分支，行为逐位不变（C2）。

### 2.3 `_try_build_and_inner_or_pattern`（`:38601`）——内层 or 组末位补收

```python
# 改前（操作数收集后直接构建）
# 改后
_tail_operand = self._reconstruct_boolop_tail_value_operand(
    region, op_chain, op_chain[-1][0], require_not_chain_target=True)
if _tail_operand is not None:
    or_operands.append(_tail_operand)
```

**解释**：内层 or 组末位操作数常驻末 or 块的 fall-through 值块（纯取值收尾、无短路跳转，故不入 `op_chain`）。不补收则 `a and (b or c)` 输出 `a and b`（or 子组蒸发）。`require_not_chain_target=True` 排除「被链块跳转目标命中的块」，避免把外层操作数入口误并入内层组。

### 2.4 `_build_boolop_expression_inner`（`:38057`）——边界形前置守卫

```python
# 改前
op_chain = region.op_chain
if not op_chain:
    return None
STRIP_JUMP_OPS = SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS
# [R7-B45] 链内 skip 边分段重建（先于分组检测）：
_b45_skipedge = self._build_boolop_skipedge_grouped(region)
# 改后（在 B45 skip 边重建之前插入）
if self._has_boolop_tail_value_boundary(region, op_chain):
    _b98_hg, _b98_oo, _b98_cls = self._detect_boolop_grouping(region, op_chain)
    if _b98_hg:
        _b98_grouped = self._build_grouped_boolop_expression(
            region, op_chain, _b98_oo, _b98_cls)
        if _b98_grouped is not None:
            return _b98_grouped
```

**解释**：边界形（`(a or b) and (c or d) and e`）下 B45 skip 边重建会把内层子组误并入外层（实测→`or(c, and(d, e))`），故分组重建须先手。predicate 不命中即维持 skip 边优先顺序，行为逐位不变（C2）；已实测 g1/g4 等既有 skip 边形态不命中该 predicate，不受影响。

---

## 3 判据合规自证（I.4 白名单）

**用到的全部判据（同层块结构事实）**：
- 块末指令 opcode 族：`SHORT_CIRCUIT_JUMP_OPS` / `FORWARD_CONDITIONAL_JUMP_OPS` / `BACKWARD_CONDITIONAL_JUMP_OPS`（由 `region_analyzer.py` 定义并导入）；
- 后继集合：`last_block.conditional_successors`；
- 区域成员关系：`region.blocks`、`region.merge_block`、链块集合 `{b.start_offset for b,_ in chain}`；
- 指令 oparg：`last_instr.argval`、`_li.argval`。

**黑名单自查（逐项）**：
- 文件名 / 函数名白名单：**无**（无任何 `name == 'xxx'` 判据）；
- `start_offset` 魔法阈值作比较常数：**无**（`start_offset` 仅作**集合成员 / 相等身份**比较，非阈值）；
- 跨层 `X.entry in Y.blocks` 反查：**无**；
- 新增 `self` 跨方法状态：**无**（全部为局部变量与入参）；
- 以少发射换全绿：**无**（新增守卫只改归属/顺序，未削减发射）；
- 硬编码深度 / 计数上限：**无**。
- I.5 禁用方法名前缀（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）：**零新增**（新增 3 方法均语义化命名）。

---

## 4 自测读数表（RV2：先改代码 → regen → verify；判据唯一 = `scripts/pyc_verify.py`）

### 4.1 本轮 28 探针回归（`test_repros/round3/`）

| 读数 | 基线（P1 前） | 本轮（修复后） | 判读 |
|---|---|---|---|
| 单元级 | 241/305 | **244/305（+3）** | 达标（不得低于基线） |
| COMPILE_ERROR | 3 | 3 | 持平 |
| 文件级 success/failure/error | 12 / 13 / 0 | 12 / 13 / 0 | 无位移 |
| e01_g1_b98_matrix | 5/15 | 5/15 | 持平 |
| **e02_g1_b98_hosts** | 7/18 | **10/18（+3）** | 模块根 `<module>`、类体 `CB98`、`f_try_body_host` 三单元转 MATCH |
| e03_g1_b1b_stress | 9/14 | 9/14 | 持平（B1b 属位 2） |
| ne01_g1_neg（负对照） | 1/5 | 1/5 | 持平（余 4 单元为 for 宿主 B99，属位 2） |
| ne10_g10_neg（负对照） | 1/3 | 1/3 | 持平 |

- `REGRESSIONS=0`（无一单元 `success→failure` 位移），`IMPROVED` 发生于 failure 文件内部（e02 7/18→10/18）。

### 4.2 移交复现（round2 B89 链）

| 复现 | 基线 | 本轮 | 判读 |
|---|---|---|---|
| `rv3_02_b89_boolop_chain` | failure 0/1（`Y = _A or _B or _C`） | **success 1/1**（`Y = (_A or _B) and _C`） | B98 最小复现转 MATCH |
| `rv3_07_b89_trim_overtrim` | failure 3/4 | failure 3/4 | 持平（`ternary_chain_then_while` 非本族） |

### 4.3 最小复现（`test_repros/round3/_scratch_b98/`）

- `hosts.pyc`：**7/7 success**；产物语义逐条正确：
  `M1 = (_P or _Q) and _R`（模块根）、`C1 = (_P or _Q) and _R`（类体）、`return (a or b) and c`（函数根）、`x = (a or b) and c`（赋值位）、`return a and (b or c)`（对称变体）、`return (a or b) and (c or d)`、`return (a or b) and (c or d) and e`。
- `resid.pyc`：**2/5**；`r_d2 a and ((b or c) and d)` → `return a and (b or c) and d` ✓（B44 浅层封闭）；`r_d1`/`r_e3`/`r_g2` 未封闭（§7）。

### 4.4 站桩回归 6 面（`r3v2_compare_regress.py`，全部 `WORSE=0`）

| 面 | 基线 | 本轮 | same / improved / **WORSE** |
|---|---|---|---|
| round2face（45） | 234/251 | 234/251 | 45 / 0 / **0** |
| probe42（42） | 154/189 | 172/196 | 32 / 10 / **0** |
| round1face（24） | 417/423 | 417/423 | 24 / 0 / **0** |
| residual（72） | 404/446 | 417/446 | 62 / 10 / **0** |
| oldface（59，旧规范 round6–10） | 658/692 | 664/692 | 55 / 4 / **0** |
| quotation 单验 | 152/153 | 152/153 | 持平（唯一失败 `change_his_to_forward`） |

> 改善集中在 round7 boolop/ternary 混合面（`r7_07_ternary_nest` 6→7、`r7_08_ternary_deep_host` 4→7、`r7_11_boolop_mixed` 6→7、`r7_12_boolop_nest` 5→6）与 round2 类体/模块面（c01/c06/c11/c13/m01/m07/m08/m12/x04/x09）。

### 4.5 交付前门禁自检

| 项 | 结果 |
|---|---|
| `import core.cfg.region_ast_generator` | IMPORT_OK |
| `python -m py_compile core/cfg/region_ast_generator.py` | PY_COMPILE_OK |
| BOM 单头 `efbbbf` | 首 6 字节 `ef bb bf 22 22 22`，全文 `bom_count=1` |
| I.5 禁用前缀新增方法 | 0（新增 3 方法语义化命名） |
| 插桩残留（新增 `print(`/`pdb`/`breakpoint(`/`# TODO`/`# FIXME`/`# DEBUG`/`# XXX`） | 0 新增（既有 `file=_sys_dbg*.stderr` 打印非本轮引入） |
| CRLF/LF 大规模改写 | 无（git diff 仅 5 处逻辑 hunk；行首 BOM 已复原，diff 无首行churn） |

---

## 5 恢复的 C 条款归纳（I.3）

- **C1 局部消费**：末尾值块定位/重建只读末链块块末 opcode 与同层后继集合；内层 or 组末位操作数补收只消费本区域块集。
- **C2 黑箱组合**：内层子组作为抽象节点整体保真组合进外层链；守卫未命中一律走既有分支（逐位不变），深层与浅层同处理。
- **C3 守卫封闭**：分组边界守卫按「链块跳转目标 / 末尾值块身份」显式封闭，排除「被链块跳转目标命中的值块」误并入内层组，恢复嵌套无感。

---

## 6 注释六项模板对照表（I.7）

| 方法（file:line） | ①算法依据 | ②归约顺序 | ③唯一归属判定 | ④嵌套处理 | ⑤入口引用语义 | ⑥反编译流程位置 | C1/C2/C3 |
|---|---|---|---|---|---|---|---|
| `_resolve_boolop_tail_value_block` `:37204` | CPython 3.11 短路块末 opcode 族定义分组极性、组末位裸值落 fall-through | 分组检测/重建前，只做定位 | 候选须 ∈`region.blocks`、∉链块、≠merge；可选排除链目标命中块 | 末链块若为嵌套宿主，交由调用方守卫过滤；本器不展开 | 返回块自身即末位操作数入口，不认领 | `_try_build_and_inner_or_pattern` / `_build_grouped_boolop_expression` 共用 | C1/C2/C3 齐全 |
| `_reconstruct_boolop_tail_value_operand` `:37260` | 定位 + 取值收尾段重建 | 内层组操作数收集之后 | 块级归属由定位器给出，二不认领 | 委托 `expr_reconstructor` 处理段内嵌套 | 以块入口指令段重建，不引用子区域入口 | 内层 or 组末位补收 | C1/C2/C3 齐全 |
| `_has_boolop_tail_value_boundary` `:37300` | 非末链块跳转目标命中末尾值块 | 先于 B45 skip 边重建 | 仅判定存在性，不认领 | 不展开嵌套 | 只读链块跳转目标（指令 `argval`） | `_build_boolop_expression_inner` 分组前置守卫 | C1/C2/C3 齐全 |
| `_detect_boolop_grouping` 新增段 `:37368` | 短路块末 opcode 族 + 组末位裸值落 fall-through | 分组检测段内、早于分组重建 | 目标命中末尾值块的非末链块标 INNER | 只加信号、不展开嵌套子组 | 块入口即操作数重建入口 | `_build_boolop_expression_inner`→raw_signals | C1/C2/C3 齐全 |
| `_build_grouped_boolop_expression` 新增段 `:37694` | 链块短路跳转目标集（指令 oparg）标记内层子组短路出口 | 分组重建末尾归属判定段 | 命中值块唯一归外层链，未命中按既有分支 | 不展开嵌套、仅改归属 | 值块入口即外层操作数入口 | 末尾 fall-through 归属 | C1/C2/C3 齐全 |
| `_build_boolop_expression_inner` 新增段 `:38105` | 非末链块短路跳转目标是否命中末尾值块 | 方法首段，先于 B45 skip 边重建 | 命中即令分组重建先手 | 存在性判定不展开 | 只读链块跳转目标、不认领块 | 分组重建前置守卫 | C1/C2/C3 齐全 |
| `_try_build_and_inner_or_pattern` 新增段 `:38729` | 末 or 块 fall-through 值块承载组末位裸值操作数 | 操作数收集末尾 | 排除链目标命中后，值块唯一归内层 or 组 | 经 `expr_reconstructor` 处理段内嵌套 | 以块入口指令段重建 | 内层 or 组末位补收 | C1/C2/C3 齐全 |

---

## 7 残留未封闭项 / 移交位 2

| 项 | 形态 | 现象 | 归属 | 处置 |
|---|---|---|---|---|
| **B44 深层全-merge 形** | `a or (b and (c or d))`、`a and (b or (c and d))`、e03 `f_b1b_deep_right`、b98-b8、`resid.r_e3` | 归约后**所有链块跳转目标 == `merge_block`**，无 tail-value 边界命中；扁平 or_groups 算法重结合错（`a or b and c or d`） | 生成层（本位）但**本轮未封闭** | 如实登记；如后续以「全链块 target==merge ⇒ 按 op 序列右结合嵌套」守卫封闭，须专门站桩回归（该形与已正确的 h1/h2/h5 同属全-merge，风险面大） |
| `((a or b) and c) or d`（b98-d1 / `resid.r_d1`） | ≥3 层显式括号 | `op_chain` 仅认领末块（blk0/blk6 未认领）→ 输出 `if not a: return c or d; if b: pass` | **识别层 `region_analyzer.py`**（超本位文件范围） | **移交位 2** |
| `resid.r_g2` | `(a and (b or c)) or (d and e)` | 既有存量重结合 | 识/生交叉 | 移交后续 |
| **B99** for 宿主 BoolOp 蒸发 | `for: return <BoolOp>` | `return None` / return 消失 | **识别层 `region_analyzer.py`** | **移交位 2** |
| **B1b 守卫域扩展**（B1 台账口径） | 深右嵌套 / while 体 if 链 / `is None or` 前缀 / IfExp 真值臂 | e03 五失败单元 | **识别层 `region_analyzer.py`** | **移交位 2** |

> 上述未封闭项均**未**以少发射、硬编码深度/计数上限或名字白名单换取绿；本轮 28 探针 244/305 与站桩 6 面 WORSE=0 为**净改善**读数。

---

## 8 落地声明（I.6）

**代码已落地。** 校验锚点（grep 树内命中，非仅归档）：

- `grep -n "\[B98\]" core/cfg/region_ast_generator.py` → 7 处（`:37209/:37265/:37302/:37368/:37694/:38105/:38729`）；
- `grep -n "def _resolve_boolop_tail_value_block|_reconstruct_boolop_tail_value_operand|_has_boolop_tail_value_boundary" core/cfg/region_ast_generator.py` → 3 新方法定义于 `:37204/:37260/:37300`；
- `import core.cfg.region_ast_generator` → IMPORT_OK；`py_compile` → OK；
- 落地证据为零回归字节级读数：站桩 6 面 `WORSE=0`、quotation 152/153 持平、28 探针 244/305（+3）。

**未提交 git**（按任务单要求，由主代理阶段边界统一提交）。
