# Round 20 验证记录（fixes）：R20-A 逐步骤实测

设计见 `arm-design.md`，逐条两世界实测见 `test_repros/round20_rollover/ANALYSIS.md`，
结果汇总见 `OUTCOME.md`。以下数值全部是工具/脚本自打印输出（我的 scratch = `D:/Temp/r20c/`）。
落地前 HEAD = `5c63ce6b`（`core/**` 与 `b7c03065`/`e42ab35b` 逐字节同源，仓库清理提交不动核）。

## 一、落地补丁（步骤 1）

`D:/Temp/r20c/fix/r20a_patch.py`（字节级：BOM 原样／纯 CRLF／锚点唯一／`ast.parse`／拒绝二次应用）
自打印：

```
[analyzer] bytes   1652534 -> 1655806  (+3272)
[analyzer] lines   26651 -> 26694
[analyzer] crlf    26693 == lf 26693 (纯 CRLF)
[analyzer] BOM     无（原文件亦无）
[analyzer] sha16 raw 255d53d3c8707a07 -> eb378bd197e2efba
[analyzer] sha16 lf  255d53d3c8707a07 -> 2311fcbbea5c166d
[analyzer] ast.parse OK, 26694 行
[generator] bytes   2970385 -> 2972400  (+2015)
[generator] lines   48227 -> 48249
[generator] crlf    48248 == lf 48248 (纯 CRLF)
[generator] BOM     保留
[generator] sha16 raw faf70dafbce09acf -> 9dff8c0ea8ece556
[generator] sha16 lf  9e8c7a6171d8ed81 -> 56f087fa178b02bf
[generator] ast.parse OK, 48249 行
R20-A 补丁已应用
```

⇒ `core/cfg/region_analyzer.py` 无 BOM、纯 CRLF（补丁前 `crlf == lf == 26650`）；
`core/cfg/region_ast_generator.py` UTF-8 BOM ＋ 纯 CRLF，两侧均保持。
`git diff --numstat`：`region_analyzer.py 46/3`、`region_ast_generator.py 23/1`。
其中**判据代码**（剥掉整行 `#` 注释后与 HEAD 做 unified diff）实测：

```
==== core/cfg/region_analyzer.py  代码行(去全注释) +19 -3
==== core/cfg/region_ast_generator.py  代码行(去全注释) +5 -1
```

（analyzer 的 +19 = 2 个 frozenset 常量 + 谓词函数体 7 行 + 英文 docstring 7 行 +
`if/elif`→三析取项改写 +3；generator 的 +5/−1 = 只在既有 splice 守卫上追加既有终止判据。）

**与已实测候选 `f3` 的等价性核对**（`D:/Temp/r20b/mirror/f3`，逐文件剥注释后 diff）：

```
==== core/cfg/region_analyzer.py code-only diff lines: 0 a_lines 19316 b_lines 19316
==== core/cfg/region_ast_generator.py code-only diff lines: 0 a_lines 37315 b_lines 37315
```

⇒ 落地核的判据代码与候选 `f3` 逐行相同（我只加了中文 `[R20-A 修复]` 注释：识别条件／归约方式／
唯一归属／反编译流程／保留理由），候选上的全部实测对本落地核有效。

## 二、单点（修到完全 OK，步骤 2）

孪生 B `scripts/pyc_batch_verify.py single site-packages/IQEngine/utils/logger/handlers.pyc`：

```
  decompile_status:   ok
  total_functions:   14
  matched_functions: 14
  match_rate:        100.00%
  missing_in_decomp: []
  extra_in_decomp:   []
```

同一文件的严格尺子：

```
  OK     17/17  IQEngine/utils/logger/handlers.pyc
文件级：全部一致 1 / 1，有真缺陷 0
函数级：严格一致 17 / 17
```

孪生 A `single site-packages/IQCommon/logger/handlers.pyc`：

```
  decompile_status:   ok
  total_functions:   18
  matched_functions: 18
  match_rate:        100.00%
```

孪生 A 严格尺子（残差必须只剩上一棒登记过的那一条）：

```
  DEFECT 29/30  IQCommon/logger/handlers.pyc
           - <module>.TWHThreadController._target: [seq_len] orig=192 decomp=190
文件级：全部一致 0 / 1，有真缺陷 1
函数级：严格一致 29 / 30
```

目标函数逐条（`_r10_strict_check` 的 `filtered/strict_compare` 直读两世界）：

```
IQCommon/logger/handlers.pyc        <module>.RotatingFileHandler.perform_rollover len(orig)=119 len(decomp)=119 verdict=OK
IQEngine/utils/logger/handlers.pyc  <module>.RotatingFileHandler.perform_rollover len(orig)=127 len(decomp)=127 verdict=OK
   carry-over <module>.TWHThreadController._target -> orig=192 decomp=190 seq_len   （孪生 A，原样未动）
```

## 三、quotation.pyc 单验（步骤 3）

`single site-packages/fly/data/quotation.pyc`：

```
  decompile_status:   partial
  total_functions:   143
  matched_functions: 142
  match_rate:        99.30%
  mismatches (1):
    - change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377
```

与 Round 19 记录逐字相同。产物未被改写（前后 sha256 相同、`git status site-packages/fly/data/` 为空）：

```
c0d3c312f11f5c40fa629b5aa548a6ac9378f67850010a393b16df85687b3e22  site-packages/fly/data/quotationOK.py   （前）
c0d3c312f11f5c40fa629b5aa548a6ac9378f67850010a393b16df85687b3e22  site-packages/fly/data/quotationOK.py   （后）
```

⇒ 本补丁对 quotation.pyc 零副作用。

## 四、全量产物门（步骤 4，402 条目分 8 片）

基线 = **落地前**磁盘产物逐函数严格比对（打补丁之前先跑，`D:/Temp/r20c/gate/b00.txt … b07.txt`，
`_r10_strict_check.py --manifest <片清单>` 以 utf-8 写出；8 片函数级分别
716/760、450/465、519/522、865/881、829/844、968/992、709/749、943/991，
基线共 66 个 DEFECT 文件，其中含 `DEFECT 28/30 IQCommon/logger/handlers.pyc`、
`DEFECT 16/17 IQEngine/utils/logger/handlers.pyc`）。逐片 SUMMARY：

```
g00 CLEAN=38 UNCHANGED=11 WORSENED(rolled back)=2          processed=51 elapsed=32s
g01 CLEAN=45 UNCHANGED=6                                   processed=51 elapsed=68s
g02 CLEAN=49 UNCHANGED=2                                   processed=51 elapsed=16s
g03 CLEAN=46 UNCHANGED=4 WORSENED(rolled back)=1           processed=51 elapsed=70s
g04 CLEAN=42 UNCHANGED=7 WORSENED(rolled back)=2           processed=51 elapsed=36s
g05 CLEAN=40 REGRESSION(rolled back)=1 UNCHANGED=10        processed=51 elapsed=58s
g06 CLEAN=44 UNCHANGED=7                                   processed=51 elapsed=32s
g07 CLEAN=32 UNCHANGED=10 WORSENED(rolled back)=3          processed=45 elapsed=35s
合计：processed=402  CLEAN=336 UNCHANGED=57 WORSENED(rolled back)=8 REGRESSION(rolled back)=1
```

9 项异常与 Round 19 **逐文件、逐数值相同**，无第 10 项：

```
  [WORSENED(rolled back)] IQCommon/api/klinedata.pyc                                 52/63 -> 50/63
  [WORSENED(rolled back)] IQCommon/util/common_func.pyc                              18/22 -> 17/22
  [WORSENED(rolled back)] IQData/plugins/plugin_system_realquote/real_quote.pyc      37/45 -> 35/45
  [WORSENED(rolled back)] IQEngine/plugins/plugin_fly_data/__init__.pyc              20/21 -> 19/21
  [WORSENED(rolled back)] IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc   17/18 -> 16/18
  [REGRESSION(rolled back)] IQEngine/plugins/plugin_system_persist/json_persistance.pyc 7/7 -> 6/7
  [WORSENED(rolled back)] fly/common/flytools.pyc                                    65/66 -> 63/66
  [WORSENED(rolled back)] fly/common/market_time.pyc                                  9/10 ->  8/10
  [WORSENED(rolled back)] fly/data/quote_handler.pyc                                 64/72 -> 61/72
```

与 Round 19 的 `CLEAN 335 / UNCHANGED 58` 相比净变化 1 项（UNCHANGED→CLEAN）＝孪生 B
（`IQEngine/utils/logger/handlers.pyc` 基线有 1 缺陷、产物门复验为 17/17 全清）⇒ 本轮零新增回退，
回滚全部生效。落地后 `git status` 只有 5 个受控路径：

```
 M core/cfg/region_analyzer.py
 M core/cfg/region_ast_generator.py
 M pyc_index.json
 M site-packages/IQCommon/logger/handlersOK.py
 M site-packages/IQEngine/utils/logger/handlersOK.py
```

⇒ 8 片产物门重生成 400 个非孪生产物后与磁盘产物逐字节相同（回滚生效、零附带漂移）。

**基线截断的补充实测**：`_r10_strict_check.py` 的 DEFECT 明细每文件最多打印 12 条
（`r['bad'][:12]`），对缺陷数 >12 的文件其 `baseline_bad` 名集不完整。用
`D:/Temp/r20c/probes/r20_prod_names.py`（不受该上限影响；落地前产物取 `git show HEAD:` 的
405 个受跟踪 `*OK.py`，落地后取当前磁盘产物，逐函数严格比对名集）全量复核：

```
IQCommon/logger/handlersOK.py            pre=2 post=1  new=[] gone=['<module>.RotatingFileHandler.perform_rollover']
IQEngine/utils/logger/handlersOK.py      pre=1 post=0  new=[] gone=['<module>.RotatingFileHandler.perform_rollover']
[PRODNAMES] files=402  name-set-diff=2
```

⇒ 产物层精确名差 = 两孪生的 `perform_rollover` 消失，`new=[]` ⇒ 402 个文件里**没有任何一个新出现的
缺陷函数名**，9 文件漂移族（含其 >12 缺陷的成员）名集零变化。

## 五、全量逐函数 A/B 归因（步骤 5，与门 4 分开）

pre-landing 核镜像：`git archive 5c63ce6b core bytecode pycdc.py _r10_strict_check.py | tar -x -C
D:/Temp/r20c/mirror/base` ＋ 复制 `pyc_index.json`。归档件与工作区逐字节核对（`core.autocrlf=true`
下 git archive 已做 EOL 归一，实测无需再处理）：

```
core/cfg/region_ast_generator.py archived bytes 2970385 bom True crlf 48226 lf 48226 sha16 faf70dafbce09acf
   already identical to pre-landing working tree
core/cfg/region_analyzer.py archived bytes 1652534 bom False crlf 26650 lf 26650 sha16 255d53d3c8707a07
   already identical to pre-landing working tree
```

cand 镜像 = 当前工作区拷贝；两侧唯一差别就是 §一那两个 hunk：

```
base core/cfg/region_analyzer.py         1652534 255d53d3c8707a07
base core/cfg/region_ast_generator.py    2970385 faf70dafbce09acf
cand core/cfg/region_analyzer.py         1655806 eb378bd197e2efba
cand core/cfg/region_ast_generator.py    2972400 9dff8c0ea8ece556
```

`D:/Temp/r19/probes/r19_par.py <coredir> <tag> N <start> <end> decomp` 分 4 片
（0-81/81-181/181-301/301-402，每片 base、cand 并发，各片 9-12 路）：

```
slice 0..81    base rc=0 cand rc=0   TOTAL records 81 (73s) / 81 (79s)
slice 81..181  base rc=0 cand rc=0   TOTAL records 100 (44s) / 100 (45s)
slice 181..301 base rc=0 cand rc=0   TOTAL records 120 (99s) / 120 (86s)
slice 301..402 base rc=0 cand rc=0   TOTAL records 101 (179s) / 101 (171s)
```

汇总（`D:/Temp/r20c/probes/r20_sum.py`）：

```
base chunks=42 records=402  cand chunks=42 records=402
base tag=r20base  sum(n_ok)=5985   cand tag=r20cand  sum(n_ok)=5987

==== cand r20cand : improved=2 broken=0 signature-only=0
  IMPROVED IQCommon/logger/handlers.pyc                                   28->29  remaining=['<module>.TWHThreadController._target']
  IMPROVED IQEngine/utils/logger/handlers.pyc                             16->17  remaining=[]
err records: base=0 cand=0
```

⇒ improved 恰为两孪生、broken=0、signature-only=0、402/402 记录、零异常，与候选 `f3` 在
`D:/Temp/r20b/logs/absum_f3b.txt` 上的打印逐字吻合。

## 六、round20_rollover 电池（步骤 6，26 项）

落地前核镜像（`--core D:/Temp/r20c/mirror/base`，我的实测，等价于诊断师的 HEAD 表）：

```
BATTERY base :: repros=26  MISMATCH=18  MATCH=8  ERROR=0  UNEXPECTED=11  NOT-REPRODUCED=0
```

（11 项 UNEXPECTED 正是候选表里判 MATCH 的 11 个锚点在 pre-landing 核上仍 MISMATCH：
`01 38/34`、`02 112/110`、`03 53/51`、`04 69/65`、`05 40/36`、`06 122/120`、`12 40/38`、
`13 37/36`、`14 38/46`、`15 49/45`、`16 39/38`。）

落地核 + 旧 EXPECT（HEAD 真值表）：

```
BATTERY pythoncdc-main :: repros=26  MISMATCH=7  MATCH=19  ERROR=0  UNEXPECTED=11  NOT-REPRODUCED=0
```

⇒ 11 个锚点全部翻正（就是上面那 11 项），7 项残留逐条签名与候选 `f3` 实测相同
（`17` 从 `47/40` 变 `47/39`：量级未变的同族别因，非恶化）。按 mandate 把 `EXPECT` 整表
改写为落地后实测真值（锚点→`SENTINEL`、7 项同族别因→`MISMATCH`、守卫/负对照→`MATCH`、
本表 `UNCONFIRMED` 为空：26 项在两世界上都有确定实测结论），`EXPECT_CAND = dict(EXPECT)`。

落地核 + 新 EXPECT：

```
BATTERY pythoncdc-main :: repros=26  MISMATCH=7  MATCH=19  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0
exit code 0
```

## 七、既有电池（回归复验，全部 `--strict`）

```
round13      repros=25  MISMATCH=12  MATCH=13  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2   （r13_20_for_else_break_lost 本轮转 MATCH，EXPECT 改标 SENTINEL）
round13b     repros=0   strict-MATCH=0 strict-MISMATCH=0
round14      repros=17  MISMATCH=0   MATCH=17  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round14_join repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0
round15_arm  repros=12  MISMATCH=2   MATCH=10  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_arm  repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_sink repros=15  MISMATCH=0   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2
round17_arm  repros=26  MISMATCH=1   MATCH=25  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round18_arm  repros=20  MISMATCH=0   MATCH=20  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round19_cont repros=39  MISMATCH=4   MATCH=35  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=7
```

十套退出码全 0，与 Round 19 收尾时逐套相同；唯一变化是 `round13` 的
`r13_20_for_else_break_lost`（正是本轮修的形状族）由「复现缺陷」变「已修」：

```
r13_20_for_else_break_lost   MATCH    (expect MISMATCH) UNEXPECTED     ← 改标前
'r13_20_for_else_break_lost': 'SENTINEL',  # fixed by R20-A            ← 改标后（ASCII 注释）
```

## 八、索引与对外序列（步骤 7）

`pyc_index.json` 逐条目比对（HEAD vs 落地后，脚本打印）：

```
entries old/new 402 402
ENTRY DIFF IQCommon/logger/handlers.pyc          changed keys: ['bytecode_match_rate', 'decompile_status', 'matched_functions'] removed: [] added: []
ENTRY DIFF IQEngine/utils/logger/handlers.pyc    changed keys: ['bytecode_match_rate', 'decompile_status', 'matched_functions'] removed: [] added: []
changed entries: 2
sum function_count 5746
```

⇒ 条目数 402、每条 `function_count` 一律不变、Σ=5746；仅 2 条目由 `single` 自己写回
（`partial 0.9444… matched 17` → `ok 1.0 matched 18`；`partial 0.9285… matched 13` →
`ok 1.0 matched 14`）。孪生 A 条目里的 `mismatch_count: 1` 是工具本轮未覆写的旧键，按
「索引只允许工具写回」不改。

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
本轮开始前（HEAD 5c63ce6b）：total_pyc 402  ok_pyc 361  total_functions 5746  matched_functions 5630  97.98%
本轮收尾                  ：total_pyc 402  ok_pyc 363  total_functions 5746  matched_functions 5632  98.02%
```

+2 全部来自本轮补丁（镜像核全量 A/B：improved 2、broken 0）。
