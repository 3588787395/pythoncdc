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
