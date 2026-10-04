# FIX_A.md — Round 1.2 修复工程师位 A（region_analyzer.py）落地报告

规范：`adversarial-complete-forms-v2-10rounds`（Round 1.2 修复批）
涉改文件：**仅 `core/cfg/region_analyzer.py`**（region_ast_generator / ast_generator_v2 / structured_analyzer / code_generator / pattern_parser 零改动）
判据纪律：I.4 白名单（块末 opcode / 后继前驱集合 / 异常边 / 区域成员关系 / code object 元数据 / oparg）；修复语义 = 封闭守卫恢复 C1/C2/C3。

**代码已落地**（落地标记 grep 证据：`_b50_fix_try_hosted_ternary_normal_copies`、`_b50_finally_copy_iso_seqs`、`_b74_guard_arm_targets_case_body` 均在树中定义且被调用；见 §1/§3）。

---

## §1 B48 残留 → t_host_try_sections（B50 族）【已封闭】

**破口**：`test_repros/round7/r7_08_ternary_deep_host.py` 的 `t_host_try_sections`
（`try: r = xs[i] if flag else xs[0] / except IndexError: r = -1 if flag else -2 / finally: r = r if flag else 0`）
try 体首语句三元丢失、finally 语句被吸进 try body。

**根因**（判定性实验 `probes_fixA/exp_try_parent.py` + `exp_iso_check.py`）：
CPython 3.11 把 finally body 复制两份（normal 副本 entry=86 落在 try 体 fallthrough 路径、exception 副本 entry=42 在 finally_blocks）。生成端 finally 副本跳过预_pass（region_ast_generator.py:26894-26924，只读锚点）以「entry ∈ try_blocks + 存在 finally_blocks 中等长兄弟三元」识别 normal 副本——本形态 normal 副本 entry ∉ try_blocks → 条件 1 不命中；而 try 体首三元 T@4（与 try 区域入口共享块 4）因 len(blocks)==len(T@100) 被条件 ⑤ 弱判据假配对误标 generated。双重效应：T@4 被 :27158 父入口 continue 阻断 + T@86 连同 merge 块 blk@122 的 return 泄漏进 try body。

**修复**（analyze() 尾部 :1980 调用 `_b50_fix_try_hosted_ternary_normal_copies`，:2010-2107）：
1. **detach**：TernaryRegion.entry is TryExceptRegion.entry 且 entry ∉ finally_blocks、块集 ⊆ try_blocks、且与**全部** exception 副本剥噪剥尾跳转后**不同构**（`_b50_finally_copy_iso_seqs`；同构 = try 体空形态的 normal 副本，预_pass 跳过是正确行为，不得 detach）→ 解除父子边。
2. **补登记**：exception 副本 `_e` 找兄弟 `_sib`（entry ∉ finally_blocks、entry ∈ finally_copy_blocks 键集〔analyzer 自产副本入口映射，handler 三元 entry 不在键集〕、len(blocks) 相等、id 不在 try_entry_ids、与 `_e` 同构）→ `_reg.try_blocks.append(_sib.entry)`，使生成端预_pass 条件 1 命中。

**判据**：仅取块结构事实（入口块同一性 / 区域父子关系 / 块集成员关系 / 剥噪 opname 序列同构 / finally_copy_blocks 键集）。无名称白名单、无魔数偏移、无跨层反查、无 self 新增跨方法状态。
**读数**：r7_08 **8/8 全 MATCH**（修复后 / 插桩清理后 / BOM 恢复后三轮复现）。

## §2 B46 尾项 t_nest_in_condition【已封闭·前会话】

融合条件三件套（连接块解引用 + while_cond 守卫）。r7_07 **7/7 全 MATCH**；本会话插桩清理后未复测回退（负对照 rv7_02 50% / rv7_04 66.67% 与基线一致）。

## §3 B74 match case 体首 if 幻影 guard【已封闭】

**破口**：`test_repros/round10/r10_06_import_deep_combo.py` `imp_combo_lambda_default`——case 体首 import + if 形态产生幻影 guard + 幻影 else continue。

**根因**（`probes_fixA/gen_b74_variants.py` 变体 A 无 import / B 有 import 同现幻影 → **import 非根因**）：case 体首块兼作 pattern 材料（UNPACK_SEQUENCE+STORE 与 if 条件同块），guard 提取器（pattern_parser.py:477-553，只读锚点）在最后 STORE 之后扫到体首 if 臂段，极性协议（G==fail→正臂；G!=fail→取反臂）把体首 if 判为取反臂。结构事实：**真 guard 失败边指向下一 case 头/merge（离开 case），绝不可能落入体块集**；体首 if 语句的跳转目标必在体块集内。

**修复**：三处 match 装配调用点（`_identify_match_regions` :14021、`_collect_nested_match_region` :15732、`_scan_literal_match_subjects` :16220）统一后校验：`parse_case_guard` 产出经 `_b74_guard_arm_targets_case_body`（:2109-2198，六项模板 docstring）重放提取器 search_start（最后 STORE_OPS 之后 / pattern_end_ops 回扫）+ 首臂定位（var-const / var-var / is-op / truthiness），臂终止跳转目标 ∈ 体块集即撤销 guard。不命中 ⇒ 原行为逐字节不变。
**读数**：r10_06 **3/3 全 MATCH**；变体 A/B 各 2/2 100%；match 系列 20 文件与 HEAD 基线逐位一致。

## §4 B65 链式赋值 × 嵌套 BoolOp【降级移交】

诊断完成：锚点 **region_ast_generator.py:37913-37928**（链式赋值目标仅 2 形态，嵌套 BoolOp RHS 通道缺失）。修复必须扩发射端目标形态——**region_ast_generator 非本位涉改文件**，按任务书「只做 region_analyzer.py 内可完成部分，其余如实登记移交」降级。**移交修复位 B**，诊断材料见 fixA_probe_results.json `handover.B65`。

## §5 B76 augassign × BoolOp RHS 体蒸发【降级移交】

诊断完成：锚点 **region_ast_generator.py:37881-37890**（装配未 return 穿透）→ **:38193 UnboundLocalError**。同理发射端越界，**移交修复位 B**，见 `handover.B76`。

## §6 插桩清理【已完成·行为等价】

- **DBG_OR ×9**（or-tail restore / or-chain member skip→裸 continue / or-member rejected / or-chain detected·negated or-chain detected·or-candidate rejected 三个 elif 整删 / region-build / region-built / boolop chain start skipped）全部删除。
- **FIXA-DBG ×3**（`FIXA det` / `FIXA fe` / `FIXA gate-reject`——第三处保留 `return None` 控制流）+ `trace_create.py` 开关行删除。
- `grep 'DBG_OR|FIXA-DBG|_fixa_trace' in core/` = **0 命中**。
- 行为等价证据：删除后 r7_08 8/8、r10_06 3/3、负对照 5 文件读数与删除前一致。

## §7 读数表

| 面 | 读数 | 判定 |
|---|---|---|
| r7_08（B50 目标） | 8/8 100% | MISMATCH→MATCH ✓ |
| r7_07（B46 目标） | 7/7 100% | 保持 MATCH ✓ |
| r10_06（B74 目标） | 3/3 100% | MISMATCH→MATCH ✓ |
| b74_a_noimport / b74_b_import | 2/2、2/2 100% | 变体对照 ✓ |
| 负对照（清理后速测） | rv7_02 50%、rv7_04 66.67%、r4_01 100%、r2_07_try_with_match 50%、r2_07_with_lock_dropped 87.5%（HEAD stash 一致） | 不变差 ✓ |
| match 系列 20 文件 | 与 HEAD 基线逐位一致（0% 瞬态读数经 stash 复测证伪） | 不变差 ✓ |
| **34 小测试集（权威 pyc_verify.py）** | **1497/1568 → 1505/1568，REGRESSED=0**（quote +3、trade_live_broker +3、jq_trans_module +2；31 文件失败名单与基线持平） | **无回退 ✓** |
| IV.2 自检 | BOM 单头 ×2（efbbbf ×1/文件）、IMPORT_OK、COMPILE_OK、插桩零残留 | PASS ✓ |

**量测工具警示**：`scripts/pyc_batch_verify.py single` 的 total_functions 为交集分母，漏函数被静默排除（quotation 143≠153、jq_trans 35≠65），曾致本位误报 19 文件「函数塌缩」回归——HEAD stash 复测全部证伪，系口径伪象非回归。回归判据唯一 = `scripts/pyc_verify.py`。

## §8 降级登记汇总

| 破口 | 状态 | 移交对象 | 原因 |
|---|---|---|---|
| B65 | 已定位未封闭 | 修复位 B | 发射端（region_ast_generator.py）越界 |
| B76 | 已定位未封闭 | 修复位 B | 发射端（region_ast_generator.py）越界 |
| 生成端 finally 副本预_pass 弱判据（条件 ⑤ len 相等假配对） | 存量观察项 | 修复位 B / 评审 | 本位以 analyzer 侧 detach+补登记封闭 r7_08 形态；预_pass 判据本体在 region_ast_generator.py:26894-26924，越界 |

## §9 产物清单

- `rounds/round1/probes_fixA/`：exp_try_parent.py、exp_iso_check.py、gen_b74_variants.py、dump_match.py、dump_try.py、dump_ternary.py、trace_create.py、trace_ternary.py、compare_34set.py、compare_34set_authoritative.py、tmp/（b74 变体 pyc/OK.py、34set 跑批日志、fixA_34set_pycverify.json 权威报告）
- `rounds/round1/probes_fixA/fixA_probe_results.json`（本报告机器可读版）
- regen 产物：r7_07OK / r7_08OK / r10_06OK / r2_07_try_with_matchOK / r4_09OK / r4_12OK / r4_13OK / r4_14OK + 34 集各 site-packages *OK.py（均为重生成，零手改）
