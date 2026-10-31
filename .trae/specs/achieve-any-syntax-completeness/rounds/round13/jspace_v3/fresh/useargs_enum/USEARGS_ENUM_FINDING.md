# USEARGS_ENUM：REAL46-004（enum.py）LOAD 失败链三族修复 + 第 4 形态登记（rr-v5r97，Task 23）

## 家族选定

46 sweep 剩余 15 DIFFERENT 中 REAL46-004（enum.py，登记 Task 11 use_args 族，
case 级 LOAD 失败 + 60 R5/R0 维度）为最重案。逐函数字节比对 + 逐层加载驱动。

## LOAD 失败链（四层，本轮修复前三层）

| 层 | 缺陷 | 复现 | 修复 |
|---|---|---|---|
| 1 | `_find_new_` 的 use_args 条件块被 `_loop_generate_for` R102 break-落点发射越权吸进外层内联 if 的 then 臂（外层 `if __new__ is None:` 的跳转目标 == 循环 break 落点 == for-else 落点三方共享）→ `use_args` 未绑定 UnboundLocalError | `fn_find_new.py`（独立自包含） | `[v97-JOIN]` 两段：R89 内联 if 的 `_r4e` 汇合块判据命中时先登记 generated 并在 If 之后作兄弟语句发射一次；`_loop_generate_for` 加外层条件汇合守卫（落点前驱中有循环外块以 FORWARD 条件跳转指为目标 → 跳过认领；m06 回边重检块为 BACKWARD 不命中 C3） |
| 2 | except 处理器内 BoolOp 赋值 `exc = e.__cause__ or e` 被 `_generate_handler_body_statements` 指令级重建逐操作数拆成裸表达式（`e.__cause__` + `e`）→ exc 未绑定 | `te1.py`（独立自包含） | `[v97-EXCBOOL]`：`_generate_try` 处理器臂块派发白名单（L38297）补 BoolOpRegion（带 value_target 守卫——条件形由其 IfRegion 派发），依本方法④契约「嵌套区域由调用方整树生成」 |
| 3 | `exc = None`（try 体内用户赋值）被 code_generator 的 as-var 清理排除规则丢弃——`_except_as_vars` 实例级跨函数泄漏（早前函数的 `as exc` 注册毒化后续函数同名赋值） | te1 + enum 实测（te1 的 as-var 为 e 不触发；enum 泄漏触发） | `[v97-EAVSCOPE]`：`_generate_function_def`/`_generate_function_def_dict` 按函数作用域快照/还原 `_except_as_vars`（入口重置出口还原；函数内排除行为逐位不变 C3；模块级 handler 注册保留） |
| 4 | `_find_data_type_` 的 elif 臂尾 `data_types.add(candidate or base)` + `break` 迁移到内层 for 之后（else 臂只剩 break、add 丢失、尾随死 continue）→ `_get_mixins_` data_types = {StrEnum, str} → `class FlagBoundary(StrEnum)` TypeError | 区域树实证（IfRegion@314 else=[388] 树正确、臂尾含 BoolOpRegion@358 参数调用 + break 的发射分层错误） | **登记未修（下一轮家族）** |

## 验证（全实测）

- `fn_find_new` 独立复现：DIFF → **BYTE-EQUAL**；te1 独立复现：DIFF → **BYTE-EQUAL**（`exc = e.__cause__ or e` 精确恢复）
- REAL46-004 函数级差异：**11 → 9**（removed：`_find_new_`、`Enum.__new__`；added：0）
- LOAD 链：UnboundLocalError(use_args) → UnboundLocalError(exc) → TypeError(_find_data_type_)——前两层消除，第 4 层在案
- 权威 semantic_diff REAL46-004：仍 DIFFERENT（LOAD 被第 4 层阻塞，60 维不变）
- yp 变体 8/8、er_variants 4/4、mk_iterencode、20 形态矩阵（w2 known-drop 不变）、前轮探针 fi1/el1/r31/ann/tern/ell 全绿（tern `<module>` 既有登记差）
- pytest 2F/282P/2XP 冻结对一致；比较器 pyc_verify.py SHA256 冻结一致
- 全量 1556 闸门（v5r97 对 v5r89 基线）：**0 回归**；EQUAL 1132→1180（48 改善 = v5r95/v5r96 已登记的原件加载恢复集逐案一致，本轮修复 J-space verdict 零变化——改善全部为字节级 co_code 层）；唯一抖动 JS-IF-074 None→ERROR（已登记）；verdicts {'EQUAL': 1180, 'ERROR': 376, None: 0}
- REAL46 sweep（v5r97 对 v5r96）：**逐案零变化、0 回归**（15 DIFFERENT/13 EQUAL/17 ERROR + skip1；REAL46-004 维持 DIFFERENT——第 4 层阻塞 LOAD，函数级差异 11→9 在 verdict 之下）

## 诚实边界

- REAL46-004 未达 EQUAL（第 4 形态阻塞 LOAD）；46 sweep 其余 DIFFERENT/ERROR 不变。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r97.diff` | 三族完整 diff（12 hunks，含判据注释） |
| `fn_find_new.py` / `fn_find_new_out.py` | 第 1 层独立复现（修复后产品） |
| `te1.py` / `te1_out.py` | 第 2/3 层独立复现（修复后产品） |
| `REAL46-004_product_v5r97.py` | enum 产品（9 fn 差状态） |
| `case_REAL46-004.json` / `semantic_REAL46-004_v97.json` | 权威判定（DIFFERENT，LOAD 第 4 层阻塞） |
