# FIX T12-09 — 认领豁免 + 已发射台账：实测「 fires 而不翻正」，已逐字节撤回

票号 **T12-09**（承接 `rounds/round11/DIAG_B153_CLOCK_WORKER_REDISPATCH_FALSIFIED.md` §3 的
指名要求：先把「发过语句但只登记块、不登记区域」那一处记进可判别集合，再谈重派发）。
靶文件 `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
（12/13，唯一失败单元 `<module>.RealtimeEventSource.clock_worker` ⇒ 整文件翻转候选）。

## 1. 改动内容（候选字节 `bb23138a3b365641`，基线 `971df5e2c9cd7d0a`）

两处新构造，三个消费点，不留第二套口径（rules.md §1.5 C1/C3）：

| 位置（候选字节行号） | 内容 |
|---|---|
| `:3978` `_r164_note_emitted(region)` | 把区域的 `entry.start_offset` 记入 `self._emitted_entry_offsets` |
| `:25228`（唯一调用处） | `if _nr_ast:` 之后才记账 —— 即「真的产出了语句」之后，不是 `try/finally` 里 |
| `:3988` `_r169_claimable_leftover(block)` | 唯一豁免判据：块是**某个区域的 entry** 且该 entry 不在已发射台账里 ⇒ 返回 False（不认领） |
| `:21216/21222`、`:21249/21255` | `_if_generate_normal` 的 or-elif 修复分支对 `region.then_blocks` / `region.else_blocks` 的全量认领各加一条豁免 |
| `:25264` | `_process_if_blocks` 嵌套区域认领循环加同一条豁免 |

t1218（重绑定免疫的类属性写栈探针）证明 `:21200/:21202`（现 21216/21222）才是 **最先** 写
`generated_blocks` 的地方，只在 `:25235`（现 25264）加豁免的 T12-05/06/08 因此全程无效。

## 2. 镜像逐文件实测（判据 `scripts/pyc_verify.py single`）

| 文件 | 产物字节 | 单元读数 |
|---|---|---|
| realtime_event_source | 20555 → **21692**（DIFF） | **12/13**（未翻正） |
| quotation | 182759 = SAME_as_HEAD | 153/153 |
| handlers | 9093 = SAME_as_HEAD | 29/30 |
| wizard_quant_api | 34472 = SAME_as_HEAD | 55/58 |

hunk 剖面（`D:/Temp/r138/hunk138.py` 口径）：`delete orig[1179:1289]=110` 仍在**原位**缺失，
`insert prod[1260:1323]=63` 出现在 **@8448**，另有 `delete orig[949:966]=17`（搬位块）。
⇒ 台账确实兑现了约 61 条指令的回收，且 402 文件零连带；但这 63 条落在了错误的槽位。

## 3. 全量门（label 12，链日志 `D:/Temp/r10gate/gate_chain12_1003.log`）

严格串行 regen → verify → report → checks → residual：

- regen `ok=402 bad=0`（应 402/0）
- `[units] 6580/6617 -> 6580/6617 (99.4408%)  [files] 387 -> 387`
- `[gates] 文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=0`
- checks：quotation `153/153`、small34 `units_success 1531 / success 19`（与 round11 同读数）、
  selfcheck OK（常量/极性变异各抓 1/153）、pytest `2 failed, 280 passed, 2 xpassed`
  （两条名为红的用例与封存基线一致 ⇒ **零新增失败**）
- residual：15 文件 / 37 单元，`UNREGISTERED 行数=0`

## 4. 裁决与处置

**fires without flips ⇒ 不落地。** 按本役既定规则（工单以实测单元翻正受理，不以判据命中受理），
候选已**逐字节撤回**：

- `cp D:/Temp/r141/pre_t1209_generator.py core/cfg/region_ast_generator.py`
  ⇒ sha256[:16] `971df5e2c9cd7d0a`（= HEAD blob），`py_compile` OK，
  `grep -c "_r169_claimable_leftover|_r164_note_emitted"` = **0**，`git status --porcelain -- core/` = **0 行**
- 候选归档为共要件 `D:/Temp/r141/t1209_candidate_generator_bb23138a.py`（sha 已核）
- 唯一漂移产物 `realtime_event_sourceOK.py` 用撤回后的代码**删除重生成** ⇒ 20555 字节，
  `git status --porcelain -- site-packages/` = **0 行**（工作树重新与 HEAD 代码一致）

## 5. 本票买到的信息（下一票的前提，全部是可复核的事实）

以下读数来自**同构建自证惰性**的派发探针（`D:/Temp/r141/t1210_probe_generator.py`，
在候选字节上运行；A/B 两次产物**逐字节相同** ⇒ 读数可用；日志 `D:/Temp/r141/t1210c_1023.log`）：

1. 「发过语句的区域入口」是**可判别**的，且在 `:25228` 一处记账即可覆盖嵌套 IfRegion 派发路径；
   `_generated_regions`（`finally` 无条件按 id 写，见 `:5402`）与 `generated_blocks`（被各处认领抢先写）
   都答不了这个问题——这一点本票正面证实。
2. **本票原先写下的两条推断已被同一轮实测否掉，就地订正**：
   - ✗「就地派发从未发生」→ **错**。`[T1210-WALK] br=then arm@7582 in_gen_blk=False entry_gen=True nstmts=1`
     且 `[T1210-GEN] request IfRegion@7972 arm@7582 br=then` / `result empty=False kind=dict`
     ⇒ 块序走到 @7972 时它已被收集、被请求、并返回了**非空** If 节点。
   - ✗「`_generated_regions` 的 `finally` 无条件登记是拦路条件」→ **错**。同一条 `[T1210-COL]`
     读数为 `er=IfRegion [8166, 7972, 7980] contained=True er_gen=False er_ing=False gen_blk=False`
     ⇒ 包含性成立、id 排除也未命中，两道前置门都没拦。
3. 真正的残余形状在**产物文本**里（`diff` HEAD 20555 vs 候选 21692，唯一 hunk 在 clock_worker）：
   候选把 @7972 发成了**负极性的空臂**，语句体掉在 if 之后无条件执行——

```
-                    server_restart_do_before_type = '0'
+                                if persist_flag is False:      # 原文是 if persist_flag is not False:
+                                    pass                        # 臂体没有挂进来
+                                try:                            # 以下 63 条指令 = 原臂体，位置对但归属错
+                                    server_restart_do_before_type = str(self._engine.config.user.server_restart_not_do_before)
+                                except AttributeError:
+                                    server_restart_do_before_type = '0'
+                                if server_restart_do_before_type == '0':
+                                    pass                        # 同一「空臂」形第二次出现
+                                elif broker_persist is not None:
+                                    ...
+                                            if len(today_info) == 0:
+                                                pass            # 第三次
```

   同一单元 hunk 剖面（候选产物）：`len 1424/1372 net=+52 hunks=51 real=7 reloc=44 deleted=186 inserted=134`。
   即：**语句回来了（63 条）但归属没回来**——IfRegion@7972 的 If 节点臂体为空，
   真臂体由父臂走查当作普通块续发，因此单元仍红。
4. 下一票（T12-11）的宿主因此收窄到一处：`_generate_region(IfRegion@7972)` 产出的 If 节点里
   `then/else` 关联为何为空（以及 `is not False` 为何被写成 `is False`）。三处「空臂 pass」同形
   出现在同一产物内 ⇒ 先按**一形三例**取证再定判据，不得单例成说。
   注意 `if X: pass` + 体无条件后继在字节上是**两条边都落到体**，与原文 `true→体 / false→体后`
   不同 ⇒ 这正是残余 `reloc=44` 的来源之一。

