"""n3_01（负对照）: 无 else 基础循环 — for/while 单层顺序体。预期全 MATCH。"""


def simple_for(n):
    acc = []
    for i in range(n):
        acc.append(i * 2)
    return acc


def simple_while(n):
    k = 0
    acc = []
    while k < n:
        acc.append(k)
        k += 1
    return acc


def simple_for_break(n):
    acc = []
    for i in range(n):
        if i == 5:
            break
        acc.append(i)
    return acc


def simple_while_continue(n):
    acc = []
    k = 0
    while k < n:
        k += 1
        if k % 2 == 0:
            continue
        acc.append(k)
    return acc
