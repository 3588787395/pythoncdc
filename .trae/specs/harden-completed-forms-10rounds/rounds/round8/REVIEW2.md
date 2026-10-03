# Round 8 复核报告（评审工程师 · 复核批次 / REVIEW2）

- 复核人：评审工程师（Round 8 任务 8.3 复核批次，独立复验，零容忍）
- 日期：2026-10-04
- 复核对象：commit `5aff0e32`（Round 8 修复批次：B54 封闭 4/4 + B55 封闭 2/2（分支 A/B/B55-c），含前位遗留改动并入）
- 树状态：复核起点 HEAD = `5aff0e32`；复核期间工作树唯一新增 = 本报告 + rv8_01..03 探针产物（`test_repros/round8/`），core 零触碰
- 唯一判据：`scripts/pyc_verify.py`（pylingual compare_pyc，Python 3.11.7）；复核期间临时 json（r8_rev1 / r6_rev1 / r7rev_residual / r7rev_rv67）已用后删除；未修改 core/、parsers/、scripts/、pycdc.py、既有 REVIEW/FIX/VERIFICATION；未手改任何既有 OK.py（schedulerOK 重生成验证逐字节零漂移）；全部命令 ≤300 s
- pre-fix 对照：`git worktree add` 于 `5aff0e32^`（= `0c0642ab`）独立工作树实测，用后已移除

## 终判：**放行**

逐 hunk 合规（10/10 PASS，判据面全部为同层结构事实，红线四项全净）、FIX.md 判据面声明与代码逐条相符（含 B55-c 窄门控四条件缺一不可的合取实现核对）、全部读数逐位复跑相符（r8 107/118 逐文件逐失败单元与提交 json 零差异、round6 115/115、残留 81/117、rv6+rv7 30/44、哨兵抽 2 全相符、BOM/插桩 0）、变体攻击 3 探针 20 单元 17 MATCH（+7 单元由 pre-fix 败转 MATCH = 补强实证，0 回归，3 MISMATCH 单元经 pre-fix worktree 证实逐位同败 = 既有缺口变体，续接登记 B63/B64/B65 候选）。

---

## §1 逐 hunk 合规判定表（`git show 5aff0e32 -- core/`，10 hunks，仅 core 1 文件）

判据红线：零名字白名单 / 零 start_offset 魔数 / 零跨层回溯 / 零新 self 跨方法状态；判据必须为同层结构事实（操作码族与栈效应、前驱后继集合、跳转边身份、区域归属、区域字段）。

| # | 位置（现行文件行） | 内容 | 判据面（实测核读） | docstring 三要素 / C 条款 | 判定 |
|---|---|---|---|---|---|
| H1 | generator :1778-1791 | [B55] 分支 A：generate() 清理预标记循环豁免钩子 | 调用 `_b55_is_try_handler_exit_trailing_return`，命中则 `continue` 跳过预标记（严格附加分支，其余形状行为逐字保持）；块交由其归属 BASIC 区域按顶层偏移序发射，非丢弃 | 钩子注释识别条件/机制/归约/AST 映射在位 | **PASS** |
| H2 | generator :2899-2923 | [B54] `_B54_CHAIN_STORE_OPS` / `_B54_LOADISH_OPS` / `_B54_STMT_TERMINATOR_OPS` | 纯操作码族类级常量（先例 = `_B42_VALUE_CONSUMER_OPS`），零名字/偏移；终结名单覆盖 POP_TOP/STORE_*/DELETE_*/IMPORT/RAISE/RETURN/YIELD 全语句收尾族 | 族注释在位 | **PASS** |
| H3 | generator :2925-2981 | [B54] `_b54_validate_chain_target_window` + `_b54_target_ast` | store 消费栈值数 ↔ 窗口栈值组数（Name=0 组 / STORE_ATTR=1 / STORE_SUBSCR=2），分组复用 `_w16_split_value_groups`（不复制判定）；目标 AST 直转与 W16 路径一致；失败一律 return None 回退 | 两方法 docstring 三要素在位 | **PASS** |
| H4 | generator :2983-3045 | [B54] `_b54_scan_chain_continuation` | CPython 3.11 链式赋值布局（非末目标 COPY 1 前导 / 末目标直接消费收尾）+ 末目标必须 store 收尾（耗尽即拒绝）+ 与 walrus 按「后续 STORE 段存在性」互斥 + 校验不过即 `(None, start)` 全量回退；窗口内 LOADISH 码族连续段 | docstring 三要素 + 调用约定在位 | **PASS** |
| H5 | generator :3047-3104 | [B55] `_b55_is_try_handler_exit_trailing_return` + `_b55_is_pure_const_return_block` | 前者四条件合取：纯 None-return 块 + 前驱恰一（与 R57-B 共享收尾豁免互斥）+ 前驱含 POP_EXCEPT 且末条 JUMP_FORWARD 精确指向本块 + 前驱归 TryExceptRegion；后者剥噪后 ≤2 指令（末条 RETURN_*，前至多 LOAD_CONST）——纯形状判定，异常机器块结构性不可满足 | 两方法 docstring 三要素在位 | **PASS** |
| H6 | generator :3106-3160 | [B54] `_b54_build_chain_assign_from_accumulation` | accum 反扫装载窗 + 窗左邻必须 COPY 1 + 值段非空且不含语句终结指令（兄弟语句污染兜底）+ 首目标窗口校验 + 全部目标构建失败即 None 回退；单一 Assign（is_chain_assign=True）链值透传 | docstring 三要素在位 | **PASS** |
| H7 | generator :11042-11074 | [B54] 自循环体门控钩子 | 置于 STORE_SUBSCR/STORE_ATTR 独立提取分支内；扫描上限 `min(len, _body_end_idx+1)` 与主循环语句边界一致；命中→整链 Assign + 延续偏移入既有 `_sl_skip_offsets` 防重复消费；未命中→逐字回退原 STORE_SUBSCR/STORE_ATTR 两路径 | 钩子注释在位且与行为一致 | **PASS** |
| H8 | generator :28496-28564 | [B55-c] post-try 窄门控收集 | 位置 = 常规收集之后、finally_copy 收集之前；门 = `not _post_try_blocks_r19n2` ∧ `region.has_finally`；候选 = try_blocks 后继 ∧ ∈ region.blocks ∧ `start_offset ≥ region.try_offset_end`（跨度外）∧ 非已知结构偏移（try/else/finally/cleanup/handler_entry/except_handlers/finally_copy keys）∧ 非 if-merge ∧ 无 RERAISE ∧ 纯常量 return ∧ 归属本 region（或无）∧ 未生成；break/continue 角色 try 块跳过；finally_copy 按 `.keys()`（前位 TypeError 迭代错误已按 FIX.md §2 诚实记录修正） | 四条件注释块逐条在位，与代码合取式逐条对应 | **PASS** |
| H9 | generator :44462-44490 | [B54] merge 路径延续扫描 | `_try_build_ternary_store_assign` 内、`_after_store_instrs` 切出后扫描；命中→延续指令从 extra statements 剥离 + targets 暂存；未命中→`_after_store_instrs` 逐字不变 | 钩子注释在位 | **PASS** |
| H10 | generator :44763-44772 + :44872-44881 | [B54] Pattern A 两返回点折入 | STORE_SUBSCR 与 STORE_ATTR 两 Pattern A 返回点：`if _b54_chain_targets:` 才改道（targets 折入 + is_chain_assign=True），无延续时与旧行为逐字一致 | 注释在位 | **PASS** |
| H11 | generator :50264-50290 | [B54] 纯 Name 链路径 return 值后缀切分 | `_rv_start` 自 RETURN 反扫至首个语句终结指令（最大后缀 = return 值表达式，不可能含语句边界）；`_pre_ret = [:_rv_start]` 交兄弟语句重建、`_rv_instrs = [_rv_start:_ret_cut]` 交 Return 值——替换旧「整段既发兄弟又拼值」双路径幻影源 | 判据注释在位（纯操作码栈效应） | **PASS** |
| H12 | generator :50518-50548 | [B54] 混合链路径 return 值后缀切分 | 同一判据于 `_body_m`；`_pre_body_m` 剥噪 + `_has_inner_jump_m` 域改为兄弟段（值后缀不含跳转参与守卫）；`_rv_instrs_m = _body_m[_rv_start_m:]`——替换旧 `_remaining_m[_cut_m+1:]`（RETURN 之后恒空 ⇒ 返回值恒丢为 None + 值段泄漏裸 Expr） | 判据注释在位 | **PASS** |
| H13 | generator :52942-52963 | [B55] 分支 B：return_succ 裸 return 登记 | elif 门 = 归属区域 entry 不是该块 ∧ 前驱恰一（排除自环）∧ 当前块在其前驱集合 ∧ 块剥噪后恰 1 条且为 RETURN_VALUE/RETURN_CONST（裸 return，值由当前块留栈消费）；命中仅 `generated_blocks.add`（防幻影重发射），未命中路径逐字不变 | 判据注释在位（块末操作码 + 前驱集合 + 区域入口身份） | **PASS** |

**红线四项核验**（全 commit `git show 5aff0e32 -- core/` 增行实测）：
- 零名字白名单：新增判据全为 opname 族 / 前驱后继身份 / 区域字段归属，无函数名/文件名字面量（grep 增行 `r8_|tools|scheduler|IQCommon|IQEngine|trade_info|option_account` = 0）；
- 零 start_offset 魔数：无 `== <3位以上字面量>` 比较；`block.start_offset` / `region.try_offset_end` 仅作边身份与跨度归属比较，非阈值；
- 零跨层回溯：全部判据取自本层块指令、前驱/后继集合、`block_to_region` 权威归属表与所在 region 自身字段（try_blocks/else_blocks/finally_blocks/cleanup_blocks/handler_entry_blocks/except_handlers/finally_copy_blocks）——与 spec「区域成员关系」白名单一致；
- 零新 self 跨方法状态：新增增行 `self._x =` 赋值 = **0**（`_B54_*` 为类级常量元组；`generated_blocks`/`generated_offsets`/`_sl_skip_offsets` 均为既有登记语义）。

**非阻塞观察（3 项，如实记录）**：
1. **[C1]/[C2]/[C3] 字面标签缺失（形式偏差）**：本 commit 增行 `[C1]|[C2]|[C3]` 字面标签 = **0**（Round 7 先例对新方法逐字标签）。实质条款以同义散文在位于每处注释/docstring（「同层结构事实——零名字/偏移白名单，零跨层回溯」「每块唯一归属不变」「整体归约禁止逐段消费」）且经行为核验一致，不构成「注释与代码不一致」；记为非阻塞形式偏差，建议下批补齐标签。
2. `_b54_scan_chain_continuation` 对「延续窗口后为独立赋值语句」的误收路径经构造排查结构性不可达：独立语句的装载窗必含其自身值装载（组数超 store 消费数 → 校验拒绝），或含条件跳转（LOADISH 族不含 JUMP → 窗口截断拒绝）；rv8_01 负对照 `single_assign_negctrl` 与 r8_03/r8_05 全 MATCH 面复跑实证。
3. FIX.md §3② 括注「（success 7 / failure 6）」与两份 json（提交的 r8_fix1.json 与复跑）均为 **success 8 / failure 5** 相悖——单元数 107/118 正确，属报告笔误（见 §3）。

## §2 判据面 vs FIX.md 声明核对

| FIX.md 声明 | 代码实测 | 判定 |
|---|---|---|
| B55-c 四条件「保护跨度外/无结构角色/纯常量 return/归属本 region」缺一不可 | H8 合取式逐条对应：`start_offset >= try_offset_end`（跨度外）；`not in _b55c_known_offs`（try/else/finally/cleanup/handler_entry/except_handlers/finally_copy keys 七类）+ `not in _all_if_merge_blocks_r19n2`（无结构角色）；`_b55_is_pure_const_return_block` ∧ 无 RERAISE（纯常量 return）；`block_to_region` owner 为 None 或本 region（归属本 region）——四条件同一 `if` 合取，删除任一即不触发 | ✓ 相符（缺一不可） |
| B55-c 门控「has_finally 且常规收集为空时」「try_blocks 后继路径之后、finally_copy 路径之前」 | `if not _post_try_blocks_r19n2 and getattr(region, 'has_finally', False)`（:28525）；位置在常规 post-try 收集循环之后（:28470-28495）、finally_copy 收集（:28579）之前 | ✓ 相符 |
| `finally_copy_blocks` 为 `{offset: int}`，keys 即副本块起始偏移 | :28541-28542 按 `.keys()` 收集，与既有 dtc-r08 消费端（:28587 `set(region.finally_copy_blocks.keys())`）同构 | ✓ 相符（前位 TypeError 迭代错误已修正并诚实记录） |
| B54 链识别「非末目标 COPY 1 前导 / 末目标直接消费」「与 walrus 按后续 STORE 段存在性互斥」 | `_b54_scan_chain_continuation` :3013-3045 逐条相符；末目标必须 store 收尾（:3044-3045 耗尽拒绝），walrus 形态无后续 store 段 → 扫描拒绝 → walrus 路径不受扰 | ✓ 相符 |
| B54「链值流完整透传至每一目标」 | `_b54_build_chain_assign_from_accumulation` 单一 Assign `is_chain_assign=True` + targets=[首目标]+cont_targets（:3136-3157）；merge 路径 Pattern A 两返回点 `[target] + _b54_chain_targets` 同值透传 | ✓ 相符 |
| B54「return 值后缀切分：后缀不含语句终结指令 → 不可能含语句边界」 | H11/H12 反扫判据逐字相符；终结名单 `_B54_STMT_TERMINATOR_OPS` 覆盖全部语句收尾族 | ✓ 相符 |
| B55 分支 A「单前驱 + POP_EXCEPT + JUMP_FORWARD 边身份 + TryExceptRegion 归属」 | `_b55_is_try_handler_exit_trailing_return` :3066-3083 四条件合取，与 (2)「与 R57-B 共享收尾豁免互斥（前驱 ≥2 vs 恰 1）」互补 | ✓ 相符 |
| B55 分支 B「裸 return 块 + 非区域入口 + 前驱唯一 + 当前块在前驱」 | :52942-52963 elif 合取 + 剥噪恰 1 条 RETURN_* 附加守卫，与 FIX.md §1 分支 B 描述逐条相符 | ✓ 相符 |
| 迭代记录：初版误迭代 `finally_copy_blocks.values()` → TypeError 5 单元劣化 → 改 `.keys()` + 跨度门控全恢复 | 提交代码无 `.values()` 迭代；§3 复跑 5 个 try 面单元（r8_01 11/11、r8_02 10/10、r8_11 5/6、r8_08 9/9、r8_03 9/9）全恢复 | ✓ 相符 |

## §3 读数复跑表（全部真实重跑，命令 ≤300 s）

| 项 | FIX.md 声明 | 复跑实测 | 逐位对照 | 判定 |
|---|---|---|---|---|
| r8 全量 batch（13 文件 118 单元） | 107/118；B54×4+B55×2 转 MATCH；B48×2/B46×1 逐位持平；n8_01 4/4、n8_02 5/5 | **107/118**（files_by_status success 8 / failure 5） | 13/13 文件 units 与失败单元名单与提交 `r8_fix1.json` **零差异**；转 MATCH = r8_pass_except、r8_pass_try_finally、r8_assign_chain、r8_assign_chain_subscript、r8_dh_while_assign_chain、r8_x_assign_ternary_chain（恰 6 单元，对 0c0642ab 面 +6）；残留 11 MISMATCH = B56×2+B57+B58+B59+B60+B61+B62+B48×2+B46×1 与 §5 名单逐一对应；B48（r8_aug_chain_rhs/r8_x_augassign_ternary）+ B46（r8_x_ret_nested_ternary）失败签名 pre/post 逐字节同 | ✓ |
| Round 7 残留 17 文件 | 81/117 持平 | **81/117** | 17/17 文件 units + 失败名单与提交 `r8_residual.json` 零差异（r7_01 8/9 … rv7_04 2/3 全逐位） | ✓ |
| round6 全量 16 文件（r6_*+n6_*） | 115/115 | **115/115**（16/16 success） | 与提交 `r8_round6_recheck.json` 相符 | ✓ |
| rv6+rv7 变体面 11 文件 | 30/44 持平（任务书 20/33 笔误如实勘误） | **30/44** | 11/11 文件与提交 `r8_rv67_check.json` 零差异 | ✓ |
| 哨兵抽 2：trade_info_utils | 36/41，失败 5 名单 = trade_operation/kill_trade_process/get_trade_status/query_trade_strategy_info/query_strategy_id | **36/41**，失败 5 名单逐字一致 | = 基线 | ✓ |
| 哨兵抽 2：scheduler（重生成 + single） | 52/52 | `pycdc.py -o` 重生成后与提交版**逐字节零漂移**；single **52/52** | = 基线 | ✓ |
| BOM `head -c 3 \| xxd` | efbbbf | `00000000: efbb bf` | ✓ | ✓ |
| 插桩 grep `_R23N20_DEBUG\|R23N21_DEBUG\|_patch_dbg\|_probe_r` core/ | 0 | **0** | ✓ | ✓ |
| `git status` 工作树盘点 | 无未提交在途变更 | 干净（复核新增仅本报告 + rv8 探针产物） | ✓ | ✓ |

**FIX.md 笔误勘误（如实记录）**：§3② 括注「success 7 / failure 6」有误，两份 json 均为 **success 8 / failure 5**（13 文件）；单元级 107/118 与逐文件读数不受影响。§3⑤ 任务书「20/33」勘误为 30/44 与实测相符。

## §4 变体攻击表（rv8_01..03，py_compile 3.11 编译 → pycdc → single，pre-fix worktree 归因）

| 探针 | 攻击面 | 单元 | post-fix | pre-fix | 判定 |
|---|---|---|---|---|---|
| rv8_01_chain3_subscript | B54 判据边界：三目标链 × 下标 RHS（`a=b=c=xs[i]+xs[j]`）/ 全下标三链 / Name+Attr+Subscript 混合目标链 / 链后 return 表达式 / 链值含 BoolOp / 单赋值负对照 | 7 | **6/7** | 2/7 | 4 单元败转 MATCH（chain3_subscript_rhs / chain3_all_subscript / chain_mixed_targets / chain_then_return_expr）= 补强实证；chain_value_boolop pre/post 逐位同败（§5-B65）；`single_assign_negctrl` 两态 MATCH |
| rv8_02_with_tryfin_constret | B55-c 判据边界：空 try/finally 尾随**非 None 常量** return（'done' / -42）/ 尾随语句段 / with 体空 try/finally / 非空 finally 段 / while 内链式下标赋值 | 7 | **5/7** | 2/7 | 3 单元败转 MATCH（tryfin_return_str / tryfin_return_negative / while_chain_subscript）= `_b55_is_pure_const_return_block`「任意常量值」与 B54 自循环路径补强实证；tryfin_then_more / with_body_tryfin_chain pre/post 逐位同败（§5-B63/B64）；try_except_fin_nonempty 两态 MATCH（非空 finally 不误收） |
| rv8_03_except_return_trailing | B55 分支 A/B 判据边界：except 段内显式 `return None` + 尾随语句 / except pass + 尾随隐式 None / 双 handler 共享收尾（单前驱互斥负对照）/ try 体 return + except return / handler return 值 + 另一 handler return None | 6 | **6/6** | 6/6 | 全 MATCH 两态持平：豁免判据不误伤共享收尾块（two_handlers_shared_tail）与非 try 形态，B45/B50 已封闭面零回归 |
| **合计** | 3 探针 | **20** | **17/20** | **10/20** | +7 补强 / 0 回归 / 3 既有缺口变体（pre-fix worktree `5aff0e32^` 逐位同败实证，失败签名 pre/post 逐字同） |

## §5 新破口登记（候选，交后续批次；全部经 pre-fix worktree 证实为既有缺口，非 `5aff0e32` 引入）

### B63（候选）— 空 try/finally 后非纯常量尾随语句段蒸发（B55-c 窄门控设计边界外形态）（P2）
- **最小复现**：`rv8_02 tryfin_then_more`：`try: pass / finally: pass / y = x + 1 / return y` → 尾随两整句蒸发，函数体退化为空 try/finally。
- **机制**：尾随块为多语句块（STORE y + RETURN y），不满足 `_b55_is_pure_const_return_block`（纯常量 return）→ B55-c 门控按设计拒绝 → 仍被 `_generate_try` 收尾毯式标记吞掉。B55-c 判据「纯常量 return」是既有窄门控的边界条件，本形态在其外。
- **归因**：pre-fix（0c0642ab）同签名 "Different bytecode" 逐位同败。

### B64（候选）— with 体空 try/finally 尾随 return：嵌套重排 + return 蒸发（B55 × with 宿主交叉）（P2）
- **最小复现**：`rv8_02 with_body_tryfin_chain`：`with open(p) as fh: try: pass / finally: pass` + `return fh` → 产物 `try: with …: pass / finally: pass` 且 `return fh` 蒸发（with/try 嵌套倒置 + 尾随 return 丢失）。
- **机制**：with 宿主内空 try/finally 的块归属与 `_generate_with`/`_generate_try` 装配竞争，尾随 return 块两装配面均未消费。
- **归因**：pre-fix 同签名 "Different control flow" 逐位同败。

### B65（候选）— 链式赋值 × 嵌套 BoolOp 值：链目标丢失 + BoolOp 嵌套压平（B54 值重建面既有缺口变体）（P2）
- **最小复现**：`rv8_01 chain_value_boolop`：`a = b = c = (x or y) and (x and y)` → 产物 `a = (x or y) and x and y`（targets 3→1，b/c 目标丢失；内层 `And[x,y]` 被压平为顶层第三操作数——源码 AST 为 `And[Or[x,y], And[x,y]]`，产物为 `And[Or[x,y], x, y]`，非解析器等价）。
- **机制**：链值含 BoolOp 时链重建路径未接管（回退单目标）+ BoolOp 重建同算子嵌套压平（B1 族签名）。注意：pre/post 产物逐字节相同——B54 新机制未触达该路径（未引入、未修复）。
- **归因**：pre-fix 同签名 "Different bytecode" 逐位同败。

**登记纪律说明**：以上 3 候选单元均不在 Round 8 交接单认领面（B54 4 单元 / B55 2 单元）之内，pre-fix 逐位同败证明为既有缺口的结构变体新暴露；零回归成立（post-fix 20 单元无一由 MATCH 转 MISMATCH）。

## §6 越界检查

| 项 | 判定 | 实测 |
|---|---|---|
| commit 改动面 | **通过** | `git show 5aff0e32 --name-only` = core 1 文件（region_ast_generator.py）+ `.trae/.../round8/` 报告与 json 5 份 + OK 再生成 8 份（toolsOK −1 / schedulerOK −2 / r6_11OK −1 = 幻影 `return None` 清除；r8_03/r8_05/r8_08/r8_09/r8_10 = B54/B55 修复产物重生成），无其他文件触碰 |
| B56–B62 未越界修复 | **通过** | 11 残留 MISMATCH 单元名单与 REVIEW.md §5 登记逐一对应，全部仍 MISMATCH；r8_06/r8_07/r8_11 失败签名 pre/post 逐字节同 |
| B48×2/B46×1 对照面 | **通过** | 失败单元与失败签名 pre/post 完全一致（§3） |
| 既有 OK.py 零手改 | **通过** | schedulerOK 重生成逐字节零漂移实证；toolsOK/r6_11/r8_* 内容 diff 均为 pycdc 再生成语义（幻影 return 清除 / 链重建 / return 恢复），无语法美容或手写痕迹 |
| 临时产物清理 | **通过** | 复核临时 json（r8_rev1/r6_rev1/r7rev_residual/r7rev_rv67）已删除；pre-fix worktree 已移除；rv8_01..03 源码+pyc+OK 保留于 `test_repros/round8/` |

---

## 附：复核过程产物清单

- `test_repros/round8/rv8_01_chain3_subscript.{py,pyc,OK.py}`、`rv8_02_with_tryfin_constret.{py,pyc,OK.py}`、`rv8_03_except_return_trailing.{py,pyc,OK.py}`（3 变体探针，保留）
- 本报告 `.trae/specs/harden-completed-forms-10rounds/rounds/round8/REVIEW2.md`
- 复核期间零修改 core/、parsers/、scripts/、pycdc.py、既有 REVIEW/FIX/VERIFICATION/OK.py
