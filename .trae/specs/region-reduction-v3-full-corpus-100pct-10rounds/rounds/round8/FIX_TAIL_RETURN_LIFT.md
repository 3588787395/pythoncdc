# Round8 · FIX_TAIL_RETURN_LIFT —— while 尾随 return None lift 的白名单判定

分支 `rr-v3r01-f557fd` / 工作树 `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
判据 `scripts/pyc_verify.py`（未修改，ruler `compare_pyc` 读数写入各 JSON）
scratch `D:/Temp/rrv8/`

## 结论

**仅归档 spec 未落地**（三文件已按测得字节精确回退，8 项电池全部回到 baseline）。
lift 守卫本身**成立且可变形证明**（见下），它精确删掉了那条 ORIG 没有的
`return None`，且**没有任何 arm 塌陷为 `pass`**；但本轮实测推翻了工单前提
「该文件距 fully-OK 只差一行」——在当前树形下 `handlers.pyc` 的
`TWHThreadController._target` 还差 **and-chain arm join** 这一条独立轴，
所以 29/30 未翻。按验收规则回退。

## 1. 位点再核验（对象同一性：以字节级变形证明，非推断）

站点 `core/cfg/region_ast_generator.py` `_loop_generate_while`
（intake 行号 `:8019` / lift `:8028` / `:8251-8259`）。

三条独立变形：

| # | 变形（在真实代码上做的唯一改动） | 产物字节差 | 判定 |
|---|---|---|---|
| D1 | stub 掉 keep 分支 `:8066-8069`（`_other_return_none_blocks == 0` → `_trailing_return_none_stmts = None`） | **0 字节**（`handlersOK.py` 逐字节相同，仍 29/30） | keep 分支**不是**生产者：本 host `region.parent` 是 `IfRegion`，`:8034` 的 `region.parent is None` 门把整个 `_other_return_none_blocks` 判定短路掉了 |
| D2 | 在 lift 内新增 `elif not _non_trivial and <谓词>` → `else_stmts = []` | 仅删去第 40 行 `            return None`，其余 205 行逐字节相同 | **该 lift 是生产者**：语句由 `:8019 _generate_block_statements(_eb)` 生成、经 `:8238 _sequential_after_loop = else_stmts` 落到 `:8264 output.extend(...)` 追加在 While 之后 |
| D3 | 把 D2 的谓词收紧为「所有退出边落点都必须是纯 return-None 叶子」而**不**豁免异常边 | 产物回到 29/30 且守卫不触发 | 守卫是 **load-bearing**：不豁免异常边则整个判定失效 |

对象同一性（运行时 dump，`D:/Temp/rrv8/probe_regions.py`）：
`_loop_generate_while` 在 `<module>.TWHThreadController._target` 上只被调用一次，
region 即 `LoopRegion@90`，其 `else_blocks` **只有一个块对象**，即
`BasicBlock(off=408, instructions=[LOAD_CONST None, RETURN_VALUE], successors=∅)`；
`:8019` 生成的语句列表 100% 来自这一个对象，`_is_trailing_return_none_statement`
判其为真 → `_non_trivial` 为空。工单「三个 Return(None) 构造皆源于
`_generate_block_statements_body(408)`」与实测一致（408 是三者共同的构造入口）。

工单的 `blk@1012` 反证亦复现：`1012 preds=[412]`，**不是** `LoopRegion@90` 的成员
（不在 `region.blocks` 亦不在 `else_blocks`），它由 IfRegion 侧发射为
`else: return None`，与本 lift 无关。

## 2. sink 前驱集 before/after

`build_cfg(<TWHThreadController._target>)` 直接测得（守卫前后同一 CFG，守卫不改归属）：

```
off  390  succ=[104, 404]  pred=[212, 378]   term=POP_JUMP_BACKWARD_IF_TRUE
off  404  succ=[]           pred=[390]       ops=[LOAD_CONST None, RETURN_VALUE]
off  408  succ=[]           pred=[90]        ops=[LOAD_CONST None, RETURN_VALUE]
off  994  succ=[518, 1008]  pred=[...]
off 1008  succ=[]           pred=[994]       off 1012 succ=[] pred=[412]
off 1016  succ=[]           pred=[458]       off 1020 succ=[] pred=[504]
LoopRegion@90  blocks=[90,104,106,180,198,212,276,294,310,324,364,378,390,404,408]  else=[408]  has_trailing_return_none=True  has_break=False
```

`off404 preds=[390]` 与 `off408 preds=[90]` **各自独立**、且都由 `LoopRegion@90` 拥有
（404 被吸入 `region.blocks`、408 在 `else_blocks`）——与工单期望一致。
守卫前后这两个前驱集不变；变的是**发射**：before 产物第 40 行有 `return None`，
after 该行消失，`off404` 从未被发射（两侧都不发射）。

## 3. 落地的规则（已回退，存档备下次）

lift 由「parent 是 None 才判定」改为「parent 非 None 时按白名单证据判定」，
新增两个方法（`_loop_generate_while` 之前）：

- `_r8_b120_pure_return_none_sink(block)`：终端 opcode 为 `RETURN_VALUE`
  且其前缀指令**全部**是 `LOAD_CONST None`，或 `RETURN_CONST None`；
  噪声 op 过滤后判定，无条数上限。
- `_r8_b120_loop_tail_is_duplicated_function_return(region)`：全部只用
  白名单输入（块终端 opcode / 前驱-后继 / 异常边 / 区域归属）：
  ① `has_break` 为假（不与 B116/B119 认领面重叠，未 re-widen）；
  ② `else_blocks` 每个成员都是 `successors=∅`、`exception_successors=∅`、
     非 `exception_handler` 的纯 return-None 叶子，且
     `predecessors ≠ ∅ ∧ predecessors ⊆ region.blocks ∪ {header}`；
  ③ 循环**正常退出边**（落点 ∉ body∪{header}）的每一个落点都必须是纯
     return-None 叶子（豁免 `RERAISE` 叶子与 except 入口 —— 异常传播产物，
     本 host 的 382/384 即此类）；
  ④ 满足 ③ 的**不同** return-None 落点 ≥2 —— 单一源码 `return` 语句编译为
     一个块、两条出口边收敛到同一落点（落点数 1）；尾部复制（tail duplication）
     使两条出口边各指独立同形叶子（本 host `{404, 408}` → 2）；
  ⑤ 本 code object 图内**另**有一个不属于本循环的 return-None sink
     （本 host 1012/1016/1020）= 函数隐式尾巴，被丢弃路径由 fall-off-end 覆盖。

判定对象始终是「所在函数/区域的隐式尾部返回」，不触碰任何 arm 内部语句。

## 4. flips / True-hits / 变形 arm

| 目标 | before | after（守卫在位） | flip |
|---|---|---|---|
| `site-packages/IQCommon/logger/handlers.pyc` | 29/30 failure | **29/30 failure** | **无** |
| `realtime_event_source.pyc`（`(c)` hunk = 17 指令 arm-tail hoisting） | 12/13 | 12/13 | 无 |
| `r1_73_cand_fortry_sinkpair.pyc`（另一 owner 轴） | 1/2 | 1/2（回退后 r1_probe 实测） | 无（未强行推动） |

True-hits 与可观察效应（实测）：守卫在位时 `handlersOK.py` 与 baseline 产物的差异
**恰为一行删除**（before 第 40 行 `            return None`），其余 205 行逐字节相同、
**无任何新增行**——因此不可能引入 `pass` 塌陷；`_target` 的 and-chain arm 内容
（before 27-39 / 41-63）在 after 逐字节保持原层级与原语句，工单所述
「同一 host 上 and-chain arm 塌陷为 `if sys.version_info[1] == 11: pass`」的
失效模式**未复现**。谓词对 `LoopRegion@90` 判真并删去该行；`LoopRegion@504`
同样满足谓词（其 `else_blocks=[1020]`、落点 `{1008, 1020}`），但该块在 baseline
产物中本就未单独发射，故无可观察差异。6 项电池 261 unit / 109 pin 文件在守卫在位
期间未出现任何 unit 变动（回退后全部读数 = baseline，见 §5）。
**可观察 flips = 0**。

变形 arm（第 4 项交付只适用于落地情形；本轮未落地，故**不**向
`test_repros/round6/r6_probe_index.json` 追加 arm，索引保持 40 条路径 +
40 个同目录 `*OK.py`，实测 `missing pyc [] missing OK []`）。
上面 D1/D2/D3 三条即本票的变形判别，D2 为「删该行」、D3 为「收紧致守卫失效」，
两者互为反证。

## 5. 回退证明 + baseline 读数

回退后（`shutil.copyfile` 自 `D:/Temp/rrv8/bak/*.py.orig`）：

```
core/cfg/region_ast_generator.py  3691860 B  58769 CRLF  1 leading BOM  sha256=2e3051ed3614bd9102e8…  (intake 2e3051ed)  与 intake 逐字节相同
core/cfg/region_analyzer.py       2058547 B  32336 CRLF  1 leading BOM  sha256=38a1d5142d132fd72882…  (intake 38a1d5142d132fd7)  未改动
core/cfg/code_generator.py        299897 B   6022 CRLF   no BOM         sha256=28aba10bae133952f14e…  (intake 28aba10b)          未改动
```

8 项电池（回退后重跑，`D:/Temp/rrv8/*_lift.json`）：

| 电池 | 读数 | = baseline |
|---|---|---|
| `r1_probe` | 108/110，44 success / 2 failure | 是 |
| `r1_regress` | 34/34（17/17 success） | 是 |
| `r6_probe` | 76/85，31 success / 9 failure（40 arms） | 是 |
| `r2v3_probe` | 105/126，41/21 | 是 |
| `r3_probe` | 101/122，35/21 | 是 |
| `r4_probe` | 77/87，30/10 | 是 |
| pytest 六文件 | `2 failed, 277 passed, 2 xpassed`（同两条 `test_B01_simple_if_then_else_merge` / `test_BOUNDARY_02_large_function`） | 是 |
| import + `compileall -q core` | `IMPORT_OK` / `COMPILEALL_OK` | 是 |

单文件：`handlers.pyc` 29/30 failure、`realtime_event_source.pyc` 12/13 failure（均 baseline）。

pins（回退后 109 文件 / 2016 units，`D:/Temp/rrv8/pins_lift.json`，1976/2016，93 success / 16 failure）
逐项对齐工单：quotation **153/153**、quote_handler **79/79**、ptradeAccount **137/137**、
fly/logger **64/64**、executor 10/10、history_api 19/19、stock_position 37/37、
trading_dates_mixin 14/14、trade_live_broker 118/128、trade_info_utils 37/41、
order_api 35/37、risk_calculation/__init__ 41/43、real_quote 43/45、wizard_quant_api 55/58、
klinedata 61/64、quote 86/92、flytools 65/66、load_daily 26/27、function 70/71、
bar 84/85、finance 31/32、matcher 16/17、api_base 27/28。

marker 前缀命中（回退后，`region_ast_generator + region_analyzer + code_generator`）：
`[R2-B106`=4、`[R2-B107`=7、`[R2-B108`=5、`[R3-B115`=1、`[R3-B109`=3、
`[R4-B116 sinkexit`=4、`[R5-B100-armjoin-trueentry`=4、`[R5-B119 loopsink`=3、
`[R6-B111 armscope`=3、`[R7-B117 exitclaim`=3 —— 与工单期望全部一致。

residue greps = 0：`grep -c "R8-B120"` 对 `core/cfg/*.py` 全部为 0；
`_trailing_rn_exit_count` 未被删除（仍 2 处）——本票规则**不**supersede 它，
它在本 host 从未进入（`region.parent is not None`），删它将是替代性删除。

## 6. narrowed residual

`handlers.pyc` `<module>.TWHThreadController._target` 现差 **两条独立轴**，
不是工单所说的一条：

1. **while 尾随 return None 的 lift**（本票轴，已解决，删行正确、arm 不塌陷）；
2. **and-chain arm join**（**下一票的唯一残余轴**）：`IfRegion@412`
   （`sys.version_info[0]==3`）与其 then 内的 `IfRegion@458`
   （`==11`）未被 join 成 `elif sys.version_info[0]==3 and sys.version_info[1]==11`，
   且 `off1012(preds=[412])` / `off1016(preds=[458])` 两个尾部复制叶子被发射为
   `else: return None`。判据满足的形状 `D:/Temp/rrv7/cand_now.py`（实测 30/30）
   与 after 产物的唯一差异就是这一条 hunk（45 行 diff，全在 40-62 区间）。

即：**先修 ②（arm join + 尾部复制叶子吸收），② 落地时本票 ① 的删行是其必要条件**
（② 单独做而保留 `return None` 时该行仍在 diff 中）。两票合并后 29/30 → 30/30。
`realtime_event_source.pyc` 的 `(c)` hunk（17 指令 run 被搬到函数尾，orig idx959:976）
与本轴同 neighbourhood 但不同生产者：其落点不是纯 return-None 叶子，本票谓词
按其定义正确地拒绝（12/13 不变）。
