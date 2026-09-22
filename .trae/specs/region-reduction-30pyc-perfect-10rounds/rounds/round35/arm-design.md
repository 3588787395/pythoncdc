# Round 35 arm design — R35-A 的方向被一手测量否证，改出并落地 R35-B（重复清理尾声的非终末副本不物化）

## 一、目标池与基线（实测，非沿用）

池由 `D:/Temp/r35gate/r35/pool35.py`（归档 `logs/pool35.py`，输出 `logs/pool35.txt`）直读 Round 33 G6
回写的索引 —— Round 34 是零改动轮、未回写索引，故 `git show HEAD:pyc_index.json` 里 402 条目仍全部
`last_tested_round==33`，脚本对该项与 `Σfunction_count`／`Σmatched_functions` 均有断言 —— 并在落地字节上逐文件复测：

```
baseline(landed round34 index, HEAD 9916a82e, core sha 2d3a5d51d114da77d3d4): files 402 partial 30 sum_deficit 100 deficit1 7 deficit2 12
```

deficit-1 池 7 个文件与 Round 34 §一 同一名单（`_init_config 86/84`、`decrypt_database_url 295/324`、
`tick_worker_thread 268/247`、`events 510/508`、`clock_worker 1275/1291`、`match 713/689`、
`save_testds_to_json 314/310`），读数逐条一致（`logs/landed_d1.jsonl`，官方尺）。deficit-2 池 12 个
文件同尺读一遍（`logs/landed_d2.jsonl`）。

G2′/G3 的「改前」侧沿用 Round 34 已建的电池落地臂读数（`logs/b39_landed.jsonl` 39 条、
`logs/a104_landed.jsonl` 104 条，均 0 error；两份都是 `round34/logs/` 同名文件的字节全等副本，
逐文件 sha 已比对），全量 G4 的「改前」侧沿用 Round 34 的 `head` 臂整批读数
`logs/g4_head_r34.all.jsonl`（402 条、0 error，与 `logs/g4_r35b.all.jsonl` 路径集全等）。
沿用成立的前提本轮重新证明：
`r35c.py build` 断言 `mirr_head/core/cfg/region_ast_generator.py` 与工作区文件**字节全等**，
且 `head` 臂对靶子文件重读仍给 `14/15 [['save_testds_to_json', 314, 310, 19, 8]]`。

## 二、Round 34 交下来的候选 R35-A：一手测量证明方向相反

Round 34 §六 把 `save_testds_to_json` 的 −4 归因为「终块未发射 ⇒ 须在清理链上补一条裸
`return None` 发射臂」。本轮先在靶子上问「这四条指令到底是**少发射**还是**多发射**造成的」：

* **探针 2（`logs/probe2_variants.txt`）**：对已落盘产物做五种文本变体，逐条 `py_compile` 成
  显式 `cfile` 后用官方尺＋严格尺读：

  | 变体 | 官方尺 | 靶函数读数 |
  |---|---|---|
  | V0 现状 | 14/15 | `314/310 j19 t8` |
  | **V1 删掉 :367 那条 `return None`** | **15/15** | **MATCHED，严格尺 `defect=None lo=314 ld=314`** |
  | V2 :367 改成 `pass` | 14/15 | 310（`pass` ≠ 什么都没有） |
  | V3 :367 改成裸 `return` | 14/15 | 310 |
  | V4 删 :367 并在函数级补 `return None` | 14/15 | 312 |

* **探针 3（`logs/probe3_returns.txt`）**：该函数产物里三条 `return None`（:345/:353/:367）的八个
  删除子集中，只有**含 :367** 的子集改变读数；单删 :367 即 15/15。
* **探针 4/5（`logs/probe4_law.txt`、`logs/probe5_depth.txt`）**：源码→字节码的规律一手量出：
  handler 尾部写 `return None` 与「什么都不写、直接落出」在 handler 嵌套深度 1–2 时**编译结果
  逐条相同**，深度 ≥3 才开始差，差集恰为 `POP_EXCEPT, POP_EXCEPT, LOAD_CONST(None),
  RETURN_VALUE`；且深度 4/5 时差的**方向与本靶相反**。

结论：缺的四条不是「没发射」，是「多发射了一条 `return None` 把两份尾声合并成一条语句」⇒
R35-A 的方向整体相反，不落地。

## 三、发射点与判据候选的求取（`core/` 全程只读）

* **探针 6（`logs/probe6_site.txt`）**：靶函数里这条 `Return(None)` 的唯一发射点是
  `_generate_try` handler 循环的**通用落出臂** `region_ast_generator.py:24695`
  （`block@1970 ops=POP_EXCEPT LOAD_CONST RETURN_VALUE role=EXCEPT_STORE`），**不是** Round 34
  §五.3 记录的 `:24687-24694` RETURN-角色臂 —— 该处记录订正。同时断言「新鲜产物 == 在册产物」为
  True，即发射点确实作用于已提交的那份产物。
* **探针 7（`logs/probe7_*.jsonl`）**：按「源码形状」（handler 末语句是 `return None` 且该
  handler 是所在块的最后一条语句）在全 402 份产物上枚举站点：`files 402 with_site 61 sites 123
  terminal 93`；对 shard0 的 83 个站点做「删掉该行→重编译→严格尺」实测：**IMPROVED=1
  REGRESSED=10 SAME=72 SKIPPED=10**。⇒ 源码形状判据直接否证（1 换 10），必须找 CFG 侧的结构判据。
* **探针 8（`logs/probe8_discriminator.txt`）**：在真实发射时刻包住 `_generate_handler_body_statements`
  取结构事实。E=本块过滤后操作码是纯清理尾声 `POP_EXCEPT*[LOAD_CONST]RETURN`；D1=同 code object
  内还有另一份同形尾声。靶 `E=True n_epi=3 D1=True`，8 个 E=True 的回归站点全部 `n_epi=1 D2/D3=False`
  ⇒ `E ∧ D1` 能分开已知这批，但对**未知形状**没有说服力。
* **G0 合成形状（`test_repros/round35_epilogue_duplicate_return/`，5 件）**：先不看语料，自己造
  见证与反例。落地尺读数（`logs/g0_landed.txt`）：

  | 形状 | 落地读数 | 尾选择是否可判 | 发射站点 |
  |---|---|---|---|
  | `r35_01` 见证：三层嵌套 try/except，最内 handler 落出到函数尾 | **FAIL 1/2 严格尺 delta−4**，hunk `delete@310 [POP_EXCEPT, POP_EXCEPT, LOAD_CONST, RETURN_VALUE]` | DETERMINED(+1) | `caller=24695 blk@304 E=True n_epi=3 D1=True` |
  | `r35_02` 控制：单层 handler + 真 `return None` | PASS 2/2 | UNDERDETERMINED | `blk@98 n_epi=1 D1=False` |
  | `r35_03` 控制：try 语句后还有代码 | PASS 2/2 | DETERMINED(+2) | `blk@192 n_epi=1 D1=False` |
  | `r35_04` 控制：两层 handler，最内落出（深度 2） | PASS 2/2 | UNDERDETERMINED | `blk@198 n_epi=2 D1=True` |
  | `r35_05` 反例：三层，最内 handler 尾**真有** `return None` | PASS 2/2 | DETERMINED(−1) | `blk@294`、`blk@310` 两处均 `E=True n_epi=3 D1=True` |

  ⇒ **`E ∧ D1` 被形状否证**：`r35_05` 的两个站点与靶同满足 `E ∧ D1`，却都必须发射。见证/控制/反例
  三者齐备，G0 才有牙齿。
* **探针 9（`logs/probe9_epilogue_structures.txt`）**：记录发射瞬间各尾声块的认领状态 —— 两个 FAIL
  案例（`r35_01`、靶）的「另一份尾声」在发射时**已在 `generated_blocks` 内且从未进过该函数**，
  `r35_05` 的两个站点则各自把兄弟留给后续发射。认领史不能当判据（依赖遍历顺序），继续找 CFG 内
  自足的事实。
* **探针 10（`logs/probe10_topology.txt`）—— 决定性**：对每个纯清理尾声块读它的 `block_role` 与所属
  区域：

  | 案例 | 尾声块 → 角色 |
  |---|---|
  | `r35_01`（FAIL） | `140 TRY_BODY` ／ `304 EXCEPT_STORE`（发射点） ／ **`312 RETURN`（`Region@312`）** |
  | 靶（FAIL） | `1328 TRY_BODY` ／ `1970 EXCEPT_STORE`（发射点） ／ **`1978 RETURN`（`Region@1978`）** |
  | `r35_04`（PASS） | `140 TRY_BODY` ／ `198 EXCEPT_STORE` —— **无 RETURN 角色尾声** |
  | `r35_05`（PASS） | `140 TRY_BODY` ／ `294 EXCEPT_STORE` ／ `310 EXCEPT_STORE` —— **无 RETURN 角色尾声** |

  两个 FAIL 案例是全部四个案例里仅有的「同 code object 内还存在一份**终末**清理尾声（角色
  `RETURN`，归约器把它当函数隐式返回的出口块）」者。这正是「同一处源码级落出被编译器按异常作用域
  退出路径复制成多份」的可判信号：终末那份已被认领，把非终末那份再物化成一条 `return None` 就是对
  一个出口的双认领（原则 2），两份额本应分别编译的尾声被并成一条语句。

## 四、本轮唯一发货判据 R35-B

`region_ast_generator.py` 模块级新增 `_cleanup_epilogue_pops(block)`（纯清理尾声形状，返回
POP_EXCEPT 个数）与 `_is_duplicated_cleanup_exit_return(analyzer, block, stmts)`（三条件：语句是
唯一一条 `Return(Constant(None))`；本块是纯清理尾声；同 code object 内另有一份同形块其
`get_block_role` 为 `BlockRole.RETURN`）。`:24695` 的通用落出臂改为：仅当
`handler_body` 非空且该判据成立时**不**并入 `hbs`，`self.generated_blocks.add(hb)` 照旧。

三条判据只读结构事实：语句形态、块的操作码类别、块角色 —— 不含名字、常量值、绝对偏移、指令计数，
也不含认领史。`handler_body` 非空这一侧条件是因为空 handler 抑制后会退化成 `pass`，而 V2 实测
`pass` 与落出的编译结果不同。
