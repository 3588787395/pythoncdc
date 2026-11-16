# rr-v5 语料战役 · 中期状态报告（截至 4753cc05 / rr-v5r181）

> 本报告只陈述**已实测**的事实，并明确区分「判官上界口径」与「保守口径」。
> 不宣称 `product_complete`，不宣称 G1/G2c/G3/G4/G6 PASS。

## 一、语料判官读数轨迹（本战役起点 = rr-v5r160 / f7d80873）

| 语料 | 起点 | 现状 | 提升 | 剩余失败单元 |
|---|---|---|---|---|
| urllib.request | 188/194（96.9%） | **194/194（100%）** | +6 | — |
| difflib | 61/62（98.4%） | **62/62（100%）** | +1 | — |
| tarfile | 146/160（91.25%） | **157/160（98.1%）** | +11 | `TarFile.next`、`main`（+`TarFile.add` 为测量性差异）。**注：`_Stream._read` 已于 rr-v5r171 `[v171-ITER-EXIT]` 侧获闭合；`_FileInFile.read` 已于 rr-v5r184 闭合（M1 循环头合并窄守卫 + M2 while 体内链式比较链区归属两机制同改）** |
| cookiejar | 91/105（86.7%） | **103/105（98.1%）** | +12 | `_timegm`、`DefaultCookiePolicy.set_ok_path` |
| subprocess | 68/78（87.2%） | **75/78（96.2%）** | +7 | `Popen.__init__`、`_internal_poll`、`_wait` |

**四语料合计：590/599 = 98.50%**（判官口径，**上界**——见第四节口径说明）。

## 二、已落地的根因族（20 个提交 / 24 个已登记族 + 1 个已回退 BLOCKED 轮）

| 轮次 | 域 | 效果 | 提交 |
|---|---|---|---|
| rr-v5r161 | NOTMIX（融合 not 头专用探测） | request 189→190 | `d900a90a` |
| rr-v5r162 | CHAINGRAFT（尾 elif 降级 + 假 elif 嫁接） | request 190→192 | `75bb916b` |
| rr-v5r163 | for-iterable 归属越界 | request 192→193 | `6b5b3a4a` |
| rr-v5r164 | NOTMIX-HEAD2（非链首残形 + 元组解包复原） | request 193→**194** | `37cb12e7` |
| rr-v5r165 | CHAINGRAPH 族 C（多块条件链边归属） | tarfile 146→149 | `a1de8c5f` |
| rr-v5r166 | 发射侧隐式汇流误判 | tarfile 149→150 | `cbbac9e6` |
| rr-v5r167 | CJB 臂判定（汇合点误判）+ C7 回归拦截 | tarfile 150→151；subprocess 68→69 | `33d82ce1` |
| rr-v5r168 | %-组蒸发 + 三元宿主跨度尾段 | tarfile 151→152 | `10506602` |
| rr-v5r169 | 循环头语句边界 + 循环后父 If 汇合块 | tarfile 152→154 | `169e802b` |
| rr-v5r170 | 循环后块去嵌套 + 循环 or 链形态 | tarfile 154→155 | `7e12e48b` |
| rr-v5r171 | 重复 continue / 文档常量 | cookiejar 91→94；tarfile 155→156 | `d677817c` |
| rr-v5r172 | raise 表达式 / 负极性 and + 嵌套 try/finally | subprocess 69→71 | `9d236f9d` |
| rr-v5r173 | 链式赋值值链保持 | cookiejar 94→97 | `73ea3a0e` |
| rr-v5r174 | 条件链末段 / 汇点 merge（单跳子类） | cookiejar 97→100 | `645fb375` |
| rr-v5r175 | with 上下文值链白名单缺项 | subprocess 71→73 | `dfb5b7f8` |
| rr-v5r176 | 迭代出口臂 merge 归属 | cookiejar 100→101 | `bfd67c6e` |
| rr-v5r177 | 去重启发式误杀语句 | subprocess 73→74 | `fa2b708c` |
| rr-v5r178 | 幻影 if 重建（未发射 try handler 入口） | subprocess 74→75 | `1785e67a` |
| rr-v5r179 | `_wait`（SP7）**BLOCKED，已回退零改动** | — | 无提交 |
| rr-v5r180 | except 体显式 return 折叠 | cookiejar 101→102 | `a20aa311` |
| rr-v5r181 | try-else 臂尾自环回边归属 | cookiejar 102→103 | `4753cc05` |

每轮均通过同一套门禁（矩阵 19 案 / 458 案电池 / 五语料判官 / pytest 冻结基线 / S1 签名闸门 /
零触碰 38 案 / 红线单元集 / AST 剪枝检查），且**每轮为单个干净提交并 push**。

## 三、门禁状态（**诚实口径**）

| 门禁 | 状态 | 说明 |
|---|---|---|
| G1 | **未 PASS** | `uncovered = 376`，全部为 `unsafe_host_module: real-package`；rr-v5r76 审计结论「0 条可诚实闭合」。属**范围/证据决策**，非工程问题 |
| G2c | 未 PASS | 见 checklist 对应条目（B142 `break` 臂等） |
| G3（变异） | **未 PASS** | 样本读数 missed **602/634**；全量变异与调用模型补齐仍挂账 |
| G4（规则 witness） | **未 PASS** | proved **0** / open **342**（旧基线 339） |
| G5（全量） | **PASS**（2026-11-16 全量复跑） | 402 八分片 **6617/6617**、small34 **1568/1568**、quotation **153/153**、pytest 七套件 **2F/282P/2XP**（失败恒 B01+BOUNDARY_02）、IV.2 import/compile/BOM(efbbbf single-head×2)/G3 全绿；`gate_report.gate_g5` = **PASS**；validator `统计: 14 个错误, 6 个警告`（证据 `fresh/final_state/G5_READINGS.md`） |
| G6 | **未 PASS** | 无独立 custody，应记 `ASSURANCE_BLOCKED`（未用 local canary 冒充） |
| product_complete | **未达成** | 需 G1–G5 全绿；当前 G1/G3/G4 未绿 |

## 四、测量口径说明（Task 91 审计结论，必读）

1. **判官 EQUAL ≠ 文本保真**。构造样本 40 例中，恶性样本 24 例里有 **11 例判官仍给 EQUAL（45.8% 盲）**——集中在空体守卫、签名族（`/`、`*`、`*args`、`**kw`）、不可达尾部。
2. **真实语料交叉核对**：447 个判官 EQUAL 函数中 156 个文本不同（34.9%），其中 144 个原始字节码逐条相同、10 个残差逐个读过全良性，**真错 0/447**；规则扫描 170 个可疑点实判 142 个，**真错 0**。
3. **因此**：本报告的 98.50% 是**上界**；保守口径按函数级另算（Task 91 记录为 **437/447 = 97.76%**，与上界不可混算）。凡对外表述必须同时给出「上界 / 保守值 + 口径限定」。
4. **S1 签名闸门已常态化**：五语料 **594/594 函数签名一致、0 未配对**（累计 12 语料 1168 函数 0 误报，耗时 ~418ms），作为「判官 EQUAL ∧ S1==0 才记签名族可信」的附加闸门。
5. **已知记账陷阱**（跨轮复现，必须在复测前核对）：
   - difflib 原件须用 `D:/Python/Lib/__pycache__/difflib.cpython-311.pyc`（用 r147diag 版会得不同字节数；S1 仍用 r147diag 配对）；
   - R110 按 **TEXT 161 / 签名 167** 记账（不是 168/167；差额恰为落入允许集的 7 案）；
   - `TarFile.add`、`Popen._execute_child` 的异常表偏移平移属**测量性差异**（NOP/2B trampoline 造成），判官归一化后 EQUAL，严格字节口径会误报；
   - 多 agent 并行时，core 文件可能处于**补丁写入中间态**，读数必须「多时点 + sha 一致性」核验。
6. **电池 TEXT-DIFF 允许集**（17 项，全部 BYTE-EQUAL）：6 功效案（E161_*）+ v111 三案 + 8 个已登记同族形态改进案（`mk_iterencode`/`yp2`/`te_variants8`/`pc9`/`pm1`/`E3_andnot_nochainstmt`/`fdt`/`pc12`）；集外新增或非 BYTE-EQUAL 一律视为回归。

## 五、方法沉淀（本战役验证有效的做法）

1. **一族一轮、先证后改**：24 族中约三分之一真根因与 recon 定性不同（recon 比的是产物文本，判别信号常在更底层：识别层白名单、块归属、异常表归属）。
2. **同形歧义需找「不可伪造的特征」**：r180（`POP_EXCEPT.starts_line`）、r161（and 子链成员数）、r162（目标是否为臂汇合点）、r163（`GET_ITER` 前是否有 `STORE_*`）。
3. **红线机制**：每轮新修单元立刻进下一轮红线集（现 23 单元 + 38 案），连续十余轮守住既有成果。
4. **回归拦截优先于收益**：r167 的 `C7_skipedge`、r179 的 `_wait` 都因违反「只增不破」被拒绝提交/整体回退。
5. **判官盲区必须用其它证据兜底**：文本形态逐处对源码、异常表逐字段、AST 计数（`ast.If`/语句数/`Pass`）前后对比，专门捕捉「静默删代码 / 凭空造代码」。

## 六、剩余工作与风险

| 项 | 内容 | 性质/风险 |
|---|---|---|
| cookiejar 2 | `_timegm`（82→97 指令）、`set_ok_path`（38→60） | recon 标注的大改写，中高风险 |
| tarfile 3（+1 测量差） | `_FileInFile.read`（while→if + 链式比较坍塌，多机制叠加）、`TarFile.next`（动异常表）、`main`（with 块蒸发）；`TarFile.add` 为已登记 NOP 测量差 | 抽不出最小复现；`main` 需语句归属重构（与 Task 107.5 同源） |
| subprocess 3 | `__init__`（5 个独立差异点）、`_internal_poll`（异常表 0→7）、`_wait`（已 BLOCKED） | 高 |
| 基础设施 | **Task 107.5 语句发射台账**（记录语句归属序列与缩进层级；链后语句由父序列追加） | 一次投入可同时解锁 `_wait` 与 `main`；但属生成器重构，回归面广 |
| G1 | 376 real-package 排除需范围/证据决策 | **非工程可解** |
| G3 / G4 | 变异补齐、witness 生成（open 342） | 开放量，工作量大 |
| G6 | 独立 custody | 外部条件 |
| Task 8 终态 | 双读数写 `rules.md`/`wiki/`、`rounds/round11/` 归档、终态报告 | 文档类，可在语料收敛后执行 |
