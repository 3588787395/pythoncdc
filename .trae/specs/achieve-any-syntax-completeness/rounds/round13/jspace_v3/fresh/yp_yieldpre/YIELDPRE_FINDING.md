# YIELDPRE：IfRegion 条件块前缀裸 yield 语句丢失（rr-v5r96，Task 22）

## 家族选定

46 sweep（rr-v5r95 后）16 DIFFERENT 中 13 个 R7-only。最小切入口 REAL46-007
（json/encoder，单 R7 dim）逐函数字节比对定位：`_make_iterencode` 嵌套生成器
`_iterencode_dict`/`_iterencode_list` 丢 yield 语句。

## 根因（独立自包含复现 mk_iterencode + settrace/monkeypatch 实证）

源：`_iterencode_dict` 三处 `yield '{'`（B[90]）/`yield _key_separator`（B[528]
第二连发）/`yield '}'`（B[950]）；`_iterencode_list` 两处 `yield '['`/`yield ']'`。

块结构：`yield` 与后续 if 条件**同块**（`[LOAD_CONST; YIELD_VALUE; RESUME;
POP_TOP; LOAD_DEREF markers; POP_JUMP_IF_NONE]` 单块）。IfRegion 条件块前置
语句提取器 `_if_extract_cond_instructions` 的 POP_TOP 冲刷（L22036）仅当缓冲含
CALL 才 `_build_statement`——裸 `yield X`（LOAD_CONST/LOAD_DEREF + YIELD_VALUE，
无 CALL）滞留缓冲、静默丢失且续入条件段污染。姊妹位点 `_loop_extract_pre_stmts_
from_instrs`（G1 fix/Round 04，probe_g1 P6）与 `_loop_process_header_instructions`
早已镜像同款 YIELD_VALUE 语句边界处理——本位点缺镜像即根因（区域归约算法原则 2：
每块唯一归属，yield 前缀语句归块前缀重建者发射）。

monkeypatch 实证：B[528] 仅 `_build_statement([530..548])`（第一条 yield 经 CALL
冲刷存活），[550..560]（RESUME+POP_TOP+第二条 yield）落在语句重建与条件提取的
缝隙中消失。

## 修复（只增不破，+47 行）

`_if_extract_cond_instructions` 补 G1 同款镜像（[v96-YIELDPRE]）：
1. 扫描循环加 `YIELD_VALUE` 语句边界分支：缓冲去噪后 reconstruct 为 Yield value，
   发射 `Expr(Yield)` 并置 `_yield_cleanup_pending`；
2. POP_TOP 分支头部加 cleanup 待定跳过（yield 协议清理 POP_TOP 非语句终结）；
3. **语句边界判据（结构事实）**：仅当 YIELD_VALUE 后越过 RESUME/NOP/CACHE/
   EXTENDED_ARG 的下一有效指令是 POP_TOP（yield 结果被丢弃）才按语句边界发射；
   下一有效指令是 STORE_*（`got = yield x` send 绑定，yp4）或条件测试类
   （`if (yield x):` 条件表达式，yp6）时维持旧行为追加缓冲交既有路径（C3）。
   首版无前瞻判据时 yp4/yp6 回归（HEAD A/B 实证 BYTE-EQUAL→DIFF），加判据后
   8/8 变体 + 复现全 BYTE-EQUAL。

## 验证（全实测）

| 检查 | 修复前（v5r95） | 修复后（v5r96） |
|---|---|---|
| mk_iterencode 独立复现（3 code object DIFF） | `_iterencode_dict` 976→952、`_iterencode_list` 636→620 | **BYTE-EQUAL（全 code object）** |
| yp 变体矩阵 8 形态 | （首版 yp4/yp6 回归已修） | **8/8 BYTE-EQUAL** |
| REAL46-007 json.encoder | 3 fn co_code 差 | **BYTE-EQUAL；权威 semantic_diff 整案 EQUAL, diffs=[]** |
| REAL46-012 difflib | 14 fn 差 | 12 fn 差（removed `_qformat`/`context_diff` 同族，余 12 属其他族） |
| REAL46-046 kb/syntax_coverage | 7 R5 差 | 产品 **BYTE-EQUAL**（R5 残差 = `__file__` 路径派生值 `GEN_DIRS` ——评估装载路径必然差，非反编译缺陷，登记为口径边界） |
| 其余 13 DIFFERENT 案逐函数 | — | **removed=0 added=0（零位移）** |
| er_variants 四形态 | BYTE-EQUAL | 4/4 不变 |
| 20 形态矩阵 | BYTE-EQUAL | 全部不变（w2 known-drop 逐字不变） |
| 前轮探针 el1/y1/x1/r31/ann/tern/ell/fi1 | BYTE-EQUAL | 全部不变（文本与记录一致） |
| pytest 7 套件 | 2F/282P/2XP 冻结对 | **一致** |
| 比较器冻结 | pyc_verify SHA256 FE1902... | **一致；tests/pyc_verify 零改动** |
| 全量 1556 闸门（v5r96 对 v5r89） | EQUAL 1132/ERROR 423/None 1 | **0 回归**；EQUAL 1180（+48 恢复集与 v5r95 完全同集，归属已提交态+测量恢复，非本轮修复）；8 抖动（JS-IF-074 None→ERROR 已知；JS-TRY-073/JS-WITH-055/062/JS-DECORATOR-003/013/017/018 ERROR→None=4 路并发下反编译 20s 超时，单跑 8.1-8.3s 复核判定 ERROR 与基线一致）|
| REAL46 sweep（v5r96 对 v5r95） | 16 DIFFERENT/13 EQUAL/17 ERROR | **0 回归**；REAL46-007 DIFFERENT→**EQUAL**（本轮修复）；REAL46-045 EQUAL→skip（环境事件见下，不可测非翻转）；15/13/17+skip1 |

## 环境事件（诚实登记）

上轮 rr-v5r95 的 __pycache__ 卫生清理（57 目录）删除了两个被 space_46 引用的
**未跟踪 gitignore 缓存 pyc 原件**（清理前未核对 space_46 的 pyc 引用清单）：

1. `tools/kb/__pycache__/syntax_coverage.cpython-311.pyc`（REAL46-046）：按空间
   记录 sha 逐 dfile 变体复原——绝对路径 co_filename 变体**逐字节复现**
   （sha 9029d34e MATCH），已恢复，REAL46-046 恢复可测。
2. `scripts/__pycache__/pyc_verify.cpython-311.pyc`（REAL46-045，比较器自身的
   pyc 自涉案）：源未变（frozen sha FE1902 匹配）但 7 种 dfile 变体均不复现
   sha ca69cde7——原编译时内嵌源 mtime 已不可恢复 → 该案从 EQUAL（可测）
   变为 skipped（c2_pyc_missing，**不可测**，非 verdict 翻转）。全量 sweep
   记录数 46→45+skip1。

教训（升级）：__pycache__ 卫生清理前必须先核对 judgment_space 与 space_46
全部 pyc 引用并逐 sha 备份可复原者；不可复原者须在登记文档显式记录
measured→unmeasurable 状态迁移。

## 诚实边界

- REAL46-012 剩 12 fn 差（其余族）、REAL46-046 R5 为装载路径口径边界；
  46 sweep 其余 DIFFERENT/ERROR 不变。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r96.diff` | [v96-YIELDPRE] 完整 diff（+47 行含判据注释） |
| `mk_iterencode.py` / `mk_iterencode_out.py` | 独立自包含复现（修复后产品） |
| `yp1..yp8.py` / `yp1..yp8_out.py` | 变体矩阵（8 形态：边界/连发/绑定/条件内嵌/嵌套/模块级） |
| `case_REAL46-007.json` / `semantic_REAL46-007_v96.json` | 整案 EQUAL |
| `case_REAL46-012.json` / `semantic_REAL46-012_v96.json` | R7 7→5 |
| `case_REAL46-046.json` / `semantic_REAL46-046_v96.json` | R5 口径边界登记 |
