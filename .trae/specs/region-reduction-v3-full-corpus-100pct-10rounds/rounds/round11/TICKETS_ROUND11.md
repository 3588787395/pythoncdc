# Round 11 派工队列（不复制读数，只登记「谁在跑 / 缺什么证据 / 谁能动哪一处」）

真相源纪律：本文件**不重述**残余单元数、文件数或逐单元名单——那些只存在于
`rounds/round10/RESIDUAL_R10.md`（由 `residual_report.py` 从八份分片报告直接生成）与
`rounds/round10/after/shard*_report.json`。此处若抄一份数字表，就成了第二真相源：
本 campaign 已多次因抄表把口径改乱（net vs 逐 hunk、首差 vs 机制、`argrepr` 假差）。
本文件只登记派工状态与宿主归属。

## 一、整文件只差 1 单元的翻正候选（宿主状态）

| 文件（残余读数见 RESIDUAL_R10.md） | 单元 | 登记机制 | 宿主/状态 |
|---|---|---|---|
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | `<module>.DefaultMatcher.match` | 两条独立丢弃通道（`:19324` merge 认领 ∧ `:54896-54921` 递延交接），三点齐修已证**层级对但单元不翻** | B132 已否证并留档；剩最后一里在 `IfRegion@2208` 子臂折叠（`is_first_five` 须走块出口而非 continue）——**待另案诊断**，禁再修同组三点 |
| `fly/dumpload/load_daily.pyc` | `<module>` | `#14` F1 面：`IfRegion(cond@740)` 的 `merge_block` 被解到整个 try 结构之外（`@2768`），真实汇合块 `@2478` 是 try 体内末条 | **B133 在飞**（镜像 `D:/Temp/r133/wt`）；宿主 `_compute_arm_level_join:3332-3349` 现由该票独占 |
| `IQCommon/util/trade_info_utils.pyc` | 4 条（含 `get_trade_status`） | `get_trade_status` = try 体尾 `break` 未发射（`_try_body_terminates_abnormally:11609-11610` 在 `self.regions` 未填充阶段读它，实测 n_regions=0）；其余 3 条属共用返回尾面 | `get_trade_status` **B133 在飞**（同票 case2）；余 3 条待 #15 后续票 |
| `IQCommon/logger/handlers.pyc` | `<module>.TWHThreadController._target` | 共用隐式尾声；**已证 G7/sink 面惰性**（该单元在 G4b 于 `:51799` 即 break，走不到 `:51806-51812`），真宿主在 `_loop_generate_while`（`@404` 从未被请求发射） | B127 已否证留档；**下一票须从 `_loop_generate_while` 的 else/出口消费面取证** |
| `IQEngine/core/bar.pyc` | `<module>.BarData._history_bars` | `#14` F2 纯落点 | **B134 在飞**（诊断） |
| `IQEngine/core/strategy/strategy_universe.pyc` | `<module>.StrategyUniverse._on_clear_de_listed` | `#14` F3 假臂语句挂错边 | **B134 在飞**（诊断） |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | `<module>.Strategy.tick_worker_thread` | ANCHOR 面（跳转须落在线锚 NOP） | 未派工；**注意 NOP 轴曾被整体否证**，须先证明该单元差确实只在锚点落点上（逐 hunk 打全），不得沿用旧断言 |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | `<module>.RealtimeEventSource.clock_worker` | 一个单元三种状态：110 指令体被跳 + 17 指令块**搬位**成 18 + 3 处目标差 | 未派工；**搬位那一面不得记成省略**（登记于 UNITMAP） |
| `IQData/api/api_base.pyc` | `<module>.get_history_df` | 曾被判「极性」，极性轴已整体否证；现按多指令 hunk 归 `#13` 压形/落点 | 未派工；须重新以身份判据取证，禁再用 `IF_TRUE↔IF_FALSE` 计数当机制 |

## 二、非翻正但推进单元的在册票

`#21` `<genexpr>` 下标操作数链（2 条，`COPY_AMBIG` 需先按 `co_consts` 次序定标）·
`#22` `order_api` 被吞条件语句 + and/or 三元操作数链（2 条，镜像对）·
`#23` 函数内 `from … import Y` 丢 `IMPORT_NAME+IMPORT_FROM`（4 处复制、前瞻窗不一致 `+3/+3/+4`，
另加 `_import_pending_store` 状态机一处；**修复须收敛为一个复用判据**，加宽常量即违反 §2/G4）·
`#24` f-string 字面碎片拼接外来标识符（1 条，普查 407 份产物仅 2 处命中且另一处是我自己正则漏 `】` 的假差）·
`#14` 其余落点/换位面（`kill_trade_process` 互换位、`etf_basket_order` 置换等）。

## 三、并发与施工规则（本轮已两次踩坑，写死在此）

1. **同一时刻只允许一个施工者改 `core/`**；其余施工一律在各自镜像（`D:/Temp/rNNN/wt`，
   先逐文件 sha256 对齐），交付**整份改后文件**而非 diff——镜像生成的 diff 在本仓 `git apply` 会报
   `corrupt patch at line 70`。装入序列固定：存原字节 → 整份复制 → `py_compile` → 标记 grep 计数 →
   目标单元 `single` 复验 → 零翻转即按 sha256 逐字节回滚。
2. 施工者改 `core/` 期间，**不得**同时派读 `core/` 行号的诊断票（锚点漂移已造成一次工单作废）。
3. 判据只用白名单事实（opcode／块末／后继与前驱身份／异常边／区域角色与成员／`generated_*` 写入时机）；
   禁计数、深度、绝对偏移、文件名与函数名特判；禁 G3 前缀新方法；触及方法的六项模板注释须与行为一致。
4. 任何修复只按**单元翻正名单**验收，不按守卫命中；零翻转不得记成绩，也不得为让复现臂变绿而放宽判据
   （最小样例常无判别力：B131 的 7 条臂全读 2/2）。
5. 门禁资源唯一：402 全量重生成由主代理跑 `bash /d/Temp/r10gate/gate_chain.sh`，
   且 `regen` 报 `bad>0` 时**先 stat 产物尺寸再读 report**（本轮 9 单元假回退即出自 99 字节残次产物）。

## 四、我于 04:24 直接实测的四个候选单元（差形分类，非台账转述）

仪器：stdlib-only（`dis` + `difflib`，CACHE 剔除、跳转目标写成 `->@off`、嵌套 code object 归一 `<co>`），
按**完整 qualname** 配对且断言副本唯一（`copies 1/1`）；产物取盘上现字节。
分类键：hunk 为 `replace` 且两侧长度相同且 opcode 序列相同 ⇒ **target-only**；否则 **content**；
content 里 `删+插 ≥4` ⇒ **big**（即 UNITMAP 的分类键）。

| 单元 | len orig/prod | hunks | target-only | content | big | 结论（对我原登记口径的更正） |
|---|---|---|---|---|---|---|
| `strategy.tick_worker_thread` | **294/294** | 4 | **4** | **0** | 0 | 全差皆同 opcode 仅目标不同 ⇒ **最干净的纯落点**，且是只差 1 单元的整文件。我此前登记的 ANCHOR 子形**未由本测量证实**：4 处目标差是否须落在线锚 NOP 上，须逐差再判，不得沿用旧标签 |
| `realtime_event_source.clock_worker` | 1442/1330 | 53 | 38 | **15** | 6 | 单元内并存省略与搬位：`delete orig[959:976]=17` 是 `if holiday_not_do_before == '0': self.event_queue.put(dt)…` 整块被吞；另有 `replace 1→3`（一条假边被拆成两条跳转）与 `7→1`。**多机制单单元**，不可一判据草率并案 |
| `api_base.get_history_df` | **1900/1900** | 20 | 15 | 5 | 5 | 长度相同但内容差真实存在：`5→1` 把 `time_count -= 1` 复合赋值压进跳转；`1→9` 把一条假边拆成嵌套测试；`orig 5→prod 5` 处 **`count > 0` 被发成 `0 < count`**（操作数顺序与极性同翻）。故「极性」不是独立轴（与 round 9 对极性轴的否证一致），此项应按**压形 + 比较子重排**取证 |
| `handlers.TWHThreadController._target` | 203/200 | 17 | 15 | 2 | **0** | 与 B127 的读数一致（少发一对 `LOAD_CONST None/RETURN_VALUE`，其余为该 4 字节沿跳转图的位移），且**无 ≥4 指令 hunk** ⇒ 与 clock_worker 那种大块省略不同面 |

注：本表只登记**分类**，不登记修复方案；具体宿主由在飞票 B133/B134/B136 与新增 B137 给出。
