# AUDIT R19 —— 「所有 pyc 都要反编译」的范围在**本工作树**重新钉死（不引用旧快照）

先前的范围证据 `baseline/corpus_census.json` + `baseline/exclusion_evidence.md` 封表于 2026-10-05，
且其 `corpus_root` 字段指向**另一个检出目录**（`worktrees/app/6f79dd/...`），
依 [[measure-committed-not-working-tree]] / [[hardcoded-repo-root-in-worktree]] 不得直接拿来当本轮结论，
故在此对当前树 `app/f557fd/site-packages` 逐文件读 pyc 头 + `marshal` 取 `co_filename` 重测（全量，非抽样）。

## 实测读数（2026-10-09 14:04，本树全量 1722 个 .pyc）

```
pyc_total = 1722
  ├─ 由 *OK.py 再编译而来的派生件（cpython-3.11 magic a70d0d0a 且 co_filename 末段含 OK.py）= 1316
  ├─ 非 3.11 magic（cpython-3.13 f30d0d0a 等）                                        =    3
  └─ 3.11 原始字节码（待反编译类）                                                    =  403
门名册 baseline/shards/shard0..7.json 条目 = 402（无重复）
ORIGINAL_NOT_IN_ROSTER = 1      ROSTER_NOT_ORIGINAL = 0      roster_without_OK_product = 0
```

那 1 个名册外「原始类」逐条核实为**测试残骸**，非待反编译语料：

```
fly/simtradding/ptradeAccountOK_marker_test.pyc   （OK 兄弟文件不存在；文件名含 OK_marker_test，
                                                   系某轮 marker 测试自造源再编译的产物）
```

## 结论（写给完成审计，不是写给施工）

1. **objective 的验证面 = 这 402 个原始 .pyc**，与门名册 1:1（`ROSTER_NOT_ORIGINAL=0`），
   差额 403−402 已逐条归因为测试残骸；余下 1319 个（1316 派生 + 3 异 magic）均非待反编译对象，
   与 `exclusion_evidence.md` 的 B/C 判据在本树复现一致（本轮实测 1316 vs 旧快照 1312，
   增量为派生件随落地产物增多，属预期方向）。
2. **402 个名册文件当前全部有同名 `+OK.py` 产物**（`roster_without_OK_product=0`），
   故「每个 pyc 同目录生成同名+OK 的 py 文件」这一条已满足形式要求；
   实质要求（产物与原字节码等价）当前读数为 **390/402 文件、6584/6617 单元**（门 18 封盘），
   残余 12 文件 / 33 单元 ⇒ 目标未达成，继续按票施工。
3. 该残骸 `ptradeAccountOK_marker_test.pyc` 属他人/他轮生成物，**未删除**（依
   [[never-touch-uncommitted-work]]：不熟悉的文件先登记再处置）；如后续要清名册，
   须由主代理判定后再动，且不得改动 site-packages 内的任何 `*OK.py` 产物
   （用户硬约束「禁止修改反编译生成的文件」）。
