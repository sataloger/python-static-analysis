# -*- coding: utf-8 -*-

import sys
from random import randint
from copy import copy, deepcopy
from itertools import *
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_tuple import TypeTuple, TypeSuperContainer
from pytypes_run.type_unknown import ParentType


class TypeSimple(ParentType):
    implemented_types = ('bool', 'int', 'float', 'complex', 'str', 'unicode', 'NoneType', 'type', 'undef')
    container_types = ('str', 'unicode')
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, *args, **kwargs):
        ParentType.__init__(self, *args, **kwargs)
        # gotcha! let's have some of value analysis here :)
        self._last_const = {}
        self.stored_types = set()

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.stored_types = copy(self.stored_types)
        res._last_const = copy(self._last_const)
        return res

    def create_from_const(self, const):
        self.stored_types.clear()
        self._last_const.clear()
        self.add_const(const)

    def create_from(self, other):
        self.stored_types.clear()
        self._last_const.clear()
        self.add_type(other)

    def _lge_inner(self, other):
        less = self.stored_types < other.stored_types
        greater = self.stored_types > other.stored_types
        equal = self.stored_types == other.stored_types
        return (less, greater, equal)

#    def _repr_inner(self):
#        return ('%s(' % self.clsname) + \
#               ', '.join(map(repr, self.stored_types)) + ')'

    def _repr_inner(self):
        res = ('%s(' % self.clsname)
        lst = []
        for name in self.stored_types:
            if name in self._last_const:
                lst.append('%s(%r)' % (name, self._last_const[name]))
            else:
                lst.append(name)

        res += ', '.join(lst)
        return res + ')' 

    def _pretty_inner(self):
        lst = []
        for name in self.stored_types:
            if name in self._last_const:
                lst.append('%s(%r)' % (name, self._last_const[name]))
            else:
                lst.append(name)

        res = ', '.join(lst)
        return res

    def __nonzero__(self):
        return len(self.stored_types) > 1 or \
               (len(self.stored_types) == 1 and \
                'undef' not in self.stored_types)

    def _list_names(self):
        return set(self.stored_types)

    def add_type(self, other):
        self.stored_types.update(other.stored_types)
        self.check_current_type()
        self._last_const.update(other._last_const)

    def add_const(self, const):
        clsname = type(const).__name__
        self.stored_types.add(clsname)
        self.check_current_type()
        self._last_const[clsname] = const

    def add_typename(self, typename):
        self.stored_types.add(typename)
        self.check_current_type()

    def __div__(self, other):
       typesdiv = set(self.types) - set(other.types)
       res = self.__class__()
       res.types = typesdiv
       return res

    def get_iter(self):
        res = set()
        for name in self.container_types:
            if name in self.stored_types:
                res.add(name)
        for name in self.stored_types:
            if name not in self.container_types:
                res.add('unknown')
                print "Warning: possible iteration of non-container type: %r" % name
                break
        return res



    def __inst_unite_info(self, vars):
        other = vars[0]
        if other is not None:
            return {"types":self | other["types"]}
        else:
            res = {"types": create_unknown()}
            res["types"].add_typeobj(deepcopy(self))
            return res

    def binary_subscr(self, inst, vars):
        init_types = {}
        for name in self.container_types:
            if name in self.stored_types:
                init_types[name] = None
        for name in self.stored_types:
            if name not in self.container_types:
                init_types['unknown'] = None
                print "Warning: possible subscribe of non-container type: %r" % name
                break
        return {"types":VarTypes(init_types=init_types)}


    insts_handler.add_set(InstSet(['BINARY_POWER', 'BINARY_MULTIPLY',
        'BINARY_DIVIDE', 'BINARY_MODULO', 'BINARY_ADD',
        'BINARY_SUBTRACT', 'BINARY_SUBSCR', 'BINARY_FLOOR_DIVIDE',
        'BINARY_TRUE_DIVIDE', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
        'BINARY_AND', 'BINARY_XOR', 'BINARY_OR', 'INPLACE_FLOOR_DIVIDE',
        'INPLACE_TRUE_DIVIDE', 'INPLACE_ADD', 'INPLACE_SUBTRACT',
        'INPLACE_MULTIPLY', 'INPLACE_DIVIDE', 'INPLACE_MODULO',
        'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT',
        'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR'], __inst_unite_info))

    insts_handler.add_set(InstSet(['UNARY_POSITIVE', 'UNARY_NEGATIVE',
                                   'UNARY_INVERT'], ParentType.do_nothing))

    insts_handler.add_set(InstSet(['BINARY_SUBSCR'], binary_subscr))


class TypeSlice(ParentType):
    implemented_types = ('slice',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, *params):
        ParentType.__init__(self)


class TypeCode(ParentType):
    implemented_types = ('code',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self):
        ParentType.__init__(self)
        self.code = None

    def __deepcopy__(self, memo):
        return self

    def _repr_inner(self):
        return '%s(%r)' % (self.clsname, self.code)

    def create(self, value):
        if isinstance(value, self.__class__):
            self.create_from(value)
        else:
            self.create_from_const(value)

    def create_from_const(self, value):
        if value is None:
            raise NotImplementedError("###Got None as const here!###")
        self.code = value

    def __ior__(self, other):
        if isinstance(other, self.__class__):
            self.add_type(other)
        else:
            self.add_const(other)
        return self

    def create_from(self, other):
        self.code = other.code

    def add_const(self, const):
        if const is None:
            raise NotImplementedError("###Got None as const here!###")
        self.code = const

    def add_type(self, other):
        raise NotImplementedError("%s.add_type: can't add_type to code objects" % self.clsname)

    def _lge_inner(self, other):
        equal = self.code == other.code
        return (0, 0, equal)

    def __nonzero__(self):
        return self.code is not None

class TypeIterator(ParentType):
    implemented_types = ('iterator',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self):
        ParentType.__init__(self)
        self.values = set()

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.values = copy(self.values)
        return res

    def _repr_inner(self):
        return ('%s<[' % self.clsname) + \
               ', '.join(map(repr, self.values)) + ']>'

    def _pretty_inner(self):
        return ('%s(' % self.implemented_types[0]) + ', '.join(map(repr, self.values)) + ')'

    def create(self, value):
        if isinstance(value, (self.__class__, TypeTuple, TypeList, TypeDict)):
            self.create_from(value)
        else:
            self.create_from_const(value)

    def create_from_const(self, const):
        if const is None:
            raise NotImplementedError("###Got None as const here!###")
            self.values = set(['unknown'])
        else:
            it, _ = itertools.tee(const)
            cnt = 0
            buf = set()
            for item in it:
                cnt += 1
                if cnt > 10:
                    break
                buf.add(get_const_typename(item))
            self.values.update(buf)
#            self.values = set([get_const_typename(item) for item in value])

    def __ior__(self, other):
        if isinstance(other, (self.__class__, TypeSuperContainer)):
            self.add_type(other)
        else:
            self.add_const(other)
        return self

    def create_from(self, other):
        if isinstance(other, self.__class__):
            self.values = deepcopy(other.values)
        else: #creating iterator from container
            values = set()
            for curcont in other.values.values():
                for curset in curcont.values:
                    values.update(curset)
            self.values = values

    def add_const(self, const):
        if const is None:
            raise NotImplementedError("###Got None as const here!###")
            self.values.add('unknown')
        else:
            it, _ = itertools.tee(const)
            cnt = 0
            buf = set()
            for item in it:
                cnt += 1
                if cnt > 10:
                    break
                buf.add(get_const_typename(item))
            self.values.update(buf)

#            self.values.update([get_const_typename(item) for item in it])

    def add_type(self, other):
        if isinstance(other, self.__class__):
            self.values.update(deepcopy(other.values))
        else: #creating iterator from container
            for curcont in other.values.values():
                for curset in curcont.values:
                    self.values.update(curset)

    def _lge_inner(self, other):
        less = self.values < other.values
        greater = self.values > other.values
        equal = self.values == other.values
        return (less, greater, equal)

    def __nonzero__(self):
        return len(self.values)

    def next(self, inst):
        init_types = {}
        for name in self.values:
            init_types[name] = None
        return {"types":VarTypes(init_types=init_types)}

    insts_handler.add_set(InstSet(['FOR_ITER'], next))

class TypeGeneratorObject(TypeIterator):
    implemented_types = ('generator_object',)

#    def __ior__(self, other):
#        if self.smtbl is not None and other.smtbl is not None:
#            self.smtbl |= other.smtbl

