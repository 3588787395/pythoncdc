# Round 73 · OUTCOME

## 1. 本轮任务

- **用户最高裁定（写入 `rounds/round73/scripts/briefs/BRIEF_fix2.md` 第 −1 节，commit `b355043e`）**：
  「就是嵌套 try-except 问题」（重复 5 次）。要求把 try/except 归约路径放在探针优先级上，
  并且中心必须给出定量判决、不得捏造支持数据。
- mandate：本轮至少 1 支 pyc 在 mandated 尺（pylingual `compare_pyc`）由 failure 修到 success，
  且 ADR-1（任何他支回归即整件拒收）全绿。
- 起始 HEAD `b355043e`（其上 `8d136040` = R72 落地）；基线 mandated **6529/6617 = 98.67%**
  （41 支 failure / 88 单元），官方 **5717/5746 = 99.50%**（ok 394 / partial 8 / failed 0）。

## 2. 批次与候选

- `diag1`：按用户指令做 try/except 定向只读诊断（`tryverdict73` / `exctable73` / `firstdiv73`）。
- `fix1`：F-PAD 家族，主候选 `specs/pad_e2fix.json`（1 edit / +29 行，臂 pad6）——
  抑制 then 臂物化 `return None` 后生成的隐式 `else:` 尾块，块序取值移入既有 pure/then/
  无 merge/owned 前置保护之内（`pad2/pad3` 因把 `max()` 放在短路保护之前、空 then 区抛
  `ValueError` 中断发射而被否决，硬证据 `dump/battery_pad2.txt`、`battery_pad3.txt`）。
- `fix2`：F-ABSORB 家族，`absm_abs1_abs2.json`（含 abs1+abs2）——**被中心拒收**（见 §3）。
- `fix3`：F-POLARITY / F-EXCTABLE 手术族，`merged_analyzer.json`（4 edits / +117）+
  `polarity_gen.json`（3 edits / +32），臂 surgm。

## 3. 中心 ADR-1 独立复测（`adr73.py`，串行单跑，不采信子代理数字）

| 臂 | mandated | ADR-1 | 判定 |
|---|---|---|---|
| pad6 | 9 靶 470/509 → **476/509**，4 支转 success，NEW=0 | WORSE=0 IMPROVED=6 | 采纳 |
| surgm | 6 靶 360/392 → **365/392**，2 支转 success | WORSE=0 IMPROVED=4 | 采纳 |
| absm | 41 靶 1671/1759 → 1675/1759，+4 单元，1 支转 success | **WORSE=1** | **拒收** |
| **m73** | 41 靶 1671/1759 → **1684/1759**，**6 支转 success**，NEW=0 | **88 单元 changed 10 WORSE 0 IMPROVED 10** | 落地 |

**absm 拒收理由（如实）**：`IQCommon/api/klinedata.get_multiminute_his_data` sdelta 60 → 64；
且 ORIG 与 landed 各 2 次 `get_kline_by_count_new` load、absm 仅 1 次（丢尾语句，
instr 535/536 → 524）。按 ADR-1「以少发射换」不得作为收益。备选方向 = `BRIEF_fix2.md` §5 的
**abs2**（`region_ast_generator` 补 orphan child 发射），交下轮。

## 4. 合并与落地 m73

- `mkfinal73.py m73` → `m73_region_ast_generator.py.json`（**4 edits / +61 行**）、
  `m73_region_analyzer.py.json`（**4 edits / +117 行**），链式锚点各恰出现 1 次。
- `mbuild73.py m73` → `mirr_m73` → `land73.py land --mirror=mirr_m73`（dry-run
  `replay == measured mirror bytes: OK`）→ `--apply` 两文件 `equals measured mirror=True`。
- 独立复核 `g4g8replay73.py`：从 **HEAD 字节**重放 spec 与 worktree 逐字节相等（两文件 True）；
  `landproof mirr_m73: 33 core files same=33 diff=0`。
- 落地字节：
  - `region_ast_generator.py` 3 210 453 → **3 214 913 B**、sha `6203253987adedcf` → `33e22ee451148af8`、
    BOM=True、CRLF 51566、裸 LF 0、numstat **+66/−5**（净 +61）。
  - `region_analyzer.py` 1 769 617 → **1 778 913 B**、sha `8ca47f7d6b9244cf` → `b9dcc727ea5918ea`、
    BOM=False、CRLF 28337、裸 LF 0、numstat **+119/−2**（净 +117）。
  - `comprehension_generator.py` 未改（`b432a35580989852`）。

## 5. 指标（中心独立重跑）

- **mandated**：6529/6617 = 98.67% → **6540/6617 = 98.84%**（+11 净成功单元）、
  success 361 → **367**、failure 41 → **35**、失败单元 88 → 77、**转绿 6 支 / 转红 0 支**。
- **官方**：**5717/5746 = 99.50%** 维持（ok 394、partial 8、failed 0）。
- **严格**（45 靶去重口径）：ok 1700 → **1704**、缺陷 79 → **75**、NEW defect functions **0**。
- **ADR-1**：WORSE **0** / IMPROVED 10；**G1/G6/G7 全 0 回归**；金丝雀 4/4 pin 全中。
- **G9 合成**：44 支 **IMPROVED=3 REGRESSED=0 SAME=41**。

## 6. 门禁 G0–G9（全 PASS，`center/logs/`）

G0 三支 ast+py_compile OK、跨层模式 code-only **new=0**（首版 raw 口径 +1 为 fix1 注释行，
diff 证据随 artifact 存档）；G1 SAME=30/MOVED=14/REG=0/ERR=0、fully matched 36→36；
G2 金丝雀 4/4 + quotation 152/153；G3 batch **402 verified / 0 failed**；
G3v **6540/6617 = 98.84%**（8 分片合并 + delta）；G4 5717/5746 = 99.50%；
G4′ ok 1700→1704 缺陷 79→75 NEW=0；G5 索引 round-stamp-only=402 / substantive=0；
G5′ blast changed=22 identical=380 **unresolved=0**；G6 82 项 **worse=0**；
G7 SAME=82 REGRESSED=0；G8 402 OK.py 在位 + py_compile bad=0 + Traceback 0；G9 见上。

## 7. 对用户裁定的定量判决（如实入档，不改口也不捏造）

`logs/TRYVERDICT_r73.txt`（数据源 `dump/exctable_diff73.txt`、`dump/firstdiv73.txt`）：

- 87 个失败单元中，原 pyc **无异常表 44 / 有异常表 43**；**et_same 57 / et_diff 30**；
  产品异常表深度从未超过原表（`prod_deeper=0`），嵌套深度 orig vs product 不差 0 项。
- **首分歧位于异常区内 14/87、区外 73/87**；kind：控制流 83 / 字节码 4。
- 结论：**「根因是嵌套 try-except」对 14 单元子族成立，对另外 73 单元定量上不成立**；
  两条读数并列入档，保留分歧而不掩盖。14 单元子族即本轮 `absm` 想覆盖但因 ADR-1 被拒的部分。
- 逐支可修残留（实测）：`trade_live_broker._process_order`（原 et=10）、
  `email_utils.send_email`（首分歧在 handler 内，et=5）、
  `bar.limit_up/limit_down`（首分歧 F-TERNARY，**本轮已修** 82/85 → 84/85）、
  quote 81/92、flytools 65/66。

## 8. 未手改声明与交接

- 未手改任何 `*OK.py`：22 支出货产物全部由 G3 批量工具链重写（`G5p_blast_r73.txt`）。
- 交接下轮（R74）：
  1. **F-ABSORB abs2**（orphan child 发射补全）——本轮 absm 的替代表，ADR-1 须 WORSE=0；
  2. try-except 14 单元子族（handler 内首分歧、异常表出口）；
  3. quote / flytools / trade_info_utils 长尾（cf=1 单元为主）；
  4. `trade_info_utils.trade_operation` target_diff #94（R70 起交接）。
