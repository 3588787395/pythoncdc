# R57-19: 全保真提取 — order_entrust_info_handle 从真 pyc 原样提取
# (含 option 臂、eval 赋值、('4','5','7','8') 检查与共享 break 中转块)。
# 预期复现真 pyc 的 +5 签名及缺陷A/B/C全部表现。
def order_entrust_info_handle(orders, entrust_list, business_type='stock'):
    try:
        for order in orders:
            for entrust in entrust_list:
                if str(entrust['entrust_no']) == order.entrust_no and order.datetime.date() == datetime.datetime.now().date():
                    if business_type == 'stock':
                        exchange_type = entrust.get('exchange_type')
                        if exchange_type not in EXCHANGE_TYPE_ENUM.keys():
                            strategy_log.error('不支持的市场类型：%s' % exchange_type)
                            continue
                        stock_code = entrust.get('stock_code') + '.' + EXCHANGE_TYPE_ENUM[exchange_type]
                    elif business_type == 'future':
                        exchange_type = entrust.get('futu_exch_type')
                        if exchange_type not in EXCHANGE_TYPE_ENUM.keys():
                            strategy_log.error('不支持的市场类型：%s' % exchange_type)
                            continue
                        stock_code = entrust.get('contract_code') + '.' + EXCHANGE_TYPE_ENUM[exchange_type]
                    elif business_type == 'option':
                        exchange_type = entrust.get('exchange_type')
                        if exchange_type not in OPT_EXCHANGE_TYPE_ENUM.keys():
                            strategy_log.error('不支持的市场类型：%s' % exchange_type)
                            continue
                        stock_code = entrust.get('option_code') + '.' + OPT_EXCHANGE_TYPE_ENUM[exchange_type]
                    else:
                        strategy_log.error('不识别的业务类型：%s' % business_type)
                        continue
                    if stock_code == order.symbol:
                        entrust_status = str(entrust['entrust_status'])
                        if entrust_status not in ENTRUST_STATUS_ENUM:
                            strategy_log.error('不识别的委托状态：%s' % entrust_status)
                            break
                        if str(order.status.value) not in SPECIAL_ENTRUST_STATUS_ENUM.keys():
                            order._status = eval(ORDER_STATUS_ENUM[entrust_status])
                        if entrust_status in ('4', '5', '7', '8'):
                            order._filled_amount = float(entrust['business_amount'])
                        break
    except BaseException:
        strategy_log.error('Order对象更新失败，错误信息：%s' % get_traceback_message())
