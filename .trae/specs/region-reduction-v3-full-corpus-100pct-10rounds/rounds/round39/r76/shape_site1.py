"""Settle the @7164 site shape by compile() on 3.11.7 (rule 5).

usage: python -X utf8 work/shape_site1.py <S1|S2|S3>
  S1 = flat `(A and B) or C` + @7492 as sequential continuation   (hypothesised true source)
  S2 = current best product shape (nested A / `if B or C: pass` / elif D / else @7492)
  S3 = flat fold but @7492 still rendered as E's else arm
"""
import dis
import marshal
import sys

PYC = (r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/"
       r"IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc")
DROP = ('NOP', 'CACHE', 'EXTENDED_ARG')
HEAD = '''
def f(self, now_date, pre_before_trading, before_trading, now_time, pm_close, dt,
      EventEnum, system_log, login_semaphore, LOGIN_TIMEOUT):
'''
TEST1 = ('    if now_date > self.pre_before_trading_date and '
         'pre_before_trading <= now_time < pm_close or '
         'self.pre_before_trading_date == self.initial_trading_date:\n')
TEST2 = ('    if now_date > self.before_trading_date and '
         'before_trading <= now_time < pm_close or '
         'self.before_trading_date == self.initial_trading_date:\n        z = 1\n')
D_E = '''        if now_date != self.first_run_date:
            system_log.debug('x')
            if login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:
                system_log.error('y')
                self.event_queue.put((dt, EventEnum.SYSTEM_EXIT))
                return None
'''
TAIL_SEQ = ('        self.event_queue.put((dt, EventEnum.PRE_BEFORE_TRADING_START))\n'
            '        self.pre_before_trading_date = now_date\n')
TAIL_ELSE = ('            else:\n'
             '                self.event_queue.put((dt, EventEnum.PRE_BEFORE_TRADING_START))\n'
             '                self.pre_before_trading_date = now_date\n')

S1 = HEAD + TEST1 + D_E + TAIL_SEQ + TEST2
S3 = HEAD + TEST1 + D_E + TAIL_ELSE + TEST2
S2 = HEAD + '''    if now_date > self.pre_before_trading_date:
        if pre_before_trading <= now_time < pm_close or self.pre_before_trading_date == self.initial_trading_date:
            pass
''' + '''        elif now_date != self.first_run_date:
            system_log.debug('x')
            if login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:
                system_log.error('y')
                self.event_queue.put((dt, EventEnum.SYSTEM_EXIT))
                return None
''' + '''            else:
                self.event_queue.put((dt, EventEnum.PRE_BEFORE_TRADING_START))
                self.pre_before_trading_date = now_date
        elif now_date > self.before_trading_date:
            if before_trading <= now_time < pm_close or self.before_trading_date == self.initial_trading_date:
                z = 1
'''

SHAPE = {'S1': S1, 'S2': S2, 'S3': S3}[sys.argv[1]]


def rows(co):
    out = []
    for i in dis.get_instructions(co):
        if i.opname in DROP:
            continue
        out.append((i.offset, i.opname, i.argrepr or ''))
    return out


orig = marshal.loads(open(PYC, 'rb').read()[16:])
CO = type(orig)
acc = []


def gather(c):
    acc.append(c)
    for k in c.co_consts:
        if isinstance(k, CO):
            gather(k)


gather(orig)
o = max([c for c in acc if c.co_name == 'clock_worker'], key=lambda c: len(c.co_code))
oi = [r for r in rows(o) if 7164 <= r[0] < 7582]

comp = compile(SHAPE, '<p>', 'exec')
pco = [k for k in comp.co_consts if isinstance(k, CO) and k.co_name == 'f'][0]
prows = rows(pco)
start = next(i for i, r in enumerate(prows) if r[1] == 'LOAD_FAST' and r[2] == 'now_date')
prows = prows[start:]
base = prows[0][0]
end = next(i for i, r in enumerate(prows) if r[2] == 'z')
prows = prows[:end]
print('%s  orig window n=%d  prod window n=%d' % (sys.argv[1], len(oi), len(prows)))


def fmt(r, off0):
    op, nm, ar = r
    if nm.startswith('POP_JUMP') or nm in ('JUMP_FORWARD', 'JUMP_BACKWARD'):
        try:
            ar = '-> @%d' % (int(ar.split()[-1]) - off0)
        except Exception:
            pass
    return '%-28s %s' % (nm, ar)


for k in range(max(len(oi), len(prows))):
    a = fmt(oi[k], 7164) + ('   [@%d]' % oi[k][0] if k < len(oi) else '') if k < len(oi) else ''
    b = fmt(prows[k], base) if k < len(prows) else ''
    mark = '  ' if a.rsplit('   [', 1)[0] == b else '**'
    print('%s %-40s | %s' % (mark, a, b))
