# Round 63 batch 2 — NONE.md（本批无可通过见证测量的 spec）

分配：klinedata.pyc(10) / real_quote.pyc(10) / scheduler.pyc(13)。
基线复测（`dump/landed.jsonl`）与 FACTS.md 完全一致；候选臂 `dump/c1.jsonl`
经 `cmp_arms.py` 比对：**SAME=3 / IMPROVED=0 / REGRESSION=0，三个文件产物字节完全不变。**

## 唯一提交的候选已被证伪（不落地）
`FALSIFIED_cand_chainmerge_armowned.json`（改 `core/cfg/region_analyzer.py`
`_build_elif_region` L19621-19636 的「单臂后继 → merge 候选」支路，
按区域归约原则 2 剔除属于任一臂的候选块）。

- 区域层**有效**：`dtrace2.py ... d1_elif_try c1` 显示
  `IfRegion entry=0 merge=252 -> merge=None`。
- 输出层**完全 inert**：`drun.py c1` 里 d1 的 `return A<cur<B or C<cur<D` 仍丢失；
  三支目标 pyc 的逐函数元组纹丝不动。
- ⇒ 「外层 elif 链把臂内 BoolOp 汇合块误认为链 merge」不是语句丢失的生效机制。**已证伪。**

## 另两条已证伪结论
1. **Scheduler.get_checked_time 不可攻**：原始布局是 CPython 3.11 `_PyCompile_OptimizeCfg`
   的落块产物。探针实测（ANALYSIS.md §1 表格）：语义正确的源码形状 A 给出不同布局；
   能复现布局的形状 B 会改变异常表（把 `divmod` 纳入内层 except 的保护范围，语义改变）。
   不属于区域归约缺陷。
2. **try/except 不是必要条件**：探针 d2（elif 臂内无 try）同样错位（return 被抬到 if/elif 链
   之外），d4（函数顶层，有 try）正常。⇒ 不要把靶心放在 try 侧。

## 下一步判据方向（实测指向发射侧）
生效条件（c1..d8 探针矩阵，ANALYSIS.md §2）= **「含链式比较的 BoolOp 表达式语句」落在
条件臂（if/elif 任一臂）内**；顶层正常。关键线索：
- 产物里该语句**不是被省略在原地，而是整块脱离臂**（d2 直接把它放到 if 链之后），
  说明 `_if_generate_full_elif_chain` 逐臂取语句时把「归属嵌套表达式子区域
  （BoolOpRegion entry=220 / merge=252；链式 IfRegion entry=190→220、222→252）」的
  尾部块截断在臂外，之后这些块被子区域标记为已生成却从未发射 ⇒ 彻底丢失（d1、d6、d8），
  或被挂到父层（d2）。d7（`r = 链式or链式` 后 `return r`）赋值整条消失，佐证
  「丢失的是表达式语句宿主块，与 Return 语法无关」。
- 因此应比对 **臂内发射路径 vs 顶层序列路径**（d4 走通的那条）对
  「子区域 merge_block 同时是本条语句的落点块」的处理差异，
  在 `core/cfg/region_ast_generator.py` 的 elif 链臂生成处收窄既有归属判据，
  而不是在 `region_analyzer.py` 的 merge 求解上继续加条件。

## 复现与测量（全部非侵入）
```
cd D:/Temp/opencode/r63gate/diag2
python -X utf8 drun.py  landed F:/Downloads/pythoncdc-main/test_repros/round63_b2/probe_r63b2_cases2.pyc
python -X utf8 dreg.py   F:/Downloads/pythoncdc-main/test_repros/round63_b2/probe_r63b2_cases2.pyc d1_elif_try
python -X utf8 dtrace2.py F:/Downloads/pythoncdc-main/test_repros/round63_b2/probe_r63b2_cases2.pyc d1_elif_try <arm>
python -X utf8 dside.py  F:/Downloads/pythoncdc-main/site-packages/IQEngine/utils/scheduler.pyc \
       Scheduler.run_interval_trade.is_run_interval_time_now build_landed/IQEngine__utils__schedulerOK.py 20 90
```
合成复现（仓库内，仅本批允许目录）：
`test_repros/round63_b2/{probe_r63b2_cases,probe_r63b2_cases2,repro_r63b2_tail_cmp_return}.{py,pyc}`
