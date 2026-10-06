# Checklist

## 规范与普查（Task 0–1）
- [ ] 三件套落盘 `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/`，理论依据引用 `rules.md` §1 与 v2 spec I/II/III/IV 条款编号
- [ ] `tools/corpus_census.py` 输出 `total=1721 A=402 B=1312 C=7` 且 `A_delta=0`；B（1312，`*OK.cpython-311*` 派生畸形）与 C（7，自造 scratch）逐类名单落盘 `baseline/corpus_census.json`
- [ ] 排除口径可复核：B/C 每类各抽 ≥3 个文件给出「由 `*OK.py` 再编译而来」的字节级证据（同名 py 源存在 + pyc header/magic 一致），禁止把 A 类文件混入
- [ ] Fresh 基线 = 当前 HEAD 代码重生成 402 产物 + 八分片 batch；`baseline_snapshot.md` 记 units / files / quotation / 34 小测试集 / tests 六套件基线失败名单
- [ ] 基线自证一致：`trade_info_utils.pyc` batch 读数与 `pyc_verify single` 同产物读数逐位相等（预期 36/41）
- [ ] v2 Round 2 分片报告在本规范中被显式标注为过期读数（不得作 before）
- [ ] 派发任何子代理前已本地提交（git log 可证）

## 每轮纪律（round1–round10 逐轮核验）
- [ ] 独立文件夹 `rounds/roundN/`（REVIEW.md、FIX.md、VERIFICATION.md）+ `test_repros/roundN/`
- [ ] 测试工程师每次只取索引中 **1 个** pyc；每个缺陷 ≥10 最小复现（深度 ≥3 变体）+ ≥2 MATCH 负对照；实测深层与浅层产物结构一致（C2 判据）
- [ ] 破口登记格式齐全：锚点 + 机制 + 违反条款（C1/C2/C3 或 I 条款），编号自 B98 续接
- [ ] 修复工程师判据只取白名单（块末 opcode / 后继前驱 / 异常边 / 区域成员关系）；无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀新增方法（G3）；无硬编码深度/计数上限（G4）
- [ ] 修复语义 = 封闭守卫恢复 C1/C2/C3；无个案补丁、无按深度特判、无窄门控（以少发射换全绿）
- [ ] 触及方法 docstring 六项模板（①算法依据②归约顺序③唯一归属判定④嵌套处理⑤入口引用语义⑥反编译流程）+ C 条款，且与代码行为一致
- [ ] 修复工程师自测门禁全过：MISMATCH 复现转 MATCH ∧ 负对照保持 MATCH ∧ 34 小测试集无回退 ∧ 站桩回归不变差 ∧ IV.2 自检（IMPORT_OK / COMPILE_OK / BOM 单头 efbbbf / 无遗留插桩 / 影响面抽验只有目标单元变化）
- [ ] FIX.md 含「代码已落地」或「仅归档 spec 未落地」声明，落地以 grep 标记为凭
- [ ] 主代理验证序六步：34 小测试集 batch → 402 八分片 batch + compare（**REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0**）→ quotation 单验零新增 → tests 六套件零新增失败 → IV.2 门禁自检 → 读数汇报
- [ ] 本轮 ≥1 个 pyc 由 failure 转 success（同目录 `+OK.py` 全单元 Equal），或全量单元读数净增；两者皆无 = 门禁未过，禁止下一轮
- [ ] 单元级不回退：任一文件 `units_success` 下降即判 FAIL（v2 暴露盲区：文件分类不变而单元 −1）
- [ ] 本轮已提交并 push 到 origin main，消息前缀 `rr-v3rNN:`
- [ ] 全程单条命令 ≤300s（超时分片；verify 内部 290s 上限）
- [ ] 无任何 `*OK.py` 被手改（产物变更只能来自 `pycdc.py -o` 重生成）；无用户既有变更被回滚

## 轮次核验记录（round1 · 2026-10-06 封表）

- [x] 独立文件夹 `rounds/round1/`（REVIEW.md、FIX_B98_REGRESS.md、FIX_B100_REGRESS.md、FIX_B103.md、VERIFICATION.md）+ `test_repros/round1/`
      （未合成单一 FIX.md：三次封闭分散于三份家族文档，如实标注，不以文件名充数）
- [x] 测试工程师每次只取 **1 个** pyc：6/6 目标逐文件给出逐指令第一分歧；每族 ≥10 复现（46 臂索引，19 MISMATCH 标本 + 27 MATCH 负对照）
- [x] 破口登记格式齐全：B98/B99/B100/B101 锚点 + 机制 + 违反条款（本轮起自 B98 续接，另登 B102/B103）
- [x] 修复工程师判据只取白名单：新增谓词 `_is_return_none_join_block`/`_is_region_internal_exit_sink`/`_compute_arm_level_join`/`_armjoin_is_skip_edge`/`_term_exhausted`
      —— 全部只读块末 opcode / 后继前驱 / 异常边 / 区域成员关系；G3 禁止前缀新增方法命中 **0**；G4 硬编码深度/计数上限命中 **0**
- [x] 修复语义 = 封闭守卫恢复无感：三次附带回退（B98→accounts×3、B100→strategy_info_utils、B100fix→handlers×2）**全部同轮封闭**，
      无深度门控、无文件名/偏移特判、无以少发射换全绿的窄门控
- [x] 触及方法 docstring 六项模板 + C 条款（`[r1-b98-elsescope]`/`[r3-b100-armjoin-tailexit]`/`[r3-b103-armjoin-termexit]` 三处标记逐处 grep 命中）
- [x] 修复工程师自测门禁全过：MISMATCH 复现转 MATCH（19→2，且残余 2 为原失败集严格子集）∧ 负对照保持 MATCH ∧ 34 小测试集不回退 ∧
      站桩回归不变差（17 哨兵臂 34/34）∧ IV.2 自检（IMPORT_OK/COMPILE_OK/BOM 单头/无插桩残留/CRLF 原样/影响面抽验只有目标单元变化）
- [x] 主代理验证序六步全跑，双门禁 **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0**（402 全量实测，非 34 集推断）
- [x] 本轮 ≥1 个 pyc 由 failure 转 success：**7 个**，同目录 `+OK.py` 全单元 Equal；units 6554→6564
- [x] 单元级不回退门禁发挥作用：三次回退都是「文件分类未变或 34 集外、但 units 下降」，纯计数面看不见，靠 402 逐文件差值抓到
- [x] 全程单条命令 ≤300s（34 集拆三片、regen/verify 分组；`verify all34` 触发内部 290s 上限已记录并按 v2 惯例拆分）
- [x] 无任何 `*OK.py` 被手改；F: 工作区零写入（语料按相对路径镜像进本工作树）
- [ ] **本轮已提交并 push 到远程 —— 未达成**：6 个提交（`fd06c87b`…`2eb319bc`）在本地，
      `git push origin HEAD:refs/heads/rr-v3-full-corpus` 两次 `Recv failure: Connection was reset`、
      `git ls-remote` 连 github.com:443 超时（本工作树环境无外网）。
      网络可用时执行该命令即可；不推 `refs/heads/main` 的理由见 `rounds/round1/VERIFICATION.md` §V.1
      （F: 本地 main 已前进至 `1aecc150` rr-v2r03 round3，推 main 会令用户本地线与 origin/main 分叉）

## 终态验收
- [ ] 402 全量 units = 6617/6617（100%）、files = 402/402 success、0 compile_error、0 error
- [ ] `site-packages/fly/data/quotation.pyc` single = 153/153 status=success
- [ ] 每个 A 类 pyc 同目录存在同名 `+OK.py` 且判据为 Equal（405 个已有产物 + 本轮补齐者，缺产物数 = 0）
- [ ] `_identify_*` 十族与生成方法注释六项模板逐方法过审，无注释/行为矛盾
- [ ] 台账与 wiki 数字一致（`syntax_coverage.py` 重跑后同步，无矛盾数字）
- [ ] 若未达 100%：残余清单（文件 × 单元 × 违反条款）如实上报，未改判据、未凑读数、未删语料
- [ ] 主代理未执行修复/评审实现任务（仅调度 + 验证 + 勾选）
