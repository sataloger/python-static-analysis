# -*- coding: utf-8 -*-

from base_classes import *

# number - точность "обычного" анализа (с простым перечислением значений)
# type_of_analysis - тип анализа
# values - список значений (для интервального анализа - список из двух элементов) целого типа!
# other_values - список значений произвольного типа! В нашем случае будут строки :)
# unknown_value - переменная, показывающая, есть ли значения, возвращаемые из функции (в случае интрапроцедурного анализа для a = f() получаем a: MyValues {unknown_value}
# error - словарь ошибок - булевское значение (означает, возможно ли ошибка такого типа в данной точке программы)
# iterator - для for-а хранится значение переменной, бегающей по циклу. Если в ней None - следующая итерация цикла не выполнится :)

cmp_op = ('<', '<=', '==', '!=', '>', '>=', 'in', 'not in', 'is', 'is not', 'exception match', 'BAD')

class MyValues(BaseInfoStorage):
    insts_handler = deepcopy(BaseInfoStorage.insts_handler)
    implemented_insts = insts_handler.stored_insts
    
    def __init__(self, init_value = None, num_of_vals = 3, type_of_analysis = 'normal'):
#  print "init_value", init_value
        self.number = num_of_vals
        self.type_of_analysis = type_of_analysis
        self.values = [] ###
        self.BDD_values = None
        self.other_values = []
        #self.unknown_value = False
        self.unknown_value = True ###
        self.iterator = None
        self.error = {}
        self.error['division_on_zero'] = False
        #self.inited = False
        if init_value is not None and not init_value[1]:
          for value in init_value[0]:
            self.add_value(value)
          self.unknown_value = False 
        
    '''
    def add_BDD_value(self, value):
        mgr = pycudd.DdManager()
        mgr.SetDefault()
        
        b = {}
        for i in range(32):
            b[i] = mgr.IthVar(i)
        
        value = bin(value)[2:] # bin(5) = '0b110'
        if (not self.BDD_values):
            if (value[len(value) - 1] == '1'):
                res = b[0]
            else:
                res = ~b[0]
        for i in range(len(value)):
            if (value[len(value) - 1 - i] == '1'):
                res &= b[i]
            else:
                res &= ~b[i]
        if (len(value) < 32):
            for i in range(len(value), 32):
                res &= ~b[i]
        self.BDD_values = res
        

        #от сих
        if (self.BDD_values):
            if (value[len(value) - 1] == '1'):   ##
                self.BDD_values = b[0]          ##
            else:                                ##
                self.BDD_values = ~b[0]         ## Пофиксить!!!
        for i in range(len(value)):
            if (value[len(value) - 1 - i] == '1'):
                self.BDD_values &= b[i]
            else:
                self.BDD_values &= ~b[i]
        if (len(value) < 32):
            for i in range(len(value), 32):
                self.BDD_values &= ~b[i]
        #до сих


        array = None
        print self.BDD_values.BddToCubeArray(array)
        print self.BDD_values.ApaPrintDensity()
    '''


    # Вроде нужен для перегрузки. Узнать действие точно!
    def __deepcopy__(self, memo):
        res = self.__class__(num_of_vals = self.number,\
                                type_of_analysis = self.type_of_analysis)
        #res.number = deepcopy(self.number)
        #res.type_of_analysis = deepcopy(self.type_of_analysis)
        #res.values = deepcopy(self.values)
        res.values = self.values
        res.other_values = self.other_values
        res.unknown_value = self.unknown_value
        res.error = self.error
        res.iterator = deepcopy(self.iterator)
        #res.BDD_values = deepcopy(self.BDD_values)
        #res.inited = self.inited
        return res
        
    def add_value(self, value):
        print "add_value: ", value 
        if (type(value) != int):
            if not (value in self.other_values):
                self.other_values.append(value)
                return
        if (self.type_of_analysis == 'normal'):
            if not (value in self.values):
                print "LEN", len(self.values), self.number
                if (len(self.values) < self.number):
                    self.values.append(value)
                else:
                    self.type_of_analysis = 'interval'
                    self.values = [min(min(self.values), value), max(max(self.values), value)]
                    print "INTERVAL"
        else:
            if not (value in range(self.values[0], self.values[1])):
                if (value < self.values[0]):
                    self.values[0] = value
                else:
                    self.values[1] = value
                    
    '''def add_myvalue(self, other):

        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                res = set(self.values) | set(other.values)
                if (len(res) <= self.number):
                    self.values = list(res)
                else:
                    self.values = [min(res), max(res)]
            else:
                other_values_list = [val for val in range(other.values[0],\
                                                    other.values[1] + 1)]
                res = set(self.values) | set(other_values_list)
                if (len(res) <= self.number):
                    self.values = list(res)
                else:
                    self.values = [min(res), max(res)]
        else:
            self.values = [min(self.values[0], min(other.values)), max(self.values[1], max(other.values))]
    '''
                                        
    # Возвращает true, если сравнимы, false - иначе :)       
    def __comparable(self, other):
        tmp = set(self.other_values) & set(other.other_values)
        if (tmp == set(self.other_values) or tmp == set(other.other_values)):
            res = tmp == set(self.other_values)                               # большое извращение. 
        else:
            return False
        ###
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                tmp = set(self.values) & set(other.values)
                if (tmp == set(self.values) or tmp == set(other.values)):
                    if (self.other_values != other.other_values):
                        if (res == (tmp == set(self.values))):
                            return True
                        else:
                            return False
                    else:
                        return True
                else:
                    return False
            else:
                other_values_list = [val for val in range(other.values[0],\
                                                       other.values[1] + 1)] ## range(3,7) = (3, 4, 5, 6) !!!
                tmp = set(self.values) & set(other_values_list)
                if (tmp == set(self.values) or tmp == set(other_values_list)):
                    if (self.other_values != other.other_values):
                        if (res == (tmp == set(self.values))):
                            return True
                        else:
                            return False
                    else:
                        return True
                else:
                    return False
        else:
            if (other.type_of_analysis == 'normal'):
                self_values_list = [val for val in range(self.values[0],\
                                                     self.values[1] + 1)]
                tmp = set(self_values_list) & set(other.values)
                if (tmp == set(self_values_list) or tmp == set(other.values)):
                    if (self.other_values != other.other_values):
                        if (res == (tmp == set(self.values))):
                            return True
                        else:
                            return False
                else:
                    return False
            else:
                if (self.values[0] < other.values[0]):
                    if (self.values[1] < other.values[1]):
                        return False
                    else:
                        if (self.other_values != other.other_values):
                            if (res):
                                return False
                            else:
                                return True
                        else:
                            return True
                else:
                    if (self.values[1] <= other.values[1]):
                        if (self.other_values != other.other_values):
                            if (res):
                                return True
                            else:
                                return False
                        else:
                            return True
                    else:
                        return False
                
    def _lge_inner(self, other):
        if not self.__comparable(other):
                return (0, 0, 0)
        ### self.other_values и other.other_values можно даже не рассматривать, так как при выполнении некоторого условия для values будет гарантироваться
        ### и для other_values (обеспечивается __comparable).
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                if (len(self.values) < len(other.values)):
                    return (1, 0, 0)
                elif (len(self.values) > len(other.values)):
                    return (0, 1, 0)
                else:
                    if (len(self.other_values) < len(other.other_values)):
                        return (1, 0, 0)
                    elif (len(self.other_values) > len(other.other_values)):
                        return (0, 1, 0)
                    else:
                        return (0, 0, 1)
            else:
                if (min(self.values) > other.values[0]):
                    return (1, 0, 0)
                elif (min(self.values) < other.values[0]):
                    return (0, 1, 0) # Т.к. сравнимы
                else:
                    if (max(self.values) > other.values[1]):
                        return (0, 1, 0)
                    elif (max(self.values) < other.values[1]):
                        return (1, 0, 0)
                    else:
                        if (len(self.other_values) < len(other.other_values)):
                            return (1, 0, 0)
                        elif (len(self.other_values) > len(other.other_values)):
                            return (0, 1, 0)
                        else:
                            return (0, 0, 1)
        else:
            if (other.type_of_analysis == 'normal'):
                if (self.values[0] > min(other.values)):
                    return (1, 0, 0)
                elif (self.values[0] < min(other.values)):
                    return (0, 1, 0)
                else:
                    if (self.values[1] > max(other.values)):
                        return (0, 1, 0)
                    elif (self.values[1] < max(other.values)):
                        return (1, 0, 0)
                    else:
                        if (len(self.other_values) < len(other.other_values)):
                            return (1, 0, 0)
                        elif (len(self.other_values) > len(other.other_values)):
                            return (0, 1, 0)
                        else:
                            return (0, 0, 1)
            else:
                if (self.values[0] < other.values[0]):
                    return (1, 0, 0) # Т.к. сравнимы - пересекаться интервалы не могут
                elif (self.values[0] > other.values[0]):
                    return (0, 1, 0)
                else:
                    if (self.values[1] < self.values[1]):
                        return (0, 1, 0)
                    elif (self.values[1] > self.values[1]):
                        return (1, 0, 0)
                    else:
                        if (len(self.other_values) < len(other.other_values)):
                            return (1, 0, 0)
                        elif (len(self.other_values) > len(other.other_values)):
                            return (0, 1, 0)
                        else:
                            return (0, 0, 1)
                                                
    def __nonzero__(self):
        return any(val for val in self.values) or\
        any(other_val for other_val in self.other_values) or self.unknown_value
        
    # operator.__ior__(a, b) a = ior(a, b) is equivalent to a |= b.
    def __ior__(self, other):
        print "IOR"
        self.iterator = other.iterator
        self.unknown_value = False
        if (other.unknown_value):
            self.unknown_value = True
        if (other.error['division_on_zero']):
            self.error['division_on_zero'] = True
        if (self.type_of_analysis == 'normal'):
            print "HE", other.type_of_analysis, "ME", self.type_of_analysis
            if (other.type_of_analysis == 'normal'):
                res = set(self.values) | set(other.values)
                if (len(res) > self.number):
                        self.values = [min(res), max(res)]
                        self.type_of_analysis = 'interval'
                else:
                        self.values = list(res)
            else:
                print "HE NOT"
                if (len(self.values) == 0):
                    self.values = [other.values[0], other.values[1]]
                else:
                    tmp = self.values
                    self.values = []
                    self.values.append(min(min(tmp), other.values[0]))
                    self.values.append(max(max(tmp), other.values[1]))
                self.type_of_analysis = 'interval'
        else:
            if (other.type_of_analysis == 'normal'):
                self.values[0] = min(self.values[0], min(other.values))
                self.values[1] = max(self.values[1], max(other.values))
            else:
                self.values[0] = min(self.values[0], other.values[0])
                self.values[1] = max(self.values[1], other.values[1])
            self.type_of_analysis = 'interval'
        ###
        res = set(self.other_values) | set(other.other_values)
        self.other_values = list(res)
        #self.BDD_values.Or(other.BDD_values)
        print "RESULT TYPES", self.type_of_analysis
        return self
        
    def __or__(self, other):
        pass
        
    def _repr_inner(self):
        if (self.type_of_analysis == 'normal'):
            res = 'MyValues: {' + str(self.values)[1:-1] + '}' 
#res =  str(self.values)[1:-1] ###
        else:
            res = 'MyValues: ' + str(self.values)
#           res =  str(self.values) ###
        if (self.error['division_on_zero']):
            res += ', DIVISION ON ZERO'
        if (self.unknown_value):
            res += ', unknown value'
        if (self.other_values):
            res += ', ' + str(self.other_values)[1:-1]
        if (self.BDD_values):
            pass
        #if (self.iterator):
        #    res += ', iterator: ' + str(self.iterator)
        return res

    
    ###
    def _pretty_inner(self):
      if self.type_of_analysis == 'normal':
        res_lst = str(self.values)[1:-1]
      else:
        res_lst = str(self.values)
      if self.unknown_value:
        res_lst = 'unknown'
      if self.other_values:
        res_lst = str(self.other_values)[1:-1]
      return res_lst

    _show_dublicates = _pretty_inner
    
   # _pretty_inner = _repr_inner
      
    def binary_power(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for pow_val in self.values:
                        if not ((val ** pow_val) in values):
                            values.append(val ** pow_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for pow_val in self.values:
                        if not ((val ** pow_val) in values):
                            values.append(val ** pow_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for pow_val in range(min(self.values), max(self.values) + 1):
                        if not ((val ** pow_val) in values):
                            values.append(val ** pow_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for pow_val in range(min(self.values), max(self.values) + 1):
                        if not ((val ** pow_val) in values):
                            values.append(val ** pow_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
#       print res
        return res
        
    def binary_multiply(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if not (other.values) and not (other.other_values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for mult_val in self.values:
                        if not ((val * mult_val) in values):
                            values.append(val * mult_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for mult_val in self.values:
                        if not ((val * mult_val) in values):
                            values.append(val * mult_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for mult_val in range(min(self.values), max(self.values) + 1):
                        if not ((val * mult_val) in values):
                            values.append(val * mult_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for mult_val in range(min(self.values), max(self.values) + 1):
                        if not ((val * mult_val) in values):
                            values.append(val * mult_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        other_values = []
        ### Только для строк!!!
        for val in other.other_values:
            for mult_val in self.values:
                if (type(val) == str):
                    if not ((val * mult_val) in other_values):
                        other_values.append(val * mult_val)
        res.other_values = other_values
        return res
        
    def binary_divide(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for div_val in self.values:
                        if (val == 0):
                            res.error['division_on_zero'] = True
                            continue
                        if not ((val / div_val ) in values):
#                print "%r/%r=%r" %(div_val,val,div_val/val)
                            values.append(val / div_val )
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for div_val in self.values:
                        if (val == 0):
                            res.error['division_on_zero'] = True
                            continue
                        if not ((val / div_val ) in values):
                            values.append(val / div_val )
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for div_val in range(min(self.values), max(self.values) + 1):
                        if (val == 0):
                            res.error['division_on_zero'] = True
                            continue
                        if not ((val / div_val ) in values):
                            values.append(val / div_val )
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for div_val in range(min(self.values), max(self.values) + 1):
                        if (val == 0):
                            res.error['division_on_zero'] = True
                            continue
                        if not ((val / div_val ) in values):
                            values.append(val / div_val )
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_floor_divide(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for div_val in self.values:
                        if not ((val // div_val) in values):
                            values.append(val // div_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for div_val in self.values:
                        if not ((val // div_val) in values):
                            values.append(val // div_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for div_val in range(min(self.values), max(self.values) + 1):
                        if not ((val // div_val) in values):
                            values.append(val // div_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for div_val in range(min(self.values), max(self.values) + 1):
                        if not ((val // div_val) in values):
                            values.append(val // div_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_modulo(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for mod_val in self.values:
                        if not ((val % mod_val) in values):
                            values.append(val % mod_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for mod_val in self.values:
                        if not ((val % mod_val) in values):
                            values.append(val % mod_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for mod_val in range(min(self.values), max(self.values) + 1):
                        if not ((val % mod_val) in values):
                            values.append(val % mod_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for mod_val in range(min(self.values), max(self.values) + 1):
                        if not ((val % mod_val) in values):
                            values.append(val % mod_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_add(self, vals):
#       print "VALUES HANDLER"
        other = vals[0]
#        print "ADDING", self, "to", other
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.other_values) and not (other.other_values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for add_val in self.values:
                        if not ((val + add_val) in values):
                            values.append(val + add_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for add_val in self.values:
                        if not ((val + add_val) in values):
                            values.append(val + add_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for add_val in range(min(self.values), max(self.values) + 1):
                        if not ((val + add_val) in values):
                            values.append(val + add_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for add_val in range(min(self.values), max(self.values) + 1):
                        if not ((val + add_val) in values):
                            values.append(val + add_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        res.unknown_value = False
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        ###
        other_values = []
        for val in other.other_values:
            for add_val in self.other_values:
                if not ((val + add_val) in other_values):
                    other_values.append(val + add_val)
        res.other_values = other_values
        return res
       
    def binary_subtract(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            print "TEST: ME NORM"
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for sub_val in self.values:
                        if not ((val - sub_val) in values):
                            values.append(val - sub_val)
            else:
                print "TEST: HIM NOT"
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for sub_val in self.values:
                        if not ((val - sub_val) in values):
                            values.append(val - sub_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for sub_val in range(min(self.values), max(self.values) + 1):
                        if not ((val - sub_val) in values):
                            values.append(val - sub_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for sub_val in range(min(self.values), max(self.values) + 1):
                        if not ((val - sub_val) in values):
                            values.append(val - sub_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_lshift(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for lsh_val in self.values:
                        if not ((val << lsh_val) in values):
                            values.append(val << lsh_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for lsh_val in self.values:
                        if not ((val << lsh_val) in values):
                            values.append(val << lsh_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for lsh_val in range(min(self.values), max(self.values) + 1):
                        if not ((val << lsh_val) in values):
                            values.append(val << lsh_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for lsh_val in range(min(self.values), max(self.values) + 1):
                        if not ((val << lsh_val) in values):
                            values.append(val << lsh_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_rshift(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for rsh_val in self.values:
                        if not ((val >> rsh_val) in values):
                            values.append(val >> rsh_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for rsh_val in self.values:
                        if not ((val >> rsh_val) in values):
                            values.append(val >> rsh_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for rsh_val in range(min(self.values), max(self.values) + 1):
                        if not ((val >> rsh_val) in values):
                            values.append(val >> rsh_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for rsh_val in range(min(self.values), max(self.values) + 1):
                        if not ((val >> rsh_val) in values):
                            values.append(val >> rsh_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_and(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for and_val in self.values:
                        if not ((val & and_val) in values):
                            values.append(val & and_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for and_val in self.values:
                        if not ((val & and_val) in values):
                            values.append(val & and_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for and_val in range(min(self.values), max(self.values) + 1):
                        if not ((val & and_val) in values):
                            values.append(val & and_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for and_val in range(min(self.values), max(self.values) + 1):
                        if not ((val & and_val) in values):
                            values.append(val & and_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_xor(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for xor_val in self.values:
                        if not ((val ^ xor_val) in values):
                            values.append(val ^ xor_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for xor_val in self.values:
                        if not ((val ^ xor_val) in values):
                            values.append(val ^ xor_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for xor_val in range(min(self.values), max(self.values) + 1):
                        if not ((val ^ xor_val) in values):
                            values.append(val ^ xor_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for xor_val in range(min(self.values), max(self.values) + 1):
                        if not ((val ^ xor_val) in values):
                            values.append(val ^ xor_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
        
    def binary_or(self, vals):
        other = vals[0]
        res = MyValues()
        res.unknown_value = False
        values = []
        if (self.values) and not (other.values):
            res.unknown_value = True
        if (self.type_of_analysis == 'normal'):
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for or_val in self.values:
                        if not ((val | or_val) in values):
                            values.append(val | or_val)
            else:
                res.type_of_analysis = 'interval'
                for val in range(min(other.values), max(other.values) + 1):
                    for or_val in self.values:
                        if not ((val | or_val) in values):
                            values.append(val | or_val)
        else:
            res.type_of_analysis = 'interval'
            if (other.type_of_analysis == 'normal'):
                for val in other.values:
                    for or_val in range(min(self.values), max(self.values) + 1):
                        if not ((val | or_val) in values):
                            values.append(val | or_val)
            else:
                for val in range(min(other.values), max(other.values) + 1):
                    for or_val in range(min(self.values), max(self.values) + 1):
                        if not ((val | or_val) in values):
                            values.append(val | or_val)
        if (res.number < len(values)):
            res.type_of_analysis = 'interval'
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        if (self.unknown_value):
            res.unknown_value = True
        return res
    
    def unary_positive(self):
        return self
        
    def unary_negative(self):
        res = deepcopy(self)
        #print res
        values = []
        for val in self.values:
            values.append(-val)
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.inited = True
        return res
        
    def unary_not(self):
        pass
        
    def unary_convert(self):
        pass
        
    def unary_invert(self):
        res = deepcopy(self)
        values = []
        for val in self.values:
            if (~val) not in values:
                values.append(~val)
        if (res.type_of_analysis == 'normal'):
            res.values = values
        else:
            res.values = [min(values), max(values)]
        #res.values = values
        #res.inited = True
        return res
        
    def slice_0(self):
        if not (self.other_values):
            raise Exception("For this type slices are not implemented")
        return self
        
    def slice_1(self, vals):
        res = deepcopy(self)
        left_border = vals[0]
        other_values = []
        if not (self.other_values):
            raise Exception("For this type slices are not implemented") 
        for val in self.other_values:
            if (type(val) == str):
                for lb in left_border.values:
                    if not (val[lb:] in other_values):
                        other_values.append(val[lb:])
        res.other_values = other_values
        #res.inited = True
        return res
        
    def slice_2(self, vals):
        res = deepcopy(self)
        right_border = vals[0]
        other_values = []
        if not (self.other_values):
            raise Exception("For this type slices are not implemented") 
        for val in self.other_values:
            if (type(val) == str):
                for rb in right_border.values:
                    if not (val[:rb] in other_values):
                        other_values.append(val[:rb])
        res.other_values = other_values
        #res.inited = True
        return res
        
    def slice_3(self, vals):
        res = deepcopy(self)
        right_border = vals[1]
        left_border = vals[0]
        other_values = []
        if not (self.other_values):
            raise Exception("For this type slices are not implemented") 
        for val in self.other_values:
            if (type(val) == str):
                for lb in left_border.values:
                    for rb in right_border.values:
                        if not (val[lb:rb] in other_values):
                            other_values.append(val[lb:rb])
        res.other_values = other_values
        #res.inited = True
        return res
                    
    def compare_op(self, vals, type_of_cmp):
        other = vals[0]
        result = create_empty_value()
        result.unknown_value = False
        res_true = True
        res_false = True
#    print self, other
        if (self.unknown_value or other.unknown_value):
            result.unknown_value = True
            return result
        elif (cmp_op[type_of_cmp] == 'in' or cmp_op[type_of_cmp] == 'not in' or cmp_op[type_of_cmp] == 'is' or cmp_op[type_of_cmp] == 'is not'):  ## Сравнения сложных типов ( в моем случае, строк)
            if (len(self.other_values) == 0 or len(other.other_values) == 0):
                result.unknown_value = True
                return result
        elif (cmp_op[type_of_cmp] == 'exception match' or cmp_op[type_of_cmp] == 'BAD'): ## Непонятно что :)
            pass
        else:
            if (len(self.values) == 0 or len(other.values) == 0): ## Числовые сравнения
                result.unknown_value = True
                return result
        if (cmp_op[type_of_cmp] == '<'):
            if (self.type_of_analysis == 'normal'):
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in self.values:
                            if (other_val < val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in self.values:
                            if (other_val < val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
            else:
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val < val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val < val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
        elif (cmp_op[type_of_cmp] == '<='):
            if (self.type_of_analysis == 'normal'):
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in self.values:
                            if (other_val <= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in self.values:
                            if (other_val <= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
            else:
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val <= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val <= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
        elif (cmp_op[type_of_cmp] == '=='):
            if (len(self.values) == len(other.values) == 1):
                if (self.values[0] == other.values[0]):
                    res_true = True
                    res_false = False
                else:
                    res_true = False
                    res_false = True
            else:
                if (self.type_of_analysis == 'normal'):
                    if (other.type_of_analysis == 'normal'): 
                        for other_val in other.values:
                            for val in self.values:
                                if (other_val == val):
                                    res_true = False
                        if (res_true):
                            res_false = True
                            res_true = False
                        else:
                            res_false = False
                    else:
                        for other_val in range(other.values[0], other.values[1] + 1):
                            for val in self.values:
                                if (other_val == val):
                                    res_true = False
                        if (res_true):
                            res_false = True
                            res_true = False
                        else:
                            res_false = False
                else:
                    if (other.type_of_analysis == 'normal'):
                        for other_val in other.values:
                            for val in range(self.values[0], self.values[1] + 1):
                                if (other_val == val):
                                    res_true = False
                        if (res_true):
                            res_false = True
                            res_true = False
                        else:
                            res_false = False
                    else:
                        for other_val in range(other.values[0], other.values[1] + 1):
                            for val in range(self.values[0], self.values[1] + 1):
                                if (other_val == val):
                                    res_true = False
                        if (res_true):
                            res_false = True
                            res_true = False
                        else:
                            res_false = False                                                               
        elif (cmp_op[type_of_cmp] == '!='):
            if (self.type_of_analysis == 'normal'):
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in self.values:
                            if (other_val != val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in self.values:
                            if (other_val != val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
            else:
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val != val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val != val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
        elif (cmp_op[type_of_cmp] == '>'):
            if (self.type_of_analysis == 'normal'):
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in self.values:
                            if (other_val > val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in self.values:
                            if (other_val > val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
            else:
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val > val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val > val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
        elif (cmp_op[type_of_cmp] == '>='):
            if (self.type_of_analysis == 'normal'):
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in self.values:
                            if (other_val >= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in self.values:
                            if (other_val >= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
            else:
                if (other.type_of_analysis == 'normal'):
                    for other_val in other.values:
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val >= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
                else:
                    for other_val in range(other.values[0], other.values[1] + 1):
                        for val in range(self.values[0], self.values[1] + 1):
                            if (other_val >= val):
                                res_true &= True
                                res_false = False
                            else:
                                res_false &= True
                                res_true = False
        elif (cmp_op[type_of_cmp] == 'in'):
            for other_val in other.other_values:
                for val in self.other_values:
                    if (other_val in val):
                        res_true &= True
                        res_false = False
                    else:
                        res_false &= True
                        res_true = False
        elif (cmp_op[type_of_cmp] == 'not in'):
            for other_val in other.other_values:
                for val in self.other_values:
                    if (other_val not in val):
                        res_true &= True
                        res_false = False
                    else:
                        res_false &= True
                        res_true = False
        elif (cmp_op[type_of_cmp] == 'is'):
            for other_val in other.other_values:
                for val in self.other_values:
                    if (other_val is val):
                        res_true &= True
                        res_false = False
                    else:
                        res_false &= True
                        res_true = False
        elif (cmp_op[type_of_cmp] == 'is not'):
            for other_val in other.other_values:
                for val in self.other_values:
                    if (other_val is not val):
                        res_true &= True
                        res_false = False
                    else:
                        res_false &= True
                        res_true = False
        elif (cmp_op[type_of_cmp] == 'exception match'):
            pass
        elif (cmp_op[type_of_cmp] == 'BAD'):
            pass
        else:
            raise Exception("This shouldn't ever happen! Exception in function compare_op()")
        if (res_true == True):
            result.add_value(1) # В случае верного для всех значений выражения в стек кладется True (в нашем случае - в множество значений - 1)
        elif (res_false == True):
            result.add_value(0) # Аналогично, в стек кладется 0
        else:
            result.unknown_value = True
        return result
        
    def get_iter(self, inst):
        res = MyValues()
        res.unknown_value = False
        if (len(self.other_values[0]) == 0): #Считаем, что обрабатываем вещи вида i in 'abc' (не i in x), т.е. в other_values лежит одна строка (!!!) _СТРОКА_
            res.iterator = None
        else:
            res.iterator = self.other_values[0]
        return res
        
    insts_handler.add_set(InstSet(['BINARY_POWER', 'INPLACE_POWER'], binary_power))
    insts_handler.add_set(InstSet(['BINARY_MULTIPLY', 'INPLACE_MULTIPLY'], binary_multiply))
    insts_handler.add_set(InstSet(['BINARY_DIVIDE','BINARY_TRUE_DIVIDE','INPLACE_DIVIDE', 'INPLACE_TRUE_DIVIDE'], binary_divide))
    insts_handler.add_set(InstSet(['BINARY_FLOOR_DIVIDE', 'INPLACE_FLOOR_DIVIDE'], binary_floor_divide))
    insts_handler.add_set(InstSet(['BINARY_MODULO', 'INPLACE_MODULO'], binary_modulo))
    insts_handler.add_set(InstSet(['BINARY_ADD', 'INPLACE_ADD'], binary_add))
    insts_handler.add_set(InstSet(['BINARY_SUBTRACT', 'INPLACE_SUBTRACT'], binary_subtract))
    insts_handler.add_set(InstSet(['BINARY_LSHIFT', 'INPLACE_LSHIFT'], binary_lshift))
    insts_handler.add_set(InstSet(['BINARY_RSHIFT', 'INPLACE_RSHIFT'], binary_rshift))
    insts_handler.add_set(InstSet(['BINARY_AND', 'INPLACE_AND'], binary_and))
    insts_handler.add_set(InstSet(['BINARY_XOR', 'INPLACE_XOR'], binary_xor))
    insts_handler.add_set(InstSet(['BINARY_OR', 'INPLACE_OR'], binary_or))
    insts_handler.add_set(InstSet(['COMPARE_OP'], compare_op))
    insts_handler.add_set(InstSet(['UNARY_POSITIVE'], unary_positive))
    insts_handler.add_set(InstSet(['UNARY_NEGATIVE'], unary_negative))
    insts_handler.add_set(InstSet(['UNARY_NOT'], unary_not))
    insts_handler.add_set(InstSet(['UNARY_CONVERT'], unary_convert))
    insts_handler.add_set(InstSet(['UNARY_INVERT'], unary_invert))
    insts_handler.add_set(InstSet(['GET_ITER'], get_iter))
    insts_handler.add_set(InstSet(['UNARY_POSITIVE'], unary_positive))
    insts_handler.add_set(InstSet(['SLICE+0'], slice_0))
    insts_handler.add_set(InstSet(['SLICE+1'], slice_1))
    insts_handler.add_set(InstSet(['SLICE+2'], slice_2))
    insts_handler.add_set(InstSet(['SLICE+3'], slice_3))
    insts_handler.add_set(InstSet(['GET_ITER'], get_iter))
 


def create_empty_value():
  return MyValues()

def create_unknown_value():
  return MyValues(init_value=['unknown',True])

setglobal('create_empty_value', create_empty_value);
setglobal('create_unknown_value', create_unknown_value);
