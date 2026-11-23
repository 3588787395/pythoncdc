# 语义差分行（REACHABILITY 第 2 行）读数 — round13

阈值（`REACHABILITY.md` L29）：`unresolved = 0`；C1–C5 齐全；R1–R7 无未裁决失败。
本行未达成；以下是全量 1556 J 的四次完整读数、人口学与根因。

## 全量读数（`tools/completeness/semantic_runner.py`，1556 条跑满，stopped=case_limit）

| 读数 | t=5 全量 | t=30 分块 | t=31 分块（布线＋vendor） | t=32 分块（新 judge r203 镜像 v1） |
|---|---|---|---|---|
| EQUAL | 1083 | 1084 | 1096 | **1096** |
| DIFFERENT | 30 | 30 | 30 | **30** |
| ERROR | 264 | 422 | 412 | **48** |
| MIRRORED_EXCEPTION | — | — | — | **364** |
| INCONCLUSIVE | 18 | 18 | 18 | **18** |
| NO_C4（反编译失败/超时） | 161 | 2 | 0 | **0** |
| module_only | 718 | 719 | 731 | **731** |
| covered_5tuple | 395 | 395 | 395 | **395** |

产物：`semantic_j_full.json`（t5）、`semantic_j_full_t30_a.json`、`semantic_j_full_t30_b.json`
（t30，两块并行执行、共享默认产物目录；产物按条目 ID 命名互不覆盖，判定迁移交叉表
证实无相互干扰）、`semantic_j_full_t31_a.json`、`semantic_j_full_t31_b.json`
（t31，两块**串行**执行——前次并行尝试因子代理失活后台作业被杀，复盘后改串行＋
跑批全程保持活跃；块 a 40 分 12 秒、块 b 45 分 38 秒，exit 3＝有 ERROR 判定预期非崩溃）、
`semantic_j_full_t32_a.json`、`semantic_j_full_t32_b.json`（t32，两块串行；块 a 56 分
13 秒、块 b 44 分 56 秒，均 exit 3＝有 ERROR 判定预期非崩溃；总 101 分 8.5 秒）。
**t32 联合读数为当前权威**（r203 新代判定器：semantic_diff v1.1.0＋semantic_runner
v1.2.0＋coverage_checker v2.1.0，`MIRRORED_EXCEPTION` 镜像裁决 v1 落地；judge
sha=8b6e6a61…b83004a 逐记录失配 0；t31→t32 隔离 judge 变量，core 零变化，两轮都出
c3/c1/c2 的 1556 条 bitwise 零漂移）。

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

## 判定迁移交叉表（t31 → t32，逐条核对无缺失，1556 aligned，新 judge 首个全量行使）

- 迁移通道恰 5 条、零意外零翻转：`ERROR→MIRRORED_EXCEPTION` **364**（site-packages
  墙类全量翻镜像，**镜像率＝site-pkg ERROR 的 100%**，364/364 两侧同
  `No module named 'IQCommon.data.TickDataCache'`，第一层消息 0——谓词零漏捕零
  误捕）；`ERROR→ERROR` 48（4 探针族×12：TypeError/NameError 非 ImportError 族，
  v1 谓词按裁决不覆盖）；`EQUAL→EQUAL` 1096；`DIFFERENT→DIFFERENT` 30；
  `INCONCLUSIVE→INCONCLUSIVE` 18。
- 按桶：.trae 123 全 EQUAL；site-packages 376＝EQUAL 12＋MIRRORED 364；test_repros
  1057＝EQUAL 961＋DIFFERENT 30＋ERROR 48＋INCONCLUSIVE 18。kept 人口学 449 逐类
  恒同；covered_5tuple 395 恒同（**全量零膨胀断言过**：coverage_checker v2.1.0 对
  t31/t32 证据实跑输出逐位恒同——covered_5tuple 365＋r7_only_different 30＝395，
  MIRRORED 364 全部 excluded 入口、入分子 0；c4_mirrored_exception 分支为 kept 镜像
  纵深防御，本空间无 kept 镜像故未触发）。
- 形式不变式兑现：新代码路径仅原始侧失败分支可达 ⇒ 旧判 EQUAL/DIFFERENT/
  INCONCLUSIVE 1544 条逐字节同判（仅 c5 代际域漂移：judge_sha256/runner_version）。
- G6 镜像块完整性：364 条逐项零违规（两侧 exception_info canonical 相等、
  family=ImportError、phase=load、boundary=module_load、exit_code=4、errors=[]、
  status=unexecuted、reason=mirror_exception、package_root=site-packages 364/364）。
- 残余 ERROR 48 分解复核：全部 test_repros（c01_class_assign→JS-ANNASSIGN 12、
  c05_class_with→JS-WITH 12、m04_module_try→JS-TRY 12、c4_15_star_import→
  JS-IMPORT 12）；site-pkg 残余 0、.trae 0。

## 人口学（t32 权威，1556 = 449 kept+calls 探针 + 1107 excluded+无calls）

| 判定 | 人口 | t30 n | t31 n | t32 n |
|---|---|---|---|---|
| EQUAL | excluded 探针（module_only） | 719 | 731 | **731** |
| EQUAL | kept 探针（有 calls） | 365 | 365 | **365** |
| DIFFERENT | kept 探针 | 30 | 30 | **30** |
| ERROR | site-packages 真实包模块 | 374 | 364 | **0** |
| MIRRORED_EXCEPTION | site-packages 真实包模块（全部 excluded 无 calls） | — | — | **364** |
| ERROR | kept 探针 | 36 | 36 | **36** |
| ERROR | excluded 探针 | 12 | 12 | **12** |
| INCONCLUSIVE | kept 探针 | 18 | 18 | **18** |
| NO_C4 | site-packages 模块 | 2 | 0 | **0** |

kept 449 逐类三轮完全一致；covered_5tuple 395 三轮恒同；MIRRORED 364 的 pyc 分布
与 t31 site-pkg ERROR 逐位相同（trade_info_utils 203 / trade_live_broker 42 /
scheduler 39 / quote_handler 28 / function 27 / live 25），签名单一
（364×builtins.ModuleNotFoundError，两侧同 TickDataCache 消息）。

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

- `unresolved=0`：**未达成**。t32 权威双口径：
  - **严格口径**（MIRRORED 不离开未解决集）：未解决＝ERROR 48＋INCONCLUSIVE 18＋
    NO_C4 0＋MIRRORED 364＝**430**（镜像已裁决但未测面显式声明，不写「已裁决无失败」）。
  - **镜像裁决口径**（MIRRORED＝已测面等价证据、测量面截断已裁决）：未解决＝
    ERROR 48＋INCONCLUSIVE 18＝**66**（48 探针源码自身崩溃＋18 超时）。
  - 两口径均 ≠ 0 ⇒ 行 2 未达成；收敛路线见下一步。
  - **v2 落地后读数（122.19 r205，2026-11-24）**：镜像裁决口径未解决＝18
    （48 条探针源码崩溃经 v2 谓词翻 MIRRORED 已 48/48 定向验证：零真分歧、
    对照组零漂移、新 judge `2110b736…b9fdb`）。本读数以 61 条定向验证为据，
    权威仍为 t32（v1 judge）；t33（v2 judge）全量后转权威。
- C1–C5 齐全：`covered_5tuple=395/1556`；module_only 731 条按定义不计覆盖；
  MIRRORED 364 全部 excluded 无 calls、不进覆盖分子（全量零膨胀断言过）。
- R1–R7 无未裁决失败：30 条已裁决 DIFFERENT（已决失败，如实保留，不混入未裁决）；
  镜像 364 的 R1–R7 墙后未测面已显式声明（other_observables=untested）；
  未裁决＝严格口径 430 / 镜像口径 66。

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
4. ~~镜像异常等价裁决实施（122.14/122.17）~~ **已完成**（r203：MIRRORED_EXCEPTION
   落地＋37 样本验证 a–g 全过＋t32 全量行使——364/364 镜像率 100%、零意外通道、
   零膨胀，见 t31→t32 交叉表节）。
5. ~~镜像 v2 族扩展裁决（122.19）~~ **已裁决并落地**（2026-11-24 裁决→r205
   实施）：族白名单扩至 {ImportError, ModuleNotFoundError, ZipImportError,
   NameError, TypeError}（48 条残余 ERROR 的全部实测族，TypeError×1＋
   NameError×3）；进程控制类经 harness 白名单结构性排除；exception_info 无
   位置敏感字段（canonical 等价可判）。semantic_diff v1.2.0（新 judge
   `2110b736…b9fdb`）＋61 条定向验证：**48/48 翻 MIRRORED、零真分歧**（逐族
   12/12），3 site-pkg 镜像控制保持（exception_family 实测化
   ModuleNotFoundError），5 守卫探针＋5 EQUAL kept 零行为变化，镜像块完整性
   G6 式零违规，c1/c2/c3 零漂移，selftest 26/26×2。镜像裁决口径 66→**18**。
6. ~~18 条 INCONCLUSIVE 探针终止性修复（122.20）~~ **已完成**（r206，2026-11-24）：
   两探针源各恰 ＋1 行可达 break（x01 L17/x04 L36，保 label/d3plus/AST 剥离
   Break 后逐字节同）、pyc 同版重建（x01→d574158f…、x04→418449ac…，gitignore
   惯例不入库）、空间恰 18 条 × 4 字段（其余 1538 条逐字节不变）、登记矩阵
   `round13/rec1_probe_repair_12220.json`、18 产品再生成。定向复测（v2 judge）
   **18/18 可判定、零 INCONCLUSIVE：EQUAL 7（x01 全部）＋DIFFERENT 11（x04
   全部）**。11 条 DIFFERENT＝单函数单根因（try_in_while 异常表保护域边界
   2 code unit：try 体内尾随 break 被重定位到不受保护的 else 子句），co_code/
   行为两侧全等——**承接立案 122.21 修复**（与 30 条原族零重叠，DIFFERENT
   总量 30→41）。镜像裁决口径 INCONCLUSIVE 18→0（pending t33 权威）。
7. 30 DIFFERENT 逐族修复（反编译器本体工作；Task 123/124 及 Starred 12 →
   With 9 → Break 5 → 4 单例路线），修复轮次与 122.20 依次推进
   （core 冻结期间不动本体），终局以全量 t33 收读数。
8. 全量读数更新本文件与 checklist 对齐表；产品目录刷新后与 `semantic_products/`
   一并入库（t32 后零漂移；时序翻转集占位债已收编真实产物 r204）。

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
| **x04 try_in_while 重建边界（122.20 复测新增，根因单函数）** | **11** | JS-TRY-008/025/050/062/078/086/087/095/096、JS-WHILE-007、JS-WITH-065 |

修复路线（按族聚合收益排序）：**Starred 12 → With 9 → Break 5 → 4 个单例**
（continue-in-match-case / if-in-match-case / try-nested-in-try / while-with-break）
＋**122.21（x04 重建边界 11，单根因单修复）**；总量 41（30 原族＋11 新，零重叠）。
注意 B142 既有缺口（`g2_brk`、`g3_three_fin`）与 Break 族可能共享 finally/环谱系判据。

## 状态

**未达成**（t32 权威，2026-11-24）：严格口径 unresolved=430 ≠ 0；镜像裁决口径
unresolved=66 ≠ 0（48 探针源码自身崩溃＋18 超时）。**镜像裁决 v1 已完整落地并全量
行使**（122.14 裁决→122.17 实施 r203→t32 全量）：`MIRRORED_EXCEPTION` 新 verdict
（v1 限 ImportError 族）、364/364 site-pkg 墙类全量翻镜像（**镜像率 100%**、单一
签名 TickDataCache、两侧 canonical exception_info 全等逐条落盘）、迁移通道恰 5 条
零意外、coverage 零膨胀（t31/t32 checker 输出逐位恒同）、G0–G8 全过。镜像边界声明
（已测面＝装载结果＋R6 模块级异常＋装载期 R2/R3/R4 等价；未测面＝R1/R5/R7 墙后，
`other_observables=untested` 如实记录；不写「已裁决无失败」）随 t32 落库成立。
依赖链四层全部落定（布线 r195 → logbook/tornado r197 → pyzmq/typing_extensions
r198 → 第四层墙 TickDataCache，vendor 路线收口）。**镜像裁决 v2 已裁决并落地**
（122.19，2026-11-24，r205：族白名单＋NameError/TypeError、48/48 定向翻镜像零真
分歧、镜像裁决口径 66→18；权威仍 t32，t33 转权威）。剩余收敛路线＝**18 条
INCONCLUSIVE 探针终止性修复（122.20 已完成 r206：18/18 可判定，EQUAL 7＋
DIFFERENT 11；INCONCLUSIVE 18→0 pending t33；11 条承接 122.21 单根因修复）**
＋ 30 真差异逐族修复（Starred 12 → With 9 → Break 5 → 4 单例；Task 123/124
并行线）→ 终局 t33 全量收权威读数。
