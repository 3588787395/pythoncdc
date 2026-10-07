# Source Generated with Decompyle++ (Python version)
# File: r9q_03_nested_try_body_dumped_in_handler.pyc (Python 3.11)

def run(sub, sock, dq, lg):
    while sub.isSet():
        try:
            try:
                continue
                if m:
                    dq.append(m)
                else:
                    lg.warn('empty')
            except BaseException as x:
                break
                sleep(0)
                sub.isSet()
                break
        except Timeout:
            lg.error('timeout')
        except BaseException as ex:
            lg.error(str(ex))
