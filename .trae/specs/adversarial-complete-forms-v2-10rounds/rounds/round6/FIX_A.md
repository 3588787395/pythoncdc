# Round 6 · Task 6.2（识别层）· 修复工程师子代理 A 交付

## 落地声明（I.6）

**注释已落地**。本次为 I.7 注释合规整改（纯 docstring 修改），非代码逻辑变更。

grep 证据（`C 条款：C1——` 命中 10 行，恰为十族识别方法 docstring 内各一条）：

```
4275:C 条款：C1——判据只来自本层块对象结构事实（回边 src/tgt、header 末条 FOR_ITER/
8263:        C 条款：C1——判据只来自本层块对象结构事实（异常表 (start,end,target,depth)
13405:        C 条款：C1——判据只来自本层块对象结构事实（BEFORE_WITH/BEFORE_ASYNC_WITH/
14067:        C 条款：C1——判据只来自本层块对象结构事实（MATCH_*/COPY+COMPARE_OP 等
16838:C 条款：C1——判据只来自本层块对象结构事实（末条前向条件跳转 opcode、恰 2 个
17602:        C 条款：C1——判据只来自本层块对象结构事实（COPY(arg=2)+COMPARE_OP 指令对、
18122:        C 条款：C1——判据只来自本层块对象结构事实（末条 FORWARD_CONDITIONAL_JUMP_OPS
22706:        C 条款：C1——判据只来自本层块对象结构事实（condition_block 末条条件跳转
25881:- C 条款：C1——判据只来自本层块对象结构事实（SHORT_CIRCUIT_JUMP_OPS /
31035:        C 条款：C1——判据只来自本层块对象结构事实（单块 entry/blocks 成员关系、
```

- 基准 HEAD：`ce19bf05`
- 改动范围：仅 `core/cfg/region_analyzer.py`（10 个 `_identify_*_regions` docstring）
- `git diff --stat`：`1 file changed, 70 insertions(+)`，**0 deletions**，全部落在 docstring 内
- 未触碰 `core/cfg/region_ast_generator.py`；未新增/删除方法；未新增 self 跨方法状态；未引入硬编码深度上限；未使用禁用前缀

---

## 逐方法修复表

> 锚点行 = 当前（修复后）行号；`C 条款`行 = 新增声明所在行；「原结尾」= 新增前 docstring 收尾句。

### 1. `_identify_loop_regions`
- 锚点行：def `4171`；C 条款 `4275`
- 原结尾（I.1 四原则）：`本方法遵循区域归约算法 4 核心原则: 自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（回边 src/tgt、header 末条 FOR_ITER/GET_ITER 等 opcode、前驱集合、异常边）；C2——嵌套 IfRegion/TryExceptRegion/WithRegion/MatchRegion/AssertRegion 经 add_child/entry 抽象节点挂到 LoopRegion，父区域不展开循环体内部（每块唯一归属）；C3——识别须参考非局部信息：回边合法性依赖全函数级支配关系 dom_analyzer.is_dominator(header, src)，出口/else 候选若是已被先归约结构化区域登记的入口块（_is_post_merge_sibling_head 跨区域 entry 反查），由 R09 边界规则显式排除并归还其归属结构；二者共同以 block_to_region「先到先得」登记封闭归一，避免循环与尾随 IfRegion 双重归属。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（4276+ 自然循环/dom 校验/子集过滤/R09 排除）逐段一致。

### 2. `_identify_try_except_regions`
- 锚点行：def `8178`；C 条款 `8263`
- 原结尾：`当前测试矩阵通过率: 100%（try_except 230/230）。本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（异常表 (start,end,target,depth) 条目、handler 入口首指令 opcode、excluded_offsets 区间包含判定）；C2——内层 try / 配对 except 经 handler 入口被外层抽象节点消费，父级不窥视子 handler body 内部；C3——须参考非局部信息：handler 类型与 try 范围来自异常表，同级/更深层 handler 偏移经 excluded_offsets 结构包含显式排除，已被其它区域（如 WithRegion 的 WITH_EXCEPT_START 块）占用的块由 block_to_region「先到先得」守卫排除（TRY 优先级最高，确保 try 块不被下游 LOOP/IF 抢走）。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（异常表解析/handler 分类/包含判定/block_to_region 守卫）一致。

### 3. `_identify_with_regions`
- 锚点行：def `13275`；C 条款 `13405`
- 原结尾：`当前测试矩阵通过率: 100%（with_region 191/191）。本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（BEFORE_WITH/BEFORE_ASYNC_WITH/WITH_EXCEPT_START 等 opcode、异常表 [start,end) body 范围、后继边性质）；C2——with body 内嵌套区域经 add_child/entry 抽象节点被本 WithRegion 消费，父序列不展开其内部；C3——须参考非局部信息：with 出口块（with 之后第一块）归父序列所有，本区域仅以 exit_block/exit_via_jump 引用而不改其归属；cleanup 扫描遇条件跳转结尾块（兄弟 IfRegion 条件块）即终止，并以 block_to_region「先到先得」排除已被非-WithRegion 占用的块（避免出口块被误收为清理块）。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（BEFORE_WITH 扫描/异常表 body 收集/_find_with_exit_block 出口引用/合并）一致。

### 4. `_identify_match_regions`
- 锚点行：def `13977`；C 条款 `14067`
- 原结尾：`...本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（MATCH_*/COPY+COMPARE_OP 等 opcode、条件跳转目标、case body 成员关系）；C2——case body 内嵌套区域经 add_child/entry 抽象节点被 MatchRegion 消费，父区域不展开子 match 内部；C3——须参考非局部信息：入口 subject_block 经前驱反查回溯（前驱关系），起始 claimed 集合取自 block_to_region（先到先得，先到者不覆盖既有归属），幻影 guard 经 B74 臂终止跳转目标重放校验后显式撤销（目标落入 case 体块集即判伪）。`
- 六项复核：①②③③④⑤⑥ 齐全，与代码（双相位扫描/_mr_collect_case_body/B74 校验/claimed）一致。

### 5. `_identify_assert_regions`
- 锚点行：def `16690`；C 条款 `16838`
- 原结尾：`当前测试矩阵通过率: 100%（assert 在 basic 测试集内通过）。本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（末条前向条件跳转 opcode、恰 2 个 conditional_successors、LOAD_ASSERTION_ERROR 指令），本方法不依赖支配树/回边；C2——message_block 可为嵌套 TernaryRegion.entry，AssertRegion 经该入口引用子区域，不窥视其内部；C3——唯一跨区域接触 = message_block 与嵌套 TernaryRegion.blocks 的重叠，由 block_to_region「先到先得」（仅 not in 时登记，不覆盖既有归属）+ analyze() 后段 _region_overlaps_with_ternary 合法嵌套特例显式守卫，无其它非局部引用。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（模式匹配/F4 前缀切分/message_block 重叠特例）一致。

### 6. `_identify_chained_compare_regions`
- 锚点行：def `17501`；C 条款 `17602`
- 原结尾：`...本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（COPY(arg=2)+COMPARE_OP 指令对、fallthrough 后继、conditional_successors）；C2——嵌套区域经 add_child/entry 抽象节点被本 IfRegion 消费，父区域不感知 chained_compare_blocks 内部结构；C3——须参考非局部信息：候选块若已被 Phase 1 区域（loop/try/with/match/assert）占用，则由 claimed 集合（取自 block_to_region）显式跳过；链追踪以「存在后向边」终止，避免侵入循环结构。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（_is_chained_compare_header/_detect_chained_compare_pattern/claimed）一致。

### 7. `_identify_conditional_regions`
- 锚点行：def `17976`；C 条款 `18122`
- 原结尾：`当前测试矩阵通过率: 100%（if_region 311/311）。本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（末条 FORWARD_CONDITIONAL_JUMP_OPS opcode、跳转目标、then/else 分支成员关系）；C2——嵌套 IfRegion/BoolOpRegion/TernaryRegion 等经 add_child/entry 抽象节点被父区域消费，父区域不展开 then/else/elif body 内部；C3——须参考非局部信息：分支收集边界经 _get_enclosing_structural_boundary_stop 回溯外层结构区域（try/loop）边界并显式传播（仅传播边界，不改 block_to_region 直接归属），_should_skip_block_for_if_region 以 LoopRegion.condition_block/header/back-edge 身份排除，block_to_region「先到先得」排除已被 loop/try/with/match/boolop/ternary 占用的块。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（Step5 [C1] 内联、边界传播 19264、_should_skip_block_for_if_region）一致；内联 `[C1]`（原 17978）保留。
- 升格说明：原 Step5 内联单条 `[C1]` 已整合进本条完整 C1/C2/C3 声明。

### 8. `_identify_ternary_regions`
- 锚点行：def `22572`；C 条款 `22706`
- 原结尾：`...本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（condition_block 末条条件跳转 opcode、true/false 值块的 JUMP_FORWARD/fallthrough、merge_block 身份）；C2——嵌套 BoolOpRegion/嵌套三元/条件链经 entry 抽象节点被父区域引用，父区域不展开 value/merge 块内部；C3——须参考非局部信息：候选头块若为既有区域的 entry/condition_block（chained_compare IfRegion.entry / AssertRegion.entry / LoopRegion.condition_block / 落入 LoopRegion.blocks）则经 self.regions 显式拒绝，块已归属时委托 existing.can_be_ternary_header 多态守卫，merge 汇合引用 + 后段 _ternary_block_sets 重叠过滤（AssertRegion.message_block 重叠为合法嵌套特例）。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（_can_be_ternary_header 的 self.regions 检查/existing 多态判定）一致。

### 9. `_identify_boolop_regions`
- 锚点行：def `25714`；C 条款 `25881`
- 原结尾：`- 本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `- C 条款：C1——判据只来自本层块对象结构事实（SHORT_CIRCUIT_JUMP_OPS / FORWARD_CONDITIONAL_JUMP_OPS 块末 opcode、后继身份、block_to_region 归属表）；C2——本 BoolOpRegion 作为单一表达式节点经 entry 被父 IfRegion/LoopRegion 引用，内部 op_chain 操作数块不展开；C3——须参考非局部信息：claimed 集合取自 block_to_region + existing_regions（先到先得），Step 5 残链超越替换的链块所有权经 block_to_region 显式校验（仅允许「未认领 / 本循环 condition_block 惯例 / 待超越残链」三类），loop_condition_blocks / match_case_body_blocks 允许重叠为显式认领例外。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（claimed 机制/Step5 残链超越替换/重叠白名单）一致；内联 `[C3]`（原 25707）保留。
- 升格说明：原 Step5 内联单条 `[C3]` 已整合进本条完整 C1/C2/C3 声明。

### 10. `_identify_sequence_regions`
- 锚点行：def `30943`；C 条款 `31035`
- 原结尾：`...本方法遵循区域归约算法 4 核心原则: ...父引用子入口。`
- 新增 C 条款原文：
  `C 条款：C1——判据只来自本层块对象结构事实（单块 entry/blocks 成员关系、_is_return_none_block 指令判定），不构造跨块 Sequence；C2——BASIC 区域作为叶子抽象节点经 entry 被父区域引用，父区域不展开 {block} 内部；C3——须参考非局部信息：仅读取 block_to_region 归属表「先到先得」以排除已被结构化区域抢占的块，不读写任何其它区域内部，无跨层窥视。`
- 六项复核：①②③④⑤⑥ 齐全，与代码（残余块兜底/单块即一区/block_to_region 跳过）一致。

---

## 自测命令与读数

| # | 命令 | 读数 |
|---|------|------|
| 1 | `python -m py_compile core/cfg/region_analyzer.py` | rc=0（PYCOMPILE_RC=0） |
| 2 | `python -c "import core.cfg.region_analyzer"` | `IMPORT_OK F:\Downloads\pythoncdc-main\core\cfg\region_analyzer.py` |
| 3 | BOM 复核 | `head3=efbbbf`，全文 `efbbbf` 计数 = 1（单头） |
| 4 | `git diff --stat -- core/cfg/region_analyzer.py` | `1 file changed, 70 insertions(+)`，0 deletions |
| 5 | `grep "C 条款：C1——"` | 命中 10 行（十族各一条） |
| 6 | RV2 抽样·quotation.pyc | HEAD 基线 152/153；修复后 152/153（**不变**，唯一失败 change_his_to_forward 与基线一致） |
| 7 | RV2 抽样·quote_handler.pyc | HEAD 基线 78/79；修复后 78/79（**不变**，唯一失败 get_kline_local 与基线一致） |

- RV2 判据：`scripts/pyc_verify.py single`（ruler = pylingual `equivalence_check.py::compare_pyc`）。
- 基线获取方式：`git worktree add <temp> HEAD` 检出 `ce19bf05` 干净树，跑同一 pyc（同判据），跑毕 `git worktree remove` 清理；临时 worktree 已删除，`git worktree list` 仅余既有项。
- 证据文件：`rounds/round6/r6v6fixa_selfcheck.json`、`r6v6fixa_quotation_verify.txt`、`r6v6fixa_quote_handler_verify.txt`、`r6v6fixa_quotation{OK.py,.pyc}`、`r6v6fixa_quote_handler{OK.py,.pyc}`（均为新增前缀文件，未覆盖任何既有文件）。

## 约束遵守

- 仅改 `core/cfg/region_analyzer.py`（10 docstring）；未碰 `region_ast_generator.py`
- BOM 保持单头（`efbbbf`，计数 1）
- 未手改任何 `*OK.py`（RV2 产物为工具 regen，且写入 `r6v6fixa_*` 新前缀路径）
- 未 git add / commit / 回滚
- 未新增/删除方法、未新增 self 跨方法状态、未引入硬编码深度上限、未使用禁用方法前缀