# -*- coding: utf-8 -*-
from __future__ import with_statement
import unittest
import sys
import os
    
__all__ = ["testCFG"]

curFileName = sys.argv[0]
#print "Warning: необходимо уметь узнавать имя этого файла из него самого!"
#и поправить это в def testCFG():

    
class TestClass(object):
    """Тестовый клаcc для проверки написанного средства анализа   
    """
    def testWhile(self):
        while True:
            x = 1
    
    def testFor1(self):
        for i in [1,2]:
            x = 1
            
    def testFor_break(self):
        for i in [1,2]:
            x = i
            if x:
                break
    
    def testFor_continue(self):
        for i in [1,2]:
            x = i
            if x:
                continue
    
    def testFor_continue2(self):
        for i in [1,2]:
            x = i
            continue
            y = 1
        return y
    
    def testFor_continue3(self):
        for i in [1,2]:
            x = i
            while x:
                y = 1
                continue
    
    def testFor_continue4(self):
        for i in [1,2]:
            x = i
            while x:
                if y:
                    continue
                y = 1
                
    
    def testWhile_break(self):
        while x:
            if x:
                break
    
    def testWhile_continue(self):
        while x:
            x = i
            if x:
                continue
    
    def testIf(self):
        if True:
            x = 1
    
    def testExcept1(self):
        try:
            x = str(1)
        except str, msg:
            x = str(2)
        except Exception, msg:
            x = str(3)
    
    def testExcept2(self):
        try:
            x = str(1)
        except:
            x = str(2)
    
    def testFinally(self):
        try:
            x = str(1)
        finally:
            x = str(2)
    
    def testTry1(self):
        try:
            x = str(1)
        except str, msg:
            x = str(2)
        except Exception, msg:
            x = str(3)
        finally:
            x = str(4)
            x
            
            
    def testTryTry1(self):
        try:
            x = str(1)
        finally:
            try:
                y = str(2)
            finally:
                z = str(3)
                
    def testTryTry2(self):
        try:
            x = str(1)
        finally:
            try:
                y = str(2)
            except:
                y = 2
            finally:
                z = str(3)
                
    def testTryTry3(self):
        try:
            x = str(1)
        finally:
            try:
                y = 2
            finally:
                z = str(3)
                
    def testTryTry4(self):
        try:
            x = str(1)
        finally:
            try:
                y = 2
            finally:
                z = 3
                
    def testTryTry5(self):
        try:
            x = 1
        finally:
            try:
                y = 2
            finally:
                z = 3
                
    def testTryTry6(self):
        try:
            x = str(1)
        finally:
            try:
                try:
                    raise y
                    y = 2
                finally:
                    z = 3
            finally:
                z = 4
                
    def testBreak(self):
        while True:
            x = 1
            print x
            break
        y = 2
        print y
    
    def testTry2(self):
        try:
            x = str(1)
        except str, msg:
            x = str(2)
        except Exception, msg:
            x = str(3)
        except:
            x = str(4)
        finally:
            x = str(5)
    
    def testYield1(self):
        x = 1
        while True:
            yield x
            x += 1
        
    def testYield_Fib(self):
        a = 1
        b = 0
        while True:
            yield a
            a, b = a+b, a

    def testWith(self):
        __entry
        __exit
        with file('adsf', 'r') as fin:
            lines = fin.readlines()
        a = 1
        b = 0
        while True:
            yield a
            a, b = a+b, a

    def testYield2(self):
        lst = range(100)
        for i in lst:
            yield i
        yield "End!"
        
            
    def testLambda1(self):
        return (lambda x,y:x**y)(2,10)
        
    def testLambda2(self):
        return (lambda x, y, z:(lambda x, y: x*y)(x+y, x) / z)(4,1,20)
    
    def testList(self):
        return [x**2 for x in range(10)]
    
    def testListGenerators(self):
        return (expr for var in collection)
    
    

class CFGTestCase(unittest.TestCase):
    def setUp(self):
        curCFG = CFG()
        curCFG.load(curFileName)
        curCFG.makeCFG()
        self.curRes = curCFG.saveStructure()
        self.rightRes = {
            'testListGenerators.<genexpr_0>': (7, frozenset([(0, 1), (2, 6), (4, 5), (1, 5), (3, 6), (0, 4), (5, 2), (5, 3)]), None),
            'testLambda2.<lambda_1>': (4, frozenset([(0, 1), (1, 2), (1, 3), (2, 3)]), None),
            'testWhile': (6, frozenset([(0, 1), (4, 3), (4, 2), (2, 5), (3, 4), (1, 4)]), None),
            'testLambda1': (4, frozenset([(0, 1), (1, 2), (1, 3), (2, 3)]), None),
            'testLambda2': (4, frozenset([(0, 1), (1, 2), (1, 3), (2, 3)]), None),
            'testList': (7, frozenset([(0, 1), (1, 2), (5, 4), (4, 5), (1, 6), (3, 6), (2, 5), (5, 3)]), None),
            'testIf': (6, frozenset([(0, 1), (1, 2), (1, 3), (4, 5), (3, 4), (2, 4)]), None),
            'testYield2': (9, frozenset([(0, 1), (1, 2), (2, 6), (4, 8), (5, 6), (0, 7), (3, 8), (1, 8), (0, 5), (6, 3), (6, 4), (7, 8)]), None),
            'testYield1': (7, frozenset([(0, 1), (2, 6), (4, 5), (1, 5), (3, 6), (0, 4), (5, 2), (5, 3)]), None),
            'testLambda1.<lambda_0>': (3, frozenset([(0, 1), (1, 2)]), None),
            'testFor': (6, frozenset([(0, 1), (4, 3), (4, 2), (2, 5), (3, 4), (1, 4)]), None),
            'testExcept2': (7, frozenset([(0, 1), (1, 2), (5, 4), (1, 3), (4, 6), (2, 6), (2, 5), (3, 4)]), None),
            'testFinally': (7, frozenset([(0, 1), (3, 2), (2, 6), (4, 6), (5, 6), (1, 3), (1, 6), (2, 4)]), None),
            'testExcept1': (12, frozenset([(1, 2), (2, 6), (10, 4), (5, 9), (6, 11), (8, 11), (9, 10), (1, 3), (2, 5), (5, 8), (0, 1), (6, 7), (7, 4), (9, 11), (4, 11), (3, 4)]), None),
            'testTry1': (15, frozenset([(6, 9), (1, 3), (10, 11), (12, 14), (4, 5), (7, 14), (1, 4), (2, 12), (3, 7), (2, 14), (8, 5), (0, 1), (11, 5), (9, 2), (5, 2), (6, 10), (13, 14), (10, 14), (3, 6), (7, 8)]), None),
            'testTry2': (16, frozenset([(6, 9), (1, 3), (10, 11), (4, 5), (13, 15), (1, 4), (12, 5), (14, 15), (3, 7), (8, 5), (0, 1), (10, 15), (7, 15), (9, 15), (7, 8), (6, 10), (2, 13), (3, 6), (2, 15), (11, 5), (5, 2), (9, 12)]), None),
            'testListGenerators': (4, frozenset([(0, 1), (1, 2), (1, 3), (2, 3)]), None),
            'testLambda2.<lambda_1>.<lambda_2>': (3, frozenset([(0, 1), (1, 2)]), None),
        }

    
    def tearDown(self):
        del self.curRes
        del self.rightRes
    
    
    for funcName in [funcName for funcName in dir(TestClass) if funcName.find("test") == 0]:
        exec("""
def %s(self):
    realName = "%s"
    curFuncName = "%s."+realName
#    print curFuncName
    self.failUnless(curFuncName in self.curRes)
    self.failUnless(isinstance(self.curRes[curFuncName], tuple))
    self.failUnless(len(self.curRes[curFuncName]) == 3)
    self.failUnless(self.curRes[curFuncName][0] == self.rightRes[realName][0])
    self.failUnless(self.curRes[curFuncName][1] == self.rightRes[realName][1])
    self.failUnless(self.curRes[curFuncName][2] == self.rightRes[realName][2])
""" % (funcName, funcName, os.path.splitext(sys.argv[0])[0]+".TestClass"))
    del(funcName)

def testCFG():
#    curFileName = 
    unittest.TextTestRunner().run(unittest.makeSuite(CFGTestCase))

def printCurTestClass():
    c1 = CFG()
    c1.load("testCFG.py")
    c1.makeCFG()
    for item in c1.saveAsObjects().items():
        if item[0].find('testCFG.TestClass.') == 0:
            tmp1 = item[0][len('testCFG.TestClass.'):]
            print "'%s': %r," % (tmp1, item[1])


class TestClass2(object):
    def f1(self):
        return 1

    o = TestClass2()
    
    def f2(self):
        return 2



if __name__ == '__main__':
#    printCurTestClass()
    o2 = TestClass2()
    print dir(o2.o)
    print dir(o2)
#    unittest.TestSuite(suite())
#    unittest.main()

