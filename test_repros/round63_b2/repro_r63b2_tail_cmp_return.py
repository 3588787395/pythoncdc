# -*- coding: utf-8 -*-
"""Round 63 batch-2 minimal repro: elif 分支 try/except 之后的链式比较 return 被丢弃。

对应真实缺陷：site-packages/IQEngine/utils/scheduler.pyc ::
Scheduler.run_interval_trade.is_run_interval_time_now（orig=225 decomp=201，
缺失的 24 条指令正是 elif 分支末尾 `return (A < cur < B) or (C < cur < D)`）。

编译：  python -m py_compile repro_r63b2_tail_cmp_return.py
反编译：在 D:/Temp/opencode/r63gate/diag2 下
    python -X utf8 h62.py run --arm=landed --list=<本目录>/repro_targets.txt \
        --out=dump/repro_landed.jsonl --budget=280
"""


def case_elif_try_tail_return(f_kwargs, A, B, C, D):
    key = f_kwargs.pop('key', '')
    if not isinstance(key, str):
        log.error('bad type {}'.format(key))
        return False
    elif not key:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
            log.error('failed {}'.format(tb()))
        return (A < cur < B) or (C < cur < D)
    else:
        items = key.split(',')
        valid = []
        for it in items:
            try:
                s, e = it.split('-')
                s = int(s)
                e = int(e)
                if s > e:
                    log.error('bad range {}'.format(it))
                    continue
                valid.append((s, e))
            except BaseException:
                log.error('bad format {}'.format(it))
        if len(valid) == 0:
            log.error('empty {}'.format(key))
            return False
        try:
            cur = int(src2())
        except BaseException:
            cur = 0
            log.error('failed {}'.format(tb()))
        for s, e in valid:
            if s <= cur < e:
                return True
        return False
