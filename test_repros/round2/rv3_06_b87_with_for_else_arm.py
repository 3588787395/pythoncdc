# rv3_06: B87 变体补充——try→with→for→while 宿主混合 + try-else 臂 + handler 臂循环控制
# 守卫边界外合法发射验证（B87 家族封闭不应损伤 else 臂/handler 臂正常发射）
def outer(flag):
    acc = []
    try:
        with open(__file__, 'r') as fh:
            for line in fh:
                while len(acc) < 2:
                    if flag:
                        acc.append(line[0])
                    else:
                        acc.append('-')
                    break
                else:
                    acc.append('else-taken')
                    break
    except OSError:
        acc.append('oserror')
        for k in range(2):
            try:
                acc.append(str(k))
            except ValueError:
                acc.append('bad')
                break
    else:
        acc.append('try-else')
    return acc
