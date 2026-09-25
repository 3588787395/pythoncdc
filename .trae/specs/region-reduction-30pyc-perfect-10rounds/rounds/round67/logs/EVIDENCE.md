# Round 67 — EVIDENCE（原始读数，逐条可复放）

所有路径为绝对路径；`logs/gate/` 里是命令原始 stdout/stderr（未编辑），本文件只做转录与判定。
复放配方与仪器在 `center/`（`h62.py` / `closeout67.py` / `strict_repo67.py` / `blast67.py` /
`audit5_g5_67.py` / `mkmirr_r66.py` / `battable67.py`），代理侧仪器在 `batches/<批>/`。

---

## A. 落地字节指纹（阶段 B 结束时实测，与门禁所用字节同一）

```
core/cfg/region_ast_generator.py       3153249 B sha=f712bc20d7ad44542e18 BOM=True  CRLF=50782 bareLF=0  py_compile+ast OK
core/cfg/region_analyzer.py            1742308 B sha=af8cc88b9f89779b3ef0 BOM=False CRLF=27873 bareLF=0  py_compile+ast OK
core/cfg/comprehension_generator.py     108192 B sha=be5490c1118c7199fe0a BOM=False CRLF= 2016 bareLF=0  py_compile+ast OK
```

R66 轮初基线（同一脚本、同一断言方式）：

```
core/cfg/region_ast_generator.py      HEAD 3140634 B sha=3db80082b87ecca06e8c   （R66 提交记录逐字命中）
core/cfg/region_analyzer.py           HEAD 1734099 B sha=0e9740cc1836f3201312   （R66 提交记录逐字命中）
core/cfg/comprehension_generator.py   HEAD 104143 B sha=00903b60ef2411cb6b37
```

⇒ 净增：generator +12 615 B（+156 行）、analyzer +8 209 B（+110 行）、comprehension +4 049 B（+56 行）。
`center/mkmirr_r66.py` 之所以能做 R66 基线列，是因为仓库配置了文本转换（`git status` 头部即报
「Git content filters are configured」）：`git cat-file blob` 给出的是 LF 归一存储体，
必须再做一次 LF→CRLF 才等于工作树字节；两支 R66 指纹（大小 + sha256 前缀）命中即为证明。

落地链核对：`closeout67.py landproof mirr_m67g` → **33 core files, same=33 diff=0**
（落地前同一命令为 diff=3，即三处待改），`land67.py land --apply` 断言「spec 重放 == 实测镜像字节」逐文件通过。

## B. 本轮落地的 8 处编辑（行号为最终落地字节上的标记）

| # | 文件 | 落地行号 | 标记 | 规模 |
|---|---|---|---|---|
| 1 | region_analyzer.py | L16452 | `[R67-diag2 C1]` 短路链「负极性末段」补全 | +66 |
| 2 | region_analyzer.py | L21094 | `[R67-diag5 (d')]` 头块前导语句的同层拆分界定 | +44 |
| 3 | region_ast_generator.py | L19900 / L25871 | `[R67-diag4-A try-handler-backedge-explicit-continue]`（helper `_handler_backedge_is_explicit_continue` + 发射点） | +37 +8 |
| 4 | region_ast_generator.py | L21970 | `[R67-fix1 J3]` 无自身汇合点的顶层兄弟区域不得在循环发射中被认领 | +57 |
| 5 | region_ast_generator.py | L34887 / L34889 | `[R67-diag5]` 值语境链式比较三元：头块前导已完结语句的同层拆分（helper `_r67_split_cc_ternary_stmt_prefix`） | +53 +1 |
| 6 | comprehension_generator.py | L1620 / L1641 / L1702 / L1718 | `[R67-fix2]` 聚合布尔三元测试（helper `_r67_boolop_chain_end`） | +56 |

三要素（识别条件 / 归约方式 / AST 映射）均已写入各编辑点的「识别方法」注释内；
全部判据只读本区域/本块自身字段（`blocks`、`merge_block`、`exit`、`condition_block`、
`chained_compare_ops/blocks`、块内 `dis.stack_effect` 前向和），
**无** `region.entry in r.blocks` 型跨区域跨层次包含，**无**按函数名/文件名片段/偏移/阈值的启发。

## C. 串行门禁原始读数

### G1 本轮「修到完全 OK」靶 `site-packages/IQData/utils/common_func.pyc`
```
decompile_status ok, total_functions 24, matched_functions 24, match_rate 100.00%,
missing_in_decomp [], extra_in_decomp []
严格尺： OK 27/27 … 文件级：全部一致 1 / 1，有真缺陷 0
```
（原始日志 `logs/gate/G1_single_common_func.txt`、`G1_strict_common_func.txt`）

### G2 金丝雀（`logs/gate/G2_*.txt`）
```
fly/data/quotation.pyc            官方 143/143 100.00%   严格 DEFECT 148/150
   缺陷集逐字： _process_bar.change_his_to_forward #250 ； _process_bar.get_trend #10
fly/common/market_time.pyc        官方 10/10   严格 10/10
IQCommon/util/datetime_func.pyc   官方 26/26   严格 26/26
IQData/utils/datetime_func.pyc    官方 25/25   严格 25/25
```

### G3 `batch --index pyc_index.json --all --round 67`（background，exit 0，`G3_batch_r67.txt`）
```
total_pyc 402 / verified_pyc 402 / ok_pyc 387 / partial_pyc 15 / failed_pyc 0
total_functions 5746 / matched_functions 5701 / cumulative_match_rate 99.22%
[BATCH] index written back: pyc_index.json
```
`grep -E "FAIL|Traceback|Error" G3_batch_r67.txt` → 0 命中。

### G4 `stats --index pyc_index.json`（`G4_stats_r67.txt`）
与 G3 逐字相同。轮初发布值 5746 / 5698 / 99.16%（ok 386、partial 16）⇒ **matched +3、完全匹配 +1、partial −1**。

### G4′ 严格尺跑已发布产物（`G4p_strict_after_r67.txt`）
```
STRICT TOTAL ok=659 / functions=727          （轮初 655/727、缺陷 72 → 68）
每一支末列均 "mirror-sha <前8位>=measured"    ⇒ 出货字节 == 被测字节（逐支成立）
```
16 支共同文件上的缺陷集逐条比对（R66 `strict_repo_r66_after.json` vs 本轮 `strict_repo_r67_after.json`）：
```
FIXED 6： wizard_quant_api::get_DMI.calculate_di(81/79)  api_base::get_history_df(1742/1719)
          common_func::handle_exrights(276/268)          realtime_event_source::get_one_event(19/20)
          trade_live_broker::get_all_orders(80/83)       quote::run_tick_transform target_diff #135
NEW   2： api_base::get_history_df(1742/1740)  ← 同一函数被改善后仍红（缺 23 → 缺 2）
          quote::run_tick_transform target_diff #56 ← 同一条缺陷换位置（计数不变，形状移动）
```
⇒ 净效果 72→68，无「新出现的缺陷函数」。

### G5 索引审计（`G5_index_audit_r67.txt`）
```
entries HEAD=402 worktree=402
added=0 removed=0  key-shape diffs=0  round-stamp-only=399  substantive=3
   IQCommon/strategy/wizard_quant_api.pyc        matched 51 -> 52   rate 0.962264 -> 0.981132
   IQData/utils/common_func.pyc                  matched 23 -> 24   status partial -> ok
   IQEngine/…/trade_live_broker.pyc              matched 107 -> 108
status HEAD={'ok': 386, 'partial': 16}  →  NEW={'ok': 387, 'partial': 15}
matched HEAD=5698/5746  NEW=5701/5746  delta=+3
```
写回后的 `pyc_index.json`：402 条目、CRLF、与 G3/G4 及 `dump/m67g_402.jsonl` **逐支相同**
（`per-file diff vs published index: 0`；两份 Σ 均为 5701/5746）。

### G5′ 产物 blast（`G5p_blast_r67.txt`）
```
products identical=396 changed=6 unresolved=0
   CHANGED IQCommon/strategy/wizard_quant_api.pyc        （IMPROVED：calculate_di 消失）
   CHANGED IQData/api/api_base.pyc                       （MOVED+改善：get_history_df 1719→1740）
   CHANGED IQData/utils/common_func.pyc                  （IMPROVED：整支全清）
   CHANGED IQEngine/…/realtime_event_source.pyc          （MOVED：缺陷元组逐字不变）
   CHANGED IQEngine/…/trade_live_broker.pyc              （IMPROVED：get_all_orders 消失）
   CHANGED fly/data/quote.pyc                            （MOVED：缺陷元组逐字不变）
official instruction-gap sum landed=328  m67g=296
matched functions landed=5698  m67g=5701        fully matched files landed=386  m67g=387
```
⇒ 改动产物集**恰等于** IMPROVED(3)+MOVED(3)；没有任何手工编辑的 `*OK.py`（全部由工具链写出）。

### G6 电池（两列，真基线）
落地后 `arm=landed` 与 `arm=m67g` 已同字节（两次读数逐行相同，见 `G6_battery_r67.txt`），
因此另用 `center/mirr_r66`（HEAD blob + LF→CRLF，两支 R66 指纹命中）作 R66 基线列：
```
31 项老清单   battery_landed.jsonl(R66) → m67g_battery.jsonl
              115/127 → 116/127   IMPROVED=1(r66d3_pred 2/3→3/3)  WORSE=0  MOVED=0  ERR=0
45 项公开清单（含本轮 14 支新复现）  G6_battery_r66_vs_m67g.txt
              matched 161/200 → 174/200    缺陷函数 39 → 26
              fewer=8  equal=37  WORSE=0    errors=0
              candidate columns worse-than-landed on 0 repro(s)
```
本轮新增见证的位移（R66 → m67g）：`r67_ccprefix 1/5→5/5`、`r67_ccprefix2 1/3→2/3`、
`r67_site2 3/8→4/8`、`r67d6_boolop_ternary 4/6→5/6`、`r67d6_boolop_ternary2 3/8→6/8`、
`r67d4_handler_continue 4/4`（不变，其收益在严格尺 `s1` 3/4→4/4）。

## D. 402 A/B 与逐臂单变量复测（阶段 A/A′）

`dump/landed_402.jsonl`（R66 字节，Σ 5698/5746、fully_ok 386）为对照列：

| 臂 | 来源 | targets(16) | 电池 31 | 金丝雀 4 | 严格尺 16 |
|---|---|---|---|---|---|
| `c1` | diag2 analyzer L16448 or-chain 尾段 | IMPROVED=1（common_func 23→24）MOVED=1 REG=0 | SAME=31 | SAME=4 sha 全同 | 655→656 |
| `hc` | diag4 generator 2 edits（handler continue） | MOVED=1（官方中性，严格 +1）REG=0 | SAME=31 | SAME=4 | `realtime_event_source` 10/12→11/12 |
| `j3` | fix1 收窄 diag1 J1 | IMPROVED=1（trade_live_broker 107→108）MOVED=1 REG=0 | SAME=31 | SAME=4 sha 全同 | trade_live_broker 105/123→106/123 |
| `m67e` | c1+hc+j3 合并 | IMPROVED=2 MOVED=3 REG=0 SAME=11 | SAME=31 | SAME=4 | 655→658（缺陷 72→69）|
| `ccp_final`+`dsplit_a`（diag5 两步）| 生成器前导段拆分 + analyzer (d') | 单文件各自惰性/丢语句，成对才生效 | IMPROVED=1 | SAME=4 | — |
| `m67f` | m67e + diag5 两步 | IMPROVED=2 MOVED=3 REG=0 SAME=11 | **115→116** | SAME=4 | 658（缺陷 69）|
| `f2` | fix2 comprehension 1 edit | IMPROVED=1（wizard 51→52）REG=0 MOVED=0 | SAME=31 | SAME=4 sha 全同 | wizard 严格 52/56→53/56 |
| **`m67g`** | m67f + f2（落地臂）| **IMPROVED=3 MOVED=3 REGRESSION=0 SAME=10 ERR=0** | 116/127 | SAME=4 | **659/727（缺陷 68）** |

402 全量（`dump/m67g_402.jsonl` vs landed）：**IMPROVED=3 REGRESSION=0 MOVED=3 SAME=396 ERR=0**，
harness 口径 fully_ok 386→387、Σmatched 5698→**5701**、Σ|Δ| 328→**296**。

diag5 的两步制证据（中心独立复测，非代理口述）：
```
analyzer (d') 单独   r66d3_pred 2/3，v6 [36,34,2,16]→[36,34,1,34]（k = 1 整段丢失）⇒ 不可单独落地
generator 单独       对 landed 的 v6 完全惰性（analyzer 仍拒绝建三元区域），但独立修好 w2/w3/w4/w5/c6
pair（两步）         r66d3_pred 2/3 → 3/3，电池 SAME=30 IMPROVED=1 REGRESSION=0，
                     合成 r67_ccprefix 1/5→5/5，16 支与 402 零回归
```

## E. 被否决的臂（全部按实测否决，判据与锚点留档在 `batches/`）

| 臂 | 批 | 实测否决理由 |
|---|---|---|
| `cand_r67_j1` | diag1 | 金丝雀 quotation sha 移开（`3eb76e512df9ab1e`）且靶支读数不利 ⇒ 两道硬门禁同败。其「J1 使靶支 ERR」的自我陈述被 fix1/中心复测更正为 108/119 且不 ERR。 |
| `cand_r67_b1` | diag1b | 复现 1/6→3/6、电池 SAME=31、金丝雀 sha 全同，但名下靶支 **变差**：`_process_order` 396→**369**（orig 454）、t349→355 ⇒ 缺陷量放大。代理自 pin 根因：回收到的汇合点 2648 同时承载消费者与其后四条语句，`_mb_first_store_idx`（L21785-21794）只会按 `STORE_*` 切。 |
| `cand_r67_bare_return_sink`（臂 `d3c1`）| diag3 | 电池 SAME=31、金丝雀 SAME=4 sha 全同、16 支 REG=0，但 `_do_request` [436,443,2,384]→[436,**429**,1,380]：过冲 7 翻成欠缺 7，**Σ|Δ| 不变** ⇒ 按否决纪律（缺陷量必须净减少）不采纳。 |
| 宽版 `cand_r67_ccprefix_wide` | diag5 | 与收紧版在 54 支上逐支相同，且 R106 站点在 43 支 + 16 个合成函数上**零触发**（实测打印 `callsite=35102`×3、`callsite=35124`×0）⇒ 无 witness，不落地。 |
| `cand_r67_whiletrue_headif`（臂 `r67d6w1`）| diag6 | 靶支 `write_logging_thread` [113,113,1,40]→[113,**41**,1,107]、电池 `r63b5_w1::init_connection` [42,41,0,25]→[42,**32**,0,32] ⇒ 两支同步崩塌；需生成器侧「重发头块前缀去重」配套才可能成立，单侧不落地。 |
| diag5 对 real_quote / order_api / scheduler | diag5 | 归一化 hunk 表实测：real_quote 四支零语句增减（30/35 条整段搬尾 + `EXTENDED_ARG` 长度位）；order_api 三支属 R50 kwarg 槽位 bail（臂体被空化成 `pass`）；scheduler `run_daily`/`func_wrapper` 属 cellvar 降级（区域层之外）。⇒ **候选：NONE**。 |

diag5 的诚实警示（写给下一轮，别让读者误判）：`cand_r67_ccprefix` 在中心可达的全部样本
（43 支被测 + 16 支已知缺陷文件）上**字节惰性**，只有合成 witness 咬合；它的落地理由是「修掉一条
已证明存在、此前无任何发射方负责的语句丢失族」，语料净收益由 402 扫描定——实测 402 上它随 pair
进入 `m67f`，`MOVED=3` 中 `api_base::get_history_df` 缺 23→缺 2 即其贡献。

## F. 代理结论中被中心独立更正的条目

1. **fix2 未自留 `FACTS.md`/`ANALYSIS.md`**（其工作区最后写入 13:55）。中心按其 dump 与其 spec 自产记录补写：
   `batches/fix2/dump/{s1,s2,rp,tg,can,bat}_*.jsonl` 显示它的自测列（臂 `cmp1`/`cmp5`）——
   合成 `r67d6_boolop_ternary` 4/6→5/6、`…ternary2` 3/8→6/8、probe 组 `r67x_a` 1/3→3/3、`r67x_c` 2/3→3/3，
   电池 31 项逐行不变（含 `r66d3_pred` 仍 2/3，因该臂不含 diag5 两步）。中心独立复测与之相符，
   并把该 edit 合入 `m67g`；落地后 wizard 官方 51→52、严格 52/56→53/56、calculate_di 缺陷消失。
2. **diag1 的「J1 让靶支 ERR」** → 复测为 108/119 不 ERR；真正死因是金丝雀 sha 移开。
   fix1 又逐帧证伪 diag1 交下来的「blocks 单元素」收窄方向（命中帧全为 2 元素 `[68,98]`/`[332,362]`），
   真正的分离判据是**被认领区域自身的 `merge_block`/`exit` 为空**；反例 `quotation::get_trend`
   的 `mb=220 x=220` 正是被第 (5) 条挡住的那一支。
3. **diag2 更正中心轮初表**：`handle_exrights` 不是位移，真实缺陷是 or-chain 第三操作数丢失
   + 块 14 被当作链成员跳过而孤立。
4. **diag5 更正中心 brief 行号与前提**：analyzer L20949 只是该 gate 的注释首行，gate 体为 L20948-21053，
   合取 (d) 的实际拒绝语句在 L21026-21028；且 v6 需要两步（单改 analyzer 丢语句、单改生成器对 landed 的 v6 惰性）。
   陷阱入库：`region_analyzer.py` **没有模块级 `import dis`**（只有 L1869 `import dis as _dis` 与
   L3709/L12388/L14020 的函数内导入），在该 gate 用 `dis.stack_effect` 必须局部 `import dis`，
   否则 NameError 被上层宽 except 吞掉、产物静默退化成 `if 0 < int(dc): if 200: pass`（实测 `[36,28,0,29]`）。
5. **diag6 报出一条尺子覆盖问题**（本轮不解决，登记）：`fly/logger::SafeFileHandler.check_baseFilename`
   官方 34/34 PASS，严格 `target_diff #14` 抓到**真实语义反转**——
   orig `return 1 if (X or not Y) else 0`，产物 `if not (X or Y): return 1`（`not` 被从单个操作数 Y 推到了整个 BoolOp 上）。
6. **中心对本文件的两处自我更正**（见 `CENTER_NOTES.md` 文末）：Σmatched 以 **5701**（非 5700）、
   Σ|Δ| 以 **296**（非 298）为准；「R66 索引对 common_func 乐观 1 条」被按 `path` 键控重算证伪
   （HEAD 索引为 23/partial，与 fresh landed 402 逐条 `inconsistent=0`）⇒ 本轮三条 substantive 全是改善方向。

## G. 仪器缺陷登记（上游未改，绕法已写在脚本里）

| 仪器 | 缺陷 | 本轮绕法 |
|---|---|---|
| `nhunks.py` | 未归一 `EXTENDED_ARG`（跳距跨过 255 被当成真缺陷）；按 `co_name` 唯一匹配，`scheduler.pyc` 有 `run_daily`@72/@255 与 `func_wrapper`@262/@437 两支同名 ⇒ 直接 `AssertionError` | diag6 自写 `nested_diff.py` 按 code-object 全路径配对；diag5 记录限制不出表 |
| `cstrict.py` | 产物名推导只认 `site-packages/`，对 `test_repros/` 合成目录报 NO-PRODUCT | 中心补 `sstrict67.py`（可配对 scratch 路径） |
| `regdump.py` | 不打印 `handler_entry_blocks` / `except_handlers` | diag4 用 `disf.py` + 手写 dump 绕过 |
| `h62.py` `run` 的 resume | `--out` 指向已存在文件时按 `arm|path` 跳过全部记录（臂名复用时静默无输出） | 中心本轮改用新 `--dst`/新 `--out` 文件名 |
| 臂名命名空间 | `center/h62 build --dst=c1` 会覆盖 `diag2/mirr_c1`？（实测镜像目录同名冲突过一次） | 统一改用带批前缀的臂名（`d3c1`、`ccp_final` 等） |
