# R75 · fix2（修复工程师）BRIEF —— F-PAD 8 + F-POLARITY 1 + F-OTHER 1 = 10 单元

## 0. 使命与工作区

工作区：`D:/Temp/opencode/r75gate/fix2`；基线 HEAD = **`982cd398`**。
目标：把 10 个非 absorb 残差单元按判据拆开、单臂单 edit 自证（ADR-1），mandate 候选 =
`trade_info_utils` 36/41→41/41 中的 3 个 F-PAD 单元、`quote.check_frequency`。

## 1. 靶单元（10，来自 `center/fam75.json` + `dump/crosstab75.txt`）

| 文件 :: 单元 | 家族 | IN/OUT | 首分歧要点（fam75 reason） |
|---|---|---|---|
| `trade_live_broker :: _sync_worker` | F-POLARITY | OUT | `POP_JUMP_FORWARD_IF_TRUE → POP_JUMP_FORWARD_IF_FALSE`（len 346/345） |
| `trade_live_broker :: etf_basket_order` | F-PAD | OUT | `EXTENDED_ARG 1 ≠ 3`（len 相同，bytecode 位移族） |
| `quote :: load_get_price` | F-OTHER | OUT | `POP_JUMP_FORWARD_IF_FALSE → POP_TOP`（产品多/少一层判断） |
| `quote :: check_frequency` | F-PAD | OUT | target 同、offset 560→562（纯位移 2 字节） |
| `quote :: run_tick_socket` | F-PAD | **IN** | `POP_JUMP_FORWARD_IF_FALSE → EXTENDED_ARG`（与 fix3 重叠） |
| `trade_info_utils :: kill_trade_process` | F-PAD | OUT | **R74 pad7_89 回退点**（strict seq_len 577→578） |
| `trade_info_utils :: query_trade_strategy_info` | F-PAD | OUT | |
| `trade_info_utils :: query_strategy_id` | F-PAD | OUT | |
| `function :: reconnect` | F-PAD | OUT | `LOAD_GLOBAL datetime → NOP`（产品多 NOP） |
| `flytools :: ProcessWrite.modify_batcktes_info` | F-PAD | **IN** | `LOAD_CONST None → NOP`（与 fix3 重叠） |

## 2. 必答问题

1. **F-PAD 判据的结构含义**：pad = 产品比原 pyc **多/少一条空转或占位**（NOP/EXTENDED_ARG/POP_TOP）。
   逐单元判定是 (i) region 归约多发一条、(ii) 布尔短路多一层、(iii) 纯位移（应判 SAME 而非 PAD）？
   给 `lenA/lenB`、`firstA/firstB`、`origTryDepth/prodTryDepth` 三列读数。
2. **`kill_trade_process`**：R74 pad7_89 曾在此产生 strict NEW defect（seq_len 577→578）。给出
   seq_len 差 1 的指令级定位，本批必须证明 **strict 无新增缺陷**。
3. **F-POLARITY `_sync_worker`**：真极性翻转（产品把 `IF_TRUE` 反写成 `IF_FALSE` 且目标改写）还是
   归约时 `not` 消去造成的等价改写？给出原 pyc 与产品对应源码行（lineA 1364 / lineB 841）对照。
4. **重叠面**：`run_tick_socket`、`modify_batcktes_info` 属 IN（fix3 面）；标注证据交中心，不得自合并。

## 3. 修复与拆分

- 单臂单 edit（`specs/pad8_<n>.json`），可改 `region_analyzer` / `region_ast_generator` /
  `comprehension_generator`；最后合并臂 `pad8m`。
- 闭环（每臂）：`mbuild75.py <arm> specs/<x>.json` 锚点断言 → 官方 41 靶 `h62.py run --arm=<arm>
  --list=list41.txt` 逐项不回退 → mandated `trade_info_utils`/`quote` 单支 `pyc_verify.py single`
  单元只减不增 → 金丝雀 4/4 → `closeout69.py battery landed <arm>` worse=0 →
  `sstrict67.py build_<arm> <缺陷名单> out` 新增缺陷 0（尤其 `kill_trade_process`）。
- synth：每类 pad（多 NOP / 少 NOP / 极性翻转）≥1 条复现 + 1 条负例（负例 sha 与落地逐字节相同）。

## 4. 硬规则

不改 repo（`land75` 只 dry-run）；不手改 `*OK.py`；每条命令 <300s；spec 三要素注释 + 同层结构
身份判据（无函数名/文件名/偏移阈值/名字白名单/新增 self 状态/跨层 `region.entry in r.blocks`）；
**任何他支回归即整件拒收**；**不得以少发射换全绿**；h62 列表 LF 无 BOM；产物名 `:` → `_`。

## 5. 交付

`FACTS.md`（10 单元 i–iii 判定表、每臂 a–e 读数、与 fix1/fix3 重叠面）、`specs/*.json`、`synth/`、
`dump/` 原始读数。
