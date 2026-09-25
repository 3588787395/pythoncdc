# Round 65 · diag4 · 任务书（只读诊断，禁止落地）

## 0. 你是谁、交付什么
你是本轮 5 个并行诊断代理之一。你**只诊断、只测量、只写候选 spec**；落地与门禁由主代理
集中验证后执行。你的交付物全部放在 `D:/Temp/opencode/r65gate/diag4` 里：
1. `specs/*.json` —— 候选编辑（`{{"file": "core/cfg/region_ast_generator.py" 或 "core/cfg/region_analyzer.py",
   "edits": [{{"anchor": …, "repl": …}}]}}`，anchor/repl 用 **LF 归一**文本，anchor 在落地字节里必须**恰好出现 1 次**）；
2. `FACTS.md` —— 每个臂的实测读数（官方 `bytecode_diff` 元组 + 电池 + canary），可复放命令；
3. `ANALYSIS.md` —— 机制结论：哪个区域模式、为什么归约失败、判据的同层次结构身份是什么。

## 1. 硬约束（违反即作废）
- **禁止修改仓库任何文件**：不许 `git` 写、不许 `single`、不许 `batch`、不许 `_r13_gate.py`、
  不许 `land*`/`mbuild`/`mkfinal`。仓库工作树的 `core/cfg/region_ast_generator.py` 在 R64 被一个
  诊断代理重排成纯 LF 过（EVIDENCE §B 事故），**再发生一次本轮就废了**。
- 每条命令 **< 300 秒**；长任务自己分片（`h62.py run --nshard/--shard`）。
- 不许设置 `PYTHONIOENCODING`；一律 `python -X utf8`。
- 判据必须是**区域归约算法内**的、同层次结构身份（entry/merge_block/parent/then_blocks/
  body_blocks、块的控制流角色、指令模式）。**禁止**按函数名/文件名/偏移阈值/字面量计数的
  跨区域跨层次启发式；禁止破坏嵌套区域作为单一抽象节点的模型。
- 每条候选都要写清 识别条件 / 归约方式 / AST 映射（这三要素之后要进代码注释）。
- 编造的“复现”不算复现：写不出 ≤15 行的合成复现，就在 FACTS.md 里写 `NONE` 并说明为什么
  该形态在合成语料里造不出来（R64 diag1 的 `NONE.md` 是可接受的交付）。
- 你的 `h62.py build` 一次只吃**一份** spec（一份 spec 只能改一个 core 文件）。若机制天然需要
  generator+analyzer **成对**改动（R63-B4 的教训：单用各停在 17/18 并在对方形状上开新洞），
  就把两份 spec 都交出来、各自单独实测，并在 FACTS.md 里写明「必须成对」和你预想的合并方式；
  跨文件合并由主代理在中心用 `mkfinal.py`+`mbuild.py` 执行。

## 2. 工具（都已指向你自己的目录，ROOT 已改写）
```bash
cd D:/Temp/opencode/r65gate/diag4
# (a) 先量落地基线（--arm=landed 导入仓库 core、只写 build_landed，不动索引不动 site-packages）
python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl
python -X utf8 h62.py run --arm=landed --list=battery.txt --out=dump/battery_landed.jsonl
python -X utf8 h62.py run --arm=landed --list=canary.txt  --out=dump/canary_landed.jsonl
# (b) 建臂：spec 打在落地字节上，镜像在 mirr_<dst>，产物在 build_<dst>
python -X utf8 h62.py build --spec=specs/cand_x.json --dst=x
python -X utf8 h62.py run --arm=x --list=targets.txt --out=dump/x.jsonl
python -X utf8 h62.py ab --a=dump/landed.jsonl --b=dump/x.jsonl      # SAME/IMPROVED/REGRESSION/MOVED
# (c) 严格尺（官方尺看不见的 missing nested code object 在这里）
python -X utf8 cstrict.py build_x targets.txt dump/x_strict.json
# (d) 定位机制
python -X utf8 disf.py  <pyc> <func> --src=build_landed/<mangled>OK.py
python -X utf8 align.py <pyc> build_landed/<mangled>OK.py <func>
python -X utf8 regdump.py <pyc> <func>
python -X utf8 probe_chain.py <pyc> <func> [watch-offset ...]
python -X utf8 trace.py <pyc> <func> <逗号分隔 block offset>
```
`battery.txt` 是 19 项已入库复现（R63+R64 全部 witness），**任何候选必须先在电池上不比
落地差**，再看你自己的 targets。`canary.txt` 是 4 支 f-string/boolop 重载文件（含
`quotation.pyc` 143/143），必须逐支 sha 不变。

## 3. 优先级（防止你在 150 轮上限里空手而死）
按顺序做，做到哪一步都要**实时把读数写进 FACTS.md**（不要攒到最后）：
1. 你名下 targets 的 landed 基线 + 逐函数 `align.py`：把「缺哪几条指令 / 多了哪一段」写成
   指令级清单（有 offsets）。这是最有价值的交付，即使没有候选也要交。
2. 归因到**具体方法/具体行**（给出落地字节上的行号，并 `grep -c` 证明它真的被调用）。
   R64 有两个代理引用了仓库里不存在的函数名——不许重犯。
3. 每支文件最多写 2 个候选 spec，各测 `targets + battery + canary`；报告
   `IMPROVED/REGRESSION/MOVED` 与电池差值。
4. 若两条都无效，写 `NONE` + 你排除掉的机制（附实测数字），并提出下一条可检验判据。

## 4. 落地现状（起点，勿再测）
```
core/cfg/region_ast_generator.py  3 103 668 B  sha c9099bb0fc35  BOM+CRLF 裸LF=0
core/cfg/region_analyzer.py       1 725 369 B  sha 24a88392ee61  CRLF   裸LF=0
R64 落地后：402 支 ok 384 / partial 18 / failed 0
```
R64 的 13 处编辑标记：generator `[R64-b2]` L14360、`[R64-B2]` L21189 / L41570 / L41624 /
L41669、`[R64-D4-B]` L32990、`[R64-B1 sibling merge-entry dispatch]` L33174、
`[R64-D4-A]` L49989；analyzer `[R64-diag1 closed-shared-exit-prefix]` L25558。

## 5. 你名下的文件与已知残余

### `IQData/plugins/plugin_system_realquote/real_quote.pyc`
```
IQData/plugins/plugin_system_realquote/real_quote.pyc  39/44 deficit=5  sha=36cb2fa07daa
      get_cache_l2_data                              orig=337   decomp=335   UNDER 2   jumpdiff=2   true=313
      get_cache_l2_data_by_one                       orig=321   decomp=320   UNDER 1   jumpdiff=2   true=300
      get_tick_direction                             orig=259   decomp=258   UNDER 1   jumpdiff=3   true=102
      get_real_minute_kline                          orig=253   decomp=254   OVER +1   jumpdiff=3   true=197
      one_prod_to_ndarray                            orig=605   decomp=607   OVER +2   jumpdiff=5   true=424
```

### `IQCommon/api/klinedata.pyc`
```
IQCommon/api/klinedata.pyc  42/45 deficit=3  sha=3cf5d75eb4b1
      get_all_real_daily_kline                       orig=188   decomp=187   UNDER 1   jumpdiff=3   true=26
      get_multiminute_his_data                       orig=479   decomp=478   UNDER 1   jumpdiff=5   true=16
      kline_datetime_list                            orig=389   decomp=389   SAME-LEN  jumpdiff=9   true=228
```
> R64 移交线索（OUTCOME §6.4 / memory project-r64-boolop-chainpop-cost）：analyzer `[R64-diag1 closed-shared-exit-prefix]`（L25558）的 chain.pop() 让本文件 `get_multiminute_his_data` [479,478,3,16]→jumpdiff 5、严格 56/63→54/63 —— 本轮唯一实测代价。R65 要试的同层收窄是「**被 pop 的块自身就是该 or-run 的首块时不 pop**」（De Morgan 形态 `if a is None or b is None or …`），必须先跑电池+canary 再谈全量。

### `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`
```
IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc  32/35 deficit=3  sha=8f1e9d4ea252
      get_TradeMode_trades                           orig=1839  decomp=1801  UNDER 38  jumpdiff=4   true=1617
      _on_publish_after_trading_end                  orig=486   decomp=481   UNDER 5   jumpdiff=3   true=33
      _save_testds_to_csv                            orig=71    decomp=68    UNDER 3   jumpdiff=7   true=19
```
> R64 MOVED 归属：`get_TradeMode_trades` 缺口 86→38 来自 diag2 c2（值栈消费者判据 L14360），计数与严格函数数都不变 ⇒ 这里已经比轮初好，剩下的 38 条是新形态，不要假设与 R64 的机制同源。

### `IQCommon/util/trade_info_utils.pyc`
```
IQCommon/util/trade_info_utils.pyc  38/40 deficit=2  sha=d242839f547b
      get_trade_list                                 orig=339   decomp=323   UNDER 16  jumpdiff=14  true=148
      trade_operation                                orig=304   decomp=302   UNDER 2   jumpdiff=2   true=40
```
