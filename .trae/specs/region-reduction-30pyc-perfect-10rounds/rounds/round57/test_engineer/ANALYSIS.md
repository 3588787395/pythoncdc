# Round 57 缺陷分析 — plugin_system_trade/function.pyc

测试工程师：纯研究 + 复现，未改动 core/、pycdc.py 与任何 *OK.py。

## 1. 度量结果

| 尺 | 结果 |
|---|---|
| 严格尺 `python _r10_strict_check.py site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | 68/71，3 缺陷，全部 [seq_len] |
| 官方尺 `python scripts/pyc_batch_verify.py single ...` | 69/71，2 mismatch（cancel 仅严格尺失败） |

失败函数（严格尺，过滤后指令数）：

| 函数 | orig | decomp | Δ | 官方尺 |
|---|---|---|---|---|
| `<module>.cancel_order_ex_handle` | 223 | 224 | +1 | 通过 |
| `<module>.get_entrust_item_info` | 535 | 531 | −4 | mismatch（first_diff #375 orig `LOAD_GLOBAL int` vs decomp `LOAD_GLOBAL float`） |
| `<module>.order_entrust_info_handle` | 220 | 225 | +5 | mismatch（first_diff #64 orig `JUMP_FORWARD→958` vs decomp `LOAD_FAST stock_code`） |

产物稳定性：functionOK.py sha256 `A5DAB685E6A0216FF28C40E6D09A155FB9E8C41A924DA1A22ED991236A5E3F84`（68638 字节），batch verify 重复生成同哈希，确定性无异常。

## 2. 逐函数根因

### 2.1 cancel_order_ex_handle（+1）— 尾随显式 `return None` 被丢弃

orig 尾部（偏移 912–1058）：`if error_dict.get('error_no') != 0: strategy_log.error(...)` else `strategy_log.info(...)`，then 臂以 `JUMP_FORWARD→1054` 汇入 `1054: LOAD_CONST None; RETURN_VALUE`，else 臂 fall-through 汇入同一块。

**关键实证**（本机 Python 3.11.7 控制实验）：
- 源码 `if/else`（无尾随 return）→ then 臂**内联** `LOAD_CONST None; RETURN_VALUE`（139 无 JUMP_FORWARD）；
- 源码 `if/else` + 尾部 `return None` → then 臂 `JUMP_FORWARD` 汇入共享 return 块——与 orig 形状完全一致。

结论：orig 源码尾部存在**显式 `return None` 语句**。反编译把它当作隐式函数尾声消费掉（functionOK.py:925-928 只有 if/else，无 return），重编译时 3.11.7 将隐式 return 内联进 then 臂，+1 指令。

**判定信号（反编译器缺失的）**：None-return 块若存在**跳转前驱**（then 臂 JUMP_FORWARD + else fall-through = 2 前驱）⇒ 源码是显式 `return None`，必须发射；仅 fall-through 单前驱的 None-return 块才可按隐式尾声消费（此时不发射与显式发射重编译等价，严格尺均通过）。

嫌疑位置：`_is_implicit_return_block`（core/cfg/region_ast_generator.py:15059，仅按内容 LOAD_CONST None+RETURN_VALUE 判定，不看前驱）；trailing return 剥离族（region_ast_generator.py:12487 `not _is_implicit_return_none(trailing_return)` 丢弃分支、36165/36537「trailing implicit return None —— 不发射」）。

复现：r57_01/02/16 MISMATCH（+1/+1/+1）；反证 r57_03（`return error_dict` 非 None）MATCH、r57_12（无尾随 return）MATCH。

### 2.2 get_entrust_item_info（−4）— 三元作为嵌套调用实参的下标赋值错构

orig 单语句（偏移 2582–2782，源行 884）：

```python
out['amount'] = int(float('+%s' % item.get('entrust_amount') if item.get('entrust_bs') == '1' else '-%s' % item.get('entrust_amount')))
```

被发为（functionOK.py:633）：

```python
item['+%s' % item.get('entrust_amount') if item.get('entrust_bs') == '1' else '-%s' % item.get('entrust_amount')] = float
```

三元 T 本身重建正确，但被误绑为 `item[...]` 的下标键；`float` 从被调方变裸名字值；`int()` 包装与真实目标 `out['amount']` 丢失。即 merge 消费者链 `CALL float → CALL int → STORE_SUBSCR out['amount']` 未被识别，回落到某种下标赋值模式时栈语义整体错位。

嫌疑位置：`_try_build_ternary_merge_consumer_expr`（core/cfg/region_ast_generator.py:39591，调用点 34805/34967/36743，R54 OUTCOME 已提及）。

**隔离结论**（r57_04/05/06/17/18）：`out['amount'] = int(float(T))` 复现 −4 签名；单层调用 `float(T)`、`int(T)` 同样失败（−2）；**普通名字赋值 `amount = int(float(T))` 通过**。⇒ 触发条件 = 三元 merge 消费者为 CALL **且** 存储目标为 STORE_SUBSCR，与外层内建名（int/float）无关。

### 2.3 order_entrust_info_handle（+5）— 循环内 if/elif/else 链的臂边界/merge 混乱（三处耦合表现）

orig 结构（已全量重建，偏移见括号）：try(2) → 外层 for orders(8→1310) → 内层 for entrust(20→1306) → 守卫 if(24–84，假边→1302 回边) → if/elif/elif/else(business_type，stock 66–458 / future 460–682 / option 684–906 均 `JUMP_FORWARD→958`；else 908–956 error+continue) → **公共尾 958** `if stock_code == order.symbol:`{ 状态检查(968–1088，error+break@1086→1298)；SPECIAL 检查(1090–1238，`not in ...keys()` CONTAINS_OP argval=1)→eval 赋值；`in ('4','5','7','8')` 检查(1240–1296，CONTAINS_OP argval=0)→`_filled_amount` 赋值；**共享 break 中转块 1298**（POP_TOP+JUMP_FORWARD→1306，真臂 fall-through 与假臂 POP_JUMP 双前驱）} → except BaseException(1314+) 体= error log。

- **缺陷 A（公共尾内联）**：公共尾(958–1296)被内联进 stock 臂（functionOK.py:740-750），future/option/else 臂丢失尾。三个非 else 臂的 `JUMP_FORWARD→958` 未被识别为「跳向链后兄弟」，链 merge 计算疑要求所有臂出口可达 merge，而 else 臂 continue 破坏该对称。嫌疑：`_build_basic_if_region` / `_build_elif_region`（core/cfg/region_analyzer.py:17610 / 18073）及臂体收集边界。
- **缺陷 B（共享 break 中转块误绑 else）**：1298 中转块（双前驱）被发成 `else: break`（functionOK.py:749-750），orig 是无条件尾随 break——真臂路径语义反转。R55-A `_generate_block_statements` 合取⑦要求唯一前驱故未消费；随后 if 区域构建把中转块当 else 臂，未检查**真臂正常后继也落入同一块**（merge-vs-else-arm 混乱）。嫌疑：`_try_generate_conditional_break_or_continue`（core/cfg/region_ast_generator.py:22076）。
- **缺陷 C（except 体迁移到伪造 for-else）**：handler 体（error log + 隐式 return）迁移到伪造的内层 for-else（functionOK.py:766-768 `else: strategy_log.error(...); return None`），真 except 体变 `pass`(769-770)。decomp 内层 FOR_ITER 出口直落 else 块(1324–1398)，外层出口(1404)后 except handler(1408+) 只剩 pass。嫌疑：`_find_loop_else`（core/cfg/region_analyzer.py:5018）+ `_clamp_loop_else_to_enclosing_try`(4881) 收集了 handler 块；`_identify_try_except_regions`(7295) / `_generate_handler_body_statements`（region_ast_generator.py:26043）归属判定。
- CONTAINS_OP 极性已逐一核对，orig/decomp 全部正确（argval=1 not in / argval=0 in），无极性缺陷。

**隔离边界**（r57_07–r57_15/r57_19）：
- r57_15（elif 链**无** else 臂，假边自然落入公共尾）MATCH ⇒ 缺陷 A 触发条件 = **else 臂 continue 的非对称出口**；
- r57_07/r57_08（else-continue + 公共尾）MISMATCH（−7/−10）⇒ 缺陷 A 独立可触发；极简两臂版表现更糟：else 内容变成 `continue` 后死代码、尾语句无条件化；
- r57_09（双前驱 break 中转块单独出现）MATCH、r57_10（try+双层 for+handler 单独出现）MATCH ⇒ 缺陷 B/C 与 A 上下文耦合；
- r57_19（真函数原样提取）MISMATCH：复现缺陷 A + break/merge 混乱的另一形态（`if not entrust_status not in ENTRUST_STATUS_ENUM:` 双重否定 + error log 变 break 后死代码 + SPECIAL/('4','5','7','8') 两块整体丢失，函数级 −28）——与真 pyc 的 +5/`else: break`/伪造 for-else 属同族但回落路径不同，说明该区域多个重建路径互相竞争，上下文（模块环境）决定最终发射形态。

## 3. 复现清单（19 文件，run_repros.py 实测）

复用 `pycdc.decompile_pyc`（与官方 pyc_batch_verify 相同入口）+ `_r10_strict_check.py` 逐函数严格比较；结果明细见 `minimal_repros/repro_results.jsonl`。

| 文件 | 靶缺陷 | 结果 |
|---|---|---|
| r57_01_ifelse_tail_return_none | 尾随 return None 丢弃 | MISMATCH +1 |
| r57_02_elifchain_tail_return_none | 同上（链+in-arm return） | MISMATCH +1 |
| r57_03_ifelse_tail_return_value | 探针：return 非 None | MATCH |
| r57_04_ternary_int_float_subscr_store | get_entrust 核心语句 | MISMATCH −4（与真 pyc 同签名） |
| r57_05_ternary_single_call_subscr_store | 探针：单层调用 | MISMATCH −2 |
| r57_06_ternary_int_float_name_assign | 探针：普通赋值 | MATCH |
| r57_07_elif3_continue_shared_tail | 缺陷 A（3 臂+守卫） | MISMATCH −7 |
| r57_08_ifelse_continue_shared_tail | 缺陷 A 极简版 | MISMATCH −10 |
| r57_09_shared_break_trampoline | 缺陷 B 隔离 | MATCH（需上下文） |
| r57_10_try_nested_for_handler | 缺陷 C 隔离 | MATCH（需上下文） |
| r57_11_order_entrust_integration | A+B+C 集成（裁剪） | MISMATCH（模块级 +2 + 函数级 −11） |
| r57_12_neg_ifelse_implicit_end | 负对照：隐式收尾 | MATCH |
| r57_13_neg_unique_pred_break | 负对照：唯一前驱 break（R55-A） | MATCH |
| r57_14_neg_try_single_for_handler | 负对照：单层 for handler | MATCH |
| r57_15_elif_chain_noelse_shared_tail | 探针：无 else 臂 | MATCH |
| r57_16_ifelse_tail_return_none_bare | 尾随 return None 极简 | MISMATCH +1 |
| r57_17_ternary_int_single_subscr_store | 探针：int 单层 | MISMATCH −2 |
| r57_18_ternary_int_float_extra_store | 探针：加前置同类赋值 | MISMATCH −4 |
| r57_19_full_fidelity_order_entrust | 真函数原样提取 | MISMATCH（模块 +2 + 函数 −28） |

统计：11 MISMATCH / 8 MATCH / 0 ERROR。3 个负对照全部 MATCH，5 个探针中 r57_03/06/15 划定隔离边界、r57_05/17 证明单层调用同断。

附带发现（非本靶三函数，仅 repro 模块出现）：单函数模块 + 字符串默认参数时，反编译把默认值伪造为模块 docstring（`"""stock"""`，r57_11/r57_19 模块级 +2）。

## 4. 修复建议（区域归约四原则，禁止点名单补丁）

1. **显式性信号（cancel 族）**：None-return 块的「显式/隐式」判定不能只看块内容（`_is_implicit_return_block`），必须引入前驱信息——存在跳转边汇入 ⇒ 源码为显式 `return None`，须作为语句发射；仅 fall-through 单前驱 ⇒ 可按隐式尾声消费。落点：所有调用 `_is_implicit_return_block` / `_is_implicit_return_none` 决定「不发射」的路径（region_ast_generator.py:12487、36165、36537 一带）。
2. **链 merge 对称性（缺陷 A）**：if/elif/else 链的 merge 应为「所有**未退出区域/循环**的臂出口的共同可达块」；某臂以 continue/break/return 离开时不参与 merge 可达性计算，但其余臂的 `JUMP_FORWARD` 必须终止臂体收集（臂体不得吸收 merge 块）。落点：`_build_basic_if_region`/`_build_elif_region`（region_analyzer.py:17610/18073）臂边界与 merge 判定。
3. **中转块=merge 而非 else 臂（缺陷 B）**：同一 if 的真臂 fall-through 与条件假边**同时**落入的块是 merge（if 后兄弟语句），不是 else 臂。将 R55-A 合取⑦从「唯一前驱才消费中转块」扩展为「双前驱若来自**同一个 if 的两条边**，仍按尾随 break/语句处理」。落点：`_try_generate_conditional_break_or_continue`（region_ast_generator.py:22076）与 `_generate_block_statements` 的前驱分类。
4. **handler 块所有权（缺陷 C）**：异常表 handler 入口可达的块不得被 `_find_loop_else` 收为 else_blocks（for-else 仅在无 break 时合法，且 else 链起点不得是 handler 入口）；`_clamp_loop_else_to_enclosing_try` 需校验 else 链不与 handler 区域重叠。落点：region_analyzer.py:5018/4881/7295。
5. **三元 merge 消费者链（get_entrust 族）**：`_try_build_ternary_merge_consumer_expr`（region_ast_generator.py:39591）需支持「多层 CALL 消费 + STORE_SUBSCR 目标」的完整链重建（CALL float→CALL int→out['amount'] 下标写），失败时禁止回落到会把栈元素误绑为下标键的模式；单层 CALL+下标存储同样断裂（r57_05/17）。
6. （低优先）模块级：单函数模块的字符串默认参数被发射为模块 docstring（r57_11/19 模块级 +2）。

## 5. 附录

- 关键偏移：cancel 912/998/1000/1054；get_entrust 2582–2782（first_diff #375）；order_entrust 8/20/958/1086/1298/1306/1310/1314/1408。
- functionOK.py 关键行：633（错构语句）、740-750（内联尾）、766-770（伪造 for-else + except pass）、925-928（丢失的尾随 return）。
- 前轮相关判据：R55-A（`_generate_block_statements` break 中转块合取⑦）、R54（`_try_build_ternary_merge_consumer_expr` 调用点 34805/34967/36743）、R56-A（`_detect_boolop_conditional_chain`，本轮未涉及）。
- 运行方式：`python run_repros.py`（目录 `.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round57/test_engineer/minimal_repros/`），临时产物在 `D:\Temp\opencode\r57t\repro_out\`（含各 repro 的反编译源 `*_dec.py` 供人工核对）。
