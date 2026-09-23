"""Append Round 46 SubTasks to tasks.md byte-exactly (prefix sha/len/CRLF asserted first)."""
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
    '  - [x] SubTask 46.1: 开工靶池实测 landed `cc71dd2d`（27 支部分失败文件，清单 `rounds/round46/g1pool46.txt`），'
    '\r\n          电池/锚点/全量 A/B 基线沿用 Round 45（143 / 109 / 544 路径，a 侧臂 `mirr_r45a` 的 generator 已核验与落地字节等值）。'
    '\r\n          三线并行：线 B（链后兄弟区域，代理）、线 C（等长 MOVE 族，代理）、线 D（`flyAccount :: init_connection`，编排方一手）。',
    '  - [x] SubTask 46.2: 根因 R46-B（发射侧）—— R45-A 只关掉「链的 merge 块被后代 IfRegion 当作 else 臂认领」一格；'
    '\r\n          未关掉的是「merge 块是其后可做完整区域的 ENTRY 块」：补发裸语句只打印前导赋值，'
    '\r\n          块终止符携带的 `if` 连同两臂与整段嵌套体消失（真实靶 `fly/data/quote_handler.pyc :: get_index_stocks_local`'
    '\r\n          链 `merge=B344 ∉ blocks`、`IF_THEN_ELSE entry=B344 parent=IfRegion@B214` 从未进入 `_generate_region`）。'
    '\r\n          合成见证 `r46b_witness.py :: r46b_01_tail_region_at_merge` 与真实靶逐字段同形（落地 strict `orig=56 decomp=33`）。',
    '  - [x] SubTask 46.3: 判据六条合取全读结构事实：owner 存在 ∧ owner 非本链亦非本链之父 ∧ `owner.entry is` 该块 ∧'
    '\r\n          该块 ∈ `owner.blocks` ∧ `id(owner) ∉ _generated_regions` ∧ `owner.blocks ∩ generated_blocks = ∅`；'
    '\r\n          命中则 `_generate_region(owner)` 整区域接在链 result 之后，否则逐字节沿用 R45-A。'
    '\r\n          R45-A 的见证在此判据 ③ 为假 ⇒ 两支 R45-A 电池（4 + 8 个 code object）在本判据下完全惰性。',
    '  - [x] SubTask 46.4: G0 合成见证（三支电池共 17 个 code object，`g0_r46.py`）：落地核 `defective=1/5` → 候选 `0/5`，'
    '\r\n          逐 code object 指令签名 `16 identical / 1 differs`（唯一 DIFFERS 即见证本身）。'
    '\r\n          G1 池 27 支 `SUM files=27 same=26 gained=1 lost=0`（`UP quote_handler.pyc 51/57 -> 52/57`）。',
    '  - [x] SubTask 46.5: G2′ 电池 143 支 `same=143 gained=0 lost=0`（首轮一支 `r2_02_guard_early_return_dec_dec.pyc`'
    '\r\n          记为 `AssertionError(\'empty reading for …\')` ＝读盘瞬时失败行，单独重跑两臂同为 `1/2` 且 mism 逐字段相同，已并回）；'
    '\r\n          G3 锚点 109 支 `same=109 gained=0 lost=0`；G4 全量 A/B（544 路径，唯一发货判据）'
    '\r\n          `SUM files=544 same=543 gained=1 lost=0`，sha 变化面仅 1 支产物。',
    '  - [x] SubTask 46.6: G4′ strict 尺对变更产物：`affected=1 fixed=0 broken=0 changed=1`，'
    '\r\n          唯一 CHANGED 是原本已失败的 `get_index_stocks_local` 换好成色 `seq_len orig=151 decomp=56 → 150`'
    '\r\n          （官方 mism 行 `[150,60,0,92]` 整行消失），两把尺同向变好 ⇒ 发货。'
    '\r\n          落地前先以「仅注释行不同、非注释行逐行相等」的臂 `mirr_r46bA2` 复测得同一组数字，再在发货字节上全部重跑。',
    '  - [x] SubTask 46.7: 落地＝`spec_r46b2.json`（锚点唯一、净插入 28 行）经 `land46.py` 写入：'
    '\r\n          region_ast_generator `e743b6de1d8efc014da8→b8bfc794dc6c852e7d9c`（len 2 997 983→3 000 351，'
    '\r\n          CRLF 48 592→48 620，BOM 保留，裸 LF 0）；region_analyzer 逐字节未动 `55a9f61b9b0703063d44`。'
    '\r\n          G5 single（`quote_handler` 52 matched，金丝雀 `fly/data/quotation` 143/143）＋'
    '\r\n          G6 `batch --index pyc_index.json --all --round 46`（402 verified，0 failed；索引差异＝402 条轮次戳 + 1 条 `51→52`）'
    '\r\n          ＋ G7 stats 375 ok / 27 partial / 0 failed，5661/5746。',
    '  - [x] SubTask 46.8: 否证与移交——线 D 拆两层：R46-D v2（归属层，then 臂无界前向吸收）合成电池 `2/9→1/9`、'
    '\r\n          R46-E（发射层，`_loop_postprocess` 把回边语句折进 then 臂）`2/6→0/6` 且对照逐字节不变，'
    '\r\n          但 **G1 池 27 支 `same=27 gained=0 lost=0` ⇒ 官方尺中性**，本轮不发货；'
    '\r\n          线 C 的 R46-C1 自报 `SAME=26 MOVED=1 IMPROVED=0`（`write_logging_thread` strict 复位、matched 合计不变）同样中性。'
    '\r\n          三者一并交 Round 47（init_connection 需 R46-D＋R46-E 成对命中；`mirr_r46dA`/`mirr_r46d2A` 留调试 print，'
    '\r\n          复用前须由 spec 重建；R46-C1 锚点行号在 R46-B 之后下移 28 行，须对新落地字节重跑 G0/G2′/G3/G4/G4′）。',
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
