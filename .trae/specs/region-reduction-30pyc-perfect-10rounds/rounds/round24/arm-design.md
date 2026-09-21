# Round 24 — 靶子选择与门禁设计（arm design）

HEAD 起点 `3b6143c4`（Round 23 已落地并 push）。本轮全部诊断/选型在镜像核上做
（`D:/Temp/r24land/mirr/*`），`core/` 在门禁全绿前不写。

## 1. 目标池（实测，来源 `D:/Temp/r24map/logs/official_defects.jsonl`）

40 个 partial 文件、111 个官方不匹配函数、Σdeficit 113；其中 **16 个文件 deficit=1**。
最便宜的九个 deficit-1 锚点（按官方 `true_diffs` 升序，`probes/batt24.py` 实测；
head-vs-head 对照跑 → SAME=9、产物零变化，说明该读数不是噪声）：

| true_diffs | 文件 | 函数 | orig/decomp | jump_diffs | 首个差异 |
|---|---|---|---|---|---|
| 8 | IQEngine/data/data_proxy.pyc | get_bar | 86/86 | 3 | LOAD_FAST self vs LOAD_CONST None |
| 8 | …/plugin_system_risk_calculation/function.pyc | save_testds_to_json | 314/310 | 19 | POP_EXCEPT vs RERAISE |
| 14 | IQEngine/api/api_base.pyc | cancel_order | 60/61 | 1 | LOAD_FAST engine vs JUMP_FORWARD 452 |
| 14 | fly/common/flytools.pyc | acquire | 88/85 | 2 | RAISE_VARARGS vs JUMP_FORWARD |
| 19 | …/plugin_fly_data/__init__.pyc | _on_before_trading_start_trading_thread | 62/62 | 2 | LOAD_FAST order vs JUMP_FORWARD 364 |
| 19 | fly/dumpload/load_daily.pyc | `<module>` | 913/913 | 1 | JUMP_FORWARD 2478 vs PUSH_NULL |
| 23 | fly/common/custom_tools.pyc | memory_handler | 65/71 | 1 | LOAD_GLOBAL float vs LOAD_CONST GiB |
| 34 | …/plugin_system_persist/__init__.pyc | can_resume_strategy | 89/57 | 0 | LOAD_FAST persist_meta vs LOAD_CONST False |
| 37 | IQCommon/manager/instance.pyc | _init_config | 86/84 | 1 | LOAD_CONST None vs PUSH_EXC_INFO |

## 2. 族划分（为「最大翻转集 / 最小触发面」选型）

* **纯换位（长度相等 `orig == decomp`）**：10 个函数 / 10 个文件；其中 3 个文件的**全部**
  缺陷都是等长型 ⇒ 单点修复即可翻转文件：`data_proxy.get_bar`(t=8)、
  `plugin_fly_data/__init__._on_before_trading_start_trading_thread`(t=19)、
  `load_daily.<module>`(t=19)。其余：`utils.load_yaml 55/55`、`fly/logger.write_logging_thread 113/113`、
  `scheduler.get_checked_time 106/106`、`graph._process_task_queue 378/378`、
  `trade_live_broker.after_trading_cancel_order 155/155`、`real_quote.get_real_L2_data 359/359`、
  `fileio_utils.write 637/637`。
* **「过早收尾」签名**（`orig LOAD_* vs decomp LOAD_CONST None`）只有 3 个函数，且其中两个
  首差之后还有更大破坏 ⇒ 该签名**不构成一族**（否证了 Round 23 移交清单的暗示）。
* **异常布局族**（POP_EXCEPT/RERAISE 次序）、**整块丢失族**（−21..−32）、
  **过量发射族**（`check_before_trading 243/254`、`decrypt_database_url 295/324`）各自独立。

## 3. 本轮开出的诊断线与结论

* **线 A（多余无条件跳转 / 块次序）**：以 `data_proxy.get_bar` 为最清晰见证 ——
  对齐差显示 orig 76-83 的 `else: return BarData(…)` 尾块与 orig 84-85 的 `return None` 尾块
  在产物里**整体换位**，3 个 jump_diffs 正是随之重接的 `POP_JUMP_FORWARD_IF_NONE` 目标
  （orig 指 574、decomp 指 582）。据此提出的候选在全量触发面上实测
  **better=2 / equal=8 / worse=14，并打坏 11 个当时已 ok 的文件** ⇒ 否证，不落地。
* **线 C（值丢弃 / 链式比较三元头）**：根因是
  `region_analyzer.can_be_ternary_header` 在 `chained_compare_blocks` 非空时**一律**返回 False，
  于是「if 区域的入口块本身就是三元头」这一同层情形被降级成语句，
  赋值语句整体丢失（HEAD 产物里 `data_count = …` 消失，名字从未被重绑 = 语义缺陷）。
  这条判据与 Round 22/23 的「同层」路线同族，产出本轮落地候选 **R24-A**（见 `fixes.md`）。
* 线 B/D/E/F/G 的诊断代理都在 150 轮上限终止且未写 `ANALYSIS.md`：线 A/C 的结论由编排方从
  on-disk 工件（`jump/logs/abreport.txt`、`poptop/logs/case_ab.txt`、`poptop/probes/risk1.json`）恢复；
  B/D/E/F/G **本轮未收口**，作为 Round 25 入口（任务 #39/#41/#42/#43/#44）。

## 4. 门禁设计（先定门禁，再动核）

主门禁 = **Round 24 电池** `test_repros/round24_cc_ternary/run_all.py`，五道闸：

* **G0** 语料锚点 `real_quote.pyc` 官方 matched 上升（非空转证明）
* **G1** 每个 `PRED_R24A_FIX` 形状：旧核 FAIL → 新核 OK
* **G2** 每个 `CONTROL` 形状：两核都 OK
* **G3** 任何形状都不允许「旧核 OK → 新核 FAIL」
* **G4** 每个 `CONTROL`/`PRED_R24A_STABLE` 形状：**产物 sha256 逐字节相同**

`PRED_R24A_STABLE` 只承诺字节相同、不承诺 OK —— 电池里 b03/c04/c06 三个形状在 HEAD 上就因
**另一族既有缺陷**而 FAIL（实测写在每个文件的 `ACTUAL-HEAD` 行），它们的价值是证明 R24-A
不触及、也不恶化这些形状。把「必须 OK」写进这类用例等于谎报。

副门禁（顺序执行，全部在落地字节上复跑）：

1. 全量 402 文件**官方臂** A/B（`probes/r24h.py`，按产物 sha256 计数）—— 这是「触发面/爆炸半径」
   的硬读数：本轮预期且实测**只有 2/402 产物变化、0 个当时已 ok 文件被改动**。
2. 语料级**严格臂**（`D:/Temp/r23fix/probes/r23_sweep.py`，`Σsad` + 按 `textlen` 的产物变化数）。
3. Round 23 电池对 landed 核复跑：`broken=0`。
4. 靶子 `single`（真尺，逐函数）+ `quotation.pyc` 零副作用。
5. `batch --index pyc_index.json --all --round 24` → `stats`（对外只发布本轮 `stats` 读数）。

**为什么官方尺优先、严格尺只作同向旁证**：R24-A 恢复被丢指令，`Σ|orig−decomp|` 完全可能
反向上升（Round 23 的教训：以 Σ|Δ| 作主门禁会直接否决正确修复）。本轮实测两尺**同向**
（real_quote 严格 bad 8→7、Σ|Δ| 10→9），因此不存在 veto 冲突 —— 这个读数是本轮的加分项，
不是主判据。

## 5. 复现构造的反面教训（写下来免得下轮重踩）

从**产物源码**回推的 6 个 `.py` 形状（`D:/Temp/r24land/repro/t1..t6`）在 HEAD 镜核下全部
官方 **2/2 matched** —— 回推源码重编译后的块布局与语料 pyc 不同，换位不能复现。
⇒ 换位族的最小复现必须从**字节码布局**构造（两个尾块分别是不同嵌套层条件的 else 目标），
不能从产物文本构造。

配套的「尺盲」实例：`t1`/`t3` 产物里含明显错误的死代码
（`return self.BarData(...)` 之后紧跟 `return None`），官方尺仍判 2/2 matched，
因为发射的指令序列不变 ⇒ 「官方 ok」不等于产物良构，`.py` 形状电池不被官方臂替代。
