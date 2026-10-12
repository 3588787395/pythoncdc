# FIX_R21-48 — clock_worker：@7248 无主测试块声明（合成 IfRegion + 伪 else 判据）

工单：**R21-48**
目标单元：`<module>.RealtimeEventSource.clock_worker`
（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`，13 单元，当前 12/13）
镜像：`D:/Temp/r77`（仓库全程只读）
基：`core/cfg/region_ast_generator.py = 30a4d7827122e165`（= r75 [R21-46] A+B on r74d），
`core/cfg/region_analyzer.py = f7d849e974904492`（需要改动：合成 IfRegion 声明与伪 else 判据均在分析端）。

## 0. 前提复测（规则 6：简报逐条重测，全部在 `D:/Temp/r77` 干净镜像里跑）

镜像认证：
```
core/cfg/region_ast_generator.py  sha256[:16] = 30a4d7827122e165  （= 简报基，MATCH）
core/cfg/region_analyzer.py       sha256[:16] = f7d849e974904492  （MATCH）
```

| 字节 | 来源 | orig/prod | delta | 窗口数（allwin）| landings | 判定 |
|---|---|---|---|---|---|---|
| `30a4d7827122e165` | 简报 base | 1424/1426 | **+2** | **2** | **7** | `status=failure units=12/13` |

简报数字全部复现。两处修正：

**修正 1（简报错误）**：简报说"`_identify_conditional_regions` walks blocks in **ascending** offset order so a parent region is built before its children"。实测代码（region_analyzer.py:18826）：
```python
blocks_in_reverse = sorted(
    self.cfg.get_blocks_in_order(),
    key=lambda b: b.start_offset, reverse=True
)
```
走的是 **降序（reverse=True）**，即子区域（较大偏移 @7270）先于父区域（较小偏移 @7248）被处理——这是正确的自底向上归约顺序。"ordering wall"不存在。

**修正 2（缺陷根因重新定位）**：`IfRegion@7248` **已被 walk 建出**，不是从未建出。探针证明：
```
BUILD_BASIC_IF for @7248: then=[7270,7372,7488] else=[] merge=7492  → result=IF_THEN entry=7248
```
之后被 elif_chain 过滤器（region_analyzer.py:1672-1691）移除，因为 @7248 ∈ `IF_ELIF_CHAIN@7186.elif_conditions`。
这是 @7248 无主的真正原因：不是 walk 漏建，是 walk 之后被删。

**@7248 的 walk 区域数据（实测探针）**：
- walk 时 @7248 建出 `IfRegion(entry=@7248, then=[@7270,@7372,@7488], else=[], merge=@7492, type=IF_THEN)`
- 该 IfRegion 被 elif_chain 过滤器（@7248 ∈ `IF_ELIF_CHAIN@7186.elif_conditions`）移除
- 最终 `block_to_region[@7248]` 归属 `TryExceptRegion`（priority 70 > IF_THEN 25），无 IfRegion
- `IF_ELIF_CHAIN@7186.elif_bodies=[[@7372,@7488]]`，不含 @7270（@7248 的真实 true successor）
  → 链错误地跳过了 @7270，@7248 不是链的 elif，而是 @7216 臂内嵌套 if-D 的测试块

**@7216 区域数据（实测）**：
`IfRegion@7216: IF_THEN, then=[@7248,@7270,@7492,@7372,@7488], else=[], merge=@7582, ibc={}`

**@7270 区域数据（实测）**：
`IfRegion@7270: IF_THEN_ELSE, then=[@7372,@7488], else=[@7492], merge=@7582`
@7492 的 IF_FALSE 来自 @7248 和 @7270 两个测试块（共享续体），这是 else 伪判的充分签名。

## 1. 真实源码形状（r76 §3 compile() 反证，本镜像直接引用，未重新证明）

`SHAPE_topology_site7164.txt` 确认目标形状 S1：
- `if A and B or C:` → then 臂内 `if D: debug(); if E: error; <@7492 顺序语句>`
- @7492 是 D/E 共享续体，不是 E 的 else

## 2. 还开着的机制与修复方案

当前基 `30a4d7827122e165` 2 窗 + 7 landing：
- 窗 #1：@7252 伪 JUMP_FORWARD ← @7164 站点 [R21-44] 被 ⑧ 拒动（@7248 无 IfRegion）
- 窗 #2：@7590 伪 JUMP_FORWARD ← 同臂 @7492 被当 E 的 else ⇒ 臂尾必须跳转

**修复方案（co-requisite pair）**：
- **半件 A**：elif_chain 过滤器不删 `IfRegion@E`（E ∈ `elif_conditions`）当且仅当：
  ① E 的 `merge_block` ∉ 对应链的 `elif_bodies`，且
  ② E 的 `merge_block` 的全部前驱恰在 `{E} ∪ {E 的 true successor}` 之内。
  这证明 E 是"嵌套 if 的臂内测试"，不是真正的 elif（真 elif 的 merge 前驱来自 body 末和 else 末，不是 E 本身）。
  应用：@7248 merge=@7492，@7492 ∉ elif_bodies[0]=[@7372,@7488]；@7492 preds={@7248,@7270}={E}∪{E.true_succ}。⇒ 保留 IfRegion@7248。

- **半件 B（伪 else 判据）**：`_build_basic_if_region(@7270, else_blocks=[@7492], ...)`：
  若 F ∈ else_blocks 且存在 CFG 前驱 P of F 满足：
  ① P.IF_FALSE → F；② P.true_succ == 本区域 condition_block C；③ F 的全部前驱 ⊆ {P} ∪ all_condition_blocks
  则 F 是 P 臂顺序续体而非 C 的 else 体（P-false 和 C-false 汇聚到 F = 顺序续体签名）。
  命中：将 else_blocks 置空，区域类型降为 IF_THEN；F 交回 P 所在套件顺序发射。

- **半件 A+B 配对（[R21-44] 平折激活）**：一旦 IfRegion@7248 存活，[R21-44] 的 ⑧ 判断
  检查 _cond_ids = {condition_block ids}，@7248 是 IfRegion@7248 的 condition_block ⇒ ⑧ 满足
  ⇒ @7164 和 @7582 站点走 [R21-44] 平折路径 ⇒ 2 伪 JUMP_FORWARD 消失 ⇒ 目标 13/13。
  同时 @7270 伪 else 修正使 @7492 不再被 E 臂吸入，臂尾 JUMP_FORWARD 消失。

## 3. 判据依据（correct-at-identification）

**半件 A**：
- 结构事实：elif_conditions 的块是链内条件序列的成员，其 merge 在 body 之后（不是 body 本身）；
  嵌套 if 的测试块其 merge 是臂外续体（不在 body 之内），且 merge 的前驱恰好是测试块自身与臂入口。
- 保守性：两个条件同时满足才放行，否则逐字节维持既有过滤器行为。
- 取材面：E 的 merge（区域自身数据），链的 elif_bodies（链数据，同层），
  F 的前驱（CFG 前驱结构），无跨区启发。

**半件 B**：
- 结构事实：CPython 编译 `if P: <arm>; F`，P 的 IF_FALSE 与 arm 内 E 的 IF_FALSE 汇聚到 F（P-false = F，E-false = F）。
  F 的前驱 = {P} ∪ {E}。E 是 P 臂内嵌套 if 的入口。若本区域把 F 当 else，则 P-false 须跳过整个 else 体到 @7582（臂尾）。
  实测 S3 证明这一形状产生 +49 vs 原始 +36 的 landing 差。F 是顺序续体而非 else 体。
- 保守性：仅当 else_blocks 恰为 [F]（单块 F），且三个条件全部满足时才动；其余区域逐字节不变。
- 取材面：本区域 condition_block、else_blocks、all_condition_blocks；F 的 CFG predecessors；
  P 的 CFG successors。无跨区启发，无绝对偏移，无计数阈值。

## 4. 人口普查（规则 3）

（见本文件 §5 实测结果，此处留占位）

## 5. 构建器与 2×2 实测

（见本文件 §5，实现后填写）

## 6. 交付物（D:/Temp/r77/DELIVER/）

（实现后填写）

## 7. 仓库状态

仓库全程只读：未写 `core/`、`scripts/`、`site-packages/`、`.trae/`。
