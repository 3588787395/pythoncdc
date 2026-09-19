"""R3-A(a) 精确签名版: get_price 形态 —— 类方法首条日志语句, f-string 含 {x[None:10]!s}
切片与 {len(x) if isinstance(x, list) else 1} 条件表达式操作数, 后随多个 {param} 操作数。
目标签名: 反编译输出为裸 f-string（模板错乱: 接收者/模板文字/BINARY_SUBSCR 丢失）。"""


class Quote:
    def log_debug(self, msg):
        pass

    def get_price(self, security, start_date='20150101', end_date='20151231',
                  frequency='daily', fields=None, fq=None):
        self.log_debug(f'调用函数get_price，参数为：stocks={security[None:10]!s}等{len(security) if isinstance(security, list) else 1}只代码,frequency={frequency},start_date={start_date},end_date={end_date},fields={fields},fq={fq}')
        data = {}
        if isinstance(security, str):
            security = [security]
        elif isinstance(security, (list, tuple)):
            for s in security:
                data[s] = [1, 2, 3]
        if len(data) > 0:
            ret = dict(data)
        else:
            ret = data
        return ret
