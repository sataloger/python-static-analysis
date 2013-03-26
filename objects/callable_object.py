# -*- coding: utf-8 -*-
from collections import deque
from copy import deepcopy
from opcode import opname
import os
from analyzer.objects.unknown_object import UnknownObject
from analyzer.py_run.functions import setglobal, getabspath
from analyzer.py_run.var_objects import create_empty
from analyzer.pytypes_run import cfg_wrapper

__author__ = 'sataloger'

class CallableObject(UnknownObject):
    implemented_type = 'CALLABLE'
    insts_handlers = deepcopy(UnknownObject.insts_handlers)
    is_generator = False

    def __init__(self):
        UnknownObject.__init__(self)
        self.cfgs = {}

    def create_from_const(self, code):
        self.cfgs = {code: cfg_dict[code]}

    def call(self, from_inst_num, func_args=None):
        setglobal('call_counter', call_counter+1)
        res = {"objects":create_empty()}
        prev_state = _state
        for code in self.cfgs:
            call_stack.append((code, from_inst_num))
            cfgobj = self._create_cfgobj(code, func_args)
            self.process_cfg(cfgobj)
            #                print call_stack
            self.store_call_result(cfgobj, *call_stack.pop())
            #                res["types"] |= cfgobj.bbs['exit'].states.states['normal'].stack.vars[-1]["types"]
            got_res = cfgobj.bbs['exit'].states.states['normal'].stack.vars[-1]
            res["types"] |= got_res["types"]
            if "aliases" in got_res.keys():
                res["aliases"] = got_res["aliases"]
            else:
                res["aliases"] = create_empty_alias(None,None)

            print cfgobj.bbs['exit'].states.states['normal'].stack
            _megastore.add_one(cfgobj)
            print cfgobj.prefix, cfgobj.bbs['exit'].states.states['normal']
            self._set_state(prev_state)
        setglobal('call_counter', call_counter-1)
        if self.is_generator:
        #            new_res = VarTypes(init_from={TypeGeneratorObject.implemented_types[0]: None})
            new_res = {"types":VarTypes(init_consts=[[]])}
            new_res["types"].types['TypeSuperList'].append(res)
            return new_res["types"].get_iter(None, TypeGeneratorObject)
        else:
            return res

    def _create_cfgobj(self, code, func_args=None):
#        from_cache = self._get_from_cache(code)
#        if from_cache is not None:
#            return from_cache

        cfg = cfg_dict[code]
        parent_smtbl = self._get_parent_smtbl(code, cfg)
        func_args = self._change_func_args(code, func_args)


        if func_args is not None:
            func_args['cfg'] = cfg
            func_args['default_params'] = self.default_params[code]
            cfgobj = cfg_wrapper.cfg(base_instance=cfg, parent_smtbl=parent_smtbl, func_args=func_args)
        else:
            cfgobj = cfg_wrapper.cfg(base_instance=cfg, parent_smtbl=parent_smtbl)
            # has to be smth like this to show analysis results
        code_modules[code].cfg[cfgobj.prefix] = cfgobj
        return cfgobj

    def _get_parent_smtbl(self, code, cfg):
        cfg = cfg_dict[code]
        prefix = cfg.prefix.rsplit('.', 1)
        mod_path = getabspath(cfg.codeobj.co_filename)
        mp_dotted = os.path.splitext(mod_path)[0].replace('/', '.')
        if len(prefix) == 2 and mp_dotted.endswith(prefix[0]):
            return module_symtables[mod_path]
        else:
            return smtbl

    def _change_func_args(self, code, func_args):
        return func_args

    def process_cfg(self, cfg):
        if not self.is_generator:
            edgesDeque = deque([('entry', bb, edgeNum)
            for edgeNum, bb in enumerate(cfg.bbs['entry'].next_bbs)])
        else:
            # FIXME: stub for generators
            edgesDeque = deque([('entry', bb, edgeNum)
            for edgeNum, bb in enumerate(cfg.bbs['entry'].next_bbs)
            if not edgeNum])

        # another hack for exceptions
        self.got_exception_insts = False
        specInfo = {}
        specInfo['except_end'] = cfg.except_end
        specInfo['finally_end'] = cfg.finally_end
        while len(edgesDeque):
            edge = edgesDeque.popleft()
            if self.skip_end_finally(cfg, edge):
                continue
            parent_id, child_id, specInfo['edgeNum'] = edge
            parent = cfg.bbs[parent_id]

            child = cfg.bbs[child_id]

            #            if mydebugDict['useAnotherSearch']:
            #                edgesSet.remove(maxVertCount*parent_id+child_id)
            if mydebugDict['printInstr']:
                print (parent_id, child_id, edgeNum)
                # т.к. номер блока совпадает с номером его первой иструкции
            specInfo['nextAtJumpAddrs'] = parent.next_bbs
            specInfo['borders'] = cfg.codeinfo['blockBorders']
            specInfo['nextIsExit'] = child_id == 'exit'

            if parent_id != 'entry':

                oldstates = deepcopy(parent.states)
                self._set_state(parent.states.states['normal'])
                self.transform_bb(parent, specInfo)

            if self.got_exception_insts:
                child_id = 'exit'
                child = cfg.bbs[child_id]

            if child_id == 'exit':
                self.adjust_to_return_state()
            if not child.states.is_stacks_inited_as_parent(parent.states):
                child.states.init_stack_from(parent.states)
                lge = (0, 0, 0)
            else:
                lge = parent.states.lge(child.states)
            if not (lge[0] or lge[2]):
                child.states |= parent.states

                if mydebugDict['printInstrVarsAfterBlock']:
                    print 'INFO_CHANGED'
                for edgecnt, bb_id in enumerate(child.next_bbs):
                    if mydebugDict['useAnotherSearch']:
                        if maxVertCount*child_id+bb_id not in edgesSet:
                            edgesDeque.appendleft((child_id, bb_id,edgecnt))
                            edgesSet.add(maxVertCount*child_id+bb_id)
                    else:
                        edgesDeque.appendleft((child_id, bb_id, edgecnt))
            if parent_id != 'entry':
                parent.transformed_states = parent.states
                parent.states = oldstates

            if self.got_exception_insts:
                return

    def skip_end_finally(self, cfg, edge):
        bbp = cfg.bbs[edge[0]]
        bbc = cfg.bbs[edge[1]]
        inst = bbp.insts[max(bbp.insts)]
        next_insts = bbp.next_bbs
        if opname[inst[0]] != 'END_FINALLY' or len(next_insts) != 2:
            return False
            # skipping raising edges
        if edge[2]:
            return True

    def adjust_to_return_state(self):
        del stack.vars[:-1]