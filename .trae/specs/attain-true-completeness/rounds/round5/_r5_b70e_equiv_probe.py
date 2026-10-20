# -*- coding: utf-8 -*-
"""Verify: nested with vs multi-with bytecode equivalence; return placement variants."""
import dis

def nested(p, a):
    while True:
        with open(p) as f:
            with open(p) as g:
                if a:
                    break
    return 6

def multi(p, a):
    while True:
        with open(p) as f, open(p) as g:
            if a:
                break
    return 6

def ret_inside(p, a):
    while True:
        with open(p) as f:
            if a:
                continue
            return 4

def ret_after_with_in_loop(p, a):
    while True:
        with open(p) as f:
            if a:
                continue
        return 4

def ret_after_loop(p, a):
    while True:
        with open(p) as f:
            if a:
                continue
    return 4

for fn in (nested, multi, ret_inside, ret_after_with_in_loop, ret_after_loop):
    print('=' * 20, fn.__name__, '=' * 20)
    dis.dis(fn)

print('nested == multi:', nested.__code__.co_code == multi.__code__.co_code)
print('nested consts == multi consts:', nested.__code__.co_consts == multi.__code__.co_consts)
print('ret_inside == ret_after_with_in_loop:',
      ret_inside.__code__.co_code == ret_after_with_in_loop.__code__.co_code)
