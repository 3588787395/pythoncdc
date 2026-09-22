# Round 33 arm design — R33-A：`return` 的值可以穿过一条**已完结的副作用语句块**（原则 1 块 = 前导语句 + 尾终止 · 以栈中性判据为白名单补一臂，而非扩表）

## 一、靶子与目标池（实测，基线 = 落地字节 `910a8f74`）

池由 `D:/Temp/r33gate/pool33.py` 从 Round 32 `batch --all` 回写的索引读出，再经两条 `--arm=landed`
分片在真实字节上复测（该分片同时是「索引不是自报数」的证明）：

```
baseline(landed round32 index, HEAD 910a8f74, core sha fa43dbc9e878eeacbfe0): files 402 partial 31 sum_deficit 101 deficit1 8 deficit2 12
```

（首行 `core sha` 一项指的是 `core/cfg/comprehension_generator.py` 的**工作树原始 CRLF 字节**哈希
`fa43dbc9e878eeacbfe0`，即上一轮落地的文件；本轮改动的 `core/cfg/region_ast_generator.py` 在动手前
的工作树字节正规化（`\r\n`→`\n`）后哈希为 `3781872bcc715f2fdb23`，与 `git cat-file blob
HEAD:core/cfg/region_ast_generator.py` 同值 ⇒ 起点纯净。）

deficit-1 的 8 个文件（`c33/landed_d1.jsonl`，逐条一手实测）：

| 文件 | 唯一缺陷函数 | orig/decomp jump true |
|---|---|---|
| `IQCommon/manager/instance.pyc` 31/32 | `_init_config` | 86/84 j1 t37 |
| `IQCommon/util/replace_utils.pyc` 8/9 | `decrypt_database_url` | 295/324 j1 t250 |
| **`IQCommon/utils.pyc` 21/22** | **`load_yaml`** | **55/55 j0 t32** |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` 23/24 | `tick_worker_thread` | 268/247 j32 t113 |
| `…/plugin_system_event_source/default_event_source.pyc` 13/14 | `events` | 510/508 j2 t157 |
| `…/plugin_system_event_source/realtime_event_source.pyc` 11/12 | `clock_worker` | 1275/1291 j15 t480 |
| `…/plugin_system_matcher/matcher.pyc` 16/17 | `match` | 713/689 j9 t524 |
| `…/plugin_system_risk_calculation/function.pyc` 14/15 | `save_testds_to_json` | 314/310 j19 t8 |

取 `utils.pyc`：它是唯一「等长、零跳转差、只差一条语句」的靶子（`load_yaml` 55/55 j0），本轮判据应命中
的正是这类「少一个 `return` 关键字」的形状。

## 二、三条诊断线的取舍

* **线 A（编排方一手，未外包）**：`load_yaml` 根因 → 本轮落地的 R33-A。诊断与实现同在本会话内完成，
  但实现只在镜像上量过之后才写字节（G0→G4′ 全绿才 `--apply`）。
* **线 B（只读代理 `B2`）**：`function.pyc :: save_testds_to_json` 的 −4。代理交付
  `D:/Temp/r33gate/B2/hunks_save_testds_to_json.txt`、`dump_save_testds_to_json.txt`，编排方逐条核对：
  hunk 文件内容与落地铁读的 `['save_testds_to_json', 314, 310, 19, 8]` 一致；其引用的
  `_is_other_region_merge`（`region_ast_generator.py:23138-23140`）、`_is_reraise_cleanup`（`:23093`）、
  `_is_exc_cleanup`（`:23178`）、`_is_trivial_return`（`:23106`）四个标识符 **grep 全部命中且行号相符**；
  唯一失准处是它引用的「汇合块由其 canonical owner …」注释行号（实在 `:31258`，非 `:31226`）。
  结论可用但**本轮不落地**：该形状缺的是终块的**第二次物化**，与本轮「值穿透清理语句」不同侧，
  移交 Round 34（见 §六）。
* **线 C（工具线）**：镜像不得继承 `__pycache__`（已硬化 `_mkmirror`：`ignore_patterns('__pycache__')`
  + 拷贝后断言，并写入项目记忆）。实测依据见 `logs/pycache_probe33.txt`：仓库 `core/` 自带 24 个
  `__pycache__` pyc，**24/24 都是 valid-timestamp（即 CPython 会直接采用）、0 个 unchecked-hash、0 个
  失效**，而 `copytree` 走 `copy2` 会保留 `.py` 的 mtime+size ⇒ 缓存一旦被拷进臂里就仍然有效，臂就会
  import 缓存而不是自己那份打过补丁的 `.py`。本轮两个臂各自跑出的 50 个 pyc 全部对**本臂源文件**
  valid-timestamp（head 臂的 `region_ast_generator.pyc` 键在 2 979 267 B 源上、cand 臂键在 2 981 305 B
  源上），故门禁读数不可能来自别臂或仓库缓存。据此重建的镜像在 G4 里 `ERR=0`，头臂读数与发布索引逐文件一致。

## 三、根因链（编排方一手实测：`logs/dbg_w1.txt`、`logs/dbg_utils.txt`、`logs/probe_w1_68_pre.txt`、
`logs/probe_w1_68_post.txt`、`logs/probe_utils_138_pre.txt`、`logs/probe_utils_138_post.txt`、
`logs/hunk_load_yaml.txt`、`logs/dump_load_yaml.txt`）

1. 靶子的官方读数等长（55/55）、零跳转差，只多 32 条真差；产物里 `load_yaml` 是
   `try: loader.get_single_data() finally: loader.dispose()` —— **`return` 整个不见了**，函数落到隐式
   `return None`。
2. 打开核内既有的 `R23N6_DEBUG` 自检开关（`region_ast_generator.py:45535` 那条链失败时自己会打印），
   两个臂各命中一行：
   ```
   block@68  try_depth=1 NO chain (last instrs: ['LOAD_METHOD', 'PRECALL', 'CALL'])   # 见证 w1
   block@138 try_depth=1 NO chain (last instrs: ['LOAD_METHOD', 'PRECALL', 'CALL'])   # load_yaml
   ```
   即提升闸门已经放行（`_try_depth>0`、块尾不是 `POP_TOP`），失败发生在
   `_find_return_chain_via_successors` 返回 `None`。
3. `probe_chain.py` 把两个 block 的 BFS 前沿逐块量化列出（roles / 净栈效应 / 终止 op / 白名单外 op /
   区域归属）。两处**完全同构**：

   | 角色 | 见证 w1 | load_yaml | 块内容 | 白名单外 | 净栈效应 | 终止 |
   |---|---|---|---|---|---|---|
   | TRY_BODY（持值块） | @68 | @138 | `LOAD_FAST LOAD_METHOD PRECALL CALL` | LOAD_FAST, LOAD_METHOD | +1 | CALL |
   | 正常路径清理语句 | **@106** | **@176** | `LOAD_FAST LOAD_METHOD PRECALL CALL POP_TOP` | LOAD_FAST, LOAD_METHOD | **0** | **POP_TOP** |
   | 穿透终点（with `__exit__` + 返回） | @146 | @216 | `SWAP LOAD_CONST×3 PRECALL CALL POP_TOP RETURN_VALUE` | RETURN_VALUE | −2 | RETURN_VALUE |
   | 异常路径 finally 副本 | @172 | @242 | `PUSH_EXC_INFO … POP_TOP RERAISE` | LOAD_FAST, LOAD_METHOD | 0 | RERAISE |
   | `with` 处理块 | @222 | @292 | `PUSH_EXC_INFO WITH_EXCEPT_START POP_JUMP_…` | … | +1 | 条件跳转 |

4. `_is_cleanup_only_no_return` 只认一张 opname 白名单（`:25487-25494`，其中没有 `LOAD_FAST` /
   `LOAD_METHOD`，因此 CPython 3.11 的方法调用序列整块被拒），BFS 在 @106/@176 处就断掉，走不到
   @146/@216；于是被持有的返回值按「块 = 前导语句 + 尾终止」被当成一条 `POP_TOP` 终结的语句发射。
5. `probe_chain` 同时否证了一条看似更「同层」的候选：正常路径的清理块**并不**在
   `try_finally` 区域的 `finally_blocks` / `cleanup_blocks` / `finally_copy_blocks` 里
   （实测 `finally=[172,216]`、`cleanup=[]`、`copy={}`），所以「后继必须属于本区域 finally 集」这类
   归属判据在此不可用——取之则靶子不翻。

## 四、判据 R33-A（原则 1 块 = 前导语句 + 尾终止 · 链穿透侧）

`core/cfg/region_ast_generator.py`，`_find_return_chain_via_successors._is_cleanup_only_no_return`
在既有白名单臂之后补**一条结构臂**（白名单判据原样保留，故所有旧命中路径逐字节不变）：

> 一个后继块若（①）整块净栈效应恰为 **0** —— 块入口值栈（被持有的 return 值）原样带到块出口；
> （②）跳过尾跳转后的**终止 op 是 `POP_TOP`** —— 该块自压的值由该块自弃，它是语句而不是值，不与
> return 值争抢栈顶；（③）块内**不传播异常**（无 `RERAISE`/`PUSH_EXC_INFO`/`WITH_EXCEPT_START`）、
> **无任何跳转**（含尾跳转）—— 穿过它之后控制流仍是直线后继，链路分叉不因它改变，
> 则该块可作为清理语句被穿透。

三条判据全是 CPython 栈纪律 / 控制流形状，不读函数名、常量、绝对偏移、指令条数。异常路径副本（@172/@242）
被 ② 与 ③ 双重挡掉；`with` 处理块（@222/@292）被 ① 与 ③ 挡掉。任一判据不满足 ⇒ 走原路径返回 `None`，
产物与落地前逐字节相同。

提升之后 `stmts[-1] = {'type':'Return', …}` 并把链路块记入 `generated_blocks`（`:45547-45552`，既有代码），
重复的清理副本因每块唯一归属而不再二次发射——这正是严格尺看到的 `+2` 与多余那份拷贝。

## 五、本轮一手实测（镜像根 `D:/Temp/r33gate/c33`，`r33c.py` 三臂 `head`/`cand`/`landed`）

| 门禁 | 读数 |
|---|---|
| **G0** 合成见证（scratch `r33a_witness.pyc`） | landed(pre) `16/17 [['w1_with_tryfinally', 47, 47, 0, 32]]` → cand `17/17 []`；5 条 CONTROL 同文件内始终匹配 |
| **G0′** 见证入册后复测 | 落地后 head(=改前镜像) `16/17` 同签名，landed `17/17` ⇒ 该文件在跟踪树里仍是**真复现** |
| **G1** 靶子 + deficit-1 全池（8 文件） | `utils 21/22 → 22/22`；其余 7 个文件读数逐字段不变（同函数、同 orig/decomp、同 jump/true） |
| **G2′** 上一轮 38 合成电池 | `TALLY SAME=38 … ERR=0`；落地后对 landed 复跑仍 `SAME=38` |
| **G3** 承重锚点 102 | `SAME=102 REGRESSION=0 MOVED=0`；Round 32 两个锚 `r32c_witness 10/10`、`r32c_repro 17/17`；落地后 landed vs cand `SAME=102` |
| **G4** 全 402 sha-first A/B（发货判据） | `TALLY SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`，唯一 `IMPROVED IQCommon/utils.pyc 21/22 -> 22/22` |
| **G4′** 严格尺读改变产物 | `utils.pyc` vs head 产物 `strict clean 25/26 sigma-defect=1 sum_abs_delta=2` → vs cand 产物 `26/26 sigma=0 sum=0`（该文件转严格干净） |
| **G5** `single` 官方判据 | 靶子 `decompile_status: ok 22/22`；canary `wizard_quant_api.pyc` 残余 4 函数（`calculate_di`/`params_analysis`/`region_mean_desicion`/`wizard_quant_check_limit`）与移交清单同形 |
| **G6** `batch --index pyc_index.json --all --round 33` | `[402/402]` → `[BATCH] index written back: pyc_index.json`；`git diff --numstat` = 405/405（402 条轮次重戳 + 靶子 3 字段：`partial→ok`、`matched 21→22`、`rate→1.0`） |
| **G7** `stats --index pyc_index.json` | `total_functions: 5746` / `matched_functions: 5646` / `cumulative_match_rate: 98.26%`（原样行见 `logs/stats33.txt`，与 G4 候选臂逐文件一致） |

发射产物前后（`logs/product_load_yaml_before_after.txt`）：

```
-            loader.get_single_data()
+            return loader.get_single_data()
```

## 六、被排除的候选与已知代价

* **「后继块须属本 `try_finally` 区域的 finally 集」**：实测否证（§三 5）。正常路径的清理副本块不在任何
  区域归属集里，此判据会让靶子原地不动。
* **「把 `LOAD_FAST`/`LOAD_METHOD` 直接加进白名单」**：放弃。白名单只约束 op 种类，不约束**栈**；补两个
  `LOAD_*` 会连带接受「压值后不弃」的值构建块，与 `:45534` 那条「块尾 POP_TOP ⇒ 值被丢弃，不得提升」的
  既有判据正面冲突。R33-A 用净栈效应 0 + 终止 POP_TOP 把这一维显式管住。
* **已知代价（风险上界已实测）**：新增可穿透块会在「同一 start block 存在多条 return 链」时改变 BFS 先找到
  哪一条（`successors` 是集合，弹出序不保证）。G4 的 `SAME=401/IMPROVED=1/MOVED=0/REGRESSION=0` 就是该
  风险在全语料上的实测结果，但它是**当前 402 文件**的读数，不是一条结构性保证；若日后出现同函数多链形状，
  应先加「链择优」判据而非依赖集合序。
* **线 B 的形状（`save_testds_to_json −4`）不在本轮**：它需要终块的第二次物化（发射侧），与 R31-C 的
  纯 `discard` 判据同教义反侧；Round 34 候选须读「终块无后继 + 跨臂前驱重数」，不得读内容同一性。
* 本轮未触碰的其他移交：`tick_worker_thread 268/247 j32`、`clock_worker 1275/1291 j15`、
  `match 713/689 j9`、`events 510/508 j2`、`_init_config 86/84 j1`、`decrypt_database_url 295/324 j1`，
  以及 Round 30 线 B（`r29x_01 <module> 142/138`）与 R30-B3。
