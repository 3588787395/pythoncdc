# Round 25 臂设计（量具、锚点、门禁）

基准核：`8a0c269a`（Round 24 落地后的工作树）。私有镜像 `D:/Temp/r25land/mirr/head25`
由 `probes/mkmirror25.py` 从工作树复制并断言两文件逐字节相同：
`core/cfg/region_analyzer.py = 6df13cdaf815920c`、`core/cfg/region_ast_generator.py = a365c378e6a40fed`。

## 一、尺与量具

* 官方尺：仓库自带 `scripts/pyc_batch_verify.bytecode_diff(pyc, 产物)`，逐函数给出
  `orig_count / decomp_count / jump_diffs / true_diffs / first_diff{index,orig_op,orig_arg,decomp_op,decomp_arg}`。
* 臂（同一 shell 命令不超过 300 s，全部 `-X utf8`，绝不设 `PYTHONIOENCODING`）：
  * `probes/pool25.py`：单核、断点续跑、可分片；产物写 `D:/Temp/r25land/pool/`，
    记录写 `dump/pool25_{0..3}.jsonl`（40 个 partial 文件，每文件一行，含每缺陷函数全字段与产物 sha256-16）。
  * `probes/headsha24.py`（Round 24 原样复用）：不反编译，直接哈希磁盘上由 `batch --all --round 24`
    写出的 `*OK.py` ⇒ 本轮 HEAD 参照臂 `dump/head25_products.jsonl`（402 条，0 个不可读）。
  * `probes/batt25.py`（`batt24.py` 换 BUILD 目录）：两核锚点 A/B，输出 FIXED/BROKEN/MOVED/SAME 与翻文件清单。
  * `probes/mk_spec25.py` + `probes/apply_spec25.py`：从「实测过的候选镜像」反推字节精确落地规格，
    规格自带自证（对 BASE 应用必须哈希等于候选），`apply_spec25.py` 只允许写那两个 permitted 文件。

## 二、对照跑（零噪声证明）

`batt25.py --cores head=head25,cand=head25 --list dump/anchors25.txt`：
`TALLY {"FIXED":0,"BROKEN":0,"MOVED":0,"SAME":21,"FLIPS":[]}` —— 同一核两次跑，21 个逐函数读数全等，
产物哈希无一处变化 ⇒ 量具与 A/B 记账本身不产生假阳性。

## 三、本轮锚点（逐文件读数，均取自 `dump/pool25_*.jsonl`）

主攻族：**等长且带跳转差的尾部同形块换位**（Round 23/24 移交的 D3）。满足该形状的函数与其所在文件的
官方读数（`matched/total`，`o=` 指令数，`j=` jump_diffs，`t=` true_diffs，`@` first_diff 下标）：

| 文件 | 函数 | 官方 | 形状 | first_diff |
|---|---|---|---|---|
| `IQEngine/data/data_proxy.pyc` | `get_bar` | 8/9 | o=86 j=3 t=8 | @76 `LOAD_FAST self` vs `LOAD_CONST None` |
| `IQEngine/plugins/plugin_fly_data/__init__.pyc` | `_on_before_trading_start_trading_thread` | 19/20 | o=62 j=2 t=19 | @43 `LOAD_FAST order` vs `JUMP_FORWARD 364` |
| `fly/dumpload/load_daily.pyc` | `<module>` | 22/23 | o=913 j=1 t=19 | @596 `JUMP_FORWARD 2478` vs `PUSH_NULL None` |
| `fly/logger.pyc` | `write_logging_thread` | 28/30 | o=113 j=1 t=40 | @71 `LOAD_FAST msgs` vs `JUMP_FORWARD 612` |
| `IQCommon/graph.pyc` | `_process_task_queue` | 29/31 | o=378 j=1 t=118 | @119 `LOAD_CONST None` vs `JUMP_FORWARD 842` |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | `after_trading_cancel_order` | 104/119 | o=155 j=3 t=122 | @31 `LOAD_GLOBAL isinstance` vs `LOAD_CONST None` |
| `IQCommon/util/fileio_utils.pyc` | `write` | 12/14 | o=637 j=4 t=519 | @42 `LOAD_CONST None` vs `JUMP_FORWARD 778` |

**只含这一个缺陷、修好即整文件翻 ok 的是前三行**（`data_proxy` / `plugin_fly_data/__init__` / `load_daily`）。
后四行的换位只是其损伤的一部分（`true_diffs` 40/118/122/519），因此它们进电池作**观察项**而非验收项。

`get_bar` 的块级对齐差（Round 24 已存档 `D:/Temp/r24diag/jump/out/NORM_get_bar__{orig,decomp}.txt`）：
内层 elif 链的 `else: return BarData(...)` 与外层 `if` 的 `else: return None` 两个兄弟尾块**互为换位**，
3 个 jump_diff 是随之改线的 `POP_JUMP_FORWARD_IF_NONE` 目标（orig 落 574、decomp 落 582）。

## 四、门禁（顺序固定，全部串行；候选只进镜像，`core/` 在校验代理运行期间不得改动）

* **G0 非空洞**：锚点 `data_proxy.get_bar` 的官方读数在候选核下必须变化（`true_diffs` 8 → 更小，或该函数消失于 mismatch 清单）。
* **G1 修复面**：电池 `PRED_R25A_FIX` 用例从 FAIL 转 OK，且产物的 MUST_CONTAIN 串在位。
* **G2 对照面**：`CONTROL` 用例在 head 与 cand 下都 OK（这些形状本轮不改）。
* **G3 无回退**：任何用例不得从 OK 变 FAIL；`quotation.pyc`（142/143）与 Round 23/24 电池 `broken=0`。
* **G4 稳定性面**：`PRED_R25A_STABLE` + `CONTROL` 用例产物 sha256 逐字节不变 —— 这是触发面判据，
  比任何聚合率都严：它直接数「有多少产物被改动」。
* 电池必须先对**已落地字节**（镜像由工作树重建）跑通，才允许 402 文件 A/B。
* 收口：靶子 `single` → `quotation.pyc` 零副作用 → `batch --all --round 25` 回填索引 → `stats` 只报本轮打印的那一条序列。

## 五、锚点的严格尺预读数（`logs/strict_pre25.txt`，对磁盘上 landed 产物）

两把尺在这三个锚点上**并不同口径**，这一条直接改写主攻形状的选择：

| 文件 | 官方 | 严格 | 严格读法 |
|---|---|---|---|
| `IQEngine/data/data_proxy.pyc` | 8/9，`get_bar` 86/86 j3 t8 | 8/9 | `[seq_len] orig=86 decomp=90` —— 产物多 4 条，官方把它当成等长 ⇒ 官方的「等长」是归一化后的等长 |
| `IQEngine/plugins/plugin_fly_data/__init__.pyc` | 19/20，`_on_before…` 62/62 j2 t19 | 20/21 | `[seq_len] orig=66 decomp=62` —— 产物少 4 条 |
| `fly/dumpload/load_daily.pyc` | 22/23，`<module>` 913/913 j1 t19 | 22/25 | `[seq_diff] #596 JUMP vs PUSH_NULL`（与官方 first_diff 同下标）＋ `api_get_from_zeromq`、`filter_abnormal_data` 各一条 `target_diff` |
| `fly/data/quotation.pyc`（零副作用基线） | 142/143 | 148/150 | `change_his_to_forward [seq_len] 548/549`、`get_trend [target_diff] #10` |

⇒ **纯次序缺陷只发生在 `load_daily.<module>`**：等长、同一条指令流，只是两条落在 #596 处换了位置。
`get_bar`（+4）与 `_on_before_trading_start_trading_thread`（−4）严格尺看是**发射量**缺陷，官方尺把它们
伪装成了等长换位 —— 所以「同形尾块唯一归属」判据必须先能解释 +4/−4，否则只是修补官方的盲区。
本轮判据的取证次序：先 `load_daily.<module>`（次序），再 `get_bar`（多发射 4 条）。

**盲区机制已定位（编排方与诊断代理各自独立测得同一结论）**：官方尺的
`testqouter/round1/base.py::_trim_spurious_intermediate_returns`（R97）会在对齐位置上静默删掉产物里
**两对** `LOAD_CONST None + RETURN_VALUE`（`get_bar` 的 @75/@77），R101 再删末尾那对，
于是严格尺的 `orig=86 decomp=90` 在官方尺里读成 86/86。
⇒ 「等长」这一族名要拆成两个子因：**（i）产物多造了原字节码里不存在的隐式 `return None` sink 块**
（`get_bar` +4、`_on_before_trading…` −4 属此）；**（ii）真实存在的兄弟块换了发射次序**（`load_daily.<module>` 属此）。
两者都需要「哪条块尾无条件跳转/哪个 sink 块归属于哪个臂」的同层判据，但 (i) 还牵涉 R16 记录的
sink-arm 归并规则（那条规则过度触发却是承重件，直接删它 = improved 8 / broken 5）。


## 六、编排方独立取证：`load_daily.<module>`（最干净的次序见证，等长且严格尺也等长）

用 `probes/dl25.py`（直接调用官方尺自己的 `testqouter/round1/base.get_bytecode_instructions` 与
`compare_bytecode`，故下标与 `first_diff.index` 同口径）读出 `orig=1017 decomp=1017 true=19 jump=1`：

* 原始流：`#596 JUMP_FORWARD 2478` → **A** = `#597-601 PUSH_NULL; LOAD_NAME print; LOAD_CONST "ERROR:********获取'000300.SS…"; CALL 1; POP_TOP`
  → **B** = `#602-616 PUSH_NULL; LOAD_NAME print; LOAD_CONST '++++++结束更新的执行时间++++++：%s'; …strftime…; CALL 1; POP_TOP`
* 产物流：**B** = `#596-610` → `#611 JUMP_FORWARD 2562` → **A** = `#612-616`
* 唯一的 `jump_diff` 在 `#281 POP_JUMP_FORWARD_IF_NONE`，原始目标 2456 / 产物目标 2540（同一个块，随换位改线）。

产物源码对应位置（`D:/Temp/r25land/diag/load_dailyOK.py`）：
```
468                  bsuccess = True
469                  print('++++++结束更新的执行时间++++++：%s' % …)      # B，落在 if 的 true 臂末尾
470              else:
471                  print("ERROR:********获取'000300.SS'…")              # A，else 臂
```

⇒ 这一例**不是两块互换，而是三物件旋转**：原始是 `JUMP · A · B`，产物是 `B · JUMP · A`。
把它与 `get_bar`（两块互换、`JUMP` 在两块之前）放在一起看，共同分母是：
**那条块尾无条件 `JUMP_FORWARD` 究竟归属于哪个块 —— 它前面的块还是它后面的块**。
本轮判据必须同时解释这两种旋转，否则只会修掉一个见证而把另一个改得更坏（Round 24 线 A 正是这样死掉的）。

## 七、翻转集按族计数（`probes/flip1_25.py`，只数「修一个函数即整文件翻 ok」的 16 个 deficit-1 文件）

| 族 | 文件数 | 文件（单个缺陷函数的官方读数） |
|---|---|---|
| 等长且带跳转（次序/归属） | 3 | `data_proxy.get_bar` 86/86 j3 t8；`load_daily.<module>` 913/913 j1 t19；`plugin_fly_data/__init__._on_before_trading_start_trading_thread` 62/62 j2 t19 |
| 产物偏短（发射不足/整块丢） | 7 | `instance._init_config` 86/84；`function.save_testds_to_json` 314/310 j19 t8；`strategy.tick_worker_thread` 268/247 j32；`matcher.match` 713/689 j9；`flytools.acquire` 88/85；`default_event_source.events` 510/486；`persist/__init__.can_resume_strategy` 89/57 |
| 产物偏长（过量发射） | 6 | `replace_utils.decrypt_database_url` 295/324；`executor.check_before_trading` 243/254；`custom_tools.memory_handler` 65/71；`quotation.change_his_to_forward` 547/548；`api_base.cancel_order` 60/61；`realtime_event_source.clock_worker` 1275/1291 |

⇒ 本轮主攻「等长且带跳转」族：**它是三文件翻转集，且三例的 first_diff 都是「块尾无条件
`JUMP_FORWARD` 与它相邻兄弟块的归属」**。

**必须先绕开的失败教训（Round 24 线 A 的否证读数）**：第一版候选（放行/删除可疑的多余无条件跳转）
在 402 文件 A/B 上是 better=2 / equal=8 / worse=14，并打破 11 个当前 ok 的文件 —— 也就是说
「看到 `X/JUMP_FORWARD` 就消跳转」在这批语料上是净负的。本轮判据只能表述为
**「哪一个块拥有这条 JUMP_FORWARD 与紧随其后的兄弟块」的同层归属规则**，
并且候选必须先通过电池 G4（对照面产物逐字节不变）才允许上 402 文件。


## 九·补、备选线（Round 24 未收口的异常布局）已取证到的位置

`probes/exc25.py`：113 个失配函数里**首差**落在异常族操作码上的只有 4 个，其中两个所在文件是 deficit-1：

| 文件 :: 函数 | 官方 | 首差 |
|---|---|---|
| `IQEngine/plugins/plugin_system_risk_calculation/function.pyc :: save_testds_to_json` | 14/15 | o=314 d=310 j=19 t=8，@302 `POP_EXCEPT` vs `RERAISE 0` |
| `IQCommon/manager/instance.pyc :: _init_config` | 31/32 | o=86 d=84 j=1 t=37，@49 `LOAD_CONST None` vs `PUSH_EXC_INFO` |
| `IQCommon/strategy/wizard_quant_api.pyc :: wizard_quant_check_limit` | 48/53 | j=2 t=10，@? `JUMP_BACKWARD 92` vs `PUSH_EXC_INFO`（所在文件另有 4 个失配函数） |
| `IQCommon/api/klinedata.pyc :: get_all_real_daily_kline` | 40/45 | j=3 t=26，`JUMP_BACKWARD 86` vs `PUSH_EXC_INFO`（同上） |

`save_testds_to_json` 的尾部（官方尺自己的下标）：
```
orig   302-305 : POP_EXCEPT; POP_EXCEPT; LOAD_CONST None; RETURN_VALUE
       310-313 : RERAISE 0; COPY 3; POP_EXCEPT; RERAISE 1
decomp 302-305 : RERAISE 0; COPY 3; POP_EXCEPT; RERAISE 1        （310-313 不存在）
```
⇒ 该例同时有「少 4 条」与「重抛链被提前」两个后果，且它落在 `try/except/finally` 与 `with` 嵌套的交界处；
本轮不动它（Round 24 的异常布局代理在 150 轮内没有收口，本轮预算优先给翻转集更大的次序族），
把它作为 Round 26 的起点连同上表一起存档。


## 八、复现约束（Round 24 否证结论，必须遵守）

从**产物源码**重建的 `.py` 全部官方 2/2 通过（产物重编译得到的块布局与语料 pyc 不同 ⇒ 换位不复现）。
⇒ 本轮最小复现必须按**字节码布局**构造：两个兄弟尾块各自是「不同嵌套深度条件」的 else 目标，
且两个 `if` 之间夹足够多的代码，使原始落地次序与生成器选择的次序相反。
