# -*- coding: utf-8 -*-
"""Annotate the archived G6 log with how completion was established (the batch ran detached,
so the shell exit status is not in the file)."""
import io

P = (r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds'
     r'\rounds\round30\logs\batch_all30.txt')
raw = io.open(P, 'rb').read()
assert b'[402/402]' in raw and raw.count(b'[BATCH] index written back') == 1
assert not any(k in raw for k in (b'Traceback', b'KeyboardInterrupt', b'MemoryError')), 'error in log'
tail = raw.decode('utf-8').splitlines()[-8:]
assert '  cumulative_match_rate: 98.19%' in ' '.join(tail)
nl = b'\r\n' if raw.count(b'\r\n') else b'\n'
if u'G6 完成判据'.encode('utf-8') in raw:
    print('already annotated')
    raise SystemExit
line = ('G6 完成判据：进程在后台分离运行，shell 退出码不写进日志，故完成性只由日志自身证据确立 —— '
        '末条进度标记 [402/402]、"[BATCH] index written back: pyc_index.json" 恰出现 1 次、'
        'Traceback/KeyboardInterrupt/MemoryError 共 0 行、结尾统计块完整打印。')
io.open(P, 'ab').write(nl + line.encode('utf-8') + nl)
print('annotated batch_all30.txt')
