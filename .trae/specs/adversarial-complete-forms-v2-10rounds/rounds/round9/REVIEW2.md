# Round 9 复核评审报告 REVIEW2（任务 9.3，对抗评审）

- 复核对象：HEAD = `42fe45fe`（批次 = `58ed696b` → `3803fa73` → `42fe45fe`，基线 `a2d1e15e`，合并树 `e42b8509`）。
- 复核方式：独立隔离树复跑（`d:\Temp\opencode\r9rev2\armtree`，逐臂 robocopy 还原，工作区零触碰）；不采信未附证据的声明；数据集复跑 = 归约器只读插桩 + `pycdc -o` regen + `scripts/pyc_verify.py single`。
- 复核证据（本轮，前缀 `r9v9rev2_`）：`r9v9rev2_arm_b126.json`（六臂/守卫计数/散列/diffcheck/聚合）、`r9v9rev2_attr_assert_deep_{HEAD,R1OFF}.json`、`r9v9rev2_attr_assert_chain_{HEAD,R1OFF}.json`、`r9v9rev2_attr_r810_at_{HEAD,R1OFF}.json`。

## §1 逐族裁定

| # | 族 | 声明（FIX_R9） | 复核实测 | 裁定 |
|---|---|---|---|---|
| 1 | §1 B104（analyzer 扩门 + generator 三扩门一因子化，`_extract_recheck_store_stmts`/`_r2166_seg_set`/`_r2166_mixed_seq_set`/路B 多语句） | 14 单元全转 MATCH | B104_main 14/14、chain4 6/6、chain5 5/5、opdeep 4/4、exprtail 4/5（v3=B123 存量）、e05 6/11、e10 32/32、n9_whilehost 9/9；因子化 = 旧内联逐位等价（diff 逐行比对，`split_expr_stmts` 仅路 B） | **通过** |
| 2 | §1.5 B124 双桶（[B124-R1] 自足 return 扩门 + [B124-R2a/R2b] 生成器守卫） | e05 3→6/11、e10 31→32/32、r8_10 8→9/12 | 三读数逐位复现；[B104-R3] 门保留且为加性扩门（`and not _b124r1_chain_region_is_self_return(region)`，删行无回滚） | **通过** |
| 3 | §2 B125（[B125-R1] 祖先链排除） | b109_loopelse 8→9/9、r5v5_13 10→11/11 | 两读数复现；判据 = `region.parent` 链成员关系；关闭对照臂 `r9v9fix_b125_arm.py` 在案 | **通过** |
| 4 | §3 B126（[B126-R2] 异常路径尾闩守卫） | n9_stmt_sweep 5→6/6；r8_07 10/11 不回退 | **R2 承重实证**：R2-off 臂复现 pre 态 5/6（assert_deep `Different control flow`）；HEAD 上守卫实际命中 `sites=[76,74]`（calls=2 hits=2）；产物 `assert 0 < a < b, a; a += 1` + `return a` 无 else，与声明逐字一致 | **R2 部分通过；本族整体打回（见 R-1）** |
| 5 | §4 尽力项移交（B127/B128/Yield 探针重建/B44） | 未修复、整体移交 round10 | 四行均如实标注"未修复"，读数与 REVIEW 登记一致；口径与 REVIEW §6 位D「低优先整体移交」一致 | **通过（移交合法性）** |

## §2 打回/必改清单

**R-1（打回项，零容忍 · 声明-diff 不一致 + 未声明活性改动）**：`_b126_claimed`（`[B126-R1 认领集补守卫]`，`region_analyzer.py` :19114-19119 docstring / :19205 定义 / :19214 守卫 / :19369 更新）在 HEAD **活跃**且改变区域模型（assert_deep：HEAD=1 个 AssertRegion，R1-off=2 个），但：

1. `FIX_R9.md` 全文（含 §3）**零处声明**该变更（grep `B126-R1|认领集|claimed` 零命中），§3 明确写「取 **E6 判据面**（守卫单点，**不做认领扩展**）」——与树内事实相反；
2. 由 `3803fa73` 引入（`git log -S` 唯一命中；该 commit message 自述「B126 **诊断**已启动（diag_b126）待续作」且把 analyzer 增量全部归给 B124-R1），`42fe45fe`（自述「唯改 region_analyzer.py +112/-4」，只声明 R2）未移除；
3. 臂实验证明其对已声明读数**非必需**：R1-off（R2 保持开）→ n9_stmt_sweep **6/6**、r8_07 **10/11**、r8_10 **9/12**、x08 **6/8**，且四个单元产物与 HEAD **逐字节相同**（sha256 见 `r9v9rev2_arm_b126.json`）——即 R2 单点即可支撑全部 §3 声明；R1 属未披露的模型面活性改动（其 docstring 所述"双 assert ⇒ 幻影 break"因果链在 R2 落地后已不成立）。

> 处理（二选一，修复方执行）：(a) **移除 R1**（与 §3「不做认领扩展/E6 单点」一致），重跑 §3 读数 + §5 七面确认不回退（本轮已证 §3 四个靶单元不依赖 R1，七面需全量）；或 (b) **保留 R1 并补声明**：在 FIX_R9 §3 写成 [B126-R1]+[B126-R2] 双组件，附 E4（守卫+扩展全对）裁决证据与七面重跑。任一选择后需更新 §3 判据段与 I.7。

**R-2（文档数字必改，低危）**：`FIX_R9.md` §5 合计分母 `2182` 与同表逐行之和 **2161** 不符（独立聚合六面 `423+251+196+446+692+153=2161`，分子 `2092` 逐位吻合；证据 `r9v9rev2_arm_b126.json::station_faces_aggregate`）。另 §5 标题「七面」与表内 6 行不一致。请对齐口径（改 2161 或补第 7 面行）。

**R-3（证据出处缺口，轻）**：§3 行 94「浅层 r8_assert_chain 28/30 块归属不动」无任何可复核出处（该单元实测仅 6 块；R2 守卫在其上调用次数 = **0** ⇒ "不动"平凡成立）。建议改为可复核表述（"R2 守卫在浅层不触发，调用计数 0"）或补证据件。

## §3 禁回滚核验（REVIEW §4 承重实证）

批次 diff（`a2d1e15e..42fe45fe -- core/`）共 64 删除行，逐行归属审计完毕：全部落在声明区内（[B124-R1] 门后移 reorder、[B104-R9] 因子化替换、[B125-R1] 单行扩、[B126-R2]/[B126-R1]、R101 docstring 缩进重排）；匹配 `B99|R21-15|R21-36|H1-H4|released` 的删行 = **0**；[B104-R3] released 门**保留且为加性扩门**（旧 `... in SHORT_CIRCUIT_JUMP_OPS):` → 新 `... in SHORT_CIRCUIT_JUMP_OPS and not self._b124r1_chain_region_is_self_return(region):`，命中面只增不减）。**通过**。

## §4 黑名单判据扫描（I.4）

批次新增行扫描：探针/单元名（逻辑引用）0、`co_name` 0、文件名/路径 0、数值偏移比较 0、跨层 entry 反查 0、新增 self 状态 0、调试 print/breakpoint 0、ARM/插桩标记 0（仅 I.7 注释内提及探针名，属允许）。`_variable` 级判据 = 块内 opcode 序 / 区域成员关系 / 声明式链长上限。**通过**。

## §5 站桩 / 34 集 / 承重面

- 七面聚合独立复算：round1face 423/423、quotation 153/153、round2face 245/251、probe42 179/196、residual 420/446、oldface 672/692 ⇒ **2092**（分母见 R-2）。
- 逐单元失败集比差（`r9v9rev2_diffcheck.py`，pre 备份 `d:\Temp\opencode\r9v9_station_pre_b126` vs 终态）：**pass→fail = 0**；fail→pass = 3（r8_x_with_ternary ×2 面 + raise_leaf），与 §5 声明逐位一致。**通过**。
- 34 集 8 片：34/34 文件 success、**1568/1568**、failure/error/compile_error 全 0 ⇒ NEWFAIL=0。**通过**。
- 承重面独立复跑全绿：matcher 17/17、nb_for/nb_with/nb_while 各 2/2、nb_b99 4/4、broker 128/128、finance 32/32、quote_handler 79/79、realtime 13/13、quotation 153/153。**通过**。

## §6 卫生

工作区 `git status` clean、`git diff --stat HEAD` 空（复核全程未触碰主干，臂实验仅在隔离副本）；三提交 `--name-only` 无 `*OK.py`/`.pyc`/`test_repros` 副产物；两文件单 BOM 头维持；零插桩/零调试残留。**通过**。

## §7 终态裁定

- 通过：§1 B104、§1.5 B124、§2 B125、§3 的 [B126-R2] 承重与读数、§4 移交合法性、§5 站桩（数值口径除外）、34 集、承重面、禁回滚、黑名单、卫生。
- **打回：§3 位C 整体（R-1：`_b126_claimed` 未声明活性改动，须移除或补声明并复跑 §5）**；R-2/R-3 为文档必改。复核证据均为只读复跑产物，未修改任何 core / 既有证据 / 提交。
