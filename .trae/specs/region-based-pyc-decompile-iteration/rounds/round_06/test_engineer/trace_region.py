"""聚焦诊断：dict 构造区域在真实流水线中的跨块传递情况。

只打印三类事件，避免全量指令噪声：
  OPEN  : BUILD_MAP 0（dict 构造区域开启）
  ADD   : MAP_ADD 执行后的 Dict 键数与该块的栈深
  CLOSE : 三元区域归约

用法: D:/Python/python.exe trace_region.py <pyc路径>
"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.ast_generator_v2 import ExpressionReconstructor

_orig = ExpressionReconstructor._process_instruction
_orig_reset = ExpressionReconstructor.reset
_orig_close = ExpressionReconstructor._close_ternary_region

_state = {'batch': 0}


def patched(self, instr):
    before = len(self.stack)
    _orig(self, instr)
    op = instr.opname
    if op == 'BUILD_MAP':
        print('  OPEN  b%-3d off=%-4d arg=%s  stack %d->%d'
              % (_state['batch'], getattr(instr, 'offset', -1),
                 instr.arg, before, len(self.stack)))
    elif op == 'MAP_ADD':
        top = self.stack[-1] if self.stack else None
        n = (len(top.get('keys', []))
             if isinstance(top, dict) and top.get('type') == 'Dict' else -1)
        print('  ADD   b%-3d off=%-4d  stack %d->%d  dict.keys=%s'
              % (_state['batch'], getattr(instr, 'offset', -1),
                 before, len(self.stack), n))
    elif op == 'STORE_FAST' or op == 'RETURN_VALUE':
        if before:
            top = self.stack[-1] if self.stack else None
            if isinstance(top, dict) and top.get('type') == 'Dict':
                print('  USE   b%-3d off=%-4d %-14s dict.keys=%d'
                      % (_state['batch'], getattr(instr, 'offset', -1), op,
                         len(top.get('keys', []))))


def patched_reset(self):
    _state['batch'] += 1
    _orig_reset(self)


def patched_close(self, instr):
    _orig_close(self, instr)
    print('  CLOSE b%-3d off=%-4d -> IfExp' % (_state['batch'],
                                               getattr(instr, 'offset', -1)))


ExpressionReconstructor._process_instruction = patched
ExpressionReconstructor.reset = patched_reset
ExpressionReconstructor._close_ternary_region = patched_close


def main():
    from pycdc import decompile_pyc
    src = decompile_pyc(sys.argv[1], use_cfg=True)
    i = src.find('def save(')
    print('--- 反编译 save ---')
    print(src[i:i + 600] if i >= 0 else 'NOT FOUND')


if __name__ == '__main__':
    main()
