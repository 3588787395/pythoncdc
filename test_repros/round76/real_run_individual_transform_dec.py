# Source Generated with Decompyle++ (Python version)
# File: real_run_individual_transform.pyc (Python 3.11)

def run_individual_transform(self, universe, deques):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVTIMEO, 30000)
    socket.setsockopt(zmq.LINGER, 0)
    address = self.get_remote_address(universe[0], 'sub', True)
    socket.connect(address)
    for item in universe:
        socket.setsockopt_string(zmq.SUBSCRIBE, '{"' + item + '"')
    panelt = None
    self._individual_subscribe_count += 1
    self.log.quote.debug(f'开始第{self._individual_subscribe_count!s}次逐笔订阅，包括{universe[:10]!s}等{len(universe)!s}只代码')
    while self.individual_subscribe.isSet():
        try:
            try:
                pass
            except BaseException as x:
                self.log.quote.error('eval转化逐笔数据异常')
                self.log.quote.error('数据内容：' + str(message))
                self.log.quote.error('异常内容:' + str(x))
                continue
                if self.individual_subscribe.isSet():
                    pass
                else:
                    socket.close()
                    context.term()
                    self.log.quote.debug('结束第%s次逐笔订阅' % self._individual_subscribe_count)
                    self.individual_subscribe.set()
                message = socket.recv()
                if message:
                    pass
                else:
                    self.log.quote.warning('逐笔数据返回为空')
                stocks = list(message.keys())[0]
                real_data = message.get(stocks)
                if real_data:
                    if real_data.get('transaction'):
                        transaction_returnDf = self.get_real_individual(stocks, real_data['transaction'], 'transaction')
                        panelt = {stocks: {'transaction': transaction_returnDf}}
                    elif real_data.get('order'):
                        order_returnDf = self.get_real_individual(stocks, real_data['order'], 'order')
                        panelt = {stocks: {'order': order_returnDf}}
                    elif real_data.get('tick'):
                        tick_returnDf = self.get_real_tick(stocks, real_data['tick'])
                        panelt = {stocks: {'tick': tick_returnDf}}
                    deques.appendleft(panelt)
                time.sleep(0)
                self.individual_subscribe.isSet()
                continue
            message = socket.recv()
            if message:
                transaction_returnDf = self.get_real_individual(stocks, real_data['transaction'], 'transaction')
                panelt = {stocks: {'transaction': transaction_returnDf}}
                if real_data.get('order'):
                    order_returnDf = self.get_real_individual(stocks, real_data['order'], 'order')
                    panelt = {stocks: {'order': order_returnDf}}
                elif real_data.get('tick'):
                    tick_returnDf = self.get_real_tick(stocks, real_data['tick'])
                    panelt = {stocks: {'tick': tick_returnDf}}
                deques.appendleft(panelt)
            else:
                self.log.quote.warning('逐笔数据返回为空')
        except zmq.error.Again:
            now_time = qdt.datetime.now().strftime('%H%M')
            if '0900' < now_time < '1515':
                self.log.quote.error('接收逐笔主推数据超时')
        except BaseException as ex:
            import traceback
            from io import StringIO
            error_message = StringIO()
            traceback.print_exc(file=error_message)
            self.log.quote.error('逐笔数据处理异常' + str(error_message.getvalue()))
        time.sleep(0)
        self.individual_subscribe.isSet()
