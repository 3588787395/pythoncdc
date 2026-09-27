# R74 · fix2（修复工程师）BRIEF — F-PAD 残留 8 + F-POLARITY 1 + F-OTHER 1（10 单元）

## 0. 使命

R73 已落地 `[R73-fix1 · F-PAD] pad_e2fix`（generator +29，抑制 then 臂物化 `return None`
后的隐式 else 尾块）与 `[R73-F-POLARITY]`（analyzer+generator）。本轮收掉**残留 10 单元**：

| 家族 | 单元（文件 :: 函数） |
|---|---|
| F-PAD 8 | `trade_info_utils :: kill_trade_process`、`:: query_trade_strategy_info`、`:: query_strategy_id`、`fly/data/quote :: check_frequency`、`:: run_tick_socket`（**且 IN**）、`fly/common/flytools :: ProcessWrite.modify_batcktes_info`（**且 IN**）、`plugin_system_trade/function :: reconnect`、`trade_live_broker :: etf_basket_order` |
| F-POLARITY 1 | `trade_live_broker :: TradeLiveBroker._sync_worker` |
| F-OTHER 1 | `fly/data/quote :: load_get_price` |

工作区：`D:/Temp/opencode/r74gate/fix2`；基线 HEAD = **`6bb9716a`**。

## 1. 输入

`filecat.json`、`fam74_r74.json`、`dump/crosstab74.txt`（家族×异常区）、`G3v_pycverify_r73.json`、
`fail74.txt`；R73 落地形态参考：repo 内 `[R73-fix1 · F-PAD]`、`[R73-F-POLARITY]` 标记处
（`core/cfg/region_ast_generator.py` / `region_analyzer.py`，**只读参考**）。

## 2. 诊断与分靶

1. 对 10 个单元逐个取首分歧（`dump/crosstab74.txt` 有 kind/位置；细看用
   `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc>` + `disf.py`）。
2. **判定与已落地 pad_e2fix 的关系**：
   - 同形态未覆盖（判据前置条件未吃下本形）→ 扩展判据（同层结构身份，**不许扩到跨层**）；
   - 新形态（then 区为空 / pad 的另一侧 / else 物化在另一条路）→ 新判据行。
3. F-POLARITY 残留 `_sync_worker`：确认是否仍是极性翻转（`POP_JUMP_*_IF_TRUE/FALSE` 配对）
   与 R73 落地判据的差别（只读比对 R73 标记处）。
4. F-OTHER `load_get_price`：给出**它到底属于哪类**（先别贴 OTHER 标签了事），
   若可归入 PAD/ABSORB 既有族，写明证据；确不可归则给出独立判据行。

## 3. 拆臂与闭环（单臂单 edit）

- 每处编辑独立成 spec（`specs/pad7_<n>.json`、`specs/pol7_<n>.json`、`specs/oth7_<n>.json`），
  各自跑下面闭环；**合并臂 `padm` 最后单独跑一遍**。
- 闭环：
  a. `mbuild74.py <arm> specs/<x>.json` 锚点断言全过（LF 恰 1 次、BOM/行尾断言）；
  b. 官方靶支：`h62.py run --arm=<arm> --list=<靶清单>` **逐项不回退**；
  c. mandated：对**本批命中文件**逐支 `pyc_verify.py single --source build_<arm>/…`
     → 失败单元减少且**零新增**；**trade_info_utils 若 5/5 全清即 mandate**
     （注意其 2 单元属 F-ABSORB，可能需与 fix1 合臂 —— 在 FACTS 标注，交中心）；
  d. 金丝雀 4 支 sha16 == pin；`closeout69.py battery landed <arm>` worse=0；
  e. `sstrict67.py build_<arm> <75 缺陷名单> out` → 新增缺陷 0。
- 若某 edit 让其他家族单元变差 → 自判弃臂并记录（ADR-1）。

## 4. 硬规则

不改 repo（`land74` 只 dry-run）；不手改 `*OK.py`；每条命令 <300s；
ALLOWED = `region_ast_generator.py` / `region_analyzer.py` / `comprehension_generator.py`；
spec 三要素注释 + 同层结构身份判据（无函数名/文件名/偏移阈值/名字白名单/新 self 状态/
跨层 `region.entry in r.blocks`）；h62 列表 LF 无 BOM；产物名 `:` 走 `.replace(':','_')`。

## 5. 交付

`FACTS.md`（10 单元根因表、每臂 a–e 读数、与 fix1/fix3 重叠面、trade_info_utils 合臂建议）、
`specs/*.json`、`synth/` 最小复现（至少 1 条 PAD 残留形态 + 1 条负例）、`dump/` 原始读数。
