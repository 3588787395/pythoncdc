# -*- coding: utf-8 -*-
"""diag4 r67: build specs/cand_r67_handler_continue.json from literal anchor/repl pairs."""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
GATE = 'D:/Temp/opencode/r67gate/diag4/'

HELPER = u'''    def _handler_backedge_is_explicit_continue(self, hb) -> bool:
        """[R67-diag4-A try-handler-backedge-explicit-continue] except 处理器纯回边块判定。

        识别条件：正在生成的 TryExceptRegion 的某个 handler body 块 hb 仅由异常清理
        指令（RESUME/NOP/CACHE/PUSH_NULL/POP_TOP/POP_EXCEPT/COPY）加一条无条件
        JUMP_BACKWARD 组成，该回边的目标块恰为当前循环的 header_block（CPython 的
        continue 汇合点），且 hb 本身就是该循环登记的唯一回边块
        （loop.back_edge_block is hb）——循环体内不存在另一个独立收尾回边块。
        CPython 对 `while True: try: return ... except E: pass` 编译出的是 handler 尾
        POP_EXCEPT + JUMP_FORWARD 指向循环尾的独立回边块（探针 c1_pass_true/
        p_true2），只有源码写显式 `continue` 才产生 POP_EXCEPT + JUMP_BACKWARD 直达
        header（探针 s1/c_true2/c_cond）；for 形两形态字节等价（探针 c4_cont_for），
        故本判据在 for 上不产生差异。
        归约方式：handler body 尚无其它语句时，把该纯回边块归约为一条显式控制流
        语句，而不是交给循环结构隐式再生回边——隐式再生会额外物化出 JUMP_FORWARD
        加循环尾 JUMP_BACKWARD 两条指令（realtime_event_source::get_one_event
        22->23、synth s1 18->19 的严格尺 seq_len 缺陷即此形状）。
        AST 映射：ExceptHandler.body 追加 {'type': 'Continue'}，渲染为 `continue`；
        块内无用户语句故不发射其它节点，handler 也不再落 `pass` 兜底。
        """
        if not self._current_loop:
            return False
        _hc_hdr = getattr(self._current_loop, 'header_block', None)
        if _hc_hdr is None or getattr(self._current_loop, 'back_edge_block', None) is not hb:
            return False
        _hc_last = hb.get_last_instruction()
        if (_hc_last is None
                or _hc_last.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                or _hc_last.argval is None):
            return False
        if self.cfg.get_block_by_offset(_hc_last.argval) is not _hc_hdr:
            return False
        _hc_noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'POP_EXCEPT', 'COPY')
        if any(i.opname not in _hc_noise for i in hb.instructions[:-1]):
            return False
        return True

'''

DEF_ANCHOR = (u"    def _if_extract_condition_from_instructions(self, region: IfRegion, "
              u"cond_block: 'BasicBlock', cond_instrs: List) -> Dict[str, Any]:\n")

CALL_ANCHOR = (u"                    _hb_role = self.region_analyzer.get_block_role(hb)\n"
               u"                    if _hb_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):\n")
CALL_REPL = (u"                    _hb_role = self.region_analyzer.get_block_role(hb)\n"
             u"                    if (_hb_role == BlockRole.LOOP_BACK_EDGE and not handler_body\n"
             u"                            and self._handler_backedge_is_explicit_continue(hb)):\n"
             u"                        # [R67-diag4-A] handler 以纯回边块收尾 = 源码显式 continue，\n"
             u"                        # 不是循环的隐式迭代（判据见上面同名方法）。\n"
             u"                        handler_body.append({'type': 'Continue'})\n"
             u"                        self.generated_blocks.add(hb)\n"
             u"                        continue\n"
             + CALL_ANCHOR)

spec = {
    'name': 'cand_r67_handler_continue',
    'file': 'core/cfg/region_ast_generator.py',
    'title': '[R67-diag4-A try-handler-backedge-explicit-continue]',
    'note': ('except 处理器尾块为 POP_EXCEPT+JUMP_BACKWARD->loop header 且该块即循环唯一'
             '登记回边时，发射显式 Continue 而非隐式迭代（get_one_event 严格尺 seq_len 缺陷）。'),
    'edits': [
        {'anchor': DEF_ANCHOR, 'repl': HELPER + DEF_ANCHOR},
        {'anchor': CALL_ANCHOR, 'repl': CALL_REPL},
    ],
}
out = GATE + 'specs/cand_r67_handler_continue.json'
io.open(out, 'w', encoding='utf-8').write(json.dumps(spec, ensure_ascii=False, indent=1) + '\n')
print('wrote', out, 'edits=%d' % len(spec['edits']))
