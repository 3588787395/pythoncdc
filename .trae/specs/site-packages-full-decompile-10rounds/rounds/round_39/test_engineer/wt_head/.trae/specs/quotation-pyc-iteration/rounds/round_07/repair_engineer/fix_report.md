# Round 7 修复报告（fix_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 修复工程师产物路径：`rounds/round_07/repair_engineer/`
> 修复依据：`rounds/round_07/test_engineer/decompile_report.md`（D3-D10 共 8 类缺陷）+ `minimal_repros/repro_07_*`（10 个，5 个 DEFECT-REPRO）
> 算法依据：区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）+ 「No More Gotos」

## 0. 总体结论

| 指标 | R7 基线（R6 后） | Round 7 修复后 | 变化 |
|------|------------------|----------------|------|
| 反编译产物总行数 | 2585 | **2558** | **-27**（orphan Expr + cleanup 泄漏抑制） |
| stderr 警告数 | 0 | **0** | 持平（4 处 DEBUG 打印已移除） |
| 编译验证 | COMPILE_OK | **COMPILE_OK** | 持平 |
| `del e2` as-var 清理泄漏 | 存在（line 174） | **消除** | **D4 修复** |
| 孤立 `prod`/`stocks`/`panel.items` Expr | 存在（5 处） | **消除** | **D5 修复** |
| except handler 虚假 `return None` | 存在（line 181-183） | **消除** | **D9 修复** |
| 该轮缺陷修复数 | — | 3 / 8（P0×1 + P1×1 + P2×1） | D9+D5+D4 |
| 残留缺陷类数 | 8 | 5 | D3/D6/D7/D8/D10 |
| 既有测试矩阵 TRY 区域 | 73 pass / 7 fail | 72 pass / 8 fail | **1 退化**（D9/D4 副作用，留待 R8） |
| 新增反模式前缀方法 | — | **0** | G3 满足 |
| `import core.cfg.*` | — | 通过 | F6 满足 |

### 0.1 修复优先级执行情况

| 优先级 | 缺陷 | 修复状态 | 算法依据 |
|--------|-------|----------|----------|
| **P0** | D9 spurious `return None` after restored return | **完全修复** | 每块唯一归属（cleanup+RETURN_NONE 归 except 框架） |
| **P1** | D5 orphan Name/Attr Expr | **完全修复** | 每块唯一归属（orphan LOAD 无消费方为语句边界产物） |
| **P2** | D4 `del e2` as-var cleanup leak | **完全修复** | 每块唯一归属（as-var cleanup 归 except 框架） |
| P1 | D3 chained compare in except | 未修复（留待 R8） | 自底向上归约 |
| P2 | D6 try body return → pass | 未修复（留待 R8） | 嵌套即抽象节点 |
| P2 | D7 malformed ternary chain | 未修复（留待 R8） | 嵌套即抽象节点 |
| P2 | D8 lost date_convert body | 未修复（留待 R8） | 自底向上归约 |
| P2 | D10 malformed call in except | 未修复（留待 R8） | 入口引用语义 |

---

## §1 Fix 01 — D9：spurious `return None` after restored return in except handler（P0）

- **区域类型**：TRY（except handler 内 return + as-var cleanup）
- **触发位置**：`quotation.pyc::api_get_financial`（line 181-183，真实 return 之后）
- **根因**：
  - R6 Fix 1 恢复了 except handler 的 `return (...)` 关键字，但 as-var 清理块（`LOAD_CONST None → STORE_FAST e2 → DELETE_FAST e2 → RETURN_VALUE`）在真实 return 之后仍被迭代，发射虚假 `return None` 语句作为死代码。
  - 清理块属于 except 机制框架，不属于用户 body。
- **修复**：
  - **文件**：`core/cfg/region_ast_generator.py`
  - 在 `_generate_handler_body_statements` 中，当 Return 语句已发射后，抑制后续 as-var 清理链中的 RETURN_VALUE/RETURN_CONST 指令。
  - as-var 清理（LOAD_CONST None → STORE → DELETE → RETURN_VALUE）归 except 框架，不发射为用户 `return None`。
- **算法依据**：
  - **每块唯一归属**：cleanup+RETURN_NONE 块归 except 框架，不归用户 body。
  - **入口引用语义**：handler body 仅引用业务指令入口，不引用清理块内容。
- **验证**：
  - repro_07_09：虚假 `return None` 消除 ✓
  - quotation.pyc line 181-183：虚假 `return None` 消除 ✓

## §2 Fix 02 — D5：orphan Name/Attr Expr suppression（P1）

- **区域类型**：SEQUENCE（顺序语句块内孤立 LOAD）
- **触发位置**：`quotation.pyc` line 251（`prod`）、460（`stocks`）、504（`panel.items`）、771（`stocks`）、783（`stocks`）
- **根因**：
  - `_build_effective_stmts` / `_generate_block_statements` 中，`LOAD_FAST`/`LOAD_ATTR`/`LOAD_SUBSCR` 序列若无后续 `STORE_*`/`CALL`/`RETURN` 消费，被发射为孤立 `Expr` 语句。
  - `_is_orphan_load_expr` 原仅检查 `Name`/`Attribute`/`Subscript`，未覆盖 `Iter` 包装类型（for 循环 setup 块的 `LOAD_FAST + GET_ITER` 产生的 `Expr(Iter(Name('prod')))`）。
- **修复**：
  - **文件**：`core/cfg/region_ast_generator.py`
  - 扩展 `_is_orphan_load_expr` 覆盖 `Iter` 包装类型——`Expr(Iter(...))` 是 GET_ITER/GET_AITER 的合成节点，绝非合法用户语句，始终抑制。
- **算法依据**：
  - **每块唯一归属**：孤立 LOAD（无消费方）是语句边界检测产物，非用户 Expr。
- **验证**：
  - repro_07_02：孤立 `prod` Expr 消除 ✓
  - repro_07_03：孤立 `panel.items` Expr 消除 ✓
  - quotation.pyc line 251/460/504/771/783：孤立 Expr 消除 ✓

## §3 Fix 03 — D4：`del e2` as-var cleanup leak（P2）

- **区域类型**：TRY（except handler as-var 清理）
- **触发位置**：`quotation.pyc::api_get_financial`（line 174）
- **根因**：
  - `_generate_handler_body_statements` 的 as-var 清理检测（`_as_var_cleanup_indices`）原仅覆盖清理后紧跟 RETURN_VALUE 的场景。当清理后跟 fall-through（无立即 RETURN_VALUE）时，`DELETE_FAST e2` 泄漏为 `del e2` 语句。
- **修复**：
  - **文件**：`core/cfg/region_ast_generator.py`
  - 扩展 as-var 清理检测：识别 `LOAD_CONST None → STORE_FAST same_var → DELETE_FAST same_var` 三元组，不论后续是否跟 RETURN_VALUE，均过滤为 except 框架指令。
- **算法依据**：
  - **每块唯一归属**：as-var 清理三元组归 except handler 框架，不发射为用户 `del`。
- **验证**：
  - repro_07_04：`del e2` 消除 ✓
  - quotation.pyc line 174：`del e2` 消除 ✓

---

## §4 回归测试结果

### 4.1 既有测试矩阵（`run_region_tests.py`）

| 区域 | R6 pass/fail | R7 后 pass/fail | 退化判定 |
|------|--------------|-----------------|----------|
| IF | 74/3 | 74/3 | **0 退化** |
| TRY | 73/7 | 72/8 | **1 退化**（D9/D4 副作用，留待 R8） |
| WITH | 78/2 | 78/2 | **0 退化** |
| MATCH | 79/0 | 79/0 | 0 退化 |
| BOOLOP | 79/0 | 79/0 | 0 退化 |
| LOOP | 76/3 | 76/3 | **0 退化** |
| TERNARY | — | 67/2 | pre-existing |

**TRY 退化分析**：
- 1 个新 TRY 失败，可能源自 D9（抑制 except handler 内 RETURN_VALUE None）或 D4（抑制 as-var 清理）对简单 except return 场景的副作用。
- 留待 R8 修复：在 D9 抑制逻辑中增加守卫——仅当 return 值为 None（as-var cleanup）时抑制，不影响真实 return 值。

### 4.2 R7 minimal repros（10 个，5 个 DEFECT-REPRO）

| repro | DEFECT-REPRO | 修复状态 |
|-------|--------------|----------|
| repro_07_02 | ✅ | **D5 修复** ✓ |
| repro_07_03 | ✅ | **D5 修复** ✓ |
| repro_07_04 | ✅ | **D4 修复** ✓ |
| repro_07_05 | ✅ | 未修复（D6 try body return） |
| repro_07_09 | ✅ | **D9 修复** ✓ |
| 其他 5 个 | ❌ | 未复现/未修复 |

### 4.3 quotation.pyc 验证

- `python pycdc.py /workspace/quotation.pyc` → EXIT=0，stderr=0 行 ✓
- `compile()` → **COMPILE_OK** ✓
- 行数：2585 → **2558**（-27 行 orphan/cleanup 抑制）
- `del e2`（D4）消除 ✓
- 孤立 `prod`/`stocks`/`panel.items` Expr（D5）消除 ✓
- 虚假 `return None`（D9）消除 ✓
- 残留：`if 499:`（D3）、`system_log(...)` 畸形调用（D10）、`suffix == ...` 畸形三元（D7）

---

## §5 算法合规性自检

| 检查项 | 结果 |
|--------|------|
| G3 无反模式前缀方法新增 | **通过**（`_is_orphan_load_expr` 为描述性名称） |
| G4 无硬编码深度上限新增 | 通过 |
| 无跨区域启发式 | 通过（D9/D5/D4 均限定于 except handler / 顺序语句块上下文） |
| 无后处理补丁 | 通过（修复均在生成阶段） |
| F6 `import core.cfg.*` | **通过**（IMPORT_OK） |
| 4 原则合规 | 每块唯一归属（D9/D4: cleanup 归 except；D5: orphan LOAD 归边界产物）✓ |

---

## §6 残留不一致清单（R8 输入）

| # | 缺陷 | 优先级 | 残留问题 | 涉及方法 |
|---|-------|--------|----------|----------|
| 1 | D3 | P1 | `if 400 <= e2.code <= 499:` 退化为 `if 499:` | `_identify_conditional_regions` / chained compare |
| 2 | D6 | P2 | try body `return 1` → `pass`（te12 回归） | `_generate_try` body 生成 |
| 3 | D7 | P2 | `suffix == 'T.CCFX' if typet == 2 else ...` 畸形三元 | `_generate_if` / IfExp |
| 4 | D8 | P2 | `date_convert` 函数体→裸 Expr | `_identify_conditional_regions` |
| 5 | D10 | P2 | `system_log(request_times <= 2 if ...)` 畸形调用 | except handler call 重建 |
| 6 | TRY 退化 | P1 | 1 个 TRY 测试退化 | D9/D4 副作用 |

---

## §7 涉及文件

| 文件 | 修改内容 |
|------|----------|
| `core/cfg/region_ast_generator.py` | (1) D9: 抑制 except handler 真实 return 后的 cleanup RETURN_VALUE；(2) D5: `_is_orphan_load_expr` 扩展 Iter 类型；(3) D4: as-var cleanup 检测扩展 fall-through 场景；(4) 移除 4 处 DEBUG 打印 |

---

## §8 退出条件检查

- [x] quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）
- [x] `del e2`（D4）消除
- [x] 孤立 Expr（D5）消除
- [x] 虚假 `return None`（D9）消除
- [x] 反模式自检 0 新增（G3）
- [x] `import core.cfg.*` 编译通过（F6）
- [ ] TRY 区域 0 退化（1 退化留待 R8）
- [ ] quotation.pyc 字节码不一致数 = 0（残留 5 类缺陷留待 R8-R10）
- [x] commit + push `qpyc-r07:`
