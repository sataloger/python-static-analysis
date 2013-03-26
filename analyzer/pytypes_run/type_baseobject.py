# -*- coding: utf-8 -*-

from copy import copy, deepcopy
from itertools import *
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_unknown import ParentType

class TypeBaseObject(ParentType):
    implemented_types = ('baseobject',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("%s doesn't implement __init__()" % self.clsname)

    def __deepcopy__(self, memo):
        raise NotImplementedError("%s doesn't implement __deepcopy__()" % self.clsname)

    def create_from_const(self, const):
        raise Exception('Something1')
        self.stored_types = set()
        self.add_const(const)

    def _repr_inner(self):
        return ('%s(' % self.clsname) + \
                ';\t'.join([ "%s:%r" % (name, attr)
                           for name, attr in self.attrs.items()]) + ')'

    def create_from(self, other):
        raise Exception('Something2')
        self.stored_types = set()
        self.add_type(other)

    def _lge_inner(self, other):
        sa = set(self.attrs.keys())
        oa = set(other.attrs.keys())
        lge_list = [self.attrs[name].lge(other.attrs[name]) 
                    for name in sa & oa]
        if lge_list:
            if len(lge_list) > 1:
                lge_united = map(all, map(None, *lge_list))
            else:
                lge_united = lge_list[0]
        else:
            lge_united = (1, 1, 1)
        less = int(sa <= oa and lge_united[0])
        greater = int(sa >= oa and lge_united[1])
        equal = int(sa == oa and lge_united[2])
        print self, other, (less, greater, equal)
        return (less, greater, equal)

    def __nonzero__(self):
        return True

    def _list_names(self):
        return ('object',)

    def store_attr(self, inst, vars):
        attrname = smtbl.get_varname_by_id(inst[2])#
        if attrname in self.attrs:
            self.attrs[attrname]["types"] |= vars[0]["types"]
        else:
            self.attrs[attrname] = vars[0]
#        print (inst[0], "STORE_ATTR", attrname), self, vars

    def delete_attr(self, inst):
        attrname = smtbl.get_varname_by_id(inst[2])
        if attrname in self.attrs:
            pass
#            del self.attrs[attrname]
        else:
            print "Warning: trying to delete attribute %r from %r" % (attrname, self)

    def load_attr(self, inst):
        attrname = smtbl.get_varname_by_id(inst[2])
        if attrname in self.attrs:
            return self.attrs[attrname]
        else:
            print "Warning: trying to load attribute %r from %r" % (attrname, self)
            return {"types":create_unknown()}

    def add_type(self, other):
        if self.__class__ != other.__class__:
            print "Warning: adding type to object: %r" % other
        # FIXME
        sa = set(self.attrs.keys())
        oa = set(other.attrs.keys())
#        print "Updating1:", self, other
        for name in sa & oa:
            self.attrs[name]["types"] |= other.attrs[name]["types"]
        for name in oa - sa:
            self.attrs[name]["types"] = deepcopy(other.attrs[name]["types"])
#        print "Updating2:", self, other

    def add_const(self, const):
        print "Got %r at TypeBaseObject.add_const()" % const

    insts_handler.add_set(InstSet(['STORE_ATTR'], store_attr))
    insts_handler.add_set(InstSet(['LOAD_ATTR'], load_attr))
    insts_handler.add_set(InstSet(['DELETE_ATTR'], delete_attr))

