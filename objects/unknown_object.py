# -*- coding: utf-8 -*-
from copy import deepcopy
from opcode import opname
from analyzer.objects.base_classes import BaseInfoStorage
from analyzer.py_run.var_operations import INSTS_NO_PUSH, VAR_INSTS

class UnknownObject(BaseInfoStorage):
    implemented_type = 'unknown'
    implemented_values = ['unknown',]
    linked_may_names = []
    linked_must_names = []
    insts_handlers = deepcopy(BaseInfoStorage.insts_handlers)
    _instance = None

    @staticmethod
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UnknownObject, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def process_any(self, inst, *args, **kwargs):
        if self.__class__ != UnknownObject:
            print "Warning: %r instance handling %r through UnknownObject" % \
                      (self, (inst[0], opname[inst[1]], inst[2]))

        iname = opname[inst[1]]
        if iname in INSTS_NO_PUSH:
            return
        elif iname != 'UNPACK_SEQUENCE':
            return {"objects":UnknownObject()}
        else:
            return {"objects":[UnknownObject() for i in range(inst[2])]}

    for inst in VAR_INSTS:
        insts_handlers.add_inst(inst, process_any)