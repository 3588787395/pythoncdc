# R71 · 中心复测 · c1（fix1 `R71-exception_exit.json`）五连独立复测结论

- 中心臂 `c1` = 镜像 `center/mirr_c1` = repo + 1 个 edit（`core/cfg/region_ast_generator.py::_if_generate_else_branch`，+62 行）
- spec 复制件：`center/specs/c1_exception_exit.json`（python 侧按字节复制，LF/UTF-8 无 BOM，4969 B；与 fix1 源 spec 逐字节同源）
- repo 只读：`git status --porcelain` 过滤 `??` 后 **Count=0**（无任何已跟踪文件被改动）；未 commit / push
- 本目录全部读数由 python 侧写文件（UTF-8/LF），存于 `center/dump/`
- 每条命令 <300 s（最慢一条 36.9 s）

---

## 判据总表

| # | 判据 | 读数 | 结论 |
|---|---|---|---|
| a | 锚点/镜像自检 | `edits=1 lines=+62 bytes 3199517→3204133 BOM=True`；landproof 33 core files same=32 **diff=1**（仅 `region_ast_generator.py`） | **PASS** |
| b | 官方尺 56 支（`h62` bytecode_diff） | `SAME=47 IMPROVED=0 REGRESSION=0 MOVED=9 ERR=0 unpaired=0`；fully matched a=48 b=48 | **PASS**（REGRESSION=0） |
| c | 金丝雀 4 支 pinned sha | `SAME=4 REGRESSION=0`；4/4 pinned 全中；quotation `143/143` | **PASS** |
| d | mandated 尺（pylingual `compare_pyc`，全部 9 个 sha 变化文件） | 失败单元 landed **26 → c1 19（Δ=−7）**，**新增 failure = 0**，清零 7 个 | **PASS** |
| e | 电池（`closeout69 battery landed c1`，82 repro） | `candidate columns worse-than-landed on 0 repro(s)`，逐格全等 | **PASS** |
| f | 严格尺（`sstrict67`，cf1+b+div48 三份靶） | cf1 `772/792/20`、b `530/532/2`、div48 `1776/1819/43`，**新增缺陷 0**（三份均与我的 landed 对照逐项相等） | **PASS** |
| g | 合成咬合（`exc_A`/`exc_P`） | c1：`exc_A 5/5 success`、`exc_P 4/5 failure`；landed 对照：`exc_A 4/5 failure` | **PASS** |

---

## a. 锚点 / 镜像（`dump/c1_build.txt`）

```
python -X utf8 mbuild71.py c1 specs/c1_exception_exit.json
  patched core/cfg/region_ast_generator.py   edits=1 lines=+62 bytes 3199517 -> 3204133 BOM=True
mirror ready: D:/Temp/opencode/r71gate/center/mirr_c1  from 1 spec(s) ['c1_exception_exit.json']
```

- mbuild 断言全过：anchor 在（LF 归一后）恰 1 次、BOM 保持、行尾统一（该文件 CRLF=51430 保持）、净插入行数 = spec 声明 +62。
- `closeout69.py landproof mirr_c1` → `33 core files, same=32 diff=1`，唯一 DIFF = `core/cfg/region_ast_generator.py`（mirror `38350ce4662e` / repo `240ecbaea36e`）。
- 字节数 3199517→3204133 与 fix1 自称**完全一致**。
- 注：镜像/仓库该文件各含 1 处 `U+FFFD`（repo 原文注释里已有的坏字符，位置随 +62 行平移），**非本次补丁引入**。

## b. 官方尺 56 支（`dump/c1_56.jsonl`、`dump/c1_ab56.txt`、`dump/c1_cadelta.txt`）

```
python -X utf8 h62.py run --arm=c1 --list=all56.txt --out=dump/c1_56.jsonl
python -X utf8 h62.py ab  --a=dump/landed56_r71.jsonl --b=dump/c1_56.jsonl
→ TALLY SAME=47 IMPROVED=0 REGRESSION=0 MOVED=9 ERR=0  (unpaired lists=0)
  files fully matched: a=48 b=48
```

**判据 REGRESSION=0 → PASS。**

基线可信度（我自己重测，不采信既有 dump）：

- landed 臂全量重跑 `dump/landed56_re.jsonl`（36.9 s）：56/56 记录、**sha 与 `landed56_r71.jsonl` 全等（diff=0）**；
- c1 臂对 9 支变化文件重跑 `dump/c1_nine_re.jsonl`：**自稳定**（两次 sha 全同）；
- landed 对这 9 支重跑 `dump/landed_nine_re.jsonl`：与基线全同。⇒ 变化是补丁效应，不是哈希/环境噪声。

聚合差异量（官方尺 `mism` 口径，全部 56 支）：

| | defects | Σ\|Δ\| | Σjumpdiff | Σtruediff |
|---|---|---|---|---|
| landed | 29 | 186 | 130 | 4990 |
| c1 | 29 | 186 | 130 | 4990 |

⇒ **Σ\|Δ\| 不升、零新增 mismatch**；MOVED 的 9 支 `gained=[] lost=[]`（mismatch 集合与 matched/total 逐项不变）。

9 支 sha 变化（`dump/nine.txt`），全部为「删掉一个源码不存在的 `else: return None`」：

| 文件 | landed sha → c1 sha | matched/total |
|---|---|---|
| IQCommon/exception | `32ef2c9998e7aa62 → 27565b876decb526` | 32/32 → 32/32 |
| IQCommon/util/trade_info_utils | `963c91bfbe3b0fad → 9d15bb7d97681cfa` | 40/40 → 40/40 |
| IQData/utils/exception | `8804bb9f572dcf2c → c93c498e85bf915b` | 29/29 → 29/29 |
| IQEngine/…/plugin_fly_data/strategy/strategy | `d5fcbdd3b09e1139 → 7ac4fbb59ff4a1e8` | 24/24 → 24/24 |
| IQEngine/…/plugin_system_accounts/__init__ | `107d632fa05049f6 → 27c4ca3e12c9b33a` | 6/6 → 6/6 |
| …/benchmark_account | `bccc2056f896440f → f752c84fca326a9a` | 20/20 → 20/20 |
| …/stock_account | `8706978e84ed03c6 → e8a153b76b4971a0` | 25/25 → 25/25 |
| IQEngine/utils/exception | `bc7f8921f2245316 → d60d1cdc9b234708` | 29/29 → 29/29 |
| fly/data/quote | `31864ff09b7476e5 → 779fd8767dfc0f36` | 72/81 → 72/81 |

## c. 金丝雀（`dump/c1_canary.jsonl`、`dump/c1_abcanary.txt`）

```
TALLY SAME=4 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0   files fully matched: a=4 b=4
```

| 支 | pinned(R70) | landed | **c1** | 官方读数 |
|---|---|---|---|---|
| fly/common/market_time | `af77224b34b203c4` | 同 | **同 ✅** | 10/10 |
| IQCommon/util/datetime_func | `e711b8ea86d49a15` | 同 | **同 ✅** | 26/26 |
| IQData/utils/datetime_func | `9d09af09249da177` | 同 | **同 ✅** | 25/25 |
| fly/data/quotation | `4d41187e356544e0` | 同 | **同 ✅** | **143/143** |

4/4 pinned 精确命中，quotation 读数 143/143（与金丝雀 pinned 口径一致）。

## d. mandated 尺（`dump/c1_pv.txt`、`dump/c1_pv_summary.txt`）

对官方尺 ab 里**全部 9 个 sha 变化文件**逐支跑 `scripts/pyc_verify.py single <pyc> --source <center>/build_*/<产物>.py`，landed 侧用我自己重跑的 `build_landed/` 产物对照：

| 文件 | landed | c1 | 变化 |
|---|---|---|---|
| IQCommon/exception | 33/34（`ModifyExceptionFromType.__exit__` cf） | **34/34 success** | −1 |
| IQData/utils/exception | 30/31（`ExceptionIdentify.__exit__`） | **31/31 success** | −1 |
| IQEngine/utils/exception | 30/31（`ModifyExceptionFromType.__exit__`） | **31/31 success** | −1 |
| accounts/\_\_init\_\_ | 5/6（`AccountPlugin.setup`） | **6/6 success** | −1 |
| benchmark_account | 19/20（`_process_mergered`） | **20/20 success** | −1 |
| stock_account | 24/25（`_process_mergered`） | **25/25 success** | −1 |
| plugin_fly_data/strategy/strategy | 25/27（`__init__` + `tick_worker_thread`） | **26/27**（只剩 `tick_worker_thread`） | −1 |
| IQCommon/util/trade_info_utils | 36/41（5 失败） | 36/41（**同一 5 个**） | 0 |
| fly/data/quote | 79/92（13 失败） | 79/92（**同一 13 个**） | 0 |

- **失败单元 26 → 19（Δ = −7）**
- **新增 failure = 0**（逐文件集合差 `NEW=0`）
- 清零 7 个，比 fix1 自称的 6 个多 1 个（`Strategy.__init__`，该文件不在 fix1 靶清单内）

被改动但状态不变的两处也已定位：`kill_trade_process`（trade_info_utils，landed 与 c1 同为 cf 失败）、`check_industry_code`（quote，两侧同为 cf 失败）——删掉的是多余的 `else: return None`，该单元本来就在失败集合里，**没有由绿转红**。

## e. 电池（`dump/c1_battery.txt`）

```
python -X utf8 closeout69.py battery landed c1
→ repro pycs discovered: 82 (round63 batches + 11 pinned R62 witnesses)
→ candidate columns worse-than-landed on 0 repro(s)
```

82 行逐格 landed 与 c1 完全相同（含既有的 `d=-75/-43/-16` 等坏样本，两侧一致）→ **worse-than-landed = 0**。

## f. 严格尺（`dump/strict_c1_*.json`、`dump/strict_*_diff.txt`、`dump/strict_c1_vs_fix1.txt`）

靶清单：`center/cf1_targets.txt`、`center/b_targets.txt`（自 `fix1/` 复制，31 + 10 支），另加 `div48.txt`（48 支，覆盖 3 支额外 sha 变化文件）做加宽对照；landed 对照由**我自己**用 `build_landed/` 现跑。

| 靶 | landed（我自测） | c1 | 新增缺陷 | 清除缺陷 |
|---|---|---|---|---|
| cf1（31） | 772/792/20 | **772/792/20** | **0** | 0 |
| b（10） | 530/532/2 | **530/532/2** | **0** | 0 |
| div48（48） | 1776/1819/43 | **1776/1819/43** | **0** | 0 |

- 逐文件 defect-set diff（去 product 路径字段）：cf1/b/div48 **全部 files_with_diff=0**；
- 我的 landed 对照与既有基线 `dump/strict_landed_r71.json` **differing files=0**（基线可复现）；
- 我的 c1 读数与 fix1 的 `strict_r71b_cf1.json` / `strict_r71b_b.json` **differing files=0**；
- 预存的 `target_diff`（local_finance / calexrights×2 / executor / strategy_universe / matcher / logger / quotation×2 等）**逐项未变，无新增 target_diff**；`handlers._target` 仍 `orig=192 decomp=190`（=landed，未恶化）。

## g. 合成咬合（`dump/c1_synth.txt`、`dump/synth/`）

`fix1/synth/exc_A.py`、`exc_P.py` 用 `py_compile` 编到 `center/dump/synth/`（A 1367 B / P 1354 B；两者 `__exit__` 均 37 insts / 222 B，仅终结块跳转目标 214↔218 互换），在 c1 与 landed 两臂各反编译一次再 `pyc_verify single`：

| 源形状 | landed | **c1** |
|---|---|---|
| `exc_A.py`（无 else） | `4/5 failure`（伪 `else: return None`，产物 17 行 sha `20f4ca814b1d46bb`） | **`5/5 success`**（15 行 sha `6a340855ad48a5d0`） |
| `exc_P.py`（真 `else: return None`） | `4/5 failure`，产物 sha `c576cbbf0769f20a` | **`4/5 failure`，产物 sha `c576cbbf0769f20a`（与 landed 逐字节相同）** |

- `exc_A` 在 c1 下 **cfg 等价为真（failure 消失）** —— 咬合「正确形状」；
- `exc_P` 行为与 fix1 记录一致（仍 `Different control flow`），且 **c1 产物与 landed 逐字节相同 ⇒ 真 else 没有被误删**（判据② 的地址序排除生效）；
- landed 臂的 `exc_A` 复现了 bug 本体（无 else 源 → 多发一个 else → 4/5）。

---

## 与 fix1 自称读数的差异

| 项 | fix1 `FACTS.md` | 我的独立读数 | 差异性质 |
|---|---|---|---|
| 锚点/字节 | `edits=1 lines=+62 bytes 3199517→3204133 BOM=True` | 同 | 一致 |
| 官方尺 sha 变化文件数 | cf1 MOVED=6 + b MOVED=3 → **去重 6 支** | **9 支**（同样 6 支 + `trade_info_utils`、`plugin_fly_data/strategy/strategy`、`fly/data/quote`） | **fix1 靶清单未覆盖这 3 支**（其 `cf1_targets.txt`/`b_targets.txt` 不含它们），故其「零新增」结论范围小于补丁实际作用面 |
| 清零单元 | 6 个 | **7 个**（多 `Strategy.__init__`） | 同源差异：多测出来的第 3 支带来的**额外改善** |
| REGRESSION / 新增 failure / 新增 strict 缺陷 / battery worse | 0 / 0 / 0 / 0 | **0 / 0 / 0 / 0** | 一致 |
| 金丝雀 pinned + quotation 143/143 | 全中 | 全中 | 一致 |
| 严格尺 cf1 `772/792/20`、b `530/532/2` | 同 | 同（逐 defect-set 相等） | 一致 |
| 合成 `exc_A`/`exc_P` | True / False（60↔64 互换） | c1：success / failure；landed 对照 exc_A=failure | 一致（口径不同：我比的是「该 pyc 自身 vs 该臂产物」） |
| repo HEAD | 称 `b21c5c61` | 实测 `a31d3f79`（已跟踪文件 0 修改，工作树干净） | 记录差异；因我的 landed 全量重跑与既有基线 56/56 全等、严格尺也与基线全等，**不影响任何读数** |

**没有任何一项 fix1 自称的读数被我推翻**；差异只在**覆盖面**：fix1 的靶清单窄于补丁真实作用面（3 支未测），我加宽后仍为 0 回归，并多出 1 个被修复单元。

## ADR-1 判定

- **族性质**：过冲族（反编译多发射了一个源码里不存在的 `else` 臂 → 相邻终结块发射次序对调 → `Different control flow`）。
- **Σ\|Δ\| 净减**：官方尺 Σ\|Δ\| 186→186（不升）、mism 29→29（零新增）；mandated 失败单元 26→**19**（净减 7）；严格尺 defect 集合 3 份靶均 0 变化。**满足「净减且不升」**。
- **不得以少发射换**（本件最关键的反作弊面）：
  1. `exc_A`（源码本无 else）在 c1 下 5/5 通过，且其编译字节码与真实 pyc 同形（37 insts/222B）⇒ 去掉的正是「重编译会自然再生」的隐式收尾；
  2. `exc_P`（源码有真 else）在 c1 下产物与 landed **逐字节相同** ⇒ 没有吞掉真分支；
  3. 9 支被改文件里，**没有任何一个单元由绿转红**（trade_info_utils 5→5、quote 13→13、其余 failure→success）。
  ⇒ 不是靠「少发指令换通过」。
- **位移族四项**：本件非位移族，但四项均未恶化——hunk 无新增（严格尺 target_diff 集合 0 变化）、无 first_diff 回移面、Σ\|Δ\| 不升、严格尺无新增 target_diff。
- **任何他支回归即整件拒收**：官方尺 REGRESSION=0（56 支）、金丝雀 0（4 支 pinned 全中）、mandated 新增 failure 0、严格尺新增缺陷 0、电池 worse-than-landed 0（82 repro）。**无他支回归。**

### 结论：**采纳（ADOPT）**

附带（不构成拒收理由）：建议把补丁实际作用面由 6 支扩记为 **9 支 / 7 个清零单元**，并将 `trade_info_utils`、`plugin_fly_data/strategy/strategy`、`fly/data/quote` 三支补入归档靶清单——它们是 fix1 自测覆盖之外、我这次才量到的真实作用点。

---

## 复现（全部在 `center/`，每条 <300 s）

```bat
python -X utf8 mbuild71.py c1 specs/c1_exception_exit.json
python -X utf8 h62.py run --arm=c1 --list=all56.txt  --out=dump/c1_56.jsonl
python -X utf8 h62.py ab  --a=dump/landed56_r71.jsonl --b=dump/c1_56.jsonl
python -X utf8 h62.py run --arm=c1 --list=canary.txt --out=dump/c1_canary.jsonl
python -X utf8 h62.py ab  --a=dump/landed_canary_r71.jsonl --b=dump/c1_canary.jsonl
python -X utf8 pv_run71.py dump/nine.txt build_c1    dump/c1_pv.txt
python -X utf8 pv_run71.py dump/nine.txt build_landed dump/c1_pv.txt --append
python -X utf8 closeout69.py battery landed c1
python -X utf8 sstrict67.py build_c1     cf1_targets.txt dump/strict_c1_cf1.json
python -X utf8 sstrict67.py build_c1     b_targets.txt   dump/strict_c1_b.json
python -X utf8 sstrict67.py build_landed cf1_targets.txt dump/strict_landed_cf1_c.json
python -X utf8 sstrict67.py build_landed b_targets.txt   dump/strict_landed_b_c.json
python -X utf8 sstrict67.py build_c1     div48.txt       dump/strict_c1_div48.json
python -X utf8 sstrict67.py build_landed div48.txt       dump/strict_landed_div48_c.json
python -X utf8 synth_c1.py c1     dump/synth/exc_A.pyc dump/synth/c1_exc_A.py
python -X utf8 synth_c1.py c1     dump/synth/exc_P.pyc dump/synth/c1_exc_P.py
python -X utf8 synth_c1.py landed dump/synth/exc_A.pyc dump/synth/landed_exc_A.py
python -X utf8 synth_c1.py landed dump/synth/exc_P.pyc dump/synth/landed_exc_P.py
```

## dump/ 索引

`c1_build.txt`、`c1_56.jsonl`、`c1_ab56.txt`、`c1_cadelta.txt`、`nine.txt`、`c1_nine_re.jsonl`、`landed_nine_re.jsonl`、`landed56_re.jsonl`、`c1_canary.jsonl`、`c1_abcanary.txt`、`c1_pv.txt`、`c1_pv_summary.txt`、`c1_battery.txt`、`strict_c1_cf1.json`、`strict_c1_b.json`、`strict_landed_cf1_c.json`、`strict_landed_b_c.json`、`strict_c1_diff.txt`、`strict_c1_div48.json`、`strict_landed_div48_c.json`、`strict_div48_diff.txt`、`strict_c1_vs_fix1.txt`、`c1_synth.txt`、`synth/`、`c1_verdict.md`
