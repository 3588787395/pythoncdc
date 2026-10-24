# Source Generated with Decompyle++ (Python version)
# File: specifiers.cpython-311.pyc (Python 3.11)

__doc__ = """
.. testsetup::

    from packaging.specifiers import Specifier, SpecifierSet, InvalidSpecifier
    from packaging.version import Version
"""
from __future__ import annotations
import abc
import enum
import functools
import itertools
import re
import sys
import typing
from typing import TYPE_CHECKING, Any, Callable, Final, Iterable, Iterator, Sequence, TypeVar, Union
from .utils import canonicalize_version
from .version import InvalidVersion, Version
if sys.version_info >= (3, 10):
    from typing import TypeGuard
elif TYPE_CHECKING:
    from typing_extensions import TypeGuard
__all__ = ['BaseSpecifier', 'InvalidSpecifier', 'Specifier', 'SpecifierSet']
def __dir__():
    return __all__
def _validate_spec(spec, /):
    return isinstance(spec, tuple) and len(spec) == 2 and isinstance(spec[0], str) and isinstance(spec[1], str)
def _validate_pre(pre, /):
    return pre is None or isinstance(pre, bool)
T = TypeVar('T')
UnparsedVersion = Union[Version, str]
UnparsedVersionVar = TypeVar('UnparsedVersionVar', bound=UnparsedVersion)
CallableOperator = Callable[[Version, str], bool]
_MIN_VERSION = Version('0.dev0')
__annotations__['_MIN_VERSION'] = 'Final[Version]'
def _trim_release(release):
    """Strip trailing zeros from a release tuple for normalized comparison."""
    end = len(release)
    while end > 1 and release[end - 1] == 0:
        end -= 1
    return release if end == len(release) else release[:end]
class _BoundaryKind(enum.Enum):
    __doc__ = 'Where a boundary marker sits in the version ordering.'
    AFTER_LOCALS = enum.auto()
    AFTER_POSTS = enum.auto()
@functools.total_ordering
class _BoundaryVersion:
    __doc__ = """A point on the version line between two real PEP 440 versions.

    Some specifier semantics imply boundaries between real versions:
    ``<=1.0`` includes ``1.0+local`` and ``>1.0`` excludes
    ``1.0.post0``.  No real :class:`Version` falls on those boundaries,
    so this class creates values that sort between the real versions
    on either side.

    Two kinds exist, shown relative to a base version V::

        V < V+local < AFTER_LOCALS(V) < V.post0 < AFTER_POSTS(V)

    ``AFTER_LOCALS`` sits after V and every V+local, but before
    V.post0.  Upper bound of ``<=V``, ``==V``, ``!=V``.

    ``AFTER_POSTS`` sits after every V.postN, but before the next
    release segment.  Lower bound of ``>V`` (final or pre-release V)
    to exclude post-releases per PEP 440.
    """
    __slots__ = ('_kind', '_trimmed_release', 'version')
    def __init__(self, version, kind):
        self.version = version
        self._kind = kind
        self._trimmed_release = _trim_release(version.release)
    def _is_family(self, other):
        """Is ``other`` a version that this boundary sorts above?"""
        v = self.version
        if other.epoch == v.epoch and _trim_release(other.release) == self._trimmed_release:
            return other.post == v.post and other.dev == v.dev
        return other.dev == v.dev or other.post is not None
    def __eq__(self, other):
        if isinstance(other, _BoundaryVersion):
            return self.version == other.version and self._kind == other._kind
        else:
            return NotImplemented
    def __lt__(self, other):
        if isinstance(other, _BoundaryVersion):
            if self.version != other.version:
                return self.version < other.version
            else:
                return self._kind.value < other._kind.value
        return not self._is_family(other) and self.version < other
    def __hash__(self):
        return hash((self.version, self._kind))
    def __repr__(self):
        return f'{self.__class__.__name__}({self.version!r}, {self._kind.name})'
@functools.total_ordering
class _LowerBound:
    __doc__ = """Lower bound of a version range.

    A version *v* of ``None`` means unbounded below (-inf).
    At equal versions, ``[v`` sorts before ``(v`` because an inclusive
    bound starts earlier.
    """
    __slots__ = ('inclusive', 'version')
    def __init__(self, version, inclusive):
        self.version = version
        self.inclusive = inclusive
    def __eq__(self, other):
        if not isinstance(other, _LowerBound):
            return NotImplemented
        return self.version == other.version and self.inclusive == other.inclusive
    def __lt__(self, other):
        if not isinstance(other, _LowerBound):
            return NotImplemented
        elif self.version is None:
            return other.version is not None
        elif other.version is None:
            return False
        elif self.version != other.version:
            return self.version < other.version
        else:
            return self.inclusive and not other.inclusive
    def __hash__(self):
        return hash((self.version, self.inclusive))
    def __repr__(self):
        bracket = '[' if self.inclusive else '('
        return f'<{self.__class__.__name__} {bracket}{self.version!r}>'
@functools.total_ordering
class _UpperBound:
    __doc__ = """Upper bound of a version range.

    A version *v* of ``None`` means unbounded above (+inf).
    At equal versions, ``v)`` sorts before ``v]`` because an exclusive
    bound ends earlier.
    """
    __slots__ = ('inclusive', 'version')
    def __init__(self, version, inclusive):
        self.version = version
        self.inclusive = inclusive
    def __eq__(self, other):
        if not isinstance(other, _UpperBound):
            return NotImplemented
        return self.version == other.version and self.inclusive == other.inclusive
    def __lt__(self, other):
        if not isinstance(other, _UpperBound):
            return NotImplemented
        elif self.version is None:
            return False
        elif other.version is None:
            return True
        elif self.version != other.version:
            return self.version < other.version
        else:
            return not self.inclusive and other.inclusive
    def __hash__(self):
        return hash((self.version, self.inclusive))
    def __repr__(self):
        bracket = ']' if self.inclusive else ')'
        return f'<{self.__class__.__name__} {self.version!r}{bracket}>'
if typing.TYPE_CHECKING:
    _VersionOrBoundary = Union[Version, _BoundaryVersion, None]
    _VersionRange = tuple[_LowerBound, _UpperBound]
_NEG_INF = _LowerBound(None, False)
_POS_INF = _UpperBound(None, False)
_FULL_RANGE: 'tuple[_VersionRange]' = ((_NEG_INF, _POS_INF),)
def _range_is_empty(lower, upper):
    """True when the range defined by *lower* and *upper* contains no versions."""
    if lower.version is None or upper.version is None:
        return False
    elif lower.version == upper.version:
        return not (lower.inclusive and upper.inclusive)
    else:
        return lower.version > upper.version
def _intersect_ranges(left, right):
    """Intersect two sorted, non-overlapping range lists (two-pointer merge)."""
    result = []
    right_index = (left_index := 0)
    while left_index < len(left) and right_index < len(right):
        left_lower, left_upper = left[left_index]
        right_lower, right_upper = right[right_index]
        lower = max(left_lower, right_lower)
        upper = min(left_upper, right_upper)
        if not _range_is_empty(lower, upper):
            result.append((lower, upper))
        if left_upper < right_upper:
            left_index += 1
        else:
            right_index += 1
    return result
def _next_prefix_dev0(version):
    """Smallest version in the next prefix: 1.2 -> 1.3.dev0."""
    release = (*version.release[:-1], version.release[-1] + 1)
    return Version.from_parts(epoch=version.epoch, release=release, dev=0)
def _base_dev0(version):
    """The .dev0 of a version's base release: 1.2 -> 1.2.dev0."""
    return Version.from_parts(epoch=version.epoch, release=version.release, dev=0)
def _coerce_version(version):
    if not isinstance(version, Version):
        try:
            version = Version(version)
        except InvalidVersion:
            return None
    return version
def _public_version(version):
    if version.local is None:
        return version
    else:
        return version.__replace__(local=None)
def _post_base(version):
    """The version that *version* is a post-release of.

    1.0.post1 -> 1.0, 1.0a1.post0 -> 1.0a1, 1.0.post0.dev1 -> 1.0.
    """
    return version.__replace__(post=None, dev=None, local=None)
def _earliest_prerelease(version):
    """Earliest pre-release of *version*.

    1.2 -> 1.2.dev0, 1.2.post1 -> 1.2.post1.dev0.
    """
    return version.__replace__(dev=0, local=None)
def _nearest_non_prerelease(v):
    """Smallest non-pre-release version at or above *v*, or None."""
    if v is None:
        return None
    elif isinstance(v, _BoundaryVersion):
        inner = v.version
        if inner.is_prerelease:
            return inner.__replace__(pre=None, dev=None, local=None)
        else:
            k = inner.post + 1 if inner.post is not None else 0
            return inner.__replace__(post=k, local=None)
    elif not v.is_prerelease:
        return v
    else:
        return v.__replace__(pre=None, dev=None, local=None)
class InvalidSpecifier(ValueError):
    __doc__ = """
    Raised when attempting to create a :class:`Specifier` with a specifier
    string that is invalid.

    >>> Specifier("lolwat")
    Traceback (most recent call last):
        ...
    packaging.specifiers.InvalidSpecifier: Invalid specifier: 'lolwat'
    """
class BaseSpecifier(metaclass=abc.ABCMeta):
    __slots__ = ()
    __match_args__ = ('_str',)
    @property
    def _str(self):
        """Internal property for match_args"""
        return str(self)
    @abc.abstractmethod
    def __str__(self):
        """
        Returns the str representation of this Specifier-like object. This
        should be representative of the Specifier itself.
        """
    @abc.abstractmethod
    def __hash__(self):
        """
        Returns a hash value for this Specifier-like object.
        """
    @abc.abstractmethod
    def __eq__(self, other):
        """
        Returns a boolean representing whether or not the two Specifier-like
        objects are equal.

        :param other: The other object to check against.
        """
    @property
    @abc.abstractmethod
    def prereleases(self):
        """Whether or not pre-releases as a whole are allowed.

        This can be set to either ``True`` or ``False`` to explicitly enable or disable
        prereleases or it can be set to ``None`` (the default) to use default semantics.
        """
    @prereleases.setter
    def prereleases(self, value):
        """Setter for :attr:`prereleases`.

        :param value: The value to set.
        """
    @abc.abstractmethod
    def contains(self, item, prereleases=None):
        """
        Determines if the given item is contained within this specifier.
        """
    @typing.overload
    def filter(self, iterable, prereleases=None, key=None):
        return None
    @typing.overload
    def filter(self, iterable, prereleases=None, key=None):
        return None
    @abc.abstractmethod
    def filter(self, iterable, prereleases=None, key=None):
        """
        Takes an iterable of items and filters them so that only items which
        are contained within this specifier are allowed in it.
        """
class Specifier(BaseSpecifier):
    __doc__ = """This class abstracts handling of version specifiers.

    .. tip::

        It is generally not required to instantiate this manually. You should instead
        prefer to work with :class:`SpecifierSet` instead, which can parse
        comma-separated version specifiers (which is what package metadata contains).

    Instances are safe to serialize with :mod:`pickle`. They use a stable
    format so the same pickle can be loaded in future packaging releases.

    .. versionchanged:: 26.2

        Added a stable pickle format. Pickles created with packaging 26.2+ can
        be unpickled with future releases.  Backward compatibility with pickles
        from packaging < 26.2 is supported but may be removed in a future
        release.
    """
    __slots__ = ('_prereleases', '_ranges', '_spec', '_spec_version', '_wildcard_split')
    _specifier_regex_str = """
        (?:
            (?:
                # The identity operators allow for an escape hatch that will
                # do an exact string match of the version you wish to install.
                # This will not be parsed by PEP 440 and we cannot determine
                # any semantic meaning from it. This operator is discouraged
                # but included entirely as an escape hatch.
                ===  # Only match for the identity operator
                \\s*
                [^\\s;)]*  # The arbitrary version can be just about anything,
                          # we match everything except for whitespace, a
                          # semi-colon for marker support, and a closing paren
                          # since versions can be enclosed in them.
            )
            |
            (?:
                # The (non)equality operators allow for wild card and local
                # versions to be specified so we have to define these two
                # operators separately to enable that.
                (?:==|!=)            # Only match for equals and not equals

                \\s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\\.[0-9]+)*   # release

                # You cannot use a wild card and a pre-release, post-release, a dev or
                # local version together so group them with a | and make them optional.
                (?:
                    \\.\\*  # Wild card syntax of .*
                    |
                    (?a:                                  # pre release
                        [-_\\.]?
                        (alpha|beta|preview|pre|a|b|c|rc)
                        [-_\\.]?
                        [0-9]*
                    )?
                    (?a:                                  # post release
                        (?:-[0-9]+)|(?:[-_\\.]?(post|rev|r)[-_\\.]?[0-9]*)
                    )?
                    (?a:[-_\\.]?dev[-_\\.]?[0-9]*)?         # dev release
                    (?a:\\+[a-z0-9]+(?:[-_\\.][a-z0-9]+)*)? # local
                )?
            )
            |
            (?:
                # The compatible operator requires at least two digits in the
                # release segment.
                (?:~=)               # Only match for the compatible operator

                \\s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\\.[0-9]+)+   # release  (We have a + instead of a *)
                (?:                   # pre release
                    [-_\\.]?
                    (alpha|beta|preview|pre|a|b|c|rc)
                    [-_\\.]?
                    [0-9]*
                )?
                (?:                                   # post release
                    (?:-[0-9]+)|(?:[-_\\.]?(post|rev|r)[-_\\.]?[0-9]*)
                )?
                (?:[-_\\.]?dev[-_\\.]?[0-9]*)?          # dev release
            )
            |
            (?:
                # All other operators only allow a sub set of what the
                # (non)equality operators do. Specifically they do not allow
                # local versions to be specified nor do they allow the prefix
                # matching wild cards.
                (?:<=|>=|<|>)

                \\s*
                v?
                (?:[0-9]+!)?          # epoch
                [0-9]+(?:\\.[0-9]+)*   # release
                (?a:                   # pre release
                    [-_\\.]?
                    (alpha|beta|preview|pre|a|b|c|rc)
                    [-_\\.]?
                    [0-9]*
                )?
                (?a:                                   # post release
                    (?:-[0-9]+)|(?:[-_\\.]?(post|rev|r)[-_\\.]?[0-9]*)
                )?
                (?a:[-_\\.]?dev[-_\\.]?[0-9]*)?          # dev release
            )
        )
        """
    _regex = re.compile('\\s*' + _specifier_regex_str + '\\s*', re.VERBOSE | re.IGNORECASE)
    _operators: 'Final' = {'~=': 'compatible', '==': 'equal', '!=': 'not_equal', '<=': 'less_than_equal', '>=': 'greater_than_equal', '<': 'less_than', '>': 'greater_than', '===': 'arbitrary'}
    def __init__(self, spec='', prereleases=None):
        """Initialize a Specifier instance.

        :param spec:
            The string representation of a specifier which will be parsed and
            normalized before use.
        :param prereleases:
            This tells the specifier if it should accept prerelease versions if
            applicable or not. The default of ``None`` will autodetect it from the
            given specifiers.
        :raises InvalidSpecifier:
            If the given specifier is invalid (i.e. bad syntax).
        """
        if not self._regex.fullmatch(spec):
            raise InvalidSpecifier(f'Invalid specifier: {spec!r}')
        spec = spec.strip()
        if spec.startswith('==='):
            operator, version = (spec[:3], spec[3:].strip())
        elif spec.startswith(('~=', '==', '!=', '<=', '>=')):
            operator, version = (spec[:2], spec[2:].strip())
        else:
            operator, version = (spec[:1], spec[1:].strip())
        self._spec = (operator, version)
        self._prereleases = prereleases
        self._spec_version = None
        self._wildcard_split = None
        self._ranges = None
    def _get_spec_version(self, version):
        """One element cache, as only one spec Version is needed per Specifier."""
        if self._spec_version is not None and self._spec_version[0] == version:
            return self._spec_version[1]
        version_specifier = _coerce_version(version)
        if version_specifier is None:
            return None
        else:
            self._spec_version = (version, version_specifier)
            return version_specifier
    def _require_spec_version(self, version):
        """Get spec version, asserting it's valid (not for === operator).

        This method should only be called for operators where version
        strings are guaranteed to be valid PEP 440 versions (not ===).
        """
        spec_version = self._get_spec_version(version)
        assert spec_version is not None
        return spec_version
    def _to_ranges(self):
        """Convert this specifier to sorted, non-overlapping version ranges.

        Each standard operator maps to one or two ranges.  ``===`` is
        modeled as full range (actual check done separately).  Cached.
        """
        if self._ranges is not None:
            return self._ranges
        else:
            op = self.operator
            ver_str = self.version
            if op == '===':
                self._ranges = _FULL_RANGE
                return _FULL_RANGE
            elif ver_str.endswith('.*'):
                result = self._wildcard_ranges(op, ver_str)
            else:
                result = self._standard_ranges(op, ver_str)
            self._ranges = result
            return result
    def _wildcard_ranges(self, op, ver_str):
        base = self._require_spec_version(ver_str[:-2])
        lower = _base_dev0(base)
        upper = _next_prefix_dev0(base)
        if op == '==':
            return [(_LowerBound(lower, True), _UpperBound(upper, False))]
        else:
            return [(_NEG_INF, _UpperBound(lower, False)), (_LowerBound(upper, True), _POS_INF)]
    def _standard_ranges(self, op, ver_str):
        v = self._require_spec_version(ver_str)
        if op == '>=':
            return [(_LowerBound(v, True), _POS_INF)]
        elif op == '<=':
            return [(_NEG_INF, _UpperBound(_BoundaryVersion(v, _BoundaryKind.AFTER_LOCALS), True))]
        elif op == '>':
            if v.dev is not None:
                lower_ver = v.__replace__(dev=v.dev + 1, local=None)
                return [(_LowerBound(lower_ver, True), _POS_INF)]
            elif v.post is not None:
                lower_ver = v.__replace__(post=v.post + 1, dev=0, local=None)
                return [(_LowerBound(lower_ver, True), _POS_INF)]
            else:
                return [(_LowerBound(_BoundaryVersion(v, _BoundaryKind.AFTER_POSTS), False), _POS_INF)]
        elif op == '<':
            bound = v if v.is_prerelease else v.__replace__(dev=0, local=None)
            if bound <= _MIN_VERSION:
                return []
            else:
                return [(_NEG_INF, _UpperBound(bound, False))]
        else:
            has_local = '+' in ver_str
            after_locals = _BoundaryVersion(v, _BoundaryKind.AFTER_LOCALS)
            upper = v if has_local else after_locals
            if op == '==':
                return [(_LowerBound(v, True), _UpperBound(upper, True))]
            elif op == '!=':
                return [(_NEG_INF, _UpperBound(v, False)), (_LowerBound(upper, False), _POS_INF)]
            elif op == '~=':
                prefix = v.__replace__(release=v.release[:-1])
                return [(_LowerBound(v, True), _UpperBound(_next_prefix_dev0(prefix), False))]
            else:
                raise ValueError(f'Unknown operator: {op!r}')
    @property
    def prereleases(self):
        if self._prereleases is not None:
            return self._prereleases
        else:
            operator, version_str = self._spec
            if operator == '!=':
                return False
            elif operator == '==' and version_str.endswith('.*'):
                return False
            else:
                version = self._get_spec_version(version_str)
                if version is None:
                    return None
                else:
                    return version.is_prerelease
    @prereleases.setter
    def prereleases(self, value):
        self._prereleases = value
    def __getstate__(self):
        return (self._spec, self._prereleases)
    def __setstate__(self, state):
        self._spec_version = None
        self._wildcard_split = None
        self._ranges = None
        if isinstance(state, tuple):
            if len(state) == 2:
                spec, prereleases = state
                if _validate_spec(spec) and _validate_pre(prereleases):
                    self._spec = spec
                    self._prereleases = prereleases
                    return None
                elif len(state) == 2 and isinstance(state[1], dict):
                    _, slot_dict = state
                    spec = slot_dict.get('_spec')
                    prereleases = slot_dict.get('_prereleases', 'invalid')
                    if _validate_spec(spec) and _validate_pre(prereleases):
                        self._spec = spec
                        self._prereleases = prereleases
                        return None
        if isinstance(state, dict):
            spec = state.get('_spec')
            prereleases = state.get('_prereleases', 'invalid')
            if _validate_spec(spec) and _validate_pre(prereleases):
                self._spec = spec
                self._prereleases = prereleases
                return None
        raise TypeError(f'Cannot restore Specifier from {state!r}')
    @property
    def operator(self):
        """The operator of this specifier.

        >>> Specifier("==1.2.3").operator
        '=='
        """
        return self._spec[0]
    @property
    def version(self):
        """The version of this specifier.

        >>> Specifier("==1.2.3").version
        '1.2.3'
        """
        return self._spec[1]
    def __repr__(self):
        """A representation of the Specifier that shows all internal state.

        >>> Specifier('>=1.0.0')
        <Specifier('>=1.0.0')>
        >>> Specifier('>=1.0.0', prereleases=False)
        <Specifier('>=1.0.0', prereleases=False)>
        >>> Specifier('>=1.0.0', prereleases=True)
        <Specifier('>=1.0.0', prereleases=True)>
        """
        pre = f', prereleases={self.prereleases!r}' if self._prereleases is not None else ''
        return f'<{self.__class__.__name__}({str(self)!r}{pre})>'
    def __str__(self):
        """A string representation of the Specifier that can be round-tripped.

        >>> str(Specifier('>=1.0.0'))
        '>=1.0.0'
        >>> str(Specifier('>=1.0.0', prereleases=False))
        '>=1.0.0'
        """
        return '{}{}'.format(*self._spec)
    @property
    def _canonical_spec(self):
        operator, version = self._spec
        if operator == '===' or version.endswith('.*'):
            return (operator, version)
        else:
            spec_version = self._require_spec_version(version)
            canonical_version = canonicalize_version(spec_version, strip_trailing_zero=operator != '~=')
            return (operator, canonical_version)
    def __hash__(self):
        return hash(self._canonical_spec)
    def __eq__(self, other):
        """Whether or not the two Specifier-like objects are equal.

        :param other: The other object to check against.

        The value of :attr:`prereleases` is ignored.

        >>> Specifier("==1.2.3") == Specifier("== 1.2.3.0")
        True
        >>> (Specifier("==1.2.3", prereleases=False) ==
        ...  Specifier("==1.2.3", prereleases=True))
        True
        >>> Specifier("==1.2.3") == "==1.2.3"
        True
        >>> Specifier("==1.2.3") == Specifier("==1.2.4")
        False
        >>> Specifier("==1.2.3") == Specifier("~=1.2.3")
        False
        """
        if isinstance(other, str):
            try:
                other = self.__class__(str(other))
            except InvalidSpecifier:
                return NotImplemented
        elif not isinstance(other, self.__class__):
            return NotImplemented
        return self._canonical_spec == other._canonical_spec
    def _get_operator(self, op):
        operator_callable = getattr(self, f'_compare_{self._operators[op]}')
        return operator_callable
    def _compare_compatible(self, prospective, spec):
        prefix = _version_join(list(itertools.takewhile(_is_not_suffix, _version_split(spec)))[:-1])
        prefix += '.*'
        return self._compare_greater_than_equal(prospective, spec) and self._compare_equal(prospective, prefix)
    def _get_wildcard_split(self, spec):
        """Cached split of a wildcard spec into components and numeric length.

        >>> Specifier("==1.*")._get_wildcard_split("1.*")
        (['0', '1'], 2)
        >>> Specifier("==3.10.*")._get_wildcard_split("3.10.*")
        (['0', '3', '10'], 3)
        """
        wildcard_split = self._wildcard_split
        if wildcard_split is None:
            normalized = canonicalize_version(spec[:-2], strip_trailing_zero=False)
            split_spec = _version_split(normalized)
            wildcard_split = (split_spec, _numeric_prefix_len(split_spec))
            self._wildcard_split = wildcard_split
        return wildcard_split
    def _compare_equal(self, prospective, spec):
        if spec.endswith('.*'):
            split_spec, spec_numeric_len = self._get_wildcard_split(spec)
            normalized_prospective = canonicalize_version(_public_version(prospective), strip_trailing_zero=False)
            split_prospective = _version_split(normalized_prospective)
            padded_prospective = _left_pad(split_prospective, spec_numeric_len)
            shortened_prospective = padded_prospective[:len(split_spec)]
            return shortened_prospective == split_spec
        else:
            spec_version = self._require_spec_version(spec)
            if not spec_version.local:
                prospective = _public_version(prospective)
            return prospective == spec_version
    def _compare_not_equal(self, prospective, spec):
        return not self._compare_equal(prospective, spec)
    def _compare_less_than_equal(self, prospective, spec):
        return _public_version(prospective) <= self._require_spec_version(spec)
    def _compare_greater_than_equal(self, prospective, spec):
        return _public_version(prospective) >= self._require_spec_version(spec)
    def _compare_less_than(self, prospective, spec_str):
        spec = self._require_spec_version(spec_str)
        if not prospective < spec:
            return False
        elif not spec.is_prerelease and prospective.is_prerelease and prospective >= _earliest_prerelease(spec):
            return False
        else:
            return True
    def _compare_greater_than(self, prospective, spec_str):
        spec = self._require_spec_version(spec_str)
        if not prospective > spec:
            return False
        elif not spec.is_postrelease and prospective.is_postrelease and _post_base(prospective) == spec:
            return False
        elif prospective.local is not None and _public_version(prospective) == spec:
            return False
        else:
            return True
    def _compare_arbitrary(self, prospective, spec):
        return str(prospective).lower() == str(spec).lower()
    def __contains__(self, item):
        """Return whether or not the item is contained in this specifier.

        :param item: The item to check for.

        This is used for the ``in`` operator and behaves the same as
        :meth:`contains` with no ``prereleases`` argument passed.

        >>> "1.2.3" in Specifier(">=1.2.3")
        True
        >>> Version("1.2.3") in Specifier(">=1.2.3")
        True
        >>> "1.0.0" in Specifier(">=1.2.3")
        False
        >>> "1.3.0a1" in Specifier(">=1.2.3")
        True
        >>> "1.3.0a1" in Specifier(">=1.2.3", prereleases=True)
        True
        """
        return self.contains(item)
    def contains(self, item, prereleases=None):
        """Return whether or not the item is contained in this specifier.

        :param item:
            The item to check for, which can be a version string or a
            :class:`Version` instance.
        :param prereleases:
            Whether or not to match prereleases with this Specifier. If set to
            ``None`` (the default), it will follow the recommendation from
            :pep:`440` and match prereleases, as there are no other versions.

        >>> Specifier(">=1.2.3").contains("1.2.3")
        True
        >>> Specifier(">=1.2.3").contains(Version("1.2.3"))
        True
        >>> Specifier(">=1.2.3").contains("1.0.0")
        False
        >>> Specifier(">=1.2.3").contains("1.3.0a1")
        True
        >>> Specifier(">=1.2.3", prereleases=False).contains("1.3.0a1")
        False
        >>> Specifier(">=1.2.3").contains("1.3.0a1")
        True
        """
        return bool(list(self.filter([item], prereleases=prereleases)))
    @typing.overload
    def filter(self, iterable, prereleases=None, key=None):
        return None
    @typing.overload
    def filter(self, iterable, prereleases=None, key=None):
        return None
    pass
    pass
    def filter(self, iterable, prereleases=None, key=None):
        """Filter items in the given iterable, that match the specifier.

        :param iterable:
            An iterable that can contain version strings and :class:`Version` instances.
            The items in the iterable will be filtered according to the specifier.
        :param prereleases:
            Whether or not to allow prereleases in the returned iterator. If set to
            ``None`` (the default), it will follow the recommendation from :pep:`440`
            and match prereleases if there are no other versions.
        :param key:
            A callable that takes a single argument (an item from the iterable) and
            returns a version string or :class:`Version` instance to be used for
            filtering.

        >>> list(Specifier(">=1.2.3").filter(["1.2", "1.3", "1.5a1"]))
        ['1.3']
        >>> list(Specifier(">=1.2.3").filter(["1.2", "1.2.3", "1.3", Version("1.4")]))
        ['1.2.3', '1.3', <Version('1.4')>]
        >>> list(Specifier(">=1.2.3").filter(["1.2", "1.5a1"]))
        ['1.5a1']
        >>> list(Specifier(">=1.2.3").filter(["1.3", "1.5a1"], prereleases=True))
        ['1.3', '1.5a1']
        >>> list(Specifier(">=1.2.3", prereleases=True).filter(["1.3", "1.5a1"]))
        ['1.3', '1.5a1']
        >>> list(Specifier(">=1.2.3").filter(
        ... [{"ver": "1.2"}, {"ver": "1.3"}],
        ... key=lambda x: x["ver"]))
        [{'ver': '1.3'}]
        """
        prereleases_versions = []
        found_non_prereleases = False
        include_prereleases = prereleases if prereleases is not None else self.prereleases
        operator_callable = self._get_operator(self.operator)
        for version in iterable:
            parsed_version = _coerce_version(version if key is None else key(version))
            match = False
            if parsed_version is None:
                if self.operator == '===' and self._compare_arbitrary(version, self.version):
                    yield version
            elif self.operator == '===':
                match = self._compare_arbitrary(version if key is None else key(version), self.version)
            else:
                match = operator_callable(parsed_version, self.version)
            if match and parsed_version is not None:
                if parsed_version.is_prerelease or include_prereleases:
                    found_non_prereleases = True
                    yield version
                    continue
                elif prereleases is None and self._prereleases is not False:
                    prereleases_versions.append(version)
            else:
                continue
        if not found_non_prereleases:
            if prereleases is None:
                if self._prereleases is not False:
                    yield from prereleases_versions
                    return None
_prefix_regex = re.compile('([0-9]+)((?:a|b|c|rc)[0-9]+)')
def _pep440_filter_prereleases(iterable, key):
    """Filter per PEP 440: exclude prereleases unless no finals exist."""
    all_nonfinal = []
    arbitrary_strings = []
    found_final = False
    for item in iterable:
        parsed = _coerce_version(item if key is None else key(item))
        if parsed is None:
            if found_final:
                yield item
            else:
                arbitrary_strings.append(item)
                all_nonfinal.append(item)
            continue
        if not parsed.is_prerelease:
            if not found_final:
                yield from arbitrary_strings
                found_final = True
            yield item
            continue
        if not found_final:
            all_nonfinal.append(item)
        else:
            continue
        continue
        continue
    if not found_final:
        yield from all_nonfinal
        return None
    else:
        return None
def _version_split(version):
    """Split version into components.

    The split components are intended for version comparison. The logic does
    not attempt to retain the original version string, so joining the
    components back with :func:`_version_join` may not produce the original
    version string.
    """
    result = []
    epoch, _, rest = version.rpartition('!')
    for item in epoch or '0':
        match = _prefix_regex.fullmatch(item)
        if match:
            result.extend(match.groups())
            continue
        result.append(item)
        continue
    return result
def _version_join(components):
    """Join split version components into a version string.

    This function assumes the input came from :func:`_version_split`, where the
    first component must be the epoch (either empty or numeric), and all other
    components numeric.
    """
    epoch, *rest = components
    return f"{epoch}!{'.'.join(rest)}"
def _is_not_suffix(segment):
    return not any((segment.startswith(prefix) for prefix in ('dev', 'a', 'b', 'rc', 'post')))
def _numeric_prefix_len(split):
    """Count leading numeric components in a :func:`_version_split` result.

    >>> _numeric_prefix_len(["0", "1", "2", "a1"])
    3
    """
    count = 0
    for segment in split:
        if not segment.isdigit():
            break
        count += 1
    return count
def _left_pad(split, target_numeric_len):
    """Pad a :func:`_version_split` result with ``"0"`` segments to reach
    ``target_numeric_len`` numeric components.  Suffix segments are preserved.

    >>> _left_pad(["0", "1", "a1"], 4)
    ['0', '1', '0', '0', 'a1']
    """
    numeric_len = _numeric_prefix_len(split)
    pad_needed = target_numeric_len - numeric_len
    if pad_needed <= 0:
        return split
    else:
        return [*split[:numeric_len], *['0'] * pad_needed, *split[numeric_len:]]
def _operator_cost(op_entry):
    """Sort key for Cost Based Ordering of specifier operators in _filter_versions.

    Operators run sequentially on a shrinking candidate set, so operators that
    reject the most versions should run first to minimize work for later ones.

    Tier 0: Exact equality (==, ===), likely to narrow candidates to one version
    Tier 1: Range checks (>=, <=, >, <), cheap and usually reject a large portion
    Tier 2: Wildcard equality (==.*) and compatible release (~=), more expensive
    Tier 3: Exact !=, cheap but rarely rejects
    Tier 4: Wildcard !=.*, expensive and rarely rejects
    """
    _, ver, op = op_entry
    if op == '==':
        return 0 if not ver.endswith('.*') else 2
    elif op in ('>=', '<=', '>', '<'):
        return 1
    elif op == '~=':
        return 2
    elif op == '!=':
        return 3 if not ver.endswith('.*') else 4
    elif op == '===':
        return 0
    else:
        raise ValueError(f'Unknown operator: {op!r}')
class SpecifierSet(BaseSpecifier):
    __doc__ = """This class abstracts handling of a set of version specifiers.

    It can be passed a single specifier (``>=3.0``), a comma-separated list of
    specifiers (``>=3.0,!=3.1``), or no specifier at all.

    Instances are safe to serialize with :mod:`pickle`. They use a stable
    format so the same pickle can be loaded in future packaging
    releases.

    .. versionchanged:: 26.2

        Added a stable pickle format. Pickles created with
        packaging 26.2+ can be unpickled with future releases.
        Backward compatibility with pickles from
        packaging < 26.2 is supported but may be removed in a future
        release.
    """
    __slots__ = ('_canonicalized', '_has_arbitrary', '_is_unsatisfiable', '_prereleases', '_resolved_ops', '_specs')
    pass
    pass
    def __init__(self, specifiers='', prereleases=None):
        """Initialize a SpecifierSet instance.

        :param specifiers:
            The string representation of a specifier or a comma-separated list of
            specifiers which will be parsed and normalized before use.
            May also be an iterable of ``Specifier`` instances, which will be used
            as is.
        :param prereleases:
            This tells the SpecifierSet if it should accept prerelease versions if
            applicable or not. The default of ``None`` will autodetect it from the
            given specifiers.

        :raises InvalidSpecifier:
            If the given ``specifiers`` are not parseable than this exception will be
            raised.
        """
        if isinstance(specifiers, str):
            split_specifiers = [s.strip() for s in specifiers.split(',') if s.strip()]
            self._specs = tuple(map(Specifier, split_specifiers))
            self._has_arbitrary = '===' in specifiers
        else:
            self._specs = tuple(specifiers)
            self._has_arbitrary = any(('===' in str(s) for s in self._specs))
        self._canonicalized = len(self._specs) <= 1
        self._resolved_ops = None
        self._prereleases = prereleases
        self._is_unsatisfiable = None
    def _canonical_specs(self):
        """Deduplicate, sort, and cache specs for order-sensitive operations."""
        if not self._canonicalized:
            self._specs = tuple(dict.fromkeys(sorted(self._specs, key=str)))
            self._canonicalized = True
            self._resolved_ops = None
            self._is_unsatisfiable = None
        return self._specs
    @property
    def prereleases(self):
        if self._prereleases is not None:
            return self._prereleases
        elif not self._specs:
            return None
        elif any((s.prereleases for s in self._specs)):
            return True
    @prereleases.setter
    def prereleases(self, value):
        self._prereleases = value
        self._is_unsatisfiable = None
    def __getstate__(self):
        return (self._specs, self._prereleases)
    def __setstate__(self, state):
        self._resolved_ops = None
        self._is_unsatisfiable = None
        if isinstance(state, tuple):
            if len(state) == 2:
                specs, prereleases = state
                if isinstance(specs, tuple) and all((isinstance(s, Specifier) for s in specs)) and _validate_pre(prereleases):
                    self._specs = specs
                    self._prereleases = prereleases
                    self._canonicalized = len(specs) <= 1
                    self._has_arbitrary = any(('===' in str(s) for s in specs))
                    return None
                elif len(state) == 2 and isinstance(state[1], dict):
                    _, slot_dict = state
                    specs = slot_dict.get('_specs', ())
                    prereleases = slot_dict.get('_prereleases')
                    if isinstance(specs, frozenset):
                        specs = tuple(sorted(specs, key=str))
                    if isinstance(specs, tuple) and all((isinstance(s, Specifier) for s in specs)) and _validate_pre(prereleases):
                        self._specs = specs
                        self._prereleases = prereleases
                        self._canonicalized = len(self._specs) <= 1
                        self._has_arbitrary = any(('===' in str(s) for s in self._specs))
                        return None
        if isinstance(state, dict):
            specs = state.get('_specs', ())
            prereleases = state.get('_prereleases')
            if isinstance(specs, frozenset):
                specs = tuple(sorted(specs, key=str))
            if isinstance(specs, tuple) and all((isinstance(s, Specifier) for s in specs)) and _validate_pre(prereleases):
                self._specs = specs
                self._prereleases = prereleases
                self._canonicalized = len(self._specs) <= 1
                self._has_arbitrary = any(('===' in str(s) for s in self._specs))
                return None
        raise TypeError(f'Cannot restore SpecifierSet from {state!r}')
    def __repr__(self):
        """A representation of the specifier set that shows all internal state.

        Note that the ordering of the individual specifiers within the set may not
        match the input string.

        >>> SpecifierSet('>=1.0.0,!=2.0.0')
        <SpecifierSet('!=2.0.0,>=1.0.0')>
        >>> SpecifierSet('>=1.0.0,!=2.0.0', prereleases=False)
        <SpecifierSet('!=2.0.0,>=1.0.0', prereleases=False)>
        >>> SpecifierSet('>=1.0.0,!=2.0.0', prereleases=True)
        <SpecifierSet('!=2.0.0,>=1.0.0', prereleases=True)>
        """
        pre = f', prereleases={self.prereleases!r}' if self._prereleases is not None else ''
        return f'<{self.__class__.__name__}({str(self)!r}{pre})>'
    def __str__(self):
        """A string representation of the specifier set that can be round-tripped.

        Note that the ordering of the individual specifiers within the set may not
        match the input string.

        >>> str(SpecifierSet(">=1.0.0,!=1.0.1"))
        '!=1.0.1,>=1.0.0'
        >>> str(SpecifierSet(">=1.0.0,!=1.0.1", prereleases=False))
        '!=1.0.1,>=1.0.0'
        """
        return ','.join((str(s) for s in self._canonical_specs()))
    def __hash__(self):
        return hash(self._canonical_specs())
    def __and__(self, other):
        """Return a SpecifierSet which is a combination of the two sets.

        :param other: The other object to combine with.

        >>> SpecifierSet(">=1.0.0,!=1.0.1") & '<=2.0.0,!=2.0.1'
        <SpecifierSet('!=1.0.1,!=2.0.1,<=2.0.0,>=1.0.0')>
        >>> SpecifierSet(">=1.0.0,!=1.0.1") & SpecifierSet('<=2.0.0,!=2.0.1')
        <SpecifierSet('!=1.0.1,!=2.0.1,<=2.0.0,>=1.0.0')>
        """
        if isinstance(other, str):
            other = SpecifierSet(other)
        elif not isinstance(other, SpecifierSet):
            return NotImplemented
        specifier = SpecifierSet()
        specifier._specs = self._specs + other._specs
        specifier._canonicalized = len(specifier._specs) <= 1
        specifier._has_arbitrary = self._has_arbitrary or other._has_arbitrary
        specifier._resolved_ops = None
        if self._prereleases is None or self._prereleases == other._prereleases:
            specifier._prereleases = other._prereleases
        elif other._prereleases is None:
            specifier._prereleases = self._prereleases
        else:
            raise ValueError('Cannot combine SpecifierSets with True and False prerelease overrides.')
        return specifier
    def __eq__(self, other):
        """Whether or not the two SpecifierSet-like objects are equal.

        :param other: The other object to check against.

        The value of :attr:`prereleases` is ignored.

        >>> SpecifierSet(">=1.0.0,!=1.0.1") == SpecifierSet(">=1.0.0,!=1.0.1")
        True
        >>> (SpecifierSet(">=1.0.0,!=1.0.1", prereleases=False) ==
        ...  SpecifierSet(">=1.0.0,!=1.0.1", prereleases=True))
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1") == ">=1.0.0,!=1.0.1"
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1") == SpecifierSet(">=1.0.0")
        False
        >>> SpecifierSet(">=1.0.0,!=1.0.1") == SpecifierSet(">=1.0.0,!=1.0.2")
        False
        """
        if isinstance(other, (str, Specifier)):
            other = SpecifierSet(str(other))
        elif not isinstance(other, SpecifierSet):
            return NotImplemented
        return self._canonical_specs() == other._canonical_specs()
    def __len__(self):
        """Returns the number of specifiers in this specifier set."""
        return len(self._specs)
    def __iter__(self):
        """
        Returns an iterator over all the underlying :class:`Specifier` instances
        in this specifier set.

        >>> sorted(SpecifierSet(">=1.0.0,!=1.0.1"), key=str)
        [<Specifier('!=1.0.1')>, <Specifier('>=1.0.0')>]
        """
        return iter(self._specs)
    def _get_ranges(self):
        """Intersect all specifiers into a single list of version ranges.

        Returns an empty list when unsatisfiable.  ``===`` specs are
        modeled as full range; string matching is checked separately
        by :meth:`_check_arbitrary_unsatisfiable`.
        """
        specs = self._specs
        result = None
        for s in specs:
            if result is None:
                result = s._to_ranges()
                continue
            result = _intersect_ranges(result, s._to_ranges())
            if not result:
                break
            else:
                continue
        if result is None:
            raise RuntimeError('_get_ranges called with no specs')
        return result
    def is_unsatisfiable(self):
        """Check whether this specifier set can never be satisfied.

        Returns True if no version can satisfy all specifiers simultaneously.

        >>> SpecifierSet(">=2.0,<1.0").is_unsatisfiable()
        True
        >>> SpecifierSet(">=1.0,<2.0").is_unsatisfiable()
        False
        >>> SpecifierSet("").is_unsatisfiable()
        False
        >>> SpecifierSet("==1.0,!=1.0").is_unsatisfiable()
        True
        """
        cached = self._is_unsatisfiable
        if cached is not None:
            return cached
        elif not self._specs:
            self._is_unsatisfiable = False
            return False
        else:
            result = not self._get_ranges()
            if not result:
                result = self._check_arbitrary_unsatisfiable()
        if not result and self.prereleases is False:
            result = self._check_prerelease_only_ranges()
        self._is_unsatisfiable = result
        return result
    def _check_prerelease_only_ranges(self):
        """With prereleases=False, check if every range contains only
        pre-release versions (which would be excluded from matching)."""
        for lower, upper in self._get_ranges():
            nearest = _nearest_non_prerelease(lower.version)
            if nearest is None:
                return False
            elif upper.version is not None:
                if nearest < upper.version:
                    return False
                elif nearest == upper.version and upper.inclusive:
                    return False
                else:
                    continue
            else:
                return False
        return True
    def _check_arbitrary_unsatisfiable(self):
        """Check === (arbitrary equality) specs for unsatisfiability.

        === uses case-insensitive string comparison, so the only candidate
        that can match ``===V`` is the literal string V.  This method
        checks whether that candidate is excluded by other specifiers.
        """
        arbitrary = [s for s in self._specs if s.operator == '===']
        if not arbitrary:
            return False
        else:
            first = arbitrary[0].version.lower()
            if any((s.version.lower() != first for s in arbitrary[1:])):
                return True
            else:
                candidate = _coerce_version(arbitrary[0].version)
                if self.prereleases is False and candidate is not None and candidate.is_prerelease:
                    return True
                standard = [s for s in self._specs if s.operator != '===']
                if not standard:
                    return False
                elif candidate is None:
                    return True
                else:
                    return not all((s.contains(candidate) for s in standard))
    def __contains__(self, item):
        """Return whether or not the item is contained in this specifier.

        :param item: The item to check for.

        This is used for the ``in`` operator and behaves the same as
        :meth:`contains` with no ``prereleases`` argument passed.

        >>> "1.2.3" in SpecifierSet(">=1.0.0,!=1.0.1")
        True
        >>> Version("1.2.3") in SpecifierSet(">=1.0.0,!=1.0.1")
        True
        >>> "1.0.1" in SpecifierSet(">=1.0.0,!=1.0.1")
        False
        >>> "1.3.0a1" in SpecifierSet(">=1.0.0,!=1.0.1")
        True
        >>> "1.3.0a1" in SpecifierSet(">=1.0.0,!=1.0.1", prereleases=True)
        True
        """
        return self.contains(item)
    pass
    pass
    def contains(self, item, prereleases=None, installed=None):
        """Return whether or not the item is contained in this SpecifierSet.

        :param item:
            The item to check for, which can be a version string or a
            :class:`Version` instance.
        :param prereleases:
            Whether or not to match prereleases with this SpecifierSet. If set to
            ``None`` (the default), it will follow the recommendation from :pep:`440`
            and match prereleases, as there are no other versions.
        :param installed:
            Whether or not the item is installed. If set to ``True``, it will
            accept prerelease versions even if the specifier does not allow them.

        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.2.3")
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains(Version("1.2.3"))
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.0.1")
        False
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.3.0a1")
        True
        >>> SpecifierSet(">=1.0.0,!=1.0.1", prereleases=False).contains("1.3.0a1")
        False
        >>> SpecifierSet(">=1.0.0,!=1.0.1").contains("1.3.0a1", prereleases=True)
        True
        """
        version = _coerce_version(item)
        if version is not None and installed and version.is_prerelease:
            prereleases = True
        if not (version is None or self._has_arbitrary and isinstance(item, Version)):
            check_item = item
        else:
            check_item = version
        return bool(list(self.filter([check_item], prereleases=prereleases)))
    @typing.overload
    def filter(self, iterable, prereleases=None, key=None):
        return None
    @typing.overload
    def filter(self, iterable, prereleases=None, key=None):
        return None
    pass
    pass
    def filter(self, iterable, prereleases=None, key=None):
        """Filter items in the given iterable, that match the specifiers in this set.

        :param iterable:
            An iterable that can contain version strings and :class:`Version` instances.
            The items in the iterable will be filtered according to the specifier.
        :param prereleases:
            Whether or not to allow prereleases in the returned iterator. If set to
            ``None`` (the default), it will follow the recommendation from :pep:`440`
            and match prereleases if there are no other versions.
        :param key:
            A callable that takes a single argument (an item from the iterable) and
            returns a version string or :class:`Version` instance to be used for
            filtering.

        >>> list(SpecifierSet(">=1.2.3").filter(["1.2", "1.3", "1.5a1"]))
        ['1.3']
        >>> list(SpecifierSet(">=1.2.3").filter(["1.2", "1.3", Version("1.4")]))
        ['1.3', <Version('1.4')>]
        >>> list(SpecifierSet(">=1.2.3").filter(["1.2", "1.5a1"]))
        ['1.5a1']
        >>> list(SpecifierSet(">=1.2.3").filter(["1.3", "1.5a1"], prereleases=True))
        ['1.3', '1.5a1']
        >>> list(SpecifierSet(">=1.2.3", prereleases=True).filter(["1.3", "1.5a1"]))
        ['1.3', '1.5a1']
        >>> list(SpecifierSet(">=1.2.3").filter(
        ... [{"ver": "1.2"}, {"ver": "1.3"}],
        ... key=lambda x: x["ver"]))
        [{'ver': '1.3'}]

        An "empty" SpecifierSet will filter items based on the presence of prerelease
        versions in the set.

        >>> list(SpecifierSet("").filter(["1.3", "1.5a1"]))
        ['1.3']
        >>> list(SpecifierSet("").filter(["1.5a1"]))
        ['1.5a1']
        >>> list(SpecifierSet("", prereleases=True).filter(["1.3", "1.5a1"]))
        ['1.3', '1.5a1']
        >>> list(SpecifierSet("").filter(["1.3", "1.5a1"], prereleases=True))
        ['1.3', '1.5a1']
        """
        if prereleases is None and self.prereleases is not None:
            prereleases = self.prereleases
        if self._specs:
            if len(self._specs) == 1:
                filtered = self._specs[0].filter(iterable, prereleases=True if prereleases is None else prereleases, key=key)
            else:
                filtered = self._filter_versions(iterable, key, prereleases=True if prereleases is None else prereleases)
            if prereleases is not None:
                return filtered
            else:
                return _pep440_filter_prereleases(filtered, key)
        elif prereleases is True:
            return iter(iterable)
        elif prereleases is False:
            return (item for item in iterable if key is None and (version := item(key(item))) is not None and not version.is_prerelease)
        else:
            return _pep440_filter_prereleases(iterable, key)
    """"""
    def _filter_versions(self, iterable, key, prereleases=None):
        """Filter versions against all specifiers in a single pass.

        Uses Cost Based Ordering: specifiers are sorted by _operator_cost so
        that cheap range operators reject versions early, avoiding expensive
        wildcard or compatible operators on versions that would have been
        rejected anyway.
        """
        if self._resolved_ops is None:
            self._resolved_ops = sorted(((spec._get_operator(spec.operator), spec.version, spec.operator) for spec in self._specs), key=_operator_cost)
        ops = self._resolved_ops
        exclude_prereleases = prereleases is False
        for item in iterable:
            parsed = _coerce_version(item if key is None else key(item))
            if parsed is None:
                if all((str(item).lower() == ver.lower() for _, ver, op in ops)):
                    yield item
                else:
                    continue
                continue
            elif exclude_prereleases and parsed.is_prerelease:
                continue
            elif all((item if op == '===' else key(item) for op_fn, ver, op in ops)):
                yield item
