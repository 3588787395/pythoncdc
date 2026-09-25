# Round 65 · diag5 · 任务书（只读诊断，禁止落地）

## 0. 你是谁、交付什么
你是本轮 5 个并行诊断代理之一。你**只诊断、只测量、只写候选 spec**；落地与门禁由主代理
集中验证后执行。你的交付物全部放在 `D:/Temp/opencode/r65gate/diag5` 里：
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
cd D:/Temp/opencode/r65gate/diag5
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

### `IQEngine/utils/scheduler.pyc`
```
IQEngine/utils/scheduler.pyc  43/45 deficit=2  sha=d809b238385b
      run_daily                                      orig=77    decomp=71    UNDER 6   jumpdiff=0   true=56
      get_checked_time                               orig=106   decomp=106   SAME-LEN  jumpdiff=0   true=43
```

### `fly/simtradding/flyAccount.pyc`
```
fly/simtradding/flyAccount.pyc  21/23 deficit=2  sha=e58c7d8dbc8f
      init_connection                                orig=42    decomp=41    UNDER 1   jumpdiff=0   true=25
      _do_request                                    orig=436   decomp=443   OVER +7   jumpdiff=2   true=384
```
> R64 移交线索（OUTCOME §6.3）：`_do_request` [436,443,2,384] 过冲 +7 由 R63-B4 成对引入（chainstore/fstail 在此逐字节中性），diag5 指到的站点是落地后 `_loop_build_if_with_exit_branches`（region_ast_generator.py 约 L10470，行号需复核）。

### `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc`
```
IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc  32/34 deficit=2  sha=5e59c43ab22b
      option_order                                   orig=83    decomp=73    UNDER 10  jumpdiff=3   true=39
      future_order                                   orig=101   decomp=92    UNDER 9   jumpdiff=2   true=36
```

### `IQCommon/util/common_func.pyc`
```
IQCommon/util/common_func.pyc  19/21 deficit=2  sha=d93288c70cba
      get_kline_time_by_section                      orig=210   decomp=190   UNDER 20  jumpdiff=0   true=84
      get_kline_time_by_frequency_array              orig=231   decomp=228   UNDER 3   jumpdiff=0   true=45
```
> 双生文件：`IQCommon/util/common_func.pyc::get_kline_time_by_section` 与 `IQData/utils/common_func.pyc::get_kline_time_by_section` 缺陷元组**完全相同** [210,190,0,84]；两处必须同时量（memory project-duplicate-source-pycs）。

### `IQData/utils/common_func.pyc`
```
IQData/utils/common_func.pyc  22/24 deficit=2  sha=937f64d6c619
      get_kline_time_by_section                      orig=210   decomp=190   UNDER 20  jumpdiff=0   true=84
      handle_exrights                                orig=276   decomp=268   UNDER 8   jumpdiff=1   true=263
```
> 双生文件：见上一条，`get_kline_time_by_section` 与 IQCommon/util/common_func.pyc 同元组。

### `IQCommon/util/fileio_utils.pyc`
```
IQCommon/util/fileio_utils.pyc  12/14 deficit=2  sha=3e3051014298
      acquire                                        orig=96    decomp=93    UNDER 3   jumpdiff=3   true=52
      write                                          orig=637   decomp=637   SAME-LEN  jumpdiff=4   true=519
```

### `IQCommon/strategy/wizard_quant_api.pyc`
```
IQCommon/strategy/wizard_quant_api.pyc  51/53 deficit=2  sha=6f08c711b833
      params_analysis                                orig=133   decomp=126   UNDER 7   jumpdiff=1   true=117
      calculate_di                                   orig=75    decomp=73    UNDER 2   jumpdiff=0   true=45
```
