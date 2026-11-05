# FINDING — rr-v5r119 [v119-TRYTOP]：循环体顶 try 错挂循环体内 IfRegion（虚假区间覆盖选父）→ try 漏渲染兜底错装、handler return 降级 pass（REAL46-008 /prepare_predicate 病形闭合）

## 0. 结论速览

- REAL46-008（xml/etree/ElementPath）`/prepare_predicate`（原判 co_code
  1204 vs 1214）病形定性为**新窄族**（非 while-1 大族）：`while 1:` 循环体
  顶的 `try: token = next() / except StopIteration: return` 被反编译器搬到
  **循环底**且 handler `return` 降级为 `pass`——**真实 R1 语义缺陷**：
  StopIteration 路径原函数正常返回，产品改为继续循环→对陈旧 token 重复
  处理→死循环；`('', '')` continue 路径同理（原 continue 重入循环顶 try
  取新 token，产品 continue 跳过底部 try 死循环）。
- 本轮修复后：最小复现 p1 **重编译全字段 BYTE-EQUAL**；
  `/prepare_predicate` 结构形状改对（try 回循环顶、return 恢复），剩余
  14 字节为另一窄族残余（§5 登记）；判官维持 DIFFERENT 2 R7
  （prepare_predicate 字节残余 + iterfind while-1 大族未动）。

## 1. 根因（区域树/AST 对照 + add_child 插桩定位 `_build_region_hierarchy`）

### 1.1 差异面（p1 = 精确最小复现）

原件：`while 1:` 循环头顶 `try: token = next() except StopIteration: return`
（块序 [NOP@2 行锚, NOP@4 try 头, try 体, except 块 POP_EXCEPT+LOAD_CONST
None+RETURN_VALUE, if ']' break, if ('','') continue, 体, 回边]）。
产品：try 整体出现在循环体**末尾**且 handler 为 `pass`。

### 1.2 机制链（三层叠加）

- **错挂（根因）**：`_build_region_hierarchy` 的
  `_use_if_tiebreaker`（child=TryExceptRegion 且候选含 IfRegion 时**只在
  If 候选**中选父，key=(优先级, −区间跨度)）——IfRegion@88（`token ==
  ('','')` 测试）的 blocks 含循环头行锚 NOP 块@2（continue 回边目标被
  then_blocks 吸收），使其块偏移区间 [2,142] 罩住 try 区间 [4,56] 而成为
  候选；tiebreaker 无视 LoopRegion 候选把 try@6 挂为 IfRegion@88 之子
  （add_child 插桩实证 `_build_region_hierarchy:36933`）。
- **漏渲染**：IfRegion@88 的 then_blocks=[continue,NOP]、else_blocks=
  [append 链] 均不含 try 入口 → 父不渲染该子；循环体走查（body_blocks 序
  [2,4,6,26,62,…] try 靠前）因「父引用子入口」原则跳过已属他区域入口的
  块 6 → try 块全部漏出。
- **兜底错装**：漏出块（try 体 6/26 + handler 28/46/48/54/56）在末尾扫尾
  作为散块生成，被装配进最深 orelse（AST 实证 While.body=[If] 单链、Try
  嵌于 If@88 orelse 链底），handler 的显式 `return`（POP_EXCEPT+
  LOAD_CONST None+RETURN_VALUE，行锚 236 落在 POP_EXCEPT 上）被降级
  为 `pass`。
- 判别要点：try 入口**不在** If 候选的任何臂体集（then/else/elif 体/末
  else）——区间覆盖是虚假包含；try 入口**确在** LoopRegion 候选
  body_blocks 内（块序第 2 位）。

### 1.3 同域排除

- 共享入口 peer 形（get_opt_objects 族：IfRegion 与 TryExceptRegion 同
  entry，try 是 if 的体外壳）——entry 不在臂体集但 peer 关系成立，维持
  If 优先（守卫显式排除，C3 案零漂移实证）。
- for 体顶 try / 条件 while 体顶 try / 无循环 try / if 臂内 try——HEAD
  本已正确（C1/C2/C4/C5 零漂移）。
- E2/E3 简化变体（无 break+continue if 链）HEAD 本已正确——病形需要
  break/continue 的 if 链产生带 NOP 块的 IfRegion 候选（虚假区间覆盖的
  来源）。

## 2. 修复（region_analyzer.py 只增不破，[v119-TRYTOP] 单点 +48/−4）

`_build_region_hierarchy` 的 `_use_if_tiebreaker` 分支增加臂体包含守卫：
If 候选须**真实包含 try 入口于臂体集**（then/else/elif 体/末 else）方可
作父；共享入口 peer（`_ic.entry is child.entry`）显式维持 If 优先；无任何
If 臂体包含且入口确在 Loop 候选 body_blocks 内时，父取 LoopRegion（循环
顶 try 的自然归属，父引用子入口原则）。不命中维持原路径逐字节不变
（7 控制案零漂移实证）。

## 3. 验证（全实测）

### 3.1 变体矩阵（`matrix_v5r119.py` 8 案，A/B HEAD `2df7f6ba` vs v119）

| 案 | 形 | HEAD | v119 | 判定 |
|---|---|---|---|---|
| E1_trytop_while1 | while1 体顶 try + except return + if-break/continue 链（p1 精确形） | TEXT-DIFF（try 搬底 + return→pass） | 重编译 BYTE-EQUAL | PASS |
| C6/E2_trytop_valret | 同形简化（无 break/continue，显式 return None） | — | 逐字节同 + BYTE-EQUAL | PASS（HEAD 本已正确） |
| C7/E3_trytop_handler_stmts | handler 多语句 + return | — | 逐字节同 + BYTE-EQUAL | PASS（HEAD 本已正确） |
| C1_try_noloop | 无循环 try | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C2_try_in_if_arm | if 臂内 try（合法 If 父形） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C3_shared_entry_peer | 共享入口 peer（get_opt_objects 族 + for 壳） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C4_try_in_for_top | for 体顶 try | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C5_try_in_while_cond | 条件 while 体顶 try | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |

### 3.2 REAL46-008（ElementPath）

- `/prepare_predicate`：结构形状改对（try 回循环顶、`except StopIteration:
  return None` 恢复——p1 重编译 4 code objects 全字段 BYTE-EQUAL 直证）；
  重编译残余 1204 vs 1218（+14 字节，`signature.append(token[0] or '-')`
  值域 boolop 调用实参渲染的 inline-cache/JUMP_IF_TRUE_OR_POP 布局差），
  exctab 同步残余——**另族登记 §5**。
- `/iterfind`（−102 字节，while-1 体丢失大族）本轮未动、零漂移。
- 权威判官：DIFFERENT 2 R7（`semantic_REAL46-008_v119.json`，与 v118 持平
  ——R7 按 code_sha 计，本轮闭合的是病形语义而非字节）。

### 3.3 回归

- A/B 回归电池（r119_regress.py：r110 169 + v111 15 + v112 15 + v113 15 +
  v115 9 + v116 4 + v117 6 + v118 7 + 本轮 8 = **248 案**，独立 TMP
  `r119regress/` 干净重跑；交换文件 = `core/cfg/region_analyzer.py`）：
  **TEXT-DIFF 1 / 248 恰为本轮唯一功效案（E1，重编译 BYTE-EQUAL）**；
  其余 247 案 TEXT-SAME；R110 案 168/169 一致（唯一差 mc1 = r110 轮功效
  案两侧同持修复正常归一，TEXT-SAME+BYTE-EQUAL）；既有登记差 10 案
  **ALL SAME-SIGNATURE**；NO-SRC 0。
  （过程登记：电池漏挂 andnot_yieldarm 路径致 v118 案源导入失败、组循环
  替换串未命中致 V119 组缺位首跑 240 案——均修正后干净重跑，本节数字为
  修正后实测。）
- pytest 7 套件：**3 failed / 277 passed / 2 xpassed**——与基线逐项一致
  （2 冻结对 + product_freshness 预存在陈旧），零新增失败；4 个 stale
  条目（strategy_universe 40 行 3787/3712、load_daily 26229/26134、
  matcher 167 行 13299/13375、trade_info_utils 1010 行 61506/61753）
  与 r118 读数逐字相同——**v119 零漂移**。
- 比较器 pyc_verify.py FE1902A9 / semantic_diff.py DBCB1E24 冻结一致、
  tests/ 零改动；唯一已跟踪改动 `M core/cfg/region_analyzer.py`
  （+48/−4，标记 `[v119-TRYTOP]`）。

## 4. 验收口径

小测试收口（全量闸门按用户政策只留给大改动）。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选，未修）

- `/prepare_predicate` 字节残余（+14：`token[0] or '-'` 值域 boolop 调用
  实参 inline-cache/JUMP_IF_TRUE_OR_POP 布局差 + exctab）。
- `/iterfind`（−102 字节）= while-1 体丢失大族（pe8 同域，r105 诊断在案
  「自然出口块前向吸收 → _is_while_true 判 True → site9k while-1 发射；
  需派发表先行」）；v118 E2 残余（while 底部 `tok = next(it, None)` 重检链
  丢失）同域。
- E6 相邻 NOP 对；46 sweep 其余 DIFFERENT（REAL46-011/012/013/014/015/016，
  022/046 已定性观察层 R5）/17 ERROR。

## 6. 证据文件

`fix_patch_v5r119.diff`、`matrix_v5r119.py`、`r119_regress.py+result`、
`semantic_REAL46-008_v119.json`、`ElementPath_product_v119.py`、
`repro_p1.py`、本文件；探针：`D:/temp/opencode/cl_layout/r119diag/`
（probe_p1 区域树、probe_disp 分发序、probe_bstmts 体语句序、probe_ast
AST 树、probe_parent add_child 插桩）、`D:/temp/opencode/cl_layout/r119matrix/`。
不入库。
