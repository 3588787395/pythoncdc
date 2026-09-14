def f(servers, down_list):
    try:
        for s in servers:
            if s['status'] == 'down':
                continue
            shard = s['upstream'].split('_')[-1]
            info = {'shard': shard, 'index': s['index']}
            local_shard = shard
            local_idx = s['index']
            same_shard = {v: k for k, v in info.items() if v == local_shard}
            return {'error_no': 0, 'index': local_idx, 'same': same_shard}
        return {'error_no': -1, 'info': 'all down'}
        return None
    except BaseException:
        return {'error_no': -1, 'info': 'exception'}
