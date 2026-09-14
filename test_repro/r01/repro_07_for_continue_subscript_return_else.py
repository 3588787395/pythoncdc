def f(entries, skip_name):
    try:
        for entry in entries:
            if entry['status'] == 'down':
                continue
            shard = entry['upstream'].split('_')[-1]
            idx = entry['index']
            return {'shard': shard, 'index': idx}
        return {'error_no': -1}
        return None
    except BaseException:
        return {'error_no': -1, 'error': 'exception'}
