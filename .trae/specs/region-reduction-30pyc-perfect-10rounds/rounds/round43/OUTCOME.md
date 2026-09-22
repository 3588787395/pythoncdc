# Round 43 — 零改动轮：三条候选线全部否证（core/ 字节不变）

落地核（本轮全程未变）：`core/cfg/region_ast_generator.py` len 2 994 079 · sha256[:20] `11e2c67e2d7681735f9d`；
`core/cfg/region_analyzer.py` len 1 678 535 · sha256[:20] `a66248d3b9a3e0a1545e`。仓库起点 `e52cb564`（Round 42 = 核零改动）。

## 一、目标池（对落地字节实测）

以 Round 42 的落地态全 402 官方口径转储 `D:/Temp/r42gate/h42_all.jsonl` 为基准：
partial 文件 **27** 个，Σdeficit **89**；deficit≤2 的 G1 池 **17** 个文件（`D:/Temp/r43gate/g1_files.txt`，a 侧 `g1_head.jsonl`，Σmatched 387/403）。

**索引审计（本轮新增，`D:/Temp/r43gate/idxaudit43.py`）**：402 条索引项与一次全新落地态全量复验**逐项相等**（overstated=0 / understated=0 / unmeasured=0，Σmatched 5657 = 索引 Σ）。
⇒ 本轮不存在需要更正的索引虚高；`stats` 的任何变化都只来自真实增减。

## 二、本轮否证的三条候选（均在镜像臂上实测，未触碰仓库 core/）

### 候选线 C（代理）：硬退出臂无合流点 ⇒ 认领 `else_succ` 为 merge

`core/cfg/region_analyzer.py` 主机锚点 `:17062`（`if (merge is None / and not then_succ.successors / …`，全文唯一）。
判据形如：`merge is None` ∧ `not then_succ.conditional_successors` ∧ 终止符 ∈ {RETURN_VALUE, RETURN_CONST, RAISE_VARARGS} ∧
`else_succ is not block` ∧ ¬(块是 loop 的条件块) ⇒ `merge = else_succ`。属同层判据（只读结构事实与操作码类）。

其自建两文件 A/B（`D:/Temp/r43diagC/headC.jsonl` vs `c1C.jsonl`，编排方独立复算）：

| 文件 | head | 候选 |
|---|---|---|
| `fly_api/order_api.pyc` | 30/34 | **32/34（+2）** |
| `plugin_system_trade/trade_live_broker.pyc` | 104/119 | **101/119（−3）** |

⇒ REGRESSION≠0，未进入 G4 即淘汰（该文件 −3 的三个函数正是本轮第五节否证表达式层的 F1 族）。

### 候选线 C1（编排方加严）：再加「被认领的 merge 只能由本块进入」

新增合取项 `set(else_succ.predecessors) == {block}`，其余同上。镜像臂 `D:/Temp/r43gate/mirr_r43c1`（`build` 报告：1 edits，`core/cfg/region_analyzer.py`，BOM=False，nl=CRLF，插入 13 行）。

- 线 C 的两文件上**增益完全消失**：`order_api 30/34 → 30/34`、`trade_live_broker 104/119 → 104/119`（FIXED=0）。
- G1（17 文件）：`SAME=4 IMPROVED=0 REGRESSION=2 MOVED=13`，Σmatched **387 → 370**；最坏 `plugin_system_trade/function.pyc 69/71 → 53/71`（−16）、`IQCommon/data/finance.pyc 22/24 → 21/24`。

**机制结论（本轮真正的收获）**：merge 补全是一串**级联兜底**——`:17014`（R35 boolop 链兜底）、`:17062`（本候选宿主）、`:17102`（orig cond block 兜底）……
在一个锚点**拒绝**认领并不会"少做一件坏事"，而是把该块**改派给更后面的兜底**，从而在别处产生新的错误认领。
⇒ 该族的任何加严都必须同时观测"被拒块的落点"，单点加合取项在这串级联里不单调；`function.pyc` −16 就是反证样本。

### 候选线 D 形状（编排方一手普查）：前导语句丢失族的语料密度不足

全 27 个 partial 文件的逐函数操作码名对齐普查（`D:/Temp/r43gate/census43.py`）：**只有 4 行丢失前导指令**——
`quote::load_bars_from_hundsun`(d=7)、`quote::get_price`(d=42)、`quote::load_get_price`(d=35)（三条均已钉为 F1 表达式层）
与 `quote_handler::get_index`(d=28)。
⇒ 「前导/尾部整块未发射」形状在语料里只剩 **1 个非 F1 见证**，按"仅修合成见证不可发货"的既有纪律不足以支撑一条新判据。

## 三、另两条今天排除的大额亏损线（避免后续轮重复分诊）

1. `trade_live_broker.pyc` {`market_fund_transfer` 94/67, `fund_transfer` 123/88, `get_etf_stock_info` 144/117, `_sync_worker` 349/323}
   ＋ `quote.pyc` {`load_get_price` 171/136, `get_price` 230/188}：j=1/0、丢 27–42 条，形似"单个区域错位"，
   实为 **F1 f-string 语句被重建为 return 值**（产物里出现 `return f"strategy_log转入{'沪A' if …}失败，错误原因：error_info"`，
   接收者被粘进字面量、插值塌成裸文本，尾部 `return False/.info/return True` 随之消失）。已写入项目记忆。
2. `plugin_system_risk_calculation/__init__.pyc :: get_TradeMode_trades` 1839/1753（j=4, fd=1620）：
   操作码名对齐给出 **14 处恰为 3 指令的删除**（`COPY COPY BINARY_SUBSCR`）＋4 处 7 指令＋1 处 21 指令，
   被删算子以 COPY 14 / SWAP 14 / BINARY_SUBSCR 20 / BINARY_OP 13 为主 = CPython 3.11 链式下标的栈纪律差异。
   19 个分散 hunk 不可能由生成器里某一条提前 return 解释 ⇒ 非区域归属问题，同层判据无从下手。

## 四、门禁与工具状态（本轮建好并已自测，供后续轮直接复用）

| 门禁 | 资产 | 自测结果 |
|---|---|---|
| G1 | `D:/Temp/r43gate/g1_files.txt`(17) + `g1_head.jsonl` | 身份检查 `SAME=17 IMPROVED=0 REGRESSION=0 MOVED=0`，Σ387 |
| G2′ | `bat43.txt`(143 = reprobat61＋anchors109＋round41＋round42 电池) + `bat43_head.jsonl` | 111 文件全匹配，Σ 550/583 |
| G3 | `anchors109.txt`(109) + `anch43_head.jsonl` | 沿用 Round 41 落地态 `SAME=109` |
| G4 | `all402.txt`(402) + `g4_head.jsonl` | 与索引逐项一致（见第一节审计） |
| G4′ | `g4prime43.py <changed.txt> <arm>` | 身份自检 `affected=1 fixed=0 broken=0 changed=0` |
| G5 | `D:/Temp/r42gate/canary_shas_landed41.txt`（9 条，全 HOLD） | 未动核，保持有效 |

一条命令即可复跑前三关：`python -X utf8 D:/Temp/r43gate/gate.py <arm> g123`。

## 五、发货决定与本层归属

本轮 **core/ 零改动、不发货**：三条候选均否证——线 C 官方口径即出现 −3 回归；线 C1 加严后增益归零并新增 −16 回归；线 D 形状缺语料见证。
`region_analyzer.py` 的 merge 补全级联（≥4 个相互让位的兜底）是本轮定位到的**层级事实**，后续攻这条线必须先解决"被拒认领的块改派到哪里"的可观测性。

## 六、`stats`（本轮逐字原样）

```
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5657
  cumulative_match_rate: 98.45%
```

## 七、移交 Round 44

1. 在跑的代理线 A（`handle_exrights` 短路链取反吞噬）、线 B（等长单跳转错位簇：`_process_task_queue` 378/378、`write_logging_thread` 113/113、`init_connection` 42/41；普查显示该簇同形者还有 `_get_influence_task` 12/1 hunk、`financial_statements` 10/1 hunk、`logging_process` 10/1 hunk）、线 D（`quote_handler` 前导/尾部丢失）交付后：先跑 `gate.py <arm> g123`，再看 G4/G4′。
2. 攻 merge 级联的话，先给 `:17014 / :17062 / :17102` 三个兜底加"认领来源"可观测性，再谈判据；`function.pyc` −16 是必测反例。
3. 勿再分诊：F1（`trade_live_broker`/`quote` 的大额 j≤1 行）、`get_TradeMode_trades` 分散栈噪声、`quote_handler::get_index`（唯一非 F1 前导丢失见证）。
4. 既有 NO-GO 与残余账目（`matcher::match`、`events` 等别归属未定、`clock_worker` +6、`decrypt_database_url` −29、8 条布局等价行等）全部照旧结转，未在本轮变动。
