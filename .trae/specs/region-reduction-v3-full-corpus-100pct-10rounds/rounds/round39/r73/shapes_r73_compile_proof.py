"""compile()-shape proof on 3.11.7: does `if X and A or B: arm` reproduce the original's
leg layout (X false -> B test, A chain-compare true -> arm, arm falls through with NO jump)?

usage: python -X utf8 work/shapes_r73.py
"""
import dis

ORIG = """\
@6322 LOAD_FAST now_date
@6324 LOAD_DEREF self
@6326 LOAD_ATTR pre_before_trading_date
@6336 COMPARE_OP >
@6342 POP_JUMP_FORWARD_IF_FALSE -> 6374
@6344 LOAD_FAST pre_before_trading
@6346 LOAD_FAST now_time
@6348 SWAP
@6350 COPY
@6352 COMPARE_OP <=
@6358 POP_JUMP_FORWARD_IF_FALSE -> 6372
@6360 LOAD_FAST pm_close
@6362 COMPARE_OP <
@6368 POP_JUMP_FORWARD_IF_TRUE -> 6406
@6370 JUMP_FORWARD -> 6374
@6372 POP_TOP
@6374 LOAD_DEREF self
@6376 LOAD_ATTR pre_before_trading_date
@6386 LOAD_DEREF self
@6388 LOAD_ATTR initial_trading_date
@6398 COMPARE_OP ==
@6404 POP_JUMP_FORWARD_IF_FALSE -> 6496
@6406 <arm statements, fall through>
"""

SRC_CANDIDATE = """
def f(now_date, self, pre_before_trading, now_time, pm_close, dt):
    if now_date > self.pre_before_trading_date and pre_before_trading <= now_time < pm_close or self.pre_before_trading_date == self.initial_trading_date:
        print(dt)
        now_date = 1
    print(2)
"""

SRC_NESTED = """
def f(now_date, self, pre_before_trading, now_time, pm_close, dt):
    if now_date > self.pre_before_trading_date:
        if pre_before_trading <= now_time < pm_close or self.pre_before_trading_date == self.initial_trading_date:
            print(dt)
            now_date = 1
    print(2)
"""


def skel(src, label):
    co = compile(src, '<p>', 'exec').co_consts[0]
    print('==== %s' % label)
    for i in dis.get_instructions(co):
        if i.opname in ('RESUME', 'CACHE', 'EXTENDED_ARG'):
            continue
        print('  %-30s %s' % (i.opname, i.argrepr))


skel(SRC_CANDIDATE, 'flat  `if X and A or B: arm`')
print()
skel(SRC_NESTED, 'nested `if X: if A or B: arm`  (current product shape)')
