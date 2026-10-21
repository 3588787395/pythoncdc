# FINDING — F1：行 `global_nonlocal` 的「完备」判据未覆盖 `nonlocal` 语句（粒度错配实例）

- **编号**：F1（本规范首条击穿证据；关联破口 **B163** 待立）
- **发现层**：L1 口径层（粒度错配）＋ L5 证据层（行级证据与行名不符）
- **被攻击对象**：`attain-true-completeness` v8 终表 §2 的 25 行终表（`rounds/round8/REVIEW.md`），其中 L09 行「global_nonlocal」判为 **完备**，登记深层探针 = `test_repros/round2/x04_try_deep_hosts.pyc`（读数 7/7）。
- **击穿性质**：**行名声明的形态（`global_nonlocal` 中的 `nonlocal` 语句）在本行证据中零出现**——行级「完备」结论与其证据不对应。

## 证据（可复现）

1. 登记探针不含目标语句：
   - `test_repros/round2/x04_try_deep_hosts.py`：`nonlocal=False`、`global=False`（77 行）
   - `test_repros/round10/r10_15_global_hosts.py`（L08 Global 行探针）：`nonlocal=False`、`global=True`（49 行）
2. 真正含 `nonlocal` 的探针存在但**未进入任何证据记录**：
   - `test_repros/round10/r10_13_nonlocal_basic.py`：`nonlocal=True`（28 行）
   - `test_repros/round10/r10_14_nonlocal_deep.py`：`nonlocal=True`（41 行）
   - 证据索引（全部 `rec1_probes_*.json` 的 `pyc_src_rel` 并集 = 202 条路径）中与 global/nonlocal 相关的**仅** `test_repros/round10/r10_15_global_hosts.pyc`；`r10_13` / `r10_14` / `n10_04_simple_nonlocal` / `r10_12_global_deep` **0 命中**。
3. 判定空间侧印证：Task 1 覆盖检查器读数中 `global_nonlocal` 族 **40/40 未覆盖**，而 `ExceptStar` 族 96/96 未覆盖（`rounds/round1/COVERAGE_BASELINE.md`）。

## 结论

- v8 口径「25 行全数完备」中，至少 1 行（`global_nonlocal`）的完备结论**不成立于该行声明的形态**；`ExceptStar`（3.11 `except*`）作为 NEW 族全族零证据。
- 这是「分母 128 把变体维度折叠」的**具体实例**：行名是 25 行粒度，证据是探针粒度，两者交集可能为空，而台账只记录「行 → 探针」的存在性映射，不校验探针内容与行名的形态对应关系。
- **处置**：登记为破口 **B163**（行级证据—形态错配），进入 Task 10 封闭；口径侧按 spec.md「判定空间」改造：行级完备 SHALL 附加「该行声明形态的逐变体证据」要求（覆盖检查器负责机械判定）。
- **方法论教训（写入 spec §3 误解清单候选）**：「行有探针且探针全绿」≠「行声明的形态被验证」——台账 SHALL 记录**形态级证据映射**（行 → 变体 → 证据），而非仅行 → 探针。

## 复现命令

```powershell
python -X utf8 -c "import io;[print(f, 'nonlocal' in io.open(f,encoding='utf-8-sig',errors='replace').read()) for f in ['test_repros/round2/x04_try_deep_hosts.py','test_repros/round10/r10_15_global_hosts.py','test_repros/round10/r10_13_nonlocal_basic.py','test_repros/round10/r10_14_nonlocal_deep.py']]"
python -X utf8 tools/completeness/coverage_checker.py --space .trae/specs/attack-completeness-claims/rounds/round1/judgment_space.json --evidence-root .trae/specs/attain-true-completeness/rounds --out rounds/round1/COVERAGE_BASELINE.md --allow-uncovered
```
