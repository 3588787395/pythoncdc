# Checklist

> 验证时间：2026-09-29。全部锚点为本次审计亲眼所见的 file:line；git 工作区程序文件零改动（仅用户自己的 `.gitignore` 修改与 `parsers/ast_builder_cleaned.py` 删除状态）；零新增脚本（仅修正既有工具 `tools/kb/syntax_coverage.py` 的 except\* 检测标准并重跑）。

- [x] 标准文档含不变式形式化定义（L(A) 局部消费 / 黑箱组合 / 守卫封闭三条款）与归纳论证（[[branch-coverage]] §1）
- [x] 三级判定（完备/破口/零能力）判据可操作，分子只计"完备"，禁止手改数字（§2/§8）
- [x] 误解清单 13 条（≥12），每条含【错误做法 / 为什么错 / 正确做法】（§3，含第 12 条 PRELOAD_RERAISE 3.12 误标实证）
- [x] 理论要求→实现程度映射表 T1–T8 每行有代码锚点与当前程度（§4）
- [x] 批次 A（控制流形态）每形态三锚点齐全 + 不变式判定（[[syntax-audit-ledger]] 表A）
- [x] 批次 B（表达式/派生形态）每形态三锚点齐全 + 不变式判定（表B + 表C，31 扩展形态全名册）
- [x] 台账合计覆盖 128 形态，三级计数与最终占比一致（完备 127 / 破口 1 / 零能力 0 ⇒ 99.2%；路径层 128/128=100% 由 syntax-coverage.json 重测背书）
- [x] B1（BoolOp×if 前导操作数）定位到归约函数（`region_ast_generator.py:47629-47643`），确证 fix1 嫁接仅存归档 spec 未落地；B1b 第二丢弃入口未定位并登记（交 fix2+）
- [x] B2（If×continue）非局部读取点定位且守卫状态明确（`_block_is_continue_target:10289` + `_loop_else_set` 排除 `:10423-10427`，已落地）
- [x] B3（Loop 共享尾）守卫现状逐条列明（W14-C `region_analyzer.py:27282/27304/19602`、fix3-T1/T2/T6 `region_ast_generator.py:12945-13075/18593`、W23 `:19185`、R71-thenover `:22758`，已落地）
- [x] B4（孤儿子）发射点定位（孤儿块释放 `region_ast_generator.py:1593-1663` + 合法子区域守卫 `region_analyzer.py:1410-1424`，已落地）
- [x] 每破口登记涉及形态 + 破坏的 T 条款 + 修复验收判据（B1 验收 = 两丢弃入口全接回 + jq 65/65 保持 + 161 产物逐字节不变）
- [x] except* 审计：**推翻零能力初判**——全链实现确证（识别 `region_analyzer.py:9731/9813/12701-12709`、`exception_handler.py:93-276` → 归约 `:8724/:9342` → 生成 `region_ast_generator.py:26839-26843` → 发射 `code_generator.py:702/2079`）；PRELOAD_RERAISE 系 3.12 操作码误标，纠正记录入标准 §5
- [x] overview / index / log 数字与台账一致，无相互矛盾数字（99.2% 两次含义全异已注明）
- [x] 复审闭环（修复批→复审→台账→重算）与 fix2/fix3 验收引用破口编号规范写入标准（§7）
- [x] 误解清单维护规则（只增不删，当前 13 条）写入标准（§7）
- [x] 断链 = 0（新增/编辑页面的全部 [[链接]] 目标存在）；check_stale 唯一 1 例 = `parsers-ast-builder-cleaned.md`（源文件删除属用户决定区、用户明令不得处理，挂起等指示，非本 change 造成）
- [x] 全程零程序文件改动、零新增脚本（git status：core/ 与 parsers/ 无本 change 修改）
