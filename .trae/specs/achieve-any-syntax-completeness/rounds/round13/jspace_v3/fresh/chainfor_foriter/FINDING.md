# CHAINFOR：for 迭代前缀提取器链式赋值整链归约修复（rr-v5r108，Task 34，REAL46-019 叶 1 闭合）

## 家族选定与根因

rr-v5r107 剩余登记：pe8（需派发表先行）、na5（while 重构域）、46 sweep 13
DIFFERENT。本轮盘点选 **REAL46-019（ipaddress.cpython-311，stdlib）叶 1**——
`_find_address_range` 的 `first = last = next(it)` 产品只渲染 `first =
next(it)`（第二目标蒸发，co_varnames 槽序 (addresses, it, first, ip, last)
vs (addresses, it, first, last, ip) 错位）。

根因（原件/产品并排 + 逐消费者插桩 BSS/SCAN 栈回溯 + ca1→ca3 梯度复现）：

①**疾病定位**：探针实证丢失调用链 `_loop_generate_for` (7758) →
`_loop_extract_for_iter_pre_stmts` (11638) → `_build_store_statement`（ops =
[LOAD_GLOBAL next, LOAD_FAST it, PRECALL, CALL, COPY, STORE_FAST first]，targets
=['first']）。`_scan_prefix_chain_assign`（[B85] 链归约）在该路径**从未被调
用**（[SCAN] 钩子静默）——[B85] 只挂在装配层 3 站点（96/42101/69092/70495），
for 迭代前缀提取器是第 5 个 STORE 消费者却未接。

②**丢失机制**：链字节码 `<值> COPY 1 STORE t1 STORE t2`。提取器 STORE 分支
三段：walrus 判据（COPY 前驱 + 后继非 STORE——链形后继是 STORE → 放行）→
[B223] 连续 STORE 段守卫②**显式排除值段含 COPY**（「链式赋值（COPY 1）
……另路已在上方 UNPACK_SEQUENCE 分支整条消费」——但链归约的「另路」在本
提取器根本不存在）→ 兜底 `_build_store_statement(_buf)` 只取单目标 first，
`_buf` 清空后 STORE last 落空被静默丢弃。

③**ca4 形态（3 目标链 `a = b = c = next(it)`）**：字节码 `[COPY STORE a
COPY STORE b STORE c]`——STORE a 的紧邻后继是 **COPY 1** 而非 STORE，walrus
判据误分（产品 `b = (a := next(it))`，c 蒸发）。判据注释明言要区分「COPY+
多 STORE 链」但漏了中间 COPY。

④**ca3 形态（REAL46-019 精确形，链为块首语句）**：生成器前导 `GEN_START`+
`POP_TOP@2` 落入 `_buf` 头部——[B85] 扫描值切片语句终结符守卫（POP_TOP 在
列）拒绝整链归约。ca2 因链前还有 `it = iter(addresses)` 语句吸收了前导
POP_TOP 而幸免；ca3/REAL46-019 链是块首语句，POP_TOP 骑行进链缓冲。旧路径
`_build_store_statement` 对前导 POP_TOP 静默忽略（产品无对应语句）。

## 修复（region_ast_generator 只增不破，[v108-CHAINFOR]，+50 行单文件）

`_loop_extract_for_iter_pre_stmts` 三处：

- **循环头吸收窗**（`_v108_absorb_end` 绝对索引）：链整链归属单一 Assign
  后，窗内指令（含链中段 COPY/STORE——中段 COPY 不触达仅在 STORE 分支递减
  的 `_unpack_skip_remaining` 计数器）按索引跳过，防泄漏进 `_buf`/`_remaining`。
- **STORE 分支链归约**（walrus 分支之后、[B223] 之前）：判据（[B85] 同源字
  节码事实，与 walrus 互斥）＝`_buf` 以 COPY(arg=COPY_STACK_TOP) 收尾（值复
  制边界）；归约＝`_scan_prefix_chain_assign(list(instrs), _idx, _buf)` 整链
  归约为单 Assign（targets 保序，`is_chain_assign=True`，发射端
  `_generate_assign` 以 `a = b = c` 渲染），吸收窗 = [_idx+1, chain_end)。
  前导 POP_TOP 剥离：仅剥 `_buf` **头部** POP_TOP 后送扫描（生成器前导
  discarded 值，非链值组成部分，旧路径同样静默忽略）；中段 POP_TOP 仍由值
  切片终结符守卫拒绝（防吞语句边界）。
- **walrus 后继判别补 COPY 1**：后继集 = STORE（末目标）∪ COPY 1（中间目
  标复制）；walrus 后继 = 两者之外（GET_ITER/调用续接等值消费）。
- **C3**：扫描返回 None（值段含语句终结 opcode/目标<2/重建失败）逐位落回
  既有路径；walrus 形（后继非 STORE 非 COPY 1）、[B223] 元组形（值段无
  COPY）、无链形 STORE 全部走原分支逐位不变。

## 验证（全实测）

- **复现矩阵 16 案**：功效案 9——ca2（链+iter 赋值前句，前导 POP_TOP 被前
  句吸收）/ca3（链块首+前导 POP_TOP，REAL46-019 精确形）/ca4（3 目标链+
  walrus 后继 COPY 误判）/ca5（常量值链 `first = last = None`）/ca7（链+独
  立迭代器 xs）/ca8（非生成器+return）/ca9（类体方法）/ca10（模块级）/
  ca14（链+前置语句+独立迭代器）——v107 TEXT-DIFF→v108 重编译全 code
  object 逐字段 **BYTE-EQUAL**；控制案 ca1（普通函数链，[B85] 既有路径）/
  ca11（B223 元组赋值）/ca12（walrus）零变化——C3。
- **未领姊妹形态 3 案（v107==v108 逐字节同，A/B 直证，如实登记）**：ca6
  （boolop 值链 `flag or next(it)`——值语境短路链域，r105 姊妹）/ca13（前导
  discarded-name Expr 语句 POP_TOP 中段——语句终结检测域）/ca15（三元条件
  值链——三元域）。
- **REAL46-019（ipaddress.cpython-311.pyc sha a40c6e99）**：产品文本
  `first = last = next(it)` 恢复；字段级真实差异集 `_find_address_range`
  **移出**（仅剩 co_firstlineno 嵌套布局噪声类别）；semantic_diff 单案复跑
  R7 维 **2→1**（剩余唯一 R7 = co_consts.v[19] = summarize_address_range
  ——已登记 while-yield loop collapse 域，维持 DIFFERENT 在案）；剩余字段级
  真实差异 4 函数（IPv4/IPv6Network.__init__、address_exclude、
  summarize_address_range）经 AST 反查均**无链式赋值**，域界定干净。
- **REAL46-004（enum.cpython-311.pyc sha 60e3ca30）**：单案权威
  semantic_diff 复跑 **EQUAL（diffs=[]）**。
- 回归电池 **145 案**（r108_regress.py 双文件交换 A/B：v5r107 HEAD=026a740c
  vs v108 同输入 pyc 反编译产物逐字节比对 + 逐顶层函数重编译比对）**9 功效
  案 TEXT-DIFF/BYTE-EQUAL + 136 TEXT-SAME**（23 原案 + 全部控制案；既有登记
  差维持与 r107 逐字节同签名：w28_shapes w2/w3、na5、pd8_prod、pe8、
  pe8_target；未领姊妹形态 ca6/ca13/ca15 与 v107 产物逐字节同）。
- pytest 7 套件 **冻结对一致 2 failed**（TestDominanceFrontierIf::test_B01
  _simple_if_then_else_merge、TestBoundaryConditions::test_BOUNDARY_02
  _large_function）/ 277 passed / 2 xpassed；第 3 failed = product_freshness
  在位产物预存在陈旧（v107 轮已 A/B 实证非本轮引入）；比较器 pyc_verify.py
  SHA256 FE1902A9 冻结一致、tests/ 与 scripts/ 零改动。
- 全量 1556 闸门（v5r108 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376=376，对 v107 **1556 案 c4 verdict 逐案零变化**（连续第八轮零抖
  动）；分片汇总 shard0 367/152、shard1 406/113、shard2 407/111（与基线逐分
  片一致）。REAL46 sweep（v5r108 对 v5r107）**46 案 c4 verdict 逐案零变化 0
  回归**：13 DIFFERENT/15 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记
  REAL46-045）——REAL46-019 维持 DIFFERENT（剩余病灶在案，本轮叶 1 闭合体
  现为其 R7 维 2→1 与字段级差异集移出）、REAL46-004 维持 EQUAL。

## 诚实边界

- REAL46-019 叶 1 闭合（`_find_address_range` 字段级+判定器 R7 维双双移
  出）；整案维持 DIFFERENT——剩余病灶（summarize_address_range while-yield
  loop collapse、address_exclude、IPv4/IPv6Network.__init__）域不同、维持
  登记。
- pe8（while-1 重构族，需派发表先行）、na5（while 条件嵌套 or 尾，loop 重
  构域）维持登记；46 sweep 其余 DIFFERENT/ERROR 在案。
- 未领姊妹形态（ca6 boolop 值链/ca13 前导丢弃名语句/ca15 三元条件值链）与
  v107 逐字节同，未在本轮家族内、如实留待后续轮。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r108.diff` | [v108-CHAINFOR] 完整 diff（+50 行单文件） |
| `ca1-ca15.py` | 变体矩阵（9 功效 + 3 控制 + 3 未领姊妹形态） |
| `pb_run.py` | compile→decompile→全 code object 字段级比对驱动 |
| `probe_ca2b.py`/`probe_ca4.py` | BSS/SCAN 逐消费者插桩（根因定位） |
| `ip_prod_v108.py`/`ip_fielddiff_v108.txt` | ipaddress 产品与字段级差异集 |
| `sd_r108_004.py`/`semantic_REAL46-004_v108.json` | enum 案权威判定（EQUAL） |
| `sd_r108_019.py`/`semantic_REAL46-019_v108.json` | ipaddress 案判定（R7 2→1） |
| `r108_regress.py`/`r108_regress_result.txt` | 145 案回归电池驱动与结果 |
| `semantic_46_v5r108.json`（+report） | REAL46 sweep v5r108 实测（46 案逐案零变化） |
| `enum_fielddiff.py` | 字段级 code object 比对器 |
