# try/except/else else 子句以循环回边收尾时整体丢失（rr-v5r90）

状态：**已修复**（`region_analyzer.py` `_find_try_else_blocks` W28 守卫豁免 +
新族级谓词 `_try_else_backedge_close`，+69/−1 行，只增不破）。真实案例形态：
G2c REAL46-003（stdlib `functools.py`）`update_wrapper`（module co_consts
v[10]）——`for` 循环体内 `try/except/else` 且 else 体是循环体最后一条语句。
修复后 v[10] 字节级 EQUAL，REAL46-003 R7 差 **4→3**（剩 v[51]/v[53]/v[55]
独立子族，见诚实边界）。

## 缺陷

`try/except/else` 的 else 体是循环体内最后一条语句时，CPython 3.11 把
else 体直接放在 try 体之后、首个 handler 之前（地址序），else 体末尾的
`JUMP_BACKWARD` 就是循环回边。区域分析 `_find_try_else_blocks` 的
`[try_end, handler_entry)` 区间收集环节里，[W28 fix] 守卫把**一切以
JUMP_BACKWARD 结尾的块**排除出 else 候选（该守卫的本意是 try 体自身
`continue` 的回边块），导致真 else 体被逐出 else 子句——else 语句被当成
try/except 之后的兄弟语句**无条件发射**。

```python
# 源（functools.update_wrapper 节选）
for attr in assigned:
    try:
        value = getattr(wrapped, attr)
    except AttributeError:
        pass
    else:
        setattr(wrapper, attr, value)
# HEAD 产物（else 子句蒸发，setattr 变成 try/except 之后的无条件语句）
for attr in assigned:
    try:
        value = getattr(wrapped, attr)
    except AttributeError:
        pass
    setattr(wrapper, attr, value)     # ← 异常路径也会执行：AttributeError
                                      #    时 value 未绑定 → UnboundLocalError
                                      #    （或用上一轮残留值 setattr 错属性）
```

这不是纯布局差：**异常路径语义改变**（R1 可捕；REAL46-003 因 input_model
module-only 仅跑 R7，故表现为 R7 差）。最小复现
`s3_tryelse_loop.py`（= te_shapes.py `s3`）：`getattr` 失败时原件静默跳过、
修复前产物抛 UnboundLocalError。

## 根因（探针实证）

`te_region_probe.py`：s3 形态区域树
`TryExceptRegion@B9 blocks=[4,5,6,7,9,11] try=[9] handlers=[(AttributeError,
None,[5,11])] else=[]`——else 体块 B10[48..124]（`setattr; out.append;
JUMP_BACKWARD`）**完全不在区域块集内**，被循环体序列发射器当兄弟语句消费。

`_find_try_else_blocks` 走向：`merge_point=None`（try 正常出口与 handler
正常出口经回边汇合于循环头，无函数内公共后支配）→ alternative_merges
非空但 `try_end_is_back_edge=True` 拦下 → Pattern TE 降级（同守卫拦下）→
`[try_end, first_handler_entry)` 区间收集 → B10 唯一候选 → **[W28] 以
JUMP_BACKWARD 结尾 → `continue` 排除** → 返回空 else。

### 四形态区分（te_shapes.py + shapes_region_probe.py）

| 形态 | 字节码布局 | 区域现状 | 修复后 |
|---|---|---|---|
| s1 `try:` 含 `if c: continue`，try 后有语句 | try 保护段、continue 回边块、`JUMP_FORWARD` 越 handler | try=[4,5,12] 正确含回边块 | 不变 ✓ |
| **s3 else 体为循环体最后语句** | try 体 fall-through→else 体（真实语句+回边）；handler 在 else 后 | else=[]（B10 孤儿）| **else=[B10] ✓** |
| s4 else 体后还有语句 | else 体 `JUMP_FORWARD` 越过 handler 到 post-else | else=[11] 正确 | 不变 ✓ |
| s5 无 else | try 体 `JUMP_FORWARD` 越过 handler | else=[11]（裸跳块，发射为空）| 不变 ✓ |

W28 本族形态复核（w28_shapes.py）：

| 形态 | 判定走向 | 修复后 |
|---|---|---|
| w1 `try: ...; if c: continue except: pass` + try 后语句 | 回边块在 [try_end,handler) 但 handler 正常出口是前向跳转 → 判据② 不汇合 → 维持排除 | `co_code`/异常表逐字节不变 ✓ |
| w2 `try: ...; continue except: pass` + try 后语句 | 同上；产物丢不可达 continue（**修复前既有行为**，stash 实证） | 逐字节同修复前 ✓ |
| w3/w4 `try: ... continue except: continue` vs `... except: continue else: continue` | 裸回边块（除回边外无真实语句）→ 判据④ 维持排除 | 两者字节码恒等，取无 else 简形，与修复前一致 ✓ |

## 修复（只增不破，+69/−1）

新族级谓词 `RegionAnalyzer._try_else_backedge_close(try_region, block,
handler_normal_exit_blocks, first_handler_entry)`（全部块图/指令序结构
事实，无名字/偏移/输入值特例），接入点为 `[try_end, handler_entry)` 收集
环节的 W28 守卫——仅当谓词全满足时豁免该排除，其余形态逐位不变（C3）：

1. **② 汇合证据**：候选块回边目标 ∈ handler 正常出口集（except 臂跳过
   else 臂后与 else 臂在同一回边目标汇合——else 子句的字节码证据）；或
   全部 handler 无正常完成路径（reraise/return 终止，v5 形态）——此时
   无 else 形态的 try_end 块以 `JUMP_FORWARD` 结尾不会进入本判定，JB
   结尾块只能是 else 体或 try 体尾部 continue，两形态字节码恒等
   （[R51] 简形口径逆命题），认领 else 保字节等价；
2. **③ 非成员**：候选块 ∉ try_blocks（else 体不在 try 体保护流内）；
3. **④ 非裸回边**：候选块除收尾回边外还有真实语句（裸 continue 回边块
   维持排除，w3/w4 口径）；
4. **⑤ 无旁路**：候选块与首 handler 入口之间无越过 handler 的
   `JUMP_FORWARD`（try 体 continue 形态存在该旁路，w1/w2 被此拦下）。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| s3 repro（else 体为循环体最后语句） | else 丢失、异常路径语义错误 | **else 恢复，co_code+异常表逐字节相等** |
| s1/s4/s5 形态 | 正确 | 不变，逐字节相等 |
| te_variants 8 变体（v1 for 宿主/v2 while-True 宿主/v3 else 含 if 多块/v4 嵌套外层 try/v5 reraise handler/v6 else 非末尾/v7 W28 continue/v8 else 内 continue） | v1-v4/v6-v7/v8 丢 else 或裸回边块 | **8/8 BYTE-EQUAL** |
| w1-w4 W28 形态 | — | w1/w3/w4 逐字节相等；w2 与修复前逐字一致（不可达 continue 既有丢弃，stash 对照实证非本修复引入） |
| REAL46-003 v[10] update_wrapper | co_code 差 | **co_code+异常表逐字节相等** |
| REAL46-003 semantic_diff（权威判据） | R7×4 | **R7×3**（v[51] `_c3_merge` IfRegion 反转、v[53] `_c3_mro` for-else 后语句吸入循环体、v[55] `_find_impl` 循环退出 merge 错构——独立子族登记）；R1–R6 干净 |
| 前轮探针 | — | el_variants MISSING none（v5r88）、va_variants 8 rc=0（v5r87）、tern_variants 5/5 preserved（v5r84）、er_variants er1-er4 读数不变（v5r89）、r31_repro A1/A2 正常（v5r86） |
| pytest 7 套件 | 2 failed / 282 passed / 2 xpassed（冻结对） | **2 failed / 282 passed / 2 xpassed，零新增失败** |
| 全量 1556 闸门 | 基线 `semantic_shard{0,1,2}_v5r89.json` | 见下节 |

## 全量 1556 闸门（对 v5r89 基线，三分片 offset 0/519/1038）

实测读数（`semantic_shard{0,1,2}_v5r90.json` vs `..._v5r89.json`，
`compare_v5r90.py`）：

- 基线 verdicts：`{'EQUAL': 1132, 'ERROR': 423, None: 1}`；本轮：**逐字相同**
- **total verdict changes: 0；REGRESSION（EQUAL→非EQUAL）：0；IMPROVEMENT：0；other：0**
- EQUAL 1132=1132（1556 条逐条不变）。repair 36 / async 62 / module 32 见证族
  为 1556 子集，同判据同输入，读数随之不变。
- G5 电池（402 八分片/small34/quotation）为「pyc vs 冻结在位 `*OK.py` 产物」
  比对（`pyc_verify.py` 只比较不再生成），对产品码变更天然不变——本轮
  `scripts/pyc_verify.py`/`tests/`/冻结产物零改动，比较器 SHA256
  `FE1902A9…38DDFF4` 与冻结基线一致（实测复核）。

## 结论

1. **try/except/else else 子句回边收尾族修复在全 1556 J 空间下零语义回归**；
   REAL46-003 R7 4→3（v[10] update_wrapper 消除，R1–R6 干净）。
2. 剩余 R7×3 为独立登记子族：v[51] `_c3_merge`（IfRegion 反转，语义等价）、
   v[53] `_c3_mro`（for-else 后首语句吸入循环体，潜在真实语义缺陷，建议下一
   轮）、v[55] `_find_impl`（循环退出 merge 错构，与 Task 11 REAL46-004
   use_args 同根因族）。
3. `product_complete` 仍 **NOT PASS**；未宣称 G2c 通过。

## 诚实边界

- REAL46-003 仍 DIFFERENT（R7×3 在案），三个独立子族**登记未修**：
  v[51] `_c3_merge`（er1 形态 IfRegion 结构反转，语义等价）、v[53]
  `_c3_mro`（for-else 之后的首语句被吸进循环体：每迭代重复执行且 break
  路径跳过——潜在真实语义缺陷，另开一轮）、v[55] `_find_impl`
  （循环退出 merge 错构与 Task 11 REAL46-004 use_args 同根因族）。
- v5-类（reraise handler + else 收尾）在放宽②后字节等价，但 handler 有
  正常完成路径且回边目标不汇合的中间形态（如 handler 经 JUMP_FORWARD
  到非回边目标）不认领 else——按最简形发射，若真实存在再登记。
- w2 类不可达 continue 丢弃为修复前既有行为（与 JS-IF-076 不可达 break
  同类：编译时不可达代码的保留与否属独立观察项），不属本族。
- 不宣称 G2c 通过（REAL46-004 use_args 60 差在案）；`product_complete`
  仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `s3_tryelse_loop.py` | 最小复现（try/except/else else 体为循环体最后语句） |
| `te_shapes.py` + `s{1,3,4,5}.pyc` | 四形态区分集（s1 W28 形/s3 本族/s4 else 非末尾/s5 无 else） |
| `w28_shapes.py` | W28 本族形态集（w1-w4） |
| `te_variants8.py` | 8 变体矩阵（宿主/嵌套/handler 终止形态） |
| `te_region_probe.py` / `shapes_region_probe.py` | 区域树/块图探针（B10 孤儿实证） |
| `case_r003.json` / `semantic_r003_result.json` | REAL46-003 权威 semantic_diff（R7 4→3） |
| `REAL46-003_product_v5r90.py` | 修复后产品（update_wrapper else 恢复） |
| `fix_patch.diff` | 修复补丁（+69/−1） |
| `compare_v5r90.py` | 全量 1556 闸门比对脚本 |
