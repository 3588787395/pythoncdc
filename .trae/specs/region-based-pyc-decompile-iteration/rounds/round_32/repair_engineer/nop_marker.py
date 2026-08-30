# -*- coding: utf-8 -*-
"""Determine if the NOP after the loop-exit block is a universal for-else marker."""


def h1(algo, datalist):
    # for-else, no finally, no return (implicit)
    for item in datalist:
        x = item
    else:
        algo.set_instance()


def h2(algo, datalist):
    # for-else, no finally, explicit return
    for item in datalist:
        x = item
    else:
        algo.set_instance()
    return None


def h3(algo, datalist):
    # plain stmt after loop, no finally, explicit return
    for item in datalist:
        x = item
    algo.set_instance()
    return None


def h4(algo, datalist):
    # plain stmt after loop, no finally, no return (implicit)
    for item in datalist:
        x = item
    algo.set_instance()


def h5(algo, datalist):
    # for-else, no finally, statement AFTER the else (sibling)
    for item in datalist:
        x = item
    else:
        algo.set_instance()
    algo.after()


def h6(algo, datalist):
    # for-else with break
    for item in datalist:
        if item > 0:
            break
    else:
        algo.set_instance()
    algo.after()


def h7(algo, datalist):
    # for-else whose else returns
    for item in datalist:
        if item > 0:
            break
    else:
        algo.set_instance()
        return 1
    algo.after()


if __name__ == "__main__":
    import dis
    for fn in (h1, h2, h3, h4, h5, h6, h7):
        print("=" * 60)
        print(fn.__name__)
        dis.dis(fn.__code__)
