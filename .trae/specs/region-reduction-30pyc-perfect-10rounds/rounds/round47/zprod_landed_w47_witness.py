# Source Generated with Decompyle++ (Python version)
# File: z_landed_w47_witness.pyc (Python 3.11)

import os
import time
def w47_01_two_ifs_in_while(d, s):
    n = 0
    while True:
        if os.path.exists(d):
            n = os.path.getsize(d)
        if os.path.exists(s):
            n = n + os.path.getsize(s)
        time.sleep(3)
def w47_02_true_else_in_while(d, s):
    n = 0
    while True:
        if os.path.exists(d):
            n = os.path.getsize(d)
        else:
            n = os.path.getsize(s)
        time.sleep(3)
def w47_03_true_elif_in_while(d, s):
    n = 0
    while True:
        if os.path.exists(d):
            n = os.path.getsize(d)
        elif os.path.exists(s):
            n = 1
        else:
            n = 2
        time.sleep(3)
def w47_04_two_ifs_at_func_level(d, s):
    n = 0
    if os.path.exists(d):
        n = os.path.getsize(d)
    if os.path.exists(s):
        n = n + os.path.getsize(s)
    return n
def w47_05_two_ifs_in_for(d, s):
    total = 0
    for p in d:
        if os.path.exists(p):
            total = total + os.path.getsize(p)
        if os.path.exists(s):
            total = total + 1
    return total
def w47_06_two_ifs_in_cond_while(d, s, lim):
    i = 0
    n = 0
    while i < lim:
        if os.path.exists(d):
            n = os.path.getsize(d)
        if os.path.exists(s):
            n = n + os.path.getsize(s)
        i = i + 1
    return n
def w47_07_then_arm_multi_block_in_while(d, e, s):
    n = 0
    while True:
        if os.path.exists(d):
            if os.path.exists(e):
                n = os.path.getsize(e)
            else:
                n = 1
        elif os.path.exists(s):
            n = n + os.path.getsize(s)
        time.sleep(3)
def w47_08_three_sequential_ifs_in_while(d, e, s):
    n = 0
    while True:
        if os.path.exists(d):
            n = os.path.getsize(d)
        if os.path.exists(e):
            n = n + 1
        if os.path.exists(s):
            n = n + os.path.getsize(s)
        time.sleep(3)
