# Task 7 门禁记录：G5 本树复跑、G6 独立保证、比较器完整性（rr-v5r07）

## 7.1 G5（本树复跑，rr-v5r06 周期）
- 402 八分片：6617/6617（`g5_regression_current.json.total`）
- small34：1568/1568；quotation：153/153
- 全量 pytest（tests/ --ignore=tests/nook）：406 失败清单与冻结基线逐字节一致
- IV.2：IMPORT_OK/COMPILE_OK true、BOM×2 one、G3_forbidden_prefix_new_defs=0
- 判定：实质全绿；gate 字符串口径 FAIL（round8 旧期望「282 passed」，差异原因在案）

## 7.2 G6（独立保证）
- 本环境无独立 custody：按规范记 **ASSURANCE_BLOCKED**，不以本地 bootstrap 冒充 PASS。
- 非资格证据（local-bootstrap，`g6_canary/canary_local.json`）：24/24 EQUAL、
  leak_hits=0、rotation_ok 未建立——runner 自身输出 G6=INCONCLUSIVE
  （reason=local_bootstrap_custody），与规范口径一致。

## 7.3 基本比较器独立复跑
- `scripts/pyc_verify.py` sha256 fe1902a90cebd4a1…，最后修改 65a331ea（本轮前已存在），
  本树零改动（git diff clean）；本轮全部 G5 判定均由该未修改比较器产生。
- `pylingual/equivalence_check.py`、`tests/` 同样零改动。

## 7.4 G1–G5 终读数与 product_complete
| 门 | 读数 | 判定 |
|---|---|---|
| G1/G2a | 395/1556 covered、189 DIFF（Task 5.4 全量） | FAIL |
| G2b | 57 EQUAL/3 DIFF/342 环境不可执行 | FAIL |
| G2c | 5 EQUAL/24 DIFF（19 仅 R7）/17 环境不可执行 | FAIL |
| G3 | 样本 32 killed/602 missed（全量总体未跑） | FAIL |
| G4 | trace 187/339 命中、152 never-hit、proved=0 | FAIL |
| G5 | 6617/6617 + small34 + quotation + IV.2 实质绿（字符串口径 FAIL） | FAIL* |
| G6 | ASSURANCE_BLOCKED（独立 custody 缺失） | BLOCKED |

**product_complete = NOT PASS（BLOCKED）**，与 GATE_REPORT_V5R06 一致；不宣称完备。
失败项进入修复挂账（189 uncovered → 15 文件 25 单元清单、152 never-hit 规则、
G2c 24 DIFF、G3 全量总体+调用模型）。
