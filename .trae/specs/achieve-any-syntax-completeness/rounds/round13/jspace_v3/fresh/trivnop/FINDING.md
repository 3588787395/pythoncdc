# FINDING — rr-v5r129 [v129-TRIVNOP]：trivial 返回体 NOP 语句位还原（E6 相邻 NOP 对族闭合，登记定性修正）

## 0. 结论速览

- E6 相邻 NOP 对（§54.5 登记首选，Task 46 曾定性「守卫同形不可分，语义等
  价低价值」）本轮**评估升级为修复**：实测缺陷面与登记定性不同——丢弃点
  不是 `_rag_is_orphan_nop_statement` 的相邻守卫，而是
  `_generate_block_statements_body` 的 **pass_return 平凡块快路径**
  （`has_nop and has_return` 全平凡 op 时主循环无条件
  `if NOP: continue`）。函数体 docstring 后随裸字符串/`pass`/`while
  False:` 折叠的平凡返回体（co_code 含行锚 NOP）重编译缺 NOP——E1 实测
  8→6、三连 10→6（**R2 级字节差**；语义惰性=行锚 NOP 不执行，但字节不
  等）。
- [v129-TRIVNOP] 单文件 +27/−0（只增不破）：快路径逐 NOP 分类——try 行
  标记/结构再生（V-T/V-S/V-B/V-L）/异常表锚定 NOP 照旧跳过（结构重编译
  自然再生）；假值残差常量（x01 残差队列）发射 `While(C, pass)` 同保
  NOP 与常量表布局；其余发射裸 pass 占位（任意语句位置恰 1 NOP、零常
  量、零跳转，x01 C2 实测）。
- 全额闸门：矩阵 10 案 **ALL PASS**（4 功效 HEAD TEXT-DIFF→v129 BYTE-
  EQUAL + 6 控制零漂移）；电池 267 案 A/B 见 §3；pytest 7 套件见 §3。

## 1. 根因（三层追踪 + 登记定性修正）

- 登记史：r114 E6 案（模块级两条相邻裸字符串）实测 v114==HEAD 零漂移、
  归「[Round 33] 相邻 NOP 守卫排除域」未领边界；Task 46 定性低价值。
- 本轮实测矩阵探针：模块级/类体形**均已绿**（E2 类体
  `__doc__='doc1'`+`""""""` 占位机制、E3 模块级、TSA 类体相邻对
  `while 0: pass`×2 Nook 机制承接）；**函数体形破**——
  `def f(): "a"; "b"; return 1` 产物只剩 docstring（w co_code 8→6）。
- 判定链插桩：块首 NOP 的 `_rag_is_orphan_nop_statement`（prev 跳过
  RESUME 后为 None→块首排除）、`_is_orphan_boundary_nop`（after 非空
  非 return-none）、`_is_protected_statement_nop`、`_nop_structural_veto`
  全 False，`_is_unaccounted_folded_head_nop` **True**——但谓词零调用：
  块语句生成被 **pass_return 快路径**（68016 区域）截胡，NOP 在其主循
  环被无条件丢弃，从未到达通用 walk 的 x01 级联。
- E4/E5 反向实证（归控制）：末位 `pass`/末位裸串被 CPython 编译器整体
  消除（原始 bytecode 无 NOP，6 字节）——两侧平凡等价，非本族。
- E6 形细化：`while False: pass` 折叠＝**单 NOP＋残留假值常量**
  （consts ('d', False, 1)）——仅还原 NOP 不够，须 `While(False, pass)`
  双还原（x01 假值行头既有语义：假值行头＝单 NOP＋残留假值常量）。

## 2. 修复（[v129-TRIVNOP]，只增不破，单文件 +27/−0）

`pass_return` 快路径主循环 NOP 分支改逐 NOP 分类：

1. **跳过类**（结构再生，语义同源 x01 归属互斥）：`_nop_is_try_line_marker`
   / `_nop_structural_veto`（V-T/V-S/V-B/V-L）/`_is_protected_statement_nop`
   → 照旧不发射。
2. **假值残差**（`_pop_head_const()` 队列=x01 残差常量单一事实源，弹出
   0/False）→ `While(C, [Pass])`（重编译还原 NOP＋常量表布局）。
3. **其余**（真值/空队列）→ `_folded_statement_placeholder()`（裸
   pass＝任意语句位置恰 1 NOP、零常量、零跳转）。

指令序保持：占位按原偏移序落位 Return 之前；`while True: break` 特例
（len==3 提前返回）不触碰；类体/模块级路径不经过本快路径、零影响。

## 3. 验证（全实测）

- **矩阵 10 案**（matrix_v5r129.py，A/B 单文件 RAG 交换 HEAD df2729e6
  vs v129）：E1 doc+裸串/E2 三连/E3 pass+return **HEAD TEXT-DIFF→
  v129 BYTE-EQUAL PASS**；E6 while-False 折叠 **双还原 BYTE-EQUAL
  PASS**；E4/E5（编译器消除形，HEAD 本已等价）+C1 类体+C2 模块级+C3
  单 docstring+C4 try 行标记全零漂移。**MATRIX: ALL PASS**。
- **A/B 电池 267 案**（r129_regress.py，单文件 RAG 交换 HEAD df2729e6
  vs v129）：**TEXT-DIFF 0/267**（全语料零触发=外科性）；R110 168/169
  一致（mc1 正常归一）；登记差 10 案 **ALL SAME-SIGNATURE**（含
  SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项一致，
  余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 sweep 46 案 A/B**（v129/HEAD 双侧新鲜产物 --source）：46 案
  读数**逐字节一致**（双侧结果文件 diff-exit=0 实证）——TRIVNOP 修复在
  46 真实包零触发；ElementPath 维持 **39/39 100%**。

## 4. 验收口径

实测读数同 §3：电池 267 案零漂移（快路径改写在 267 语料零触发——语料
无平凡返回体含 NOP 形，闭合面=合成域+矩阵 4 功效案）；REAL46 sweep 46
案逐字节一致、ElementPath 39/39 100% 维持。不宣称 G1/G2c/G3/G4/G6 通
过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. REAL46-011~016 DIFFERENT 族/4 compile_error；pytest 余 2 失败=冻结对
   （B01/B02，登记态）；E6 若电池揭示真值残差形残差则另登记。

## 6. 证据文件

`fix_patch_v5r129.diff`（+27 单文件）、`matrix_v5r129.py`+result、
`product_HEAD_e1.py`/`product_v129_e1.py`/`product_HEAD_e6.py`/
`product_v129_e6.py`（双态产物）、`r129_regress.py`+result、本文件；
中间件 D:/temp/opencode/cl_layout/r129diag、r129matrix、r129regress 不
入库。
