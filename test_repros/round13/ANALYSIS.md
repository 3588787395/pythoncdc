# Round 13 — 测试工程师根因报告（R13-* 分类）

判据唯一：`_r10_strict_check.strict_compare`（严格尺子，逐指令 + 跳转终点）。
复现电池：`test_repros/round13/run_all.py`（25 个形状；21:05 与 21:20 两次复跑结果一致：
`repros=25 MISMATCH=15 MATCH=10 ERROR=0 UNEXPECTED=0 NOT-REPRODUCED=2`，`--strict` 退出码 0）。
同族工作探针：`test_repros/round13d/r13d_chain_absorption_probe.py`（7/7 PASS，未改动）。
交叉引用：`diagnosis_wave2.md`（链吸收 + 指令差分布）、`leverage_map.txt`（一次修复翻多文件）。

> **命名消歧**：本文的 `R13-A … R13-N` 是**根因类编号**（本轮内自拟，顺序即本表出现顺序）。
> 它与共享任务清单里的 agent 标签「Round 13b / 13c / 13-D（return-demoted-to-break）」**无关**：
> 那个「Round 13-D」= 本文的 **R13-A**。请勿混用两套编号。

> **本轮最重要的一个事实（drift，必须先看）**
> 报告的实测快照取自 **2026-09-20 20:55–21:10**，期间并发进行的 R13-A3 修复（工作区里
> `core/cfg/region_analyzer.py` +378 行、`core/cfg/region_ast_generator.py` +536 行未提交）
> 把基线 18 个目标 pyc 中的 **4 个直接翻正**：
> `backtest_info_utils`(creat_sheet1 1655→1655)、`config`(parse_config 293→293)、
> `setting_api`(set_parameters 170→170)、`plugin_system_control`(_terminate 43→43)。
> 另有两个文件（`set_engine` ×2）从 `seq_len -1` **变成** `target_diff`（指令数已相等，落点仍错）。
> ⇒ 基线 `targets_1fix.txt` 的 18 个缺陷函数，现在只剩 **14 个文件 / 16 个函数** 仍缺陷
> （`plugin_fly_data/__init__.pyc` 有 2 个、`flytools.pyc` 有 3 个）。
> **上一位工程师的 5 个「未触发」复现里，有 4 个（r13_03/04/18/19）瞄准的正是已经消失的缺陷**，
> 不是它们写得不对，是目标已被同期修掉。已按实测重新建模，见 §R13-C 与 MAPPING.md。

---

## 0. 分类总表

| 类 | 一句话根因（症状层面） | 复现 | 解释的 18 文件（基线 → 2026-09-20 实测） | 复现状态 |
|---|---|---|---|---|
| **R13-A** | 循环体内臂尾的 `return` 被判成 `break`（少一条 RETURN，多一条回边）| r13_01 | 基线 3：`plugin_system_control._terminate`、`set_engine`×2 → **现 0**（4 文件实测翻正，r13_01 形状也已 MATCH）| 已修复 → 转回归哨兵(SENTINEL) |
| **R13-B** | 循环体最末 region 之后又补一条 `continue`（多一条 JUMP_BACKWARD，+1）| r13_02 | 基线 2：`user_info_utils.remove_lock_files`、`config.parse_config` → **现 1**（user_info_utils 96→97 仍缺陷）| 复现成功 |
| **R13-C** | **链后共享语句被吸入「唯一能落空到链尾」的臂**；根因是 if/elif/else 链的 merge 计算退化为 `None` | r13_03, r13_04, r13_18, r13_21, r13_22（+round13d s2/s7/s8/s10）| 基线 2：`creat_sheet1`、`set_parameters` → **现 0 个 18 文件成员**（两者被并发 A3 的**循环内**子形态修复翻正）；但**函数体层子形态仍稳定复现**，且 `diagnosis_wave2` §1 量到语料级 `-1`(24)+`+2`(22) ≈ 46 个函数 | 复现成功（5 个形状 + 3 个负对照划边界）|
| **R13-D** | dict 字面量里两个推导式塌成一层嵌套推导式（`BUILD_CONST_KEY_MAP` 整条消失）| r13_05 | 2：`broker.SimulationBroker.save`(-7)、`live.DefaultLiveBroker.save`(-4) | 复现成功 |
| **R13-E** | `if x is not None: … else: return` 被展开成重复分支（+16）| r13_06 | 1：`data_proxy.DataProxy.get_bar` 86→102 | 复现成功 |
| **R13-F** | `break` 之前的语句被整批丢弃（-4）| r13_07 | 1：`plugin_fly_data/__init__._on_before_trading_start_trading_thread` 66→62 | 复现成功 |
| **R13-G** | 链后的整块 `if … : return` 被丢（-32）| r13_08 | 1：`plugin_system_persist.can_resume_strategy` 89→57 | 复现成功 |
| **R13-H** | 嵌套 `except` 与 `return` 汇合错位（-4）| r13_09 | 1：`risk_calculation/function.save_testds_to_json` 314→310 | 复现成功 |
| **R13-I** | 空 `if …: pass` 被复制多份（+11）| r13_10 | 1：`executor.Executor.check_before_trading` 243→254 | 复现成功 |
| **R13-J** | for 体前导赋值被整批下沉到回边之前 + break 前语句丢失（-24）| r13_11 | 1：`default_event_source.events` 512→488（**真实文件仍缺陷**）| **未复现**（骨架重建 + 4 个变体全 MATCH）|
| **R13-K** | elif 分支内容旋转（臂之间语句互换位置，-26）| r13_12 | 1：`matcher.DefaultMatcher.match` 715→689 | 复现成功 |
| **R13-L** | 裸 `raise` 下沉到别的路径（-5）| r13_13 | 1：`flytools.FileLock.acquire` 90→85（同文件另有 `get_mem_under_oom_status` 47→18、`whitelist_filter` 116→114）| 复现成功 |
| **R13-M** | `for … else` 的 `break` 丢失（-2）| r13_20 | 1：`utils/logger/handlers.perform_rollover` 127→125（`leverage_map`：同一函数在 `IQCommon/logger/handlers.pyc` 也缺陷 ×2）| 复现成功 |
| **R13-N** | **新识别**：链臂出口 JUMP 落点错位（`target_diff`，指令数已相等，delta=0）| 无（未复现）| 2：`set_engine`×2 —— `#60 JUMP 终点 orig=('utils'/'time',LOAD_GLOBAL) decomp=('system_log',LOAD_GLOBAL)`，即某臂应当跳过链首的 `system_log.debug(...)`，产物让它落在链尾 | **未复现**（仅真实文件证据）|

基线 18 = 3+2+2+2+1×9+… （A3 B2 C2 D2 E1 F1 G1 H1 I1 J1 K1 L1 M1 = 18）✓
2026-09-20 现存 14 个缺陷文件 = B1 + D2 + E/F/G/H/I/J/K/L/M 各1 + N2 = 14 ✓

---

## 1. R13-C（本轮唯一定位到方法级的那一类）—— 链后共享语句被吸入唯一落空臂

### 1.1 证据

最小复现（严格尺子实测，均语义错误，不是布局差异）：

| 形状 | 构造 | 实测 |
|---|---|---|
| r13_04 (=round13d s8/c01) | `if c: return 1` / `elif r: for d in r: pass` / `x = 7`（无 else 臂）| seq_len **16→18 (+2)** |
| r13_03 (=round13d b07/d03 族) | 同上但带 `else: return 2` | seq_len **23→22 (-1)** |
| r13_18 (=c08) | 5 臂宽链 + else，链尾 3 条语句 | seq_len **37→36 (-1)** |
| r13_21 (=a09/b08) | 臂尾是 `try/except` | seq_diff **#23 orig=('2',LOAD_CONST) decomp=('7',LOAD_CONST)**（内容旋转，长度相等）|
| r13_22 (=a07/c11) | 臂尾是**无 else 的 if**（无循环、无 try）| seq_len **18→17 (-1)** |

产物形态（实测输出，r13_04）：

```
if c: return 1
elif r:
    for d in r: pass
    x = 7          <<< 链尾语句被吸进 elif 臂；c 假且 r 假时不再执行 x=7
```

真实目标：基线 `creat_sheet1`(#958 `JUMP` vs `LOAD_FAST 'row'`)、`set_parameters`(#111 `JUMP`
vs `LOAD_GLOBAL 'str'`)，以及 `setting_apiOK.py:195-196` 被多写出来的
`user_config_items[key] = str(value); continue` —— 都是「链尾（循环尾语句）被搬进臂内 + 补 continue」。
**这两个 pyc 现已实测翻正**（并发 A3 修复覆盖了「臂体含 continue ⇒ NCPD 退化为循环头」那个**循环内**子形态）。

### 1.2 触发谓词（38 个形状实测，无反例；负对照见 r13_23/24/25）

设 C 为 if/elif/[else] 链区，M = 链后第一条语句所在块：

1. **M 非空**（链后确有语句；`nothing_after_chain` → MATCH）；
2. 链内**恰好一个**臂能以落空方式到达 M，其余臂全部以 `RETURN_VALUE/RETURN_CONST` 终结
   （两臂都落空 → MATCH：`two_fallthrough_arms`；兄弟臂以 `raise` 终结 → MATCH：`raise_terminator_arms`）；
3. 该唯一落空臂的**最后一条语句本身是一个带本地 join 的子区域**，且其出口是**落空型**：
   `for` / `while cond` / `for…else` / `with` / `try/except` / **无 else 的 if** 都触发；
   臂尾是普通语句（`x = 5`）或 `if/else` 全分支赋值（无本地 join）→ MATCH；
   `while True: … break`（唯一出口是无条件 jump，非落空型）→ MATCH；
4. 链**无 else 臂**时，还要求该臂是**最后一个臂**（落空臂在前 + 兄弟臂 return → MATCH）。

⇒ 触发条件与「循环」无关（try / 无 else 的 if 一样触发），**禁止 FOR_ITER 特判式修法**。

### 1.3 归约层证据（运行时插桩，未改 `core/`）

对 r13_04 / r13_03 / r13_22 三个形状跟踪 `_collect_branch_blocks` 的入参与结果：

```
c01: IFREGION entry=0 merge=None
       then=[6[LOAD_CONST,RETURN_VALUE]]
       else=[10[elif cond], 14[GET_ITER], 24[LOAD_CONST,STORE_FAST,LOAD_CONST,RETURN_VALUE], 18,20]
                                        ^^^^ 链尾块 24 被收进 else_blocks
     内层循环自己却算对了：CALL entry=14 merge=24 stop={24} collected=[14,18,20]
a07: 外层同样 merge=None 且 collected 含链尾块 28；内层 IfRegion entry=14 merge=22 正常
d03: 外层 merge=None collected=[6,10,12,26,40]，40 = 链尾 `x=7; return None`
```

结论：**缺陷发生在区域分类/归约阶段，不在 AST 生成阶段**。
`_generate_if`（`core/cfg/region_ast_generator.py:10918`，其文档明确 `then_blocks→If.body`、
`else_blocks→If.orelse`）只是忠实地把已经被污染的 `else_blocks` 渲染成了臂体。

责任方法与行号（本轮实际读过）：

| 位置 | 事实 |
|---|---|
| `core/cfg/region_analyzer.py:1255` `RegionAnalyzer.analyze` | 归约主流程入口 |
| `core/cfg/region_analyzer.py:15367` `_identify_conditional_regions` | if/elif 链区识别 + merge 计算（本次缺陷所在） |
| `core/cfg/region_analyzer.py:1890` `_find_nearest_common_post_dominator` | 臂尾 return ⇒ post-dominator 无解，返回 None（A3 已加「结果为循环头时改算」守卫，但**没有覆盖「链尾块只有唯一入边」这一形态**）|
| `core/cfg/region_analyzer.py:1953` `_find_merge_via_forward_reachability` | A3 新增；其 `[R13-A3 扩展]` 分支当前被 `if True: return None  # TEMP-DISABLED` 短路（工作区未提交状态，21:05 实测），扩展判据尚未生效 |
| `core/cfg/region_analyzer.py:2053` `_compute_merge_from_jump_targets` | 第二级兜底，对本形状同样返回 None |
| `core/cfg/region_analyzer.py:16916-16998` | merge 兜底阶梯；**16979-16998 的最后一档用 `_8_test = _collect_branch_blocks(else_succ, None, stop)` 收集到的块数 `> 25` 作为阈值**来决定 `merge = else_succ`。r13_03/04/22 的过度收集只有 5-6 块 ⇒ 远够不到阈值，merge 保持 None，随后 17046/17143 两次 `_collect_branch_blocks(..., merge=None, ...)` 无界收集，把 M 及其后继整段吸进臂 |
| `core/cfg/region_analyzer.py:25432` `_collect_branch_blocks` | `merge=None` 时按「无界收集」工作；25456-25465 `stop = {merge} ∪ stop_set` 且 `stop.discard(entry)` |
| `core/cfg/region_analyzer.py:25516-25536` | W14-C「共享尾部语句反向剪枝」被 **`if False and len(collected) > 1`** 整段禁用 |
| `core/cfg/region_analyzer.py:25546` | 生效版剪枝只在 **`not merge`** 时运行，且判据是「存在**不在 stop 里**的外部前驱」。本形状 M 的全部前驱要么在臂内（落空边），要么就是链的条件块/边界块（在 `stop` 里）⇒ 剪枝按定义不触发 ⇒ **这就是吸收的最后一道闸失效点** |

### 1.4 修复（三元式，禁止跨区启发式）

* **识别条件（纯结构）**：对候选链区 C，定义区域出口集
  `E(C) = { s | s ∈ succ(b), b ∈ C, s ∉ C }`，剔除终结块（RETURN_VALUE/RETURN_CONST/RERAISE）与回边目标
  （`s` 支配 `b`）。若 `|E(C)| = 1`，记 `E(C) = {M}`，则 **M = 该链区的 merge**，无论各臂是否以 return 终结、
  无论 C 是否有 else 臂、无论 `M` 相对 C 的偏移远近。
  该判据即标准「单出口区域」定义，等价于 `diagnosis_wave2` §4 写的「M 必须是整个 if 区间的单一出口节点」。
* **归约方式**：把 M 计入 C 的 merge 引用而**不是**任何臂的 body —— 即 `_collect_branch_blocks(entry, merge=M, stop)`
  必须以 `M` 为界（`visited` 初始化即含 M，见 25466），父区域顺序段继续从 M 归约；
  链的其余臂（return 终结者）不向 M 贡献入边，这正是 `|E(C)|=1` 成立的原因，不得反过来当作「臂独占 M」的证据。
  同时删除 16979-16998 的 `len(_8_test) > 25` 计数阈值档，改为上面的出口集判据；
  25546 的剪枝判据把「`stop` 内的前驱」也算作**外部性证据**（条件块落到 M 的边不是臂内部边），
  或在 `merge is None` 时统一按 `E(C)` 重算 merge —— 两处任选其一即可，但不得引入块数/偏移阈值。
* **AST 映射（单一节点类型）**：链后语句映射为 `ast.If` 的**兄弟语句**（父级 `stmts` 列表中的后续元素）；
  `ast.If.orelse` 仅当 CFG 里真的存在 else 边时才有成员，无 else 臂时**必须**保持 `[]`
  （禁止为安置被吸走的语句而合成 `else:`，这是 r13_04 的 +2 来源）。
  被吸收后多出来的那条不可达 `LOAD_CONST None; RETURN_VALUE`（`diagnosis_wave2` §2 的
  `get_covered_amount` 双尾部 return）随本修复自动消失，不要单独处理。
* **明确禁止**：`op[offset] == FOR_ITER` / `JUMP_FORWARD` 目标偏移区间 / 按 `co_name` 或文件白名单 /
  在 AST 生成阶段（`region_ast_generator`）事后搬动已生成的语句 / 跨层级「看兄弟区域有几条语句」的计数启发式。
  本类必须只在**分类/归约**层用支配-后支配 + 出口集解决。

---

## 2. R13-A / R13-B（同族：终结边被降级/复制）

* **R13-A**（r13_01）：`for f in (a,b): inst=f(); if isinstance(...): inst.terminate(); return`
  → 产物 `break`，`sys.exit(0)` 被错误执行。`_terminate` 实测 43→43 已翻正、r13_01 形状也已 MATCH
  （A3 落地），但 `set_engine`×2 留下了 **R13-N** 的落点错位，说明该类只是**换了症状**、未收口。
  建议：r13_01 保留为 SENTINEL；R13-N 需另建复现（见 §4）。
* **R13-B**（r13_02）：`remove_lock_files` 96→97 真实仍缺陷。症状 = 最内层 for 体最后一条语句之后
  多一条 `JUMP_BACKWARD`。与 R13-C 同源机制（merge/出口集判定）但落点在循环回边，
  归约层证据未做到方法级（本轮预算），**修复工程师请以 r13_02 为尺子**，
  三元式提示：识别条件 = 臂/体的出口集 `E` 含「回边」与「顺序后继」两类且被并成单条回边；
  归约方式 = 两条边各自保留其语义；AST 映射 = `Continue` 只允许来自真正的回边块，
  不得由「臂尾 region 的自然落空」合成。禁止按 opcode 判 `continue`。

---

## 3. R13-D … R13-N（各自 1–2 个文件，本轮只做到「形状级复现 + 症状定位」）

下列各类的**复现与证据充分**（见 MAPPING.md 的实测 seq_len/seq_diff 行），但**方法级定位未做**，
诚实标注为「待修复工程师确认」；给出的 stage 判断只依据产物差异本身，不依据猜测的行号。

* **R13-D**（r13_05，`broker.save` 22→15、`live.save` 16→12）：
  `{k1:[…], k2:[…]}` 的两个推导式被套成一层嵌套推导式，`BUILD_CONST_KEY_MAP` 消失，
  真实产物 `IQEngine/plugins/plugin_system_simulation/liveOK.py:66` 形态为
  `return [o.load() for account, o in [o.load() for account, o in copy.deepcopy(self._open_orders)]]`。
  **阶段**：表达式/推导式重建（`core/cfg/comprehension_generator.py`，由
  `core/cfg/region_ast_generator.py:196` 装配的 `ComprehensionGenerator`）——
  不是 CFG 分类问题（两个 MAKE_FUNCTION+LOAD_CONST 常量在原始字节码里彼此独立）。
  三元式：识别条件 = dict 的每个 value 是**独立的 comprehension 常量对象**（`co_consts` 里两个不同 code）；
  归约方式 = 每个 value 子区域各自归约为表达式节点，禁止把相邻两个推导式并成一个嵌套结构；
  AST 映射 = `ast.Dict(values=[ListComp, ListComp])`。这是**字典字面量重建**，不是控制流区域。
* **R13-E**（r13_06，`get_bar` 86→102，+16）：`if x is not None: … else: return` 被展开成重复分支。
  阶段：区域分类（IF/IF_THEN_ELSE）+ 复制式回退。与 `diagnosis_wave2` §6 的
  「`else: return None` 退化文本不是缺陷指纹」一并看，勿用文本判据。
* **R13-F**（r13_07，66→62）：`break` 之前的语句被丢 —— 与 R13-C 的 M 归属同族（`stop`/`boundary_stop`
  把臂尾块挡在外面后整段丢弃，参见 `region_analyzer.py:25456-25465` 的 `stop.discard(entry)` 注释所述失败模式）。
* **R13-G**（r13_08，89→57）：链后整块 `if/return` 被丢，是本报告 §1 的**反面症状**（同一条 merge 判据
  失败时，视形状不同表现为「吸收」或「丢弃」）。**若 §1 的出口集判据落地，本类有望连带翻正，请务必先跑 r13_08 + `can_resume_strategy` 的真实 pyc 复核**。
* **R13-H**（r13_09，314→310）：嵌套 `except` 与 `return` 汇合错位。
* **R13-I**（r13_10，243→254）：空 `if …: pass` 被复制（+11）。
* **R13-J**（r13_11，512→488）**未复现**：正确源骨架 + 4 个变体（生成器全形 / while True+break /
  for 前导+while+break / 生成器前导+嵌套 for+yield）全部 MATCH ⇒ 真实缺陷依赖 events() 的
  多层 try/except + yield 混合上下文。**不得据 r13_11 下结论**；请对真实 pyc 取证（§5 的探针配方）。
* **R13-K**（r13_12，715→689）：elif 分支内容旋转。与 r13_21 的 `#23 LOAD_CONST '2' vs '7'`
  旋转症状**同型**，即 §1 的吸收在宽链上表现为「臂尾与链尾两段语句互换」⇒ 再次提示 R13-K 可能是 R13-C 的子集。
* **R13-L**（r13_13，90→85）：裸 `raise` 下沉。
* **R13-M**（r13_20，127→125）：`for … else` 的 `break` 丢失；`leverage_map.txt` 显示同一
  `perform_rollover` 在 `IQCommon/logger/handlers.pyc` 与 `IQEngine/utils/logger/handlers.pyc` 各一处 ⇒ 一次修复 ×2 文件。
* **R13-N**（无复现）：`set_engine`×2 的 `target_diff #60`（指令数已相等、JUMP 终点由 `utils`/`time` 块
  变成 `system_log` 块）。真实形态：链的某个臂本应跳过链首的 `system_log.debug(...)`。
  本轮尝试不足以建立最小复现（38 个形状里没有覆盖「臂跳过链首一条语句」这一向），标注**未复现**。

---

## 4. 编译器小版本差异，不必修

**本轮没有候选被证明是 CPython 小版本代码生成差异，本节为空。**

依据（都是实测，不是推断）：

1. 本机解释器就是 **3.11.7**（`python -c sys.version` → `3.11.7 (tags/v3.11.7:fa7a6f2, Dec 4 2023 …)`），
   与 targets 的编译版本一致 ⇒ 「用重建源码做复现」这条路径**不存在**小版本退路：
   重建源码若 MATCH，只能说明形状选错或该缺陷已被修掉，不能甩锅编译器。
2. `diagnosis_wave2` §2 已经用 3.11.7 探针证伪了「尾部隐式 `return None` 是编译器发的」这一 excuses：
   各臂全 return 的 if/elif/else **不发射**尾部 `LOAD_CONST None/RETURN_VALUE`，
   只有存在可达落空路径时才发射恰好一条 ⇒ 产物里的**第二条**必是 decompiler 造的（本轮 r13_04 的 +2 即此形态）。
3. `diagnosis_wave2` §6 的 `CONTAINS_OP invert` + 极性同时翻转（`Quote.check_industry_code`）是
   **联合反演**，控制流等价 —— 该条已被判为「不改尺子、只要求生成器忠实保留原始极性」，不属于本节（未被证伪为编译器差异，也不许当编译器差异放过）。

反面提醒：本轮**不要**把 §3 里任何未复现项（R13-J、R13-N）解释成编译器差异 —— 它们的真实 pyc 现在仍在缺陷中，
只是最小形状还没找对。

---

## 5. 复跑与取证配方（scratch 探针，仓库外）

```
# 电池（25 形状；--strict 时 UNEXPECTED/REGRESSED 会退出码 1）
PYTHONIOENCODING=utf-8 python test_repros/round13/run_all.py
PYTHONIOENCODING=utf-8 python test_repros/round13/run_all.py 03 04 18 21 22 --show-diff
# 同族工作探针（不得修改）
PYTHONIOENCODING=utf-8 python test_repros/round13d/r13d_chain_absorption_probe.py

# 真实 pyc 逐函数取证（输出全部写 D:/Temp，不覆盖任何 *OK.py / pyc_index.json）
#   步骤：decompile_pyc(真实pyc) -> 写 D:/Temp/r13real/<tag>_DECOMP.py -> py_compile(cfile=同目录)
#         -> _load_map(两侧) -> strict_compare 逐函数 -> 打印 orig/decomp/delta
PYTHONIOENCODING=utf-8 python D:/Temp/r13_real.py IQEngine/plugins/plugin_system_persist/__init__.pyc
# 归约层插桩（monkey-patch，不改 core/）：看 _collect_branch_blocks 的 merge/stop/collected
PYTHONIOENCODING=utf-8 python D:/Temp/r13_trace.py D:/Temp/r13probe/c01_looparm_last_noelse_1stmt.pyc
```
`D:/Temp/*` 是临时件，可能被清；§1.3 已把关键结论全部落成本文档的文字，复现判据以 `run_all.py` 为准。

## 6. 给修复工程师的顺序建议

**按 18 文件的实测翻正数排序**：R13-D = 2、R13-N = 2（但无复现）、其余每类 = 1；
R13-A / R13-B / R13-C 的 18 文件成员已被并发 A3 抢先翻正（现 0 / 1 / 0）。

1. **先做 R13-D**（`broker`+`live` 两个文件，`save` 只有 22/16 条指令，r13_05 稳定复现）：
   现存唯一「一个修复翻 2 个文件且已有最小复现」的类，单位成本最低、门最好设。
2. **再做 R13-C 的出口集判据**（`|E(C)| = 1 ⇒ merge = M`，替换 `region_analyzer.py:16979-16998` 的 `> 25` 计数档
   与 25546 剪枝的外部性判据）。理由：① 它是本轮唯一做到**方法级 + 行号级**定位的类；
   ② 它是 `diagnosis_wave2` §1 里 `-1`(24) + `+2`(22) 共 **≈46 个函数**（语料级）的共同根因；
   ③ 它同时是 R13-G（整块丢弃型）与 R13-K（旋转型）的疑似母类，一次修复的**外溢收益最大**（最多再带 2 个 18 文件成员）；
   ④ 在 18 文件上的直接翻正数目前是 0（成员已被并发 A3 抢先翻正），所以**必须**用
   `run_all.py 03 04 18 21 22` + `r13_23/24/25` 三个负对照当门，不能只看 18 文件计数。
3. 再 **R13-M**（`perform_rollover` 同函数 ×2 文件，r13_20 已复现；leverage 跨 IQCommon/IQEngine 两份 handlers）。
4. R13-B 只有 1 个文件存活（user_info_utils），但它是「多一条回边」族的代表，顺手做。
5. R13-J / R13-N **先补复现再动手**；不要按 §3 的猜测直接改代码。
6. 任何一步之后：先跑 `r13_01`（SENTINEL）与 `r13_23/24/25`（负对照）确认没把 return→break、
   两臂落空、`while True`+break 这些**本来正确**的形状改坏。
