# Round 33 OUTCOME — R33-A 落地：`return` 的值可穿过一条已完结的副作用语句块

落地提交：`core/cfg/region_ast_generator.py`（+31 行，单条判据）＋ `IQCommon/utilsOK.py` ＋
`pyc_index.json` ＋ `test_repros/round33_return_through_statement/` ＋ 本轮记录。

## 一、目标池（实测，基线 = 落地字节 `910a8f74`）

```
baseline(landed round32 index, HEAD 910a8f74, core sha fa43dbc9e878eeacbfe0): files 402 partial 31 sum_deficit 101 deficit1 8 deficit2 12
```

（首行 `core sha` 一项 = 上一轮落地文件 `core/cfg/comprehension_generator.py` 的工作树原始 CRLF 哈希；
本轮动手前 `core/cfg/region_ast_generator.py` 正规化后哈希 `3781872bcc715f2fdb23`，与 `git cat-file blob
HEAD:…` 同值，起点纯净。）基线由 G4 的 `head` 臂（= 改前镜像，逐文件跑完 402）复测拉回实测：与发布索引 `pyc_index.json`
（HEAD 版）**逐文件比对 0 处 `matched_functions`/`function_count` 冲突、0 处 `decompile_status` 冲突**
（`logs/index_vs_head_arm.txt`）—— 索引是测出来的，不是自报的。

## 二、三条线的取舍

* **线 A（编排方一手，靶子 `IQCommon/utils.pyc 21/22`，唯一缺陷 `load_yaml 55/55 j0 t32`）**：
  根因坐实并落地，即 R33-A。
* **线 B（只读代理）**：`function.pyc :: save_testds_to_json 314/310 j19 t8`。交付物
  `logs/hunks_save_testds_to_json.txt`、`logs/dump_save_testds_to_json.txt` 与落地铁读数一致；其引用的
  `_is_other_region_merge`(`:23138`)、`_is_reraise_cleanup`(`:23093`)、`_is_exc_cleanup`(`:23178`)、
  `_is_trivial_return`(`:23106`) 逐个 grep 命中（唯一失准：canonical-owner 注释实在 `:31258`）。
  形状是**终块的第二次物化**（发射侧），与本轮判据不同侧，未落地 → Round 34。
* **线 C（工具线）**：镜像不得继承 `__pycache__`（`_mkmirror` 已加 `ignore_patterns` + 断言）。
  `logs/pycache_probe33.txt` 实测：仓库 `core/` 自带 24 个缓存 pyc，**24/24 valid-timestamp（会被
  CPython 直接采用）、0 个失效、0 个 unchecked-hash**，而 `copytree` 用 `copy2` 保留 `.py` 的
  mtime+size ⇒ 拷进臂里就仍然命中，臂会 import 缓存而不是自己打过补丁的 `.py`；本轮两臂自产的 50 个
  pyc 全部对本臂源文件命中（head 臂键在 2 979 267 B 源、cand 臂键在 2 981 305 B 源）⇒ 臂隔离成立。
  上一轮 G4 的头臂读数与发布索引逐文件一致（`logs/index_vs_head_arm.txt` 0 冲突）所以未出事，但这条
  陷阱本轮已封死。

## 三、根因（一手实测，见 `logs/`）

核内自带的 `R23N6_DEBUG` 自检开关在两处各打出一行 `NO chain`（见证 `block@68`、靶子 `block@138`，
last instrs 均为 `['LOAD_METHOD','PRECALL','CALL']`）。`logs/probe_*_pre.txt` 把两处 BFS 前沿逐块列出，
两个形状**完全同构**：持值 TRY_BODY → 正常路径清理语句块（`LOAD_FAST/LOAD_METHOD/PRECALL/CALL/POP_TOP`，
净栈效应 0、终止 `POP_TOP`）→ `with __exit__` + `RETURN_VALUE` 终点。`_is_cleanup_only_no_return`
只有 opname 白名单（无 `LOAD_FAST`/`LOAD_METHOD`），故在中间那块断开，被持有的返回值按语句发射，函数
丢掉 `return`。同一份表否证了「后继须属本区域 finally 集」这条更诱人的判据：正常路径清理块实测
`owned=[]`、`copy={}`，取之靶子原地不动。

## 四、判据 R33-A（原则 1 块 = 前导语句 + 尾终止 · 链穿透侧）

在 `_find_return_chain_via_successors._is_cleanup_only_no_return` 的白名单臂之后补一条结构臂：
后继块若 **①净栈效应恰为 0**（入口值栈原样带到出口）**＋②跳过尾跳转后终止于 `POP_TOP`**（自压自弃，
是语句不是值）**＋③块内不传播异常（`RERAISE`/`PUSH_EXC_INFO`/`WITH_EXCEPT_START`）且无任何跳转**
（穿过它控制流仍直线后继），即可被穿透。三条全是栈纪律 / 控制流形状，不读名字、常量、绝对偏移、条数；
白名单臂原样保留，故旧命中路径逐字节不变；任一不满足即回到今日行为。
异常路径 finally 副本被 ②③ 双重挡掉，`with` 处理块被 ①③ 挡掉。

## 五、门禁（严格串行，全部在镜像根 `D:/Temp/r33gate/c33` 量得）

| 门禁 | 判据 | 读数 |
|---|---|---|
| G0 | 合成见证须在改前失败、改后通过 | landed(改前) `16/17 [['w1_with_tryfinally', 47, 47, 0, 32]]` → cand `17/17 []`；入册后复测 head 臂仍 `16/17` 同签名、落地臂 `17/17` |
| G1 | 靶子 + deficit-1 全池（8 文件） | `utils 21/22 → 22/22`；其余 7 文件逐字段不变 |
| G2′ | 上轮 38 合成电池对候选 | `SAME=38 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`；落地后对 landed 复跑仍 `SAME=38` |
| G3 | 承重锚点 102 对候选 | `SAME=102`，Round 32 两锚 `r32c_witness 10/10`、`r32c_repro 17/17`；落地后 landed vs cand `SAME=102` |
| G4 | 全 402 sha-first A/B（发货判据） | `TALLY SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`，唯一改变 `IMPROVED …/IQCommon/utils.pyc  21/22 -> 22/22` |
| G4′ | 严格尺读每个改变产物 | `utils.pyc`：head 产物 `strict clean 25/26 sigma-defect=1 sum_abs_delta=2` → cand 产物 `26/26 sigma=0 sum_abs_delta=0`（该文件转严格干净） |
| G5 | `single` 官方判据 + canary | 靶子 `decompile_status: ok / 22 / 22`；canary `wizard_quant_api.pyc` 残余 4 函数与移交清单同形（`calculate_di`、`params_analysis`、`region_mean_desicion`、`wizard_quant_check_limit`） |
| G6 | `batch --index pyc_index.json --all --round 33` | `[402/402]` → `[BATCH] index written back: pyc_index.json`；`git diff --numstat` 405/405 = 402 条轮次重戳 + 靶子 3 个字段（`partial→ok`、`matched 21→22`、`rate→1.0`），别无他动 |
| G7 | `stats --index pyc_index.json` 原样行 | `total_functions: 5746` / `matched_functions: 5646` / `cumulative_match_rate: 98.26%` |

产物前后（`logs/product_load_yaml_before_after.txt`）：

```
-            loader.get_single_data()
+            return loader.get_single_data()
```

## 六、方法论增益（本轮新得，已写记忆）

1. **先开核内自带的自检开关再猜判据**：`R23N6_DEBUG`（`:45535` 失败分支）一行日志直接指名哪个块、
   以哪三条 op 结尾失败，省掉整轮猜测；配套 `probe_chain.py` 用 `ast` 从出厂源码里读白名单本身，
   探针因此不可能与核漂移。
2. **`--arm` 隔离要打在探针上**：探针第一次跑「改前臂」时因只 `sys.path.insert(0, CORE)` 而未
   `append(REPO)`，`bytecode/` 包解析不到 → 整块输出为空。修成「打印并断言 `pycdc.__file__` 属于当前
   臂」，四张表（pre/post × 见证/靶子）才可信。
3. **`git` 哈希可比性**：`core.autocrlf=true` 下工作树原始 CRLF 哈希与 HEAD blob 永不相等；本轮把
   纯净性断言改成「正规化后 == `git cat-file blob HEAD:…`」，避免上一轮那种 `git show` 误判。
4. **落地即复测**：`land33.py` 的「内存重放 == 被测镜像字节」证明，加上落地后以 `--arm=landed` 复跑
   G0/G2′/G3，才把「电池跑的是落地字节」变成事实而不是断言。

## 七、Round 34 移交

* 线 B 形状（`save_testds_to_json −4`）：需终块第二次物化的发射侧判据，须读「终块无后继 + 跨臂前驱
  重数」，禁读内容同一性与指令条数；与 R31-C 的纯 `discard` 判据同教义反侧。
* 已知风险上界：R33-A 扩大了 BFS 可达集，多条 return 链时先找到哪一条依赖 `successors` 集合弹出序；
  本轮 402 文件 A/B 为 `MOVED=0`，但这不是结构保证 —— 若出现同函数多链形状，先加「链择优」判据。
* 残余 deficit-1 六个：`_init_config 86/84 j1 t37`、`decrypt_database_url 295/324 j1 t250`、
  `tick_worker_thread 268/247 j32 t113`、`events 510/508 j2 t157`、`clock_worker 1275/1291 j15 t480`、
  `match 713/689 j9 t524`；`wizard_quant_api.pyc 49/53` 的 4 个函数（本轮 canary 读数同上）。
* 锚点电池须扩为 104：在 102 之上加 `test_repros/round33_return_through_statement/r33a_witness.pyc`
  （落地字节上应读 `17/17`）与本轮靶子 `IQCommon/utils.pyc`（`22/22`）。见证的 `.pyc` 受 `.gitignore`
  管、不入册（与 Round 32 两个合成件同例），下轮须由受跟踪的 `r33a_witness.py` 以
  `py_compile.compile(src, cfile=<dst>, doraise=True)` 显式指定 `cfile` 重新生成后再跑电池。
* 旧移交未动：R30-B3 与 `r29x_01 <module> 142/138`（汇合块源级嵌套归属残余）。
