# FIX R13-01b — 单操作数 run 的混合链头放行：`bar.pyc` 84/85 → **85/85**

票号 **R13-01b**（`FIX_R1301_PAIR_JOIN.md` 的第二半；同一族的第二判据，另票记账，
不把 bar 记在 R13-01 账上）。靶 `IQEngine/core/bar.pyc`，唯一失败单元
`<module>.BarData._history_bars`（1 条 hunk：`POP_JUMP_FORWARD_IF_FALSE` @126 应落 `->@140`，
产物落 `->@304`）。

## 1. 拦路点（镜像内惰性自证探针，CLI-vs-CLI 同臂两次逐字节相同）

`region_analyzer.py` R54-A 门（种子字节 `:29179-29185`）条件 (5)：

```
SBRET start_block=@34[preds=[18,30]] _sb_last=POP_JUMP_FORWARD_IF_FALSE@126->140
 _r54_mixed=False _r54_k_shares_exit=False _r54_j=@140[preds=[34,128]] _r54_f=@128[preds=[34]]
 _r54_k=@206[preds=[128,140]] _r54_tj=@304 _r54_tf=@206[preds=[128,140]] _r54_f_ft=@140
```

bar 的第二 run **只有一个操作数** ⇒ 该门里 `K` 落到的是**语句体**而不是下一个操作数，
`_r54_k_shares_exit` 因此不成立 ⇒ 链头不被承认、walk 根本不开始（该调用点之后没有 APPEND/WALKEND）。
R13-01 的二入汇合放行覆盖不到它：R13-01 管的是「and→or 边界要不要收下一个候选」，
这里卡在更早的「这条混合链的链头要不要被承认」。

## 2. 判据（复用刚落地的 `_r1234_pair_join`，不新建第二口径）

链头在「第二 run 只有一个操作数」时同样承认，当且仅当两个二入汇合关系同时成立：
`J` 的前驱恰为 {链头 H, F}，且体块 `tf` 的前驱恰为 {F, J}
（`_r54_k is _r54_tf` 保证 `K` 就是那个体块）。全部是入边身份事实：无偏移、无指令计数、无名字（G4）。

```python
                            _r54_one_operand_run = bool(
                                _r54_k is _r54_tf
                                and self._r1234_pair_join(_r54_j, start_block, _r54_f)
                                and self._r1234_pair_join(_r54_tf, _r54_f, _r54_j))
...
                                and (_r54_k_shares_exit or _r54_one_operand_run))
```

识别期生效：它只让**既有**的深度回走在 `_sb_has_body` 计算之前跑起来，不重读区域、不改写已渲染块
（与「生成端折叠」那条被否的路线不同——那一条虽然也读到 11/11，但发生在臂渲染之后，
违反 rules.md 2.1/2.3，未采用）。

字节：`core/cfg/region_analyzer.py` `f396df179b76c144` → **`640d33a77dcb71c2`**（32623 → 32652 行，
+29：28 行注释 + 5 行代码 / 1 行改写；备份 `D:/Temp/r142/pre_r1301b_analyzer.py`；
交付件 `D:/Temp/r1301b/region_analyzer_LAND.py`，落地哈希一致即测量字节）。

## 3. 读数

镜像 A/B（21 产物，见 `D:/Temp/r1301b/log/`）：bar `84/85 → status=success units=85/85`，
其余 **20 个产物逐字节 SAME**（含 strategy_universe 11/11、matcher 17/17、quotation 153/153、
两个 handlers、两个 strategy、两个 engine、market_time/time_validator 等同族近邻）。

落地字节在仓库内复测（`D:/Temp/r142/land16_*.log`）：

```
bar.pyc               16951 c011103e61f98c1a  status=success units=85/85
strategy_universe.pyc  3787 890f3635c862eab3  status=success units=11/11
matcher.pyc           13299 7f5ab1467621a033  status=success units=17/17
```

bar 产物第 287 行成为 B134 §2.2 oracle 的形状：

```python
if engine.config.strategy.frequency == '1m' and frequency == '1d' or ExecutionContext.phase() == ExecutionPhase.BEFORE_TRADING_START:
```

## 4. 门（label 16 vs 15，链日志 `D:/Temp/r10gate/gate_chain16_*.log`）

判决数字由 `D:/Temp/r142/fill_gate16.py` 逐字回填（不手抄）。验收同前：
`翻正单元 ≥ 1 ∧ 新增失败单元 = 0` 且四门同读数；否则逐字节回滚
（`cp D:/Temp/r142/pre_r1301b_analyzer.py core/cfg/region_analyzer.py`）并按共要件留档。

## 5. 尚未验证（明列）

门以外的语料面未测；`@140` 处那条 W14 走链断点已定位但未证明「没有别的单元依赖它」；
新臂与异常边的交互未测（bar 的 H/F/J 都无异常边）；>1 操作数的第二 run 不在本判据内。

门（label 16 vs 15）读数，逐字取自链日志 `D:/Temp/r10gate/gate_chain16_1412.log`：

```
[regen 合计] ok=402 bad=0（应 ok=402 bad=0）
dirty product count after regen (= blast radius vs committed products): 1
[units] 6582/6617 -> 6583/6617  (99.4862%)   [files] 389 -> 390
[gates] 文件级回退=0  UNIT_REGRESSIONS=0  新增失败单元=0  翻正单元=1
[quotation] rc=0 [single] status=success units=153/153 success_rate=100.00%
[small34] rc=0 "units_success": 1534, "success": 22,
[selfcheck] rc=0 [selfcheck] 自证：153/153 单元 Equal | [selfcheck] 变异「常量」抓到 1/153 单元 | [selfcheck] 变异「极性」抓到 1/153 单元 | [selfcheck] OK —— 判据可用
[pytest] rc=1 2 failed, 280 passed, 2 xpassed in 3.95s
单元 6583/6617 (99.4862%)  文件 390/402  残余文件 12 个  残余单元 34 条
UNREGISTERED 行数=0（应为 0）
### chain end 14:24:32
```