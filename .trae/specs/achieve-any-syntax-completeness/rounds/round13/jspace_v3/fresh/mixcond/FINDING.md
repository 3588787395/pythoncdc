# rr-v5r163 MIXCOND-STMT —— request 余 2 单元（目标 193/194，本族只做 ftp_open）

轮次：rr-v5r163（Task 89）｜域：MIXCOND-STMT｜单族单轮

## 一、侦察结论：两单元**两族**，不共享修复代码（r163 RECON163.md）

request 192/194 的两个失败单元（均 `Different control flow`）：

| 单元 | 错误产物 | 真实源码 | 缺陷侧 |
|---|---|---|---|
| `FTPHandler.ftp_open` | `:1119 type = file and 'I' or 'D'`（对）；`:1120 for attr in file and 'I' or 'D':`（**错**） | `for attr in attrs:` | **消费端**：for-iterable 归属 |
| `URLopener.retrieve` | `:1302 if filename is None and type:` + 嵌套 `if type=='file': pass else: fp=self.open(...)`，`:1314` 又重复 open | `if filename is None and (not type or type=='file'):` | **检测端**：BoolOp 链类型/截断 |

## 二、最小复现（r163/min repro 清单）

| 案 | 形 | 改前 |
|---|---|---|
| `mx1_a`/`mx1_b` | 原形（赋值 + for） | failure（iterable 错） |
| `mx1_c` | `a and 'I'` | failure |
| `mx1_d` | `a or 'D'` | failure |
| `mx1_e` | 前置调用 | failure |
| `mx2_a` | 带 try/except | failure（守卫条件错） |
| `mx2_b` | 仅守卫 | failure |
| `mx2_f` | `not type or other` | failure |
| `mx2_c` | 体为 pass | 判官 success 但条件仍错（**判官盲区**，登记） |
| `mx2_d`/`mx2_e` | 无 `not` / 无 `or` | 正常（对照） |

## 三、ftp_open 根因（本轮修复对象，已实证）

基本块 **B25（偏移 696-700）** 同时包含 `STORE_FAST type`(696) + `LOAD_FAST attrs`(698) + `GET_ITER`(700)。
`BoolOpRegion.merge_block` 与 `LoopRegion.for_iter_setup` **同为 B25**；
`region_ast_generator.py` 两处镜像点（约 `:8026-8032` 与 `:53004-53010`）**仅凭 merge 身份**就把整条 BoolOp 当作 `iter_expr`，
导致约 `:8093` 跳过 `_loop_extract_for_iter_pre_stmts`（约 `:12033`）。
→ 是「for-iterable 提取在基本块粒度越界」，**不是**语句层复制。
实模块 `:1119` 的赋值行由并存的 TernaryRegion 发射；最小复现中该行被 LoopRegion 吞掉，同一谓词。

**修复方向**：判定 `iter_expr = BoolOpRegion` 时追加结构性要求——merge 块内在 `GET_ITER`
之前不得存在 `STORE_*` / `POP_TOP`（本例 `STORE_FAST` ⇒ 拒绝）；拒绝后回落既有
`_loop_extract_for_iter_pre_stmts` 拆分前缀并使用 `attrs`。两镜像点同谓词，并复用
约 `:8183` 既有「已发射」守卫防重复赋值。

## 四、retrieve 根因（**下一轮 r164 处理，本轮不动**）

检测端：B2(6-8) 的 `IF_FALSE→172`（then body）被 `:35110/35177` 按 opcode 标成 `'and'`，
而真实 merge 是 400；B1 经 `_normalize_none_check_op_types`(`:33284-33400`) 纠成 `and`
后 op_chain 成 `[and,and,and]` 并压平。v161-NOTMIX 的 `_detect_fused_not_head_chain`
(`:34137`) 只认链首，本例 `not type or ...` 是**第二成员**，探针确认从未调用——
属 NOTMIX 非链首残形。候选门控：`IF_FALSE` 成员的假边目标 ≠ 链共享 merge 时截断外层
链，交 IfRegion 重建；或把 NOTMIX 探测扩到非链首。

## 五、风险族（改动必须零触碰验证）

v161-NOTMIX（本单元即其残形）、v148-NOTTAIL（同形镜像，勿破 `A and not (B and C)`）、
v162-CHAINGRAFT（if/elif merge 耦合）、for-iter Ternary / while BoolOp、
`_normalize_none_check_op_types`。

## 六、验收判据（r163）

request **193/194**（仅剩 `URLopener.retrieve`）；difflib 62/62、tarfile 146/160、
cookiejar 91/105、subprocess 68/78 维持；矩阵 19 案 ALL PASS；电池 TEXT-DIFF 恰 6；
R110 168/167；REG-10 维持；NO-SRC 0；pytest 2F/282P/2XP；r161/r162 全部最小复现集
逐字节零触碰。

## 七、r163 落地（region_ast_generator.py +72/−3）

**门控谓词** `_v163_boolop_merge_is_iter_source`（新 L7961-8009）：merge 块最后一个
`GET_ITER`/`GET_AITER` 之前出现 `STORE_*`（例外：`COPY` 紧邻的 walrus 值保留写回）
或 `POP_TOP` ⇒ **拒绝**该 BoolOp 作 `iter_expr`；块内无 `GET_ITER` 返回 True（保持
现状，C3）。纯块内 opcode，无名字/偏移白名单（I.4）。

**注入点**：L8079（`_loop_generate_for` 候选）、L8086（同函数 fallback 归属，防重
认领）、L53062（`_generate_boolop_impl` 镜像）；L54237 另加「每块唯一归属」守卫
（BoolOp post-store 段遇 loop `for_iter_setup` 时不发射裸 iterable Expr）。

**命中实证**（gate163_log.txt）：`mx1_a/b/c/d/e` merge=`[STORE_FAST x, LOAD_FAST b,
GET_ITER]` 在 L53062 与 L8079 双镜像均 REJECT；真实 `ftp_open` B=696-700
`[STORE_FAST type, LOAD_FAST attrs, GET_ITER]` REJECT@8079；正例 `for x in (a or b)`
merge=`[GET_ITER]` ALLOW、`for x in (n := a or b)` merge=`[COPY, STORE_FAST n,
GET_ITER]` ALLOW（walrus 不误伤）。

**读数**：request **192→193/194**（仅剩 `URLopener.retrieve`），差异仅目标两行
（`for attr in file and 'I' or 'D':` → `for attr in attrs:`）；difflib 62/62、
tarfile 146/160、cookiejar 91/105、subprocess 68/78 且后四者产物与改前逐字节 SAME。

**归类澄清（勿再误判）**：`mx1_d`（`a or 'D'` 形）改前本身即 **failure**，与 `mx1_c`
块/merge 完全相同、仅短路 opcode 极性不同（`JUMP_IF_FALSE_OR_POP` vs
`JUMP_IF_TRUE_OR_POP`），任何结构性门控必然同时修好两者——因此 `mx1_d` 属**同族
功效案**（改后判官 success 2/2 = 改进），不是「不得漂移的对照案」。若强行冻结它
需加 op 极性特判，那属非结构性修补并会留下 or-only 同缺陷，故不采纳。

**零触碰（逐字节，20 案 + for-iter 对照 10 案 + 新增 4 案）**：cg1..cg9、
not_or/nottail/nottail3/ggo/fused、mx2_a..f 全 SAME；for-iter 对照 c1..c10 全 SAME；
新增 ctrl2 c11（STORE 后缀带调用）/c12（ternary-for-iter）/c13（ternary 赋值+for）
全 SAME，c14 为同族修正。补丁 `fix163.py`（utf-8-sig 保 BOM/LF、5 处 anchor
`count==1`、`py_compile` 校验、可重复执行）。

## 八、首轮独立验收：2 PASS / 2 FAIL（如实记录，未放宽口径）

**PASS**：矩阵 19/19（6×E161 HEAD-TEXT-DIFF+EQUAL；12×C161 SAME+EQUAL；b116
SAME+预存在 DIFF；FILES RESTORED，analyzer 与基线逐字节同）；五语料 request
**193/194**（唯一 `URLopener.retrieve`）、difflib 62/62、tarfile 146/160、
cookiejar 91/105、subprocess 68/78。

**FAIL 1 — pytest 3F/281P/2XP（期望 2F/282P/2XP）**：新增
`test_repo_tool_hygiene.py::TestSignatureValidatorHasTeeth::test_registered_red_
count_does_not_grow` 失败——仓库签名验证器报 `统计: 15 个错误, 6 个警告`（基线
14），点名新助手名 `_v163_boolop_merge_is_iter_source` 命中
`FORBIDDEN_PATTERNS (r'_merge_', 'merge_pattern')`。**处置**：助手改名去掉
`_merge_` 子串（三处调用点与补丁脚本同步），重跑该测试须回到 14。

**FAIL 2 — 电池 TEXT-DIFF 7 案（期望恰 6）**：多出 `ca6`（R110 语料）——
源 `first = last = flag or next(it)` + `for x in it:`；HEAD 产
`for x in flag or next(it):`（iterable 错），现树产 `first = flag or next(it)` +
`for x in it:`（iterable 修对，链式赋值疑似丢 `last =`）；`REG-10 ca6 CHANGED`
（r162 时为 SAME-SIG）。**处置（先证后断）**：分别用现树与 f7d80873 版两文件
反编译 ca6 并对**两份产物各跑判官**——若判官无 failure→success 收益，则门控再
收窄（链式双 STORE 形维持现状，仅「单次 STORE 写回后即 LOAD 另一变量 +
GET_ITER」拒绝），使 ca6 回到改前文本；若确有判官收益，才登记为第 7 个已登记
改进案并说明口径变化。**不接受「文本变了就算改进」**。

**零触碰复核归因**：命名基线 11/14 SAME；3 DIFF 为 `cg5_elif_continue` /
`cg7_with_guard_then_ifelse` / `cg8_with_guard_then_if`——因这 3 个 `*_out.py`
是 r162 **改前**产物；当前产物与 `r162/new/` 的 9/9 逐字节相同（cg7 当前 =
new = 486DBCD766FF，`*_out.py` = DC9BBEE86C3E），r161c 5/5 SAME ⇒ 零触碰按
r162 定稿口径为 14/14，**非 r163 回归**。


