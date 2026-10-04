# Round 10 任务 10.1b 复核报告（REVIEW2）

复核对象：修复批次 `b53d449c`（diff 基线 = 评审批次 `72f46912`）。零容忍立场：逐 hunk 审计 + 读数独立复跑（不信任修复自报）+ 哨兵口径裁决 + 变体攻击 + worktree 归因。判据工具 = scripts/pyc_verify.py（ruler sha 9c7567bd6776b36b，3.11.7）。

---

## §0 终判

**放行**。B72/B48/B46 封闭经独立复跑确证、判据纯同层结构事实、docstring 三要素与 C1/C2/C3 与代码逐条一致；两项实施降级如实登记且取证文件在案（D:\Temp\r10_incond.py / r10_then38.py 实测存在）；全哨兵面零回归（失败名单与基线逐位一致）；唯一新 MISMATCH 经 worktree @ 72f46912 逐字节同败证实为既有缺口（登记 B76），非修复引入。归因 worktree 已 remove 清零。

---

## §1 逐 hunk 判定表（git diff 72f46912 b53d449c -- core/，共 324 行，2 文件）

| # | 位置 | 内容 | 判据纯度审查 | 判定 |
|---|---|---|---|---|
| H1 | region_analyzer.py ~1984（`_B48_INPLACE_BINOP_MAP` + `_b48_attach_ternary_augassign`，+80 行） | B48 登记通道 | merge 块剥噪（RESUME/NOP/CACHE/PUSH_NULL 既有噪声族）→ 首个 STORE_* 回扫（仅跳 SWAP——attr/subscr 栈重排同层事实）→ BINARY_OP oparg ∈ [13,25] 类级映射表 = 3.11 `dis` nb_inplace 编码事实，**非魔法阈值**；无名字/文件白名单；无跨层回溯；无新增 self 跨方法状态（登记挂 region 属性，与 BoolOpRegion 既有通道同构）。docstring 三要素（识别条件/归约方式/AST 映射）+ C1/C2/C3 与代码逐条一致 | **PASS** |
| H2 | region_analyzer.py ~2082（`_detect_global_declarations`，-12/+9） | B72：移除 parent.co_cellvars 过滤 | STORE_DEREF ∧ argval ∈ co_freevars ∧ ∉ co_cellvars 直接命中 = code object 元数据（允许的同层事实）；co_cellvars 排除项保留（自建 cell 写 = 普通本地赋值，声明 nonlocal 反 SyntaxError）；孙代透传（中间层 co_cellvars 空）不再被误杀；fallback 路径的 parent_code 仅作元数据确认（C2 合规）。docstring 三要素完整，机制注释与代码一致 | **PASS** |
| H3 | region_analyzer.py ~22970/~23469/~23650（`_detect_ternary_pattern` B46，+1 标志/两道门放行/docstring 条款） | true 臂嵌套三元对称放行 | 判据 = `block_to_region` 成员关系 + 内层 entry 恒等 + `_jt_check ∈ 内层 blocks`（内层自身判别跳转，非语句逃逸边）+ false 单表达式 + 内层 merge 末 STORE_*/RETURN_* 终结（值被同块消费的栈事实）；`NOISE_OPS` 为模块级既有常量（:60）；两道拒绝门（`_boolop_merge_to_ternary` 门 + `false_is_ternary` 门）对称放行，未命中路径逐字节不变。docstring 三要素 + [C1][C2][C3] 完整 | **PASS** |
| H4 | region_analyzer.py ~24947/~25124（两处 TernaryRegion 构造点，+6 行） | `_b48_attach_ternary_augassign` 挂载 | 双构造点对称调用，纯登记 | **PASS** |
| H5 | region_ast_generator.py ~3175-3194（`_b68_is_tryfin_tail_releasable` B71 门控，+20 行） | finally 循环控制终结块显式排除 | opcode 白名单（POP_TOP/JUMP_FORWARD/JUMP_ABSOLUTE/JUMP_BACKWARD/JUMP_BACKWARD_NO_INTERRUPT）= BlockSemantics.is_break/is_continue 同层 opcode 事实；machinery 块必含 PUSH_EXC_INFO/POP_EXCEPT/RERAISE（不在白名单）→ 不会误吞异常帧；方向保守（宁可不释放不误吞）；与后续 machinery/栈操作扫描循环（3195-3206）共享 `_b68_fin_user` 语义一致 | **PASS** |
| H6 | region_ast_generator.py ~40544/~42493（`_generate_ternary` B48 发射，+52 行） | AugAssign 发射 + 未折叠 IfExp | `_b48_ternary_raw` 保留纯 IfExp 防折叠；发射端**双端同判据**复核（登记态 + merge_all[:store_idx] 反向扫描确认 in-place BINARY_OP，两源同一确定性映射表无错位可能）；AugAssign dict 与既有 Assign 路径共用 trailing 处理；docstring 三要素 + C1/C2/C3 完整 | **PASS** |

**「以少发射换全绿」审查**：全哨兵失败名单与基线逐位一致（§2/§3），变体面 v_aug_boolop_rhs 体蒸发经 pre-fix 逐字节同败证实既有（§5），零「以少发射」证据。

**降级自洽性**：B46 t_nest_in_condition（r7_07 唯一残留失败单元，与降级清单一致）与 B71（r10_21 2/4 与 HEAD 持平）降级理由与 FIX.md 记录自洽；两项取证脚本实测存在。

---

## §2 独立复跑读数（不信任修复自报，全部重跑）

| 面 | 文件 | 权威读数 | 修复自报 | 裁决 |
|---|---|---|---|---|
| B72 | r10_14 + r10_16 + n10_01..04 | **23/23**（7/7 + 7/7 + 9/9） | 7/7 + 7/7 + 9/9 | 一致 ✓ |
| B48 | r7_03 / r8_06 / r8_10 | **7/7 / 10/10 / 9/12** | 7/7 / 10/10 / 9/12 | 一致 ✓（r8_10 失败 = B56/B57/B58 登记面；任务书期望 8/12 系笔误，FIX.md 9/12 准确） |
| B46 | r7_07 | **6/7**（唯一失败 t_nest_in_condition = 降级项） | 6/7 | 一致 ✓ |

---

## §3 哨兵口径裁决（重点）

**「114/114 之谜」裁决**：修复自报「r6 面 107/107 + _cmp 7/7 = 114/114」**漏跑 n6_01_control.pyc（8 单元）**。本轮权威重跑 round6 全量 16 pyc：

| 哨兵面 | 权威读数 | 基线 | 裁决 |
|---|---|---|---|
| **round6 全量 16 pyc**（n6_01 + r6_01..15） | **115/115，零失败** | 115/115 | **零回归 ✓**（114/114 = 口径缺口非造假：r6_* 15 文件 107/107 属实 + _cmp 7/7 属实，唯 n6_01 缺席） |
| round6 rv6_01..07 变体面 | 18/29 | 18/29 | 失败 11 单元 = B37(2)/B38(2)/B39(3)/B40(1)/B41(3) 逐位持平 ✓ |
| _cmp.pyc | 无法复验 | — | `_cmpOK.py` 已被主代理清扫（b53d449c commit message 申报在案），以 f10_final_cmp.json 记录为准 |
| **round7 全量 16 文件** | **108/128** | 104/128 | **+4 = r7_03 2→0（B48）+ r7_07 3→1（B46）**；其余 20 失败单元（B42×3/B43/B44/B47/B48 宿主变体 t_host_while_body/B49/B50/B46 b_ternary_lhs_and 等）与基线逐位一致 ✓ |
| **round8 全量 13 文件** | **110/118** | 107/118 | **+3**；8 失败单元（r8_assert_nested_func/r8_dh_for_else_del/r8_dh_with_assert/r8_dh_match_multi/r8_x_assert_ternary/r8_x_for_iter_ternary/r8_x_raise_ternary_class/r8_dh2_match_guard）与基线逐位一致 ✓ |
| quotation | **152/153** | 152/153 | 唯一失败 change_his_to_forward 逐位一致 ✓ |
| 六哨兵 | **115/120** | 115/120 | trade_info_utils 5 失败（trade_operation/kill_trade_process/get_trade_status/query_trade_strategy_info/query_strategy_id）= 基线名单逐位一致 ✓ |
| option_account | **35/35** | 35/35 | ✓（任务书「302/308」= 六哨兵+option_account+quotation 三面合计口径，本轮实测 115/120 + 35/35 + 152/153 = **302/308** 完全复现） |

**裁决结论：零回归成立。** B48 封闭为主形态（merge 块 in-place BINARY_OP 前缀）；r7_08 t_host_while_body（round8 登记面标注 B48 归属）仍 MISMATCH 系 while 体宿主变体，判据未触达——与基线逐位持平，不构成回归，如实登记为 B48 残留变体（判据面已收敛，交下批认领）。

---

## §4 被改动探针 OK.py 抽验（4/6 ≥ 3 达标）

r10_14 / r10_16 / r7_03 / r8_06 四个 OK.py 临时重生成至独立目录逐行 diff：**4/4 零差异 = 纯 pycdc 重生成**，无手改。临时目录已删除，仓库文件零触碰。

---

## §5 变体攻击（B72/B48/B46 守卫边界外推，3 探针 27 单元 → rv10_variants.json）

| 探针 | 攻击面 | 读数 | 结果 |
|---|---|---|---|
| rv10_31_nonlocal_variant | nonlocal 只读闭包（LOAD_DEREF 无 STORE——守卫不触发）/ del（DELETE_DEREF）/ 双并行链 / nonlocal 增量赋值 / 循环宿主闭包 | **5/5** | 全 MATCH：B72 判据边界收放正确 |
| rv10_32_augassign_variant | attr/subscr 目标（守卫边界外）/ 冷门算子 >>= %= //= / BoolOp RHS / Assign 负对照 | **4/5** | attr/subscr 两态均正确发射（既有通道）；冷门算子 pre-fix `x = x + (t)` 降级 → post-fix `x >>= t` 正确（**B48 真增益实证**）；Assign 负对照无误判；**v_aug_boolop_rhs（`x += a or b`）函数体蒸发 = 新 MISMATCH → B76** |
| rv10_33_ternary_variant | false 臂嵌套（既有对称通道）/ 三层嵌套 / return 位 / 语句逃逸负对照 / BoolOp 条件 + true 臂嵌套 | **5/5** | 全 MATCH：B46 放行边界收放正确，逃逸负对照被正确拒绝 |

**B76 登记（编号续接 B75）**：augassign × BoolOp RHS 整句蒸发——`x += a or b` 全函数体丢失（仅剩 docstring），pre-fix（worktree @ 72f46912 重生成）产物逐字节同败 = **既有缺口**（B44/B62 族变体），非本批引入，不构成打回。判据草案（同层事实）：augassign 块 STORE 前为 JUMP_IF_TRUE_OR_POP 短路链 + BINARY_OP（oparg 任意）时 BoolOp 值重建必须消费短路链输出至 STORE；装配器对「块集非空但发射为空」必须报错禁止静默。P2。

**worktree 归因清零**：D:\Temp\rv10_wt @ 72f46912 用毕已 `git worktree remove --force`；`git worktree list` 仅剩主工作区。

---

## §6 遗留移交清单（不构成打回）

1. **B48 宿主变体**：r7_08 t_host_while_body（while 体宿主 augassign×三元，基线逐位持平）——判据面收敛待认领。
2. **B76**（§5 新登记）：augassign × BoolOp RHS 体蒸发，P2。
3. 既有降级：B46 t_nest_in_condition（融合条件三件套）、B71 fin_break/fin_continue 发射归属层（W11-A 认领分支）——取证脚本在案（D:\Temp\r10_incond.py / r10_then38.py）。
4. B42×3/B43/B44/B47/B49/B50/B51/B56–B62/B65/B69/B70 等残留名单逐位持平（§3），按原交接单继续。

---

## §7 复核产出物

- 本报告：rounds/round10/REVIEW2.md
- 验证输出：rv10_b72.json / rv10_b4846.json / rv10_round6_full.json / rv10_round6_variants.json / rv10_round7_full.json / rv10_round8_full.json / rv10_quotation.json / rv10_sentry.json / rv10_option.json / rv10_variants.json（均在 rounds/round10/）
- 变体探针：test_repros/round10/rv10_31..33（各含 .py/.pyc/OK.py）
