# SWAP 多目标赋值路径中段兄弟语句丢失（rr-v5r88）

状态：**已修复**（`region_ast_generator.py` SWAP 多目标 unpack 路径 +39 行，
只增不破）。真实案例：G2c REAL46-003（`functools.py`）`lru_cache` elif 分支
丢 `wrapper = _lru_cache_wrapper(...)` 与 `wrapper.cache_parameters = lambda: ...`
两条中段语句；修复后 R7 差 6→4（剩余为独立子族，见诚实边界）。

## 缺陷

`a, b = x, y` 形态（CPython 对 cellvar 目标插入 `SWAP 2`）触发的多目标
unpack 路径把「末 STORE 之后、RETURN 之前的剩余指令」整体当作**单一 return
值表达式**喂给 `expr_reconstructor.reconstruct`——`reconstruct` 只取栈顶值，
中间完整兄弟语句的 STORE 被静默丢弃；无 RETURN 时整段剩余指令直接丢弃。

```python
# 源（functools.lru_cache elif 分支节选）
elif callable(maxsize) and isinstance(typed, bool):
    user_function, maxsize = maxsize, 128      # SWAP 2 + STORE_FAST + STORE_DEREF
    wrapper = _lru_cache_wrapper(user_function, maxsize, typed, _CacheInfo)   # ← 丢
    wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}  # ← 丢
    return update_wrapper(wrapper, user_function)
# HEAD 产物（中段两条蒸发，wrapper 退化为未定义裸名）
elif callable(maxsize) and isinstance(typed, bool):
    user_function, maxsize = (maxsize, 128)
    return update_wrapper(wrapper, user_function)
```

最小复现 `x1_tuple_lambda_return.py`（元组赋值目标含被 lambda 捕获的
cellvar）：`info = lambda : maxsize` 整条丢失。`y1_swap_noreturn.py`
（无 return 尾形态）：`info = lambda : maxsize` 与 `typed = 5` 两条全丢。

## 根因（探针实证）

`region_ast_generator.py` SWAP unpack 路径（原 67280-67297）：

1. `_swap_remaining = _chain_instrs[_last_swap_store_idx:]` 取末 STORE 后全部
   剩余指令；
2. `_has_return` 为真时把**整段**（含兄弟语句）过滤噪指令后喂
   `reconstruct`——探针 x1_probe3 实证：`[LOAD_CLOSURE, BUILD_TUPLE,
   LOAD_CONST, MAKE_FUNCTION, STORE_FAST, LOAD_GLOBAL, LOAD_FAST, PRECALL,
   CALL]` 被当一个表达式重建，产出 `Call`，lambda 赋值（STORE_FAST info）
   被丢；
3. `_has_return` 为假时不做任何处理，剩余段整体丢弃（y1 实证）。

触发边界（变体矩阵隔离）：必须走 SWAP 路径——元组赋值 + 目标含 cellvar
（lambda/嵌套函数捕获）时 CPython 才插 SWAP；普通 STORE_FAST 对（el3）
走 noswap/通用路径不受影响。同方法 noswap 路径已有 [B238-V3R42] 修复
（按语句终结指令切分剩余段），SWAP 路径缺同一切分。

## 修复（只增不破，+39 行）

镜像 noswap 路径 [B238-V3R42] 判据到 SWAP 路径：

1. 从 RETURN 之前回扫到最近一条语句终结指令（复用既有
   `_B54_STMT_TERMINATOR_OPS` 白名单：STORE_*/DELETE_*/POP_TOP/RAISE_VARARGS/
   IMPORT_*/YIELD_*/RETURN_*，块内 opcode 序结构事实，无偏移/名字特例）；
2. 终结指令之前的指令段交既有通用语句构建器
   `_build_statements_from_instructions` 重建为兄弟语句，追加在元组赋值
   之后、return 之前（源序）；
3. 终结指令之后的尾段仍按 return 值表达式重建（旧行为）；无 RETURN 时
   剩余段整体按兄弟语句重建（修复 y1 丢语句）；
4. 保守守卫（与 B238 路径同）：前导段含 JUMP*/POP_JUMP*/FOR_ITER 结构
   事实时不重建、维持旧行为；不含语句终结指令的段不可能含语句边界，
   行为与旧实现逐位相同（C3）。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| x1 repro（lambda 中段） | `info = lambda` 丢 | **恢复**，与源逐字一致 |
| el1 repro（REAL46-003 形态） | 中段 2 条丢 | **2 条全恢复**，与源逐字一致 |
| y1 repro（无 return 尾） | 中段 2 条丢 | **2 条全恢复** |
| el_variants 6 变体 | el1/2/4/5 缺中段语句 | **6/6 MISSING: none** |
| el_narrow 8 变体 | w1/3/4/7/8 LOST | **8/8 OK** |
| REAL46-003 R7 差 | 6 条 | **4 条**（v[47] lru_cache 本体修复；剩 v[10]/v[51]/v[53]/v[55] 独立子族） |
| varargs 注解回归（rr-v5r87） | — | repro `__annotations__` 逐字一致、va_variants 8/8 |
| 三元回归（rr-v5r84） | — | repro 真三元、变体 5/5 preserved |
| if-早返回回归（rr-v5r86） | — | repro `f(-1)` 仍抛 ValueError |
| Ellipsis 回归（rr-v5r85） | — | `type(...)` 三处形态保持 |
| pytest 7 文件 | 2 failed / 282 passed / 2 xpassed（既有） | **2 failed / 282 passed / 2 xpassed，零新增失败** |
| 全量 1556 闸门 | 基线 `semantic_shard{0,1,2}_v5r87.json` | 见下节 |

## 全量 1556 闸门（对 v5r87 基线，三分片 offset 0/519/1038）

实测读数（`semantic_shard{0,1,2}_v5r88.json` vs `..._v5r87.json`）：

- 基线 verdicts：`{'EQUAL': 1132, 'ERROR': 424}`；本轮：`{'EQUAL': 1132, 'ERROR': 423, None: 1}`
- **REGRESSION（EQUAL→非EQUAL）：0**
- IMPROVEMENT（非EQUAL→EQUAL）：0
- 唯一变化 `JS-IF-066 ERROR→None`：基线 ERROR 原因为 `original artifact did not load/execute`（原产物加载失败，非反编译差），本轮 probe_only 未产出 C4——记录抖动，非回归（同 v5r86 轮 JS-GENEXP-020 情形）。
- 分片读数：shard0 EQUAL 343 / ERROR 175 / NO_C4 1；shard1 EQUAL 394 / ERROR 125；shard2 EQUAL 395 / ERROR 123。

## 诚实边界

- REAL46-003 仍 DIFFERENT（R7×4 在案）：v[51] `_c3_merge` 为**早返回极性
  反转**子族（`if not sequences: return result` 被重构成
  `if sequences: ... else: return result`，语义等价但字节码翻转）；v[10]/
  v[53]/v[55] 为 closure/listcomp 布局子族——均**独立登记未修**，不在本族
  范围。
- 其余 R7-only 条目（001/007/008/011/012/013/014/015/016/018/019/036）
  的差数不变（4/1/4/4/7/7/7/3/5/1/2/1），其内部形态经 r7_nested_diff 抽查
  为 closure 布局（json/encoder `_make_iterencode` cellvar 序）等独立子族。
- 不宣称 G2c 通过（REAL46-004 use_args 60 差观察层在案）；`product_complete`
  仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `x1_tuple_lambda_return.py/.pyc` + `x1_out.py` | 最小复现（lambda 中段丢失→恢复） |
| `el1_full.py/.pyc` + `el1_out.py` | REAL46-003 形态复现（2 条中段丢失→恢复） |
| `y1_swap_noreturn.py/.pyc` + `y1_out.py` | 无 return 尾形态（2 条全丢→恢复） |
| `el_variants.py` | 6 变体矩阵（and 条件/嵌套 if/中段形态/尾部 elif） |
| `el_narrow.py` | 8 变体触发边界二分（属性目标 vs lambda 值 vs 无 SWAP） |
| `x1_probe.py`/`x1_probe2.py`/`x1_probe3.py` | 三层定位探针（块语句产出 → 助手函数命中 → reconstruct 输入切片实证） |
| `r7_nested_diff.py` | R7 嵌套 code_sha 差异 dis 级分解器（子族定性用） |
| `apply_swfix2.py` | 精确文本替换应用脚本（CRLF 安全） |
| `fix_patch.diff` | 完整修复 diff（含判据注释） |
