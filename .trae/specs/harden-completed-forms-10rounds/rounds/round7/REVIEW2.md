# Round 7 复核报告（评审工程师 · 复核批次 / REVIEW2）

- 复核人：评审工程师（Round 7 任务 7.3 复核批次，独立复验，零容忍）
- 日期：2026-10-03
- 复核对象：commit `c0ab03c1`（Round 7 修复批次一：R7-O1 / R7-O2 / B45 2/2 / B42 6/9）
- 树状态：复核起点 HEAD = `c0ab03c1`；复核进行期间主代理归档 commit `a1c55316` 落地（仅 VERIFICATION.md + 分片 json + tasks.md 勾选，`git diff c0ab03c1 -- core/ parsers/ scripts/ pycdc.py` = **空**，core 与 c0ab03c1 逐位一致，全部复跑读数不受影响）
- 唯一判据：`scripts/pyc_verify.py`（pylingual compare_pyc，Python 3.11.7）；复核期间临时 json（r7_rev1 / r6_rev1 / rv6_rev1）已用后删除；未修改 core/、parsers/、scripts/、pycdc.py、既有 REVIEW/FIX/VERIFICATION；全部命令 ≤300 s

## 终判：**放行**

逐 hunk 合规（14/14 PASS，判据面全部为同层结构事实）、FIX.md 三项判据面声明与代码逐条相符（含全空段守卫对 n7_01 纯裸三元路径的真实保护路径核对）、全部读数逐位复跑相符（r7 104/128、round6 115/115、rv6 18/29 持平、哨兵 36/41+52/52、BOM/插桩 0）、变体攻击 4 探针 12/15 MATCH（4 单元由 pre-fix 败转 MATCH＝补强实证，3 单元 MISMATCH 均与 pre-fix 逐位同败＝既有缺口变体，零回归），新登记 B52/B53 交后续批次。

---

## §1 逐 hunk 合规判定表（`git show c0ab03c1 -- core/`，14 hunks）

判据红线：零名字白名单 / 零 start_offset 魔数 / 零跨层回溯修正 / 零新 self 跨方法状态；判据必须为同层结构事实（块内首条件跳转定位、操作码栈效应、区域归属、merge 边身份）。

| # | 文件:位置 | 内容 | 判据面（实测核读） | C1/C2/C3 | 判定 |
|---|---|---|---|---|---|
| H1 | analyzer :17378-17382 | R7-O2 清除 _R23N20_DEBUG 站点 1-2（含 `import traceback` 死代码） | 纯减法，无条件触碰 | — | **PASS** |
| H2 | analyzer :17388-17394 | R7-O2 清除站点 3-4 | 纯减法 | — | **PASS** |
| H3 | analyzer :17415-17424 | R7-O2 清除站点 5-7（含 `start_offset == 342` 魔数探针） | 纯减法；7 站点计数与 FIX.md 一致 | — | **PASS** |
| H4 | analyzer :25501-25577（Step 6） | 值上下文 BoolOp 链 pop-form 链头补全 | 块末 opcode 族（POP_JUMP_*IF_TRUE/FALSE 六族）+ 跳转目标 ∈ 链偏移集 + fall-through is 链头 + block_to_region 归属 + 多候选拒绝；极性映射 IF_TRUE→or / IF_FALSE→and | 注释块 [C1][C2][C3] 在位 | **PASS** |
| H5 | analyzer :25661-25668 + :26379-26513 | `_detect_while_condition_nested_and_or_chain` 新方法 + 前位调用 | and 头假边越过整个 or run 直达循环出口（与扁平形态假边目标结构性区分）+ or 成员真边=循环体入口 + 假出口同块身份 + walrus COPY+STORE 例外 + 非本循环条件块；全部块末 opcode/后继身份/循环体语义集合 | docstring [识别条件][归约方式][AST 映射][C1][C2][C3] 在位 | **PASS** |
| H6 | generator :9185-9195 | `_collect_await_protocol_chain` docstring [C2] 同步 | 与 H7 行为一致（先链头资格守卫，再逐环短路；poll 短路先于 `_resume_of_poll`） | ✓ | **PASS** |
| H7 | generator :9282-9283 | R7-O1 `if p is None: return None` 恢复 | 置于 `_is_setup` 之后、`_resume_of_poll(p)` 之前——p=None 不再触达指令流迭代 | ✓ | **PASS** |
| H8 | generator :34918-35039 | `_b45_rebuild_boolop_chain_slice` | 链切片逐成员操作数重建 + excluded_offsets=全链偏移集（结构身份非魔数）+ op 转折分段 | docstring 三要素+三 C 在位 | **PASS** |
| H9 | generator :35041-35120 + :35830-35832 | `_build_boolop_skipedge_grouped` + 前位钩子 | 恰一条链内 skip 边且极性 IF_TRUE（IF_FALSE 链内边=扁平 and→or 边界明确排除，neg_if_and 反例注释在位）+ si==0/sj≥2 + 均匀切片拒绝 + seg1 禁 and→or 转折；外层操作符=极性取反 | docstring 三要素+三 C 在位 | **PASS** |
| H10 | generator :36376-36418 | `_try_build_and_inner_or_pattern` while 条件上下文变体 | is_condition_context + 父 LoopRegion + 非末 or 成员 IF_TRUE=header / 末成员 IF_FALSE=merge | 注释 [C1][C2][C3] 在位 | **PASS** |
| H11 | generator :40171-40194 | B42 钩子（`_generate_ternary`） | 门 = merge_ctx ∈ (None,'return') + not value_target + merge_block 存在 + not func_call_info；置于 chained-container 尝试之前 | 钩子注释在位且与行为一致（含 n7_01 回退保证表述） | **PASS** |
| H12 | generator :41628 | `_up_targets` 三元加括号 | 纯语法等价变换，零行为变化 | — | **PASS** |
| H13 | generator :41641-41686 | 解包模式 trailing 语句发射 | 指令流语句终结符切分 + trivial `return None` 抑制（显式/隐式 return None 字节码同构，逐位等价）+ 镜像模式 1 既有 `_mt_trailing` 语义 | 注释在位 | **PASS** |
| H14 | generator :46863-46938 + :46939-47100 | `_B42_VALUE_CONSUMER_OPS` + `_b42_split_cond_prefix` + `_b42_rebuild_chain_value_stream` | 锚点=块内**首个**条件跳转（覆盖合并真臂续块 POP_JUMP 居中布局）+ 反扫栈效应表 + 前缀含 STORE 即 None + 段收集 `ternary_chain[1:]` 含最内层前缀 + 后向扩展 merge_block==entry（visited 防环）+ 全空段守卫 + 单链受限操作码 + 纯值校验 + 终栈恰单值 + 全链块归约标记（仅成功路径） | 两方法 docstring 三要素+三 C 在位 | **PASS** |

**红线四项核验**：零名字白名单（全部判据为 opname 族/后继身份/偏移集合归属）；零 start_offset 魔数（唯一位移量 342 恰在本批被清除）；零跨层回溯（全部判据局限于本层块指令/归属表/区域身份）；零新 self 跨方法状态（`_B42_VALUE_CONSUMER_OPS` 为类级常量 frozenset；成功路径 `generated_blocks` 登记属既有归约语义）。

**非阻塞观察（2 项，如实记录）**：
1. `_b42_rebuild_chain_value_stream` 直接操纵 `self.expr_reconstructor.stack` 并调用私有 `_process_instruction`——实测 `ExpressionReconstructor.reconstruct()`（ast_generator_v2.py:210）入口自带 `self.reset()`，外部栈残留不影响后续调用，安全。
2. `_b42_split_cond_prefix` 反扫栈效应表未列 `BINARY_SLICE`（按 0,0 处理，反扫方向偏保守、起点可能略前）；纯值校验白名单含 BINARY_SLICE，极端形态下前缀可能多收，但终栈恰单值硬校验兜底。不改判定。

## §2 判据面 vs FIX.md 声明核对

| FIX.md 声明 | 代码实测 | 判定 |
|---|---|---|
| 单链受限消费操作码 `{COMPARE_OP, IS_OP, CONTAINS_OP, BINARY_SUBSCR, BINARY_SLICE}` | `_b42_single` 分支 `_sn_ops & {…五操作码…}`（:46994-46999），逐一相符 | ✓ 相符 |
| BINARY_OP/CALL 不劫持 | 单链 SN 含 BINARY_OP/CALL → 受限集不含 → return None 回退既有 Pattern A/call 装配；r7_04 t_binop_both（多链 BINARY_OP）本批复跑保持 MATCH 实证 | ✓ 相符 |
| 全空段守卫保护 n7_01 纯裸三元 | `if all(not _seg for _seg in segments): return None`（:46989）；另核路径细节：单链裸三元即使全空守卫未触发，其 SN 仅含 LOAD_*（假臂加载），被单链受限操作码守卫二次拦截；多链裸三元 SN 仅含假臂 LOAD，终栈 >1 值被「终栈恰单值」拦截——三重守卫闭合，实测 n7_01 5/5、n7_02 5/5 | ✓ 相符（且保护路径不止守卫一条） |
| 段收集 [1:-1]→[1:]（含最内层 cond 前缀） | `for tr in ternary_chain[1:]`（:46954），段数 = len(elts)+1 注释与代码一致 | ✓ 相符 |
| 后向链扩展 merge_block==entry + visited 防环 | :46925-46937 逐条相符 | ✓ 相符 |
| 钩子放行 merge_ctx in (None,'return') | :40185 逐字相符 | ✓ 相符 |
| R7-O1 短路恢复 + docstring 同步 | H6/H7 相符 | ✓ 相符 |
| R7-O2 7 站点清除 | H1-H3 计数=7，grep=0 | ✓ 相符 |
| B42 残留 3 单元如实登记 | r7_rev1 逐文件失败名单= t_arg_multi_mixed / t_compare_lhs_only / t_listcomp_ternary_filter.<listcomp> 恰 3 单元 | ✓ 相符 |

## §3 读数复跑表（全部真实重跑）

| 项 | FIX.md 声明 | 复跑实测 | 逐位对照 | 判定 |
|---|---|---|---|---|
| r7 攻击面 batch（16 文件） | 104/128，负对照 n7_01/n7_02 各 5/5 | **104/128**（success 5 / failure 11） | 逐文件：r7_01 8/9、r7_02 **8/8 success**、r7_03 5/7、r7_04 6/7、r7_05 15/16、r7_06 7/10、r7_07 4/7、r7_08 4/8、r7_09 7/7、r7_10 7/8、r7_11 6/7、r7_12 5/8、r7_13 7/7、r7_14 5/9、n7_01 5/5、n7_02 5/5——与 FIX.md 及 r7_fix1.json 逐位一致 | ✓ |
| B42 封闭 6 单元 | dict_both/list_element/nested_container + t_subscript_index_ternary + t_compare_both_sides + t_unpack_ternary | 失败名单核读：上 6 单元全部退出失败名单；r7_02 整文件 8/8 | ✓ |
| B45 封闭 2 单元 | h_while_composite + b_nest_deep_mixed | 两单元退出失败名单（r7_14 4/9→5/9、r7_12 4/8→5/8 与基线对照吻合） | ✓ |
| B42 残留 3 单元 | 如实登记 | 恰 3 单元在失败名单 | ✓ |
| 未认领族 B46-B51/B43/B44/B47/B48 | 未越界修复 | 全部登记单元仍在失败名单（t_nest_left_assoc/in_condition/mixed_binop、await×3、augassign×2+t_host_while_body、t_host_for_else、t_host_try_sections、c_chain_and_combo、b_and_or_repeat/b_nest_three_layers/b_nest_deep_right、h_listcomp_filter_composite×2、h_if_ternary_chain_composite） | ✓ |
| round6 batch（16 文件） | 115/115，r6_04 11/11、r6_10 6/6 重点盯 | **115/115**（16 success），r6_04 **11/11**、r6_10 **6/6** | ✓ |
| rv6 探针 | 18/29 持平 | **18/29**；失败名单逐单元 = REVIEW.md §3 基线（aw_break/aw_continue、outer_raise_catch/nested_with_else_loop、try_fin_with_nested/double_fin_overwrite/try_fin_fin_body_with、gen_for_else_mixed、deep_tuple_star/star_mid_async/nested_star_tuple）零漂移 | ✓ |
| 哨兵① trade_info_utils | 36/41（失败 5 名单=基线） | **36/41**；失败 5 = trade_operation / kill_trade_process / get_trade_status / query_trade_strategy_info / query_strategy_id，与 round6 r6_sentinel_trade_info.json 基线名单逐一相同 | ✓ |
| 哨兵② scheduler | 52/52（重生成+single） | pycdc -o 重生成 → single = **52/52 success 100%** | ✓ |
| BOM（G0 红线） | efbbbf | `head -c 3 core/cfg/region_ast_generator.py | xxd` = `efbb bf` | ✓ |
| 插桩残留 | 0 | `grep -rn "_R23N20_DEBUG\|R23N21_DEBUG" core/` = **0** | ✓ |
| ast.parse + import | 通过 | 双 core 文件 ast.parse + import OK | ✓ |

## §4 变体攻击表（判据面 = B42 修复面；源码 py_compile 3.11 编译 → pycdc 反编译 → single 判定；pre-fix 对照 = c0ab03c1^ worktree 同 pyc 反编译）

探针已落盘：`test_repros/round7/rv7_01_quad_chain_container.{py,pyc,OK.py}` 等 4 套 12 文件。

| 探针 | 攻击形态 | 单元 | 本批复跑 | pre-fix 对照 | 判定 |
|---|---|---|---|---|---|
| rv7_01_quad_chain_container | 四元链式三元容器（list/dict/tuple 各 3-4 个三元臂 + 尾常量元素） | 4 | **4/4 MATCH** | 3/3 函数单元全败（list/tuple 第 4 元素蒸发、dict 键值错位） | **补强实证**：B42 多链分段重建超出被探 2-3 元形态仍成立 |
| rv7_02_compare_chain_ternary | 比较链内三元：`(aT)<(xT)<c`、`(aT)<=(xT)<(mT)`、`(aT)<abs(xT)` | 4 | **2/4**（chain_lhs_ternary_rhs_call MATCH） | chain_two_ternary / chain_three_ternary 与 pre-fix **逐位同败**（链塌缩为裸三元+if）；chain_lhs_ternary_rhs_call pre-fix 败（return+比较蒸发）→ 本批 MATCH | 2 败 = 既有缺口变体（见 B52）；1 单元补强（单链 COMPARE_OP 受限接管对 call 比较位形态生效） |
| rv7_03_subscript_slice_ternary | 下标切片双三元 `xs[t1:t2]` + 嵌套下标 `xs[t1][ys[t1]]` + 单侧切片 | 4 | **4/4 MATCH** | sub_then_sub pre-fix 败（外层 xs 容器蒸发）；slice 双三元 pre-fix 已绿 | **补强实证**（1 单元 fail→MATCH），零回归 |
| rv7_04_dict3_ternary | dict 三键双三元（纯值）+ 三键混合（list 值三元 + 下标三元 + 常量） | 3 | **2/3**（dict3_two_ternary MATCH） | dict3_two_ternary pre-fix 败（整 dict 塌缩为裸三元）→ 本批 MATCH；dict3_nested_value 与 pre-fix **逐位同败** | 1 败 = 既有缺口变体（见 B53）；1 单元补强 |
| **合计** | 4 探针 | **15** | **12/15** | 4 单元 fail→MATCH，3 单元 pre/post 逐位同败，**0 回归** | |

## §5 新破口登记（续接 B51；变体实证，均 pre-fix 同败＝既有缺口非本批引入）

### B52 — 链式比较操作数含三元（比较链 ∧ 三元链交界塌缩）（P1）
- **锚点**：`_identify_chained_compare_regions` / `_build_chained_compare_region` 与 `_identify_ternary_regions` 的区域抢占边界 + `_generate_ternary` B42 钩子消费形态覆盖面（单链受限操作码仅认 {COMPARE_OP,IS_OP,CONTAINS_OP,BINARY_SUBSCR,BINARY_SLICE} 单条比较；多链分段重建未覆盖 ChainedCompare 消费段的链式比较节点重装配）。
- **机制**：`(aT) < (xT) < c` 的链式比较区域与两条三元链交界处装配失败——链塌缩为裸三元 + `if (xT): pass`（比较节点与尾操作数 c 全蒸发）；三链形态退化为三个裸三元 + `return c3`。
- **最小复现**：`rv7_02 chain_two_ternary`、`rv7_02 chain_three_ternary`。共 2 单元。
- **回归哨兵**：r7_09 7/7、r7_10 7/8（不含本形态）、rv7_02 chain_lhs_ternary_rhs_call。

### B53 — dict 多键混合容器值三元塌缩（P2）
- **锚点**：`_extract_dict_prefix_values` / chained-container 装配与 `_b42_rebuild_chain_value_stream` 的链连续性判据（merge→entry 单链衔接）——多键值分属独立三元链（非一条链）时既有多链重建与 chained-container 路径都不接管。
- **机制**：`{'a': [v1 if c1 else v2], 'b': xs[0] if flag else xs[-1], 'c': 3}` 三键值各含独立三元（list 包裹值 + 下标值 + 常量混合），输出塌缩为裸 `v1 if c1 else v2`。
- **最小复现**：`rv7_04 dict3_nested_value`。共 1 单元。
- **回归哨兵**：r7_02 8/8、rv7_04 dict3_two_ternary（三键纯值双三元本批转绿）。

## §6 越界与产物一致性检查

| 项 | 判定 | 实测 |
|---|---|---|
| commit 改动面 | **通过** | `git show c0ab03c1 --stat` = 2 core + FIX.md + 4 json（r7_fix1/r7_fix1_probe/r6_guard1/rv6_guard1）+ 6 个 r7 OK 产物；无 scripts/parsers/pycdc.py/spec 触碰 |
| B46–B51 未越界修复 | **通过** | §3 失败名单核读：全部登记单元仍 MISMATCH，无一被"顺手"修复 |
| OK 产物零手改 | **通过** | 6 个被改 OK 文件逐一与当前核 `pycdc.py -o` 新生成输出 **byte-identical**（r7_01/02/03/04/12/14 六文件 diff 全空） |
| 复核期间外来变更 | 记录 | `a1c55316`（主代理验证归档）仅 VERIFICATION.md + 分片 json + tasks.md；`git diff c0ab03c1 -- core/ parsers/ scripts/ pycdc.py` = 空 |
| 命令时长 | 通过 | 全部 ≤300 s（batch 最大 5.4 s；402 重生成不在本复核范围，未重跑） |

## §7 复核结论

修复批次一四项声明（R7-O1 / R7-O2 / B45 2/2 / B42 6/9）在逐 hunk 合规、判据面如实性、读数复跑、变体对抗四个维度全部经受住复核：**封闭声明成立、残留如实、零回归、零越界、零手改**。变体攻击净改善 4 单元（fail→MATCH），同时暴露 2 个既有缺口变体形态（B52/B53，共 3 单元，pre-fix 逐位同败）如实登记交后续批次。

**终判：放行。** 附带交接：B52（P1）/B53（P2）续接 B46-B48/B43/B44/B47/B48 + B42 残留 3 单元，进入批次二工作清单。
