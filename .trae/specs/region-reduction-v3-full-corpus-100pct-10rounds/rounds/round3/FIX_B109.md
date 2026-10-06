# FIX_B109 — elif 臂 or 短路链把「跳过臂体的出口边」折成臂条件（`if not A(): …` → `elif A or B:`）

轮次：Round 3 / 破口 B109（登记见 `rounds/round3/REVIEW.md` §2.3）。执行人：round-3 修复 agent。
判定尺：`scripts/pyc_verify.py`（未修改、未替代）。所有产物均「先删 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」
重生成（电池 54 臂、9 个语料靶、order_api 全部重生成），**未手改任何 `*OK.py`**。
落地文件：**`core/cfg/region_analyzer.py` 单文件**（`region_ast_generator.py` / `code_generator.py` 零改动）。
字节完整性（改前 → 改后）：`region_analyzer.py` 单前导 BOM（文件内 BOM 计数 1）、全 CRLF、
LF-only 行数 0（31914 → 31978 行，补丁区未做任何整文件换行归一）；`region_ast_generator.py` 未触碰（58576 行全 CRLF、单 BOM）。
Round-2 守卫未扰动：`[R2-B106 …]` ×4、`[R2-B107 …]` ×7、`[R2-B108 …]` ×5 逐条计数复验通过（全在 `region_ast_generator.py`）。

## 0. 落地标记（grep 用）

```
[R3-B109 修复·elif 臂 or 链成员真边同一性核验]
```

| 行（当前字节） | 站点 | 作用 |
|---|---|---|
| 21074 | `_build_elif_region` docstring 追加的六项 ①-⑥ + C1/C2/C3 条款块 | 本票改动面的算法记账（所属方法即改动方法） |
| 21715 | `_build_elif_region._check_elif_chain` elif 臂 or 链行走（21725-21735 的核验代码体） | **判据本体**：候选成员真边必须命中链体入口，核验不过不入链 |
| 21738 | 同函数 `if len(_or_chain) >= 2:` 接受点 | 链长度只统计**已核验**成员；不过则整链弃权（不写 `inline_boolop_chain`、不改 `inner_condition_block`） |

## 1. 误折叠与修复前的具体证据（ORIG ↔ PROD）

靶单元 `<module>.base_order`（`order_api.pyc`，臂头 off **890**，ORIG/PROD 200=200 条 ⇒ 纯边差异）：

```
ORIG  off890 POP_JUMP_FORWARD_IF_TRUE  succ=['jump:197','fall:155']   197 块 = LOAD_FAST order_obj;LOAD_ATTR order_id;RETURN_VALUE
PROD  off890 POP_JUMP_FORWARD_IF_TRUE  succ=['jump:164','fall:155']   164 块 = LOAD_CONST;STORE_FAST;JUMP_FORWARD;LOAD_CONST（臂体首块）
终态块 off1124 的 preds：ORIG [154, 196]  →  PROD [196]（臂前驱被吞）
```

合成孪生 `test_repros/round3/r3_a01_terminal_return_join_absorbed.pyc`（同形，块号不同）逐块事实：

```
B40  off 66 last=POP_JUMP_FORWARD_IF_TRUE  succ=[164, 68]  preds=[12]     ← `not is_trade()` 的跳过边
B112 off112 last=POP_TOP                    succ=[164]      preds=[102,108] ← 臂体末落穿
B164 off164 last=RETURN_VALUE                succ=[]         preds=[40, 112] ← 共享终态汇合块
```

修复前产物（`r3_a01…OK.py` / `order_apiOK.py:56-63` 原文）：

```python
    if o is None:
        return None
    elif is_trade() or o.symbol[:2] in ('11', '12'):
        info = 'CB'
    else:
        info = 'STK'
    LOG.info(info)
    return o.order_id
```

修复后（同一产物文件，sanctioned 重生成；`order_apiOK.py:56-64` 同形）：

```python
    if o is None:
        return None
    elif not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
```

臂跳恢复为「→ 终态块」的入口引用，终态块的两条前驱（40/112）复原，臂体回到 `if not A()` 的臂内。
`_r2diag.py diff` 对该 pyc 首分歧行消失，判据 `single` ⇒ `status=success units=2/2`。

## 2. 新增的拒绝条件与它读的白名单判据

`_check_elif_chain`（`_build_elif_region` 内嵌）为下一条 elif 臂收集 or 短路链时，臂头块（块末 IF_TRUE 族跳转）的
跳转落点被**假定**为「链体入口 T」。旧码在行走里已经把「成员真边是否命中 T」写出来了
（21677-21681：`_or_ft == _or_body_block` 的两个分支都 `break`），但成员**先 append 后核验、核验结果被丢弃**，
链长按未核验的收集计，于是 `if not A(): <臂体>` 的**出口边**（A 真 → 跳过臂体直达作用域续行块）被当成链成员真边，
链成立 ⇒ `not A` → `A or B` 折叠、臂体无条件执行、终态块丢臂前驱。

修复后的判据（只读白名单结构事实）：

* **块末 opcode**：候选成员必须以后向条件/短路跳转结尾（既有判据，不变）。
* **后继归属同一性**：`IF_TRUE` 族成员的**跳转目标**、`IF_FALSE` 族成员的**非跳转后继（落穿边）**必须恰为 T；
  命中才 `append` 入链（`IF_FALSE` 命中即链末），不命中即断链且**不入链**。
* **前驱/成员关系后果**：T 同时被链外同层前向路径汇入（臂体末尾落穿，实测 preds `[154,196]` / `[40,112]`）时，
  第二成员的真边必然不再命中 T，判据自动拒折叠 —— 即「终态块是父级兄弟序列的汇合点、不属本链」由
  成员真边同一性表达，无需额外谓词。

零名字/函数名/文件名白名单、零绝对偏移、零深度或操作数计数上限、无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`
新方法（改动落在既有 `_build_elif_region`/`_check_elif_chain` 内）、无文本级改写；识别阶段一次定形，
链不成立时不写 `inline_boolop_chains`、不改 `inner_condition_block`，AST 端据臂头 IF_TRUE 与 then/else 归属
自然取反为 `elif not A():`，终态块由父级兄弟序列发射 —— 符合 §1.3 单向数据流（未做发射后回溯修正）。

**已实测后删除的候选形（如实登记，避免留下零命中守卫）**：先落地过一版显式前驱谓词
`RegionAnalyzer._elif_or_chain_join_is_shared(body_entry, chain_blocks)`（「T 存在链外同层前向前驱 ⇒ 拒绝」），
与判据 (1) 并行；在 52 臂 + `order_api.pyc` + `quotation.pyc` 共 54 个文件上插桩统计其返回 True 次数 = **0**
（成员真边同一性核验已先行断链），故属零命中启发式，已整段移除（方法与调用点均不残留，
`grep _elif_or_chain_join_is_shared` = 0 命中）。

## 3. 门禁读数（全部为本次实测原文，判据 `scripts/pyc_verify.py`）

| 命令 | 修复前 | 修复后 | 结论 |
|---|---|---|---|
| `batch --index test_repros/round3/r3_probe_index.json`（52 臂认证基线） | 84/114 units，52 文件 = 22 success / 30 failure | **93/114 units，52 文件 = 31 success / 21 failure** | +9 文件 / +9 单元 |
| 同上（追加两条永久臂后 54 臂） | — | **97/118 units，54 文件 = 33 success / 21 failure**，`compile_error=0 error=0` | 新臂 2/2 + 2/2 success |
| B109 的 11 标本 | 全 MISMATCH | **9 转 MATCH**：`a01 a03 a05 a07 a09 a11 a12 a13 a15`；仍红 `a08`（测试工程师标记的自我否证臂，非本票证据）、`a14` | 9/11 |
| B109 的 4 对照 `a02 a04 a06 a10` + `c07` | MATCH | **MATCH（保持）** | 无过伸展 |
| 其余 19 条红臂（B110/B111/B112/B113 + B100/B104 实例） | MISMATCH | **MISMATCH（不变）**，`partial-change` 单元数变化 = 0 | 未越界 |
| `single site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | 34/37 | **35/37**（`base_order` 翻转；`future_order`/`option_order` 见 §4） | 未达 37/37 |
| `batch --index test_repros/round2/r2v3_probe_index.json` | 105/126，41 success / 21 failure | **105/126，41 / 21** | 保持 |
| `batch --index test_repros/round1/r1_probe_index.json` | 108/110，44 / 2 | **108/110，44 / 2** | 保持 |
| `batch --index test_repros/round1/r1_regress_index.json` | 34/34，17 / 0 | **34/34，17 / 0** | 保持 |
| `single site-packages/fly/data/quotation.pyc` | 152/153 | **152/153，失败单元仍 `<module>.get_fundflow_day`** | 保持、单元未换 |
| `single …/IQCommon/util/cgroup_utils.pyc` / `email_utils.pyc` / `IQData/utils/calexrights_func.pyc` | 8/8 · 4/4 · 8/8 | **8/8 · 4/4 · 8/8** | 保持 |
| `single …/plugin_system_trade/function.pyc` | 70/71 | **70/71** | 未跌 |
| `single …/IQEngine/core/bar.pyc` | 84/85 | **84/85** | 未跌 |
| `single …/fly/data/quote_handler.pyc` | 78/79 | **78/79** | 未跌 |
| `single …/plugin_system_matcher/matcher.pyc` | 16/17 | **16/17** | 未跌 |
| `pytest -q …（6 个测试文件）` | 2 failed / 277 passed / 2 xpassed | **2 failed / 277 passed / 2 xpassed**（同两条 `TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`TestBoundaryConditions::test_BOUNDARY_02_large_function`） | 保持 |
| `import core.cfg.region_analyzer, region_ast_generator, code_generator` + `compileall -q core` | ok | **ok / ok** | — |

## 4. 未闭环部分（如实登记）

* **`order_api.pyc` 为 35/37 而非 37/37**。`future_order`(115→88) / `option_order`(94→55) 的 **B109 边差异已消失**：
  `_r2diag diff` 中 off412 / off204 的 `POP_JUMP_FORWARD_IF_TRUE` 目标内容两侧同为
  `LOAD_FAST,LOAD_ATTR,RETURN_VALUE`，终态块前驱复原；残留首分歧改为**臂体语句整体丢失**
  （`delete orig[72:80]` = `strategy_log.info(… .format(…, '买入' if … else '卖出', …))` 被降级为裸三元表达式）。
  该机制读的是「调用实参内嵌三元（TernaryRegion）的语句归属」，与链构造无关，属另一破口面
  （本轮 52 臂中 `r3_a03` 的「先赋值后调 format」同族形已 MATCH，说明差异仅在**三元内联在实参表**这一维），
  不在本票判据面上特判。
* **`r3_a14_three_arm_inner_chain`（三臂内层链）仍红**：边全部正确，首分歧为尾部 `insert`（+2 条），
  产物把终态汇合块发成显式 `else: return o.order_id` 而非落穿 —— 属 else/sink 材料化面（Round-2 §5、B99/B111 同轴），
  非本票的折叠判据。
* **`r3_a08_with_host`**：测试工程师标记的自我否证臂（首分歧在 `with` 退出簿记 + 凭空 `while False: pass`），
  本票未据其换绿，读数仍 1/2。

## 5. 永久臂（已追加，索引读数含它们）

`test_repros/round3/r3_probe_index.json` 追加 2 臂（`.py` → `py_compile` → `.pyc` → sanctioned `pycdc` 产物）：

| 臂 | 要求 | 源码要点 | 实测 |
|---|---|---|---|
| `r3_a16_orchain_real_chain_folds.pyc` | **必须折叠**（防过伸展） | `if o is None: return None` 后 `if is_trade() or o.symbol[:2] in ('11','12'): LOG.info('hit')` ⇒ 两名成员真边同命中链体入口，且入口无前链外前向前驱 | `status=success units=2/2`，产物保持 `elif is_trade() or o.symbol[:2] in ('11', '12'):` |
| `r3_a17_negated_if_empty_then_no_fold.pyc` | **必须不折叠** | `if not is_trade(): if o.symbol[:2] in ('11','12'): pass else: LOG.info('skip')` + 尾 `return o.order_id` —— 臂头真边是出口边，第二成员真边不命中该出口 | `status=success units=2/2`，产物 `elif not is_trade():` + 完整内层 if/else |

```
$ python -X utf8 scripts/pyc_verify.py batch --index test_repros/round3/r3_probe_index.json --json D:/Temp/rrv3/r3_final.json
files_total=54  units_total=118  units_success=97  files_by_status={'success': 33, 'failure': 21, 'compile_error': 0, 'error': 0}
```

## 6. 声明

**「代码已落地」**：判据已写入 `core/cfg/region_analyzer.py`（3 个 `[R3-B109 修复·elif 臂 or 链成员真边同一性核验]`
标记站点，见 §0 表），Round-3 电池 9 标本翻转 / 4 对照与 19 条非本票红臂零变化、Round-2 与 Round-1 三批读数逐位不变、
9 个语料哨兵零回退、pytest 同两条失败。B109 的**边折叠机制在本票判据面上已闭**（`base_order` 与 9 条合成臂为证）；
`order_api.pyc` 未达 37/37，残余两单元是 §4 登记的臂体语句丢失（不同构造），未以拒绝形换绿。
