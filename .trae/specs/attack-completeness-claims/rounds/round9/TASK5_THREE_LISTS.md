# Task 5.4 三类清单（rr-v5r05，全量 J C1–C5 实测）

输入：`judgment_space.json`（1556 条，Task 5.1/5.2 恢复后 `c1_source_missing=0`、`c2_pyc_missing=0`）；证据：`semantic_j_sample.json`（1556 条 C1–C5 记录，8 分片合并）；判定：`coverage_c1c5.json`（covered_5tuple=395、excluded=1107、inconclusive=54，judge=semantic_diff.py）。

## 口径（无重叠四分桶，合计 1556）

| 桶 | 条数 | 定义 |
|---|---:|---|
| covered_equal | 250 | 有 calls、C1–C5 链全通、C4 EQUAL（进入覆盖分子） |
| uncovered（缺陷清单） | 189 | C4 DIFFERENT（结构/行为差，无论是否有 calls；含 44 条同时被 module_only 降级的条目） |
| module_only（降级清单） | 675 | 无沙箱可调用入口，EQUAL 证据保留、按 Task 5.3 降级不入分子（manifest `excluded` 登记） |
| unjudgeable（不可判定清单） | 442 | C4 ERROR/INCONCLUSIVE：424 条真实语料 pyc 独立执行缺第三方依赖（IQCommon/IQEngine），18 条原件执行超时（含 JS-IF-076 `if_in_while` 源码死循环，Task 1.3 口径单列） |

checker 口径差异说明：`coverage_c1c5.json` 的 covered_5tuple=395 计入「有 calls 且 C1–C5 全通」的 EQUAL+DIFFERENT（DIFFERENT 属已判定缺陷，semantic_failures 单列），uncovered=1161 为 J_total−covered 的门禁算术，与本清单逐条四分桶口径不同；门禁 GATE FAIL 如实记录，不宣称完备。

## uncovered 缺陷清单（189 条 → 15 个探针文件 → 25 个失配单元）

| 探针文件 | 条数 | 失配单元 |
|---|---:|---|
| test_repros/round4/c4_03_except_star.py | 96 | e03_deep（for 臂内多 except* 尾多 continue）、e08_match_host |
| test_repros/round3/e04_g2_ifexp_deep.py | 12 | f_chain_ternary / f_ternary_deep_right / f_ternary_boolop_group / f_ternary_return 等 9 单元（三元链/嵌套家族） |
| test_repros/round2/x09_funcdef_hosts.py | 12 | def_in_if |
| test_repros/round4/c4_04_match_patterns.py | 12 | e02_singleton、e06_or_guard |
| test_repros/round1/r1_10_while_mixed.py | 12 | f |
| test_repros/round2/x08_stmt_leaves.py | 11 | delete_leaf |
| test_repros/round5/rec1_synth_b93d_with_ret_case.py | 7 | wrc_guard |
| test_repros/round2/x02_for_deep_hosts.py | 6 | for_in_if / for_in_while（折叠 if 1: 行头 + 循环体包裹丢失） |
| test_repros/round2/x05_with_deep_hosts.py | 6 | with_in_if / with_in_for / with_in_while |
| test_repros/round5/rec1_synth_g2b_with_match_cross.py | 5 | g2b_deep_cross |
| test_repros/round5/rec1_synth_g3b_b61_deephost.py | 4 | 无字节码失配但产物行为差（return None(None, None) 幻影调用，R3/R4） |
| test_repros/round8/rv8_02_with_tryfin_constret.py | 2 | tryfin_return_str / tryfin_return_negative / tryfin_then_more（常量 return-in-finally） |
| test_repros/round8/r8_11_deep_host_combo2.py | 2 | r8_dh2_match_guard |
| test_repros/round9/rv9_01_b68_nonfin_tail.py | 1 | emptyfin_ifelse_ret / emptyfin_in_if |
| test_repros/round5/rec1_synth_g4b_b70_whiletrue_with.py | 1 | g4b_wt_with_continue |

## module_only 降级清单（675 条）

全部 1107 条 `excluded` 登记中：675 条为「源无可调用入口且 C4 EQUAL」（探针 299 + 语义相等的语料 376）；其余 432 条 = 424 语料环境不可执行 + 8 条有 DIFFERENT 判定的降级条目（已计入 uncovered）。逐条清单见 `judgment_space.json` 各条目 `excluded`/`input_model.note` 字段（含原因）。

## unjudgeable 清单（442 条）

| 原因 | 条数 | 处置 |
|---|---:|---|
| 原件 pyc 独立执行缺第三方依赖（original artifact did not load/execute） | 424 | 环境固有：IQCommon/IQEngine 为 pyc-only 发行且依赖运行时上下文；在判据外提供依赖属非目标；逐条保留 C1–C3/C5 证据 |
| 原件执行超时（original execution timed out） | 18 | 含 JS-IF-076/114（`if_in_while` 源码级死循环，Task 1.3 口径单列）与其余超时探针 |

## Task 5.1/5.2 恢复记录

- JS-PEP604-001..012：`jspace_probes/` 生成 12 个变体探针（var-annotation × 6 宿主 + return-annotation × 6 宿主）并编译 pyc。
- 376 条 pyc-only 语料条目：原始发行无 .py（全盘核查无源），按 Task 5.1「生成等价 source」以 `jspace_sources/*__eqsrc.py` 恢复 p_j（反编译等价源，仅作 C1/C5 溯源绑定；C4 判定始终为原件 pyc vs 重生成产物，不受其影响）。
- `input_model.calls`：449 条按源结构派生（零参/全默认顶层函数、main()、零参 __init__ 类）；其余显式登记 module_only 降级。

## 修复推进更新（rr-v5r09 系列，2026-10-25）

Task 5.4 后按族修复推进（每族：定位→修复→strict 验证→全回归→J 刷新→提交）：

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| 6fdf02ac | R9-FOLDWRAP | 区域认领 setup 块上的折叠 ``if 1:`` 包裹（for/with/def 宿主）+ 多 item with 边界 NOP 嵌套切分 | x09 全等（12）|
| 9bf19184 | R9-ELIDE | 无回边 ``while 1:``+尾 break 消除壳（with 宿主变体） | x05 全等（6）|
| 96f07bd5 | B214b | B142 continue 物化的 try 体出口闩窄守卫 | x08 全等（11）|
| 5c31c7d1 | R10-TRYLINE + R9a | try 行首标记 NOP 游程消费；match 臂锚排除 | rv8/rv9 全等（5）|
| 7a5c0df2 | B215 | 无 COPY 字面量 match 识别（双锚判据） | e08 全等（文件级待 e03）|

读数：covered_equal 250→**281**、uncovered 189→**157**（回收 32 条）、module_only 675→676、unjudgeable 442。
每次提交均通过：shard0 786/786、small34 1568/1568、pytest 406 失败清单逐字节一致、fuzz 24/24、探针全绿。

剩余 uncovered 157 主簇：JS-EXCEPTSTAR 96（待 B214 e03 绿重试；e08 已由 B215 解锁）、
JS-WHILE 14（while+BoolOp 回边重测链未识别）、JS-IFEXP 12（三元链族）、
match 子族（c4_04 singleton/or_guard、r8_11、g2b）、g3b 行为差（return None(None,None)）、g4b 等单点。

## B214 修复落地（rr-v5r10，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | B214 | `_b214_try_tail_natural_backedge`：try 体顺序收尾块的直连裸回边 = 「源码无 continue」的编译签名（显式 continue 编译为 JUMP_FORWARD 中转形态）；抑制幻影 Continue 发射 | JS-EXCEPTSTAR 全等（96）|

- 判据（I.4 白名单结构事实）：剥噪后恰为一条裸 JUMP_BACKWARD 且目标=当前循环 header；块在 TryExceptRegion try 跨度内（try 体侧块全部在循环体内，except* 清理链尾可越界）；存在 try 侧非跳转收尾前驱顺序落入本块（条件 continue 块的前驱以条件跳转收尾，被排除）；后继除 header 外仅异常处理入口。
- 与 R11 守卫的关系：R11 保护 try 跨度内**中段** continue（省略后编译器生成 JUMP_FORWARD 越过 handler）；本谓词只命中 try 体**顺序收尾点**的直连回边，二者不冲突（e03_deep 前驱 @42 POP_TOP 非跳转）。
- 验证：c4_03_except_star 13/13 单元 strict 全等；pytest 406 失败清单与基线逐字节一致（PYFAIL_IDENTICAL）；402 语料读数零漂移（57 EQUAL/3 DIFFERENT/342 环境性，flips=0）；fuzz 24/24 EQUAL；x01 7/7。
- 读数：covered_equal 281→**377**、uncovered 157→**61**、module_only 676、unjudgeable 442。

剩余 uncovered 61（9 探针文件）：e04_ifexp 12、c4_04_match 12（e02_singleton/e06_or_guard）、
r1_10_while 12（BoolOp 回边重测）、b93d_wrc 7、x02_for 6、g2b_match_cross 5、
g3b_b61 行为差 4、r8_11 2、g4b 1。

## r1_10 修复落地（rr-v5r11，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | B134-V3R4 | `_while_pred_has_body_retest` 组边界重检豁免：and 组成员假边直达 or 尾重检块（=回边块，POP_JUMP_BACKWARD 收束到 header）且目标谓词与 pred 不同时认作有效重检；同谓词（``if A: while A:`` 习惯形）维持拒绝（x08::return_leaf 实证回归后收紧） | JS-WHILE 12 条转 EQUAL |

- 形态：``while a and b or c:`` 混合链——链检测后向回溯在 a 前缀处被 V3R3 守卫截断（a 重检块 @56 假边目标=回边块 @64，被「目标须离开循环」误拒），无 BoolOpRegion → 错读为 ``if a: while b:`` + 回边链散架。
- 验证：r1_10 2/2 单元 strict 全等；x08 回归闭环（宽松版曾致 return_leaf ``while i and i:``，收紧后恢复字节精确）；pytest 406 逐字节一致；402 语料零漂移（0067 单条竞态假漂移复跑归位）；fuzz 24/24；8 探针全绿。
- 读数：covered_equal 377、uncovered 61→**49**（12 条 JS-WHILE DIFFERENT→EQUAL；无calls 入 module_only 降级桶，676→688）、module_only 688、unjudgeable 442。

## g4b 修复落地（rr-v5r12b，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | B66c | `_b66c_is_with_exit_return_chain_head`（B66 的 return 变体）：with 体内 if 假臂落点的边界 NOP 块 + 后继 [__exit__(None×3) 清理 + return 载荷] 时抑制占位 pass，接入两个 B66 站点 | JS-WHILE-042 EQUAL |

- 验证：g4b 文件 strict 全等（幻影 pass 消除）；pytest 406 逐字节一致；fuzz 24/24；探针全绿。
- 读数：covered_equal 377、uncovered 49→**48**、module_only 689、unjudgeable 442。

## x02 修复落地（rr-v5r13，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | R9-ELIDE-f | while-1 消除壳 for 宿主三处扩展：①头 NOP 内联在 setup 前驱块（排除回边前驱）；②头 NOP 独立成块（唯一前驱链回走）；③尾 break 标记块放宽（前驱在区域内 / 块本身在 region.blocks 内）；④调度兜底扩展 len>2（[wrap, For, 尾随 return]）；⑤壳读法取代 wrap 占位读法（头 NOP 认领排除移除） | JS-FOR x02 6 条 covered_equal |

- 验证：x02 文件 strict 全等（for_in_while 的 ``while 1:`` 壳 + break 正确重建）；x05（with 宿主原用户）保持 strict；pytest 406 逐字节一致；402 语料零漂移；fuzz 24/24；12 探针全绿。
- 读数：covered_equal 377→**383**、uncovered 48→**42**、module_only 689、unjudgeable 442。

## b93d 修复落地（rr-v5r14，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | B93d | match 臂内 with 机制块（__exit__ 清理 / WITH_EXCEPT_START 处理链 / 纯异常展开块 COPY+POP_EXCEPT+RERAISE+POP_TOP）空语句时不再补幻影 pass | JS-WITH 7 条转 EQUAL |

- 实测依据：wrc_guard 的 co_code 差 = 双幻影 pass 各产生 1 NOP 使全部出口目标偏移 4 字节；嵌套 with 与多 item with 的 co_code 本身逐位相同（`with A as b: with B as c:` ≡ `with A as b, B as c:`）。
- 验证：b93d 文件 strict 全等；pytest 406 逐字节一致；fuzz 24/24；9 探针全绿（g2b/e04 为各自族原样）。
- 读数：covered_equal 383、uncovered 42→**35**、module_only 696、unjudgeable 442。

## c4_04 修复落地（rr-v5r15，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | C404 三联 | ①`_c404_match_arm_tail_natural_backedge`：match 臂尾直连回边 = 无 continue 签名（B214 的 match 臂变体），抑制臂体+回边融合块的幻影 Continue；②C404w：落空机制伪臂丢弃（真 ``case _: pass`` 编译含 NOP 行标记，裸 [POP_TOP, JUMP_*] 是失败出口非臂，实测 WITH/WITHOUT NOP 对比）；③C404n：B103 with 宿主分支补 `_match_arm_entry_block_without_marker`（与 Try 分支同构），臂入口 case 行 NOP 不再被读成 ``if 1:`` 包裹 | c4_04 12 条 covered_equal |

- 验证：c4_04 全文件 strict 全等（e02 幻影 continue×4 + 幻影通配臂、e06 ``if 1:`` 包裹均消除）；pytest 406 逐字节一致；402 语料零漂移；fuzz 24/24；12 探针全绿。
- 读数：covered_equal 383→**395**、uncovered 35→**23**、module_only 696、unjudgeable 442。
- 剩余 uncovered 23：e04_ifexp 12（6 子族长尾）、g2b_match_cross 5、g3b 行为差 4、r8_11 2（尾 return None 吞没点未定位，已时间盒）。

## g2b 修复落地（rr-v5r16，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | G2B | case 臂体剥噪后恰为 [LOAD_CONST None, RETURN_VALUE] 时发射显式 ``return None``（空臂/落空编译为跳 match 尾而非 return；带值 return 的 LOAD_CONST argval 非 None 不入此列） | g2b 5 条转 EQUAL |

- 过程：首版（仅看末两条 opcode）引发 95 项 pytest 回归 + fuzz 1 例（``return 'small'`` 等带值 return 的常量装载也被误配）——已回退；v2 收紧为「剥噪后恰两条且 argval is None」全绿。
- 验证：g2b 文件 strict 全等；pytest 406 逐字节一致；fuzz 24/24；8 探针全绿。
- 读数：covered_equal 395、uncovered 23→**18**、module_only 701、unjudgeable 442。
- 剩余 uncovered 18：e04_ifexp 12（6 子族长尾）、g3b 行为差 4（字节相等但行为差 return None(None,None)）、r8_11 2。

## g3b 修复落地（rr-v5r17，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | G3B | match 臂内 with 退出 return 机制块跳过（[SWAP/COPY 前导] + [LOAD_CONST None×3, PRECALL, CALL] + POP_TOP/SWAP/COPY 余量 + RETURN_VALUE 收尾 + WithRegion 成员；余量集检查排除末位 RETURN 本身） | g3b 4 条 R3 行为差→EQUAL |

- 根因：臂内 return 值穿透 with 体的机制块 [SWAP 2, None×3, CALL, POP_TOP, RETURN_VALUE] 被语句重建为幻影 ``return None(None, None)``（不可达但 R3 行为判定失败）。
- 调试教训：初版谓词的余量集检查把末位 RETURN_VALUE 一并要求 ∈ {POP_TOP,SWAP,COPY} 恒 False——三小时排除法（陈旧 pycache/区域时序/内联重写均为假嫌疑）后定位为 rest[:-1] 边界；内联版修复后全绿，未用 helper 已删。
- 验证：g3b strict 全等 + 幻影消除；pytest 406 逐字节一致；fuzz 24/24；12 探针全绿。
- 读数：covered_equal 395、uncovered 18→**14**、module_only 705、unjudgeable 442。
- 剩余 uncovered 14：e04_ifexp 12（6 子族长尾）、r8_11 2（尾 return None 吞没点未定位）。

## G2B v3 收敛与本轮修复阶段小结（rr-v5r18，2026-10-25）

| 提交 | 修复 | 说明 |
|---|---|---|
| 0a988981 | G3B with 退出 return 机制块跳过（rest[:-1] 边界修复） | g3b 4 条 R3→EQUAL，uncovered 18→14 |
| (本轮) | G2B-v3 全块形态判据（POP_TOP 计入） | 修复 v2 在 r8_11 落空尾块上的误触发（``case _: pass`` 不再变 ``case _: return None``）；g2b 保持全等 |

### 本修复阶段累计（rr-v5r09f 起）

| 提交 | 族 | J 回收 |
|---|---|---:|
| 7eceaa61/6bb07820 | 台账刷新（三族） | 32 |
| cad5e8c0 | B214 try 尾自然回边 | 96 |
| be826688 | B134-V3R4 混合链组边界重检 | 12 |
| 02aed0d9 | E04a 三元 return 穿透 for 迭代器清理 | (3 单元) |
| ce849302 | B66c with 退出 return 链头 | 1 |
| d8590c9c | R9-ELIDE-f while-1 壳 for 宿主 | 6 |
| 32b2b09f | B93d match 臂 with 机制块 | 7 |
| 7acdf676 | C404 三联 + G2B v2 | 12+5 |
| 0a988981 | G3B 机制块 | 4 |
| (本轮) | G2B v3 收敛 | 0（防回归）|

**读数：covered_equal 281→395、uncovered 189→14、module_only 676→705、unjudgeable 442。**
每步均通过：目标探针 strict 全等、pytest 406 失败清单逐字节一致、402 语料零漂移（4 次全跑）、fuzz 24/24（≥10 次）、全探针电池回归。

### 剩余 uncovered 14（登记）
- e04_g2_ifexp_deep 12：6 个子族（as_cond 宿主丢失 ``in xs``、boolop_group 幻影 return None、comp_cond 三元误读 BoolOp、default_arg 双 def、nested_in_boolop 结构散架、walrus_rhs 载荷）——文件级判定需全部修复。
- r8_11 2：match 尾 [POP_TOP×2, NOP, NOP, LC None, RETURN] 的显式 return None 需从 case_bodies 剥离改走 B15 merge 发射（分析器层，两次定位时间盒用尽，判据与字节签名已留档本文件 rr-v5r12b~v5r18 各节）。

### 环境性不可回收（442 unjudgeable + 424 语料）
固有依赖（IQCommon/IQEngine 运行时上下文）与 18 条原件超时，维持判定外处置。

## r8_11 修复落地（rr-v5r20，2026-10-25）

| 提交 | 族 | 修复 | J 条目 |
|---|---|---|---:|
| (本轮) | R811 | match 伪臂体 [POP_TOP×2, NOP, NOP, LC None, RETURN]（``case _: pass`` 行标记 + match 后 ``return None`` 行标记，body_start 切分致 NOP 划出臂体）拆分：case 体仅再生 pass 的 1 NOP，Return(None) 打 ``_explicit_return`` 旗标（R15-10 既有豁免机制）提为 match 后语句 | r8_11 2 条 EQUAL |

- 定位链：case_body_start_indices 划分（@4）与生成期 pattern_store_names 重算（@6）不一致 → body_instrs=[LC,RETURN] 落噪声过滤；改用全块判据（含 POP_TOP 前缀 + 双 NOP + return None 尾 + 白名单）。
- 渲染链：AST 追加成功但 code_generator._filter_trailing_return_none 把末尾 Return(None) 当隐式返回剥离——该机制已有 ``_explicit_return`` 豁免旗标（R15-10），打旗即过。
- 验证：r8_11 文件 strict 全等；pytest 406 逐字节一致；fuzz 24/24；14 探针全绿。
- 读数：covered_equal 395、uncovered 14→**12**、module_only 707、unjudgeable 442。
- 剩余 uncovered 12：e04_ifexp 12 条（6→3 子族已修 3：boolop_group/walrus_rhs/default_arg；剩 as_cond/comp_cond/nested_in_boolop 3 单元，文件级判定需全修）。

## e04 三元族推进（rr-v5r19~v5r21，2026-10-25）

| 提交 | 修复 | 单元 |
|---|---|---|
| 92a60ed5 | E04b/c/d：清理对+后继 RETURN（boolop_group）、walrus return 消费者（walrus_rhs）、ternary 宿主 def 去重（default_arg，双 store-statement 分支） | 3 |
| (本轮 E04f) | comp-filter 三元假值常量折叠（假臂单条回循环头直跳 → orelse 规范 0） | comp_cond |
| (本轮 E04g) | BoolOp 尾跨块形态分支（防御性；nested_in_boolop 崩在更上游未触发） | 0 |

- e04 文件 9 单元 → **7 strict 全等**；文件级 J 判定需全部修复，12 条暂维持 uncovered 登记。
- 剩余 2 单元（字节签名留档）：
  - ``f_ternary_as_cond``：``if (a if b else c) in xs:`` 的 Compare(IfExp, In, xs) 消费——TernaryRegion merge_context=compare 已标但 compare 重建未接管；且 if 假出口 @50 与 while 假出口 @54 同块 @64，while 被读成 if（区域化两层合并）。
  - ``f_ternary_nested_in_boolop``：``return (a if b else c) and d`` 的 while i 区域未建立（单元整体散架为 ``if i: pass``）——LoopRegion 判定层，非消费者层。
- 验证：E04f/G 提交均 pytest 406 逐字节一致、fuzz 无失败、402 语料零漂移（flips=0）、14 探针电池全绿。

### 最终读数（本轮修复阶段 rr-v5r09f → rr-v5r21）

**covered_equal 281→395、uncovered 189→12、module_only 676→707、unjudgeable 442。**
剩余 uncovered 12 = e04_ifexp 12 条（9 单元中 7 已 strict 全等，2 单元待上游区域判定修复，签名如上）。

## ═══ uncovered 归零（rr-v5r22，2026-10-25） ═══

| 提交 | 修复 | J 条目 |
|---|---|---|
| 60cf9628 | R811 match 尾拆分 | r8_11 2 |
| rr-v5r19 | E04b/c/d（清理对 RETURN / walrus return / ternary 宿主 def 去重） | (e04 3 单元) |
| rr-v5r21 | E04f comp-filter 假值折叠 | (comp_cond) |
| (本轮 rr-v5r22) | E04h compare 消费者构建 if 语句（`if (a if b else c) in xs:`，父认领让位门）；E04g BoolOp 尾跨块（双后继 + 收尾链拼接） | e04 全 12 条 |

**最终四桶（判定空间 1556 条）：**

| 桶 | 条数 |
|---|---:|
| covered_equal（有 calls、C1–C5 全通、C4 EQUAL） | **395** |
| uncovered（缺陷清单） | **0** |
| module_only（无沙箱入口、EQUAL 证据保留、降级） | 719 |
| unjudgeable（环境性：424 缺依赖 + 18 超时） | 442 |

- 判定空间内全部 1114 条可判定条目 C4 均 EQUAL（395 入分子 + 719 module_only 降级）；DIFFERENT 缺陷清单清零。
- 402 语料零漂移（57 EQUAL / 3 DIFFERENT / 342 环境性，flips=0）；pytest 406 失败清单与基线逐字节一致；fuzz 24/24；16 探针文件 strict R7 全等。
- E04h 收紧过程：首版放宽 ctx 门槛引发 5 项 pytest 回归（抢走父区域认领的 compare/while_cond 形态）→ 加父认领让位门（IfRegion/LoopRegion.condition_block is merge/entry 时放弃）后归零。
- E04g 定位链：BoolOp 尾跨块三段（@54 [JIFOP] / @56 [LOAD d] / @58 [SWAP,POP_TOP] / @62 [RETURN]），块切分比预期细——双后继判定 + 收尾链拼接。

## 语料残差收尾（rr-v5r23，2026-10-25）

402 语料 C4 读数 57 EQUAL / **3→2 DIFFERENT** / 342 环境性：

| 条目 | 定性 | 处置 |
|---|---|---|
| CORPUS402-0373 (fly/common/user_error) | 模块尾行标记 NOP（Round 33 占位被渲染为三引号空串 → 末位常量语句被本机编译器消除） | **已修 rr-v5r23**：`[UERR]` 模块尾占位替换 [Pass, Expr(0)]（pass 非末位发 1 行 NOP + 尾随常量消除垫背，实测单 NOP 构造）→ EQUAL |
| CORPUS402-0226 (IQEngine/interface) | 类体 @abstractmethod def 前装饰行/def 行标记 NOP（REF 双 NOP） | 登记：本机 3.11.7 编译器对类体 pass/常量语句全消除（实测），行标记 NOP 无法从源码构造复现；REF pyc 为其他 3.11 微版编译 |
| CORPUS402-0354 (fly/common/convert) | `direct_chn2arab` 的 @420 块身兼 if 假出口 else 体 + 循环回边（`total_integer += r*val`），反编译接为 continue 后死码位 | 登记：修复需动分析层 IfRegion merge 判定（假出口目标含用户语句时取目标块），全语料回归风险高；R3/R4 行为判定无差异（执行覆盖未达该路径） |

- 验证：user_error 4/4 单元 strict 全等；pytest 406 逐字节一致；fuzz 24/24。
- 判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442）；本轮修复属语料证据面（G2b 402）。

### convert 残差补充定性（rr-v5r23b）

E05a 假出口 else 体补发原型实测：orelse 正确装配（total_integer += r*val 进 else 位）但牵动循环回边补发与后续平级 if 的 elif 化（字节差从 51→44 但引入新结构差）。回退原型，登记两项前提：
① 循环回边块身兼 else 体时，回边补发逻辑需与 orelse 装配协同（back_edge_block 语句/continue 补发需感知 orelse 已覆盖）；
② 假出口目标块标记 generated 后，后续平级 if 的 elif 判定受块标记顺序影响。
两处均为装配层协同问题，非单点谓词可修；1 条语料条目 vs 分析层全局回归风险，按时间盒原则登记。

### CORPUS402-0354 装配层协同修复（rr-v5r24，2026-10-25）

rr-v5r23b 登记的两项前提已按族级谓词落地，E05a 重新启用并带两道结构门：

- **[E05a-g1]** 假出口目标块即本区域 merge_block 时不收编——merge 同时被 then 臂出口自然贯通（平级语句流），收编后 then 出口改 JUMP_FORWARD 越过 else 臂，凭空多出 return None 块（0354 @438/@636 实测）。修复前提②：假出口目标标记 generated 对后续平级 if elif 判定的影响由此门归零（E05a 不再触碰 merge 块）。
- **[E05a-g2]** 仅服务「块即回边」形：目标块末条须为无条件 JUMP_BACKWARD(→循环头)（0354 @420 形，块本身是回边、循环机制无法把它当体语句再发）。while 循环回边由独立条件重测块承担、体尾块只是落回重测块（L13_WhileElse 形），此时收编会把 while-else 体/平级语句吸入 orelse 并越界游走，不触发。修复前提①：回边补发感知 orelse——E05a 游走在 JUMP_BACKWARD 即断、沿途块登记 generated，循环体走查按已生成跳过，不重复补发回边 continue。

- 0354 `direct_chn2arab` strict R7：全单元 co_code sha256 **DIFFCOUNT 0**（REF 158 指令逐字节全等，含 @420 回边块）。
- 全电池：pytest 406 失败清单与基线**逐字节一致**；fuzz 24/24 EQUAL（0 失败）；402 语料 **59 EQUAL / 2→1 DIFFERENT / 342 环境性**，唯一翻转即 0354 DIFFERENT→EQUAL（漂移读数 _r5_drift_r24.json）。
- J 刷新：CORPUS402-0354 复测记录 c4.verdict=EQUAL（make_record，judge sha 对齐 run9 口径；module_only 语义不变）。
- E05a-g2 首版（back_edge_block 身份判据）不足：while 的 back_edge_block 指向重测块前的体尾块，身份成立仍会游走——收紧为「末条无条件 JUMP_BACKWARD→header」结构判据后 11 处 while-else 回归全部消除。
- 判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442）。

402 语料残差仅剩：

| 条目 | 定性 | 处置 |
|---|---|---|
| CORPUS402-0226 (IQEngine/interface) | 类体 @abstractmethod def 前装饰行/def 行标记 NOP（REF 双 NOP） | 登记：本机 3.11.7 编译器对类体 pass/常量语句全消除（实测），行标记 NOP 无法从源码构造复现；REF pyc 为其他 3.11 微版编译 |

### G5 全量回归本轮复跑（rules.md §6.2-11/15 口径，2026-10-25）

E05a 落地后按规则门禁命令全量重跑（非历史引用；读数 `_r5_g5/g5_after_summary.json` + 8 分片原始报告）：

| 门禁 | 历史基线 | 本轮复跑 | 结论 |
|---|---|---|---|
| 402 语料八分片（pyc_verify batch ×8） | 402/402 files_failure=0；单元 6617/6617 | 402/402，failure/compile_error/error 全 0；单元 6617/6617（786+469+538+887+855+999+801+1282） | 一致 |
| small34 | 34/34；1568/1568 | 34/34；1568/1568 | 一致 |
| quotation 单验 | 153/153 rc=0 | 153/153 rc=0 | 一致 |
| tests 七套件 | 2 failed / 282 passed / 2 xpassed（基线名单） | 2 failed / 282 passed / 2 xpassed；失败名单逐位一致（test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function） | 一致 |
| IV.2 | 全绿 | IMPORT_OK（八 core 模块）；region_analyzer/region_ast_generator BOM 单头 + compile() 过；本轮新增前缀方法仅 `_e05a_false_exit_else`（E05a，六项 docstring 已登记）；无 start_offset 阈值/深度上限 | 一致 |

- 判据完整性：`freeze_check.py` 5/5 PASS（pyc_verify.py 与外部 equivalence_check.py SHA 未动）；本轮 G2b 语料读数 59 EQUAL / 1 DIFFERENT / 342 环境性（唯一翻转 0354）。
- 诚实状态（rules.md §16/§17）：v3 放行门禁（§11 五项）本轮全过；**v9 overall 维持 BLOCKED**——G1 全量 0/1556、G3/G4 UNESTABLISHED、G6 未重跑、G2b 含 1 DIFFERENT + 342 环境性 ≠ 0 失败门。本轮只可表述为「形态门禁零回归 + 语料残差 2→1」，不得写完备/100%。
- 附注：`tests/nook` 不在规则门禁内（七套件口径不含），其收集期 FileNotFoundError（缺运行期数据文件 file3.txt 等）为既存状态；本轮为本地调试在树根补建 file3.txt（未跟踪 scratch，不随提交）。

### rr-v5r26：两族根因修复（2026-10-26）

对 G2c 24 条 DIFFERENT 中的 `core/fast_stack.py` 族（REAL46-039/040/041/042/044/045/046 子集）定位到两个通用根因，均按族级判据修复。

#### B220-V3R26 块中段 SWAP 多目标交换赋值

- 现象：`FastStack.swap` 的 `self._stack[idx1], self._stack[idx2] = self._stack[idx2], self._stack[idx1]` 被反编译为 `self._stack[idx1] = self._stack[idx1]`，第二目标整体丢失。
- 根因链：交换赋值所在块是 `IF_ELIF_CHAIN` 的 else 臂，块内已有两条前导语句（`idx1 = self._ptr`、`idx2 = self._ptr + 1 - i`）的 STORE_FAST，SWAP 不在块首 → 块首 SWAP 解析器 `_swap_unpack_result`（要求 `_swap_idx >= 1` 且值段不含 STORE_*）整体失效；SWAP 又属 `SKIP_OPS` 永不进 `stmt_instrs`；于是首个 `STORE_SUBSCR` 把 `[值段+目标1窗口]` 当单目标消费，第二目标被吞。
- 判据（只读块内指令序，I.4 白名单）：自当前 STORE_* 向前回溯并跳过 `RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG`，首个非噪声须为 `SWAP(arg>=2)`；回溯途中遇任一 `_SWAP_TARGET_STORE_OPS`（`STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF/STORE_ATTR/STORE_SUBSCR`）或 `POP_TOP/RETURN_*/RAISE_VARARGS/IMPORT_NAME/YIELD_VALUE` 即放弃；SWAP 前最后一条非噪声指令须是值段末条；SWAP 之后须恰解析出 N 个「目标窗口 + STORE_*」且第 0 段 STORE 即当前指令；值段净栈效应（`_instruction_stack_effect` 求和）须恰为 N；目标窗口映射 Name/Attribute/Subscript；含复杂目标才收（纯名字目标返回 None，归 SIG2 反源序连续 STORE 路径）。
- 归约：整组 → `Assign(Tuple(targets, Store), Tuple(rhs, Load))`，消费区间 `[SWAP 起点, 末 STORE]`；C3：不命中返回 None，既有 STORE_* 路径逐位不变。
- 落位：`core/cfg/region_ast_generator.py` 新增 `_build_swap_multi_target_assign`（六项 docstring + C1/C2/C3，约 71333 起）与 `_generate_block_statements_body` 块语句流前置门（约 68163 起）。
- 最小复现 `/tmp/mini2`（`class C.swap` 带前导 `idx1/idx2` 语句）：修复前 `self._stack[idx1] = self._stack[idx1]`；修复后 `self._stack[idx1], self._stack[idx2] = (self._stack[idx2], self._stack[idx1])`；逐 code object 重编译 `co_code/co_consts/co_exceptiontable` 零差异。

#### B221-V3R26 常量折叠注解元组

- 现象：`FastStack.clear/copy`、`StackHistory.clear`、`DebugStack.reset_operations` 的 `-> None` / `-> 'FastStack'` 注解静默丢失，重编译 `co_consts` 48→46 / 12→11 / 21→20。
- 根因链：注解元组元素全为常量时 CPython 把 `BUILD_TUPLE` 折叠为单个 `LOAD_CONST`（如 `LOAD_CONST ('return', None); LOAD_CONST <code>; MAKE_FUNCTION 4`）；`ExpressionReconstructor` 据此产出 `{'type':'Constant','value':('return', None)}` 而非 Tuple 节点；`_build_function_def` 仅识别 `type == 'Tuple'`，`_annotations.get('return')` 恒为 None。
- 修复：新增 `Constant + tuple` 分支，按同一 `(name, type)` 交替序列还原为 Constant 元素序列，与 Tuple 路径共用归属循环；非 tuple 常量不在此列（C3）。
- 最小复现 `/tmp/mini3`（`clear -> None`、`copy -> 'FastStack'`）：修复后注解保留；重编译 4 个 code object 的 `co_code` 与 `co_consts` 长度逐项相等。

#### 复跑读数（本轮实测，不引用历史）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | `out.json` 2 EQUAL / 5 DIFFERENT → `out3.json` **4 EQUAL / 3 DIFFERENT**；REAL46-040 6 diffs→0、REAL46-042 2→0、REAL46-045 33→31；041/046 各 1 仍 DIFFERENT（其他族） |
| A/B 零回归 `/tmp/ab`（24 个 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `same=24 diff=0 total=24` |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`） |
| fuzz | `total=24 failures=0 stopped=case_limit` |
| `freeze_check.py` | 3/5 PASS；2 项 FAIL 已定性：`pyc_verify_sha256` 为换行符口径差异（`sha256(LF)=CA8E63DF...`、`sha256(LF→CRLF)=FE1902A9...`，`git diff -- scripts/pyc_verify.py` 为空），`external_equivalence_check_sha256` 为外部判据文件缺失（Windows 路径 `D:\Desktop\ptrade相关\pylingual`） |
| 402 八分片 / small34 | 本沙箱不可重跑：`/workspace/site-packages/` 仅 1 个 `.pyc`（quotation），`pyc_index.json`/`small34_index.json` 为 Windows 绝对路径，small34 34 条中 33 条 pyc 缺失；如实登记为环境不可达 |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442）。诚实状态（rules.md §16/§17）：v9 overall 维持 **BLOCKED**。

### rr-v5r27：两族根因修复（2026-10-26）

REAL46-041（`core/object_pool.py`）与 REAL46-046（`tools/kb/syntax_coverage.py`）各定位到一族通用根因。

#### B222-V3R26 函数体 scope 声明置于 docstring 之前

- 现象：`get_ast_node_pool` 反编译为 `global _ast_node_pool` 在 docstring 之前，重编译后 docstring 退化为常量表达式语句（编译为行 NOP），`__doc__` 变 None 且 `co_code` 恰多 1 条 NOP（REAL46-041 唯一诊断 `co_consts.v[10].code_sha`）。
- 根因：`_build_function_def` 把 `scope_stmts`（由 `_detect_global_declarations` 产出）无条件前置到 `body[0]`，而 `generate()` 已先把 docstring Expr 放在首位——顺序被颠倒。
- 修复：按首节点结构 `Expr(Constant(str))` 判定 docstring 头，命中则把 scope 声明插到索引 1，否则仍在 0 位（旧行为逐位一致，C3）。
- 最小复现 `/tmp/mini3` 扩展 + `shutil._fastcopy_sendfile` A/B：`global` 回到 docstring 之后。

#### B223-V3R26 for_iter_setup 前导区连续 STORE 段整组归约

- 现象：`extra_covered, extra_uncovered = [], []` 反编译为 `extra_uncovered = []`，首目标整体丢失（REAL46-046 诊断 `co_consts.v[64].code_sha` + 后续偏移错位）。
- 根因：该赋值位于 for 循环前导块，经 `_loop_extract_for_iter_pre_stmts` 逐 STORE 调 `_build_store_statement`；首 STORE 把整段值指令当单一 RHS 只弹栈顶，后随 STORE 因 `_buf` 已清空而无值可配，目标被吞。该路径没有 `_generate_block_statements_body` 内的 SIG2 归约。
- 判据（I.4 白名单：块内 opcode 序 + 值栈净效应）：当前 STORE 后紧邻另有 STORE_* 形成 N>=2 连续段；值段无 `COPY/SWAP/UNPACK_SEQUENCE/UNPACK_EX`（排除链式/cell 交换/元组解包，后者已由上方 UNPACK 分支整条消费）；值段重建栈深 >= N。
- 归约：`Assign(Tuple(源序目标), Tuple(压栈序值))`，目标取 STORE 段反序；被吸并的次级 STORE 记入既有 `_unpack_skip_remaining` 计数器（每块唯一归属）。守卫不命中逐位落回旧路径（C3）。
- 最小复现 `/tmp/mini4`：修复前 `extra_uncovered = []`，修复后 `extra_covered, extra_uncovered = ([], [])`；`enum` 的 `original_names, names = (names, [])` 同步恢复。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | rr-v5r26 的 4 EQUAL / 3 DIFFERENT → **6 EQUAL / 1 DIFFERENT**；新增翻转 REAL46-041（1→0）、REAL46-046（1→0）；仅剩 REAL46-045（`scripts/pyc_verify.py`）31 diffs |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `same=19 diff=5`；5 处逐项核对均为**改进**：functools/logging/tempfile 差异 code object 数与指令差同时下降，enum 恢复 `original_names, names`，shutil `global` 回到 docstring 之后；零回归 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，名单与基线逐位一致 |
| 最小复现 | `/tmp/mini2`（B220）产物不变；`/tmp/mini3`（B221/B222）注解与 docstring 顺序正确；`/tmp/mini4`（B223）双目标恢复 |

判定空间四桶不变。REAL46-045 残差已定位到「大 dict 字面量赋值整体丢失」（`report = {...}` 只剩一个 value 表达式），登记为下一轮族。

### rr-v5r28：IF_TRUE 内联 if 双重翻转（2026-10-26）

REAL46-045（`scripts/pyc_verify.py`）的 31 diffs 中，`cmd_single` 的结构错位单独成族修复。

#### B224-V3R26 BoolOp 后继 merge 块尾部内联 if 的 IF_TRUE 极性

- 现象：`cmd_single` 中 `if not os.path.isfile(source): sys.exit('[fatal] 缺少产物 %s' % source)` 之后的 `tmp = tempfile.mkdtemp(prefix='pycverify_')` 被搬进 if 体，而 `sys.exit(...)` 落到 if 之外——真值路径与假值路径整体互换。
- 根因链：`_generate_boolop_impl` 的 R89 内联 if 提取对 `POP_JUMP_FORWARD_IF_TRUE` 把**跳转目标**当 then 臂、fall-through 当 else 臂，而测试表达式按原始栈值重建后再由 `_if_negate_r89` 对 `TRUE/NONE` 取反一次 ⇒ **双重翻转**。`POP_JUMP_FORWARD_IF_TRUE` 的语义是条件为真时跳转到跳转目标、fall-through 为假值路径，取反后的 then 臂必须取 fall-through。
- 判据（I.4 白名单：仅读跳转 opname 与其两个后继块身份）：命中 `FALSE` 分支保持跳转目标作 else 臂（旧行为）；命中 `TRUE` 分支时 then 臂取 fall-through、else 臂取跳转目标；其余（无极性信息）沿用 fall-through 作 then。
- 归约：只交换该分支两个块变量的绑定，不新增区域、不改归约次序；`FALSE` 与无极性路径逐位不变（C3）。
- 落位：`core/cfg/region_ast_generator.py` `_generate_boolop_impl` 的 R89 IF_TRUE 分支（约 50629–50646 行）。
- 最小复现 `/tmp/mini7`（`source = args.source or 'z'` + `if not os.path.isfile(source): sys.exit(...)` + `tmp = tempfile.mkdtemp(...)`）：修复前产物把 `tmp = ...` 放进 if 体；修复后与源码逐行一致。对照 `/tmp/mini6` 的三种 `if not ...: sys.exit(...)` 形态（无 BoolOp 后继 merge 尾部内联）修复前后均正确，确认触发面恰为该路径。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**（REAL46-045 仍 31 diffs）；`cmd_single` 语义已恢复源码形态，残差收敛到第二族（`print('%s' % (..., ternary))` 被识别为 tuple 容器构造三元 + 大 dict 字面量赋值整体丢失） |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `same=19 diff=5`，与 rr-v5r27 的 5 处改进逐项同文；`new3` vs `new4` **24/24 一致**，B224 零回归 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=24 failures=0` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

### rr-v5r29：容器字面量中兄弟推导式的 GET_ITER/MAKE_FUNCTION 误判（2026-10-26）

REAL46-045（`scripts/pyc_verify.py`）残差的第二族：`cmd_batch` 的 `report` 大 dict 字面量整体丢失。

#### B225-V3R29 汇合块栈纪律：兄弟推导式先压栈导致三元作迭代器误判

- 现象：`report = {'rate': ..., 'files_by_status': {c: len(v) for c, v in buckets.items()}, 'rows': rows}` 反编译为键值错位的短字典 / 裸表达式语句；修复第一处后进一步退化为 `@(ternary) def <target>(.0): {...}` 伪装饰器函数，宿主容器赋值整体消失。
- 根因链：同一字典字面量内，紧跟三元项的**兄弟推导式**在汇合块前段先执行 `LOAD_CONST <dictcomp>; MAKE_FUNCTION 0; <iterable>; GET_ITER; CALL 0`，此时三元结果仍压在栈底。分析层 `_identify_ternary_regions` 的 merge_context 扫描只看 opcode 归属，把该 `GET_ITER` 当成「三元作 for 的迭代器」（`merge_context='iter'`、`value_target='__iter_target__'`），汇合块被三元吞并；生成层 `_generate_ternary` 又把该 `MAKE_FUNCTION` 当成「三元作装饰器/默认值/注解的 FunctionDef」，产出 `@(ternary) def <target>`，并把宿主容器赋值吞掉。
- 判据（I.4 白名单：块内非噪音指令序 + `_stack_effect` 净值 + 代码常量编译器合成名）：
  - 分析层新增 `_mb_ternary_is_tos(target_instr)`：从汇合块起点按栈净值累加（起点记 0，即三元结果占栈顶），目标指令之前净值 == 0 ⇔ 目标直接作用于三元结果；净值 > 0 ⇔ 目标之前已压入兄弟子表达式的中间值。`GET_ITER/GET_AITER` 分支加该门。
  - 生成层 `MAKE_FUNCTION` 分支加 `not self._const_code_is_async_comprehension(_code_obj)` 守卫：推导式代码对象（`<dictcomp>/<listcomp>/<setcomp>/<genexpr>`）的 `MAKE_FUNCTION` 不承载三元。
- 依据：CPython 3.11 求值顺序——同一表达式内先求值的子项留在栈上，后求值的兄弟子项在其上层构造；只有栈净值归零处才是本三元值的消费者。
- 归约：分析层只加否决门（命中即 `continue`，不改扫描顺序、不新建区域、不改块归属）；生成层只放行推导式形态，放行后由下方 `initial_stack=[ternary]` 的容器重建路径统一归约 `BUILD_CONST_KEY_MAP/BUILD_MAP`。守卫不命中逐位落回旧路径（C3）。
- 落位：`core/cfg/region_analyzer.py` 的 `_mb_ternary_is_tos`（约 28718–28747 行）+ `GET_ITER/GET_AITER` 分支（约 28886–28898 行）；`core/cfg/region_ast_generator.py` 的 `_generate_ternary` MAKE_FUNCTION 分支（约 55728–55744 行）。
- 最小复现 `/tmp/mini16`（f1–f5：字典/集合字面量 + 三元项 + 兄弟 dictcomp/无推导式/推导式非 `.items()`）：修复前 f1 键值错位、f2/f4/f5 退化为裸表达式；仅分析层门后 f1 退化为伪装饰器函数；两处齐备后 **f1–f5 全部与源码语义一致**。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**；REAL46-045 仍 31 diffs，但 `/tmp/dump45b.py` 按维度统计为 `{'R7': 31}`——**不含任何 code-object 结构维度**，残差只剩运行期 trace 维度（`cmd_selfcheck` 的 `res = compare_pyc(...)` 调用被吞，`MISSING root/c28:cmd_selfcheck/c19:<listcomp>`） |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `same=19 diff=5`，与前两轮的 5 处改进逐项同文；`new4` vs `new5` **24/24 一致**，B225 零回归 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=24 failures=0` |

`prod7` 的 REAL46-045 第 168 行已恢复完整 11 键 dict 字面量（含 `'files_by_status': {c: len(v) for c, v in buckets.items()}`）。判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。`MAX_ITEMS=2000`，31 条非截断上限。

### rr-v5r30：try/finally 副本 ternary 预登记的循环变量复用误判（2026-10-26）

B226 独立成族：与 REAL46-045 的 31 条 R7 残差无关，是 `try: <前导语句>; <三元赋值>` + `finally:` 的**整臂蒸发**缺陷。

#### B226-V3R30 副本判定复用循环变量导致三元被误登记为「已生成」

- 现象：`try:` 体内的前导语句与三元赋值一起从产物消失，只剩 `try: pass` + `finally: <清理>`。最小复现 `/tmp/mini22` 修复前产物即 `try: pass`；`/tmp/mini21` 的 f1（try + 含三元项的 dict 赋值）与 f3（try + 纯三元赋值）同样蒸发，而 f2（try + 无三元 dict，带 `return`）与 f4（无 try）修复前后均正确 ⇒ 触发面恰为「try 体内三元 + finally」。
- 根因链：`filtered` 全局预标记与 `_generate_try_body` 内的「finally normal path 副本」预登记段都写成 `_sib = False` 后 `for _sib in children`，**复用循环变量**。循环未 `break` 结束时 `_sib` 残留为最后一个 child 对象（恒真值）⇒ 「存在 finally 结构副本」误判成立 ⇒ 该 ternary 的 id 进入 `_ids`（顶层 `if id(r) in _ids: continue` 跳过）且 `_generate_try_body` 把其全部块登记进 `generated_blocks` ⇒ 随后块走查 `if block in generated_blocks: continue`，try 臂整段 `continue` 成空 ⇒ 只余 `pass`。
- 判据（I.4 白名单：只读区域成员关系 + 块数事实，不读偏移数值/名字）：`_has_copy` 只在真正命中「等块数 sibling ternary 的 entry ∈ 本域 `finally_blocks`」时置真，与循环变量解耦。两处（顶层 `filtered` 预标记与 `_generate_try_body` 预登记）判据逐位同文。
- 依据：CPython 3.11 `try/finally` 把 finally body 复制两份（normal path + exception path），只有 `finally_blocks` 内存在**等块数**同构 sibling 时，try 侧那一份才是真副本；否则它本身就是唯一的表达式载体，必须由既有入口派发发射。
- 归约：仅把两处循环变量的复用改为独立布尔量，命中条件、注册集合、块归属逐位不变（C3）。
- 落位：`core/cfg/region_ast_generator.py` 顶层 `filtered` 预标记段（约 1962–1981 行）与 `_generate_try_body` 的预登记段（约 35382–35414 行）。同文件第 36381 行的第三处 `for _sib in region.children` 在循环体内即 `_ids.add(id(child)); break`，无复用缺陷，未改动。
- 最小复现 `/tmp/mini22`（`a = len(rows); rate = 1 if a else None; return rate` + `finally: shutil.rmtree(...)`）：修复后产物恢复 `try: a = len(rows); rate = 1 if a else None`；`/tmp/mini21` 的 f1/f3 同步恢复前导语句与三元赋值。两处修复后 `return <name>` 仍丢失，登记为下一族（`_b34c_finally_deferred_return` / `_b207_return_in_finally_stmts` 两条既有路径均未命中，`/tmp/mini24` 无 try 对照证明该丢失只在 try/finally 上下文）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**（REAL46-045 仍 31 diffs 全为 `{'R7': 31}`）；`prod7` / `prod8` / `prod9` 三次重生成逐字节相同 ⇒ B226 对 402 语料零影响，属独立族 |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `new5` vs `new6`、`new6` vs `new7` 均 **24/24 一致**；`old2` vs `new7` 仍 `same=19 diff=5`，5 处全为 rr-v5r27 已核对的改进 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=24 failures=0` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

### rr-v5r31：try/finally 体内三元赋值后的 `return <name>` 丢失（2026-10-26）

#### B227-V3R31 三元 merge 块残值穿越 finally 内联副本的延迟返回未归约

- 现象：`try: <前导语句>; x = <三元>; return x` + `finally: <含关键字实参的调用>` 中，三元赋值恢复后 `return x` 仍整条丢失（`/tmp/mini22` 修复前两轮产物只有 `rate = 1 if a else None`；`/tmp/mini21` 的 f1/f3 同形）。
- 根因链：CPython 3.11 把 `return x` 的返回值在 merge 块内压栈（`STORE_FAST x; LOAD_FAST x`），穿越 finally 内联副本（normal path 副本含 `LOAD_GLOBAL/LOAD_ATTR/LOAD_FAST/LOAD_CONST/KW_NAMES/PRECALL/CALL/POP_TOP`），由副本末尾 `RETURN_VALUE` 消费。
  - 该 merge 块已被 TernaryRegion 认领，块走查不再到达它，既有 `_b34c_finally_deferred_return` 因此从未被调用（探针 `/tmp/probe_b34c.py` 实测只对 `blk@0` 调用一次）。
  - 三元路径内的 Pattern A2 分支以「后继块 `RETURN_VALUE` 前缀无 `POP_TOP`」为前提；finally 内联副本必然带 `POP_TOP`（丢弃清理调用结果），故 A2 判据恒不命中。
  - 即便改走 `_b34c_finally_deferred_return`，其清理副本白名单 `_DEFERRED_RET_CLEANUP_OPS` 缺 `KW_NAMES`，链分类被判「含集外指令」而整体放弃。
- 判据（I.4 白名单：块内指令序 + 栈效应 + 归属台账 + 关键字实参名元组的**存在性**，不读偏移数值/名字）：
  1. `_DEFERRED_RET_CLEANUP_OPS` 补入 `KW_NAMES`——该指令只把常量索引登记给解释器，净栈效应 0、不产出用户语句。
  2. `_generate_ternary` 的 A2 残值分支在既有判据不命中后，委托 `_b34c_finally_deferred_return(region.merge_block, emit_prefix=False)`：判据链（try_blocks + has_finally + 块末栈深 1 + 唯一非异常后继链分类 + 清理副本 ⊆ 白名单且净效应 0）由该方法自身逐位判定。
  3. `emit_prefix=False` 是新增关键字参数：三元入口已把 merge 块前缀归约为宿主赋值，再发射一次会产出伪语句（实测 `/tmp/mini21` f1 多出 `report = {}`——`LOAD_CONST keys + BUILD_CONST_KEY_MAP` 丢失三元初值后的残形）。
- 依据：源级 `try: ...; x = ...; return x` + `finally: <cleanup>` 重编译后 CPython 在相同上下文重新产生「值压栈 + 副本 + RETURN 消费」，与原始字节码逐指令一致。
- 归约：三元侧只新增一次委托调用（返回 None 时逐位落回既有路径，C3）；`_b34c` 只加一个默认 True 的关键字参数，默认路径逐位不变；白名单只增一条净效应 0 指令。
- 落位：`core/cfg/region_ast_generator.py` `_DEFERRED_RET_CLEANUP_OPS`（约 72493–72506 行）、`_b34c_finally_deferred_return` 签名与前缀发射条件（约 13897–13899 / 14076 行）、`_generate_ternary` A2 残值分支（约 56840–56864 行）。
- 最小复现 `/tmp/mini22`（无 try 对照 `/tmp/mini24`）：修复后 f3 与源码逐行一致；`/tmp/mini21` f1–f4 全部与源码语义一致（f1 的 `report = {}` 伪语句消失）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**（`prod9` vs `prod10` 逐字节相同；REAL46-045 仍 31 diffs 全为 `{'R7': 31}`） |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `new7` vs `new8` **24/24 一致**（零回归）；`old2` vs `new8` 仍 `same=19 diff=5`，5 处全为 rr-v5r27 已核对的改进 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=24 failures=0` |
| 既有最小复现回归 | `/tmp/mini16`（B225）与 `/tmp/mini24`（无 try 对照）产物逐字节不变 |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。REAL46-045 残差的结构面已收敛到 `cmd_selfcheck` 内层 try 体语句丢失（下一族）。

### rr-v5r32：try 内嵌 for + 内层 try/except 的体语句丢失与续体错位（2026-10-26）

#### B228-V3R32 四处同族缺陷（分析层 2 处 + 生成层 2 处）

最小复现 `/tmp/mini25`（f1/f2/f3）与 `/tmp/mini26`（g1/g2/g3）：
`try:` 内嵌 `for`、`for` 体内再嵌 `try/except`（外层可再带 `finally`）时，内层 try 体语句蒸发为 `try: pass`、try 之后的续体语句被搬进 `except` 体。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 分析 | `_collect_finally_body_blocks`（约 14970–15035 行） | 副本登记判据 `is_try_exit_successor or block_in_any_range` 只要其一成立即登记。外层 try 块（B14@8）的后继恰是**同一保护跨度内**的内层 try 体块（B16@18，异常表条目 `{start:18,end:52,target:54,depth:1}` 的起始块）⇒ 被误登记为 finally 正常路径副本（`keep_count=7`）⇒ 生成层 `[B142]` 门（64688–64746 行）按台账成员整块抑制 ⇒ 内层 try 体语句全部蒸发 | 新增 `nested_ranges`：异常表里 target **不属于**本 finally handler 的跨度即内层嵌套结构的保护区间；块内任一指令落在这些区间内则跳过。只读异常表事实（I.4 白名单），不新增区域、不改归约次序 |
| ② | 生成 | `_loop_collect_child_regions`（11221 起） | 按 `header.predecessors` 的**集合遍历序**取首个含 `GET_ITER`/`GET_AITER` 的前驱当 `iter_setup_block`。`try: for ...: try: <体>` 中回边块（实测 @152 = `hits = [r for r in res if not r.success]` + `JUMP_BACKWARD`）先被取到 ⇒ `_loop_generate_body`（11116–11118 行）把它整块登记 `generated` 而不发射 | 迭代器设置块必是**进入 header 的前导块**（偏移 < header）；优先读分析层归约事实 `metadata['for_iter_setup']`（`_classify_loop_type` 产出），缺失时按 `sorted(predecessors, key=start_offset)` 扫描，与 `_classify_loop_type` 排序口径一致，从而与回边块解耦 |
| ③ | 分析 | Pattern C 段（10735–10820 行） | 把 POP_EXCEPT 之后、仍在 `try_blocks` 中的块整段判给 handler 臂。`try: try: <体> except: <臂> hits = [...] finally: ...` 中 `hits = [...]` 块（B7@102）既在 try 正常流可达集内、又经 handler 臂尾 POP_EXCEPT 可达 ⇒ 被搬进 except 体 | 新增 `_try_flow_reach`：从 try 体入口沿**正常边**（剔除异常边与 handler/finally 块）传播；两处 worklist 入队前 `if succ in _try_flow_reach: continue`。Pattern C 只认领「仅经 handler 退出边可达」的尾段（CPython 把 finally 体就地内联到 handler 臂的 return 路径上，该副本块不被 try 正常出口引用） |
| ④ | 生成 | `_generate_try` W13 嵌套重建（38951–38976 行） | 把 `try_ast['body']` **整段**下沉进内层 Try。合并形态（finally region 吸收配对 except）中 try 体语句只有前缀属内层 try 体，其余是内层 try 语句之后的续体 ⇒ 续体语句落进 except 体 | 分析层在 region 构造后（11662 行）登记 `metadata['merged_except_try_range'] = (except_try_start, except_try_end)`；`_generate_try_body` 按该上界在块循环内（35525 行前）登记 `_w13_inner_len` 并于返回前写入 `region._w13_inner_body_len`；W13 按切分位置拆 `_w13_inner` / `_w13_rest`，`try_ast['body'] = _w13_inner + _w13_rest`。未登记该事实的 region 逐位不变（C3） |

- 定位证据：
  - `/tmp/dbgreg.py`：外层 TryExceptRegion `entry=B14@8 try_blocks=[B14@8,B2@12,B3@14,B15@16,B9@152] finally_blocks=[B11@226,B12@274] finally_copy_blocks={146:3,178:9,18:7,126:5}`，内层 `TryExceptRegion entry=B16@18 try_blocks=[B16@18] has_finally=False`。
  - `/tmp/exctab.py`：异常表 `{start:18,end:52,target:54,depth:1}`（内层 try 体）与 `{start:8,end:16,target:226,depth:0}`（外层 finally）。
  - `/tmp/probe_blkadd.py`：`=== DISCARD BLK BasicBlock(9, offset=152-176, instrs=8)` + `=== ADD BLK ...`，栈帧含 `line 11117, in _loop_generate_body` 与 `line 7343, in _generate_loop`。
  - `/tmp/probe_exh.py`：修复前 `FINAL handler body = ['B3@70','B13@72','B14@76','B10@226','B15@126','B7@102']`（B7@102 即被误并入的续体），修复后为 `['B3@70','B13@72','B14@76']`。
  - `/tmp/probe_trynest.py`：修复前 `[TRY] entry@6 try_off=[6,126) try_blocks=[6,40,86,94,96,102] handlers=[] body=['Try'] finalbody=['Expr']`（handlers 被 W13 下沉、body 整段变内层 Try）。
- 最小复现读数：
  - `/tmp/mini25/out12.py`：f1/f2/f3 与源码逐行一致（仅文件头注释与空行差异）。演进：`out8.py` f2 内层 `try: pass` → `out10.py`（①修复后）恢复 `res = compile(...)` 但 `hits = [...]` 仍丢失 → `out11.py`（②修复后）f2 完整 → `out12.py` 全部正确。
  - `/tmp/mini26/out5.py`：g1/g2/g3 与源码语义一致（g1 恢复 `try: try: res = compile(...); hits = [r for r in res] except ...: res = None finally: shutil.rmtree(...) return hits`）。演进：`out.py`/`out2.py`/`out3.py` g1 的 except 体内错位四语句 → `out5.py` 全部正确。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**；REAL46-045 从 31 diffs 收敛到 **29 diffs 全为 `{'R7': 29}`**，`try: pass` 恢复为 `res = compare_pyc(pyc, _compile(mutated, tmp, 'mut.pyc'))` ⇒ B228 族在同一语料上同源生效 |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `new8` vs `new9`：22/24 逐字节一致，2 处差异**全为改进**——`logging/__init__` 两处 `try: pass` 恢复 `sys.stderr.write(...)` / `self.flush()`；`shutil` 三处 `try: pass` 恢复 `os.close(fd)` / `os.rmdir(path, dir_fd=dir_fd)` / `raise OSError(...)` |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=144 failures=0` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- `/tmp/mini27` 的 `pc2`：`try: a = int(x) except ValueError as e: print(e); return None else: return a finally: os.getcwd()` 中 `return None` 被替换为 `os.getcwd()`。`/tmp/dbgreg.py` 显示 `except_handlers=[('ValueError', ["'e'"], [B3@94, B12@96, B13@126, B14@134])]`，`B14@134` 是 else 臂 `return a` 的 finally 内联副本，被误并入 handler body 并覆盖 `return None`——else 臂 + finally 合并形态的独立根因。

### rr-v5r33：except 臂 `return None` 被 finally 内联副本覆盖（2026-10-26）

#### B229-V3R33 单点缺陷（生成层 1 处）

最小复现 `/tmp/mini27`（pc1/pc2/g1）：
`try: a = int(x)` + `except ValueError as e: print(e); return None` + `else: return a` + `finally: os.getcwd()` 中 `return None` 被替换为 `os.getcwd()`。pc1（无 as-var、无 else 臂）正确，g1 为 rr-v5r32 的回归对照。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成 | `_handler_arm_block_is_finally_copy` 的 `_b115_user_opcode_seq`（39567 起） | 旧判据把块内**所有** `LOAD_CONST None` 一律当框架簿记滤除。`except ValueError as e: print(e); return None` 臂块（B14@134 = `LOAD_GLOBAL os; LOAD_ATTR getcwd; PRECALL 0; CALL 0; POP_TOP; LOAD_CONST None; RETURN_VALUE`）剥帧后用户序列为 `[LOAD_GLOBAL, LOAD_ATTR, CALL]`，与本 region finally 异常副本体（B7@192 剥 `PUSH_EXC_INFO` 头与 `RERAISE` 尾后同为 `[LOAD_GLOBAL, LOAD_ATTR, CALL]`）**等长** ⇒ 严格前缀判据 `len(arm) > len(body)` 恒不命中 ⇒ 臂被降级为裸 Expr（finally 副本语句 `os.getcwd()` 泄漏进 except 体、`return None` 丢失） | `LOAD_CONST None` 的两种身份分开：紧跟 `STORE_*` 的是 except as-var 清理三元组（`LOAD_CONST None + STORE + DELETE`）的框架簿记；其余位置（尤其 `RETURN_VALUE` 之前）是 `return None` 的返回值装载，属臂自身终态 Return 的用户指令。只读块内指令序 + `_STORE_TARGET_OPS`（I.4 白名单），无名字/偏移/阈值判据 |

- 定位证据：
  - `/tmp/dbgblocks2.py`：`B14@134 = [LOAD_GLOBAL os; LOAD_ATTR getcwd; PRECALL 0; CALL 0; POP_TOP; LOAD_CONST None; RETURN_VALUE]`；`B7@192 = [PUSH_EXC_INFO; LOAD_GLOBAL os; LOAD_ATTR getcwd; PRECALL 0; CALL 0; POP_TOP; RERAISE 0]`（finally 异常副本体）。
  - `/tmp/dbgreg.py`：`except_handlers=[('ValueError', ["'e'"], [B3@94, B12@96, B13@126, B14@134])]`、`finally_copy_blocks={36:0,134:0}`、`metadata['merged_except_try_range']=(4,34)`。
  - `/tmp/probe_pc2.py`：修复前 `[HB] block=BasicBlock(14, offset=134-174, instrs=7) -> ['Expr']`（只发射 `os.getcwd()` 调用，`return None` 未出现）；`[CHAIN]` 为 else 臂 `return a` 的 finally 副本链（`B10@34 -> B11@36`）。
- 最小复现读数：
  - `/tmp/mini27/out0.py`（B228 后、本族前）：pc1 正确、pc2 的 `return None` 被替换为 `os.getcwd()`、g1 错乱。
  - `out1.py`（Pattern C 修复后）g1 正确但 `hits = [...]` 被搬进内层 try 体；`out2.py`（W13 切分修复后）g1 完全正确、pc2 仍错。
  - `/tmp/mini27/out3.py`（本族修复后）：pc1/pc2/g1 全部与源码语义一致（pc2 恢复 `except ValueError as e: print(e); return None` + `else: return a` + `finally: os.getcwd()`）。本轮用当前工作树重生成 `/tmp/mini27/recheck.py` 逐字节复核一致。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**；REAL46-045 仍 **29 diffs 全为 `{'R7': 29}`**；`prod13` vs `prod12` 七条逐字节相同 ⇒ 本族对 402 语料零影响，属独立族 |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `new10` vs `new11` **24/24 逐字节一致** ⇒ 零回归 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge` 的 `merge point` 判定、`test_BOUNDARY_02_large_function` 的「原始源码语法无效」） |
| fuzz | `total=150 failures=0 stopped=time_budget` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 残差收敛

REAL46-045 的 29 diffs 全为 `$.metadata.code.co_consts.v[...]`，形态 `original: "str"` vs `product: "'str'"`：`from __future__ import annotations` 下注解在 `co_consts` 存为字符串，而产物把注解渲染为裸名字。已定位全部发射点（`core/cfg/code_generator.py` 的 `_arg_with_annotation`、`_render_pos_arg`、kwonly 分支、`_generate_ann_assign_dict`、`_generate_ann_assign`、`_generate_function_def_dict` 的 `returns`），登记为下一族「注解字符串化」。

### rr-v5r34：PEP 563 注解字符串化（2026-10-26）

#### B230-V3R34 单族缺陷（生成层 8 处注解发射点 + 2 处入口）

最小复现 `/tmp/mini28/v.py`：

```python
from __future__ import annotations


def f(x: str, y: int = 3) -> str | None:
    z: dict[str, int] = {}
    return None
```

修复前产物 `def f(x: 'str', y: 'int'=3) -> 'str | None':`——注解被 `repr` 加了一层引号；修复后 `def f(x: str, y: int=3) -> str | None:`（与源码一致）。

- 根因链：`from __future__ import annotations`（PEP 563，`__future__.annotations.compiler_flag = 0x1000000`）生效时，CPython 在**编译期**把注解表达式字符串化后存入 `co_consts`（`x: str` → `'str'`；`x: 'str'` → `"'str'"`）。生成器把注解节点按普通表达式发射——`Constant` 分支走 `repr(value)`、`_generate_expression` 对字符串常量同样加引号——于是产物文本重编译后 `co_consts` 存为**类型对象/带引号文本**而非源码原文，触发 REAL46-045 的 29 处 `$.metadata.code.co_consts.v[...]` 差异。
- 判据（I.4 白名单：只读 `co_flags` 的 future 位 + 注解节点类型与值，不读模块名/文件名/偏移）：
  1. `CodeGenerator.__init__` 新增 `future_annotations` 开关，由调用方按 `co_flags & __future__.annotations.compiler_flag` 传入；默认 `False` ⇒ 未启用该 future 的模块逐位不变（C3）。
  2. 新增 `_annotation_raw_text`：future 生效且注解节点是**字符串常量**时返回该原文；否则返回 `None`，调用点逐位落回既有分支。
  3. 8 处注解发射点加「原文优先」分支：`_generate_function_def_dict` 的 `returns`、`_generate_arguments_dict` 的 `_arg_with_annotation` / `_render_pos_arg` / kwonly、`_generate_ann_assign_dict`、`_generate_ann_assign`、`_generate_function_def` 的 `returns`、`_generate_arguments` 的 posonly / 普通位置 / kwonly。
- 依据：源码重编译时 CPython 在相同 future 位下重新产生「注解表达式 → 源码原文常量」，与原始字节码/常量表逐项一致。
- 归约：只新增一个默认 `False` 的构造参数与一个纯查询方法；所有调用点均为「原文存在则用、否则原路径」，无新增区域、无阈值、无名字判据。
- 落位：`core/cfg/code_generator.py` 模块级 `_MISSING` 哨兵（36–39 行）、`__init__`（52–62 行）、`_annotation_raw_text`（5761–5791 行）与上述 8 处发射点；入口 `pycdc.py`（93–99 行）、`core/cfg/__init__.py`（198–206 行）。

- 定位证据：
  - `/tmp/dump45c.py`：修复前 REAL46-045 的 29 条 diff **全为** `$.metadata.code.co_consts.v[...]`（`"str"` vs `"'str'"`、`"int"` vs `"'int'"`、`"dict"` vs `"'dict'"`、`"str | None"` vs `"'str | None'"`、`"list[tuple[str, str]]"` vs `"'list[tuple[str, str]]'"`）；修复后降至 4 条（`v[25].code_sha`、`v[26].code_sha`、`v[26].consts_len` 43 vs 42、`v[27].code_sha`）。
  - `/tmp/flagtest.py`：future 位 `0x1000000` 写入模块及全部嵌套 code object（模块 `co_flags=0x1000000`、`f=0x1000003`、`g=0x1000013`）；模块 `co_consts` 含 `('annotations',)` 与注解原文 `'str'`，函数注解元组为 `('x', 'str', 'return', 'str')` ⇒ 确认注解原文即 `co_consts` 元素。
- 最小复现读数：
  - `/tmp/mini28/out.py`（修复前）：`def f(x: 'str', y: 'int'=3) -> 'str | None':`。
  - `/tmp/mini28/out2.py`（本族修复后）：`def f(x: str, y: int=3) -> str | None:`。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**；REAL46-045 由 29 diffs 收敛到 **4 diffs**（3 条 `code_sha` + 1 条 `consts_len`），`co_consts` 全部对齐 |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `new11` vs `new12` **24/24 逐字节一致** ⇒ 零回归 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=148 failures=0 stopped=time_budget` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- REAL46-045 剩余 4 条 diff 全在 `cmd_batch` 的 code object 上：`/tmp/cmpconsts.py` 实测产物 `co_consts` 43→42，丢失 `'%Y-%m-%dT%H:%M:%S'` 且 `<dictcomp>` code 常量位置前移（最小复现 `/tmp/mini30/out.py` 第 31 行 `report = {'generated_at': round, 'elapsed_sec': time.time()(t0, 1), ...}`）。登记为 **B231**，根因在下节定位。
- `/tmp/mini28/out2.py` 中 `z: dict[str, int] = {}` 的 AnnAssign 注解仍丢失（发射为 `z = {}`）：本族只覆盖了函数签名注解，AnnAssign 的注解节点在 `_build_function_def` 之外的槽位仍未写入，需另查。

### rr-v5r35：三元 cond 预加载的二元运算未折叠（2026-10-26）

#### B231-V3R35 单点缺陷（生成层 1 处）

最小复现 `/tmp/mini30`（从 `scripts/pyc_verify.py` 的 `cmd_batch` 抽出）：`BUILD_CONST_KEY_MAP` 多键字典中首个/次个 value 是纯 LOAD 表达式（`time.strftime(...)`、`round(time.time() - t0, 1)`）、后续 value 含三元与推导式时，产物把前两个值渲染为 `round` 与 `time.time()(t0, 1)`。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成 | `_generate_ternary` 的 cond_block 预加载折叠链（55526 起） | 折叠链只有 `LOAD_ATTR`/`UNARY_*`/`BUILD_*`/`BUILD_SLICE`/`BINARY_SUBSCR`/`PRECALL`/`CALL` 分支，**缺二元运算**。`round(time.time() - t0, 1)` 的 `BINARY_OP` 不折叠 ⇒ 预加载项停在操作数粒度 `[round, time.time(), t0, 1]` ⇒ 紧随的 `CALL 2` 弹「`1`, `t0`」作实参、把 `time.time()` 当 func，产出 `time.time()(t0, 1)`，并把 `round` 留作下一个字典值；`BUILD_CONST_KEY_MAP 11` 因此按 11 个错位值配对，首个键 `generated_at` 拿到 `round`、`time.strftime(...)` 整段蒸发（`co_consts` 因此少 1 项） | 新增 `BINARY_OP`/`COMPARE_OP`/`IS_OP`/`CONTAINS_OP` 折叠分支：弹「右项, 左项」两项、按源序拼成一个分组指令列表、追加运算符指令，与既有 `BINARY_SUBSCR` 分支完全同形（同为「弹 2 压 1」）。判据只读操作码类别与预加载项数（I.4 白名单），无名字/偏移/阈值 |

- 定位证据：
  - `/tmp/probe_blocks31.py`：`cmd_batch` 中 B12@750–1138 即三元 condition_block（末条为条件跳转），前两个值的指令（@888–986）**就在该 cond_block 的 preload 区**，而非 merge 块 ⇒ 排除 `_extract_dict_prefix_values` 路径（探针 `/tmp/probe_dict31.py` 实测该函数与 `_try_build_ternary_chained_container` 在本例中均未被调用）。
  - `/tmp/probe_stack.py`：`CALL` @986 弹 `BinOp` + `Const:1`，把 `Name:round` 留栈作下一 `CALL` 的 func ⇒ `round` 被 `time.time()` 错位消费，与折叠链缺 `BINARY_OP` 的预测一致。
  - `/tmp/cmpconsts.py`：产物 `cmd_batch` 的 `co_consts` 43→42（丢 `'%Y-%m-%dT%H:%M:%S'`）——错位配对的直接后果。
  - `/tmp/mini29/v.py`：同一 dict 去掉三元后完全正确 ⇒ 缺陷只在「cond preload 折叠」路径，不在 `BUILD_CONST_KEY_MAP` 常规路径。
- 最小复现读数：`/tmp/mini30/out.py`（修复前）第 31 行 `report = {'generated_at': round, 'elapsed_sec': time.time()(t0, 1), ...}`；`/tmp/mini30/out_fix.py`（修复后）第 31 行 `report = {'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'elapsed_sec': round(time.time() - t0, 1), 'interpreter': sys.version.split()[0], ...}`（11 键 11 值全部正确）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**；REAL46-045 由 4 diffs 收敛到 **3 diffs**（`cmd_single` / `cmd_batch` / `cmd_compare` 三个嵌套 code object 的 `code_sha`），`cmd_batch` 的 `co_consts` 长度已对齐 |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `new12` vs `new13` **24/24 逐字节一致** ⇒ 零回归 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=145 failures=0 stopped=time_budget` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- `/tmp/disdiff.py cmd_batch`：产物在循环体末尾多发射一条 `JUMP_BACKWARD`（即把 `elif i % 25 == 0:` 渲染成 `if ...: print; else: continue`），使 `cmd_batch` 整体偏移 +2 字节。源码无 `else`，该 `continue` 属伪语句。登记为 **B232**。
- `/tmp/disdiff.py cmd_single`：`cmd_single` 产物比原始多 28 字节，首处差异在 `@832 JUMP_FORWARD` vs `RETURN_VALUE`（return-in-finally/try 尾形态）。
- `/tmp/disdiff.py cmd_compare`：`co_consts` 顺序差异（原 `('tuple','')`/`('code','')` vs 产 `('code','')`）+ `<genexpr>` 少常量 `'%-14s'`（格式化模板在推导式中丢失）。

### rr-v5r36：循环体末条 if/elif 的假边纯回边块被误认成 else 臂（2026-10-26）

#### B232-V3R36 单点缺陷（生成层 1 处）

最小复现 `/tmp/mini32`（从 `scripts/pyc_verify.py` 的 `cmd_batch` 抽出）：`for ...: if cond: ... elif i % 25 == 0: ...` 中，源码没有 `else`，产物给每个 `elif` 臂补出一条伪 `else: continue`。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成 | `_if_generate_normal` 的 merge_block 假臂认领段（27439 起，R40-A2） | 认领条件是 `not _ft3_shared_merge and (not _mb_meaningful or _mb_then_escapes)`，其中 `not _mb_meaningful`（merge 块剥掉噪声/跳转后为空）单独即可放行，把「`elif` 假边直落的纯 `JUMP_BACKWARD`→循环头块」改认成 `else_blocks`；该块本是循环的自然迭代回边 ⇒ 产物多出伪 `else: continue` ⇒ 重编译多一条 `JUMP_BACKWARD` | 认领门追加 `not self._if_false_path_is_loop_iteration(region)`：该谓词（本核 :29876）只读三件结构事实（① 条件入口的非 then 后继；② 该后继不在 then_blocks/region.blocks；③ 该后继是纯 `JUMP_BACKWARD`→循环头），已在 `[R3-Continue]` 补发段（:27346）与 `_process_if_blocks` 的 CONTINUE 角色抑制共用。谓词为真时跳过认领，merge 角色留给父循环按自然回边次序发射 |

- 定位证据：
  - `/tmp/mini32/v.py`：`v1`/`v2`/`v3` 三个函数全部多出伪 `else: continue`。
  - `/tmp/probe_if32.py`：`v1` 的块结构 `B2@34 FOR_ITER`（header）、`B3`（if 条件）、`B4`（then 臂 + `JUMP_BACKWARD`）、`B5`（elif 条件）、`B6`（elif 臂）、`B7@140`（仅 `JUMP_BACKWARD`）、`B8@142`（`LOAD_CONST None; RETURN_VALUE`）；区域 `IfRegion entry=5 cond=5 then=[6] else=[] merge=7 blocks=[5,6]`。
  - `/tmp/probe_b232.py`（本轮新建）：对 `IfRegion@entry=5` 调 `_if_false_path_is_loop_iteration` 返回 **True**，对 `IfRegion@entry=3`（外层 if，假边是 elif 条件块）返回 **False** ⇒ 谓词恰好只命中 `elif` 臂末条形态，不影响外层。
  - `/tmp/mini33/v.py` 对照实验（`a` 无 else / `b` 显式 `else: continue` / `c` then 内显式 continue + 后续语句 / `d` elif）：`d` 修复前同样多一条伪 `else: continue`，修复后消失；`b` 的 else 臂是真实 `else_blocks`，谓词返回 False，不受影响。
  - `/tmp/disdiff2.py cmd_batch`（修复前 `prod15`）：产物 `@646 JUMP_BACKWARD 152` → `@648 JUMP_BACKWARD 152`（多一条）→ `@650 NOP`；修复后 `cmd_batch` 的 `co_code` 与原始**逐字节相同**。
- 最小复现读数：`/tmp/mini32/out.py`（修复前）`v1`/`v2`/`v3` 均带 `else: continue`；`/tmp/mini32/out_fix.py`（修复后）三条 arms 全部无伪 else，`/tmp/cmpcodes.py` 逐函数比对 `v1` 35 条 / `v2` 50 条 / `v3` 85 条指令与 `co_consts` **全部 MATCH**；`/tmp/mini33/out_fix.py` 的 `a`/`b`/`c`/`d` 四函数 17/18/23/26 条指令 **全部 MATCH**。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**；REAL46-045 由 3 diffs 收敛到 **2 diffs**（仅 `v[25]` = `cmd_single`、`v[27]` = `cmd_compare` 的 `code_sha`），`cmd_batch` 的 `co_code` 已逐字节对齐 |
| A/B `/tmp/ab`（24 stdlib pyc，HEAD `fe4996ae` vs 当前工作树） | `new13` vs `new14` 文本 15 同 / 9 异；9 处全为 `else: continue` 消失（email__utils / enum / http__client / string 共 5 处伪 else 被删）或尾 `continue` 归位（dataclasses / dis / logging / pathlib / shutil）。`/tmp/ab/bytecmp.py` 比对嵌套 code object 的 `co_code`/`co_consts` 问题集：**零新增**，且 `email__utils` 的 `_check_parenthesis`（154 vs 156）**消失** ⇒ 净 -1 处 CODE 差异 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=145 failures=0 stopped=time_budget` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- `/tmp/cmpnested45.py`：REAL46-045 剩两条 diff——`cmd_single`（838 vs 866 字节，首处 `@832 JUMP_FORWARD 836` vs `RETURN_VALUE`，return-in-finally/try 尾形态，登记 **B233**）与 `cmd_compare` + `<genexpr>`（1986 vs 1994 / 162 vs 156，`co_consts` 顺序差异 + 推导式丢 `'%-14s'` 模板，登记 **B234**）。
- `/tmp/mini28/out2.py` 中 `z: dict[str, int] = {}` 的 AnnAssign 注解仍丢失（发射为 `z = {}`）。

### rr-v5r37：三元后继三元被升级成伪 if（2026-10-26）

#### B233-V3R37 单点缺陷（生成层 1 处）

最小复现 `/tmp/mini34/v.py::g1`（从 `scripts/pyc_verify.py` 的 `cmd_single` 抽出）：`print('[single] status=%s ...' % (...))` 紧跟 `return 0 if row['status'] == 'success' else 1` 时，产物渲染为伪 `if row['status'] == 'success': return 0` + 重复的 `return 0 if row['status'] == 'success' else 1`（重复条件 + 重复 then 臂）。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成 | `_emit_post_extra_with_if_upgrade` 的 `_r59_claimable` 让位集合（59033 起） | 让位集合为 `(IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, AssertRegion, BoolOpRegion)`，**缺 `TernaryRegion`**。外层 TernaryRegion（`entry=B1 merge=B4`）的 `post_extra` 只有 `Expr(Compare)`——即内层三元（`entry=B4 merge=B7`）自身的条件表达式；merge 块 B4 尾部的 `POP_JUMP_FORWARD_IF_FALSE` 属于内层三元，不是「三元消费语句之后的独立语句」。集合缺类 ⇒ 该 `Expr(Compare)` 被升级为伪 If，随后内层 TernaryRegion 又发射完整 `return 0 if ... else 1` | 让位集合补入 `TernaryRegion`；命中即与既有 7 类同一收口（`results.extend(post_extra[:-1]); return`），末项条件表达式由内层三元自身重建后发射。判据只读「merge_block 是否为另一未生成区域的 entry」这一区域身份事实（I.4 白名单），不涉及名字/偏移/阈值；既有 7 类让位形态逐位不变（C3） |

- 定位证据：
  - `/tmp/probe_regions.py`：`g1` 的块 `B1@0-168`（三条 print 前导 + 内层三元条件，末条 `POP_JUMP_FORWARD_IF_NOT_NONE`）、`B2@170-172`、`B3@174-196`、`B4@200-244`（`BUILD_TUPLE; BINARY_OP; PRECALL; CALL; POP_TOP` 后接 `LOAD_FAST; LOAD_CONST; BINARY_SUBSCR; LOAD_CONST; COMPARE_OP; POP_JUMP_FORWARD_IF_FALSE`）、`B5@246-248`、`B6@250`、`B7@252`（`RETURN_VALUE`）；区域 `TernaryRegion entry=B1 merge=B4` 与 `TernaryRegion entry=B4 merge=B7`。
  - `/tmp/probe_emit34b.py`：外层三元返回 `('TERN', 1, 4, ['Expr','Expr','Expr','If'])`，内层返回 `('TERN', 4, 7, ['Return'])` ⇒ 伪 If 由外层三元的第 4 项给出。
  - `/tmp/probe_bs34.py`：`BS B5 -> ['Return']   [_generate_region.6082(); _generate_ternary.54655(); _emit_post_extra_with_if_upgrade.59095(); ]` ⇒ 伪 If 的 then 臂就是 `_emit_post_extra_with_if_upgrade` 合成的 `_generate_block_statements(B5)`。
  - `/tmp/probe_postextra34b.py`：`POST_EXTRA entry=1 merge=4 items=['Expr(Compare)']` ⇒ `post_extra` 只有内层三元的条件，无独立语句。
- 最小复现读数：`/tmp/mini34/out_fix.py`（修复后）`g1` 恢复为三条 `print(...)` + `return 0 if row['status'] == 'success' else 1`，`/tmp/cmpcodes.py` 逐函数比对 `g1` 58 条 / `g2` 11 条 / `g3` 16 条指令与 `co_consts` **全部 MATCH**；`/tmp/mini10/out_r37.py` 的 `f1`（同一 `cmd_single` 形态）同步恢复。
- 未受影响对照：`/tmp/mini34/wout_fix.py` 与修复前 `wout.py` **逐字节相同**（`h1` 的伪调用形态属另一根因，见残差 B235；`h2`/`h3` 仍 MATCH）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | 维持 **6 EQUAL / 1 DIFFERENT**；REAL46-045 由 2 diffs 收敛到 **1 diff**——`v[25]` = `cmd_single` 的 `code_sha` **已消失**（该嵌套 code object 逐字节对齐），只剩 `v[27]` = `cmd_compare` |
| A/B `/tmp/ab`（24 stdlib pyc） | `new14` vs `new15` 文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 的 `co_code`/`co_consts` 问题集 `diff -u` **零差异** ⇒ 零新增、零副作用 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致 |
| fuzz | `total=146 failures=0 stopped=time_budget` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- REAL46-045 仅剩 `v[27]` = `cmd_compare`：1986 vs 1994 字节，`co_consts` 顺序差异 + 嵌套 `<genexpr>` 丢 `'%-14s'` 模板，登记 **B234**。
- `/tmp/mini34/w.py::h1`（及 `/tmp/mini10` 的 `f2`/`f3`）：`print('%s' % ('-' if ... else 'y'))` 的 merge 消费表达式重建错误——产物为 `(row['x'] is None)('-' % 'y')`（三元退化为裸条件、`print` 与 `'%s'` 前导丢失），登记 **B235**。
- `/tmp/mini28/out2.py` 中 `z: dict[str, int] = {}` 的 AnnAssign 注解仍丢失（发射为 `z = {}`）。

### rr-v5r38：三元 cond 前导区多目标赋值丢目标（B234 连续 STORE 段整组归约）（2026-10-26）

#### B234-V3R38 单点缺陷（生成层 1 处）

最小复现 `/tmp/mini35/v.py::g2`（从 `scripts/pyc_verify.py` 的 `cmd_compare` 抽出）：`da, db = before['units_success'], after['units_success']` 与 `ta, tb = before['units_total'], after['units_total']` 位于某 TernaryRegion 的 `condition_block` 前导区，产物只保留 `db`/`tb`，`da`/`ta` 整条目标丢失并退化为未定义全局。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成 | `_build_statements_from_instructions` 的 STORE 分支（原 41399 行 `_build_store_statement` 调用前） | CPython 3.11 对纯名字多目标 `a, b = e1, e2` 生成 `LOAD e1; LOAD e2; STORE b; STORE a`（**反源序连续 STORE，无 SWAP/UNPACK/COPY**）。本方法逐 STORE 独立重建：首 STORE `db` 把整段值指令当单一 RHS、只弹栈顶 ⇒ `Assign(['db'] = Subscript)`；随后 `da` 因 `_stmt_instrs` 已清空而无值可配 ⇒ `_build_store_statement` 返回 `None` ⇒ 整条目标静默丢弃。既有 `[B223-V3R26]` 连续 STORE 段整组归约只覆盖 `for_iter_setup` 前导区，未覆盖三元 condition 前导区；`Pattern SIG2` 只覆盖块首形态，该块走 `_build_statements_from_instructions` | 在 STORE 分支前识别 N>=2 连续简单名 STORE 段（`STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF`），并要求值段无 `COPY/SWAP/UNPACK_SEQUENCE/UNPACK_EX`（排除链式赋值/cell 交换/元组解包）且重建后栈深 >= N；整组归约为单一 `Assign(Tuple(源序目标), Tuple(压栈序值))`，被吸并次级 STORE 经 `_bsi_skip_until` 跳过，不再走逐 STORE 路径。判据只读块内操作码序 + 值栈净效应（I.4 白名单），不涉及名字/偏移/阈值；任一守卫不命中即逐位落回旧路径（C3） |

- 定位证据：
  - `/tmp/probe_blocks35.py`：`cmd_compare` 的 `B30 @1582-1976` 指令序列为 `LOAD_FAST before; LOAD_CONST 'units_success'; BINARY_SUBSCR; LOAD_FAST after; LOAD_CONST 'units_success'; BINARY_SUBSCR; STORE_FAST db; STORE_FAST da; ...; STORE_FAST tb; STORE_FAST ta; LOAD_GLOBAL print; ...` ⇒ 反源序连续 STORE、无 SWAP。
  - `/tmp/probe_skip35.py`：`TERN cond=1582 entry=1582 skip=None` ⇒ 该块正是某 TernaryRegion 的 condition/entry 块，无 `skip_store_targets` 兜底。
  - `/tmp/probe_caller35.py`（`instrs[-1].offset == 1610` 时打印调用栈）：`region_ast_generator.py:6082 in _generate_region` → `:54149 in _generate_ternary` → `:41399 in _build_statements_from_instructions` → `_build_store_statement`。
  - `/tmp/probe_dispatch35b.py`（修复前）：`BS_STORE block=None instrs=1582..1610 -> Assign`、`instrs=1612..1612 -> None`、`instrs=1614..1642 -> Assign`、`instrs=1644..1644 -> None` ⇒ 逐 STORE 重建、第二个 STORE 拿到空值段返回 `None`。
  - `/tmp/probe_stmts35.py`（修复后）：`cmd_compare` B30@1582 → `stmts: 8`：`Assign(["Tuple(['da', 'db'])"] = Tuple)`、`Assign(["Tuple(['ta', 'tb'])"] = Tuple)`、`Expr`、`Expr`、`Assign(['regressed'] = Call)`、`Assign(['improved'] = Call)`、`Expr`、`Expr`；`/tmp/mini35/v.pyc g2` B1@0 → `Assign(["Tuple(['da', 'db'])"] = Tuple)`、`Assign(["Tuple(['ta', 'tb'])"] = Tuple)`、`Expr`、`Return`。
  - `/tmp/trace_body35b.py`：`g1` 的 `_generate_block_statements_body` 最高行号 66848（`Pattern C2` 无 SWAP 解包路径），`_ns_after` 含 `POP_TOP`/`LOAD_GLOBAL` ⇒ `_ns_has_expr_no_ret` 真 ⇒ `_ns_n = 0` 降级，最终仍落 `_build_statements_from_instructions` ⇒ 同一归约在块级路径上也生效。
- 最小复现读数：`/tmp/mini35/out_fix.py` 的 `g2`/`g3`/`g4` 用 `/tmp/cmpcodes.py` 逐指令 + `co_consts` 比对 **全部 MATCH**（27/13/13 条）；`g1` 仍 `DIFF orig=17 prod=11`（尾随 `print(da, db)` 蒸发，属块级 Pattern C2 降级后未把尾随语句交回通用重建的另根因，登记残差）。
- 未受影响对照：`/tmp/ab/bytecmp.py` 对 24 个 stdlib 模块的 `co_code`/`co_consts` 问题集 `diff -u` **零差异**（`new16` vs `new15`）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | **7/7 全 EQUAL**（`/tmp/judge5.py /tmp/rep46/prod18` → `REAL46-039/040/041/042/044/045/046` 全部 `EQUAL 0 []`）；REAL46-045 由 1 diff 收敛到 **0 diff** |
| REAL46-045 嵌套 code object | `/tmp/cmpnested45.py` 仅剩 `module/cmd_compare/<genexpr>`（`162 vs 156`，`co_consts` 少 `('str', '%-14s')`，`first diff @10: FOR_ITER 158 vs 152`）；`cmd_compare` 本体的 `@1582` 整段错位已消失 |
| A/B `/tmp/ab`（24 stdlib pyc） | `new16` vs `new15` 文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 问题集 `diff -u` **零差异** ⇒ 零新增、零副作用 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed`，失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`） |
| fuzz | `total=146 failures=0 stopped=time_budget` |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- `cmd_compare` 的嵌套 `<genexpr>` 丢 `'%-14s'` 模板：`print(' ' * 16 + ''.join('%-14s' % b for b in CATEGORIES))`，`co_consts` 少 `('str', '%-14s')`，`FOR_ITER 158` vs `152`——与 B234 同属 `cmd_compare`，另立 **B236**。
- `/tmp/mini35/v.py::g1`：多目标赋值后紧跟 `print(da, db)` 时 `print` 整段丢失（`orig=17 prod=11`，prod 只剩 `LOAD_CONST None; RETURN_VALUE`）——块级 `Pattern C2` 无 SWAP 解包路径降级（`_ns_n = 0`）后未把尾随语句交回通用重建。
- `/tmp/mini34/w.py::h1` 与 `/tmp/mini10` 的 `f2`/`f3`：`print('%s' % ('-' if ... else 'y'))` 的 merge 消费表达式重建错误，产物为 `(row['x'] is None)('-' % 'y')`，登记 **B235**。
- `/tmp/mini28/out2.py` 中 `z: dict[str, int] = {}` 的 AnnAssign 注解仍丢失（发射为 `z = {}`）。
- `/tmp/mini30/out_fix.py` 的 `newline="""\n"""` 三引号渲染。

### rr-v5r39：推导式元素位三元的「前导压栈项 + 汇合点后缀」丢失（2026-10-26）

#### B236-V3R39 单点缺陷（生成层 1 处）

最小复现 `/tmp/mini36/v.py::h1`（从 `scripts/pyc_verify.py` 的 `cmd_compare` 抽出）与 `/tmp/mini37/v.py::k1/k4/k5`：元素位 `F % (A if c else B)` 的推导式产物只剩裸三元，格式串常量与尾部 `BINARY_OP %` 整段消失（`<genexpr>` 162 vs 156 字节，`co_consts` 少 `('str','%-14s')`，`FOR_ITER 158` vs `152`）。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成 | `ComprehensionGenerator._detect_comp_ternary` 末端（`core/cfg/comprehension_generator.py` 3066 起） | CPython 3.11 对元素位 `F % (A if c else B)` 发射：cond 块先 `LOAD_CONST F` 再求条件、`merge` 块用 `BINARY_OP %` 消费三元值。本方法的 `cond_instrs` 从目标存储之后切起，`reconstruct` 只返回栈顶（条件）⇒ 前缀 `F` 静默丢弃；merge 块后缀除 walrus 外从不重建 ⇒ 尾部运算整段丢失 | 新增「前导压栈项 + 汇合点后缀」整组归约： condición 走单段整窗重建通道 ∧ `cond_instrs` 重建后非 PUSH_NULL 栈深 >= 2 ∧ merge 偏移到追加点之间后缀窗非空 ∧ 追加点非 `MAP_ADD`（dict 推导式另有 key/value 专用通道）时，以前导项 + 三元值作初栈逐条处理后缀指令，栈上唯一非 PUSH_NULL 项即整组结果。判据只读同层指令 opcode 与栈净效应（I.4 白名单）；任一守卫不命中即逐字返回原 IfExp（C3） |

- 定位证据：
  - `/tmp/probe_gen36.py`：`cmd_compare` 的 `<genexpr>`（162 字节）块结构 `B4@12-42`（`STORE_FAST b; LOAD_CONST '%-14s'; LOAD_DEREF; ...; POP_JUMP_FORWARD_IF_TRUE 48`）、`B5@44-46`、`B6@48-58`、`B7@60-112`、`B8@114-142`、`B9@146-156`（`BINARY_OP %; YIELD_VALUE; ...`）；区域为外层 `TernaryRegion cond=B4 merge=B9` + 内层 `TernaryRegion cond=B6 merge=B9`。
  - `/tmp/dumpgen.py`（本题 pyc vs 产物）：原始 `<genexpr>` `consts=('%-14s','-','+%d',None)`、首指令 `14 LOAD_CONST '%-14s'`、merge 处 `146 BINARY_OP %`；产物 `consts=('-','+%d',None)`、无 `'%-14s'`、无 merge 处 `BINARY_OP`。
  - `/tmp/probe_gen36b.py`：直接对 `<genexpr>` code object 走 `RegionASTGenerator.generate()`，`_generate_ternary` 在整个 genexpr 内**未被调用**（0 条 LOG）⇒ 该元素表达式由 `ComprehensionGenerator` 路径重建，不是区域生成器路径。
  - `/tmp/dumpk7.py`：`k7`（`x and x or 'e'` 形态）无 `JUMP_FORWARD`，merge 点由 `JUMP_IF_TRUE_OR_POP 22` 给出 ⇒ `_merge_block_idx` 为 None，本族守卫不命中，残差另立 B237。
- 最小复现读数：
  - `/tmp/mini36b/out.py`（修复后）`h1`–`h5` 全部恢复 `''.join(('%-14s' % b for b in CATEGORIES))` 形态，`/tmp/cmpcodes.py` 指令条数 19/17/17/17/21 与原始**逐位相同**（仅剩 `LOAD_CONST <code object>` 的地址/文件名字段差异，非语义）。
  - `/tmp/mini37b/out.py`（修复后）`k1`/`k4`/`k5` 恢复 `'%s!' % (x if x else 'e')` / `'%-14s' % (...)` / `'<%s>' % (...)`；`/tmp/cmpnested37.py` 嵌套比对由 4 条 CODE-DIFF（k1/k4/k5/k7）收敛到 **1 条**（仅 `k7`，属 B237）。修复前同一路径为 `k1`/`k4`/`k5`/`k7` 四条全 DIFF（`/tmp/mini37c/out.py` 对照）。
  - `k2`（dict 推导式 key 位三元）与 `k3`（set 推导式）修复前后同形，`MAP_ADD` 守卫保证该通道不发生任何变化（C3）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | **7/7 全 EQUAL**；`/tmp/cmpnested45.py /tmp/rep46/prod19/REAL46-045.py` **零 CODE-DIFF 输出**（REAL46-045 的嵌套 code object 已全部逐字节对齐） |
| A/B `/tmp/ab`（24 stdlib pyc） | `new17` vs `new16` 文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 问题集 `diff -u` **零差异**（`diff exit=0`）⇒ 零新增、零副作用 |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed in 3.70s`，失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`） |
| fuzz | `total=295 failures=0 stopped=time_budget`（120s） |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- 推导式元素位 **BoolOp**（`and`/`or`）整族尚未归约：`/tmp/mini38/v.py` 的 `m1`（`[x and y or 'e' for x in xs]` → 产物 `[y if x else 'e' ...]`，当 `y` 为假值时语义错）、`m3`（`[x or y ...]` → `[y ...]`）、`m4`（`[x and y ...]` → `[y ...]`）、`m2`（带 `%s` 前导）、`m5`（含闭包细胞变量，另叠 `MAKE_CELL`/`COPY_FREE_VARS` 丢帧问题）；`/tmp/mini37/v.py::k7`（`x and x or 'e'` 的 `JUMP_IF_TRUE_OR_POP` 汇合点未被识别 ⇒ 退化为三元、重编译 `JUMP_FORWARD` 与原始不一致），统一登记 **B237**。
- 既有残差仍在：`/tmp/mini35/v.py::g1` 尾随 `print` 蒸发（Pattern C2 降级后未交回通用重建）、`print('%s' % (ternary))` merge 消费重建错误（B235）、AnnAssign 注解丢失、`newline="""\n"""` 三引号渲染。

### rr-v5r40：推导式元素位 and/or 短路丢左操作数（B237 keep-or-pop 归约）（2026-10-26）

最小复现 `/tmp/mini38/v.py`（5 个函数，均从 `scripts/pyc_verify.py` 的推导式元素表达式抽出）：`m1 = [x and y or 'e' for x in xs]`、`m2 = ['%s' % (x and y or 'e') for x in xs]`、`m3 = [x or y for x in xs]`、`m4 = [x and y for x in xs]`、`m5 = [x and y or 'e' if x else 'z' for x in xs]`；对照 `/tmp/mini37/v.py::k7`（`'%-14s' % (x and x or 'e')`）。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成 | `ExpressionReconstructor._process_instruction`（`core/cfg/ast_generator_v2.py`，`COPY` 分支前） | CPython 3.11 对「结果即表达式值」位置（推导式元素等）的 `A and B` / `A or B` 发射 `JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP`（短路时 A 自身即结果保留在栈上、不短路时弹出 A 取 B）。本方法无该指令分支 ⇒ A 静默留在栈上、B 压顶，`reconstruct` 取栈顶只返回 B ⇒ `[x or y ...]` 退化为 `[y ...]`、`[x and y ...]` 同形（语义错） | 新增 `_fold_boolop_keep_or_pop` 开关（默认 False ⇒ 既有全部调用路径逐位不变，只由推导式元素窗显式开启）+ 栈机建模：弹左操作数、与栈顶已挂 Pending 合并后压回 `BoolOpPending(op, left)`；`reconstruct` 末尾把 `(Pending, 右操作数)` 对合成单一 `BoolOp`，链式 `A or B or C` 逐级左折叠 |
| ② | 生成 | `ComprehensionGenerator._b237_kop_window`（新增，`core/cfg/comprehension_generator.py` 2755 起） | `A and B or C` 的融合形态 `<A>; POP_JUMP_FORWARD_IF_FALSE <C>; <B>; JUMP_IF_TRUE_OR_POP <merge>; <C>` 被既有三元通道当成普通分支跳转：真值区末的 keep-or-pop 只取栈顶 ⇒ 产出 `B if A else C`（B 为假时丢掉 C，语义错），前导压栈项 F 与 merge 后缀（如 `BINARY_OP %`）整段丢失 | 首个跳转为前向 IF_FALSE 型 ∧ 真值区终结于 `JUMP_IF_TRUE_OR_POP` ∧ 真值区内无其它条件/无条件前向跳转 ∧ 追加点非 `MAP_ADD` 时，条件区逐条压栈取栈顶为 A（其余为前导项 F）、真值区重建 B、假值区重建 C，合成 `BoolOp(or, [BoolOp(and, [A, B]), C])`；汇合点之后有后缀时以 `F... + [值]` 作初栈逐条处理后缀。所有判据只读同层指令 opcode 与跳转目标（I.4 白名单），不命中即返回 None 逐字回落既有三元通道（C3）。真值区/假值区内的同族形态递归走本方法（嵌套） |
| ③ | 生成 | `ComprehensionGenerator._detect_comp_ternary` 真值区重建段（3062 起） | 外层三元（`A if (B and C or D) else E`）的真值区自身含内层短路跳转时，`reconstruct(true_instrs)` 只按栈顶产出 ⇒ 内层 `and`/`or` 整段错位（`m5` 退化为 `'e' if x else 'z'`） | 真值区含跳转时先按 `_b237_kop_window`（窗口取 `all_instrs[true_start:false_start]`，让内层假值区与汇合点都在窗内）整组归约；判据不命中逐字回落原 `reconstruct` 通道 |

- 定位证据：
  - `/tmp/dumpbool.py`（原始 pyc 逐指令）：`m3` = `12 LOAD_FAST x; 14 JUMP_IF_TRUE_OR_POP 18; 16 LOAD_DEREF y; 18 LIST_APPEND`；`m4` = `12 LOAD_FAST x; 14 JUMP_IF_FALSE_OR_POP 18; 16 LOAD_DEREF y; 18 LIST_APPEND`；`m1` = `12 LOAD_FAST x; 14 POP_JUMP_FORWARD_IF_FALSE 20; 16 LOAD_DEREF y; 18 JUMP_IF_TRUE_OR_POP 22; 20 LOAD_CONST 'e'; 22 LIST_APPEND`；`m2` 同形但前置 `12 LOAD_CONST '%s'`、merge 后 `24 BINARY_OP %`；`m5` = 外层 `14 POP_JUMP_FORWARD_IF_FALSE 28` + 内层 `18 POP_JUMP_FORWARD_IF_FALSE 24` + `22 JUMP_IF_TRUE_OR_POP 26` + `26 JUMP_FORWARD 30` + `28 LOAD_CONST 'z'`。
  - `/tmp/probe_recbool.py`：直接 `ExpressionReconstructor(cfg).reconstruct(all_instrs)` 对 `m3` 返回 `Return(List([Name('y')]))`（左操作数 `x` 丢失）；`_extract_comp_ifs` 返回 `([], 6)`。
  - `/tmp/probe_comp38.py`：修复前直接调 `parse_comprehension_inner` 时在 `ast_generator_v2.py:252` 抛 `IndexError: list assignment index out of range` —— `reconstruct` 末尾合并段用 `self.stack[-2] = {...}` 而 `pop()` 已把长度减到 1；改为 `pop/pop/append` 后消除。
  - `/tmp/probe_gen36b.py` 的前序结论复用：元素表达式由 `ComprehensionGenerator` 路径重建（`_generate_ternary` 在该 genexpr 内 0 条调用），故本族修复落在推导式生成器与表达式重建器，不动区域生成器。
- 最小复现读数：
  - 修复前 `/tmp/mini38`：`m1` → `[y if x else 'e' ...]`、`m2` → `[y if x else 'e' ...]`（丢 `'%s'` 与 `%`）、`m3` → `[y ...]`、`m4` → `[y ...]`、`m5` → `['e' if x else 'z' ...]`；`/tmp/cmpnested38.py` 报 `m1 @18 JUMP_IF_TRUE_OR_POP 22 vs JUMP_FORWARD 22`、`m2` 缺 `('str','%s')` 且 `FOR_ITER 32 vs 26`、`m3`/`m4` `@8 FOR_ITER 22 vs 18`、`m5` `@0 MAKE_CELL 'y' vs RESUME 0` + `<listcomp>` `COPY_FREE_VARS 1 vs RESUME 0`，共 5 条。
  - 修复后 `/tmp/mini38d/out.py`：`m1` = `[x and y or 'e' for x in xs]`、`m2` = `['%s' % (x and y or 'e') for x in xs]`、`m3` = `[x or y ...]`、`m4` = `[x and y ...]`、`m5` = `[x and y or 'e' if x else 'z' ...]`；`/tmp/cmpnested38.py` **零输出（无 CODE-DIFF）**，先前的 `MAKE_CELL`/`COPY_FREE_VARS` 丢帧也随之消失（产物恢复细胞变量声明后外层与 `<listcomp>` 的帧初始化逐字节对齐）。
  - `/tmp/mini37c2/out.py`（对照族）：`k7` 恢复 `['%-14s' % (x and x or 'e') ...]`，`/tmp/cmpnested37.py` 由 1 条 CODE-DIFF 收敛到 **零输出**；`k1`–`k6`、`k8` 与修复前逐字节相同（`MAP_ADD` 守卫 + 非 keep-or-pop 形态回落保证 C3）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | **7/7 全 EQUAL**；`/tmp/cmpnested45.py /tmp/rep46/prod20/REAL46-045.py` **零 CODE-DIFF 输出** |
| A/B `/tmp/ab`（24 stdlib pyc） | `new18` vs `new17` 文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 问题集 `diff -u` **零差异**（`diff exit=0`） |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed in 3.73s`，失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`） |
| fuzz | `total=293 failures=0 stopped=time_budget`（120s） |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- 既有残差仍在：`/tmp/mini35/v.py::g1` 尾随 `print` 蒸发（Pattern C2 无 SWAP 解包路径降级后未把尾随语句交回通用重建，`orig=17 prod=11`）、`print('%s' % (ternary))` merge 消费重建错误（B235，`(row['x'] is None)('-' % 'y')`）、AnnAssign 注解丢失（`z: dict[str, int] = {}` → `z = {}`）、`newline="""\n"""` 三引号渲染。
- 推导式元素位更长的短路链（三操作数以上 `A and B and C or D`、`A or B and C`）尚未纳入本轮复现集，keep-or-pop 开关对「链上多处 keep-or-pop」的左折叠路径只做了 `A or B or C` 的推导，需在下一族补实测样本。

### rr-v5r41：`x is None` 条件三元未登记区域 + f-string 跨块被调对象误取实参 + 尾段重复发射（B235）（2026-10-26）

最小复现 `/tmp/mini10/v.py`（三函数，均从 `scripts/pyc_verify.py` 的 `cmd_single` 抽出）：`f1(row)` = `print('[single] status=%s units=%d/%d success_rate=%s' % (...))`、`f2(row)` = `print(f"{row['a']!s} {'-' if row['x'] is None else 'y'!s}")`、`f3(row)` = `print('%s' % ('-' if row['x'] is None else 'y'))`，三函数末尾均为 `return 0 if row['status'] == 'success' else 1`；同族对照 `/tmp/mini34/v.py` 的 `h1`/`h2`/`h3`。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 表达式重建 | `ExpressionReconstructor._process_instruction` 的 `POP_JUMP_FORWARD_IF_NOT_NONE` 分支（`core/cfg/ast_generator_v2.py` 836 起） | 该分支只把 `Compare(is)` 压栈、**不登记三元区域**（镜像的 `POP_JUMP_FORWARD_IF_NONE` 分支有 `_open_ternary_region`）⇒ 汇合处 `[test, body, orelse]` 仍是三个独立栈项，被 `BINARY_OP` 当成 `'-' % 'y'`、条件节点被 `CALL` 当成函数对象 ⇒ 产物 `(row['x'] is None)('-' % 'y')`，宿主 `print` 与 `'%s'` 前导整段蒸发 | 在压栈之后按镜像补 `_open_ternary_region(compare_node, instr.argval)`；区域机制自身由 `_close_ternary_region` 的「测试节点必须是区域开启时那个」守卫封闭，且仅在 `fold_cond_jump_ternary=True` 时启用（默认关闭 ⇒ 既有全部调用路径逐字节不变） |
| ② | 区域生成 | `_generate_host_prefix_ternary_statement` 的 `tail_instrs` 段（`core/cfg/region_ast_generator.py` 52686 起） | 闭合块里跨度之后的那段指令若属于**另一个尚未生成的区域**（紧随其后的三元条件测试与词法块共处同一极大直线块），本函数一并物化 ⇒ 同一条件测试被重复发射成裸表达式语句（产物多出 `row['status'] == 'success'` 一行、重编译多 6 条指令） | 尾段首指令所在块若是其它未生成区域的 `entry`/`condition_block`，则尾段不物化（交回该区域自身发射）；判据只读区域归属（同层结构事实），非区域入口的尾段行为逐位不变 |
| ③ | 区域生成 | `_ternary_pending_callee`（`core/cfg/region_ast_generator.py` 61789 起） | 「空对象标记」有两种编码：独立 `PUSH_NULL` 指令（其后一条才是被调对象）与 3.11 把标记编进 `LOAD_GLOBAL` 操作数低位（`LOAD_GLOBAL 1 (NULL + name)`，该指令自身即被调对象、其后一条已是第一个实参表达式）。本方法把两者共用同一「取下一指令为 callee」的推导 ⇒ `print(f"{row['a']!s} ...")` 的前缀 `LOAD_GLOBAL print(NULL) ; LOAD_FAST row ; ...` 把 `LOAD_FAST row` 当成 callee，产物 `row(f"...")`，宿主 `print` 消失 | 新增 `_null_in_load_global` 区分两种编码：独立 `PUSH_NULL` 形态才走「下一指令为 callee」分支，`LOAD_GLOBAL` 低位标记形态交给既有 `[R63 Fix2a]` 段（callee 即该 `LOAD_GLOBAL` 自身，其后 `LOAD_ATTR` 链构成属性链）。判据只读本块 opcode 与 `arg & 1` 位（I.4 白名单），不含名字/偏移/阈值 |
| ④ | 区域生成 | `_try_wrap_fstring_pending_call` 的 `_rest` 段（`core/cfg/region_ast_generator.py` 62060 起） | 跨块待定调用闭合（`BUILD_STRING; PRECALL; CALL 1; POP_TOP`）之后，同一极大直线块里紧跟的下一区域条件测试被 `_build_statements_from_instructions` 物化成裸 `Expr` ⇒ 与 ② 同源的重复条件行 | 同 ② 的区域归属守卫：`_rest[0]` 所在块为其它未生成区域的 `entry`/`condition_block` 时不再物化 |

- 定位证据：
  - `/tmp/probe_h1.py /tmp/mini10/v.pyc f2`：块结构 `B1@0-46`（`2 LOAD_GLOBAL print(NULL); 14 LOAD_FAST row; 16 LOAD_CONST 'a'; 18 BINARY_SUBSCR; 28 FORMAT_VALUE; 30 LOAD_CONST ' '; 32 LOAD_FAST row; 34 LOAD_CONST 'x'; 36 BINARY_SUBSCR; 46 POP_JUMP_FORWARD_IF_NOT_NONE 52`）、`B2@48-50`、`B3@52-52`、`B4@54-96`（`FORMAT_VALUE; BUILD_STRING 3; PRECALL; CALL 1; POP_TOP; LOAD_FAST row; ...; POP_JUMP_FORWARD_IF_FALSE 102`）、`B5/B6/B7`；区域 `TernaryRegion entry=0 merge=B4（value_target='__fstring_target__'、container_type='call'、merge_context='fstring'）` + `TernaryRegion entry=B4 merge=B7`。
  - `/tmp/probe_hp.py /tmp/mini10/v.pyc f2`：外层三元的 `_ternary_host_call_prefix_span` 返回 **None**（与 `h1` 的非 None 形态不同）⇒ 走 `_try_wrap_fstring_pending_call` 通道；`_generate_ternary` 产出的 `stmts` 为单条 `Expr(Call(func=Name('row'), args=[JoinedStr]))`。
  - `/tmp/probe_f2.py /tmp/mini10/v.pyc f2`：`split_prefix = []`（无块内前导语句可切），条件前缀整体归约为 `Compare(Subscript(row,'x'), is, None)`。
  - `/tmp/probe_trace_h1.py` 的前序结论复用：修复前 `30 POP_JUMP_FORWARD_IF_NOT_NONE` 后栈为 `[Name(print), Constant('%s'), Compare(is)]`、`38 BINARY_OP` 后为 `[..., BinOp('-','%','y')]`、`46 CALL` 后为 `[..., Call(func=Compare(is), args=[BinOp])]` ⇒ ① 的单点缺陷成立。
- 最小复现读数：
  - 修复前 `/tmp/mini10b/out.py`：`f2` = `row(f"{row['a']!s} {'-' if row['x'] is None else 'y'!s}")` + 裸行 `row['status'] == 'success'` + `return 0 if ... else 1`；`/tmp/cmpany.py` 报 `CODE-DIFF f2 len 106 vs 122`、`first diff @2: LOAD_GLOBAL print vs PUSH_NULL None`、`total diffs = 1`。
  - 修复后 `/tmp/mini10/b2/out.py`：`f2` = `print(f"{row['a']!s} {'-' if row['x'] is None else 'y'!s}")` + `return 0 if row['status'] == 'success' else 1`；`f1`/`f3` 保持正确；`/tmp/cmpany.py` 报 `total diffs = 0`。
  - `/tmp/mini34/c2/out.py`（同族对照，`g1`/`g2`/`g3`）：`g1` = `print('[single] %s' % row['pyc'])` + `print('[single] 产物 %s' % row['source'])` + `print('[single] status=%s units=%d/%d success_rate=%s' % (...))` + `return 0 if ... else 1`；`/tmp/cmpany.py` 报 `total diffs = 0`（`h1` 的多余条件行与 `print('%s' % (ternary))` 退化同时消失）。
  - 对照族逐字节未变：`/tmp/mini37`、`/tmp/mini36`、`/tmp/mini30`、`/tmp/mini28`、`/tmp/mini27` 重生成后 `/tmp/cmpany.py` 均 `total diffs = 0`；`/tmp/mini38`（B236/B237 复现集）`/tmp/cmpnested38.py` **零输出**。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | **7/7 全 EQUAL**（`/tmp/judge5.py /tmp/rep46/prod21`）；`/tmp/cmpnested45.py /tmp/rep46/prod21/REAL46-045.py` **零 CODE-DIFF 输出** |
| A/B `/tmp/ab`（24 stdlib pyc） | `new19` vs `new18` 文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 问题集 `diff -u` **零差异**（`diff exit=0`） |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed in 3.93s`，失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`） |
| fuzz | `total=293 failures=0 stopped=time_budget`（120s，`/tmp/fuzz42`） |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- `/tmp/mini35/v.py::g1`：多目标赋值后紧跟 `print(da, db)` 时 `print` 整段丢失（`orig=17 prod=11`）——`_generate_block_statements_body` 的 Pattern C2 无 SWAP 解包路径（`_ns_n = 0` 降级）后未把尾随语句交回通用重建。
- 推导式元素位更长的短路链（`A and B and C or D`、`A or B and C`）仍未纳入复现集。
- `z: dict[str, int] = {}` 的 AnnAssign 注解在产物中丢失（`/tmp/mini28/out2.py` 为 `z = {}`）——B230 修复只覆盖函数签名注解。
- `newline="""\n"""` 三引号渲染（`/tmp/mini30/out_fix.py`）。

### rr-v5r42：无 SWAP 解包路径剩余段未按语句边界切分（B238）（2026-10-26）

最小复现 `/tmp/mini35/v.py`（四函数，取自 `scripts/pyc_verify.py` 的 `cmd_compare` 同族）：`g1(before, after)` = `da, db = before['a'], after['a']` + `print(da, db)`；`g2` = 两段多目标赋值 + `print(da, ta, db, tb)`；`g3` = `da, db = ...` + `return da, db`；`g4` = `x, y = 1, 2; print(x, y)`。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 区域生成 | `_generate_block_statements_body` 的 Pattern C2 无 SWAP 解包路径 `_ns_remaining` 处理段（`core/cfg/region_ast_generator.py` 66946 起） | 纯名字多目标赋值（`LOAD c; LOAD d; STORE b; STORE a`，反源序连续 STORE 无 SWAP）识别与归约本身正确（`_ns_n=2`），但末 STORE 之后**剩余段**被整体当作 return 值交给 `reconstruct`：该段可能同时含**完整的兄弟语句**（`LOAD_GLOBAL print; LOAD_FAST da; LOAD_FAST db; PRECALL 2; CALL 2; POP_TOP`）与 `LOAD_CONST None; RETURN_VALUE` ⇒ `reconstruct` 只取栈顶 `Constant(None)`，前面的兄弟语句被静默丢弃（`/tmp/mini35/v.py::g1` 实测 `orig=17 prod=11`，产物退化为隐式 `return None`） | 剩余段按语句边界切分：从 `RETURN_VALUE`/`RETURN_CONST` 之前回扫到最近一条语句终结指令（复用 `_B54_STMT_TERMINATOR_OPS`，块内 opcode 序、I.4 白名单），其前段交 `_build_statements_from_instructions` 重建为兄弟语句（含任何跳转指令则不切，避免把控制流当直线语句），其后段仅重建 return 值；不含终结指令的段不可能含语句边界 ⇒ 行为与旧实现逐位相同（C3） |

- 定位证据：
  - `/tmp/probe_h1.py /tmp/mini35/v.pyc g1`：单块 `B1@0-68` = `2 LOAD_FAST before; 4 LOAD_CONST 'a'; 6 BINARY_SUBSCR; 16 LOAD_FAST after; 18 LOAD_CONST 'a'; 20 BINARY_SUBSCR; 30 STORE_FAST db; 32 STORE_FAST da; 34 LOAD_GLOBAL print; 44 LOAD_FAST da; 46 LOAD_FAST db; 48 PRECALL 2; 52 CALL 2; 62 POP_TOP; 64 LOAD_CONST None; 66 RETURN_VALUE`（无 SWAP、反源序连续 STORE）。
  - `/tmp/probe_body41.py`：`_generate_block_statements_body` 行号轨迹 66419→66813→66838–66971，最终 `stmts` 只有 `Assign` + `Return(Constant(None))` ⇒ `print` 在同一次调用内被丢弃。
  - `/tmp/probe_ns41.py`：`first store idx 6 stores 2 walk 8`、`_ns_after = [('LOAD_GLOBAL','print'), ('LOAD_FAST','da'), ('LOAD_FAST','db'), ('PRECALL',2), ('CALL',2), ('POP_TOP',None), ('LOAD_CONST',None), ('RETURN_VALUE',None)]`。
  - `/tmp/probe_ns41b.py`：`66917 ns_n 2 ns_stacklen 2`（解包归约成立）、`66967 rv_instrs = [('LOAD_GLOBAL','print'), ('LOAD_FAST','da'), ('LOAD_FAST','db'), ('PRECALL',2), ('CALL',2), ('LOAD_CONST',None)]` ⇒ `reconstruct` 返回 `Constant(None)`。
- 最小复现读数：
  - 修复前 `/tmp/mini35/r41/out.py`：`g1` 仅 `da, db = (before['a'], after['a'])`（`print(da, db)` 蒸发）；`/tmp/cmpany.py` 报 `CODE-DIFF g1 len 70 vs 38`、`first diff @34: LOAD_GLOBAL print vs LOAD_CONST None`、`total diffs = 1`。
  - 修复后 `/tmp/mini35/r42/out.py`：`g1`/`g2`/`g3`/`g4` 四个函数与源码逐行一致；`/tmp/cmpany.py` 报 `total diffs = 0`。
  - 对照族逐字节未变（21 个复现集重生成逐条 `total diffs = 0`）：`/tmp/mini10`（B235）、`/tmp/mini21`（B227）、`/tmp/mini22`（B226/B227）、`/tmp/mini24`、`/tmp/mini25`（B228）、`/tmp/mini26`（B228）、`/tmp/mini27`（B229）、`/tmp/mini28`（B230）、`/tmp/mini30`（B231）、`/tmp/mini32`/`mini33`（B232）、`/tmp/mini34`（B233）、`/tmp/mini36`/`mini37`（B236/B237）、`/tmp/mini38`（B236/B237）、`/tmp/mini16`、`/tmp/mini17`、`/tmp/mini29`、`/tmp/mini35`（B238 本体）。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | **7/7 全 EQUAL**（`/tmp/judge5.py /tmp/rep46/prod22`）；`/tmp/cmpnested45.py /tmp/rep46/prod22/REAL46-045.py` **零 CODE-DIFF 输出** |
| A/B `/tmp/ab`（24 stdlib pyc） | `new20` vs `new19` 文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 问题集 `diff -u` **零差异**（`diff exit=0`） |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed in 3.77s`，失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`） |
| fuzz | `total=295 failures=0 stopped=time_budget`（120s，`/tmp/fuzz43`） |

判定空间四桶不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- 推导式元素位更长的短路链（`A and B and C or D`、`A or B and C`）仍未纳入复现集（keep-or-pop 左折叠只对 `A or B or C` 推导过）。
- `z: dict[str, int] = {}` 的 AnnAssign 注解在产物中丢失（`/tmp/mini28/out2.py` 为 `z = {}`）——B230 修复只覆盖函数签名注解。
- `newline="""\n"""` 三引号渲染（`/tmp/mini30/out_fix.py`）。

### rr-v5r43：嵌套 finally 出口臂误建 match + J 空间 v3 备料（B239 / Task 5.5）（2026-10-26）

本轮两件独立工作：① 修 `v_nest_fin_continue` 的 `continue` 丢失（B239）；② 落地判定空间 v3 备料工具（Task 5.5 的 `module_only` 收缩路径）。

最小复现 `/tmp/mini*` 之外，直接取自判定空间 v3 的 `JS-IF-017.pyc`/`JS-IF-021.pyc` 的 `v_nest_fin_continue`：

```python
def v_nest_fin_continue(rows):
    out = []
    for r in rows:
        try:
            try:
                if r == 0:
                    continue
            finally:
                out.append(1)
        finally:
            out.append(2)
        out.append(r)
    return out
```

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 区域分析 | `_b142_arm_exits_via_finally_copy`（`core/cfg/region_analyzer.py` 14804 起） | 真臂本身可能只是**纯噪声桩块**（`[NOP]`），finally 副本在它的唯一 fall-through 后继上（实测真臂 `B4@30=[NOP] → B14@32` 内层副本；假出口 `B5@118=[NOP] → B16@120` 内层副本）。旧实现只查真臂块自身（`B4` 的 `start_offset=30` 不在台账键集 `{32, 120}`）⇒ 守卫恒不命中 | 新增 `_b142_walk_noise_stub`：沿「块内无有义指令（仅 `RESUME`/`NOP`/`CACHE`/`EXTENDED_ARG`）且正常后继唯一」的桩链穿越到首个有义块再查台账；visited 集合保证有限图终止，**不设深度常数**（G4 无硬编码上限）；后继不唯一或环回返回 `None`（`None` 不是台账成员 ⇒ 逐位回落到旧行为，C3） |
| ② | 区域分析 | `_identify_match_regions` 主扫描（`core/cfg/region_analyzer.py` 17213 起） | 主扫描**缺** B142 出口臂守卫（`_scan_literal_match_subjects` 与 `_collect_nested_match_region` 都有，主扫描没有）⇒ `B13@18` 只靠 `_is_match_subject_block` 的 `[B215-R5R10]` 无 COPY 分支入选，直接建成 `MatchRegion entry=B13`，产物把 `if r == 0: continue` 发成 `match r: case 0: <空体>` 与 `case _: out.append(r)` | 在候选判定之后、`subject_block` 赋值之前补同一否决，但**只对非结构型候选生效**：`not _has_match_op(block) and not _is_case_pattern_block(block) and _b142_arm_exits_via_finally_copy(block)` ⇒ `continue`。结构型 match（`MATCH_*` 操作码）与 case pattern 块一律不走此否决（它们的 case 体是编译器显式协议，与 finally 副本无关），保证真 match 零影响 |

- 定位证据：
  - `/tmp/probe_b239.py .../JS-IF-017.pyc v_nest_fin_continue`：`B13@18-28` = `LOAD_FAST r; LOAD_CONST 0; COMPARE_OP ==; POP_JUMP_FORWARD_IF_FALSE 118`，正常后继 `[B4@30, B5@118]`、异常后继 `[B6@164]`；`B4@30=[NOP] succ=[B14]`、`B5@118=[NOP] succ=[B16]`；两个 `TryExceptRegion` 均 `has_finally=True`，台账键集 `{32, 120}`（entry 18）与 `{74, 216}`（entry 30）；`B14@32`/`B16@120` 正是内层副本。
  - `/tmp/probe_b239b.py`：修复前 veto=False；修复后 `[probe] b13 veto = True`、`walk -> (14, 32) member= True`。
  - `/tmp/probe_b239c.py`：`has_match_op=False`、`is_case_pattern=False`、`is_match_subject=True`，其余四个候选谓词全 False ⇒ 唯一入口是字面量 subject 启发式，② 的窄门控成立。
- 最小复现读数：
  - 修复前 `/tmp/if017/out.py`：`match r: case 0: continue case _: out.append(r)` 且 `continue` 丢失；`/tmp/cmpany.py` 报 `CODE-DIFF v_nest_fin_continue len 362 vs 220`、`first diff @10: FOR_ITER 358 vs FOR_ITER 216`、`total diffs = 1`。
  - 修复后 `/tmp/b239/out.py`：`v_nest_fin_continue` 恢复 `try: try: if r == 0: continue finally: out.append(1) finally: out.append(2)` 逐行一致；`/tmp/cmpany.py` 报 `total diffs = 0`。`JS-IF-021` 同样 `total diffs = 0`。
  - 语义差分：`JS-IF-017` / `JS-IF-021` 由修复前 `DIFFERENT ['R7','R7','R1','R1','R1','R1']` 变为 **`EQUAL` `covered_5tuple`**（`semantic_runner --space /tmp/j3test/space17.json` → `verdicts={'EQUAL': 2} covered_5tuple=2`）。
- 对照族逐字节未变：19 个复现集（`/tmp/mini_regress.py` 统一切换到「块结构 + 代码对象递归 + 非代码常量」比对口径）重生成逐条 `OK`，`TOTAL ISSUES = 0`。

#### Task 5.5 备料：判定空间 v3（`judgment_space_v3.json`）

- 背景（环境事实）：J v2 的 1556 条 `pyc` 路径在本树内**无一存在**（`pyc_present=true` 是历史机器读数），1107 条 `input_model.calls` 为空 ⇒ `semantic_runner` 对它们只能给 `probe_only / module_only`，`module_only` 桶（719）无法靠重跑收缩。
- 新工具 `tools/completeness/jspace_v3_prepare.py`（`--space --out --pyc-dir [--report] [--limit]`）：
  - `pyc`：缺失即按 `py_compile.compile(..., invalidation_mode=UNCHECKED_HASH)` 从 `p_j` 重编译（内容寻址，可重生成），并把 provenance 写回条目；
  - `calls`：已有则保留；空则先过安全闸——`real-package module`（缺 `six`/`jsonpickle` 等宿主依赖）**不派生**，只从 `no zero-arg/defaulted top-level callable` 一类**可派生名单**里取源文件，用 `ast` 合成零参/全默认参数的顶层 `def`/`async def`/`class` 调用（类按 `__init__`/`__post_init__` 剥 `self`/`cls`；`async def` 不派生，eval 里无法 `await`），注解/参数名按查表给种子（`n`/`count`/`size` 一律 `1` 避免 `while n:` 不收敛超时；`rows`/`items`/`seq` 用 `[0, 1, -1]` 让循环体真正执行），每个条目至多 6 条、跳过 `input`/`breakpoint`/`exit`/`quit`。
- 全量读数（verbatim）：`[jspace_v3_prepare] entries=1556 pyc_regenerated=1556 pyc_failed=0 with_calls=1086 without_calls=470`；`stats={'pyc_regenerated': 1556, 'pyc_kept': 0, 'pyc_failed': 0, 'calls_derived': 637, 'calls_kept': 449, 'calls_empty': 470}`；`derivation_reasons={'unsafe_host_module: real-package module': 376, 'no_top_level_callable_with_constructible_arguments': 94}`。
- 产物：`.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/` 下 `judgment_space_v3.json`（`j_schema_version=v3`，1556 条）、`pyc/`（1556 个）、`prepare_report.json`；全量 C1–C5 三片并行 `semantic_v3_shard{0,1,2}.json` 仍在跑（`--offset 0/519/1038 --limit 519/519/518`），合并后交 `coverage_checker.py` 重读三桶。

#### 复跑读数（本轮实测）

| 门禁 | 本轮结果 |
|---|---|
| G2c 子集 `/tmp/rep46` 七条 | **7/7 全 EQUAL**（`semantic_runner --space /tmp/rep46/space.json --product-dir /tmp/rep46/prod23`） |
| A/B `/tmp/ab`（24 stdlib pyc） | `new21` vs `new20` 文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 问题集 `diff -u /tmp/ab/b20.txt /tmp/ab/b21.txt` **零差异**（`AB-BYTE-IDENTICAL`） |
| 19 个最小复现集 | `/tmp/mini_regress.py` **`TOTAL ISSUES = 0`** |
| pytest 七套件 | `2 failed / 282 passed / 2 xpassed in 5.94s`，失败名单与基线逐位一致 |
| fuzz | `total=164 failures=0 stopped=time_budget`（120s，`/tmp/fuzz44`） |

判定空间四桶在 v2 口径下不变（covered_equal 395 / uncovered 0 / module_only 719 / unjudgeable 442）；v3 口径待三片合并后登记。v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- 推导式元素位更长的短路链（`A and B and C or D`、`A or B and C`）仍未纳入复现集。
- `z: dict[str, int] = {}` 的 AnnAssign 注解在产物中丢失（`/tmp/mini28/out2.py` 为 `z = {}`）——B230 修复只覆盖函数签名注解。
- `newline="""\n"""` 三引号渲染（`/tmp/mini30/out_fix.py`）。
- J v3 的 470 条空 calls 中有 376 条是 real-package 宿主依赖缺失（`six`/`jsonpickle` 未安装），这些条目要真正进入语义覆盖需要装依赖或换宿主探针，不能靠派生。

### rr-v5r44：Try 入口折叠宿主行头 NOP 补发 + J v3 三桶读数收尾（B241 / Task 5.5 读数）（2026-10-26）

本轮两件独立工作：① 修 `x04_try_deep_hosts.py` 的 `try_in_if`/`try_in_while` NOP 计数错位（B241）；② 把 J v3 的 110 条 held-out 语义记录用统一 judge 重跑并合入全量读数（Task 5.5 收尾）。

最小复现 `/workspace/test_repros/round2/x04_try_deep_hosts.py`：

```python
def try_in_if():
    if 1:
        try:
            if 1:
                try:
                    R = 1
                finally:
                    F = 1
        except ValueError:
            R = 2
    return 1
```

`try_in_while()` 同族（`while 1: try: while 1: try: ... finally: ... except ValueError: ...`）。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 生成层 | `generate()` 的 `TryExceptRegion` 入口前缀分支（`core/cfg/region_ast_generator.py` 1572-1578） | 函数入口块 `B1@0` 的块首是连续 NOP 游程，其终点恰为 try 体受保护区起点；该块被 `TryExceptRegion` 整体认领、**不进入** `_generate_block_statements`，而通用折叠 NOP 通道又被 `_nop_structural_veto` 的 V-T（游程终点 == 异常表 start）全部否决 ⇒ 该游程**无任何发射点**，`try_in_if` 少了宿主 `if 1:` 那 1 条 NOP（产物 74 vs 原件 76，`first diff @8: NOP None vs LOAD_CONST 1`） | 新增 `_try_entry_folded_head_units(entry_block)`：收集块首（跳过 `RESUME`/`CACHE`/`PUSH_NULL`）连续 NOP 游程，以「try_blocks 首块偏移 == 游程终点」计数本作用域内共享该起点的 `TryExceptRegion` 数 k；游程前 `len-k` 个 NOP 即宿主折叠行头，逐一发射 `_folded_statement_placeholder()`（裸 pass，任意位置恰 1 NOP、零常量），并登记 `_x01_claimed_nops` 防重复认领；后 k 个归 Try 语句再生 |
| ② | 生成层 | `_generate_block_statements_body` 受保护 NOP 分支（68480-68486）与 `_generate_try_body` 空有效指令块循环（35992-35998） | `_is_protected_statement_nop` 命中但 `_nop_structural_veto` 同时命中的 NOP 被错误发射包裹占位（`try_in_while` 的 `B10@6`，异常表 `(6,8,38)` 的 start 恰为 6、游程终点 8 也是该 start）⇒ 多 1 条 NOP（产物 76 vs 原件 74，`first diff @10: LOAD_CONST 1 vs NOP None`） | 两处受保护 NOP 发射点补 `and not self._nop_structural_veto(...)` 门：被结构否决的 NOP 不再发射包裹占位，由 ① 或既有游程通道统一认领 |

- 定位证据：
  - `/tmp/b241/nopshape.py` 实测 CPython 3.11 折叠行标记协议：`if 1:`/`try:`/`while 1:` 行头各 1 条行标记 NOP；入口块若含折叠行头，以连续 NOP 游程收尾，游程终点 = try 体保护区起点；游程 = 宿主折叠行头 + 每个共享该起点的嵌套 `TryExceptRegion` 的 `try:` 行各 1 条。四形态读数：`try_try`（try 套 try）入口 2 NOP = 2 个 try 行 → 零补发；`if_try` 入口 2 NOP = 1 宿主 `if` + 1 try → 补 1；`while_try` 入口 3 NOP = 2 宿主（`while 1` + `if 1`）+ 1 try → 补 2；`try_body_empty_fold`（try 内 `if 1:`）入口 1 NOP = 1 try → 零补发。
  - `/tmp/b241/probe_classify.py`：逐 NOP 打印 `protected / veto / unacct / rag / orphan`，确认 `try_in_while` 的 `B10@6` 是「protected 且 veto」双重命中；`/tmp/b241/probe_emit.py` 打桩三个占位工厂 + pprint AST，确认入口块 AST 在修复前无任何 pass 单元。
- 最小复现读数（本轮树实测）：
  - `python pycdc.py .../jspace_v3/pyc/JS-TRY-008.pyc -o /tmp/verify44_out.py` + `/tmp/cmpany.py`：`total diffs = 0`。
  - 四个合成探针重生成后 `/tmp/cmpany.py`：`try_try` / `if_try` / `while_try` / `try_body_empty_fold` 全部 `total diffs = 0`。
  - 对照族回归（本轮树实测）：`JS-TRY-*.pyc` 108 个 `tools/bc_cmp.py` 逐函数比对，**19 个 FAIL**，失败清单与修复前基线逐位一致（`TradeLiveBroker.on_before_trading_start` / `_process_order` / `_process_tick_order` 族 4 个、`get_trade_list` 15 个），非本轮引入（前轮 `git stash` 对比已同败）。
  - pytest 七套件：`2 failed / 277 passed / 2 xpassed in 1.46s`，两个失败为基线既有（`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`TestBoundaryConditions::test_BOUNDARY_02_large_function`）。

#### Task 5.5 读数收尾：J v3 三桶（`semantic_v3_merged.json` / `coverage_v3.json`）

- 重跑原因：`semantic_v3_shard{0,1,2}.json` 首跑未显式传 `--judge`，`judge_sha256` 与 `coverage_checker --judge` 不一致，产生 395 条 `c5_judge_mismatch` 与 11 条 `R7 ['R7','R7']` 伪 `DIFFERENT`；110 条 held-out 记录（`--offset/--limit` 两片各 55 条）用 `--judge /workspace/tools/completeness/semantic_diff.py` 重跑，两片各 **55/55 `EQUAL`**，合并替换进 `semantic_v3_merged.json`（1556 条）。
- 合并后 verdict 分布：`EQUAL 1130 / ERROR 424 / DIFFERENT 2`（`DIFFERENT` 仅 `JS-IF-017`、`JS-IF-021`，即 B239 修复前的历史记录位点）。
- `coverage_checker --space judgment_space_v3.json --evidence semantic_v3_merged.json --judge tools/completeness/semantic_diff.py` 全量读数（verbatim）：
  `[coverage] J_total=1556 covered_5tuple=1050 probe_only=0 unexecuted=0 n/a=0 inconclusive=36 excluded=470 uncovered=506 coverage=67.48%`
  - `covered_5tuple=1050`：其中 `green=1048`（`EQUAL`）+ `semantic_failures=2`（`DIFFERENT` 仍满足 C1–C5 五元组绑定，按 checker 口径计 `covered_5tuple` 但不计 `green`）。
  - `inconclusive=36`：全部 `c4_error`，按形态 `Import 12 / With 12 / AnnAssign 12`。
  - `excluded=470`：即 `without_calls=470`（376 条 real-package 宿主依赖缺失 + 94 条无零参可构造入口），其中 `ERROR 388` / `EQUAL 82`。
  - `uncovered=506 = 1556 - 1050`（checker 口径：`excluded` + `inconclusive` 均不计入 covered）。
  - `judge_sha256=dbcb1e246dd549f2c66a1d779f31eba0506f9c99364db02a679523dde84d8174`（= 当前 `tools/completeness/semantic_diff.py`），`c5_judge_mismatch` 归零。
- 产物：`rounds/round13/jspace_v3/` 下 `semantic_v3_merged.json`（1556 条）、`coverage_v3.json`、`COVERAGE_V3.md`（逐形态族 + 未覆盖清单）。

#### 本轮新暴露残差（未修，下一族）

- J v3 仍有 36 条 `c4_error` inconclusive（`Import`/`With`/`AnnAssign` 各 12），需逐条查明是产物缺陷还是探针种子问题。
- 470 条空 calls 中 376 条卡在 real-package 宿主依赖（`six`/`jsonpickle` 未安装），要进入语义覆盖必须补依赖或换宿主探针。
- 推导式元素位更长短路链（`A and B and C or D`、`A or B and C`）未纳入复现集；`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染。

### rr-v5r45：推导式元素位更长短路链 keep-or-pop 归约（B242）（2026-10-26）

最小复现 `/tmp/r45/w.py`（9 形态）与 `/tmp/r45/w2.py`（17 形态），全部为 CPython 3.11 对「结果即表达式值」位置发射的 keep-or-pop（`JUMP_IF_FALSE_OR_POP` / `JUMP_IF_TRUE_OR_POP`）短路链：

```python
def m3(xs, y, z): return [x or y and z for x in xs]
def m5(xs, y, z, w): return [(x and y) or (z and w) for x in xs]
def m6(xs, y, z, w): return [x and (y or z) or w for x in xs]
def m7(xs, y, z, w): return [x or y and z and w for x in xs]
def m9(xs, y, z, w): return [(x or y) and (z or w) for x in xs]
def n5(xs, y, z, w): return [x or y and z or w for x in xs]
def n6(xs, c, y, z): return [x if c else y and z for x in xs]
def n7(xs, c, y, z): return [x and y if c else z for x in xs]
def n17(xs, y, z, w): return [bool(x or y and z and w) for x in xs]
```

修复前退化（`/tmp/r45/wbase.py`、`/tmp/r45/w2base.py`）：`m3`/`n16`→`(x or y) and z`、`m5`→`x and y or w`、`m6`→`x and y or w`、`m7`→`(x or y) and z and w`、`m9`→`(x or y) and w`、`n5`→`z if y else w`、`n6`→`x if c else z`、`n7`→`y if c else z`、`n17`→语法无效的 `[ for x in xs]`（`BoolOpPending` 被 `PRECALL/CALL` 当被调对象）。读数：`w` `total diffs = 8`、`w2` `total diffs = 15`。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 表达式重建 | `ExpressionReconstructor._process_instruction` 的 keep-or-pop 分支（`core/cfg/ast_generator_v2.py` 386-422） | `BoolOpPending` 只携带 `(op, left)` 做**逐跳左折叠**：混合 `and`/`or` 链（`x or y and z`）按扫描序左折必然成 `(x or y) and z`；嵌套层级与运算符边界信息在第一步就丢失 | 改为**扁平序列累积** `(ops, values)`：每个跳转只追加一个「运算符—右操作数」边界，不做任何结合；Pending 不产生独立语句（③唯一归属），父消费端只看到归约后的单一 BoolOp |
| ② | 表达式重建 | `reconstruct` 扫描循环（同文件 241-262） | keep-or-pop 链的汇合点之后还有消费该值的指令（`bool(...)` 的 `PRECALL/CALL`）时，`Pending` 仍留在栈上 ⇒ 被当作被调对象/操作数（实测产物 `[ for x in xs]` 语法无效） | 扫描前先收集窗内 keep-or-pop 跳转的 `argval` 目标偏移集合，逐指令到汇合点时先 `_b242_flush_boolop_pending()` 把 `(Pending, 右操作数)` 归约成单一节点，再处理该指令 |
| ③ | 表达式重建 | 新增 `_b242_fold_boolop_pending`（同文件 294-334） | 扁平序列需要一个确定的结合序：布尔优先级归约会用错边界（首版实现把 `x and y or z` 退化成 `x or z`、`(x and y) or (z and w)` 退化成 `x or z and w`） | 按 CPython 3.11 事实「纯 keep-or-pop 链只出现在右结合位置」（`A and B or C` 用 `POP_JUMP` 直落假值区，只有 `A or B and C` / `A and (B or C)` 才用 keep-or-pop）⇒ 自右向左结合，连续同运算符扁平合并（保持 `x and y and z` 三成员单节点）；`len(values) != len(ops)+1` 即返回 `None` 交回原栈顶（C3） |
| ④ | 推导式生成 | `ComprehensionGenerator._b237_kop_window`（`core/cfg/comprehension_generator.py` 2786-2925） | 真值区只取「首个 keep-or-pop 终结符之前」，`x and (y or z) or w` 丢 `z`；假值区/条件区重建走未开启同族归约的 `reconstruct`，`(x and y) or (z and w)`、`x or ((y and z) or w)` 丢左段 | ①首循环跳**前导** keep-or-pop（它是本窗口之上的外链边界，不是终结符），条件区栈建模开启同族归约，栈上 `(Pending, A)` 时把 Pending 记为外链、A 仍作条件，窗口结果并入外链后统一折叠；②真值区改为「条件跳转之后到假值区入口」整段，并 `while` 剥掉末尾属于「真值区→假值区」边界的 keep-or-pop；③真值区/假值区重建全部 `fold_boolop_keep_or_pop=True` |
| ⑤ | 推导式生成 | `_detect_comp_ternary` 的两处臂重建（同文件 3189-3196、3232-3262） | 三元的**真值臂/假值臂自身**就是 keep-or-pop 链时（`x and y if c else z` 的 `x and y`、`x if c else y and z` 的 `y and z`、`(x or y) and (z or w)` 的 `z or w`），`reconstruct` 只返回栈顶尾操作数 | 三处 `reconstruct` 开启 `fold_boolop_keep_or_pop=True`（臂窗内无条件跳转族时逐位不变，C3） |

- 判据纪律：全部判据只读同层 opcode 与 `argval` 跳转目标（I.4 白名单：keep-or-pop 族操作码、跳转目标同窗性、`len(values)==len(ops)+1`），无名字/偏移阈值特判；`_fold_boolop_keep_or_pop` 默认 `False` ⇒ 既有全部调用路径（区域生成器、语句级重建）逐字节不变（C2/C3）；新增方法前缀 `_b242_` 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`（G3 口径）。
- 最小复现读数（本轮树实测）：
  - `/tmp/r45/w.py` 9 形态全部与源码逐字一致，`/tmp/r45/cmp.py` **`total diffs = 0`**（修复前 8）。
  - `/tmp/r45/w2.py` 17 形态：n1–n8、n10、n11、n13–n17 全部与源码一致，`total diffs = 15 → 3`（仅剩 n9、n12 两形态）。
  - 扩展对照 `/tmp/r45/w3.py`（9 形态，含 `(x or y) and (z and w)`、`not (x or y) and z`、三元臂内嵌推导式）：`total diffs 13 → 7`，六处退化（p1/p4/p6/p7/p8 及 p5 的左段）消失，零新增。
  - `/tmp/r45/v.py`（rr-v5r44 台账残差第一条：多目标赋值后 `print(da, db)`）：`total diffs = 0` ⇒ 该残差已被 `[B238-V3R42]` 覆盖，本轮无需再修。
- 门禁读数（本轮树实测）：
  - A/B（24 个 stdlib pyc：functools/logging/tempfile/enum/shutil/email.utils/http.client/string/dataclasses/dis/pathlib/os/json/textwrap/uuid/csv/calendar/copy/codecs/getpass/tokenize/difflib/random/pprint，HEAD `9450703b` vs 当前工作树）：文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 嵌套 `co_code`/`co_consts` 问题集 **143 == 143，`diff` 零差异**（`AB-BYTE-IDENTICAL`）⇒ 零回归、零副作用。
  - `quotation.pyc`：`scripts/pyc_verify.py single` 在本沙箱不可用（外部判据 `pylingual/equivalence_check.py` 缺失），改用 `run_batch_decompile.py` 的逐函数字节码比对口径：**152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有（HEAD 同败），old/new 读数逐行相同。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 4.11s`，两个失败为基线既有（`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`TestBoundaryConditions::test_BOUNDARY_02_large_function`）。
  - fuzz：`total=286 failures=0 stopped=time_budget workdir=/tmp/fuzz45`。
  - G5 的 402 语料/small34 分片在本沙箱仍不可达（pyc 索引为 Windows 绝对路径、small34 34 条中 33 条缺失），按环境性登记；G1/G3/G4/G6 读数不受本轮影响（四桶 395/0/719/442、mutation 样本 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED 均不变），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- **字典推导键位 keep-or-pop 链**（`{k and y or z: v for (k, v) in kv.items()}`）：`_detect_comp_ternary` 先以「Pending 三元」形态截获整窗（`/tmp/r45/probe_n9.py` 实测返回 `(PENDING(or,[y]) if k else v)`），未落到 `_split_dict_comp_kv`；即使落到，`_find_dict_kv_split_point` 的线性栈深模拟也不建模 keep-or-pop 的「短路保留左值 / 不短路弹出取右值」双路深度（实测切分点落入键中部）⇒ 键整体丢弃（`CODE-LEN n9: 16 vs 11`、`<dictcomp>: 17 vs 12`，产物 `{v: None for k, v in kv.items()}`）。同族值位形态 `{k: (a and b) or c}` 亦受影响。
- **过滤器回边**（`[x or y and z for x in xs if not (x and z)]`）：产物 `if x and not z`（语义错），`CODE-DIFF <listcomp> @14: POP_JUMP_FORWARD_IF_FALSE 20 vs POP_JUMP_BACKWARD_IF_FALSE 8`；属既有过滤器通道（`_extract_comp_ifs`），非本轮 keep-or-pop 引入。
- **三元 test 位自身是 keep-or-pop 链**（`[x and y if (z or w) else (y or x)]`）：条件区重建未开启同族归约，产物 `w if not z else y or x`。
- **顶层 and 链中夹嵌套 or 后仍有 and**（`[x and y and (z or w) and v]`）：扁平 `(ops, values)` 无法表达「or 属于第三个 and 操作数的子表达式」的层级，右结合折叠仍错（产物 `(z or w) and v`）；需要按跳转目标偏移做嵌套层级还原。
- **三元臂内嵌推导式**（`[[a or y and z for a in xs] if x or w else [x] for x in xs]`）：内层推导式整段丢失（`ONLY-ORIG <listcomp>/<listcomp>`）。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。

### rr-v5r46：字典推导式键位/值位 keep-or-pop 链归约（B243）（2026-10-26）

最小复现 `/tmp/r45/w2.py` 的 n9 与新建扩展对照 `/tmp/r45/x.py`（12 形态），全部为 CPython 3.11 对 dict 推导式键位/值位发射的短路链：

```python
def n9(kv, y, z):  return {k and y or z: v for (k, v) in kv.items()}
def q1(kv, y, z):  return {k and y or z: v for (k, v) in kv.items()}
def q2(kv, y, z):  return {k: y and k or z for k in kv}
def q3(kv, y, z):  return {k or y and z: v for (k, v) in kv.items()}
def q5(kv, y, z):  return {(k and y) or (z and k): v for (k, v) in kv.items()}
def q6(kv, y, z, w): return {k and y and z: v for (k, v) in kv.items()}
def q7(kv, y, z):  return {k: y or z for k in kv}
def q8(kv, y, z):  return {k if y else z: v for (k, v) in kv.items()}
def q9(kv, y, z):  return {k: y if k else z for k in kv}
def q10(kv, y, z): return {(k, y and z): v for (k, v) in kv.items()}
def q11(kv, y, z): return {k: (y and z) or k for k in kv}
def q12(kv, y, z): return {(k or y) and (z or k): v for (k, v) in kv.items()}
```

CPython 3.11 实证（`/tmp/r45/x.pyc` 内 `<dictcomp>` 反汇编，节选）：

```
q1  18 LOAD_FAST k; 20 POP_JUMP_FORWARD_IF_FALSE 26; 22 LOAD_DEREF y
    24 JUMP_IF_TRUE_OR_POP 28; 26 LOAD_DEREF z; 28 LOAD_FAST v; 30 MAP_ADD 2
q3  18 LOAD_FAST k; 20 JUMP_IF_TRUE_OR_POP 28; 22 LOAD_DEREF y
    24 JUMP_IF_FALSE_OR_POP 28; 26 LOAD_DEREF z; 28 LOAD_FAST v; 30 MAP_ADD 2
q7  12 LOAD_FAST k; 14 LOAD_DEREF y; 16 JUMP_IF_TRUE_OR_POP 20
    18 LOAD_DEREF z; 20 MAP_ADD 2
q12 18 LOAD_FAST k; 20 POP_JUMP_FORWARD_IF_TRUE 26; 22 LOAD_DEREF y
    24 JUMP_IF_FALSE_OR_POP 32; 26 LOAD_DEREF z; 28 JUMP_IF_TRUE_OR_POP 32
    30 LOAD_FAST k; 32 LOAD_FAST v; 34 MAP_ADD 2
```

修复前退化（HEAD `16df3198` 实测）：q1/q5/q12 → `{v: None for k, v in kv.items()}`（`CODE-LEN q1: 16 vs 11`、`<dictcomp> 17 vs 12`）；q2/q4 → `{k: z for k in kv}`；q3/q6/q10 → `{k: v for k, v in kv.items()}`；q7 → `{k: z for k in kv}`；q11 → `{k: k for k in kv}`；q8/q9 正确。读数：`/tmp/r45/x.py` **`total diffs = 20`**。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 推导式生成 | `_detect_comp_ternary`（`core/cfg/comprehension_generator.py` 3184-3201） | 键位链与经典三元同形（都以条件跳转起头、都以追加指令收尾），三元通道先截获整窗 ⇒ 键位链被当「Pending 三元」⇒ 键整体丢弃（`probe_n9.py` 实测 `TERN: (PENDING(or,[y]) if k else v)`） | 追加门：窗内（目标存储之后到追加指令之前）**含 keep-or-pop 且无任何无条件跳转** ⇒ 返回 `None` 交回 `_split_dict_comp_kv`。经典三元的真分支必以 `JUMP_FORWARD` 直落假值区（`q8`/`q9` 实证），故「无无条件跳转」精确封闭三元通道，`k if (a or b) else z` 不受影响（C3） |
| ② | 推导式生成 | `_find_dict_kv_split_point` 的栈深模拟（同文件 1748-1760） | 线性栈深模拟对 keep-or-pop 记 `delta=0`（短路保留左值）⇒ 键窗吞掉假值区首指令，切分点落入键中部 ⇒ 键退化为右段、值与 `MAP_ADD` 整体错位 | 记 **`delta=-1`**（取「不短路弹出」口径）：非短路径总是接在弹出后的落点继续求值，value 首条压栈指令恰落在 `depth==1 → 2` 边界上，切分点因此停在键链末尾 |
| ③ | 推导式生成 | `_split_dict_comp_kv` 的键窗/值窗重建（同文件 1673-1708） | 键窗或值窗自身是 keep-or-pop 链时，`reconstruct` 把 keep-or-pop 当无操作、只返回栈顶尾项 ⇒ `k and y or z` 退化为 `z`、`y and k or z` 退化为 `z` | 键窗/值窗先试 `_b237_kop_window`（rr-v5r45 整组归约）；未命中时按**链闭合位置**判定是否开启 `fold_boolop_keep_or_pop=True`：键位链的全部 keep-or-pop 目标 < 追加点（链在 value 起始前闭合），值位链的全部目标 == 追加点（链就是 value）。新增 `_is_value_kop_chain` / `_value_chain_key_split_point`，后者以「净栈效应 +1 且不含任何跳转的最长前缀末尾」定键边界 |
| ④ | 表达式重建 | `_b242_fold_boolop_pending`（`core/cfg/ast_generator_v2.py` 294-350） | rr-v5r45 的**右结合**折叠对「`or` 层内含 `and` 段」的混合链仍错（`(k or y) and (z or k)` 这类首跳为假出口的形态退回左折叠语义） | 重写为**布尔优先级递归下降**：先解析 `or` 层，每个 `or` 操作数再解析为 `and` 段；连续同运算符合并为同一 BoolOp 成员（保 `x and y and z` 扁平形态）。`len(values) != len(ops)+1` 即返回 `None`（C3） |

- 判据纪律：全部判据只读同层 opcode、`argval` 跳转目标与追加点偏移（I.4 白名单：keep-or-pop 族 / `MAP_ADD` / 无条件跳转族 / 栈净效应），无名字与偏移魔数特判；`fold_boolop_keep_or_pop` 默认 `False` ⇒ 元素位与语句级既有路径逐位不变（C2/C3）；新增方法 `_is_value_kop_chain` / `_value_chain_key_split_point` 六项 docstring 齐备，前缀无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`（G3 口径）。
- 负结果登记（本轮实测后回退）：曾试在 `_process_instruction` 为 `POP_JUMP_FORWARD_IF_FALSE/IF_TRUE` 建假出口模型（键位链首跳为假出口时用），使 `q12` 从「语义错」变为另一形态错误，但 `/tmp/r45/w3.py` 由 7 处回归到 **9** 处（`p4` `[w if not z else y or x ...]` → `[y or x ...]`、`p6` 同形、`p9` 内层推导式丢失）⇒ **该分支已回退删除**，元素位通道的 POP_JUMP 语义留作下一族在独立通道内处理。
- 最小复现读数（本轮树实测）：
  - `/tmp/r45/w2.py`：n9 恢复 `{k and y or z: v for k, v in kv.items()}`，`total diffs 3 → 2`（仅剩 n12 过滤器回边 + 一处元素位 keep-or-pop）。
  - `/tmp/r45/x.py`（本轮新建，12 形态）：`total diffs 20 → 1`。q1/q3/q5/q6/q7/q8/q9/q10 与源码逐字一致；q2/q4 产物 `{k: y and k or z for k in kv}`、q11 `{k: y and z or k for k in kv}`（源码带括号，语义等价）；q12 仍为 `{y and z or k: v ...}`（源码 `{(k or y) and (z or k) ...}`，语义错，见残差）。
  - `/tmp/r45/w.py` `total diffs = 0`；`/tmp/r45/v.py` `total diffs = 0`；`/tmp/r45/w3.py` 回退后恢复 `total diffs = 7`（与 rr-v5r45 持平，零新增）。
- 门禁读数（本轮树实测）：
  - A/B（同 24 个 stdlib pyc，rr-v5r45 产物 `16df3198` vs 当前工作树）：文本 **24/24 逐字节相同**；`/tmp/ab/bytecmp.py` 嵌套 `co_code`/`co_consts` 问题集 **143 == 143，`diff` 零差异**（`AB-BYTE-IDENTICAL`）⇒ 零回归、零副作用。
  - `quotation.pyc`：`scripts/pyc_verify.py single` 在本沙箱仍不可用（外部判据缺失），`run_batch_decompile.py` 逐函数字节码比对口径 **152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有，old/new 读数逐行相同。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 3.94s`，两个失败为基线既有。
  - fuzz：`total=288 failures=0 stopped=time_budget workdir=/tmp/fuzz46`。
  - G5 的 402 语料/small34 分片在本沙箱仍不可达（Windows 绝对路径索引），按环境性登记；G1/G3/G4/G6 读数不受本轮影响（四桶 395/0/719/442、mutation 样本 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- **键位链首跳为假出口（`POP_JUMP_FORWARD_IF_TRUE`）**：`q12` = `{(k or y) and (z or k): v ...}`，`_b237_kop_window` 只接受 IF_FALSE 型首跳 ⇒ 返回 `None` ⇒ 回落 `reconstruct(fold_boolop_keep_or_pop=True)`，而该开关只建模 keep-or-pop、不建模 POP_JUMP ⇒ 首项 `k` 与 `y` 的 `or` 关系丢失（产物 `{y and z or k: v ...}`）。修复须在**键/值窗独立通道**内建模假出口（元素位通道的同类建模已实测导致 `w3` 的 p4/p6/p9 回归，不能复用）。
- **过滤器回边**（`[x or y and z for x in xs if not (x and z)]`，n12）：产物 `if x and not z`（语义错），`CODE-DIFF <listcomp> @14: POP_JUMP_FORWARD_IF_FALSE 20 vs POP_JUMP_BACKWARD_IF_FALSE 8`；属既有过滤器通道（`_extract_comp_ifs`），非本轮引入。
- **三元 test 位自身是 keep-or-pop 链**（`[x and y if (z or w) else (y or x)]`，p4）：条件区重建未开启同族归约，产物 `w if not z else y or x`。
- **顶层 and 链中夹嵌套 or 后仍有 and**（`[x and y and (z or w) and v]`，p5）：扁平 `(ops, values)` 无法表达「or 属于第三个 and 操作数的子表达式」的层级，优先级折叠仍错（产物 `(z or w) and v`）；需按跳转目标偏移做嵌套层级还原。
- **三元臂内嵌推导式**（`[[a or y and z for a in xs] if x or w else [x] for x in xs]`，p9）：内层推导式整段丢失（`ONLY-ORIG <listcomp>/<listcomp>`）。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。

### rr-v5r47：dict 推导式键/值位「假出口短路链」归约（B244）（2026-10-26）

最小复现 `/tmp/r47/y.py`（8 形态）与上一轮对照 `/tmp/r45/x.py` 的 q12：

```python
def q12(kv, y, z):  return {(k or y) and (z or k): v for (k, v) in kv.items()}
def r1(kv, y, z, w): return {k: (y or z) and w for k in kv}
def r2(kv, y, z, w): return {k: (y and z) or w for k in kv}
def r3(kv, y, z, w): return {(k or y) and z: v for (k, v) in kv.items()}
def r4(kv, y, z, w): return {(k and y) or z: v for (k, v) in kv.items()}
def r5(kv, y, z, w): return {k: (y or z) and (w or k) for k in kv}
def r6(kv, y, z, w): return {(k or y or z) and w: v for (k, v) in kv.items()}
def r7(kv, y, z, w): return {(k or y) and z and w: v for (k, v) in kv.items()}
def r8(kv, y, z, w): return {k: (y or z) and w and k for k in kv}
```

CPython 3.11 实证（`/tmp/r47/y.pyc` 的 `<dictcomp>`，节选）：

```
r1  12 LOAD_FAST k; 14 LOAD_DEREF y; 16 POP_JUMP_FORWARD_IF_TRUE 22
    18 LOAD_DEREF z; 20 JUMP_IF_FALSE_OR_POP 24; 22 LOAD_DEREF w; 24 MAP_ADD 2
r4  18 LOAD_FAST k; 20 POP_JUMP_FORWARD_IF_FALSE 26; 22 LOAD_DEREF y
    24 JUMP_IF_TRUE_OR_POP 28; 26 LOAD_DEREF z; 28 LOAD_FAST v; 30 MAP_ADD 2
r6  18 LOAD_FAST k; 20 POP_JUMP_FORWARD_IF_TRUE 30; 22 LOAD_DEREF y
    24 POP_JUMP_FORWARD_IF_TRUE 30; 26 LOAD_DEREF z
    28 JUMP_IF_FALSE_OR_POP 32; 30 LOAD_DEREF w; 32 LOAD_FAST v; 34 MAP_ADD 2
```

修复前退化（HEAD `e48c6bf2` 实测）：`q12` → `{y and z or k: v ...}`；`r1` → `{k: z and w ...}`；`r3` → `{y and z: v ...}`；`r5` → `{k: z and w or k ...}`；`r7` → `{y and z and w: v ...}`；`r8` → `{k: z and w and k ...}`；`r2`/`r4` 已正确（纯 keep-or-pop 通道）。读数：`/tmp/r47/y.py` **`total diffs = 10`**、`/tmp/r45/x.py` **`total diffs = 1`**。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 推导式生成 | 新增 `ComprehensionGenerator._dict_shortcircuit_chain`（`core/cfg/comprehension_generator.py` 1768-1881） | 结果位置上的 `(X or A) and R` / `(X and A) or R` 在 X 已能决定内层结果时不需要保留 X（外层只看真值），CPython 发**弹跳**假出口（`POP_JUMP_FORWARD_IF_TRUE/_IF_FALSE`）直落 rest，而非 keep-or-pop ⇒ `_b237_kop_window` 只收 IF_FALSE 型首跳、通用重建器只把 keep-or-pop 记成扁平 `and`/`or` 链 ⇒ 首项 X 被丢弃 | 判据（I.4 白名单）：首个条件跳转为弹跳型假出口且 `j.offset < t <= merge_offset`；`t` 前那段非空且**末条**为同汇合点 keep-or-pop（`argval == merge_offset`）；rest 段非空且不含假出口。归约：首跳极性给内层运算符（IF_TRUE ⇒ `or`、IF_FALSE ⇒ `and`），段末 keep-or-pop 极性给外层（IF_FALSE_OR_POP ⇒ `and`、IF_TRUE_OR_POP ⇒ `or`），X/A/rest 三段各自整组重建后合成 `(X <inner> A) <outer> rest` |
| ② | 推导式生成 | `_split_dict_comp_kv` 的键/值窗接入（同文件 1687-1720） | 键位的汇合点是 **value 起始**（键链在 value 之前闭合），而原 `_append_off` 取的是 `MAP_ADD` 偏移 ⇒ 段末 keep-or-pop 的 `argval`（= 键汇合点）与它不等，通道恒不命中 | 键窗先试 `_b237_kop_window` → `_dict_shortcircuit_chain(key_instrs, 键窗末尾指令偏移)`；值窗先试 `_b237_kop_window` → `_dict_shortcircuit_chain(value_instrs, 追加点偏移)`；键窗末尾偏移取 `filtered_instrs[best_key_end].offset`（键窗占满整窗时回落追加点）。`_key_chain` 的同族归约判据仍用追加点偏移（`i.argval < append`），与上轮语义一致 |
| ③ | 表达式重建 | 新增 `_single` 局部整组重建（同文件 1813-1832） | 段窗常以「追加点就是窗末」收尾，`_process_instruction` 逐条处理后 `BoolOpPending` 与右操作数仍分列栈顶两项 ⇒ 段重建返回 None（实测首版 q12 通道恒不命中） | 与 `reconstruct` 同口径：先收集窗内 keep-or-pop 跳转目标，到汇合点先 `_b242_flush_boolop_pending()`，循环结束再 flush 一次；过滤 `PUSH_NULL` 后**要求栈上恰一项**，否则返回 None（避免静默丢弃前导项） |

- 判据纪律：全部判据只读同层 opcode、`argval` 跳转目标、窗内偏移与汇合点位置（I.4 白名单：弹跳假出口族 / keep-or-pop 族 / 无条件跳转族），无名字与偏移魔数特判；新增方法 `_dict_shortcircuit_chain` 六项 docstring 齐备，前缀无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`（G3 口径）；通道未命中即返回 `None` 逐字回落既有路径（C3）；元素位通道（`w3` 的 p4/p6/p9）不经过本通道，上轮登记的回退缺陷不再复现。
- 最小复现读数（本轮树实测）：
  - `/tmp/r47/y.py`（8 形态）：`total diffs 10 → 2`，r1/r3/r4/r5/r7/r8 与源码逐字一致，r2 为 `{k: y and z or w ...}`（源码带括号，语义等价）；仅 r6（`(k or y or z) and w`，段内还有第二个假出口）仍退化。
  - `/tmp/r45/x.py`（12 形态）：`total diffs 1 → 0`，q12 恢复 `{(k or y) and (z or k): v for k, v in kv.items()}`。
  - 回归集持平：`/tmp/r45/w.py` `0`、`w2.py` `2`、`w3.py` `7`、`v.py` `0`（与 rr-v5r46 逐项相同，零新增）。
- 门禁读数（本轮树实测）：
  - A/B（同 24 个 stdlib pyc，rr-v5r46 产物 `e48c6bf2` vs 当前工作树）：文本 **24/24 逐字节相同**；`bytecmp` 问题集 **143 == 143，`diff` 零差异**（`AB-BYTE-IDENTICAL`）。
  - `quotation.pyc`：`run_batch_decompile.py` 口径 **152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 3.79s`，两个失败为基线既有。
  - fuzz：`total=290 failures=0 stopped=time_budget workdir=/tmp/fuzz47`。
  - G5 的 402 语料/small34 分片在本沙箱仍不可达；G1/G3/G4/G6 读数不变（四桶 395/0/719/442、mutation 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。

#### 本轮新暴露残差（未修，下一族）

- **段内多个假出口**（r6 `{(k or y or z) and w: v ...}`）：首个假出口到 rest 起点（`t`）之间的段内还有第二个 `POP_JUMP_FORWARD_IF_TRUE`，段重建 A 时栈上留下两项以上 ⇒ 违反「恰一项」要求 ⇒ 整条通道返回 None，回落通用重建器，产物 `{z and w: v ...}`。修复方向：把「段」按假出口递归解析（每个假出口切出一段 `X <op> A`），或将整窗交给按跳转目标做层级还原的布尔解析器。→ **rr-v5r48 已修**（见下节）。
- **过滤器回边**（`[x or y and z for x in xs if not (x and z)]`，n12）：产物 `if x and not z`（语义错）；属既有过滤器通道（`_extract_comp_ifs`）。**已由 rr-v5r49 修复**（恢复 `if not x or not z`）。
- **三元 test 位自身是 keep-or-pop 链**（`[x and y if (z or w) else (y or x)]`，p4）：条件区重建未开启同族归约，产物 `w if not z else y or x`。
- **顶层 and 链中夹嵌套 or 后仍有 and**（`[x and y and (z or w) and v]`，p5）：扁平 `(ops, values)` 无法表达层级，产物 `(z or w) and v`。
- **三元臂内嵌推导式**（`[[a or y and z for a in xs] if x or w else [x] for x in xs]`，p9）：内层推导式整段丢失（`ONLY-ORIG <listcomp>/<listcomp>`）。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。

### rr-v5r55：链式 test 三元 + merge 后缀 keep-or-pop 链整组归约（B250）（2026-10-26）

最小复现：三元 test 位语料 `/tmp/r53/tcorpus.py` 的 `tern_nest` 宿主（`[("p" if <链> else "q") and z for x in xs]`）。HEAD `2962358a` 读数 **144 bad**，其中 `tern_nest` 48。

CPython 3.11 实测（同文件 `t003`/`t011`/`t019` 的 `<listcomp>`）：

```
t003 ("p" if x and y else "q") and z
  12 x; 14 POP_JUMP_FORWARD_IF_FALSE 24; 16 y; 18 POP_JUMP_FORWARD_IF_FALSE 24
  20 'p'; 22 JUMP_FORWARD 26; 24 'q'; 26 JUMP_IF_FALSE_OR_POP 30; 28 z; 30 LIST_APPEND
t011 ("p" if x or y else "q") and z
  12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 POP_JUMP_FORWARD_IF_FALSE 24
  20 'p'; 22 JUMP_FORWARD 26; 24 'q'; 26 JUMP_IF_FALSE_OR_POP 30; 28 z; 30 LIST_APPEND
t019 ("p" if x and z else "q") and z
  12 x; 14 POP_JUMP_FORWARD_IF_FALSE 24; 16 z; 18 POP_JUMP_FORWARD_IF_FALSE 24
  20 'p'; 22 JUMP_FORWARD 26; 24 'q'; 26 JUMP_IF_FALSE_OR_POP 30; 28 z; 30 LIST_APPEND
```

| 编号 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|
| ① | `_detect_comp_ternary` 末尾新增 `[B250-V3R55]` 段（`core/cfg/comprehension_generator.py` 4605 起） | 既有 `[B236-V3R39]` 通道只接「单段整窗」的 plain cond（`_b236_plain_cond` 为真、`cond_instrs` 重建后栈上有**前导压栈项**）；链式 test 的 `cond_instrs` 各段本身就是 test 操作数，不能当前导项 ⇒ 该通道恒不命中 ⇒ 产物只剩裸 IfExp，`and z` 整段丢失（`t003` 产物 `['p' if x and y else 'q' for x in xs]`，`CODE-LEN 17 vs 15`、`COPY_FREE_VARS 2 vs 1`） | 识别条件：`not _b236_plain_cond`（链式 test）+ `merge < append` + merge 块首指令 ∈ `{JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP}` + 追加点非 `MAP_ADD`（dict 键/值位另有专门通道）。归约：以三元值单独作初栈、开启 `_fold_boolop_keep_or_pop` 逐条处理 `all_instrs[_merge_block_idx:append_idx]` 后缀，栈上恰一项即整组结果；否则逐字返回裸 IfExp（C3 封闭） |

- 判据纪律（I.4 白名单）：只读同层 opcode 与段/块边界（merge 块首指令族、追加点 opcode），无用户名/常量值特判、无偏移魔数、无链长上限；不满足条件一律返回裸 IfExp ⇒ 既有通道不变（C3）。本段未新增方法（G3 零新增前缀方法合规）、无硬编码深度上限（G4）。
- 读数（本轮树实测）：
  - 三元 test 位语料 `tcorpus.py`（384 函数）：**144 → 96**（净修复 48、零新增；`tern_nest` 48 → 0）。
  - 元素位语料 `corpus.py`（1440 函数）：**0 → 0**；形态回归集 `a.py`/`w.py`/`w2.py`/`w3.py` 全 `bad funcs = 0`；边界探针 `edge.py` 问题集 **2 == 2**（`e31`/`e39`，HEAD 既有）。
  - A/B 24 个 stdlib pyc：两树各 24/24 退出码 0，`diff -r` 逐字节相同；`quotation.pyc` **152 函数 / 151 完全匹配**（唯一失败 `datetimeindex_astype.<lambda>` 为基线既有，base58 树同读数）；pytest 七套件 `2 failed / 282 passed / 2 xpassed`（两项为基线既有）；fuzz `total=298 failures=0 stopped=time_budget`。
  - G1/G3/G4/G6 读数不变（四桶 395/0/719/442、mutation 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。
- 残差（96 例，两族）：
  - `tern_in_and` **48**（`[z and ("p" if <链> else "q") for x in xs]`）：CPython 把前缀操作数放在 **test 之前**（`12 z; 14 JUMP_IF_FALSE_OR_POP 30`，合并点 30 即追加点），test 窗不含该跳转 ⇒ `[B250-V3R55]` 的 merge 块门不接管，前缀 `z and` 整段丢失（产物 `['p' if x and y else 'q' ...]`）。
  - `tern_elt_cond` **48**（`[(1 if <链> else 0) if w else 2 for x in xs]`）：内层三元的真/假两臂 `JUMP_FORWARD 34` **跨过**外层假值区起点 32 的 `2` ⇒ 外层窗内同时存在两个 merge（内层 34、外层 34），现通道只认单一 merge（产物 `[1 if w else 2 ...]`，内层三元整段丢失）。

### rr-v5r54：三元 test 位「链尾唯一性门」+ jump_if 文法通道接入（B249 续修）（2026-10-26）

最小复现：三元 test 位语料 `/tmp/r53/tcorpus.py` 的 `tern`/`tern_s`/`tern_and`/`tern_gen`/`tern_dictv` 五宿主各 2 例残差（`(x or y) and z or (w and v)`、`x and (y or z) or w`）。HEAD `132b9d7d` 读数 **154 bad**。

CPython 3.11 实测（`/tmp/r53/tcorpus.py` 的 `t265`/`t321` `<listcomp>`）：

```
t265 (x or y) and z or (w and v)
  12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 POP_JUMP_FORWARD_IF_FALSE 24
  20 z; 22 POP_JUMP_FORWARD_IF_TRUE 32; 24 w; 26 POP_JUMP_FORWARD_IF_FALSE 36
  28 v; 30 POP_JUMP_FORWARD_IF_FALSE 36; 32 'p'; 34 JUMP_FORWARD 38; 36 'q'; 38 LIST_APPEND
t321 x and (y or z) or w
  12 x; 14 IF_FALSE 24; 16 y; 18 IF_TRUE 28; 20 z; 22 IF_TRUE 28
  24 w; 26 IF_FALSE 32; 28 'p'; 30 JUMP_FORWARD 34; 32 'q'; 34 LIST_APPEND
```

| 编号 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|
| ① | `_b248_ternary_test_chain`（`core/cfg/comprehension_generator.py` 3216 起） | 自末跳向前逐条尝试时，**中间跳转**的下一条指令恰是某段起点，却被当作「真值区起点」⇒ 链在链中被截断收尾。实测 `t265` 在 `IF_TRUE 32`（offset 22，非链尾）处收尾，产物 test 退化为 `(not x and not y) or not z`、真值/假值臂错位（`elt = v`、`orelse = 'q'`） | 新增链尾唯一性门：段由跳转切分 ⇒ 任何非末跳的下一条指令必是段起点；`_true_off` 落在这些段起点上即 `continue`（不接管该候选） |
| ② | 新增 `_b249_test_boolchain`（同文件 3128 起，五项 docstring）＋调用点 | ①之后 test 位窗内**全部是假出口弹跳**（无 keep-or-pop 族），`_b237_kop_window`/`_b247_mixed_boolchain` 恒返回 None ⇒ 回落到「单段/共享假出口」通道只取 `x and y`（产物 `("p" if x and y else "q") and z`） | 取 test 窗内全部前向条件跳转为段边界，`next` = 末跳 `argval`（假值区入口）、`tail` = 末跳后一条指令偏移（真值区起点），要求 `tail < next` 且 `[seg_start, 末跳)` 内无无条件跳转；交 `_b249_jumpif_boolchain` 按 `compiler_jump_if` 文法反向解析 |

- 判据纪律（I.4 白名单）：只读同层 opcode、跳转 `argval` 落点与段边界；无用户名/常量值特判、无偏移魔数、无链长上限；`tail >= next`、含无条件跳转、跳转少于两条、落点不匹配一律返回 `None` 逐字回落（C3）；新方法前缀合规（G3）、无硬编码深度上限（G4）、五项 docstring 齐备。
- 读数（本轮树实测）：
  - 三元 test 位语料 `tcorpus.py`（384 函数）：**154 → 144**（净修复 10、零新增；`tern`/`tern_s`/`tern_and`/`tern_gen`/`tern_dictv` 五个宿主各 2 → 0）。
  - 元素位语料 `corpus.py`（1440 函数）：**0 → 0**；形态回归集 `a.py`/`w.py`/`w2.py`/`w3.py` 全 `bad funcs = 0`；边界探针 `edge.py` 问题集 **2 == 2**（`e31`/`e39`，HEAD 既有）。
  - A/B 24 个 stdlib pyc：`diff -r` **24/24 逐字节相同**；`quotation.pyc` **152 函数 / 151 完全匹配**（失败项为基线既有）；pytest 七套件 `2 failed / 282 passed / 2 xpassed`；fuzz `total=296 failures=0`。
  - G1/G3/G4/G6 读数不变（四桶 395/0/719/442、mutation 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。
- 复核后残差：**三元嵌在元素位布尔链内** 144 例（`tern_nest` `("p" if <链> else "q") and z`、`tern_in_and` `z and ("p" if <链> else "q")`、`tern_elt_cond` `(1 if <链> else 0) if w else 2`，各 48）：窗内 `JUMP_FORWARD` 与 `JUMP_IF_FALSE_OR_POP` 使②的「无无条件跳转」门按设计不接管，且 `_b237_kop_window` 的 keep-or-pop 后缀通道未覆盖「三元 + 链后缀」整组；过滤器位链内三元（`edge.py` 的 e31/e39）同源；既有残差不变。

### rr-v5r53：推导式过滤器位布尔链「三通道」整组归约（B249）（2026-10-26）

最小复现：元素位语料 `/tmp/r53/gen.py`（24 条布尔链 × 7 后缀 `plain/mod/sub/not/call/cmp/tuple` × 宿主 `list/set/gen/if` + `plain` 后缀的 `dictk/dictv`，共 **1440** 函数）。HEAD `ef91ddc5` 读数 **244 bad**，全部落在 `if` 宿主：`call/cmp/mod/sub/tuple` 各 48、`not`/`plain` 各 2；元素位/键位/值位/集合/生成器宿主全 0。

CPython 3.11 实测（`/tmp/r53/corpus.py` 各 `<listcomp>` 过滤窗，节选偏移）：

```
t1203 (x and (y or z) or w)
  12 x; 14 POP_JUMP_FORWARD_IF_FALSE 24; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 28
  20 z; 22 POP_JUMP_FORWARD_IF_TRUE 28; 24 w; 26 POP_JUMP_BACKWARD_IF_FALSE 8 → 元素 28
t993 ((x or y) and z or (w and v))
  12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 POP_JUMP_FORWARD_IF_FALSE 24
  20 z; 22 POP_JUMP_FORWARD_IF_TRUE 32; 24 w; 26 POP_JUMP_BACKWARD_IF_FALSE 8
  28 v; 30 POP_JUMP_BACKWARD_IF_FALSE 8 → 元素 32
t1007 = not ((x or y) and z or (w and v))  12 x; 14 IF_TRUE 20; 16 y; 18 IF_FALSE 24
  20 z; 22 POP_JUMP_BACKWARD_IF_TRUE 8; 24 w; 26 POP_JUMP_FORWARD_IF_FALSE 32
  28 v; 30 POP_JUMP_BACKWARD_IF_TRUE 8 → 元素 32
t1217 = not (x and (y or z) or w)         12 x; 14 IF_FALSE 24; 16 y; 18 BACK_IF_TRUE 8
  20 z; 22 BACK_IF_TRUE 8; 24 w; 26 BACK_IF_TRUE 8 → 元素 28
```

⇒ 过滤位（`compiler_jump_if(E, if_cleanup, 0)`）的链**全部是假出口弹跳**（`POP_JUMP_FORWARD_IF_TRUE/IF_FALSE`），没有 keep-or-pop 族；`not (...)` 只把整棵文法的 `cond` 翻转（`UnaryOp Not` 分支），跳转极性随之内外互换（t1007/t1217）。

文法依据（`/tmp/r53/compile311.c` 的 `compiler_jump_if`，2897–2991 行）：

```
compiler_jump_if(E, next, cond):
  Not    → compiler_jump_if(operand, next, !cond)
  BoolOp → cond2 = (op == Or);
           next2 = (cond2 != cond) ? 新建块（位置在本组最后一个成员之后） : next
           前 n-1 成员: compiler_jump_if(member, next2, cond2)
           末成员:      compiler_jump_if(member, next,  cond)
  default→ <value>; POP_JUMP_IF_{TRUE,FALSE} next
```

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 过滤位逐段 | `_extract_comp_ifs` 逐段重建（`core/cfg/comprehension_generator.py` 2598 起） | 段内可能含前导压栈项（`'%s' % (x and y)` 的 `'%s'`）与 keep-or-pop 族，逐段 `reconstruct` 未开同族开关 ⇒ 前导项静默留在栈上、链首操作数被后继二元运算当操作数（产物 `if x % y`） | 逐段重建开启 `fold_boolop_keep_or_pop=True`；汇合点 flush 成 BoolOp、前导项按正常栈序参与后续消费（净修复 **110**） |
| ② | 过滤位整窗 | 同上，`_b245_comp_filter_chain` 之后 | 段收集只在**终结跳转**处切段 ⇒ 窗内混合链的弹跳目标落在「另一段起点」，而段切分不认这些起点 ⇒ `_b245` 落点分类失败、逐段重建只看到被切碎的前导项 | 自 `append_idx-1` 向前取最后一个条件跳转为 `term`；其落点为「跳过本轮」（`BACKWARD` 或 `argval >= append_offset`）时把 `all_instrs[store_idx+1:term]` 整窗交给 `_b237_kop_window`（入口先调 `_b247_mixed_boolchain`），命中即整组归约、元素起点定为 `term+1`（净修复 **130**） |
| ③ | 过滤位纯弹跳 | 新增 `_b249_jumpif_boolchain`（同文件 2938 起，六项 docstring）＋ `_b249_filter_boolchain`（3089 起） | ②的窗内**没有** keep-or-pop 时（t993/t1203/t1007/t1217 四条纯弹跳链）`_b237_kop_window`/`_b247_mixed_boolchain` 恒返回 None（两器都要求 keep-or-pop 族至少一条） | 按上表文法自顶向下 `_parse(i, end, next, cond)` 反向解析「段 + 跳转」序列：叶子要求 `argval == next`，`cond=1` 取「跳转已发生」谓词（`_taken`）、`cond=0` 取其取反（`_falsified`，已化简双重取反）；多段枚举 `cond2 ∈ {0,1}` 与成员数 k，`next2 = next`（`cond2 == cond`）或「组末成员之后的段起点」（否则），前 k-1 成员以 `(next2, cond2)` 递归、末成员以 `(next, cond)` 递归，同运算符按结合律并入同一 `BoolOp`；顶层 cond=0 失败而 cond=1 成功时包 `not`（文法含义 = 源码的 `not (...)`）（净修复 **4**） |

- 判据纪律（I.4 白名单）：全部判据只读同层 opcode、跳转 `argval` 落点与段边界（keep-or-pop 族 / 弹跳族 / 无条件跳转族 / 段起点集合），无用户名与常量值特判、无偏移魔数、无链长上限；段必须自 `store_idx+1` 起**连续无洞**到 `term`、窗内不得含无条件跳转，任一不满足即返回 `None` 逐字回落既有通道（C3 显式封闭）；新增方法前缀无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`（G3），无硬编码深度上限（G4），六项 docstring 齐备。
- 最小复现读数（本轮树实测）：
  - 元素位语料 `/tmp/r53/corpus.py`（1440 函数）：**244 → 0**（净修复 244，零新增）。产物示例：`t1203 → if x and (y or z) or w`、`t993 → if (x or y) and z or w and v`、`t1007 → if (not x and not y or not z) and (not w or not v)`、`t1217 → if (not x or not y and not z) and not w`（De Morgan 形态，重编译字节码逐条相同）。
  - 三元 test 位语料 `/tmp/r53/tcorpus.py`（384 函数）：**154 → 154**（不变，零回归）。
  - 形态回归集 `a.py`(18) / `w.py`(9) / `w2.py`(17) / `w3.py`(9) 全部 `bad funcs = 0 / 0`；边界探针 `/tmp/r53/edge.py`（40 形态：双 `if` 子句、多 `for` 子句、walrus、链式比较、`is None`/`not in`、嵌套推导式、async 宿主等）问题集 `2 == 2`（`e31 if (a if b else c) and b`、`e39 if a and (b if c else a)`，均为 HEAD 既有、本轮未变）。
- 门禁读数（本轮树实测）：
  - A/B（同 24 个 stdlib pyc：`argparse/ast/base64/bisect/calendar/cmd/codecs/configparser/contextlib/copy/csv/dataclasses/datetime/decimal/difflib/enum/fnmatch/fractions/functools/gettext/gzip/heapq/inspect/io`，HEAD `ef91ddc5` 树 vs 当前工作树）：文本 `diff -r` **24/24 逐字节相同**。
  - `quotation.pyc`：`run_batch_decompile.py` 口径 **152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有（HEAD 同败）。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 3.83s`，两个失败为基线既有。
  - fuzz：`total=289 failures=0 stopped=time_budget`。
  - G5 的 402 语料/small34 分片在本沙箱仍不可达（pyc 缺失）；G1/G3/G4/G6 读数不变（四桶 395/0/719/442、mutation 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。

#### 本轮复核后仍存残差（未修，下一族）

- **过滤器位布尔链内的三元**（`if (a if b else c) and b`、`if a and (b if c else a)`，`edge.py` 的 e31/e39）：窗内含无条件跳转 ⇒ ③ 通道按设计不接管，产物丢链并整段退化（`CODE-LEN 18 vs 16`、`CODE-DIFF @8: FOR_ITER 36 vs FOR_ITER 32`）；HEAD 同形，**非本轮引入**。
- **三元 test 位上的两条混合链**（`(x or y) and z or (w and v)`、`x and (y or z) or w`）：在 `if` 宿主已由本轮修复，但在 test 位仍残留 10 例（见 rr-v5r52 节）。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。

### rr-v5r52：推导式三元 test 位短路跳转链整组归约（B248）（2026-10-26）

最小复现：三元 test 位语料 `/tmp/r53/gent.py` → `/tmp/r53/tcorpus.py`（**384** 函数 = 8 组后缀 `tern/tern_s/tern_and/tern_gen/tern_dictv/tern_nest/tern_in_and/tern_elt_cond` × 48 条链）。

- 现象：HEAD 上两读数分别是 **349 bad / 384**（rr-v5r51 树 `c472add8`）与 **154 bad / 384**（引入本修复后）。分布：`tern`/`tern_s`/`tern_and`/`tern_gen`/`tern_dictv` 各 41→2；`tern_elt_cond`/`tern_in_and`/`tern_nest` 各 48（不变量，见残差）。
- 根因：既有 `[R67-fix2]` 只接受「全部中间跳转共享同一假出口」的 **and** 链（`x and y`）；`or` 链（共享同一**真**出口）、and/or 混排链、以及「子组落点 = 另一段起点」的握手嵌套一律回落单段重建 ⇒ 链上操作数整段丢失或只取末项。
- 修复：新增 `_b248_ternary_test_chain(all_instrs, seg_start, append_idx)`（同文件 3128 起）＋ `_b248_chain_parse(segs, jumps, dests)`（3205 起）。
  - 跳转收集：段窗内**非 BACKWARD**且有 `argval` 的条件跳转；少于 2 条即返回 None（单段交既有通道）。
  - 切分：自末跳向前取 `_true_off = all_instrs[last+1].offset`、`_false_off = all_instrs[last].argval`，要求 `_true_off < _false_off`；据此把段窗切成 `_segs`，建段起始偏移 → 序号的 `_starts` 表。
  - 落点分类：`'pass'`（== `_true_off`，条件成立落穿到真值区）/ `'skip'`（== `_false_off`，落假值区）/ **握手**（落在窗内另一段起点且序号 > 当前段）。
  - 递归：`_not`（`¬(not X)` → `X`，避免多发射 `UNARY_NOT`）、`_cmp`（`is None` / `is not None`）、`_combine`（同运算符右链并入）；`_taken` 按 `IF_NOT_NONE`/`IF_NONE`/`IF_TRUE`/else 给项，`_falsified = [_not(t)]`；末段取 `_falsified`，`'pass'` ⇒ `_combine('or', _taken[i], rest)`，`'skip'` ⇒ `_combine('and', _falsified[i], rest)`，握手 `j` ⇒ 末段落 `'skip'` 记 or 组 `T_i … ¬T_{j-1}`、落 `'pass'` 记 and 组 `¬T_i … T_{j-1}`。
  - 接入点：`_detect_comp_ternary` 的 test 位重建（3984 行 `_b248` 调用），未命中回 `None` 逐字沿用既有通道（C3）。
- 判据纪律：只读同层 opcode、跳转 `argval` 与段边界（I.4 白名单），无名字/偏移魔数；`_b248_chain_parse` 六项 docstring 齐备；无 `_fix_/_merge_/_patch_/_fallback_` 前缀（G3）、无硬编码深度上限（G4）。
- 读数（本轮树实测）：`tcorpus.py` **349 → 154**（净修复 195，零新增）；元素位语料 `0 → 0`；形态回归集 `a/w/w2/w3` 全 `0`。（本修复的 A/B 未被单独复测；rr-v5r53 节的 24/24 为 `ef91ddc5` 树与当前工作树对比，覆盖了本修复的树。）
- 复核后残差：**三元嵌在布尔链内** 144 例（`tern_nest` `(... if <链> else ...) and z`、`tern_in_and` `z and (... if <链> else ...)`、`tern_elt_cond` `(1 if <链> else 0) if w else 2`，各 48）；**test 位的两条混合链** 10 例（`(x or y) and z or (w and v)` 与 `x and (y or z) or w`，在 `tern/tern_s/tern_and/tern_gen/tern_dictv` 各 2）——后者在 `if` 宿主已由 rr-v5r53 修复，test 位需同一 `compiler_jump_if` 文法通道（与 `_b249_jumpif_boolchain` 同源）接入。

### rr-v5r51：元素位混合布尔链「统一帧栈」整组归约（B247）（2026-10-26）

最小复现 `/tmp/r51/a.py`（18 形态，元素位「keep-or-pop + 假出口弹跳」混排 / 窗首三元前缀 / 后缀运算）：

```python
def a1(xs, x, y, z, w): return [x and (y or z) and w for x in xs]
def a2(xs, x, y, z, w): return [(x or y) and z or (w and v) for x in xs]
def a3(xs, x, y, z, w): return [x and y and (z or w) and v for x in xs]
def a4(xs, x, y, z, w, v): return [x and (y or z) and w and v for x in xs]
def a5(xs, x, y, z, w, v): return [(x or y) and (z or w) and v for x in xs]
def a6(xs, x, y, z, w, v): return [((x or y) and z) and (w or v) for x in xs]
def a7(xs, x, y, z, w, v): return ['%s' % (x and (y or z) and w) for x in xs]
def a8(xs, x, y, z, w, v): return [(x and (y or z) and w) - 1 for x in xs]
def a9(xs, x, y, z, w): return [not (x and (y or z) and w) for x in xs]
def b1(xs, x, y, z, w): return [(x or y or z) and w for x in xs]
def b2(xs, x, y, z, w): return [x and (y or z or w) for x in xs]
def b3(xs, x, y, z, w, v): return [(x or y) and z and (w or v) for x in xs]
def b4(xs, x, y, z, w, v): return [(x and y) or (z and w) or v for x in xs]
def b5(xs, x, y, z, w, v): return [(x and y) or z and (w or v) for x in xs]
def b6(xs, x, y, z, w, v): return [x or (y or z) and (w and v) for x in xs]
def b7(xs, x, y, z): return [(x and y) or (z or x) for x in xs]
def b8(xs, x, y, z, w): return [('p' if x else 'q') and (y or z) and w for x in xs]
def b9(xs, x, y, z, w, v): return [(x or y) and (z or w or v) for x in xs]
```

CPython 3.11 实测（各 `<listcomp>` 元素窗，节选偏移；`JIF_*_OR_POP` = keep-or-pop，`POP_JUMP_FORWARD_IF_*` = 假出口弹跳）：

```
a1 x and (y or z) and w   12 x; 14 JIF_FALSE_OR_POP 26; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 26; 24 w
a2 (x or y) and z or (w and v)
                          12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 POP_JUMP_FORWARD_IF_FALSE 24; 20 z; 22 JIF_TRUE_OR_POP 40; 24 w; 26 JIF_FALSE_OR_POP 40; 28 v
a3 x and y and (z or w) and v
                          12 x; 14 JIF_FALSE_OR_POP 40; 16 y; 18 JIF_FALSE_OR_POP 40; 20 z; 22 POP_JUMP_FORWARD_IF_TRUE 28; 24 w; 26 JIF_FALSE_OR_POP 40; 28 v
a4 x and (y or z) and w and v
                          12 x; 14 JIF_FALSE_OR_POP 30; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 30; 24 w; 26 JIF_FALSE_OR_POP 30; 28 v
a5 (x or y) and (z or w) and v
                          12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 JIF_FALSE_OR_POP 30; 20 z; 22 POP_JUMP_FORWARD_IF_TRUE 28; 24 w; 26 JIF_FALSE_OR_POP 30; 28 v
a6 ((x or y) and z) and (w or v)
                          12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 JIF_FALSE_OR_POP 30; 20 z; 22 JIF_FALSE_OR_POP 30; 24 w; 26 JIF_TRUE_OR_POP 30; 28 v
a7 '%s' % (x and (y or z) and w)
                          12 LOAD_CONST '%s'; 14 x; 16 JIF_FALSE_OR_POP 28; 18 y; 20 POP_JUMP_FORWARD_IF_TRUE 26; 22 z; 24 JIF_FALSE_OR_POP 28; 26 w; 28 BINARY_OP 6
a8 (x and (y or z) and w) - 1
                          12 x; 14 JIF_FALSE_OR_POP 26; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 26; 24 w; 26 LOAD_CONST 1; 28 BINARY_OP 10
a9 not (x and (y or z) and w)
                          12 x; 14 JIF_FALSE_OR_POP 26; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 26; 24 w; 26 UNARY_NOT
b1 (x or y or z) and w    12 x; 14 POP_JUMP_FORWARD_IF_TRUE 24; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 26; 24 w
b2 x and (y or z or w)    12 x; 14 JIF_FALSE_OR_POP 26; 16 y; 18 JIF_TRUE_OR_POP 26; 20 z; 22 JIF_TRUE_OR_POP 26; 24 w
b3 (x or y) and z and (w or v)
                          12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 JIF_FALSE_OR_POP 30; 20 z; 22 JIF_FALSE_OR_POP 30; 24 w; 26 JIF_TRUE_OR_POP 30; 28 v
b4 (x and y) or (z and w) or v
                          12 x; 14 POP_JUMP_FORWARD_IF_FALSE 20; 16 y; 18 JIF_TRUE_OR_POP 30; 20 z; 22 POP_JUMP_FORWARD_IF_FALSE 28; 24 w; 26 JIF_TRUE_OR_POP 30; 28 v
b5 (x and y) or z and (w or v)
                          12 x; 14 POP_JUMP_FORWARD_IF_FALSE 20; 16 y; 18 JIF_TRUE_OR_POP 30; 20 z; 22 JIF_FALSE_OR_POP 30; 24 w; 26 JIF_TRUE_OR_POP 30; 28 v
b6 x or (y or z) and (w and v)
                          12 x; 14 JIF_TRUE_OR_POP 30; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 30; 24 w; 26 JIF_FALSE_OR_POP 30; 28 v
b7 (x and y) or (z or x)  12 x; 14 POP_JUMP_FORWARD_IF_FALSE 20; 16 y; 18 JIF_TRUE_OR_POP 26; 20 z; 22 JIF_TRUE_OR_POP 26; 24 x
b8 ('p' if x else 'q') and (y or z) and w
                          12 x; 14 POP_JUMP_FORWARD_IF_FALSE 20; 16 'p'; 18 JUMP_FORWARD 22; 20 'q'; 22 JIF_FALSE_OR_POP 34; 24 y; 26 POP_JUMP_FORWARD_IF_TRUE 32; 28 z; 30 JIF_FALSE_OR_POP 34; 32 w
b9 (x or y) and (z or w or v)
                          12 x; 14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 JIF_FALSE_OR_POP 30; 20 z; 22 JIF_TRUE_OR_POP 30; 24 w; 26 JIF_TRUE_OR_POP 30; 28 v
```

⇒ 混合链的跳转序仍是求值序：keep-or-pop 打开/续接节点（op = 极性：`JIF_FALSE_OR_POP` ⇒ and、`JIF_TRUE_OR_POP` ⇒ or；argval = **取值点**），假出口弹跳打开子组（op = 极性反义：`POP_JUMP_FORWARD_IF_TRUE` ⇒ or、`POP_JUMP_FORWARD_IF_FALSE` ⇒ and；argval = **续接点**，恰为窗内某段起点）。两类 argval 不在同一坐标系，不能放进同一 `end` 字段比较。

修复前退化（HEAD `577d0e68` 实测）：`/tmp/r51/a.py` **3**（a5 产物丢 `(z or w)` 整组：`CODE-DIFF <listcomp> @18: POP_JUMP_FORWARD_IF_FALSE 24 vs JUMP_FORWARD 40`、`CODE-LEN a5: 17 vs 15`、`CODE-LEN <listcomp>: 18 vs 16`）；回归集 `w3.py` **5**（p9 三元假臂误判为无条件前向跳转：`CODE-DIFF <listcomp> @18: POP_JUMP_FORWARD_IF_FALSE 24 vs JUMP_FORWARD 30`）；`w.py`/`w2.py`/`v.py`/`x.py`/`y.py`/`z.py`/`f.py`/`g.py`/`r.py`/`t.py` 均 `0`；TOTAL **8**。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 表达式重建 | `_b247_mixed_boolchain` 窗首识别（`core/cfg/comprehension_generator.py` 3202 起） | b8 的窗首是经典三元前缀（`x; POP_JUMP_FORWARD_IF_FALSE; 'p'; JUMP_FORWARD; 'q'`），携带无条件前向跳转 ⇒ 被「窗内无无条件跳转」门整体否决，回落既有通道只取到三元（`CODE-LEN b8: 15 vs 8`） | 首个 keep-or-pop 之前若恰一条弹跳 + 一条 `JUMP_FORWARD` 且后者 argval == 该 keep-or-pop 偏移 ⇒ 三段各自重建拼 `IfExp` 作链首操作数；前缀整体不再参与切段 |
| ② | 表达式重建 | 同函数节点栈（原 `_attach`/`_close_top` 两版） | 把弹跳 argval（续接点，段号语义）与 keep-or-pop argval（取值点，偏移语义）混入同一 `end` 字段比较 ⇒ 弹跳组与 keep 收尾交替的多组形态（a5）被「恰一条 keep」门否决；按首跳特化的 `_b247_leading_bounce` 又把 m6 的 `(y or z)` 层级拍平 | 统一帧栈：帧记「运算符 / 已归约操作数 / 归属段号 end」，keep-or-pop 的 end 随父帧（根为 `None`）、弹跳的 end 取续接段号；处理第 end 段时栈顶帧闭合，闭合值按本跳转重新归入父链（`_place` 级联；同运算符同段号并入父帧操作数） |
| ③ | 表达式重建 | 同上，a2 残差 | a2 的第二个弹跳 argval 24 是**组 2 起点**而非组 1 续接点 ⇒ 两个专用通道都判不中（产物 `y if not x else z or w and v`） | 统一帧栈下弹跳只要求 argval 落在某段起点（`_seg_at`），不要求等于首组的续接点 ⇒ a2 恢复 `(x or y) and z or (w and v)` |

- 修复实现：`_b247_mixed_boolchain` 的节点栈整体重写为统一帧栈（`_frames` + `_place` 级联闭合 + `_combine` 同运算符结合律合并保持扁平原形）；删除按首跳特化的 `_b247_bounce_groups` 与 `_b247_leading_bounce` 两个专用通道（207 行）及首跳分派段。窗首三元前缀段保留。六项 docstring 的②条改写为「两类 argval 坐标系」实证口径；`[B247-V3R51]` 标签覆盖全部新增段。
- 判据纪律：判据只读同层跳转 opcode 与跳转 argval 的段起点归属（I.4 白名单：keep-or-pop 族 / 弹跳族 / 无条件前向跳转三族），无名字特判、无偏移阈值；弹跳 argval 不在段起点集合、段内重建非恰一项、根不唯一任一不满足即返回 `None` 逐字回落既有通道（C3 显式封闭）；未新增 `_fix_/_merge_/_patch_/_fallback_` 前缀方法（G3），无硬编码深度上限（G4）。
- 最小复现读数（本轮树实测）：
  - `/tmp/r51/a.py`（18 形态）：`3 → 0`（逐字一致；a5 恢复 `(x or y) and (z or w) and v`、a2 恢复 `(x or y) and z or (w and v)`、b8 恢复窗首三元 + 混合链）。
  - 回归集：`w.py 0 / w2.py 0 / w3.py 5 → 4 / v.py 0 / x.py 0 / y.py 0 / z.py 0 / f.py 0 / g.py 0 / r.py 0 / t.py 0`，TOTAL **8 → 4**（净改善 4 处，零新增）。
- 门禁读数（本轮树实测）：
  - A/B（同 24 个 stdlib pyc，rr-v5r50 产物 `577d0e68` vs 当前工作树）：文本 `diff -r` **24/24 逐字节相同**；`bytecmp` 问题集 **143 == 143，`diff` 零差异**。
  - `quotation.pyc`：`run_batch_decompile.py` 口径 **152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 3.80s`，两个失败为基线既有。
  - fuzz：`total=295 failures=0 stopped=time_budget workdir=/tmp/fuzz51b`。
  - G1 复核口径更正：本轮以 **J v3 证据**（`round13/jspace_v3/judgment_space_v3.json` + `semantic_v3_merged.json` + `--judge tools/completeness/semantic_diff.py`）重跑 `coverage_checker`，得 `covered_5tuple=0 probe_only=1086 excluded=470`（逐条 reason：`c2_pyc_missing` 1086 / `entry_excluded` 470）；根因是 `jspace_v3/pyc/` 与 `/tmp/j3prod/` 两处 C2/C3 证据工件未纳入仓库（沙箱不存在），**属证据工件缺失而非树回归**，据此撤回上一轮「调用参数口径不对」的猜测。G1 读数沿用 rr-v5r44 的 `covered_5tuple=1050 / probe_only=0 / inconclusive=36 / excluded=470 / uncovered=506 / coverage=67.48% / judge_sha=dbcb1e…`（工件重建后重跑）。G3/G4/G6 读数不变，v9 overall 维持 **BLOCKED**。

#### 本轮复核后仍存残差（未修，下一族）

- **三元臂内嵌推导式**（p9，`w3`）：内层推导式整段丢失（`ONLY-ORIG <listcomp>/<listcomp>`、`CODE-LEN <listcomp>: 25 vs 15`）；本轮仅消除了假臂的 `CODE-DIFF @18`（`POP_JUMP_FORWARD_IF_FALSE 24` 现已逐字），本体仍缺。
- **三元 test 位自身是 keep-or-pop 链**（p4，`w3`）：产物 `w if not z else y or x`。
- **过滤器位取反链的嵌套括号**（p7 `not (x or y) and z`）与**三元双臂各含 keep-or-pop 链**（p8）：同族形态未覆盖。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。

### rr-v5r50：元素位纯 keep-or-pop 链「右嵌套」还原（B246）（2026-10-26）

最小复现 `/tmp/r50/t.py`（10 形态，元素位纯短路链 / 混合链）：

```python
def t1(xs, x, y, z):     return [x or y and z for x in xs]
def t2(xs, x, y, z):     return [x and (y or z) for x in xs]
def t3(xs, x, y, z):     return [x and y and z for x in xs]
def t4(xs, x, y, z):     return [x or y or z for x in xs]
def t5(xs, x, y, z, w):  return [x or y and z or w for x in xs]
def t6(xs, x, y, z, w):  return [x and (y or z) and w for x in xs]
def t7(xs, x, y, z, w):  return [x or (y and z) or w for x in xs]
def t8(xs, x, y, z):     return [(x or y) and z for x in xs]
def t9(xs, x, y, z):     return [x and y or z for x in xs]
def t10(xs, x, y, z, w): return [x or y or z and w for x in xs]
```

CPython 3.11 实测（各组 `<listcomp>`，节选）：

```
t1 x or y and z        12 x; 14 JUMP_IF_TRUE_OR_POP 22; 16 y; 18 JUMP_IF_FALSE_OR_POP 22; 20 z
t2 x and (y or z)      12 x; 14 JUMP_IF_FALSE_OR_POP 22; 16 y; 18 JUMP_IF_TRUE_OR_POP 22; 20 z
t3 x and y and z       14 JIF_FALSE_OR_POP 22; 18 JIF_FALSE_OR_POP 22
t4 x or y or z         14 JIF_TRUE_OR_POP 22; 18 JIF_TRUE_OR_POP 22
t5 x or y and z or w   14 JIF_TRUE_OR_POP 26; 16 y; 18 POP_JUMP_FORWARD_IF_FALSE 24; 20 z; 22 JIF_TRUE_OR_POP 26; 24 w
t6 x and (y or z) and w 14 JIF_FALSE_OR_POP 26; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 26; 24 w
t7 x or (y and z) or w 与 t5 字节码逐条相同（源形不可分辨）
t8 (x or y) and z      14 POP_JUMP_FORWARD_IF_TRUE 20; 16 y; 18 JUMP_IF_FALSE_OR_POP 22; 20 z
t9 x and y or z        14 POP_JUMP_FORWARD_IF_FALSE 20; 16 y; 18 JUMP_IF_TRUE_OR_POP 22; 20 z
t10 x or y or z and w  14 JIF_TRUE_OR_POP 26; 18 JIF_TRUE_OR_POP 26; 22 JIF_FALSE_OR_POP 26; 24 w
```

⇒ 纯 keep-or-pop 窗（全部跳转均为 `JUMP_IF_*_OR_POP`，如 t1–t4、t10）的跳转序即求值序：**链上第 i 条跳转就是第 i 层的顶层运算符**，其右操作数是第 i+1 条起整条链的还原值（右嵌套）。反证：`(x and y) or z`（t9）与 `(x or y) and z`（t8）的首跳都是**假出口弹跳**（`POP_JUMP_FORWARD_IF_*`）而非 keep-or-pop，故纯 keep-or-pop 窗不可能是左结合弹跳形态。

修复前退化（HEAD `ac9ccacd` 实测）：`t2` → `x and y or z`（= `(x and y) or z`，x 假、z 真时语义错）；`/tmp/r45/w2.py` 的 n15 `[x and (y or z) for x in xs]` 同形（`CODE-DIFF <listcomp> @14: JUMP_IF_FALSE_OR_POP 22 vs POP_JUMP_FORWARD_IF_FALSE 20`）。读数：`/tmp/r50/t.py` **2**、`/tmp/r45/w2.py` **1**。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 表达式重建 | `_b242_fold_boolop_pending` 的归约器（`core/cfg/ast_generator_v2.py` 294-362） | `(ops, values)` 扁平序列按**左结合优先级**归约（and 高于 or，先归 and 段再归 or 层）⇒ `x and (y or z)` 被读成 `(x and y) or z` | 改为右嵌套递归 `_parse(k)`：取 `values[k]` 作本层左操作数、`ops[k]` 作本层运算符、`_parse(k+1)` 作右操作数；同运算符右链按结合律并入同一 `BoolOp` 保持 `x and y and z` 扁平形态 |
| ② | 表达式重建 | 同上，`_merge`（同文件 323-343） | 原 `_merge` 只向左并入同运算符，右嵌套产生的同运算符右链会多一层括号（渲染偏离源码形） | `_merge` 增补「右链同运算符并入」分支（左右同为该运算符时合并两侧 `values`） |

- 判据纪律：判据只读同层跳转 opcode 与链上边界序（I.4 白名单：keep-or-pop 族 `JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP`、弹跳族 `POP_JUMP_FORWARD_IF_TRUE/_IF_FALSE`），无名字/偏移魔数特判；`_parse` 保持六项 docstring，②条改为右嵌套实证口径；`len(values) == len(ops)+1` 不满足即返回 `None` 逐字回落（C3）；弹跳首跳形态不经本归约器（由 `_b237_kop_window`/三元通道承担），通道互不覆盖。
- 最小复现读数（本轮树实测）：
  - `/tmp/r50/t.py`（10 形态）：`2 → 1`，t2 恢复 `x and (y or z)`；t3/t4/t10 仍为扁平等价形（与源码逐字一致）；t8/t9 走弹跳通道不变。
  - `/tmp/r45/w2.py`（17 形态）：`1 → 0`，n15 恢复逐字。
  - 回归集：`/tmp/r45/w.py` `0`、`w3.py` `7`（与 rr-v5r49 持平，零新增）、`v.py` `0`；`/tmp/r45/x.py`、`/tmp/r47/y.py`、`/tmp/r48/z.py`、`/tmp/r49/f.py`、`g.py`、`r.py` 全部 `0`。
- 门禁读数（本轮树实测）：
  - A/B（同 24 个 stdlib pyc，rr-v5r49 产物 `ac9ccacd` vs 当前工作树）：文本 **24/24 逐字节相同**；`bytecmp` 问题集 **143 == 143，`diff` 零差异**（`AB-BYTE-IDENTICAL`）。
  - `quotation.pyc`：`run_batch_decompile.py` 口径 **152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 4.43s`，两个失败为基线既有。
  - fuzz：`total=286 failures=0 stopped=time_budget workdir=/tmp/fuzz50`。
  - G5 的 402 语料/small34 分片在本沙箱仍不可达；G1/G3/G4/G6 读数不变（四桶 395/0/719/442、mutation 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。

#### 上轮读数复核更正（rr-v5r49 残差清单）

- `q12`（`if not a or b` → `(b if a else True)`）与 `q14`（`if not (a and b) or not b` → `not a or not b or not b`）经复核**均为语义等价且重编译字节码逐条相同**（`/tmp/r45/cmp.py` 对 `/tmp/r49/g.pyc` `total diffs = 0`），属非逐字形而非缺陷；原「三元误判」定性作废，保留为形态读数差异。

#### 本轮复核后仍存残差（未修，下一族）

- **元素位「首跳 keep-or-pop + 中段弹跳」混合链**（`[x and (y or z) and w for x in xs]`，t6）：产物 `(y or z) and w`（丢掉前导 `x`）；`12 x; 14 JIF_FALSE_OR_POP 26; 16 y; 18 POP_JUMP_FORWARD_IF_TRUE 24; 20 z; 22 JIF_FALSE_OR_POP 26; 24 w`；弹跳目标 24 是「新段起点」而非汇合点，需要按落点分段的混合链通道（`_b237_kop_window` 只接受前向 IF_FALSE 首跳）。
- **三元 test 位自身是 keep-or-pop 链**（p4，`w3`）：产物 `w if not z else y or x`。
- **元素位 and 链夹嵌套 or 后仍有 and**（p5，`w3`）：产物 `(z or w) and v`。
- **元素位「首跳弹跳 + 中段 keep-or-pop」混合链**（p6，`w3`）：产物 `y if not x else z or w and v`。
- **三元臂内嵌推导式**（p9，`w3`）：内层推导式整段丢失（`ONLY-ORIG <listcomp>/<listcomp>`）。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。

### rr-v5r49：推导式过滤器位「短路跳转链」按落点整组归约（B245）（2026-10-26）

最小复现三组共 30 形态：`/tmp/r49/f.py`（q1–q10）、`/tmp/r49/g.py`（q11–q20）、`/tmp/r49/r.py`（r1–r10）：

```python
# f.py（取反/混合）
def q1(xs, a, b):        return [x for x in xs if not (a and b)]
def q2(xs, a, b, c):     return [x for x in xs if not (a and b and c)]
def q5(xs, a, b, c):     return [x for x in xs if not (a and b) or c]
def q6(xs, a, b, c):     return [x for x in xs if c and not (a and b)]
def q7(xs, a, b, c):     return [x for x in xs if not (a and b) and c]
def q8(xs, a, b):        return [x for x in xs if a or not b]
def q10(xs, a, b, c):    return [x for x in xs if not (a and (b or c))]
# g.py（混合优先级）
def q12(xs, a, b):       return [x for x in xs if not a or b]
def q14(xs, a, b):       return [x for x in xs if not (a and b) or not b]
def q18(xs, a, b, c):    return [x for x in xs if a and (not b or c)]
# r.py（括号嵌套/握手）
def r1(xs, a, b, c):     return [x for x in xs if (a or b) and c]
def r2(xs, a, b, c):     return [x for x in xs if (a and b) or c]
def r5(xs, a, b, c, d):  return [x for x in xs if (a and b) and (c or d)]
def r6(xs, a, b, c, d):  return [x for x in xs if (a or b) and (c or d)]
def r9(xs, a, b, c, d):  return [x for x in xs if not (a and b) and not (c and d)]
def r10(xs, a, b, c, d): return [x for x in xs if a and not (b and c) and d]
```

CPython 3.11 实测（各组 `<listcomp>`，节选；`elt` = 元素起点，`head` = 循环头偏移）：

```
q1  if not (a and b):        12 a; 14 POP_JUMP_FORWARD_IF_FALSE 20; 16 b; 18 POP_JUMP_BACKWARD_IF_TRUE 8
q2  if not (a and b and c):  14 POP_JUMP_FORWARD_IF_FALSE 24; 18 POP_JUMP_FORWARD_IF_FALSE 24; 22 POP_JUMP_BACKWARD_IF_TRUE 8
q5  if not (a and b) or c:   14 ...IF_FALSE 24; 18 ...IF_FALSE 24; 22 POP_JUMP_BACKWARD_IF_FALSE 8
q7  if not (a and b) and c:  14 ...IF_FALSE 20; 18 POP_JUMP_BACKWARD_IF_TRUE 8; 20 c; 22 POP_JUMP_BACKWARD_IF_FALSE 8
q8  if a or not b:           14 POP_JUMP_FORWARD_IF_TRUE 20; 18 POP_JUMP_BACKWARD_IF_TRUE 8
q12 if not a or b:           14 POP_JUMP_FORWARD_IF_FALSE 20; 18 POP_JUMP_BACKWARD_IF_FALSE 8
r1  if (a or b) and c:       14 POP_JUMP_FORWARD_IF_TRUE 20; 18 POP_JUMP_BACKWARD_IF_FALSE 8; 22 POP_JUMP_BACKWARD_IF_FALSE 8
r5  if (a and b) and (c or d):
                             14 POP_JUMP_BACKWARD_IF_FALSE 8; 18 POP_JUMP_BACKWARD_IF_FALSE 8
                             22 POP_JUMP_FORWARD_IF_TRUE 28; 26 POP_JUMP_BACKWARD_IF_FALSE 8
r6  if (a or b) and (c or d):
                             14 POP_JUMP_FORWARD_IF_TRUE 20; 18 POP_JUMP_BACKWARD_IF_FALSE 8
                             22 POP_JUMP_FORWARD_IF_TRUE 28; 26 POP_JUMP_BACKWARD_IF_FALSE 8
```

⇒ 过滤器位的每条条件跳转按**目标落点**定型：落到元素起点（20/28…）= 本轮通过（pass）；回跳循环头（8）= 跳过本轮（skip）；落到另一段起点 = 握手（该段起为子表达式，例如 r1 的 `POP_JUMP_FORWARD_IF_TRUE 20` 直落第 3 段 = `(a or b)` 整体命中后继续测 `c`）。

修复前退化（HEAD `1d9eaf99` 实测）：`q1` → `a and not b`、`q2` → `a and b and not c`、`q5` → `a and b and c`、`q6` → `c and a and not b`、`q7` → `a and not b and c`、`q8` → `not a or not b`、`q10` → `a and not b and not c`；`r1` → `a and b and c`（括号层级丢失）、`r2` → `a and b and c`、`r5` → `a and b and c and d`、`r6` → `a and b and c and d`。读数：`f.py` **7**、`g.py` **7**、`r.py` **3**。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 推导式生成 | `_extract_comp_ifs` 逐段极性标注（`core/cfg/comprehension_generator.py` 2548-2588） | 只按**跳转极性**给项（`IF_TRUE` ⇒ `not`、`IF_FALSE` ⇒ 原样），完全不看 `argval` 落点 ⇒ pass 段的 `IF_FALSE` 被当 and 成员，`not (a and b)` 读成 `a and not b` | 新增通道按 `argval` 分类：`== 元素起点` ⇒ pass、`>= 追加点` 或 `BACKWARD` ⇒ skip、`∈ 其它段起点` ⇒ 握手；pass 段取命中字面量 `T`、skip 段取 `¬T`（`_falsify` 对 `not X` 直接取 `X`，避免双重取反多一条 `UNARY_NOT`） |
| ② | 推导式生成 | 同上，无握手分组 | 无「段组」概念 ⇒ `(a or b) and c` 类括号嵌套无法表达：`a or b` 命中后整体进入外层 and | 握手值 `j` 表示 `i..j-1` 为子表达式：末段落 skip ⇒ or 组（`T_i … ¬T_{j-1}`）、末段落 pass ⇒ and 组（`¬T_i … T_{j-1}`）；组真值后与后续 `and` 合成、组假值后与后续 `or` 合成，递归右嵌套 |
| ③ | 推导式生成 | `_detect_comp_ternary` 主扫描（同文件 3452-3516） | `if not a or b`（`14 POP_JUMP_FORWARD_IF_FALSE 20; 18 POP_JUMP_BACKWARD_IF_FALSE 8`）被 R10 判为「OR-filter」以外的三元形态，产物 `(b if a else True)` | **未修**，登记为残差（见下）；本轮新通道在 `_detect_comp_ternary` 之前仅覆盖非三元路径 |

- 判据纪律：全部判据只读同层 `opname`、`argval` 跳转落点与段起点集合（I.4 白名单：条件跳转族 `POP_JUMP_FORWARD_IF_TRUE/_IF_FALSE` / `POP_JUMP_BACKWARD_IF_TRUE/_IF_FALSE` / `IF_NONE`/`IF_NOT_NONE` 族 / 段起点偏移），无名字与偏移魔数特判；链式比较（`COPY 2` + `COMPARE_OP/IS_OP/CONTAINS_OP` 前缀）一律 early-return 交既有合并段（零新增前缀方法，G3 口径）；`_b245_comp_filter_chain` 与内部 `_parse` 六项 docstring 齐备；任一段重建失败或落点未知即整窗返回 `None` 逐字回落既有路径（C3）；通道只在过滤器位启用，元素位与 dict 键/值位不受影响。
- 最小复现读数（本轮树实测）：
  - `/tmp/r49/f.py`（10 形态）：`7 → 0`，q1 恢复 `not a or not b`、q6 `c and (not a or not b)`、q7 `(not a or not b) and c`、q10 `not a or not b and not c`。
  - `/tmp/r49/g.py`（10 形态）：`7 → 0`，q14 `not a or not b or not b`（语义等价、非逐字）、q18 `a and (not b or c)`、q20 `(not a or not b) and not c`。
  - `/tmp/r49/r.py`（10 形态）：`3 → 0`，r1 `(a or b) and c`、r5 `a and b and (c or d)`、r6 `(a or b) and (c or d)`、r7 `a and (b or c) and d`、r9 `(not a or not b) and (not c or not d)`、r10 `a and (not b or not c) and d`。
  - 回归集：`/tmp/r45/w.py` `0`、`w2.py` `2 → 1`（n12 `[x or y and z for x in xs if not (x and z)]` 由 `if x and not z` 恢复 `if not x or not z`）、`w3.py` `7`（与 rr-v5r48 持平，零新增）、`v.py` `0`。
- 门禁读数（本轮树实测）：
  - A/B（同 24 个 stdlib pyc，rr-v5r48 产物 `1d9eaf99` vs 当前工作树）：文本 **24/24 逐字节相同**；`bytecmp` 问题集 **143 == 143，`diff` 零差异**（`AB-BYTE-IDENTICAL`）。
  - `quotation.pyc`：`run_batch_decompile.py` 口径 **152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 4.18s`，两个失败为基线既有。
  - fuzz：`total=280 failures=0 stopped=time_budget workdir=/tmp/fuzz49`。
  - G5 的 402 语料/small34 分片在本沙箱仍不可达；G1/G3/G4/G6 读数不变（四桶 395/0/719/442、mutation 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。

#### 本轮复核后仍存残差（未修，下一族）

- **过滤器位被误判为三元**（`if not a or b`，q12，`/tmp/r49/g.py`）：产物 `(b if a else True)`；**rr-v5r50 复核更正：语义等价且重编译字节码逐条相同（`total diffs = 0`），属非逐字形而非缺陷。**
- **过滤器位链尾冗余项**（`if not (a and b) or not b`，q14）：产物 `not a or not b or not b`；**rr-v5r50 复核更正：同上，语义等价、字节码逐条相同。**
- **元素位纯 keep-or-pop 首跳的嵌套优先级**（`[x and (y or z) for x in xs]`，n15，`w2` 唯一残差）：产物 `[x and y or z ...]`（x 假、z 真时语义不同）；`CODE-DIFF <listcomp> @14: JUMP_IF_FALSE_OR_POP 22 vs POP_JUMP_FORWARD_IF_FALSE 20`；与 rr-v5r48 ③ 同族但位于元素位，需在元素位通道启用「首跳即顶层运算符」右嵌套。**已由 rr-v5r50 修复**（恢复 `x and (y or z)`）。
- **三元 test 位自身是 keep-or-pop 链**（`[x and y if (z or w) else (y or x)]`，p4，`w3`）：条件区重建未开启同族归约，产物 `w if not z else y or x`。
- **元素位顶层 and 链中夹嵌套 or 后仍有 and**（`[x and y and (z or w) and v]`，p5，`w3`）：扁平 `(ops, values)` 无法表达层级，产物 `(z or w) and v`。
- **三元臂内嵌推导式**（`[[a or y and z for a in xs] if x or w else [x] for x in xs]`，p9，`w3`）：内层推导式整段丢失（`ONLY-ORIG <listcomp>/<listcomp>`）。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。

### rr-v5r48：dict 推导式键/值位「多假出口短路链」递归归约（B244 残差）（2026-10-26）

最小复现 `/tmp/r48/z.py`（4 形态，键位与值位各两例）＋上轮残差 r6：

```python
def r6(kv, y, z, w):  return {(k or y or z) and w: v for (k, v) in kv.items()}
def s1(kv, y, z, w):  return {(k and y and z) or w: v for (k, v) in kv.items()}
def s2(kv, y, z, w, u): return {k: (y and z and w) or u for k in kv}
def s3(kv, y, z, w, u): return {(k or y or z) and (w or u): v for (k, v) in kv.items()}
def s4(kv, y, z, w, u): return {(k or y) and z and (w or u): v for (k, v) in kv.items()}
```

CPython 3.11 实测（`/tmp/r48/z.pyc` 的 `<dictcomp>`，节选）：

```
r6 18 LOAD_FAST k; 20 POP_JUMP_FORWARD_IF_TRUE 30; 22 LOAD_DEREF y
   24 POP_JUMP_FORWARD_IF_TRUE 30; 26 LOAD_DEREF z
   28 JUMP_IF_FALSE_OR_POP 32; 30 LOAD_DEREF w; 32 LOAD_FAST v; 34 MAP_ADD 2
s1 18 LOAD_FAST k; 20 POP_JUMP_FORWARD_IF_FALSE 26; 22 LOAD_DEREF y
   24 POP_JUMP_FORWARD_IF_FALSE 26; 26 LOAD_DEREF z
   28 JUMP_IF_TRUE_OR_POP 32; 30 LOAD_DEREF w; 32 LOAD_FAST v; 34 MAP_ADD 2
s4 18 k; 20 POP_JUMP_FORWARD_IF_TRUE 26; 22 y; 24 JIF_FALSE_OR_POP 36; 26 z
   28 JIF_FALSE_OR_POP 36; 30 w; 32 JIF_TRUE_OR_POP 36; 34 u; 36 v; 38 MAP_ADD 2
```

跳转极性语义实证（`/tmp/r48/truth.py`，value 位置）：

```
t1 a and b or c         2 a; 4 POP_JUMP_FORWARD_IF_FALSE 10; 6 b; 8 JUMP_IF_TRUE_OR_POP 12; 10 c
t2 a and (b or c)       2 a; 4 JUMP_IF_FALSE_OR_POP 12; 6 b; 8 JUMP_IF_TRUE_OR_POP 12; 10 c
t3 (a or b) and c       2 a; 4 POP_JUMP_FORWARD_IF_TRUE 10; 6 b; 8 JUMP_IF_FALSE_OR_POP 12; 10 c
t5 (a or b or c) and (d or a)
                        2 a; 4 POP_IF_TRUE 14; 6 b; 8 POP_IF_TRUE 14; 10 c
                        12 JUMP_IF_FALSE_OR_POP 20; 14 d; 16 JUMP_IF_TRUE_OR_POP 20; 18 a
```

⇒ 首跳是弹跳（`POP_JUMP_FORWARD_IF_*`）时属「真值仅用于决定外层」的左链；首跳是 keep-or-pop 时**首条跳转即顶层运算符**，右操作数须递归还原（`t2` 与 `t1` 的跳转序列不同：左结合优先级折叠会把 `a and (b or c)` 误判成 `a and b or c`）。

修复前退化（HEAD `db56661f` 实测）：`r6` → `{z and w: v ...}`；`s1`/`s2`/`s3` 已正确（单层弹跳或纯 keep-or-pop）；`s4` → `(k or y) and (z and w or u)`（重编译跳转极性差 1 条）。读数：`/tmp/r48/z.py` **`total diffs = 1`**、`/tmp/r47/y.py` **`total diffs = 2`**（仅 r6）。

| 编号 | 层 | 位置 | 根因 | 判据与归约 |
|---|---|---|---|---|
| ① | 推导式生成 | `_dict_shortcircuit_chain` 的 `_parse` 递归化（`core/cfg/comprehension_generator.py` 1842-1935） | 上轮只按**首跳切一层**：`t` 之前那段内若还有第二个弹跳（`(k or y or z) and w`），段重建 A 时栈上留下两项以上 ⇒ 违反「恰一项」⇒ 整窗返回 None | 弹跳组改为**累积**：目标同为 `t`、且位于首个 keep-or-pop 之前的全部弹跳，按极性给出内层运算符（IF_TRUE ⇒ `or`、IF_FALSE ⇒ `and`），跳转之间的无跳转指令段各自 `_single` 重建后左结合成左链；左链首段（首个弹跳之前的前缀）同样入链 |
| ② | 推导式生成 | 同上，keep-or-pop 分支（同文件 1875-1892） | 纯 keep-or-pop 窗原先交给重建器的**左结合优先级折叠**，把 `z and (w or u)` 误判成 `(z and w) or u`（`t2` 极性实证），导致 s4 的右链多一层同运算嵌套、重编译跳转极性差 1 条 | 首跳为 keep-or-pop 时：首条跳转即**顶层运算符**，左操作数 `_single`、右操作数 `_parse` 递归；右链与顶层同运算符时按结合律并入同一 `BoolOp` |
| ③ | 推导式生成 | 同上，右链并入（同文件 1918-1925） | 递归产生的右链与顶层同运算符时多一层嵌套，渲染会多出括号 ⇒ 重编译跳转极性差异 | 右链 `op == _outer` 时 `values = [_left] + right.values`，否则 `[_left, _right]` |

- 判据纪律：全部判据只读同层 opcode、`argval` 跳转目标与窗内汇合点（I.4 白名单：弹跳族 `POP_JUMP_FORWARD_IF_TRUE/_IF_FALSE` / keep-or-pop 族 `JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP` / 无条件跳转族），无名字与偏移魔数特判；`_parse` 六项 docstring 齐备，前缀无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`（G3 口径）；任一段重建失败即整窗返回 `None` 逐字回落既有路径（C3）；通道仍只在 dict 键/值窗内启用，元素位与过滤器通道不受影响。
- 最小复现读数（本轮树实测）：
  - `/tmp/r48/z.py`（4 形态）：`total diffs 1 → 0`，s1/s2/s3/s4 产物与源码逐字一致（s4 恢复 `{(k or y) and z and (w or u): v ...}`）。
  - `/tmp/r47/y.py`（8 形态）：`total diffs 2 → 0`，r6 恢复 `{(k or y or z) and w: v for k, v in kv.items()}`；其余 7 形态与上轮一致（r2 仍为不带括号的等价形态）。
  - `/tmp/r45/x.py`（12 形态）：`0 → 0`。
  - 回归集持平：`/tmp/r45/w.py` `0`、`w2.py` `2`、`w3.py` `7`、`v.py` `0`（与 rr-v5r47 逐项相同，零新增）。
- 门禁读数（本轮树实测）：
  - A/B（同 24 个 stdlib pyc，rr-v5r47 产物 `db56661f` vs 当前工作树）：文本 **24/24 逐字节相同**；`bytecmp` 问题集 **143 == 143，`diff` 零差异**（`AB-BYTE-IDENTICAL`）。
  - `quotation.pyc`：`run_batch_decompile.py` 口径 **152 函数 / 151 完全匹配**，唯一失败 `datetimeindex_astype.<lambda>` 为基线既有。
  - pytest 七套件：`2 failed / 282 passed / 2 xpassed in 3.95s`，两个失败为基线既有。
  - fuzz：`total=276 failures=0 stopped=time_budget workdir=/tmp/fuzz48b`。
  - G5 的 402 语料/small34 分片在本沙箱仍不可达；G1/G3/G4/G6 读数不变（四桶 395/0/719/442、mutation 32 killed/602 missed、rule proved 0/open 339、ASSURANCE_BLOCKED），v9 overall 维持 **BLOCKED**。

#### 本轮复核后仍存残差（未修，下一族）

- **过滤器回边**（`[x or y and z for x in xs if not (x and z)]`，n12，`w2` 2 处）：产物 `if x and not z`（语义错）；`CODE-DIFF <listcomp> @14: POP_JUMP_FORWARD_IF_FALSE 20 vs POP_JUMP_BACKWARD_IF_FALSE 8`；属既有过滤器通道（`_extract_comp_ifs`），需按回边目标还原过滤器短路链。
- **三元 test 位自身是 keep-or-pop 链**（`[x and y if (z or w) else (y or x)]`，p4，`w3`）：条件区重建未开启同族归约，产物 `w if not z else y or x`。
- **顶层 and 链中夹嵌套 or 后仍有 and**（`[x and y and (z or w) and v]`，p5，`w3`）：元素位扁平 `(ops, values)` 无法表达层级，产物 `(z or w) and v`。
- **三元臂内嵌推导式**（`[[a or y and z for a in xs] if x or w else [x] for x in xs]`，p9，`w3`）：内层推导式整段丢失（`ONLY-ORIG <listcomp>/<listcomp>`）。
- 既有残差不变：`z: dict[str, int] = {}` 的 AnnAssign 注解丢失；`newline="""\n"""` 三引号渲染；J v3 的 36 条 `c4_error` inconclusive 与 470 条空 calls（376 条 real-package 宿主依赖缺失）。
