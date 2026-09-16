import dis

# Pattern 1: and with NOT
def p1():
    if a and not b:
        pass

# Pattern 2: or (De Morgan)
def p2():
    if not a or b:
        pass

print("=== a and not b ===")
dis.dis(p1)
print()
print("=== not a or b ===")
dis.dis(p2)
