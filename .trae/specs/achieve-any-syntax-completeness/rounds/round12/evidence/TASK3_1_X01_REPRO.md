# Task 3.1–3.3 — JS-IF-076 复现、R7 清零与 docstring 保真（achieve-any-syntax-completeness）

日期：2026-10-24。输入：`test_repros/round2/x01_if_deep_hosts.py`（J 空间 p_j，sha256
`844bb517…8655f0`）与 `test_repros/round2/x01_if_deep_hosts.pyc`。

## 一、复现命令与读数

```bash
python -X utf8 pycdc.py test_repros/round2/x01_if_deep_hosts.pyc \
  -o test_repros/round2/x01_if_deep_hosts_fresh.py
python -X utf8 scripts/pyc_verify.py single test_repros/round2/x01_if_deep_hosts.pyc \
  --source test_repros/round2/x01_if_deep_hosts_fresh.py     # → 7/7（按值归一口径）
python -X utf8 tools/completeness/semantic_diff.py \
  --case case_js_if_076_fresh.json --out semantic_js_if_076_fresh.json   # → EQUAL（修复后）
python -X utf8 tools/completeness/semantic_diff.py \
  --case case_js_if_076_archived.json --out semantic_js_if_076_archived.json # → DIFFERENT（归档旧产物基线，R7×5 + R1×1）
```

两口径差异说明：`pyc_verify` 的按单元比较对常量索引做按值归一（LOAD_CONST oparg
按常量值对齐），故判 7/7；Task 1 修正口径后的 `semantic_diff` R7 对 `co_code` /
`co_consts` 取原始字节 sha，不做未登记归一——**R7 是更严的正确判据**。修复前基线
5 条 R7 全部成立；修复后 fresh 产物 R7 清零（EQUAL）。

## 二、修复前 5 条 R7 差异（归档基线，semantic_js_if_076_archived.json）

| # | 路径 | 原件 | 归档产物 | 机制 |
|---|---|---|---|---|
| 1 | `$.metadata.code.co_consts.v[2].code_sha` | `e4ef787b…` | `638a25f5…` | if_in_while：`while True` 把 `True` 写进常量表（原件 `while 1` 复用已有 `1`），`LOAD_CONST` oparg 1→3，co_code 字节不同 |
| 2 | `$.metadata.code.co_consts.v[2].consts_len` | 2 | 4 | 同上：常量表 `(None, 1)` → `(None, False, True, 1)`（`while False` 骨架引入 `False`） |
| 3 | `$.metadata.code.co_consts.v[3].code_sha` | `b7a8bdfa…` | `4db091ad…` | if_in_try：同一机制（两个 `while False` 骨架 + 字面形式） |
| 4 | `$.metadata.code.co_consts.v[3].consts_len` | 4 | 5 | 同上 |
| 5 | `$.metadata.code.co_consts.v[6].code_sha` | `9d9747ef…` | `04d12b84…` | if_shallow：源码 `if 1: R = 1` 折叠点的行 NOP 在产物直落形式中缺位，co_code 字节不同 |

R1：修复前新鲜产物 0 条（`if_in_while()` 源码本身为死循环——内层 `while 1` 无出
口——调用超时，按 Task 1.3 口径单列，其字节级由 pyc_verify 单元覆盖）。

## 三、族级根因与修复（3.2 / 3.3）

**根因（折叠控制行头的字面形式、行标记计数与常量残留未对齐原件）**：反编译端在常
量折叠后的字节码上重建控制结构时，(a) 用 `while True`/`while False` 骨架而非原件
字面形式（常量表污染 → consts_len + LOAD_CONST oparg 偏移）；(b) 直落形式丢失折叠
点的行 NOP（co_code 错位）；(c) 折叠行头的**测试常量残留**未重写出（CPython 为
`if 1:` 发射测试 LOAD_CONST 后 peephole 移除指令但保留常量条目——常量表中留下无指
令引用的 `1`/`False`）；(d) try/finally 正常路径内联副本在 try 体末语句为折叠 if
包裹形态时于 finally 入口再生**后继语句行位 NOP**（x01::if_in_try NOP@14 实测，
line=26 即 R=1 语句行位）；(e) 模块级 docstring 被块走查按普通赋值发射为
`__doc__ = '…'`。

**修复（全部族级谓词，无 B 编号/测试名/输入值特判，判据只读 CFG 指令序、异常表、
回边目标与原件常量表——I.4 白名单）**，`core/cfg/region_ast_generator.py`：

1. `_folded_statement_placeholder` → 裸 `pass` 单元：任意语句位置恰编译为 1 个行
   NOP、零常量（实测），替代 `while False: pass`（恒引入 `False`）与多行
   `if <C>: pass`（非末位 2 NOP，计数不可控）。
2. `_nop_structural_veto`（自 `_is_orphan_boundary_nop` 抽出，判定逐位保持）：
   V-T/V-S/V-B/V-L 四类结构性 NOP 否决，三方共用保证「每 NOP 唯一归属」。
3. `_is_unaccounted_folded_head_nop` + `_emit_folded_nop_run_units`：未归属折叠常量
   控制行头（`if 1:`/`while 1:` 行标记，后随同块非噪声指令）按**邻接游程＋常量残留
   队列**贪心解析：假值头 → `while <C>: pass`（单 NOP＋残留假值，实测）；真值头＋
   pass 行 → `if <C>: pass`（双 NOP＋残留真值，实测）；真值头＋实体 → 包裹占位
   `if <C>: <后继>`（单 NOP＋残留真值）；无残留 → 去重候选值/裸 pass。残留队列
   `_unfolded_head_consts` 取原件常量表中未被任何取常量指令引用的数值常量（表序）。
4. `_folded_wrap_placeholder` + `_resolve_folded_wrap_placeholders`：try 体受保护行头（[B87-V3R3]
   两发射点）改为包裹形态并在作用域终结期与后继语句合并——try/finally 内联副本行
   位 NOP（机制 (d)）由此再生；无后继退化为裸 pass/`if <C>: pass`。
5. `_unconditional_loop_test` / `_folded_statement_placeholder` 字面形式：真实
   LoopRegion 发射点的 `while` 测试按原件常量表选 1/True（含 True ⇒ True，否则
   1——`while True` 会向重编译常量表新增 True，x01::if_in_while consts_len 2→4
   根因）；合成包裹（continue 宿主 / 重检拆分 / Assert 兜底）仍用 Constant True
   （R04/R21 包裹合并判据与再调和机制按 True 识别——实测改 1 会使 4 条
   continue/try 用例幻影包裹复现，合并判据已扩展为折叠真值字面等价族 1/True）。
6. 模块 docstring（机制 (e)，Task 3.3）：const[0] 为 str 且模块前两条指令为
   `LOAD_CONST(0)+STORE_NAME(__doc__)` ⇒ 前置字符串字面量 Expr 并剥去块走查产出的
   同值 Assign（两形式重编译逐字节相同，字面量形式保源码形态）。

## 四、修复后形态（新鲜产物，7/7 比较器 + semantic_diff EQUAL）

| 函数 | 原件源码 | 产物（修复后） | R7 |
|---|---|---|---|
| if_in_while | `while 1: if 1: while 1: if 1: R = 1` + `break`（死循环，break 被优化器移除） | `pass` / `pass` / `while 1:` / `pass` / `R = 1` | EQUAL（4 NOP 计数与回边目标逐位对齐；嵌套形态信息已被编译销毁，字节级还原即上限） |
| if_in_try | `try: if 1: try: if 1: R = 1 finally: F = 1 except ValueError: …` | 同一嵌套形态（包裹占位合并还原 `if 1:` 两层 + finally 内联行位 NOP@14） | EQUAL |
| if_shallow | `if 1: R = 1` | `pass` / `R = 1` | EQUAL |
| if_in_match | 嵌套 match | `case [a, b]: if a and b == 2: …`（形态差保留：嵌套 match 折为 and 条件） | EQUAL（字节级） |
| 模块 docstring | 字符串字面量 | 字符串字面量（Task 3.3） | EQUAL |

## 五、修复验证（回归全绿）

- x01：`pyc_verify single` 7/7；`semantic_diff` fresh **EQUAL**（0 diff）；归档基线保持 DIFFERENT（R7×5+R1×1，作为修复前证据）。
- 合成探针 `rounds/round12/probes_x01/p_x01_variants.py`（Task 3.4，v1 行头直落体 /
  v2 行头+pass 体 / v3 while 宿主 / v4 try-if-finally / v5 孤立残留共存，全可调用）：
  `pyc_verify single` 7/7；`semantic_diff`（含 6 条 call_exprs）**EQUAL**。
- B142 定向：v_b71_face 4/4、p_g1 3/3、p_g2 2/3、p_g3 2/3（全部持平冻结基线）；
  x04 7/7、p5_docstring 4/4。
- 全量：402 八分片 6617/6617、small34 1568/1568、quotation 153/153；pytest 基线
  （2 失败为 stash 对比既有）。

## 六、附件

- `case_js_if_076_fresh.json` / `case_js_if_076_archived.json`：semantic_diff 输入
- `semantic_js_if_076_fresh.json`（EQUAL）/ `semantic_js_if_076_archived.json`（修复前基线）：R 级裁决
- `../probes_x01/`：Task 3.4 合成探针 + 调用级 case + R 级裁决
- `test_repros/round2/x01_if_deep_hostsOK.py`：修复后产物
