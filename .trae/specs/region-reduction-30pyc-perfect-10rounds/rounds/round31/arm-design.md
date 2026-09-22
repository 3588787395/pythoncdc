# Round 31 arm design — R31-C：臂停止集里「没有正常后继、前驱全在臂内」的终止块是本臂的终点语句，不得作臂与兄弟臂的边界认领（原则 2 · 站点一 ＋ elif 链重收集处复放）

## 靶子与目标池（实测，基线 = 落地字节 `7b5f760c`，核 sha `7ee4151d31faf41b8202`）

`logs/pool31.txt` 首行（从 round 30 G6 回写的 `pyc_index.json` 直接读，不转述）：

```
baseline(landed round30 index, HEAD 7b5f760c): files 402 partial 32 sum_deficit 104 deficit1 8
```

即：Round 30 落地的 R30-C1 把靶子 `default_event_source :: events` 的 17 条外层循环尾语句取回，但
**没有翻转任何文件**（官方尺只看函数整体是否逐位相同，函数内补回指令仍是 unmatched）⇒ 官方计数池
与 Round 30 同形。八个 deficit-1 文件按落地核逐个 `single` 复测（`logs/landed_d1.txt`，逐条一手）：

| 文件 | 唯一 unmatched 函数 | orig/decomp | jump | true | 上一轮的归因 |
|---|---|---|---|---|---|
| `fly/common/flytools.pyc` | `FileLock.acquire` | 88/85 | 2 | 14 | R30 线 A 拆出的「`except-as e` 清理＋裸 raise 迁移＋环尾回边」族 |
| `IQCommon/manager/instance.pyc` | `_init_config` | 86/84 | 1 | 37 | 共享 `return None` 尾声内联，R16 J1 在册反例 |
| `IQCommon/util/replace_utils.pyc` | `decrypt_database_url` | 295/324 | 1 | 250 | 已生成区域体二次走查（过量发射，需放弃发射侧） |
| `IQEngine/.../strategy.pyc` | `tick_worker_thread` | 268/247 | 32 | 113 | 链式比较条件块整体未发射（真 deficit） |
| `IQEngine/.../default_event_source.pyc` | `events` | 510/508 | 2 | 157 | R30 残余：15 条错位＋两跳转槽（R30-C2 形状） |
| `IQEngine/.../realtime_event_source.pyc` | `clock_worker` | 1275/1291 | 15 | 480 | R22/R23 在册残余 D2＋D3 |
| `IQEngine/.../matcher.pyc` | `DefaultMatcher.match` | 713/689 | 9 | 524 | 281 指令区域被推迟到函数尾并旋转 |
| `IQEngine/.../risk_calculation/function.pyc` | `save_testds_to_json` | 314/310 | 19 | 8 | 异常尾声缺**重复副本**（发射侧） |

## 三条候选线的取舍（全部实测，线 A 由只诊断代理在其私有目录完成，编排方在自己的镜像根独立复现）

* **线 A（取）**：`flytools :: FileLock.acquire`。理由：① 有可得的 G0 —— 代理造的 3 见证＋6 CONTROL
  合成件在落地核上确实失败（`1/4`），且 CONTROL 在三把核下逐字节相同；② 判据是**纯归属取消**
  （只 `set.discard`，不新增任何发射），命中面可穷举；③ 靶子是**能翻转**的：`64/65 → 65/65`，
  且在严格尺下从 `65/66`（σ-defect=1、Σ|Δ|=5）到 `66/66`（σ=0、Σ|Δ|=0）—— 两条尺同时收口。
* **线 B（不取，继续移交 #61）**：R30-B3（汇合块两臂同时取消认领）门禁齐备但**官方尺中性、无 G0**。
* **线 C（不取）**：`events` 残余 −2 需要**两条**判据（R30-C2 的裸体块就地渲染 ＋ 那两跳转槽），
  且 R30-C2 单独使用时官方尺 `jump_diffs 2→4` 反而变差 —— 不是一条同层判据能收口的靶子。

## 二、根因链（代理一手打戳＋块级树转储 `logs/diagA_ANALYSIS.md`、`logs/blockdump_head.txt`；
编排方复核：靶子翻转到 `65/65` 且严格尺 `66/66`，落地核上的同形转储 `logs/blockdump_landed_regions.txt`
—— 终止块 B364 由 `pred=B242,B314` 的 `role=LOOP_ELSE` 变成臂尾，`succ=B568` 一条不变）

1. `acquire` 的 `except OSError as e` 处理器臂是一个 `IfRegion@B200`：`then=[B242]`、
   `else=[B366,B508,B558]`、`merge=None`。臂内嵌套区域（`IfRegion@B242`，其 then 臂 `B314`）的
   **终止块 B364**（`RAISE_VARARGS 0`，`successors == exception_successors == {B568}`，即没有
   正常后继）被 `boundary_stop`（`region_analyzer.py:16581 / 16610`）原样带进外层 if 的
   `then_stop`／`else_stop`（`:17135-17136`）。
2. 于是 B364 **不属于任何一条臂**：`_collect_branch_blocks` 见到它在停止集里就停止扩张，而它又
   不被登记为臂尾。落单后由父区（`except` 处理器的顺序尾部，发射点
   `region_ast_generator.py:24695`）在**整个 if/else 之后**把它发出来。
3. 一个错位同时造出靶子的全部三处 hunk（`logs/hunks_head_tracked.txt`）：臂尾 `raise` 落到 if/else
   之后（H1，官方尺 @364 的 jump 差）、`except` 正常出口的 as-var 清理尾声被那份错位覆盖而失去
   发射路径（H2，−4）、循环回边失去发射路径（H3，−1）。这就是 R30 把它误记成「三族混合」的原因：
   它是**一个**归属错误的三个症状。

## 三、判据 R31-C（原则 2 每块唯一归属 · 臂内终止汇合块侧；站点一 ＋ 站点二复放）

落地位置：`core/cfg/region_analyzer.py:17137`（站点一，40 行）与 `:19310`（站点二，28 行），
`git diff --numstat` = `68 0`，纯新增、无删除。代码内注释标签写作 `[R31-B 同层判据 …]`（站点一的
代码即 R31-B 本体，站点二复放同一判据）；本轮发货名 R31-C。

```python
for _r31b_arm, _r31b_other, _r31b_merge, _r31b_stop in (
        (then_succ, else_succ, merge, then_stop),
        (else_succ, then_succ, merge, else_stop)):
    if _r31b_arm is None:
        continue
    _r31b_inner = {_r31b_arm}
    _r31b_go = True
    while _r31b_go:                      # 不动点：取消认领后臂内集扩大，可能露出新的终止块
        _r31b_go = False
        for _r31b_s in list(_r31b_stop):
            if (_r31b_s is _r31b_merge or _r31b_s is _r31b_other
                or _r31b_s is _r31b_arm):
                continue                                  # ① 仍是汇合块／兄弟臂入口／臂入口
            if (_r31b_s.successors
                - (getattr(_r31b_s, "exception_successors", None) or set())):
                continue                                  # ② 有正常后继 ⇒ 它是真正的边界
            _r31b_preds = set(_r31b_s.predecessors)
            if not _r31b_preds or not (_r31b_preds & _r31b_inner):
                continue                                  # ③ 至少一个前驱已在臂内
            if not _r31b_preds <= (_r31b_inner | _r31b_stop):
                continue                                  # ③ 全部前驱都在臂内∪停止集
            _r31b_stop.discard(_r31b_s)
            _r31b_inner.add(_r31b_s)
            _r31b_go = True
            break
```

识别的全部是**同层结构**：块身份（是否本区域汇合块／兄弟臂入口／臂入口）、后继集与异常后继集的
差（有没有正常后继 = 是否硬出口语句块）、前驱集与「臂内集∪停止集」的包含关系。不读名字、常量、
绝对偏移、指令条数、函数名。归约方式是**只删不增**：仅从本臂的局部停止集取消成员认领，让它落回
`_collect_branch_blocks` 的臂尾；不命中时代码路径与既有行为逐字节相同。

站点二必要性的实测证据（`logs/g01_b.jsonl` vs `logs/g01_c.jsonl`）：只做站点一时合成见证
`w_a_handler_raise_after_nested_if` 仍失败（`witness 2/4`），因为链汇合重建 `_chain_merge` 后
`_then_stop` 在此处**重新从 `boundary_stop` 组装**，把站点一的成果覆盖掉；复放同一判据后
`witness 3/4`。两臂在语料上的产物 sha 级 `SAME=402`（代理测）／本轮 G4 只用发货形 R31-C。

## 四、本轮一手实测（编排方自己的镜像根 `D:/Temp/r31gate/c1`，非转述）

| 门禁 | 读数 | 日志 |
|---|---|---|
| G0 见证 | 落地核 `1/4`（w_a 52/47 j4 t11、w_b 48/44 j3 t14、w_c 64/63 j2 t51）→ R31-C `3/4` | `g0p_head.jsonl` / `g0p_c.jsonl` |
| G0 CONTROL | 三把核同读 `5/7`，失败对同形（`c2_arm_tail_is_break` 51/49、`c6_both_arms_end_in_raise` 46/52），产物 sha `SAME` | 同上 |
| G1 靶子 | `flytools.pyc 64/65 [acquire 88/85 j2 t14]` → `65/65 []` | `g1_head.jsonl` / `g1_c.jsonl` |
| G2′ 38 合成复现 | `{"SAME": 38, "IMPROVED": 0, "REGRESSION": 0, "MOVED": 0, "other": 0}` | `g2prime_38.txt` |
| G3 98 承重锚点 | `{"SAME": 98, ...}`（本轮起把 R30 的两件合成锚并入 `anchors98.txt`） | `g3_98.txt` |
| G4 全 402 A/B（sha 优先，发货判据） | `SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0`，`files fully matched: a=370 b=371` | `g4_ab402_sha.txt` |
| G4′ 严格尺逐个变化产物 | `flytools` `65/66 σ1 Σ|Δ|=5` → `66/66 σ0 Σ0`；`gtn_api` 两把核均 `5/5 σ0 Σ0` | `g4prime_head_flytools.txt` / `g4prime_flytools.txt` / `g4prime_head_gtn_api.txt` / `g4prime_gtn_api.txt` |
| G4′ 产物身份 | 入库的两个 `*OK.py` 与实测镜像 `build_c` 产物逐字节相同（sha16 `d1ddb72cf60efdfe` / `f26e8a084eef60cc`） | `products_sha.txt` |

## 五、被排除的候选与已知代价（勿再取）

* **R31-B（只做站点一）**：靶子同样翻转 `65/65`，且语料产物与 R31-C 逐字节相同，但合成见证少一半
  （`2/4`）—— 站点二的覆盖是真实存在的失效路径，不取。
* **`w_c_handler_nested_raise_deep`（`64/63 j2 t51`）不属本判据**：它的落单块前驱不满足③，
  是第三个形状，保持失败并登记为新锚点要求。
* **CONTROL 里 `c2`／`c6` 在落地核上已经失败**：与本判据无关的既有缺陷（`c2` 臂尾是 `break`
  → 有正常后继，判据不该命中；`c6` 两臂同以裸 raise 终止）。它们只作 sha 级不变性证据，
  不得当作「保持 matched」的见证 —— 代理原稿的 CONTROL 头注释在这两点上是错的，
  入库时已按实测改写。
* **`IQCommon/api/gtn_api.pyc` 的 MOVED**：官方尺 `5/5 → 5/5`、严格尺两把核 `5/5 σ0`，产物差异是两处
  `else: time.sleep(1)` 折叠成不缩进的顺序语句（`logs/g4prime_gtn_api_diff.txt`，产物 87→85 行）。
  两条尺都判忠实 ⇒ 接受，但登记为「ok 文件产物文本变化」在册观察项。
* 靶子族的两个兄弟成员未被本判据触及：`risk_calculation/function.pyc :: save_testds_to_json`
  （缺**重复的**清理副本，需发射侧「增」）与 `replace_utils.pyc :: decrypt_database_url`
  （过量发射，需放弃发射侧）—— R30 的「同族拆分」结论继续有效。
