def to_dict(self):
    data = {'name': 'x', 'size': 1}
    return data


def main():
    print(to_dict(object()))
