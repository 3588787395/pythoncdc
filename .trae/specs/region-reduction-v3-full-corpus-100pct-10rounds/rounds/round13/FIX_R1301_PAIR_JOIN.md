# FIX R13-01 — 二入汇合放行：`strategy_universe.pyc` 10/11 → **11/11**（12 文件 A/B 零连带）

票号 **R13-01**（= round12 队列里的 T12-23/T12-24；靶与判据来自
`rounds/round11/DIAG_B134_TARGET_ONLY_LANDING.md` §2.1/§2.2/§3.1，那一份的 §4-§7 从未写完，
本文补上判决与施工）。靶文件 `IQEngine/core/strategy/strategy_universe.pyc`
（10/11，唯一失败单元 `<module>.StrategyUniverse._on_clear_de_listed` ⇒ 整文件翻转候选）；
同判据的第二靶 `IQEngine/core/bar.pyc`（84/85，唯一失败单元 `BarData._history_bars`）**本轮未翻**，
原因实测见 §4。

## 1. 拦路的那一行（实测，非推断）

`core/cfg/region_analyzer.py::_b1b_loop_body_run_continuation` 的情形 (1)（and→or 边界）：

```python
        if not _cur_true and _cand_true:
            # (1) and→or 边界：candidate 落空边汇聚到 current 假出口 Y（下一 run 头）
            return _cand_ft is _cur_tgt and _tgt_is_cond
```

`_tgt_is_cond` 要求汇合块 Y **自己**以正向条件跳转结尾。B134 与我方的读数一致表明两靶的 Y 都不是
条件测试块（`strategy_universe` Y=@156 只有一个后继；`bar` Y=@140 的后继是 [206,304]），于是链被拒 ⇒
外层 IfRegion 的 `merge_block`（**已经等于原始落点** 156 / 140）在尾巴附着时从不被读取，
产物把尾巴落到内层语句末（198 / 304）—— 正是那唯一一条 hunk。

## 2. 落地的判据（只读入边身份）

情形 (1) 增加第二个放行形：Y 的前驱**恰为**本对操作数块 `{cur, cand}`（纯二入汇合点，
结构上不可能是另一条语句的入口）。

```python
    def _r1234_pair_join(self, tgt, a, b):
        if tgt is None or a is None or b is None or a is b:
            return False
        preds = getattr(tgt, 'predecessors', None)
        if not preds:
            return False
        want = {a.start_offset, b.start_offset}
        got = set()
        for p in preds:
            off = getattr(p, 'start_offset', None)
            if off is None:
                return False
            got.add(off)
        return got == want
```

* G4 合规：只用前驱身份，无偏移常量、无指令计数、无名字门（脚本自审：新方法代码行内 ≥2 位数字 0 次）；
* C3 守卫封闭：`_r1234_pair_join` 全文只有 1 个定义 + 1 个调用点（标记命中 2）；
* 施工层合规：**分析端识别期**，不是生成端事后重排。
  上一轮一次同族尝试在生成端 `:21829` 折叠，确实也让 su 读到 11/11，但它发生在臂已渲染之后
  （回改子区域的块归属，违反 rules.md 2.1/2.3），故**未采用**，把同一判据搬回分析端后重测。

字节：`core/cfg/region_analyzer.py` `48b812e60ef52d27` → **`f396df179b76c144`**
（+30 行；备份 `D:/Temp/r142/pre_r1301_analyzer.py`；构建器 `D:/Temp/r142/t1235_build_land.py`
断言「落地文件的 4 条代码行与实测补丁逐条唯一相同」，因此 §3 的读数描述的就是落地字节）。

## 3. A/B 实测（12 文件；`D:/Temp/r142/t1234_pairjoin.py`，日志 `pj2_1318.log`）

```
BASE su 3806 c6cc05ab5fee6b97 10/11    ->  CAND su 3787 DIFF  status=success units=11/11 (100.00%)
BASE bar 0c175045e3b0a186 84/85        ->  CAND bar SAME 84/85
BASE m   7f5ab1467621a033 17/17        ->  CAND m   SAME 17/17
BASE q   302f449afc9245eb 153/153      ->  CAND q   SAME
BASE h   65badb9485d3b8f3 29/30        ->  CAND h   SAME
BASE w   0f8ec52303f447fa 55/58        ->  CAND w   SAME
BASE e   174e1174f28a669c 12/13        ->  CAND e   SAME
BASE k   08e13ec9166f78fe 62/64        ->  CAND k   SAME
BASE t   a8c8074a964d2a20 38/41        ->  CAND t   SAME
BASE st  a387e7e0f43443c3 26/27        ->  CAND st  SAME
BASE qt  ecbca274b41375b2 86/92        ->  CAND qt  SAME
BASE tlb 118/128                         ->  CAND tlb SAME
```

落地字节复测（仓库内，`land15_*.log`）：su `3787` 字节 sha `890f3635c862eab3` **11/11**，
matcher `17/17` 不变，quotation/handlers/realtime_event_source/bar 读数不变。
产物形状与 B134 §2.2 的 oracle 一致（`if not i or not X:` 一条测试，而非嵌套 if）。

## 4. 为什么 `bar` 没跟着翻（同一判据的第二形，实测边界）

`bar` 需要的是**三元混合链** `(A and B) or C`：链头 @34 的 and-run 之后再越过 or 边界，
它的 Y=@140 虽满足「前驱恰为 {34,128}」，但链的**后续成员**不再由情形 (1) 决定，
而是被 `:29983-29990` 的循环归属豁免与 `len(chain) < 2` 拒绝（`A4/A5` 读数：
`chain=[(46,'and')]` 一类）。⇒ 本票只买 su；bar 属**同族第二判据**，另开 R13-01b，
不得把 bar 记在本票账上。

## 5. 门与状态

全量门 label 15 vs 14 在跑（链日志 `D:/Temp/r10gate/gate_chain15_*.log`）。
验收：`翻正单元 ≥ 1 ∧ 新增失败单元 = 0` 且四门同读数；否则逐字节回滚
（`cp D:/Temp/r142/pre_r1301_analyzer.py core/cfg/region_analyzer.py`）并按共要件留档。
判决读数由 `D:/Temp/r142/fill_gate15.py` 从链日志逐字取回填进本文末节，不手抄。
