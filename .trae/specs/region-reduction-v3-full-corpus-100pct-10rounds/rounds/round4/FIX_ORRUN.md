# Round 4 · FIX_ORRUN —— or-run 完整性（chained compare 续接入链）

状态：**仅归档 spec 未落地**（代码已按入站字节精确回退，五套电池与全部 pin 与基线逐位相同）。
flips 计数：**0**（既无 corpus 文件读数改善，也无任何 r4 臂 MISMATCH→MATCH）。

---

## 1. 根因复核（起点＝工单指名的函数，未重新探索该簇）

`core/cfg/region_analyzer.py:28396 _detect_boolop_conditional_chain` 对
`IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc <module>.Strategy.tick_worker_thread`
（原条件 `dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00'`，
run 真入口 off568=`time.sleep(60)`，run 假出口 off612＝后继 elif 串）的 walk：

* 实测基线返回 `[(512,'or'), (524,'or')]` —— 链式比较的两条 leg（536/552）没有入链。
* 用 line-trace 定位到确切停机点：**不是** 29256 的 chained-compare hop（此处没有
  带 `chained_compare_ops` 的 IfRegion 可供 hop），而是 `[R64-diag1 closed-shared-exit-prefix]`
  的 `chain.pop(); break`（回退前位于 29548）：前缀两名成员已汇入同一目标 T=568，
  而 536 的两条边（564 清理桩 / 552）都不是 T，`_r64_rejoin`（R65 豁免）只检查
  「后继的短路边一跳落到 T」，链式比较的正极性 or-run 形态不满足。
* 该截断是消费端 R14c .negate 的成因：`region_ast_generator.py:19133 / :23857 /
  _boolop_mixed_polarity_or_chain(:38252 区)` 看到「全员 IF_TRUE 同目标 568」⇒
  写成 `not (A or B)`，臂入口互换，产生工单描述的
  `off1040 [18,21]→[21]`、`off1098 [17,20,22]→[20,22]`、`off994/1006 3→2 / 2→1`。

## 2. 落地的候选改动（全部在分析端，5 个 hunk，均已回退）

识别规则（只用白名单输入：块末 opcode、后继/前驱关系、块内指令集＝清理桩身份）：

> 当 or-run 前缀已全部汇入同一目标 T，而当前成员 P 的短路边指向块 X、P 的落空后继 Q
> 亦以正向条件跳转结尾时，若 **X 末条为裸无条件跳转、其余指令仅 POP_TOP/噪声，且 X 的
> 目标正是 Q 的短路目标 Y（Y≠T）**，并且 **Q 的落空后继直接或经一个裸 JUMP_FORWARD 纯跳转块
> 落到 T**，且 P 的算子与前缀 run 的算子不同（混合极性边界），则 P 与 Q 是**同一个**
> chained compare 操作数（CPython 把中间操作数 SWAP/COPY 复制入栈，故第一 leg 的假边必须
> 先经清理桩弹掉复制值再汇入第二 leg 的假边；普通 `C and D` 的两 leg 共用同一假出口，
> 因而条件不成立），run 未闭合，P/Q 都是本 run 成员。

hunk 清单：
1. `[R4-ORRUN-CCG]` 检测端：把 R64 的 `chain.pop()` 换成 rejoin（walk 自然落到 Q）。
2. `[R4-ORRUN-CCG]` 同 run 出口同一性：`_r53_same_run_exit` 允许「经清理桩传递」。
3. `[R4-ORRUN-CCG]` W14-A or 链裁剪：末成员落空后继到 T0 由「同块」放宽为
   「同块或经裸 JUMP_FORWARD 纯跳转块同块」。
4. `[R4-ORRUN-CCG]` `_boolop_resolve_merge`：R113 清理块概念的无条件变体
   （`POP_TOP + 裸 JUMP_FORWARD` 桩），merge 由 564 解析为 612。
5. `[R4-ORRUN-CCG]` op_chain 修剪（18462 区）：被剪掉的第二 leg 保留在 `bor.blocks` 归属内。

实测效果（区域层面达成，但**不产出 flips**）：

| 项 | 回退前 | 基线 |
|---|---|---|
| `_detect_boolop_conditional_chain(512)` 返回 | `[(512,'or'),(524,'or'),(536,'and'),(552,'and')]` | `[(512,'or'),(524,'or')]` |
| BoolOpRegion(entry 512) op_chain | `[(512,'or'),(524,'or'),(536,'and')]`（既有修剪） | 同左（但 536 是别处的 entry） |
| BoolOpRegion(entry 512) merge | 564 →（hunk4）**612** | 612 |
| 发射条件 | `elif dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00':` | `elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):` |
| 首个字节码失配 | 仍在 idx 86：`POP_JUMP_IF_FALSE to 612` vs `to 818`（臂体吞掉后继 elif 串） | idx 73：`to 568` vs `to 820` |

per-file 读数（全部未变，逐文件列明）：
strategy 26/27（基线 26/27）、api_base 27/28、matcher 16/17、bar 84/85、
function 70/71、strategy_universe 10/11、load_daily 26/27。
**flips = 0**；无 `off1040 / off1098 / off994 / off1006` 前驱塌缩的修复。

## 3. True-hit vs flips（marker `[R4-ORRUN-CCG]`，line-trace 逐文件计数）

| 文件 | hunk1 CCG 命中 | hunk2 R53 桩 | hunk4 merge 桩 | hunk5 leg 归属 | flips |
|---|---|---|---|---|---|
| strategy.pyc | 2 | 2 | 0 | 2 | 0 |
| api_base / matcher / bar / strategy_universe / load_daily | 0 | 0 | 0 | 0 | 0 |
| function.pyc | 0 | 0 | 1 | 0 | 0 |
| **合计** | **2** | **2** | **1** | **2** | **0** |

即「guard fires, nothing flips」——按验收规则必须回退。回退后
`[R4-ORRUN-CCG]` 计数为 0（marker 随代码一并撤除）。

## 4. 已排除的判别式（后续工单勿重复）

1. **保留 4 名 op_chain + 阻止修剪**（曾实测实现）：修剪端豁免「前一名假边经清理桩汇入本名假边」
   ⇒ op_chain 含两条 leg ⇒ 生成端把同一链式比较**重复计入**，实测发射
   `... or '11:30:00' < dt_strf < '12:30:00' and '12:30:00'`，并把同簇的后继 run
   从 `elif X or Y:` 退化成分层 `elif X: if Y:`（bar/function 一侧读数不变、strategy 仍 26/27）。**排除**。
2. **仅补 rejoin（hunk1）**：Q 在下一轮被 `_r53_same_run_exit`（裸块身份比较）弹出 ⇒ 仍 2 名。
   必须叠加 hunk2；两者都只解决「成员进链」，不解决臂边界。
3. **仅补 merge 桩解析（hunk4）/ 仅补 leg 归属（hunk5）**：run 成员齐了、merge 正确了、
   第二 leg 也不再是无主孤儿块（`Region entry 552` 消失），**臂边界仍旧错误** ——
   后继 elif 串仍在臂体内。
4. **真正的剩余根因在 if/elif 臂归属层，不在 boolop 识别层**：回退前后均实测
   `entry 512` 处**没有 IfRegion**（elif 由父 IfRegion 的 elif_conditions 承载），
   而 `entry 612` 的 region 是带 `chained_compare_ops ['<=','<']`、merge=674 的
   IfRegion；run 完整后 536/552 不再自成一个 IfRegion，该 elif 串便失去宿主而被并入臂体。
   这条「or-run 尾段是链式比较时，父 if 的 else 臂 / elif 链宿主如何选取」是本簇的第二个根，
   与 §1.3 单向数据流的「识别时分类正确」并不冲突，但需要另一张票在条件区域装配层解决。
5. `finance.get_fields` 未追（按工单说明，其首个 diff 已是纯 argval 位移）。
6. 上一票已排除的两项未重复：分析端条件 (6)「J 只能经臂体到达」、生成端 B108 分裂子句。

## 5. 全部读数（回退后，判据唯一 ＝ `scripts/pyc_verify.py`，未修改该脚本）

电池（基线 → 实测，全部相等）：

| 电池 | 单位 | 文件 success/failure | 结论 |
|---|---|---|---|
| r4_probe | **51/67** | 15 / 16 | = 基线 |
| r1_probe | **108/110** | 44 / 2 | = 基线 |
| r1_regress | **34/34** | 17 / 0 | = 基线 |
| r2v3_probe | **105/126** | 41 / 21 | = 基线 |
| r3_probe | **101/122** | 35 / 21 | = 基线 |

pin（回退后 single 读数）：quotation 152/153（失败单元仍是 `get_fundflow_day`）、
cgroup_utils 8/8、email_utils 4/4、calexrights_func 8/8、future_contract_info 29/29、
logger 64/64、ptradeAccount 137/137、quote 86/92（未跌）、
trade_info_utils 37/41（未跌）、trade_live_broker 118/128（未跌）。

pytest（6 个测试文件）：`277 passed, 2 failed, 2 xpassed`，失败仍是
`test_algorithm_correctness.py::TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`
与 `test_deep_nesting_pressure.py::TestBoundaryConditions::test_BOUNDARY_02_large_function`
（与基线同两条）。

## 6. 字节核验（回退后）

| 文件 | 字节 | 行数 | BOM | 行尾 |
|---|---|---|---|---|
| `core/cfg/region_analyzer.py` | **2030385**（= 入站） | **31979** | 恰好 1 个 | 全 CRLF，bare LF = 0 |
| `core/cfg/region_ast_generator.py` | **3684310**（未改） | **58669** | 恰好 1 个 | 全 CRLF，bare LF = 0 |
| `core/cfg/code_generator.py` | 299897（未改） | — | 无 BOM | — |

marker 存续核验：生成端 `[R2-B106 修复·处理器尾回边按循环入口归属]`×4、
`[R2-B107 修复·if 臂按循环入口认领抽象节点]`×7、`[R2-B108 修复·混合极性 or 链逐项还原]`×5、
`[R3-B115 修复·handler 臂终态块 finally 副本前缀唯一归属]`×1、
分析端＋生成端 `r3-b100-armjoin` 8+1、`[R3-B109]` 未增未减；`[R4-ORRUN-CCG]` = 0。
`import core.cfg.region_analyzer, core.cfg.region_ast_generator, core.cfg.code_generator` 通过，
`python -X utf8 -m compileall -q core` 通过。
7 个目标文件的 `*OK.py` 均以「删除 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」重新生成，
无任何手工编辑，读数已回到上表所列基线值。

## 7. r4 探针索引

**未** 追加臂（改动未落地；按验收规则「guard fires / 0 flips ⇒ 回退，不提交」）。
链式比较-in-or-run 的 must-graft / must-not-graft 两条臂留待该簇第二张票（§4.4 的臂宿主根因）
落地时一并入索引，最小 repro 已在 §2/§4 记录：
must-graft `if A or B or ('11:30:00' < x < '12:30:00'): body`（清理桩 `POP_TOP; JUMP_FORWARD`）；
must-not `if A and B: body` 之后紧跟 `if C and D: body2`（两 leg 共用同一假出口 ⇒ 条件 (1) 失败）。
