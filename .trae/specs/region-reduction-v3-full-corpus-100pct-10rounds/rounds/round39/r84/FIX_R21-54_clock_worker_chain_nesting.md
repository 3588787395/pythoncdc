# FIX_R21-54 — clock_worker `@7186` flat if/elif 链在**生成端**改发嵌套 `else: If(…)`

工单 **R21-54**。单元 `<module>.RealtimeEventSource.clock_worker`
（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`，当前 12/13）。
基线 = `rounds/round39/r75/CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py`（整个生成器，sha16 `30a4d7827122e165`）。

按规则 5，本文在**前提核对之后立即写就**，随做随补。

## 0. 镜像认证（本轮实测）

镜像 `D:/Temp/r84` = 仓库 `core/ scripts/ parsers/ utils/ bytecode/ pycdc.py`（仓库只读，未改动）。
安装基线为 `core/cfg/region_ast_generator.py`；`core/cfg/region_analyzer.py` 保持已落地的 `f7d849e974904492`。

| 文件 | sha16 | 字节 | 约定 |
|---|---|---|---|
| `core/cfg/region_ast_generator.py`（基线安装） | `30a4d7827122e165` | 3884461 | BOM + 全 CRLF，0 裸 LF，0 `\r\r\n` |
| `core/cfg/region_analyzer.py`（落地，保留） | `f7d849e974904492` | 2104888 | BOM + 全 CRLF，0 `\r\r\n` |

仓库落地字节 = 生成器 `11324f276cce6d5b` / 分析器 `f7d849e974904492`（从 `core/cfg/` 复测）。
交付基线是被存取的 r75a 候选（`30a4d782`），非仓库字节 —— 与简报一致。

## 1. 基线复测（复现简报，逐字）

`python -X utf8 pycdc.py --region -o out_base/realtime_event_source_base.py <abs pyc>`（21548 字节）：

```
len orig=1424 prod=1426 delta=2
hunks=2 landings=7 judge_diff=True
[single] status=failure units=12/13 success_rate=92.31%
  ***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow
```

两个未过滤窗口（`unit_diff --all`）都是单指令插入：

```
insert orig[1046..1046 @@7248] prod[1046..1047] del=0 ins=1   + @7252 JUMP_FORWARD   (line 250 `pass` 臂尾)
insert orig[1099..1099 @@7582] prod[1100..1101] del=0 ins=1   + @7590 JUMP_FORWARD   (line 259 尾)
```

两条新跳转都落在 prod `@9206` = 原字节 `@9194` 循环回测块（`while self.active:` 的 `POP_JUMP_BACKWARD_IF_TRUE 5614`）。
（简报的 `+2` 已复测为真。）

## 2. 前提核对（`work/probe_chain.py`，只读探针，不碰产物字节；本轮在镜像基线上实测）

### 2a. 区域事实（与简报 §2a/§2c 一致，逐条复核）

```
IfRegion cond=7186 kind=IF_ELIF_CHAIN
  then_blocks      [7212]                              # @7212 = JUMP_FORWARD->7216，被发成空 `pass` 臂
  elif_conditions  [7248]                              # @7248 被误收为 elif 条件
  elif_bodies      [[7372, 7488]]
  elif_final_else  42 blocks，首=7492,7582,... 末=8544
  merge_block      7216  (last=POP_JUMP_FORWARD_IF_FALSE->7582)   # merge 本身是 C 测试块，不是汇合点
  blocks count     48
臂正常出口：
  elif_body[0] 尾块 @7488 = RETURN_VALUE               # 该臂以 return 终结，不前跳
  final_else   尾块 @8544 = JUMP_FORWARD->9194          # 落到循环回测 @9194
@7248 = POP_JUMP_FORWARD_IF_FALSE->7492, succ=[7270,9218,7492]
```

**关键区别（对简报的实测修正，规则 6）**：两条臂的**正常出口并不相同**——一条 `RETURN`、一条前跳循环回测。
因此**已落地的 `[R21-43]` 判据本身在此不成立**（它要求两臂收敛于同一个纯 continue 块，本例不成立）。
但 `[R21-43]` 的**动作挂点**成立：在 `_if_generate_full_elif_chain` 的 orelse 挂载点（基线 16762/16767 区），
`@7186` 的 `_ft3_orelse` 恰为**单节点**（`is_elif=True, is_nested_if=False, orelse_len=1, body_len=2`），
`_r2143_hit=None`。所以「把这一个 elif 节点摘掉 `_is_elif`、标 `_is_nested_if`」这一动作可直接施加，
**但需要一个新判据**（键于本链的结构事实），而非复用 continue-收敛谓词。

### 2b. 结构签名（判据只用区域数据 / opcode 类 / 前驱后继，不读名字/偏移/计数）

共享块签名（r82a §12 / r83a §2a，实测复核成立）：
```
@7248 ∈ @7186.elif_conditions                                   = True
@7248 的假出口（CFG POP_JUMP_IF_FALSE 后继）                    = 7492
@7492 ∈ @7186.elif_final_else                                    = True
@7492 ∉ @7186.elif_bodies[0]                                     = True   （故 @7248 不是真 elif，是 @7186 then 体里嵌套的 if）
merge_block(@7216) 本身是条件测试块（末指令 POP_JUMP_*），非纯汇合块
```

## 3. 计划

1. 在生成端加判据 `_r2154_chain_elif_is_nested_body(region)`：单 elif 条件 + 在循环内 + 该 elif 条件的假出口
   落在本链 `elif_final_else` 且不在 `elif_bodies` + merge 是测试块 —— 全部结构事实。
2. 动作（复用 `[R21-43]` 惯用写法）：在 orelse 挂载点摘 `_is_elif`、标 `_is_nested_if`，让发射器走
   `code_generator._generate_elif_or_else` 的「嵌套 if ≠ elif」分支，把 orelse 整个列表作为 else 子句依次发射。
   **不补 `Continue`**（本例无 continue 块），不改任何跳转目标。
3. 先数派（20 面板求值+命中、corpus 计数、惯性探针、每命中字节变化）。
4. 测半/配对：delta/windows/landings + judge 并列；成员数派 regions/blocks/two_owner/zero_owner（附计数规则）。
5. 达标则交付；否则带数字存档。

## 4. 状态日志（随做随补）

* 2026-10-12 镜像认证，基线复测 `+2 / 2 windows / 7 landings`，judge 12/13，changed files 未测（面板待跑）。
* 前提复核：`@7248` 被收为 elif；假出口 `@7492` 在 `elif_final_else`、不在 `elif_bodies`；两臂出口不同（RETURN vs 前跳循环回测）⇒ `[R21-43]` 谓词不成立、动作挂点成立（`_ft3_orelse` 单节点）。

## 5. 实测结果（候选 `966945af956aa9b4`，builder `build_cand_r84a_r2154.py`）

### 5a. 判据点派（`work/census_r2154.py`，纯区域数据谓词，无副作用）

- 20 面板文件：`chains_eval=554 FIRES=1`，唯一命中即目标 `realtime_event_source @7248`（fx@7492、te@7270、merge@7216、fin_n=42）。
- 加「真边不落入臂体」合取之前：面板 FIRES=**66**（quotation 17、quote 9、broker 13…），宽判据不可用（会波及已落地绿单元）；加该合取后收敛到 1。
- corpus（遍历 1748 个 .pyc，含 `__pycache__` 反编译副本）：`chains_eval=6154 FIRES=14`。剔除 `__pycache__` 重复后，非面板的真实命中只有 3 处：`IQCommon/util/backtest_info_utils.pyc @3254`、`IQData/manager/plugin_manager.pyc @360`、`IQEngine/core/plugin_manager.pyc @360`。探针可证惯性（返回 False 即不改 `_ft3_orelse`）。

### 5b. 候选产物读数（clock_worker，`unit_diff --all`）

| 变体 | delta | windows | landings | judge | changed files |
|---|---|---|---|---|---|
| 基线 `30a4d7827122e165` | `+2` | 2（@7252/@7590 JUMP_FORWARD） | 7 | 12/13 Different control flow | — |
| `[R21-54]` 嵌套 else 候选 `966945af956aa9b4` | `+2` | 2（同两条） | 7 | 12/13 Different control flow | 面板 1 / 20（仅 realtime，源码字节） |

动作**确实发射**：产物源码把 `elif now_date != self.first_run_date:` 改写成 `else: if now_date != self.first_run_date:`（`elif_final_else` 子臂保留为该嵌套 if 的 elif），字节 21548 → 21809。

### 5c. 字节码全等证明（r68a 法：编译整模块，`work/co_compare`）

base 产物 vs 候选产物逐 code object 比较 `co_code`：**12 个 code object，co_code 全等（0 处差异）**，只有 `co_linetable` 因重缩进行号不同。这正是预期：CPython 把 `else: if …` 与 `elif …` 编成**逐条相同的字节码**。因此候选对所有单元判据**中性**（无翻正亦无回退）。

### 5d. 成员数派（`work/membership_census.py`，计数规则见脚本头）

规则：`claim[b]` = 拥有 b 的区域数（b ∈ R.blocks ∪ {R.entry,header,condition,merge}，按块对象身份）。
clock_worker：`regions=67 blocks=191 two_owner(==2)=14 multi_owner(>2)=173 zero_owner=0`。
基线 vs 候选**逐值相同**——本判据在生成端只读区域数据、无副作用，且分析器字节 `f7d849e974904492` 未改，故成员归属构造上不变（原则 2/4 未被触碰）。此定义与 r82a 的 148 / r78a 的 186 不同，引用时须带定义。

### 5e. 验收面（候选安装）

broker **126/128**、quote **92/92**、quotation **153/153**、order_api **37/37**、realtime 12/13；面板其余 19 文件产物字节全等。无文件回退。

## 6. 结论 / 仍开放的机理

`[R21-54]` 把「`@7186` flat 链改发嵌套 `else: If(…)`」这一 `[R21-43]` 机理在此单元完整跑通并正确发射，但**不翻正**：两条残余 `JUMP_FORWARD → @9206` 属主是外层 `if @7186: pass` 的**空 then 臂 `@7212`**（它必须跳到链尾标签，即循环回测），不是我改写的 elif 节点；`elif→嵌套 else` 在字节码层面等价，碰不到那条空臂跳转。要消掉它必须取消 `@7212` 这个空 then 臂、把 `@7248` 归回 `@7186` 的 then 体——那正是被 `[R21-49]/[R21-53]` 测到 `−269` 回退的 re-collection/re-parenting 轴。

⇒ 存档、不安装（`+2` 未变、非改善、非回退，符合简报「landing 在 +2 与 13/13 之间或回退就带数字存档」）。仍开放的机理：生成端无法用「等价的 orelse 重缩进」消跳转；跳转的唯一所有者是空 then 臂 `@7212` 的 re-parenting，与已测 dead 的 collection 轴同面。
