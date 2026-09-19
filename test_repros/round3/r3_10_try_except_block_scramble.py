"""R3-I: try/except/else 与 if/else 嵌套区域块归属错乱。
对照 quote.pyc run_tick_socket: 内层 try/except 的正常出口块被反编译为 try/except/else 的
else 子句，if message: 的 else 体被搬移/吞并，elif 链错位挂接。"""


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
                    panelt = {stocks: {'tick': tick_returnDf}}
                    if flag:
                        deques.appendleft(panelt)
            elif message[stocks][-1] == 1 and panelt is not None and flag:
                deques.appendleft(panelt)
        else:
            return None
    except zmq.error.Again:
        now_time = qdt.datetime.now().strftime('%H%M')
        if '0900' < now_time < '1515':
            self.log.quote.error('接收tick主推数据超时')
    except BaseException as ex:
        self.log.quote.error('tick数据处理异常')
    time.sleep(0)
