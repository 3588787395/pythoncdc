# FINDING — rr-v5r127 [v127-TUPKEY]：单元素元组下标键渲染修复（键类型 tuple→str 改变 R2 级）——LOAD 位括号+尾逗号归位

## 0. 结论速览

- 常量元组下标键渲染族（v126 §52.7 登记）**修复**：`d[('k',)]` 曾渲染为
  `d['k']`（键类型 tuple→str，重编译 LOAD_CONST ('k',) vs 'k' 字节不等，
  R2 级）——缺陷位点 = code_generator `_generate_subscript`（AST 对象分支
  ~4686）的元组切片渲染 `', '.join(slice_codes)` 对 1 元组无尾逗号。
  [v127-TUPKEY] 单文件 2 处（AST 分支 + dict 分支同构防御）+22/−2。
- 修复后：`d[('k',)]` 精确还原，**repro1 重编译全字段 BYTE-EQUAL**；
  多元素隐式元组 `d['a', 'b']`（与原编译等价形）与 STORE 位（HEAD 本已正
  确）维持不变。
- 全额闸门：电池 267 案 **TEXT-DIFF 0**；pytest 7 套件 2 failed/282 passed/
  2 xpassed（基线一致）；矩阵 6 案 **ALL PASS**；REAL46 sweep A/B 见 §4。

## 1. 根因（三层追踪）

- 复现：`def f(d): return d[('k',)]` → 产物 `return d['k']`（LOAD_CONST
  ('k',) vs 'k'）。
- 管线分层排查：v2 reconstructor 的 BINARY_SUBSCR 分支（Round4-09）把元组
  常量切片重建为 Tuple AST 节点 ✓（AST 层无恙——FunctionDef 转换后
  `ASTSubscript(slice=ASTTuple)` 且 `slice.to_code()='('k',)'` 正确）；
  **CFGCodeGenerator 的 AST 对象分支 `_generate_subscript`（~4686）**把元
  组切片展开为 `', '.join(...)`——1 元组无尾逗号 → 键类型改变。
- 位点辨析：dict 分支（~3800）同构缺陷同修（防御性——两分支服务不同管
  线态）；STORE 位（STORE_SUBSCR 目标渲染）HEAD 本已正确（E2 实测归控制）；
  赋值位 `x = ('k',)` 本已正确（ASTTuple.to_code 自带 arity 处理）。

## 2. 修复（[v127-TUPKEY]，只增不破，2 处 +22/−2）

1. **AST 分支**（`_generate_subscript` ~4686）：`len(slice_codes)==1` →
   `'(' + slice_codes[0] + ',)'`（括号+尾逗号，与原源形一致）；多元素维持
   隐式元组 join。
2. **dict 分支**（~3803）：同构防御（dict 态管线的同型渲染）。
3. C2：多元素分支逐位不变；C3：纯渲染 arity 补齐，无结构改动。

## 3. 验证（全实测）

- **repro1**：`return d[('k',)]` 精确还原，重编译全字段 BYTE-EQUAL。
- **A/B 电池 267 案**（r127_regress.py，单文件 CGN 交换 HEAD d796034b vs
  v127）：**TEXT-DIFF 0/267**；R110 168/169 一致（mc1 正常归一）；登记差
  10 案 ALL SAME-SIGNATURE；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线逐项一致，
  余 2 失败=既有冻结对）。
- **变体矩阵 6 案**（matrix_v5r127.py，A/B 单文件交换）：E1 LOAD 位 1 元
  组键 HEAD TEXT-DIFF→v127 BYTE-EQUAL **PASS**；E2 STORE 位（HEAD 本已正
  确归控制）+C1 多元素隐式元组+C2 赋值位 1 元组+C3 嵌套元组键+C4 无元组
  下标全零漂移 BYTE-EQUAL。**MATRIX: ALL PASS**。
- **REAL46 sweep 46 案 A/B**（v127/HEAD 双侧新鲜产物 --source）：§4 读数。

## 4. 验收口径与 sweep 读数

REAL46 sweep A/B：46 案读数**逐字节一致**（diff-exit=0 实证）——TUPKEY
修复在 46 真实包零触发（无 1 元组下标形），ElementPath 维持 **39/39
100%**；46 sweep 剩余 DIFFERENT=REAL46-011~016+4 compile_error（在案）。
不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. v118 E2 残余（while 底部 store-recheck）；E6 相邻 NOP 对；
   46 sweep 其余 DIFFERENT（REAL46-011~016）/4 compile_error。
2. pytest 余 2 失败 = 冻结对（B01/B02，登记态）。

## 6. 证据文件

`repro_one_tuple.py`/`product_HEAD_one_tuple.py`/`product_v127_one_tuple.py`
（最小复现双态产物）、`matrix_v5r127.py`+result、`r127_regress.py`+result、
本文件；中间件 D:/temp/opencode/cl_layout/r127diag、r127matrix、r127regress
（sweep 双侧）不入库。
