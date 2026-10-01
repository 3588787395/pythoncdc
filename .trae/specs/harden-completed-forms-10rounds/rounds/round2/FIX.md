# Round 2 修复工程师报告（B8 except* 类型表达式 + R2-O2 白名单移除 + B9 异常区域混合链装配）

- 修复对象：评审交 fix 批三项——①B8（except* 首 handler 类型表达式被丢弃退化
  `Exception`，4 复现全转 MATCH）；②R2-O2（exception_handler.py 异常类型名白名单，
  零容忍违规，结构性移除）；③B9 链装配层（异常区域包裹下混合链 or 尾续接被
  TryRegion 范围认领阻断，r2_08 全封闭、r2_17.g 封闭、r2_09.g/r2_10 两单元/r2_17.f
  症状改善但读数未变，残留已定位到消费层，见 §4）。
- 基线：工作树 = fe486d42（round2 评审产物），core/ 起点零改动；全部基线读数先行
  实测记录（与本轮对照，见 §7）。
- 唯一判据：`python scripts/pyc_verify.py single`（pylingual compare_pyc 逐单元）；
  全量回退门禁 = 402 文件重生成 + 8 分片 batch + compare（REGRESSIONS=0）。
- 硬约束自检：无函数名/文件名/异常类型名白名单（R2-O2 已拔除）、无 start_offset
  数值魔法阈值（帧前缀签名 argval 全等、位置锚定于末个 PUSH_EXC_INFO 之后，属块
  内结构事实）、无跨层读取（豁免判据只读同层 block_to_region + 块内 opcode 集合）、
  无新增 self 跨方法状态（`_EXC_FRAME_GUARD_OPS`/`_EXCEPT_STAR_FRAME_PREFIX` 为类
  常量，`try_scope_exempt` 为参数）、被丢弃操作数全部接回（or 尾操作数并回原链，
  「以少发射换全绿」不适用——B8 是把错误默认值换成正确重建，B9 是补齐链成员）。
- 未执行 git commit（主代理负责）。

---

## 1. B8 — except* 首 handler 类型表达式退化 'Exception'

### 1.1 根因（结构性，file:line）

except* 组匹配的 CPython 3.11 标准降级帧（dis 实测 n2_02/r2_12）：

```
PUSH_EXC_INFO; COPY 1; BUILD_LIST 0; SWAP 2; <类型表达式>; CHECK_EG_MATCH
```

`_collect_pre_check_instrs`（修复前 region_analyzer.py:10116-10134）把 PUSH_EXC_INFO
与 CHECK_EG_MATCH 之间的**整段**收集为匹配表达式——框架帧头
`COPY 1; BUILD_LIST 0; SWAP 2`（构造未匹配子组收集列表，不属于用户类型表达式）混入
段内；`_reconstruct_except_match_expr` 对含组合指令的段走 ExpressionReconstructor，
帧污染致「栈上恰余一个白名单类型节点」接受判据失败，命中保守回退 **'Exception'**
（code_generator.py:717/:2094 直通发射 `except* Exception`）。后续 handler 入口块无
框架前缀（首指令即 LOAD_GLOBAL）故类型保留——与评审「仅首 handler 丢失」实证一致。

条款违反：C1（读了 handler 入口块内的类型求值段，但把帧指令当表达式语义归约——
识别面读了 L(A) 而归约语义错配）。性质 = 丢弃（捕获范围扩大）。

### 1.2 修复（region_analyzer.py:10131-10134 + :10135-10179）

`_collect_pre_check_instrs` 增加除 except* 组匹配帧前缀的剔除判据：

- 新类常量 `_EXCEPT_STAR_FRAME_PREFIX = (('COPY',1), ('BUILD_LIST',0), ('SWAP',2))`；
- 识别条件：本帧终止 op 为 CHECK_EG_MATCH（`has_eg_match`，块内 opcode 集合事实），
  且末个 PUSH_EXC_INFO 之后**紧邻**的前三条指令 opname+argval 与帧前缀**逐位全等**；
- 归约方式：命中即重置收集段（帧头不进表达式段），剩余段原样交
  `_reconstruct_except_match_expr`（纯加载段 → 名字字符串；组合段 → 单节点重建）；
- AST 映射：剩余段 → handler 节点 exc_type（`except* TypeError:` 保留 TypeError）。

[C1] 只读 handler 入口块自身指令序，前缀签名位置锚定 + argval 全等（与既有
PUSH_EXC_INFO…POP_TOP 裸 except 帧签名判定同风格）；[C2] 段→exc_type 单节点黑箱
重建；[C3] 显式守卫：仅 CHECK_EG_MATCH 帧触发（普通 except 帧无此帧头不剔除），
签名不匹配不剔除（保守回退通道原样保留，绝不静默退化裸 except）。

### 1.3 单变量自证

B8 修复单独落地后四复现全 MATCH（见 §7.1）；哨兵七项读数逐字节持平（§7.5）。

## 2. R2-O2 — exception_handler.py 异常类型名白名单结构性移除

### 2.1 违规面（file:line）

`exception_handler.py:148/:196`（修复前行号）：CHECK_EG_MATCH / CHECK_EXC_MATCH 的
同块 backward 扫描失败时，跨块回退在**全部块**中按 argval ∈ ('ValueError',
'TypeError', …, 'BaseException') 白名单 + 字节距离阈值（40/30）拾取 LOAD_GLOBAL。
两条都违规：名字白名单（任意类型的 handler 均可合法出现）、数值距离（无结构语义）。

### 2.2 修复（exception_handler.py:50-105 新方法 + :199-204/:235-240 两处回退替换）

- 新模块级方法 `_find_handler_type_load(analyzer, block, check_index)`：
  - 识别条件：异常类型求值段是与 CHECK_* 同块的直线前缀；同块扫描失败时，类型加载
    若存在只可能位于与 CHECK 块经**无条件转移**线性连通的前驱块中，且必须是该前驱
    块**首指令**（handler 链后续入口 = 前一 CHECK 匹配失败跳 / 异常表目标 ⇒ 块首）；
  - 归约方式：沿「末指令为无条件 JUMP_FORWARD/JUMP_ABSOLUTE 且目标=当前块」或
    「末指令非跳转且当前块 ∈ 其正常 successors（fall-through，且不在
    exception_successors 中）」的边逐块回溯；每块自首指令向后扫描
    LOAD_GLOBAL/LOAD_NAME，命中块首加载即返回 offset；帧边界块
    （PUSH_EXC_INFO/CHECK_*/RERAISE）、条件跳转块、RETURN/RERAISE 收尾块、已访块
    一律终止；
  - AST 映射：返回 offset 作为 handler 链后续 handler 入口加入
    except_handler_targets（与同块扫描命中点同语义）；
  - [C1] 只读块内 opcode 序列与 CFG 后继/前驱集合（无条件转移与 fall-through 均为
    正常边，异常边被显式排除）；[C2] 不窥视区域内部；[C3] 显式守卫：帧边界、条件
    分支、已访块终止，绝不按名字/数值距离跨块拾取。
- CHECK_EXC_MATCH 侧回退点补齐 `check_block`/`check_index` 记录（原实现重扫全块后
  丢弃块身份），None 防御保留。
- 零回归实证：round2 全组 19 文件 + 七哨兵 + 402 全量重生成（REGRESSIONS=0，§7.6）。
  另以临时插桩（验后即除）实测白名单回退在全语料（round2 19 文件 + 七真身）零触发，
  即该回退在可达语料上是死路径，移除无行为影响。

## 3. B9 — 异常区域包裹下混合链装配降级（链装配层封闭）

### 3.1 根因（结构性，与评审「装配未触发」定性收敛到单点）

CFG/区域 dump 实证（四复现全部命中同一断点）：TryRegion 建立时按 try 范围表把
try 体/handler 体/finally 体**整段**登记进 block_to_region（`_register_region_blocks`
族）；随后 `_identify_boolop_regions` 的主链 walk 经 `_try_unify_mixed_boolop_chain`
沿链尾 fall-through 续接 or 尾操作数时，`if ft_succ in self.block_to_region:` 处因
候选块 owner = TryExceptRegion 而 **break**（修复前豁免仅认 LoopRegion）——范围内层
`if/while/assert` 混合链的 or 尾操作数块被父区域按**范围**认领（与循环 body_blocks
认领同构，正是 [B1b fix-r2] 已在循环维度修过的同一缺陷族），op_chain 停在 and→or
边界，残链被消费端物化为拆裂结构（极性反转 / 幻影 while False / or 尾丢失）。

插桩实测四复现断点（链=[and 组…, 边界成员], ft=or 尾候选, owner=TryExceptRegion）：

| 复现 | 断点（unify break-at-claimed） |
|---|---|
| r2_08.f / r2_08.g | chain=[66,72] ft=76 |
| r2_09.g（finally 内 while+assert 两链） | chain=[150,154] ft=158 / [142,146] ft=150 / [194,198] ft=202 |
| r2_10.f_while / f_ternary / f_assert | chain=[4,8] ft=12 / [4,32] ft=36 |
| r2_17.f / r2_17.g | chain=[38,42] ft=46 / [96,100,104] ft=108 / [8,12] ft=16 |

条款：C1（候选块的块级结构事实已满足续接判据，仅因父区域范围登记被整体排除——
豁免缺失即未封闭）；与 B7「外层循环包裹」同构，包裹维度从 Loop 扩至 Try 族。

### 3.2 修复（region_analyzer.py，4 处）

| # | 锚点（当前树行号） | 内容 | 条款 |
|---|---|---|---|
| A | `_try_unify_mixed_boolop_chain` :27523-27559 | **[R2-B9 fix] TryRegion 范围认领豁免**（[B1b fix-r2] 循环豁免在异常区域维度的镜像）：候选块 owner=TryExceptRegion 时放行判据 = (a) 候选块与链内全部成员块均不含异常帧指令（新类常量 `_EXC_FRAME_GUARD_OPS` = PUSH_EXC_INFO/CHECK_EXC_MATCH/CHECK_EG_MATCH/PREP_RERAISE_STAR/RERAISE/WITH_EXCEPT_START——handler 入口帧、except* 匹配/清理帧、finally 收尾帧、with 异常帧一律带帧指令，被此守卫排除，链不是 try 自身帧装配）；(b) 放行后落到与未认领候选**完全相同**的验收路径（多成员 run 交 `_detect_boolop_conditional_chain`，单成员 or 尾交 [B1b] 三判据），不另套 `_b1b_loop_body_run_continuation`——其 (2) 臂三元真值块守卫对 if-else 形 or 尾误报（Y=then 体 JF→merge、Z=else 体后继含 merge 与普通 if-else 同签名），该守卫是循环上下文专用加强，try 上下文的帧风险已由 (a) 覆盖（r2_08.f 实证：走续接判据被误拒，走 [B1b] 判据正确装配）。任一验收不成立维持原 break | [C1] 帧指令集合 + block_to_region 同层查表；[C2] 完整链交 `_create_boolop_region_from_chain` 单 BoolOpRegion 黑箱组合；[C3] 显式守卫排除帧块，认领面零扩大（TryRegion 结构消费走 entry 引用语义不受影响） |
| B | `_detect_boolop_conditional_chain` :25603 签名 + :26625-26643 claimed-check | **[R2-B9 fix] try_scope_exempt 参数**：多成员 or-run 子 walk 的镜像豁免——`try_scope_exempt=True` 时，候选块被 TryExceptRegion 认领且不含 `_EXC_FRAME_GUARD_OPS` 帧指令则放行进链，其余被认领块维持原 break（`ft_succ in claimed` 硬 break 保留，skip_claimed_check=False 原语义在参数缺省时逐位不变） | 同 A |
| C | `_try_unify_mixed_boolop_chain` :27563-27566 | 多成员 run 子 walk 调用改传 `try_scope_exempt=True`（与豁免 (a) 同一判据闭合 run 场景） | 同 A |
| D | `RegionAnalyzer` 类头 :1212-1221 | 新类常量 `_EXC_FRAME_GUARD_OPS`（与既有守卫族 `_detect_while_condition_boolop_chain` 后向回溯、`_identify_conditional_regions` 使用的帧指令集一致，RERAISE/WITH_EXCEPT_START 补齐 finally 收尾与 with 帧） | 判据集共享，防漂移 |

触及方法 docstring 三要素（识别条件/归约方式/AST 映射 + C1/C2/C3 声明）已同步：
`_collect_pre_check_instrs`（B8 全量重写）、`_find_handler_type_load`（新方法）、
`_try_unify_mixed_boolop_chain`（豁免段内联注释声明三要素，方法 docstring 既有
[B1b] 段落之后补 [R2-B9] 判据段）、`_detect_boolop_conditional_chain`（claimed-check
处 [R2-B9] 注释段：识别条件/归约方式/AST 映射/守卫）。

### 3.3 单变量自证

- 豁免 (a)+(b)（含续接判据）落地：r2_08.g、r2_17.g 转 MATCH；r2_08.f 仍失败
  （f 为 if-else 形，`_b1b_loop_body_run_continuation` (2) 臂三元真值块守卫误报）；
- 去除 (b)、改落共享验收路径（终版）：r2_08 全 3/3、r2_17.g MATCH；
- 多成员 run 子 walk 豁免（C）：`a and b or c and d` 形在 try 内可装配
  （r2_17.f 第二链 `elif a or b and c:` 恢复正确 op 组）；
- 全部哨兵 + round1 抽验 + 402 全量零回退（§7）。

## 4. B9 残留（如实登记：消费层缺陷，本轮不扩线）

链装配层封闭后残留单元（读数未变、症状改善，见 §7.2 diff）：

| 单元 | 现症状（对比基线） | 残留根因（已定位，未修） |
|---|---|---|
| r2_09.g | 输出与基线逐字节相同（`if a and b or c:` + 幻影 while False + assert 链拆裂） | finally 内旋转 while 的**消费层**：LoopRegion（entry=b 测试块，体/尾重检块均被 TryRegion 范围认领）的 while 条件关联与 `_loop_generate_while` 生成；assert 链经 `_b6_assert_absorb_and_run` 的前驱吸收同样被范围认领阻断（R2-O1 哨兵面相邻） |
| r2_10.f_while | `if not (a and b):`+孤儿 `if c:` → **`if a and b or c:`**（极性/or 尾已修复）；循环体仍内联、break 仍丢 | 旋转 while 条件消费：IfRegion 抢先吞并循环（`_build_basic_if_region` 的 `_find_containing_loop_body(block)` 只认「if 入口块 ∈ LoopRegion.blocks」，try 包裹下链头块 4 在 LoopRegion@8 之外 ⇒ in-loop 过滤不触发 ⇒ then_blocks 吸收整个循环体；对照 r1_10（无 try）同形状被既有守卫清空 then） |
| r2_10.f_ternary | `if a and b:` → **`if a and b or c:`**（条件链完整）；值结构（2/3）仍丢 | TernaryRegion **已正确创建**（实测 `TernaryRegion@4 blocks=[4,32,36,40,44,46]` 且进 self.regions），但 try 体语句生成端未把 TernaryRegion 当 `acc.append(...)` 内 IfExp 消费，退化为 if 语句——生成端 try 体装配缺陷 |
| r2_17.f | 双链条件全部恢复正确（`if a and b or c:` / `elif a or b and c:`）；幻影 `while False` 与末尾 `return out` 丢失仍在 | 同 f_while（旋转 while 消费）+ try 体尾部块发射 |

立项建议（交后续轮）：「异常区域包裹下循环/三元消费层」专项——①`_find_containing_loop_body`
/ `_should_skip_block_for_if_region` 族守卫的归属判据从「block ∈ LoopRegion.blocks」
扩为「block ∈ LoopRegion.blocks ∪ 候选 then 臂入口块 ∈ LoopRegion.blocks」（镜像
[W43]/[R52] 的结构回退先例）；②try 体语句生成端对 TernaryRegion 子区域的 IfExp
派发；③`_b6_assert_absorb_and_run` 前驱吸收的 TryRegion 豁免（与 A 臂同判据，
触及即回归 R2-O1）。三者均有本轮.dump 可复用的机制锚点。

## 5. 基线既有独立缺陷（量力项，逐个评估后登记不修）

| 复现 | 现读数（=基线） | 根因假设（一句话） | 立项建议 |
|---|---|---|---|
| r2_04（try 嵌 3 层+重抛） | 1/2（f） | 中层 try 的 handler 被物化为内层 try 的 `else: try: pass except…` 幻影结构——try 嵌套归约把「内层 try + 空洞体 + 外层 handler」误配对（异常表 target 链在重抛 RERAISE 处分裂后，中层 handler 与内层 try 的 else/finally 帧匹配错位） | R2-01 立项：`_identify_try_except_regions` 多层配对以异常表 depth+target 恒等重建 handler 归属，禁止 else 块携带 handler 帧 |
| r2_06（循环内 try 体 continue） | 2/3（f） | try 体尾 `continue`（JUMP_BACKWARD→FOR_ITER，位于异常表范围**外**的独立块）在 try 体语句装配中被丢弃——R76-D continue-sink 族在「continue 块不属于 try 范围但属循环体」时的 sink 判据未覆盖该归属组合 | R76-D 立项扩充：try 体尾块以 JUMP_BACKWARD 落循环头时显式发射 Continue（块末 opcode + 回边目标身份判据，零名字特判） |
| r2_14（finally 内 break/return 吞异常） | 3/4（f） | finally 体 `if i == 1: break` 的 break 被降为 pass、post-loop `return out` 前移进 finally——finally 帧吞异常形态下 break 的循环出口边与 finally 收尾帧（RERAISE 尾）的发射序竞争（评审 A-3 注记的 `_loop_generate_while` if-break 丢弃分支与 finally 叠加面） | R2-04 立项：finally 体 if-break 与 for 组合的发射路径（块末 JUMP_BACKWARD→循环头身份 + finally_copy 帧守卫） |
| r2_07（match 模式降级） | — | 按 REVIEW 归 Round 4 match 形态范围，本轮只登记不修 | 已登记 |

## 6. B7 复验（rv_03/rv_05/rv_09）

读数与 round1/round2 评审归档一致（各 failure 1/2），未回退未变化；其根因（外层
循环包裹混合链，无 try 参与）与本轮 B9 的 TryRegion 豁免不同面，维持「已定位未修」。

## 7. 自测全量读数表（终版树）

### 7.1 自测 1：B8 四复现 → 全 MATCH（pycdc 重生成 *OK.py 后 single）

| 复现 | 修复前 | 修复后 |
|---|---|---|
| r2_11_except_star_single | failure 1/2 | **success 2/2 100%** |
| r2_12_except_star_multi | failure 1/2 | **success 2/2 100%** |
| r2_13_except_star_mixed（f+g） | failure 1/3 | **success 3/3 100%**（评审预期的框架序位移残留未出现，随类型修复一并闭合） |
| n2_02_except_star_simple（负对照翻案） | failure 1/2 | **success 2/2 100%** |

产物逐句对照（n2_02）：`except* ValueError as e:` 类型保留（基线 `except* Exception as e:`）。

### 7.2 自测 2：B9 复现逐单元

| 复现 | 基线 | 终版 | 变化 |
|---|---|---|---|
| r2_08_handler_mixed_boolop | failure 1/3（f+g） | **success 3/3 100%** | 全封闭（g 的 `while a and b or c:` 装配；f 的 if-else 形极性/or 尾修复） |
| r2_09_finally_mixed_boolop | failure 2/3（g） | failure 2/3（g） | 读数未变、产物逐字节同基线（消费层残留，§4） |
| r2_10_trybody_mixed_boolop | failure 2/4（f_while+f_ternary） | failure 2/4 | 读数未变、症状改善：f_while `if not (a and b):`+孤儿`if c:` → `if a and b or c:`；f_ternary `if a and b:` → `if a and b or c:`（TernaryRegion 已建，生成端未消费，§4） |
| r2_17_trywrap_loop_mixed | failure 1/3（f+g） | failure 2/3（f） | **g 封闭**；f 双链条件全部恢复正确（含 `elif a or b and c:`），残留幻影 while False + 末尾 return 丢失（§4） |

### 7.3 自测 3：量力项（不修，读数与基线一致）

r2_04_try_nest3 failure 1/2、r2_06_loop_try_continue failure 2/3、
r2_14_finally_swallows failure 3/4 —— 均与基线逐字节同产物；根因假设与立项见 §5。

### 7.4 自测 4：B7 + 负对照 + MATCH 组 + round1 抽验

| 目标 | 读数 |
|---|---|
| rv_03 / rv_05 / rv_09（--source 法） | 各 failure 1/2（与基线持平） |
| n2_01_try_simple / n2_03_while_plain_try | 2/2、2/2 100% |
| r2_01_try_multi_handler / r2_02_try_finally_only / r2_03_try_four_part | 3/3、3/3、3/3 100% |
| r2_05_try_loop_try / r2_15_reraise / r2_16_handler_complex_type | 2/2、2/2、3/3 100% |
| r1_01_stmt_andor3 / r1_10_while_mixed / r1_21_comprehension_mixed | 2/2、2/2、3/3 100% |

### 7.5 自测 5：真身哨兵（--source 法，临时产物写系统临时目录）

| 目标 | 本批读数 | 基线 | 回退 |
|---|---|---|---|
| IQCommon/strategy/jq_trans_module.pyc | **65/65** | 65/65 | 0 |
| fly/data/quotation.pyc | **152/153** | 152/153 | 0 |
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | **118/128** | 118/128 | 0 |
| fly/data/quote.pyc | **84/92** | 84/92 | 0 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | **41/43** | 41/43 | 0 |
| IQCommon/util/email_utils.pyc | **3/4** | 3/4 | 0 |
| IQCommon/util/trade_info_utils.pyc | **36/41** | 36/41 | 0 |

### 7.6 自测 6：402 文件全量重生成 + 分片验证（零回退门禁）

round1 verify_driver 流程复用（输出写本轮临时目录，未触碰 round1 归档）：
402/402 重生成 0 失败 → 8 分片 batch → 与 baseline/shards 报告 compare：

- **REGRESSIONS=0**（8/8 分片）；units 6546 → 6554（+8，= round1 归档 +8 增益的
  完整保持：jq_trans_module 63→65 failure→success、trade_live_broker 115→118、
  quote 81→92 中 +3，逐单元比对仅此三文件读数变化且全部为 round1 已登记增益）；
- 文件级 success 369/402（与 round1 归档一致）。

## 8. 修改点清单（file + 方法 + 行号，当前树）

| 文件 | 方法/位置 | 行号 | 内容 |
|---|---|---|---|
| core/cfg/region_analyzer.py | `RegionAnalyzer._EXCEPT_STAR_FRAME_PREFIX`（新类常量） | :10131-10134 | except* 组匹配帧头签名 |
| core/cfg/region_analyzer.py | `_collect_pre_check_instrs` | :10135-10179 | B8：帧前缀剔除判据 + docstring 三要素 |
| core/cfg/region_analyzer.py | `RegionAnalyzer._EXC_FRAME_GUARD_OPS`（新类常量） | :1212-1221 | 异常帧指令守卫集 |
| core/cfg/region_analyzer.py | `_try_unify_mixed_boolop_chain` | :27511-27576 | B9：TryRegion 豁免（判据 A/C） |
| core/cfg/region_analyzer.py | `_detect_boolop_conditional_chain` | :25603（签名）+ :26625-26643 | B9：try_scope_exempt 参数与豁免（判据 B） |
| core/cfg/exception_handler.py | `_find_handler_type_load`（新方法） | :50-105 | R2-O2：结构判据定位类型 LOAD |
| core/cfg/exception_handler.py | CHECK_EG_MATCH 侧回退 | :199-204 | 白名单回退替换 |
| core/cfg/exception_handler.py | CHECK_EXC_MATCH 侧回退（+check_block 记录） | :213-241 | 白名单回退替换 |

产物更新（重生成，全部经 single 验证）：test_repros/round2/{n2_02, r2_08, r2_10,
r2_11, r2_12, r2_13, r2_17}OK.py。site-packages 402 产物重生成后与提交版本逐字节
一致（git status 零变化），本轮修复对其输出无影响、round1 增益完整保持。

## 9. 遗留与交接

1. B9 消费层残留（§4）：r2_09.g / r2_10.f_while / r2_10.f_ternary / r2_17.f，
   根因已定位到「异常区域包裹下循环/三元消费」与「assert 前驱吸收」三个面，
   机制锚点与立项建议已给出，交后续轮。
2. 量力项 r2_04/r2_06/r2_14（§5）：登记根因假设 + 立项建议，未修。
3. r2_07（match 模式降级）：Round 4 范围，维持登记。
4. B7（rv_03/05/09）：维持「已定位未修」，读数未变。
5. 本批零调试残留：临时插桩（B9DBG/IFDBG/TDBG 族）已全部移除
   （`grep -c "TDBG|IFDBG|B9DBG" core/` = 0）；pristine worktree 与临时目录已删除；
   两支回归探针中误生成的非索引产物（klinedataOKOK.py、两个历史 r2_ 文件的
   OK.py）已还原/删除，git 工作树仅含 §8 清单 + 本报告。
