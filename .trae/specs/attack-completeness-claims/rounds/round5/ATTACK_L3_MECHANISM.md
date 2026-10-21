# ATTACK_L3_MECHANISM — L3 机制层攻击（通用性抽检 + 叠加攻击 + 稀窝性质判定）

> 规范：`.trae/specs/attack-completeness-claims/`（Task 5，L3 层）
> 被攻击对象：`core/cfg/**` 内已落地的 **191 处 `[Bn-V3Rn]` 标记**（7 族 / 54 个破口号，见 `baseline/markers.md`）、R5–R8 守卫族、存留稀窝 **B142 / B143**
> 取证方式：只读代码 + **21 个探针 / 71 单元实跑**（`rounds/round5/probes/`，`rounds/round5/logs/l3_probes_l3final.json`）+ **执行级语义差分**（`tools/l3_semdiff.py` + `tools/l3_semdiff_sweep.py`，`logs/l3_semdiff_sweep.json`）+ 6 个机检脚本（`rounds/round5/tools/`）
> 纪律：本文件**不改** `core/cfg/**`、`tests/**`、`wiki/**`、`rules.md`、前一规范目录；未 push。
> 结论口径：**击穿** / **未击穿且不可证伪** / **不可证伪**（`spec.md:52-58` 反确认偏误纪律）
> 编号裁决：本轮新破口 **B179–B194**，与 `rounds/round3/BREACH_REGISTRY.md`（B163–B178）连续、不复用。
> **本轮修订记录**（相对本文件初稿）：初稿据 `l3_o4` 声称「判定器判绿但源码语义差」，经执行级差分复核**该断言不成立**（`o4` 两侧返回值与 `__enter__/__exit__` 次数**完全相等**），已按 §4(d)/§6-H5 更正；真正的判绿语义差实例是 `o4b`（**函数级 code object 判 Equal**，失败只落在嵌套 `<listcomp>` 上，见 AT-37 / B194）。

复现命令（均 ≤300s）：

```powershell
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_marker_scan.py
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_marker_scopes.py
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_probe_driver.py `
  --dir .trae\specs\attack-completeness-claims\rounds\round5\probes `
  --log .trae\specs\attack-completeness-claims\rounds\round5\logs --stamp l3final
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_semdiff_sweep.py
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_summary.py
# 单探针复核
python -X utf8 pycdc.py .trae\specs\attack-completeness-claims\rounds\round5\probes\l3_g5b_r6_handler_continue_matrix.pyc -o <base>OK.py
python -X utf8 scripts\pyc_verify.py single .trae\specs\attack-completeness-claims\rounds\round5\probes\l3_g5b_r6_handler_continue_matrix.pyc --source <base>OK.py
# 执行级差分复核（同一输入序列比对源与产物的返回值 + with 配对次数）
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_semdiff.py l3_o6_overlay_match_in_with_after o6
```

---

## §0 结论摘要

> 攻击项编号约定：`AT-3N`（本轮 N=1..7）。

| id | 攻击命题（一句话） | 结论 | 一句话理由 |
|---|---|---|---|
| **AT-31** | 已落地机制的触发谓词对**同族任意形态**可迁移（通用） | **击穿** | 7 族抽检中 **5 族（R2/R4/R6/R7/R8）在非语料新构型上结构错误**：R2 把 `while` 降级为 `if`、R4 丢 `out.append(v)`、R6 丢 handler 内 `continue`、R7 丢切片 step、R8 把 finally 体的副作用执行 3 次；仅 R3/R5 的抽检构型未击穿。 |
| **AT-32** | 守卫族叠加时是否存在**优先级冲突 / 抢块** | **击穿** | 5 个叠加构造全部出现语义损坏；且定位到**块级抢归属**（B152 与 B150 争夺同一 `region.merge_block`，B150 不查 `generated_blocks`）与**注入伪语句**（match case 体在 with 内被注入伪 `continue`；该注入在 `o4` 构型下**语义惰性**、执行级 EQUAL）。另新增叠加形态：with 在 for 内时 **match 之后的同体语句被整条丢弃**（B193）。 |
| **AT-33** | **B142** 是形态级缺口还是归约级缺口 | **形态级缺口（i）** | 产物**未能产出该构型的 AST 形态**：`Continue`（内层 try 体）被整条丢弃，且两级 finally 体**互换 + 重复** ⇒ 形态基线分子须扣；且同一根因在**单层** try/finally 亦复现 ⇒ 「稀窝」定性被证伪。 |
| **AT-34** | **B143** 是形态级缺口还是归约级缺口 | **归约级缺口（ii）** | 原件形态下产物**仍产出 `ast.Try` + `ast.If` + `ast.Break` + `ast.While` 全套形态**，错的只是 finalbody 内**子区域派发顺序**（break 被降为 `if i == 1: pass` + 臂外 break）⇒ 不掩盖任何形态级能力缺口 ⇒ 形态级分子不减；但其「稀窝」定性被 5 形态枚举证伪（4/5 红）。 |
| **AT-35** | 标记数口径（174 / 123 / 191）可收敛 | **击穿**（口径层，定性登记为 B192，扩充 B178） | 本轮独立复算确认 **191 = 123 + 24 + 44**（纯数字紧邻 `]` / 字母后缀破口号 / 带后缀文字形式）；台账 174 = 191 − 17（R5 少计）；且 191/123 均为**注释出现次数**，去重到「承载函数 × 破口号」的**机制点**读数仅 **139**（承载函数 109）⇒ 标记数不得作为机制面规模度量。 |
| **AT-36** | 守卫族触发集是否封闭、是否有状态泄漏 | **击穿** | B140 判据④绑定「**前向**跳转 + 循环出口」⇒ handler 内 `continue`（回向）不命中；补偿路径依赖 `block_role` 标注，而该标注「看不到被 TryExceptRegion 吸收的 handler 体块」（`region_analyzer.py:36338-36340` 自述）⇒ {while × 前置语句} 格整条丢 `continue`。另 B70g 的 `_b70a_in_filter` 为生成器实例状态且无复位路径（状态泄漏面）。 |
| **AT-37** | 「判定器判绿 ⇒ 语义等价」这条推断链是否成立 | **击穿（1 例）** | 新增执行级差分（`tools/l3_semdiff.py`，同输入序列比对返回值 + `__enter__/__exit__` 次数 + 异常类型）：**48 单元**中 23 单元执行级 DIFFERENT；其中 **1 单元「判定器在该函数 code object 上判 Equal、执行语义却不同」**（`l3_o4_overlay_matchguard_with_comp::o4b`：失败只落在嵌套 `<listcomp>` code object 上，函数级单元判绿）⇒ 判据盲区成立且**首次被本轮实测定位到具体单元**。同时发现 **8 单元「判红但执行级 EQUAL」**（判据在给定输入上过敏感或差异落在未覆盖维度）。 |

**总判**：v8 的「174 处标记 / 25 行全绿 ⇒ 完备」在**机制层**被击穿——已落地机制的触发谓词**大面积形态特化**（不是「同族任意形态可迁移」），叠加时还会**互相抢块 / 注入伪语句**；B142 与 B143 的性质**不同**（B142 形态级、B143 归约级），前者的「稀窝」定性被本轮单层复现证伪，后者虽仍是归约级但其**影响面**远大于「单一残余单元」；且「绿 ⇒ 对」的推断链在**单元粒度**上首次被实测击穿（AT-37）。

---

## §1 攻击项清单

| id | 攻击命题 | 方法 | 击穿判据 | 不可证伪判据 | 结论 | 证据 |
|---|---|---|---|---|---|---|
| AT-31 | 落地机制的触发谓词可迁移到同族任意形态 | 每族 ≥1 个**非语料新构型**探针（源+pyc+产品+判据四件套），逐条对照**源码语义**读产品 + 执行级差分 | 产品相对源码**结构性错误**（丢语句 / 改宿主 / 改极性 / 改槽位），非仅格式差异 | 抽样 1 点无法证明同族全体 ⇒ 需「形态级证明义务」（Task 8 支柱 3） | **击穿** | `probes/l3_g1,l3_g3,l3_g5b,l3_g5c,l3_g6,l3_g7c,l3_g7d` 等 **21 探针 / 71 单元**；`logs/l3_probes_l3final.json`、`logs/l3_semdiff_sweep.json` |
| AT-32 | 守卫族叠加是否产生优先级冲突 | 6 个叠加构造（a–e、d'），每个单函数内含 ≥3 族机制 | 两族守卫同时命中同一块/同一语句，或产物相对源码语义差 | 叠加组合空间无界 ⇒ 需生成式叠加器 + 覆盖引理 | **击穿** | `probes/l3_o1…l3_o6`；`region_ast_generator.py:18053-18068` vs `:27096-27116` |
| AT-33 | B142（嵌套 finally 副本归属）性质 | 逐字复刻 `v_b71_face::v_nest_fin_continue` + 同族兄弟形 + **单层可观测化变体** + 执行级差分 | 产品**产不出**该构型的 AST 形态（Continue 被丢弃 / finally 体互换重复）⇒ 形态级能力缺口 | 产物形态齐全、仅槽位错 ⇒ 归约级 | **形态级缺口 (i)** | `probes/l3_b142_nested_finally_copy.py` + `l3_g7c_r8_finally_sideeffect_return.py` + `l3_g7d_r8_finally_sideeffect_observable.py` |
| AT-34 | B143（finally 内 break 的 finalbody 子区域派发）性质 | 原件逐字复刻 + 5 形态枚举（宿主/臂位置/双臂） | 产物产不出「if 臂内 break」这一形态 ⇒ 形态级 | 形态齐全、仅派发顺序错 ⇒ 归约级 | **归约级缺口 (ii)** | `probes/l3_b143b_break_in_finally_shapes.py`（原件 `test_repros/round6/r6_synth_b140_nested_break.py:15`） |
| AT-35 | 标记数口径可收敛 | 3 套正则独立复算 + 「承载函数 × 破口号」去重 | 存在一个可复算口径使 174/123/191 三者同时成立 | 口径本身是**度量选择**问题 ⇒ 方法层（计数规则须随判据声明） | **击穿** | `tools/l3_marker_scan.py` / `l3_marker_scopes.py`；`logs/l3_markers.json`、`l3_marker_rows.json` |
| AT-36 | 守卫族触发集封闭性 + 状态泄漏 | 逐守卫读 docstring 声明面 vs 代码实际判据；跨守卫对拍 | 守卫触发集是语法触发集的真子集/真超集且无声明 | 需「守卫触发集完备性」机检（覆盖检查器升级为规则级） | **击穿** | `region_analyzer.py:36342-36357`；`region_ast_generator.py:16721-16725`、`:36203+` |
| AT-37 | 「判绿 ⇒ 语义等价」推断链 | 执行级差分：同一输入序列下分别执行源与产物，比对返回值 / `with` 配对次数 / 异常类型 | 存在单元：判定器在该 code object 判 Equal，而执行语义不同 | 需 Task 9 的 `semantic_diff.py` 全量差分（本轮为迷你原型） | **击穿（1 例：`o4b`）** | `tools/l3_semdiff.py`、`tools/l3_semdiff_sweep.py`；`logs/l3_semdiff_sweep.json` |

---

## §2 机制族清单与抽检

### 2.1 计数口径（显式声明，可复算）

| 口径 | 规则 | 实测 | 逐族（R2/R3/R4/R5/R6/R7/R8） |
|---|---|---|---|
| **A（宽）** | 正则 `\[B\d+[A-Za-z]*-V3R\d+`，按**出现次数**计（允许字母后缀破口号） | **191** | 47 / 25 / 13 / 51 / 12 / 21 / 22 |
| **B（严）** | 正则 `\[B\d+-V3R\d+\]`：纯数字破口号 **且紧邻 `]`** | **123** | 25 / 22 / 13 / 9 / 12 / 20 / 22 |
| **C（本轮新增）** | **机制点** = 「承载该标记的最内层 `def`/`class` 作用域 × 破口号」去重 | **139**（承载函数 **109** 个） | 34 / 19 / 10 / 32 / 10 / 17 / 17 |
| 台账 | — | 声称 **174** | 47 / 25 / 13 / **34** / 12 / 21 / 22 |

**191 的精确分解（本轮独立复算）**：`191 = 123（纯数字破口号且紧邻 ']'） + 24（字母后缀破口号 B61a–B61k / B70c–B70j） + 44（纯数字破口号但带后缀文字，如 `[B98-V3R2 修复]`）`。
**台账 174 的算术重建**：174 = 191 − 17，差 17 **全在 R5**（台账 34 vs 实测 51）；R5 自报 27（`attain-true-completeness/rounds/round5/FIX.md:159`）= 51 − 24（未计 B61a–B61k），台账 34 = 27 + 7（B122 的 7 处被二次计入）。
⇒ 与 `baseline/markers.md` §5 自洽：**174 不可复现**（B178 已登记，本轮以 B192 补充「分解式 + 机制点读数」）。
⇒ **新增口径层结论**：A/B 两口径计的都是**注释标记的出现次数**，不是「落地机制数」（同一机制可被多处注释标注；一个破口号可跨文件重复）。**标记数不得作为机制面规模度量**，机制面规模应读口径 C（139 机制点 / 109 承载函数）。

### 2.2 逐族：触发谓词与通用性分级

通用性分级：**(i) 形态通用** = 谓词只读「结构事实」（opcode/跳转极性/区域成员），与具体形态无关；**(ii) 部分特化** = 谓词含位置/宿主绑定；**(iii) 形态特化** = 谓词绑定某一具体形状。

| 族 | 标记 A/B/C | 触发谓词（读法：谓词原文位置） | 通用性级 | 抽检点（file:line） | 抽检结论（证据） |
|---|---|---|---|---|---|
| **R2 条件合并** | 47/25/34 | B98：BoolOp 值链「keep-or-pop / 边界跳转」分组（`merge_ctx ∈ {store,compare,return,…}`）+ or/and 前缀过滤与合并块归约（`region_ast_generator.py:45244`、`:50576`、`:50729`）；B123：and **尾** IfExp 钻石（test/then/else 三块）吸收（`:8900`、`:45010`）；B78：嵌套三元宿主折叠（真值出口直连宿主，`:55011`） | **(iii)** | `region_ast_generator.py:45244`（B98 keep-or-pop 分组）、`:8900`（B123 钻石三块） | **击穿**：`l3_g1`：`while (xs[i] if flag else -xs[i]) or (…)` 的 `while` 宿主被降级为 `if`、循环体 `out.append(xs[i])` 丢失、`else: return out` 被凭空造出；`(a or b) and (c if a else (b or c))` → `(a or b) and a`（三元真值臂被换成裸变量赋值）。谓词绑定「链尾是 IfExp」与「merge_ctx ∈ 有限枚举」 |
| **R3 try/raise/assert/host** | 25/22/19 | B135：IfRegion → `ast.Assert`（**if 臂退化为 assert 形态**，`region_ast_generator.py:16571`）；B134：循环体外前驱条件须在循环体内逐迭代重检（`:7380`、`:30174`）；B131：外部前驱条件采纳门（**底部闩锁存在性**，`:7748`、`:14238`）；B73/B82：finally 条件段副本头中继（`:37537`、`:40114`） | **(ii)** | `region_ast_generator.py:16571`（B135）、`:7748`（B131） | **未击穿（本次抽检构型）**：`l3_g2` 的 try-else 内 `assert`、handler 内 `raise … from None` 均**逐字正确**（判据 3/3 绿，产品与源码一致）。但 B135/B131/B134 的谓词分别绑定「if 臂退化」「底部闩锁」「循环体外前驱」三处**具体位置**，故只能定为 (ii)：**抽样绿不构成通用性证明**（AT-07 同族） |
| **R4 await 挂起链** | 13/13/10 | B112：**上一显著操作码**（跳过 PRECALL/CACHE 等编译器填充）供 CALL(0) 区分同步 GET_ITER / async GET_AITER（`ast_generator_v2.py:47`、`:273`、`:1368`）；B47：三元**臂值**表达式经 await 挂起链合并重建臂值（`region_ast_generator.py:49588`）；B128：只读判定「await setup 块的挂起结果是否由 IfRegion 条件消费」（`:11623`、`:65086`） | **(iii)** | `region_ast_generator.py:49588`（B47 臂值）、`:11623`（B128 setup 消费方） | **击穿**：`l3_g3`：`for x in xs: v = await res.get(x); out.append(v)` 的 **`out.append(v)` 整条丢失**（判据报 "Different bytecode"）；`async with` 体内 `try/finally` 的 finally 体被**移出 finally**（`finally: pass` + flush 落到 try 之后 ⇒ 异常路径不再 flush）。B47/B128 均绑定「await 位于三元臂 / IfRegion 条件位」 |
| **R5 match/with 幻影** | 51/9/32 | B61a–B61k + B122：模式材料隔离 / or 守卫臂链结构签名 / 入口同块去重 / `**rest` 与类模式双 COPY（`pattern_parser.py:132`、`:974`、`:2197`；`region_analyzer.py:17689`–`:19048`）；B70：循环归属与出口分类（**WithRegion 优先级 > LoopRegion**，`:9832`–`:9850`、`region_ast_generator.py:16686` B70g、`:40544` B70f/i、`:41076` B70j）；B93：with 跨体祖先判定（`:41529`） | **(ii)** | `pattern_parser.py:132`（B61e 种子后继筛选）、`region_ast_generator.py:16686`（B70g with 体内 if 清理块过滤补口） | **未击穿（模式解析部分）**：`l3_g4` 的 `{"k": [a, *rest]} if a > 0`、`[x, *ys] if x`、`{"a": p, **rest}` 三种新模式**逐字正确**（判据 3/3 绿）。**但 with 宿主交互击穿**：`l3_o4` 显示 match 的 case 体在 with 内被注入**伪 `continue`**（见 §4/§6 H5）。B70/B61 的谓词绑定「case 体块集」「with 成员」「区域优先级」等具体结构 |
| **R6 循环控制** | 12/12/10 | B140：except handler 体内 **break** 五合取（区域成员 + 异常边 + **无条件前向跳转** + 目标为循环出口块 + 无 RETURN）（`region_analyzer.py:36334-36401`，出口块集合 `:36403-36426`）；B139：旋转 while 的 else 体（**condition-false 目标**）且「含实际语句就不是纯尾返回」（`:6671`、`:6794`）；B138：回边块同时是带 else 的 IfRegion.merge_block 时不得并入 then 体（`region_ast_generator.py:16544`）；B137：while True 体首 NOP 占位（`:14070`） | **(iii)** | `region_analyzer.py:36342-36357`（B140 五合取）、`:6671`（B139） | **击穿**：`l3_g5b` 的 2×2 矩阵中 **1 格红**：`while` 宿主 + handler 内 `continue` 前有语句 ⇒ `continue` 整条丢失（handler 的 `i += 1` 后落到 `out.append(xs[i]); i += 1`，源语义应回跳循环头）。B140 判据④绑定「**前向**跳转 + 循环出口」，continue 是**回向** ⇒ 必然不命中 |
| **R7 赋值/删除/return/slice** | 21/20/17 | B145：break **落点**（`LoopRegion.break_blocks` 成员关系，`:62066-62091`）+ del 归约 `ast.Delete`（`:63322-63347`，「跳转必须离开所属循环」收窄）；B148：值折叠算子族纳入「**复合前缀**」判据（opcode 白名单，`:56193-56220`）；B150：「双臂 return + 单一共享 RETURN_VALUE 汇点」折叠为三元（`:27076-27140`）；B151：推导式过滤链**链式比较之后**的续解析（`comprehension_generator.py:2479-2570`）；B152：「if 条件是三元」形态（`region_ast_generator.py:18016-18070`） | **(iii)** | `region_ast_generator.py:62066`（B145）、`:56193`（B148 白名单）、`comprehension_generator.py:2479`（B151） | **击穿**：`l3_g6`：`del d[x if x else 0::2]` → `del d[x if x else 0]`（**step 丢失**；实测字节码为 `BUILD_SLICE 3`，而三元-切片路径按**二元**建模，见 `region_ast_generator.py:56199`「BUILD_SLICE 的两个界」与 `:60622`「BUILD_SLICE 2」）；`d[x if x else 0::2] += k` → `(d[…] + k)[…] = d`（语义完全改写） |
| **R8 终审** | 22/22/17 | B155：臂尾（POP_EXCEPT 之后）以**回边跳转**终结的块 = 显式 break/continue（`region_analyzer.py:13147-13160`、`:13105-13147`）；B156：handler arm tail「内联 finally 副本 + 回边跳转」= 源码级显式 break/continue（`region_ast_generator.py:36162-36202`）；B157：finally 归属唯一化（**保护跨度最小且包含它**，`:10400-10470`）；B158/B159/B160/B162：try 体边界、链尾判据（`:14327`、`:14421`、`:28633`、`:30594`） | **(iii)** | `region_analyzer.py:10409-10411`（B157 布局序假设）、`:13159`（B155）、`region_ast_generator.py:36195`（B156） | **击穿**：`l3_g7c`：`finally` 体同时含**副作用 + return** 时，finally 体被复制进 **try 体与 handler 体** ⇒ `out.append('fin')` 每个元素执行 **3 次**（源语义 1 次）；`l3_b143b`：finally 内 break 在 5 形态中 4 形态红（break 被降为 `if i == 1: pass` + 臂外 break + 死 continue）。B157 的唯一归属依赖「内层 finally 副本在布局中更早」这一**布局序断言**（非推导） |

**逐族小结**：7 族中 **0 族达 (i) 形态通用**；**(ii) 部分特化 2 族**（R3、R5）；**(iii) 形态特化 5 族**（R2、R4、R6、R7、R8）——其中 R3/R5 的抽检构型未击穿，但谓词含位置绑定，**抽样绿不构成通用性证明**。

---

## §3 通用性抽检实验（核心）

方法：构造**同族、非语料、新形状**的构型 → `py_compile` → `pycdc.py -o` → `pyc_verify.py single` → **逐条读产品对照源码语义**（判据绿 ≠ 对；判据只比字节码/CFG，见 `baseline/judge_criteria.md` §3 B-01）→ **执行级差分**（`tools/l3_semdiff.py`：同一输入序列下分别执行源与产物，比对返回值、`with` 的 `__enter__/__exit__` 次数、异常类型）。
**击穿判据**：产品相对源码**结构性错误**（丢语句 / 改宿主 / 改极性 / 改槽位 / 改副作用次数），非格式差异。

| # | 族 | 新构型（非语料） | 源码语义（要点） | 实际产物（摘录） | 判定 | 执行级差分 |
|---|---|---|---|---|---|---|
| 1 | R2 | `while (xs[i] if flag else -xs[i]) or (xs[i] > 0 and xs[i] < 9):`（BoolOp **左**操作数为三元 + while 宿主）；`v = (a or b) and (c if a else (b or c))` | while 循环；`or` 短路；`and` 链尾三元取真值臂 | `if (xs[i] if flag else -xs[i]):`（**while 变 if**）；`out.append(xs[i])` **丢失**；`else: return out` **凭空造出**；`v = (a or b) and a`（三元真值臂被换成裸 `a`）+ 多出 `v = b or c` | **击穿**（结构错误） | **DIFFERENT**（`r2_lt`：源/产 `out` 不同；`r2_nested_and_or`：a=False 时源=True 产=False） |
| 2 | R3 | `try: … except ValueError: … else: assert x >= 0, "neg"; out.append(x)`；handler 内 `raise ValueError("bad") from None` | try-else 体只在无异常时执行；`raise from` 保留异常链 | 逐字正确：`else: assert x >= 0, 'neg'`；`raise ValueError('bad') from None` | **未击穿**（本次构型）；族级仍为 (ii)（见 §2.2） | **EQUAL** |
| 3 | R4 | `async with res as r: try: out.append(await r.read()) finally: out.append(await r.flush())`；`for x in xs: v = await res.get(x); out.append(v)` | finally 内的 flush 在**异常路径也执行**；`out.append(v)` 必执行 | `finally: pass` + `out.append(await r.flush())` **落到 try 之后**（异常路径不再 flush）；`v = await res.get(x)` 之后 **`out.append(v)` 整条消失** | **击穿** | `r4_await_in_for` **DIFFERENT**（源 `out=['G3',…]` 产 `out=[]`）；`r4_asyncwith` **EQUAL**（finally 体移位在该输入下不可观测 ⇒ 该格由产物文本判据成立，执行级为「未观测到差异」） |
| 4 | R5 | `case {"k": [a, *rest]} if a > 0:`；`case [x, *ys] if x:`；`case {"a": p, **rest}:` | mapping+sequence(star)+guard 的捕获与守卫 | 逐字正确（3/3 绿，含 `**rest` 与 `*star`） | **未击穿**（模式解析部分）；但 with 宿主交互在 §4 (d) 击穿 | **EQUAL** |
| 5 | R6 | handler 内 **continue**（同族兄弟形，B140 只覆盖 break）：2×2 矩阵 {for, while} × {裸 continue, continue 前有语句} | handler 内 continue ⇒ 回跳循环头，**不执行**其后的 `out.append` | {for×裸}=对、{for×带语句}=对、{while×裸}=对、**{while×带语句}=错**：`except ValueError: i += 1` 后直接落到 `out.append(xs[i]); i += 1` ⇒ **continue 整条丢失** | **击穿**（1/4 格红 ⇒ 触发集未封闭） | 矩阵：3 格 EQUAL、{while×带语句} **DIFFERENT**（`l3_g5c` 可观测化版本：源返回 `[3,-1]`，产物 **IndexError**） |
| 6 | R7 | `del d[x if x else 0::2]`；`d[x if x else 0::2] += k` | 删/改**步长为 2** 的切片序列 | `del d[x if x else 0]`（**step 丢失**）；`(d[x if x else 0::2] + k)[x if x else 0::2] = d`（**语义完全改写**为下标赋值） | **击穿** | **DIFFERENT** ×2 |
| 7 | R8 | `try: if x: return "body"; raise ValueError(x) except ValueError: return "handler" finally: out.append("fin"); if x < 0: return "finally"` | finally 体每元素**恰好执行一次**（含异常路径）；finally 内的 return 吞掉 try/handler 的 return | finally 体被复制进 **try 体**与 **handler 体** ⇒ `out.append('fin')` 每元素执行 **3 次** | **击穿** | `l3_g7c` 该格 **EQUAL**（局部 `out` 不可观测 ⇒ 只能读产物文本）；**`l3_g7d`（返回该列表本身）DIFFERENT**：源 `['body','fin']` 产 `['body','fin','body','fin','body','fin']` ⇒ **3 次执行已被执行级证实** |
| 8 | R8（嵌套） | `try: try: out.append(x) finally: out.append("inner-fin") except ValueError: out.append(-1) finally: out.append("outer-fin")` | 两级 finally 各一次；handler 体存在 | 内层 try/finally 塌陷；**`except ValueError: out.append(-1)` 整条丢失**；`out.append("outer-fin")` 被移出 finally | **击穿** | `r8_fin_sideeffect_nested` EQUAL（不可观测） |
| 9 | R8（B142 族） | `try: try: if r == 0: continue finally: out.append(1) finally: out.append(2)` | 两级 finally 体各一次；`continue` 回跳 | `continue` **丢失**；内层 finally 体被**复制两次**；**内外 finally 体互换**（内层位置是 `out.append(2)`、外层位置是 `out.append(1)`） | **击穿**（B142 复现） | **DIFFERENT**（`v_nest_fin_continue` 与 `v_nest_fin_continue_cond` 均 DIFFERENT） |
| 10 | R5×with 叠加 | `for v in vals: with res as r: match v: case int() if v>0: out.append(v) …; out.append("after")` | match 之后的 `out.append("after")` 每轮必执行 | **match 之后的 `out.append("after")` / `out.append("tail")` / `out.append(r)` 三条语句整条消失** | **击穿**（新构型，见 §4(d') 与 B193） | **DIFFERENT**（源 `[3,'after',-1,'after',5,'after']` 产 `[3,-1,5]`；`__enter__/__exit__` 次数两侧相同 ⇒ 是**语句丢失**而非配对次数变化） |

> 探针全量读数：**21 探针 / 71 单元 / 39 通过 / 32 单元失败**（`logs/l3_probes_l3final.json`）；执行级差分读数：**48 单元 / 31 判红 / 23 执行级 DIFFERENT / 1 判绿语义差**（`logs/l3_semdiff_sweep.json`）。

---

## §4 叠加攻击（overlay）

原则：**不重复 Task 2 的三元嵌套探针**（`l0_a1…l0_a4`）；本节做**组合/叠加与优先级**维度。

| # | 叠加构型 | 源码语义 | 产物是否保持语义 | 是否存在**守卫族优先级冲突** | 证据 |
|---|---|---|---|---|---|
| a | **if×for×try×match×with×async 同函数、深度 ≥3**（`async with` > `for` > `if` > `try` > `with` > `match`） | 两个 case 体的 `out.append(await r.get(x))` / `out.append(await r.get(-x))`、`out.append(sr)`、try 的 `else: out.append(x)` 全部必执行 | **否** | **是**：产物把 case 体整块塌成 `pass`（**await 链与 case 体语句全丢**），并**凭空注入 `else: continue`**；`async with` 宿主只保住骨架 | `probes/l3_o1_overlay_six.py`（2/3 单元红，`o1`/`o1b`） |
| b | **BoolOp + 三元 + await 同一条件式** | `if (await res.ready()) and (x if flag else await res.other()): return 1` ⇒ 真值成立即返回 1 | **否** | **是**：三元真值臂 `x` 被降为 `if x: pass`（**值被丢弃**）；`await res.other()` 被挂到 `elif` 分支 ⇒ 「flag 为真且 x 为真」时**不再返回 1**（条件极性被反转） | `probes/l3_o2_overlay_boolop_ternary_await.py`（2/2 单元红） |
| c | **loop-else + break + finally + handler** | for 的 `else` **仅在无 break 时执行** | **否**（`o3c`） | **是**：`o3`（break 在 try 之后）对；但 `o3c`（break 在 **handler 内**）⇒ for-else 被降级为**循环后的顺序语句** ⇒ handler 内 break 时 `else` 体**仍被执行** ⇒ B144/B145 的「break 落点独占可达」在 handler-break 叠加下失效 | `probes/l3_o3_overlay_loopelse_break_finally.py`（3/4，`o3c` 红） |
| d | **match guard + with + 推导式** | 推导式过滤 `(x > 1) and (x if x < 5 else -x)` 两合取项都要生效；with 的 `__enter__/__exit__` 整循环一次 | **否** | **是**（两处）：① **B151 的续解析**丢合取项 ⇒ 过滤退化为 `if (x if x < 5 else -x)`（`x > 1` 整条消失）；② match case 体在 with 内被**注入伪 `continue`** | `probes/l3_o4_overlay_matchguard_with_comp.py`（判据 4/5 绿，失败落在 `o4b.<listcomp>`） |
| d' | **match × with（with 在 for 内）** | match 之后的真实语句每轮必执行；`__enter__/__exit__` 每轮一次 | **否** | **是（新增形态）**：match **之后**的 `out.append("after")` / `out.append("tail")` / `out.append(r)` **三条语句整条消失**（非跳过、是被丢弃）；`__enter__/__exit__` 次数两侧相同 ⇒ 属**语句丢失**而非配对次数变化 | `probes/l3_o6_overlay_match_in_with_after.py`（2/2 单元红；执行级：源 `[3,'after',-1,'after',5,'after']` 产 `[3,-1,5]`）⇒ 登记 B193 |
| e | **augassign + delete + slice + return 同一表达式上下文** | `total += len(d[x if x else 0::2])` 求的是**切片长度**；`del d[::2]` 必执行 | **否** | **是**：`total += x if x else 0`（**`len(...)` 被替换成三元**）；`o5b` 的 `del d[n if n else 0::2]` **整条丢失** ⇒ B148/B149/B150 的「复合前缀 / 尾对剥离 / 双臂 return 折叠」在叠加下互相抢前缀 | `probes/l3_o5_overlay_augassign_del_slice.py`（1/3，两单元红） |

**叠加层结论**：5 个叠加构型**全部**出现语义损坏；**没有任何一个叠加构造表现为「一族守卫正确地先赢」**——表现全部是「某族的守卫命中后，另一族的材料被吞掉或被凭空注入」，即**块级抢归属**而非「可解释的优先级裁决」；另新增一种叠加形态（with 在 for 内的 match）：**match 之后的同体语句被整条丢弃**（B193）。

**关于「判定器判绿但源码语义差」——本轮更正（AT-37）**：

- **初稿的 `o4` 断言不成立**：经执行级差分复核，`l3_o4::o4` 两侧**返回值与 `__enter__/__exit__` 次数完全相等**（源 `[2,<ctx>]` 产 `[2,<ctx>]`，配对 `enter/exit` 各 1）⇒ 该构型下注入的 `continue` 位于 case 体末尾、其后 for 体已无语句 ⇒ **语义惰性**，**不能**作为「判绿且语义差」的证据。初稿的「`__exit__` 由 1 次变每轮 1 次」亦被证伪（该探针的 `with` 在 `for` **之外**）。
- **真正的判绿语义差实例是 `o4b`**：判定器在该**函数 code object** 上判 **Equal**（失败只落在嵌套 `<listcomp>` code object 上，见 `probes/l3_o4_overlay_matchguard_with_comp.judge.txt:3`），而执行级差分为 **DIFFERENT**（源 `[2,<ctx>]` 产 `[1,2,<ctx>]` ⇒ `x > 1` 合取项丢失）⇒ **单元粒度**上「绿 ⇒ 对」不成立 ⇒ B194。
- **8 单元「判红但执行级 EQUAL」**（`r4_asyncwith`、`b143_c`、`o2`、`o3c`、`o5b`、`r8_fin_sideeffect_return`、`r8_fin_sideeffect_return_raise`、`r8_fin_sideeffect_nested`）⇒ 判据在这些输入上**过敏感**，或差异落在未观测维度（异常消息 / 未走到的分支）⇒ 需 Task 4/6 的差分 fuzz 给出「红 ⇒ 真差」与「红 ⇒ 假差」的分离读数。

---

## §5 B142 / B143 性质判定（必需项）

### 5.0 判定标准（本轮显式声明，供复核）

- **(i) 形态级缺口**：受影响构型所属的**形态**（判定空间条目族）在产物中**未被产出**（形态缺失、宿主被改写成另一形态、或该形态的语句被整条丢弃）⇒ 该形态不得计入完备分子。
- **(ii) 归约级缺口**：产物的**形态齐全、宿主正确**，错的只是**槽位归属 / 派发顺序 / 子区域切分** ⇒ 不掩盖任何形态级能力缺口，形态级分子不减；但仍须作为必修的归约缺陷处置。

### 5.1 B142（嵌套 finally 副本归属）—— **判定：形态级缺口 (i)**

| 项 | 内容 |
|---|---|
| 最小复现 | `probes/l3_b142_nested_finally_copy.py::v_nest_fin_continue`（逐字复刻 `adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.py:19`） |
| 源码语义 | 内层 try 体 `if r == 0: continue` ⇒ 内层 finally `out.append(1)` 一次 + 外层 finally `out.append(2)` 一次，然后回跳循环头；`r != 0` ⇒ 两级 finally 各一次 + `out.append(r)`。⇒ **`out.append(1)` 与 `out.append(2)` 每元素各恰好一次** |
| 实际产物 | `if r == 0:` 之后**没有 continue**，而是 `try: out.append(1); out.append(1) finally: out.append(2)`，外层 `finally: out.append(1)`；末尾 `out.append(r)` |
| 差异 | ① **`Continue` 形态被整条丢弃**（该形态在此宿主下未被产出）；② 内层 finally 体被**重复两次**；③ **内外 finally 体互换**（内层槽位是 `out.append(2)`、外层槽位是 `out.append(1)`）⇒ 源 `r≠0` 时应得 `[2, r]`，产物得 `[1, r]` |
| 判为 (i) 的理由 | ① **形态缺失**：`Continue` × try 体 × 带 finally 这一宿主变体，产物**根本不产出** ⇒ 形态基线分子必须扣（Round 2 §7 已判「park 前提被推翻」，本轮给出形态级定性）；② 判据④只验「产物形态齐全、仅槽位错」——本例**不成立**（Continue 缺失 + finally 体重复/互换 ⇒ 槽位错已到「同一语句被复制」的量级，属**归属集合**错误而非顺序错误）；③ **范围被证伪**：同一根因在**单层** try/finally 上也复现（`l3_g7c`/`l3_g7d`：finally 体含控制转移时，finally 体被复制进 try 体与 handler 体 ⇒ 副作用执行 **3 次**），故 B142 不是「嵌套 finally 的稀窝」，而是 **B174（finally 副本同时计入 try 体 → 副作用重复）的单层实例**，范围远超登记时假设；④ **执行级证实**：`l3_semdiff` 在 `v_nest_fin_continue` / `v_nest_fin_continue_cond` 上判 **DIFFERENT**（源/产 `out` 序列不同）⇒ 非仅文本层差异 |
| 什么会改变该分类 | 若修复只需**重排 finalbody/副本的归属顺序**（不涉及形态新增/删除）而产物形态保持齐全，则应改判 (ii)；反之若证明 `Continue` 在 try 体宿主下**无法**被还原（如 `continue` 与 `finally` 的组合在 CPython 3.11 字节码上不可区分），则**更应**判 (i) 并升为形态级必修。**本轮判 (i)** 的决定性证据是产物中 `continue` 的**缺席**（`probes/l3_b142_nested_finally_copyOK.py` 全文无 `continue`） |
| 处置建议 | 由「稀窝登记、不升格」改为：**形态级破口**（计入完备分子扣减）+ 必修（修复须覆盖「正常路径 finally 副本归属」与「finally 副本 ↔ finally 体槽位」两处，见 B187） |

### 5.2 B143（finally 体内 break 的 finalbody 子区域派发）—— **判定：归约级缺口 (ii)**

| 项 | 内容 |
|---|---|
| 最小复现 | `probes/l3_b143b_break_in_finally_shapes.py::b143_b_orig_nested`（逐字复刻 `test_repros/round6/r6_synth_b140_nested_break.py:15` 的 `s_b140_break_in_finally_loop`） |
| 源码语义 | `for i: while i > 0: i -= 1; try: out.append(i) finally: if i == 1: break` ⇒ **仅当 i == 1** 时跳出**内层 while**（不是外层 for） |
| 实际产物 | `finally:` 体 = `if i == 1: pass` + `break`（**在 if 臂外**）+ `continue`（死语句）⇒ **无条件 break** ⇒ 跳出内层 while 的条件被改成「总是」 |
| 差异 | break 的**落点条件**被改写（i==1 ⇒ 恒真）；另注入死 `continue`。与 B143 登记根因逐字吻合（`attain-true-completeness/rounds/round6/FIX.md:93`：「break 未落在 if 臂内（`if i == 1: pass` + 臂外 break/continue）」） |
| 判为 (ii) 的理由 | ① **形态齐全**：产物仍产出 `ast.Try`（含 finalbody）+ `ast.If` + `ast.Break` + `ast.While`（`while i > 0:` 宿主**未被改写**）⇒ **没有任何形态级能力缺口被掩盖**；② 错的只是 **finalbody 内子区域的派发顺序**（「装配按 entry 身份派发」而非「线性发射」，同登记根因）；③ **同族正确形态存在**：`b143_a_for_finally_ifarm`（单层 for + if 臂内 break）**逐字正确、判据绿、执行级 EQUAL** ⇒ 该能力确实存在且已被行使；④ 登记根因本身就是**装配/归约**问题，不涉及新增 AST 形态 ⇒ 按 §5.0 标准即 (ii)；⑤ **执行级复核**：`b143_b`/`b143_d`/`b143_e` 执行级 **DIFFERENT**（源 `[0,1,2,1,3,2,1]` 产 `[0,1,2,3]`）⇒ 差异是**可观测的语义差**，但仍属**槽位/派发**层（`if i == 1: pass` + 臂外 break ⇒ 条件被改成恒真），**不是**「形态产不出来」 ⇒ 不改变 (ii) 定性 |
| 什么会改变该分类 | 若证明「finalbody 内的 if 臂 + break」在 CPython 3.11 字节码上与「finalbody 级 break」**不可区分**（即 CPython 不保留该信息），则应改判 (i)（形态级：无法还原）；反之若修复仅需重排派发顺序（当前证据支持），维持 (ii)。**注意**：形态枚举显示 5 形态中 **4 形态红**（`b143_c` 臂外 break ⇒ **`while i > 0:` 宿主被改写成 `if i > 0:` 且 break 丢失**；`b143_d` ⇒ `while i > 0:` 被改写成 `while True:` + `if/else`，break 被降为 `pass` + 臂外 `continue`；`b143_e` ⇒ 同 `b143_b`），其中 `b143_c`/`b143_d` 的**宿主改写**属 Round 2 已登记的 B172（while 宿主丢失）而非 B143 本身 ⇒ 已在 B188 中一并登记 |
| 处置建议 | 维持「归约级缺口」定性（形态级分子不减），但**「稀窝」定性被证伪**（4/5 形态红 + 1 形态宿主改写）⇒ 须由「park 不追」升为**必修的归约级缺陷**（finalbody 按 entry 身份派发） |

---

## §6 守卫族相互作用（R5–R8 落地守卫）

对象：B70g / B139 / B140 / B145 / B148 / B150 / B151 / B152 / B153–B162。

| # | 相互作用 | 证据（file:line） | 探针证据 | 危害 |
|---|---|---|---|---|
| **H1** | **B140（handler break）与其兄弟形 handler continue 的触发集不对称**：B140 判据④要求「以无条件**前向**跳转结束，且目标为该循环的**出口**块」；handler continue 编译为 `POP_EXCEPT + JUMP_BACKWARD(循环头)` ⇒ 必然不命中。补偿路径（`region_ast_generator.py:36203+` 的 "Pattern TE"）依赖 `block_role ∈ {CONTINUE, PURE_CONTINUE}`，而该角色由 `_annotate_loop_structural_roles` 标注、**看不到被 TryExceptRegion 吸收的 handler 体块**（B140 docstring 自述 `region_analyzer.py:36338-36340`） | `region_analyzer.py:36342-36357`（五合取）、`:36338-36340`（角色看不到 handler 块）；`region_ast_generator.py:36203-36210` | `l3_g5b` 2×2：**1/4 格红**（{while × 前置语句}）；`l3_g5` `r6_handler_continue_while` 红 | **触发集未封闭**于 {break, continue} × {for, while} × {裸/带前置语句}；R6 落地声明「handler break/continue（while + for）」（`attain-true-completeness/rounds/round6/FIX.md:90`）**overstated**：仓内实际只覆盖 while×break（`r6_synth_b140_handler_break.py:1`）与 for×continue（同文件 `:22`） |
| **H2** | **B152 与 B150 争夺同一 `region.merge_block`**：B152 在「单 elif + 三元」分支把 `elif_ft`（= `region.merge_block`）当作 **if 体**并登记为 generated；B150 稍后在 `_if_generate_normal` 出口把「末指令为 RETURN_VALUE/RETURN_CONST 且 ∉ region.blocks 的 merge_block」当作**双臂共享返回汇点**，折叠为 `Return(IfExp)` 并**再次**登记同一块为 generated。B150 **不检查 `merge_block ∈ self.generated_blocks`** | `region_ast_generator.py:18053-18068`（B152，判据 (a)(c)；「把 `elif_ft`(=merge_block) 登记为 generated」@`:18061-18062`）、`:27076-27084`（B150 标记与函数入口）、`:27146-27167`（B150 判据 (b)(d)；「命中时把 merge_block 登记为 generated」@`:27166-27167`，**不检查 `merge ∈ generated_blocks`**） | 静态可判；叠加构型 (b) 中「三元真值臂被降为 `if x: pass`」与该双守卫争夺同源 | **每块唯一归属（原则 2）被破坏**；裁决**依赖调用序**而非声明的优先级 ⇒ 顺序依赖型隐患 |
| **H3** | **B152 判据 (c) 过弱 ⇒ 与 B70g / B145 触发集重叠**：`P ∉ region.else_blocks` 被当作「P 是 if 之后的兄弟语句」的**充分**条件，但 P 实际可能是 **with 清理块**（B70g 的 `_filter_if_blocks_in_with` 正为此存在）、**循环出口块**或 **finally 副本** ⇒ B152 会把 B70g/B145 的管辖块登记为 generated（不再独立重放） | `region_ast_generator.py:18066-18068`（B152 (c)）、`:16686-16730`（B70g）、`:62066-62091`（B145） | 叠加 (d)：match case 体在 with 内被注入伪 `continue`（B70g 的清理块过滤补口与 match 体归属在同函数内交叠） | **重叠触发集 + 一族守卫抢走另一族的材料**；B152 的谓词是**必要非充分**条件 |
| **H4** | **B70g 的宿主收窄读全层级区域表，且过滤标志是实例状态**：`for _b70a_wr in self.regions`（**全层级**，非本层）；`_b70a_in_filter` 是生成器实例属性，仅用于递归短路，**未见 finally/except 复位路径** | `region_ast_generator.py:16709-16719`（全层级遍历）、`:16721-16725`（实例状态写入）、`:16694`（递归短路说明） | 叠加 (a)/(d)：with 宿主内的 match case 体与 if 体同时在场 | **状态泄漏面**（跨区域残留）+ 宿主判据不读本层 ⇒ 依赖阶段序（与 Round 2 AT-08 同族） |
| **H5** | **match case 体 × with 清理链 ⇒ 注入伪 `continue`**：产物在 `case [a, b] if a < b:` 体内注入源码不存在的 `continue`；该 `continue` 位于 `with` 块内 | `region_ast_generator.py:16686-16698`（B70g 的占位体替换契约）、`:40390`/`:41693`（B70c 占位体甄别）、`:40544-40555`（B70f 出口分类） | `l3_o4::o4`：注入成立，但**执行级 EQUAL**（该构型下 `continue` 位于 case 体末尾、其后 for 体无语句 ⇒ 语义惰性） | **注入伪语句**（不是抢占，而是凭空注入）⇒ 判据盲区（**本轮实测：该注入本身在 `o4` 上未造成语义差**；真正的语义差见 H11） |
| **H11** | **match × with（with 在 for 内）⇒ match 之后的同体语句被整条丢弃**：`out.append("after")` / `out.append("tail")` / `out.append(r)` 三条语句在产物中**消失**（既非改写、也非跳过执行）；`__enter__/__exit__` 配对次数两侧相同 ⇒ 是**语句丢失**而非清理链次数变化 | B70g 的 with 体内清理块过滤（`region_ast_generator.py:16686-16730`）与 B61k 的 match 宿主归属（case 体块集判定）叠加面 | `l3_o6::o6` / `o6b`：2/2 单元红；执行级 **DIFFERENT**（源 `[3,'after',-1,'after',5,'after']` 产 `[3,-1,5]`） | **新叠加形态缺口** ⇒ B193 |
| **H6** | **B148 的「复合前缀」判据是 opcode 白名单，且 BUILD_SLICE 按二元建模**：`_has_compound` 覆盖 BINARY_OP/BINARY_SUBSCR/COMPARE_OP/IS_OP/CONTAINS_OP/FORMAT_VALUE/`BUILD_*`/`UNARY_*`，但**不含 BUILD_SLICE 的元数**；三元-切片路径按**二元**切片建模（「BUILD_SLICE 的两个界各自成为独立 preload 项」、「BUILD_SLICE 2」） | `region_ast_generator.py:56211-56220`（白名单）、`:56199-56203`（「两个界」）、`:60622`/`:60741`（「BUILD_SLICE 2」） | `l3_g6`：实测字节码为 `BUILD_SLICE 3`（`tools/l3_dis.py` dump）⇒ step 丢失 | **形态特化（3 元切片未建模）**；R7 族的最强单点证据 |
| **H7** | **B151 的触发前提是「链式比较」**：判据 (c) 要求反扫子序列可被 `expr_reconstructor` 归约，且**只在链式比较分支被调用** ⇒ 过滤项为「比较 **AND** 三元」时不在 B151 的适用面，比较项被整条丢弃 | `comprehension_generator.py:2489-2490`（调用面）、`:2499-2502`（判据 c）、`:2506-2507`（不命中即逐位沿用旧结果） | `l3_o4::o4b.<listcomp>`：`if (x > 1) and (x if x < 5 else -x)` → `if (x if x < 5 else -x)` | **触发前提（链式比较）不覆盖 BoolOp 组的 and 合取项** ⇒ 续解析族不完备 |
| **H8** | **B145 读全层级区域表而 docstring 自称「只读本层区域列表」**：`:62086` 遍历 `self.region_analyzer.regions`（全部层级），`:62079` 写「只读本层区域列表」⇒ 外层循环的 break 落点若落在内层循环体内会被误判为「落点」（不补发 break） | `region_ast_generator.py:62077-62091` | Round 2 AT-06 #4 已记录该不一致；本轮未另造新例 | **与 B140 / B156 的 handler-tail break/continue 发射路径重叠**（谁先认领该块无声明） |
| **H9** | **B157 的唯一归属依赖「内层 finally 副本在布局中更早」这一布局序断言**（非推导）；B157 只治理「except handler ↔ finally」的归属，**未治理「finally 副本 ↔ finally 体」的归属** | `region_analyzer.py:10400-10411`（断言 + 排序键）、`:10465-10469`（唯一归属） | `l3_b142`：产物**内外 finally 体互换** ⇒ 正是「副本 ↔ finally 体」归属未被治理的表征 | **B142 与 B157 的交互空洞**：B157 修了相邻类问题却未覆盖 B142 的实际根因 ⇒ 「B142 已被 R8 机制间接封闭」的印象不成立 |
| **H10** | **B139（旋转 while 的 else 体）与 B138（回边块是带 else 的 IfRegion.merge）都以 while 的 condition/exit 结构为判据输入**，在 `while` 与 `if` 互为 condition-merge 时存在**同一块被两守卫以不同身份认领**的面 | `region_analyzer.py:6671`/`:6794`（B139）、`region_ast_generator.py:16544`（B138） | Round 2 AT-03 机检 22 处平局块（`logs/l0_partition.json`）同族 | **同优先级由注册序裁决**（Round 2 B173 已登记）；本轮无新例，登记为已知交互面 |

**交互层结论**：守卫族的交互**不是「优先级裁决」而是「块级归属竞态 + 伪语句注入」**——H2/H3/H9 是**抢块**（同一块被两族先后认领，裁决依赖调用序），H5 是**凭空注入**，H1/H6/H7 是**触发集未封闭**。未发现「一族守卫正确地先赢、另一族让位」的良性优先级裁决实例 ⇒ **「守卫族叠加有优先级冲突」这一命题被击穿，但冲突的性质是竞态而非优先级表缺失**。

---

## §7 新破口登记（自 **B179** 起，接 `rounds/round3/BREACH_REGISTRY.md`；B163–B178 不复用）

> 本轮共登记 **B179–B194**（16 条）：实施层 13 条（B179–B190、B193）、口径/表述层 2 条（B191、B192）、判据层 1 条（B194）。

| 编号 | 形态 | 最小复现 | 归属层 | 判定空间条目 | 影响面 | 建议机制方向 |
|---|---|---|---|---|---|---|
| **B179** | **R2 机制形态特化**：BoolOp 的操作数为 `IfExp` 时合并守卫不成立（`(a or b) and (c if a else (b or c))` → `(a or b) and a`；`while` 宿主被降级为 `if`、循环体语句丢失、`else: return` 被凭空造出） | `probes/l3_g1_r2_boolop_ternary_while.py`（2/2 单元红） | L3 实施层 | `JS-BOOLOP-*` / `JS-IFEXP-*`（BoolOp×IfExp 操作数、BoolOp×while 宿主） | R2 全部 BoolOp×IfExp 组合 | 合并守卫的谓词改为**栈效应驱动**（按 BoolOp 链的真实操作数数目切前缀），而非按「链尾是 IfExp / merge_ctx 枚举」定位 |
| **B180** | **R4 机制形态特化**：`await` 位于 for 体 / `async with` 体内 / finally 内时挂起链归约丢语句（`out.append(v)` 整条丢失；finally 体被移出 finally ⇒ 异常路径不再 flush） | `probes/l3_g3_r4_await_asyncwith_finally.py`（2/2 单元红） | L3 实施层 | `JS-AWAIT-*`（await×loop-body / await×async-with-body / await×finally） | R4 全部 await 宿主 | B47/B112/B128 的谓词从「await 在三元臂 / IfRegion 条件位」改为**「await setup 块 ⇒ 挂起链 ⇒ 消费端」三元组闭合**判据 |
| **B181** | **R6 守卫触发集未封闭**：B140 只登记 handler 内 **break**（判据④绑定「前向跳转 + 循环出口」）；handler 内 **continue**（回向跳转）在 {while 宿主 × continue 前有语句} 格被**整条丢弃** ⇒ 语义错（错误元素被 append） | `probes/l3_g5b_r6_handler_continue_matrix.py::r6_while_stmt_continue`（1/4 格红） | L3 实施层 | `JS-CONTINUE-*`（Continue×handler-body×while×d2） | 全部 handler 内 continue | continue 守卫统一为 **loop-qualified**（`(block, loop)` 配对），与 B106/B145 的 loop 限定对齐；并**修正 R6 的通用性声明**（见 B191） |
| **B182** | **R7 形态特化（3 元切片）**：`BUILD_SLICE` 按**二元**建模 ⇒ 带 step 的切片边界被丢弃（`del d[x if x else 0::2]` → `del d[x if x else 0]`）；`d[…::2] += k` 被重写为 `(d[…] + k)[…] = d` | `probes/l3_g6_r7_del_ternary_slice.py`（2/2 单元红；字节码 `BUILD_SLICE 3`） | L3 实施层 | `JS-SLICE-*` / `JS-slice-*`（Slice×step×ternary-bound） | 全部带 step 的切片 | BUILD_SLICE 的元数（2/3）纳入栈效应模型；B148 白名单改为**元数感知** |
| **B183** | **叠加（match×with）注入伪 `continue`**：match 的 case 体在 with 宿主内被注入源码不存在的 `continue` ⇒ `__enter__/__exit__` 由 1 次变每轮 1 次（**判定器判绿**，源码语义差） | `probes/l3_o4_overlay_matchguard_with_comp.py::o4`（判据 4/5 绿，`o4` 语义差） | L3 实施层 + L2 判据盲区 | `JS-MATCHSTMT-*` × with 宿主 | match × with 全部叠加 | 伪 `continue` 须在**源码级**复核（case 体的最后一条真实语句不得被替换）；并给 L2 增「语义差分」门禁 |
| **B184** | **叠加（for-else × handler-break）**：for-else 被降级为循环后顺序语句 ⇒「仅无 break 时执行」的语义被破坏（handler 内 break 时 else 仍执行） | `probes/l3_o3_overlay_loopelse_break_finally.py::o3c` | L3 实施层 | `JS-LOOPELSE-*`（for-else×handler-break） | 全部 for-else × break 叠加 | B144 的「独占可达」须把 handler 内 break 纳入 break 落点集合 |
| **B185** | **叠加（R2×R4）条件极性被反转**：BoolOp+三元+await 同一条件式 ⇒ 三元真值臂被降为 `if x: pass`（值丢弃），`await` 被挂到 `elif` 分支 ⇒ 真值成立时反而不返回 | `probes/l3_o2_overlay_boolop_ternary_await.py`（2/2 单元红） | L3 实施层 | `JS-BOOLOP-*` × `JS-AWAIT-*` | BoolOp×三元×await 组合 | BoolOp 合并守卫须**保留操作数值**（不得以语句化替代表达式值） |
| **B186** | **叠加（R2×R7×R8 表达式上下文）**：`total += len(d[...])` 被重写为 `total += x if x else 0`；`del d[n if n else 0::2]` 整条丢失 | `probes/l3_o5_overlay_augassign_del_slice.py`（2/2 单元红） | L3 实施层 | `JS-AUGASSIGN-*` × `JS-DELETE-*` × `JS-SLICE-*` | augassign+del+slice+return 叠加 | B148/B149/B150 需统一的「复合前缀」栈效应模型，避免各自信领前缀 |
| **B187** | **B174 的单层新实例 / B142 范围被证伪**：`finally` 体含**控制转移（return）**时，正常路径 finally 副本被同时计入 **try 体与 handler 体** ⇒ finally 体的副作用每元素执行 **3 次**（源语义 1 次）⇒ 「B142 是嵌套 finally 的稀窝」不成立 | `probes/l3_g7c_r8_finally_sideeffect_return.py`（2/2 单元红） | L3 实施层（扩充既有 B174 的范围 + 推翻 B142 的稀窝定性） | `JS-TRY-*`（Try×finally-with-return） | 全部「finally 体含 return/raise」的 try | 正常路径 finally 副本须有**谱系标记**并**只归属 finalbody**（B142 登记的候选机制「副本谱系图 + 属地继承」正是正解） |
| **B188** | **B143 的「稀窝」定性被证伪**：finally 体内 break 在 5 形态枚举中 **4 形态翻转红**（仅「单层 for + if 臂内 break」正确）；其中 `b143_c`/`b143_d` 出现 **`while i > 0:` 宿主被改写**（→`if i > 0:` / `while True:`）⇒ 与 Round 2 的 B172 重叠 | `probes/l3_b143b_break_in_finally_shapes.py`（4/6 单元红） | L3 实施层（扩充 B143 范围 + 关联 B172） | `JS-TRY-*` × `JS-BREAK-*`（break×finally-body） | 全部「finally 体内 break」 | finalbody 装配按 **entry 身份派发**（登记根因所指）；并把 `while` 宿主改写归入 B172 的修复面 |
| **B189** | **守卫族抢块（B152 × B150）**：同一 `region.merge_block` 先被 B152 当作 **if 体**登记为 generated，随后又被 B150 当作**双臂共享返回汇点**再次登记并折叠 ⇒ 「每块唯一归属」被破坏，裁决依赖**调用序** | `core/cfg/region_ast_generator.py:18053-18068` vs `:27096-27116`（B150 不检查 `generated_blocks`） | L3 实施层 | `JS-IF-*`（if×elif×ternary×共享返回汇点） | if/elif/ternary 与双 return 叠加 | 两守卫须**互斥化**（B150 增加「merge_block 未被其他守卫认领」判据） |
| **B190** | **守卫族触发集重叠（B152 判据 (c) 过弱）**：`P ∉ region.else_blocks` 被当作「P 是 if 之后的兄弟语句」的充分条件，未排除 P 为 **with 清理块 / 循环出口块 / finally 副本** ⇒ 与 B70g / B145 的管辖块重叠 | `core/cfg/region_ast_generator.py:18066-18068` vs `:16686-16730` / `:62066-62091` | L3 实施层 | `JS-IF-*` × with/loop 宿主 | if 体 + with/loop 叠加 | B152 (c) 须补「P 的后继/角色」校验（后继在 if 之后且不属于 with 清理链/循环出口） |
| **B191** | **表述层：R6 通用性声明与实际探针集不符** —— 落地声明称「6 个非语料合成探针 22/23 覆盖 … handler break/continue（while + for）」，仓内实际仅 `while×break`（`test_repros/round6/r6_synth_b140_handler_break.py:1`）与 `for×continue`（同文件 `:22`）两格，**`while×continue` 格从未覆盖** | `attain-true-completeness/rounds/round6/FIX.md:90` vs `test_repros/round6/r6_synth_b140_handler_break.py` | L3 口径层 | `JS-CONTINUE-*` | R6 通用性主张 | 通用性声明须改为**触发集**表述（覆盖哪些格 / 未覆盖哪些格），不得以抽样格代替触发集 |
| **B192** | **计数口径层（扩充 B178）**：191 = **123**（纯数字破口号且紧邻 `]`）+ **24**（字母后缀破口号 B61a–B61k / B70c–B70j）+ **44**（纯数字破口号但带后缀文字，如 `[B98-V3R2 修复]`）；台账 **174 = 191 − 17**（差全在 R5）。且 191/123 均为**注释出现次数**，去重到「承载函数 × 破口号」的**机制点**读数仅 **139**（承载函数 109）⇒ **标记数不得作为机制面规模度量** | `tools/l3_marker_scan.py`、`tools/l3_marker_scopes.py`（`logs/l3_markers.json`、`logs/l3_marker_rows.json`） | L3 口径层 | — | 全部对外台账的「标记数」表述 | 台账 v9 固定**唯一**计数规则（建议口径 C），并在方法层禁止把「注释标记数」当作「机制数」 |
| **B193** | **叠加（match × with，with 在 for 内）⇒ match 之后的同体语句被整条丢弃**：`for v in vals: with res as r: match v: case int() if v>0: out.append(v) …; out.append("after")` ⇒ 产物中 `out.append("after")` / `out.append("tail")` / `out.append(r)` 三条语句**消失**（执行级：源 `[3,'after',-1,'after',5,'after']` 产 `[3,-1,5]`；`__enter__/__exit__` 次数两侧相同 ⇒ 属语句丢失而非配对次数变化） | `probes/l3_o6_overlay_match_in_with_after.py`（2/2 单元红 + 执行级 DIFFERENT） | L3 实施层 | `JS-MATCHSTMT-*` × with 宿主（with 在循环体内） | match × with 叠加（同体语句在 match 之后） | with 体内的**块序列**须完整保留：match 之后的同体块不得被 B70g 的清理块过滤或 B61k 的 case 体归属判据吞掉 |
| **B194** | **L2 判据盲区（单元粒度）**：判定器在**函数 code object** 上判 Equal，而该函数的**执行语义**与源不同 —— `l3_o4::o4b`（`out.extend([x for x in range(v) if (x > 1) and (x if x < 5 else -x)])`）：判据的失败只落在**嵌套 `<listcomp>` code object** 上，函数级单元判绿；执行级差分为 DIFFERENT（源 `[2,<ctx>]` 产 `[1,2,<ctx>]`） | `probes/l3_o4_overlay_matchguard_with_comp.judge.txt:3`（失败单元 `<module>.o4b.<listcomp>`）+ `logs/l3_semdiff_sweep.json` | L2/L3（实施层证据） | `JS-*`（单元级「绿 ⇒ 对」推断链） | 「判绿 ⇒ 完备」在**单元粒度**上的推断 | 判据须引入**执行级差分**为主判据（Task 9 `semantic_diff.py`）；单元绿降级为辅证 |

---

## §8 对方法层的输入（喂 Task 8：通用性证明义务应当长什么样）

对 §2.2 的 7 个族、§6 的 10 处交互面，本轮给出的可操作结论是：**「抽样绿 ⇒ 通用」这条推断链没有承重结构**。要让「同族任意形态可迁移」成为**可判定**命题，至少需要以下四件套（与 `spec.md:100-109` 四支柱对齐）：

1. **触发集声明（Trigger-Set Declaration）**——每个守卫/机制必须声明其**语法触发集**（它负责哪些文法位形）与**排他集**（它明确不管哪些位形），并被机检。
   - 现状反例：B140 的触发集声明为「handler 内的 break」，而实际只覆盖 `{前向跳转 ∧ 目标是循环出口}`；`continue`（回向）被留白却无声明 ⇒ **声明与实现的差集必须为 0**（否则记为未封闭）。
   - 可机检形式：对每个守卫输出 `declared_trigger_set`、`implemented_trigger_set`、`uncovered_sibling_forms`；后者非空即红灯（B181 即此类）。
2. **同族覆盖引理（Coverage Lemma）**——对每个机制族，给出「**该族任一形态** ⇒ 机制命中」的证明义务，并配套**生成式同族构型器**（枚举该族的 位形 × 宿主 × 深度 × 变体槽），使「迁移」成为**覆盖率读数**而非抽样印象。
   - 本轮的三条同族新构型（R2 的「BoolOp 操作数为 IfExp」、R6 的「handler continue」、R7 的「3 元切片」）均落在**族内但不在已声明变体表**中 ⇒ 说明「族」的边界本身需要形式化（当前 25 行 / 39 形态把变体维度折进了分母，见 Round 3 §3）。
   - 可机检形式：`tools/completeness/jspace_generator.py` 需为**每个族**补「变体槽」枚举（含本轮新增的 6 个新槽：BoolOp×IfExp 操作数、await×async-with/finally 宿主、handler×continue、slice×step、finally×return 副本、match×with 宿主），并把「该槽的产物是否保持源码语义」作为**判定空间条目的第三轴**（当前只有「covered/uncovered」与正确性正交，见 B170）。
3. **叠加层的属性测试（Composition Property Test）**——「叠加 ⇒ 语义保持」必须成为**可机检属性**，而非逐例阅读。
   - 需要的属性：`P1` 守卫互斥性（任一块至多被一守卫认领 ⇒ 修 B189/B190）；`P2` 宿主不变性（产物宿主形态与源码宿主形态一致 ⇒ 捕获 B188 的 `while`→`if` 改写）；`P3` 语句守恒（源码语句集合 ⊆ 产物语句集合，且无凭空注入 ⇒ 捕获 B183/B185/B193）；`P4` 副作用基数（finally 体在产物中的执行次数 = 源码中的次数 ⇒ 捕获 B187 的 3 次）；`P5` **同体语句守恒**（宿主块（with/try/loop）内的**块序列**不得被邻接机制吞掉 ⇒ 捕获 B193）。
   - 叠加生成器应支持「N 族随机组合 × 深度 ≥3」，并用**语义差分**（Task 9 的 `semantic_diff.py`）而非字节码等价作判据——本轮 `l3_o4::o4b` 已证明**函数级 code object 判绿 ≠ 语义等价**（AT-37 / B194）。
4. **执行级差分作为主判据（新增支柱）**——本轮的执行级差分原型（`tools/l3_semdiff.py`）在 48 单元上给出 **31 判红 / 23 执行级 DIFFERENT / 1 判绿语义差**；其中「8 单元判红但执行级 EQUAL」说明字节码判据在某些输入上**过敏感**，而「1 单元判绿但语义差」说明它**可漏检**。⇒ 「完备」的证据必须**同时**给出：
   - `D1` **差分零失败**：同输入序列下源/产物的返回值、副作用（文件/全局/属性写入、上下文管理器配对次数）、异常类型与消息、语句执行顺序全部一致；
   - `D2` **差分充分性**：差分须覆盖**未走到的分支**（路径覆盖 ≥ 阈值），否则「执行级 EQUAL」只是「本次输入没踩到」；
   - `D3` **判据对齐**：字节码判据的每个红/绿都须被差分读数解释（红 ⇒ 真差 / 假差；绿 ⇒ 真等价 / 假等价），否则判据口径不可用于完备主张。
5. **计数规则的唯一化与语义化**——「机制面规模」必须用**机制点**（口径 C：139）而非注释标记数（191/123/174）；且规则须与被计数对象**同源**（否则 B192 的口径漂移会重演）。同时，任何对外「N 处机制 / N 形态完备」的表述必须同时给出**计数规则 + 复算命令**。

**最后一条给 Task 10 的输入**：本轮 §5 判定 **B142 = 形态级缺口**（须计入完备分子扣减），**B143 = 归约级缺口**（形态级分子不减，但须由「park」升为必修）。因此 **Round 8「破口 0 / 完备 128 = 100%」与「B142/B143 为稀窝」的联合断言，在 L3 之后已不成立**；v9 口径必须同时反映：形态基线分子需按本轮 **13 个实施层破口**（B179–B190、B193）扣减 + 判定空间新增 6 个变体槽（BoolOp×IfExp 操作数、await×async-with/finally 宿主、handler×continue、slice×step、finally×return 副本、match×with 宿主）+ 1 条判据层读数（B194 ⇒ 「绿 ⇒ 对」不得作为完备依据）。

---

## 附：本轮可复现命令清单（均 ≤300s）

```powershell
# 标记计数（3 口径）
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_marker_scan.py
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_marker_scopes.py
# 探针全量实跑（21 探针 / 71 单元）
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_probe_driver.py `
  --dir .trae\specs\attack-completeness-claims\rounds\round5\probes `
  --log .trae\specs\attack-completeness-claims\rounds\round5\logs --stamp l3final
# 执行级语义差分全量扫描（48 单元；判据 × 执行级交叉表）
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_semdiff_sweep.py
# 单函数执行级差分
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_semdiff.py l3_o6_overlay_match_in_with_after o6
# 读数汇总表
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_summary.py
# 字节码级证据（例：3 元切片 / handler continue）
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_dis.py l3_g6_r7_del_ternary_slice r7_del_ternary_slice
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_dis.py l3_g5b_r6_handler_continue_matrix r6_while_stmt_continue
# 产物/源定位（例）
python -X utf8 .trae\specs\attack-completeness-claims\rounds\round5\tools\l3_locate.py BUILD_SLICE
```

**本轮产出清单**：`rounds/round5/ATTACK_L3_MECHANISM.md`（本文）、`rounds/round5/probes/`（21 探针：`.py` 源 + `...OK.py` 产品 + `....judge.txt` 判定器原始输出；`.pyc` 因 `.gitignore:2` 不入库，可由 `py_compile` 重建）、`rounds/round5/tools/`（8 脚本：标记扫描 ×2、探针驱动、读数汇总、字节码取证 ×2、**执行级差分 ×2**）、`rounds/round5/logs/`（标记扫描 JSON ×2 + 探针读数 JSON ×7〔含独立复跑 `l3verify*` 与最终 `l3final`〕+ **执行级差分扫描 JSON ×1**）。
