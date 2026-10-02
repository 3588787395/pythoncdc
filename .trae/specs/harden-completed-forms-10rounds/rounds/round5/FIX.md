# Round 5 修复记录（批次一：B20 + B21 + B22）

- 修复工程师：批次一（B20 跨 clause 过滤 / B21 解包 target / B22 walrus 幻影目标）
- 日期：2026-10-02
- 唯一判据：`scripts/pyc_verify.py single`（逐 code object 单元判 Equal，全 Equal 才 success）
- 改动文件（共 2 个 core 文件 + 3 个由 `pycdc.py` 重生成的 OK 产物，未手改任何 OK 内容）：
  - `core/cfg/comprehension_generator.py`（B20 识别/装配、B21+B22 目标解析）
  - `core/cfg/code_generator.py`（B21 目标发射：嵌套 Tuple/Starred/单元素 arity 渲染）
  - `test_repros/round5/r5_04_comp_condOK.py`、`r5_06_comp_unpackOK.py`、`r5_07_comp_walrusOK.py`（`pycdc.py -o` 重生成）
- 约束遵守：未 git commit；未修改 `.trae/specs/` 既有内容（仅新建本文件）；未修改 site-packages；全部命令 ≤300 s；调试探针零残留（`git diff` 增行 grep `print(/DEBUG/FIXME/XXX/TODO/pdb/breakpoint` 零命中）。

---

## B22（P0）— walrus 在推导式内被吸收为幻影迭代目标

- **根因**：`_find_comp_target_names`（原 :1348-1356）把推导式 code object 内**全部** `STORE_FAST/STORE_DEREF/STORE_NAME` 收进名袋，`_build_comprehension_target`（原 :1358-1377）对 >1 个名字一律发顶层 `Tuple(Name…)` 目标。3.11 中推导式内 walrus 编译为 `COPY 1; STORE_DEREF y`（原 pyc `w_body.<listcomp>` @20-22 实测），其 STORE 与迭代目标 STORE 在名袋中不可区分 → `[y := f(x) for x in xs]` 产物为 `for x, y in xs` → `SyntaxError: assignment expression cannot rebind comprehension iteration variable`，文件级 compile_error（r5_07 11 单元不可比）。
- **修复落点**：
  - `core/cfg/comprehension_generator.py:1374-1406`（`_find_comp_target_names` 加 walrus 守卫）
  - `core/cfg/comprehension_generator.py:1409-1469`（新增 `_parse_target_store_sequence`）
  - `core/cfg/comprehension_generator.py:1471-1516`（`_build_comprehension_target` 重写）
- **判据的结构事实表述**：目标存储序列 = FOR_ITER 之后由 STORE_* 与 UNPACK_SEQUENCE/UNPACK_EX 构成的**连续前缀**（叶=STORE_*；元组=UNPACK_SEQUENCE n 后恰 n 个子目标按左→右存储序；星号=UNPACK_EX arg 低 8 位星号前数/高 8 位星号后数）。walrus 的 `COPY 1; STORE_*` 不属于该前缀——其 STORE 位于 elt/if 表达式窗内、前驱是 COPY 而非 FOR_ITER/UNPACK 链，**结构上不可达**，故按结构解析时天然不被吸收；名袋回退路径（异步 GET_ANEXT 布局）则按 [Round10-05] 同一 COPY 守卫（`_cur.arg==1 ∧ _nxt∈STORE_*`）显式排除。判据只用操作码形态/栈效应，无任何名单。
- **docstring 三要素与 C1/C2/C3 落点**：`_parse_target_store_sequence`（:1410-1424 docstring：识别条件=存储序列前缀形态；归约方式=确定性递归下降；AST 映射=Name/Tuple/Starred，深度与星号组合不限；[C1] 仅读本推导式指令流、[C2] 子目标黑箱递归）+ `_build_comprehension_target`（:1472-1483，[C3] 名袋回退的 walrus COPY 守卫）+ `_find_comp_target_names`（:1375-1386，[C3] 守卫排除表达式内绑定）。
- **同根合并说明**：B21/B22 同一名袋根因，以同一 `_parse_target_store_sequence` 一并解决；walrus 排除不是独立补丁而是「前缀可达性」的结构推论。
- **自测读数**：r5_07 **compile_error 0/11 → 11/11 success（100%）**，5 函数产物全部恢复合法语法（`[(y := x * 2) for x in xs]` 等，幻影目标全部消失）。
- **边界（诚实登记）**：异步推导式（GET_ANEXT/SEND 布局，无 FOR_ITER）走名袋回退路径；该路径已带 walrus 守卫（比修复前严格更安全），但无 FOR_ITER 前缀锚点、未做 async 结构化解析——async 面属批次二（B23）辖域。

## B21 — 解包 target 嵌套拍平 / 星号坍缩

- **根因**：同 B22 名袋。`for a, (b, c) in triples` 的 `UNPACK_SEQUENCE 2; STORE a; UNPACK_SEQUENCE 2; STORE b; STORE c` 与 `for a, *rest in pairs` 的 `UNPACK_EX 1; STORE a; STORE rest` 的嵌套 arity/星号位结构信息在名袋中不可表达 → 顶层 3 元 Tuple / 普通二元解包。
- **修复落点**：
  - 识别/归约：`core/cfg/comprehension_generator.py:1409-1469`（`_parse_target_store_sequence` 递归构造嵌套 Tuple/Starred）+ :1485-1492（`_build_comprehension_target` 优先结构解析）+ :1083-1087（multi-for 路径同样改用结构解析，原 :1067-1069 的「FOR_ITER 后必须单条 STORE」限制解除）。
  - 发射：`core/cfg/code_generator.py:5099-5112`（`_generate_comprehensions_from_dict` 目标渲染统一委托 `_generate_for_target_from_dict`）与 :5472-5486（`_generate_comprehensions` dict/ASTTuple 两分支同改）——复用 [Round9-02] 既有 for-target 渲染（嵌套 Tuple 加括号、Starred 加 *前缀）。
  - arity 补全：`core/cfg/code_generator.py:1889-1906`（`_generate_for_target`）与 :1921-1942（`_generate_for_target_from_dict`）——单元素 Tuple 渲染补尾随逗号（`(b,)`/顶层 `b,`），否则 `(b)` 退化为普通名、UNPACK_SEQUENCE 1 丢失。该缺口在既有 [Round9-02] 嵌套括号逻辑中潜伏，B21 任意深度嵌套要求下由额外探针暴露并一并封闭。
- **判据的结构事实表述**：识别 = FOR_ITER 后存储序列的 UNPACK 栈结构（同 B22）；发射 = 目标节点自身形态（Tuple 递归加括号/逗号、Starred 加前缀、扁平 Tuple 保持 `k, v` 不加外括号），渲染 arity 与重编译 UNPACK_SEQUENCE/UNPACK_EX 一一对应。无任何字面量/函数名判据。
- **docstring 三要素与 C1/C2/C3 落点**：`_parse_target_store_sequence`（:1410-1424）+ `_build_comprehension_target`（:1472-1483）+ code_generator 两处 [Round5-B21] 注记（:5099-5106 三要素、:5472-5475 同引；:1924-1929 三要素 [C1]）。[C2] 子目标作为黑箱递归组合。
- **自测读数**：r5_06 **11/13 → 13/13 success（100%）**：`u_nested_target` 产物恢复 `[a + c for a, (b, c) in triples]`、`u_star_target` 恢复 `[a + rest[0] for a, *rest in pairs]`；正向面 u_tuple_target/u_star_body/u_two_star/u_dict_items 保持 MATCH。
- **嵌套无感旁证（判据外加测，/tmp 临时文件已删，不入库）**：`[a + d for (a, (b, (c, d))), *rest in xs]`、`[a + rest[0] + b for a, *rest, b in xs]`、`[a + b for a, (b,) in xs]`、`[p + q for (p, q) in xs]` 全组 9/9 success。

## B20 — 多 for 推导式跨 clause 过滤静默丢失

- **根因**：`_parse_multi_for_comprehension` 装配每个 generator 时硬编码 `'ifs': []`（原 :1102），ifs 只在 :1121/:1156/:1175 挂最内层 generator；非最内层 clause 的过滤链（`STORE x; LOAD x; POP_JUMP_BACKWARD_IF_FALSE → 本层 FOR_ITER`）无任何提取路径 → 27→23 指令静默丢条件。伴生根因：后续 clause 的 iter 表达式窗按「回扫上一个 STORE」定位（原 :1092-1096），有过滤时会把过滤跳转误收进 iter 窗。
- **修复落点**：
  - `core/cfg/comprehension_generator.py:1051-1061`（`_parse_multi_for_comprehension` docstring 补 B20 三要素）
  - :1074-1081（`_next_iter_start` 窗起点机制）、:1093-1102（每非最内层 clause 以 `[seq_end, fi_{k+1})` 为窗复用 `_extract_comp_ifs`；其返回窗起点即下一 clause iter 起点）、:1104-1117（iter 窗改用 `_iter_start`，删除回扫 STORE）
  - :1133（`'ifs': list(ifs)` 替代硬编码 `[]`）
- **判据的结构事实表述**：clause k 的过滤跳转链**全部回跳 clause k 自己的 FOR_ITER 偏移**，且位于该 clause 目标存储序列之后、下一 clause FOR_ITER 之前（最内层则在 APPEND 之前）；最后一个过滤跳转之后的指令才是下一 clause 的可迭代求值序列。故取 `[seq_end_k, fi_{k+1})` 为窗、以 `_extract_comp_ifs` 既有段机制甄别（BACKWARD 回跳段=and 成员；前向 IF_TRUE+回向 IF_FALSE=or 过滤 [R10]；混合 and/or 分组 [B6-comp]），append 锚点换成下一 clause 的 FOR_ITER 偏移；最内层保持原窗 `[store, APPEND)`，两窗不重叠（同一过滤不被双重归属，[C3] 守卫）。窗口边界只由本指令流的 FOR_ITER 偏移与存储序列末端决定——任意 clause 位置、任意 clause 数同法，无单形补丁。
- **docstring 三要素与 C1/C2/C3 落点**：:1051-1061（识别条件/归约方式/AST 映射 + [C1] 窗口边界只读本指令流、[C3] 最内层/非最内层窗口互斥守卫）+ 行内注记 :1074-1081/:1093-1102。
- **自测读数**：r5_04 **12/13 → 13/13 success（100%）**：`c_between_fors` 产物恢复 `[x + y + z for x in a if x for y in b if y for z in c]`（27 指令复原）；尾部条件面 c_single_if/c_double_if/c_ifelse_body/c_cross_for/sc_cond_set 全保持 MATCH。
- **嵌套无感旁证（判据外加测，临时文件已删）**：3 clause 双端过滤（含复合谓词 `if x > 0`）、clause 0 双 if + 最内层 if、2 clause 尾过滤 + 解包 target、4 clause 每 clause 一过滤，全组 11/11 success。
- **边界（诚实登记）**：非最内层 clause 的「三元作过滤」（Pattern B，`if (a if c else b)`）未扩展——Pattern B 是内层路径的独立检测器（`_detect_comp_ternary_as_filter`），不属于 B20 的「回跳过滤链」结构事实；该形态不在本轮复现组内，现若出现会经 `_extract_comp_ifs` 三元 break 路径降级（iter 表达式吞并三元段、过滤丢失），不会产生语法非法产物。留待后续轮按需扩展。

---

## 自测读数全表（pyc_verify single 实际输出）

### 最小验收组（转 MATCH）

| 单元 | 修复前 | 修复后 | 判定 |
|---|---|---|---|
| r5_04_comp_cond（B20） | 12/13 | **13/13 success 100.00%** | ✅ c_between_fors 转 MATCH |
| r5_06_comp_unpack（B21） | 11/13 | **13/13 success 100.00%** | ✅ 全部单元 MATCH |
| r5_07_comp_walrus（B22） | compile_error 0/11 | **11/11 success 100.00%** | ✅ 11 单元全部可比较且 MATCH |

### 回归哨兵（全部持平，arity 补全落地后二次全扫复测一致）

| 哨兵 | 登记基线 | 本轮读数 | 判定 |
|---|---|---|---|
| probe_comp_min | 3/3 | 3/3 success | 持平 |
| r5_01_comp_basic | 13/13 | 13/13 success | 持平 |
| r5_02_genexp | 12/12 | 12/12 success | 持平 |
| r5_03_comp_multifor | 13/13 | 13/13 success | 持平 |
| r5_05_comp_nested | 19/19 | 19/19 success | 持平 |
| r5_08_comp_in_loop | 14/14 | 14/14 success | 持平 |
| r5_12_comp_compress | 17/17 | 17/17 success | 持平 |
| r5_13_comp_return | 18/18 | 18/18 success | 持平 |
| n5_01_control | 7/7 | 7/7 success | 持平 |
| r5_09_comp_try（B24，批次二） | 11/12 | 11/12 failure | 持平 |
| r5_10_comp_async（B23，批次二） | 9/13 | 9/13 failure | 持平 |
| r5_11_comp_lambda（B25，批次二） | 17/19 | 17/19 failure | 持平 |
| probe_lam_default（B25，批次二） | 4/6 | 4/6 failure | 持平 |
| site-packages/fly/data/quotation.pyc | 152/153 | 152/153（99.35%） | 持平 |
| site-packages/IQCommon/strategy/jq_trans_module.pyc | 65/65 | 65/65（100%） | 持平 |
| site-packages/fly/data/quote.pyc | 84/92 | 84/92（91.30%） | 持平 |
| site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | 118/128（92.19%） | 持平 |
| site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | 41/43（95.35%） | 持平 |
| round4 r4_04_match_mapping | 4/6（REVIEW §4） | 4/6（66.67%） | 持平 |
| round4 r4_01_match_value | 6/6（现树实测①） | 6/6（100%） | 持平 |
| round4 r4_14_match_case_body | 7/7（现树实测①） | 7/7（100%） | 持平 |
| round3 r3_33_b11r_or3prefix | 4/4 | 4/4 success | 持平 |
| round3 r3_34_b10r_innerforelse_break | 1/2 | 1/2（50.00%） | 持平 |
| round2 r2_01_try_multi_handler | 3/3 | 3/3 success | 持平 |
| round2 r2_03_try_four_part | 3/3 | 3/3 success | 持平 |
| round1 r1_13_return_mixed | MATCH | 2/2 success | 持平 |
| round1 r1_02_stmt_orand | MATCH | 2/2 success | 持平 |

① r4_01_match_value（round4 REVIEW 登记 4/6）与 r4_14（登记 3/7）在当前树读数为 6/6、7/7，优于 round4 评审时登记值——该两文件源内**零推导式构造**（已逐一核对源码），且经 `git stash` 摘除本次两个 core 文件改动后复测读数相同（6/6、7/7），证实为修复前既存的现树状态（round4 后续 fix 批改善），非本次改动引入。

### round4 抽验说明

任务书要求 r4_01..r4_14 抽 3 支：实抽 r4_04_match_mapping（4/6，与 REVIEW §4 登记一致）、r4_01_match_value、r4_14_match_case_body（见上①）。另 round5 REVIEW §4 五项残留（rv4_12 1/4、rv4_13 2/4、rv4_16 2/4、rv4_17 2/4、r4_04 4/6）本轮未逐一复跑——本轮改动仅触及推导式 target/ifs 装配与渲染，五项均为 match/boolop 族面，且 r4_04 与全部推导式哨兵已复证零漂移。

## 未落地项及原因

| 项 | 状态 | 原因 |
|---|---|---|
| B22 async（GET_ANEXT 布局）目标结构化解析 | 未落地 | async 推导式无 FOR_ITER 前缀锚点，属批次二 B23（async 第二装配轴）辖域；名袋回退已加 walrus 守卫（严格优于修复前），r5_10 9/13 持平未受影响 |
| B20 非最内层 clause 三元作过滤（Pattern B） | 未落地 | Pattern B（`_detect_comp_ternary_as_filter`）是内层路径独立检测器，不属「回跳过滤链」结构事实；不在本轮复现组，降级产物仍语法合法（见 B20 边界） |
| B23/B24/B25 | 未触碰 | 批次二辖域，读数持平零漂移 |

## 落地标记（防回归监控）

`_parse_target_store_sequence`（comprehension_generator.py:1409，grep 应命中 ≥1 定义 + 调用点）、`[Round5-B20]`、`[Round5-B21]`、`[Round5-B22]` 注记族（comprehension_generator.py / code_generator.py）。
