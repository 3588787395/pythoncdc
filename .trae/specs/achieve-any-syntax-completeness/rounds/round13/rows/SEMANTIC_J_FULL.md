# 语义差分行（REACHABILITY 第 2 行）读数 — round13

阈值（`REACHABILITY.md` L29）：`unresolved = 0`；C1–C5 齐全；R1–R7 无未裁决失败。
本行未达成；以下是全量 1556 J 的三次完整读数、人口学与根因。

## 全量读数（`tools/completeness/semantic_runner.py`，1556 条跑满，stopped=case_limit）

| 读数 | t=5 全量 | t=30 A+B 分块（offset 0/778） | t=31 A+B 分块（同构复刻＋布线＋vendor） |
|---|---|---|---|
| EQUAL | 1083 | 1084 | **1096** |
| DIFFERENT | 30 | 30 | **30** |
| ERROR | 264 | 422 | **412** |
| INCONCLUSIVE | 18 | 18 | **18** |
| NO_C4（反编译失败/超时） | 161 | 2 | **0** |
| module_only | 718 | 719 | **731** |
| covered_5tuple | 395 | 395 | **395** |

产物：`semantic_j_full.json`（t5）、`semantic_j_full_t30_a.json`、`semantic_j_full_t30_b.json`
（t30，两块并行执行、共享默认产物目录；产物按条目 ID 命名互不覆盖，判定迁移交叉表
证实无相互干扰）、`semantic_j_full_t31_a.json`、`semantic_j_full_t31_b.json`
（t31，两块**串行**执行——前次并行尝试因子代理失活后台作业被杀，复盘后改串行＋
跑批全程保持活跃；块 a 40 分 12 秒、块 b 45 分 38 秒，exit 3＝有 ERROR 判定预期非崩溃）。
**t31 联合读数为当前权威**（runner v1.1.0 布线 auto＋r197/r198 vendor 后；
judge 冻结 sha=d31948b3… 两轮一致；per-record c5 judge sha 失配 0）。

## 判定迁移交叉表（t5 → t30，逐条核对无缺失）

- `EQUAL→EQUAL` 1083、`DIFFERENT→DIFFERENT` 30、`ERROR→ERROR` 263、`INCONCLUSIVE→INCONCLUSIVE` 18：
  **完全稳定**。
- `NO_C4→ERROR` 159、`NO_C4→EQUAL` 1、`NO_C4→NO_C4` 1、`ERROR→NO_C4` 1。
- 结论：ERROR 264→422 的膨胀**不是并发干扰或产品漂移**，而是 t5 的 161 条反编译超时
  在 t30 下解开（161→2）后，暴露出同一批条目在裁决阶段的原始工件执行失败。

## 判定迁移交叉表（t30 → t31，逐条核对无缺失，1556 aligned）

- `EQUAL→EQUAL` 1084、`DIFFERENT→DIFFERENT` 30、`INCONCLUSIVE→INCONCLUSIVE` 18、
  `ERROR→ERROR` 410：稳定。
- `ERROR→EQUAL` **12**：全部＝site-packages/fly/common/aes_encrypt.pyc
  （JS-DECORATOR-001/002/005/006/007/008/009/010/011/012/015/016）——该 pyc 不依赖
  TickDataCache，布线＋vendor 后全程执行成功。
- `NO_C4→ERROR` 2（JS-IMPORT-015、JS-WHILE-037，trade_live_broker 时序翻转：
  本轮 42 条全部反编译成功，无 NO_C4）。
- 分桶：.trae 123 全 EQUAL→EQUAL；site-packages 376＝12 ERROR→EQUAL＋362 ERROR
  ＋2 NO_C4→ERROR；test_repros 1057 恒同（EQUAL 961＋DIFFERENT 30＋ERROR 48＋
  INCONCLUSIVE 18）。kept 人口学 449 逐类恒同（EQUAL 365＋DIFFERENT 30＋
  ERROR 36＋INCONCLUSIVE 18）。
- 零漂移主判据：两轮都出 c3/c1/c2 的记录 SHA 逐位一致（c3 失配 0、c1/c2 失配 0）；
  git 层面漂移恰 2 文件（时序翻转集，见根因节），非 core 变化。

## 人口学（t31 权威，1556 = 449 kept+calls 探针 + 1107 excluded+无calls）

| 判定 | 人口 | t30 n | t31 n |
|---|---|---|---|
| EQUAL | excluded 探针（module_only） | 719 | **731** |
| EQUAL | kept 探针（有 calls） | 365 | **365** |
| DIFFERENT | kept 探针 | 30 | **30** |
| ERROR | site-packages 真实包模块 | 374 | **364** |
| ERROR | kept 探针 | 36 | **36** |
| ERROR | excluded 探针 | 12 | **12** |
| INCONCLUSIVE | kept 探针 | 18 | **18** |
| NO_C4 | site-packages 模块 | 2 | **0** |

kept 449 逐类两轮完全一致；module_only 719→731＝12 条 aes_encrypt 迁移条目；
covered_5tuple 395 两轮恒同。

## 根因（已单案复现取证）

- **374/422 ERROR 是测量环境边界，不是反编译缺陷**：site-packages 真实包模块
  （IQEngine/IQCommon/fly 等）以独立 worker 子进程执行，`cwd=沙箱`，仓库的
  `site-packages/` 根不在 `sys.path` 上，原始 pyc 在模块级 `import IQEngine` 即
  `ModuleNotFoundError`（复现样本 `JS-IF-003`：original 侧
  `{"type":"builtins.ModuleNotFoundError","message":"No module named 'IQEngine'"}`）。
  仓库**确实带有** `site-packages/IQEngine|IQCommon|IQData|fly`，判定器
  `semantic_diff._load_target` 也**已支持** `target["package_root"]`（插入 sys.path），
  只是 `semantic_runner.py` 组装 case 时从未传过。
- **根因第二层（2026-11-22 夜样本实测，37 条）**：布线入库
  （`semantic_runner` v1.1.0 `--package-root auto|off|<path>`，默认 auto）后，
  仓库包 import 链推进（`No module named 'IQEngine'` → `No module named 'logbook'`，
  live.pyc L10→L11 直接证据），但真实包自身 import 第三方依赖 **logbook**（20 条：
  IQEngine 10 + fly 10，经 IQEngine/utils→IQCommon/logger 链）与 **tornado**
  （10 条：IQCommon/trade_info_utils L48 直 import）——仓库与本机均无 ⇒
  原始侧仍 load 失败 ⇒ **30 条 ERROR 样本 0 翻转**（5 守卫探针全 EQUAL 且无
  package_root 字段；`--package-root off` 复现旧 ERROR；c3 产物 sha 37 条全与
  t30 一致；四项守卫断言全 PASS）。样本覆盖 374 条涉及的全部 7 个 pyc。
- **修正后的结论**：package_root 布线是必要非充分；374 条的可执行性还差
  `logbook`/`tornado` 两个第三方依赖（IQData 在 J 中实际为 0 条，此前推断有误）。
- **t31 终局根因（2026-11-23 全量＋双侧探针实测，布线态）**：残余 364 条
  site-packages ERROR 的 6 个 distinct pyc（trade_info_utils 203 / trade_live_broker
  42 / scheduler 39 / quote_handler 28 / function 27 / live 25）代表探针 6/6
  统一死于 `No module named 'IQCommon.data.TickDataCache'`——IQEngine/IQCommon/
  fly/tornado/zmq/logbook 导入链全部解析，第四层墙为唯一残余根因。未布线态
  对照（复现 t30 v1.0.0 环境）逐 pyc 死于首导入层（tornado/IQCommon/fly/
  IQEngine）——死亡层前进链条闭合，判决计数变化仅在 aes_encrypt 12 条
  （不依赖 TickDataCache）与时序翻转 2 条，kept 人口学零变化。
- **48 条探针 ERROR 根因（t31 实测复核，4 族 48/48 根因逐字不变）**：
  m04_module_try（TypeError：`with (CFG if 0 else json) as j`，json 非 context
  manager，外层 try 只捕 NameError）、c4_15_star_import（NameError：`path` 未
  定义，两处 star import 均不导出）、c05_class_with（NameError：class 体内
  `_CM` 未定义）、c01_class_assign（NameError：class 体内 lambda 不捕获类作用域
  `B`）——全部为**探针源码自身确定性模块级崩溃**，与 vendor/布线无关，
  非 ImportError 族（镜像裁决 v1 不覆盖，维持 ERROR 属实）。
- t5 的 161 NO_C4 是 `--timeout 5` 对大体量真实模块反编译太紧
  （如 `IQCommon/util/trade_info_utils.pyc`），t30 解决 159 条。
  trade_live_broker.pyc 在 30 s 边缘（NO_C4↔ERROR 随负载漂移，两轮实测不同）。
  **t31 时序方差集＝{JS-IMPORT-015, JS-WHILE-037}**（方向 NO_C4→ERROR；本轮
  42 条全部反编译成功）。该集合为逐次运行随机落点，读数差异计入方差注释而非
  判定变化。
- **30 DIFFERENT 三次读数完全稳定**（kept 探针，有 calls）：真实语义差异，需逐族修复。
- 18 INCONCLUSIVE：任一侧执行超时（Task 1.3 口径，不计 EQUAL/DIFFERENT）；
  t31 逐条复现同超时（JS-IF-076/114、JS-MATCHSTMT-002、JS-TRY-008/009/025/
  050/062/078/086/087/095/096/097、JS-WHILE-007/032/038、JS-WITH-065），零新增。

## 行阈值对照

- `unresolved=0`：**未达成**。未解决（ERROR+INCONCLUSIVE+NO_C4）= **430**（t31
  权威：364 TickDataCache 墙 + 48 探针源码自身崩溃 + 18 超时 + 0 反编译失败）。
- C1–C5 齐全：`covered_5tuple=395/1556`；module_only 731 条按定义不计覆盖。
- R1–R7 无未裁决失败：30 条已裁决 DIFFERENT（已决失败，如实保留，不混入未裁决）；
  未裁决 430 条。

## 下一步（按收益排序，2026-11-23 t31 落地后修订）

1. ~~`semantic_runner.py` 包根布线~~ **已入库**（v1.1.0 `--package-root auto|off|<path>`，
   默认 auto；37 条样本四项守卫断言全 PASS，c3 产物 37 条 sha 与 t30 全一致；
   `--package-root off` 复现旧 ERROR）。布线后样本 **0 翻转**——根因第二层
   （logbook/tornado 第三方依赖缺失）浮出，见上节。
2. ~~补齐第三方依赖＋t31 全量重测~~ **已完成**（r197 logbook/tornado → r198
   pyzmq/typing_extensions → vendor 路线收口于第四层 TickDataCache 墙，
   `rows/VENDOR_DEPS.md`；t31 全量重测 2026-11-23 完成，本文件读数即 t31 权威）。
3. ~~36+12 探针 ERROR 逐条诊断~~ **已定性**（t31：48/48＝4 族探针源码自身
   确定性模块级崩溃，与布线/vendor 无关；v1 镜像裁决不覆盖，如实保持 ERROR；
   后续若收敛需探针源修正或镜像裁决 v2 族扩展裁决，未排期）。
4. **镜像异常等价裁决实施（122.14，方案 D 已裁决）**：`MIRRORED_EXCEPTION`
   verdict＋runner 词表/exit 4＋守卫重规约 → 37 样本验证（唯一允许翻转
   27 ERROR→MIRRORED）→ 全量 t32（t31→t32 隔离 judge 变量，core 不变）。
   严格口径下 MIRRORED 不离开未解决集；边界口径另行裁决。
5. 30 DIFFERENT 逐族修复（反编译器本体工作；Task 123/124 及 Starred 12 →
   With 9 → Break 5 → 4 单例路线），18 INCONCLUSIVE 加时/优化后复测；
   修复轮次在 t32 落地后启动（core 冻结期间不动本体），终局以全量 t33 收读数。
6. 全量读数更新本文件与 checklist 对齐表；产品目录刷新后与 `semantic_products/`
   一并入库（t31 后零漂移，已复原 tracked 态，无需入库新产物）。

## 30 条 DIFFERENT 逐族拆解（t30 记录逐条核对）

**全部 30 条的 diff 维度只有 R7**（code object 级：co_code/co_consts/异常表等按
TOLERANCE_REGISTRY 保护口径），声明 calls 上的行为维度 R1–R6 全部干净。按
`expected_label.form/variant` 分族：

| 族 | 条数 | entry ids |
|---|---|---|
| Starred（starred-in-call 9 / starred-at-head 3） | **12** | JS-STARRED-001/002/005..011（in-call）、012/013/014（at-head） |
| With（multi-item 2 / as-target 2 / item-call 2 / in-loop 1 / in-func 1 / body-nested 1） | **9** | JS-WITH-017/020/033/034/047/054/064/075/076 |
| Break（in-for / in-while / in-if-arm / target-outer / in-nested-loop） | **5** | JS-BREAK-001/011/023/027/030 |
| Continue（in-match-case） | 1 | JS-CONTINUE-025 |
| If（in-match-case） | 1 | JS-IF-115 |
| Try（nested-in-try） | 1 | JS-TRY-077 |
| While（with-break） | 1 | JS-WHILE-040 |

修复路线（按族聚合收益排序）：**Starred 12 → With 9 → Break 5 → 4 个单例**
（continue-in-match-case / if-in-match-case / try-nested-in-try / while-with-break）。
注意 B142 既有缺口（`g2_brk`、`g3_three_fin`）与 Break 族可能共享 finally/环谱系判据。

## 状态

**未达成**：unresolved=430 ≠ 0（t31 权威，2026-11-23）。依赖链四层全部落定：
布线 r195 → logbook/tornado r197 → pyzmq/typing_extensions r198 → 第四层墙＝
内部 Linux-only 扩展 TickDataCache（364 条残余 ERROR 的 6 distinct pyc 布线态
6/6 同根因，`rows/VENDOR_DEPS.md`），vendor 路线已收口；t31 全量重测完成，
未解决 442→430（12 条 aes_encrypt 翻转 EQUAL＋2 条时序翻转）。剩余收敛路线＝
**镜像异常等价裁决实施（122.14 已裁决方案 D：`MIRRORED_EXCEPTION` 新 verdict＋
边界声明＋严格/边界双口径，v1 限 ImportError 族，实施门＝37 样本验证＋全量
t32，详见 `rows/ROUTE2_MIRROR_DESIGN.md` 与 tasks.md 122.14）**＋ 48 探针
源码自身崩溃（v1 镜像不覆盖，未排期）＋ 30 真差异逐族修复＋ 18 超时收敛。
TickDataCache 墙 364 条的处置＝镜像裁决 v1 的目标人群（两侧同
`No module named 'IQCommon.data.TickDataCache'` ⇒ 模块边界内等价证据）；
双侧镜像率待 t32 实测（t31 记录不含产物侧异常，旧记录不可离线改判）。
