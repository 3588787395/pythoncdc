# FINDING — rr-v5r133 [v133-DEFLINE/DELSTMT]：IfRegion 条件块前导段提取器模块级语句还原（REAL46-012 difflib 53→54/62，module 单元 100%）

## 0. 结论速览

- REAL46-012 difflib 首战：判官 9 差单元中的 **`<module>`** 修复——
  **53/62 → 54/62（85.48%→87.10%）**，module 单元 100%。两个缺陷位点
  （同一提取器 = IfRegion 条件块前导段提取器 `_if_extract_cond_instructions`，
  模块尾部 `if __name__` 的巨型条件块吸收全部模块级 def 作为前导段）：
  1. **[v133-DEFLINE]** 多行 def 签名行锚 NOP 游程（unified_diff 签名跨
     2 行 → NOP(firstlineno)+NOP(firstlineno+1)）被无条件跳过；且既有
     v107-NOPSIG 判据④ `starts_line > co_firstlineno` 把 def 首行 NOP
     （== firstlineno）排除——双因叠加，NOP 对丢失（module co_code
     388→374）。
  2. **[v133-DELSTMT]** 模块级 `del re`（restore def 前，line=2017）被
     默认累积吞没（提取器无 DELETE 分支）。
- 余 8 差单元（find_longest_match/get_matching_blocks/get_grouped_
  opcodes/get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper）=
  深层循环/控制流族（get_matching_blocks 实测 B234 反源序形在循环头
  提取路丢 `la` 赋值=la 变全局 R1 隐患）——各自独立轮登记。

## 1. 根因（三层追踪）

- `<module>` 字节差定位：388 vs 374，首差 byte 216 = unified_diff def
  前的 NOP(line=1095)+NOP(line=1096)（difflib.py 1095-1096 = 签名跨两
  行）；次差 byte 334 = `DELETE_NAME 're'`（difflib.py 2017 `del re`）。
- 提取器链定位：unified_diff 的 STORE 经 traceback =
  `_generate_if→_if_generate_normal→_if_extract_cond_instructions:22522`
  ——模块尾部 if 的条件块=巨型块@0（145 指令），全部模块级 def 作为
  前导段提取；该提取器的 NOP 分支只有 W11-B 孤立边界形
  （`_is_orphan_boundary_nop`：after≤2 且 return-none 形——NOP 对后随
  LOAD_CONST+MAKE_FUNCTION 不命中）→ 无条件跳过。
- v107 判据④复核：`_is_def_prologue_nop_run` 要求游程内全部 NOP 的
  starts_line **>** def 的 co_firstlineno——CPython 对多行 def 头的每行
  （含 def 行本身）发行锚 NOP，首行 NOP == firstlineno 被拒 → 即便补
  分支也须先放宽判别。

## 2. 修复（[v133-DEFLINE]+[v133-DELSTMT]，只增不破，单文件 +60/−1）

1. **[v133-DEFLINE]**（`_is_def_prologue_nop_run` 判据④）：`<=` → `<`
   （同线不可能共存裸常量语句，Round-33 排除语义由 `< firstlineno`
   完整保留）；注释更新。
2. **[v133-DEFLINE]**（`_if_extract_cond_instructions` NOP 分支）：语句
   边界（pre_instrs 空）先试 `_is_def_prologue_nop_run`——命中发射 K 个
   裸 pass 占位（每个恰 1 NOP、零常量），游程余量 `_dpr_skip` 局部计数
   消化（防逐 NOP 重复发射 K×K）。
3. **[v133-DELSTMT]**（同提取器）：语句边界 DELETE_NAME/FAST/GLOBAL/
   DEREF → `Delete([Name(ctx=Del)])`；DELETE_ATTR/DELETE_SUBSCR 经既有
   `_build_delete_stmt`（R10-N1 同源）重建目标链；非语句边界维持旧行为
   （C3）。

## 3. 验证（全实测）

- **矩阵 6 案**（matrix_v5r133.py，A/B 单文件 RAG 交换 HEAD d39aac5e
  vs v133）：E1 模块级多行 def 签名（行锚 NOP 对夹于 def 间）HEAD
  TEXT-DIFF→v133 **BYTE-EQUAL PASS**；E2 模块级 del（无 if 宿主走其他
  路径，HEAD 本已等价归控制）；C1 单行 def/C2 函数体多行 def（v107
  既有域）/C3 函数内 del/C4 模块裸串+def（Round-33 域）全零漂移。
  **MATRIX: ALL PASS**。
- **REAL46 判官**：difflib **53/62→54/62（85.48%→87.10%）**，module
  单元闭合（388=388）。
- **A/B 电池 267 案**（r133_regress.py，单文件 RAG 交换 HEAD d39aac5e
  vs v133）：**TEXT-DIFF 0/267**（全语料零漂移）；R110 168/169 一致
  （mc1 正常归一）；登记差 10 案 **ALL SAME-SIGNATURE**（含 SUBST-SIG
  pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项一致，
  余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接覆盖
  触达面（54/62）；回归面由电池 267 案零漂移+矩阵 5 控制案兜底。

## 4. 验收口径

实测读数同 §3：difflib **53/62→54/62（85.48%→87.10%）**，module 单元
闭合；电池 267 案 TEXT-DIFF 0；pytest 冻结对基线一致。不宣称
G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. difflib 余 8 差单元族（get_matching_blocks 实测 B234 反源序形在循环
   头提取路丢首目标=真实 R1 隐患——循环头提取器缺 B234/SIG2 归约，首
   选下一轮）；REAL46-014 tarfile（142/160）/016 urllib.request
   （185/194）；REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；
   4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r133.diff`（+60/−1 单文件）、`matrix_v5r133.py`+result、
`r133_regress.py`+result、本文件；中间件
D:/temp/opencode/cl_layout/r132diag、r133matrix、r133regress 不入库。
