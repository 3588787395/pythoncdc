# Round 23 结果（OUTCOME）

一条线：**把 `clock_worker` 的 −197 塌陷拆开，先解掉其中唯一使产物语义错误的那一层**。
落地 R23-A（or-extension 臂状态 callee-saved）＋ R23-B（loop 条件块前导语句发射权归父序列）。
门禁顺序：最小复现电池（对落地字节复跑）→ 靶子 `single` → `quotation.pyc` 零副作用 →
全量 `batch --all --round 23` → `stats`。设计稿 `arm-design.md`，落地与实测 `fixes.md`，
最小复现集 `test_repros/round23_clobber/`（16 复现/对照 + `run_all.py` + `ANALYSIS.md`，本轮首次入库）。

## 一、解决了什么

1. **Round 22 移交项（SubTask 22.9 ①）的根因被改判并修掉**。旧标题假设「截断 BoolOp 链后父臂
   未收养子表达式」被实测否证（402 文件 A/B 只动 1 文件；6 个手写 or-extension 形状两核产物逐字节
   相同）。真机制是 `self._or_then_block/_or_else_block/_or_rhs_block` 挂在 `self` 上，被**自己递归
   下去的那一层**在 `_if_generate_normal` 开头无条件复位 ⇒ 父区域 else 臂静默丢弃。
2. **`clock_worker` 由 −197 塌陷回到 +16**：`realtime_event_source` 严格尺 `sad 198 → 12`
   （R23-A）→ 17（加 R23-B）。语料级 `Σsad 1771 → 1585`（−186，`Σn_ok` 6004 不变）。
3. **Q1（`dt = datetime.datetime.now()` 整条被丢弃）被消掉** —— 本轮唯一使产物**语义错误**的缺陷
   （`dt` 在该点未绑定）。R23-B 用既有同层构件 `_split_block_condition_prefix`（块内栈深切点）＋
   `_build_statements_from_instructions` ＋ Round 15 指令粒度台账 `_register_prefix_emitted`，
   把「祖先循环 header 块」内的前导语句交还父序列，发射在 `While` 节点之前。
   三例最小复现 `b07/b08/b11`（各 −3）由 FAIL 转 OK，判别子 `b09`（内层是 `if`）与 6 条 CONTROL 零变化。
4. **触发面实测**：两个候选核在 402 个 pyc 里**各自只改变 1 个文件的产物**（同一个
   `realtime_event_source`）；谓词前驱形状在 39 个文件出现，38 个逐字节不变，其中 14 个当时已
   完全匹配者**全部逐字节零变化**（`arm-design.md` §四 (iii) 的硬要求）。
5. **索引继续留在实测状态**：`batch --all --round 23` 复验 402/402、`failed_pyc 0`，
   402 条 `last_tested_round` 全部由 22 推进到 23，**实质字段（`function_count` /
   `matched_functions` / `decompile_status`）改动条目 0 条**。

## 二、门禁原始输出（顺序与判据）

0. 电池（16 case ＋ 语料锚点，`--cores head=<mirr/head23>,landed=<mirr/landed23>`，
   `landed23` 由**已落地工作树**拷贝而来且 42 个文件 sha256 与工作树逐一对应；零仓库写入）：
   `fixed by landed = 3 / broken = 0`、`.py` 形状 `Σ|d| 21 → 12`、锚点 `198 → 17`、
   `G0=True G2=True G3=True → GATE: PASS`（`G1=NOT EVALUATED`：R23-A 在 `.py` 形状层不可测，
   非虚报）。候选阶段另跑 `head/c1a/r23b` 三核电池，同值。
1. 靶子 `single`（官方尺）：
   `realtime_event_source.pyc` → `partial 11/12 91.67%`，唯一缺陷
   `clock_worker orig=1275 decomp=1291 jump_diffs=15 true_diffs=480`，
   `first_diff` 由 `index=666`（`LOAD_GLOBAL datetime` vs `LOAD_FAST dt`）后移到 `index=794`
   ⇒ 替换门禁 (i)(ii) 通过。**本轮不翻转该 pyc**（设计 §四已预告）。
2. `quotation.pyc`：`partial 142/143 99.30%`，唯一缺陷
   `change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377` —— 与 Round 21/22
   记录逐字相同，且 `quotationOK.py` 在工作树里**未被改动** ⇒ 本轮零副作用。
3. `batch --index pyc_index.json --all --round 23`：402/402、`failed_pyc 0`。
4. `stats --index pyc_index.json`：

```
  total_pyc: 402   verified_pyc: 402   ok_pyc: 362   partial_pyc: 40   failed_pyc: 0
  total_functions:       5746
  matched_functions:     5633
  cumulative_match_rate: 98.03%
```

对外序列与上一轮同值（本轮为**零官方增益**）：索引条目实质字段改动 0 条、
`function_count` 逐条不变、Σ=5746、条目数 402、added/removed=0（脚本复核）。
区别只在于这个 5633 是用本轮落地核重新复验出的实测值。

## 三、代价与残留（如实登记）

1. **严格尺上唯一一处读数变差，且是本轮修复的必然后果**：`realtime_event_source` 的 `sad`
   `12 → 17`（`clock_worker` 长度 `1287 → 1292`，官方 `decomp` 计数 `1286 → 1291`）。
   机理：`_r10_strict_check.py:105-106` 在长度不等时立刻 `return 'seq_len'`，逐 token 与跳转落点
   比较不执行 ⇒ 补回缺失的 6 条之前，D2（过量发射）与 D3（同形块换位）根本不被计分。
   本轮据此**弃用 Σ\|orig−decomp\| 作门禁**（`arm-design.md` §四），改用 (i) 产物含该语句 /
   (ii) 官方 `first_diff` 后移 / (iii) 其余 401 文件不回退，三条均已实测通过。
2. **`clock_worker` 仍未收口**，残余两层：D2 过量发射（+16）、D3 同形块换位
   （`ANALYSIS.md` §3.3 给出 token 级实测；§3.4 说明它当前不被任何尺子计分）。
   顺序上 D2 已**首次可见可测**，是 Round 24 的直接入口。
3. `realtime_event_source` 官方读数不变（`partial 11/12`），故索引该条 `11/12` 未动；
   `get_one_event 19→20`（过量发射族，Round 22 登记项）逐字未动。
4. Round 22 电池 5 项残留本轮未触碰：`r22_23`（`A and B or C`）、`r22_24`（`X or (A and B)` 括号形）、
   `r22_25`（`while A and b or C and D` 循环 test）、`r22_26`（`or` 后接 `and` 臂）、
   `r22_27`（`persist` 在 while 内 73→65）。
5. 过量发射族其余 3 项未动：`executor.check_before_trading 243→254`、`data_proxy.get_bar 86→90`、
   `replace_utils.decrypt_database_url 295→324`；quotation `change_his_to_forward` seq_len +1、
   `handlers.pyc TWHThreadController._target 192→190`、`api_base.get_history_df`（Round 22 §四-1）
   与 `f89b85f2` 遗留退化（`trade_info_utils −2`、`custom_tools −1`）照旧。
6. **R23-A 在 `.py` 层不可测**这一事实进方法论：callee-saved 类修复的验收只能靠语料锚点 +
   逐文件触发面（本轮 = 1/402），电池的 `G1` 因此显式打印 `NOT EVALUATED` 而非谎报 True。

## 四、提交物

核：`core/cfg/region_ast_generator.py`（sha256 前 16 位 `a203dd17fe82f824 → a365c378e6a40fed`，
纯 CRLF、UTF-8 BOM 保持；`core/cfg/region_analyzer.py` 本轮未动，仍为 `59b70fa360d19ad0`）。
产物：1 个 `*OK.py`（`realtime_event_sourceOK.py`，由 `single`/`batch` 按当前核重写，`+54/−17` 行，
本轮零手写）。记录：`pyc_index.json`（402 条 `last_tested_round=23`，实质字段 0 改动）、
`test_repros/round23_clobber/`（首次入库：16 case + `run_all.py` + `ANALYSIS.md`）、
`rounds/round23/{arm-design.md,fixes.md,OUTCOME.md}`、`tasks.md`（Task 23）。
