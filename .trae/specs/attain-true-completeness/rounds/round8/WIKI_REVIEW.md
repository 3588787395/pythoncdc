# WIKI_REVIEW.md — Round 9 wiki 台账 v8 落账（§8.2 复审六步实录）

> 范围 = Task 9.1–9.4；基线 = `rr-v3r08`（b6e634b7）。六步全部主代理实跑取证。

## §1 六步实录

| 步 | 内容 | 结果 |
|---|---|---|
| ① fix 批归档落位确认 | 13 commits（rr-v3r01…rr-v3r08 及其子补丁）`git merge-base --is-ancestor` = **13/13 在 origin/main 祖先链**（cb24db60/ece1aab5/69132f55/841e511e/774cd9cb/8c088ef7/63520cb4/b6e634b7 全 OK） | ✅ |
| ② grep 落地标记全表 | `core/cfg/*.py` 标记 `[Bn-V3Rn]` 逐轮计数 = **R2:47 / R3:25 / R4:13 / R5:34 / R6:12 / R7:21 / R8:22，共 174**；各批「代码已落地」声明与树内 hunk 一一比对属实（含 B155/B156、B162 两处等新机制，见 `round8/REVIEW.md`） | ✅ |
| ③ 台账 §5 全量更新 + §6/§8.1 | 总纲 [[decompile-invariant-completeness]]：§0 读数表改 v8（**完备 128 / 破口 0 / 零能力 0 ⇒ 100%**；组合级 28 项全数处置；v7 留档一行）；§5.5 判定汇总改 128/0/0/100%；§6 开放破口表逐行加 v8 终态（B98/B122/B127/B128/Yield/B44/行内编号族全封闭）；§9.1 口径史加 v8 行（v7 移「现行」标记）；台账页 [[syntax-audit-ledger]] 汇总与 updated 同步；[[branch-coverage]] 当前读数与检索词同步 | ✅ |
| ④ `tools/kb/syntax_coverage.py` 重跑 | **128/128 = 100%**（ast 97 + 扩展 31，denom/numer/pct 三读一致）；sha256 前缀 `38003eb46f2bdd6a`（v7 重跑为 `86539c44…`，历史记录保留）；JSON = `docs/refactor/syntax-coverage.json` | ✅ |
| ⑤ 占比重算 + 五页数字同步 | 总纲 / branch-coverage / syntax-audit-ledger 数字行已更新；overview / index 复核**无三态数字行**（v7 条目所列五页在 v8 只有引用文本，无需改动，实测核对一致） | ✅ |
| ⑥ log | [[log]] 顶部新增 2026-10-21 条目（六步 + 口径 v8 取代 v7 + 稀窝属地） | ✅ |

## §2 数字核对

| 项 | 值 | 依据 |
|---|---|---|
| 三态 v8 | 完备 128 / 破口 0 / 零能力 0 | `round8/REVIEW2.md` §3 |
| 占比 | 128/128 = 100% | docs/refactor/syntax-coverage.json + 工具输出 |
| 组合级 | 25 号 + 另册 3 号 = 28 项全数处置；唯一属地残余 B142 稀窝 | `round8/REVIEW.md` §3/§6 |
| 稀窝（不升格） | B142（嵌套 finally 副本归属）、B143（finalbody 内 break 派发） | R6 登记，R8 复核不变 |
| 门禁 | 402 八分片 6617/6617 files_failure=0；small34 1568/1568；quotation 153/153；tests 基线名单 | `round8/final_verify_summary.json` |

## §3 页面改动清单

1. `wiki/concepts/decompile-invariant-completeness.md`（updated 2026-10-21；§0 / §5.5 / §6 / §9.1）
2. `wiki/concepts/syntax-audit-ledger.md`（汇总 v8）
3. `wiki/concepts/branch-coverage.md`（读数 v8 + 检索词）
4. `wiki/log.md`（新增条目）
5. overview / index：核验无涉改数字行（本步零写）

## §4 结论

六步全过、数字三处互证一致（工具 JSON / 台账 §5.5 / 五页文本）、历史条目只增不删（v7/v6/v5 留档）。**wiki v8 落账完成，放行 Task 10（主代理全量终验 + 终归档）。**
