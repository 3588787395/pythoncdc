#!/usr/bin/env python3
"""Test: break in for-else inside function"""
import sys
import dis
sys.stdout.reconfigure(encoding='utf-8')

src = """
def test():
    for item in my_list:
        if item == 3:
            break
    else:
        print('not found')
        counter = 0
        while counter < 5:
            print(f'counter: {counter}')
            counter += 1
        while counter < 10:
            if counter == 7:
                break
            counter += 1
        else:
            for i in range(10):
                if i == 3:
                    continue
                elif i == 7:
                    break
                else:
                    print(i)
            return result
        print('loop done')
"""
code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test':
        print("=== test() function ===")
        for i in dis.get_instructions(c):
            print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
