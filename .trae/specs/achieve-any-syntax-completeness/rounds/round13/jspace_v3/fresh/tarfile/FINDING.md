# tarfile 域总账（rr-v5r165 + rr-v5r166）

## 一、语料读数轨迹

| 轮次 | tarfile | 说明 |
|---|---|---|
| 起点（r164 后） | 146/160（91.25%） | 14 失败单元 |
| rr-v5r165（族 C 多块条件链边归属） | **149/160** | 闭合 `itn`、`TarInfo.create_pax_header`、`TarFile.gettarinfo` |
| rr-v5r166（`TarFile._check` 发射侧） | **150/160** | 闭合 `_check`；剩 10 项：`_Stream.__init__`/`_init_read_gz`/`_read`、`_FileInFile.read`、`TarFile.__init__`/`list`/`add`/`next`/`_load`/`main` |

## 二、r165 族 C（CHAINGRAPH）

4 个门：`[v165-ATTRPREFIX]`（R14b 前缀含 CALL 才拒绝链吸收）、`[v165-CCMEMBER]`
（成员失败出口经纯跳转连接块 ≤4 跳归一；elif 臂分派点取链式比较组末比较块）、
`[v165-CCHEAD]`（else 候选块前驱全在链内 ⇒ 就地升级整条 if/elif/else 链）、
`[v165-SBDOWN]`（链尾合并块作为下游 IfRegion 入口时豁免双角色）。
**反向对照四案（c4 简单 elif / c6 简单 and / c7 纯链式比较 / c3 普通形参 not-and）判官
全 Equal 且产物逐字节 SAME ⇒ 窗口未扩大。**

## 三、r166 `TarFile._check`（两次前提纠正后定稿）

**被推翻的两次误判**：
1. r165 侦察定性「臂尾隐式 return None」——错；
2. 主代理在 r166 任务书里断言「`not in` 操作数互换」——**错**。实查
   `D:/Python/Lib/tarfile.py:2702` 源即 `if mode is not None and self.mode not in mode:`，
   产物 `self.mode not in mode` 本来正确，`CONTAINS_OP` 两侧操作数完全相同。此前把
   「跳转目标互换」误读成「操作数调序」，属未验证的推理。

**真正缺陷（发射侧）**：`region_ast_generator.py` `_if_generate_elif_chain`（原
26782-26790）用闸门 `_r23n16_blocks_have_explicit_return`（「末块以 RETURN_VALUE 结尾」
即算显式 return）把**函数尾隐式汇流 sink** 当语句 → 臂体 `[If, Return None]` → 重编译后
`74 POP_JUMP_FORWARD_IF_NONE` 与 `92 POP_JUMP_FORWARD_IF_FALSE` 的目标 140↔144 互换。
**修复谓词**（+23/−1）：臂末块无后继 ∧ 尾随 `return none` ∧ 无 fallthrough 前驱（W14-B）
∧ 末语句无显式 return ⇒ 弹出该 `Return None`；不命中逐字节回退（C3）。
**不动的杠杆**：elif 嫁接本身在此形上与 `if/if` 字节码同构——放行者
`_else_has_matching_raise`(25388-25396)，强制 DENY 后 R27-A 兜底闸(25446-25448) 会复位
ALLOW（`r166/work/gate_rescue_166.txt`），收益为零、风险高。

## 四、验收判据更新（本轮起生效，可机器检查）

原口径「电池 TEXT-DIFF 恰 6」在本轮被 3 例**同族文本改进**突破：
`v111_m1_exact`、`v111_m2_no_genexpr`、`v111_two_if_diffmsg` 三案由 TEXT-SAME 变
TEXT-DIFF，**全部 BYTE-EQUAL**（判官等价 = 语义零变化），差异内容为 `elif …: raise …`
臂尾那个 HEAD 伪造的、不可达的 `return None`。

**新判据**（写死，后续轮次一律适用）：

> 电池 TEXT-DIFF 集合 = 6 个功效案 ∪ 已登记同族文本改进案；
> **集合内每一项必须是 BYTE-EQUAL**；任何**非 BYTE-EQUAL** 的新增 TEXT-DIFF 视为回归。

理由：`BYTE-EQUAL` 是判官能给出的最强等价声明（产物 pyc 与原件 pyc 逐字节相同）；
在此前提下改变文本，只可能是「删掉伪造语句 / 换等价写法」，属改进而非漂移。
反之若新增 TEXT-DIFF 且判官 DIFF，则一定是语义或控制流变化，必须回退重做。

## 五、已登记未修（测量性差异，Task 93.5）

`TarFile.add`：产物插入一条 `NOP` → 其后全部偏移 +2、异常表 DIFF（orig 182 指令 /
prod 183 指令）。**语义无误，属判官按字节比对造成的测量性差异**。归入 Task 91 统一
评估（加「等价偏移归一」判据或消除 NOP 插入源），不为刷数字而改。
