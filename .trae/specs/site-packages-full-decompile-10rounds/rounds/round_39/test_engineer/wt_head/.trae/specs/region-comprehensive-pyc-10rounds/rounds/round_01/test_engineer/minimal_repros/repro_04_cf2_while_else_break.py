# while-else with break
def test():
    counter = 0
    while counter < 10:
        if counter == 5:
            break
        counter += 1
    else:
        print("loop completed")
    return counter
