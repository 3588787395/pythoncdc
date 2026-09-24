# R57-11: order_entrust_info_handle 集成复现 — 缺陷A/B/C 同框
# (真 pyc 裁剪版: 去 option 臂与 eval 赋值, 保留三缺陷全部触发结构)。
def order_entrust_info_handle(orders, entrust_list, business_type='stock'):
    try:
        for order in orders:
            for entrust in entrust_list:
                if str(entrust['entrust_no']) == order.entrust_no and order.datetime.date() == datetime.datetime.now().date():
                    if business_type == 'stock':
                        exchange_type = entrust.get('exchange_type')
                        if exchange_type not in EXCHANGE_TYPE_ENUM.keys():
                            log.error('不支持的市场类型：%s' % exchange_type)
                            continue
                        stock_code = entrust.get('stock_code') + '.' + EXCHANGE_TYPE_ENUM[exchange_type]
                    elif business_type == 'future':
                        exchange_type = entrust.get('futu_exch_type')
                        if exchange_type not in EXCHANGE_TYPE_ENUM.keys():
                            log.error('不支持的市场类型：%s' % exchange_type)
                            continue
                        stock_code = entrust.get('contract_code') + '.' + EXCHANGE_TYPE_ENUM[exchange_type]
                    else:
                        log.error('不识别的业务类型：%s' % business_type)
                        continue
                    if stock_code == order.symbol:
                        entrust_status = str(entrust['entrust_status'])
                        if entrust_status not in ENTRUST_STATUS_ENUM:
                            log.error('不识别的委托状态：%s' % entrust_status)
                            break
                        if entrust_status in ('4', '5', '7', '8'):
                            order._filled_amount = float(entrust['business_amount'])
                        break
    except BaseException:
        log.error('Order对象更新失败，错误信息：%s' % get_traceback_message())
