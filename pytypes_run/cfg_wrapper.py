# -*- coding: utf-8 -*-

import pytypes_cfg.cfg_creator as cfg_creator
from pytypes_run.base_classes import *
from pytypes_cfg.cfg_creator import CFGCreator
from pprint import pprint

class bb(cfg_creator.bb):
    def __init__(self, *args, **kwargs):
        if 'base_instance' in kwargs:
            for attr in dir(kwargs['base_instance']):
                if not (attr.startswith('__') and attr.endswith('__')):
                    setattr(self, attr, getattr(kwargs['base_instance'], attr))
        else:
            cfg_creator.bb.__init__(self, *args, **kwargs)
        self.states = kwargs['states']
        try:
            first_smtbl # hack to overcome first import (at entry point)
#            print "hacked"
        except NameError:
            setglobal('first_smtbl', self.states.states['normal'].smtbl)
#            print "hacking"
#            self._set_smtbl_stack(self.states.states['normal'].smtbl,
#                    self.states.states['normal'].stack) 

    def __repr__(self):
        res = "%s\n%r" % (cfg_creator.bb.__repr__(self), self.states)
        return res

class cfg(cfg_creator.cfg):
    def __init__(self, *args, **kwargs):
        if 'base_instance' in kwargs:
            for attr in dir(kwargs['base_instance']):
                if not (attr.startswith('__') and
                   attr.endswith('__')) and attr != 'bbs':
                    setattr(self, attr, getattr(kwargs['base_instance'],
                                                attr))
            bbs_orig = kwargs['base_instance'].bbs
        else:
            cfg_creator.cfg.__init__(self, *args, **kwargs)
            bbs_orig = self.bbs


        consts = [(const,) for const in self.codeinfo['co_consts']]

        # setting up codeobjects hierarchy
        for const in self.codeinfo['co_consts']:
            if isinstance(const, self.codeobj.__class__):
                parent_code[const] = self.codeobj

        self.bbs = {}

        newkw = {'smtbl_args': {'vars': (self.codeinfo['co_names'],
                                         self.codeinfo['co_varnames'],
                                         self.codeinfo['co_cellvars'],
                                         self.codeinfo['co_freevars']),
                                'consts': consts,
                                'arg_count': self.codeinfo['co_argcount'],
                                'parent': kwargs['parent_smtbl'],
                                'cfg': kwargs['base_instance'],
                               },
                }
        
        if 'func_args' in kwargs:
            newkw['smtbl_args']['func_args'] = kwargs['func_args']

        shared_symtable = None
        for bb_id in bbs_orig:
            newkw['entry_bb'] = bb_id == 'entry'
            newkw['exit_bb'] = bb_id == 'exit'
            newkw['init_stack'] = bb_id == 'entry'
            if 'shared_symtable' in kwargs and shared_symtable is None:
                newkw['entry_bb'] = True
                cur_states  = InterpreterStates(**newkw)
                shared_symtable = cur_states.states['normal'].smtbl
                newkw['shared_symtable'] = shared_symtable
                module_symtables[getabspath(self.codeobj.co_filename)] = shared_symtable
            else:
                cur_states  = InterpreterStates(**newkw)

            self.bbs[bb_id] = bb(base_instance=bbs_orig[bb_id], states=cur_states)
        
#        print self.prefix, id(self.bbs['exit'])
        self.bbs_keys = sorted(self.bbs.keys())


setglobal('cfg_dict', {})
setglobal('call_table', {})
setglobal('call_stack', [])
setglobal('import_table', {})
setglobal('import_stack', [])
setglobal('module_symtables', {})
class MyModule(cfg_creator.MyModule):
    def __init__(self, *args, **kwargs):
        if 'base_instance' in kwargs:
            for attr in dir(kwargs['base_instance']):
                if not (attr.startswith('__') and attr.endswith('__')) and attr != 'cfg':
                    setattr(self, attr, getattr(kwargs['base_instance'], attr))
            cfg_orig = kwargs['base_instance'].cfg
        else:
            cfg_creator.MyModule.__init__(self, *args, **kwargs)
            cfg_orig = self.cfg

        self.cfg = {}
        if self.module_name not in cfg_orig: 
            raise Exception("Coudn't find module %r CFG!" % self.module_name)
        else:
            self.top = cfg(base_instance=cfg_orig[self.module_name],
                           parent_smtbl=RootSymTable, shared_symtable=True)

        self.cfg[self.module_name] = self.top
#        setglobal('smtbl', self.top.bbs[0].states.states['normal'].smtbl)
#        top_module._set_smtbl_stack(bb_first.states.states['normal'].smtbl, bb_first.states.states['normal'].stack)
#        for cfg_name in cfg_orig.keys():
#            self.cfg[cfg_name] = cfg(base_instance = cfg_orig[cfg_name])

setglobal('parent_code', {})
setglobal('code_modules', {})
setglobal('modules_cfg', {})
setglobal('modules_stack', [])
#import weakref
#setglobal('all_object', weakref.WeakValueDictionary())

def import_module(fname):
    cfg_module = CFGCreator.make_cfgs(fname)
    module = MyModule(base_instance=cfg_module)
    for name, cfg in cfg_module.cfg.items():
        parent_code[cfg.codeobj] = None
        cfg_dict[cfg.codeobj] = cfg
        code_modules[cfg.codeobj] = module
    modules_cfg[module.top.codeobj] = module.top
    return module

def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

#def _pickle_code(code):
#    func_name = code.im_func.__name__
#    obj = code.im_self
#    cls = code.im_class
#    return _unpickle_method, (func_name, obj, cls)
#
#import byteplay
#def _unpickle_code(func_name, obj, cls):
#    for cls in cls.mro():
#        try:
#            func = cls.__dict__[func_name]
#        except KeyError:
#            pass
#        else:
#            break
#    return func.__get__(obj, cls)

import copy_reg
import types
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)
#copy_reg.pickle(types.CodeType, _pickle_code, _unpickle_code)

import binascii
from copy import copy

_exp_name = 'buildbot'

class MegaStore(object):
    def __init__(self):
        self._cobjs = {}

    def add_one(self, cfgobj):
        if not getglobal('_use_megastore'):
            return

        name = cfgobj.prefix
        filename = cfgobj.codeobj.co_filename.rsplit('.', 1)[0].replace('/', '.')
        np = name.split('.')
        i = 0
        while i < len(np) and filename.find('.'.join(np[:i+1])) != -1:
            i += 1
        left = '.'.join(np[i:])

        fullname = '.'.join(filter(None, (filename, left)))

        fixed_name = fullname.split('%s.%s.' % (_exp_name, _exp_name), 1)[-1]
        name = fixed_name
#        name = fullname

        if name not in self._cobjs:
            print "NEW:", name
            self._cobjs[name] = cfgobj
        else:
            self._unite_cfgs(self._cobjs[name], cfgobj)

    def _unite_cfgs(self, one, another):
        name = one.prefix
        print "UNITING:", name


#    def cleanup_callable(self, tp):
#        if isinstance(tp, TypeCallable):
#            for b in ('cfgs', 'default_params', 'freevars'):
#                if hasattr(tp, b):
#                    setattr(tp, b, {})
#            print tp
#
#    def cleanup_obj(self, tp):
#        if isinstance(tp, TypeCallable):
#            for b in ('cfgs', 'default_params', 'freevars'):
#                if hasattr(tp, b):
#                    setattr(tp, b, {})
#            print tp

    def prepickle(self):
        from my_serialize import dict_to_set
        vars_res = {}
        for name, cfgobj in self._cobjs.items():
            cfg_res = {}
            for bb_id, bb in cfgobj.bbs.items():
                state = bb.states.states['normal']
                smtbl = state.smtbl
                bb_res = {}
                for vset_name in ('globals', 'locals', 'cell_free_vars'):
                    vset = getattr(smtbl, vset_name)
                    vset_dict = {}
                    for vname, v in vset.items():
                        vset_dict[vname] = dict_to_set(v._pickle())
                    bb_res[vset_name] = vset_dict

                bb_types = copy(bb_res['globals'])
                bb_types.update(bb_res['locals'])
                bb_types.update(bb_res['cell_free_vars'])
                cfg_res[bb_id] = {'borders': (bb.insts_list[0][0],
                                              bb.insts_list[-1][0]),
                                  'types': bb_types,
                                 }
#                cfg_res[bb_id] = bb_res
                cfg_res['__code_str'] = binascii.hexlify(cfgobj.code)
            vars_res[name] = cfg_res
#        pprint(vars_res)
        del self._cobjs
        self.vars = vars_res

    def compare_var(self, prefix, bb_id):
        if prefix in self.vars_res:
            cfg_res = self.vars_res


setglobal('_megastore', MegaStore())

