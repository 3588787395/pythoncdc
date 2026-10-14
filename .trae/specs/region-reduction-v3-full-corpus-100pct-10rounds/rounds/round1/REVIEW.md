# Round 1 — 测试工程师 REVIEW（诊断 only，零生产代码改动）

- 工作树 `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`，分支 `rr-v3r01-f557fd`
- 解释器 `python -X utf8`（Python 3.11.7）；判据唯一 `scripts/pyc_verify.py single`
- before = `../baseline_snapshot.md`（units 6554/6617、files 369/402）
- 本轮实测顺序严格按 tasks.md 2.1 的 6 个 pyc，逐文件完成；全部命令 rc=0 且 <300s
- 产物目录：`test_repros/round1/`（复现 .py + .pyc + pycdc 生成 OK.py + 电池索引 `r1_probe_index.json`）
- 本目录内的 `.py` 全部由 `pycdc.py -o` 生成或本人手写；**未手改任何 `*OK.py` 交付产物**，未触碰 `core/**`、`pycdc.py`、`scripts/**`、`bytecode/**`、`parsers/**`、`utils/**`
- 工具（仅测试侧，只读用途）：`test_repros/round1/_diag.py`（marshal/dis 逐指令对齐）、`_run.py`（compile→pycdc→single 三步电池）、`_search.py`（形态搜索生成器）

## 0. 基线核对（复算，非重测全量）

```
***<module>.set_cgroup_config: Failure: Different control flow
[single] .../site-packages/IQCommon/util/cgroup_utils.pyc status=failure units=7/8 success_rate=87.50%
```
与 baseline_snapshot.md 逐位一致。其余 5 个 pyc 直接沿用基线读数（未重跑 single），
其失败单元的逐指令差异全部由 pyc↔OK.py 二进制比对得出（`_diag.py diff`）。

## 1. 术语与判据口径

- 「第一分歧」= 线性指令序列（跳过 CACHE）首个 (opcode, argval) 不同处。
- 「结构分歧」= 排除纯对齐伪影后的首个真实差异。本轮 6 个 pyc 中 4 个的**首个线性分歧只是跳转目标偏移变化**（`EXTENDED_ARG` 插入 / 目标 +2），这是下游结构差异的位移伪影，不是缺陷本身；下表同时给出两者。
- pylingual 归一化口径已豁免「重编译跳转目标偏移」，因此凡判 `Different control flow` 均为**边/成员关系**真差异。

---

## 2. pyc #1 `site-packages/IQCommon/util/cgroup_utils.pyc`（7/8，`<module>.set_cgroup_config`）

### 2.1 逐指令第一分歧

```
orig set_cgroup_config: 653 insns | prod: 654 insns
首个线性分歧 idx508 off3618  POP_JUMP_FORWARD_IF_FALSE 4414(orig) vs 4416(prod)   ← 纯位移伪影
首个结构分歧 idx620 off4412：
  ORIG  JUMP_FORWARD 4446            （then 臂跳到共享汇合块）
  PROD  LOAD_CONST None(4412) / RETURN_VALUE(4414)   （汇合块被就地复制）
```
ORIG 尾部：`…system_log.info(…) / JUMP_FORWARD 4446` → else 臂 `4414..4444` → `4446 LOAD_CONST None; RETURN_VALUE`（函数唯一出口块，2 前驱）。
PROD 尾部：then 臂自带 `LOAD_CONST None; RETURN_VALUE`，出口块只剩 else 臂一个前驱。
产物源码中 try 体之后**没有** `return None` 语句，而 except 处理器以 `return None` 结尾：

```
    except BaseException:
        system_log.error('设置CGroup配置失败，错误原因：{}'.format(get_traceback_message()))
        return None            # ← 处理器末条
    <缺少 return None>          # ← 原始存在（try 自然出口的汇合块）
```

### 2.2 机制实证（CPython 侧）
`_diag` 直接编译对照：`try: if/else / except: …; return None`（无函数尾 `return None`）→ CPython 把 return **就地内联**进 if/else 两臂；而原始字节码是「两臂汇入唯一出口块」。所以缺陷 = 产物丢掉了函数级汇合出口语句，重编译后 CFG 由「1 个 2-前驱出口块」变成「2 个出口块」。

### 2.3 复现表（族 = B98）

| repro | 今日判定 | 期望修复后 | 证明什么 |
|---|---|---|---|
| `r1_43_cand_try_ifelse_hret_trailing` | **MISMATCH** `units=1/2` | success | 最小标本：try{if/else} + 处理器 `return None` + 函数尾 `return None` |
| `r1_44_cand_cgroup_microcosm` | **MISMATCH** | success | 真实文件微缩版（guard return + 嵌套 if/else + 2 块 + 处理器 return + 尾 return） |
| `r1_47_cand_try_while_hret_trailing` | **MISMATCH** | success | 宿主换成 while |
| `r1_48_cand_try_for_hret_trailing` | **MISMATCH** | success | 宿主换成 for |
| `r1_49_cand_tryintry_hret_trailing` | **MISMATCH** | success | try 套 try（深度形） |
| `r1_50_cand_method_hret_trailing` | **MISMATCH** `units=2/3` | success | 类方法宿主 |
| `r1_52_cand_hraise_trailing` | **MISMATCH** | success | 处理器以 `raise` 结尾（终止臂）同样触发 |
| `r1_53_cand_trystmt_hret_trailing` | **MISMATCH** | success | **深度 1** 也错：try 体单语句仍丢尾 `return None`（orig `JUMP_FORWARD 100` → prod 出口块整体消失，27→26 insns） |
| `r1_45_cand_hnoreturn_trailing` | MATCH | 必须仍 MATCH | 去掉处理器末尾 `return None` → 尾 `return None` 正常保留（产物含 `return None`） |
| `r1_38_cand_try_ifelse_hret` | MATCH | 必须仍 MATCH | 去掉函数尾 `return None` → 正确 |
| `r1_51_cand_hret_trailing_nonnone` | MATCH | 必须仍 MATCH | 尾语句改 `return 1`（非 None）→ 保留，缺陷专属 `return None` |
| `r1_46_cand_notry_ifelse_trailing` | MATCH | 必须仍 MATCH | 无 try 宿主 → 正确，缺陷需 Try 区域 |
| `r1_60/r1_61`（try 体以 `return x` 结尾） | MATCH | 必须仍 MATCH | 兄弟形（处理器与 try 体都终止于非常量 return）不受影响 |
| `r1_30…r1_37, r1_39…r1_41` | MATCH | 必须仍 MATCH | 模块体/类体/循环/嵌套 if/elif/else 各宿主浅-深负对照 |
| `r1_42_self_product_cgroup` | MATCH `units=8/8` | — | pycdc 对**自身产物字节码**是幂等的（8/8）⇒ 缺陷只在原始形态方向丢失，标本必须取原始形 |

标本↔对照的具体改动：删掉处理器末条 `return None`（43→45）、删掉函数尾 `return None`（43→38）、把尾语句改成 `return 1`（43→51）、去掉 try（43→46），四者均使判定由 failure 翻回 success，且 `OK.py` 文本差异恰为那一条语句的有无。

### 2.4 破口登记

**B98 — TryRegion 自然出口汇合块被处理器 return 吞并，函数级 `return None` 未发射**
- 锚点：`site-packages/IQCommon/util/cgroup_utils.pyc` / `<module>.set_cgroup_config` / orig off **4412 `JUMP_FORWARD 4446`** vs prod off 4412 `LOAD_CONST None; RETURN_VALUE`；标本 `r1_43` off **46 `JUMP_FORWARD 78`** vs prod `LOAD_CONST None; RETURN_VALUE`；`r1_53` off **34 `JUMP_FORWARD 100`**（出口块整体缺失）。
- 机制：出口块（`LOAD_CONST None; RETURN_VALUE`，try 区域自然退出 / if-else 链的汇合后继）被最后一个 handler 的终止 return 认领，函数体语句序列里不再作为兄弟语句发射 ⇒ try 区域出口归属错误；重编译后 CPython 把 return 内联回各臂，汇合块前驱由 2 变 1。
- 违反条款：**C1 局部消费 + 原则2（每块唯一归属）**（handler 区域内联消费了非本区域 `L(A)` 的汇合块）；亦违 §1.5 推论的修复语义——缺陷**不是深度形**（`r1_53` 深度 1 即错），故禁止用深度/语料门控修。
- 站点（已 grep 核实存在，只指认不建议修法）：
  `core/cfg/code_generator.py:2232 _filter_trailing_return_none`（含 `:2218` 与 `:521` 两个调用点；`_is_after_try` 豁免在 `:2321-2355`，仅覆盖「前一条语句是 Try」这一种兄弟形）、
  `core/cfg/region_ast_generator.py:2154 _build_function_def`（`:2345 _has_explicit_return_recursive`、`:2372-2392` 出口计数与「始终保留 return None」决定）、
  `core/cfg/region_ast_generator.py:29067 _generate_try`（`:30704-30734` 把 `has_trailing_return_none` 单 BASIC 兄弟区域并入 `ast.Try.body` 的 r65 归位逻辑）、
  `core/cfg/region_analyzer.py:1315 _check_block_has_trailing_return_none`、`region_analyzer.py:212/217 has_trailing_return_none/mark_trailing_return_none`（写入点 `:4855`、`:20618-20621`、`:22140+`、`:30782`）、
  `core/cfg/region_ast_generator.py:57446 _is_trailing_return_none_statement` / `:57461 _filter_module_level_returns`。

---

## 3. pyc #2 `site-packages/IQCommon/util/email_utils.pyc`（3/4，`<module>.send_email`）

### 3.1 逐指令第一分歧

```
orig 222 insns | prod 224 insns
idx193 insert:  PROD 多出 LOAD_CONST None(1120) / RETURN_VALUE(1122)
真实首分歧在更早处（跳转边目标）：
  idx28 off130  POP_JUMP_FORWARD_IF_FALSE  ORIG→674   PROD→1120
```
即 `if attachment_path != '':` 的假臂跳转：原始跳到 **674**（紧随 if 链之后的近邻汇合块，其后 `674..1118` 是 try 体内与该 if **同层的兄弟语句**，以 `return return_info`(1118) 结尾）；产物把跳点推到 **1120**（try 体尾），并把 674..1118 整段吸收进 if 链的臂内；因吸收后 try 体出现可达自然出口，重编译多出一个 `LOAD_CONST None; RETURN_VALUE`。

### 3.2 复现表（族 = B100，宿主 = try 体）

| repro | 今日判定 | 期望修复后 | 证明 |
|---|---|---|---|
| `r1_75_cand_try_arm_absorb` | **MISMATCH** `units=1/2` | success | try 体内 if/else 吸收后续兄弟语句：off48 跳转 142→186（opname 序列全同，仅边不同） |
| `r1_80_cand_try_arm_absorb_ctrl` | **MISMATCH** | success | 同形但处理器不终止 → 仍错，证明与 handler 终止性无关（区别 B98） |
| `r1_81_cand_flat_arm_absorb2` | MATCH | 必须仍 MATCH | **去掉 try 宿主**（同 if 嵌套 + 同兄弟语句）→ 正确：宿主形为 try 体时才炸 |
| `r1_79_cand_flat_arm_absorb` | MATCH | 必须仍 MATCH | 平铺宿主负对照 |
| `r1_66/r1_67/r1_70` | MATCH | 必须仍 MATCH | 无 return 终止臂 / 无后续兄弟 的浅对照 |

### 3.3 破口登记
**B100**（与 pyc #3/#4/#5 同一机制，见 §6/§7）— 锚点：`site-packages/IQCommon/util/email_utils.pyc` / `<module>.send_email` / off **130 `POP_JUMP_FORWARD_IF_FALSE 674 → 1120`**，副产物 off1120 多出 `LOAD_CONST None; RETURN_VALUE`。
- 站点（grep 核实存在）：`core/cfg/region_analyzer.py:2585 _compute_merge_from_jump_targets`、`core/cfg/region_analyzer.py:2974 _compute_in_loop_if_merge`（循环感知 merge 重算 = R24A 家族的现行实现体）、`region_analyzer.py:1967-1968 _cr.merge_block/_cr._shared_merge_block` 改写点。

---

## 4. pyc #3 `site-packages/IQData/utils/calexrights_func.pyc`（7/8，`<module>.change_his_to_forward`）

### 4.1 逐指令第一分歧

```
orig 426 | prod 427
idx199 insert EXTENDED_ARG（伪影）→ 真实：off1022 POP_JUMP_FORWARD_IF_FALSE  ORIG→1328  PROD→2148
idx244/245                        → 真实：off1324 POP_JUMP_FORWARD_IF_FALSE  ORIG→1328  PROD→2132，且 ORIG 的 off1326 NOP 在 PROD 消失
```
ORIG：外层 `if <A>:`（off 1022）假臂与内层 `if <D>:`（off 1324）假臂**都汇入近邻块 1328**（`LOAD_FAST pre_index; POP_JUMP_FORWARD_IF_NOT_NONE 1712`，1328..2130 是循环体内与 if 链同层的兄弟语句）。
PROD：两条跳转都改投 2132/2148（循环体尾），即 1328..2130 被吸收进 if 链的臂。D 臂的 NOP（空体行追踪）同步丢失。

### 4.2 复现表（族 = B100，宿主 = 循环体）

| repro | 今日判定 | 期望修复后 | 证明 |
|---|---|---|---|
| `r1_68_cand_for_arm_absorb` | **MISMATCH** `units=1/2` | success | for 体内 `if A: if C: continue / if D: pass` + 同层兄弟语句；off32 跳转 86→150，off82 86→150，NOP 丢 |
| `r1_69_cand_for_nested_absorb` | **MISMATCH** | success | 臂内再嵌一层 if/else，同一跳转外推（46→206、96→206） |
| `r1_76_cand_while_arm_absorb` | **MISMATCH** | success | 宿主换 while：off38 68→132 |
| `r1_77_cand_nestedfn_arm_absorb` | **MISMATCH** `units=2/3` | success | 宿主 = 含嵌套函数定义的函数的循环体 |
| `r1_78_cand_method_arm_absorb` | **MISMATCH** `units=2/3` | success | 宿主 = 类方法循环体：off32/88/112 全部 116→180 |
| `r1_66_cand_else_absorb_siblings` | MATCH | 必须仍 MATCH | 同 if 形状但宿主为函数体平铺 → 正确 |
| `r1_67_cand_loop_else_absorb` | MATCH | 必须仍 MATCH | 循环体内 if/else 但臂内不终止、无 `pass` 空体 → 正确 |
| `r1_70_cand_chain_controls` | MATCH `units=3/3` | 必须仍 MATCH | if/elif/else + 兄弟语句（平铺）与纯 if/else 收尾两种负对照 |
| `r1_36_cand_loop_try_nest` | MATCH | 必须仍 MATCH | try 套循环宿主对照 |

标本↔对照的具体改动：把 `if n[0] == end: pass` 的空体/臂内 `continue|return` 终止形去掉，或把整段从循环体/try 体挪到函数体平铺（68→66/67/70），判定即由 failure 翻回 success；两两 `OK.py` 文本差异恰是被吸收进臂的那几条兄弟语句的缩进层级。

## 5. pyc #4 `site-packages/IQData/plugins/plugin_system_fly_basicdata/calexrights_func.pyc`（7/8，同名单元）

逐指令与 #3 **完全同形**（同偏移、同跳转外推）：
```
orig 426 | prod 427
idx199 EXTENDED_ARG insert → off1022 POP_JUMP_FORWARD_IF_FALSE  ORIG→1328  PROD→2148
idx244/245                → off1324 POP_JUMP_FORWARD_IF_FALSE  ORIG→1328  PROD→2132 + NOP(off1326) 丢
```
两文件字节不同（12423 vs 12537，产物 9839 字节同名函数）但失败单元与偏移逐位一致 ⇒ 同一份源码的两份编译副本，机制唯一。复现表 = §4.2 同一套（标本 5 + 对照 4 已覆盖两种宿主与两种臂深）。
**B100** 锚点：`…/plugin_system_fly_basicdata/calexrights_func.pyc` / `<module>.change_his_to_forward` / off 1022 `1328→2148`、off 1324 `1328→2132`。

---

## 6. pyc #5 `site-packages/IQCommon/data/finance.pyc`（31/32，`<module>.get_fields`）

### 6.1 逐指令第一分歧

```
orig 177 | prod 178
idx23 insert EXTENDED_ARG（伪影）→ 真实：off92 JUMP_FORWARD  ORIG→236  PROD→742
（其余全部跳转目标 +2 位移，属重编译对齐，判据已豁免）
```
ORIG：`if table == 'valuation':` 的 then 臂以 `error_msg, financial_data_tmp = get_finance_open_api_data(…)` 结束，off92 `JUMP_FORWARD 236` 跳到紧随整个 if/else 链之后的**近邻汇合块 236**，236..740 是同层兄弟语句。
PROD：同一条跳转改投 **742**（函数尾块）⇒ else 臂吸收了 236..740 的兄弟语句，then 臂跳过了本应两臂都执行的代码。

### 6.2 复现表（族 = B100，宿主 = 函数体内联 if/else + 后续兄弟）

| repro | 今日判定 | 期望修复后 | 证明 |
|---|---|---|---|
| `r1_68/r1_69/r1_76/r1_77/r1_78`（§4.2） | **MISMATCH** | success | 跳转外推同一机制的 5 个标本（循环宿主族） |
| `r1_75/r1_80`（§3.2） | **MISMATCH** | success | 同机制的 try 宿主族，与 #5 同为「非循环宿主」 |
| `r1_66/r1_67/r1_70/r1_79/r1_81` | MATCH | 必须仍 MATCH | 平铺/无终止臂/无后续兄弟 负对照 |
说明：#5 的**最小标本未单独再造一条与 `get_fields` 完全同宿主（含 try + 循环 + 解包赋值）的 ≤20 行样本**；现有 B100 标本覆盖同一判据形态（外推的臂跳转 + 兄弟吸收），`r1_75/r1_78` 即非循环宿主两例。此点如实标注，未夸大为「#5 专属标本」。

### 6.3 破口登记
**B100** 锚点：`site-packages/IQCommon/data/finance.pyc` / `<module>.get_fields` / off **92 `JUMP_FORWARD 236 → 742`**。

---

## 7. pyc #6 `site-packages/IQCommon/logger/handlers.pyc`（29/30，`<module>.TWHThreadController._target`）

### 7.1 逐指令第一分歧

```
orig 203 | prod 201
idx74 delete ['LOAD_CONST','RETURN_VALUE'] → 真实：ORIG 有 off404/406 与 off408/410 两个出口块，PROD 只剩一个
边变化：ORIG idx17 off102 POP_JUMP_FORWARD_IF_FALSE 408（「循环从未进入」出口）
        PROD 同一条边改投合并后的单一出口块
其余跳转目标 +2/+4 位移属对齐伪影。
```
产物源码该分支为 `while self.running: try/except/else …` 后跟一条 `return None`；CPython 为此形态发射**两个** `LOAD_CONST None; RETURN_VALUE` 无后继 sink 块（循环跳过 / 循环正常退出），反编译器把两个 sink 归并成一条 `return None` ⇒ 少一个出口块、一条边改投。

### 7.2 复现表（族 = B99）

| repro | 今日判定 | 期望修复后 | 证明 |
|---|---|---|---|
| `r1_65_cand_while_try_sinkpair` | **MISMATCH** `units=3/4` | success | 类方法内 `if …: while+try/except/else / return None` + 后续兄弟；idx39 ORIG `LOAD_CONST,RETURN_VALUE` vs PROD `JUMP_FORWARD` |
| `r1_74_cand_whiletry_noelse` | **MISMATCH** `units=1/2` | success | 去掉 try 的 `else` 仍错 ⇒ sink 归并与 else 无关 |
| `r1_73_cand_fortry_sinkpair` | **MISMATCH** `units=1/2` | success | 宿主换 for 循环，同族（出口块改投 + 语句序变化） |
| `r1_72_cand_whiletry_sinkpair_fn` | MATCH | 必须仍 MATCH | 把该 `if` 外层去掉（循环+`return None` 直接作函数末）→ 正确：既有「函数末」守卫有效 |
| `r1_64_cand_while_if_sinkpair` | MATCH | 必须仍 MATCH | 循环体不含 try → 正确（需 try 形才分裂 sink） |
| `r1_62_cand_while_epi_dup` / `r1_63_cand_while_epi_dup_fn` | MATCH `units=4/4`/`2/2` | 必须仍 MATCH | 裸 while 结尾（无 return 语句）函数/方法宿主对照 |

标本↔对照的具体改动：删掉外层 `if v == 3:` 使其成为函数末语句（65→72）、或删掉循环体内 try/except（65→64），判定即由 failure 翻回 success。

### 7.3 破口登记
**B99 — 循环+尾随 `return None` 的双 sink 出口块在非函数末分支内被归并为单条语句**
- 锚点：`site-packages/IQCommon/logger/handlers.pyc` / `<module>.TWHThreadController._target` / ORIG off **404 LOAD_CONST None; 406 RETURN_VALUE** 与 **408/410** 两块 → PROD 仅存一块；标本 `r1_74` idx32 `['LOAD_CONST','RETURN_VALUE'] → ['JUMP_FORWARD']`。
- 机制：出口块计数/归属判据只在**函数体层**生效（区域级信息被当作全局信息消费），当 `while + return None` 位于 `if` 臂内时，「循环从未进入」与「循环正常退出」两个无后继 sink 被认作同一条隐式返回语句发射。
- 违反条款：**C3 守卫封闭**（既有守卫作用域未闭合到分支层：按区域层级差别对待）+ **原则2 每块唯一归属**（两个不同块归并为一条语句）；同处亦触 §1.2 原则4（出口引用语义隐式化）。
- 站点（grep 核实存在）：`core/cfg/region_ast_generator.py:2364-2378`（`_build_function_def` 内 trailing-return-None 出口块计数，注释自陈「函数末语句是 while/for 循环时」）、`core/cfg/region_analyzer.py:1315 _check_block_has_trailing_return_none`、`region_analyzer.py:212/217`、`core/cfg/code_generator.py:2232 _filter_trailing_return_none`。

---

## 8. 跨文件家族分析：三个 `change_his_to_forward`（#3、#4、quotation 锚点）

quotation（`site-packages/fly/data/quotation.pyc`，基线 152/153，唯一失败单元 `<module>.change_his_to_forward`）逐指令比对（本轮只读比对，不占判据）：

```
orig 597 | prod 598
idx272 insert EXTENDED_ARG / idx327 insert EXTENDED_ARG / idx328 delete NOP
真实边差：ORIG off1366 POP_JUMP_FORWARD_IF_FALSE → 1748   |  PROD off1368 → 2912
（off1048/1092/1160/1204/1300/1302 等其余跳转在两版中一致）
```

三处同名单元的读数并列：

| 文件 | orig/prod insns | 臂跳转外推（ORIG→PROD） | EXTENDED_ARG | NOP 丢 |
|---|---|---|---|---|
| `IQData/utils/calexrights_func.pyc` | 426/427 | 1022: 1328→2148；1324: 1328→2132 | +2 | 1（off1326） |
| `IQData/plugins/…/calexrights_func.pyc` | 426/427 | 同上，偏移逐位相同 | +2 | 1（off1326） |
| `fly/data/quotation.pyc` | 597/598 | 1366: 1748→2912 | +2 | 1 |

**结论：一个机制同时解释三处（#3/#4/quotation）** —— 循环体内 if 链的臂跳转被外推到循环体尾（+2 位移与 EXTENDED_ARG 是其算术后果，不是独立缺陷），且伴随空体 `if …: pass` 的行追踪 NOP 丢失。#2/#5 是同机制在 try 体/函数体内的实例（外推目标为 try 体尾/函数尾）。故 Round 1 的 B100 覆盖 pyc #2/#3/#4/#5 四个失败单元 + quotation 的终局单元（Round 4 面）；B98 覆盖 pyc #1；B99 覆盖 pyc #6。

与 `rules.md` 既有记录的对应：R24A「`change_his_to_backward` IF 吸收兄弟，修复 = 循环感知 merge 重算」（§7.1）是**同名家族的既往形态**；本轮 `change_his_to_forward`（三处）呈同一形态的反向臂，说明 R24A/B3 守卫族未封闭「臂的后继 join 被吸收」的另一侧。

---

## 9. 破口汇总（本轮新登记 B98–B101）

| 编号 | 覆盖 pyc / 单元 | 锚点（opcode/offset） | 机制一句话 | 违反条款 |
|---|---|---|---|---|
| **B98** | #1 `set_cgroup_config` | off4412 `JUMP_FORWARD 4446` vs `LOAD_CONST None/RETURN_VALUE`；标本 off46 `JUMP_FORWARD 78` | try 区域自然出口的函数级汇合出口块被末位 handler 的终止 return 吞并，函数尾 `return None` 未发射 | C1 局部消费 + 原则2/原则4 |
| **B99** | #6 `_target` | off404/406 + off408/410 双 sink → 单 sink；标本 `LOAD_CONST,RETURN_VALUE → JUMP_FORWARD` | 循环跳过 / 循环正常退出的两个 `return None` sink 块在 `if` 臂内被归并为一条语句，既有出口计数守卫只覆盖函数末 | C3 守卫封闭 + 原则2 |
| **B100** | #2 `send_email`、#3/#4 `change_his_to_forward`、#5 `get_fields`（+quotation 同名单元） | #2 off130 `674→1120`；#3/#4 off1022 `1328→2148`、off1324 `1328→2132`；#5 off92 `236→742`；quotation off1366 `1748→2912` | IfRegion 臂的 merge/join 取成外层作用域尾（循环体尾/try 体尾/函数尾），紧随 if 链之后的同层兄弟语句被吸收进臂，臂跳转外推（并伴随空体 `if …: pass` 的行追踪 NOP 丢失） | C1 局部消费 + 原则2/原则3（§3.2.1 边界判定） |
| **B101** | 附带发现（非本轮 6 靶，来自形态搜索 `test_repros/round1/_search/handler_ifelse.pyc` `<module>.f`） | orig 107 insns vs prod 76 insns（`-31`）：try 体内两条文本完全同形的 `if k1==1: … else: …` 兄弟块只剩一条 | 同形兄弟块被 `generated_blocks/generated_offsets` 过度标记而丢弃（语句丢失，原则2 的反向形态） | 原则2 每块唯一归属（过度认领）。**注意：本条为合成标本，未在 6 个目标 pyc 中定位实例，仅登记线索，禁止据此改判据** |

**关于「深度形」的如实结论**：本轮 3 个真缺陷都**不是**「深层才错、浅层没事」——B98 在深度 1（`r1_53`）即失败，B100 在两层 if（`r1_66/67`）为 MATCH 而在「循环/try 宿主 + 臂内终止 + 同层后续兄弟」形失败，B99 在函数末形（`r1_72`）为 MATCH。判据差异的真实维度是**区域成员关系与宿主区域类型**，不是嵌套深度。因此 §1.5 推论在此的用法是：修复必须封闭 C1/C2/C3 守卫、按区域成员关系判据（块末 opcode / 后继前驱 / 异常边 / 区域成员）落地，**禁止按深度或语料个案门控**；若修复采用深度阈值或文件/函数名白名单即为反模式（§2.2/§2.3）。

## 10. 电池索引

`test_repros/round1/r1_probe_index.json`（46 条目，格式同 `round2/r2_probe_index.json`，可 `pyc_verify batch --index` 直接跑）：
- B98 标本 8（MISMATCH）+ 对照 17（MATCH）
- B99 标本 3 + 对照 4
- B100 标本 7 + 对照 5
- B101 附带 1（MISMATCH）
- 附 `r1_42_self_product_cgroup.pyc`（幂等性证据，MATCH）
合计 **19 MISMATCH / 27 MATCH**（标本=修复后必须转 MATCH；对照=修复后必须保持 MATCH）。
另：`test_repros/round1/` 下 `n1_*`、`r1_01…r1_22`、`rv_*`、`r1_reg_*` 属既往轮次遗留文件，**不是本轮标本**，未写入索引。

索引自检（唯一判据，实测原文）：

```
python -X utf8 scripts/pyc_verify.py batch --index test_repros/round1/r1_probe_index.json --json test_repros/round1/_battery_baseline.json
files_total=46 units_success=91/110 success_rate=0.8272727272727273
files_by_status={'compile_error': 0, 'error': 0, 'failure': 19, 'success': 27} elapsed_sec=25.6
```
即 19 个标本今日 MISMATCH、27 个对照今日 MATCH，与上表逐条一致；`git status --short core scripts bytecode parsers utils pycdc.py site-packages` = 空（本轮零生产改动、零产物改动）。

## 11. 未完成 / 风险声明

1. pyc #1、#2、#3、#4、#5、#6 全部完成到「第一分歧 + 机制 + 破口登记 + 复现族」；#5 未另造「与 `get_fields` 完全同宿主」的专属最小标本（§6.2 已如实标注）。
2. 未重跑 402 全量与八分片（按硬约束），未跑 quotation `single`（只做了 pyc↔OK.py 只读逐指令比对）。
3. B98/B99 共用 `_filter_trailing_return_none` / `has_trailing_return_none` 家族符号，修复时两族判据面可能互相牵动：`r1_42`（幂等 8/8）与 §2.3/§7.2 的 MATCH 对照是回归哨兵，任何修复后 `units=1/2` 的 MISMATCH 集合必须全部转 success 且上述 MATCH 集合一个都不能变差。
4. 每条命令均 <300s（最长：形态搜索 20 例 39.9s，单文件 single 6.5s）。
