# Round 9 终审复核报告 REVIEW3（任务 9.3c，整改批终审）

- 复核对象：HEAD = `c1fa6fcf`（9.3b 整改批，父 `3b0cc343` = REVIEW2；批次链 `58ed696b` → `3803fa73` → `42fe45fe` → `3b0cc343` → `c1fa6fcf`；基线 `a2d1e15e`）。
- 复核方式：独立复跑（临时目录 `pycdc -o` regen + `scripts/pyc_verify.py single <pyc> --source <regen 产物>`，工作区零触碰）；tree diff 逐字比对（逐行反序/上下文窗口）；站桩 3 分片 live 重跑 + 17 分片聚合独立复算；pre 备份与 `e9110d21` 提交原件逐字节（sha256）校验。不采信未附证据的声明。
- 复核证据（本轮，前缀 `r9v9rev3_`，12 件）：`r9v9rev3_r1_removal.json`、`r9v9rev3_guard_attr.json`、`r9v9rev3_file_checks.json`、`r9v9rev3_compare.json`、`r9v9rev3_s3units.json`、`r9v9rev3_loopsfam_0_10.json`、`r9v9rev3_loopsfam_10_19.json`、`r9v9rev3_bearing.json`、`r9v9rev3_bearing2.json`、`r9v9rev3_station_residual_c54-72.json`、`r9v9rev3_station_oldface_c45-59.json`、`r9v9rev3_station_probe42_c28-42.json`。

## §1 整改项逐项裁定

| # | 项 | REVIEW2 裁定 | 整改声明（FIX_R9 §3 末段 :115 + 头 :6 + §5 :142） | 复核实测 | 裁定 |
|---|---|---|---|---|---|
| R-1 | `[B126-R1]` `_b126_claimed` 全量移除（方案 a） | **打回**（未声明活性改动，零容忍） | `git diff` = 1+/26- = `3803fa73` 增量逐字逆操作；树 = R1-off 态（assert_deep 1→2 个 AssertRegion）；承重 = `[B126-R2]` 单点 | **VERBATIM_INVERSE = true**：26 删行与 `3803fa73` R1 增量 26 增行按序逐字相等；唯一 +1 行 = 被还原守卫 `if isinstance(_existing_region, AssertRegion):`；R1 hunk 内无其他特性标记；c1fa6fcf 树 `_b126_claimed` = 0、`B126-R1` = 0；认领集 8 处→3 处（:19908/:19950/:19956 全为 [B104] 既有文档概念）；assert_deep = 2 个 AssertRegion（与 REVIEW2 R1OFF dump 逐位一致）；`core/` 唯一改动文件 = region_analyzer.py（numstat 1/26） | **通过** |
| R-2 | §5 合计分母 2182→2161、标题七面→六面 | 文档必改（低危） | 4 处改 2161；标题六面 | FIX_R9.md 142 行：`2161`×4、`2182`×0、`七面`×0、`六面`×6；表值与独立聚合（423+153+245+179+420+672）/（423+153+251+196+446+692）= **2092/2161** 逐位一致 | **通过** |
| R-3 | §3「浅层 28/30 块归属不动」改可复核表述 | 证据出处缺口（轻） | 改「R2 守卫在浅层 r8_assert_chain 上调用计数 0（不触发）⇒ 平凡成立」+ 引 `r9v9fix3b_s3_guard.json` | :95 表述在案、证据引用在案；独立复跑该证据件读数 `calls=0 hits=0` 逐位一致；行 :104-105 g2 校正「渲染存续折叠、非字节等价、R2-off 同形、非本修复引入」在案，且 live 复跑 probe_break_raise 3/4（g2）失败面一致 | **通过** |

## §2 R-1 移除正确性（逐字逆操作核验）

- 树差 `3b0cc343..c1fa6fcf -- core/`：单文件 `core/cfg/region_analyzer.py`，numstat `1 + / 26 -`，4 hunk 全落 R1 四站点（:19111 docstring / :19188 定义 / :19211 守卫 / :19363 更新点）。
- 26 删行 == `3803fa73` 的 26 增行（按序逐字）；+1 行 == `3803fa73` 的删行（原守卫还原）；R1 hunk 内无其他特性标记（`no_other_feature_markers_in_r1_hunks=[]`）。
- 触点外零改：未触及 `_b124r1_*`/`_b126r2_*`/`_extract_recheck_store_stmts`/B104-R9/B125-R1/B104-R3；守卫上下文窗口（58ed696b vs c1fa6fcf）逐字相同。
- 模型面 = R1-off：assert_deep 守卫 `calls=2 hits=2 sites=[(76,True),(74,True)]`、AssertRegion = 2；`r8_assert_chain calls=0`；`raise_leaf calls=1 hits=1 site=42`；`g1/g2 calls=1 hits=0 site=14` —— 与证据件 `r9v9fix3b_s3_guard.json` 逐位一致。

## §3 读数抽验（live 重跑，regen + `--source`）

- §3 六单元：n9_stmt_sweep **6/6**、r8_07 **10/11**、r8_10 **9/12**、x08 **6/8**、probe_for_assert **3/3**、probe_break_raise **3/4**（g2）——与 `r9v9fix3b_s3_units.json` 逐位一致。
- 循环族 **68/68** + B104_main **14/14**（loopsfam live 82/82）；B104 族 9 探针（e05 6/11、e10 32/32、chain4 6/6、chain5 5/5、foror 3/3、opdeep 4/4、exprtail 4/5、b102 8/10、b96 14/18）与证据一致。
- live 探针 vs 证据逐位比对（`r9v9rev3_compare.json`）：s3 六单元 + loopsfam/fam 19 探针，**mismatches = 0**。
- station 3 分片 live 重跑：residual c54-72 **95/95**、oldface c45-59 **331/331**、probe42 c28-42 **70/81**（失败清单逐项一致：x01 4/7、x02 5/7、x03 6/7、x04 6/7、x05 6/7、x08 6/8、x10 2/3）——与 fix3b 分片读数逐位一致。

## §4 不回退核验

- pre 备份真实性：`d:\Temp\opencode\r9v9_station_pre_b126` 与基线提交 `e9110d21` 原件逐字节相等（sha256；residual c18-36 / oldface c30-45 / probe42 c28-42 三件抽验）。
- 比差复算：**pass→fail = 0**；fail→pass = 3（r8_x_with_ternary ×2 面 + raise_leaf），与 `42fe45fe` 声明逐位一致。
- fix3b 分片 vs fix3 正式分片（round9 内 `r9v9_*`）：17 片逐单元 `identical_all_shards = true`（R1 移除对六面读数零效应）；副本 == temp 原件 17/17；聚合独立复算 = **2092/2161**。
- 34 集：8 片独立重算 = 34 文件 **1568/1568**，failure/error/compile_error 全 0（NEWFAIL = []）。
- 承重面 live 全绿（10 目标 432 单元）：broker 128/128、matcher 17/17、finance 32/32、quote_handler 79/79、realtime 13/13、quotation 153/153、nb_for 2/2、nb_with 2/2、nb_while 2/2、nb_b99 4/4。

## §5 卫生

- c1fa6fcf 39 文件无 `*OK.py`/`.pyc`/`test_repros` 副产物；证据 `r9v9fix3b_*` **37 件**在案。
- 两 core 文件单 BOM（count=1，仅头）；批次 diff 中 `[T]` 唯一命中 = region_ast_generator.py 注释行（[B124-R2b] 分析记录，非插桩）；零调试 print/breakpoint。
- 复核全程工作区 clean（`git status --porcelain` 空）；本轮仅新增 `r9v9rev3_*` 证据 12 件与本报告，未改 core、未改既有证据、未 commit。

## §6 终态裁定

- **放行**。R-1 逐字逆操作核验通过（树 = R1-off 态、承重 = R2 单点、声明-diff 一致）；R-2/R-3 已改且可独立复核；六面 2092/2161 零 pass→fail；34 集 1568/1568；承重面全绿；卫生通过。
- 遗留（维持 REVIEW2 §4/§5 移交口径，均非本批引入、比差 pass→fail=0）：B127 f_slice_expr_bounds 15/16、B128 f_await_cond_pos 10/11、Yield 探针重建、B44 证据缺口；存量失败面（r8_07 10/11、x08 6/8、probe42 179/196、residual 420/446、oldface 672/692、round2face 245/251、exprtail 4/5、b102 8/10、b96 14/18 等）。
- 复核证据 12 件 `r9v9rev3_*` 随本报告落档于本目录；全部为只读复跑产物。
