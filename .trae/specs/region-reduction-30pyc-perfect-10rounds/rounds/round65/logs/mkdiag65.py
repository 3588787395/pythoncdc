# -*- coding: utf-8 -*-
"""Round 65 pre-flight: build five ISOLATED read-only diagnose workspaces.

Each diagN gets its own copy of the mirror harness with ROOT retargeted (so build_<arm>
products and mirr_<arm> cores can never be cross-contaminated between agents), the four
generic probe tools, its own target list, the shared battery/canary lists, and a BRIEF.md
carrying the rules + its pre-digested defect numbers.

Nothing here writes to the repository.
"""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
CR = chr(13)
REPO = r'F:/Downloads/pythoncdc-main'
SP = REPO + '/site-packages/'
SRC = r'D:/Temp/opencode/r64gate'
D65 = r'D:/Temp/opencode/r64gate/diag1'
GATE = r'D:/Temp/opencode/r65gate'
BS = os.sep

BATCH = {
    1: ['IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc',
        'IQEngine/plugins/plugin_system_matcher/matcher.pyc',
        'IQCommon/graph.pyc',
        'fly/logger.pyc',
        'IQData/api/api_base.pyc'],
    2: ['fly/data/quote.pyc'],
    3: ['IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'],
    4: ['IQData/plugins/plugin_system_realquote/real_quote.pyc',
        'IQCommon/api/klinedata.pyc',
        'IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc',
        'IQCommon/util/trade_info_utils.pyc'],
    5: ['IQEngine/utils/scheduler.pyc',
        'fly/simtradding/flyAccount.pyc',
        'IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc',
        'IQCommon/util/common_func.pyc',
        'IQData/utils/common_func.pyc',
        'IQCommon/util/fileio_utils.pyc',
        'IQCommon/strategy/wizard_quant_api.pyc'],
}

LEADS = {
    'IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc':
        'R64 移交线索（OUTCOME §6.1）：clock_worker 的 +11 过冲**不是**缺/多语句的净数——'
        '产物 `realtime_event_sourceOK.py` 第 275 与 312 行把 `elif check_trading_time(...)` '
        '**发射两次**，而原 code object 只有一个调用点（check_trading_time @8594、'
        'check_handle_date @8668）；同时 @6690 处丢了约 100 条指令，两相抵消。'
        '要找的是 elif 链分派（`_if_generate_normal` / R61 elif 通道）的**重复发射**，'
        '归属层面（每块每层唯一归属）先证明没坏，再查发射层。',
    'IQEngine/plugins/plugin_system_matcher/matcher.pyc':
        'R64 移交线索（OUTCOME §6.2 / memory project-r64-matcher-displacement-lead）：'
        'match 已 715/715 **计数相同**，官方仍是 16/17，第二处缺陷是 orig[180:462] 共 282 条'
        '指令整体被投到产物尾部（decomp 428..713），而 `if self._volume_limit:` 占了前槽。'
        '落地臂与候选臂 probe_align 的 hunk 表逐字节相同 ⇒ 与 R63/R64 改动无关，'
        '**这是顺序问题不是归属问题**：查块被排到 tail 的那次排序/追加，不要再去找缺失语句。',
    'IQCommon/api/klinedata.pyc':
        'R64 移交线索（OUTCOME §6.4 / memory project-r64-boolop-chainpop-cost）：'
        'analyzer `[R64-diag1 closed-shared-exit-prefix]`（L25558）的 chain.pop() 让本文件 '
        '`get_multiminute_his_data` [479,478,3,16]→jumpdiff 5、严格 56/63→54/63 —— 本轮唯一'
        '实测代价。R65 要试的同层收窄是「**被 pop 的块自身就是该 or-run 的首块时不 pop**」'
        '（De Morgan 形态 `if a is None or b is None or …`），必须先跑电池+canary 再谈全量。',
    'fly/simtradding/flyAccount.pyc':
        'R64 移交线索（OUTCOME §6.3）：`_do_request` [436,443,2,384] 过冲 +7 由 R63-B4 成对引入'
        '（chainstore/fstail 在此逐字节中性），diag5 指到的站点是落地后 '
        '`_loop_build_if_with_exit_branches`（region_ast_generator.py 约 L10470，行号需复核）。',
    'IQCommon/util/common_func.pyc':
        '双生文件：`IQCommon/util/common_func.pyc::get_kline_time_by_section` 与 '
        '`IQData/utils/common_func.pyc::get_kline_time_by_section` 缺陷元组**完全相同** '
        '[210,190,0,84]；两处必须同时量（memory project-duplicate-source-pycs）。',
    'IQData/utils/common_func.pyc':
        '双生文件：见上一条，`get_kline_time_by_section` 与 IQCommon/util/common_func.pyc 同元组。',
    'IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc':
        'R64 MOVED 归属：`get_TradeMode_trades` 缺口 86→38 来自 diag2 c2（值栈消费者判据 '
        'L14360），计数与严格函数数都不变 ⇒ 这里已经比轮初好，剩下的 38 条是新形态，'
        '不要假设与 R64 的机制同源。',
}

BRIEF0 = """# Round 65 · diag0 · 技术债批次：清除生成器里的调试导入（只读诊断，禁止落地）

## 0. 任务
`core/cfg/region_ast_generator.py`（落地字节 3 103 668 B / sha c9099bb0fc35 / BOM+CRLF）里残留
**13 处 `import os as _os_dbg*` 调试导入**，实测行号：
```
L20961 _os_dbg5   L20999 _os_dbg4   L33020 _os_dbg_13  L43773 _os_dbg    L44507 _os_dbg_main
L47086 _os_dbg_lf L47246 _os_dbg_r23n6_trace L47294 _os_dbg_pre
L47331 _os_dbg    L47348 _os_dbg    L47353 _os_dbg     L47358 _os_dbg    L47366 _os_dbg
```
（R64 OUTCOME §6.5 的技术债条目；全仓库只有这一个文件残留，`grep -rlc "_os_dbg_" --include=*.py core/` 已证。）
目标是产出一份**可落地的清理 spec**：删掉这些导入，以及**只为它们服务**的临时写盘/打印语句。

## 1. 必须先做的引用普查（这是本批次的主要风险）
只删 `import` 而留着 `_os_dbg.path.join(...)` / `_os_dbg.open(...)` 会让那条代码路径在运行时
`NameError`。所以对每一个不同的名字（`_os_dbg`、`_os_dbg4`、`_os_dbg5`、`_os_dbg_13`、
`_os_dbg_main`、`_os_dbg_lf`、`_os_dbg_pre`、`_os_dbg_r23n6_trace`）都要：
- `grep -n "_os_dbgXXX"` 列出**全部**引用行（不止 import 行），逐条判断是否有写盘/打印副作用；
- 判断该语句是否被 `try/except` 吞掉（若是，删除会**改变异常路径**，必须说明）；
- 给出「删哪些行、留哪些行」的逐行清单。注意 `_os_dbg`（裸名）的 `grep -n _os_dbg` 会连带命中
  `_os_dbg_main` 等，必须用词边界（`grep -nE "_os_dbg\\b(?!_)"` 之类）或逐条人工核对。

## 2. 硬约束（违反即作废）
- **禁止修改仓库任何文件**：不许 `git` 写、不许 `single`、不许 `batch`、不许 `_r13_gate.py`、
  不许 `land*`/`mbuild`/`mkfinal`。R64 有一个诊断代理把工作树 core 重排成纯 LF（EVIDENCE §B
  事故），再发生一次本轮就废了。你只能在 `{ws}` 下写。
- 每条命令 **< 300 秒**；402 支一律 `h62.py run --nshard=4 --shard=i` 分片后合并。
- 不许设置 `PYTHONIOENCODING`；一律 `python -X utf8`。
- 清理**不得改变任何产物字节**：这是本批次唯一的正确性判据。

## 3. 门禁（候选臂 vs 落地臂，全部要实测数字）
```bash
cd {ws}
python -X utf8 h62.py build --spec=specs/cand_r65b0_stripdbg.json --dst=s1
# landed 基线：402 支分 4 片
for i in 0 1 2 3; do python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/l402_$i.jsonl --nshard=4 --shard=$i & done; wait
for i in 0 1 2 3; do python -X utf8 h62.py run --arm=s1 --list=targets.txt --out=dump/s402_$i.jsonl --nshard=4 --shard=$i & done; wait
python -X utf8 h62.py ab --a=dump/l402_0.jsonl --b=dump/s402_0.jsonl   # 四片都要 TALLY SAME=全部 REGRESSION=0 MOVED=0
python -X utf8 h62.py run --arm=s1 --list=battery.txt --out=dump/s1_battery.jsonl
python -X utf8 h62.py ab --a=dump/battery_landed.jsonl --b=dump/s1_battery.jsonl
python -X utf8 h62.py run --arm=s1 --list=canary.txt  --out=dump/s1_canary.jsonl
python -X utf8 h62.py ab --a=dump/canary_landed.jsonl --b=dump/s1_canary.jsonl
```
**MOVED 必须为 0**：本批次任何产物 sha 变化都是失败信号（说明删掉的语句其实在起作用）。
`SAME=402 / REGRESSION=0 / MOVED=0` + 电池全同 + canary 全同 + `py_compile` OK 才算交付。
（`h62.py ab` 要求两侧行数一致；分片对照时把同一 shard 的 landed/s1 配成一对。）

## 4. 交付
1. `specs/cand_r65b0_stripdbg.json` —— 一条 spec 内含全部 edits（anchor 在落地字节里各恰好 1 次）；
2. `FACTS.md` —— 引用普查表（每个名字：引用行数、是否有副作用、删/留决定）+ 402 分片 TALLY +
   电池/canary TALLY + 可复放命令；
3. `ANALYSIS.md` —— 这些调试导入来自哪几轮（按名字里的 r23n6/r63 等线索）、为何行为中性、
   以及热路径里是否真的发生过文件 I/O（给实测：如在 `--arm=landed` 跑前后计数）。
4. 若发现某处删除**确实**会改变产物，就把它单独列成「不可清理」并给出见证，不要硬删。

## 5. 与本轮 mandate 的关系
本批次**不解决任何 partial**，所以主代理不会用它冒充「至少修好一支」。它的价值是把 3 MB
生成器里的隐藏文件 I/O 与阅读噪声清掉，为后续轮次提速。落地由主代理集中执行。
"""


COMMON = """# Round 65 · diag{N} · 任务书（只读诊断，禁止落地）

## 0. 你是谁、交付什么
你是本轮 5 个并行诊断代理之一。你**只诊断、只测量、只写候选 spec**；落地与门禁由主代理
集中验证后执行。你的交付物全部放在 `{ws}` 里：
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
cd {ws}
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
"""


def facts_for(rel):
    lines = io.open(os.path.join(GATE, 'r65_targets.txt'), encoding='utf-8').read().split('\n')
    block, keep = [], False
    for l in lines:
        if 'deficit=' in l:
            keep = l.split()[0].endswith('/' + rel)
            if keep:
                block.append(l.split('site-packages/')[-1].strip())
            continue
        if keep and l.startswith('      '):
            block.append(l)
    return '\n'.join(block)


def main():
    ws0 = os.path.join(GATE, 'diag0')
    os.makedirs(os.path.join(ws0, 'specs'), exist_ok=True)
    os.makedirs(os.path.join(ws0, 'dump'), exist_ok=True)
    os.makedirs(os.path.join(ws0, 'logs'), exist_ok=True)
    src = io.open(os.path.join(SRC, 'h62.py'), encoding='utf-8-sig', newline='').read()
    old_root = "ROOT = r'D:/Temp/opencode/r64gate'"
    src0 = src.replace(old_root, "ROOT = r'D:/Temp/opencode/r65gate/diag0'")
    io.open(os.path.join(ws0, 'h62.py'), 'w', encoding='utf-8', newline='').write(src0)
    cs = io.open(os.path.join(SRC, 'cstrict.py'), encoding='utf-8-sig', newline='').read()
    cs = cs.replace("GATE = r'D:/Temp/opencode/r64gate'", "GATE = r'D:/Temp/opencode/r65gate/diag0'")
    io.open(os.path.join(ws0, 'cstrict.py'), 'w', encoding='utf-8', newline='').write(cs)
    io.open(os.path.join(ws0, 'targets.txt'), 'w', encoding='utf-8', newline='').write(
        '\n'.join(SP + l.strip() for l in io.open(os.path.join(SRC, 'all402.txt'), encoding='utf-8') if l.strip()) + '\n')
    shutil.copyfile(os.path.join(GATE, 'battery65.txt'), os.path.join(ws0, 'battery.txt'))
    shutil.copyfile(os.path.join(SRC, 'canary4.txt'), os.path.join(ws0, 'canary.txt'))
    io.open(os.path.join(ws0, 'BRIEF.md'), 'w', encoding='utf-8-sig', newline='').write(BRIEF0.replace('{ws}', ws0.replace(BS, '/')).replace('\n', '\r\n'))
    print('diag0: cleanup batch -> %s' % ws0)
    for n, files in BATCH.items():
        ws = os.path.join(GATE, 'diag%d' % n)
        os.makedirs(os.path.join(ws, 'specs'), exist_ok=True)
        os.makedirs(os.path.join(ws, 'dump'), exist_ok=True)
        os.makedirs(os.path.join(ws, 'logs'), exist_ok=True)
        src = io.open(os.path.join(SRC, 'h62.py'), encoding='utf-8-sig', newline='').read()
        old_root = "ROOT = r'D:/Temp/opencode/r64gate'"
        assert src.count(old_root) == 1, 'h62 ROOT not found'
        src = src.replace(old_root, "ROOT = r'D:/Temp/opencode/r65gate/diag%d'" % n)
        io.open(os.path.join(ws, 'h62.py'), 'w', encoding='utf-8', newline='').write(src)
        cs = io.open(os.path.join(SRC, 'cstrict.py'), encoding='utf-8-sig', newline='').read()
        old_gate = "GATE = r'D:/Temp/opencode/r64gate'"
        assert cs.count(old_gate) == 1, 'cstrict GATE not found'
        cs = cs.replace(old_gate, "GATE = r'D:/Temp/opencode/r65gate/diag%d'" % n)
        io.open(os.path.join(ws, 'cstrict.py'), 'w', encoding='utf-8', newline='').write(cs)
        for t in ['disf.py', 'align.py', 'regdump.py', 'trace.py', 'probe_chain.py']:
            shutil.copyfile(os.path.join(D65, t), os.path.join(ws, t))
        paths = [SP + f for f in files]
        io.open(os.path.join(ws, 'targets.txt'), 'w', encoding='utf-8', newline='').write('\n'.join(paths) + '\n')
        shutil.copyfile(os.path.join(GATE, 'battery65.txt'), os.path.join(ws, 'battery.txt'))
        shutil.copyfile(os.path.join(SRC, 'canary4.txt'), os.path.join(ws, 'canary.txt'))
        txt = COMMON.replace('{N}', str(n)).replace('{ws}', ws.replace(BS, '/'))
        for f in files:
            txt += '\n### `%s`\n```\n%s\n```\n' % (f, facts_for(f))
            if f in LEADS:
                txt += '> %s\n' % LEADS[f]
        io.open(os.path.join(ws, 'BRIEF.md'), 'w', encoding='utf-8-sig', newline='').write(txt.replace('\n', '\r\n'))
        print('diag%d: %d files, %d defect fns -> %s' % (n, len(files), sum(
            1 for l in '\n'.join(facts_for(f) for f in files).split('\n') if l.startswith('      ')), ws))
    print('OK')


if __name__ == '__main__':
    main()
