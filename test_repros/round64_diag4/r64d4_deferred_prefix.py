"""R64-D4 repro A: statements preceding a `return <dict>` inside a try get dropped.

Mirrors site-packages/IQCommon/common/main.pyc :: get_same_shard_server_ip_info
(original lines 678/680/681: the dictcomp over the cell variable `target`, the
`msg = ... % nginx_ip` assignment and the `user_log.info(msg)` call, all swallowed
by RegionASTGenerator._try_deferred_return_in_loop, which emits only the Return).

Landed arm:  picked/msg/log.info missing  -> official 1/2, strict seq_len + missing
             nested <dictcomp> code object.
Arm cand_r64d4_a_deferred_prefix: recovered -> official 2/2.
"""

log = None


def lookup(rows, target):
    info = {}
    try:
        for r in rows:
            if r['name'] == target:
                info[r['name']] = r['index']
        picked = {v: k for k, v in info.items() if v > 0}
        msg = 'found %s' % target
        log.info(msg)
        return {'error_no': 0, 'detail': picked}
    except BaseException:
        msg = 'fail %s' % target
        log.error(msg)
        return {'error_no': -1, 'info': msg}
