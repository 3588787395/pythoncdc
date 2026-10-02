# Round 5 攻击流程记录（ANALYSIS）

主文档 = `.trae/specs/harden-completed-forms-10rounds/rounds/round5/REVIEW.md`（攻防判定、机制锚点、破口登记、交接单）。本文件仅记流程与操作明细。

## 1. 执行序列

1. **活性探针** `probe_comp_min.py`（单函数 `[x*2 for x in xs]`）→ 编译 → pycdc 反编译 → `pyc_verify single` = **3/3 success**。管线活性确认。
2. **攻击源构造**（14 面全覆盖，13 个 r5_* + 负对照 n5_01）：
   - 初版 2 处源码级非法形态被 CPython 3.11 拒编（`[*a for a in pairs]` → SyntaxError: iterable unpacking cannot be used in comprehension；`[v for v in (s := xs)]` → assignment expression cannot be used in a comprehension iterable expression）。均为攻击源问题而非管线问题，替换为合法同族形态后重编：
     - r5_06.u_star_body：`[*a for a in pairs]` → `[[*a] for a in pairs]`（星号移入 display，结果 MATCH，见 REVIEW §1 正向记录）；
     - r5_07.w_iter_walrus → `w_two_walrus`：`[(a := x) + (b := x * 2) for x in xs]`。
3. **批量编译**：14 文件全部 `py_compile` 通过。
4. **批量反编译**：14 文件全部由 `python pycdc.py -o XOK.py X.pyc` 生成（零反编译崩溃；r5_07 产物语法非法属产物级，非工具崩溃）。
5. **逐文件判定**（唯一判据 `scripts/pyc_verify.py single`）：

| 文件 | 读数 |
|---|---|
| r5_01_comp_basic | success 13/13 |
| r5_02_genexp | success 12/12 |
| r5_03_comp_multifor | success 13/13 |
| r5_04_comp_cond | failure 12/13 |
| r5_05_comp_nested | success 19/19 |
| r5_06_comp_unpack | failure 11/13 |
| r5_07_comp_walrus | compile_error 0/0 |
| r5_08_comp_in_loop | success 14/14 |
| r5_09_comp_try | failure 11/12 |
| r5_10_comp_async | failure 9/13 |
| r5_11_comp_lambda | failure 17/19 |
| r5_12_comp_compress | success 17/17 |
| r5_13_comp_return | success 18/18 |
| n5_01_control | success 7/7 |

6. **失败单元定位**：`pyc_verify` 输出的 `***<module>.X: Failure` 行取失败单元名；`test_repros/round3/_r3_firstdiff.py` 取首分歧。r5_09/r5_11 的首分歧被 code-object 身份噪声遮挡 → 新增只读对照器 `_r5_cmp.py`（marshal 载入原 pyc、compile OK.py，逐 code object 以 (offset, opname, 归一化 argval) 三元对照，code object 归一为 `<code:名>`），两文件失败单元的完整指令差由此取得。
7. **t_try_finally 全量字节码对照**：直接 `dis` 原 pyc 与 OK.py 重编译体，取得 B24 的 28→30 指令级签名（o: CALL→…→RETURN_VALUE(98)；d: CALL→POP_TOP(30)→…→LOAD_CONST None(100)→RETURN_VALUE(102)）。
8. **walrus 字节码取证**：`w_body.<listcomp>` = `… BINARY_OP *; COPY 1; STORE_DEREF y; LIST_APPEND`（freevars=('y',)）→ B22 名袋吸收的直接证据。
9. **机制锚点核对**（全部当轮 grep/read/探针实测，非记忆）：
   - `comprehension_generator.py`（2217 行）：:910-914 多 for 判定、:1029 `_parse_multi_for_comprehension`、:1102 `'ifs': []`、:1121/:1156/:1175 ifs 仅挂 generators[-1]（B20）；:1348-1377 `_find_comp_target_names`/`_build_comprehension_target` 名袋（B21/B22）；:1189-1196 [Round10-05] dict-comp walrus 守卫先例（B22 对照）；:316-325/:1014-1024/:112-139 async 识别与 await 模板（B23）；:555-565 R9 POP_TOP Expr 降级判据候选（B24）。
   - `ast_generator_v2.py`：:1975 起 MAKE_FUNCTION flags 解码与 defaults 弹栈（B25 判据侧排除）。
   - 探针实证：对 `lam_default_arg.<listcomp>` elt 窗直接调 `ExpressionReconstructor.reconstruct` → 产出 `FunctionObject{defaults=Tuple[Name x]}`（正确）→ 丢失在区域管线装配链（B25）。
   - `region_ast_generator.py`：:2024 `_build_function_def`、:2041-2062 defaults 装配、:2311 Lambda dict、:21797-21845 `_convert_lambda_function_objects`（键清单无 elt/generators）——B25 候选锚点。
   - `code_generator.py`：:4948 `_generate_lambda_from_dict` → `_generate_arguments_dict`（:542-601）支持 defaults 渲染（B25 发射侧排除）。
10. **追加鉴别探针** `probe_lam_default.py`：lambda 默认值在函数级（fd_stmt）同样丢 → 4/6 failure → B25 升格为跨上下文破口（非推导式专属）。
11. **任务 B**（Round4 残留复验）：rv4_12/rv4_13/rv4_16/rv4_17/r4_04_match_mapping 五项 single，读数 1/4、2/4、2/4、2/4、4/6，与登记值逐一持平。
12. **任务 C**（哨兵）：quotation 152/153、jq_trans_module 65/65、quote 84/92、trade_live_broker 118/128、risk_calculation __init__ 41/43 —— 全部持平。
13. **产出**：rounds/round5/REVIEW.md（主）+ 本文件。

## 2. 本轮新增文件清单（全部在允许路径内）

- 攻击源/复现：`test_repros/round5/probe_comp_min.py|.pyc|OK.py`、`r5_01_comp_basic` ~ `r5_13_comp_return`（13 组 .py/.pyc/*OK.py）、`n5_01_control` 三件、`probe_lam_default` 三件。
- 只读配套工具：`test_repros/round5/_r5_cmp.py`（code-object 归一化逐指令 diff，判据配套，不修改 core//scripts/）。
- 评审产物：`.trae/specs/harden-completed-forms-10rounds/rounds/round5/REVIEW.md`。
- 历史遗留（本轮之前已存在，未改动）：`test_repros/round5/r5a_elif_join_REVERTED.patch`、`rounds/round5/verify_driver.py`。

## 3. 结论一句话

推导式族「完备」声明证伪：14 攻击面 8 面浅层封闭、6 面破（B20 跨 clause 条件丢、B21 target 名袋、B22 walrus 幻影 target→compile_error、B23 async 坍缩、B24 try/finally 吞 return、B25 lambda 默认值丢），登记破口 B20–B25，任务 B/C 读数零漂移。
