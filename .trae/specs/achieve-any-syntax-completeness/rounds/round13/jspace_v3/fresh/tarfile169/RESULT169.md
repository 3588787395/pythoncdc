# RESULT169 — 族 D（`TarFile.__init__` + `TarFile._load`）tarfile 152→**154**/160

> 仓库 `F:\Downloads\pythoncdc-main`；只改 1 个文件 1 个 hunk 族（+105/-0 行）；全部产物在 `D:\temp\opencode\cl_layout\r169\`。
> 解释器 `D:/Python/python.exe -I -X utf8 <script>`，cwd=仓库。判官 `scripts/pyc_verify.py single <pyc> --source <product>`。

## 0. 读数

| 项 | 改前 (r168) | 改后 (r169) |
|---|---|---|
| tarfile | 152/160 (95.00%) | **154/160 (96.25%)** |
| `TarFile.__init__` | Failure: Different control flow | **EQUAL** |
| `TarFile._load` | Failure: Different bytecode | **EQUAL** |
| tarfile 产物 | 90139 B `96b2d38d` | 89953 B `11532278` |
| 失败单元（6） | — | `_init_read_gz`、`_read`、`_FileInFile.read`、`add`、`next`、`main` |
| request / difflib | 194/194 · 62/62 | 194/194 · 62/62（产物逐字节 SAME） |
| cookiejar / subprocess | 91/105 · 69/78 | 91/105 · 69/78（`7c122a0d` / `53d99059` 逐字节 SAME） |
| 458 电池 | 9 TEXT-DIFF（允许集） | **9 TEXT-DIFF / 458，全 BYTE-EQUAL**；逐案行与 r168 accepted 基准 **458/458 完全一致**；`C7_skipedge` TEXT-SAME |
| 红线零触碰 | 38/38 | **38/38 SAME**（含 33 红线案，bytes+sha16 逐条相同） |
| 卫生 | 14 错 6 警 | **14 个错误, 6 个警告** |

## 1. `TarFile._load`（16 → 11 指令，头语句蒸发 + `is None` 极性丢失）

真因**不在** `_loop_handle_header:12903`（探针实测该函数正常返回，`_loop_process_header_instructions` 根本没被调用）：
`region_ast_generator._loop_handle_header` 的 **if-break 指令级回退段**（`while True:` 的 header 尾 = 条件跳转，
一个后继是 break/return 出口、另一个后继是回边 ⟹ 走 13357–13475 的手写路径）。

- 命中分支：`_loop_handle_header` 13228–13250 的「`_hdr_last` 为前向条件跳转 ∧ 恰一个 break/return 出口后继
  ∧ 另一后继是回边 ∧ 2 后继」→ `_loop_process_header_instructions`；本例 13273 的 PLACEHOLDER 判据不命中
  （`header.instructions[0]` 是 RESUME），落到 13286–13475 的 `is_if_break_pattern and region.is_while_true` 段。
- 断点 1（语句边界）：13361–13367 的后向扫描只认 `POP_TOP/RETURN_VALUE/RETURN_CONST`（表达式语句收尾）与
  `COMPARE_OP/IS_OP/IS_NOT/CONTAINS_OP/NOT_OP/UNARY_NOT`（条件起点）。`_load` 的 header 块是
  `LOAD self/LOAD_METHOD next/PRECALL/CALL/STORE_FAST tarinfo/LOAD_FAST tarinfo/POP_JUMP_FORWARD_IF_NOT_NONE`
  ——赋值收尾的 `STORE_FAST` 不被认作边界 ⇒ `_stmt_end = len(pre_cond_instrs)` ⇒ 走 13388
  `test_expr = reconstruct(pre_cond_instrs)`，整段前缀被当条件 ⇒ 前导语句蒸发、条件退化为裸 `tarinfo`。
- 断点 2（极性）：13446–13454 的 `_er_ret_on_true` 只覆盖 `POP_JUMP_*_IF_TRUE/IF_FALSE`；3.11 把 `x is None`
  融合进 `POP_JUMP_*_IF_NONE/IF_NOT_NONE`（无 COMPARE_OP），未被处理 ⇒ 真值测试。
- 修复：
  - `[v169-WHILEHEAD]` 后向扫描把 `STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF` 也当语句边界
    （排除 walrus：STORE 前一条是 `COPY 1` 时不切）；切出的前导语句走既有 `_acc → _build_statement` 分支发射。
  - `[v169-NONECHK]` 跳转为 None 类时按「臂块 == 跳转目标 ⟹ 臂在条件成立侧执行」重建
    `Compare(left=test, ops=[IsNot(IF_NOT_NONE)/Is(IF_NONE)], comparators=[Constant(None)])`；落空侧取反用既有
    `_flip_is_none_compare`（不得用 `not()`：会多出 UNARY_NOT，重编译退化成 `UNARY_NOT + POP_JUMP_IF_FALSE`）。
- 产物：`while True: tarinfo = self.next(); if tarinfo is None: break` + `self._loaded = True`，与源码逐字一致。

## 2. `TarFile.__init__`（323/329 指令 + EXTENDED_ARG + 异常表 DIFF）

分析层是正确的（`IfRegion@972 merge=1346`，`then_blocks=[994,996,1058,1060,1164,1344]`）；坏在**发射端归属**：

- `_r58_collect_break_target_stmts(@9206)` 对 `region.break_blocks=[1346]` 命中，1346 正是外层
  `IfRegion@972` 的 `merge_block`；它把 1346 起的语句（=`if self.mode in ('a','w','x')` 整块）收进
  「循环后顺序语句」，`_loop_generate_while` 11688–11692 把它并入**自己的返回列表**，
  父 `If` 的 `_if_generate_then_branch` 直接 extend 进 then 体 ⇒ pax 块整体搬进 `if self.mode == 'a':` 体内。
- 只跳过收集不够：`_generate_loop` 7822–7832 的成员块收尾扫会「只登记不发射」地把 1346 标进
  `generated_blocks`，外层序列随后按 generated 守卫跳过它 ⇒ 语句蒸发（实测：`if self.mode in (...)` 的守卫整条消失）。
- 修复：新增 `_v169_post_loop_parent_if(region, block)`（纯结构事实：`region.parent` 是 `IfRegion`
  且 `block is parent.merge_block`）。merge 是两臂汇合点：then 臂内循环的 break 目标 == merge ⟹ 臂内循环之后
  没有别的语句、break 直接跳出整个 if ⟹ 该块语句属**外层序列**（If 之后）。同判据两处生效：
  收集侧跳过（`_r58_collect_break_target_stmts`）、登记侧跳过（`_generate_loop` 收尾扫）⇒ 交外层序列在 If 之后正常发射。

## 3. 复现与证据

- 基线：`work/tarfile_base.py`（90139 B）判官 152/160，失败 10 项与 r168 一致。
- 中间态：`work/t1.py`（只打 `_load` 修）→ 153/160；`work/t2.py`（只跳过收集）→ `_loaded = True` 掉出 if 但守卫丢失；
  `work/t3.py` = `work/t_final.py` → **154/160**。
- dis：`work/dis_targets.txt`（`TarFile._load` / `TarFile.__init__` 原始 pyc 全量反汇编）。
- 区域/发射追踪：`work/probe_load.txt`、`trace_load.txt`、`probe_init1.txt`、`trace_init*.txt`、
  `lt_trybody.txt`（证明 1346 在 try 体走查时已在 generated）、`lt_genloop.txt`（证明 7832 行是登记点）。
- `work/region_ast_generator.v169final.py` = 打完补丁的最终文件（sha256 `4fda0303baefaf8b`）。
- `fix169.py`：5 个 anchor（`git show HEAD:` 的 r168 基线上 count==1）、utf-8-sig 感知、`py_compile` 预检 + 回滚、
  幂等；实测「pristine → fix169.py」产出与 `work/region_ast_generator.v169final.py` **逐字节相同**。
- 电池：`battery169.py`（复制 `fresh/tarfile167/r168_regress.py`，只把 EV→`tarfile167`、TMP→`r169regress`、
  OUTDIR→`v169`），结果 `work/battery169_result.txt`。**注意**：该脚本 phase2 会临时把 `core/cfg/*` 换成
  `HEAD=f7d80873`（v148 基线）版本做 A/B，`finally` 恢复；期间 `git diff` 会显示大量「删除」，属瞬态。

## 4. 零触碰 / 未动项

- 红线 38 案：`r161c` 5、`r162/new` 9、`r163 mx1_*` 5、`r164 request_final`、`r165 repro` 4、`r167 repro` 14
  —— 全部逐字节 SAME（`work/zerotouch169.txt`）。`dc1/dc2/dc3`、`f2`、`fc2` 均 SAME。
- 未改：`.trae/`（电池写过的 `tarfile167/r161_regress_result.txt` 内容与本轮产物逐字节相同，已 `git checkout` 还原，
  sha `a78f7417…` 与 r168 accepted 一致）、`scripts/`、`tests/`、异常表相关注入点（族 A 的 `return None` 未动）。
- 仓库无 `V169DBG`、无探针残留；未 commit/push/stash。
