# -*- coding: utf-8 -*-
"""R70 diag1 Step-3 synthetic witness for 根因 B:
R57-E 单侧规则把 try 体越过 handler 的 JUMP_FORWARD 当臂出口票，且因游走跳过异常边，
把 handler 内前驱误判成「兄弟臂外部汇入」，merge 被改成内层 if 条件块 ⇒ 内层 if 被提升到
外层 else 之后（同时丢 1 个 JUMP_FORWARD + 1 个 EXTENDED_ARG）。

landed 失败签名：official mismatch（matched < total）。
"""


def repro(events, ctrl, log, keep):
    n = 0
    while len(events) > 0:
        event = events.pop(0)
        if ctrl == '1':
            info = {}
            try:
                code = event['code']
            except AttributeError:
                code = '0'
            if code == '1':
                log.debug('in %s' % code)
                info['a'] = 1
                n = n + 1
            else:
                log.debug('out %s' % code)
                log.warning('drop %s' % event)
        else:
            log.debug('host %s' % event)
            keep.append(event)
    return n
