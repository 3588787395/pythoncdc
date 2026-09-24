# Round 63 batch 4 — 行情/风控 API 族 5 支

## 基线（landed 臂，已复测确认与 FACTS.md 一致）
```
landed main.pyc                     29/33  [get_same_shard_server_ip_info 192/173 j11 t62, get_server_ip_info 194/166 j9 t71]
landed wizard_quant_api.pyc         51/53  [calculate_di 75/73 j0 t45, params_analysis 133/126 j1 t117]
landed api_base.pyc                 23/25  [get_future_history_df 973/957 j3 t229, get_history_df 1742/1719 j14 t1277]
landed fly_historyquote/hsds.pyc    16/18  [get_kline_by_count 854/841 j3 t807, get_price 550/544 j4 t475]
landed risk_calculation/__init__    32/35  [_on_publish_after_trading_end 486/481 j3 t33, _save_testds_to_csv 71/68 j7 t19, get_TradeMode_trades 1839/1753 j4 t1620]
```
dump = diag4/dump/landed.jsonl，产物 diag4/build_landed/。

## 定位手段
- diag4/tools/align.py —— orig/decomp 指令序列 SequenceMatcher 对齐，直接打印差异块（带原始偏移与源码行）。
- diag4/tools/probe.py —— 只读打印区域树 + 块归属。
- diag4/tools/trace4.py / trace5.py —— 运行时 monkeypatch `_generate_region`，跟踪某个区域为何发射 None。

## 见证 1：fly_historyquote/history_data_source.pyc :: HistoryDataSource.get_price
真实缺失语句（orig L470，7 条指令 @358/@360/@362/@374/@376/@388/@390 + RETURN@400）：
```
        if len(bars) == 0:                     # L466  IfRegion@216
            if frequency == '1d':              # L467  IfRegion@302 (IF_THEN_ELSE, then=[314] else=[358])
                return A if fields is None else A[fields]   # TernaryRegion@314  ✅ 发射
            return B if fields is None else B[fields]       # TernaryRegion@358  ❌ 丢失
```
decomp 该处退化为 `LOAD_CONST None; RETURN_VALUE`，即 else 臂整体消失。

### 区域转储（实测）
```
REGION If@302 else_blocks=[358] children=[('Region',302,[302]),
        ('TernaryRegion',314,[314,318,332,356]), ('TernaryRegion',358,[358,362,376,400])]
   elif_conditions=[] chained_compare_blocks=[] merge=None
CALL _generate_region TernaryRegion@358 blocks=[358,362,376,400] idgen=False gblocks=[]
RET  _generate_region TernaryRegion@358 -> null          # ← 语句在此被吞
```

### 生效机制（已定位）
`region_ast_generator.py :: _generate_region` 的 TernaryRegion 分支首道守卫（落地态 L3181-3185）：
```
should_skip = False
for r in self.regions:
    if r is not region and isinstance(r, IfRegion) and r.region_type.name == 'IF_ELIF_CHAIN':
        if r.entry == region.entry or (region.entry and region.entry in r.blocks):
            should_skip = True
```
第二个析取支 `region.entry in r.blocks` 是**跨区域跨层次的包含判断**：只要三元区域入口落在*任意深度*的 IF_ELIF_CHAIN 区域块全集里就整块让位。实测本函数：
```
IF@216 rt=RegionType.IF_ELIF_CHAIN
TERN@358 elifchain_hits=[216]   ← 被吞的那个（IfRegion@302 的 else 臂）
TERN@314 elifchain_hits=[216]   ← then 臂（另由 if 生成路径发射，故看起来只少一份）
TERN@460/594/788/1018/3242 hits=[216 或 916,216]
TERN@128/172 hits=[]             ← IF@116 是 IF_THEN_ELSE，故同一形状的 else 臂正常发射
```
这解释了「同一函数里 455/457 的 if/else 完整、467/470 的 if/else 少 else」——两支的差异不在三元本身，而在其祖先链上是否存在一个 IF_ELIF_CHAIN（@216 因 then 臂全路径 return，402 被并成 elif）。

违反的设计律：区域归约要求「父层引用子区域**入口**而非其全部块」。`r.blocks` 全集包含判断正是被禁止的形状。

## 候选与实测

### c1 = 删除第二析取支（只留 `r.entry == region.entry`）
specs/c1.json，`python -X utf8 h62.py build --spec=specs/c1.json --dst=c1`

本批 5 支（dump/landed.jsonl vs dump/c1.jsonl）：
```
files=5 errors=0  landed: matched=151  ->  c1: matched=152
IMPROVED   IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc  16/18 -> 17/18
    +fixed   get_price (orig=550 decomp=544 true=475)
TALLY  landed->c1 : REGRESSION=0 IMPROVED=1 MOVED=0 SAME=4
```
逐行 diff 产物只有两条新增（正是 L470 的 else 臂），无任何其他改动：
```
                     return EMPTY_DAY_BAR_NP_ARRAY if fields is None else EMPTY_DAY_BAR_NP_ARRAY[fields]
+                else:
+                    return EMPTY_BAR_NP_ARRAY if fields is None else EMPTY_BAR_NP_ARRAY[fields]
             elif fq is not None:
```
402 全量（dump/landed_402.jsonl vs dump/c1_402.jsonl）：
```
files=402 errors=0  landed: matched=5675 clean=381  ->  c1: matched=5676 clean=381
IMPROVED   .../plugin_system_fly_historyquote/history_data_source.pyc  16/18 -> 17/18  (+fixed get_price)
MOVED      IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc  104/119 -> 104/119
    ~delta   fund_transfer        123->88  (-35)  =>  123->106 (-17)     # 朝 orig 收敛
    ~delta   market_fund_transfer  94->67  (-27)  =>   94->77 (-17)      # 朝 orig 收敛
MOVED      fly/simtradding/flyAccount.pyc  21/23 -> 21/23
    ~delta   _do_request  436->429 (-7) => 436->443 (+7)                 # 反向：多 7 条
TALLY  landed->c1 : REGRESSION=0 IMPROVED=1 MOVED=2 SAME=399
```
⇒ c1 零回退、+1 函数、另两支逐函数元组一支收敛一支发散。

### c2 = 把让位判据收窄到「链条本层可见的结构槽位」
specs/c2.json：让位仅当三元 entry ∈ {r.entry, r.condition_block, r.merge_block} ∪ r.elif_conditions。
5 支与合成复现与 c1 同（history_data_source 16/18→17/18，get_price 从缺陷表消失，复现 2/3→3/3）。

### c3 = 交付候选：让位判据收窄到「同层结构身份」＝ specs/cand_r63b4_tern_slot.json
```
if r.entry is region.entry or getattr(region, 'parent', None) is r:
        should_skip = True
```
- (1) 三元入口 **就是** elif 链区域的入口块（链头条件表达式）；
- (2) 三元的**直接父区域**就是该 elif 链（三元平铺挂在链臂语句序列里）。
两者都是本层可见的结构事实，不再读 `r.blocks` 全集。

本批 5 支：history_data_source 16/18 → **17/18**，get_price 从缺陷表消失；其余 4 支逐函数元组与 landed 完全相同（MOVED=0）。
合成复现 test_repros/round63_b4：landed 2/3（`pick` 39/31 j1 t20）→ c3 **3/3**；同文件阴性对照
`negative_pair_no_elif_chain` 两臂都匹配 ⇒ 触发条件确为「IF_ELIF_CHAIN 祖先」，与三元自身形状无关。

402 全量（dump/landed_402.jsonl vs dump/c3_402.jsonl）：
```
files=402 errors=0  landed: matched=5675 clean=381  ->  c3: matched=5676 clean=381
IMPROVED   IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc  16/18 -> 17/18
    +fixed   get_price (orig=550 decomp=544 j4 t475)      # 逐函数元组 → 从缺陷表消失（干净）
MOVED      trade_live_broker.pyc  104/119 -> 104/119
    ~delta   fund_transfer        123->88 (-35) => 123->106 (-17)   # 收敛
    ~delta   market_fund_transfer  94->67 (-27) =>   94->77 (-17)   # 收敛
MOVED      fly/simtradding/flyAccount.pyc  21/23 -> 21/23
    ~delta   _do_request  436->429 (-7) => 436->443 (+7)            # 已失配函数上长度再偏 14 条
TALLY  landed->c3 : REGRESSION=0 IMPROVED=1 MOVED=2 SAME=399
```
c3 与 c1 在 402 上 **逐字节等价**（`cmp_arms c1 vs c3 → SAME=402 IMPROVED=0 MOVED=0 REGRESSION=0`），
故第二析取支在本语料里 inert，交付 c3 是为把「链头条件」这一既有语义显式留在同一层判据内。

候选文件体检：mirr_c3/core/cfg/region_ast_generator.py — py_compile OK、ast.parse OK、BOM 保留、
size 3 061 465、CRLF 49 485、裸 LF 0（净 +22 行全为中文注释）。

严格尺（只读 landed 磁盘产物，反映落地态）：
```
22/24 IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc
  - get_kline_by_count: [seq_len] orig=857 decomp=844
  - get_price:          [seq_len] orig=553 decomp=549   ← c3 修掉的就是这一条
```

## 被证伪 / 移交的假设
1. **c2（槽位集 {r.entry, r.condition_block, r.merge_block} ∪ r.elif_conditions）证伪**：
   402 上 `REGRESSION=2`（order_api.base_order 32/34→31/34、order_api_trade.order_market 24/24→23/24），
   matched 5675→5674。⇒ 让位凭据**不是**「落在链条的某个槽位块上」，而是「是否同一层次的结构身份」；
   把 condition_block/merge_block/elif 条件块纳入认领集会把值上下文三元错误抢给链。不要走这条路。
2. **flyAccount._do_request 的退化不是层次判据能表达的**：其被多发的 14 条来自一个入口既非链入口、
   直接父也不是链的三元（`region.parent is r` 与 `r.entry is region.entry` 都不命中），
   landed 靠 `region.entry in r.blocks` 的过宽包含才压住它。该函数 landed 即已失配（436/429），
   文件级与 matched 均不受影响；收口方向 = 给「链臂语句序列里的值上下文三元」补一条同层判据，
   而非恢复跨层 blocks 包含。已列为 R64 候选。
3. **get_kline_by_count（本支另一见证，854/841 j3 t807）与 c1/c3 无关、逐函数元组纹丝不动**（实测三候选均不变）。
   其首块缺陷是 `if len(asset) < 1 or count == 0:`（BoolOp `or` 链，@114 POP_JUMP_IF_TRUE / @126 POP_JUMP_IF_FALSE）
   被反编译成**负极性 + 整支 then 体丢失**（decomp @126 变成 POP_JUMP_FORWARD_IF_TRUE，随后 L625 的 return、
   L628 `cur_date = convert_int_to_date(query_date)`、L630 `if asset['type'] == 'FUTURE'` 全部错位），
   属 R61 `_negate_expr` / `_r61_is_pure_jump_stub` 家族的另一条 `or` 链路径，与本轮三元让位判据正交。
4. **本批其余 3 支（main.pyc、wizard_quant_api.pyc、api_base.pyc、risk_calculation/__init__.pyc）
   在 c1/c3 下逐函数元组完全不变**（SAME），即本机制与它们无关：
   - `_save_testds_to_csv` 实测形状 = 两个**同层兄弟 while 循环**（L858 与 L869，各自 top-test +
     bottom-test 回边）被归约成 `while True: while...; while...; break` 的伪嵌套，且
     `from ...function import THREAD_STATUS` 被归约成 `THREAD_STATUS = ('THREAD_STATUS',)`；
   - `calculate_di` jumpdiff=0 / deficit=-2，缺陷在 genexpr 闭包（`sum(x for ...)`），不在区域归约两支文件内；
   - `get_history_df` / `get_TradeMode_trades` 未在本轮定位到机制，留 R64。
