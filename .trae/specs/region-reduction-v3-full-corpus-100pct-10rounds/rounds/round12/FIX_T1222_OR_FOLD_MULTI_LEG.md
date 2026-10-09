# FIX T12-22 — or 折叠许可「disjunct 跨多条短路腿」：matcher 16/17 → **17/17**（实测）

票号 **T12-22**（承接 `FIX_T1221_ELIF_ARM_PREDS.md` §5 与 `DIAG_T1212_MATCHER_MERGE_AS_ENTRY.md`）。
靶文件 `IQEngine/plugins/plugin_system_matcher/matcher.pyc`（16/17，唯一失败单元
`<module>.DefaultMatcher.match` ⇒ **整文件翻转候选**）。
基线是 **T12-21 的收集侧钳制**（`analyzer_t1221_land.py`，`48b12e…`/`48b812e60ef52d27`）：
两票叠加才可能翻正，单票都不行（T12-21 单独 ⇒ 残余 4 hunk、16/17）。

## 1. 宿主与判据（全部是边/成员关系）

宿主：`core/cfg/region_ast_generator.py` `_if_generate_normal` 的闭包 `_fold_chain_consistent`
（HEAD 行 `:21501-21508`）与它唯一的判据函数 `_condition_chain_targets_consistent`（`:20126-20172`）。
该 `or` 判据要求 `FT(c_i) is c_{i+1}`，即**假定每个 disjunct 只有一条短路腿**。

实测（惰性探针 t1228/t1229，CLI-vs-CLI 证惰性，产物 13355 = 13355）：

```
region@1324 mode=or merge@1444 tested_blocks=[1372, 1432] targets=[(1444,1384), (1696,1444)]
链腿 (offset, JT, FT, 末指令)= (1372,1444,1384,POP_JUMP_FORWARD_IF_TRUE)
                               (1384,1696,1432,POP_JUMP_FORWARD_IF_FALSE)
                               (1432,1696,1444,POP_JUMP_FORWARD_IF_FALSE)
```

⇒ 第二 disjunct 在字节码里是**两条连续腿**：其子 IfRegion 的 `entry` 落在第一条腿（1384）、
`condition_block` 落在最后一条腿（1432），而父腿的 fall-through 命中的是 **entry**，
所以严格判据必然落空 —— 这是**判据的覆盖缺口**，不是结构不成立。

放宽判据（新方法 `_or_multi_leg_chain_consistent`，只在严格判据失败后被调用一次，唯一调用点）：
沿子区域自身的 `entry → condition_block` 落空边展开各 disjunct 的腿（不得离开该子区域的 `blocks`），
要求 ①展开后是一条连续落空链；②末腿的 fall-through 恰为 `region.merge_block`；
③首腿的跳转目标也是该 merge；④每条中间腿的跳转目标 ∈ {merge, 末腿的跳转目标}，
且至少有一条中间腿真的跳到末腿的目标。`op_type != 'or'` 一律 False ⇒ `and` 站在结构上不可能被翻转。

## 2. 施工与字节

| 文件 | 基线 sha | 落地铁 sha | 行数 | 标记 |
|---|---|---|---|---|
| `core/cfg/region_analyzer.py` | `e926a54f17753b33` | `48b812e60ef52d27` | 32570 → 32593 | `r12-t1221` ×1 |
| `core/cfg/region_ast_generator.py` | `971df5e2c9cd7d0a` | `851b0723732a2402` | 59112 → 59217（+97，其中新方法 89 行） | `_or_multi_leg_chain_consistent` ×4（定义 1 + 调用 1 + 文档 2） |

自审（脚本核对，不靠叙述）：新方法代码行里 **≥2 位数字出现 0 次** ⇒ 无硬编码偏移/指令计数（G4）；
`and` 模式早退 ⇒ `and` 负对照不可能被翻；一个判据函数、一个调用点（§1.5 C3 守卫封闭）。

## 3. 判决性读数（我自己在**新种的镜像**里复现，不是转述）

种法：复制仓库 `core bytecode parsers utils scripts pycdc.py`，先出 HEAD 产物，再装两票、逐文件比对。

```
HEAD   matcher 13255 a4e4980f31e5f46f  ->  [single] status=failure units=16/17 (94.12%)
落地后 matcher 13299 7f5ab1467621a033  ->  [single] status=success units=17/17 (100.00%)
```

hunk 剖面（`D:/Temp/r138/hunk138.py`）：HEAD `net=+10 hunks=25 real=1` → T12-21 后
`net=+0 hunks=4 real=0` → 本票后 **`hunks=1 real=0 reloc=1`**。
产物文本第 158 行变成 oracle 的那一条：

```
if order.asset.symbol[:3] == '300' and trading_date < gem_change_date or order.asset.symbol[:3] == '300' and stock_listed_date_str < gem_change_date:
```

**读数口径声明（不粉饰）**：残余的 `hunks=1`（@1322 `JUMP_FORWARD ->@2464` vs `->@3210`）
在同一工具下也出现在**已验证 17/17 的 oracle 文本** `D:/Temp/r138/m_or_full.py` 上，
即它是 hunk 对齐工具的搬移伪影，不是产物缺陷；判据以 `pyc_verify` 的 `status=success units=17/17` 为准。
不得把 `hunks=0` 写成本票的验收线——那条线本身是假的。

## 4. 连带控制（同一镜像，逐文件 base/after 比 sha）

quotation `302f449afc9245eb`、handlers `65badb9485d3b8f3`、wizard_quant_api `0f8ec52303f447fa`、
realtime_event_source `174e1174f28a669c`、klinedata `08e13ec9166f78fe`、trade_info_utils
`a8c8074a964d2a20`、real_quote `53052c9c412414dc`、IQData/api_base `3edfd391d0b8c2f7`、
IQEngine/api_base `e53bbe5b114031ba`、order_api `14a6a26334a3f09d`、trade_live_broker
`d6af28bf3086b2b3`、function×3、engine×2、logger/handlers —— 17 个产物 **全部 SAME**。
其中 4 个 or-型站在放宽下**主动拒绝**（`reg=570, 996, 992×2`，`strict=False relaxed=False`），
`@3432`（and 型负对照）两臂都仍被拒 ⇒ 放宽「生效但不滥」。

## 5. 一处对本票简述的否证（订正）

我在派发简述里写「`or` 模式少剥掉首项的 `not`，需要在 `:21539-21548` 补一次剥离」——
**实测否证**：`_flip_is_none_compare` 在不透明非 Compare 操作数上回落到 `_negate_expr`，
而 `_negate_expr` 对 `UnaryOp('not', …)` 就是剥壳，两处 or 装配点已经发出**未否定**的首 disjunct；
再加一次剥离等于把同一个判据复制两遍（违反「一处判定，多处复用」）。因此本票只改判据许可，不改装配。

## 6. 落地与门（本轮判决）

两票叠加后由 `gate_round.py 14 13` 全量门判：验收 = `翻正单元 ≥ 1`（matcher 整文件应为第一例）
且 `新增失败单元 = 0`，checks 四门须仍是 quotation 153/153、small34 `1531/19`、
selfcheck OK、七套件 `2 failed / 280 passed / 2 xpassed` 同名两红，
residual 表由 `residual_report.py` 重发且 `UNREGISTERED=0`。
链日志：`D:/Temp/r142/land14_*.log` + `D:/Temp/r10gate/gate_chain14_*.log`。
撤回备份：`D:/Temp/r142/pre_t122x_analyzer.py`、`D:/Temp/r142/pre_t122x_generator.py`。

**尚未验证（明列）**：402 全量重生成与逐单元比对（门在做）；pytest 七套件与 residual（门在做）；
超过 2 个 disjunct 的多腿链（判据故意拒绝）；`_all_negated` 与 De Morgan 分支（未触碰）；
以及本票对**其它文件**是否存在单元级增益（只有门能回答）。

门（label 14 vs 13）读数，逐字取自链日志 `D:/Temp/r10gate/gate_chain14_1230.log`：

```
[regen 合计] ok=402 bad=0（应 ok=402 bad=0）
dirty product count after regen (= blast radius vs committed products): 1
[units] 6580/6617 -> 6581/6617  (99.4559%)   [files] 387 -> 388
[gates] 文件级回退=0  UNIT_REGRESSIONS=0  新增失败单元=0  翻正单元=1
[quotation] rc=0 [single] status=success units=153/153 success_rate=100.00%
[small34] rc=0 "units_success": 1532, "success": 20,
[selfcheck] rc=0 [selfcheck] 自证：153/153 单元 Equal | [selfcheck] 变异「常量」抓到 1/153 单元 | [selfcheck] 变异「极性」抓到 1/153 单元 | [selfcheck] OK —— 判据可用
[pytest] rc=1 2 failed, 280 passed, 2 xpassed in 6.57s
单元 6581/6617 (99.4559%)  文件 388/402  残余文件 14 个  残余单元 36 条
UNREGISTERED 行数=0（应为 0）
### chain end 12:45:45
```