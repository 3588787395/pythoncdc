# Source Generated with Decompyle++ (Python version)
# File: subject.pyc (Python 3.11)

global events
events = []
def main():
    try:
        for i in range(5):
            try:
                if i == 1:
                    pass
            finally:
                events.append(('fin', i))
    finally:
        events.append('outer')
    return events
