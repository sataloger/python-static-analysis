# -*- coding: utf-8 -*-

#def testAssertation():
    #x = '%sasdf%s' % ('s1', u'asdf')
    #print type(x)



def testBlocksFunc():
    x = 1
    y = 2**x+x
    z = str(y)
    if z:
        z = (1,2)
    elif z:
        z = \
            (1,2,3)
    elif z:
        z = (1,2,3,4)
    elif z:
        z = [1]
    return z
    
    
def testAssertation(z):
    #x = 5
    #z = 2
    y = 1
    x = 5
    def r1(z, p = "default_value"):
        y = x+z
        return r1(z+p+y)
    
    x = r1(x)
    #return r1(z) + x
    
    
    def r2(x, y):
        y = x
        if x<100:
            return x
        else:
            return r2(x/100)
        
        
        
    def r4(x):
        if x<100:
            return x
        else:
            return r3(x+1)
    
    
        
    return r4
       #def r3(x):
         #y = r4(x+1)
         #return y
    
    
    #def r5(x):
        #def r5_1(x):
            #return r5_1(x+1)
        
        #def r5_2(x):
            #return x+1
        
        #if x<100:
            #return r5_1(x)
        #else:
            #return r5_2(x)
    
    #r6 = lambda x, y: x+2
    
    #def r7(x):
        #for i in range(x):
            #return x+y
    
    #def r8(x):
        #y = 1
        #for i in range(x):
            #return x+y
    
    
    
    
    
    #while x:
        #x -= 1; y = x; y = z; z = 'test'
        #z = 2.0
        
    #name = None
    #pagename = "lasdjflasjdf"
    #field = {
            #'name': name or 2,
            #'type': 1,
            #'order': 2,
            #'label': 3
        #}
    #pagename = pagename.rstrip('/') or 'WikiStart'





#def testFunc2():
    #z = 2
    #while x:
        #x = 2; y = 1; y = str; y = z
        #z = 2.0

#def testMy():
    #f = file('asdf')
    #m = f.read(1)
    #if m:
        #x = str
    #else:
        #x = int
    #p = x(10)



#def testIfFunc():
    #x = 2
    #while x:
        #if x:
            #y = 5
        #elif x == [1234]:
            #y = '123'
        #elif x == ():
            #y = {}
        #elif x == ():
            #y = []
        #elif x == ():
            #y = ()
        #elif x == ():
            #y = None
        #elif x == ():
            #y = str(10)
    #return x


#def testExc():
    #if z:
        #x = str(2)
    #else:
        #x = str
    #p = x()
    #try:
        #x = 1
##        raise x
        #while x:
            #while y:
                #x = 2.0
                #raise x
                #print x,
            #break
    #except str, msg:
        #print msg
        #x = '1'
    #finally:
        #y = True
##    x = 2.0
    #y = 1
    #return x
    
#def testExc2():
    #if x:
        #try:
            #raise x
            #print x,
        #except str, msg:
            #print msg
    #else:
        #x = 2
    #y = 1
    
    #return x
    

#class TestClass1():
    #def __init__(self):
        #pass

#t1 = TestClass1()

#class strangeRaiseClass():
    #def __init__(self):
        #raise strangeRaiseClass, None
##получили то, что и ожидали:

##если сделать x = strangeRaiseClass()
##alximi@home:~/projectsvn$ python run/testBlocks.py
##Traceback (most recent call last):
  ##File "run/testBlocks.py", line 66, in <module>
    ##x = strangeRaiseClass()
  ##File "run/testBlocks.py", line 62, in __init__
    ##raise strangeRaiseClass, None
##RuntimeError: maximum recursion depth exceeded


if __name__ == "__main__":
    import dis as dddis
    dddis.dis(testAssertation)
    
    #testAssertation()



##getattr(sys.modules['run'], '__path__')
##import sys, os, imp
##print dir(__builtins__)
##print
##print dir(sys)
##print

###print dir(sys._getframe())
###print 
###print sys._getframe().f_restricted
###print

###print os.getcwd()

##print getattr(sys.modules[__name__], '__file__')






##интересный набор:
##while len(vars()):
    ##del vars()[vars().keys()[0]]
##while len(locals()):
    ##del locals()[locals().keys()[0]]
##while len(globals()):
    ##del globals()[globals().keys()[0]]


    