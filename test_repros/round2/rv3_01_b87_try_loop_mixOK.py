# Source Generated with Decompyle++ (Python version)
# File: rv3_01_b87_try_loop_mix.pyc (Python 3.11)

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
                            total += 100
                            return -1
                    else:
                        total += 1
                    i += 1
                continue
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
