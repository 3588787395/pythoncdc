# Round 11 实测翻正记录（只登记我亲自量到的读数，不转录工程师的自报数）

## 1. B133 case 1 — `fly/dumpload/load_daily.pyc` **27/27 status=success**

时间 2026-10-08 04:49。验证方式**不入仓库**：施工者当时仍在 A/B 之间来回还原镜像
（12:26 我取到的 `region_analyzer.py` 仍是封表字节 38a1d5142d132fd7，12:43 才变成 4db00de8e56b2503），
而 `region_analyzer.py:3332-3349 _compute_arm_level_join` 改的正是**臂级汇合点选择**，
与同时在跑的 B134（bar / strategy_universe 纯落点）、B136（handlers 环出口落点）、B137（strategy 四处目标差）
是同一族判据——若把改后字节装进仓库，三张诊断票的行号锚点与实际行为都会漂。
故我在**自己的镜像** `D:/Temp/r11b133/wt` 里复验：

| 项 | 值 |
|---|---|
| 镜像 `core/cfg/region_analyzer.py` | `4db00de8e56b2503`（改后） |
| 镜像 `core/cfg/region_ast_generator.py` | `e9a8f65f6451bcc8`（封表，未动） |
| `fly/dumpload/load_daily.pyc` | 26/27 → **27/27 status=success**（整文件翻正） |
| `fly/data/quotation.pyc` | **153/153** 不回退 |
| `IQCommon/util/trade_info_utils.pyc` | 37/41（**未**变 38/41） |
| `matcher` 16/17、`handlers` 29/30 | 不变（与该票无关，符合预期） |
| 仓库 `git status --porcelain -- core/` | 0（仓库字节未被本次验证触碰） |

**该字节状态只含 case 1**：`trade_info_utils` 保持 37/41 而非施工者报的 38/41，说明这次取到的镜像文件
只落了 case 1（`_compute_arm_level_join` 的越区汇合证据否证），case 2（`_try_body_terminates_abnormally`
在 `self.regions` 未填充阶段读它）不在其中。两半各自移动自己靶的字节这一点与施工者的 A/B 表一致。

## 2. 落地前置条件（顺序不可颠倒）

1. 等 B133 交付最终补丁（含两半）并声明终态；
2. 等 B134/B136/B137 三张诊断票返回（它们正在读 `core/` 的行号与行为，装补丁会让锚点漂，
   本 session 已因此作废过工单）；
3. 用 `install_and_measure.sh` 装入（备份原字节 → 整份复制 → `py_compile` → 标记计数 →
   landed sha 与原字节相同即 exit 3 拒绝空转安装）；
4. 跑整链路 `gate_round.py 11 10 --stage regen/verify/report/checks` + `residual_report.py 11 10`，
   `regen` 若非 `ok=402 bad=0` 则**先 stat 产物尺寸再读 report**（本轮 9 单元假回退即出自 99 字节残次产物）；
5. 四项门禁必须为 0 才记翻正；任一哨兵回退即按 sha256 逐字节回滚并把证据留档。
