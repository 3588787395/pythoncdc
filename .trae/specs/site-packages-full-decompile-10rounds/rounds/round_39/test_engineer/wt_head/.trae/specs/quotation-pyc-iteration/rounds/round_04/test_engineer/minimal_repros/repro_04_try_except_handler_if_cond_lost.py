# R4 minimal repro: except handler 内 if e2.code == 401 Compare 节点丢失
# 关联缺陷：repro_03_try_except_handler_if_cond_lost (P2 残留)
# 触发区域：TRY
# 预期：except HTTPError as e2: 后 system_log.error(...); if e2.code == 401: time.sleep(10); ...
# R4 实际产物：if HTTPError: pass else: if BaseException: pass  (Compare 丢失)
import json
import time


def api_get_financial(url, params=None, request_times=0):
    token_value = get_token()
    if not token_value:
        print('ERROR:获取token失败！')
        return None
    real_url = url_concat(url, params)
    headers = {'Authorization': 'Bearer %s' % token_value}
    data = params
    return_data = None
    try:
        response = requests.get(real_url, headers=headers, data=data)
        return_data = response.json()
    except ConnectionRefusedError as e1:
        system_log.error(get_traceback_message())
        error_no = -1
        error_info = e1
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except HTTPError as e2:
        system_log.error(get_traceback_message())
        if e2.code == 401:
            if request_times <= 2:
                time.sleep(10)
                request_times += 1
                return_data = api_get_financial(url, params, request_times)
            else:
                return_data = None
        else:
            error_no = e2.code
            if not e2.response:
                error_info = None
            else:
                try:
                    error_info = json.loads(e2.response.body.decode('utf8', 'replace'))
                except ValueError:
                    system_log.error(get_traceback_message())
                    error_info = str(e2.response.body.decode('utf8', 'replace'))
            return ({'error_no': error_no, 'error_info': error_info}, {})
    return return_data
