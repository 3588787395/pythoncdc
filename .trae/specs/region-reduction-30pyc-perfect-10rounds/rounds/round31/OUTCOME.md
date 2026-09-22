# Round 31 OUTCOME —— R31-C 落地：臂停止集里的「无正常后继、前驱全在臂内」终止块归还本臂尾

基线 = 落地字节 `7b5f760c`（Round 30 R30-C1 之后）。本轮发货判据 R31-C，落地于
`core/cfg/region_analyzer.py` 两处站点（`+68 / -0` 行，核 sha `a66248d3b9a3e0a1545e`，与实测镜像
`mirr_c/core/cfg/region_analyzer.py` 逐字节相同）。靶子 `fly/common/flytools.pyc :: FileLock.acquire`
由 `64/65` 翻转为 `65/65`，官方尺与严格尺同时收口。

## 一、目标池与三条诊断线（均实测）

`logs/pool31.txt` 首行直接读自 Round 30 G6 回写的索引，不转述：

```
baseline(landed round30 index, HEAD 7b5f760c): files 402 partial 32 sum_deficit 104 deficit1 8
```

八个 deficit-1 文件在落地核上逐个 `single` 一手复测（`logs/landed_d1.txt`，八条全在，无缺行）。三条
候选线的取舍全部由实测决定（详见 `arm-design.md` 第一节）：

* **线 A（取）**：`flytools :: FileLock.acquire`。有可得的 G0（合成见证在落地核上 `1/4`）、判据是
  纯归属取消（只 `discard`，不新增发射）、且靶子**能翻转**并同时在严格尺上从 `65/66 σ1 Σ|Δ|=5`
  到 `66/66 σ0 Σ0`。
* **线 B（继续移交 #61）**：R30-B3 门禁齐备但官方尺中性、无可得 G0。
* **线 C（不取）**：`events` 残余 −2 需两条判据，且其中一条单独使官方尺 `jump_diffs 2→4` 变差。

## 二、判据 R31-C（原则 2 每块唯一归属 · 臂内终止汇合块侧）

一句话：**臂停止集里那个「没有正常后继（其后继全为异常后继）、且全部前驱都在本臂内∪停止集」的块，
是本臂的终止语句块，不得充当本臂与兄弟臂的边界认领；只 `set.discard`，交回 `_collect_branch_blocks`
作臂尾。** 站点一在 `then_stop`/`else_stop` 构造处（`:17137`，40 行），站点二在 elif 链
`_chain_merge` 重建后复放同一判据（`:19310`，28 行）—— 因为该处会从 `boundary_stop` 重新组装
`_then_stop`，不复放即覆盖站点一的成果。

根因是**一个**归属错误的三个症状（H1 臂尾 `raise` 落到 if/else 之后、H2 `except` 正常出口的
as-var 清理尾声失去发射路径 −4、H3 循环回边失去发射路径 −1），而非 Round 30 误记的「三族混合」。

## 三、门禁（严格串行；原始日志全在 `logs/`）

| 门禁 | 读数 | 日志 |
|---|---|---|
| G0 合成见证 | 落地核 `1/4` → R31-C `3/4`（`w_a` 52/47 j4 t11、`w_b` 48/44 j3 t14 均修复；`w_c` 64/63 j2 t51 为第三形状，保持失败） | `g0p_head.jsonl` / `g0p_c.jsonl` |
| G0 CONTROL | 三把核同读 `5/7`，失败对同形（`c2_arm_tail_is_break`、`c6_both_arms_end_in_raise`），产物 sha `SAME` | 同上 |
| G0 站点二必要性 | 只做站点一 → 见证 `2/4`；复放后 `3/4` | `g01_b.jsonl` / `g01_c.jsonl` |
| G1 靶子 | `64/65 [acquire 88/85 j2 t14]` → `65/65 []` | `g1_head.jsonl` / `g1_c.jsonl` |
| G2′ 上一轮 38 合成复现 | `{"SAME": 38, "IMPROVED": 0, "REGRESSION": 0, "MOVED": 0, "other": 0}` | `g2prime_38.txt` |
| G3 承重锚点 98（本轮起并入 R30 两件合成锚） | `{"SAME": 98, "IMPROVED": 0, "REGRESSION": 0, "MOVED": 0, "other": 0}` | `g3_98.txt` |
| G4 全 402 A/B（sha 优先，发货判据） | `SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0`，`files fully matched: a=370 b=371` | `g4_ab402_sha.txt` |
| G4′ 严格尺逐个变化产物 | `flytools` `65/66 σ1 Σ5` → `66/66 σ0 Σ0`；`gtn_api` 两把核 `5/5 σ0 Σ0` | `g4prime_*.txt` |
| G5 `single` 靶子＋五锚 canary | 靶子 `65/65 100.00%`；`quotation 143/143`、`load_daily 23/23`、`plugin_system_persist/__init__ 15/15`、`custom_tools 6/6` 全保持；残余 `instance 31/32`、`quote 67/81`、`replace_utils 8/9` 逐条同形 | `g5_single.txt` |
| G6 `batch --index pyc_index.json --all --round 31` | 末条 `[402/402]`、`index written back` 恰 1 次、崩溃标记 0 行、统计块完整 | `batch_all31.txt` |
| G7 `stats` | `total_pyc 402 / verified_pyc 402 / ok_pyc 371 / partial_pyc 31 / failed_pyc 0 / total_functions 5746 / matched_functions 5643 / cumulative_match_rate 98.21%` | `stats31.txt` |

## 四、唯一产物变化的逐项交代

`logs/index_delta31.txt`：`entries with real (non round-stamp) field changes: 1 ->
['fly/common/flytools.pyc']`（`decompile_status partial -> ok`、`matched_functions 64 -> 65`、
`bytecode_match_rate 0.9846153846153847 -> 1.0`；其余 402 条只被重打 round 戳）。

被改的跟踪产物恰两个，且都与实测镜像 `build_c` 产物逐字节相同（`logs/products_sha.txt`）：

1. `site-packages/fly/common/flytoolsOK.py`（sha16 `d1ddb72cf60efdfe`）—— 靶子翻转的正面结果，
   `acquire` 严格尺 `orig=90 decomp=85 → 90/90`，非等价块 `3 → 0`（`hunks_head_tracked.txt` 的三处
   hunk 在 `hunks_c_tracked.txt` 下全部消失）。
2. `site-packages/IQCommon/api/gtn_apiOK.py`（sha16 `f26e8a084eef60cc`）—— **官方尺与严格尺都判中性**
   的 MOVED（`5/5 → 5/5`，两侧 `σ0 Σ0`）。差异是两处 `else: time.sleep(1)` 折叠为不缩进的顺序语句
   （产物 87→85 行：删 4 行、增 2 行，`g4prime_gtn_api_diff.txt`）。本轮判据把它从「多余 else 分支」变成「与字节码等价的
   顺序发射」，两条尺都认忠实 ⇒ 接受，同时登记为「ok 文件产物文本变化」在册观察项，不得视为已解释。

## 五、方法论收获

1. **严格尺干净的翻转是比官方计数更强的证据**：靶子在两条尺上同时从有缺陷到 `σ0 Σ0`，说明本轮不是
   「用一条尺的漏洞换另一条尺的分数」。
2. **一次错位可以伪装成三族**：Round 30 把 `acquire` 记成「清理尾声＋裸 raise 迁移＋环尾回边」三族
   混合，本轮块级转储＋hunk 一手重建证明它是单个归属错误的三个症状。教训：多 hunk 之前先做「一处
   错位能否同时解释全部 hunk」的检验，别按 hunk 数开诊断线。
3. **代理的转储探针必须验长度**：`blockdump_b_regions.txt` 是 0 字节的坏探针输出（不是「空结果」），
   归档时已换成编排方在落地核上重跑的同形转储 `blockdump_landed_regions.txt`（B364 从 `pred=B242,B314`
   的 `role=LOOP_ELSE` 变回臂尾，`succ=B568` 不变）。凡归档的探针日志都要断言非空。
4. **CONTROL 只能当 sha 级不变性证据**：`c2`／`c6` 在落地核上本就失败，代理原稿的「全部 CONTROL 保持
   matched」头注释是错的，入库前已按实测改写为 sha 级判据（见 `arm-design.md` 第五节）。

## 六、残余与移交（Round 32 目标池，逐条带本轮读数）

* `w_c_handler_nested_raise_deep` `64/63 j2 t51` —— 本轮见证第三成员，前驱不满足判据③，属另一形状。
* `default_event_source.pyc :: events` `510/508`（`jump_diffs 2`）—— 需 R30-C2（裸体块就地渲染）＋
  那两跳转槽两条判据，不可拆成本轮单判据。
* `#61` R30-B3（汇合块两臂同时取消认领）—— 门禁齐备、官方尺中性，继续待一个能翻靶子的组合。
* `risk_calculation/function.pyc :: save_testds_to_json` `314/310`（缺**重复**清理副本，需发射侧「增」）
  与 `replace_utils.pyc :: decrypt_database_url` `295/324`（过量发射，需放弃发射侧）—— 同族两兄弟，
  都是发射侧，不是本轮归属侧。
* `instance.pyc :: _init_config` `86/84` —— R16 J1 在册反例，受保护，勿再取。
* `clock_worker` `1275/1291`（D2 过量 ＋16、D3 换位）、`matcher :: match` `713/689`（281 指令区域被
  推迟到函数尾并旋转）、`strategy :: tick_worker_thread` `268/247`、`quote.pyc` `67/81`（含
  `load_bars_from_hundsun 477/470`）、`r29x_01 <module> 142/138`。
* 在册观察项：`gtn_api` 产物文本变化（两条尺均判忠实）；代码内注释标签写作 `R31-B` 而本轮发货名
  `R31-C` —— 改名会改动被测量字节，须整轮重测，故留作字面债。
* 锚点新要求：落地核上 `r31a_witness.pyc` 必须读 `3/4`、`r31a_control.pyc` 必须读 `5/7`，且失败对
  只能是 `c2`/`c6`；Round 32 电池 = `anchors100.txt`（本轮 `anchors98.txt` ＋ 这两个新件）。
  重生成合成件时 `py_compile` 必须显式给 `cfile`，因为电池读的是同目录兄弟 `.pyc`。
