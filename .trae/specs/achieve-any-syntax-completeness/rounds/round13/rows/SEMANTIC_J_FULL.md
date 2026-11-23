# 语义差分行（REACHABILITY 第 2 行）读数 — round13

阈值（`REACHABILITY.md` L29）：`unresolved = 0`；C1–C5 齐全；R1–R7 无未裁决失败。
本行未达成；以下是全量 1556 J 的两次完整读数、人口学与根因。

## 全量读数（`tools/completeness/semantic_runner.py`，1556 条跑满，stopped=case_limit）

| 读数 | t=5 全量 | t=30 A+B 分块（offset 0/778） |
|---|---|---|
| EQUAL | 1083 | 1084 |
| DIFFERENT | 30 | 30 |
| ERROR | 264 | 422 |
| INCONCLUSIVE | 18 | 18 |
| NO_C4（反编译失败/超时） | 161 | 2 |
| module_only | 718 | 719 |
| covered_5tuple | 395 | 395 |

产物：`semantic_j_full.json`（t5）、`semantic_j_full_t30_a.json`、`semantic_j_full_t30_b.json`
（t30，两块并行执行、共享默认产物目录；产物按条目 ID 命名互不覆盖，判定迁移交叉表
证实无相互干扰）。**t30 联合读数为当前权威**。

## 判定迁移交叉表（t5 → t30，逐条核对无缺失）

- `EQUAL→EQUAL` 1083、`DIFFERENT→DIFFERENT` 30、`ERROR→ERROR` 263、`INCONCLUSIVE→INCONCLUSIVE` 18：
  **完全稳定**。
- `NO_C4→ERROR` 159、`NO_C4→EQUAL` 1、`NO_C4→NO_C4` 1、`ERROR→NO_C4` 1。
- 结论：ERROR 264→422 的膨胀**不是并发干扰或产品漂移**，而是 t5 的 161 条反编译超时
  在 t30 下解开（161→2）后，暴露出同一批条目在裁决阶段的原始工件执行失败。

## 人口学（t30，1556 = 449 kept+calls 探针 + 1107 excluded+无calls）

| 判定 | 人口 | n |
|---|---|---|
| EQUAL | excluded 探针（module_only） | 719 |
| EQUAL | kept 探针（有 calls） | 365 |
| DIFFERENT | kept 探针 | 30 |
| ERROR | **site-packages 真实包模块** | **374** |
| ERROR | kept 探针 | 36 |
| ERROR | excluded 探针 | 12 |
| INCONCLUSIVE | kept 探针 | 18 |
| NO_C4 | site-packages 模块 | 2 |

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
- t5 的 161 NO_C4 是 `--timeout 5` 对大体量真实模块反编译太紧
  （如 `IQCommon/util/trade_info_utils.pyc`），t30 解决 159 条。
  trade_live_broker.pyc 在 30 s 边缘（NO_C4↔ERROR 随负载漂移，两轮实测不同）。
- **30 DIFFERENT 两次读数完全稳定**（kept 探针，有 calls）：真实语义差异，需逐族修复。
- 18 INCONCLUSIVE：任一侧执行超时（Task 1.3 口径，不计 EQUAL/DIFFERENT）。

## 行阈值对照

- `unresolved=0`：**未达成**。未解决（ERROR+INCONCLUSIVE+NO_C4）= **442**（374 包根缺失
  + 48 探针 ERROR + 18 超时 + 2 反编译失败）。
- C1–C5 齐全：`covered_5tuple=395/1556`；module_only 719 条按定义不计覆盖。
- R1–R7 无未裁决失败：30 条已裁决 DIFFERENT（已决失败，如实保留，不混入未裁决）；
  未裁决 442 条。

## 下一步（按收益排序，2026-11-22 夜修订）

1. ~~`semantic_runner.py` 包根布线~~ **已入库**（v1.1.0 `--package-root auto|off|<path>`，
   默认 auto；37 条样本四项守卫断言全 PASS，c3 产物 37 条 sha 与 t30 全一致；
   `--package-root off` 复现旧 ERROR）。布线后样本 **0 翻转**——根因第二层
   （logbook/tornado 第三方依赖缺失）浮出，见上节。
2. **给仓库 `site-packages/` 补齐缺失第三方依赖**（374 条原始 pyc 的模块级硬依赖；
   IQData 在 J 中实际 0 条）。**进度（r197）**：logbook 1.10.1＋tornado 6.6.1 已
   vendor（溯源 `rows/VENDOR_DEPS.md`），37 样本复测 **5 条翻转 EQUAL**
   （JS-DECORATOR-001/002/005/006/007，fly/aes_encrypt 家族，链止于 logbook）；
   25 条残留 ERROR **全部卡第三层 `import zmq`**（27/27 布线 probe 同一异常，
   汇聚 IQCommon/common/main.pyc L57；宿主亦无）→ 122.13 续 vendor pyzmq＋
   typing_extensions 并逐层收口。**进度（r198，122.13 完成）**：pyzmq 27.3.0＋
   typing_extensions 4.16.0 已 vendor（`_zmq.pyd` add -f 入库）；布线 probe
   27/27 越过 zmq 层后统一死于**第四层** `No module named
   'IQCommon.data.TickDataCache'`——公司内部 Cython 扩展，语料唯一制品为
   Linux x86_64 ELF `.so`（Windows EXTENSION_SUFFIXES 不含 `.so`，不可装载，
   非 PyPI 可 vendor；语料内同类 Linux `.so` 共 9 个）。**vendor 路线到此收口**，
   37 样本 v3 复测 EQUAL 10/ERROR 27、零翻转零回退零 DIFFERENT、守卫四断言全
   PASS（sample_out_v3.json；root cause 27/27 统一 TickDataCache）。25 条残留的
   处置改走「镜像异常等价」裁决路线（原始与产物两侧同异常 ⇒ 模块边界内等价
   证据；语义行新裁决项，见 tasks.md），另需 t31 全量重测拿 vendor 后权威读数。
3. 36+12 探针 ERROR 逐条诊断（区分：探针自身模块级异常 vs 工件装载路径）。
4. 30 DIFFERENT 逐族修复（反编译器本体工作），18 INCONCLUSIVE 加时/优化后复测。
5. 全量读数更新本文件与 checklist 对齐表；产品目录刷新后与 `semantic_products/`
   一并入库。

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

**未达成**：unresolved=442 ≠ 0（t30 读数，vendor 前）。依赖链已四层收口（布线
r195 → logbook/tornado r197 → pyzmq/typing_extensions r198 → 第四层墙＝内部
Linux-only 扩展 TickDataCache，非 PyPI 可操作，`rows/VENDOR_DEPS.md`）；t31
全量重测待跑（vendor 后权威读数，预期 ERROR 显著下降、DIFFERENT/INCONCLUSIVE/
NO_C4 复测）。剩余收敛路线＝镜像异常等价裁决（平台缺口类）＋ 30 真差异逐族修复
＋ 探针诊断 ＋ 超时收敛。
