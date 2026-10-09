# DIAG/FIX B142 + B143 — handlers 循环落点：发射契约挡住强发，不登记形同惰性

票号 **B142 / B143**（同一条通道的两臂，接 B141）。镜像 `D:/Temp/r141/wt`
（98 个 `.py` 与仓库逐文件 sha256 对齐 `bad=0`），仓库 `core/` 全程未动
（收尾复核 `region_ast_generator.py = e9a8f65f6451bcc8`、`region_analyzer.py = e926a54f17753b33`）。

## 0. 先补齐 B141 缺的读数（全部无副作用，逐条实测）

**探针惰性自证**：在 `_generate_region` 入口打 `[R142]` 行（只读 `type(region).__name__`、
`region.entry.start_offset`、`id(region)`、`len(self.regions)`、`len(self.generated_blocks)`，
**不碰 `.successors/.predecessors/get_block_by_offset`**）跑 handlers ⇒ 产物 `9093` 字节，
与仓库封存产物**逐字节相同** ⇒ 该形探针可用。同样在 B141 补丁里加 `[B141P]`（只读局部量与
`start_offset`、`len(stmts)`）⇒ 产物与纯 B141 补丁**逐字节相同** ⇒ 读数可信。

读回的事实：

| # | 实测 | 用途 |
|---|---|---|
| 1 | `LoopRegion(entry@90)` **确实**经 `_generate_region` 的 loop 分支派发（`enter LoopRegion entry@90`） | 施工点没选错 |
| 2 | `@404` 的 `BlockRole = None`（新建 CFG + 新建 RegionAnalyzer 独立进程读 `an.block_roles`） | **排除**「LOOP_EXIT 抑制」通道（发射器 `:9240`、`:52760`、文档 `:51228` 那条与本案无关） |
| 3 | `@390`（回边块）`succs=[404, 104]`，`@404` `succs=[] preds=[390]`，`@408` `preds=[90]` | `@404` 是回边测试的**顺序落点**，`@408` 是条件假边的 while-else 臂——两者身份可分，无需名字/偏移特判 |
| 4 | `LoopRegion@90` 的 `merge_block/exit` 均为 None，`@404` 只是 `blocks` 的 plain-member | B141 的排除表并没有把 `@404` 挡在门外 |
| 5 | B141 打印：`terms=[404]`，`_generate_block_statements(@404)` 返回 **1 条语句**，即**发得出来** | 失败原因不是判据，而是返回契约 |
| 6 | 同一文件另有 `TWHThreadRotatingFileHandler._target`：存在**两个 entry 相同（@2）的 LoopRegion**，其一 `break_blocks=[784]`；落点块 `@780` 在另一个区域里是 `body_blocks` 成员 | 角色面必须取**全局所有区域**，只看本区域会双发 `return None`（B141 把该健康单元从绿打红就是这条） |
| 7 | B141 产物里 `TWHThreadController._target` 只剩 **77** 指令（orig 199）：`@412` 之后 122 条全丢 | `[result] + 落点语句` 这个**列表返回**在父区域（IfRegion 右臂）位置不被消费 ⇒ 父臂被裁掉 |

## 8. B142（不登记，交父区域发射）——惰性

按 #7 的教训改成**只放开登记、不强发**：在 `region_ast_generator.py:5361-5374` 收尾扫的
`self.generated_blocks.add(block)` 之前，若块满足「在**任何**区域里都不属于任何角色字段 ∧ 零正常后继 ∧
零异常后继 ∧ 前驱全在本循环块集内」则 `continue`（不登记），将发射交回父区域的线性序列。
补丁字节 `a0a13cfad723da6d`。

| 文件 | HEAD | B142 |
|---|---|---|
| `IQCommon/logger/handlers.pyc` | 29/30（红 `_target`） | 29/30，产物 `9093` 字节 **SAME_as_HEAD** |
| `fly/data/quotation.pyc` | 153/153 | 153/153，**SAME_as_HEAD** |

⇒ 放开登记**没有**让 `@404` 被任何地方发射（父区域的臂走查并不回到未登记的 plain-member 落点），
逐字节退回修复前。这不是判据错，而是**父序列的取块方式**不消费它。

## 9. 结论与下一票的唯一入口

三个形（B141 强发 / B142 不登记 / B127 成员判据）现在都被实测钉住：**handlers 的 `@404`
落在「循环区域的收尾扫只登记不发射」与「父区域臂走查只消费自己认领的块」两条规则的缝里**。
可行的落地通道只剩一条，且必须先读它、不许再叠判据：

> 读 `IfRegion` 右臂（本案例的父区域）用于**顺序消费块**的那个集合/游标
> （`_if_generate_branch_stmts`，B136 旧档记录 `:8007` 是 `@408` 的唯一请求者，
> 说明该函数**能**请求循环之后的落点块），查清它对 `@404` 为什么不请求
> ——是被 `generated_blocks` 挡（B142 已放开仍无效 ⇒ 不是这条）、
> 还是被「臂块集只取 `then_blocks/else_blocks`」挡（若是，则修的是**臂的块集来源**，
> 不是发射开关），还是父区域 `blocks` 里根本没有它。

在该读数拿到之前，禁止再向 `_generate_region` 的 loop 分支加任何发射/登记开关；
禁止把 `[result] + stmts` 的列表返回当作可用通道（#7 已证它在 IfRegion 臂位丢 122 条）。

本轮（round 11）至此：落地补丁 1 张（B133，封表读数不变 6580/6617、387/402），
证伪 5 臂（B139c blanket、J-gate、J+F-gate、B141 强发、B142 不登记），
残余 **15 文件 / 37 单元**。
