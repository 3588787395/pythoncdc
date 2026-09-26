# R72 fix2 — 头部 control-flow 族候选 FACTS（broker 支）

工作区 `D:/Temp/opencode/r72gate/fix2`；镜像臂 `f2broker`（镜像 `center/mirr_f2broker`，产物 `center/build_f2broker`）。
全程只读 repo，未落任何字节到 `F:/Downloads/pythoncdc-main`，未提交，未 `land72 --apply`，未做 402 全量扫描。

---

## 0. 结论（供中心复测）

单 spec、单文件、清零整支：

- **spec**：`specs/broker_comp_return.json`（file = `core/cfg/comprehension_generator.py`，1 个 edit，anchor 3 行，repl +20 行）
- **靶支**：`IQEngine/plugins/plugin_system_simulation/broker.pyc` mandated `pyc_verify` **35/42 → 38/38（status=success，7 失败单元 → 0，零新增失败）**；官方 24/24 维持
- **ADR-1**：25 支头部/靶文件官方读数 **SAME=23 / IMPROVED=0 / REGRESSION=0 / MOVED=2 / ERR=0**；82 支 battery witness **worse-than-landed = 0**；严格尺两臂 **ok=1186/1243 defects=57 完全相同（零新缺陷）**；4 金丝雀 sha 与 R71 pin 逐字节一致
- **声明**：本 spec 与本轮 fix1 同改 `core/cfg/comprehension_generator.py` → 属「一 spec 一文件」，中心合并时须把两份 edits 合成同一文件的顺序 edits（`mbuild72` 对同文件第二份 spec 会 `assert 'merge them first'`）

---

## 1. 根因（结构身份，非函数名/偏移/阈值）

`core/cfg/comprehension_generator.py::try_generate_comprehension_assign`：

- **缺记账**：`elif last_instr.opname in ('RETURN_VALUE','RETURN_CONST')` 分支只 `all_stmts.append({'type':'Return','value':comp_value})`，**漏 `prev_end = len(instrs)`**；而同 `else` 族的 `_chained_pairs` 分支与 `_ret_succ`/兜底分支（L242-246 / L565 / L568 / L571）都有该记账推进。
- **后果**：`remaining_instrs = instrs[prev_end:]` 仍从 0 开始 → 重新落进 `_generate_remaining_stmts`（L687）对同一块整块重建 → 同型 `Return` 第二次发射。
- **触发条件（本块自身指令结构）**：块 = `[可选闭包前缀] + LOAD_CONST/MAKE_FUNCTION/<listcomp>/…/RETURN_VALUE`，且 `store_instr` 为空、`pre_comp_instrs` 为空（或以 STORE/POP_TOP 等终止符收尾，导致 L273-278 的 `pre_comp` 终止符守卫不发火）。
- **反例（原代码即无 dup，用于限定条件）**：前缀含 `BUILD_TUPLE`（`_all_prior_are_closure` 被提前置 False → L278 `return None`）——`synth/chain_mixed.pyc`、`synth/chain3_plain.pyc`。
- **判据必须区分嵌套**：块内**多**个 `MAKE_FUNCTION <listcomp>`（嵌套推导式，外层在后）时，先被处理的是**内层**，此时若无条件推进记账，会绕过下一轮 `pre_comp` 守卫、把嵌套拆成两条 `Return`（见 §4 事故）。故判据取**本块 `comp_indices` 清单的尾项**。

---

## 2. spec 细节

`specs/broker_comp_return.json`

- `file`: `core/cfg/comprehension_generator.py`（`mbuild72 ALLOWED` 三文件之一）
- `anchor`（3 行，LF 文本，mbuild 归一 CRLF→LF 后 `count == 1` 断言通过）：

```
                elif last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    all_stmts.append({'type': 'Return', 'value': comp_value})
                elif (region_ast_gen is not None and block.successors):
```

  锚点位于原文件 **line 520**（字节偏移 27146，CRLF 文件，BOM=False，插入后行尾仍统一 CRLF）。
- `repl` 三要素注释（识别条件 / 归约方式 / AST 映射）齐备，代码体为：

```
                    all_stmts.append({'type': 'Return', 'value': comp_value})
                    if _comp_loop_idx == len(comp_indices) - 1:
                        prev_end = len(instrs)
```

- **判据自检**：`_comp_loop_idx == len(comp_indices)-1` 是「本块推导式清单尾项」这一**同层指令结构事实**；无函数名/文件名/偏移/阈值启发，无名字白名单，无新增 `self` 状态，无 `region.entry in r.blocks` 跨层模式。

---

## 3. 验证闭环读数（步骤 a–e）

### a. 镜像 + 断言（mbuild72）

```
python -X utf8 mbuild72.py f2broker specs/broker_comp_return.json
  patched core/cfg/comprehension_generator.py edits=1 lines=+20 bytes 108192 -> 110044 BOM=False
mirror ready: D:/Temp/opencode/r72gate/center/mirr_f2broker
```

镜像 = worktree 字节（mbuild 断言 `mirror == worktree`）；anchor 出现次数=1；BOM 未变；行尾统一。

### b. 靶支 + 同层次他支（官方尺 + mandated 尺）

清单：`dump/f2head.txt`（25 文件，LF 无 BOM = all16 + broker/finance/bar/jq_trans_module/flytools + 3 支 position + asset_mixin/trade_info_utils），跑前删旧 jsonl。

- 官方尺（h62）：`dump/f2head_landed.jsonl` vs `dump/f2head_cand.jsonl`，`h62 ab` →
  `TALLY SAME=23 IMPROVED=0 REGRESSION=0 MOVED=2 ERR=0 (unpaired lists=0)`
  - MOVED×2 = `broker.pyc`（24/24→24/24）、`trade_live_broker.pyc`（111/119→111/119），mismatch 集合均不变（`gained=[] lost=[]`），仅产物文本变化。
  - 其余 23 支 **sha 逐字节相同** → mandated 结果按构造不变（无需重跑）。
- mandated 尺（`pyc_verify single --source build_f2broker/…`）：

| 文件 | landed | 候选 | 失败单元 |
|---|---|---|---|
| `broker.pyc` | 35/42 failure | **38/38 success (100.00%)** | 7 → **0**，零新增 |
| `trade_live_broker.pyc` | 114/129 failure | **114/128 failure** | 15 → **14**，零新增（清掉的 1 个是 `***None: Extra bytecode`） |
| `asset_mixin.pyc`（ADR-1 关键支） | 20/21 failure | **20/21 failure（完全相同）** | 同一失败 `get_assets.<listcomp> Different bytecode (line 91 / offset 10)`，产物 sha 与 landed 逐字节相同 |

broker 被清零的 7 个单元（filecat.json 原样）：

```
***<module>.SimulationBroker.get_orders.<listcomp>: Failure: Different bytecode
***None: Failure: Extra bytecode            ×4
***<module>.SimulationBroker.get_open_orders.<listcomp>: Failure: Different control flow
***<module>.SimulationBroker.get_open_orders.<listcomp>: Failure: Different bytecode
```

（官方 `24/24` 维持；`get_trades` 两臂均 2 个 listcomp，本就无失败单元。）

### c. 金丝雀

`dump/f2canary.txt` → 两臂 `dump/f2canary_landed.jsonl` / `dump/f2canary_cand.jsonl`（均在**最终**镜像重建后跑）：

| 单元 | pin | landed | 候选 |
|---|---|---|---|
| quotation.pyc | `3eb76e512df9ab1e` | 3eb76e512df9ab1e 143/143 | **3eb76e512df9ab1e 143/143** |
| market_time.pyc | `af77224b34b203c4` | af77224b34b203c4 10/10 | **af77224b34b203c4 10/10** |
| IQCommon datetime_func | `e711b8ea86d49a15` | e711b8ea86d49a15 26/26 | **e711b8ea86d49a15 26/26** |
| IQData datetime_func | `9d09af09249da177` | 9d09af09249da177 25/25 | **9d09af09249da177 25/25** |

quotation 的热门 cf 单元 `change_his_to_forward` 未转差：143/143 维持，mandated 无需重跑。

### d. 电池（closeout69）

```
python -X utf8 closeout69.py battery landed f2broker   →  dump/f2battery.txt
repro pycs discovered: 82  (round63 batches + 11 pinned R62 witnesses)
candidate columns worse-than-landed on 0 repro(s)      (14.5s)
```

逐条 sha 对比：**same=81 / diff=1**，唯一差异 `round67_diag1/r67_join_after_noelse.pyc`（7/7→7/7、mism 相同、`d=+0`），差异内容 = 删掉两处**重复的** `return [x for x in r if x == c]`（即本病的同型 witness），属改善非回归。

### e. 严格尺（sstrict67）

```
python -X utf8 sstrict67.py build_landed dump/f2head.txt dump/f2strict_landed.json
python -X utf8 sstrict67.py build_f2broker dump/f2head.txt dump/f2strict_cand.json
```

两臂输出**逐行相同**：`STRICT TOTAL ok=1186 / functions=1243 / defects=57`，每文件 strict 计数与逐缺陷清单一致 → **零新增缺陷函数**（含 `asset_mixin 19/20`、`broker 29/29`、`trade_live_broker 109/123` 全部持平）。

---

## 4. ADR-1 事故记录（第一版 spec 已拒收）

第一版 spec 为**无条件** `prev_end = len(instrs)`（+13 行）。ADR-1 自查命中他支回归：

- `IQEngine/data/asset_mixin.pyc` 官方 **16/16 → 15/16**，mismatch `get_assets`（orig 89 / decomp 83，jump_diffs=1）。
- 差异本体（两臂 build 产物 diff）：

```
             elif isinstance(asset_or_symbols, list):
-            return [i for i in [self.get_assets(sid) for sid in asset_or_symbols] if i]
+            return [i for i in asset_or_symbols if i]
+            return [self.get_assets(sid) for sid in asset_or_symbols]
```

  即无条件推进记账绕过了下一轮 `pre_comp_instrs` 终止符守卫（L273-278），把**嵌套**推导式拆成两条 `Return`，原「整体 `return None` → 由 `expr_reconstructor` 发射嵌套 `ast.Return(ListComp(iter=ListComp))`」路径失效。

- 处置：按 ADR-1（任何他支回归即整件拒收）拒收该版，判据收紧为「本块 `comp_indices` 尾项」（`if _comp_loop_idx == len(comp_indices) - 1`），非尾项保持旧记账、继续走守卫。重跑 a–e：
  - `asset_mixin.pyc` 恢复 **16/16**，且 sha 与 landed **逐字节相同**（`9aa80c3312568114`）；
  - 全部 ADR-1 读数如 §3。

---

## 5. 冲突与声明

1. **与 diag1 的潜在分歧**：写此 FACTS 时工作区内未见 diag1 的任何产物（`fix2/` 下只有本候选的 specs/dump/synth）。若 diag1 对 `comprehension_generator.py` 给出不同病因，须按 BRIEF §4 在此标注分歧并保留双方实证；本候选的实证是「同型 `Return` 重复发射」，最小复现 `synth/chain3_lc.pyc`（3 → 0 dup），反例 `chain_mixed/chain3_plain`（本就无 dup）。
2. **与 fix1 的同文件冲突**：本轮 fix1 也改 `core/cfg/comprehension_generator.py`。中心合并须按「一 spec 一文件」把两份 edits 合到同一份 spec 的 `edits` 数组（或顺序应用）；`mbuild72` 对同文件第二份 spec 直接 `assert 'merge them first'`。两 spec 的锚点不重叠（本 spec 锚在 L520 的 `RETURN_VALUE/RETURN_CONST` 分支）。
3. **仪器 ROOT 说明**：`mbuild72/h62/closeout69/sstrict67` 内部 ROOT/GATE 指向 `center`（非 fix2 目录），故镜像/产物落在 `center/mirr_f2broker`、`center/build_landed|f2broker`；臂名 `f2broker` 为唯一名，不与 center/fix1 碰撞。
4. **未触碰**：repo 任何文件、`pyc_index.json`、site-packages 产物；未运行 402 全量扫描。

---

## 6. 原始输出（均在 `dump/`）

| 用途 | 文件 |
|---|---|
| 25 文件清单 | `f2head.txt`（LF 无 BOM） |
| b 官方尺 landed / 候选 | `f2head_landed.jsonl` / `f2head_cand.jsonl` |
| b mandated 计数 | 本文 §3 表（命令输出为 stdout，broker/trade_live_broker 均已复跑） |
| c 金丝雀 | `f2canary.txt`、`f2canary_landed.jsonl`、`f2canary_cand.jsonl` |
| d 电池 | `f2battery.txt`（两臂对照表），jsonl `center/dump/repro65_landed.jsonl`、`repro65_f2broker.jsonl` |
| e 严格尺 | `f2strict_landed.json`、`f2strict_cand.json` |
| 根因诊断 | `broker_orig_dis.txt`、`ladder.txt`、`line_trace.txt`、`dup_trace.txt` |
| 最小复现 | `synth/*.py(c)`、`dump/synth_repro.txt` |
| 候选产物样例 | `dump/broker_cand.py` |
