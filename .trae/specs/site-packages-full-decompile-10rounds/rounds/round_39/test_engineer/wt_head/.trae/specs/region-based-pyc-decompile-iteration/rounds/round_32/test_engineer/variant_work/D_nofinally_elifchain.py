
def f(algo, datalist):
    tmporders = algo.tmporders.get_instance()
    dict_map = algo._dict_map.get_instance()
    for order_item in datalist:
        entrust_no = order_item['entrust_no']
        if entrust_no in dict_map:
            order_id = dict_map[entrust_no]
            if order_id in tmporders:
                order_obj = tmporders[order_id]
            else:
                order_obj = algo.create_order_object(order_id, order_item)
            status = int(order_item['status'])
            if status in {5, 6}:
                order_obj.filled = order_obj.filled + order_item['business_amount']
            elif status == 9:
                order_obj.filled = 0
            else:
                order_obj.filled += order_item['business_amount']
            order_obj.status = status
            tmporders[order_id] = order_obj
    algo.tmporders.set_instance(tmporders)
