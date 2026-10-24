# probes_x01 — Task 3.4 合成探针（折叠常量控制行头族 + docstring）

输入：`p_x01_variants.py`（源）→ `p_x01_variants.pyc`（CPython 3.11）→
`p_x01_variantsOK.py`（当前管线产物）。调用级 case：`case_p_x01_variants.json`
（6 条 call_exprs），R 级裁决：`semantic_p_x01_variants.json` = **EQUAL**；
`pyc_verify single` = 7/7。

## 覆盖结构族（rr-v5r03 修复面，判据均为 I.4 白名单：CFG 指令序 / 异常表 / 回边目标 / 原件常量表）

| 变体 | 结构族 | 修复机制 |
|---|---|---|
| v1_head_inline | 折叠 `if 1:` 行头 + 实体（单 NOP 头） | `_emit_folded_nop_run_units` 包裹占位 → `_resolve_folded_wrap_placeholders` 合并 `if <C>: <体>` |
| v2_head_pass | 折叠 `if 1:` 行头 + pass 体（非末位双 NOP 游程） | 游程解析：真值头 + 邻接 pass 行 → `if <C>: pass`（残留常量按表重写） |
| v3_while_host | `while 1:` 宿主 + 折叠头（回边目标＝体首行 NOP） | 游程解析 + 真实循环测试字面按常量表选 1/True（`_unconditional_loop_test`，仅真实 LoopRegion 发射点） |
| v4_try_fin | `try:`/`if 1:` 嵌套 + finally（内联副本行位 NOP） | [B87-V3R3] 受保护行头包裹占位（`_folded_wrap_placeholder`），finally 入口行位 NOP 由此再生 |
| v5_head_orphan | 孤立 `while False: pass`（假值残留 False）与折叠 `if 1:` 头共存 | 游程解析假值单元 `while <C>: pass`（单 NOP + 残留假值）；队列 `_unfolded_head_consts` 按表序消费 |
| 模块/函数 docstring | 模块级字面量还原 + 函数 docstring 保留 | 模块 `LOAD_CONST(0)+STORE_NAME(__doc__)` 形态判定 → 前置字面量 Expr 并剥同值 Assign（Task 3.3） |

## 字面形式实测事实（CPython 3.11，本探针与 x01 复核）

- 裸 `pass`（任意位置）＝ 1 个行 NOP、零常量、零跳转。
- 多行 `if <C>: pass` 非末位 ＝ 2 NOP（if 行 + pass 行）且保留 C；末位 ＝ 1 NOP、
  C 不保留。
- `while False/0: pass` ＝ 单 NOP 且保留假值 C。
- `while 1:` 与 `while True:` co_code 逐字节相同；`while True` 向常量表新增 True，
  `while 1` 不新增——真实循环测试字面必须按原件常量表选型；合成包裹（continue 宿
  主、重检拆分）仍用 Constant True（R04/R21 包裹合并判据 `value is True` 与再调和
  机制按 True 识别，rr-v5r03 已把合并判据扩展为折叠真值字面等价族 1/True）。
- try/finally 正常路径内联副本：try 体末语句为折叠 if 包裹形态时，finally 入口再
  生后继语句行位 NOP（x01::if_in_try NOP@14）。
