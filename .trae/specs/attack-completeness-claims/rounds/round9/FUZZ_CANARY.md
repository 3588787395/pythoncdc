# Task 9.5 — Fuzz 与 Canary 证据

## 结论

- `fuzz_driver.py`、`minimize.py`、`canary_runner.py`、`fuzz_selftest.py` 已实现；自测 11/11 通过。
- 有界 fuzz：24 例，`20 EQUAL / 4 DIFFERENT`；4 个失败全部最小化成功。
- Bootstrap canary：24 条，`20 EQUAL / 4 DIFFERENT`；泄漏扫描 0 命中；G6 = `FAIL`，原因 `canary_not_equal`。
- 本轮不能声明 G6 通过，也不能声明「4 小时内无新 DIFF」：实际只跑了 24 例、240 秒预算，`stopped=case_limit`，不是周级 4 CPU 小时。
- 4 个发现尚未分配新 B 编号；去重与登记留给 Task 10，不能在本轮宣称是全新破口。

## 运行命令

```powershell
python -X utf8 tools\completeness\fuzz_driver.py `
  --seed 0 --cases 24 --seconds 240 `
  --json .trae\specs\attack-completeness-claims\rounds\round9\fuzz_report.jsonl `
  --summary .trae\specs\attack-completeness-claims\rounds\round9\fuzz_summary.json `
  --workdir .trae\specs\attack-completeness-claims\rounds\round9\fuzz_work

python -X utf8 tools\completeness\minimize.py `
  --input .trae\specs\attack-completeness-claims\rounds\round9\fuzz_report.jsonl `
  --out .trae\specs\attack-completeness-claims\rounds\round9\minimized `
  --limit 4 --seconds 300 `
  --json .trae\specs\attack-completeness-claims\rounds\round9\minimized\minimized.json

python -X utf8 tools\completeness\fuzz_selftest.py
```

Canary 使用 git-ignored 的 `.canary-private/` 本地 bootstrap 集；命令：

```powershell
python -X utf8 tools\completeness\canary_runner.py `
  --canary .canary-private `
  --json .trae\specs\attack-completeness-claims\rounds\round9\canary_report.json `
  --leak-scan-md .trae\specs\attack-completeness-claims\rounds\round9\canary_leak_scan.md `
  --scan-root core --scan-root tools --scan-root tests --scan-root wiki `
  --scan-root docs --scan-root rules.md `
  --scan-root .trae\specs\attack-completeness-claims
```

## Fuzz 读数

`fuzz_summary.json`：

- `total=24`
- `counts={"EQUAL":20,"DIFFERENT":4}`
- `failures=4`
- `budget_seconds=240`
- `stopped=case_limit`
- `new_diff=4`

工具边界：

- 生成器只依赖 CPython 3.11 AST，不 import 产品代码。
- 每个用例经 `compile` → `pycdc.py` → product compile → `semantic_diff` 执行比对。
- 失败用例保留 `subject.py`、`subject.pyc`、`product.py`；EQUAL 用例默认删除工作目录。
- `INCONCLUSIVE`/`ERROR` 不计入 EQUAL；`--keep-equal` 可保留全部工作目录。
- `--cases 0` 表示按时间预算持续生成；本轮显式使用 `--cases 24`。

## 四个失败与最小化

| case | template | 最小维度 | 行数 | 现象 |
|---|---|---|---|---|
| `FZ-raresyntax-015-11d70844` | `starred-unpack` | R6, R7 | `6→3` | product 丢掉 `data = [...]`，并把嵌套 `call` 的绑定/签名弄乱；最小源执行 `NameError: name 'data' is not defined` |
| `FZ-semantictrap-020-1d4bb36d` | `generator-send` | R1, R7 | `15→14` | `g.send()` 序列的返回值与 `yield` 恢复值不一致；product 少一次 `yield` 赋值路径 |
| `FZ-raresyntax-021-5433fdc8` | `annotations-posonly` | R7 | `2→2` | product 签名丢失 positional-only `/`；两行已最小，无法再删 |
| `FZ-semantictrap-023-cb72b56d` | `finally-return` | R1, R5, R7 | `14→10` | product 丢失 `return ("ret", i)` 并把 `global` 提升到模块层；返回 `events` 列表，副作用事件数不同 |

最小化判据要求**最小化后状态与维度集合和原始完全一致**，不是维度子集。初版子集判据曾把 generator 失败缩成另一个 R7/NameError 失败，已修正并全量重跑。证据在 `minimized/minimized.json` 与每个 `.original.py`/`.min.py`。

## Canary 读数

- 私有集：`.canary-private/`（本地 git-ignored，不提交明文）。
- 规模：24 条，`rare_syntax=8`、`deep_host=8`、`semantic_trap=8`。
- 公开清单：`canary_manifest.json`，只含 24 条 ID、类别、template、source sha256、feature sha256；不含源码或 feature 明文。
- 结果：`20 EQUAL / 4 DIFFERENT`，泄漏扫描 0 命中。
- 失败：`CN-RARE-06`（R6/R7）、`CN-RARE-08`（R7）、`CN-TRAP-07`（R1/R7）、`CN-TRAP-08`（R1/R5/R7），分别对应上面的四个 fuzz 模板。
- G6：`FAIL`，`reason=canary_not_equal`。

这一组是 **local-bootstrap**，不是独立保管的 C 角色 canary。即使 24/24 EQUAL，G6 也只能记 `INCONCLUSIVE`；当前 4 条失败则直接 `FAIL`。公开清单可复现 ID 与哈希，但无法证明私有集未被产品生成器接触。

## 泄漏扫描边界

扫描根：`core`、`tools`、`tests`、`wiki`、`docs`、`rules.md`、`.trae/specs/attack-completeness-claims`。命中 0。

这不是全文件系统秘密扫描；`--canary` 私有目录被显式排除，避免把探针自身算作泄漏。命中任意 feature 即判定 `FAIL`。

## 未完成/后续

- 周级 fuzz 仍不足 4 CPU 小时，不能写「连续 4 小时无新 DIFF」。
- 4 个 fuzz 发现未去重、未登记 B 编号；Task 10 需映射到既有 B 族（可能涉及 B142/B203/B207/B210）或新增 B220+。
- 没有产品修复；本轮只证明检测能力与失败台账。
- 独立 canary 保管、季度轮换、真实 C 角色签署缺失；Task 9.6/最终审计不得把本地 bootstrap 当作 G6 PASS。
