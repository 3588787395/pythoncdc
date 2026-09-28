# Round 74 · OUTCOME

起点 = Round 73 落地 `6bb9716a`；本轮 start commit = `cd1cd670`（BRIEF + 四批 brief）。
本轮落地 = **m74**（fix1 `abs1.json` + fix1 `abs2_orphan_child_emit.json` 与 fix3 `try7_3.json`
合并的生成器臂 `abs2t3.json`），落地字节：

| 文件 | edits | 行数 | 字节 | BOM | CRLF | sha256 |
|---|---|---|---|---|---|---|
| core/cfg/region_ast_generator.py | 6 | +185 | 3 214 913 → **3 226 993** | True | 51751 | `e54dd931e91e9f6a…` |
| core/cfg/region_analyzer.py | 1 | +34 | 1 778 913 → **1 781 244** | False | 28371 | `d6b11bcabf1a4256…` |
| core/cfg/comprehension_generator.py | 0 | 0 | 115583 | False | 2115 | `b432a35580989852…`（未改） |

裸 LF 均 0；`mkfinal74 m74` 链式锚点各恰出现 1 次；`mbuild74 m74` → `mirr_m74`；
`land74` dry-run 与 `--apply` 双双断言 replay == measured mirror；landproof `mirr_m74`
33 个 core 文件 same=33 diff=0。

## 1. 指令与裁定（对用户裁定的定量回应）

用户最高裁定：「就是嵌套 try-except 问题」。本轮中心定量判决（`logs/TRYVERDICT_r74.txt`，
读数来自 77 个失败单元 / 76 可探）：

- 原 pyc **无异常表 37 / 有异常表 39**，`et_same 49 / et_diff 27`，`prod_deeper=0`；
- **首分歧在异常区内 11/76、区外 65/76**（控制流 73 / 字节码 3）；
- 结论（两读数并列）：裁定对 **11 单元 inside-try 子族成立**、对其余 65 个单元定量上
  不是单一根因；本轮对 inside-try 子族实修 2 个单元
  （`real_quote.one_prod_to_ndarray`、`real_quote.get_cache_l2_data_by_one`，
  41/45 → 43/45），其余 9 个转下轮。

## 2. 四批产出与中心 ADR-1 独立复测

| 臂 | spec | ADR-1（77 单元串行复测） | 判定 |
|---|---|---|---|
| absj | `abs1` + `abs2_orphan_child_emit` | changed 5 **WORSE=0** IMPROVED=5 | 通过（未并 try） |
| absjt | absj + `try7_10d`（7 edits） | changed 10 **WORSE=1** `real_quote.get_tick_direction hunks_norm 2→3` | **拒收** |
| absj9 | absj + `try7_9`（7 edits） | changed 10 **WORSE=1**（同上单元） | **拒收** |
| **absj3** | absj + `try7_3`（5 edits） | changed 7 **WORSE=0** IMPROVED=7 | **采纳 = m74** |
| pad7_89 | fix2 `pad7_8`+`pad7_9` | 官方 REGRESSION=1（trade_info_utils 40/40→39/40）、strict NEW=1 | 拒收（不另跑 ADR） |

`adr74_absj.json` / `adr74_absjt.json` / `adr74_absj9.json` / `adr74_absj3.json` 全部入档。
两件 try 臂被拒的理由、以及它们在 mandated/官方上的收益（real_quote +2、quote +1）都如实保留，
交 R75 处理 `get_tick_direction hunks_norm 2→3` 这一处回退。

## 3. 落地前后读数（中心独立重跑）

- **mandated 尺（`scripts/pyc_verify.py`，pylingual `compare_pyc`）**：
  6540/6617 = 98.84% → **6546/6617 = 98.93%**（+6 单元；success 367→368、failure 35→34）
  **转绿 1 支：`IQCommon/data/local_finance.pyc` 20/21 → 21/21 ⇒ mandate 达成**；转红 0；
  同状态位移 finance 29/32→31/32（+2）、real_quote 41/45→43/45（+2）、
  trade_live_broker 114/128→115/128（+1）。
- **官方尺（`scripts/pyc_batch_verify.py batch --round 74 --all`）**：
  402 verified / 0 failed、ok 394、partial 8、**5717/5746 = 99.50% → 5720/5746 = 99.55%**、
  Traceback 0、FAIL 0。
- **官方 41 靶 `h62 ab`**：SAME=34 IMPROVED=2（real_quote 40→42、trade_live_broker 111→112）
  MOVED=5 REGRESSION=0 ERR=0，fully matched 36→36。
- **严格尺（45 靶去重口径 `G4p`）**：ok **1704 → 1710**、缺陷 **75 → 69**、
  TALLY IMPROVED=4 REGRESSION=0 SAME=40、defect-worse=0（原始打印口径 1853→1859、缺陷 76→70）。
- **电池**：`closeout69 battery prev landed` → worse-than-landed **0** repro。
- **金丝雀**：G2 4/4 pin 全中、sha SAME=4/4；G2b quotation mandated 152/153（唯一 failure
  `change_his_to_forward`，无新增）。

## 4. try7_3 臂的收益来源（为什么不是 try7_9/7_10d）

`try7_3` = 5 处生成器编辑（anchor 141/225/200/230/190），不包含 `try7_9` 新增的
anchor 436/145 两处；后两者在 ADR-1 上把 `real_quote.get_tick_direction` 的 hunk_norm
2→3，按 ADR-1「任何回退即整件拒收」否决。`try7_3` 保留了 try 子族中
`one_prod_to_ndarray` / `get_cache_l2_data_by_one` 两个单元的修复，
并把 `quote.get_real_from_zeromq` 的 official 段差从 |d|=551 收敛到 550（无回归）。

## 5. 门禁（gates74，全过）

G0 三支 ast+py_compile OK，跨层 `x.entry in y.blocks` 模式 raw 9→10、code-only 7→8，
其中 **sanctioned-try-guard=1 / other=0**（唯一新增为用户裁定对应的
`region.entry in _ft3_rr.blocks` TryExceptRegion 守卫，diff 证据入档）⇒ PASS；
G1 SAME=37 IMPROVED=2 MOVED=5 REG=0 ERR=0 ⇒ PASS；G2 金丝雀 4/4 ⇒ PASS；
G2b quotation 152/153 ⇒ PASS；G3 batch 402/0 failed ⇒ G4 99.55% PASS；
G3v 8 分片 6546/6617、转红 0 ⇒ PASS；G4′ ok 1704→1710 缺陷 75→69 NEW=0 ⇒ PASS；
G5 索引 402→402、round-stamp-only=400、substantive=2（improved=2 worsened=0 other=0）
⇒ PASS；G5′ blast changed=7 unresolved=0 **REGRESSED=0**；G6 电池 worse=0；
G7 逐项 IMPROVED=1 SAME=81 REGRESSED=0 ⇒ PASS；landproof 33/33 diff=0；
G8 402/402 *OK.py 在位 + py_compile bad=0 + Traceback 0 ⇒ PASS；
G9 合成 25 臂 IMPROVED=1 REGRESSED=0 SAME=24 ⇒ PASS；
Land74 replay（HEAD 字节 + m74 spec == worktree）两文件 **PASS**。

> 门禁仪器本轮两处判据按实测收紧/校准并入档：G0 增加 code-only 新增行的
> sanctioned/other 拆分（sanctioned = TryExceptRegion 守卫上下文，raw/code/sanctioned
> 三个数字并列打印）；G5 把 substantive 差异按方向拆成 improved/worsened/other
> （只有 worsened/other 才 CHECK），并跳过 `last_tested_round` 噪声。

## 6. 被拒候选与残留（交 R75）

- `try7_10d` / `try7_9`：ADR-1 拒收，唯一回退 `real_quote.get_tick_direction`
  `hunks_norm 2→3`；它们能带来 quote +1、real_quote +2，值得在修掉该回退后重测。
- fix2 `pad7_89`：官方 REGRESSION=1 + strict NEW=1（`kill_trade_process` seq_len 577→578）拒收；
  fix2 尚有 6 个单元（`quote.check_frequency` / `run_tick_socket`、`function.reconnect`、
  `trade_live_broker.etf_basket_order` / `_sync_worker`、`quote.load_get_price`）未攻。
- fix3 无 `FACTS.md`、无合并臂 `trym`；`trade_operation` target_diff #94 仍开放。
- 最大残留：trade_live_broker 13、quote 11、trade_info_utils 5、flytools 1、email_utils 1。

## 7. 未手改产物 / 工具链

未手改任何 `*OK.py`；7 支变更产物全部由 `scripts/pyc_batch_verify.py batch --round 74 --all`
批量重写（G5p changed=7、identical 395、unresolved=0）。

## 8. 归档与提交

`rounds/round74/`（OUTCOME.md + logs/EVIDENCE.md + logs/gate 20 份 + logs/dump +
specs + batches diag1/fix1/fix2/fix3 + scripts）；tasks.md 记 Task 74；
提交含 sha256 与读数证据并 push。
