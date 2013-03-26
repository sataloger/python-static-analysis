# -*- coding: utf-8 -*-

import sys
import itertools
from random import randint
from copy import copy, deepcopy
from itertools import *
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_tuple import TypeTuple, TypeSuperContainer

class TypeList(TypeTuple):
    implemented_types = ('list',)

    def store_subscr(self, inst, vars):
        values = self.values
        newtypes = set()
        vartostore_types = vars[-1]["types"].types
        for typename in vartostore_types:
            if typename == 'TypeSimple':
                newtypes.update(vartostore_types[typename].stored_types)
            else:
                newtypes.update(vartostore_types[typename].implemented_types)
        if self.values:
            for curset in copy(self.values):
                if not curset.issuperset(newtypes):
                    values.remove(curset)
                    values.add(curset | newtypes)
        else:
            new_values.add(frozenset(newtypes))
        self.values = values

    # hack to process through store_subscr
    def append(self, var):
        self.store_subscr(42, [var])
        if self.length != self.maxlen_name:
            self.length += 1
        self.len_fixed = False
        self.fix_length(self.length)
        
    # hack to lose length info in list comrehentions
    def list_append(self, vars):
        self.store_subscr(42, vars)
        self.length = self.maxlen_name
        self.len_fixed = False
        self.fix_length(self.length)
        

class TypeSuperList(TypeSuperContainer):
    implemented_types = ('list',)
    cont_class = TypeList

    insts_handler = deepcopy(TypeSuperContainer.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def store_slice(self, inst, vars):
        storeobj = vars[-1]
        conts = storeobj.get_containers()
        if conts:
            for cont in conts:
                self.store_slice_from_cont(inst, vars[:-1], cont)
        else:
            if 'unknown' not in storeobj.types:
                print "WARNING: trying to iterate over non-iterable object(%r)" % storeobj
            unknown_cont = TypeSuperContainer(self.maxlen, 
                                              self.maxlen_name,
                                              TypeTuple)
            unknown_cont.create(None)
            self.store_slice_from_cont(inst, vars[:-1],
                                       unknown_cont)
        self.check_length('TEST20')


    def store_slice_from_cont(self, inst, vars, storeobj):
        if opname[inst[1]] == 'STORE_SLICE+0':
            self.values.clear()
            self.values = deepcopy(storeobj.values)
            return
        res = self.cont_class(self.maxlen, self.maxlen_name)
        for sl in self.values.values():
            for ol in storeobj.values.values():
                res |= sl.add((ol,))
        res.length = self.maxlen_name

        self.values = {self.maxlen_name: res}
        self.check_length('TEST21')

    def delete_slice(self, inst, vars):
        if opname[inst[1]] == 'DELETE_SLICE+0':
            self.clear()
        else:
            new_values = self.cont_class(self.maxlen, self.maxlen_name)
            for sl in self.values.values():
                res_values.iadd(sl)
            new_values.length = self.maxlen_name
            self.values = {self.maxlen_name: res_values}


    def store_subscr(self, inst, vars):
        for lst in self.values.values():
            lst.store_subscr(inst, vars)

    def append(self, var):
        for lst in self.values.values():
            lst.append(var)
        self._rehash_length()

    def list_append(self, inst, vars):
        for lst in self.values.values():
            lst.list_append(vars)
        self._rehash_length()

    def _rehash_length(self):
        new_values = {}
        for length, lst in self.values.items():
            if lst.length in new_values:
                new_values[lst.length] |= lst
            else:
                new_values[lst.length] = lst
        if 0 in new_values:
            new_values[0].clear()
        self.values = new_values

    # hack to process through delete_subscr
    def pop(self, index=-1):
        self.delete_subscr(42, [])
        
    def delete_subscr(self, inst, vars):
        new_values = {}
        for length, lst in self.values.items():
            if length != self.maxlen_name and length:
                lst.length -= 1
        self._rehash_length()
#            new_values[lst.length] = lst
#        if 0 in new_values:
#            new_values[0].clear()
#        self.values = new_values


    insts_handler.add_set(InstSet(['STORE_SLICE+0', 'STORE_SLICE+1', 
                                   'STORE_SLICE+2', 'STORE_SLICE+3'], 
                                  store_slice))
    insts_handler.add_set(InstSet(['DELETE_SLICE+0', 'DELETE_SLICE+1', 
                                   'DELETE_SLICE+2', 'DELETE_SLICE+3'], 
                                  delete_slice))
    insts_handler.add_set(InstSet(['STORE_SUBSCR'], store_subscr))
    insts_handler.add_set(InstSet(['DELETE_SUBSCR'], delete_subscr))
    insts_handler.add_set(InstSet(['LIST_APPEND'], list_append))



