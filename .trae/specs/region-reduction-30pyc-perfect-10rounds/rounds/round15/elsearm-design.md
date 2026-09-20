# Round 15 B 项设计（else/then 臂的「嵌套区域边界」归属）

## 选靶（一处修复翻多个 pyc：重复源效应）
| 靶函数 | 受影响 pyc | 严格尺子症状（实测） |
| --- | --- | --- |
| `ArgumentChecker._is_valid_quarter` | `IQCommon/arg_checker.pyc`、`IQData/utils/arg_checker.pyc`、`IQEngine/utils/arg_checker.pyc`（**×3**，现 48/49） | `seq_len orig=90 decomp=88`，少的正是 `LOAD_FAST valid; POP_JUMP_FORWARD_IF_FALSE` |
| `PluginManager.set_engine` | `IQEngine/core/plugin_manager.pyc`、`IQData/manager/plugin_manager.pyc`（**×2**，现 8/9） | `target_diff #60 JUMP 终点 orig='time' decomp='system_log'` |
| r14j_09 复现 | `test_repros/round14_join/r14j_09_try_in_else_arm.py` | `seq_len orig=49 decomp=47`（本轮唯一残留 MISMATCH） |

## 实测结构（`_is_valid_quarter`，工具见文末）
```
if value is None: valid = True
else:
    valid = isinstance(...) and value[-2] == 'q'   # BoolOpRegion@12，值上下文
    if valid:                                      # IfRegion@86  ← 整条 if 丢失
        try: ... except: valid = False             # TryExceptRegion@94，parent=IfRegion@86（登记正确）
if not valid: raise ...                            # IfRegion@290
```
- `BoolOpRegion@12.blocks=[12,64,86]`，`merge_block=86`（块内 `STORE_FAST valid | LOAD_FAST valid | POP_JUMP_FORWARD_IF_FALSE 99`）
  ⇒ 块 86 是「双角色块」：既是 BoolOp 的归并点，又是 `if valid:` 的入口/条件块（Round 14 例外 3 允许）。
- `IfRegion@86.blocks=[86,92,94,152,162,166,168,222,232,236,238]`。
- **决定性证据**：`_process_if_blocks(region=IfRegion@0, branch='else')` 收到的块表是
  `[92,94,152,162,166,168,222,232,236,238]` —— 即 **IfRegion@86 的全部内部块，但不含入口块 86**。
  于是臂内经 `_try_entry_generate` 直接派发**孙辈** `TryExceptRegion@94`，把它挂到祖父的臂上；
  IfRegion@86 随后在 `generate()` 主循环 `region_ast_generator.py:1570-1577`
  （`all(b in self.generated_blocks for b in region.blocks) → continue`）被跳过。
  直接 wrap 验证：本函数内 `_generate_if` 只对 entry=0 与 entry=290 调用过，**从未对 86 调用**。

## 违反的原则
原则 4：「归约后父区域的 then/else 列表引用**子区域的入口**，而不是子区域的所有块」。
现状是父臂吸入了子区域的内部块（过晚止步）；r14j_09 是同一判据的**反向**症状
（`IfRegion@84 blocks=[84,90] then_blocks=[90]` 无 else_blocks，而 `TryExceptRegion@100`
作为**兄弟**抢走 `[98,100,…]` 且 `parent` 为空 —— 过早止步）。同一条臂边界判据的两面。

## 候选修复位点
1. **分析器（首选，原则层）**：`region_analyzer._collect_branch_blocks(entry, merge, stop_set)`
   （`:25523`，自陈「纯拓扑收集，不使用 block_to_region 排除，区域归属冲突由上层调用者处理」）
   的调用方在收集 IfRegion 臂时，把「尚未发射的其他结构区域入口块」并入 stop_set
   （多态钩子已存在：`Region.get_if_branch_boundary_stop`，基类 `:282`，
   `LoopRegion` 覆写 `:527`）。臂据此以**子区域入口**结案，内部块归还子区域。
2. **生成器（必须同步）**：`_process_if_blocks` 的 `_nested_if_entry_generate` 判据
   `:19967` `_nr_blocks_in_set = all(_nb in _block_set for _nb in _nr.blocks)`
   与臂止步改动冲突（子区域内部块本就不在父臂块表里），需改为
   「入口块在父臂块表内即由子区域负责其内部块」；否则改动 1 之后仍走
   `_nested_if_entry_skip`（`:19971`）而继续丢失。
   同时 `generate()` 主循环 `:1572` 的 `all(blocks generated)` 判据必须以
   **「该区域自身是否已发射」**为准（`_generated_regions` 台账），
   否则子区域先归约会把父结构一并跳过——这正是 A2 系列在发射权维度上处理过的同一类量纲错配。

## 定稿（第二轮取证后改判：**分析器无罪，缺陷全在生成器 else 臂收集**）
臂块表其实**完整**：`IfRegion@0.else_blocks=[12,64,86,92,94,…,238]`（含入口块 86）。
把它切成 `[92,…]` 的是生成器 `_if_generate_else_branch` 内的三阶段收集
`_try_collect_c3`（`:14591-14651`）：

- 阶段 1 复合子区域（Try/With/Loop）：If@0 无直接 Try 子节点 ⇒ 无；
- 阶段 2 值区域：`BoolOp@12` 入选，`_claimed_blocks_c3 ∪= {12,64,86}`（`:14631-14633`）；
- 阶段 3 IfRegion 子区域：`If@86` 被 **`:14596 if child.entry in _claimed_blocks_c3: return False`**
  否决（86 正是阶段 2 里 BoolOp 的 merge 块）⇒ If@86 不进 `_reachable_children_c3`；
- 发射单元切分（`:14668-14679`）：64/86 因 `_blk in _child_block_set_c3` 被 `continue` 丢掉
  （`:14674`），剩下的 `[92,94,…,238]` 作为 `'seq'` 单元交给 `_process_if_blocks`
  （`:14696`）⇒ 臂内 `_try_entry_generate` 直接派发**孙辈** Try@94。

`:14640-14647` 的 R36 注释给出了这条否决的原始动机：值上下文 chained-compare IfRegion
的 `merge_block == BoolOp entry`，若先收 If 会挡住 BoolOp。但**该情形已由
`:14605-14620` 的 `chained_compare_ops` 专用判据独立处理**，因此这条「入口被值区域认领即否决」
的通用否决是过度收窄，与 Round 14 分析器例外 3（`_value_merge_hosts_next_if`：允许
「值上下文 BoolOp 的 merge 块 == 下一条 if 的入口块」双角色）**直接矛盾**：分析器放行、
生成器否决 ⇒ 中间 if 消失。

### 两处改动（均在 `core/cfg/region_ast_generator.py`）
- **H1**（`:14591-14598`）：`_try_collect_c3` 的否决改为「仅当 entry 被别人**作为自身入口/主体块**
  占用才否决」。实现：阶段 2 收集时另记 `_value_merge_blocks_c3 = {值区域的 merge_block}`；
  判据改为 `child.entry in _claimed_blocks_c3 and child.entry not in _value_merge_blocks_c3`。
  语义＝原则 4「父臂引用子区域入口」+ 例外 3「双角色块是引用不是占用」；
  chained-compare 形态仍由 `:14605` 原样否决，不放宽。
- **H2**（`_if_generate_normal` 的 `_boolop_merge_owner` 分支，`:16418` 附近）：owner 若已在
  `self._generated_regions` 中（臂已按单元顺序把赋值发过），**不得再次 `_generate_boolop`**，
  只做 `_generated_regions.add` + `_if_extract_cond_instructions(cond_block, region,
  boolop_merge_target=…)` 取回块尾条件。这是 H1 的必要配套，否则 `valid = …` 会重复发射
  （r15a_09 那类 +9 症状即重复族）。

`generate()` 主循环 `:1572` 与 `_process_if_blocks` `:19967` 本轮**不动**：
H1 生效后 If@86 由臂单元直接派发，不再经过主循环，也就不依赖那两处判据。


## 风险与不变量
- 双角色块（86 同时属于 BoolOp@12 与 If@86）是例外 3 允许的既有语义，改动不得撤销它；
  前缀发射权仍由 A2 的 `prefix_emitted_upto` 记账。
- 严防重复发射：If@86 一旦被派发，其内部块必须整体由它拥有，父臂不得再经
  `_try_entry_generate` 取走同一 Try（`id(region) in self._generated_regions` 是唯一权威判据）。
- 验收顺序不变：`test_repros/round14_join` 全绿（r14j_09 → SENTINEL）
  → quotation 单验 → 全量产物门（`_r13_gate.py`，自动回滚）。

## 复现/取证工具（全部只读，产物一律写到 D:/Temp）
`r15_dump_regions.py`（区域图）、`r15_tr_pib.py`（臂块表 + 每块 entry/owner 区域）、
`r15_tr_who.py`（谁派发了某区域：生成器内调用链）、`r15_seqdiff.py`（单函数指令级对齐差异）、
`r15_ab3.py`（换 core 文件做 A/B，退出复原并核对 sha）。
## 定稿 → 实测（落地前的 dry-run，core/ 未被写入）
落地方式：`D:/Temp/r15_h1_patch.py`（H1.1/H1.2/H1.3 + H2.1..H2.5，六个字节级 hunk，
断言 base sha `f8debe9af6b60b20`、锚点唯一、CRLF/BOM 不变、补丁文本可 compile）；
验证方式：`D:/Temp/r15_seed_run.py` / `D:/Temp/r15_h1_dryrun.py` 把打完补丁的**副本**
（`D:/Temp/r15_h1_copy.py`）以 sys.modules 播种进 `core.cfg.region_ast_generator` 后跑
`test_repros/*/run_all.py` —— 全程不写仓库，因此可与只读诊断子代理并行。

### H1 单独落地不足以复原语句（实测否证了设计稿的「H2 只是配套」判断）
```
  collect BoolOpRegion@12  ret=True
  >>> generate IfRegion@76            # H1 之后区域被收集、被派发
   <- IfRegion@76  list(0)             # 但 _generate_if 仍把它扔掉
    => else_stmts=1                     # 只剩赋值语句
```
`D:/Temp/r15_tr_c3_01_patched.txt`。真正的丢弃点在 `:11090`（A1b/A2b 的 carve-out）：
`_boolop_merge_owner_for(region, include_generating=True)` 对**已发射完毕**的 owner
（兄弟单元）返回 None ⇒ `return []`。⇒ H2 必须同时改「识别」与「发射权」两处，
设计稿里只写了 `_if_generate_normal` 半边。

### H2 的最终形态（与设计稿的差异）
1. `_boolop_merge_owner_for` 增加 `include_generated` 形参：把「owner 是否已被发射」
   从**识别判据**里摘出来 —— 双角色块的存在性只取决于 `owner.merge_block is cond_block`；
2. `:11090` carve-out 传 `include_generated=True` ⇒ 区域不再被丢弃；
3. `_if_generate_normal` 的祖先兜底后加 `else` 分支：`_bo_sib` 命中且
   `id(_bo_sib) in self._generated_regions` ⇒ 置 `_boolop_owner_emitted_by_ancestor`，
   即 **不再** `_generate_boolop`（原则 2：一条语句一个发射者），但仍把
   `boolop_merge_target=owner.value_target` 交给 `_if_extract_cond_instructions`，
   让条件从块尾 store 之后起算。
设计稿中「`:1572` 主循环 / `:19967` 不动」的约束成立：全量 A/B 无任何文件变差。

### 量化结果（唯一真值尺子，函数级 identical 数；产物写 D:/Temp，不动仓库 OK.py）
`D:/Temp/r15_corpus_check.py` + `D:/Temp/r15_ab_{base,patched}_31.txt`
（31 文件门名单，`r15_1fix_targets.txt`）：

| 指标 | 修复前 | 修复后 |
|---|---|---|
| 31 文件函数级 identical 合计 | 445 | **447** |
| `IQData/utils/arg_checker.pyc` | 38/39 | **39/39** |
| `IQEngine/utils/arg_checker.pyc` | 42/43 | **43/43** |
| `IQCommon/arg_checker.pyc` | 48/49（deficit 2 条） | 48/49（deficit 16 条） |
| 其余 28 文件 | — | 逐个不变 |

⇒ 本轮至少解决一个 pyc 的要求由**两份重复源 arg_checker** 满足；
`IQCommon` 变差（仍不干净）见下，记为下一轮靶子。

### 三个残留（都已定位，均**不**由 H1/H2 引入）
- **IQCommon `_is_valid_quarter` / r15a_01 / r15a_02**：`if` 已找回，但 then 臂内的
  `TryExceptRegion@84` 不是 `IfRegion@76` 的 children（分析层未建父子边），
  `_if_generate_then_branch` 先把块 84 作为 BoolOp 归并点标记 generated
  （`D:/Temp/r15_tr_gs_01_patched.txt` 栈：`_generate_boolop_impl → _if_generate_then_branch:14054`），
  `_try_entry_generate` 因 `b in self.generated_blocks` 空转
  （`D:/Temp/r15_tr_try_01.txt`）⇒ try/except 整体丢失。修复属**分析层嵌套**（原则 3）。
- **r15a_08**：`if flag != 'q':` 仍被 `:10969` 的 R36 否决 —— 豁免分支 (b) 依赖
  `region.guard_clause_prefix_end`，而分析层 `_value_merge_hosts_next_if` 只在
  「后继 if 条件是裸同名变量」时写它。比较式条件拿不到豁免 ⇒ 分析层判据过窄。
- **r15a_09**：顶层语句序列中的双角色块把赋值与 `if` 条件各发一遍（orig 39 / decomp 48），
  与 else 臂无关，是另一条发射链的重复族。
