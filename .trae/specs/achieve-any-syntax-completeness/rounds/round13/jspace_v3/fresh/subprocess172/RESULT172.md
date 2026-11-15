# RESULT172 — subprocess SP2 RAISE-EXPR + SP8 IFMERGE（69→71/78）

> 仓库 `F:\Downloads\pythoncdc-main`；解释器 `D:/Python/python.exe -I -X utf8`，cwd=仓库根。
> 补丁 `D:\temp\opencode\cl_layout\r172\fix172.py`（2 文件 / 7 anchor，count==1、utf-8-sig BOM 感知、
> LF 空间编辑 + CRLF 还原、`py_compile`、幂等；从 `git show HEAD:` 重打 = 逐字节同 sha）。
> 判官 `scripts/pyc_verify.py single <pyc> --source <产物>`。

## 0. 读数

| 语料 | r171 | r172 | 产物 |
|---|---|---|---|
| subprocess | 69/78 | **71/78（91.03%）** | 69763 B `1ee06b68` → **69863 B `37575864`** |
| request | 194/194 | **194/194** | 87699 B `db2172e8` **逐字节 SAME** |
| difflib | 62/62 | **62/62** | 67855 B `d70df600` **逐字节 SAME** |
| tarfile | 156/160 | **156/160** | 89892 B `fcb8a7fb` **逐字节 SAME** |
| cookiejar | 94/105 | **94/105** | 69418 B `f2c8b33a` **逐字节 SAME** |

subprocess 失败 9 → 7（`_check_timeout`、`_execute_child` 转 EQUAL）：
`call`(bytecode)、`run`、`Popen.__init__`、`Popen.__exit__`、`Popen.__del__`、
`Popen._internal_poll`、`Popen._wait`（后 7 项与 r170 分区一致，属 SP1/SP3..SP7，本轮不动）。

## 1. SP2 RAISE-EXPR（`Popen._check_timeout`，+1）

两处独立根因，都在 region 层重建（CFG 本来就等价，判官报 Different bytecode 属实）：

1. **`raise` 被当表达式语句**（`core/cfg/region_ast_generator.py:68137`，
   `_try_build_ternary_kwarg_call`）。`output=… if stdout_seq else None` 的两个三元挂在
   末合并块 `KW_NAMES/PRECALL/CALL/RAISE_VARARGS` 上，该函数重建 `Call` 后**无条件**返回
   `Expr(Call)`，`RAISE_VARARGS 1` 被丢、尾声补 `LOAD_CONST None; RETURN_VALUE`。
   修复谓词：`final_merge.get_last_instruction().opname == 'RAISE_VARARGS'` 且 `arg == 1`
   → 返回 `Raise(exc=call_expr)`；`RAISE_VARARGS 2`（`raise E() from cause`）逐位回落原 `Expr`。
2. **`.args` 错绑**（`core/cfg/region_analyzer.py:28203`，`_identify_ternary_regions` 内嵌
   `_detect_ternary_context`）。属性链起点恒取 `push_null_idx + 2`，对 implicit-NULL 形态
   （`LOAD_GLOBAL arg&1`）会跳过紧跟的首个实参装载指令，把下一条 `LOAD_ATTR` 误接到被调对象：
   `TimeoutExpired(self.args, …)` → `TimeoutExpired.args(…)`（LOAD_METHOD + 首实参被偷）。
   修复谓词：`push_null_idx+2 if instrs[push_null_idx].opname == 'PUSH_NULL' else +1`。

结果：`raise TimeoutExpired(self.args, orig_timeout, output=b''.join(stdout_seq) if … , stderr=…)`
（与源码 L1252–1256 逐形一致），判官 **EQUAL**。

## 2. SP8 IFMERGE（POSIX `Popen._execute_child`，+1）

复核实测**不是 1 处**差异：归一化后 5 条指令差（`160/164/220` 三条 `POP_JUMP_FORWARD_IF_TRUE`
目标 + `170/230` 的 `is_jump_target` 派生量）＋异常表少 `(586,598,692)`、`(612,…,692)`→`(618,…)`。
两类独立根因：

1. **负极性 and 操作数错标 'or'**（条件 `_USE_POSIX_SPAWN and … and not close_fds and
   not pass_fds and cwd is None and (… or …) and not start_new_session and …`）：
   链内逐指令 `'and' if 'FALSE' else 'or'` 把 `not X`（TRUE 极性 → 链出口）与嵌套 or 组首位
   （TRUE 极性 → 组内真出口）混为一类，随后 or 分组把 3 个 `not X` 成员并进 or 组：
   产品 `(close_fds or pass_fds or cwd is None)` / `(start_new_session or process_group == -1)`。
   修复：新归一化器 `core/cfg/region_analyzer.py:33688` `_v172_negated_and_operand_op_types`
   （`_create_boolop_region_from_chain` 调用点 `:34104`）——末成员为 `'and'` 且以失败极性跳转
   （opname 含 `FALSE`）时取其目标为链出口，把「TRUE 极性且目标 = 该出口」的 `'or'` 成员改回
   `'and'`；`if A and (B or C): pass`（body 与 exit 重合）与 `not (A or B)`（末成员非 FALSE）
   两形态被守卫排除，逐位回落。
2. **嵌套 try/finally 被拆成兄弟 try**（`try: try: … finally: os.close(errpipe_write) …
   finally: os.close(errpipe_read)`）。外层 try 的保护跨度被 `existing_entry_regions` 入口
   下移逻辑切成「内层之后」的续体 → 外层 try 体少一段、异常表少一条覆盖内层 finally 正常副本
   的区间。三处协同修复：
   - `core/cfg/region_analyzer.py:11694`（`_identify_try_except_regions`）：`existing.try_blocks`
     是本 region try 体块集的**真子集**时不下移入口（内层 try 保持与外层同入口；同入口非嵌套
     的双 region 形态 try 体块集相等，不命中守卫）。
   - `core/cfg/region_analyzer.py:38672`（`get_entry_region_for_block`）：同入口多个
     TryExceptRegion 且保护跨度互相包含时，入口归**外层**（内层由外层 Try.body 的
     `nested_try_regions` 预循环整树嵌套）。
   - `core/cfg/region_ast_generator.py:38098`（`_generate_try_body`）：嵌套归属判据放宽——
     保护跨度包含（`_is_span_contained`）即认内层为外层 try 体抽象节点（本单元内外层
     `parent` 同为 posix_spawn `IfRegion`，原 `parent is region` 判据拒收 → 内层语句蒸发）。

结果：条件逐字还原源码 L1823–1837，try/finally 逐层嵌套 = 源码 L1857–1912，判官 **EQUAL**
（异常表 11 条与原件逐条相同）。

## 3. 文本变化（只有 subprocess；其余四语料逐字节 SAME）

`r171verify/products/subprocess_now.py` → `r172 .../subprocess_now.py` 共 3 处，均**更接近源码**：
1. `TimeoutExpired.args(self.args, …)` → `raise TimeoutExpired(self.args, …)`（源码 L1252–1256）。
2. `(close_fds or pass_fds or cwd is None)` → `not close_fds and not pass_fds and cwd is None`；
   `(start_new_session or process_group == -1)` → `not start_new_session and process_group == -1`
   （源码 L1826–1833）。
3. 内层 `try/finally` 归位到外层 `try` 体内（源码 L1857–1912），不再是两个兄弟 try。
判官读数不下降（71/78），四语料读数不变。

## 4. 458 电池（硬门）

`D:\temp\opencode\cl_layout\r172\battery172.py`（由 `...fresh\tarfile167\r170_regress.py` 复制，
只改 `TMP/OUTDIR/EV` 到 `D:\temp\opencode\cl_layout\r172battery`；仓库内脚本未改），先删 scratch 再跑，
`exit=0`：
- **TEXT-DIFF = 17 / 458，集合与 r171 允许集逐案相同**（新增 0、减少 0）：
  功效 6（`E161_olf_real/not_or_and/not_or_notand/pre_if/try_wrap/and3`）+ v111 3
  （`m1_exact/m2_no_genexpr/two_if_diffmsg`）+ 8（`mk_iterencode/yp2/te_variants8/pc9/pm1/
  E3_andnot_nochainstmt/fdt/pc12`）。
- 17 案**全部 BYTE-EQUAL**；`C7_skipedge` **TEXT-SAME**。
- **458 案逐案 (TEXT, 签名) 状态与 r171 完全一致（changed statuses: 0）** → 零回归。
- 收尾把补丁内一处局部变量名 `_last_merge_i` 改为 `_v172_tail_i`（满足「新名不含 `_merge_`」），
  随后**删 scratch 重跑电池**（`battery_stdout2.txt`）：结果与首跑逐案相同（run2 vs run1 changed: 0），
  subprocess 产物 sha 亦不变（69863 B `37575864`）。

## 5. 零触碰 38 案 / 红线

`r172\verify\zerotouch_v172.txt`：38 案 **37 SAME + r164/request_final**（唯一允许例外，
DIFF 且 == 本轮 request 产物 YES），**非允许差异 0 → PASS**。
subprocess 侧红线：`list2cmdline` #32 EQUAL、`_on_error_fd_closer` #53 EQUAL（原地保持）。

## 6. numstat / 卫生 / 零触碰结论

```
128  1  core/cfg/region_analyzer.py
 22  1  core/cfg/region_ast_generator.py
```
`scripts/validate_region_generator_signatures.py` → **统计: 14 个错误, 6 个警告**（与基线一致）。
仅改 2 文件；`.trae/` 未写；未 commit/push/stash；仓库内无探针、无 `V172DBG`（探针只在
`D:\temp\...\r172\work`，已删）。

## 7. 证据索引（`D:\temp\opencode\cl_layout\r172\`）

| 文件 | 内容 |
|---|---|
| `fix172.py` | 补丁（7 anchor；`work\verify_fix172.py` 证明 pristine 重打 = 逐字节同 sha、二次运行全 skip） |
| `verify\products\*_now.py` / `verify\judge_raw_*.txt` | 五语料产物与判官原始读数 |
| `verify\j_corpus172.py` / `verify\j_zerotouch172.py` / `verify\zerotouch_v172.txt` | 复跑脚本与零触碰报告 |
| `battery172.py` / `battery_stdout.txt` / `r172battery\ev\r161_regress_result.txt` | 458 电池与结果 |
| `work\diff_sp_base.txt` / `work\diff_sp_2.txt` | 改前后逐单元逐指令差分（`matching_iter` 配对） |
| `work\cmp_battery.py` | r171↔r172 逐案状态比对（changed statuses: 0） |
| `work\ast_mod_ec.json` / `work\ast_ct.json` | region AST 取证（改前 `Expr(Call)` / `func=Attribute`） |
| `work\backup\` | 改前 4 个 core 文件快照 |
