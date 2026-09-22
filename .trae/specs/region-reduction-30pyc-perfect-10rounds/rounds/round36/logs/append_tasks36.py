# -*- coding: utf-8 -*-
"""Round 36 close-out: append Task 36 + SubTasks to tasks.md byte-level.

Forked from round 35's appender. Asserts the exact prefix identity read before writing (raw
sha256, byte length, CRLF/LF counts, BOM state) so a stale assumption can never rewrite the
file, then appends one CRLF-normalised block. The Edit tool is deliberately not used: it
re-serialises line endings.
"""
import hashlib
import io
import sys

REPO = r'F:\Downloads\pythoncdc-main'
P = REPO + '/.trae/specs/region-reduction-30pyc-perfect-10rounds/tasks.md'
CR = chr(13)

EXPECTED = {'bytes': 161634, 'sha256_20': 'ab111f622fb9a29b66be', 'crlf': 1522, 'lf': 1522}

BLOCK = u"""- [x] Task 36: 落地 R36-A —— break→return 折叠读臂容器必须满足语句容器表示不变量：`orelse` 取到 `None`
      与缺键一律归一为空表，不得让 `len(None)` 抛 TypeError 后被区域生成的上层兜底 `except` 吞掉而把
      整条 `for` 连同体内赋值一起丢掉（记录 `rounds/round36/arm-design.md` ＋ `rounds/round36/OUTCOME.md`）
  - [x] SubTask 36.1: 目标池按落地字节实测（工具 `logs/pool36.py`，输出 `logs/pool36.txt`）：
          `baseline(landed round35 index, HEAD 703be216, core sha 92c8c2aabdcd37b9f32b)` ⇒ 402 文件／
          29 partial／Σdeficit 99／deficit-1 池 6 个／deficit-2 池 12 个；靶
          `IQEngine/plugins/plugin_fly_data/fly_api/base.pyc 39/41`（deficit 2，两个孪生方法
          `FutureSettingStore.get_close_position_type 30/9`＋`has_close_position_type 27/6` 各缺整条
          `for`）。deficit-1／deficit-2 两侧读数留档 `logs/landed_d1.jsonl`／`logs/landed_d2.jsonl`（官方尺）。
  - [x] SubTask 36.2: 电池扩到 44／105 并**先证明可复用**：本轮自建落地基线 `logs/b44_landed.jsonl`
          （39 件上一轮形状 ＋ R35-B 的 5 件）与 `logs/a105_landed.jsonl`（104 件锚点 ＋ R35-B 靶），
          `logs/tally_b44growth.txt` 读「上一轮 39 件基线 vs 本轮 44 件基线」= `SAME=39`、未配对 5 件、
          全匹配 28 → 33 ⇒ 增量确实只是新形状。G4 的「改前」侧沿用上轮落地臂整批读数
          （`logs/ref_g4_r35b.all.jsonl`，sha256[:20] `7ac9248fe4d6f9291da2`），沿用前提本轮重新证明：
          `r36c.py build` 断言 `mirr_head` 与工作区核文件**字节全等**，且 `head` 臂对 deficit-2 池 12 件
          重读给出 `SAME=12`（`logs/tally_g1d2head.txt`）。
  - [x] SubTask 36.3: 分片跑批的**静默丢行**修复：三 shard 共写一份 jsonl 会少一行——G3 首跑日志显示
          `r3_10_try_except_block_scramble_dec.pyc` 已处理，合并文件却只有 104/105 条。改为每 shard 各写
          自己的 out 文件再拼接（`g3_r36a.s{0,1,2}.jsonl` → `g3_r36a.jsonl`），缺的那一条由 `logs/miss1.txt`
          单独补跑；此后 G3／G4 全部按此写法。
  - [x] SubTask 36.4: 诊断代理（150 轮耗尽、未交 `ANALYSIS.md`）的产出分两处处置：它的 in-memory 修补
          产物（`logs/diag_p10_agentpatch_product.txt` 把循环摊平成 `enumerate(tc)`／`c.isdigit()` 三条裸
          表达式语句）被本轮边界电池直接否证，未采纳；它的崩溃扫描被接手重做并**订正覆盖面**——
          `logs/diag_p7c_crashscan128.txt` 128 行里只有 21 行是语料 `.pyc`（402 个中的 21 个）、107 行是
          `test_repros/` 合成件（输入名单同名 `logs/diag_p7c_roster.txt`），被扫到的 21 个语料文件中只有
          靶文件崩溃（`2x TypeError @ region_ast_generator.py:4824 in _fold_break_to_return`）；
          「全语料只有靶文件崩溃」这句改由 G4 全 402 A/B 承担。
  - [x] SubTask 36.5: G0 电池**先于**任何 `core/` 改动建成（`test_repros/round36_for_loop_dropped/`
          七件：三见证三控制加一片 `r36_06`，源件 `shapes36.py`，`g0_build36.py` 写盘并显式 `cfile`
          `py_compile`，`g0_run36.py` 双尺读且断言 `pycdc` 解析到请求的臂）。落地／`head` 臂
          `logs/g0_landed.txt`＝`logs/g0_head.txt`：`PASS 3/7`——`r36_01/02/03` FAIL 均 `delta-21`、
          `r36_06` FAIL `delta-25`，`r36_04/05/07` PASS；候选臂 `logs/g0_r36a.txt`：`PASS 7/7`。
  - [x] SubTask 36.6: 判别式由该表一手定出，并**否证两个先前假设**：触发只与 ①循环无 `else`（break 后继
          即自然出口，故 `_break_to_return_map` 非空、`:4809` 才进折叠；该表要求 break 后继块
          `get_block_role` ∈ {RETURN, RETURN_NONE}，`:4798-4800`）＋ ②`break` 所在臂还带有自己的前导语句
          （臂不是纯跳转，够不到 `:4818` 的单条 `break` 分支，才走到 `:4824` 的 `len(_orelse)`）二者有关；
          「汇合块兼作函数尾才触发」被 `r36_03` 否证（中间隔一条语句照样整块丢）。三条 PASS 控制各自
          站在崩溃点的另一侧（`:4818` 先命中／表空不进折叠）。
  - [x] SubTask 36.7: 根因闭合：`_loop_generate_for`（`:4279`）折叠内 `:4817` 写作
          `_orelse = s.get('orelse', [])`，而本项目 If 节点存在 `{'orelse': None}` 这一表示
          （`:17214`／`:17457`／`:34766`／`:36939`／`:37090`／`:44441` 发射
          `else_stmts if else_stmts else None`）——`dict.get` 的默认值只在**键缺失**时生效 ⇒ `len(None)`
          抛 TypeError ⇒ 被 `:1681-1683` 的兜底 `except Exception` 吞掉、该区域走
          `_generate_degraded_statements`（`:1688`）逐块降级 ⇒ 症状是整条 `for` 消失而不是报错。核内
          `_normalize_stmt_lists`（`:573`）docstring 早已写明这条契约与这条故障链，其归一发生在
          `generate()` 汇总处（`:1697`）**晚于**区域生成；同一个折叠的 while 路径（`:4935`）早已用安全
          惯式 `s.get('orelse') or []`（`:6381`），for 路径 `:4817` 是同一处逻辑的漏网第二半。
  - [x] SubTask 36.8: 判据 **R36-A**（唯一发货项）：break→return 折叠读臂容器时 `None` 与缺键一律按语句
          容器表示不变量归一为空表——for 路径取值式与 while 路径既有归一读取同式。补丁 `spec36a.json`
          1 处编辑、0 增删行、2 字节（锚点两行在 2984322 字节文件中唯一）。同层性：读的是节点表示不变量，
          不读变量名/常量/绝对偏移/指令条数/认领历史，不改折叠的识别条件与 AST 映射，只在原本必然抛错的
          那一个求值点停止抛错。同族第三处 `:2118`（`_build_function_def` 内同款读取）**不改**：无触发证据。
  - [x] SubTask 36.9: 门禁严格串行、逐条实测，TALLY 全部就归档 `.jsonl` 复算留档 `logs/tally_*.txt`。
          G0 `3/7 → 7/7`；G1 deficit-1 池 `SAME=6 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`；G1 deficit-2 池
          `IMPROVED=1(base 39/41 -> 41/41) SAME=11 REGRESSION=0`；G2′ `SAME=44 ERR=0`（33 条全匹配不变）；
          G3 `SAME=105 ERR=0`（75 条全匹配不变）；**G4 全 402 A/B（sha-first，唯一发货权威）
          `SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`**，整文件全匹配 373 → 374；G4′ 严格尺读变更产物
          `strict clean 60/63 sigma-defect=3 sum_abs_delta=66` → `62/63 sigma-defect=1 sum_abs_delta=24`。
  - [x] SubTask 36.10: 落地即复测：`land36.py` 以「同一份 spec 重放 == 被测镜像字节」为准 →
          `applied: 2984322 -> 2984324 bytes, CRLF 48418 = LF 48418, BOM=True, equals measured mirror=True`，
          核身份 `raw bbfe1a414032436921ab / 正规化 761d927617bd162b5d9f`（`logs/core_identity36.txt`）。
          G5 `single`：靶 `41 / 41`，在册产物 == 候选臂产物（18163 字节，sha256[:16] `15bbbf460c0ddc5e`），
          产物 diff 恰为 +8 行（两条 `for` 各 4 行），`baseOK.py:319-324` 与原始源码逐字符一致；canary
          `fly/data/quotation.pyc 143/143`，重生成产物与在册产物字节相同（183261 字节）；G6
          `batch --index pyc_index.json --all --round 36` 402 条读完、`failed_pyc 0`，索引逐条目差异只有
          402 条 `last_tested_round` 与靶自身的 `partial→ok / 39→41 / rate→1.0`（改前侧取
          `git show HEAD:pyc_index.json`）；G7 见 `OUTCOME.md` §五。零副作用面：G6 之后
          `git status --porcelain` 只有核／靶产物／索引三项在册文件被改。
  - [x] SubTask 36.11: 方法论收获：①`-21` 级「整块丢失」先前记在 #41/#43「整块丢失族」名下当算法缺陷，
          本轮证明它是一处两字节的机械漏网——**先挂异常探针再谈判据**，且探异常要显式（兜底 `except`
          会把崩溃伪装成「判据太严」，退化产物形状与「区域被拒」在官方尺下不可区分）；②扫描的**覆盖面**
          与结论的措辞必须配得上：名单里只有 21/402 个语料文件时，全语料暴露面只能由 402 文件 A/B 给；
          ③一条已修过的惯式要当契约看待，同层判据最稳的形态是**让漏网的一半向已修的一半对齐**，
          而不是新增条件；④上游轮次（本轮是台账 #41/#43）把症状归成「族」的标签是待验证假设，不是结论；
          ⑤代理产出的证据要逐条重做，采纳前先问能否被一个便宜的独立实验复现。
  - [x] SubTask 36.12: 移交 Round 37：①靶文件唯一残余 `OverNightOrder.__init__ 172/148 delta-24`——
          现属 #41「整块丢失族」在册成员，本轮崩溃探针显示本文件只崩过 2 次且都在孪生上，**不属**本族，
          下一轮先用异常探针判它是机械故障还是判据；②`tick_worker_thread 268/247`（单条 29 指令 elif 臂
          缺失、首合取支被借走，`logs/probe1_strategy_tick_worker_thread.txt` hunk `delete orig[114:143]`，
          已排除与本族同源）、`match 713/689`（281 删除 + 259 插入的换位，另丢
          `STORE_FAST is_first_five_trading_days`）；③台账继续在册：`decrypt_database_url 295/324`（+29
          过量发射，#43）、`clock_worker 1275/1291`（R22/R23 移交 D2/D3）、`events 510/508`（Round 34 已判
          字节码层欠定，勿再从 else 归属侧进攻）、`_init_config 86/84`（R16 J1 在册反例，受保护勿再取）、
          #61 R30-B3 ＋ 语料外见证 `r29x_01 <module> 142/138`；④**崩溃探针制度化**：把异常枚举扫描的输入
          换成全 402 名单（`logs/all402.txt`）作为每轮目标选择的常备尺子，一遍同时给出「谁崩」与
          「谁被兜底降级」；⑤电池增量：G2′ 的 44 件应加本轮 7 件（尤其见证 `r36_01` 与控制
          `r36_04`／`r36_07`），G3 的 105 件应加已全匹配的靶 `plugin_fly_data/fly_api/base.pyc`。
"""


def main():
    raw = io.open(P, 'rb').read()
    _crlf = raw.count(b'\r\n')
    got = {'bytes': len(raw), 'sha256_20': hashlib.sha256(raw).hexdigest()[:20],
           'crlf': _crlf, 'lf': raw.count(b'\n')}
    assert got == EXPECTED, 'prefix identity changed: %s != %s' % (got, EXPECTED)
    assert raw[:3] != b'\xef\xbb\xbf' and raw.endswith(b'\r\n'), 'unexpected file shape'

    blk = BLOCK.replace('\r\n', '\n')
    assert CR not in blk and blk.endswith('\n')
    out = raw + blk.replace('\n', '\r\n').encode('utf-8')
    assert out[:len(raw)] == raw, 'append was not purely additive'
    u = out.decode('utf-8')
    assert u.count(CR) == u.count('\n') == EXPECTED['crlf'] + blk.count('\n')
    _lines = u.replace('\r\n', '\n').split('\n')
    assert not [l for l in _lines if l != l.rstrip()], 'trailing whitespace'
    io.open(P, 'wb').write(out)
    after = io.open(P, 'rb').read()
    assert after == out
    print('tasks.md appended: %d -> %d bytes  CRLF %d (was %d)  +%d lines  sha256[:20] %s'
          % (len(raw), len(after), after.count(b'\r\n'), _crlf, blk.count('\n'),
             hashlib.sha256(after).hexdigest()[:20]))
    print('Task 36 header line %d; SubTasks 36.x lines %d'
          % (next(i for i, l in enumerate(_lines, 1) if l.startswith('- [x] Task 36:')),
             sum(1 for l in _lines if 'SubTask 36.' in l)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
