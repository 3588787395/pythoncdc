# J 空间行（REACHABILITY 主表第 1 行）实测记录

**表内阈值**（`REACHABILITY.md` L28）：`1556 条全量`；`source_missing = 0`、`pyc_missing = 0`、
`calls_missing = 0`。**注意：这不是 `covered_5tuple`**——本行问的是「每条 J 是否有源码、有 pyc、
有可调用入口」，不是覆盖率。此前把本行读成覆盖率（1174/1556）是口径错误，现按表实测。

## 实测（`round13/row_fix/fix_jspace_source.py` 生成 `jspace_row` 块）

| 指标 | 修复前 | 修复后 | 说明 |
|---|---|---|---|
| `total` | 1556 | 1556 | 全量 |
| `source_missing_non_excluded` | **12** | **0** | JS-PEP604-001..012 的 `source` 字段写的是散文
  `"Task5.2 generated probe (rr-v5r04)"`，而真实源码就在同名 `js-pep604-00X.py` 旁边 |
| `source_missing_excluded` | 376 | 376 | pyc-only 分布（`site-packages/IQEngine/...`），**无 .py 属客观
  事实**；这些条目 `excluded=true`，按 J 五字段设计正当排除，不计入 `source_missing` |
| `pyc_missing` | 0 | **0** | 1556/1556 文件存在 |
| `pyc_loadable`（magic 实测） | 未测（字段为 `null`） | **1556/1556** | `co_magic == importlib.util.MAGIC_NUMBER` |
| `calls_missing_non_excluded` | — | **0** | 449 条非排除条目**全部**有非空 `input_model.calls`；
  1107 条排除条目无 calls（`excluded` 与 `calls 为空` 完全一一对应：`{(True, False): 1107,
  (False, True): 449}`） |

## 修复内容
- 仅改 12 条 `source`：指向 pyc 同目录同名 `.py`；旧值保存在新增 `source_note` 字段（可 `--revert`）。
- 其余 1544 条逐字未变；`entries` 数组顺序、`p_j`/`pyc_sha256`/`expected_label`/`input_model` 全部未动。

## 诚实边界
- `376` 条 `excluded` 条目的 `source` 仍是散文而非路径。这是**客观无源码**（pyc-only 发布物）而非
  记账缺陷；表中 `source_missing = 0` 的解释是「非排除条目无缺失」。若要求**全部 1556 条**都有
  真实源码路径，则本行不可能达成（原始 .py 已不存在），必须由评审裁决该解释是否成立。
- `pyc_loadable` 此前字段为 `null` 却从未有人测量，本轮补测 1556/1556 通过（magic 匹配）。

## 复算命令
```
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\rowfix\fix_jspace_source.py
# 输出 {"total":1556,"source_missing_non_excluded":0,"source_missing_excluded":376,
#       "pyc_missing":0,"calls_missing_non_excluded":0}
```
