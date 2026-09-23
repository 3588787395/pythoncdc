# -*- coding: utf-8 -*-
"""Append Round 49 SubTasks to tasks.md byte-exactly (prefix sha/len/CRLF asserted first)."""
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
    '  - [x] SubTask 49.1: 接手 Round 48 移交的线 A 并**先否证其结论**——`dis` 复核 CPython 3.11.7'
    '\r\n          并不合并同变量 `return` 尾块，手工把两臂各写一遍 `return` 的渲染仍 `seq_len orig=322 decomp=323`'
    '\r\n          （发射侧重复不可能复原原字节面）；真实形状是两臂与函数续段**共同落入**同一尾部 sink 块，'
    '\r\n          该块在 AST 上只能由父区域写一次。再用带打印的镜像核定位阻塞站点：'
    '\r\n          `klinedata :: get_history_new` 的 `H=298 T=312 E=1556` 在 **17012**（`_else_has_external_pred`）'
    '\r\n          绑 `merge=1556`，同文件 `H=154 T=312 E=1556` 在 **17055**（短路链兜底）亦绑 `else_succ`'
    '\r\n          ⇒ 判据必须同时挂两处，单点加合取项会被另一点镜像抵消。',
    '  - [x] SubTask 49.2: 根因 R49-A——`NCPD(312,1556)=None`（then 臂内含 `RETURN_VALUE` 出口块 1350），'
    '\r\n          `_compute_merge_from_jump_targets` 第 1 步只读 `then_succ` **自身**的 `JUMP_FORWARD`（臂出口在更深的'
    '\r\n          块 1548/1550）故亦 `None`，两处兜底把 merge 绑成 `else_succ`；`_collect_branch_blocks(312,1556)`'
    '\r\n          遂沿 then 臂越过真实汇合块 `1678`（`LOAD_FAST kline_data_dict; RETURN_VALUE`，前驱 1548/1550/1674）'
    '\r\n          把它吸入臂内 ⇒ 尾部 `return` 重复发射（臂内 2 条 vs 原处 1 条 `JUMP_FORWARD`）且函数末尾退化为'
    '\r\n          隐式 `return None`。判据四条合取全读结构事实：① `else_succ ∉ then 臂前向闭包`（闭包不越过条件结构块）；'
    '\r\n          ② 候选 `t ∈ 闭包 ∧ t ∉ 结构块 ∧` 终结符属 return/raise 族 `∧` 无正常流后继；③ `t` 有前驱 `p`'
    '\r\n          既不在闭包内也不属结构块，且 `p` 不经闭包即可由 `else_succ` 前向到达；④ 满足 ①..③ 的 `t` 唯一。'
    '\r\n          未命中返回 `None` ⇒ 逐字保留原兜底世界（原则 1 ＋原则 2「归属者必须发射」）。',
    '  - [x] SubTask 49.3: 命中普查与靶子复验（离线把判据套在同一 CFG 上，`w49eval_preland.txt`）：'
    '\r\n          `get_history_new` 的 15 个 if 区域中**恰 1 个**命中（`H=298 → 1678`，唯一候选、唯一闭包外前驱 1674），'
    '\r\n          其余 14 个 `cands=[]`；落地后同址 `merge=1678`。G0 靶文件逐函数 strict `11 → 10` 缺陷，'
    '\r\n          `get_history_new seq_len orig=322 decomp=323 → clean ok`，其余 10 支缺陷消息逐字未变；'
    '\r\n          合成电池 `g049.py`（4 个 code object）两臂 `MISMATCH=1 MATCH=3 ERROR=0` 逐项相同（惰）。',
    '  - [x] SubTask 49.4: 门禁——G1 sha 变化面**仅 1 支**（`g49_changed.txt`＝`IQCommon/api/klinedata.pyc`）；'
    '\r\n          G2′ 143 `same=143 gained=0 lost=0`；G3 109 `same=109 gained=0 lost=0`；'
    '\r\n          G4 全量 544 路径（唯一发货判据）`SAME=543 IMPROVED=1 REGRESSION=0 MOVED=0`，'
    '\r\n          402 索引子集 `SAME=401 IMPROVED=1 REGRESSION=0`，改进项 `klinedata.pyc 40/45 → 41/45`；'
    '\r\n          G4′ strict 尺 `affected=1 fixed=1 broken=0 changed=0`（官方尺可见的真修复，非假 ok）；'
    '\r\n          G5 single `klinedata.pyc 41/45 91.11%`（mism 剩 `_all_bars_of_cache`、`get_all_real_daily_kline`、'
    '\r\n          `get_multiminute_his_data`、`kline_datetime_list`）＋金丝雀 `fly/data/quotation.pyc 143/143 100.00%`'
    '\r\n          ＋`test_repros/round16_sink/run_all.py` `repros=15 MISMATCH=0 MATCH=15 ERROR=0 UNEXPECTED=0`；'
    '\r\n          落地态产物与门禁臂产物逐字节相同。',
    '  - [x] SubTask 49.5: 落地＝`region_analyzer.py` 单文件 3 hunk（新增同层谓词定义 + 两站点改接），'
    '\r\n          按 `spec_r49a.json`/`mkspec49a.py` 派生（锚点唯一性由 build2 断言）：'
    '\r\n          `0e1c4ce1417fe38993ab → c644a6ccab745ac6be0e`，len 1 683 289→1 687 755，'
    '\r\n          CRLF 27 049→27 126（裸 LF 0），无 BOM；`region_ast_generator.py` 逐字节未动 `2a3d522b0ec9e8fe66e4`'
    '\r\n          （BOM 保留）。G6 `batch --index pyc_index.json --all --round 49`：402 verified / 0 failed，'
    '\r\n          索引差异 = 401 条仅轮次戳 + `klinedata.pyc` 一条 `matched_functions 40→41`（同条 rate 0.8889→0.9111）；'
    '\r\n          G7 stats：375 ok / 27 partial / 0 failed，`matched_functions 5665`、`cumulative_match_rate 98.59%`。',
    '  - [x] SubTask 49.6: 边界与移交——本判据只覆盖 `merge = else_succ` 的 2 处兜底，其余 10 处绑定点'
    '\r\n          （16770/16826/16853/16908/16913/16915/16953/17109/17240/17317）未动，后续靶子落在那些站点时须'
    '\r\n          逐站点开证、不得一次全铺（merge 补全是级联兜底，非单调）。同文件 `get_multiminute_his_data 481/482`、'
    '\r\n          `kline_datetime_list 390/391`、`_all_bars_of_cache 230/231` 仍各差 1 条，但其区域内 `cands=[]`'
    '\r\n          ⇒ 非本形状，另找同层事实。第一优先线索仍是 Round 45/46 挂着的链 merge 选取'
    '\r\n          （`_chain_merge_candidates` 的 `len(_non_empty_exits)==1` 分支：已被 `TernaryRegion` 臂认领的候选'
    '\r\n          不得再作链 merge；靶 `order_api :: future_order [101,92,2,36]`、`option_order [83,73,3,39]`）'
    '\r\n          与 `else` 体内 merge 之后尾随块的 `_elif_struct_blocks` 回填。归档 `rounds/round49/`'
    '\r\n          （27 支：spec/生成器/落地脚本、臂两侧 G4 jsonl、G4′ 与 G6 日志、命中普查前后两态、G0 电池三态 json、'
    '\r\n          靶文件 strict 三态清单）。起始 HEAD `6fad2655`，门禁跑完前 `git status --porcelain core/` 为空。',
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
