# Round 19 设计（arm-design）：R19-A `[R3-Continue]` 补发射加「自然迭代回边」末判据

## 一、症状与目标

`site-packages/IQCommon/util/user_info_utils.pyc` 项目工具 `partial 8/9`，唯一不一致函数
`remove_lock_files`，严格尺子 `[seq_len] orig=96 decomp=97`。产物在

```python
                for file in files:
                    if file.endswith('.lock'):
                        file_path = os.path.join(root, file)
                        try:
                            os.unlink(file_path)
                        except BaseException:
                            system_log.error(...)
                        continue        # ← 原始源码里没有
```

指令级唯一真实差异 = 多一条 `JUMP_BACKWARD to 420`（420 是 `for file in files:` 的 FOR_ITER）。
`for: if c: <stmts>` 的臂尾本来就有这条循环自然迭代回边，源码级再写一条 `continue`
就编成两条。逐条两世界实测与候选规则表见 `test_repros/round19_cont/ANALYSIS.md`。

## 二、发射点：两条路径对同一结构给出相反结论

* `_process_if_blocks` 的 CONTINUE 角色分支已**正确抑制**（`_r100_suppress` 末支
  正是 `region.merge_block is _r100_hdr and self._if_false_path_is_loop_iteration(region)`）。
* `_if_generate_normal` 的 `[R3-Continue]` 补发射随后又判一次：「then 分支末块
  `JUMP_BACKWARD` 直达 merge 且 `merge_block is 当前循环头`」⇒ `then_stmts.append({'type': 'Continue'})`，
  把上层刚得出的「if 是循环体末条语句」结论推翻。实测发射行 = 打补丁前 `:16896`
  （该文件内该函数唯一命中，`sys.settrace` 抓真实命中而非读码猜测）。

同一层次、同一结构在两条路径上得到互斥结论——这正是 Round 17 删判据④用的标准
（同层同结构必须同结论）。

## 三、修法：只加末判据，且用**既有**谓词

```python
            if (then_stmts
                    and self._current_loop is not None
                    and getattr(region, 'merge_block', None) is not None
                    and region.merge_block is getattr(self._current_loop, 'header_block', None)
                    and not self._if_false_path_is_loop_iteration(region)):   # ← 第⑤条
```

`_if_false_path_is_loop_iteration`（打补丁后 `:18789`）是**已存在**的同层判据，语义为
「if 无 else 分支，且条件入口的非 then 后继是纯 `JUMP_BACKWARD→header` 块 ⇒ if 是循环体
末条语句」；`:20702` 的 CONTINUE 角色抑制已经在用它。把它接到补发射上，两条路径共用同一
结论，不新建任何判据、不加新函数、不看名字/常量/偏移。

## 四、被实测否掉的三个候选（镜像核，仓库零写入）

| 候选 | 规则 | 39 项电池 | 全量 402 逐函数 A/B |
|---|---|---|---|
| `cand_a` | 整段删 `[R3-Continue]` | 修 10 锚点、负对照全保 | 改好 2 / **改坏 5，净 −3** |
| `cand_g` | 只加 28 行新谓词「臂尾块由本区域块裸 fall-through 进入」 | 修 10 锚点 | 改好 2 / **改坏 2，净 0** |
| `cand_e` | ⑤ + `cand_g` | 修 9 锚点、负对照全保 | 改好 1 / 改坏 0，净 +1 |
| **`cand_d`＝R19-A** | **只加 ⑤（既有谓词）** | **修 9 锚点、负对照全保** | **改好 1 / 改坏 0，净 +1** |

`cand_e` 与 `cand_d` 在电池与全量两项实测上逐条相同 ⇒ 那 28 行新谓词是纯冗余，按最小改动取 `cand_d`。

关键教训（已写进 `ANALYSIS.md` §三）：`cand_a` 在 39 项电池上**全绿**（19 个负对照一个没破），
在全量上却净亏 3 个函数——破掉的是 `local_finance.get_local_valuation_factors`、
`basic_data_source.BasicDataSource.get_security_info`、`trade_live_broker._process_*` 等
真实形状。**电池绿不等于无回退，门禁必须含全量逐函数 A/B。**

## 五、门禁计划（按 mandate 顺序）

1. 单点：`scripts/pyc_batch_verify.py single site-packages/IQCommon/util/user_info_utils.pyc`
   → 必须 `ok 9/9 100.00%`，再用严格尺子复验 `9/9`。
2. `quotation.pyc` 单验 → 必须与本轮开始前逐字相同（`partial 142/143 99.30%`，产物不被改写）。
3. 全量批量回归：`_r13_gate.py` 分 8 片（基线 = 落地前磁盘产物逐函数严格比对，utf-8），
   异常集合必须与 Round 18 **逐文件相同**（9 项既有漂移族）。
4. 电池：`round19_cont` 39 项 `--strict` 退出码 0；既有 8 套逐一复跑。
5. 索引只按工具实测回填，`stats` 不得下降。
