# Round 8 测试工程师：反编译报告

## 1. 总体统计

- 总函数数: 150
- 一致函数数: 142
- 不一致函数数: 8
- 成功率: 94.67%
- compile_ok: True
- 相对 R7: 142→142 无退化（基线保持）

## 2. 不一致函数清单（8 个）

| 函数 | 状态 | orig_len | new_len | diff |
|------|------|----------|---------|------|
| <module> | instr_diff@394 | - | - | - |
| one_prod_to_dataframe | instr_diff@131 | - | - | - |
| build_future_fill_time | instr_diff@226 | - | - | - |
| load_bars_from_hundsun | len_diff | 501 | 459 | -42 |
| load_get_price | len_diff | 226 | 224 | -2 |
| get_str_data | len_diff | 317 | 269 | -48 |
| change_his_to_backward | instr_diff@296 | - | - | - |
| get_date_and_count | len_diff | 714 | 687 | -27 |

## 3. 缺陷分类（按区域类型 + 算法原则）

- **Loop 区域**：change_his_to_backward(-57)、get_str_data(-48)、load_bars_from_hundsun(-88) — 循环体内/循环后语句丢失，疑似违反原则 2（每块唯一归属）
- **Conditional/BoolOp 区域**：load_get_price(-26)、get_date_and_count(-27)、one_prod_to_dataframe(+10) — if/elif/BoolOp 链结构或条件表达式丢失/冗余
- **Sequence/Module 区域**：<module>(instr_diff)、build_future_fill_time(instr_diff) — 模块级 NOP/跳转目标偏移或语句顺序差异

## 4. 详细 diff

见 `diff_detail.txt`（/tmp/r10_out/diff_detail.txt），含每个函数 orig vs new 指令逐行对比。

## 5. 最小复现实例

见 `minimal_repros/`，共 ≥10 个 repro，每个标注所属区域类型与违反的算法原则。
