# DIAG R14-06 — realtime_event_source.clock_worker：缺失量与区域事实的再实测（未解，供下一票）

尺：`scripts/pyc_verify.py single <pyc> --source <pycdc 产物>`；基线字节
`region_analyzer 640d33a77dcb71c2`、`region_ast_generator 851b0723732a2402`，本票 core/ 未动。
目标：`IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` ⇒ 12/13，
唯一失败单元 `<module>.RealtimeEventSource.clock_worker`（该文件整文件翻转候选）。

## 1. 本轮重新实测的三个事实

1. **缺失量**（hunk 尺，对现行 CLI 产物）：
   `UNIT /<module>/RealtimeEventSource/clock_worker len 1424/1311 net=+113 hunks=51 real=7 reloc=44 deleted=186 inserted=73`
   ⇒ 产物比原始少 **113 条指令**（186 删 / 73 插）。B153 系列说的「110 指令语句体整块不发」成立，
   且缺失是**分散在 replace 块里的大段折叠**（只有一个 17 指令的连续 delete 段 @6690，其余以
   N 条对 1 条的形式出现）——不是单纯丢一条跳转。
2. **@7972 区域形状**（进程内 `RegionAnalyzer(cfg).analyze()` 只读实测）：
   `IfRegion entry=7972 blocks=[7972,7980,8166] parent=LoopRegion@5598 children=0`
   ⇒ 该 IfRegion 的 then 体块**不在自己的 blocks 里**（blocks 只有入口、7980、8166 三块），
   所以「按 blocks 发射区域」的任何路径都只会发出一个空壳或整块跳过；
   生成结束后 `7972 ∈ generated_blocks` 且 `∈ generated_offsets`，产物里
   `if persist_flag is not False:` 一次都没出现。
3. **重复区域对象再次确认**：`self.regions` 里 `LoopRegion entry=5598` 出现**两次**
   （一次 parent=Loop@5598、一次 parent=None 且 children=[Loop@5598]）——与 B153 系列 §4
   记的同形。⇒ 任何以 `id(region)` 或「入口是否等于某区域」为状态判据的修法仍会在两处失真。

## 2. 与既有 4 次失败的关系（不再重复的方向）

`round11/DIAG_B153_CLOCK_WORKER_REDISPATCH_FALSIFIED.md` 已实测否决四条「重派发 entry@7972」判据
（无约束 ⇒ quotation 16 回归；parent 相同 ⇒ 惰性；containment ⇒ 函数体被吞 5423 字节；
入口偏移 ⇒ 仍 16 回归）。该文档指定的下一步是：**先把「发过语句但只登记块、不登记区域」
的那处记账补上**，再谈重派发；候选点是循环体消费路径
`region_ast_generator.py:8291-8295`（`for block in region.body_blocks: if block in self.generated_blocks: continue`，
其上方已有 `_direct_child_entries_r405` 直接子区域入口集）与 `:7538`、`:7766` 两处同类消费。
本轮实测补充：@7972 的 blocks 缺体这一条必须一起解决，否则即便重派发成功，发射出的区域仍无体可发。

## 3. 下一票建议

1. 先做**只读记账实验**（不改行为）：在三处消费点对每个「被 generated 集合挡掉的块」记录
   其所属区域的 entry 与是否曾有语句产出，产出一张「入口 → 是否真发过」对照表；
   用它验证 @7972 是否属于「从未发过」而非「已发但不登记」。
2. 再做**体块补齐**：若 §1.2 成立（then 体不在 region.blocks），则真正的缺陷在识别端的
   IfRegion 体收集（与 R14-05 的臂成员/merge 身份是同一族），应先修那里；
   否则记账 + 受控重派发才有效。
3. 验收顺序不变：小复现例（若有）→ 本文件 13/13 → 13 文件面板 → 完整门链 label 17 vs 16 → 提交推送。

## 4. 语料现状（本轮段结束）

390/402 文件、6583/6617 单元（99.4862 %），残余 12 文件 / 34 单元。
core/ 与 site-packages/、tests/ 工作树 0 行差异。
