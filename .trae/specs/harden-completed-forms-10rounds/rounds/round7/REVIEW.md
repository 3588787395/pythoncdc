# Round 7 评审报告（评审工程师 · 对抗攻击批次）

- 评审人：评审工程师（Round 7，任务 7.1，独立攻击，零容忍）
- 日期：2026-10-03
- 攻击对象：wiki 台账已判「无感完备」的表达式形态——**Ternary（IfExp，台账 :12654 / `_identify_ternary_regions`:22025）+ 链式比较（`_identify_chained_compare_regions`:16953）+ 表达式面 BoolOp 组合**——实测「深层与浅层产物结构一致」声明
- 树状态：HEAD = `02dc780c`（round7 启动快照）；core/、parsers/、scripts/、pycdc.py 相对 Round 6 放行态（75ca08bd）**零改动**
- 唯一判据：`scripts/pyc_verify.py`（pylingual compare_pyc，Python 3.11.7）；全部 r7_*/n7_* OK.py 仅经 `pycdc.py -o` 再生成，零手改；未修改 core/、parsers/、scripts/、pycdc.py、spec.md/tasks.md 及既有 REVIEW/FIX；全部命令 ≤300 s
- 复现盘面：`test_repros/round7/`（r7_01–r7_14 + n7_01–n7_02，源码 + pyc + OK 产物）；报告：`rounds/round7/r7_all.json`、`rounds/round7/r7_residual.json`

## 终判：**打回**（攻击面发现即登记，不做修复）

三形态浅层（负对照 10/10 MATCH、链式比较基本面 7/7、短路调用面 7/7）成立，但**深层位置面/嵌套面/交叉组合面 32/128 单元 MISMATCH（12/16 文件 failure），台账「完备」声明不可扩展至深度维**。另登记 1 项在途缺陷打回项（R7-O1，§8 备忘 F2 副带实测确证）。新破口 **B42–B51 十族**（§5）。

---

## §1 攻击面读数总表

探针源码 `test_repros/round7/r7_*.py`（`python -c "import ast; ast.parse(...)"` 全部预检通过后 `py_compile` 编译，pyc 自 `__pycache__` 复制）；OK 产物 `pycdc.py -o` 生成；读数 = `pyc_verify.py single` 实测（status + units），批量对账 = `r7_all.json`（16 文件 128 单元，与逐文件 single 读数逐位一致）。

| 探针 | 攻击面 | 单元 | MATCH | 判定 | 机制归因（OK.py ↔ 源码 diff 实证） |
|---|---|---|---|---|---|
| r7_01_ternary_args_index | 三元实参（单/多参混合/嵌套 call）+ 下标值 + 双侧切片 + 下标比较 + 下标存储目标 | 9 | 7 | **MISMATCH** | t_arg_multi_mixed：`return min(t1,t2,3)` → 裸 `min(t1,t2)`——**return 剥除 + 第 3 实参蒸发**；t_subscript_index_ternary：`xs[ti]+ys[tj]` → `(ti)+(tj)`——**容器加载 xs/ys 蒸发**（B42） |
| r7_02_ternary_containers | dict 值/键/键值双三元、list/set/tuple 元素、嵌套容器 | 8 | 5 | **MISMATCH** | t_dict_both_ternary：`{kT: vT}` → 裸 `k1 if c1 else k2`——**dict 塌缩为裸三元**；t_list_element：**首元素 a 蒸发**；t_nested_container：**键 "k" 丢失且 list→set**（B42） |
| r7_03_ternary_stmt_pos | return 位/赋值 RHS/augmented 赋值（+=、*=、-=）/多目标/解包 RHS 三元 | 7 | 4 | **MISMATCH** | t_augassign_ternary：`x += t` → `x = x + (t)`（降级）；t_augassign_mul_ternary：`*=`/`-=` **双误发射为 `+`**（操作符丢失，语义破坏）；t_unpack_ternary：**尾随 `return m + n` 蒸发**（B48 / B42） |
| r7_04_ternary_binop_compare | binop 两侧/单侧三元、比较两侧/单侧、比较入参、幂 | 7 | 5 | **MISMATCH** | t_compare_both_sides：`(aT) < (bT)` → 裸 `a if f1 else b` + `return x if f2 else y`——**比较节点蒸发、三元泄漏为裸 Expr**；t_compare_lhs_only 同签名（B42） |
| r7_05_ternary_comprehension | listcomp/dictcomp（值+键）/setcomp/genexp/嵌套 comp/过滤三元 | 16 | 15 | **MISMATCH** | 仅 t_listcomp_ternary_filter.<listcomp> 败：元素 `x if flag else 0` → `0`（三元塌缩）且过滤 `(x%2 if flag else True)` → `flag and x % 2`（重结合，语义反转风险）（B42） |
| r7_06_ternary_lambda_await | lambda 体三元 ×3、await 三元分支/赋值/深嵌 | 10 | 7 | **MISMATCH** | lambda 三元全 MATCH；**await 三元 3/3 全败**：`await io.a() if flag else await io.b()` → `None if flag else None`——**await 臂值蒸发为 Constant None**（B47） |
| r7_07_ternary_nest | 右结合/左结合嵌套三元、三连链、条件位嵌套、臂含 binop、元组双三元 | 7 | 4 | **MISMATCH** | 右结合/三连链/元组 MATCH；**左结合 `(aT) if c2 else d` 3/3 提升为 if/else 语句**（return 分裂）；t_nest_in_condition 另丢 **false 臂 `else 0` 整段**（B46） |
| r7_08_ternary_deep_host | if 臂/while 体/for-else/try 三段/with 体/match case/async for 体 | 8 | 4 | **MISMATCH** | t_host_while_body：`acc += t` → `= acc + (t)`（B48）；t_host_for_else：**else 子句整体蒸发**、else 体语句线性外提（B49）；t_host_try_sections：try 体三元蒸发 + **finally 语句泄漏进 try + 幻影 return**（B50）；t_host_match_case：case 体三元提升为 if/else 双 return（B46） |
| r7_09_chain_compare_basic | 链式比较基本面（同向/混合算子/三链/in-not-in/is-is not） | 7 | 7 | MATCH | 浅层声明面成立（含 `a <= b != c`、`a < b <= c < d` 混合链） |
| r7_10_chain_compare_calls | 链内调用/混合调用、链内下标/pop、链∧BoolOp 组合、方法链 | 8 | 7 | **MISMATCH** | c_chain_and_combo：`a < b < c and d` → `a < b < c`——**尾部合取 d 蒸发**；调用链/下标链/双链 or 组合全 MATCH（B43） |
| r7_11_boolop_mixed | and/or/not 混排优先级、not 组合、not a == b | 7 | 6 | **MISMATCH** | 仅 b_and_or_repeat：`(a and b) or (b and c) or a` → `a and b or b and c and a or a`——**末项 `or a` 误并入第二个 And**（结合性重排）（B44） |
| r7_12_boolop_nest | BoolOp 嵌套 ≥3 层、嵌套比较链、嵌套三元、not 多层 | 8 | 4 | **MISMATCH** | b_nest_three_layers：`(a and b) and (c or d)` → `a and b and c`——**Or 臂塌缩、d 蒸发**；b_nest_deep_right：`a and (b or (c and d))` → `a and b or c and d`（**层级重排**）；b_nest_deep_mixed：外层 And 提升为 if 且 **`(d or e)` 整臂蒸发**（B44/B45）；b_ternary_lhs_and：三元提升 if/else（B46） |
| r7_13_boolop_shortcut | 短路副作用调用序列（and/or 链式调用、if 守卫、赋值 RHS） | 7 | 7 | MATCH | 调用序列与短路语义完整保持 |
| r7_14_boolop_deep_host | if/while/推导式过滤复合条件、条件位三元+链、return 复合体 | 9 | 4 | **MISMATCH** | h_while_composite：`while n>0 and (a<b or flag)` → `if n>0: while a<b or flag`——**合取外提出循环=每次迭代不复查（语义破坏）**；h_listcomp_filter_composite：过滤尾合取 `(flag or x%2)` 蒸发（B43）；h_if_ternary_chain_composite：`if a if flag else b<c` → **体 return 蒸发为 pass、return 'f' 误位 't'**（B51）；h_return_composite：三元提升 + else 臂 `or flag` 蒸发（B46）。h_if_composite 产物为嵌套双 if 但字节码同构 → verify Equal（不计 MISMATCH） |
| **攻击面合计** | 14 文件 | **118** | **86** | **32 MISMATCH / 12 文件** | |
| n7_01–n7_02（负对照） | 单层三元 / 单层 and/or | 10 | 10 | MATCH（§2） | |
| **总计** | 16 文件 | **128** | **96** | 75.00%；success 4 / failure 12 | |

分形态读数：Ternary 位置面（r7_01–08）51/72；链式比较（r7_09–10）14/15；BoolOp 组合（r7_11–14）21/31。三形态均 ≥10 复现（53/13/25 个复现函数，单元数含嵌套 code object 与模块级）。

## §2 负对照结果

| 负对照 | 形态 | 单元 | MATCH |
|---|---|---|---|
| n7_01_simple_ternary | 单层三元（return/assign）+ 单层 and/or/not | 5 | **5/5** |
| n7_02_simple_andor | 单层 or/and 链 + 三元实参 + if 混合 | 5 | **5/5** |

两负对照全 MATCH：浅层判定面正常工作，**深层 MISMATCH 为深度/组合维真实缺口**（非判据系统性失效），亦反证失败探针的最小归因成立。

## §3 Round 6 残留复验表

方法：5 支 rv6 pyc 先经当前核重反编译，MD5 与已提交 OK.py **逐一 SAME（零漂移）**，后 `pyc_verify.py single` 实测 + `r7_residual.json` 批量对账（10/21，5 文件 failure）。

| 探针 | 登记面（Round 6） | 本轮实测 | MISMATCH 名单 | 变差判定 |
|---|---|---|---|---|
| rv6_01_asyncwith_threestate | 3/5 | **3/5** | aw_break_in_try_for、aw_continue_in_try_for（B37 面） | 持平 |
| rv6_02_outer_handler_boundary | 2/4 | **2/4** | outer_raise_catch、nested_with_else_loop（B38 面） | 持平 |
| rv6_04_finally_deferred_double | 1/4 | **1/4** | try_fin_with_nested、double_fin_overwrite、try_fin_fin_body_with（B39 面） | 持平 |
| rv6_05_yieldfrom_mixed_else | 3/4 | **3/4** | gen_for_else_mixed（B40 面） | 持平 |
| rv6_06_withitem_deep_async | 1/4 | **1/4** | deep_tuple_star、star_mid_async、nested_star_tuple（B41 面） | 持平 |

**结论：B37–B41 登记面逐文件逐单元持平，零回归。**

## §4 合规审计结果（在途变更审计）

| 项 | 判定 | 实测证据 |
|---|---|---|
| BOM（G0 红线） | **通过** | `head -c 3 core/cfg/region_ast_generator.py | xxd` = `efbb bf` |
| 插桩残留（R23N21_DEBUG/_patch_dbg/_probe_r） | **通过** | `grep -rn "R23N21_DEBUG\|_patch_dbg\|_probe_r" core/ | wc -l` = **0** |
| 在途变更面 | **通过（无可审新增）** | `git diff 75ca08bd..HEAD -- core/ parsers/ scripts/ pycdc.py` = 空；`git log -1 -- core/` = 75ca08bd（Round 6 放行态）。`_b34b_`/`_b34c_`/`_is_setup` 周边代码均系 Round 6 已审放行代码，无新增判据 |
| 名字白名单 / start_offset 魔数 / 跨层回溯 / 新 self 跨方法状态（新增面） | **通过** | 放行态后零新增，无从触发红线；历史 self 状态（`_current_loop`/`_or_then_block`/`_chain_compare_expr_cache` 等）均前代已审 |
| **R7-O1（打回项）** | **❌ 失同步** | `region_ast_generator.py:9276-9277`：`p = _poll_succ_of(cur)` 后**无 `if p is None: return None` 短路**即 `_resume_of_poll(p)`（p=None 时 `for i in p.instructions` → AttributeError 崩溃）；而 `_collect_await_protocol_chain` docstring [C2]（:9207-9209）仍声明「链不闭合（缺 setup/poll/resume 任一环）即返回 None」。与 Round 6 REVIEW2 §8 备忘 1 完全吻合——**docstring 与代码行为失同步在途缺陷实测确证**，交修复工程师按 tasks.md 7.2 处理（恢复短路或同步 [C2] 条款） |
| R7-O2（观察项，非新增） | 记录 | `region_analyzer.py:17381-17435` 存在 7 处 `_R23N20_DEBUG` env 门控插桩，含 `block.start_offset == 342` 魔数探针——系 a6666b92 代码（先于本 spec 存在，非本轮/上轮新增），本轮红线 grep 面未覆盖；不构成打回，建议后续轮次一并清理 |

## §5 新破口登记（B42 起；编号续接 B41）

### B42 — 含三元操作数的外围表达式结构蒸发（P0）
- **锚点**：`region_ast_generator._generate_ternary`(:38717) 输出形态 (1)/(2)/(3) 分支与外围表达式装配的衔接 + `_build_ternary_value_expr`(:37938)、`_extract_dict_prefix_values`(:45442)/`_ternary_prefix_stack_effect`(:45533) 栈效应模型；识别侧 `region_analyzer._identify_ternary_regions`(:22025)/`_detect_ternary_pattern`(:22840)。
- **机制**：三元区域归约把外围表达式的非三元栈项（容器构建/键、比较节点、实参、RETURN 终结、解包后继语句）误并进三元区域或重装配时静默丢弃——浅层单三元不受影响，深层组合位面崩塌。docstring 自称「字节码一致性 100%（ternary 116/116）」，本轮 9 单元实证该声明不可扩展至嵌套位置面。
- **最小复现**：`r7_04 t_compare_both_sides`（比较节点蒸发）、`r7_02 t_dict_both_ternary/t_nested_container/t_list_element`、`r7_01 t_subscript_index_ternary/t_arg_multi_mixed`（return+实参蒸发）、`r7_03 t_unpack_ternary`（尾随 return 蒸发）、`r7_05 t_listcomp_ternary_filter.<listcomp>`（元素塌缩+过滤重结合）。共 9 单元。
- **回归哨兵**：n7_01/n7_02 5/5、r7_05 t_dictcomp_ternary 等 15 MATCH 单元。

### B43 — 链式比较 ∧ BoolOp 组合的尾部合取蒸发（P1）
- **锚点**：`_identify_chained_compare_regions`(:16953)/`_build_chained_compare_region`(:21753) 与 `_detect_boolop_chain_start`(:26387) 的区域抢占边界；生成侧 `_chain_compare_expr_cache`(:13503)/`_chain_head_active`(:19285)。
- **机制**：`<链> and/or X` 的链式比较区域识别吞并尾合取块且重装配时只发射链——`a < b < c and d` → `a < b < c`。链与链的 or 组合（r7_10 c_chain_or_and_combo）MATCH，唯链∧单一合取形态破。
- **最小复现**：`r7_10 c_chain_and_combo`、`r7_14 h_listcomp_filter_composite`（+.<listcomp>）。共 3 单元。

### B44 — BoolOp 嵌套 BoolOp 再结合/塌缩（P1）
- **锚点**：`_generate_boolop_impl`(:36394) + `_suppress_boolop_merge_tail`(:19328)；识别侧 `_identify_boolop_regions`(:23420)/`_build_basic_if_region`(:19710) 的 main_inline_boolop_chain 参数。
- **机制**：多层嵌套 BoolOp 的链重建按扁平链处理，嵌套层级丢失 → 结合性重排（`(b and c) or a` → `b and c and a`）或嵌套 Or 臂整段塌缩（`(c or d)` → `c`，d 蒸发）——语义改变。
- **最小复现**：`r7_11 b_and_or_repeat`、`r7_12 b_nest_three_layers/b_nest_deep_right`。共 3 单元。

### B45 — 复合布尔条件被拆成宿主控制流（循环复查语义破坏）（P0）
- **锚点**：`_detect_while_condition_boolop_chain`(:25580)/`_detect_while_boolop_forward_chain`(:26316) + IfRegion 装配路径。
- **机制**：`while A and B` 的合取被外提出循环（`if A: while B:`）——A 每次迭代不再复查，纯语义破坏；外层 And 条件提升为 if 时嵌套臂整段蒸发且无 false 路径发射。
- **最小复现**：`r7_14 h_while_composite`、`r7_12 b_nest_deep_mixed`。共 2 单元。

### B46 — 三元提升为 if/else 语句 + false 臂丢失（P1）
- **锚点**：`_identify_ternary_regions`(:22025) 识别判据（左结合三元/条件或臂含嵌套 BoolOp·三元时识别失败）→ IfRegion 通用路径接管；`_generate_ternary`(:38717) 形态 (1) 未触达。
- **机制**：表达式位三元被提升为语句 if（return 分裂、字节码形态改变：双 RETURN_VALUE），部分形态 false 臂整段丢失（`else 0` 蒸发 → 隐式 None，语义破坏）。右结合与纯常量链 MATCH。
- **最小复现**：`r7_07 t_nest_left_assoc/t_nest_in_condition/t_nest_mixed_binop`、`r7_12 b_ternary_lhs_and`、`r7_14 h_return_composite`、`r7_08 t_host_match_case`。共 6 单元。

### B47 — async 宿主 await 三元臂值蒸发为 None（P1）
- **锚点**：`_build_ternary_value_expr`(:37938) 与 await 协议链消费（`_collect_await_protocol_chain`(:9166) 调用方 :9421/:9526/:9580/:9815）的块归属冲突。
- **机制**：async def 内三元臂含 await 调用协议链时，臂块被 await 链消费/标记 generated，三元臂值重建无源 → `Constant None` 回填（`await io.a() if flag else await io.b()` → `None if flag else None`）。裸 await（r6 异步面全绿）与 lambda 三元均 MATCH，唯二形态交叉破。
- **最小复现**：`r7_06 t_await_ternary_branches/t_await_assign_ternary/t_await_deep_ternary`。共 3 单元。

### B48 — augmented 赋值 × 三元 RHS：操作符丢失降级（P1）
- **锚点**：三元 value_target 路径（`_generate_ternary` 形态 (1) Assign 重建）与 in-place BINARY_OP(arg≥13) 判据（:2930-2940 附近）未覆盖 RHS 含三元区域形态。
- **机制**：RHS 为三元区域时赋值装配走 TernaryRegion 的 Assign 重建（固定 `x = x + (t)` 模板）——`+=` 降级（字节码形态改变）；`*=`/`-=` **操作符误发射为 `+`（语义破坏）**。无三元 RHS 的 augassign（`n -= 1`）MATCH。
- **最小复现**：`r7_03 t_augassign_ternary/t_augassign_mul_ternary`、`r7_08 t_host_while_body`。共 3 单元。

### B49 — for-else else 体含三元增强赋值时 else 子句蒸发（P2）
- **锚点**：`_loop_generate_for`(:4710) else 装配（B35 拆分判据面）。
- **机制**：else 体语句被 B48 同源 TernaryRegion 认领后，for-else else 块归属判据不再命中，else 体被当作循环后线性语句发射（else 语义 = 正常结束才执行 → 语义破坏）。
- **最小复现**：`r7_08 t_host_for_else`。1 单元。

### B50 — try 体三元蒸发 + finally 语句泄漏进 try + 幻影 return（P2）
- **锚点**：`_generate_try`(:27893) 体装配 + B42 同源过认领。
- **机制**：try 体首语句（双下标臂三元）区域归约失败后块归属悬空，try/finally 装配把 finally 段并入 try 体并补 Return（`return r` 落入 try 内）——语句错位 + 幻影 return。
- **最小复现**：`r7_08 t_host_try_sections`。1 单元。

### B51 — if 条件为三元+链式比较复合体时体蒸发/return 错位（P2）
- **锚点**：IfRegion 条件装配与 TernaryRegion/链式比较区域对同一条件块的归属竞争。
- **机制**：`if a if flag else b < c:` 条件块归属被改写后体发射走错合并块——体 `return "t"` 蒸发为 `pass`、尾随 `return "f"` 误位为 `return 't'`（常量错位）。
- **最小复现**：`r7_14 h_if_ternary_chain_composite`。1 单元。

### 归属总表

| 编号 | 归属 | 证据 |
|---|---|---|
| B42–B51 | 既有缺口（深度/组合维变体新暴露，非修复引入） | core/ 自 75ca08bd 放行态零改动（§4）——本轮全部 MISMATCH 均产生于已放行代码，无在途修复可归因；负对照 10/10 MATCH 证明浅层判定面未变 |

## §6 交接单（按优先级排序，供修复工程师认领）

| 序 | 项 | 优先级 | 类型 | 修复要求（判据只允许同层结构事实） | 自测哨兵 |
|---|---|---|---|---|---|
| 1 | **R7-O1** docstring [C2] 失同步（:9276-9277 缺 `if p is None: return None` 短路） | 打回项 | 机械修复 | 恢复短路或同步 [C2] 条款（二选一，代码与注释必须一致） | BOM efbbbf + round6 115/115 + r6 异步面（r6_05–08、12、13）全绿 |
| 2 | **B42** 三元操作数外围结构蒸发 | P0 | 算法修复 | 三元区域归约的栈效应模型补外围非三元栈项（容器构建/键/比较/RETURN/实参）的归属与重发射 | n7 10/10 + r7_05 15/16 不变差 + 本轮 B42 面 9 单元转 MATCH |
| 3 | **B45** while/if 复合条件外提变形 | P0 | 算法修复 | 复合条件的链成员必须留在循环/分支条件位 | r7_13 7/7 + h_while_composite 转 MATCH |
| 4 | **B46** 三元提升 if/else + false 臂丢失 | P1 | 算法修复 | 左结合三元/臂含 BoolOp·三元识别面补齐（识别→归约→AST 映射三要素 + C1/C2/C3） | t_nest_right_assoc/t_nest_three_chain MATCH 保持 |
| 5 | **B43** 链式比较∧BoolOp 尾合取蒸发 | P1 | 算法修复 | 链区域与 BoolOp 链区域抢占边界按块末跳转形态互斥判定 | r7_10 7/8 不变差 |
| 6 | **B44** BoolOp 嵌套再结合/塌缩 | P1 | 算法修复 | 嵌套层级在链重建中保持（禁止扁平化） | b_nest_not_layers/b_nest_with_chain MATCH 保持 |
| 7 | **B47** await 三元臂 None 回填 | P1 | 算法修复 | await 协议链消费与三元臂块归属冲突消解 | r6 异步面全绿 + r7_06 lambda 面 MATCH 保持 |
| 8 | **B48** augassign×三元操作符丢失 | P1 | 算法修复 | TernaryRegion Assign 重建透传原 in-place 操作符 | t_host_while_body/t_augassign 面 3 单元转 MATCH |
| 9 | **B49/B50/B51** else 蒸发 / try 泄漏 / 条件位复合体 | P2 | 算法修复 | 认领修复后按块归属重验 else/finally/体发射次序 | r7_08 其余 4 MATCH 单元保持 |

**总回归哨兵清单（修复自测 = 全部保持 + 本轮 MISMATCH 转 MATCH）**：round6 全量 16 文件 115/115；rv6 面 18/29 持平（B37–B41 不变差）；六哨兵（tools 6/6、trade_schedule 6/6、mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils 36/41）+ option_account 35/35；本轮 n7_01/n7_02 5/5、r7_09 7/7、r7_13 7/7 全 MATCH 面及各文件部分 MATCH 面禁变差（r7_01 7/9、r7_02 5/8、r7_03 4/7、r7_04 5/7、r7_05 15/16、r7_06 7/10、r7_07 4/7、r7_08 4/8、r7_10 7/8、r7_11 6/7、r7_12 4/8、r7_14 4/9）。

---

## 附：复现产物清单

- `test_repros/round7/r7_01_ternary_args_index.{py,pyc,OK.py}` … `r7_14_boolop_deep_host.{py,pyc,OK.py}`（14 攻击文件）
- `test_repros/round7/n7_01_simple_ternary.{py,pyc,OK.py}`、`n7_02_simple_andor.{py,pyc,OK.py}`（2 负对照）
- `rounds/round7/r7_all.json`（16 文件 batch 报告）、`rounds/round7/r7_residual.json`（rv6 残留 batch 报告）
- 编译链：`ast.parse` 预检 → `py_compile.compile` → `__pycache__/*.cpython-311.pyc` 复制为 `*.pyc` → `pycdc.py -o *OK.py` → `pyc_verify.py single/batch`
- 评审过程零修改 core/、parsers/、scripts/、pycdc.py、spec.md/tasks.md；未手改任何既有 *OK.py
