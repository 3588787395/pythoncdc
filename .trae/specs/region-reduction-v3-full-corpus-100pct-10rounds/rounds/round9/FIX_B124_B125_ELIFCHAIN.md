# Round 9 FIX（B124 + B125）：链出口被臂块表认领 ⇒ 发射边界切开；臂出口＝区域接口而非臂首块末指令

## 落地声明

**代码已落地**（非「仅归档 spec」）。凭据＝grep 标记，工作树与提交内容同字节：

| 标记 | 位置（HEAD 之上的新字节） | 命中 |
|---|---|---|
| `[R9-B124 elifchain-exit-in-armtail]` | `core/cfg/region_ast_generator.py` 新方法 `_split_arm_at_chain_exit` docstring 与其调用点 | 2 处 |
| `[R9-B125 loopheader-arm-exit-confluence]` | 同文件 `:13058` 起既有分支内 | 1 处 |

字节面：`git diff --stat` ＝ 158 插 / 36 删（单文件）；
WIP sha256 `e9a8f65f6451bcc895c55585…`；回滚凭据 HEAD blob `a1f20232e3f526937e998188…`，
快照 `D:/Temp/r9main/WIP_R9_ELIFCHAIN.py`（与工作树逐字节相同，已核）。
BOM 单头 `efbbbf` ✓；CRLF 未被整文件改写（改动行数 194／总行 59,107）；`py_compile` COMPILE_OK；
新增 `print(` **0**；`def _?(fix|merge|patch|fallback|hack|workaround|temp)_` **0**（G3）；
按文件/函数名、绝对偏移、长度阈值的特判 **0**（G4，正则扫 `\.pyc['\"]|start_offset\s*[<>=]+\s*\d{2,}|len\(.*\)\s*[<>=]+\s*\d{2,}` 无命中）。

## 一、B124：链的汇出块 M 被写进臂块表

`_split_arm_at_chain_exit(region, arm_blocks)` 由 `_if_generate_full_elif_chain` 在
`_if_generate_elif_chain` 装配**之前**调用。**调用点 1 处**（`:15745`），处在一个
`for _r91_arm_attr in ('elif_bodies_0', 'elif_final_else')` 的循环里：依次对
`region.elif_bodies[0]` 与 `region.elif_final_else` 两类臂表试切，首个命中即 `break`
并被 `region.elif_bodies[0] = _r91_kept`／`region.elif_final_else = _r91_kept` 就地替换，
原表存入 `_r91_saved_*` 于装配后还原。
（注：方法 docstring 写「在…两处调用本方法」，实为 1 个调用点覆盖 2 类臂表——
措辞与实现不同形，且首个命中即 `break` 意味着两类臂表同时误认 `M` 时只切第一类；
一并记入 §四.3 的注释审计项。）三条合取判据（缺一即返回 `None`，
调用方逐字节走既有路径）：

- (a) `region.merge_block` 存在且**确实是该臂块表的成员**（认领冲突的直接证据，区域成员关系）；
- (b) 链内存在块 `b`（`b != M` 且 `b` 不在切出的链后集）以**无条件前向跳转**
  （`JUMP_FORWARD`/`JUMP_ABSOLUTE`）终止且目标正是 `M`（越臂短路入边；fall-through 不算）；
- (c) 切分后臂仍留有 ≥1 块（排除把整臂清空——那是另一个缺陷面）。

归属由**可达性**决定，不由偏移排序决定：臂入口＝臂内无任何臂内前驱的块；
臂体闭包＝从入口出发、遇 `M` 即停的后继闭包；闭包外（含 `M`）唯一归属链后序列。
切出的链后块以**入口**为单位交给区域发射器整体渲染（原则 3/4），`M` 被登记进
`generated_blocks/generated_offsets`，父序列不重复发射，与既有 R45-A/R46-B 补发路径互斥。

根因链（实测 `IQCommon/data/finance.pyc :: <module>.get_fields`）：`M` 及其链后后续被嵌进臂体内部
⇒ 那条越臂跳转在产物里没有合法落点，被重定位到整个区域之后 ⇒ 该路径**绕过两条入边共用的汇出测试**
（654 行跳过 665 行共用的 `error_no == 0`，直达 `return fields`）。

## 二、B125：臂出口是**该臂区域的汇出块**，不是臂首块的末指令

`:13058` 分支原读「`_else_succ` 是否 `then` 臂首块的顺序后继」来判循环体尾。
但若 `then` 臂已被某区域认领（`_r47_ter.entry is _then_succ` ∧ `id(_r47_ter) in self._generated_regions`）
并已作为抽象节点发射，则该臂的出口是**该区域的 `merge_block`**，臂首块自身的末指令只是该区域的条件跳转。
此时「`_else_succ` 是臂的落入块」的唯一正确读法就是 `_else_succ is 该臂区域的 merge_block`——
它同时是循环头条件跳转的落点，两条入边共享它 ⇒ 按定义是**两臂汇合点**，不是 `else` 子句体
（真 `else` 臂的 then 臂必以无条件前向跳转越过它）。

判据只读 `L(A)` 内的区域出口接口与该块的归属身份；非区域态时沿用既有
「顺序后继 ∧ 末指令既非前向跳转亦非后向跳转」的旧读法，**逐位不变**。

⇒ 这一票直接证实了被回滚工单 `ADJUDICATION_R9LO_REVERTED.md` §二.2 的实质发现：
`function.reconnect` 在 HEAD 的**识别**已经是对的（`IfRegion@192 merge=520`），
坏落点出自生成端为「循环头条件 `if`（它根本没有 IfRegion）」构造 elif 链的那一步。
修法因此落在生成端，而非我先前两度尝试的分析端边界判据。

## 三、实测翻转（逐单元名单，主代理自有复测）

| 文件 | before | after | 翻正单元（完整 qualname） |
|---|---|---|---|
| `IQCommon/data/finance.pyc` | 31/32 | **32/32 success** | `<module>.get_fields` |
| `IQEngine/plugins/plugin_system_trade/function.pyc` | 70/71 | **71/71 success** | `<module>.reconnect` |

全量 402 八分片：units **6575 → 6577**／6617（99.3653% → **99.3955%**），
files **384 → 386**／402，`REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`，
**新增失败单元＝0**（逐单元名集差集实测为 0），quotation 153/153，六套件仍 2 failed/277 passed/2 xpassed。
详见 `VERIFICATION.md`。

## 四、本票的缺口（如实登记，不粉饰）

1. **未做 ≥10 条最小复现臂**（spec 每轮纪律「每个缺陷 ≥10 复现 · 深度 ≥3 变体 · ≥2 MATCH 负对照」）。
   `test_repros/round9/` 内 `b124/b125/elifchain/chainexit` 命名臂命中 **0**；
   工程师在 150 回合上限处被截断，最后完成的是既有电池复跑（`D:/Temp/rrv9/regress_step3.log`：
   anchor 454/454 保持、r9a1 15/20 不变差、r9quote 43/53 不变差）与 34 集／402 集前的目标面读数，
   没有留给它建臂。**本票因此是按「逐单元翻转」接受，而非按自有牙接受**——
   补臂登记为轮 10 前置项（Task 11 之前），机制＝「链汇出块被臂表认领」的深 3 变体 + `else` 真臂负对照。
2. 工程师**未写 FIX.md**（回报文件 0 字节，`d:\Temp\qoder-cli\…\a5ef877e050a662ce.output`）。
   本文件由主代理按其落地字节与自有复测代写，判据段（§一/§二）是从代码 docstring 与条件式
   逐条对照读出，不是转述其口头结论。
3. `:15722` 起 49 行改动消费者方法 `_if_generate_full_elif_chain` 本体，
   其**自身 docstring 未补六项模板**（新方法 `_split_arm_at_chain_exit` 有完整六项 ✓）；
   且该 docstring 称「两处调用本方法」而实为 1 个调用点遍历 2 类臂表、首个命中即 `break`——
   两处均属**注释 vs 行为**不一致，记为 Task 11 逐方法审计对象。
