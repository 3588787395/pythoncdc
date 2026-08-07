# Source Generated with Decompyle++ (Python version)
# File: base.pyc (Python 3.11)

class BaseObject(object):
    _repr_attr_list = []
    def __repr__(self):
        return '<{class_name} {property}>'.format(class_name=self.__class__.__name__, property={attr: getattr(self, attr, None) for attr in self._repr_attr_list})
