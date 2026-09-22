# Round 32 OUTCOME —— R32-C 落地：`POP_TOP` 是语句终止符，不是填充指令（推导式前导扫描器与调用方同层一致）

基线 = 落地字节 `dca5bbff`（Round 31 R31-C 之后）。本轮发货判据 R32-C，落地于第三个核文件
`core/cfg/comprehension_generator.py:621`（`+13 / -1` 行，核 sha `fa43dbc9e878eeacbfe0`，与实测镜像
`mirr_c/core/cfg/comprehension_generator.py` 逐字节相同）。函数级净收益 `+2`：
`IQCommon/utils.pyc :: load_ini`（`18/13` → matched）与
`IQCommon/strategy/wizard_quant_api.pyc :: get_strategy_finance_factor_info`（`28/18` → matched）。

## 一、目标池与三条诊断线（均实测）

`logs/pool32.txt` 首行直接读自 Round 31 G6 回写的索引，不转述：

```
baseline(landed round31 index, HEAD dca5bbff): files 402 partial 31 sum_deficit 103 deficit1 7
```

七个 deficit-1 文件在落地核上逐个 `single` 一手复测（`logs/landed_d1.txt`，七条全在）；另外把 13 个
deficit-2 文件同尺读了一遍（`logs/landed_d2.txt`），因为本轮假设的形状是「一条语句整条消失」，它在
deficit-2 一侧更常见。三条线的取舍（细节见 `arm-design.md` 第二、六节）：

* **线 A（只诊断代理，候选与归因均不可沿用）**：`risk_calculation/function.pyc ::
  save_testds_to_json 314/310` 的「缺失的重复清理尾声」。代理报称跑了全 402 sha A/B
  （`SAME=379 IMPROVED=0 REGRESSION=1 MOVED=22`），但它私有目录里**没有任何 402 产物**；它给出的
  「真实根因＝发射位点未置位既有标志」点名的两个符号在 `core/` 全树 grep **零命中**。⇒ 数字与名词都
  不进入记录，该形状回到未诊断状态。
* **线 B（只诊断代理，因果归因被编排方否证）**：`strategy.pyc :: tick_worker_thread 268/247`。它把
  责任归到 Round 31 落地的 R31-C「过火」，被 Round 31 归档 A/B（`strategy.pyc` 为 400 个 SAME 之一）
  与该读数在 Round 30 落地核上就已存在两条事实否证；其 `oauth2.pyc 71/72` 亦与实测 `11/11` 冲突。
* **线 C（取，本轮发货）**：编排方自己从 deficit-2 读数里挑出 `IQCommon/utils.pyc :: load_ini`，
  块级 hunk ＋ 逐条指令转储一手重建后定位到本判据。理由：① 第一个合成见证就在落地核上失败（G0 立即
  可得），CONTROL 同次运行保持 matched；② 判据是**补回一条结构上已存在的语句**，不引入新的形状识别；
  ③ 命中面在全量 A/B 实测后才发货。

## 二、判据 R32-C（原则 1 块 = 前导语句 + 尾终止 · 两侧同层一致）

一句话：**推导式前导语句扫描器不得把 `POP_TOP` 当噪声滤掉 —— 它是「栈上的值被丢弃」的语句终止符；
遇到它就闭合此前累积的栈上表达式并作为一条 `Expr` 语句发射。**

根因是**同一文件内两处对同一 op 的层级不一致**：调用方 `region_ast_generator.py:43514` 一带（其自身
终止判据 `:273-278`）把 `pre_comp_instrs` 末尾的 `STORE / POP_TOP / IMPORT` 认作语句边界，而被调方
`_generate_pre_comp_stmts` 的扫描循环 `:621-623` 把 `POP_TOP` 与 `RESUME / NOP / CACHE / PUSH_NULL`
并列 `continue` 掉 ⇒ 累积的调用栈永不闭合，`open(...).read()` 这类「值被丢弃的表达式语句」在「同块
还构造推导式」时整条消失（`load_ini` 单块 `−5`，`jump_diffs=0`）。归约方式：只在 `current_instrs`
非空且重建成功时发射；为空时控制流与既有行为逐字节相同（即「该行本就没有值被丢弃」）。判据只读
opname 类与累积段这一局部结构状态，不读名字／常量／绝对偏移／条数／函数名。

## 三、门禁（严格串行；原始日志全在 `logs/`）

| 门禁 | 读数 | 日志 |
|---|---|---|
| G0 合成见证（首件 5 函数） | 落地核 `7/10`（`w1 17/12 j0`、`w2 17/12 j0`、`w3 19/14 j0`）→ 发货核 `10/10` | `g0_head.log.txt` / `g0_c.log.txt` |
| G0 扩样（10 函数） | 落地核 `12/17`（`w1..w5` 全部 `j0`）→ 发货核 `17/17`；5 条 CONTROL 两把核下逐字节同 | `rp_head.log.txt` / `rp_c.log.txt` |
| G0 靶子＋CONTROL | `utils.pyc 20/22 → 21/22`；CONTROL `quotation.pyc 143/143`、`oauth2.pyc 11/11` 两把核 `SAME` | `g0_head.jsonl` / `g0_c.jsonl` |
| G2′ 上一轮 38 合成复现 | `{"SAME": 38, "IMPROVED": 0, "REGRESSION": 0, "MOVED": 0, "other": 0}` | `g2prime_38.txt` |
| G3 承重锚点 100（Round 31 要求的 `anchors100.txt`） | `{"SAME": 100, "IMPROVED": 0, "REGRESSION": 0, "MOVED": 0, "other": 0}` | `g3_100.txt` |
| G4 全 402 A/B（sha 优先，发货判据） | `SAME=400 IMPROVED=2 REGRESSION=0 MOVED=0 ERR=0`，`files fully matched: a=371 b=371` | `g4_ab402_sha.txt` |
| G4-d1 七个 deficit-1 文件 | `SAME=7 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（本判据与七个靶子无交集） | `g4d1_d1.txt` |
| G4′ 严格尺逐个变化产物 | `utils.pyc 24/26 σ2 Σ7 → 25/26 σ1 Σ2`；`wizard_quant_api.pyc 49/56 σ7 Σ22 → 50/56 σ6 Σ12` | `g4prime_utils.txt` / `g4prime_wizard.txt` |
| G5 `single` 两靶＋三 canary＋三残余 | `utils 21/22`、`wizard 49/53`；`flytools 65/65`、`quotation 143/143`、`oauth2 11/11` 全保持；残余 `strategy 23/24`、`matcher 16/17`、`default_event_source 13/14` 逐条同形 | `g5_single.txt` |
| G6 `batch --index pyc_index.json --all --round 32` | 末条 `[402/402]`、`index written back` 恰 1 次、崩溃标记 0 行、统计块完整 | `batch_all32.txt` |
| G7 `stats` | `total_pyc 402 / verified_pyc 402 / ok_pyc 371 / partial_pyc 31 / failed_pyc 0 / total_functions 5746 / matched_functions 5645 / cumulative_match_rate 98.24%` | `stats32.txt` |

## 四、唯一产物变化的逐项交代

`logs/index_delta32.txt`：402 条全部被重打 round 戳 `31 → 32`，真实字段变化恰 2 条 ——
`IQCommon/utils.pyc`（`matched_functions 20 → 21`、`bytecode_match_rate 0.9090909090909091 →
0.9545454545454546`）与 `IQCommon/strategy/wizard_quant_api.pyc`（`48 → 49`、`0.9056603773584906 →
0.9245283018867925`）；两者 `decompile_status` 仍为 `partial`（各自还差 1／4 个函数）。

被改的跟踪产物恰两个，且都与实测镜像 `build_c` 产物逐字节相同（`logs/products_sha.txt`）：

1. `site-packages/IQCommon/utilsOK.py`（sha16 `44cb899bf07e0197`，183 行）—— 补回 `load_ini` 里
   `open(...).read()` 一类的丢弃值表达式语句后靶子 matched。
2. `site-packages/IQCommon/strategy/wizard_quant_apiOK.py`（sha16 `8081d9342d523bc5`，771 行）——
   `get_strategy_finance_factor_info` 同形收口。

本轮 `MOVED=0`：除这两处外全 402 文件产物字节不变，故无须「ok 文件文本变化」登记。

## 五、方法论收获

1. **代理报告里的符号名必须先 grep 再入库**：本轮线 A 交回的「接线缺失根因」点名两个标志，`core/`
   全树零命中，其 402 读数也没有对应产物。教训固化为本轮起的硬规矩：代理给出的**每一个**要写进记录的
   标识符（函数名、变量名、行号、A/B tally）都要由编排方 grep 或重跑一次；否则该线只留作线索，不进
   移交清单。
2. **「同层一致」也包括同一文件内调用方与被调方的自洽**：本轮根因不是跨文件，而是同一模块里「谁是语句
   边界」的两套答案。以后审噪声过滤表时，与它的**调用方终止判据**成对读，比单看过滤器本身更有效。
3. **`只删不增` 不是教条，但「增」必须是补回结构上已存在之物**：判据发射的那条 `Expr` 在字节码里本就有
   `POP_TOP` 作为终止证据；配合「累积段为空则逐字节同形」的守卫，G4 得到本轮（也是全程序迄今）最干净的
   A/B —— 零附带文本变化。
4. **假设形状要在两侧的池子里都量一遍**：`load_ini` 在 deficit-2 组，而七个 deficit-1 靶子里该形状
   零命中（`G4-d1 SAME=7`）。因此本轮明确不声称触及 Round 31 移交的任何一个靶子。

## 六、残余与移交（Round 33 目标池，逐条带本轮读数）

* `IQCommon/utils.pyc :: load_yaml 55/55 jump_diffs=0 true_diffs=32`（等长错位，
  `first_diff index=22 LOAD_FAST(loader) vs POP_TOP`）—— 该文件 `21/22` 的唯一 blocker，与本轮判据
  不同形状（本轮修的是「少一条语句」，此处是「同一条语句的落点错位」）。
* `wizard_quant_api.pyc` 仍 4 个 unmatched：`calculate_di 75/73 j0 t45`、`params_analysis 133/126 j1
t117`、`region_mean_desicion 50/48 j2 t2`、`wizard_quant_check_limit 91/90 j2 t10`（四条均为本轮之前的
  既有项，本轮只把该文件从 `48/53` 抬到 `49/53`）。
* `risk_calculation/function.pyc :: save_testds_to_json 314/310`（该文件即 `14/15`，本轮 `G4-d1
  SAME=7` 未触及它）—— 线 A 的形状**仍未诊断**：Round 33 必须从落地字节自己重建 hunk／块级证据，不得
  沿用其符号名与 tally。它的结构探针原样存于 `logs/A-p13_pred.log.txt`、候选 spec 存于
  `logs/A-candidate-spec.json`，仅供参照。
* `strategy.pyc :: tick_worker_thread 268/247`、`matcher :: match 713/689`、`events 510/508 j2`、
  `quote.pyc 67/81`、`instance.pyc :: _init_config 86/84`（R16 J1 在册反例，受保护）、
  `decrypt_database_url 295/324`（过量发射侧）。
* `#61`（R30-B3 ＋ 合成见证 `r29x_01 <module> 142/138`）继续挂起。
* 七个 deficit-1 文件本轮未触及（`G4-d1 SAME=7`），下一轮目标池须在落地字节上重测。
* 锚点新要求：Round 33 电池 = `anchors102.txt`（`anchors100.txt` ＋ 本轮两件合成件
  `r32c_witness.pyc`、`r32c_repro.pyc`，二者各自内嵌 CONTROL）。落地核上必须读到 `witness 10/10`、
  `repro 17/17`；此前 G2′ 那 38 件在落地核上本就失败的，重跑仍须失败同形。合成件重生成时
  `py_compile` 必须显式给 `cfile`，因为电池读的是同目录兄弟 `.pyc`。
