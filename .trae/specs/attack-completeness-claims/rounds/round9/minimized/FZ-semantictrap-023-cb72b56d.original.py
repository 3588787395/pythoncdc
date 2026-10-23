events = []

def main():
    global events
    try:
        for i in range(5):
            try:
                if i == 1:
                    return ("ret", i)
            finally:
                events.append(("fin", i))
    finally:
        events.append("outer")
    return events
