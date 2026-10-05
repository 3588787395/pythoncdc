# rv3_01: B87 守卫边界外形态——三层嵌套 try 混合宿主（try→for→try→while→if→try）+ handler 臂含 return
# 守卫不得误伤合法发射：中间循环宿主内的 try 应由循环体走查整树生成，语句序与体完整
import os as _os
import sys


def deep_try_nest(flag):
    total = 0
    try:
        for i in range(3):
            try:
                while i < 2:
                    if flag:
                        try:
                            total += i
                        except ValueError:
                            return -1
                    else:
                        total += 1
                    i += 1
            except KeyError:
                total = 0
    finally:
        total += 100
    return total


def handler_arm_return(x):
    out = 0
    for i in range(4):
        try:
            if x:
                out += i
            else:
                out -= 1
        except TypeError:
            return out
    return out


if __name__ == '__main__':
    print(deep_try_nest(True))
    print(deep_try_nest(False))
    print(handler_arm_return(1))
    print(handler_arm_return(0))
