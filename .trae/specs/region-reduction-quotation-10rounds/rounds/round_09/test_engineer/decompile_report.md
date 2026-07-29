# Round 9 测试工程师：反编译报告

## 1. 总体统计

- 总函数数: 150
- 一致函数数: 142
- 不一致函数数: 8
- 成功率: 94.67%
- compile_ok: True
- 相对 R8: 142→142 无退化（基线保持）

## 2. 不一致函数清单（8 个）

| 函数 | 状态 | orig_len | new_len | diff | 相对 R8 |
|------|------|----------|---------|------|---------|
| `<module>` | instr_diff@394 | - | - | - | 持平（code 对象 filename 元数据）|
| `one_prod_to_dataframe` | instr_diff@131 | - | - | - | 持平（R8 已修复 len，残留跳转目标）|
| `build_future_fill_time` | instr_diff@226 | - | - | - | 持平（listcomp code 对象 + 跳转目标）|
| `load_bars_from_hundsun` | len_diff | 501 | 413 | -88 | 持平 |
| `load_get_price` | len_diff | 226 | 200 | -26 | 持平 |
| `get_str_data` | len_diff | 317 | 269 | -48 | 持平 |
| `change_his_to_backward` | instr_diff@296 | 578 | 578 | **0** | **R9 修复：-57 len_diff → instr_diff（语句数 578=578 完全恢复）** |
| `get_date_and_count` | len_diff | 714 | 687 | -27 | 持平 |

## 3. 缺陷分类（按区域类型 + 算法原则）

- **Loop + Conditional 嵌套**：change_his_to_backward（R9 已修复 else 分支体丢失）、get_str_data(-48)、get_date_and_count(-27)、load_get_price(-26) — 循环体内嵌套 if/elif/else 分支语句丢失，违反原则 2（每块唯一归属）+ 原则 4（入口引用语义）
- **Conditional 嵌套**：load_bars_from_hundsun(-88) — if os.path.exists 内嵌套赋值 + if 链语句丢失，违反原则 1（自底向上归约）
- **跳转目标/元数据**：one_prod_to_dataframe、build_future_fill_time、`<module>` — 字节码级跳转目标偏移或 code 对象 filename 差异，源码结构已正确

## 4. R9 修复效果

change_his_to_backward 的 for 循环体内嵌套 `if len(data[predataindex:y_curdataindex]) == 0:` 的 **else 分支体整段丢失**（变 pass）已修复：
- 修复前：`if len(...)==0: pass`（else 体丢失，-57 指令）
- 修复后：`if len(...)==0: pass else: data.loc[...]=round(...); tmpdata=tmpdata.append(...)`（else 体恢复，578=578 指令数完全匹配，残留 instr_diff@296 为跳转目标归一化差异）

根因：`_if_generate_then_branch`（region_ast_generator.py L9038）用 `_if_generate_else_branch` 作探针检查有副作用（预标记 generated_blocks），正规调用时 else 块已标记为已生成而返回空。违反原则 2（每块唯一归属）+ 原则 4（入口引用语义）。

## 5. 详细 diff

见 `diff_detail.txt`（/tmp/r9_out/diff_detail.txt），含每个函数 orig vs new 指令逐行对比。

## 6. 最小复现实例

见 `minimal_repros/`，共 10 个 repro（全部 py_compile 通过），覆盖：
- repro_01/02: Loop+Conditional else 分支体丢失（change_his_to_backward 模式，已修复）
- repro_03: Conditional 嵌套赋值链丢失（load_bars_from_hundsun 模式）
- repro_04/05: Loop 嵌套 for/while + if/elif 链语句丢失（get_str_data/get_date_and_count 模式）
- repro_06: Conditional+BoolOp 嵌套分支丢失（load_get_price 模式）
- repro_07-10: Loop 通用模式（break/continue/STORE_SUBSCR/聚合丢失）

每个 repro 标注所属区域类型与违反的算法原则。
