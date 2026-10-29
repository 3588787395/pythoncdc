# while-True 循环头早返回守卫条件极性反转（rr-v5r89）

状态：**已修复**（`region_ast_generator.py` 循环头手写 if-break/return 路径
+34 行，只增不破）。真实案例形态：REAL46-003 `_c3_merge` 的
`if not sequences: return result` 早返回守卫。修复前 er3/er4 最小复现把
`if not items: return` **真反转**为 `if items: return/break`（语义错误）；
修复后与源逐字一致。

## 缺陷

`while True:` 循环头以条件跳转结尾、一臂是 return 的形态，手写重建路径
（`region_ast_generator.py` 12616-12700）直接把 return 臂当 then 分支发射
`if <test>: return`，未处理两件事：

1. **条件跳转极性**：CPython 3.11 对 `if not cond: <臂>` 做跳转翻转——
   编译为 `LOAD cond; POP_JUMP_IF_TRUE(跳过臂)`。旧路径不看跳转极性，
   把「条件为假时执行的 return 臂」发成 then 分支 → `if items: return`
   （条件取反，语义错误）。
2. **return-None 降级**：`LOAD_CONST None; RETURN_VALUE` 臂因
   `argval is not None` 守卫不回收返回值，被降级发射为 `break`
   （er3：`if not items: return None` → `if items: break`，极性与语义双错）。

```python
# 源
while True:
    if not items:
        return result
    result.append(items[0])
    items = items[1:]
# HEAD 产物（极性反转）
while True:
    if items:
        return result        # ← 条件反了：items 非空时 return
    result.append(items[0])
    items = items[1:]
```

## 根因（探针实证）

`er4_probe.py`：LoopRegion blocks=[(8,10) 头, (12,14) return 臂, (16,90) 体]。
头块尾指令 `POP_FORWARD_IF_TRUE (to 16)`——跳过 return 臂，即 return 在
**条件为假**时执行。手写路径 `_return_val` 回收成功后直接
`If(test=test_expr, body=[Return])`，test 未经极性调整。

触发边界（`er_variants.py` 四形态隔离）：
- er3/er4（循环头平铺语句体 + 早返回守卫）：极性真反转 → 本族缺陷；
- er1（守卫后体以 for 循环开头）：走 IfRegion 结构反转路径，产出
  `if cond: <体> else: return`——语义等价，独立登记非本族；
- er2（非循环的普通 if 早返回）：走通用 IfRegion 路径，仅多 `else`，
  语义等价，不受影响。

## 修复（只增不破，+34 行）

1. **极性判定**（结构事实，无名字/偏移特例）：条件跳转指令 `argval`
   即跳转目标块偏移——return/break 臂块偏移 == 跳转目标 ⟶ 臂在 test
   为真时执行（不反转），否则臂在 test 为假时执行（test 前加 Not）。
   仅对 `POP_JUMP_FORWARD/BACKWARD_IF_TRUE/IF_FALSE` 判定，其余跳转
   形态维持旧行为（C3）。Not 用小写 `'op': 'not'`（`ast_converter`
   op_map 只认小写；`code_generator` 同样接受）。
2. **return-None 保留**：`LOAD_CONST None` 臂且块含 RETURN_VALUE 且非
   模块级时回收 `Constant(None)` 返回值——break 在字节码中是
   JUMP_FORWARD 不含 RETURN_VALUE，故该臂只可能是真实 `return None`。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| er3 repro（`if not items: return None`） | `if items: break`（极性+语义双错） | **`if not items: return None`**，与源逐字一致 |
| er4 repro（`if not items: return result`） | `if items: return result`（极性反） | **`if not items: return result`**，与源逐字一致 |
| er1（IfRegion 结构反转） | `if sequences: ... else: return` | 不变（语义等价，非本族） |
| er2（普通 if 早返回） | `if not sequences: ... else:` | 不变（语义等价） |
| SWAP 中段族回归（rr-v5r88） | — | x1/el1/y1 中段语句全在 |
| el_variants 6 / el_narrow 8 | — | 6/6 MISSING none、8/8 无 LOST |
| varargs 注解回归（rr-v5r87） | — | ann_repro 三函数注解全在、va_variants 8/8 |
| 三元/if-早返回/Ellipsis 回归 | — | 全绿 |
| REAL46-003 / REAL46-031 R7 | 4 / 2 | 4 / 2（不变——er1 形态走 IfRegion 反转路径，语义等价独立子族） |
| pytest 7 文件 | 2 failed / 282 passed / 2 xpassed（既有） | **零新增失败** |
| 全量 1556 闸门 | 基线 v5r88 shard json | 见下节 |

## 全量 1556 闸门（对 v5r88 基线）

实测读数（`semantic_shard{0,1,2}_v5r89.json` vs `..._v5r88.json`）：

- 基线 verdicts：`{'EQUAL': 1132, 'ERROR': 423, None: 1}`；本轮：`{'EQUAL': 1132, 'ERROR': 423, None: 1}`（逐字相同）
- **REGRESSION（EQUAL→非EQUAL）：0**；IMPROVEMENT：0
- 唯二变化 `JS-IF-066 None→ERROR`、`JS-IF-074 ERROR→None`：均为产物加载/执行失败类记录在两个互斥状态间的抖动（同 v5r86/v5r88 轮已登记情形），EQUAL 计数不变，非回归。

## 诚实边界

- er1 形态（守卫后循环体以 for/嵌套结构开头）走 IfRegion 结构反转路径，
  产出 `if cond: <body> else: return`——语义等价但 AST 形态与源不同，
  REAL46-003 v[51] `_c3_merge` R7 差属此独立子族，**登记未修**。
- 不宣称 G2c 通过（REAL46-004 use_args 60 差观察层在案）；
  `product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `er3_guardsimple.py` + `er3_guardsimple_decompiled.py` | 极性反转+return-None 降级复现（修复后产物） |
| `er4_guardappend.py` + `er4_guardappend_decompiled.py` | 极性反转复现（修复后产物） |
| `er1_c3merge.py` / `er2_plainguard.py` + decompiled | 等价形态边界（不受影响） |
| `er_variants.py` | 四形态变体矩阵 |
| `er4_probe.py` | LoopRegion 块结构探针 |
| `apply_erfix.py` / `fix_not_op.py` | 精确替换应用脚本（CRLF 安全） |
| `fix_patch.diff` | 完整修复 diff（含判据注释） |
