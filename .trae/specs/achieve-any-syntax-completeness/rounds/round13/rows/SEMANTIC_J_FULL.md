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
  （IQEngine/IQCommon/IQData 等）以独立 worker 子进程执行，`cwd=沙箱`，仓库的
  `site-packages/` 根不在 `sys.path` 上，原始 pyc 在模块级 `import IQEngine` 即
  `ModuleNotFoundError`（复现样本 `JS-IF-003`：original 侧
  `{"type":"builtins.ModuleNotFoundError","message":"No module named 'IQEngine'"}`）。
  仓库**确实带有** `site-packages/IQEngine|IQCommon|IQData`，判定器
  `semantic_diff._load_target` 也**已支持** `target["package_root"]`（插入 sys.path），
  只是 `semantic_runner.py` 组装 case 时从未传过。
- t5 的 161 NO_C4 是 `--timeout 5` 对大体量真实模块反编译太紧
  （如 `IQCommon/util/trade_info_utils.pyc`），t30 解决 159 条。
- **30 DIFFERENT 两次读数完全稳定**（kept 探针，有 calls）：真实语义差异，需逐族修复。
- 18 INCONCLUSIVE：任一侧执行超时（Task 1.3 口径，不计 EQUAL/DIFFERENT）。

## 行阈值对照

- `unresolved=0`：**未达成**。未解决（ERROR+INCONCLUSIVE+NO_C4）= **442**（374 包根缺失
  + 48 探针 ERROR + 18 超时 + 2 反编译失败）。
- C1–C5 齐全：`covered_5tuple=395/1556`；module_only 719 条按定义不计覆盖。
- R1–R7 无未裁决失败：30 条已裁决 DIFFERENT（已决失败，如实保留，不混入未裁决）；
  未裁决 442 条。

## 下一步（按收益排序）

1. `semantic_runner.py` 为 site-packages 条目向 original/product 两侧传
   `package_root`（判定器已支持，属测量布线，不触碰 R1–R7 判定语义），
   先抽样 ~30 条验证再全量重跑：预期 374 ERROR 大部分转为可裁决。
2. 36+12 探针 ERROR 逐条诊断（区分：探针自身模块级异常 vs 工件装载路径）。
3. 30 DIFFERENT 逐族修复（反编译器本体工作），18 INCONCLUSIVE 加时/优化后复测。
4. 全量读数更新本文件与 checklist 对齐表；产品目录刷新后与 `semantic_products/`
   一并入库。

## 状态

**未达成**：unresolved=442 ≠ 0。包根布线是第一刀，预期可把未解决降到 ~70 量级，
剩余为 30 真差异 + 探针诊断 + 超时收敛。
