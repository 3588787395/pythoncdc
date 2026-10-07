# Round 9 A 轴工单简报（主代理实测取证，待派发）

## 标题
循环体内嵌套 IfRegion 吸收了**父循环的前导块与出口块**，导致发射层把臂尾物化成 `break`，
方法体剩余部分被 CPython 当作死码丢弃。

## 实测锚点（`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`）

单元 `TradeLiveBroker._process_order`：产物 code object **42** 条指令 vs 原始 **520** 条；
`_process_cancel_order`：40 vs 344。产物文本看着完整（`break` 之后还印着 30+ 行语句），
但那语句**不在字节码里**。机制已用最小样例证实（CPython 3.11 丢弃循环体内无条件 `break`
之后的同块语句；样例里 `co_names == ()`）。

区域识别现场（`CFGBuilder` + `RegionASTGenerator`，probe `D:/Temp/r9main/probe_break.py`）：

    LoopRegion entry=46 nblocks=62
        condition_block = 46
        else_blocks     = [3024, 3116, 3128]
        back_edge_block = 3128
        body_blocks     = [46, 96, 98, 206, 258, 318, 360, 418, ...]
    IfRegion   entry=318 nblocks=49          ← 这是循环体**内部**的区域
        condition_block = 318
        then_blocks     = [360]
        else_blocks     = [44, 418, 420, 456, 500, ...]   ← 44 在区域入口之前
        merge_block     = 3128                            ← 正是父循环的 back_edge/出口块

CFG 事实：`blk@44`（单条 NOP，唯一的后继是循环测块 46）`own = LoopRegion@46, IfRegion@318`；
`blk@46` 末指令 `POP_JUMP_FORWARD_IF_FALSE arg=3128`，succ=[96, 3128]；
循环体真实起点 `blk@96`（NOP）→ `TryExceptRegion@98`（`with self.lock:`，产物把它整个丢了）。

## 两处原则违反（同一根因）

1. **原则 2（每块每层唯一归属）**：`blk@44` 同时属于父 `LoopRegion@46` 与嵌套 `IfRegion@318`。
2. **原则 4（入口引用语义）**：嵌套区域的 `merge_block` 取了**父区域的出口块** 3128；
   于是该 IfRegion 的「else 臂尾」在发射时等于「跳出循环」，发射器如实写出 `break`，
   而循环体的其余成员（96/98 起的 with/try 与后续）被排在 `break` 之后 ⇒ 死码。

根因面貌：从区域出口做「避开入口的可达性」走查时，循环回边把**前导块 44**（以及出口 3128）
当成了可达节点吸收进来——即回边方向未参与区域边界裁剪。

## 要求（不许做的事）

- 修在**识别端**（`region_analyzer.py` 的区域边界/merge 判定），使任何子区域的 `blocks` /
  `then_blocks` / `else_blocks` / `merge_block` 都落在**父区域的本层体集合之内**，
  且永不吸收父循环的 `condition_block`、其前导块与 `back_edge_block`。
  这是父/子区域成员关系的边界条件，不是发射端的补丁。
- **禁止**：新增 `_fix_/_merge_/_patch_/_fallback_` 类事后修正；禁止在生成端「把 break 之后的
  语句搬回去」（违反 rules.md §1.3 单向数据流）；禁止按块号/循环层数/语句条数特判。
- 判据必须能表达成块/边/区域成员事实：例如「候选 merge 块若为某父 LoopRegion 的
  back_edge_block，或该块是本区域入口的**前驱闭包**成员（回边可达），则该候选不成立，
  改取本层体内可达的第一个汇合块」。具体谓词由工单按实测形状定，须写满 docstring 六项模板。

## 验收（必须逐条实测，读数由主代理复核）

1. 复现电池先行：`test_repros/round9/` 至少 2 条最小合成臂复现「循环体首成员是 with/try 区域、
   体内后段有 if 臂、其出口经回边指回前导块」形状；**先对已落地字节跑绿/跑红确认形状成立**，
   再动生产代码（Battery before corpus）。
2. `pyc_verify single` 目标单元翻转：`_process_order`、`_process_cancel_order` 从 failure → Equal；
   同时 `trade_live_broker` 其余 8 个失败单元**不得**因本案换形态（逐单元名单前后对比，
   不许只看 118/128 这类总数）。
3. `order_api.option_order` / `future_order`（94/55、115/88）**同向核对但不得并案**：该文件
   `loops=[]`、无循环回边，形状不同轴；若被顺带翻正须单列证据。
4. 七套电池（r1/r1_regress/r2v3/r3/r4/r6/r8）零绿臂转红；quotation 153/153、quote_handler 79/79、
   ptradeAccount 137/137、`history_data_source` 19/19 四枚锚点不回退。
5. 全量 402 门禁由**主代理**执行（工单自测不得作为轮的判定）：402 重生成 + 八分片 per-file unit diff，
   `unit_down=0 ∧ file_down=0`。

## 主代理纪律提醒

- 每条命令 ≤300s；产物一律先删后 `python -X utf8 pycdc.py -o` 生成，**禁止手改 `*OK.py`**；
  不要 `import` 任何装配脚本；scratch 只写 `D:/Temp/rrv9/`。
- 只改 `core/cfg/region_analyzer.py`（如需生成端配合，须在报告里单列并给出理由）。
- 报告须写明「代码已落地」或「仅归档 spec 未落地」，落地以 `[R9-B1xx …]` 前缀标记为凭。
