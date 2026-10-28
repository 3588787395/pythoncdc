# Round13 新缺陷族登记：循环退出汇合块误嵌循环体（REAL46-004 `use_args`）

状态：**ROOT-CAUSED，未修复**（风险评估见末节；按 spec 纪律「一次只开一个根因族、
不贸然改 36K 行 region 代码」，本轮只登记 + 归因，不改产品码）。

## 症状

REAL46-004（反编译 `D:/Python/Lib/enum.py`）产物在 `_find_new_` 处 exec 报：

```
File ".../REAL46-004.py", line 371, in __new__
    __new__, save_new, use_args = metacls._find_new_(...)
File ".../REAL46-004.py", line 725, in _find_new_
    return (__new__, save_new, use_args)
UnboundLocalError: cannot access local variable 'use_args'
```

语义维度：`LOAD + R0`（产品模块 exec 失败、入口体未达）。这是 REAL46-004 在
rr-v5r78 修掉 f-string 语法族之后**剩余的第二个独立缺陷**，与 f-string 无关。

## Ground truth（原源结构）

`enum.py::_find_new_`（line 1023–1049）：

```python
if __new__ is None:                       # line 1023
    for method in ('__new_member__', '__new__'):   # 1026
        for possible in (member_type, first_enum): # 1027
            target = getattr(possible, method, None)
            if target not in {None, None.__new__, object.__new__, Enum.__new__}:
                __new__ = target
                break
        if __new__ is not None:           # 1037
            break                          # 1038  (break 外层 for)
    else:                                  # 1039  for-else
        __new__ = object.__new__           # 1040
# ---- 方法级：if __new__ is None 整块之后 ----
if first_enum is None or __new__ in (Enum.__new__, object.__new__):  # 1045
    use_args = False                       # 1046
else:
    use_args = True                        # 1048
return __new__, save_new, use_args         # 1049
```

`use_args` 的 if/else 在**方法级**（line 1045，`if __new__ is None` 整块**之后**），
**恒执行**，两臂都赋值，故 `use_args` 在 return 前必已绑定。

## 产物（错误结构）

`REAL46-004.py` line 708–725 把 `use_args` if/else **嵌进了 `for method` 循环体**
（16 空格缩进），紧跟 `if __new__ is not None: break`：

```python
if __new__ is None:                 # 710
    for method in (...):            # 711
        for possible in (...):      # 712
            ...
            if target not in {...}: # 714
                __new__ = target
                break
        if __new__ is not None:     # 717
            break                   # 718
        if first_enum is None or ...:  # 719  ← 误入循环体
            use_args = False
        else:
            use_args = ...
    # （原 for-else 丢失/错位）
return (__new__, save_new, use_args)  # 725
```

后果：若循环 `break`（line 718）或整个循环被跳过（`__new__` 初值非 None），则
719–722 的 `use_args` 赋值被绕过 → return 时 `use_args` 未绑定 → UnboundLocalError。

## CFG（正确）

`cfg_findnew_probe.py` dump（`build_cfg(fnc)`）：关键块与边——

| 块 | 内容 | preds | succs |
|---|---|---|---|
| B3 | `if __new__ is None` 后的 STORE + POP_JUMP_IF_NOT_NONE | 1,2 | **4**(进循环), **15**(跳过循环) |
| B4 | `GET_ITER`（for method 设置） | 3 | 5 |
| B5 | `FOR_ITER`（外层 for 头） | 4,13 | 6,14 |
| B11 | `if __new__ is not None` 条件 | 7,9 | 12(then),13(else) |
| B12 | `break` | 11 | **15** |
| B13 | 循环体余下 → 回边 B5 | 11 | 5 |
| B14 | for-else（耗尽） | 5 | **15** |
| B15 | `use_args` if 条件（line 1045） | **3,12,14** | 16,17 |

**B15 是循环退出汇合点**：三条入边 B3（跳过循环）、B12（break）、B14（for-else）
全部是「循环已结束/被跳过」，B15 属方法级。

## Region 归属错误（根因）

`region_findnew_probe.py` dump（`RegionAnalyzer(cfg).analyze()`）：

```
LoopRegion@5 blocks=[4..15] body=[5..13] else=[14]
  LoopRegion@7 blocks=[6..10] body=[7,8,10]
  IfRegion@11 blocks=[11,12,15]        ← if __new__ is not None: break
    BoolOpRegion@15 blocks=[15,16]
block_to_region: B15 -> LoopRegion@5
```

两处错误叠加：

1. **LoopRegion@5 把 B15 收进 blocks**（`[4..15]`）。B15 有前驱 B3，B3 可经
   `B3→B4→B5` 绕过 B15 直达循环头——B15 非循环私有，不应入循环块集。
2. **IfRegion@11 取 B15 为 merge**。`_find_merge`(line 2550) 用
   `NCPD(B12, B13)`，两臂（break 出口 B15 / 回边 B5→…→B15）公共后支配者恰为
   B15。生成层把 `merge_block` 之后的块当作该 if 的延续 emit，于是 `use_args`
   if（B15–B18）被写进 IfRegion@11 → 落入 LoopRegion@5 循环体。

既有守卫 `_compute_in_loop_if_merge`(line 3121) 本就是「循环内 if 合并点」的
意图修正，但其触发条件是「NCPD 返回的出口块在 `loop_region.blocks` **之外**」
——本例 B15 被 LoopRegion@5 收进了 blocks（错误 1），守卫不触发。

## 候选窄判据（已实证，未实施）

`dom_useargs_probe.py` 实测支配关系：

- **B11（if-entry）不支配 B15**：`B11 dominates B15? False`。
- B15 前驱 {3,12,14} 中，**仅 B3 可绕过 B15 抵达循环头 B5**（True），B12/B14 皆否。

教科书性质：**真正的 if-merge 必被 if-entry 支配**（两臂皆经条件才可达 merge）。
B15 不被 B11 支配 → B15 不是 IfRegion@11 的 merge。

候选判据（结构性，无指令/偏移特例）：`_find_merge` 算出 merge 后，若该 merge
**不被 if-entry 支配**，则拒绝认领（视作无合法 in-loop merge，回退
`_compute_in_loop_if_merge` 或置 None）。

## 风险评估（为何本轮不实施）

- `_find_merge`(line 2550) 是**全反编译器所有 if/elif region 的中央 merge 选取**。
  改它影响每一个 if 的区域重建，而 region_analyzer 有大量按「当前行为」逐轮加的
  守卫族（R09、R13-A3、B104R2、BoolOp 吞并、await 聚类……），部分可能**依赖**
  「非支配 merge」的现状（异常边、break/continue、goto 式字节码）。
- 「entry 支配 merge」虽是标准性质，但异常处理边 / 复杂 break 让它并非对所有
  现有 region 恒成立；一次全局拒绝可能在别处触发区域重建漂移。
- **回归门禁本就被外部阻断**：G1（1180/1556，376 excluded）、G2b（342 不可执行）、
  G2c、G4（FAIL）均无法认证「region 改动语义无回归」。可跑的只有 pytest 286 +
  IV.2；而 **G5 6617 单元比对的是冻结的 `*OK.py` 产品（不重新生成），根本不执行
  当前树 region 代码**。即：region 改动的语义回归面在此环境**无干净全量闸门**。
- 结论：满足 spec「不贸然改 36K 行 region 代码 / 一次只开一个根因族」的登记而非
  实施条件。修复应作为**独立一轮**、先补一个能重生成产品并比对 1556 全量语义的
  闸门，再改 `_find_merge` 并验证。

## 诚实边界

- 本族**未修复**。REAL46-004 仍 DIFFERENT（`LOAD+R0+…`，由 `use_args` 运行时
  错误导致）。rr-v5r78 已修的 f-string 语法族不在本族范围。
- 不宣称 G1/G2b/G2c/G3/G4/G6 通过；`product_complete` 仍 **NOT PASS**。
- 候选判据仅为归因产物，未经全量语义回归验证，**不作为已证修复**。

## 证据探针（归档于本目录）

| 脚本 | 作用 |
|---|---|
| `cfg_findnew_probe.py` | `build_cfg` dump `_find_new_` 块/边，定位 B15 循环退出汇合 |
| `region_findnew_probe.py` | `RegionAnalyzer` dump region 归属，定位 LoopRegion@5 / IfRegion@11 误嵌 |
| `dom_useargs_probe.py` | 支配关系实证：B11 不支配 B15、B3 绕过 B15 达循环头 |
