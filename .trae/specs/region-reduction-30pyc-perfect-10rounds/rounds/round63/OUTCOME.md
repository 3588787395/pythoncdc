# Round 63 — OUTCOME

起始 HEAD `96a5f310`（Round 62 记录）。轮初 21 支 partial（`stats` 5746/5675/98.76%，ok 381）。

## 1. 本轮形态

按指令「针对剩余的 partial，分成 5 批由 5 个子代理快速完成，再集中验证回退」执行：

| 批 | 覆盖 pyc | 交付 | 集中判定 |
|---|---|---|---|
| diag1 | common_func / trade_info_utils / … | `cand_fstail3.json`（3 edit） | **采纳** |
| diag2 | scheduler 族 | `FALSIFIED_cand_chainmerge_armowned.json` + `NONE.md` | 拒（自有见证上实测 INERT） |
| diag3 | matcher / trade function 族 | `cand_r63_claim.json` + `NONE.md` | 部分（转交 fix1 → chainstore） |
| diag4 | 行情/风控 API 族 | `cand_r63b4_tern_slot.json`（1 edit） | **采纳** |
| diag5 | 下单 API 族 | `cand_r63b5_hdrjt.json` / `hdrjt2.json` | 拒（见证缺陷量不变且新丢 `i += 1` / 内层 `break`，c2 变体更差） |

实现阶段另派 2 个单变量代理：fix1（生成器 chainstore）、fix2（分析器 boolop_exit）。
fix2 交付了自写分析（子代理在集中验证方补写之后返回并追加了自己的附录，其附录更正了首版表格
把 `b4x`（单变量分析器臂）与 `f2`（blunt 整体关闭）两个标签写反、以及把 `f3` 说成
「去掉 store 门控」之处；更正后的读数与归属见 `batches/fix2/ANALYSIS.md`）。
fix1 未留下 ANALYSIS.md，其工作区分析由集中验证方依据其 `dump/` 自产记录补写。
两支的独立复核：`fix2/dump/b4x_402.jsonl` vs `fix2/dump/f2_402.jsonl`（201+201，402 条不同路径）
经集中重跑 `SAME=402 IMPROVED=0 REGRESSION=0 MOVED=0` ⇒ P5 值块扩展在本语料两臂逐字节等价，
窄门控的理由是保留 P5 本职用途，不是全量收益。fix2 另提示：工作树 `core/` 于 04:20:39
被集中落地改写，其后任何 `--arm=landed` 读数代表 R63 而非 R62（已核对其 landed 列复现
R62 基线 5675/381，故仍为轮初态）。

## 2. 修到完全 OK 的 pyc（本轮 mandate）

`site-packages/IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc`
官方 **18/18 100.00%**，`history_data_sourceOK.py` 由工具链重写（源 31 915 字符）。
达成靠**成对**两支（单用任一支只能到 17/18）：

- 生成器 `[R63-B4 Fix1]`（region_ast_generator.py:3221）：`_generate_region` 的
  TernaryRegion 让位判据由 `region.entry in r.blocks`（跨区域跨层次全集包含，违反
  「父层只引用子区域入口」）收窄为 `r.entry is region.entry or region.parent is r`
  的同层结构身份 → 复原 `get_price` L470 的 `return B if fields is None else B[fields]`。
- 分析器 `[R63-B4 Fix2]`（region_analyzer.py:24415）：条件语境 BoolOp 短路链不再把
  语句体首块/汇合块吸为三元值块（`_all_ternary_cond_c = not (is_condition_context and merge is not None)`）
  → 复原 `get_kline_by_count` L625 三元 return 与 L628-630 的赋值和 `if asset['type']=='FUTURE'`。

## 3. 落地集

`core/cfg/region_ast_generator.py`：合并 spec `final_region_ast_generator.py.json`，
**9 edit / +474 行**（= b4s tern_slot 1 + b1f f-string tail 3 + fix1 chainstore 5）。
BOM + 纯 CRLF 保留，sha256 `7ec41fa2f9cdd5d62c1a`，3 086 600 B，CRLF 49 937，裸 LF 0，
`py_compile` + `ast` OK，与测量镜像 `mirr_final` 逐字节相同（`landproof` 33/33 core 文件）。

`core/cfg/region_analyzer.py`：**1 edit / +22 行**，无 BOM + 纯 CRLF，
sha256 `c694d2514eb2f2b21ccf`，1 721 959 B，CRLF 27 590，`py_compile` OK。

三处判据均按「识别条件 / 归约方式 / AST 映射」三要素写入注释（fix1 的两个 helper 另附
纯结构判据：`_r63b3_is_chain_cleanup_arm` 只用指令族 + 至少一条 POP_TOP + 栈效应和 ≤0；
`_r63b3_reduce_value_ctx_chain_store` 四条结构合取，任一不满足即返回 None 交回既有路径）。
无偏移特例、无函数名白名单、无阈值。

## 4. 门禁（严格串行，全部实测）

```
G1 single  靶 history_data_source.pyc        18/18 100.00%
G2 single  quotation.pyc                     官方 143/143；严格 148/150 缺陷集逐字未变
           market_time.pyc                   官方 10/10 + 严格 10/10
G3 batch --index pyc_index.json --all --round 63   402 verified / 0 failed / ok 382 / partial 20
G4 stats                                    5746 funcs / 5677 matched / 98.80%
G5 影响面  402 A/B（轮 f4_402 → mirr_final）  SAME=398 IMPROVED=1 REGRESSION=0 MOVED=3，文件 381→382
G6 电池    落地字节 17 项                     matched 44 / clean 8 / worse-than-landed 0
```

独立印证：fix1 进程在落地后重读的 402 支（`fix1/dump/wl.jsonl`）与集中镜像读数
**402/402 逐支 (matched, sha) 相同**，合计 5677、完全匹配 382。

索引逐条比对 HEAD：402 条目无增删，401 条仅 `last_tested_round` 变化，唯一实质变化即靶条目。
被改动的生成产物恰 4 支 `*OK.py`（靶 + matcher + trade_live_broker + flyAccount），
与 G5 的 IMPROVED/MOVED 集合一致；未手改任何反编译产物。

## 5. 附带改善与残余（如实记录）

附带改善（官方计数不变的 MOVED，按指令不计作「解决一支」）：
- `matcher.pyc :: match` 指令 713/689 → **715/715** 完全对齐，严格缺陷由 `seq_len` 转为 `seq_diff #182`
  （缺指令变顺序），官方仍 16/17。
- `trade_live_broker.pyc :: fund_transfer` 123/88 → **123/123** 长度对齐（残余一条
  FORMAT_VALUE 常量），`market_fund_transfer` 缺 27 → 缺 17。
- `flyAccount.pyc :: _do_request` 429 → 443（orig 436，官方口径过冲 +7；严格口径 431 → 445）：
  **该过冲由落地前的一对（`tern_slot` + `boolop_exit`）引入**，chainstore/fstail 在此文件上
  逐字节中性（fix2 的 `b4c_402` 与 `mirr_final` 读数同为 `[436,443,2,384]`）。作为漂移债务移交。

残余严格缺陷（本轮引入的形状变化，官方无感）：
`get_kline_by_count` 857/859、`get_price` 553/555（原 844/549 缺 13/4，缺失变 +2 过冲）。

20 支 partial 清单见 `logs/targets_partial21.txt` 与 `pyc_index.json` 轮次戳；
本轮 mandate 满足（≥1 支修到完全 OK 且 quotation + 批量回归通过）。

## 6. 移交下一轮的线索

1. **`matcher.pyc` 到不了 17/17 的第二处缺陷（R64 头号）**：`match` 的 orig 索引
   `180..462`（282 条指令，源码 219-232 区段、偏移 1314..~3200）被整体投到产物尾部
   （decomp 428..713 / 偏移 3060..4980），而 `if self._volume_limit:`（原 292 行 / 产物 161 行）
   占了前面的槽。落地臂与 chainstore 候选臂的 `probe_align` hunk 表**逐字节相同**
   （RATIO 0.5926 vs 0.5818）⇒ 与本轮改动无关的既有位移缺陷，fix1 §4 有 hunk 明细。
2. `tern_slot` 与 `boolop_exit` 是**成对生效**（各自单独用都会在对方负责的形状上砸开缺口，
   实测见 `batches/fix2/ANALYSIS.md` 表格）。与记忆 `analyzer-generator-pair-inertness` 同形。
   后续对分析器块归属的改动必须与生成器让位判据一起过电池。
3. `region.entry in r.blocks` 这类「跨层次全集包含」判据在 `_generate_region` 各分支里仍有同族
   写法（diag4 的 ANALYSIS 记录了同函数 IF@216 的成因：then 臂全路径 return 把 402 并成 elif）。
4. 两支 b4 变体已证伪，勿重试：`f3`（按块内容含 STORE 即拒，被吞的 128 本就不含 STORE，
   缺的是结构事实）；`f2`（整体关闭值块扩展）与落地窄门控在全量 402 上**逐字节等价**
   （`ab --a=b4x_402 --b=f2_402` → SAME=402），说明 P5 扩展在本语料值上下文 inert。
5. `flyAccount._do_request` 的过冲（官方 +7 / 严格 +9）发生在 b4 成对上，根因站点 diag5 已指到
   `_loop_build_if_with_exit_branches`（落地后位于 region_ast_generator.py:10470；diag5 读到的
   :10444 是落地前行号）的臂极性选择；需要一条「补发臂不得重复汇合后语句」的合取，
   而不是回退（回退臂 `mirr_nog1` 未跑完，其 `dump/wn.jsonl` 停在 185/402）。
6. `_boolop_resolve_merge` 在 get_kline_by_count 上给出的 `merge=374`（真出口应是 172）本轮未动，
   属另一判据，fix2 §证伪 5 留给 R64。
7. 未收敛的两批判据（各自 FACTS 已留探针读数，勿在电池外重试）：b2 尾比较 + return
   （`probe_r63b2_cases2` 仍 d=-94、`repro_r63b2_tail_cmp_return` d=-24），
   b5 下单头跳转（`r63b5_w1` d=-1）；b1 f-string 尾落仍有 `r63_ft4` d=-9。

## 7. 归档

`batches/diag1..5`、`batches/fix1..2`（含 specs 与被拒臂）、`logs/EVIDENCE.md`（A–F 六节，
F 节为落地后终读）、`logs/gate/`（G1–G6 原始输出 + 合并 spec）、`logs/targets_partial21.txt`、
`logs/shapes_r62.txt`。最小复现入库 `test_repros/round63_{b1,b2,b3,b4,b5,fix2}/`（10 组 .py/.pyc）。
