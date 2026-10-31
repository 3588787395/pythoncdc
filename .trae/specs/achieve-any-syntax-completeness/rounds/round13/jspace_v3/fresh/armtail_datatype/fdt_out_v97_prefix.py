# Source Generated with Decompyle++ (Python version)
# File: fdt.pyc (Python 3.11)

def _find_data_type_(mcls, class_name, bases):
    data_types = set()
    base_chain = set()
    for chain in bases:
        candidate = None
        for base in chain.__mro__:
            base_chain.add(base)
            if base is object:
                continue
            elif isinstance(base, EnumType):
                if base._member_type_ is not object:
                    data_types.add(base._member_type_)
                    break
                continue
            elif '__new__' in base.__dict__ or '__dataclass_fields__' in base.__dict__:
                if isinstance(base, EnumType):
                    continue
                else:
                    break
                continue
            else:
                candidate = candidate or base
        data_types.add(candidate or base)
        break
    if len(data_types) > 1:
        raise TypeError(f'too many data types for {class_name!r}: {data_types!r}')
    elif data_types:
        return data_types.pop()
