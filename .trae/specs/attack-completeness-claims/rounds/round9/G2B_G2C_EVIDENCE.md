# Task 6.1/6.2 门禁证据：G2b（402 语料）与 G2c（46 真实 pyc）语义差分（rr-v5r06）

## G2b：402 语料（`g2b_402/space_402.json` → 8 分片 semantic_runner → `semantic_402.json`）

| verdict | 条数 | 说明 |
|---|---:|---|
| EQUAL | 57 | 反编译→重编译与原件 pyc 行为等价（module-only） |
| DIFFERENT | 3 | CORPUS402-0226, CORPUS402-0354, CORPUS402-0373 |
| ERROR | 342 | 全部为 `original artifact did not load/execute`——语料为 pyc-only 发行（IQ*/fly），独立执行缺第三方依赖/运行时上下文（环境不可判定，非产品缺陷） |

G2b 判定：**FAIL（部分可判定）**——可判定的 60 条中 57 EQUAL、3 DIFFERENT；342 条环境不可执行逐条在案（C1–C3/C5 证据保留于 semantic_402.json）。
3 条 DIFFERENT 的变体：
- `CORPUS402-0226` → `site-packages/IQEngine/interface.pyc`
- `CORPUS402-0354` → `site-packages/fly/common/convert.pyc`
- `CORPUS402-0373` → `site-packages/fly/common/user_error.pyc`

## G2c：46 真实 pyc（`g2c_46/space_46.json` → `semantic_46.json`）

| verdict | 条数 | 说明 |
|---|---:|---|
| EQUAL | 5 | 行为等价 |
| DIFFERENT（仅 R7 结构） | 19 | 行为等价、字节码/元数据差（真实世界源形态保真缺口） |
| DIFFERENT（含行为差 R0–R5） | 5 | REAL46-004, REAL46-022, REAL46-023, REAL46-031, REAL46-046 |
| ERROR | 17 | 独立执行环境不可判定 |

G2c 判定：**FAIL**——24/46 DIFFERENT（19 条仅 R7 结构差、5 条含行为差）逐条在 semantic_46.json；真实世界源（stdlib）暴露的保真缺口登记为后续族修复输入。

## 口径说明

- 两清单均为 module-only（语料/真实模块不可沙箱调用入口），C4 verdict 为模块级执行 R1–R7 判定；G2b/G2c 门禁阈值（unresolved=0）未达，如实记 FAIL，不宣称语义完备。
- 工具链：semantic_runner 1.0.0 + semantic_diff 1.0.0（judge sha 链 C5 全通）。
