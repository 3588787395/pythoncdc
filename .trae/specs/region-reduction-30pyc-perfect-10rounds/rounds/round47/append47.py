"""Append Round 47 SubTasks to tasks.md byte-exactly (prefix sha/len/CRLF==LF asserted first)."""
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
    '  - [x] SubTask 47.1: 开工靶池沿用 Round 46 落地态实测清单（27 支部分失败文件 `rounds/round46/g1pool46.txt`），'
    '\r\n          电池 143 / 锚点 109 / 全量 544 路径的 a 侧基线沿用 `bat45.jsonl`/`anch45.jsonl`/`round46/g4bB_all.jsonl`'
    '\r\n          （其生成臂 generator 已逐字节核验 = 落地 `b8bfc794dc6c852e7d9c`）。三线并行（线 A log 插件、'
    '\r\n          线 B `fly/data/quote.pyc` 四函数族、线 C 七支 deficit-1）+ 编排方一手 R47-B。',
    '  - [x] SubTask 47.2: 根因 R47-A（线 A 交付、编排方独立复测）—— `IQEngine/plugins/plugin_system_log/__init__.pyc ::'
    '\r\n          DefaultLogger.trade_logs_control`（官方 `[189,190,1,144]`、strict `orig=193 decomp=194`）是**多一条指令**：'
    '\r\n          编辑脚本唯一非平移行 `INSERT (\'JUMP\',420)`。`B12` 头条件跳 `_is_if_false` 取 `_then_succ=B232/_else_succ=B294`，'
    '\r\n          而 `B232` 终结符是 `STORE_FAST`（纯落入、无跳转），`B294` 只是它紧随的顺序后继 ⇒ '
    '\r\n          `_loop_handle_no_exit_successors` 把兄弟块当 else 臂收进 `orelse`，渲染成 `if/elif` 才必须凭空补 `JUMP_FORWARD`；'
    '\r\n          源文本实为两个平铺 if（原则 1 被违反，且 `B294` 被提前记为已发射）。',
    '  - [x] SubTask 47.3: 判据六条合取全读结构事实：① `not _then_is_continue`；② `_else_succ is not block`；'
    '\r\n          ③ `_else_succ ∈ _then_succ.successors`；④ `_then_succ` 终结符 ∉ `FORWARD_JUMP_OPS ∪ BACKWARD_JUMP_OPS`'
    '\r\n          （⇒ ③ 只能由落入成立）；⑤ `_then_succ` 不是任何子区域入口块（臂尾即自身）；'
    '\r\n          ⑥ `_else_succ ∈ self._current_loop.blocks ∧ ∉ self.generated_blocks`。命中 ⇒ 发 `If(test, body)`（无 orelse）、'
    '\r\n          只登记 `_then_succ`、`return` 而不认领 `_else_succ`，发射责任交回循环体顺序归约（原则 2＋4）。'
    '\r\n          反证：真 else 臂的 then 臂末块必以无条件前向跳转跨过 else 臂（④ 假）或其后继集不含 `_else_succ`（③ 假）。',
    '  - [x] SubTask 47.4: 编排方一手候选 R47-B **在 G0 即回归、本轮否证不落地**。靶 `fly/data/quote_handler.pyc ::'
    '\r\n          get_Ashares_local`（官方 `75/77`、`j=0`、`t=24`）：try 体保护段把 `LOAD_FAST returnlist | RETURN_VALUE`'
    '\r\n          切成两块，`_generate_try_body:23536` 遂发 `Expr(returnlist)` + `return None`（多 `POP_TOP/LOAD_CONST None`），'
    '\r\n          新电池 `r47_tryret_witness.py` 落地 `defective=3/15`。折叠臂 `mirr_r47b`（`3fa23dc13fd7f2bc5d48`）'
    '\r\n          把它推到 `7/15`：`r47_01/04/05` 的 `try` 语句整条消失（strict `orig=50 decomp=5`、嵌套 `<listcomp>` MISSING）、'
    '\r\n          对照 `r47_07` 破为 `44/6`，且 stderr 无 `Region-based decompilation exception` ⇒'
    '\r\n          下游结构守卫把「体尾为带值 Return」的 Try 节点静默丢弃，折叠点须换到守卫可接受的表示；'
    '\r\n          三支旧电池（5/4/8 个 code object）在该臂下签名零变化 ⇒ 折叠对无关形状确为惰性，但不足以发货。靶移交 R48。',
    '  - [x] SubTask 47.5: G0 合成见证（`rounds/round47/g047.py`，9 个 code object）落地前 `defective=3/9` → 候选 `1/9`，'
    '\r\n          逐 code object 指令签名 `identical=7 differs=2`（两条 DIFFERS 即见证 `w47_01/w47_08` 本身）；'
    '\r\n          唯一残差 `w47_07`＝then 臂自身是嵌套 if/else（判据 ⑤ 为假），属另一子形状、不声称。'
    '\r\n          G1 池 27 支 `SUM files=27 same=26 gained=1 lost=0`（`UP __init__.pyc 8/10 → 9/10`）。',
    '  - [x] SubTask 47.6: G2′ 电池 143 支 `same=143 gained=0 lost=0`；G3 锚点 109 支 `same=109 gained=0 lost=0`；'
    '\r\n          G4 全量 A/B（544 路径，唯一发货判据）`SUM files=544 same=543 gained=1 lost=0`，'
    '\r\n          sha 变化面 = **1 支产物**（`changed47a.txt`）；G4′（落地前）strict 对变更产物'
    '\r\n          `affected=1 fixed=1 broken=0 changed=0`（`FIXED trade_logs_control [seq_len orig=193 decomp=194]`，'
    '\r\n          同文件其余 8 个 code object 签名与原始相等、`setup` 未被扰动）。',
    '  - [x] SubTask 47.7: 落地＝`spec_r47a.json`（锚点唯一、纯插入 34 行：16 行依据注释 + 18 行代码，'
    '\r\n          插入点为 `_loop_handle_no_exit_successors` 内唯一行 `if _else_is_continue:` 之前）经 `land47.py` 写入并复核：'
    '\r\n          region_ast_generator `b8bfc794dc6c852e7d9c→2a3d522b0ec9e8fe66e4`（len 3 000 351→3 003 323，'
    '\r\n          CRLF 48 620→48 654，裸 LF 0，BOM 保留，`git diff --stat` = 34 插入 / 0 删除）；'
    '\r\n          region_analyzer 逐字节未动 `55a9f61b9b0703063d44`。',
    '  - [x] SubTask 47.8: G5 single：`__init__.pyc matched_functions: 9`、mism 只剩 `setup [320,253,1,293]`，'
    '\r\n          产物唯一改动 `elif os.path.exists(sys_log_path)` → `if …`；落地后五支电池复跑 `1/9, 3/15, 0/5, 0/4, 0/8`'
    '\r\n          （`zg0_landed.json`）。G6 `batch --index pyc_index.json --all --round 47`：402 verified / 0 failed，'
    '\r\n          索引差异 = 402 条轮次戳 + 1 条 `matched_functions 8→9`（同条 `bytecode_match_rate 0.8→0.9`）。'
    '\r\n          G7 stats：375 ok / 27 partial / 0 failed，`matched_functions 5662`、`cumulative_match_rate 98.54%`。',
    '  - [x] SubTask 47.9: 否证与移交——线 A 证明 `setup` 缺的 65 条**不是区域洞**：三条语句前缀 48+9+9=66 删、1 插'
    '\r\n          （`BUILD_TUPLE`），涉事块全部已发射，前缀被三元区域边界的待定操作数队列吞掉'
    '\r\n          （`IF_ELIF_CHAIN@B112` 的 `merge_block=B646` 是后代 `TernaryRegion(entry=B176)` 的内部块，R46-B 判据 ③ 在此为假）；'
    '\r\n          区分事实是「块指令流停在表达式中段」＝操作数栈层，非层内判据。合成电池 `g0tern.py` 在落地字节上复现同一'
    '\r\n          `(cond, cond)` 伪影（`t47_10 69/37`，阴性对照 `17/17`、`24/24`）⇒ 交 R48。'
    '\r\n          另否证同簇假设：`write_logging_thread 113/113 j1`（R46-C1）与 `flyAccount :: init_connection 42/41`（线 D）'
    '\r\n          在 R47-A 下逐字节不变（`fly/logger.pyc` 仍 28/30、`flyAccount.pyc` 仍 21/23）。'
    '\r\n          线 B（`fly/data/quote.pyc` 四函数族）、线 C（七支 deficit-1）交付窗口用尽，scratch `D:/Temp/r47diagB`、'
    '\r\n          `D:/Temp/r47diagC` 与臂留原地，结论并入 Round 48 开工复测。',
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
assert n[:pre_len] == raw, 'append modified the prefix'
assert n.count(b'\r\n') == n.count(b'\n'), 'append introduced bare LF'
