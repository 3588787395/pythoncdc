# Source Generated with Decompyle++ (Python version)
# File: enum.cpython-311.pyc (Python 3.11)

import sys
import builtins as bltns
from types import MappingProxyType, DynamicClassAttribute
from operator import or_ as _or_
from functools import reduce
__all__ = ['EnumType', 'EnumMeta', 'Enum', 'IntEnum', 'StrEnum', 'Flag', 'IntFlag', 'ReprEnum', 'auto', 'unique', 'property', 'verify', 'member', 'nonmember', 'FlagBoundary', 'STRICT', 'CONFORM', 'EJECT', 'KEEP', 'global_flag_repr', 'global_enum_repr', 'global_str', 'global_enum', 'EnumCheck', 'CONTINUOUS', 'NAMED_FLAGS', 'UNIQUE', 'pickle_by_global_name', 'pickle_by_enum_name']
Enum = Flag = EJECT = _stdlib_enums = ReprEnum = None
class nonmember(object):
    __doc__ = """
    Protects item from becoming an Enum member during class creation.
    """
    def __init__(self, value):
        self.value = value
class member(object):
    __doc__ = """
    Forces item to become an Enum member during class creation.
    """
    def __init__(self, value):
        self.value = value
def _is_descriptor(obj):
    """
    Returns True if obj is a descriptor, False otherwise.
    """
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')
def _is_dunder(name):
    """
    Returns True if a __dunder__ name, False otherwise.
    """
    return len(name) > 4 and name[:2] == name[-2:] == '__' and name[2] != '_' and name[-3] != '_'
def _is_sunder(name):
    """
    Returns True if a _sunder_ name, False otherwise.
    """
    return len(name) > 2 and name[0] == name[-1] == '_' and name[1:2] != '_' and name[-2:-1] != '_'
def _is_internal_class(cls_name, obj):
    if not isinstance(obj, type):
        return False
    qualname = getattr(obj, '__qualname__', '')
    s_pattern = cls_name + '.' + getattr(obj, '__name__', '')
    e_pattern = '.' + s_pattern
    return qualname == s_pattern or qualname.endswith(e_pattern)
def _is_private(cls_name, name):
    pattern = f'_{cls_name!s}__'
    pat_len = len(pattern)
    if len(name) > pat_len and name.startswith(pattern) and name[pat_len:pat_len + 1] != ['_']:
        return True
    return False
def _is_single_bit(num):
    """
    True if only one bit set in num (should be an int)
    """
    if num == 0:
        return False
    else:
        num &= num - 1
        return num == 0
def _make_class_unpicklable(obj):
    """
    Make the given obj un-picklable.

    obj should be either a dictionary, or an Enum
    """
    def _break_on_call_reduce(self, proto):
        raise TypeError('%r cannot be pickled' % self)
    if isinstance(obj, dict):
        obj['__reduce_ex__'] = _break_on_call_reduce
        obj['__module__'] = '<unknown>'
        return None
    else:
        setattr(obj, '__reduce_ex__', _break_on_call_reduce)
        setattr(obj, '__module__', '<unknown>')
def _iter_bits_lsb(num):
    original = num
    if isinstance(num, Enum):
        num = num.value
    if num < 0:
        raise ValueError('%r is not a positive integer' % original)
    while num:
        b = num & ~num + 1
        yield b
        num ^= b
def show_flag_values(value):
    return list(_iter_bits_lsb(value))
def bin(num, max_bits=None):
    """
    Like built-in bin(), except negative values are represented in
    twos-compliment, and the leading bit always indicates sign
    (0=positive, 1=negative).

    >>> bin(10)
    '0b0 1010'
    >>> bin(~10)   # ~10 is -11
    '0b1 0101'
    """
    ceiling = 2 ** num.bit_length()
    if num >= 0:
        s = bltns.bin(num + ceiling).replace('1', '0', 1)
    else:
        s = bltns.bin(~num ^ ceiling - 1 + ceiling)
    sign = s[:3]
    digits = s[3:]
    if max_bits is not None and len(digits) < max_bits:
        digits = (sign[-1] * max_bits + digits)[-max_bits:]
    return f'{sign!s} {digits!s}'
def _dedent(text):
    """
    Like textwrap.dedent.  Rewritten because we cannot import textwrap.
    """
    lines = text.split("""
""")
    blanks = 0
    for i, ch in enumerate(lines[0]):
        if ch != ' ':
            break
    for j, l in enumerate(lines):
        lines[j] = l[i:]
    return """
""".join(lines)
class _auto_null:
    def __repr__(self):
        return '_auto_null'
_auto_null = _auto_null()
class auto:
    __doc__ = """
    Instances are replaced with an appropriate value in Enum class suites.
    """
    def __init__(self, value=_auto_null):
        self.value = value
    def __repr__(self):
        return 'auto(%r)' % self.value
class property(DynamicClassAttribute):
    __doc__ = """
    This is a descriptor, used to define attributes that act differently
    when accessed through an enum member and through an enum class.
    Instance access is the same as property(), but access to an attribute
    through the enum class will instead look in the class' _member_map_ for
    a corresponding enum member.
    """
    def __get__(self, instance, ownerclass=None):
        if instance is None:
            try:
                return ownerclass._member_map_[self.name]
            except KeyError:
                raise AttributeError(f'{ownerclass!r} has no attribute {self.name!r}')
        elif self.fget is None:
            try:
                return ownerclass._member_map_[self.name]
            except KeyError:
                raise AttributeError(f'{ownerclass!r} has no attribute {self.name!r}') from None
        else:
            return self.fget(instance)
    def __set__(self, instance, value):
        if self.fset is None:
            raise AttributeError(f'<enum {self.clsname!r}> cannot set attribute {self.name!r}')
        return self.fset(instance, value)
    def __delete__(self, instance):
        if self.fdel is None:
            raise AttributeError(f'<enum {self.clsname!r}> cannot delete attribute {self.name!r}')
        return self.fdel(instance)
    def __set_name__(self, ownerclass, name):
        self.name = name
        self.clsname = ownerclass.__name__
class _proto_member:
    __doc__ = """
    intermediate step for enum members between class execution and final creation
    """
    def __init__(self, value):
        self.value = value
    def __set_name__(self, enum_class, member_name):
        """
        convert each quasi-member into an instance of the new enum class
        """
        delattr(enum_class, member_name)
        value = self.value
        if not isinstance(value, tuple):
            args = (value,)
        else:
            args = value
        if enum_class._member_type_ is tuple:
            args = (args,)
        if not enum_class._use_args_:
            enum_member = enum_class._new_member_(enum_class)
        else:
            enum_member = enum_class._new_member_(enum_class, *args)
        if not hasattr(enum_member, '_value_'):
            if enum_class._member_type_ is object:
                enum_member._value_ = value
            else:
                try:
                    enum_member._value_ = enum_class._member_type_(*args)
                except Exception as exc:
                    new_exc = TypeError('_value_ not set in __new__, unable to create it')
                    new_exc.__cause__ = exc
                    raise new_exc
        value = enum_member._value_
        enum_member._name_ = member_name
        enum_member.__objclass__ = enum_class
        enum_member.__init__(*args)
        enum_member._sort_order_ = len(enum_class._member_names_)
        if Flag is not None and issubclass(enum_class, Flag):
            enum_class._flag_mask_ |= value
            if _is_single_bit(value):
                enum_class._singles_mask_ |= value
            enum_class._all_bits_ = 2 ** enum_class._flag_mask_.bit_length() - 1
        try:
            try:
                enum_member = enum_class._value2member_map_[value]
            except TypeError:
                for name, canonical_member in enum_class._member_map_.items():
                    if canonical_member._value_ == value:
                        enum_member = canonical_member
                        break
                else:
                    raise KeyError
        except KeyError:
            if not Flag is not None or not issubclass(enum_class, Flag):
                enum_class._member_names_.append(member_name)
            elif Flag is not None and issubclass(enum_class, Flag) and _is_single_bit(value):
                enum_class._member_names_.append(member_name)
        found_descriptor = None
        for base in enum_class.__mro__[1:]:
            descriptor = base.__dict__.get(member_name)
            if descriptor is not None:
                if isinstance(descriptor, (property, DynamicClassAttribute)):
                    found_descriptor = descriptor
                    break
                if hasattr(descriptor, 'fget') and hasattr(descriptor, 'fset') and hasattr(descriptor, 'fdel'):
                    found_descriptor = descriptor
                    continue
                continue
        if found_descriptor:
            redirect = property()
            redirect.member = enum_member
            redirect.__set_name__(enum_class, member_name)
            redirect.fget = found_descriptor.fget
            redirect.fset = found_descriptor.fset
            redirect.fdel = found_descriptor.fdel
            setattr(enum_class, member_name, redirect)
        else:
            setattr(enum_class, member_name, enum_member)
        enum_class._member_map_[member_name] = enum_member
        try:
            enum_class._value2member_map_.setdefault(value, enum_member)
            return None
        except TypeError:
            enum_class._unhashable_values_.append(value)
            return None
class _EnumDict(dict):
    __doc__ = """
    Track enum member order and ensure member names are not reused.

    EnumType will use the names found in self._member_names as the
    enumeration member names.
    """
    def __init__(self):
        super().__init__()
        self._member_names = {}
        self._last_values = []
        self._ignore = []
        self._auto_called = False
    def __setitem__(self, key, value):
        """
        Changes anything not dundered or not a descriptor.

        If an enum member name is used twice, an error is raised; duplicate
        values are not checked for.

        Single underscore (sunder) names are reserved.
        """
        if _is_internal_class(self._cls_name, value):
            import warnings
            warnings.warn('In 3.13 classes created inside an enum will not become a member.  Use the `member` decorator to keep the current behavior.', DeprecationWarning, stacklevel=2)
        if _is_private(self._cls_name, key):
            pass
        elif _is_sunder(key):
            if key not in ('_order_', '_generate_next_value_', '_numeric_repr_', '_missing_', '_ignore_', '_iter_member_', '_iter_member_by_value_', '_iter_member_by_def_'):
                raise ValueError(f'_sunder_ names, such as {key!r}, are reserved for future Enum use')
            elif key == '_generate_next_value_':
                if self._auto_called:
                    raise TypeError('_generate_next_value_ must be defined before members')
                _gnv = value.__func__ if isinstance(value, staticmethod) else value
                setattr(self, '_generate_next_value', _gnv)
            elif key == '_ignore_':
                if isinstance(value, str):
                    value = value.replace(',', ' ').split()
                else:
                    value = list(value)
                self._ignore = value
                already = set(value) & set(self._member_names)
                if already:
                    raise ValueError(f'_ignore_ cannot specify already set names: {already!r}')
        elif _is_dunder(key):
            if key == '__order__':
                key = '_order_'
        elif key in self._member_names:
            raise TypeError(f'{key!r} already defined as {self[key]!r}')
        elif key in self._ignore:
            pass
        elif isinstance(value, nonmember):
            value = value.value
        elif _is_descriptor(value):
            pass
        else:
            if key in self:
                raise TypeError(f'{key!r} already defined as {self[key]!r}')
            elif isinstance(value, member):
                value = value.value
            non_auto_store = True
            single = False
            if isinstance(value, auto):
                single = True
                value = (value,)
            if type(value) is tuple and any((isinstance(v, auto) for v in value)):
                auto_valued = []
                for v in value:
                    if isinstance(v, auto):
                        non_auto_store = False
                        if v.value == _auto_null:
                            v.value = self._generate_next_value(key, 1, len(self._member_names), self._last_values[:])
                            self._auto_called = True
                        v = v.value
                        self._last_values.append(v)
                    auto_valued.append(v)
                if single:
                    value = auto_valued[0]
                else:
                    value = tuple(auto_valued)
            self._member_names[key] = None
            if non_auto_store:
                self._last_values.append(value)
        super().__setitem__(key, value)
    def update(self, members, **more_members):
        try:
            for name in members.keys():
                self[name] = members[name]
        except AttributeError:
            for name, value in members:
                self[name] = value
        for name, value in more_members.items():
            self[name] = value
class EnumType(type):
    __doc__ = """
    Metaclass for Enum
    """
    @classmethod
    def __prepare__(metacls, cls, bases, **kwds):
        metacls._check_for_existing_members_(cls, bases)
        enum_dict = _EnumDict()
        enum_dict._cls_name = cls
        member_type, first_enum = metacls._get_mixins_(cls, bases)
        if first_enum is not None:
            enum_dict['_generate_next_value_'] = getattr(first_enum, '_generate_next_value_', None)
        return enum_dict
    def __new__(metacls, cls, bases, classdict, *, boundary=None, _simple=False, **kwds):
        if _simple:
            return super().__new__(metacls, cls, bases, classdict, **(kwds))
        classdict.setdefault('_ignore_', []).append('_ignore_')
        ignore = classdict['_ignore_']
        for key in ignore:
            classdict.pop(key, None)
        member_names = classdict._member_names
        invalid_names = set(member_names) & {'mro', ''}
        if invalid_names:
            raise ValueError('invalid enum member name(s) %s' % ','.join((repr(n) for n in invalid_names)))
        _order_ = classdict.pop('_order_', None)
        classdict = dict(classdict.items())
        member_type, first_enum = metacls._get_mixins_(cls, bases)
        __new__, save_new, use_args = metacls._find_new_(classdict, member_type, first_enum)
        classdict['_new_member_'] = __new__
        classdict['_use_args_'] = use_args
        for name in member_names:
            value = classdict[name]
            classdict[name] = _proto_member(value)
        classdict['_member_names_'] = []
        classdict['_member_map_'] = {}
        classdict['_value2member_map_'] = {}
        classdict['_unhashable_values_'] = []
        classdict['_member_type_'] = member_type
        classdict['_value_repr_'] = metacls._find_data_repr_(cls, bases)
        classdict['_boundary_'] = boundary or getattr(first_enum, '_boundary_', None)
        classdict['_flag_mask_'] = 0
        classdict['_singles_mask_'] = 0
        classdict['_all_bits_'] = 0
        classdict['_inverted_'] = None
        try:
            enum_class = super().__new__(metacls, cls, bases, classdict, **(kwds))
        except RuntimeError as e:
            e.__cause__
            e
        if exc is not None:
            raise exc
        classdict.update(enum_class.__dict__)
        if ReprEnum is not None and ReprEnum in bases:
            if member_type is object:
                raise TypeError('ReprEnum subclasses must be mixed with a data type (i.e. int, str, float, etc.)')
            if '__format__' not in classdict:
                enum_class.__format__ = member_type.__format__
                classdict['__format__'] = enum_class.__format__
            if '__str__' not in classdict:
                method = member_type.__str__
                if method is object.__str__:
                    method = member_type.__repr__
                enum_class.__str__ = method
                classdict['__str__'] = enum_class.__str__
        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            if name not in classdict:
                enum_method = getattr(first_enum, name)
                found_method = getattr(enum_class, name)
                object_method = getattr(object, name)
                data_type_method = getattr(member_type, name)
                if found_method in (data_type_method, object_method):
                    setattr(enum_class, name, enum_method)
        if Flag is not None and issubclass(enum_class, Flag):
            for name in ('__or__', '__and__', '__xor__', '__ror__', '__rand__', '__rxor__', '__invert__'):
                if name not in classdict:
                    enum_method = getattr(Flag, name)
                    setattr(enum_class, name, enum_method)
                    classdict[name] = enum_method
        if Enum is not None:
            if save_new:
                enum_class.__new_member__ = __new__
            enum_class.__new__ = Enum.__new__
        if _order_ is not None and isinstance(_order_, str):
            _order_ = _order_.replace(',', ' ').split()
        if not (Flag is None and cls != 'Flag'):
            if Flag is not None:
                if not issubclass(enum_class, Flag):
                    delattr(enum_class, '_boundary_')
                    delattr(enum_class, '_flag_mask_')
                    delattr(enum_class, '_singles_mask_')
                    delattr(enum_class, '_all_bits_')
                    delattr(enum_class, '_inverted_')
                elif Flag is not None and issubclass(enum_class, Flag):
                    member_list = [m._value_ for m in enum_class]
                    if member_list != sorted(member_list):
                        enum_class._iter_member_ = enum_class._iter_member_by_def_
                    if _order_:
                        _order_ = [o for o in _order_ if o not in enum_class._member_map_ or _is_single_bit(enum_class[o]._value_)]
        if _order_:
            _order_ = [o for o in _order_ if o not in enum_class._member_map_ or o in enum_class._member_map_ and o in enum_class._member_names_]
            if _order_ != enum_class._member_names_:
                raise TypeError(f'member order does not match _order_:\n  {enum_class._member_names_!r}\n  {_order_!r}')
        return enum_class
    def __bool__(cls):
        """
        classes/types should always be True.
        """
        return True
    def __call__(cls, value, names=None, *, module=None, qualname=None, type=None, start=1, boundary=None):
        """
        Either returns an existing member, or creates a new enum class.

        This method is used both when an enum class is given a value to match
        to an enumeration member (i.e. Color(3)) and for the functional API
        (i.e. Color = Enum('Color', names='RED GREEN BLUE')).

        When used for the functional API:

        `value` will be the name of the new class.

        `names` should be either a string of white-space/comma delimited names
        (values will start at `start`), or an iterator/mapping of name, value pairs.

        `module` should be set to the module this class is being created in;
        if it is not set, an attempt to find that module will be made, but if
        it fails the class will not be picklable.

        `qualname` should be set to the actual location this class can be found
        at in its module; by default it is set to the global scope.  If this is
        not correct, unpickling will fail in some circumstances.

        `type`, if set, will be mixed in as the first base class.
        """
        if names is None:
            return cls.__new__(cls, value)
        else:
            return cls._create_(value, names, module=module, qualname=qualname, type=type, start=start, boundary=boundary)
    def __contains__(cls, member):
        """
        Return True if member is a member of this enum
        raises TypeError if member is not an enum member

        note: in 3.12 TypeError will no longer be raised, and True will also be
        returned if member is the value of a member in this enum
        """
        if not isinstance(member, Enum):
            import warnings
            warnings.warn("""in 3.12 __contains__ will no longer raise TypeError, but will return True or
False depending on whether the value is a member or the value of a member""", DeprecationWarning, stacklevel=2)
            raise TypeError(f'unsupported operand type(s) for \'in\': \'{type(member).__qualname__!s}\' and \'{cls.__class__.__qualname__!s}\'')
        return isinstance(member, cls) and member._name_ in cls._member_map_
    def __delattr__(cls, attr):
        if attr in cls._member_map_:
            raise AttributeError(f'{cls.__name__!r} cannot delete member {attr!r}.')
        super().__delattr__(attr)
    def __dir__(cls):
        interesting = set(['__class__', '__contains__', '__doc__', '__getitem__', '__iter__', '__len__', '__members__', '__module__', '__name__', '__qualname__'] + cls._member_names_)
        if cls._new_member_ is not object.__new__:
            interesting.add('__new__')
        if cls.__init_subclass__ is not object.__init_subclass__:
            interesting.add('__init_subclass__')
        if cls._member_type_ is object:
            return sorted(interesting)
        else:
            return sorted(set(dir(cls._member_type_)) | interesting)
    def __getattr__(cls, name):
        """
        Return the enum member matching `name`

        We use __getattr__ instead of descriptors or inserting into the enum
        class' __dict__ in order to support `name` and `value` being both
        properties for enum members (which live in the class' __dict__) and
        enum members themselves.
        """
        if _is_dunder(name):
            raise AttributeError(name)
        try:
            return cls._member_map_[name]
        except KeyError:
            raise AttributeError(name) from None
    def __getitem__(cls, name):
        """
        Return the member matching `name`.
        """
        return cls._member_map_[name]
    def __iter__(cls):
        """
        Return members in definition order.
        """
        return (cls._member_map_[name] for name in cls._member_names_)
    def __len__(cls):
        """
        Return the number of members (no aliases)
        """
        return len(cls._member_names_)
    @bltns.property
    def __members__(cls):
        """
        Returns a mapping of member name->value.

        This mapping lists all enum members, including aliases. Note that this
        is a read-only view of the internal mapping.
        """
        return MappingProxyType(cls._member_map_)
    def __repr__(cls):
        if Flag is not None and issubclass(cls, Flag):
            return '<flag %r>' % cls.__name__
        return '<enum %r>' % cls.__name__
    def __reversed__(cls):
        """
        Return members in reverse definition order.
        """
        return (cls._member_map_[name] for name in reversed(cls._member_names_))
    def __setattr__(cls, name, value):
        """
        Block attempts to reassign Enum members.

        A simple assignment to the class namespace only changes one of the
        several possible ways to get an Enum member from the Enum class,
        resulting in an inconsistent Enumeration.
        """
        member_map = cls.__dict__.get('_member_map_', {})
        if name in member_map:
            raise AttributeError(f'cannot reassign member {name!r}')
        super().__setattr__(name, value)
    def _create_(cls, class_name, names, *, module=None, qualname=None, type=None, start=1, boundary=None):
        """
        Convenience method to create a new Enum class.

        `names` can be:

        * A string containing member names, separated either with spaces or
          commas.  Values are incremented by 1 from `start`.
        * An iterable of member names.  Values are incremented by 1 from `start`.
        * An iterable of (member name, value) pairs.
        * A mapping of member name -> value pairs.
        """
        metacls = cls.__class__
        bases = (cls,) if type is None else (type, cls)
        _, first_enum = cls._get_mixins_(class_name, bases)
        classdict = metacls.__prepare__(class_name, bases)
        if isinstance(names, str):
            names = names.replace(',', ' ').split()
        if isinstance(names, (tuple, list)) and names and isinstance(names[0], str):
            original_names, names = (names, [])
            last_values = []
            for count, name in enumerate(original_names):
                value = first_enum._generate_next_value_(name, start, count, last_values[:])
                last_values.append(value)
                names.append((name, value))
        if names is None:
            names = ()
        for item in names:
            if isinstance(item, str):
                member_name, member_value = (item, names[item])
            else:
                member_name, member_value = item
            classdict[member_name] = member_value
        if module is None:
            try:
                module = sys._getframe(2).f_globals['__name__']
            except (AttributeError, ValueError, KeyError):
                pass
        if module is None:
            _make_class_unpicklable(classdict)
        else:
            classdict['__module__'] = module
        if qualname is not None:
            classdict['__qualname__'] = qualname
        return metacls.__new__(metacls, class_name, bases, classdict, boundary=boundary)
    def _convert_(cls, name, module, filter, source=None, *, boundary=None, as_global=False):
        """
        Create a new Enum subclass that replaces a collection of global constants
        """
        module_globals = sys.modules[module].__dict__
        if source:
            source = source.__dict__
        else:
            source = module_globals
        members = [(name, value) for name, value in source.items() if filter(name)]
        try:
            members.sort(key=lambda t: (t[1], t[0]))
        except TypeError:
            members.sort(key=lambda t: t[0])
        cls = boundary or KEEP
        if as_global:
            global_enum(cls)
        else:
            sys.modules[cls.__module__].__dict__.update(cls.__members__)
        module_globals[name] = cls
        return cls
    @classmethod
    def _check_for_existing_members_(mcls, class_name, bases):
        for chain in bases:
            for base in chain.__mro__:
                if isinstance(base, EnumType) and base._member_names_:
                    raise TypeError(f'<enum {class_name!r}> cannot extend {base!r}')
    @classmethod
    def _get_mixins_(mcls, class_name, bases):
        """
        Returns the type for creating enum members, and the first inherited
        enum class.

        bases: the tuple of bases that was given to __new__
        """
        if not bases:
            return (object, Enum)
        else:
            mcls._check_for_existing_members_(class_name, bases)
            first_enum = bases[-1]
            if not isinstance(first_enum, EnumType):
                raise TypeError('new enumerations should be created as `EnumName([mixin_type, ...] [data_type,] enum_type)`')
            member_type = mcls._find_data_type_(class_name, bases) or object
            return (member_type, first_enum)
    @classmethod
    def _find_data_repr_(mcls, class_name, bases):
        for chain in bases:
            for base in chain.__mro__:
                if base is object:
                    continue
                elif isinstance(base, EnumType):
                    return base._value_repr_
                elif '__repr__' in base.__dict__:
                    return base.__dict__['__repr__']
                else:
                    continue
    @classmethod
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
    @classmethod
    def _find_new_(mcls, classdict, member_type, first_enum):
        """
        Returns the __new__ to be used for creating the enum members.

        classdict: the class dictionary given to __new__
        member_type: the data type whose __new__ will be used by default
        first_enum: enumeration to check for an overriding __new__
        """
        __new__ = classdict.get('__new__', None)
        save_new = first_enum is not None and __new__ is not None
        if __new__ is None:
            for method in ('__new_member__', '__new__'):
                for possible in (member_type, first_enum):
                    target = getattr(possible, method, None)
                    if target not in {None, None.__new__, object.__new__, Enum.__new__}:
                        __new__ = target
                        break
                if __new__ is not None:
                    break
                if first_enum is None or __new__ in (Enum.__new__, object.__new__):
                    use_args = False
                else:
                    use_args = True
            else:
                __new__ = object.__new__
        return (__new__, save_new, use_args)
EnumMeta = EnumType
class Enum(metaclass=EnumType):
    __doc__ = """
    Create a collection of name/value pairs.

    Example enumeration:

    >>> class Color(Enum):
    ...     RED = 1
    ...     BLUE = 2
    ...     GREEN = 3

    Access them by:

    - attribute access::

    >>> Color.RED
    <Color.RED: 1>

    - value lookup:

    >>> Color(1)
    <Color.RED: 1>

    - name lookup:

    >>> Color['RED']
    <Color.RED: 1>

    Enumerations can be iterated over, and know how many members they have:

    >>> len(Color)
    3

    >>> list(Color)
    [<Color.RED: 1>, <Color.BLUE: 2>, <Color.GREEN: 3>]

    Methods can be added to enumerations, and members can have their own
    attributes -- see the documentation for details.
    """
    def __new__(cls, value):
        if type(value) is cls:
            return value
        try:
            return cls._value2member_map_[value]
        except KeyError:
            pass
        except TypeError:
            for member in cls._member_map_.values():
                if member._value_ == value:
                    return member
        if not cls._member_map_:
            raise TypeError('%r has no members defined' % cls)
        try:
            result = cls._missing_(value)
        except Exception as e:
            exc = e
            result = None
        try:
            if isinstance(result, cls):
                return result
            elif Flag is not None and issubclass(cls, Flag) and cls._boundary_ is EJECT and isinstance(result, int):
                return result
            else:
                ve_exc = ValueError(f'{value!r} is not a valid {cls.__qualname__!s}')
                if result is None and exc is None:
                    raise ve_exc
                if exc is None:
                    exc = TypeError(f'error in {cls.__name__!s}._missing_: returned {result!r} instead of None or a valid member')
                if not isinstance(exc, ValueError):
                    exc.__context__ = ve_exc
                raise exc
        finally:
            ve_exc = None
    def __init__(self, *args, **kwds):
        return None
    def _generate_next_value_(name, start, count, last_values):
        """
        Generate the next value when not given.

        name: the name of the member
        start: the initial start value or None
        count: the number of existing members
        last_values: the list of values assigned
        """
        if not last_values:
            return start
        try:
            last = last_values[-1]
            last_values.sort()
            if last == last_values[-1]:
                return last + 1
            else:
                raise TypeError
        except TypeError:
            import warnings
            warnings.warn("""In 3.13 the default `auto()`/`_generate_next_value_` will require all values to be sortable and support adding +1
and the value returned will be the largest value in the enum incremented by 1""", DeprecationWarning, stacklevel=3)
            for v in reversed(last_values):
                try:
                    return v + 1
                except TypeError:
                    pass
            return start
            return None
    @classmethod
    def _missing_(cls, value):
        return None
    def __repr__(self):
        v_repr = self.__class__._value_repr_ or repr
        return f'<{self.__class__.__name__!s}.{self._name_!s}: {v_repr(self._value_)!s}>'
    def __str__(self):
        return f'{self.__class__.__name__!s}.{self._name_!s}'
    def __dir__(self):
        """
        Returns public methods and other interesting attributes.
        """
        interesting = set()
        if self.__class__._member_type_ is not object:
            interesting = set(object.__dir__(self))
        for name in getattr(self, '__dict__', []):
            if name[0] != '_' and name not in self._member_map_:
                interesting.add(name)
        for cls in self.__class__.mro():
            for name, obj in cls.__dict__.items():
                if name[0] == '_':
                    continue
                if isinstance(obj, property):
                    if not obj.fget is None or name not in self._member_map_:
                        interesting.add(name)
                        continue
                    interesting.discard(name)
                    continue
                    continue
                if name not in self._member_map_:
                    interesting.add(name)
                continue
                continue
        names = sorted(set(['__class__', '__doc__', '__eq__', '__hash__', '__module__']) | interesting)
        return names
    def __format__(self, format_spec):
        return str.__format__(str(self), format_spec)
    def __hash__(self):
        return hash(self._name_)
    def __reduce_ex__(self, proto):
        return (self.__class__, (self._value_,))
    def __deepcopy__(self, memo):
        return self
    def __copy__(self):
        return self
    @property
    def name(self):
        """The name of the Enum member."""
        return self._name_
    @property
    def value(self):
        """The value of the Enum member."""
        return self._value_
class ReprEnum(Enum):
    __doc__ = """
    Only changes the repr(), leaving str() and format() to the mixed-in type.
    """
class IntEnum(int, ReprEnum):
    __doc__ = """
    Enum where members are also (and must be) ints
    """
class StrEnum(str, ReprEnum):
    __doc__ = """
    Enum where members are also (and must be) strings
    """
    def __new__(cls, *values):
        """values must already be of type `str`"""
        if len(values) > 3:
            raise TypeError(f'too many arguments for str(): {values!r}')
        elif len(values) == 1 and not isinstance(values[0], str):
            raise TypeError(f'{values[0]!r} is not a string')
        elif len(values) >= 2 and isinstance(values[1], str):
            raise TypeError(f'encoding must be a string, not {values[1]!r}')
        elif len(values) == 3 and not isinstance(values[2], str):
            raise TypeError('errors must be a string, not %r' % values[2])
        else:
            value = str(*values)
            member = str.__new__(cls, value)
            member._value_ = value
            return member
    def _generate_next_value_(name, start, count, last_values):
        """
        Return the lower-cased version of the member name.
        """
        return name.lower()
def pickle_by_global_name(self, proto):
    return self.name
_reduce_ex_by_global_name = pickle_by_global_name
def pickle_by_enum_name(self, proto):
    return (getattr, (self.__class__, self._name_))
class FlagBoundary(StrEnum):
    __doc__ = """
    control how out of range values are handled
    "strict" -> error is raised             [default for Flag]
    "conform" -> extra bits are discarded
    "eject" -> lose flag status
    "keep" -> keep flag status and all bits [default for IntFlag]
    """
    STRICT = auto()
    CONFORM = auto()
    EJECT = auto()
    KEEP = auto()
STRICT, CONFORM, EJECT, KEEP = FlagBoundary
class Flag(Enum, boundary=STRICT):
    __doc__ = """
    Support for flags
    """
    _numeric_repr_ = repr
    def _generate_next_value_(name, start, count, last_values):
        """
        Generate the next value when not given.

        name: the name of the member
        start: the initial start value or None
        count: the number of existing members
        last_values: the last value assigned or None
        """
        if not count:
            return start if start is not None else 1
        last_value = max(last_values)
        try:
            high_bit = _high_bit(last_value)
        except Exception:
            raise TypeError('invalid flag value %r' % last_value) from None
        return 2 ** (high_bit + 1)
    @classmethod
    def _iter_member_by_value_(cls, value):
        """
        Extract all members from the value in definition (i.e. increasing value) order.
        """
        for val in _iter_bits_lsb(value & cls._flag_mask_):
            yield cls._value2member_map_.get(val)
    _iter_member_ = _iter_member_by_value_
    @classmethod
    def _iter_member_by_def_(cls, value):
        """
        Extract all members from the value in definition order.
        """
        yield from sorted(cls._iter_member_by_value_(value), key=lambda m: m._sort_order_)
    @classmethod
    def _missing_(cls, value):
        """
        Create a composite member containing all canonical members present in `value`.

        If non-member values are present, result depends on `_boundary_` setting.
        """
        if not isinstance(value, int):
            raise ValueError(f'{value!r} is not a valid {cls.__qualname__!s}')
        flag_mask = cls._flag_mask_
        singles_mask = cls._singles_mask_
        all_bits = cls._all_bits_
        neg_value = None
        if ~all_bits <= value <= all_bits:
            if value & (all_bits ^ flag_mask):
                if cls._boundary_ is STRICT:
                    max_bits = max(value.bit_length(), flag_mask.bit_length())
                    raise ValueError(f'{cls!r} invalid value {value!r}\n    given {bin(value, max_bits)!s}\n  allowed {bin(flag_mask, max_bits)!s}')
                elif cls._boundary_ is CONFORM:
                    value = value & flag_mask
                elif cls._boundary_ is EJECT:
                    return value
                elif cls._boundary_ is KEEP:
                    if value < 0:
                        value = max(all_bits + 1, 2 ** value.bit_length()) + value
                else:
                    raise ValueError(f'{cls!r} unknown flag boundary {cls._boundary_!r}')
        if value < 0:
            neg_value = value
            value = all_bits + 1 + value
        unknown = value & ~flag_mask
        aliases = value & ~singles_mask
        member_value = value & singles_mask
        if unknown and cls._boundary_ is not KEEP:
            raise ValueError(f'{cls.__name__!s}({value!r}) -->  unknown values {unknown!r} [{bin(unknown)!s}]')
        if cls._member_type_ is object:
            pseudo_member = object.__new__(cls)
        else:
            pseudo_member = cls._member_type_.__new__(cls, value)
        if not hasattr(pseudo_member, '_value_'):
            pseudo_member._value_ = value
        if member_value or aliases:
            members = []
            combined_value = 0
            for m in cls._iter_member_(member_value):
                members.append(m)
                combined_value |= m._value_
            if aliases:
                value = member_value | aliases
                for n, pm in cls._member_map_.items():
                    if pm not in members and pm._value_ and pm._value_ & value == pm._value_:
                        members.append(pm)
                        combined_value |= pm._value_
            unknown = value ^ combined_value
            pseudo_member._name_ = '|'.join([m._name_ for m in members])
            if not combined_value:
                pseudo_member._name_ = None
            else:
                if unknown and cls._boundary_ is STRICT:
                    raise ValueError(f'{cls!r}: no members with value {unknown!r}')
                if unknown:
                    pseudo_member._name_ += '|%s' % cls._numeric_repr_(unknown)
        else:
            pseudo_member._name_ = None
        pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
        if neg_value is not None:
            cls._value2member_map_[neg_value] = pseudo_member
        return pseudo_member
    def __contains__(self, other):
        """
        Returns True if self has at least the same flags set as other.
        """
        if not isinstance(other, self.__class__):
            raise TypeError(f'unsupported operand type(s) for \'in\': {type(other).__qualname__!r} and {self.__class__.__qualname__!r}')
        return other._value_ & self._value_ == other._value_
    def __iter__(self):
        """
        Returns flags in definition order.
        """
        yield from self._iter_member_(self._value_)
    def __len__(self):
        return self._value_.bit_count()
    def __repr__(self):
        cls_name = self.__class__.__name__
        v_repr = self.__class__._value_repr_ or repr
        if self._name_ is None:
            return f'<{cls_name!s}: {v_repr(self._value_)!s}>'
        else:
            return f'<{cls_name!s}.{self._name_!s}: {v_repr(self._value_)!s}>'
    def __str__(self):
        cls_name = self.__class__.__name__
        if self._name_ is None:
            return f'{cls_name!s}({self._value_!r})'
        else:
            return f'{cls_name!s}.{self._name_!s}'
    def __bool__(self):
        return bool(self._value_)
    def __or__(self, other):
        if isinstance(other, self.__class__):
            other = other._value_
        elif self._member_type_ is not object and isinstance(other, self._member_type_):
            other = other
        else:
            return NotImplemented
        value = self._value_
        return self.__class__(value | other)
    def __and__(self, other):
        if isinstance(other, self.__class__):
            other = other._value_
        elif self._member_type_ is not object and isinstance(other, self._member_type_):
            other = other
        else:
            return NotImplemented
        value = self._value_
        return self.__class__(value & other)
    def __xor__(self, other):
        if isinstance(other, self.__class__):
            other = other._value_
        elif self._member_type_ is not object and isinstance(other, self._member_type_):
            other = other
        else:
            return NotImplemented
        value = self._value_
        return self.__class__(value ^ other)
    def __invert__(self):
        if self._inverted_ is None:
            if self._boundary_ in (EJECT, KEEP):
                self._inverted_ = self.__class__(~self._value_)
            else:
                self._inverted_ = self.__class__(self._singles_mask_ & ~self._value_)
        return self._inverted_
    __rand__ = __and__
    __ror__ = __or__
    __rxor__ = __xor__
class IntFlag(int, ReprEnum, Flag, boundary=KEEP):
    __doc__ = """
    Support for integer-based Flags
    """
def _high_bit(value):
    """
    returns index of highest bit, or -1 if value is zero or negative
    """
    return value.bit_length() - 1
def unique(enumeration):
    """
    Class decorator for enumerations ensuring unique member values.
    """
    duplicates = []
    for name, member in enumeration.__members__.items():
        if name != member.name:
            duplicates.append((name, member.name))
    if duplicates:
        alias_details = ', '.join([f'{alias!s} -> {name!s}' for alias, name in duplicates])
        raise ValueError(f'duplicate values found in {enumeration!r}: {alias_details!s}')
    return enumeration
def _power_of_two(value):
    if value < 1:
        return False
    else:
        return value == 2 ** _high_bit(value)
def global_enum_repr(self):
    """
    use module.enum_name instead of class.enum_name

    the module is the last module in case of a multi-module name
    """
    module = self.__class__.__module__.split('.')[-1]
    return f'{module!s}.{self._name_!s}'
def global_flag_repr(self):
    """
    use module.flag_name instead of class.flag_name

    the module is the last module in case of a multi-module name
    """
    module = self.__class__.__module__.split('.')[-1]
    cls_name = self.__class__.__name__
    if self._name_ is None:
        return f'{module!s}.{cls_name!s}({self._value_!r})'
    elif _is_single_bit(self):
        return f'{module!s}.{self._name_!s}'
    elif self._boundary_ is not FlagBoundary.KEEP:
        return '|'.join([f'{module!s}.{name!s}' for name in self.name.split('|')])
    else:
        name = []
        for n in self._name_.split('|'):
            if n[0].isdigit():
                name.append(n)
                continue
            name.append(f'{module!s}.{n!s}')
            continue
        return '|'.join(name)
def global_str(self):
    """
    use enum_name instead of class.enum_name
    """
    if self._name_ is None:
        cls_name = self.__class__.__name__
        return f'{cls_name!s}({self._value_!r})'
    else:
        return self._name_
def global_enum(cls, update_str=False):
    """
    decorator that makes the repr() of an enum member reference its module
    instead of its class; also exports all members to the enum's module's
    global namespace
    """
    if issubclass(cls, Flag):
        cls.__repr__ = global_flag_repr
    else:
        cls.__repr__ = global_enum_repr
    if not issubclass(cls, ReprEnum) or update_str:
        cls.__str__ = global_str
    sys.modules[cls.__module__].__dict__.update(cls.__members__)
    return cls
def _simple_enum(etype=Enum, *, boundary=None, use_args=None):
    """
    Class decorator that converts a normal class into an :class:`Enum`.  No
    safety checks are done, and some advanced behavior (such as
    :func:`__init_subclass__`) is not available.  Enum creation can be faster
    using :func:`simple_enum`.

        >>> from enum import Enum, _simple_enum
        >>> @_simple_enum(Enum)
        ... class Color:
        ...     RED = auto()
        ...     GREEN = auto()
        ...     BLUE = auto()
        >>> Color
        <enum 'Color'>
    """
    def convert_class(cls):
        nonlocal use_args
        cls_name = cls.__name__
        if use_args is None:
            use_args = etype._use_args_
        __new__ = cls.__dict__.get('__new__')
        if __new__ is not None:
            new_member = __new__.__func__
        else:
            new_member = etype._member_type_.__new__
        attrs = {}
        body = {}
        if __new__ is not None:
            body['__new_member__'] = new_member
        body['_new_member_'] = new_member
        body['_use_args_'] = use_args
        body['_generate_next_value_'] = etype._generate_next_value_
        body['_member_names_'] = []
        body['_member_map_'] = {}
        body['_value2member_map_'] = {}
        body['_unhashable_values_'] = []
        body['_member_type_'] = etype._member_type_
        body['_value_repr_'] = etype._value_repr_
        if issubclass(etype, Flag):
            body['_boundary_'] = boundary or etype._boundary_
            body['_flag_mask_'] = None
            body['_all_bits_'] = None
            body['_singles_mask_'] = None
            body['_inverted_'] = None
            body['__or__'] = Flag.__or__
            body['__xor__'] = Flag.__xor__
            body['__and__'] = Flag.__and__
            body['__ror__'] = Flag.__ror__
            body['__rxor__'] = Flag.__rxor__
            body['__rand__'] = Flag.__rand__
            body['__invert__'] = Flag.__invert__
        for name, obj in cls.__dict__.items():
            if name in ('__dict__', '__weakref__'):
                continue
            if _is_dunder(name) or _is_private(cls_name, name) or _is_sunder(name) or _is_descriptor(obj):
                body[name] = obj
                continue
            attrs[name] = obj
            continue
            continue
        if cls.__dict__.get('__doc__') is None:
            body['__doc__'] = 'An enumeration.'
        enum_class = type(cls_name, (etype,), body, boundary=boundary, _simple=True)
        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            if name not in body:
                enum_method = getattr(etype, name)
                found_method = getattr(enum_class, name)
                object_method = getattr(object, name)
                data_type_method = getattr(member_type, name)
                if found_method in (data_type_method, object_method):
                    setattr(enum_class, name, enum_method)
        gnv_last_values = []
        if issubclass(enum_class, Flag):
            single_bits = 0
            for name, value in attrs.items():
                if isinstance(value, auto) and auto.value is _auto_null:
                    value = gnv(name, 1, len(member_names), gnv_last_values)
                if value in value2member_map:
                    redirect = property()
                    redirect.__set_name__(enum_class, name)
                    setattr(enum_class, name, redirect)
                    member_map[name] = value2member_map[value]
                    continue
                if use_args:
                    if not isinstance(value, tuple):
                        value = (value,)
                    member = new_member(enum_class, *value)
                    value = value[0]
                else:
                    member = new_member(enum_class)
                if __new__ is None:
                    member._value_ = value
                member._name_ = name
                member.__objclass__ = enum_class
                member.__init__(value)
                redirect = property()
                redirect.__set_name__(enum_class, name)
                setattr(enum_class, name, redirect)
                member_map[name] = member
                member._sort_order_ = len(member_names)
                value2member_map[value] = member
                if _is_single_bit(value):
                    member_names.append(name)
                    single_bits |= value
                else:
                    multi_bits |= value
                gnv_last_values.append(value)
                continue
            enum_class._flag_mask_ = single_bits | multi_bits
            enum_class._singles_mask_ = single_bits
            enum_class._all_bits_ = 2 ** (single_bits | multi_bits).bit_length() - 1
            member_list = [m._value_ for m in enum_class]
            if member_list != sorted(member_list):
                enum_class._iter_member_ = enum_class._iter_member_by_def_
        else:
            for name, value in attrs.items():
                if isinstance(value, auto):
                    if value.value is _auto_null:
                        value.value = gnv(name, 1, len(member_names), gnv_last_values)
                    value = value.value
                if value in value2member_map:
                    redirect = property()
                    redirect.__set_name__(enum_class, name)
                    setattr(enum_class, name, redirect)
                    member_map[name] = value2member_map[value]
                    continue
                if use_args:
                    if not isinstance(value, tuple):
                        value = (value,)
                    member = new_member(enum_class, *value)
                    value = value[0]
                else:
                    member = new_member(enum_class)
                if __new__ is None:
                    member._value_ = value
                member._name_ = name
                member.__objclass__ = enum_class
                member.__init__(value)
                member._sort_order_ = len(member_names)
                redirect = property()
                redirect.__set_name__(enum_class, name)
                setattr(enum_class, name, redirect)
                member_map[name] = member
                value2member_map[value] = member
                member_names.append(name)
                gnv_last_values.append(value)
        if '__new__' in body:
            enum_class.__new_member__ = enum_class.__new__
        enum_class.__new__ = Enum.__new__
        return enum_class
    return convert_class
@_simple_enum(StrEnum)
class EnumCheck:
    __doc__ = """
    various conditions to check an enumeration for
    """
    CONTINUOUS = 'no skipped integer values'
    NAMED_FLAGS = 'multi-flag aliases may not contain unnamed flags'
    UNIQUE = 'one name per value'
CONTINUOUS, NAMED_FLAGS, UNIQUE = EnumCheck
class verify:
    __doc__ = """
    Check an enumeration for various constraints. (see EnumCheck)
    """
    def __init__(self, *checks):
        self.checks = checks
    def __call__(self, enumeration):
        checks = self.checks
        cls_name = enumeration.__name__
        if Flag is not None and issubclass(enumeration, Flag):
            enum_type = 'flag'
        elif issubclass(enumeration, Enum):
            enum_type = 'enum'
        else:
            raise TypeError("the 'verify' decorator only works with Enum and Flag")
        for check in checks:
            if check is UNIQUE:
                duplicates = []
                for name, member in enumeration.__members__.items():
                    if name != member.name:
                        duplicates.append((name, member.name))
                if duplicates:
                    alias_details = ', '.join([f'{alias!s} -> {name!s}' for alias, name in duplicates])
                    raise ValueError(f'aliases found in {enumeration!r}: {alias_details!s}')
                continue
            elif check is CONTINUOUS:
                values = set((e.value for e in enumeration))
                if len(values) < 2:
                    continue
                low, high = (min(values), max(values))
                missing = []
                if enum_type == 'flag':
                    for i in range(_high_bit(low) + 1, _high_bit(high)):
                        if 2 ** i not in values:
                            missing.append(2 ** i)
                elif enum_type == 'enum':
                    for i in range(low + 1, high):
                        if i not in values:
                            missing.append(i)
                else:
                    raise Exception('verify: unknown type %r' % enum_type)
                if missing:
                    raise ValueError(f"invalid {enum_type!s} {cls_name!r}: missing values {', '.join((str(m) for m in missing))!s}"[:256])
                continue
            elif check is NAMED_FLAGS:
                member_names = enumeration._member_names_
                member_values = [m.value for m in enumeration]
                missing_names = []
                missing_value = 0
                for name, alias in enumeration._member_map_.items():
                    if name in member_names:
                        continue
                    if alias.value < 0:
                        continue
                    values = list(_iter_bits_lsb(alias.value))
                    missed = [v for v in values if v not in member_values]
                    if missed:
                        missing_names.append(name)
                        missing_value |= reduce(_or_, missed)
                if missing_names:
                    if len(missing_names) == 1:
                        alias = 'alias %s is missing' % missing_names[0]
                    else:
                        alias = f"aliases {', '.join(missing_names[:-1])!s} and {missing_names[-1]!s} are missing"
                    if _is_single_bit(missing_value):
                        value = 'value 0x%x' % missing_value
                    else:
                        value = 'combined values of 0x%x' % missing_value
                    raise ValueError(f'invalid Flag {cls_name!r}: {alias!s} {value!s} [use enum.show_flag_values(value) for details]')
        return enumeration
def _test_simple_enum(checked_enum, simple_enum):
    """
    A function that can be used to test an enum created with :func:`_simple_enum`
    against the version created by subclassing :class:`Enum`::

        >>> from enum import Enum, _simple_enum, _test_simple_enum
        >>> @_simple_enum(Enum)
        ... class Color:
        ...     RED = auto()
        ...     GREEN = auto()
        ...     BLUE = auto()
        >>> class CheckedColor(Enum):
        ...     RED = auto()
        ...     GREEN = auto()
        ...     BLUE = auto()
        >>> _test_simple_enum(CheckedColor, Color)

    If differences are found, a :exc:`TypeError` is raised.
    """
    failed = []
    if checked_enum.__dict__ != simple_enum.__dict__:
        checked_dict = checked_enum.__dict__
        checked_keys = list(checked_dict.keys())
        simple_dict = simple_enum.__dict__
        simple_keys = list(simple_dict.keys())
        member_names = set(list(checked_enum._member_map_.keys()) + list(simple_enum._member_map_.keys()))
        for key in set(checked_keys + simple_keys):
            if key in ('__module__', '_member_map_', '_value2member_map_', '__doc__'):
                continue
            if key in member_names:
                continue
            if key not in simple_keys:
                failed.append(f'missing key: {key!r}')
                continue
            if key not in checked_keys:
                failed.append(f'extra key:   {key!r}')
                continue
            checked_value = checked_dict[key]
            simple_value = simple_dict[key]
            if callable(checked_value) or isinstance(checked_value, bltns.property):
                continue
            if key == '__doc__':
                compressed_checked_value = checked_value.replace(' ', '').replace('\t', '')
                compressed_simple_value = simple_value.replace(' ', '').replace('\t', '')
                if compressed_checked_value != compressed_simple_value:
                    failed.append(f"{key!r}:\n         {f'checked -> {checked_value!r}'!s}\n         {f'simple  -> {simple_value!r}'!s}")
                continue
            if checked_value != simple_value:
                failed.append(f"{key!r}:\n         {f'checked -> {checked_value!r}'!s}\n         {f'simple  -> {simple_value!r}'!s}")
            continue
            continue
            continue
            continue
            continue
        failed.sort()
        for name in member_names:
            failed_member = []
            if name not in simple_keys:
                failed.append('missing member from simple enum: %r' % name)
            elif name not in checked_keys:
                failed.append('extra member in simple enum: %r' % name)
            else:
                checked_member_dict = checked_enum[name].__dict__
                checked_member_keys = list(checked_member_dict.keys())
                simple_member_dict = simple_enum[name].__dict__
                simple_member_keys = list(simple_member_dict.keys())
                for key in set(checked_member_keys + simple_member_keys):
                    if key in ('__module__', '__objclass__', '_inverted_'):
                        continue
                    if key not in simple_member_keys:
                        failed_member.append(f'missing key {key!r} not in the simple enum member {name!r}')
                        continue
                    if key not in checked_member_keys:
                        failed_member.append(f'extra key {key!r} in simple enum member {name!r}')
                        continue
                    checked_value = checked_member_dict[key]
                    simple_value = simple_member_dict[key]
                    if checked_value != simple_value:
                        failed_member.append(f"{key!r}:\n         {f'checked member -> {checked_value!r}'!s}\n         {f'simple member  -> {simple_value!r}'!s}")
                    continue
                    continue
            if failed_member:
                failed.append(f'{name!r} member mismatch:\n      {"""
      """.join(failed_member)!s}')
        for method in ('__str__', '__repr__', '__reduce_ex__', '__format__', '__getnewargs_ex__', '__getnewargs__', '__reduce_ex__', '__reduce__'):
            if method in simple_keys and method in checked_keys:
                continue
            if method not in simple_keys and method not in checked_keys:
                checked_method = getattr(checked_enum, method, None)
                simple_method = getattr(simple_enum, method, None)
                if hasattr(checked_method, '__func__'):
                    checked_method = checked_method.__func__
                    simple_method = simple_method.__func__
                if checked_method != simple_method:
                    failed.append(f"{method!r}:  {f'checked -> {checked_method!r}'!s:30} {f'simple -> {simple_method!r}'!s}")
                continue
            continue
    if failed:
        raise TypeError("""enum mismatch:
   %s""" % """
   """.join(failed))
def _old_convert_(etype, name, module, filter, source=None, *, boundary=None):
    """
    Create a new Enum subclass that replaces a collection of global constants
    """
    module_globals = sys.modules[module].__dict__
    if source:
        source = source.__dict__
    else:
        source = module_globals
    members = [(name, value) for name, value in source.items() if filter(name)]
    try:
        members.sort(key=lambda t: (t[1], t[0]))
    except TypeError:
        members.sort(key=lambda t: t[0])
    cls = etype(name, members, module=module, boundary=boundary or KEEP)
    return cls
_stdlib_enums = (IntEnum, StrEnum, IntFlag)
