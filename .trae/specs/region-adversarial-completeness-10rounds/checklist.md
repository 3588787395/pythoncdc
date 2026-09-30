# Checklist

## 规范与基线
- [ ] 新规范文档（本 spec）已基于 `wiki/concepts/decompile-invariant-completeness.md` 创建，含嵌套无感（C1/C2/C3）与语法完备（128 形态）双目标
- [ ] 基线报告已产出：`scripts/pyc_verify.py batch` 分片跑 402，失败文件清单（小测试集索引）落位 `baseline/failing_index.json`
- [ ] 12 个 `_identify_*` 识别方法注释三要素缺口表已盘点（`baseline/comment_gaps.md`）

## 每轮纪律（round76–round85 逐轮核验）
- [ ] 调用子代理前已提交到本地（git log 可证）
- [ ] 独立文件夹 `rounds/roundN/` 已建立（分析、修复说明、评审意见、验证读数四类归档齐全）
- [ ] 测试工程师：恰好 1 个靶 pyc、≥10 最小复现（≥10 MISMATCH + ≥2 MATCH 负对照）、ANALYSIS.md 根因归类含区域类型 × C 条款
- [ ] 修复工程师：修复符合区域归约算法（无跨区域跨层次启发式、无文件名/函数名白名单、无 start_offset 魔法阈值、无「以少发射换全绿」）
- [ ] 修复触及的识别方法注释已同步三要素（识别条件→归约方式→AST 映射）并声明 C1/C2/C3 合规
- [ ] 评审工程师：独立对抗审查完成，含台账已判完备形态轮换抽查 ≥2（深层嵌套探针）；结论「通过」（打回记录留档）
- [ ] 主代理验证序执行：靶 pyc 达 success → quotation.pyc 验证通过 → 批量回归分片 + compare **REGRESSIONS=0** → 现有区域相关测试通过
- [ ] 靶 pyc 的 `*OK.py` 由程序生成于同目录（未手改；git diff 无手工痕迹）
- [ ] 本轮至少 1 个 pyc 新达 success（否则该轮未过门禁）
- [ ] 成功率读数已汇报（字节码一致函数数、单元级成功率、文件级 success 数）且逐轮递增
- [ ] 本轮已提交并 push 到 origin main
- [ ] 全程所有命令 ≤300 秒（无超时命令）

## 破口与台账
- [ ] B1a 已落地：`_graft_pending_operand` + `_contains_identity` 当前树 grep 命中
- [ ] B1b 已定位并封闭：neg75_jqcond2 3/3 success
- [ ] B1 验收读数：jq_trans_module 保持 65/65、161 产物逐字节不变或改善
- [ ] 评审对抗发现的新破口已登记（Bn 续接，状态机推进）
- [ ] wiki §8.2 复审六步已执行：落地标记 grep → 台账更新 → syntax_coverage.py 重跑 → 占比重算 → log 记录
- [ ] 台账数字与 wiki 页面一致（禁手改、禁矛盾数字）

## 终态验收
- [ ] 402/402 pyc 全部 success（pyc_verify.py batch 全量报告，其余桶全 0）
- [ ] 全部 `*OK.py` 在位且程序生成
- [ ] 完备占比重算达 128/128（破口清零）
- [ ] 主代理未执行修复/测试/评审实现任务（仅调度 + 验证 + 勾选）
- [ ] 无用户既有变更被回滚
