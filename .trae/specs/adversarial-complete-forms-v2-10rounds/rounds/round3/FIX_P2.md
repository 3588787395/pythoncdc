# Round 3 修复位 2（FIX_P2）：B99 for 宿主 BoolOp 蒸发封闭（识别/认领层）

- 涉改文件：`core/cfg/region_analyzer.py`（**唯一**；未改 `region_ast_generator.py`，未手改任何 `*OK.py`）
- 对应评审：`rounds/round3/REVIEW.md`（B99 主目标、B1b 次目标；评审给出候选锚点 `region_analyzer.py:27978 _b1b_loop_body_run_continuation`，但明确「待修复工程师定位真正的断链点」）
- 落地状态：**代码已落地**（见 §8 声明与 grep 锚点）

> 评审候选锚点 `_b1b_loop_body_run_continuation` 经实测**不是**断链点。真正的两个断链点均在识别/认领层（见 §1、§3），已定位并封闭。

---

## 1 破口 → 修复动作 → 落地位置 → 判据 → 恢复的 C 条款

| 破口 | 根因（同层结构事实） | 修复动作（算法语义） | 落地位置 file:line | 判据（I.4 白名单） | 恢复条款 |
|---|---|---|---|---|---|
| **B99-断链点 1**：`for` 体内 `return <值位 BoolOp>`，链在短路跳转处被截断为单元素 → 表达式蒸发/退化为 `return None` | CPython 3.11 对 `for` 体内 `return <表达式>` 排出**隐藏迭代器拆除段** `SWAP 2; POP_TOP; RETURN_VALUE`；其 `SWAP+POP_TOP` 与链式比较清理块（`[R113 fix]` 引入）指令序列**完全同形**，被 `_is_chained_compare_cleanup_block` 误判 → `_detect_boolop_short_circuit_chain` 的 R113 分支把值位 BoolOp 链当比较链截断 | 清理块识别加**前驱守卫**：仅当该块存在「以短路跳转收尾、且跳转前紧跟比较族操作码（`COMPARE_OP`/`IS_OP`/`CONTAINS_OP`）」的前驱时才认定为真·比较链清理块；否则按普通值位操作数继续常规链走查 | `region_analyzer.py:30069-30076`（R113 分支守卫）+ 新增方法 `:31131`（`_has_compare_chain_step_predecessor`） | 块末 opcode 族（`SHORT_CIRCUIT_JUMP_OPS`）+ 前驱集合 + 前驱块内指令 opcode（`NOISE_OPS` 过滤后） | **C1**（只读同层块结构事实）+ **C2**（真·链式比较判定逐位不变）+ **C3**（对同形拆除段显式排除，守卫封闭） |
| **B99-断链点 2（主因）**：`for: if i: return <值位 BoolOp>` 形态下整条 `return` 消失为 `return None` | `_can_be_ternary_header` 把**值上下文 BoolOp 链步块**（末指令为 `JUMP_IF_*_OR_POP`，即 `SHORT_CIRCUIT_JUMP_OPS`）误当作 ternary 条件头；因该链步短路跳转的汇合点恰是隐藏迭代器拆除段，`_detect_ternary_pattern` 误判为钻石形，建出与 `BoolOpRegion` **同入口**的重叠 `TernaryRegion`；`get_entry_region_for_block` 在同优先级(3)下按块跨度误选 `TernaryRegion`，使 `_process_if_blocks` 的 R61 兜底从不调用 `_generate_boolop` → IfRegion 直接产出 `Return(None)` | 三元条件头判据加**收尾极性守卫**：块末为 `SHORT_CIRCUIT_JUMP_OPS` 时直接判否（真·ternary 条件恒以条件跳转 `FORWARD/BACKWARD_CONDITIONAL_JUMP_OPS` 收尾；短路跳转是 BoolOp 链步自身求值，其语义是「把当前操作数短路留在栈上并跳出」，非分支选择） | `region_analyzer.py:22580-22594`（`_can_be_ternary_header` 内新增守卫） | 块末指令 opcode 族（`SHORT_CIRCUIT_JUMP_OPS` vs `FORWARD/BACKWARD_CONDITIONAL_JUMP_OPS`） | **C2**（黑箱组合：ternary 与 BoolOp 各自独立保真，不再互相遮蔽）+ **C3**（守卫封闭 ternary 认领域）+ 原则 2「每块唯一归属」（链步块唯一归 `BoolOpRegion`） |

---

## 2 改动明细（改前 / 改后关键片段）

### 2.1 `_detect_boolop_short_circuit_chain` R113 分支（`:30069-30076`）

```python
# 改前
if last.argval is not None:
    _jt_block = self.cfg.get_block_by_offset(last.argval)
    if _jt_block is not None and self._is_chained_compare_cleanup_block(_jt_block):
        op_type = 'and' if 'FALSE' in last.opname else 'or'
        chain.append((current, op_type))
# 改后
if last.argval is not None:
    _jt_block = self.cfg.get_block_by_offset(last.argval)
    if (_jt_block is not None
            and self._is_chained_compare_cleanup_block(_jt_block)
            and self._has_compare_chain_step_predecessor(_jt_block)):
        op_type = 'and' if 'FALSE' in last.opname else 'or'
        chain.append((current, op_type))
```

**解释**：`for` 体内 `return <表达式>` 的拆除段与比较清理块同形。追加「比较链步前驱」守卫后，拆除段不再走 R113 跳过逻辑，值位 BoolOp 链得以完整走查。守卫未命中即逐位维持原行为（C2）。

### 2.2 新增方法 `_has_compare_chain_step_predecessor`（`:31131`）

```python
def _has_compare_chain_step_predecessor(self, block: BasicBlock) -> bool:
    for _pred in block.predecessors:
        _pred_last = _pred.get_last_instruction()
        if _pred_last is None or _pred_last.opname not in SHORT_CIRCUIT_JUMP_OPS:
            continue
        _pred_meaningful = [i for i in _pred.instructions
                            if i.opname not in NOISE_OPS]
        if (len(_pred_meaningful) >= 2
                and _pred_meaningful[-2].opname in ('COMPARE_OP', 'IS_OP',
                                                    'CONTAINS_OP')):
            return True
    return False
```

**解释**：真·比较链清理块的必要结构事实是「存在以短路跳转收尾、跳转前紧跟比较族操作码的前驱」。循环返回拆除段的前驱是普通操作数块（`LOAD_* + JUMP_IF_*_OR_POP`），不含比较族操作码，据此区分。带完整六项模板 docstring + C1/C2/C3（对照表见 §6）。命名无 I.5 禁用前缀。

### 2.3 `_can_be_ternary_header` 新增守卫（`:22580-22594`）

```python
# 改前：（Round4-04 chained_compare 守卫循环之后直接）
            if block not in self.block_to_region:
# 改后：在守卫循环之后、`if block not in self.block_to_region:` 之前插入
            if last.opname in SHORT_CIRCUIT_JUMP_OPS:
                for _r in self.regions:
                    if (isinstance(_r, IfRegion)
                            and _r.region_type == RegionType.IF
                            and _r.entry is block):
                        ...                                      # chained_compare 既有豁免保持
                        break
                # [B99 fix] 值上下文 BoolOp 链步块不是 ternary 条件头。 ...（完整中文注释）
                return False
            if block not in self.block_to_region:
```

**解释**：值位 BoolOp 链步块（末指令 `JUMP_IF_*_OR_POP`）不再被认领为 ternary 条件头，杜绝与 `BoolOpRegion` 同入口的重叠 `TernaryRegion`。真·ternary 条件恒以条件跳转收尾，故本守卫对一切真三元为恒真通过（C2）。

---

## 3 判据合规自证（I.4 白名单）

**用到的全部判据（同层块结构事实）**：
- 块末指令 opcode 族：`SHORT_CIRCUIT_JUMP_OPS` / `FORWARD_CONDITIONAL_JUMP_OPS` / `BACKWARD_CONDITIONAL_JUMP_OPS`（`region_analyzer.py` 内定义）；
- 前驱集合：`block.predecessors`、块内指令序列（`NOISE_OPS` 过滤）；
- 指令 opcode：`COMPARE_OP` / `IS_OP` / `CONTAINS_OP` / `SWAP` / `POP_TOP`；
- 区域成员关系：`self.regions`、`IfRegion.entry` / `region_type`（仅按入口身份与类型筛选，不做跨层 `X.entry in Y.blocks` 反查）。

**黑名单自查（逐项）**：
- 文件名 / 函数名白名单：**无**（无任何 `name == 'xxx'` 判据）；
- `start_offset` 魔法阈值作比较常数：**无**；
- 跨层 `X.entry in Y.blocks` 反查：**无**；
- 新增 `self` 跨方法状态：**无**（`git diff` 新增 `self.x =` 计数 = 0；全部为局部变量与入参）；
- 以少发射换全绿：**无**（未削减任何发射；改动只改「是否认领/截断」）；
- 硬编码深度 / 计数上限：**无**。
- I.5 禁用方法名前缀（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）：**零新增**（唯一新增方法 `_has_compare_chain_step_predecessor` 语义化命名）。

---

## 4 自测读数表（RV2：先改代码 → regen → verify；判据唯一 = `scripts/pyc_verify.py`）

> **关键**：`pyc_verify` 只读取同名 `*OK.py` 产物、**不会重新反编译**。每次改代码后必须先 `python pycdc.py <pyc> -o <OK.py>` 重建全部产物，否则读数无效。本轮全部读数均在重建产物后取得。

### 4.1 本轮 28 探针回归（`test_repros/round3/`，证据 `r3v2_probe_results_fixP2.json`）

| 读数 | 基线（位 1 修复后） | 本轮（FIX_P2） | 判读 |
|---|---|---|---|
| 单元级 | 244/305 | **248/305（+4）** | 达标（不得低于基线） |
| COMPILE_ERROR | 3 | 3 | 持平 |
| `NEWFAIL`（success→failure 位移） | — | **0** | 无回归 |
| e01_g1_b98_matrix | 5/15 | 5/15 | 持平 |
| e02_g1_b98_hosts | 10/18 | **11/18（+1）** | 改善 |
| e03_g1_b1b_stress | 9/14 | 9/14 | 持平（B1b 残留，见 §7） |
| ne01_g1_neg | 1/5 | **4/5** | B99 平坦/成对形转 MATCH |
| ne10_g10_neg | 1/3 | 1/3 | 持平 |

**FIXED 单元（逐改名集合比对）**：`e02 <module>.CB98.m_class_body_host`、`ne01 n_flat_and`、`ne01 n_flat_or`、`ne01 n_simple_two`。

### 4.2 位 1 零回归确认（`region_ast_generator.py` B98 改动区不受影响）

| 复现 | 基线 | 本轮 | 判读 |
|---|---|---|---|
| `test_repros/round3/e01_g1_b98_matrix.pyc` | 5/15 | 5/15 | 持平 |
| `test_repros/round3/e02_g1_b98_hosts.pyc` | 10/18 | 11/18 | 不下降 |
| `test_repros/round2/rv3_02_b89_boolop_chain.pyc` | 1/1 | **1/1 success** | 持平 |
| `test_repros/round3/_scratch_b98/hosts.pyc` | 7/7 | **7/7 success** | 持平 |

### 4.3 最小复现（`test_repros/round3/_scratch_b99/`）

- `b99min.pyc`（8 函数）：`for_noif` → `return a or b or c` ✓；`for_host_plain` → `return a or b or c` ✓；`for_flat_and` → `return a and b and c` ✓；`w_host` / `top` / `if_top` / `while_noif` 保持正确 ✓。**`for_grouped`（`return (a or b) and c`）未封闭**（§7）。
- 对照（`ne01`）：`n_flat_or` / `n_flat_and` / `n_simple_two` 转 MATCH；`n_grouped_pair` 残留。

### 4.4 站桩回归 6 面（`r3v2_fixP2_station.py` + `r3v2_compare_regress.py`，全部 `WORSE=0`）

| 面 | 基线 | 本轮 | same / improved / **WORSE** |
|---|---|---|---|
| round2face（45） | 234/251 | 234/251 | 45 / 0 / **0** |
| probe42（42） | 154/189 | 172/196 | 32 / 10 / **0** |
| round1face（24） | 417/423 | 417/423 | 24 / 0 / **0** |
| residual（72） | 404/446 | 417/446 | 62 / 10 / **0** |
| oldface（59） | 658/692 | 664/692 | 55 / 4 / **0** |
| quotation 单验 | 152/153 | 152/153 | 持平（唯一失败 `change_his_to_forward`） |

> 改善集中在 round7 boolop/ternary 混合面（`r7_07_ternary_nest` 6→7、`r7_08_ternary_deep_host` 4→7、`r7_11_boolop_mixed` 6→7、`r7_12_boolop_nest` 5→6）与 round2/round10 类体、模块、导入面。

### 4.5 交付前门禁自检

| 项 | 结果 |
|---|---|
| `import core.cfg.region_analyzer` | IMPORT_OK |
| `python -m py_compile core/cfg/region_analyzer.py` | PY_COMPILE_OK |
| BOM 单头 `efbbbf` | 首 6 字节 `ef bb bf 22 22 22`，全文 `bom_count=1` |
| I.5 禁用前缀新增方法 | 0（唯一新增方法语义化命名） |
| 插桩残留（新增 `print(`/`pdb`/`breakpoint(`/`# TODO`/`# FIXME`/`# DEBUG`/`# XXX`） | 0 新增（`git diff` 命中计数 = 0） |
| 新增 `self` 跨方法状态 | 0 |
| `region_ast_generator.py` 改动 | 无（本轮未触碰；位 1 B98 改动区隔离） |
| `*OK.py` 手改 | 无（全部由 `pycdc.py -o` 重建） |

---

## 5 恢复的 C 条款归纳（I.3）

- **C1 局部消费**：两处守卫只读同层块结构事实（块末 opcode 族、前驱集合、前驱块内指令 opcode），不跨层、不读名字、不读阈值。
- **C2 黑箱组合**：`BoolOpRegion` 与 `TernaryRegion` 各自独立保真组合；守卫未命中一律走既有分支（逐位不变）。真·链式比较、真·三元行为不变。
- **C3 守卫封闭**：对与比较清理块同形的循环返回拆除段显式排除；值位 BoolOp 链步块显式排除出 ternary 认领域，恢复「每块唯一归属」。

---

## 6 注释六项模板对照表（I.7）

| 方法（file:line） | ①算法依据 | ②归约顺序 | ③唯一归属判定 | ④嵌套处理 | ⑤入口引用语义 | ⑥反编译流程位置 | C1/C2/C3 |
|---|---|---|---|---|---|---|---|
| `_has_compare_chain_step_predecessor` `:31131` | 真·比较链清理块必有「短路跳转收尾 + 跳转前紧跟比较族操作码」前驱 | 作为 `_is_chained_compare_cleanup_block` 前置谓词，任意时点求值 | 仅判存在性，不认领块 | 只查一层直接前驱，不展开嵌套 | 不返回块、不引用入口 | BoolOp/链式比较归约期清理块识别守卫 | C1/C2/C3 齐全 |
| `_is_chained_compare_cleanup_block` `:31185` | **本方法只按 `SWAP 2 + POP_TOP` 指令序列（NOISE_OPS 过滤后恰两条有效指令）判定「清理块形态」，不做任何前驱判定**；B99 的「比较链步前驱」追加条件由调用点（R113 分支）以 `_has_compare_chain_step_predecessor` 施加，不在本方法内 | 归约期按需调用，只判不认领 | 只判形态、不认领块；命中的块交调用方决定（R113 分支再经守卫，`_get_effective_merge_through_cleanup` 按可穿透语义下溯） | 只读本块指令序列与 opcode，不跨层 | 不返回块、不引用入口 | BoolOp/链式比较归约期清理块识别原语 | C1（只读本块指令序列与 opcode，同层结构事实）/ C2（形态相同则判定逐位不变）/ C3（本方法只判形态；对循环返回拆除段的显式排除由调用点 `_has_compare_chain_step_predecessor` 施加，守卫封闭在调用侧）——与代码逐字一致 |
| `_can_be_ternary_header` 新增段 `:22580` | ternary 条件恒以条件跳转收尾；短路跳转是 BoolOp 链步求值 | ternary 识别期条件头判定段 | 短路收尾块判否（`:22598`）→ 唯一归 `BoolOpRegion` | 存在性判定不展开嵌套 | 不返回块、不引用入口 | `_identify_ternary_regions` 条件头认领守卫 | C1/C2/C3 **显式齐全**（`:22594-22597`，评审整改项 B 已闭环） |

---

## 7 残留未封闭项（如实登记，未以少发射/硬编码深度/名字白名单换绿）

| 项 | 形态 | 现象 | 归属层 | 处置 |
|---|---|---|---|---|
| **B99 混合分组形** `for_grouped` / `ne01.n_grouped_pair` | `for: if i: return (a or b) and c` | 残留 spurious `IfRegion@14`（entry=14，条件块 @18，@14 末指令为 `POP_JUMP_FORWARD_IF_TRUE` 条件跳转）；`BoolOpRegion@18` 仅捕获 `and` 步、`op_chain=[18]`，`or` 步（条件跳转化为的 @14）未纳入 → 输出 `if (a or b) and c: pass`（`return` 消失） | 识别层（本文件），但与真·ternary 收尾极性不同：该形是**条件跳转与短路跳转混合**的链（`or` 步用值位丢弃型条件跳转），需链检测层扩展「条件跳转步」的认领，改动面与风险大于本位守卫域 | 移交后续（如扩展须专门站桩回归） |
| **B1b-1** `f_b1b_and_or_and` | `if a and b or c and d:` | Different control flow → `if not (a and b): if c and d:`（`and,or,and` 三段链未统一） | 识别层 `_detect_boolop_conditional_chain` | 移交后续 |
| **B1b-2** `f_b1b_deep_right` | `if a or (b and (c or d)):` | Different control flow → `if not a: if b and (c or d):`（`or,and,or` 三段链） | 识别层 | 移交后续（评审亦允许如实登记） |
| **B1b-3** `f_b1b_none_check_prefix` | `if s is None or a:` | Different control flow → `if s is not None: if a and i:`（`POP_JUMP_FORWARD_IF_NONE` 首步 `or` 丢失、极性反转） | 识别层（`NONE_CHECK_OPS` 首步的 `or` 认领） | 移交后续 |
| **B1b-4** `f_b1b_loop_body_chain` | `while: if a and b or c: ...else...` | Different control flow → `if a: if b or c:`（`and,or` 链在 while 体+else 宿主下未统一） | 识别层 | 移交后续 |
| **B1b-5** `f_b1b_ifexp_trueval` | `for: if i: return (a and b) if c else (a or b)` | Different bytecode → 裸表达式语句 + `return None`（真三元 `TernaryRegion@40` 的 `merge_block` 停在隐藏迭代器拆除段 @58，未下溯到 `RETURN` @62，`return` 包裹丢失） | 生/识交叉：真三元 `merge_block` 未穿越拆除段下溯 | 移交后续 |

> 上述 6 项均**未**以少发射、硬编码深度/计数上限或名字白名单换取绿；本轮 28 探针 248/305（+4）与站桩 6 面 WORSE=0 为**净改善**读数。

---

## 8 落地声明（I.6）

**代码已落地。** 校验锚点（grep 树内命中，非仅归档）：

- `grep -n "\[B99 fix\]" core/cfg/region_analyzer.py` → 4 处（代码守卫锚点 `:22580`、`:30069`；新方法 docstring 内引用 `:31135`、`:31190`）；
- `def _has_compare_chain_step_predecessor` → `:31131`（新方法，六项模板 docstring + C1/C2/C3）；
- R113 分支守卫行 `_has_compare_chain_step_predecessor(_jt_block)` → `:30076`；
- `import core.cfg.region_analyzer` → IMPORT_OK；`py_compile` → PY_COMPILE_OK；BOM `bom_count=1`；
- 落地证据为零回归字节级读数：28 探针 248/305（+4）、位 1 零回归（e01 5/15、e02 11/18、rv3_02 1/1、hosts 7/7）、站桩 6 面 `WORSE=0`、quotation 152/153 持平。
- 证据 JSON（**FIX_P2 期实际归档名**，与无后缀的更早基线/评审产物区分）：`r3v2_probe_results_fixP2.json`、`r3v2_full_round1face_fixP2.json`、`r3v2_full_residual_a_fixP2.json` / `r3v2_full_residual_b_fixP2.json`、`r3v2_full_oldface_a_fixP2.json` / `r3v2_full_oldface_b_fixP2.json`、`r3v2_regress_round2face_fixP2.json`、`r3v2_regress_probe42_fixP2.json`、`r3v2_station_regress_compare_fixP2.json`；驱动 `r3v2_fixP2_station.py`。（FIX_P1 期同名读数并存归档为 `*_fixP1.json`，未覆盖。）

**未提交 git**（按任务单要求，由主代理阶段边界统一提交）。

---

## 9 整改（REVIEW2 §5.2 打回项闭环）

> 本段为 Task 3.3 复核**打回项 A / B**（I.7 项）的整改记录。**纯文档级，零算法改动**：仅改注释/docstring 文本，未改任何判据、控制流或发射逻辑；行号可位移，逻辑 hunk = 0。

### 9.1 打回项 A —— `_is_chained_compare_cleanup_block` docstring ① 与代码行为不符

- 事实（复核）：docstring ① 声称方法体追加了 `_has_compare_chain_step_predecessor` 守卫，但方法体未变；守卫实际施加在**调用点** `_detect_boolop_short_circuit_chain` R113 分支。
- **改前文本**（① 算法依据，`:31183`）：
  ```
  链式比较（`a < b < c` 等）在值上下文由 [R113 fix] 引入的清理块
  （SWAP 2 + POP_TOP）承载中间值抹除；清理块的指令序列与 `for` 循环体
  内 `return <表达式>` 的隐藏迭代器拆除段（SWAP 2; POP_TOP; RETURN_VALUE）
  完全同形。原实现仅凭两条有效指令（SWAP + POP_TOP）判定，会把循环
  返回拆除段误判为比较链清理块，使 `for` 体宿主下的值位 BoolOp 消费链
  在短路跳转处被 R113 分支截断（B99 表达式蒸发）。[B99 fix] 追加
  `_has_compare_chain_step_predecessor` 守卫：只有存在「短路跳转收尾且
  跳转前紧跟比较族操作码」的前驱块时才认定为清理块。
  判据只读同层块结构事实（块末 opcode 族 + 前驱集合 + 前驱块指令
  opcode），符合 I.4 白名单。
  ```
- **改后文本**（① 算法依据，`:31184-31193`）：
  ```
  链式比较（`a < b < c` 等）在值上下文由 [R113 fix] 引入的清理块
  （SWAP 2 + POP_TOP）承载中间值抹除。**本方法只按 `SWAP 2 + POP_TOP`
  指令序列（NOISE_OPS 过滤后恰两条有效指令）判定「清理块形态」，不做
  任何前驱判定**；因该指令序列与 `for` 循环体内 `return <表达式>` 的隐藏
  迭代器拆除段（SWAP 2; POP_TOP; RETURN_VALUE）完全同形，单凭本方法会把
  循环返回拆除段一并判为清理块。B99 的「比较链步前驱」追加条件由**调用点**
  （`_detect_boolop_short_circuit_chain` 的 R113 分支）以
  `_has_compare_chain_step_predecessor` 施加，不在本方法内。判据只读本块
  指令序列与 opcode，符合 I.4 白名单。
  ```
- **C 条款尾行改后文本**（`:31218-31221`）：
  ```
  满足 C1（只读本块指令序列与 opcode，同层结构事实）/ C2（真实链式比较
  判定不变：形态相同则判定逐位不变）/ C3（本方法只判形态；对循环返回
  拆除段的显式排除由调用点 `_has_compare_chain_step_predecessor` 施加，
  守卫封闭在调用侧）。
  ```
- **方法体原样证据**：`_is_chained_compare_cleanup_block`（def 现 `:31185`）方法体仍为原 **4 行**（`:31223-31226`）：
  `meaningful = [...] / if len(meaningful) == 2 and meaningful[0].opname == 'SWAP' and meaningful[1].opname == 'POP_TOP': / return True / return False`，无任何前驱守卫调用。守卫调用点 `_has_compare_chain_step_predecessor(_jt_block)` 仍在 R113 分支 `:30076`（未移动、未增删）。

### 9.2 打回项 B —— `_can_be_ternary_header` 新增段缺显式 C1/C2/C3

- 事实（复核）：FIX_P2 §6 声明该段「C1/C2/C3 齐全」，但代码该段注释为散文，未显式给出 C1/C2/C3。
- **改后文本**（在守卫注释段末尾、`return False` 前补 3 行，`:22594-22597`）：
  ```
  # C1：只读本块末指令 opcode 族（SHORT_CIRCUIT_JUMP_OPS），同层结构事实；
  # C2：真 ternary 条件恒以条件跳转收尾，不被本守卫命中；守卫未命中
  #     时逐位维持既有 ternary 认领行为，BoolOp 与 ternary 各自独立保真；
  # C3：守卫封闭 ternary 认领域，令值位 BoolOp 链步块唯一归 BoolOpRegion。
  ```
- **守卫位置原样证据**：`if last.opname in SHORT_CIRCUIT_JUMP_OPS:` 守卫段仍在 `_can_be_ternary_header` 内、`if block not in self.block_to_region:` 之前（未移动）；仅在其注释块内追加 3 行注释，`return False` 顺延至 `:22598`。

### 9.3 「纯文档级、零算法改动」自证（逻辑 hunk = 0）

| 证据 | 方法 | 结果 |
|---|---|---|
| **AST 恒等** | `test_repros/round3/_scratch_b99/doconly_check.py`：将当前文本按 A/B 三处编辑**反向还原**为整改前文本 → 各自 `ast.parse` + 剥离 docstring → `ast.dump` 比较 | **`LOGIC_AST_EQUAL = True`**（`cur_len=1687539`，`pre_len=1687185`，`delta=354` 全部来自注释/docstring 文本） |
| **git diff 逐 hunk** | `git diff -- core/cfg/region_analyzer.py`（HEAD 已含位 2 阶段一逻辑提交 `7090ad96`，故 diff 仅含本轮 doc-only 编辑） | 3 个 hunk，**全部为 `#` 注释行 / docstring 文本**：`@@ -22591`（+4 注释行）、`@@ -31183`（docstring ① 段重写）、`@@ -31213`（docstring C 条款尾行重写）；**无任何可执行语句行增删** |
| **diff 统计** | `git diff --stat -- core/cfg/region_analyzer.py` | `1 file changed, 16 insertions(+), 11 deletions(-)`（均为注释/docstring） |
| **BOM** | 首 6 字节 + 全文计数 | `ef bb bf 22 22 22`，`bom_count=1` |
| **编译/导入** | `python -m py_compile core/cfg/region_analyzer.py`；`import core.cfg.region_analyzer` | `PY_COMPILE_OK` / `IMPORT_OK` |

### 9.4 抽验读数（regen 后 `pyc_verify.py batch`，判据唯一）

| 抽验 pyc | 期望 | 实测 | 判读 |
|---|---|---|---|
| `test_repros/round3/e02_g1_b98_hosts.pyc` | 11/18 | **11/18** | 持平（doc-only 无位移） |
| `test_repros/round3/ne01_g1_neg.pyc` | 4/5 | **4/5** | 持平（doc-only 无位移） |

> 两者均**先 `pycdc.py -o <OK.py> <pyc>` 重建产物**再 `pyc_verify batch`（证据 `test_repros/round3/_scratch_b99/doconly_sample.json`）。读数与整改前一致，印证 doc-only 未触及任何判据/发射。

**整改落地状态**：打回项 A / B 均已闭环，`FIX_P2.md` §6 对照表对应两行已同步为与整改后代码逐字一致。
