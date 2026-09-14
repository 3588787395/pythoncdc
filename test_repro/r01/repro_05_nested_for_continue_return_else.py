def f(ips, down_ips):
    try:
        for ip in ips:
            if ip in down_ips:
                continue
            shard_info = {}
            for info in get_info(ip):
                shard_info[info['name']] = info['shard']
            same = {v: k for k, v in shard_info.items()}
            return {'error_no': 0, 'data': same}
        return {'error_no': -1, 'info': 'all failed'}
        return None
    except BaseException:
        return {'error_no': -1, 'info': 'exception'}

def get_info(ip):
    return [{'name': ip, 'shard': '0'}]
