# Round 4（Match 族）流程记录

主记录 = `.trae/specs/harden-completed-forms-10rounds/rounds/round4/REVIEW.md`。
注：本目录既有 `ANALYSIS.md` 属 2026-09 boolop_merge 历史战役（commit c33af45b），零改动；本轮流程记录以本文件落盘。

## 产物清单

| 文件 | 用途 | 读数 |
|---|---|---|
| probe_match_min.py/.pyc/OK.py | 管线活性探针（value 单/双 case） | 3/3 success |
| r4_01_match_value.py … r4_14_match_case_body.py/.pyc/*OK.py | 任务A 攻击面 1-15（8 模式 + 组合面） | 见 REVIEW §1（38/96，4 文件 compile_error） |
| n4_01_no_match_control.py/.pyc/OK.py | 负对照（无 match 等价 if/elif + 循环 + try） | 7/7 success |
| r4_or4_and2.py/.pyc/OK.py | 任务B B11-R2 残留探针（or4_and2 形态） | 1/2 failure（已定位签名：or 前缀提升出循环条件） |

## 流程

1. 活性探针先行：最小 value 单 case match 3/3 MATCH，确认管线活性后展开组合面。
2. 14 攻击文件逐个 `py_compile` → `pycdc.py` → `pyc_verify.py single`，全量单元级读数入 REVIEW §1。
3. MISMATCH 单元用 `test_repros/round3/_r3_firstdiff.py` 定位首分歧三元组（滤除 `<module>` 级 code-object 身份噪声）。
4. compile_error 四文件（r4_04/r4_06/r4_09/r4_12）以 `py_compile` 直查 OK.py 语法错误定位发射层废料（内部对象 repr 外泄），并沿 `code_generator.py:3374` 回退汇点 → `ast_converter.py:1710/:1761/:1736` 混合树生产者完成锚定。
5. 任务B：B10-R 以归档产物 single 复验（1/2 持平）；B11-R2 新构 r4_or4_and2 复现 MISMATCH 并首次定位机制签名。
6. 任务C：五支哨兵 single 复验，四支与登记持平；risk_calculation 41/43 为 round3 FIX.md 已注记的口径差异（29 units 旧口径 vs 41/43 现行验证器），零新增回退，建议固化 41/43 为现行登记值。

## 关键结论

- wiki「Match 形态完备」声明被证伪：8 攻击面 6 面 MISMATCH，单元级 38/96（39.6%）。
- 新破口 B12–B19 登记与验收组见 REVIEW §2/§6。
- 判据盲区观察点 R4-O1：pyc_verify 对尾 `return None` 差异归一化，r4_03.match_seq_list2 语义破缺但判 Equal。
