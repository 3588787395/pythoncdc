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
