# -*- coding: utf-8 -*-
"""Line-trace _generate_ternary while decompiling one pyc."""
import sys, io, os
sys.path.insert(0, '.')
import h62
pycdc = h62._load_arm(sys.argv[1])
import core.cfg.region_ast_generator as G
tgt = os.path.normcase(os.path.abspath(G.__file__))
log = []
WANT = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else {'_generate_ternary'}


def tr(frame, event, arg):
    if event != 'call':
        return None
    fn = os.path.normcase(os.path.abspath(frame.f_code.co_filename))
    if fn != tgt:
        return None
    if frame.f_code.co_name not in WANT:
        return None

    def local(frame, event, arg):
        if event == 'line':
            log.append(frame.f_lineno)
        elif event == 'return':
            log.append('RET@%s -> %s' % (frame.f_lineno, repr(arg)[:200]))
        elif event == 'call':
            if frame.f_code.co_name in WANT:
                return local
        return local

    log.append('CALL %s' % frame.f_code.co_name)
    return local


out = pycdc.decompile_pyc(sys.argv[2])
sys.settrace(None)
io.open('trace_gt.txt', 'w', encoding='utf-8').write('\n'.join(map(str, log)))
print('log entries', len(log))
for e in log:
    print(e)
