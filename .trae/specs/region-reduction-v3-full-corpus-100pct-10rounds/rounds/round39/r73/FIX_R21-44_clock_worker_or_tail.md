# FIX_R21-44 — `if X and A or B` 被区域归约拆成 `if X: if A or B:` ⇒ 尾腿抬回同一条测试（r73，未安装：fires without flips，按合取件入库）

目标单元：`<module>.RealtimeEventSource.clock_worker`
（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`，13 单元，面板读数 12/13）
工程师：r73（镜像 `D:/Temp/r73`，仓库全程只读；`git status --porcelain` 见 §9）
builder：`build_cand_r73_r2144.py`（本目录），re-anchor 用 `merge_hunks_copy_used_for_reanchor.py`

## 0. 镜像与前提校验（规则 6，全部实测）

```
core/cfg/region_ast_generator.py   sha256[:16] = 11324f276cce6d5b   （门禁 38 认证字节，MATCH）
core/cfg/region_analyzer.py        sha256[:16] = f7d849e974904492   （MATCH）
```

* landed 字节重生成 `realtime_event_source.pyc`：产物 20205 字节（CR 去除后）与入库
  `realtime_event_sourceOK.py` **逐字节一致**（`cmp` IDENTICAL）⇒ 复现成立，后续读数可比。
* landed 上 clock_worker：`len orig=1424 prod=1311 delta=-113`，`hunks=7 landings=18`，
  判据 `status=failure units=12/13`，失败项 `***<module>.RealtimeEventSource.clock_worker: Different control flow`。
  工单给的 −113/7 前提**成立**。
* `unit_diff.py` 小窗过滤会藏指令：全程同时跑 `allwin_r63.py`（未过滤）读数一致。

## 1. P1+P2 重新锚定到门禁 38 字节（本工单第一件事）

`CANDIDATE_r38_P1P2_onto_landed_BANKED_not_landed.py`（`c4a934d595200c84`）的基是**门禁 37** 的
`20fa73b4e8231f0f`，落在 `D:/Temp/r67/landed_region_ast_generator.py`。移植命令与结果：

```
python -X utf8 merge_hunks.py --base D:/Temp/r67/landed_region_ast_generator.py \
  --candidate rounds/round38/CANDIDATE_r38_P1P2_onto_landed_BANKED_not_landed.py \
  --current  D:/Temp/r73/core/cfg/region_ast_generator.py \
  --expect-residual '[R21-43]' --out work/ANCHORED_r38_P1P2_on_g38.py
# applied 6 hunks, dropped 0; merged size=3856474 sha16=cf5868e68208adf6
# residual merged-vs-candidate: 2 blocks, 两块 explained-by-marker=True（都是 [R21-43] 自身）
```

工具的 `FAIL: residual not explained` 判定没有触发，但我仍**独立验证**了移植忠实性：
`diff(门禁37 landed → 门禁38 landed)` 恰是两处纯插入（`+130 @15607`、`+30 @16595`，删除 0 行），
即门禁 38 只带了 [R21-43]；merged 相对 current 的差也只有这两块 ⇒ 除 P1/P2/M1 六窗外无任何夹带。

**重新锚定后的实测 hunk 表**（base = `cf5868e68208adf6`，`allwin` 未过滤读数）：

```
len orig=1424 prod=1418 delta=-6  hunks=5 landings=12 judge_diff=True   （工单预估 −6/5 成立）
 #1 insert  prod @6498  JUMP_FORWARD                        ← 伪臂尾跳转（站点 @6322）
 #2 delete  orig @6778..@6782 (3)  self.before_trading_date = now_date
 #3 insert  prod @7244  JUMP_FORWARD                        ← 伪臂尾跳转（站点 @7164）
 #4 delete  orig @7270..@7308 (6)  system_log.debug('获取重登信号量')
 #5 replace orig @9210..@9212 (2) → prod @9170..@9172 (3)   ← #2 的内容被发在函数尾 = 位置错，不是没发
```

关于「位置」的口径（工单要求按原始 CFG 块序说，不信对齐器）：#5 的对齐方向两个对齐器结论相反，
本工单只用 CFG 事实陈述：块 `@6778..@6782` 的前驱是 `@6690`（假出口）与 `@6702`（臂落点），
后继是 `@6792` 与异常边；而 `IfRegion@6690` 自己声明 `then=[6702] else=[] merge=@6778..@6782(3)`。
所以它在源码顺序上必然紧跟 `if holiday_not_do_before == '0': …` 之后、`@6792` 之前 —— 与对齐器无关。

## 2. 结构事实：本单元有 4 处同一个形状，源码里是 `X and A or B`，不是一个嵌套 if

CPython 3.11 把 `(X and A) or B` 编译成唯一布局。3.11.7 实测（`shapes_r73_compile_proof.py`，
两条语句 `if X and A or B: arm` / `if X: if A or B: arm`，同变量同作用域）：

| 形态 | X 的 `POP_JUMP_IF_FALSE` 落点 | 臂尾 | 与本单元原始字节码 |
|---|---|---|---|
| flat `if X and A or B: arm` | **尾腿 B 的测试块** | **无 JUMP_FORWARD，直落下一句** | 逐条一致 |
| nested `if X: if A or B: arm` | 整个 if 之后（跳过头腿） | 被 elif 采集器折叠后需要臂尾跳转 | 不一致（就是 #1/#3） |

区域数据（`probe_regions.py`/`probe_sites.py`，只读，无探针）：

```
IfRegion@6322  cond=@6322(X, 末跳 IF_FALSE→@6374) then=[@6344,@6360,@6370,@6372,@6406] else=[] merge=@6374
  子区域 @6344：chained_compare_blocks=[@6360] ops=['<=','<']  ← and 腿 A 是一条链式比较
  「merge」@6374：末跳 IF_FALSE→@6496，另一条件后继 @6406 —— @6406 就在本区域 then_blocks 里
IfRegion@6496  同形（A=@6518 链式比较，尾腿 @6548→E=@6792，臂 @6580）
IfRegion@7164  同形（A=@7186 链式比较，尾腿 @7216→E=@7582，臂 @7248）
IfRegion@7582  同形（A=@7604 链式比较，尾腿 @7634→E=@8592，臂 @7668）
```

「@6374 不是汇合点」是可证明的而不是猜的：汇合点只可能被臂体流向，而 @6374 的条件后继之一 @6406
**是本区域的 then 块**（M 流向臂 ⇒ M 是 or 的尾腿）。这正是新「着陆通道」定律的用法：不写跳转目标，
只改语句挂进哪个 suite —— suite 选了，`compile()` 线程出来的跳转落点就跟着对。

## 3. 判据 `[R21-44]`（`_r2144_and_leg_before_or_tail`，插在 `_r4701_and_lift_or_tail` 之前；调用点 `region_ast_generator.py:25958`，与已落地的 [R21-19]/[R47-01] 同一挂载点 `_if_extract_condition_from_instructions`）

八条合取，全部来自区域数据 / opcode 类别 / 前驱后继结构，无函数名、无绝对偏移、无计数阈值：

① `else_blocks` 空且 `merge_block` M 存在；② M 末跳是**前向条件跳转**（非 `NONE_CHECK` 同族）——
汇合点不再测东西；③ M 去掉假出口后唯一条件后继 T 必须是本区域 then 块（M 流向臂 ⇒ M 非 merge）；
④ X 末跳为 `IF_FALSE` 且落点恰为 M 起点，X 的另一条件后继 A ∈ then_blocks；
⑤ A 是某子 `IfRegion` 的 `condition_block` 且带 `chained_compare_blocks`+`chained_compare_ops`
（A 可整体重建为一条链式比较）；⑥ 腿内自洽：腿跨度内每个条件后继仍落在 腿∪{T,M,E}；
⑦ 臂体在 `[T,E)` 内做后继闭包确实落回 E（语句顺序事实）；⑧ 臂体正常流里**不得有无主测试块**
（以条件跳转收尾的块必须是某 `IfRegion` 的 `condition_block`；`PUSH_EXC_INFO` 开头的处理器入口按 opcode 类别排除）。
另有纯表达式守卫：X、腿块、M 的指令中不得出现任何 `STORE_*`。

归约动作：测试改为 `BoolOp(or, [BoolOp(and, [X, A]), B])`；臂表取自「被误判成 merge 的尾腿自己的 then」
在 `[T,E)` 内的块（站点 @6322 得 `[6406]`，@6496 得 `[6580,6582,6652,6690]`）；`merge_block = E`、
`else_blocks = []`；腿块与 M 登记 `generated_blocks/offsets`（原则 2：一条语句只有一个发射者）。
不成立时返回 None，零副作用 ⇒ 产物逐字节不变。

**为什么 ⑧ 也在证明里**：站点 @7164/@7582 的臂跨里有块 `@7248`（`now_date != self.first_run_date` 测试），
它不是任何区域的 `condition_block`，只是 `inline_boolop_chains={blocks:[7248,7270], op:None}` 的成员
（与 `CENSUS_R21-38A_r66a.md` §2 同一事实）。实测把 @7164 并进来会丢整条测试（delta −6→−324），
所以判据在识别期拒绝对它动作 —— 这是保守性，不是偏好。

## 4. 数派（`CENSUS_r2144_counts.txt` / `CENSUS_r2144_fire_log_all20files.txt`）

20 个面板文件、**847** 次求值（`negate=False` 且 `else` 空，走到判据本体）、**845** 次拒绝、**FIRES=2**，
两处都在文件 #13（`realtime_event_source`）：`cond=@6322` 与 `cond=@6496`。其余 19 个文件 0 命中。
探针（`_r2144_census_note`，环境变量 `R2144_CENSUS` 才写文件，FIRE 行写在改区域之前）**已证惯性**：
探针版 + census ON 与交付版（`--no-probe`，`83a430f2700ae3a4`）在 20/20 个面板文件上产物 `cmp` 全等。

## 5. 实测：指令差与单元判定并排（规则 3，不拿缩小当进展）

| 字节 | clock_worker `orig/prod` | delta | hunks | landings | 判据读数 |
|---|---|---|---|---|---|
| landed `11324f276cce6d5b` | 1424/1311 | −113 | 7 | 18 | `units=12/13`，clock_worker Different control flow |
| landed + R21-44（半件独走） | 1424/1310 | −114 | 6 | 15 | `units=12/13`，同一单元 |
| anchored `cf5868e68208adf6`（P1+P2） | 1424/1418 | −6 | 5 | 12 | `units=12/13`，同一单元 |
| anchored + R21-44 `83a430f2700ae3a4` | 1424/1417 | **−7** | **4** | **9** | `status=failure units=12/13 success_rate=92.31%`，`***<module>.RealtimeEventSource.clock_worker: Different control flow` |

关掉的是 #1（@6496 那条伪臂尾 `JUMP_FORWARD`）与 3 处 landing；#3（@7242）留在原地，因为它属于
被 ⑧ 拒动的 @7164 站点。delta 计数变差（−6→−7）而形状变简（5 窗→4 窗，其中 2 窗同类），
按本战役惯例以「窗口 + 是否翻正」论，不以 `abs(delta)` 论。

## 6. 面板（`PANEL_20files_before_after.txt`）

20 个文件逐一 landed / anchored / +R21-44 三列 sha16 + `units=x/y`：
**changed files = 1**（`realtime_event_source.pyc`，22322 → 22108 字节）；landed → anchored 也是 1，
证明 re-anchor 没有夹带别的文件。单元读数三列**全等**：`153/153, 92/92, 64/64, 30/30, 58/58, 41/41,
28/28, 45/45, 27/27, 37/37, 126/128, 17/17, 12/13, 43/43, 49/49, 39/39, 43/43, 17/17, 15/15, 18/18`，
面板合计 954/966 在三列上不变 ⇒ 19 个其它面板文件零下降、零回归、零翻正。
六个重名 canary（`arg_checker` ×3、`profiler_func` ×3）本轮改为按完整相对路径落盘（早期 rig 用
basename 会让三者互相覆盖，读数曾假报 33/50 —— 已修，不影响结论）。

## 7. 结论与入库理由

**未安装**：FIRES=2 而 FLIPS=0（规则 3），且半件独走（landed+R21-44）也不翻正 ⇒ 只能作为合取件入库。
入库价值是实测的：它关掉本单元 7 条 hunk 链路上的第一类（臂尾伪跳转 + 3 处 landing），
且爆炸半径恰为一个文件，任何后续门禁与它无耦合风险。

本单元翻正仍需另两条机制同时闭合（项目记忆「三条独立发射缺陷必须同时闭合」在这里成立）：

* **(B) `@6778` 汇合块位置**：`IfRegion@6690`（`then=[6702] else=[] merge=@6778..@6782(3)`）已声明，
  但内容被发在函数尾 `@9170`。这就是 `CANDIDATE_r67a_mergeblock_BANKED_reclaimed_WIP.py`
  （`17b73582864fbba0`）未完成的目标；`RECLAIM_R21-38B_r67a.md` 说它在 `c4a934d595200c84` 基上才可见，
  下次 dispatch 应直接从 `cf5868e68208adf6`（本文重新锚定的同一基）起步，并用 §1 的 hunk #2/#5 配对验收。
* **(A) 臂跨里的无主测试块 `@7248`**：它使 @7164/@7582 两站点被 ⑧ 拒动，同一站点也吞掉
  `system_log.debug('获取重登信号量')`（hunk #4，6 条指令）。两条出路都是**声明级**的：
  分析端为 `@7248` 声明 `IfRegion(condition_block=@7248)`（它现在只作为 ibc 链成员存在，`op=None`），
  或按 `CENSUS_R21-38A_r66a.md` §3 在 `_if_generate_elif_chain` 的臂体装配里发「前缀语句 + 嵌套 If」。
  两者闭合后 ⑧ 自动放行，@7164/@7582 的 flat 形状由本判据接管（R21-44 已就绪，无需重写）。

## 8. 交付物清单（`D:/Temp/r73/DELIVER/`）

`ANCHORED_r38_P1P2_on_g38_landed_11324f276cce6d5b_cf5868e68208adf6.py`（重锚定后的 P1+P2 基）
`CANDIDATE_r73_r2144_region_ast_generator_83a430f2700ae3a4.py`（交付候选，无探针）
`CANDIDATE_r73_r2144_for_census_probebuild_878619b1db9d0dc2.py`（同一判据 + census 探针）
`CANDIDATE_r73_r2144_on_plain_landed_halfalone_248d5253c432eb6b.py`（半件独走用）
`build_cand_r73_r2144.py`、`merge_hunks_copy_used_for_reanchor.py`、`shapes_r73_compile_proof.py`
`PRODUCT_landed_/ PRODUCT_anchoredP1P2_/ PRODUCT_R2144_/ PRODUCT_R2144_on_plain_landed_realtime_event_sourceOK.py`
`CENSUS_r2144_counts.txt`、`CENSUS_r2144_fire_log_all20files.txt`、`census_r2144pp2_01..20.txt`
`PANEL_20files_before_after.txt`

## 9. 仓库状态

仓库全程只读：`core/`、`scripts/`、`site-packages/` 未写；所有生成物落在 `D:/Temp/r73/out|work|DELIVER`。
镜像收尾恢复为门禁 38 字节（`core/cfg/region_ast_generator.py = 11324f276cce6d5b`，
`core/cfg/region_analyzer.py = f7d849e974904492`，安装前后各 `cmp` 一次）。
