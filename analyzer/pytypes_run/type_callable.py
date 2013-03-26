# -*- coding: utf-8 -*-

from collections import deque
from itertools import *
from opcode import opname
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_classes import TypeGeneratorObject
#from pytypes_run.type_list import TypeSuperList
from pytypes_run.type_unknown import ParentType
from pytypes_run.type_baseobject import TypeBaseObject
from analyzer.pytypes_run.base_classes import getmodulename, getabspath, setglobal
import cfg_wrapper
import os, sys


from copy import deepcopy
#dirty hacks:
import copy
import types

def _deepcopy_method(x, memo):
   return type(x)(x.im_func, deepcopy(x.im_self, memo), x.im_class)
copy._deepcopy_dispatch[types.MethodType] = _deepcopy_method
#end of hacks

from copy import copy


class TypeCallable(ParentType):
    implemented_types = ('CALLABLE',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts
    is_generator = False

    def __init__(self):
        ParentType.__init__(self)
        self.cfgs = {}

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.cfgs = copy(self.cfgs)
        return res

    def _repr_inner(self):
        return '%s(' % self.clsname + \
                ', '.join(map(str, self.cfgs.keys())) + ')'

    def _pretty_inner(self):
        return '%s(' % self.implemented_types[0] + \
                ', '.join(map(str, self.cfgs.keys())) + ')'

    def _lge_inner(self, other):
        sc = set(self.cfgs.keys())
        oc = set(other.cfgs.keys())
        less = int(sc <= oc)
        greater = int(sc >= oc)
        equal = int(sc == oc)
        return (less, greater, equal)

    def __nonzero__(self):
        return True

    def _list_names(self):
        return self.implemented_types

    def create_from(self, other):
        self.cfgs = other.cfgs

    # !!FIXME: replaces result at module when using one codeobj at least twice
    def create_from_const(self, code):
        self.cfgs = {code: cfg_dict[code]}

    def _get_from_cache(self, code):
        if code in modules_cfg:
            return modules_cfg[code]
        return None

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

    def _create_cfgobj(self, code, func_args=None):
        from_cache = self._get_from_cache(code)
        if from_cache is not None:
            return from_cache

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

    def init_callable(self, curSt):
        raise NotImplementedError('%s.init_callable' % self.clsname)

    def add_const(self, const):
        if const is None:
            return
        raise NotImplementedError('%s.add_const' % self.clsname)

#    def __ior__(self, other):
#        self.cfgs.update(other.cfgs)

    def add_type(self, other):
        self.cfgs.update(other.cfgs)

    @staticmethod
    def _set_state(state):
        setglobal('stack', state.stack)
        setglobal('smtbl', state.smtbl)
        setglobal('_aso', state._aso)
        setglobal('_state', state)

#    @staticmethod
#    def _set_smtbl_stack(smtbl, stack):
#        setglobal('stack', stack)
#        setglobal('smtbl', smtbl)

    #dirty hack for exceptions
    def adjust_to_return_state(self):
        del stack.vars[:-1]

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
#        if not edge[2] and not 'normal' in bbp.states.states:
#            return True
#        elif edge[2] and not 'raised' in bbp.states.states:
#            return True

    def handle_inst(self, inst_name, *args, **kwargs):
        newkw = copy(kwargs)
        if 'interp' in newkw:
            del newkw['interp']
            count = get_pop_count(kwargs['inst'])
            stack.pop_count(count)
            # BARMEN if inst_name != 'FOR_ITER' and (inst_name in VAR_INSTS or \
            #     inst_name in stack.implemented_insts or inst_name in smtbl.implemented_insts):
            if(inst_name in VAR_INSTS or inst_name in stack.implemented_insts or inst_name in smtbl.implemented_insts):
                return self.handle_inst_rd(inst_name, *args, **newkw)
            elif inst_name in self.implemented_insts:
                newkw['self_obj'] = self
                return self.insts_handler.handle(inst_name, *args, **newkw)
            else:
                print call_stack
                print _state
                raise NotImplementedError("%s doesn't implement instruction %r" % \
                         (self.__class__.__name__, inst_name))
        else:
            newkw['self_obj'] = self
            return self.insts_handler.handle(inst_name, *args, **newkw)


    def handle_inst_rd(self, inst_name, *args, **kwargs):
        res = None
        newkw = copy(kwargs)
        for rd_instance in (stack, smtbl):
            if rd_instance.implement_inst(inst_name):
                newkw['self_obj'] = rd_instance
#                print "Handling inst via %r" % rd_instance.__class__.__name__
                res = rd_instance.handle_inst(inst_name, *args, **newkw)
                break
        else:
            if inst_name in VAR_INSTS:
                reordered = reorder(kwargs['inst'], stack.vars_dlt)
                if inst_name == 'COMPARE_OP':
                  newkw['type_of_cmp'] = kwargs['inst'][2]
                res = {}
                print "REORDERED", reordered
                newkw['self_obj'] = reordered[0]
                newkw['vars'] = reordered[1:]
#                print "handling inst via %r" % reordered[0]["types"].__class__.__name__
                res = reordered[0]["types"].handle_inst(inst_name, **newkw)
                #BARMEN
                vals = tuple(list( x['values'] for x in reordered[1:]))
                temp = reordered[0]['values'].handle_inst(inst_name, vals=vals, **newkw)
                if type(temp).__name__ != 'NoneType':
                    res['values'] = temp['values']
                else:
                    res['values'] = create_unknown_value()
            else:
                raise NotImplementedError("%s doesn't implement instruction %r" % \
                     (self.__class__.__name__, inst_name))

        if res is None:
#            #print"Warning: got None result while processing %r: " % inst_name
            res = {"types": None, "values": create_empty_value()}

        if inst_name not in INSTS_NO_PUSH:
            print inst_name, "will be pushed"
            pres = res
            if isinstance(res["types"], VarTypes):
                stack.push_var(res)
            elif isinstance(res["types"], list):
                for rv in res["types"]:
                    pres = res
                    pres["types"] = rv
                    stack.push_var(pres)
            elif res is not None:
                print res
                print "Warning: got to place after %r: %r" % (inst_name, res)
                return
                raise Exception("Warning: got to place after %r: %r" % (inst_name, res))
                stack.push_var(res)
            else:
                raise Exception("Warning: got to place 'None' after %r: %r" % (inst_name, res))
#                print "Warning: got to place 'None' after %r!" % inst_name

    def transform_bb(self, bb, specInfo):
#        print "BEFORE %r: %r\n%r" % (bb.id,  smtbl, stack)
        for instCounter, inst in enumerate(bb.insts_list):
            # print "BEFORE %r: %r\n%r" % (bb.id,  smtbl, stack)
            print "%03d %s %r" % (inst[0], opname[inst[1]], inst[2])
           # try:
            res = self.handle_inst(opname[inst[1]], inst=inst, specInfo=specInfo, interp=True)
            if res != None: 
              _state._cleanup_aso()
              return {opname[inst[1]]:res}
            #except Exception, e:
             #   print "ERROR: catched exception %r" % e
             #   print "State %r: %r\n%r" %  (bb.id, smtbl, stack)
             #   self.handle_inst('RAISE_VARARGS', inst=inst, specInfo=specInfo, interp=True)

#            if (inst[0] in (13,16,19)) and (opname[inst[1]] in ('RETURN_VALUE','BINARY_ADD')):
#            if opname[inst[1]] in ('RETURN_VALUE','BINARY_ADD'):
#            print "AFTER %r: %r\n%r" %  (bb.id, smtbl, stack)
            # print('\n aso after\n', bb.states.states['normal']._aso)   
        _state._cleanup_aso()
#        print "AFTER %r: %r\n%r" %  (bb.id, smtbl, stack)

    def process_cfg(self, cfg):

        print cfg
        appended = set()
# !FIXME
#        visited = set()
#        to_visit = deque(['entry'])
#        edgesList = []
#        changed = True
#        while to_visit:
#            bb_id = to_visit.popleft()
#            to_visit.extend(set(cfg.bbs[bb_id].next_bbs)-visited)
#            visited.update(cfg.bbs[bb_id].next_bbs)
#            edgesList.extend([(bb_id, bb, edgeNum)
#                 for edgeNum, bb in enumerate(cfg.bbs[bb_id].next_bbs)])
#        edgesDeque = deque(edgesList)
# !FIXME - previous until here
        if not self.is_generator:
            edgesDeque = deque([('entry', bb, edgeNum)
                 for edgeNum, bb in enumerate(cfg.bbs['entry'].next_bbs)])
        else:
            # FIXME: stub for generators
            edgesDeque = deque([('entry', bb, edgeNum)
                 for edgeNum, bb in enumerate(cfg.bbs['entry'].next_bbs)
                 if not edgeNum])

#        if mydebugDict['useAnotherSearch']:
#            edgesSet = set()
#            maxVertCount = len(cfg.bbs_keys)
#            for edge in edgesList:
#                edge = list(edge)
#                if edge[0] == 'entry':
#                    edge[0] = -1
#                if edge[1] == 'exit':
#                    edge[1] = maxVertCount
#                edgesSet.add(maxVertCount*edge[0]+edge[1])

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
            specInfo['nextAtJumpAddrs'] = parent.next_bbs

            res =  None
            if parent_id != 'entry':

                oldstates = deepcopy(parent.states)
                self._set_state(parent.states.states['normal'])
                res = self.transform_bb(parent, specInfo)
                print res

            if res is not None:
              #print"FOR_TEST"
              if ('JUMP_FORWARD' in res.keys() or 'JUMP_ABSOLUTE' in res.keys() or 'CONTINUE_LOOP' in res.keys()):
                child_id = specInfo['nextAtJumpAddrs'][0]
              elif ('JUMP_IF_TRUE' in res.keys()):
                pass
              elif ('JUMP_IF_FALSE' in res.keys()):
                #print"JIFJIF", res['JUMP_IF_FALSE']
                if (res['JUMP_IF_FALSE']['values'].unknown_value ):
                  pass
                elif (res['JUMP_IF_FALSE']["values"].values[0] == True):
                  child_id = min(specInfo['nextAtJumpAddrs'])
                else:
                  child_id = max(specInfo['nextAtJumpAddrs'])
              elif ('FOR_ITER' in res.keys()):
                if (res['FOR_ITER']["values"].values[0]==True):
                  child_id = max(specInfo['nextAtJumpAddrs'])
                else:
                  child_id = min(specInfo['nextAtJumpAddrs'])
              else:
                pass
              child = cfg.bbs[child_id]
                ###TEST HERE
              state_ch = child.states.states['normal']
              #print"CHILD_STACK", state_ch.stack
              if (state_ch.inited and state_ch.stack_inited):
                  #print"CHILD_STACK", state_ch.stack
                  #print"FIRST"
                  if (len(state_ch.stack.vars) > 0): 
                    #print"SECOND"
                    if (state_ch.stack.vars[-1]["values"].iterator is not None):
                      #print"THIRD"
                      if (len(state_ch.stack.vars[-1]["values"].iterator) > 1): 
                        #print"CUT"
                        state_ch.stack.vars[-1]['values'].iterator = state_ch.stack.vars[-1]['values'].iterator[1:]
                      else:
                        #print"KILL"
                        state_ch.stack.vars[-1]['values'].iterator = None
            #print"1======", edgesDeque, "======"

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
#                if cfg.prefix.find('ff') != -1:
#                    print '>>>>>>>> %r' % child_id
#                    print edgesDeque
#                    print lge
#                    print cfg.bbs[child_id].states
#                    print "<<<<<<<< %r" % parent_id
#                    print cfg.bbs[parent_id].states
#                    print "========"

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
            #else:
                #for edgecnt, bb_id in enumerate(cfg.bbs[child].next_bbs):
                    #edgesDeque.appendleft((child, bb_id, edgecnt))

    def store_call_result(self, cfgobj, code, inst_num):
        call_table[(code, inst_num)] = cfgobj.bbs['exit'].states.states['normal'].stack.vars[-1]

    def call(self, analysis_type, from_inst_num, func_args=None):
        setglobal('call_counter', call_counter+1)
        res = {"types":create_empty( 'types' ), 'values':create_empty_value()}
        prev_state = _state
        for code in self.cfgs:
#            if (code, from_inst_num) in call_table:
#                res |= call_table[(code, from_inst_num)]
##                print "FUNCTIONS CACHE HIT: %r %r!" % (code, from_inst_num)
#            else:
                call_stack.append((code, from_inst_num))
                cfgobj = self._create_cfgobj(code, func_args)     
                self.process_cfg(cfgobj)
#                print call_stack
                print "============================================================"
                print cfgobj.bbs['exit'].states.states['normal']
                print "============================================================"
                #self.store_call_result(cfgobj, *call_stack.pop())
                if cfgobj.bbs['exit'].states.states['normal'].stack is not None:
                    temp = cfgobj.bbs['exit'].states.states['normal'].stack.vars[-1]
                    res["types"] |= temp["types"]
                    res["values"] |= temp["values"]
                    print "TYPE", temp["values"].type_of_analysis
                    if "aliases" in temp.keys():
                      res["aliases"] = temp["aliases"]
                    else:
                      res["aliases"] = create_empty_alias(None,None)

                #res["types"] |= cfgobj.bbs['exit'].states.states['normal'].stack.vars[-1]["types"]
                #got_res = cfgobj.bbs['exit'].states.states['normal'].stack.vars[-1]
                #res["types"] |= got_res["types"]
                #if "aliases" in got_res.keys():
                #    res["aliases"] = got_res["aliases"]
                #else:
                #    res["aliases"] = create_empty_alias(None,None)

                print cfgobj.bbs['exit'].states.states['normal'].stack
                _megastore.add_one(cfgobj)
                #print cfgobj.prefix, cfgobj.bbs['exit'].states.states['normal']
                self._set_state(prev_state)
        setglobal('call_counter', call_counter-1)
        if self.is_generator:
#            new_res = VarTypes(init_from={TypeGeneratorObject.implemented_types[0]: None})
            new_res = {"types":VarTypes(init_consts=[[]]),'values':create_unknown_value()}
            new_res["types"].types['TypeSuperList'].append(res)
            return new_res["types"].get_iter(None, TypeGeneratorObject)
        else:
            return res


    def call_func(self, inst, specInfo, no_push=False):
        count = ((inst[2] & 0xff00) >> 8)*2 + (inst[2] & 0xff) + 1
    #CALL_FUNCTION(argc)¶
        #Calls a function. The low byte of argc indicates the number of positional parameters, the high byte the number of keyword parameters. On the stack, the opcode finds the keyword parameters first. For each keyword argument, the value is on top of the key. Below the keyword parameters, the positional parameters are on the stack, with the right-most parameter on top. Below the parameters, the function object to call is on the stack. Pops all function arguments, and the function itself off the stack, and pushes the return value.
        if opname[inst[1]] in ('CALL_FUNCTION_VAR', 'CALL_FUNCTION_KW'):
            additional_count = 1
        elif opname[inst[1]] == 'CALL_FUNCTION_VAR_KW':
            additional_count = 2
        else:
            additional_count = 0

#        if not specInfo['edgeNum']:
        stack.pop_count(count + additional_count)
        cobj = stack.vars_dlt[0]
        func_args = {'params': stack.vars_dlt[1:count]}

#        from pprint import pprint
#        print "func_args"
#        pprint(func_args)

        if opname[inst[1]] == 'CALL_FUNCTION_VAR':
            func_args['args'] = stack.vars_dlt[-1]
        elif opname[inst[1]] == 'CALL_FUNCTION_KW':
            func_args['kwargs'] = stack.vars_dlt[-1]
        elif opname[inst[1]] == 'CALL_FUNCTION_VAR_KW':
            func_args['args'] = stack.vars_dlt[-2]
            func_args['kwargs'] = stack.vars_dlt[-1]

#        print "CALLING %r from object %r inst %r" % (cobj, self, inst)

        res = TypeCallable.call_object(cobj, inst[0], func_args)
        if no_push:
            return res
        else:
            stack.push_var(res)

#        else:
#            stack.pop_block_raising()
#            self.states.raise_exception()


    @staticmethod
    def call_object(cobj, from_inst_num, func_args):
        if call_counter > 100:
#            #print"Recursion limit(100) reached at calling %r from %r!" % (cobj, self)
            #print"Recursion limit(100) reached at calling %r!" % cobj
            res = {"types":create_unknown("types"), 'values':create_unknown_value()}
        else:
            res = {"types":create_empty("types"), 'values':create_empty_value()}
            # process every callable type
            for cname in VarTypes.callable_wo_unknown:
                print "CNAME", cname
                if cname in cobj["types"].types:
                    print "CNAME CALL"
                    try:
                        #print cobj["types"].types[cname].call(inst[0], func_args)
                        #res["types"] |= cobj["types"].types[cname].call(inst[0], func_args)["types"]
                        #got_res = cobj["types"].types[cname].call(inst[0], func_args)
                        #res["types"] |= got_res["types"]

                        temp = cobj["types"].types[cname].call("types",inst[0], func_args)
#       #printcobj
                        print "============================================"
                        res["values"] |= temp["values"]
                        print "============================================"
                        res["types"] |= temp["types"]
#                        print res
                        if "aliases" in temp.keys():
                            res["aliases"] = temp["aliases"]
                        else:
                            res["aliases"] = create_empty_alias(None,None)

                    except RuntimeError, e:
                        if isinstance(e, NotImplementedError):
                            print call_stack
                            print _state
                            raise
                        print "Got %r" % e 
                        exit()

            # if found not callable type - add TypeUnknown
            for tname in cobj["types"].types:
                if tname not in VarTypes.callable_wo_unknown:
                    #print"Warning: trying to call variable %r" % cobj.types
                    res["types"] |= create_unknown( "types" )
                    res['values'] |= create_unknown_value()
                    break
        return res

    insts_handler.add_set(InstSet(['CALL_FUNCTION', 'CALL_FUNCTION_VAR',
         'CALL_FUNCTION_KW', 'CALL_FUNCTION_VAR_KW'], call_func))

    def break_loop(self, inst):
        for state in self.states.states.values():
            if state.inited and state.stack_inited:
                state.stack.handle_inst(opname[inst[1]], inst=inst)

    def for_iter(self, inst, specInfo):

      if specInfo['edgeNum']:
        stack.pop_top()
      else:
#      for state in  _state.states.values():
        if _state.inited and _state.stack_inited:
            res_f = {"values":create_empty_value()} 
            res_f["values"].unknown_value = False
            top_val = stack.vars[-1]
            #print"MAINITER", top_val["values"].iterator
            if (top_val["values"].iterator is None):
              #print"FOR_TRUE"
              res_f["values"].add_value(1)
              return res_f
            else:
              res = {"values":create_empty_value()}
              res["values"].unknown_value = False
              res["values"].other_values.append(top_val["values"].iterator[0])
              res["values"].iterator = top_val["values"].iterator[1:]
              res["types" ] = top_val["types"]
              stack.pop_top()
              stack.push_var(res)
#res["types"] = top_val["types"].handle_inst(inst=inst, inst_name=opname[inst[1]], vars=())["types"]
              #print"FOR_FALSE"
              res_f["values"].add_value(0)
              return res_f

      '''
      if specInfo['edgeNum']:
            stack.pop_top()
      else:
            top_var = stack.vars[-1]
            #printopname[inst[1]]
            stack.push_var(top_var["types"].handle_inst(inst=inst, inst_name=opname[inst[1]], vars=()))
      '''  
    def return_value(self, inst, specInfo):
        pass

    def yield_value(self, inst, specInfo):
        pass

    def with_cleanup(self, inst, specInfo):
        stack.pop_top()
        top_var = stack.vars_dlt[0]
        func_args = (None, None, None)
        TypeCallable.call_object(top_var, inst[0], func_args)

    def raise_varargs(self, inst, specInfo):
        if not self.states.is_raised():
            if self.states['normal'].stack_inited:
                vars = self.states['normal'].stack.pop_count(inst[2])
                self.states['normal'].stack.pop_block_raising()
        elif len(self.states.states) == 1:
            if self.states['normal'].stack_inited:
                vars = self.states['raised'].stack.pop_count(inst[2])
                self.states['raised'].stack.pop_block_raising()
        else:
            #если у нас почему-то при возбуждении исключения
            #2 состояния - то информацию от них необходимо объединить
            vars = []
            for state in self.states.states.values():
                if state.stack_inited:
                    vars.append(state.stack.pop_count(inst[2]))
                    state.stack.pop_block_raising()
            if len(vars) == 2:
                vars = map(lambda x,y: x|y, *vars)
            elif vars:
                vars = vars[0]
        self.states.raise_exception(vars)

#    def end_finally(self, inst, specInfo):
#        if inst[0] in specInfo['except_end'] or \
#           specInfo['edgeNum']: # перевозбуждение исключения
#            if self.states.is_raised():
#                state = self.states['raised']
#                if state.inited and state.stack_inited:
#                    vars = state.stack.pop_count(3)
#                    state.stack.pop_block_raising()
#                    state.stack.extend_vars(vars)
#            else:
#                raise Exception('Error at interpreting END_FINALLY')
#        else: # исключение уже было погашено
#            if self.states['normal'].inited and self.states['normal'].stack_inited:
#                self.states['normal'].stack.pop_count(3)

    def end_finally(self, inst, specInfo):
        pass
#        if inst[0] in specInfo['except_end'] or \
#           specInfo['edgeNum']: # перевозбуждение исключения
#            if self.states.is_raised():
#                state = self.states['raised']
#                if state.inited and state.stack_inited:
#                    vars = state.stack.pop_count(3)
#                    state.stack.pop_block_raising()
#                    state.stack.extend_vars(vars)
#            else:
#                raise Exception('Error at interpreting END_FINALLY')
#        else: # исключение уже было погашено
#            if self.states['normal'].inited and self.states['normal'].stack_inited:
#                self.states['normal'].stack.pop_count(3)

    def pop_block(self, inst):
        stack.pop_block()
#        tos = {}
#        for key, state in self.states.states.items():
#            if state.inited and state.stack_inited:
#                tos[key] = state.stack.pop_block()
#        if self.states.is_raised() and tos['raised']['type'] == 'FINALLY':
#            if self.states['raised'].inited and self.states['raised'].stack_inited:
#                self.states.disable_exception()
#                self.states['normal'].stack.push_var_unknown()
#                self.states['normal'].stack.push_var_unknown()
#        elif 'normal' in tos and tos['normal']['type'] == 'FINALLY':
#            if self.states['normal'].inited and self.states['normal'].stack_inited:
#                self.states['normal'].stack.push_var_unknown()
#                self.states['normal'].stack.push_var_unknown()


    def exec_stmt(self, inst):
#        for state in self.states.states.values():
#            if state.inited and state.stack_inited:
#                states.stack.pop_count(3)
        if _state.inited and _state.stack_inited:
            stack.pop_count(3)

    def cfg_error(self, inst):
        print "Instruction (%r %r %r) shouldn't be after CFG creation"%\
                (inst[0], opname[inst[1]], inst[2])

    def print_insts(self, inst):
        pass

    def exceptions_stub(self, inst, specInfo):
        self.got_exception_insts = True
        stack.push_var_unknown()

    def pop_jump_if(self, inst, specInfo):
        stack.pop_top()

    def jump_if_or_pop(self, inst, specInfo):
        if specInfo['edgeNum']:
            pass
        else:
            stack.pop_top()

    def jump_absolute(self, inst, specInfo):
        return True

    def jump_if_true(self, inst, specInfo):
        pass

    def jump_if_false(self, inst, specInfo):
      res = {"values" : create_empty_value()}
      for stack_val in list( x['values'] for x in _state.stack.vars ):
        if (stack_val.unknown_value):
          return {"values":create_unknown_value()} # Означает, что надо проверять обе ветви
        for val in stack_val.values:
          res["values"].add_value(val)
      if (0 in res["values"].values and len(res["values"].values) == 1): 
        res["values"].unknown_value = False
        return res
      elif (0 not in res["values"].values and len(res["values"].values) > 0): 
        res["values"].unknown_value = False
        return res
      else:
        return {"values":create_unknown_value()}


    insts_handler.add_set(InstSet(['BREAK_LOOP'], break_loop))
    insts_handler.add_set(InstSet(['FOR_ITER'], for_iter))
#    insts_handler.add_set(InstSet(['RAISE_VARARGS'], raise_varargs))
    insts_handler.add_set(InstSet(['RAISE_VARARGS'], exceptions_stub))
    insts_handler.add_set(InstSet(['END_FINALLY'], end_finally))
    insts_handler.add_set(InstSet(['POP_BLOCK'], pop_block))
    insts_handler.add_set(InstSet(['RETURN_VALUE'], return_value))
    insts_handler.add_set(InstSet(['YIELD_VALUE'], yield_value))
    insts_handler.add_set(InstSet(['EXEC_STMT'], exec_stmt))

    insts_handler.add_set(InstSet(['WITH_CLEANUP'], with_cleanup)) # let's have some extra problems :)

    insts_handler.add_set(InstSet(['JUMP_FORWARD', 'JUMP_ABSOLUTE', 'CONTINUE_LOOP'], jump_absolute))

    if sys.version_info < (2, 7):
      insts_handler.add_set(InstSet(['JUMP_IF_TRUE'], jump_if_true))
      insts_handler.add_set(InstSet(['JUMP_IF_FALSE'], jump_if_false))

    else:
        insts_handler.add_set(InstSet(['POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE'],
                                       pop_jump_if))
        insts_handler.add_set(InstSet(['JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'],
                                       jump_if_or_pop))

    insts_handler.add_set(InstSet(['PRINT_EXPR', 'PRINT_ITEM',
           'PRINT_NEWLINE', 'PRINT_ITEM_TO', 'PRINT_NEWLINE_TO'], print_insts))

    insts_handler.add_set(InstSet(['STOP_CODE', 'NOP', 'EXTENDED_ARG'], cfg_error))

setglobal('TypeCallable', TypeCallable)

class TypeModule(TypeCallable, TypeBaseObject):
    implemented_types = ('module',)
    insts_handler = deepcopy(TypeCallable.insts_handler)
    insts_handler.update(TypeBaseObject.insts_handler)
    implemented_insts = insts_handler.stored_insts
#    print implemented_insts

    import ihooks
    il = ihooks.ModuleLoader()
#    if getglobal('include_path'):
#        il.default_path().append(include_path)

    def __init__(self, module=None, name=None, path=None):
        TypeCallable.__init__(self)
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

    def add_const(self, const):
        # FIXME: should fix this method
#        self.names.append(const.__name__)
        if '__file__' in dir(const):
            self.names[const.__name__] = const.__file__
        else:
            self.names[const.__name__] = ''
        self.last_name = const.__name__
        self.module = const
        self.attrs.clear()
#        print self.names
#        raise Exception(repr(self.names))

    def add_type(self, other):
#        print "ADDING TYPE TO MODULE: %r" % other
        if other.names:
            # FIXME: quick hack for modules
            if self.module is not None and (set(other.names) <= set(self.names)):
                return
            self.names.update(other.names)
            self.last_name = other.last_name
            self.module = other.module
            self._set_attrs()

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

    def call(self, analysis_type, *args, **kwargs):
        if self.module is not None:
            modules_stack.append(self)
            super(TypeModule, self).call( "types", *args, **kwargs)
    #        #printmodules_stack
            modules_stack.pop()


    @staticmethod
    def from_code(path):
        path = getabspath(path)
        module_name = getmodulename(path)
        res = TypeModule(cfg_wrapper.import_module(path), module_name, path)
        prev_state = _state

        TypeCallable._set_state(RootState)
        res.call("types",0)
        res._set_attrs()
        TypeCallable._set_state(prev_state)
        import_table[path] = res
        return res

    @staticmethod
    def module_in_stack(path):
        for m in modules_stack:
            if path in m.names.values():
                return True
        return False

    @staticmethod
    def import_from_path(full_path, is_package=False):
#        print "\n\n\nNOTE: %r\n\n\n" % full_path
        name = getmodulename(full_path)
        if full_path in import_table:
#            print "IMPORTING CACHE %r: %r" % (name, full_path)
            res = import_table[full_path]
        else:
#            print "IMPORTING NEW %r: %r" % (name, full_path)
            if TypeModule.module_in_stack(full_path):
#                #print"GOT IT IN IMPORTED_STACK"
                return {"types":create_unknown( "types" ), "values": create_empty_value() }
            if is_package:
                res = TypePackage.from_code(full_path)
            else:
                res = TypeModule.from_code(full_path)

        res_vtype = {"types":create_empty( "types" ), "values" : create_empty_value()}
        res_vtype["types"].add_typeobj(res)
        return res_vtype

    @staticmethod
    def import_by_name(name, parent_path):
        minfo = TypeModule.find_module(name, parent_path)
        if minfo is None:
#            #printname, parent_path
            return {"types":create_unknown( "types" ), "values":create_unknown_value()}
        elif (minfo[1].find('/usr/') != -1) or (minfo[1] == ''):
            # stub for system modules or some libs
            return {"types":create_unknown( "types" ), "values":create_unknown_value()}

        full_path = getabspath(minfo[1])
        if minfo[0] is not None:
            minfo[0].close()
        return TypeModule.import_from_path(full_path, minfo[0] is None)

    @staticmethod
    def import_by_name_from_dir(name, parent_path):
        minfo = TypeModule.find_module_in_dir(name, parent_path)
        if minfo is None:
#            #printname, parent_path
            return {"types":create_unknown( "types" ), "values":create_unknown_value()}
        elif (minfo[1].find('/usr/') != -1) or (minfo[1] == ''):
            # stub for system modules or some libs
            return {"types":create_unknown( "types" ), "values":create_unknown_value()}

        full_path = getabspath(minfo[1])
        if minfo[0] is not None:
            minfo[0].close()
        return TypeModule.import_from_path(full_path, minfo[0] is None)

    @staticmethod
    def find_module(name, parent_dir):
        TypeModule.il.default_path().append(parent_dir)
        res = TypeModule.il.find_module(name.replace('.', '/'))
        del TypeModule.il.default_path()[-1]
        return res

    @staticmethod
    def find_module_in_dir(name, parent_dir):
        return TypeModule.il.find_module_in_dir(name.replace('.', '/'), parent_dir)

    def _repr_inner(self):
        return '%s([' % self.clsname + '; '.join(map(lambda x: '%s: %s' % (x[0], x[1]), self.names.items())) + '])'

    def _pretty_inner(self):
        return 'module(' + ', '.join(self.names.values()) + ')'

setglobal('TypeModule', TypeModule)

class TypePackage(TypeModule):
    implemented_types = ('module',)
    insts_handler = deepcopy(TypeModule.insts_handler)
    implemented_insts = insts_handler.stored_insts

#    def __init__(self, name=None, path=None, module=None):
#        TypeCallable.__init__(self)
#        self.cfgs = {}
#        if name is not None:
#            self.names = {name: path}
#            self.last_name = name
#            self.module = module
#        else:
#            self.names = {}
#            self.last_name = ''
#            self.module = None
#
#    def __deepcopy__(self, memo):
#        res = self.__class__()
#        res.names = copy(self.names)
#        res.last_name = self.last_name
#        res.module = self.module
#        return res
#
#    def add_const(self, const):
#        # FIXME: should fix this method
#        if '__file__' in dir(const):
#            self.names[const.__name__] = const.__file__
#        else:
#            self.names[const.__name__] = ''
#        self.last_name = const.__name__
#        res.module = const
#
#    def add_type(self, other):
##        print "ADDING TYPE TO PACKAGE: %r" % other
#        if other.names:
#            self.names.update(other.names)
#            self.last_name = other.last_name
#            self.module = other.module
#
#    def call(self, *args, **kwargs):
#        print "Warning: trying to call package %r" % self
#        pass

    @staticmethod
    def from_code(path):
        path = getabspath(path)
        module_name = getmodulename(path)
        init_path = os.path.join(path, '__init__.py')
#        print "IMPORTING PACKAGE %r" % path
        if os.path.exists(init_path):
#            print "FOUND INIT %r" % init_path
            module_name = getmodulename(init_path)
            res = TypePackage(cfg_wrapper.import_module(init_path), module_name, path)
            prev_state = _state
            TypeCallable._set_state(RootState)
            res.call("types",0)
            res._set_attrs()
            TypeCallable._set_state(prev_state)
        else:
            res = TypePackage(None, module_name, path)
        import_table[path] = res
        return res

    def load_attr(self, inst):
        attrname = smtbl.get_varname_by_id(inst[2])
#        if attrname == 'NS_BYTESTREAM':
#            print self
#            print self.attrs
#            print self.names
#            print self.module
#            exit(0)
        if attrname in self.attrs:
            return self.attrs[attrname]
        else:
            return TypeModule.import_by_name_from_dir(attrname, self.names[self.last_name])
#            path = os.path.join(self.names[self.last_name], '%s.py' % attrname)
#            print 'FROM %r LOADING MODULE: %r' % (self, path)
#            res = TypeModule.import_from_path(path)
#            res_vtype = create_empty()
#            res_vtype.add_typeobj(res)
#            return res_vtype

    def _pretty_inner(self):
        return 'package(' + ', '.join(self.names.values()) + ')'

    insts_handler.add_set(InstSet(['LOAD_ATTR'], load_attr))

setglobal('TypePackage', TypePackage)
_unknown_package = TypePackage()
setglobal('_unknown_package', _unknown_package)

class TypeFunction(TypeCallable):
    implemented_types = ('function',)
    insts_handler = deepcopy(TypeCallable.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, code=None, default_params_one=None, freevars_one=None):
        TypeCallable.__init__(self)
        if code is not None:
            self.init_callable(code, default_params_one, freevars_one)
        else:
            self.default_params = {}
            self.freevars = {}

    def init_from(self, other):
        self.cfgs = other.cfgs
        self.default_params = other.default_params
        self.freevars = other.freevars

    def __deepcopy__(self, memo):
        res = TypeCallable.__deepcopy__(self, memo)
        res.default_params = copy(self.default_params)
        res.freevars = copy(self.freevars)
        return res

    def add_type(self, other):
        TypeCallable.add_type(self, other)
        self.default_params.update(other.default_params)
        self.freevars.update(other.freevars)

    def init_callable(self, code, default_params_one, freevars_one):
        if 'TypeCode' not in code.types:
            raise Exception('Got %r as code at creation function' % code)
        realcode = code.types['TypeCode'].code
        self.create_from_const(realcode)
        self.default_params = {realcode: default_params_one}
        self.freevars = {realcode: freevars_one}


class TypeGenerator(TypeFunction):
    implemented_types = ('generator',)
    insts_handler = deepcopy(TypeFunction.insts_handler)
    implemented_insts = insts_handler.stored_insts
    is_generator = True


class TypeBuiltinFunction(TypeCallable):
    implemented_types = ('builtin_function_or_method',)
    insts_handler = deepcopy(TypeCallable.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, name=None, res_type=None):
        ParentType.__init__(self)
#        self.bf_info = {}
        self.united_res = None
        self.names = set()
        if name is not None:
            self.init_callable(name, res_type)

    def __deepcopy__(self, memo):
        res = self.__class__()
#        res.bf_info = copy(self.bf_info)
        res.united_res = deepcopy(self.united_res)
        res.names = copy(self.names)
        return res

    def init_callable(self, name, res_type):
#        self.bf_info = {name: VarTypes(init_const=[res_type])}
        self.names = set([name])
        self.united_res = res_type

    def add_type(self, other):
        if self.united_res is not None and other.united_res is not None:
            self.united_res |= other.united_res
        elif other.united_res is not None:
            self.united_res = deepcopy(other.united_res)
        self.names |= other.names

    def call(self, analysis_type, from_inst_num, func_args=None):
        #print"STRANGE CALL"
        return {"types":deepcopy(self.united_res), "values": create_empty_value()}

    def _lge_inner(self, other):
        sc = set(self.names)
        oc = set(other.names)
        less = int(sc <= oc)
        greater = int(sc >= oc)
        equal = int(sc == oc)
        return (less, greater, equal)

    def _repr_inner(self):
        return '%s([' % self.clsname + \
                ', '.join(self.names) + ']: ' + ('%r)' % self.united_res)

    def _pretty_inner(self):
        return 'builtin_function([' + ', '.join(self.names) + ']: ' + ('%r)' % self.united_res)


class TypeBuiltinSmthCallable(TypeBuiltinFunction):
    implemented_types = ('builtin_smth_callable',)


