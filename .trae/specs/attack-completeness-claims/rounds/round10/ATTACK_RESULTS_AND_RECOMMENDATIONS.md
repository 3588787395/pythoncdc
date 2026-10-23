# 攻击结果与完备方法建议（v9 终态）

> 结论：v9 攻击已经击穿“v8 100% = 完备”的旧口径；L6 方法已交付，但没有通过自身门禁。当前唯一诚实的正向表述仍是：
>
> **形态基线达成（v8 口径，128/128）；判定空间、语义差分、变异、规则覆盖与独立金丝雀未达标，完备未成立。**
>
> 本文件只回答两件事：攻击结果是什么，完备方法下一步应该怎么改；不新增完成声明。

## 1. 攻击结果

### 1.1 分层结论

| 层 | 结论 | 关键读数 | 证据 |
|---|---|---|---|
| L0 理论 | **击穿**：C1 字段公式与实现不一致；归纳步不闭合；区域唯一归属有反例 | 22 个 tie 块；三元组合探针击穿二元投影；B172–B176 | `rounds/round2/ATTACK_L0_THEORY.md` |
| L1 口径 | **击穿**：128 不是互斥语言划分；变体维度被折叠 | 97 节点集漏 7 类；279 声明变体仅触发 118（42.3%）；24/25 行有缺口 | `rounds/round3/ATTACK_L1_MEASURE.md` |
| L2 判据 | **击穿**：`pyc_verify` 不执行，值/注解/docstring/参数槽差异不可见 | 变异漏检 **366/1311 = 27.92%**；`x=1→x=True` **83/84 = 98.81%**；函数 docstring **108/108**；参数重排 **159/162** | `rounds/round4/ATTACK_L2_JUDGE.md` |
| L3 机制 | **击穿**：0/7 机制族形态通用；守卫族叠加冲突；B142 为形态级缺口 | 6 个叠加探针崩溃；H1–H11；B142 升格、B143 归约级 | `rounds/round5/ATTACK_L3_MECHANISM.md` |
| L4 运行时 | **击穿**：语料外真实 pyc 判据绿率低；语义差异可执行；规模超线性 | 46 真实 pyc：判据绿 **4/46 = 8.70%**，不可编译 **7/46 = 15.22%**，单元 **2765/3079 = 89.80%**；执行差分 **14/56**；4000 语句约 89.84s | `rounds/round6/ATTACK_L4_RUNTIME.md` |
| L5 证据 | **击穿**：402 语料没有可用原始源；6617/6617 是判据自洽，不是语义真值 | 原始源 **0/402**；405 stamps / 3342 records / **197** 唯一产物；10/32 形态零覆盖；61.44% ≤3 形态；402/14237 = 2.82% | `rounds/round7/ATTACK_L5_EVIDENCE.md` |
| L6 方法 | **已交付、未通过**：四支柱 + 可伪证门槛 + 路线图；工具已落地 | 方法、评审、路线图；`semantic_diff`、mutation、J、rule manifest、fuzz、canary、gate 工具 | `rounds/round8/COMPLETENESS_METHOD.md`、`METHOD_REVIEW.md`、`roadmap.md` |

### 1.2 门禁终态

| 门禁 | 读数 | 状态 |
|---|---|---|
| G1 判定空间覆盖 | 全量 **0/1556**；样本 **51/1556 = 3.28%** | FAIL |
| G2a 样本语义差分 | **45 EQUAL / 6 DIFFERENT / 0 ERROR** | FAIL |
| G2b 402 语义差分 | 未运行 | UNESTABLISHED |
| G2c 46 真实 pyc 语义差分 | 未运行 | UNESTABLISHED |
| G3 变异测试 | 仅 1/1 smoke | UNESTABLISHED |
| G4 规则覆盖 | **339 rules / 339 manifest / 0 proved / 339 open** | INCONCLUSIVE |
| G5 语料回归 | 6617/6617、1568/1568、153/153 | PASS，但仅历史基线，未重跑 |
| G6 独立 canary | **20/24 EQUAL**，0 leak，本地 bootstrap | FAIL |
| 总门禁 | — | **BLOCKED** |

### 1.3 本次补充发现

#### A. 六条 J R7 不是 docstring 问题

样本 `45 EQUAL / 6 DIFFERENT` 的 6 条 R7 需要拆开：

| id | 源/pyc | R7 位置 | 实际归属 |
|---|---|---|---|
| `JS-IF-017` | `v_b71_face.py` / `.pyc` | `$.metadata.code.co_consts.v[2].code_sha` | **B142** |
| `JS-IF-021` | 同上 | 同上 | **B142** |
| `JS-IF-088` | 同上 | 同上 | **B142** |
| `JS-IF-090` | 同上 | 同上 | **B142** |
| `JS-IF-097` | 同上 | 同上 | **B142** |
| `JS-IF-076` | `test_repros/round2/x01_if_deep_hosts.py` / `.pyc` | 5 个 `co_consts` code_sha / consts_len | x01 结构差；不是 B142 |

- 前 5 条的 R7 是 `v_nest_fin_continue` 的 **code object** 差异，不是模块 `__doc__ = ...`。此前 `BREACH_TRIAGE.md` 中“module docstring / metadata only”的归属是错误的。
- 对 `v_nest_fin_continue` 加真实调用后，B142 是**可执行语义差**，不是仅元数据差：
  - `v_nest_fin_continue([[0, 1]])`：原产物返回长度 5，产品返回 7；元素 `2/1` 顺序错位。
  - `v_nest_fin_continue([[1, 2]])`：原产物返回长度 6，产品返回 4。
  - 这些 R1 差异在 module-only 调用下完全不可见，只有 R7 的 `code_sha` 暴露了问题。
- `JS-IF-076` 的 5 个 R7 差异为：
  - `co_consts[2].code_sha` 变化、`consts_len` 2→4（`if_in_while`）；
  - `co_consts[3].code_sha` 变化、`consts_len` 4→5（`if_in_try`）；
  - `co_consts[6].code_sha` 变化（`if_shallow`）。
  - 产品把 `if_in_while` 的 `break` 丢掉，变成 `while True: R = 1`；`if_in_try` / `if_shallow` 也发生结构变化，但 module-level R1–R6 仍相等。
- 因此：**R7 的 code object 差异必须视为阻断信号，不能按“metadata only”忽略。** 之前“likely B199/B202”的判断至少对 5/6 条不成立。

#### B. C4 覆盖缺陷：runner 没有消费 `input_model.calls`

`tools/completeness/semantic_runner.py` 当前固定：

- `entrypoint = "module"`；
- `args = []`；
- 不读取 `entry.input_model.calls`。

`JS-IF-076` 证明这会漏掉函数体缺陷：module import 成功，R1–R6 全相等，只有 R7 看到 code object 差异。J 空间中大量 `input_model` 是 `{"kind": "module", "calls": []}`，本质上仍是 module-only 模型。

这是**判定空间的方法缺陷**，不是单个产品的缺陷。

#### C. B142 的机制候选

对 `v_nest_fin_continue` 的区域快照：

- 内层 `TryExceptRegion`：`try_blocks=[18]`，`finally_blocks=[164, 210]`，`finally_copy_blocks=[]`。
- 外层 `TryExceptRegion`：`try_blocks=[30, 32, 74, 118, 120]`，`finally_blocks=[262, 308]`，`finally_copy_blocks=[74, 216]`。

问题链：

1. 内层 finally 的正常路径副本在 32 和 120；异常副本在 164/210。
2. 副本检测只检查 try 块的**直接后继**；18 的直接后继是 30/118/164，32/120 在 NOP 链后面，因此内层 `finally_copy_blocks` 为空。
3. 外层 try 把 30/32/74/118/120 全部收进 `try_blocks`；74 同时被标为外层副本，形成“同一块既像 try 体又像 finally 副本”的自相矛盾。
4. 生成层因此把内层 finally 正常副本当 try 体发射，造成 `append(1)` 双发、`continue` 丢失、finally 层级错位。

候选修复方向（与 B142 登记一致）：**finally 副本谱系标注 + 属地继承**，而不是按形态打补丁。最低判据应包括：

- 以 finally 异常副本的 `PUSH_EXC_INFO..RERAISE` 体指令序列（opname + argval）为签名；
- 沿透明块链（NOP/单后继）找到正常路径副本，而不是只看直接后继；
- 副本归属内层 region，外层不得再把副本块计入 `try_blocks`；
- continue/break 回边目标同时校验“循环 header 同一性 + finally 域成员关系”。

#### D. J 空间容量

J v2 当前：

- 总条目 **1556**；
- 同时有有效 source + pyc **1168**；
- 缺 source **388**；
- 缺 pyc **12**（PEP604 条目的子集）。

因此 G1 的“0/1556”不是单纯“没跑”，还包括 **388 条无法从 source 侧执行**的结构性缺口。全量 G1 之前必须先解决 source 恢复/生成与 12 条 pyc 缺失。

#### E. 其他仍然成立的结论

- B163–B219：**57 个编号，0 个正式关闭**。
- 四个 fuzz 发现仍未修：`FZ-raresyntax-015`、`FZ-semantictrap-020`、`FZ-raresyntax-021`、`FZ-semantictrap-023`。
- `B200` 在 `rounds/round3/BREACH_REGISTRY.md` 中的行仍是截断的，必须先修复台账。
- G6 在当前单代理、同机 bootstrap 下不可能满足“独立 custody”；即使 24/24 也只能记为 local canary，不能写 G6 PASS。

## 2. 对完备方法的建议

### 2.1 判定空间：把“可调用性”变成一维

现有 J 的维度是形态 × 宿主 × 深度 × 变体，但 `input_model` 大量退化为 module-only。建议增加第五维：

| 维度 | 要求 |
|---|---|
| 形态 | 文法族/节点/扩展形态 |
| 宿主 | 循环、try、with、match、async、class/module 等 |
| 深度 | ≥3 级宿主嵌套 |
| 变体 | 语义变体槽（值、作用域、异常、装饰器、docstring 等） |
| **可调用性** | 每个条目至少一个函数/类入口调用；module-only 只能算“导入证据”，不能算语义覆盖 |

每个 J 条目应显式带 `input_model.calls`。没有 calls 的条目，其 C4 状态应为 `INCONCLUSIVE`，而不是 `covered_5tuple`。

### 2.2 判据：R7 必须阻断，执行必须真的发生

建议把语义差分判据改成下面这条硬规则：

1. `semantic_runner` 必须把 `input_model.calls` 传给 `semantic_diff`；没有 calls 时自动为每个公开函数生成最小调用，或显式标 `INCONCLUSIVE`。
2. 任何 `R7` 的 `co_code` / `co_consts` / `co_exceptiontable` 差异，默认判 `DIFFERENT`；只有经过书面 tolerance 的字段才能忽略。
3. 超时不是 EQUAL，也不是 DIFFERENT，而是 `INCONCLUSIVE`；超时不得计入覆盖。
4. module-only 运行不得再产出 `covered_5tuple`。
5. 变异测试先用“已知错产物”校准：`1` vs `True`、删语句、反转极性、参数重排、docstring 删除都必须被抓；否则 G3 不成立。

这条规则会直接把当前的 `JS-IF-076` 从“metadata only”改成阻断项，也会让 B142 从“R7 元数据差”升级为“R1 语义差”。

### 2.3 证明义务：339 条规则要有 witness

G4 目前是 `339 rules / 0 proved / 339 open`，说明规则清单已有，但**没有可机检的证明义务**。建议每条规则至少绑定：

- 规则 id 与源码锚点；
- 触发该规则的 CFG 片段/witness；
- 规则前后不变式（至少一条可断言性质）；
- 覆盖引理：该规则覆盖的形态集合；
- 一条“规则不命中时行为不变”的负对照。

没有 witness 的规则不能从 `open` 变为 `proved`；G4 的 0 未覆盖必须由 trace 生成，而不是人工勾选。

### 2.4 持续证据：fuzz、canary、回归

- 四个 fuzz 发现先做 dedup 与最小化，再决定是否新增 B 编号；不要重复登记同一机制。
- G6 若无法获得独立 custody/rotation，应明确降级为“local canary”，不写 PASS；独立第三方 custody 是 G6 的必要条件。
- G5 必须在本轮树上重跑 402 八分片、small34、quotation、pytest、IV.2；历史 6617/6617 只能作基线。
- 每次改 `core/cfg/**` 后都要重跑 G5；没有 G5 的 core 改动不能进入“完成”结论。

### 2.5 产品修复优先级

| 优先级 | 项目 | 理由 |
|---|---|---|
| P0 | **B142** `v_nest_fin_continue` | 已有 call probe 证明 R1 语义差；影响 5 条 J R7 |
| P0 | **B200** registry 截断 | 台账不完整会污染所有 closure 判定 |
| P0 | `semantic_runner` calls + R7 阻断 | 不改这个，后续所有 G2a 读数都不可信 |
| P1 | `JS-IF-076` x01 结构差 | `if_in_while` 丢 `break`；R7 是唯一信号 |
| P1 | 四个 fuzz 发现（B203/B207/B210/B197+B202） | 已有最小复现，需 I.4 机制与合成探针 |
| P1 | module docstring / B199/B202 | 独立保真问题；**不能解释六条 R7**，不要混为一谈 |
| P2 | 388 缺 source、12 缺 pyc | G1 全量的前置条件 |
| P2 | G2b/G2c/G3/G4 全量 | 需要长跑与独立证据 |
| P3 | G6 独立 custody | 单代理环境不可满足，需外部托管 |

### 2.6 验收口径

“完备”只能在以下条件同时成立时使用：

- G1：判定空间 0 未覆盖（含可调用性维度）；
- G2a/G2b/G2c：语义差分 0 未裁决失败；
- G3：变异 0 漏检；
- G4：规则 0 open，且有 witness/trace；
- G5：本轮树上的语料回归全绿；
- G6：独立 custody 的 canary 全绿且 0 leak。

否则只能写：

> **形态基线达成（v8 口径）；判定空间/语义差分/变异/规则覆盖/独立金丝雀未达标，完备未成立。**

## 3. 一句话建议

先把**测量**修对（calls + R7 阻断 + B200 台账），再修**产品**（B142 副本谱系 + x01 结构差 + 四个 fuzz），最后才谈**全量门禁**（388 source / 12 pyc / G2b–G4 / G5 重跑 / G6 独立 custody）。顺序反了，得到的只会是更精致的假绿。
