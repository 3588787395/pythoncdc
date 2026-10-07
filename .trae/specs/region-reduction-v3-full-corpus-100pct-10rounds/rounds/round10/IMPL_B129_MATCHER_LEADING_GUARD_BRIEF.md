# Round 10 实现票 B129 简报：`_leading_*` 交接失败后仍把块标成「已生成」⇒ 语句静默丢弃

诊断凭据来自 `DIAG_B128_MATCHER_DROPSITE.md`（Q1/Q2，探针 `D:/Temp/r10diag/probe3-7.py`、
行级 trace `probe4.out` 377 事件）。本简报只定义**实现边界与验收**，不重复取证。

## 一、已被证据钉死的三件事

1. **表达式不是失败点**：`ExpressionReconstructor.reconstruct([2164..2204])` 成功返回完整
   `Compare(Subscript(Attribute(Attribute(order,'asset'),'symbol'), Slice(None,3)), 'in', ('688','689'))`。
2. **丢弃发生在「交接后无人接手」**：发射端在
   `region_ast_generator.py:54896-54921` 走 `_cjb_skip_inline_if` 分支，把条件挂在**落空块入口**上：
   - `_leading_operand`（`:54906`）唯一消费者 `_graft_pending_operand`（`:38289`）只被
     `_build_boolop_expression`（`:38412`）调用 ⇒ 只有 `BoolOpRegion` 会读；本例落空块 `2208`
     的入口区域是 `IfRegion(IF_THEN)` ⇒ **永不消费**（trace 实测：`generate()` 返回后该属性仍在块上）。
   - `_leading_guard_candidate`（`:38472`，记于 `:38516`）在其 **[C3] 守卫① `:38496`
     `if getattr(_R,'parent',None) is not None: return False`** 处返回 False，
     因为 `2208` 的 `IfRegion` 的 `parent` 是外层 `LoopRegion`（`for account, order in open_orders:`）
     ⇒ 无记录、`then._leading_guard is None`。
   - **`:54918` 丢弃了 `_leading_guard_candidate(...)` 的返回值** ⇒ 发射端无法区分「登记成功」与「登记失败」；
     随后 `:54920 self.generated_blocks.add(block)` + `:54921 return stmts`（`stmts == []`）。
3. **这是静默豁免且无退路**：块被登记为已生成，故 `generate()` 的逐语句降级
   （`:1887 _generate_degraded_statements`）也永远看不到它；无日志、无计数、无 fallback。
   同处 docstring（`:54913`）自称该守卫「替代此处对条件的静默丢弃」——**注释与行为矛盾**
   （嵌套宿主下被 advertised 的静默丢弃恰恰仍是执行路径）。此条另记 Task 11。

## 二、修复必须满足的形状（白名单事实；不接受更窄的替代）

判据的核心事实是一句话：**「把块登记为已生成」必须与「该块语句确实被某处接手」同命题**。

- 若条件表达式已重建成功，而**没有任何消费者接手它**（即两条记录都未成立），
  则该条件**必须由本块就地发射**（`stmts.append(...)` 挂上其 if/测试语义），
  且**不得**把源块加入 `generated_blocks`；
- 接手与否必须是**可测的事实**（登记函数的返回值 / 记录属性是否真在会被读的区域内），
  不是「调用过 setter 就算数」；
- 允许的表达手段：区域成员关系（该入口属哪个区域、其 `parent` 是谁）、块末 opcode、
  条件后继身份（fall-through vs taken）、`generated_blocks/generated_offsets` 的写入时机。

## 三、禁止项（每条都有本轮的前例）

1. 禁**放宽 `:38496` 的 parent 守卫**让嵌套区域也能登记 —— 那是把一个正确守卫改松去救另一处，
   会改变所有 `BoolOp`/guard 语义（B122/B123 两票即因「改松判据换读数」被否证与回滚）。
2. 禁按 `matcher`、`DefaultMatcher`、偏移 `2164`、指令条数 10、深度 1 等任何名/数特判。
3. 禁「不登记块」这一半修法而不补第 2 点（只让 `generated_blocks` 不写会走降级路径，
   产物可能变成降级形状而非正确形状——仍属以少发射/改形状换全绿）。
4. 禁 `_fix_/_merge/_patch/_fallback/_hack/_workaround/_temp_` 前缀新方法（G3）；
   禁硬编码计数/深度/偏移（G4）。
5. **本票只治这一面**。同函数里 `_cjb_pend_key`/`_leading_operand` 的其他宿主
   （真 `BoolOpRegion` 场景）行为必须逐位不变 ⇒ 负对照必须包含它们。

## 四、验收（主代理自有跑，工程师只需交出靶内读数）

| 步 | 要求 |
|---|---|
| 1 臂 | 复用/扩展 `test_repros/round9/r10ls_probe_index.json`（磁盘已有 7 臂：`r10ls_01/02/04/05` 复现、`c1…c6` 对照）。**建臂前先用 14 条索引本身生成清单**，禁止 glob `*OK.pyc` 当输入（B128 的 `final_base.json` 因 `files=28` vs 索引 14、表头 `units=33/16` 自相矛盾而被判不可信） |
| 2 | 红臂 → 绿；`c*` 对照臂**保持**绿（尤其 `c6_nonslice_twochain` 在 HEAD 态读红：它是**已知既存红**，不得算本票成绩，也不得为它改判据） |
| 3 | `python -X utf8 scripts/pyc_verify.py single site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc` → **17/17 status=success**（该文件只差这 1 单元 ⇒ 整文件翻正） |
| 4 | 产物文本须出现 `order.asset.symbol[None:3] in ('688', '689')`（或其等价正确形状），**不得**以删语句达成 |
| 5 | 哨兵不回退：`D:/Temp/r9w16/anchor_index.json`（5 文件 454/454）、`quotation` 153/153、`baseline/small34_index.json`（现 1528/1568、18 文件） |
| 6 | **402 全量双门禁由主代理跑** `gate_round.py 10 9 --stage regen/verify/report/checks`（`rounds/round10/after/` 会被本轮重生成覆盖，裁定 B126 用的那份读数已入库于 `9249c5ae`，随时可 `git show` 复取）；工程师不得自己跑全量重生成（唯一门禁资源，且 300s 命令上限） |
| 7 | 零翻转 ⇒ 按 sha256 逐字节回滚（封表值：`region_analyzer.py = 38a1d5142d13…`、`region_ast_generator.py = e9a8f65f6451…`，**以工作树哈希比对，不比 blob**） |
| 8 | 回报边做边写：`rounds/round10/FIX_B129_LEADING_GUARD_HANDOFF.md`，末节必须写「代码已落地」或「仅归档 spec 未落地」＋ grep 标记 |

## 五、回合预算纪律（三次 150 回合截断的教训）

本票只做「实现＋靶内复测＋哨兵」，**不**做诊断、**不**做全量门禁、**不**扩名单。
若中途受阻，把已证与已否证的写进回报文件即视为有效交付——空回报（B128 那种六个复选项全未勾）
比不派工更贵。
