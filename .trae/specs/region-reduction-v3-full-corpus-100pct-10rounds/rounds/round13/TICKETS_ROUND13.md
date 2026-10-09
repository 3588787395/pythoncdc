# Round 13 工单队列（按「唯一失败单元文件优先、同判据多文件优先」排序）

起点 = round 12 终态（门 label 14 认证）：单元 **6581/6617**（99.4559 %），文件 **388/402**，
残余 **14 文件 / 36 单元**，`UNREGISTERED=0`。表源
`rounds/round12/RESIDUAL_R12.md`（由 `residual_report.py 14 13` 出表，不手抄）。

本轮已在飞的机制族：链的「操作数分段 / 落点归属」。已认证可复用的两条落地判据
（写在这里免得后人重新推导）：

| 判据 | 位置 | 证据 |
|---|---|---|
| elif 臂候选的每条前驱必须归 `header_` 所属区域 | `region_analyzer._check_elif_chain`（HEAD `:21852` 前） | 门 14：matcher 16/17 → 17/17；全仓仅 1 个产物漂移 |
| `or` 折叠须按子区域 `entry→condition_block` 的落空边展开多腿 disjunct，且 `and` 模式早退 | `region_ast_generator._fold_chain_consistent` → `_or_multi_leg_chain_consistent` | 同上（两票为共要件，单票 0 翻正） |

## R13-01（在测，实为 round12 的 T12-23/24 续）— 二入汇合放行：`bar` + `strategy_universe`（各 2 文件里各 1 个失败单元）

`region_analyzer._b1b_loop_body_run_continuation` 情形 (1)（and→or 边界）现要求汇合块 Y
自身以正向条件跳转结尾（`_tgt_is_cond`）。实测（B134 §2.1/§3.1 + 本轮探针）：
`bar` Y=@140、`strategy_universe` Y=@156 都不是条件测试块，于是链被拒 ⇒ 外层区域的
`merge_block`（已经等于原始落点）在尾巴附着时从不被读取，产物把尾巴落到内层语句末（304 / 198）。
候选放行：**当 Y 的前驱恰为 {H, F} 本对操作数块**时接受（纯二入汇合，不可能是别处语句入口）。
镜像 A/B 在测（`D:/Temp/r142/t1234_pairjoin.py`，12 文件：su/bar/matcher/quotation/handlers/
wizard_quant_api/realtime_event_source/klinedata/trade_info_utils/strategy/quote/trade_live_broker）。
B134 §2.2 的 oracle 证明两靶形状各为 `if A and B or C:` 与 `if not i or not X:` ⇒
只改那一条测试的形状即可 85/85、11/11。

## R13-02 `handlers.TWHThreadController._target`（29/30，唯一失败单元）— 隐式尾声族

台账登记的机制：`+2`，一对 `LOAD_CONST None/RETURN_VALUE` 未发（`orig[75:77]`）。
LEDGER_R11_DAY2 §B146 已实测：放行分支确实执行（产物 9093→9147，3 处注入点），
但 handlers 仍 29/30 ⇒ 拒绝发生在 `_generate_block_statements` 内部（B119 相邻双 sink 对 /
B121 逐边落点块守卫之一），改登记/改顺序/改归属都动不了它。
先做：把「该块到底被 B119 还是 B121 拦下」用一次惰性探针钉死（两个守卫各自打印命中与否），
再谈判据；不得再用「重派发/改归属」碰这条（B127 已实测惰性并回滚）。

## R13-03 `realtime_event_source.clock_worker`（12/13，唯一失败单元）— 空臂归属

T12-09 已回收 61 指令但 0 翻正；产物形状实测为
`if persist_flag is False:` + `pass`，63 指令体掉在其后无条件执行，同形在同一产物内出现 3 次。
分派侧已排除（就地派发确实发生、两道收集前置门都没拦，`FIX_T1209…` §5）。
先做：用**已证惰性**的行级追踪（r150/t1217 那类，产物逐字节相同）钉死「谁把 @7972 的 then 块
当作普通块续发」，再谈归属；禁止再用 `_generated_regions`/入口偏移当「未生成」的代理判据（已两次实测不可用）。

## R13-04 多文件同判据族（次优先，因每文件需 ≥2 单元翻正才算账）

- `wizard_quant_api` 55/58：`filter_desicion`(−2) + 2 个 `calculate_di.<genexpr>` COPY_AMBIG
  （须先按出现次序人工定标副本，再谈开票）；
- `trade_info_utils` 38/41：`kill_trade_process`(TRANSPOSED 1) + `query_trade_strategy_info`(净 0)
  + `query_strategy_id`(+1) —— 后两条属 #15 隐式尾声族，与 R13-02 同判据，可并案；
- `klinedata` 62/64：`get_kline_by_count_new`（回边被写成正向跳过）+ `kline_datetime_list`（5→1 压形）；
- `api_base` 27/28、`real_quote` 43/45、`order_api` 35/37、`__init__`(risk) 41/43、
  `quote` 86/92、`trade_live_broker` 118/128、`strategy` 26/27（唯一失败单元）。

## R13-05 纪律（沿用，不重述理由）

一次一票、一票一机制；FIX 文档先行，判决只认字节；
镜像施工（交付整份文件，备份→复制→py_compile→标记→复验）；
探针一律 CLI-vs-CLI 自证惰性、插入用锚行自己的缩进；
零读数必须有正对照；每轮终态由 `residual_report.py` 出表；
调用子代理前先本地提交；每轮终了提交并 push 本分支。
