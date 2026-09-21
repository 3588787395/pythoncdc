# Round 21 验证记录（fixes）：R21-A 逐步骤实测

设计见 `arm-design.md`，逐条两世界实测见 `test_repros/round21_oauth2/ANALYSIS.md`，
结果汇总见 `OUTCOME.md`。以下数值全部是工具/脚本自打印输出（我的 scratch = `D:/Temp/r21fix/`）。
落地前 HEAD = `15a8de06`（Round 20 收尾）。解释器一律 `D:/Python/python.exe`（3.11.9）＋
`PYTHONIOENCODING=utf-8`。

## 一、落地补丁（步骤 1）

`D:/Temp/r21fix/fix/r21a_patch.py`（字节级：BOM 原样／纯 CRLF／锚点唯一／`ast.parse`／
拒绝二次应用／判据代码与候选 `c6` 逐行 assert 等价）自打印：

```
[analyzer] bytes   1655806 -> 1661311  (+5505)
[analyzer] lines   26694 -> 26766  (+72)
[analyzer] crlf    26765 == lf 26765 (纯 CRLF)
[analyzer] BOM     无（原文件亦无）
[analyzer] sha16 raw eb378bd197e2efba -> 8529b7e8e36dc336
[analyzer] sha16 lf  2311fcbbea5c166d -> 2b9c48a681a2cb23
[analyzer] ast.parse OK, 26766 行
[A] +46 行（替换 8 行为 54 行；其中判据代码 30 行、全行注释 24 行）
[B] +26 行（替换 11 行为 37 行；其中判据代码 18 行、全行注释 19 行）
R21-A 补丁已应用
```

⇒ `core/cfg/region_analyzer.py` 无 BOM、纯 CRLF（补丁前后 `crlf == lf`），两侧保持。
`git diff --numstat`：`region_analyzer.py 74/2`。判据代码净增 **29 行**（站点 A 22、站点 B 7），
注释 **43 行**；剥掉整行 `#` 注释后与 HEAD 做 unified diff：

```
==== core/cfg/region_analyzer.py  代码行(去全注释) +31 -2  a_lines 19574 b_lines 19603
```

（+31/−2 与「净增 29」的 2 行出入是 diff 算法把两处 `break` 行最小化的结果。）

**与已实测候选 `c6` 的等价性核对**：补丁脚本在写盘前对两个站点分别 assert
「新块剥掉全行注释后的行列表 == `D:/Temp/r21d/probes/r21_mk.py` 里
`NEW_MEMBER_C6` / `NEW_ELIF` 的同一行列表」，assert 通过 ⇒ 落地核的判据代码与候选 `c6`
逐行相同（我只把注释改写成 `[R21-A 修复]` 五段式：识别条件／归约方式／唯一归属／
反编译流程／保留理由），候选上的全部实测（孪生 12/12、电池、全量 A/B）对本落地核有效。

站点行号（落地后）：`_check_elif_chain`（def 17991）内注释 18280-18298 ＋ 代码 18299-18310；
`_detect_boolop_conditional_chain`（def 23908）内注释 24270-24293 ＋ 代码 24294-24315。
`git diff -U0` 的 hunk 头：`@@ -18279,0 +18280,19 @@`、`@@ -18281,2 +18300,5 @@`、
`@@ -18284,0 +18307,4 @@`、`@@ -24243,0 +24270,46 @@`。

## 二、单点（修到完全 OK，步骤 2）

`scripts/pyc_batch_verify.py single site-packages/fly/oauthenticator/oauth2.pyc`：

```
  decompile_status:   ok
  total_functions:   11
  matched_functions: 11
  match_rate:        100.00%
  missing_in_decomp: []
  extra_in_decomp:   []
```

同一文件的严格尺子 `D:/Python/python.exe _r10_strict_check.py site-packages/fly/oauthenticator/oauth2.pyc`：

```
  OK     12/12  fly/oauthenticator/oauth2.pyc
文件级：全部一致 1 / 1，有真缺陷 0
函数级：严格一致 12 / 12
```

无任何 DEFECT 行。落地前同一命令打印 `DEFECT 10/12` ＋
`HSIDOAuthCallbackHandler.post: [seq_len] orig=175 decomp=166`、
`OAuthCallbackHandler.post: [seq_len] orig=190 decomp=181`（`D:/Temp/r21fix/logs/`）。

产物 `oauth2OK.py`（只由工具改写）`ast.parse` 通过（7013 chars，纯 CRLF，161 行），
逐行 diff 只有两处 hunk、全在这两个 `post` 里（`D:/Temp/r21fix/logs/oauth2_product_diff.txt`）：
`if status is not None and cgroupmode == '1':` 拆回嵌套 if、`yield self.spawn_single_user(user)`
回到 then 臂、else 臂恢复 `yield self.spawn_single_user(user)` 与各臂 `return None`
（154 → 162 行）。⇒ 恢复的正是被吞的语句与 `return`，无其他内容变化。

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

与 Round 20 `fixes.md` §三 逐字相同。产物未被改写（sha256 前后相同、`git status site-packages/fly/data/` 为空）：

```
c0d3c312f11f5c40fa629b5aa548a6ac9378f67850010a393b16df85687b3e22  site-packages/fly/data/quotationOK.py  （前）
c0d3c312f11f5c40fa629b5aa548a6ac9378f67850010a393b16df85687b3e22  site-packages/fly/data/quotationOK.py  （后）
```

⇒ 本补丁对 quotation.pyc 零副作用。

## 四、全量产物门（步骤 4，402 条目分 8 片）

基线 = **落地前**磁盘产物逐函数严格比对（打补丁之前先跑，`D:/Temp/r21fix/gate/b00.txt … b07.txt`，
`_r10_strict_check.py --manifest <片清单>` utf-8 输出；片清单 `t00…t07` 与 Round 20 逐字节相同
（`diff -q` 八片全 SAME），函数级分别 717/760、450/465、519/522、865/881、829/844、968/992、
710/749、943/991；共 65 个 DEFECT 文件，其中 `DEFECT 10/12 fly/oauthenticator/oauth2.pyc`）。
逐片 SUMMARY（`_r13_gate.py --targets … --baseline … --out …`，rc 全 0）：

```
g00 CLEAN=38 UNCHANGED=11 WORSENED(rolled back)=2            processed=51 elapsed=21s
g01 CLEAN=45 UNCHANGED=6                                     processed=51 elapsed=10s
g02 CLEAN=49 UNCHANGED=2                                     processed=51 elapsed=7s
g03 CLEAN=46 UNCHANGED=4 WORSENED(rolled back)=1             processed=51 elapsed=10s
g04 CLEAN=42 UNCHANGED=7 WORSENED(rolled back)=2             processed=51 elapsed=11s
g05 CLEAN=40 REGRESSION(rolled back)=1 UNCHANGED=10          processed=51 elapsed=12s
g06 CLEAN=44 UNCHANGED=7                                     processed=51 elapsed=18s
g07 CLEAN=33 UNCHANGED=9 WORSENED(rolled back)=3             processed=45 elapsed=24s
合计：processed=402  CLEAN=337 UNCHANGED=56 WORSENED(rolled back)=8 REGRESSION(rolled back)=1
```

9 项异常与 Round 20 **逐文件、逐数值相同**，无第 10 项：

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

与 Round 20 的 `CLEAN 336 / UNCHANGED 57` 相比净变化 1 项（UNCHANGED→CLEAN）＝本轮目标
`fly/oauthenticator/oauth2.pyc 12/12 -> 12/12 [CLEAN]`（该文件在步骤 2 已由 `single` 重生成，
故产物门看到的 before 已是 12/12；其**落地前**基线在 `b07.txt` 里仍是 `DEFECT 10/12`）。
`fly/data/quotation.pyc 148/150 -> 148/150 [UNCHANGED]` 逐字未动。落地后 `git status`
只有 3 个受控路径：

```
 M core/cfg/region_analyzer.py
 M pyc_index.json
 M site-packages/fly/oauthenticator/oauth2OK.py
```

⇒ 其余 399 个产物被工具重生成后与磁盘产物逐字节相同（9 项回滚生效、零附带漂移）；
第 400 个（`realtime_event_sourceOK.py`）被改坏并另行保全，见 §九。

## 五、全量逐函数 A/B 归因（步骤 5，与门 4 分开）

真正的落地基是 `15a8de06`（诊断的 402 全量是在 `5c63ce6b` 上跑的），故按 mandate 在
`15a8de06` 上重跑：base 镜像 `git archive 15a8de06 core bytecode pycdc.py _r10_strict_check.py
| tar -x -C D:/Temp/r21fix/ab/base15` ＋ 复制 `pyc_index.json`；cand 镜像 = 当前工作区的
`core bytecode pycdc.py _r10_strict_check.py` 拷贝。两侧唯一差别就是 §一那个 hunk：

```
base15 core/cfg/region_analyzer.py  1655806 eb378bd197e2efba    （与落地前工作区逐字节相同）
head   core/cfg/region_analyzer.py  1661311 8529b7e8e36dc336
```

`D:/Temp/r21fix/probes/r21_par.py <coredir> <tag> 10 0 402 decomp`（10 片并发，零仓库写入）：

```
base rc=0   TOTAL 402/402 records; missing=0 []
head rc=0   TOTAL 402/402 records; missing=0 []
```

汇总 `D:/Temp/r21fix/probes/r21_sum.py r21base r21head`：

```
records r21base=402  r21head=402

==== cand r21head : improved=1 broken=0 signature-only=1 (sum n_ok base=5987 cand=5989)
  IMPROVED fly/oauthenticator/oauth2.pyc                                  10->12  remaining=[]
  SIG    IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc  bad=['<module>.RealtimeEventSource.clock_worker', '<module>.RealtimeEventSource.get_one_event']
```

err records：`r21base records 402 err 0` / `r21head records 402 err 0`。
⇒ **improved=1（就是目标 pyc 的两个 `post`）、broken=0**、Σn_ok 5987 → 5989（+2），
与诊断在 `5c63ce6b` 上的 `improved=1 broken=0 signature-only=1`、Σ 5985→5987 同形。
signature-only 那一条的实际代价见 §九——它不是中性的。

## 六、round21_oauth2 电池（步骤 6，16 项）

落地核 `D:/Python/python.exe test_repros/round21_oauth2/run_all.py --strict`：

```
core = F:\Downloads\pythoncdc-main   table = EXPECT
repro files = 16 (keys = 16)
BATTERY pythoncdc-main :: repros=16  MISMATCH=3  MATCH=13  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0
exit code 0
```

逐项判定与 ANALYSIS §7 的候选列**完全一致**：01/03/08/10/16 `MATCH (expect SENTINEL) OK-SENTINEL`，
02/04/05/06/07/09/11/15 `MATCH AS-EXPECTED`，12/13/14 `MISMATCH AS-EXPECTED`。
⇒ `EXPECT` 表在诊断交付时**已经是**落地后实测真值（键集合 == 文件名去后缀，`selfcheck` 通过），
本步无需改写；`EXPECT_BASE` 是它的机械映射（SENTINEL→MISMATCH）。

## 七、既有电池（回归复验，全部 `--strict`，全部用工作树落地核）

```
round13        rc=0  repros=25  MISMATCH=12  MATCH=13  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2
round13b       rc=0  round13b repros: 0 strict-MATCH, 0 strict-MISMATCH (of 0)
round14        rc=0  repros=17  MISMATCH=0   MATCH=17  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round14_join   rc=0  repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0
round15_arm    rc=0  repros=12  MISMATCH=2   MATCH=10  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_arm    rc=0  repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_sink   rc=0  repros=15  MISMATCH=0   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2
round17_arm    rc=0  repros=26  MISMATCH=1   MATCH=25  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round18_arm    rc=0  repros=20  MISMATCH=0   MATCH=20  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round19_cont   rc=0  repros=39  MISMATCH=4   MATCH=35  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=7
round20_rollover rc=0 repros=26 MISMATCH=7   MATCH=19  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0
```

十一套退出码全 0，逐套计数与 Round 20 收尾时**逐字相同** ⇒ 本轮没有任何既有锚点被
「顺带修好」（无需改标 `SENTINEL`），也没有任何一项被改坏（`UNEXPECTED=0`）。

## 八、索引与对外序列（步骤 7）

`pyc_index.json` 逐条目比对（HEAD vs 落地后，脚本打印并 assert）：

```
assert OK: entries=402 sum function_count new=5746 old=5746 (==5746)
changed entries: 1
  fly/oauthenticator/oauth2.pyc  ['bytecode_match_rate','decompile_status','matched_functions']
      {(0.9090909090909091, 1.0), ('partial','ok'), (10, 11)}
added entries=0 removed entries=0
```

⇒ 条目 402、每条 `function_count` 一律不变、Σ=5746；仅 1 条目由 `single` 自己写回
（`partial 0.909… matched 10` → `ok 1.0 matched 11`）。`git diff --stat pyc_index.json`
= `3 insertions(+), 3 deletions(-)`。

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
本轮开始前（HEAD 15a8de06 的索引）：total_pyc 402  verified_pyc 402  ok_pyc 363  total_functions 5746  matched_functions 5632  98.02%
本轮收尾                        ：total_pyc 402  verified_pyc 402  ok_pyc 364  total_functions 5746  matched_functions 5633  98.03%
```

**与任务书预期的偏差（如实记录）**：预期 `ok_pyc 364 / matched_functions 5634 / 98.05%`，
实测 `5633 / 98.03%`，少 1。原因是 `matched_functions` 走的是**官方**尺子，而该 pyc 落地前
索引里 `mismatch_count: 1`、`matched_functions: 10`——两个 `post` 里只有一个是官方 mismatch
（另一个只有严格尺子抓得到），所以官方序列只 +1。门下限 402/5746/5632/98.02% 满足。
+1 全部来自本轮补丁（镜像核全量 A/B：improved 1、broken 0）。

## 九、落地时发现的尺子盲区副作用（不在诊断预期内，如实记录）

诊断把 `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` 记为
`signature-only`（bad 计数不变）。落地时按要求复核，实测它**不是中性的**：

* 落地前该文件磁盘产物 = `15a8de06` 核的逐字节输出（`D:/Temp/r21fix/probes/r21_prod_probe.py`
  base15 核 → 21381 chars、LF 归一 sha16 `e5f216ab559526a1`，与 `git show HEAD:` 同 sha）
  ⇒ 它**不在**9 文件漂移族里，此前是核/产物一致的文件。
* 产物门重生成后（落地核）sha 变 `3e367cad6833514f`、18560 chars，严格尺子仍 `10/12`
  但 `clock_worker` 由 `orig=1276 decomp=1251` 变成 `orig=1276 decomp=1079`；
  官方 `bytecode_diff` 同向：`clock_worker orig_count=1275 decomp_count 1250 -> 1078`。
  ⇒ 丢的指令从 25 条涨到 197 条（−172），产物实质变差。
* **归因实验**（`D:/Temp/r21fix/probes/r21a_variant.py` 在 `base15` 镜像上单开一半）：

```
variant a（只站点 A）  chars=18560 sha16=3e367cad6833514f  clock_worker orig=1276 decomp=1079   ← 与两站点全开完全相同
variant b（只站点 B）  chars=21381 sha16=e5f216ab559526a1  clock_worker orig=1276 decomp=1251   ← 与落地前逐字节相同
```

  ⇒ 恶化 100% 出自站点 A（BoolOp 成员块截断），与站点 B 无关。
* **全语料盲区扫描**（`D:/Temp/r21fix/probes/r21_blind.py r21base r21head`，把 §五 两侧记录里
  每个 bad 函数的 `orig/decomp` 取 `Σ|orig−decomp|` 再逐文件比较）：

```
records base=402 cand=402
signature-changed files = 2
  WORSE IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc n_ok 10->10  sum|delta| 26 -> 198
        <module>.RealtimeEventSource.clock_worker            -25 -> -197
  BETTER fly/oauthenticator/oauth2.pyc                       n_ok 10->12  sum|delta| 18 -> 0
TOTAL worse=1 better=1
```

  ⇒ 全语料**只有这一个**函数因本补丁变差，目标文件是唯一变好者。
* **处置**：产物门只按 bad 计数回滚，抓不到这种量级恶化，故该文件按 mandate
  「不得变差」人工保全——`git checkout HEAD -- …/realtime_event_sourceOK.py`
  恢复为落地前逐字节版本（sha256 `125dc621a35690e0…`，与 §九 第一行的落地前 sha 相同；
  内容未手写）。`single` 已按要求在其上重跑（打印 `partial 11/12 91.67%`，
  `mismatches (1): clock_worker: orig=1275 decomp=1078 jump_diffs=3 true_diffs=602`），
  随后恢复产物；索引条目复核为一致：`bytecode_diff(保留产物)` = `total 12 / matched 11 /
  rate 0.9166666666666666 / status partial`，与索引里存的值逐字段相同 ⇒ 写回值与产物版本无关，
  索引无额外改动（§八 的 `changed entries: 1` 已含此核对）。
* **登记**：这是本补丁新增的**第 10 个产物/核不一致文件**（但**不是**第 10 项产物门异常——
  它的门裁决是 `UNCHANGED`）。根因与 SubTask 20.9 的 J1 同族：截断 BoolOp 链后父臂对块的
  双认领没有收口。移交 Round 22（见 `OUTCOME.md` §三）。
