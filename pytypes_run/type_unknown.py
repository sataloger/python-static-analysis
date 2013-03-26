# -*- coding: utf-8 -*-

from opcode import opname
from copy import copy, deepcopy
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from analyzer.pytypes_run.base_classes import BaseType


class TypeUnknown(BaseType):
    implemented_types = ('unknown',)
    insts_handler = deepcopy(BaseType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    # singleton feature
    _instance = None
    @staticmethod
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TypeUnknown, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @staticmethod
    def implement_inst(inst_name):
        return inst_name in TypeUnknown.implemented_insts

    @staticmethod
    def handle_inst(inst_name, *args, **kwargs):
        if inst_name in TypeUnknown.implemented_insts:
            return TypeUnknown.insts_handler.handle(inst_name, *args, **kwargs)
        else:
            raise NotImplementedError("%s doesn't implement instruction %r" % \
                     (TypeUnknown.__name__, inst_name))

#    def __deepcopy__(self, memo):
#        return self.__class__()

    def __deepcopy__(self, memo):
        return self

    def create_from_const(self, const):
        self.add_const(const)

    def create_from(self, other):
        self.add_type(other)

    def _lge_inner(self, other):
        return (0, 0, 1)

    def __nonzero__(self):
        return True

    def _repr_inner(self):
        return '%s(id: %r)' % (self.clsname, id(self))

    def _pretty_inner(self):
        return self.implemented_types[0]

    def _list_names(self):
        return ('unknown',)

    def add_type(self, other):
        if self.__class__ != other.__class__:
            print "Warning: adding type to unknown: %r" % other

    def add_const(self, const):
        pass
#        if const is not None:
#            print "Warning: got not None as const at %s.add_const(): %r ###" % (self.clsname, const)

    def process_any(self, inst, *args, **kwargs):
        if self.__class__ != TypeUnknown:
            if mydebugDict['printWarnings']:
                print "Warning: %r instance handling %r through TypeUnknown" % \
                        (self, (inst[0], opname[inst[1]], inst[2]))

        iname = opname[inst[1]]
        if iname in INSTS_NO_PUSH:
            return
        elif iname != 'UNPACK_SEQUENCE':
            return {"types":TypeUnknown()}
        else:
            return {"types":[create_unknown() for i in range(inst[2])]}
        
    insts_handler.add_set(InstSet(VAR_INSTS, process_any))

class ParentType(TypeUnknown):
    implemented_types = ('unknown',)
    insts_handler = deepcopy(TypeUnknown.insts_handler)
    implemented_insts = insts_handler.stored_insts

    @staticmethod
    def __new__(cls, *args, **kwargs):
        return super(TypeUnknown, cls).__new__(cls, *args, **kwargs)

    def implement_inst(self, inst_name):
        direct_impl = (inst_name in self.implemented_insts) or \
                      (inst_name in self.redirected_insts)
        if not direct_impl:
            raise Exception(ParentType.__base__)
            basecls = ParentType.__base__
#            while basecls != ParentType.__base__:
#                basecls = basecls.__base__
            return basecls.implement_inst(inst_name)
        else:
            return True

    def handle_inst(self, inst_name, *args, **kwargs):
        if inst_name in self.implemented_insts:
            kwargs['self_obj'] = self
            return self.insts_handler.handle(inst_name, *args, **kwargs)
        elif inst_name in self.redirected_insts:
            return self.handle_inst_rd(inst_name, *args, **kwargs)
        else:
            basecls = ParentType.__base__
            if basecls.implement_inst(inst_name):
                kwargs['self_obj'] = self
                return basecls.handle_inst(inst_name, *args, **kwargs) 
            else:
                raise NotImplementedError("%s doesn't implement instruction %r" % \
                         (self.__class__.__name__, inst_name))

