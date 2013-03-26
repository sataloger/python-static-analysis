# -*- coding: utf-8 -*-
from __future__ import with_statement
import types
import yapgvb
import py_compile
import marshal
import os
import sys
import copy
from collections import deque
import symtable
import opcode
from analyzer.byteplay import *

return_opcodes = [RETURN_VALUE, YIELD_VALUE]
raising_opcodes = [RAISE_VARARGS, END_FINALLY]
if sys.version_info < (2, 7):
    ifjump_opcodes = [JUMP_IF_FALSE, JUMP_IF_TRUE, FOR_ITER]
else:
    ifjump_opcodes = [POP_JUMP_IF_FALSE, POP_JUMP_IF_TRUE, FOR_ITER,
                      JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP]

blockEndInstrs = [JUMP_FORWARD, JUMP_ABSOLUTE, BREAK_LOOP, CONTINUE_LOOP] \
        + return_opcodes + raising_opcodes + ifjump_opcodes
 # считаем, что все вызовы бросают исключения
#blockEndInstrs += [opmap[op_name] for op_name in opmap
#                       if op_name.startswith('CALL_FUNCTION')]
start_ops = [
    opmap['STORE_GLOBAL'],opmap['STORE_NAME'], opmap['STORE_FAST'],opmap['STORE_DEREF'],
    opmap['DELETE_GLOBAL'],opmap['DELETE_FAST'], opmap['STORE_ATTR'], opmap['DELETE_ATTR']
]

class bb(object): # TODO: rename it to BaseBlock ?
    def __init__(self, prefix, parent_cfg, insts = None):
        if insts:
            self.set_insts(insts)
            self.insts = insts
        else:
            self.id = None
            self.insts = {}
            self.inst_keys = []
        self.__next_bbs_set = set()
        self.next_bbs = []
        self.prefix = prefix
        self.parent_cfg = parent_cfg

    def __repr__(self):
        if hasattr(self, 'insts_list'):
            res = ''
            for inst in self.insts_list:
                res += self.__inst_formatted(inst, self.parent_cfg) + '\n'
            return res
        else:
            return ''


    def add_next(self, next_bbs):
        for cur_bb_id in next_bbs:
            if not cur_bb_id in self.__next_bbs_set:
                self.next_bbs.append(cur_bb_id)
                self.__next_bbs_set.add(cur_bb_id)

    def clear_next(self):
        self.next_bbs = []
        self.__next_bbs_set = set()

    def set_insts(self, insts):
        self.insts = insts
        if self.insts:
            self.id = min(self.insts)
            self.inst_keys = self.insts.keys()
            self.inst_keys.sort()
        else:
            self.id = None
            self.inst_keys = []

    def get_next_ids(self):
        return self.next_bbs[:]

    def dot_repr(self, cfg, all_instructions = False):
        if self.id == 'entry':
            curLabel =  "%s\\nentry" % cfg.prefix
        elif self.id == 'exit':
            curLabel =  'exit'
        elif all_instructions:
            curLabel = "\\n".join([str(self.id)] + [self.__inst_formatted(inst, cfg, True) for inst in self.insts_list])
        elif len(self.insts_list) <= 3:
            curLabel = "\\n".join([str(self.id)] + [self.__inst_formatted(inst, cfg, True) for inst in self.insts_list])
        else:
            curLabel = "\\n".join([str(self.id)] + [self.__inst_formatted(self.insts_list[0], cfg, True), '...',
                        self.__inst_formatted(self.insts_list[-1], cfg, True)])
        return "bb_" + str(self.id), curLabel

    @staticmethod
    def __inst_formatted(inst, cfg, for_pyGraphviz = False):
        res = str(inst[0]).rjust(4, '0')+"  "+repr(inst[1]).ljust(15)+str(inst[2])
        if repr(inst[1]).find('_FAST') != -1:
            res = res + '  (%s)' % cfg.codeinfo['co_varnames'][inst[2]]
        elif repr(inst[1]).find('_GLOBAL') != -1 or repr(inst[1]).find('_ATTR') != -1 or repr(inst[1]).find('_NAME') != -1:
            res = res + '  (%s)' % cfg.codeinfo['co_names'][inst[2]]
        elif inst[1] == LOAD_CONST:
            valTmp = repr(cfg.codeinfo['co_consts'][inst[2]])
            if len(valTmp) > 100 and for_pyGraphviz:
                res = res + '  (%s...)' % repr(cfg.codeinfo['co_consts'][inst[2]])[:100]
            else:
                res = res + '  (%s)' % repr(cfg.codeinfo['co_consts'][inst[2]])
        if for_pyGraphviz:
            res = res.replace('\n', '<br>')
            res = res.replace('\\', '\\\\')
            res = res.replace('.', '\\.')
            res = res.replace(':', ' ')
            res = res.replace(';', '\\;')
            res = res.replace('\'', '\\\'')
            res = res.replace('"', '\\"')
        return res


    def __contains__(self, inst_num):
        return inst_num in self.insts

    def split_at(self, inst_num):
        new_insts = {}
        start_pos = min(self.insts)
        while start_pos != inst_num:
            new_insts[start_pos] = self.insts[start_pos]
            del self.insts[start_pos]
            start_pos = new_insts[start_pos][2]
        new_bb = bb(self.prefix, self.parent_cfg, self.insts)
        new_bb.add_next(self.next_bbs)
        self.insts = new_insts
        self.clear_next()
        self.add_next([new_bb.id])
        return (self, new_bb)

    def make_insts_list(self):
        keys = sorted(self.insts.keys())
        self.insts_list = [(i, self.insts[i][0], self.insts[i][1]) for i in keys]


    def get_next_inst_nums(self, end_finally_next):
        next_insts = []
        if not self.insts:
            return next_insts
        inst_num = max(self.insts)
        inst = self.insts[inst_num]

        if inst[0] in hasjump:
            # Continue execution
            if inst[0] in ifjump_opcodes:
                next_insts.append(inst[2])
            # Jump
            if inst[0] in hasjrel:
                next_insts.append(inst[2] + inst[1])
            else:
                next_insts.append(inst[1])
        elif repr(inst[0]).startswith("CALL_FUNCTION"):
            next_insts.append(inst[2])
        elif inst[0] == END_FINALLY:
            next_insts.extend(end_finally_next[inst_num])
        elif inst[0] not in blockEndInstrs:
        #            print opname[inst[0]]
        #            print inst
        #            print 'Falls on %s' % opname[inst[0]]
                    if inst[0] < opcode.HAVE_ARGUMENT:
                        next_insts.append(inst_num + 1)
                    else:
                        next_insts.append(inst_num + 3)
        return next_insts

    def starts_with(self):
        if not self.insts:
            return (-1, (-1, None, None))
        inst_num = min(self.insts)
        return (inst_num, self.insts[inst_num])

    def ends_with(self):
        if not self.insts:
            return (-1, (-1, None, None))
        inst_num = max(self.insts)
        return (inst_num, self.insts[inst_num])


class cfg(object):
    def __init__(self, prefix, code, syminfo):
        self.prefix = prefix
        self.bbs = {
            # для обнаружения странных ошибок (на всякий случай)
            'entry' : bb(prefix, self, {'entry' :  (NOP, None, 'exit')}),
            # для того, чтобы exit был полноценной вершиной
            'exit' : bb(prefix, self, {'exit' :  (NOP, None, 'exit')}),
        }
#        import byteplay
#        code = byteplay.Code.from_code(code).to_code()
        self.codeobj = code
        self.syminfo = syminfo
        self.code = code.co_code
        self.__make_insts(self.code)
        self.__make_cfg()
        self.__post_process()
        self.flags = {'accept_args' : bool(code.co_flags & 0x04),
                      'accept_kwargs' : bool(code.co_flags & 0x08),
                      'is_generator' : bool(code.co_flags & 0x20),
                      }
        self.__add_codeinfo(code)

        self.format()


    def format(self):
        for cur_bb_id in self.bbs:
            self.bbs[cur_bb_id].make_insts_list()
        self.bbs_keys = self.bbs.keys()
        self.bbs_keys.sort()

    def all_bbs_in_insts(self):
        res = {}
        for cur_bb_id in self.bbs:
            if cur_bb_id not in ('entry', 'exit'):
                res.update(self.bbs[cur_bb_id].insts)
        return res

    def dot_repr(self, all_instructions = False):
        graph = yapgvb.Digraph('cfg')
        graph.dpi = 600
        nodes_dict = {}

        for cur_bb_id in self.bbs:
            lst = self.bbs[cur_bb_id].dot_repr(self, all_instructions)
            nodes_dict[lst[0]] = graph.add_node(lst[0], label=lst[1])

        for cur_bb_id in self.bbs:
            nextNodeNum = 0
            for next_bb_id in self.bbs[cur_bb_id].get_next_ids():
                edge = nodes_dict["bb_"+str(cur_bb_id)] - nodes_dict["bb_" + str(next_bb_id)]
                edge.label = str(nextNodeNum)
                nextNodeNum += 1
        return graph


    def __make_insts(self, code):
        all_insts = {}
        self.__exceptEnter = []
        self.__finallyEnter = []
        self.__loopEnter = []
        n = len(code)
        self.block_borders = {}
        i = 0
        extended_arg = 0
        while i < n: #определение начал блоков кода
            op = Opcode(ord(code[i]))
            i_orig = i
            i+=1
            if op >= opcode.HAVE_ARGUMENT:
                oparg = ord(code[i]) + ord(code[i+1])*256 + extended_arg
                extended_arg = 0
                i = i + 2
                if op == opcode.EXTENDED_ARG:
                    extended_arg = oparg*65536L
            if op != opcode.EXTENDED_ARG:
                if op >= opcode.HAVE_ARGUMENT:
                    all_insts[i_orig] = (op, oparg, i)
                else:
                    all_insts[i_orig] = (op, None, i)
            if op == SETUP_FINALLY or (sys.version_info >= (2, 7) and op == SETUP_WITH):
                self.__finallyEnter.append((i_orig, i + oparg))
                self.block_borders[i_orig] = i + oparg
            elif op == SETUP_EXCEPT:
                self.__exceptEnter.append((i_orig, i + oparg))
                self.block_borders[i_orig] = i + oparg
            elif op == SETUP_LOOP:
                self.__loopEnter.append((i_orig, i + oparg))
                self.block_borders[i_orig] = i + oparg
        self.all_insts = all_insts
        self.__calc_END_FINALLY()

    def __find_where_jump(self, jumpFrom, arr):
        minLen = max(self.all_insts)
        jumpWhere = 'exit'
        if not arr:
            return None
        for elem in arr:
            if (minLen >= elem[1] - elem[0]) and (elem[0] <= jumpFrom < elem[1]):
                jumpWhere = elem[1]
                minLen = elem[1] - elem[0]
        return jumpWhere

    def __find_jump_head(self, jumpFrom, arr):
        minLen = max(self.all_insts)
        jumpHead = 'entry'
        if not arr:
            return None
        for elem in arr:
            if (minLen >= elem[1] - elem[0]) and (elem[0] <= jumpFrom < elem[1]):
                jumpHead = elem[0]
                minLen = elem[1] - elem[0]
        return jumpHead

    def get_seq_instrs(self, start_pos):
        if start_pos in ('entry', 'exit'):
            return {}
        pos = start_pos
        cur_inst = self.all_insts[start_pos]
        res = {pos : cur_inst}
        while cur_inst[0] not in blockEndInstrs:
            pos = cur_inst[2]
            if pos in ('entry', 'exit') or \
               pos in self.bbs:
                break
            cur_inst = self.all_insts[pos]

            if cur_inst[0] in start_ops:
            #                print "Here we go" # следующая инструкция должна быть началом ББ
                            break
            res[pos] = cur_inst
        return res

    def __inst_num_in_bb(self, inst_num):
        for cur_bb in self.bbs.values():
            if inst_num in cur_bb:
                return cur_bb.id
        return None

    def __insert_connection(self, cur_bb_id, inst_num):
        next_bb_id = self.__inst_num_in_bb(inst_num)
        if next_bb_id is not None:
            if self.bbs[next_bb_id].starts_with()[0] == inst_num:
                self.bbs[cur_bb_id].add_next([next_bb_id])
            else:
                new_bb = self.bbs[next_bb_id].split_at(inst_num)[1]
                self.bbs[new_bb.id] = new_bb
                self.bbs[cur_bb_id].add_next([new_bb.id])
                next_bb_id = None
        else:
            new_bb = bb(self.prefix, self, self.get_seq_instrs(inst_num))
            self.bbs[new_bb.id] = new_bb
            self.bbs[cur_bb_id].add_next([new_bb.id])
        if next_bb_id is None:
            return new_bb
        else:
            return None

    def __walk_from(self, start_pos):
        if start_pos == 'exit':
            return
        if start_pos not in self.bbs:
            self.bbs[start_pos] = bb(self.prefix, self, self.get_seq_instrs(start_pos))
        bb_queue = [start_pos]
        ind = 0
        while ind < len(bb_queue):
            cur_bb_id = bb_queue[ind]
            ind += 1
            if cur_bb_id in ('entry', 'exit'):
                continue
            next_insts = self.bbs[cur_bb_id].get_next_inst_nums(self.end_finally_next)
            bb_insts = self.bbs[cur_bb_id].insts
            if not next_insts and \
                bb_insts[max(bb_insts)][2] in self.bbs:
                next_insts.append(bb_insts[max(bb_insts)][2])
            for inst_num in next_insts:
                new_bb = self.__insert_connection(cur_bb_id, inst_num)
                if new_bb: # new basic block created
                    bb_queue.append(new_bb.id)

    def __make_cfg(self):
        start_pos = min(self.all_insts)
        self.__walk_from(start_pos)
        self.bbs['entry'].add_next([start_pos])


    def __calc_END_FINALLY(self):
        block_stack = deque()
        except_end = {}
        finally_end = {}
        end_finally_next = {}
        for inst_num in sorted(self.all_insts):
            inst_name, inst_param, inst_next = self.all_insts[inst_num]
            if inst_name in (SETUP_FINALLY, SETUP_EXCEPT, SETUP_LOOP,
                    (sys.version_info >= (2, 7)) and SETUP_WITH):
                block_stack.append((inst_name, inst_num))
            elif inst_name == END_FINALLY:
                tos = (SETUP_LOOP, None)
                while tos[0] == SETUP_LOOP:
                    tos = block_stack.pop()
                bl_copy = copy.copy(block_stack)
                while True:
                    tos2 = (SETUP_LOOP, None)
                    while tos2[0] == SETUP_LOOP and bl_copy:
                        tos2 = bl_copy.pop()
                    if tos2[0] == SETUP_LOOP:
                        next_handler = 'exit'
                        break
                    else:
                       next_handler = self.block_borders[tos2[1]]
                       if tos2[1] < inst_num < next_handler:
                           break
                if tos[0] == SETUP_EXCEPT:
                    except_end[inst_num] = tos[1]
                    end_finally_next[inst_num] = (next_handler,)
                elif tos[0] == SETUP_FINALLY or (sys.version_info >= (2, 7) and tos[0] == SETUP_WITH):
                    finally_end[inst_num] = tos[1]
                    end_finally_next[inst_num] = (inst_next, next_handler)

        self.except_end = except_end
        self.finally_end = finally_end
        self.end_finally_next = end_finally_next

    def __process_return(self):
        for cur_bb_id in self.bbs.keys():
            if self.bbs[cur_bb_id].ends_with()[1][0] == RETURN_VALUE:
                self.bbs[cur_bb_id].add_next(['exit'])

    def __process_yield(self):
        for cur_bb_id in self.bbs.keys()[:]:
            inst_num, inst = self.bbs[cur_bb_id].ends_with()
            if inst[0] == YIELD_VALUE:
                self.bbs[cur_bb_id].add_next(['exit'])
                self.__walk_from(inst[2])
                self.bbs['entry'].add_next([inst[2]])

    def __process_break_continue(self):
        for cur_bb_id in self.bbs.keys()[:]:
            inst_num, inst = self.bbs[cur_bb_id].ends_with()
            if inst[0] == BREAK_LOOP:
                new_inst_num = self.__find_where_jump(inst_num, self.__loopEnter)
                if new_inst_num is None or new_inst_num == 'exit':
                    print self.prefix,
                    print self.__loopEnter, new_inst_num
                    raise SyntaxError('cfg_creator: BREAK_LOOP outside of SETUP_LOOP block!')
                    new_inst_num = 'exit'
                self.__insert_connection(cur_bb_id, new_inst_num)
            if inst[0] == CONTINUE_LOOP:
                new_inst_num = self.__find_jump_head(inst_num, self.__loopEnter)
                if new_inst_num is None or new_inst_num == 'entry':
                    print self.prefix,
                    print self.__loopEnter, new_inst_num
                    raise SyntaxError('cfg_creator: CONTINUE_LOOP outside of SETUP_LOOP block!')
                    new_inst_num = 'exit'
                self.__insert_connection(cur_bb_id, new_inst_num)

    def __process_raise_call(self):
        keys = self.bbs.keys()
        keys.sort()
        for cur_bb_id in keys:
            inst_num, inst = self.bbs[cur_bb_id].ends_with()

#            if opname[inst[0]] == 'RAISE_VARARGS' or \
#               opname[inst[0]].startswith('CALL_FUNCTION'):
            if inst[0] == RAISE_VARARGS:
                except_inst_num = self.__find_where_jump(inst_num, self.__exceptEnter)
                finally_inst_num = self.__find_where_jump(inst_num, self.__finallyEnter)
                if except_inst_num is None:
                    if finally_inst_num is not None:
                        new_inst_num = finally_inst_num
                    else:
                        new_inst_num = 'exit'
                else:
                    if except_inst_num > finally_inst_num and \
                       finally_inst_num is not None:
                        new_inst_num = finally_inst_num
                    else:
                        new_inst_num = except_inst_num
                new_bb = self.__insert_connection(cur_bb_id, new_inst_num)
                if new_bb:
                    self.__walk_from(new_inst_num)


    def __find_END_FINALLY(self):
        using_insts = self.all_insts
        using_insts_keys = self.all_insts.keys()
        using_insts_keys.sort()
        self.__end_finally = []
        self.__end_finally_pos = {}
        for cur_item in self.__finallyEnter:
            cur_inst_num = cur_item[1]
            while using_insts[cur_inst_num][0] != END_FINALLY:
                cur_inst_num = using_insts[cur_inst_num][2]
            self.__end_finally.append((cur_item[0], cur_inst_num))
        for inst_num in using_insts_keys:
            if using_insts[inst_num][0] == END_FINALLY:
                self.__end_finally_pos[inst_num] = True


    def __post_process(self):
        # при нескольких постобработках, обнаруживающих ББ,
        # нужно их класть в цикл и крутить пока bbs пополняется

        # вне цикла, т.к. поиск идет сразу по _всем_ инструкциям --
        # даже тем, которые могут быть мертвыми
        self.__find_END_FINALLY()
        old_len = 0
        while old_len != len(self.bbs):
            old_len = len(self.bbs)
            self.__process_yield()
            self.__process_raise_call()

        # должны быть последними операциями -
        # тут не обнаруживаются новые базовые блоки
        self.__process_break_continue()
        self.__process_return()


    def __add_codeinfo(self, code):
        codeinfo = {'self_code' : code,
                    }
        for attr in dir(code):
            if attr.find('__') != 0:
                codeinfo[attr] = getattr(code, attr)
        codeinfo['blockBorders'] = {'loop': copy.deepcopy(self.__loopEnter),
                                    'except': copy.deepcopy(self.__exceptEnter),
                                    'finally': copy.deepcopy(self.__finallyEnter)}
        self.codeinfo = codeinfo

    def __repr__(self):
        res = ("=====%s=====\n" % self.prefix) + ("----%s----\n%r\n" % ('entry', self.bbs['entry']))
        keys = sorted(set(self.bbs.keys()) - set(['entry', 'exit']))
        res += '\n'.join(["----%s----\n%r" % (name, self.bbs[name])
                           for name in keys])
        res += ("\n----%s----\n%r\n" % ('exit', self.bbs['exit'])) + "============"  
        return res



class MyModule(object):
    def __init__(self, module_name, code, syminfo):
        self.module_name = module_name
        self.module_code = code
        self.syminfo = syminfo
        self.__make_cfgs()

    def __make_cfgs(self):
        self.cfg = {}
        self.__nameLevels = []
        self.lambdaCount = 0
        self.genexprCount = 0
        self.__make_cfg(self.module_code, self.syminfo)

    def __make_cfg(self, code, syminfo):
        if code is None:
            return
        name = code.co_name
        if name == "<lambda>":
            self.__nameLevels.append("<lambda_%i>" % self.lambdaCount)
            self.lambdaCount += 1
        elif name == "<genexpr>":
            self.__nameLevels.append("<genexpr_%i>" % self.genexprCount)
            self.genexprCount += 1
        elif name == "<module>":
            self.__nameLevels.append(self.module_name)
        else:
            self.__nameLevels.append(name)
        name = ".".join(self.__nameLevels)
        self.cfg[name] = cfg(name, code, syminfo)

        sym_children = syminfo.get_children()
        for const in code.co_consts:
            if type(const) == types.CodeType:
                sym_name = const.co_name
                for sym_ch in sym_children:
                    sym_ch_name = sym_ch.get_name()
                    if sym_ch_name == sym_name:
                        break
                    elif sym_name == '<%s>' % sym_ch_name:
                        break
                else:
                    print sym_ch.get_name()
                    raise Exception("NOT FOUND symbol info for %s.%s" % (name, sym_name))
                self.__make_cfg(const, sym_ch)
        self.__nameLevels.pop()

    def dot_repr(self, all_instructions = False):
        return [(curName, self.cfg[curName].dot_repr(all_instructions))
                for curName in  self.cfg]



class CFGCreator(object):
    @staticmethod
    def make_cfgs(filename):
        return MyModule(*CFGCreator.load_file(filename))

    @staticmethod
    def load_file(filename):
        filename = os.path.abspath(filename)
        with open(filename) as fp:
            syminfo = symtable.symtable(fp.read() + '\n', filename, 'exec')

        if(os.path.splitext(filename)[1] == '.py'):
            try:
                py_compile.compile(filename, filename+'c', doraise=True)
            except py_compile.PyCompileError, msg:
                print str(msg)
                print 'Couldn\'t compile %s, stopping.' % filename
                os._exit(0)
            filename += 'c'

        module_name = os.path.splitext(os.path.basename(filename))[0]
        with open(filename, 'rb') as fp:
            magic = fp.read(4)
            moddate = fp.read(4)
            module_code = marshal.load(fp)
        return (module_name, module_code, syminfo)

