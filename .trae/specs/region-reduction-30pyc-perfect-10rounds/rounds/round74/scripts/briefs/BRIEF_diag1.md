# R74 · diag1（只读诊断）BRIEF — 77 失败单元子机理归属

## 0. 使命

只读诊断（**不出 spec、不写 repo、不碰 `*OK.py`**），把 R74 基线 77 个失败单元按
**「可判据的子机理」**逐单元钉死，给 fix1/fix2/fix3 三批分靶与重叠面证据。

工作区：`D:/Temp/opencode/r74gate/diag1`；基线 HEAD = **`6bb9716a`**（R73 落地）。

## 1. 输入

- `filecat.json`（35 文件 / 77 单元，含每单元真尺 verdict）、`fail74.txt`、
  `fam74_r74.json`（中心已按真尺聚类：F-ABSORB 67 / F-PAD 8 / F-POLARITY 1 / F-OTHER 1）、
  `dump/crosstab74.txt`（家族 × 异常区交叉表：F-ABSORB OUT58/IN9、F-PAD OUT6/IN2、
  F-POLARITY OUT1、F-OTHER OUT1）、`G3v_pycverify_r73.json`（基线）。
- R73 交接事实：`r73gate/fix2/FACTS.md`（abs1 根因表、orphan child 成因、klinedata 丢语句）。

## 2. 必答问题（每个都要**可复现的读数**，禁止形容词）

1. **F-ABSORB 67 单元三拆**（fix1 主攻面）：
   - **A 类 same-target 共享 else**（abs1 `_is_nested_if_else_pattern` 豁免可解）：单元清单 + 判据
     （链成员条件跳转是否汇聚同一块，逐链打印 `argval→block`）；
   - **B 类 orphan-child 丢语句**（合并后 child 不在 `blocks/then_blocks`，须 generator 补发射）：
     逐单元打区域树（`blocks` / `then_blocks` / children 覆盖差），给出哪些单元合并后会出现
     「child 有语句但生成器跳过」；
   - **C 类 其余**（boolop 链尾/链内其他归约）：给出判据行与首分歧（`dump/crosstab74.txt` 有 kind）。
   - 输出形态表：`落点同/len 变` vs `落点不同指令`（沿用 R73 细分口径）。
2. **11 个 inside-try 单元逐行根因**（fix3 主攻面，按用户裁定）：
   `quote.run_tick_socket`、`trade_info_utils.trade_operation`、
   `real_quote.one_prod_to_ndarray` / `get_real_minute_kline` / `get_cache_l2_data_by_one`、
   `finance.get_fields`（R73 记 IN-TRY k=18）、`flytools.modify_batcktes_info`、
   `email_utils.send_email`（et=5）、`realtime_event_source.clock_worker`、
   `cgroup_utils.set_cgroup_config`、`strategy.tick_worker_thread`。
   逐个给：异常表条目数、首分歧偏移是否在 try 区、产品 vs 原表条目差异、
   **是「共享尾被吞」「handler 出口错位」还是「try 内 elif/boolop 链」**（三选一 + 证据行）。
3. **F-PAD 8 单元的 pad 残留形态**（fix2 主攻面）：`trade_info_utils.kill_trade_process /
   query_trade_strategy_info / query_strategy_id`、`quote.check_frequency / run_tick_socket`、
   `flytools.modify_batcktes_info`、`function.reconnect`、`trade_live_broker.etf_basket_order`
   —— 与已落地 `[R73-fix1 · F-PAD]`（pad_e2fix）的关系：**同一形态未覆盖**还是**新形态**？
4. **重叠面标注**：同单元被多批命中时（IN 且属某家族），写明归属建议 + 为何不冲突的证据。

## 3. 方法与工具

- 只读探针脚本命名 `d74_*.py`；产物落 `dump/`；**每条命令 <300s**；分片跑大文件。
- 首分歧/异常表复用中心件：`firstdiv73.py`、`exctable73.py`、`tryverdict73.py`
  （已重定向到 round73 G3v；如需自定义输出加 `--out`/改输出路径，别覆盖中心 dump）。
- mandated 单点复核可用 `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py
  single <pyc>`（对 repo 落地产物，只读）；**禁 `--source` 指向未验证自造产物之外的写操作**。
- 家族判定可复用 `fam73.py`（已放本区）。

## 4. 交付

- `FACTS.md`：§1 三拆清单（A/B/C 逐单元表）、§2 11 单元根因表、§3 PAD 形态表、§4 重叠面表、
  每节附原始 dump 文件名；文末「对 fix1/fix2/fix3 的建议与风险」。
- `dump/`：全部探针原始输出（json/jsonl/txt）。
- **不出 `specs/`**（本批无 spec 交付）。

## 5. 硬规则

只读 repo、不提交不 push、不动 `*OK.py`、不跑 402 全量、不与他批互相改文件；
读数一律写进 `FACTS.md`，禁止口头结论。
