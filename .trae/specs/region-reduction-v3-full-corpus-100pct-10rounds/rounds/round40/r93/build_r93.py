# -*- coding: utf-8 -*-
"""build_r93.py — byte-level builder for FIX_R21-64 (Half 1: analyzer duplicated-while
test chain assembly). Regenerates the candidate region_analyzer.py from the LANDED bytes
(repo copy in D:/Temp/r93) byte-exactly, CRLF+ BOM preserved, asserting unique anchors and
no \\r\\r\\n. Installs the candidate into the mirror core/ for testing and copies to DELIVER.

Usage: python -X utf8 build_r93.py [half]   half in {1,2,all}. Default all (currently 1).
"""
import sys, os, shutil, py_compile

MIRROR = 'D:/Temp/r93'
REPO   = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
ANAL   = 'core/cfg/region_analyzer.py'
GENT   = 'core/cfg/region_ast_generator.py'

def read_lines(path):
    raw = open(path, 'rb').read()
    assert raw[:3] == b'\xef\xbb\xbf', 'missing BOM: ' + path
    text = raw[3:].decode('utf-8')
    lines = text.split('\r\n')
    assert raw.count(b'\r\r\n') == 0
    return lines

def write_lines(path, lines):
    body = '\r\n'.join(lines)
    out = b'\xef\xbb\xbf' + body.encode('utf-8')
    assert out.count(b'\r\r\n') == 0
    open(path, 'wb').write(out)
    # compile check
    py_compile.compile(path, doraise=True)

def find1(lines, needle):
    idxs = [i for i, l in enumerate(lines) if l == needle]
    assert len(idxs) == 1, 'anchor not unique (%d): %r' % (len(idxs), needle[:60])
    return idxs[0]

PREDICATE_METHOD = '''    def _r2164_duplicated_test_predicate(self, loop: 'LoopRegion') -> bool:
        """[R21-64] Predicate P: a while whose test CPython duplicated. True iff loop
        header receives (a) a FORWARD conditional jump from a block outside loop.blocks
        (entry-copy leg) AND (b) a BACKWARD conditional jump from a block inside
        loop.body_blocks (latch-copy leg). Read off CFG block data only: terminator
        opcode class, conditional_successors membership, region block/body membership.
        No names, no offsets, no counters, no thresholds."""
        hdr = loop.header_block
        if hdr is None or loop.condition_block is None:
            return False
        own = {b.start_offset for b in (loop.blocks or ())}
        body = {b.start_offset for b in (loop.body_blocks or ())}
        fwd_out = False
        bwd_in = False
        for b in self.cfg.get_blocks_in_order():
            li = b.get_last_instruction()
            if not li or li.argval is None or hdr not in b.conditional_successors:
                continue
            if li.opname in FORWARD_CONDITIONAL_JUMP_OPS and b.start_offset not in own:
                fwd_out = True
            elif li.opname in BACKWARD_CONDITIONAL_JUMP_OPS and b.start_offset in body:
                bwd_in = True
            if fwd_out and bwd_in:
                break
        return fwd_out and bwd_in

    def _r2164_purge_latch_legs(self, loop: 'LoopRegion',
                                boolop_region: 'BoolOpRegion') -> None:
        """[R21-64 Half 2] A duplicated while test's LATCH copy is the mirror of the
        ENTRY copy already folded into boolop_region.op_chain. Its legs live inside
        loop.body_blocks and would otherwise be emitted as body statements. Remove them
        from the body sequence at identification time. Proof of sameness, not preference:
        a body block is a latch leg iff it carries no STORE and either
          (a) it ends in a conditional jump (forward or backward) and its loaded names are
              a non-empty subset of the assembled condition's loaded names — the same test
              recomputed at the back edge; or
          (b) it holds no load/store/call of its own (pure jump / noise), i.e. the latch
              chain's exit stub.
        The body-start header is never a leg: it also carries the loop body's real
        statement, so its loads are not a subset of the condition's. Regions consisting
        solely of purged legs are deregistered (每块唯一归属). Read only block opcode
        classes, conditional successors and region membership — no names/offsets/counts.
        """
        hdr = loop.header_block
        cond_vars = set()
        for cb, _ in (getattr(boolop_region, 'op_chain', None) or []):
            for i in cb.instructions:
                if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF') and i.argval:
                    cond_vars.add(i.argval)
        LOAD_OPS = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
        STORE_OPS = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                     'STORE_ATTR', 'STORE_SUBSCR')
        JUMP_OPS = ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'NOP')
        to_purge = []
        for b in list(loop.body_blocks or []):
            if b is hdr:
                continue
            li = b.get_last_instruction()
            eff = [i for i in b.instructions if i.opname not in NOISE_OPS]
            loads = {i.argval for i in eff if i.opname in LOAD_OPS and i.argval}
            has_store = any(i.opname in STORE_OPS for i in eff)
            if has_store:
                continue
            is_leg = (li is not None
                      and li.opname in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS)
                      and bool(loads) and loads <= cond_vars)
            is_stub = (not loads
                       and all(i.opname in NOISE_OPS or i.opname in JUMP_OPS for i in eff))
            if is_leg or is_stub:
                to_purge.append(b)
        if not to_purge:
            return None
        purge_set = set(to_purge)
        for b in to_purge:
            loop.body_blocks = [x for x in (loop.body_blocks or []) if x is not b]
            try:
                loop.blocks.discard(b)
            except Exception:
                pass
            # re-claim the latch leg under the condition BoolOpRegion (the latch copy IS
            # the condition's duplicate), so no ancestor loop emits it as a statement.
            boolop_region.blocks.add(b)
            self.block_to_region[b] = boolop_region
        # deregister regions wholly made of purged latch blocks
        wholly = []
        for r in list(self.regions):
            if r is loop or r is boolop_region:
                continue
            blks = set(getattr(r, 'blocks', None) or ())
            if blks and blks <= purge_set:
                wholly.append(r)
        for r in wholly:
            if r in self.regions:
                self.regions.remove(r)
            for b in set(getattr(r, 'blocks', None) or ()):
                if self.block_to_region.get(b) is r:
                    del self.block_to_region[b]
            parent = getattr(r, 'parent', None)
            if parent is not None and r in (parent.children or []):
                parent.children.remove(r)
        return None

'''.split('\n')

NEW_METHOD = '''    def _detect_duplicated_while_test_chain(self, cond_block: BasicBlock,
                                            loop: 'LoopRegion') -> Optional[List[Tuple[BasicBlock, str]]]:
        """[R21-64] CPython 3.11 lays a `while <BoolOp>:` test out TWICE: an entry copy
        above the body whose legs jump FORWARD to the body-start header, and a latch copy
        below the body whose legs jump BACKWARD to that same header. Assemble the single
        mixed `or`-head + `and`-tail condition chain [(or-leg,'or')..., (and-leg,'and')...]
        for such a duplicated test, or None.

        [识别条件 P] loop header 同时收到 (a) 一条来自 loop 自身块集之外的**正向**条件跳转
        （entry-copy 腿，真出口=header）与 (b) 一条来自 loop body_blocks 之内的**反向**条件
        跳转（latch-copy 腿）。二者齐备 ⇒ 该 while 的短路测试被复制。
        [归约方式] 自 cond_block 沿 fall-through 收集全部「正向条件跳转目标==header」的腿
        （or 头，≥2，均以真边进体）；随后自末条 or 腿的 fall-through 进入合取尾，逐腿收集
        「正向条件跳转目标==循环出口」的腿（and 尾），出口一致性依 [R21-13] 同一事实双向
        证明：各尾腿出口两两经纯跳转块等价（_is_equivalent_exit_block），且落在 body/own 之外；
        当某尾腿的 fall-through（可经若干纯跳转块）抵达 header（真路径入体）即闭合。
        合法性由结构事实决定而非归属：仅吸收「不在 body_blocks 且正向条件跳转目标恰为
        header（or 头）或等价循环出口（and 尾）」的腿；吸收跳到他处的腿会把测试移出循环，
        禁止——这正是 conjunctive 尾必须走出口一致判据、or 头必须走 header 判据的原因。
        [C1] 只读块末 opcode 族 / conditional_successors / block_to_region 归属 / body_blocks /
        header 与循环出口的等价关系；零名字、零常量、零偏移阈值、零计数器、跨层仅用 header
        身份与 body 成员关系。
        [C2] P 不成立或任一结构闭合校验失败即返回 None，调用方回退既有 walk，行为逐字节不变。
        [C3] 无状态、无副作用、单出口。
        """
        hdr = loop.header_block
        if hdr is None or cond_block is None:
            return None
        own = {b.start_offset for b in (loop.blocks or ())}
        body = {b.start_offset for b in (loop.body_blocks or ())}
        if not self._r2164_duplicated_test_predicate(loop):
            return None

        def _fallthrough(b, jt_off):
            for s in b.conditional_successors:
                if s.start_offset != jt_off:
                    return s
            return None

        def _reaches(src, target):
            # 沿单后继的纯跳转/噪声块上溯，判断 src 是否抵达 target。
            seen = set()
            stack = [src]
            while stack:
                cur = stack.pop()
                if cur is target:
                    return True
                if cur is None or id(cur) in seen:
                    continue
                seen.add(id(cur))
                succs = list(cur.successors)
                if len(succs) != 1:
                    continue
                nxt = succs[0]
                if nxt is target:
                    return True
                eff = [i for i in nxt.instructions if i.opname not in NOISE_OPS]
                if eff and not all(i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD')
                                   for i in eff):
                    continue
                stack.append(nxt)
            return False

        # ── or 头：自 cond_block 收「正向条件跳转目标==header」的连续腿 ──
        or_head: List[Tuple[BasicBlock, str]] = []
        visited = set()
        cur = cond_block
        tail_entry = None
        while cur is not None and cur.start_offset not in visited:
            li = cur.get_last_instruction()
            if (not li or li.argval is None
                    or li.opname not in FORWARD_CONDITIONAL_JUMP_OPS):
                return None
            if self.cfg.get_block_by_offset(li.argval) is not hdr:
                break  # 离开 or 头，进入合取尾
            if 'TRUE' not in li.opname:
                return None  # or 腿必须真边进体（目标=header）
            or_head.append((cur, 'or'))
            visited.add(cur.start_offset)
            succs = list(cur.conditional_successors)
            if len(succs) != 2:
                return None
            ft = _fallthrough(cur, li.argval)
            if ft is None or ft.start_offset in visited or ft.start_offset in body:
                tail_entry = None
                break
            tail_entry = ft
            cur = ft
        if len(or_head) < 2 or tail_entry is None:
            return None
        # ── and 尾：合取腿正向条件跳转目标==循环出口，出口两两等价，真路径入体闭合 ──
        and_tail: List[Tuple[BasicBlock, str]] = []
        cur = tail_entry
        exit_ref = None
        while cur is not None and cur.start_offset not in visited:
            if cur.start_offset in body or cur.start_offset == hdr.start_offset:
                return None
            li = cur.get_last_instruction()
            if (not li or li.argval is None
                    or li.opname not in FORWARD_CONDITIONAL_JUMP_OPS):
                return None
            tgt = self.cfg.get_block_by_offset(li.argval)
            if tgt is None or tgt is hdr:
                return None
            if tgt.start_offset in own or tgt is loop.condition_block:
                return None
            if exit_ref is None:
                exit_ref = tgt
            elif not self._is_equivalent_exit_block(tgt, exit_ref):
                return None
            and_tail.append((cur, 'and'))
            visited.add(cur.start_offset)
            succs = list(cur.conditional_successors)
            if len(succs) != 2:
                return None
            ft = _fallthrough(cur, li.argval)
            if ft is None or ft.start_offset in visited:
                return None
            if _reaches(ft, hdr):
                break  # 真路径入体，合取尾闭合
            if ft.start_offset in body:
                return None
            cur = ft
        if not and_tail:
            return None
        return or_head + and_tail

'''.split('\n')

def apply_half1(anal_lines, purge=True):
    lines = list(anal_lines)
    # 1) insert the new method before _detect_while_boolop_forward_chain def
    anchor_def = "    def _detect_while_boolop_forward_chain(self, cond_block: BasicBlock, loop: LoopRegion, BOOLOP_CHAIN_JUMPS) -> Optional[List[Tuple[BasicBlock, str]]]:"
    i = find1(lines, anchor_def)
    lines[i:i] = PREDICATE_METHOD + NEW_METHOD
    # 2) insert the call before the forward_chain line
    anchor_call = "        forward_chain = self._detect_while_boolop_forward_chain(cond_block, loop, BOOLOP_CHAIN_JUMPS)"
    j = find1(lines, anchor_call)
    ins = [
        "        _dup_chain = self._detect_duplicated_while_test_chain(cond_block, loop)",
        "        if _dup_chain and len(_dup_chain) >= 2:",
        "            return _dup_chain",
    ]
    lines[j:j] = ins
    # 3) Step 5: skip the recheck-variable guard-trim for a duplicated-test loop so the
    #    full or-head+and-tail chain survives (its conjunctive legs recompute only in the
    #    latch copy, which the header-only traversal would otherwise mistake for spurious).
    anchor_wt = "                    region.is_while_true = False"
    k = find1(lines, anchor_wt)
    if purge:
        lines[k + 1:k + 1] = [
            "                    if self._r2164_duplicated_test_predicate(region):",
            "                        self._r2164_purge_latch_legs(region, boolop_region)",
            "                        continue",
        ]
    else:
        lines[k + 1:k + 1] = [
            "                    if self._r2164_duplicated_test_predicate(region):",
            "                        continue",
        ]
    return lines

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    purge = (mode != 'half1')
    src_anal = os.path.join(REPO, ANAL)  # landed bytes (repo == landed, verified)
    assert read_lines(src_anal)
    lines = read_lines(src_anal)
    new_lines = apply_half1(lines, purge=purge)
    tag = 'R21-64a_half1' if not purge else 'R21-64a'
    cand = os.path.join(MIRROR, 'DELIVER', 'region_analyzer_%s.py' % tag)
    write_lines(cand, new_lines)
    # install into mirror for testing
    dst = os.path.join(MIRROR, ANAL)
    write_lines(dst, new_lines)
    import hashlib
    h = hashlib.sha256(open(dst, 'rb').read()).hexdigest()[:16]
    print('mode', mode, 'installed analyzer', dst, 'sha16', h)
    print('lines', len(new_lines))

if __name__ == '__main__':
    main()
