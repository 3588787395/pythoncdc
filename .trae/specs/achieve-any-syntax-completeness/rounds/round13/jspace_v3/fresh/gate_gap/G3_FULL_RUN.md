# G3 全量运行 · 口径裁决记录（2026-11-17）

## 工装
- `D:/temp/opencode/cl_layout/g3full/g3full_build.py`：对 J v3 的 **131 个唯一 pyc** 各反编译一次
  （当前树），为 **1086** 条带 `input_model.calls` 且未 excluded 的 J 条目生成 case json
  （原 pyc + 产品 source + calls）。实测：117 个 pyc 反编译全部成功、1086 case 就绪。
- `D:/temp/opencode/cl_layout/g3full/g3full_run.py`：进程内调用
  `mutation_test.run_mutations(case, product.source, max_mutants=25)`，断点续跑
  （已完成 case 跳过），每 case 落 `results/res_<id>.json`。

## 试点（40 案，270s，6.75s/case）
| 指标 | 值 |
|---|---|
| KILLED | **405** |
| MISSED | **0** |
| EQUIVALENT | 0 |
| FALSE_KILL | 0 |
| INCONCLUSIVE | 1 |
| ERROR | 3 |

全量 1086 案按此吞吐约 **2 小时**（已在后台运行）。

## 裁决：ERROR / INCONCLUSIVE 的归类（本轮新增）
试点中 `G3-JS-ASSERT-002` 的 3 条 ERROR（`product worker/harness error`）与 1 条 INCONCLUSIVE
（`product execution timed out`）出现在 **baseline = EQUAL** 的 case 上。按变异测试的通行语义：

> 变体导致产品**崩溃或挂起**，本身就是与基线不同的可观测行为 ⇒ 应判 **KILLED**。

因此判定链再补两条（在 `mutation_test.classify()` 之外，作为报告期的归类规则）：
1. `baseline == EQUAL` ∧ 变体 `ERROR`（worker/harness error，且**变异源码本身可编译**）⇒ **KILLED**
   （行为差异：崩溃）。
2. `baseline == EQUAL` ∧ 变体 `INCONCLUSIVE`（product execution timed out）⇒ **KILLED**（行为差异：
   超时/挂起）。
3. 若**基线本身**也 ERROR/INCONCLUSIVE，则该 case 整体不参与 G3 统计（记为 case-level
   `unjudgeable`）。
4. 若 ERROR 来自**变异源码生成/编译失败**（generator error），则该 mutant 不计入分母（与 identity
   no-op 同处置，记 `generator_fixes`）。

**执行方式**：全量跑完后，按 `res_*.json` 里逐 mutant 的 `status`/`semantic_status`/`errors`/
`inconclusive` 字段**离线重分类**，不重跑。

## 仍待处理（不掩盖）
- `JS-AUGFORM-031` M0005 的 ERROR（round9 样本内）仍原样保留，需单独定位是否属生成器失败。
- 全量结果尚未产生；在跑完并离线重分类之前，**G3 不给任何 PASS/FAIL 结论**。
