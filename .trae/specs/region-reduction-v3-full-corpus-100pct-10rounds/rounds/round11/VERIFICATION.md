# Round 11 门禁验证（region-reduction-v3-full-corpus-100pct-10rounds 续轮）

判据与口径完全沿用 round 10：唯一判据 `scripts/pyc_verify.py`（pylingual `compare_pyc`，
CPython 3.11.7 64 位，**只比较不产码** ⇒ 每项读数前必先按当前字节删除旧产物再 `pycdc.py -o`）；
产物一律流水线上重生成，未手改任何 `*OK.py`。
对照基线 = `rounds/round10/after/`（封表字节实测：6577/6617 单元、386/402 文件、
残余 16 文件 / 40 单元、`regen ok=400 bad=2` 的两例残次产物见 round 10 档 §九）。

## 一、落地清单

| 票 | 机制 | 落地状态 | 装前筛（镜像，16 残余文件，按失败单元**名集合**比较） |
|---|---|---|---|
| **B133** | `region_analyzer._compute_arm_level_join` 新增 `(4c)`「双臂共落点」认领（一臂无条件前向跳入 ∧ 另一臂 fall-through 入、两臂集不相交、J 不在臂内子区域），与发射端 `[R9-B124]/[R9-B125]` 同判据的两半；第二半重写 `_try_body_terminates_abnormally`（不再在未填充阶段读 `self.regions`） | **已装入**：`core/cfg/region_analyzer.py` sha256 前 16 位 `e926a54f17753b33`（原字节留档 `D:/Temp/r10gate/pre_b133_analyzer.py`），`py_compile` 通过，标记 `_armjoin_is_dual_role_meeting` / `[r10-b133-armjoin-dualrole]` 各 3 次 | 706 → **709** 单元；`load_daily` 26/27→**27/27**（整文件翻正）、`klinedata` 61→62、`trade_info_utils` 37→38；其余 13 文件 0 变化；**regressions = []**；quotation 153/153 不回退。详见 `MEASURED_FLIPS.md` §8 |
| B139 | or 短路链被折叠成嵌套 if（bar `A and B or C`、su `¬A∨¬B`、strategy `A∨B∨C` 三形同一族） | ⟨填：是否落地；补丁 `D:/Temp/r139b/b139.patch`⟩ | ⟨填：r139_ 电池 16 臂基线与改后逐臂读数⟩ |
| B127 / B129 / B132 | 见 `rounds/round10/VERIFICATION.md` §二 | 均已否证并逐字节回滚 | — |

## 二、门禁读数（label 11 / before 10）

| # | 门禁项 | 命令 | round10 基线 | round11 终态 |
|---|---|---|---|---|
| 1 | 402 全量重生成 | `gate_round.py 11 10 --stage regen` | ok=402 bad=0（首轮 ok=400 bad=2 系产码器残次产物，非代码问题） | ⟨填⟩ |
| 2 | 逐文件逐单元比较 | `--stage verify` + `--stage report` | 6577/6617（99.3955%）、386/402 | ⟨填⟩ |
| 3 | 四项硬门禁 | 同上 report 段 | 文件级回退 0 ∧ UNIT_REGRESSIONS 0 ∧ 新增失败单元 0 | ⟨填：翻正单元须列名⟩ |
| 4 | quotation | `single site-packages/fly/data/quotation.pyc` | 153/153 | ⟨填⟩ |
| 5 | small34 | `batch --index baseline/small34_index.json` | 1528/1568，34 文件中 18 全绿 | ⟨填⟩ |
| 6 | 尺子自检 | `selfcheck` | 153/153 Equal；变异常量 1/153、极性 1/153 | ⟨填⟩ |
| 7 | pytest 七套件 | `--stage checks` | 2 failed / 280 passed / 2 xpassed，二红同名 ⇒ 零新增失败 | ⟨填⟩ |
| 8 | 残余表 | `residual_report.py 11 10` | 16 文件 / 40 单元，UNREGISTERED=0 | ⟨填⟩ |

## 三、纪律核对

- 装前筛在**镜像**内完成，仓库 `core/` 与 `site-packages/` 在读回前未被施工触碰（`git status` 复验）；
- 任一硬门禁非 0 ⇒ `cp /d/Temp/r10gate/pre_b133_analyzer.py core/cfg/region_analyzer.py` 逐字节回滚，
  补丁留档不落地；
- 工程师 A/B 表与主代理实测不一致时以**主代理实测**为准（本票两处：case-2 标记名自拟致误判、
  「case 1 单独不动 trade_info_utils」在最终字节下不成立）；
- 引用他票行号须先按 `MEASURED_FLIPS.md` §9 的漂移量（`>11524` 为 +195、`3051..11524` 为 +76）
  换算并逐条 grep 复验。
