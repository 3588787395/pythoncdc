# FINDING — rr-v5r121 [诊断登记轮]：or 链拆臂丢体（混合 or+and 嵌套链，真实 R1）——根因闭环与修复路径定性，本轮不修

## 0. 结论速览

- Task 47 目标族实证闭环：最小复现 o1 在 HEAD（96d4113b）精确复现否定卫臂
  拆臂丢体——`if sig == 'a' or sig == 'b' or ((sig == 'c' or sig == 'd')
  and not pred.isdigit()): <臂体>` 渲染成 `if not (sig == 'a' or sig == 'b'):
  <余部整体嵌套>`，a/b 两真路径整体丢失（sig='a' 原应 return tag，产品返回
  None；对应 prepare_predicate 的 `.='` 签名误入 raise SyntaxError，真实 R1）。
- 本轮实施 [v121-ORCHAIN] R64 rejoin 直落边扩展实验：链吸收成功（26/38/50
  全部入链），但消费端 or_groups 对平坦 op 序列做**平坦重建**，产出
  `not ((a or b or c or d) and pred.isdigit())`——内层分组丢失 + `not` 极性
  反转（o1_out2.py 存档）。**证明单点守卫扩展不足，且暴露第二层缺口**。
- 架构定性：臂体已被内层区域认领（每块唯一归属），外层 IfRegion 真臂为空
  才回退否定卫臂；「复制臂体重渲染」违反唯一归属原则（No More Gotos），
  架构性禁止。**唯一正确修复 = 两段式嵌套 BoolOpRegion 构造**（研究级），
  本轮按纪律「新失败先登记，不并行打补丁」回退实验、登记收口，不修。

## 1. 复现（o1，`repro_o1.py`/`repro_o1.pyc`）

```python
def f(sig, pred):
    if sig == 'a' or sig == 'b' or ((sig == 'c' or sig == 'd') and not pred.isdigit()):
        tag = pred[0]
        return tag
    if sig == 'e':
        return 'E'
    else:
        raise ValueError('bad')
```

块边（pycdump 实测）：@0 PJT→90 ft→14；@14 PJT→90 ft→26；@26 PJT→50
ft→38；@38 PJF→110 ft→50；@50 PJT→110 **ft→90**；@90=臂体 [STORE tag,
RETURN]；@110=e 测试 PJF→126；@126=raise。正确结构：
`or[a(@0), b(@14), and[or[c(@26), d(@38)], ¬re(@50)]]`，真出口 90，假出口 110。

语义实测（HEAD 产物）：
- sig='a'：原→臂体→return tag；产品→`not(a or b)`=False→跳过→隐式 None
  （**真实 R1**，prepare_predicate 对应 `.='` 签名误 raise）。
- sig='c'、pred 非数字：原/产品一致（臂体执行）——内层 and 形未被破坏。
- sig='e'：两侧一致 'E'（否定卫臂真臂内的 e 测试恰好保序）。

## 2. 机制链（三层实证）

1. **走查层**（region_analyzer `_detect_boolop_conditional_chain`）：成员 26
   的 rejoin 判定失败——其链上后继 50 的 PJT 目标=110≠T=90，而 50 的
   **直落边**才是 90；R64 守卫（closed-shared-exit-prefix）`chain.pop() +
   break` 弹出成员 26（line-trace 实证，probe_o1.py）。守卫行为**正确**：
   平坦链表达不了嵌套 and 组，强吞必错。
2. **区域层**：BoolOpRegion 仅 [0,14]（merge=90 共享臂体）；臂体 @90 被内层
   BoolOpRegion（`(c or d) and not re`，真出口 90）认领。外层 IfRegion 真臂
   空 → 回退**否定卫臂**渲染（条件取反、余部整体入真臂）——即 HEAD 产物形。
3. **消费端**（or_groups 平坦重建）：[v121-ORCHAIN] 实验把 rejoin 判定扩到
   「后继条件块的直落边汇聚 T」（@50 ft→90 命中）后，链吸收为
   [(0,or),(14,or),(26,or),(38,?),(50,?)]，但 op 序列是**平坦的**——
   内层 or 段 [26,38]（共享真出口 50=and 组续测）的边界与否定 and 尾成员
   [50]（PJT→假出口 110、ft→真出口 90、极性反转）无法从平坦序列恢复；
   重建产出 `not ((a or b or c or d) and pred.isdigit())`（分组丢 + 极性
   反，o1_out2.py）。**第二层缺口实证。**

### 2.1 为什么不能小修

- 否定卫臂回退的成因是臂体唯一归属：真臂空 ≠ 可复制。把臂体复制进
  `if a or b:` 与 `elif (c or d)…:` 两处，重编译字节形不同（CPython 不去重
  语句块）且违反每块唯一归属——架构性禁止。
- R64 扩展已证：吸收成功 ≠ 重建正确；修 op 分配/分组需同时让消费端理解
  「or 段真跳目标=and 组续测」的内层边界 + 否定成员极性——即完整嵌套构造。

## 3. 修复路径（登记，独立轮次实施）

两段式嵌套 BoolOpRegion 构造（先内后外）：

1. **内层段**：识别 or-run [26,38]——判别锚点：成员 PJT 目标 = 链上后继
   测试块（50）而非臂体（与外层 or 成员 PJT=臂体 90 相区分；即指令判别锚
   「成员真跳目标=共享臂体」的反向应用）；尾随 and 尾成员 [50]——PJT=
   全链假出口（110）且 ft=真出口（90）且极性反转（`not` 操作数，W14-A/R3-K
   同域极性机制）。先构成嵌套 BoolOpRegion：`and[or[c,d], ¬re]`，真出口
   90、假出口 110。
2. **外层链**：嵌套区域作为**单一成员**并入外层 or 链 [0,14]（成员可为
   区域，链真出口 90、假出口 110），消费端按既有 or_groups 重建
   `or[a, b, <嵌套区>]`。
3. 验收：o1 重编译 BYTE-EQUAL 为目标；prepare_predicate /prepare_predicate
   字节收敛（+12 残余的主体）；因动核心走查+消费端，需全额 254 案电池 +
   pytest 7 套件 + REAL46 sweep 复核（按用户政策，此为「大改动」级别）。

## 4. 验收口径

本轮诊断登记收口，**零源码改动**（[v121-ORCHAIN] 实验已完整回退，工作树
core/* 与 HEAD 96d4113b 逐字节一致；grep 复核否定卫臂形=1 确认基线还原）。
不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。实验产物
（o1_out2.py）与探针存档于本目录，供下轮实施比对。

## 5. 剩余登记（未变）

- `/iterfind`（−102 字节）while-1 体丢失大族（pe8 同域，r105 诊断在案需
  派发表先行）；v118 E2 残余（while 底部 store-recheck）同域。
- E6 相邻 NOP 对（Round-33 守卫同形不可分，语义等价低价值）；
  46 sweep 其余 DIFFERENT（REAL46-011/012/013/014/015/016）、17 ERROR。

## 6. 证据文件

`repro_o1.py`/`repro_o1.pyc`（最小复现）、`product_HEAD_o1.py`（HEAD 否定
卫臂产物）、`product_v121experiment_o1.py`（实验错误形存档）、`probe_o1.py`
（区域树+走查 line-trace 探针）、本文件；过程中间件（pycdump、对照产物）
在 `D:/temp/opencode/cl_layout/r121diag/`，不入库。
