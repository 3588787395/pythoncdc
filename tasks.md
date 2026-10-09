
## Task 13 — Round 12（票面已建：rounds/round12/TICKETS_ROUND12.md）

- 13.0 前置测量票 **T12-01**：建立可判别的「已发射区域入口」台账。读 `_loop_generate_while`/`_loop_generate_for`
  内对 `region.body_blocks` 的逐块消费点（候选 `region_ast_generator.py:8291`、`:7538`、`:7766`），
  只用**自证惰性**探针（只读局部量 + `start_offset`，跑完与封存产物逐字节比对）回答三问：
  兄弟臂子区域发射时是否有任何地方记下入口偏移；若无，记录点须与 `generated_blocks.add(block)` 同处（避免第二真相源）；
  evt `@7972` 与 quotation 那 16 个回归单元在「谁发射了它」上的可分事实是什么。**此票不许动发射行为。**
- 13.1 **T12-02**（依赖 13.0）：`realtime_event_source` 12/13 ⇒ 整文件翻转候选，只闭合 110 指令体不发这一形，
  放行必须排除被兄弟区域以角色字段认领的块（实测一次放行命中 3 块，含健康单元的 `@780`）。
- 13.2 **T12-03**：`#15` 隐式尾声族（`handlers._target` +2、`query_strategy_id` +1、
  `query_trade_strategy_info` 净 0、`filter_desicion` −2）——入口是 `_generate_block_statements` 对
  `LOAD_CONST None; RETURN_VALUE` 的拒绝路径，并须解释同一块在收尾扫处返回 1 条、在父臂处返回空的上下文差。
- 13.3 **T12-04**：`matcher` 三形同单元（or-fold `@1382` ＋ guard-fold `@1910` ＋ 被吞 `@2164` 十指令测试），
  oracle `m_or_full.py` 实测 17/17；单形不开票（`m_or_i/ii/iii` 全为 16/17）。
- 13.4 三条已钉死的不可用信号，禁止重复：链首放宽（三形净 0）、
  「区域从未生成 ⇒ 重派发入口」（quotation 153→137 两形 / evt 产物 5423 一形 / 惰性一形）、
  按 `id(region)` 判已生成（`LoopRegion@2` 与 `@5598` 均有同入口重复对象）。
