# -*- coding: utf-8 -*-
"""R13-K 复现：`try/except/else: break` 里，except 处理体某个分支末尾的裸 `raise`
被下沉到 handler 出口（变成所有路径共用），顺带吃掉 handler 的 POP_EXCEPT 收尾与
while 回边。

对应真实目标：
  fly/common/flytools.pyc  <module>.FileLock.acquire  [seq_len] orig=90 decomp=85

实测 dis：
  ORIG   #40-#44 LOAD_FAST 'os.unlink' ... CALL 1 ; POP_TOP | #45 364 RAISE_VARARGS 0
               #46 366 LOAD_GLOBAL 'time' ... （else 侧继续）
         #71 558 POP_EXCEPT ; #72 LOAD_CONST None ; #73 STORE_FAST 'e' ; #74 DELETE_FAST 'e' ;
         #75 566 JUMP_FORWARD '->584'
         #84 586 JUMP_BACKWARD '->42'      <- while 回边仍在
  DECOMP #45 364 JUMP_FORWARD '->558'      <- raise 从分支里搬到了 558
         #71 558 RAISE_VARARGS 0 ; #72-#74 收尾 ; #75 566 RERAISE 1
         （POP_EXCEPT、JUMP_FORWARD、while 回边 共少 5 条）
"""


class FileLockException(Exception):
    pass


def acquire(self, os, time, errno, start_time):
    start_time = time.time()
    while True:
        try:
            self.fd = os.open(self.lockfile, os.O_CREAT)
        except OSError as e:
            if e.errno != errno.EEXIST:
                if os.path.exists(self.lockfile):
                    os.unlink(self.lockfile)
                raise
            else:
                if time.time() - start_time >= self.timeout:
                    os.unlink(self.lockfile)
                    raise FileLockException('Timeout occured.')
                time.sleep(self.delay)
        else:
            break
    self.is_locked = True
    return None
