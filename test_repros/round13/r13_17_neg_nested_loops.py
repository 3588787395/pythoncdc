# -*- coding: utf-8 -*-
"""R13 负对照 C：嵌套循环 + 显式 continue/break + try/except 结尾 —— 不应多出回边。

对照 R13-B：这里 try/except 后面**还有**语句，因此不存在「region 尾就是循环尾」的
歧义，尺子必须判 MATCH。
"""


def walk_files(os, log, base_dirs, user_id):
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for name in files:
                    if name.endswith('.lock'):
                        path = os.path.join(root, name)
                        try:
                            os.unlink(path)
                        except BaseException:
                            log.error('fail {}'.format(user_id))
                        log.info('done')
    return None


def loops(a, b, c, sink):
    for x in a:
        while x:
            if x > 10:
                sink(x)
                break
            elif x < 0:
                continue
            x -= 1
        for y in b:
            if y in c:
                continue
            sink(y)
    return None
