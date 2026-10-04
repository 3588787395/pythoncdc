# Round 10 终审主代理验证报告（VERIFICATION.md）

- 验证人：主代理（不执行实现任务，仅调度 + 验证 + 归档）
- 日期：2026-10-04
- 树状态：HEAD 起点 = `b49b5b61`（Round 9 归档）；本轮提交链 = `72f46912`（评审批次一）→ `b53d449c`（修复批次）→ `0caea12b`（复核放行）→ 本归档
- 判据唯一：`scripts/pyc_verify.py`（single/batch/compare，pylingual compare_pyc，Python 3.11.7）；全部命令 ≤300s
- 驱动：`rounds/round10/verify_driver.py`（复制自 round9，同深度 ROOT）+ `rounds/round10/verify7_split.py`（shard7 超时拆分合并，见 §1 注记）

## 1. 402 全量八分片重生成 + batch + compare

| 分片 | 文件 | units（原基线→本轮终审） | 文件 success | 判定 |
|---|---|---|---|---|
| shard0 | 51 | 775/786 → **777/786**（+2） | 45 → **46** | REGRESSIONS=0 IMPROVED=1 |
| shard1 | 51 | 462/469 → 462/469 | 48 → 48 | REGRESSIONS=0 |
| shard2 | 51 | 537/538 → 537/538 | 50 → 50 | REGRESSIONS=0 |
| shard3 | 51 | 883/887 → 883/887 | 48 → 48 | REGRESSIONS=0 |
| shard4 | 51 | 848/855 → 848/855 | 46 → 46 | REGRESSIONS=0 |
| shard5 | 51 | 993/999 → 993/999 | 46 → 46 | REGRESSIONS=0 |
| shard6 | 51 | 786/801 → **789/801**（+3） | 48 → 48 | REGRESSIONS=0 |
| shard7 | 45 | 1262/1282 → **1265/1282**（+3） | 37 → 37 | REGRESSIONS=0 |
| **合计** | **402** | **6546/6617 → 6554/6617（99.05%）** | **369/402** | **REGRESSIONS=0** |

- regen 402/402 成功零失败（regen_shard0..7.json 全零）
- 注记一：shard7 单批 verify 触发驱动内部 290s 上限（45 文件含多个大文件），按「超时必须分片」纪律以 `verify7_split.py` 拆两半（73.0s + 30.1s）执行后合并（595/608 + 670/674 = 1265/1282，rows/paths_by_status 全量拼接，files/units 聚合重算），合并报告落 `shard7_report_new.json`，compare 正常消费
- 注记二：shard0 IMPROVED=1（jq_trans_module failure→success）为对**原始基线**的位移，Round 9 已计入；对 Round 9 终态（6554/6617、369/402）逐位持平，零位移
- 本轮修复真身增益在合成对抗面（round7 面 +4、round8 面 +3、round10 面 +7 单元，见 §5），402 真身文件无新增封闭单元，亦零回退

## 2. 小测试集 34（baseline/failing_index.json）

- 实测 **1505/1568**（95.98%），1 success / 33 failure
- compare（round9/small34_new.json → round10/small34_new.json）：**REGRESSIONS=0 IMPROVED=0**，文件与单元逐位持平

## 3. quotation.pyc（基线路径口径）

- `site-packages/fly/data/quotation.pyc`：**152/153**，唯一失败 `change_his_to_forward`（Different control flow）= Round 8/9 VERIFICATION 逐字一致，零新增失败（single 命令 exit 1 = failure 状态预期行为）

## 4. tests/ 六套件

- `test_algorithm_correctness + test_deep_nesting_pressure + test_control_flow_completeness_matrix + test_complete_syntax_coverage + test_boundary_cases + test_core_functional`
- 实测 **277 passed / 2 failed / 2 xpassed**（6.03s）
- 2 failed = `test_B01_simple_if_then_else_merge` + `test_BOUNDARY_02_large_function`，与 Round 7/8/9 登记基线失败名单逐字一致，**零新增失败**

## 5. 修复面读数（评审 REVIEW2.md 独立复跑，主代理采信）

- B72 面 23/23（r10_14 7/7 + r10_16 7/7 + 负对照 n10_01..04 9/9）；B48 面 r7_03 7/7、r8_06 10/10、r8_10 9/12；B46 面 r7_07 6/7（唯一失败 = 实施降级项 t_nest_in_condition）
- 哨兵口径裁决：修复自报「114/114」系漏跑 n6_01（8 单元）口径缺口非造假；评审权威重跑 round6 全量 16 pyc = **115/115** 零失败；round7 **108/128**（+4 补强）、round8 **110/118**（+3 补强）失败名单逐位持平；六哨兵 + option_account **302/308** 基线完全复现
- 变体攻击 26/27：`x >>= t` 冷门算子修复后转正确 = B48 真增益实证；唯一新 MISMATCH = **B76**（augassign × BoolOp RHS 整句蒸发），worktree @ 72f46912 逐字节同败证实既有缺口

## 6. 轮门禁与终审门禁判定

- **≥1 破口封闭：达成**——B72/B48 封闭 + B46 部分（净 +7 单元），评审放行 6/6 hunk（判据全为同层结构事实：oparg 13-25 = 3.11 dis nb_inplace 编码事实 / STORE_DEREF 纯元数据 / 成员关系+逃逸边检测，零白名单/阈值/跨层/self 状态/少发射）
- **台账覆盖率提升（终审轮门禁）：达成**——台账 41 组全映射，35 组有对抗覆盖（本轮新增专攻 Import 族与 Global/Nonlocal 族），6 组零专攻如实登记；补攻击 17 文件组 61/72 + 负对照 9/9 全 MATCH
- **无回退：达成**——402 八分片 REGRESSIONS=0、34 小集 REGRESSIONS=0、quotation 零新增、tests 零新增失败
- **红线核验：通过**——双核心单 BOM（评审字节级验证）；core/ 插桩 grep 零命中；探针 OK.py 抽验 4/4 纯 pycdc 重生成（零手改）；归因 worktree 全部清零（评审/复核各自 `git worktree list` 仅剩主工作区）；主代理清扫前轮遗留 worktree 3 个（pcdc_r0/pcdc_wt/pcdc_r8wt）+ 临时对照孤儿 `_cmpOK.py`；远古 stash 2 条（基线 c9b9452c/73b2029）非本轮产物、保留未动

## 7. wiki §8.2 复审六步全量（任务 10.3，主代理亲自执行）

1. fix 批归档落位：round10/FIX.md @ b53d449c ✓
2. grep 落地标记在树：本轮 `[B48]`×5 / `[B46]`×5 / `[B71]`×2 / `[B72]`+ 共 13+ 处；历史 B1 族 `[B1b fix]`/`[B1b fix-r2]` + `_sb_has_body` 十余处 ✓
3. 台账更新：总纲 §0/§5.5 完备 127→128、破口 1→0；§6 B1a/B1b 改「已封闭（防回归监控）」；§8.1 标记表同步 ✓
4. `tools/kb/syntax_coverage.py` 重跑：**128/128 = 100%** → `docs/refactor/syntax-coverage.json` ✓
5. 占比重算与页面数字同步（禁手改、禁矛盾数字）：总纲 / branch-coverage / syntax-audit-ledger / overview（乱行修复）/ index 五页全部同步为 v6 口径 ✓
6. log 记录：`wiki/log.md` 新增 2026-10-04 终审条目（B1 族升格 + 口径 v6）✓

## 8. 终态口径（v6，诚实分层）

- 路径层 128/128 = 100%；**形式层**（路径 × 单形态不变式）完备 128 / 破口 0 / 零能力 0 ⇒ **100%**
- **组合级对抗挂账 25 号未清零**（B42–B51/B56–B65/B69–B71/B73–B76 内未封闭部分 + 残留单元；含本轮新登记 B73/B74/B75/B76 与实施降级 B46 尾项/B71；权威清单 = rounds/round10/REVIEW.md 残留决策表 + REVIEW2.md）+ 6 组零专攻形态组（Module 专攻、ClassDef 体专攻、AnnAssign、fstring_conversion、keyword_args/star_args、decorator_with_args）+ r4_or4_and2 1/2（B11-R2）+ round7 残留登记面 81/117
- 挂账透明化：不计入形式层分母，按 wiki §8.3 状态机继续推进；checklist「破口清零」终态项保持未勾

## 9. 流程记录

1. 评审批次一（72f46912，任务 10.1）：覆盖矩阵 41 组 + 补攻击 61/72 + 残留 29 项全判可封闭 + B71–B75 登记
2. 修复批次（b53d449c，任务 10.1b）：B72/B48/B46 部分封闭 + 两项实施降级如实登记 + FIX.md
3. 复核批次（0caea12b）：终判放行 6/6 hunk + 哨兵口径裁决 + 变体 26/27 + B76 登记
4. 主代理终验（本报告）：402 八分片 + 34 小集 + quotation + tests 六套件 + §8.2 六步全过
5. 终归档：tasks.md 10.1–10.4 勾选 + checklist 终态核验 + 提交并 push origin main

## 10. 网络故障记录（push 重试）

- 终归档提交 `f831eeae` 后 push 连续失败 3 次：
  1. `git push origin main` → `fatal: unable to access 'https://github.com/3588787395/pythoncdc.git/': Recv failure: Connection was reset`
  2. `git push https://<TOKEN>@github.com/3588787395/pythoncdc.git main` → 同上 Connection was reset
  3. 等待 20s/60s 后两次重试 → `Failed to connect to github.com port 443 after 21398/21242/21139 ms: Couldn't connect to server`
- 判定：github.com:443 网络中断（非凭据问题，显式 token 同样失败）；与 Round 9 push 网络故障同型
- 重试命令（网络恢复后执行）：`git push origin main`（origin 已内嵌 token）或 `git push https://<TOKEN>@github.com/3588787395/pythoncdc.git main`（<TOKEN> = origin remote URL 内嵌凭据，依 GITHUB PUSH PROTECTION 要求脱敏不落盘）
- 待推送提交：`f831eeae`（round10 终审归档）与本网络记录提交
