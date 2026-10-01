# Round 3 评审（对抗性审查：For/While/loop-else/Break/Continue 族）

- 评审人：评审工程师（Round 3）
- 日期：2026-10-01
- 唯一判据：`scripts/pyc_verify.py`（附件 pylingual `compare_pyc`，sha256 见命令输出）；验证方式 = `pycdc.py -o <x>OK.py <x>.pyc` → `pyc_verify.py single <x>.pyc [--source <x>OK.py]`；登记项复验一律 `--source` 法（新产物落 `test_repros/round3/_r3_*OK.py`，归档产物不动）。
- 硬约束遵守：未修改任何 `core/`、`scripts/`、`site-packages/` 文件；每条 shell 命令 ≤300 s；`*OK.py` 全部由 `pycdc.py` 生成。
- 命名注记：`test_repros/round3/` 内 r3_01..13 为 2026-09-19 quote.pyc 战役历史遗留（ANALYSIS.md 在案），本轮新探针以 **r3_20+ / n3_01+** 编号避让，历史产物零改动。
- 首分歧定位工具：`test_repros/round3/_r3_firstdiff.py`（marshal+dis 对原 pyc 与 OK.py 重编译码对象逐指令对照；`pycdas.py` 仅反汇编模块顶层，嵌套 code object 首分歧以 dis 对照为准，所引 offset 均为原 pyc 偏移）。

---

## §1 任务A — 算法合规审计结论表（零容忍口径）

理论权威：`wiki/concepts/decompile-invariant-completeness.md` §1（C1/C2/C3）、§5 表A、§6 破口登记。

| # | 审计项 | 锚点（2026-10-01 实测） | 结论 | 依据 |
|---|---|---|---|---|
| A1 | `_find_loop_else` + clamp（else 块被区域外引用时守卫封闭性） | `_find_loop_else` `region_analyzer.py:5252`；FOR break 证据链 `:5310-5372`（`_break_hits_for_iter_exit` 置真 `:5332-5333/:5344`，命中即 `return None, natural_exit` `:5371-5372`）；break_targets 后必经路径 `:5373-5469`；无 break 路径 R09 兄弟头守卫 `:5493` + NOP 判别器 `_loop_else_nop_marker:5160`（调用 `:5506-5508`）；clamp `_clamp_loop_else_to_enclosing_try:5115-5158`（**唯一调用点 :5465，仅 FOR 分支+break_targets 路径**；WHILE 分支 R4-08 BFS 仅有同入口守卫 `_08_foreign_owned` `:5647-5686`，自然出口路径 `:5732-5955` 无 clamp） | **打回** | FOR 分支 break 证据链在「break 落点与 else 出口汇聚同一续流块」形态下判据失效（`:5332-5333` 落在 for_iter_exit 即整体放弃 else；`:5374-5388` 后必经推进把真 else 块让渡给外层循环体认领）→ else 体降级为顺序语句（无条件执行=语义错误）或整体丢失。实测 §2 R3-A 族 8 单元 + R3-B 族 4 单元；且深嵌套（r3_24/r3_25）与浅层（n3_02 同形 MATCH）结果分叉 = 嵌套无感破缺（C3）。clamp 面本身（try 边界裁剪）本轮实测未暴露缺口，登记观察点 R3-O2（WHILE 分支无 clamp 为潜在缺口，未实证） |
| A2 | `_block_is_continue_target` / `_loop_else_set`（continue 目标跨区域） | `_block_is_continue_target` `region_ast_generator.py:10403-10414`；`_loop_else_set` 排除 `:10537-10541`；纯 continue 判别 `_block_is_pure_continue:10456-10472`；回边汇合抑制 `_is_loop_tail_convergence_block:10416-10454` | **有条件通过** | B2 语料实测全 MATCH（§2 r3_23 5/5、n3_02 5/5）；`_loop_else_set` 对「then/else 后继为当前循环 else 块」的排除守卫封闭。静态盲点：`:10407-10410` 以 `target.loop_header` 判真，**不校验目标是当前循环还是外层循环**（外层回边块同判 True），且 `_loop_else_set` 只排当前循环 else 块——跨循环 continue 身份守卫缺失（C3 显式守卫缺失），本轮语料未实证触发，登记观察点 R3-O1 |
| A3 | B2（If×continue）守卫族 | `region_ast_generator.py:10455-10579`（`_loop_handle_no_exit_successors` 对称分支 `:10551-10568`、取反分支 `:10569-10590`） | **通过** | r3_23 四形态（then 纯 continue / then=continue+else 体 / if×break+if×continue 混排 / continue 在 for-else 前后件）5/5 MATCH，零回退 |
| A4 | `_detect_while_condition_boolop_chain` 混合链双向续接（for/while-else 语料） | `region_analyzer.py:24239`（分发）；后向回溯 `:24266-24502`（R3-L 体语义集合 `:24363-24374`）；[B6-while 双向续接] `:24504-24600`（四判据：链尾 IF_TRUE→header `:24539-24545`、链首 IF_FALSE `:24546-24549`、or 尾成员续接 `:24576-24594`、边界闭合 `:24595`）；均匀链 all_same_target 收尾校验 `:24611-24623` | **打回** | 判据形态覆盖面窄于宣称：(1) 双向续接要求链尾为 IF_TRUE 族跳 header——`while (a or b) and c:` 的 condition_block 是 and 尾（IF_FALSE→出口），签名不匹配 → r3_28.while_or_and 条件错+幻影 continue；(2) 非名操作数（比较 `k < m`）混合链 → r3_28.while_and_or / while_chain3 / for_body_while_mixed 循环整体消失（首分歧 @0，35 指令→2）；**浅层即败**，不满足 B7「深层才错」签名——B6/B7 宣称的混合链封闭仅对 `A and B or C` 单名操作数形态成立（r1_10 基准的隐含前提）。C1/C2 装配降级，实测 §2 R3-C 族 |
| A5 | `_loop_generate_while` if-break 三分在嵌套循环 | 三分 `region_ast_generator.py:6558-6582`：orelse=无语句 elif 链→剥离（`:6570-6575`）；**orelse 含真实语句→维持丢弃**（`_b6_s = None` `:6576-6581`，自承 r2_14 登记面）；干净 if-break→保留（`:6582-6584`）；while-else 发射 break 门 `:6596-6626` | **打回** | 嵌套/try 语料下 else 侧物化抑制失效：r3_24.double_loop_outer_break（else 内 `if i==3: break` → 无条件 `else: break` + `if i==3: pass` 物化改写）；r3_27.loop_try_with_break（try/finally 内**双 break** 发射 + 尾 `return` 丢失）；r3_20.inner_break_out（break→幻影 `return k` + 循环体后件丢失）。三分第二分支的历史丢弃面在嵌套上下文扩大为结构改写（C2/C3），实测 §2 R3-B 族 |

**A1/A4/A5 判定细节补充（审计正向发现）**：
- 无 break 证据的 loop-else 降级为顺序语句是**字节等价**的（r3_27.loop_try_continue、r3_27.loop_with_match 无 break 语料 demotion 后 8/9 单元 MATCH）——判据对「无 break 时 else 与顺序代码不可区分」的处理正确；**只有 break 证据存在时** else 判定失效才产生字节分歧（A1 打回范围由此精确界定）。
- 空 else（r3_21 5/5）、元组解包/starred/async for-else（r3_30 5/5）、推导式×loop-else 交错（r3_32 11/11）、while-else 内嵌套 while（r3_26.nested_while_in_while_else）全部 MATCH——这些子面守卫封闭成立。

---

## §2 任务B — 复现清单（14 r3_* + 2 n3_*，共 77 单元：56 success / 21 failure）

统计：**MISMATCH 21 单元 / 8 文件（目标 ≥10 达成）**；MATCH 文件 6（含负对照 2，全 5/5、11/11）；文件级 6/14 success，单元级 56/77 = 72.7%。

### MISMATCH 清单

| 文件 | 焦点形态 | 读数（single） | 首分歧（原 pyc offset vs 重编译） | 根因归类（区域类型 × C 条款） |
|---|---|---|---|---|
| r3_20_for_else_break_exit | for/while-else 体含 break 出口 | 1/4（3 失败） | inner_break_out @5：o16 PJF→146 vs d16→78；else_break_with_flag @6：FOR_ITER 108 vs 110；while_else_break_exit @6：FOR_ITER 140 vs 98 | R3-A + R3-B：inner_break_out `break`→幻影 `return k` + 体后件丢失（B10）；else_break_with_flag 幻影外层 for-else + `return found` 位移（B10）；while_else_break_exit 外层 for-else 整体丢失 + `acc.append(t)` 丢失（B10） |
| r3_22_loop_else_return_continue | else 含 return/continue（continue 绑外层） | 3/5（2 失败） | for_else_continue_outer @6：FOR_ITER 180 vs 136；while_else_continue_outer @7：PJF 166 vs 100 | R3-A + R3-B：for_else_continue_outer 内层 else 体丢失 + `acc.append(j)` 丢失 + continue 位移（B10）；while_else_continue_outer `break`→幻影 `return acc` + 体尾丢失（B10）。正向：for_else_return（else=return）3/3 MATCH——else-return 与顺序 return 字节同形，判据正确 |
| r3_24_double_loop_break | 双层循环 break 内外层 + continue 混排 | 1/5（4 失败） | double_loop_inner_break @19：o19(88) JUMP_FORWARD→184 vs d19(88)→138；double_loop_outer_break @6：FOR_ITER 158 vs 160；double_loop_both_else @7：PJF 156 vs 152；double_break_with_continue @31：o31(122) JUMP_FORWARD→216 vs d31(122)→174 | R3-A + R3-B：inner_break/double_break_with_continue else 体（`append(('else',i))`/`append(-1)`）降级为顺序=无条件执行（语义错误）+ break 落进降级体（B10）；outer_break else 内 `if i==3: break` 提升为无条件 `else: break` + `if i==3: pass` 物化（B10/A5）；both_else `break`→幻影 `return acc` + 外层 while-else 丢失（B10） |
| r3_25_triple_for_else | for>for>for ≥3 层各含 else | 1/4（3 失败） | triple_for_else @29：o29(134) JUMP_FORWARD→228 vs d29→186；triple_for_mixed_break @6：FOR_ITER 214 vs 210；for_for_while_else @50：o50(200) JUMP_FORWARD→250 vs d50→204 | R3-A：内/中层 for-else 体（`'k-done'`/`'j-done'`/continue/`('j',i)`）全部降级为顺序或丢弃，break 不再跳过 else 体（B10）。深层才错形态成立（外层 else 保留） |
| r3_26_while_for_mixed | while>for 混套 + 跨层 continue | 2/4（2 失败） | while_for_mixed @23：o23(82) JUMP_FORWARD→178 vs d23→132；while_for_continue_cross @7：PJF 262 vs 270 | R3-A + R3-B：while_for_mixed 内层 for-else 降级（B10）；while_for_continue_cross `break`→幻影 `return acc` + for-else 降级（B10）。正向：nested_while_in_while_else MATCH（else 内嵌循环子区域成立） |
| r3_27_loop_try_with_match | 循环嵌 try/with/match（B9 消费层关联） | 8/9（1 失败） | loop_try_with_break @7：PJF 300 vs 304 | R3-B：try/finally 内 if-break → **双 break**（`break; break`）+ 尾 `return acc` 丢失（B10/A5×try）。正向：try 体 continue（r2_06 族）本轮 MATCH（8/9 含该单元）——r2_06 登记面在 for-else 语料未扩大 |
| r3_28_while_mixed_chain | while 条件混合布尔链（B7 关联，浅层基准） | 1/5（4 失败） | while_and_or @0：31 指令 vs 11 指令（o0 BUILD_LIST vs d0 LOAD_FAST k）；while_or_and @7：PJF 102 vs 104；while_chain3 @0：35 指令 vs 2 指令（仅 LOAD_GLOBAL acc/RETURN）；for_body_while_mixed @0：45 vs 16 | R3-C（**B11**）：`while k<m and a or c` 循环整体消失（体+出口全丢）；`while (a or b) and k<m` 条件错+幻影 continue；`while a and k<m or b and d` 函数体只剩 return；for 体嵌 while 混合链循环消失。C1/C2（_detect_while_condition_boolop_chain 判据形态覆盖面窄，浅层即败） |
| r3_31_else_mixed_if | else 块含混合布尔链 if / elif 链 | 3/5（2 失败） | else_mixed_if @23：o23(106) PJT→112 vs d23→150；elif_chain_in_else @13：JUMP_FORWARD 260 vs 262 | R3-D（**B1b 签名复现**）：`if a and b or c:` → `if not (a and b):` 极性反转 + `if c: pass` 拆裂；elif `b and c or a` 同形。C1（_build_boolop_expression 家族，loop-else 上下文）。正向：`if a or b and c`（or 先）与循环变量复用 MATCH |

### MATCH 清单（含负对照）

| 文件 | 焦点形态 | 读数 | 备注 |
|---|---|---|---|
| **n3_01_simple_loops（负对照）** | 无 else 基础 for/while/break/continue | 5/5 MATCH | 判据有效性成立（无误报基线） |
| **n3_02_guard_and_else（负对照）** | 单层 if×continue/if×break + 单层 for-else/while-else 有 break | 5/5 MATCH | 同形浅层 MATCH 与 r3_24 深层 MISMATCH 构成嵌套无感破缺的直接证据 |
| r3_21_for_else_empty | else 为空（pass/裸） | 5/5 MATCH | — |
| r3_23_if_break_continue_guard | B2 守卫族四形态 | 5/5 MATCH | A3 通过的实测依据 |
| r3_30_for_unpack_async | 元组解包/starred/嵌套解包/async for-else | 5/5 MATCH | — |
| r3_32_comp_loop_interleave | 推导式在 loop-else 内/循环内/嵌套推导 | 11/11 MATCH | — |

---

## §3 登记项复验读数表（--source 法，新产物 = test_repros/round3/_r3_*OK.py）

| 登记项 | 探针 | Round 2 归档读数 | 本轮读数（现树新产物） | 判定 |
|---|---|---|---|---|
| B7 | round1/rv_03_loopbody_forinwhile_break | failure 1/2 | **failure 1/2**（f：Different control flow） | 维持 MISMATCH，未修 |
| B7 | round1/rv_05_while_mixed_in_for | failure 1/2 | **failure 1/2**（f） | 维持 MISMATCH，未修 |
| B7 | round1/rv_09_ternary_mixed_in_while | failure 1/2 | **failure 1/2**（f） | 维持 MISMATCH，未修 |
| B9 消费层 | round2/r2_09_finally_mixed_boolop | g MISMATCH（f 单元改善 2/3） | **failure 2/3**（g 失败） | 维持（g=finally 内 while+assert 混合链装配未触发） |
| B9 消费层 | round2/r2_10_trybody_mixed_boolop | failure 2/4 | **failure 2/4**（f_while + f_ternary 失败） | 维持。注记：round2/REVIEW.md 行34 所记「f_while MATCH」与现读数不符——新产物与归档产物**逐字节相同**（diff IDENTICAL），两者同读 2/4，非新回退，疑归档文档笔误，以本表 --source 法读数为准 |
| B9 消费层 | round2/r2_17_trywrap_loop_mixed | f 残留（g 已由 B9 装配层修复封闭） | **failure 2/3**（f 失败=幻影 while False + return 丢失；g MATCH） | 与登记一致（装配层修复保持生效，消费层 f 未修） |
| R2-O3 | round2/r2_06_loop_try_continue | f MISMATCH（try 体 continue 丢失） | **failure 2/3**（f 失败） | 维持，未修 |
| R2-O3 | round2/r2_14_finally_swallows | f MISMATCH（finally 吞异常 break 丢失） | **failure 3/4**（f 失败） | 维持，未修 |

**结论**：8 项登记读数与 Round 1/2 归档状态全部一致，零回退、零意外改善；B7/B9 消费层/r2_06/r2_14 维持「登记未修」。

---

## §4 新破口登记（Bn 续接）

### B10 — loop-else×break 证据链失效族（**新登记，未修**）

- **破坏条款**：C3（守卫未封闭）为主，C2（else 块所有权被外层循环体越界认领）
- **机制（两个签名）**：
  - **R3-A（识别/归约层）**：`_find_loop_else`（`region_analyzer.py:5252`）FOR 分支 break 证据链在「break 落点与 else 出口汇聚同一续流块」形态下失效——`:5332-5333/:5344` break 落在 for_iter_exit 即 `return None` 放弃 else；`:5374-5388` 后必经推进把真 else 块让渡给外层循环体。后果：else 体降级为顺序语句（**无条件执行 = 语义错误**）或整体丢失；WHILE 分支同族（自然出口路径无 clamp、无 else 兄弟头守卫的对称判据）。
  - **R3-B（生成层）**：else 体含终结语句时出口边改写——`break`→幻影 `return acc`/`return k`；else 内 `if c: break` 提升为无条件 `else: break`；try/finally 内**双 break** 发射 + 尾 return 丢失（`region_ast_generator.py:6558-6582` 三分第二分支丢弃面在嵌套/try 上下文扩大）。
- **复现组（验收组）**：r3_20（3 单元）、r3_22（2）、r3_24（4）、r3_25（3）、r3_26（2）、r3_27.loop_try_with_break（1）= **15 单元 / 6 文件**
- **最小验收组**：r3_24.double_loop_inner_break（首分歧 o19(88) JUMP_FORWARD→184 vs →138）+ r3_26.while_for_continue_cross（break→`return acc`）
- **状态**：已定位（锚点如上），交 fix 批

### B11 — while 条件混合布尔链非名操作数形态装配灾难（B6/B7 范围扩展，**新登记，未修**）

- **破坏条款**：C1/C2（浅层即败 = 装配降级，非嵌套信号）
- **机制**：`_detect_while_condition_boolop_chain`（`region_analyzer.py:24239`）[B6-while 双向续接] `:24504-24600` 四判据仅匹配「链尾 IF_TRUE→header + 链首 IF_FALSE + or 尾成员 + 边界闭合」的 `A and B or C` 单名操作数形态；比较操作数（`k < m`）、or 组前置（`(a or b) and c`）、三操作数链（`a and k<m or b and d`）全部装配失败，主扫描残链/超越替换把循环整体吞掉。
- **复现组**：r3_28 ×4 单元（浅层！`while_and_or` 31→11 指令、`while_chain3` 35→2 指令、`for_body_while_mixed` 45→16 指令）
- **状态**：已定位，交 fix 批；**B7 判定签名修正**：B7 原登记「深层才错、浅层没事」不完整——本轮证明浅层非名操作数混合链同样失败，B6 封闭声明须降格为「`A and B or C` 单名操作数浅层封闭」

### B1b 复现扩充（不新增编号）

- r3_31.else_mixed_if / elif_chain_in_else：`if a and b or c:` → `if not (a and b):` 极性反转 + `if c: pass` 拆裂（首分歧 @23 o106 PJT→112 vs →150），= B1b 签名在 **loop-else 上下文**的新实例，验收组扩入 B1b（r3_31）。

### 观察点（未实证，不占 Bn 编号）

- **R3-O1**：`_block_is_continue_target`（`region_ast_generator.py:10407-10410`）以 `target.loop_header` 判真不区分当前/外层循环；`_loop_else_set`（`:10537`）只排当前循环 else 块——跨循环 continue 身份守卫缺失（C3 潜在面，本轮语料零触发）。
- **R3-O2**：clamp `_clamp_loop_else_to_enclosing_try`（`region_analyzer.py:5115`，唯一调用点 `:5465`）仅覆盖 FOR+break_targets 路径；WHILE 分支 try/finally 语料无对称 clamp（本轮实测未暴露缺口，r3_27 失败归 R3-B）。

---

## §5 总结论

1. **负对照双 MATCH（n3_01/n3_02 各 5/5）**——判据无误报，本轮 21 个 MISMATCH 全部为反编译器真实缺陷。
2. **任务A：5 项审计 = 2 通过（B2 家族、continue 守卫实测面）、1 有条件通过（A2，观察点 R3-O1）、2 打回（A1 → B10；A4+A5 → B11/B10 生成层）**。wiki §5.2 表A 对 For/AsyncFor、While、Break/Continue 的「完备」判定按三级判定规则（三路径存在 ∧ 不变式破坏有确证）应降格：For/AsyncFor、While、Break/Continue 三形态在「loop-else×break 证据」与「混合链条件非名操作数」两个子面存在破口确证（B10/B11），建议台账标注「浅层/受限形态完备」。
3. **任务B：14 探针 77 单元 56/77（72.7%）；MISMATCH 21 单元/8 文件（目标 ≥10 达成）；登记项 8/8 读数与归档一致（零回退），B7/B9 消费层/r2_06/r2_14 维持登记未修**。
4. **新破口：B10（loop-else×break 证据链失效族，15 单元/6 文件）、B11（while 混合链非名操作数装配灾难，4 单元浅层即败）；B1b 验收组扩入 r3_31**；观察点 R3-O1/R3-O2 待后续轮实证。
5. 交 fix 批建议：①B10 以 r3_24.double_loop_inner_break + r3_26.while_for_continue_cross 为最小验收组；②B11 以 r3_28 四单元为验收组；③回归面 = 本轮 14 文件 + round1/2 全组 + 402 全量门禁。

### 产物清单（本轮落盘）

- `test_repros/round3/r3_20..r3_32`（13 个 .py/.pyc/*OK.py）、`n3_01/n3_02`（负对照）、`_r3_firstdiff.py`（首分歧定位工具）、`_r3_rv_*OK.py`/`_r3_r2_*OK.py`（登记项复验新产物 8 件）
- 本文档：`.trae/specs/harden-completed-forms-10rounds/rounds/round3/REVIEW.md`
