"""Build R21-41c: keep [R8 fix]'s header-landing Continue EXCEPT for the designated natural tail.

Why 41b was wrong and this is right: E1 (in `1bdc3206451cef57`) REPLACED the landed condition
`_be_target == _loop_hdr` with a re-entry-block test, so it suppressed the Continue for every block
whose operand lands on the header - which is what `ipo_stocks_order` needs (measured: it lost
`JUMP_BACKWARD @5582`, broker 125 -> 124/128). The narrow change the evidence supports is an EXCEPTION,
not a replacement: keep the landed behaviour, and skip it only when the block IS the loop's designated
`back_edge_block`, i.e. the natural tail that the [R21-40] analyzer hunk now elects accurately
(`@2000..@2042`, the `time.sleep(0.001)` block whose operand lands on the header `@46`).

Predicted effect (to be measured, not assumed): broker back to 125/128 with `ipo_stocks_order` intact,
`_process_cancel_order` still differing from the original by exactly one byte at co_code offset 1711
(the pass arm's forward-jump target) - so still zero flips, still banked. If the measurement differs
from that, the doc is corrected from the numbers.

usage: python -X utf8 build_cand_r38_R21-41c.py        # writes CAND_r41c_gen.py next to it
"""
import hashlib
import py_compile

SRC = 'D:/Temp/r40/CAND_r41_gen.py'
OUT = 'D:/Temp/r40/CAND_r41c_gen.py'

START = "                                if (_be_target and _be_target is not _loop_hdr"
END = "                                    stmts.append({'type': 'Continue'})"

NEW = """                                # [R21-41c] 保留 [R8 fix] 的既有判据（落点即 header ⇒ 补 Continue），
                                # 只排除一种情形：该块正是循环自己的自然尾——即分析层 [R21-40] 修正
                                # back_edge_block 之后所指向的那块（其实测特征就是「操作数落在 header 上」）。
                                # 自然尾的回边由循环结构本身发射；此处再补一条 Continue 会把这同一条跳转的
                                # 落点从 header 挪到 header 之前的 continue 再入块（指令条数不变、目标变，
                                # judge 读作控制流不同）。实测 _process_cancel_order 的最后一个字节差异就是它。
                                # 其余落点在 header 的载荷回边块保持原样：ipo_stocks_order 需要它
                                # （E1 用「只认再入块」替换判据后该单元少一条 JUMP_BACKWARD，broker 125→124）。
                                _r41c_be = getattr(self._current_loop, 'back_edge_block', None)
                                _r41c_reentry = (_be_target is not None and _be_target is not _loop_hdr
                                                 and getattr(_be_target, 'instructions', None)
                                                 and all(i.opname in ('RESUME', 'NOP', 'CACHE',
                                                                       'PUSH_NULL', 'EXTENDED_ARG',
                                                                       'END_ASYNC_FOR')
                                                         for i in _be_target.instructions)
                                                 and len(_be_target.successors) == 1
                                                 and _loop_hdr in _be_target.successors)
                                if ((_be_target == _loop_hdr and block is not _r41c_be)
                                        or _r41c_reentry):
                                    stmts.append({'type': 'Continue'})"""


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    lines = open(SRC, 'rb').read().split(b'\r\n')
    s = [n for n in range(len(lines)) if lines[n] == START.encode('utf-8')]
    assert len(s) == 1, 'start anchor hits %d' % len(s)
    i = s[0]
    e = [n for n in range(i, i + 20) if lines[n] == END.encode('utf-8')]
    assert len(e) == 1, 'end anchor hits %d' % len(e)
    j = e[0]
    out = lines[:i] + [x.encode('utf-8') for x in NEW.split('\n')] + lines[j + 1:]
    data = b'\r\n'.join(out)
    open(OUT, 'wb').write(data)
    py_compile.compile(OUT, doraise=True)
    print('replaced lines %d..%d with %d; size=%d sha16=%s (src was %s) py_compile=OK'
          % (i + 1, j + 1, len(NEW.split('\n')), len(data), sha16(data), sha16(open(SRC, 'rb').read())))


if __name__ == '__main__':
    main()
