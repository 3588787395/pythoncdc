
def f(algo, datalist):
    algo.tmporders.write_lock.acquire()
    tmporders = algo.tmporders.get_instance()
    dict_map = algo._dict_map.get_instance()
    try:
        for order_item in datalist:
            entrust_no = order_item['entrust_no']
            if entrust_no in dict_map:
                order_id = dict_map[entrust_no]
                try:
                    order_obj = tmporders[order_id]
                except BaseException:
                    system_log.error(get_traceback_message())
                    order_obj = algo.create_order_object(order_id, order_item)
                order_obj.status = int(order_item['status'])
                tmporders[order_id] = order_obj
        algo.tmporders.set_instance(tmporders)
    finally:
        algo.tmporders.write_lock.release()
