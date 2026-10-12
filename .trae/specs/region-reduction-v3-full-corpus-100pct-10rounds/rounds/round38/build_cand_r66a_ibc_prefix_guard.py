"""Build CANDIDATE_r66a: a fourth-consumer-free, refusal-only guard on the
inline_boolop_chains fold sites inside _if_generate_elif_chain.

Diagnosis basis (measured on mirror D:/Temp/r66, base = banked r38 P1+P2
candidate c4a934d595200c84, panel 12/13, clock_worker delta=-6 hunks=5):

  * The IfRegion@7270 of clock_worker is NEVER dispatched: the probe census
    (inert, product byte-identical) shows zero _generate_region/_generate_if
    events for entry 7270/7216. The arm is rendered by
    _if_generate_elif_chain(region@7186) through the inline_boolop_chains
    path (analyzer records {'blocks': [7248, 7270]} for the elif head):
    every member's non-jump instructions are rebuilt as a conjunct, and
    `for _cb in _chain_blocks[1:]: self.generated_blocks.add(_cb)` marks
    block @7270 generated whole; its 6 leading debug-call instructions are
    dropped by the conjunct filter (POP_TOP noise filter + expression
    reconstructor) and nobody ever builds statements from them
    (prefix_emitted_upto[@7270] == None at end of run).
  * Positive control: stubbing _if_generate_elif_chain only for entry 7186
    makes `system_log.debug('获取重登信号量')` and the nested `if acquire`
    reappear (product -4125) -> the fold is the sole owner of the loss.
  * _discover_predicate_and_chain_forward / _chain_block_condition_instrs /
    _extract_condition_for_elif_block ablate byte-identical (SAME): the
    forward-discovery fallback is NOT the emitter here (purity rejects
    @7270 because of POP_TOP).

Fix = refuse the fold (do not emit anything ourselves) iff a NON-HEAD chain
member carries a statement prefix per the EXISTING cutter
_split_block_condition_prefix that is also NOT yet registered in the
EXISTING monotone ledger prefix_emitted_upto. Pure test blocks return []
from the cutter, so the guard is inert for every other fold in the corpus;
the refused region then flows through the existing un-generated-block walk
(_process_if_blocks -> region dispatch), which is exactly the path the
positive control proved to emit the 6 instructions once.

byte discipline: input starts with UTF-8 BOM, CRLF-only newlines, unique
anchors asserted, py_compile, sha16 reported.

usage: python -X utf8 build_cand_r66a_ibc_prefix_guard.py
"""
import hashlib

SRC = r"D:/Temp/r66/logs/base_cand_generator.py"
DST = r"D:/Temp/r66/DELIVER/CANDIDATE_r66a_region_ast_generator.py"

HELPER = [
    "def _r66a_ibc_chain_has_stmt_prefix(gen, chain_blocks) -> bool:",
    "    \"\"\"[R21-38-r66a] True when a NON-HEAD member of an inline_boolop_chains",
    "    'and'/'or' chain carries a completed-statement prefix that nobody has",
    "    emitted yet (realtime_event_source::clock_worker: the fused block",
    "    @7270..@7370 = debug CALL + `acquire(...) is False` test, loss (A),",
    "    the 6 instructions @7270..@7308 absent from the product).",
    "",
    "    The ibc fold in _if_generate_elif_chain reads every chain member ONLY",
    "    as a conjunct and marks blocks[1:] generated, so a member with a",
    "    leading statement loses that statement. Facts read: the existing",
    "    stack-depth cutter _split_block_condition_prefix (AssertRegion/",
    "    LoopRegion R23-B/ternary already consume it; it returns [] for a pure",
    "    test block, hence this guard is inert for every fold the corpus does",
    "    today on prefix-free chains) and the existing monotone ledger",
    "    prefix_emitted_upto (offsets already emitted by another consumer do",
    "    not refuse the fold). No new predicate, no offsets, no names.",
    "    Refuse-only: this guard never emits, so double emission is",
    "    structurally impossible from here; the emitted-by-nobody blocks",
    "    return to the un-generated walk which is their only remaining owner.",
    "    \"\"\"",
    "    for _cb in list(chain_blocks or [])[1:]:",
    "        try:",
    "            _pfx = gen._split_block_condition_prefix(_cb)",
    "        except Exception:",
    "            return False",
    "        if not _pfx:",
    "            continue",
    "        _upto = gen.prefix_emitted_upto.get(_cb, -1)",
    "        if any(i.offset > _upto for i in _pfx):",
    "            return True",
    "    return False",
    "",
]

ANCHOR_MODULE = b"def _r52_m1_undispatched_struct_entries(gen, blocks):"

# fold site 1 (primary elif arm): 12-space indent
OLD1 = [
    "                _inline_chain_info = None",
    "            if _inline_chain_info:",
    "                _chain_blocks = _inline_chain_info['blocks']",
]
NEW1 = [
    "                _inline_chain_info = None",
    "            if (_inline_chain_info",
    "                    and _r66a_ibc_chain_has_stmt_prefix(",
    "                        self, _inline_chain_info.get('blocks') or [])):",
    "                # [R21-38-r66a] a chain member carries leading statements:",
    "                # folding it into the elif test would mark its block",
    "                # generated while the prefix is emitted by nobody; refuse",
    "                # the fold and let the region walk below reduce it instead.",
    "                _inline_chain_info = None",
    "            if _inline_chain_info:",
    "                _chain_blocks = _inline_chain_info['blocks']",
]

# fold site 2 (last-elif arm): 20-space indent
OLD2 = [
    "                    _inline_chain_info = getattr(region, 'inline_boolop_chains', {}).get(id(_last_elif_cond_block))",
    "                    if _inline_chain_info:",
]
NEW2 = [
    "                    _inline_chain_info = getattr(region, 'inline_boolop_chains', {}).get(id(_last_elif_cond_block))",
    "                    if (_inline_chain_info",
    "                            and _r66a_ibc_chain_has_stmt_prefix(",
    "                                self, _inline_chain_info.get('blocks') or [])):",
    "                        # [R21-38-r66a] same refusal as the primary elif arm site",
    "                        _inline_chain_info = None",
    "                    if _inline_chain_info:",
]


def main():
    raw = open(SRC, 'rb').read()
    assert raw.startswith(b'\xef\xbb\xbf'), 'missing UTF-8 BOM'
    assert b'\n' not in raw.replace(b'\r\n', b''), 'lone LF found'
    lines = raw.split(b'\r\n')
    print('base sha16', hashlib.sha256(raw).hexdigest()[:16], 'lines', len(lines))

    def find(prefix_bytes):
        hits = [n for n, ln in enumerate(lines) if ln.startswith(prefix_bytes)]
        assert len(hits) == 1, 'anchor %r hits=%d' % (prefix_bytes[:60], len(hits))
        return hits[0]

    def splice(old, new, tag):
        ob = [x.encode('utf-8') for x in old]
        hits = [n for n in range(len(lines) - len(ob) + 1)
                if lines[n:n + len(ob)] == ob]
        assert len(hits) == 1, '%s anchor hits=%d (must be unique)' % (tag, len(hits))
        n = hits[0]
        return n, lines[:n] + [x.encode('utf-8') for x in new] + lines[n + len(old):]

    n = find(ANCHOR_MODULE)
    lines = lines[:n] + [x.encode('utf-8') for x in HELPER] + lines[n:]

    _, lines = splice(OLD1, NEW1, 'fold-site-1')
    _, lines = splice(OLD2, NEW2, 'fold-site-2')

    out = b'\r\n'.join(lines)
    open(DST, 'wb').write(out)
    print('candidate sha16', hashlib.sha256(out).hexdigest()[:16])
    import py_compile
    py_compile.compile(DST, doraise=True)
    print('py_compile OK ->', DST)


main()
