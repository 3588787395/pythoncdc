events = []
def main():
    try:
        for i in range(5):
            try:
                    return ("ret", i)
            finally:
                events.append(("fin", i))
    finally:
        events.append("outer")
