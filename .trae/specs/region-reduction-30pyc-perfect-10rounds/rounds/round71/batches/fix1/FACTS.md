# R71 · fix1 · FACTS

候选（唯一，已过 a–e）：`specs/R71-exception_exit.json`
→ 臂 `r71b`（`mirr_r71b/`、`build_r71b/`），补丁落点
`core/cfg/region_ast_generator.py::_if_generate_else_branch`（repo L15503 起，
anchor = L15549–15550 的 `if region.else_blocks:` + `[R115 fix]` 首行）。
repo 未被修改（本目录只写镜像/产物/dump）。

---

## 0. 一屏结论

| 项 | 读数 |
|---|---|
| 族 | A：`__exit__` / `_process_mergered` / `setup` 的「隐式收尾被当成 else 臂」（cf=1，Different control flow） |
| 修掉的单元 | 6 个（cf=1 组里 31 支的 6 支）：`ModifyExceptionFromType.__exit__`×2、`ExceptionIdentify.__exit__`、`AccountPlugin.setup`、`BenchmarkAccount._process_mergered`、`StockAccount._process_mergered` |
| 零新增 | cf1/b 两份 `pv71` diff：只有 6 行 failure 消失，无任何新增 failure；`sstrict67` 缺陷集合 diff = 0（cf1 772/792 defects=20、b 530/532 defects=2，与 landed 逐项相等） |
| 金丝雀 | 4 支 pinned sha 全部 = R70（见 §6c）；quotation `143/143`、sha `4d41187e356544e0` 未动 |
| 电池 | `closeout69.py battery landed r71b` → `candidate columns worse-than-landed on 0 repro(s)` |
| 族 B（position_model genexpr） | 未开工：源形状未命中，见 §8 |

---

## 1. 边界 / 环境

- 工作区 `D:/Temp/opencode/r71gate/fix1`；repo `F:/Downloads/pythoncdc-main`，HEAD=R70 `b21c5c61`；`h62 --arm=landed` = repo 字节。
- 判据只有 `pylingual/equivalence_check.py::compare_pyc`（经 `scripts/pyc_verify.py single`）。
- 本地 Python 3.11.7（magic 3495）。repo 目标文件是 CRLF+BOM，anchor 一律按 LF 归一后比对（`mbuild71.py` 自带）。
- 本目录所有文本输出均由 python 侧写文件（避免 PowerShell 重定向 UTF-16）。

## 2. 输入聚类（`filecat.json`，56 支）

- **B 组** = cf=1 长尾 31 支 + cf=0 的 Different/Extra bytecode 6 支（`fc_cluster.py` 输出留档）。
- 按失败单元名聚类：`__exit__`×3、`_process_mergered`×2、`setup`×1 是「if 链 + 终结臂」同构簇 → **族 A**（本次交付）；
  `<genexpr>`×12（future/live/option position 三支 4/4/2 同构）→ **族 B**（未完成）；
  其余 `change_his_to_forward`×4、`get_price`/`get_kline_*` 等单发散点本轮不动。
- 用户线索「多数是嵌套 try-except」**实测否定**：族 A 的 6 支靶单元里没有任何 try/except（`dis` 逐条核对），异常只出现在 `__exit__` 的语义上；exception.pyc 的 try 结构在别的单元。

## 3. 族 A：根因（钉到行）

1. **现象**：`pyc_verify.py single` 报 `<module>.ModifyExceptionFromType.__exit__: Different control flow`；
   `failunits.dump` 显示指令数/块数相等、`is_control_flow_equivalent=False`，差异是两个相邻终结块的跳转目标互换。
2. **机制（CPython 侧事实，`dump/epilogue_evidence.txt`）**：原始 pyc 的 `__exit__` 尾部有 3 个相邻
   `LOAD_CONST None; RETURN_VALUE`（raw offset 210/214/218，函数 37 insts / co_code 222B）；
   用**完全没有 else** 的源码（`synth/exc_A.py`）重新编译，得到 **逐指令、逐 offset 完全相同**的 37 insts / 222B。
   ⇒ 这 3 个 return 里有 2 个是 CPython 给各跳转目标复制的**隐式收尾（implicit epilogue）**，源码里并不存在。
3. **反编译侧 bug**：region 把「条件跳转目标 = 隐式收尾块」认成 `IfRegion.else_blocks`，发射成
   `else: return None`，于是**相邻两个终结块的发射次序对调**（原序 `[... then 臂][收尾214][收尾218]`
   变成 `[... then 臂][else=218 提前][214]`），pylingual 按址节点映射的出边集合随即不等。
   合成咬合（`dump/synth_exc.txt`）：
   - `synth/exc_A.py`（无 else）vs 原 pyc → `inst 34/34 blocks 8/8 cfg_equiv=True first DIFF=None`
   - `synth/exc_P.py`（显式 `else: return None`）vs 原 pyc → `cfg_equiv=False`，
     DIFF 在 idx1/idx19：`argval=60 ↔ 64`（两个终结块跳转目标互换）—— 与真实失败同形。
4. **触发区域（探针 `patch_probe.py` → `probe.log`，15 个「纯 else + 无 merge」候选区）**：

   | 站点 | order(②) | then 臂区域内自洽(③) | 判定 |
   |---|---|---|---|
   | exception `ModifyExceptionFromType.__exit__` ×3 文件 | True | OWNED | 真命中 |
   | exception `ExceptionIdentify.__exit__`（IQData） | True | OWNED | 真命中 |
   | accounts `AccountPlugin.setup` | True | OWNED | 真命中 |
   | benchmark `_process_mergered`（region#2） | True | OWNED | 真命中 |
   | stock `_process_mergered`（region#4） | True | OWNED | 真命中 |
   | handlers `TWHThreadController._target` ×2 region | True | **UNOWNED:[658,1008]** | 误命中（反例） |
   | exception `<module>` ×3、benchmark region#1、stock ×3 | False | OWNED | order 已排除 |

   即：`order=True` 8 区 = 6 真 + 2 假；**纯区域形状在 exception 与 handlers 之间同构**，
   可用判别式只剩 ③（then 臂是否能只经 `region.blocks` 内后继边全部到达）。
   handlers 的终止块 658/1008 只能经**区域外**回边（循环体 630/994）到达 → then 臂不是单一源码子树。

## 4. 候选 spec 演进（三稿）

| 稿 | 判据 | 结果 |
|---|---|---|
| v1（`specs/_v1_rejected_R71-exception_exit.json`，+37 行） | 只有 ①纯 else + ②无 merge + order | 6 单元转绿，但 handlers 被误命中两次（probe.log：entry=458/else=[1016]、entry=412/else=[1012]）：`dump/handlers_v1_v2.txt` 记录 `landed inst 191/189 blocks 43/42 → r71a inst 191/187 blocks 43/41`，strict `seq_len` decomp `190→188`（landed=190，Δ 由 −2 恶化到 −4）→ **ADR-1 幅度回归，整件拒收** |
| v2（`specs/_v2_rejected_...`，+62 行） | v1 + ③then 臂区域内自洽 BFS | handlers 回落 landed（`seq_len` 190、产物 sha 与 landed 逐字节相同），6 单元仍全绿；仅注释/一行不可达 `return None` 不美观 |
| **final（`specs/R71-exception_exit.json`，+62 行）** | 与 v2 判据完全相同 | 注释改写（站点名标注“不参与判据”）、删掉那行不可达 `return None`；镜像 diff = 仅注释 3 处 + 1 行删除，产物 sha/记录与 v2 **0 差异**（`cmp_prevspec.py`：cf1 31/31、b 10/10 全等） |

判据写进 repl 的三要素注释（无函数名/文件名/偏移常量/阈值/名字白名单/新增 self 状态/跨层
`region.entry in r.blocks` 型模式）：

- ① else 臂每块是纯 `LOAD_CONST None; RETURN` 终结臂，且 `region.merge_block is None`；
- ② `min(else.start_offset) < max(then.start_offset)`（真 else 恒在全部 then 之后发射）；
- ③ 从条件块出发只沿 `region.blocks` 内 `successors` BFS，可达全部 `then_blocks`。
命中后的动作：整臂不发射，但登记 `self.generated_blocks` / `self.generated_offsets`（父序列按唯一归属
不再重复发射），隐式收尾由重编译自然再生 → 指令数/块数不变；AST 映射 = `ast.If.orelse` 置空。

## 5. a–e 验证读数（臂 `r71b`，final spec）

**a. 锚点自检**
```
python -X utf8 mbuild71.py r71b specs\R71-exception_exit.json
→ patched core/cfg/region_ast_generator.py  edits=1 lines=+62 bytes 3199517 -> 3204133 BOM=True
```
（`mk_spec_final.py` 自检：anchor 在 repo LF 归一后恰 1 次、repl 无连续重复 `return None`。）

**b. 靶支读数**
```
python -X utf8 h62.py run --arm=r71b --list=cf1_targets.txt --out=dump/cf1_r71b.jsonl
python -X utf8 h62.py run --arm=r71b --list=b_targets.txt   --out=dump/b_r71b.jsonl
python -X utf8 h62.py ab --a=dump/cf1_landed.jsonl --b=dump/cf1_r71b.jsonl
→ TALLY SAME=25 IMPROVED=0 REGRESSION=0 MOVED=6 ERR=0  (unpaired lists=0)  files fully matched a=29 b=29
python -X utf8 h62.py ab --a=dump/b_landed.jsonl --b=dump/b_r71b.jsonl
→ TALLY SAME=7  IMPROVED=0 REGRESSION=0 MOVED=3 ERR=0  (unpaired lists=0)  files fully matched a=10 b=10
```
MOVED 的 6/3 支正是被修的族；`gained/lost` 全空。

mandated 尺（`dump/pv71_cf1_r71b.txt` vs `dump/pv71_cf1_landed.txt`，仅列非路径行）：
```
-  ***<module>.ModifyExceptionFromType.__exit__: Failure: Different control flow     (IQCommon)
-  ***<module>.ExceptionIdentify.__exit__: Failure: Different control flow           (IQData)
-  ***<module>.AccountPlugin.setup: Failure: Different control flow
-  ***<module>.BenchmarkAccount._process_mergered: Failure: Different control flow
-  ***<module>.StockAccount._process_mergered: Failure: Different control flow
-  ***<module>.ModifyExceptionFromType.__exit__: Failure: Different control flow     (IQEngine)
+ [single] status=success units=34/34 / 31/31 / 6/6 / 20/20 / 25/25 / 31/31
```
`+` 行只有这 6 条（failure→success），**零新增 failure**；`dump/pv71_r71b.txt`（b 组 10 支）
同样只有 exception×3 三处 failure 消失，`handlers` 仍 29/30、`quotation` 仍 151/153（既有 2 个 cf 单元），
其余逐行等于 landed。

**c. 金丝雀（`dump/canary_r71b.txt`，sha = `sha256(去 CRLF 后的产物文本)[:16]`，与 h62 口径一致）**

| 支 | pinned(R70) | landed | r71b |
|---|---|---|---|
| `fly/common/market_time.pyc` | `af77224b34b203c4` | 同 | 同 ✅ |
| `IQCommon/util/datetime_func.pyc` | `e711b8ea86d49a15` | 同 | 同 ✅ |
| `IQData/utils/datetime_func.pyc` | `9d09af09249da177` | 同 | 同 ✅ |
| `fly/data/quotation.pyc` | `4d41187e356544e0` | 同 | 同 ✅（h62 官方读数 `143/143`） |
| position_model 三支（future/live/option） | – | `b227642f94b168fd` / `fda230b7bd1b8119` / `30e2c51401df04ac` | 逐支相同 ✅ |

**d. 电池**
```
python -X utf8 closeout69.py battery landed r71b   → dump/battery_r71b.txt
candidate columns worse-than-landed on 0 repro(s)
```

**e. 严格尺**
```
python -X utf8 sstrict67.py build_r71b cf1_targets.txt dump/strict_r71b_cf1.json
→ STRICT TOTAL ok=772 / functions=792 / defects=20      （landed 同为 772/792/20）
python -X utf8 sstrict67.py build_r71b b_targets.txt   dump/strict_r71b_b.json
→ STRICT TOTAL ok=530 / functions=532 / defects=2       （landed 同为 530/532/2）
```
按支逐项比对（去掉 product 路径字段）：**defect-set diff = 0**（cf1 31/31、b 10/10 全等）；
`handlers._target` 的 `seq_len` 保持 landed 的 `orig=192 decomp=190`（v1 是 188）。

ADR-1：本族不是缺失/过冲族——被修单元只是 failure→success，其他单元计数逐项不变；
`Σ|Δ|`、hunk、first_diff 均无恶化面（电池 0 回归、严格尺 0 新增）。

## 6. 合成最小复现（`synth/` + `dump/synth_exc.txt`）

- `synth/exc_A.py` = 无 else 源码形状 → `cfg_equiv=True`（咬合“正确形状”）；
- `synth/exc_P.py` = 显式 `else: return None` → `cfg_equiv=False` 且跳转目标 60↔64 互换（咬合“错误形状”，即 landed 产物行为）；
- `order_A/C/P.py` = 用于验证判据②（else 臂地址序）的形状样本。
- `dump/epilogue_evidence.txt` = 原始 pyc 与「无 else 重编译」的逐指令对照（37 insts / 222B 全同）。

## 7. 候选 / 拒绝清单

- **交付**：`specs/R71-exception_exit.json`（final，a–e 全绿，臂 r71b）。
- **拒绝**：v1（+37 行，判据缺 ③ → handlers `seq_len` 190→188 幅度回归）；
  v2（判据与 final 相同，仅注释措辞 + 一行不可达 `return None`；其产物与 final 逐字节相同，留档可比对）。
- **未动**：cf=1 其余 25 支（local_finance / cgroup_utils / email_utils / api_base / entry / calexrights×2 /
  executor / slippage / strategy_universe / trading_dates / history_api / matcher / broker / profiler /
  quote_handler / fly.logger / flyAccount / realtime_event_source / risk_calc function / trade function …）——
  失败单元各不相同，不构成同构族。

## 8. 未完成：族 B（position_model `<genexpr>`，cf=0 Different bytecode 4/4/2）

- 三支同目录同族（future 79/83、live 71/75、option 65/67），失败点都是
  `<genexpr>` 的 line 215/221/236/239（offset 20）`Different bytecode`，大概率一条判据清三支。
- 障碍：`sweep_genexpr.py` 的 AST 枚举没有命中目标跳转形态——
  comprehension 双 filter/`and`→(B,B)、elt 三元单 filter→(B,F)、genfunc 嵌套 if→(F,F)、
  `if not X: continue`→(F,IF_TRUE)，均与目标 `(F, ?)` 不符；
  下一步应改用「原始 genexpr 的 `dis` 目标序列 → 反查源形状」而不是正向枚举。

## 9. 复现命令（都在本目录、每条 <300s）

```bat
python -X utf8 mk_spec_final.py                 # 生成 spec + anchor 自检
python -X utf8 mbuild71.py r71b specs\R71-exception_exit.json
del dump\cf1_r71b.jsonl dump\b_r71b.jsonl
python -X utf8 h62.py run --arm=r71b --list=cf1_targets.txt --out=dump/cf1_r71b.jsonl
python -X utf8 h62.py run --arm=r71b --list=b_targets.txt   --out=dump/b_r71b.jsonl
python -X utf8 h62.py ab --a=dump/cf1_landed.jsonl --b=dump/cf1_r71b.jsonl
python -X utf8 h62.py ab --a=dump/b_landed.jsonl    --b=dump/b_r71b.jsonl
python -X utf8 pv71.py r71b --save --list=cf1_targets.txt --tag=cf1_r71b
python -X utf8 pv71.py r71b --save
python -X utf8 sstrict67.py build_r71b cf1_targets.txt dump/strict_r71b_cf1.json
python -X utf8 sstrict67.py build_r71b b_targets.txt   dump/strict_r71b_b.json
python -X utf8 run_canary.py                     # -> dump/canary_r71b.txt
python -X utf8 run_battery.py                    # -> dump/battery_r71b.txt
python -X utf8 run_synth.py                      # -> dump/synth_exc.txt
python -X utf8 epilogue_evidence.py              # -> dump/epilogue_evidence.txt
python -X utf8 probe_table.py                    # probe.log -> 15 区域判别表
python -X utf8 handlers_ab.py                    # -> dump/handlers_v1_v2.txt（landed/r71a/r71b 的 inst/blocks）
python -X utf8 cmp_prevspec.py                   # final spec 与 v2 产物记录全等性
```

## 10. 关键文件

- spec：`specs/R71-exception_exit.json`（final）、`specs/_v1_rejected_*.json`、`specs/_v2_rejected_*.json`；
  生成器 `mk_spec_final.py`（v1→v2 的历史脚本 `mk_spec_v2.py`）。
- 探针/事实：`patch_probe.py`、`fix_probe.py`、`fix_probe2.py`、`probe.log`、`probe_table.py`、`regionfacts.py`、`dbg/`。
- 镜像与产物：`mirr_r71b/`（final）、`mirr_r71a/`（v1，留档）、`mirr_probe/`（插桩）、`build_r71b/`、`build_landed/`、`build_r71a/`。
- dump：`cf1_r71b.jsonl`、`b_r71b.jsonl`（及其 `*_prevspec` 对照）、`pv71_cf1_r71b.txt`、`pv71_r71b.txt`、
  `strict_r71b_cf1.json`、`strict_r71b_b.json`、`battery_r71b.txt`、`canary_r71b.txt`、`synth_exc.txt`、
  `epilogue_evidence.txt`、`mirr_r71b_prevspec.py`、`handlers_v1_v2.txt`。
- 落点（只读）：`F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py` L15503 `def _if_generate_else_branch`，
  L15549 `if region.else_blocks:`。
