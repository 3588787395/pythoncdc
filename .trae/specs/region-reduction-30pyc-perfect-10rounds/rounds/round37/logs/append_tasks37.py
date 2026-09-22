# -*- coding: utf-8 -*-
"""Round 37 close-out: append Task 37 + SubTasks to tasks.md byte-level.

Forked from round 36's appender. Asserts the exact prefix identity read before writing (raw
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

EXPECTED = {'bytes': 172080, 'sha256_20': 'c88deb428de55a76f441', 'crlf': 1609, 'lf': 1609}

BLOCK = u"""- [x] Task 37: 落地 R37-A —— or-extension 找「可借 elif 臂的链」时在扁平 `regions` 整表上筛供体，
      必须加归属约束：把**本区域入口块**收进自己块集里的 `IfRegion` 是本区域的祖先（或自身），
      不得把自己的 elif 臂挂到子孙区域上发射（记录 `rounds/round37/arm-design.md` ＋
      `rounds/round37/OUTCOME.md`）
  - [x] SubTask 37.1: 目标池按落地字节实测（工具 `logs/pool37.py`，输出 `logs/pool37.txt`）：
          `baseline(landed round36 index, HEAD d1052a6c, core sha bbfe1a414032436921ab)` ⇒ 402 文件／
          28 partial／Σdeficit 97／deficit-1 池 6 个／deficit-2 池 11 个。partial 由 Round 36 开池的 29
          降为 28 只因 R36-A 使 `fly_api/base.pyc` 翻转；`logs/summ37.py` 的 d2 表里那条
          `base.pyc 39/41` 是 Round 36 的**改前**在册读数，不是本轮读数。本轮靶
          `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc 23/24`，唯一 unmatched
          `tick_worker_thread 268/247 j32 t113`；六个 deficit-1 逐条留档
          `logs/g1_landed_d17.jsonl`／`logs/g1_d17_table.txt`（官方尺）。
  - [x] SubTask 37.2: 电池扩到 51／106（`logs/lists37.py`，逐条 `assert len(...)`）：合成侧 = Round 36 的
          44 片 + R36-A 的 7 片（`test_repros/round36_for_loop_dropped/`）；锚点侧 = Round 36 的 105 个
          + 已全匹配的 R36-A 靶 `plugin_fly_data/fly_api/base.pyc`。两条改前基线
          `logs/b51_landed.jsonl`（51 行）、`logs/a106_landed.jsonl`（106 行）均 0 error。改前侧的复用
          前提照旧逐项重证：`r37c.py build` 断言 `mirr_head` 与工作区核文件**字节全等**才用。
  - [x] SubTask 37.3: Round 36 移交项④（崩溃探针制度化＋全 402 名单）落地并给出结论：
          `logs/crashscan37.py` 钩 `_generate_region`（异常被 per-region 兜底吞掉）与
          `_generate_degraded_statements`（降级入口），三分片跑完 **全 402 个语料文件**
          （`logs/scan37_all402.txt` + 三个分片日志）：landed 字节 **0 fatal／0 swallowed／
          0 degradation**。正对照跑在**镜像**（`--core=mirr_pre36`，R36-A 之前的字节，
          `logs/crash37_ctl.py`）上报出 `2x TypeError @ region_ast_generator.py:4824` ＋
          `2x degradation-arm-entered`（`logs/ctl_head.txt`）——探针报不出东西不等于没有东西，
          没有这条正对照整节都不成立。⇒ 剩余 28 个 partial 的缺陷全在判断侧，「异常吞掉一整块」
          的机械因对全池已排除，R36 那族是首例也是孤例。
  - [x] SubTask 37.4: 线 A 代理（`D:/Temp/r37diagA`）在 150 轮上限处终止且**未交 ANALYSIS.md**；
          候选补丁文本从它的 `logs/diagA_mkfix.py` 里恢复。它的读数一律不沿用：`mkfix.py` 的输入是
          **已插桩的** `mirr_probe`，其 `mirr_fix` 臂不等于「landed ＋ 候选」。编排方用
          `r37c.py build --spec=spec37a.json --dst=r37a` 从 landed 字节重建干净臂，§37.9 的每个读数
          都在干净臂上重跑；代理的块级证据（`logs/diagA_dump_orig.txt`：66 块／20 区域，缺失区域
          `@718..820` = B23..B32，B23 前驱集 {19,21}，是 B18 @642 的兄弟）作为线索采纳、由 37.8 的
          stamps 独立证实。
  - [x] SubTask 37.5: 线 B（`D:/Temp/r37diagB/ANALYSIS.md`，已归档）诊断 `matcher :: match 713/689`，
          给出机制（`core/cfg/region_analyzer.py:17290` `_collect_branch_blocks` 遇停止集即停）与候选
          R37-B，并由**它自己的代价门**否证：`Σ|Δ| 1779→2694`、official matched `5649/5746→5626/5746`、
          partial `28→41`、变化文件 better 5 / worse 19 ⇒ NO-GO。**该表是代理私有目录读数，编排方
          未复测**——NO-GO 不需要独立确认，只有发货需要；但它的**基线**经交叉核对为真：它用的
          `5649/5746` 与编排方从 `git show HEAD:pyc_index.json` 求得的 Σmatched／Σfc 完全相同。
          机制线索与等长换位见证留账（37.12），候选不取。
  - [x] SubTask 37.6: G0 电池（不依赖语料）由编排方自建驱动 `logs/g0_37.py`（弃用代理的 `bat_run.py`，
          它把片名弄混过），32 片 = `wit` 7 ＋ `battery` 7 ＋ `ladder` 10 ＋ `ladder2` 8，每片
          显式 `cfile` 编译 → 指定臂反编译 → 重编译 → strict 尺逐函数读 → 同进程异常探针。
          首跑有一行 `DECOMPILE-FAIL` 来自驱动 glob 到的一次陈旧片名（两侧同现、不影响判决，但仍是
          坏探针）；清单重跑见 `logs/g0_wit2_landed.txt`／`logs/g0_wit2_r37a.txt`（7 片，
          改前 `CLEAN=0 DEFECT=7` → 候选 `CLEAN=1 DEFECT=6`）。
  - [x] SubTask 37.7: 根因链：`_if_generate_normal` 的 `[R23-A]` 段（`:16947-16964`）为带 or-extension
          的区域找 elif 链供体，筛选只有①供体是带 `elif_conditions` 的 `IfRegion`、②其 `then_blocks`
          含与 `_r23_or_then` **偏移相等**的块；①缺归属约束，而 `self.region_analyzer.regions` 是
          同时装着**祖先区域**的扁平表 ⇒ 祖先通过筛选，`:16973-16977` 把祖先的
          `elif_conditions/elif_bodies/elif_final_else` 挂到子孙区域并 `_if_generate_elif_chain`。
          原则 2 要求每块唯一主人 ⇒ 子孙「替祖先发射」使祖先侧与该臂相连的整段区域被跳过，
          `tick_worker_thread` 丢的正是 @718..820 那 21 条指令。
  - [x] SubTask 37.8: 判据 **R37-A**（唯一发货项，`logs/spec37a.json`）：供体区域块集若含本区域入口块
          则跳过。只消费块同一性与区域块归属，不读名字／常量／绝对偏移／指令条数／认领历史。
          补丁 1 处编辑、+3 行、243 字节，锚点在 2984324 字节文件中唯一。一手因果证据
          （`logs/stamp37.py` → `logs/g0_stamp_strategy.txt`）：在落地核的镜像副本 `mirr_stamp37` 的
          **新 `continue` 站点**插桩、只跑语料靶文件，命中两行且都带 `would_have_been_accepted=True`
          （改前的偏移测试会接受该供体）：`donor entry=210 donor_blocks=56 cur_entry=612` 与
          `cur_entry=718`。后者即 37.4 独立报出的缺失区域入口；两处拒绝的**联合**效果才是本轮读数，
          不单独归因给其中一处。
  - [x] SubTask 37.9: 门禁严格串行、逐条实测，TALLY 就归档 `.jsonl` 复算并留档。G0：见证
          `+5→0`／`+4→0` 共四片翻正、7 片控制两侧全 CLEAN、32 片里**无一片 Σ|Δ| 上升**、逐片
          0 swallowed／0 degraded。G1（d1+d2 共 17 文件）`SAME=15 IMPROVED=1 REGRESSION=0 MOVED=1
          ERR=0`、全匹配 `a=0 b=1`（IMPROVED 即靶；MOVED 是 `clock_worker [1275,1291,15,480] →
          [1275,1281,10,478]`）。G2′ `SAME=51 ERR=0`（40 条全匹配不变）。G3 `SAME=106 ERR=0`
          （76 条全匹配不变）。**G4 全 402 A/B（sha-first，唯一发货权威）`SAME=400 IMPROVED=1
          REGRESSION=0 MOVED=1 ERR=0`**，整文件全匹配 374 → 375。G4′（`logs/g4prime37_readings.txt`）
          `strategy.pyc 25/27 σ=2 Σ|Δ|=21 → 25/27 σ=2 Σ|Δ|=0`、`realtime_event_source.pyc
          10/12 σ=2 Σ|Δ|=17 → 10/12 σ=2 Σ|Δ|=7`。
  - [x] SubTask 37.10: 落地即复测：`land37.py` 以「同一份 spec 重放 == 被测镜像字节」为准 →
          `applied: 2984324 -> 2984567 bytes, CRLF 48421, BOM=True, equals measured mirror=True`，
          核身份 `bbfe1a414032436921ab → 6b0759b1a0a566a4eb8f`（`logs/core_identity37.txt`）。
          G5 `single`：靶 `24/24 rate=100.00%`，`strategyOK.py` 重生成 13159 字节
          `68c457315b02353f` 与候选臂产物**字节全等**；canary `quotation.pyc 143/143`，产物仍
          183261 字节 `3f2242e73d7fd56a0096`（与 Round 36 收尾值逐字节相同）。G6
          `batch --index pyc_index.json --all --round 37` 402 条读完、`failed_pyc 0`，索引实质差异
          只有 `strategy.pyc` 三个字段（`23→24`／`partial→ok`／`rate→1.0`），其余 402 条仅
          `last_tested_round 36→37`；Σfc 5746→5746、Σmatched 5649→5650、全匹配文件 374→375、
          partial 28→27。零副作用面：G6 之后 `git status --porcelain` 的在册 `M` 只有核／索引／
          `strategyOK.py`／`realtime_event_sourceOK.py`，后两者与候选臂产物各自字节全等
          （`68c457315b02353f`／`b1b282deba63cd16`）⇒ 落地核复现被测臂。G7 见 `OUTCOME.md` §四。
  - [x] SubTask 37.11: 本轮 G0 见证钉成常驻电池 `test_repros/round37_ancestor_elif_or_arm/`
          （4 见证 + 4 控制，`logs/pinbat37.py`；`.py` 入仓、`.pyc` 现地重编，`.gitignore:2` 忽略
          `*.pyc`，与 round36 目录同一做法），落地字节上 `cases=8 CLEAN=8 DEFECT=0`
          （`logs/g0_pinned_on_landed.txt`）。
  - [x] SubTask 37.12: 方法论收获：①诊断代理耗尽轮次时**候选仍可从它的 scratch 脚本恢复**，但恢复后
          必须在干净镜像臂上重建再测——它的臂若叠在已插桩的镜像上，读数一句都不能进记录；
          ②语料级阴性结论必须有**镜像核正对照**背书（37.3），否则「探针没报」与「探针坏了」不可区分；
          ③NO-GO 的候选不必复测，但其**基线**要与编排方自己的独立求和交叉核对，否则一条假否证会
          白白关掉一族；④扁平静态表（`region_analyzer.regions`）作查找域时，「同层」判据的常态是
          **补一条归属约束**，而不是新增形状识别——本轮 3 行即翻转一个文件。
  - [x] SubTask 37.13: 移交 Round 38：①`tick_worker_thread` 同族另一半——同一函数里 `cur_entry=612`
          也命中过一次，且线 A 的 `w2_outer_three_arms` 那片「mangled or-arm」产物形状在候选下 14→14
          未动 ⇒ or 臂形状还有一次要取，入口块归属之外还差臂内容器的表示；②`matcher :: match 713/689`
          （线索见 37.5，先解决排序再谈判据，暴露面 21 函数／13 文件）；③`clock_worker 1275/1281 +6`
          （本轮从 +16 推进 10 条，仍未收口）；④台账继续在册：`decrypt_database_url 295/324`（+29，
          需放弃发射侧）、`events 510/508`（欠定，勿再从 else 归属侧进攻）、`_init_config 86/84`
          （R16 J1 在册反例，受保护勿再取）、`OverNightOrder.__init__ 172/148 −24`（#41，
          `base.pyc` 唯一残余）、#61 汇合块残余 + `r29x_01 <module> 142/138`、等长换位 5 处
          （`fileio_utils::write`／`graph`／`logger`／`scheduler`×2）、`:2118` 附近读 `orelse` 的
          同族读者本轮未动；⑤电池增量：G2′ 用 `reprobat51 + round37 的 8 片 = 59`，
          G3 的 106 个锚点须对 Round 37 落地字节重读作基线。
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
    print('Task 37 header line %d; SubTasks 37.x lines %d'
          % (next(i for i, l in enumerate(_lines, 1) if l.startswith('- [x] Task 37:')),
             sum(1 for l in _lines if 'SubTask 37.' in l)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
