# R7 口径发现（2026-11-16，rr-v5r185 期间实测）

## 发现

`TarFile.next`（rr-v5r185 闭合）在**冻结比较器** `scripts/pyc_verify.py`（`compare_pyc`）口径下
为 `EQUAL`，但在 `spec.md` 的 **R7** 口径下**仍为 DIFFERENT**：

| 检查项 | 结果 |
|---|---|
| 指令流（`dis.get_instructions`） | 288 / 288 条，`opname` 差异 **0**、`argval` 差异 **0** |
| `co_exceptiontable` | raw **96B / 96B 逐字节相同** |
| `co_code` 原始字节 | **7 字节不同**，全部落在 `LOAD_CONST` 的操作数索引（457/459/625/627/867/1173/1311） |
| 根因 | **`co_consts` 顺序不同**：原件 `True` 在 index 6，产物在 index 10；11 个常量值的集合完全相同 |
| 按 `TOLERANCE_REGISTRY.md` | `co_consts` 属**受保护字段**，未登记 tolerance ⇒ **默认 DIFFERENT** |

## 结论（影响所有语料读数）

1. **冻结比较器口径**（`compare_pyc`）：对常量索引顺序、跳转偏移、NOP 布局做归一化，因此
   「常量集合相同、指令流语义相同」即判 `EQUAL`。语料判官读数（request 194/194、tarfile
   158/160、cookiejar 103/105、subprocess 75/78、difflib 62/62）都是这个口径。
2. **R7 严格口径**（`TOLERANCE_REGISTRY.md` + `semantic_diff`）：`co_code`/`co_consts`/
   `co_exceptiontable` 任一不同即 `DIFFERENT`，不得计入覆盖分子。按此口径，本轮 `next`
   **不计入**。
3. 因为反编译产物是**重新编译**得到的，`co_consts` 顺序由发射顺序决定，与原件（由原源码编译
   决定）不保证一致 ⇒ **「判官 EQUAL」不能推出「R7 clean」**，这是系统性的，不是个例。
4. 因此：**语料判官百分比不能作为 J 空间 `covered_5tuple` 或 `complete` 的证据**；两者必须分开
   报告。`covered_5tuple` 只由 `semantic_diff`（R7 阻断）+ `input_model.calls` 决定。

## 处置

- **不修改** `TOLERANCE_REGISTRY.md`：`co_consts` 是受保护字段，放宽它等于自证完备。
- 后续凡报「某单元闭合」，必须同时标注口径：`judge-EQUAL` / `R7-clean` 二者不可混用；
  `R7-clean` 需 `co_code`/`co_consts`/`co_exceptiontable` 三者逐字节相同。
- 若要提升 `R7-clean` 比例，需要的不是语料轮，而是**让发射顺序与原件常量表顺序一致**的
  生成侧改造（属独立工程，未评估工期）。
