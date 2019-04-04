'''
    This module provide some facilities to use YAML formated data.
    It defines several decorators to easily create YAML compatible
    classes witch will be used both in parsing YAML formated data
    and in writing YAML formated data.
'''
from __future__ import print_function, division, unicode_literals
import re
from inspect import ismethod
import yaml

from . import Loader
from .errors import NotAvailableTagError

re_word = re.compile(r'[a-zA-Z0-9_]+')


def normalize_attr(string):
    return '_'.join(re_word.findall(string))  # .lower()


def yaml_tag_mangle(Cls):
    '''
        Return the mangled name of the attribute __yaml_tag.
    '''
    return '_' + Cls.__name__.lstrip('_') + '__yaml_tag'


def yaml_map(Cls):
    '''
        Register a class as a known tag for YAML.
        The class must expose methods from_map and to_map.
        from_map must return a valid instance of Cls.
        It can be a classmethod or a normal method but in
        the last case 'Cls()' must be a valid initialisation.
    '''
    tag = '!' + getattr(Cls, yaml_tag_mangle(Cls), Cls.__name__)

    def constructor(loader, node):
        map = dict(loader.construct_mapping(node, deep=True))
        if ismethod(Cls.from_map):
            return Cls.from_map(map)
        else:
            return Cls().from_map(map)

    def representer(dumper, data):
        return dumper.represent_mapping(tag, data.to_map())

    yaml.add_constructor(tag, constructor, Loader=Loader)
    yaml.add_representer(Cls, representer)

    return Cls


def yaml_seq(Cls):
    '''
        Register a class as a known tag for YAML.
        The class must expose methods from_seq and to_seq.
        from_seq must return a valid instance of Cls.
        It can be a classmethod or a normal method but in
        the last case 'Cls()' must be a valid initialisation.
    '''
    tag = '!' + getattr(Cls, yaml_tag_mangle(Cls), Cls.__name__)

    def constructor(loader, node):
        seq = list(loader.construct_sequence(node, deep=True))
        if ismethod(Cls.from_seq):
            return Cls.from_seq(seq)
        else:
            return Cls().from_seq(seq)

    def representer(dumper, data):
        return dumper.represent_sequence(tag, data.to_seq())

    yaml.add_constructor(tag, constructor, Loader=Loader)
    yaml.add_representer(Cls, representer)

    return Cls


def yaml_scalar(Cls):
    '''
        Register a class as a known tag for YAML.
        The class must expose methods from_scalar to_scalar.
        from_scalar must return a valid instance of Cls.
        It can be a classmethod or a normal method but in
        the last case 'Cls()' must be a valid initialisation.
    '''
    tag = '!' + getattr(Cls, yaml_tag_mangle(Cls), Cls.__name__)

    def constructor(loader, node):
        scalar = loader.construct_scalar(node)
        if ismethod(Cls.from_scalar):
            return Cls.from_scalar(scalar)
        else:
            return Cls().from_seq(scalar)

    def representer(dumper, data):
        return dumper.represent_scalar(tag, data.to_scalar())

    yaml.add_constructor(tag, constructor, Loader=Loader)
    yaml.add_representer(Cls, representer)

    return Cls


class BaseDictWrapper(object):
    '''
        Allow attribute access and key access to the values of dictionary to
        keep a consistent behaviour with AutoMap structures.
    '''
    _is_dict_like = True

    def __init__(self, d={}):
        for attr in d:
            self[attr] = d[attr]

    def get(self, key, default=None):
        nkey = normalize_attr(key)
        if nkey in self.__dict__:
            elem = self.__dict__[nkey]
        else:
            elem = default
        if type(elem) is dict:
            return BaseDictWrapper(elem)
        else:
            return elem

    def __getitem__(self, key):
        nkey = normalize_attr(key)
        if nkey not in self.__dict__:
            raise KeyError(key)
        elem = self.__dict__[nkey]
        if type(elem) is dict:
            return BaseDictWrapper(elem)
        else:
            return elem

    def __setitem__(self, key, val):
        if type(val) is dict:
            val = BaseDictWrapper(val)
        self.__dict__[normalize_attr(key)] = val

    def __repr__(self):
        r = self.__class__.__name__ + '('
        for attr, val in self.__dict__.items():
            r += '{}={}, '.format(attr, val)
        return r[:-2] + ')'

    def __iter__(self):
        for key in self.__dict__:
            yield key

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()


def auto_map(Cls):
    '''
        Automatically append methods from_map, to_map and __repr__ to a
        class intended to be used with YAML tag, as long as __getitem__
        and __setitem__ to be accessed like a dictionnary. Attributes name
        are normalized to be accessible as regular property even if the
        original name contained spaces or special characters. The original
        name can still be used in dict like access.
        Example:
            >>> @auto_map
            ... class A(object):
            ...     pass
            ...
            >>> a = A()
            >>> a['attr w/ spaces'] = 78
            >>> a.attr_w_spaces
            78
            >>> a.attr_w_spaces = 82
            >>> a['attr w/ spaces']
            82
            >>> # be careful, simple normalization imply collisions
            >>> a['attr .w. --spaces']
            82
    '''
    class AutoMap(Cls, BaseDictWrapper):
        @classmethod
        def from_map(cls, d):
            new = cls()
            for attr in d:
                new[attr] = d[attr]
            return new

        def to_map(self):
            return self.__dict__

    AutoMap.__name__ = Cls.__name__
    return AutoMap


def yaml_auto_map(Cls):
    '''
            @yaml_auto_map
        is equivalent to:
            @yaml_map
            @auto_map
    '''
    return yaml_map(auto_map(Cls))


def yaml_implicit_scalar(Cls):
    '''
        Register a class as a known tag for YAML and a pattern
        wich imply this tag.
        The class must expose methods from_scalar to_scalar.
        Moreover it must have a class attribute yaml_pattern that
        can be either a string containing the regex pattern matching
        all string representing this kind of data or the compiled
        object of this same regex.
    '''
    yaml_scalar(Cls)  # register the constructor and the representer
    tag = '!' + getattr(Cls, yaml_tag_mangle(Cls), Cls.__name__)

    re_pattern = Cls.yaml_pattern
    if not hasattr(re_pattern, 'match'):
        re_pattern = re.compile(re_pattern)
    yaml.add_implicit_resolver(tag, re_pattern)  # register the mplicit pattern
    return Cls


def yaml_not_available_tag(tag, reason):
    def constructor(loader, node):
        raise NotAvailableTagError(tag, reason)
    yaml.add_constructor('!' + tag, constructor, Loader=Loader)
