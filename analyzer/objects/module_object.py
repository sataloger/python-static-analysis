# -*- coding: utf-8 -*-
from copy import deepcopy, copy
import sys
from analyzer.objects.base_object import BaseObject
from analyzer.py_run.functions import getmodulename, getabspath, setglobal
from analyzer.objects.callable_object import CallableObject
import ihooks
from analyzer.pytypes_run import cfg_wrapper

__author__ = 'sataloger'

class ModuleObject(CallableObject, BaseObject):
    implemented_type = 'module'
    insts_handlers = deepcopy(CallableObject.insts_handlers)
    il = ihooks.ModuleLoader()

    def __init__(self, module=None, name=None, path=None):
        CallableObject.__init__(self)
        self.implemented_values = []
        self.linked_may_names = []
        self.linked_must_names = []

        if name:
            self.create_from_const(module.top.codeobj)
            self.names = {name: path}
            self.last_name = name
            self.module = module
            self.attrs = {}
        else:
            self.names = {}
            self.module = None
            self.attrs = {}

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.module = self.module
        res.names = copy(self.names)
        res.last_name = self.last_name
        res.attrs = copy(self.attrs)
        return res

    def _set_attrs(self):
        cur_name = self.last_name
        try:
            smt = self.module.cfg[cur_name].bbs['exit'].states['normal'].smtbl
            self.attrs.clear()
            for name, v in smt.globals.items():
                self.attrs[name] = v
        except KeyError, msg:
            print "Warning: %r" % sys.exc_info()[1]
            self.attrs.clear()

    def call(self, *args, **kwargs):
        if self.module is not None:
            modules_stack.append(self)
            super(ModuleObject, self).call(*args, **kwargs)
            modules_stack.pop()

    @staticmethod
    def from_code(path):
        path = getabspath(path)
        module_name = getmodulename(path)
        res = ModuleObject(cfg_wrapper.import_module(path), module_name, path)
#        prev_state = _state

#        CallableObject._set_state(RootState)
        res.call(0)
        res._set_attrs()
#        CallableObject._set_state(prev_state)
        import_table[path] = res
        return res

    @staticmethod
    def _set_state(state):
        setglobal('stack', state.stack)
        setglobal('smtbl', state.smtbl)
        setglobal('_aso', state._aso)
        setglobal('_state', state)