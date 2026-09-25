# -*- coding: utf-8 -*-
import time

SUCCESS = 0


def init_connection(self):
    i = 0
    while True:
        error_no, error_info = self.connector_manager.CreateConnector(1, self.t2sdk_ini_path)
        if error_no != SUCCESS:
            if i < 3:
                time.sleep(1)
                i += 1
            else:
                error_info = 'init_connection创建连接超时,请稍后再试'
                break
        else:
            break
    return {'error_no': error_no, 'error_info': error_info}
