# FIX B133 — try 体尾 `break` 抑制（case 2）与 if 汇合块跨区域认领（case 1）

状态：**进行中**。本轮只写本文件到仓，代码改动全部在镜像 `D:/Temp/r133/wt`，交付物 `D:/Temp/r133/b133.patch`。

## 0. 工作态与封存校验

- 镜像 `D:/Temp/r133/wt`（core/ bytecode/ parsers/ utils/ scripts/ pycdc.py），98 个 .py 逐文件 sha256 与仓 HEAD **全部相等**（mismatch 0）。
- 封存值复核：`core/cfg/region_ast_generator.py = e9a8f65f6451bcc8…` ✓、`core/cfg/region_analyzer.py = 38a1d5142d132fd7…` ✓。
- 全程未写仓 `core/`、未跑 git 写命令；`.pyc` 输入取仓 `site-packages/`，产物一律写 `D:/Temp/r133/prod/`，从不读仓内 `*OK.py`（402 全量重生正在跑，仓产物不可作证据）。
- 量测 rig：`D:/Temp/r133/scratch/rig.py`（镜像 pycdc.py 产产品 → 镜像 `scripts/pyc_verify.py batch --index`，index 每条带显式 `source`，因此永不触碰仓产物）。

## 1. HEAD 基线（实测，产物由镜像 HEAD 码生成）

| 读数 | 值 |
|---|---|
| `fly/dumpload/load_daily.pyc` | **26/27**，失败单元 `***<module>: Failure: Different control flow` |
| `IQCommon/util/trade_info_utils.pyc` | **37/41**，失败单元 `kill_trade_process` / `get_trade_status` / `query_trade_strategy_info` / `query_strategy_id`（全为 Different control flow） |
| 两文件合计 | units 63/68，rig 标签 `head_target2`，`D:/Temp/r133/prod/head_target2.json`，elapsed 85s（2 文件） |

（后续读数逐节增量追加。）

## 2. Case 2（`get_trade_status` / s9）— 已落地并实测

**宿主**：`core/cfg/region_analyzer.py:_try_body_terminates_abnormally`（镜像行 11582-11584 → 11602）。
**判据（一句话）**：块尾 `RETURN_*`/`JUMP_BACKWARD`/`JUMP_FORWARD→loop header` 的 try 体块，若它属于
**嵌在本 try 体内的循环**——该身份由「循环头 ∈ 本次扫描的 try 体块集 ∧ 循环头严格支配该块 ∧ 该块从
循环头的『能回到循环头』的那条后继（= 循环体入口，FOR_ITER 耗尽边/条件为假边被排除在外）沿正常后继、
只经仍在 try 体块集内的块可达」给出——则不构成 try 体异常收尾；`self.regions` 不再被读取（该读在本
调用点恒为空集，即 §1.3 单向数据流违规的静默豁免面，本票把它封闭为边/支配闭包）。

新增方法 `_try_nested_loop_body_blocks`（六项 docstring + C 条款齐备，无新 self 状态，无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀，
无名字/偏移/计数/深度判据）；`_try_body_terminates_abnormally` 的 docstring 整体改写为六项模板，散文与新行为一致。

### 2.1 读数（半票 A/B，case 1 未叠加）

| 靶 | HEAD | +case 2 | 判定 |
|---|---|---|---|
| `IQCommon/util/trade_info_utils.pyc` | 37/41 | **38/41** | ✓ 门禁 2 |
| 失败单元名单 | kill_trade_process / **get_trade_status** / query_trade_strategy_info / query_strategy_id | kill_trade_process / query_trade_strategy_info / query_strategy_id | ✓ `get_trade_status` 清、其余三个名字不变 |
| `fly/dumpload/load_daily.pyc` | 26/27 | 26/27（不变） | ✓ 两案独立（Q3 复证） |
| 复现臂 **s9** | 1/2（`<module>.f10` 红） | **2/2** | ✓ 门禁 3 |
| 规定四臂 r1/r2/r3/r4 | 2/2 各 | 2/2 各 | ✓ 无红（无回退） |
| 负对照 s5/s6/s7/s8 | 2/2 各 | 2/2 各 | ✓ 无红 |
| 产物是否移动字节 | — | **是**：trade_info_utils 产物 sha256 前缀 `bb5f874a3769d485` → `a8c8074a964d2a20` | ✓ 非 byte-identical（B129/B127 零翻转教训） |

探针实测（`D:/Temp/r133/scratch/probe_case2c.py`，s9 的 `f10`）：`loop_headers=[14,20]`，只有 20（FOR_ITER）
∈ try 体块集 ⇒ 参与豁免；`_try_nested_loop_body_blocks` = `[20,22,62,86,92,94,112,114]`（整条 for 体，
含两个死胡同 `RETURN_VALUE` 块 92/112）⇒ `VETO=False`。14（外层 while 头）不在 try 体块集内 ⇒ 外层循环
成员身份不参与豁免（否则 try 体外层循环里的 return 会被一并豁免，那是放宽而非封闭）。

## 3. Case 1（`load_daily :: <module>`）— 已落地并实测

**宿主**：`core/cfg/region_analyzer.py:_compute_arm_level_join` 的认领循环（HEAD `:3332-3349`）+ 新方法 `_armjoin_is_dual_role_meeting`。
**判据 (4c)（一句话）**：`len(_arms)==2` ∧ 候选 J 的前驱分箱恰为 `{0,1}`（两臂各一条入边，无 E/S/N 箱）∧ J 不在任何臂内嵌套子
区域块集内（`J ∉ _sub_arm`）∧ 「一臂的尾块以无条件前向跳转（`JUMP_FORWARD`/`JUMP_ABSOLUTE`，目标偏移恰为 J）落在 J ∧
另一臂的尾块块末既非任何跳转族也非 return/raise 终态、其唯一正常后继即 J（fall-through）」且两条入边分属**不同**臂
⇒ J 即两臂同层最近汇合块，先到先得认领，BFS 不再向外走到那条只靠跨越本作用域的跳过边（`@104→@2768`）拿到 E 证据的
外层块。与发射端 `[R9-B124]/[R9-B125]`（`region_ast_generator._split_arm_at_chain_exit` 条件 (b) 读同一条「臂以无条件前向
跳转落在 merge_block」事实）对齐为同一判据的两半：归约端认领、发射端切开，未另立并行尺子，未读外层区域块集（C2/C1）。

### 3.1 半票 A/B 读数（case 1 单独 = HEAD + 仅 case 1）

| 靶 | HEAD | +case 1 单独 | +case 2 单独 | 两者 |
|---|---|---|---|---|
| `fly/dumpload/load_daily.pyc` | 26/27 failure | **27/27 success** ✓门禁 1（整文件翻绿） | 26/27（不变） | 27/27 |
| `IQCommon/util/trade_info_utils.pyc` | 37/41 | 37/41（4 个失败单元名不变） | **38/41** ✓门禁 2 | 38/41 |
| 九臂（r1-r4 + s5-s9） | 17/18 | 17/18（s9 仍红） | 18/18 | **18/18** ✓门禁 3 |
| load_daily 产物 sha256 | `63c013c960cf17f3` | `6f012ee06293d18e` **变了** | `63c013c960cf17f3` 未变 | `6f012ee06293d18e` |
| trade_info_utils 产物 sha256 | `bb5f874a3769d485` | `bb5f874a3769d485` 未变 | `a8c8074a964d2a20` **变了** | `a8c8074a964d2a20` |

⇒ 两半各自移动自己靶的字节、对方靶逐字节不动（Q3「两处独立宿主」在产物层再证一次）；不存在 B129/B127 那种
「半票产物 byte-identical」的空转。s5（case 1 负对照，NCPD 直接给对 merge）仍 2/2 ⇒ (4c) 没有把健康例推出界。
