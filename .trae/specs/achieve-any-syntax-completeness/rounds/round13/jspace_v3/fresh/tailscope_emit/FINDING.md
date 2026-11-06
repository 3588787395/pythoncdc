# FINDING — rr-v5r126 [v126-TAIL]：handler 尾块作用域归位实施——判官 REAL46-008 **39/39 = 100%**（R7=0），ElementPath 全文件 BYTE-EQUAL

## 0. 结论速览

- 尾块发射步（v125 §51.4③ 登记的判官最后一里）本轮**实施完成并全验收**：
  **[v126-TAIL] 前驱子树候选判别式 + POP_EXCEPT 终结链走查 + 防御发射**
  （region_ast_generator 单文件 +81）——REAL46-008 /ElementPath 判官
  **status=success units=39/39 success_rate=100.00%**（v124/v125 态 38/39，
  R7 1→**0**），**全文件全字段 BYTE-EQUAL**（iterfind 的 `_cache[cache_key]
  = selector` 归位 handler 末语句，缩进 8）。
- 历轮「id 布局敏感性」复判：净态重放 r9 序列**三连稳定触发**（每次独立
  进程 1 fire）——r10b 零日志系当时文件/缓存态污染（v125 真相二的自伤链
  尾声），非管线 id 敏感性实锤；同进程双跑区域树签名稳定（repro_idsens.py
  三连 True）。id 敏感性**降级为未证实假说**登记（定序专案撤销，§5）。
- 全额闸门：电池 267 案 **TEXT-DIFF 0**（判别式外科性——全语料零触发）；
  pytest 7 套件 2 failed/282 passed/2 xpassed（基线一致）；矩阵 6 案
  **ALL PASS**；REAL46 sweep A/B 见 §4（预期仅 008 案 38/39→39/39）。

## 1. 实现（[v126-TAIL]，单文件 +81，补丁 fix_patch_v5r126.diff）

`_generate_try` handler 装配（handler_node 组装前）新增尾块归位：

1. **候选链首搜索（前驱子树判别式，v125 §51.4① 闭环设计）**：未被实义区
   域认领的块 ∧ 全部条件前驱区域 ∈ region 严格子树（`_v126_in_subtree` 沿
   parent 链）。判别式天然排除：handler 直落尾（前驱=自身，普通 try/except
   的 try 后语句不可吞）、他域回流（内层 handler 偷外层尾块）、已生成块。
   候选按偏移排序（消费确定性）。
2. **链走查（POP_EXCEPT 终结先于 generated 检查）**：沿线收集（8 步上限），
   链内必现 POP_EXCEPT（handler 终结框架块，作证明不重标记不发射）方收束；
   条件终结（JUMP/RETURN/RERAISE/RAISE_VARARGS）与多后继即弃。
3. **防御发射**：链块语句经 `_generate_handler_body_statements` 逐块归位
   handler 体并标记 generated（post-try 收集器不再拾取）；发射设 except
   Exception 守卫——异常时放弃尾块（维持 v124 行为），不中止装配
   （v125 真相一的教训内化）。

## 2. 功效直证

- **ElementPath**：iterfind 尾赋值归位（缩进 8=handler 内）；全文件全字段
  **BYTE-EQUAL**（v124 25 字节尾块序残差清零）；判官 `--source` 新鲜产物
  **39/39 = 100.00%**（R7 **0**——REAL46-008 自 rr-v5r107 时代登记以来首次
  全等）。
- while1 壳/append/raise/break（v124 成果）维持。

## 3. 验证（大改动级全额闸门）

- **A/B 电池 267 案**（r126_regress.py，单文件 RAG 交换 HEAD 4811d386 vs
  v126）：**TEXT-DIFF 0/267**——判别式外科性（全语料零触发，仅 iterfind 形
  命中）；R110 168/169 一致（mc1 正常归一）；登记差 10 案 ALL
  SAME-SIGNATURE；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项一致，
  余 2 失败=既有冻结对）。
- **变体矩阵 6 案**（matrix_v5r126.py，A/B 单文件交换）：E1 iterfind 同构
  精确形 HEAD TEXT-DIFF→v126 **BYTE-EQUAL PASS**（合成案首跑暴露
  `LOAD_CONST ('k',)` vs `'k'` 常量元组下标键渲染残差=无关预存在表达层家
  族，改用变量键对齐真码后全等，残差登记 §5）；E1b 无环直落尾（不可吞
  对照）/C1 while1+循环顶 try/C2 try-in-try/C3 环体 try+break/C4 嵌套
  while-try 全部零漂移 BYTE-EQUAL。**MATRIX: ALL PASS**。
- **REAL46 sweep 46 案 A/B**（v126/HEAD 双侧新鲜产物 --source）：46 案读数
  **仅 1 差**——stdlib_xml_ElementPath HEAD 38/39 97.44% failure → v126
  **39/39 100.00% success**（方向=修复），其余 45 案逐字节一致零回归
  （sweep46_v126/head_result.txt diff 实证）。

## 4. 验收口径与 sweep 读数

实测读数同 §3：stdlib_xml_ElementPath **38/39 → 39/39 100% success**（唯一
变化案，方向=修复），其余 45 案逐字节一致（零回归）。**REAL46-008 全闭合**
（R7=0；46 sweep 剩余 DIFFERENT=REAL46-011~016+4 compile_error，均在案）。
不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **常量元组下标键渲染**（E1 合成案暴露的无关预存在表达层家族）：
   `_cache[('k',)]` 渲染为 `_cache['k']`——LOAD_CONST 元组常量被重建为裸
   串（真实 R2 级：重编译键类型改变）。登记未修。
2. **id 布局敏感性**：降级为未证实假说（本轮同进程三连稳定+进程间触发稳
   定）；定序专案撤销；若未来再现装配翻转再立。
3. v118 E2 残余（while 底部 store-recheck）；E6 相邻 NOP 对；
   46 sweep 其余 DIFFERENT（REAL46-011~016）/4 compile_error。

## 6. 证据文件

`fix_patch_v5r126.diff`（+81 单文件）、`matrix_v5r126.py`+result、
`r126_regress.py`+result、`ElementPath_product_v126.py`、`repro_idsens.py`
（同进程双跑复现脚本——实测稳定）、本文件；中间件
D:/temp/opencode/cl_layout/r126diag、r126matrix、r126regress（sweep 双侧）
不入库。
