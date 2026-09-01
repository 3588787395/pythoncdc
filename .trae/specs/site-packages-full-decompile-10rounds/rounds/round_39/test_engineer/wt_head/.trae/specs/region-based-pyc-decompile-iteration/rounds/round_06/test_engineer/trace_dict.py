"""追踪 dict 字面量构造：记录每次 MAP_ADD 时 dict 的键数量，定位丢失点。

打桩 ExpressionReconstructor._process_instruction，在 MAP_ADD 后打印
栈上 Dict 节点的键数量；同时在栈深度被清空时告警。
"""
import sys
import types
import marshal

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.ast_generator_v2 import ExpressionReconstructor

_orig = ExpressionReconstructor._process_instruction
_state = {'last_depth': 0, 'map_add': 0, 'resets': 0}


def patched(self, instr):
    op = getattr(instr, 'opname', '')
    before = len(self.stack)
    _orig(self, instr)
    after = len(self.stack)
    if op == 'MAP_ADD':
        _state['map_add'] += 1
        top = self.stack[-1] if self.stack else None
        n = len(top.get('keys', [])) if isinstance(top, dict) and top.get('type') == 'Dict' else -1
        print('  MAP_ADD #%-2d  off=%-4s  depth %d->%d  dict.keys=%d'
              % (_state['map_add'], getattr(instr, 'offset', '?'), before, after, n))
    # 栈被清空（非因 POP/STORE 等正常消费）
    if before >= 3 and after == 0 and op not in ('RETURN_VALUE', 'STORE_FAST', 'STORE_NAME'):
        _state['resets'] += 1
        if _state['resets'] <= 5:
            print('  *** STACK RESET at off=%s op=%s  depth %d->%d'
                  % (getattr(instr, 'offset', '?'), op, before, after))


ExpressionReconstructor._process_instruction = patched


def main():
    pyc = ROOT + r'\site-packages\IQEngine\account\order.pyc'
    with open(pyc, 'rb') as f:
        f.read(16)
        orig = marshal.load(f)

    def find(co, name, out):
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                if c.co_name == name:
                    out.append(c)
                find(c, name, out)

    o = []
    find(orig, 'save', o)
    co = o[0]

    import dis
    ins = list(dis.get_instructions(co))
    print('原始 save() %d 条指令' % len(ins))
    print('--- 单独喂 save() 的指令序列 ---')
    r = ExpressionReconstructor()
    for x in ins:
        r._process_instruction(x)
    print('最终栈深度:', len(r.stack))
    if r.stack:
        top = r.stack[-1]
        if isinstance(top, dict) and top.get('type') == 'Dict':
            print('最终 dict 键数:', len(top.get('keys', [])))


if __name__ == '__main__':
    main()
