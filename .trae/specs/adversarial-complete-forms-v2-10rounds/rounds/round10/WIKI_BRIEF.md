# Round 10 · 10.2 派发简报：wiki §8.2 复审六步全量重验与增量更新（评审工程师执行，主代理验收）

## 任务
执行 wiki §8.2 复审六步（定义见 `wiki/concepts/decompile-invariant-completeness.md` §8.2，2026-10-04 v6 首跑后**首度全量重验 + B77+ 增量**）：
1. fix 批归档落位确认（本规范 round1-9 各批次提交已在 origin/main；见文末提交链）
2. **grep 全部落地标记**确认代码真在树（I.6 纪律：含本规范各轮「代码已落地」声明 + B77+ 核验）
3. 台账（§5）全量更新：III.2–III.4 全 128 形态 II.3 三态判定落位 + 组合级挂账分层（清零或如实分层）
4. 路径层重跑 `tools/kb/syntax_coverage.py`（输出 `docs/refactor/syntax-coverage.json`）
5. 占比重算（II.1 口径 = 完备形态数 ÷ 128）、页面数字同步（禁手改、禁矛盾数字）
6. `wiki/log.md` 记录迭代 + 破口状态变迁

## 输入锚点
- 本规范 `rounds/round9/`：
  - `REVIEW_DRAFT.md`（9.1：三态 128 = 完备 101 / 破口 27 / 零能力 0；§1 全部专项实证；§3.2 移交族维持读数；§6 位D 队列；**台账落账路径 = 25 行 v2 轮次确证 + 2 行合并翻案 + B124-B128 统一落账**）
  - `FIX_R9.md`（142 行终态；三段存证 58ed696b/3803fa73/42fe45fe；本轮封闭 B104 族 14 + 存量 B104-R4、B124 族 5、B125 族 2、B126 族 1；§4 移交 B127/B128/Yield 探针重建/B44）
  - `REVIEW2.md`（首判打回 3 项 → 整改）、`REVIEW3.md`（终审放行）、`VERIFICATION.md`（9.4 六步实录）
- 本轮落地标记（grep 验证候选，以代码实证为准）：
  - round9：`[B104-R9`、`[B104-R4]`、`_extract_recheck_store_stmts`、`[B124-R1`、`_b124r1_chain_region_is_self_return`、`[B124-R2a`、`[B124-R2b`、`_ternary_host_call_prefix_span`、`[B125-R1`、`_child_region_blocks_r23`、`[B126-R2`、`_b126r2_raise_only_trampoline_exit`；`[B126-R1` / `_b126_claimed` **应 0 命中**（9.3b 已移除）
  - 前八轮（§8.1 表既有 + 8.x 归档）：B106-R3、B109、B110/B112/B113、B118/B119/B120/B121、B83、B77、B81、B102、B96、B98-R1、B82、B103、B104-R2a/R2b、B105-R2、B107-R2 等逐一复核「已落地/已封闭」仍成立
  - 每轮提交前缀 `rr-v2rNN:`；§8.1 表状态列「2026-10-04 终审」须更新至 2026-10-17
- 旧 round10（v6 首跑）先例（格式参照，勿回改）：`.trae/specs/harden-completed-forms-10rounds/rounds/round10/`（提交 72f46912→b53d449c→0caea12b→f831eeae）
- 判定口径：II.1 完备占比 = 完备形态数 ÷ 128（分母不取 RegionType 枚举/语料）；II.3 三态 = 完备/破口/零能力；§8.3 状态机 = 未定位→已定位→已落地→已复审（**仅已复审入分子**）
- III.5 组合级挂账 25 号透明分层 + B77+ 破口登记（B124/B125/B126/B127/B128 新编号、Yield 行探针状态、B44 证据缺口）

## 交付物（全部落盘）
1. 更新 `wiki/concepts/decompile-invariant-completeness.md`：§0 当前读数、§5（5.2/5.3/5.4 表 + 5.5 判定汇总）、§6 破口登记与已封闭守卫族（增 B124-B128/Yield/B44 行；状态机落位）、§8.1 标记表（状态列更新至 2026-10-17）
2. 更新 `wiki/log.md`：追加本规范迭代记录 + 破口状态变迁（含提交号；旧规范已记勿重复、禁矛盾）
3. 重跑 `tools/kb/syntax_coverage.py` → `docs/refactor/syntax-coverage.json`（记录 sha256）
4. `rounds/round10/WIKI_REVIEW.md`：六步逐步实录（每步命令 + 结果 + 证据），含——
   - grep 标记全表（标记 | 命中文件:行 | 状态判定；0 命中项如实列）
   - 128 形态三态终表（完备 X / 破口 Y / 零能力 Z）+ 与 round9 评审（101/27/0）增量对照（哪行升完备、依据哪次修复/哪条证据）
   - 组合级挂账 25 号分层终表（清零 X 项 / 维持 Y 项，每项一行口径）
   - 完备占比重算（II.1）与新值
   - 数字同步核对表（页面全部数字 vs 工具输出/台账一致；禁矛盾）
5. `rounds/round10/r10v10_wiki_marks.json`：grep 结果机器可读
6. `rounds/round10/r10v10_coverage_before.json` / `_after.json`：coverage 前后快照 + sha256

## 纪律（硬约束）
- **禁止改代码**（`core/` 零改动）；只动 `wiki/`、`docs/refactor/syntax-coverage.json`（工具输出）、`rounds/round10/` 证据
- 禁止手改工具输出数字；页面所有数字必须可由 syntax-coverage.json / §5 汇总推得
- 每个 grep 实名实证；**「声明已落地但 grep 不中」= 重大发现**，写入 WIKI_REVIEW.md「异常」节，勿自行修代码（主代理裁决）
- 完备占比分子只计「已复审」行；破口不计分子
- 命令 ≤300s 分片；python 一律 `python -X utf8`

## 本规范提交链（供步骤 1 核对）
`f831eeae/fc2aa1b1`（前序规范终态补推）→ Round 1–8 各 `rr-v2rNN:` 提交（`5f784272..91f8d27d`）→ merge gate `e42b8509` → round9 修复 `58ed696b/3803fa73/42fe45fe` → 复核 `3b0cc343/c1fa6fcf/c1a0c53f` → 9.4/9.5 归档 `64314aed/9a3d681c/0ad55951` → round10 套件 `a8bc0abc/ea34ae03`
