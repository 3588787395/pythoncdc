# Round 2 修复复核报告（REVIEW2，评审工程师对抗复审）

- 复核对象：commit 124bde37（Round 2 修复批次，基线 = fe486d42 round2 评审产物）
- 复核范围：B8（region_analyzer.py `_collect_pre_check_instrs` except* 帧前缀剔除）、
  R2-O2 移除（exception_handler.py `_find_handler_type_load` + 两处回退替换）、
  B9 装配层（`_try_unify_mixed_boolop_chain` TryRegion 认领豁免 +
  `_detect_boolop_conditional_chain` try_scope_exempt）
- 判据：唯一判据 `python scripts/pyc_verify.py single <pyc> --source <pycdc 重生成产物>`
  （pylingual compare_pyc 逐单元）；对照基线 = git worktree @ fe486d42（临时目录，
  验后已删）逐字节 diff。所有产物由 `python pycdc.py <pyc> -o <OK.py>` 默认模式生成
  （先验证默认模式产物与提交 OK.py 逐字节一致后方可比较）。
- 硬约束遵守：未修改 core/、scripts/、site-packages/；新增文件仅
  test_repros/round2/rv2_0{1..6}*（探针 .py/.pyc/OK.py，OK.py 全部由 pycdc.py 生成）
  与本报告。

---

## 1. 逐项结论表

| # | 复核项 | 结论 | 锚点 |
|---|---|---|---|
| 1.1 | R2-O2 旧白名单 + 字节距离阈值移除干净 | **通过** | `git diff fe486d42..124bde37 -- core/cfg/exception_handler.py`：旧 `argval ∈ ('ValueError','TypeError',…)` 两处白名单与 `distance < 40/< 30` 阈值整段删除（-32 行），无残留引用；`grep "distance < \|< 40\|< 30" exception_handler.py` = 空 |
| 1.2 | 新判据不含变相白名单 | **通过** | exception_handler.py:50-105 `_find_handler_type_load`：只读 opcode 族（`_FRAME_BOUNDARY_OPS`/`_UNCOND_JUMP_TARGET_OPS`/`LOAD_GLOBAL,LOAD_NAME`/`RETURN_VALUE,RETURN_CONST`——全为 opcode 名，无异常类型名/文件名/函数名）；边判据 = 无条件转移目标恒等（:90）或 fall-through 且非异常边（:93-99）；帧边界/条件跳转/已访块终止（:74-77,:106）；多前驱取首个结构命中，语义保守（返回 None 即维持基线行为）；git diff 新增行 grep 白名单形态 = 仅注释与探针文件命中 |
| 1.3 | start_offset 魔法阈值 / 跨层读取 / self 跨方法状态 | **通过** | B8 前缀签名 = opname+argval 逐位全等 + 位置锚定末个 PUSH_EXC_INFO 后紧邻三条（region_analyzer.py:10174-10178），无数值距离；B9 豁免只读同层 `self.block_to_region` 与块内 opcode 集（:27546-27554、:26636-26641）；新状态仅类常量 `_EXCEPT_STAR_FRAME_PREFIX`（:10131-10133）/`_EXC_FRAME_GUARD_OPS`（:1216-1219）与参数 `try_scope_exempt`（:25603，全仓唯一传 True 点 :27565-27566）——零新增 self 跨方法状态 |
| 1.4 | 帧前缀剔除不以少发射换全绿（伪造面） | **通过（探针实证）** | 伪造探针：对 35 个候选类型表达式 dis 扫描（含 `[]`/`(x:=[])`/`a==b<c`（SWAP 2 出现于链中）/`[*a]`/`{**a}` 等），**0 个**用户表达式以 `COPY 1` 开头（3.11 中 COPY 1 仅出现在异常帧与 walrus 的值后位置）——三连全等判据不可能被用户代码伪造；rv2_03（`except* []:`，唯一用户段以 BUILD_LIST 0 开头的形态）**success 2/2**，用户 BUILD_LIST 0 原样保留，剔除恰为帧头三条；基线同探针 failure 1/2（修复正向） |
| 2 | B8 修复正确性（4 复现复跑 + 2 新变体） | **通过** | r2_11 **2/2**、r2_12 **2/2**、r2_13 **3/3**、n2_02 **2/2** 全 MATCH（--source 法，新重生成，与 FIX.md §7.1 一致）；新变体 rv2_01（元组类型首 handler）g 单元封闭 + f 的首 handler 类型保留（基线 `except* Exception` → 现在 `except* (TypeError, ValueError)`），rv2_02（except* 嵌 try 内层）**3/3**（基线 1/3）——判据普适 |
| 3 | B9 修复边界 + 残留登记真实性 | **通过** | 复跑读数与 FIX.md §7.2 逐字一致：r2_08 **3/3**、r2_09 failure 2/3（g）产物与基线**逐字节相同**、r2_10 failure 2/4 且 diff 实证症状改善恰如登记（f_while `if not (a and b):`+孤儿`if c:` → `if a and b or c:`；f_ternary `if a and b:` → `if a and b or c:`）、r2_17 failure 2/3（g 封闭：`elif a or b and c:` 恢复；f 残留幻影 `while False:` + 末尾 return 丢失确在产物中）——四单元残留为**如实登记非谎报** |
| 3b | Round1 判据交互（try 包裹 r1_01 / r1_10 形态） | **通过（rv2_05 封闭 / rv2_06 登记面既有零回退）** | rv2_05（try 包 `if a and b or c:`）**success 2/2**（基线 failure 1/2）——新豁免与 B1b 判据无冲突；rv2_06（try 包 `while a and b or c:`）failure 1/2 = 基线 failure 1/2（条件链恢复正确、循环仍被 IfRegion 吞并——与 FIX.md §4 已登记「异常区域包裹下循环消费层」同一缺陷族，读数未变、症状改善，无新增回退） |
| 4 | 零回退抽验 | **通过（13/13 抽验目标全部持平或改善）** | 见 §3 读数表 |
| 5 | docstring 三要素 + C 条款 | **通过（附 2 处轻微记录）** | 见 §4 |
| 6 | 调试残留 | **通过** | `git diff fe486d42..124bde37` 中 DBG/插桩行 = 0（FIX.md 所称 B9DBG/IFDBG/TDBG 已移除属实）；core/ 无新增临时文件写入。**既有项（非本轮引入）**：core/cfg/region_analyzer.py 仍有 18 行 `os.environ.get('DBG_OR')` 门控打印（Round 67 ffc6dc7a 引入，:16901-18366、:25997）——基线既有，建议立项清理 |

**总结论：放行。** 三处修复算法合规（零容忍项全数清零）、实证读数与 FIX.md 全部一致、
残留登记如实、13 项抽验零回退。无打回项；2 处轻微文档瑕疵与 2 项新登记见 §5。

## 2. rv2_ 探针统计（6 支，均入 test_repros/round2/，pyc 现编译 3.11.7）

| 探针 | 形态 | 基线 fe486d42 | 修复后（当前树） | 结论 |
|---|---|---|---|---|
| rv2_01_except_star_tuple_type | except* 首 handler 元组类型 `(TypeError, ValueError) as e` + 链式第二 handler `except* KeyError:` | failure **1/3**（f：`except* Exception` + 第二 handler 丢；g：Different bytecode） | failure **2/3**（g 封闭；f 首 handler 类型保留，残留第二 handler 退化 `if KeyError is not None:`） | B8 对元组类型成立；残留 = **基线既有**（见 §5 登记 R2-NEW-1） |
| rv2_02_except_star_nested_try | except* 嵌在 try 嵌套内层（外层普通 except 包裹） | failure **1/3** | **success 3/3** | B8 判据在嵌套异常表下普适，封闭 |
| rv2_03_except_star_empty_list_type | `except* []:`（唯一用户段以 BUILD_LIST 0 开头形态，帧前缀剔除边界） | failure **1/2** | **success 2/2** | 剔除恰为帧头三条、用户字面量保留——判据不可伪造、不多删 |
| rv2_04_except_star_tuple_noas_chain | 元组类型无 as + 链式第二 handler（rv2_01 变量隔离） | failure **1/2** | failure **1/2**（产物同形） | 残留触发变量 = 元组类型首 handler（与 as 绑定无关），基线读数相同 → 非本轮回退 |
| rv2_05_trywrap_r1_01_shape | try 包裹 r1_01 形态（`if a and b or c:` 语句上下文） | failure **1/2** | **success 3 单元中 2/2**（全 MATCH） | B9 豁免 × B1b 判据无冲突，封闭 |
| rv2_06_trywrap_r1_10_shape | try 包裹 r1_10 形态（`while a and b or c:` 循环条件） | failure **1/2**（`if not (a and b):`+孤儿`if c:`） | failure **1/2**（`if a and b or c:` 链恢复，循环仍内联+幻影 else） | 与已登记消费层残留同族，读数持平、症状改善，零回退 |

rv2_01 的单元级失败详情（pylingual）：`<module>.f: Different control flow`（第二
handler 丢失）；对照 dis：第二 handler 入口块 206 起始即 `LOAD_GLOBAL KeyError` +
`CHECK_EG_MATCH`，属 exception_handler 同块扫描/区域层 except* 链归并
（region_analyzer.py :10424-10483 多 handler 归并）未认领的**新登记面**，见 §5。

## 3. 零回退抽验读数（--source 法，产物全部由 pycdc.py 新生成于临时目录）

| 目标 | 本复核读数 | FIX.md 声称 | 判定 |
|---|---|---|---|
| IQCommon/strategy/jq_trans_module.pyc | **65/65 success** | 65/65 | 持平 |
| fly/data/quotation.pyc | **152/153** | 152/153 | 持平 |
| IQEngine/.../trade_live_broker.pyc | **118/128** | 118/128 | 持平 |
| fly/data/quote.pyc | **84/92** | 84/92 | 持平 |
| r1_01_stmt_andor3 | **2/2 success** | 2/2 | 持平 |
| r1_09_continue_break_guard | **2/2 success** | — | 绿 |
| r1_21_comprehension_mixed | **3/3 success** | 3/3 | 持平 |
| r2_01_try_multi_handler | **3/3 success** | 3/3 | 持平 |
| r2_05_try_loop_try | **2/2 success** | 2/2 | 持平 |
| r2_15_reraise | **2/2 success** | 2/2 | 持平 |
| n2_01_try_simple | **2/2 success** | 2/2 | 持平 |
| n2_03_while_plain_try | **2/2 success** | 2/2 | 持平 |
| 提交 OK.py 7 支（n2_02/r2_08/r2_10/r2_11/r2_12/r2_13/r2_17）vs 现树重生成 | **逐字节 IDENTICAL ×7** | §8 产物更新 | 无手改产物 |

402 全量重生成门禁未在本复核重跑（成本）；以四真身哨兵 + 7 支产物逐字节比对 +
git 工作树零变化佐证 FIX.md §7.6 声称可信。

## 4. docstring 三要素核对（5 处触及点逐条对照代码行为）

| 方法 | 三要素（识别条件/归约方式/AST 映射） | C 条款 | 与代码行为一致性 |
|---|---|---|---|
| `_collect_pre_check_instrs`（region_analyzer.py:10135-10179，B8 全量重写） | 全 | [C1][C2][C3] 全 | 一致：has_eg_match 守卫、末个 PUSH_EXC_INFO 后紧邻三条全等剔除、剩余段交 `_reconstruct_except_match_expr`——docstring 所述与实现逐条对得上 |
| `_find_handler_type_load`（exception_handler.py:50-105，新方法） | 全 | [C1][C2][C3] 全 | 一致：无条件转移目标恒等（:90）/fall-through 非异常边（:99）、帧边界/条件跳转/已访块终止、块首 LOAD 返回 offset——与实现一致 |
| `_try_unify_mixed_boolop_chain`（:27451-27484 docstring + :27523-27554 豁免分支注释） | 全（docstring 既有 [B1b] 段 + [R2-B9] 在分支注释 (a)/(b)） | [C1] 在注释；[C2][C3] 由 docstring 验收路径段承担 | 一致；**轻微记录 D-1**：docstring「识别条件」段仅写了 [B1b] 循环例外，未同步提及 TryRegion 例外（豁免只存在于分支注释） |
| `_detect_boolop_conditional_chain`（:25603 签名 + :26627-26641 claimed-check 注释） | 部分在注释 | [C1][C3] 在注释；[C2] 未逐字出现 | 一致；**轻微记录 D-2**：FIX.md §3.2-B 称该注释含「归约方式/AST 映射」，实际注释只写识别条件+[C1]+[C3]（归约走与未认领候选同路径，由 docstring [B1b] 段覆盖）——报告表述略夸大，代码行为本身无缺口 |
| `identify_try_except_simplified` 两处回退替换点（exception_handler.py:199-208 / :235-242） | 判据与替代面在行内注释 | 守卫描述在注释 | 一致；函数级 docstring 未扩（新方法已携带全量三要素，可接受） |

## 5. 本复核新登记（交后续轮/主代理台账）

1. **R2-NEW-1（except* 链式第二 handler 丢失，基线既有非本轮回退）**：首 handler
   类型为元组/复合表达式时，链式第二 handler（入口块首指令即类型 LOAD + CHECK_EG_MATCH，
   rv2_01.f 块 206）未被 except* 多 handler 归并认领，退化为 `if KeyError is not None: pass`。
   基线 fe486d42 同读数（rv2_01 基线 1/3、rv2_04 基线 1/2）；r2_12（简单名首 handler +
   三 handler 链）不受影响。建议立项：except* 链归并（region_analyzer.py :10424-10483）对
   首 handler 匹配段含 BUILD_TUPLE/组合表达式的后续 handler 入口认领补判。
2. **R2-NEW-2（B9 豁免未覆盖 WithRegion 属主）**：`_try_unify_mixed_boolop_chain`
   豁免只认 LoopRegion/TryExceptRegion（:27510/:27523），WithRegion 若同样按范围登记
   block_to_region，`with` 体包裹的混合链 or 尾续接仍会 break。本轮未构造 with 语料探针
   （超出 B9 登记范围），登记为潜在扩展面。
3. **清理项（基线既有）**：core/cfg/region_analyzer.py 的 `DBG_OR` env 钩子打印
   （Round 67 引入，18 处）建议专项清除。
4. **轻微文档瑕疵 D-1/D-2**（§4）：不影响放行；下轮修相关方法时顺手补齐。

## 6. 复核产物清单

- 新增探针：test_repros/round2/rv2_01..rv2_06（.py/.pyc/OK.py，OK.py 均由
  `python pycdc.py` 生成）
- 本报告：.trae/specs/harden-completed-forms-10rounds/rounds/round2/REVIEW2.md
- 基线对照所用 git worktree（/tmp/rv2_baseline @ fe486d42）与临时产物目录
  （/tmp/rv2_review）位于仓库外，可随时清除
