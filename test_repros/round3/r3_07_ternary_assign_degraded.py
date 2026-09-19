"""R3-F(变体): 三元赋值 `x = A if C else B` 被降级为两个裸表达式语句（赋值丢失）；
以及块尾构造+return 被替换为 return None。
对照 quote.pyc get_individual_data:
    data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
    ... returnPa = pandas.Panel(data); return returnPa
反编译输出: `int(data_count)` / `200` 裸表达式; `return None`。"""


def get_individual_data(self, data_type, stocks, data_count=50, start_pos=0, search_direction=1):
    if stocks:
        data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
        if isinstance(stocks, str):
            param = [data_type, [stocks], str(search_direction), str(data_count), str(start_pos)]
        elif isinstance(stocks, (list, tuple)):
            param = [data_type, list(stocks), str(search_direction), str(data_count), str(start_pos)]
        redata, flag = self.api_get_from_zeromq(str(param))
        count = 0
        while not redata and count < 3:
            time.sleep(1)
            redata, flag = self.api_get_from_zeromq(str(param))
            count += 1
        if redata:
            redata = redata.get('data').get(data_type)
            data = {}
            data[stocks] = redata
            returnPa = pandas.Panel(data)
            return returnPa
        elif flag == 1:
            self.log.quote.info('逐笔数据转化异常，默认返回空值')
        elif flag == -1:
            self.log.quote.info('逐笔数据返回空值')
    return None
