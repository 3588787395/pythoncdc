# Round 35 OUTCOME —— 落地 R35-B：重复清理尾声的非终末副本不得物化为 `return None`

## 一、结论

* Round 34 交下来的候选 **R35-A 被一手测量否证**：靶函数的 −4 不是「终块没发射」，而是
  「多发射了一条 handler 尾 `return None`，把编译器按异常作用域退出路径复制的两份清理尾声并成了
  一条语句」。删掉那条语句（V1）即 15/15、严格尺等长；把它换成 `pass` 或裸 `return`（V2/V3）读数
  不变。详见 `arm-design.md` §二。
* 本轮唯一发货判据 **R35-B**（`arm-design.md` §四）：`:24695` 的 handler 通用落出臂，当且仅当
  ①`hbs` 是唯一一条 `Return(Constant(None))`；②本块过滤后操作码是纯清理尾声
  `POP_EXCEPT*[LOAD_CONST]RETURN`；③同 code object 内另有一份同形块其 `block_role` 为
  `BlockRole.RETURN`（函数终末出口，已由隐式返回认领）；且 ④`handler_body` 非空
  （空 handler 抑制后只剩 `pass`，V2 实测 `pass` ≠ 落出）时，**不**并入该语句，认领照旧。
* 靶 `IQEngine/plugins/plugin_system_risk_calculation/function.pyc`：**14/15 → 15/15**，
  唯一缺陷函数 `save_testds_to_json` 由 `314/310 j19 t8` 变为逐条全等。
* 全量 A/B（G4，发货权威）：`SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0` —— 只动了一个文件，
  且是往好的方向。索引由 G6 拉回实测。

## 二、门禁（严格按序，逐条实测）

| 门禁 | 判据 | 实测 |
|---|---|---|
| **G0** 合成见证/控制/反例（5 件，`test_repros/round35_epilogue_duplicate_return/`） | 见证须在落地字节上 FAIL，控制与反例须 PASS；候选臂须把见证转 PASS 且不动其余 | 落地/`head` 臂：`r35_01` FAIL `1/2 314→310 delta-4`（hunk `delete@310 [POP_EXCEPT, POP_EXCEPT, LOAD_CONST, RETURN_VALUE]`），`02/03/04/05` 全 PASS。候选臂：`TALLY SAME=4 IMPROVED=1 REGRESSION=0`，五件全 2/2 |
| **G1** deficit-1 池（7 件，官方尺） | 靶翻转，其余 6 件逐条 SAME（sha-first） | `TALLY SAME=6 IMPROVED=1 REGRESSION=0 MOVED=0`；靶 `14/15 -> 15/15` |
| **G2′** 上一轮合成复现电池（39 件） | 候选 vs 落地逐条 SAME=39 | `TALLY SAME=39 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（28 条全匹配不变） |
| **G3** 承重锚点电池（104 件） | 候选 vs 落地逐条 SAME=104 | `TALLY SAME=104 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（74 条全匹配不变） |
| **G4** 全 402 A/B（sha-first，唯一发货权威） | 无 REGRESSION、无 ERR，且 IMPROVED≥1 | `SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`；整文件全匹配 372 → 373 |
| **G4′** 严格尺读每一个变更产物 | 变更文件在严格尺下 sigma-defect 与 Σ\|Δ\| 都不得升高 | 靶：`head` 臂 `strict clean 14/15 sigma-defect=1 sum_abs_delta=4` → 候选臂 `strict clean 15/15 sigma-defect=0 sum_abs_delta=0` |
| **G5** `single` 靶子 | 官方尺 15/15，且在册产物 == 候选臂产物 | `total_functions 15 matched 15 rate=100.00%`；`tracked product == cand-arm product: True`（30128 字节）；产物 diff 恰为 1 行删除（删掉虚构的 :367 `return None`） |
| **G6** `batch --index pyc_index.json --all --round 35` | 402/402 复验、索引回写 | 402 条读完、`failed_pyc 0`；逐条目差异 = 401 条只改 `last_tested_round`，1 条（靶）改 `partial→ok / 14→15 / rate 1.0`；除此之外无状态翻转 |
| **G7** `stats` | 本轮只发布这一行 | 见 §五 |

零副作用面：`git status --porcelain` 在 G6 之后只剩 3 个在册文件被改（`core/cfg/region_ast_generator.py`、
靶产物、`pyc_index.json`）——402 份产物里只有靶那一份字节变化，与 G4 的 `SAME=401` 一致。

## 三、落地内容与字节身份

* 补丁经镜像臂测量后由 `land35.py` 重放：`spec_r35b.json` 两处编辑（模块级新增
  `_CLEANUP_EPILOGUE_NOISE`／`_CLEANUP_EPILOGUE_TERMINAL_OPS`＋`_cleanup_epilogue_pops()`＋
  `_is_duplicated_cleanup_exit_return()`，站点 `:24695` 加 4 行守卫），插入 57 行，
  `replay == measured mirror bytes` 断言通过 ⇒ 落地的就是量过的那份。
* 核身份：`pre-land HEAD blob 正规化 sha256[:20]=473193456cc137c62217`（2932944 字节）→
  `post-land 原始 sha256[:20]=92c8c2aabdcd37b9f32b`、正规化 `ed005632e450f81da09c`，
  2984322 字节，CRLF 48418 = LF 48418（行尾仍统一），UTF-8 BOM 保留，`compile()` 通过。
  见 `logs/core_identity35.txt`。

## 四、方法论收获

1. **「产物里多一行」与「字节少四条」可以是同一件事**：R35-A 把「严格尺 hunk 是 delete」直接读成
   「发射侧缺一条语句」，方向就反了。文本变体 A/B（探针 2/3：删一行 / 换成 `pass` / 换成裸
   `return` / 在别处补一行）成本是一次 `py_compile`，却把因果钉死——本轮所有后续工作都建立在
   「少发射一条语句」而不是「多发射一条语句」上。
2. **源码形状判据必须先在全语料上枚举再否决**（探针 7：1 改善 / 10 回归 / 72 同 / 10 不可删），
   18 秒的 AST 扫描省下了一次 402 文件 A/B；而它的替代品必须由 CFG 侧结构事实承担。
3. **反例形状要自己造**：`E ∧ D1`（本块是纯清理尾声 ∧ 同 code object 有另一份）在已知 11 个站点上
   分得很干净，但 `r35_05`（三层嵌套、最内 handler 尾**真有** `return None`，两份尾声都必须发射）
   一造出来它就失效。真正把两个 FAIL 案例与全部 PASS 案例分开的是**块角色**：失败案例各有一份
   `role=RETURN` 的终末尾声，四个 PASS 案例一份也没有。
4. **发射点归属要一手量**：Round 34 §五.3 把这条 `Return(None)` 记到 `:24687-24694`（RETURN-角色臂），
   探针 6 的调用栈证明它来自 `:24695` 通用落出臂、块角色是 `EXCEPT_STORE`。记错臂会导致守卫加在
   永远不会命中的分支上。
5. **认领史不能当判据**：探针 9 显示「另一份尾声在发射瞬间是否已被认领」也恰好分开这批案例，但它
   依赖区域遍历顺序；探针 10 的角色事实是 code object 的静态性质，才够格作同层判据。

## 五、本轮索引读数（`stats` 原样）

```
total_pyc:             402
verified_pyc:          402
ok_pyc:                373
partial_pyc:           29
failed_pyc:            0
total_functions:       5746
matched_functions:     5647
cumulative_match_rate: 98.28%
```

## 六、移交 Round 36

1. **本族残余**：`r35_01` 与靶都是「非终末副本恰为一份」的形状；同族更深（4–5 层）的落出方向相反
   （探针 5 的深度阶梯），本轮判据在更深嵌套上是否仍只抑制该抑制的那一份，只有真实样本能回答——
   deficit-2 池 12 个文件里若再有 `POP_EXCEPT×k` 族 hunk，应先用探针 10 的角色表读一遍。
2. **deficit-1 池剩 6 个**（本轮逐条未动）：`_init_config 86/84`（R16 J1 在册反例，受保护）、
   `decrypt_database_url 295/324`（+29 过量发射，#43）、`tick_worker_thread 268/247`、
   `events 510/508`（Round 34 线 B 已判为字节码欠定，勿再从 else 归属进攻）、
   `clock_worker 1275/1291`（R22/R23 移交 D2 过量发射 / D3 同形换位）、`match 713/689`。
3. **#61 合成见证 `r29x_01 <module> 142/138`** 仍未收口。
4. 电池增量：G2′ 的 39 件应加入本轮 5 件形状（尤其 `r35_05` 反例与 `r35_01` 见证）；G3 的 104 件应
   加入靶 `plugin_system_risk_calculation/function.pyc`（现已全匹配，作承重锚）。
