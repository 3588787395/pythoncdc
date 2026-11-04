# WYIELD_BREAK：`while + yield + 尾部 break` 生成器被反编译成普通函数（rr-v5r113，REAL46-019 闭合）

## 家族选定与真实案面

rr-v5r112 后目标 **REAL46-019**（`D:\Python\Lib\ipaddress.py`，pyc
`D:\Python\Lib\__pycache__\ipaddress.cpython-311.pyc`）。HEAD `d742d4d0`
整案 `semantic_diff.compare_case` = **DIFFERENT，唯一 R7**
`$.metadata.code.co_consts.v[19].code_sha`（`semantic_diag.json`），对应函数
`summarize_address_range`。前置只读诊断（`D:/temp/opencode/cl_layout/r112diag_a/`）
已确认是可观察的真实功能错误：原件是生成器（co_flags 0x23），
`list(summarize_address_range(IPv4Address('192.0.2.0'),
IPv4Address('192.0.2.130')))` 返回 3 个网段；产品变成普通函数（co_flags 0x3），
运行抛 `UnboundLocalError: cannot access local variable 'first_int'`
（`runtime_diff.txt`）。产品把整个 `while` 循环、`yield net`、循环前三条
初始化赋值全丢，只剩循环体首语句 + `if first_int - 1 == ip._ALL_ONES: pass`
/ `else: first_int <= last_int`（条件被渲染成裸表达式语句）。

四组最小复现（HEAD 实测，`minimal_repro.txt`）：r1（基础尾 break）/ r2（前置
初始化）/ r4（精确复刻）BYTE-EQUAL=NO；**r3（同形但无尾 break）BYTE-EQUAL=YES**，
是关键控制案。`verify_shape.txt` 证实四个原件都含 `CO_GENERATOR /
RETURN_GENERATOR / YIELD_VALUE / JUMP_BACKWARD`，缺陷不在「是否生成器」判别。

## 插桩 / 区域树 dump：对前置假设的证伪与精确定位

前置诊断的推测是「尾部 break 让 CFG 把循环头/条件块误判为 if-else 出口，
从而整个 WhileRegion 没被构造」。本轮用 `probe_tree_v113.py`（wrap
`RegionASTGenerator.generate` 捕获每层 gen，dump `region_analyzer.regions`、
`loop_analyzer.back_edges/get_all_loops`、CFG 块前驱/后继/last-instr、
`block_to_region`、各 Region 字段）、`probe_gen_v113.py`（wrap `_generate_region`
/ `_generate_loop` / `_generate_degraded_statements` 记调用链与
`generated_blocks`）、`probe_exc_v113.py`（wrap `_generate_loop` 捕获异常堆栈）
实测，**该推测被证伪**：

### ① 分析器没有丢 WhileRegion —— LoopRegion 被正确构造

`tree_r1_*.txt` / `tree_r3_*.txt`（`D:/temp/opencode/cl_layout/r113diag/`）：

```
r1 (有尾 break)                         r3 (无尾 break)
LoopRegion entry=@2 WHILE_LOOP          LoopRegion entry=@2 WHILE_LOOP
  blocks=[2,18,48,52,64,68]             blocks=[2,18,48,52]
  header=@18 cond=@2                    header=@18 cond=@2
  back_edge=@52 back_edges=[52]         back_edge=@18 back_edges=[18]
  body=[18,48,52] else=[68]             body=[18] else=[52]
  break=[48] has_break=True             break=[] has_break=False
```

`_identify_loop_regions`（`region_analyzer.py:5293`）在两种情形下都建出了
LoopRegion，且 `block_to_region` 把 @2/@18/@48/@52/@64/@68 全部登记到该
LoopRegion —— **没有块被误判为入口/出口**：@48（break 的 RETURN_VALUE）正确
登记 `break_blocks`，@68（循环头假出口）正确登记 `else_blocks`，@52 正确
登记 `back_edge_block`。分析端零缺陷。

### ② 尾部 break 真正改变的是 back_edge_block 身份，进而改变生成层派发路径

CPython 3.11 为「while + 尾部 break」把循环条件复制两份（`dis19.txt` /
CFG dump）：

```
r1:
  @2   first_int<=last_int; POP_JUMP_FORWARD_IF_FALSE->68   # 循环头条件（假→return）
  @18  ... YIELD_VALUE ... POP_JUMP_FORWARD_IF_FALSE->52     # 循环体 + break 条件（假→52）
  @48  LOAD_CONST None; RETURN_VALUE                          # break（生成器 break==return None）
  @52  first_int<=last_int; POP_JUMP_BACKWARD_IF_TRUE->18    # 尾部条件重检，跳回循环体（跳过头部）
  @64  RETURN_VALUE                                           # 尾部条件假出口
  @68  RETURN_VALUE                                           # 循环头条件假出口
r3:
  @2   first_int<=last_int; POP_JUMP_FORWARD_IF_FALSE->52
  @18  ... YIELD_VALUE ... POP_JUMP_BACKWARD_IF_TRUE->18      # 循环体块自跳（back_edge==循环体）
  @48  RETURN_VALUE ; @52 RETURN_VALUE
```

即 r1 的 `back_edge_block` 是**独立的尾部条件重检块**（@52，含
`POP_JUMP_BACKWARD_IF_TRUE` 跳回循环体 @18），循环体块 @18 以
`POP_JUMP_FORWARD_IF_FALSE` 收尾；r3 的 `back_edge_block` 就是循环体块
自己（@18，以 `POP_JUMP_BACKWARD_IF_TRUE` 自跳收尾）。这一形状差异使
`_loop_generate_body` → `_loop_dispatch_block`（`:11346`）→
`_loop_handle_header`（`:12004`）→ `_loop_process_header_instructions`
（`:12670`）在 r1 被派发去逐指令处理**含 YIELD_VALUE 的循环 header 块**，
而 r3 走另一条已闭合路径（`_is_boolop_recheck_header` 简化段，`:15881`），
不进入该处理器。

### ③ 真实根因：`_ii` 笔误 NameError → 顶层 except 吞异常 → 逐块降级

`probe_exc_v113.py` 捕获（r1/r2/r4 各 1 次，r3 = 0 次）：

```
NameError: name '_ii' is not defined
  region_ast_generator.py:7438  _generate_loop -> _loop_generate_while
  :10644 _loop_generate_while -> _loop_generate_body
  :11346 _loop_generate_body -> _loop_dispatch_block
  :12004 _loop_dispatch_block -> _loop_handle_header
  :12670 _loop_handle_header -> _loop_process_header_instructions
  :16114 _loop_process_header_instructions   <-- 抛点
```

`_loop_process_header_instructions` 的枚举循环变量是 `_instr_idx`
（`:15926` `for _instr_idx, _instr in enumerate(block.instructions)`），
但 YIELD_VALUE send 绑定前向扫描段（`:16113-16118`，FZ-020-V5R04 引入）
误用未定义的 `_ii` 取 `block.instructions[_ii + 1]` / `[_ii + 2]`。
只要 header 块含 `YIELD_VALUE` 就必然抛 `NameError`。

`generate()` 顶层主循环（`region_ast_generator.py:2278` `for region in
top_level_regions`）以 `try/except Exception`（`:2330-2337`）包裹
`self._generate_region(region)`，异常被吞后改调
`_generate_degraded_statements(prefer_blocks=region.blocks)` —— 这就是
「把条件渲染成裸表达式」的消费者：降级路径把 LoopRegion 的块逐块线性
重建，@18 的顺序语句变函数级语句、`POP_JUMP_FORWARD_IF_FALSE` 被当
`if ...: pass`、`@52` 的 `COMPARE_OP` 结果被当表达式语句发射成
`else: first_int <= last_int`，`YIELD_VALUE`/`RETURN_VALUE`(break)/
循环前初始化/整个 `while` 结构一并蒸发。`probe_gen_v113.py` 的调用链
直证：

```
r1: _generate_region(LoopRegion@2) -> _generate_loop(LoopRegion@2)
    -> _generate_degraded_statements        # 降级
r3: _generate_region(LoopRegion@2) -> _generate_loop(LoopRegion@2)
    （无降级，正常产出 ast.While）
```

结论：缺陷既不在生成器判别、也不在 LoopRegion 构造，而是**生成层一个
未定义变量笔误在特定 CFG 形状下抛异常，被通用降级兜底掩盖成「结构丢失」**。
尾部 break 是触发该形状的充分条件（把 back_edge 拆成独立条件重检块），
不是分析器的误判。

## 修复（region_ast_generator 只增不破，`[v113-WYBREAK]`，单文件 7 行纯新增）

仅改 `core/cfg/region_ast_generator.py`；`region_analyzer.py` 零改动。
补丁 `fix_patch_v5r113.diff`（`+7 / -0`）。在 `:16113` YIELD_VALUE 分支内、
既有 `_yv_nx` 扫描之前**新增一行** `_ii = _instr_idx`，把枚举索引按指令序
结构事实补绑定给原本未定义的 `_ii`，使既有 send 绑定扫描逻辑真正可执行；
既有 `_yv_nx`/`_yv_nn`/`_yv_bind`/`Expr(Yield)`/`Assign(Name,Yield)`
全部逐字不改。判据不依赖 B 编号、测试名、文件名、具体偏移量、具体变量/
函数名；`YIELD_VALUE` 的存在由既有 `if _instr.opname == 'YIELD_VALUE':`
指令序分支提供，新增行是通用索引锚点，对所有含 YIELD_VALUE 的循环
header 同判生效，非专用分支。C1 只读本块枚举索引；C2 未定义变量补齐后
既有逻辑原样执行；C3 不认领/不改写任何块或区域、不动 generated 状态。

## 验证（全实测，权威判官 `semantic_diff.compare_case`）

- **REAL46-019 整案**（`sd_v113_all.py` / `semantic_REAL46-019_v113.json`）：
  `status: EQUAL, diffs: 0 []`，完成 **DIFFERENT → EQUAL，唯一 R7 全消**。
  001 / 004 / 036 均 EQUAL, diffs=[]；031 `status + diffs 全签名`
  与基线一致 = **BASELINE-UNCHANGED**（不要求修好）。
- **复现矩阵 15 案**（`matrix_v5r113.py` / `matrix_v5r113_result.json`）：
  compile→pyc→pycdc→recompile 逐 code object 比对
  `co_code/co_exceptiontable/co_consts/co_names/co_varnames/
  co_freevars/co_cellvars/co_flags`。**15/15 BYTE-EQUAL**；9 功效案
  （r1/r2/r4 + w1..w6：不同 break 条件 / 无前置初始化 / 多 yield /
  常量 break / 属性 break / 复合循环体）A/B TEXT-DIFF 且 HEAD 全 DIFF、
  v113 全 BYTE-EQUAL；6 控制案（r3 无 break、c1 无 yield 有 break、
  c2 尾 break 换 continue、c3 普通 while、c4 while True+break、
  c5 break 在中）**A/B 全 TEXT-SAME**、v113 全 BYTE-EQUAL。
  特别地 r3（关键控制）修复前后产品逐字节不变且均 BYTE-EQUAL。
- **A/B 回归电池 214 案**（`r113_regress.py` / `r113_regress_result.txt`
  / `.json`）：169 r110 + 15 v111 + 15 v112 + 15 本轮新案。以 `git show
  d742d4d0` 文件交换，中间产物写 `D:/temp/opencode/cl_layout/r113regress/`。
  **TEXT-DIFF 恰 9 / 214，全部是本轮 9 个功效案且重编译全 BYTE-EQUAL**；
  其余 205 案逐字节 TEXT-SAME（C3 实证：非目标形态产品文本零漂移）。
  R110 169 案 TEXT 状态一致 168 / 签名一致 168（唯一差异为
  `pd8_prod` 语料替代案，与 r112 同源如实单列）；10 个用户点名登记差
  全部 **SAME-SIGNATURE**；NO-SRC 0。
- **pytest 7 套件**（`pytest_v5r113.log`）：`3 failed / 277 passed /
  2 xpassed`，3 个 failed 与基线逐名一致（2 冻结对
  `TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、
  `TestBoundaryConditions::test_BOUNDARY_02_large_function` +
  `TestProductFreshness::test_products_match_current_code` 预存在陈旧，
  其 3 个 stale 条目字节数与基线逐字相同），**零新增失败**。
  （曾误跑全量 pytest 触发 nook 目录 90 collection errors 并改写
  `testqouter/round1/bc_results.txt`，已 `git checkout --` 恢复该文件；
  正式读数取历史同款 7 文件套件。）
- **完整性**：`scripts/pyc_verify.py` SHA256 =
  `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4`；
  `tests/`、`tools/completeness/semantic_diff.py` 零改动；`core/` 仅
  `M core/cfg/region_ast_generator.py`（7 行纯新增）。
  **未提交 git**。

## 与历史族对照 / 未闭合说明

| 族 | 形态 | 断链位置 |
|---|---|---|
| `[v111-ORAND]` / `[v112-NOTBOOL]` | or/and 短路链、not 双消费 | 生成端 If/BoolOp 消费者 |
| `[v108]/[v109]/[v110]-MCSUB` | for 迭代前缀链式赋值 | for 提取器消费者 |
| **`[v113-WYBREAK]`** | **`while+yield+尾 break` 生成器** | **`_loop_process_header_instructions` 未定义变量 → 顶层 except 逐块降级** |

- 判官 R7 只看顶层 co_consts（`judge_coverage.txt`）：REAL46-019 另有 3 个
  layer-2 的 co_code 差异（address_exclude / IPv4Network.__init__ /
  IPv6Network.__init__）对判官不可见。本轮**未动判官、未按可见层凑整**：
  019 转 EQUAL 完全来自 v[19] 这一真实功能错误的修复；其余 layer-2
  差异是否顺带改善未经逐案确认，如实登记为判官覆盖盲区，不宣称闭合。
- REAL46-031 维持基线 DIFFERENT（2 diff），非本轮目标。
- 两次窄改纪律：本轮第一次窄改即达成目标且未破坏任何已闭合案，未触发
  整体回退条件；无第二次尝试。
