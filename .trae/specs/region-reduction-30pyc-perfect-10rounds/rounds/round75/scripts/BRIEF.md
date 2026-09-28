# R75 · 任务书（BRIEF.md）—— 34 支失败 pyc / 71 单元，四批攻剩余残差

## -1. 用户裁定（最高优先级，延续 R73 `b355043e` / R74 已定量复核，不得推翻）

用户明确指认：**剩余控制流失败的根因就是「嵌套 try-except 问题」**。
R74 已对该裁定做中心定量读数（77 单元 / 76 可探：首分歧 inside 11 / outside 65），
R75 在落地后的 71 单元上重跑同口径（`center/dump/{firstdiv75,exctable_diff75,tryverdict75,crosstab75}.txt`）：

| 读数 | R75 基线（71 失败单元，tryverdict 可匹配 70） |
|---|---|
| 原 pyc 有异常表 `with_et` | **36**（nest=0，即原表**无嵌套**） |
| 产品多建 try 层 `product_nested_try` / 深度≥2 | **67 / 30** |
| 首分歧在异常区内 IN / 区外 OUT | **9 / 62**（crosstab75） |
| 异常表逐条 `SAME` / `DIFF` | 见 `exctable_diff75.txt`（DIFF = 表条目数/范围不一致） |

**裁定对 9 单元 inside-try 子族成立**（fix3 主战场）；对其余 **62 单元定量上不成立**，
须以同层次结构判据另解（fix1/fix2 承担）。两组读数并列存档、保留分歧而不掩盖。
**不改尺、不以少发射换全绿**。

## 0. 使命与基线

- 基线 HEAD = **R74 提交 `982cd398`**：mandated `6546/6617 = 98.93%`（34 支 failure、**71 失败单元**）；
  官方 `5720/5746 = 99.55%`（402 verified / 0 failed、ok 394、partial 8）；
  严格尺 45 靶去重 **ok 1710 / defects 69**（原始 1859/1929、defects 70）；
  金丝雀 4/4 pin 不变；quotation mandated 152/153。
- 每批产出**候选 patch spec 并在镜像上闭环自证**（只读 repo、禁落地），按子机制**单臂单 edit 拆开自证**（ADR-1）。
- **本轮 mandate：≥1 支 pyc failure → success**。已知最短路径（按剩余单元数升序）：
  1. `real_quote.pyc` 43/45 → **45/45**（仅 2 单元：`get_real_minute_kline` IN、`get_tick_direction` OUT——
     后者正是 R74 拒收臂 absjt/absj9 的唯一回退点 `hunks_norm 2→3`，本轮须先解它再谈合臂）；
  2. `jq_trans_module` / `risk_calculation/__init__` / `future_contract_info` / `ptradeAccount` 各 2 单元；
  3. `trade_info_utils` 36/41 → 41/41（5 单元：F-PAD 3 + F-ABSORB 2，含 `trade_operation` target_diff #94）；
  4. `klinedata` 61/64 → 64/64（3 单元，注意 R73 absm 尾语句教训）、`wizard_quant_api` 3、`order_api` 3。

## 1. 家族地图（R75 中心实测：`center/fam75.json`，71 单元按真实 ruler verdict 聚类）

| 家族 | 单元数 | 异常区外 OUT | 异常区内 IN | 主战场文件 |
|---|---|---|---|---|
| **F-ABSORB** | **61** | 54 | **7** | trade_live_broker 11、quote 8、klinedata/wizard_quant_api/order_api 各 3、trade_info_utils/jq/real_quote/risk_calc/future_contract/ptradeAccount 各 2，其余 21 支各 1 |
| **F-PAD** | **8** | 6 | **2** | quote 2（`check_frequency`、`run_tick_socket`）、trade_info_utils 3、flytools 1（IN）、function 1、trade_live_broker `etf_basket_order` 1 |
| **F-POLARITY** | 1 | 1 | 0 | trade_live_broker `_sync_worker`（`POP_JUMP_FORWARD_IF_TRUE → FALSE`） |
| **F-OTHER** | 1 | 1 | 0 | quote `load_get_price` |

失败单元分布（34 支）：trade_live_broker 13、quote 11、trade_info_utils 5、
klinedata/wizard_quant_api/order_api 各 3，jq/real_quote/risk_calculation/future_contract_info/
ptradeAccount 各 2，其余 22 支各 1（明细 `filecat.json` / `dump/fail_units75.txt`）。

## 2. R74 交接（直接决定本批走向）

- **已落地 m74 = `abs1` + `abs2_orphan_child_emit` 与 `try7_3` 合并的 `abs2t3`**（+6 单元、local_finance 转绿）。
- **absjt（absj+try7_10d）与 absj9（absj+try7_9）被 ADR-1 拒收**：两臂共同唯一回退
  `real_quote.get_tick_direction hunks_norm 2→3`。→ **fix1/fix3 若触该单元，必须证明 hunk 回归为 0。**
- **fix2 `pad7_89` 拒收**：官方 REGRESSION=1（`trade_info_utils` 40/40→39/40）+ strict NEW=1
  （`kill_trade_process` seq_len 577→578）；未攻单元 `quote.check_frequency / run_tick_socket`、
  `function.reconnect`、`trade_live_broker.etf_basket_order / _sync_worker`、`quote.load_get_price`。
- **fix3 缺 `FACTS.md` 与合并臂 `trym`**（R74 只交付了 `try7_1..11.json`），本轮须补齐交付闭环。
- `trade_operation` **target_diff #94**（R70 遗留）仍在 `trade_info_utils` 5 单元内。

## 3. 批次分工

| 批 | 主攻 | 交付 |
|---|---|---|
| **diag1** | 只读：61 F-ABSORB 单元子机理归属（same-target 共享 else / orphan-child / handler 出口错位 / 其他）+ 9 inside-try 逐行根因 + `get_tick_direction` 回退点解剖 | `FACTS.md` + `dump/` 探针（不出 spec） |
| **fix1** | **F-ABSORB 61 单元**（analyzer/generator 同层次结构判据，按子机制单臂单 edit） | `specs/abs*.json` 合臂 + 闭环读数 |
| **fix2** | **F-PAD 8 + F-POLARITY 1 + F-OTHER 1 = 10 单元** | 每 edit 单臂 spec + 闭环读数 |
| **fix3** | **inside-try 9 单元**（按用户裁定走 try/except 归约路径） | 单臂 spec + 合并臂 `trym` + 闭环读数 + `FACTS.md` |

重叠仲裁：同一单元可能被多批命中（`quote.run_tick_socket` = F-PAD ∩ IN、`flytools.modify_batcktes_info`
= F-PAD ∩ IN、trade_live_broker 多单元判据重叠）——**批次不得跨判据点自合并**，
全部标注重叠面交中心（`center/adr75.py` 同尺复测）裁定；中心合并臂唯一、落地唯一。

## 4. 硬规则（每批必守）

1. **不改 repo 任何文件**（`F:/Downloads/pythoncdc-main` 全程只读；`land75` 只许 dry-run，禁 `--apply`）；
   禁手改任一 `*OK.py`；402 全量扫描禁止在批内做（归中心）。
2. 每条命令 **<300s**；大活拆分片；dis/region 侧探针**局部 import**（避免 try 内 NameError）。
3. 镜像闭环用本工作区工具：`mbuild75.py <arm> specs/<x>.json`（锚点必须 LF 归一后恰出现 1 次）→
   `h62.py run --arm=<arm> --list=…`（官方读数）→ `python -X utf8 -m scripts/pyc_verify.py single <pyc>
   --source build_<arm>/<产物>`（mandated）→ `closeout69.py battery landed <arm>`（worse=0）→
   `sstrict67.py build_<arm> <名单> <out>`（无新增缺陷）。
4. **金丝雀 4 支 sha16 不得变**：quotation `3eb76e512df9ab1e`、market_time `af77224b34b203c4`、
   IQCommon datetime_func `e711b8ea86d49a15`、IQData datetime_func `9d09af09249da177`。
5. **ADR-1**：任何他支回归即整件拒收；**不得以少发射换**（少一条语句、少一个 load 都是 WORSE）；
   位移族要 hunk 严格子集 + first_diff 回移 + Σ|Δ| 不升。
6. spec 三要素注释（识别条件 / 归约方式 / AST 映射）；同层次结构身份判据：无函数名、无文件名、
   无偏移阈值、无名字白名单、无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。
7. 产物名带 `:` 时 `mbuild`/`h62` 做 `.replace(':','_')`；h62 列表文件 LF 无 BOM、跑前删除旧 jsonl。
8. 每批结束交 `FACTS.md`（读数表 + 与他批重叠面 + 原始 jsonl 索引），spec 放 `specs/`，复现放 `synth/`。

## 5. 输入清单（每工作区已就位）

- `filecat.json`（34 文件 / 71 单元明细）、`dump/fail_units75.txt`、`center/fam75.json`（家族判定）、
  `center/dump/crosstab75.txt`（家族×异常区交叉表）、`rounds/round74/logs/gate/G3v_pycverify_r74.json`（基线 G3v）、
  `center/dump/strict_base75.json`（严格尺基线 1859/1929、defects 70）。
- 工作区：`D:/Temp/opencode/r75gate/{diag1,fix1,fix2,fix3,center}`（工具已从 r74gate 中心件重定向）。
- 中心件：`adr75`（=`adr73.py`，路径重定向）、`gates75`（=`gates74.py`）、`merge_g3v75`、`land75`、
  `mkfinal75`、`mkmirr_prev75`、`mkarchive75`、`tryverdict_summary75`。
