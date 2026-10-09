# DIAG T12-12 — matcher.DefaultMatcher.match：两处 if 测试**没有被识别为区域**（Round 12）

范围：诊断，不改 `core/`，不跑 402 门。镜像 `D:/Temp/r142/`。
仓库字节（实测）：generator `971df5e2c9cd7d0a`（= HEAD，T12-09 已逐字节撤回），
analyzer `e926a54f17753b33`（封存，含 B133）。
消费的前置结论：`rounds/round11/DIAG_B138_MATCHER_LAST_MILE.md`（三处折叠 + 17/17 oracle 文本）。

## 1. 复现（当前字节，本轮自己的读数）

- `python -X utf8 pycdc.py site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc -o D:/Temp/r142/m_now.py`
  ⇒ rc=0，产物 13255 字节
- `python -X utf8 scripts/pyc_verify.py single …matcher.pyc --source D:/Temp/r142/m_now.py`
  ⇒ `status=failure units=16/17 (94.12%)` —— 与 B138 同读数（B138 时 generator 为 `e9a8f65f6451bcc8`，
  其间只落过注释改动 ⇒ B138 的 oracle 结论仍适用）

## 2. 普查仪器与一次假零（自曝）

仪器 `D:/Temp/r141/p1_census.py`（只跑分析/生成一次，不落文件到仓库；输出 `D:/Temp/r142/census_match.txt`）。
它的 UNIT 过滤原本是 **substring**，于是 `match` 先命中 `set_matching_type@66`、再命中
`is_current_match@169` —— 两次读数都是**另一个 code object** 的（本役第 N 次踩同名/首匹配）。
已给仪器加 `!name` 精确 co_name 模式，正对照 = `dumped=True` 且表头
`===== UNIT match@176 co_lines count=819 blocks=78 regions=45 =====`。
（`co_qualname` 在这些重建 code object 上不存在，label 实为 `co_name@co_firstlineno`。）

## 3. 普查事实（全部是**区域字段/角色**，不是偏移推断）

被吞的那条语句头 = 块 @2164（10 指令）：

```
@2164 LOAD_FAST order|LOAD_ATTR asset|LOAD_ATTR symbol|LOAD_CONST None|LOAD_CONST 3|
      BUILD_SLICE 2|BINARY_SUBSCR|LOAD_CONST ('688','689')|CONTAINS_OP 0|
      POP_JUMP_FORWARD_IF_FALSE 2464          lines=[241…]  succs=[2208, 2464]
  preds: 1834(IF_FALSE) 1884(IF_FALSE) 1896(IF_FALSE) 1908(IF_TRUE) 2038(IF_FALSE) 2080(IF_FALSE)
  roles: LoopRegion@6:body_blocks
         IfRegion@2038:else_blocks  IfRegion@816:else_blocks  IfRegion@800:then_blocks
         IfRegion@732:else_blocks   IfRegion@664:else_blocks  IfRegion@546:then_blocks …
```

关键：**普查里没有任何区域的 `entry=2164`**，而 @2164 自己是一条完正的 if 测试
（CONTAINS_OP + 条件跳转，两条出边 2208/2464）。它被 **四个区域当 merge_block** 认领：

```
IfRegion entry=1834 cond=1896 merge=2164 parent=6
IfRegion entry=1884 cond=1896 merge=2164 parent=6
IfRegion entry=1908 cond=1908 merge=2164 parent=6
IfRegion entry=1912 cond=1954 merge=2164 parent=6
BoolOpRegion entry=2038 merge=2164 parent=2038
```

⇒ **机制定名**：@2164 既是前一串条件的汇合落点、又是下一条语句的测试入口；识别端只承认前者，
于是这条语句**没有 owning 区域**，发射端也就无从发它 —— 这正是 B138 §Task1 看到的
「体（IfRegion@2208 确实存在，cond=2208 merge=3210）被发出来了，但它的**头测试**不在」。

## 4. 这**不是**结构上不可能——同一单元里就有反例

@1444 同样是「既是别人的 merge、又是自己的区域入口」，识别端两个都给了：

```
IfRegion entry=1324 cond=1372 merge=1444 parent=6      （BoolOpRegion entry=1324 merge=1486 也在）
IfRegion entry=1444 cond=1486 merge=1696 parent=6      ← merge 块同时是区域入口，正常发射
```

@1324 甚至有两个同入口区域（BoolOp + If）。所以「merge 块不得再是入口」并非本仓的既有约束，
@2164 缺入口是**识别判定漏掉了它**，不是设计不允许它。

## 5. 与 B138 三处折叠的关系（把症状归位）

| B138 的折叠 | 本轮普查给出的位置 |
|---|---|
| F3 被吞语句头 @2164 | **就是 §3：无 owning 区域**（新事实，B138 只看到 del 10 条） |
| F2 守卫折叠 `… and not is_first_five` → `is_first_five or …`（@1910、@2210） | 条件链被拆成 1834/1884/1908/1912 四个**共用 cond=1896/1954 的小区域**（§3 第二张表）⇒ 折叠发生在链的分段归属，不是单一布尔表达式渲染 |
| F1 or 链折叠 `(A∧B)∨(A∧C)` → `if not (A∧B): if (A∧C):`（@1382） | @1324 有 BoolRegion+IfRegion 双抽象，@1384/@1432/@1612 各成区域；链的分段同样在识别端成形 |

⇒ 三处折叠**同属一个宿主**：`_identify_conditional_regions` 对「一条语句内多个条件跳转块」的
分段与入口判定。@1836 也没有入口区域（同族），@2164 是其中唯一造成整条语句丢失的那块。

## 6. 下一票的判据草案（**尚未实测**，落地前必须先证）

候选规则（分析端一处判定）：一个块 **同时** 满足
① 块尾是条件跳转（`POP_JUMP_IF_TRUE/FALSE`）且两条出边都在同一作用域；
② 它被 ≥1 个区域认作 `merge_block`；
③ 它的 fall-through 出边不是它自己的 merge（即不是 `while` 头测形）；
⇒ 仍应建 IfRegion(entry=该块)，其 merge 取两条出边的**共同后继**（@2164：2208 与 2464 的汇合）。

必测反例/控制（缺一不得谈翻正）：
- 正例：matcher 16/17 → 17/17（B138 已给 17/17 的字节正确文本，可逐字对照）
- 控制：@1444 形（merge 同时是入口）**已经**正确 ⇒ 规则不得把它改成两遍
- 连带：quotation 153/153、handlers 29/30、wizard_quant_api 55/58 产物逐字节不动
- 轴纪律：本轴此前未被打过（B139c 攻的是 BoolOp 链**起点**判据，B123 攻的是 merge_block **选取**，
  两者都不是「merge 块作为语句入口的区域身份缺失」）；若本票零翻正，按规则登记并换轴，
  不得在同一判据上磨第三次。
