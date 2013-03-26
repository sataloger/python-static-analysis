# -*- coding: utf-8 -*-

import sys
import itertools
from random import randint
from copy import copy, deepcopy
from itertools import *
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_tuple import TypeSuperContainer
from pytypes_run.type_list import TypeList, TypeSuperList

class TypeDict(TypeList):
    implemented_types = ('dict',)

    def __init__(self, *args, **kwargs):
        self.__class__.__base__.__init__(self, *args, **kwargs)
        self.values = {}

    def _repr_inner(self):
        res_lst = map(lambda k: "%r:%r" %(list(k), list(self.values[k])),
                      self.values)
        return ('%s_%s({' % (self.clsname, str(self.length))) + \
            '}, {'.join(res_lst)+ '})'

    def _pretty_inner(self):
        if self.length:
            res_lst = map(lambda k: "%r:%r" %(list(k), list(self.values[k])),
                          self.values)
            return ('%s_%s({' % (self.implemented_types[0], str(self.length))) + \
                '}, {'.join(res_lst)+ '})'
        else:
            return '%s_0' % self.implemented_types[0]

    def create_from_const(self, value):
        if value is None:
            self.stored_types = set(self.implemented_types)
            self.values = {frozenset(['unknown']):set(['unknown'])}
            self.length = self.maxlen_name
        else: 
            self.stored_types = set([type(value).__name__])
            self.values = {frozenset([get_const_typename(item)
                                      for item in value.keys()]):\
                           set([get_const_typename(item)
                                      for item in value.values()])
                          }
            self.__length = len(value)
        self.len_fixed = True

    def _list_names(self):
        return set(self.implemented_types)

    def create_from(self, other):
        self.stored_types = deepcopy(other.stored_types)
        self.values = deepcopy(other.values)
        self.length = other.length
        self.len_fixed = True


    def update_set(self, key, value):
        if key not in self.values:
            self.values[key] = value
        else:
            self.values[key] |= value


    def add_const(self, const):
        if const is None:
            self.update_set(frozenset(['unknown']), set(['unknown']))
            return
        if len(const) != self.length and \
           not (self.length == self.maxlen_name and \
                len(const) > self.maxlen):
            raise Exception("In %s.add_const: lengths differ(%r:%r)" % \
                            (self.clsname, self.length, len(const)))

        self.update_set(frozenset([get_const_typename(item)
                                  for item in const.keys()]),
                        set([get_const_typename(item)
                             for item in const.values()])
                       )


    def add_type(self, other):
        self.stored_types.update(other.stored_types)
        self.values.update(deepcopy(other.values))
        if self.length != other.length:
            self.length = self.maxlen_name

    def _lge_inner(self, other):
        if self.length != other.length:
            raise Exception("Couldn't compare tuples with unequal length(%d:%d)" % \
                              (self.length, other.length))

        equal = set(self.values) == set(other.values) and \
                all(map(lambda k: self.values[k] == other.values[k],
                        self.values))

        less = not equal and (set(self.values) < set(other.values) or \
               (set(self.values) == set(other.values) and \
                all(map(lambda k: self.values[k] <= other.values[k],
                        self.values))))

        greater = not equal and (set(self.values) > set(other.values) or \
               (set(self.values) == set(other.values) and \
                all(map(lambda k: self.values[k] >= other.values[k],
                        self.values))))

        return (less, greater, equal)


    def __nonzero__(self):
        return len(self.values)

    def store_subscr(self, inst, vars):
        new_values = self.values
        value_types = set()
        cur_types = vars[1]["types"].types
        for typename in cur_types:
            if typename == 'TypeSimple':
                value_types.update(cur_types[typename].stored_types)
            else:
                value_types.update(cur_types[typename].implemented_types)


        key_types = set()
        cur_types = vars[0]["types"].types
        for typename in cur_types:
            if typename == 'TypeSimple':
                key_types.update(cur_types[typename].stored_types)
            else:
                key_types.update(cur_types[typename].implemented_types)
        key_types = frozenset(key_types)

        if self.values:
            prev_values = deepcopy(self.values)
            self.values = {}
            for curset in prev_values:
                self.update_set(curset|key_types, 
                                prev_values[curset]|value_types)
        else:
            self.update_set(key_types, value_types)

class TypeSuperDict(TypeSuperList):
    implemented_types = ('dict',)
    cont_class = TypeDict

    insts_handler = deepcopy(TypeSuperList.insts_handler)
    implemented_insts = insts_handler.stored_insts


    def build(self, inst):
        res = self.cont_class(self.maxlen, self.maxlen_name)
        res.fix_length(self.maxlen_name)
        self.values = {res.length: res}

#    insts_handler.add_set(InstSet(['STORE_MAP'], 
#                                  TypeSuperList.store_subscr))
    insts_handler.add_set(InstSet(['STORE_SUBSCR', 'STORE_MAP'], 
                                  TypeSuperList.store_subscr))
    insts_handler.add_set(InstSet(['DELETE_SUBSCR'], 
                                  TypeSuperList.delete_subscr))


