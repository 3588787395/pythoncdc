# A2 正解设计（Round 14 · 区域归属层）—— 前置语句发射权的登记方案

## 现状：判据为什么测不出来
`core/cfg/region_ast_generator.py:31200` 用块级布尔判据
`if first_chain_block in self.generated_blocks: pre_stmts = []` 决定「本区域是否还要
发射链首块的前置语句」。而 `generated_blocks.add(...)` 在该文件里有 **690 处**调用点，
既包含「语句序列已由本块发射」的路径，也包含「本块指令被父表达式/条件消费」的路径
（`generate()` 入口的 Ternary/BoolOp「被父消费」分支只登记块、不发射语句）。
⇒ 该集合在语义上不可分辨，任何在其上的细化都不成立。

已实测失败的两条细化（Round 13，证据见 `rounds/round13/OUTCOME.md` §四）：
* (a) 改判「每条前缀指令偏移是否都在 `generated_offsets`」——该集合只零散登记
  `block.start_offset`，对任何多指令块恒为假 ⇒ 凡块被标记就重新提取整段前缀，
  `create_order` / `trade` / `base_validator` / `itn` / `json_persistance` /
  `quotation` 共 **6 处整块语句重复发射**；
* (b) 新增 `statement_emitted_blocks` 台账（在 `_generate_block_statements` 漏斗与
  `_generate_block_statements_body` 入口各登记一次）——6 处症状一字不变，
  证明 `create_order` 的第一份语句**不经该漏斗产出**。

## 正解：把归属登记降到**指令粒度**，且登记量与消费量的单位一致
关键观察：前置语句的唯一构造漏斗是
`_build_prefix_stmt_list(pre_instrs, block)`（`region_ast_generator.py:46017`），
全仓库只有 **2 个调用点**（`:31173` 走 `region.prefix_block`，`:31219` 走 `first_chain_block`）。
失败尝试 (a) 的病根是「登记的量（块 start_offset）」与「要判的量（前缀指令偏移）」
**不是同一个量纲**。因此：

1. 新增单一登记表 `self.prefix_emitted_upto: Dict[BasicBlock, int]`，
   语义 = 「该块内已发射语句所覆盖到的最后一条指令偏移（开区间/闭区间需一次性定死）」。
2. **只在 `_build_prefix_stmt_list` 内部登记**（漏斗唯一 ⇒ 不可能再出现 (b) 的
   「第一份语句不走台账」漏覆盖），登记值取本次实际消费到的前缀末指令偏移，
   而不是 `block.start_offset`。
3. `:31200` 的判据改为**同量纲切片**：只提取偏移严格大于
   `self.prefix_emitted_upto.get(first_chain_block, -1)` 的那段前缀语句；
   若剩余段为空则 `pre_stmts = []`。等价地：块是「语句 k 的前缀 ++ 语句 k+1 的前导」
   的极大直线序列，前缀切点之前的发射权属于已认领它的区域，之后的属于本区域。
4. 该表必须是**单向数据流**（自底向上、只写不减、不回改），
   与 `region_analyzer` 里 `block_to_region` 的单值映射解耦：
   块级单值映射无法表达双角色块（A-1 的 `ANALYSIS.md` §5 原则 2 同一结论），
   所以发射权只能记在生成层的指令偏移上，不能记在块归属上。

## 必须先补的尺子（当前是缺口）
仓库里**没有任何**钉住 A2 症状的复现（`grep -rn "a2" test_repros/` 为空，
`repro_01` 只存在于上一会话的临时目录）。因此实施顺序必须是：

1. 先按 `:31176-31181` 注释里的形状（`a = None; a = a or x.close`，BoolOp 结果被父表达式消费）
   写出 ≥10 个最小复现，逐个确认「前置赋值被吞」在**当前代码**上真实发生
   （不能拿猜的形状当尺子）；同时收录 6 处重复发射的负对照：
   `create_order` / `create_trade` / `_check_order` / `itn.authenticate` /
   `json_persistance.persist` / `quotation.change_future_real_date`，
   它们必须保持「不重复」。
2. 再实施 1–4；A-1 已改动了 `region_analyzer.py` 的 BoolOp merge 块放行逻辑，
   与本项是同一片邻域 ⇒ **A2 的复现必须在 A-1 落地之后重测**，
   否则基线会漂。

## 与其它项的关系
* 依赖：A-1（`region_analyzer.py:15910` 放行 + `chain_blocks` 登记）先落地。
* 不冲突：R14-D 改的是 `comprehension_generator.py` 的焊接认领，
  与前置语句发射权是两个正交记账面。
