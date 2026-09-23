# -*- coding: utf-8 -*-
"""Append Round 51 SubTasks to tasks.md byte-exactly (prefix bytes asserted after write)."""
import hashlib
import io

P = (r'F:/Downloads/pythoncdc-main/.trae/specs/'
     'region-reduction-30pyc-perfect-10rounds/tasks.md')

raw = io.open(P, 'rb').read()
pre_len = len(raw)
pre_sha = hashlib.sha256(raw).hexdigest()[:20]
pre_crlf = raw.count(b'\r\n')
pre_lf = raw.count(b'\n')
print('before len=%d sha20=%s crlf=%d lf=%d' % (pre_len, pre_sha, pre_crlf, pre_lf))
assert pre_crlf == pre_lf, 'tasks.md has bare LF lines before append'

L = [
    '  - [x] SubTask 51.1: 接手 Round 50 移交的三元链 kwarg 线并**先量其射程**：'
    '\r\n          该线只到 `order_api` 一个文件；改按 Round 50 记录的靶文件逐函数 strict 另找同层事实，'
    '\r\n          靶 `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`'
    '\r\n          （strict `98/123`、官方 `105/119`），四支缺陷逐字：`get_crdt_stock_info seq_len orig=251 decomp=250`、'
    '\r\n          `get_crdt_target_stockinfo 285/284`、`get_crdt_enslosecu_stock_info 350/349`、`etf_basket_order 696/695`'
    '\r\n          ——全部是「恰少 1 条」的长度缺陷而非内容缺陷。落地前产物 `trade_live_brokerOK.py` 2024/2071/2123 三处'
    '\r\n          链尾形如 `elif …: code += \'.SZ\'` 之后紧跟 `while False: pass`，再跟 `stock_out_info = dict()`。',
    '  - [x] SubTask 51.2: 根因三段逐点取证（原则 1「块 = 前导语句＋恰好一个终结子」＋原则 2「每块唯一归属且归属者必须发射」）：'
    '\r\n          ① 源码是 `if … elif … else: pass`（空 else 子句）；② `region_analyzer.py :: _build_elif_region`'
    '\r\n          的 `19138-19139`（`all(self._is_trivial_block(b)) ⇒ inner_else_blocks = []`）把平凡臂整体擦除，'
    '\r\n          垫块既不入本链也不属任何子区域；③ `region_ast_generator.py :: _generate_block_statements_body`'
    '\r\n          的孤立边界 NOP 分支（`44730-44749`）把它作为**兄弟语句**摊平成 `while False: pass`，'
    '\r\n          于是前一臂末不再需要「越过空臂」的出口跳转，re-compile 恰少一条 `JUMP_FORWARD`。'
    '\r\n          结构依据（判据的图面证据方向）：无 `else` 子句时 CPython 3.11 让最后一个测试的落空边直指汇合点，'
    '\r\n          不会留下需要被跳过的中间块——留下这样一块本身就是「源码有一个空 else」的证据。'
    '\r\n          **本轮不动分析侧擦除点**（`_build_elif_region` 的平凡臂擦除是 merge/region 归属的上游依赖，'
    '\r\n          按 Round 49「merge 补全是级联兜底、非单调」的教训须逐站点开证），改在链的发射点按归属收回。',
    '  - [x] SubTask 51.3: 落地 R51-A ＋ R51-B（`_if_generate_elif_chain` 定义 15091 的单站点 `16099-16205`，'
    '\r\n          判据体已写入注释）。R51-A（16099-16140）：链**有** `elif_final_else` 臂且此刻无 `nested_elif_stmts`'
    '\r\n          无 `final_else_stmts` 时，要求该臂全部块只含噪声指令（`RESUME/NOP/CACHE/EXTENDED_ARG/PUSH_NULL`'
    '\r\n          ＋一条 `JUMP_FORWARD|JUMP_ABSOLUTE`）、块非汇合块、臂首块是链最后一个测试（`elif_conditions[-1]`，'
    '\r\n          退化时 `condition_block`）的后继、臂末块以跳转或顺序后继到达 `merge_block`、无区域 entry 落在臂内'
    '\r\n          ⇒ `final_else_stmts = [Pass]` 并把臂块标为已生成（命中 `etf_basket_order`）。R51-B（16141-16205）：'
    '\r\n          链此刻无任何 orelse 内容时按**归属**找回垫块——候选非汇合块、有前驱、全指令皆噪声（连跳转都没有'
    '\r\n          ⇒ 与 R51-A 的「臂体自带出口跳转」互斥）、后继集恰 `{merge}`、未发射、非任何区域 entry、'
    '\r\n          每个前驱要么属本链块集要么其终结子是指向该块的条件跳转且至少一个属后者（这条边即 if/elif 落空边）、'
    '\r\n          满足者唯一；容器逐条择一：`nested_elif_stmts` 恰一条且其 `orelse` 空 ⇒ 写它的 `orelse`，否则写'
    '\r\n          `final_else_stmts`（命中三支 `get_crdt_*`）。两判据全读块同一性／终结子类别／前驱后继关系，'
    '\r\n          不读名字、常量、绝对偏移与指令数。',
    '  - [x] SubTask 51.4: 门禁（严格串行，G4 为唯一发货判据）——G0 十二靶逐函数 strict `trade_live_broker 98/123 → 101/123`'
    '\r\n          （三支 `get_crdt_*` 转 clean，`etf_basket_order` 由 `seq_len 696/695` 转同长 `seq_diff #254`），'
    '\r\n          其余 11 靶缺陷消息逐字未变；14 支最小复现电池 head `MISMATCH=3` → landed `MISMATCH=2`，'
    '\r\n          `r51b_05`（try 包裹的嵌套链＋空 else，`seq_len orig=46 decomp=45`）转 MATCH，`r51a_04`/`r51b_06`'
    '\r\n          逐字未变、无一支转坏。G1 17 支 `SAME=17`、G2′ 143 `SAME=143`、G3 109 `SAME=109`（均零移动）；'
    '\r\n          G4 全量 544 路径 `TALLY SAME=543 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0`、`files fully matched a=484 b=484`，'
    '\r\n          唯一 MOVED 即靶文件，产物 diff `+5/-3`；G4′ `affected=4 fixed=3 broken=0 changed=1`，'
    '\r\n          官方尺可见的改进是 `etf_basket_order` mism 明细 `[693,692,12,431] → [693,693,11,216]`。',
    '  - [x] SubTask 51.5: 落地与收口——G5 落地态 12 靶产物 sha/mism 与臂逐项相同、金丝雀 `fly/data/quotation.pyc`'
    '\r\n          官方 `143/143`／strict `148/150` 逐字不变、`test_repros/round16_sink/run_all.py`'
    '\r\n          `repros=15 MISMATCH=0 MATCH=15 ERROR=0 UNEXPECTED=0`；G6 `batch --index pyc_index.json --all --round 51`'
    '\r\n          402 verified / 0 failed；`pyc_index.json` 仅 402 条 `last_tested_round 49 → 51`、值域零变化'
    '\r\n          （脚本断言「非轮次戳改动行数 = 0」），文件仍纯 CRLF `4553/4553`、无 BOM、`json.dumps` 往返逐字节成立。'
    '\r\n          字节面：`region_ast_generator 2a3d522b0ec9e8fe66e4 → 944c18b3e0807f7139c0`（3 003 323 → 3 010 264 B，'
    '\r\n          ＋107 行，BOM 保留，CRLF 48 654 → 48 761、裸 LF 恒 0），`region_analyzer.py` 逐字节未动'
    '\r\n          （`c644a6ccab745ac6be0e` / 1 687 755 B）；落地经 `spec_r51ab.json` 重放且断言臂＝测量镜像后才写 `core/`。'
    '\r\n          **收益口径如实说明**：三支 `get_crdt_*` 在官方尺本就判为匹配（其 −1 长度差被官方尺跳转容忍吸收），'
    '\r\n          故本轮 G4 `IMPROVED=0`、G7 `stats` 与 Round 49 收口逐字相同（`5665`/`98.59%`），'
    '\r\n          不是 Round 48/49 那种官方 +1 的落地。',
    '  - [x] SubTask 51.6: 否证与移交——**R51-C**（放宽 R51-A 的 `not nested_elif_stmts` 合取、与 R51-B 共用容器）'
    '\r\n          在 12 靶＋14 支电池上逐行逐字与 A＋B 臂相同（两日志仅差 core 路径一行）⇒ 无可测收益、只增命中面，'
    '\r\n          **不落地**（`mk_cand51c_falsified.py`／`g051_c51c_falsified.log`）。移交 Round 52 线 A：'
    '\r\n          `r51b_06`（外层与内层**各有一个空 else**）与 `r51a_04` 仍各差 1 条且改前后逐字相同——内层链收回垫块后'
    '\r\n          外层链的 `nested_elif_stmts[0][\'orelse\']` 已非空，R51-B 的「此刻没有任何 orelse 内容」前置因此闭嘴'
    '\r\n          ⇒ 须把该前置从**全局**改为**逐臂/逐层**判据，先用这两支单证再铺真文件。'
    '\r\n          台账未变项：靶文件 strict 仍余 22 支（整段丢失族 `_process_order 454/399`、`_sync_worker 350/323`、'
    '\r\n          `fund_transfer 123/88`、`market_fund_transfer 94/67`、`get_etf_stock_info 144/117` 与多出族'
    '\r\n          `ipo_stocks_order 1075/1076`、`get_max_amount 201/213`）；Round 50 三元链 kwarg 线'
    '\r\n          （`order_api :: future_order 101/93`、`option_order 83/74`）与同文件 `base_order [target_diff] #136`'
    '\r\n          仍不得并入同一判据。归档 `rounds/round51/`（31 支＋`wit51/` 14 支：落地 spec、三臂生成脚本、'
    '\r\n          G0/G4/G4′/G5/G6/G7 日志、head 与 cand 两侧 jsonl、产物 diff）。起始 HEAD `bc134e10`，'
    '\r\n          门禁跑完前 `git status --porcelain core/ pycdc.py` 为空。',
]
block = ('\r\n' + '\r\n'.join(L) + '\r\n').encode('utf-8')
if not raw.endswith(b'\r\n'):
    block = b'\r\n' + block
out = raw + block
io.open(P, 'wb').write(out)
n = io.open(P, 'rb').read()
print('appended %d bytes -> len=%d sha20=%s crlf=%d lf=%d'
      % (len(block), len(n), hashlib.sha256(n).hexdigest()[:20],
         n.count(b'\r\n'), n.count(b'\n')))
assert n[:pre_len] == raw, 'prefix mutated'
assert n.count(b'\r\n') == n.count(b'\n'), 'mixed endings after append'
print('prefix preserved: byte-equal for first %d bytes' % pre_len)
