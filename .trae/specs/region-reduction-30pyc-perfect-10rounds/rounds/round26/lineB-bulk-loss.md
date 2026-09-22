# Round 26 诊断线 B：整块丢失族（bulk-loss）取证

只读取证，未触碰 `core/`。原始转储见同目录 `logs/`。

## 一、结论：本族不是「一个原因」，实测拆成三个互不相同的同层形状

对 6 个 deficit≥4 的函数做「原始码流 vs 产物重编译码流」逐条对齐（`logs/dl_*.txt`）与带字节偏移的控制流转储
（`logs/dump_*.txt`），三类机制各自的判据材料如下。

### B1 · 嵌套 elif 链被展平后，链尾条件块被整块跳过 ⇒ 条件丢失 + 后续全成死代码

锚点：`IQEngine/plugins/plugin_system_persist/__init__.pyc :: ObjectPersistancePlugin.can_resume_strategy`
`orig=89 decomp=57`（−32），产物 12 函数中该文件唯一缺陷。

原始（`logs/dump_persist_orig.txt`，5 个**各自独立**的 if，无任何 elif）：

```
B0   L94  if persist_meta['start_date'] != self._meta['start_date']:   POP_JUMP_FORWARD_IF_FALSE ->178
B48  L95     raise RuntimeError(...)                              RAISE_VARARGS (off 176 → 178)
B178 L99  if persist_meta['last_calendar_dt'] is None:           POP_JUMP_FORWARD_IF_NOT_NONE ->198
B194 L100    return False
B198 L103 if last_calendar_dt > self._meta['end_date']:          POP_JUMP_FORWARD_IF_FALSE ->374
B244 L104    raise RuntimeError(...)
B374 L106 if last_calendar_dt == self._meta['end_date']:         POP_JUMP_FORWARD_IF_FALSE ->424
B420 L107    return False
B424 L110 next_start_date = …;  L111 …;  if … > end:            POP_JUMP_FORWARD_IF_FALSE ->548
B544 L113    return False
B548 L115 return True
```

区域层级（`region_analyzer` 实测，代理侧同函数转储与此一致）：

```
IfRegion entry=B0  cond=B0 then=[B48]
                 elif_conditions=[B178, B198]           ← 外层吞掉了内层链的前两级
                 elif_bodies=[[B194], [B244]]
                 elif_final_else=[B374, B420, B424, B544, B548]   ← 链尾成了扁平语句表
IfRegion entry=B178 cond=B178 then=[B194]
                 elif_conditions=[B198, B374]            ← 同一批块的第二套归属
                 elif_bodies=[[B244], [B420]]
                 elif_final_else=[B424, B544, B548]
```

产物（`site-packages/IQEngine/plugins/plugin_system_persist/__init__OK.py` L71-84）：

```
if persist_meta['start_date'] != self._meta['start_date']:
    raise RuntimeError(…)
elif persist_meta['last_calendar_dt'] is None:
    return False
elif persist_meta['last_calendar_dt'] > self._meta['end_date']:
    raise RuntimeError(…)
else:
    return False                          # ← B420，它的条件 B374 被整块跳过
    next_start_date = data_proxy.get_next_trading_date(…)     # ← 重编译时被编译器当作死代码消除
    …
```

机制的**已否证假设**（镜像 `core/` 插桩实测，`D:/Temp/r26self/probe_guard26c.py`）：
最初把丢失归给 `region_ast_generator.py` L11145-11147 的守卫「本区域入口若出现在**另一个**
`IfRegion` 的 `elif_conditions` 里就整体发射 `[]`」——因为 B374 确实同时是 `IfRegion(B178)` 的
elif 条件。**该守卫在本函数上一次都没有触发**（在该站点加 stderr 打印后跑镜像核，产物与落地核逐字节相同、
无 `R26PROTECT` 行）⇒ 「条件块被他人归属吞掉而整块跳过」不成立，落地前须另找发射现场。
候选现场（尚未取证）：`_if_generate_full_elif_chain`（L11708）与 `_generate_elif_part`（L14913）
对 `elif_final_else` 的语句化，以及 L12270-12350 的「else-return 提升为链后尾随语句」一族变换
（后者与本案形状相反：本案是 `else` 臂内 `return False` **之后**还跟着兄弟语句）。

已确证的部分只剩区域层级这一条硬事实：`IfRegion(B0)` 与 `IfRegion(B178)` 对 B178..B548 是**两套归属**
（外层吞掉内层链的前两级、把第三级的条件块留在扁平 `elif_final_else` 表头），
违反原则 2（每块唯一归属）；而 `elif` 与 `else: if` 在 3.11 下码流等价，
所以「外层链在内层已成形区域处收尾」是一个候选方向 —— 但**必须先测出条件在哪一步消失**，
再谈判据（见 [[feedback-measure-block-site-before-editing]]）。

未做（本轮不得做：诊断与落地不同代理）：上述发射现场的取证、`.py` 形状最小复现、全量 A/B。


### B2 · 臂内终结语句（break）之前的兄弟语句被丢

锚点：`IQEngine/plugins/plugin_fly_data/__init__.pyc :: ApiMethodPlugin._on_before_trading_start_trading_thread`
`orig=66 decomp=62`（−4）。原始 L238-242（`logs/dump_thread.txt`）：

```
o38 LOAD_FAST now | o41 COMPARE_OP >= | o42 POP_JUMP_FORWARD_IF_FALSE ->328
o43 LOAD_FAST order | o44 LOAD_METHOD commit | o45 CALL 0 | o46 POP_TOP     L239
o47 JUMP_FORWARD ->404      L240        ← 404 = 外层 while 的重测块 B59 ⇒ 语义是 break
o48 LOAD_GLOBAL time … time.sleep(min(order_time-now, 30))   L242  (328..402)
o58 JUMP_BACKWARD ->132     L234
```
即真实源码是 `if now >= order.order_time: order.commit(); break` / 尾随 `time.sleep(…)`。
产物 `else`-less 形状只剩 `if now >= order.order_time: break`（`logs/dl__on_before_trading_start_trading_thread.txt`
的 `replace orig[42:48] decomp[42:44]` 回段：真值臂被替换成「守卫 + 无条件跳转」两条）。
⇒ **臂的首干语句（非终结）在「臂以 break 收尾」时被丢**，与 B1 不同层（B1 丢条件，B2 丢臂内前导语句）。
同文件另一函数 `_on_handle_order` 里 `order.commit()` 正常保留，差别正在臂尾是否 `break`。

### B3 · 异常清理尾声按出口路径复制，产物只留一份 → 属既有异常布局族

锚点：`IQEngine/plugins/plugin_system_risk_calculation/function.pyc :: save_testds_to_json`
`orig=314 decomp=310`（−4）。`logs/dl_save_testds_to_json.txt` 末尾唯一删除回段 `delete orig[298:302]`：

```
o298 POP_EXCEPT | o299 POP_EXCEPT | o300 LOAD_CONST None | o301 RETURN_VALUE     L639
o302 POP_EXCEPT | o303 POP_EXCEPT | o304 LOAD_CONST None | o305 RETURN_VALUE     L639   ← 第二份
```
产物只有第一份（`d298..d301`，L367）。3.11 把 `finally` 内联到**每一条**离开 try 的路径上，
产物把两处清理尾声合成了一处 ⇒ 少 4 条。归 #39 异常处理布局族，不入本族判据。

### 已排除

* `IQCommon/manager/instance.pyc :: _init_config`（87→86）：`JUMP_FORWARD` 到共享 `return None` 与内联
  return 的布局差，且 `instance.pyc` 是 R16 记录在案的 5 个反例之一 —— 保护，不动。
* `IQEngine/plugins/plugin_system_matcher/matcher.pyc :: DefaultMatcher.match`（715→689，−26）：
  回段是 `replace orig[180:462] decomp[180:181]` **加** `insert decomp[428:687]` —— 259 条大块换位而非纯删除，
  difflib 无法对齐，与 B1/B2 均不同形，另立一项。
* `DefaultEventSource.events`（−24）、`Strategy.tick_worker_thread`（−21）：未逐条对齐，暂不归因。

## 二、与承重件的关系（落地前必读）

* `project-r16-lead-sink-collapse`：sink 臂归并过度触发但承重，整块删除实测 improved=8 / **broken=5**。
  B1 的判据不碰 `_if_arm_is_sink`，只碰「臂内条件块被另一区域的 elif 归属吞掉」这一条，二者不同源。
* R25-A（`_r25_fe_merge`，`region_analyzer.py` ≈L19127-19170）处理的是「链的 `final_else` 候选被链内块
  条件跳入 ⇒ 它是 post-statement merge，降格」。本例 B374 是 `final_else` **表头**且表内还有它的 then 臂与
  merge，R25-A 显式跳过条件块前驱，故不覆盖本形状 —— 是本判据的补半而非重复。
* 生成侧：L11145-11147 的「入口在他人 `elif_conditions` ⇒ 发射 `[]`」守卫**已实测与本缺陷无关**
  （见 B1 的否证段），不要在那里落地。分析侧候选改动点仍在 `_build_elif_region` 里
  `elif_info = _check_elif_chain(block, else_blocks, merge)` 之后（R25-A 同处），
  但落地前先测出条件块在哪一步消失。

