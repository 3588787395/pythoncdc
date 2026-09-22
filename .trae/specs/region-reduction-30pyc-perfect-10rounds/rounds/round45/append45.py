"""Append Round 45 SubTasks to tasks.md byte-exactly (prefix sha/len/CRLF asserted first)."""
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
    '  - [x] SubTask 45.1: 承接 Round 44 移交线索 3（生成器侧「兄弟块起于前一守卫区域的 merge 块」），'
    '\r\n          按纯发射侧形状排查命中 `IQCommon/strategy/wizard_quant_api.pyc :: <module>.region_mean_desicion`'
    '\r\n          （strict `seq_len orig=51 decomp=52`，官方 `50/53`）。`probe45e.py` 区域转储在合成见证与真实靶上逐字段同形：'
    '\r\n          链 `merge=B250` 而 `B250 ∉ region.blocks`，内层 `IF entry=B114 else=[B250]` 认领它'
    '\r\n          （真实靶同形：链 `merge=B268`、内层 `IF entry=B112 then=[B264] else=[B268]`）。',
    '  - [x] SubTask 45.2: 根因 R45-A（发射侧）—— 链的 merge 块被链内某个后代 IfRegion 取得归属后，'
    '\r\n          链的 elif 发射路径只读 elif_conditions/elif_bodies/elif_final_else 不读 merge_block，'
    '\r\n          而被链吞并的内层区域又不独立发射自己的 else 臂 ⇒ 归属者不发射（原则 2 的发射责任空档）。'
    '\r\n          判据五条合取全读结构事实：后代认领 ∧ 链内有块以正常后继指向它 ∧ 非隐式 return None 块 ∧'
    '\r\n          偏移未登记 ∧ 未经 trailing_return/_r57/_r91 任一路径承担。',
    '  - [x] SubTask 45.3: G0 合成见证（`r45e`，4 个 code object + 7 支对照函数＝8 个 code object）：'
    '\r\n          落地核 `defective=1/4` → 候选 `0/4`，链尾 `return False` 复位；'
    '\r\n          对照电池两臂产物 `BYTE-IDENTICAL products`（候选在 8 个 code object 上完全惰）。',
    '  - [x] SubTask 45.4: G1 池 18 支 `SAME=17 GAINED=1 LOST=0`（`UP wizard_quant_api.pyc 50/53 -> 51/53`）；'
    '\r\n          G2′ 电池 143 支 `same=143 gained=0 lost=0`；G3 锚点 109 支 `same=109 gained=0 lost=0`（本轮无缺行）。',
    '  - [x] SubTask 45.5: G4 全量 A/B（544 路径＝402 索引 + 142 电池/锚点补充 + 4 支 G0 见证，唯一发货判据）'
    '\r\n          `SUM files=544 same=539 gained=1 lost=0`，sha 变化面仅 2 支；G4′ strict 尺 '
    '\r\n          `affected=2 fixed=1 broken=0 changed=1`，唯一 CHANGED 是原本已失败的 `get_index_stocks_local`'
    '\r\n          换好成色（发射 56→60 条、官方 mism 跳转差 j=5→0），非回归。',
    '  - [x] SubTask 45.6: 落地＝单文件单处插入并按 spec 派生（`mkspec45.py` 断言锚点唯一、插入 29 行）：'
    '\r\n          region_ast_generator d4c430303a5d2b63753d→e743b6de1d8efc014da8（len 2 995 945→2 997 983，'
    '\r\n          CRLF 48 563→48 592，BOM 保留，裸 LF 0）；region_analyzer 逐字节未动 55a9f61b9b0703063d44。',
    '  - [x] SubTask 45.7: G5 single（`wizard_quant_api` 51/53，金丝雀 `fly/data/quotation` 143/143）'
    '\r\n          + G6 `batch --index pyc_index.json --all --round 45`（402 verified，0 failed）'
    '\r\n          + G7 stats 375 ok / 27 partial / 0 failed，5660/5746；索引审计仅 1 条漂移；'
    '\r\n          Round 44 的 5 支 sha 变化产物本轮补入库；写 rounds/round45/OUTCOME.md 并移交 Round 46'
    '\r\n          （merge 块被后代 Loop/Try 认领的同邻域残余、`get_index_stocks_local` 剩余 91 条、'
    '\r\n          四条代理诊断线 A/B/C/D 耗尽轮次未交结论但 scratch 目录在盘）。',
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
