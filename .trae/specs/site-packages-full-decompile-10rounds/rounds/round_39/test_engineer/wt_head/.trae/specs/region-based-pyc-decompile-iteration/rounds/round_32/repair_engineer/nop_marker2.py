# -*- coding: utf-8 -*-
"""Which statements inside try/finally emit a NOP before the finally copy?"""


def w1(algo, datalist):
    # plain expression/assignment statement
    try:
        for item in datalist:
            x = item
        algo.set_instance()
    finally:
        algo.release()


def w2(algo, datalist):
    # for-else
    try:
        for item in datalist:
            x = item
        else:
            algo.set_instance()
    finally:
        algo.release()


def w3(algo, datalist):
    # if statement as last statement
    try:
        if algo.cond():
            x = 1
    finally:
        algo.release()


def w4(algo, datalist):
    # while loop as last statement
    try:
        while algo.cond():
            x = 1
    finally:
        algo.release()


def w5(algo, datalist):
    # while-else
    try:
        while algo.cond():
            x = 1
        else:
            algo.set_instance()
    finally:
        algo.release()


def w6(algo, datalist):
    # try-except as last statement
    try:
        try:
            x = 1
        except ValueError:
            x = 2
    finally:
        algo.release()


def w7(algo, datalist):
    # with statement as last statement
    try:
        with algo.lock():
            x = 1
    finally:
        algo.release()


def w8(algo, datalist):
    # nested for-else where else has 2 statements then finally
    try:
        for item in datalist:
            x = item
        else:
            algo.set_instance()
            algo.after()
    finally:
        algo.release()


if __name__ == "__main__":
    import dis
    for fn in (w1, w2, w3, w4, w5, w6, w7, w8):
        print("=" * 60)
        print(fn.__name__)
        dis.dis(fn.__code__)
