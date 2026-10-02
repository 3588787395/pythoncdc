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

---

# Round 5 修复记录（批次二：B25 + B23 + B24）

- 修复工程师：批次二（B25 lambda 默认值 / B23 async 组合 / B24 try/finally return 推导式）
- 日期：2026-10-02
- 唯一判据：`scripts/pyc_verify.py single`（逐 code object 单元判 Equal，全 Equal 才 success）
- 改动文件（共 4 个 core 文件 + 4 个由 `pycdc.py` 重生成的 OK 产物，未手改任何 OK 内容）：
  - `core/cfg/ast_converter.py`（B25 两处装配/转换端口）
  - `core/cfg/code_generator.py`（B25 lambda 发射）
  - `core/cfg/comprehension_generator.py`（B23 外层闭包过滤 + 内层统一 clause 装配；B24 R9 收窄 + 后继块判据）
  - `core/cfg/ast_generator_v2.py`（B23 伴随：ExpressionReconstructor CALL 的 PUSH_NULL 双槽补消费）
  - `test_repros/round5/probe_lam_defaultOK.py`、`r5_09_comp_tryOK.py`、`r5_10_comp_asyncOK.py`、`r5_11_comp_lambdaOK.py`（`pycdc.py -o` 重生成）
- 约束遵守：未 git commit；未回退批次一任何修复（r5_04 13/13、r5_06 13/13、r5_07 11/11 复测持平）；未修改 `.trae/specs/` 既有内容（仅追加本章节）；未修改 site-packages；全部命令 ≤300 s；region_ast_generator.py 本批次零改动（BOM efbbbf 自检通过）；`git diff` 增行 grep `print(/DEBUG/FIXME/XXX/TODO/pdb/breakpoint` 零命中。
- 锚点实证复核更正（诚实登记）：评审 B24 交接单把触发分支标注为「:555-565 R9 POP_TOP 降级候选（精确分支待查）」；实测 t_try_finally 的 try 体被异常表保护区间在 CALL 末尾切块（块 4 只含 comp 装载/CALL，POP_TOP 在后继块内），R9 的 `any(POP_TOP)` 在该块恒假——真实触发点是 **:620 附近「R12 平凡 return 后继未命中 → else 分支无条件 Expr 降级」**。批次二对两处（R9 收窄 + else 回退分支）同批修复，机制描述以下文实测为准。

---

## B25（P0）— lambda 默认值元组整体丢失（函数级与推导式内双杀）

- **根因（实测更正评审圈定）**：评审排除的两个端口（ast_generator_v2.py:1975 flags 解码、code_generator.py:4948 dict 发射）确实正确，但丢弃点不在其圈定的 region_ast_generator 装配链，而在其后的两个**转换/发射端口**：
  1. `ast_converter.py _convert_lambda_expr`（原 :1596）把 Lambda dict 的 arguments dict **扁平化为 ASTName 列表**，`defaults`/`kw_defaults` 静默丢弃（fd_stmt 函数级：AST dict 中 Lambda.args.defaults 实测携带 `[Name x]`，转换后丢失）；
  2. `ast_converter.py _convert_expression` 的 FunctionObject 分支（原 :966-1000）对推导式内/任意未转换位形的 `<lambda>` FunctionObject 只按 `co_varnames[:co_argcount]` 重建扁平参数，不读 FunctionObject 自带的 `defaults`/`kw_defaults`（fd_in_comp 推导式级：ListComp.elt 下的 FunctionObject 实测携带 `defaults=Tuple[Name x]`，转换后丢失）。
  两端口汇合的 ASTLambda 节点本身无默认值槽位，发射侧 `_generate_lambda_expr`（原 :5439）只能渲染 `lambda x:` → 重编译 MAKE_FUNCTION 1→0、BUILD_TUPLE 1 对丢失。
- **修复落点**：
  - `core/cfg/ast_converter.py:1649-1673`（`_convert_lambda_expr` 末尾：args 为 dict 且 defaults/kw_defaults 任一非空时，把完整 arguments dict 原样挂到 `ASTLambda._args_dict` 节点属性；无默认值时显式守卫保持旧扁平路径）
  - `core/cfg/ast_converter.py:996-1040`（FunctionObject 分支：`<lambda>` 且宿主携带 defaults/kw_defaults 时，经新增 `_build_lambda_args_dict_from_function_obj`（:1675-1748）按 co_varnames 布局 + flags 位重建完整 arguments dict，统一委托 `_convert_lambda_expr` 装配）
  - `core/cfg/ast_converter.py:1727-1734`（Constant 包装原始 tuple 形态的 defaults（如 `Constant((3,))`）按元素展开，与 `_build_function_def` :2051-2057 同型处理）
  - `core/cfg/code_generator.py:5439-5474`（`_generate_lambda_expr`：携带 `_args_dict` 时委托既有 `_generate_arguments_dict`（:536，[P2-2026]）渲染 `x=d`/`*, y=d`/`*args`/`**kw`；未携带走旧扁平路径）
- **判据的结构事实表述**：defaults 的存在性与对齐完全由 MAKE_FUNCTION flags 位（0x01 位置默认 / 0x02 kw-only 默认）+ 栈序决定——flags&1 弹出的 BUILD_TUPLE n 元组按栈序对应**末尾 n 个位置形参**（发射侧 `default_idx = i - (len(args)-len(defaults))` 既有对齐式）；flags&2 弹出的 BUILD_CONST_KEY_MAP 字典按键名对齐 kwonly 形参位（无默认值位为 None）。kwonly/vararg/kwarg 形参名一律取自 code object 布局（co_varnames 分段 + CO_VARARGS/CO_VARKEYWORDS 位），无任何名单。
- **docstring 三要素与 C1/C2/C3 落点**：`_build_lambda_args_dict_from_function_obj`（:1678-1701 三要素：识别条件=FunctionObject 携带 flags 解码产物；归约方式=co_varnames 布局 + flags 位 → arguments dict；AST 映射=defaults 按栈序对齐末尾等长位置形参、kw_defaults 按键名对齐 kwonly；[C1] 只读该节点与 code object 布局、[C2] 默认值表达式子节点黑箱挂入、[C3] 无默认值位显式置 None）+ `_convert_lambda_expr`（:1654-1666，[C3] 无 defaults/kw_defaults 时显式守卫走旧路径）+ `_generate_lambda_expr`（:5441-5451，[C3] 同）。
- **嵌套无感旁证（判据外加测，/tmp 临时文件已删）**：kwdefaults 函数级（`lambda x, *, y=10`）、推导式内常量默认（`lambda t, k=3`）、返回值位形（`return lambda x=x: [comp]`）、字典值位形 + vararg（`{'h': lambda a, b=2, *args: a+b}`）、实参位形（`map(lambda v, w=1: v+w, xs)`）、async 推导式内默认（`[lambda a=a: a+x for x in xs]` 于 async comp），探针组 13/13 success。
- **自测读数**：probe_lam_default **4/6 → 6/6**、r5_11 **17/19 → 19/19**。

## B23 — async 推导式组合坍缩为 `await <iterable>()`（双层根因）

- **根因（实测双层，均在评审圈定文件内、更精确分支）**：
  1. **外层（函数体区域）**：`try_generate_comprehension_assign` 的 pre_comp 闭包装载序列过滤（原 :287-297）要求「BUILD_TUPLE 之前全部指令都是 closure 系」才认领闭包元组。async 函数前导 RETURN_GENERATOR 的伴声 POP_TOP 混入后，`MAKE_FUNCTION 8` 闭包形态的 LOAD_CLOSURE→BUILD_TUPLE 失配，BUILD_TUPLE 被当值生产指令留下 → :306 终止符守卫整块判 return None → 推导式识别被跳过 → 通用重建坍缩 `await ait()`。单 clause MATCH 组（a_async_for/a_async_cond）恰为 MAKE_FUNCTION 0 无闭包，与破口互为对照组。`[x+y async for x in ait for y in b]` 与 `[await g(x) async for x in ait]` 两个失败形态共同点正是 `MAKE_FUNCTION 8`（内层引用外层 b/g → 闭包）。
  2. **内层（comp code object）**：多 clause 判据只数 FOR_ITER；`async for + 同步 for` 内层仅 1 个 FOR_ITER + 1 个 GET_ANEXT 协议块 → 误走单 for 路径，同步 FOR_ITER 的存储序列前缀解析把第二 clause 的 target（y）认领为整体 target、iter 停留在外层传入值，async clause 结构整体不可表达。
- **修复落点**：
  - `core/cfg/comprehension_generator.py:288-312`（闭包过滤改局部状态机：closure 系 op 开启序列、紧随 BUILD_TUPLE 闭合——与同文件 :213-226 chained-pair 窗内既有模式同构）
  - :1066-1081（多 clause 入口：clause 头 = FOR_ITER ∪ GET_ANEXT 协议块，总数 > 1 即统一多 clause 路径）
  - :1192-1240（新增 `_find_async_clause_heads`：GET_ANEXT; LOAD_CONST None; SEND; (YIELD_VALUE; RESUME; JUMP_BACKWARD_NO_INTERRUPT) 协议块识别，协议尾兼容 CLEANUP_THROW/END_ASYNC_FOR，返回 (头索引, 目标存储序列起点)）
  - :1276-1393（`_parse_multi_for_comprehension` 统一 clause 装配：每 clause target 经 `_parse_target_store_sequence` 从各自头后的存储序列起点解析；async clause iter 锚点 GET_AITER、同步锚点 GET_ITER（首个 clause 用外层传入 iter，不回扫）；过滤窗 `[seq_end_k, 下一头)` 语义与 B20 同构；**is_async 标志沿 clause 归位**（async 头→1、同步头→0），删除整推导式统一标记）
  - `core/cfg/ast_generator_v2.py:1353-1372`（CALL 处理器 PUSH_NULL 双槽布局补消费：`PUSH_NULL; LOAD f` 布局中 NULL 标记位于 callable 之下，取完 func 后残留在栈中成为 BINARY_OP 假操作数——`elt = x + y + await g(x)` 组合形态的 `x + y +` 前缀由此丢失）
- **判据的结构事实表述**：async clause 头 = GET_ANEXT 取值协议块（操作码形态 + LOAD_CONST None 常量位），其目标存储序列起点 = 协议尾之后第一条 STORE_*/UNPACK_*；clause 间窗口（过滤窗/iter 窗/elt 窗）边界只由本指令流的头偏移与存储序列末端决定，async 头与同步头仅「锚点操作码选择」（GET_AITER vs GET_ITER）与 is_async 位不同——任意 async/同步 clause 混排同法。PUSH_NULL 补消费只认 `'PUSH_NULL'` 类型伪节点（永不承载用户值），真值节点不动。
- **docstring 三要素与 C1/C2/C3 落点**：`_find_async_clause_heads`（:1193-1215 三要素 + [C1] 仅读本推导式指令流、[C2] 协议块整体消费、[C3] 头判据失败即不认领）+ `_parse_multi_for_comprehension`（:1223-1275 docstring 补 [Round5-B23] 段 + 行内注记 :1297/:1313/:1353/:1386）+ 闭包过滤（:288-302 三要素式注记 + [C3] 终止符守卫宽度不变）+ ast_generator_v2 CALL 补消费（:1353-1371 三要素 + [C3] 仅认伪节点）。
- **嵌套无感旁证（判据外加测，/tmp 临时文件已删）**：async clause 双过滤（`async for x in ait if x for y in b if y`）、双 async clause（`async for x in ait async for z in c2`）、await 作 dict key（`{await g(x): x async for x in ait}`）、await 与同步 for/过滤混排（`x + y + await g(x) async for x in ait for y in b if x`）、walrus 于 async 过滤、lambda 默认于 async comp，探针组 18/18 success（修复前同组 7/18）。
- **自测读数**：r5_10 **9/13 → 13/13**。

## B24 — try/finally 包 `return <推导式>`：return 剥除、值 POP_TOP、改返回 None

- **根因（实测更正触发分支）**：t_try_finally 的 try 体被异常表保护区间在 comp CALL 末尾切块（块 4 = [LOAD_CONST <listcomp> … CALL]， succs=[异常帧头 100, 正常清理副本 30]）。R9 的 `any(POP_TOP)` 在块 4 内恒假；真实触发点是 **R12 平凡 return 后继未命中后的 else 分支**（原 :620-621）：后继块 30（finally 正常路径副本：清理语句 + POP_TOP + RETURN_VALUE）非「单条 RETURN_VALUE 平凡块」，R12 不认领 → 无条件 `Expr(comp_value)` 降级 → return 语义被吞。R9 全窗 `any(POP_TOP)` 本身也是同族隐患：清理语句自己的 POP_TOP（弹 append(...) 返回值）与「推导式值被丢弃」不可区分。
- **修复落点**：
  - `core/cfg/comprehension_generator.py:563-580`（R9 判据收窄：`instrs[wrapper_end].opname == 'POP_TOP'`——只有紧邻 wrapper 段末的 POP_TOP 弹的才是推导式值本身；R9 原形（comp; POP_TOP; LOAD_CONST None; RETURN_VALUE 单块）恰为紧邻，收窄后仍命中，**未关闭 R9**）
  - :644-668（else 回退分支前新增 B24 认领：尾项 comp + 末条指令为值消费型（非跳转）且 `_find_returns_pending_value_successor` 命中时发 `Return(comp_value)`；不标记后继为已生成，仍由 try 区域装配认领 finalbody）
  - :685-797（新增 `_find_returns_pending_value_successor`：前向正常后继块的三重结构判据，见下）
- **判据的结构事实表述**：3.11 异常表把 try 体在其保护区间末尾切块，`return <值>` 的值**压栈穿越 finally 清理段**、由清理段末尾 RETURN_VALUE 返回。后继块判据三重：(a) 非异常帧头（首指令 ∈ PUSH_EXC_INFO/CHECK_EXC_MATCH/CHECK_EG_MATCH 的块是 handler/异常边）；(b) 末条 RETURN_VALUE 之前线性无跳转；(c) 从栈深 0 起按 `dis.stack_effect` 线性模拟（未知操作码即放弃）**全程无下溢且末条 RETURN 前栈深恰为 0**——即 RETURN 的操作数不是本块产生的值而是入口悬挂值。双向反例同判据排除：`LOAD_CONST None; RETURN_VALUE`（隐式 return None）、`LOAD_FAST x; RETURN_VALUE`、`cleanup; POP_TOP; LOAD y; RETURN_VALUE`（返回块内产值）末条前栈深非 0。异常帧簿记（POP_EXCEPT/COPY/SWAP/RERAISE）按 0 效应处理（不承载用户值：except handler 内 return 经 SWAP 2 + POP_EXCEPT 剥帧留值），簿记-only 中间块沿唯一前向正常边有界穿越（≤4 跳，逐跳排除帧头）后对首个含用户操作块检查——覆盖异常表把 handler 值就位段/清理段切块的布局。try/finally 与 try/except/finally 双形同法（异常边后继被 (a) 排除，正常边即清理副本）。
- **docstring 三要素与 C1/C2/C3 落点**：`_find_returns_pending_value_successor`（:686-723 三要素全注记 + [C1] 只读本块与直接后继指令流/栈效应、[C2] 清理段整体黑箱模拟、[C3] (a)(b)(c) 三重守卫 + 簿记穿越有界）+ R9 收窄注记（:563-573，[C3] 栈顶来源/前驱形态）+ 认领分支注记（:647-662，[原则 3] 后继块仍归 try 装配）。
- **嵌套无感旁证（判据外加测，/tmp 临时文件已删）**：try/except/finally 三子句（`try: return [comp] / except TypeError: log.append(1) / finally: …`）success；多语句清理段（三条 append）success；`try: [comp]（值丢弃）/ finally: return 42` success（R9 收窄后原 discard 形不回退）；`try: out=[comp] / finally: … / return out`（store 路径不受扰）success；`return sorted(genexp)` 于 try/finally success。**未落地残留**：`return <值>` 位于 **except handler 内**且带 finally 时（无论值是推导式还是普通常量），handler 块语句由 try 区域 handler 装配子系统生成（插桩实测 handler 块不经 `try_generate_comprehension_assign`——见下文未落地表）；该形态修复前后失败签名一致（stash 对照 10/11 → 10/11），非本批次引入。
- **自测读数**：r5_09 **11/12 → 12/12**。

---

## 自测读数全表（pyc_verify single 实际输出，OK.py 全部由 pycdc.py 重生成后复测）

### 最小验收组（转 MATCH）

| 单元 | 修复前 | 修复后 | 判定 |
|---|---|---|---|
| probe_lam_default（B25） | 4/6 | **6/6 success 100.00%** | ✅ fd_stmt/fd_in_comp.<listcomp> 转 MATCH |
| r5_11_comp_lambda（B25） | 17/19 | **19/19 success 100.00%** | ✅ lam_default_arg/lam_with_arg.<listcomp> 转 MATCH |
| r5_10_comp_async（B23） | 9/13 | **13/13 success 100.00%** | ✅ a_async_multi/a_await_body 及其 <listcomp> 转 MATCH（产物恢复 `[x + y async for x in ait for y in b]`、`[await g(x) async for x in ait]`） |
| r5_09_comp_try（B24） | 11/12 | **12/12 success 100.00%** | ✅ t_try_finally 产物恢复 `try: return [x for x in xs] / finally: log.append(len(xs))` |

### 回归哨兵（全部持平；round5 全部 16 文件均以重生成 OK.py 复测）

| 哨兵 | 登记基线 | 本轮读数 | 判定 |
|---|---|---|---|
| r5_04_comp_cond（批次一验收面） | 13/13 | 13/13 success | 持平 |
| r5_06_comp_unpack（批次一验收面） | 13/13 | 13/13 success | 持平 |
| r5_07_comp_walrus（批次一验收面） | 11/11 | 11/11 success | 持平 |
| probe_comp_min | 3/3 | 3/3 success | 持平 |
| r5_01_comp_basic | 13/13 | 13/13 success | 持平 |
| r5_02_genexp | 12/12 | 12/12 success | 持平 |
| r5_03_comp_multifor | 13/13 | 13/13 success | 持平 |
| r5_05_comp_nested | 19/19 | 19/19 success | 持平 |
| r5_08_comp_in_loop | 14/14 | 14/14 success | 持平 |
| r5_12_comp_compress | 17/17 | 17/17 success | 持平 |
| r5_13_comp_return | 18/18 | 18/18 success | 持平 |
| n5_01_control | 7/7 | 7/7 success | 持平 |
| site-packages/fly/data/quotation.pyc | 152/153 | 152/153（99.35%） | 持平 |
| site-packages/IQCommon/strategy/jq_trans_module.pyc | 65/65 | 65/65（100%） | 持平 |
| site-packages/fly/data/quote.pyc | 84/92 | 84/92（91.30%） | 持平 |
| site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | 118/128（92.19%） | 持平 |
| site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | 41/43（95.35%） | 持平 |
| round4 r4_04_match_mapping | 4/6 | 4/6（66.67%） | 持平 |
| round4 r4_01_match_value | 6/6（批次一实测） | 6/6（100%） | 持平 |
| round4 r4_14_match_case_body | 7/7（批次一实测） | 7/7（100%） | 持平 |
| round3 r3_33_b11r_or3prefix | 4/4 | 4/4 success | 持平 |
| round3 r3_34_b10r_innerforelse_break | 1/2 | 1/2（50.00%） | 持平 |
| round2 r2_01_try_multi_handler | 3/3 | 3/3 success | 持平 |
| round2 r2_03_try_four_part | 3/3 | 3/3 success | 持平 |
| round1 r1_13_return_mixed | 2/2 | 2/2 success | 持平 |
| round1 r1_02_stmt_orand | 2/2 | 2/2 success | 持平 |

哨兵验证方式与批次一一致：site-packages 与 round1–4 仅运行 pyc_verify（未重生成其 OK 产物，不触碰 site-packages）；round5 全部 16 文件在批次二改码后统一 `pycdc.py -o` 重生成再验证。

## 未落地项及原因

| 项 | 状态 | 原因 |
|---|---|---|
| `return <值>` 位于 except handler 内且带 finally（探针 r1：`return []`；s2/s3：`return [comp]`） | 未落地 | 插桩实测（spy `try_generate_comprehension_assign`）该形态的 handler 块语句由 try 区域 handler 装配子系统直接生成，**不经推导式入口**（B24 判据所在路径，全 generate 期间仅块 4/46 被调用、handler comp 块 66/68 从未进入）；修复需改 handler 装配子系统（W11/SW11 try 机制），超出 B24 交接单锚点（comprehension_generator :555-565 R9 判据）辖域。stash 对照证实修复前后失败签名一致（10/11 → 10/11、6/8 → 6/8），非批次二引入。B24 交接单「try/except/finally 双形」的 comp-in-try-body 形态（探针 s1）已由本批修复覆盖并 success |
| B23 单 async clause elt 内多值表达式（`x + y + await g(x)`） | 已落地（伴随修复） | 根因不在推导式侧而在 ExpressionReconstructor CALL 的 PUSH_NULL 双槽布局缺第三槽消费（ast_generator_v2 :1353），随 B23 一并封闭（探针 18/18 内含此形） |
| B25 Constant 包装原始 tuple 形态 defaults（`Constant((3,))`，如推导式内 `lambda t, k=3`） | 已落地（伴随修复） | FunctionObject['defaults'] 在常量默认值场景为 Constant 包装 tuple 而非 Tuple 节点；按元素展开（与 `_build_function_def` :2051-2057 同型），探针 13/13 内含此形 |
| B24 交接单残留（Round4 rv4_12/rv4_13/rv4_16/rv4_17） | 未触碰 | 与批次一同样判定：本批改动仅触及推导式 target/clause/return 装配与 lambda/await 表达式端口，四项均为 match/boolop 族面；round5 全哨兵 + r4_04 已复证零漂移 |

## 落地标记（防回归监控）

`[Round5-B23]`（comprehension_generator.py :288/:1069/:1193/:1280/:1297/:1313/:1353/:1386 + ast_generator_v2.py :1353）、`[Round5-B24]`（comprehension_generator.py :563/:651/:686/:723/:736）、`[Round5-B25]`（ast_converter.py :1001/:1654/:1678/:1727 + code_generator.py :5441）注记族；新方法 `_find_async_clause_heads`（comprehension_generator.py:1192）、`_find_returns_pending_value_successor`（comprehension_generator.py:685）、`_build_lambda_args_dict_from_function_obj`（ast_converter.py:1675）grep 应各命中 ≥1 定义 + 调用点。
