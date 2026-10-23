# METHOD_REVIEW — Task 8.2 红队评审记录

> 评审对象：`rounds/round8/COMPLETENESS_METHOD.md` v1
> 评审方式：独立子代理只读评审（不写文件、不改代码），以 `spec.md` §100–142、Task 8、L0–L5 报告和 `BREACH_REGISTRY.md` 为依据。
> 评审日期：2026-10-23
> 首轮结论：**不通过（revise & re-review）**。
> 第二轮结论：**仍不通过**（见 §8）。
> 第三轮结论：**有条件通过**（见 §9）；2 项条件已修。
> 当前状态：Task 8.1–8.4 完成；`98e77821` + `3f43c965` 已 push，origin/main 已同步。

---

## §1 首轮结论

方法方向正确：双读数、五元组、执行级语义差分、规则证明义务、fuzz/canary 都对应了 L0–L5 的真实问题，可以保留。
但 v1 把「未定义、未实现、不可执行」的内容写成门槛，并用旧判据/旧探针读数充当新门槛现状，导致 G1–G6 既不可执行，也不能被一致证伪。因此不接受 v1，也不接受 v1 中预写的「有条件通过」。

---

## §2 阻断性意见（首轮）

| # | 严重度 | 反对意见 | 证据/影响 | v2 处置 |
|---|---|---|---|---|
| 1 | 阻断 | **G2 的语料分母没有输入模型**：要求全 J + 402 + small34 + quotation + tests 的 `DIFF=0`，但 402 是 402 个产物/6617 code object，tests 是基线名单，L4 只有 24 样例/56 探针；没有 `(entrypoint,input)` 时 `DIFF=0` 可能是 import 级或空真 | L4 §执行差分；`semantic_diff` 未实现 | 新增 `semantic_case` 与 G2a/G2b/G2c；`N/A` 单列，不得冒充绿；402 每个 artifact 至少 import case，可建模 code object 才进函数级 |
| 2 | 阻断 | **G2 把「判据绿」当「语义绿」**：同时引用 L4 `4/46=8.70%` 判据绿与 `14/56` 执行差异，两者不是同一读数 | L4 `ATTACK_L4_RUNTIME.md`；旧 `compare_pyc` 不执行 | `4/46`、`7/46`、`12/21` 移入「旧结构判据（历史）」；G2 只报 `EQUAL/DIFF/INCONCLUSIVE/N/A` |
| 3 | 阻断 | **G3 没有独立的新变异运行器**：拿 L2 `366/1311=27.92%` 当 G3 当前读数，但 L2 是对 `compare_pyc` 的结构变异，判据不执行程序（B-01） | L2 `ATTACK_L2_JUDGE.md`；B195–B201 | G3 改用 `semantic_diff` oracle；新增 `killed/survived/equivalent/invalid`、漏检率、误杀率；旧 27.92% 明确标为历史结构读数 |
| 4 | 阻断 | **G3 的等价变异体可缩小分母**：v1 只要求「证明/排除理由」，作者声明即可移出分母 | 无等价判定器/独立变异生成器 | `equivalent` 必须有机器可检证明；否则按 `survived` 计；`equivalent[]` 与证明公开；变异生成器独立于产品 |
| 5 | 阻断 | **G4 在 `total_rules=0` 时自动通过**：`proved_rules=total_rules` 在 0/0 时为真；`Cov(R_i)≠∅` 只要求一个条目 | 规则 manifest 未建立 | `total_rules>0`；`0/0` 记 `INCONCLUSIVE`；manifest 与代码锚点双向对账；`unmapped_anchors=0`、`orphan_rules=0` |
| 6 | 高 | **G4 覆盖引理过弱**：每条规则只要求一正一反例，不能证明域/守卫/组合完备 | O1–O7 只是抽象存在 | 增加 `semantic_domain` 在 `H×D` 的单元见证、每个 guard 调用点负例、O6 组合见证、proof 字段可复算 |
| 7 | 阻断 | **G1 检查器仍是 probe-only**：`coverage_checker.py` 仍以 `required_evidence[]` 中存在 probe 即 covered；无 `covered_5tuple/probe_only/inconclusive` | B170；旧 976/1556 | 五元组 C1–C5；输出 `J_total, covered_5tuple, probe_only, unexecuted, n/a, inconclusive, excluded, uncovered`；旧 976 不计入；检查器先用合成正反例自测 |
| 8 | 高 | **J 条目没有可机检的绑定字段**：现有 `judgment_space.json` 只有 `id/form/host/depth/variant/row/required_evidence/status/source`；缺 `P_j/I_j/expected_label/host_prelude/counterexample`；实际只装配 299/408 个 `(form,variant)` 槽、584 个 `(form,host,depth)` 单元 | L1 `JUDGMENT_SPACE.md`；评审核验 | J schema 增字段；生成 `excluded[]`；J 充分性独立审查；报告装配率与 excluded |
| 9 | 高 | **J v1 继承 128 口径缺口**：`arg/arguments` 等 7 个真实节点类型未独立检查；签名/docstring 仍在 R1–R5 之外 | L1 B164–B171；L2 docstring/形参盲区 | `arg/arguments`、签名、docstring 进入 J 或 R7；若排除必须给语言论证 |
| 10 | 高 | **真实项目维度没有进入 G1/G2 分母**：L4 只测 46 个真实 pyc；`except*` 真实语料 0；v1 的 F/H/D/V 没有真实项目维度 | spec §96–98；L4 B213 | 新增 G2c：46 个真实 pyc、8 类特性各 ≥1、`except*` 缺口显式保留；4/46、7/46、14/56 入报告 |
| 11 | 高 | **语义差分缺元数据/ABI/别名观测**：未比较 `__doc__`、`__annotations__`、`inspect.signature`、`__defaults__`、`co_*`、闭包、函数/类身份；R3 深拷贝看不出别名拓扑 | L2 docstring 108/108、形参换序 159/162、`x=1→x=True` 83/84 | 新增 R7；别名用身份图同构；丢失 docstring/注解/默认值/签名/装饰器顺序判 `DIFF` |
| 12 | 高 | **B/U 破口没有逐条映射到门槛**：v1 声称 B163–B219 对应，但没有 traceability 表；B171、U-02、U-06、B214–B219、B172–B175 未明确归属 | `BREACH_REGISTRY.md` §8 | 新增 §10.2 方法级映射；三元组/双归属/守卫闭包强制进 J/O1–O3；U-06 归 G6；B214–B219 归 P3/P4/P6 与报告模板 |
| 13 | 高 | **报告模板遗漏反向读数**：只列 128、976、27.92%、0/—，没有 4/46、14/56、0/402、405/3342/197、12/21、7/46；模板写「语义差分 —」却又声称 G2 要 DIFF=0 | §7 v1 | 模板加入 `N/A`、`INCONCLUSIVE`、`0/402`、`4/46`、`7/46`、`14/56`、`12/21`、`405/3342/197`；旧判据单列 |
| 14 | 阻断 | **§8 预写「有条件通过」，且引用不存在的文件**：`METHOD_REVIEW.md`、`roadmap.md` 在评审前不存在；Task 8.2/8.3 未满足 | v1 §8/§9 | 删除预写结论；本文件记录首轮不通过；新增 `roadmap.md`；复审前不标记完成 |
| 15 | 高 | **G6/Task 9 不可执行**：G6 只有文字；canary 无数量/持有者/轮换/泄漏检测；Task 9 没有 rule_manifest、fuzz/canary、独立审计子项 | v1 §5/§9 | G6 定为 24 条（3 类×8）、独立保管、季度轮换、泄漏扫描；roadmap 增 S4–S6；预算/owner/验收/回退写入 roadmap |

---

## §3 数值核验（首轮）

| 读数 | 核验结果 | 口径风险 |
|---|---|---|
| `128/128` | 算术正确 | 分母不是语言面：缺 7、多 32、重复 31；独立增量 0；只能称形态清单 |
| `J v1 = 1556` | 正确 | 39 形态族/48 宿主/3 深度/408 变体槽；实际装配 299/408 槽、584 单元；选择规则/excluded 未审计 |
| `976/1556 = 62.72%` | 正确 | 976 是 probe-only，不是五元组覆盖；不能作为 G1 分子 |
| `366/1311 = 27.92%` | 正确 | 旧结构判据复合读数（8 类 99/1031、补测 267/280、in-process 199/2046）；不是 G3 |
| `4/46 = 8.70%` | 正确 | `compare_pyc` 判据绿，不是语义差分绿；同批 7/46=15.22% 不可编译 |
| `14/56` | 正确 | 24 个样例、56 个探针、14 处差异、9 个样例；不能外推全 J/全 402 |
| `2765/3079 = 89.80%` | 正确 | 单元是 code object，不是语义正确率 |
| `402/402`、`6617/6617` | 正确 | 同一判据、同一批产物的 drift 复现；不构成独立语义验证 |
| `1568/1568`、`153/153` | 正确 | 回归读数，只能证明回归 |
| `0/402` 原始源 | 正确 | 397 缺失、5 个 0 字节；源级 oracle 缺失；`SourcelessFileLoader` 可执行 pyc，但不能替代源级检查 |
| `405 stamps/3342 记录/197 产物` | 正确 | 404 个不同 stamp 名；解析到产物 3275 条；16.96 条/产物，解析后 16.62；分母未统一（B219） |
| `12/21 = 57.1%` 判红假阳性 | 正确 | 「红」不等于语义错；报告必须列 |
| `10/32 形态为零`、`70/402 无函数`、`68/402 单单元`、`61.44% ≤3 形态` | 正确 | 语料/探针偏向小而浅；不能支撑完整覆盖 |
| `0/7 族通用`、B142/B143、6 例叠加塌陷 | 正确 | 机制层未达形态通用；三元组/守卫仍开放 |
| `3.12 模拟 96.24%` | 正确 | 3.12 不在 v1 范围；版本绑定和 deny-list 仍是风险 |

结论：算术基本一致；问题在分子/分母和观测对象，v2 已按此重写门槛。

---

## §4 四支柱判定（首轮）

| 支柱 | 首轮判定 | 阻断点 | v2 变化 |
|---|---|---|---|
| 判定空间 | 部分 | 检查器 probe-only；J 缺字段；976 旧口径；299/408、584 单元无 excluded 审计；`arg/arguments` 仍缺 | 五元组输出、J 字段、excluded 审计、形参/签名进 J/R7 |
| 判据升级 | 部分 | G2 的 402/tests 无输入模型；8.70% 是旧判据；缺元数据/ABI/别名/真实项目；`INCONCLUSIVE` 可被 N/A 规避 | G2a/b/c、`semantic_case`、R7、G2c 真实项目；N/A 单列 |
| 证明义务 | 不成立 | `total_rules=0` 空真；单正/单反例太弱；无实际规则对账；无独立变异 oracle；0 条规则完成 | `total_rules>0`、双向对账、域/守卫/组合见证、G3 独立 oracle |
| 持续证据 | 计划态，不可评 | 全部未来计划；canary 无规格；无预算/owner/审计；G6 无法评 | 24 canary、独立保管/轮换/泄漏扫描；roadmap S4–S6、预算/回退 |

---

## §5 G1–G6 首轮自查

| 门槛 | 首轮状态 | 首轮判定 | v2 当前 |
|---|---|---|---|
| G1 判定空间覆盖 | 1556 中 580 未覆盖；976 只是 probe-only；检查器未升级 | 未达成 | 不可评（检查器未实现） |
| G2 语义差分 | 无 `semantic_diff`；4/46 是旧判据；14/56 只有 24 样例；402/tests 无输入模型 | 未达成 | 未建立（G2a/b/c） |
| G3 变异测试 | 无新 `mutation_test`；27.92% 是旧结构读数；无等价清单/误杀 | 未达成 | 未建立 |
| G4 规则覆盖 | 无 manifest；0/0 可空真；Cov≠∅ 只证明触达 | 未达成 | 未建立；0/0 记 INCONCLUSIVE |
| G5 回归门禁 | 6617/6617、1568/1568、153/153 绿 | 满足，但仅回归 | 满足，但仅回归 |
| G6 金丝雀 | 只有文字；无 runner/数量/轮换/泄漏检测 | 未建立/不可评 | 规格已定，runner 未建立 |

---

## §6 v2 修订清单

1. 重写 G2 为 G2a（J）、G2b（402）、G2c（真实项目）；新增 `semantic_case`，`N/A`/`INCONCLUSIVE` 单列，禁止 import 级假绿。
2. 把 G1 改为五元组 C1–C5；输出 `covered_5tuple`/`probe_only`/`unexecuted`/`n/a`/`inconclusive`；旧 976 不计入；J 补机器字段与 `excluded[]`。
3. 重定义 G3：独立语义变异、`killed/survived/equivalent/invalid`、漏检率/误杀率；等价变异体须机器证明，否则计 survived。
4. 重定义 G4：`total_rules>0`、`unmapped_anchors=0`、`orphan_rules=0`；规则需域/守卫/组合见证；`0/0` 记 `INCONCLUSIVE`。
5. 新增 R7 元数据/ABI/别名观测；新增 G2c 真实项目维度与 `except*` 缺口。
6. 报告模板加入 `0/402`、`4/46`、`7/46`、`14/56`、`12/21`、`405/3342/197`、`N/A`、`INCONCLUSIVE`；旧判据单列。
7. 删除预写「有条件通过」；新增本评审记录与 `roadmap.md`；G6 定为 24 条 canary、独立保管、季度轮换、泄漏扫描。
8. 新增 §10.2 破口到门槛的方法级映射；逐条封闭仍在 v9 台账，Task 10 签收。

---

## §7 复审条件与剩余风险

复审必须确认：

- [ ] G1 检查器输出五元组字段，旧 976 不再计 covered；J 字段/excluded 可机检。
- [ ] G2a/b/c 的 `semantic_case` 定义能阻止 import 级空真；`N/A`/`INCONCLUSIVE` 均单列。
- [ ] G3 的 `equivalent` 有机器可检证明；`survived=0`/`false_kill=0` 可计算。
- [ ] G4 `total_rules>0`、双向对账、域/守卫/组合见证齐全；`0/0` 不可通过。
- [ ] R7 覆盖 docstring/annotations/signature/defaults/`co_*`/身份/装饰器顺序/别名图。
- [ ] 报告模板列出全部反向读数；双读数分列不互替。
- [ ] `roadmap.md` 有 S1–S6 的 owner、预算、命令、验收读数、回退条件；Task 9 承接 S4–S6。
- [ ] 破口映射表覆盖 B163–B219 + U-01–U-06 的方法级归属。

剩余风险：

- J 的 299/408 槽、584 单元是否足以支撑「判定空间」仍需独立充分性审查；
- G2b 的 `N/A=0` 可能难以达成；若最终不可达，只能永久保留「J 门槛达标」，不得改口径；
- `proved` 仍是工程证明，不是定理证明；任何对外文本必须保留这一限定；
- 24 条 canary 仍可能被过拟合；轮换与泄漏扫描不能替代独立审计。

**复审通过前，Task 8 保持未完成状态。**

---

## §8 第二轮复审（v2）

第二轮独立复审结论：**不通过（revise & re-review）**。v2 已实质修复首轮多数文本问题，但仍有 3 组阻断：Task 9 未承接 S4–S6、G4 对账仍可自证、G2 输入无效时仍可能假绿；另有 G3 分母/等价证明不可计算、口径术语/R7 规范化/报告模板残余。

第二轮阻断与 v3 处置：

| # | 严重度 | 第二轮问题 | v3 处置 |
|---|---|---|---|
| N1 | 阻断 | `tasks.md` Task 9 只有 9.1–9.5，未承接 S4 `rule_manifest`、S5 fuzz/canary、S6 gate/双读数/审计；S4 依赖只写 S1 | Task 9 扩为 9.1–9.7：9.3 五元组检查器、9.4 独立规则全集、9.5 fuzz/canary、9.6 G1–G6 门禁/双读数/审计；roadmap S4 依赖改为 S1+S2 |
| N2 | 阻断 | G4 的 `total_rules` 与锚点全集都由 manifest canonical 正则定义，可自证；1/1 也能通过 | 新增独立规则全集枚举器 `rule_universe`；`total_rules=|rule_universe|`；manifest 只做映射；独立枚举失败记 `INCONCLUSIVE` |
| N3 | 阻断 | G2 的 `arg_model` 未绑定签名；双方都抛 `TypeError` 仍可 `EQUAL`；G2b 的「可建模」无定义 | `semantic_case` 增 `signature_binding` + `body_reached`；绑定失败记 `ERROR/N/A`；`modeled` 必须签名成功 + 到达目标体 + 无 harness 异常；G2b `N/A>0` 不通过 |
| N4 | 高 | G3 的 `accepted/false_kill/equivalent` 无公式/证明格式；`invalid` 未入报告；校准集不等于总体 | 新增 §3.7 变异总体与公式；`accepted = M_total - invalid`；`equivalent` 证明 schema；报告单列 `invalid`；生成器独立 |
| N5 | 高 | 术语「完备（J v1）」与「全部门槛」冲突；G2b N/A>0 可能被称完备；R7 裸比 `co_*` 会误判；模板缺反向读数 | 统一为「J 门槛达标」/「语料完备」/「完备（仅指语料完备）」；G2b 要求 `N/A=0`；R7 增 `co_*` 白名单；模板加 `ERROR/invalid/excluded_slots/空间不变式` |

v3 当前状态：上述 5 项已改；**待第三轮复审**。第三轮通过前，Task 8 仍不得标记完成，`rr-v4r08` 不得提交。

---

## §9 第三轮复审（v3）

第三轮独立复审结论：**有条件通过**。5 项核验结果：

| 项 | 结果 | 证据 |
|---|---|---|
| Task 9 承接 S4–S6 | 关闭 | `tasks.md` 9.1–9.7；`roadmap.md` S4 依赖 S1+S2、Task 9 映射表 |
| G4 独立 `rule_universe` | 关闭 | 方法 §4.1/§6；roadmap S4 交付/验收/回退 |
| G2 签名绑定/到达目标体 | 关闭 | 方法 §3.1/§3.3/§6 |
| G3 公式/等价证明 | 部分关闭，需修边界 | `false_kill` 与 `killed` 的互斥关系未写明；`accepted` 公式可能重复扣减 |
| 术语/R7/模板 | 部分关闭 | roadmap 仍写「J 完备」；方法 §7 仍写「J 完备」；roadmap 头部仍写 v2 |

必须修正的 2 项及处置：

1. 术语统一：`roadmap.md` 的「J 完备」改为「J 门槛达标」；方法 §7 的「J 完备」改为「J 门槛达标」；roadmap 头部 v2 → v3。**已修**。
2. G3 集合划分：明确 `killed` 不含 `false_kill`；采用 `N = killed + survived`、`accepted = killed + survived + E`、`E = false_kill + true_neg`。**已修**；roadmap 同步。

第三轮残余建议（不阻断）：

- Task 9.2 增加 `invalid/M_total` 上限（roadmap 已定 >30% 记 `INCONCLUSIVE`）；
- `body_reached` 建议原/产物双侧 `hits>=1`（方法已写 `body_reached.hits>=1`，实现时需双侧验证）。

**签收状态**：Task 8.1–8.4 完成（方法、评审记录、路线图齐备；`98e77821` + `3f43c965` 已 push）。两轮「不通过」与第三轮「有条件通过」全部留档，未删除失败记录。
