# Round 73 · fix1 · F-PAD 家族 —— FACTS

工作区：`D:/Temp/opencode/r73gate/fix1`  ·  基线 HEAD `1137c155`（R72 落地 `8d136040`，core 字节未变）  ·  仓只读（全程无改/无 commit/无 push/无 402 全量扫描，末次 `git status --porcelain` 仅历史遗留 `??`）

## 0. 结论（一句话）

**主候选 `specs/pad_e2fix.json`（臂 `pad6`，单 edit，+29 行）**：mandated 命中 **4 支 pyc failure→success**（order / slippage / oauth2 / flyAccount，共清 6 个单元，`NEW=0`），官方尺/严格尺/金丝雀/82 支 synth battery **全零回归**，ADR-1 位移指标 **88 单元 0 变差、6 单元严格变好**。

## 1. 新鲜复扫（基线确认）

- `dump/scan_fam73_r73.txt` · `dump/fam73_pad_r73.json`：88 单元 = F-ABSORB 67 / **F-PAD 14** / F-POLARITY 2 / F-OTHER 2 / F-TERNARY 2 / F-EXCTABLE 1，verdict `cf 84 + bc 4`（与 `filecat.json` 41 支 88 单元一致）。
- F-PAD 14 单元清单 `pad14_r73.txt`，涉及 9 支 pyc `fampad9.txt`：
  trade_live_broker.etf_basket_order · quote.check_frequency · quote.run_tick_socket ·
  trade_info_utils.kill_trade_process / query_trade_strategy_info / query_strategy_id ·
  flytools.set_userid_containerid_dict · flytools.ProcessWrite.modify_batcktes_info ·
  oauth2.HSIDOAuthCallbackHandler.post · oauth2.OAuthCallbackHandler.post ·
  order.Order.mark_cancelled · slippage.SlippageHelp.set_slippage · function.reconnect ·
  flyAccount.TradeAccount.register_async_callback

## 2. 根因（已实测、可复现）

产物在 then 臂多物化一条 `return None`（重复清理尾声），并把**非源码的隐式收尾**发射成 `else:`；Python 3.11 下两个相邻 4 字节 return-None 尾块的发射次序被对调 ⇒ 条件跳转落点 ±4（F-PAD）。

- 探针 `dump/r2m14_r73.json` / `dump/probe_r2m14_r73.txt`：edit1 站点 5 次命中，全部 `reach_entry=False / all_preds_in_region=False / ext_jump_target=True`（oauth2×2、order、slippage、flyAccount）。
- 产物形状 `padshape.py` → `dump/padshape_{landed,pad1,pad2,pad6}.json`：
  - **DUP（then 内连续两条 return）** 恰好 5 个单元：oauth2×2、order.mark_cancelled、slippage.set_slippage、flyAccount.register_async_callback（= 探针 5 次命中）。
  - **ELSE（if.orelse 单条 return 收尾）** 覆盖：上述 5 个 + quote.check_frequency、trade_info_utils.kill / query_strategy_id、flytools.set_userid、flytools.modify。
  - 既无 DUP 也无 ELSE：quote.run_tick_socket、trade_info_utils.query_trade_strategy_info、function.reconnect、trade_live_broker.etf_basket_order。
- 机制实验（编译 A/B）：带 `else: return None` → `is_final→末块`；去掉 else → `is_final→中间块`（= ORIG 模式）⇒ **必须抑制该隐式 else**。

## 3. 候选演化（含被否决件与其证据）

| 臂 | spec | 内容 | 判定 |
|---|---|---|---|
| pad1 / pad4 | `specs/pad_r2m.json` / `pad_e1.json` | 仅 edit1（不可达块不吸进 then 尾） | **否**：mandated `NEW=0` 但 `CLEARED=0`（0 单元变好），ADR-1 `changed=0` |
| pad2 | `specs/pad_r2m_r71.json` | edit1 + edit2（未加前置保护） | **否**：battery 2 支 synth 变差（见下） |
| pad3 | `specs/pad_e2.json` | 仅 edit2（同样未加保护） | **否**：同上 ⇒ 归因 edit2 |
| **pad6** | **`specs/pad_e2fix.json`** | **仅 edit2，块序取值移入既有 pure/then/无 merge/owned 前置之内** | **主候选** |

**pad2/pad3 被否决的硬证据**（`dump/battery_pad2.txt` / `battery_pad3.txt`，与 `landed` 逐列比）：
- `round67_diag6/r67d6_whiletrue_headif.pyc`：landed `2/2 bad=0 d=+0` → 候选 `1/2 bad=1 d=-21`（`dump/strict_repro_*.json`：`w1 seq_len orig=39 decomp=18`，反编译净丢 21 条指令）；
- `round68_diag4/r68b3_headif.pyc`：`4/7 bad=3 d=-1` → `d=-101`（Σ|Δ| 暴涨）。
- **机理**：旧 repl 把 `max(b.start_offset for b in _r71_ee_then)` 放在 `if _r71_ee_pure and _r71_ee_then …` 短路保护**之前**；`then_blocks` 为空的区域抛 `ValueError: max() arg is an empty sequence`，中断该函数发射。修复即 `pad_e2fix.json` 的前置分组（`_r71_ee_gap` 先置 False，仅在前置成立后求值）。
- 复现读数（逐臂重跑同一 repro，非偶然）：`landed 2/2`、`pad1 2/2`、`pad3 1/2`、`pad5(带调试) 1/2`、**`pad6 2/2`**；`r68b3_headif`：`landed 4/7 … d=-1` = **`pad6 4/7 … d=-1`**（`dump/rep1_*.jsonl`、`dump/rep2_*.jsonl`、`dump/h62_pad6_repros.txt`）。

## 4. 主候选 pad6（`specs/pad_e2fix.json`）的 a–e 全量读数

| 项 | 命令 / 产物 | 读数 |
|---|---|---|
| (a) 构建+断言 | `dump/mbuild_pad6.txt`（`mbuild73.py pad6 specs/pad_e2fix.json`） | `edits=1 lines=+29 bytes 3210453 → 3212819 BOM=True`；镜像 33 个 core 文件**仅 `core/cfg/region_ast_generator.py` 不同**，patch 后 `compile()` 通过，anchor 命中数 1 |
| (b1) 官方尺（全 41 支） | `dump/h62_run_pad6_{a,b}.txt`、`dump/all41_{landed,pad6}.jsonl`、`dump/h62_ab_all41_pad6.txt` | `SAME=30 IMPROVED=0 REGRESSION=0 MOVED=11 ERR=0`，11 支 MOVED 全部 `gained=[] lost=[]`，`files fully matched a=33 b=33` ⇒ **逐单元 verdict 集合完全相同** |
| (b2) mandated（9 支 F-PAD 靶） | `dump/mand_pad6_r73.txt` / `dump/mand_pad6_r73.json` | **4 支 success**：order `67/68→68/68`、slippage `6/7→7/7`、oauth2 `10/12→12/12`、flyAccount `23/24→24/24`；flytools `64/66→65/66`（set_userid 清）；**CLEARED 6 单元，NEW 0**，其余文件 `[ok,total]` 逐支相同 |
| (b3) mandated（其余 32 支） | `dump/mand_rest0{0..3}_pad6.json` | 4 批全部 `landed == pad6`（逐文件 `[ok,total]` 相同，无 CLEARED/NEW） |
| (c) 金丝雀 | `dump/canary_pad6.jsonl` + `dump/h62_run_pad6_b.txt` | 4/4 sha 等于 pin：`3eb76e512df9ab1e` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177` |
| (d) synth battery | `dump/battery_pad6.txt`（`closeout69.py battery landed pad6`） | 82 支 repro，**`candidate columns worse-than-landed on 0 repro(s)`**；逐列复核（ok/bad/d）亦 0 差异 |
| (e) 严格尺（全 41 支） | `dump/strict_all41_{landed,pad6}.json` | landed `ok=1639 / 1718 / defects=79`，pad6 `ok=1639 / 1718 / defects=79`，**41 行逐行 defect/missing/extra 集合 `IDENTICAL=True`** |
| ADR-1 位移指标 | `dump/adr73_pad6.json` / `dump/adr73_pad6.txt` | 88 单元：**WORSE=0**；IMPROVED=6（均 `hunks 2→0`、`first_diff → None`、`Σ|Δ| 8→0`）：order.mark_cancelled、slippage.set_slippage、flytools.set_userid、oauth2.post×2、flyAccount.register_async_callback |

产物形状（`dump/padshape_pad6.txt`）：6 个单元 `dup=[] / else_ret=[]`（DUP+ELSE 双清）；quote.check_frequency 的隐式 else 亦被抑制（读数不变，见 §5）；其余单元 `SAME`。

## 5. 未修的 8 个 F-PAD 单元（边界与族归属）

| 单元 | pad6 下产物 | 归因 |
|---|---|---|
| trade_info_utils.kill_trade_process | 完全未变（`SAME`） | 两次编辑均未命中；其 DUP/ELSE 形状与 5 个已修单元不同（else 臂非"纯 return 收尾"或不满足 gap/反序判据） |
| trade_info_utils.query_strategy_id | 完全未变（`SAME`） | 同上（形状 `else_ret=[1080]`，但区域结构不满足判据） |
| trade_info_utils.query_trade_strategy_info | 完全未变（`SAME`） | 无 DUP/ELSE；位移来自另一站点（嵌套 return 尾次序） |
| function.reconnect | 完全未变（`SAME`） | 无 DUP/ELSE（`nret=1`），不同子机制 |
| trade_live_broker.etf_basket_order | 完全未变（`SAME`） | try/except 清理尾声族（与 F-PAD 5 单元不同站点） |
| flytools.ProcessWrite.modify_batcktes_info | 仅受上文 set_userid 删除影响的行号平移，自身形状不变 | 同 else 臂但不满足反序/gap 判据 |
| quote.check_frequency | **隐式 else 被抑制（`else_ret [1012] → []`）**，mandated 仍 `80/92`（该单元仍失败） | 位移量 +38（大位移），非 ±4 尾块对调，**另一子机制** |
| quote.run_tick_socket | 仅行号平移（`ln 1431→1429`） | 不同子机制 |

家族重叠标注：quote 的 2 个单元同时落在 fix2（F-ABSORB 8 单元）/ fix3（F-OTHER 2 单元）靶区；本件对 quote 的**官方/mandated/严格三尺读数均未变**，合并时无需担心本件改动改变其 verdict。

## 6. 只读与纪律自证

- 全程产物写在 `D:/Temp/opencode/r73gate/{fix1,center}`；repo 无任何跟踪文件变更（`git status --porcelain` 仅历史 `??`），HEAD 仍 `1137c155`。
- 所有命令经 `runcap.py` 落盘（PowerShell 重定向会写 UTF-16，故全部改由 Python 侧写文件），单命令 <300s；h62 list 均 LF 无 BOM，跑前删旧 jsonl；从 repo 导入时 `PYTHONDONTWRITEBYTECODE=1`；`r2m_probe.py` 参数用绝对路径。
- 判据行复核（R73 HEAD）：`:185 _is_duplicated_cleanup_exit_return`、`:14865 _if_generate_then_branch`、`:26482 [R35-B]`、`:15549 _if_generate_else_branch`（本件 edit 落点，anchor 唯一）、`:22512 [R71-thenover]`。
