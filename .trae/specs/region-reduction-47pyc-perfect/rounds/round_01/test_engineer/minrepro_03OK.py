# Source Generated with Decompyle++ (Python version)
# File: minrepro_03.pyc (Python 3.11)

def nested_except_with_continue(data_list):
    for item in data_list:
        try:
            result = process(item)
            if result is None:
                pass
            else:
                break
        except ValueError:
            pass
def process(x):
    return x
