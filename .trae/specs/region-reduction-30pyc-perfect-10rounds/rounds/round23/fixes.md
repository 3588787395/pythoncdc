# Round 23 修复（fixes）：R23-A ＋ R23-B 落地与实测

设计见 `arm-design.md`。本轮落地**只改一个文件**：`core/cfg/region_ast_generator.py`
（`core/cfg/region_analyzer.py` 逐字节未动）。产物侧只有 1 个 `*OK.py` 被重写、索引只有
`last_tested_round` 被推进；不改脚本、不改其他任何文件。

## 一、落地方式（可复现）

镜像谱（全部在 `D:/Temp/r23land/`、`D:/Temp/r23fix/`、`D:/Temp/r23res/`，门禁步骤零仓库写入）：

```
基准镜像  mirr/head23 = 仓库 HEAD(177774b0) 的工作树副本
          （region_ast_generator.py a203dd17fe82f824 / region_analyzer.py 59b70fa360d19ad0，
            与仓库 sha256 前 16 位逐字节相同 ⇒ 它就是"被测量过的 HEAD"）
候选谱    mirr/r23a  (= r23fix/mirr/c1a, ast_gen 40ae2ff060d01adc)   = head23 + R23-A
          mirr/r23b  (ast_gen 506da950eefd201a)                      = r23a + R23-B
          mirr/r23b2 (ast_gen a365c378e6a40fed)                      = r23b + 切分函数 docstring
落地规格  probes/mk_spec23.py  →  probes/sp_landed23.py
          （head23→r23b2 的行级 hunk，3 行上下文、间隔 <4 行合并：analyzer 0 hunks、
            ast_generator 8 hunks；**内置自证**：把 spec 施加到 head23 内存文本，
            两文件的 sha256 必须等于候选镜像，否则不写文件）
落地      probes/apply_spec.py probes/sp_landed23.py          （dry：锚点唯一性 + 逐文件字节增量）
          probes/apply_spec.py probes/sp_landed23.py --write
```

`apply_spec.py` 的约束：白名单只允许 `core/cfg/region_analyzer.py`、
`core/cfg/region_ast_generator.py` 两个路径；每个锚点 `count(old)==1` 否则立即退出；
按目标文件既有 EOL 约定还原 CRLF（该文件纯 CRLF、UTF-8 BOM，行尾不被改写）；
写盘后以内存 `compile()` 做语法自检（不产生 `__pycache__`）。

落地读数：

```
core/cfg/region_ast_generator.py  8 hunks  a203dd17fe82f824 -> a365c378e6a40fed (2976420 bytes)
syntax OK for core/cfg/region_ast_generator.py
```

写盘后复验（`mirr/landed23` = 从**已落地工作树**重新拷贝出的镜像）：

```
core: repo=33 mirror=33 identical=True      bytecode: identical=True (8 files)
pycdc.py identical=True                     region_ast_generator.py a365c378e6a40fed == 候选镜像
工作树该文件：CRLF=48300 / LF-only=0 / BOM=True（与落地前同类）
```

⇒ 后面所有门禁与批量都在"与工作树逐字节相同、且被电池测过"的那一份字节上进行。

## 二、两处代码改动

### R23-A `core/cfg/region_ast_generator.py` `_if_generate_normal`（`16865` 段）

`if _has_or_ext:` 分支开头加本帧快照，分支内 13 处 `self._or_then_block` / `self._or_else_block` /
`self._or_rhs_block` 读取全部改用快照：

```python
_r23_or_then, _r23_or_else, _r23_or_rhs = (
    self._or_then_block, self._or_else_block, self._or_rhs_block)
```

不写回 `self`（`arm-design.md` §二的一致性核对：该函数内 19 处使用全在此分支内，
快照点之后不存在读 `self._or_*` 的消费者）。

### R23-B `core/cfg/region_ast_generator.py` `_loop_generate_while`（`5511-5536` 段）

`_cond_is_ancestor_header` 守卫的 else 分支，在 `self.generated_blocks.add(cond_block)` 之前插入：

```python
_r23_cond_prefix = self._split_block_condition_prefix(cond_block)
if _r23_cond_prefix:
    _r23_cond_stmts = self._build_statements_from_instructions(
        _r23_cond_prefix, cond_block)
    if _r23_cond_stmts:
        pre_stmts.extend(_r23_cond_stmts)
        self._register_prefix_emitted(cond_block, _r23_cond_prefix)
```

配套：`_split_block_condition_prefix` 的 docstring（`286-301`）新增「消费者」一节，把
`AssertRegion` 与 `LoopRegion` 两处消费写成同一条划界 —— 这是 P3 契约同构的落档证据。

## 三、实测读数

### 语料级严格 A/B（`r23_sweep.py`，402 文件 × 3 个镜像核，零仓库写入）

| 核 | Σn_ok | n_fn | Σ\|orig−decomp\| | 产物长度变化的文件数 |
|---|---|---|---|---|
| `head23` | 6004 | 6207 | 1771 | — |
| `r23a`（R23-A） | 6004 | 6207 | **1585** | **1 / 402** |
| `r23b2`（R23-A＋B，落地核） | 6004 | 6207 | 1590 | **1 / 402** |

逐文件对照：`r23a → r23b2` **只有 1 个文件**变化（`realtime_event_source`，
`n_ok 10/12` 不变、`sad 12 → 17`）；BETTER 0 / WORSE 1 / cand-err 0。
两个候选的语料触发面都是同一个文件 —— `sad` 上升正是 `arm-design.md` §四预告的
"标尺在 D1 未消前对 D2/D3 全盲"，**不能当门禁**。

`ANALYSIS.md` §4 风险面复核（谓词前驱形状 vs 落地核）：

```
files carrying precursor shape: 39   byte-identical products head vs landed: 38
   of which fully strict-matching at head: 14  (all byte-identical: True)
```

即：形状出现 39 次，只在那 1 个文件里真正触发；14 个当时已完全匹配的文件逐字节零变化（要求满足）。

### 最小复现电池（16 case ＋ 语料锚点，对**落地字节**复跑，`battery_landed.txt`）

```
cases=16  PRED_R23A_FIX=0  CONTROL=6  OK-on-all-cores=9
fixed by landed (vs head) = 3 ; broken by landed = 0
sum |orig-decomp| per core (py shapes): head=21, landed=12
G0(corpus anchor improves with landed)=True     G2(controls untouched)=True   G3(no regressions)=True
GATE: PASS
CORPUS ANCHORS  realtime_event_source: head |d|=198 (clock_worker 1276/1079)
                                    landed |d|=17  (clock_worker 1276/1292; get_one_event 19/20)
```

被修好的 3 例即 `ANALYSIS.md` §2.4 的 Q1 复现三兄弟：
`b07_outer_body_stmt_then_inner_rotated_while`、`b08_outer_true_loop_body_stmt_then_inner_while`、
`b11_chained_compare_loop_cond_prefix`（各 −3 → OK）；判别子 `b09`（内层是 `if`）与
`b10/c12..c15` 六条 CONTROL 全部零变化；候选核阶段另跑过三核电池 `battery_r23b.txt`，
`head/c1a/r23b` 同值。`G1` 打印 `NOT EVALUATED`（R23-A 在 `.py` 形状层不可测，见设计 §二）。

### (i)(ii)(iii) 替换门禁

* **(i)** 产物 `realtime_event_sourceOK.py`（`single` 写出，21823 chars）里
  `dt = datetime.datetime.now()` 出现在内层 `while dt.replace(second=0, microsecond=0) <= ...`
  **之前**（落地前该处 `dt` 未绑定）。
* **(ii)** 官方尺 `first_diff`：`index=666`（orig `LOAD_GLOBAL 'datetime'` / decomp
  `LOAD_FAST 'dt'`）→ `index=794`（orig `LOAD_FAST 'now_date'` / decomp `JUMP_FORWARD`）。
  同一函数 `true_diffs 612 → 480`、`jump_diffs 3 → 15`。
* **(iii)** 其余 401 文件逐文件 `sad` 不回退（上表：变化文件数 = 1）。

### 靶子 `single`（官方尺）

```
site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc
  partial 11/12 91.67%   clock_worker orig=1275 decomp=1291 jump_diffs=15 true_diffs=480
                         first_diff index=794
```

本轮**不翻转**该 pyc（三层残余只消了 D1，见 §四）。翻转 0 个 pyc 是设计里就写下的预期
（`ANALYSIS.md` §6：R23-A 单独、R23-A＋B 合起来都翻不动 `realtime_event_source`）。
