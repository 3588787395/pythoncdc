# FIX_B103 — `[r3-b100-armjoin-tailexit]` 的收束种类收紧（round 1 / 单族窄口径）

分支 `rr-v3r01-f557fd`。本单只处理 (4b) 守卫带来的 collateral 回退 B103：
`IQEngine/utils/logger/handlers.pyc` 17/17 → 16/17、`IQCommon/logger/handlers.pyc`
29/30 → 28/30，失败单元同为 `<module>.RotatingFileHandler.perform_rollover`
（两文件同一模块的近重复副本 ⇒ 同一形状）。`strategy_info_utils.get_strategy`
（4b 的既得收益，30/30）**必须保持**。

落地面：`core/cfg/region_analyzer.py` **单文件**，只**收紧**既有 (4b) 认领分支
的成员条件，不删除、不放松任何其他判据；B100 的 (1)…(6)、
`_armjoin_is_skip_edge`、`_arm_declared_exit` 的直落链体**逐字未动**。
收紧后标记 **`[r3-b103-armjoin-termexit]`**（代码侧 4 处命中：
`3137` docstring (4b) 的收束种类段、`3203` `_term_exhausted` 声明注释、
`3292` BFS 收束登记分支注释、`3354` 接受分支注释；`3372` 为收紧后的实际条件行）。
原 `[r3-b100-armjoin-tailexit]` 标记 4 处仍在（同一守卫的历史标记，未改名）。

---

## 1. 第一分歧实测（两个形状各读一遍）

### 1a. 反例形状 `perform_rollover`（IQEngine/utils/logger/handlers.pyc）

原始 pyc 逐指令（`RotatingFileHandler.perform_rollover`，行 128-149）：

```
130  106 FOR_ITER 202 / 108 STORE_FAST x / 110..194 src=…; os.path.exists(src)
     194 POP_JUMP_FORWARD_IF_FALSE 200      <- 本 if（header 块 134，arms=(196,200)）
133  196 POP_TOP                            <- break 的迭代器清理
     198 JUMP_FORWARD 306                   <- ★ break 的落点 = **for 区域自己的出口**
     200 JUMP_BACKWARD 106                  <- 对侧臂只有回边（循环续行 = continue 形）
     202..304 for-else 支体（行 135-137）；块末 304 RETURN_VALUE
138  306 LOAD_GLOBAL xrange …               <- ★★ 已在 for 区域**之外**的第二条语句
```

修复前产物（实测读出，`site-packages/IQEngine/utils/logger/handlersOK.py`，
16/17 态）把 `if os.path.exists(src): break` 的 merge 认成了 **306**，
于是 `_collect_branch_blocks` 把 202..304（for-else 支体）与 306..726
（for 区域之后的语句）全部吸进循环体：产物里 `for x in xrange(…)` 的体内
出现 `for i in xrange(x, 0, -1)` + `rename/self._open/return None`，
`else:` 支体被排到其后 —— 首分歧即 **198 的 `JUMP_FORWARD 306` 被降级成
「臂尾汇合跳」，break 的实际作用域出口（for 区域出口）被当成 if 的同层兄弟**。

合成孪生件 `r1_104_regress_b103_rollover_break_forelse.py`（本单新建）逐字复现，
插桩实测（`_compute_arm_level_join` 打印认领）。**收紧前**（旧 (4b) 条件）真文件
与孪生件各一行：

```
真 handlers.pyc ：CLAIM arms=(196,200) struct=[108,196,200] cur=None -> join=306   ← 过度认领
   region LoopRegion FOR_LOOP blocks=[0,106,108,196,200,202,306] has_join=True has_struct=True
孪生 r1_104    ：CLAIM arms=(82,86)  struct=[44,82,86]     cur=None -> join=114
   region LoopRegion FOR_LOOP blocks=[0,42,44,82,86,88,114] has_join=True has_struct=True
```

两处都显示：认领的落点（306 / 114）**同时是外层 LoopRegion 的成员/出口块**
（`has_join=True` 且该区域 `has_struct=True`）——臂尾那条无条件跳转是 `break`
（跨区域跳转），不是 if 链的臂尾跳。**收紧后**同一插桩在真 handlers 文件上
已无任何 `arms=(196,200)` / `join=306` 认领行，单元读数回到 17/17。

### 1b. 正例形状 `get_strategy`（IQCommon/util/strategy_info_utils.pyc）

原始 pyc（行 211-222）：

```
217  988 POP_JUMP_FORWARD_IF_FALSE 1038     <- 内层 if error_no==0，arms=(990,1038)
214  990..1032 content=aes_decrypt(…); strategy['content']=content
    1036 JUMP_FORWARD 1088                  <- ★ then 臂跳过 else 支体的臂尾跳
217 1038..1086 system_log.error(…); RETURN_VALUE   <- 对侧臂**终态**收束
220 1088 LOAD_GLOBAL IS_ENCRYPTION …        <- ★★ 紧随 if 链的同层兄弟语句入口
```

收紧后插桩实测（本单在最终代码态重跑，仍成立）：

```
CLAIM arms=(990,1038) struct=[936,990,1038] cur=None -> join=1088   ← 正确认领，保持
```

反例侧（真 handlers 文件）在同一插桩下已**无任何认领行**（`arms=(196,200)` /
`join=306` 不再出现），单元读数回到 17/17。

---

## 2. 判别条件（discriminator）

两个形状在 (4b) 的旧表述下**完全同形**（单臂汇入 + 臂尾无条件前向跳转 + 另一臂
`_exhausted`），差别只在**另一臂的收束种类**：

* `get_strategy`：另一臂块末 = `RETURN_VALUE`（1086）= **终态收束** —— 控制流从
  本作用域**永久消失**，本 if 只剩一条活臂，该臂自声明的落点 1088 就是紧随 if 链
  的同层兄弟语句入口 ⇒ (4b) 必须成立。
* `perform_rollover`：另一臂块末 = `JUMP_BACKWARD 106`（只有回边）= **回边收束**
  （continue/循环续行形）—— 该臂并未离开本作用域，它把控制交回**外层结构**
  （for 环头）继续迭代，本 if 所在的同层层序尚未结束；此时汇入臂尾那条
  `JUMP_FORWARD 306` 是 `break`，落点是**外层区域自己的出口**（跨区目标，实测
  306/114 属该 LoopRegion 的成员），不是本 if 的同层兄弟语句 ⇒ (4b) 不得成立。

依据：rules.md §1.5 C1（归约只读本区域的出边 —— 回边臂的出边属外层结构）、
C2（外层区域是黑箱，其出口块不得被内层 if 认领）、C3（外层循环的臂尾形态由既有
守卫族 R24A/B3、`_compute_in_loop_if_merge`、`_r57e_in_loop_branch_convergence`
封闭判定，(4b) 不重复认领）+ §1.2 原则2/原则3。

## 3. 落地的收紧（确切条件）

`_compute_arm_level_join` 内新增按**收束种类**分箱的集合，并接受分支的
`all(...)` 改用它（其余代码逐字未动）：

* BFS 里：`_terminal`（块末 ∈ `_ARMJOIN_EXIT_OPS` = RETURN_VALUE/RETURN_CONST/
  RAISE_VARARGS/RERAISE）时除登记 `_exhausted` 外**同时**登记 `_term_exhausted`；
  「只有回边/异常边」的收束只进 `_exhausted`。
* (4b) 接受条件由 `all(_k in _exhausted or _k == _solo …)` 收紧为
  `all(_k in _term_exhausted or _k == _solo …)`。
* 其余部分（`_arm_exit.get(_solo) is _s` 的臂尾直落链判据、`len(_arms) == 2`、
  `_sub_arm` 区域成员截断、E 判据 (4)、(6) 的现-merge 比较）**未放宽也未删除**：
  这是严格收紧，只可能减少认领。

白名单谓词：块末终止 opcode、前驱/后继关系（`_normal_succ` 排异常边、
`start_offset` 单调前向、唯一后继）、区域成员关系。零名字/零绝对偏移阈值/
零深度/零语句计数/零文件名/函数名特判（§2 合规）。

---

## 4. 门禁读数（before → after，after 全部在最终代码态重新生成产物后实测）

| 命令（`python -X utf8 …`） | 本单前（B103 现态） | 本单后 | 要求 |
|---|---|---|---|
| `pyc_verify.py single site-packages/IQEngine/utils/logger/handlers.pyc` | 16/17 failure（`perform_rollover`） | **17/17 success** | 17/17 |
| `… single site-packages/IQCommon/logger/handlers.pyc` | 28/30（`_target` + `perform_rollover`） | **29/30**，只剩 `TWHThreadController._target`(B99) | 29/30 |
| `… single site-packages/IQCommon/util/strategy_info_utils.pyc` | 30/30 | **30/30 success** | 保持 |
| `… single site-packages/fly/data/quotation.pyc` | 152/153 | **152/153**（仍只 `get_fundflow_day` = B102） | 不新增 |
| `… batch --index test_repros/round1/r1_probe_index.json --json D:/Temp/r1_b103.json` | 108/110，44 success / 2 failure | **108/110，44 success / 2 failure**，失败恰为 `_search/handler_ifelse.pyc`(B101) 与 `r1_73_cand_fortry_sinkpair.pyc`(B99) | 保持 |
| `… batch --index test_repros/round1/r1_regress_index.json --json D:/Temp/r1_b103_regress.json` | 26/26（13 臂） | **34/34（17 臂，新增 4 臂全 MATCH）** | 全 MATCH |
| `pytest -q … 六个套片` | 277 passed / 2 failed / 2 xpassed | **277 passed / 2 failed / 2 xpassed**，失败恰为 `test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function` | 保持 |
| `-c "import core.cfg.region_analyzer, core.cfg.region_ast_generator, core.cfg.code_generator"` | ok | **import ok** | clean |
| `-m compileall -q core` | ok | **clean** | clean |

不得回退项（同样在最终代码态重新生成产物 + 单测读数，全部保持）：
`IQCommon/util/cgroup_utils` **8/8**、`IQCommon/util/email_utils` **4/4**、
`IQData/utils/calexrights_func` **8/8**、
`IQData/plugins/plugin_system_fly_basicdata/calexrights_func` **8/8**、
`IQEngine/core/executor` **10/10**、
`IQEngine/plugins/plugin_fly_data/fly_api/history_api` **19/19**、
`fly/simtradding/ptradeAccount` **137/137**、`fly/data/quote` **85/92**、
`IQEngine/plugins/plugin_system_accounts/__init__` **6/6**、
`…/account_model/benchmark_account` **20/20**、`…/account_model/stock_account` **25/25**。

文件完整性：`core/cfg/region_analyzer.py` 仍全 CRLF（31914/31914），BOM 恰 1 枚，
未整文归一化换行；只动这一个文件（`region_ast_generator.py` 的 `[r1-b98-elsescope]`
 collateral 修复与 B100 主体未触碰）。产物 `*OK.py` 一律重新生成，未手改。

---

## 5. 永久臂（synthetic specimens，`test_repros/round1/`）

自建 `compile → py_compile(.pyc) → pycdc(-o *OK.py) → pyc_verify single`
（用 `test_repros/round1/_run.py`），已追加进 `r1_regress_index.json`
（13 → 17 臂，批量读数 34/34 全 MATCH）。三态 = (4b) 关掉 / (4b) 旧条件（本单
收紧前）/ 现态：

| 臂 | 形状 | 现态 | off(4b 删) | loose(收紧前) |
|---|---|---|---|---|
| `r1_104_regress_b103_rollover_break_forelse` | **perform_rollover 原形**：`for … : if exists: break / else: … return` + 环后第二条语句（回边收束臂 ⇒ (4b) 不得成立） | MATCH | MATCH | **MISMATCH** |
| `r1_105_regress_b103_getstrat_tailexit` | **get_strategy 原形**：外层 if/else 链 + 内层 if 的 else 臂 `return` + 臂尾无条件跳转 + 同层兄弟 if（终态收束臂 ⇒ (4b) 必须成立） | MATCH | **MISMATCH** | MATCH |
| `r1_106_regress_b103_loop_termarm_tailjoin` | 判别构造的另一侧消融：**保留 for 宿主**，把回边臂换成终态 `return` 臂 ⇒ (4b) 在循环宿主里仍须成立（挡「一刀切拒绝循环宿主」的过收紧） | MATCH | **MISMATCH** | MATCH |
| `r1_107_regress_b103_getstrat_noexitarm` | 判别构造消融：get_strategy 形去掉对侧臂的 `return`（两臂都前向汇入）⇒ 由 (4) 的 E 判据承担，(4b) 不介入 | MATCH | MATCH | MATCH |

即：把 `all(_k in _term_exhausted …)` 再 loosening 回 `_exhausted` ⇒ `r1_104` 立刻红；
把 (4b) 整条删掉 ⇒ `r1_105`/`r1_106` 立刻红。既有 `r1_97`（off 态实测 MISMATCH、
loose/tight MATCH）与 `r1_100`（三态皆 MATCH，循环续行负例）继续由本电池覆盖。
未动 `r1_probe_index.json`，未动任何 `REVIEW.md`。

---

## 6. 声明

**「代码已落地」**：`core/cfg/region_analyzer.py` 单文件，严格收紧 (4b) 的成员条件
（新增 `_term_exhausted` 按收束种类分箱 + 接受分支改用终态收束 + docstring (4b)
补写收束种类段），grep 标记 **`[r3-b103-armjoin-termexit]`**（代码侧 4 处命中：
`3137`、`3203`、`3292`、`3354`；条件本体在 `3372`）。
两侧同时成立：`IQEngine/utils/logger/handlers.pyc` **17/17**、
`IQCommon/logger/handlers.pyc` **29/30**（仅剩 B99 的 `_target`）、
`IQCommon/util/strategy_info_utils.pyc` **30/30**；probe 电池 108/110（44/2，
失败恰为 B101/B99）、regress 电池 34/34、pytest 277/2/2 全部保持。
