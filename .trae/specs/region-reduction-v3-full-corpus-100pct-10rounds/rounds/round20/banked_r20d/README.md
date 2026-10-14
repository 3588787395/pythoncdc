# r20d 交付存档（判决 FALSIFIED： fires without flips ⇒ 不安装）

- `region_analyzer.py` sha16 `ce8ac50d11401920`（32810 行，全 CRLF，`py_compile` 通过）；`FIX_T20-1.md` 为阶段读数。
- 实时仓库 `core/` 未被写过；其镜像分析端还原为 pristine `640d33a77dcb71c2`。
- 面板 19 文件与 6 电池**全部与基线同读数**；产物字节也与不加其判据的对照臂相同
  （`api_base 07e731a45762eb4a`、`strategy a387e7e0f43443c3`）⇒ 安装它没有任何产出变化。

## 买到的关键转移（下一票的前提，省一轮重复）

**识别端的 blocker A 已被解决。** 判据 `[T20-1-A]`（`_r20_explicit_edge_into` +
`_r20_carries_statement`，施加在 `_identify_conditional_regions` 中 then/else 两次收集之间
唯一的 `merge = else_succ` 写入点）只读父区构造时就存在的 CFG 边：
`else_succ` 的每一条**臂内部前驱都由显式正向跳落入（其间无落空边）**，
外加一条带语句的臂尾其正常后继正是重定向前的 merge。
探针普查：`[T20DBG] blk=992 es=1098 merge=1782 jumpers=[1024,1036] expl=True tail=True`
⇒ `IfRegion e=992 merge=1782 then=[996,1024,1034,1036,1040] else=[1098,1142,1200]`
——正是 r19t4 §6 要求的身份。**不读 `self.regions`/`block_to_region`，不依赖子区成员，无事后修补。**

**剩余缺陷在消费端**：策略那条链的分析端已经声明了正确落点
（`IfRegion e=512 else_blocks[0]=B@568`、`BoolOpRegion e=512 merge=568`），
产物仍发 `@522/@534 -> 820`；api_base 声明的 `else=[1098,…]` 语句组仍未被发出
（缺 `- @1124 BINARY_OP +`、`- @1128 STORE_FAST _last_real_59`）。
⇒ 判据落点在 `core/cfg/region_ast_generator.py` 的
**BoolOp-run-as-condition 边解析**一族——与已落地的 #37 以及
`trade_live_broker` 三条纯落点单元（`_process_tick_order`/`rzrq_credit_order`/`get_ipo_stocks`，
各差 1 条、产物落点一律偏早 3/5/10 条）**同族**。一条生成端判据理论上可同解
api_base + strategy + 3 条 broker 单元。

## 下一票的施工序（照此做，勿从头诊断）

1. 先把本存档的 `region_analyzer.py` 装进**丢弃式镜像**（它与当前落地生成端
   `dff6e81a5f2ff9f6` 同树可用），确认它使 `strategy` 的分析端声明与产物落点出现
   **可测差**（`unit_diff … landings` 仍 4，但普查里 merge 已正确）⇒ 证明「识别端已就绪」。
2. 在生成端 BoolOp-run 边解析处（先 grep `inline_boolop_chains` / `_main_ibc` /
   `op_chain` 的取边处，数清调用点再改）加判据：**当区域声明的 else/merge 边指向的块
   本身就是该 BoolOp run 的成功落点时，臂尾跳必须落在该块，而非其后继汇合**。
3. 命中自证用文件计数器（照 `NOTE_T20_ORDERING_WALL.md` 里登记的正确探针写法：
   逐行拼 CRLF、只读已绑定标量、每次做 `cmp` 惰性自证），不要第四版猜判据。
4. 验收：`strategy 27/27` **或** `api_base 28/28`（另一件不降）＋ broker 三条至少一条
   `landings→0`，六电池不变，面板 19 文件不变，门 label 20 vs `rounds/round19/after`。
