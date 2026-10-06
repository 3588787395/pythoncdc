# FIX_B100_REGRESS — B100 arm-join 附带回退 `strategy_info_utils.get_strategy` 的封闭（round 1 / 单族窄口径）

分支 `rr-v3r01-f557fd`。本文只处理未提交 B100（`_compute_arm_level_join` /
`_armjoin_is_skip_edge`）带来的 1 个 collateral 回退
（`site-packages/IQCommon/util/strategy_info_utils.pyc` 30/30 → 29/30，
`<module>.get_strategy: Failure: Different control flow`），不动 B99/B101，
不改 `region_ast_generator.py` / `code_generator.py`，不重构、不扩域。

落地面：`core/cfg/region_analyzer.py` **单文件**，守卫标记
**`[r3-b100-armjoin-tailexit]`**（代码侧 4 处：方法 docstring 的 (4b) 项、
`_arm_declared_exit` 的 docstring、`_arm_exit` 消费点注释、接受分支注释；
守卫体内另有区域成员截断注释）。B100 既有判据 (1)…(6) 与
`_armjoin_is_skip_edge` **逐字未动**，本次只做**严格附加**：新增一条
「认领」分支，不删除、不放松任何既有拒绝条件。

---

## 1. 第一分歧实测（修复前产物 vs 原始 pyc，逐指令）

复现步骤（产物一律重新生成，未手改 `*OK.py`）：

```
del site-packages/IQCommon/util/strategy_info_utilsOK.py
python -X utf8 pycdc.py -o site-packages/IQCommon/util/strategy_info_utilsOK.py site-packages/IQCommon/util/strategy_info_utils.pyc
python -X utf8 scripts/pyc_verify.py single site-packages/IQCommon/util/strategy_info_utils.pyc
  → status=failure units=29/30  ***<module>.get_strategy: Failure: Different control flow
```

`dis.get_instructions` 逐条对比（原 `get_strategy` code 对象 vs
`compile(OK.py)` 里同名对象，纯位移伪差 = 同一 `(opname, offset)` 槽位上
argval 才比）：

| 项 | 原始 pyc | 修复前产物 |
|---|---|---|
| 指令条数 | 385 | **384**（少一条跳转） |
| 首个真分歧 | 线性 idx 183 / off **1036** / `JUMP_FORWARD` argval **1088** | off 1036 / `LOAD_GLOBAL`（直接落入下一语句） |

原始字节码（`get_strategy`，行 211-222）：

```
211  934 POP_JUMP_FORWARD_IF_FALSE 1286      <- 外层 if is_encryption in (…) / elif 链
212  936 …PyRead_AES_Binary…; 978 error_no==0
     988 POP_JUMP_FORWARD_IF_FALSE 1038      <- 内层 if error_no == 0（本单元）
214  990 content = aes_decrypt(…); 1032 strategy['content'] = content
    1036 JUMP_FORWARD 1088                    <- ★ 臂尾自声明的作用域出口
217 1038 system_log.error(…); 1086 RETURN_VALUE   <- else 臂终态，永不汇入
220 1088 LOAD_GLOBAL IS_ENCRYPTION …          <- ★★ 紧随 if 链的同层兄弟语句入口
    1284 JUMP_FORWARD 2068
225 1286 elif IS_ENCRYPTION in (…) …          <- 外层链下一条臂
```

即：内层 `if error_no == 0:` 的臂级 merge 应为 **1088**，修复前取到 **2068**
（外层 if/elif 链的汇合块），`_collect_branch_blocks` 于是把 1088..2068
的兄弟语句全部吸进 then 臂，`JUMP_FORWARD 1088` 失去落点而整条消失
（384 vs 385）。产物里对应的构造（`grep` 实测）是
`if IS_ENCRYPTION == ENCRYPTION_MODE_0:` 被排到 `if error_no == 0:` 的
**then 臂内部**、而 `else: … return None` 退到其后。

调用点实测（`_compute_arm_level_join` 插桩，本 pyc 共 116 次调用，
`get_strategy` 的 CFG 有 26 块）：

```
arms=(990,1038) current_merge=None   -> 返回 2068   ← 过度外推（缺陷）
arms=(936,1286) current_merge=None   -> 返回 None   ← 外层链原判（应保持）
候选层实测：L0 blk 1088 labels=['0']（唯一前驱 990，块末 JUMP_FORWARD→1088）
           L2 blk 2068 labels=['0','E','N']（E 来自 1286/1330/1758/2010 的跳过边）
```

---

## 2. 缺的成员条件（判定哪一侧错）

错在 **`_compute_arm_level_join` 认领了 2068**（本应 1088）。判据 (4)
要求「箱数 ≥ 2 **且** E 箱非空」，而本形状里另一臂（1038）以
`RETURN_VALUE` 收束、根本不参与前向汇合 ⇒ 真汇合块 1088 的正常前驱
**只有汇入臂自己一个箱**，(4) 永不同时成立；BFS 遂越过它，在更外层撞上
「与**外层 if/elif 链**的其他臂汇合」的块——那里的 E 证据
（1286/1330/1758/2010 的 `POP_JUMP_FORWARD_IF_FALSE` 跳过边）是
**相对外层链**的同层兄弟路径，不是本 if 的同层兄弟路径。

缺失的成员条件（补为 (4b)）：其余臂全部 `_exhausted`
（块末 ∈ `_ARMJOIN_EXIT_OPS`，或只有回边/异常边 = continue/break）时，
汇入臂的**直落尾块**——自臂入口沿「块末非任何跳转/非终态、且恰有一个
前向正常后继」的链走到的最后一块——以**无条件前向跳转**
（`JUMP_FORWARD`/`JUMP_ABSOLUTE`）收尾且落点恰为 J ⇒ J 即该臂自己声明的
作用域出口 = 同层最近汇合块。截断条件：链一旦走进 `_sub_arm`
（按区域成员关系折算的臂内已归约子区域块，try/with/循环体…）即不成立。

两条负例由该截断/形态条件挡住（各自实测）：

* `IQCommon/util/strategy_info_utils.get_strategy` 的 `if os.path.exists(…)`
  @234：臂入口是 try 的 NOP 块，直落链 234→236 走进 TryRegion 内部，
  376 的 `JUMP_FORWARD 494` 属于 try 语句自身 ⇒ `_cur in _sub_arm` 截断。
  （第一版实现未加此截断，本 pyc 掉到 25/30，5 个单元回退。）
* 外层链调用 `(936,1286)`：臂 936 的尾块块末是 `POP_JUMP_FORWARD_IF_FALSE`
  （条件跳过边，属内层 `if error_no==0` 结构自身），非无条件跳转 ⇒ 不认领，
  原判 None 逐字保留。

---

## 3. 落地的守卫与白名单谓词

读的唯一谓词：**块末终止 opcode**（`RETURN_VALUE/RETURN_CONST/RAISE_VARARGS/RERAISE`
= 既有 `_ARMJOIN_EXIT_OPS`；`_R20_FWD_JUMPS` = `JUMP_FORWARD/JUMP_ABSOLUTE`；
`CONDITIONAL_JUMP_OPS` / `SHORT_CIRCUIT_JUMP_OPS` / `BACKWARD_JUMP_OPS` 作截断）、
**前驱/后继关系**（`_normal_succ` 排除异常边、`start_offset` 单调前向、
唯一后继）、**区域成员关系**（`self.regions` → `_sub_arm`）。
零名字/零绝对偏移阈值/零深度/零计数上限/零文件名特判；`_compute_arm_level_join`
的消费点仍只有 `_identify_conditional_regions` 一处，方法名不违 §2 禁用前缀。
rules.md §1.2 原则2（1088 归还父级兄弟序列）/ 原则3（子区域内部块不认兄弟）
+ §1.5 C1（只读本区域两臂出边）/ C2（不窥子区域内部）/ C3（显式认领被父级
入口引用的汇合块）。

---

## 4. 门禁读数（before → after，全部在最终代码态实测）

| 命令（`python -X utf8 …`） | B100 未修（回退态） | 本单落地后 | 要求 |
|---|---|---|---|
| `scripts/pyc_verify.py single site-packages/IQCommon/util/strategy_info_utils.pyc` | 29/30 failure | **30/30 success** | 30/30 |
| `… single site-packages/IQCommon/util/email_utils.pyc` | 4/4 | **4/4 success** | 保持 4/4 |
| `… single IQData/utils/calexrights_func.pyc` | 8/8 | **8/8 success** | 保持 8/8 |
| `… single IQData/plugins/plugin_system_fly_basicdata/calexrights_func.pyc` | 8/8 | **8/8 success** | 保持 8/8 |
| `… single fly/simtradding/ptradeAccount.pyc` | 137/137 | **137/137 success** | 保持 |
| `… single IQEngine/core/executor.pyc` | 10/10 | **10/10 success** | 保持 |
| `… single IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc` | 19/19 | **19/19 success** | 保持 |
| `scripts/pyc_verify.py batch --index test_repros/round1/r1_probe_index.json --json D:/Temp/r1_b100fix.json` | 108/110, 44 success / 2 failure | **108/110, 44 success / 2 failure**，失败恰为 `_search/handler_ifelse.pyc`(B101) 与 `r1_73_cand_fortry_sinkpair.pyc`(B99) | 108/110，仅这两个 |
| `scripts/pyc_verify.py batch --index test_repros/round1/r1_regress_index.json --json D:/Temp/r1_regress_after.json` | 14/14（7 臂） | **26/26（13 臂，新增 6 臂全 MATCH）** | 不降 |
| `… single site-packages/fly/data/quotation.pyc` | 152/153 | **152/153**（仍只 `<module>.get_fundflow_day`） | 不得新增失败 |
| `… single IQCommon/util/cgroup_utils.pyc` | 8/8 | **8/8 success** | 保持 |
| `… single IQEngine/plugins/plugin_system_accounts/__init__.pyc` | 6/6 | **6/6 success** | 保持 |
| `… single …/account_model/benchmark_account.pyc` | 20/20 | **20/20 success** | 保持 |
| `… single …/account_model/stock_account.pyc` | 25/25 | **25/25 success** | 保持 |
| `… single fly/data/quote.pyc` | 85/92 | **85/92**（7 个既有失败，与 B100 读数 84→85 一致） | 不新增 |
| `… single IQCommon/data/finance.pyc` | 31/32 | **31/32**（仍只 `get_fields`，非门禁项） | — |
| `python -X utf8 -m pytest -q --no-header -p no:cacheprovider tests/test_algorithm_correctness.py tests/test_deep_nesting_pressure.py tests/test_control_flow_completeness_matrix.py tests/test_complete_syntax_coverage.py tests/test_boundary_cases.py tests/test_core_functional.py` | 277 passed / 2 failed / 2 xpassed | **277 passed / 2 failed / 2 xpassed**，失败恰为 `test_B01_simple_if_then_else_merge` 与 `test_BOUNDARY_02_large_function` | 保持 |
| `python -X utf8 -c "import core.cfg.region_analyzer, core.cfg.region_ast_generator, core.cfg.code_generator"` | ok | **ok** | clean |
| `python -X utf8 -m compileall -q core` | ok | **clean** | clean |

文件完整性：`core/cfg/region_analyzer.py` 仍全 CRLF（31868/31868），
BOM 恰 1 枚；未整文归一化换行。

---

## 5. 永久臂（synthetic specimens，`test_repros/round1/`）

自建 `compile → py_compile(.pyc) → pycdc(-o *OK.py) → pyc_verify single`，
已追加进 `r1_regress_index.json`（7 → 13 臂，批量读数 26/26 全 MATCH）：

| 臂 | 形状 | 现态 | 三态对照（armjoin-off / tailexit-off / current） |
|---|---|---|---|
| `r1_97_regress_b100reg_tailexit_if_host` | get_strategy 原形：外层 if/else 链 + 内层 if 的 else 臂 return + 臂内同层兄弟 if | MATCH | MATCH / **DIFF** / MATCH |
| `r1_99_regress_b100reg_tailexit_func_host` | 函数宿主：臂尾无条件跳转 + 对侧 return + 兄弟语句 | MATCH | MATCH / **DIFF** / MATCH |
| `r1_98_regress_b100reg_tailexit_try_stop` | try 宿主 `if path:`：臂入口进 TryRegion（§2 截断负例） | MATCH | MATCH / MATCH / MATCH |
| `r1_100_regress_b100reg_tailexit_loop_cont` | 循环宿主：else 臂 `continue`（回边收束）+ 臂内兄弟 if | MATCH | MATCH / MATCH / MATCH |
| `r1_101_regress_b100win_try_chain_seq_tail` | B100-win 形：try 体内 if 链，链后同层兄弟序列 | MATCH | MATCH / MATCH / MATCH |
| `r1_102_regress_b100win_elif_arm_tailjoin` | B100-win 形（calexrights 形）：elif 臂内嵌套 if/else 一臂 return + 兄弟赋值 | MATCH | MATCH / MATCH / MATCH |

`r1_97` / `r1_99` 在关掉本守卫（`_get_jump_forward_target` 置 None 以模拟
(4b) 缺失）时 **DIFF** ⇒ 二者真正钉住本次补齐的成员条件；
其余四臂是「不得变化」的截断/宿主负例。B100 的 E 判据收益在合成件上
未能单独复现（既有 7 臂同样对 armjoin-off 不敏感），其永久证据由
`email_utils` 4/4、两处 `calexrights_func` 8/8、`quote` 85/92 的
whitelist 门禁承担。未动 `r1_probe_index.json` 与 `REVIEW.md`。

试写过 `r1_103_regress_b100win_try_chain_return_arm`（try 体内
`if perm=='1'` 链 + return 臂 + `info['n']=1` 兄弟）：**三态皆 DIFF**，
即与 B100/本守卫无关的既有缺陷形状（疑似 B99/B101 族），为避免把已知
失败混进永久臂已删除，未落任何文件、未记入索引。

---

## 6. 声明

**「代码已落地」**：`core/cfg/region_analyzer.py` 单文件，严格附加
（新增 `_arm_declared_exit` + 一条认领分支 + docstring (4b) + 区域成员截断），
grep 标记 **`[r3-b100-armjoin-tailexit]`**（代码侧 4 处命中：
`3122` docstring (4b)、`3221` `_arm_declared_exit` docstring、
`3297` `_arm_exit` 消费点注释、`3319` 接受分支注释；另 `3234`
区域成员截断注释属同一守卫体内）。**B100 的 `region_analyzer.py` 改动
无需回退**：`strategy_info_utils` 回到 30/30，三条 B100 收益
（email_utils 4/4、两处 calexrights 8/8）与 108/110 电池、13 臂永久臂、
六个 pytest 套片读数全部保持。
