# FIX_B115 — finally 正常副本前缀在 handler 臂终态块被二次物化（**代码已落地**）

轮次：Round 3 / 单票 B115（靶 `site-packages/fly/common/future_contract_info.pyc` 28/29 → **29/29**）
执行人：round-3 B115 修复 agent
判定尺：`scripts/pyc_verify.py`（未修改、未替代）。所有被判产物均先删后由
`python -X utf8 pycdc.py -o <base>OK.py <base>.pyc` 重生成；未手改任何 `*OK.py`。
落地文件：**单个** `core/cfg/region_ast_generator.py`（`core/cfg/region_analyzer.py` 零改动）。

---

## 0. 落地标记与站点（grep 用）

```
[R3-B115 修复·handler 臂终态块 finally 副本前缀唯一归属]
```

| 站点 | 行（落地后实测） | 作用 |
|---|---|---|
| 新方法 `_handler_arm_block_is_finally_copy`（def 行 31583，六项 docstring ①-⑥ + C1/C2/C3） | 31583 | 归属裁决判据本体 |
| `_generate_try` handler 臂块遍历接线（RETURN 分支之前，标记注释行 30297） | 30297 | 命中时交回块级归约 `_generate_block_statements` |

`grep -c "\[R3-B108" = 5`（round-2 守卫原样保留）、`grep -c "R3-IFEXP" = 0`、
`grep -c "_handler_arm_block_is_finally_copy" = 3`（def + 调用 + docstring 首行）、
`grep -c "_b115_" = 39`（本票局部变量前缀）。

**实测命中计数（猴子补丁计数器统计谓词返回 True 的次数，脚本 `D:/Temp/rrv3/b115_measure2.py`，
仓库内零残留）**：

| 被试 | 谓词询问次数 | 其中块在本区域 `finally_copy_blocks` 台账内 | **判据 True** |
|---|---|---|---|
| `fly/common/future_contract_info.pyc` | 9 | 1 | **1**（`FutureInfoCache.check_user` 处理器臂块） |
| `test_repros/round3/r3_a18_…`（孪生） | 3 | 1 | **1** |
| `test_repros/round3/r3_a19_…`（must-not-fold 对照） | 3 | 1 | **1**（但块级归约产出 `Expr+Return`，被 `all Return` 接管闩锁拒绝 ⇒ 不折叠，见 §4） |
| `IQCommon/strategy/wizard_quant_api.pyc`（B112 宿主） | 7 | **0** | **0** |
| `IQEngine/plugins/…/order_api.pyc`（B114 宿主） | 3 | 0 | 0 |

⇒ 守卫**不是零命中摆设**：在靶文件与孪生上各命中 1 次并翻转单元；在 B112/B114 宿主上命中 0 次，
两文件读数原样不变。

---

## 1. 首分歧证据：修复前

`python -X utf8 scripts/pyc_verify.py single …/future_contract_info.pyc`（认证 HEAD `78d4af25` 代码）
→ `status=failure units=28/29`，唯一红单元 `***<module>.FutureInfoCache.check_user: Failure: Different control flow`。

`python -X utf8 test_repros/round3/_r3_firstdiff.py <pyc> <OK.py> check_user`：

```
[FutureInfoCache.check_user] first_diff @72 (orig 150 instrs / decomp 155)
 >> o72: (488, 'POP_JUMP_FORWARD_IF_TRUE',  942)    d72: (488, 'POP_JUMP_FORWARD_IF_TRUE',  992)
```

即**首条真分歧是跳转目标漂移**，漂移源在其后：`or` 链第二条成员的臂（off488 的 TRUE 边）在
orig 汇入 off820 的 release 块，prod 汇入 off870 的第二条同值 release 块（+5 条计入指令 =
`LOAD_FAST/LOAD_ATTR/LOAD_METHOD/CALL/POP_TOP` 副本，`PRECALL` 为 diff 尺噪声不计）。

逐指令对照（`D:/Temp/rrv3/b115_dump.py`，ORIG 166 / PROD 172 live）：

| ORIG（异常臂） | PROD（异常臂） |
|---|---|
| 816 `POP_TOP` | 816 `POP_TOP` |
| 818 `POP_EXCEPT` | **818-866 release 副本 #1（异常栈仍未弹出）** |
| 820-868 `self.lock.release()` | 868 `POP_EXCEPT` |
| 870 `LOAD_CONST 2` / 872 `RETURN_VALUE` | **870-918 release 副本 #2** |
| — | 920 `LOAD_CONST 2` / 922 `RETURN_VALUE` |

被复制的块 = **`finally` 体的 release 块（清理段）与其后臂自身终态 `return 2` 融合成的单个基本块**
（CFG 中该臂块 `preds=[816]`、`last=RETURN_VALUE`，release 与 return 之间无跳转，不可按块切开）。
产物文本因此是 `except BaseException: self.lock.release(); return 2` + `finally: self.lock.release()`
（臂内多一条 release）；ORIG 的真实源码是 `except BaseException: return 2` + `finally: self.lock.release()`
（已用候选源 `except: return 2 / finally: release()` 重编译逐指令核对，与 ORIG 尾部 816-944 全等）。

**为何产物无法汇入**：`finally` 正常路径副本的归属台账 `TryExceptRegion.finally_copy_blocks`
（本函数实测含 try 体内联点与臂内联点）在**块级**归约里早已被消费
——`_generate_block_statements` 的 inlined-cleanup 分支（`region_ast_generator.py:53554-53659`，本票落地后行号；编辑前为 53462-53567）
判「块 ∈ `finally_copy_blocks` + 块末 opcode ∈ `RETURN_*` + 用户指令前缀 = finally 体序列」时
**剥掉清理前缀、只重建 `Return(value)`**，try 体两条臂（off604-652、off744-792）正是走这条路，
所以 `return 2` / `return 1` 都只有一份。**唯独 handler 臂遍历**
（`_generate_try` 的 `for hb in handler_blocks`）先于该归属查表直接调
`_generate_handler_body_statements(hb)`，该方法只按 opcode 过滤异常框架指令，
把块内 release 段当作臂自己的语句发射 ⇒ 同一段清理代码被第二个归属方再物化一次，
`POP_EXCEPT` 随之被推后，控制流形状不等价（判据报 `Different control flow`）。

这是 §1.2 **原则2 每块唯一归属**的 **OVER-claim 面**（与 B99 双 sink 塌陷的 under-claim 面相反，
B99 仍开放、非本票）。

---

## 2. 归属规则（新增的唯一判据）

`_handler_arm_block_is_finally_copy(block, region)` —— 只读四类白名单同层事实：

1. **区域成员关系 / 归属台账**：`region` 为 `TryExceptRegion` 且 `has_finally` 且 `finally_blocks` 非空，
   `block.start_offset ∈ region.finally_copy_blocks`（分析器既有台账，本票未新增字段、未新增状态）；
2. **块末 opcode**：`block.get_last_instruction().opname ∈ {RETURN_VALUE, RETURN_CONST}`；
3. **本区域异常副本体序列**：对 `region.finally_blocks` 逐块剥帧噪声
   （`RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG/POP_TOP/JUMP_*/COPY/SWAP/POP_EXCEPT/PUSH_EXC_INFO/RERAISE/PRECALL/RETURN_*`
   与 `LOAD_CONST None`）取用户 opcode 序列；
4. **严格前缀包含**：臂块用户序列长度 > 副本体序列长度且前缀逐项相等
   ⇒ 前缀段归 finally（已发射一次），臂侧只余自身终态。

**归约方式**：命中即把该块交回既有块级归约 `_generate_block_statements`（同一归属口径的**唯一**实现，
不新建第二套发射面），并加接管闩锁：仅当块级归约产出**纯 `Return` 语句**时才接管，
否则原样退回既有 `_generate_handler_body_statements` 路径（C3 保守拒绝，输出与编辑前逐位一致）。
判据不读函数名/文件名/绝对偏移/深度/数量阈值；无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`
命名；无文本级后处理；单向数据流（归属一次裁形，无发射后回溯）。

---

## 3. 修复后证据

```
single site-packages/fly/common/future_contract_info.pyc  -> status=success units=29/29 success_rate=100.00%
_r3_firstdiff.py … check_user                              -> （无任何输出 = 零分歧）
产物 check_user 文本                                        -> except BaseException: return 2 / finally: self.lock.release()
```

---

## 4. B112 与本票判据的关系：**不是同一条**（B112 零改动、原样保留）

对 `site-packages/IQCommon/strategy/wizard_quant_api.pyc` / `<module>.filter_desicion`
（REVIEW §4.1 / `rounds/round2/REVIEW.md` §B112）按同法做了指令对照：该单元 195/197，
首分歧 off **704** `POP_JUMP_FORWARD_IF_NONE`：orig `jump:181`（两成员共享的
`LOAD_CONST None; RETURN_VALUE` 终态 sink，preds `[178,180]`）vs prod `jump:195`，
并在函数末块之后新增第二条同值 sink（+2 指令，preds `[178]`，710 只剩 preds `[180]`）。

形状差异（实测，非推断）：

| | B115（本票） | B112（`filter_desicion`） |
|---|---|---|
| 重复物化的对象 | `finally` 体的**清理语句段**（与臂终态融合在同一块内） | **终态 sink 块**（`LOAD_CONST None; RETURN_VALUE`）本身，独立成块、独立 pred 集 |
| 归属载体 | `TryExceptRegion.finally_copy_blocks` 台账（异常/正常双副本） | BoolOp 短路链成员汇入臂终态块的边重投（无 finally 概念参与） |
| 判据可读事实 | 块末 opcode + finally 台账 + 副本体 opcode 序列 | 成员真边目标 vs 共享 then 块 preds |
| 本票谓词命中 | 1 | **0**（台账成员 0 / True 0） |

⇒ **不强行合并**：本票未为 B112 添加任何分支。`wizard_quant_api.pyc` 读数 **55/58 未变**，
三条红单元仍是 `filter_desicion`（B112）与 `get_DMI.calculate_di.<genexpr>` ×2（B113），逐条同名。
`order_api.pyc`（B114 宿主）同样 35/37 未变。

---

## 5. 全部门禁读数（判据 = `scripts/pyc_verify.py`；产物全部先删后重生成）

| 命令 | before（认证） | after（本票） | 结论 |
|---|---|---|---|
| `single …/fly/common/future_contract_info.pyc` | 28/29（红：`check_user`） | **29/29 status=success** | **整文件翻转** |
| `batch --index test_repros/round3/r3_probe_index.json`（旧 54 臂） | 97/118，54 文件 = 33 success / 21 failure | **97/118，54 文件 = 33 / 21**（逐位不变，零绿臂变红） | 保持 |
| `batch --index …round3…`（**本票追加 2 臂后 56 臂**） | — | **101/122，56 文件 = 35 success / 21 failure**（+4 单元 / +2 success 恰为两条新臂） | 无回退 |
| `batch --index test_repros/round2/r2v3_probe_index.json` | 105/126，62 文件 = 41 / 21 | **105/126，62 文件 = 41 / 21** | 保持 |
| `batch --index test_repros/round1/r1_probe_index.json` | 108/110，46 文件 = 44 / 2 | **108/110，46 文件 = 44 / 2** | 保持 |
| `batch --index test_repros/round1/r1_regress_index.json` | 34/34，17 文件 = 17 / 0 | **34/34，17 文件 = 17 / 0** | 保持 |
| `single …/fly_api/order_api.pyc` | 35/37 | **35/37** | 未跌 |
| `single …/strategy/wizard_quant_api.pyc` | 55/58 | **55/58**（B112 未动） | 未跌 |
| `single …/fly/data/quotation.pyc` | 152/153，红单元 `get_fundflow_day` | **152/153，红单元仍是 `<module>.get_fundflow_day`** | 未跌、单元未换 |
| `single …/IQCommon/util/cgroup_utils.pyc` | 8/8 | **8/8** | 保持 |
| `single …/IQCommon/util/email_utils.pyc` | 4/4 | **4/4** | 保持 |
| `single …/fly/data/quote.pyc` | 86/92 | **86/92** | 未跌 |
| `single …/IQCommon/api/klinedata.pyc` | 61/64 | **61/64** | 未跌 |
| `pytest -q …6 个测试文件…` | 2 failed / 277 passed / 2 xpassed | **2 failed / 277 passed / 2 xpassed**（同两条：`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`TestBoundaryConditions::test_BOUNDARY_02_large_function`） | 保持 |
| `python -X utf8 -c "import core.cfg.region_analyzer, core.cfg.region_ast_generator, core.cfg.code_generator"` | ok | **ok** | — |
| `python -X utf8 -m compileall -q core` | rc=0 | **rc=0** | — |

未跑 402 文件 8 分片批（由发起方持有全语料门禁）。

**字节完整性**：`core/cfg/region_ast_generator.py` 58576 → **58668 行**（+92），全 CRLF、
bare LF **0**、恰 **1** 个前导 BOM（`open(f,'rb').read()[:3] == b'\xef\xbb\xbf'` 开工前后均为 True）；
`core/cfg/region_analyzer.py` **未触碰**：31978 行 / CRLF 31978 / bare LF 0 / BOM True，与开工前逐字节相同
（开工前 sha256[:16] `a5162443f23d0a11` 的生成器原件已备份于 `D:/Temp/rrv3/b115_backup_gen.py`）。
补丁区按字节插入，未做任何整文件换行归一。

---

## 6. 永久臂（已写入 `test_repros/round3/r3_probe_index.json`，54 → **56** 条，格式与原文件逐字相同）

| 臂 | 形状 | 本票后读数 |
|---|---|---|
| `r3_a18_finally_copy_release_dup_in_handler_arm.pyc` | **重复形标本（must-fold）**：`s.lock.acquire()` + `try: for …: if not m: return 2 / return 1` + `except BaseException: return 2` + `finally: s.lock.release()` —— 落地前 `Different control flow`（臂内多一条 release），落地后 **2/2 success** | 2/2 success |
| `r3_a19_handler_own_release_not_folded.pyc` | **不得折叠对照（must-not-fold）**：标本同宿主，但 except 臂**自带** `s.lock.release()` 且 `finally` 亦 release（源码里两处 release 都真实存在）——谓词虽 True，块级归约产出 `Expr+Return` 非纯 Return ⇒ 闩锁拒绝接管，两条 release 全部保留 | 2/2 success |

两条均为绿臂后方才追加；`test_repros/round1/`、`test_repros/round2/` 两批索引与
`REVIEW.md` / `FIX_IFEXP.md` **零改动**。第 3 条备用标本
`D:/Temp/rrv3/probe2/c1_arm_stmt_diff.py`（臂 release + `finally: s.log.append('x')`，2/2 success）
未追加，避免冗余臂。

## 7. 声明

**「代码已落地」**：单文件 `core/cfg/region_ast_generator.py`，1 处判据 + 1 处接线；
靶文件 `future_contract_info.pyc` **29/29 整文件翻转**；四批电池 + 7 个语料哨兵 + pytest + import/compileall
全部零回退；谓词在靶文件与孪生上实测各命中 1 次（非零命中摆设），在 B112/B114 宿主上 0 命中且读数不变。
**B115 已闭环；B112 / B113 / B114 / B99 与本票正交，原样保留。**
