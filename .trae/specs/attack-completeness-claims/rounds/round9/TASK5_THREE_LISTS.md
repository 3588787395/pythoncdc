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
