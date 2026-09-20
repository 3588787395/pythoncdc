# Round 16-A 设计：if 臂表达式子区域预生成不得越过结构兄弟区域的入口

## 0. 目标与受害真源

`site-packages/IQCommon/arg_checker.pyc` `<module>.ArgumentChecker._is_valid_quarter`，
严格尺子 `orig=90 decomp=74`（缺 16 条），官方口径 46/47。真源结构：

```python
if valid:                       # 双角色块 86（STORE_FAST valid 之后接 POP_JUMP_IF_FALSE）
    try:
        valid = 1990 <= int(value[:-2]) <= 9999 and 1 <= int(value[-1]) <= 4
    except (ValueError, TypeError):
        valid = False
```

Round 15-B（H1+H2）复原了 `if valid:` 与臂内赋值，但 **整个 `try/except` 外壳消失**：
丢失的 16 条 = `238 JUMP_FORWARD 290` + `240 PUSH_EXC_INFO … 288 RERAISE 1`
（`and` 的 `JUMP_IF_FALSE_OR_POP/COMPARE_OP` 都在，`except` 处理块不在）。

## 1. 归因：结构层无错，是生成层的「越级消费」

区域树（`D:/Temp/r16_arm/out/tree.txt`，未打任何补丁的当前 core）：

```
IfRegion          entry=86  blocks=[86,92,94,152,162,166,168,222,232,236,238]
  children = [Region@92, TryExceptRegion@94, BoolOpRegion@94, TernaryRegion@94]
  TryExceptRegion entry=94  try_blocks=[94,152,162,166,168,222,232,236]  else_blocks=[238]
  BoolOpRegion    entry=94  blocks  =[94,152,162,166,168,222,232,236]   ← 与 try_blocks 逐个相同
```

⇒ Round 15 OUTCOME §四里「分析层没把 Try 挂到 If 下」的猜想**被否证**：
`TryExceptRegion@94.parent` 正是 `IfRegion@86`，父子链完整。真正的机制是：

1. `_if_generate_then_branch` 的第一轮（`region.children`，`region_ast_generator.py:14052-14056`）
   对表达式子区域 `BoolOpRegion@94` 调 `_generate_boolop`，随后
   `for b in child.blocks: self.generated_blocks.add(b)`（`:14070-14071`）把它的 8 个块
   **全量**记成已生成；
2. 这 8 个块恰是 `TryExceptRegion@94.try_blocks`，其入口 94 因此已被占用；
3. `_process_if_blocks` 的 `_try_entry_generate`（`:20349-20367`，守卫 `:20354-20355`）
   只遍历 `region.children` 找 `entry in generated_blocks` 的结构子区域 —— 见入口已 generated
   即 `continue`，`try/except` 整条语句无人发射；
4. 第二轮回退扫描（`:14123` 起，标记在 `:14228-14229`）对同一区域会做同样的事，
   所以只在第一轮加守卫不够（实测 S1/S2 单独都无效，见 §3）。

**同族不对称证据**：else 臂的收集器 `_try_collect_c3` 因为**先**收结构子区域
（`:14663-14675`）再收表达式子区域（`:14677+`）而免疫 —— `r16a_09_diff_try_in_else_arm`
与 then 臂只差 `if/else`，实测 MATCH。这是「then 臂少一条排序不变式」的直接证明。

## 2. 判据（写入识别方法注释的形式）

`识别条件`：待预生成的表达式子区域 `child`（`BoolOpRegion`/`TernaryRegion`）的 `blocks`
包含同一父区域某个**结构兄弟** `sib ∈ region.children`（`LoopRegion`/`TryExceptRegion`/
`WithRegion`/`MatchRegion`）的 `entry`，且 `sib` 既不在 `_generated_regions` 也不在
`_generating_regions`。

`归约方式`：命中即**不预生成本表达式子区域** —— 不发射语句、也不把它的 blocks 记入
`generated_blocks`；把它留在臂的线性序列里，由 `sib` 自己作为单个抽象节点归约
（`sib` 内部再自底向上生成该表达式）。方向仍是从最内层到最外层、不回改数据流。

`AST 映射`：`sib` 生成 `try: <该 BoolOp 的 Assign> … except (ValueError, TypeError): valid = False`
（或 loop/with/match 的对应语句），父区域的臂列表只引用 `sib.entry`，不引用它的块集合。

`原则归属`：原则 2（每个块在任何层级只属于一个区域 —— 入口块的指令段属于结构区域，
不属于越过它的表达式区域）+ 原则 3（嵌套区域作为单个抽象节点）+ 原则 4（父引用子入口）。
判据只用「同一父区域的兄弟之间 blocks/entry 的包含关系」，**不跨区域、不跨层次**，
与既有的 `[Round5-05]` chain-compare carve-out（`:14116-14150`）、
`[R2-With]` 反向补偿（`:14073-14105`）是同一层的互补判据。

`类型集合为何排除 IfRegion`：IfRegion 兄弟与表达式区域共享 entry 是既有的
链式比较 / elif 形状（上方 carve-out 已处理）。实测把 IfRegion 计入（S12c）会让
`r15a_11_anchor_two_nested_regions` 由 MATCH 退为 MISMATCH，并使 4 个 Round 13 已知债
函数继续劣化 ⇒ 结构兄弟集合只取「语句级」四类。

## 3. 实测（落地前全部走 D:/Temp 副本播种，仓库零写入）

候选形态（`D:/Temp/r16_arm/patcher.py`，两轮预生成各加守卫）：

| 变体 | 结构集合 | 21 文件 blast | 说明 |
| --- | --- | --- | --- |
| S1 | 4 类 | FIXED=0 | 只挡第一轮 → 第二轮仍吞 |
| S2 | 4 类 | FIXED=0 | 只挡第二轮 → 第一轮先吞 |
| **S12** | Loop/Try/With/Match | **FIXED=1 BROKEN=0 CHANGED=0** | 采用 |
| S12b | 仅 TryExcept | FIXED=1 BROKEN=0 | 与 S12 同（本形状只涉 try） |
| S12c | +IfRegion | 21 文件同 | 见 §2 末段，代价实测存在 ⇒ 不采用 |

复现电池 `test_repros/round16_arm/`（16 项，全部实测回填）：
基线 `MISMATCH=10 MATCH=6 UNEXPECTED=3`（三个原判为负对照的形状实测也是真缺陷：
`r16a_06` 入口偏移不同、`r16a_12` try/finally、`r16a_05` while 入口 +8 重复发射）；
S12 播种后 `MISMATCH=1 MATCH=15` —— 10 项里 **9 项翻正**，唯一残留
`r16a_05_probe_while_boolop_entry`（`orig=31 decomp=39`，越界**多**发射，另一族）。

全语料只读复算（404 个 pyc，逐函数严格尺子，`D:/Temp/r16_arm/out/corpus_*.txt`）：
`NONE 258 缺陷函数 → S12 257`，FIXED=1（`_is_valid_quarter`）、**BROKEN=0、CHANGED=0**。

## 4. 落地形态与待决项

- 守卫在两个站点重复 19 行不可接受（同一判据两份实现必然漂移，Round 13/14 已多次吃亏）
  ⇒ 抽成识别方法 `_expr_child_blocked_by_structural_sibling(expr_region, parent_region)`，
  注释按 §2 的「识别条件 → 归约方式 → AST 映射」写，两处各调用一次；结构兄弟类型集合
  抽成类常量 `_STMT_LEVEL_STRUCTURAL_REGION_TYPES = (LoopRegion, TryExceptRegion,
  WithRegion, MatchRegion)`（紧挨既有 `_EXPR_REGION_TYPES`，`:180` 后）。
  补丁脚本 `D:/Temp/r16_arm/r16a_patch.py`：4 个 hunk，断言 base sha
  `d07996aaa20d4665`、锚点唯一、BOM/纯 CRLF 不变、`ast.parse` 通过、拒绝重复应用；
  副本产物 `D:/Temp/r16_arm/gen_R16.py`（48175 行，+53 行，0 删除）。

落地前实测（全部副本播种，仓库 `core/` 未写入）：

| 尺子 / 电池 | 基线（当前 core `d07996aaa20d4665`） | R16 补丁 |
| --- | --- | --- |
| 目标 pyc 严格尺子 | 48/49（`_is_valid_quarter` 90→74） | **49/49** |
| 目标 pyc 官方口径 | 46/47 rate=0.9787 | **47/47 rate=1.0** |
| 404 pyc 全语料只读复算（逐函数严格） | 258 缺陷函数 | **257；FIXED=1 BROKEN=0 CHANGED=0** |
| `test_repros/round16_arm`（16） | MISMATCH=10 MATCH=6 | **MISMATCH=1 MATCH=15**（残留 `r16a_05`） |
| `test_repros/round15_arm`（12） | MISMATCH=4 | **MISMATCH=2**（`r15a_01/02` 翻正，无 SENTINEL 回归） |
| `test_repros/round14_join`（16） | MISMATCH=1 | MISMATCH=1（`r14j_09` 不属本族，无变化） |
| `test_repros/round14`（17）/ `round13`（25） | 0 UNEXPECTED | 0 UNEXPECTED |

变体对照（同一 harness，只换结构兄弟类型集合 / 只加一处守卫）：

| 变体 | 结构集合 | 21 文件 blast | 全语料 |
| --- | --- | --- | --- |
| S1 | 4 类（仅第一轮） | FIXED=0 | — |
| S2 | 4 类（仅第二轮） | FIXED=0 | — |
| **R16（=S12 的重构版）** | Loop/Try/With/Match | **FIXED=1 BROKEN=0** | **257，FIXED=1 BROKEN=0 CHANGED=0** |
| S12b | 仅 TryExcept | FIXED=1 BROKEN=0 | 与 S12 同形状（本族只涉 try） |
| S12c | +IfRegion | FIXED=1 BROKEN=0（21 文件看不出） | **BROKEN=1**：`IQEngine/api/api_base.assure_asset` 112→117 ⇒ 排除 IfRegion |

残留与后续：
1. `r16a_05_probe_while_boolop_entry`（`orig=31 decomp=39`）—— loop 入口的**越界重复发射**，
   与本轮「越级消费」方向相反，另立族。
2. T1/T2（把 then 臂也改成「结构子区域先于表达式子区域」，与 else 臂 `_try_collect_c3`
   对齐，并补 `_generating_regions` 进栈）：测试工程师的全语料复算报出「另修 12 个
   SENTINEL、但打坏 4 个 Round 13 已知债函数」⇒ **本轮不合并**，其收益面须先按 §4 的
   同一 A/B 尺子复核（该报告的数字已发现与主代理复算不一致，见 memory 记录）。
3. `r14j_09` / `r15a_08` / `r15a_09` 与 R13c sink 塌陷（`plugin_manager` ×2）见
   `rounds/round16/OUTCOME.md` 的交接清单。

