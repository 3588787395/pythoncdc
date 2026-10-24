# R7 tolerance 台账（书面登记）

依据 `spec.md`「R7 code object 阻断」：任何 `co_code` / `co_consts` / `co_exceptiontable` 的 code object 差异默认判 `DIFFERENT`；只有经过书面 tolerance 且不改变行为语义的字段可以忽略。本文件即该书面登记；未在本文件登记的忽略按未登记处理，验收判失败。

## 1. 已登记 tolerance

| 字段 / 路径 | 类别 | 登记理由（为何不改变行为语义） | 生效方式 |
|---|---|---|---|
| `metadata.code.co_filename` | 默认忽略 | 编译环境文件路径，随编译位置变化，与语义无关 | `semantic_diff.DEFAULT_METADATA_IGNORE`，逐 case 恒定生效 |
| `metadata.code.co_firstlineno` | 默认忽略 | 源码首行号偏移，包装/嵌套写法可移动，与语义无关 | 同上 |
| `metadata.code.co_linetable` | 默认忽略 | 行号-字节码映射表，仅调试信息，与语义无关 | 同上 |
| `float_abs_tol` / `float_rel_tol` | 数值容差 | 浮点求值顺序差；默认 0（严格相等） | case `tolerance` 字段，按 case 显式给出 |
| NaN == NaN | 内建容差 | IEEE 754 NaN 比较语义，双方均为 NaN 视为相等 | `semantic_diff.compare_canon` 内建 |

## 2. 受保护字段（不可忽略）

`co_code`、`co_consts`、`co_exceptiontable`，含其子路径与祖先路径（如 `$.metadata.code`、`$.metadata`、`$`）。

`semantic_diff.judge_case` 对任何试图通过 `tolerance.ignore_metadata_fields` 忽略上述路径的 case 直接判 `ERROR`（错误信息 `unregistered R7 tolerance (protected code-object fields): ...`），不产出 verdict、不计覆盖。该硬校验是「无未登记忽略」的执行机制，不得移除或放宽。

## 3. 其它 metadata 字段的自定义忽略

`tolerance.ignore_metadata_fields` 允许登记受保护字段以外的路径（如 `metadata.doc`），但必须同时满足：

1. 先在本文件登记，并写明「不改变行为语义」的依据；
2. 实际生效路径会完整写入该 case 结果的 `tolerances` 字段，供审计逐 case 比对；
3. 审计中发现未登记的忽略路径时，该 case 验收判失败。

## 4. 变更流程

新增或修改 tolerance：先修改本文件（登记理由 + 影响面），评审通过后才能在 case 中使用；`semantic_diff` 中受保护字段的硬校验不得随任何 case 需求移动。
