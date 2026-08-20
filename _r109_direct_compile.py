"""Test compile the decompiled source directly"""
import dis

src = '''def test_try_wrap_for_else_break(data):
    try:
        for item in data:
            if isinstance(item, int):
                if item > 100:
                    break
                continue
            break
        else:
            return True
    except Exception as e:
        return False
'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_try_wrap_for_else_break':
        print("=== Direct compile ===")
        dis.dis(c)
        break
