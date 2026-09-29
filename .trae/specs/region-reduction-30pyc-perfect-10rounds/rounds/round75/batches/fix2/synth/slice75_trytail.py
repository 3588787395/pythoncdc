# -*- coding: utf-8 -*-
# [R75 fix2 synth] 三函数切片（不入判据）：jump 目标几何与真身相差 4 字节
# （LOAD_GLOBAL NULL 位 / 目标行表），两臂产物不同但 mandated 均 success，
# 说明最小复现必须保留真身字节码几何 => repro 用真身 pyc。
# Source Generated with Decompyle++ (Python version)
# File: trade_info_utils.pyc (Python 3.11)

import csv
import datetime
import html
import json
import logging
import os
import re
import subprocess
import time
from tornado.log import app_log
from IQCommon import pandas as pd
from IQCommon.common import GET_TRADE_STATUS_TIME, IS_ENCRYPTION, KILL_TRADE_PROCESS_ATTEMPTS, LOCAL_IP, STRATEGY_DIR_PATH, TRADE_DIR_PATH, TRADE_STOP_TIME_WAIT, base_path, future_am_close, future_am_open, future_before_trading_time, future_pm_close, future_pm_open, future_trade_daily, hks_after_trading_time, hks_am_close, hks_am_open, hks_before_trading_time, hks_pm_close, hks_pm_open, hks_trade_daily, l2_switch, max_trade_count, stock_after_trading_time, stock_am_close, stock_am_open, stock_before_trading_time, stock_pm_close, stock_pm_open, stock_trade_daily, sync_seconds, trades_download_path
from IQCommon.const import AI_ADD_TRADE_STRATEGY_TYPE, AI_STRATEGY_TYPE, COMMON_STRATEGY_TYPE, CUSTOM_STRATEGY_TYPE_DICT, DELETE_SIM_TRADING_LIST_FILE, GREP_CMD, KILL_CMD, SIM_TRADING_COLUMN_NAMES, SIM_TRADING_LIST_FILE, STRATEGY_PROFILE, TradeStatus, USER_CODE_DAT, USER_OPERATIONS_FILE, ZT_ADD_TRADE_STRATEGY_TYPE
from IQCommon.data.pycrypto import PyRead_AES_Binary
from IQCommon.exception import get_traceback_message
from IQCommon.logger import system_log
from IQCommon.util.crypto_utils import aes_decrypt
from IQCommon.util.fileio_utils import FileIO, FileLock
from IQCommon.util.strategy_info_utils import get_strategy, get_upload_strategy
from IQCommon.util.user_info_utils import get_user_info as get_user_info_from_json
from fly.common.aes_encrypt import code_encrypt_pyc, code_encrypt_so
from fly.common.enums import BUSINESS_MODE_1, BUSINESS_MODE_2, ENCRYPTION_MODE_1, ENCRYPTION_MODE_2
from fly.common.fly_exception import CompileError, UnknownError
from fly.common.flytools import get_code_public, get_mem_under_oom_status, kill_trade_proc
USER_CODE_PY = 'user_code.py'
USER_CONFIG_JSON = 'user_config.json'
TRADES_DOWNLOAD_FILE = 'trades_download.csv'
USER_INFO_FILE = 'user_info.csv'
TRADE_POSITION_FILE = 'sim_position.csv'
TRADE_ORDER_FILE = 'sim_order.csv'
TRADE_BUSINESS_FILE = 'sim_business.csv'
TRADE_DELIVERY_FILE = 'sim_delivery.csv'
USER_STRATEGY_SO = 'user_strategy.so'
USER_STRATEGY_SO_ENCRYPTION = 'user_strategy.cpython-35m-x86_64-linux-gnu.so'
USER_STRATEGY_PY = 'user_strategy.py'
USER_STRATEGY_PYC = 'user_strategy.pyc'
pyflakes_error_template = """^(?P<path>[^
]*/user_strategy.?[\\d]*.py)"""

def kill_trade_process(user_id, trade_id, time_wait=True):
    if time_wait:
        time.sleep(int(TRADE_STOP_TIME_WAIT))
    if len(trade_id) != 36:
        app_log.error('交易ID: %s不合法，不执行强制停止进程操作' % trade_id)
        return None
    else:
        qry_info = os.popen("ps -ef | grep %s | grep -v grep | awk '{print $2}'" % trade_id).readlines()
        if len(qry_info) != 0:
            qry_info = [item.replace("""
""", '') for item in qry_info]
            user_trade_info = os.popen('ps -ef | grep jupyter-{} | grep start_user_code.py | grep -v grep'.format(user_id)).read()
            trade_id_list = re.findall(re.compile('result/(.*)/start_user_code.py'), user_trade_info)
            if trade_id in trade_id_list:
                trade_id_list.remove(trade_id)
            sim_trading_path = os.path.join(TRADE_DIR_PATH, user_id, SIM_TRADING_LIST_FILE)
            try:
                with FileLock(sim_trading_path):
                    app_log.warning('获取锁成功，交易状态为终止/删除，后台进程仍旧存在，强制停止当前交易进程，交易ID：%s' % trade_id)
                    os.system(KILL_CMD % trade_id)
            except BaseException:
                app_log.warning('获取锁失败，交易状态为终止/删除，后台进程仍旧存在，强制停止当前交易进程，交易ID：%s' % trade_id)
                os.system(KILL_CMD % trade_id)
                if os.path.getsize(sim_trading_path) == 0:
                    app_log.warning('用户{}{}文件大小为空，执行删除操作'.format(user_id, SIM_TRADING_LIST_FILE))
                    os.system('sudo rm -rf {}'.format(sim_trading_path))
                    if len(trade_id_list) > 0:
                        app_log.info('用户{}使用强制停止交易进程前正则匹配数据{}重新生成{}文件'.format(user_id, trade_id_list, SIM_TRADING_LIST_FILE))
                        current_time = datetime.datetime.now()
                        current_date = current_time.strftime('%Y-%m-%d')
                        now_time = current_time.strftime('%H:%M:%S')
                        start_time = '{} {}'.format(current_date, now_time)
                        count = 1
                        write_info = [SIM_TRADING_COLUMN_NAMES]
                        for running_trade_id in trade_id_list:
                            strategy = get_trade_strategy(user_id, running_trade_id)
                            strategy_id = strategy.get('id')
                            frequency = strategy.get('frequency', 'minute')
                            business_type = strategy.get('business_type')
                            strategy_name = strategy.get('name')
                            if 'hg_' in strategy_name:
                                strategy_type = AI_ADD_TRADE_STRATEGY_TYPE
                            elif 'zt_' in strategy_name:
                                strategy_type = ZT_ADD_TRADE_STRATEGY_TYPE
                            elif strategy_name.startswith('CUSTOM_'):
                                strategy_type = CUSTOM_STRATEGY_TYPE_DICT['_'.join(strategy_name.split('_')[1:-1])]
                            else:
                                strategy_type = COMMON_STRATEGY_TYPE
                            response = re.findall(re.compile('"op_station": "(.*)"'), open(os.path.join(TRADE_DIR_PATH, user_id, 'result', running_trade_id, 'user_code.py')).read())
                            if len(response) > 0:
                                op_station = response[0]
                            else:
                                app_log.error('用户{}交易ID{}获取站点信息失败，跳过信息恢复'.format(user_id, running_trade_id))
                                continue
                            write_info.append([running_trade_id, '异常交易{}'.format(count), '0', '0', start_time, '10000000', frequency, strategy_id, running_trade_id, '0', '0', '0', op_station, strategy_type, business_type, LOCAL_IP])
                            count += 1
                        with FileLock(sim_trading_path):
                            FileIO(sim_trading_path).write(write_info, mode='w', data_type='list')
            sim_trading_lock_path = os.path.join(TRADE_DIR_PATH, user_id, SIM_TRADING_LIST_FILE + '.lock')
            if os.path.exists(sim_trading_lock_path):
                try:
                    os.system('sudo chmod 755 {}'.format(sim_trading_lock_path))
                    os.system('sudo chown fly:fly {}'.format(sim_trading_lock_path))
                    process_id = None
                    count = 0
                    while count < KILL_TRADE_PROCESS_ATTEMPTS:
                        process_id = open(sim_trading_lock_path, mode='r', encoding='utf-8').readline()
                        if process_id != '':
                            break
                        time.sleep(0.001)
                        count += 1
                except BaseException:
                    process_id = None
                    app_log.warning('获取用户{}交易信息锁文件中进程号失败，错误原因{}'.format(user_id, get_traceback_message()))
                if process_id is not None:
                    process_id = process_id.replace("""
""", '')
                    if process_id in qry_info:
                        try:
                            os.unlink(sim_trading_lock_path)
                            app_log.warning('用户{}交易信息锁文件中进程号{}属于当前强制停止的交易{}，执行删除锁文件操作'.format(user_id, process_id, trade_id))
                            return None
                        except BaseException:
                            app_log.warning('删除锁文件操作失败，错误原因：{}'.format(get_traceback_message()))
                            return None
                    elif process_id == '':
                        try:
                            os.unlink(sim_trading_lock_path)
                            app_log.warning('用户{}交易信息锁文件中内容为空，执行删除锁文件操作'.format(user_id))
                            return None
                        except BaseException:
                            app_log.warning('删除锁文件操作失败，错误原因：{}'.format(get_traceback_message()))
                            return None
                    else:
                        return None
            else:
                app_log.info('用户{}不存在交易信息锁文件'.format(user_id))
        else:
            return None

def query_strategy_id(user_id, trade_id):
    trade_status = [TradeStatus.TRADE_RUNNING, TradeStatus.TRADE_PRE_RESTART]
    sim_trading_list_path = os.path.join(TRADE_DIR_PATH, user_id, SIM_TRADING_LIST_FILE)
    if os.path.exists(sim_trading_list_path):
        try:
            with FileLock(sim_trading_list_path, mode='shared'):
                file_io = FileIO(sim_trading_list_path)
                df = file_io.read(return_type='dataframe')
            trade_df = df[df['id'] == trade_id]
            if len(trade_df) == 1:
                return trade_df.backtestContentId.iloc[0]
            else:
                return None
        except BaseException:
            system_log.error('获取交易streagy_id异常，错误原因：{}'.format(get_traceback_message()))
            time.sleep(1)
        return None

def query_trade_strategy_info(user_id, strategy_id):
    trade_status = [TradeStatus.TRADE_RUNNING, TradeStatus.TRADE_PRE_RESTART]
    sim_trading_list_path = os.path.join(TRADE_DIR_PATH, user_id, SIM_TRADING_LIST_FILE)
    if os.path.exists(sim_trading_list_path):
        try:
            with FileLock(sim_trading_list_path, mode='shared'):
                file_io = FileIO(sim_trading_list_path)
                csv_reader = file_io.read(return_type='csv_reader')
            for items in csv_reader:
                if len(items) > 0 and items[2] in trade_status and items[7] == strategy_id and items[16] == 'app':
                    return True
        except BaseException:
            system_log.error('获取交易状态失败，错误原因：{}'.format(get_traceback_message()))
        return None
