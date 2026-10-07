# 终局审计状态（prompt→artifact 对照，逐条以**本次实测**为凭）

审计时点：2026-10-08 03:03（本地 +0800）。判据唯一 `scripts/pyc_verify.py`（pylingual `compare_pyc`，
CPython 3.11.7 64 位）。**本文件的作用是防止把「做了很多」当成「达标」**：
每条只认实测证据，未达即写 ✗，禁止改判据、禁止缩题。

## 一、原始要求的逐条对照

| # | 要求（原话要点） | 实测证据 | 状态 |
|---|---|---|---|
| 1 | 以 `site-packages` 全部 pyc 建索引逐个处理，直到全部反编译成功 | 索引 `baseline/full_index.json`；402 个 A 类逐文件逐单元比对（`rounds/round10/after/`） | ✗ **6577/6617 单元、386/402 文件**，余 40 单元／16 文件 |
| 2 | 每个 pyc 同目录生成同名 +OK 的 py 文件 | 产物名实为 `<stem>OK.py`（如 `trade_live_broker.pyc → trade_live_brokerOK.py`）；盘上 `*OK.py` 共 **407**（＝402 A 类 ＋ 3 非 A 类 ＋ 2 孤儿，已在 `baseline/exclusion_evidence.md` 登记）；**字面 `*+OK.py` 计数 0**——命名约定为「同名＋OK」，无加号 | ✓（约定名以文档为准，此点写清防误读） |
| 3 | 反编译前后字节码一致函数有多少、成功率多少 | 同一脚本口径：**units 6577/6617 = 99.3955%**；files 386/402 = 96.02% | ✓ 读数有凭（未达 100%） |
| 4 | 每轮 ≥1 个 pyc 由 failure 转 success，否则禁止下一轮 | Round 9：`finance` 31/32→32/32、`function` 70/71→71/71（逐单元名单核对，`REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`） | ✓ Round 9 达标；**Round 10 尚未达标** |
| 5 | 修复到完全 OK 后先单验 `quotation.pyc`，再批量回归 | 本轮实测 `single` ＝ **153/153 status=success**；八分片批量已跑（402 重生成 `bad=0`） | ✓ |
| 6 | 必须用 `scripts/pyc_verify.py` 验证（替换旧 `pyc_batch_verify.py`） | 全部读数出自该脚本 `batch/single/compare/selfcheck`；尺子自检 153/153 自证 ∧ 常量／极性变异各抓到 | ✓ |
| 7 | 所有命令 ≤300 秒 | 402 重生成 8 片各 21–28s；8 片 verify 各 11–32s；六套件 3.1s；最长的 `verify all34` 已按内部 290s 上限拆分并记录 | ✓ |
| 8 | 调用子代理前必须提交到本地 | 每次派发前均有本地提交（#16 派发前 `5ad5d36f…`，#13-P0 派发前 `9243b2ce`），`git log` 可证 | ✓ |
| 9 | **每轮必须提交并 push 到远程** | Round 9 起的多次 push 均实测成交，本文件成稿前刚核过：`106695dd / 3ed58f77 / 59f34459 / 3101d1fe / 9ada300b` 五个引用哈希对 `origin/rr-v3-full-corpus` **均为祖先**（`git merge-base --is-ancestor` 逐个跑，非凭印象）；**但 Round 10 现 `ahead=8`**（`git push` 连续 `Out of memory, malloc failed (524288000 bytes)`，此前另有连接重置／443 不通／一次认证失败） | ✗ **本轮 push 未成交**，须 `ahead=0` 才算闭 |
| 10 | 禁止修改反编译生成的文件 | 产物只由 `pycdc.py -o` 先删后产；`git status -- site-packages` 只出现重生成的差异，无手改痕迹；回滚工单时连产物一并重生并复验 118/128、32/32、71/71 | ✓ |
| 11 | 每轮独立文件夹 + 三角色分工（测试工程师→修复工程师→主代理验证） | `rounds/round1..round10/`、`test_repros/roundN/`；主代理未实现修复（G7 一次例外已登记）；两次工程师截断均按字节自有复测裁定 | ✓（截断风险已改为「单机制一票」） |
| 12 | 判据只取白名单事实；无禁止前缀；无硬编码上限 | Round 9 落地票：G3 前缀命中 0、G4 特判命中 0、新增 `print(` 0；B126 回滚票同样为 0 | ✓（但本轮**新查出存量违例**：`MIN_INSTRS_FOR_SUBSCR_ASSIGN` 1 定义＋6 使用，`IMPORT_NAME` 走查 4 份不同硬宽窗口——见 #13/#23） |
| 13 | 触及方法 docstring 六项模板 ＋ C 条款 | 实测 `_identify_*` 12 个方法中**仅 1 个**含 ①–⑥ 与 C1/C2/C3（`_identify_boolop_regions`），其余 11 个 50–148 行长注释但无模板 | ✗ **Task 11 未做**（起点已量化，`TASK11_COMMENT_AUDIT_BRIEF.md`） |
| 14 | 终态 402 全量 100%、files 402/402、0 compile_error、0 error | `rounds/round9/after` 八份报告 `paths_by_status` 聚合＝**success 386 / failure 16 / compile_error 0 / error 0**（可直接重算：对每份报告该字段的列表取长度求和） | ✗ |
| 15 | `site-packages/fly/data/quotation.pyc` single 153/153 success | 实测 153/153 | ✓ |
| 16 | tests 六套件零新增失败 | 2 failed / 277 passed / 2 xpassed，失败恰为基线那二条 | ✓ |
| 17 | 未达 100% 时如实上报残余（文件×单元×违反条款），未改判据未凑读数未删语料 | `rounds/round10/UNITMAP_R10.md` 40 条逐单元具名清单 ＋ §十二 收尾断言（具名 33／半具名 7／未具名 0）；语料 1722 pyc 计数未动，867 长路径缺件为工作树固有状态未「清理」 | ✓（残余如实） |

## 二、还差什么（按证据而非按感觉）

1. **40 个单元**（16 文件）——已按机制分派：#14 纯落点／锚点／换位（含 4 个「只差 1 单元」文件）、
   #15 隐式尾声与共用返回（7 单元、含 1 个可翻正文件）、#13 P0 在飞（`matcher` 1 文件）、
   #13 次刀（`clock_worker` 等）、#21（`<genexpr>` 操作数链 2 单元）、#22（`order_api` 2 单元）、
   #23（函数内 `import` 硬编码窗口）、以及 **`_process_order`/`_process_cancel_order` 的发射截断**
   （27 块→4 块、17 块→4 块）须 **#16 共要件补丁 ＋ A1 认领面判据**同轮共担。
2. **push 未成交**（`ahead=8`）：内存不足使 `git push` 失败，待工程师跑完释放内存后续推，
   并在本轮 `VERIFICATION.md` 记 `ahead=0` 的实测时刻。
3. **Task 11 注释合规**：12 个 `_identify_*` 逐方法过审 ＋ 常驻检查器 ＋ 反向夹钳。
4. **轮次**：规范为 10 轮，现第 10 轮在飞；10 轮用尽仍未达 100% 时，按第 17 条上报残余清单，
   **不得**以「读数接近」代行完成。

## 三、完成判据（达成才允许 UpdateGoal complete）

`units_success == units_total == 6617` ∧ `files success == 402` ∧ `compile_error == 0` ∧ `error == 0`
∧ `quotation single == 153/153` ∧ 六套件零新增失败 ∧ 每个 A 类 pyc 同目录 `<stem>OK.py` 存在且逐单元 Equal
∧ 本轮已提交并 `ahead=0` ∧ Task 11 逐方法过审无注释／行为矛盾。
**以上任一项不成立，则本目标未完成。**
