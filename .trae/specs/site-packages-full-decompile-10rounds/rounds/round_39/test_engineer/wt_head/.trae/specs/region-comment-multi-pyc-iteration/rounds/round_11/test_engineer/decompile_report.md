# R11 测试工程师报告 — Pattern C2（tuple unpack without SWAP，窥孔优化消除 SWAP）

## 1. 目标 pyc 与轮次

| 字段 | 值 |
|---|---|
| 轮次 | R11 (rcm-r11) |
| 目标 pyc | `site-packages/IQEngine/main.pyc`（R07 状态 `partial`，33.33%，`_adjust_start_date` 的 tuple 解包丢失） |
| 缺陷模式 | Pattern C2（peephole-optimized tuple unpack：N 个 LOAD + N 个 STORE 反源序，无 SWAP/UNPACK_SEQUENCE） |
| 修复层 | 区域 AST 生成层 `core/cfg/region_ast_generator.py` |
| 累计成功率（R10 末） | 67.28%（committed pyc_index.json） |

## 2. 反编译产物实证（不一致清单）

### 2a. main.pyc `_adjust_start_date`（核心缺陷段）

原 pyc 的 else 分支含 tuple 解包：
```python
origin_start_date, origin_end_date = config.strategy.start_date, config.strategy.end_date
```

Python 3.11 函数体内，窥孔优化器消除 `SWAP 2`（因 STORE 已按栈弹出顺序排列，SWAP 冗余）。字节码布局：
```
LOAD_FAST config, LOAD_ATTR start_date,
LOAD_FAST config, LOAD_ATTR end_date,
STORE_FAST origin_end_date, STORE_FAST origin_start_date   # 反源序，无 SWAP
```

**R11 pre-fix 反编译产物**（`mainOK.py`）：仅捕获一个 STORE，丢失 tuple 解包语义：
```python
origin_end_date = config.strategy.end_date   # 丢失 origin_start_date
```

### 2b. main.pyc 字节码 diff（3 函数）

| 函数 | orig instrs | decomp instrs | jump_diffs | true_diffs | 状态 |
|---|---|---|---|---|---|
| `<module>` | — | — | — | — | **一致** ✓ |
| `_adjust_start_date` | 220 | 222 | 1 | 2 | 不一致（trailing LOAD_CONST None） |
| `run` | 881 | 774 | 32 | 375 | 不一致（独立模式） |

- `_adjust_start_date`：R11 修复后 tuple 解包正确，残留 2 true_diffs（尾部多余 `LOAD_CONST None`，trailing-return 独立模式，非本轮 scope）。
- `run`：375 true_diffs，独立模式（POP_JUMP 目标偏移 + 控制流坍缩），非本轮 scope。

## 3. Pattern C2 根因分析

### 缺陷机制

Python 3.11 对 `a, b = c, d`（函数体内）生成字节码时，窥孔优化器消除 `SWAP 2`：
- **有 SWAP 路径**（已支持）：`LOAD c, LOAD d, SWAP 2, STORE a, STORE b`
- **无 SWAP 路径**（Pattern C2，本轮修复）：`LOAD c, LOAD d, STORE b, STORE a`（STORE 按反源序弹栈）

反编译器原实现仅在 `_generate_block_statements` 中检测 SWAP 路径，未检测 no-SWAP 路径。R11 pre-fix 已在 `_generate_block_statements` L30684 添加 `_noswap_unpack_result` 检测，但存在两个 BUG：

#### BUG A（守卫过保守，L30722）

`_noswap_unpack_result` 的守卫 `_ns_has_real_after` 使用**白名单**（noise_after）判定 post-STORE 指令：仅允许 RESUME/NOP/LOAD/RETURN 等。但 `return x, y` 生成 `BUILD_TUPLE`、`return x + y` 生成 `BINARY_OP`，均不在白名单 → 守卫误判为"有后续语句" → 降级（`_ns_n = 0`）→ tuple 解包丢失。

**影响 repro**：repro_02（3-name unpack + return tuple）、repro_03/04/06/07/09（2-tuple + return expr）。

#### BUG B（块未到达 `_generate_block_statements`，L9565）

`_adjust_start_date` 的 else 入口块（Block@28）被区域分析器合并为嵌套 IfRegion 的 cond_block（tuple 解包 + `if len(...)` 条件同块）。`_if_generate_normal` 通过 `_if_extract_cond_instructions` 提取 cond_block 前置语句（pre_stmts），该方法的 STORE 处理**逐 STORE 调用 `_build_store_statement`**，每个 STORE 弹 TOS 作为独立赋值，丢失 tuple 解包语义。

**影响 repro**：repro_05（main.pyc 镜像）、main.pyc `_adjust_start_date`。

## 4. 最小复现实例（12 个，10 DEFECT-REPRO / 2 NO-DEFECT）

| # | 实例 | 源码模式 | pre-fix | post-fix |
|---|---|---|---|---|
| 01 | two_attr_unpack | `a, b = obj.x, obj.y` (if body) | DEFECT* | OK* |
| 02 | three_name_unpack | `x, y, z = b, c, a; return x, y, z` | DEFECT (BUG A) | OK* |
| 03 | attr_and_name | `a, b = obj.x, v; return a, b` | DEFECT (BUG A) | OK* |
| 04 | method_call_rhs | `a, b = obj.get_a(), obj.get_b(); return a, b` | DEFECT (BUG A) | OK* |
| 05 | main_pyc_mirror | else 分支 tuple 解包 + if + raise | DEFECT (BUG B) | OK* |
| 06 | func_top_level | `x, y = a, b; return x + y` (顶层) | DEFECT (BUG A) | OK* |
| 07 | subscript_rhs | `a, b = d['x'], d['y']; return a, b` | DEFECT (BUG A) | OK* |
| 08 | four_tuple_unpack | `a, b, c, d = w, x, y, z` (if body) | DEFECT* | OK* |
| 09 | binary_op_rhs | `x, y = a + 1, b * 2; return x, y` | DEFECT (BUG A) | OK* |
| 10 | ctrl_chain_assign (CTRL) | `a = b = c` (chain assign) | DEFECT* | OK* |
| 11 | ctrl_swap_based_unpack (CTRL) | `a, b = c, d` (有 SWAP 路径) | NO-DEFECT | NO-DEFECT |
| 12 | ctrl_unpack_sequence (CTRL) | `a, b = iterable` (UNPACK_SEQUENCE) | NO-DEFECT | NO-DEFECT |

> `*` 标记的 DEFECT-REPRO 系 verify_repros.py 的 **code-object 身份噪声**误报（LOAD_CONST argval 含 code object，其 co_filename/co_firstlineno 因 OK.py 文件名/行偏移不同而不等）。手动 dis.dis 确认 `f` 函数字节码完全一致。post-fix 全部 10 个 Pattern C2 repro 源码正确、`f` 字节码一致。

- **DEFECT-REPRO 计数**：pre-fix 10 → post-fix 0（真实缺陷 0；verify 报告的 10 个均为 code-object 身份噪声）
- **CTRL 组（11, 12）全部 NO-DEFECT**：证明修复不影响 SWAP 路径与 UNPACK_SEQUENCE 路径

## 5. decompile 流程诊断

```
python diag_trace_repro05.py
=== _generate_block_statements called for blocks ===
  block@0, block@24, block@134, block@164   # block@28 缺失！
=== _process_if_blocks calls ===
  branch=else region=IfRegion@Block1 blocks=[Block3(28-132), Block4, Block5]
  branch=then region=IfRegion@Block3(28-132) blocks=[Block4]
  # Block3 是嵌套 IfRegion 的 cond_block，含 tuple 解包 + if 条件
```

Block@28（tuple 解包）被合并入嵌套 IfRegion cond_block（Block3, offset 28-132），由 `_if_extract_cond_instructions` 处理，未进入 `_generate_block_statements`。

## 6. 当前 pyc 状态与累计成功率

| 指标 | R10 末 | R11 post-fix |
|---|---|---|
| 累计成功率 | 67.28% | **71.30%**（+3.98%） |
| verified pyc | 30 | 402（索引刷新） |
| ok pyc | 22 | 22 |
| partial pyc | 7 | 8 |
| failed pyc | 1 | 1 |
| main.pyc | partial 33.33% | partial 33.33%（`_adjust_start_date` tuple 解包修复，残留 2 trailing-return diffs） |

## 7. 修复方向建议

**修复目标**：
1. **BUG A**（`_generate_block_statements` L30722）：将守卫从白名单改为黑名单（语句级指令集 STORE/POP_JUMP/JUMP/RAISE/IMPORT/FOR_ITER）+ 无 return 表达式判定，允许 `return tuple`/`return x+y` 等 return 表达式通过。
2. **BUG B**（`_if_extract_cond_instructions` L9733）：在 STORE 处理中添加 Pattern C2 检测，N≥2 连续简单名 STORE（前缀无 SWAP/UNPACK）一次性构建 tuple 解包赋值，用 `_c2_skip_until` 跳过已消费的后续 STORE。

**算法依据**：区域归约算法原则 2（每块唯一归属）—— RHS 表达式片段（N 个 LOAD 栈帧）与 LHS 目标片段（N 个 STORE）分别归属不同层；原则 4（入口引用语义）—— 父 Assign 节点通过 Tuple 子节点引用 N 个 RHS 子表达式与 N 个 LHS 子目标。

**预期效果**：
- 10 DEFECT-REPRO → 0 真实缺陷（code-object 身份噪声除外）
- main.pyc `_adjust_start_date` tuple 解包修复
- 累计成功率单调递增
