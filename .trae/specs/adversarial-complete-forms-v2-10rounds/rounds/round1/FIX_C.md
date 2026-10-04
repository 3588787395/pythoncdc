# FIX_C — Round 1 位 C：op_station.pyc 回归修复报告

- 修复工程师：C（Round 1.2 后续回归修复）
- 回归单元：`site-packages/fly/common/op_station.pyc` → `***<module>.OpStation.__new__`（pyc_sha 5e09167a062b）
- 判据工具：`scripts/pyc_verify.py`（single/batch，compare_pyc 唯一判据）
- 修复基线：HEAD 616437c3（batch B = 33d6e87e 引入回归，20/21）

---

## 1. 根因分析

### 1.1 一句话根因

批次 B 在 `_generate_try` finalbody 发射循环新增的 **[B71] 循环出口块归属守卫**（hunk：`@@ -29683,6 +30078,44 @@`）判据只检查 `fb.predecessors` 中是否存在 `loop_header` 块，**未区分前驱边的类型**——而 finally 异常副本入口块经 3.11 异常表边持有 try 体内全部块（含循环头）作前驱，守卫把异常副本误判为「宿主循环出口块」移出 `finally_blocks`，`Try.finalbody` 语句源蒸发。

### 1.2 结构证据（OpStation.__new__，Python 3.11）

CFG 布局（区域分析 dump）：

```
B0   : if cls._instanced is None          → B18 / B442
B20  : lock.acquire() + 内层 if 条件      → [382(异常), 330, 84]
B84..B266 : try 体（config/for 循环/dict）
B330 : finally 正常副本 lock.release(); JUMP_FORWARD → B442（preds=[266,20]，正常边）
B382 : PUSH_EXC_INFO; lock.release(); RERAISE   ← finally 异常副本入口（finally_blocks=[382,436]）
B436 : COPY; POP_EXCEPT; RERAISE
B442 : return super().__new__(cls)
```

区域结构：`TRY_FINALLY entry=20，try_blocks=[20,84,156,202,204,230,264,266]，finally_blocks=[382,436]，try_offset_end=330`；for 循环 `FOR_LOOP entry=202` 在 try 体内。

关键事实（边类型，来自 `BasicBlock.exception_successors`，dominator_analyzer.py:356 对含 FOR_ITER 的块标 `loop_header=True`）：

```
op_station.__new__（回归场景）:
  fb B382 <- pred B202 loop_header=True  exception_edge=True   ← 异常表边
  fb B382 <- pred B84/B156/B204/B230/B264/B266/B20 ... exception_edge=True

r10_21::fin_break（守卫本应服务的场景）:
  fb B74  <- pred B10  loop_header=True  exception_edge=False  ← FOR_ITER 正常出口边
```

### 1.3 误触发链（破坏的 C 条款）

1. 自底向上发射：try 体内 `FOR_LOOP(202)` 先行生成完毕；
2. `_generate_try` finalbody 分支（`_w11a_nc_blocks` 为空 → `else:` 支，逐 `finally_blocks` 发射）中，[B71] 守卫对 B382 命中（`any(pred.loop_header)` 成立——B202 经**异常边**是 B382 前驱）；
3. 守卫执行「三重释放」：B382 移入 `FOR_LOOP(202).else_blocks` 并从 `finally_blocks`/`blocks` 移除；因宿主循环已发射完毕，移交**永不发射**；
4. `finalbody` 只剩框架块 B436（COPY/POP_EXCEPT/RERAISE，无语句）→ 发射 `finally: pass`，`cls.lock.release()` 整句蒸发；
5. 重编译字节码 finally 体缺失 → `Different control flow`。

**违反条款：C1（嵌套无感不变式）**——守卫把「前驱含循环头」当循环出口证据，但异常表使 try 体内每个块都经异常边指向异常副本入口，循环头（FOR_ITER 块）只是其中特例；守卫未用边类型（`exception_successors`）区分「FOR_ITER 正常出口边」与「异常表边」，判据不封闭。守卫本身设计场景（r10_21 fin_break：出口块被分析器误并入 finally_blocks，B10→B74 为正常边）不受影响。

---

## 2. 修复方案（封闭守卫）

文件：`core/cfg/region_ast_generator.py`（`_generate_try` finalbody 发射循环内）

1. **守卫触发判据加边类型封闭**：循环头前驱仅计正常出口边——

   ```python
   if any(getattr(_p, 'loop_header', False)
          and fb not in (getattr(_p, 'exception_successors', None) or ())
          for _p in (getattr(fb, 'predecessors', None) or ())):
   ```

   即 `fb ∈ pred.exception_successors`（异常边）的循环头前驱不构成出口证据，异常副本入口留在 `finally_blocks` 作 finalbody 语句源。

2. **守卫内宿主循环选取同判据**：内层 `_b71_lh` 选取循环同步跳过异常边循环头，防止异常边循环头抢占移交目标（与触发证据同源，fin_break 行为不变）。

3. **`_generate_try` docstring 补齐六要素**（①算法依据②归约顺序③唯一归属判定④嵌套处理⑤入口引用语义⑥反编译流程）+ 注明 C1/C2/C3 满足方式；守卫处注释同步更新（注释与代码行为一致）。

判据白名单核对：块元数据（`loop_header`）+ 边类型（`exception_successors` 集合成员 = CFG 异常边结构事实）+ 前驱集合 + 区域成员关系（`get_region_for_block`）。无函数名/文件名白名单、无 start_offset 魔数、无跨层反查（`X.entry in Y.blocks`）、无 self 跨方法新状态、无硬编码深度/计数。修复对同构结构通用（任何「try 体含循环的 try/finally」均受益），非 op_station 个案。C3：守卫不命中时其余发射路径逐位不变。

---

## 3. 自测读数表

### 门禁 1：回归单元恢复

| 项 | 修复前 HEAD | 修复后 |
|---|---|---|
| op_station.pyc single | failure 20/21（`OpStation.__new__` Different control flow） | **success 21/21**（逐字节 MATCH） |

op_stationOK.py 由 pycdc 重新生成（非手改），diff 恰为一行：`finally: pass` → `finally: cls.lock.release()`。

### 门禁 2：批次 B 既有收益站桩（全部经 stash 单变量对照修复前 HEAD）

| 文件 | 任务基线口径 | 修复前 HEAD 实测 | 修复后实测 | 结论 |
|---|---|---|---|---|
| test_repros/round8/rv8_01_chain3_subscript.pyc | 7/8（≥修复前） | 7/7 | **7/7** | 持平（任务口径 7/8 为早期快照） |
| test_repros/round8/rv8_02_with_tryfin_constret.pyc | ≥6/7 且 with_body_tryfin_chain MATCH | 6/7（失败单元 tryfin_then_more） | **6/7**（同一单元） | 持平；with_body_tryfin_chain MATCH |
| test_repros/round10/r10_14_nonlocal_deep.pyc | 7/7 | 7/7 | **7/7** | 持平 |
| test_repros/round10/r10_16_scope_mix.pyc | 7/7 | 7/7 | **7/7** | 持平 |
| test_repros/round7/r7_03_ternary_stmt_pos.pyc | 7/7 | 7/7 | **7/7** | 持平 |
| test_repros/round8/r8_06_augassign_ops.pyc | 10/10 | 10/10 | **10/10** | 持平 |
| test_repros/round10/r10_21_fin_loopctrl.pyc | 2/4（B71 部分封闭基线，不得变差） | 4/4 | **4/4** | 持平（2/4 为批次 B 修复前锚点，FIX_B 记录 after=4/4） |
| test_repros/round7/r7_08_ternary_deep_host.pyc | ≥4/8 | 7/8 | **7/8** | 持平（t_host_match_case 存量 B77） |

批次 B 锚点收益复核：r10_15_global_hosts **6/6**（B75）、r10_04_import_try_cross **3/3**（B73）、rv10_32_augassign_variant **8/8**（B76）——全部保持。

### 门禁 3：负对照探针（全部经 stash 对照，修复前后读数逐位一致）

| 探针 | 修复前 HEAD | 修复后 | 结论 |
|---|---|---|---|
| v_b65_face | 3/3 | **3/3 MATCH** | 保持 |
| v_b71_face | 3/4（v_nest_fin_continue 存量） | **3/4**（同一单元） | 基线同态 |
| v_b73_face | 2/3（v_imp_cond_fin 存量） | **2/3**（同一单元） | 基线同态 |
| v_b74_face | 3/4（n_true_guard 存量） | **3/4**（同一单元） | 基线同态 |
| v_b75_face | 1/3（v_swap_arm_returns + n_fin_noseg 存量） | **1/3**（同单元） | 基线同态 |
| v_b76_face | 4/4 | **4/4 MATCH** | 保持 |
| v_b50_face | 4/4 | **4/4** | 保持修复前读数（B50 +1 后口径） |
| v_b46_face | 1/4（v_if_cond_nest + n_for_body_nest 存量） | **1/4**（同单元） | 基线同态 |

注：任务书「v_b71/b73/b74/b75_face 必须 MATCH」与复核批次（165f082c）登记不符——该批登记「6 MISMATCH 全部基线同态存量 B77-B82」；实测上述失败单元在修复前 HEAD 同样失败且失败单元逐一相同，非本次修复引入。

### 门禁 4：34 小集抽样 6 文件 batch（对照 small34_report_new.json）

| 文件 | 基线 | 修复后 |
|---|---|---|
| site-packages/IQCommon/util/email_utils.pyc | 3/4 | **3/4** |
| site-packages/IQCommon/util/cgroup_utils.pyc | 7/8 | **7/8** |
| site-packages/IQEngine/core/executor.pyc | 9/10 | **9/10** |
| site-packages/IQEngine/core/strategy/strategy_universe.pyc | 10/11 | **10/11** |
| site-packages/IQEngine/data/trading_dates_mixin.pyc | 13/14 | **13/14** |
| site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc | 12/13 | **12/13** |

合计 54/60，逐文件持平，单元数零下降。证据：`probes_fixC/fixC_small6_report.json`。

### 门禁 5：埋点/合规自查

- `git diff` 新增行 grep `print\(|DBG|import pdb|breakpoint\(` = **0**（存量命中均为原有代码）；
- 双核心文件 BOM：`region_ast_generator.py`、`region_analyzer.py` 首 3 字节均为 `efbbbf` 单头 ✓；
- `import core.cfg.region_ast_generator / structured_analyzer / ast_generator_v2` = IMPORT_OK；
- 无新增方法（无禁用前缀问题）；未 git commit。

---

## 4. 触及文件清单

| 文件 | 改动 |
|---|---|
| `core/cfg/region_ast_generator.py` | [B71 边类型封闭] 守卫判据 + 内层宿主循环选取同判据 + 注释；`_generate_try` docstring 六要素补齐 |
| `site-packages/fly/common/op_stationOK.py` | pycdc 重新生成（finally 体恢复 `cls.lock.release()`） |
| `.trae/.../rounds/round1/probes_fixC/fixC_small6_report.json` | 门禁 4 证据（新增） |
| `.trae/.../rounds/round1/FIX_C.md` | 本报告（新增） |

临时探针（dump/probe 脚本、diff 快照）已删除，不留垃圾；二分验证经 `git stash push/pop` 单变量进行，未产生 revert 副本文件。

## 5. 遗留观察项

1. **v_b75_face.v_swap_arm_returns / n_fin_noseg、v_b46_face.v_if_cond_nest / n_for_body_nest、v_b71_face.v_nest_fin_continue、v_b73_face.v_imp_cond_fin、v_b74_face.n_true_guard、r7_08.t_host_match_case**：均为评审登记的基线同态存量（B77-B82），本轮未触碰，留待后续轮次。
2. 任务书门禁 2 的 r10_21「2/4」与 rv8_01「7/8」口径早于批次 B 终态（FIX_B 记录 r10_21 after=4/4）；建议主代理以本报告「修复前 HEAD 实测」列更新门禁基线表。
