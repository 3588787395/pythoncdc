# Source Generated with Decompyle++ (Python version)
# File: real_run_tick_socket.pyc (Python 3.11)

def run_tick_socket(self, socket, deques, dataDict, userLock, flag):
    imagedata = dataDict['imagedata']
    panelt = None
    try:
        message = socket.recv()
        if message:
            try:
                message = eval(message.decode())
            except BaseException as x:
                self.log.quote.error('eval转化tick数据异常')
                self.log.quote.error('数据内容：' + str(message))
                self.log.quote.error('异常内容:' + str(x))
                userLock.acquire()
                dataDict['updateflag'] = 1
                userLock.release()
                return None
            stocks = list(message.keys())[0]
            real_data = message.get(stocks)
            if real_data:
                if real_data['tick'][-1] == 0:
                    tick_returnDf = self.get_real_tick(stocks, real_data['tick'])
                    imagedata[stocks] = tick_returnDf
                    userLock.acquire()
                    dataDict['imagedata'] = imagedata
                    dataDict['updateflag'] = 0
                    userLock.release()
                    transaction_returnDf = self.get_real_individual(stocks, real_data['transaction'], 'transaction')
                    order_returnDf = self.get_real_individual(stocks, real_data['order'], 'order')
                    panelt = {stocks: {'tick': tick_returnDf, 'transaction': transaction_returnDf, 'order': order_returnDf}}
                    if flag:
                        deques.appendleft(panelt)
                elif message[stocks][-1] == 1 and panelt is not None and flag:
                    deques.appendleft(panelt)
        else:
            self.log.quote.warning('tick数据返回为空')
            userLock.acquire()
            dataDict['updateflag'] = -1
            userLock.release()
            return None
    except zmq.error.Again:
        now_time = qdt.datetime.now().strftime('%H%M')
        if '0900' < now_time < '1515':
            self.log.quote.error('接收tick主推数据超时')
    except BaseException as ex:
        import traceback
        from io import StringIO
        error_message = StringIO()
        traceback.print_exc(file=error_message)
        self.log.quote.error('tick数据处理异常' + str(error_message.getvalue()))
        userLock.acquire()
        dataDict['updateflag'] = 2
        userLock.release()
    time.sleep(0)
