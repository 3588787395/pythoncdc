# -*- coding: utf-8 -*-
"""Append the Round 52 SubTasks block to tasks.md byte-level.

The file is 100% CRLF; nothing is rewritten, only bytes are appended after the
last line. A prefix assertion on the tail (the closing words of SubTask 51.6)
guards against appending onto a moved/edited file.
"""
import io
import os

REPO = r'F:\Downloads\pythoncdc-main'
P = os.path.join(REPO, r'.trae/specs/region-reduction-30pyc-perfect-10rounds/tasks.md')
raw = io.open(P, 'rb').read()
crlf = raw.count(b'\r\n')
assert raw.count(b'\n') == crlf, 'tasks.md line endings are not pure CRLF'
tail = raw[-260:].decode('utf-8')
assert u'门禁跑完前' in tail and u'git status --porcelain core/ pycdc.py' in tail, \
    'unexpected tasks.md tail (Round 51 block not last): %r' % tail[-120:]
assert raw.endswith(b'\r\n'), 'tasks.md does not end with a newline'

BLOCK = u'''  - [x] SubTask 52.1: 测试工程师——靶定到 `IQCommon/api/klinedata.pyc` 的**长度**缺陷族（`+1` 而非 `−1`，与
          Round 45–51 的「丢指令」方向相反）：`_all_bars_of_cache [seq_len] orig=230 decomp=231`、
          `kline_datetime_list [seq_len] orig=390 decomp=391`，同族另有 `fly/data/quote.pyc :: check_stock
          orig=88 decomp=89` 与在册复现体 `test_repros/round3/r3_12_assert_absorbed_as_else.pyc 1/2`。
          `dis` 逐字取证给出地面真相：比较链最后一段的落空边（`238 POP_JUMP_FORWARD_IF_FALSE to 250`）、
          短路中间出口（`244 JUMP_FORWARD to 250`）与臂体块 246 的正常流**同指块 250**，而 250 是臂后
          兄弟语句 `if history_cache == 1:` 的条件块 ⇒ 250 是两臂汇合点，不是 else 臂。
  - [x] SubTask 52.2: 修复工程师——落地 **R52-B**（`core/cfg/region_analyzer.py ::
          _build_chained_compare_region`，`19683-19704`，+22 行单 hunk）：构造 `IfRegion` 前取
          `else_blocks[0]`，若 then 臂块集 `_blocks` 中任一块把它列为 `successors` 成员，则该块是汇合点
          ⇒ 按「无 else 的比较链 if」归约（`else_blocks = []`、`merge_block = ` 该块、把它从 `all_blocks`
          摘出交父层作兄弟发射）。只读块集与后继关系，不读名字/常量/偏移/指令数；未命中逐字节不变。
          新增电池 `wit52b/` 12 例：落地前 `MISMATCH=7 MATCH=5`、候选臂 `MISMATCH=1 MATCH=11`
          （5 例阴性对照两臂均 MATCH ⇒ 判据不过火），逐例见 `rounds/round52/wit52b_tally.md`。
  - [x] SubTask 52.3: 落地 **R52-A**（`core/cfg/region_ast_generator.py :: _if_generate_elif_chain` 的
          entry 否决精化，`16135-16150`，+16 行）：`该块是某区域 entry` 仅在该区域**真的拥有这块**时构成
          竞争归属；分析器留下的退化占位容器（`Region` 且 `region_type=BASIC` 且 `blocks == {entry}`）在归属
          正是本链时不是竞争者。**这即 Round 51 移交线 A 的正解**：阻塞点不是 R51-B 的「全局无 orelse」前置，
          而是这条占位区域否决——`wit52/` 电池因此 13/14 → **14/14**（`r51a_04`、`r51b_06` 双证闭合）。
          真实语料作用面如实入账：R52-A 单独 `G4 SAME=541 IMPROVED=0 REGRESSION=0 MOVED=3`，与 R52-B 合并
          `SAME=541 IMPROVED=0 REGRESSION=0 MOVED=3`（相对 c52b 臂）⇒ 两条判据零相互作用；其收益是 4 处
          `else: pass` 的源码保真，两把尺子都不可见（`pass` 臂编译成噪声 NOP），**不计入任何率值收益**。
  - [x] SubTask 52.4: 门禁（候选臂与落地核双跑，严格串行）——G0 15 靶逐函数仅 `quote 71/89 → 72/89`、
          靶面严格缺陷行 `95 → 94`、电池 14/14；G1 `SAME=16 REGRESSION=0 MOVED=1`；G2′ 143 支
          `IMPROVED=1 REGRESSION=0`、`fully matched 111 → 112`；G3 109 支 `IMPROVED=1 REGRESSION=0`、
          `79 → 80`；G4 全量 544 路径 `TALLY SAME=538 IMPROVED=3 REGRESSION=0 MOVED=3 ERR=0`、
          `files fully matched 484 → 485`（`klinedata 41/45→42/45`、`quote 69/81→70/81`、
          `r3_12 1/2→2/2`）；G4′ `fixed=2 broken=0 changed=3` 且三处 changed 逐项严格靠近
          （`api_base :: get_history_df |1742−1718|=24 → 23`；`_all_bars_of_cache seq_len → target_diff #24`；
          `kline_datetime_list seq_len → seq_diff #151` = 长度缺陷清除后露出内容缺陷）。
  - [x] SubTask 52.5: 落地与收口——`land52.py` 先内存应用两份 spec（锚点各 `count==1`）并与通过门禁的合并臂
          `mirr_c52ab/core/cfg/*` 逐字节相同后才写盘；G5 落地核重跑 6 支受影响 pyc ⇒ 产物与臂产物 **6/6 逐字节相同**、
          金丝雀 `fly/data/quotation.pyc` 官方 `143/143`／strict `148/150` 逐字不变、`test_repros/round16_sink`
          15/15 MATCH；G6 `batch --index pyc_index.json --all --round 52` 402 verified / 0 failed，
          全量重跑后仅 5 支 `*OK.py` 内容变化（＝ G4 的 MOVED∪IMPROVED 集合，无手改产物）；
          `pyc_index.json` 值域变化仅 2 条（`klinedata 41 → 42`、`quote 69 → 70`），仍纯 CRLF 4553 行。
          字节面：`region_analyzer c644a6ccab745ac6be0e → 66553c66939e9e9242f4`（1 687 755 → 1 689 673 B，
          CRLF 27 126 → 27 148、裸 LF 0、无 BOM），`region_ast_generator 944c18b3e0807f7139c0 →
          c36cf1fe7dad68377c80`（3 010 264 → 3 011 895 B，CRLF 48 761 → 48 777、裸 LF 0、BOM 保留）；
          G7 `stats`：`total_functions 5746`（分母未动）、`matched_functions 5665 → 5667`、
          `cumulative_match_rate 98.59% → 98.63%`。
  - [x] SubTask 52.6: 否证与移交——**R52-B 的判据在「链嵌在 or 里」不触发**（`wit52b/r52b_09` 同形残支
          `if a < b < c or d:` 两臂均 `+2`）：此时落空边指向 boolop 自身的塌缩块而非本区域
          `short_circuit_succ`，开证点是 `chain_blocks`/`all_compare_blocks` 与外层布尔区域汇合块的互指，
          交 Round 53。同文件已清长度、余内容缺陷两支（`_all_bars_of_cache target_diff #24`
          `POP_JUMP_FORWARD_IF_TRUE 160 vs 148`、`kline_datetime_list seq_diff #151`）与
          `check_datetime_common 39/45` 不得并入本轮判据。**伪造尾随 continue（T1/T2）族本轮未触碰**：
          `gt52_try.py` 已给出两种 CPython 布局地面真值、发射站点定位到 `region_ast_generator.py`
          的 `stmts.append({'type': 'Continue'})`（`blk=964`），且该块前驱 `≥2` 已被
          `_is_loop_tail_convergence_block` 吞掉 ⇒ 需发射侧判据另轮开证（靶 `_on_set_positions 297/298`、
          `finance :: func_get_fundamentals_daily_data 192/193`）。Round 50 三元链 kwarg 线（`order_api ::
          future_order 101/93`、`option_order 83/74`）与 `base_order [target_diff] #136` 仍未动。
          归档 `rounds/round52/`（OUTCOME.md + `wit52/` 14 支 + `wit52b/` 12 支 + 两臂 spec/生成脚本 +
          G0/G1/G2′/G3/G4/G4′/G5/G6/G7 日志与 jsonl + 产物 diff）。起始 HEAD `bc134e10`（Round 50 记录），
          落地前 `git status --porcelain core/ pycdc.py` 为空。
'''

add = BLOCK.replace(u'\n', u'\r\n').encode('utf-8')
io.open(P, 'ab').write(add)
raw2 = io.open(P, 'rb').read()
assert raw2[:len(raw)] == raw, 'existing bytes were not preserved'
assert raw2.count(b'\n') == raw2.count(b'\r\n'), 'appending broke CRLF purity'
print('tasks.md %d -> %d B ; CRLF %d -> %d ; appended %d lines'
      % (len(raw), len(raw2), crlf, raw2.count(b'\r\n'), BLOCK.count(u'\n')))
