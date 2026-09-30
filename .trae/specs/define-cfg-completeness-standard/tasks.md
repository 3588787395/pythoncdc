# Tasks

> 硬约束：全程不改程序文件、不新增脚本。全部产出为 KB 文档，证据来自只读代码审计 + 既有工具读数。
> 状态：全部完成（2026-09-29）。审计推翻两项初判：except\* 非零能力（全链实现）；B1 修复未落地（仅存归档 spec）。

- [x] Task 1: 重写 `wiki/concepts/branch-coverage.md` 为完备性衡量标准本体
  - [x] 1.1 不变式形式化定义（局部消费 L(A) / 黑箱组合 / 守卫封闭）+ 归纳论证（为什么分母不是无限组合）
  - [x] 1.2 三级判定判据表（完备 / 破口 / 零能力），明确分子只计"完备"
  - [x] 1.3 误解清单 13 条，每条含【错误做法 / 为什么错 / 正确做法】（含第 12 条 PRELOAD_RERAISE 3.12 误标实证、第 13 条语料上限≠能力上限）
  - [x] 1.4 理论要求→实现程度映射表 T1–T8（每行带代码锚点与当前程度）
  - [x] 1.5 占比公式 + 台账驱动更新规则（数字禁止手改，页面间禁止矛盾数字）
- [x] Task 2: 审计批次 A —— 控制流形态
  - 范围：If / elif 链 / Loop（for/while）/ for-else / while-else / break / continue / Try 四形态 / TryStar / With（单/多上下文）/ Match+8 模式 / async for / async with / raise / assert
  - [x] 2.1 识别锚点（`RegionType` 19 类 `region_analyzer.py:170-189` 等）
  - [x] 2.2 归约锚点（`_find_loop_else:5242`、handler 归并 `:7891/:8724/:9342`、汇合剪枝 `:27282/27304`）
  - [x] 2.3 生成锚点（If `:9575/18957/24043`、While `:5463/12086`、Try `:26901/27389`、Match `:31596`、elif `:17027/17261`、Break/Continue `:10198/:24098`）
  - [x] 2.4 不变式判定（B2/B3/B4 守卫族定位；except\* 全链确证）
  - [x] 产出：`wiki/concepts/syntax-audit-ledger.md` 表A
- [x] Task 3: 审计批次 B —— 表达式与派生形态
  - [x] 3.1 三锚点记录（BoolOp `:32662`、IfExp `:12654`、Lambda `:2250`、ListComp `comprehension_generator.py:2074` 等 + JSON 背书规则）
  - [x] 3.2 不变式判定（B1 丢弃点 `region_ast_generator.py:47629-47643` 确证）
  - [x] 产出：台账表B + 表C（31 扩展形态全名册）
- [x] Task 4: 破口专项定位（B1–B4）
  - [x] 4.1 B1：`_cjb_skip_inline_if` 丢弃点 `:47629-47643` 确证；fix1 嫁接（`_graft_pending_operand`/`_leading_operand`/`_contains_identity`）**仅存归档 spec jqop1.json，未落地代码**（commit db9364bf 自述零写入）；B1b 第二丢弃入口未定位（交 fix2+）
  - [x] 4.2 B2：continue 守卫 `_block_is_continue_target:10289` + `_loop_else_set` 排除 `:10423-10427`（已落地）
  - [x] 4.3 B3：共享尾守卫族 W14-C/fix3-T1T2T6/W23/R71-thenover（`region_analyzer.py:27282/27304/19602`、`region_ast_generator.py:12945-13075/18593/19185/22758`）已落地
  - [x] 4.4 B4：孤儿块释放+合法子区域守卫（`region_ast_generator.py:1593-1663`、`region_analyzer.py:1410-1424`）已落地
  - [x] 4.5 验收判据：B1 验收 = 两丢弃入口全部接回 + jq 65/65 保持 + 161 产物逐字节不变（写入标准 §6）
- [x] Task 5: except* 零能力路径审计
  - [x] 5.1 **结论推翻初判**：`CHECK_EG_MATCH` 100+ 引用中大量为识别逻辑（`region_analyzer.py:9731/9813/12701-12709`、`exception_handler.py:93-276`）；全链识别→归约→生成→发射（`code_generator.py:702` `except_keyword='except*'`）。`PRELOAD_RERAISE` 是 3.12 操作码，不构成 3.11 未实现证据
  - [x] 5.2 登记纠正记录（标准 §5）；工具 `tools/kb/syntax_coverage.py` 检测标准同步纠正（`is_except_star`/`PREP_RERAISE_STAR`），JSON 重测 128/128
- [x] Task 6: 汇总台账 → 占比与缺口清单
  - [x] 6.1 台账 `syntax-audit-ledger.md`：表A/B/C 覆盖 128 形态，判定汇总 完备 127 / 破口 1 / 零能力 0
  - [x] 6.2 `branch-coverage.md` 最终数字：路径 100% × 不变式 ⇒ **99.2%**（与旧数巧合、含义全异，已注明）
  - [x] 6.3 `overview.md` / `index.md` / `log.md` 同步（含口径演变史与纠正记录）
  - [x] 6.4 check_stale = 0、断链 = 0
- [x] Task 7: 持续迭代机制落地
  - [x] 7.1 复审闭环写入标准 §7（修复批→复审→台账→重算）
  - [x] 7.2 fix2/fix3 验收引用破口编号（B1/B1b）规范写入 §7
  - [x] 7.3 误解清单维护规则（只增不删，当前 13 条）写入 §7

# Task Dependencies

- Task 2、Task 3、Task 4、Task 5 依赖 Task 1（标准先行）——已按序完成
- Task 6 依赖 Task 2–5；Task 7 依赖 Task 6——均已闭环
