# Round 16 结果（OUTCOME）

本轮一条根因线（R16-A），按门禁顺序完成：单点修到完全 OK → quotation.pyc 单验 → 全量批量回归 →
双口径复验 → 标注回填 → 索引纠正 → 提交 push。
设计稿 `arm-design.md`，修复与验证记录 `fixes.md`。

## 一、解决了什么

目标真源：`site-packages/IQCommon/arg_checker.pyc` → **`_is_valid_quarter` 的 `try/except` 外壳 16 条指令恢复**。

- Round 15 §四 移交的猜想「analyzer 未把 `TryExceptRegion` 挂到 `IfRegion` 下」被**实测否证**：
  区域树里 `TryExceptRegion@94.parent == IfRegion@86`，父子关系本来就建好了。
- 真根因在**生成层**：if 臂的表达式子区域（BoolOp/Ternary）预生成把 `child.blocks` 整批写入
  `generated_blocks`，抢走了语句级结构兄弟（Try/Loop/With/Match）的入口块，
  使 `_process_if_blocks` 的入口块生成守卫空转 ⇒ 整块语句无人发射。
- 正解是一个纯结构谓词 + 两处 `continue` 守卫（**+53 / −0**，无删除、无重排）：
  表达式子区域不得在预生成阶段认领「其块内含结构兄弟入口」的那部分。
  对应区域归约四原则：每块只属一个区域、父区域引用子区域**入口**、自底向上、嵌套即单节点。

`core/cfg/region_ast_generator.py`：`d07996aaa20d4665 → 0fc591a8433e7032`（48122 → 48175 行，
BOM/CRLF 不变，落地内容与落地前逐字节验证过的副本 sha256 全值相同）。

## 二、两把尺子

| 口径 | 落地前 | 落地后 | 差 |
|---|---|---|---|
| 严格（`_r13_gate` 重生成产物，405 计分文件） | 函数 6079/6332，满clean 329 文件 | 函数 **6080/6332**，满clean **330** 文件 | +1 / +1 |
| 官方（`pyc_batch_verify.bytecode_diff`，406 targets，同脚本 pre/post） | 355 ok / 50 partial，函数 5699/5838 | **356 ok / 49 partial**，函数 **5700/5838** | +1 ok / +1 函数 |
| 目标文件严格 | 48/49 | **49/49** | +1 |
| 目标文件官方 | 46/47（rate 0.9787） | **47/47（rate 1.0）** | +1 |

两把尺子各自独立，禁止跨口径相减（官方口径分母与 Round 15 记录不同：本轮 pre/post 由
`D:/Temp/r16_arm/official_all.py` 统一重算）。

## 三、门禁与归因

1. 单点：`[FLIPPED-CLEAN] IQCommon/arg_checker.pyc 48/49 -> 49/49`，无回滚。
2. `quotation.pyc`：`148/150 -> 147/150`，`WORSENED(rolled back)`；缺陷函数
   `change_future_real_date` / `change_his_to_forward` / `get_trend` 与 Round 15 同集合，
   补丁对该文件**逐函数无影响** ⇒ 属 SubTask 13.3 已登记的产物/核心漂移，非本轮回退。
3. 全量 406 targets：`CLEAN=330 UNCHANGED=64 WORSENED=9 REGRESSION=2 NO-OKPY=1`
   （Round 15：`329 / 65 / 9 / 2 / 1`）；异常文件集合与 R15、R14 **逐个相同（11 个，新增 0）**
   ⇒ 满足「零新增回退」。

## 四、复现代价与残留

六套电池落地后 `--strict` 全部退出码 0（`UNEXPECTED=0`、`ERROR=0`）：
`round16_arm 1`、`round15_arm 2`、`round14_join 1`、`round14 0`、`round13 14`、`round16_sink 8` 个 MISMATCH。
标注回填：`round16_arm` 9 项 → SENTINEL 且 `r16a_05` 纠正为 MISMATCH；`r15a_01/02` → SENTINEL。

移交下一轮：

1. `r16a_05` loop 入口重复发射（over-emit，orig=31 / decomp=39）；
2. R16-S sink 族：`IQData/manager/plugin_manager` 9/10、`IQEngine/core/plugin_manager` 8/9
   （`PluginManager.set_engine`）—— 与本轮补丁**正交**（裸核心与 R16 播种下 15 复现逐条一致），
   线索在 `region_analyzer._build_elif_region` / `_check_elif_chain`（`:17831` / `:17948`）
   的 else 臂归并判据；诊断 agent 已耗尽 150 轮上限（电池交付完整，ANALYSIS.md 缺失）；
3. T1/T2「then 臂先结构后表达式」整体重排（影响面未测，且并行 agent 声称的收益未经我方复测）；
4. `r15a_08` `guard_clause_prefix_end`、`r15a_09` body-sequence 重复发射；
5. SubTask 13.3 / 13.4、Task 5 遗留（`decrypt_database_url` +29、`cgroup` +2/+1、`replace_utils` 差 2）。

## 五、提交物

`core/cfg/region_ast_generator.py`、`site-packages/IQCommon/arg_checkerOK.py`、`pyc_index.json`、
`rounds/round16/{arm-design.md,fixes.md,OUTCOME.md,targets_1fix.txt,targets_all.txt}`、
`test_repros/round16_arm/`（16 复现 + `run_all.py`）、`test_repros/round16_sink/`（15 复现 + `run_all.py`）、
`test_repros/round15_arm/run_all.py`（SENTINEL 回填）、`rounds/round15/OUTCOME.md`（§四 猜想否证更正）、
`tasks.md`（Task 16）。
